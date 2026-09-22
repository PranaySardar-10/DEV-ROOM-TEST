from __future__ import annotations

import subprocess
from dataclasses import dataclass

from .orchestrator import AgentProvider, AgentResult, AgentTask


@dataclass(frozen=True)
class LocalQwenConfig:
    command: str = "ollama"
    model: str = "qwen2.5-coder:3b"
    timeout_seconds: int = 600


class LocalQwenProvider(AgentProvider):
    """Runs a configured Qwen model through a local Ollama CLI process."""

    def __init__(self, config: LocalQwenConfig | None = None) -> None:
        self.config = config or LocalQwenConfig()
        if not self.config.model.strip():
            raise ValueError("Qwen model must not be blank.")
        if self.config.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0.")

    def execute(self, task: AgentTask) -> AgentResult:
        prompt = self._build_prompt(task)
        command = (self.config.command, "run", self.config.model, prompt)
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.config.timeout_seconds,
                check=False,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                f"Local Qwen command was not found: {self.config.command!r}"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(
                f"Local Qwen provider timed out after "
                f"{self.config.timeout_seconds}s."
            ) from exc

        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise RuntimeError(
                f"Local Qwen provider failed with exit code "
                f"{completed.returncode}: {detail or 'no diagnostic output'}"
            )

        summary = completed.stdout.strip()
        if not summary:
            raise RuntimeError("Local Qwen provider returned empty output.")

        return AgentResult(role=task.role, summary=summary)

    @staticmethod
    def _build_prompt(task: AgentTask) -> str:
        context = "\n".join(
            f"- {key}: {value}" for key, value in sorted(task.context.items())
        )
        return (
            "You are a local DevRoom agent. Follow the assigned role and do not "
            "claim actions you did not perform.\n\n"
            f"ROLE: {task.role}\n"
            f"GOAL: {task.goal}\n"
            "CONTEXT:\n"
            f"{context or '- none'}\n\n"
            "Return a concise, evidence-based result suitable for the next "
            "workflow stage."
        )


__all__ = ["LocalQwenConfig", "LocalQwenProvider"]
