"""
Handles 2D full-screen atmospheric post-processing overlays.
"""

import pygame

import settings.settings as settings


class AtmosphericOverlay:
    """
    Renders full-screen post-processing effects for volumetric immersion.
    """

    def __init__(self, screen: pygame.Surface) -> None:
        """
        Initializes the overlay surfaces for desaturation and tinting.
        """
        self.screen: pygame.Surface = screen
        
        # Screen-sized desaturation buffer
        self.washout: pygame.Surface = pygame.Surface(settings.SCREEN_RES)
        self.washout.fill(settings.HAZE_WASHOUT_RGB)
        
        # Screen-sized mist tint buffer
        self.tint: pygame.Surface = pygame.Surface(settings.SCREEN_RES)
        self.tint.fill(settings.HEIGHT_FOG_RGB)

    def draw_haze_submersion(self, submersion: float) -> None:
        """
        Applies atmospheric desaturation and tint based on player depth.
        """
        # Guard: Effect is invisible
        if submersion <= 0.01:
            return

        # 1. Neutralization Pass
        # Bleaches colors toward a neutral gray
        w_alpha: int = int(submersion * settings.HAZE_WASHOUT_STRENGTH * 255)
        self.washout.set_alpha(w_alpha)
        self.screen.blit(self.washout, (0, 0))

        # 2. Tint Pass
        # Overlays the glowing haze color
        t_alpha: int = int(submersion * 255)
        self.tint.set_alpha(t_alpha)
        self.screen.blit(self.tint, (0, 0))
