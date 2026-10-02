CONTINUE OMNIVERSEL ROLEPLAY FROM THE SAVED WORLD BUILDER BACKUP.

Read this backup first:
docs/backups/OMNIVERSEL_WORLD_BUILDER_CONTINUATION_2026-10-03.md

Do NOT mix this with the old DevRoom project. DevRoom/local Ollama work is historical/scrapped origin context only.

CURRENT PROJECT:
- Omniversel Roleplay
- Unity 6.3
- mobile-first open-world real-life/crime RP multiplayer
- target public release within 2027
- project path historically: D:\OMNIVERSEL ROLEPLAY\OMNIVERSEL ROLEPLAY

CURRENT PRIORITY:
Build the game first. The World Builder is currently being built specifically to make Omniversel's world. Do not turn this into a commercial/general-purpose Builder project yet. Commercialization is future work after the game/world is substantially complete.

WORLD BUILDER CORE:
Deterministic code/algorithms only, NOT AI world design.
Masterplan + seed + asset registry + rules -> deterministic world.
Same input must reproduce the same world.
No arbitrary hard-coded world-size ceiling.
Runtime must use chunks/streaming/LOD/adaptive detail so a huge authored world can still run on mobile.

LOCKED INTERIOR ARCHITECTURE:
World Builder has ZERO responsibility for interiors.
Only exterior houses are generated in the world.
Door/entry point + property metadata leads to a separate runtime interior system.
Interior scenes/templates are loaded separately when appropriate.
No outside visibility into interiors.
Do not add rooms, furniture, interior lights or interior scene generation to World Builder.

HOUSING RULES:
Poor = lower privacy.
Middle = medium privacy.
Rich = high privacy + fences + gardens + attached/private pools.
Very rich = very high privacy + fences + gardens + attached/private pools + larger setbacks/luxury landscaping.
Correct regional assets matter. Do not substitute unrelated final assets merely to unblock generation.

ASSET PIPELINE:
DFF is NOT required.
Support common Unity-importable model sources such as FBX, OBJ, DAE, DXF, 3DS, BLEND and any other format only when actual import support exists.
Source -> intake -> normalization -> metadata -> LOD Injector -> generated prefab -> registry -> world placement.
World Builder should not care what source format produced an asset.
LOD Injector is core and must use class-aware profiles plus unique-source caching.
FCG remains a major city-generation core.

CURRENT BUILDER VERSIONS:
v0.5 = initial .ovworld/masterplan/region/chunk/rule/validation/preview foundation.
v0.6 = terrain/hydrology foundation.
v0.6.1 = GameObject/Transform compile fixes.
v0.7 = multi-format asset intake; DFF removed; USER CONFIRMED ZERO ERRORS in actual Unity 6.3 project.
v0.8 = expanded terrain/hydrology: coast lowlands, plains, hills, mountains/ranges, ridges, plateaus/depressions, valleys, elevation zones, deterministic noise, rivers/streams/canals/waterfalls, lakes/basins, coastline lowering.
IMPORTANT: v0.8 has NOT YET been confirmed clean in the user's actual Unity 6.3 project.

IMMEDIATE NEXT TASK:
1. Import v0.8 into actual Unity 6.3 project.
2. Compile.
3. Fix every blocking Unity error.
4. Test small terrain, starting at 129 heightmap resolution.
5. Verify coast, hills, mountains, valleys, river carving, lake basin and deterministic regeneration.
6. Ensure asset intake and LOD functionality remain intact.
7. Only after clean validation continue adding major Builder systems.

DO NOT START FINAL MASTERPLAN DESIGN YET. Build the bed first.

WHEN BUILDER FOUNDATION IS STABLE, MASTERPLAN WILL BE EXTREMELY DETAILED:
- world dimensions/chunks
- geography
- 12 initial regions: 2 major cities, 2 normal cities, 2 very rich villages, 2 rich villages, 2 middle-class villages, 2 poor villages
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

The Omniversel map should be larger than GTA V's map while being engineered for mobile through aggressive streaming and optimization.

CRITICAL CONTINUITY RULES:
- Current Unity is 6.3, not 6.6.
- DevRoom is not the current game architecture.
- Do not reintroduce RADMIR/DFF as the final asset strategy.
- Do not put interiors into World Builder.
- Do not make Builder decisions AI-driven.
- Do not jump into commercial Builder work now.
