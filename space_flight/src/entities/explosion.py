"""Visual explosive special effects triggered during entity collisions."""
from __future__ import annotations
import typing
from random import randint
import pygame

import src.settings as settings

if typing.TYPE_CHECKING:
    from src.game import Game


class Explosion(pygame.sprite.Sprite):
    """The visual animated explosion effect."""

    def __init__(
        self,
        game: Game,
        pos_x: list[int],
        pos_y: list[int],
        original: bool = False,
    ) -> None:
        """Initialize placement ranges and cached frames."""
        super().__init__()
        self.game: Game = game
        self.pos_x: list[int] = pos_x
        self.pos_y: list[int] = pos_y
        self.rand_pos_x: int = randint(pos_x[0], pos_x[1])
        self.rand_pos_y: int = randint(pos_y[0], pos_y[1])
        self.original: bool = original

        self.explosion_list: list[pygame.Surface] = (
            self.game.assets.animations["explosion"]
        )
        self.explosion_masks: list[pygame.Mask] = (
            self.game.assets.animation_masks["explosion"]
        )
        
        self.explosion_index: float = 0.0
        self.image: pygame.Surface = self.explosion_list[
            int(self.explosion_index)
        ]
        self.rect: pygame.Rect = self.image.get_rect(
            center=(self.rand_pos_x, self.rand_pos_y)
        )
        self.mask: pygame.Mask = self.explosion_masks[
            int(self.explosion_index)
        ]

    def animation(self, dt: float) -> None:
        """Advance detonation frames based on delta scale."""
        self.explosion_index += 60.0 * dt
        if self.explosion_index >= len(self.explosion_list):
            self.explosion_index = float(len(self.explosion_list) - 1)
            self.kill()
        
        idx = int(self.explosion_index)
        self.image = self.explosion_list[idx]
        self.mask = self.explosion_masks[idx]

        if self.original:
            self.game.explosions.add(
                Explosion(self.game, self.pos_x, self.pos_y)
                    )

    def update(self, dt: float) -> None:
        """Calculate layout frame updates."""
        self.animation(dt)
