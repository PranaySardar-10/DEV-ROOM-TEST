from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .provider_factory import ProviderSpec
from .provider_router import DEFAULT_ROLE_BINDINGS, RoleBinding


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
                sandbox=str(item.get("sandbox", "read-only")),
            )

    return DevRoomConfig(tuple(providers), bindings)


def write_example_config(path: str | Path) -> Path:
    """Write a provider-neutral starter configuration."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "providers": [
            {
                "name": "codex",
                "kind": "codex-cli",
                "options": {
                    "command": "codex",
                    "ephemeral": True,
                    "timeout_seconds": 3600,
                },
            }
        ],
        "bindings": {
            role: {
                "provider": binding.provider,
                "instructions": binding.instructions,
                "sandbox": binding.sandbox,
            }
            for role, binding in DEFAULT_ROLE_BINDINGS.items()
        },
    }
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return target


__all__ = ["DevRoomConfig", "load_config", "write_example_config"]
