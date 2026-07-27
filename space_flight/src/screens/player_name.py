"""Accepts alphabetical entries upon securing a highscore place."""
from __future__ import annotations
import typing
from pathlib import Path
import pygame

import src.settings as settings

if typing.TYPE_CHECKING:
    from src.game import Game


class PlayerName(pygame.sprite.Sprite):
    """Accepts alphabetical entries upon securing a highscore place."""

    def __init__(self, game: Game) -> None:
        """Initialize placement directories and dynamic layouts."""
        super().__init__()
        self.game: Game = game
        self.submit_clicked: bool = False
        
        # Guard flag preventing instant click carry-over on state transitions
        self.nothing_clicked: bool = False

        over_p: Path = settings.GRAPHICS_DIR / "artwork" / "game over.png"
        self.image: pygame.Surface = pygame.image.load(
            str(over_p)
        ).convert_alpha()
        self.rect: pygame.Rect = self.image.get_rect(topleft=(0, 100))

        hs_p: Path = (
            settings.GRAPHICS_DIR / "artwork" / "new highscore.png"
        )
        self.new_highscore: pygame.Surface = pygame.image.load(
            str(hs_p)
        ).convert_alpha()

        ent_n_p: Path = (
            settings.GRAPHICS_DIR / "artwork" / "enter name.png"
        )
        self.enter_name: pygame.Surface = pygame.image.load(
            str(ent_n_p)
        ).convert_alpha()

        ent_p: Path = settings.GRAPHICS_DIR / "artwork" / "enter.png"
        self.enter: pygame.Surface = pygame.image.load(
            str(ent_p)
        ).convert_alpha()

    def draw_extras(self, surface: pygame.Surface) -> None:
        """Renders overlay key input letters and verification interfaces."""
        surface.blit(self.new_highscore, (35, 260))
        surface.blit(self.enter_name, (25, 360))
        surface.blit(self.enter, (250, 640))

        # Toggle cursor visibility every 500ms using modulo system ticks
        show_cursor: bool = (pygame.time.get_ticks() // 500) % 2 == 0
        cursor_char: str = "|" if show_cursor else ""
        display_name: str = f"{self.game.player_name}{cursor_char}"

        render_name: pygame.Surface = self.game.font_3.render(
            display_name, True, (140, 255, 251)
        )
        x_pos: float = (
            settings.SCREEN_WIDTH / 2 - render_name.get_width() / 2
        )
        surface.blit(render_name, (x_pos, 495))
        pygame.draw.rect(
            surface, (140, 255, 251), (175, 493, 454, 94), 2
        )

    def interaction(self) -> None:
        """Observe mouse coordinates to submit score entries."""
        # Click Guard: only enable clicks once the mouse has been fully released
        if not pygame.mouse.get_pressed()[0]:
            self.nothing_clicked = True

        if self.nothing_clicked:
            if pygame.mouse.get_pressed()[0]:
                m_pos = pygame.mouse.get_pos()
                if (
                    m_pos[0] in range(285, 515)
                    and m_pos[1] in range(640, 730)
                ):
                    self.submit_clicked = True

        if self.submit_clicked and not pygame.mouse.get_pressed()[0]:
            self.game.place_highscore(
                self.game.player_name,
                self.game.score,
                self.game.difficulty,
            )
            self.game.transition_to("start")

    def update(self, dt: float) -> None:
        """Detect submission validation click interactions."""
        self.interaction()
