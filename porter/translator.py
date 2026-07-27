"""Provides spatial translation calculations between 2D and 3D frames."""

import math
from typing import Tuple, Dict, Any


class CoordinateTranslator:
    """Translates pixel coordinates and orientations into 3D space."""

    def __init__(self, screen_w: float, screen_h: float) -> None:
        """Initializes the translator with 2D bounds and tracking history."""
        self.sw: float = screen_w
        self.sh: float = screen_h

        # Map pixels to 3D block units (e.g., 25 pixels = 1 block)
        self.scale_factor: float = 25.0

        # Passive motion history matching id(actor) -> spatial state
        self._history: Dict[int, Dict[str, Any]] = {}

    def to_3d_coords(
        self, x_2d: float, y_2d: float, z_offset: float = 1.0
    ) -> Tuple[float, float, float]:
        """Translates flat 2D coordinates into a 3D world position."""
        x_3d: float = x_2d / self.scale_factor
        y_3d: float = (self.sh - y_2d) / self.scale_factor
        z_3d: float = z_offset

        return x_3d, y_3d, z_3d

    def get_passive_tilt_rad(
        self,
        actor_id: int,
        current_x: float,
        current_y: float,
        tilt_factor: float,
        tilt_agility: float = 1.0,
    ) -> float:
        """Passively profiles actor velocity to calculate dynamic tilt."""
        if actor_id not in self._history:
            self._history[actor_id] = {
                "prev_x": current_x,
                "prev_y": current_y,
                "current_tilt": 0.0,
                "active": True
            }

        state = self._history[actor_id]
        state["active"] = True

        # Extract movement delta along the X-axis
        dx: float = current_x - state["prev_x"]

        # Scale target calculation dynamically based on tilt agility
        scaled_input: float = dx * 0.1 * tilt_agility
        target_tilt: float = max(-1.0, min(1.0, scaled_input))

        # Scale interpolation speed dynamically based on agility
        lerp_factor: float = 0.15 * tilt_agility
        current_tilt: float = state["current_tilt"]
        current_tilt += (target_tilt - current_tilt) * lerp_factor

        # Cache coordinates for subsequent frames
        state["prev_x"] = current_x
        state["prev_y"] = current_y
        state["current_tilt"] = current_tilt

        # Return calculated tilt in radians scaled by dynamic tilt factor
        return math.radians(current_tilt * tilt_factor)

    def start_frame(self) -> None:
        """Marks all cached actor histories as inactive before updates."""
        for state in self._history.values():
            state["active"] = False

    def prune_inactive(self) -> None:
        """Removes cached history for actors no longer active this frame."""
        inactive_ids = [
            k for k, v in self._history.items() if not v["active"]
        ]
        for k in inactive_ids:
            del self._history[k]
