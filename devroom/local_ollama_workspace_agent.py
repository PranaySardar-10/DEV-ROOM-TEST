from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from .orchestrator import AgentResult, AgentTask
from .sandbox_policy import WORKSPACE_WRITE
from .workspace_provider import LocalWorkspaceProvider


ARTIFACT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "files": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["summary", "files"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class LocalOllamaWorkspaceAgent:
    """Controlled local Ollama Implementer using structured API output."""

    command: str = "ollama"
    model: str = ""
    timeout_seconds: int = 600
    api_url: str = "http://localhost:11434/api/generate"

    def execute_in_workspace(
        self,
        task: AgentTask,
        workspace: LocalWorkspaceProvider,
    ) -> AgentResult:
        if task.role != "Implementer":
            raise PermissionError("LocalOllamaWorkspaceAgent is restricted to Implementer.")
        if task.context.get("sandbox") != WORKSPACE_WRITE:
            raise PermissionError("Implementer requires workspace-write.")
        if not self.model.strip():
            raise ValueError("Ollama model must not be blank.")

        allowed_raw = task.context.get("allowed_paths", "")
        allowed = {item.strip().replace("\\", "/") for item in allowed_raw.split(",") if item.strip()}
        if not allowed:
            raise ValueError("Implementer requires an explicit allowed_paths scope.")

        prompt = self._build_prompt(task, allowed, workspace)
        payload = self._generate_structured(prompt)
        files = payload.get("files")
        if not isinstance(files, list) or not files:
            raise RuntimeError("Implementer response contained no file changes.")

        validated: list[tuple[str, str]] = []
        seen: set[str] = set()
        for item in files:
            if not isinstance(item, dict):
                raise RuntimeError("Every file change must be an object.")
            relative_path = str(item.get("path", "")).replace("\\", "/").strip()
            content = item.get("content")
            if relative_path not in allowed:
                raise PermissionError(
                    f"Implementer attempted to modify a path outside its approved scope: {relative_path!r}"
                )
            if relative_path in seen:
                raise RuntimeError(f"Implementer returned duplicate file path: {relative_path!r}")
            if not isinstance(content, str):
                raise RuntimeError(f"File content must be a string: {relative_path!r}")
            seen.add(relative_path)
            validated.append((relative_path, content))

        # Validate the complete response before writing anything.
        original_contents: dict[str, str | None] = {}
        for relative_path, _content in validated:
            target = workspace._safe_path(relative_path)
            if target.exists() and not target.is_file():
                raise RuntimeError(f"Approved path is not a regular file: {relative_path!r}")
            original_contents[relative_path] = (
                target.read_text(encoding="utf-8") if target.exists() else None
            )

        written: list[str] = []
        try:
            for relative_path, content in validated:
                workspace.write_file(relative_path, content)
                written.append(relative_path)
        except Exception as exc:
            try:
                for relative_path, original in original_contents.items():
                    target = workspace._safe_path(relative_path)
                    if original is None:
                        if target.exists():
                            target.unlink()
                    else:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_text(original, encoding="utf-8")
            except Exception as rollback_exc:
                raise RuntimeError(
                    "Implementer write failed and workspace rollback also failed."
                ) from rollback_exc
            raise

        summary = str(payload.get("summary", "")).strip() or (
            f"Implemented {len(written)} approved file(s)."
        )
        return AgentResult(
            role=task.role,
            summary=summary,
            artifacts=tuple(written),
        )

    def _generate_structured(self, prompt: str) -> dict[str, Any]:
        request_body = json.dumps(
            {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": ARTIFACT_SCHEMA,
                "options": {"temperature": 0},
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            self.api_url,
            data=request_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace").strip()
            raise RuntimeError(
                f"Ollama API returned HTTP {exc.code}: {detail or 'no diagnostic output'}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Could not reach Ollama API at {self.api_url!r}: {exc.reason}"
            ) from exc
        except TimeoutError as exc:
            raise TimeoutError(
                f"Local Ollama model {self.model!r} timed out after {self.timeout_seconds}s."
            ) from exc

        try:
            envelope = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Ollama API returned invalid JSON.") from exc
        if not isinstance(envelope, dict):
            raise RuntimeError("Ollama API returned an invalid response envelope.")

        response_text = envelope.get("response")
        if isinstance(response_text, str):
            payload = self._try_parse_json(response_text)
            if isinstance(payload, dict):
                return payload

        message = envelope.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str):
                payload = self._try_parse_json(content)
                if isinstance(payload, dict):
                    return payload

        raise RuntimeError(
            "Ollama API returned no valid JSON artifact payload; "
            "no workspace files were changed."
        )

    @staticmethod
    def _build_prompt(task: AgentTask, allowed: set[str], workspace: LocalWorkspaceProvider) -> str:
        relevant_keys = {
            "approved_proposal",
            "architecture_summary",
            "approval_feedback",
            "proposal",
            "architecture",
            "feedback",
            "revision_instruction",
        }
        context = "\n".join(
            f"- {key}: {task.context[key]}"
            for key in sorted(relevant_keys)
            if key in task.context
        )
        source_files: list[str] = []
        for relative_path in sorted(allowed):
            try:
                content = workspace.read_file(relative_path)
            except FileNotFoundError:
                content = "<file does not exist yet>"
            source_files.append(
                f"FILE {relative_path}\nBEGIN CURRENT CONTENT\n{content}\nEND CURRENT CONTENT"
            )
        source = "\n\n".join(source_files)
        scope = ", ".join(sorted(allowed))
        return (
            "You are the DevRoom production Implementer.\n"
            "Execute ONLY the approved implementation for the stated GOAL.\n"
            "Ignore unrelated recommendations, examples, prior conversations, and project ideas.\n"
            "Do not redesign the task. Do not invent additional files. Do not self-approve.\n\n"
            f"GOAL: {task.goal}\n"
            f"APPROVED FILE SCOPE: {scope}\n"
            f"APPROVED IMPLEMENTATION CONTEXT:\n{context or '- none'}\n\n"
            "CURRENT CONTENT OF APPROVED FILES:\n"
            f"{source}\n\n"
            "Return only the approved implementation artifact. The response is enforced "
            "against a JSON schema. Return complete replacement content for every file "
            "you modify. Every path must be one of the approved paths."
        )

    @staticmethod
    def _try_parse_json(text: str) -> Any:
        normalized = LocalOllamaWorkspaceAgent._escape_raw_control_chars(text.strip())
        if not normalized:
            return None
        try:
            return json.loads(normalized)
        except json.JSONDecodeError:
            return LocalOllamaWorkspaceAgent._extract_json_object(normalized)

    @staticmethod
    def _escape_raw_control_chars(text: str) -> str:
        out: list[str] = []
        in_string = False
        escaped = False
        for char in text:
            if in_string:
                if escaped:
                    out.append(char)
                    escaped = False
                elif char == "\\":
                    out.append(char)
                    escaped = True
                elif char == '"':
                    out.append(char)
                    in_string = False
                elif char == "\n":
                    out.append("\\n")
                elif char == "\r":
                    out.append("\\r")
                elif char == "\t":
                    out.append("\\t")
                elif ord(char) < 0x20:
                    out.append(f"\\u{ord(char):04x}")
                else:
                    out.append(char)
            else:
                out.append(char)
                if char == '"':
                    in_string = True
        return "".join(out)

    @staticmethod
    def _extract_json_object(text: str) -> dict[str, Any] | None:
        decoder = json.JSONDecoder()
        for start, char in enumerate(text):
            if char != "{":
                continue
            try:
                candidate, _end = decoder.raw_decode(text[start:])
            except json.JSONDecodeError:
                continue
            if isinstance(candidate, dict) and isinstance(candidate.get("files"), list):
                return candidate
        return None


__all__ = ["ARTIFACT_SCHEMA", "LocalOllamaWorkspaceAgent"]
