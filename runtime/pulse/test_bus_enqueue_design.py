"""Tests for design-only Pulse Agent Bus enqueue preflights."""

from __future__ import annotations

import inspect
import shutil
import unittest
from pathlib import Path

import runtime.pulse.bus_enqueue_design as enqueue_module
from runtime.agents.execution_repair_memory import ExecutionRepairMemoryEntry, RepairPattern
from runtime.agents.repair_candidate_store import (
    build_execution_repair_memory_candidate,
    persist_execution_repair_memory_candidate,
)
from runtime.pulse.bus_enqueue_design import (
    PULSE_BUS_ALLOWED_REVIEW_RECIPIENTS,
    PULSE_BUS_ENQUEUE_BLOCKED_EFFECTS,
    PulseAgentBusEnqueueDesign,
    PulseAgentBusEnqueuePreflight,
    build_agent_bus_enqueue_plan,
    build_agent_bus_enqueue_preflight,
    build_agent_bus_enqueue_preflight_for_candidate,
)
from runtime.pulse.bus_review_contract import build_agent_bus_review_request_contract
from runtime.pulse.candidate_inspector import PulseCandidateInspectorItem
from runtime.pulse.feedback import PulseFeedbackRecord, load_feedback_candidates, persist_feedback_candidate


_TMP_ROOT = Path(__file__).resolve().parent / "_tmp_bus_enqueue_design"


class PulseAgentBusEnqueueDesignTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = _TMP_ROOT
        self._clean_tmp_root()
        self.tmp_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._clean_tmp_root()

    def _clean_tmp_root(self) -> None:
        if self.tmp_root.exists():
            resolved = self.tmp_root.resolve()
            if resolved.name != "_tmp_bus_enqueue_design":
                raise AssertionError(f"refusing to remove unexpected path: {resolved}")
            shutil.rmtree(resolved)

    def _seed_feedback_candidate(self):
        deck_path = self.tmp_root / "07_LOGS" / "Pulse-Decks" / "users" / "2026-04-30-user-pulse.json"
        deck_path.parent.mkdir(parents=True, exist_ok=True)
        deck_path.write_text('{"deck_id": "pulse-deck-test", "cards": []}', encoding="utf-8")
        artifact = persist_feedback_candidate(
            self.tmp_root,
            PulseFeedbackRecord(
                feedback_id="feedback-enqueue-001",
                card_id="pulse-card-enqueue-001",
                feedback_type="show_more_like_this",
                operator_note="Surface runtime blockers more often.",
                created_at="2026-04-30T09:45:00+01:00",
            ),
            source_deck_path=deck_path,
        )
        candidate = load_feedback_candidates(self.tmp_root)[0]
        return candidate, artifact

    def _seed_repair_candidate(self):
        entry = ExecutionRepairMemoryEntry(
            repair_id="repair-openflow-enqueue-001",
            runtime_id="openflow",
            workflow_id="shopify_upload",
            failure_surface="browser",
            failure_type="missing_product_assets",
            failure_summary="Upload could not continue without product images.",
            resolution_summary="Runtime stopped and requested manual input.",
            repair_pattern=RepairPattern(
                trigger="missing product images",
                workaround="request image batch before upload",
                recommended_response=["create Manual Input Needed card"],
                future_prevention=["add product image preflight check"],
            ),
            source_logs=["07_LOGS/Agent-Activity/openflow/enqueue-example.md"],
        )
        candidate = build_execution_repair_memory_candidate(
            entry,
            reason="Reusable execution repair pattern.",
            source_card_id="pulse-agent-card-enqueue-001",
            source_deck_path="07_LOGS/Pulse-Decks/users/2026-04-30-user-pulse.json",
            created_at="2026-04-30T09:46:00+01:00",
        )
        artifact = persist_execution_repair_memory_candidate(self.tmp_root, candidate)
        return candidate, artifact

    def _review_contract(self, *, recipient: str = "Hermes"):
        item = PulseCandidateInspectorItem(
            item_id="candidate-enqueue-001",
            item_kind="feedback_candidate",
            record_id="candidate-enqueue-001",
            status="pending_review",
            title="Feedback candidate",
            candidate_kind="feedback",
            candidate_id="candidate-enqueue-001",
            source_log_path="07_LOGS/Pulse-Decks/feedback-candidates/2026-04-30-feedback-candidates.jsonl",
            source_deck_path="07_LOGS/Pulse-Decks/users/2026-04-30-user-pulse.json",
            source_card_id="pulse-card-enqueue-001",
            target_ref="pulse-card-enqueue-001",
            created_at="2026-04-30T09:45:00+01:00",
        )
        return build_agent_bus_review_request_contract(
            item,
            recipient=recipient,
            requested_by="codex",
            created_at="2026-04-30T09:50:00+01:00",
        )

    def test_module_does_not_import_agent_bus_writer_or_backend(self) -> None:
        source = inspect.getsource(enqueue_module)

        forbidden_tokens = (
            "runtime.agent_bus.bus",
            "create_task",
            "init_db",
            "get_backend",
            "update_task_status",
            "claim_task",
        )
        for token in forbidden_tokens:
            with self.subTest(token=token):
                self.assertNotIn(token, source)

    def test_static_design_is_denied_by_default(self) -> None:
        design = PulseAgentBusEnqueueDesign()
        payload = design.to_dict()

        self.assertEqual(payload["design_status"], "design_only")
        self.assertEqual(tuple(payload["allowed_review_recipients"]), PULSE_BUS_ALLOWED_REVIEW_RECIPIENTS)
        self.assertFalse(payload["allowed"])
        self.assertTrue(payload["approval_required"])
        self.assertFalse(payload["live_enqueue_allowed"])
        self.assertFalse(payload["agent_bus_write_allowed"])
        self.assertFalse(payload["approval_request_write_allowed"])
        self.assertFalse(payload["candidate_apply_allowed"])
        self.assertFalse(payload["review_response_ingest_allowed"])
        self.assertFalse(payload["canonical_writeback_allowed"])
        self.assertEqual(set(payload["blocked_effects"]), set(PULSE_BUS_ENQUEUE_BLOCKED_EFFECTS))

    def test_preflight_from_review_contract_is_ready_but_non_enqueueing(self) -> None:
        contract = self._review_contract()

        preflight = build_agent_bus_enqueue_preflight(
            contract,
            requested_by="codex",
            created_at="2026-04-30T09:55:00+01:00",
        )
        task_payload = preflight.to_task_payload_preview()

        self.assertEqual(preflight.preflight_status, "ready_for_operator_approval")
        self.assertEqual(preflight.contract_id, contract.contract_id)
        self.assertEqual(preflight.candidate_id, "candidate-enqueue-001")
        self.assertEqual(preflight.intent, "REVIEW")
        self.assertEqual(preflight.sender, "Operator")
        self.assertEqual(preflight.recipient, "Hermes")
        self.assertTrue(preflight.allow_external_sender_required)
        self.assertFalse(preflight.duplicate_check_performed)
        self.assertFalse(preflight.enqueue_allowed)
        self.assertFalse(preflight.agent_bus_task_written)
        self.assertFalse(preflight.approval_request_written)
        self.assertFalse(preflight.writes_performed)
        self.assertFalse(preflight.live_runtime_dispatch_allowed)
        self.assertFalse(preflight.candidate_apply_allowed)
        self.assertFalse(preflight.review_response_ingest_allowed)
        self.assertFalse(preflight.canonical_writeback_allowed)
        self.assertIn("operator approval", preflight.notes)
        self.assertEqual(task_payload["intent"], "REVIEW")
        self.assertFalse(task_payload["enqueue_allowed"])
        self.assertFalse(task_payload["agent_bus_task_written"])

    def test_preflight_for_candidate_is_read_only_and_creates_no_bus_state(self) -> None:
        candidate, artifact = self._seed_feedback_candidate()
        before = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        preflight = build_agent_bus_enqueue_preflight_for_candidate(
            self.tmp_root,
            candidate.candidate_id,
            requested_by="codex",
            created_at="2026-04-30T10:00:00+01:00",
        )
        after = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        self.assertEqual(before, after)
        self.assertEqual(preflight.candidate_id, candidate.candidate_id)
        self.assertEqual(preflight.source_log_path, artifact.path)
        self.assertFalse(preflight.enqueue_allowed)
        self.assertFalse(preflight.agent_bus_task_written)
        self.assertFalse((self.tmp_root / ".chaseos").exists())

    def test_enqueue_plan_wraps_queue_preview_without_persisting_queue_or_tasks(self) -> None:
        self._seed_feedback_candidate()
        self._seed_repair_candidate()
        before = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        plan = build_agent_bus_enqueue_plan(
            self.tmp_root,
            recipient_by_candidate_kind={"execution_repair": "OpenClaw"},
            requested_by="codex",
            created_at="2026-04-30T10:05:00+01:00",
        )
        after = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        self.assertEqual(before, after)
        self.assertEqual(plan.plan_status, "read_only")
        self.assertEqual(plan.preflight_count, 2)
        self.assertEqual(plan.counts_by_recipient, {"Hermes": 1, "OpenClaw": 1})
        self.assertEqual(len(plan.task_payload_previews), 2)
        self.assertEqual(plan.writes, [])
        self.assertFalse(plan.enqueue_allowed)
        self.assertFalse(plan.agent_bus_tasks_written)
        self.assertFalse(plan.approval_requests_written)
        self.assertFalse(plan.candidate_apply_allowed)
        self.assertFalse(plan.review_response_ingest_allowed)
        self.assertFalse(plan.canonical_writeback_allowed)
        self.assertFalse((self.tmp_root / ".chaseos").exists())

    def test_codex_is_not_default_pulse_review_recipient_for_enqueue_design(self) -> None:
        contract = self._review_contract(recipient="Codex")

        with self.assertRaises(ValueError):
            build_agent_bus_enqueue_preflight(
                contract,
                requested_by="codex",
                created_at="2026-04-30T10:10:00+01:00",
            )

    def test_forbidden_flags_are_rejected(self) -> None:
        preflight = build_agent_bus_enqueue_preflight(
            self._review_contract(),
            created_at="2026-04-30T10:15:00+01:00",
        )
        base = preflight.to_dict()
        base.pop("task_payload_preview")

        forbidden_true_flags = (
            "duplicate_check_performed",
            "enqueue_allowed",
            "agent_bus_task_written",
            "approval_request_written",
            "writes_performed",
            "live_runtime_dispatch_allowed",
            "candidate_apply_allowed",
            "review_response_ingest_allowed",
            "canonical_writeback_allowed",
            "mutates_canonical_state",
            "second_datastore_write_allowed",
            "provider_or_connector_call_allowed",
            "schedule_activation_allowed",
        )
        for flag in forbidden_true_flags:
            payload = dict(base)
            payload[flag] = True
            with self.subTest(flag=flag):
                with self.assertRaises(ValueError):
                    PulseAgentBusEnqueuePreflight(**payload).validate()

        payload = dict(base)
        payload["allow_external_sender_required"] = False
        with self.assertRaises(ValueError):
            PulseAgentBusEnqueuePreflight(**payload).validate()


if __name__ == "__main__":
    unittest.main()
