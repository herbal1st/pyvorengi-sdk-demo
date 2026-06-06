"""
Application entry point for the Voxel Engine.
"""

from engine.engine import VoxelEngine


def main() -> None:
    """
    Bootstraps and starts the main application loop.
    """
    # Create the central engine instance
    app: VoxelEngine = VoxelEngine()
    
    # Start the application lifecycle
    app.run()


if __name__ == "__main__":
    main()