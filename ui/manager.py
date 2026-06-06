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
        total_sections: int
    ) -> None:
        """
        Dispatches drawing calls with strict temporal throttling.
        """
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
