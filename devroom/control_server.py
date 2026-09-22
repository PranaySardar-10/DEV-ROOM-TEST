from __future__ import annotations

import argparse
import time
from pathlib import Path

from .bootstrap import build_from_config_file
from .config import write_example_config
from .control_api import WorkflowController, serve_control_api
from .orchestrator import MockProvider


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local DevRoom control API.")
    parser.add_argument("--goal", required=True, help="Workflow goal.")
    parser.add_argument("--workspace", required=True, help="Existing workspace directory.")
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the production DevRoom JSON configuration.",
    )
    parser.add_argument(
        "--workflow-id",
        default="devroom-local",
        help="Stable workflow identifier.",
    )
    parser.add_argument(
        "--provider",
        choices=("config", "mock"),
        default="config",
        help="Use the production configured local workforce or deterministic mock mode.",
    )
    parser.add_argument(
        "--allowed-path",
        action="append",
        default=[],
        help="Relative production file path the Implementer may modify; repeat for multiple files.",
    )
    parser.add_argument("--state-file", default=".devroom/workflow.json")
    parser.add_argument("--max-feedback-cycles", type=int, default=3)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    if not workspace.is_dir():
        raise SystemExit(f"Workspace does not exist or is not a directory: {workspace}")

    if args.provider == "config":
        provider = build_from_config_file(args.config).provider
    else:
        provider = MockProvider()

    state_path = Path(args.state_file)
    if not state_path.is_absolute():
        state_path = workspace / state_path

    from .state_store import JsonWorkflowStateStore, WorkflowStateWriter

    writer = WorkflowStateWriter(
        JsonWorkflowStateStore(state_path),
        args.workflow_id,
    )
    controller = WorkflowController(
        provider,
        workflow_id=args.workflow_id,
        goal=args.goal,
        workspace=str(workspace),
        allowed_paths=tuple(args.allowed_path),
        state_writer=writer,
        max_feedback_cycles=args.max_feedback_cycles,
    )
    server = serve_control_api(controller, host=args.host, port=args.port)
    print(f"DevRoom control API listening on http://{args.host}:{server.server_address[1]}")
    print(f"Workflow: {args.workflow_id}")
    print("Press Ctrl+C to stop.")

    try:
        while controller.snapshot()["status"] not in {"complete", "halted", "error"}:
            time.sleep(0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
