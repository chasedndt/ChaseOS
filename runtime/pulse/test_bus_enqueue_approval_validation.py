"""Tests for non-executing Pulse Agent Bus approval validation."""

from __future__ import annotations

import inspect
import shutil
import unittest
from pathlib import Path

import runtime.pulse.bus_enqueue_approval_validation as validation_module
from runtime.pulse.bus_enqueue_approval_request import (
    build_agent_bus_enqueue_approval_request,
    persist_agent_bus_enqueue_approval_request,
)
from runtime.pulse.bus_enqueue_approval_validation import (
    PULSE_BUS_APPROVAL_VALIDATION_BLOCKED_EFFECTS,
    PULSE_BUS_APPROVAL_VALIDATION_STATUS_BLOCKED,
    PULSE_BUS_APPROVAL_VALIDATION_STATUS_READY,
    PulseAgentBusApprovalValidationEvidence,
    PulseAgentBusApprovalValidationResult,
    build_agent_bus_enqueue_approval_validation_ledger,
    validate_agent_bus_enqueue_approval_request,
    validate_agent_bus_enqueue_approval_request_by_id,
)
from runtime.pulse.bus_enqueue_design import build_agent_bus_enqueue_preflight
from runtime.pulse.bus_review_contract import build_agent_bus_review_request_contract
from runtime.pulse.candidate_inspector import PulseCandidateInspectorItem


_TMP_ROOT = Path(__file__).resolve().parent / "_tmp_bus_enqueue_approval_validation"


class PulseAgentBusEnqueueApprovalValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = _TMP_ROOT
        self._clean_tmp_root()
        self.tmp_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._clean_tmp_root()

    def _clean_tmp_root(self) -> None:
        if self.tmp_root.exists():
            resolved = self.tmp_root.resolve()
            if resolved.name != "_tmp_bus_enqueue_approval_validation":
                raise AssertionError(f"refusing to remove unexpected path: {resolved}")
            shutil.rmtree(resolved)

    def _approval_request(self):
        item = PulseCandidateInspectorItem(
            item_id="candidate-validation-001",
            item_kind="feedback_candidate",
            record_id="candidate-validation-001",
            status="pending_review",
            title="Feedback candidate",
            candidate_kind="feedback",
            candidate_id="candidate-validation-001",
            source_log_path="07_LOGS/Pulse-Decks/feedback-candidates/2026-04-30-feedback-candidates.jsonl",
            source_deck_path="07_LOGS/Pulse-Decks/users/2026-04-30-user-pulse.json",
            source_card_id="pulse-card-validation-001",
            target_ref="pulse-card-validation-001",
            created_at="2026-04-30T11:10:00+01:00",
        )
        contract = build_agent_bus_review_request_contract(
            item,
            requested_by="codex",
            created_at="2026-04-30T11:11:00+01:00",
        )
        preflight = build_agent_bus_enqueue_preflight(
            contract,
            requested_by="codex",
            created_at="2026-04-30T11:12:00+01:00",
        )
        return build_agent_bus_enqueue_approval_request(
            preflight,
            requested_by="codex",
            requested_at="2026-04-30T11:13:00+01:00",
        )

    def test_module_does_not_import_agent_bus_writer_or_backend(self) -> None:
        source = inspect.getsource(validation_module)

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

    def test_default_validation_blocks_missing_required_evidence(self) -> None:
        validation = validate_agent_bus_enqueue_approval_request(
            self._approval_request(),
            validated_at="2026-04-30T11:20:00+01:00",
        )

        self.assertEqual(validation.validation_status, PULSE_BUS_APPROVAL_VALIDATION_STATUS_BLOCKED)
        self.assertEqual(
            set(validation.missing_approvals),
            {
                "operator_enqueue_approval",
                "gate_policy_defined",
                "external_sender_allowance",
                "duplicate_work_fingerprint_review",
            },
        )
        self.assertEqual(validation.satisfied_approvals, ())
        self.assertTrue(validation.validation_record_only)
        self.assertFalse(validation.persisted_validation)
        self.assertFalse(validation.approval_granted)
        self.assertFalse(validation.live_agent_bus_handoff_allowed)
        self.assertFalse(validation.agent_bus_task_written)
        self.assertFalse(validation.candidate_apply_allowed)
        self.assertFalse(validation.canonical_writeback_allowed)
        self.assertEqual(set(validation.blocked_effects), set(PULSE_BUS_APPROVAL_VALIDATION_BLOCKED_EFFECTS))

    def test_partial_validation_lists_remaining_missing_evidence(self) -> None:
        validation = validate_agent_bus_enqueue_approval_request(
            self._approval_request(),
            evidence=PulseAgentBusApprovalValidationEvidence(
                operator_enqueue_approval_present=True,
                external_sender_allowance_present=True,
                reviewer="codex",
                evidence_note="Operator and sender allowance evidence only.",
            ),
            validated_at="2026-04-30T11:25:00+01:00",
        )

        self.assertEqual(validation.validation_status, PULSE_BUS_APPROVAL_VALIDATION_STATUS_BLOCKED)
        self.assertEqual(
            set(validation.satisfied_approvals),
            {"operator_enqueue_approval", "external_sender_allowance"},
        )
        self.assertEqual(
            set(validation.missing_approvals),
            {"gate_policy_defined", "duplicate_work_fingerprint_review"},
        )
        self.assertFalse(validation.approval_granted)
        self.assertFalse(validation.duplicate_query_performed)

    def test_all_evidence_is_ready_for_final_review_but_not_executable(self) -> None:
        validation = validate_agent_bus_enqueue_approval_request(
            self._approval_request(),
            evidence=PulseAgentBusApprovalValidationEvidence(
                operator_enqueue_approval_present=True,
                gate_policy_defined=True,
                external_sender_allowance_present=True,
                duplicate_work_fingerprint_reviewed=True,
                reviewer="operator",
                evidence_note="All required evidence is present for final review.",
            ),
            validated_at="2026-04-30T11:30:00+01:00",
        )

        self.assertEqual(validation.validation_status, PULSE_BUS_APPROVAL_VALIDATION_STATUS_READY)
        self.assertEqual(validation.missing_approvals, ())
        self.assertEqual(
            set(validation.satisfied_approvals),
            {
                "operator_enqueue_approval",
                "gate_policy_defined",
                "external_sender_allowance",
                "duplicate_work_fingerprint_review",
            },
        )
        self.assertFalse(validation.approval_granted)
        self.assertFalse(validation.approval_executed)
        self.assertFalse(validation.live_agent_bus_handoff_allowed)
        self.assertFalse(validation.agent_bus_task_written)
        self.assertFalse(validation.review_response_ingest_allowed)

    def test_validate_by_id_loads_requests_read_only(self) -> None:
        request = self._approval_request()
        persist_agent_bus_enqueue_approval_request(self.tmp_root, request)
        before = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        validation = validate_agent_bus_enqueue_approval_request_by_id(
            self.tmp_root,
            request.request_id,
            validated_at="2026-04-30T11:35:00+01:00",
        )
        after = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        self.assertEqual(before, after)
        self.assertEqual(validation.request_id, request.request_id)
        self.assertEqual(validation.validation_status, PULSE_BUS_APPROVAL_VALIDATION_STATUS_BLOCKED)

    def test_validation_ledger_is_read_only_and_counts_statuses(self) -> None:
        request = self._approval_request()
        persist_agent_bus_enqueue_approval_request(self.tmp_root, request)
        before = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        ledger = build_agent_bus_enqueue_approval_validation_ledger(
            self.tmp_root,
            evidence_by_request_id={
                request.request_id: PulseAgentBusApprovalValidationEvidence(
                    operator_enqueue_approval_present=True,
                    gate_policy_defined=True,
                    external_sender_allowance_present=True,
                    duplicate_work_fingerprint_reviewed=True,
                )
            },
            validated_at="2026-04-30T11:40:00+01:00",
        )
        after = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        self.assertEqual(before, after)
        self.assertEqual(ledger.ledger_status, "read_only")
        self.assertEqual(ledger.validation_count, 1)
        self.assertEqual(ledger.counts_by_status[PULSE_BUS_APPROVAL_VALIDATION_STATUS_READY], 1)
        self.assertEqual(ledger.writes, [])
        self.assertFalse(ledger.approval_granted)
        self.assertFalse(ledger.agent_bus_task_written)
        self.assertFalse(ledger.canonical_writeback_allowed)

    def test_empty_validation_ledger_creates_no_folders(self) -> None:
        ledger = build_agent_bus_enqueue_approval_validation_ledger(self.tmp_root)

        self.assertEqual(ledger.validation_count, 0)
        self.assertFalse((self.tmp_root / "07_LOGS").exists())

    def test_rejects_approval_execution_or_authority_flags(self) -> None:
        base = validate_agent_bus_enqueue_approval_request(
            self._approval_request(),
            validated_at="2026-04-30T11:45:00+01:00",
        ).to_dict()

        forbidden_true_flags = (
            "persisted_validation",
            "approval_granted",
            "approval_executed",
            "gate_policy_mutated",
            "duplicate_query_performed",
            "live_agent_bus_handoff_allowed",
            "agent_bus_task_written",
            "review_response_ingest_allowed",
            "candidate_apply_allowed",
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
                    PulseAgentBusApprovalValidationResult(**payload).validate()

        payload = dict(base)
        payload["validation_record_only"] = False
        with self.assertRaises(ValueError):
            PulseAgentBusApprovalValidationResult(**payload).validate()


if __name__ == "__main__":
    unittest.main()
