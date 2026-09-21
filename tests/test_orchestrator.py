import tempfile
import unittest
from pathlib import Path

from devroom.orchestrator import AgentResult, DevRoomOrchestrator, HumanDecision, MockProvider, Stage
from devroom.state_store import JsonWorkflowStateStore, WorkflowStateWriter


class DevRoomOrchestratorTests(unittest.TestCase):
    def approve_all(self, stage, prompt, context):
        return HumanDecision.APPROVE, ""

    def test_full_workflow_requires_explicit_human_approval(self) -> None:
        provider = MockProvider()
        result = DevRoomOrchestrator(provider).run(
            "Implement persistent vehicle ownership",
            workspace=r"D:\DEV_ROOM_TEST",
        )
        self.assertEqual(result.stage, Stage.HALTED)
        self.assertIn(Stage.GATE_1, result.history)
        self.assertEqual(len(provider.calls), 2)    def test_gate_decision_persists_after_callback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workflow.json"
            writer = WorkflowStateWriter(JsonWorkflowStateStore(path), "workflow-callback")
            provider = MockProvider()
            seen = []

            def gate(stage, prompt, context):
                persisted = JsonWorkflowStateStore(path).load("workflow-callback")
                seen.append((stage, persisted.last_decision))
                return (
                    (HumanDecision.APPROVE, "")
                    if stage is Stage.GATE_1
                    else (HumanDecision.HALT, "stop")
                )

            result = DevRoomOrchestrator(
                provider,
                state_writer=writer,
            ).run(
                "Persist callback ordering",
                human_gate=gate,
            )
            final_state = JsonWorkflowStateStore(path).load("workflow-callback")
            self.assertEqual(result.stage, Stage.HALTED)
            self.assertEqual(
                seen,
                [
                    (Stage.GATE_1, None),
                    (Stage.GATE_2, HumanDecision.APPROVE.value),
                ],
            )
            self.assertEqual(final_state.last_decision, HumanDecision.HALT.value)
            self.assertEqual(final_state.last_feedback, "stop")

