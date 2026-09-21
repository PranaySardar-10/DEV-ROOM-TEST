import unittest

from devroom.codex_provider import CodexCliProvider
from devroom.orchestrator import AgentTask


class CodexCliProviderTests(unittest.TestCase):
    def test_extracts_last_agent_message_from_jsonl(self) -> None:
        jsonl = """
{"type":"thread.started","thread_id":"test"}
{"type":"item.completed","item":{"type":"agent_message","text":"first"}}
{"type":"item.completed","item":{"type":"command_execution","command":"python -m unittest"}}
{"type":"item.completed","item":{"type":"agent_message","text":"final result"}}
{"type":"turn.completed"}
"""
        self.assertEqual(
            CodexCliProvider._extract_final_message(jsonl),
            "final result",
        )

    def test_ignores_non_json_lines_and_missing_messages(self) -> None:
        self.assertEqual(
            CodexCliProvider._extract_final_message(
                "progress\nnot-json\n{\"type\":\"turn.completed\"}\n"
            ),
            "",
        )

    def test_build_command_targets_explicit_workspace(self) -> None:
        task = AgentTask(
            role="Reviewer",
            goal="Inspect the current diff.",
            context={"workspace": r"D:\DEV_ROOM_TEST", "role_instructions": "Read only."},
        )
        command = CodexCliProvider()._build_command(task, r"D:\DEV_ROOM_TEST")
        self.assertEqual(
            command[:8],
            [
                "codex",
                "exec",
                "--json",
                "--cd",
                r"D:\DEV_ROOM_TEST",
                "--sandbox",
                "workspace-write",
                "--ephemeral",
            ],
        )

    def test_execute_requires_explicit_workspace(self) -> None:
        provider = CodexCliProvider()
        task = AgentTask(role="Reviewer", goal="Inspect the repository.", context={})
        with self.assertRaises(ValueError):
            provider.execute(task)


if __name__ == "__main__":
    unittest.main()
