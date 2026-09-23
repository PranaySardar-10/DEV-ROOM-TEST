from __future__ import annotations

import json
import shutil
import urllib.error
import urllib.request
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


def _ollama_model_available(api_url: str, model: str, timeout_seconds: float) -> tuple[bool, str]:
    tags_url = api_url.rsplit("/", 2)[0] + "/api/tags"
    request = urllib.request.Request(tags_url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return False, f"Ollama API unavailable at {tags_url!r}: {exc}"

    models = payload.get("models", [])
    if not isinstance(models, list):
        return False, "Ollama API returned an invalid /api/tags payload."

    installed = {
        str(item.get("name", ""))
        for item in models
        if isinstance(item, dict)
    }
    if model not in installed:
        return False, f"Configured Ollama model not installed: {model!r}."

    return True, f"Ollama API reachable and configured model is installed: {model!r}."


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
        elif spec.kind in {"local-qwen-ollama", "local-ollama", "local-ollama-workspace"}:
            command = str(spec.options.get("command", "ollama"))
            model = str(spec.options.get("model", ""))
            api_url = str(spec.options.get("api_url", "http://localhost:11434/api/generate"))
            timeout_seconds = float(spec.options.get("healthcheck_timeout_seconds", 5))
            command_available = _command_available(command)
            if not command_available:
                diagnostics.append(
                    ProviderDiagnostic(
                        spec.name,
                        spec.kind,
                        False,
                        f"Local Ollama CLI not found: {command!r}.",
                    )
                )
                continue
            if not model:
                diagnostics.append(
                    ProviderDiagnostic(
                        spec.name,
                        spec.kind,
                        False,
                        "No Ollama model is configured.",
                    )
                )
                continue
            api_available, api_message = _ollama_model_available(
                api_url, model, timeout_seconds
            )
            diagnostics.append(
                ProviderDiagnostic(
                    spec.name,
                    spec.kind,
                    api_available,
                    f"Local Ollama CLI found: {command!r}; {api_message}",
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
