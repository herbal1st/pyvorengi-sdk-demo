"""
Batch converts images (PNG/JPG) in /pic_imports into .npz voxel maps.
"""

from pathlib import Path
from typing import Tuple, List

import numpy as np
import pygame
from numpy.typing import NDArray

from map.registry import VoxelRegistry
from settings import settings
from utils.paths import PROJECT_ROOT


def run_batch_forge() -> None:
    """
    Scans the import directory for images and executes the pipeline.
    """
    pygame.init()
    # Initialize a hidden display to allow surface conversion
    pygame.display.set_mode((1, 1), pygame.NOFRAME)

    registry: VoxelRegistry = VoxelRegistry()

    # Path setup
    import_dir: Path = PROJECT_ROOT / "pic_imports"
    output_dir: Path = PROJECT_ROOT / "map" / "maps"
    import_dir.mkdir(exist_ok=True)

    # Supported formats
    valid_exts: Tuple[str, ...] = (".png", ".jpg", ".jpeg")
    img_files: List[Path] = [
        f for f in import_dir.iterdir()
        if f.suffix.lower() in valid_exts
    ]

    if not img_files:
        print(f"[Forge] No images found in {import_dir}.")
        return

    stats: dict[str, int] = {"created": 0, "skipped": 0, "failed": 0}
    print(f"[Forge] Scanning {len(img_files)} file(s)...")

    for img_path in img_files:
        result: str = _process_single_image(img_path, output_dir, registry)
        stats[result] += 1

    print(f"\n[Forge Report]")
    print(f"Created: {stats['created']} | "
          f"Skipped: {stats['skipped']} | "
          f"Failed:  {stats['failed']}")


def _process_single_image(
    path: Path,
    out_dir: Path,
    reg: VoxelRegistry
) -> str:
    """
    Converts one image to a voxel map if no naming conflict exists.
    """
    map_name: str = path.stem
    output_path: Path = out_dir / f"{map_name}.npz"

    if output_path.exists():
        print(f"[-] Skip: '{map_name}.npz' (Already exists)")
        return "skipped"

    try:
        # Load and force alpha channel support for math consistency
        raw_surf: pygame.Surface = pygame.image.load(str(path))
        surf: pygame.Surface = raw_surf.convert_alpha()

        pixels: NDArray[np.uint8] = pygame.surfarray.array3d(surf)
        alphas: NDArray[np.uint8] = pygame.surfarray.array_alpha(surf)

        # Color Matching
        ids, palette = _get_palette_data(reg)
        mask: NDArray[np.bool_] = alphas > 0
        active_rgb: NDArray[np.uint8] = pixels[mask]

        if active_rgb.size == 0:
            print(f"[!] Fail: '{path.name}' has no visible pixels.")
            return "failed"

        # Euclidean Comparison
        diff = (active_rgb[:, np.newaxis, :].astype(np.int32) -
                palette[np.newaxis, :, :].astype(np.int32))
        dist_sq: NDArray[np.int32] = np.sum(diff**2, axis=2)
        matched_ids: NDArray[np.uint8] = ids[np.argmin(dist_sq, axis=1)]

        # Allocation & Injection matching the new ZYX standard
        w, h = surf.get_size()
        vx: int = ((w // settings.CHUNK_SIZE) + 1) * settings.CHUNK_SIZE
        # Pad Y-axis for Launchpad (1 Chunk) + Empty Gap (1 Chunk) + Image
        vy: int = (
            ((h // settings.CHUNK_SIZE) + 1) * settings.CHUNK_SIZE
            + (2 * settings.CHUNK_SIZE)
        )

        vol: NDArray[np.uint8] = np.zeros(
            (settings.MAP_DEPTH, vy, vx),
            dtype=np.uint8
        )

        # Map color IDs to image grid
        id_grid: NDArray[np.uint8] = np.zeros((w, h), dtype=np.uint8)
        id_grid[mask] = matched_ids

        # Center calculations for spawn alignment within Chunk 0 constraints
        mid_index: int = settings.CHUNK_SIZE // 2
        spawn_x_final: int = min(w // 2, settings.CHUNK_SIZE - 1)

        plat_start: int = spawn_x_final - mid_index
        plat_end: int = spawn_x_final + mid_index

        # 1. Build Solid 16x16 Launchpad Runway at Z=0
        # Mapped to the pre-flip coordinate equivalent
        vol[0, 0:settings.CHUNK_SIZE, vx - plat_end : vx - plat_start] = 10

        # 2. Spawn point at Z=1 centered on our platform
        target_spawn_x: int = vx - 1 - spawn_x_final
        vol[1, mid_index, target_spawn_x] = 100

        # 3. Inject image structure at Z=0 (same height as the platform floor)
        # Offset Y by 2 chunks (Launchpad + Gap) and place the image
        y_start: int = 2 * settings.CHUNK_SIZE
        vol[0, y_start:y_start + h, vx - w : vx] = id_grid.T

        # 4. Flip horizontally along the X-axis (dimension 2) to bake in winding
        vol = vol[:, :, ::-1]

        np.savez_compressed(output_path, voxels=vol)
        print(f"[+] Forge: '{map_name}.npz' ({path.suffix.upper()})")
        return "created"

    except Exception as error:
        print(f"[!] Error on '{path.name}': {error}")
        return "failed"


def _get_palette_data(registry: VoxelRegistry) -> Tuple[NDArray, NDArray]:
    """
    Gathers valid block data for matrix-based comparison.
    """
    ids, rgbs = [], []
    for b_id, p in registry._cache.items():
        if p.get("color") and b_id not in (0, 100):
            ids.append(b_id)
            rgbs.append(p["color"])
    return np.array(ids), np.array(rgbs)


if __name__ == "__main__":
    run_batch_forge()
