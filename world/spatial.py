"""
Defines spatial sub-volumes and basic geometric logic for chunk management.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, TypedDict

import numpy as np
from numpy.typing import NDArray

from settings import settings
from constants import constants

Normal = Tuple[int, int, int]
FaceBuffer = NDArray[np.float32]
GroupedFaces = Dict[Normal, FaceBuffer]


class MeshContext(TypedDict):
    """
    Encapsulates environmental state variables for the mesher.
    """
    cam_pos: Tuple[float, float, float]
    render_dist: float
    fog_density: float
    h_fog_dens: float
    h_fog_max_z: float
    h_fog_fade: float


@dataclass
class Section:
    """
    Represents a spatial sub-volume within a chunk.
    """
    bbox_min: NDArray[np.float32]
    bbox_max: NDArray[np.float32]
    center: NDArray[np.float32]
    radius: float
    grouped_faces: GroupedFaces
    chunk_wx: float
    chunk_wy: float
    grid_pos: Tuple[int, int, int]
    raw_stacked_faces: Optional[NDArray[np.float32]] = None


def create_section(
    faces: GroupedFaces,
    gx: int,
    gy: int,
    gz: int,
    wx: int,
    wy: int,
    z_range: Tuple[int, int],
    y_range: Tuple[int, int],
    x_range: Tuple[int, int]
) -> Section:
    """
    Factory method for Section creation and bounds calculation.
    """
    w_min: NDArray[np.float64] = np.array(
        [wx + x_range[0], wy + y_range[0], z_range[0]], dtype=np.float64
    )
    w_max: NDArray[np.float64] = np.array(
        [wx + x_range[1], wy + y_range[1], z_range[1]], dtype=np.float64
    )

    center: NDArray[np.float64] = (w_min + w_max) * 0.5
    radius: float = float(np.linalg.norm((w_max - w_min) * 0.5))

    face_list: List[NDArray[np.float32]] = []
    norm_list: List[NDArray[np.float32]] = []

    for norm, buf in faces.items():
        face_list.append(buf)
        norms: NDArray[np.float32] = np.tile(
            np.array(norm, dtype=np.float32), (len(buf), 1)
        )
        norm_list.append(norms)

    raw_faces, _ = _stack_section_data(face_list, norm_list, wx, wy)

    return Section(
        bbox_min=w_min.astype(np.float32),
        bbox_max=w_max.astype(np.float32),
        center=center.astype(np.float32),
        radius=radius,
        grouped_faces=faces,
        chunk_wx=float(wx),
        chunk_wy=float(wy),
        grid_pos=(gx, gy, gz),
        raw_stacked_faces=raw_faces
    )


def generate_search_grid(
    cam_x: float,
    cam_y: float,
    radius: float
) -> Tuple[NDArray[np.int32], NDArray[np.int32]]:
    """
    Calculates a flat grid of chunk coordinates around the camera.
    """
    rad_chunks: int = int(radius // settings.CHUNK_SIZE) + 2
    c_sx: int = int(cam_x // settings.CHUNK_SIZE)
    c_sy: int = int(cam_y // settings.CHUNK_SIZE)

    x_rng = np.arange(c_sx - rad_chunks, c_sx + rad_chunks + 1, dtype=np.int32)
    y_rng = np.arange(c_sy - rad_chunks, c_sy + rad_chunks + 1, dtype=np.int32)

    cx_g, cy_g = np.meshgrid(x_rng, y_rng)
    return cx_g.ravel(), cy_g.ravel()


def get_section_ranges(
    sz_idx: int,
    sy_idx: int,
    sx_idx: int
) -> Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]:
    """
    Calculates boundaries for a section within the padded volume.
    """
    z_start: int = sz_idx * constants.SECTION_SIZE_Z
    z_end: int = (sz_idx + 1) * constants.SECTION_SIZE_Z

    y_start: int = sy_idx * constants.SECTION_SIZE_XY
    y_end: int = (sy_idx + 1) * constants.SECTION_SIZE_XY

    x_start: int = sx_idx * constants.SECTION_SIZE_XY
    x_end: int = (sx_idx + 1) * constants.SECTION_SIZE_XY

    return (z_start, z_end), (y_start, y_end), (x_start, x_end)


def _stack_section_data(
    face_list: List[NDArray[np.float32]],
    norm_list: List[NDArray[np.float32]],
    wx: int,
    wy: int
) -> Tuple[NDArray[np.float32], NDArray[np.float32]]:
    """
    Merges direction-specific buffers into a single section array.
    """
    if not face_list:
        return (
            np.empty((0, 21), dtype=np.float32),
            np.empty((0, 3), dtype=np.float32)
        )

    all_faces: NDArray[np.float32] = np.concatenate(face_list)
    all_norms: NDArray[np.float32] = np.concatenate(norm_list)

    expanded: NDArray[np.float32] = np.zeros(
        (len(all_faces), 21), dtype=np.float32
    )
    expanded[:, 0:19] = all_faces
    expanded[:, 19] = float(wx)
    expanded[:, 20] = float(wy)

    return expanded, all_norms
