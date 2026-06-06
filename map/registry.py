"""
Voxel registry for block properties and YAML definitions.
"""

from pathlib import Path
from typing import Any, Dict, Final, Optional, Tuple

import numpy as np
import yaml
from numpy.typing import NDArray

from utils.paths import get_data_path

# --- Constants & Mapping ---
# Normal to semantic face name mapping
_FACE_MAP: Final[Dict[Tuple[int, int, int], str]] = {
    (0, 0, 1): "top",
    (0, 0, -1): "bottom",
    (0, 1, 0): "north",
    (0, -1, 0): "south",
    (1, 0, 0): "east",
    (-1, 0, 0): "west",
}

# Standard Block IDs
ID_AIR: Final[int] = 0
ID_GRASS: Final[int] = 1
ID_DIRT: Final[int] = 2
ID_STONE: Final[int] = 3
ID_BEDROCK: Final[int] = 4
ID_WATER: Final[int] = 5
ID_ICE: Final[int] = 6
ID_SNOW: Final[int] = 7
ID_SAND: Final[int] = 8
ID_LAVA: Final[int] = 9
ID_OBSIDIAN: Final[int] = 10
ID_WOOD: Final[int] = 11
ID_GOLD: Final[int] = 12
ID_DIAMOND: Final[int] = 13
ID_EMERALD: Final[int] = 14
ID_SPAWN: Final[int] = 100


class VoxelRegistry:
    """
    Lookup for block properties defined in external configuration.
    """

    def __init__(self) -> None:
        """
        Initializes the registry and loads definitions from disk.
        """
        # Path to the block definition file
        self.path: Path = get_data_path("voxels.yaml")
        
        # Internal cache for block properties
        self._cache: Dict[int, Dict[str, Any]] = {}
        
        self._load_definitions()

    def get_color_palette(
        self, 
        normal: Tuple[int, int, int]
    ) -> NDArray[np.uint8]:
        """
        Generates a NumPy lookup table (LUT) for block colors on a specific face.
        """
        # Create a palette for all possible 256 block IDs
        palette: NDArray[np.uint8] = np.zeros((256, 3), dtype=np.uint8)

        for b_id, props in self._cache.items():
            # Retrieve specific face color or fallback to default
            color: Optional[Tuple[int, int, int]] = self.get_color(b_id, normal)
            if color:
                palette[b_id] = color

        return palette

    def get_color(
        self,
        b_id: int,
        normal: Optional[Tuple[int, int, int]] = None
    ) -> Optional[Tuple[int, int, int]]:
        """
        Retrieves the RGB color for a specific block ID and face normal.
        """
        # Retrieve properties from cache
        props: Optional[Dict[str, Any]] = self._cache.get(b_id)
        
        # Guard: Block ID not registered
        if not props:
            return None

        # 1. Attempt to fetch face-specific color override
        if normal and (face_name := _FACE_MAP.get(normal)):
            face_colors: Dict[str, list] = props.get("face_colors", {})
            if face_name in face_colors:
                color_val = face_colors[face_name]
                return (int(color_val[0]), int(color_val[1]), int(color_val[2]))

        # 2. Fallback to default block color
        default_color = props.get("color")
        
        # Guard: No color data available
        if not default_color:
            return None

        return (
            int(default_color[0]),
            int(default_color[1]),
            int(default_color[2])
        )

    def is_solid(self, b_id: int) -> bool:
        """
        Checks if a block ID represents a solid voxel.
        """
        return self._cache.get(b_id, {}).get("solid", False)

    def is_spawn(self, b_id: int) -> bool:
        """
        Checks if a block ID is designated as a spawn marker.
        """
        return self._cache.get(b_id, {}).get("is_spawn", False)

    def _load_definitions(self) -> None:
        """
        Parses YAML block definitions and populates the cache.
        """
        # Fallback to .yaml.txt if .yaml is missing
        target: Path = self.path
        if not target.exists():
            target = self.path.with_suffix(".yaml.txt")

        # Guard: File not found
        if not target.exists():
            return

        try:
            with open(target, "r", encoding="utf-8") as file:
                raw_data: Dict[str, Any] = yaml.safe_load(file) or {}
                blocks: list = raw_data.get("blocks", [])
                
                # Map block data by their integer IDs
                self._cache = {
                    b["id"]: b for b in blocks if "id" in b
                }
        except Exception as error:
            print(f"[Registry] YAML Error: {error}")
