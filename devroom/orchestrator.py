from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Mapping, Protocol
import time

from .errors import AgentPreflightError
from .state_store import PersistedWorkflow, WorkflowStateWriter
from .workspace_provider import LocalWorkspaceProvider
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


_CODER_PROPOSAL_REQUIREMENTS = (
    "IMPLEMENTATION FILES/DIRECTORIES",
    "CONCRETE CHANGES",
    "DEPENDENCIES AND CONSTRAINTS",
    "VERIFICATION PLAN",
    "COMPLETENESS CHECK",
)


def validate_coder_proposal(summary: str) -> str | None:
    """Return a deterministic completeness error for proposals missing required sections."""
    normalized = summary.upper()
    missing = [section for section in _CODER_PROPOSAL_REQUIREMENTS if section not in normalized]
    if missing:
        return (
            "Coder proposal is incomplete before human review; missing required sections: "
            + ", ".join(missing)
            + ". The Coder must make the proposal implementation-ready without leaving design decisions "
              "for the Implementer."
        )
    return None


class MockProvider:
    """Deterministic provider used to validate orchestration without an AI model."""

    def __init__(self) -> None:
        self.calls: list[AgentTask] = []

    def execute(self, task: AgentTask) -> AgentResult:
        self.calls.append(task)
        summary = f"Mock {task.role} completed: {task.goal}"
        if task.role == "Coder":
            summary += (
                "\nIMPLEMENTATION FILES/DIRECTORIES\n"
                "Mock implementation paths.\n"
                "CONCRETE CHANGES\n"
                "Mock concrete changes.\n"
                "DEPENDENCIES AND CONSTRAINTS\n"
                "Mock dependencies and constraints.\n"
                "VERIFICATION PLAN\n"
                "Mock verification.\n"
                "COMPLETENESS CHECK\n"
                "All mock requirements addressed."
            )
        return AgentResult(
            role=task.role,
            summary=summary,
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
        specification: str | None = None,
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
        specification = specification or ""

        if resume_state is not None:
            if resume_state.goal is not None and resume_state.goal != goal:
                raise ValueError("resume state goal does not match the requested goal")
            if resume_state.specification is not None and resume_state.specification != specification:
                raise ValueError("resume state specification does not match the requested specification")
            if resume_state.workspace != workspace:
                raise ValueError("resume state workspace does not match the requested workspace")
            if resume_state.allowed_paths != tuple(allowed_paths):
                raise ValueError("resume state allowed_paths do not match the requested scope")
            if resume_state.max_feedback_cycles != max_feedback_cycles:
                raise ValueError("resume state max_feedback_cycles does not match the requested limit")
            try:
                persisted_stage = Stage(resume_state.stage)
            except ValueError as exc:
                raise ValueError("resume state has an invalid stage") from exc
            if not resume_state.history or resume_state.history[-1] != persisted_stage.value:
                raise ValueError("resume state stage does not match its history checkpoint")
            if resume_state.stage in {Stage.COMPLETE.value, Stage.HALTED.value}:
                raise ValueError("terminal workflow state cannot be resumed")
            if resume_state.in_flight_role is not None:
                if not resume_state.history or resume_state.history[-1] != resume_state.in_flight_role.lower():
                    raise ValueError("resume state in-flight role does not match its history checkpoint")
                raise ValueError(
                    f"workflow has an interrupted {resume_state.in_flight_role} execution; reconcile the workspace before resuming"
                )
            role_by_stage = {
                Stage.LEAD: "Lead",
                Stage.ARCHITECT: "Architect",
                Stage.CODER: "Coder",
                Stage.IMPLEMENTER: "Implementer",
                Stage.QA: "QA",
            }
            expected_roles = [
                role_by_stage[Stage(item)]
                for item in resume_state.history
                if Stage(item) in role_by_stage
            ]
            actual_roles = [str(item["role"]) for item in resume_state.results]
            if actual_roles != expected_roles[:len(actual_roles)]:
                raise ValueError("resume state results do not match the workflow history checkpoint")
            if len(expected_roles) > len(actual_roles):
                if persisted_stage not in role_by_stage or expected_roles[-1] != role_by_stage[persisted_stage]:
                    raise ValueError("resume state results do not match the workflow history checkpoint")
            if len(expected_roles) - len(actual_roles) > 1:
                raise ValueError("resume state results do not match the workflow history checkpoint")

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
        replay_gate = (
            resume_state.last_decision_stage
            if resume_state is not None
            else None
        )

        persisted_decision_stage: str | None = (
            resume_state.last_decision_stage
            if resume_state is not None
            else None
        )

        def persist(
            stage: Stage,
            halted_reason: str | None = None,
            last_decision: HumanDecision | None = None,
            last_feedback: str | None = None,
            in_flight_role: str | None = None,
        ) -> None:
            nonlocal persisted_decision, persisted_feedback, persisted_decision_stage
            if last_decision is not None:
                persisted_decision = last_decision
                persisted_feedback = last_feedback
                persisted_decision_stage = stage.value
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
                specification=specification,
                in_flight_role=in_flight_role,
                last_decision_stage=persisted_decision_stage,
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
            if role == "Coder":
                # Coder proposals have a five-section contract and need more output headroom
                # than the other planning roles. Keep this budget role-specific so ordinary
                # local inference does not become slower just because Coder needs completeness.
                task_context["generation_num_predict"] = "8192"
            role_specification = task_specification_for_role(role)
            if role_specification:
                task_context["task_specification"] = role_specification
            self.resource_guard.before_agent()
            persist(stage, in_flight_role=role)
            try:
                result = self.provider.execute(
                    AgentTask(role=role, goal=task_goal, context=task_context)
                )
            except AgentPreflightError as exc:
                reason = f"{role} preflight failed: {type(exc).__name__}: {exc}"
                persist(stage, reason, in_flight_role=None)
                raise
            except Exception as exc:
                reason = f"{role} execution failed: {type(exc).__name__}: {exc}"
                persist(Stage.HALTED, reason)
                raise
            finally:
                self.resource_guard.after_agent()
            results.append(result)
            persist(stage, in_flight_role=None)
            return result

        def task_specification_for_role(role: str) -> str:
            """Expose only workflow-relevant specification sections to each role."""
            if not specification:
                return ""
            if role == "QA":
                return specification

            excluded = {"qa", "human unity validation", "completion"}
            lines = specification.splitlines()
            kept: list[str] = []
            skip = False
            for line in lines:
                if line.startswith("#"):
                    heading = line.lstrip("#").strip().lower()
                    level = len(line) - len(line.lstrip("#"))
                    if level <= 2:
                        skip = heading in excluded
                if not skip:
                    kept.append(line)
            return "\n".join(kept).strip()

        def collect_qa_evidence() -> dict[str, str]:
            if workspace is None:
                return {"workspace_evidence": "No workspace was supplied; filesystem verification is unavailable."}
            try:
                provider = LocalWorkspaceProvider(workspace)
                inspection = provider.inspect()
            except FileNotFoundError:
                return {
                    "workspace_evidence": (
                        f"WORKSPACE: {workspace}\n"
                        "UNVERIFIED: workspace path does not exist in the current execution environment; "
                        "filesystem and Git evidence are unavailable."
                    )
                }
            files = "\n".join(str(path) for path in inspection["files"])
            git_status = "\n".join(str(item) for item in inspection["git"])
            allowed = ", ".join(str(path) for path in allowed_paths) or "<none>"
            contents: list[str] = []
            for relative_path in allowed_paths:
                try:
                    content = provider.read_file(str(relative_path))
                except FileNotFoundError:
                    content = "<FILE NOT FOUND>"
                contents.append(
                    f"FILE {relative_path}\nBEGIN ACTUAL CONTENT\n{content}\nEND ACTUAL CONTENT"
                )
            return {
                "workspace_evidence": (
                    f"WORKSPACE: {inspection['workspace']}\n"
                    f"ACTUAL FILES (excluding .git/__pycache__):\n{files or '<none>'}\n"
                    f"ACTUAL GIT STATUS:\n{git_status or '<clean>'}\n"
                    f"APPROVED PATHS: {allowed}\n"
                    + "\n\n".join(contents)
                )
            }

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

        # Lead is an advisory planning stage. Do not feed raw model-generated Lead
        # output into Architect: upstream free-form text can contain role-like
        # instructions or simulated reasoning that small local models may follow.
        # Architect must derive its implementation specification from the authoritative
        # task specification and its own role contract.
        call(Stage.LEAD, "Lead", goal)
        architecture = call(
            Stage.ARCHITECT,
            "Architect",
            f"Design the implementation for: {goal}",
        )

        revision_feedback = ""
        cycle = 0

        while cycle <= max_feedback_cycles:
            # Coder completeness correction is human-controlled. If the proposal is
            # incomplete, show the exact missing requirements and let the human provide
            # a corrective prompt or halt. A complete proposal proceeds normally.
            coder_revision_feedback = revision_feedback
            proposal: AgentResult | None = None
            for coder_attempt in range(max_feedback_cycles + 1):
                coder_context = {
                    "architecture_summary": architecture.summary,
                    "review_target": (
                        "Prepare a concrete implementation proposal for human/ChatGPT review. "
                        "Do not integrate into the production workspace."
                    ),
                    "coder_output_contract": (
                        "Before returning the proposal, verify that it contains ALL five exact "
                        "sections: IMPLEMENTATION FILES/DIRECTORIES, CONCRETE CHANGES, "
                        "DEPENDENCIES AND CONSTRAINTS, VERIFICATION PLAN, and COMPLETENESS CHECK. "
                        "Do not leave design decisions, file contents, dependencies, or verification "
                        "steps for the Implementer. Treat this as a mandatory pre-submission checklist."
                    ),
                }
                if coder_revision_feedback:
                    coder_context["revision_instruction"] = coder_revision_feedback

                proposal = call(
                    Stage.CODER,
                    "Coder",
                    (
                        f"Produce the implementation proposal for: {goal}. "
                        "Before finishing, self-check the proposal against every required section "
                        "and make it implementation-ready."
                    ),
                    coder_context,
                )
                if not proposal.artifacts:
                    reason = "Coder completed without producing a reviewable implementation proposal."
                    persist(Stage.HALTED, reason)
                    return WorkflowResult(Stage.HALTED, history, results, reason)

                proposal_error = validate_coder_proposal(proposal.summary)
                if proposal_error is None:
                    break

                incomplete_context = {
                    "architecture": architecture.summary,
                    "proposal": proposal.summary,
                    "validation": proposal_error,
                    "decision_options": (
                        "Provide a corrective prompt to the Coder or halt. "
                        "An incomplete proposal cannot be approved."
                    ),
                }
                decision, feedback = gate(
                    Stage.HUMAN_REVIEW,
                    (
                        "Coder produced an incomplete proposal. Review the missing requirements below. "
                        "Choose REQUEST_CHANGES to give the Coder a corrective prompt, or HALT."
                    ),
                    incomplete_context,
                )
                if decision is HumanDecision.HALT:
                    reason = feedback or proposal_error
                    persist(Stage.HALTED, reason)
                    return WorkflowResult(Stage.HALTED, history, results, reason)
                if decision is HumanDecision.APPROVE:
                    reason = "An incomplete Coder proposal cannot be approved for implementation."
                    persist(Stage.HALTED, reason)
                    return WorkflowResult(Stage.HALTED, history, results, reason)
                coder_revision_feedback = feedback or proposal_error

            assert proposal is not None

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
                architecture = call(
                    Stage.ARCHITECT,
                    "Architect",
                    f"Revise the implementation specification for: {goal}",
                    {
                        "previous_architecture_summary": architecture.summary,
                        "revision_instruction": revision_feedback,
                    },
                )
                cycle += 1
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

            qa_context = {
                "implementation_summary": implementation.summary,
                "approved_proposal": proposal.summary,
            }
            qa_context.update(collect_qa_evidence())
            qa = call(
                Stage.QA,
                "QA",
                f"Run automated validation for the integrated implementation: {goal}",
                qa_context,
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
            cycle += 1

        reason = "Workflow ended without approval."
        persist(Stage.HALTED, reason)
        return WorkflowResult(Stage.HALTED, history, results, reason)


__all__ = [
    "AgentPreflightError",
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
