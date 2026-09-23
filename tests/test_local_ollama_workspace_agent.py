import json
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from devroom.local_ollama_workspace_agent import ARTIFACT_SCHEMA, LocalOllamaWorkspaceAgent
from devroom.orchestrator import AgentTask
from devroom.sandbox_policy import WORKSPACE_WRITE
from devroom.workspace_provider import LocalWorkspaceProvider


class LocalOllamaWorkspaceAgentTests(unittest.TestCase):
    def test_non_json_output_is_rejected(self):
        with self.assertRaises(RuntimeError):
            LocalOllamaWorkspaceAgent._try_parse_json("not json")

    def test_wrapped_json_payload_is_extracted(self):
        output = 'Model preface: \\n{"summary":"ok","files":[{"path":"smoke_test.txt","content":"ok"}]}'
        payload = LocalOllamaWorkspaceAgent._try_parse_json(output)
        self.assertEqual(payload["files"][0]["path"], "smoke_test.txt")

    def test_ollama_response_envelope_is_parsed(self):
        output = '{"model":"gemma4:e4b","response":"{\\"summary\\":\\"ok\\",\\"files\\":[{\\"path\\":\\"smoke_test.txt\\",\\"content\\":\\"ok\\"}]}","done":true}'
        envelope = json.loads(output)
        payload = LocalOllamaWorkspaceAgent._try_parse_json(envelope["response"])
        self.assertEqual(payload["files"][0]["content"], "ok")

    def test_multiline_json_string_is_recovered(self):
        output = '{"summary":"ok","files":[{"path":"script.txt","content":"line one\\nline two"}]}'
        payload = LocalOllamaWorkspaceAgent._try_parse_json(output)
        self.assertEqual(payload["files"][0]["content"], "line one\nline two")

    def test_empty_output_is_rejected(self):
        with self.assertRaises(RuntimeError):
            LocalOllamaWorkspaceAgent._try_parse_json("")

    def test_scope_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = LocalWorkspaceProvider(directory)
            agent = LocalOllamaWorkspaceAgent(model="gemma4:e4b")
            with self.assertRaises(ValueError):
                agent.execute_in_workspace(
                    AgentTask(
                        "Implementer",
                        "Implement",
                        {"sandbox": WORKSPACE_WRITE},
                    ),
                    workspace,
                )

    @patch("devroom.local_ollama_workspace_agent.urllib.request.urlopen")
    def test_implementer_uses_structured_ollama_api(self, urlopen):
        response = MagicMock()
        response.read.return_value = json.dumps(
            {
                "model": "gemma4:e4b",
                "response": json.dumps(
                    {
                        "summary": "created smoke test",
                        "files": [
                            {
                                "path": "smoke_test.txt",
                                "content": "DevRoom live smoke test passed.",
                            }
                        ],
                    }
                ),
                "done": True,
            }
        ).encode("utf-8")
        urlopen.return_value.__enter__.return_value = response

        with tempfile.TemporaryDirectory() as directory:
            workspace = LocalWorkspaceProvider(directory)
            agent = LocalOllamaWorkspaceAgent(model="gemma4:e4b")
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
            self.assertEqual(
                workspace.read_file("smoke_test.txt"),
                "DevRoom live smoke test passed.",
            )

        self.assertEqual(result.artifacts, ("smoke_test.txt",))
        request = urlopen.call_args.args[0]
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(body["model"], "gemma4:e4b")
        self.assertFalse(body["stream"])
        self.assertEqual(body["format"], ARTIFACT_SCHEMA)
        self.assertEqual(body["options"]["temperature"], 0)
        self.assertEqual(request.full_url, "http://localhost:11434/api/generate")


if __name__ == "__main__":
    unittest.main()
