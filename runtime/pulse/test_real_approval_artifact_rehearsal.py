"""Tests for real Pulse approval-artifact rehearsal chain."""

from __future__ import annotations

import inspect
import json
import shutil
import unittest
from pathlib import Path

import runtime.pulse.real_approval_artifact_rehearsal as rehearsal_module
from runtime.pulse.real_approval_artifact_rehearsal import (
    PULSE_REAL_APPROVAL_REHEARSAL_STATUS_BLOCKED,
    PULSE_REAL_APPROVAL_REHEARSAL_STATUS_READY,
    PulseRealApprovalArtifactRehearsal,
    run_real_approval_artifact_rehearsal,
)


_TMP_ROOT = Path(__file__).resolve().parent / "_tmp_real_approval_artifact_rehearsal"


class PulseRealApprovalArtifactRehearsalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = _TMP_ROOT / self._testMethodName[:48]
        self._clean_tmp_root()
        self.tmp_root.mkdir(parents=True, exist_ok=True)
        self.deck_path = (
            self.tmp_root
            / "07_LOGS"
            / "Pulse-Decks"
            / "users"
            / "2026-05-01-user-pulse.json"
        )
        self.deck_path.parent.mkdir(parents=True, exist_ok=True)
        self.deck_path.write_text(
            json.dumps(
                {
                    "deck_id": "pulse-deck-test",
                    "audience": "user",
                    "cards": [
                        {
                            "card_id": "pulse-card-real-approval-rehearsal-001",
                            "title": "Rehearsal card",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._clean_tmp_root()

    def _clean_tmp_root(self) -> None:
        if self.tmp_root.exists():
            resolved = self.tmp_root.resolve()
            if resolved.parent.name != "_tmp_real_approval_artifact_rehearsal":
                raise AssertionError(f"refusing to remove unexpected path: {resolved}")
            shutil.rmtree(resolved, ignore_errors=True)
            try:
                resolved.parent.rmdir()
            except OSError:
                pass

    def test_module_does_not_import_agent_bus_writer(self) -> None:
        source = inspect.getsource(rehearsal_module)
        forbidden_tokens = (
            "create_task",
            "update_task_status",
            "claim_task",
            "enqueue_pulse_review_task",
            "runtime.agent_bus",
        )
        for token in forbidden_tokens:
            with self.subTest(token=token):
                self.assertNotIn(token, source)

    def test_default_rehearsal_creates_artifact_chain_but_blocks_enqueue(self) -> None:
        result = run_real_approval_artifact_rehearsal(
            self.tmp_root,
            generated_at="2026-05-01T08:00:00+01:00",
        )

        self.assertEqual(result.status, PULSE_REAL_APPROVAL_REHEARSAL_STATUS_BLOCKED)
        self.assertFalse(result.ready_for_manual_enqueue)
        self.assertFalse(result.operator_enqueue_approval_present)
        self.assertFalse(result.gate_policy_defined)
        self.assertFalse(result.external_sender_allowance_present)
        self.assertFalse(result.duplicate_work_fingerprint_reviewed)
        self.assertFalse(result.approval_granted)
        self.assertFalse(result.agent_bus_task_written)
        self.assertFalse(result.candidate_apply_allowed)
        self.assertFalse(result.canonical_writeback_allowed)
        self.assertEqual(len(result.created_artifact_paths), 3)
        for path in result.created_artifact_paths:
            self.assertTrue((self.tmp_root / path).exists())

    def test_explicit_full_evidence_makes_manual_command_preview_ready(self) -> None:
        result = run_real_approval_artifact_rehearsal(
            self.tmp_root,
            operator_enqueue_approval_present=True,
            gate_policy_defined=True,
            external_sender_allowance_present=True,
            duplicate_work_fingerprint_reviewed=True,
            generated_at="2026-05-01T08:05:00+01:00",
        )

        self.assertEqual(result.status, PULSE_REAL_APPROVAL_REHEARSAL_STATUS_READY)
        self.assertTrue(result.ready_for_manual_enqueue)
        self.assertIn("enqueue-candidate", result.supervised_rehearsal.manual_command_preview)
        self.assertFalse(result.approval_granted)
        self.assertFalse(result.live_enqueue_executed)
        self.assertFalse(result.agent_bus_task_written)

    def test_rejects_execution_authority_flags(self) -> None:
        result = run_real_approval_artifact_rehearsal(
            self.tmp_root,
            generated_at="2026-05-01T08:10:00+01:00",
        )

        for flag in (
            "approval_granted",
            "approval_executed",
            "live_enqueue_executed",
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
                    PulseRealApprovalArtifactRehearsal(
                        rehearsal_run_id=result.rehearsal_run_id,
                        generated_at=result.generated_at,
                        status=result.status,
                        source_deck_path=result.source_deck_path,
                        source_card_id=result.source_card_id,
                        feedback_type=result.feedback_type,
                        recipient=result.recipient,
                        feedback_candidate_artifact=result.feedback_candidate_artifact,
                        approval_request_artifact=result.approval_request_artifact,
                        evidence_artifact=result.evidence_artifact,
                        supervised_rehearsal=result.supervised_rehearsal,
                        created_artifact_paths=result.created_artifact_paths,
                        **{flag: True},
                    ).validate()


if __name__ == "__main__":
    unittest.main()
