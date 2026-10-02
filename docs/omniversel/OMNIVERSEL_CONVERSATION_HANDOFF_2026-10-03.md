# Omniversel Roleplay — Conversation Handoff Backup
## 2026-10-03 — Final checkpoint of conversation

This document is the authoritative handoff for continuing the Omniversel Roleplay world-building work after the conversation limit.

## 1. PROJECT IDENTITY

Project: Omniversel Roleplay

Primary goal: build the game first. The World Builder is being developed specifically to make Omniversel's world/map a masterpiece. A future commercial/general-purpose World Builder is a later goal, not the current project priority.

Engine: Unity 6.3 (the active project/editor; Unity 6.6 was abandoned).

Project location:
D:\OMNIVERSEL ROLEPLAY\OMNIVERSEL ROLEPLAY

Target:
- Mobile-first open-world real-life/crime RP multiplayer game.
- Public release target is within 2027.
- The map is intended to be larger than GTA V's map.
- Despite the large world, the runtime must remain practical for mobile through aggressive streaming, LODs, asset optimization, chunking, and selective loading.
- The Builder itself should not impose an arbitrary small world-size ceiling. World size should be constrained by actual hardware/storage/runtime/precision limits rather than a hardcoded artificial maximum.
- Long-term dream: after Omniversel is built, the Builder architecture may evolve into a commercial world-generation product, potentially capable of extremely large/custom worlds. Do NOT let that future goal distract from building Omniversel now.

## 2. CRITICAL ARCHITECTURAL PRINCIPLE

World Builder is deterministic code + algorithms, NOT an AI deciding world placement.

Masterplan -> deterministic rules/seed -> World Builder -> reproducible world.

Same masterplan + same seed should produce the same result.

The masterplan will eventually be extremely detailed:
- region geography
- terrain
- elevation
- mountains
- hills
- valleys
- coastlines
- rivers/streams/lakes/canals
- forests and biome/ecology rules
- roads
- districts
- lots
- buildings
- vegetation
- props
- wealth-specific landscaping
- density
- exclusion zones
- regional asset categories
- chunking/streaming
- LOD profiles

Do not rush into the final masterplan until the Builder can actually execute the required systems.

## 3. INTERIOR ARCHITECTURE — LOCKED DECISION

World Builder has ZERO responsibility for interiors.

Exterior houses are world objects only:
- exterior shell
- roof
- windows/exterior details
- collision
- LODs
- door/entry point
- property metadata

Interiors are separate runtime scenes/templates.

Interaction:
Player -> Door -> permission/property check -> load interior if allowed.

Interiors are loaded only as needed and are kept out of the exterior world visibility path. There is no intended ability to see through the exterior into an interior, and no arbitrary window-entry system.

Builder should NOT generate rooms, furniture, interior lighting, interior geometry, etc.

Example property metadata:
PropertyID
OwnerID
ExteriorAssetID
InteriorTemplateID
Position
DoorID

Many houses may reuse interior templates.

## 4. HOUSING / WEALTH RULES

The world will contain:
- 2 major cities
- 2 normal cities
- 2 very rich villages
- 2 rich villages
- 2 middle-class villages
- 2 poor villages

Very rich/rich housing needs eventually:
- privacy-oriented setbacks
- fences
- gardens/landscaping
- attached pools
- luxury exterior features

Poor housing should NOT automatically receive those luxury privacy/landscaping features.

These should be deterministic wealth/region rules, not random decoration.

Important current asset reality:
We do not yet have final rich/very-rich housing assets, fences, gardens, and pools. Builder must therefore support planned asset dependencies/placeholders without redesigning the generator. Do not substitute unrelated-region assets merely to make the Builder work.

## 5. ASSET PIPELINE — CURRENT DIRECTION

The Builder should accept common model sources rather than requiring hand-made Unity prefabs.

Current direction:
FBX / OBJ / DAE / 3DS / other normal Unity-supported model sources -> intake -> normalization -> prefab -> LOD -> registry -> world placement.

DFF is NOT required. We explicitly decided not to build DFF support into the Builder.

The internal Builder representation should be source-format agnostic:
AssetID
SourceFormat
SourcePath
Category
SubCategory
Bounds
Materials
Meshes
Colliders
LODProfile
RegionTags
WealthTags
BiomeTags
Metadata
PrefabPath

World Builder should only care about AssetID after registration.

Asset preprocessing goals:
- automatic metadata extraction
- categorization
- bounds
- materials
- collision metadata
- LOD processing
- cached processed assets
- no per-asset human approval

Important optimization principle:
FCG may create thousands of instances, but identical source assets should share processed mesh/LOD data through a unique-source cache. Do NOT regenerate LODs for every placed instance.

## 6. LOD INJECTOR — REQUIRED SYSTEM

LOD Injector is part of the Builder pipeline.

Pipeline:
Source asset -> import/normalize -> LOD Injector -> optimized prefab -> Asset Registry -> World Builder.

LOD Injector responsibilities:
- detect existing LODs
- generate missing LODs where appropriate
- create/configure LODGroup
- calculate bounds
- use class-aware profiles
- validate triangle/material limits
- cache processed results

Different classes need different LOD profiles:
House, tree, fence, road prop, landmark, etc. do not need identical numbers of LODs.

## 7. TERRAIN / HYDROLOGY — CURRENT BUILDER DIRECTION

Terrain must be real generation, not just metadata.

Required:
- base elevation
- coastline lowering
- plains
- hills
- mountain ranges
- ridges
- plateaus
- valleys/depressions
- explicit elevation zones
- deterministic noise
- slope analysis
- river valleys
- lake basins

Hydrology:
- rivers
- streams
- canals
- waterfalls
- lakes
- ponds/reservoirs
- coast

Rivers must be capable of affecting terrain rather than merely being lines.

Terrain should use batched heightmap operations for performance.

The Builder should keep physical world dimensions separate from heightmap sampling density.

## 8. VEGETATION / FOREST / REGIONAL PROPS

These are algorithmic systems.

Example conceptual forest density:
region forest profile
x elevation factor
x slope factor
x moisture factor
x distance-from-road
x distance-from-building
x deterministic noise

Props should depend on:
region profile
district type
road type
terrain
wealth
population density
exclusion zones
seed

The final masterplan must carefully define regional differences. The Builder must execute those rules exactly; it must not improvise like an AI.

## 9. WORLD SIZE / CHUNKING

The world is intended to be larger than GTA V's map.

World size should be user-defined at the data level, while runtime loading is limited to active/nearby chunks.

Concept:
TOTAL WORLD -> world data/chunks -> streaming -> active area -> player device.

CPU:
- generation speed
- streaming work
- simulation/physics/AI

RAM:
- loaded terrain/assets/chunks

GPU/VRAM:
- visible geometry
- textures
- effects
- shadows

Storage:
- total world/asset data

Assets:
- affect total and runtime memory

Streaming:
- major factor in playable world scale

The Builder must not be hardcoded around the developer PC (i5-2400, 16 GB RAM, Intel HD 2000). That machine is a development bottleneck, not the game's theoretical world-size ceiling.

Very large worlds will eventually need an origin/precision strategy.

## 10. FCG

Fantastic City Generator (FCG) is part of the world-generation ecosystem and is the city-generation core/integration source.

Omniversel World Builder is the world compiler/integration layer.

World plan .ovworld describes regions/chunks/rules/assets.

FCG source prefabs -> preprocess/cache unique mesh LODs -> optimized prefab -> FCG instances share processed assets.

FCG license allows commercial use of its assets as part of a game/project, but does not allow redistribution/resale of the FCG assets themselves. Preserve this distinction.

## 11. WATER / TERRAIN RELATED HISTORY

Earlier tests included PLATEAU terrain data and water systems. Water architecture should eventually support multiple water types rather than assuming only ocean.

Possible water metadata/categories:
ocean, coast, river, stream, lake, pond, reservoir, canal, waterfall.

## 12. ASSET LICENSING — IMPORTANT

RADMIR/RADMiR assets were investigated but should NOT be treated as a safe final commercial asset source without explicit permission.

The published RADMIR terms state restrictions around commercial use, redistribution, modification, and downloading/using Materials outside intended game use. The project therefore moved toward finding properly licensed/regional assets instead of building its commercial strategy around extracted RADMIR assets.

Do not advise evading licensing by changing topology/UV/metadata. A modified derivative is not automatically free of the original rights issue.

The current asset strategy is to continue searching for legally usable, region-appropriate assets while Builder development continues independently.

## 13. BLENDER / ASSET TOOLING HISTORY

Blender 5.2.2 LTS is installed and was made runnable on the old Intel HD 2000 machine using Mesa3D software OpenGL.

Installed/used:
- DragonFF
- Quick Mesh Cleanup+
- Tidy Monkey

DFF tooling is no longer required for the World Builder because DFF support was dropped from the intended Builder asset pipeline.

## 14. BUILDER VERSION HISTORY IN THIS CONVERSATION

v0.5:
- initial actual World Builder foundation
- .ovworld masterplan save/load
- region/chunk data
- deterministic seed
- road/water rules
- housing rules
- explicit placement
- validation
- preview generation
- no interiors

v0.6:
- terrain/hydrology layer
- intended terrain generation, mountains, rivers, lakes etc.
- LOD direction

v0.6.1:
- fixed Unity compile issues involving GameObject/Transform mismatches
- actual project testing continued

v0.7:
- multi-format asset intake
- common model-source ingestion
- prefab generation/registry
- LOD integration
- DFF deliberately excluded
- User tested v0.7 in actual Unity 6.3 project and reported ZERO ERRORS.

v0.8:
- expanded terrain generation/hydrology:
  coastline lowlands
  plains
  hills
  mountains
  mountain-zone masking
  valleys/depressions
  explicit elevation zones
  mountain/hill/plateau features
  deterministic noise
  rivers/streams/canals/waterfalls
  lakes/basins
- v0.8 package was delivered but actual Unity 6.3 compile/test result for v0.8 was not yet reported at the end of this conversation.

IMPORTANT: Do not claim v0.8 is compile-clean until the user confirms it in Unity.

## 15. CURRENT EXACT STATE

Last confirmed state:
- Unity project is compiling cleanly with v0.7.
- User said: "zero error".
- v0.8 has been generated and handed to the user.
- v0.8 has NOT yet been confirmed by the user as compile-clean.
- The next immediate step is to test v0.8 in the actual Unity 6.3 project.
- Do not start final masterplan design until the Builder's core systems are sufficiently real and tested.

## 16. IMMEDIATE NEXT WORK

1. User tests v0.8 in Unity 6.3.
2. Fix all compile/runtime issues found.
3. Test actual terrain generation.
4. Test coast/elevation/mountain generation.
5. Test river/lake terrain interaction.
6. Test vegetation/forest rule generation.
7. Test asset intake with real FBX/OBJ/etc.
8. Test LOD injection on real assets.
9. Test deterministic regeneration.
10. Test chunk generation and world-scale data handling.
11. Continue building missing Builder systems.
12. Only after the machine is solid, begin the detailed Omniversel masterplan.

## 17. MASTERPLAN DESIGN ORDER WHEN WE REACH IT

Do NOT jump directly to houses.

Design in this order:
1. macro world dimensions
2. geography/terrain
3. coastlines/water bodies
4. mountain ranges/hills/valleys
5. major rivers
6. regional biome/ecology
7. 12 regions
8. cities/villages
9. district boundaries
10. road/highway hierarchy
11. lots
12. housing/commercial/industrial distribution
13. vegetation
14. region-specific props
15. wealth-specific landscaping
16. landmarks
17. streaming/chunk rules
18. asset assignment
19. validation/performance budgets

## 18. DO NOT CONFUSE THESE PROJECTS

DEV-ROOM was an older/scrapped orchestration project and is NOT the current game project.

Its historical role:
- factory workflow
- local model routing
- architecture/coding/QA orchestration
- Git backup history

Do not interpret old DevRoom details as the current game architecture.

Current game project:
Omniversel Roleplay in Unity 6.3.

## 19. BACKUP POLICY

User explicitly wants meaningful milestones backed up.

Use an existing continuation/backup branch when possible.
Do NOT create a new branch for every conversation.
For this checkpoint, use:
backup/omniversel-plateau-continuation-2026-10-01

Other existing backup branches:
backup/memory-for-project-2026-09-24
backup/omniversel-plateau-continuation-2026-10-01
backup/omniversel-plateau-world-foundation-2026-10-01
backup/starting-memory-game-development-2026-09-24

## 20. READY-MADE CONTINUATION PROMPT

Paste this at the start of the next conversation:

"Continue Omniversel Roleplay World Builder from the 2026-10-03 handoff checkpoint. Treat the attached/linked backup document as authoritative context.

We are building Omniversel Roleplay first, not a commercial generic Builder yet. The Builder exists specifically to make Omniversel's world/map a masterpiece. Omniversel is a Unity 6.3 mobile-first open-world multiplayer real-life/crime RP game planned for release within 2027, with a world intended to be larger than GTA V's map. Runtime must remain mobile-capable through chunk streaming, LODs, aggressive optimization, and selective loading.

The World Builder is deterministic code/algorithms, NOT an AI deciding placement. Masterplan + seed -> reproducible world.

Interior architecture is completely outside the World Builder. Exterior buildings only contain shell/roof/windows/collision/LODs/door-entry metadata. Interiors are separate scenes/templates loaded through the property/door system. Never add interior generation to the Builder.

The world plan eventually has 12 initial regions: 2 major cities, 2 normal cities, 2 very rich villages, 2 rich villages, 2 middle-class villages, 2 poor villages, with varied geography. Rich/very-rich housing eventually needs fences, gardens/landscaping, attached pools and greater privacy; poor housing should not receive those luxury features automatically.

Asset pipeline is format-agnostic. We want common model sources such as FBX/OBJ/DAE/3DS/etc. -> intake -> normalization -> standardized prefab -> LOD Injector -> Asset Registry -> World Builder. DFF is NOT required. Identical source assets must use cached processed meshes/LODs rather than regenerating per instance.

LOD Injector is a core subsystem. Use class-aware LOD profiles and persistent caching.

Terrain must be real generation, not just metadata: coastline lowering, elevation zones, plains, hills, mountains, ridges, plateaus, valleys/depressions, deterministic noise, slope analysis, rivers/streams/canals/waterfalls/lakes and terrain interaction.

Forests/vegetation/props must be algorithmic and masterplan-driven using region, biome, elevation, slope, moisture, road/building distance, wealth, district type, exclusion zones and deterministic seed.

The Builder must not have an arbitrary tiny world-size limit. Total world can be huge in data, while runtime loads only active chunks. However, do not claim infinite worlds; actual hardware/storage/runtime/precision impose physical limits. The architecture should separate world dimensions, chunk size and terrain sampling density and eventually include a precision/origin strategy.

FCG is the city-generation core/source. Omniversel World Builder is the world compiler/integration layer. .ovworld stores world regions/chunks/rules/assets. FCG source prefabs should be preprocessed/cached so instances share optimized LOD assets.

RADMIR assets were investigated but are not the safe final commercial source without explicit permission. Do not advise license evasion. We are continuing to search for properly licensed, region-appropriate assets in parallel.

Version state:
v0.5 = initial Builder foundation.
v0.6 = terrain/hydrology layer.
v0.6.1 = compile fixes.
v0.7 = multi-format asset intake/registry/prefab/LOD pipeline; USER TESTED V0.7 IN UNITY 6.3 AND CONFIRMED ZERO ERRORS.
v0.8 = expanded terrain/hydrology implementation; delivered but NOT YET CONFIRMED CLEAN BY USER.

Immediate task: have the user test v0.8 in Unity 6.3. Fix compile/runtime issues first. Then continue building the actual terrain, hydrology, vegetation, LOD, chunking and deterministic-generation systems. Do not jump into the final masterplan until the Builder is genuinely capable of executing it.

Use the existing continuation branch backup/omniversel-plateau-continuation-2026-10-01. Do not create a new branch unless explicitly requested.

When the Builder is ready, design the Omniversel masterplan carefully in this order: macro dimensions -> geography -> coast/water -> mountains/hills/valleys -> major rivers -> biome/ecology -> 12 regions -> cities/villages -> districts -> road hierarchy -> lots -> buildings -> vegetation -> props -> wealth landscaping -> landmarks -> streaming/chunk rules -> asset assignment -> validation/performance budgets.

Do not confuse the old DEV-ROOM orchestration project with the current Omniversel Unity project."

## 21. CONTINUATION RULE

The next conversation must begin from the exact Builder state above. Do not restart the architecture, do not re-propose interiors, do not reintroduce DFF, do not replace the deterministic Builder with AI generation, and do not jump back to the old DevRoom project.
