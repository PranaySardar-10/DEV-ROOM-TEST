# BACKUP MEMORY FOR PROJECT
## DevRoom / Omniversel Roleplay — Continuity Snapshot
**Created:** 2026-09-24  
**Purpose:** Preserve the important project context, architecture, decisions, repository state, production workflow, and current debugging status so a future conversation can continue without reconstructing the work.

---

## 1. PROJECT IDENTITY

- Main game/project: **Omniversel Roleplay**.
- Intended project direction: Unity multiplayer/open-world real-life roleplay ecosystem, mobile-first eventually.
- Target production/launch planning reference: around **2028-02-01**.
- **DevRoom** is the AI development/orchestration factory intended to produce the main game.
- DevRoom is no longer treated as a random experiment. It is the **production factory build**.
- Human owner is the final authority.
- Git is the source of truth, audit trail, and recovery mechanism.

Core production principle:
**Finish factory → validate factory → inaugurate factory → use factory for game production.**

---

## 2. DEVROOM REPOSITORY

GitHub repository:
https://github.com/PranaySardar-10/DEV-ROOM-TEST

Important branches:
- `main`: production factory base.
- `devroom/factory-production-workflow`: factory foundation branch, merged through PR #6.
- `devroom/stall-timeout-role-contracts`: current hardening branch / PR #7.
- This backup branch: `backup/memory-for-project-2026-09-24`.

PR #6:
- Title: `factory: production workflow foundation`
- Base: `main`
- Merge commit: `453251c66d93c1c3107132b44d46770169582a1e`
- User explicitly approved the merge.
- After merge, local main was updated to that merge commit.
- Full suite after merge: **116 tests, OK**.

PR #7:
- Title: `factory: add stall-aware local execution and precise role contracts`
- Base: `main`
- Current head at backup creation: `7108db7dfb69a8613b32b500a47c83502ed5b299`
- State: **open, unmerged, mergeable**.
- Do NOT merge without explicit human approval.
- PR URL: https://github.com/PranaySardar-10/DEV-ROOM-TEST/pull/7

Current local validation immediately before this backup:
```
Ran 123 tests in 10.338s
OK
```

GitHub did not report individual status checks for the exact `7108db7` commit, so the local 123/123 suite is the confirmed validation result.

---

## 3. PRODUCTION WORKFLOW

Intended workflow:

Human/ChatGPT task/spec
→ Lead / Architect
→ Coder
→ Human + ChatGPT review
→ if rejected: correction/revision cycle
→ Implementer
→ QA
→ Human opens Unity and validates actual runtime/gameplay
→ if broken: correction command → Coder → review → implementation → QA → Unity
→ if valid: complete.

Roles:
- **Lead:** turns task into concise work brief.
- **Architect:** produces concrete implementation specification.
- **Coder:** produces reviewable implementation proposal.
- **Human/ChatGPT review:** approval gate.
- **Implementer:** applies only approved work within explicit allowed paths.
- **QA:** independently evaluates actual implementation evidence.
- **Unity validation:** human runtime validation.
- Human is authority; AI does not self-approve.

Privileges:
- Lead: read-only.
- Architect: read-only.
- Coder: proposal/read-only.
- Implementer: workspace-write, constrained to approved paths.
- QA: read-only.
- No AI merge to main without explicit human approval.

Git policy:
- Protected main.
- Task branches follow `agent/<role>/<task-id>`.
- Git is recovery/audit source of truth.

---

## 4. PR #6 / FACTORY FOUNDATION

PR #6 established the production workflow foundation.

Important earlier work:
- Windows state-store regression fixed in `devroom/state_store.py` at commit `2581e2f`.
  - Windows `os.replace` retry behavior was added.
  - Non-Windows behavior remained unchanged.
- Full suite reached 115/115.
- QA hardening at `ad8168c`, tests at `a9e3c6c`.
  - `devroom/orchestrator.py` independently collects actual workspace evidence before QA.
  - QA receives actual files, Git status, approved paths, and actual file contents.
  - QA does not rely solely on implementation-agent claims.
- Full suite reached 116/116.
- Real smoke tests `smoke-test-001` and `smoke-test-002` successfully passed the workflow.
- Smoke file exact content:
  `DEVROOM_SMOKE_TEST_OK`.

---

## 5. PR #7 — STALL-AWARE EXECUTION

Problem:
- Original local model execution used a hard 600-second total timeout.
- Gemma startup/generation can take several minutes.
- A hard wall-clock timeout was the wrong failure model.

Implemented:
- New `devroom/process_runner.py`.
- `run_with_stall_timeout(command, stall_timeout_seconds)`.
- Uses `subprocess.Popen`, stdout/stderr pipes, background draining, and observable byte-level output activity.
- Process is terminated only when there is no observable output for the configured stall period.
- Default stall timeout: **1800 seconds / 30 minutes**.
- Legacy `timeout_seconds` config is migrated to a minimum 1800-second stall timeout.
- Qwen uses the same stall-aware execution.
- Workspace-agent configuration was updated to accept `stall_timeout_seconds`.
- A previous production startup issue occurred because `LocalOllamaWorkspaceAgent.__init__` did not accept the new configuration; this was fixed and tested.

Real local model checks:
- `qwen2.5-coder:3b` exact test output succeeded in roughly 15 seconds.
- `gemma4:e4b` exact test output succeeded after roughly 4–5 minutes of startup/generation.
- This demonstrated why stall-aware execution is required.

---

## 6. LOCAL MODELS

Installed through Ollama at the time of this work:
- `qwen3.5:4b` — ~3.4 GB.
- `gemma4:e4b` — ~9.6 GB.
- `qwen2.5-coder:3b` — ~1.9 GB.
- `qwen2.5-coder:1.5b` — ~986 MB.

Preference/observations:
- Gemma4:e4b was somewhat slower to start but was preferred for quality over qwen3.5:4b.
- qwen2.5-coder:3b is used for the Implementer/local coding path.

---

## 7. THE IMPORTANT ROLE-CONTRACT FAILURE

Production task:
`GAME-FOUNDATION-001.md`

Goal:
**Create the minimal, deterministic Omniversel Roleplay Unity project foundation.**

The first real production run exposed a major problem:
- Architect was assigned Architect but produced a full QA report.
- Coder was assigned Coder but also followed QA instructions.
- Both exposed “Thinking Process”.
- Architect simulated implementation and declared every QA field PASS despite having no implementation evidence.
- Coder also simulated successful completion.

Example failure pattern:
```
The final output must be the QA Report structure...
simulate the successful outcome
STRUCTURE: PASS
ASSEMBLIES: PASS
...
```

Human correctly rejected the proposal with feedback that:
- Architect must produce only implementation specification.
- Coder must produce only reviewable implementation proposal.
- Neither may produce QA PASS/FAIL.
- Neither may simulate implementation/validation.
- QA reporting belongs only to QA after evidence exists.

This was the central issue being fixed.

---

## 8. WHY THE FIRST PROMPT FIX WAS NOT ENOUGH

Original local provider prompt construction placed task specification into generic context.

Even though the prompt said context was “data”, the task specification itself contained imperative sections such as:
- QA report format.
- Human Unity validation.
- Completion instructions.

Small local models, especially Gemma in this workflow, treated those embedded instructions as executable instructions.

Adding more natural-language warnings alone did not solve it.

The real solution became:
**Do not expose downstream workflow instructions to upstream roles in the first place.**

---

## 9. ROLE-SPECIFIC TASK SPECIFICATION FIX

Current orchestrator contains a role-specific task specification view.

Function:
`task_specification_for_role(role)`

Behavior:
- QA receives the complete task specification.
- Non-QA roles receive a filtered specification.
- The following downstream sections are excluded for non-QA roles:
  - `## QA`
  - `## Human Unity validation`
  - `## Completion`
- The complete original specification is still preserved in workflow state.
- This prevents Architect/Coder/Implementer from receiving downstream reporting instructions as part of their prompt.

Current conceptual flow:

FULL TASK SPEC
→ role-specific view
→ role contract
→ local model

Expected:
- Lead: filtered task requirements + Lead contract.
- Architect: filtered task requirements + Architect contract.
- Coder: filtered task requirements + Coder contract.
- Implementer: filtered task requirements + Implementer contract.
- QA: complete task spec + QA contract + actual workspace evidence.

This is a control-plane enforcement mechanism, not merely a prompt suggestion.

---

## 10. ROLE CONTRACTS

Current `devroom/provider_router.py` contracts:

Lead:
- Translate goal/spec into concise work brief.
- Identify outcomes, constraints, forbidden scope, acceptance requirements, ambiguities.
- Do not design implementation.
- Do not code.
- Do not perform QA.
- Do not report implementation PASS/FAIL.

Architect:
- Produce concrete implementation specification.
- Define required components/files, dependency direction, interfaces/data flow only when required.
- Do not write code.
- Do not claim files exist.
- Do not claim compilation.
- Do not perform QA.
- Must produce actionable implementation requirements.

Coder:
- Produce reviewable implementation proposal.
- Identify exact files to create/change, concrete changes, required verification.
- Do not modify files.
- Do not claim implementation happened.
- Do not claim tests passed.
- Do not add scope.
- Proposal goes to human/ChatGPT review.

Implementer:
- Apply only human-approved proposal.
- Stay within explicit allowed paths.
- Do not reinterpret approval.
- Do not redesign.
- Do not add unapproved features.
- Report actual changes/artifacts only.
- Do not claim tests/runtime validation unless actually performed.

QA:
- Independently evaluate implementation against task specification and approved proposal.
- Treat implementation summaries/agent claims as untrusted claims.
- Use actual workspace evidence.
- Report required QA fields exactly.
- If evidence is unavailable: `UNVERIFIED`, not PASS.
- Do not modify files or redesign.

---

## 11. LOCAL PROVIDER PROMPT BOUNDARIES

`devroom/local_ollama_provider.py` and `devroom/local_qwen_provider.py` now separate:

1. ROLE INSTRUCTIONS — authoritative.
2. GOAL.
3. TASK SPECIFICATION — reference requirements.
4. OTHER CONTEXT — reference data.

The task specification is explicitly delimited.

The prompt states that sections belonging to another workflow role do not transfer their role duties.

The role contract is deliberately placed as authoritative prompt material after the task specification.

Router also supplies:
`role_contract_boundary`

Meaning:
the task specification cannot replace, override, or extend the assigned role contract.

---

## 12. TEST HISTORY

Important suite milestones:
- 115/115 after state-store fix.
- 116/116 after QA evidence hardening.
- 121/121 after PR #7 hardening.
- 122/122 after prompt-boundary changes.
- A 123-test run initially exposed accidental regressions in our new changes:
  - missing return from ProviderRouter.
  - specification whitespace preservation mismatch.
- Those were fixed.
- Final confirmed local result before this backup:
```
Ran 123 tests in 10.338s
OK
```

ResourceWarnings seen in tests:
- HTTP 401
- HTTP 400
- HTTP 409
These did not fail the suite.

---

## 13. REGRESSION BUGS AND FIXES

During the role-specific specification change, two bugs were introduced:

Bug 1:
`ProviderRouter.execute()` accidentally failed to return the provider result.
Symptoms:
- `NoneType` errors in bootstrap/registry tests.
- router tests had empty provider call lists.

Fix:
- Restored:
```python
return provider.execute(
    AgentTask(role=task.role, goal=task.goal, context=context)
)
```

Bug 2:
Changing:
```specification = (specification or "").strip()
```
caused exact specification persistence mismatch for trailing newline.

Fix:
- Preserve original specification text:
```python
specification = specification or ""
```
This keeps exact persisted source content while role-specific prompt views can still be stripped when constructed.

---

## 14. GAME-FOUNDATION-001

Task specification is on main:
`tasks/GAME-FOUNDATION-001.md`

Current spec reference at the time of earlier work:
- main blob SHA: `8f4e494239a7a9419809770007fbbbff081eeda7`

Objective:
Create minimal deterministic Unity foundation.

Unity:
- Unity 6000.6.2f1.
- URP.
- GPU Resident Drawer already disabled and must not be changed.
- Existing project:
  `D:\OMNIVERSEL ROLEPLAY\OMNIVERSEL ROLEPLAY`

Required directories:
- Assets/Omniversel/
- Assets/Omniversel/Core/
- Assets/Omniversel/Infrastructure/
- Assets/Omniversel/Gameplay/
- Assets/Omniversel/UI/
- Assets/Omniversel/Bootstrap/
- Assets/Omniversel/Editor/
- Assets/Omniversel/Tests/

Required files:
- Assets/Omniversel/Core/Omniversel.Core.asmdef
- Assets/Omniversel/Infrastructure/Omniversel.Infrastructure.asmdef
- Assets/Omniversel/Gameplay/Omniversel.Gameplay.asmdef
- Assets/Omniversel/UI/Omniversel.UI.asmdef
- Assets/Omniversel/Bootstrap/Omniversel.Bootstrap.asmdef
- Assets/Omniversel/Editor/Omniversel.Editor.asmdef
- Assets/Omniversel/Tests/Omniversel.Tests.asmdef
- Assets/Omniversel/Bootstrap/FoundationBootstrap.cs
- Assets/Omniversel/Tests/FoundationTest.unity

Assembly boundaries:
- Core has no dependencies on other Omniversel runtime assemblies.
- Infrastructure → Core only.
- Gameplay → Core + Infrastructure.
- UI → Core only.
- Bootstrap → Core + Infrastructure + Gameplay + UI.
- Editor is editor-only.
- Tests may reference target assemblies.
- No production assembly references Assembly-CSharp.
- No circular dependencies.
- No additional assemblies.

FoundationBootstrap:
- Namespace: Omniversel.Bootstrap
- MonoBehaviour: FoundationBootstrap
- deterministic initialization.
- exactly emits:
  `Omniversel Foundation initialized`
- initializes once per instance.
- no networking, database, backend, player, UI, file writes, PlayerPrefs, async init, persistent singleton, or hidden global state.

Test scene:
- Assets/Omniversel/Tests/FoundationTest.unity
- exactly one root GameObject named OmniverselFoundation with FoundationBootstrap.
- no gameplay/networking/player/camera-controller/UI/audio/other gameplay objects.

Forbidden scope includes:
networking, multiplayer, authentication, backend, database, player/character, vehicle, economy, inventory, weapons, NPCs, missions/quests, map/world streaming, save/load, server, matchmaking, chat/voice, account, monetization/shop/admin/anti-cheat/analytics/telemetry/AI/procedural generation/mobile controls/addressables/ECS-DOTS/dependency injection/service locator/third-party packages/speculative architecture.

Acceptance:
1. directories exist.
2. exact seven asmdefs.
3. dependencies correct/acyclic.
4. no Assembly-CSharp production reference.
5. bootstrap compiles/behaves exactly.
6. test scene correct.
7. Unity compiles.
8. Play Mode exact message.
9. Play Mode enter/exit twice cleanly.
10. clean Unity reopen.
11. Git changes limited to task.
12. no cache/secrets/unrelated files.

QA fields:
```
STRUCTURE: PASS/FAIL
ASSEMBLIES: PASS/FAIL
DEPENDENCIES: PASS/FAIL
COMPILATION: PASS/FAIL
BOOTSTRAP: PASS/FAIL
SCENE: PASS/FAIL
SCOPE: PASS/FAIL
GIT HYGIENE: PASS/FAIL
```
If evidence is missing, QA must not claim completion.

Human Unity validation:
Open FoundationTest.unity → Play Mode → verify exact message → exit → Play Mode again → verify again without errors.

---

## 15. PRODUCTION COMMAND

The real production command used:

```powershell
cd D:\DEV-ROOM-TEST
python -m devroom.cli `
  --config D:\DevRoom-local-config.json `
  --goal "Create the minimal, deterministic Omniversel Roleplay Unity project foundation." `
  --workspace "D:\OMNIVERSEL ROLEPLAY\OMNIVERSEL ROLEPLAY" `
  --spec-file "D:\DEV-ROOM-TEST\tasks\GAME-FOUNDATION-001.md" `
  --allowed-path "Assets/Omniversel" `
  --max-feedback-cycles 2 `
  --workflow-id GAME-FOUNDATION-001
```

Do not approve the human-review gate until Architect and Coder outputs are checked.

---

## 16. CURRENT NEXT STEP

At the moment of this backup:

**DO NOT merge PR #7 yet.**

The immediate next validation after the 123/123 deterministic suite was intended to be exactly one real production run with Gemma.

Expected Architect output:
- implementation specification only.
- no QA report.
- no simulated PASS.
- no fabricated validation.
- no exposed thinking process.

Expected Coder output:
- concrete implementation proposal only.
- no QA report.
- no simulated implementation/validation.

If this succeeds:
1. Human/ChatGPT reviews proposal.
2. Only if explicitly approved does Implementer run.
3. QA receives actual filesystem/Git evidence.
4. Human performs Unity validation.
5. Only then can workflow complete.
6. PR #7 itself still requires separate explicit human approval before merging.

If it fails again:
- do not repeatedly spend Gemma inference time.
- capture exact Architect/Coder prompt/output.
- inspect serialized prompt construction/control-plane logic.
- fix with deterministic unit tests before another real model run.

---

## 17. INTERRUPTION / STALL OBSERVATION

One production attempt was manually interrupted with Ctrl+C while `process_runner.py` was sleeping during the long stall window.

Observed traceback ended at:
`time.sleep(min(0.25, max(0.01, stall_timeout_seconds - idle_seconds)))`

This is worth hardening later:
- KeyboardInterrupt should ideally be handled cleanly.
- In-flight workflow state should remain coherent.
- Avoid ugly traceback where possible.
- Existing durable workflow machinery already tracks `in_flight_role`.

This was not the primary role-contract blocker and should not distract from the production validation unless it becomes necessary.

---

## 18. IMPORTANT PROJECT DECISIONS

- Do not add speculative architecture.
- Do not add more prompt complexity without evidence.
- Prefer enforcement in DevRoom control-plane code over asking local models to behave.
- Keep QA evidence-based.
- Keep human approval gates.
- Keep implementation scope explicit.
- Keep Git as source of truth.
- Do not let AI merge to main autonomously.
- Do not burn long Gemma runs for changes that can be tested with mocked providers.
- Real Unity runtime validation remains human-owned.

---

## 19. DEVROOM STATUS AT BACKUP

Factory foundation:
**Merged into main and validated.**

PR #7:
**Open / unmerged / mergeable.**

Latest branch head:
`7108db7dfb69a8613b32b500a47c83502ed5b299`

Latest local deterministic validation:
**123 tests — OK.**

Role-specific specification filtering:
**Implemented and unit-tested.**

Stall-aware local execution:
**Implemented and tested.**

QA workspace evidence:
**Implemented and tested.**

Real production task:
**Not yet successfully completed.**

Human Unity validation:
**Not yet reached for GAME-FOUNDATION-001.**

---

## 20. CONTINUATION RULE FOR A NEW CHAT

When continuing this project in a new conversation, start from this backup and the GitHub repository state.

First facts to establish:
1. Repository: `PranaySardar-10/DEV-ROOM-TEST`
2. Backup branch: `backup/memory-for-project-2026-09-24`
3. Development branch: `devroom/stall-timeout-role-contracts`
4. PR #7 is open/unmerged.
5. Latest known head: `7108db7`.
6. Latest known deterministic suite: 123/123 OK.
7. Do not rerun expensive Gemma until control-plane assumptions are checked.
8. Current intended next step is one controlled production validation of GAME-FOUNDATION-001.

The backup is a continuity document, not a replacement for the Git history. Always treat the actual repository, commits, task specification, and tests as authoritative over this narrative.


---

## 21. ONGOING CONTINUITY RULE

From 2026-09-24 onward, project-significant progress should be recorded in this backup memory branch so future conversations can continue from an up-to-date project state.

When a meaningful project action, decision, repository change, test result, architecture change, debugging discovery, production-run result, or next-step decision is completed, update `BACKUP_MEMORY_FOR_PROJECT.md` on `backup/memory-for-project-2026-09-24` with the new state.

The backup is a continuity aid; actual repository files, commits, task specifications, tests, and production evidence remain authoritative.
