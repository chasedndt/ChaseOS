"""Tests for Pulse Agent Bus enqueue evidence artifacts."""

from __future__ import annotations

import inspect
import shutil
import unittest
from pathlib import Path

import runtime.pulse.bus_enqueue_evidence as evidence_module
from runtime.pulse.bus_enqueue_approval_request import (
    build_agent_bus_enqueue_approval_request,
    persist_agent_bus_enqueue_approval_request,
)
from runtime.pulse.bus_enqueue_design import build_agent_bus_enqueue_preflight
from runtime.pulse.bus_enqueue_evidence import (
    PULSE_BUS_ENQUEUE_EVIDENCE_BLOCKED_EFFECTS,
    PulseAgentBusEnqueueEvidenceRecord,
    build_agent_bus_enqueue_evidence_ledger,
    build_agent_bus_enqueue_evidence_record,
    create_agent_bus_enqueue_evidence_record,
    load_agent_bus_enqueue_evidence_record_by_id,
    load_agent_bus_enqueue_evidence_records,
    persist_agent_bus_enqueue_evidence_record,
)
from runtime.pulse.bus_review_contract import build_agent_bus_review_request_contract
from runtime.pulse.candidate_inspector import PulseCandidateInspectorItem


_TMP_ROOT = Path(__file__).resolve().parent / "_tmp_bus_enqueue_evidence"


class PulseAgentBusEnqueueEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = _TMP_ROOT / self._testMethodName[:48]
        self._clean_tmp_root()
        self.tmp_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._clean_tmp_root()

    def _clean_tmp_root(self) -> None:
        if self.tmp_root.exists():
            resolved = self.tmp_root.resolve()
            if resolved.parent.name != "_tmp_bus_enqueue_evidence":
                raise AssertionError(f"refusing to remove unexpected path: {resolved}")
            shutil.rmtree(resolved, ignore_errors=True)
            try:
                resolved.parent.rmdir()
            except OSError:
                pass

    def _approval_request(self):
        item = PulseCandidateInspectorItem(
            item_id="candidate-evidence-001",
            item_kind="feedback_candidate",
            record_id="candidate-evidence-001",
            status="pending_review",
            title="Feedback candidate",
            candidate_kind="feedback",
            candidate_id="candidate-evidence-001",
            source_log_path="07_LOGS/Pulse-Decks/feedback-candidates/2026-04-30-feedback-candidates.jsonl",
            source_deck_path="07_LOGS/Pulse-Decks/users/2026-04-30-user-pulse.json",
            source_card_id="pulse-card-evidence-001",
            target_ref="pulse-card-evidence-001",
            created_at="2026-04-30T18:10:00+01:00",
        )
        contract = build_agent_bus_review_request_contract(
            item,
            requested_by="codex",
            created_at="2026-04-30T18:11:00+01:00",
        )
        preflight = build_agent_bus_enqueue_preflight(
            contract,
            requested_by="codex",
            created_at="2026-04-30T18:12:00+01:00",
        )
        return build_agent_bus_enqueue_approval_request(
            preflight,
            requested_by="codex",
            requested_at="2026-04-30T18:13:00+01:00",
        )

    def test_module_does_not_import_agent_bus_writer_or_backend(self) -> None:
        source = inspect.getsource(evidence_module)
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

    def test_build_partial_evidence_record_is_record_only(self) -> None:
        record = build_agent_bus_enqueue_evidence_record(
            "pulse-bus-enqueue-approval-001",
            reviewer="operator",
            operator_enqueue_approval_present=True,
            evidence_note="Operator approves enqueue review, pending Gate evidence.",
            created_at="2026-04-30T18:15:00+01:00",
        )

        self.assertEqual(record.request_id, "pulse-bus-enqueue-approval-001")
        self.assertTrue(record.operator_enqueue_approval_present)
        self.assertFalse(record.gate_policy_defined)
        self.assertEqual(
            set(record.validation_evidence.missing_approvals),
            {
                "gate_policy_defined",
                "external_sender_allowance",
                "duplicate_work_fingerprint_review",
            },
        )
        self.assertTrue(record.evidence_record_only)
        self.assertFalse(record.approval_granted)
        self.assertFalse(record.agent_bus_task_written)
        self.assertFalse(record.canonical_writeback_allowed)

    def test_all_evidence_record_converts_to_validation_evidence(self) -> None:
        record = build_agent_bus_enqueue_evidence_record(
            "pulse-bus-enqueue-approval-002",
            operator_enqueue_approval_present=True,
            gate_policy_defined=True,
            external_sender_allowance_present=True,
            duplicate_work_fingerprint_reviewed=True,
            evidence_note="operator-approval-ref: pulse-test-approval",
            gate_policy_ref="gate-policy-ref: pulse-test-policy",
            external_sender_allowance_ref="allowance-ref: pulse-test-allowance",
            duplicate_review_ref="duplicate-review-ref: pulse-test-duplicate-review",
            created_at="2026-04-30T18:16:00+01:00",
        )

        validation_evidence = record.validation_evidence
        self.assertEqual(validation_evidence.missing_approvals, ())
        self.assertEqual(
            set(validation_evidence.satisfied_approvals),
            {
                "operator_enqueue_approval",
                "gate_policy_defined",
                "external_sender_allowance",
                "duplicate_work_fingerprint_review",
            },
        )

    def test_satisfied_evidence_flags_require_explicit_refs(self) -> None:
        required_ref_cases = (
            (
                "operator_enqueue_approval_present",
                {"operator_enqueue_approval_present": True},
                "operator approval evidence requires --note",
            ),
            (
                "gate_policy_defined",
                {"gate_policy_defined": True},
                "Gate policy evidence requires gate_policy_ref",
            ),
            (
                "external_sender_allowance_present",
                {"external_sender_allowance_present": True},
                "external sender allowance evidence requires external_sender_allowance_ref",
            ),
            (
                "duplicate_work_fingerprint_reviewed",
                {"duplicate_work_fingerprint_reviewed": True},
                "duplicate work_fingerprint evidence requires duplicate_review_ref",
            ),
        )
        for name, kwargs, message in required_ref_cases:
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, message):
                    build_agent_bus_enqueue_evidence_record(
                        "pulse-bus-enqueue-approval-missing-ref",
                        created_at="2026-04-30T18:16:30+01:00",
                        **kwargs,
                    )

    def test_unsatisfied_operator_slot_does_not_surface_generic_note_as_ref(self) -> None:
        record = build_agent_bus_enqueue_evidence_record(
            "pulse-bus-enqueue-approval-unsatisfied-note",
            evidence_note="Generic rehearsal note is not an operator approval ref.",
            created_at="2026-04-30T18:16:45+01:00",
        )

        self.assertFalse(record.operator_enqueue_approval_present)
        self.assertEqual(record.validation_evidence.satisfied_approvals, ())

    def test_evidence_refs_reject_cli_placeholders(self) -> None:
        placeholder_cases = (
            (
                "operator_placeholder_note",
                {
                    "operator_enqueue_approval_present": True,
                    "evidence_note": "<operator-approval-ref>",
                },
                "operator approval evidence requires a real --note ref",
            ),
            (
                "gate_policy_placeholder",
                {
                    "gate_policy_defined": True,
                    "gate_policy_ref": "<gate-policy-ref>",
                },
                "Gate policy evidence requires a real gate_policy_ref",
            ),
            (
                "external_sender_placeholder",
                {
                    "external_sender_allowance_present": True,
                    "external_sender_allowance_ref": "<allowance-ref>",
                },
                "external sender allowance evidence requires a real external_sender_allowance_ref",
            ),
            (
                "duplicate_review_placeholder",
                {
                    "duplicate_work_fingerprint_reviewed": True,
                    "duplicate_review_ref": "<duplicate-review-ref>",
                },
                "duplicate work_fingerprint evidence requires a real duplicate_review_ref",
            ),
        )
        for name, kwargs, message in placeholder_cases:
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, message):
                    build_agent_bus_enqueue_evidence_record(
                        "pulse-bus-enqueue-approval-placeholder-ref",
                        created_at="2026-04-30T18:16:50+01:00",
                        **kwargs,
                    )

    def test_persist_and_load_evidence_record(self) -> None:
        record = build_agent_bus_enqueue_evidence_record(
            "pulse-bus-enqueue-approval-003",
            operator_enqueue_approval_present=True,
            evidence_note="operator-approval-ref: pulse-test-approval",
            created_at="2026-04-30T18:17:00+01:00",
        )
        artifact = persist_agent_bus_enqueue_evidence_record(self.tmp_root, record)

        self.assertEqual(artifact.evidence_id, record.evidence_id)
        self.assertTrue((self.tmp_root / artifact.path).exists())

        loaded = load_agent_bus_enqueue_evidence_records(self.tmp_root)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].evidence_id, record.evidence_id)

    def test_create_requires_existing_approval_request(self) -> None:
        with self.assertRaises(ValueError):
            create_agent_bus_enqueue_evidence_record(
                self.tmp_root,
                "missing-request",
                operator_enqueue_approval_present=True,
            )

    def test_create_persists_for_existing_request(self) -> None:
        request = self._approval_request()
        persist_agent_bus_enqueue_approval_request(self.tmp_root, request)

        record, artifact = create_agent_bus_enqueue_evidence_record(
            self.tmp_root,
            request.request_id,
            operator_enqueue_approval_present=True,
            gate_policy_defined=True,
            external_sender_allowance_present=True,
            duplicate_work_fingerprint_reviewed=True,
            evidence_note="operator-approval-ref: pulse-test-approval",
            gate_policy_ref="gate-policy-ref: pulse-test-policy",
            external_sender_allowance_ref="allowance-ref: pulse-test-allowance",
            duplicate_review_ref="duplicate-review-ref: pulse-test-duplicate-review",
            created_at="2026-04-30T18:18:00+01:00",
        )

        self.assertEqual(record.request_id, request.request_id)
        self.assertEqual(artifact.evidence_id, record.evidence_id)
        loaded = load_agent_bus_enqueue_evidence_record_by_id(
            self.tmp_root,
            record.evidence_id,
        )
        self.assertEqual(loaded.validation_evidence.missing_approvals, ())

    def test_read_only_ledger_creates_no_folders_on_empty_read(self) -> None:
        ledger = build_agent_bus_enqueue_evidence_ledger(self.tmp_root)

        self.assertEqual(ledger.ledger_status, "read_only")
        self.assertEqual(ledger.record_count, 0)
        self.assertEqual(ledger.writes, [])
        self.assertFalse((self.tmp_root / "07_LOGS").exists())

    def test_rejects_authority_flags(self) -> None:
        base = build_agent_bus_enqueue_evidence_record(
            "pulse-bus-enqueue-approval-004",
            operator_enqueue_approval_present=True,
            evidence_note="operator-approval-ref: pulse-test-approval",
            created_at="2026-04-30T18:19:00+01:00",
        ).to_dict()

        for flag in (
            "approval_granted",
            "approval_executed",
            "gate_policy_mutated",
            "agent_bus_task_written",
            "live_agent_bus_handoff_allowed",
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
                    PulseAgentBusEnqueueEvidenceRecord.from_dict(payload)

        payload = dict(base)
        payload["evidence_record_only"] = False
        with self.assertRaises(ValueError):
            PulseAgentBusEnqueueEvidenceRecord.from_dict(payload)

    def test_blocked_effects_are_declared(self) -> None:
        record = build_agent_bus_enqueue_evidence_record(
            "pulse-bus-enqueue-approval-005",
            created_at="2026-04-30T18:20:00+01:00",
        )
        self.assertEqual(
            set(record.blocked_effects),
            set(PULSE_BUS_ENQUEUE_EVIDENCE_BLOCKED_EFFECTS),
        )


if __name__ == "__main__":
    unittest.main()
