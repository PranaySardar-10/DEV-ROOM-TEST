import json
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
                goal="Test resume",
                workspace=r"D:\\workspace",
                allowed_paths=("Assets/Test.cs",),
                max_feedback_cycles=2,
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

    def test_rejects_corrupt_and_malformed_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workflow.json"
            store = JsonWorkflowStateStore(path)

            path.write_text("{not-json", encoding="utf-8")
            with self.assertRaises(ValueError):
                store.load("abc")

            path.write_text(json.dumps({
                "schema_version": 2,
                "workflow_id": "abc",
                "stage": "complete",
                "history": "not-a-list",
                "results": [],
            }), encoding="utf-8")
            with self.assertRaises(ValueError):
                store.load("abc")

            path.write_text(json.dumps({
                "schema_version": 2,
                "workflow_id": "abc",
                "stage": "complete",
                "history": [],
                "results": [{"role": "Lead", "summary": 123}],
            }), encoding="utf-8")
            with self.assertRaises(ValueError):
                store.load("abc")

    def test_accepts_legacy_v1_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workflow.json"
            path.write_text(json.dumps({
                "schema_version": 1,
                "workflow_id": "legacy",
                "stage": "human_review",
                "history": ["lead", "architect", "coder", "human_review"],
                "results": [],
            }), encoding="utf-8")
            state = JsonWorkflowStateStore(path).load("legacy")
            self.assertEqual(state.max_feedback_cycles, 3)
            self.assertEqual(state.allowed_paths, ())


if __name__ == "__main__":
    unittest.main()
