"""Compiles 2D PNG sprites into standalone 3D voxel .npz assets."""

from pathlib import Path
from typing import List, Tuple, Dict, Set
import numpy as np
import pygame
from numpy.typing import NDArray

from map.registry import VoxelRegistry
from porter.registry import PorterRegistry, get_qualified_key
from porter.porter_settings import PORTER_SCAN_DIRS
from utils.paths import PROJECT_ROOT


def compile_sprite(
    image_path: Path,
    output_dir: Path,
    registry: VoxelRegistry,
    relative_npz_path: str,
    thickness: int = 1,
) -> bool:
    """Converts a 2D PNG into a 3D voxel array, preserving subdirectories."""
    if not image_path.exists():
        print(f"[Compiler] Error: File not found {image_path.name}")
        return False

    try:
        raw_surf = pygame.image.load(str(image_path))
        surf: pygame.Surface = raw_surf.convert_alpha()
        w, h = surf.get_size()

        pixels: NDArray[np.uint8] = pygame.surfarray.array3d(surf)
        alphas: NDArray[np.uint8] = pygame.surfarray.array_alpha(surf)

        ids: List[int] = []
        rgbs: List[Tuple[int, int, int]] = []
        for b_id, props in registry._cache.items():
            color = registry.get_color(b_id)
            if color and b_id not in (0, 100):
                ids.append(b_id)
                rgbs.append(color)

        palette_ids = np.array(ids, dtype=np.uint8)
        palette_colors = np.array(rgbs, dtype=np.uint8)

        mask: NDArray[np.bool_] = alphas > 0
        active_rgb: NDArray[np.uint8] = pixels[mask]

        if active_rgb.size == 0:
            print(f"[Compiler] Skip: '{image_path.name}' is blank.")
            return False

        diff = (
            active_rgb[:, np.newaxis, :].astype(np.int32)
            - palette_colors[np.newaxis, :, :].astype(np.int32)
        )
        dist_sq: NDArray[np.int32] = np.sum(diff**2, axis=2)
        matched_ids: NDArray[np.uint8] = palette_ids[
            np.argmin(dist_sq, axis=1)
        ]

        id_grid: NDArray[np.uint8] = np.zeros((w, h), dtype=np.uint8)
        id_grid[mask] = matched_ids

        vol: NDArray[np.uint8] = np.zeros(
            (thickness, h, w), dtype=np.uint8
        )
        vol[:, :, :] = id_grid.T

        # Recursively construct target folders if they do not exist
        output_path: Path = output_dir / relative_npz_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        np.savez_compressed(output_path, voxels=vol)
        print(
            f"[Success] Compiled: '{image_path.name}' -> "
            f"'{relative_npz_path}' (Layers: {thickness})"
        )
        return True

    except Exception as error:
        print(
            f"[Compiler] Failed to compile '{image_path.name}': "
            f"{error}"
        )
        return False


def _clean_empty_directories(directory: Path) -> None:
    """Recursively removes empty subdirectories inside a path."""
    if not directory.exists():
        return
    for path in list(directory.rglob("*"))[::-1]:
        if path.is_dir() and not any(path.iterdir()):
            try:
                path.rmdir()
                print(f"[Compiler] Cleaned empty folder: {path.name}")
            except OSError:
                pass


def run_compilation() -> None:
    """Finds and compiles configured 3D sprites based on registry."""
    pygame.init()
    pygame.display.set_mode((1, 1), pygame.NOFRAME)

    voxel_reg = VoxelRegistry()
    porter_reg = PorterRegistry()
    output_dir: Path = PROJECT_ROOT / "porter" / "voxel_assets"

    # Map relative targets (e.g. 'ship/lights/lights 01.npz')
    active_paths: Set[str] = set()
    for name, config in porter_reg.mappings.items():
        if config.get("render_3d", False):
            npz_rel = str(Path(name).with_suffix(".npz")).replace("\\", "/")
            active_paths.add(npz_rel)

    # Perform recursive directory sweep to prune stale assets
    if output_dir.exists():
        for npz_path in output_dir.rglob("*.npz"):
            rel_npz = npz_path.relative_to(output_dir)
            rel_npz_str = str(rel_npz).replace("\\", "/")
            if rel_npz_str not in active_paths:
                try:
                    npz_path.unlink()
                    print(
                        f"[Compiler] Purged stale asset: {rel_npz_str}"
                    )
                except OSError as error:
                    print(
                        f"[Compiler] Error deleting "
                        f"{rel_npz_str}: {error}"
                    )

        # Remove empty folders left behind by the pruning sweep
        _clean_empty_directories(output_dir)

    scanned_files: Dict[str, Path] = {}
    for relative_dir in PORTER_SCAN_DIRS:
        target_path: Path = PROJECT_ROOT / relative_dir
        if not target_path.exists():
            continue

        for path in target_path.rglob("*"):
            if "voxel_assets" in path.parts:
                continue
            if path.suffix.lower() in (".png", ".jpg", ".jpeg"):
                key = get_qualified_key(path)
                scanned_files[key] = path

    print("[Compiler] Running YAML-driven sprite compilation...")

    compiled_count = 0
    for name, config in porter_reg.mappings.items():
        if not config.get("render_3d", False):
            continue

        if name in scanned_files:
            img_path = scanned_files[name]
            raw_thickness = config.get("thickness", 0.0)
            thickness_val = max(1, int(float(raw_thickness)))

            relative_npz_path = str(Path(name).with_suffix(".npz"))

            # Dynamic check: skip if .npz file already exists on disk
            target_npz = output_dir / relative_npz_path
            if target_npz.exists():
                try:
                    # Lazy load shape header to check if thickness matches
                    with np.load(target_npz) as archive:
                        # In ZYX, voxels shape is (thickness, height, width)
                        current_depth = archive["voxels"].shape[0]
                    if current_depth == thickness_val:
                        print(
                            f"[-] Skip: '{relative_npz_path}' "
                            f"already exists."
                        )
                        continue
                except Exception:
                    # If file is corrupted or unreadable, overwrite it
                    pass

            success = compile_sprite(
                img_path,
                output_dir,
                voxel_reg,
                relative_npz_path=relative_npz_path,
                thickness=thickness_val,
            )
            if success:
                compiled_count += 1
        else:
            print(f"[-] Missing source image for: {name}")

    print(f"[Compiler] Done. Compiled {compiled_count} asset(s).")


if __name__ == "__main__":
    run_compilation()
