"""
Post-projection atmospheric and lighting effects.
"""

from typing import Final

import numpy as np
from numpy.typing import NDArray

import settings.settings as settings

# Pre-converted static colors for vectorized blending
SKY_RGB: Final[NDArray[np.float32]] = np.array(
    settings.SKY_COLOR, dtype=np.float32
)
HEIGHT_FOG_RGB: Final[NDArray[np.float32]] = np.array(
    settings.HEIGHT_FOG_RGB, dtype=np.float32
)


def apply_height_shading(
    colors: NDArray[np.float32],
    z_centers: NDArray[np.float32],
    height_shading_factor: float
) -> NDArray[np.float32]:
    """
    Darkens terrain based on depth from the map ceiling.
    """
    norm_depth: NDArray[np.float32] = np.clip(
        (settings.MAP_DEPTH - z_centers) / settings.MAP_DEPTH, 
        0.0, 1.0
    )
    
    falloff: NDArray[np.float32] = (
        norm_depth ** settings.HEIGHT_SHADING_EXPONENT
    )
    
    darken: NDArray[np.float32] = falloff * height_shading_factor * 100.0
    shaded: NDArray[np.float32] = colors - darken[:, np.newaxis]
    return np.clip(shaded, 0, 255)


def apply_height_fog(
    colors: NDArray[np.float32],
    z_centers: NDArray[np.float32],
    fog_density: float,
    fog_max_z: float,
    fog_fade: float
) -> NDArray[np.float32]:
    """
    Simulates a dense flat atmospheric volume that thickens with depth.
    """
    if fog_density <= 0:
        return colors

    under_surface: NDArray[np.float32] = np.clip(
        fog_max_z - z_centers, 0.0, None
    )
    submersion: NDArray[np.float32] = np.clip(
        under_surface / max(0.1, fog_fade), 0.0, 1.0
    )
    
    vis: NDArray[np.float32] = (1.0 - submersion) ** (fog_density * 4.0)
    vis_mask: NDArray[np.float32] = vis[:, np.newaxis]

    washout: NDArray[np.float32] = vis_mask ** 2.0
    avg_lum: NDArray[np.float32] = np.mean(colors, axis=1)[:, np.newaxis]
    
    flat_colors: NDArray[np.float32] = (
        (colors * washout) + (avg_lum * (1.0 - washout))
    )

    return (flat_colors * vis_mask) + (HEIGHT_FOG_RGB * (1.0 - vis_mask))


def apply_fog_effect(
    colors: NDArray[np.float32],
    euclidean_distances: NDArray[np.float32],
    render_dist: float,
    fog_density: float
) -> NDArray[np.float32]:
    """
    Blends voxel colors with the sky based on distance.
    """
    if render_dist <= 0 or fog_density <= 0:
        return colors

    rel_dist: NDArray[np.float32] = euclidean_distances / render_dist

    if settings.FOG_MODE == settings.FOG_MODE_LINEAR:
        visibility: NDArray[np.float32] = 1.0 - (rel_dist * fog_density)
    else:
        coeff: float = 1.5 * fog_density
        falloff: NDArray[np.float32] = (
            (rel_dist * coeff) ** settings.FOG_EXPONENT
        )
        visibility = np.exp(-falloff)

    vis_mask: NDArray[np.float32] = np.clip(
        visibility, 0.0, 1.0
    )[:, np.newaxis]
    
    return (colors * vis_mask) + (SKY_RGB * (1.0 - vis_mask))


def apply_visual_effects(
    colors: NDArray[np.float32],
    z_centers: NDArray[np.float32],
    euclidean_dist: NDArray[np.float32],
    render_dist: float,
    fog_density: float,
    use_h_shading: bool,
    height_shading_factor: float,
    height_fog_density: float,
    height_fog_max_z: float,
    height_fog_fade: float
) -> NDArray[np.int32]:
    """
    Orchestrates the visual post-processing pipeline.
    """
    proc_colors: NDArray[np.float32] = colors.copy()

    if use_h_shading:
        proc_colors = apply_height_shading(
            proc_colors, z_centers, height_shading_factor
        )
        
    proc_colors = apply_height_fog(
        proc_colors, z_centers, 
        height_fog_density, height_fog_max_z, height_fog_fade
    )

    proc_colors = apply_fog_effect(
        proc_colors, euclidean_dist, render_dist, fog_density
    )

    return np.clip(proc_colors, 0, 255).astype(np.int32)
