from __future__ import annotations


class AgentPreflightError(RuntimeError):
    """Raised when an agent is blocked before it can modify the workspace."""


__all__ = ["AgentPreflightError"]
