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


# Production workforce: local Ollama providers only. Human/ChatGPT review is a
# workflow gate, not an autonomous provider role.
DEFAULT_ROLE_BINDINGS = {
    "Lead": RoleBinding(
        provider="gemma4-e4b-local",
        instructions="Coordinate the production task, bound scope, and acceptance criteria. Do not modify production files.",
    ),
    "Architect": RoleBinding(
        provider="gemma4-e4b-local",
        instructions="Produce interfaces, dependencies, implementation boundaries, and acceptance criteria. Do not modify production files.",
    ),
    "Coder": RoleBinding(
        provider="gemma4-e4b-local",
        instructions="Produce a concrete implementation proposal for human/ChatGPT review. Do not integrate it into the production workspace.",
    ),
    "Implementer": RoleBinding(
        provider="qwen3.5-3b-workspace-local",
        instructions="Integrate only the explicitly approved proposal within the assigned task scope. Do not self-approve.",
        sandbox=WORKSPACE_WRITE,
    ),
    "QA": RoleBinding(
        provider="qwen3.5-4b-local",
        instructions="Run or inspect automated validation and report reproducible evidence. Do not modify implementation.",
    ),
}

__all__ = ["DEFAULT_ROLE_BINDINGS", "ProviderRouter", "RoleBinding"]
