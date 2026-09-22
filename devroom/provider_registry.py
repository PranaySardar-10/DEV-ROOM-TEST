from __future__ import annotations

from typing import Mapping

from .orchestrator import AgentProvider


class ProviderRegistry:
    """Explicit registry for provider instances used by DevRoom."""

    def __init__(self, providers: Mapping[str, AgentProvider] | None = None) -> None:
        self._providers: dict[str, AgentProvider] = dict(providers or {})

    def register(self, name: str, provider: AgentProvider) -> None:
        normalized = name.strip()
        if not normalized:
            raise ValueError("Provider name must not be blank.")
        if normalized in self._providers:
            raise ValueError(f"Provider is already registered: {normalized!r}")
        self._providers[normalized] = provider

    def get(self, name: str) -> AgentProvider:
        try:
            return self._providers[name]
        except KeyError as exc:
            raise KeyError(f"Provider is not registered: {name}") from exc

    def snapshot(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))

    def as_mapping(self) -> Mapping[str, AgentProvider]:
        return dict(self._providers)


__all__ = ["ProviderRegistry"]
