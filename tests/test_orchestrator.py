import unittest

from devroom.orchestrator import DevRoomOrchestrator, MockProvider, Stage


class DevRoomOrchestratorTests(unittest.TestCase):
    def test_full_workflow_reaches_complete(self) -> None:
        provider = MockProvider()
        result = DevRoomOrchestrator(provider).run("Implement persistent vehicle ownership")

        self.assertEqual(result.stage, Stage.COMPLETE)
        self.assertEqual(
            result.history,
            [
                Stage.LEAD,
                Stage.ARCHITECT,
                Stage.GATE_1,
                Stage.IMPLEMENTER,
                Stage.REVIEWER,
                Stage.QA,
                Stage.LEAD_REPORT,
                Stage.GATE_2,
                Stage.COMPLETE,
            ],
        )
        self.assertEqual(len(provider.calls), 6)

    def test_gate_1_halts_before_implementation(self) -> None:
        provider = MockProvider()
        result = DevRoomOrchestrator(provider).run(
            "Implement persistent vehicle ownership",
            approve_gate_1=False,
        )

        self.assertEqual(result.stage, Stage.HALTED)
        self.assertIn(Stage.GATE_1, result.history)
        self.assertNotIn(Stage.IMPLEMENTER, result.history)

    def test_gate_2_halts_after_qa(self) -> None:
        provider = MockProvider()
        result = DevRoomOrchestrator(provider).run(
            "Implement persistent vehicle ownership",
            approve_gate_2=False,
        )

        self.assertEqual(result.stage, Stage.HALTED)
        self.assertIn(Stage.QA, result.history)
        self.assertIn(Stage.GATE_2, result.history)
        self.assertNotIn(Stage.COMPLETE, result.history)


if __name__ == "__main__":
    unittest.main()
