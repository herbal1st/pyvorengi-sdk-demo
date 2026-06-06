"""
Implements visibility tests to discard geometry outside the camera's FOV.
"""

from typing import Any, Final

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
        Performs 3D frustum tests against multiple section spheres at once.
        """
        # Vector from camera to all sphere centers
        deltas: NDArray[np.float32] = centers - cam_pos

        # 1. Radial Check: Euclidean distance from camera
        limit: float = max_dist + constants.SECTION_RADIUS
        # Using sum of squares for performance
        dist_sq: NDArray[np.float32] = np.sum(deltas**2, axis=1)
        radial_mask: NDArray[np.bool_] = dist_sq <= limit**2

        # 2. Forward Check: Plane-space Z-clipping
        fwd_distances: NDArray[np.float32] = np.dot(deltas, look_v)
        fwd_mask: NDArray[np.bool_] = (
            fwd_distances >= -constants.SECTION_MARGIN
        )

        # 3. Horizontal Boundary Check: View trapezoid width
        side_distances: NDArray[np.float32] = np.abs(np.dot(deltas, right_v))
        side_limits: NDArray[np.float32] = (
            (fwd_distances * FOV_RATIO) + constants.SECTION_RADIUS
        )
        side_mask: NDArray[np.bool_] = side_distances <= side_limits

        # 4. Vertical Boundary Check: View trapezoid height
        up_distances: NDArray[np.float32] = np.abs(np.dot(deltas, up_v))
        up_limits: NDArray[np.float32] = (
            (fwd_distances * constants.V_FOV_RATIO) + constants.SECTION_RADIUS
        )
        up_mask: NDArray[np.bool_] = up_distances <= up_limits

        # Combined intersection of all visibility tests
        return radial_mask & fwd_mask & side_mask & up_mask
