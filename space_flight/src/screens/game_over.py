"""The game over scoring scoreboard interface."""
from __future__ import annotations
import typing
import pygame

import src.settings as settings

if typing.TYPE_CHECKING:
    from src.game import Game


class GameOver(pygame.sprite.Sprite):
    """The game over scoring scoreboard interface."""

    def __init__(self, game: Game) -> None:
        """Initialize labels, game states, and fade out system audio."""
        super().__init__()
        self.game: Game = game
        self.nothing_clicked: bool = False
        self.back_clicked: bool = False

        over_p: Path = settings.GRAPHICS_DIR / "artwork" / "game over.png"
        self.image: pygame.Surface = pygame.image.load(
            str(over_p)
        ).convert_alpha()
        self.rect: pygame.Rect = self.image.get_rect(topleft=(0, 100))

        score_p: Path = (
            settings.GRAPHICS_DIR / "artwork" / "final score.png"
        )
        self.final_score: pygame.Surface = pygame.image.load(
            str(score_p)
        ).convert_alpha()

        back_p: Path = settings.GRAPHICS_DIR / "artwork" / "back.png"
        self.back: pygame.Surface = pygame.image.load(
            str(back_p)
        ).convert_alpha()

        self.game.sound_game_music.fadeout(2000)
        self.game.sound_menu_music.play(loops=-1, fade_ms=2000)

    def draw_extras(self, surface: pygame.Surface) -> None:
        """Render score details and navigation back buttons."""
        surface.blit(self.final_score, (0, 310))
        surface.blit(self.back, (285, 640))
        score_str: str = str(self.game.score)
        score_x: float = settings.SCREEN_WIDTH / 2 - len(score_str) * 12
        surface.blit(
            self.game.font_3.render(score_str, True, (140, 255, 251)),
            (score_x, 450),
        )

    def interaction(self) -> None:
        """Route click bounds to score input or menu lists."""
        if not pygame.mouse.get_pressed()[0]:
            self.nothing_clicked = True
        if self.nothing_clicked:
            if pygame.mouse.get_pressed()[0]:
                m_pos = pygame.mouse.get_pos()
                if (
                    m_pos[0] in range(285, 515)
                    and m_pos[1] in range(640, 730)
                ):
                    self.back_clicked = True

        if self.back_clicked and not pygame.mouse.get_pressed()[0]:
            if self.game.test_highscore(
                self.game.score, self.game.difficulty
            ):
                self.game.transition_to("input name")
            else:
                self.game.transition_to("start")

    def update(self, dt: float) -> None:
        """Evaluate submission events and back clicks."""
        self.interaction()
