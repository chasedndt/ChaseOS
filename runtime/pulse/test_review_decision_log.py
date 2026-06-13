"""Tests for persisted, non-applying Pulse review decisions."""

from __future__ import annotations

import shutil
import unittest
from pathlib import Path

from runtime.agents.execution_repair_memory import ExecutionRepairMemoryEntry, RepairPattern
from runtime.agents.repair_candidate_store import build_execution_repair_memory_candidate
from runtime.memory.candidate_store import build_personal_map_node_candidate
from runtime.memory.personal_map import PersonalMapNode
from runtime.pulse.feedback import PulseFeedbackCandidate
from runtime.pulse.review_decision_log import (
    REVIEW_DECISION_BLOCKED_EFFECTS,
    PulseCandidateReviewDecision,
    build_review_decision,
    build_review_decision_ledger,
    load_review_decisions,
    persist_review_decision,
)


_TMP_ROOT = Path(__file__).resolve().parent / "_tmp_review_decision_log"


class PulseReviewDecisionLogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = _TMP_ROOT
        self._clean_tmp_root()
        self.tmp_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._clean_tmp_root()

    def _clean_tmp_root(self) -> None:
        if self.tmp_root.exists():
            resolved = self.tmp_root.resolve()
            if resolved.name != "_tmp_review_decision_log":
                raise AssertionError(f"refusing to remove unexpected path: {resolved}")
            shutil.rmtree(resolved)

    def _feedback_candidate(self) -> PulseFeedbackCandidate:
        candidate = PulseFeedbackCandidate(
            candidate_id="feedback-candidate-card-001",
            feedback_id="feedback-001",
            card_id="pulse-card-001",
            feedback_type="thumbs_up",
            source_deck_path="07_LOGS/Pulse-Decks/users/2026-04-30-user-pulse.json",
            operator_note="Useful card.",
            created_at="2026-04-30T02:50:00+01:00",
        )
        candidate.validate()
        return candidate

    def _personal_map_candidate(self):
        return build_personal_map_node_candidate(
            PersonalMapNode(
                node_id="personal_domain_business_os",
                node_type="business_os",
                label="Business OS",
                summary="Candidate business operating domain.",
            ),
            reason="Pulse suggested a Personal Map update.",
            source_card_id="pulse-card-002",
            created_at="2026-04-30T02:55:00+01:00",
        )

    def _repair_candidate(self):
        entry = ExecutionRepairMemoryEntry(
            repair_id="repair-openflow-001",
            runtime_id="openflow",
            workflow_id="shopify_upload",
            failure_surface="browser",
            failure_type="missing_product_assets",
            failure_summary="Shopify upload could not continue without product assets.",
            resolution_summary="Runtime deferred upload and requested manual input.",
            repair_pattern=RepairPattern(
                trigger="product image or metadata assets are absent",
                workaround="stop before publish and create manual input card",
                recommended_response=["request product image batch"],
                future_prevention=["add preflight asset check"],
            ),
            source_logs=["07_LOGS/Agent-Activity/openflow/example.md"],
        )
        return build_execution_repair_memory_candidate(
            entry,
            reason="Reusable browser workflow repair pattern.",
            source_card_id="pulse-agent-card-001",
            created_at="2026-04-30T03:00:00+01:00",
        )

    def test_persists_feedback_review_decision_without_applying_feedback(self) -> None:
        decision = build_review_decision(
            self._feedback_candidate(),
            decision_type="accept_for_future_ranking",
            reviewer="operator",
            operator_note="Use similar cards later.",
            source_candidate_log_path=(
                "07_LOGS/Pulse-Decks/feedback-candidates/"
                "2026-04-30-feedback-candidates.jsonl"
            ),
            created_at="2026-04-30T03:10:00+01:00",
        )

        artifact = persist_review_decision(self.tmp_root, decision)
        loaded = load_review_decisions(self.tmp_root)

        self.assertEqual(
            artifact.path,
            "07_LOGS/Pulse-Decks/review-decisions/2026-04-30-review-decisions.jsonl",
        )
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].candidate_kind, "feedback")
        self.assertEqual(loaded[0].followup_signals, ("future_ranking_signal",))
        self.assertTrue(loaded[0].decision_record_only)
        self.assertTrue(loaded[0].persisted_decision)
        self.assertFalse(loaded[0].applies_feedback_to_source_deck)
        self.assertFalse(loaded[0].canonical_writeback_allowed)
        self.assertFalse(loaded[0].second_datastore_write_allowed)

    def test_persists_personal_map_review_decision_without_map_mutation(self) -> None:
        decision = build_review_decision(
            self._personal_map_candidate(),
            decision_type="approve_for_future_apply",
            operator_note="Looks right, but apply later.",
            created_at="2026-04-30T03:20:00+01:00",
        )
        persist_review_decision(self.tmp_root, decision)

        loaded = load_review_decisions(self.tmp_root, candidate_kind="personal_map")

        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].target_ref, "personal_domain_business_os")
        self.assertEqual(loaded[0].followup_signals, ("future_apply_review_signal",))
        self.assertFalse(loaded[0].applies_personal_map_update)
        self.assertIn("personal_map_mutation", loaded[0].blocked_effects)

    def test_persists_repair_review_decision_without_runtime_memory_mutation(self) -> None:
        decision = build_review_decision(
            self._repair_candidate(),
            decision_type="approve_for_future_apply",
            operator_note="Good repair candidate; do not apply yet.",
            created_at="2026-04-30T03:30:00+01:00",
        )
        persist_review_decision(self.tmp_root, decision)

        loaded = load_review_decisions(self.tmp_root, candidate_kind="execution_repair")

        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].runtime_id, "openflow")
        self.assertEqual(loaded[0].target_ref, "repair-openflow-001")
        self.assertFalse(loaded[0].applies_runtime_repair_memory)
        self.assertFalse(loaded[0].updates_runtime_navigation_map)
        self.assertFalse(loaded[0].updates_agent_identity_ledger)
        self.assertFalse(loaded[0].expands_permissions)
        self.assertIn("runtime_memory_mutation", loaded[0].blocked_effects)

    def test_ledger_snapshot_is_read_only_and_declares_blocked_effects(self) -> None:
        persist_review_decision(
            self.tmp_root,
            build_review_decision(
                self._feedback_candidate(),
                decision_type="reject_candidate",
                operator_note="Not useful.",
                created_at="2026-04-30T03:40:00+01:00",
            ),
        )
        before = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        ledger = build_review_decision_ledger(self.tmp_root)
        after = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        self.assertEqual(before, after)
        self.assertEqual(ledger.ledger_status, "read_only")
        self.assertEqual(ledger.item_count, 1)
        self.assertEqual(set(ledger.to_dict()["blocked_effects"]), set(REVIEW_DECISION_BLOCKED_EFFECTS))
        self.assertEqual(ledger.writes, [])
        self.assertFalse(ledger.canonical_writeback_allowed)
        self.assertFalse(ledger.second_datastore_write_allowed)

    def test_empty_ledger_does_not_create_decision_folder(self) -> None:
        ledger = build_review_decision_ledger(self.tmp_root)

        self.assertEqual(ledger.item_count, 0)
        self.assertFalse((self.tmp_root / "07_LOGS").exists())

    def test_rejects_decision_type_that_does_not_match_candidate_kind(self) -> None:
        with self.assertRaises(ValueError):
            build_review_decision(
                self._personal_map_candidate(),
                decision_type="accept_for_future_ranking",
                created_at="2026-04-30T03:50:00+01:00",
            )

    def test_rejects_apply_or_authority_flags(self) -> None:
        base = build_review_decision(
            self._repair_candidate(),
            decision_type="approve_for_future_apply",
            created_at="2026-04-30T04:00:00+01:00",
        ).to_dict()

        forbidden_flags = (
            "canonical_writeback_allowed",
            "applies_feedback_to_source_deck",
            "applies_personal_map_update",
            "applies_runtime_repair_memory",
            "approves_memory",
            "creates_task",
            "creates_sop",
            "updates_runtime_navigation_map",
            "updates_agent_identity_ledger",
            "expands_permissions",
            "mutates_canonical_state",
            "calls_provider_or_connector",
            "second_datastore_write_allowed",
        )
        for forbidden_flag in forbidden_flags:
            payload = dict(base)
            payload[forbidden_flag] = True
            with self.subTest(forbidden_flag=forbidden_flag):
                with self.assertRaises(ValueError):
                    PulseCandidateReviewDecision.from_dict(payload)

    def test_rejects_decision_log_path_outside_review_decision_root(self) -> None:
        outside = self.tmp_root.parent / "outside-review-decisions.jsonl"

        with self.assertRaises(ValueError):
            load_review_decisions(self.tmp_root, log_path=outside)


if __name__ == "__main__":
    unittest.main()
