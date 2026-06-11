"""
Visibility culling using vectorized frustum-trapezoid tests.
"""

from typing import Final

import numpy as np
from numpy.typing import NDArray

from settings import settings
from constants import constants

# Expansion ratio for the view trapezoid
FOV_RATIO: Final[float] = (
    (constants.HALF_WIDTH / settings.FOV) * settings.FRUSTUM_MARGIN
)


class FrustumCuller:
    """
    Utility for performing sphere-vs-frustum visibility tests.
    """

    @staticmethod
    def cull_sections_vectorized(
        centers: NDArray[np.float32],
        cam_pos: NDArray[np.float32],
        look_v: NDArray[np.float32],
        right_v: NDArray[np.float32],
        up_v: NDArray[np.float32],
        max_dist: float,
    ) -> NDArray[np.bool_]:
        """
        Tests multiple sub-volumes for visibility in a single vectorized pass.
        """
        # Vector from camera to all sphere centers
        deltas: NDArray[np.float32] = centers - cam_pos

        # 1. Radial Check (Distance from camera)
        limit_sq: float = (max_dist + constants.SECTION_RADIUS) ** 2
        # Sum of squares instead of hypot
        dist_sq: NDArray[np.float32] = np.sum(np.square(deltas), axis=1)
        radial_mask: NDArray[np.bool_] = dist_sq <= limit_sq

        # 2. Forward Check (Z-Plane)
        # Scalar projection of delta onto look vector
        fwd_dist: NDArray[np.float32] = np.dot(deltas, look_v)
        fwd_mask: NDArray[np.bool_] = fwd_dist >= -constants.SECTION_MARGIN

        # 3. Width Check (View Trapezoid)
        side_dist: NDArray[np.float32] = np.abs(np.dot(deltas, right_v))
        side_limit: NDArray[np.float32] = (
            (fwd_dist * FOV_RATIO) + constants.SECTION_RADIUS
        )
        side_mask: NDArray[np.bool_] = side_dist <= side_limit

        # 4. Height Check (View Trapezoid)
        up_dist: NDArray[np.float32] = np.abs(np.dot(deltas, up_v))
        up_limit: NDArray[np.float32] = (
            (fwd_dist * constants.V_FOV_RATIO) + constants.SECTION_RADIUS
        )
        up_mask: NDArray[np.bool_] = up_dist <= up_limit

        # Result is the intersection of all boundary masks
        return radial_mask & fwd_mask & side_mask & up_mask
