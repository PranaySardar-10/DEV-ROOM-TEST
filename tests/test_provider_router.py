import unittest

from devroom.orchestrator import AgentResult, AgentTask
from devroom.provider_router import ProviderRouter, RoleBinding
from devroom.sandbox_policy import READ_ONLY, WORKSPACE_WRITE


class RecordingProvider:
    def __init__(self) -> None:
        self.tasks = []

    def execute(self, task: AgentTask) -> AgentResult:
        self.tasks.append(task)
        return AgentResult(role=task.role, summary="ok")


class ProviderRouterTests(unittest.TestCase):
    def test_same_provider_can_back_multiple_read_only_roles(self) -> None:
        worker = RecordingProvider()
        router = ProviderRouter(
            {"worker": worker},
            {
                "Coder": RoleBinding("worker", "Produce a proposal."),
                "QA": RoleBinding("worker", "Validate without modifying."),
            },
        )

        router.execute(AgentTask(role="Coder", goal="Add feature X"))
        router.execute(AgentTask(role="QA", goal="Validate feature X"))

        self.assertEqual([task.role for task in worker.tasks], ["Coder", "QA"])
        self.assertEqual(worker.tasks[0].context["sandbox"], READ_ONLY)
        self.assertEqual(worker.tasks[1].context["sandbox"], READ_ONLY)
        self.assertNotEqual(
            worker.tasks[0].context["role_instructions"],
            worker.tasks[1].context["role_instructions"],
        )

    def test_workspace_agent_adapter_can_back_implementer(self) -> None:
        from devroom.workspace_agent import LocalWorkspaceAgentAdapter

        class WorkspaceImplementer:
            def execute_in_workspace(self, task, workspace):
                workspace.write_file("implemented.txt", task.goal)
                return AgentResult(
                    role=task.role,
                    summary="implemented in workspace",
                    artifacts=("implemented.txt",),
                )

        workspace_agent = WorkspaceImplementer()
        router = ProviderRouter(
            {"workspace": LocalWorkspaceAgentAdapter(workspace_agent)},
            {"Implementer": RoleBinding("workspace", "Implement only the approved scope.", WORKSPACE_WRITE)},
        )

        import tempfile
        from devroom.workspace_provider import LocalWorkspaceProvider
        with tempfile.TemporaryDirectory() as directory:
            workspace = LocalWorkspaceProvider(directory)
            workspace.run_command(("git", "init", "-b", "main"), approved_executables=("git",))
            workspace.run_command(
                ("git", "checkout", "-b", "agent/implementer/router-test"),
                approved_executables=("git",),
            )
            result = router.execute(
                AgentTask(
                    role="Implementer",
                    goal="Create the implementation",
                    context={"workspace": directory, "allowed_paths": "implemented.txt"},
                )
            )
            self.assertEqual(result.artifacts, ("implemented.txt",))

    def test_read_only_role_cannot_be_escalated(self) -> None:
        router = ProviderRouter(
            {"worker": RecordingProvider()},
            {"Coder": RoleBinding("worker", "Review only.")},
        )
        with self.assertRaises(PermissionError):
            router.execute(
                AgentTask(
                    role="Coder",
                    goal="Review",
                    context={"sandbox": WORKSPACE_WRITE},
                )
            )

    def test_missing_role_binding_fails_loudly(self) -> None:
        with self.assertRaises(KeyError):
            ProviderRouter({}, {}).execute(AgentTask(role="Unknown", goal="Do something"))


if __name__ == "__main__":
    unittest.main()
