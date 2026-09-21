import tempfile
import unittest
from pathlib import Path

from devroom.control_server import build_provider


class ControlServerTests(unittest.TestCase):
    def test_mock_provider_bootstrap(self) -> None:
        provider = build_provider("mock")
        self.assertEqual(type(provider).__name__, "MockProvider")

    def test_unknown_provider_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_provider("unknown")

    def test_state_file_path_can_live_inside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            state = workspace / ".devroom" / "workflow.json"
            self.assertEqual(state.parent, workspace / ".devroom")


if __name__ == "__main__":
    unittest.main()
