"""
Simple step-based voxel raymarching for block targeting.
"""

import math
from typing import Optional, Tuple
import numpy as np
from numpy.typing import NDArray

from settings import settings
from world.storage.manager import World


def perform_raycast(
    world: World,
    start_pos: Tuple[float, float, float],
    look_vector: NDArray[np.float32],
    max_dist: float = settings.RAYCAST_DIST,
    step_size: float = 0.1
) -> Optional[Tuple[Tuple[int, int, int], Tuple[int, int, int]]]:
    """
    Steps along the look direction to detect the first solid block.

    Returns:
        A tuple containing ((hit_x, hit_y, hit_z), (prev_x, prev_y, prev_z))
        or None if no solid block is targeted.
    """
    curr_pos: NDArray[np.float32] = np.array(start_pos, dtype=np.float32)

    norm: float = float(np.linalg.norm(look_vector))
    if norm < 1e-5:
        return None

    look_dir: NDArray[np.float32] = look_vector / norm
    steps: int = int(max_dist / step_size)

    prev_voxel: Tuple[int, int, int] = (
        math.floor(curr_pos[0]),
        math.floor(curr_pos[1]),
        math.floor(curr_pos[2])
    )

    for _ in range(steps):
        curr_pos += look_dir * step_size
        curr_voxel: Tuple[int, int, int] = (
            math.floor(curr_pos[0]),
            math.floor(curr_pos[1]),
            math.floor(curr_pos[2])
        )

        if curr_voxel == prev_voxel:
            continue

        voxel_id = world.get_voxel(
            float(curr_voxel[0]),
            float(curr_voxel[1]),
            float(curr_voxel[2])
        )

        if voxel_id is not None and world.registry.is_solid(voxel_id):
            return curr_voxel, prev_voxel

        prev_voxel = curr_voxel

    return None
