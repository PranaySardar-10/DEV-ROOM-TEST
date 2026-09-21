# DevRoom Agent Instructions

## Mission
DevRoom is a provider-independent multi-agent software-development orchestrator.

## Core workflow
1. Lead validates the goal and breaks it into bounded tasks.
2. Architect produces design, interfaces, dependencies, and acceptance criteria.
3. Human Gate 1 approves the implementation plan.
4. Implementer works only within the assigned task scope.
5. Reviewer independently audits the proposed change.
6. QA independently validates behavior and evidence.
7. Lead produces the final report.
8. Human Gate 2 approves integration.

## Boundaries
- No agent may silently skip a human gate.
- Implementers do not self-certify their work.
- Reviewers do not directly bypass the implementation/review process.
- QA reports evidence; it does not modify implementation.
- The orchestrator must remain provider-independent.
- A provider may back multiple logical roles, but each role has its own instructions and context.
- Reviewer execution must receive an independent review context rather than inheriting implementation assumptions.
- Git is the durable project state; conversation history is not the source of truth.

## Provider strategy
- Codex is the primary high-capability provider for Lead, Architect, Implementer, and Reviewer roles.
- Implementer and Reviewer are separate logical agents even when both use Codex.
- Local Qwen workers are fallback/low-cost providers for bounded work such as QA and repetitive tasks.
- Provider names are configuration, not workflow logic.

## Current milestone
Validate provider routing and role isolation before adding live model adapters or persistent workflow state.
