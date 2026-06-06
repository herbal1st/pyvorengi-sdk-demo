"""
Global manager for coordinate-based chunk access and voxel queries.
"""

import math
from typing import Dict, Optional, Tuple

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
        # Chunk map indexed by (cx, cy) grid coordinates
        self.chunks: Dict[Tuple[int, int], Chunk] = {}
        
        # Block property lookup
        self.registry: VoxelRegistry = VoxelRegistry()

        # Flag indicating that meshes need recalculation
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

        # Guard: Vertical bounds
        if not (0 <= iz < settings.MAP_DEPTH):
            return None

        # Determine chunk identity
        cx: int = ix // settings.CHUNK_SIZE
        cy: int = iy // settings.CHUNK_SIZE
        
        chunk: Optional[Chunk] = self.chunks.get((cx, cy))
        if chunk is None:
            return None

        # Resolve clean local coordinate indices
        lx: int = ix % settings.CHUNK_SIZE
        ly: int = iy % settings.CHUNK_SIZE
        
        return int(chunk.data[iz, ly, lx])

    def find_spawn_point(self) -> Tuple[float, float, float]:
        """
        Locates the spawn block or calculates a ground fallback.
        """
        # Default coordinates (center-map)
        f_x: float = 0.5
        f_y: float = 0.5
        f_z: float = float(settings.MAP_DEPTH // 2)

        origin: Optional[Chunk] = self.chunks.get((0, 0))
        if origin is None:
            return (f_x, f_y, f_z)

        # 1. Scan for specific spawn marker ID
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

        # 2. Fallback: Identify terrain height at origin coordinate
        # Sample the column at world (0,0) which is (1,1) in haloed data
        column: NDArray[np.uint8] = origin.data[:, 1, 1]
        solid_indices: NDArray[np.int_] = np.where(column != ID_AIR)[0]

        if solid_indices.size > 0:
            h_z: float = float(solid_indices[-1])
            return (f_x, f_y, h_z + 1.0 + settings.PLAYER_HEIGHT)

        return (f_x, f_y, f_z)
