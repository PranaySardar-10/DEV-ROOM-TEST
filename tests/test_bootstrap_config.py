import json
import tempfile
import unittest
from pathlib import Path

from devroom.bootstrap import build_from_config, build_from_config_file
from devroom.config import load_config
from devroom.orchestrator import AgentResult, AgentTask
from devroom.provider_factory import ProviderFactory


class RecordingProvider:
    def execute(self, task: AgentTask) -> AgentResult:
        return AgentResult(task.role, "ok", ("artifact",))


class BootstrapConfigTests(unittest.TestCase):
    def _factory(self) -> ProviderFactory:
        factory = ProviderFactory()
        factory.register("fake", lambda _: RecordingProvider())
        return factory

    def _config_path(self, tmp: str) -> Path:
        path = Path(tmp) / "devroom.json"
        path.write_text(json.dumps({
            "providers": [{"name": "worker", "kind": "fake"}],
            "bindings": {
                role: {
                    "provider": "worker",
                    "instructions": f"{role} instructions",
                    "sandbox": "workspace-write" if role == "Implementer" else "read-only",
                }
                for role in ("Lead", "Architect", "Coder", "Implementer", "QA")
            },
        }), encoding="utf-8")
        return path

    def test_build_from_loaded_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_config(self._config_path(tmp))
            orchestrator = build_from_config(config, factory=self._factory())
            result = orchestrator.run("config integration")
            self.assertEqual(result.stage.value, "halted")

    def test_build_directly_from_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            orchestrator = build_from_config_file(
                self._config_path(tmp),
                factory=self._factory(),
            )
            result = orchestrator.run("config file integration")
            self.assertEqual(result.stage.value, "halted")


if __name__ == "__main__":
    unittest.main()
