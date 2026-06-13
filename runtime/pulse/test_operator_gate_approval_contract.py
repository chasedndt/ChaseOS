"""Tests for Pulse operator/Gate approval UI contract."""

from __future__ import annotations

import inspect
import shutil
import unittest
from pathlib import Path

import runtime.pulse.operator_gate_approval_contract as contract_module
from runtime.pulse.bus_enqueue_approval_request import (
    build_agent_bus_enqueue_approval_request,
    persist_agent_bus_enqueue_approval_request,
)
from runtime.pulse.bus_enqueue_design import build_agent_bus_enqueue_preflight
from runtime.pulse.bus_enqueue_evidence import create_agent_bus_enqueue_evidence_record
from runtime.pulse.bus_review_contract import build_agent_bus_review_request_contract
from runtime.pulse.candidate_inspector import PulseCandidateInspectorItem
from runtime.pulse.operator_gate_approval_contract import (
    PULSE_OPERATOR_GATE_BLOCKED_EFFECTS,
    PULSE_OPERATOR_GATE_CONTRACT_STATUS_BLOCKED,
    PULSE_OPERATOR_GATE_CONTRACT_STATUS_READY,
    PulseOperatorGateApprovalUIContract,
    build_operator_gate_approval_ui_contract,
)


_TMP_ROOT = Path(__file__).resolve().parent / "_tmp_operator_gate_approval_contract"


class PulseOperatorGateApprovalContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = _TMP_ROOT / self._testMethodName[:48]
        self._clean_tmp_root()
        self.tmp_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._clean_tmp_root()

    def _clean_tmp_root(self) -> None:
        if self.tmp_root.exists():
            resolved = self.tmp_root.resolve()
            if resolved.parent.name != "_tmp_operator_gate_approval_contract":
                raise AssertionError(f"refusing to remove unexpected path: {resolved}")
            shutil.rmtree(resolved, ignore_errors=True)
            try:
                resolved.parent.rmdir()
            except OSError:
                pass

    def _approval_request(self):
        item = PulseCandidateInspectorItem(
            item_id="candidate-operator-gate-001",
            item_kind="feedback_candidate",
            record_id="candidate-operator-gate-001",
            status="pending_review",
            title="Feedback candidate",
            candidate_kind="feedback",
            candidate_id="candidate-operator-gate-001",
            source_log_path="07_LOGS/Pulse-Decks/feedback-candidates/2026-04-30-feedback-candidates.jsonl",
            source_deck_path="07_LOGS/Pulse-Decks/users/2026-04-30-user-pulse.json",
            source_card_id="pulse-card-operator-gate-001",
            target_ref="pulse-card-operator-gate-001",
            created_at="2026-04-30T21:10:00+01:00",
        )
        review_contract = build_agent_bus_review_request_contract(
            item,
            requested_by="codex",
            created_at="2026-04-30T21:11:00+01:00",
        )
        preflight = build_agent_bus_enqueue_preflight(
            review_contract,
            requested_by="codex",
            created_at="2026-04-30T21:12:00+01:00",
        )
        return build_agent_bus_enqueue_approval_request(
            preflight,
            requested_by="codex",
            requested_at="2026-04-30T21:13:00+01:00",
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
            evidence_note="operator-approval-ref: pulse-contract-test-approval",
            gate_policy_ref="gate-policy-ref: pulse-contract-test-policy",
            external_sender_allowance_ref="allowance-ref: pulse-contract-test-allowance",
            duplicate_review_ref="duplicate-review-ref: pulse-contract-test-duplicate-review",
            created_at="2026-04-30T21:14:00+01:00",
        )
        return record

    def test_module_does_not_import_agent_bus_writer_or_ui_renderer(self) -> None:
        source = inspect.getsource(contract_module)
        forbidden_tokens = (
            "create_task",
            "update_task_status",
            "claim_task",
            "render_html",
            "write_text",
            "open(",
        )
        for token in forbidden_tokens:
            with self.subTest(token=token):
                self.assertNotIn(token, source)

    def test_ready_preflight_builds_contract_only_packet(self) -> None:
        request = self._persist_request()
        evidence = self._persist_full_evidence(request.request_id)
        before = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        contract = build_operator_gate_approval_ui_contract(
            self.tmp_root,
            request.request_id,
            evidence_id=evidence.evidence_id,
            generated_at="2026-04-30T21:15:00+01:00",
            bus_tasks=[],
        )
        after = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        self.assertEqual(before, after)
        self.assertEqual(contract.contract_status, PULSE_OPERATOR_GATE_CONTRACT_STATUS_READY)
        self.assertTrue(contract.ready_for_operator_gate_decision)
        self.assertEqual(contract.evidence_id, evidence.evidence_id)
        self.assertIn("enqueue-candidate", contract.supervised_live_command_preview)
        self.assertIn(evidence.evidence_id, contract.supervised_live_command_preview)
        self.assertTrue(contract.ui_contract_only)
        self.assertFalse(contract.visual_ui_built)
        self.assertFalse(contract.approval_granted)
        self.assertFalse(contract.live_agent_bus_handoff_allowed)
        self.assertFalse(contract.agent_bus_task_written)
        self.assertFalse(contract.canonical_writeback_allowed)

    def test_blocked_preflight_disables_approve_control_and_has_no_command(self) -> None:
        request = self._persist_request()

        contract = build_operator_gate_approval_ui_contract(
            self.tmp_root,
            request.request_id,
            generated_at="2026-04-30T21:16:00+01:00",
            bus_tasks=[],
        )

        self.assertEqual(contract.contract_status, PULSE_OPERATOR_GATE_CONTRACT_STATUS_BLOCKED)
        self.assertFalse(contract.ready_for_operator_gate_decision)
        self.assertEqual(contract.supervised_live_command_preview, ())
        approve_control = next(
            control
            for control in contract.decision_controls
            if control.decision_type == "approve_supervised_live_enqueue"
        )
        self.assertFalse(approve_control.enabled)
        self.assertIn("no_persisted_evidence_record", contract.blocked_reasons)

    def test_ready_contract_exposes_required_evidence_fields(self) -> None:
        request = self._persist_request()
        evidence = self._persist_full_evidence(request.request_id)
        contract = build_operator_gate_approval_ui_contract(
            self.tmp_root,
            request.request_id,
            evidence_id=evidence.evidence_id,
            generated_at="2026-04-30T21:17:00+01:00",
            bus_tasks=[],
        )

        payload = contract.to_dict()
        self.assertIn("visible_evidence_fields", payload)
        self.assertIn("satisfied_approvals", payload["visible_evidence_fields"])
        self.assertIn("approval_evidence_slots", payload["visible_evidence_fields"])
        self.assertEqual(
            set(payload["handoff_preflight"]["validation"]["satisfied_approvals"]),
            {
                "operator_enqueue_approval",
                "gate_policy_defined",
                "external_sender_allowance",
                "duplicate_work_fingerprint_review",
            },
        )
        slots_by_key = {slot["approval_key"]: slot for slot in payload["approval_evidence_slots"]}
        self.assertEqual(
            set(slots_by_key),
            {
                "operator_enqueue_approval",
                "gate_policy_defined",
                "external_sender_allowance",
                "duplicate_work_fingerprint_review",
            },
        )
        self.assertTrue(all(slot["satisfied"] for slot in slots_by_key.values()))
        self.assertEqual(
            slots_by_key["operator_enqueue_approval"]["ref"],
            "operator-approval-ref: pulse-contract-test-approval",
        )
        self.assertEqual(
            slots_by_key["gate_policy_defined"]["ref"],
            "gate-policy-ref: pulse-contract-test-policy",
        )

    def test_blocked_contract_exposes_unsatisfied_evidence_slots_with_capture_commands(self) -> None:
        request = self._persist_request()
        contract = build_operator_gate_approval_ui_contract(
            self.tmp_root,
            request.request_id,
            generated_at="2026-04-30T21:17:30+01:00",
            bus_tasks=[],
        )

        payload = contract.to_dict()
        slots_by_key = {slot["approval_key"]: slot for slot in payload["approval_evidence_slots"]}
        self.assertEqual(
            set(slots_by_key),
            {
                "operator_enqueue_approval",
                "gate_policy_defined",
                "external_sender_allowance",
                "duplicate_work_fingerprint_review",
            },
        )
        self.assertFalse(any(slot["satisfied"] for slot in slots_by_key.values()))
        self.assertIsNone(slots_by_key["operator_enqueue_approval"]["ref"])
        self.assertIn(
            "--operator-approved",
            slots_by_key["operator_enqueue_approval"]["capture_command"],
        )
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
        self.assertIn(
            "--gate-policy-ref <gate-policy-ref>",
            slots_by_key["gate_policy_defined"]["capture_command"],
        )
        self.assertEqual(
            slots_by_key["gate_policy_defined"]["ref_placeholder"],
            "<gate-policy-ref>",
        )
        self.assertTrue(slots_by_key["gate_policy_defined"]["requires_real_ref"])
        self.assertTrue(slots_by_key["gate_policy_defined"]["placeholder_ref_rejected"])
        self.assertFalse(payload["approval_granted"])
        self.assertFalse(payload["agent_bus_task_written"])

    def test_rejects_authority_flags(self) -> None:
        request = self._persist_request()
        evidence = self._persist_full_evidence(request.request_id)
        contract = build_operator_gate_approval_ui_contract(
            self.tmp_root,
            request.request_id,
            evidence_id=evidence.evidence_id,
            generated_at="2026-04-30T21:18:00+01:00",
            bus_tasks=[],
        )

        for flag in (
            "visual_ui_built",
            "persisted_contract",
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
            with self.subTest(flag=flag):
                with self.assertRaises(ValueError):
                    PulseOperatorGateApprovalUIContract(
                        contract_id=contract.contract_id,
                        request_id=contract.request_id,
                        preflight_id=contract.preflight_id,
                        generated_at=contract.generated_at,
                        contract_status=contract.contract_status,
                        handoff_preflight=contract.handoff_preflight,
                        evidence_id=contract.evidence_id,
                        decision_controls=contract.decision_controls,
                        supervised_live_command_preview=contract.supervised_live_command_preview,
                        **{flag: True},
                    ).validate()

    def test_blocked_effects_are_declared(self) -> None:
        request = self._persist_request()
        evidence = self._persist_full_evidence(request.request_id)
        contract = build_operator_gate_approval_ui_contract(
            self.tmp_root,
            request.request_id,
            evidence_id=evidence.evidence_id,
            generated_at="2026-04-30T21:19:00+01:00",
            bus_tasks=[],
        )

        self.assertEqual(
            set(contract.blocked_effects),
            set(PULSE_OPERATOR_GATE_BLOCKED_EFFECTS),
        )


if __name__ == "__main__":
    unittest.main()
