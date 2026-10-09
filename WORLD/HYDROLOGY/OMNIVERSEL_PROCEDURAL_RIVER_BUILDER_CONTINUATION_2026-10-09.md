# Omniversel Roleplay — Procedural River Builder Continuation Backup
**Snapshot date:** 2026-10-09  
**Purpose:** Resume the Omniversel world/hydrology work in a new ChatGPT conversation without losing decisions, current state, constraints, or next steps.

## 1. Current objective and design decision

The active project is **Omniversel Roleplay**, a Unity 6.3 LTS (6000.3.25f1), URP, mobile-first open-world multiplayer roleplay game. The current goal is to build a **custom Omniversel Procedural River Builder** that works on the project's own connected terrain, instead of depending on a generic one-click river tool that cannot fully conform to the world.

The user asks whether it can dig its own path and produce a finished river with shorelines, riverbanks, and a rough floor under the river. **Design answer: yes, this is feasible as an Editor-time terrain/mesh generation workflow**, provided the tool explicitly implements those stages. It is not yet implemented. Do not imply it already works or that a package has been created.

The desired output is not merely a green spline or a flat river ribbon. The eventual generator should be capable of producing:
- Terrain-conforming river path derived from the master hydrology route.
- Controlled terrain carving for a river channel, with a configurable depth profile.
- Natural-looking banks and shoulders, not vertical cuts or a simple rectangular trench.
- A rough/irregular riverbed floor with deterministic variation, while preserving plausible downhill flow.
- Shoreline transition/blending where appropriate.
- Water surface mesh conforming to the generated channel and target water elevation.
- River flow UVs/material integration using the already-tested water shader.
- Water-body metadata for later gameplay queries (surface height, depth, flow direction/strength, swimming eligibility).
- Cross-tile continuity across the 40 connected Unity Terrain tiles.
- Preview/validation, backups, and explicit commit/apply controls so heightmaps are not destructively modified without review.
- Editor-time generation and saved meshes wherever possible; avoid heavy runtime procedural work.

This should be a **hybrid**: authored master river routes + terrain-aware sampling/validation + generated terrain shaping and mesh geometry + shader-driven animated water + lightweight gameplay physics. Do NOT build full-world fluid simulation. The user explicitly does not need high-detail localized Level 2 simulation now.

## 2. Project priorities and constraints

- Omniversel is the active project; old DevRoom/local-agent work is historical only.
- Game first; World Builder exists to build this game's world.
- User wants a professional result and practical downloadable project files/instructions, not an unimplemented concept or disposable prototype.
- User prefers direct, accurate steps and dislikes rushed/contradictory instructions.
- Do not ask the user to manually sculpt all rivers or manually recreate all routes point-by-point.
- Do not replace previously accepted terrain tiles or reset the terrain.
- Do not make another ocean surface: **the ocean surface already exists in the Unity scene**.
- Existing ocean should remain at sea level Y=0 and should not be duplicated by hydrology tooling.
- Avoid expensive mandatory compute-shader features; the development PC has Intel HD 2000 and has previously had compute/RGBA16 SFloat limitations.
- Rendering/shader polish should happen after geography/geometry is sound.
- Keep optional advanced fluid simulation out of the current scope.
- Never claim an operation succeeded unless the user or tool confirms it.

## 3. World scale and tile architecture

Master world working envelope:
- 40 km east-west × 25 km north-south = 1,000 km² (not 1,000 km × 1,000 km).
- X is east/west, Z is south/north, Y is elevation in metres.
- Terrain bounds: X = -20 km to +20 km; Z = -12.5 km to +12.5 km.
- Sea level Y=0.
- Existing ocean is a separate surface extending beyond the terrain.

Terrain grid:
- 8 columns × 5 rows = 40 tiles.
- Each tile is 5 km × 5 km.
- Skeleton TerrainData resolution 513×513.
- Imported RAW encoding: decoded height = raw/65535*2200 - 100; imported terrain base Transform Y should be -100 m.
- Tile edges were repaired in Unity TerrainData and verified: **67 internal seams checked; 67 pass within 0.01 m; 0 failures**. Do not rerun or redo seam repair unless a later diagnostic demonstrates a real issue.
- User saved the project after the successful seam repair.

Authoritative handwritten tile layout (do not substitute a guessed layout):
```text
T00  T01  T02  T03  T04  T54  T64  T74
T10  T11  T12  T13  T14  T53  T63  T73
T20  T21  T22  T23  T24  T52  T62  T72
T30  T31  T32  T33  T34  T51  T61  T71
T40  T41  T42  T43  T44  T50  T60  T70
```
A Unity hierarchy may sort object names alphabetically; that does not define physical layout. Physical positions were corrected and validated by the handwritten-layout repair tool.

## 4. Source-of-truth master geography in repository

Repository: https://github.com/PranaySardar-10/DEV-ROOM-TEST  
Original working backup branch: `backup/memory-for-project-2026-09-24`

Master geography source of truth:
- `WORLD/MASTER_GEOGRAPHY/OMNIVERSEL_MASTER_GEOGRAPHY_v1.yaml`
- `WORLD/MASTER_GEOGRAPHY/OMNIVERSEL_MASTER_GEOGRAPHY_v1.md`

Links:
- https://github.com/PranaySardar-10/DEV-ROOM-TEST/blob/backup/memory-for-project-2026-09-24/WORLD/MASTER_GEOGRAPHY/OMNIVERSEL_MASTER_GEOGRAPHY_v1.yaml
- https://github.com/PranaySardar-10/DEV-ROOM-TEST/blob/backup/memory-for-project-2026-09-24/WORLD/MASTER_GEOGRAPHY/OMNIVERSEL_MASTER_GEOGRAPHY_v1.md

Previously recorded SHA values:
- YAML: `95bf51b12d222becd1b0150ca4bd75ceae7c712c`
- MD: `31f00275c27a66f1ecb830e33732ca130046c162`

These are design/control values, not real-world measured geography. The YAML is machine-readable source of truth.

Relevant approximate region centers (km X,Z):
- NW Coast [-16,9]
- Military Zone [-12,8], 80–450m
- Western Forest [-12,3], 200–900m
- Port City [-9,-2], 0–90m
- Main City [0,-1], 5–180m
- Mountain Lake [-1,4.5], 650–1050m
- Northern Mountains [1.5,8.5], 700–2100m
- Northern Rural [6.5,6], 150–450m
- Rural Farm [2,1.5], 50–220m
- Eastern Rural [8.5,1.5], 40–300m
- Desert [13,7], 40–650m, one dominant lake
- Airport [11.5,-0.5], 0–80m
- Coastal City [8.5,-4], 0–120m
- Southern Rural [0,-6.5], 20–250m
- Resort Island [-7,-10], 0–280m
- Private Island [12,-9], 0–320m

Mountain systems:
- Northern Backbone: [(-8,7),(-4,8.5),(0,10),(4,9),(7.5,7)], peaks [1200,1550,1900,2100,1700]
- Western Hills: [(-18,6),(-15,4),(-13,1.5)], peaks [700,900,650]
- Desert Rim: [(8,8.5),(12,10),(17,8)], peaks [450,650,500]

Lakes:
- Mountain Lake center [-1.5,5], approx 12 km², target water level 780m
- Desert Lake [13,7], approx 10 km², target water level 55m
- Northern Small Lake [4.5,8], approx 3 km², target water level 980m

## 5. Current hydrology foundation and committed river routes

Hydrology foundation files/tool were installed successfully after fixing the folder nesting issue. Intended package layout:
```text
Assets/
├── Editor/
│   └── OmniverselHydrologyFoundationBuilderV2.cs
└── Omniversel/
    └── World/
        └── Hydrology/
            └── OmniverselMasterHydrologyData.cs
```
The master hydrology layout was created in Unity.

Existing master hydrology data:
- Sea level = 0m.
- Mountain Lake, Desert Lake, Northern Small Lake as listed above.
- Three main rivers with routes below.

Initial river elevation diagnostics found four inversions. A route solver adjusted the controls and the user applied the solved routes using the route-apply tool. **These are the currently committed routes**:

CentralRiver:
`(1,9.5) -> (0.5,6.5) -> (0,2.5) -> (-0.5,0.5) -> (-0.5,-3.5) -> (-1.25,-8.75)`

WestRiver:
`(-11,7) -> (-11.5,5.5) -> (-11,1) -> (-10,-1) -> (-10,-3)`

EastRiver:
`(5,8.5) -> (6.5,6) -> (7,3) -> (8.5,0.5) -> (9.5,-4.25)`

The solver validated all three route lines as solved. These routes are intended control points, not a final high-resolution centerline. The future builder should interpolate/sample them into smooth curves, sample the actual terrain, solve local bank/channel elevations, and validate the entire path. Do not silently revert them to the original routes.

Important note: the route solver adjusted a few control points significantly to remove uphill inversions. A new terrain-aware solver may refine/flag these routes if it finds a real problem, but should preserve authored geography and present proposed changes before committing.

## 6. Water and river tools already in project

### Existing ocean
The scene hierarchy screenshot shows a GameObject named `Water Surface`; this is the existing ocean surface. It must be preserved. Do not create another ocean plane.

### Uber Stylized Water
- Asset: Uber Stylized Water by MatrixRex.
- Unity 6 + URP, open source/MIT according to prior review.
- User combined its material with Realistic Texture Pack and liked the realism, though it caused some lag.
- This should be the leading rendering/material option, subject to mobile profiling.
- It is a shader/rendering layer, not the river geometry generator.

### Easy River
- Already present in the Unity project.
- User screenshot shows a green spline and editable control points across the terrain; hierarchy has `RiverSystem`.
- This proves the tool offers a spline-style editing workflow, but its exact capability to carve terrain, shape banks, produce a rough riverbed, support connected 5km terrain tiles, and generate water mesh has **not yet been confirmed**.
- Keep it available as a possible spline/path authoring UI or source of route data.
- Do not assume it is enough to create the final river.
- Do not buy a new tool before evaluating whether it can be integrated.

### Other free tools investigated
- InstantRiver: https://github.com/bonahona/instantriver — MIT open-source Bézier-based Unity river generation. Small repository, no published releases; documented workflow expects collider/terrain beneath the river. Potential code reference or separate test, not a confirmed production solution.
- SplineMesh: https://github.com/methusalah/SplineMesh — MIT general-purpose spline mesh generation. Could help with custom mesh generation; not a complete hydrology/terrain-carving solution.
- Spline Stamper: https://github.com/Rumesic/spline-stamper-unity-terrain-tool — edits native Unity Terrain heightmaps/texture maps along paths, but known mesh UV/normal and overlapping-stamper concerns make it risky without fixes.
- Unity Splines: https://docs.unity3d.com/Manual/com.unity.splines.html — native spline foundation, not a finished river generator.
- LibreTerrain: https://libreterrain.org/ — external node-based terrain/hydrology tool for experiments, but do not regenerate current world in it; Unity integration needs verification.
- River Modeler and R.A.M 3 were considered but are paid; user explicitly wants free options.
- Uber Stylized Water should be kept as rendering candidate.
- Do not rely on WaterWorks or older Built-In pipeline-only tools without Unity 6.3 URP verification.

## 7. Experimental package that must NOT be run yet

A previous assistant generated:
`Omniversel_HydrologyWaterGeometry_v1.zip`

It contains a menu to create:
- a 100km × 100km ocean at Y=0,
- 3 lake surfaces represented as flattened cylinders,
- 3 river quad-strip meshes sampled only at route control points.

This is a placeholder and **must not be run** because:
1. It would create a duplicate ocean even though the ocean already exists.
2. Lake circles and simple river ribbons are not finished terrain-aware rivers.
3. It does not carve a channel, shape banks, create a rough floor, or provide production-quality shoreline geometry.
4. It is not the desired final system.

Do not confuse this experimental package with a completed river generator. Do not import/run it unless it is first corrected and explicitly needed for a controlled test.

## 8. What the user means by “finished procedural river”

The user's latest explicit requirement is that the generator should be able to **dig its own path into the custom terrain and produce a finished result**, including:
- Natural river channel cut into the terrain.
- River banks on both sides.
- Shoreline edges/transitions.
- Rough, irregular floor beneath the water (riverbed).
- Water surface that follows the carved channel and flows downhill.
- Professional result with easy, preferably one-click Editor workflow.
- Work across custom 40-tile terrain and maintain seams.
- Integrate with our own terrain and hydrology data, not force us to redesign the map.
- Keep the existing ocean, connect rivers to it, do not duplicate it.
- Generate/commit terrain changes only after preview/validation and create backups.
- Use no mandatory expensive runtime fluid simulation.

A high-quality implementation should likely be staged:
1. Read-only audit of current terrain objects, tile names/positions, TerrainData, master hydrology data, Easy River API/data, existing ocean and water material.
2. Build a non-destructive preview mode and backup current heightmaps.
3. Smooth/interpolate each route into a sampled centerline at controlled spacing.
4. Terrain-aware channel carving with configurable width/depth and a cross-section profile: thalweg/bed, sloped banks, shoulder blend, deterministic roughness.
5. TerrainData writes across every intersected tile using consistent world-space samples, preserving border continuity and neighboring tiles.
6. Generate riverbed/bank geometry only if needed for overhangs/rocky floor/visual detail; avoid z-fighting with terrain and water.
7. Generate water surface mesh from the channel route and target water level/slope, with UVs for animated flow. Water surface must not simply copy noisy floor heights; use a stable, flow-aware surface with controlled elevation.
8. Create or update `OmniverselWaterBody` metadata for surface/depth/current and later swimming/buoyancy.
9. Validate downhill slope, terrain/water intersections, channel coverage, tile-edge seams, river outlet to the existing ocean, and lake connections.
10. Show a preview/report and require explicit Apply/Commit; support restore from saved backups.
11. Test one river first (CentralRiver or a short controllable section), then extend to other rivers.
12. Profile runtime on target mobile-like constraints; bake geometry at edit time and keep gameplay physics lightweight.

Potential technical nuance: “dig its own way” should mean **editor-time terrain carving along a terrain-aware path**, not runtime hydraulic erosion or a fully dynamic fluid solver. Terrain shaping should be controllable and reversible. A natural rough riverbed should use bounded deterministic variation and optional rock/pebble detail, not extreme random height noise that breaks flow.

## 9. Previous terrain/grid package status

- Lightweight terrain grid package: `Omniversel_MasterTerrainGrid_v2.zip` (40 connected tiles, 513×513 skeleton resolution).
- Tile coordinate repair package: `Omniversel_TerrainCoordinateRepair_v1.zip`; applied and validated PASS.
- Vertical alignment repair package: `Omniversel_TerrainVerticalAlignmentRepair_v3.zip`; applied and validated PASS, terrain base Y=-100m.
- Seam scanner v2: `Omniversel_MasterTerrainSeamScanner_v2.zip`.
- Seam repair v2: `Omniversel_MasterTerrainSeamRepair_v2.zip`; applied.
- Last seam scan: 67/67 internal seams passed <=0.01m, 0 failed.
- Hydrology foundation v2 successfully installed.
- Flow diagnostics v3, route planner v1/v2, route solver v3, route apply v1 used; final routes are listed in Section 5.
- User reports the Unity scene has `Water Surface`, `OMNIVERSEL_MASTER_HYDROLOGY`, and `RiverSystem` in hierarchy.
- Scene screenshot shows terrain with ocean in foreground and Easy River spline/control points visible. Do not assume screenshot proves channel carving.

## 10. Broader world design context (retain as guardrails)

One coherent region/country, not three disconnected GTA clones:
- Japanese-inspired major metropolis; dense center, business district, suburbs, hills.
- Miami-like coastal/beach city with commercial airport nearby and FBI HQ.
- Compact dense port/industrial/commercial city, some apartment residential, no major beaches or detached housing.
- Japanese farm village; Eastern-European rural village; Sandy Shores/desert village.
- Rich beachside residential and rich lake/mountain residential.
- Super-rich beachfront area and private island connected by bridge.
- Exactly one commercial airport and one separate military airfield.
- Mountain systems, valleys, forests, ocean coast, rocky coves/cliffs, beaches, bays, bridges, ports, meaningful islands.
- 2–3 major rivers and 2–3 major lakes; desert has one dominant lake, not lots of ponds.
- Desert includes hills, off-road area, rocky coast, oil rig, sparse/abandoned structures.
- Continuous open world, no ordinary teleport/loading boundaries between neighboring areas.
- Mobile-friendly performance and controlled storage. User ideally wanted world map manageable in 10–15 GB but can accept 150–200 GB overall project storage excluding assets/editor.

## 11. Exact continuation instructions for the next ChatGPT conversation

Treat this backup file as the authoritative handoff. The user is continuing Omniversel, not starting a new project.

**First response:** confirm the key decision succinctly: yes, a proper generator can carve the river channel and create banks, shorelines and a rough riverbed at Editor time, but this has not been implemented yet. Confirm the existing ocean stays and that `Omniversel_HydrologyWaterGeometry_v1.zip` must not be run.

**Then work, do not merely describe:** inspect the repository/Unity code and existing data before writing code. Use connected GitHub tools/repository branch or the actual project files if available. Do not guess Easy River class names/API. If source access to the Easy River package is unavailable, ask the user for the package's relevant folder/Inspector only after inspecting what is already available. The next implementation deliverable should be a downloadable Unity Editor package with a safe audit/preview-first workflow, not a vague architecture diagram.

Implementation priority:
1. Verify current repo state and read the master geography + hydrology data.
2. Inspect available code for `OmniverselMasterHydrologyData`, current terrain grid/layout, and Easy River package integration if files are available.
3. Design the terrain-carving algorithm carefully; ensure world-space coordinates and cross-tile writes are correct.
4. Provide preview + backup + apply/restore; no destructive heightmap edits without explicit Apply.
5. Test one river segment and report limitations honestly.
6. Preserve all existing accepted terrain and ocean objects.

Do not regenerate old accepted terrain tiles (especially original T00–T04). Do not redo the completed terrain seam repair without new evidence. Do not install paid tools unless the user changes the free-only preference. Do not implement Level 2 localized fluid simulation now.

## 12. Resume prompt (copy into the new chat)

You are continuing my active Unity project, **Omniversel Roleplay**, from the repository backup branch `backup/omniversel-river-builder-2026-10-09` in `PranaySardar-10/DEV-ROOM-TEST`. Read `WORLD/HYDROLOGY/OMNIVERSEL_PROCEDURAL_RIVER_BUILDER_CONTINUATION_2026-10-09.md` completely before replying.

Our goal is a professional, easy-to-use **custom procedural river generator** for our own 40-tile connected terrain. It must be able to carve its own channel at Editor time and create natural banks, shoreline transitions, a rough riverbed, and a water mesh that follows the route and downhill profile. It must work with our custom TerrainData and cross tile borders seamlessly. We already have master hydrology data and three solved routes in the backup. Our existing ocean surface is already in the scene at Y=0: never create a duplicate ocean. Do not run the old `Omniversel_HydrologyWaterGeometry_v1.zip` placeholder.

We want a mobile-friendly hybrid: terrain/meshes generated and baked in the Editor, animated water shader at runtime, and lightweight `OmniverselWaterBody` gameplay queries. No full-world fluid simulation and no Level 2 localized simulation for now. Keep Uber Stylized Water as our leading rendering candidate. Easy River is already installed and has a spline/control-point editor, but its terrain-carving and bank-generation abilities are not yet verified. Prefer free solutions and build our own integration where needed.

Do not replace accepted terrain tiles, reset terrain, redo successful seam repairs, or write destructive terrain changes without backup, preview, validation, and explicit Apply/Commit. Start by inspecting the repository and available Unity code/data, then create a real implementation deliverable rather than only explaining a plan. Be direct, accurate, and honest about what has and hasn't been tested.
