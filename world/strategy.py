"""
Logic for spatial update triggers and circular candidate selection.
"""

from typing import List, Tuple

import numpy as np
from numpy.typing import NDArray

from settings import settings
from world.spatial import generate_search_grid


class LifecycleStrategist:
    """
    Determines spatial update triggers using standard distance sweeps.
    """

    def __init__(self) -> None:
        """
        Initializes tracking coordinates for movement thresholds.
        """
        self.last_pos: NDArray[np.float32] = np.zeros(2, dtype=np.float32)
        self.last_yaw: float = 0.0

    def needs_update(
        self,
        player_pos: Tuple[float, float],
        camera_yaw: float
    ) -> bool:
        """
        Checks if the player has exceeded spatial update thresholds.
        """
        curr_p: NDArray[np.float32] = np.array(player_pos, dtype=np.float32)

        m_dist: float = float(np.linalg.norm(curr_p - self.last_pos))
        y_dist: float = abs(np.degrees(camera_yaw - self.last_yaw))

        pos_triggered: bool = m_dist > settings.MOVEMENT_UPDATE_THRESHOLD
        rot_triggered: bool = y_dist > settings.ROTATION_UPDATE_THRESHOLD

        return pos_triggered or rot_triggered

    def update_tracking(
        self,
        player_pos: Tuple[float, float],
        camera_yaw: float
    ) -> None:
        """
        Stores baseline coordinates for subsequent checks.
        """
        self.last_pos = np.array(player_pos, dtype=np.float32)
        self.last_yaw = camera_yaw

    def get_loading_candidates(
        self,
        cam_x: float,
        cam_y: float,
        radius: float
    ) -> List[Tuple[int, int]]:
        """
        Identifies grid coordinates falling inside the circular load radius.
        """
        flat_cx, flat_cy = generate_search_grid(cam_x, cam_y, radius)

        c_off: float = settings.CHUNK_SIZE / 2.0
        wx: NDArray[np.float32] = (flat_cx * settings.CHUNK_SIZE) + c_off
        wy: NDArray[np.float32] = (flat_cy * settings.CHUNK_SIZE) + c_off

        dist_sq: NDArray[np.float32] = (wx - cam_x) ** 2 + (wy - cam_y) ** 2
        limit_sq: float = radius ** 2

        mask: NDArray[np.bool_] = dist_sq <= limit_sq
        indices: NDArray[np.intp] = np.where(mask)[0]

        return [(int(flat_cx[i]), int(flat_cy[i])) for i in indices]
