# Omniversel Roleplay — World Builder Continuation Backup
Date: 2026-10-03 (conversation closeout)
Repository: PranaySardar-10/DEV-ROOM-TEST
Backup branch: backup/omniversel-plateau-continuation-2026-10-01

## 1. Project identity and priority
Omniversel Roleplay is the MAIN project. The old DevRoom/local-agent work is historical/origin context, NOT the current game project and must not be mixed into the game-development state.
Current game target: Unity 6.3, mobile-first, open-world real-life/crime RP multiplayer, planned public release within 2027.
Current priority is the GAME first. The World Builder exists to build Omniversel's world; only after Omniversel is substantially complete should the Builder be generalized/upgraded commercially.
Do not redirect the project into a generic commercial world-builder right now.

## 2. World Builder philosophy
The Builder is deterministic code/algorithms, NOT an AI world designer.
Masterplan input + seed + registered assets + rules => deterministic world output.
Same inputs must reproduce the same world.
The masterplan must eventually be extremely detailed: regions, districts, terrain, roads, rivers, forests, vegetation, props, housing density, wealth, privacy, landscaping, landmarks, etc.
The Builder must execute the owner's explicit plan; it must not invent visual decisions like an AI.
The eventual Omniversel map should be larger than GTA V's map while remaining feasible on mobile through chunking, streaming, LODs, adaptive detail and aggressive optimization.
The architecture should avoid arbitrary hard-coded world-size limits. Physical limits still come from hardware, storage, generation time, GPU/CPU/RAM, precision and runtime constraints.
Long-term, after the game, the Builder could become a commercial world-generation product, potentially supporting vastly larger worlds, but this is NOT the current goal.

## 3. World structure currently planned
Initial world concept has 12 regions:
- 2 major cities
- 2 normal cities
- 2 very rich villages
- 2 rich villages
- 2 middle-class villages
- 2 poor villages
Each region should have deliberately different geography and environmental/prop/vegetation profiles.
The final masterplan will define these carefully rather than relying on randomness.

## 4. Interior architecture — LOCKED DECISION
World Builder has ZERO responsibility for interiors.
Every house exterior is part of the exterior world.
Interiors are separate scenes/templates loaded by a separate runtime interior system.
There must be no exterior visibility into the interior; windows/geometry are opaque/non-see-through as appropriate.
Entry is through a door interaction/entry point with property permission checking.
Concept:
Player -> DoorInteraction -> property accessible? -> load interior scene/template.
Suggested property data:
PropertyID
OwnerID
ExteriorAssetID
InteriorTemplateID
Position
DoorID
The Builder only needs exterior property metadata / entry point IDs. It must NOT generate rooms, furniture, interior lighting, or interior scene content.
This is intentional for mobile performance, database simplicity and scalable property reuse.

## 5. Housing wealth rules — LOCKED DESIGN DIRECTION
Poor housing:
- lower privacy
- no luxury fence/garden/pool requirement

Middle-class:
- medium privacy
- normal landscaping as defined by masterplan

Rich:
- high privacy
- perimeter fencing
- garden/landscaping
- attached/private pool

Very rich:
- very high privacy
- perimeter fencing
- garden/landscaping
- attached/private pool
- more luxurious lot/setback treatment

Fence, garden and pool assets are not all available yet. The Builder must support planned asset dependencies/placeholders for development/testing without substituting unrelated-region final assets.
When correct assets are acquired, register them by asset ID and let the rules place them.

## 6. Asset sourcing/licensing context
A RADMIR/RP asset reuse strategy was investigated and found unsafe under the published RADMIR terms without explicit permission. Their terms state game assets/materials belong to the copyright holder and restrict commercial sale/resale/distribution, modification and downloading outside intended function. Do NOT build the final commercial game around extracted RADMIR assets or attempt to evade licensing by topology/UV changes.
The current direction is to find legally usable, region-appropriate assets and/or hire a modeler later.
The Unity Asset Store “Country House FREE” asset was inspected as a possible source. It is free under the Asset Store EULA, published by A ALP, 269.9 MB, version 1.1, released Aug 11 2023, original Unity version 2019.4.34. It has village/country/rustic/Soviet-style tags. Do not infer rights beyond its actual EULA.

## 7. Asset pipeline — current Builder direction
DFF is intentionally NOT required.
The Builder should accept normal usable 3D source formats and normalize them into a common internal representation.
v0.7 asset-intake direction:
- FBX
- OBJ
- DAE
- DXF
- 3DS
- BLEND
- other common Unity-supported/imported source formats where the Unity project can actually import them
Do NOT claim GLB/GLTF support unless an actual importer/package is installed and tested.
DFF was excluded from the pipeline.
Core pipeline:
source model -> import adapter/intake -> normalization -> metadata -> LOD injection -> generated prefab -> asset registry -> world placement.
Internal asset representation should be source-format agnostic:
AssetID
SourceFormat
SourcePath
SourceObject
RuntimePrefab
LODProfile
Category
Tags
Bounds/material/mesh/collider metadata as needed.

## 8. LOD Injector — required core subsystem
LOD Injector is part of the Builder ecosystem.
It should:
- detect existing LODs
- generate missing LODs where possible
- create/configure LODGroup
- calculate bounds
- use class-aware LOD profiles
- enforce conservative triangle/material budgets
- cache processed unique source assets
- avoid regenerating LODs for every FCG instance
Example profiles:
House: full -> simplified -> low -> very distant
Tree: full -> simplified -> billboard/impostor where available
Fence/prop: fewer levels
Landmark: more detailed levels
LOD processing is source-asset based, then FCG/world instances reuse processed results.

## 9. FCG integration
Fantastic City Generator (FCG) remains a major city-generation core.
Omniversel World Builder is the world compiler/integration layer.
FCG source prefabs -> preprocess/cache unique meshes/LODs -> optimized prefab -> FCG instances reuse cached LOD assets.
World Builder must not be dependent on FCG for every world feature; it must be able to build non-FCG regions/features too.
FCG assets can be used commercially according to its license as long as they are integrated into a game/project and not redistributed as the asset package itself; verify exact license before any future redistribution feature.

## 10. Terrain / geography requirements
The Builder must generate actual terrain, not merely store terrain metadata.
Required terrain concepts:
- base elevation
- coastline lowering / coastal lowlands
- plains
- hills
- mountains / mountain ranges
- ridges
- valleys
- depressions
- plateaus
- explicit elevation zones with target elevation/radius/blend
- deterministic noise
Terrain and world dimensions must be separate from heightmap sampling density.
Use chunking and adaptive resolution rather than making every area maximally dense.
Unity TerrainData heightmap APIs are the intended runtime/editor mechanism.
Batch terrain height changes using SetHeightsDelayLOD where appropriate, then synchronize terrain LOD/vegetation once per batch rather than repeatedly.

## 11. Rivers, water and hydrology
Required water types include:
- river
- stream
- lake
- pond
- reservoir
- canal
- waterfall
- coast
Water is not just a visual spline. The Builder should eventually support terrain interaction:
river valley/carving
river bed depth
source elevation
mouth elevation
lake basin / closed polygon
bank falloff
coastline lowering
The water renderer itself can remain a separate system driven by water metadata.
Multiple water types are required; not only ocean.

## 12. Vegetation / forest system
Vegetation must be algorithmic and masterplan-controlled, not AI-selected.
Potential factors:
tree density
biome/region profile
elevation
slope
moisture
distance from roads
distance from buildings
water proximity
exclusion zones
deterministic noise
Different regions should have different forest/vegetation species and density profiles according to registered assets and rules.
Props likewise depend on:
region profile
district type
road type
terrain
wealth
population density
exclusion zones
seed
The masterplan should be detailed enough that a coastal city, mountain village, rich village, poor village, etc. have visibly and structurally distinct environments.

## 13. World size and streaming philosophy
The total authored world can be much larger than the simultaneously loaded runtime world.
World size should be user/masterplan-defined, not hard-coded to one fixed map.
Chunk grid should be derived from world dimensions and chunk size.
Example at 512m chunks:
100x100 chunks = 51.2km x 51.2km (~2621 km^2)
200x200 = 102.4km x 102.4km (~10486 km^2)
300x300 = 153.6km x 153.6km (~23593 km^2)
These are planning dimensions, not a claim that all chunks are loaded simultaneously.
Runtime:
master world -> chunk database/content -> streaming -> only nearby/needed chunks loaded.
Mobile performance depends heavily on active loaded area, visible geometry, textures, GPU/VRAM, CPU, RAM, storage, network and simulation.
The Builder should not use the current development PC as the hard maximum.
Very large worlds will eventually require precision/origin management; do not ignore floating-point precision at extreme coordinates.

## 14. World Builder data architecture
Target pipeline:
Masterplan (.ovworld)
 -> parser
 -> validator
 -> deterministic WorldPlan
 -> terrain/geography
 -> water
 -> roads
 -> lots/districts
 -> exterior buildings
 -> vegetation
 -> props
 -> LOD/optimization
 -> chunk output
 -> runtime streaming
Interiors are not in this pipeline.

Expected data concepts:
WorldPlan
RegionDefinition
ChunkDefinition
AssetReference
PlacementRule
GenerationSeed
WorldValidationResult
The .ovworld should describe regions/chunks/rules/assets, not interior scenes.

## 15. Builder versions built during this conversation
v0.5:
- initial World Builder package
- .ovworld masterplan save/load
- 12-region skeleton
- region/chunk editing
- deterministic master seed
- road/water rules and points
- housing placement rules
- explicit asset placement
- generic generation rules
- validation
- preview generation
- placeholders for testing
- no interior handling

v0.6:
- terrain/hydrology layer started
- elevation/base terrain concepts
- coast, hills, mountains, ridges, plateaus/depressions
- river/stream/canal/waterfall metadata and terrain interaction direction
- vegetation/forest direction
- LOD injector integration direction

v0.6.1:
- fixed four GameObject/Transform type mismatches in OmniverselWorldCompiler.cs and OmniverselVegetationGenerator.cs
- package was then tested in Unity context

v0.7:
- asset intake expanded beyond prefabs
- common model source formats supported through Unity import pipeline
- DFF removed from requirements
- source -> normalized prefab -> registry/LOD pipeline
IMPORTANT CURRENT TEST RESULT: user reported ZERO ERRORS in their actual Unity 6.3 project after v0.7.

v0.8:
- terrain generation expanded
- coast lowlands
- plains/hills/mountains
- mountain-zone masks
- valleys/depressions
- explicit elevation zones
- deterministic noise
- rivers with source/mouth/valley carving concepts
- streams/canals/waterfalls
- lakes/basins
- coastline lowering
IMPORTANT: v0.8 has NOT yet been confirmed clean in the user's actual Unity 6.3 project. Next task is to import/test/compile v0.8 before adding another major subsystem.

## 16. Current exact next step
Do NOT jump into designing the final masterplan yet.
First:
1. Put v0.8 into the actual Unity 6.3 Omniversel project.
2. Compile.
3. Fix every Unity-side error/warning that blocks use.
4. Test a small terrain (e.g. 129 heightmap resolution).
5. Verify coastline, mountains/hills, river carving, lake basin, and deterministic regeneration.
6. Verify LOD/asset intake remains intact.
7. Only after this is clean, continue with the next Builder subsystem.
Then we can begin the actual detailed Omniversel masterplan: geography -> regions -> cities/villages -> districts -> roads -> forests -> vegetation -> props -> housing wealth/privacy -> landmarks -> streaming/optimization.

## 17. Current Unity/project facts
Current project editor is Unity 6.3. Unity 6.6 was abandoned; do not resurrect it.
Current project location historically used:
D:\OMNIVERSEL ROLEPLAY\OMNIVERSEL ROLEPLAY
Development machine:
Intel i5-2400
16 GB DDR3
Intel HD 2000
512 GB SATA SSD
Windows 11 Home
The Builder must be architected for the final mobile target, not optimized only for this development PC.

## 18. Critical conversation continuity warning
The old DevRoom project was SCRAPPED/HISTORICAL context. It must not be treated as the current game architecture.
Do not confuse DevRoom factory branches/local Ollama work with Omniversel World Builder implementation.
Do not mix old Unity 6.6 references into current project state.
Do not reintroduce RADMIR/DFF asset plans as the final asset strategy.
Do not move interior generation into the World Builder.
Do not make the Builder AI-driven.
Do not start commercial Builder work before Omniversel game/world is substantially built.

## 19. Ready-to-paste continuation prompt
CONTINUE OMNIVERSEL ROLEPLAY FROM THE WORLD BUILDER BACKUP EXACTLY.

Omniversel Roleplay is the main project. The old DevRoom/local-agent project is historical origin context only and was scrapped; do not mix it with current game development.

Current editor: Unity 6.3. Current project: D:\OMNIVERSEL ROLEPLAY\OMNIVERSEL ROLEPLAY.
Goal: build a mobile-first open-world real-life/crime RP multiplayer game, public release target within 2027.
Current immediate priority: finish the World Builder and then create the detailed Omniversel masterplan. The game comes first; commercial/general-purpose Builder upgrades are future work.

World Builder philosophy:
- deterministic code and algorithms, NOT AI decision-making
- masterplan + seed + registered assets + rules -> deterministic world
- same input must reproduce the same world
- no arbitrary fixed world-size ceiling in the architecture
- total authored world can be huge, but runtime uses chunk streaming and only loads active/needed areas
- target Omniversel map is larger than GTA V's map but must remain feasible on mobile
- eventually handle large worlds through chunking, LODs, adaptive terrain, streaming, asset caching and precision/origin strategy

Current Builder pipeline:
.ovworld -> parser -> validator -> deterministic WorldPlan -> terrain/geography -> water -> roads -> lots/districts -> exterior buildings -> vegetation -> props -> LOD/optimization -> chunk output -> runtime streaming.

Interiors are completely outside the Builder:
- exterior house only in world
- door/entry point + property metadata
- permission check
- separate interior scene/template loaded by separate runtime interior system
- no outside visibility into interior
- Builder never generates rooms/furniture/interior lighting

Housing wealth rules:
- poor: low privacy, no luxury fence/garden/pool requirement
- middle: medium privacy
- rich: high privacy + fence + garden + attached/private pool
- very rich: very high privacy + fence + garden + attached/private pool + more luxury/setback
Correct region-appropriate assets are important; do not substitute unrelated assets just to make generation work.

Asset strategy:
- DFF is NOT required.
- Accept common Unity-importable source models such as FBX/OBJ/DAE/DXF/3DS/BLEND and other formats only when actual import support exists.
- Source -> intake -> normalization -> metadata -> LOD injector -> generated prefab -> registry -> placement.
- Asset source format must not matter to the World Builder after normalization.
- LOD Injector is a core subsystem with class-aware profiles and unique-source caching.
- FCG remains a major city-generation core and its unique-source LOD cache strategy is retained.
- RADMIR extracted assets are not the final strategy because published terms restrict use; do not evade licensing.

Terrain/hydrology already implemented in v0.8:
- coast lowlands
- plains
- hills
- mountains/ranges
- ridges
- plateaus/depressions
- valleys
- explicit elevation zones
- deterministic noise
- rivers/streams/canals/waterfalls
- river source/mouth/valley-carving concepts
- lakes/basins
- coastline lowering
Need to test v0.8 in actual Unity 6.3 next. v0.7 was confirmed by user as ZERO ERRORS in their actual Unity project.

Versions:
v0.5 initial Builder
v0.6 terrain/hydrology foundation
v0.6.1 compiler type fixes
v0.7 multi-format asset intake + DFF removed; user confirmed zero errors
v0.8 expanded actual terrain/hydrology; not yet user-confirmed clean

EXACT NEXT ACTION:
Import v0.8 into the actual Unity 6.3 project, compile, test a small 129-heightmap terrain, verify coast/mountains/hills/rivers/lakes/deterministic regeneration, and fix any errors before adding more systems. Do not jump to masterplan design until the Builder layer is clean.

After Builder foundation is stable, begin detailed Omniversel masterplan design:
- world dimensions/chunks
- geography
- 12 initial regions (2 major cities, 2 normal cities, 2 very rich villages, 2 rich villages, 2 middle-class villages, 2 poor villages)
- terrain profiles
- rivers/lakes/coast
- roads/highways/rail
- districts
- lots
- building density
- forests/biomes/vegetation
- region-specific props
- wealth/landscaping/privacy
- landmarks
- streaming/LOD/optimization
The masterplan must be extremely detailed because the Builder is deterministic code, not AI.

Never confuse this with the old DevRoom project. Continue from this exact state.
