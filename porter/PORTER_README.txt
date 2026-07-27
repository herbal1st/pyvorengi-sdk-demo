```text
 ____               __                   
/\  _`\            /\ \__                
\ \ \L\ \___   _ __\ \ ,_\    __   _ __  
 \ \ ,__/ __`\/\`'__\ \ \/  /'__`\/\`'__\
  \ \ \/\ \L\ \ \ \/ \ \ \_/\  __/\ \ \/ 
   \ \_\ \____/\ \_\  \ \__\ \____\\ \_\ 
    \/_/\/___/  \/_/   \/__/\/____/ \/_/ 
===============================================================================
       THE PORTER BRIDGE (3.5D HYBRID SYSTEM) - USER & TECH MANUAL
===============================================================================

[1.0 THE PORTER BRIDGE CONCEPT & 3.5D HYBRID RENDERING]
-------------------------------------------------------------------------------
The Porter Bridge is a specialized 2D-to-3D graphics translation pipeline. 
It allows the engine to intercept standard flat 2D sprite draw calls at 
runtime and project them as fully-realized, depth-sorted 3D voxel models on 
top of the gameplay layer.

This hybrid approach is referred to as "3.5D" rendering:
  - The core simulation, movement, and collision loops run on a flat 2D plane.
  - The visuals of the actors are calculated and projected in 3D.
  - Perspective drift is eliminated by locking the camera straight down at a
    flat height of 25.0 and look-down pitch of -pi/2, achieving a 1:1 pixel-to-
    block projection while rendering true 3D hulls and vertical side walls.


[2.0 DYNAMIC LAYER EXTRUSION & COMPILATION PIPELINE]
-------------------------------------------------------------------------------
Normally, 2D sprites converted to 3D voxel grids look thin and paper-like. The 
Porter Bridge solves this through a configuration-driven compilation pipeline 
that extrudes flat images into thick, solid 3D volumes.

The Data Flow:
  - 1. Discovery (autofill.py):
       Automatically scans selected graphics folders to detect new sprite images
       and registers them in a centralized configuration file named 
       "assets_config.yaml" with baseline templates.
       
  - 2. Configuration (assets_config.yaml):
       Allows you to set the active "render_3d" flag and adjust the model's 
       extrusion thickness using the "thickness" parameter.
       
  - 3. Compilation (forge_assets.py):
       Reads assets_config.yaml and compiles only the sprites marked for 3D 
       rendering. It processes transparent PNG pixels as empty air and uses 
       high-precision color comparison to map image pixels to solid voxel IDs. 
       Finally, it extrudes the flat 2D grid along the Z-axis (height) into a 
       solid 3D voxel block of "thickness" depth, saving it as a compressed 
       ".npz" asset file.


[3.0 OPTIMIZATIONS, CULLING & BOUNDARY CLAMPING]
-------------------------------------------------------------------------------
To render 3D assets in real-time on a single-threaded CPU, the Porter Bridge 
implements several advanced optimizations to minimize the polygon drawing and 
sorting overhead:

  - Bottom-Face skipping:
       Since the camera looks straight down at the play plane, the bottom faces 
       of the 3D models are always hidden from the player's view. By skipping 
       their compilation entirely, the pipeline cuts mesh sizes by roughly 45%.
       
  - Side-Face Culling:
       Voxel faces inside the solid model are completely removed. A voxel’s 
       side face is only generated if it is adjacent to empty air, leaving 
       the interior of the model hollow and saving valuable rendering budget.
       
  - Top-Boundary Safety Clamping:
       Normally, culling engines use shift calculations to check if a block is 
       covered from above. On thick assets, this can cause "rollover culling," 
       where the top layer falsely assumes it is covered and culls itself, 
       rendering the model hollow. The pipeline implements a top safety clamp, 
       forcing the absolute top-most layer of voxels to keep their top faces 
       intact and solid under any thickness setting.


[4.0 COORDINATE SYSTEMS, ALIGNMENT & ROTATIONS]
-------------------------------------------------------------------------------
To keep the pipeline robust, the bridge maps the image's coordinate space to 
the Cartesian world by addressing three orientation domains:

  - The Matrix Transpose:
       Pygame's pixel array is structured in an (X, Y) layout. The compiler 
       transposes this to standard (Y, X) Cartesian memory layout at save-time. 
       This removes the need for real-time transpositions during gameplay.
       
  - The Double-Chirality Inversion:
       In 3D graphics, single coordinate reflections (like a vertical flip or 
       horizontal flip) invert coordinate "chirality" (handedness). This flips 
       the face winding orders, causing the backface culling engine to misidentify 
       visible side walls as hidden and cull them. The bridge applies zero flips 
       at compile-time, preserving perfect coordinate chirality so side walls 
       render stably.
       
  - The Viewport Correction:
       Because zero flips are applied during compile-time to protect the culling 
       math, the model naturally faces South (backward). The viewport interceptor 
       (viewport.py) resolves this by applying a 180-degree rotation offset 
       at draw-time, turning the model forward along its actual flight path 
       without changing coordinate chirality.


[5.0 CONFIGURATION METRICS REFERENCE]
-------------------------------------------------------------------------------
The "assets_config.yaml" database contains the following tunable metrics 
governing how each sprite is projected in 3D:

  - render_3d   : Boolean. Toggle 3D voxel interception and drawing. Set to 
                  True to project the sprite as a 3D model, or False to render 
                  it as a flat 2D sprite.
                  Metric: bool.
                  
  - scale       : Float. Resizing scale multiplier applied to the 3D model. 
                  Allows you to expand or shrink the voxel mesh.
                  Metric: scale.
                  
  - thickness   : Float. The number of vertical 3D voxel layers to extrude the 
                  flat 2D sprite into. Larger values create thicker 3D structures.
                  Metric: layers.
                  
  - tilt_factor : Float. Maximum lateral banking roll limit in degrees. Controls 
                  how much the 3D model banks left or right relative to its 
                  horizontal movement speed.
                  Metric: degrees.

===============================================================================

Distributed under the MIT License. Copyright (c) 2025 herbal1st.