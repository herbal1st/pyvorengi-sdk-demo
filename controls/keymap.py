"""
Abstracts hardware key codes into logical game actions.
"""

from typing import Dict, List, Final

import pygame

# --- Movement Actions ---
MOVE_FORWARD: Final[str] = "MOVE_FORWARD"
MOVE_BACKWARD: Final[str] = "MOVE_BACKWARD"
MOVE_LEFT: Final[str] = "MOVE_LEFT"
MOVE_RIGHT: Final[str] = "MOVE_RIGHT"
MOVE_UP: Final[str] = "MOVE_UP"
MOVE_DOWN: Final[str] = "MOVE_DOWN"

# --- State & Utility ---
QUIT_APP: Final[str] = "QUIT_APP"
TOGGLE_FULLSCREEN: Final[str] = "TOGGLE_FULLSCREEN"
TOGGLE_PAUSE: Final[str] = "TOGGLE_PAUSE"
TOGGLE_DEBUG: Final[str] = "TOGGLE_DEBUG"
TOGGLE_FOG_MODE: Final[str] = "TOGGLE_FOG_MODE"

# --- Block Selection ---
SELECT_PREV_BLOCK: Final[str] = "SELECT_PREV_BLOCK"
SELECT_DEFAULT_BLOCK: Final[str] = "SELECT_DEFAULT_BLOCK"
SELECT_NEXT_BLOCK: Final[str] = "SELECT_NEXT_BLOCK"

BINDINGS: Dict[str, List[int]] = {
    MOVE_FORWARD:         [pygame.K_w, pygame.K_UP],
    MOVE_BACKWARD:        [pygame.K_s, pygame.K_DOWN],
    MOVE_LEFT:            [pygame.K_a, pygame.K_LEFT],
    MOVE_RIGHT:           [pygame.K_d, pygame.K_RIGHT],
    MOVE_UP:              [pygame.K_e],
    MOVE_DOWN:            [pygame.K_q],
    QUIT_APP:             [pygame.K_ESCAPE],
    TOGGLE_FULLSCREEN:    [pygame.K_RETURN],
    TOGGLE_PAUSE:         [pygame.K_PAUSE],
    TOGGLE_DEBUG:         [pygame.K_0],
    TOGGLE_FOG_MODE:      [pygame.K_t],
    SELECT_PREV_BLOCK:    [pygame.K_1],
    SELECT_DEFAULT_BLOCK: [pygame.K_2],
    SELECT_NEXT_BLOCK:    [pygame.K_3],
}


def is_key_bound_to(key_id: int, action: str) -> bool:
    """
    Checks if a hardware key ID is assigned to a specific logical action.
    """
    return key_id in BINDINGS.get(action, [])
