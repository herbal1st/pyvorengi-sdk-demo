"""
Core orchestrator for the Voxel Engine application.
"""

import asyncio
import random
import sys
from typing import Tuple

import numpy as np
import pygame

from camera.camera import Camera
import controls.controls as controls
from engine.bootstrapper import WorldBootstrapper
from engine.clock import EngineClock
from engine.display import DisplayManager
from map.loader import generate_unique_world_id
from physics.entity import Entity
from renderer.renderer import Renderer
from session.atmosphere import AtmosphereManager
from ui.manager import UIManager
from settings import settings
from statemanager.statemanager import StateManager
from utils import paths
import world.logic.lifecycle as lifecycle
from world.session import WorldSession
from world.spatial import MeshContext
from world.storage.manager import World


class VoxelEngine:
    """
    Core orchestrator linking simulation logic, 3D visuals, and UI.
    """

    def __init__(self) -> None:
        """
        Initializes the engine subsystems and hardware context.
        """
        # Safety check to prevent double-initialization
        if not pygame.get_init():
            pygame.init()

        paths.check_environment()

        # Core hardware and state components
        self.display: DisplayManager = DisplayManager()
        self.clock: EngineClock = EngineClock()
        self.state_manager: StateManager = StateManager()
        self.running: bool = True

        # Simulation data components
        self.world: World = World()
        self.camera: Camera = Camera()
        self.atmosphere: AtmosphereManager = AtmosphereManager()
        
        # Player and visual pipeline
        self.player: Entity = self._init_player()
        self.renderer: Renderer = Renderer(
            self.display.screen, 
            self.world, 
            self.atmosphere
        )
        self.ui: UIManager = UIManager(self.display.screen)

        self._bootstrap_session()
        self._sync_hardware_state()

    async def run(self) -> None:
        """
        Main execution loop driving input, physics, and rendering.
        """
        while self.running:
            self.clock.tick()
            controls.process_input(self)

            while self.clock.consume_step():
                self._update_physics_logic()

            self._process_render_frame(self.clock.alpha)
            pygame.display.flip()
            
            # Non-blocking yield for the browser event loop
            await asyncio.sleep(1 / (settings.FPS * 2))

        self._shutdown()

    def toggle_fullscreen(self) -> None:
        """
        Refreshes surface references across all systems.
        """
        is_fs = self.state_manager.is_fullscreen
        surf = self.display.toggle_fullscreen(is_fs)

        self.state_manager.toggle_fullscreen()
        self.renderer.update_screen_reference(surf)
        self.ui.update_screen_reference(surf)

    def regenerate_world(self) -> None:
        """
        Clears the active world and spawns a new procedural landscape.
        """
        # Assign a random seed
        settings.WORLD_SEED = random.randint(1, 999999)
        
        # Force the global generator module to rebuild its noise instance
        import map.generator as generator
        generator.reinit_noise_generator()
        
        # Clear active cache and rebuild everything around the spawn
        self.world.chunks.clear()
        self._bootstrap_session()

    def cycle_noise_algorithm(self) -> None:
        """
        Toggles between Perlin and Simplex generation models.
        """
        if settings.ACTIVE_NOISE_TYPE == settings.NOISE_TYPE_PERLIN:
            settings.ACTIVE_NOISE_TYPE = settings.NOISE_TYPE_SIMPLEX
        else:
            settings.ACTIVE_NOISE_TYPE = settings.NOISE_TYPE_PERLIN
            
        import map.generator as generator
        generator.reinit_noise_generator()
        
        self.world.chunks.clear()
        self._bootstrap_session()

    def cycle_haze_height(self) -> None:
        """
        Cycles through valley haze height presets.
        """
        heights = [0.0, 5.0, 9.0, 15.0, 22.0]
        curr = self.atmosphere.h_fog_max_z
        next_idx = 0
        for i, h in enumerate(heights):
            if abs(curr - h) < 0.1:
                next_idx = (i + 1) % len(heights)
                break
        self.atmosphere.h_fog_max_z = heights[next_idx]
        self.atmosphere.needs_remesh = True

    def cycle_fog_density(self) -> None:
        """
        Cycles through distance fog density values.
        """
        densities = [0.0, 0.3, 0.7, 1.2, 2.0]
        curr = self.atmosphere.fog_density
        next_idx = 0
        for i, d in enumerate(densities):
            if abs(curr - d) < 0.1:
                next_idx = (i + 1) % len(densities)
                break
        self.atmosphere.fog_density = densities[next_idx]
        self.atmosphere.needs_remesh = True

    def cycle_sky_color(self) -> None:
        """
        Cycles through background sky color presets.
        """
        colors = [
            (20, 195, 230),  # Classic cyan
            (10, 20, 40),    # Midnight dark blue
            (240, 140, 80),  # Sunset orange
            (120, 160, 140), # Misty sage
        ]
        curr = settings.SKY_COLOR
        next_idx = 0
        for i, c in enumerate(colors):
            if curr == c:
                next_idx = (i + 1) % len(colors)
                break
        new_color = colors[next_idx]
        
        # Update both settings and the module-level array in visuals
        import settings.settings as settings_mod
        settings_mod.SKY_COLOR = new_color
        
        import renderer.visuals as visuals
        visuals.SKY_RGB = np.array(new_color, dtype=np.float32)
        self.atmosphere.needs_remesh = True

    def _update_physics_logic(self) -> None:
        """
        Executes a single step of physics if the game is not paused.
        """
        if not self.state_manager.is_playing:
            return

        self.player.store_previous_state()
        controls.process_input(self)

    def _process_render_frame(self, alpha: float) -> None:
        """
        Orchestrates the layered rendering of 3D world and 2D interface.
        """
        self._handle_atmosphere_sync()

        phys_pos = self.player.position
        self.player.x, self.player.y, self.player.z = \
            self.player.get_interpolated_position(alpha)

        face_count: int = self.renderer.render(
            self.player, self.camera, self.clock
        )

        if not hasattr(self, "_cached_t_sec"):
            self._cached_t_sec = 0
            self._frame_counter = 0

        if self.state_manager.show_debug and self._frame_counter % 10 == 0:
            self._cached_t_sec = sum(
                len(c.sections) for c in self.world.chunks.values()
            )
        self._frame_counter += 1

        self.ui.draw(
            state=self.state_manager,
            player_ref=self.player,
            atmo_ref=self.atmosphere,
            clock_ref=self.clock,
            active_faces=face_count,
            visible_sections=len(self.renderer.scene.last_v_count),
            total_sections=self._cached_t_sec
        )

        self.lifecycle.manage_updates(self.player, self.camera, self.renderer)
        self.player.x, self.player.y, self.player.z = phys_pos

    def _handle_atmosphere_sync(self) -> None:
        """
        Requests world remesh if atmospheric parameters have changed.
        """
        if not self.atmosphere.needs_remesh:
            return
            
        self.world.request_remesh()
        self.atmosphere.needs_remesh = False

    def _capture_context(self) -> MeshContext:
        """
        Wraps visual and atmospheric state for the meshing system.
        """
        return {
            "cam_pos": self.player.position,
            "render_dist": self.atmosphere.render_dist,
            "fog_density": self.atmosphere.fog_density,
            "h_fog_dens": self.atmosphere.h_fog_dens,
            "h_fog_max_z": self.atmosphere.h_fog_max_z,
            "h_fog_fade": self.atmosphere.h_fog_fade,
            "atmos_provider": self.atmosphere
        }

    def _bootstrap_session(self) -> None:
        """
        Initializes the world session and performs geometry bootstrap.
        """
        s_id: str = generate_unique_world_id()
        
        # Purge cached world state if config mandates clean run
        if settings.FORCE_FRESH_WORLD:
            import map.loader as loader
            loader.clear_world_saves(s_id)

        self.session: WorldSession = WorldSession.create(s_id)
        self.lifecycle: lifecycle.ChunkLifecycleManager = (
            lifecycle.ChunkLifecycleManager(self.world, self.session)
        )

        self.lifecycle.load_initial_chunks()
        self._place_player_at_spawn()
        self.atmosphere.sync_from_manifest(self.session.metadata)
        
        boot = WorldBootstrapper(
            self.world, self.lifecycle, self.player, self.renderer
        )
        boot.run_bootstrap()

    def _init_player(self) -> Entity:
        """
        Creates a player entity at the world spawn.
        """
        sx, sy, sz = self.world.find_spawn_point()
        return Entity(sx, sy, sz)

    def _place_player_at_spawn(self) -> None:
        """
        Forces player to world spawn coordinates.
        """
        spawn: Tuple[float, float, float] = self.world.find_spawn_point()
        self.player.x, self.player.y, self.player.z = spawn
        self.player.store_previous_state()

    def _sync_hardware_state(self) -> None:
        """
        Applies initial OS-level hardware configurations.
        """
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

    def _shutdown(self) -> None:
        """
        Gracefully terminates resources.
        """
        self.lifecycle.stop()
        pygame.quit()
        sys.exit()
