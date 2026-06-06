"""
Manages the application display surface and hardware windowing states.
"""

import pygame
from settings import settings


class DisplayManager:
    """
    Handles initialization and modification of the Pygame display.
    """

    def __init__(self) -> None:
        """
        Sets up the initial display window based on global settings.
        """
        # Primary rendering surface
        self.screen: pygame.Surface = self._create_window(
            settings.START_FULLSCREEN
        )
        
        pygame.display.set_caption("PyVorengi SDK")

    def toggle_fullscreen(self, is_currently_fullscreen: bool) -> pygame.Surface:
        """
        Switches between windowed and fullscreen modes.
        """
        # Toggle based on the provided state
        new_state: bool = not is_currently_fullscreen
        self.screen = self._create_window(new_state)
        
        return self.screen

    def _create_window(self, use_fullscreen: bool) -> pygame.Surface:
        """
        Internal factory for the Pygame surface.
        """
        flags: int = pygame.FULLSCREEN if use_fullscreen else 0
        
        return pygame.display.set_mode(settings.SCREEN_RES, flags)
