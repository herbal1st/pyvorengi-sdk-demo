"""
Central configuration for engine constants and tunable parameters.
"""

from typing import Dict, Final, Tuple


# ------ Persistence ------
MAP_VERSION: Final[str] = "1.0"  # version
HEADER_PREFIX: Final[str] = "v_"  # string
FORCE_FRESH_WORLD: Final[bool] = True  # bool

# ------ Hardware & Display ------
SCREEN_RES: Final[Tuple[int, int]] = (1280, 800)  # pixels
START_FULLSCREEN: Final[bool] = False  # bool
FPS: Final[int] = 30  # hertz
FOV: Final[int] = 600  # ratio
WINDOW_ICON_NAME: Final[str] = "icon.png"  # filename

# ------ Raycasting & Interaction ------
RAYCAST_DIST: Final[float] = 8.0  # blocks
DEFAULT_BLOCK_ID: Final[int] = 3  # id

# ------ User Interface ------
UI_BG_ALPHA: Final[int] = 180  # opacity
UI_REFRESH_RATE_MS: Final[int] = 100  # ms

# ------ Rendering & Visibility ------
INITIAL_RENDER_DIST: Final[float] = 95.0  # blocks
NEAR_PLANE: Final[float] = 0.05  # blocks
CAM_VISUAL_OFFSET: Final[float] = 0.075  # blocks
MESH_EPSILON: Final[float] = 1e-6  # scale
FRUSTUM_MARGIN: Final[float] = 0.95  # ratio
ALTITUDE_THROTTLE_HEIGHT_RATIO: Final[float] = 0.5  # ratio
ALTITUDE_THROTTLE_FACTOR: Final[float] = 0.85  # scale

# ------ Physics & Movement ------
MOVE_SPEED: Final[float] = 0.075  # blocks
VERTICAL_MOVE_COOLDOWN: Final[int] = 50  # ms
MOUSE_SENSITIVITY: Final[float] = 0.003  # scale
PITCH_LIMIT: Final[float] = 1.5  # radians
PLAYER_HEIGHT: Final[float] = 1.75  # blocks
COLLISION_RADIUS: Final[float] = 0.3  # blocks

# ------ World Geometry ------
MAP_DEPTH: Final[int] = 24  # blocks
CHUNK_SIZE: Final[int] = 16  # blocks
SECTION_DIVS_XY: int = 1  # count
SECTION_DIVS_Z: int = 2  # count

# ------ Loading & Sweep Boundaries ------
LOAD_MARGIN: Final[float] = CHUNK_SIZE * 1.0  # blocks
UNLOAD_MARGIN: Final[float] = CHUNK_SIZE * 2.0  # blocks
SAFETY_RADIUS: Final[float] = CHUNK_SIZE * 3.0  # blocks
MOVEMENT_UPDATE_THRESHOLD: Final[float] = 2.0  # blocks
ROTATION_UPDATE_THRESHOLD: Final[float] = 3.0  # degrees
BOOTSTRAP_TIMEOUT: Final[float] = 5.0  # seconds
ANGULAR_BUFFER_DEG: Final[float] = 5.0  # degrees
ANGULAR_BUFFER_RAD: float = 0.087  # radians

# ------ Terrain Generation ------
USE_PROCEDURAL: bool = True  # bool
GLOBAL_MAP_NAME: Final[str] = "default_map.npz"  # string
WORLD_SEED: int = 420  # seed
NOISE_TYPE_PERLIN: Final[str] = "PERLIN"  # type
NOISE_TYPE_SIMPLEX: Final[str] = "SIMPLEX"  # type
ACTIVE_NOISE_TYPE: str = NOISE_TYPE_PERLIN  # type
NOISE_SCALE: float = 50.0  # scale
MAX_TERRAIN_HEIGHT_RATIO: Final[float] = 0.95  # ratio

# ------ Sky Islands (Procedural Post-Processing) ------
SKY_ISLANDS_ON: bool = False  # bool
SKY_ISLAND_MIRROR_HEIGHT: int = 11  # blocks
SKY_ISLAND_BOTTOM_FILL_ID: int = 3  # id
SPAWN_SAFETY_PAD_SIZE: int = 3  # blocks

# ------ Lighting & Shading ------
SKY_COLOR: Final[Tuple[int, int, int]] = (20, 195, 230)  # rgb
USE_HEIGHT_SHADING: bool = True  # bool
HEIGHT_SHADING_FACTOR: Final[float] = 0.9  # scale
HEIGHT_SHADING_EXPONENT: Final[float] = 1.125  # exponent
LIGHT_MAP: Final[Dict[Tuple[int, int, int], float]] = {
    (0, 0, 1): 1.0,
    (0, 0, -1): 0.4,
    (0, 1, 0): 0.9,
    (0, -1, 0): 0.8,
    (1, 0, 0): 0.7,
    (-1, 0, 0): 0.6,
}  # shading

# ------ Atmospheric FX (Fog & Haze) ------
FOG_MODE_LINEAR: Final[str] = "LINEAR"  # mode
FOG_MODE_EXP: Final[str] = "EXP"  # mode
FOG_MODE: str = FOG_MODE_EXP  # mode
FOG_EXPONENT: float = 50.0  # exponent
INITIAL_FOG_DENSITY: Final[float] = 0.7  # density
HEIGHT_FOG_RGB: Final[Tuple[int, int, int]] = (215, 190, 40)  # rgb
INITIAL_HEIGHT_FOG_MAX_Z: Final[float] = 9.0  # blocks
INITIAL_HEIGHT_FOG_DENSITY: Final[float] = 0.9  # density
INITIAL_HEIGHT_FOG_FADE: Final[float] = 14.0  # blocks
HAZE_WASHOUT_RGB: Final[Tuple[int, int, int]] = (200, 200, 200)  # rgb
HAZE_WASHOUT_STRENGTH: Final[float] = 0.75  # ratio
