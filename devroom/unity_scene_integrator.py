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
    return list(re.finditer(r"(?ms)^--- !u!(\\d+) &(-?\\d+)\\n.*?(?=^--- !u!|\\Z)", text))


def _block(text: str, match) -> str:
    return match.group(0)


def _field(block: str, name: str) -> str | None:
    m = re.search(rf"(?m)^\\s*{re.escape(name)}:.*?fileID: (-?\\d+)", block)
    return m.group(1) if m else None


def _object_name(block: str) -> str | None:
    m = re.search(r"(?m)^  m_Name: (.*)$", block)
    return m.group(1).strip() if m else None


def _append_component_to_gameobject(block: str, component_id: int) -> str:
    if re.search(rf"fileID: {component_id}\\}}", block):
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
    ids = [int(m.group(2)) for m in _blocks(scene)]
    next_id = max(ids + [1000]) + 1

    guid_input = ensure_script_meta(workspace, SCRIPT_PATHS[0])
    guid_controller = ensure_script_meta(workspace, SCRIPT_PATHS[1])
    guid_camera = ensure_script_meta(workspace, SCRIPT_PATHS[2])

    matches = _blocks(scene)
    gameobjects = {m.group(2): m for m in matches if m.group(1) == "1"}
    animators = [m for m in matches if m.group(1) == "95"]
    cameras = [m for m in matches if m.group(1) == "20"]

    if not animators:
        raise RuntimeError("CharacterTest.unity contains no Animator component to identify Joe.")
    joe_animator = next(
        (
            m for m in animators
            if (_object_name(gameobjects.get(_field(_block(scene, m), "m_GameObject"), m)) or "").lower()
            in {"joe", "character"}
        ),
        animators[0],
    )
    joe_id = int(_field(_block(scene, joe_animator), "m_GameObject") or 0)
    if joe_id == 0:
        raise RuntimeError("Could not resolve Joe GameObject from its Animator.")

    camera_match = next(
        (
            m for m in cameras
            if (_object_name(gameobjects.get(_field(_block(scene, m), "m_GameObject"), m)) or "").lower()
            == "main camera"
        ),
        cameras[0] if len(cameras) == 1 else None,
    )
    if camera_match is None:
        raise RuntimeError("Could not uniquely identify the Main Camera in CharacterTest.unity.")
    camera_id = int(_field(_block(scene, camera_match), "m_GameObject") or 0)

    # Re-read after meta creation so this remains idempotent.
    scene = workspace.read_file(scene_path)
    matches = _blocks(scene)
    ids = [int(m.group(2)) for m in matches]
    next_id = max(ids + [1000]) + 1
    gameobjects = {m.group(2): m for m in matches if m.group(1) == "1"}

    # Resolve component lists from the refreshed blocks.
    joe_block_match = gameobjects[str(joe_id)]
    camera_block_match = gameobjects[str(camera_id)]
    joe_block = _block(scene, joe_block_match)
    camera_block = _block(scene, camera_block_match)

    existing_script_ids = set(re.findall(r"guid: ([0-9a-f]{32})", scene))
    created_blocks: list[str] = []

    if guid_input not in existing_script_ids:
        input_id = next_id; next_id += 1
        joe_block = _append_component_to_gameobject(joe_block, input_id)
        created_blocks.append(_mono_block(input_id, joe_id, guid_input, ""))
    else:
        input_id = None

    if guid_controller not in existing_script_ids:
        controller_id = next_id; next_id += 1
        joe_block = _append_component_to_gameobject(joe_block, controller_id)
        animator_id = int(joe_animator.group(2))
        created_blocks.append(
            _mono_block(
                controller_id,
                joe_id,
                guid_controller,
                f"  cameraTransform: {{fileID: 0}}\n"
                f"  animator: {{fileID: {animator_id}}}\n"
                "  walkSpeed: 3\n"
                "  sprintSpeed: 5.5\n"
                "  rotationSpeed: 720\n"
                "  jumpHeight: 1.2\n"
                "  gravity: -20\n"
                "  standingHeight: 1.8\n"
                "  crouchingHeight: 1.1\n",
            )
        )
    if not re.search(r"(?m)^CharacterController:\\n", scene):
        cc_id = next_id; next_id += 1
        joe_block = _append_component_to_gameobject(joe_block, cc_id)
        created_blocks.append(_character_controller_block(cc_id, joe_id))

    if guid_camera not in existing_script_ids:
        camera_component_id = next_id; next_id += 1
        camera_block = _append_component_to_gameobject(camera_block, camera_component_id)
        created_blocks.append(
            _mono_block(
                camera_component_id,
                camera_id,
                guid_camera,
                f"  target: {{fileID: {joe_id}}}\n"
                "  distance: 4.5\n"
                "  height: 1.6\n"
                "  lookHeight: 1.25\n"
                "  mouseSensitivity: 3\n"
                "  minPitch: -25\n"
                "  maxPitch: 65\n"
                "  followSharpness: 18\n",
            )
        )

    # Replace only the two existing GameObject blocks, preserving all other scene text.
    scene = scene[:joe_block_match.start()] + joe_block + scene[joe_block_match.end():]
    # Match positions changed; re-find camera block in updated text.
    camera_matches = _blocks(scene)
    camera_go = next(m for m in camera_matches if m.group(1) == "1" and m.group(2) == str(camera_id))
    camera_block = _block(scene, camera_go)
    scene = scene[:camera_go.start()] + camera_block + scene[camera_go.end():]
    if created_blocks:
        scene = _append_block(scene, "\n".join(created_blocks))

    workspace.write_file(scene_path, scene)
    return [scene_path] + [p + ".meta" for p in SCRIPT_PATHS]