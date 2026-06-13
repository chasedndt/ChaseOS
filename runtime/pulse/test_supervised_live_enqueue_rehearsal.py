"""Tests for Pulse supervised live-enqueue rehearsal."""

from __future__ import annotations

import inspect
import shutil
import unittest
from pathlib import Path

import runtime.pulse.supervised_live_enqueue_rehearsal as rehearsal_module
from runtime.pulse.bus_enqueue_approval_request import (
    build_agent_bus_enqueue_approval_request,
    persist_agent_bus_enqueue_approval_request,
)
from runtime.pulse.bus_enqueue_design import build_agent_bus_enqueue_preflight
from runtime.pulse.bus_enqueue_evidence import create_agent_bus_enqueue_evidence_record
from runtime.pulse.bus_review_contract import build_agent_bus_review_request_contract
from runtime.pulse.candidate_inspector import PulseCandidateInspectorItem
from runtime.pulse.supervised_live_enqueue_rehearsal import (
    PULSE_SUPERVISED_REHEARSAL_STATUS_BLOCKED,
    PULSE_SUPERVISED_REHEARSAL_STATUS_READY,
    PulseSupervisedLiveEnqueueRehearsal,
    build_supervised_live_enqueue_rehearsal,
)


_TMP_ROOT = Path(__file__).resolve().parent / "_tmp_supervised_live_enqueue_rehearsal"


class PulseSupervisedLiveEnqueueRehearsalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = _TMP_ROOT / self._testMethodName[:48]
        self._clean_tmp_root()
        self.tmp_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._clean_tmp_root()

    def _clean_tmp_root(self) -> None:
        if self.tmp_root.exists():
            resolved = self.tmp_root.resolve()
            if resolved.parent.name != "_tmp_supervised_live_enqueue_rehearsal":
                raise AssertionError(f"refusing to remove unexpected path: {resolved}")
            shutil.rmtree(resolved, ignore_errors=True)
            try:
                resolved.parent.rmdir()
            except OSError:
                pass

    def _approval_request(self):
        item = PulseCandidateInspectorItem(
            item_id="candidate-supervised-rehearsal-001",
            item_kind="feedback_candidate",
            record_id="candidate-supervised-rehearsal-001",
            status="pending_review",
            title="Feedback candidate",
            candidate_kind="feedback",
            candidate_id="candidate-supervised-rehearsal-001",
            source_log_path="07_LOGS/Pulse-Decks/feedback-candidates/2026-05-01-feedback-candidates.jsonl",
            source_deck_path="07_LOGS/Pulse-Decks/users/2026-05-01-user-pulse.json",
            source_card_id="pulse-card-supervised-rehearsal-001",
            target_ref="pulse-card-supervised-rehearsal-001",
            created_at="2026-05-01T00:10:00+01:00",
        )
        review_contract = build_agent_bus_review_request_contract(
            item,
            requested_by="codex",
            created_at="2026-05-01T00:11:00+01:00",
        )
        preflight = build_agent_bus_enqueue_preflight(
            review_contract,
            requested_by="codex",
            created_at="2026-05-01T00:12:00+01:00",
        )
        return build_agent_bus_enqueue_approval_request(
            preflight,
            requested_by="codex",
            requested_at="2026-05-01T00:13:00+01:00",
        )

    def _persist_request(self):
        request = self._approval_request()
        persist_agent_bus_enqueue_approval_request(self.tmp_root, request)
        return request

    def _persist_full_evidence(self, request_id: str):
        record, _artifact = create_agent_bus_enqueue_evidence_record(
            self.tmp_root,
            request_id,
            reviewer="operator",
            operator_enqueue_approval_present=True,
            gate_policy_defined=True,
            external_sender_allowance_present=True,
            duplicate_work_fingerprint_reviewed=True,
            evidence_note="operator-approval-ref: pulse-rehearsal-test-approval",
            gate_policy_ref="gate-policy-ref: pulse-rehearsal-test-policy",
            external_sender_allowance_ref="allowance-ref: pulse-rehearsal-test-allowance",
            duplicate_review_ref="duplicate-review-ref: pulse-rehearsal-test-duplicate-review",
            created_at="2026-05-01T00:14:00+01:00",
        )
        return record

    def test_module_does_not_import_agent_bus_writer(self) -> None:
        source = inspect.getsource(rehearsal_module)
        forbidden_tokens = (
            "create_task",
            "update_task_status",
            "claim_task",
            "enqueue_pulse_review_task",
            "persist_agent_bus_enqueue",
            "write_text",
            "open(",
        )
        for token in forbidden_tokens:
            with self.subTest(token=token):
                self.assertNotIn(token, source)

    def test_ready_rehearsal_exposes_manual_command_without_writes(self) -> None:
        request = self._persist_request()
        evidence = self._persist_full_evidence(request.request_id)
        before = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        rehearsal = build_supervised_live_enqueue_rehearsal(
            self.tmp_root,
            request.request_id,
            evidence_id=evidence.evidence_id,
            generated_at="2026-05-01T00:15:00+01:00",
            bus_tasks=[],
        )
        after = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        self.assertEqual(before, after)
        self.assertEqual(rehearsal.rehearsal_status, PULSE_SUPERVISED_REHEARSAL_STATUS_READY)
        self.assertTrue(rehearsal.ready_for_manual_enqueue)
        self.assertIn("enqueue-candidate", rehearsal.manual_command_preview)
        self.assertIn(evidence.evidence_id, rehearsal.manual_command_preview)
        self.assertFalse(rehearsal.live_enqueue_executed)
        self.assertFalse(rehearsal.agent_bus_task_written)
        self.assertFalse(rehearsal.candidate_apply_allowed)
        self.assertFalse(rehearsal.canonical_writeback_allowed)

    def test_blocked_rehearsal_hides_manual_command(self) -> None:
        request = self._persist_request()

        rehearsal = build_supervised_live_enqueue_rehearsal(
            self.tmp_root,
            request.request_id,
            generated_at="2026-05-01T00:16:00+01:00",
            bus_tasks=[],
        )

        self.assertEqual(rehearsal.rehearsal_status, PULSE_SUPERVISED_REHEARSAL_STATUS_BLOCKED)
        self.assertFalse(rehearsal.ready_for_manual_enqueue)
        self.assertEqual(rehearsal.manual_command_preview, ())
        self.assertIn("no_persisted_evidence_record", rehearsal.blocked_reasons)

    def test_rejects_execution_authority_flags(self) -> None:
        request = self._persist_request()
        evidence = self._persist_full_evidence(request.request_id)
        rehearsal = build_supervised_live_enqueue_rehearsal(
            self.tmp_root,
            request.request_id,
            evidence_id=evidence.evidence_id,
            generated_at="2026-05-01T00:17:00+01:00",
            bus_tasks=[],
        )

        for flag in (
            "persisted_rehearsal",
            "live_enqueue_executed",
            "approval_granted",
            "approval_executed",
            "gate_policy_mutated",
            "agent_bus_task_written",
            "runtime_dispatch_allowed",
            "review_response_ingest_allowed",
            "candidate_apply_allowed",
            "canonical_writeback_allowed",
            "mutates_canonical_state",
            "second_datastore_write_allowed",
            "provider_or_connector_call_allowed",
            "schedule_activation_allowed",
        ):
            with self.subTest(flag=flag):
                with self.assertRaises(ValueError):
                    PulseSupervisedLiveEnqueueRehearsal(
                        rehearsal_id=rehearsal.rehearsal_id,
                        request_id=rehearsal.request_id,
                        generated_at=rehearsal.generated_at,
                        rehearsal_status=rehearsal.rehearsal_status,
                        operator_gate_contract=rehearsal.operator_gate_contract,
                        evidence_id=rehearsal.evidence_id,
                        manual_command_preview=rehearsal.manual_command_preview,
                        required_operator_steps=rehearsal.required_operator_steps,
                        **{flag: True},
                    ).validate()


if __name__ == "__main__":
    unittest.main()
