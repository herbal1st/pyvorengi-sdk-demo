"""
Orchestration layer for user interface components with temporal throttling.
"""

from typing import TYPE_CHECKING

import pygame

from ui.debug import DebugView

if TYPE_CHECKING:
    from engine.clock import EngineClock
    from session.atmosphere import AtmosphereManager
    from statemanager.statemanager import StateManager


class UIManager:
    """
    Handles visibility and throttled updates for all 2D engine overlays.
    """

    def __init__(self, screen: pygame.Surface) -> None:
        """
        Initializes UI sub-components and the refresh timer.
        """
        from settings import settings

        self.screen: pygame.Surface = screen
        self.debug: DebugView = DebugView(screen)
        
        # Establish font for permanent UI elements
        self.font: pygame.font.Font = pygame.font.SysFont(
            "monospace", 18, bold=True
        )

        # Rate at which numbers (FPS, Coords) are recalculated
        self._refresh_rate_ms: int = settings.UI_REFRESH_RATE_MS
        self._last_refresh: int = 0

        # Cached values to prevent formatting every frame
        self._cached_fps: int = 0
        self._cached_ms: float = 0.0

    def draw(
        self,
        state: "StateManager",
        player_ref: any,
        atmo_ref: "AtmosphereManager",
        clock_ref: "EngineClock",
        active_faces: int,
        visible_sections: int,
        total_sections: int,
        current_build_id: int = 0,
    ) -> None:
        """
        Dispatches drawing calls with strict temporal throttling.
        """
        if state.is_playing:
            self._draw_crosshair()
            self._draw_block_indicator(current_build_id)

        if not state.show_debug:
            return

        now: int = pygame.time.get_ticks()
        is_dirty: bool = False

        # Threshold check for expensive string formatting
        if (now - self._last_refresh) > self._refresh_rate_ms:
            self._cached_fps = int(clock_ref.get_fps())
            self._cached_ms = float(clock_ref.get_time_ms())
            self._last_refresh = now
            # Signals DebugView to rebuild the text texture
            is_dirty = True

        self.debug.render(
            player=player_ref,
            atmo=atmo_ref,
            fps=self._cached_fps,
            frame_ms=self._cached_ms,
            active_faces=active_faces,
            visible_sections=visible_sections,
            total_sections=total_sections,
            refresh=is_dirty
        )

    def update_screen_reference(self, new_screen: pygame.Surface) -> None:
        """
        Propagates screen surface updates to all UI elements.
        """
        self.screen = new_screen
        self.debug.screen = new_screen

    def _draw_crosshair(self) -> None:
        """
        Renders a simple targeting cross at the center of the screen.
        """
        center_x: int = self.screen.get_width() // 2
        center_y: int = self.screen.get_height() // 2
        size: int = 6
        color = (255, 255, 255)

        # Horizontal line
        pygame.draw.line(
            self.screen, color,
            (center_x - size, center_y),
            (center_x + size, center_y),
            1
        )
        # Vertical line
        pygame.draw.line(
            self.screen, color,
            (center_x, center_y - size),
            (center_x, center_y + size),
            1
        )

    def _draw_block_indicator(self, build_id: int) -> None:
        """
        Draws a semi-transparent HUD circle indicating the selected block.
        """
        radius: int = 24
        padding: int = 40

        # Calculate bottom-right positioning dynamically
        cx: int = self.screen.get_width() - radius - padding
        cy: int = self.screen.get_height() - radius - padding

        # Temporary surface configured with alpha channel transparency
        temp_surf = pygame.Surface(
            (radius * 2, radius * 2), pygame.SRCALPHA
        )

        # Semi-transparent background (R, G, B, A)
        bg_color = (20, 20, 20, 140)
        pygame.draw.circle(
            temp_surf, bg_color, (radius, radius), radius
        )

        # Subtle dark border
        outline_color = (100, 100, 100, 200)
        pygame.draw.circle(
            temp_surf, outline_color, (radius, radius), radius, 1
        )

        # Blit the combined alpha layer to target screen coordinate
        self.screen.blit(temp_surf, (cx - radius, cy - radius))

        # Render centered numerical text overlay
        text_str: str = str(build_id)
        t_img = self.font.render(text_str, True, (255, 255, 255))
        tx: int = cx - (t_img.get_width() // 2)
        ty: int = cy - (t_img.get_height() // 2)
        self.screen.blit(t_img, (tx, ty))
