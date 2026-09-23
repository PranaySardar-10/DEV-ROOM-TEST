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
        self.assertIsNone(LocalOllamaWorkspaceAgent._try_parse_json("not json"))

    def test_wrapped_json_payload_is_extracted(self):
        output = 'Model preface: \\n{"summary":"ok","files":[{"path":"smoke_test.txt","content":"ok"}]}'
        payload = LocalOllamaWorkspaceAgent._try_parse_json(output)
        self.assertEqual(payload["files"][0]["path"], "smoke_test.txt")

    def test_ollama_response_envelope_is_parsed(self):
        output = '{"model":"gemma4:e4b","response":"{\\\"summary\\\":\\\"ok\\\",\\\"files\\\":[{\\\"path\\\":\\\"smoke_test.txt\\\",\\\"content\\\":\\\"ok\\\"}]}","done":true}'
        envelope = json.loads(output)
        payload = LocalOllamaWorkspaceAgent._try_parse_json(envelope["response"])
        self.assertEqual(payload["files"][0]["content"], "ok")

    def test_multiline_json_string_is_recovered(self):
        output = '{"summary":"ok","files":[{"path":"script.txt","content":"line one\\nline two"}]}'
        payload = LocalOllamaWorkspaceAgent._try_parse_json(output)
        self.assertEqual(payload["files"][0]["content"], "line one\nline two")

    def test_empty_api_response_is_rejected(self):
        with patch("devroom.local_ollama_workspace_agent.urllib.request.urlopen") as urlopen:
            response = MagicMock()
            response.read.return_value = b""
            urlopen.return_value.__enter__.return_value = response
            with self.assertRaises(RuntimeError):
                LocalOllamaWorkspaceAgent(model="gemma4:e4b")._generate_structured("test")

    def test_non_json_api_response_is_rejected(self):
        with patch("devroom.local_ollama_workspace_agent.urllib.request.urlopen") as urlopen:
            response = MagicMock()
            response.read.return_value = b"not json"
            urlopen.return_value.__enter__.return_value = response
            with self.assertRaises(RuntimeError):
                LocalOllamaWorkspaceAgent(model="gemma4:e4b")._generate_structured("test")

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

    def test_write_failure_rolls_back_all_changes(self) -> None:
        class FailingWorkspace(LocalWorkspaceProvider):
            def __init__(self, workspace):
                super().__init__(workspace)
                self.write_count = 0

            def write_file(self, relative_path, content):
                self.write_count += 1
                path = super().write_file(relative_path, content)
                if self.write_count == 2:
                    raise OSError("disk write failed")
                return path

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.txt").write_text("original", encoding="utf-8")
            workspace = FailingWorkspace(root)
            task = AgentTask(
                role="Implementer",
                goal="Update two files",
                context={
                    "sandbox": WORKSPACE_WRITE,
                    "allowed_paths": "a.txt,b.txt",
                },
            )
            agent = LocalOllamaWorkspaceAgent(model="gemma4:e4b")
            with unittest.mock.patch.object(
                agent,
                "_generate_structured",
                return_value={
                    "summary": "two files",
                    "files": [
                        {"path": "a.txt", "content": "changed"},
                        {"path": "b.txt", "content": "created"},
                    ],
                },
            ):
                with self.assertRaisesRegex(OSError, "disk write failed"):
                    agent.execute_in_workspace(task, workspace)

            self.assertEqual((root / "a.txt").read_text(encoding="utf-8"), "original")
            self.assertFalse((root / "b.txt").exists())


if __name__ == "__main__":
    unittest.main()
