"""Tests for non-mutating Pulse to Agent Bus review request contracts."""

from __future__ import annotations

import shutil
import unittest
from pathlib import Path

from runtime.agents.execution_repair_memory import ExecutionRepairMemoryEntry, RepairPattern
from runtime.agents.repair_candidate_store import (
    build_execution_repair_memory_candidate,
    persist_execution_repair_memory_candidate,
)
from runtime.pulse.bus_review_contract import (
    PULSE_BUS_DEFAULT_RECIPIENT,
    PULSE_BUS_REVIEW_BLOCKED_EFFECTS,
    PulseAgentBusReviewRequestContract,
    build_agent_bus_review_request_contract,
    build_agent_bus_review_request_contract_for_candidate,
)
from runtime.pulse.candidate_inspector import PulseCandidateInspectorItem
from runtime.pulse.feedback import PulseFeedbackRecord, load_feedback_candidates, persist_feedback_candidate
from runtime.pulse.review_decision_log import build_review_decision, persist_review_decision


_TMP_ROOT = Path(__file__).resolve().parent / "_tmp_bus_review_contract"


class PulseAgentBusReviewContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = _TMP_ROOT
        self._clean_tmp_root()
        self.tmp_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._clean_tmp_root()

    def _clean_tmp_root(self) -> None:
        if self.tmp_root.exists():
            resolved = self.tmp_root.resolve()
            if resolved.name != "_tmp_bus_review_contract":
                raise AssertionError(f"refusing to remove unexpected path: {resolved}")
            shutil.rmtree(resolved)

    def _seed_feedback_candidate(self):
        deck_path = self.tmp_root / "07_LOGS" / "Pulse-Decks" / "users" / "2026-04-30-user-pulse.json"
        deck_path.parent.mkdir(parents=True, exist_ok=True)
        deck_path.write_text('{"deck_id": "pulse-deck-test", "cards": []}', encoding="utf-8")
        artifact = persist_feedback_candidate(
            self.tmp_root,
            PulseFeedbackRecord(
                feedback_id="feedback-001",
                card_id="pulse-card-001",
                feedback_type="show_more_like_this",
                operator_note="Useful runtime signal.",
                created_at="2026-04-30T04:30:00+01:00",
            ),
            source_deck_path=deck_path,
        )
        candidate = load_feedback_candidates(self.tmp_root)[0]
        return candidate, artifact

    def _seed_repair_candidate(self):
        entry = ExecutionRepairMemoryEntry(
            repair_id="repair-openflow-001",
            runtime_id="openflow",
            workflow_id="shopify_upload",
            failure_surface="browser",
            failure_type="missing_product_assets",
            failure_summary="Shopify upload could not continue without product images.",
            resolution_summary="Runtime stopped before publish and requested manual input.",
            repair_pattern=RepairPattern(
                trigger="product upload lacks assets",
                workaround="create manual input card before continuing",
                recommended_response=["request product image batch"],
                future_prevention=["add upload preflight check"],
            ),
            source_logs=["07_LOGS/Agent-Activity/openflow/example.md"],
        )
        candidate = build_execution_repair_memory_candidate(
            entry,
            reason="Reusable repair pattern for browser-runtime review.",
            source_card_id="pulse-agent-card-001",
            source_deck_path="07_LOGS/Pulse-Decks/users/2026-04-30-user-pulse.json",
            created_at="2026-04-30T04:35:00+01:00",
        )
        artifact = persist_execution_repair_memory_candidate(self.tmp_root, candidate)
        return candidate, artifact

    def test_builds_review_contract_from_inspector_item_without_bus_write(self) -> None:
        item = PulseCandidateInspectorItem(
            item_id="candidate-001",
            item_kind="feedback_candidate",
            record_id="candidate-001",
            status="pending_review",
            title="Feedback candidate",
            summary="Candidate for future ranking.",
            candidate_kind="feedback",
            candidate_id="candidate-001",
            source_log_path="07_LOGS/Pulse-Decks/feedback-candidates/2026-04-30-feedback-candidates.jsonl",
            source_deck_path="07_LOGS/Pulse-Decks/users/2026-04-30-user-pulse.json",
            source_card_id="pulse-card-001",
            target_ref="pulse-card-001",
            created_at="2026-04-30T04:30:00+01:00",
        )

        contract = build_agent_bus_review_request_contract(
            item,
            requested_by="codex",
            created_at="2026-04-30T04:40:00+01:00",
        )
        preview = contract.to_task_preview()

        self.assertEqual(contract.contract_status, "contract_ready")
        self.assertEqual(contract.intent, "REVIEW")
        self.assertEqual(contract.sender, "Operator")
        self.assertEqual(contract.recipient, PULSE_BUS_DEFAULT_RECIPIENT)
        self.assertEqual(contract.candidate_id, "candidate-001")
        self.assertTrue(contract.approval_required)
        self.assertTrue(contract.allow_external_sender_required)
        self.assertFalse(contract.bus_task_creation_allowed)
        self.assertFalse(contract.bus_task_written)
        self.assertFalse(contract.writes_performed)
        self.assertFalse(contract.candidate_apply_allowed)
        self.assertFalse(contract.canonical_writeback_allowed)
        self.assertFalse(contract.second_datastore_write_allowed)
        self.assertIn("Do not apply", contract.request)
        self.assertEqual(preview["intent"], "REVIEW")
        self.assertFalse(preview["bus_task_creation_allowed"])
        self.assertTrue(preview["allow_external_sender_required"])
        self.assertTrue(contract.work_fingerprint.startswith("pulse-candidate-review:feedback:"))
        self.assertEqual(set(contract.blocked_effects), set(PULSE_BUS_REVIEW_BLOCKED_EFFECTS))

    def test_builds_review_contract_for_candidate_from_logs_without_creating_bus_state(self) -> None:
        candidate, artifact = self._seed_feedback_candidate()
        before = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        contract = build_agent_bus_review_request_contract_for_candidate(
            self.tmp_root,
            candidate.candidate_id,
            requested_by="codex",
            created_at="2026-04-30T04:45:00+01:00",
        )
        after = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        self.assertEqual(before, after)
        self.assertEqual(contract.candidate_id, candidate.candidate_id)
        self.assertEqual(contract.source_item_kind, "feedback_candidate")
        self.assertEqual(contract.candidate_kind, "feedback")
        self.assertEqual(contract.source_log_path, artifact.path)
        self.assertEqual(contract.source_card_id, "pulse-card-001")
        self.assertFalse((self.tmp_root / ".chaseos").exists())
        self.assertFalse(contract.bus_task_written)

    def test_repair_candidate_contract_preserves_runtime_ref(self) -> None:
        candidate, _artifact = self._seed_repair_candidate()

        contract = build_agent_bus_review_request_contract_for_candidate(
            self.tmp_root,
            candidate.candidate_id,
            recipient="OpenClaw",
            requested_by="codex",
            created_at="2026-04-30T04:50:00+01:00",
        )

        self.assertEqual(contract.recipient, "OpenClaw")
        self.assertEqual(contract.candidate_kind, "execution_repair")
        self.assertEqual(contract.runtime_id, "openflow")
        self.assertEqual(contract.target_ref, "repair-openflow-001")
        self.assertIn(":openflow:", contract.work_fingerprint or "")
        self.assertIn("runtime=openflow", contract.request)
        self.assertFalse(contract.live_runtime_dispatch_allowed)

    def test_prefers_candidate_item_over_review_decision_for_candidate_id(self) -> None:
        candidate, artifact = self._seed_feedback_candidate()
        decision = build_review_decision(
            candidate,
            decision_type="request_more_context",
            reviewer="operator",
            operator_note="Ask Hermes for evidence before apply.",
            source_candidate_log_path=artifact.path,
            created_at="2026-04-30T04:55:00+01:00",
        )
        persist_review_decision(self.tmp_root, decision)

        contract = build_agent_bus_review_request_contract_for_candidate(
            self.tmp_root,
            candidate.candidate_id,
            created_at="2026-04-30T05:00:00+01:00",
        )

        self.assertEqual(contract.source_item_kind, "feedback_candidate")
        self.assertEqual(contract.candidate_id, candidate.candidate_id)

    def test_missing_candidate_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_agent_bus_review_request_contract_for_candidate(self.tmp_root, "")
        with self.assertRaises(ValueError):
            build_agent_bus_review_request_contract_for_candidate(self.tmp_root, "missing-candidate")

    def test_rejects_apply_bus_write_and_authority_expansion_flags(self) -> None:
        item = PulseCandidateInspectorItem(
            item_id="candidate-001",
            item_kind="feedback_candidate",
            record_id="candidate-001",
            status="pending_review",
            title="Feedback candidate",
            candidate_kind="feedback",
            candidate_id="candidate-001",
        )
        base = build_agent_bus_review_request_contract(
            item,
            created_at="2026-04-30T05:05:00+01:00",
        ).to_dict()
        base.pop("agent_bus_task_preview")

        forbidden_flags = (
            "approval_required",
            "allow_external_sender_required",
            "bus_task_creation_allowed",
            "bus_task_written",
            "writes_performed",
            "candidate_apply_allowed",
            "approval_request_written",
            "canonical_writeback_allowed",
            "mutates_canonical_state",
            "second_datastore_write_allowed",
            "provider_or_connector_call_allowed",
            "schedule_activation_allowed",
            "live_runtime_dispatch_allowed",
        )
        for flag in forbidden_flags:
            payload = dict(base)
            payload[flag] = False if flag in {"approval_required", "allow_external_sender_required"} else True
            with self.subTest(flag=flag):
                with self.assertRaises(ValueError):
                    PulseAgentBusReviewRequestContract(**payload).validate()


if __name__ == "__main__":
    unittest.main()
