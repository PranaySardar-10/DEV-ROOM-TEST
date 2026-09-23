from __future__ import annotations

import hmac
import ipaddress
import json
import threading
from dataclasses import asdict, dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Mapping

from .orchestrator import AgentProvider, AgentResult, DevRoomOrchestrator, HumanDecision, Stage
from .state_store import WorkflowStateWriter


@dataclass
class ControlSnapshot:
    workflow_id: str
    stage: str
    status: str
    goal: str
    workspace: str | None
    cycle: int
    current_agent: dict[str, str] | None
    history: list[str]
    results: list[dict[str, Any]]
    feedback: list[dict[str, Any]]
    halted_reason: str | None = None


class _TrackingProvider:
    def __init__(self, controller: "WorkflowController", provider: AgentProvider) -> None:
        self.controller = controller
        self.provider = provider

    def execute(self, task):
        self.controller._set_agent(task.role, task.context.get("provider", "unknown"))
        try:
            result = self.provider.execute(task)
            self.controller._add_result(result)
            return result
        finally:
            self.controller._clear_agent()


class WorkflowController:
    """Run one DevRoom workflow in the background and expose human gates to a UI."""

    def __init__(
        self,
        provider: AgentProvider,
        *,
        workflow_id: str,
        goal: str,
        workspace: str | None = None,
        allowed_paths: tuple[str, ...] = (),
        state_writer: WorkflowStateWriter | None = None,
        max_feedback_cycles: int = 3,
    ) -> None:
        if not workflow_id.strip():
            raise ValueError("workflow_id must not be blank")
        if not goal.strip():
            raise ValueError("goal must not be blank")

        self._condition = threading.Condition()
        self._provider = provider
        self._workflow_id = workflow_id
        self._goal = goal
        self._workspace = workspace
        self._allowed_paths = allowed_paths
        self._state_writer = state_writer
        self._max_feedback_cycles = max_feedback_cycles
        self._pending: tuple[HumanDecision, str] | None = None
        self._active_gate: Stage | None = None
        self._thread: threading.Thread | None = None
        self._snapshot = ControlSnapshot(
            workflow_id=workflow_id,
            stage=Stage.LEAD.value,
            status="starting",
            goal=goal,
            workspace=workspace,
            cycle=1,
            current_agent=None,
            history=[],
            results=[],
            feedback=[],
        )

    def start(self) -> None:
        with self._condition:
            if self._thread is not None:
                raise RuntimeError("workflow already started")
            self._thread = threading.Thread(target=self._run, name=f"devroom-{self._workflow_id}", daemon=True)
            self._thread.start()

    def snapshot(self) -> dict[str, Any]:
        with self._condition:
            return asdict(self._snapshot)

    def decide(self, decision: HumanDecision | str, feedback: str = "") -> None:
        try:
            decision = HumanDecision(decision)
        except ValueError as exc:
            raise ValueError(f"invalid decision: {decision!r}") from exc

        feedback = feedback.strip()
        with self._condition:
            if self._active_gate is None:
                raise RuntimeError("workflow is not waiting for a human decision")
            if decision is HumanDecision.REQUEST_CHANGES and not feedback:
                raise ValueError("feedback is required for request_changes")
            if self._pending is not None:
                raise RuntimeError("a gate decision is already pending")
            self._pending = (decision, feedback)
            self._snapshot.status = "resuming"
            self._condition.notify_all()

    def _set_agent(self, role: str, provider: str) -> None:
        with self._condition:
            self._snapshot.status = "running"
            self._snapshot.current_agent = {"role": role, "provider": provider}

    def _clear_agent(self) -> None:
        with self._condition:
            self._snapshot.current_agent = None

    def _add_result(self, result: AgentResult) -> None:
        with self._condition:
            self._snapshot.results.append(
                {"role": result.role, "summary": result.summary, "artifacts": list(result.artifacts)}
            )

    def _gate(self, stage: Stage, prompt: str, context: Mapping[str, str]):
        with self._condition:
            self._active_gate = stage
            self._snapshot.stage = stage.value
            self._snapshot.status = "awaiting_human"
            self._pending = None
            self._snapshot.feedback.append({"gate": stage.value, "decision": "awaiting", "feedback": prompt})
            self._condition.notify_all()
            while self._pending is None:
                self._condition.wait()

            decision, feedback = self._pending
            self._pending = None
            self._active_gate = None
            self._snapshot.status = "running"
            self._snapshot.feedback.append(
                {"gate": stage.value, "decision": decision.value, "feedback": feedback}
            )
            return decision, feedback

    def _run(self) -> None:
        try:
            orchestrator = DevRoomOrchestrator(
                _TrackingProvider(self, self._provider),
                state_writer=self._state_writer,
            )
            result = orchestrator.run(
                self._goal,
                workspace=self._workspace,
                allowed_paths=self._allowed_paths,
                human_gate=self._gate,
                max_feedback_cycles=self._max_feedback_cycles,
            )
            with self._condition:
                self._snapshot.stage = result.stage.value
                self._snapshot.status = "complete" if result.stage is Stage.COMPLETE else "halted"
                self._snapshot.history = [stage.value for stage in result.history]
                self._snapshot.halted_reason = result.halted_reason
                self._condition.notify_all()
        except Exception as exc:
            with self._condition:
                self._snapshot.status = "error"
                self._snapshot.stage = Stage.HALTED.value
                self._snapshot.halted_reason = f"{type(exc).__name__}: {exc}"
                self._condition.notify_all()


class _Handler(BaseHTTPRequestHandler):
    controller: WorkflowController | None = None
    control_token: str | None = None

    def _is_authorized(self) -> bool:
        if self.control_token is None:
            return True
        expected = f"Bearer {self.control_token}"
        provided = self.headers.get("Authorization", "")
        return hmac.compare_digest(provided, expected)

    def _is_loopback_origin(self) -> bool:
        origin = self.headers.get("Origin", "")
        if not origin:
            return False
        try:
            from urllib.parse import urlparse
            parsed = urlparse(origin)
            return parsed.scheme in {"http", "https"} and ipaddress.ip_address(parsed.hostname or "").is_loopback
        except ValueError:
            return False

    def _send(self, status: int, payload: Mapping[str, Any]) -> None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        origin = self.headers.get("Origin")
        if origin and self._is_loopback_origin():
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()
        if status != 204:
            self.wfile.write(data)

    def do_OPTIONS(self) -> None:
        self._send(204, {})

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self._send(200, {"ok": True})
            return
        if self.path == "/api/workflow" and self.controller is not None:
            if not self._is_authorized():
                self._send(401, {"error": "unauthorized"})
                return
            self._send(200, self.controller.snapshot())
            return
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/api/workflow/decision" or self.controller is None:
            self._send(404, {"error": "not found"})
            return
        if not self._is_authorized():
            self._send(401, {"error": "unauthorized"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length) or b"{}")
            self.controller.decide(body.get("decision", ""), str(body.get("feedback", "")))
            self._send(202, {"accepted": True, "workflow": self.controller.snapshot()})
        except (ValueError, RuntimeError) as exc:
            self._send(409, {"error": str(exc)})

    def log_message(self, format: str, *args: object) -> None:
        return


def serve_control_api(
    controller: WorkflowController,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    control_token: str | None = None,
) -> ThreadingHTTPServer:
    """Start the control API and return its server for lifecycle management."""
    try:
        is_loopback = ipaddress.ip_address(host).is_loopback
    except ValueError:
        is_loopback = host.lower() in {"localhost", "localhost.localdomain"}
    if not is_loopback and not control_token:
        raise ValueError("control_token is required when binding the control API to a non-loopback host")
    if control_token is not None and not control_token.strip():
        raise ValueError("control_token must not be blank")
    _Handler.controller = controller
    _Handler.control_token = control_token
    server = ThreadingHTTPServer((host, port), _Handler)
    controller.start()
    thread = threading.Thread(target=server.serve_forever, name="devroom-control-api", daemon=True)
    thread.start()
    return server


__all__ = ["ControlSnapshot", "WorkflowController", "serve_control_api"]
