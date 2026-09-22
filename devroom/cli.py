from __future__ import annotations

import argparse
import sys

from .bootstrap import build_from_config
from .config import load_config
from .orchestrator import HumanDecision, Stage
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
        "--check",
        action="store_true",
        help="Validate configuration and provider availability, then exit.",
    )
    args = parser.parse_args()
    if not args.check and (not args.goal or not args.workspace):
        parser.error("--goal and --workspace are required unless --check is used.")
    return args


def main() -> int:
    args = _parse_args()

    try:
        config = load_config(args.config)
        require_available_providers(config.providers)
        if args.check:
            print("DevRoom startup checks passed.")
            return 0
        orchestrator = build_from_config(config)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"DevRoom startup failed: {exc}", file=sys.stderr)
        return 2

    result = orchestrator.run(
        args.goal,
        workspace=args.workspace,
        allowed_paths=tuple(args.allowed_path),
        human_gate=_human_gate,
        max_feedback_cycles=args.max_feedback_cycles,
    )
    print(f"\nDevRoom finished: {result.stage.value}")
    if result.halted_reason:
        print(f"Reason: {result.halted_reason}")
    return 0 if result.stage.value == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
