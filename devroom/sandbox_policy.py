from __future__ import annotations

from dataclasses import dataclass

from .orchestrator import Stage

READ_ONLY = "read-only"
WORKSPACE_WRITE = "workspace-write"

_DEFAULT_POLICIES = {
    "Lead": READ_ONLY,
    "Architect": READ_ONLY,
    "Coder": READ_ONLY,
    "Implementer": WORKSPACE_WRITE,
    "QA": READ_ONLY,
}


@dataclass(frozen=True)
class RoleSandboxPolicy:
    """Maximum sandbox privilege allowed for each production role."""

    policies: dict[str, str] | None = None

    def __post_init__(self) -> None:
        policies = self.policies or _DEFAULT_POLICIES
        invalid = {
            role: value
            for role, value in policies.items()
            if value not in {READ_ONLY, WORKSPACE_WRITE}
        }
        if invalid:
            raise ValueError(f"Invalid sandbox policies: {invalid}")
        for role in ("Lead", "Architect", "Coder", "QA"):
            if policies.get(role, READ_ONLY) == WORKSPACE_WRITE:
                raise PermissionError(f"Non-Implementer role {role!r} cannot be configured writable.")

    def sandbox_for(self, role: str) -> str:
        return (self.policies or _DEFAULT_POLICIES).get(role, READ_ONLY)


__all__ = ["READ_ONLY", "WORKSPACE_WRITE", "RoleSandboxPolicy"]
