"""
Implements 2D noise algorithms for procedural terrain generation.
"""

import math
import random
from typing import List, Final

# Skewing and unskewing factors for 2D Simplex noise
_F2: Final[float] = 0.5 * (math.sqrt(3.0) - 1.0)
_G2: Final[float] = (3.0 - math.sqrt(3.0)) / 6.0

# Predefined gradients for Simplex noise
_GRAD3: Final[List[List[int]]] = [
    [1, 1, 0], [-1, 1, 0], [1, -1, 0], [-1, -1, 0],
    [1, 0, 1], [-1, 0, 1], [1, 0, -1], [-1, 0, -1],
    [0, 1, 1], [0, -1, 1], [0, 1, -1], [0, -1, -1]
]


class PerlinNoise:
    """
    A 2D Perlin noise generator producing smooth pseudo-random values.
    """

    def __init__(self, seed: int = 42) -> None:
        """
        Initializes the permutation table using a fixed seed.
        """
        permutation: List[int] = list(range(256))
        random.seed(seed)
        random.shuffle(permutation)

        # Double the table to eliminate modulo wraps during hashing
        self.p: List[int] = permutation + permutation

    def noise(self, x: float, y: float) -> float:
        """
        Samples the noise field at (x, y). Returns value in range [0.0, 1.0].
        """
        # Identify grid cell and fractional offsets
        xi: int = int(math.floor(x)) & 255
        yi: int = int(math.floor(y)) & 255

        xf: float = x - math.floor(x)
        yf: float = y - math.floor(y)

        # Smooth the fractional components (Quintic Fade)
        u: float = self._fade(xf)
        v: float = self._fade(yf)

        # Hash corners and interpolate
        raw_val: float = self._interpolate_cell(xi, yi, xf, yf, u, v)

        # Normalize from [-1.0, 1.0] to [0.0, 1.0]
        normalized: float = (raw_val + 1.0) / 2.0

        return max(0.0, min(1.0, normalized))

    def _fade(self, t: float) -> float:
        """
        Quintic interpolation curve: 6t^5 - 15t^4 + 10t^3.
        """
        return t * t * t * (t * (t * 6 - 15) + 10)

    def _grad(self, hash_val: int, x: float, y: float) -> float:
        """
        Calculates dot product between pseudo-random gradient and distance.
        """
        h: int = hash_val & 7
        u: float = x if h < 4 else y
        v: float = y if h < 4 else x

        g_u: float = u if (h & 1) == 0 else -u
        g_v: float = v if (h & 2) == 0 else -v

        return g_u + g_v

    def _interpolate_cell(
        self,
        xi: int,
        yi: int,
        xf: float,
        yf: float,
        u: float,
        v: float
    ) -> float:
        """
        Bilinearly interpolates gradients from the unit square corners.
        """
        p: List[int] = self.p

        # Hash corner coordinates
        aa: int = p[p[xi] + yi]
        ab: int = p[p[xi] + yi + 1]
        ba: int = p[p[xi + 1] + yi]
        bb: int = p[p[xi + 1] + yi + 1]

        # Calculate corner gradients
        g1: float = self._grad(aa, xf, yf)
        g2: float = self._grad(ba, xf - 1, yf)
        g3: float = self._grad(ab, xf, yf - 1)
        g4: float = self._grad(bb, xf - 1, yf - 1)

        # Horizontal interpolation
        layer_1: float = g1 + u * (g2 - g1)
        layer_2: float = g3 + u * (g4 - g3)

        # Vertical interpolation
        return layer_1 + v * (layer_2 - layer_1)


class SimplexNoise:
    """
    A 2D Simplex noise generator for faster, high-contrast terrain.
    """

    def __init__(self, seed: int = 42) -> None:
        """
        Initializes the permutation table and internal gradients.
        """
        perm: List[int] = list(range(256))
        random.seed(seed)
        random.shuffle(perm)

        # Doubled permutation table for seamless wrapping
        self.p: List[int] = perm + perm

        # Modulo-mapped gradients for optimization
        self.perm_grad_index: List[int] = [i % 12 for i in self.p]

    def noise(self, x: float, y: float) -> float:
        """
        Samples the 2D Simplex field. Returns value in range [0.0, 1.0].
        """
        # Skew input space to determine which simplex cell we are in
        s: float = (x + y) * _F2
        i, j = math.floor(x + s), math.floor(y + s)

        # Unskew the cell origin back to (x, y) space
        t: float = (i + j) * _G2
        x0, y0 = x - (i - t), y - (j - t)

        # Determine which of the two triangles we are in
        i1, j1 = (1, 0) if x0 > y0 else (0, 1)

        # Offsets for the middle and last corners
        x1, y1 = x0 - i1 + _G2, y0 - j1 + _G2
        x2, y2 = x0 - 1.0 + 2.0 * _G2, y0 - 1.0 + 2.0 * _G2

        # Wrap indices for lookup
        ii, jj = i & 255, j & 255

        # Calculate contributions from each of the three corners
        n0 = self._get_corner_contribution(x0, y0, self.p[ii + self.p[jj]])
        n1 = self._get_corner_contribution(x1, y1, self.p[ii + i1 + self.p[jj + j1]])
        n2 = self._get_corner_contribution(x2, y2, self.p[ii + 1 + self.p[jj + 1]])

        # Sum and scale to [0, 1] range
        raw: float = 70.0 * (n0 + n1 + n2)
        return (raw + 1.0) * 0.5

    def _get_corner_contribution(self, x: float, y: float, hash_v: int) -> float:
        """
        Calculates the noise contribution from a single simplex corner.
        """
        t: float = 0.5 - x * x - y * y

        # Guard: Corner is too far away to contribute
        if t < 0:
            return 0.0

        # Select gradient vector from the hash
        gi: int = self.perm_grad_index[hash_v]
        grad: List[int] = _GRAD3[gi]

        # Calculate t^4 * (grad . dist)
        return (t * t) * (t * t) * (grad[0] * x + grad[1] * y)
