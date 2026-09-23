import unittest
from unittest.mock import patch

from devroom.local_qwen_provider import LocalQwenConfig, LocalQwenProvider
from devroom.orchestrator import AgentTask
from devroom.process_runner import ProcessRunResult


class LocalQwenProviderTests(unittest.TestCase):
    @patch("devroom.local_qwen_provider.run_with_stall_timeout")
    def test_executes_configured_model_and_returns_output(self, run) -> None:
        run.return_value = ProcessRunResult("QA evidence", "", 0)
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

    @patch("devroom.local_qwen_provider.run_with_stall_timeout")
    def test_nonzero_exit_is_reported(self, run) -> None:
        run.return_value = ProcessRunResult("", "model missing", 1)
        with self.assertRaisesRegex(RuntimeError, "model missing"):
            LocalQwenProvider().execute(AgentTask("QA", "Validate it"))

    @patch("devroom.local_qwen_provider.run_with_stall_timeout")
    def test_timeout_is_reported(self, run) -> None:
        run.side_effect = TimeoutError("stalled")
        with self.assertRaises(TimeoutError):
            LocalQwenProvider(LocalQwenConfig(stall_timeout_seconds=5)).execute(
                AgentTask("QA", "Validate it")
            )


if __name__ == "__main__":
    unittest.main()
