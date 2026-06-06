"""
Orchestrates voxel-to-mesh conversion for chunk sections.
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray

from mesher import geometry
from world.spatial import MeshContext


def generate_section_mesh(
    padded_data: NDArray[np.uint8],
    registry: Any,
    z_range: Tuple[int, int],
    y_range: Tuple[int, int],
    x_range: Tuple[int, int],
    context: Optional[MeshContext] = None
) -> Dict[Tuple[int, int, int], NDArray[np.float32]]:
    """
    Generates 1x1 face buffers for all visible directions in a section.
    """
    mesh_groups: Dict[Tuple[int, int, int], NDArray[np.float32]] = {}
    solid_mask: NDArray[np.bool_] = _create_solidity_mask(
        padded_data, registry
    )

    z0, z1 = z_range
    y0, y1 = y_range
    x0, x1 = x_range

    interior_ids: NDArray[np.uint8] = padded_data[
        z0 + 1 : z1 + 1, y0 + 1 : y1 + 1, x0 + 1 : x1 + 1
    ]
    interior_solid: NDArray[np.bool_] = solid_mask[
        z0 + 1 : z1 + 1, y0 + 1 : y1 + 1, x0 + 1 : x1 + 1
    ]

    if not np.any(interior_solid):
        return mesh_groups

    for normal, v_offsets, _ in geometry.FACE_DATA:
        buf: Optional[NDArray[np.float32]] = _generate_directional_faces(
            solid_mask,
            interior_ids,
            interior_solid,
            normal,
            v_offsets,
            registry,
            z_range,
            y_range,
            x_range,
        )

        if buf is not None:
            mesh_groups[normal] = buf

    return mesh_groups


def _create_solidity_mask(
    data: NDArray[np.uint8], registry: Any
) -> NDArray[np.bool_]:
    """
    Maps voxel IDs to a boolean mask indicating solidity.
    """
    unique_ids: NDArray[np.uint8] = np.unique(data)
    solid_ids: List[int] = [i for i in unique_ids if registry.is_solid(i)]
    return np.isin(data, solid_ids)


def _generate_directional_faces(
    solid_mask: NDArray[np.bool_],
    interior_ids: NDArray[np.uint8],
    interior_solid: NDArray[np.bool_],
    normal: Tuple[int, int, int],
    v_offsets: List[Tuple[int, int, int]],
    registry: Any,
    z_range: Tuple[int, int],
    y_range: Tuple[int, int],
    x_range: Tuple[int, int]
) -> Optional[NDArray[np.float32]]:
    """
    Generates standard 1x1 faces for a given direction normal.
    """
    nx, ny, nz = normal
    z0, z1 = z_range
    y0, y1 = y_range
    x0, x1 = x_range

    z_s = slice(z0 + 1 + nz, z1 + 1 + nz)
    y_s = slice(y0 + 1 + ny, y1 + 1 + ny)
    x_s = slice(x0 + 1 + nx, x1 + 1 + nx)

    visible_mask: NDArray[np.bool_] = (
        interior_solid & ~solid_mask[z_s, y_s, x_s]
    )
    indices: Tuple[NDArray[np.int_], ...] = np.where(visible_mask)

    if indices[0].size == 0:
        return None

    chunk_indices: Tuple[NDArray[np.int_], ...] = (
        indices[0] + z0,
        indices[1] + y0,
        indices[2] + x0,
    )

    return geometry.assemble_face_buffer(
        chunk_indices,
        indices,
        interior_ids,
        normal,
        v_offsets,
        registry
    )
