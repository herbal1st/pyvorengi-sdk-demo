"""
Service layer for retrieving voxel data from disk or generation.
"""

import numpy as np
from numpy.typing import NDArray

import map.generator as generator
import map.loader as loader


class WorldProvider:
    """
    Manages the fallback sequence for sourcing chunk voxel data.
    """

    def __init__(self, world_id: str) -> None:
        """
        Initializes world identity.
        """
        self.world_id: str = world_id

    def get_chunk_data(self, cx: int, cy: int) -> NDArray[np.uint8]:
        """
        Sequence: Check Disk -> Generate Procedural.
        """
        # 1. Attempt load from existing save on disk
        saved_data = loader.load_chunk_from_disk(self.world_id, cx, cy)
        if saved_data is not None:
            return saved_data

        # 2. Procedural generation fallback
        return generator.generate_chunk_data(cx, cy)
