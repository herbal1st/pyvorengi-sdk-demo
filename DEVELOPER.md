# Developer Overview & Architecture Blueprint

This document outlines the development philosophy, structural assembly, and 
vectorized data pipelines of the PyVorengi Demo Engine.

---

## 1. About the Developer & AI-Assisted Workflow

This engine was designed and built by a self-taught, non-degree indie hobbyist 
developer. 

While I do not hold a formal degree in mathematics or computer science, my 
approach centers on systemic design, modular architecture, and rapid learning.

To bridge the gap between high-level architectural ideas like the 
([+2]x[+2]x[+2]) coordinate halos and C-contiguity memory layouts and dense 
vector math, I utilized modern AI coding assistants as collaborative R&D partners. 

This workflow allowed me to:
* **Systematically Design:** Define and build the engine boundaries and 
  modular state-flow logic.
* **Optimize Operations:** Leverage AI assistants to generate and optimize 
  dense, vectorized NumPy matrix transformations.
* **Learn and Apply:** Research, verify, and implement advanced graphics 
  and physics concepts interactively on the fly.

---

## 2. Minimalist Development Workflow & Toolchain

Rather than relying on resource-heavy IDEs, complex compiler toolchains, or 
bloated project-management suites, this engine was developed using an 
ultra-lightweight, high-efficiency R&D pipeline:

1. **Context Aggregation (The Flattening Script):** A custom local script is 
   executed to parse the entire implicit namespace folder tree, merging the 
   entire multi-module codebase into a single, structured `.txt` file.
2. **AI-Collaborative Engineering:** The flattened codebase file is uploaded 
   to an online assistant to provide 100% project-aware context for 
   mathematical evaluations, code reviews, and structural refactoring.
3. **Zero-Overhead Environments:** Generated code blocks and architectural 
   refinements are manually integrated and tested using standard Python 
   **IDLE** or raw **Windows Notepad**. 

This process demonstrates that structured systemic discipline, paired with 
modern collaborative AI tools, can produce optimized software on simple, 
standard systems.

---

## 3. Core Subsystem Architecture

Below is the verified structural topology of the single-threaded demo:

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
      ┌────────────────────────────────┴────────────────────────────────┐
      ▼                                                                 ▼
┌──────────────┐ (Fixed dt=1/FPS)                        ┌──────────────┐ (Variable FPS)
│ PHYSICS LOOP │                                         │ RENDER LOOP  │
└──────┬───────┘                                         └──────┬───────┘
       │                                                        │
       ├─► [ Player Entity ] (physics/entity)                   ├─► [ Interpolation ]
       │   ├─► Collide (physics/physics)                        │   └─► Position Blend via α
       │   └─► Resolve (physics/resolution)                     │
       │                                                        ├─► [ Scene Manager ] (renderer/scene)
       └─► [ Static Map Slice ] (map/custom_map_buffer)         │   ├─► Frustum Sweeper (frustum)
                                                                │   └─► Depth Sorting (scene)
                                                                │
                                                                ├─► [ Batch Renderer ] (renderer/batch)
                                                                │   ├─► Aggregation (batch)
                                                                │   ├─► Shaders & FX (visuals)
                                                                │   └─► Rasterize (Pygame Surface)
                                                                │
                                                                ├─► [ World Lifecycle ] (world/logic/lifecycle)
                                                                │   ├─► Strategist (world/strategy)
                                                                │   └─► Worker Tasks (world/workers)
                                                                │       └─► Generation (map/generator)
                                                                │       └─► Meshing (mesher/mesher)
                                                                │
                                                                └─► [ UI & Telemetry ] (ui/manager)
                                                                    └─► Memoized View (ui/debug)

```
---

## 4. Co-Existing Co-Axial Orientation Domains

The engine bridges the gap between classic Cartesian spaces and contiguous 
memory layouts by maintaining three distinct coordinate domains:

### Domain 1: The Cartesian Zone `(X, Y, Z)`
* **Scope:** Physics resolving, player entity coordinates, camera raycasting, 
  and geometric projection matrices.
* **Chirality:** Standard right-handed space. Yaw = 0 faces North (`+Y`), 
  Right points East (`+X`), and Up points toward the Sky (`+Z`).

### Domain 2: The Memory Zone `(Z, Y, X)`
* **Scope:** 3D voxel data grids, compressed `.npz` storage buffers, and 
  NumPy array operations.
* **Layman's Analogy:** Imagine a neatly sorted file cabinet. To read files 
  as fast as possible, you want them organized in drawers (Z-slices), then 
  rows (Y-coordinates), then individual folders (X-coordinates). This structure, 
  known as "C-order contiguity", allows NumPy to slice through the data with 
  minimal hardware delay.

### Domain 3: The Asset Transpose Zone (Offline Pipeline)
* **Scope:** Sourcing raw voxels from pre-authored static maps and images.
* **Implementation:** To achieve zero real-time load overhead, the 3D array 
  shuffling is handled entirely offline. When `map_maker.py` or 
  `pic_to_voxel.py` save files, they perform the `(X, Y, Z)` to `(Z, Y, X)` 
  transpose and horizontal flip (`[:, :, ::-1]`) *before* compression. 
  This allows the `MapManager` at runtime to execute a pure, pass-through read 
  directly into memory, completely removing real-time load-screen delays.

---

## 5. Geometric Winding & Normal Conventions

To ensure zero-allocation backface culling on the CPU without hardware depth 
buffers, the visual pipeline enforces strict rendering rules:

* **Winding Order:** Polygons are packed using Counter-Clockwise (CCW) 
  vertex indices. 
* **Layman's Analogy:** Think of winding order like drawing a circle on a 
  clear pane of glass. If you draw it counter-clockwise, it is facing you. If 
  you view it from the other side, your circle appears clockwise. The engine uses 
  this simple visual trick to instantly discard any polygon that looks "clockwise" 
  (meaning it is on the back or inside of a block) to save drawing time.
* **Culling Metric:** Signed 2D Projected Area is calculated per polygon. 
  Areas $< 0$ are rendered; Areas $\ge 0$ are discarded (backfaces).
* **Basis Vectors:**
  * World Right: `+X` $(1, 0, 0)$
  * World Forward: `+Y` $(0, 1, 0)$
  * World Up: `+Z` $(0, 0, 1)$

---
Distributed under the MIT License. Copyright (c) 2025 herbal1st.