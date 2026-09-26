from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .process_runner import ProcessRunResult, run_with_stall_timeout


@dataclass(frozen=True)
class UnityCliResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    log_file: str | None
    log_excerpt: str = ""

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0

    def summary(self) -> str:
        status = "passed" if self.succeeded else "failed"
        lines = [
            f"Unity CLI validation {status}.",
            f"RETURN CODE: {self.returncode}",
        ]
        if self.log_file:
            lines.append(f"LOG FILE: {self.log_file}")
        if self.log_excerpt.strip():
            lines.append("UNITY LOG EXCERPT:\n" + self.log_excerpt)
        if self.stderr.strip():
            lines.append("STDERR:\n" + self.stderr.strip())
        if self.stdout.strip():
            lines.append("STDOUT:\n" + self.stdout.strip())
        return "\n".join(lines)


@dataclass(frozen=True)
class UnityCliRunner:
    executable: str
    method: str
    stall_timeout_seconds: float = 1800.0
    log_file: str | None = None
    accept_api_update: bool = True
    nographics: bool = False
    extra_args: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.executable.strip():
            raise ValueError("Unity executable must not be blank.")
        if not self.method.strip():
            raise ValueError("Unity executeMethod must not be blank.")
        if self.stall_timeout_seconds <= 0:
            raise ValueError("Unity CLI stall_timeout_seconds must be > 0.")

    def build_command(self, workspace: str) -> tuple[str, ...]:
        project_path = str(Path(workspace).expanduser().resolve())
        command: list[str] = [self.executable]
        if self.accept_api_update:
            command.append("-accept-apiupdate")
        command.extend(("-batchmode", "-quit", "-projectPath", project_path))
        if self.nographics:
            command.append("-nographics")
        command.extend(("-executeMethod", self.method))
        if self.log_file:
            log_path = str(Path(self.log_file).expanduser().resolve())
            Path(log_path).parent.mkdir(parents=True, exist_ok=True)
            command.extend(("-logFile", log_path))
        command.extend(self.extra_args)
        return tuple(command)

    def run(self, workspace: str) -> UnityCliResult:
        project_path = Path(workspace).expanduser().resolve()
        if not project_path.is_dir():
            raise FileNotFoundError(
                f"Unity project workspace does not exist: {project_path}"
            )
        executable = Path(self.executable).expanduser()
        if not executable.is_file():
            raise FileNotFoundError(
                f"Unity executable does not exist: {executable}"
            )

        command = self.build_command(str(project_path))
        try:
            completed: ProcessRunResult = run_with_stall_timeout(
                command,
                stall_timeout_seconds=self.stall_timeout_seconds,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                f"Unity CLI executable could not be started: {self.executable!r}"
            ) from exc
        except TimeoutError as exc:
            raise TimeoutError(
                f"Unity CLI method {self.method!r} stalled after "
                f"{self.stall_timeout_seconds:g}s without observable output."
            ) from exc

        log_excerpt = ""
        if self.log_file:
            log_path = Path(self.log_file).expanduser().resolve()
            if log_path.is_file():
                try:
                    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
                    interesting = [
                        line for line in lines
                        if "[OMNIVERSEL" in line
                        or "error CS" in line
                        or "Exception" in line
                        or "Command failed" in line
                    ]
                    selected = (interesting if interesting else lines[-80:])[-120:]
                    log_excerpt = "\n".join(selected)
                except OSError:
                    log_excerpt = "<UNITY LOG COULD NOT BE READ>"
        return UnityCliResult(
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            log_file=self.log_file,
            log_excerpt=log_excerpt,
        )


__all__ = ["UnityCliResult", "UnityCliRunner"]
