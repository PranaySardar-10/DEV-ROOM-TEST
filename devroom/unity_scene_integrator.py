from __future__ import annotations

import re
import uuid
from pathlib import Path

SCRIPT_PATHS = (
    "Assets/Omniversel/Gameplay/Character/OmniverselCharacterInput.cs",
    "Assets/Omniversel/Gameplay/Character/OmniverselCharacterController.cs",
    "Assets/Omniversel/Gameplay/Character/OmniverselThirdPersonCamera.cs",
)

NAMESPACE = uuid.UUID("7e6c8b8a-6d6f-4c2a-9f1a-0d7e2b4c9a11")


def script_guid(path: str) -> str:
    return uuid.uuid5(NAMESPACE, path).hex


def ensure_script_meta(workspace, path: str) -> str:
    guid = script_guid(path)
    meta_path = path + ".meta"
    target = workspace._safe_path(meta_path)
    if not target.exists():
        workspace.write_file(
            meta_path,
            "fileFormatVersion: 2\n"
            f"guid: {guid}\n"
            "MonoImporter:\n"
            "  externalObjects: {}\n"
            "  serializedVersion: 2\n"
            "  defaultReferences: []\n"
            "  executionOrder: 0\n"
            "  icon: {instanceID: 0}\n"
            "  userData:\n"
            "  assetBundleName:\n"
            "  assetBundleVariant:\n",
        )
    return guid


def _blocks(text: str):
    return list(re.finditer(r"(?ms)^--- !u!(\d+) &(-?\d+)\n.*?(?=^--- !u!|\Z)", text))


def _block(text: str, match) -> str:
    return match.group(0)


def _field(block: str, name: str) -> str | None:
    m = re.search(rf"(?m)^\s*{re.escape(name)}:.*?fileID: (-?\d+)", block)
    return m.group(1) if m else None


def _object_name(block: str) -> str | None:
    m = re.search(r"(?m)^  m_Name: (.*)$", block)
    return m.group(1).strip() if m else None


def _append_component_to_gameobject(block: str, component_id: int) -> str:
    if re.search(rf"fileID: {component_id}\}}", block):
        return block
    marker = "  m_Layer:"
    insertion = f"  - component: {{fileID: {component_id}}}\n"
    if marker in block:
        return block.replace(marker, insertion + marker, 1)
    raise RuntimeError("Unity GameObject block has no m_Layer insertion point.")


def _append_block(text: str, block: str) -> str:
    return text.rstrip() + "\n" + block.rstrip() + "\n"


def _mono_block(file_id: int, game_object_id: int, guid: str, fields: str) -> str:
    return (
        f"--- !u!114 &{file_id}\n"
        "MonoBehaviour:\n"
        "  m_ObjectHideFlags: 0\n"
        "  m_CorrespondingSourceObject: {fileID: 0}\n"
        "  m_PrefabInstance: {fileID: 0}\n"
        "  m_PrefabAsset: {fileID: 0}\n"
        "  m_GameObject: {fileID: " + str(game_object_id) + "}\n"
        "  m_Enabled: 1\n"
        "  m_EditorHideFlags: 0\n"
        f"  m_Script: {{fileID: 11500000, guid: {guid}, type: 3}}\n"
        "  m_Name:\n"
        "  m_EditorClassIdentifier:\n"
        + fields
    )


def _character_controller_block(file_id: int, game_object_id: int) -> str:
    return (
        f"--- !u!143 &{file_id}\n"
        "CharacterController:\n"
        "  m_ObjectHideFlags: 0\n"
        "  m_CorrespondingSourceObject: {fileID: 0}\n"
        "  m_PrefabInstance: {fileID: 0}\n"
        "  m_PrefabAsset: {fileID: 0}\n"
        f"  m_GameObject: {{fileID: {game_object_id}}}\n"
        "  m_Enabled: 1\n"
        "  serializedVersion: 2\n"
        "  m_Radius: 0.3\n"
        "  m_Height: 1.8\n"
        "  m_SlopeLimit: 45\n"
        "  m_StepOffset: 0.3\n"
        "  m_SkinWidth: 0.08\n"
        "  m_MinMoveDistance: 0\n"
        "  m_Center: {x: 0, y: 0.9, z: 0}\n"
        "  m_DetectCollisions: 1\n"
        "  m_EnableOverlapRecovery: 1\n"
    )


def integrate_character_test(workspace) -> list[str]:
    scene_path = "Assets/Scenes/Character Test.unity"
    scene = workspace.read_file(scene_path)

    guid_input = ensure_script_meta(workspace, SCRIPT_PATHS[0])
    guid_controller = ensure_script_meta(workspace, SCRIPT_PATHS[1])
    guid_camera = ensure_script_meta(workspace, SCRIPT_PATHS[2])

    # This character is an imported FBX/model prefab instance, so its Animator
    # and root GameObject are not serialized as ordinary scene-local objects.
    matches = _blocks(scene)
    prefab_matches = [
        m for m in matches
        if m.group(1) == "1001" and f"guid: c8b4ee65ffebe3e468cfd4b9bc2777f4" in _block(scene, m)
    ]
    if len(prefab_matches) != 1:
        raise RuntimeError(
            "Character Test.unity must contain exactly one character FBX PrefabInstance "
            "(guid c8b4ee65ffebe3e468cfd4b9bc2777f4)."
        )

    prefab_match = prefab_matches[0]
    prefab_id = int(prefab_match.group(2))
    prefab_block = _block(scene, prefab_match)

    source_root_transform = "-8679921383154817045"
    source_root_gameobject = "919132149155446097"
    if f"fileID: {source_root_transform}, guid: c8b4ee65ffebe3e468cfd4b9bc2777f4" not in prefab_block:
        raise RuntimeError("Character FBX PrefabInstance does not contain the expected root Transform target.")
    if f"fileID: {source_root_gameobject}, guid: c8b4ee65ffebe3e468cfd4b9bc2777f4" not in prefab_block:
        raise RuntimeError("Character FBX PrefabInstance does not contain the expected root GameObject target.")

    camera_matches = [m for m in matches if m.group(1) == "20"]
    gameobjects = {m.group(2): m for m in matches if m.group(1) == "1"}
    camera_match = next(
        (
            m for m in camera_matches
            if (_object_name(gameobjects.get(_field(_block(scene, m), "m_GameObject"), m)) or "").lower()
            == "main camera"
        ),
        camera_matches[0] if len(camera_matches) == 1 else None,
    )
    if camera_match is None:
        raise RuntimeError("Could not uniquely identify the Main Camera in Character Test.unity.")
    camera_id = int(_field(_block(scene, camera_match), "m_GameObject") or 0)
    if camera_id == 0:
        raise RuntimeError("Could not resolve the Main Camera GameObject.")

    # Re-read after meta creation and allocate deterministic scene-local IDs.
    scene = workspace.read_file(scene_path)
    matches = _blocks(scene)
    ids = [int(m.group(2)) for m in matches]
    next_id = max(ids + [1000]) + 1

    prefab_match = next(
        m for m in matches
        if m.group(1) == "1001"
        and f"guid: c8b4ee65ffebe3e468cfd4b9bc2777f4" in _block(scene, m)
    )
    prefab_id = int(prefab_match.group(2))
    camera_matches = [m for m in matches if m.group(1) == "20"]
    gameobjects = {m.group(2): m for m in matches if m.group(1) == "1"}
    camera_match = next(
        (
            m for m in camera_matches
            if (_object_name(gameobjects.get(_field(_block(scene, m), "m_GameObject"), m)) or "").lower()
            == "main camera"
        ),
        camera_matches[0] if len(camera_matches) == 1 else None,
    )
    if camera_match is None:
        raise RuntimeError("Could not uniquely identify the Main Camera after meta creation.")
    camera_id = int(_field(_block(scene, camera_match), "m_GameObject") or 0)

    existing_script_ids = set(re.findall(r"guid: ([0-9a-f]{32})", scene))
    prefab_block = _block(scene, prefab_match)

    # Unity represents a model-prefab root through stripped placeholders. Added
    # components target the source GameObject and point to ordinary scene-local
    # component objects whose m_GameObject references that stripped GameObject.
    stripped_go_match = next(
        (
            m for m in matches
            if m.group(1) == "1"
            and " stripped" in m.group(0).splitlines()[0]
            and f"m_CorrespondingSourceObject: {{fileID: {source_root_gameobject}, guid: c8b4ee65ffebe3e468cfd4b9bc2777f4, type: 3}}" in m.group(0)
            and f"m_PrefabInstance: {{fileID: {prefab_id}}}" in m.group(0)
        ),
        None,
    )
    if stripped_go_match is None:
        stripped_go_id = next_id
        next_id += 1
        stripped_go_block = _stripped_gameobject_block(
            stripped_go_id, int(source_root_gameobject),
            "c8b4ee65ffebe3e468cfd4b9bc2777f4", prefab_id
        )
    else:
        stripped_go_id = int(stripped_go_match.group(2))
        stripped_go_block = ""

    stripped_transform_match = next(
        (
            m for m in matches
            if m.group(1) == "4"
            and " stripped" in m.group(0).splitlines()[0]
            and f"m_CorrespondingSourceObject: {{fileID: {source_root_transform}, guid: c8b4ee65ffebe3e468cfd4b9bc2777f4, type: 3}}" in m.group(0)
            and f"m_PrefabInstance: {{fileID: {prefab_id}}}" in m.group(0)
        ),
        None,
    )
    if stripped_transform_match is None:
        stripped_transform_id = next_id
        next_id += 1
        stripped_transform_block = _stripped_transform_block(
            stripped_transform_id, int(source_root_transform),
            "c8b4ee65ffebe3e468cfd4b9bc2777f4", prefab_id
        )
    else:
        stripped_transform_id = int(stripped_transform_match.group(2))
        stripped_transform_block = ""

    added_entries: list[str] = []
    created_blocks: list[str] = []

    if guid_input not in existing_script_ids:
        input_id = next_id
        next_id += 1
        added_entries.append(
            _added_component_entry(int(source_root_gameobject),
                                   "c8b4ee65ffebe3e468cfd4b9bc2777f4", input_id)
        )
        created_blocks.append(_mono_block(input_id, stripped_go_id, guid_input, ""))

    if guid_controller not in existing_script_ids:
        controller_id = next_id
        next_id += 1
        added_entries.append(
            _added_component_entry(int(source_root_gameobject),
                                   "c8b4ee65ffebe3e468cfd4b9bc2777f4", controller_id)
        )
        # The approved controller already resolves GetComponentInChildren<Animator>()
        # when no serialized Animator reference is available. This is required here
        # because the Animator is inside the imported FBX artifact, not a scene-local
        # Animator YAML block.
        created_blocks.append(
            _mono_block(
                controller_id,
                stripped_go_id,
                guid_controller,
                "  cameraTransform: {fileID: 0}\n"
                "  animator: {fileID: 0}\n"
                "  walkSpeed: 3\n"
                "  sprintSpeed: 5.5\n"
                "  rotationSpeed: 720\n"
                "  jumpHeight: 1.2\n"
                "  gravity: -20\n"
                "  standingHeight: 1.8\n"
                "  crouchingHeight: 1.1\n",
            )
        )

    if not re.search(r"(?m)^--- !u!143 &", scene):
        cc_id = next_id
        next_id += 1
        added_entries.append(
            _added_component_entry(int(source_root_gameobject),
                                   "c8b4ee65ffebe3e468cfd4b9bc2777f4", cc_id)
        )
        created_blocks.append(_character_controller_block(cc_id, stripped_go_id))

    if guid_camera not in existing_script_ids:
        camera_component_id = next_id
        next_id += 1
        # Camera is a normal scene-local GameObject, so its component is attached
        # directly to the Main Camera component list.
        camera_go_match = next(
            m for m in _blocks(scene)
            if m.group(1) == "1" and m.group(2) == str(camera_id)
        )
        camera_block = _block(scene, camera_go_match)
        camera_block = _append_component_to_gameobject(camera_block, camera_component_id)
        scene = scene[:camera_go_match.start()] + camera_block + scene[camera_go_match.end():]
        created_blocks.append(
            _mono_block(
                camera_component_id,
                camera_id,
                guid_camera,
                f"  target: {{fileID: {stripped_transform_id}}}\n"
                "  distance: 4.5\n"
                "  height: 1.6\n"
                "  lookHeight: 1.25\n"
                "  mouseSensitivity: 3\n"
                "  minPitch: -25\n"
                "  maxPitch: 65\n"
                "  followSharpness: 18\n",
            )
        )

    if added_entries:
        # Re-find the PrefabInstance after the camera block edit.
        prefab_match = next(
            m for m in _blocks(scene)
            if m.group(1) == "1001"
            and f"guid: c8b4ee65ffebe3e468cfd4b9bc2777f4" in _block(scene, m)
        )
        scene = _add_prefab_components(scene, prefab_match, added_entries)

    # Place stripped placeholders and newly-added component objects in the scene.
    appended = []
    if stripped_go_block:
        appended.append(stripped_go_block)
    if stripped_transform_block:
        appended.append(stripped_transform_block)
    appended.extend(created_blocks)
    if appended:
        scene = _append_block(scene, "\n".join(appended))

    workspace.write_file(scene_path, scene)
    return [scene_path] + [p + ".meta" for p in SCRIPT_PATHS]
