from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import Sequence

from .provider_factory import ProviderSpec


@dataclass(frozen=True)
class ProviderDiagnostic:
    name: str
    kind: str
    available: bool
    message: str


def _command_available(command: str) -> bool:
    return shutil.which(command) is not None


def diagnose_providers(
    specs: tuple[ProviderSpec, ...] | list[ProviderSpec],
) -> tuple[ProviderDiagnostic, ...]:
    diagnostics: list[ProviderDiagnostic] = []
    for spec in specs:
        if spec.kind == "codex-cli":
            command = str(spec.options.get("command", "codex"))
            available = _command_available(command)
            diagnostics.append(
                ProviderDiagnostic(
                    spec.name,
                    spec.kind,
                    available,
                    f"Codex CLI {'found' if available else 'not found'}: {command!r}.",
                )
            )
        elif spec.kind == "local-qwen-ollama":
            command = str(spec.options.get("command", "ollama"))
            model = str(spec.options.get("model", "qwen2.5-coder:3b"))
            available = _command_available(command)
            diagnostics.append(
                ProviderDiagnostic(
                    spec.name,
                    spec.kind,
                    available,
                    (
                        f"Local Qwen CLI {'found' if available else 'not found'}: "
                        f"{command!r}; configured model: {model!r}. "
                        "Model installation is not probed by this startup check."
                    ),
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


def require_available_providers(
    specs: tuple[ProviderSpec, ...] | list[ProviderSpec],
) -> None:
    diagnostics = diagnose_providers(specs)
    unavailable = [item for item in diagnostics if not item.available]
    if unavailable:
        details = "; ".join(f"{item.name}: {item.message}" for item in unavailable)
        raise RuntimeError(f"Configured providers are not ready: {details}")


__all__ = ["ProviderDiagnostic", "diagnose_providers", "require_available_providers"]
