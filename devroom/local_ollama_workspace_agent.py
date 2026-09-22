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

        prompt = self._build_prompt(task, allowed)
        try:
            completed = subprocess.run(
                (self.command, "run", self.model, prompt),
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

        written: list[str] = []
        for item in files:
            if not isinstance(item, dict):
                raise RuntimeError("Every file change must be an object.")
            relative_path = str(item.get("path", "")).replace("\\", "/")
            content = item.get("content")
            if relative_path not in allowed:
                raise PermissionError(
                    f"Implementer attempted to modify a path outside its approved scope: {relative_path!r}"
                )
            if not isinstance(content, str):
                raise RuntimeError(f"File content must be a string: {relative_path!r}")
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
    def _build_prompt(task: AgentTask, allowed: set[str]) -> str:
        context = "\n".join(
            f"- {key}: {value}" for key, value in sorted(task.context.items())
            if key not in {"sandbox"}
        )
        scope = ", ".join(sorted(allowed))
        return (
            "You are the DevRoom production Implementer. Integrate ONLY the approved "
            "implementation into the assigned workspace. Do not self-approve.\n\n"
            f"ROLE: {task.role}\nGOAL: {task.goal}\n"
            f"APPROVED FILE SCOPE: {scope}\nCONTEXT:\n{context}\n\n"
            "Return ONLY valid JSON with this exact shape: "
            '{"summary":"short evidence-based summary","files":[{"path":"relative/path","content":"complete file content"}]}. '
            "Every path must be one of the approved paths. Do not use markdown fences."
        )

    @staticmethod
    def _parse_payload(output: str) -> dict[str, Any]:
        text = output.strip()
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Implementer returned non-JSON output; no workspace files were changed."
            ) from exc
        if not isinstance(payload, dict):
            raise RuntimeError("Implementer JSON response must be an object.")
        return payload


__all__ = ["LocalOllamaWorkspaceAgent"]
