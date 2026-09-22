import tempfile
import unittest

from devroom.orchestrator import AgentResult, AgentTask
from devroom.provider_registry import ProviderRegistry
from devroom.provider_router import ProviderRouter, RoleBinding


class RecordingProvider:
    def __init__(self) -> None:
        self.tasks = []

    def execute(self, task: AgentTask) -> AgentResult:
        self.tasks.append(task)
        return AgentResult(task.role, "ok", ("artifact",))


class ProviderRegistryRouterTests(unittest.TestCase):
    def test_router_accepts_registry_mapping_without_owning_registration(self) -> None:
        registry = ProviderRegistry()
        provider = RecordingProvider()
        registry.register("codex", provider)

        router = ProviderRouter(
            registry.as_mapping(),
            {"Implementer": RoleBinding("codex", "Implement.", "workspace-write")},
        )

        result = router.execute(
            AgentTask(
                "Implementer",
                "Implement feature",
                {"workspace": tempfile.gettempdir()},
            )
        )

        self.assertEqual(result.artifacts, ("artifact",))
        self.assertIs(provider.tasks[0], provider.tasks[0])


if __name__ == "__main__":
    unittest.main()
