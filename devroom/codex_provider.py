from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass

from .orchestrator import AgentProvider, AgentResult, AgentTask
from .sandbox_policy import READ_ONLY, WORKSPACE_WRITE, RoleSandboxPolicy


@dataclass(frozen=True)
class CodexCliConfig:
    command: str = "codex"
    # Legacy override may only tighten a role's effective privilege.
    sandbox: str | None = None
    ephemeral: bool = True
    timeout_seconds: int = 3600


class CodexCliProvider:
    """Run a DevRoom role through the installed Codex CLI."""

    def __init__(
        self,
        config: CodexCliConfig | None = None,
        *,
        sandbox_policy: RoleSandboxPolicy | None = None,
    ) -> None:
        self.config = config or CodexCliConfig()
        self.sandbox_policy = sandbox_policy or RoleSandboxPolicy()

    def execute(self, task: AgentTask) -> AgentResult:
        workspace = task.context.get("workspace")
        if not workspace:
            raise ValueError("Codex tasks require an explicit 'workspace' context value.")
        if shutil.which(self.config.command) is None:
            raise RuntimeError(f"Codex CLI not found: {self.config.command!r}.")

        sandbox = self._effective_sandbox(task)
        before = self._workspace_fingerprint(str(workspace)) if task.role == "Implementer" else None
        print(f"[DevRoom] {task.role} → Codex started", flush=True)
        try:
            completed = subprocess.run(
                self._build_command(task, str(workspace), sandbox),
                cwd=str(workspace),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.config.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"Codex execution timed out after {self.config.timeout_seconds}s for role {task.role!r}."
            ) from exc
        print(f"[DevRoom] {task.role} → Codex finished (exit {completed.returncode})", flush=True)

        if completed.returncode != 0:
            raise RuntimeError(
                f"Codex execution failed with exit code {completed.returncode}: {completed.stderr.strip()}"
            )

        summary = self._extract_final_message(completed.stdout)
        if not summary:
            raise RuntimeError("Codex completed without a final agent message.")
        artifacts = self._implementation_artifacts(str(workspace), before) if task.role == "Implementer" else ()
        return AgentResult(role=task.role, summary=summary, artifacts=artifacts)

    @staticmethod
    def _workspace_fingerprint(workspace: str) -> tuple[str, tuple[str, ...]]:
        try:
            head = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=workspace,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            ).stdout.strip()
            status = subprocess.run(
                ["git", "status", "--porcelain", "--untracked-files=all"],
                cwd=workspace,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            ).stdout.splitlines()
        except (OSError, subprocess.CalledProcessError):
            return ("", ())
        return (head, tuple(line for line in status if not _ignored_runtime_path(line)))

    @staticmethod
    def _implementation_artifacts(
        workspace: str,
        before: tuple[str, tuple[str, ...]] | None,
    ) -> tuple[str, ...]:
        after = CodexCliProvider._workspace_fingerprint(workspace)
        if before is None or after == before:
            return ()
        before_head, before_status = before
        after_head, after_status = after
        changed = sorted(set(before_status) | set(after_status))
        if before_head != after_head:
            changed.append(f"git:{after_head}")
        return tuple(dict.fromkeys(changed))

def _ignored_runtime_path(status_line: str) -> bool:
    path = status_line[3:].strip()
    return path.startswith(".devroom/") or "__pycache__/" in path or path.endswith(".pyc")

    def _effective_sandbox(self, task: AgentTask) -> str:
        maximum = self.sandbox_policy.sandbox_for(task.role)
        requested = task.context.get("sandbox", maximum)
        if requested not in {READ_ONLY, WORKSPACE_WRITE}:
            raise ValueError(f"Unsupported sandbox policy: {requested}")

        if self.config.sandbox is not None:
            if self.config.sandbox not in {READ_ONLY, WORKSPACE_WRITE}:
                raise ValueError(f"Unsupported legacy sandbox policy: {self.config.sandbox}")
            if maximum == READ_ONLY and self.config.sandbox == WORKSPACE_WRITE:
                raise PermissionError(f"Legacy sandbox override cannot elevate role {task.role!r}.")
            requested = self._stricter_sandbox(requested, self.config.sandbox)

        if maximum == READ_ONLY and requested == WORKSPACE_WRITE:
            raise PermissionError(f"Role {task.role!r} cannot execute with workspace-write.")
        return requested

    @staticmethod
    def _stricter_sandbox(left: str, right: str) -> str:
        return READ_ONLY if READ_ONLY in {left, right} else WORKSPACE_WRITE

    def _build_command(self, task: AgentTask, workspace: str, sandbox: str | None = None) -> list[str]:
        effective = sandbox or self._effective_sandbox(task)
        return [
            self.config.command,
            "exec",
            "--json",
            "--cd",
            workspace,
            "--sandbox",
            effective,
            *(["--ephemeral"] if self.config.ephemeral else []),
            self._build_prompt(task),
        ]

    @staticmethod
    def _build_prompt(task: AgentTask) -> str:
        instructions = task.context.get("role_instructions", "")
        context_lines = [
            f"{key}: {value}" for key, value in task.context.items() if key != "role_instructions"
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
