"""
Service layer for retrieving voxel data from disk or generation.
"""

import numpy as np
from numpy.typing import NDArray

import map.generator as generator
import map.loader as loader
from map.custom_map_buffer import MapManager
from settings import settings


class WorldProvider:
    """
    Manages the fallback sequence for sourcing chunk voxel data.
    """

    def __init__(self, world_id: str) -> None:
        """
        Initializes world identity and the static map manager.
        """
        self.world_id: str = world_id
        self.map_manager: MapManager = MapManager()

    def get_chunk_data(self, cx: int, cy: int) -> NDArray[np.uint8]:
        """
        Sequence: Check Disk -> Check Procedural -> Check Static Map.
        """
        # 1. Attempt load from existing save on disk
        saved_data = loader.load_chunk_from_disk(self.world_id, cx, cy)
        if saved_data is not None:
            return saved_data

        # 2. Fallback to procedural generation if enabled
        if settings.USE_PROCEDURAL:
            return generator.generate_chunk_data(cx, cy)
        
        # 3. Fallback to static file slicing
        return self.map_manager.get_chunk_slice(cx, cy)
