from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Iterable, Mapping

from .local_ollama_provider import LocalOllamaConfig, LocalOllamaProvider
from .orchestrator import AgentTask

DEFAULT_MODEL_SUITE: tuple[str, ...] = (
    "qwen3.5:4b",
    "qwen3.5:3b",
    "qwen3.5:1.5b",
    "gemma4:e4b",
)

UNITY_CSHARP_BENCHMARKS: tuple[Mapping[str, str], ...] = (
    {
        "id": "architecture",
        "role": "Architect-Benchmark",
        "goal": "Design a Unity C# player inventory service with item definitions, owned item state, validation, and persistence boundaries. Give interfaces and responsibilities, not a giant implementation.",
    },
    {
        "id": "implementation",
        "role": "Implementer-Benchmark",
        "goal": "Implement a small Unity C# InventoryService that validates item IDs, prevents negative quantities, exposes AddItem and RemoveItem, and is easy to unit test. Include focused code only.",
    },
    {
        "id": "debugging",
        "role": "Debugger-Benchmark",
        "goal": "Diagnose this Unity C# bug: a list is modified inside a foreach loop while removing expired entries. Explain the failure and provide a safe corrected implementation.",
    },
    {
        "id": "testing",
        "role": "QA-Benchmark",
        "goal": "Write focused C# unit tests for an inventory service covering add, remove, insufficient quantity, invalid item ID, and zero/negative quantity cases.",
    },
    {
        "id": "review",
        "role": "Reviewer-Benchmark",
        "goal": "Review a hypothetical Unity inventory implementation for null handling, state integrity, testability, separation of static item definitions from player-owned state, and unnecessary coupling. Return a concise review checklist.",
    },
)


def benchmark_models(
    models: Iterable[str],
    *,
    command: str = "ollama",
    timeout_seconds: int = 600,
    benchmarks: Iterable[Mapping[str, str]] = UNITY_CSHARP_BENCHMARKS,
) -> list[dict[str, object]]:
    """Run the same Unity/C# benchmark suite against each local model."""
    results: list[dict[str, object]] = []
    for model in models:
        model_result: dict[str, object] = {"model": model, "tasks": []}
        for benchmark in benchmarks:
            task = AgentTask(
                role=benchmark["role"],
                goal=benchmark["goal"],
                context={
                    "benchmark": "unity-csharp-v1",
                    "evaluation": "correctness, architecture, instruction following, clarity, testability",
                },
            )
            provider = LocalOllamaProvider(
                LocalOllamaConfig(
                    command=command,
                    model=model,
                    timeout_seconds=timeout_seconds,
                )
            )
            started = time.perf_counter()
            try:
                result = provider.execute(task)
                task_result = {
                    "id": benchmark["id"],
                    "status": "ok",
                    "elapsed_seconds": round(time.perf_counter() - started, 3),
                    "output": result.summary,
                }
            except Exception as exc:
                task_result = {
                    "id": benchmark["id"],
                    "status": "error",
                    "elapsed_seconds": round(time.perf_counter() - started, 3),
                    "error": str(exc),
                }
            model_result["tasks"].append(task_result)
        results.append(model_result)
    return results


def write_benchmark_report(results: list[dict[str, object]], path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return target


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark local Unity/C# Ollama models.")
    parser.add_argument("--models", nargs="+", default=list(DEFAULT_MODEL_SUITE))
    parser.add_argument("--command", default="ollama")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--output", default="local-model-benchmark.json")
    args = parser.parse_args()

    results = benchmark_models(
        args.models,
        command=args.command,
        timeout_seconds=args.timeout,
    )
    write_benchmark_report(results, args.output)
    for model_result in results:
        tasks = model_result["tasks"]
        ok = sum(task["status"] == "ok" for task in tasks)
        total_time = sum(task["elapsed_seconds"] for task in tasks)
        print(f"{model_result['model']}: {ok}/{len(tasks)} tasks completed ({total_time:.3f}s)")
    print(f"Report written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DEFAULT_MODEL_SUITE",
    "UNITY_CSHARP_BENCHMARKS",
    "benchmark_models",
    "write_benchmark_report",
    "main",
]
