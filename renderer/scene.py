"""
Scene management for visibility filtering and back-to-front sorting.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Tuple, TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from renderer.frustum import FrustumCuller
from settings import settings
from constants import constants

if TYPE_CHECKING:
    from world.world import Chunk
    from world.spatial import Section


class SceneManager:
    """
    Filters and sorts the world chunks for optimal painter-algorithm rendering.
    """

    def __init__(self) -> None:
        """
        Initializes the visibility culler.
        """
        self.culler: FrustumCuller = FrustumCuller()
        
        # Statistics tracking
        self.last_v_count: List[Section] = []

    def get_visible_chunks(
        self, 
        chunks: Dict[Tuple[int, int], "Chunk"], 
        cam: NDArray[np.float64],
        look: NDArray[np.float32], 
        right: NDArray[np.float32], 
        up: NDArray[np.float32],
        dist: float
    ) -> List["Section"]:
        """
        Gathers visible sections via a 3D-aware frustum sweep.
        """
        visible_sections: List["Section"] = []
        cam_f32: NDArray[np.float32] = cam.astype(np.float32)
        
        ccx: int = int(cam[0] // settings.CHUNK_SIZE)
        ccy: int = int(cam[1] // settings.CHUNK_SIZE)
        
        # Updated to use constants.CHUNK_RADIUS
        max_search: float = dist + constants.CHUNK_RADIUS
        radius: int = int(max_search // settings.CHUNK_SIZE) + 1

        x_range = self._get_sweep_range(ccx, radius, look[0])
        y_range = self._get_sweep_range(ccy, radius, look[1])

        for cx in x_range:
            for cy in y_range:
                self._process_chunk(
                    chunks, cx, cy, cam_f32, look, right, up, dist, 
                    visible_sections
                )

        self.last_v_count = visible_sections
        return visible_sections

    def _process_chunk(
        self,
        chunks: Dict[Tuple[int, int], "Chunk"],
        cx: int,
        cy: int,
        cam_f32: NDArray[np.float32],
        look: NDArray[np.float32],
        right: NDArray[np.float32],
        up: NDArray[np.float32],
        dist: float,
        out_sections: List["Section"]
    ) -> None:
        """
        Filters visible chunk sections using vectorized batch testing.
        """
        target: Optional["Chunk"] = chunks.get((cx, cy))
        
        # Early exit if chunk is missing or hasn't generated geometry
        if target is None or not target.is_meshed or not target.sections:
            return

        # Prepare section centers for batch processing
        section_list: List["Section"] = target.sections
        centers: NDArray[np.float32] = np.array(
            [s.center for s in section_list], 
            dtype=np.float32
        )

        # Execute vectorized visibility sweep
        visibility_mask: NDArray[np.bool_] = self.culler.cull_sections_vectorized(
            centers, cam_f32, look, right, up, dist
        )

        # Filter the section objects based on the boolean mask
        visible_subset: List["Section"] = [
            section_list[i] 
            for i, is_visible in enumerate(visibility_mask) 
            if is_visible
        ]

        # Apply painter-algorithm sorting to the visible subset
        if visible_subset:
            sorted_secs: List["Section"] = self._get_sorted_sections(
                visible_subset, look
            )
            out_sections.extend(sorted_secs)

    def _get_sweep_range(
        self, 
        center: int, 
        radius: int, 
        velocity: float
    ) -> Iterable[int]:
        """
        Returns background-to-foreground indices for the grid sweep.
        """
        low: int = center - radius
        high: int = center + radius
        
        # Looking Positive: background is at 'High', foreground is 'Low'
        if velocity >= 0:
            return range(high, low - 1, -1)
        
        # Looking Negative: background is at 'Low', foreground is 'High'
        return range(low, high + 1, 1)

    def _get_sorted_sections(
        self, 
        sections: List[Section], 
        look: NDArray[np.float32]
    ) -> List[Section]:
        """
        Deterministic topological sort for sections within a chunk.
        """
        # (Axis Index, Look Magnitude, Direction Sign)
        priority: List[Tuple[int, float, int]] = [
            (0, abs(look[0]), 1 if look[0] >= 0 else -1),
            (1, abs(look[1]), 1 if look[1] >= 0 else -1),
            (2, abs(look[2]), 1 if look[2] >= 0 else -1)
        ]
        
        # Sort axes by dominance to define primary sort keys
        priority.sort(key=lambda item: item[1], reverse=True)

        return sorted(
            sections, 
            key=lambda s: self._generate_sort_key(s, priority)
        )

    def _generate_sort_key(
        self, 
        sec: Section, 
        priority: List[Tuple[int, float, int]]
    ) -> Tuple[int, int, int]:
        """
        Generates a comparative tuple for axis-priority sorting.
        """
        keys: List[int] = []
        
        for idx, _, sign in priority:
            # Map grid pos based on direction to ensure back-to-front
            # If sign +1, higher values draw first (* -1)
            # If sign -1, lower values draw first (* +1)
            keys.append(sec.grid_pos[idx] * -sign)
            
        return (keys[0], keys[1], keys[2])
