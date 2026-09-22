from __future__ import annotations

from typing import Protocol, Sequence

from .orchestrator import AgentProvider, AgentResult, AgentTask
from .workspace_provider import LocalWorkspaceProvider


class WorkspaceAgent(Protocol):
    def execute_in_workspace(
        self,
        task: AgentTask,
        workspace: LocalWorkspaceProvider,
    ) -> AgentResult:
        ...


class LocalWorkspaceAgentAdapter:
    """Adapts a workspace-aware agent to the provider interface.

    The adapter deliberately does not contain model logic. A model-backed agent
    receives the same AgentTask and a controlled workspace bridge.
    """

    def __init__(self, agent: WorkspaceAgent) -> None:
        self.agent = agent

    def execute(self, task: AgentTask) -> AgentResult:
        workspace_path = task.context.get("workspace")
        if not workspace_path:
            raise ValueError("Workspace-aware execution requires a workspace context.")
        workspace = LocalWorkspaceProvider(workspace_path)
        return self.agent.execute_in_workspace(task, workspace)


__all__ = ["LocalWorkspaceAgentAdapter", "WorkspaceAgent"]
