import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from devroom.local_model_benchmark import (
    DEFAULT_MODEL_SUITE,
    UNITY_CSHARP_BENCHMARKS,
    benchmark_models,
    write_benchmark_report,
)


class LocalModelBenchmarkTests(unittest.TestCase):
    @patch("devroom.local_model_benchmark.LocalOllamaProvider")
    def test_default_suite_covers_unity_csharp_work(self) -> None:
        self.assertEqual(
            DEFAULT_MODEL_SUITE,
            ("qwen3.5:4b", "qwen3.5:3b", "qwen3.5:1.5b", "gemma4:e4b"),
        )
        self.assertEqual(
            [item["id"] for item in UNITY_CSHARP_BENCHMARKS],
            ["architecture", "implementation", "debugging", "testing", "review"],
        )

    @patch("devroom.local_model_benchmark.LocalOllamaProvider")
    def test_benchmark_runs_every_suite_task_for_each_model(self, provider_cls) -> None:
        provider_cls.return_value.execute.return_value.summary = "result"
        results = benchmark_models(["qwen3.5:4b", "gemma4:e4b"])
        self.assertEqual([item["model"] for item in results], ["qwen3.5:4b", "gemma4:e4b"])
        self.assertTrue(all(len(item["tasks"]) == 5 for item in results))
        self.assertEqual(provider_cls.call_count, 10)

    @patch("devroom.local_model_benchmark.LocalOllamaProvider")
    def test_benchmark_records_provider_errors(self, provider_cls) -> None:
        provider_cls.return_value.execute.side_effect = RuntimeError("model unavailable")
        results = benchmark_models(["qwen3.5:1.5b"])
        self.assertEqual(results[0]["tasks"][0]["status"], "error")
        self.assertIn("model unavailable", results[0]["tasks"][0]["error"])

    def test_write_benchmark_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = write_benchmark_report(
                [{"model": "qwen3.5:4b", "status": "ok"}],
                Path(directory) / "report.json",
            )
            self.assertIn('"model": "qwen3.5:4b"', path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
