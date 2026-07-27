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

1. Core Voxel Engine (Main Sandbox)
Launch the main sandbox world viewer:
python run.py
(By default, generates procedural terrain from a seed. Can be configured 
to load static map archives by setting USE_PROCEDURAL = False in settings).

2. Sky Islands Addon (Procedural Modification)
To enable floating procedural terrain, toggle settings in settings.py:
- Set SKY_ISLANDS_ON = True
- Launch via 'python run.py' to generate sky-islands with mirrored floors.

3. Porter Pipeline & Space Flight Game
Launch the 3.5D hybrid space combat simulator:
python space_flight/main.py
(Note: This launches the game using the Porter Bridge, which intercepts 
2D sprite draws and projects them dynamically as sorted 3D voxel models
using the Engine as Renderer. 
Further custom configurations, calibration details, and advanced asset 
pipelines are fully documented in the 'porter/PORTER_README.txt' file.)

4. Picture-to-Voxel Forge (Custom Maps)
Convert flat 2D images (PNG/JPG/JPEG) to 3D voxel geometry:
- Place images inside the 'pic_imports' directory.
- Run: python pic_to_voxel.py
- This compiles them into '.npz' voxel volumes saved inside 'map/maps/'.
- Configure settings.py with GLOBAL_MAP_NAME = "your_image_name.npz" and
  USE_PROCEDURAL = False to launch and explore your custom picture.

5. Map Maker Walkway
Generate a static physical walk-through grid of all registered voxels:
python map_maker.py
- Exports a block-palette matrix to 'map/maps/default_map.npz'.
- Ideal for inspecting textures, normals, and colors side-by-side.


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
                 places a new block (using the currently selected ID shown in 
                 the HUD badge) in the empty space preceding the hit.


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


[2.5 THE PORTER BRIDGE (3.5D HYBRID PIPELINE)]
-------------------------------------------------------------------------------
Bridge System  : Decoupled 2D-to-3D adapter linking sprite draws to voxels.
Scale Lock     : Sets a flat camera height (25.0) and look-down pitch 
                 (-pi/2) to achieve a 1:1 pixel-to-block projection, 
                 eliminating vertical and horizontal perspective drift.
Winding Order  : Vertices are processed in standard index layout. The straight 
                 downward projection automatically resolves camera and vertical 
                 negation signs, keeping face normals fully intact.
Culling Save   : Bottom voxel faces are completely skipped during load compilation 
                 to cut mesh sizes by 45% and conserve processing budget.
Lazy Cache     : Compiles NPZ boundaries once and caches them to protect the 
                 runtime rendering thread from I/O pauses.

[2.6 VOXEL COLOR PALETTE MAPPING]
-------------------------------------------------------------------------------
Color Matching: Both the offline picture-to-voxel compiler (pic_to_voxel.py)
and the Porter sprite compiler (forge_assets.py) use a high-precision 
Euclidean distance match in RGB space to map 2D image pixels to the closest 
solid block color defined in the central engine block database (data/voxels.yaml).
Because of this matching process, compiled 3D voxel textures may experience 
subtle color adjustments to align with the active voxel registry.


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