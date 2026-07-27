"""Parallax scrolling star background element rendering layers."""
from __future__ import annotations
import typing
from random import randint
import pygame

import src.settings as settings

if typing.TYPE_CHECKING:
    from src.game import Game


class Star(pygame.sprite.Sprite):
    """Parallax scrolling star for the simulated depth background."""

    SCALES: tuple[tuple[int, int], ...] = (
        (5, 13),
        (10, 26),
        (14, 39),
        (17, 52),
        (19, 89),
        (20, 117),
    )

    def __init__(self, game: Game, y_pos: int = -50) -> None:
        """Initialize scroll parameters and retrieve cached frames."""
        super().__init__()
        self.game: Game = game
        self.star_distance: int = randint(0, 20)

        scale_size: int = 13
        for limit, size in self.SCALES:
            if self.star_distance <= limit:
                scale_size = size
                break

        self.all_stars_index: int = randint(0, 3)
        anim_key: str = f"star_{self.all_stars_index + 1}_{scale_size}"
        self.star_list: list[pygame.Surface] = (
            self.game.assets.animations[anim_key]
        )

        self.star_index: float = float(
            randint(0, len(self.star_list) - 1)
        )

        self.image: pygame.Surface = self.star_list[
            int(self.star_index)
        ]
        self.rect: pygame.Rect = self.image.get_rect(
            center=(randint(-25, settings.SCREEN_WIDTH + 25), y_pos)
        )

        self.pos_x: float = float(self.rect.x)
        self.pos_y: float = float(self.rect.y)

        # Resolve scroll speed based on distance grouping
        if self.star_distance in (0, 1, 2, 3, 4, 5):
            self.scroll_speed: float = 60.0
        elif self.star_distance in (6, 7, 8, 9, 10):
            self.scroll_speed = 120.0
        elif self.star_distance in (11, 12, 13, 14):
            self.scroll_speed = 180.0
        elif self.star_distance in (15, 16, 17):
            self.scroll_speed = 240.0
        elif self.star_distance in (18, 19):
            self.scroll_speed = 300.0
        else:
            self.scroll_speed = 360.0

    def animation(self, dt: float) -> None:
        """Calculate animated offset frames."""
        self.star_index += 30.0 * dt
        if self.star_index >= len(self.star_list):
            self.star_index = 0.0
        self.image = self.star_list[int(self.star_index)]

    def movement(self, dt: float) -> None:
        """Propagate dynamic depth vector coordinates."""
        # Calculate dynamic Scaling Multiplier (Sm)
        scaling_factor: float = (
            settings.BASE_GAME_SPEED_SCALING_DAMPENER
            + self.game.game_speed
        ) / (
            settings.BASE_GAME_SPEED_SCALING_DAMPENER
            + settings.INITIAL_GAME_SPEED
        )

        self.pos_y += self.scroll_speed * scaling_factor * dt
        self.rect.y = int(self.pos_y)
        if self.rect.top > settings.SCREEN_HEIGHT:
            self.kill()

    def update(self, dt: float) -> None:
        """Process layouts and parallax vector offsets."""
        self.animation(dt)
        self.movement(dt)
