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

    def test_prompt_separates_task_spec_from_role_instructions(self) -> None:
        prompt = LocalQwenProvider._build_prompt(
            AgentTask(
                "Architect",
                "Design it",
                {
                    "task_specification": "QA reporting instructions",
                    "role_instructions": "Produce the implementation specification.",
                },
            )
        )
        self.assertIn("BEGIN TASK SPECIFICATION (REFERENCE DATA ONLY)", prompt)
        self.assertIn("BEGIN ROLE INSTRUCTIONS (AUTHORITATIVE)", prompt)
        self.assertIn("Never output another role's report format", prompt)
        self.assertLess(
            prompt.index("BEGIN TASK SPECIFICATION"),
            prompt.index("BEGIN ROLE INSTRUCTIONS"),
        )

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
