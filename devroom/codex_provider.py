from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass

from .orchestrator import AgentProvider, AgentResult, AgentTask


@dataclass(frozen=True)
class CodexCliConfig:
    command: str = "codex"
    sandbox: str = "workspace-write"
    ephemeral: bool = True
    timeout_seconds: int = 3600


class CodexCliProvider:
    """Run a DevRoom role through the installed Codex CLI.

    DevRoom owns role/context routing while Codex owns model execution, tool use,
    and its sandbox. The target workspace is passed explicitly to Codex.
    """

    def __init__(self, config: CodexCliConfig | None = None) -> None:
        self.config = config or CodexCliConfig()

    def execute(self, task: AgentTask) -> AgentResult:
        if shutil.which(self.config.command) is None:
            raise RuntimeError(
                f"Codex CLI not found: {self.config.command!r}. "
                "Install/login to Codex before enabling this provider."
            )

        workspace = task.context.get("workspace")
        if not workspace:
            raise ValueError(
                "Codex tasks require an explicit 'workspace' context value."
            )

        command = self._build_command(task, str(workspace))
        completed = subprocess.run(
            command,
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=self.config.timeout_seconds,
            check=False,
        )

        if completed.returncode != 0:
            raise RuntimeError(
                f"Codex execution failed with exit code {completed.returncode}: "
                f"{completed.stderr.strip()}"
            )

        summary = self._extract_final_message(completed.stdout)
        if not summary:
            raise RuntimeError("Codex completed without a final agent message.")

        return AgentResult(role=task.role, summary=summary)

    def _build_command(self, task: AgentTask, workspace: str) -> list[str]:
        command = [
            self.config.command,
            "exec",
            "--json",
            "--cd",
            workspace,
            "--sandbox",
            self.config.sandbox,
        ]
        if self.config.ephemeral:
            command.append("--ephemeral")
        command.append(self._build_prompt(task))
        return command

    @staticmethod
    def _build_prompt(task: AgentTask) -> str:
        instructions = task.context.get("role_instructions", "")
        context_lines = [
            f"{key}: {value}"
            for key, value in task.context.items()
            if key != "role_instructions"
        ]
        context = "\n".join(context_lines)

        return (
            f"You are the DevRoom {task.role} agent.\n"
            f"Role instructions:\n{instructions}\n\n"
            f"Task:\n{task.goal}\n\n"
            f"Relevant context:\n{context or '(none)'}\n\n"
            "Follow repository instructions and report what you actually did. "
            "Do not claim tests or changes you did not perform."
        )

    @staticmethod
    def _extract_final_message(jsonl: str) -> str:
        final_messages: list[str] = []

        for line in jsonl.splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if event.get("type") != "item.completed":
                continue

            item = event.get("item") or {}
            if item.get("type") == "agent_message" and item.get("text"):
                final_messages.append(str(item["text"]))

        return final_messages[-1].strip() if final_messages else ""


__all__ = ["CodexCliConfig", "CodexCliProvider"]
