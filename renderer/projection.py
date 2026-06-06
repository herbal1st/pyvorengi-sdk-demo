"""
Vectorized mathematical transformations for 3D to 2D projection.
"""

from typing import Final, Tuple, Any

import numpy as np
from numpy.typing import NDArray

from settings import settings
from constants import constants

# Clipping and FOV constants
NEAR: Final[float] = settings.NEAR_PLANE
FOV_VAL: Final[float] = float(settings.FOV)

# Small margin to prevent precision-based clipping on perpendicular faces
_AREA_EPSILON: Final[float] = 1e-6


def project_vertices(
    verts: NDArray[np.float32],
    origin: NDArray[np.float32],
    sin_y: float,
    cos_y: float,
    sin_p: float,
    cos_p: float,
) -> Tuple[NDArray[np.int32], NDArray[np.float32], NDArray[np.bool_]]:
    """
    Transforms 3D world faces into 2D screen coordinates.
    """
    num_faces: int = verts.shape[0]
    
    # Guard: No geometry to process
    if num_faces == 0:
        return _get_empty_projection()

    # 1. TRANSLATION: Center vertices around camera origin
    v_local: NDArray[np.float32] = verts.reshape(-1, 3) - origin

    # 2. YAW ROTATION: Rotate vertices on the XY plane
    rx_y: NDArray[np.float32] = (
        v_local[:, 0] * cos_y - v_local[:, 1] * sin_y
    )
    ry_temp: NDArray[np.float32] = (
        v_local[:, 0] * sin_y + v_local[:, 1] * cos_y
    )

    # 3. PITCH ROTATION: Rotate vertices on the YZ plane
    ry_p: NDArray[np.float32] = (
        v_local[:, 2] * sin_p + ry_temp * cos_p
    )
    rz_p: NDArray[np.float32] = (
        v_local[:, 2] * cos_p - ry_temp * sin_p
    )

    # 4. PERSPECTIVE PROJECTION
    # Prevent division by zero or negative depth
    depth_safe: NDArray[np.float32] = np.maximum(ry_p, NEAR)
    
    # Scale coordinates to pixels based on depth and FOV
    screen_x: NDArray[np.int32] = (
        constants.HALF_WIDTH + (rx_y * FOV_VAL / depth_safe)
    ).astype(np.int32)
    screen_y: NDArray[np.int32] = (
        constants.HALF_HEIGHT - (rz_p * FOV_VAL / depth_safe)
    ).astype(np.int32)

    # 5. PACKING: Group vertex pairs into 4-point polygons
    proj_points: NDArray[np.int32] = np.stack(
        [screen_x, screen_y], axis=1
    ).reshape(num_faces, 4, 2)
    
    # Calculate representative depth for distance effects
    depth_per_face: NDArray[np.float32] = (
        ry_p.reshape(num_faces, 4).mean(axis=1)
    )

    # 6. VISIBILITY MASK: Screen bounds and backface culling
    mask: NDArray[np.bool_] = _calc_visibility_mask(
        screen_x, screen_y, ry_p.reshape(num_faces, 4)
    )

    return proj_points, depth_per_face, mask


def _get_empty_projection() -> Tuple[Any, Any, Any]:
    """
    Returns empty structures for the projection pipeline.
    """
    return (
        np.empty((0, 4, 2), dtype=np.int32), 
        np.empty(0, dtype=np.float32), 
        np.empty(0, dtype=bool)
    )


def _calc_visibility_mask(
    sx: NDArray[np.int32], 
    sy: NDArray[np.int32], 
    depths: NDArray[np.float32]
) -> NDArray[np.bool_]:
    """
    Identifies visible faces via frustum bounds and winding order.
    """
    num_faces: int = depths.shape[0]
    sx_f: NDArray[np.int32] = sx.reshape(num_faces, 4)
    sy_f: NDArray[np.int32] = sy.reshape(num_faces, 4)

    # 1. Frustum Clipping: Is the polygon off-screen or behind camera?
    is_behind: NDArray[np.bool_] = np.all(depths < NEAR, axis=1)
    is_off_x: NDArray[np.bool_] = (
        np.all(sx_f < 0, axis=1) | np.all(sx_f > constants.WIDTH, axis=1)
    )
    is_off_y: NDArray[np.bool_] = (
        np.all(sy_f < 0, axis=1) | np.all(sy_f > constants.HEIGHT, axis=1)
    )
    
    # 2. Backface Culling: Shoelace formula for clockwise winding
    v0_x, v1_x, v2_x = sx_f[:, 0], sx_f[:, 1], sx_f[:, 2]
    v0_y, v1_y, v2_y = sy_f[:, 0], sy_f[:, 1], sy_f[:, 2]
    area: NDArray[np.int32] = (
        (v1_x - v0_x) * (v2_y - v0_y) - (v1_y - v0_y) * (v2_x - v0_x)
    )
    
    # Preservation of the custom epsilon for top-face visibility
    is_backface: NDArray[np.bool_] = area > -_AREA_EPSILON

    return ~(is_behind | is_off_x | is_off_y | is_backface)
