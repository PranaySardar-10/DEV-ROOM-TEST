# GAME-CHARACTER-001 — Playable Joe Prototype

## OBJECTIVE

Create the minimal, deterministic Omniversel Roleplay third-person playable-character prototype using the existing Joe asset and existing Mixamo/Unity Humanoid setup in the Unity workspace.

The implementation must inspect and reuse what is already present. Do not recreate or replace existing Joe/avatar/animation assets unless required by compilation or integration.

## WORKSPACE

Unity workspace:
`D:\OMNIVERSEL ROLEPLAY\OMNIVERSEL ROLEPLAY`

Unity version: 6000.6.2f1, URP.

Do not modify `Assets/Omniversel/Tests/FoundationTest.unity`.
Do not change the project's GPU Resident Drawer setting.

## CURRENT VERIFIED ASSETS

Existing character asset under:
`Assets/Omniversel/Characters/`

The downloaded Mixamo character was originally named Joe on Mixamo, but the imported FBX/model currently has the filename/display name `character`. Treat the character identity as **Joe** while preserving existing asset references. Do not perform a risky global rename.

Existing verified setup:
- Joe/character FBX imported as Humanoid.
- Humanoid Avatar is valid.
- Mixamo Walking animation was downloaded without skin.
- Walking animation uses Joe's Humanoid Avatar via Copy From Other Avatar.
- Walking clip is set to loop.
- Existing Animator Controller is `JoeAnimator` / `JoeAnimatorController` as currently present in the project.
- Walking is the current default Animator state and plays successfully on Joe in Play Mode.
- Character material extraction was attempted; materials/textures exist but visual appearance is currently unresolved. Do not make material repair a blocker for this task.

## TARGET BEHAVIOUR

Implement a minimal third-person character prototype:

- W/A/S/D: movement
- Shift held: sprint
- Space: jump
- C held/toggled: crouch
- Hold LMB + mouse movement: rotate third-person camera
- RMB: context action input
- RMB must expose a clean gameplay action hook so a future hit/attack action can be bound to it, but do NOT implement a combat system in this task.
- Camera follows/rotates around the player in third-person.
- Movement and animation state should be integrated with the existing Joe Animator.
- Walking must remain functional.
- Sprint/jump/crouch must have deterministic state handling even if dedicated animations are not yet available. Do not invent or download additional animation assets during implementation unless the approved workspace already contains them.
- Do not add networking, multiplayer, combat, vehicles, inventory, economy, NPC AI, backend, save/load, or other gameplay systems.

## IMPLEMENTATION APPROACH

Prefer an existing Unity-provided/installed third-person character-controller capability or package if it is already available in the project/package manifest and can be integrated cleanly.

If no suitable installed controller exists, implement only the minimal local controller required for this task using Unity-supported APIs. Do not introduce speculative third-party frameworks, dependency injection, service locators, ECS/DOTS, or custom architecture.

Input should be represented as gameplay actions rather than scattering hard-coded mouse/keyboard checks through unrelated gameplay code, so the bindings can later be replaced for controller/mobile input.

Keep camera control separate from movement and keep RMB as an action/context hook rather than hard-coding combat.

## TEST SCENE

Use the existing:
`Assets/Scenes/CharacterTest.unity`

This is a development/test scene only. Do not modify FoundationTest.

The test scene may contain the Joe character, camera, lighting, controller components, Animator Controller, and minimal test-only objects required for the prototype.

## NAMING

Use Omniversel-specific names for new scripts/components. Avoid generic names that could collide later.

## SCOPE GUARDRAILS

Forbidden:
- networking/multiplayer
- authentication/accounts
- backend/database
- vehicles
- inventory/economy/shop
- weapons/combat implementation
- NPC AI
- missions/quests
- map/world streaming
- save/load
- chat/voice
- monetization/admin/anti-cheat/analytics/telemetry
- mobile-specific implementation
- Addressables/ECS/DOTS/DI/service locator
- speculative frameworks
- modifications to FoundationTest

## VERIFICATION PLAN

Implementer must:
1. Inspect the current workspace before modifying it.
2. Reuse the existing Joe Humanoid/Animator setup.
3. Keep all changes inside the approved character/test scope.
4. Compile successfully.
5. Produce a deterministic change/artifact report.

QA must independently verify:
- expected files/components exist
- no forbidden systems were introduced
- no FoundationTest modification
- references are valid
- compilation/static checks available to QA pass
- input bindings and controller state transitions are present
- camera and character-controller setup is internally consistent

Human Unity validation remains required for actual runtime behaviour:
- Joe appears in CharacterTest
- WASD moves Joe
- Shift changes movement to sprint state/behaviour
- Space jumps
- C crouches
- holding LMB and moving mouse rotates camera
- camera follows Joe in third person
- RMB invokes the context-action hook
- Walking animation plays during movement
- Play/Stop can be repeated without errors

## COMPLETENESS CHECK

Before implementation, confirm:
- every required behaviour above has a concrete implementation location
- existing Joe/Animator assets are reused
- CharacterTest is the only scene intended for runtime validation
- FoundationTest remains untouched
- no forbidden scope is introduced
- verification steps are executable
