"""Application entry point initializing the game context and loop."""

import sys
from pathlib import Path

# =========================================================================
# PORTER INTEGRATION: PATH INJECTION FOR MODULE RESOLUTION
# =========================================================================
# To avoid manually renaming every relative import across game-specific
# modules (e.g., 'import src.settings' to 'import space_flight.src...'),
# we dynamically inject both the absolute SDK project root and the local
# space_flight folder directly into Python's sys.path at launch time.
#
# This allows the clean 2D game codebase to run completely unmodified,
# while still resolving core SDK utilities natively.
#
# Modified Files for Porting Integration:
# 1. space_flight/main.py - Sets up paths, instantiates Game.
# 2. space_flight/src/game.py - Hooks up Viewport and VoxelSurface.
# =========================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GAME_ROOT = PROJECT_ROOT / "space_flight"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(GAME_ROOT) not in sys.path:
    sys.path.insert(0, str(GAME_ROOT))


from src.game import Game


def main() -> None:
    """Instantiate and run the master game application."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
