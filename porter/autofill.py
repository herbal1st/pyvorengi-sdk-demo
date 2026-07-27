"""Scans whitelisted game folders to sync and format the assets YAML config."""

from pathlib import Path
from typing import Any, Dict, Set, Final
import yaml

from porter.porter_settings import PORTER_SCAN_DIRS
from utils.paths import PROJECT_ROOT

_METRIC_MAP: Final[Dict[str, str]] = {
    "render_3d": "bool",
    "scale": "scale",
    "thickness": "layers",
    "tilt_factor": "degrees",
    "tilt_agility": "agility",
    "z_offset": "blocks",
}

_YAML_LEGEND: Final[str] = """
# ============================================================================
# ASSETS CONFIGURATION LEGEND
# ============================================================================
# render_3d    : Toggle 3D voxel interception and drawing (bool).
# scale        : Resizing scale multiplier applied to the 3D model (scale).
# thickness    : Number of vertical 3D layers to composite (layers).
# tilt_factor  : Maximum lateral banking roll limit in degrees (degrees).
# tilt_agility : Responsiveness and bank acceleration rate (multiplier).
# z_offset     : Vertical offset relative to pivot. If null, uses
#                automatic semantic defaults from settings (blocks).
# ============================================================================
"""


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


def scan_and_update_config() -> None:
    """Scans whitelist paths, updates mappings, and cleans obsolete assets."""
    extensions: Set[str] = {".png", ".jpg", ".jpeg"}
    scanned_files: Dict[str, Path] = {}

    for relative_dir in PORTER_SCAN_DIRS:
        target_path: Path = PROJECT_ROOT / relative_dir
        if not target_path.exists():
            continue

        for path in target_path.rglob("*"):
            if "voxel_assets" in path.parts:
                continue
            if path.suffix.lower() in extensions:
                key = get_qualified_key(path)
                scanned_files[key] = path

    config_path: Path = (
        Path(__file__).resolve().parent / "assets_config.yaml"
    )

    config_data: Dict[str, Any] = {"assets": {}}

    # 1. Non-destructive Loading or Clean Initialization
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as file:
                loaded = yaml.safe_load(file)
                if isinstance(loaded, dict) and "assets" in loaded:
                    config_data = loaded
        except Exception as error:
            print(f"[Autofill] Warning: Load failed: {error}")

    assets: Dict[str, Any] = config_data.setdefault("assets", {})

    # 2. Prune obsolete entries for files deleted from disk
    outdated: Set[str] = set(assets.keys()) - set(scanned_files.keys())
    for key in outdated:
        del assets[key]
        print(f"[Autofill] Removed outdated entry: {key}")

    # 3. Append templates ONLY for newly discovered files (preserves existing)
    added_count: int = 0
    for key in scanned_files:
        if key in assets:
            continue  # Existing custom entries are completely preserved

        assets[key] = {
            "render_3d": False,
            "scale": 1.0,
            "thickness": 0.0,
            "tilt_factor": 0.0,
            "tilt_agility": 1.0,
            "z_offset": None,
        }
        added_count += 1
        print(f"[Autofill] Added template for: {key}")

    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        raw_yaml: str = yaml.safe_dump(
            config_data,
            default_flow_style=False,
            sort_keys=True,
        )

        lines = raw_yaml.splitlines()

        max_len: int = 0
        for line in lines:
            is_param: bool = (
                line.startswith("    ")
                and not line.startswith("     ")
                and ":" in line
            )
            if is_param:
                max_len = max(max_len, len(line))

        formatted_lines = []
        first_asset: bool = True

        for line in lines:
            is_header: bool = (
                line.startswith("  ")
                and not line.startswith("   ")
                and line.endswith(":")
            )
            if is_header:
                if not first_asset:
                    formatted_lines.append("")
                else:
                    first_asset = False

            is_param = (
                line.startswith("    ")
                and not line.startswith("     ")
                and ":" in line
            )
            if is_param:
                parts = line.split(":", 1)
                key_name = parts[0].strip()
                if key_name in _METRIC_MAP:
                    metric = _METRIC_MAP[key_name]
                    padding = " " * (max_len - len(line) + 2)
                    line = f"{line}{padding}# {metric}"

            formatted_lines.append(line)

        final_yaml: str = (
            "\n".join(formatted_lines)
            + "\n"
            + _YAML_LEGEND.strip()
            + "\n"
        )

        with open(config_path, "w", encoding="utf-8") as file:
            file.write(final_yaml)

        print(
            f"[Autofill] Sync completed. "
            f"Added: {added_count}, Removed: {len(outdated)}"
        )
    except Exception as error:
        print(f"[Autofill] Error writing config: {error}")


if __name__ == "__main__":
    scan_and_update_config()
