"""
Defines physical objects with world positions and hitboxes.
"""

from typing import TYPE_CHECKING, Tuple

from physics.resolution import MovementResolver
from settings import settings

if TYPE_CHECKING:
    from world.storage.manager import World


class Entity:
    """
    Base class for physical objects with collision resolution.
    """

    def __init__(
        self, 
        x: float, 
        y: float, 
        z: float, 
        height: float = settings.PLAYER_HEIGHT
    ) -> None:
        """
        Initializes entity position and its movement resolver.
        """
        # Current physics coordinates
        self.x: float = x
        self.y: float = y
        self.z: float = z
        
        # Previous frame coordinates for interpolation
        self.prev_x: float = x
        self.prev_y: float = y
        self.prev_z: float = z
        
        # Vertical size for collision checks
        self.height: float = height
        
        # Logic component for handling movement collisions
        self._resolver: MovementResolver = MovementResolver()

    def store_previous_state(self) -> None:
        """
        Saves current coordinates as the previous state before physics steps.
        """
        self.prev_x = self.x
        self.prev_y = self.y
        self.prev_z = self.z

    def get_interpolated_position(
        self, 
        alpha: float
    ) -> Tuple[float, float, float]:
        """
        Calculates a blended position between states for smooth rendering.
        """
        ix: float = self.prev_x + (self.x - self.prev_x) * alpha
        iy: float = self.prev_y + (self.y - self.prev_y) * alpha
        iz: float = self.prev_z + (self.z - self.prev_z) * alpha
        
        return ix, iy, iz

    def move(self, dx: float, dy: float, world: "World") -> None:
        """
        Horizontal movement with collision resolution.
        """
        self._resolver.apply_movement(self, dx, dy, world)

    def teleport_vertical(self, amount: float, world: "World") -> None:
        """
        Immediate vertical displacement (climbing or flying).
        """
        self._resolver.apply_vertical_step(self, amount, world)

    @property
    def position(self) -> Tuple[float, float, float]:
        """
        Returns the current world coordinates as a tuple.
        """
        return (self.x, self.y, self.z)
