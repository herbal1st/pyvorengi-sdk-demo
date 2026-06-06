"""
Manages transitions between game states and hardware input focus.
"""

from typing import Final

import pygame

from settings import settings


class State:
    """
    Enumeration of valid application states.
    """
    MENU: Final[int] = 0
    PLAYING: Final[int] = 1
    PAUSED: Final[int] = 2


class StateManager:
    """
    Handles state logic, input grabbing, and debug overlay toggles.
    """

    def __init__(self) -> None:
        """
        Initializes the default state and focus tracking.
        """
        # Starting game state
        self.current_state: int = State.PLAYING
        
        # Track whether the application is in fullscreen mode
        self.is_fullscreen: bool = settings.START_FULLSCREEN
        
        # Internal window focus tracker
        self._is_window_focused: bool = True
        
        # Visibility flag for debug telemetry
        self.show_debug: bool = False

    def toggle_fullscreen(self) -> None:
        """
        Flips the internal fullscreen state tracker.
        """
        self.is_fullscreen = not self.is_fullscreen

    def toggle_debug(self) -> None:
        """
        Flips the visibility flag for the debug overlay.
        """
        self.show_debug = not self.show_debug

    def update_focus(self, is_focused: bool) -> None:
        """
        Updates the window focus status and synchronizes hardware input.
        """
        # Guard: Only process if the focus status actually changed
        if self._is_window_focused == is_focused:
            return

        self._is_window_focused = is_focused
        self._apply_hardware_state()

    def set_state(self, new_state: int) -> None:
        """
        Transitions to a new game state and updates input behavior.
        """
        # Guard: Only process if the state is actually changing
        if self.current_state == new_state:
            return

        self.current_state = new_state
        self._apply_hardware_state()

    def toggle_pause(self) -> None:
        """
        Convenience method to switch between Playing and Paused states.
        """
        if self.is_playing:
            self.set_state(State.PAUSED)
            return
            
        if self.is_paused:
            self.set_state(State.PLAYING)

    def _apply_hardware_state(self) -> None:
        """
        Syncs mouse visibility and input grab with current state and focus.
        """
        # Logic: Input is captured only if playing AND window is focused
        should_capture: bool = self.is_playing and self._is_window_focused

        # Inverse: Mouse is visible only if input is NOT captured
        pygame.mouse.set_visible(not should_capture)
        pygame.event.set_grab(should_capture)

    @property
    def is_playing(self) -> bool:
        """
        Checks if the application is currently in the PLAYING state.
        """
        return self.current_state == State.PLAYING

    @property
    def is_paused(self) -> bool:
        """
        Checks if the application is currently in the PAUSED state.
        """
        return self.current_state == State.PAUSED
