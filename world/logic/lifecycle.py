"""
Orchestrates the synchronous loading, meshing, and purging of chunks.
"""

from typing import TYPE_CHECKING, List, Optional, Tuple

import numpy as np
from numpy.typing import NDArray

from settings import settings
import world.workers as workers
from world.provider import WorldProvider
from world.spatial import MeshContext
from world.storage.chunk import Chunk
from world.strategy import LifecycleStrategist

if TYPE_CHECKING:
    from camera.camera import Camera
    from renderer.renderer import Renderer
    from physics.entity import Entity
    from world.session import WorldSession
    from world.storage.manager import World


class ChunkLifecycleManager:
    """
    Manages sequential chunk updates without background worker threads.
    """

    def __init__(self, world: "World", session: "WorldSession") -> None:
        """
        Initializes the manager with synchronous state tracking.
        """
        self.world: "World" = world
        self.session: "WorldSession" = session
        self.brain: LifecycleStrategist = LifecycleStrategist()

        self.load_queue: List[Tuple[int, int]] = []
        self.mesh_queue: List[Tuple[int, int]] = []
        self.remesh_pool: List[Tuple[int, int]] = []

    def manage_updates(
        self,
        player: "Entity",
        camera: "Camera",
        renderer: "Renderer"
    ) -> None:
        """
        Checks thresholds to drive synchronous world reconciliation.
        """
        pos_2d: Tuple[float, float] = (player.x, player.y)
        needs_work: bool = self.brain.needs_update(pos_2d, camera.yaw)

        has_pending_tasks: bool = (
            bool(self.load_queue)
            or bool(self.mesh_queue)
            or bool(self.remesh_pool)
        )

        if not (needs_work or self.world.remesh_requested or has_pending_tasks):
            camera.yaw_velocity = 0.0
            return

        self.brain.update_tracking(pos_2d, camera.yaw)
        self._reconcile_world(player, renderer)

    def _reconcile_world(
        self,
        player: "Entity",
        rend: "Renderer"
    ) -> None:
        """
        Updates loading search bounds and executes a slice of pending work.
        """
        ctx: MeshContext = self._capture_context(rend, player)
        r_dist: float = rend.atmo.render_dist

        if self.world.remesh_requested:
            self._trigger_radiating_remesh(player.x, player.y)
            self.world.remesh_requested = False

        self._trickle_remesh_pool(player.x, player.y)

        radius: float = r_dist + settings.LOAD_MARGIN
        candidates: List[Tuple[int, int]] = self.brain.get_loading_candidates(
            player.x, player.y, radius
        )
        self._enqueue_candidates(candidates)
        self._purge_distant(player.x, player.y, r_dist + 50.0)
        self._process_queued_tasks(player.x, player.y, ctx)

    def _enqueue_candidates(self, coords: List[Tuple[int, int]]) -> None:
        """
        Appends candidates to the queue if they are not loaded or queued.
        """
        for c in coords:
            if c in self.world.chunks:
                continue
            if c not in self.load_queue:
                self.load_queue.append(c)

    def _process_queued_tasks(
        self,
        px: float,
        py: float,
        ctx: MeshContext
    ) -> None:
        """
        Executes a limited batch of loading and meshing tasks inline.
        """
        self._sort_queue(self.load_queue, px, py)
        self._identify_meshing_needs(ctx, px, py)
        self._sort_queue(self.mesh_queue, px, py)

        if self.load_queue:
            coords: Tuple[int, int] = self.load_queue.pop(0)
            _, data = workers.worker_load_chunk(
                self.session.world_id, coords[0], coords[1]
            )
            self.world.chunks[coords] = Chunk(coords[0], coords[1], data)

        elif self.mesh_queue:
            coords = self.mesh_queue.pop(0)
            chunk: Optional[Chunk] = self.world.chunks.get(coords)
            if chunk:
                _, sections = workers.worker_mesh_chunk(
                    coords[0], coords[1], chunk.data, ctx
                )
                chunk.sections = sections
                chunk.is_meshed = True
                chunk.needs_remesh = False

    def _identify_meshing_needs(
        self,
        ctx: MeshContext,
        px: float,
        py: float
    ) -> None:
        """
        Queues unmeshed chunks that are within active visibility range.
        """
        l_sq: float = (ctx["render_dist"] + settings.LOAD_MARGIN) ** 2
        half: float = settings.CHUNK_SIZE / 2.0

        for coords, chunk in self.world.chunks.items():
            if chunk.is_meshed or coords in self.mesh_queue:
                continue

            dx: float = (chunk.world_x + half) - px
            dy: float = (chunk.world_y + half) - py

            if (dx ** 2 + dy ** 2) < l_sq:
                self.mesh_queue.append(coords)

        self._sort_queue(self.mesh_queue, px, py)

    def _trigger_radiating_remesh(self, px: float, py: float) -> None:
        """
        Marks all chunks to be remeshed sequentially.
        """
        self.remesh_pool.clear()
        self.mesh_queue.clear()

        for coords, chunk in self.world.chunks.items():
            if chunk.is_meshed:
                chunk.needs_remesh = True
                self.remesh_pool.append(coords)

        self._sort_queue(self.remesh_pool, px, py)

    def _trickle_remesh_pool(self, px: float, py: float) -> None:
        """
        Gradually transfers remesh tasks to the active queue.
        """
        if not self.remesh_pool:
            return

        while self.remesh_pool and len(self.mesh_queue) < 4:
            coords: Tuple[int, int] = self.remesh_pool.pop(0)
            if coords not in self.mesh_queue:
                self.mesh_queue.append(coords)

    def _purge_distant(self, px: float, py: float, dist: float) -> None:
        """
        Unloads chunks that have drifted outside the retention radius.
        """
        limit_sq: float = dist ** 2
        purged: int = 0
        half: float = settings.CHUNK_SIZE / 2.0

        for coords in list(self.world.chunks.keys()):
            if purged >= 2:
                break

            chunk: Optional[Chunk] = self.world.chunks.get(coords)
            if not chunk:
                continue

            dx: float = (chunk.world_x + half) - px
            dy: float = (chunk.world_y + half) - py

            if (dx ** 2 + dy ** 2) > limit_sq:
                self.world.chunks.pop(coords, None)
                purged += 1

    def _sort_queue(
        self,
        queue: List[Tuple[int, int]],
        px: float,
        py: float
    ) -> None:
        """
        Sorts target queue in-place by distance from reference coordinate.
        """
        mid: float = settings.CHUNK_SIZE / 2.0

        def _dist_sq(c: Tuple[int, int]) -> float:
            dx: float = (c[0] * settings.CHUNK_SIZE + mid) - px
            dy: float = (c[1] * settings.CHUNK_SIZE + mid) - py
            return dx ** 2 + dy ** 2

        queue.sort(key=_dist_sq)

    def load_initial_chunks(self) -> None:
        """
        Synchronously sets up the starting grid around spawn.
        """
        provider: WorldProvider = WorldProvider(self.session.world_id)

        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if (dx, dy) not in self.world.chunks:
                    data: NDArray[np.uint8] = provider.get_chunk_data(dx, dy)
                    self.world.chunks[(dx, dy)] = Chunk(dx, dy, data)

    def update_circular(self, player: "Entity", renderer: "Renderer") -> None:
        """
        Triggers circular loading sweeps during bootstrapper phase.
        """
        self._reconcile_world(player, renderer)

    def stop(self) -> None:
        """
        No-op placeholder for single-threaded lifecycle stability.
        """
        pass

    @property
    def is_busy(self) -> bool:
        """
        Determines if there are outstanding tasks in local queues.
        """
        return (
            bool(self.load_queue)
            or bool(self.mesh_queue)
            or bool(self.remesh_pool)
        )

    def _capture_context(
        self,
        rend: "Renderer",
        player: "Entity"
    ) -> MeshContext:
        """
        Prepares a dictionary of visual state for worker tasks.
        """
        return {
            "cam_pos": (player.x, player.y, player.z),
            "render_dist": rend.atmo.render_dist,
            "fog_density": rend.atmo.fog_density,
            "h_fog_dens": rend.atmo.h_fog_dens,
            "h_fog_max_z": rend.atmo.h_fog_max_z,
            "h_fog_fade": rend.atmo.h_fog_fade
        }
