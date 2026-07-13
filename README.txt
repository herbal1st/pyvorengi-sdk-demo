```text
____           __  __                                             
/\  _`\        /\ \/\ \                                      __    
\ \ \L\ \__  __\ \ \ \ \    ___   _ __    __    ___      __ /\_\   
 \ \ ,__/\ \/\ \\ \ \ \ \  / __`\/\`'__\/'__`\/' _ `\  /'_ `\/\ \  
  \ \ \/\ \ \_\ \\ \ \_/ \/\ \L\ \ \ \//\  __//\ \/\ \/\ \L\ \ \ \ 
   \ \_\ \/`____ \\ `\___/\ \____/\ \_\\ \____\ \_\ \_\ \____ \ \_\
    \/_/  `/___/> \`\/__/  \/___/  \/_/ \/____/\/_/\/_/\/___L\ \/_/
             /\___/                                      /\____/   
             \/__/                                       \_/__/    
===============================================================================
               PYVORENGI ENGINE - TECHNICAL SPECIFICATION
===============================================================================

[HOW TO RUN]
-------------------------------------------------------------------------------
Prerequisites:
Ensure Python 3.x is installed. Install required dependencies via pip:
pip install pygame numpy pyyaml

Launching the Engine:
Execute the entry script from the project root:
python run.py

Controls:
  - Movement   : W/A/S/D or Arrow keys.
  - Elevation  : E to fly upward, Q to fly downward.
  - Interaction: LEFT CLICK to destroy blocks, RIGHT CLICK to place blocks.
  - Toggle HUD : Key 0 toggles the diagnostic debug overlay.
  - Aiming     : A static targeting cross (+) is rendered at the center of 
                 the screen during play to assist with aiming.

Note: 1. Run map_maker.py to generate a block inspection walkway.
      2. Run pic_to_voxel.py to batch-convert images from /pic_imports
         into compressed voxel maps (.npz) within map/maps/.
      3. In settings.py, set USE_PROCEDURAL = False and GLOBAL_MAP_NAME 
         to your desired filename (e.g., "ship.npz") to load a static map.
      4. To enable procedural Floating Sky Islands, set USE_PROCEDURAL = True
         and SKY_ISLANDS_ON = True in settings.py.
      (A pre-authored "default_map.npz" and demo pixel art images
       inside /pic_imports are pre-installed for immediate testing)

Hint: The aesthetic sweet spot for voxel art is 16x16 to 128x128 pixels. 
      Higher resolutions (256+) often lose the "chunky" voxel charm and 
      will eventually degrade CPU-side rendering performance.


[1.0 SYSTEM OVERVIEW]
-------------------------------------------------------------------------------
Core Philosophy: Vectorized, Cache-Conscious, and Single-Threaded.
Architecture   : Chessboard-modular voxel engine utilizing static halo-padding.
Source Hardware: Ryzen 7 5825U (16GB RAM).
Performance    : Target 30 FPS @ 60m-80m view. Throughput: ~60k-100k faces/sec.
                 Note: Single-threaded architecture may experience frame-time
                 spikes during synchronous chunk generation and meshing.


[2.0 MEMORY CONVENTION & DATA LAYOUT]
-------------------------------------------------------------------------------
Standard       : Single Unified Layout - (Z, Y, X) [Storage & Simulation]
Rationale      : Both procedural generation and pre-authored static maps store 
                 voxels as (Z, Y, X) to align with NumPy C-order contiguity and 
                 optimize flat serialization.
The Transpose  : To avoid costly real-time 3D array transpositions on load, 
                 the (X, Y, Z) to (Z, Y, X) mapping and horizontal flip is 
                 done entirely offline inside the map maker and forge scripts 
                 at save-time.
The Halo Trick : Chunks are generated with a +1 block border ([+2]x[+2]x[+2])
                 to ensure geometry continuity across boundaries.


[2.1 PROCEDURAL PIPELINE]
-------------------------------------------------------------------------------
Bypass Logic   : Pure procedural chunks are regenerated from seed rather than
                 saved to disk to minimize I/O overhead in the demo.
Caching        : VoxelRegistry definitions are loaded once at initialization
                 to prevent redundant disk access during chunk generation.


[2.2 FRAME 1 KICKSTART]
-------------------------------------------------------------------------------
Kickstart      : The Lifecycle Manager ignores movement thresholds on Frame 1.
Rationale      : Forces immediate world reconciliation so the view frustum is 
                 populated instantly before the player gains control.


[2.3 REAL-TIME BLOCK INTERACTION & RAYMARCHING]
-------------------------------------------------------------------------------
Targeting      : To interact with the world, the engine projects an invisible 
                 line (a raycast) from the player's eye-line in the direction 
                 the camera is looking.
Fixed-Steps    : Instead of complex math formulas, the engine advances along 
                 this line in small, 0.1-block increments up to a configurable 
                 limit (8.0 blocks). At each step, it checks the voxel ID. If 
                 a solid voxel is detected, the marching stops.
Actions        : 
  - Destruction: Left click replaces the targeted solid voxel with AIR (0).
  - Placement  : Right click backtracks exactly one step along the ray and 
                 places a new block (using ACTIVE_BLOCK_ID from settings) in 
                 the empty space preceding the hit.


[2.4 DOUBLE-BUFFERED REMESHING (FLICKER-FREE UPDATE)]
-------------------------------------------------------------------------------
Double Buffer  : Normally, editing a block flags the chunk as unmeshed, 
                 instantly hiding its entire structure from view and causing 
                 a jarring blank flicker on the screen while the CPU rebuilds 
                 the model.
The Solution   : To solve this, the engine implements double-buffering. It 
                 keeps drawing the old, existing geometry on-screen while the 
                 meshing worker silently constructs the updated chunk model. 
                 Once ready, the engine swaps them in a single frame, resulting 
                 in completely seamless real-time updates.
Boundary Sync  : Modifying a block on a chunk's outer boundary automatically 
                 flags neighbor chunks to be updated. When rebuilt, the meshing 
                 worker overlays adjacent chunk edits directly onto the halo 
                 margins, preventing visual seams or missing faces at borders.


[3.0 ATMOSPHERIC & VOLUMETRIC FX]
-------------------------------------------------------------------------------
Power Fog      : Distance-based blending using an exponential power scale.
Height Shading : Global luma darkening relative to the map ceiling.
Haze Overlay   : 2D alpha-blended screen wash simulating immersion depth.
Note           : Volumetric overlays and height-shading are automatically 
                 disabled for pre-authored inspection maps to ensure clear, 
                 unobscured visibility.


[3.1 AIMING HUD OVERLAY (CROSSHAIR)]
-------------------------------------------------------------------------------
Aiming HUD     : A static, thin targeting cross (+) is drawn on top of the 
                 rendered scene.
Implementation : The crosshair is drawn directly in 2D space by the UI manager 
                 at the exact coordinates of the viewport center. It is 
                 rendered unconditionally during gameplay to help aim block 
                 placements and destructions.


[4.0 DATA INTEGRITY]
-------------------------------------------------------------------------------
Fingerprinting : Session manifest stores a hash of (Seed, Size, Depth).
                 Mismatches trigger a manifest update to prevent corruption.


[5.0 CO-EXISTING CO-AXIAL ORIENTATION DOMAINS]
-------------------------------------------------------------------------------
1. THE CARTESIAN ZONE (X, Y, Z)
   - Scope       : Physics, Raycasting, and Mesh Rendering.
   - Identity    : Yaw = 0 faces North (+Y), Right points East (+X).

2. THE MEMORY ZONE (Z, Y, X)
   - Scope       : Voxel Storage and Binary .npz Serialization.

3. THE LAUNCHPAD UX DESIGN (PIC TO VOXEL)
   - Layout      : Chunk row 0 contains a solid, 16x16 launchpad runway at Z=0.
                   Chunk row 1 is empty air (the flight gap).
                   Chunk row 2 contains the forged picture starting at Z=0, 
                   perfectly aligned horizontally with the player's line of 
                   sight at spawn.


[6.0 GEOMETRIC WINDING & NORMAL CONVENTION]
-------------------------------------------------------------------------------
Winding Order : Counter-Clockwise (CCW) for front-facing polygons.
Culling Logic : Signed 2D Area < 0 is visible; Area >= 0 is culled.
Basis Alignment: 
  - World Right   : +X (1, 0, 0)
  - World Forward : +Y (0, 1, 0)
  - World Up      : +Z (0, 0, 1)


[7.0 CORE SUBSYSTEM ARCHITECTURE]
-------------------------------------------------------------------------------
                                  [ run.py ]
                                       │
                                       ▼
                             [ VoxelEngine (Core) ]
                                       │
               ┌───────────────────────┴───────────────────────┐
               ▼                                               ▼
       [ Timing Control ]                             [ State & Inputs ]
        (engine/clock)                               (statemanager/control)
               │                                               │
               └───────────────────────┬───────────────────────┘
                                       ▼
                              [ SYSTEM TICK LOOP ]
                                       │
      ┌────────────────────────────────┴───────────────────────────────┐
      ▼                                                                ▼
┌──────────────┐ (Fixed dt)                              ┌──────────────┐
│ PHYSICS LOOP │                                         │ RENDER LOOP  │
└──────┬───────┘                                         └──────┬───────┘
       │                                                        │
       ├─► [ Player Entity ]                                    ├─► [ Blend (α) ]
       │   └─► Collision/Resolution                             │
       │                                                        ├─► [ Scene ]
       └─► [ Static Map Slice ]                                 │   ├─► Frustum
                                                                │   └─► Sorting
                                                                │
                                                                ├─► [ Batcher ]
                                                                │   └─► Rasterize
                                                                │
                                                                ├─► [ Lifecycle ]
                                                                │   └─► Meshing
                                                                │
                                                                └─► [ UI/Debug ]

===============================================================================

Distributed under the MIT License. Copyright (c) 2025 herbal1st.