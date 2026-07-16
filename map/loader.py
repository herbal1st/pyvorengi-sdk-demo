"""
Handles disk persistence for chunk data and world manifests.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
from numpy.typing import NDArray

from settings import settings
from utils.paths import get_save_path

# Version tag for data compatibility checks
VERSION_TAG: str = f"{settings.HEADER_PREFIX}{settings.MAP_VERSION}"


def generate_unique_world_id() -> str:
    """
    Creates a unique identifier for the world save folder.
    """
    algo_tag: str = _get_noise_algorithm_tag()

    return (
        f"procedural_{algo_tag}_S{settings.WORLD_SEED}_"
        f"CS{settings.CHUNK_SIZE}_MD{settings.MAP_DEPTH}"
    )


def clear_world_saves(world_id: str) -> None:
    """
    Safely purges cached chunk data files from the world directory.
    """
    root: Path = get_save_path(world_id)
    if not root.exists():
        return
        
    for f in root.glob("chunk_*.npz"):
        try:
            f.unlink()
        except OSError:
            pass


def _get_noise_algorithm_tag() -> str:
    """
    Returns a short string tag representing the active noise type.
    """
    if settings.ACTIVE_NOISE_TYPE == settings.NOISE_TYPE_PERLIN:
        return "PERL"
    return "SIMP"


def _ensure_world_dir(world_id: str) -> Path:
    """
    Returns world path and ensures the directory exists on disk.
    """
    path: Path = get_save_path(world_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_manifest(world_id: str, metadata: Dict[str, Any]) -> None:
    """
    Saves world metadata to a JSON manifest file.
    """
    root: Path = _ensure_world_dir(world_id)
    dest_path: Path = root / "manifest.json"
    
    with open(dest_path, "w") as file:
        json.dump(metadata, file, indent=4)


def load_manifest(world_id: str) -> Dict[str, Any]:
    """
    Loads metadata from manifest.json or returns defaults.
    """
    manifest_path: Path = get_save_path(world_id) / "manifest.json"

    if not manifest_path.exists():
        return {"generation_type": "unknown"}

    with open(manifest_path, "r") as file:
        return dict(json.load(file))


def save_chunk_to_disk(
    world_id: str,
    cx: int,
    cy: int,
    grid: NDArray[np.uint8]
) -> bool:
    """
    Saves a chunk array to a compressed .npz archive.
    """
    try:
        dest_path: Path = get_save_path(world_id) / f"chunk_{cx}_{cy}.npz"
        np.savez_compressed(dest_path, voxels=grid, version=VERSION_TAG)
        return True
    except Exception as error:
        print(f"[Loader] Save failed for {cx},{cy}: {error}")
        return False


def load_chunk_from_disk(
    world_id: str,
    cx: int,
    cy: int
) -> Optional[NDArray[np.uint8]]:
    """
    Loads chunk data if the file exists and version tag matches.
    """
    chunk_path: Path = get_save_path(world_id) / f"chunk_{cx}_{cy}.npz"

    if not chunk_path.exists():
        return None

    try:
        with np.load(chunk_path) as archive:
            if archive.get("version") != VERSION_TAG:
                return None
            return archive.get("voxels")
    except Exception:
        return None
