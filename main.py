# /// script
# dependencies = [
#     "numpy",
# ]
# ///

"""
Web-compatible entry point for the PyVorengi Engine.
"""

import asyncio
import pygame

# Initialize pygame globally so the compiler detects and configures the HTML canvas
pygame.init()
pygame.display.set_mode((1280, 720))

from engine.engine import VoxelEngine


async def main() -> None:
    """
    Main asynchronous bootstrap function for Pygbag.
    """
    app = VoxelEngine()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
