import json
import time
import unittest
from urllib.error import HTTPError
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

    def test_controller_exposes_human_review_and_accepts_decision(self) -> None:
        controller = WorkflowController(
            MockProvider(),
            workflow_id="test-1",
            goal="Test human review",
        )
        controller.start()
        self._wait_for_gate(controller, "human_review")

        snapshot = controller.snapshot()
        self.assertEqual(snapshot["status"], "awaiting_human")
        self.assertEqual(snapshot["stage"], "human_review")
        self.assertTrue(any(item["decision"] == "awaiting" for item in snapshot["feedback"]))

        controller.decide(HumanDecision.APPROVE)
        self._wait_for_gate(controller, "unity_validation")
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
        self._wait_for_gate(controller, "human_review")

        with self.assertRaises(ValueError):
            controller.decide(HumanDecision.REQUEST_CHANGES, "   ")

        controller.decide(HumanDecision.REQUEST_CHANGES, "Fix the implementation.")
        self._wait_for_gate(controller, "human_review")
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

            self._wait_for_gate(controller, "human_review")
            request = Request(
                f"http://127.0.0.1:{port}/api/workflow/decision",
                data=json.dumps({"decision": "approve"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=2) as response:
                self.assertEqual(response.status, 202)
            self._wait_for_gate(controller, "unity_validation")
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


    def test_remote_bind_requires_control_token(self) -> None:
        controller = WorkflowController(MockProvider(), workflow_id="remote-bind", goal="Remote bind")
        with self.assertRaises(ValueError):
            serve_control_api(controller, host="0.0.0.0", port=0)

    def test_control_token_protects_workflow_and_decision(self) -> None:
        controller = WorkflowController(MockProvider(), workflow_id="auth-test", goal="Test control auth")
        server = serve_control_api(controller, port=0, control_token="test-secret")
        try:
            port = server.server_address[1]
            with urlopen(f"http://127.0.0.1:{port}/api/health", timeout=2) as response:
                self.assertEqual(response.status, 200)

            self._wait_for_gate(controller, "human_review")
            with self.assertRaises(HTTPError) as ctx:
                urlopen(f"http://127.0.0.1:{port}/api/workflow", timeout=2)
            self.assertEqual(ctx.exception.code, 401)

            request = Request(
                f"http://127.0.0.1:{port}/api/workflow/decision",
                data=json.dumps({"decision": "approve"}).encode(),
                headers={"Content-Type": "application/json", "Authorization": "Bearer wrong"},
                method="POST",
            )
            with self.assertRaises(HTTPError) as ctx:
                urlopen(request, timeout=2)
            self.assertEqual(ctx.exception.code, 401)

            request = Request(
                f"http://127.0.0.1:{port}/api/workflow/decision",
                data=json.dumps({"decision": "approve"}).encode(),
                headers={"Content-Type": "application/json", "Authorization": "Bearer test-secret"},
                method="POST",
            )
            with urlopen(request, timeout=2) as response:
                self.assertEqual(response.status, 202)
            self._wait_for_gate(controller, "unity_validation")

            request = Request(
                f"http://127.0.0.1:{port}/api/workflow/decision",
                data=json.dumps({"decision": "approve"}).encode(),
                headers={"Content-Type": "application/json", "Authorization": "Bearer test-secret"},
                method="POST",
            )
            with urlopen(request, timeout=2) as response:
                self.assertEqual(response.status, 202)
            self._wait_for_status(controller, "complete")
        finally:
            server.shutdown()
            server.server_close()

    def test_cors_does_not_allow_arbitrary_origins(self) -> None:
        controller = WorkflowController(MockProvider(), workflow_id="cors-test", goal="Test CORS")
        server = serve_control_api(controller, port=0)
        try:
            port = server.server_address[1]
            request = Request(f"http://127.0.0.1:{port}/api/health", headers={"Origin": "https://evil.example"})
            with urlopen(request, timeout=2) as response:
                self.assertIsNone(response.headers.get("Access-Control-Allow-Origin"))

            request = Request(f"http://127.0.0.1:{port}/api/health", headers={"Origin": "http://127.0.0.1:3000"})
            with urlopen(request, timeout=2) as response:
                self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "http://127.0.0.1:3000")
        finally:
            server.shutdown()
            server.server_close()

    def test_controller_forwards_allowed_paths_to_orchestrator(self) -> None:
        provider = MockProvider()
        controller = WorkflowController(
            provider,
            workflow_id="scope-test",
            goal="Test scoped implementation",
            workspace=r"D:\DEV_ROOM_TEST",
            allowed_paths=("Assets/Scripts/Test.cs",),
        )
        controller.start()
        self._wait_for_gate(controller, "human_review")
        controller.decide(HumanDecision.APPROVE)
        self._wait_for_gate(controller, "unity_validation")

        implementer = next(task for task in provider.calls if task.role == "Implementer")
        self.assertEqual(implementer.context["workspace"], r"D:\DEV_ROOM_TEST")
        self.assertEqual(implementer.context["allowed_paths"], "Assets/Scripts/Test.cs")

        controller.decide(HumanDecision.HALT, "Stop after scope assertion.")
        self._wait_for_status(controller, "halted")


if __name__ == "__main__":
    unittest.main()
