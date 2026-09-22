import unittest

from devroom.orchestrator import AgentResult, AgentTask
from devroom.provider_factory import ProviderFactory, ProviderSpec, build_default_factory


class RecordingProvider:
    def __init__(self, label: str) -> None:
        self.label = label
        self.tasks = []

    def execute(self, task: AgentTask) -> AgentResult:
        self.tasks.append(task)
        return AgentResult(task.role, self.label, ("artifact",))


class ProviderFactoryTests(unittest.TestCase):
    def test_factory_builds_named_registry_from_specs(self) -> None:
        factory = ProviderFactory()
        factory.register(
            "fake",
            lambda options: RecordingProvider(str(options["label"])),
        )

        registry = factory.build_registry(
            [
                ProviderSpec("alpha", "fake", {"label": "A"}),
                ProviderSpec("beta", "fake", {"label": "B"}),
            ]
        )

        self.assertEqual(registry.snapshot(), ("alpha", "beta"))
        self.assertEqual(registry.get("alpha").label, "A")
        self.assertEqual(registry.get("beta").label, "B")

    def test_unknown_kind_is_rejected(self) -> None:
        factory = ProviderFactory()
        with self.assertRaises(KeyError):
            factory.create(ProviderSpec("missing", "unknown"))

    def test_duplicate_kind_registration_is_rejected(self) -> None:
        factory = ProviderFactory()
        factory.register("fake", lambda _: RecordingProvider("one"))
        with self.assertRaises(ValueError):
            factory.register("fake", lambda _: RecordingProvider("two"))

    def test_default_factory_registers_codex_builder(self) -> None:
        factory = build_default_factory()
        provider = factory.create(
            ProviderSpec(
                "codex",
                "codex-cli",
                {"command": "codex", "ephemeral": True, "timeout_seconds": 60},
            )
        )
        self.assertEqual(provider.__class__.__name__, "CodexCliProvider")


if __name__ == "__main__":
    unittest.main()
