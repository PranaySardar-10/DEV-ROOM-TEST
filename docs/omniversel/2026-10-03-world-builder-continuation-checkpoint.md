# Omniversel Roleplay — World Builder Continuation Checkpoint
Date: 2026-10-03

MAIN PRIORITY
Main goal is Omniversel Roleplay first, not commercializing the Builder yet. The Builder exists to make Omniversel's world/masterplan a masterpiece. Future commercial/general-purpose Builder ambitions come only after the game.

PROJECT
- Unity 6.3; mobile-first open-world real-life/crime RP multiplayer.
- Public release target within 2027.
- World should be larger than GTA V's map.
- Builder must not impose an arbitrary fixed world-size ceiling. Practical limits come from hardware, storage, runtime, precision, generation time and platform constraints.
- Total authored world may be huge while runtime loads only active/nearby chunks.
- Development PC: i5-2400, 16 GB DDR3, Intel HD 2000, 512 GB SATA SSD; optimization is critical.

MASTERPLAN
- Initial regions: 2 major cities, 2 normal cities, 2 very rich villages, 2 rich villages, 2 middle-class villages, 2 poor villages, with varied geography.
- Masterplan must be extremely detailed and deterministic. Builder is code/algorithm driven, not AI driven.
- Same masterplan plus seed should produce the same result.
- Regional rules control terrain, districts, roads, lots, buildings, density, housing wealth, forests, vegetation, props, water, landmarks and optimization.
- Use region-appropriate assets; do not substitute unrelated regional assets just to unblock generation.

INTERIORS
- World Builder has ZERO responsibility for interiors.
- Exterior houses are placed in the world; interiors are separate scenes/templates and runtime systems.
- Door interaction checks property access and loads the permitted interior.
- No outside visibility through interior geometry and no arbitrary window/geometry entry.
- Builder only needs property/exterior metadata such as PropertyID, OwnerID, ExteriorAssetID, Door/EntryPoint ID and InteriorTemplateID.
- Housing wealth: poor = low privacy; middle = moderate; rich = higher privacy plus fences/gardens/attached pools; very rich = highest privacy/luxury plus fences/gardens/attached pools.
- Missing final luxury assets must not force unrelated substitutes; preview placeholders are acceptable, production validates missing dependencies.

ASSET PIPELINE
- Accept common non-DFF sources: FBX, OBJ, DAE, 3DS, BLEND and other formats only when an actual tested Unity importer exists.
- DFF is explicitly NOT required going forward.
- Pipeline: source model -> importer/intake adapter -> normalization -> metadata -> collision/validation -> LOD Injector -> standardized prefab -> Asset Registry -> World Builder.
- World Builder places stable AssetIDs and does not care about source format.
- Registry stores AssetID, source format/path, runtime prefab, category/subcategory, bounds, meshes/materials, collider information, LOD profile, region/biome/wealth tags and generation metadata.
- Cache processing per unique source.

LOD INJECTOR
- Dedicated preprocessing stage.
- Detect existing LODs, generate missing LODs, configure LODGroup, calculate bounds, use class-aware profiles, cache simplified meshes and validate triangle/material limits.
- Different classes may have different LOD profiles: houses, trees, fences, props, roads, landmarks, etc.

TERRAIN AND HYDROLOGY
- Terrain generation is part of Builder.
- Capabilities: coastline lowering, plains, hills, mountains, mountain ranges/ridges, valleys, plateaus, depressions, explicit elevation zones, deterministic noise and slope analysis.
- Hydrology: rivers, streams, canals, waterfalls, lakes, ponds/reservoirs, coastlines, river valley carving, lake/pond basins, configurable water surface/elevation and bed depth.
- Physical terrain dimensions and heightmap sampling remain separate so huge worlds do not require maximum resolution everywhere.

VEGETATION AND PROPS
- Forest/vegetation placement is deterministic and rule based.
- Factors can include biome/region, elevation, slope, moisture, road distance, building distance, deterministic noise and exclusion zones.
- Props depend on region, district, road type, wealth, terrain, density and explicit masterplan rules.

WORLD SIZE AND STREAMING
- World is chunk based; 512 x 512 world units was the default conceptual chunk size discussed, but it should become configurable.
- World dimensions are user-defined and Builder calculates the chunk grid.
- Total authored world can exceed what the development PC can load.
- Runtime streaming loads only relevant nearby chunks.
- CPU, RAM, GPU/VRAM, storage, assets, network/server and streaming design all affect practical scale.
- Do not make the current development PC a hard maximum.
- Large-world precision/origin strategy must eventually be addressed.

BUILDER ARCHITECTURE
MASTERPLAN -> .ovworld -> parser -> validator -> deterministic WorldPlan -> terrain/surface -> water/hydrology -> roads/districts/lots -> exterior buildings -> vegetation -> props -> LOD/optimization -> world chunks/output.

VERSION STATUS
- v0.5: World Builder foundation.
- v0.6: terrain/geography and hydrology layer.
- v0.6.1: fixed four GameObject/Transform compile mismatches.
- v0.7: common non-DFF asset intake, standardized prefab/registry/LOD pipeline. User tested v0.7 in actual Unity 6.3 and reported ZERO ERRORS.
- v0.8: expanded elevation/mountains/valleys/rivers/lakes terrain generation. Package delivered; actual Unity 6.3 test result not yet reported. Initial test recommendation: 129 heightmap resolution.

DEVROOM
Repository: PranaySardar-10/DEV-ROOM-TEST
CONTINUING BRANCH: devroom/factory-production-workflow
Do NOT create a new branch unless the user explicitly requests it.
Factory architecture: ChatGPT architecture/coding -> Human Review -> constrained Implementer -> QA -> Unity validation.
Prior facts: 143 tests / 0 failures/errors before successful foundation run; do not merge PR #5; meaningful milestones need detailed checkpoints/backups; preferred local model was gemma4:e4b; earlier runner issue involved old 600-second timeout vs PR #7 hardened 1800-second stall-aware runner.

FCG
Fantastic City Generator remains the city-generation core; Omniversel is the world compiler/integration layer. FCG assets can be used commercially as part of a game under its license, but not redistributed/resold as standalone assets; verify the current project license before distribution.

LICENSING
RADMIR/RADMIR RP assets were investigated but are NOT the final licensing strategy. Published RADMIR terms restrict commercial use/distribution/modification/downloading of their Materials without permission. Do not use RADMIR assets as a core commercial source without explicit permission. Prefer legally usable/licensed/original region-appropriate assets.

TOOLS / PREVIOUS WORK
- Blender 5.2.2 LTS runs through Mesa3D software OpenGL due Intel HD 2000 limitations.
- DragonFF, Quick Mesh Cleanup+ and Tidy Monkey were installed for prior GTA/CRMP experiments, but DFF is no longer part of the Builder requirement.
- Old CRMP/RADMIR extraction experiments are not the final asset strategy.

IMMEDIATE NEXT STEPS
1. Test v0.8 in actual Unity 6.3 and fix compile/runtime issues.
2. Strengthen terrain and hydrology.
3. Add deterministic biome/forest/vegetation distribution.
4. Add region-aware prop distribution.
5. Add roads/districts/lots generation.
6. Build chunk streaming/output architecture.
7. End-to-end validate Builder.
8. Only then author the detailed Omniversel masterplan.
9. Continue the rest of the game systems in parallel; the map is one major subsystem, not the whole game.

RESTART PROMPT
You are continuing Omniversel Roleplay from the 2026-10-03 checkpoint. Treat this checkpoint as authoritative for the current World Builder state. Main goal is to build Omniversel Roleplay first; do not redirect toward commercializing the Builder yet. Continue on the existing devroom/factory-production-workflow branch; never create a new branch unless explicitly requested. v0.7 compiled with zero errors in the user's Unity 6.3 project. v0.8 has been delivered but still needs actual Unity 6.3 testing. Continue from terrain/elevation/hydrology, then vegetation/forests, region-specific props, roads/districts/lots, chunk streaming, validation, and only then detailed masterplan authoring. Interiors are completely outside the Builder. Asset intake is common-format and DFF-free. Preserve deterministic generation, asset caching, LOD injection, region-specific asset correctness, mobile optimization, and eventual very-large-world capability without an arbitrary Builder-imposed world-size ceiling.