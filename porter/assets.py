"""Loads, meshes, and caches standalone 3D voxel assets."""

from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from numpy.typing import NDArray

from map.registry import VoxelRegistry
from mesher import geometry
from utils.paths import PROJECT_ROOT


class VoxelAsset:
    """Represents a pre-compiled 3D voxel mesh asset."""

    def __init__(
        self,
        faces: NDArray[np.float32],
        width: float = 33.0,
        height: float = 33.0,
        depth: float = 1.0,
        is_flat: bool = False
    ) -> None:
        """Initializes the asset with its assembled face array and bounds."""
        self.faces: NDArray[np.float32] = faces
        self.width: float = width
        self.height: float = height
        self.depth: float = depth
        self.is_flat: bool = is_flat


class AssetCache:
    """Caches 3D assets to eliminate runtime disk I/O overhead."""

    def __init__(self) -> None:
        """Initializes the cache and block registry."""
        self.cache: Dict[str, VoxelAsset] = {}
        self.registry: VoxelRegistry = VoxelRegistry()

    def get_asset(
        self, 
        filename: str, 
        config: Optional[Dict[str, Any]] = None
    ) -> VoxelAsset:
        """Retrieves an asset from cache or loads it on the fly."""
        # Normalize slashes for cross-platform matching consistency
        norm_filename: str = filename.replace("\\", "/")

        if norm_filename in self.cache:
            return self.cache[norm_filename]

        asset: VoxelAsset = self._load_and_mesh(norm_filename, config)
        self.cache[norm_filename] = asset
        return asset

    def warm_up_cache(self, registry: Any) -> None:
        """Pre-warms the cache with all configured 3D assets."""
        print("[AssetCache] Pre-warming 3D voxel assets...")
        for key, config in registry.mappings.items():
            if config.get("render_3d", False):
                npz_filename: str = str(
                    Path(key).with_suffix(".npz")
                ).replace("\\", "/")
                self.get_asset(npz_filename, config)
        print(
            f"[AssetCache] Pre-warm completed. "
            f"Cached {len(self.cache)} asset(s)."
        )

    def _load_and_mesh(
        self, 
        filename: str, 
        config: Optional[Dict[str, Any]] = None
    ) -> VoxelAsset:
        """Loads an NPZ file and generates basic faces with culling."""
        file_path: Path = (
            PROJECT_ROOT / "porter" / "voxel_assets" / filename
        )
        if not file_path.exists():
            return VoxelAsset(np.empty((0, 19), dtype=np.float32))

        try:
            with np.load(file_path) as archive:
                voxels: NDArray[np.uint8] = archive["voxels"]
        except Exception as error:
            print(f"[AssetCache] Error loading {filename}: {error}")
            return VoxelAsset(np.empty((0, 19), dtype=np.float32))

        depth, length, width = voxels.shape
        solid: NDArray[np.bool_] = voxels > 0

        is_flat_asset: bool = False
        if config is not None:
            is_flat_asset = (config.get("thickness", 1.0) == 0.0)

        assembled_list: List[NDArray[np.float32]] = []

        for normal, v_offsets, _ in geometry.FACE_DATA:
            nx, ny, nz = normal

            if normal == (0, 0, -1):
                continue

            if is_flat_asset and normal != (0, 0, 1):
                continue

            exposed: NDArray[np.bool_] = np.zeros_like(solid)

            if normal == (0, 0, 1):
                if depth == 1:
                    exposed = solid.copy()
                else:
                    z_shift = np.roll(solid, -1, axis=0)
                    exposed = solid & ~z_shift
                    exposed[-1, :, :] = solid[-1, :, :]
            else:
                y_shift = (
                    np.roll(solid, -ny, axis=1)
                    if ny != 0 else solid
                )
                x_shift = (
                    np.roll(solid, -nx, axis=2)
                    if nx != 0 else solid
                )
                exposed = solid & ~x_shift if nx != 0 else exposed
                exposed = solid & ~y_shift if ny != 0 else exposed

                if nx == 1:
                    exposed[:, :, -1] = solid[:, :, -1]
                elif nx == -1:
                    exposed[:, :, 0] = solid[:, :, 0]
                elif ny == 1:
                    exposed[:, -1, :] = solid[:, -1, :]
                elif ny == -1:
                    exposed[:, 0, :] = solid[:, 0, :]

            indices: Tuple[NDArray[np.int_], ...] = np.where(exposed)
            if indices[0].size == 0:
                continue

            chunk_indices: Tuple[NDArray[np.int_], ...] = (
                indices[0],
                indices[1],
                indices[2],
            )

            face_buf = geometry.assemble_face_buffer(
                chunk_indices,
                indices,
                voxels,
                normal,
                v_offsets,
                self.registry
            )
            assembled_list.append(face_buf)

        if not assembled_list:
            return VoxelAsset(
                np.empty((0, 19), dtype=np.float32),
                float(width),
                float(length),
                float(depth),
                is_flat=is_flat_asset
            )

        stacked_faces: NDArray[np.float32] = np.concatenate(assembled_list)
        return VoxelAsset(
            stacked_faces,
            float(width),
            float(length),
            float(depth),
            is_flat=is_flat_asset
        )
