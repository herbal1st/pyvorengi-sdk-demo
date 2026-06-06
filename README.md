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
Make sure you have Python 3.x installed along with the required libraries.
You can install them by running:
pip install pygame numpy pyyaml

Launching the Engine:
To start the demo, navigate to the project directory and run the entry
script:
python run.py


[1.0 SYSTEM OVERVIEW]
-------------------------------------------------------------------------------
Core Philosophy: Vectorized, Cache-Conscious, and Interaction-Synchronized.
Architecture   : Chessboard-modular voxel engine utilizing a "Hot-Zone" bubble.
Source Hardware: Ryzen 7 5825U (16GB RAM) - Stable 25+ FPS @ 95 block view.

Note: Run _map_maker.py to generate a structured block inspection walkway.
Set USE_PROCEDURAL = False in settings.py to load this static map.
(Pre-created Map included)

[2.0 MEMORY CONVENTION & DATA LAYOUT]
-------------------------------------------------------------------------------
Standard       : Dual Layout - (Z, Y, X) [Load] | (X, Y, Z) [Core Gameplay]
Rationale      : Storage/IO processes raw voxels as (Z, Y, X) to align with
                 NumPy C-order contiguity and optimize flat serialization.
The Cartesian  : A transpose is executed in the meshing/physics boundary to
The Transpose  : align array indexing with classic (X, Y, Z) Cartesian math.
The Halo Trick : All chunks are padded with a +1 block border ([+2]x[+2]x[+2]).
Hot-Zone Sync  : Inside the interaction radius, the halo is sourced from 
                 neighbor core memory rather than procedural noise. This 
                 ensures absolute geometry continuity during block edits.

[2.1 PROCEDURAL SERIALIZATION BYPASS]
-------------------------------------------------------------------------------
Optimized Path : Pure procedural chunks are never automatically written to disk.
Rationale      : Regeneration from seed is more efficient than disk I/O.
Stale Conflict : Disk saving is strictly reserved for pre-authored map files 
                 (USE_PROCEDURAL = False) or modified procedural chunks 
                 (chunk.is_dirty = True) to maintain zero-I/O gameplay.

[2.2 PROCESS WORKER MEMORY CACHING]
-------------------------------------------------------------------------------
Optimization   : VoxelRegistry is instantiated at the module level in workers.
Rationale      : Background processes persist on Windows; caching at module 
                 level compiles voxels.yaml once, bypassing disk IO.

[2.3 FRAME 1 KICKSTART (REPLACES BOOTSTRAP LOCK)]
-------------------------------------------------------------------------------
Kickstart      : The Lifecycle Manager ignores movement thresholds on Frame 1.
Rationale      : By forcing an immediate world reconciliation, the view frustum
                 is populated with mesh tasks instantly. The bootstrapper 
                 loop now confirms the 3x3 spawn area in milliseconds.

[2.4 THE DUAL-FLAG SYNCHRONIZATION SYSTEM]
-------------------------------------------------------------------------------
State 1: is_dirty (Persistence)
      - Scope: Chunk Level.
      - Trigger: Voxel modification (set_voxel).
      - Effect: Forces a disk-write to the world delta layer on exit.

State 2: dirty_sections (Geometric)
      - Scope: Section Level (Z-index).
      - Trigger: Voxel modification or initial load.
      - Effect: Signals the LifecycleManager to queue a sub-volume remesh.

[3.0 ATMOSPHERIC & VOLUMETRIC FX]
-------------------------------------------------------------------------------
Power Fog      : Distance-based blending using an exponent power scale.
Height Shading : Global luma darkening relative to map ceiling depth.

[4.0 DATA INTEGRITY]
-------------------------------------------------------------------------------
Fingerprinting : Session manifest stores a hash of (Seed, Size, Depth).
                 Mismatches trigger a force-clean to prevent corrupted geometry.

[5.0 CO-EXISTING CO-AXIAL ORIENTATION DOMAINS]
-------------------------------------------------------------------------------
1. THE CARTESIAN ZONE (X, Y, Z)
   - Scope       : Physics, Raycasting, Sensation, and Mesh Rendering.
   - Identity    : Yaw = 0 faces North (+Y), Right points East (+X).
   - Source      : Centralized via spatial.transformer.

2. THE MEMORY ZONE (Z, Y, X)
   - Scope       : Bulk Chunks, Voxel Storage, and Binary Disk Serialization.

3. THE GENERATOR & LOADER ZONE (PROCEDURAL VS. STATIC TRANSPOSE)
   - Procedural  : meshgrid(world_y, world_x) mapped into (Z, Y, X) memory.
   - Static Maps : Files (X, Y, Z) require a (2, 1, 0) transpose to align.

[6.0 GEOMETRIC WINDING & NORMAL CONVENTION]
-------------------------------------------------------------------------------
Winding Order : Counter-Clockwise (CCW) for front-facing polygons.
Area Logic    : Signed 2D Area < 0 is visible; Area > 0 is culled (Backface).
Basis Alignment: 
  - World Right   : +X (1, 0, 0)
  - World Forward : +Y (0, 1, 0)
  - World Up      : +Z (0, 0, 1)
HUD Projection Math (Turntable Logic):
  - Matrix        : Pitch(X) @ Yaw(Z) order to ensure tilt stability.
  - Pivot         : Geometry is centered at (0,0,0) before rotation pass.
  - Mapping       : World-X -> Screen-X | World-Z -> Screen-Y (Reflected).
  - Depth-Axis    : World-Y serves as the Depth-into-Screen for Painter's Sort.
The Reflection Tax:
  - The Z-to-Screen-Y reflection creates a mathematical Mirror-Basis. 
  - To maintain visibility under the Signed 2D Area test, vertex indices 
    must be reversed to [0, 3, 2, 1] during 3D-to-2D flattening in the HUD. 
  - This ensures projected polygons remain "Front-Facing" (CCW) relative 
    to the 2D screen camera without hardware depth buffers.

[7.0 CORE SUBSYSTEM ARCHITECTURE]
-------------------------------------------------------------------------------
<pre>
```text
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
       ├─► [ Player Entity ] (physics/entity)                   ├─► [ Blend (α) ]
       │   ├─► Collide (physics/physics)                        │
       │   └─► Resolve (physics/resolution)                     ├─► [ Scene ]
       │                                                        │   ├─► Frustum
       └─► [ Static Map Slice ] (map/buffer)                    │   └─► Sorting
                                                                │
                                                                ├─► [ Batcher ]
                                                                │   ├─► Shaders
                                                                │   └─► Raster
                                                                │
                                                                ├─► [ Lifecycle ]
                                                                │   ├─► Workers
                                                                │   └─► Meshing
                                                                │
                                                                └─► [ UI/Debug ]
```
</pre>

===============================================================================

Distributed under the MIT License. Copyright (c) 2025 herbal1st.