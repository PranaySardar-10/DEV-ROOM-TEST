import tempfile
import unittest
from pathlib import Path

from devroom.workspace_provider import LocalWorkspaceProvider


class LocalWorkspaceProviderTests(unittest.TestCase):
    def test_inspect_read_write_and_git_diff(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").mkdir()
            provider = LocalWorkspaceProvider(root)

            provider.write_file("src/example.txt", "hello")
            self.assertEqual(provider.read_file("src/example.txt"), "hello")

            snapshot = provider.inspect()
            self.assertEqual(snapshot["workspace"], str(root.resolve()))
            self.assertIn("src/example.txt", snapshot["files"])
            self.assertNotIn(".git", snapshot["files"])

    def test_paths_cannot_escape_workspace_or_touch_git(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").mkdir()
            provider = LocalWorkspaceProvider(root)

            with self.assertRaises(ValueError):
                provider.read_file("../outside.txt")
            with self.assertRaises(PermissionError):
                provider.read_file(".git/config")

    def test_write_creates_parent_directories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = LocalWorkspaceProvider(directory)
            path = provider.write_file("a/b/c.txt", "content")
            self.assertTrue(path.exists())
            self.assertEqual(path.read_text(encoding="utf-8"), "content")

    def test_run_command_requires_explicit_approval(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = LocalWorkspaceProvider(directory)

            with self.assertRaises(PermissionError):
                provider.run_command(
                    ("python", "-c", "print('x')"),
                    approved_executables=("git",),
                )

            result = provider.run_command(
                ("python", "-c", "print('x')"),
                approved_executables=("python",),
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "x")

    def test_run_command_captures_failure_and_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = LocalWorkspaceProvider(directory)

            failed = provider.run_command(
                ("python", "-c", "import sys; print('bad', file=sys.stderr); sys.exit(2)"),
                approved_executables=("python",),
            )
            self.assertEqual(failed.returncode, 2)
            self.assertIn("bad", failed.stderr)

            with self.assertRaises(TimeoutError):
                provider.run_command(
                    ("python", "-c", "import time; time.sleep(1)"),
                    approved_executables=("python",),
                    timeout_seconds=1,
                )

    def test_git_diff_is_available_for_repository_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = LocalWorkspaceProvider(directory)
            provider.run_command(
                ("git", "init"),
                approved_executables=("git",),
            )
            provider.write_file("changed.txt", "change")
            self.assertIn("changed.txt", provider.git_diff())


if __name__ == "__main__":
    unittest.main()
