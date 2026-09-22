import tempfile
import unittest
from pathlib import Path

from devroom.orchestrator import AgentResult, DevRoomOrchestrator, HumanDecision, MockProvider, Stage
from devroom.state_store import JsonWorkflowStateStore, WorkflowStateWriter


class DevRoomOrchestratorTests(unittest.TestCase):
    def approve_all(self, stage, prompt, context):
        return HumanDecision.APPROVE, ""

    def test_workflow_without_human_confirmation_halts_after_report(self) -> None:
        provider = MockProvider()
        result = DevRoomOrchestrator(provider).run(
            "Implement persistent vehicle ownership",
            workspace=r"D:\DEV_ROOM_TEST",
        )
        self.assertEqual(result.stage, Stage.HALTED)
        self.assertIn(Stage.HUMAN_CONFIRMATION, result.history)
        self.assertEqual(len(provider.calls), 6)

    def test_final_confirmation_persists_after_callback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workflow.json"
            writer = WorkflowStateWriter(JsonWorkflowStateStore(path), "workflow-callback")
            provider = MockProvider()
            seen = []

            def gate(stage, prompt, context):
                persisted = JsonWorkflowStateStore(path).load("workflow-callback")
                seen.append((stage, persisted.last_decision))
                return HumanDecision.HALT, "stop"

            result = DevRoomOrchestrator(
                provider,
                state_writer=writer,
            ).run(
                "Persist callback ordering",
                human_gate=gate,
            )
            final_state = JsonWorkflowStateStore(path).load("workflow-callback")
            self.assertEqual(result.stage, Stage.HALTED)
            self.assertEqual(seen, [(Stage.HUMAN_CONFIRMATION, None)])
            self.assertEqual(final_state.last_decision, HumanDecision.HALT.value)
            self.assertEqual(final_state.last_feedback, "stop")

    def test_missing_implementation_artifacts_halt_before_review(self) -> None:
        class EmptyImplementerProvider(MockProvider):
            def execute(self, task):
                self.calls.append(task)
                if task.role == "Implementer":
                    return AgentResult(role=task.role, summary="No implementation was produced.")
                return AgentResult(role=task.role, summary=f"Mock {task.role} completed.", artifacts=("mock",))

        provider = EmptyImplementerProvider()
        result = DevRoomOrchestrator(provider).run(
            "Require implementation proof",
            human_gate=self.approve_all,
        )
        self.assertEqual(result.stage, Stage.HALTED)
        self.assertIn("implementation artifacts", result.halted_reason or "")
        self.assertEqual(
            [task.role for task in provider.calls],
            ["Lead", "Architect", "Implementer"],
        )

    def test_full_workflow_reaches_complete_after_final_confirmation(self) -> None:
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
                Stage.LEAD,
                Stage.ARCHITECT,
                Stage.IMPLEMENTER,
                Stage.REVIEWER,
                Stage.QA,
                Stage.LEAD_REPORT,
                Stage.HUMAN_CONFIRMATION,
                Stage.COMPLETE,
            ],
        )
        self.assertEqual(len(provider.calls), 6)
        self.assertTrue(
            all(task.context["workspace"] == r"D:\DEV_ROOM_TEST" for task in provider.calls)
        )

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

    def test_implementation_feedback_triggers_new_implementation_cycle(self) -> None:
        provider = MockProvider()
        decisions = iter([
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
                "Lead",
                "Architect",
                "Implementer",
                "Reviewer",
                "QA",
                "Lead",
                "Implementer",
                "Reviewer",
                "QA",
                "Lead",
            ],
        )
        second_implementation = provider.calls[6]
        self.assertEqual(
            second_implementation.context["human_feedback"],
            "The vehicle clips through the road in Unity.",
        )

    def test_human_halt_stops_workflow(self) -> None:
        provider = MockProvider()
        result = DevRoomOrchestrator(provider).run(
            "Implement persistent vehicle ownership",
            human_gate=lambda stage, prompt, context: (
                HumanDecision.HALT,
                "Keep the change isolated for now.",
            ),
        )
        self.assertEqual(result.stage, Stage.HALTED)
        self.assertIn(Stage.HUMAN_CONFIRMATION, result.history)
        self.assertNotIn(Stage.COMPLETE, result.history)

    def test_feedback_cycle_limit_halts(self) -> None:
        provider = MockProvider()
        result = DevRoomOrchestrator(
            provider,
        ).run(
            "Implement visual feature",
            max_feedback_cycles=1,
            human_gate=lambda stage, prompt, context: (
                HumanDecision.REQUEST_CHANGES,
                "Fix it again.",
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
            self.assertEqual(
                tuple(stage.value for stage in result.history),
                persisted.history,
            )
            self.assertEqual(len(result.results), len(persisted.results))
            self.assertIsNone(persisted.halted_reason)

    def test_blank_goal_and_workspace_are_rejected(self) -> None:
        provider = MockProvider()
        with self.assertRaises(ValueError):
            DevRoomOrchestrator(provider).run("  ")
        with self.assertRaises(ValueError):
            DevRoomOrchestrator(provider).run("Goal", workspace="  ")


if __name__ == "__main__":
    unittest.main()
