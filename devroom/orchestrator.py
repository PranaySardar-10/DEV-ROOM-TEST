from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Mapping, Protocol

from .state_store import WorkflowStateWriter


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


class HumanDecision(str, Enum):
    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"
    HALT = "halt"


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


HumanGate = Callable[[Stage, str, Mapping[str, str]], tuple[HumanDecision, str]]


class MockProvider:
    """Deterministic provider used to validate orchestration without an AI model."""

    def __init__(self) -> None:
        self.calls: list[AgentTask] = []

    def execute(self, task: AgentTask) -> AgentResult:
        self.calls.append(task)
        return AgentResult(role=task.role, summary=f"Mock {task.role} completed: {task.goal}", artifacts=("mock-artifact",))


@dataclass
class WorkflowResult:
    stage: Stage
    history: list[Stage]
    results: list[AgentResult]
    halted_reason: str | None = None


class DevRoomOrchestrator:
    """Provider-neutral state machine with explicit gates, feedback, and durable snapshots."""

    def __init__(self, provider: AgentProvider, *, state_writer: WorkflowStateWriter | None = None) -> None:
        self.provider = provider
        self.state_writer = state_writer

    @classmethod
    def with_provider_router(
        cls,
        providers: Mapping[str, AgentProvider],
        bindings: Mapping[str, object] | None = None,
        *,
        state_writer: WorkflowStateWriter | None = None,
    ) -> "DevRoomOrchestrator":
        from .provider_router import DEFAULT_ROLE_BINDINGS, ProviderRouter

        return cls(
            ProviderRouter(providers, bindings or DEFAULT_ROLE_BINDINGS),
            state_writer=state_writer,
        )

    def run(
        self,
        goal: str,
        *,
        workspace: str | None = None,
        human_gate: HumanGate | None = None,
        max_feedback_cycles: int = 3,
    ) -> WorkflowResult:
        if not goal.strip():
            raise ValueError("goal must not be empty")
        if workspace is not None and not str(workspace).strip():
            raise ValueError("workspace must not be blank")
        if max_feedback_cycles < 0:
            raise ValueError("max_feedback_cycles must be >= 0")

        history: list[Stage] = []
        results: list[AgentResult] = []

        def persist(
            stage: Stage,
            halted_reason: str | None = None,
            last_decision: HumanDecision | None = None,
            last_feedback: str | None = None,
        ) -> None:
            if self.state_writer is None:
                return
            self.state_writer.write(
                stage=stage.value,
                history=(item.value for item in history),
                results=(
                    {
                        "role": result.role,
                        "summary": result.summary,
                        "artifacts": list(result.artifacts),
                    }
                    for result in results
                ),
                halted_reason=halted_reason,
                last_decision=last_decision.value if last_decision is not None else None,
                last_feedback=last_feedback,
            )

        def call(stage: Stage, role: str, task_goal: str, context: dict[str, str] | None = None) -> AgentResult:
            history.append(stage)
            task_context = dict(context or {})
            if workspace is not None:
                task_context["workspace"] = str(workspace)
            result = self.provider.execute(AgentTask(role=role, goal=task_goal, context=task_context))
            results.append(result)
            persist(stage)
            return result

        def gate(stage: Stage, prompt: str, context: Mapping[str, str]) -> tuple[HumanDecision, str]:
            history.append(stage)
            persist(stage)
            if human_gate is None:
                return HumanDecision.HALT, f"{stage.value} requires explicit human decision."
            decision, feedback = human_gate(stage, prompt, context)
            if not isinstance(decision, HumanDecision):
                decision = HumanDecision(decision)
            feedback = feedback.strip()
            # Persist the human decision immediately. Agents must never have to infer
            # an approval from stale pre-gate durable state.
            persist(stage, last_decision=decision, last_feedback=feedback)
            return decision, feedback

        lead = call(Stage.LEAD, "Lead", goal)
        architecture = call(
            Stage.ARCHITECT,
            "Architect",
            f"Design the implementation for: {goal}",
            {"lead_summary": lead.summary},
        )

        decision, feedback = gate(
            Stage.GATE_1,
            f"Review the architecture before implementation: {goal}",
            {"architecture_summary": architecture.summary},
        )
        if decision is HumanDecision.REQUEST_CHANGES:
            if not feedback:
                feedback = "Human requested architecture changes."
            architecture = call(
                Stage.ARCHITECT,
                "Architect",
                f"Revise the implementation design for: {goal}",
                {"previous_architecture": architecture.summary, "human_feedback": feedback},
            )
            decision, feedback = gate(
                Stage.GATE_1,
                f"Review the revised architecture before implementation: {goal}",
                {"architecture_summary": architecture.summary, "human_feedback": feedback},
            )
        if decision is not HumanDecision.APPROVE:
            reason = feedback or f"{Stage.GATE_1.value} was not approved."
            persist(Stage.HALTED, reason)
            return WorkflowResult(Stage.HALTED, history, results, reason)

        implementation_feedback = ""
        for cycle in range(max_feedback_cycles + 1):
            implementer_context = {
                "architecture_summary": architecture.summary,
                "gate_1_decision": HumanDecision.APPROVE.value,
            }
            if implementation_feedback:
                implementer_context["human_feedback"] = implementation_feedback
            implementation = call(
                Stage.IMPLEMENTER,
                "Implementer",
                f"Implement the approved design for: {goal}",
                implementer_context,
            )
            if not implementation.artifacts:
                reason = (
                    "Implementer completed without producing implementation artifacts. "
                    "Reviewer and QA are blocked until an implementation is actually submitted."
                )
                persist(Stage.HALTED, reason)
                return WorkflowResult(Stage.HALTED, history, results, reason)

            review = call(
                Stage.REVIEWER,
                "Reviewer",
                f"Independently review the implementation for: {goal}",
                {"architecture_summary": architecture.summary},
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
                {"review_summary": review.summary, "qa_summary": qa.summary},
            )

            decision, feedback = gate(
                Stage.GATE_2,
                f"Review the implementation, tests, and visual/gameplay result for: {goal}",
                {
                    "review_summary": review.summary,
                    "qa_summary": qa.summary,
                    "lead_report": report.summary,
                },
            )
            if decision is HumanDecision.APPROVE:
                history.append(Stage.COMPLETE)
                persist(Stage.COMPLETE)
                return WorkflowResult(Stage.COMPLETE, history, results)
            if decision is HumanDecision.HALT:
                reason = feedback or "Human Gate 2 halted the workflow."
                persist(Stage.HALTED, reason)
                return WorkflowResult(Stage.HALTED, history, results, reason)
            if cycle >= max_feedback_cycles:
                reason = "Maximum human feedback cycles reached."
                persist(Stage.HALTED, reason)
                return WorkflowResult(Stage.HALTED, history, results, reason)
            implementation_feedback = feedback or "Human requested implementation changes."

        reason = "Workflow ended without approval."
        persist(Stage.HALTED, reason)
        return WorkflowResult(Stage.HALTED, history, results, reason)


__all__ = [
    "AgentProvider",
    "AgentResult",
    "AgentTask",
    "DevRoomOrchestrator",
    "HumanDecision",
    "HumanGate",
    "MockProvider",
    "Stage",
    "WorkflowResult",
]
