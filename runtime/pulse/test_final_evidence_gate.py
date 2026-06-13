"""Tests for the read-only Pulse final evidence gate."""

from __future__ import annotations

import inspect
import json
import shutil
import unittest
from pathlib import Path

import runtime.pulse.final_evidence_gate as gate_module
from runtime.pulse.bus_enqueue_evidence import (
    create_agent_bus_enqueue_evidence_record,
)
from runtime.pulse.final_evidence_gate import (
    PULSE_FINAL_GATE_STATUS_BLOCKED,
    PULSE_FINAL_GATE_STATUS_READY,
    PulseFinalEvidenceGateStatus,
    build_pulse_final_evidence_gate_status,
)
from runtime.pulse.real_approval_artifact_rehearsal import (
    run_real_approval_artifact_rehearsal,
)


_TMP_ROOT = Path(__file__).resolve().parent / "_tmp_final_evidence_gate"


class PulseFinalEvidenceGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = _TMP_ROOT / self._testMethodName[:48]
        self._clean_tmp_root()
        self.tmp_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._clean_tmp_root()

    def _clean_tmp_root(self) -> None:
        if self.tmp_root.exists():
            resolved = self.tmp_root.resolve()
            if resolved.parent.name != "_tmp_final_evidence_gate":
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
            / "2026-05-02-user-pulse.json"
        )
        deck_path.parent.mkdir(parents=True, exist_ok=True)
        deck_path.write_text(
            json.dumps(
                {
                    "deck_id": "pulse-deck-final-gate-test",
                    "audience": "user",
                    "cards": [
                        {
                            "card_id": "pulse-card-final-gate-001",
                            "title": "Final gate card",
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
            generated_at="2026-05-02T02:20:00+01:00",
        )
        return rehearsal.approval_request_artifact.request_id

    def test_module_does_not_import_writer_or_live_execution_functions(self) -> None:
        source = inspect.getsource(gate_module)
        forbidden_tokens = (
            "create_task",
            "enqueue_pulse_review_task",
            "persist_agent_bus_enqueue_evidence_record",
            "persist_review_decision",
            "apply_reviewed_candidates",
        )
        for token in forbidden_tokens:
            with self.subTest(token=token):
                self.assertNotIn(token, source)

    def test_blocked_gate_is_read_only_and_names_operator_slots(self) -> None:
        request_id = self._request_id()
        before = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        gate = build_pulse_final_evidence_gate_status(
            self.tmp_root,
            request_id,
            generated_at="2026-05-02T02:21:00+01:00",
            bus_tasks=[],
        )
        after = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        self.assertEqual(before, after)
        self.assertEqual(gate.gate_status, PULSE_FINAL_GATE_STATUS_BLOCKED)
        self.assertFalse(gate.ready_for_live_enqueue)
        self.assertTrue(gate.operator_action_required)
        self.assertFalse(gate.can_runtime_self_satisfy_remaining)
        self.assertEqual(gate.closure_status, "blocked_by_external_authority")
        self.assertEqual(
            gate.closure_authority_classes,
            ("operator_decision", "gate_policy", "external_sender_policy"),
        )
        self.assertEqual(gate.closure_runtime_action_keys, ("duplicate_work_fingerprint_review",))
        self.assertEqual(
            set(gate.missing_approvals),
            {
                "operator_enqueue_approval",
                "gate_policy_defined",
                "external_sender_allowance",
                "duplicate_work_fingerprint_review",
            },
        )
        slots_by_key = {
            slot["approval_key"]: slot for slot in gate.missing_operator_action_slots
        }
        self.assertFalse(slots_by_key["operator_enqueue_approval"]["runtime_self_satisfiable"])
        self.assertEqual(slots_by_key["gate_policy_defined"]["authority_class"], "gate_policy")
        self.assertIn(request_id, slots_by_key["external_sender_allowance"]["capture_command"])
        self.assertEqual(
            tuple(slot["approval_key"] for slot in gate.missing_authority_action_slots),
            (
                "operator_enqueue_approval",
                "gate_policy_defined",
                "external_sender_allowance",
            ),
        )
        self.assertEqual(
            tuple(slot["approval_key"] for slot in gate.missing_runtime_self_satisfiable_slots),
            ("duplicate_work_fingerprint_review",),
        )
        payload = gate.to_dict()
        self.assertEqual(
            [slot["approval_key"] for slot in payload["missing_authority_action_slots"]],
            [
                "operator_enqueue_approval",
                "gate_policy_defined",
                "external_sender_allowance",
            ],
        )
        self.assertEqual(
            [slot["approval_key"] for slot in payload["missing_runtime_self_satisfiable_slots"]],
            ["duplicate_work_fingerprint_review"],
        )
        self.assertFalse(gate.agent_bus_task_written)
        self.assertFalse(gate.evidence_write_allowed)
        self.assertFalse(gate.canonical_writeback_allowed)
        self.assertFalse(gate.rd_workbook_update_allowed)
        self.assertEqual(gate.supervised_live_command_preview, ())

    def test_ready_gate_exposes_command_preview_only_after_full_evidence(self) -> None:
        request_id = self._request_id()
        record, _artifact = create_agent_bus_enqueue_evidence_record(
            self.tmp_root,
            request_id,
            operator_enqueue_approval_present=True,
            gate_policy_defined=True,
            external_sender_allowance_present=True,
            duplicate_work_fingerprint_reviewed=True,
            evidence_note="operator-approval-ref: pulse-test-approval",
            gate_policy_ref="gate-policy-ref: pulse-test-policy",
            external_sender_allowance_ref="allowance-ref: pulse-test-allowance",
            duplicate_review_ref="duplicate-review-ref: pulse-test-duplicate-review",
            created_at="2026-05-02T02:22:00+01:00",
        )

        gate = build_pulse_final_evidence_gate_status(
            self.tmp_root,
            request_id,
            evidence_id=record.evidence_id,
            generated_at="2026-05-02T02:23:00+01:00",
            bus_tasks=[],
        )

        self.assertEqual(gate.gate_status, PULSE_FINAL_GATE_STATUS_READY)
        self.assertTrue(gate.ready_for_operator_gate_decision)
        self.assertTrue(gate.ready_for_manual_enqueue)
        self.assertTrue(gate.ready_for_live_enqueue)
        self.assertFalse(gate.operator_action_required)
        self.assertEqual(gate.closure_status, "ready_for_supervised_live_enqueue")
        self.assertEqual(gate.closure_authority_classes, ())
        self.assertEqual(gate.closure_runtime_action_keys, ())
        self.assertEqual(gate.missing_approvals, ())
        self.assertEqual(gate.missing_operator_action_slots, ())
        self.assertTrue(gate.supervised_live_command_preview)
        self.assertIn("no_live_pulse_review_enqueue", gate.final_feature_blockers)
        self.assertFalse(gate.live_enqueue_executed)

    def test_runtime_self_satisfiable_duplicate_gap_is_not_operator_approval(self) -> None:
        request_id = self._request_id()
        record, _artifact = create_agent_bus_enqueue_evidence_record(
            self.tmp_root,
            request_id,
            operator_enqueue_approval_present=True,
            gate_policy_defined=True,
            external_sender_allowance_present=True,
            evidence_note="operator-approval-ref: pulse-test-approval",
            gate_policy_ref="gate-policy-ref: pulse-test-policy",
            external_sender_allowance_ref="allowance-ref: pulse-test-allowance",
            created_at="2026-05-02T02:24:00+01:00",
        )

        gate = build_pulse_final_evidence_gate_status(
            self.tmp_root,
            request_id,
            evidence_id=record.evidence_id,
            generated_at="2026-05-02T02:25:00+01:00",
            bus_tasks=[],
        )

        self.assertEqual(gate.gate_status, PULSE_FINAL_GATE_STATUS_BLOCKED)
        self.assertFalse(gate.operator_action_required)
        self.assertTrue(gate.can_runtime_self_satisfy_remaining)
        self.assertEqual(gate.closure_status, "runtime_self_satisfiable_evidence_missing")
        self.assertEqual(gate.closure_authority_classes, ())
        self.assertEqual(gate.closure_runtime_action_keys, ("duplicate_work_fingerprint_review",))
        self.assertEqual(gate.missing_approvals, ("duplicate_work_fingerprint_review",))
        self.assertEqual(gate.missing_authority_action_slots, ())
        self.assertEqual(
            tuple(slot["approval_key"] for slot in gate.missing_runtime_self_satisfiable_slots),
            ("duplicate_work_fingerprint_review",),
        )

    def test_active_duplicate_blocks_closure_after_full_evidence(self) -> None:
        request_id = self._request_id()
        record, _artifact = create_agent_bus_enqueue_evidence_record(
            self.tmp_root,
            request_id,
            operator_enqueue_approval_present=True,
            gate_policy_defined=True,
            external_sender_allowance_present=True,
            duplicate_work_fingerprint_reviewed=True,
            evidence_note="operator-approval-ref: pulse-test-approval",
            gate_policy_ref="gate-policy-ref: pulse-test-policy",
            external_sender_allowance_ref="allowance-ref: pulse-test-allowance",
            duplicate_review_ref="duplicate-review-ref: pulse-test-duplicate-review",
            created_at="2026-05-02T02:24:00+01:00",
        )

        initial_gate = build_pulse_final_evidence_gate_status(
            self.tmp_root,
            request_id,
            evidence_id=record.evidence_id,
            generated_at="2026-05-02T02:24:30+01:00",
            bus_tasks=[],
        )
        gate = build_pulse_final_evidence_gate_status(
            self.tmp_root,
            request_id,
            evidence_id=record.evidence_id,
            generated_at="2026-05-02T02:25:00+01:00",
            bus_tasks=[
                {
                    "task_id": "task-duplicate",
                    "recipient": initial_gate.recipient,
                    "intent": "REVIEW",
                    "status": "review",
                    "work_fingerprint": initial_gate.work_fingerprint,
                }
            ],
        )

        self.assertEqual(gate.gate_status, PULSE_FINAL_GATE_STATUS_BLOCKED)
        self.assertEqual(gate.missing_approvals, ())
        self.assertEqual(gate.closure_status, "blocked_by_active_duplicate")
        self.assertEqual(gate.closure_authority_classes, ())
        self.assertEqual(gate.closure_runtime_action_keys, ("active_duplicate_work_fingerprint",))
        self.assertFalse(gate.ready_for_live_enqueue)
        self.assertFalse(gate.supervised_live_command_preview)

    def test_rejects_authority_flags(self) -> None:
        request_id = self._request_id()
        gate = build_pulse_final_evidence_gate_status(
            self.tmp_root,
            request_id,
            generated_at="2026-05-02T02:26:00+01:00",
            bus_tasks=[],
        )
        base = gate.to_dict()
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
            payload = dict(base)
            payload[flag] = True
            with self.subTest(flag=flag):
                with self.assertRaises(ValueError):
                    PulseFinalEvidenceGateStatus(**payload).validate()


if __name__ == "__main__":
    unittest.main()
