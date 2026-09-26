import sys
import unittest

from devroom.process_runner import run_with_stall_timeout


class ProcessRunnerTests(unittest.TestCase):
    def test_long_running_process_is_allowed_when_output_continues(self) -> None:
        script = (
            "import sys,time; "
            "[(print('progress', flush=True), time.sleep(0.15)) for _ in range(5)]"
        )
        result = run_with_stall_timeout(
            (sys.executable, "-c", script),
            stall_timeout_seconds=0.4,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("progress", result.stdout)

    def test_process_is_terminated_after_observable_stall(self) -> None:
        script = "import time; print('started', flush=True); time.sleep(2)"
        with self.assertRaisesRegex(TimeoutError, "stalled"):
            run_with_stall_timeout(
                (sys.executable, "-c", script),
                stall_timeout_seconds=0.2,
            )

    def test_large_stdin_payload_is_supported(self) -> None:
        script = (
            "import sys; "
            "data = sys.stdin.buffer.read(); "
            "print(len(data), flush=True)"
        )
        payload = b"x" * 300_000
        result = run_with_stall_timeout(
            (sys.executable, "-c", script),
            input_data=payload,
            stall_timeout_seconds=1,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), str(len(payload)))


if __name__ == "__main__":
    unittest.main()
