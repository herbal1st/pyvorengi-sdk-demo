```text
 ____                                        ______  ___                __      __      
/\  _`\                                     /\  ___\/\_ \    __        /\ \    /\ \__   
\ \,\L\_\  _____      __      ___     __    \ \ \__/\//\ \  /\_\     __\ \ \___\ \ ,_\  
 \/_\__ \ /\ '__`\  /'__`\   /'___\ /'__`\   \ \ ,__\ \ \ \ \/\ \  /'_ `\ \  _ `\ \ \/  
   /\ \L\ \ \ \L\ \/\ \L\.\_/\ \__//\  __/    \ \ \_/  \_\ \_\ \ \/\ \L\ \ \ \ \ \ \ \_ 
   \ `\____\ \ ,__/\ \__/.\_\ \____\ \____\    \ \_\   /\____\\ \_\ \____ \ \_\ \_\ \__\
    \/_____/\ \ \/  \/__/\/_/\/____/\/____/     \/_/   \/____/ \/_/\/___L\ \/_/\/_/\/__/
             \ \_\                                                   /\____/            
              \/_/                                                   \_/__/
===============================================================================
                       3.5D PORTER INTEGRATION SHOWCASE
===============================================================================

Welcome to the Space Flight 3.5D integration showcase. This sub-directory
contains the modernized, zero-global state edition of Space Flight
configured to use the PyVorengi Porter Bridge rendering pipeline.

* Standalone 2D Repository:
  If you are looking to inspect or play the pure, unmodified 2D arcade 
  edition of this game, please visit the dedicated standalone repository:
  https://github.com/herbal1st/space-flight-pygame

--- 3D VOXEL PORTING DOCUMENTATION ---

The 3.5D viewport translates flat, 2D game loops into a 3D projected arena:
* Integration Touchpoints:
  1. space_flight/main.py: Injects absolute project root and game paths into 
     Python's C-runtime list (sys.path) to ensure clean namespace resolution.
  2. space_flight/src/game.py: Swaps Pygame's raw window screen surface with 
     the VoxelSurface proxy, and binds context parent IDs.
* 3-Pass Viewport Layering:
  Separates rendering into Background (Pass 1), 3D Voxel Core hulls (Pass 2), 
  and Deferred 2D overlays like engine fire and vector gauges (Pass 3).


===============================================================================
                      3.5D PORTER INTEGRATION FOOTPRINT
===============================================================================

To bridge the standard 2D arcade loop of Space Flight into the 3.5D
viewport, the game code implements these minimal-impact integrations:

* Active Context Locks (src/game.py):
  Before drawing sub-component overlays, the loop updates the viewport with
  the current parent's unique ID. This explicitly binds engine fire, weapon 
  flares, and shields directly to their rendering parent.

* Folder-Preserved Asset Keys:
  Configuration and asset lookups are handled through folder-relative 
  pathways. This keeps the configs for player muzzle flashes and enemy 
  muzzle flashes isolated, resolving naming collisions.


===============================================================================
                      HYBRID GROUP ARCHITECTURE (3.5D)
===============================================================================
The game utilizes a balanced, hybrid group rendering setup that isolates 3D
parent hulls from standard flat 2D overlays while preserving performance:

* 3D Parent Hulls (Voxel Groups):
  The primary structural anchors (self.ship, self.enemies, self.obstacles)
  utilize VoxelGroupSingle and VoxelSpriteGroup. These groups explicitly
  feed their physical Sprite object references into the parent viewport
  pipeline. This is required to handle 3D coordinate mapping, passive
  velocity-banking tilt, and dynamic child attachment stitching.

* Independent Overlays (Standard Pygame Groups):
  All independent game elements—including projectile shots (player_shots,
  enemy_shots), background stars, powerup collectibles, and animated
  explosions—remain standard, unmodified Pygame sprite groups. Thanks to the
  SDK's proxy shielding, they are automatically intercepted and processed in
  their own coordinate frames with zero game-code footprint.


===============================================================================
                      DIAGNOSTIC SIDE-BY-SIDE TELEMETRY
===============================================================================
The showcase provides a direct side-by-side performance evaluation setup when 
running the 3.5D ported runner:

  - Lower-Left Overlay (Porter 3D Telemetry):
       Monitors the combined performance of the hybrid 3.5D projection 
       rasterization and 3D culling passes.
       
  - Lower-Right Overlay (Standard 2D Telemetry):
       Tracks the native game loop progression. In the 3D runner, this acts 
       as a control measure; in the standard standalone 2D launcher, this 
       verifies the baseline performance of the direct 2D drawing pipeline 
       without 3D projection overhead.

===============================================================================
                                GAME CONTROLS
===============================================================================

* Movement (Mouse Mode - Default):
  -> Hover / Move:   Track mouse coordinate mapping
  -> Toggle Mode:    Press [M] to activate Mouse Mode
  -> Cursor Capture: The mouse cursor is captured, bound, and clamped strictly
                     inside the ship's flight corridor during combat.
                     Press [ESC] to pause and release the cursor.

* Movement (Keyboard Mode):
  -> Arrow Keys:     [Up] / [Down] / [Left] / [Right]
  -> Toggle Mode:    Press [K] to activate Keyboard Mode

* Combat:
  -> Primary Fire:   [Spacebar] or [Left Click] (Consumes Energy)
  
* Game State:
  -> Pause Game:     Press [ESC] (Locks/Unlocks inputs automatically)
  -> Resume/Exit:    Use the interactive back button or close the window

===============================================================================
Distributed under the MIT License. Copyright (c) 2026 herbal1st.