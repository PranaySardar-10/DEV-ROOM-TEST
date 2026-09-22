import unittest

from devroom.orchestrator import AgentResult, AgentTask
from devroom.provider_registry import ProviderRegistry


class Provider:
    def execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(task.role, "ok")


class ProviderRegistryTests(unittest.TestCase):
    def test_register_get_and_snapshot(self) -> None:
        registry = ProviderRegistry()
        provider = Provider()
        registry.register("codex", provider)

        self.assertIs(registry.get("codex"), provider)
        self.assertEqual(registry.snapshot(), ("codex",))
        self.assertIs(registry.as_mapping()["codex"], provider)

    def test_blank_and_duplicate_names_are_rejected(self) -> None:
        registry = ProviderRegistry()
        registry.register("codex", Provider())

        with self.assertRaises(ValueError):
            registry.register("   ", Provider())
        with self.assertRaises(ValueError):
            registry.register("codex", Provider())

    def test_missing_provider_fails_loudly(self) -> None:
        with self.assertRaises(KeyError):
            ProviderRegistry().get("missing")


if __name__ == "__main__":
    unittest.main()
