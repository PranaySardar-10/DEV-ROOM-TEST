from __future__ import annotations

from typing import Mapping

from .orchestrator import AgentProvider, DevRoomOrchestrator
from .provider_factory import ProviderFactory, ProviderSpec, build_default_factory
from .provider_registry import ProviderRegistry
from .provider_router import DEFAULT_ROLE_BINDINGS, RoleBinding


def build_provider_registry(
    specs: list[ProviderSpec] | tuple[ProviderSpec, ...],
    *,
    factory: ProviderFactory | None = None,
) -> ProviderRegistry:
    """Build the named provider registry from external configuration."""
    active_factory = factory or build_default_factory()
    return active_factory.build_registry(specs)


def build_orchestrator(
    specs: list[ProviderSpec] | tuple[ProviderSpec, ...],
    *,
    bindings: Mapping[str, RoleBinding] | None = None,
    factory: ProviderFactory | None = None,
) -> DevRoomOrchestrator:
    """Construct the execution stack without hardcoding provider instances."""
    registry = build_provider_registry(specs, factory=factory)
    return DevRoomOrchestrator.with_provider_registry(
        registry,
        bindings or DEFAULT_ROLE_BINDINGS,
    )


__all__ = ["build_orchestrator", "build_provider_registry"]
