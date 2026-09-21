import unittest

from devroom.orchestrator import AgentTask, AgentResult
from devroom.provider_router import ProviderRouter, RoleBinding


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
                "Implementer": RoleBinding(
                    provider="codex",
                    instructions="Implement only the approved scope.",
                ),
                "Reviewer": RoleBinding(
                    provider="codex",
                    instructions="Review independently from fresh context.",
                ),
            },
        )

        router.execute(AgentTask(role="Implementer", goal="Add feature X"))
        router.execute(AgentTask(role="Reviewer", goal="Review feature X"))

        self.assertEqual([task.role for task in codex.tasks], ["Implementer", "Reviewer"])
        self.assertNotEqual(
            codex.tasks[0].context["role_instructions"],
            codex.tasks[1].context["role_instructions"],
        )
        self.assertEqual(codex.tasks[0].context["provider"], "codex")
        self.assertEqual(codex.tasks[1].context["provider"], "codex")

    def test_missing_role_binding_fails_loudly(self) -> None:
        router = ProviderRouter({}, {})
        with self.assertRaises(KeyError):
            router.execute(AgentTask(role="Unknown", goal="Do something"))


if __name__ == "__main__":
    unittest.main()
