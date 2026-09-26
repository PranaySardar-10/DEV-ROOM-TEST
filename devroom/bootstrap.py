from __future__ import annotations

from pathlib import Path
from typing import Mapping

from .config import DevRoomConfig, load_config, validate_config
from .orchestrator import AgentProvider, DevRoomOrchestrator, ResourceGuard
from .state_store import WorkflowStateWriter
from .provider_factory import ProviderFactory, ProviderSpec, build_default_factory
from .provider_registry import ProviderRegistry
from .provider_router import DEFAULT_ROLE_BINDINGS, RoleBinding
from .unity_cli import UnityCliRunner


def build_provider_registry(
    specs: list[ProviderSpec] | tuple[ProviderSpec, ...],
    *,
    factory: ProviderFactory | None = None,
) -> ProviderRegistry:
    """Build the named provider registry from explicit provider specifications."""
    active_factory = factory or build_default_factory()
    return active_factory.build_registry(specs)


def build_orchestrator(
    specs: list[ProviderSpec] | tuple[ProviderSpec, ...],
    *,
    bindings: Mapping[str, RoleBinding] | None = None,
    factory: ProviderFactory | None = None,
    state_writer: WorkflowStateWriter | None = None,
    unity_cli_runner: UnityCliRunner | None = None,
) -> DevRoomOrchestrator:
    """Construct the execution stack from provider specifications."""
    registry = build_provider_registry(specs, factory=factory)
    return DevRoomOrchestrator.with_provider_registry(
        registry,
        bindings or DEFAULT_ROLE_BINDINGS,
        state_writer=state_writer,
    )


def build_from_config(
    config: DevRoomConfig,
    *,
    factory: ProviderFactory | None = None,
    state_writer: WorkflowStateWriter | None = None,
    unity_cli_runner: UnityCliRunner | None = None,
) -> DevRoomOrchestrator:
    """Construct the complete execution stack from a loaded DevRoom config."""
    validate_config(config)
    orchestrator = build_orchestrator(
        config.providers,
        bindings=config.bindings,
        factory=factory,
        state_writer=state_writer,
        unity_cli_runner=unity_cli_runner,
    )
    orchestrator.resource_guard = ResourceGuard(
        cooldown_after_seconds=config.cooldown_after_seconds,
        cooldown_seconds=config.cooldown_seconds,
    )
    return orchestrator


def build_from_config_file(
    path: str | Path,
    *,
    factory: ProviderFactory | None = None,
) -> DevRoomOrchestrator:
    """Load a JSON config file and construct the complete execution stack."""
    return build_from_config(load_config(path), factory=factory)


__all__ = [
    "build_from_config",
    "build_from_config_file",
    "build_orchestrator",
    "build_provider_registry",
]
