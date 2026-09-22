import json
import tempfile
import unittest
from pathlib import Path

from devroom.config import load_config, write_example_config


class ConfigTests(unittest.TestCase):
    def test_loads_provider_and_role_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "devroom.json"
            path.write_text(json.dumps({
                "providers": [
                    {"name": "worker", "kind": "fake", "options": {"label": "test"}}
                ],
                "bindings": {
                    "Implementer": {
                        "provider": "worker",
                        "instructions": "Implement only.",
                        "sandbox": "workspace-write",
                    }
                },
            }), encoding="utf-8")

            config = load_config(path)
            self.assertEqual(config.providers[0].name, "worker")
            self.assertEqual(config.providers[0].kind, "fake")
            self.assertEqual(config.providers[0].options["label"], "test")
            self.assertEqual(config.bindings["Implementer"].sandbox, "workspace-write")

    def test_default_bindings_are_used_when_omitted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "devroom.json"
            path.write_text('{"providers": []}', encoding="utf-8")
            config = load_config(path)
            self.assertIn("Implementer", config.bindings)

    def test_example_config_is_valid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_example_config(Path(tmp) / "devroom.example.json")
            config = load_config(path)
            self.assertEqual(config.providers[0].kind, "codex-cli")
            self.assertEqual(config.bindings["Implementer"].sandbox, "workspace-write")


if __name__ == "__main__":
    unittest.main()
