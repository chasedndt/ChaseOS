"""Tests for read-only Pulse approval readiness summary."""

from __future__ import annotations

import inspect
import json
import shutil
import unittest
from pathlib import Path

import runtime.pulse.approval_readiness_summary as summary_module
from runtime.pulse.approval_readiness_summary import (
    build_pulse_approval_readiness_summary,
)
from runtime.pulse.bus_enqueue_evidence import (
    create_agent_bus_enqueue_evidence_record,
)
from runtime.pulse.real_approval_artifact_rehearsal import (
    run_real_approval_artifact_rehearsal,
)


_TMP_ROOT = Path(__file__).resolve().parent / "_tmp_approval_readiness"


class PulseApprovalReadinessSummaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = _TMP_ROOT / self._testMethodName[:48]
        self._clean_tmp_root()
        self.tmp_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._clean_tmp_root()

    def _clean_tmp_root(self) -> None:
        if self.tmp_root.exists():
            resolved = self.tmp_root.resolve()
            if resolved.parent.name != "_tmp_approval_readiness":
                raise AssertionError(f"refusing to remove unexpected path: {resolved}")
            shutil.rmtree(resolved, ignore_errors=True)
            try:
                resolved.parent.rmdir()
            except OSError:
                pass

    def _write_user_deck(self) -> None:
        deck_path = (
            self.tmp_root
            / "07_LOGS"
            / "Pulse-Decks"
            / "users"
            / "2026-05-01-user-pulse.json"
        )
        deck_path.parent.mkdir(parents=True, exist_ok=True)
        deck_path.write_text(
            json.dumps(
                {
                    "deck_id": "pulse-deck-readiness-test",
                    "audience": "user",
                    "cards": [
                        {
                            "card_id": "pulse-card-readiness-001",
                            "title": "Readiness card",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    def _request_id(self) -> str:
        self._write_user_deck()
        rehearsal = run_real_approval_artifact_rehearsal(
            self.tmp_root,
            generated_at="2026-05-01T22:10:00+01:00",
        )
        return rehearsal.approval_request_artifact.request_id

    def test_module_does_not_import_writer_or_apply_functions(self) -> None:
        source = inspect.getsource(summary_module)
        forbidden_tokens = (
            "create_task",
            "enqueue_pulse_review_task",
            "persist_review_decision",
            "apply_reviewed_candidates",
            "persist_agent_bus_enqueue_evidence_record",
        )
        for token in forbidden_tokens:
            with self.subTest(token=token):
                self.assertNotIn(token, source)

    def test_blocked_summary_is_read_only_and_lists_missing_evidence(self) -> None:
        request_id = self._request_id()
        before = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        summary = build_pulse_approval_readiness_summary(
            self.tmp_root,
            request_id,
            generated_at="2026-05-01T22:11:00+01:00",
            bus_tasks=[],
        )
        after = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        self.assertEqual(before, after)
        self.assertEqual(summary.readiness_status, "blocked_missing_required_evidence")
        self.assertFalse(summary.ready_for_manual_enqueue)
        self.assertEqual(summary.supervised_live_command_preview, ())
        self.assertIn("operator_enqueue_approval", summary.missing_approvals)
        self.assertTrue(summary.evidence_capture_command_hints)
        slots_by_key = {slot["approval_key"]: slot for slot in summary.approval_evidence_slots}
        self.assertEqual(
            set(slots_by_key),
            {
                "operator_enqueue_approval",
                "gate_policy_defined",
                "external_sender_allowance",
                "duplicate_work_fingerprint_review",
            },
        )
        self.assertFalse(slots_by_key["operator_enqueue_approval"]["satisfied"])
        self.assertEqual(
            slots_by_key["operator_enqueue_approval"]["required_ref"],
            "operator-approval-ref",
        )
        self.assertEqual(
            slots_by_key["operator_enqueue_approval"]["ref_placeholder"],
            "<operator-approval-ref>",
        )
        self.assertTrue(slots_by_key["operator_enqueue_approval"]["requires_real_ref"])
        self.assertTrue(
            slots_by_key["operator_enqueue_approval"]["placeholder_ref_rejected"]
        )
        self.assertEqual(
            slots_by_key["operator_enqueue_approval"]["authority_class"],
            "operator_decision",
        )
        self.assertFalse(
            slots_by_key["operator_enqueue_approval"]["runtime_self_satisfiable"]
        )
        self.assertEqual(
            slots_by_key["gate_policy_defined"]["authority_class"],
            "gate_policy",
        )
        self.assertFalse(slots_by_key["gate_policy_defined"]["runtime_self_satisfiable"])
        self.assertEqual(
            slots_by_key["external_sender_allowance"]["authority_class"],
            "external_sender_policy",
        )
        self.assertFalse(
            slots_by_key["external_sender_allowance"]["runtime_self_satisfiable"]
        )
        self.assertEqual(
            slots_by_key["duplicate_work_fingerprint_review"]["authority_class"],
            "queue_inspection",
        )
        self.assertTrue(
            slots_by_key["duplicate_work_fingerprint_review"]["runtime_self_satisfiable"]
        )
        self.assertIn(request_id, slots_by_key["gate_policy_defined"]["capture_command"])
        self.assertFalse(summary.agent_bus_task_written)
        self.assertFalse(summary.canonical_writeback_allowed)

    def test_ready_summary_marks_structured_evidence_slots_satisfied(self) -> None:
        request_id = self._request_id()
        record, _artifact = create_agent_bus_enqueue_evidence_record(
            self.tmp_root,
            request_id,
            operator_enqueue_approval_present=True,
            gate_policy_defined=True,
            external_sender_allowance_present=True,
            duplicate_work_fingerprint_reviewed=True,
            evidence_note="test-only full evidence",
            gate_policy_ref="test-gate-policy",
            external_sender_allowance_ref="test-allowance",
            duplicate_review_ref="test-duplicate-review",
            created_at="2026-05-01T22:12:00+01:00",
        )

        summary = build_pulse_approval_readiness_summary(
            self.tmp_root,
            request_id,
            evidence_id=record.evidence_id,
            generated_at="2026-05-01T22:12:30+01:00",
            bus_tasks=[],
        )

        slots_by_key = {slot["approval_key"]: slot for slot in summary.approval_evidence_slots}
        self.assertTrue(all(slot["satisfied"] for slot in slots_by_key.values()))
        self.assertEqual(slots_by_key["gate_policy_defined"]["ref"], "test-gate-policy")
        self.assertEqual(
            slots_by_key["external_sender_allowance"]["ref"], "test-allowance"
        )
        self.assertEqual(
            slots_by_key["duplicate_work_fingerprint_review"]["ref"],
            "test-duplicate-review",
        )
        self.assertFalse(summary.agent_bus_task_written)
        self.assertFalse(summary.live_enqueue_executed)

    def test_ready_summary_exposes_manual_command_preview_only_after_full_evidence(self) -> None:
        request_id = self._request_id()
        record, artifact = create_agent_bus_enqueue_evidence_record(
            self.tmp_root,
            request_id,
            operator_enqueue_approval_present=True,
            gate_policy_defined=True,
            external_sender_allowance_present=True,
            duplicate_work_fingerprint_reviewed=True,
            evidence_note="test-only full evidence",
            gate_policy_ref="test-gate-policy",
            external_sender_allowance_ref="test-allowance",
            duplicate_review_ref="test-duplicate-review",
            created_at="2026-05-01T22:12:00+01:00",
        )
        self.assertEqual(record.evidence_id, artifact.evidence_id)

        summary = build_pulse_approval_readiness_summary(
            self.tmp_root,
            request_id,
            evidence_id=record.evidence_id,
            generated_at="2026-05-01T22:13:00+01:00",
            bus_tasks=[],
        )

        self.assertEqual(summary.readiness_status, "ready_for_operator_approved_live_enqueue")
        self.assertTrue(summary.ready_for_operator_gate_decision)
        self.assertTrue(summary.ready_for_manual_enqueue)
        self.assertEqual(summary.missing_approvals, ())
        self.assertTrue(summary.supervised_live_command_preview)
        self.assertFalse(summary.agent_bus_task_written)
        self.assertFalse(summary.live_enqueue_executed)

    def test_rejects_authority_flags(self) -> None:
        request_id = self._request_id()
        summary = build_pulse_approval_readiness_summary(
            self.tmp_root,
            request_id,
            generated_at="2026-05-01T22:14:00+01:00",
            bus_tasks=[],
        )
        for flag in (
            "writes_status_artifact",
            "evidence_write_allowed",
            "approval_granted",
            "live_enqueue_executed",
            "agent_bus_task_written",
            "runtime_dispatch_allowed",
            "review_response_ingest_allowed",
            "candidate_apply_allowed",
            "canonical_writeback_allowed",
            "mutates_canonical_state",
            "provider_or_connector_call_allowed",
            "schedule_activation_allowed",
            "rd_workbook_update_allowed",
        ):
            with self.subTest(flag=flag):
                with self.assertRaises(ValueError):
                    type(summary)(
                        generated_at=summary.generated_at,
                        request_id=summary.request_id,
                        readiness_status=summary.readiness_status,
                        feature_done=summary.feature_done,
                        backend_control_plane_done=summary.backend_control_plane_done,
                        completion_status=summary.completion_status,
                        next_recommended_pass=summary.next_recommended_pass,
                        candidate_id=summary.candidate_id,
                        candidate_kind=summary.candidate_kind,
                        recipient=summary.recipient,
                        work_fingerprint=summary.work_fingerprint,
                        evidence_id=summary.evidence_id,
                        ready_for_operator_gate_decision=summary.ready_for_operator_gate_decision,
                        ready_for_manual_enqueue=summary.ready_for_manual_enqueue,
                        handoff_status=summary.handoff_status,
                        validation_status=summary.validation_status,
                        satisfied_approvals=summary.satisfied_approvals,
                        missing_approvals=summary.missing_approvals,
                        duplicate_found=summary.duplicate_found,
                        active_duplicate_task_ids=summary.active_duplicate_task_ids,
                        target_bus_snapshot_status=summary.target_bus_snapshot_status,
                        target_active_task_count=summary.target_active_task_count,
                        target_review_task_count=summary.target_review_task_count,
                        blocked_reasons=summary.blocked_reasons,
                        readiness_reasons=summary.readiness_reasons,
                        required_operator_steps=summary.required_operator_steps,
                        evidence_capture_command_hints=summary.evidence_capture_command_hints,
                        approval_evidence_slots=summary.approval_evidence_slots,
                        **{flag: True},
                    ).validate()


if __name__ == "__main__":
    unittest.main()
