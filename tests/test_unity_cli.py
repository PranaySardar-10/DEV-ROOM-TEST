import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from devroom.unity_cli import UnityCliResult, UnityCliRunner


class UnityCliRunnerTests(unittest.TestCase):
    def test_build_command_contains_project_and_execute_method(self) -> None:
        runner = UnityCliRunner(
            executable=r"D:\Unity\Editor\Unity.exe",
            method="OmniverselCliAutomation.ValidateCharacterPrototype",
            log_file=r"D:\logs\unity.log",
        )

        command = runner.build_command(r"D:\Project")

        self.assertEqual(command[0], r"D:\Unity\Editor\Unity.exe")
        self.assertIn("-accept-apiupdate", command)
        self.assertIn("-batchmode", command)
        self.assertIn("-quit", command)
        self.assertIn("-projectPath", command)
        self.assertIn("OmniverselCliAutomation.ValidateCharacterPrototype", command)
        self.assertIn("-logFile", command)

    def test_run_requires_existing_workspace_and_executable(self) -> None:
        runner = UnityCliRunner(
            executable=r"D:\missing\Unity.exe",
            method="Example.Validate",
        )

        with self.assertRaises(FileNotFoundError):
            runner.run(r"D:\missing\Project")

    def test_run_returns_success_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "Project"
            executable = workspace / "Unity.exe"
            workspace.mkdir()
            executable.write_text("test", encoding="utf-8")

            completed = type(
                "Completed",
                (),
                {
                    "stdout": "UNITY PASS",
                    "stderr": "",
                    "returncode": 0,
                },
            )()

            with patch(
                "devroom.unity_cli.run_with_stall_timeout",
                return_value=completed,
            ) as run:
                runner = UnityCliRunner(
                    executable=str(executable),
                    method="Example.Validate",
                )
                result = runner.run(str(workspace))

            run.assert_called_once()
            self.assertIsInstance(result, UnityCliResult)
            self.assertTrue(result.succeeded)
            self.assertEqual(result.returncode, 0)
            self.assertIn("-executeMethod", result.command)
            self.assertIn("Example.Validate", result.command)

    def test_run_reports_nonzero_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "Project"
            executable = workspace / "Unity.exe"
            workspace.mkdir()
            executable.write_text("test", encoding="utf-8")

            completed = type(
                "Completed",
                (),
                {
                    "stdout": "",
                    "stderr": "validation failed",
                    "returncode": 1,
                },
            )()

            with patch(
                "devroom.unity_cli.run_with_stall_timeout",
                return_value=completed,
            ):
                runner = UnityCliRunner(
                    executable=str(executable),
                    method="Example.Validate",
                )
                result = runner.run(str(workspace))

            self.assertFalse(result.succeeded)
            self.assertEqual(result.returncode, 1)
            self.assertIn("validation failed", result.summary())


if __name__ == "__main__":
    unittest.main()
