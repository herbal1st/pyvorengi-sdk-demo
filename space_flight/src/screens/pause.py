"""Suspend execution displaying resume option buttons."""
from __future__ import annotations
import typing
import pygame

import src.settings as settings

if typing.TYPE_CHECKING:
    from src.game import Game


class PauseScreen(pygame.sprite.Sprite):
    """Suspend execution displaying resume option buttons."""

    def __init__(self, game: Game) -> None:
        """Initialize graphics lists and select buttons."""
        super().__init__()
        self.game: Game = game
        self.back_clicked: bool = False

        path_back: Path = settings.GRAPHICS_DIR / "artwork" / "back.png"
        self.image: pygame.Surface = pygame.image.load(str(path_back)).convert_alpha()
        self.rect: pygame.Rect = self.image.get_rect(topleft=(285, 355))

    def interaction(self) -> None:
        """Observe coordinates to evaluate return updates."""
        pygame.mouse.set_visible(True)

        if pygame.mouse.get_pressed()[0]:
            m_pos = pygame.mouse.get_pos()
            if m_pos[0] in range(285, 515) and m_pos[1] in range(355, 445):
                self.back_clicked = True

        if self.back_clicked and not pygame.mouse.get_pressed()[0]:
            self.game.resume_game()

    def update(self, dt: float) -> None:
        """Observe click bounds to process exit-pause requests."""
        self.interaction()
