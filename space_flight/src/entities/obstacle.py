"""Space rocks, meteors, and tumbling hazard entities."""
from __future__ import annotations
import typing
from random import randint, uniform
import pygame

import src.settings as settings
from src.entities.explosion import Explosion

if typing.TYPE_CHECKING:
    from src.game import Game


class Obstacle(pygame.sprite.Sprite):
    """The falling hazard space rocks/asteroids."""

    def __init__(self, game: Game) -> None:
        """Initialize asteroid velocity, rotations, and vectors."""
        super().__init__()
        self.game: Game = game

        # Calculate dynamic Scaling Multiplier (Sm)
        scaling_factor: float = (
            settings.BASE_GAME_SPEED_SCALING_DAMPENER
            + self.game.game_speed
        ) / (
            settings.BASE_GAME_SPEED_SCALING_DAMPENER
            + settings.INITIAL_GAME_SPEED
        )

        self.speed_x: float = (
            float(randint(0, 5)) * 60.0 * scaling_factor
        )
        self.speed_y: float = (
            float(randint(2, 5)) * 60.0 * scaling_factor
        )
        self.direction_x: int = randint(0, 1)
        self.turn_direction: int = randint(0, 1)
        self.turn_speed: float = uniform(30.0, 60.0)

        self.obstacle_list: list[pygame.Surface] = (
            self.game.assets.animations["rock"]
        )
        self.obstacle_masks: list[pygame.Mask] = (
            self.game.assets.animation_masks["rock"]
        )
        
        self.obstacle_index: float = 0.0
        self.image: pygame.Surface = self.obstacle_list[
            int(self.obstacle_index)
        ]
        self.rect: pygame.Rect = self.image.get_rect(
            center=(randint(-100, settings.SCREEN_WIDTH + 100), -50)
        )
        self.mask: pygame.Mask = self.obstacle_masks[
            int(self.obstacle_index)
        ]

        self.pos_x: float = float(self.rect.x)
        self.pos_y: float = float(self.rect.y)

    def animation(self, dt: float) -> None:
        """Compute active tumbling rotation layout frame."""
        if self.turn_direction:
            self.obstacle_index += self.turn_speed * dt
            if self.obstacle_index >= len(self.obstacle_list):
                self.obstacle_index = 0.0
        else:
            self.obstacle_index -= self.turn_speed * dt
            if self.obstacle_index <= 0:
                self.obstacle_index = float(
                    len(self.obstacle_list) - 1
                )
        
        idx = int(self.obstacle_index)
        self.image = self.obstacle_list[idx]
        self.mask = self.obstacle_masks[idx]

    def movement(self, dt: float) -> None:
        """Calculate directional translation and viewport exits."""
        if self.direction_x:
            self.pos_x += self.speed_x * dt
        else:
            self.pos_x -= self.speed_x * dt
        self.pos_y += self.speed_y * dt

        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)

        if (
            self.rect.right >= settings.SCREEN_WIDTH + 150
            or self.rect.x <= -150
        ):
            # Recalculate dynamic scaling factor
            scaling_factor: float = (
                settings.BASE_GAME_SPEED_SCALING_DAMPENER
                + self.game.game_speed
            ) / (
                settings.BASE_GAME_SPEED_SCALING_DAMPENER
                + settings.INITIAL_GAME_SPEED
            )
            self.speed_x = (
                float(randint(2, 5)) * 60.0 * scaling_factor
            )
            self.speed_y = (
                float(randint(2, 5)) * 60.0 * scaling_factor
            )
            self.direction_x = not self.direction_x
        if self.rect.top > settings.SCREEN_HEIGHT:
            self.kill()

    def collision(self) -> None:
        """Check laser impacts to trigger explosions and add scores."""
        for laser_beam in self.game.player_shots:
            if pygame.sprite.collide_rect(self, laser_beam):
                if pygame.sprite.collide_mask(self, laser_beam):
                    self.game.score += 10
                    laser_beam.kill()
                    self.game.sound_rock_explosion.play()
                    self.game.sound_rock_explosion.set_volume(0.2)
                    self.game.explosions.add(
                        Explosion(
                            self.game,
                            [self.rect.x, self.rect.right],
                            [self.rect.y, self.rect.bottom],
                            True,
                        )
                    )
                    self.kill()

    def update(self, dt: float) -> None:
        """Process animation matrices, motion delta, and hit overlaps."""
        self.animation(dt)
        self.movement(dt)
        self.collision()
