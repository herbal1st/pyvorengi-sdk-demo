"""
Procedural terrain generation using selectable noise algorithms.
"""

import numpy as np
from numpy.typing import NDArray
from typing import Tuple

import map.registry as registry
from settings import settings
from utils.noise import PerlinNoise, SimplexNoise


def _init_noise() -> any:
    """
    Initializes the noise engine once at module level.
    """
    if settings.ACTIVE_NOISE_TYPE == settings.NOISE_TYPE_SIMPLEX:
        return SimplexNoise(seed=settings.WORLD_SEED)
    return PerlinNoise(seed=settings.WORLD_SEED)


# Global noise instance used by all generation calls
_NOISE = _init_noise()


def reinit_noise_generator() -> None:
    """
    Reinitializes the global noise generator with updated settings.
    """
    global _NOISE
    _NOISE = _init_noise()


def generate_chunk_data(
    cx: int, 
    cy: int, 
    padded: bool = False
) -> NDArray[np.uint8]:
    """
    Creates a 3D voxel array for a chunk with optional 1-block XY padding.
    """
    # Core dimensions: 16x16 or 18x18 if padded
    size: int = settings.CHUNK_SIZE + (2 if padded else 0)
    depth: int = settings.MAP_DEPTH
    
    # Starting world coordinate (offset by -1 if padded)
    offset: int = -1 if padded else 0
    
    # Initialize the volume
    grid: NDArray[np.uint8] = np.zeros((depth, size, size), dtype=np.uint8)

    # 1. Coordinate Grid Generation
    local_range: NDArray[np.int32] = np.arange(0, size)
    world_x: NDArray[np.int32] = (
        local_range + (cx * settings.CHUNK_SIZE) + offset
    )
    world_y: NDArray[np.int32] = (
        local_range + (cy * settings.CHUNK_SIZE) + offset
    )
    
    gy, gx = np.meshgrid(world_y, world_x, indexing="ij")

    # 2. Vectorized Height Calculation
    v_height_func = np.vectorize(_calculate_clamped_height)
    height_grid: NDArray[np.int32] = v_height_func(gx, gy)

    # 3. 3D Volume Filling
    z_indices: NDArray[np.int32] = np.arange(depth).reshape(depth, 1, 1)

    grid[z_indices < height_grid] = registry.ID_STONE
    
    dirt_mask: NDArray[np.bool_] = (z_indices == (height_grid - 2))
    grid[dirt_mask & (z_indices > 0)] = registry.ID_DIRT

    grass_mask: NDArray[np.bool_] = (z_indices == (height_grid - 1))
    grid[grass_mask & (z_indices >= 0)] = registry.ID_GRASS

    # 4. Global Structural Rules
    grid[0, :, :] = registry.ID_BEDROCK

    # Only place markers in the center of the clean chunk (0,0)
    if cx == 0 and cy == 0:
        _place_spawn_marker_procedural(grid, height_grid, padded)

    return grid


def _calculate_clamped_height(gx: int, gy: int) -> int:
    """
    Calculates terrain height using scaled noise coordinates.
    """
    nx: float = gx / settings.NOISE_SCALE
    ny: float = gy / settings.NOISE_SCALE
    
    # Normalize noise and scale to vertical map limit
    noise_val: float = _NOISE.noise(nx, ny)
    max_h: float = settings.MAP_DEPTH * settings.MAX_TERRAIN_HEIGHT_RATIO
    raw_h: int = int(noise_val * max_h)
    
    return max(1, min(raw_h, settings.MAP_DEPTH))


def _place_spawn_marker_procedural(
    grid: NDArray[np.uint8], 
    heights: NDArray[np.int32],
    padded: bool
) -> None:
    """
    Places the spawn block at (0,0) world coordinates.
    """
    # Adjust index for padded/non-padded mode
    idx: int = 1 if padded else 0
    surface_z: int = int(heights[idx, idx])
    
    if surface_z < settings.MAP_DEPTH:
        grid[surface_z, idx, idx] = registry.ID_SPAWN
