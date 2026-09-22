from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from .orchestrator import AgentProvider
from .provider_registry import ProviderRegistry

ProviderBuilder = Callable[[Mapping[str, Any]], AgentProvider]


@dataclass(frozen=True)
class ProviderSpec:
    """Configuration for one named provider instance."""

    name: str
    kind: str
    options: Mapping[str, Any] = field(default_factory=dict)


class ProviderFactory:
    """Builds provider instances from explicit, provider-neutral configuration."""

    def __init__(self) -> None:
        self._builders: dict[str, ProviderBuilder] = {}

    def register(self, kind: str, builder: ProviderBuilder) -> None:
        normalized = kind.strip()
        if not normalized:
            raise ValueError("Provider kind must not be blank.")
        if normalized in self._builders:
            raise ValueError(f"Provider kind is already registered: {normalized!r}")
        self._builders[normalized] = builder

    def create(self, spec: ProviderSpec) -> AgentProvider:
        if not spec.name.strip():
            raise ValueError("Provider name must not be blank.")
        if not spec.kind.strip():
            raise ValueError("Provider kind must not be blank.")
        try:
            builder = self._builders[spec.kind]
        except KeyError as exc:
            raise KeyError(
                f"Provider kind is not registered: {spec.kind}"
            ) from exc
        return builder(dict(spec.options))

    def build_registry(
        self, specs: list[ProviderSpec] | tuple[ProviderSpec, ...]
    ) -> ProviderRegistry:
        registry = ProviderRegistry()
        for spec in specs:
            registry.register(spec.name, self.create(spec))
        return registry


def build_default_factory() -> ProviderFactory:
    """Return the built-in factory without constructing any providers yet."""
    factory = ProviderFactory()

    def build_codex(options: Mapping[str, Any]) -> AgentProvider:
        from .codex_provider import CodexCliConfig, CodexCliProvider
        return CodexCliProvider(CodexCliConfig(**dict(options)))

    def build_local_qwen(options: Mapping[str, Any]) -> AgentProvider:
        from .local_qwen_provider import LocalQwenConfig, LocalQwenProvider
        return LocalQwenProvider(LocalQwenConfig(**dict(options)))

    factory.register("codex-cli", build_codex)
    factory.register("local-qwen-ollama", build_local_qwen)
    return factory


__all__ = [
    "ProviderBuilder",
    "ProviderFactory",
    "ProviderSpec",
    "build_default_factory",
]
