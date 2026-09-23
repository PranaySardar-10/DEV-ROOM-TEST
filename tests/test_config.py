import json
import tempfile
import unittest
from pathlib import Path

from devroom.config import load_config, validate_config, write_example_config


class ConfigTests(unittest.TestCase):
    def test_loads_provider_and_role_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "devroom.json"
            path.write_text(json.dumps({
                "providers": [{"name": "worker", "kind": "fake", "options": {"label": "test"}}],
                "bindings": {
                    role: {
                        "provider": "worker",
                        "instructions": f"{role} instructions",
                        "sandbox": "workspace-write" if role == "Implementer" else "read-only",
                    }
                    for role in ("Lead", "Architect", "Coder", "Implementer", "QA")
                },
            }), encoding="utf-8")

            config = load_config(path)
            self.assertEqual(config.providers[0].name, "worker")
            self.assertEqual(config.providers[0].kind, "fake")
            self.assertEqual(config.providers[0].options["label"], "test")
            validate_config(config)

    def test_default_bindings_are_used_when_omitted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "devroom.json"
            path.write_text('{"providers": []}', encoding="utf-8")
            config = load_config(path)
            self.assertIn("Implementer", config.bindings)

    def test_rejects_invalid_resource_cooldowns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for value in ("not-a-number", "NaN", "Infinity", "-Infinity", -1):
                path = Path(tmp) / "devroom.json"
                path.write_text(
                    json.dumps({
                        "providers": [],
                        "resource_guard": {
                            "cooldown_after_seconds": value,
                            "cooldown_seconds": 45,
                        },
                    }),
                    encoding="utf-8",
                )
                with self.assertRaises(ValueError):
                    load_config(path)

    def test_example_config_is_valid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_example_config(Path(tmp) / "devroom.example.json")
            config = load_config(path)
            validate_config(config)
            self.assertEqual(config.providers[0].kind, "local-ollama")
            self.assertEqual(config.providers[1].kind, "local-ollama-workspace")
            self.assertEqual(config.providers[1].options["model"], "gemma4:e4b")
            self.assertEqual(config.providers[2].options["model"], "qwen3.5:4b")
            providers_by_name = {provider.name: provider for provider in config.providers}
            self.assertEqual(
                providers_by_name["qwen2.5-coder-3b-workspace-local"].options["model"],
                "qwen2.5-coder:3b",
            )
            self.assertEqual(
                config.bindings["Implementer"].provider,
                "qwen2.5-coder-3b-workspace-local",
            )
            self.assertEqual(config.bindings["Implementer"].sandbox, "workspace-write")


if __name__ == "__main__":
    unittest.main()
