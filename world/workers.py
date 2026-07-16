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

    # Always generate padded chunk procedurally
    gen_padded: NDArray[np.uint8] = generator.generate_chunk_data(
        cx, cy, padded=True
    )

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
