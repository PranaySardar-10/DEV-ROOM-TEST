from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .orchestrator import AgentProvider, AgentResult, AgentTask


@dataclass(frozen=True)
class RoleBinding:
    """Maps a logical DevRoom role to a provider and role-specific instructions."""

    provider: str
    instructions: str


class ProviderRouter:
    """Routes logical roles to providers without coupling roles to model vendors."""

    def __init__(
        self,
        providers: Mapping[str, AgentProvider],
        bindings: Mapping[str, RoleBinding],
    ) -> None:
        self._providers = dict(providers)
        self._bindings = dict(bindings)

    def execute(self, task: AgentTask) -> AgentResult:
        binding = self._bindings.get(task.role)
        if binding is None:
            raise KeyError(f"No provider binding configured for role: {task.role}")

        provider = self._providers.get(binding.provider)
        if provider is None:
            raise KeyError(f"Provider is not registered: {binding.provider}")

        context = dict(task.context)
        context["role_instructions"] = binding.instructions
        context["provider"] = binding.provider

        return provider.execute(
            AgentTask(role=task.role, goal=task.goal, context=context)
        )


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
    ),
    "Reviewer": RoleBinding(
        provider="codex",
        instructions=(
            "Review independently from a fresh context. Inspect the diff, requirements, tests, "
            "and repository. Do not assume the implementer is correct and do not modify the implementation."
        ),
    ),
    "QA": RoleBinding(
        provider="qwen2.5-coder-3b-local",
        instructions="Run or inspect tests and report reproducible evidence; do not modify implementation.",
    ),
}


__all__ = ["DEFAULT_ROLE_BINDINGS", "ProviderRouter", "RoleBinding"]
