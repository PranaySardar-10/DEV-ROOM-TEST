import unittest
from unittest.mock import patch

from devroom.provider_factory import ProviderSpec, build_default_factory
from devroom.provider_health import diagnose_providers


class LocalQwenIntegrationTests(unittest.TestCase):
    def test_default_factory_builds_local_qwen_provider(self) -> None:
        provider = build_default_factory().create(
            ProviderSpec(
                "qwen2.5-coder-3b-local",
                "local-qwen-ollama",
                {"model": "qwen2.5-coder:3b"},
            )
        )
        self.assertEqual(provider.__class__.__name__, "LocalQwenProvider")

    def test_default_factory_builds_generic_local_ollama_provider(self) -> None:
        provider = build_default_factory().create(
            ProviderSpec("gemma4-e4b-local", "local-ollama", {"model": "gemma4:e4b"})
        )
        self.assertEqual(provider.__class__.__name__, "LocalOllamaProvider")

    @patch("devroom.provider_health.shutil.which", return_value="C:/tools/ollama.exe")
    def test_local_qwen_cli_is_reported_available(self, _which) -> None:
        result = diagnose_providers(
            [
                ProviderSpec(
                    "qwen2.5-coder-3b-local",
                    "local-qwen-ollama",
                    {"model": "qwen2.5-coder:3b"},
                )
            ]
        )
        self.assertTrue(result[0].available)
        self.assertIn("qwen2.5-coder:3b", result[0].message)

    @patch("devroom.provider_health.shutil.which", return_value=None)
    def test_local_qwen_cli_is_reported_unavailable(self, _which) -> None:
        result = diagnose_providers(
            [ProviderSpec("local", "local-qwen-ollama")]
        )
        self.assertFalse(result[0].available)


if __name__ == "__main__":
    unittest.main()
