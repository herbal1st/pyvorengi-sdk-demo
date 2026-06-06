"""
Manages the environmental and atmospheric state of the world session.
"""

from typing import Any, Dict

from settings import settings


class AtmosphereManager:
    """
    Stores visual parameters like fog, haze, and lighting.
    """

    def __init__(self) -> None:
        """
        Initializes atmosphere settings from global defaults.
        """
        self.fog_density: float = settings.INITIAL_FOG_DENSITY
        self.render_dist: float = settings.INITIAL_RENDER_DIST
        self.use_height_shading: bool = settings.USE_HEIGHT_SHADING
        self.height_shading_factor: float = settings.HEIGHT_SHADING_FACTOR
        self.h_fog_dens: float = settings.INITIAL_HEIGHT_FOG_DENSITY
        self.h_fog_max_z: float = settings.INITIAL_HEIGHT_FOG_MAX_Z
        self.h_fog_fade: float = settings.INITIAL_HEIGHT_FOG_FADE
        self.needs_remesh: bool = False

    def toggle_fog_mode(self) -> None:
        """
        Cycles between atmospheric models in settings.
        """
        if settings.FOG_MODE == settings.FOG_MODE_LINEAR:
            settings.FOG_MODE = settings.FOG_MODE_EXP
        else:
            settings.FOG_MODE = settings.FOG_MODE_LINEAR
        self.needs_remesh = True

    def sync_from_manifest(self, metadata: Dict[str, Any]) -> None:
        """
        Updates settings based on saved world session data.
        """
        self.use_height_shading = metadata.get(
            "use_height_shading", 
            self.use_height_shading
        )
        self.height_shading_factor = metadata.get(
            "height_shading_factor", 
            self.height_shading_factor
        )
        self.needs_remesh = True
