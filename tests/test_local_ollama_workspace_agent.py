import tempfile
import unittest

from devroom.local_ollama_workspace_agent import LocalOllamaWorkspaceAgent
from devroom.orchestrator import AgentTask
from devroom.sandbox_policy import WORKSPACE_WRITE
from devroom.workspace_provider import LocalWorkspaceProvider


class LocalOllamaWorkspaceAgentTests(unittest.TestCase):
    def task(self, **extra):
        context = {
            "sandbox": WORKSPACE_WRITE,
            "allowed_paths": "Assets/Test.cs",
        }
        context.update(extra)
        return AgentTask("Implementer", "Implement the approved change", context)

    def test_non_json_output_is_rejected_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = LocalWorkspaceProvider(directory)
            agent = LocalOllamaWorkspaceAgent(model="qwen3.5:3b")
            agent._parse_payload("not json")
            self.fail("expected parser to reject invalid JSON")

    def test_payload_parser_requires_object(self):
        with self.assertRaises(RuntimeError):
            LocalOllamaWorkspaceAgent._parse_payload("[]")

    def test_scope_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = LocalWorkspaceProvider(directory)
            agent = LocalOllamaWorkspaceAgent(model="qwen3.5:3b")
            with self.assertRaises(ValueError):
                agent.execute_in_workspace(
                    AgentTask(
                        "Implementer",
                        "Implement",
                        {"sandbox": WORKSPACE_WRITE},
                    ),
                    workspace,
                )


if __name__ == "__main__":
    unittest.main()
