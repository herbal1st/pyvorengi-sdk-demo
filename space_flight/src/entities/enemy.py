"""Hostile UFO spaceship and its weapons animations."""
from __future__ import annotations
import typing
from random import randint, uniform
import pygame

import src.settings as settings
from src.entities.explosion import Explosion

if typing.TYPE_CHECKING:
    from src.game import Game


class Enemy(pygame.sprite.Sprite):
    """The hostile UFO entity."""

    def __init__(self, game: Game) -> None:
        """Initialize UFO speeds, trackers, and retrieve assets."""
        super().__init__()
        self.game: Game = game

        # --- Dynamic Scaling Factor ---
        scaling_factor: float = (
            settings.BASE_GAME_SPEED_SCALING_DAMPENER
            + self.game.game_speed
        ) / (
            settings.BASE_GAME_SPEED_SCALING_DAMPENER
            + settings.INITIAL_GAME_SPEED
        )

        self.x_movement_speed: float = (
            settings.BASE_ENEMY_SPEED_X_MAX * scaling_factor
        )
        self.y_movement_speed: float = (
            settings.BASE_ENEMY_SPEED_Y * scaling_factor
        )
        self.move_down_cooldown: float = 0.0
        self.distance_moved: float = 0.0
        self.move_down: bool = False
        self.speed_change_cooldown: float = 0.0
        self.turn_direction: int = randint(0, 1)
        self.movement_direction: int = randint(0, 1)
        self.evading_chance: int = 50
        self.evaded: bool = bool(randint(0, 1))
        self.evasion_cooldown: float = 0.0
        self.trigger_laser_fire: int = 0

        self.laser_fired: bool = False

        self.image: pygame.Surface = (
            self.game.assets.sprites["enemy_ufo"]
        )
        self.rect: pygame.Rect = self.image.get_rect(
            midtop=(
                randint(75, settings.SCREEN_WIDTH - 75),
                -50
            )
        )
        self.mask: pygame.Mask = self.game.assets.masks["enemy_ufo"]

        self.pos_x: float = float(self.rect.x)
        self.pos_y: float = float(self.rect.y)

        self.lights_list: list[pygame.Surface] = (
            self.game.assets.animations["enemy_lights"]
        )
        self.lights_index: float = 0.0

        self.laser_gun_list: list[pygame.Surface] = (
            self.game.assets.animations["enemy_laser_gun"]
        )
        self.laser_gun_index: float = 0.0

        # --- Dynamic Target Calculations ---
        # Cache visual delay constants at initialization to save runtime CPU
        self.fire_delay: float = 4.0 / 30.0
        self.player_half_width: float = 33.0

        self.laser_cooldown: float = uniform(
            settings.BASE_ENEMY_LASER_LOCK_MIN,
            settings.BASE_ENEMY_LASER_LOCK_MAX
        ) / scaling_factor

    def movement(self, dt: float) -> None:
        """Calculate directional vectors, evasion steps, and bounds."""
        if self.rect.top < 75:
            self.pos_y += self.y_movement_speed * 2.0 * dt

        if self.movement_direction:
            self.pos_x += self.x_movement_speed * dt
        else:
            self.pos_x -= self.x_movement_speed * dt

        for laser_beam in self.game.player_shots:
            in_range: bool = (
                self.rect.left 
                <= laser_beam.rect.centerx 
                <= self.rect.right
            )
            is_above: bool = laser_beam.rect.top > self.rect.centery
            if in_range and is_above:
                if (
                    self.evading_chance >= randint(0, 100) 
                    and not self.evaded
                ):
                    self.movement_direction = (
                        not self.movement_direction
                    )
                    self.evaded = True

        if self.evaded:
            self.evasion_cooldown += dt
            if self.evasion_cooldown >= 2.5:
                self.evaded = False
                self.evasion_cooldown = 0.0

        self.speed_change_cooldown += dt
        if self.speed_change_cooldown >= 0.5:
            # Recalculate scaling factor dynamically
            scaling_factor: float = (
                settings.BASE_GAME_SPEED_SCALING_DAMPENER
                + self.game.game_speed
            ) / (
                settings.BASE_GAME_SPEED_SCALING_DAMPENER
                + settings.INITIAL_GAME_SPEED
            )
            self.x_movement_speed = (
                uniform(
                    settings.BASE_ENEMY_SPEED_X_MIN,
                    settings.BASE_ENEMY_SPEED_X_MAX
                ) * scaling_factor
            )
            self.speed_change_cooldown = 0.0

        self.move_down_cooldown += dt
        if self.move_down_cooldown >= 2.0:
            self.move_down_cooldown = 0.0
            self.move_down = True

        if self.move_down:
            step_y: float = self.y_movement_speed * dt
            self.pos_y += step_y
            self.distance_moved += step_y
            if self.distance_moved >= 75.0:
                self.distance_moved = 0.0
                self.move_down = False

        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)

        if self.rect.bottom <= settings.SCREEN_HEIGHT // 2:
            if self.rect.left <= 25:
                self.movement_direction = True
            if self.rect.right >= settings.SCREEN_WIDTH - 25:
                self.movement_direction = False
        if (
            self.rect.right <= 0
            or self.rect.left >= settings.SCREEN_WIDTH
        ):
            self.kill()

    def laser_fire(self, dt: float) -> None:
        """Process alignments and spawn ufo laser beams."""
        self.laser_cooldown -= dt
        if self.laser_cooldown <= 0.0:
            self.laser_cooldown = 0.0
            if self.game.ship.sprite:
                player_rect = self.game.ship.sprite.rect
                p_vel_x: float = self.game.ship.sprite.velocity_x

                # Determine active speed based on direction
                v_enemy: float = (
                    self.x_movement_speed
                    if self.movement_direction
                    else -self.x_movement_speed
                )

                # Calculate relative drift distance during muzzle delay
                d_rel: float = (v_enemy - p_vel_x) * self.fire_delay

                # Symmetrical trigger boundary check
                if abs(d_rel) <= self.player_half_width:
                    # Low speed: direct alignment
                    is_aligned = (
                        player_rect.left
                        <= self.rect.centerx
                        <= player_rect.right
                    )
                else:
                    # High speed: predictive target offset alignment
                    is_aligned = (
                        player_rect.left
                        <= self.rect.centerx + d_rel
                        <= player_rect.right
                    )

                if is_aligned:
                    self.trigger_laser_fire = 1
                    # Dynamic Firing Cooldown Scaling with Randomization
                    scaling_factor: float = (
                        settings.BASE_GAME_SPEED_SCALING_DAMPENER
                        + self.game.game_speed
                    ) / (
                        settings.BASE_GAME_SPEED_SCALING_DAMPENER
                        + settings.INITIAL_GAME_SPEED
                    )
                    self.laser_cooldown = uniform(
                        settings.BASE_ENEMY_LASER_DELAY_MIN,
                        settings.BASE_ENEMY_LASER_DELAY_MAX
                    ) / scaling_factor

        if (
            self.trigger_laser_fire
            and self.laser_gun_index >= 4.0
            and not self.laser_fired
        ):
            self.game.enemy_shots.add(
                EnemyLaserBeam(self.game, self.rect.midbottom)
            )
            self.game.sound_ufo_laser_shot.play()
            self.game.sound_ufo_laser_shot.set_volume(0.15)
            self.laser_fired = True

    def collision(self) -> None:
        """Observe projectile contacts to resolve scores."""
        for laser_beam in self.game.player_shots:
            if self.rect.top >= 0:
                if pygame.sprite.collide_rect(self, laser_beam):
                    if pygame.sprite.collide_mask(self, laser_beam):
                        self.game.score += 100
                        laser_beam.kill()
                        self.game.sound_ufo_explosion.play()
                        self.game.sound_ufo_explosion.set_volume(0.2)
                        self.game.explosions.add(
                            Explosion(
                                self.game,
                                [self.rect.x, self.rect.right],
                                [self.rect.y, self.rect.bottom],
                                True,
                            )
                        )
                        self.kill()

    def draw_extras(self, surface: pygame.Surface) -> None:
        """Render animated overlay indicators."""
        lights_img = self.lights_list[int(self.lights_index)]
        surface.blit(lights_img, self.rect.topleft)

        if self.trigger_laser_fire:
            gun_img = self.laser_gun_list[int(self.laser_gun_index)]
            surface.blit(
                gun_img, (self.rect.x, self.rect.y + 58)
            )

    def update(self, dt: float) -> None:
        """Evaluate layout offsets, ticks, and overlaps."""
        self.movement(dt)
        self.laser_fire(dt)
        self.collision()

        if self.turn_direction:
            self.lights_index += 30.0 * dt
            if self.lights_index >= len(self.lights_list):
                self.lights_index = 0.0
        else:
            self.lights_index -= 30.0 * dt
            if self.lights_index <= 0:
                self.lights_index = float(len(self.lights_list) - 1)

        if self.trigger_laser_fire:
            self.laser_gun_index += 30.0 * dt
            if self.laser_gun_index >= len(self.laser_gun_list):
                self.laser_gun_index = 0.0
                self.trigger_laser_fire = 0
                self.laser_fired = False


class EnemyLaserBeam(pygame.sprite.Sprite):
    """Weapon laser fired by UFOs."""

    def __init__(self, game: Game, pos: tuple[int, int]) -> None:
        """Initialize weapons, vectors, and retrieve assets."""
        super().__init__()
        self.game: Game = game

        # Dynamic enemy laser projectile speed scaling
        scaling_factor: float = (
            settings.BASE_GAME_SPEED_SCALING_DAMPENER
            + self.game.game_speed
        ) / (
            settings.BASE_GAME_SPEED_SCALING_DAMPENER
            + settings.INITIAL_GAME_SPEED
        )
        self.movement_speed: float = (
            settings.BASE_ENEMY_LASER_SPEED * scaling_factor
        )

        self.pos: tuple[int, int] = pos

        self.laser_beam_list: list[pygame.Surface] = (
            self.game.assets.animations["enemy_laser_beam"]
        )
        self.laser_beam_masks: list[pygame.Mask] = (
            self.game.assets.animation_masks["enemy_laser_beam"]
        )
        
        self.laser_beam_index: float = 0.0
        self.image: pygame.Surface = self.laser_beam_list[
            int(self.laser_beam_index)
        ]
        self.rect: pygame.Rect = self.image.get_rect(midtop=pos)
        self.mask: pygame.Mask = self.laser_beam_masks[
            int(self.laser_beam_index)
        ]

        self.pos_x: float = float(self.rect.x)
        self.pos_y: float = float(self.rect.y)

    def animations(self, dt: float) -> None:
        """Calculate animated offset positions."""
        self.laser_beam_index += 12.0 * dt
        if self.laser_beam_index >= len(self.laser_beam_list):
            self.laser_beam_index = 0.0
        
        idx = int(self.laser_beam_index)
        self.image = self.laser_beam_list[idx]
        self.mask = self.laser_beam_masks[idx]

    def movement(self, dt: float) -> None:
        """Update translation vectors."""
        self.pos_y += self.movement_speed * dt
        self.rect.y = int(self.pos_y)
        if self.rect.top > settings.SCREEN_HEIGHT:
            self.kill()

    def update(self, dt: float) -> None:
        """Calculate delta motion and frames indexes."""
        self.animations(dt)
        self.movement(dt)
