"""
Geometric utilities for vertex packing and static directional lighting.
"""

from typing import Any, Final, List, Tuple

import numpy as np
from numpy.typing import NDArray

from settings import settings

# --- Type Aliases ---
Normal3D = Tuple[int, int, int]
Vertex3D = Tuple[int, int, int]
CardinalAxisInfo = Tuple[int, int]

# --- Constants ---

# Structure: (Normal, Vertex Offsets, Axis Index/Direction)
FACE_DATA: Final[List[Tuple[Normal3D, List[Vertex3D], CardinalAxisInfo]]] = [
    ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], (2, 1)),
    ((0, 0, -1), [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)], (2, -1)),
    ((0, 1, 0), [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)], (1, 1)),
    ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], (1, -1)),
    ((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)], (0, 1)),
    ((-1, 0, 0), [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)], (0, -1)),
]


def assemble_face_buffer(
    chunk_indices: Tuple[NDArray[np.int_], NDArray[np.int_], NDArray[np.int_]],
    lookup_indices: Tuple[NDArray[np.int_], NDArray[np.int_], NDArray[np.int_]],
    block_ids: NDArray[np.uint8],
    normal: Normal3D,
    v_offsets: List[Vertex3D],
    registry: Any,
) -> NDArray[np.float32]:
    """
    Packs geometry into a vectorized buffer without iterative loops.
    """
    lz_c, ly_c, lx_c = chunk_indices
    lz_l, ly_l, lx_l = lookup_indices
    count: int = len(lz_c)

    # 19 columns: 12 vertices, 3 centers, 3 RGB, 1 ID
    buffer: NDArray[np.float32] = np.zeros((count, 19), dtype=np.float32)

    # 1. Vectorized Vertex Packing
    for i, (vx, vy, vz) in enumerate(v_offsets):
        col: int = i * 3
        buffer[:, col] = lx_c + vx
        buffer[:, col + 1] = ly_c + vy
        buffer[:, col + 2] = lz_c + vz

    # 2. Vectorized Center Calculation
    buffer[:, 12] = lx_c + 0.5 + (normal[0] * 0.5)
    buffer[:, 13] = ly_c + 0.5 + (normal[1] * 0.5)
    buffer[:, 14] = lz_c + 0.5 + (normal[2] * 0.5)

    # 3. Vectorized ID Extraction
    active_ids: NDArray[np.uint8] = block_ids[lz_l, ly_l, lx_l]
    buffer[:, 18] = active_ids.astype(np.float32)

    # 4. Vectorized Color & Flat Lighting Application
    palette: NDArray[np.uint8] = registry.get_color_palette(normal)
    colors: NDArray[np.float32] = palette[active_ids].astype(np.float32)

    # Calculate final shading multipliers from static direction lighting map
    shade_mult: float = settings.LIGHT_MAP.get(normal, 1.0)

    # Apply flat shade multiplier uniformly across channels
    buffer[:, 15:18] = colors * shade_mult

    return buffer
