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
- Git is the durable project state; conversation history is not the source of truth.

## Current milestone
Build and test the provider-neutral orchestration state machine before adding real model providers.
