"""
Collision resolution logic implementing axis-aligned sliding movement.
"""

from typing import Final, TYPE_CHECKING

from physics.physics import CollisionEngine
from settings import settings

if TYPE_CHECKING:
    from physics.entity import Entity
    from world.storage.manager import World

# Scalar for safety margin during collision detection
_SAFE: Final[float] = 0.05


class MovementResolver:
    """
    Resolves entity movement axis-by-axis to handle collisions.
    """

    def __init__(self) -> None:
        """
        Initializes the resolver with a collision engine instance.
        """
        self.engine: CollisionEngine = CollisionEngine()

    def apply_movement(
        self, 
        entity: "Entity", 
        dx: float, 
        dy: float, 
        world: "World"
    ) -> None:
        """
        Resolves horizontal movement with sliding collision.
        """
        # Calculate the vertical floor level for the entity
        base_z: float = entity.z - entity.height
        
        # Determine the effective collision radius
        raw_r: float = max(
            settings.COLLISION_RADIUS, 
            settings.CAM_VISUAL_OFFSET + _SAFE
        )
        radius: float = raw_r - 0.001

        # Resolve X axis movement first
        if dx != 0:
            self._resolve_axis(entity, "x", dx, radius, base_z, world)
            
        # Resolve Y axis movement second
        if dy != 0:
            self._resolve_axis(entity, "y", dy, radius, base_z, world)

    def _resolve_axis(
        self, 
        entity: "Entity", 
        axis: str, 
        delta: float, 
        r: float, 
        bz: float, 
        world: "World"
    ) -> None:
        """
        Generalized axis resolver checking leading edge corners.
        """
        # Identify target position and movement direction
        current_pos: float = getattr(entity, axis)
        target: float = current_pos + delta
        sign: float = 1.0 if delta > 0 else -1.0
        
        # Position of the leading collision edge
        lead: float = target + (r * sign)

        # Check the two corners on the leading edge
        if axis == "x":
            is_blocked: bool = (
                self.engine.is_at_solid(world, lead, entity.y - r, bz) or 
                self.engine.is_at_solid(world, lead, entity.y + r, bz)
            )
        else:
            is_blocked = (
                self.engine.is_at_solid(world, entity.x - r, lead, bz) or 
                self.engine.is_at_solid(world, entity.x + r, lead, bz)
            )

        # Guard: Do not update position if path is blocked
        if is_blocked:
            return

        setattr(entity, axis, target)

    def apply_vertical_step(
        self, 
        entity: "Entity", 
        dz: float, 
        world: "World"
    ) -> None:
        """
        Resolves a single vertical displacement step (climbing/flying).
        """
        target_z: float = entity.z + dz
        
        # Check if the target vertical position is clear
        at_solid: bool = self.engine.is_at_solid(
            world, entity.x, entity.y, target_z - entity.height
        )
        
        # Guard: Path is solid
        if at_solid:
            return
            
        entity.z = target_z
