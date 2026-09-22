from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Any

from .orchestrator import AgentResult, AgentTask
from .sandbox_policy import WORKSPACE_WRITE
from .workspace_provider import LocalWorkspaceProvider


@dataclass(frozen=True)
class LocalOllamaWorkspaceAgent:
    """Controlled local Ollama Implementer using a strict file-change protocol."""

    command: str = "ollama"
    model: str = ""
    timeout_seconds: int = 600

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
        try:
            completed = subprocess.run(
                (self.command, "run", self.model, "--format", "json", prompt),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_seconds,
                check=False,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(f"Ollama command was not found: {self.command!r}") from exc
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(
                f"Local Ollama model {self.model!r} timed out after {self.timeout_seconds}s."
            ) from exc

        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise RuntimeError(
                f"Local Ollama model {self.model!r} failed with exit code "
                f"{completed.returncode}: {detail or 'no diagnostic output'}"
            )

        payload = self._parse_payload(completed.stdout)
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

        # Validate the complete response before writing anything. This prevents
        # a malformed second file entry from leaving the workspace partially changed.
        for relative_path, content in validated:
            workspace._safe_path(relative_path)
        written: list[str] = []
        for relative_path, content in validated:
            workspace.write_file(relative_path, content)
            written.append(relative_path)

        summary = str(payload.get("summary", "")).strip() or (
            f"Implemented {len(written)} approved file(s)."
        )
        return AgentResult(
            role=task.role,
            summary=summary,
            artifacts=tuple(written),
        )

    @staticmethod
    def _build_prompt(task: AgentTask, allowed: set[str], workspace: LocalWorkspaceProvider) -> str:
        relevant_keys = {"proposal", "architecture", "feedback", "revision_instruction"}
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
                f"### {relative_path}\n```text\n{content}\n```"
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
            "Your response MUST be one JSON object and nothing else. "
            "Do not output reasoning, markdown, headings, commentary, or code fences. "
            "Use exactly this schema: "
            '{"summary":"short evidence-based summary","files":[{"path":"relative/path","content":"complete file content"}]}. '
            "Return complete replacement content for every file you modify. "
            "Every path must be one of the approved paths."
        )

    @staticmethod
    def _parse_payload(output: str) -> dict[str, Any]:
        text = output.strip()
        if not text:
            raise RuntimeError(
                "Implementer returned empty output; no workspace files were changed."
            )

        # Ollama CLI JSON mode may return a response envelope whose assistant
        # content is itself the JSON artifact payload. Accept both the direct
        # payload and the envelope without weakening the artifact validation.
        candidates = [text]
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                envelope = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(envelope, dict):
                response = envelope.get("response")
                if isinstance(response, str):
                    candidates.append(response)
                message = envelope.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str):
                        candidates.append(content)

        for candidate_text in candidates:
            payload = LocalOllamaWorkspaceAgent._try_parse_json(candidate_text)
            if isinstance(payload, dict) and isinstance(payload.get("files"), list):
                return payload

        raise RuntimeError(
            "Implementer returned no valid JSON artifact payload; "
            "no workspace files were changed."
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
        # Recover JSON objects containing literal newlines/tabs inside string
        # values, which some local models emit despite JSON mode.
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
                    out.append("\\\\n")
                elif char == "\r":
                    out.append("\\\\r")
                elif char == "\t":
                    out.append("\\\\t")
                elif ord(char) < 0x20:
                    out.append(f"\\\\u{ord(char):04x}")
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

__all__ = ["LocalOllamaWorkspaceAgent"]
