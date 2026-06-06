"""
Manages game timing, fixed-timestep accumulation, and frame interpolation.
"""

from typing import Tuple
import pygame

from settings import settings


class EngineClock:
    """
    Handles delta time accumulation for physics-consistent updates.
    """

    def __init__(self) -> None:
        """
        Initializes the Pygame clock and timing accumulators.
        """
        self._clock: pygame.time.Clock = pygame.time.Clock()
        
        # Target duration of a single physics step in seconds
        self.fixed_dt: float = 1.0 / settings.FPS
        
        # Accumulated time waiting to be processed by physics
        self.accumulator: float = 0.0
        
        # Actual time elapsed in the last frame
        self.frame_time: float = 0.0

    def tick(self) -> None:
        """
        Updates the internal timers based on the elapsed hardware time.
        """
        # Delta time in seconds
        raw_ms: int = self._clock.tick(settings.FPS)
        self.frame_time = raw_ms / 1000.0
        
        # Cap delta to 100ms to prevent "Spiral of Death" on lag spikes
        self.accumulator += min(self.frame_time, 0.1)

    def consume_step(self) -> bool:
        """
        Checks if enough time has accumulated for a physics update.
        """
        if self.accumulator >= self.fixed_dt:
            self.accumulator -= self.fixed_dt
            return True
        return False

    def get_fps(self) -> float:
        """
        Returns the current hardware frames per second.
        """
        return self._clock.get_fps()

    def get_time_ms(self) -> int:
        """
        Returns the milliseconds elapsed since the last tick.
        """
        return self._clock.get_time()

    @property
    def alpha(self) -> float:
        """
        Calculates the interpolation ratio for visual smoothing.
        """
        return self.accumulator / self.fixed_dt
