"""Centralized asset registry for pre-loading and caching graphics."""

from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pygame

import src.settings as settings


class AssetRegistry:
    """Loads and pre-caches standard 2D game assets on startup."""

    def __init__(self) -> None:
        """Initializes cache structures and triggers the load sweep."""
        self.sprites: Dict[str, pygame.Surface] = {}
        self.masks: Dict[str, pygame.Mask] = {}
        self.animations: Dict[str, List[pygame.Surface]] = {}
        self.animation_masks: Dict[str, List[pygame.Mask]] = {}
        
        print("[AssetRegistry] Pre-loading 2D resources...")
        self._load_all()
        print("[AssetRegistry] All 2D resources cached.")

    def _load_frames(
        self,
        path: Path,
        size: Optional[Tuple[int, int]] = None,
        threshold: Optional[int] = None,
    ) -> Tuple[List[pygame.Surface], List[pygame.Mask]]:
        """Helper to load, scale, and convert animations from a folder."""
        frames: List[pygame.Surface] = []
        masks: List[pygame.Mask] = []
        if not path.exists():
            return frames, masks
        for p in sorted(path.glob("*.png")):
            img = pygame.image.load(str(p))
            if size is not None:
                img = pygame.transform.scale(img, size)
            img = img.convert_alpha()
            frames.append(img)
            
            # If a custom threshold is set, compile with it; otherwise,
            # fall back to Pygame's standard core-only mask generation.
            if threshold is not None:
                masks.append(pygame.mask.from_surface(img, threshold))
            else:
                masks.append(pygame.mask.from_surface(img))
        return frames, masks

    def _load_all(self) -> None:
        """Executes standard pre-loading and alpha conversion passes."""
        # --- Pre-load Background Star Scaling (6 scales) ---
        for num in range(1, 5):
            for size in (13, 26, 39, 52, 89, 117):
                path = settings.GRAPHICS_DIR / "bg" / f"star {num}"
                frames, _ = self._load_frames(path, (size, size))
                self.animations[f"star_{num}_{size}"] = frames

        # --- Pre-load Obstacle Asteroids (78 x 78) ---
        rock_path = settings.GRAPHICS_DIR / "obstacles" / "rock"
        frames, masks = self._load_frames(rock_path, (78, 78))
        self.animations["rock"] = frames
        self.animation_masks["rock"] = masks

        # --- Pre-load Explosions (50 x 50) ---
        exp_path = settings.GRAPHICS_DIR / "explosion"
        frames, masks = self._load_frames(exp_path, (50, 50))
        self.animations["explosion"] = frames
        self.animation_masks["explosion"] = masks

        # --- Pre-load Powerup Items (Default Sizes) ---
        for p_type in (
            "powerup shield", "powerup health", "powerup energy"
        ):
            p_path = settings.GRAPHICS_DIR / "powerups" / p_type
            frames, masks = self._load_frames(p_path)
            self.animations[p_type] = frames
            self.animation_masks[p_type] = masks

        # --- Pre-load Player Ship (66 x 66 Base) ---
        ship_path = settings.GRAPHICS_DIR / "ship" / "ship 33x33.png"
        if ship_path.exists():
            img = pygame.image.load(str(ship_path))
            scaled = pygame.transform.scale(img, (66, 66)).convert_alpha()
            self.sprites["ship"] = scaled
            self.masks["ship"] = pygame.mask.from_surface(scaled)

        # Player Ship Extra Decals and Weapons animations
        path = settings.GRAPHICS_DIR / "ship" / "lights"
        frames, masks = self._load_frames(path, (42, 14))
        self.animations["ship_lights"] = frames
        self.animation_masks["ship_lights"] = masks

        path = settings.GRAPHICS_DIR / "ship" / "exhaust"
        frames, masks = self._load_frames(path, (66, 66))
        self.animations["ship_exhaust"] = frames
        self.animation_masks["ship_exhaust"] = masks

        path = settings.GRAPHICS_DIR / "ship" / "laser gun"
        frames, masks = self._load_frames(path, (66, 66))
        self.animations["ship_laser_gun"] = frames
        self.animation_masks["ship_laser_gun"] = masks

        path = settings.GRAPHICS_DIR / "ship" / "laser beam"
        frames, masks = self._load_frames(path, (25, 38))
        self.animations["ship_laser_beam"] = frames
        self.animation_masks["ship_laser_beam"] = masks

        # The shield assets load here with a highly sensitive threshold of 1
        path = settings.GRAPHICS_DIR / "ship" / "shield"
        frames, masks = self._load_frames(path, (98, 98), threshold=1)
        self.animations["ship_shield"] = frames
        self.animation_masks["ship_shield"] = masks

        # --- Pre-load Enemy UFO (66 x 66 Base) ---
        ufo_path = settings.GRAPHICS_DIR / "enemy" / "ufo 33x33.png"
        if ufo_path.exists():
            img = pygame.image.load(str(ufo_path))
            scaled = pygame.transform.scale(img, (66, 66)).convert_alpha()
            self.sprites["enemy_ufo"] = scaled
            self.masks["enemy_ufo"] = pygame.mask.from_surface(scaled)

        # Enemy UFO Extra Decals and Weapons animations
        path = settings.GRAPHICS_DIR / "enemy" / "lights"
        frames, masks = self._load_frames(path, (66, 66))
        self.animations["enemy_lights"] = frames
        self.animation_masks["enemy_lights"] = masks

        path = settings.GRAPHICS_DIR / "enemy" / "laser gun"
        frames, masks = self._load_frames(path, (66, 22))
        self.animations["enemy_laser_gun"] = frames
        self.animation_masks["enemy_laser_gun"] = masks

        path = settings.GRAPHICS_DIR / "enemy" / "laser beam"
        frames, masks = self._load_frames(path, (21, 33))
        self.animations["enemy_laser_beam"] = frames
        self.animation_masks["enemy_laser_beam"] = masks
