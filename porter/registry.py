"""Manages the mapping between 2D legacy assets and 3D voxel files."""

from pathlib import Path
from typing import Any, Dict, Optional
import pygame
import yaml

from utils.paths import PROJECT_ROOT

_NATIVE_LOAD = pygame.image.load
_NATIVE_SCALE = pygame.transform.scale

_NATIVE_RECT = pygame.draw.rect
_NATIVE_LINE = pygame.draw.line
_NATIVE_CIRCLE = pygame.draw.circle
_NATIVE_POLYGON = pygame.draw.polygon


class VoxelSurfaceImage(pygame.Surface):
    """Subclass of pygame.Surface that carries source path metadata."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initializes the surface and prepares the metadata."""
        super().__init__(*args, **kwargs)
        self._source_path: Optional[str] = None

    def convert(self, *args: Any, **kwargs: Any) -> "VoxelSurfaceImage":
        """Converts the surface while preserving custom pathing."""
        new_raw: pygame.Surface = super().convert(*args, **kwargs)
        new_surf = VoxelSurfaceImage(
            new_raw.get_size(),
            flags=new_raw.get_flags(),
            depth=new_raw.get_bitsize(),
        )
        new_surf.blit(new_raw, (0, 0))
        new_surf._source_path = self._source_path
        return new_surf

    def convert_alpha(
        self, *args: Any, **kwargs: Any
    ) -> "VoxelSurfaceImage":
        """Converts the surface while preserving custom pathing."""
        new_raw: pygame.Surface = super().convert_alpha(*args, **kwargs)
        new_surf = VoxelSurfaceImage(
            new_raw.get_size(),
            flags=new_raw.get_flags(),
            depth=new_raw.get_bitsize(),
        )
        new_surf.blit(new_raw, (0, 0))
        new_surf._source_path = self._source_path
        return new_surf


def get_qualified_key(path: Path) -> str:
    """Returns the asset key relative to the graphics root directory."""
    try:
        parts = path.parts
        for root_dir in ("enemy", "obstacles", "ship", "powerups", "bg"):
            if root_dir in parts:
                idx = parts.index(root_dir)
                return "/".join(parts[idx:])
    except Exception:
        pass
    return path.name


def _intercepted_load(
    file_path: Any, *args: Any, **kwargs: Any
) -> pygame.Surface:
    """Loads an image and returns a path-carrying VoxelSurfaceImage."""
    raw_surf: pygame.Surface = _NATIVE_LOAD(file_path, *args, **kwargs)

    voxel_surf = VoxelSurfaceImage(
        raw_surf.get_size(),
        flags=raw_surf.get_flags(),
        depth=raw_surf.get_bitsize(),
    )
    voxel_surf.blit(raw_surf, (0, 0))

    if isinstance(file_path, (str, Path)):
        voxel_surf._source_path = get_qualified_key(Path(file_path))

    return voxel_surf


def _intercepted_scale(
    surface: pygame.Surface, *args: Any, **kwargs: Any
) -> pygame.Surface:
    """Scales a surface and preserves its custom path subclass."""
    new_raw: pygame.Surface = _NATIVE_SCALE(surface, *args, **kwargs)

    source_path = getattr(surface, "_source_path", None)
    if source_path:
        new_surf = VoxelSurfaceImage(
            new_raw.get_size(),
            flags=new_raw.get_flags(),
            depth=new_raw.get_bitsize(),
        )
        new_surf.blit(new_raw, (0, 0))
        new_surf._source_path = source_path
        return new_surf

    return new_raw


def _intercepted_rect(
    surface: Any, *args: Any, **kwargs: Any
) -> Optional[pygame.Rect]:
    """Draws a rect, extracting the raw C-surface if a proxy is passed."""
    from porter.porter_settings import PORTER_DEFER_RECT_DRAWS

    if hasattr(surface, "_viewport") and PORTER_DEFER_RECT_DRAWS:
        viewport = surface._viewport
        viewport.pending_vector_draws.append(
            (_NATIVE_RECT, surface._surface, args, kwargs)
        )
        return None

    surf = getattr(surface, "_surface", surface)
    return _NATIVE_RECT(surf, *args, **kwargs)


def _intercepted_line(
    surface: Any, *args: Any, **kwargs: Any
) -> Optional[pygame.Rect]:
    """Draws a line, extracting the raw C-surface if a proxy is passed."""
    from porter.porter_settings import PORTER_DEFER_LINE_DRAWS

    if hasattr(surface, "_viewport") and PORTER_DEFER_LINE_DRAWS:
        viewport = surface._viewport
        viewport.pending_vector_draws.append(
            (_NATIVE_LINE, surface._surface, args, kwargs)
        )
        return None

    surf = getattr(surface, "_surface", surface)
    return _NATIVE_LINE(surf, *args, **kwargs)


def _intercepted_circle(
    surface: Any, *args: Any, **kwargs: Any
) -> pygame.Rect:
    """Draws a circle, extracting the raw C-surface if a proxy is passed."""
    surf = getattr(surface, "_surface", surface)
    return _NATIVE_CIRCLE(surf, *args, **kwargs)


def _intercepted_polygon(
    surface: Any, *args: Any, **kwargs: Any
) -> pygame.Rect:
    """Draws a polygon, extracting the raw C-surface if a proxy is passed."""
    surf = getattr(surface, "_surface", surface)
    return _NATIVE_POLYGON(surf, *args, **kwargs)


pygame.image.load = _intercepted_load
pygame.transform.scale = _intercepted_scale

pygame.draw.rect = _intercepted_rect
pygame.draw.line = _intercepted_line
pygame.draw.circle = _intercepted_circle
pygame.draw.polygon = _intercepted_polygon


class PorterRegistry:
    """Loads and coordinates configuration parameters for 2D/3D assets."""

    def __init__(self) -> None:
        """Initializes the registry and loads mappings from config."""
        self.config_path: Path = (
            Path(__file__).resolve().parent / "assets_config.yaml"
        )
        self.mappings: Dict[str, Dict[str, Any]] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Scans directories for assets and overlays custom YAML overrides."""
        self.mappings.clear()

        voxel_assets_dir: Path = (
            PROJECT_ROOT / "porter" / "voxel_assets"
        )

        from porter.porter_settings import PORTER_SCAN_DIRS

        extensions = ("*.png", "*.jpg", "*.jpeg")

        for relative_dir in PORTER_SCAN_DIRS:
            dir_path: Path = PROJECT_ROOT / relative_dir
            if not dir_path.exists():
                continue

            for ext in extensions:
                for file_path in dir_path.rglob(ext):
                    if "voxel_assets" in file_path.parts:
                        continue

                    stem_name: str = file_path.stem
                    file_name: str = file_path.name
                    qualified_key = get_qualified_key(file_path)
                    npz_path: Path = (
                        voxel_assets_dir / f"{stem_name}.npz"
                    )

                    if npz_path.exists():
                        rel_npz = npz_path.relative_to(PROJECT_ROOT)
                        self.mappings[qualified_key] = {
                            "voxel_path": str(rel_npz).replace(
                                "\\", "/"
                            ),
                            "render_3d": True,
                            "scale": 1.0,
                            "thickness": 0.0,
                            "tilt_factor": 0.0,
                        }
                    else:
                        self.mappings[qualified_key] = {
                            "voxel_path": "",
                            "render_3d": False,
                        }

        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as file:
                    data = yaml.safe_load(file) or {}
                    yaml_assets: Dict[str, Dict[str, Any]] = data.get(
                        "assets", {}
                    )

                    for key, config in yaml_assets.items():
                        if key in self.mappings:
                            self.mappings[key].update(config)
                        else:
                            self.mappings[key] = config
            except Exception as error:
                print(f"[PorterRegistry] Error parsing config: {error}")

    def get_mapping(self, sprite_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves 3D translation configs for a given sprite name."""
        # Normalize slashes first for cross-platform robustness
        norm_name = sprite_name.replace("\\", "/")

        # 1. High-Performance Direct Dictionary Match
        if norm_name in self.mappings:
            return self.mappings[norm_name]

        # 2. Collision-Safe Suffix Matching Fallback
        for key, config in self.mappings.items():
            if key.endswith(norm_name) or norm_name.endswith(key):
                return config
            
        return None
