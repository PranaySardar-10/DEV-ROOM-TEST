import unittest

from devroom.orchestrator import DevRoomOrchestrator, MockProvider, Stage


class DevRoomOrchestratorTests(unittest.TestCase):
    def test_full_workflow_reaches_complete(self) -> None:
        provider = MockProvider()
        result = DevRoomOrchestrator(provider).run(
            "Implement persistent vehicle ownership",
            workspace=r"D:\DEV_ROOM_TEST",
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
        )
        reviewer = provider.calls[3]
        self.assertEqual(reviewer.role, "Reviewer")
        self.assertIn("architecture_summary", reviewer.context)
        self.assertNotIn("implementation_summary", reviewer.context)

    def test_gate_1_halts_before_implementation(self) -> None:
        provider = MockProvider()
        result = DevRoomOrchestrator(provider).run(
            "Implement persistent vehicle ownership",
            workspace=r"D:\DEV_ROOM_TEST",
            approve_gate_1=False,
        )
        self.assertEqual(result.stage, Stage.HALTED)
        self.assertIn(Stage.GATE_1, result.history)
        self.assertNotIn(Stage.IMPLEMENTER, result.history)

    def test_gate_2_halts_after_qa(self) -> None:
        provider = MockProvider()
        result = DevRoomOrchestrator(provider).run(
            "Implement persistent vehicle ownership",
            workspace=r"D:\DEV_ROOM_TEST",
            approve_gate_2=False,
        )
        self.assertEqual(result.stage, Stage.HALTED)
        self.assertIn(Stage.QA, result.history)
        self.assertIn(Stage.GATE_2, result.history)
        self.assertNotIn(Stage.COMPLETE, result.history)


if __name__ == "__main__":
    unittest.main()
