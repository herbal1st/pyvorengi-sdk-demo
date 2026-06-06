"""
Centralized project directory and file resolution.
"""

import sys
from pathlib import Path

# Resolve project root relative to this file's location
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent


def get_data_path(filename: str) -> Path:
    """
    Returns the absolute path to a file in the data/ directory.
    """
    return PROJECT_ROOT / "data" / filename


def get_save_path(world_id: str) -> Path:
    """
    Returns the absolute path to a specific world save folder.
    """
    return PROJECT_ROOT / "saves" / world_id


def get_map_path(filename: str) -> Path:
    """
    Returns the absolute path to a static map file.
    """
    return PROJECT_ROOT / "map" / "maps" / filename


def check_environment() -> None:
    """
    Validates and ensures critical folder structures exist.
    """
    required_dirs: list[Path] = [
        PROJECT_ROOT / "data",
        PROJECT_ROOT / "map/maps",
        PROJECT_ROOT / "saves",
    ]

    for directory in required_dirs:
        if directory.exists():
            continue
            
        print(f"[Critical] Environment Error: Missing folder {directory}")
        sys.exit(1)