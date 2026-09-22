from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Iterable

from .local_ollama_provider import LocalOllamaConfig, LocalOllamaProvider
from .orchestrator import AgentTask


def benchmark_models(
    models: Iterable[str],
    *,
    command: str = "ollama",
    timeout_seconds: int = 600,
    goal: str = (
        "Implement and explain a small Unity C# service with clear validation, "
        "error handling, and unit-testable design. Review the task for correctness "
        "before returning the proposed implementation."
    ),
) -> list[dict[str, object]]:
    """Run the same coding task against each local model for comparison."""
    results: list[dict[str, object]] = []
    task = AgentTask(
        role="Implementer-Benchmark",
        goal=goal,
        context={
            "benchmark": "local-model-coding-v1",
            "evaluation": "correctness, architecture, instruction following, clarity",
        },
    )
    for model in models:
        provider = LocalOllamaProvider(
            LocalOllamaConfig(command=command, model=model, timeout_seconds=timeout_seconds)
        )
        started = time.perf_counter()
        try:
            result = provider.execute(task)
            results.append({
                "model": model, "status": "ok",
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "output": result.summary,
            })
        except Exception as exc:
            results.append({
                "model": model, "status": "error",
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "error": str(exc),
            })
    return results


def write_benchmark_report(results: list[dict[str, object]], path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return target


__all__ = ["benchmark_models", "write_benchmark_report"]
