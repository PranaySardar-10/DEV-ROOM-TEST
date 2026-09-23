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
_DEFAULT_NO_EXTRA = (
    "STRICT OUTPUT RULES: Perform ONLY the assigned role for the stated GOAL. "
    "Do not explain reasoning. Do not provide explanations, ideas, recommendations, "
    "optional features, alternatives, redesigns, commentary, role-play, or unrelated "
    "content. Do not invent requirements. Do not change the goal. Do not discuss "
    "previous conversations or context. Do not claim actions you did not perform. "
    "Do not self-approve. Return only the required result for your role."
)

DEFAULT_ROLE_BINDINGS = {
    "Lead": RoleBinding(
        provider="gemma4-e4b-local",
        instructions=(
            _DEFAULT_NO_EXTRA + " Produce only the minimum concrete requirements, "
            "scope boundaries, and acceptance criteria needed by the Architect. "
            "Do not write code or modify files."
        ),
    ),
    "Architect": RoleBinding(
        provider="gemma4-e4b-local",
        instructions=(
            _DEFAULT_NO_EXTRA + " Convert ONLY the supplied goal and Lead result "
            "into a concrete implementation specification. Define exactly what must "
            "be changed and nothing else. Do not write implementation code or modify files."
        ),
    ),
    "Coder": RoleBinding(
        provider="gemma4-e4b-local",
        instructions=(
            _DEFAULT_NO_EXTRA + " Produce ONLY the concrete implementation proposal "
            "required by the supplied goal and architecture. Do not implement files, "
            "add features, redesign architecture, or provide alternatives."
        ),
    ),
    "Implementer": RoleBinding(
        provider="qwen2.5-coder-3b-workspace-local",
        instructions=(
            _DEFAULT_NO_EXTRA + " Implement ONLY the explicitly approved proposal. "
            "Modify ONLY the supplied allowed_paths. Do not interpret, expand, improve, "
            "redesign, or add requirements. Return only the required implementation result."
        ),
        sandbox=WORKSPACE_WRITE,
    ),
    "QA": RoleBinding(
        provider="gemma4-e4b-local",
        instructions=(
            _DEFAULT_NO_EXTRA + " Verify ONLY whether the implementation satisfies the "
            "stated goal and approved proposal. Report only reproducible validation evidence. "
            "Do not modify implementation or suggest new features."
        ),
    ),
}

__all__ = ["DEFAULT_ROLE_BINDINGS", "ProviderRouter", "RoleBinding"]
