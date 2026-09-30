# Omniversel Roleplay — Development Backup
## Checkpoint: 2026-10-01
## Topic: PLATEAU world foundation / structural planning / player-scale validation

This checkpoint records the important decisions and discoveries from the recent Omniversel Roleplay development session.

## 1. Project direction
- Project: Omniversel Roleplay.
- Unity: Unity 6.x; PLATEAU test project is Unity 6000.3.25f1 with PLATEAU SDK for Unity 4.3.0.
- Goal: build the actual release game now; the ~3-month milestone is a marketing/community-facing checkpoint of the same release game, not a separate prototype.
- Public release target: within 2027.
- Current broad development target: playable foundation in roughly 6–8 months from late September 2026, possibly sooner.

## 2. Release-world structure
The world is intentionally divided into manually designed, attachable regions. This takes the structural typing idea from CRMP-style RP worlds, but not proprietary assets/content.

Initial world classification:
- 2 major cities
- 2 normal cities
- 2 very rich villages
- 2 rich villages
- 2 middle-class villages
- 2 poor villages

Total initial region types/count: 12 regions.

Regions should have different geographic identities as well, for example:
- mountain region
- sea/coastal region
- rural region
- forest/other distinct environments

The user wants to assemble/design these regions by hand for lower error risk and better control/satisfaction. Do NOT build an automated world-region generator that decides the world layout.

## 3. PLATEAU discovery
A successful PLATEAU local import was completed in the Unity 6.3 test project.

Source dataset:
- Official Tokyo 23 wards 2022 CityGML dataset.
- Extracted root: 13100_tokyo23-ku_2022_citygml_1_2_op
- Dataset contains udx feature folders including bldg, brid, dem, fld, frn, htd, lsld, luse, tran, urf, plus metadata/codelists.
- The extracted dataset is large (~66 GB expanded); keep the raw dataset as source/reference material. Do not delete it merely because the Unity test city will be removed.

Successful PLATEAU import demonstrated:
- real 3D city geometry appears in Unity
- dense buildings, roads, bridges and terrain are present
- imported structures are separately represented objects/models and can be selected/modified
- the result is usable as a real-world city foundation rather than a flat map
- road structure is already largely supplied by PLATEAU
- this can replace months of manual city/world construction work

Important visual limitation observed:
- some ground/road/terrain presentation contains low-quality imagery-like surfaces and baked-looking objects such as cars/humans/shadows
- final Omniversel presentation should replace/improve these surfaces/materials rather than relying on raw imagery
- building visual quality can be improved through higher-quality import settings, materials, shaders, LODs and custom game presentation
- PLATEAU geometry is the foundation; Omniversel controls the final game presentation

## 4. PLATEAU import settings used/recommended for the player-scale test
Global:
- Coordinate system: 09 Tokyo
- Import format: scene placement
- Include textures: ON
- Merge textures: ON
- Texture resolution: 2048x2048 for the first test
- Mesh Collider: ON
- Model combination: major feature unit (主要地物単位)
- City-object attributes: OFF for the first visual/gameplay test

Feature selections:
- Buildings: ON, available LODs
- Bridges: ON, available LODs
- Terrain: ON
- Aerial/map texture: ON for the test
- Map URL: default
- Zoom: 18
- Roads: ON
- Disaster risk: OFF
- City planning information: OFF
- Land use: OFF
- City equipment: ON
- Coordinate offsets: leave automatically calculated/default

Official PLATEAU guidance was checked during the session. The game-oriented guidance supports disabling unnecessary disaster-risk/city-planning/land-use layers and using textures, mesh colliders, all relevant LODs and major-feature-unit combination for game import.

## 5. World-building workflow decision
Do NOT import the entire final world and optimize it afterward.

Preferred workflow:
1. Choose a specific real-world/PLATEAU region.
2. Import a manageable section at relatively high source quality.
3. Inspect it in Unity.
4. Improve/replace poor surface presentation where needed.
5. Add/customize aggressive LODs.
6. Apply graphics/performance settings.
7. Test on the available development PC.
8. Validate the chunk/area.
9. Lock it as a usable world section.
10. Move to the next section.

Important distinction:
- Source/import quality should remain sufficiently high so useful geometry/detail is not discarded too early.
- Runtime graphics quality is controlled separately through LODs, materials, shadows, view distance, etc.

## 6. Planned Omniversel graphics architecture
Player-facing graphics must be customizable according to device capability.

Planned quality levels:
- Very Low
- Low
- Medium
- High
- Very High
- Ultra / Custom where hardware permits

Potential individual settings:
- resolution/render scale
- texture quality
- shadow quality/distance
- LOD quality
- view distance
- vegetation/foliage
- reflections
- ambient occlusion
- anti-aliasing
- post-processing
- effects

A separate Cinematic Graphics Mode is planned for high-quality screenshots/trailers/YouTube capture. It should be a separate profile rather than permanently changing gameplay settings.

Cinematic mode may push:
- high/maximum LOD
- high-quality textures
- longer view distance
- higher-quality shadows
- higher render scale
- cinematic lighting/post-processing
- controlled camera/weather/time-of-day
- screenshot/video capture settings

Marketing principle:
- Prefer real in-engine screenshots and trailers from the actual Omniversel world.
- Avoid advertising with AI-generated fake gameplay imagery.
- Cinematic mode can make the actual game world into a virtual film set.

## 7. LOD optimizer idea
A builder/optimizer is useful AFTER a city/region has been manually designed.

It should NOT decide world design.

Proposed future tool:
- scan every renderer/mesh
- detect existing LODGroups
- generate missing LODs
- assign aggressive but class-aware LOD distances
- preserve important/landmark structures longer
- treat roads, buildings, props, vegetation and gameplay objects differently
- optimize materials where safe
- validate collision meshes
- produce a report before/after optimization

Concept:
Human designs world -> optimizer handles repetitive technical LOD work.

Example conceptual profile:
- close: LOD0
- medium: LOD1
- farther: LOD2/LOD3
- distant: very cheap LOD
- very distant: silhouette/cheap representation

Actual distances must be determined experimentally from player-scale tests and target hardware.

## 8. Current vehicle architecture decision
The earlier custom WheelCollider vehicle-builder V3 path is parked/failed and should NOT be resumed as the main physics solution.

Chosen direction:
- use the installed MotionCore Vehicle controller as the proven vehicle physics core
- Omniversel layer handles seats, entry/exit, camera, damage, ownership, DB, mobile and multiplayer integration
- MotionCore setup for RMCar26 was successfully integrated earlier with four WheelColliders, axle mapping, RWD, driving, braking/reverse and collision
- camera system is reusable for player and vehicles
- existing camera artifact: OmniverselCameraSystem_v1.zip; scripts include OmniverselCameraManager.cs and OmniverselCameraButton.cs
- remove/avoid MotionCore Chase as the final camera architecture; use Omniversel camera manager

Do not return to the old cube-car/manual WheelCollider implementation.

## 9. Player/UAL architecture
PLAYER ENTITY is the long-term player architecture; UAL/Joe is only a visual representation.

Concept:
PLAYER ENTITY
- movement
- camera
- input
- jump/crouch/sprint
- interaction
- PlayerVisual
  - current model
  - future models

Current UAL test:
- Unity 6000.6.2f1 URP in the main game project
- UAL1_Standard
- UAL animation states include Idle, Walk, Sprint, Crouch Idle, Crouch Walk, JumpStart, JumpLoop
- crouch is toggle-based
- current player movement/animation system works
- jump is intentionally frozen for later replacement/refinement

## 10. Immediate next test
After the successful PLATEAU city import, create a small player-basis validation environment.

Test components:
- imported PLATEAU area
- Mesh Colliders enabled
- a simple player character
- character controller
- camera
- movement

Do NOT add full vehicles or complex gameplay yet.

Purpose of the test:
1. verify building/road/sidewalk scale from player height
2. verify collision quality
3. test terrain slopes/elevation
4. test bridges/roads
5. inspect which structures could become enterable
6. inspect LOD quality from player distance
7. measure actual rendering/performance cost
8. determine sensible view distance
9. determine sensible region/chunk size
10. identify what needs visual/material modification

This is a structural validation step before committing to the actual 12-region world foundation.

## 11. Backup policy
The project already uses dedicated backup branches.
Existing historical branches include:
- backup/memory-for-project-2026-09-24
- backup/starting-memory-game-development-2026-09-24

This checkpoint was created as:
- backup/omniversel-plateau-world-foundation-2026-10-01

Base branch:
- devroom/factory-production-workflow

This backup records the current Omniversel architectural/world decisions and PLATEAU milestone. It does not claim that the entire local Unity project binary/assets have been pushed to GitHub; the large PLATEAU dataset remains local/source data.

## 12. Do-not-regress constraints
- Do not resume the failed custom vehicle physics V3 path.
- Do not build an automated world-region generator; regions are manually designed.
- Do not delete the extracted PLATEAU source dataset until the world-building pipeline is fully validated.
- Do not treat PLATEAU LOD as the same thing as Unity runtime LOD; use both appropriately.
- Do not rely on AI-generated fake gameplay imagery for marketing.
- Do not import the entire final world blindly before chunk-level validation.
