from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol


class Stage(str, Enum):
    LEAD = "lead"
    ARCHITECT = "architect"
    GATE_1 = "human_gate_1"
    IMPLEMENTER = "implementer"
    REVIEWER = "reviewer"
    QA = "qa"
    LEAD_REPORT = "lead_report"
    GATE_2 = "human_gate_2"
    COMPLETE = "complete"
    HALTED = "halted"


@dataclass(frozen=True)
class AgentTask:
    role: str
    goal: str
    context: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentResult:
    role: str
    summary: str
    artifacts: tuple[str, ...] = ()


class AgentProvider(Protocol):
    def execute(self, task: AgentTask) -> AgentResult:
        ...


class MockProvider:
    """Deterministic provider used to validate orchestration without an AI model."""

    def __init__(self) -> None:
        self.calls: list[AgentTask] = []

    def execute(self, task: AgentTask) -> AgentResult:
        self.calls.append(task)
        return AgentResult(
            role=task.role,
            summary=f"Mock {task.role} completed: {task.goal}",
            artifacts=(),
        )


@dataclass
class WorkflowResult:
    stage: Stage
    history: list[Stage]
    results: list[AgentResult]
    halted_reason: str | None = None


class DevRoomOrchestrator:
    """Provider-neutral state machine for the first DevRoom workflow."""

    def __init__(self, provider: AgentProvider) -> None:
        self.provider = provider

    def run(
        self,
        goal: str,
        *,
        approve_gate_1: bool = True,
        approve_gate_2: bool = True,
    ) -> WorkflowResult:
        if not goal.strip():
            raise ValueError("goal must not be empty")

        history: list[Stage] = []
        results: list[AgentResult] = []

        def call(stage: Stage, role: str, task_goal: str, context: dict[str, str] | None = None) -> AgentResult:
            history.append(stage)
            result = self.provider.execute(
                AgentTask(role=role, goal=task_goal, context=context or {})
            )
            results.append(result)
            return result

        lead = call(Stage.LEAD, "Lead", goal)
        architecture = call(
            Stage.ARCHITECT,
            "Architect",
            f"Design the implementation for: {goal}",
            {"lead_summary": lead.summary},
        )

        history.append(Stage.GATE_1)
        if not approve_gate_1:
            return WorkflowResult(
                Stage.HALTED,
                history,
                results,
                "Human Gate 1 was not approved.",
            )

        implementation = call(
            Stage.IMPLEMENTER,
            "Implementer",
            f"Implement the approved design for: {goal}",
            {"architecture_summary": architecture.summary},
        )

        review = call(
            Stage.REVIEWER,
            "Reviewer",
            f"Independently review the implementation for: {goal}",
            {"implementation_summary": implementation.summary},
        )

        qa = call(
            Stage.QA,
            "QA",
            f"Validate the implementation for: {goal}",
            {"review_summary": review.summary},
        )

        report = call(
            Stage.LEAD_REPORT,
            "Lead",
            f"Prepare the integration report for: {goal}",
            {
                "review_summary": review.summary,
                "qa_summary": qa.summary,
            },
        )

        history.append(Stage.GATE_2)
        if not approve_gate_2:
            return WorkflowResult(
                Stage.HALTED,
                history,
                results,
                "Human Gate 2 was not approved.",
            )

        history.append(Stage.COMPLETE)
        return WorkflowResult(Stage.COMPLETE, history, results)


__all__ = [
    "AgentProvider",
    "AgentResult",
    "AgentTask",
    "DevRoomOrchestrator",
    "MockProvider",
    "Stage",
    "WorkflowResult",
]
