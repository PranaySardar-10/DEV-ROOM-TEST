from __future__ import annotations

import argparse
import sys
from pathlib import Path
from uuid import uuid4


from .bootstrap import build_from_config
from .config import load_config
from .orchestrator import HumanDecision, Stage
from .state_store import JsonWorkflowStateStore, WorkflowStateWriter
from .provider_health import require_available_providers


def _human_gate(stage: Stage, prompt: str, context: dict[str, str]):
    print(f"\n[{stage.value}]")
    print(prompt)
    for key, value in context.items():
        print(f"\n{key}:\n{value}")
    while True:
        choice = input("\nDecision [approve/request_changes/halt]: ").strip().lower()
        if choice in {"approve", "halt"}:
            return HumanDecision(choice), ""
        if choice == "request_changes":
            feedback = input("Feedback: ").strip()
            if feedback:
                return HumanDecision.REQUEST_CHANGES, feedback
        print("Enter approve, request_changes, or halt.")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a DevRoom workflow.")
    parser.add_argument("--config", required=True, help="Path to devroom.json")
    parser.add_argument("--goal", help="Workflow goal")
    parser.add_argument("--workspace", help="Target workspace")
    parser.add_argument(
        "--allowed-path",
        action="append",
        default=[],
        help="Relative production file path the Implementer may modify; repeat for multiple files.",
    )
    parser.add_argument("--max-feedback-cycles", type=int, default=3)
    parser.add_argument(
        "--state-dir",
        default=".devroom/state",
        help="Directory for durable workflow state snapshots.",
    )
    parser.add_argument(
        "--workflow-id",
        default=None,
        help="Optional workflow ID; generated automatically when omitted.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate configuration and provider availability, then exit.",
    )
    args = parser.parse_args()
    if not args.check and not args.resume and (not args.goal or not args.workspace):
        parser.error("--goal and --workspace are required unless --check or --resume is used.")
    if not args.check and not args.resume and not args.allowed_path:
        parser.error("At least one --allowed-path is required for a production Implementer run.")
    if args.resume and not args.workflow_id:
        parser.error("--workflow-id is required with --resume.")
    return args


def main() -> int:
    args = _parse_args()

    try:
        config = load_config(args.config)
        require_available_providers(config.providers)
        if args.check:
            print("DevRoom startup checks passed.")
            return 0
        workflow_id = args.workflow_id or uuid4().hex
        state_path = Path(args.state_dir) / f"{workflow_id}.json"
        state_store = JsonWorkflowStateStore(state_path)
        resume_state = state_store.load(workflow_id) if args.resume else None
        if resume_state is not None:
            if resume_state.goal is None or resume_state.workspace is None:
                raise ValueError("workflow state does not contain resume inputs")
            goal = resume_state.goal
            workspace = resume_state.workspace
            allowed_paths = resume_state.allowed_paths
            max_feedback_cycles = resume_state.max_feedback_cycles
        else:
            goal = args.goal
            workspace = args.workspace
            allowed_paths = tuple(args.allowed_path)
            max_feedback_cycles = args.max_feedback_cycles
        state_writer = WorkflowStateWriter(state_store, workflow_id)
        orchestrator = build_from_config(config, state_writer=state_writer)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"DevRoom startup failed: {exc}", file=sys.stderr)
        return 2

    result = orchestrator.run(
        goal,
        workspace=workspace,
        allowed_paths=allowed_paths,
        human_gate=_human_gate,
        max_feedback_cycles=max_feedback_cycles,
        resume_state=resume_state,
    )
    print(f"\nDevRoom finished: {result.stage.value}")
    if result.halted_reason:
        print(f"Reason: {result.halted_reason}")
    return 0 if result.stage.value == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
