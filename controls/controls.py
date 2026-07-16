"""
Orchestrates input processing by merging discrete events and polling.
"""

from typing import Dict, Sequence, Tuple, TYPE_CHECKING, List

import pygame

from controls import keymap
from settings import settings

if TYPE_CHECKING:
    from engine.engine import VoxelEngine

_action_cooldowns: Dict[str, int] = {}


def process_input(engine: "VoxelEngine") -> None:
    """
    Main entry point for handling all user input per frame.
    """
    _handle_events(engine)

    if not engine.state_manager.is_playing:
        return

    keys: Sequence[bool] = pygame.key.get_pressed()

    _apply_movement_logic(engine, keys)
    _apply_vertical_movement(engine, keys)


def _handle_events(engine: "VoxelEngine") -> None:
    """
    Processes the Pygame event queue for discrete triggers.
    """
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            engine.running = False
        elif event.type == pygame.KEYDOWN:
            _handle_single_keypress(engine, event.key)
        elif event.type == pygame.MOUSEMOTION:
            _handle_mouse(engine, event.rel)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            _handle_mouse_click(engine, event.button)
        elif event.type in (
            pygame.WINDOWFOCUSGAINED, 
            pygame.WINDOWFOCUSLOST
        ):
            is_f: bool = (event.type == pygame.WINDOWFOCUSGAINED)
            engine.state_manager.update_focus(is_f)


def _handle_mouse(engine: "VoxelEngine", rel: Tuple[int, int]) -> None:
    """
    Processes mouse movement for camera rotation.
    """
    if not engine.state_manager.is_playing:
        return
    engine.camera.update_rotation(float(rel[0]), float(rel[1]))


def _handle_mouse_click(engine: "VoxelEngine", button: int) -> None:
    """
    Handles discrete mouse clicks for block placement and destruction.
    """
    if not engine.state_manager.is_playing:
        return

    from physics.raycast import perform_raycast

    look, _, _ = engine.camera.get_orientation_vectors()
    start_pos = (engine.player.x, engine.player.y, engine.player.z)

    result = perform_raycast(engine.world, start_pos, look)
    if result is None:
        return

    hit_voxel, prev_voxel = result

    if button == 1:  # Left click: Destroy
        hx, hy, hz = hit_voxel
        engine.world.set_voxel(hx, hy, hz, 0)
    elif button == 3:  # Right click: Place
        px, py, pz = prev_voxel
        engine.world.set_voxel(px, py, pz, settings.ACTIVE_BLOCK_ID)


def _handle_single_keypress(engine: "VoxelEngine", key_id: int) -> None:
    """
    Handles actions that trigger once per key press.
    """
    if keymap.is_key_bound_to(key_id, keymap.QUIT_APP):
        engine.running = False
        return

    if keymap.is_key_bound_to(key_id, keymap.TOGGLE_PAUSE):
        engine.state_manager.toggle_pause()
        return

    if keymap.is_key_bound_to(key_id, keymap.TOGGLE_FULLSCREEN):
        engine.toggle_fullscreen()
        return

    if keymap.is_key_bound_to(key_id, keymap.TOGGLE_DEBUG):
        engine.state_manager.toggle_debug()

    if keymap.is_key_bound_to(key_id, keymap.TOGGLE_FOG_MODE):
        engine.atmosphere.toggle_fog_mode()

    # --- Interactive Showcase Hooks ---
    if keymap.is_key_bound_to(key_id, keymap.REGEN_WORLD):
        engine.regenerate_world()

    if keymap.is_key_bound_to(key_id, keymap.CYCLE_ALGO):
        engine.cycle_noise_algorithm()

    if keymap.is_key_bound_to(key_id, keymap.CYCLE_HAZE_HEIGHT):
        engine.cycle_haze_height()

    if keymap.is_key_bound_to(key_id, keymap.CYCLE_FOG_DENS):
        engine.cycle_fog_density()

    if keymap.is_key_bound_to(key_id, keymap.CYCLE_SKY):
        engine.cycle_sky_color()


def _apply_movement_logic(
    engine: "VoxelEngine", 
    keys: Sequence[bool]
) -> None:
    """
    Handles continuous horizontal movement with delta-time smoothing.
    """
    f_x, f_y, r_x, r_y = engine.camera.get_movement_vectors()
    dx, dy = 0.0, 0.0

    if _is_active(keys, keymap.MOVE_FORWARD):
        dx += f_x
        dy += f_y
    if _is_active(keys, keymap.MOVE_BACKWARD):
        dx -= f_x
        dy -= f_y
    if _is_active(keys, keymap.MOVE_LEFT):
        dx -= r_x
        dy -= r_y
    if _is_active(keys, keymap.MOVE_RIGHT):
        dx += r_x
        dy += r_y

    if dx == 0.0 and dy == 0.0:
        return

    move_speed: float = (
        settings.MOVE_SPEED * (engine.clock.fixed_dt * 60.0)
    )
    engine.player.move(dx * move_speed, dy * move_speed, engine.world)


def _apply_vertical_movement(
    engine: "VoxelEngine", 
    keys: Sequence[bool]
) -> None:
    """
    Handles vertical movement with internal cooldowns.
    """
    now: int = pygame.time.get_ticks()
    cooldown: int = settings.VERTICAL_MOVE_COOLDOWN

    for action in (keymap.MOVE_UP, keymap.MOVE_DOWN):
        if not _is_active(keys, action):
            _action_cooldowns[action] = 0
            continue

        if (now - _action_cooldowns.get(action, 0)) < cooldown:
            continue

        step: float = 1.0 if action == keymap.MOVE_UP else -1.0
        engine.player.teleport_vertical(step, engine.world)
        _action_cooldowns[action] = now


def _is_active(keys: Sequence[bool], action: str) -> bool:
    """
    Checks if any hardware key bound to a logical action is pressed.
    """
    bound_keys: List[int] = keymap.get_bindings().get(action, [])
    return any(keys[k] for k in bound_keys)
