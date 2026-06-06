<pre>
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
Make sure you have Python 3.x installed along with the required libraries:
pip install pygame numpy pyyaml

Launching the Engine:
To start the demo, navigate to the project directory and run:
python run.py

Note: Run map_maker.py to generate a structured block inspection walkway.
Set USE_PROCEDURAL = False in settings.py to load this static map.


[1.0 SYSTEM OVERVIEW]
-------------------------------------------------------------------------------
Core Philosophy: Vectorized, Cache-Conscious, and Single-Threaded.
Architecture   : Chessboard-modular voxel engine utilizing a "Hot-Zone" bubble.
Source Hardware: Ryzen 7 5825U (16GB RAM) - Stable 25+ FPS @ 95 block view.

[2.0 MEMORY CONVENTION & DATA LAYOUT]
-------------------------------------------------------------------------------
Standard       : Dual Layout - (Z, Y, X) [Storage] | (X, Y, Z) [Simulation]
Rationale      : Storage/IO processes raw voxels as (Z, Y, X) to align with
                 NumPy C-order contiguity and optimize flat serialization.
The Transpose  : A (2, 1, 0) transpose is executed during the meshing phase to
                 align array indexing with classic (X, Y, Z) Cartesian math.
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

[3.0 ATMOSPHERIC & VOLUMETRIC FX]
-------------------------------------------------------------------------------
Power Fog      : Distance-based blending using an exponential power scale.
Height Shading : Global luma darkening relative to the map ceiling.
Haze Overlay   : 2D alpha-blended screen wash simulating immersion depth.

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

3. THE LOADER TRANSPOSE (STATIC MAPS)
   - Logic       : Static files stored as (X, Y, Z) are transposed and X-axis 
                   reversed to match the engine's internal winding order.

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
</pre>
