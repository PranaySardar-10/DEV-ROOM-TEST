import unittest

from devroom.bootstrap import build_orchestrator, build_provider_registry
from devroom.orchestrator import AgentResult, AgentTask
from devroom.provider_factory import ProviderFactory, ProviderSpec
from devroom.provider_router import RoleBinding


class RecordingProvider:
    def execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(task.role, "ok", ("artifact",))


class BootstrapTests(unittest.TestCase):
    def _factory(self) -> ProviderFactory:
        factory = ProviderFactory()
        factory.register("fake", lambda _: RecordingProvider())
        return factory

    def test_builds_registry_from_specs(self) -> None:
        registry = build_provider_registry(
            [ProviderSpec("worker", "fake")],
            factory=self._factory(),
        )
        self.assertEqual(registry.snapshot(), ("worker",))

    def test_builds_orchestrator_from_configuration(self) -> None:
        bindings = {
            role: RoleBinding("worker", f"{role} instructions")
            for role in ("Lead", "Architect", "Implementer", "Reviewer", "QA")
        }
        orchestrator = build_orchestrator(
            [ProviderSpec("worker", "fake")],
            bindings=bindings,
            factory=self._factory(),
        )
        result = orchestrator.run("bootstrap test")
        self.assertEqual(result.stage.value, "halted")


if __name__ == "__main__":
    unittest.main()
