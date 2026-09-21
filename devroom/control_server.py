from __future__ import annotations

import argparse
from pathlib import Path

from .codex_provider import CodexCliProvider
from .control_api import WorkflowController, serve_control_api
from .orchestrator import MockProvider
from .provider_router import ProviderRouter, RoleBinding
from .sandbox_policy import READ_ONLY, WORKSPACE_WRITE, RoleSandboxPolicy
from .state_store import JsonWorkflowStateStore, WorkflowStateWriter


def build_provider(kind: str):
    if kind == "mock":
        return MockProvider()

    if kind == "codex":
        codex = CodexCliProvider()
        bindings = {
            "Lead": RoleBinding("codex", "Coordinate the workflow; do not implement production code or merge changes.", READ_ONLY),
            "Architect": RoleBinding("codex", "Produce design, interfaces, dependencies, and acceptance criteria; do not implement production code.", READ_ONLY),
            "Implementer": RoleBinding("codex", "Implement only the approved task scope. Do not self-certify or merge changes.", WORKSPACE_WRITE),
            "Reviewer": RoleBinding("codex", "Review independently from a fresh context. Inspect the diff, requirements, tests, and repository. Do not modify the implementation.", READ_ONLY),
            "QA": RoleBinding("codex", "Run or inspect tests and report reproducible evidence; do not modify implementation.", READ_ONLY),
        }
        return ProviderRouter(
            {"codex": codex},
            bindings,
            sandbox_policy=RoleSandboxPolicy(),
        )

    raise ValueError(f"Unsupported provider: {kind}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local DevRoom control API.")
    parser.add_argument("--goal", required=True, help="Workflow goal.")
    parser.add_argument("--workspace", required=True, help="Existing workspace directory.")
    parser.add_argument("--workflow-id", default="devroom-local", help="Stable workflow identifier.")
    parser.add_argument("--provider", choices=("mock", "codex"), default="mock")
    parser.add_argument("--state-file", default=".devroom/workflow.json")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    if not workspace.is_dir():
        raise SystemExit(f"Workspace does not exist or is not a directory: {workspace}")

    state_path = Path(args.state_file)
    if not state_path.is_absolute():
        state_path = workspace / state_path

    provider = build_provider(args.provider)
    writer = WorkflowStateWriter(JsonWorkflowStateStore(state_path), args.workflow_id)
    controller = WorkflowController(
        provider,
        workflow_id=args.workflow_id,
        goal=args.goal,
        workspace=str(workspace),
        state_writer=writer,
    )
    server = serve_control_api(controller, host=args.host, port=args.port)
    print(f"DevRoom control API listening on http://{args.host}:{server.server_address[1]}")
    print(f"Workflow: {args.workflow_id}")
    print("Press Ctrl+C to stop.")

    try:
        controller._thread.join()  # Keep the small bootstrap process alive until the workflow exits.
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
