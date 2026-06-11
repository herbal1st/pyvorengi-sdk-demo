"""
Optimized geometry batcher using in-place vertex transformations.
"""

from typing import Any, List, Tuple, Optional, Final

import pygame
import numpy as np
from numpy.typing import NDArray

from renderer.projection import project_vertices
from renderer.visuals import apply_visual_effects

# Slicing constants for the 19-column face buffer
V_COLS: Final[slice] = slice(0, 12)
C_COLS: Final[slice] = slice(12, 15)
RGB_COLS: Final[slice] = slice(15, 18)


class BatchRenderer:
    """
    Orchestrates high-throughput geometry processing for voxel faces.
    """

    def __init__(self, screen: pygame.Surface) -> None:
        """
        Initializes the renderer with a target surface.
        """
        self.screen: pygame.Surface = screen
        self.active_face_count: int = 0

    def render_scene(
        self,
        visible_sections: List[Any],
        cam_pos: NDArray[np.float64],
        view_params: Tuple[float, float, float, float],
        render_dist: float,
        fog_density: float,
        h_shade: bool,
        h_shade_factor: float,
        h_fog_dens: float,
        h_fog_max_z: float,
        h_fog_fade: float
    ) -> None:
        """
        Processes the visual pipeline using in-place arithmetic.
        """
        self.active_face_count = 0

        all_faces: Optional[NDArray[np.float32]] = self._aggregate_geometry(
            visible_sections
        )
        if all_faces is None:
            return

        # Perform coordinate transformation
        verts: NDArray[np.float32] = self._transform_to_world(all_faces)

        # Projection (Optimized in previous step)
        cam_f32: NDArray[np.float32] = cam_pos.astype(np.float32)
        pts, _, proj_mask = project_vertices(verts, cam_f32, *view_params)

        if not np.any(proj_mask):
            return

        # Distance clipping and visibility filtering
        clip_data = self._apply_horizon_clipping(
            pts[proj_mask],
            all_faces[proj_mask],
            cam_f32,
            render_dist
        )
        if clip_data is None:
            return

        f_pts, f_faces, f_dist_sq, f_wz = clip_data

        # Painter's Algorithm sort (Far to Near)
        sorted_data = self._sort_faces(f_pts, f_faces, f_dist_sq, f_wz)
        s_pts, s_faces, s_dist, s_wz = sorted_data

        # Atmospheric Shader Pipeline (Optimized in previous step)
        final_colors: NDArray[np.int32] = apply_visual_effects(
            colors=s_faces[:, RGB_COLS],
            z_centers=s_wz,
            euclidean_dist=np.sqrt(s_dist),
            render_dist=render_dist,
            fog_density=fog_density,
            use_h_shading=h_shade,
            height_shading_factor=h_shade_factor,
            height_fog_density=h_fog_dens,
            height_fog_max_z=h_fog_max_z,
            height_fog_fade=h_fog_fade
        )

        self._rasterize(s_pts, final_colors)
        self.active_face_count = len(final_colors)

    def _aggregate_geometry(
        self,
        sections: List[Any]
    ) -> Optional[NDArray[np.float32]]:
        """
        Merges individual section buffers into a single render array.
        """
        arrays: List[NDArray[np.float32]] = [
            s.raw_stacked_faces for s in sections
            if s.raw_stacked_faces.size > 0
        ]

        if not arrays:
            return None

        return np.concatenate(arrays)

    def _transform_to_world(
        self,
        faces: NDArray[np.float32]
    ) -> NDArray[np.float32]:
        """
        Adds chunk offsets to local vertices using in-place broadcasting.
        """
        # Copy only the vertex columns to the work buffer
        verts: NDArray[np.float32] = faces[:, V_COLS].copy()

        # Add chunk WX to columns 0, 3, 6, 9
        verts[:, 0::3] += faces[:, 19, np.newaxis]
        # Add chunk WY to columns 1, 4, 7, 10
        verts[:, 1::3] += faces[:, 20, np.newaxis]

        return verts

    def _apply_horizon_clipping(
        self,
        pts: NDArray[np.int32],
        faces: NDArray[np.float32],
        cam_pos: NDArray[np.float32],
        render_dist: float
    ) -> Optional[Tuple]:
        """
        Removes faces outside the render distance using minimal allocations.
        """
        # Calculate world-space centers (Face Center + Chunk Offset)
        wx: NDArray[np.float32] = faces[:, 12] + faces[:, 19]
        wy: NDArray[np.float32] = faces[:, 13] + faces[:, 20]
        wz: NDArray[np.float32] = faces[:, 14]

        # Calculate squared Euclidean distance in-place
        dx = wx - cam_pos[0]
        dy = wy - cam_pos[1]
        dz = wz - cam_pos[2]

        dist_sq: NDArray[np.float32] = np.square(dx)
        dist_sq += np.square(dy)
        dist_sq += np.square(dz)

        limit_sq: float = (render_dist + 0.5) ** 2
        mask: NDArray[np.bool_] = dist_sq <= limit_sq

        if not np.any(mask):
            return None

        return (
            pts[mask],
            faces[mask],
            dist_sq[mask],
            wz[mask]
        )

    def _sort_faces(
        self,
        pts: NDArray[np.int32],
        faces: NDArray[np.float32],
        dist_sq: NDArray[np.float32],
        wz: NDArray[np.float32]
    ) -> Tuple:
        """
        Sorts face buffers by distance from camera.
        """
        idx: NDArray[np.intp] = np.argsort(dist_sq)[::-1]
        return pts[idx], faces[idx], dist_sq[idx], wz[idx]

    def _rasterize(
        self,
        pts: NDArray[np.int32],
        colors: NDArray[np.int32]
    ) -> None:
        """
        Iterative polygon draw calls.
        """
        draw_poly = pygame.draw.polygon
        surface = self.screen

        for i in range(len(pts)):
            draw_poly(surface, colors[i], pts[i])
