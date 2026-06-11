"""
Optimized 3D to 2D projection with reduced memory allocation.
"""

from typing import Final, Tuple, Any

import numpy as np
from numpy.typing import NDArray

from settings import settings
from constants import constants

NEAR: Final[float] = settings.NEAR_PLANE
FOV_VAL: Final[float] = float(settings.FOV)
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
    Transforms world faces into screen space using in-place operations.
    """
    num_faces: int = verts.shape[0]
    if num_faces == 0:
        return _get_empty_projection()

    # 1. TRANSLATION: Center vertices around camera
    v_local: NDArray[np.float32] = verts.reshape(-1, 3) - origin

    # 2. YAW ROTATION (XY Plane)
    # Temporary buffers to avoid multiple large array allocations
    vx = v_local[:, 0]
    vy = v_local[:, 1]
    vz = v_local[:, 2]

    rx_y: NDArray[np.float32] = (vx * cos_y) - (vy * sin_y)
    ry_temp: NDArray[np.float32] = (vx * sin_y) + (vy * cos_y)

    # 3. PITCH ROTATION (YZ Plane)
    ry_p: NDArray[np.float32] = (vz * sin_p) + (ry_temp * cos_p)
    rz_p: NDArray[np.float32] = (vz * cos_p) - (ry_temp * sin_p)

    # 4. PERSPECTIVE PROJECTION
    # Re-use ry_p memory for depth safety if possible, or use out=
    depth_safe: NDArray[np.float32] = np.maximum(ry_p, NEAR)

    # Calculate screen coordinates directly into target dtype
    screen_x: NDArray[np.int32] = (
        constants.HALF_WIDTH + (rx_y * FOV_VAL / depth_safe)
    ).astype(np.int32)
    
    screen_y: NDArray[np.int32] = (
        constants.HALF_HEIGHT - (rz_p * FOV_VAL / depth_safe)
    ).astype(np.int32)

    # 5. PACKING
    proj_points: NDArray[np.int32] = np.stack(
        [screen_x, screen_y], axis=1
    ).reshape(num_faces, 4, 2)

    depth_per_face: NDArray[np.float32] = (
        ry_p.reshape(num_faces, 4).mean(axis=1)
    )

    # 6. VISIBILITY MASK
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
    Identifies visible faces using optimized winding and boundary checks.
    """
    num_faces: int = depths.shape[0]
    sx_f: NDArray[np.int32] = sx.reshape(num_faces, 4)
    sy_f: NDArray[np.int32] = sy.reshape(num_faces, 4)

    # Screen/Depth Bounds
    is_behind: NDArray[np.bool_] = np.all(depths < NEAR, axis=1)
    is_off_x: NDArray[np.bool_] = (
        np.all(sx_f < 0, axis=1) | np.all(sx_f > constants.WIDTH, axis=1)
    )
    is_off_y: NDArray[np.bool_] = (
        np.all(sy_f < 0, axis=1) | np.all(sy_f > constants.HEIGHT, axis=1)
    )

    # Backface Culling (Shoelace Area)
    # v1_x - v0_x
    dx1 = sx_f[:, 1] - sx_f[:, 0]
    # v2_y - v0_y
    dy2 = sy_f[:, 2] - sy_f[:, 0]
    # v1_y - v0_y
    dy1 = sy_f[:, 1] - sy_f[:, 0]
    # v2_x - v0_x
    dx2 = sx_f[:, 2] - sx_f[:, 0]

    area: NDArray[np.int32] = (dx1 * dy2) - (dy1 * dx2)
    is_backface: NDArray[np.bool_] = area > -_AREA_EPSILON

    return ~(is_behind | is_off_x | is_off_y | is_backface)
