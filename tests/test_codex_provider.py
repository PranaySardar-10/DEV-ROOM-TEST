import unittest

from devroom.codex_provider import CodexCliProvider


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


if __name__ == "__main__":
    unittest.main()
