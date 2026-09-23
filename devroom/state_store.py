from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class PersistedWorkflow:
    workflow_id: str
    stage: str
    history: tuple[str, ...]
    results: tuple[dict[str, object], ...]
    halted_reason: str | None = None
    last_decision: str | None = None
    last_feedback: str | None = None
    goal: str | None = None
    workspace: str | None = None
    allowed_paths: tuple[str, ...] = ()
    max_feedback_cycles: int = 3


class JsonWorkflowStateStore:
    """Small durable state store for resumable DevRoom workflow records."""

    schema_version = 2

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def save(self, state: PersistedWorkflow) -> None:
        payload = {
            "schema_version": self.schema_version,
            "workflow_id": state.workflow_id,
            "stage": state.stage,
            "history": list(state.history),
            "results": list(state.results),
            "halted_reason": state.halted_reason,
            "last_decision": state.last_decision,
            "last_feedback": state.last_feedback,
            "goal": state.goal,
            "workspace": state.workspace,
            "allowed_paths": list(state.allowed_paths),
            "max_feedback_cycles": state.max_feedback_cycles,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(temporary, self.path)

    def load(self, workflow_id: str) -> PersistedWorkflow:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Workflow state is unreadable: {self.path}") from exc

        if not isinstance(payload, dict):
            raise ValueError("Workflow state root must be an object.")
        if payload.get("schema_version") not in {1, self.schema_version}:
            raise ValueError("Unsupported workflow state schema version.")
        if payload.get("workflow_id") != workflow_id:
            raise KeyError(f"Workflow state not found: {workflow_id!r}")

        stage = payload.get("stage")
        history = payload.get("history")
        results = payload.get("results")
        if not isinstance(stage, str) or not stage.strip():
            raise ValueError("Workflow state has an invalid stage.")
        if not isinstance(history, list) or not all(isinstance(item, str) for item in history):
            raise ValueError("Workflow state has invalid history.")
        if not isinstance(results, list):
            raise ValueError("Workflow state has invalid results.")
        for item in results:
            if not isinstance(item, dict):
                raise ValueError("Workflow state contains an invalid result entry.")
            if not isinstance(item.get("role"), str) or not isinstance(item.get("summary"), str):
                raise ValueError("Workflow state result entries require string role and summary.")
            artifacts = item.get("artifacts", [])
            if not isinstance(artifacts, list) or not all(isinstance(path, str) for path in artifacts):
                raise ValueError("Workflow state result artifacts must be a string list.")

        allowed_paths = payload.get("allowed_paths", [])
        if not isinstance(allowed_paths, list) or not all(isinstance(path, str) for path in allowed_paths):
            raise ValueError("Workflow state has invalid allowed_paths.")
        max_feedback_cycles = payload.get("max_feedback_cycles", 3)
        if isinstance(max_feedback_cycles, bool) or not isinstance(max_feedback_cycles, int) or max_feedback_cycles < 0:
            raise ValueError("Workflow state has invalid max_feedback_cycles.")

        for field in ("halted_reason", "last_decision", "last_feedback", "goal", "workspace"):
            value = payload.get(field)
            if value is not None and not isinstance(value, str):
                raise ValueError(f"Workflow state field {field!r} must be a string or null.")

        return PersistedWorkflow(
            workflow_id=workflow_id,
            stage=stage,
            history=tuple(history),
            results=tuple(dict(item) for item in results),
            halted_reason=payload.get("halted_reason"),
            last_decision=payload.get("last_decision"),
            last_feedback=payload.get("last_feedback"),
            goal=payload.get("goal"),
            workspace=payload.get("workspace"),
            allowed_paths=tuple(allowed_paths),
            max_feedback_cycles=max_feedback_cycles,
        )


class WorkflowStateWriter:
    """Adapter used by the orchestrator to persist snapshots after each transition."""

    def __init__(self, store: JsonWorkflowStateStore, workflow_id: str) -> None:
        if not workflow_id.strip():
            raise ValueError("workflow_id must not be blank")
        self.store = store
        self.workflow_id = workflow_id

    def write(
        self,
        stage: str,
        history: Iterable[str],
        results: Iterable[dict[str, object]],
        halted_reason: str | None = None,
        last_decision: str | None = None,
        last_feedback: str | None = None,
        goal: str | None = None,
        workspace: str | None = None,
        allowed_paths: Iterable[str] = (),
        max_feedback_cycles: int = 3,
    ) -> None:
        self.store.save(
            PersistedWorkflow(
                workflow_id=self.workflow_id,
                stage=stage,
                history=tuple(history),
                results=tuple(dict(item) for item in results),
                halted_reason=halted_reason,
                last_decision=last_decision,
                last_feedback=last_feedback,
                goal=goal,
                workspace=workspace,
                allowed_paths=tuple(allowed_paths),
                max_feedback_cycles=max_feedback_cycles,
            )
        )


__all__ = ["JsonWorkflowStateStore", "PersistedWorkflow", "WorkflowStateWriter"]
