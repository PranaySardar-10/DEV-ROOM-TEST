import tempfile
import unittest
from pathlib import Path

from devroom.orchestrator import DevRoomOrchestrator, HumanDecision, MockProvider, Stage
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
        self.assertEqual(len(provider.calls), 2)

    def test_full_workflow_reaches_complete_after_human_approval(self) -> None:
        provider = MockProvider()
        result = DevRoomOrchestrator(provider).run(
            "Implement persistent vehicle ownership",
            workspace=r"D:\DEV_ROOM_TEST",
            human_gate=self.approve_all,
        )
        self.assertEqual(result.stage, Stage.COMPLETE)
        self.assertEqual(
            result.history,
            [
                Stage.LEAD, Stage.ARCHITECT, Stage.GATE_1, Stage.IMPLEMENTER,
                Stage.REVIEWER, Stage.QA, Stage.LEAD_REPORT, Stage.GATE_2, Stage.COMPLETE,
            ],
        )
        self.assertEqual(len(provider.calls), 6)
        self.assertTrue(all(task.context["workspace"] == r"D:\DEV_ROOM_TEST" for task in provider.calls))

    def test_reviewer_gets_independent_context(self) -> None:
        provider = MockProvider()
        DevRoomOrchestrator(provider).run(
            "Implement persistent vehicle ownership",
            workspace=r"D:\DEV_ROOM_TEST",
            human_gate=self.approve_all,
        )
        reviewer = provider.calls[3]
        self.assertEqual(reviewer.role, "Reviewer")
        self.assertIn("architecture_summary", reviewer.context)
        self.assertNotIn("implementation_summary", reviewer.context)
        self.assertNotIn("human_feedback", reviewer.context)

    def test_gate_1_request_changes_revises_architecture(self) -> None:
        provider = MockProvider()
        decisions = iter([
            (HumanDecision.REQUEST_CHANGES, "Use a server-authoritative ownership model."),
            (HumanDecision.APPROVE, ""),
            (HumanDecision.APPROVE, ""),
        ])

        result = DevRoomOrchestrator(provider).run(
            "Implement persistent vehicle ownership",
            workspace=r"D:\DEV_ROOM_TEST",
            human_gate=lambda stage, prompt, context: next(decisions),
        )

        self.assertEqual(result.stage, Stage.COMPLETE)
        self.assertEqual(
            [task.role for task in provider.calls],
            ["Lead", "Architect", "Architect", "Implementer", "Reviewer", "QA", "Lead"],
        )
        self.assertIn("human_feedback", provider.calls[2].context)

    def test_gate_2_visual_feedback_triggers_implementation_cycle(self) -> None:
        provider = MockProvider()
        decisions = iter([
            (HumanDecision.APPROVE, ""),
            (HumanDecision.REQUEST_CHANGES, "The vehicle clips through the road in Unity."),
            (HumanDecision.APPROVE, ""),
        ])

        result = DevRoomOrchestrator(provider).run(
            "Implement vehicle suspension",
            workspace=r"D:\DEV_ROOM_TEST",
            human_gate=lambda stage, prompt, context: next(decisions),
        )

        self.assertEqual(result.stage, Stage.COMPLETE)
        self.assertEqual(
            [task.role for task in provider.calls],
            [
                "Lead", "Architect",
                "Implementer", "Reviewer", "QA", "Lead",
                "Implementer", "Reviewer", "QA", "Lead",
            ],
        )
        second_implementation = provider.calls[6]
        self.assertEqual(
            second_implementation.context["human_feedback"],
            "The vehicle clips through the road in Unity.",
        )

    def test_gate_2_halt_stops_workflow(self) -> None:
        provider = MockProvider()
        result = DevRoomOrchestrator(provider).run(
            "Implement persistent vehicle ownership",
            workspace=r"D:\DEV_ROOM_TEST",
            human_gate=lambda stage, prompt, context: (
                HumanDecision.HALT if stage is Stage.GATE_2 else HumanDecision.APPROVE,
                "Keep the change isolated for now." if stage is Stage.GATE_2 else "",
            ),
        )
        self.assertEqual(result.stage, Stage.HALTED)
        self.assertIn(Stage.GATE_2, result.history)
        self.assertNotIn(Stage.COMPLETE, result.history)

    def test_gate_2_feedback_cycle_limit_halts(self) -> None:
        provider = MockProvider()
        result = DevRoomOrchestrator(provider).run(
            "Implement visual feature",
            workspace=r"D:\DEV_ROOM_TEST",
            max_feedback_cycles=1,
            human_gate=lambda stage, prompt, context: (
                (HumanDecision.APPROVE, "")
                if stage is Stage.GATE_1
                else (HumanDecision.REQUEST_CHANGES, "Fix it again.")
            ),
        )
        self.assertEqual(result.stage, Stage.HALTED)
        self.assertIn("Maximum human feedback cycles", result.halted_reason or "")

    def test_persists_final_workflow_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workflow.json"
            writer = WorkflowStateWriter(JsonWorkflowStateStore(path), "workflow-1")
            result = DevRoomOrchestrator(
                MockProvider(),
                state_writer=writer,
            ).run("Persist this workflow", human_gate=self.approve_all)

            persisted = JsonWorkflowStateStore(path).load("workflow-1")
            self.assertEqual(result.stage.value, persisted.stage)
            self.assertEqual(tuple(stage.value for stage in result.history), persisted.history)
            self.assertEqual(len(result.results), len(persisted.results))
            self.assertEqual(persisted.halted_reason, None)

    def test_blank_goal_and_workspace_are_rejected(self) -> None:
        provider = MockProvider()
        with self.assertRaises(ValueError):
            DevRoomOrchestrator(provider).run("  ")
        with self.assertRaises(ValueError):
            DevRoomOrchestrator(provider).run("Goal", workspace="  ")


if __name__ == "__main__":
    unittest.main()
