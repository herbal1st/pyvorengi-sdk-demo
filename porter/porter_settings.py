"""Local configuration for the Porter 2D-to-3D asset pipeline."""

from typing import Final

# Directories containing gameplay sprites to scan recursively
PORTER_SCAN_DIRS: Final[list[str]] = [
    "space_flight/graphics/enemy",
    "space_flight/graphics/obstacles",
    "space_flight/graphics/ship",
]  # folders

# Standard micro-layered vertical offset for child attachments
PORTER_Z_ATTACHMENT_OFFSET: Final[float] = 0.002  # blocks

# High-precision top-down camera configurations for 1:1 pixel locking
PORTER_CAMERA_YAW: Final[float] = 0.0  # radians
PORTER_CAMERA_PITCH: Final[float] = -1.5707963267948966  # radians
PORTER_CAMERA_HEIGHT: Final[float] = 25.0  # blocks
PORTER_CAMERA_CENTER_X: Final[float] = 16.0  # blocks
PORTER_CAMERA_CENTER_Y: Final[float] = 16.0  # blocks

# --- High-Performance Layering Settings ---
# Semantic groupings mapping filenames to specific vertical default heights
PORTER_OVERLAYS_TOP: Final[list[str]] = [
    "lights",
    "shield",
]  # keywords

PORTER_OVERLAYS_MID: Final[list[str]] = [
]  # keywords

# Enable/Disable perspective lens parallax shifting for overlays
PORTER_PERSPECTIVE_PARALLAX_ON: Final[bool] = True  # bool

# Toggle selective vector drawing deferral to prevent 3D overlap on UI
PORTER_DEFER_RECT_DRAWS: Final[bool] = True  # bool
PORTER_DEFER_LINE_DRAWS: Final[bool] = True  # bool

# --- Telemetry & Diagnostics ---
# Display a performance tracking FPS monitor directly on the viewport
PORTER_SHOW_FPS: Final[bool] = False  # bool
