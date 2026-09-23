from __future__ import annotations

import subprocess
import threading
import time
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ProcessRunResult:
    stdout: str
    stderr: str
    returncode: int


def run_with_stall_timeout(
    command: Sequence[str],
    *,
    stall_timeout_seconds: float,
) -> ProcessRunResult:
    """Run a process until it exits; abort only after observable output stalls."""
    if stall_timeout_seconds <= 0:
        raise ValueError("stall_timeout_seconds must be > 0.")

    process = subprocess.Popen(
        tuple(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    lock = threading.Lock()
    last_activity = time.monotonic()

    def drain(stream, target: list[str]) -> None:
        nonlocal last_activity
        if stream is None:
            return
        try:
            for chunk in iter(stream.readline, ""):
                target.append(chunk)
                with lock:
                    last_activity = time.monotonic()
        finally:
            stream.close()

    stdout_thread = threading.Thread(
        target=drain, args=(process.stdout, stdout_chunks), daemon=True
    )
    stderr_thread = threading.Thread(
        target=drain, args=(process.stderr, stderr_chunks), daemon=True
    )
    stdout_thread.start()
    stderr_thread.start()

    stalled = False
    try:
        while process.poll() is None:
            with lock:
                idle_seconds = time.monotonic() - last_activity
            if idle_seconds >= stall_timeout_seconds:
                stalled = True
                process.kill()
                break
            time.sleep(min(0.25, max(0.01, stall_timeout_seconds - idle_seconds)))
        returncode = process.wait()
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        stdout_thread.join(timeout=2)
        stderr_thread.join(timeout=2)

    result = ProcessRunResult(
        stdout="".join(stdout_chunks),
        stderr="".join(stderr_chunks),
        returncode=int(returncode),
    )
    if stalled:
        raise TimeoutError(
            f"Process stalled for {stall_timeout_seconds:g}s without observable output."
        )
    return result


__all__ = ["ProcessRunResult", "run_with_stall_timeout"]
