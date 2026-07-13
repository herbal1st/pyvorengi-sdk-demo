"""
Global manager for coordinate-based chunk access and voxel queries.
"""

import math
from typing import Dict, List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray

from map.registry import ID_AIR, ID_SPAWN, VoxelRegistry
from settings import settings
from world.storage.chunk import Chunk


class World:
    """
    Orchestrates chunk storage and provides spatial query interfaces.
    """

    def __init__(self) -> None:
        """
        Initializes the world dictionary and block registry.
        """
        self.chunks: Dict[Tuple[int, int], Chunk] = {}
        self.registry: VoxelRegistry = VoxelRegistry()
        self.remesh_requested: bool = False

    def request_remesh(self) -> None:
        """
        Signals that all chunks should be re-evaluated by the mesher.
        """
        self.remesh_requested = True

    def get_voxel(self, x: float, y: float, z: float) -> Optional[int]:
        """
        Resolves world-space coordinates to a specific block ID.
        """
        ix: int = math.floor(x)
        iy: int = math.floor(y)
        iz: int = math.floor(z)

        if not (0 <= iz < settings.MAP_DEPTH):
            return None

        cx: int = ix // settings.CHUNK_SIZE
        cy: int = iy // settings.CHUNK_SIZE

        chunk: Optional[Chunk] = self.chunks.get((cx, cy))
        if chunk is None:
            return None

        lx: int = ix % settings.CHUNK_SIZE
        ly: int = iy % settings.CHUNK_SIZE

        return int(chunk.data[iz, ly, lx])

    def set_voxel(
        self,
        ix: int,
        iy: int,
        iz: int,
        voxel_id: int
    ) -> bool:
        """
        Updates the voxel ID and flags local and neighbors for remeshing.
        """
        if not (0 <= iz < settings.MAP_DEPTH):
            return False

        cx: int = ix // settings.CHUNK_SIZE
        cy: int = iy // settings.CHUNK_SIZE

        chunk: Optional[Chunk] = self.chunks.get((cx, cy))
        if chunk is None:
            return False

        lx: int = ix % settings.CHUNK_SIZE
        ly: int = iy % settings.CHUNK_SIZE

        chunk.data[iz, ly, lx] = voxel_id

        chunk.needs_remesh = True
        self.remesh_requested = True

        neighbors: List[Tuple[int, int]] = []
        if lx == 0:
            neighbors.append((cx - 1, cy))
        elif lx == settings.CHUNK_SIZE - 1:
            neighbors.append((cx + 1, cy))

        if ly == 0:
            neighbors.append((cx, cy - 1))
        elif ly == settings.CHUNK_SIZE - 1:
            neighbors.append((cx, cy + 1))

        if lx == 0 and ly == 0:
            neighbors.append((cx - 1, cy - 1))
        elif lx == 0 and ly == settings.CHUNK_SIZE - 1:
            neighbors.append((cx - 1, cy + 1))
        elif lx == settings.CHUNK_SIZE - 1 and ly == 0:
            neighbors.append((cx + 1, cy - 1))
        elif (
            lx == settings.CHUNK_SIZE - 1
            and ly == settings.CHUNK_SIZE - 1
        ):
            neighbors.append((cx + 1, cy + 1))

        for n_coords in neighbors:
            n_chunk = self.chunks.get(n_coords)
            if n_chunk is not None:
                n_chunk.needs_remesh = True

        return True

    def find_spawn_point(self) -> Tuple[float, float, float]:
        """
        Locates the spawn block or calculates a safe ground fallback.
        """
        f_x: float = 0.5
        f_y: float = 0.5
        f_z: float = float(settings.MAP_DEPTH // 2)

        origin: Optional[Chunk] = self.chunks.get((0, 0))
        if origin is None:
            return (f_x, f_y, f_z)

        s_idx: Tuple[NDArray, ...] = np.where(origin.data == ID_SPAWN)

        if s_idx[0].size > 0:
            sz: int = int(s_idx[0][0])
            sy: int = int(s_idx[1][0])
            sx: int = int(s_idx[2][0])

            return (
                float(origin.world_x + sx + 0.5),
                float(origin.world_y + sy + 0.5),
                float(sz) + settings.PLAYER_HEIGHT
            )

        c_center: int = settings.CHUNK_SIZE // 2
        column: NDArray[np.uint8] = origin.data[:, c_center, c_center]
        solid_indices: NDArray[np.int_] = np.where(column != ID_AIR)[0]

        if solid_indices.size > 0:
            h_z: float = float(solid_indices[-1])
            return (
                float(origin.world_x + c_center + 0.5),
                float(origin.world_y + c_center + 0.5),
                h_z + 1.0 + settings.PLAYER_HEIGHT
            )

        return (f_x, f_y, f_z)
