"""
Defines immutable engine constants derived from base settings.
"""

import numpy as np
from settings import settings


# --- Display ---
WIDTH: int = settings.SCREEN_RES[0]
HEIGHT: int = settings.SCREEN_RES[1]
HALF_WIDTH: int = WIDTH // 2
HALF_HEIGHT: int = HEIGHT // 2

# ------ Optimization & Loading ------
V_FOV_RATIO: float = (HALF_HEIGHT / settings.FOV) * settings.FRUSTUM_MARGIN

# ------ Culling Radius Calculations ------
_CHUNK_HALF_XY: float = settings.CHUNK_SIZE * 0.5
_CHUNK_MID_Z: float = settings.MAP_DEPTH * 0.5
_RAW_RAD: list[float] = [_CHUNK_HALF_XY, _CHUNK_HALF_XY, _CHUNK_MID_Z]
_CORE_RADIUS: float = float(np.linalg.norm(_RAW_RAD))
CHUNK_RADIUS: float = _CORE_RADIUS * 1.635
CHUNK_MARGIN: float = CHUNK_RADIUS

# ------ Sectioning (Sub-chunks) ------
SECTION_SIZE_XY: int = settings.CHUNK_SIZE // settings.SECTION_DIVS_XY
SECTION_SIZE_Z: int = settings.MAP_DEPTH // settings.SECTION_DIVS_Z
_SEC_HALF_RAW: list[float] = [
    SECTION_SIZE_XY * 0.5,
    SECTION_SIZE_XY * 0.5,
    SECTION_SIZE_Z * 0.5
]
_SEC_RADIUS: float = float(np.linalg.norm(_SEC_HALF_RAW))
SECTION_RADIUS: float = _SEC_RADIUS * 1.635
SECTION_MARGIN: float = SECTION_RADIUS
