from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .orchestrator import AgentProvider, AgentResult, AgentTask
from .sandbox_policy import READ_ONLY, WORKSPACE_WRITE, RoleSandboxPolicy


@dataclass(frozen=True)
class RoleBinding:
    """Maps a logical role to a provider and execution constraints."""

    provider: str
    instructions: str
    sandbox: str = READ_ONLY


class ProviderRouter:
    """Routes production roles while enforcing maximum role privileges."""

    def __init__(
        self,
        providers: Mapping[str, AgentProvider],
        bindings: Mapping[str, RoleBinding],
        *,
        sandbox_policy: RoleSandboxPolicy | None = None,
    ) -> None:
        self._providers = dict(providers)
        self._bindings = dict(bindings)
        self._sandbox_policy = sandbox_policy or RoleSandboxPolicy()

    def execute(self, task: AgentTask) -> AgentResult:
        binding = self._bindings.get(task.role)
        if binding is None:
            raise KeyError(f"No provider binding configured for role: {task.role}")

        provider = self._providers.get(binding.provider)
        if provider is None:
            raise KeyError(f"Provider is not registered: {binding.provider}")

        allowed = self._sandbox_policy.sandbox_for(task.role)
        if binding.sandbox not in {READ_ONLY, WORKSPACE_WRITE}:
            raise ValueError(f"Unsupported sandbox policy: {binding.sandbox}")
        if binding.sandbox == WORKSPACE_WRITE and allowed != WORKSPACE_WRITE:
            raise PermissionError(f"Role {task.role!r} is not permitted to use workspace-write.")

        context = dict(task.context)
        requested = context.get("sandbox", binding.sandbox)
        if requested == WORKSPACE_WRITE and binding.sandbox != WORKSPACE_WRITE:
            raise PermissionError(f"Task attempted to escalate role {task.role!r} to workspace-write.")
        context["role_instructions"] = binding.instructions
        context["provider"] = binding.provider
        context["sandbox"] = binding.sandbox

        return provider.execute(AgentTask(role=task.role, goal=task.goal, context=context))


_DEFAULT_NO_EXTRA = (
    "COMMON CONTRACT: "
    "Perform only this role. Do not expose chain-of-thought or a thinking process. "
    "Do not invent requirements, expand scope, redesign, or add optional features. "
    "Do not claim actions, files, tests, runtime behavior, or validation you did not perform. "
    "Do not self-approve or declare workflow completion. "
    "If evidence is unavailable, report UNVERIFIED with the exact missing evidence. "
    "If the task specification defines an exact output format, that format is authoritative. "
)

DEFAULT_ROLE_BINDINGS = {
    "Lead": RoleBinding(
        provider="gemma4-e4b-local",
        instructions=(
            _DEFAULT_NO_EXTRA
            + "ROLE CONTRACT: Translate the goal and task specification into a concise "
            "work brief for the Architect. Identify required outcomes, explicit constraints, "
            "forbidden scope, acceptance requirements, and unresolved ambiguities. "
            "Do not design the implementation, write code, inspect runtime behavior, or perform QA. "
            "Do not report PASS/FAIL for implementation because implementation has not happened."
        ),
    ),
    "Architect": RoleBinding(
        provider="gemma4-e4b-local",
        instructions=(
            _DEFAULT_NO_EXTRA
            + "ROLE CONTRACT: Produce the concrete implementation specification from the goal, "
            "task specification, and Lead brief. Define required components/files, dependency direction, "
            "interfaces or data flow only where explicitly required, and implementation constraints. "
            "Do not write code, claim files exist, claim compilation, or perform QA. "
            "Do not repeat the task as a generic plan; produce actionable implementation requirements."
        ),
    ),
    "Coder": RoleBinding(
        provider="gemma4-e4b-local",
        instructions=(
            _DEFAULT_NO_EXTRA
            + "ROLE CONTRACT: Produce a reviewable implementation proposal based only on the task "
            "specification and Architect result. Identify exact files to create/change, concrete changes, "
            "and any required verification steps. Do not modify files, claim implementation occurred, "
            "claim tests passed, or add scope. The proposal is an input to human/ChatGPT review, not approval."
        ),
    ),
    "Implementer": RoleBinding(
        provider="qwen2.5-coder-3b-workspace-local",
        instructions=(
            _DEFAULT_NO_EXTRA
            + "ROLE CONTRACT: Apply only the human-approved proposal within the explicit allowed path scope. "
            "Do not reinterpret approval, add files outside scope, redesign, or implement unapproved features. "
            "Return only an accurate summary of actual changes and actual artifacts. Do not claim tests or runtime "
            "validation unless those actions were actually performed by the implementer."
        ),
        sandbox=WORKSPACE_WRITE,
    ),
    "QA": RoleBinding(
        provider="gemma4-e4b-local",
        instructions=(
            _DEFAULT_NO_EXTRA
            + "ROLE CONTRACT: Independently evaluate the implementation against the task specification and "
            "approved proposal. Treat implementation summaries and agent claims as untrusted claims, not evidence. "
            "Use supplied workspace evidence and other permitted evidence. Report the task-required QA fields exactly. "
            "If a requirement cannot be verified from available evidence, mark it UNVERIFIED rather than PASS. "
            "Do not modify files, fix issues, or suggest new architecture."
        ),
    ),
}

__all__ = ["DEFAULT_ROLE_BINDINGS", "ProviderRouter", "RoleBinding"]
