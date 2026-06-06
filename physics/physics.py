"""
Voxel-level collision queries and solidity checks.
"""

import math
from typing import Final, Optional, TYPE_CHECKING

from settings import settings

if TYPE_CHECKING:
    from world.storage.manager import World

# Probe heights relative to the entity base (feet and head)
PROBES: Final[list[float]] = [0.05, settings.PLAYER_HEIGHT]


class CollisionEngine:
    """
    Stateless utility for performing point-in-voxel collision tests.
    """

    def is_at_solid(
        self, 
        world: "World", 
        x: float, 
        y: float, 
        base_z: float
    ) -> bool:
        """
        Checks if a point column (x, y) intersects any solid geometry.
        """
        # Calculate integer grid coordinates
        ix: int = math.floor(x)
        iy: int = math.floor(y)

        # Check for solid blocks at each probe height
        for offset in PROBES:
            iz: int = math.floor(base_z + offset)
            if self._is_block_solid(world, ix, iy, iz):
                return True
                
        return False

    def _is_block_solid(
        self, 
        world: "World", 
        ix: int, 
        iy: int, 
        iz: int
    ) -> bool:
        """
        Checks if a specific grid coordinate contains a solid voxel.
        """
        # Fetch the voxel ID from the world manager
        vid: Optional[int] = world.get_voxel(float(ix), float(iy), float(iz))
        
        # Guard: Treat unloaded or out-of-bounds as non-solid
        if vid is None:
            return False
            
        return world.registry.is_solid(vid)
