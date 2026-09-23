import tempfile
import unittest
from pathlib import Path

from devroom.orchestrator import (
    AgentResult,
    DevRoomOrchestrator,
    HumanDecision,
    MockProvider,
    ResourceGuard,
    Stage,
)
from devroom.state_store import JsonWorkflowStateStore, WorkflowStateWriter


class DevRoomOrchestratorTests(unittest.TestCase):
    def approve_all(self, stage, prompt, context):
        return HumanDecision.APPROVE, ""

    def test_workflow_without_human_review_halts_before_implementation(self) -> None:
        provider = MockProvider()
        result = DevRoomOrchestrator(provider).run("Implement vehicle ownership")
        self.assertEqual(result.stage, Stage.HALTED)
        self.assertIn(Stage.HUMAN_REVIEW, result.history)
        self.assertNotIn(Stage.IMPLEMENTER, result.history)
        self.assertEqual([task.role for task in provider.calls], ["Lead", "Architect", "Coder"])

    def test_approval_precedes_implementation(self) -> None:
        provider = MockProvider()
        result = DevRoomOrchestrator(provider).run(
            "Implement vehicle ownership",
            workspace=r"D:\DEV_ROOM_TEST",
            allowed_paths=("Assets/Scripts/VehicleOwnership.cs",),
            human_gate=self.approve_all,
        )
        self.assertEqual(result.stage, Stage.COMPLETE)
        self.assertEqual(
            result.history,
            [
                Stage.LEAD,
                Stage.ARCHITECT,
                Stage.CODER,
                Stage.HUMAN_REVIEW,
                Stage.IMPLEMENTER,
                Stage.QA,
                Stage.UNITY_VALIDATION,
                Stage.COMPLETE,
            ],
        )
        roles = [task.role for task in provider.calls]
        self.assertEqual(
            roles,
            ["Lead", "Architect", "Coder", "Implementer", "QA"],
        )
        self.assertTrue(
            all(task.context["workspace"] == r"D:\DEV_ROOM_TEST" for task in provider.calls)
        )
        self.assertTrue(
            all(task.context["allowed_paths"] == "Assets/Scripts/VehicleOwnership.cs"
                for task in provider.calls)
        )

    def test_proposal_rejection_returns_to_coder(self) -> None:
        provider = MockProvider()
        decisions = iter([
            (HumanDecision.REQUEST_CHANGES, "Split persistence from runtime state."),
            (HumanDecision.APPROVE, ""),
            (HumanDecision.APPROVE, ""),
        ])
        result = DevRoomOrchestrator(provider).run(
            "Implement vehicle ownership",
            human_gate=lambda stage, prompt, context: next(decisions),
        )
        self.assertEqual(result.stage, Stage.COMPLETE)
        self.assertEqual(
            [task.role for task in provider.calls],
            ["Lead", "Architect", "Coder", "Coder", "Implementer", "QA"],
        )
        self.assertEqual(
            provider.calls[3].context["revision_instruction"],
            "Split persistence from runtime state.",
        )

    def test_unity_failure_returns_to_coder(self) -> None:
        provider = MockProvider()
        decisions = iter([
            (HumanDecision.APPROVE, ""),
            (HumanDecision.REQUEST_CHANGES, "The vehicle is not persisted after restart."),
            (HumanDecision.APPROVE, ""),
            (HumanDecision.APPROVE, ""),
        ])
        result = DevRoomOrchestrator(provider).run(
            "Implement persistent vehicle ownership",
            human_gate=lambda stage, prompt, context: next(decisions),
        )
        self.assertEqual(result.stage, Stage.COMPLETE)
        self.assertEqual(
            [task.role for task in provider.calls],
            [
                "Lead", "Architect", "Coder", "Implementer", "QA",
                "Coder", "Implementer", "QA",
            ],
        )
        self.assertEqual(
            provider.calls[5].context["revision_instruction"],
            "The vehicle is not persisted after restart.",
        )

    def test_empty_coder_halts_before_review(self) -> None:
        class EmptyCoder(MockProvider):
            def execute(self, task):
                self.calls.append(task)
                if task.role == "Coder":
                    return AgentResult(role=task.role, summary="No proposal.")
                return super().execute(task)

        result = DevRoomOrchestrator(EmptyCoder()).run("Build a feature")
        self.assertEqual(result.stage, Stage.HALTED)
        self.assertIn("reviewable implementation proposal", result.halted_reason or "")

    def test_empty_implementer_halts_before_qa(self) -> None:
        class EmptyImplementer(MockProvider):
            def execute(self, task):
                if task.role == "Implementer":
                    self.calls.append(task)
                    return AgentResult(role=task.role, summary="No integration.")
                return super().execute(task)

        provider = EmptyImplementer()
        result = DevRoomOrchestrator(provider).run(
            "Build a feature",
            human_gate=self.approve_all,
        )
        self.assertEqual(result.stage, Stage.HALTED)
        self.assertIn("integration artifacts", result.halted_reason or "")
        self.assertEqual(
            [task.role for task in provider.calls],
            ["Lead", "Architect", "Coder", "Implementer"],
        )

    def test_human_halt_stops_workflow(self) -> None:
        provider = MockProvider()
        result = DevRoomOrchestrator(provider).run(
            "Build a feature",
            human_gate=lambda stage, prompt, context: (
                HumanDecision.HALT,
                "Stop this task.",
            ),
        )
        self.assertEqual(result.stage, Stage.HALTED)
        self.assertIn(Stage.HUMAN_REVIEW, result.history)
        self.assertNotIn(Stage.IMPLEMENTER, result.history)

    def test_persists_final_workflow_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workflow.json"
            writer = WorkflowStateWriter(JsonWorkflowStateStore(path), "workflow-1")
            result = DevRoomOrchestrator(
                MockProvider(),
                state_writer=writer,
            ).run("Persist this workflow", human_gate=self.approve_all)

            persisted = JsonWorkflowStateStore(path).load("workflow-1")
            self.assertEqual(result.stage.value, persisted.stage)
            self.assertEqual(
                tuple(stage.value for stage in result.history),
                persisted.history,
            )
            self.assertEqual(len(result.results), len(persisted.results))
            self.assertIsNone(persisted.halted_reason)

    def test_resume_replays_completed_work_and_reopens_pending_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workflow.json"
            writer = WorkflowStateWriter(JsonWorkflowStateStore(path), "resume-test")

            def interrupting_gate(stage, prompt, context):
                raise RuntimeError("simulated process interruption")

            first_provider = MockProvider()
            with self.assertRaisesRegex(RuntimeError, "simulated process interruption"):
                DevRoomOrchestrator(first_provider, state_writer=writer).run(
                    "Resume this workflow",
                    workspace=r"D:\\DEV_ROOM_TEST",
                    allowed_paths=("Assets/Test.cs",),
                    human_gate=interrupting_gate,
                    max_feedback_cycles=2,
                )

            persisted = JsonWorkflowStateStore(path).load("resume-test")
            self.assertEqual(persisted.stage, Stage.HUMAN_REVIEW.value)
            self.assertIsNone(persisted.last_decision)
            self.assertEqual([item["role"] for item in persisted.results], ["Lead", "Architect", "Coder"])

            resumed_provider = MockProvider()
            decisions = iter([
                (HumanDecision.APPROVE, ""),
                (HumanDecision.APPROVE, ""),
            ])
            result = DevRoomOrchestrator(resumed_provider, state_writer=writer).run(
                "Resume this workflow",
                workspace=r"D:\\DEV_ROOM_TEST",
                allowed_paths=("Assets/Test.cs",),
                human_gate=lambda stage, prompt, context: next(decisions),
                max_feedback_cycles=2,
                resume_state=persisted,
            )

            self.assertEqual(result.stage, Stage.COMPLETE)
            self.assertEqual([task.role for task in resumed_provider.calls], ["Implementer", "QA"])
            self.assertEqual(
                [stage.value for stage in result.history],
                ["lead", "architect", "coder", "human_review", "implementer", "qa", "unity_validation", "complete"],
            )

    def test_resume_rejects_interrupted_agent_execution(self) -> None:
        from devroom.state_store import PersistedWorkflow

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workflow.json"
            store = JsonWorkflowStateStore(path)
            store.save(PersistedWorkflow(
                workflow_id="interrupted",
                stage=Stage.IMPLEMENTER.value,
                history=("lead", "architect", "coder", "human_review", "implementer"),
                results=(),
                goal="Interrupted implementation",
                in_flight_role="Implementer",
            ))
            persisted = store.load("interrupted")
            with self.assertRaisesRegex(ValueError, "interrupted Implementer execution"):
                DevRoomOrchestrator(MockProvider()).run(
                    "Interrupted implementation",
                    workspace=r"D:\\DEV_ROOM_TEST",
                    allowed_paths=("Assets/Test.cs",),
                    human_gate=self.approve_all,
                    resume_state=persisted,
                )

    def test_agent_failure_persists_halt_and_releases_guard(self) -> None:
        class FailingProvider(MockProvider):
            def execute(self, task):
                self.calls.append(task)
                if task.role == "Architect":
                    raise RuntimeError("model unavailable")
                return super().execute(task)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "workflow.json"
            writer = WorkflowStateWriter(JsonWorkflowStateStore(path), "workflow-failure")
            result = None
            with self.assertRaisesRegex(RuntimeError, "model unavailable"):
                DevRoomOrchestrator(
                    FailingProvider(),
                    state_writer=writer,
                ).run("Fail safely")

            persisted = JsonWorkflowStateStore(path).load("workflow-failure")
            self.assertEqual(persisted.stage, Stage.HALTED.value)
            self.assertIn("Architect execution failed", persisted.halted_reason or "")

    def test_resource_guard_cools_down_after_continuous_limit(self) -> None:
        now = [0.0]
        sleeps = []
        def clock(): return now[0]
        def sleeper(seconds):
            sleeps.append(seconds)
            now[0] += seconds
        guard = ResourceGuard(cooldown_after_seconds=60.0, cooldown_seconds=45.0, clock=clock, sleeper=sleeper)
        guard.before_agent()
        now[0] = 59.0
        self.assertFalse(guard.after_agent())
        now[0] = 60.0
        self.assertTrue(guard.after_agent())
        self.assertEqual(sleeps, [45.0])
        self.assertFalse(guard.after_agent())
    def test_blank_goal_workspace_and_scope_are_rejected(self) -> None:
        provider = MockProvider()
        with self.assertRaises(ValueError):
            DevRoomOrchestrator(provider).run("  ")
        with self.assertRaises(ValueError):
            DevRoomOrchestrator(provider).run("Goal", workspace="  ")
        with self.assertRaises(ValueError):
            DevRoomOrchestrator(provider).run("Goal", allowed_paths=("",))


if __name__ == "__main__":
    unittest.main()
