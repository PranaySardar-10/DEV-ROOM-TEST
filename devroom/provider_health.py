from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import Mapping

from .provider_factory import ProviderSpec


@dataclass(frozen=True)
class ProviderDiagnostic:
    name: str
    kind: str
    available: bool
    message: str


def diagnose_providers(specs: tuple[ProviderSpec, ...] | list[ProviderSpec]) -> tuple[ProviderDiagnostic, ...]:
    diagnostics: list[ProviderDiagnostic] = []
    for spec in specs:
        if spec.kind == "codex-cli":
            command = str(spec.options.get("command", "codex"))
            available = shutil.which(command) is not None
            diagnostics.append(
                ProviderDiagnostic(
                    spec.name,
                    spec.kind,
                    available,
                    f"Codex CLI {'found' if available else 'not found'}: {command!r}.",
                )
            )
        else:
            diagnostics.append(
                ProviderDiagnostic(
                    spec.name,
                    spec.kind,
                    False,
                    f"No availability probe is registered for provider kind {spec.kind!r}.",
                )
            )
    return tuple(diagnostics)


def require_available_providers(specs: tuple[ProviderSpec, ...] | list[ProviderSpec]) -> None:
    diagnostics = diagnose_providers(specs)
    unavailable = [item for item in diagnostics if not item.available]
    if unavailable:
        details = "; ".join(f"{item.name}: {item.message}" for item in unavailable)
        raise RuntimeError(f"Configured providers are not ready: {details}")


__all__ = ["ProviderDiagnostic", "diagnose_providers", "require_available_providers"]
