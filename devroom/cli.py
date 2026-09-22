from __future__ import annotations

import argparse

from .bootstrap import build_from_config_file
from .orchestrator import HumanDecision, Stage


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a DevRoom workflow.")
    parser.add_argument("--config", required=True, help="Path to devroom.json")
    parser.add_argument("--goal", required=True, help="Workflow goal")
    parser.add_argument("--workspace", required=True, help="Target workspace")
    parser.add_argument("--max-feedback-cycles", type=int, default=3)
    args = parser.parse_args()

    orchestrator = build_from_config_file(args.config)
    result = orchestrator.run(
        args.goal,
        workspace=args.workspace,
        human_gate=_human_gate,
        max_feedback_cycles=args.max_feedback_cycles,
    )
    print(f"\nDevRoom finished: {result.stage.value}")
    if result.halted_reason:
        print(f"Reason: {result.halted_reason}")
    return 0 if result.stage.value == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
