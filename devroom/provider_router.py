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
    """Routes logical roles while enforcing role-specific execution constraints."""

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


DEFAULT_ROLE_BINDINGS = {
    "Lead": RoleBinding(
        provider="codex",
        instructions="Coordinate the workflow; do not implement production code or merge changes.",
    ),
    "Architect": RoleBinding(
        provider="codex",
        instructions="Produce design, interfaces, dependencies, and acceptance criteria; do not implement production code.",
    ),
    "Implementer": RoleBinding(
        provider="codex",
        instructions="Implement only the approved task scope. Do not self-certify or merge.",
        sandbox=WORKSPACE_WRITE,
    ),
    "Reviewer": RoleBinding(
        provider="codex",
        instructions="Review independently from a fresh context. Inspect the diff, requirements, tests, and repository. Do not modify the implementation.",
    ),
    "QA": RoleBinding(
        provider="qwen3.5-4b-local",
        instructions="Run or inspect tests and report reproducible evidence; do not modify implementation.",
    ),
}


__all__ = ["DEFAULT_ROLE_BINDINGS", "ProviderRouter", "RoleBinding"]
