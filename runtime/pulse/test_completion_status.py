"""Tests for read-only ChaseOS Pulse completion status."""

from __future__ import annotations

import inspect
import json
import shutil
import unittest
import zipfile
from pathlib import Path

import runtime.pulse.completion_status as completion_module
from runtime.pulse.bus_enqueue import PulseAgentBusEnqueueResult
from runtime.pulse.bus_enqueue_evidence import PulseAgentBusEnqueueEvidenceRecord
from runtime.pulse.completion_status import build_pulse_completion_status
from runtime.pulse.real_approval_artifact_rehearsal import (
    run_real_approval_artifact_rehearsal,
)
from runtime.pulse.review_decision_log import (
    DECISION_FOLLOWUP_SIGNALS,
    PulseCandidateReviewDecision,
    persist_review_decision,
)


_TMP_ROOT = Path(__file__).resolve().parent / "_tmp_completion_status"


class PulseCompletionStatusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = _TMP_ROOT / self._testMethodName[:48]
        self._clean_tmp_root()
        self.tmp_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._clean_tmp_root()

    def _clean_tmp_root(self) -> None:
        if self.tmp_root.exists():
            resolved = self.tmp_root.resolve()
            if resolved.parent.name != "_tmp_completion_status":
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
                    "deck_id": "pulse-deck-test",
                    "audience": "user",
                    "cards": [
                        {
                            "card_id": "pulse-card-completion-status-001",
                            "title": "Completion status card",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    def _write_fake_pulse_workbook(self) -> None:
        workbook_path = (
            self.tmp_root
            / "99_ARCHIVE"
            / "Reporting"
            / "ChaseOS_RnD_Canonical_Full_2026-04-28.xlsx"
        )
        workbook_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(workbook_path, "w") as archive:
            archive.writestr(
                "xl/sharedStrings.xml",
                "<sst><si><t>FR-028 F176 F198 FIT-132 FIT-139 CH-1005 ChaseOS Pulse</t></si></sst>",
            )

    def _write_complete_backend_chain_with_schedule_proof(self) -> None:
        candidate_id = "feedback-candidate-complete-backend-001"
        request_id = "pulse-bus-enqueue-approval-complete-backend-001"
        evidence = PulseAgentBusEnqueueEvidenceRecord(
            evidence_id="pulse-bus-enqueue-evidence-complete-backend-001",
            request_id=request_id,
            created_at="2026-05-02T14:00:00+01:00",
            reviewer="Hermes-Optimus",
            operator_enqueue_approval_present=True,
            gate_policy_defined=True,
            external_sender_allowance_present=True,
            duplicate_work_fingerprint_reviewed=True,
            evidence_note="operator-approval:test-complete-backend-chain",
            gate_policy_ref="06_AGENTS/Pulse-Feedback-Policy.md#next-pass",
            external_sender_allowance_ref="HERMES.md#current-local-truth",
            duplicate_review_ref="07_LOGS/Agent-Activity/test-pulse-duplicate-review.md",
        )
        evidence_path = (
            self.tmp_root
            / "07_LOGS"
            / "Pulse-Decks"
            / "agent-bus-enqueue-evidence"
            / "2026-05-02-agent-bus-enqueue-evidence.jsonl"
        )
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text(
            json.dumps(evidence.to_dict(), sort_keys=True) + "\n",
            encoding="utf-8",
        )
        enqueue_result = PulseAgentBusEnqueueResult(
            result_id="pulse-bus-enqueue-result-complete-backend-001",
            validation_id="pulse-bus-approval-validation-complete-backend-001",
            request_id=request_id,
            candidate_id=candidate_id,
            candidate_kind="feedback",
            recipient="Hermes",
            work_fingerprint=f"pulse-candidate-review:feedback:{candidate_id}",
            result_status="enqueued",
            enqueued=True,
            enqueued_at="2026-05-02T14:01:00+01:00",
            task_id="task-complete-backend-001",
            reason="Task created on Agent Bus.",
        )
        enqueue_path = (
            self.tmp_root
            / "07_LOGS"
            / "Pulse-Decks"
            / "agent-bus-enqueue-results"
            / "2026-05-02-enqueue-results.jsonl"
        )
        enqueue_path.parent.mkdir(parents=True, exist_ok=True)
        enqueue_path.write_text(
            json.dumps(enqueue_result.to_dict(), sort_keys=True) + "\n",
            encoding="utf-8",
        )
        decision = PulseCandidateReviewDecision(
            decision_id="pulse-review-decision-complete-backend-001",
            candidate_id=candidate_id,
            candidate_kind="feedback",
            decision_type="accept_for_future_ranking",
            reviewer="Hermes",
            followup_signals=DECISION_FOLLOWUP_SIGNALS["accept_for_future_ranking"],
        )
        persist_review_decision(self.tmp_root, decision)
        registry_path = (
            self.tmp_root
            / "07_LOGS"
            / "Pulse-Decks"
            / "apply-registry"
            / "applied-decisions.json"
        )
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            json.dumps({"applied_decision_ids": [decision.decision_id]}),
            encoding="utf-8",
        )
        agents_dir = self.tmp_root / "06_AGENTS"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "ChaseOS-Pulse-Post-Apply-Truth-State-Audit.md").write_text(
            "# Audit\n\nStatus: PASS\n",
            encoding="utf-8",
        )
        (agents_dir / "ChaseOS-Pulse-RnD-Workbook-Update-Approval.md").write_text(
            "# Approval Packet\n\nStatus: NO-WRITE APPROVAL PACKET\n",
            encoding="utf-8",
        )
        (agents_dir / "ChaseOS-Pulse-Native-Schedule-Activation-Catchup-Proof.md").write_text(
            "# Schedule Proof\n\nStatus: PROOF ONLY - NO SCHEDULE ACTIVATION\n",
            encoding="utf-8",
        )
        self._write_fake_pulse_workbook()

    def test_module_does_not_import_agent_bus_writer(self) -> None:
        source = inspect.getsource(completion_module)
        forbidden_tokens = (
            "create_task",
            "update_task_status",
            "claim_task",
            "enqueue_pulse_review_task",
            "persist_review_decision",
            "apply_reviewed_candidates",
        )
        for token in forbidden_tokens:
            with self.subTest(token=token):
                self.assertNotIn(token, source)

    def test_empty_repo_reports_not_done_without_writes(self) -> None:
        before = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))
        status = build_pulse_completion_status(
            self.tmp_root,
            generated_at="2026-05-01T21:40:00+01:00",
        )
        after = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        self.assertEqual(before, after)
        self.assertFalse(status.feature_done)
        self.assertFalse(status.backend_control_plane_done)
        self.assertFalse(status.agent_bus_task_written)
        self.assertFalse(status.canonical_writeback_allowed)
        self.assertIn("no_live_pulse_review_enqueue", status.blocked_reasons)

    def test_artifact_chain_status_reports_missing_approval_evidence(self) -> None:
        self._write_user_deck()
        run_real_approval_artifact_rehearsal(
            self.tmp_root,
            generated_at="2026-05-01T21:41:00+01:00",
        )

        status = build_pulse_completion_status(
            self.tmp_root,
            generated_at="2026-05-01T21:42:00+01:00",
        )
        approval_item = next(item for item in status.items if item.area == "approval_evidence")

        self.assertEqual(status.overall_status, "backend_proof_pending")
        self.assertFalse(status.feature_done)
        self.assertEqual(approval_item.status, "blocked")
        self.assertIn("missing:operator_enqueue_approval", status.blocked_reasons)
        self.assertIsNotNone(status.approval_request_id)
        self.assertIsNotNone(status.evidence_id)
        self.assertEqual(status.enqueue_result_count, 0)
        self.assertEqual(status.review_decision_count, 0)

    def test_completed_enqueue_and_review_are_reported_as_observed_proof(self) -> None:
        candidate_id = "feedback-candidate-pulse-status-reconciled-001"
        request_id = "pulse-bus-enqueue-approval-status-reconciled-001"
        evidence = PulseAgentBusEnqueueEvidenceRecord(
            evidence_id="pulse-bus-enqueue-evidence-status-reconciled-001",
            request_id=request_id,
            created_at="2026-05-02T10:00:00+00:00",
            reviewer="Hermes-Optimus",
            operator_enqueue_approval_present=True,
            gate_policy_defined=True,
            external_sender_allowance_present=True,
            duplicate_work_fingerprint_reviewed=True,
            evidence_note="operator-approval:test-status-reconciliation",
            gate_policy_ref="06_AGENTS/Pulse-Feedback-Policy.md#next-pass",
            external_sender_allowance_ref="HERMES.md#current-local-truth",
            duplicate_review_ref="07_LOGS/Agent-Activity/test-pulse-duplicate-review.md",
        )
        evidence_path = (
            self.tmp_root
            / "07_LOGS"
            / "Pulse-Decks"
            / "agent-bus-enqueue-evidence"
            / "2026-05-02-agent-bus-enqueue-evidence.jsonl"
        )
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text(json.dumps(evidence.to_dict(), sort_keys=True) + "\n", encoding="utf-8")

        enqueue_result = PulseAgentBusEnqueueResult(
            result_id="pulse-bus-enqueue-result-status-reconciled-001",
            validation_id="pulse-bus-approval-validation-status-reconciled-001",
            request_id=request_id,
            candidate_id=candidate_id,
            candidate_kind="feedback",
            recipient="Hermes",
            work_fingerprint=f"pulse-candidate-review:feedback:{candidate_id}",
            result_status="enqueued",
            enqueued=True,
            enqueued_at="2026-05-02T10:01:00+00:00",
            task_id="task-status-reconciled-001",
            reason="Task created on Agent Bus.",
        )
        enqueue_path = (
            self.tmp_root
            / "07_LOGS"
            / "Pulse-Decks"
            / "agent-bus-enqueue-results"
            / "2026-05-02-enqueue-results.jsonl"
        )
        enqueue_path.parent.mkdir(parents=True, exist_ok=True)
        enqueue_path.write_text(
            json.dumps(enqueue_result.to_dict(), sort_keys=True) + "\n",
            encoding="utf-8",
        )

        decision = PulseCandidateReviewDecision(
            decision_id="pulse-review-decision-status-reconciled-001",
            candidate_id=candidate_id,
            candidate_kind="feedback",
            decision_type="accept_for_future_ranking",
            reviewer="Hermes",
            followup_signals=DECISION_FOLLOWUP_SIGNALS["accept_for_future_ranking"],
        )
        persist_review_decision(self.tmp_root, decision)

        status = build_pulse_completion_status(
            self.tmp_root,
            generated_at="2026-05-02T10:02:00+00:00",
        )
        enqueue_item = next(item for item in status.items if item.area == "agent_bus_review_enqueue")
        ingest_item = next(item for item in status.items if item.area == "review_response_ingest")

        self.assertEqual(enqueue_item.status, "complete")
        self.assertEqual(ingest_item.status, "complete")
        self.assertTrue(status.live_enqueue_proof_observed)
        self.assertTrue(status.agent_bus_task_write_proof_observed)
        self.assertTrue(status.review_decision_proof_observed)
        self.assertFalse(status.live_enqueue_executed)
        self.assertFalse(status.agent_bus_task_written)
        self.assertFalse(status.review_response_ingest_allowed)
        self.assertNotIn("no_live_pulse_review_enqueue", status.blocked_reasons)
        self.assertNotIn("no_real_review_response_ingest", status.blocked_reasons)
        self.assertIn("no_approved_candidate_apply", status.blocked_reasons)
        self.assertEqual(
            status.next_recommended_pass,
            "chaseos-pulse-candidate-apply-approval-contract",
        )

    def test_applied_review_decision_clears_candidate_apply_blocker(self) -> None:
        decision = PulseCandidateReviewDecision(
            decision_id="pulse-review-decision-applied-001",
            candidate_id="feedback-candidate-applied-001",
            candidate_kind="feedback",
            decision_type="accept_for_future_ranking",
            reviewer="Hermes",
            followup_signals=DECISION_FOLLOWUP_SIGNALS["accept_for_future_ranking"],
        )
        persist_review_decision(self.tmp_root, decision)
        registry_path = (
            self.tmp_root
            / "07_LOGS"
            / "Pulse-Decks"
            / "apply-registry"
            / "applied-decisions.json"
        )
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            json.dumps({"applied_decision_ids": [decision.decision_id]}),
            encoding="utf-8",
        )

        status = build_pulse_completion_status(
            self.tmp_root,
            generated_at="2026-05-02T10:50:00+01:00",
        )
        candidate_apply_item = next(item for item in status.items if item.area == "candidate_apply")

        self.assertEqual(candidate_apply_item.status, "complete")
        self.assertTrue(candidate_apply_item.complete_for_feature_done)
        self.assertNotIn("no_approved_candidate_apply", status.blocked_reasons)
        self.assertEqual(
            status.next_recommended_pass,
            "chaseos-pulse-post-apply-truth-state-audit",
        )

    def test_post_apply_audit_moves_next_pass_to_rnd_approval(self) -> None:
        decision = PulseCandidateReviewDecision(
            decision_id="pulse-review-decision-applied-audit-001",
            candidate_id="feedback-candidate-applied-audit-001",
            candidate_kind="feedback",
            decision_type="accept_for_future_ranking",
            reviewer="Hermes",
            followup_signals=DECISION_FOLLOWUP_SIGNALS["accept_for_future_ranking"],
        )
        persist_review_decision(self.tmp_root, decision)
        registry_path = (
            self.tmp_root
            / "07_LOGS"
            / "Pulse-Decks"
            / "apply-registry"
            / "applied-decisions.json"
        )
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            json.dumps({"applied_decision_ids": [decision.decision_id]}),
            encoding="utf-8",
        )
        audit_path = (
            self.tmp_root
            / "06_AGENTS"
            / "ChaseOS-Pulse-Post-Apply-Truth-State-Audit.md"
        )
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text("# Audit\n\nStatus: PASS\n", encoding="utf-8")

        status = build_pulse_completion_status(
            self.tmp_root,
            generated_at="2026-05-02T11:05:00+01:00",
        )
        audit_item = next(
            item for item in status.items if item.area == "post_apply_truth_state_audit"
        )

        self.assertEqual(audit_item.status, "complete")
        self.assertNotIn("post_apply_truth_state_audit_not_done", status.blocked_reasons)
        self.assertEqual(
            status.next_recommended_pass,
            "chaseos-pulse-rnd-workbook-update-approval",
        )
        self.assertIn("rd_workbook_approval_packet_not_done", status.blocked_reasons)

    def test_rnd_approval_packet_moves_next_pass_to_sync_after_operator_approval(self) -> None:
        decision = PulseCandidateReviewDecision(
            decision_id="pulse-review-decision-applied-audit-approval-001",
            candidate_id="feedback-candidate-applied-audit-approval-001",
            candidate_kind="feedback",
            decision_type="accept_for_future_ranking",
            reviewer="Hermes",
            followup_signals=DECISION_FOLLOWUP_SIGNALS["accept_for_future_ranking"],
        )
        persist_review_decision(self.tmp_root, decision)
        registry_path = (
            self.tmp_root
            / "07_LOGS"
            / "Pulse-Decks"
            / "apply-registry"
            / "applied-decisions.json"
        )
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            json.dumps({"applied_decision_ids": [decision.decision_id]}),
            encoding="utf-8",
        )
        audit_path = (
            self.tmp_root
            / "06_AGENTS"
            / "ChaseOS-Pulse-Post-Apply-Truth-State-Audit.md"
        )
        approval_packet_path = (
            self.tmp_root
            / "06_AGENTS"
            / "ChaseOS-Pulse-RnD-Workbook-Update-Approval.md"
        )
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text("# Audit\n\nStatus: PASS\n", encoding="utf-8")
        approval_packet_path.write_text(
            "# Approval Packet\n\nStatus: NO-WRITE APPROVAL PACKET\n",
            encoding="utf-8",
        )

        status = build_pulse_completion_status(
            self.tmp_root,
            generated_at="2026-05-02T11:30:00+01:00",
        )
        approval_item = next(
            item for item in status.items if item.area == "rd_workbook_approval_packet"
        )

        self.assertEqual(approval_item.status, "complete")
        self.assertNotIn("rd_workbook_approval_packet_not_done", status.blocked_reasons)
        self.assertIn("rd_workbook_not_updated", status.blocked_reasons)
        self.assertIn(
            "native_schedule_activation_catchup_proof_not_done",
            status.blocked_reasons,
        )
        self.assertEqual(
            status.next_recommended_pass,
            "chaseos-pulse-rnd-workbook-sync-after-operator-approval",
        )
        self.assertFalse(status.rd_workbook_update_allowed)

    def test_synced_rnd_workbook_moves_next_pass_to_native_schedule_proof(self) -> None:
        decision = PulseCandidateReviewDecision(
            decision_id="pulse-review-decision-applied-audit-sync-001",
            candidate_id="feedback-candidate-applied-audit-sync-001",
            candidate_kind="feedback",
            decision_type="accept_for_future_ranking",
            reviewer="Hermes",
            followup_signals=DECISION_FOLLOWUP_SIGNALS["accept_for_future_ranking"],
        )
        persist_review_decision(self.tmp_root, decision)
        registry_path = (
            self.tmp_root
            / "07_LOGS"
            / "Pulse-Decks"
            / "apply-registry"
            / "applied-decisions.json"
        )
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            json.dumps({"applied_decision_ids": [decision.decision_id]}),
            encoding="utf-8",
        )
        audit_path = (
            self.tmp_root
            / "06_AGENTS"
            / "ChaseOS-Pulse-Post-Apply-Truth-State-Audit.md"
        )
        approval_packet_path = (
            self.tmp_root
            / "06_AGENTS"
            / "ChaseOS-Pulse-RnD-Workbook-Update-Approval.md"
        )
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text("# Audit\n\nStatus: PASS\n", encoding="utf-8")
        approval_packet_path.write_text(
            "# Approval Packet\n\nStatus: NO-WRITE APPROVAL PACKET\n",
            encoding="utf-8",
        )
        self._write_fake_pulse_workbook()

        status = build_pulse_completion_status(
            self.tmp_root,
            generated_at="2026-05-02T12:05:00+01:00",
        )
        workbook_item = next(item for item in status.items if item.area == "rd_workbook")
        schedule_item = next(
            item for item in status.items if item.area == "native_schedule_activation_proof"
        )

        self.assertEqual(workbook_item.status, "complete")
        self.assertEqual(schedule_item.status, "blocked")
        self.assertNotIn("rd_workbook_not_updated", status.blocked_reasons)
        self.assertIn(
            "native_schedule_activation_catchup_proof_not_done",
            status.blocked_reasons,
        )
        self.assertEqual(
            status.next_recommended_pass,
            "chaseos-pulse-native-schedule-activation-catchup-proof",
        )

    def test_native_schedule_catchup_proof_leaves_only_phase10_ui_pending(self) -> None:
        candidate_id = "feedback-candidate-applied-audit-sync-schedule-001"
        request_id = "pulse-bus-enqueue-approval-sync-schedule-001"
        evidence = PulseAgentBusEnqueueEvidenceRecord(
            evidence_id="pulse-bus-enqueue-evidence-sync-schedule-001",
            request_id=request_id,
            created_at="2026-05-02T13:00:00+01:00",
            reviewer="Hermes-Optimus",
            operator_enqueue_approval_present=True,
            gate_policy_defined=True,
            external_sender_allowance_present=True,
            duplicate_work_fingerprint_reviewed=True,
            evidence_note="operator-approval:test-schedule-catchup-proof",
            gate_policy_ref="06_AGENTS/Pulse-Feedback-Policy.md#next-pass",
            external_sender_allowance_ref="HERMES.md#current-local-truth",
            duplicate_review_ref="07_LOGS/Agent-Activity/test-pulse-duplicate-review.md",
        )
        evidence_path = (
            self.tmp_root
            / "07_LOGS"
            / "Pulse-Decks"
            / "agent-bus-enqueue-evidence"
            / "2026-05-02-agent-bus-enqueue-evidence.jsonl"
        )
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text(
            json.dumps(evidence.to_dict(), sort_keys=True) + "\n",
            encoding="utf-8",
        )
        enqueue_result = PulseAgentBusEnqueueResult(
            result_id="pulse-bus-enqueue-result-sync-schedule-001",
            validation_id="pulse-bus-approval-validation-sync-schedule-001",
            request_id=request_id,
            candidate_id=candidate_id,
            candidate_kind="feedback",
            recipient="Hermes",
            work_fingerprint=f"pulse-candidate-review:feedback:{candidate_id}",
            result_status="enqueued",
            enqueued=True,
            enqueued_at="2026-05-02T13:01:00+01:00",
            task_id="task-sync-schedule-001",
            reason="Task created on Agent Bus.",
        )
        enqueue_path = (
            self.tmp_root
            / "07_LOGS"
            / "Pulse-Decks"
            / "agent-bus-enqueue-results"
            / "2026-05-02-enqueue-results.jsonl"
        )
        enqueue_path.parent.mkdir(parents=True, exist_ok=True)
        enqueue_path.write_text(
            json.dumps(enqueue_result.to_dict(), sort_keys=True) + "\n",
            encoding="utf-8",
        )
        decision = PulseCandidateReviewDecision(
            decision_id="pulse-review-decision-applied-audit-sync-schedule-001",
            candidate_id=candidate_id,
            candidate_kind="feedback",
            decision_type="accept_for_future_ranking",
            reviewer="Hermes",
            followup_signals=DECISION_FOLLOWUP_SIGNALS["accept_for_future_ranking"],
        )
        persist_review_decision(self.tmp_root, decision)
        registry_path = (
            self.tmp_root
            / "07_LOGS"
            / "Pulse-Decks"
            / "apply-registry"
            / "applied-decisions.json"
        )
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            json.dumps({"applied_decision_ids": [decision.decision_id]}),
            encoding="utf-8",
        )
        agents_dir = self.tmp_root / "06_AGENTS"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "ChaseOS-Pulse-Post-Apply-Truth-State-Audit.md").write_text(
            "# Audit\n\nStatus: PASS\n",
            encoding="utf-8",
        )
        (agents_dir / "ChaseOS-Pulse-RnD-Workbook-Update-Approval.md").write_text(
            "# Approval Packet\n\nStatus: NO-WRITE APPROVAL PACKET\n",
            encoding="utf-8",
        )
        (agents_dir / "ChaseOS-Pulse-Native-Schedule-Activation-Catchup-Proof.md").write_text(
            "# Schedule Proof\n\nStatus: PROOF ONLY — NO SCHEDULE ACTIVATION\n",
            encoding="utf-8",
        )
        self._write_fake_pulse_workbook()

        status = build_pulse_completion_status(
            self.tmp_root,
            generated_at="2026-05-02T13:05:00+01:00",
        )
        schedule_item = next(
            item for item in status.items if item.area == "native_schedule_activation_proof"
        )

        self.assertEqual(schedule_item.status, "complete")
        self.assertNotIn(
            "native_schedule_activation_catchup_proof_not_done",
            status.blocked_reasons,
        )
        self.assertEqual(status.blocked_reasons, ("phase10_ui_not_built",))
        self.assertTrue(status.backend_control_plane_done)
        self.assertFalse(status.feature_done)
        self.assertEqual(status.overall_status, "phase10_ui_pending")
        self.assertEqual(status.next_recommended_pass, "chaseos-pulse-phase10-ui")
        self.assertFalse(status.schedule_activation_allowed)

    def test_phase10_ui_proof_closes_current_pulse_completion_without_authority_expansion(self) -> None:
        self._write_complete_backend_chain_with_schedule_proof()
        agents_dir = self.tmp_root / "06_AGENTS"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "ChaseOS-Pulse-Phase10-UI-Proof.md").write_text(
            "# Phase 10 UI Proof\n\nStatus: LOCAL UI FOOTHOLD COMPLETE\n",
            encoding="utf-8",
        )
        shell_dir = self.tmp_root / "runtime" / "studio" / "shell"
        shell_dir.mkdir(parents=True, exist_ok=True)
        (shell_dir / "api.py").write_text(
            "# test evidence only\n",
            encoding="utf-8",
        )

        status = build_pulse_completion_status(
            self.tmp_root,
            generated_at="2026-05-02T14:10:00+01:00",
        )
        ui_item = next(item for item in status.items if item.area == "phase10_ui")

        self.assertEqual(ui_item.status, "complete")
        self.assertTrue(ui_item.complete_for_feature_done)
        self.assertEqual(status.blocked_reasons, ())
        self.assertTrue(status.backend_control_plane_done)
        self.assertTrue(status.feature_done)
        self.assertEqual(status.overall_status, "complete")
        self.assertEqual(
            status.next_recommended_pass,
            "chaseos-pulse-post-completion-hardening",
        )
        self.assertFalse(status.schedule_activation_allowed)
        self.assertFalse(status.canonical_writeback_allowed)
        self.assertFalse(status.provider_or_connector_call_allowed)
        self.assertFalse(status.agent_bus_task_written)
        self.assertFalse(status.rd_workbook_update_allowed)

    def test_complete_status_exposes_read_only_post_completion_hardening_boundary(self) -> None:
        self._write_complete_backend_chain_with_schedule_proof()
        agents_dir = self.tmp_root / "06_AGENTS"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "ChaseOS-Pulse-Phase10-UI-Proof.md").write_text(
            "# Phase 10 UI Proof\n\nStatus: LOCAL UI FOOTHOLD COMPLETE\n",
            encoding="utf-8",
        )
        shell_dir = self.tmp_root / "runtime" / "studio" / "shell"
        shell_dir.mkdir(parents=True, exist_ok=True)
        (shell_dir / "api.py").write_text(
            "# test evidence only\n",
            encoding="utf-8",
        )

        status = build_pulse_completion_status(
            self.tmp_root,
            generated_at="2026-05-02T15:00:00+01:00",
        )
        hardening = status.post_completion_hardening

        self.assertEqual(status.next_recommended_pass, "chaseos-pulse-post-completion-hardening")
        self.assertEqual(hardening["status"], "ready")
        self.assertTrue(hardening["read_only_hardening_allowed"])
        self.assertFalse(hardening["requires_operator_permission_for_read_only_hardening"])
        self.assertEqual(hardening["current_pass_permission_request"], "not_required")
        self.assertIn("schedule_activation", hardening["approval_required_for"])
        self.assertIn("provider_or_connector_call", hardening["approval_required_for"])
        self.assertIn("canonical_writeback", hardening["approval_required_for"])
        self.assertIn("rd_workbook_update", hardening["approval_required_for"])
        self.assertIn("full_studio_product_ui_or_deployment", hardening["approval_required_for"])
        self.assertFalse(status.schedule_activation_allowed)
        self.assertFalse(status.provider_or_connector_call_allowed)
        self.assertFalse(status.canonical_writeback_allowed)
        self.assertFalse(status.rd_workbook_update_allowed)

    def test_rejects_authority_flags(self) -> None:
        status = build_pulse_completion_status(
            self.tmp_root,
            generated_at="2026-05-01T21:43:00+01:00",
        )
        for flag in (
            "writes_status_artifact",
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
                    type(status)(
                        generated_at=status.generated_at,
                        overall_status=status.overall_status,
                        feature_done=status.feature_done,
                        backend_control_plane_done=status.backend_control_plane_done,
                        next_recommended_pass=status.next_recommended_pass,
                        blocked_reasons=status.blocked_reasons,
                        items=status.items,
                        **{flag: True},
                    ).validate()


if __name__ == "__main__":
    unittest.main()
