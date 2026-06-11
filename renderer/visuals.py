"""
Optimized post-projection effects using in-place memory operations.
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
) -> None:
    """
    Darkens terrain based on depth from the map ceiling in-place.
    """
    # Calculate normalized depth (0.0 to 1.0)
    norm_depth: NDArray[np.float32] = (settings.MAP_DEPTH - z_centers)
    norm_depth /= settings.MAP_DEPTH
    np.clip(norm_depth, 0.0, 1.0, out=norm_depth)

    # Apply exponential contrast curve
    np.power(norm_depth, settings.HEIGHT_SHADING_EXPONENT, out=norm_depth)

    # Calculate final darkening magnitude
    norm_depth *= (height_shading_factor * 100.0)

    # Apply to colors in-place
    colors -= norm_depth[:, np.newaxis]
    np.clip(colors, 0, 255, out=colors)


def apply_height_fog(
    colors: NDArray[np.float32],
    z_centers: NDArray[np.float32],
    fog_density: float,
    fog_max_z: float,
    fog_fade: float
) -> None:
    """
    Simulates a dense flat atmospheric volume via in-place blending.
    """
    if fog_density <= 0:
        return

    # Calculate submersion factor
    submersion: NDArray[np.float32] = (fog_max_z - z_centers)
    np.clip(submersion, 0.0, None, out=submersion)
    submersion /= max(0.1, fog_fade)
    np.clip(submersion, 0.0, 1.0, out=submersion)

    # Determine visibility using power curve
    vis: NDArray[np.float32] = (1.0 - submersion)
    np.power(vis, (fog_density * 4.0), out=vis)
    vis_mask: NDArray[np.float32] = vis[:, np.newaxis]

    # Desaturate colors inside fog (washout)
    washout: NDArray[np.float32] = vis_mask ** 2.0
    avg_lum: NDArray[np.float32] = np.mean(colors, axis=1)[:, np.newaxis]

    colors *= washout
    colors += (avg_lum * (1.0 - washout))

    # Final blend with height fog color
    colors *= vis_mask
    colors += (HEIGHT_FOG_RGB * (1.0 - vis_mask))


def apply_fog_effect(
    colors: NDArray[np.float32],
    euclidean_distances: NDArray[np.float32],
    render_dist: float,
    fog_density: float
) -> None:
    """
    Blends voxel colors with the sky based on distance in-place.
    """
    if render_dist <= 0 or fog_density <= 0:
        return

    # Calculate distance ratio
    rel_dist: NDArray[np.float32] = euclidean_distances / render_dist

    if settings.FOG_MODE == settings.FOG_MODE_LINEAR:
        vis: NDArray[np.float32] = 1.0 - (rel_dist * fog_density)
    else:
        # Exponential falloff
        coeff: float = 1.5 * fog_density
        vis = (rel_dist * coeff)
        np.power(vis, settings.FOG_EXPONENT, out=vis)
        vis *= -1.0
        np.exp(vis, out=vis)

    np.clip(vis, 0.0, 1.0, out=vis)
    v_mask: NDArray[np.float32] = vis[:, np.newaxis]

    # In-place blend: (color * vis) + (sky * (1-vis))
    colors *= v_mask
    colors += (SKY_RGB * (1.0 - v_mask))


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
    Orchestrates the visual pipeline with minimal allocations.
    """
    # Create the single working buffer for this frame's visual pass
    proc_colors: NDArray[np.float32] = colors.copy()

    if use_h_shading:
        apply_height_shading(proc_colors, z_centers, height_shading_factor)

    apply_height_fog(
        proc_colors, z_centers,
        height_fog_density, height_fog_max_z, height_fog_fade
    )

    apply_fog_effect(proc_colors, euclidean_dist, render_dist, fog_density)

    # Final cast to integer for Pygame blitting
    np.clip(proc_colors, 0, 255, out=proc_colors)
    return proc_colors.astype(np.int32)
