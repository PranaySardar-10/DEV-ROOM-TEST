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


---

## 22. 2026-09-24 — PRODUCTION RUN ROLE-CONTAMINATION FIX

A real GAME-FOUNDATION-001 production run was halted at the human-review gate after the Architect output incorrectly identified itself as Lead and reproduced a simulated Lead "Thinking Process". The following Coder/proposal output then began treating the prior generated specification as an active interaction. This confirmed a real cross-stage free-form context contamination problem.

Concrete control-plane fix applied on development branch `devroom/stall-timeout-role-contracts`:
- The Lead stage remains part of the workflow for planning/audit visibility.
- Raw model-generated Lead output is no longer passed into the Architect context.
- Architect now derives its implementation specification directly from the authoritative role contract, goal, and role-filtered task specification.
- This removes a known contamination path instead of adding more prompt wording.
- Added a deterministic regression test asserting that the Architect task contains no `lead_summary` and no raw Lead output.

Commits on the development branch:
- `e461e8cde41f60070ecd464e1fd8570e7ee0d908` — isolate Architect from raw Lead output.
- `3005d5bf87d4a6615470d829e40b2ab3a1f68865` — add regression test for Lead→Architect isolation.

The fix has been committed to the PR #7 development branch but has NOT yet been locally executed against the 123-test suite in this conversation. Do not claim the suite passed until the user runs it or equivalent execution evidence is available.

Next execution path:
1. Pull/update the local development checkout to the new branch head.
2. Run the deterministic test suite.
3. If green, rerun exactly one GAME-FOUNDATION-001 Gemma production validation.
4. Inspect Architect and Coder outputs before human approval.
5. If clean, continue to Implementer → QA → human Unity validation.

Decision: stop adding speculative prompt complexity; use deterministic stage isolation and tests to eliminate the observed contamination path.


## 23. 2026-09-24 — DETERMINISTIC SUITE PASSED AFTER ROLE-ISOLATION FIX

The local development checkout was fast-forwarded to `3005d5b` on `devroom/stall-timeout-role-contracts`.

After the Lead→Architect isolation fix, the full deterministic test suite was executed successfully:
- `python -m unittest discover -s tests -v`
- **127 tests ran in 10.966 seconds — OK**.
- The new regression test `test_architect_isolated_from_raw_lead_output` passed.
- Existing local Ollama, orchestrator, provider-router, state-store, sandbox, workspace, and control/API tests also passed.
- ResourceWarning messages for temporary HTTP 401/400/409 cleanup appeared but did not fail the suite.

This is the first clean deterministic validation of the new contamination fix. The next step is one controlled real Gemma GAME-FOUNDATION-001 production run. Do not modify the architecture or add prompt complexity before observing that run.


## 24. 2026-09-24 — GEMMA OUTPUT TRUNCATION DIAGNOSIS AND GENERATION-BUDGET FIX

The controlled real GAME-FOUNDATION-001 production validation was run after the 127/127 deterministic suite.

Observed behavior:
- The Lead→Architect contamination fix is working: Architect no longer produced a Lead identity, QA report, fake PASS results, or exposed thinking process.
- However, the Architect output itself repeatedly stopped very early, before completing the implementation specification.
- The Coder then also stopped extremely early, often immediately after headings such as `**Directory Structure Creation:**`.
- The final run was correctly halted at the human-review gate without entering implementation.
- The task specification was inspected and is not unusually large; the non-QA role-filtering removes the downstream QA/Human Unity/Completion sections.
- The local Ollama provider was inspected and was not explicitly setting an output-token budget. This makes an implicit/default model generation limit a concrete suspect for the repeated short completions. The pattern is consistent with a generation-budget ceiling rather than the earlier role-contamination failure.

Concrete fix applied on `devroom/stall-timeout-role-contracts`:
- `LocalOllamaConfig` now has `num_predict: int = 4096`.
- The Ollama API payload now explicitly sends:
  `"options": {"num_predict": self.config.num_predict}`
- Invalid non-positive generation budgets are rejected.
- Added deterministic tests in `tests/test_local_ollama_generation_budget.py` covering:
  - default 4096 generation budget is serialized into the Ollama request;
  - custom generation budget is serialized correctly;
  - invalid generation budget is rejected.

Commits:
- `f4537e896928f5f4879b8c3166e2753f37287200` — fix: set explicit local Ollama generation budget
- `637134ac1e49471d2ed9b03508807b9e8e067326` — test: cover explicit Ollama generation budget

Current development branch head after these commits:
`637134ac1e49471d2ed9b03508807b9e8e067326`

Important:
- These new commits have been created remotely but have NOT yet been executed in the user's local checkout in this conversation.
- Do not claim the deterministic suite is still 127/127 after these changes until the user pulls and runs it.
- Do not run another expensive Gemma production task until the new deterministic tests pass.
- If the suite passes, rerun one controlled GAME-FOUNDATION-001 production validation and inspect the complete Architect/Coder outputs.


## 25. 2026-09-24 — GENERATION-BUDGET TEST FIX

The first local test run after the explicit `num_predict` fix produced **130 tests with 2 errors**, both in the newly added generation-budget tests. The production provider itself was not shown to fail; the failures came from the test fixture.

Root cause:
- The mocked Ollama streaming response in `tests/test_local_ollama_generation_budget.py` contained literal escaped `\\n` text instead of actual newline separators.
- `LocalOllamaProvider.execute()` correctly parses Ollama's streaming response line-by-line with `splitlines()`, so the malformed fixture produced no parsed message content and triggered the intended empty-output guard.

Concrete fix:
- Corrected the test fixture to use actual newline separators.
- Commit: `5ea33a306c9cc70709badd89df9c66fbab3f91c7` — `test: fix Ollama stream fixture newlines`.

Current state:
- The user's local checkout has not yet pulled this latest test-only fix.
- The correct next action is to pull the branch and rerun the deterministic suite.
- Do not run another Gemma production task until the full suite is green.


## 26. 2026-09-24 — CODER IMPLEMENTATION-COMPLETENESS GAP IDENTIFIED

After the deterministic suite reached 133/133 and the real GAME-FOUNDATION-001 workflow reached the human-review gate, the generated Coder proposal was reviewed and found incomplete. The proposal listed required directories and files but did not provide enough concrete implementation detail for the Implementer to execute safely without making design decisions.

Specific incompleteness observed in the proposal:
- It listed `Assets/Omniversel/Tests` as the scene-file creation item instead of the required `Assets/Omniversel/Tests/FoundationTest.unity`.
- It omitted the exact seven asmdef dependency relationships.
- It omitted the required `FoundationBootstrap.cs` namespace, class behavior, exact log message, and prohibited behaviors.
- It omitted the exact required test-scene structure: one root `OmniverselFoundation` GameObject with `FoundationBootstrap` and no extra gameplay/network/UI/audio objects.
- It omitted the required compilation, Play Mode, scope, and Git-hygiene verification requirements.

Human/ChatGPT review decision:
`request_changes` — do not allow implementation from an incomplete proposal.

Important process observation:
Repeated implementation-stage review failures are now recognized as a factory-quality pattern: upstream Architect/Coder outputs can be structurally descriptive but implementation-incomplete. Human Review should not repeatedly reconstruct missing implementation details. Instead, the DevRoom role contract should enforce completeness upstream.

New intended Coder contract direction:
- The Coder must produce an implementation-ready proposal.
- Every required directory/file must have an exact path and purpose.
- Every required file must specify concrete implementation requirements, dependencies, and verification.
- Every task requirement must be mapped to the proposal.
- The proposal must contain a completeness check confirming that all requirements, behaviors, dependencies, and constraints are covered.
- The Implementer must be able to execute the approved proposal without inventing architecture or making design decisions.
- The Coder must not modify files or claim implementation/tests/runtime validation.

Human Review principle refined:
The primary review question should be:
**“Can the Implementer execute this proposal exactly as approved without inventing or designing anything?”**
If the answer is no, request changes before implementation.

This is a control-plane/factory-quality improvement, not a reason to add speculative game architecture. The next implementation work should strengthen the Coder contract and add deterministic tests for proposal completeness before spending another expensive real-model production run.

The user explicitly requested that this and all subsequent meaningful project information be preserved in the ongoing backup branch `backup/memory-for-project-2026-09-24` for continuity in future chats. The starting-memory branch remains historical and must not be used for ongoing updates.


## 27. 2026-09-24 — IMPLEMENTATION-COMPLETENESS ENFORCEMENT ADDED

The incomplete Coder proposal problem was fixed at the DevRoom control-plane level rather than relying only on Human Review wording.

Changes on devroom/stall-timeout-role-contracts:
- provider_router.py strengthened the Architect contract:
  - every task requirement must map to concrete implementation requirements;
  - every required file/directory must include exact path, purpose, contents/structure, dependencies, and constraints;
  - required behaviors must be concretely specified;
  - the Architect must end with a REQUIREMENT COVERAGE CHECK;
  - implementation decisions must not be left for Coder/Implementer to invent.
- The Coder contract was strengthened:
  - proposal must be implementation-ready;
  - every file/directory needs exact path, purpose, concrete change/create instructions, dependencies, and constraints;
  - structured artifacts/scenes must specify exact structure/objects/fields, not merely a containing directory;
  - proposal must include a VERIFICATION PLAN;
  - proposal must end with a COMPLETENESS CHECK;
  - missing Architect detail must be identified rather than silently invented.
- orchestrator.py now performs a deterministic pre-review completeness gate for Coder output. A proposal is halted before Human Review if it lacks:
  - IMPLEMENTATION FILES/DIRECTORIES
  - CONCRETE CHANGES
  - DEPENDENCIES AND CONSTRAINTS
  - VERIFICATION PLAN
  - COMPLETENESS CHECK
- Mock workflow output was updated to satisfy the new contract.
- Deterministic tests were added for the validator and for halting an incomplete Coder proposal before Human Review.

Commits:
- f767d29cb4aa099ce92a74e20930fe64707a0686 — strengthen Architect/Coder implementation-completeness contracts.
- 8f1cbe8fdca2557d6fb0bc794f4fffa863b1b7c5 — reject incomplete Coder proposals before review.
- de2396070300f835901a0fea00fe110cad0a821b — keep mock Coder proposal contract-complete.
- 0b6b9aa297afcb631187cea5c3daa604327152ae — add deterministic completeness tests.

Current known development branch head: 0b6b9aa297afcb631187cea5c3daa604327152ae.

Important validation status:
- These changes have been committed remotely.
- The user has NOT yet run the updated deterministic suite after these changes.
- Do not claim the suite is green until the user pulls the branch and executes it.
- Only after the suite passes should another expensive real GAME-FOUNDATION-001 Gemma run be performed.


## 28. 2026-09-24 — CODER RETRY TEST FIX AND 136/136 GREEN

The deterministic DevRoom suite reached 136/136 after fixing a test-fixture call-counting bug.

The failing Coder retry tests had been double-counting non-Coder roles because their test-provider overrides appended the task and then called MockProvider.execute(), which appended the same task again. This made Lead/Architect/Implementer/QA appear to run twice even though the orchestrator was not doing so.

Fix:
- Test overrides now record calls themselves only when intercepting Coder; normal roles are recorded once by MockProvider.
- Commit: 651a3aded2332467c60400fd349e58ac8e816665 — `test: avoid double-counting non-Coder calls`.

Validation:
- User pulled 651a3ad.
- Full deterministic suite: 136 tests, 0 failures, 0 errors, status OK.
- The Coder incomplete-proposal retry tests passed.
- This established a real green baseline before the next production run.

## 29. 2026-09-24 — REAL PRODUCTION RUN EXPOSED PERSISTENT CODER OMISSION; WORKFLOW DESIGN REVISED

A real GAME-FOUNDATION-001 production run was attempted after the 136/136 deterministic suite passed.

Production result:
- Workflow halted at the Coder completeness check.
- Exact reason: missing `DEPENDENCIES AND CONSTRAINTS`, `VERIFICATION PLAN`, and `COMPLETENESS CHECK`.
- This demonstrates that the local model can still omit required proposal sections even though the control-plane validator correctly detects the omission.

The user proposed a workflow redesign:
- Remove the idea that DevRoom automatically generates a Coder repair feedback prompt.
- When Coder output is incomplete, DevRoom should show exactly what is missing and pause for the human.
- Human choices at this point should be:
  1. provide a corrective prompt to the Coder, which then reruns Coder only;
  2. halt the workflow.
- If Coder output is complete, continue through the normal Human Review approval flow.
- Lead and Architect must not be rerun merely because Coder needs correction.

Control-plane changes implemented on `devroom/stall-timeout-role-contracts`:
- `orchestrator.py` now makes incomplete Coder correction human-controlled instead of automatically inventing correction feedback.
- The incomplete proposal gate exposes the original proposal, deterministic missing-section validation, and explicit prompt-or-halt decision options.
- An incomplete proposal can never be approved for implementation; an approval attempt is converted to a halt.
- `cli.py` now presents `prompt/halt` for this incomplete-Coder gate rather than the normal approve/request_changes/halt menu.
- Coder task prompting was strengthened with a mandatory five-section pre-submission checklist and explicit self-check instruction:
  - IMPLEMENTATION FILES/DIRECTORIES
  - CONCRETE CHANGES
  - DEPENDENCIES AND CONSTRAINTS
  - VERIFICATION PLAN
  - COMPLETENESS CHECK
- Tests were updated to cover human-controlled correction and to assert that the missing requirements are surfaced to the human.

Latest commits:
- c4ddf3b7bf33228f5948d4fb4990053624184df8 — `change: make incomplete Coder proposals human-gated`
- d96315a225a3f929020555ccaf4a4395119c36e4 — `cli: offer prompt-or-halt for incomplete Coder proposals`
- 4d756842a3126f7c613b4cb3d6daf870a126e430 — `test: cover human-controlled Coder correction`
- cc4f03532e602a850eb68008b71d038844d8a49 — `test: assert human control on incomplete Coder output`
- 2bce35688bfafa9ac7e0c56c4c49cce6fb89fd31 — `test: capture incomplete Coder gate context`

Important validation status:
- The latest redesign commits have NOT yet been pulled and run by the user.
- Do not claim the 136/136 suite remains green after these changes until the user reruns it.
- If the updated suite passes, rerun GAME-FOUNDATION-001. On an incomplete Coder proposal, the intended behavior is now to stop at a human prompt-or-halt gate rather than automatically consume retries.


## 30. 2026-09-24 — HUMAN-GATE TEST REGRESSIONS FIXED; 136/136 GREEN

After pulling commit `8015c0075a63a88effd9c7cfd03052474a396c2e` (`test: fix human-gate regression assertions`), the user reran the complete deterministic suite.

Validation:
- `python -m unittest discover -s tests -v`
- **136 tests ran in 10.693 seconds — OK.**
- The previously broken `test_proposal_rejection_returns_to_coder` passed.
- `test_incomplete_coder_proposal_halts_after_feedback_limit` passed with the human-controlled halt reason.
- `test_incomplete_coder_proposal_requires_human_correction` passed.
- All other factory, provider, orchestration, control API, sandbox, workspace, state-store, and process-runner tests passed.
- ResourceWarnings for temporary HTTP cleanup remained non-fatal.

This establishes the current human-controlled incomplete-Coder gate as deterministically green.

Current development branch head:
`8015c0075a63a88effd9c7cfd03052474a396c2e`.

The deterministic suite is now validated after the human-gate redesign. The next real production validation is allowed, but PR #7 still requires explicit human approval before merge.

## 31. 2026-09-24 — HUMAN CORRECTIVE PROMPT PASTE FORMAT STANDARDIZED

During the next real GAME-FOUNDATION-001 production run, the new human gate appeared correctly:

- Coder produced an incomplete proposal.
- DevRoom displayed the missing requirements:
  - `DEPENDENCIES AND CONSTRAINTS`
  - `VERIFICATION PLAN`
  - `COMPLETENESS CHECK`
- DevRoom presented the intended `[prompt/halt]` choice instead of automatically generating repair feedback.

A practical CLI interaction issue was then discovered: a multiline corrective prompt pasted into the interactive PowerShell input was submitted after only its first line, so the complete corrective instruction did not reach the Coder. The user force-stopped the run.

The user then tested a **large single-line corrective prompt with no blank lines** in the same PowerShell prompt, and confirmed that the entire prompt was accepted correctly and submitted as intended.

New operational rule:
- For human corrective prompts at the incomplete-Coder gate, use **one continuous physical line**.
- Do not include blank lines or multiline formatting.
- Keep the prompt comprehensive but single-line so PowerShell/interactive CLI paste does not interpret line breaks as submission.
- Future corrective prompts supplied by ChatGPT for this gate should follow this single-line format.

This is an interaction/input-format workaround, not yet a DevRoom code change. Do not claim the CLI itself has been permanently fixed unless a code change and test are made.

Current production state:
- The interrupted run should not be treated as a successful GAME-FOUNDATION-001 completion.
- The Coder correction mechanism itself is now usable when the corrective prompt is pasted as one line.
- Next production attempt should continue only after the user starts a fresh controlled run.

## 32. Coder production-completion fix
- Real GAME-FOUNDATION-001 production runs repeatedly reached the human gate with an incomplete Coder proposal. The deterministic validator correctly rejected missing DEPENDENCIES AND CONSTRAINTS, VERIFICATION PLAN, and COMPLETENESS CHECK, but repeated human corrective prompts did not solve the underlying generation/completion issue.
- Root cause evidence: Gemma Coder output repeatedly stopped during CONCRETE CHANGES, even after multiple corrective prompts. This was treated as a Coder generation-completion problem rather than weakening the completeness gate.
- Fix committed on devroom/stall-timeout-role-contracts:
  - 587d5793e4fb123cb0542d42aa2ebb2995ba5e8d — Local Ollama provider now supports a per-task generation_num_predict override while retaining the normal default of 4096.
  - 0e6e2ae5453ede5e68fc6664c8b46854fd9ddcb1 — Orchestrator gives only the Coder role generation_num_predict=8192, preserving the smaller budget for other roles.
  - 5c4d61fa75ab08751c932e6d7d30a1024828bc3c — Coder role contract made concise/completion-focused: exactly five required sections, no task-spec reproduction, no generic preamble/planning, and explicit instruction to finish all five sections.
  - 6c842a1f041c56fb2c6ab5bfc609df2ebb123491 — Provider test added for generation-budget override.
  - e51a5649e2f51634acaae5717abacd2c592dd798 — Orchestrator test added to assert Coder receives the 8192 generation budget.
- Human-gated completeness behavior remains intact; this change does not auto-approve, auto-repair, or weaken the Coder validator.
- GitHub Actions did not report a workflow run for the latest commit, so the deterministic suite still needs to be run from the user's local checkout before treating the fix as verified.



## 33. 2026-09-25 — SIMPLIFIED TO ONE HUMAN REVIEW GATE WITH TARGETED ROLE CORRECTIONS

The user rejected the separate special-case incomplete-Coder human gate. The intended factory control flow is now:

Lead → Architect → Coder → **one normal Human Review gate** → Implementer → QA → Human Unity Validation.

The Human Review gate is the same gate regardless of whether the Coder proposal is complete or incomplete. It presents the proposal and, when applicable, deterministic validation findings. The human can:
- APPROVE when the proposal is implementation-ready.
- REQUEST_CHANGES and optionally target a specific role by prefixing the feedback, e.g. `Coder: ...` or `Architect: ...`.
- HALT.

Correction behavior:
- No role prefix defaults to Coder correction.
- `Coder: ...` reruns only Coder using the existing architecture plus the human's specific correction.
- `Architect: ...` reruns Architect with the correction, then Coder is rerun against the revised architecture.
- An incomplete Coder proposal cannot be approved; it must be corrected or halted.
- Lead/Architect are no longer rerun merely because Coder output is incomplete.
- There is no separate prompt/halt gate for incomplete Coder output.
- CLI uses the same `approve/request_changes/halt` interaction for normal Human Review; the user can mention the target role directly in the feedback.

Implementation commits on `devroom/stall-timeout-role-contracts`:
- `factory: simplify human review to one targeted correction gate` — removed the special incomplete-Coder gate and routed review corrections through the normal Human Review gate.
- `factory: use one standard human review prompt` — removed the CLI-specific `prompt/halt` branch.
- `tests: update human review flow for targeted role corrections` — updated regression expectations so ordinary proposal correction targets Coder by default / explicitly.

Important validation status:
- These latest simplification changes have been committed to the development branch but have NOT yet been run through the user's local 136+ deterministic test suite.
- Do not claim the suite is green until the user pulls/runs the updated branch.
- PR #7 remains open/unmerged and requires explicit human approval before merge.

## 34. 2026-09-25 — CHATGPT DIRECT IMPLEMENTATION EXPERIMENT CREATED

After the latest real GAME-FOUNDATION-001 run continued to fail because the local Coder repeatedly produced incomplete implementation proposals, the project direction was experimentally simplified.

Key design realization:
- ChatGPT can perform the architecture and coding reasoning directly.
- The local Coder role was acting as an unnecessary translation layer: it had to convert architecture into a complete proposal, and the small local model repeatedly failed at completion.
- The preferred experimental flow is now:
  **ChatGPT architecture + coding → Human approval → constrained Implementer → independent QA → Human Unity validation.**
- This is an experiment only. The existing production Lead/Architect/Coder workflow remains intact until the experiment is proven.

Experimental Git state:
- New branch: `devroom/chatgpt-implementer-qa-experiment`
- Base: PR #7 head `9fc97500055c5ebeae15fa44d165045077fa06f1`.
- Draft PR #8: `experiment: ChatGPT direct implementation workflow`
- PR #8 is open, draft, unmerged, and must not be merged until the experiment is validated.
- PR URL: https://github.com/PranaySardar-10/DEV-ROOM-TEST/pull/8

Experimental code changes:
- `devroom/orchestrator.py` now has an optional direct `implementation_plan` path. When supplied, it skips local Lead/Architect/Coder and enters the existing Human Review gate.
- After human approval, the existing constrained Implementer runs, then independent QA receives actual workspace evidence, followed by Human Unity Validation.
- Existing normal workflow is unchanged when `implementation_plan` is not supplied.
- `devroom/cli.py` now accepts:
  `--implementation-plan-file`
  for the experimental direct ChatGPT path.
- Added deterministic orchestration coverage in `tests/test_orchestrator.py` proving the direct path invokes only Implementer and QA before Unity validation.
- No automatic merge or production replacement was performed.

ChatGPT-authored GAME-FOUNDATION-001 implementation plan:
- Added:
  `experiments/GAME-FOUNDATION-001.chatgpt-plan.md`
- The plan contains concrete asmdef definitions/dependencies, FoundationBootstrap code, deterministic test-scene structure, fixed script/scene metadata requirements, forbidden-scope constraints, and verification requirements.
- The plan is intended to be human-reviewed before the Implementer is allowed to modify the Unity workspace.

Experimental branch comparison:
- Relative to PR #7 head `9fc97500055c5ebeae15fa44d165045077fa06f1`, the experiment currently contains 4 commits and 4 changed files.
- The branch head is `f3130997295ee1f7fbae919c1df140340b466944`.
- The four changed files are:
  - `devroom/cli.py`
  - `devroom/orchestrator.py`
  - `tests/test_orchestrator.py`
  - `experiments/GAME-FOUNDATION-001.chatgpt-plan.md`

Validation status:
- The experiment has been structurally created, but its full deterministic test suite has NOT yet been run in the user's local checkout.
- GitHub Actions had no workflow run reported for the experiment branch at the time of creation.
- Therefore do not claim the experimental path is validated yet.
- Next step is to pull `devroom/chatgpt-implementer-qa-experiment`, run the full deterministic suite, then run GAME-FOUNDATION-001 through the direct ChatGPT plan path.
- Human Unity validation has not yet been reached for this experiment.
- PR #8 must remain unmerged until the experiment demonstrates the desired behavior.

Important continuity decision:
- The historical `backup/starting-memory-game-development-2026-09-24` branch remains untouched.
- This live backup branch remains the ongoing project memory and must continue to receive meaningful DevRoom/Omniversel progress updates.



## 35. 2026-09-25 — CHATGPT DIRECT IMPLEMENTATION EXPERIMENT: FIRST END-TO-END SUCCESS

The direct ChatGPT implementation experiment has now completed its first successful GAME-FOUNDATION-001 end-to-end workflow.

Key workflow proven:
**ChatGPT architecture + coding → Human Review approval → constrained Implementer → independent QA → Human Unity Validation approval → COMPLETE.**

Important implementation/factory fixes made before the successful run:
- Implementer default generation budget increased from 4096 to 16384 for workspace implementation tasks.
- Directory-scoped allowed paths were fixed so nested files under `Assets/Omniversel` are permitted.
- In the direct ChatGPT experiment, the approved ChatGPT plan is now parsed deterministically into file artifacts instead of asking a small local model to regenerate the already-approved implementation plan as JSON.
- Deterministic extraction test added for approved ChatGPT plans.
- Frozen-dataclass test mocking issue fixed.
- QA evidence collection was fixed to expand directory scopes against actual files instead of attempting to read a directory as a file.
- Ollama request transport was fixed for large payloads: JSON is now sent through stdin using `curl.exe --data-binary @-` rather than placing the entire payload on the Windows command line. This resolved the observed WinError 206 command-length failure.
- Process runner now supports stdin payloads while retaining stdout/stderr draining and stall detection.
- Generation-budget tests were updated for stdin payloads.

Deterministic validation before the successful production run:
- Full local suite reached **143 tests, 0 failures, 0 errors — OK**.

Successful GAME-FOUNDATION-001 run:
- Correct Unity workspace used:
  `D:\\OMNIVERSEL ROLEPLAY\\OMNIVERSEL ROLEPLAY`
- Human Review displayed the ChatGPT-authored implementation plan and the user entered `approve`.
- Implementer reported:
  `Applied 11 file artifact(s) from the approved ChatGPT plan.`
- The 11 artifacts correspond to the seven required asmdefs, FoundationBootstrap.cs and its metadata, and FoundationTest.unity and its metadata.
- Workflow reached QA after implementation.
- Workflow then reached the Human Unity Validation gate.
- User approved the final Unity validation gate.
- Final CLI result:
  `DevRoom finished: complete`

Evidence from the successful terminal run is preserved in the conversation upload `Pasted text(20260925-060125).txt`; the implementation approval/application appears around lines 326-335 and the final Unity validation approval/completion around lines 331-365.

Important qualification:
- The terminal output shown in the captured run contains abbreviated QA evidence rather than the full eight-line QA PASS/FAIL report, so do not independently claim every individual QA field was visually verified from that output.
- What is established is that the workflow passed through the QA stage to Human Unity Validation, and the human approved the final Unity validation gate.
- The human Unity validation approval is a workflow gate approval; it is not a substitute for recording detailed manual observations if future audits require them.

Incident during this milestone:
- One attempted run used the mistyped workspace path `D:\\OMNIVERSAL ROLEPLAY\\OMNIVERSAL ROLEPLAY` and failed before implementation because the workspace did not exist.
- No project files were modified by that failed attempt.
- The corrected path was then used for the successful run.

Current experimental Git state:
- PR #8: `experiment: ChatGPT direct implementation workflow`
- Branch: `devroom/chatgpt-implementer-qa-experiment`
- PR #8 remains **open, draft, and unmerged**.
- Do NOT merge PR #8 until the human explicitly decides to promote the experiment.

Current project status:
- The direct ChatGPT implementation path is no longer merely structural; it has completed a real end-to-end GAME-FOUNDATION-001 workflow successfully.
- The next sensible action is to manually open the Unity project and independently inspect the generated foundation before treating the Unity foundation itself as fully validated outside the CLI workflow. This includes opening `FoundationTest.unity`, checking the one-root scene structure, entering Play Mode, verifying the exact log `Omniversel Foundation initialized`, exiting and entering Play Mode again, and checking for compile/runtime errors.
- After manual Unity inspection, update the backup again with the observed Unity result before making a merge/promotion decision for PR #8.


## 36. 2026-09-25 — UNITY FOUNDATION MANUAL VALIDATION CONFIRMED; FACTORY MILESTONE COMPLETED

The successful GAME-FOUNDATION-001 workflow was followed by direct manual inspection in Unity 6000.6.2f1.

Human Unity validation observations:
- `FoundationTest.unity` opened successfully in the Omniversel Roleplay Unity project.
- Hierarchy showed the expected single `OmniverselFoundation` root object.
- The Game view displayed `No cameras rendering`, which is expected because the foundation task intentionally requires no camera.
- Play Mode started successfully.
- Console showed the exact bootstrap message:
  `Omniversel Foundation initialized`
- Unity showed **0 errors** during the observed Play Mode run.
- One unrelated shader warning was visible concerning Edge Adaptive Spatial Upsampling; it was not an error and was outside the foundation implementation.
- Play Mode could be stopped normally.
- A subsequent Play Mode start again produced the expected behavior; the apparent visual duplication/freezing was confirmed to be limited to the Game view because Unity itself remained responsive and Play Mode could be stopped normally.
- No camera was added, because adding one would violate the required minimal foundation scene.

This confirms the important manual runtime behavior of the generated foundation: Unity can enter Play Mode, execute FoundationBootstrap, emit the required initialization log, and exit normally without foundation runtime errors.

### FACTORY MILESTONE

The project has now reached the intended major DevRoom factory milestone:

**DevRoom orchestration factory has been built, hardened, exercised, and used successfully to produce and manually validate the first Omniversel Roleplay Unity foundation.**

Proven production chain:
**ChatGPT architecture + coding → Human approval → constrained Implementer → independent QA → Human Unity validation → complete.**

Validation milestones now recorded:
- Deterministic DevRoom suite: **143/143 tests — OK** before the successful production run.
- GAME-FOUNDATION-001: successful end-to-end workflow.
- Implementer: 11 approved artifacts applied.
- QA stage reached successfully.
- Human Unity validation gate approved.
- Direct manual Unity inspection confirmed the expected scene structure and bootstrap runtime behavior.

The factory should now be treated as a **validated production foundation**, while PR #8 remains an experimental branch that still requires an explicit human decision before promotion/merge.

Important next decision:
- Do not immediately modify the validated foundation just because the factory milestone is complete.
- First preserve this state in Git/backup and then decide deliberately whether PR #8 should be promoted/merged and whether this direct ChatGPT implementation workflow should become the normal production path.
