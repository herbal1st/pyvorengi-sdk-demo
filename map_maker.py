"""
Generates a 'Bookshelf Matrix' display map for available voxel blocks.

Constructs vertical plates for registered block types, leaving an open
walkway corridor for visual inspection and player movement.
"""

from pathlib import Path
from typing import List, Final

import numpy as np
from numpy.typing import NDArray

from map.registry import ID_AIR, ID_OBSIDIAN, ID_SPAWN, VoxelRegistry
from settings import settings

# Presentation parameters for matrix structure
SHELF_WIDTH: Final[int] = 5  # blocks
SHELF_HEIGHT: Final[int] = 1  # blocks
FLOOR_BLOCK_ID: Final[int] = ID_OBSIDIAN  # block id
BASE_WIDTH: Final[int] = settings.CHUNK_SIZE  # corridor width
WALL_HEIGHT: Final[int] = 5  # blocks


def build_bookshelf_map(registry: VoxelRegistry) -> NDArray[np.uint8]:
    """
    Generates horizontal bookshelf plates with a solid platform floor.
    """
    depth: int = settings.MAP_DEPTH
    border_pad: int = settings.CHUNK_SIZE

    # Get block IDs, excluding AIR and SPAWNPOINT
    layer_blocks: List[int] = [
        b_id
        for b_id in registry._cache.keys()
        if b_id not in (ID_AIR, ID_SPAWN)
    ]

    # Calculate map dimensions dynamically based on registry count
    num_layers: int = len(layer_blocks)
    base_length: int = num_layers * 3

    map_width: int = BASE_WIDTH + (2 * border_pad)
    map_length: int = base_length + (2 * border_pad)

    # Allocate map with native memory layout (Z, Y, X) ordering
    map_data: NDArray[np.uint8] = np.zeros(
        (depth, map_length, map_width), dtype=np.uint8
    )

    # 1. Fill Z = 0 with a solid platform floor
    map_data[0, :, :] = FLOOR_BLOCK_ID

    # 2. Build vertical plates within the padded inner region
    for i, block_id in enumerate(layer_blocks):
        y_pos: int = border_pad + (i * 3)

        if y_pos >= (map_length - border_pad):
            continue

        x_start: int = border_pad
        x_end: int = border_pad + SHELF_WIDTH
        z_start: int = 1
        z_end: int = 1 + SHELF_HEIGHT

        # Indexed as [Z, Y, X]
        map_data[z_start:z_end, y_pos, x_start:x_end] = block_id

    # 3. Add surrounding outer safety walls
    wall_z_end: int = 1 + int(WALL_HEIGHT)
    if wall_z_end > 1:
        map_data[1:wall_z_end, :, 0] = FLOOR_BLOCK_ID   # West wall
        map_data[1:wall_z_end, :, -1] = FLOOR_BLOCK_ID  # East wall
        map_data[1:wall_z_end, 0, :] = FLOOR_BLOCK_ID   # South wall
        map_data[1:wall_z_end, -1, :] = FLOOR_BLOCK_ID  # North wall

    # 4. Place SPAWNPOINT on the launchpad-like center
    mid_index: int = settings.CHUNK_SIZE // 2
    # Compensate for the pre-save flip so it lands exactly at mid_index
    target_spawn_x: int = map_width - 1 - mid_index
    map_data[1, mid_index, target_spawn_x] = ID_SPAWN

    # 5. Flip horizontally along the X-axis (dimension 2) to bake in winding
    map_data = map_data[:, :, ::-1]

    return map_data


def export_map(map_data: NDArray[np.uint8], filename: str) -> None:
    """
    Saves and validates the generated map volume.
    """
    out_path: Path = Path("map/maps") / filename

    try:
        np.savez_compressed(out_path, voxels=map_data)
        print(
            f"Exported matrix map to {out_path} with shape {map_data.shape}"
        )
    except Exception as error:
        print(f"Error exporting map: {error}")


if __name__ == "__main__":
    registry_inst = VoxelRegistry()

    # Build the bookshelf map matching visual design specifications
    bookshelf_map: NDArray[np.uint8] = build_bookshelf_map(registry_inst)
    export_map(bookshelf_map, "default_map.npz")
