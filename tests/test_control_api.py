import json
import time
import unittest
from urllib.request import Request, urlopen

from devroom.control_api import WorkflowController, serve_control_api
from devroom.orchestrator import HumanDecision, MockProvider


class ControlApiTests(unittest.TestCase):
    def _wait_for_gate(self, controller: WorkflowController, gate: str) -> None:
        for _ in range(200):
            snapshot = controller.snapshot()
            if snapshot["stage"] == gate and snapshot["status"] == "awaiting_human":
                return
            time.sleep(0.01)
        self.fail(f"workflow did not reach active {gate}")

    def _wait_for_status(self, controller: WorkflowController, status: str) -> None:
        for _ in range(200):
            if controller.snapshot()["status"] == status:
                return
            time.sleep(0.01)
        self.fail(f"workflow did not reach status {status}")

    def test_controller_exposes_final_confirmation_and_accepts_decision(self) -> None:
        controller = WorkflowController(
            MockProvider(),
            workflow_id="test-1",
            goal="Test final confirmation",
        )
        controller.start()
        self._wait_for_gate(controller, "human_confirmation")

        snapshot = controller.snapshot()
        self.assertEqual(snapshot["status"], "awaiting_human")
        self.assertEqual(snapshot["stage"], "human_confirmation")
        self.assertTrue(any(item["decision"] == "awaiting" for item in snapshot["feedback"]))

        controller.decide(HumanDecision.APPROVE)
        self._wait_for_status(controller, "complete")
        self.assertEqual(controller.snapshot()["stage"], "complete")

    def test_request_changes_requires_feedback(self) -> None:
        controller = WorkflowController(
            MockProvider(),
            workflow_id="test-2",
            goal="Test feedback validation",
        )
        controller.start()
        self._wait_for_gate(controller, "human_confirmation")

        with self.assertRaises(ValueError):
            controller.decide(HumanDecision.REQUEST_CHANGES, "   ")

        controller.decide(HumanDecision.REQUEST_CHANGES, "Fix the implementation.")
        self._wait_for_gate(controller, "human_confirmation")
        snapshot = controller.snapshot()
        self.assertEqual(snapshot["status"], "awaiting_human")
        self.assertTrue(
            any(
                item["decision"] == HumanDecision.REQUEST_CHANGES.value
                and item["feedback"] == "Fix the implementation."
                for item in snapshot["feedback"]
            )
        )

    def test_http_health_and_decision(self) -> None:
        controller = WorkflowController(
            MockProvider(),
            workflow_id="http-test",
            goal="Test HTTP control",
        )
        server = serve_control_api(controller, port=0)
        try:
            port = server.server_address[1]
            with urlopen(f"http://127.0.0.1:{port}/api/health", timeout=2) as response:
                self.assertEqual(json.load(response)["ok"], True)

            self._wait_for_gate(controller, "human_confirmation")
            request = Request(
                f"http://127.0.0.1:{port}/api/workflow/decision",
                data=json.dumps({"decision": "approve"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=2) as response:
                self.assertEqual(response.status, 202)
            self._wait_for_status(controller, "complete")
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
