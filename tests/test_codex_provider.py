import unittest

from devroom.codex_provider import CodexCliConfig, CodexCliProvider
from devroom.orchestrator import AgentTask
from devroom.sandbox_policy import READ_ONLY, WORKSPACE_WRITE


class CodexCliProviderTests(unittest.TestCase):
    def test_extracts_last_agent_message_from_jsonl(self) -> None:
        jsonl = '''
{"type":"thread.started","thread_id":"test"}
{"type":"item.completed","item":{"type":"agent_message","text":"first"}}
{"type":"item.completed","item":{"type":"command_execution","command":"python -m unittest"}}
{"type":"item.completed","item":{"type":"agent_message","text":"final result"}}
{"type":"turn.completed"}
'''
        self.assertEqual(CodexCliProvider._extract_final_message(jsonl), "final result")

    def test_ignores_non_json_lines_and_missing_messages(self) -> None:
        self.assertEqual(
            CodexCliProvider._extract_final_message("progress\nnot-json\n{\"type\":\"turn.completed\"}\n"),
            "",
        )

    def test_build_command_uses_role_sandbox(self) -> None:
        task = AgentTask(
            role="Reviewer",
            goal="Inspect the current diff.",
            context={"workspace": r"D:\DEV_ROOM_TEST", "sandbox": READ_ONLY},
        )
        command = CodexCliProvider()._build_command(task, r"D:\DEV_ROOM_TEST")
        self.assertEqual(command[5:7], ["--sandbox", READ_ONLY])

        implementer = AgentTask(
            role="Implementer",
            goal="Implement the approved change.",
            context={"workspace": r"D:\DEV_ROOM_TEST", "sandbox": WORKSPACE_WRITE},
        )
        command = CodexCliProvider()._build_command(implementer, r"D:\DEV_ROOM_TEST")
        self.assertEqual(command[5:7], ["--sandbox", WORKSPACE_WRITE])

    def test_direct_implementer_defaults_to_workspace_write(self) -> None:
        provider = CodexCliProvider()
        task = AgentTask(role="Implementer", goal="Implement", context={"workspace": r"D:\\DEV_ROOM_TEST"})
        self.assertEqual(provider._effective_sandbox(task), WORKSPACE_WRITE)

    def test_read_only_role_rejects_workspace_write(self) -> None:
        provider = CodexCliProvider()
        task = AgentTask(
            role="Reviewer",
            goal="Inspect",
            context={"workspace": r"D:\DEV_ROOM_TEST", "sandbox": WORKSPACE_WRITE},
        )
        with self.assertRaises(PermissionError):
            provider._effective_sandbox(task)

    def test_legacy_config_can_only_tighten(self) -> None:
        provider = CodexCliProvider(CodexCliConfig(sandbox=READ_ONLY))
        task = AgentTask(
            role="Implementer",
            goal="Implement",
            context={"workspace": r"D:\DEV_ROOM_TEST"},
        )
        self.assertEqual(provider._effective_sandbox(task), READ_ONLY)

        with self.assertRaises(PermissionError):
            CodexCliProvider(CodexCliConfig(sandbox=WORKSPACE_WRITE))._effective_sandbox(
                AgentTask(role="Reviewer", goal="Review", context={"workspace": r"D:\DEV_ROOM_TEST"})
            )

    def test_execute_requires_explicit_workspace(self) -> None:
        with self.assertRaises(ValueError):
            CodexCliProvider().execute(AgentTask(role="Reviewer", goal="Inspect", context={}))


if __name__ == "__main__":
    unittest.main()
