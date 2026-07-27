"""Player controlled spaceship and secondary weapons/shields."""
from __future__ import annotations
import typing
import pygame

import src.settings as settings
from src.entities.explosion import Explosion

if typing.TYPE_CHECKING:
    from src.game import Game


class PlayerShip(pygame.sprite.Sprite):
    """The player controlled spaceship sprite."""

    def __init__(self, game: Game) -> None:
        """Initialize ship attributes, positions, and cached assets."""
        super().__init__()
        self.game: Game = game
        self.score: int = 0
        self.movement_speed: float = 600.0
        self.laser_cooldown: float = 0.0
        self.trigger_laser_fire: int = 0
        self.use_mouse: bool = True
        self.activate_shield: bool = True
        self.health: int = 10
        self.energy: int = 200

        self.laser_fired: bool = False

        self.image: pygame.Surface = self.game.assets.sprites["ship"]
        self.rect: pygame.Rect = self.image.get_rect(
            midtop=(
                settings.SCREEN_WIDTH // 2,
                settings.SCREEN_HEIGHT - 200,
            )
        )
        self.mask: pygame.Mask = self.game.assets.masks["ship"]

        self.pos_x: float = float(self.rect.x)
        self.pos_y: float = float(self.rect.y)

        self.lights_list: list[pygame.Surface] = (
            self.game.assets.animations["ship_lights"]
        )
        self.lights_index: float = 0.0

        self.exhaust_list: list[pygame.Surface] = (
            self.game.assets.animations["ship_exhaust"]
        )
        self.exhaust_index: float = 0.0

        self.laser_gun_list: list[pygame.Surface] = (
            self.game.assets.animations["ship_laser_gun"]
        )
        self.laser_gun_index: float = 0.0

        # --- Dynamic Velocity Tracking Attributes ---
        self.prev_x: float = float(self.rect.x)
        self.velocity_x: float = 0.0

        # --- UI Score Memoization Cache ---
        self.cached_score: int = -1
        self.score_surface: pygame.Surface = None

    def health_func(self) -> None:
        """Check structural health limits to trigger defeat states."""
        if self.health <= 0:
            self.use_mouse = False
            self.game.trigger_game_over()

    def controls(self, dt: float) -> None:
        """Process movement bindings, clamps, and projectiles."""
        pressed = pygame.key.get_pressed()

        if pressed[pygame.K_k]:
            self.use_mouse = False
        if pressed[pygame.K_m]:
            self.use_mouse = True

        if not self.use_mouse:
            pygame.mouse.set_visible(True)

            # Dampen keyboard speed dynamically
            kb_scaling: float = (
                settings.KEYBOARD_MOVE_SPEED_SCALING_DAMPENER
                + self.game.game_speed
            ) / (
                settings.KEYBOARD_MOVE_SPEED_SCALING_DAMPENER
                + settings.INITIAL_GAME_SPEED
            )
            current_speed: float = self.movement_speed * kb_scaling

            if pressed[pygame.K_LEFT]:
                self.pos_x -= current_speed * dt
            if pressed[pygame.K_RIGHT]:
                self.pos_x += current_speed * dt
            if pressed[pygame.K_UP]:
                self.pos_y -= current_speed * dt
            if pressed[pygame.K_DOWN]:
                self.pos_y += current_speed * dt

            self.rect.x = int(self.pos_x)
            self.rect.y = int(self.pos_y)

            self.rect.left = max(25, self.rect.left)
            self.rect.right = min(
                settings.SCREEN_WIDTH - 25, self.rect.right
            )
            self.rect.top = max(
                settings.SCREEN_HEIGHT // 2, self.rect.top
            )
            self.rect.bottom = min(
                settings.SCREEN_HEIGHT - 50, self.rect.bottom
            )

            self.pos_x = float(self.rect.x)
            self.pos_y = float(self.rect.y)

        if self.use_mouse:
            pygame.mouse.set_visible(False)
            m_x, m_y = pygame.mouse.get_pos()

            clamped_x: int = max(
                25, min(settings.SCREEN_WIDTH - 25, m_x)
            )
            clamped_y: int = max(
                settings.SCREEN_HEIGHT // 2,
                min(settings.SCREEN_HEIGHT - 50, m_y),
            )

            if m_x != clamped_x or m_y != clamped_y:
                pygame.mouse.set_pos((clamped_x, clamped_y))

            self.rect.center = (clamped_x, clamped_y)
            self.pos_x = float(self.rect.x)
            self.pos_y = float(self.rect.y)

        # Calculate dynamic Scaling Multiplier (Sm)
        scaling_factor: float = (
            settings.BASE_GAME_SPEED_SCALING_DAMPENER + self.game.game_speed
        ) / (
            settings.BASE_GAME_SPEED_SCALING_DAMPENER
            + settings.INITIAL_GAME_SPEED
        )

        dynamic_delay: float = (
            settings.BASE_PLAYER_LASER_DELAY / scaling_factor
        )

        if self.laser_cooldown < dynamic_delay:
            self.laser_cooldown += dt
        if self.energy > 0:
            firing_input = (
                pressed[pygame.K_SPACE]
                or pygame.mouse.get_pressed()[0]
            )
            if firing_input and self.laser_cooldown >= dynamic_delay:
                self.trigger_laser_fire = 1

            if (
                self.trigger_laser_fire
                and self.laser_gun_index >= 4.0
                and not self.laser_fired
            ):
                self.game.player_shots.add(PlayerLaserBeam(self.game))
                
                # Calculate dynamic smoothed energy cost per shot
                dampener: float = (
                    1.0 + (scaling_factor - 1.0)
                    * settings.ENERGY_SAVING_FACTOR
                )
                cost: float = (
                    settings.BASE_PLAYER_LASER_COST / dampener
                )
                self.energy -= cost
                
                self.laser_cooldown = 0.0
                self.game.sound_player_laser_shot.play()
                self.game.sound_player_laser_shot.set_volume(0.2)
                self.laser_fired = True

    def _resolve_collision(
        self,
        group: pygame.sprite.Group,
        kill_target: bool,
        damage: int,
        sound: any,
        vol: float,
        is_major: bool,
    ) -> None:
        """Resolve impacts, hull damage, audio triggers, and bursts."""
        for target in group:
            if pygame.sprite.collide_rect(self, target):
                if pygame.sprite.collide_mask(self, target):
                    if kill_target:
                        target.kill()
                    self.health = max(0, self.health - damage)
                    sound.play()
                    sound.set_volume(vol)
                    self.game.explosions.add(
                        Explosion(
                            self.game,
                            [target.rect.x, target.rect.right],
                            [target.rect.y, target.rect.bottom],
                            is_major,
                        )
                    )

    def collision(self) -> None:
        """Observe visual overlaps to apply damage or powerups."""
        self._resolve_collision(
            self.game.enemy_shots,
            True,
            1,
            self.game.sound_ufo_laser_hit,
            0.1,
            False,
        )
        self._resolve_collision(
            self.game.enemies,
            True,
            1,
            self.game.sound_ufo_explosion,
            0.2,
            True,
        )
        self._resolve_collision(
            self.game.obstacles,
            True,
            1,
            self.game.sound_rock_explosion,
            0.2,
            True,
        )

        from src.entities.powerups import (
            ShieldPowerup, HealthPowerup, EnergyPowerup
        )
        for powerup in self.game.powerups:
            if pygame.sprite.collide_rect(self, powerup):
                if pygame.sprite.collide_mask(self, powerup):
                    self.game.sound_powerup.play()
                    self.game.sound_powerup.set_volume(0.2)
                    if isinstance(powerup, ShieldPowerup):
                        powerup.kill()
                        self.game.player_shield.add(
                            PlayerShield(self.game)
                        )
                    elif isinstance(powerup, HealthPowerup):
                        powerup.kill()
                        self.health = min(10, self.health + 5)
                    elif isinstance(powerup, EnergyPowerup):
                        powerup.kill()
                        self.energy = min(200, self.energy + 100)

    def _draw_hud_gauge(
        self,
        surface: pygame.Surface,
        x_bg: int,
        border_color: tuple[int, int, int],
        start_x: float,
        end_x: float,
        color_channel: int,
    ) -> None:
        """Render vectors representing ship statuses."""
        pygame.draw.rect(surface, border_color, (x_bg, 11, 256, 29), 2)
        for i in range(1, 6):
            color = (
                (0, 130 + i * 25, 0)
                if color_channel == 1
                else (0, 0, 130 + i * 25)
            )
            pygame.draw.line(
                surface,
                color,
                (int(start_x), 25),
                (int(end_x), 25),
                30 - i * 5,
            )

    def draw_extras(self, surface: pygame.Surface) -> None:
        """Draw composite decals, overlays, and status gauges."""
        if self.game.score != self.cached_score or not self.score_surface:
            self.cached_score = self.game.score
            score_str: str = str(self.cached_score)
            self.score_surface = self.game.font_2.render(
                score_str, True, (255, 255, 251)
            )

        x_pos: int = (
            settings.SCREEN_WIDTH // 2 - self.score_surface.get_width() // 2
        )
        surface.blit(self.score_surface, (x_pos, 0))

        lights_img = self.lights_list[int(self.lights_index)]
        surface.blit(
            lights_img, (self.rect.x + 12, self.rect.y + 38)
        )

        exhaust_img = self.exhaust_list[int(self.exhaust_index)]
        surface.blit(
            exhaust_img, (self.rect.x, self.rect.y + 50)
        )

        if self.energy > 0 and self.trigger_laser_fire:
            gun_img = self.laser_gun_list[int(self.laser_gun_index)]
            surface.blit(gun_img, (self.rect.x, self.rect.y - 42))

        self._draw_hud_gauge(
            surface, 8, (0, 130, 0), 10, 11 + self.health * 25, 1
        )
        self._draw_hud_gauge(
            surface,
            settings.SCREEN_WIDTH - 263,
            (0, 0, 130),
            settings.SCREEN_WIDTH - 11 - self.energy * 1.25,
            settings.SCREEN_WIDTH - 10,
            2,
        )

    def update(self, dt: float) -> None:
        """Calculate layout animations, check controls, and impacts."""
        starting_x: float = self.pos_x

        self.health_func()
        self.controls(dt)

        self.velocity_x = (self.pos_x - starting_x) / dt

        self.lights_index += 60.0 * dt
        if self.lights_index >= len(self.lights_list):
            self.lights_index = 0.0

        self.exhaust_index += 30.0 * dt
        if self.exhaust_index >= len(self.exhaust_list):
            self.exhaust_index = 0.0

        if self.energy > 0 and self.trigger_laser_fire:
            self.laser_gun_index += 60.0 * dt
            if self.laser_gun_index >= len(self.laser_gun_list):
                self.laser_gun_index = 0.0
                self.trigger_laser_fire = 0
                self.laser_fired = False

        self.collision()


class PlayerLaserBeam(pygame.sprite.Sprite):
    """The player fired laser projectile."""

    def __init__(self, game: Game) -> None:
        """Initialize projectile constructor, positions, and bounds."""
        super().__init__()
        self.game: Game = game
        self.laser_beam_list: list[pygame.Surface] = (
            self.game.assets.animations["ship_laser_beam"]
        )
        self.laser_beam_masks: list[pygame.Mask] = (
            self.game.assets.animation_masks["ship_laser_beam"]
        )
        
        self.laser_beam_index: float = 0.0
        self.image: pygame.Surface = self.laser_beam_list[
            int(self.laser_beam_index)
        ]
        self.rect: pygame.Rect = self.image.get_rect(
            midbottom=self.game.ship.sprite.rect.midtop
        )
        self.mask: pygame.Mask = self.laser_beam_masks[
            int(self.laser_beam_index)
        ]

        self.pos_x: float = float(self.rect.x)
        self.pos_y: float = float(self.rect.y)

        # Dynamic player laser projectile speed scaling
        scaling_factor: float = (
            settings.BASE_GAME_SPEED_SCALING_DAMPENER + self.game.game_speed
        ) / (
            settings.BASE_GAME_SPEED_SCALING_DAMPENER
            + settings.INITIAL_GAME_SPEED
        )
        self.movement_speed: float = (
            settings.BASE_PLAYER_LASER_SPEED * scaling_factor
        )

    def animations(self, dt: float) -> None:
        """Calculate active layout indices."""
        self.laser_beam_index += 60.0 * dt
        if self.laser_beam_index >= len(self.laser_beam_list):
            self.laser_beam_index = 0.0
        
        idx = int(self.laser_beam_index)
        self.image = self.laser_beam_list[idx]
        self.mask = self.laser_beam_masks[idx]

    def movement(self, dt: float) -> None:
        """Propagate forward translation vector."""
        self.pos_y -= self.movement_speed * dt
        self.rect.y = int(self.pos_y)
        if self.rect.bottom < 0:
            self.kill()

    def update(self, dt: float) -> None:
        """Compute layout updates and forward movement vector."""
        self.animations(dt)
        self.movement(dt)


class PlayerShield(pygame.sprite.Sprite):
    """Energy barrier defending the player."""

    def __init__(self, game: Game) -> None:
        """Initialize barrier health, bounding parameters, and paths."""
        super().__init__()
        self.game: Game = game
        self.shield_health: int = 5

        self.image_list: list[pygame.Surface] = (
            self.game.assets.animations["ship_shield"]
        )
        self.image_masks: list[pygame.Mask] = (
            self.game.assets.animation_masks["ship_shield"]
        )
        
        self.image_index: float = 0.0
        self.image: pygame.Surface = self.image_list[
            int(self.image_index)
        ]
        self.rect: pygame.Rect = self.image.get_rect(
            center=(
                self.game.ship.sprite.rect.centerx,
                self.game.ship.sprite.rect.centery + 9,
            )
        )
        self.mask: pygame.Mask = self.image_masks[int(self.image_index)]

    def animation(self, dt: float) -> None:
        """Calculate rotation layout indexes."""
        self.rect = self.image.get_rect(
            center=(
                self.game.ship.sprite.rect.centerx,
                self.game.ship.sprite.rect.centery + 9,
            )
        )
        self.image_index += 6.0 * dt
        if self.image_index >= len(self.image_list):
            self.image_index = 0.0
        
        idx = int(self.image_index)
        self.image = self.image_list[idx]
        self.mask = self.image_masks[idx]

    def _resolve_collision(
        self,
        group: pygame.sprite.Group,
        damage: int,
        sound: any,
        vol: float,
        is_major: bool,
    ) -> None:
        """Process target hits and reduce integrity indices."""
        for target in group:
            if pygame.sprite.collide_rect(self, target):
                if pygame.sprite.collide_mask(self, target):
                    target.kill()
                    self.shield_health -= damage
                    sound.play()
                    sound.set_volume(vol)
                    self.game.explosions.add(
                        Explosion(
                            self.game,
                            [target.rect.x, target.rect.right],
                            [target.rect.y, target.rect.bottom],
                            is_major,
                        )
                    )

    def collision(self) -> None:
        """Observe overlaps to absorb projectile elements."""
        self._resolve_collision(
            self.game.enemy_shots,
            1,
            self.game.sound_ufo_laser_hit,
            0.1,
            False,
        )
        self._resolve_collision(
            self.game.enemies,
            1,
            self.game.sound_ufo_explosion,
            0.2,
            True,
        )
        self._resolve_collision(
            self.game.obstacles,
            1,
            self.game.sound_rock_explosion,
            0.2,
            True,
        )

        if self.shield_health <= 0:
            self.kill()

    def update(self, dt: float) -> None:
        """Compute layout updates and overlap conditions."""
        self.animation(dt)
        self.collision()
