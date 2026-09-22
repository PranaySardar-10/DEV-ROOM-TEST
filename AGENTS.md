# DevRoom Agent Instructions

## Mission

DevRoom is the production factory for the main game project. It is not an experimental playground.

## Production workflow

1. Lead validates the goal and bounds the task.
2. Architect produces design, interfaces, dependencies, and acceptance criteria.
3. Coder produces a concrete implementation proposal.
4. Human/ChatGPT review decides whether the proposal may proceed.
5. Implementer integrates only the approved proposal into the assigned workspace.
6. QA runs automated validation and reports evidence.
7. Human opens the Unity project and validates the actual runtime/gameplay result.
8. Approval completes the task; a rejection becomes a correction instruction and returns to the Coder.

## Authority

- The human remains the final authority.
- No agent may silently skip a human gate.
- No agent may self-approve its own work.
- ChatGPT review is represented by the human-review gate, not by an autonomous provider pretending to be ChatGPT.
- Git is the durable project state and audit trail.

## Role boundaries

- Lead: read-only coordination.
- Architect: read-only design.
- Coder: read-only proposal generation; no production integration.
- Implementer: workspace-write, only after explicit human approval.
- QA: read-only evidence gathering.
- Unity validation: human-controlled runtime/gameplay validation.

## Provider strategy

The production workforce uses local Ollama agents. Provider names are configuration, not workflow logic. Codex is historical infrastructure and must not be treated as the active production workforce.

## Factory milestone

The immediate milestone is to make the production workflow enforceable, then validate it with a small real factory task before game production begins.
