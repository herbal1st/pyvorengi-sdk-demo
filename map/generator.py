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


def generate_chunk_data(
    cx: int,
    cy: int,
    padded: bool = False
) -> NDArray[np.uint8]:
    """
    Creates a 3D voxel array for a chunk with optional 1-block XY padding.
    """
    size: int = settings.CHUNK_SIZE + (2 if padded else 0)
    depth: int = settings.MAP_DEPTH
    offset: int = -1 if padded else 0
    grid: NDArray[np.uint8] = np.zeros((depth, size, size), dtype=np.uint8)

    local_range: NDArray[np.int32] = np.arange(0, size)
    world_x: NDArray[np.int32] = (
        local_range + (cx * settings.CHUNK_SIZE) + offset
    )
    world_y: NDArray[np.int32] = (
        local_range + (cy * settings.CHUNK_SIZE) + offset
    )
    gy, gx = np.meshgrid(world_y, world_x, indexing="ij")

    v_height_func = np.vectorize(_calculate_clamped_height)
    height_grid: NDArray[np.int32] = v_height_func(gx, gy)
    z_indices: NDArray[np.int32] = np.arange(depth).reshape(depth, 1, 1)

    grid[z_indices < height_grid] = registry.ID_STONE

    dirt_mask: NDArray[np.bool_] = (z_indices == (height_grid - 2))
    grid[dirt_mask & (z_indices > 0)] = registry.ID_DIRT

    grass_mask: NDArray[np.bool_] = (z_indices == (height_grid - 1))
    grid[grass_mask & (z_indices >= 0)] = registry.ID_GRASS

    grid[0, :, :] = registry.ID_BEDROCK

    if settings.SKY_ISLANDS_ON:
        _apply_sky_island_filter(grid)
        if cx == 0 and cy == 0:
            _apply_spawn_safety_pad(grid, padded)

    if cx == 0 and cy == 0:
        _place_spawn_marker_procedural(grid, padded)

    return grid


def _calculate_clamped_height(gx: int, gy: int) -> int:
    """
    Calculates terrain height using scaled noise coordinates.
    """
    nx: float = gx / settings.NOISE_SCALE
    ny: float = gy / settings.NOISE_SCALE

    noise_val: float = _NOISE.noise(nx, ny)
    max_h: float = settings.MAP_DEPTH * settings.MAX_TERRAIN_HEIGHT_RATIO
    raw_h: int = int(noise_val * max_h)

    return max(1, min(raw_h, settings.MAP_DEPTH))


def _apply_sky_island_filter(grid: NDArray[np.uint8]) -> None:
    """
    Applies vertical slicing and downward underbelly mirroring.
    """
    z_mid: int = settings.SKY_ISLAND_MIRROR_HEIGHT
    fill_id: int = settings.SKY_ISLAND_BOTTOM_FILL_ID
    depth: int = settings.MAP_DEPTH

    # Clear under mirror height to air (0)
    grid[0:z_mid, :, :] = 0

    # Mirror terrain downward into the void symmetrically
    for z_curr in range(z_mid, depth):
        dz: int = z_curr - z_mid
        z_target: int = z_mid - dz - 1

        if z_target < 0:
            break

        solid_mask: NDArray[np.bool_] = (grid[z_curr, :, :] != 0)
        grid[z_target, :, :] = np.where(
            solid_mask, fill_id, grid[z_target, :, :]
        )


def _apply_spawn_safety_pad(
    grid: NDArray[np.uint8],
    padded: bool
) -> None:
    """
    Ensures a fallback stone safety pad is generated around the origin.
    """
    pad_size: int = settings.SPAWN_SAFETY_PAD_SIZE
    half_pad: int = pad_size // 2
    z_mid: int = settings.SKY_ISLAND_MIRROR_HEIGHT
    fill_id: int = settings.SKY_ISLAND_BOTTOM_FILL_ID

    idx: int = 1 if padded else 0
    c_center: int = (settings.CHUNK_SIZE // 2) + idx

    y_slice = slice(c_center - half_pad, c_center + half_pad + 1)
    x_slice = slice(c_center - half_pad, c_center + half_pad + 1)

    grid[z_mid, y_slice, x_slice] = fill_id


def _place_spawn_marker_procedural(
    grid: NDArray[np.uint8],
    padded: bool
) -> None:
    """
    Places the spawn block at the highest solid point at (0,0).
    """
    idx: int = 1 if padded else 0
    c_center: int = settings.CHUNK_SIZE // 2 + idx

    column = grid[:, c_center, c_center]
    solid_indices = np.where(column != registry.ID_AIR)[0]

    if solid_indices.size > 0:
        top_solid = int(solid_indices[-1])
        if top_solid + 1 < settings.MAP_DEPTH:
            grid[top_solid + 1, c_center, c_center] = registry.ID_SPAWN
