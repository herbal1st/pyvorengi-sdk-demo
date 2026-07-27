"""Adjusts difficulty properties before deploying ship."""
from __future__ import annotations
import typing
import pygame

import src.settings as settings

if typing.TYPE_CHECKING:
    from src.game import Game


class Options(pygame.sprite.Sprite):
    """Adjusts difficulty properties before deploying ship."""

    def __init__(self, game: Game) -> None:
        """Initialize options layouts, textures, and engine listings."""
        super().__init__()
        self.game: Game = game
        self.game_start_clicked: bool = False

        img_p: Path = settings.GRAPHICS_DIR / "ship" / "ship 33x33.png"
        img = pygame.image.load(str(img_p))
        self.image: pygame.Surface = pygame.transform.scale(
            img, (66, 66)
        ).convert_alpha()
        self.rect: pygame.Rect = self.image.get_rect(
            midtop=(
                settings.SCREEN_WIDTH // 2,
                settings.SCREEN_HEIGHT - 200,
            )
        )

        exh_p: Path = settings.GRAPHICS_DIR / "ship" / "exhaust"
        exhaust_list = [
            pygame.image.load(str(p))
            for p in sorted(exh_p.glob("*.png"))
        ]
        self.exhaust_list: list[pygame.Surface] = [
            pygame.transform.scale(img, (66, 66)).convert_alpha()
            for img in exhaust_list
        ]
        self.exhaust_index: float = 0.0

        dif_p: Path = (
            settings.GRAPHICS_DIR
            / "artwork"
            / "select difficulty.png"
        )
        self.difficulty: pygame.Surface = pygame.image.load(
            str(dif_p)
        ).convert_alpha()

        easy_p: Path = settings.GRAPHICS_DIR / "artwork" / "easy.png"
        self.easy: pygame.Surface = pygame.image.load(
            str(easy_p)
        ).convert_alpha()

        easy_on_p: Path = (
            settings.GRAPHICS_DIR / "artwork" / "easy on.png"
        )
        self.easy_selected: pygame.Surface = pygame.image.load(
            str(easy_on_p)
        ).convert_alpha()

        med_p: Path = settings.GRAPHICS_DIR / "artwork" / "medium.png"
        self.medium: pygame.Surface = pygame.image.load(
            str(med_p)
        ).convert_alpha()

        med_on_p: Path = (
            settings.GRAPHICS_DIR / "artwork" / "medium on.png"
        )
        self.medium_selected: pygame.Surface = pygame.image.load(
            str(med_on_p)
        ).convert_alpha()

        hard_p: Path = settings.GRAPHICS_DIR / "artwork" / "hard.png"
        self.hard: pygame.Surface = pygame.image.load(
            str(hard_p)
        ).convert_alpha()

        hard_on_p: Path = (
            settings.GRAPHICS_DIR / "artwork" / "hard on.png"
        )
        self.hard_selected: pygame.Surface = pygame.image.load(
            str(hard_on_p)
        ).convert_alpha()

        play_p: Path = (
            settings.GRAPHICS_DIR / "artwork" / "play game.png"
        )
        self.play_game: pygame.Surface = pygame.image.load(
            str(play_p)
        ).convert_alpha()

    def draw_extras(self, surface: pygame.Surface) -> None:
        """Renders difficulty layout selectors and dynamic exhausts."""
        exhaust_img = self.exhaust_list[int(self.exhaust_index)]
        surface.blit(
            exhaust_img, (self.rect.x, self.rect.y + 50)
        )

        if self.game.difficulty == settings.DIFFICULTY_EASY:
            surface.blit(self.easy_selected, (235, 255))
        else:
            surface.blit(self.easy, (235, 255))

        if self.game.difficulty == settings.DIFFICULTY_MEDIUM:
            surface.blit(self.medium_selected, (235, 360))
        else:
            surface.blit(self.medium, (235, 360))

        if self.game.difficulty == settings.DIFFICULTY_HARD:
            surface.blit(self.hard_selected, (235, 465))
        else:
            surface.blit(self.hard, (235, 465))

        surface.blit(self.difficulty, (0, 50))
        surface.blit(self.play_game, (140, 580))

    def interaction(self) -> None:
        """Observe mouse positions to process selections."""
        if pygame.mouse.get_pressed()[0]:
            m_pos = pygame.mouse.get_pos()
            if m_pos[0] in range(235, 565) and m_pos[1] in range(255, 345):
                self.game.difficulty = settings.DIFFICULTY_EASY
            if m_pos[0] in range(235, 565) and m_pos[1] in range(360, 450):
                self.game.difficulty = settings.DIFFICULTY_MEDIUM
            if m_pos[0] in range(235, 565) and m_pos[1] in range(465, 555):
                self.game.difficulty = settings.DIFFICULTY_HARD

            if m_pos[0] in range(140, 660) and m_pos[1] in range(580, 720):
                self.game_start_clicked = True

        if self.game_start_clicked and not pygame.mouse.get_pressed()[0]:
            self.game.start_game()

    def update(self, dt: float) -> None:
        """Calculate exhaust animation ticks and process selections."""
        self.exhaust_index += 30.0 * dt
        if self.exhaust_index >= len(self.exhaust_list):
            self.exhaust_index = 0.0
        self.interaction()
