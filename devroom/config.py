from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .provider_factory import ProviderSpec
from .provider_router import DEFAULT_ROLE_BINDINGS, RoleBinding
from .sandbox_policy import READ_ONLY, WORKSPACE_WRITE


@dataclass(frozen=True)
class DevRoomConfig:
    """Provider and role configuration loaded from a JSON document."""

    providers: tuple[ProviderSpec, ...]
    bindings: Mapping[str, RoleBinding]


def load_config(path: str | Path) -> DevRoomConfig:
    config_path = Path(path).expanduser().resolve()
    if not config_path.is_file():
        raise FileNotFoundError(f"DevRoom config does not exist: {config_path}")

    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid DevRoom JSON configuration: {config_path}") from exc

    if not isinstance(raw, dict):
        raise ValueError("DevRoom configuration root must be an object.")

    providers_raw = raw.get("providers", [])
    if not isinstance(providers_raw, list):
        raise ValueError("'providers' must be a list.")

    providers: list[ProviderSpec] = []
    for item in providers_raw:
        if not isinstance(item, dict):
            raise ValueError("Each provider entry must be an object.")
        options = item.get("options", {})
        if not isinstance(options, dict):
            raise ValueError("Provider 'options' must be an object.")
        providers.append(
            ProviderSpec(
                name=str(item.get("name", "")),
                kind=str(item.get("kind", "")),
                options=options,
            )
        )

    bindings_raw = raw.get("bindings")
    if bindings_raw is None:
        bindings = dict(DEFAULT_ROLE_BINDINGS)
    else:
        if not isinstance(bindings_raw, dict):
            raise ValueError("'bindings' must be an object.")
        bindings = {}
        for role, item in bindings_raw.items():
            if not isinstance(item, dict):
                raise ValueError(f"Binding for {role!r} must be an object.")
            bindings[str(role)] = RoleBinding(
                provider=str(item.get("provider", "")),
                instructions=str(item.get("instructions", "")),
                sandbox=str(item.get("sandbox", READ_ONLY)),
            )

    return DevRoomConfig(tuple(providers), bindings)


def validate_config(config: DevRoomConfig) -> None:
    """Validate cross-references and execution constraints before startup."""
    names = [spec.name.strip() for spec in config.providers]
    if any(not name for name in names):
        raise ValueError("Every provider must have a non-blank name.")
    if len(names) != len(set(names)):
        raise ValueError("Provider names must be unique.")

    required_roles = {"Lead", "Architect", "Coder", "Implementer", "QA"}
    missing_roles = required_roles - set(config.bindings)
    if missing_roles:
        raise ValueError(
            "Production configuration is missing required role bindings: "
            + ", ".join(sorted(missing_roles))
        )

    known = set(names)
    for role, binding in config.bindings.items():
        if not role.strip():
            raise ValueError("Role names must not be blank.")
        if binding.provider not in known:
            raise ValueError(
                f"Binding for role {role!r} references unknown provider {binding.provider!r}."
            )
        if binding.sandbox not in {READ_ONLY, WORKSPACE_WRITE}:
            raise ValueError(
                f"Binding for role {role!r} has unsupported sandbox {binding.sandbox!r}."
            )

    implementer = config.bindings["Implementer"]
    if implementer.sandbox != WORKSPACE_WRITE:
        raise ValueError("Implementer must use the workspace-write sandbox.")

    for role in ("Lead", "Architect", "Coder", "QA"):
        if config.bindings[role].sandbox != READ_ONLY:
            raise ValueError(f"{role} must use the read-only sandbox.")


def write_example_config(path: str | Path) -> Path:
    """Write the local-agent production configuration."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "providers": [
            {
                "name": "gemma4-e4b-local",
                "kind": "local-ollama",
                "options": {
                    "command": "ollama",
                    "model": "gemma4:e4b",
                    "timeout_seconds": 600,
                },
            },
            {
                "name": "qwen3.5-4b-local",
                "kind": "local-ollama",
                "options": {
                    "command": "ollama",
                    "model": "qwen3.5:4b",
                    "timeout_seconds": 600,
                },
            },
            {
                "name": "qwen3.5-4b-workspace-local",
                "kind": "local-ollama-workspace",
                "options": {
                    "command": "ollama",
                    "model": "qwen3.5:4b",
                    "timeout_seconds": 600,
                },
            },
        ],
        "bindings": {
            role: {
                "provider": (
                    "qwen3.5-4b-workspace-local"
                    if role == "Implementer"
                    else binding.provider
                ),
                "instructions": binding.instructions,
                "sandbox": binding.sandbox,
            }
            for role, binding in DEFAULT_ROLE_BINDINGS.items()
        },
    }
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return target


__all__ = ["DevRoomConfig", "load_config", "validate_config", "write_example_config"]
