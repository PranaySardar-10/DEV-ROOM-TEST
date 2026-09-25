from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from devroom.local_ollama_provider import LocalOllamaConfig, LocalOllamaProvider
from devroom.orchestrator import AgentTask


class LocalOllamaGenerationBudgetTests(unittest.TestCase):
    def _task(self) -> AgentTask:
        return AgentTask(
            role="Coder",
            goal="Produce an implementation proposal.",
            context={
                "role_instructions": "Produce a complete reviewable proposal.",
                "task_specification": "Create the required files and verification steps.",
            },
        )

    def test_default_generation_budget_is_explicitly_sent(self) -> None:
        captured = {}

        def fake_runner(command, *, input_data, stall_timeout_seconds):
            captured["command"] = command
            captured["input_data"] = input_data
            captured["input_data"] = input_data
            captured["input_data"] = input_data
            return type("Completed", (), {
                "returncode": 0,
                "stdout": '{"message":{"content":"complete proposal"}}\n{"done":true}\n',
                "stderr": "",
            })()

        with patch("devroom.local_ollama_provider.run_with_stall_timeout", side_effect=fake_runner):
            result = LocalOllamaProvider(
                LocalOllamaConfig(model="gemma4:e4b")
            ).execute(self._task())

        payload = json.loads(captured["input_data"])
        self.assertEqual(payload["options"]["num_predict"], 4096)
        self.assertFalse(payload["think"])
        self.assertEqual(result.summary, "complete proposal")

    def test_custom_generation_budget_is_sent(self) -> None:
        captured = {}

        def fake_runner(command, *, input_data, stall_timeout_seconds):
            captured["command"] = command
            return type("Completed", (), {
                "returncode": 0,
                "stdout": '{"message":{"content":"proposal"}}\n',
                "stderr": "",
            })()

        with patch("devroom.local_ollama_provider.run_with_stall_timeout", side_effect=fake_runner):
            LocalOllamaProvider(
                LocalOllamaConfig(model="gemma4:e4b", num_predict=8192)
            ).execute(self._task())

        payload = json.loads(captured["input_data"])
        self.assertEqual(payload["options"]["num_predict"], 8192)

    def test_invalid_generation_budget_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            LocalOllamaProvider(
                LocalOllamaConfig(model="gemma4:e4b", num_predict=0)
            )


if __name__ == "__main__":
    unittest.main()
