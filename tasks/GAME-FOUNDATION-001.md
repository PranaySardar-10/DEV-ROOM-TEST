# GAME-FOUNDATION-001

## Objective
Create the minimal, deterministic Omniversel Roleplay Unity project foundation.

## Current state
- Unity 6000.6.2f1 project already exists.
- Rendering uses URP.
- GPU Resident Drawer is already disabled and must not be changed.
- The Unity project is a Git workspace on branch agent/implementer/game-foundation-001.
- No database, backend, gameplay systems, networking systems, or persistent game systems exist yet.

## Required directories
Create exactly:
- Assets/Omniversel/
- Assets/Omniversel/Core/
- Assets/Omniversel/Infrastructure/
- Assets/Omniversel/Gameplay/
- Assets/Omniversel/UI/
- Assets/Omniversel/Bootstrap/
- Assets/Omniversel/Editor/
- Assets/Omniversel/Tests/

## Required files
Create exactly:
- Assets/Omniversel/Core/Omniversel.Core.asmdef
- Assets/Omniversel/Infrastructure/Omniversel.Infrastructure.asmdef
- Assets/Omniversel/Gameplay/Omniversel.Gameplay.asmdef
- Assets/Omniversel/UI/Omniversel.UI.asmdef
- Assets/Omniversel/Bootstrap/Omniversel.Bootstrap.asmdef
- Assets/Omniversel/Editor/Omniversel.Editor.asmdef
- Assets/Omniversel/Tests/Omniversel.Tests.asmdef
- Assets/Omniversel/Bootstrap/FoundationBootstrap.cs
- Assets/Omniversel/Tests/FoundationTest.unity

## Assembly boundaries
- Core has no dependencies on other Omniversel runtime assemblies.
- Infrastructure may reference Core only.
- Gameplay may reference Core and Infrastructure only.
- UI may reference Core only.
- Bootstrap may reference Core, Infrastructure, Gameplay and UI.
- Editor is editor-only and may reference runtime assemblies only when required.
- Tests contain only test infrastructure and may reference target assemblies as required.
- No production assembly may reference Assembly-CSharp.
- No circular dependencies.
- Do not create additional assemblies.

## Bootstrap
FoundationBootstrap.cs:
- Namespace Omniversel.Bootstrap.
- MonoBehaviour named FoundationBootstrap.
- Deterministic initialization.
- Emit exactly: Omniversel Foundation initialized
- Initialize once per FoundationBootstrap instance.
- No networking, database, backend, player, UI, file writes, PlayerPrefs, async initialization, persistent singleton, or hidden global state.

## Test scene
Create Assets/Omniversel/Tests/FoundationTest.unity.
It must contain one root GameObject named OmniverselFoundation with FoundationBootstrap.
Do not add gameplay, networking, player, camera-controller, UI, audio, or other gameplay objects.

## Forbidden scope
Do not create or implement networking, multiplayer, authentication, backend, database, player, character, vehicle, economy, inventory, item, weapon, NPC, mission, quest, map, world streaming, save/load, server, matchmaking, chat, voice, account, monetization, shop, admin, anti-cheat, analytics, telemetry, AI, procedural generation, mobile controls, addressables, ECS/DOTS, dependency injection, service locator, third-party packages, or speculative architecture.

## Project settings
Do not modify unrelated ProjectSettings, graphics, URP, GPU Resident Drawer, Android settings, input, physics, or quality settings unless strictly required for this task. Report unavoidable conflicts instead of inventing changes.

## Acceptance
PASS only when:
1. Required directories exist.
2. Exact seven asmdefs exist.
3. Dependency direction is correct and acyclic.
4. No production assembly references Assembly-CSharp.
5. FoundationBootstrap compiles and has exact required behavior.
6. FoundationTest exists with the required object/component.
7. Unity compiles without task-caused errors.
8. Play Mode produces the exact required initialization message.
9. Play Mode can be entered/exited twice without foundation-related errors.
10. Clean Unity reopen still works.
11. Git changes are limited to this task.
12. No generated/cache directories, secrets, or unrelated files are added.

## QA
Report exactly:
STRUCTURE: PASS/FAIL
ASSEMBLIES: PASS/FAIL
DEPENDENCIES: PASS/FAIL
COMPILATION: PASS/FAIL
BOOTSTRAP: PASS/FAIL
SCENE: PASS/FAIL
SCOPE: PASS/FAIL
GIT HYGIENE: PASS/FAIL

If any requirement fails, do not claim completion.

## Human Unity validation
Open FoundationTest.unity, enter Play Mode, verify Omniversel Foundation initialized, exit, enter Play Mode again, and verify the same result without errors.

## Completion
Do not report completion until implementation, QA, and human Unity validation all pass. If any requirement is ambiguous or impossible, report the exact conflict instead of inventing a solution.
