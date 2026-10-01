# Omniversel Roleplay — Full Continuation Backup
## Checkpoint: 2026-10-01
## Milestone: PLATEAU 8K validation, world-foundation decisions, and current continuation state

> Self-contained continuation/progression record. Intended to let a future ChatGPT conversation resume the project without depending on the original conversation.

## 1. PROJECT IDENTITY AND CURRENT GOAL

Project: Omniversel Roleplay.
Genre: Unity open-world multiplayer real-life/crime RP, mobile-first, original project inspired by the structural organization of GTA RP / CRMP / SA-MP-style worlds, but not copying proprietary assets/content.
Release target: one public release within 2027.
The ~3-month milestone is a public/marketing/community-facing checkpoint of the same release game, not a separate prototype.
Broad target: playable foundation in roughly 6–8 months from late September 2026, possibly sooner.

Initial release-game scope:
- 2 Police Departments
- 1 FBI
- 2 Hospitals
- 1 Government House
- 1 Military
- at least 3 crime organizations
- later possible fire stations, jail and additional organizations
- 300+ houses using reusable exterior/interior templates
- apartment buildings
- 200+ businesses using reusable business templates
- many interiors/buildings
- male + female base character systems with customization
- cars, clothing, accessories
- inventory, items, trading, businesses, fuel stations, money/economy
- organizations/ranks/permissions
- properties/ownership
- multiplayer
- authoritative server/database architecture
- mobile optimization and device-specific graphics
- damage, vehicles, interactions and other RP mechanics

## 2. WORLD STRUCTURE

Initial manually designed region classification:
- 2 major cities
- 2 normal cities
- 2 very rich villages
- 2 rich villages
- 2 middle-class villages
- 2 poor villages
Total initial planned region count: 12.
Regions should have distinct geography such as mountain, coastal/sea, rural and forest environments.
Do NOT build an automated system that decides the world layout. Human designs/assembles regions; automation handles repetitive technical optimization.

## 3. PLATEAU DISCOVERY

PLATEAU SDK for Unity was investigated because manually building a realistic world would take too long.
Current PLATEAU test environment: Unity 6000.3.25f1 / Unity 6.3 LTS test project, PLATEAU SDK for Unity 4.3.0.
SDK source tarball: D:\PLATEAU-SDK-for-Unity-v4.3.0.tgz
The main game project previously had SDK compatibility/duplicate-folder problems, so PLATEAU experiments moved to the separate Unity 6.3 test project.

## 4. LOCAL DATASET

Dataset: Tokyo 23 wards 2022 CityGML.
Extracted root: 13100_tokyo23-ku_2022_citygml_1_2_op
Expanded size: approximately 66 GB.
IMPORTANT: this is NOT all of Japan.
Observed folders: udx/bldg, brid, dem, fld, frn, htd, lsld, luse, tran, urf, plus metadata and codelists.
Keep the raw dataset as source/reference data until the PLATEAU pipeline is fully validated.

## 5. PLATEAU IMPORT RESULTS

Original 1× area + 2048 texture:
- successful 3D city import.

~10× area + 8192 texture:
- Unity hit D3D11 device reset/removed / Windows GPU TDR.
- Unity Editor had to close.
- This is a workload boundary for the current development PC/import combination, not proof PLATEAU cannot represent the area.

~4× area + 8192 texture:
- many GML conversion/placement failures.
- Console repeatedly showed Failed to placing to scene, Failed to serialize PLATEAU.CityInfo.CityObjectList value, and skipping because id LOD1 is not existing.
- result was mostly unusable/flat.

2× area + 8192 texture:
- SUCCESS after retry.
- usable detailed 3D city imported.
- source PLATEAU LODs work correctly.
- buildings become visibly more detailed when approached.
- roads/terrain/structures are present.
- therefore 8K is viable as a source-quality target at manageable chunk sizes.

## 6. BUILDING VISUAL ISSUE

Some buildings have white/gray tops and some appear incomplete, sometimes with fewer floors/partial geometry than expected.
Do NOT attribute the white roof directly to metadata.
CityObject metadata describes city objects; the visual problem is more likely geometry/material/texture/LOD coverage.
Future workflow: detect suspicious structures, classify them, repair/replace only necessary structures, keep good PLATEAU structures, then optimize.
Do not manually rebuild every building.

## 7. LOD FINDING

Premade/source PLATEAU LODs are useful and visibly working.
PLATEAU source LOD is not the same thing as Unity runtime LOD.
Future runtime optimization should be class-aware: protect landmarks/important buildings, use aggressive LOD for normal buildings, use cheap distant representations, and treat roads/gameplay objects specially.

## 8. CURRENT IMPORT PHILOSOPHY

Target source quality: 8K where appropriate.
Runtime strategy: high-quality source -> chunk/stream -> Unity/runtime LOD -> texture streaming/mips -> material optimization -> culling -> collider optimization -> device-specific graphics.
Do not destroy source quality just to make the old development PC comfortable.

## 9. WORLD IMPORT WORKFLOW

Never blindly import the entire final Omniversel world into one giant Unity scene.
Preferred workflow:
1. choose a real-world PLATEAU municipality/region
2. select a manageable geographic chunk
3. import at high source quality
4. inspect geometry/materials/LOD
5. identify bad/incomplete structures
6. repair/replace only necessary structures
7. add Omniversel gameplay content
8. run future automatic LOD/collider/material optimizer
9. test on target hardware
10. lock/validate the chunk
11. move to the next chunk

## 10. FUTURE OPTIMIZATION BUILDER

After manual world design, build a tool that scans renderers/meshes, detects existing LODGroups, generates missing LODs, assigns aggressive but class-aware distances, protects important structures, optimizes materials where safe, validates collision meshes, and reports statistics.
Human designs world; automation handles repetitive technical optimization.

## 11. NEXT LOCATION

After Tokyo validation, investigate a visually beautiful Japanese region, with Fuji/Shizuoka as a candidate and mountain/coastal/tourist regions preferred.
Before downloading: verify exact PLATEAU coverage, municipality, available LODs/features and approximate download size.
Do not assume Mt. Fuji itself is a highly detailed standalone PLATEAU game asset.

## 12. NEXT TECHNICAL STEP

Create a player-scale validation environment using the successful PLATEAU city:
- PLAYER ENTITY
- CharacterController
- camera
- movement
- collision

Measure player/building scale, road/sidewalk scale, terrain slopes, bridges, building boundaries, LOD transitions, FPS/performance, view distance and sensible chunk size.
Do NOT add complete vehicle/gameplay systems yet.

## 13. PLAYER ENTITY

Long-term architecture:
PLAYER ENTITY -> movement, camera, input, sprint, crouch, jump, interaction, PlayerVisual.
UAL/Joe is only a visual representation.
Current UAL: Unity 6000.6.2f1 URP main game project, UAL1_Standard, Idle/Walk/Sprint/Crouch Idle/Crouch Walk/JumpStart/JumpLoop; crouch is toggle; movement/animation works; jump is intentionally frozen for later replacement.

## 14. VEHICLE ARCHITECTURE — DO NOT REGRESS

The custom WheelCollider vehicle-builder V3/V3.5 path failed and is parked.
Do NOT resume the cube-car/manual physics path or the failed custom V3/V3.5 WheelCollider physics as the main controller.
Chosen architecture: MotionCore Vehicle is the ready-made physics core; Omniversel adapter handles seats, entry/exit, camera, damage, ownership, database, mobile and multiplayer.
RMCar26 was configured with MotionCore earlier.
Use OmniverselCameraManager rather than MotionCore's final chase camera.

## 15. DATABASE DIRECTION

Unity client -> authoritative game server -> PostgreSQL/MySQL.
Planned entities: Players, Characters, Vehicles, Ownership, Properties, Businesses, Organizations, Inventory, Items, Money, Jobs, Ranks, Permissions.
Design the database incrementally by entity/system.

## 16. GRAPHICS

Planned player profiles: Very Low, Low, Medium, High, Very High, Ultra/Custom.
Potential settings: resolution/render scale, texture quality, shadows, LOD quality, view distance, vegetation, reflections, AO, AA, post-processing, effects.
Separate Cinematic Graphics Mode for YouTube/screenshots/trailers, using the actual game scene/assets rather than fake AI gameplay.

## 17. BACKUP POLICY

Backups are a core project requirement.
Every meaningful milestone must preserve project identity, current goal, date, completed work, tests/results, architecture, files/scripts/packages, dependencies, settings, decisions/reasons, failed approaches, known bugs, limitations, next steps, recovery instructions and progression history.
Backups serve three purposes: restart point across conversations/platforms, progression evidence, and technical documentation.
Large binary Unity/PLATEAU assets are not assumed to be pushed to GitHub.

## 18. BACKUP BRANCHES

Repository: PranaySardar-10/DEV-ROOM-TEST
Current branch: backup/omniversel-plateau-continuation-2026-10-01
Previous PLATEAU branch: backup/omniversel-plateau-world-foundation-2026-10-01
Older branches: backup/memory-for-project-2026-09-24 and backup/starting-memory-game-development-2026-09-24.
Development/factory branch: devroom/factory-production-workflow.
Previous PLATEAU checkpoint commit: fc956e0f653872282883e44a45eb5f28f504adda.

## 19. IMMEDIATE NEXT ACTIONS

1. Keep the 66 GB Tokyo source dataset.
2. Preserve the successful 2×/8K test scene until the checkpoint is secure.
3. Add simple PLAYER ENTITY + camera and test player scale/collision/LOD/performance.
4. Record incomplete/white-top building examples.
5. Research a scenic PLATEAU location, preferably Fuji/Shizuoka or another mountain/coastal/tourist region.
6. Check size/LOD/features before downloading.
7. Import a manageable scenic chunk at high quality.
8. Continue chunk-level validation before building the full world.

## 20. CURRENT STATE IN ONE SENTENCE

Omniversel has proven that a manageable PLATEAU area can be imported at 8K with working source LODs and detailed 3D buildings; the next stage is player-scale traversal, selective repair of imperfect structures, scenic-region testing, and construction of the chunk/optimization pipeline.