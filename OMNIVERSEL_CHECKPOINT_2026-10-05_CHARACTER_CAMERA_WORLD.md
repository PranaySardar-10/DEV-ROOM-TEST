# Omniversel Roleplay — Checkpoint 2026-10-05

## Project authority
Omniversel Roleplay is the primary active project. Old DevRoom/local-agent material is historical tooling context only and must not be mixed into current game development decisions.
Target engine: Unity 6.3 LTS, URP. Mobile-first open-world real-life/crime RP multiplayer, planned public release within 2027.

## Current world-building production decision
The old idea of one-click full-world masterplan generation is rejected for final production because generic procedural output does not meet the desired visual quality.
New method: build Omniversel professionally area-by-area using the best specialized tools available, then manually make final geography/visual/gameplay decisions.
Each area must become real final-game content, not a disposable prototype.
The atlas is the geographic reference, not a one-shot final generator.

## Area production pipeline
1. Lock area's boundaries, purpose, neighbors and world-space coordinates.
2. Build final-use terrain geography.
3. Build hydrology and water.
4. Assign/blend terrain materials automatically where possible.
5. Build highways/roads/infrastructure.
6. Place major structures.
7. Generate/assemble settlements and buildings.
8. Add vegetation.
9. Add props/environmental dressing.
10. Visual/art pass.
11. Gameplay pass.
12. LOD/HLOD/culling/instancing/streaming optimization.
13. Validate connections to neighboring areas.
14. Lock the area.

## Continuous-world connection contract
Areas must connect as one world:
- fixed world-space coordinates
- terrain edges aligned
- roads physically connect
- rivers/water leave and enter areas at matching positions/elevations
- coastlines and beaches continue naturally
- streaming boundaries are defined
- LOD/HLOD transitions are consistent
- gameplay/navigation links are preserved
No teleport/loading boundary should be required between normal neighboring regions.

## Terrain-generation findings
External CPU terrain generation is now a proven route for large authored terrain data.
Verified:
- 8 x 8 km = 64 km² imported successfully.
- 10 x 10 km = 100 km² tested.
- 25 x 25 km = 625 km² terrain imported into Unity as a 2049 x 2049 heightmap terrain.
Large terrain area is therefore technically plausible; final Omniversel size is deliberately NOT locked.
Area is not the same as perceived scale; final dimensions/travel distances/density matter.

## Current atlas geography
- Main City: Japanese metropolis style.
- Coastal City: Miami-like coastal city.
- Port City: dense mid-level port/industrial city.
- Military zone with its own airfield.
- One commercial airport.
- Northern mountain range.
- Western forest region.
- Eastern desert region.
- Japanese rural village.
- Eastern-European rural village.
- Rural/farmland regions.
- Mountain/lake rich residential region.
- Beach rich area.
- Resort island.
- Private super-rich island connected by bridge.
- Large surrounding coastline with beaches, cliffs and coves.
- Multiple major rivers/lakes including a desert lake.
All numerical labels printed on the atlas are placeholders and are not locked.

## Desert area decision
The desert should feel Sandy Shores-inspired but larger and more geographically believable.
Final geography target:
- one large main lake
- coast/beach, including rocky shoreline
- a few hill systems
- 2–3 residential/settlement areas
- large open/breathable desert space
- quarry
- dedicated off-road area
- offshore oil-rig location reserved geographically
- detailed buildings/props added later
The earlier many-pond version was rejected as too procedural/unrealistic.
A 12 x 10 km (120 km²) desert terrain test exists as a geographic foundation/test, not final art.

## Automatic terrain-material system
World Builder should eventually maintain a material/asset registry.
TerrainLayer selection should be deterministic from:
- biome
- height
- slope
- distance to water
- distance to coast
- explicit masks
Examples:
flat desert -> sand
steep desert -> rocky sand/rock
mountain -> rock
grassland -> grass
river/lake edge -> mud/wet ground
beach -> sand/wet sand
Use smooth falloff/blending instead of hard biome borders.

## Current character scene state (from Unity screenshots 2026-10-05)
Character root: Armature.
Visible components:
- Animator
- Character Controller
- Player Input
- Third Person Controller (Script)

ThirdPersonController visible values:
- Move Speed: 2
- Sprint Speed: 5.335
- Rotation Smooth Time: 0.12
- Speed Change Rate: 10
- Jump Height: 1.2
- Gravity: -15
- Jump Timeout: 0.5
- Fall Timeout: 0.15
- Grounded enabled
- Grounded Offset: -0.14
- Grounded Radius: 0.28
- Ground Layers: Nothing
- Cinemachine Camera Target: Armature
- Top Clamp: 70
- Bottom Clamp: -30
- Camera Angle Override: 0
- Lock Camera Position: off

Character Controller visible values:
- Slope Limit: 45
- Step Offset: 0.3
- Skin Width: 0.08
- Min Move Distance: 0.001
- Radius: 0.5
- Height: 2

Animator screenshot:
- Avatar: ArmatureAvatar
- Runtime Animator Controller: None in the screenshot
- Apply Root Motion: enabled
- Culling Mode: Cull Update Transforms

Player Input screenshot:
- Actions asset: InputSystem_Actions
- Default Scheme: <Any>
- Auto-Switch enabled
- Default Map: <None>
- UI Input Module: None
- Camera: None
- Behavior: Send Messages
The inspector warns that using a project-wide action asset with Player Input is not recommended unless maps are manually controlled.

## Camera follow decision
Use the existing Cinemachine setup instead of adding a second unrelated follow system.
The ThirdPersonController already exposes a Cinemachine Camera Target field, so the character's intended camera target can drive the third-person camera.
Use exactly one real Main Camera. Add/configure a Cinemachine Camera for follow/positioning; do not add duplicate Main Cameras.
For Cinemachine, the camera should follow the character camera-target transform and use a third-person positioning mode with appropriate damping. Unity/Cinemachine documentation describes Follow as the target the camera moves with, and a third-person follow component as a purpose-built third-person tracking system.
Current goal: get the camera following Armature correctly in the current scene before refining camera feel, collision, mobile controls, or camera-relative movement.

## Character-system continuity
Previous UAL work included stable animation driver integration, sprint/crouch behavior fixes and jump/landing fixes. Preserve working animation behavior; do not replace UAL or existing character functionality unnecessarily.

## World Builder architecture
Preferred role of World Builder: world assembly/streaming/validation/orchestration rather than one giant procedural generator.
Backends may include:
- Terrain: Vista/external heightmap route
- Hydrology: InstantRiver/UWS/erosion where useful
- Roads: procedural roads
- Cities: FCG and other city tools
- Water: Oceana-URP/UWS depending on testing
- Vegetation/props: registered asset packs
- Optimization: existing Omniversel LOD Injector + streaming/culling/HLOD
Tool compatibility must be verified in Unity 6.3 before relying on it.

## Key rule
Do not call generated terrain, city, road, material, vegetation or prop output "finished" until it passes the area production pipeline and connection validation.
