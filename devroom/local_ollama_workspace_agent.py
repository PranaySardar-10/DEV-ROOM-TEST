from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from .orchestrator import AgentResult, AgentTask
from .sandbox_policy import WORKSPACE_WRITE
from .workspace_provider import LocalWorkspaceProvider
from .unity_scene_integrator import integrate_character_test


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
    stall_timeout_seconds: int = 1800
    timeout_seconds: int = 600
    api_url: str = "http://localhost:11434/api/generate"
    num_predict: int = 16384

    def __post_init__(self) -> None:
        if self.stall_timeout_seconds <= 0:
            raise ValueError("stall_timeout_seconds must be > 0.")
        if self.num_predict <= 0:
            raise ValueError("num_predict must be > 0.")

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
        allowed = {
            self._normalize_path(item)
            for item in allowed_raw.split(",")
            if item.strip()
        }
        if not allowed:
            raise ValueError("Implementer requires an explicit allowed_paths scope.")

        # The direct ChatGPT experiment already provides the approved implementation
        # as the source artifact. In that path, the Implementer is an executor, not
        # another code-generating model. Parse the approved plan deterministically so
        # a small local model cannot truncate or corrupt the implementation artifact.
        approved_plan = task.context.get("approved_proposal")
        if (
            task.context.get("plan_source")
            == "ChatGPT direct architecture + coding experiment"
            and isinstance(approved_plan, str)
        ):
            payload = self._payload_from_approved_plan(approved_plan)
        else:
            prompt = self._build_prompt(task, allowed, workspace)
            payload = self._generate_structured(prompt)
        files = payload.get("files")
        if not isinstance(files, list) or not files:
            raise RuntimeError("Implementer response contained no file changes.")

        direct_scene_required = (
            task.context.get("plan_source")
            == "ChatGPT direct architecture + coding experiment"
            and isinstance(approved_plan, str)
            and "SCENE FILE IS A REQUIRED IMPLEMENTATION ARTIFACT" in approved_plan
        )

        validated: list[tuple[str, str]] = []
        seen: set[str] = set()
        for item in files:
            if not isinstance(item, dict):
                raise RuntimeError("Every file change must be an object.")
            relative_path = self._normalize_path(str(item.get("path", "")))
            content = item.get("content")
            if not self._path_is_allowed(relative_path, allowed):
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
        generated_paths: list[str] = []
        if direct_scene_required:
            scene_path = "Assets/Scenes/CharacterTest.unity"
            if not self._path_is_allowed(scene_path, allowed):
                raise PermissionError(
                    "Direct CharacterTest integration requires Assets/Scenes/CharacterTest.unity "
                    "to be inside the Implementer allowed_paths scope."
                )
            generated_paths = [
                scene_path,
                "Assets/Omniversel/Gameplay/Character/OmniverselCharacterInput.cs.meta",
                "Assets/Omniversel/Gameplay/Character/OmniverselCharacterController.cs.meta",
                "Assets/Omniversel/Gameplay/Character/OmniverselThirdPersonCamera.cs.meta",
            ]
            for path in generated_paths:
                if path not in original_contents:
                    target = workspace._safe_path(path)
                    original_contents[path] = (
                        target.read_text(encoding="utf-8") if target.exists() else None
                    )

        try:
            for relative_path, content in validated:
                workspace.write_file(relative_path, content)
                written.append(relative_path)

            if direct_scene_required:
                integrated = integrate_character_test(workspace)
                for path in integrated:
                    if path not in written:
                        written.append(path)
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
            f"Implemented {len(written)} approved artifact(s)."
        )
        return AgentResult(
            role=task.role,
            summary=summary,
            artifacts=tuple(written),
        )

    @classmethod
    def _payload_from_approved_plan(cls, plan: str) -> dict[str, Any]:
        """Extract file artifacts from the human-approved ChatGPT plan.

        The experimental plan format associates each fenced file-content block with
        the nearest preceding Assets/... path declaration. This keeps implementation
        deterministic: the Implementer applies the approved artifact verbatim instead
        of asking a second model to reproduce it.
        """
        lines = plan.splitlines()
        files: list[dict[str, str]] = []
        in_fence = False
        fence_lines: list[str] = []
        path_for_fence: str | None = None
        recent_path: str | None = None

        import re

        path_pattern = re.compile(r"(?:\x60)?(Assets/[A-Za-z0-9_./-]+)(?:\x60)?")
        for line in lines:
            matches = path_pattern.findall(line)
            if matches:
                recent_path = matches[-1]

            if line.startswith("\x60\x60\x60"):
                if not in_fence:
                    in_fence = True
                    fence_lines = []
                    path_for_fence = recent_path
                else:
                    if path_for_fence:
                        files.append(
                            {
                                "path": path_for_fence,
                                "content": "\n".join(fence_lines) + "\n",
                            }
                        )
                    in_fence = False
                    fence_lines = []
                    path_for_fence = None
                continue

            if in_fence:
                fence_lines.append(line)

        if in_fence:
            raise RuntimeError(
                "Approved ChatGPT plan contains an unterminated code fence."
            )
        if not files:
            raise RuntimeError(
                "Approved ChatGPT plan contained no file artifacts."
            )

        deduplicated: dict[str, dict[str, str]] = {}
        for item in files:
            path = cls._normalize_path(item["path"])
            deduplicated[path] = {"path": path, "content": item["content"]}

        return {
            "summary": f"Applied {len(deduplicated)} file artifact(s) from the approved ChatGPT plan.",
            "files": list(deduplicated.values()),
        }

    def _generate_structured(self, prompt: str) -> dict[str, Any]:
        request_body = json.dumps(
            {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": ARTIFACT_SCHEMA,
                "options": {"temperature": 0, "num_predict": self.num_predict},
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            self.api_url,
            data=request_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=max(self.stall_timeout_seconds, self.timeout_seconds),
            ) as response:
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
                f"Local Ollama model {self.model!r} timed out after "
                f"{max(self.stall_timeout_seconds, self.timeout_seconds)}s."
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
            "no workspace files were changed. "
            "The Implementer may have exhausted its output budget before completing the artifact."
        )

    @staticmethod
    def _normalize_path(path: str) -> str:
        return path.replace("\\", "/").strip().strip("/")

    @classmethod
    def _path_is_allowed(cls, path: str, allowed: set[str]) -> bool:
        normalized = cls._normalize_path(path)
        return any(
            normalized == scope or normalized.startswith(scope + "/")
            for scope in allowed
        )

    @classmethod
    def _build_prompt(
        cls,
        task: AgentTask,
        allowed: set[str],
        workspace: LocalWorkspaceProvider,
    ) -> str:
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
        existing_files: list[str] = []
        try:
            inspection = workspace.inspect()
            existing_files = [
                str(path).replace("\\", "/")
                for path in inspection["files"]
                if cls._path_is_allowed(str(path), allowed)
            ]
        except (FileNotFoundError, OSError):
            existing_files = []

        for relative_path in sorted(existing_files):
            try:
                content = workspace.read_file(relative_path)
            except FileNotFoundError:
                continue
            source_files.append(
                f"FILE {relative_path}\nBEGIN CURRENT CONTENT\n{content}\nEND CURRENT CONTENT"
            )

        source = "\n\n".join(source_files) or "<no existing files in approved scope>"
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
            "you modify. Every path must be inside one of the approved scope directories "
            "or equal an explicitly approved file path. "
            "Do not return markdown fences or explanatory text outside the JSON artifact."
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
