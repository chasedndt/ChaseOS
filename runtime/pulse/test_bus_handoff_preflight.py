"""Tests for non-live Pulse Agent Bus handoff preflight."""

from __future__ import annotations

import inspect
import shutil
import unittest
from pathlib import Path

import runtime.pulse.bus_handoff_preflight as preflight_module
from runtime.pulse.bus_enqueue_approval_request import (
    build_agent_bus_enqueue_approval_request,
    persist_agent_bus_enqueue_approval_request,
)
from runtime.pulse.bus_enqueue_design import build_agent_bus_enqueue_preflight
from runtime.pulse.bus_enqueue_evidence import create_agent_bus_enqueue_evidence_record
from runtime.pulse.bus_handoff_preflight import (
    PULSE_BUS_HANDOFF_PREFLIGHT_BLOCKED_EFFECTS,
    PULSE_BUS_HANDOFF_PREFLIGHT_STATUS_DUPLICATE,
    PULSE_BUS_HANDOFF_PREFLIGHT_STATUS_MISSING_EVIDENCE,
    PULSE_BUS_HANDOFF_PREFLIGHT_STATUS_READY,
    PulseAgentBusHandoffPreflight,
    build_agent_bus_handoff_preflight,
)
from runtime.pulse.bus_review_contract import build_agent_bus_review_request_contract
from runtime.pulse.candidate_inspector import PulseCandidateInspectorItem


_TMP_ROOT = Path(__file__).resolve().parent / "_tmp_bus_handoff_preflight"


class PulseAgentBusHandoffPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = _TMP_ROOT / self._testMethodName[:48]
        self._clean_tmp_root()
        self.tmp_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._clean_tmp_root()

    def _clean_tmp_root(self) -> None:
        if self.tmp_root.exists():
            resolved = self.tmp_root.resolve()
            if resolved.parent.name != "_tmp_bus_handoff_preflight":
                raise AssertionError(f"refusing to remove unexpected path: {resolved}")
            shutil.rmtree(resolved, ignore_errors=True)
            try:
                resolved.parent.rmdir()
            except OSError:
                pass

    def _approval_request(self):
        item = PulseCandidateInspectorItem(
            item_id="candidate-handoff-001",
            item_kind="feedback_candidate",
            record_id="candidate-handoff-001",
            status="pending_review",
            title="Feedback candidate",
            candidate_kind="feedback",
            candidate_id="candidate-handoff-001",
            source_log_path="07_LOGS/Pulse-Decks/feedback-candidates/2026-04-30-feedback-candidates.jsonl",
            source_deck_path="07_LOGS/Pulse-Decks/users/2026-04-30-user-pulse.json",
            source_card_id="pulse-card-handoff-001",
            target_ref="pulse-card-handoff-001",
            created_at="2026-04-30T20:00:00+01:00",
        )
        contract = build_agent_bus_review_request_contract(
            item,
            requested_by="codex",
            created_at="2026-04-30T20:01:00+01:00",
        )
        preflight = build_agent_bus_enqueue_preflight(
            contract,
            requested_by="codex",
            created_at="2026-04-30T20:02:00+01:00",
        )
        return build_agent_bus_enqueue_approval_request(
            preflight,
            requested_by="codex",
            requested_at="2026-04-30T20:03:00+01:00",
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
            evidence_note="operator-approval-ref: pulse-handoff-test-approval",
            gate_policy_ref="gate-policy-ref: pulse-handoff-test-policy",
            external_sender_allowance_ref="allowance-ref: pulse-handoff-test-allowance",
            duplicate_review_ref="duplicate-review-ref: pulse-handoff-test-duplicate-review",
            created_at="2026-04-30T20:04:00+01:00",
        )
        return record

    def test_module_does_not_import_agent_bus_writer_or_backend_mutators(self) -> None:
        source = inspect.getsource(preflight_module)
        forbidden_tokens = (
            "create_task",
            "init_db",
            "update_task_status",
            "claim_task",
            "reclaim_task",
            "cleanup_tasks",
        )
        for token in forbidden_tokens:
            with self.subTest(token=token):
                self.assertNotIn(token, source)

    def test_missing_evidence_blocks_without_writing(self) -> None:
        request = self._persist_request()
        before = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        result = build_agent_bus_handoff_preflight(
            self.tmp_root,
            request.request_id,
            checked_at="2026-04-30T20:05:00+01:00",
            bus_tasks=[],
        )
        after = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        self.assertEqual(before, after)
        self.assertEqual(result.handoff_status, PULSE_BUS_HANDOFF_PREFLIGHT_STATUS_MISSING_EVIDENCE)
        self.assertFalse(result.evidence_record_present)
        self.assertIn("no_persisted_evidence_record", result.blocked_reasons)
        self.assertFalse(result.live_agent_bus_handoff_allowed)
        self.assertFalse(result.agent_bus_task_written)

    def test_full_evidence_without_duplicate_is_ready_but_non_executing(self) -> None:
        request = self._persist_request()
        evidence = self._persist_full_evidence(request.request_id)

        result = build_agent_bus_handoff_preflight(
            self.tmp_root,
            request.request_id,
            evidence_id=evidence.evidence_id,
            checked_at="2026-04-30T20:06:00+01:00",
            bus_tasks=[],
        )

        self.assertEqual(result.handoff_status, PULSE_BUS_HANDOFF_PREFLIGHT_STATUS_READY)
        self.assertTrue(result.ready_for_supervised_live_command)
        self.assertEqual(result.evidence_id, evidence.evidence_id)
        self.assertEqual(result.blocked_reasons, ())
        self.assertFalse(result.live_agent_bus_handoff_allowed)
        self.assertFalse(result.agent_bus_task_written)
        self.assertFalse(result.approval_granted)
        self.assertFalse(result.candidate_apply_allowed)
        self.assertFalse(result.canonical_writeback_allowed)

    def test_active_duplicate_blocks_handoff_preflight(self) -> None:
        request = self._persist_request()
        evidence = self._persist_full_evidence(request.request_id)

        result = build_agent_bus_handoff_preflight(
            self.tmp_root,
            request.request_id,
            evidence_id=evidence.evidence_id,
            checked_at="2026-04-30T20:07:00+01:00",
            bus_tasks=[
                {
                    "task_id": "task-duplicate",
                    "recipient": request.recipient,
                    "intent": "REVIEW",
                    "status": "review",
                    "work_fingerprint": request.work_fingerprint,
                }
            ],
        )

        self.assertEqual(result.handoff_status, PULSE_BUS_HANDOFF_PREFLIGHT_STATUS_DUPLICATE)
        self.assertTrue(result.duplicate_posture.duplicate_found)
        self.assertEqual(result.duplicate_posture.active_duplicate_task_ids, ("task-duplicate",))
        self.assertIn("active_duplicate_work_fingerprint", result.blocked_reasons)
        self.assertFalse(result.ready_for_supervised_live_command)

    def test_evidence_must_match_request(self) -> None:
        request = self._persist_request()
        other_request = self._approval_request()
        other_request.candidate_id = "candidate-handoff-other"
        other_request.request_id = "pulse-bus-enqueue-approval-other"
        persist_agent_bus_enqueue_approval_request(self.tmp_root, other_request)
        evidence = self._persist_full_evidence(other_request.request_id)

        with self.assertRaises(ValueError):
            build_agent_bus_handoff_preflight(
                self.tmp_root,
                request.request_id,
                evidence_id=evidence.evidence_id,
                bus_tasks=[],
            )

    def test_rejects_authority_flags(self) -> None:
        request = self._persist_request()
        evidence = self._persist_full_evidence(request.request_id)
        base = build_agent_bus_handoff_preflight(
            self.tmp_root,
            request.request_id,
            evidence_id=evidence.evidence_id,
            checked_at="2026-04-30T20:08:00+01:00",
            bus_tasks=[],
        ).to_dict()

        for flag in (
            "persisted_preflight",
            "approval_granted",
            "approval_executed",
            "gate_policy_mutated",
            "live_agent_bus_handoff_allowed",
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
            payload = dict(base)
            payload[flag] = True
            with self.subTest(flag=flag):
                with self.assertRaises(ValueError):
                    PulseAgentBusHandoffPreflight(
                        preflight_id=payload["preflight_id"],
                        request_id=payload["request_id"],
                        checked_at=payload["checked_at"],
                        handoff_status=payload["handoff_status"],
                        request=request,
                        validation=build_agent_bus_handoff_preflight(
                            self.tmp_root,
                            request.request_id,
                            evidence_id=evidence.evidence_id,
                            checked_at="2026-04-30T20:08:00+01:00",
                            bus_tasks=[],
                        ).validation,
                        duplicate_posture=build_agent_bus_handoff_preflight(
                            self.tmp_root,
                            request.request_id,
                            evidence_id=evidence.evidence_id,
                            checked_at="2026-04-30T20:08:00+01:00",
                            bus_tasks=[],
                        ).duplicate_posture,
                        target_posture=build_agent_bus_handoff_preflight(
                            self.tmp_root,
                            request.request_id,
                            evidence_id=evidence.evidence_id,
                            checked_at="2026-04-30T20:08:00+01:00",
                            bus_tasks=[],
                        ).target_posture,
                        evidence_id=evidence.evidence_id,
                        evidence_record_present=True,
                        **{flag: True},
                    ).validate()

    def test_blocked_effects_are_declared(self) -> None:
        request = self._persist_request()
        evidence = self._persist_full_evidence(request.request_id)
        result = build_agent_bus_handoff_preflight(
            self.tmp_root,
            request.request_id,
            evidence_id=evidence.evidence_id,
            checked_at="2026-04-30T20:09:00+01:00",
            bus_tasks=[],
        )

        self.assertEqual(
            set(result.blocked_effects),
            set(PULSE_BUS_HANDOFF_PREFLIGHT_BLOCKED_EFFECTS),
        )


if __name__ == "__main__":
    unittest.main()
