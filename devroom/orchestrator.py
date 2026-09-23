from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Mapping, Protocol
import time

from .state_store import PersistedWorkflow, WorkflowStateWriter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .provider_registry import ProviderRegistry


class Stage(str, Enum):
    LEAD = "lead"
    ARCHITECT = "architect"
    CODER = "coder"
    HUMAN_REVIEW = "human_review"
    IMPLEMENTER = "implementer"
    QA = "qa"
    UNITY_VALIDATION = "unity_validation"
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
        return AgentResult(
            role=task.role,
            summary=f"Mock {task.role} completed: {task.goal}",
            artifacts=(f"mock-{task.role.lower()}-artifact",),
        )

class ResourceGuard:
    """Protect long-running local inference with a configurable cooldown between agent calls."""
    def __init__(self, *, cooldown_after_seconds: float = 3600.0, cooldown_seconds: float = 45.0, clock: Callable[[], float] = time.monotonic, sleeper: Callable[[float], None] = time.sleep) -> None:
        if cooldown_after_seconds < 0: raise ValueError("cooldown_after_seconds must be >= 0")
        if cooldown_seconds < 0: raise ValueError("cooldown_seconds must be >= 0")
        self.cooldown_after_seconds = cooldown_after_seconds
        self.cooldown_seconds = cooldown_seconds
        self.clock = clock
        self.sleeper = sleeper
        self._work_started_at: float | None = None

    def before_agent(self) -> None:
        if self._work_started_at is None: self._work_started_at = self.clock()

    def after_agent(self) -> bool:
        if self._work_started_at is None: return False
        elapsed = self.clock() - self._work_started_at
        if elapsed < self.cooldown_after_seconds: return False
        if self.cooldown_seconds > 0: self.sleeper(self.cooldown_seconds)
        self._work_started_at = self.clock()
        return True

@dataclass
class WorkflowResult:
    stage: Stage
    history: list[Stage]
    results: list[AgentResult]
    halted_reason: str | None = None


class DevRoomOrchestrator:
    """Production factory workflow with human approval before integration and Unity validation."""

    def __init__(self, provider: AgentProvider, *, state_writer: WorkflowStateWriter | None = None, resource_guard: ResourceGuard | None = None) -> None:
        self.provider = provider
        self.state_writer = state_writer
        self.resource_guard = resource_guard or ResourceGuard()

    @classmethod
    def with_provider_registry(
        cls,
        registry: "ProviderRegistry",
        bindings: Mapping[str, object] | None = None,
        *,
        state_writer: WorkflowStateWriter | None = None,
    ) -> "DevRoomOrchestrator":
        from .provider_router import DEFAULT_ROLE_BINDINGS, ProviderRouter

        return cls(
            ProviderRouter(registry.as_mapping(), bindings or DEFAULT_ROLE_BINDINGS),
            state_writer=state_writer,
        )

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
        allowed_paths: tuple[str, ...] = (),
        human_gate: HumanGate | None = None,
        max_feedback_cycles: int = 3,
        resume_state: PersistedWorkflow | None = None,
    ) -> WorkflowResult:
        if not goal.strip():
            raise ValueError("goal must not be empty")
        if workspace is not None and not str(workspace).strip():
            raise ValueError("workspace must not be blank")
        if any(not str(path).strip() for path in allowed_paths):
            raise ValueError("allowed_paths must not contain blank paths")
        if max_feedback_cycles < 0:
            raise ValueError("max_feedback_cycles must be >= 0")

        if resume_state is not None:
            if resume_state.goal is not None and resume_state.goal != goal:
                raise ValueError("resume state goal does not match the requested goal")
            if resume_state.workspace != workspace:
                raise ValueError("resume state workspace does not match the requested workspace")
            if resume_state.allowed_paths != tuple(allowed_paths):
                raise ValueError("resume state allowed_paths do not match the requested scope")
            if resume_state.max_feedback_cycles != max_feedback_cycles:
                raise ValueError("resume state max_feedback_cycles does not match the requested limit")
            if resume_state.stage in {Stage.COMPLETE.value, Stage.HALTED.value}:
                raise ValueError("terminal workflow state cannot be resumed")

        history: list[Stage] = (
            [Stage(item) for item in resume_state.history]
            if resume_state is not None else []
        )
        results: list[AgentResult] = (
            [
                AgentResult(
                    role=str(item["role"]),
                    summary=str(item["summary"]),
                    artifacts=tuple(str(path) for path in item.get("artifacts", [])),
                )
                for item in resume_state.results
            ]
            if resume_state is not None else []
        )
        replay_index = 0
        persisted_decision: HumanDecision | None = (
            HumanDecision(resume_state.last_decision)
            if resume_state is not None and resume_state.last_decision else None
        )
        persisted_feedback: str | None = (
            resume_state.last_feedback if resume_state is not None else None
        )
        replay_gate = resume_state.stage if resume_state is not None else None

        def persist(
            stage: Stage,
            halted_reason: str | None = None,
            last_decision: HumanDecision | None = None,
            last_feedback: str | None = None,
        ) -> None:
            nonlocal persisted_decision, persisted_feedback
            if last_decision is not None:
                persisted_decision = last_decision
                persisted_feedback = last_feedback
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
                last_decision=(persisted_decision.value if persisted_decision is not None else None),
                last_feedback=persisted_feedback,
                goal=goal,
                workspace=workspace,
                allowed_paths=allowed_paths,
                max_feedback_cycles=max_feedback_cycles,
            )

        def call(
            stage: Stage,
            role: str,
            task_goal: str,
            context: dict[str, str] | None = None,
        ) -> AgentResult:
            nonlocal replay_index
            if resume_state is not None and replay_index < len(resume_state.results):
                stored = resume_state.results[replay_index]
                expected_role = str(stored["role"])
                if expected_role == role:
                    replay_index += 1
                    return AgentResult(
                        role=expected_role,
                        summary=str(stored["summary"]),
                        artifacts=tuple(str(path) for path in stored.get("artifacts", [])),
                    )
            if not history or history[-1] is not stage:
                history.append(stage)
            task_context = dict(context or {})
            if workspace is not None:
                task_context["workspace"] = str(workspace)
            if allowed_paths:
                task_context["allowed_paths"] = ",".join(str(path) for path in allowed_paths)
            self.resource_guard.before_agent()
            try:
                result = self.provider.execute(
                    AgentTask(role=role, goal=task_goal, context=task_context)
                )
            except Exception as exc:
                reason = f"{role} execution failed: {type(exc).__name__}: {exc}"
                persist(Stage.HALTED, reason)
                raise
            finally:
                self.resource_guard.after_agent()
            results.append(result)
            persist(stage)
            return result

        def gate(
            stage: Stage,
            prompt: str,
            context: Mapping[str, str],
        ) -> tuple[HumanDecision, str]:
            nonlocal replay_gate
            if not history or history[-1] is not stage:
                history.append(stage)
            if replay_gate == stage.value and persisted_decision is not None:
                replay_gate = None
                return persisted_decision, persisted_feedback or ""
            persist(stage)
            if human_gate is None:
                return HumanDecision.HALT, f"{stage.value} requires explicit human decision."
            decision, feedback = human_gate(stage, prompt, context)
            if not isinstance(decision, HumanDecision):
                decision = HumanDecision(decision)
            feedback = feedback.strip()
            persist(stage, last_decision=decision, last_feedback=feedback)
            return decision, feedback

        lead = call(Stage.LEAD, "Lead", goal)
        architecture = call(
            Stage.ARCHITECT,
            "Architect",
            f"Design the implementation for: {goal}",
            {"lead_summary": lead.summary},
        )

        revision_feedback = ""
        for cycle in range(max_feedback_cycles + 1):
            coder_context = {
                "architecture_summary": architecture.summary,
                "review_target": "Prepare a concrete implementation proposal for human/ChatGPT review. Do not integrate into the production workspace.",
            }
            if revision_feedback:
                coder_context["revision_instruction"] = revision_feedback

            proposal = call(
                Stage.CODER,
                "Coder",
                f"Produce the implementation proposal for: {goal}",
                coder_context,
            )
            if not proposal.artifacts:
                reason = "Coder completed without producing a reviewable implementation proposal."
                persist(Stage.HALTED, reason)
                return WorkflowResult(Stage.HALTED, history, results, reason)

            decision, feedback = gate(
                Stage.HUMAN_REVIEW,
                f"Review the proposed implementation with ChatGPT and decide whether it may enter the implementation stage: {goal}",
                {
                    "architecture": architecture.summary,
                    "proposal": proposal.summary,
                },
            )

            if decision is HumanDecision.HALT:
                reason = feedback or "Human review halted the workflow."
                persist(Stage.HALTED, reason)
                return WorkflowResult(Stage.HALTED, history, results, reason)

            if decision is HumanDecision.REQUEST_CHANGES:
                if cycle >= max_feedback_cycles:
                    reason = "Maximum proposal revision cycles reached."
                    persist(Stage.HALTED, reason)
                    return WorkflowResult(Stage.HALTED, history, results, reason)
                revision_feedback = feedback or "Revise the proposal according to human/ChatGPT review."
                continue

            implementation = call(
                Stage.IMPLEMENTER,
                "Implementer",
                f"Integrate the approved implementation for: {goal}",
                {
                    "architecture_summary": architecture.summary,
                    "approved_proposal": proposal.summary,
                    "approval_feedback": feedback,
                },
            )
            if not implementation.artifacts:
                reason = "Implementer completed without producing integration artifacts."
                persist(Stage.HALTED, reason)
                return WorkflowResult(Stage.HALTED, history, results, reason)

            qa = call(
                Stage.QA,
                "QA",
                f"Run automated validation for the integrated implementation: {goal}",
                {
                    "implementation_summary": implementation.summary,
                    "approved_proposal": proposal.summary,
                },
            )

            validation_decision, validation_feedback = gate(
                Stage.UNITY_VALIDATION,
                f"Open the Unity project and validate the actual gameplay/runtime result for: {goal}",
                {
                    "implementation": implementation.summary,
                    "qa": qa.summary,
                },
            )

            if validation_decision is HumanDecision.APPROVE:
                history.append(Stage.COMPLETE)
                persist(Stage.COMPLETE)
                return WorkflowResult(Stage.COMPLETE, history, results)

            if validation_decision is HumanDecision.HALT:
                reason = validation_feedback or "Unity validation halted the workflow."
                persist(Stage.HALTED, reason)
                return WorkflowResult(Stage.HALTED, history, results, reason)

            if cycle >= max_feedback_cycles:
                reason = "Maximum Unity correction cycles reached."
                persist(Stage.HALTED, reason)
                return WorkflowResult(Stage.HALTED, history, results, reason)

            revision_feedback = (
                validation_feedback
                or "Unity validation found a problem. Produce a corrected implementation proposal."
            )

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
    "ResourceGuard",
    "Stage",
    "WorkflowResult",
]
