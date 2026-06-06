"""
Defines the Chunk container for voxel data and geometry sections.
"""

from typing import List, TYPE_CHECKING

from numpy.typing import NDArray
import numpy as np

from settings import settings

if TYPE_CHECKING:
    from world.spatial import Section


class Chunk:
    """
    Container for a 3D voxel grid and its geometric sub-sections.
    """

    def __init__(self, cx: int, cy: int, data: NDArray[np.uint8]) -> None:
        """
        Initializes chunk position and voxel data.
        """
        self.cx: int = cx
        self.cy: int = cy
        
        # World-space coordinates of the chunk origin
        self.world_x: int = cx * settings.CHUNK_SIZE
        self.world_y: int = cy * settings.CHUNK_SIZE

        # 3D voxel ID grid
        self.data: NDArray[np.uint8] = data
        self.sections: List["Section"] = []
        
        # State flags for the lifecycle manager
        self.is_meshed: bool = False
        self.is_dirty: bool = False
        
        # Indicates geometry is out of date but can still be rendered
        self.needs_remesh: bool = False
