import tempfile
import unittest
from unittest.mock import patch

from devroom.local_ollama_workspace_agent import LocalOllamaWorkspaceAgent
from devroom.orchestrator import AgentTask
from devroom.sandbox_policy import WORKSPACE_WRITE
from devroom.workspace_provider import LocalWorkspaceProvider


class LocalOllamaWorkspaceAgentTests(unittest.TestCase):
    def test_non_json_output_is_rejected(self):
        with self.assertRaises(RuntimeError):
            LocalOllamaWorkspaceAgent._parse_payload("not json")

    def test_payload_parser_requires_object(self):
        with self.assertRaises(RuntimeError):
            LocalOllamaWorkspaceAgent._parse_payload("[]")

    def test_scope_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = LocalWorkspaceProvider(directory)
            agent = LocalOllamaWorkspaceAgent(model="qwen3.5:4b")
            with self.assertRaises(ValueError):
                agent.execute_in_workspace(
                    AgentTask(
                        "Implementer",
                        "Implement",
                        {"sandbox": WORKSPACE_WRITE},
                    ),
                    workspace,
                )

    @patch("devroom.local_ollama_workspace_agent.subprocess.run")
    def test_implementer_requests_json_mode(self, run):
        class Completed:
            returncode = 0
            stdout = '{"summary":"ok","files":[{"path":"smoke_test.txt","content":"ok"}]}'
            stderr = ""

        run.return_value = Completed()
        with tempfile.TemporaryDirectory() as directory:
            workspace = LocalWorkspaceProvider(directory)
            agent = LocalOllamaWorkspaceAgent(model="qwen3.5:4b")
            result = agent.execute_in_workspace(
                AgentTask(
                    "Implementer",
                    "Create smoke_test.txt",
                    {
                        "sandbox": WORKSPACE_WRITE,
                        "allowed_paths": "smoke_test.txt",
                    },
                ),
                workspace,
            )

        self.assertEqual(result.artifacts, ("smoke_test.txt",))
        self.assertEqual(
            run.call_args.args[0][:5],
            ("ollama", "run", "qwen3.5:4b", "--format", "json"),
        )


if __name__ == "__main__":
    unittest.main()
