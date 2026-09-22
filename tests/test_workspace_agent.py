import tempfile
import unittest
from pathlib import Path

from devroom.orchestrator import AgentResult, AgentTask
from devroom.sandbox_policy import READ_ONLY, WORKSPACE_WRITE
from devroom.workspace_agent import LocalWorkspaceAgentAdapter


class FakeWorkspaceAgent:
    def __init__(self):
        self.workspace = None
        self.task = None

    def execute_in_workspace(self, task, workspace):
        self.task = task
        self.workspace = workspace
        workspace.write_file("agent.txt", "created")
        return AgentResult("Implementer", "done", ("agent.txt",))


class WorkspaceAgentAdapterTests(unittest.TestCase):
    def test_adapter_supplies_controlled_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            agent = FakeWorkspaceAgent()
            adapter = LocalWorkspaceAgentAdapter(agent)
            task = AgentTask(
                role="Implementer",
                goal="Create a file",
                context={"workspace": directory, "sandbox": WORKSPACE_WRITE},
            )

            result = adapter.execute(task)

            self.assertEqual(result.artifacts, ("agent.txt",))
            self.assertEqual(agent.workspace.read_file("agent.txt"), "created")
            self.assertEqual(agent.task, task)


    def test_adapter_rejects_non_implementer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            task = AgentTask(
                "Reviewer",
                "Review the implementation",
                {"workspace": directory, "sandbox": READ_ONLY},
            )
            with self.assertRaises(PermissionError):
                LocalWorkspaceAgentAdapter(FakeWorkspaceAgent()).execute(task)

    def test_adapter_rejects_missing_write_sandbox(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            task = AgentTask(
                "Implementer",
                "Create a file",
                {"workspace": directory, "sandbox": READ_ONLY},
            )
            with self.assertRaises(PermissionError):
                LocalWorkspaceAgentAdapter(FakeWorkspaceAgent()).execute(task)

    def test_adapter_requires_workspace(self) -> None:
        with self.assertRaises(ValueError):
            LocalWorkspaceAgentAdapter(FakeWorkspaceAgent()).execute(
                AgentTask("Implementer", "Create a file")
            )


if __name__ == "__main__":
    unittest.main()
