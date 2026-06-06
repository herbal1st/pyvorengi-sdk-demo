"""
Handles coordinate remapping and slicing for static external map files.
"""

from pathlib import Path
from typing import Any, Optional, Tuple

import numpy as np
from numpy.typing import NDArray

from settings import settings
from utils.paths import get_map_path


class MapManager:
    """
    Manages loading and sub-sampling of pre-authored global voxel maps.
    """

    def __init__(self) -> None:
        """
        Initializes path and attempts to load the map buffer.
        """
        self.path: Path = get_map_path(settings.GLOBAL_MAP_NAME)
        self.data: Optional[NDArray[np.uint8]] = self._load_data()

    def _load_data(self) -> Optional[NDArray[np.uint8]]:
        """
        Attempts to load and transpose map data into (Z, Y, X) order.
        """
        if settings.USE_PROCEDURAL or not self.path.exists():
            return None

        try:
            with np.load(self.path) as archive:
                raw_voxels = archive["voxels"]
                return self._standardize_axes(raw_voxels)
        except Exception as error:
            print(f"[MapManager] Load error: {error}")
            return None

    def _standardize_axes(self, data: NDArray[Any]) -> NDArray[np.uint8]:
        """
        Standardizes axes to (Z, Y, X) and corrects winding-order chirality.
        """
        z_axis: int = int(np.argmin(data.shape))

        if z_axis == 0:
            return data.astype(np.uint8)

        # Standardize Cartesian (X, Y, Z) to Engine Memory (Z, Y, X)
        order: Tuple[int, int, int] = (2, 1, 0) if z_axis == 2 else (1, 0, 2)
        transposed: NDArray[np.uint8] = np.transpose(data, order).astype(
            np.uint8
        )

        # Reverse the X axis to correct the winding order chirality
        # This prevents backface culling from culling the outer shell
        return transposed[:, :, ::-1]

    def get_chunk_slice(self, cx: int, cy: int) -> NDArray[np.uint8]:
        """
        Slices a chunk-sized volume out of the global map buffer.
        """
        grid_shape: Tuple[int, int, int] = (
            settings.MAP_DEPTH,
            settings.CHUNK_SIZE,
            settings.CHUNK_SIZE
        )
        grid: NDArray[np.uint8] = np.zeros(grid_shape, dtype=np.uint8)

        if self.data is None:
            return grid

        x_start: int = cx * settings.CHUNK_SIZE
        y_start: int = cy * settings.CHUNK_SIZE
        z_lim, y_lim, x_lim = self.data.shape

        if x_start >= x_lim or y_start >= y_lim or x_start < 0 or y_start < 0:
            return grid

        x_end: int = min(x_start + settings.CHUNK_SIZE, x_lim)
        y_end: int = min(y_start + settings.CHUNK_SIZE, y_lim)

        extracted = self.data[0:settings.MAP_DEPTH, y_start:y_end, x_start:x_end]
        
        sz, sy, sx = extracted.shape
        grid[0:sz, 0:sy, 0:sx] = extracted

        return grid
