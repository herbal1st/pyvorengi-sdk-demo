"""Displays local leaderboards stored across files."""
from __future__ import annotations
import typing
import pygame

import src.settings as settings

if typing.TYPE_CHECKING:
    from src.game import Game


class Highscores(pygame.sprite.Sprite):
    """Displays local leaderboards stored across files."""

    def __init__(self, game: Game) -> None:
        """Initialize visual arrows, layouts, and load data lists."""
        super().__init__()
        self.game: Game = game
        self.show: str = "medium"
        self.back_clicked: bool = False
        self.left_clicked: bool = False
        self.right_clicked: bool = False

        easy_p: Path = settings.GRAPHICS_DIR / "artwork" / "easy title.png"
        med_p: Path = settings.GRAPHICS_DIR / "artwork" / "medium title.png"
        hard_p: Path = settings.GRAPHICS_DIR / "artwork" / "hard title.png"

        self.title_images: dict[str, pygame.Surface] = {
            "easy": pygame.image.load(str(easy_p)).convert_alpha(),
            "medium": pygame.image.load(str(med_p)).convert_alpha(),
            "hard": pygame.image.load(str(hard_p)).convert_alpha(),
        }
        self.image: pygame.Surface = self.title_images[self.show]
        img_w: int = self.image.get_width()
        self.rect: pygame.Rect = self.image.get_rect(
            topleft=(settings.SCREEN_WIDTH / 2 - img_w / 2, 25)
        )

        arr_l_p: Path = (
            settings.GRAPHICS_DIR / "artwork" / "arrow left.png"
        )
        self.arrow_left: pygame.Surface = pygame.image.load(
            str(arr_l_p)
        ).convert_alpha()

        arr_r_p: Path = (
            settings.GRAPHICS_DIR / "artwork" / "arrow right.png"
        )
        self.arrow_right: pygame.Surface = pygame.image.load(
            str(arr_r_p)
        ).convert_alpha()

        back_p: Path = settings.GRAPHICS_DIR / "artwork" / "back.png"
        self.back: pygame.Surface = pygame.image.load(
            str(back_p)
        ).convert_alpha()

        self.names: list[str] = []
        self.scores: list[str] = []
        self.change_site()

    def draw_extras(self, surface: pygame.Surface) -> None:
        """Render leaderboard visual guidelines, arrows, and listings."""
        if self.show in ("medium", "hard"):
            surface.blit(self.arrow_left, (0, 300))
        if self.show in ("medium", "easy"):
            surface.blit(self.arrow_right, (720, 300))
        surface.blit(self.back, (285, 640))

        pygame.draw.rect(
            surface, (140, 255, 251), (100, 178, 604, 434), 2
        )
        pygame.draw.line(
            surface, (140, 255, 251), (400, 180), (400, 610), 2
        )

        for y_pos, name in enumerate(self.names[1:11]):
            surface.blit(
                self.game.font_1.render(name, True, (14, 209, 69)),
                (220, 190 + y_pos * 42),
            )
            if y_pos < 9:
                pygame.draw.line(
                    surface,
                    (140, 255, 251),
                    (100, 222 + y_pos * 42),
                    (700, 222 + y_pos * 42),
                )

        for y_pos, number in enumerate(self.scores[1:11]):
            x_pos: float = 550 - len(number) * 7 / 2
            surface.blit(
                self.game.font_1.render(number, True, (14, 209, 69)),
                (x_pos, 190 + y_pos * 42),
            )

    def interaction(self) -> None:
        """Route click bounds to difficulty list changes."""
        if pygame.mouse.get_pressed()[0]:
            m_pos = pygame.mouse.get_pos()
            if m_pos[0] in range(0, 80) and m_pos[1] in range(300, 435):
                self.left_clicked = True

        if (
            self.left_clicked
            and not pygame.mouse.get_pressed()[0]
        ):
            if self.show == "hard":
                self.show = "medium"
                self.change_site()
            elif self.show == "medium":
                self.show = "easy"
                self.change_site()
            self.left_clicked = False

        if pygame.mouse.get_pressed()[0]:
            m_pos = pygame.mouse.get_pos()
            if m_pos[0] in range(720, 800) and m_pos[1] in range(300, 435):
                self.right_clicked = True

        if (
            self.right_clicked
            and not pygame.mouse.get_pressed()[0]
        ):
            if self.show == "easy":
                self.show = "medium"
                self.change_site()
            elif self.show == "medium":
                self.show = "hard"
                self.change_site()
            self.right_clicked = False

        if pygame.mouse.get_pressed()[0]:
            m_pos = pygame.mouse.get_pos()
            if m_pos[0] in range(285, 515) and m_pos[1] in range(640, 730):
                self.back_clicked = True

        if self.back_clicked and not pygame.mouse.get_pressed()[0]:
            self.game.transition_to("start")

    def change_site(self) -> None:
        """Update visual titles and open name/score directories."""
        self.image = self.title_images[self.show]
        img_w: int = self.image.get_width()
        self.rect = self.image.get_rect(
            topleft=(settings.SCREEN_WIDTH / 2 - img_w / 2, 25)
        )

        n_p: Path = settings.HIGHSCORES_DIR / f"{self.show} names.txt"
        with open(n_p, "r") as f:
            self.names = "".join(f.readlines()).split()

        s_p: Path = settings.HIGHSCORES_DIR / f"{self.show} scores.txt"
        with open(s_p, "r") as f:
            self.scores = "".join(f.readlines()).split()

    def update(self, dt: float) -> None:
        """Handle difficulty list scrolling and back interactions."""
        self.interaction()
