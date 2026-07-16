```text                 
    __           __                         
 __/\ \__       /\ \           __           
/\_\ \ ,_\   ___\ \ \___      /\_\    ___   
\/\ \ \ \/  /'___\ \  _ `\    \/\ \  / __`\ 
 \ \ \ \ \_/\ \__/\ \ \ \ \  __\ \ \/\ \L\ \
  \ \_\ \__\ \____\\ \_\ \_\/\_\\ \_\ \____/
   \/_/\/__/\/____/ \/_/\/_/\/_/ \/_/\/___/   
===============================================================================
             PYVORENGI ENGINE - WEB & BENCHMARKING RELEASES
===============================================================================

Welcome to the specialized WebAssembly deployment branch of the PyVorengi 
Voxel Engine. 

This branch hosts the exact legacy build compiled for the web-based interactive 
demo running live on itch.io:
https://herbal1st.itch.io/pyvorengi-voxel-engine-demo


[1.0 ENGINE AND BRANCH SYNCHRONIZATION STATUS]
-------------------------------------------------------------------------------
Please note that this branch is intentionally NOT fully synchronized with our 
main desktop branch. This is due to:

  - Specialized Web Requirements: The web build utilizes single-threaded task-
    trickling loops to preserve web browser responsiveness.
  - Omission of Heavy Subsystems: Desktop-specific features such as the 3.5D 
    Porter Bridge, the Space Flight hybrid game, image-to-voxel compilations, 
    and persistent file caching are stripped to minimize deployment footprint.
  - Semi-Active Porting: Core optimizations are brought over selectively only 
    as they prove viable within single-threaded WebAssembly runtimes.


[2.0 WEB COMPATIBILITY AND WASM OPTIMIZATIONS]
-------------------------------------------------------------------------------
This branch has been designed around the strict constraints of standard web-
assembly browsers:

  - Single-Threaded Pipeline: Python multiprocessing is bypassed. Chunk loads 
    and meshing tasks are trickled sequentially (via asyncio.sleep) to maintain 
    smooth browser refresh rates without crashing WASM execution layers.
  - Vectorized Math Focus: Direct, highly-vectorized NumPy operations are used 
    for projection, backface culling, and topological sorting to maximize 
    CPU throughput.
  - Configured for Web Compilers: This branch includes standard Pygbag script 
    headers in 'main.py' and a modern 'pyproject.toml' configuration file for 
    Pygodide automated dependency resolution.


[3.0 RUNNING THE BENCHMARKS LOCALLY]
-------------------------------------------------------------------------------
You can compile and run this web build locally using either Pygbag or 
Pygodide tools.

Running with Pygbag:
1. Install pygbag via pip:
   pip install pygbag
2. Execute pygbag targeting the branch directory:
   pygbag .

Running with Pygodide:
1. Ensure your local Pygodide environment is configured.
2. The Pygodide compiler will automatically parse 'pyproject.toml' to fetch 
   and bundle the required 'numpy' and 'pygame' dependencies.


[4.0 INTERACTIVE SANDBOX CONTROLS]
-------------------------------------------------------------------------------
To test rendering and calculation latency, please click inside the window to 
capture your mouse, and use the following interactive diagnostic hotkeys:

  - Move / Fly: W/A/S/D — Move horizontally | E — Fly Up | Q — Fly Down
  - Telemetry : 0 (Zero Key) — Toggle Debug & Controls latency HUD
  - World Seed: R — Rebuild world with a completely randomized seed
  - Noise Model: N — Cycle between Perlin and Simplex noise algorithms
  - Fog Density: F — Cycle through distance fog intensities
  - Valley Haze: H — Cycle valley haze/mist altitudes
  - Fog Formula: T — Toggle distance fog calculations (Linear vs Exponential)
  - Sky Preset : C — Cycle sky and ambient background colors


[5.0 CODE AND ARCHITECTURE DETAILS]
-------------------------------------------------------------------------------
For a deep dive into the engine's core coordinate domains, C-contiguity, and 
topological sorting math, please consult the primary desktop branch's 
documentation:

  - DEVELOPER.md : Conceptual blueprints, memory layouts, and workflow setups.
  - MANUAL.txt   : Full documentation of core engine settings and variables.

===============================================================================
Distributed under the MIT License. Copyright (c) 2025-2026 herbal1st.