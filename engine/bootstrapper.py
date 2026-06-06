"""
Handles the initial loading and meshing synchronization for the world.
"""

import math
import pygame
from typing import TYPE_CHECKING
from settings import settings

if TYPE_CHECKING:
    from world.world import World
    from world.lifecycle import ChunkLifecycleManager
    from physics.entity import Entity
    from renderer.renderer import Renderer


class WorldBootstrapper:
    """
    Ensures a minimum radius of geometry is generated before starting the loop.
    """

    def __init__(
        self, 
        world: "World", 
        lifecycle: "ChunkLifecycleManager", 
        player: "Entity", 
        renderer: "Renderer"
    ) -> None:
        """
        Initializes the bootstrapper with required subsystem references.
        """
        self.world = world
        self.lifecycle = lifecycle
        self.player = player
        self.renderer = renderer

    def run_bootstrap(self) -> None:
        """
        Blocks execution until the critical area is meshed or a timeout occurs.
        """
        start_time: float = pygame.time.get_ticks() / 1000.0
        
        # Determine the radius required for a stable visual start
        target_rad: float = self._calculate_critical_radius()

        print(f"[Engine] Bootstrapping (Target: {target_rad:.1f}m)...")

        while True:
            # Force high-priority loading
            self.lifecycle.update_circular(self.player, self.renderer)

            if self._is_area_ready(target_rad):
                break

            # Guard: Exit on hardware timeout
            elapsed: float = (pygame.time.get_ticks() / 1000.0) - start_time
            if elapsed > settings.BOOTSTRAP_TIMEOUT:
                print("[Engine] Bootstrap timeout. Entering world.")
                break

            pygame.time.wait(10)

        print("[Engine] Core Ready.")

    def _calculate_critical_radius(self) -> float:
        """
        Calculates the distance requiring completion before play.
        """
        # Distance requiring completion before play
        load_limit: float = settings.INITIAL_RENDER_DIST + settings.LOAD_MARGIN
        
        # Subtract one chunk to ensure neighbor visibility for meshes
        safe_limit: float = load_limit - settings.CHUNK_SIZE
        
        return min(settings.SAFETY_RADIUS, safe_limit)

    def _is_area_ready(self, radius: float) -> bool:
        """
        Checks if all chunks within range have finalized geometry.
        """
        c_size: int = settings.CHUNK_SIZE
        cx: int = int(self.player.x // c_size)
        cy: int = int(self.player.y // c_size)
        
        # Convert radius to grid units
        rad_chunks: int = int(math.ceil(radius / c_size))

        for dx in range(-rad_chunks, rad_chunks + 1):
            for dy in range(-rad_chunks, rad_chunks + 1):
                if not self._is_chunk_ready(cx + dx, cy + dy, radius):
                    return False
        return True

    def _is_chunk_ready(self, cx: int, cy: int, radius: float) -> bool:
        """
        Validates the mesh state of a specific coordinate if it is in range.
        """
        c_size: int = settings.CHUNK_SIZE
        wx: float = (cx * c_size) + (c_size / 2.0)
        wy: float = (cy * c_size) + (c_size / 2.0)

        dist_sq: float = (wx - self.player.x)**2 + (wy - self.player.y)**2
        
        # If outside the zone, we don't care if it's ready
        if dist_sq > radius**2:
            return True

        chunk = self.world.chunks.get((cx, cy))
        return chunk is not None and chunk.is_meshed
