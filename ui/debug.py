"""
Optimized telemetry overlay using surface memoization and static caching.
"""

from collections import deque
from typing import Deque, Final, List, Tuple, TYPE_CHECKING, Optional

import pygame

from controls import keymap
from settings import settings

if TYPE_CHECKING:
    from physics.entity import Entity
    from session.atmosphere import AtmosphereManager


class DebugView:
    """
    Renders pre-baked and memoized UI panels for maximum performance.
    """

    def __init__(self, screen: pygame.Surface) -> None:
        """
        Initializes fonts and pre-renders the static legend surface.
        """
        from settings import settings

        self.screen: pygame.Surface = screen
        self._padding: Final[int] = 10
        self._line_h: Final[int] = 22
        self._bg_alpha: int = settings.UI_BG_ALPHA
        self._panel_gap: Final[int] = 8

        self.font: pygame.font.Font = pygame.font.SysFont(
            "monospace", 18, bold=True
        )

        self.history: Deque[float] = deque(maxlen=350)
        self._legend_surf: pygame.Surface = self._build_legend_surface()
        self._metric_surf: Optional[pygame.Surface] = None

    def render(
        self,
        player: "Entity",
        atmo: "AtmosphereManager",
        fps: int,
        frame_ms: float,
        active_faces: int,
        visible_sections: int,
        total_sections: int,
        refresh: bool
    ) -> None:
        """
        Blits pre-composed textures to the screen.
        """
        if refresh or self._metric_surf is None:
            self._metric_surf = self._rebuild_metric_surface(
                player, atmo, fps, active_faces, 
                visible_sections, total_sections
            )

        m_x, m_y = 5, 5
        self.screen.blit(self._metric_surf, (m_x, m_y))

        l_x: int = m_x + self._metric_surf.get_width() + self._panel_gap
        self.screen.blit(self._legend_surf, (l_x, m_y))

        self._draw_graph(frame_ms)

    def _rebuild_metric_surface(
        self,
        player: "Entity",
        atmo: "AtmosphereManager",
        fps: int,
        active_faces: int,
        v_secs: int,
        t_secs: int
    ) -> pygame.Surface:
        """
        Formats metrics and bakes them into a single texture.
        """
        px, py, pz = player.position
        thru: float = (active_faces * fps) / 1000.0 if active_faces > 0 else 0.0
        mode: str = settings.FOG_MODE

        if settings.FOG_MODE == settings.FOG_MODE_EXP:
            mode = f"EXP {settings.FOG_EXPONENT:.1f}"

        lines: List[str] = [
            f"FPS:  {fps}",
            f"VIEW: {atmo.render_dist:0.1f} BLOCKS",
            "---------------------",
            f"X COORDS: {px:0.1f}",
            f"Y COORDS: {py:0.1f}",
            f"Z COORDS: {pz:0.1f}",
            "---------------------",
            f"FOG MODE:  {mode}",
            f"FOG DENS:  {atmo.fog_density:.3f}",
            f"HAZE LOCN: {atmo.h_fog_max_z:.2f}",
            f"HAZE DENS: {atmo.h_fog_dens:.3f}",
            f"HAZE FADE: {atmo.h_fog_fade:0.2f}",
            f"LUMA:      {atmo.height_shading_factor:.2f}",
            "---------------------",
            f"# CHUNKS: {v_secs}/{t_secs}",
            f"# FACES:  {active_faces:,}",
            f"THRUPUT:  {thru:0.2f} k/s"
        ]
        return self._create_panel_texture(lines)

    def _build_legend_surface(self) -> pygame.Surface:
        """
        Constructs the static control legend panel.
        """
        lines: List[str] = [""] * 8
        lines[1] = "MOVE: W/A/S/D | ARROWS"
        lines[2] = "ELEV: PGUP | PGDN"
        lines[3] = f"QUIT: {self._get_keys(keymap.QUIT_APP)}"
        lines[4] = f"FOG:  {self._get_keys(keymap.TOGGLE_FOG_MODE)}"
        lines[5] = f"FS:   {self._get_keys(keymap.TOGGLE_FULLSCREEN)}"
        lines[6] = f"DBUG: {self._get_keys(keymap.TOGGLE_DEBUG)}"
        lines[7] = f"PAUS: {self._get_keys(keymap.TOGGLE_PAUSE)}"

        return self._create_panel_texture(lines)

    def _get_keys(self, act_pos: str, act_neg: Optional[str] = None) -> str:
        """
        Extracts and formats key names from the logic keymap.
        """
        def _n(a: str) -> str:
            k = keymap.BINDINGS.get(a, [])
            return pygame.key.name(k[0]).upper() if k else "?"
        return f"{_n(act_pos)} | {_n(act_neg)}" if act_neg else _n(act_pos)

    def _create_panel_texture(self, lines: List[str]) -> pygame.Surface:
        """
        Bakes text lines into an optimized per-pixel alpha surface.
        """
        valid_w = [self.font.size(ln)[0] for ln in lines if ln.strip()]
        max_w: int = max(valid_w) if valid_w else 50

        tw: int = max_w + (self._padding * 2)
        th: int = (len(lines) * self._line_h) + self._padding

        surf: pygame.Surface = pygame.Surface((tw, th), pygame.SRCALPHA)
        surf.fill((20, 20, 20, self._bg_alpha))
        pygame.draw.rect(surf, (100, 100, 100), (0, 0, tw, th), 1)

        for i, line in enumerate(lines):
            if not line:
                continue
            y = (self._padding // 2) + (i * self._line_h)
            
            s_img = self.font.render(line, True, (0, 0, 0))
            surf.blit(s_img, (self._padding + 2, y + 2))
            
            t_img = self.font.render(line, True, (255, 255, 255))
            surf.blit(t_img, (self._padding, y))

        return surf

    def _draw_graph(self, ms: float) -> None:
        """
        Renders the latency graph with alpha blending.
        """
        self.history.append(ms)
        if len(self.history) < 2:
            return

        xb, yb = 5, self.screen.get_height() - 100
        gw, gh = 350, 90

        bg = pygame.Surface((gw, gh), pygame.SRCALPHA)
        bg.fill((20, 20, 20, self._bg_alpha))
        self.screen.blit(bg, (xb, yb))
        pygame.draw.rect(self.screen, (100, 100, 100), (xb, yb, gw, gh), 1)

        for m, c in [(16.6, (0, 180, 0)), (33.3, (180, 180, 0))]:
            y = yb + gh - int((m / 60.0) * gh)
            pygame.draw.line(self.screen, c, (xb, y), (xb + gw, y))

        pts = [
            (xb + i, yb + gh - int((min(m, 60) / 60) * gh)) 
            for i, m in enumerate(self.history)
        ]
        pygame.draw.lines(self.screen, (255, 80, 80), False, pts, 1)

        pk_txt = f"Peak: {max(self.history):.1f}ms"
        pk_img = self.font.render(pk_txt, True, (255, 255, 180))
        self.screen.blit(pk_img, (xb + 5, yb + 2))
