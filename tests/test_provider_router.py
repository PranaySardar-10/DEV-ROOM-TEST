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
    def test_same_provider_can_back_developer_and_reviewer_as_separate_roles(self) -> None:
        codex = RecordingProvider()
        router = ProviderRouter(
            {"codex": codex},
            {
                "Implementer": RoleBinding("codex", "Implement only the approved scope.", WORKSPACE_WRITE),
                "Reviewer": RoleBinding("codex", "Review independently from fresh context."),
            },
        )

        router.execute(AgentTask(role="Implementer", goal="Add feature X"))
        router.execute(AgentTask(role="Reviewer", goal="Review feature X"))

        self.assertEqual([task.role for task in codex.tasks], ["Implementer", "Reviewer"])
        self.assertEqual(codex.tasks[0].context["sandbox"], WORKSPACE_WRITE)
        self.assertEqual(codex.tasks[1].context["sandbox"], READ_ONLY)
        self.assertNotEqual(
            codex.tasks[0].context["role_instructions"],
            codex.tasks[1].context["role_instructions"],
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
        with tempfile.TemporaryDirectory() as directory:
            result = router.execute(
                AgentTask(
                    role="Implementer",
                    goal="Create the implementation",
                    context={"workspace": directory},
                )
            )
            self.assertEqual(result.artifacts, ("implemented.txt",))
            with open(f"{directory}/implemented.txt", encoding="utf-8") as handle:
                self.assertEqual(handle.read(), "Create the implementation")

    def test_read_only_role_cannot_be_escalated(self) -> None:
        router = ProviderRouter(
            {"codex": RecordingProvider()},
            {"Reviewer": RoleBinding("codex", "Review only.")},
        )
        with self.assertRaises(PermissionError):
            router.execute(
                AgentTask(
                    role="Reviewer",
                    goal="Review",
                    context={"sandbox": WORKSPACE_WRITE},
                )
            )

    def test_missing_role_binding_fails_loudly(self) -> None:
        with self.assertRaises(KeyError):
            ProviderRouter({}, {}).execute(AgentTask(role="Unknown", goal="Do something"))


if __name__ == "__main__":
    unittest.main()
