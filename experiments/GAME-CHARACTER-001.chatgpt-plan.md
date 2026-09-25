# GAME-CHARACTER-001 — DIRECT CHATGPT IMPLEMENTATION ARTIFACT PLAN

## APPROVAL CONTRACT

This document is the complete implementation artifact plan authored by ChatGPT.

The constrained Implementer must apply these artifacts and the exact scene/component configuration below. It must NOT redesign the controller, choose different architecture, invent additional systems, or ask a local model to generate missing code.

The only implementation decisions left to the Implementer are mechanical integration details required to attach these exact artifacts to the already-existing Joe and CharacterTest scene.

## OBJECTIVE

Create the minimal deterministic third-person playable Joe prototype in:

`D:\OMNIVERSEL ROLEPLAY\OMNIVERSEL ROLEPLAY`

Unity 6000.6.2f1 URP.

Existing Joe/character FBX, valid Humanoid Avatar, existing walking clip, and existing JoeAnimator/Controller must be reused.

Do not modify `Assets/Omniversel/Tests/FoundationTest.unity`.
Do not change GPU Resident Drawer.

## ARTIFACTS TO CREATE

Create exactly these three runtime scripts:

- `Assets/Omniversel/Gameplay/Character/OmniverselCharacterInput.cs`
- `Assets/Omniversel/Gameplay/Character/OmniverselCharacterController.cs`
- `Assets/Omniversel/Gameplay/Character/OmniverselThirdPersonCamera.cs`

No additional runtime scripts are authorized.

These scripts use Unity's built-in legacy Input API behind one centralized input component. This keeps keyboard/mouse checks out of gameplay logic and avoids introducing a new package dependency for this minimal prototype. Unity 6 documents `Input.GetAxisRaw` as the unsmoothed virtual-axis API and notes that the newer Input System is preferred for new projects; for this prototype, the centralized input boundary is deliberate and can later be replaced without changing controller/camera contracts. citeturn5search0

## ARTIFACT 1

### Assets/Omniversel/Gameplay/Character/OmniverselCharacterInput.cs

```csharp
using UnityEngine;

namespace Omniversel.Gameplay.Character
{
    public sealed class OmniverselCharacterInput : MonoBehaviour
    {
        public Vector2 Move
        {
            get
            {
                return Vector2.ClampMagnitude(
                    new Vector2(
                        Input.GetAxisRaw("Horizontal"),
                        Input.GetAxisRaw("Vertical")),
                    1f);
            }
        }

        public bool SprintHeld =>
            Input.GetKey(KeyCode.LeftShift) || Input.GetKey(KeyCode.RightShift);

        public bool JumpPressed => Input.GetKeyDown(KeyCode.Space);

        public bool CrouchHeld => Input.GetKey(KeyCode.C);

        public bool CameraRotateHeld => Input.GetMouseButton(0);

        public Vector2 LookDelta
        {
            get
            {
                if (!CameraRotateHeld)
                {
                    return Vector2.zero;
                }

                return new Vector2(
                    Input.GetAxisRaw("Mouse X"),
                    Input.GetAxisRaw("Mouse Y"));
            }
        }

        public bool ContextActionPressed => Input.GetMouseButtonDown(1);
    }
}
```

## ARTIFACT 2

### Assets/Omniversel/Gameplay/Character/OmniverselCharacterController.cs

```csharp
using System;
using UnityEngine;

namespace Omniversel.Gameplay.Character
{
    [RequireComponent(typeof(CharacterController))]
    [RequireComponent(typeof(OmniverselCharacterInput))]
    public sealed class OmniverselCharacterController : MonoBehaviour
    {
        [Header("References")]
        [SerializeField] private Transform cameraTransform;
        [SerializeField] private Animator animator;

        [Header("Movement")]
        [SerializeField] private float walkSpeed = 3.0f;
        [SerializeField] private float sprintSpeed = 5.5f;
        [SerializeField] private float rotationSpeed = 720.0f;

        [Header("Vertical Movement")]
        [SerializeField] private float jumpHeight = 1.2f;
        [SerializeField] private float gravity = -20.0f;

        [Header("Crouch")]
        [SerializeField] private float standingHeight = 1.8f;
        [SerializeField] private float crouchingHeight = 1.1f;

        public event Action ContextActionRequested;

        public bool IsGrounded => _characterController.isGrounded;
        public bool IsSprinting { get; private set; }
        public bool IsCrouching { get; private set; }
        public float VerticalVelocity => _verticalVelocity;

        private CharacterController _characterController;
        private OmniverselCharacterInput _input;
        private float _verticalVelocity;
        private float _standingCenterY;

        private static readonly int SpeedHash = Animator.StringToHash("Speed");
        private static readonly int IsSprintingHash = Animator.StringToHash("IsSprinting");
        private static readonly int IsCrouchingHash = Animator.StringToHash("IsCrouching");
        private static readonly int GroundedHash = Animator.StringToHash("Grounded");
        private static readonly int VerticalVelocityHash = Animator.StringToHash("VerticalVelocity");

        private void Awake()
        {
            _characterController = GetComponent<CharacterController>();
            _input = GetComponent<OmniverselCharacterInput>();

            if (animator == null)
            {
                animator = GetComponentInChildren<Animator>();
            }

            if (cameraTransform == null && Camera.main != null)
            {
                cameraTransform = Camera.main.transform;
            }

            standingHeight = Mathf.Max(standingHeight, _characterController.radius * 2f);
            crouchingHeight = Mathf.Clamp(
                crouchingHeight,
                _characterController.radius * 2f,
                standingHeight);

            if (_characterController.height > 0f)
            {
                standingHeight = _characterController.height;
            }

            _standingCenterY = _characterController.center.y;
        }

        private void Update()
        {
            UpdateCrouch();
            UpdateMovement();
            UpdateVerticalMovement();
            UpdateAnimation();
            HandleContextAction();
        }

        private void UpdateCrouch()
        {
            bool wantsCrouch = _input.CrouchHeld;

            if (wantsCrouch)
            {
                SetCrouching(true);
            }
            else
            {
                SetCrouching(false);
            }
        }

        private void SetCrouching(bool crouching)
        {
            if (IsCrouching == crouching)
            {
                return;
            }

            IsCrouching = crouching;

            float targetHeight = IsCrouching ? crouchingHeight : standingHeight;
            _characterController.height = targetHeight;

            Vector3 center = _characterController.center;
            center.y = IsCrouching
                ? _standingCenterY - (standingHeight - targetHeight) * 0.5f
                : _standingCenterY;
            _characterController.center = center;
        }

        private void UpdateMovement()
        {
            Vector2 input = _input.Move;

            if (input.sqrMagnitude <= 0.0001f)
            {
                IsSprinting = false;
                return;
            }

            Vector3 forward = cameraTransform != null
                ? cameraTransform.forward
                : Vector3.forward;

            Vector3 right = cameraTransform != null
                ? cameraTransform.right
                : Vector3.right;

            forward.y = 0f;
            right.y = 0f;

            forward.Normalize();
            right.Normalize();

            Vector3 movement = (forward * input.y) + (right * input.x);
            movement = Vector3.ClampMagnitude(movement, 1f);

            IsSprinting = !_input.CrouchHeld && _input.SprintHeld;

            float speed = IsSprinting ? sprintSpeed : walkSpeed;
            Vector3 horizontalMotion = movement * speed;

            if (movement.sqrMagnitude > 0.0001f)
            {
                Quaternion targetRotation = Quaternion.LookRotation(movement, Vector3.up);
                transform.rotation = Quaternion.RotateTowards(
                    transform.rotation,
                    targetRotation,
                    rotationSpeed * Time.deltaTime);
            }

            _characterController.Move(horizontalMotion * Time.deltaTime);
        }

        private void UpdateVerticalMovement()
        {
            if (_characterController.isGrounded)
            {
                if (_verticalVelocity < 0f)
                {
                    _verticalVelocity = -2f;
                }

                if (_input.JumpPressed && !IsCrouching)
                {
                    _verticalVelocity = Mathf.Sqrt(jumpHeight * -2f * gravity);
                }
            }

            _verticalVelocity += gravity * Time.deltaTime;
            _characterController.Move(
                Vector3.up * (_verticalVelocity * Time.deltaTime));
        }

        private void UpdateAnimation()
        {
            if (animator == null)
            {
                return;
            }

            Vector2 move = _input.Move;
            float movementAmount = Mathf.Clamp01(move.magnitude);

            animator.speed = movementAmount > 0.001f
                ? (IsSprinting ? 1.35f : 1.0f)
                : 0f;

            SetFloatIfPresent(SpeedHash, movementAmount);
            SetBoolIfPresent(IsSprintingHash, IsSprinting);
            SetBoolIfPresent(IsCrouchingHash, IsCrouching);
            SetBoolIfPresent(GroundedHash, _characterController.isGrounded);
            SetFloatIfPresent(VerticalVelocityHash, _verticalVelocity);
        }

        private void HandleContextAction()
        {
            if (_input.ContextActionPressed)
            {
                ContextActionRequested?.Invoke();
            }
        }

        private void SetFloatIfPresent(int hash, float value)
        {
            if (HasParameter(hash, AnimatorControllerParameterType.Float))
            {
                animator.SetFloat(hash, value);
            }
        }

        private void SetBoolIfPresent(int hash, bool value)
        {
            if (HasParameter(hash, AnimatorControllerParameterType.Bool))
            {
                animator.SetBool(hash, value);
            }
        }

        private bool HasParameter(int hash, AnimatorControllerParameterType type)
        {
            foreach (AnimatorControllerParameter parameter in animator.parameters)
            {
                if (parameter.nameHash == hash && parameter.type == type)
                {
                    return true;
                }
            }

            return false;
        }
    }
}
```

## ARTIFACT 3

### Assets/Omniversel/Gameplay/Character/OmniverselThirdPersonCamera.cs

```csharp
using UnityEngine;

namespace Omniversel.Gameplay.Character
{
    public sealed class OmniverselThirdPersonCamera : MonoBehaviour
    {
        [SerializeField] private Transform target;
        [SerializeField] private float distance = 4.5f;
        [SerializeField] private float height = 1.6f;
        [SerializeField] private float lookHeight = 1.25f;
        [SerializeField] private float mouseSensitivity = 3.0f;
        [SerializeField] private float minPitch = -25.0f;
        [SerializeField] private float maxPitch = 65.0f;
        [SerializeField] private float followSharpness = 18.0f;

        private OmniverselCharacterInput _input;
        private float _yaw;
        private float _pitch = 12.0f;

        private void Awake()
        {
            if (target == null)
            {
                OmniverselCharacterController controller =
                    FindFirstObjectByType<OmniverselCharacterController>();

                if (controller != null)
                {
                    target = controller.transform;
                }
            }

            if (target != null)
            {
                _input = target.GetComponent<OmniverselCharacterInput>();
                _yaw = target.eulerAngles.y;
            }
        }

        private void LateUpdate()
        {
            if (target == null)
            {
                return;
            }

            if (_input == null)
            {
                _input = target.GetComponent<OmniverselCharacterInput>();
            }

            if (_input != null && _input.CameraRotateHeld)
            {
                Vector2 look = _input.LookDelta;
                _yaw += look.x * mouseSensitivity;
                _pitch = Mathf.Clamp(
                    _pitch - (look.y * mouseSensitivity),
                    minPitch,
                    maxPitch);
            }

            Quaternion rotation = Quaternion.Euler(_pitch, _yaw, 0f);

            Vector3 focusPoint = target.position + Vector3.up * lookHeight;
            Vector3 desiredPosition =
                focusPoint
                - (rotation * Vector3.forward * distance)
                + (Vector3.up * (height - lookHeight));

            float interpolation = 1f - Mathf.Exp(-followSharpness * Time.deltaTime);
            transform.position = Vector3.Lerp(
                transform.position,
                desiredPosition,
                interpolation);

            transform.rotation = rotation;
        }
    }
}
```

## SCENE FILE IS A REQUIRED IMPLEMENTATION ARTIFACT

The scene wiring is **not documentation-only**. The Implementer must make a real serialized change to:

`Assets/Scenes/CharacterTest.unity`

The task MUST NOT be reported as implemented if the three scripts exist but CharacterTest.unity has not changed.

### Required serialized scene result

The Implementer must inspect the existing YAML scene and make the minimum serialized edits necessary to produce this exact component graph:

- Existing Joe/character root:
  - existing Transform preserved
  - existing Animator preserved
  - new CharacterController
  - new OmniverselCharacterInput
  - new OmniverselCharacterController
- Existing Main Camera:
  - existing Camera preserved
  - new OmniverselThirdPersonCamera
- No additional Camera.
- No Rigidbody on Joe.

The Implementer must resolve the actual fileIDs and script GUIDs from the workspace rather than inventing them.

### Deterministic implementation procedure

After creating the three scripts:

1. Read the generated `.cs.meta` files and use their actual GUIDs for the MonoBehaviour script references.
2. Read `Assets/Scenes/CharacterTest.unity`.
3. Identify the existing Joe/character root by locating the GameObject that owns the existing Animator component and the JoeAnimator controller.
4. Identify the existing Main Camera by its GameObject name/tag and existing Camera component.
5. Add the required CharacterController component to the Joe root with the exact values specified below.
6. Add OmniverselCharacterInput to the Joe root.
7. Add OmniverselCharacterController to the Joe root and serialize its Animator reference to the existing Joe Animator. Leave cameraTransform null.
8. Add OmniverselThirdPersonCamera to the existing Main Camera and serialize its target reference to the Joe root. Use the exact camera defaults specified below.
9. Preserve all unrelated serialized scene data byte-for-byte where practical; do not recreate the scene.
10. Save the resulting `CharacterTest.unity`.
11. Verify that the resulting YAML contains references to all three new script GUIDs and that the Joe/Main Camera component lists contain the expected components.
12. The Implementer result MUST list `Assets/Scenes/CharacterTest.unity` as an applied artifact.

### Required implementation artifact set

The successful implementation must report at least these four artifacts:

- `Assets/Omniversel/Gameplay/Character/OmniverselCharacterInput.cs`
- `Assets/Omniversel/Gameplay/Character/OmniverselCharacterController.cs`
- `Assets/Omniversel/Gameplay/Character/OmniverselThirdPersonCamera.cs`
- `Assets/Scenes/CharacterTest.unity`

If CharacterTest.unity is not actually modified, the Implementer must report failure instead of claiming completion.

## EXACT SCENE INTEGRATION

Use only `Assets/Scenes/CharacterTest.unity`.

Do not modify `FoundationTest.unity`.

### Joe / character GameObject

On the existing Joe/character root GameObject that already owns the existing Animator:

1. Add `CharacterController`.
2. Add `OmniverselCharacterInput`.
3. Add `OmniverselCharacterController`.
4. Keep the existing Animator and existing JoeAnimator/Controller unchanged.
5. Assign the existing Animator to `OmniverselCharacterController.animator`.
6. Leave `cameraTransform` unassigned; the controller resolves Main Camera automatically if present.
7. Set CharacterController:
   - Height: 1.8
   - Radius: 0.3
   - Center: (0, 0.9, 0)
   - Slope Limit: 45
   - Step Offset: 0.3
   - Skin Width: 0.08
   - Min Move Distance: 0
8. Do not add Rigidbody.

### Main Camera

On the existing Main Camera:

1. Keep its Camera component.
2. Add `OmniverselThirdPersonCamera`.
3. Leave target unassigned; it resolves the existing `OmniverselCharacterController`.
4. Keep the camera enabled.
5. Initial runtime behavior:
   - distance 4.5
   - height 1.6
   - lookHeight 1.25
   - mouseSensitivity 3
   - minPitch -25
   - maxPitch 65
   - followSharpness 18

If the scene has no Main Camera, create exactly one Main Camera and add the component. Do not create additional cameras.

### Animator

Do not replace JoeAnimator.

The existing Walking state remains the existing controller's default state.

The controller only writes optional parameters if they already exist:
- Speed (Float)
- IsSprinting (Bool)
- IsCrouching (Bool)
- Grounded (Bool)
- VerticalVelocity (Float)

Therefore no Animator Controller redesign is required in this task.

The existing Walking clip remains the movement animation. While there is movement, the existing Animator plays at normal speed; while sprinting, it plays at 1.35x. When stationary, the Animator is paused. This deliberately avoids inventing unavailable sprint/jump/crouch animation clips.

## INPUT CONTRACT

The single `OmniverselCharacterInput` component is the only location containing keyboard/mouse polling.

Bindings:

- Horizontal/Vertical axes: W/A/S/D through Unity's existing `Horizontal` and `Vertical` axes.
- Left Shift or Right Shift: sprint.
- Space: jump.
- C: crouch while held.
- Left mouse button held: enable camera rotation.
- Mouse X/Y while LMB is held: camera rotation.
- Right mouse button pressed: context-action hook.

The gameplay controller and camera do not directly poll keyboard or mouse state.

## RMB CONTEXT HOOK

`OmniverselCharacterController.ContextActionRequested` is an instance event.

This task does not subscribe combat code and does not implement attacks.

QA must verify that pressing RMB invokes the event path without producing combat, weapon, damage, or hit logic.

## FORBIDDEN

Do not add:
- networking/multiplayer
- authentication/accounts
- backend/database
- vehicles
- inventory/economy/shop
- weapons/combat
- NPC AI
- missions/quests
- world streaming
- save/load
- chat/voice
- monetization/admin/anti-cheat
- analytics/telemetry
- mobile-specific implementation
- Addressables
- ECS/DOTS
- DI/service locator
- third-party controller frameworks
- additional animation downloads
- FoundationTest modifications
- GPU Resident Drawer changes
- new assemblies

## IMPLEMENTER VERIFICATION

Before reporting completion:

1. Confirm the three exact scripts exist at the exact paths.
2. Confirm only CharacterTest is changed for scene integration.
3. Confirm FoundationTest has no Git diff.
4. Confirm existing Joe/avatar/Walking/JoeAnimator assets were reused.
5. Confirm no forbidden systems were introduced.
6. Confirm Unity compilation has no script errors.
7. Confirm CharacterController and Animator references are valid.
8. Confirm Main Camera has exactly one `OmniverselThirdPersonCamera`.
9. Confirm no Rigidbody was added to Joe.
10. Produce the deterministic changed-artifact report.

## QA VERIFICATION

QA must independently inspect actual workspace evidence and verify:

- all three scripts exist and match the approved artifacts
- no unauthorized scripts were added
- CharacterTest changed only within this task's scope
- FoundationTest is unchanged
- Joe retains Humanoid Avatar and existing Animator Controller
- no forbidden system exists
- CharacterController configuration is valid
- input polling is centralized in OmniverselCharacterInput
- controller uses CharacterController.Move for movement
- camera follows and rotates around Joe
- RMB only raises the context-action event
- compilation/static evidence is clean

Unity's CharacterController is appropriate here because it provides collision-constrained movement through Move without requiring a Rigidbody; Unity documents that Move does not apply gravity automatically, which is why the controller explicitly applies its own deterministic gravity. citeturn1search7turn1search6

## HUMAN UNITY VALIDATION

After QA approval, human validation in CharacterTest:

1. Enter Play Mode.
2. Confirm Joe is visible.
3. W/A/S/D moves Joe.
4. Joe rotates toward movement.
5. Shift changes to sprint speed/animation playback.
6. Space jumps.
7. Hold C crouches and release C restores standing height.
8. Hold LMB and move mouse rotates the third-person camera.
9. Camera follows Joe.
10. RMB invokes the context-action path without combat.
11. Walking animation plays during movement.
12. Stop Play Mode.
13. Enter Play Mode again.
14. Confirm no new errors.

## ACCEPTANCE

The task is complete only after:

**ChatGPT artifact approval → Implementer applies exact artifacts → independent QA passes → human Unity validation passes.**

No local Lead, Architect, or Coder regeneration is part of this direct ChatGPT workflow.
