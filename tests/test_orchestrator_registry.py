import unittest

from devroom.orchestrator import AgentResult, AgentTask, DevRoomOrchestrator
from devroom.provider_registry import ProviderRegistry
from devroom.provider_router import RoleBinding


class RecordingProvider:
    def __init__(self) -> None:
        self.tasks = []

    def execute(self, task: AgentTask) -> AgentResult:
        self.tasks.append(task)
        return AgentResult(task.role, "ok", ("artifact",))


class OrchestratorRegistryTests(unittest.TestCase):
    def test_orchestrator_can_be_constructed_from_registry(self) -> None:
        registry = ProviderRegistry()
        provider = RecordingProvider()
        registry.register("worker", provider)

        orchestrator = DevRoomOrchestrator.with_provider_registry(
            registry,
            {
                "Lead": RoleBinding("worker", "Coordinate."),
                "Architect": RoleBinding("worker", "Design."),
                "Implementer": RoleBinding("worker", "Implement.", "workspace-write"),
                "Reviewer": RoleBinding("worker", "Review."),
                "QA": RoleBinding("worker", "Test."),
            },
        )

        result = orchestrator.run("build a test feature", workspace=".")
        self.assertEqual(result.stage.value, "halted")
        self.assertGreaterEqual(len(provider.tasks), 5)
        self.assertEqual(provider.tasks[0].role, "Lead")


if __name__ == "__main__":
    unittest.main()
