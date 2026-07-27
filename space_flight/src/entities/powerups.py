"""Shield, Health, and Energy collectibles."""
from __future__ import annotations
import typing
from random import randint
import pygame

import src.settings as settings

if typing.TYPE_CHECKING:
    from src.game import Game


class _BasePowerup(pygame.sprite.Sprite):
    """Internal base class handling movement, bounds, and animations."""

    def __init__(
        self,
        game: Game,
        folder_name: str,
        anim_speed: float = 15.0,
    ) -> None:
        """Initialize generic parameters and query cached frames."""
        super().__init__()
        self.game: Game = game
        self.anim_speed: float = anim_speed

        self.image_list: list[pygame.Surface] = (
            self.game.assets.animations[folder_name]
        )
        self.image_masks: list[pygame.Mask] = (
            self.game.assets.animation_masks[folder_name]
        )
        
        self.image_index: float = 0.0
        self.image: pygame.Surface = self.image_list[
            int(self.image_index)
        ]
        self.rect: pygame.Rect = self.image.get_rect(
            center=(randint(50, settings.SCREEN_WIDTH - 50), -50)
        )
        self.mask: pygame.Mask = self.image_masks[int(self.image_index)]

        self.pos_x: float = float(self.rect.x)
        self.pos_y: float = float(self.rect.y)

    def animation(self, dt: float) -> None:
        """Compute dynamic animation ticks."""
        self.image_index += self.anim_speed * dt
        if self.image_index >= len(self.image_list):
            self.image_index = 0.0
        
        idx = int(self.image_index)
        self.image = self.image_list[idx]
        self.mask = self.image_masks[idx]

    def movement(self, dt: float) -> None:
        """Update forward vertical translation vector."""
        # Calculate dynamic game speed scaling factor (damped)
        scaling_factor: float = (
            settings.BASE_GAME_SPEED_SCALING_DAMPENER
            + self.game.game_speed
        ) / (
            settings.BASE_GAME_SPEED_SCALING_DAMPENER
            + settings.INITIAL_GAME_SPEED
        )

        self.pos_y += 300.0 * scaling_factor * dt
        self.rect.y = int(self.pos_y)
        if self.rect.top > settings.SCREEN_HEIGHT:
            self.kill()

    def update(self, dt: float) -> None:
        """Process animation indexes and linear translation."""
        self.animation(dt)
        self.movement(dt)


class ShieldPowerup(_BasePowerup):
    """Collectible shield regeneration powerup."""

    def __init__(self, game: Game) -> None:
        """Construct active shield powerup indicators."""
        super().__init__(
            game, "powerup shield", anim_speed=30.0
        )


class HealthPowerup(_BasePowerup):
    """Collectible hull repair powerup."""

    def __init__(self, game: Game) -> None:
        """Construct repair indicators."""
        super().__init__(game, "powerup health")


class EnergyPowerup(_BasePowerup):
    """Collectible ammunition recharging powerup."""

    def __init__(self, game: Game) -> None:
        """Construct reload indicators."""
        super().__init__(game, "powerup energy")
