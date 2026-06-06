"""
Defines the Camera class for player orientation and 3D vector math.
"""

import math
from typing import Tuple

import numpy as np
from numpy.typing import NDArray

from settings import settings


class Camera:
    """
    Manages the player's 3D orientation and orientation vectors.
    """

    def __init__(self) -> None:
        """
        Initializes camera rotation and limits from global settings.
        """
        self.yaw: float = 0.0
        self.yaw_velocity: float = 0.0
        self.pitch: float = 0.0
        self.sensitivity: float = settings.MOUSE_SENSITIVITY
        self.pitch_limit: float = settings.PITCH_LIMIT

    def update_rotation(self, rel_x: float, rel_y: float) -> None:
        """
        Updates yaw and pitch based on mouse movement deltas.
        """
        prev_yaw: float = self.yaw
        
        # Horizontal rotation
        self.yaw += rel_x * self.sensitivity
        self.yaw_velocity = self.yaw - prev_yaw

        # Vertical rotation with clamping
        raw_pitch: float = self.pitch - (rel_y * self.sensitivity)
        self.pitch = max(-self.pitch_limit, min(self.pitch_limit, raw_pitch))

    def get_view_trig(self) -> Tuple[float, float, float, float]:
        """
        Returns (sin_yaw, cos_yaw, sin_pitch, cos_pitch).
        """
        return (
            math.sin(self.yaw), 
            math.cos(self.yaw), 
            math.sin(self.pitch), 
            math.cos(self.pitch)
        )

    def get_orientation_vectors(
        self
    ) -> Tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.float32]]:
        """
        Calculates 3D unit vectors for look, right, and up directions.
        """
        s_y, c_y, s_p, c_p = self.get_view_trig()

        # Direction the camera is facing
        look: NDArray[np.float32] = np.array(
            [s_y * c_p, c_y * c_p, s_p], 
            dtype=np.float32
        )

        # Vector pointing to the player's right
        right: NDArray[np.float32] = np.array(
            [c_y, -s_y, 0], 
            dtype=np.float32
        )

        # Vector pointing to the camera's local 'up'
        up: NDArray[np.float32] = np.array(
            [-s_y * s_p, -c_y * s_p, c_p], 
            dtype=np.float32
        )

        return look, right, up

    def get_movement_vectors(self) -> Tuple[float, float, float, float]:
        """
        Returns (forward_x, forward_y, right_x, right_y) for 2D physics.
        """
        s_y: float = math.sin(self.yaw)
        c_y: float = math.cos(self.yaw)

        return s_y, c_y, c_y, -s_y
