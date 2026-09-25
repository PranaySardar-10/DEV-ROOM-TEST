import json
import unittest
from unittest.mock import patch

from devroom.local_ollama_provider import LocalOllamaConfig, LocalOllamaProvider
from devroom.orchestrator import AgentTask
from devroom.process_runner import ProcessRunResult


class LocalOllamaProviderTests(unittest.TestCase):
    @patch("devroom.local_ollama_provider.run_with_stall_timeout")
    def test_uses_chat_api_with_thinking_disabled(self, run) -> None:
        run.return_value = ProcessRunResult(
            '{"message":{"content":"Architect result"}}\n',
            "",
            0,
        )
        provider = LocalOllamaProvider(LocalOllamaConfig(model="gemma4:e4b"))
        result = provider.execute(
            AgentTask(
                "Architect",
                "Design it",
                {"role_instructions": "Produce implementation specification only."},
            )
        )
        self.assertEqual(result.summary, "Architect result")
        command = run.call_args.args[0]
        self.assertEqual(command[0], "curl.exe")
        self.assertEqual(command[1], "-sN")
        self.assertEqual(command[-1], "@-")
        self.assertEqual(run.call_args.kwargs["input_data"], run.call_args.kwargs["input_data"])
        payload = json.loads(run.call_args.kwargs["input_data"])
        self.assertEqual(payload["model"], "gemma4:e4b")
        self.assertFalse(payload["think"])
        self.assertTrue(payload["stream"])
        self.assertEqual(payload["options"]["num_predict"], 4096)
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertIn("implementation specification", payload["messages"][0]["content"])

    @patch("devroom.local_ollama_provider.run_with_stall_timeout")
    def test_nonzero_exit_is_reported(self, run) -> None:
        run.return_value = ProcessRunResult("", "model missing", 1)
        with self.assertRaisesRegex(RuntimeError, "model missing"):
            LocalOllamaProvider(LocalOllamaConfig(model="gemma4:e4b")).execute(
                AgentTask("Architect", "Design it")
            )

    @patch("devroom.local_ollama_provider.run_with_stall_timeout")
    def test_stall_is_reported(self, run) -> None:
        run.side_effect = TimeoutError("stalled")
        with self.assertRaises(TimeoutError):
            LocalOllamaProvider(LocalOllamaConfig(model="gemma4:e4b", stall_timeout_seconds=5)).execute(
                AgentTask("Architect", "Design it")
            )

    @patch("devroom.local_ollama_provider.run_with_stall_timeout")
    def test_role_generation_budget_override_is_used(self, run) -> None:
        run.return_value = ProcessRunResult(
            '{"message":{"content":"Coder result"}}\n',
            "",
            0,
        )
        provider = LocalOllamaProvider(LocalOllamaConfig(model="gemma4:e4b"))
        provider.execute(
            AgentTask(
                "Coder",
                "Write the proposal",
                {
                    "role_instructions": "Produce all five proposal sections.",
                    "generation_num_predict": "8192",
                },
            )
        )
        payload = json.loads(run.call_args.kwargs["input_data"])
        self.assertEqual(payload["options"]["num_predict"], 8192)


if __name__ == "__main__":
    unittest.main()
