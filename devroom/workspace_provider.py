from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class CommandResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


class LocalWorkspaceProvider:
    """Small, provider-neutral bridge for controlled local workspace operations."""

    def __init__(self, workspace: str | Path) -> None:
        root = Path(workspace).expanduser().resolve()
        if not root.exists():
            raise FileNotFoundError(f"Workspace does not exist: {root}")
        if not root.is_dir():
            raise NotADirectoryError(f"Workspace is not a directory: {root}")
        self.workspace = root

    def inspect(self) -> dict[str, object]:
        return {
            "workspace": str(self.workspace),
            "exists": self.workspace.exists(),
            "files": tuple(
                path.relative_to(self.workspace).as_posix()
                for path in sorted(self.workspace.rglob("*"))
                if path.is_file()
                and ".git" not in path.parts
                and "__pycache__" not in path.parts
            ),
            "git": self._git_status(),
        }

    def read_file(self, relative_path: str) -> str:
        return self._safe_path(relative_path).read_text(encoding="utf-8")

    def write_file(self, relative_path: str, content: str) -> Path:
        path = self._safe_path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def run_command(
        self,
        command: Sequence[str],
        *,
        approved_executables: Sequence[str],
        timeout_seconds: int = 120,
    ) -> CommandResult:
        if not command:
            raise ValueError("command must not be empty")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")
        executable = Path(command[0]).name
        if executable not in set(approved_executables):
            raise PermissionError(
                f"Command executable {executable!r} is not approved."
            )
        try:
            completed = subprocess.run(
                list(command),
                cwd=self.workspace,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(
                f"Command timed out after {timeout_seconds}s: {tuple(command)!r}"
            ) from exc
        return CommandResult(
            command=tuple(command),
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

    def require_implementation_branch(self) -> str:
        """Require a Git worktree on a named, non-protected branch."""
        branch_result = self.run_command(
            ("git", "branch", "--show-current"),
            approved_executables=("git",),
        )
        if branch_result.returncode != 0:
            raise RuntimeError(
                branch_result.stderr.strip() or "Unable to determine Git branch."
            )
        branch = branch_result.stdout.strip()
        if not branch:
            raise PermissionError(
                "Implementer requires a named Git branch; detached HEAD is not allowed."
            )
        if branch in {"main", "master"}:
            raise PermissionError(
                f"Implementer cannot write to protected branch {branch!r}."
            )
        return branch

    def require_implementation_branch(self) -> str:
        """Require a dedicated Implementer task branch in a Git workspace."""
        repository = self.run_command(
            ("git", "rev-parse", "--is-inside-work-tree"),
            approved_executables=("git",),
        )
        if repository.returncode != 0 or repository.stdout.strip().lower() != "true":
            raise RuntimeError("Implementer workspace must be a Git repository.")

        branch = self.run_command(
            ("git", "symbolic-ref", "--quiet", "--short", "HEAD"),
            approved_executables=("git",),
        )
        if branch.returncode != 0 or not branch.stdout.strip():
            raise PermissionError("Implementer workspace must be on a named Git branch.")

        name = branch.stdout.strip()
        if name in {"main", "master"}:
            raise PermissionError(f"Implementer cannot modify protected branch {name!r}.")
        if not name.startswith("agent/implementer/"):
            raise PermissionError(
                "Implementer workspace must use an agent/implementer/<task-id> branch."
            )
        return name

    def git_diff(self) -> str:
        result = self.run_command(
            ("git", "diff", "--no-ext-diff", "--"),
            approved_executables=("git",),
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "git diff failed")
        return result.stdout

    def _git_status(self) -> tuple[str, ...]:
        result = self.run_command(
            ("git", "status", "--porcelain", "--untracked-files=all"),
            approved_executables=("git",),
        )
        if result.returncode != 0:
            return ()
        return tuple(line for line in result.stdout.splitlines() if line.strip())

    def _safe_path(self, relative_path: str) -> Path:
        candidate = Path(relative_path)
        if candidate.is_absolute():
            raise ValueError("Workspace paths must be relative.")
        resolved = (self.workspace / candidate).resolve()
        try:
            resolved.relative_to(self.workspace)
        except ValueError as exc:
            raise ValueError("Path escapes the workspace.") from exc
        if ".git" in resolved.relative_to(self.workspace).parts:
            raise PermissionError("Access to .git is not allowed through this provider.")
        return resolved


__all__ = ["CommandResult", "LocalWorkspaceProvider"]
