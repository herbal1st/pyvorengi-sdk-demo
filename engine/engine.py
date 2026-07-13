"""
Core orchestrator for the Voxel Engine application.
"""

import sys
from typing import Tuple

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
        
        # Initialize building state variables
        self.current_build_id: int = settings.DEFAULT_BLOCK_ID

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

    def run(self) -> None:
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

    def cycle_build_block(self, direction: int) -> None:
        """
        Cycles the active buildable block ID smoothly with wrapping.
        """
        buildable_ids = self.world.registry.get_registered_ids()
        if not buildable_ids:
            return

        try:
            idx = buildable_ids.index(self.current_build_id)
        except ValueError:
            idx = 0

        new_idx = (idx + direction) % len(buildable_ids)
        self.current_build_id = buildable_ids[new_idx]

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
            total_sections=self._cached_t_sec,
            current_build_id=self.current_build_id
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
        
        # Disable volumetric overlays/darkening automatically for inspection maps
        if not settings.USE_PROCEDURAL:
            self.atmosphere.h_fog_max_z = 0.0
            self.atmosphere.h_fog_dens = 0.0
            self.atmosphere.height_shading_factor = 0.0

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
