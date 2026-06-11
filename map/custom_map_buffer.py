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
        Attempts to load map data with a fallback to the default showcase.
        """
        if settings.USE_PROCEDURAL:
            return None

        # 1. Primary Attempt: Load user-specified map
        if self.path.exists():
            return self._execute_load(self.path)

        # 2. Fallback Attempt: Load the default showcase map
        print(f"[MapManager] Warning: '{self.path.name}' not found.")
        fallback_path: Path = get_map_path("default_map.npz")

        if fallback_path.exists():
            print("[MapManager] Falling back to showcase matrix.")
            return self._execute_load(fallback_path)

        # 3. Critical Failure: Return empty world to prevent crash
        print(
            "[MapManager] Critical: No static maps found. "
            "Spawning in void."
        )
        return None

    def _execute_load(self, target_path: Path) -> Optional[NDArray[np.uint8]]:
        """
        Performs the actual file I/O and axis standardization.
        """
        try:
            with np.load(target_path) as archive:
                raw_voxels = archive["voxels"]
                return self._standardize_axes(raw_voxels)
        except Exception as error:
            print(f"[MapManager] Load error on {target_path.name}: {error}")
            return None

    def _standardize_axes(self, data: NDArray[Any]) -> NDArray[np.uint8]:
        """
        Ensures the loaded map matches the native ZYX memory order directly.
        """
        if data.ndim != 3:
            raise ValueError("Voxel map data must be 3-dimensional.")

        z_axis: int = int(np.argmin(data.shape))

        # Already in the native memory-contiguous (Z, Y, X) order
        if z_axis == 0:
            return data.astype(np.uint8)

        # Defensive fallback for legacy Cartesian (X, Y, Z) files
        order: Tuple[int, int, int] = (
            (2, 1, 0) if z_axis == 2 else (1, 0, 2)
        )
        transposed: NDArray[np.uint8] = np.transpose(data, order).astype(
            np.uint8
        )
        return transposed[:, :, ::-1]

    def get_chunk_slice(self, cx: int, cy: int) -> NDArray[np.uint8]:
        """
        Slices a chunk-sized volume out of the global map buffer.
        """
        grid_shape: Tuple[int, int, int] = (
            settings.MAP_DEPTH,
            settings.CHUNK_SIZE,
            settings.CHUNK_SIZE,
        )
        grid: NDArray[np.uint8] = np.zeros(grid_shape, dtype=np.uint8)

        if self.data is None:
            return grid

        x_start: int = cx * settings.CHUNK_SIZE
        y_start: int = cy * settings.CHUNK_SIZE
        z_lim, y_lim, x_lim = self.data.shape

        if (
            x_start >= x_lim
            or y_start >= y_lim
            or x_start < 0
            or y_start < 0
        ):
            return grid

        x_end: int = min(x_start + settings.CHUNK_SIZE, x_lim)
        y_end: int = min(y_start + settings.CHUNK_SIZE, y_lim)

        extracted = self.data[
            0 : settings.MAP_DEPTH, y_start:y_end, x_start:x_end
        ]
        sz, sy, sx = extracted.shape
        grid[0:sz, 0:sy, 0:sx] = extracted

        return grid
