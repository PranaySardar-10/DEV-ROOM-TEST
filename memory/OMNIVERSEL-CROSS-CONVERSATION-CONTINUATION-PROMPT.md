# OMNIVERSEL ROLEPLAY — CROSS-CONVERSATION CONTINUATION PROMPT
## Give this prompt to a new ChatGPT conversation when continuing the project

IMPORTANT: This is an existing long-running project. Do NOT restart it as a new project.

## PRIMARY INSTRUCTION

Before answering project-development questions, reconstruct the project state from the GitHub backup records in this prompt.

Repository: PranaySardar-10/DEV-ROOM-TEST
Current branch: backup/omniversel-plateau-continuation-2026-10-01
Current checkpoint: memory/omniversel-plateau-full-continuation-2026-10-01.md
Previous PLATEAU checkpoint branch: backup/omniversel-plateau-world-foundation-2026-10-01

Read the current continuation checkpoint first. Consult older backup branches when historical context, failed approaches, architecture decisions, or progression evidence is relevant.

## DIRECT LINKS

Current continuation branch:
https://github.com/PranaySardar-10/DEV-ROOM-TEST/tree/backup/omniversel-plateau-continuation-2026-10-01

Previous PLATEAU foundation:
https://github.com/PranaySardar-10/DEV-ROOM-TEST/tree/backup/omniversel-plateau-world-foundation-2026-10-01

Older project-memory backup:
https://github.com/PranaySardar-10/DEV-ROOM-TEST/tree/backup/memory-for-project-2026-09-24

Starting game-development backup:
https://github.com/PranaySardar-10/DEV-ROOM-TEST/tree/backup/starting-memory-game-development-2026-09-24

Repository:
https://github.com/PranaySardar-10/DEV-ROOM-TEST

Factory/development branch:
https://github.com/PranaySardar-10/DEV-ROOM-TEST/tree/devroom/factory-production-workflow

## HOW TO RECONSTRUCT STATE

1. Read the current continuation checkpoint.
2. Read the previous PLATEAU foundation checkpoint.
3. Consult the older memory backups if needed.
4. Treat the newest checkpoint as current state.
5. Treat older checkpoints as historical evidence.
6. Preserve failed approaches so they are not accidentally repeated.
7. Do not claim large local Unity/PLATEAU binary assets are in GitHub unless the backup says so.
8. If GitHub access is unavailable, do not invent missing state; ask for access or for the checkpoint content.

## CURRENT PROJECT

Omniversel Roleplay is a Unity open-world multiplayer real-life/crime RP game, mobile-first, original, targeting public release within 2027.
The ~3-month milestone is a marketing/community-facing checkpoint of the same release game, not a separate prototype.
Initial release scope includes 2 Police Departments, 1 FBI, 2 Hospitals, 1 Government House, 1 Military, 3+ crime organizations, 300+ houses, apartments, 200+ businesses, many interiors, vehicles, clothing/accessories, customization, inventory/items/trading, businesses/fuel, properties, organizations, economy, multiplayer, database, mobile optimization and graphics systems.

World structure: 2 major cities, 2 normal cities, 2 very rich villages, 2 rich villages, 2 middle-class villages, 2 poor villages, with contrasting mountain/coastal/rural/forest identities.
World layout is manually designed. Do not create an automated world-layout generator.

## PLATEAU CURRENT STATE

PLATEAU SDK for Unity 4.3.0 is being tested in Unity 6000.3.25f1.
Local dataset: Tokyo 23 wards 2022 CityGML, extracted root 13100_tokyo23-ku_2022_citygml_1_2_op, approximately 66 GB expanded.
This is NOT all of Japan.
Keep the raw dataset until the world-building pipeline is validated.

## MOST IMPORTANT PLATEAU RESULT

A 2× original-area import at 8192×8192 texture resolution successfully completed.
It produced detailed 3D buildings, roads and terrain, and the premade/source PLATEAU LODs visibly work: buildings become more detailed when approached.
Therefore 8K is viable as a source-quality target at manageable chunk sizes.

## TEST HISTORY

1× + 2K: successful.
~10× + 8K: D3D11 GPU/TDR failure and Unity shutdown.
~4× + 8K: many GML conversion/placement failures and CityObjectList/LOD errors; mostly unusable result.
2× + 8K: successful after retry.

## CURRENT BUILDING ISSUE

Some buildings have white/gray tops and some appear incomplete or partially modelled.
Do not claim metadata itself creates the white roof. CityObject metadata describes objects; the visual issue is more likely geometry/material/texture/LOD coverage.
Future approach: detect suspicious structures, classify them, repair/replace only necessary structures, and keep good PLATEAU structures.
Do not manually rebuild every building.

## 8K PHILOSOPHY

8K is a source-quality target, not a requirement that every device render full 8K everywhere.
Use high-quality source -> chunking/streaming -> runtime LOD -> texture streaming/mips -> material optimization -> culling -> collider optimization -> device-specific graphics.
Do not destroy source quality prematurely just to accommodate the current old development PC.

## NEXT STEP

Use the successful PLATEAU scene for a player-scale validation:
- PLAYER ENTITY
- CharacterController
- camera
- movement
- collision

Test scale, roads/sidewalks, terrain, bridges, building boundaries, LOD transitions, FPS/performance, view distance and chunk size.
Do not add complete vehicles/gameplay yet.

## NEXT LOCATION

Investigate a beautiful Japanese PLATEAU region after Tokyo validation, with Fuji/Shizuoka as a candidate.
Before downloading, verify municipality/coverage, available LODs/features and download/extracted size.
Do not assume Mt. Fuji itself is a highly detailed standalone PLATEAU asset.

## ARCHITECTURE — DO NOT REGRESS

PLAYER ENTITY is the gameplay entity; UAL/Joe is only a visual representation.
Do not resume failed custom vehicle V3/V3.5 WheelCollider physics.
Use MotionCore Vehicle as the physics core; Omniversel adapter handles seats, entry/exit, camera, damage, ownership, database, mobile and multiplayer.
Backend: Unity client -> authoritative server -> PostgreSQL/MySQL.

## BACKUP RULE

Every meaningful milestone must receive a detailed checkpoint containing current state, tests/results, settings, architecture, decisions/reasons, failed approaches, bugs, limitations, next steps, recovery instructions and progression history.
These backups are the project's continuity record, progression evidence and technical documentation.

## CONTINUATION BEHAVIOR

Do not restart the project.
Do not ask the user to repeat information already present in the backups.
Do not revive abandoned approaches without an explicit new reason.
When a screenshot/video/error is supplied, interpret it in the context of the checkpoint, distinguish known issues from new issues, and propose the smallest controlled next test.
Do not change many variables at once unless there is a clear reason.
Preserve successful configurations.
After meaningful milestones, update the backup branch with a new detailed checkpoint.

## EXACT CURRENT CONTINUATION POINT

PLATEAU 2× area + 8K SUCCESSFUL -> player-scale validation -> investigate incomplete/white-top structures -> research scenic Japanese PLATEAU region -> build chunk/optimization pipeline.