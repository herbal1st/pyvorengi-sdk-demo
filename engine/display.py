"""
Manages the application display surface and hardware windowing states.
"""

from pathlib import Path
import pygame
from settings import settings
from utils.paths import PROJECT_ROOT


class DisplayManager:
    """
    Handles initialization and modification of the Pygame display.
    """

    def __init__(self) -> None:
        """
        Sets up the initial display window and application branding.
        """
        # Primary rendering surface
        self.screen: pygame.Surface = self._create_window(
            settings.START_FULLSCREEN
        )
        
        pygame.display.set_caption("PyVorengi SDK")
        self._apply_window_icon()

    def toggle_fullscreen(self, is_currently_fullscreen: bool) -> pygame.Surface:
        """
        Switches between windowed and fullscreen modes.
        """
        new_state: bool = not is_currently_fullscreen
        self.screen = self._create_window(new_state)
        
        return self.screen

    def _apply_window_icon(self) -> None:
        """
        Loads and sets the window icon from the project root.
        """
        icon_path: Path = PROJECT_ROOT / settings.WINDOW_ICON_NAME
        
        # Guard: Icon file missing
        if not icon_path.exists():
            return

        try:
            icon_surf: pygame.Surface = pygame.image.load(str(icon_path))
            pygame.display.set_icon(icon_surf)
        except Exception as error:
            print(f"[Display] Failed to load window icon: {error}")

    def _create_window(self, use_fullscreen: bool) -> pygame.Surface:
        """
        Internal factory for the Pygame surface.
        """
        flags: int = pygame.FULLSCREEN if use_fullscreen else 0
        
        return pygame.display.set_mode(settings.SCREEN_RES, flags)
