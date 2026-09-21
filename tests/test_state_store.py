import tempfile
import unittest
from pathlib import Path

from devroom.state_store import JsonWorkflowStateStore, PersistedWorkflow


class WorkflowStateStoreTests(unittest.TestCase):
    def test_round_trip_and_atomic_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state" / "workflow.json"
            store = JsonWorkflowStateStore(path)
            state = PersistedWorkflow(
                workflow_id="abc",
                stage="gate_2",
                history=("lead", "architect", "gate_1", "implementer", "gate_2"),
                results=(
                    {"role": "Lead", "summary": "ok", "artifacts": []},
                ),
            )
            store.save(state)

            self.assertTrue(path.exists())
            self.assertFalse(path.with_suffix(".json.tmp").exists())
            self.assertEqual(store.load("abc"), state)

    def test_rejects_wrong_workflow_id_and_schema(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workflow.json"
            store = JsonWorkflowStateStore(path)
            store.save(PersistedWorkflow("abc", "complete", (), ()))

            with self.assertRaises(KeyError):
                store.load("other")

            path.write_text(
                '{"schema_version": 999, "workflow_id": "abc", "stage": "complete", "history": [], "results": []}',
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                store.load("abc")


if __name__ == "__main__":
    unittest.main()
