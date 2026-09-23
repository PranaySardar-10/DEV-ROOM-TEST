import json
import unittest
from unittest.mock import patch, MagicMock

from devroom.provider_factory import ProviderSpec
from devroom.provider_health import diagnose_providers, require_available_providers


class ProviderHealthTests(unittest.TestCase):
    @patch("devroom.provider_health.shutil.which", return_value="C:/tools/codex.exe")
    def test_codex_is_reported_available(self, _which) -> None:
        result = diagnose_providers([ProviderSpec("codex", "codex-cli")])
        self.assertTrue(result[0].available)

    @patch("devroom.provider_health.shutil.which", return_value=None)
    def test_codex_is_reported_unavailable(self, _which) -> None:
        result = diagnose_providers([ProviderSpec("codex", "codex-cli")])
        self.assertFalse(result[0].available)

    def test_unknown_provider_kind_is_not_claimed_available(self) -> None:
        result = diagnose_providers([ProviderSpec("local", "qwen-local")])
        self.assertFalse(result[0].available)

    @patch("devroom.provider_health.urllib.request.urlopen")
    @patch("devroom.provider_health.shutil.which", return_value="C:/tools/ollama.exe")
    def test_ollama_is_available_when_api_and_model_are_ready(self, _which, urlopen) -> None:
        response = MagicMock()
        response.read.return_value = json.dumps(
            {"models": [{"name": "gemma4:e4b"}, {"name": "qwen3.5:4b"}]}
        ).encode("utf-8")
        urlopen.return_value.__enter__.return_value = response

        result = diagnose_providers(
            [ProviderSpec("gemma", "local-ollama", {"model": "gemma4:e4b"})]
        )
        self.assertTrue(result[0].available)
        self.assertIn("model is installed", result[0].message)

    @patch("devroom.provider_health.urllib.request.urlopen")
    @patch("devroom.provider_health.shutil.which", return_value="C:/tools/ollama.exe")
    def test_ollama_is_unavailable_when_model_is_missing(self, _which, urlopen) -> None:
        response = MagicMock()
        response.read.return_value = json.dumps({"models": [{"name": "qwen3.5:4b"}]}).encode("utf-8")
        urlopen.return_value.__enter__.return_value = response

        result = diagnose_providers(
            [ProviderSpec("gemma", "local-ollama", {"model": "gemma4:e4b"})]
        )
        self.assertFalse(result[0].available)
        self.assertIn("not installed", result[0].message)

    @patch("devroom.provider_health.urllib.request.urlopen", side_effect=OSError("connection refused"))
    @patch("devroom.provider_health.shutil.which", return_value="C:/tools/ollama.exe")
    def test_ollama_is_unavailable_when_api_cannot_be_reached(self, _which, _urlopen) -> None:
        result = diagnose_providers(
            [ProviderSpec("gemma", "local-ollama", {"model": "gemma4:e4b"})]
        )
        self.assertFalse(result[0].available)
        self.assertIn("API unavailable", result[0].message)

    @patch("devroom.provider_health.shutil.which", return_value=None)
    def test_require_available_providers_fails_with_diagnostic(self, _which) -> None:
        with self.assertRaisesRegex(RuntimeError, "ollama.*not found"):
            require_available_providers(
                [ProviderSpec("ollama", "local-ollama", {"model": "gemma4:e4b"})]
            )


if __name__ == "__main__":
    unittest.main()
