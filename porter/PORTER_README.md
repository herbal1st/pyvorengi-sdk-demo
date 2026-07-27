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

[PORTER PIPELINE HOW-TO (HOW TO COMPILE & RUN)]
-------------------------------------------------------------------------------
Prerequisites:
Ensure Python 3.x, Pygame, NumPy, and PyYAML are installed.

1. Discovery Phase (Scan and Sync Directories):
   Run the discovery script to recursively catalog your assets and write 
   baseline templates inside 'porter/assets_config.yaml':
   python porter/autofill.py

2. Configuration Phase (Asset Calibration):
   Open 'porter/assets_config.yaml' and configure your files:
   - Set 'render_3d: true' and 'thickness: 6.0' (or greater) for primary 
     parent models (like the base ship and UFOs) that need true 3D depth.
   - Set 'render_3d: true' and 'thickness: 0.0' for dynamic overlay details 
     (such as engine exhaust fire or cockpit lights) that must bank, tilt, 
     and coordinate with parent hulls in 3D.
   - Set 'render_3d: false' for purely static, non-banking flat overlays 
     (like weapons laser beams or vector HUD gauges) to draw them as 2D blits.
     * Layman Note: Projectiles like lasers have soft glowing edges that
       can look pixelated in 3D. Keeping 'render_3d: false' retains their 
       smooth 2D glow while letting them slide beneath 3D hulls.
   - Adjust scale and parent tilt_factor parameters as desired.

3. Compilation Phase (Extruding 3D Voxel Meshes):
   Run the forge script to compile configured 2D sprites into 3D assets:
   python -m porter.forge_assets

4. Execution Phase:
   Launch the hybrid 3.5D space combat simulation:
   python -m space_flight.main


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

  - 4. Euclidean Color Matching:
       The pipeline maps image colors to the closest solid block color 
       defined in the engine block database (data/voxels.yaml) using 
       a high-precision Euclidean distance algorithm. Compiled voxel 
       textures may experience subtle color adjustments to match the 
       active voxel registry.


[2.1 THE PORTER BRIDGE (3.5D HYBRID PIPELINE)]
-------------------------------------------------------------------------------
Bridge System  : Decoupled 2D-to-3D adapter linking sprite draws to voxels.
Scale Lock     : Sets a flat camera height (25.0) and look-down pitch 
                 (-pi/2) to achieve a 1:1 pixel-to-block projection, 
                 eliminating vertical and horizontal perspective drift.
Winding Order  : Vertices are processed in standard index layout. The straight 
                 downward projection automatically resolves camera and vertical 
                 negation signs, keeping face normals fully intact.
Culling Save   : Bottom voxel faces are completely skipped during load 
                 compilation to cut mesh sizes by 45% and conserve budget.
Pre-Warm Cache : Loads and pre-compiles all 3D meshes on startup. To prevent 
                 micro-stutters during combat, the engine builds these meshes 
                 before Frame 1, ensuring near-instantaneous memory lookups.
                 * Layman Analogy: Imagine preparing all your ingredients on 
                   the counter before cooking. Instead of pausing to chop 
                   vegetables in the middle of a recipe, the engine has every 
                   ingredient ready to serve immediately.
3-Pass Layers  : Structurally splits rendering into 2D Background, 3D Voxel 
                 Core (hulls), and 2D Foreground Overlays (exhausts, lights). 
                 Eliminates Z-fighting and ensures perfect depth sorting.
Parallax Math  : Mathematically scales, squishes (cos(theta)), and offsets 
                 (-h*sin(theta)) 2D overlays to match the tilted 3D hull.
Lens Skewing   : Dynamically shifts 2D overlays toward screen borders under 
                 perspective view (using H/h ratio), mimicking lens parallax.


[2.2 ARCHITECTURAL RUNTIME SCALING RULES]
-------------------------------------------------------------------------------
Due to the decoupled nature of the Porter's offline asset compilation,
scaling is parsed through two distinct runtime mechanisms:

  - Absolute Independent Scaling (3D Assets):
       Voxel arrays compiled to NPZ are assembled completely offline. 
       The 'scale' parameter in assets_config.yaml represents the final,
       absolute size of the asset in 3D world blocks (e.g., scale: 2.0
       renders at exactly 2.0 blocks wide).
       * Layman Analogy: Imagine placing a 3D sticker on a toy. If you scale 
         the toy (the parent hull), you do not want the sticker (the exhaust) 
         to scale up with it and become huge. The SDK pre-scales child 
         attachments to decouple them from the parent's scale, preventing 
         mathematical warping while keeping them physically bound in motion.

  - Intercepted 2D Sprite Overlays (Pass 3):
       Flat sprite blits remain standard Pygame surfaces during execution. 
       The Porter intercepts these surfaces inside the active rendering pass, 
       meaning they automatically respect the runtime scaling applied by the 
       developer's game loop (e.g., pygame.transform.scale).


[2.3 THE 3-PASS LAYERING ENGINE & PROXIMITY-STITCH PURGE]
-------------------------------------------------------------------------------
The Porter viewport resolves depth ordering conflicts and eliminates rendering 
overhead through a high-performance 3-Pass Layering pipeline:

  - Pass 1: 2D Background:
       Renders native, distant 2D space starfields and parallax nebulas 
       directly to the raw window surface at the start of the frame.

  - Pass 2: 3D Voxel Core (Dynamic Face Stitching):
       Transforms, depth-sorts, and rasterizes heavy structural hulls. 
       To resolve visual drift of attachments (engine fire, cockpit lights) 
       during banking, their pre-compiled 3D face buffers are dynamically 
       shifted and stitched (concatenated) directly into the parent model's 
       face buffer array at draw-time.
       * Deterministic ID-Locks: Proximity-based stitching (dist < 3.0) 
         has been completely removed from the pipeline. Attachments are now 
         bound strictly using the active parent's unique memory ID during the 
         game's drawing passes. This prevents parent-bleeding errors (such as 
         lights swapping parents or lasers sticking to UFOs) in crowded combat.

  - Pass 3: 2D Foreground Overlays & Vectors:
       - 2D Sprite Overlays: Intercepts flat 2D sprite blits containing our 
         defined overlay keywords (lights, exhausts, shields) and defers them 
         to render cleanly on top of Pass 2, preventing depth-clipping.
       - Vector HUD Drawings: Defers standard rectangles and lines, drawing 
         them last to float over any passing 3D assets without clipping.


[2.4 HYBRID 3.5D STATE INTEGRATION & PROXY SHIELDING]
-------------------------------------------------------------------------------
The Porter Bridge provides a minimally invasive 2D-to-3D graphics adapter. 
To integrate the 3.5D renderer without restructuring a game's logic, three 
core features are used to manage lookup, alignment, and rendering behavior:

1. Proxy Shielding (.blits Interception)
   - What it is: The VoxelSurface proxy intercepts both native single-image 
     draws (.blit()) and fast batch-image lists (.blits()).
   - Why it is useful: This shielding makes standard Pygame sprite groups fully 
     compatible out-of-the-box. Independent overlays (like projectiles and 
     explosions) can use standard Pygame collections, preventing Pygame's 
     underlying C-level optimizations from bypassing our 3D viewport.

2. Cross-Platform Directory Normalization (Automatic)
   - What it is: Standardizes all lookup paths to use standard forward 
     slashes (POSIX formatting) before matching keys.
   - Why it is useful: Prevents key mismatches and folder resolution crashes 
     when developers run the pipeline on different operating systems.

3. Type-Based Routing Discriminator (Automatic)
   - What it is: Distinguishes between 3D Parent Hulls and stitched Attachments 
     by examining the data type of the drawing actor.
   - Why it is useful: If the actor is a Sprite object (Group.draw), it is 
     routed strictly as a parent. If the actor is an integer ID (VoxelSurface.blit), 
     it is processed strictly as an attachment. This prevents parent models 
     from being misclassified as attachments.

4. Roll-then-Yaw Coordinate Transformation
   - What it is: Re-orders the graphics projection matrix to apply banking 
     tilt (Roll) to the local coordinate system first, followed by heading 
     orientation (Yaw).
   - Why it is useful: This ensures the parent hull and the stitched attachments 
     rotate on the exact same mathematical plane, maintaining perfect 
     alignment at any heading.

5. Dynamic Thickness Calibration (Automatic)
   - What it is: Lazy-loads and compares the vertical voxel depth of existing 
     NPZ files against your active YAML configuration before deciding to skip 
     compilation.
   - Why it is useful: If you increase or decrease an asset's thickness in 
     assets_config.yaml, the compiler instantly detects the change, overrides 
     the "Skip" bypass, and re-forges the 3D array with the correct layer depth.

[2.5 PORTER BRIDGE RENDERING & INTER-SCREEN INPUT CAPTURE]
-------------------------------------------------------------------------------
To support standard 2D vector elements and prevent mouse click carry-overs:

* Vector Rendering Precheck:
  The projection loop checks if 2D queues contain any elements before 
  exiting early. This preserves menu performance while rendering grids 
  and dividers stably.

* Click-Release Guard:
  Menus sharing button positions implement a click-release gate check. 
  This prevents button click overlap on state transitions under heavy 
  processor loads.


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
                  flat 2D sprite into. Set to greater than 0.0 to create thick, 
                  extruded structures, or set to exactly 0.0 to generate a flat, 
                  banking 3D sheet (which automatically culls all bottom and 
                  side faces to act as a lightweight card).
                  Metric: layers.
                  
  - tilt_factor : Float. Maximum lateral banking roll limit in degrees. Controls 
                  how much the 3D model banks left or right relative to its 
                  horizontal movement speed.
                  * Note on Banking Tilt: Stitched child assets dynamically 
                    inherit the parent's actual tilt, so their individual 
                    tilt_factor configuration values are ignored at runtime.
                  Metric: degrees.

  - tilt_agility : Float. Responsiveness and banking weight multiplier.
                   Controls how snappy and sensitive the roll behaves. Set
                   above 1.0 for agile, responsive fighters, or below 1.0
                   to simulate massive, heavy capital ships.
                   Metric: multiplier.

  - z_offset     : Float. Vertical offset relative to parent pivot. If a
                   float, overrides default height configurations to pin the
                   asset's origin at a specific layer. If null, the engine
                   uses automatic semantic defaults from settings.
                   Metric: blocks.


[6.0 DIAGNOSTICS & TELEMETRY SYSTEMS]
-------------------------------------------------------------------------------
The Porter viewport features a real-time diagnostic performance overlay:

  - Exponential Moving Average (EMA): The display FPS is smoothed using 
    an EMA with a coefficient of 0.05. This represents an active lookback 
    window of 39 frames (~0.65 seconds of history at 60 FPS).
    * Layman Analogy: This acts like a shock absorber for your car. Instead 
      of the dashboard numbers bouncing up and down wildly over minor bumps, 
      the EMA provides a smooth, readable calculation that shows your true 
      active speed.
    
  - Sliding Window Min/Max: The overlay displays the absolute performance 
    floor and ceiling over a rolling 5.0-second interval to trace frame-time 
    spikes during high-throughput sequences.

  - rep-Positioned Interface: The Porter's telemetry box is positioned cleanly 
    in the lower-left corner of the viewport to allow developers to perform a 
    direct, side-by-side performance comparison against standard 2D viewports.

===============================================================================
Distributed under the MIT License. Copyright (c) 2026 herbal1st.