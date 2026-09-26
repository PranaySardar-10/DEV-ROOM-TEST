# GAME-FOUNDATION-001 — ChatGPT implementation plan

This plan is the experimental direct ChatGPT architecture/coding output for the first Omniversel Roleplay foundation task.

## Implementation scope

Modify only `Assets/Omniversel/`. Create these directories:

- Assets/Omniversel/
- Assets/Omniversel/Core/
- Assets/Omniversel/Infrastructure/
- Assets/Omniversel/Gameplay/
- Assets/Omniversel/UI/
- Assets/Omniversel/Bootstrap/
- Assets/Omniversel/Editor/
- Assets/Omniversel/Tests/

Create exactly these seven runtime/editor assembly definitions:

### Assets/Omniversel/Core/Omniversel.Core.asmdef
```json
{
  "name": "Omniversel.Core",
  "rootNamespace": "Omniversel.Core",
  "references": [],
  "includePlatforms": [],
  "excludePlatforms": [],
  "allowUnsafeCode": false,
  "overrideReferences": false,
  "precompiledReferences": [],
  "autoReferenced": true,
  "defineConstraints": [],
  "versionDefines": [],
  "noEngineReferences": false
}
```

### Assets/Omniversel/Infrastructure/Omniversel.Infrastructure.asmdef
```json
{
  "name": "Omniversel.Infrastructure",
  "rootNamespace": "Omniversel.Infrastructure",
  "references": [
    "Omniversel.Core"
  ],
  "includePlatforms": [],
  "excludePlatforms": [],
  "allowUnsafeCode": false,
  "overrideReferences": false,
  "precompiledReferences": [],
  "autoReferenced": true,
  "defineConstraints": [],
  "versionDefines": [],
  "noEngineReferences": false
}
```

### Assets/Omniversel/Gameplay/Omniversel.Gameplay.asmdef
```json
{
  "name": "Omniversel.Gameplay",
  "rootNamespace": "Omniversel.Gameplay",
  "references": [
    "Omniversel.Core",
    "Omniversel.Infrastructure"
  ],
  "includePlatforms": [],
  "excludePlatforms": [],
  "allowUnsafeCode": false,
  "overrideReferences": false,
  "precompiledReferences": [],
  "autoReferenced": true,
  "defineConstraints": [],
  "versionDefines": [],
  "noEngineReferences": false
}
```

### Assets/Omniversel/UI/Omniversel.UI.asmdef
```json
{
  "name": "Omniversel.UI",
  "rootNamespace": "Omniversel.UI",
  "references": [
    "Omniversel.Core"
  ],
  "includePlatforms": [],
  "excludePlatforms": [],
  "allowUnsafeCode": false,
  "overrideReferences": false,
  "precompiledReferences": [],
  "autoReferenced": true,
  "defineConstraints": [],
  "versionDefines": [],
  "noEngineReferences": false
}
```

### Assets/Omniversel/Bootstrap/Omniversel.Bootstrap.asmdef
```json
{
  "name": "Omniversel.Bootstrap",
  "rootNamespace": "Omniversel.Bootstrap",
  "references": [
    "Omniversel.Core",
    "Omniversel.Infrastructure",
    "Omniversel.Gameplay",
    "Omniversel.UI"
  ],
  "includePlatforms": [],
  "excludePlatforms": [],
  "allowUnsafeCode": false,
  "overrideReferences": false,
  "precompiledReferences": [],
  "autoReferenced": true,
  "defineConstraints": [],
  "versionDefines": [],
  "noEngineReferences": false
}
```

### Assets/Omniversel/Editor/Omniversel.Editor.asmdef
```json
{
  "name": "Omniversel.Editor",
  "rootNamespace": "Omniversel.Editor",
  "references": [],
  "includePlatforms": [
    "Editor"
  ],
  "excludePlatforms": [],
  "allowUnsafeCode": false,
  "overrideReferences": false,
  "precompiledReferences": [],
  "autoReferenced": true,
  "defineConstraints": [],
  "versionDefines": [],
  "noEngineReferences": false
}
```

### Assets/Omniversel/Tests/Omniversel.Tests.asmdef
```json
{
  "name": "Omniversel.Tests",
  "rootNamespace": "Omniversel.Tests",
  "references": [],
  "includePlatforms": [
    "Editor"
  ],
  "excludePlatforms": [],
  "allowUnsafeCode": false,
  "overrideReferences": false,
  "precompiledReferences": [],
  "autoReferenced": false,
  "defineConstraints": [],
  "versionDefines": [],
  "noEngineReferences": false
}
```

## Bootstrap code

Create `Assets/Omniversel/Bootstrap/FoundationBootstrap.cs`:

```csharp
using UnityEngine;

namespace Omniversel.Bootstrap
{
    public sealed class FoundationBootstrap : MonoBehaviour
    {
        private bool _initialized;

        private void Awake()
        {
            if (_initialized)
            {
                return;
            }

            _initialized = true;
            Debug.Log("Omniversel Foundation initialized");
        }
    }
}
```

No networking, database, backend, player, UI, file writes, PlayerPrefs, async initialization, persistent singleton, or static/global state.

## Deterministic script metadata

Create `Assets/Omniversel/Bootstrap/FoundationBootstrap.cs.meta` with this fixed GUID so the test scene can reference the script deterministically:

```yaml
fileFormatVersion: 2
guid: bb704dd25e1246b49e762964da65cdb8
MonoImporter:
  externalObjects: {}
  serializedVersion: 2
  defaultReferences: []
  executionOrder: 0
  icon: {instanceID: 0}
  userData:
  assetBundleName:
  assetBundleVariant:
```

## Test scene

Create `Assets/Omniversel/Tests/FoundationTest.unity` containing exactly one root GameObject named `OmniverselFoundation`, with exactly one Transform and one FoundationBootstrap component.

Use this deterministic scene:

```yaml
%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!1 &1000
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  serializedVersion: 6
  m_Component:
  - component: {fileID: 4000}
  - component: {fileID: 11400000}
  m_Layer: 0
  m_Name: OmniverselFoundation
  m_TagString: Untagged
  m_Icon: {fileID: 0}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!4 &4000
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: 1000}
  serializedVersion: 2
  m_LocalRotation: {x: 0, y: 0, z: 0, w: 1}
  m_LocalPosition: {x: 0, y: 0, z: 0}
  m_LocalScale: {x: 1, y: 1, z: 1}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {fileID: 0}
  m_LocalEulerAnglesHint: {x: 0, y: 0, z: 0}
--- !u!114 &11400000
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {fileID: 0}
  m_PrefabInstance: {fileID: 0}
  m_PrefabAsset: {fileID: 0}
  m_GameObject: {fileID: 1000}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {fileID: 11500000, guid: bb704dd25e1246b49e762964da65cdb8, type: 3}
  m_Name:
  m_EditorClassIdentifier:
--- !u!1660057539 &9223372036854775807
SceneRoots:
  m_ObjectHideFlags: 0
  m_Roots:
  - {fileID: 1000}
```

Create `Assets/Omniversel/Tests/FoundationTest.unity.meta`:

```yaml
fileFormatVersion: 2
guid: 10b032a56f0d44129e25ce3fcff1e2d6
DefaultImporter:
  externalObjects: {}
  userData:
  assetBundleName:
  assetBundleVariant:
```

## Important implementation constraints

- Do not modify ProjectSettings, URP, GPU Resident Drawer, Android settings, input, physics, quality settings, packages, or unrelated files.
- Do not create any additional assemblies.
- Do not create gameplay, networking, player, vehicle, economy, inventory, weapon, NPC, mission, quest, map, streaming, save/load, server, matchmaking, chat, voice, accounts, monetization, admin, anti-cheat, analytics, telemetry, AI, procedural generation, mobile controls, Addressables, ECS/DOTS, DI, service locator, or third-party systems.
- Unity-generated asset metadata for the seven asmdefs/folders may be created by Unity; do not hand-author unrelated metadata.
- The fixed script and scene .meta files above are intentional because the scene must reference the FoundationBootstrap script deterministically.
- Do not modify files outside `Assets/Omniversel/`.

## Verification

After writing the files:

1. Confirm the seven exact asmdef names and their references.
2. Confirm there is no `Assembly-CSharp` reference.
3. Confirm the dependency graph is acyclic and follows the required direction.
4. Confirm `FoundationBootstrap.cs` contains the exact log message and no forbidden systems.
5. Confirm `FoundationTest.unity` has exactly one root object named `OmniverselFoundation` and the FoundationBootstrap component.
6. Let Unity import/recompile the project.
7. Open FoundationTest.unity.
8. Enter Play Mode and verify the exact Console message:
   `Omniversel Foundation initialized`
9. Exit and re-enter Play Mode and verify the same message again.
10. Confirm no foundation-related errors and no extra gameplay/camera/UI/audio/network objects.
11. Confirm Git changes are limited to the task.

The Implementer must report only actual changes. QA must independently verify the workspace and must not trust the plan or Implementer claims as evidence.
