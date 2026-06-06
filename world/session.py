"""
Manages active world state, versioning, and manifest validation.
"""

from dataclasses import dataclass
from typing import Any, Dict

from map import loader
from settings import settings


@dataclass
class WorldSession:
    """
    Maintains session metadata and disk compatibility fingerprints.
    """
    world_id: str
    metadata: Dict[str, Any]

    @classmethod
    def create(cls, world_id: str) -> "WorldSession":
        """
        Initializes a session and verifies setting compatibility.
        """
        meta: Dict[str, Any] = loader.load_manifest(world_id)
        
        # Unique fingerprint based on current engine settings
        curr_fingerprint: str = loader.generate_unique_world_id()
        saved_fingerprint: str = meta.get("fingerprint", "")

        # Validation Logic
        _validate_fingerprint(world_id, meta, curr_fingerprint, saved_fingerprint)
        _ensure_shading_meta(world_id, meta)

        return cls(world_id, meta)


def _validate_fingerprint(
    world_id: str, 
    meta: Dict[str, Any], 
    current: str, 
    saved: str
) -> None:
    """
    Updates the world fingerprint if an engine setting mismatch is detected.
    """
    if saved and saved != current:
        print(f"[Session] Warning: Engine mismatch. ID updated to {current}.")

    if saved != current:
        meta["fingerprint"] = current
        loader.save_manifest(world_id, meta)


def _ensure_shading_meta(world_id: str, meta: Dict[str, Any]) -> None:
    """
    Ensures global shading constants are present in the manifest.
    """
    if "use_height_shading" not in meta:
        meta["use_height_shading"] = settings.USE_HEIGHT_SHADING
        
    if "height_shading_factor" not in meta:
        meta["height_shading_factor"] = settings.HEIGHT_SHADING_FACTOR
        
    loader.save_manifest(world_id, meta)