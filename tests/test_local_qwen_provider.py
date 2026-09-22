import subprocess
import unittest
from unittest.mock import patch

from devroom.local_qwen_provider import LocalQwenConfig, LocalQwenProvider
from devroom.orchestrator import AgentTask


class LocalQwenProviderTests(unittest.TestCase):
    @patch("devroom.local_qwen_provider.subprocess.run")
    def test_executes_configured_model_and_returns_output(self, run) -> None:
        run.return_value = subprocess.CompletedProcess(
            args=("ollama", "run", "qwen2.5-coder:3b", "prompt"),
            returncode=0,
            stdout="QA evidence",
            stderr="",
        )
        provider = LocalQwenProvider()
        result = provider.execute(
            AgentTask("QA", "Validate it", {"provider": "local-qwen"})
        )
        self.assertEqual(result.role, "QA")
        self.assertEqual(result.summary, "QA evidence")
        self.assertEqual(result.artifacts, ())
        command = run.call_args.args[0]
        self.assertEqual(command[:3], ("ollama", "run", "qwen2.5-coder:3b"))
        self.assertIn("Validate it", command[3])
        self.assertIn("QA", command[3])

    @patch("devroom.local_qwen_provider.subprocess.run")
    def test_nonzero_exit_is_reported(self, run) -> None:
        run.return_value = subprocess.CompletedProcess(
            args=(), returncode=1, stdout="", stderr="model missing"
        )
        with self.assertRaisesRegex(RuntimeError, "model missing"):
            LocalQwenProvider().execute(AgentTask("QA", "Validate it"))

    @patch("devroom.local_qwen_provider.subprocess.run")
    def test_timeout_is_reported(self, run) -> None:
        run.side_effect = subprocess.TimeoutExpired(("ollama",), 5)
        with self.assertRaises(TimeoutError):
            LocalQwenProvider(LocalQwenConfig(timeout_seconds=5)).execute(
                AgentTask("QA", "Validate it")
            )


if __name__ == "__main__":
    unittest.main()
