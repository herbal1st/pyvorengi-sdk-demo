"""
Core 3D visual pipeline for projection and rasterization.
"""

from __future__ import annotations

from typing import Any

import pygame
import numpy as np
from numpy.typing import NDArray

from camera.camera import Camera
from physics.entity import Entity
from renderer.batch import BatchRenderer
from renderer.overlay import AtmosphericOverlay
from renderer.scene import SceneManager
from session.atmosphere import AtmosphereManager


class Renderer:
    """
    Pure scene renderer focusing on 3D geometry and volumetric post-effects.
    """

    def __init__(
        self, 
        screen: pygame.Surface, 
        world: Any, 
        atmo: AtmosphereManager
    ) -> None:
        """
        Sets up the scene, batcher, and volumetric post-processing.
        """
        self.screen: pygame.Surface = screen
        self.world: Any = world
        self.atmo: AtmosphereManager = atmo

        self.scene: SceneManager = SceneManager()
        self.batch: BatchRenderer = BatchRenderer(screen)
        self.atmos: AtmosphericOverlay = AtmosphericOverlay(screen)

    def render(
        self, 
        player: Entity, 
        camera: Camera, 
        clock: Any
    ) -> int:
        """
        Renders the 3D scene and returns the count of active faces drawn.
        """
        from settings import settings
        
        self.screen.fill(settings.SKY_COLOR)

        look, rgt, up = camera.get_orientation_vectors()
        cam_p: NDArray[np.float64] = np.array(player.position, dtype=np.float64)

        # Calculate altitude-based render distance throttling
        base_dist: float = self.atmo.render_dist
        trigger_z: float = (
            settings.MAP_DEPTH * settings.ALTITUDE_THROTTLE_HEIGHT_RATIO
        )
        
        if player.z > trigger_z:
            active_dist: float = base_dist * settings.ALTITUDE_THROTTLE_FACTOR
        else:
            active_dist = base_dist

        v_sections = self.scene.get_visible_chunks(
            self.world.chunks, cam_p, look, rgt, up, active_dist
        )
        
        self.batch.render_scene(
            visible_sections=v_sections, 
            cam_pos=cam_p, 
            view_params=camera.get_view_trig(),
            render_dist=active_dist,
            fog_density=self.atmo.fog_density,
            h_shade=self.atmo.use_height_shading, 
            h_shade_factor=self.atmo.height_shading_factor, 
            h_fog_dens=self.atmo.h_fog_dens, 
            h_fog_max_z=self.atmo.h_fog_max_z, 
            h_fog_fade=self.atmo.h_fog_fade
        )
        
        self._apply_volumetric_effects(player)

        return self.batch.active_face_count

    def update_screen_reference(self, new_screen: pygame.Surface) -> None:
        """
        Syncs surface across rendering sub-systems.
        """
        self.screen = new_screen
        self.batch.screen = new_screen
        self.atmos.screen = new_screen

    def _apply_volumetric_effects(self, player: Entity) -> None:
        """
        Draws screen-space haze washes based on immersion depth.
        """
        depth: float = (self.atmo.h_fog_max_z - player.z)
        fade: float = max(0.1, self.atmo.h_fog_fade)
        factor: float = np.clip(depth / fade, 0.0, 1.0)
        
        self.atmos.draw_haze_submersion(factor)
