"""
Background worker functions for chunk data loading and mesh generation.
"""

from itertools import product
from typing import Dict, List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray

import map.generator as generator
from map.registry import VoxelRegistry
from mesher import mesher
from settings import settings
from world.provider import WorldProvider
from world.spatial import (
    MeshContext,
    Section,
    create_section,
    get_section_ranges,
)


def worker_load_chunk(
    world_id: str,
    cx: int,
    cy: int
) -> Tuple[Tuple[int, int], NDArray[np.uint8]]:
    """
    Generates or loads terrain data in an isolated process.
    """
    provider: WorldProvider = WorldProvider(world_id)
    data: NDArray[np.uint8] = provider.get_chunk_data(cx, cy)

    return (cx, cy), data


def worker_mesh_chunk(
    cx: int,
    cy: int,
    data: NDArray[np.uint8],
    context: MeshContext,
    neighbors: Optional[Dict[Tuple[int, int], NDArray[np.uint8]]] = None
) -> Tuple[Tuple[int, int], List[Section]]:
    """
    Builds geometry with correct neighbor sampling via generator re-call.
    """
    registry: VoxelRegistry = VoxelRegistry()

    if settings.USE_PROCEDURAL:
        gen_padded: NDArray[np.uint8] = generator.generate_chunk_data(
            cx, cy, padded=True
        )
    else:
        gen_padded = _get_static_padded_chunk(cx, cy)

    padded_vol: NDArray[np.uint8] = np.zeros(
        (
            settings.MAP_DEPTH + 2, 
            settings.CHUNK_SIZE + 2, 
            settings.CHUNK_SIZE + 2
        ),
        dtype=np.uint8
    )

    padded_vol[1:-1, :, :] = gen_padded
    padded_vol[1:-1, 1:-1, 1:-1] = data

    # Overlay neighbor modifications onto halo padding
    if neighbors:
        for (dx, dy), n_data in neighbors.items():
            if dx == -1 and dy == 0:
                padded_vol[1:-1, 1:-1, 0] = n_data[:, :, -1]
            elif dx == 1 and dy == 0:
                padded_vol[1:-1, 1:-1, -1] = n_data[:, :, 0]
            elif dx == 0 and dy == -1:
                padded_vol[1:-1, 0, 1:-1] = n_data[:, -1, :]
            elif dx == 0 and dy == 1:
                padded_vol[1:-1, -1, 1:-1] = n_data[:, 0, :]
            elif dx == -1 and dy == -1:
                padded_vol[1:-1, 0, 0] = n_data[:, -1, -1]
            elif dx == -1 and dy == 1:
                padded_vol[1:-1, -1, 0] = n_data[:, 0, -1]
            elif dx == 1 and dy == -1:
                padded_vol[1:-1, 0, -1] = n_data[:, -1, 0]
            elif dx == 1 and dy == 1:
                padded_vol[1:-1, -1, -1] = n_data[:, 0, 0]

    wx: int = cx * settings.CHUNK_SIZE
    wy: int = cy * settings.CHUNK_SIZE
    sections: List[Section] = []

    section_indices = product(
        range(settings.SECTION_DIVS_Z),
        range(settings.SECTION_DIVS_XY),
        range(settings.SECTION_DIVS_XY)
    )

    for sz_idx, sy_idx, sx_idx in section_indices:
        z_rng, y_rng, x_rng = get_section_ranges(sz_idx, sy_idx, sx_idx)

        faces = mesher.generate_section_mesh(
            padded_vol, registry, z_rng, y_rng, x_rng, context
        )

        if not faces:
            continue

        gx: int = cx * settings.SECTION_DIVS_XY + sx_idx
        gy: int = cy * settings.SECTION_DIVS_XY + sy_idx

        sections.append(
            create_section(
                faces, gx, gy, sz_idx, wx, wy, z_rng, y_rng, x_rng
            )
        )

    return (cx, cy), sections


def _get_static_padded_chunk(cx: int, cy: int) -> NDArray[np.uint8]:
    """
    Extracts an XY-padded chunk slice from the static map buffer.
    """
    from map.custom_map_buffer import MapManager

    manager = MapManager()
    depth: int = settings.MAP_DEPTH
    size: int = settings.CHUNK_SIZE + 2
    grid: NDArray[np.uint8] = np.zeros((depth, size, size), dtype=np.uint8)

    if manager.data is None:
        return grid

    z_lim, y_lim, x_lim = manager.data.shape

    x_start: int = cx * settings.CHUNK_SIZE - 1
    y_start: int = cy * settings.CHUNK_SIZE - 1
    x_end: int = x_start + size
    y_end: int = y_start + size

    src_x0: int = max(0, x_start)
    src_x1: int = min(x_lim, x_end)
    src_y0: int = max(0, y_start)
    src_y1: int = min(y_lim, y_end)

    if src_x0 >= src_x1 or src_y0 >= src_y1:
        return grid

    dest_x0: int = src_x0 - x_start
    dest_x1: int = src_x1 - x_start
    dest_y0: int = src_y0 - y_start
    dest_y1: int = src_y1 - y_start

    grid[:, dest_y0:dest_y1, dest_x0:dest_x1] = manager.data[
        0:depth, src_y0:src_y1, src_x0:src_x1
    ]

    return grid
