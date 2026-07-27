"""Defines custom sprite groups that override drawing routines for 3D."""

from typing import Any, List
import pygame


class VoxelSpriteGroup(pygame.sprite.Group):
    """Sprite group that intercepts 2D drawing and routes to 3D."""

    def __init__(self, *sprites: Any, viewport: Any = None) -> None:
        """Initializes the group with a reference to the 3D viewport."""
        super().__init__(*sprites)
        self.viewport: Any = viewport

    def draw(self, surface: pygame.Surface) -> List[pygame.Rect]:
        """Overridden drawing routing redirecting 3D-mapped images."""
        sprites = self.sprites()
        if not self.viewport:
            return super().draw(surface)

        dirty_rects: List[pygame.Rect] = []
        for spr in sprites:
            # Retrieve mapped filename directly from custom surface subclass
            source_path = getattr(spr.image, "_source_path", None)

            # Route to 3D viewport with raw surface & bounding rect data
            if source_path and self.viewport.draw_actor(
                spr, source_path, spr.rect.center,
                source_surf=spr.image, dest_rect=spr.rect
            ):
                pass
            else:
                # Fallback to standard 2D blit
                rect = surface.blit(spr.image, spr.rect)
                dirty_rects.append(rect)

        return dirty_rects


class VoxelGroupSingle(pygame.sprite.GroupSingle):
    """Single-sprite container that routes 2D draws to 3D."""

    def __init__(self, sprite: Any = None, viewport: Any = None) -> None:
        """Initializes the container with viewport tracking."""
        super().__init__(sprite)
        self.viewport: Any = viewport

    def draw(self, surface: pygame.Surface) -> List[pygame.Rect]:
        """Diverts the single sprite's base image draw call to 3D."""
        if not self.sprite:
            return []

        if not self.viewport:
            return super().draw(surface)

        spr = self.sprite
        source_path = getattr(spr.image, "_source_path", None)

        # Route to 3D viewport with raw surface & bounding rect data
        if source_path and self.viewport.draw_actor(
            spr, source_path, spr.rect.center,
            source_surf=spr.image, dest_rect=spr.rect
        ):
            return []

        rect = surface.blit(spr.image, spr.rect)
        return [rect]
