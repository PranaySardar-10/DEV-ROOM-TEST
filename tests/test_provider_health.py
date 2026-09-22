import unittest
from unittest.mock import patch

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

    @patch("devroom.provider_health.shutil.which", return_value=None)
    def test_require_available_providers_fails_with_diagnostic(self, _which) -> None:
        with self.assertRaisesRegex(RuntimeError, "codex.*not found"):
            require_available_providers([ProviderSpec("codex", "codex-cli")])


if __name__ == "__main__":
    unittest.main()
