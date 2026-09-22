import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch

from devroom import cli
from devroom.provider_factory import ProviderSpec


class CliStartupTests(unittest.TestCase):
    def test_check_runs_provider_preflight_without_building_orchestrator(self):
        args = SimpleNamespace(
            config="devroom.json",
            goal=None,
            workspace=None,
            max_feedback_cycles=3,
            check=True,
        )
        config = SimpleNamespace(providers=(ProviderSpec("codex", "codex-cli"),))

        with (
            patch.object(cli, "_parse_args", return_value=args),
            patch.object(cli, "load_config", return_value=config),
            patch.object(cli, "require_available_providers") as health,
            patch.object(cli, "build_from_config") as build,
        ):
            output = io.StringIO()
            with redirect_stdout(output):
                result = cli.main()

        self.assertEqual(result, 0)
        health.assert_called_once_with(config.providers)
        build.assert_not_called()
        self.assertIn("startup checks passed", output.getvalue())

    def test_startup_failure_returns_exit_code_two(self):
        args = SimpleNamespace(
            config="devroom.json",
            goal="test goal",
            workspace="workspace",
            max_feedback_cycles=3,
            check=False,
        )

        with (
            patch.object(cli, "_parse_args", return_value=args),
            patch.object(cli, "load_config", side_effect=RuntimeError("provider unavailable")),
            patch.object(cli, "require_available_providers") as health,
            patch.object(cli, "build_from_config") as build,
        ):
            error = io.StringIO()
            with redirect_stderr(error):
                result = cli.main()

        self.assertEqual(result, 2)
        health.assert_not_called()
        build.assert_not_called()
        self.assertIn("provider unavailable", error.getvalue())


if __name__ == "__main__":
    unittest.main()
