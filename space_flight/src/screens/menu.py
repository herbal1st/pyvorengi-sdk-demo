"""Starting / landing main menu screen layout."""
from __future__ import annotations
import typing
import pygame

import src.settings as settings

if typing.TYPE_CHECKING:
    from src.game import Game


class StartingScreen(pygame.sprite.Sprite):
    """Initial landing main menu screen."""

    def __init__(self, game: Game) -> None:
        """Initialize graphics arrays and buttons of the landing page."""
        super().__init__()
        self.game: Game = game
        self.options_clicked: bool = False
        self.controls_clicked: bool = False
        self.highscores_clicked: bool = False
        self.game.score = 0

        title_p: Path = (
            settings.GRAPHICS_DIR / "artwork" / "game title.png"
        )
        self.image: pygame.Surface = pygame.image.load(
            str(title_p)
        ).convert_alpha()
        self.rect: pygame.Rect = self.image.get_rect(topleft=(0, 0))

        start_p: Path = settings.GRAPHICS_DIR / "artwork" / "start.png"
        self.start_game: pygame.Surface = pygame.image.load(
            str(start_p)
        ).convert_alpha()

        ctrl_p: Path = settings.GRAPHICS_DIR / "artwork" / "controls.png"
        self.controls: pygame.Surface = pygame.image.load(
            str(ctrl_p)
        ).convert_alpha()

        scores_p: Path = (
            settings.GRAPHICS_DIR / "artwork" / "highscores.png"
        )
        self.highscores: pygame.Surface = pygame.image.load(
            str(scores_p)
        ).convert_alpha()

        quit_p: Path = settings.GRAPHICS_DIR / "artwork" / "quit.png"
        self.quit: pygame.Surface = pygame.image.load(
            str(quit_p)
        ).convert_alpha()

    def draw_extras(self, surface: pygame.Surface) -> None:
        """Renders overlay main menu interactive buttons."""
        surface.blit(self.start_game, (120, 345))
        surface.blit(self.controls, (120, 450))
        surface.blit(self.highscores, (120, 555))
        surface.blit(self.quit, (120, 660))

    def interaction(self) -> None:
        """Route click coordinates to distinct layout transitions."""
        if pygame.mouse.get_pressed()[0]:
            m_pos = pygame.mouse.get_pos()
            if m_pos[0] in range(120, 680) and m_pos[1] in range(345, 435):
                self.options_clicked = True
            if m_pos[0] in range(120, 680) and m_pos[1] in range(450, 540):
                self.controls_clicked = True
            if m_pos[0] in range(120, 680) and m_pos[1] in range(555, 645):
                self.highscores_clicked = True
            if m_pos[0] in range(120, 680) and m_pos[1] in range(660, 750):
                self.game.shutdown()

        if self.options_clicked and not pygame.mouse.get_pressed()[0]:
            self.game.transition_to("options")

        if self.controls_clicked and not pygame.mouse.get_pressed()[0]:
            self.game.transition_to("controls")

        if self.highscores_clicked and not pygame.mouse.get_pressed()[0]:
            self.game.transition_to("highscores")

    def update(self, dt: float) -> None:
        """Detect and route click events on primary menu options."""
        self.interaction()
