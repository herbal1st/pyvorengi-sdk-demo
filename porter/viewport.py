"""Orchestrates hybrid 2D and 3D rendering for ported game elements."""

import math
from pathlib import Path
import time
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pygame
from numpy.typing import NDArray

from constants.constants import HALF_WIDTH, HALF_HEIGHT
from porter.assets import AssetCache, VoxelAsset
from porter.registry import PorterRegistry, get_qualified_key
from porter.translator import CoordinateTranslator
from porter.porter_settings import (
    PORTER_Z_ATTACHMENT_OFFSET,
    PORTER_OVERLAYS_TOP,
    PORTER_OVERLAYS_MID,
    PORTER_PERSPECTIVE_PARALLAX_ON,
    PORTER_CAMERA_HEIGHT,
)
from renderer.projection import project_vertices
from renderer.visuals import apply_visual_effects

ParentState = Tuple[Tuple[float, float, float], float, float, float]


class VoxelSurface:
    """Proxy class that intercepts blits on the primary screen surface."""

    def __init__(self, surface: pygame.Surface, viewport: Any) -> None:
        """Initializes the surface proxy wrapping the display window."""
        self._surface = surface
        self._viewport = viewport

    def __getattr__(self, name: str) -> Any:
        """Delegates standard operations directly to Pygame's C surface."""
        return getattr(self._surface, name)

    def blit(
        self,
        source: pygame.Surface,
        dest: Any,
        area: Any = None,
        special_flags: int = 0
    ) -> pygame.Rect:
        """Intercepts raw blits to check for 3D visual redirection."""
        source_path = getattr(source, "_source_path", None)

        if isinstance(dest, pygame.Rect):
            center_pos = dest.center
        elif isinstance(dest, (tuple, list)) and len(dest) >= 2:
            w, h = source.get_size()
            center_pos = (dest[0] + w // 2, dest[1] + h // 2)
        else:
            center_pos = (0, 0)

        if source_path and self._viewport.draw_actor(
            id(source), source_path, center_pos,
            source_surf=source, dest_rect=dest
        ):
            return pygame.Rect(0, 0, 0, 0)

        if source_path:
            is_overlay_top = any(
                k in source_path for k in PORTER_OVERLAYS_TOP
            )
            is_overlay_mid = any(
                k in source_path for k in PORTER_OVERLAYS_MID
            )
            if is_overlay_top or is_overlay_mid:
                self._viewport.pending_2d_overlays.append(
                    (source, dest, area, special_flags, source_path)
                )
                return pygame.Rect(0, 0, 0, 0)

        return self._surface.blit(source, dest, area, special_flags)

    def blits(
        self,
        blit_sequence: Any,
        d_args: Any = None,
        **kwargs: Any
    ) -> List[pygame.Rect]:
        """Intercepts and unpacks batched 2D blits to protect 3D routing."""
        rects: List[pygame.Rect] = []
        for item in blit_sequence:
            source = item[0]
            dest = item[1]
            area = item[2] if len(item) > 2 else None
            special_flags = item[3] if len(item) > 3 else 0

            rects.append(
                self.blit(source, dest, area, special_flags)
            )
        return rects


class PortViewport:
    """Intercepts draw calls to render them in hybrid 2.5D space."""

    def __init__(
        self,
        screen: pygame.Surface,
        screen_w: float,
        screen_h: float
    ) -> None:
        """Initializes the viewport with rendering subsystems."""
        self.screen: pygame.Surface = screen
        self.registry: PorterRegistry = PorterRegistry()
        self.translator: CoordinateTranslator = CoordinateTranslator(
            screen_w, screen_h
        )
        self.assets: AssetCache = AssetCache()
        
        self.pending_3d_parents: List[Tuple] = []
        self.pending_3d_attachments: List[Tuple] = []
        self.pending_2d_overlays: List[Tuple] = []
        self.pending_vector_draws: List[Tuple] = []

        self.active_parent_id: Optional[int] = None

        self._last_time: float = time.perf_counter()
        self._fps_font: Optional[pygame.font.Font] = None

        self._smoothed_fps: Optional[float] = None
        self._fps_history: List[Tuple[float, float]] = []

        # Pre-warm all registered 3D voxel models before Frame 1
        self.assets.warm_up_cache(self.registry)

    def clear(self) -> None:
        """Clears the screen and pending drawing queues."""
        self.screen.fill((0, 0, 0))
        self.pending_3d_parents.clear()
        self.pending_3d_attachments.clear()
        self.pending_2d_overlays.clear()
        self.pending_vector_draws.clear()
        self.active_parent_id = None
        self.translator.start_frame()

    def draw_actor(
        self,
        actor: Any,
        sprite_path: str,
        position: Tuple[float, float],
        angle: float = 0.0,
        source_surf: Optional[pygame.Surface] = None,
        dest_rect: Optional[pygame.Rect] = None,
    ) -> bool:
        """Intercepts a sprite drawing call. Returns True if handled in 3D."""
        mapping = self.registry.get_mapping(sprite_path)
        if not mapping:
            return False

        # TYPE-BASED ROUTING DISCRIMINATOR
        if not isinstance(actor, int):
            # --- PARENT PIPELINE ---
            # Triggered when actor is a Sprite instance (Group.draw)
            if mapping.get("render_3d", False):
                scale: float = mapping.get("scale", 1.0)
                z_offset: float = 1.0
                pos_3d = self.translator.to_3d_coords(
                    position[0], position[1], z_offset
                )
                npz_filename = str(Path(sprite_path).with_suffix(".npz"))
                asset = self.assets.get_asset(npz_filename, mapping)
                
                if asset.faces.size == 0:
                    return False

                self.pending_3d_parents.append(
                    (actor, asset, pos_3d, angle, scale)
                )
                return True
        else:
            # --- ATTACHMENT PIPELINE ---
            # Triggered when actor is an integer ID (VoxelSurface.blit)
            is_overlay_top = any(k in sprite_path for k in PORTER_OVERLAYS_TOP)
            is_overlay_mid = any(k in sprite_path for k in PORTER_OVERLAYS_MID)
            has_z_config = mapping.get("z_offset") is not None

            if is_overlay_top or is_overlay_mid or has_z_config:
                pos_3d = self.translator.to_3d_coords(
                    position[0], position[1], 1.0
                )
                npz_filename = str(Path(sprite_path).with_suffix(".npz"))
                asset = self.assets.get_asset(npz_filename, mapping)

                if asset.faces.size == 0:
                    return False

                self.pending_3d_attachments.append(
                    (sprite_path, asset, pos_3d, angle, mapping,
                     source_surf, dest_rect, self.active_parent_id)
                )
                return True

        return False

    def render_3d_layer(
        self,
        cam_pos: NDArray[np.float64],
        yaw: float,
        pitch: float,
        fov: float
    ) -> None:
        """Projects, sorts, shades, and draws all queued 3D geometry."""
        if not self.pending_3d_parents:
            # Process remaining 3D attachments as standard 2D overlays
            for item in self.pending_3d_attachments:
                (
                    path, c_asset, c_pos, c_angle,
                    c_map, s_surf, d_rect, p_id
                ) = item
                if s_surf is not None and d_rect is not None:
                    self.pending_2d_overlays.append(
                        (s_surf, d_rect, None, 0, path)
                    )
            self.pending_3d_attachments.clear()

            # Precheck: skip loop iterations if no 2D layers are queued
            if self.pending_2d_overlays or self.pending_vector_draws:
                for source, dest, area, special_flags, s_path in (
                    self.pending_2d_overlays
                ):
                    self.screen.blit(source, dest, area, special_flags)

                for draw_func, target_surf, d_args, d_kwargs in (
                    self.pending_vector_draws
                ):
                    draw_func(target_surf, *d_args, **d_kwargs)

                self.pending_2d_overlays.clear()
                self.pending_vector_draws.clear()

            self.translator.prune_inactive()
            self._render_diagnostic_fps()
            return

        all_faces_list: List[NDArray[np.float32]] = []
        parent_map: Dict[int, ParentState] = {}

        for actor, asset, pos_3d, angle, scale in self.pending_3d_parents:
            # Retrieve specific custom YAML mapping for the parent
            sprite_path = getattr(actor.image, "_source_path", "")
            mapping = self.registry.get_mapping(sprite_path) or {}
            
            p_tilt_factor: float = float(mapping.get("tilt_factor", 0.0))
            p_tilt_agility: float = float(mapping.get("tilt_agility", 1.0))

            tilt_rad = self.translator.get_passive_tilt_rad(
                id(actor),
                pos_3d[0] * 25.0,
                self.translator.sh - (pos_3d[1] * 25.0),
                p_tilt_factor,
                p_tilt_agility
            )
            parent_map[id(actor)] = (pos_3d, angle, tilt_rad, asset.depth)

        for actor, p_asset, p_pos, p_angle, p_scale in self.pending_3d_parents:
            p_pos_3d, p_angle, p_tilt, p_depth = parent_map[id(actor)]
            faces_to_stitch: List[NDArray[np.float32]] = [p_asset.faces.copy()]

            for item in self.pending_3d_attachments[:]:
                path, c_asset, c_pos, c_angle, c_map, s_surf, d_rect, p_id = item
                
                # Strict parenting check: strictly matches explicit IDs
                belongs: bool = False
                if p_id is not None:
                    belongs = (p_id == id(actor))

                if not belongs:
                    continue

                self.pending_3d_attachments.remove(item)
                
                dx: float = c_pos[0] - p_pos_3d[0]
                dy: float = c_pos[1] - p_pos_3d[1]

                rad: float = math.radians(-p_angle) + math.pi
                cos_r, sin_r = math.cos(rad), math.sin(rad)
                
                rx: float = dx
                ry: float = dy

                local_x: float = -(rx * cos_r + ry * sin_r)
                local_y: float = -rx * sin_r + ry * cos_r

                transform_scale: float = p_scale / self.translator.scale_factor
                
                local_x = local_x / transform_scale
                local_y = local_y / transform_scale

                cfg_z: Optional[float] = c_map.get("z_offset", None)
                if cfg_z is not None:
                    local_z = float(cfg_z)
                else:
                    is_top = any(k in path for k in PORTER_OVERLAYS_TOP)
                    is_mid = any(k in path for k in PORTER_OVERLAYS_MID)
                    if is_top:
                        local_z = p_depth
                    elif is_mid:
                        local_z = p_depth / 2.0
                    else:
                        local_z = p_depth

                local_z += PORTER_Z_ATTACHMENT_OFFSET / transform_scale

                child_faces = c_asset.faces.copy()
                child_half_x: float = c_asset.width / 2.0
                child_half_y: float = c_asset.height / 2.0
                child_half_z: float = (
                    c_asset.depth 
                    if c_asset.is_flat 
                    else (c_asset.depth / 2.0)
                )

                # Pre-scale child geometry to maintain absolute YAML scaling
                c_scale: float = float(c_map.get("scale", 1.0))
                p_scale_safe: float = max(1e-5, float(p_scale))
                ratio: float = c_scale / p_scale_safe

                for i in range(4):
                    col = i * 3
                    child_faces[:, col] = (
                        (child_faces[:, col] - child_half_x) * ratio 
                        + child_half_x
                    )
                    child_faces[:, col + 1] = (
                        (child_faces[:, col + 1] - child_half_y) * ratio 
                        + child_half_y
                    )
                    child_faces[:, col + 2] = (
                        (child_faces[:, col + 2] - child_half_z) * ratio 
                        + child_half_z
                    )

                child_faces[:, 12] = (
                    (child_faces[:, 12] - child_half_x) * ratio 
                    + child_half_x
                )
                child_faces[:, 13] = (
                    (child_faces[:, 13] - child_half_y) * ratio 
                    + child_half_y
                )
                child_faces[:, 14] = (
                    (child_faces[:, 14] - child_half_z) * ratio 
                    + child_half_z
                )

                parent_half_x: float = p_asset.width / 2.0
                parent_half_y: float = p_asset.height / 2.0

                z_flat_shift = c_asset.depth if c_asset.is_flat else 0.0

                for i in range(4):
                    col = i * 3
                    child_faces[:, col] += (
                        local_x - child_half_x + parent_half_x
                    )
                    child_faces[:, col + 1] += (
                        local_y - child_half_y + parent_half_y
                    )
                    child_faces[:, col + 2] += local_z - z_flat_shift

                child_faces[:, 12] += local_x - child_half_x + parent_half_x
                child_faces[:, 13] += local_y - child_half_y + parent_half_y
                child_faces[:, 14] += local_z - z_flat_shift

                faces_to_stitch.append(child_faces)

            parent_faces = np.concatenate(faces_to_stitch)
            
            all_faces_list.append(
                self._transform_faces(
                    parent_faces, p_pos_3d, p_angle, p_tilt, p_scale,
                    p_asset.width, p_asset.height, p_asset.depth,
                    is_flat=p_asset.is_flat
                )
            )

        for path, c_asset, c_pos, c_angle, c_map, s_surf, d_rect, p_id in (
            self.pending_3d_attachments
        ):
            if c_map.get("render_3d", False):
                scale_val = c_map.get("scale", 1.0)
                faces = c_asset.faces.copy()
                all_faces_list.append(
                    self._transform_faces(
                        faces, c_pos, c_angle, 0.0, scale_val,
                        c_asset.width, c_asset.height, c_asset.depth,
                        is_flat=c_asset.is_flat
                    )
                )
            else:
                if s_surf is not None and d_rect is not None:
                    self.pending_2d_overlays.append(
                        (s_surf, d_rect, None, 0, path)
                    )

        if all_faces_list:
            stacked_faces = np.concatenate(all_faces_list)
            verts = stacked_faces[:, 0:12]

            sin_y, cos_y = math.sin(yaw), math.cos(yaw)
            sin_p, cos_p = math.sin(pitch), math.cos(pitch)

            cam_f32 = cam_pos.astype(np.float32)
            pts, depths, mask = project_vertices(
                verts, cam_f32, sin_y, cos_y, sin_p, cos_p
            )

            if np.any(mask):
                f_pts = pts[mask]
                f_faces = stacked_faces[mask]
                f_depths = depths[mask]

                sort_idx = np.argsort(f_depths)[::-1]
                s_pts = f_pts[sort_idx]
                s_faces = f_faces[sort_idx]

                s_pts[:, :, 0] -= HALF_WIDTH - int(self.translator.sw // 2)
                s_pts[:, :, 1] -= HALF_HEIGHT - int(self.translator.sh // 2)

                final_colors = apply_visual_effects(
                    colors=s_faces[:, 15:18],
                    z_centers=s_faces[:, 14],
                    euclidean_dist=f_depths[sort_idx],
                    render_dist=95.0,
                    fog_density=0.7,
                    use_h_shading=False,
                    height_shading_factor=0.0,
                    height_fog_density=0.0,
                    height_fog_max_z=0.0,
                    height_fog_fade=14.0
                )

                draw_poly = pygame.draw.polygon
                for i in range(len(s_pts)):
                    draw_poly(self.screen, final_colors[i], s_pts[i])

        for source, dest, area, special_flags, s_path in (
            self.pending_2d_overlays
        ):
            self.screen.blit(source, dest, area, special_flags)

        for draw_func, target_surf, d_args, d_kwargs in (
            self.pending_vector_draws
        ):
            draw_func(target_surf, *d_args, **d_kwargs)

        self.translator.prune_inactive()

        self.pending_3d_parents.clear()
        self.pending_3d_attachments.clear()
        self.pending_2d_overlays.clear()
        self.pending_vector_draws.clear()
        self.active_parent_id = None

        self._render_diagnostic_fps()

    def _render_diagnostic_fps(self) -> None:
        """Samples frame intervals and draws real-time telemetry."""
        from porter.porter_settings import PORTER_SHOW_FPS

        if not PORTER_SHOW_FPS:
            return

        current_time: float = time.perf_counter()
        delta_sec: float = current_time - self._last_time
        self._last_time = current_time

        delta_sec = max(0.0001, delta_sec)
        raw_fps: float = 1.0 / delta_sec

        if self._smoothed_fps is None:
            self._smoothed_fps = raw_fps
        else:
            alpha = 0.05
            self._smoothed_fps = (
                (self._smoothed_fps * (1.0 - alpha)) + (raw_fps * alpha)
            )

        self._fps_history.append((current_time, raw_fps))

        cutoff = current_time - 5.0
        self._fps_history = [
            item for item in self._fps_history if item[0] >= cutoff
        ]

        raw_values = [item[1] for item in self._fps_history]
        min_fps = min(raw_values) if raw_values else raw_fps
        max_fps = max(raw_values) if raw_values else raw_fps

        if self._fps_font is None:
            self._fps_font = pygame.font.SysFont(
                "monospace", 16, bold=True
            )

        fps_text_1: str = f"Avg FPS: {self._smoothed_fps:5.1f}"
        fps_text_2: str = f"Min/Max: {min_fps:5.1f} - {max_fps:5.1f}"

        fps_surf_1 = self._fps_font.render(fps_text_1, True, (0, 255, 0))
        fps_surf_2 = self._fps_font.render(fps_text_2, True, (0, 255, 0))

        screen_w = self.screen.get_width()
        screen_h = self.screen.get_height()
        text_w = max(fps_surf_1.get_width(), fps_surf_2.get_width())
        h1 = fps_surf_1.get_height()
        h2 = fps_surf_2.get_height()
        text_h = h1 + h2 + 4

        pad = 6
        box_w = text_w + (pad * 2)
        box_h = text_h + (pad * 2)
        
        # Position box at the lower-left corner
        box_x = 10
        box_y = screen_h - box_h - 10

        bg_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg_surf.fill((20, 20, 20, 180))
        pygame.draw.rect(
            bg_surf, (100, 100, 100, 200), (0, 0, box_w, box_h), 1
        )

        self.screen.blit(bg_surf, (box_x, box_y))
        self.screen.blit(fps_surf_1, (box_x + pad, box_y + pad))
        self.screen.blit(fps_surf_2, (box_x + pad, box_y + pad + h1 + 4))

    def _transform_faces(
        self,
        faces: NDArray[np.float32],
        pos: Tuple[float, float, float],
        angle_deg: float,
        tilt_rad: float,
        asset_scale: float,
        width: float,
        height: float,
        depth: float,
        is_flat: bool = False
    ) -> NDArray[np.float32]:
        """Applies translation, rotation, and tilt to asset faces."""
        px, py, pz = pos

        rad: float = math.radians(-angle_deg) + math.pi
        cos_r, sin_r = math.cos(rad), math.sin(rad)
        
        # Apply inverted tilt to correct mirrored South-facing bank mapping
        cos_t, sin_t = math.cos(-tilt_rad), math.sin(-tilt_rad)

        scale: float = asset_scale / self.translator.scale_factor

        half_x: float = width / 2.0
        half_y: float = height / 2.0
        half_z: float = depth if is_flat else (depth / 2.0)

        for i in range(4):
            col: int = i * 3
            lx: float = faces[:, col] - half_x
            ly: float = faces[:, col + 1] - half_y
            lz: float = faces[:, col + 2] - half_z

            # ROLL-THEN-YAW TRANSFORMATION
            # 1. Roll (rotate lateral-horizontal axes in raw coordinate frame)
            rx_rolled: float = lz * sin_t + lx * cos_t
            rz_rolled: float = lz * cos_t - lx * sin_t
            ry_rolled: float = ly

            # 2. Yaw (orient already rolled face relative to active heading)
            rx_final: float = rx_rolled * cos_r - ry_rolled * sin_r
            ry_final: float = rx_rolled * sin_r + ry_rolled * cos_r
            rz_final: float = rz_rolled

            faces[:, col] = rx_final * scale + px
            faces[:, col + 1] = ry_final * scale + py
            faces[:, col + 2] = rz_final * scale + pz

        lx_c: float = faces[:, 12] - half_x
        ly_c: float = faces[:, 13] - half_y
        lz_c: float = faces[:, 14] - half_z

        rx_rolled_c: float = lz_c * sin_t + lx_c * cos_t
        rz_rolled_c: float = lz_c * cos_t - lx_c * sin_t
        ry_rolled_c: float = ly_c

        rx_final_c: float = rx_rolled_c * cos_r - ry_rolled_c * sin_r
        ry_final_c: float = rx_rolled_c * sin_r + ry_rolled_c * cos_r
        rz_final_c: float = rz_rolled_c

        faces[:, 12] = rx_final_c * scale + px
        faces[:, 13] = ry_final_c * scale + py
        faces[:, 14] = rz_final_c * scale + pz

        return faces
