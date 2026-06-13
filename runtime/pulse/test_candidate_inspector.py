"""Tests for the read-only unified Pulse candidate inspector."""

from __future__ import annotations

import shutil
import unittest
from pathlib import Path

from runtime.agents.execution_repair_memory import ExecutionRepairMemoryEntry, RepairPattern
from runtime.agents.repair_candidate_store import (
    build_execution_repair_memory_candidate,
    persist_execution_repair_memory_candidate,
)
from runtime.memory.candidate_store import (
    build_personal_map_node_candidate,
    persist_personal_map_candidate,
)
from runtime.memory.personal_map import PersonalMapNode
from runtime.pulse.candidate_inspector import (
    INSPECTOR_BLOCKED_EFFECTS,
    PulseCandidateInspectorItem,
    build_candidate_inspector_snapshot,
    discover_candidate_inspector_sources,
)
from runtime.pulse.feedback import (
    PulseFeedbackRecord,
    load_feedback_candidates,
    persist_feedback_candidate,
)
from runtime.pulse.review_decision_log import build_review_decision, persist_review_decision


_TMP_ROOT = Path(__file__).resolve().parent / "_tmp_candidate_inspector"


class PulseCandidateInspectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = _TMP_ROOT
        self._clean_tmp_root()
        self.tmp_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._clean_tmp_root()

    def _clean_tmp_root(self) -> None:
        if self.tmp_root.exists():
            resolved = self.tmp_root.resolve()
            if resolved.name != "_tmp_candidate_inspector":
                raise AssertionError(f"refusing to remove unexpected path: {resolved}")
            shutil.rmtree(resolved)

    def _persist_feedback_candidate(self):
        deck_path = self.tmp_root / "07_LOGS" / "Pulse-Decks" / "users" / "2026-04-30-user-pulse.json"
        deck_path.parent.mkdir(parents=True, exist_ok=True)
        deck_path.write_text('{"deck_id": "pulse-deck-test", "cards": []}', encoding="utf-8")
        artifact = persist_feedback_candidate(
            self.tmp_root,
            PulseFeedbackRecord(
                feedback_id="feedback-001",
                card_id="pulse-card-001",
                feedback_type="thumbs_up",
                operator_note="Keep this signal visible.",
                created_at="2026-04-30T03:30:00+01:00",
            ),
            source_deck_path=deck_path,
        )
        candidate = load_feedback_candidates(self.tmp_root)[0]
        return candidate, artifact

    def _persist_personal_map_candidate(self):
        candidate = build_personal_map_node_candidate(
            PersonalMapNode(
                node_id="personal_domain_business_os",
                node_type="business_os",
                label="Business OS",
                summary="Business operating domain candidate.",
            ),
            reason="Pulse inferred a recurring Business OS operating domain.",
            source_card_id="pulse-card-002",
            source_deck_path="07_LOGS/Pulse-Decks/users/2026-04-30-user-pulse.json",
            created_at="2026-04-30T03:35:00+01:00",
        )
        artifact = persist_personal_map_candidate(self.tmp_root, candidate)
        return candidate, artifact

    def _persist_repair_candidate(self):
        entry = ExecutionRepairMemoryEntry(
            repair_id="repair-openflow-001",
            runtime_id="openflow",
            workflow_id="shopify_upload",
            failure_surface="browser",
            failure_type="missing_product_assets",
            failure_summary="Shopify upload could not continue without product assets.",
            resolution_summary="Runtime deferred upload and requested manual input.",
            repair_pattern=RepairPattern(
                trigger="product assets are absent before upload",
                workaround="stop before publish and create a manual input card",
                recommended_response=["request product image batch"],
                future_prevention=["add preflight asset check"],
            ),
            source_logs=["07_LOGS/Agent-Activity/openflow/example.md"],
        )
        candidate = build_execution_repair_memory_candidate(
            entry,
            reason="Reusable browser-work repair pattern for later review.",
            source_card_id="pulse-agent-card-001",
            source_deck_path="07_LOGS/Pulse-Decks/users/2026-04-30-user-pulse.json",
            created_at="2026-04-30T03:40:00+01:00",
        )
        artifact = persist_execution_repair_memory_candidate(self.tmp_root, candidate)
        return candidate, artifact

    def _seed_all_lanes(self):
        feedback_candidate, feedback_artifact = self._persist_feedback_candidate()
        personal_candidate, personal_artifact = self._persist_personal_map_candidate()
        repair_candidate, repair_artifact = self._persist_repair_candidate()
        decision = build_review_decision(
            feedback_candidate,
            decision_type="accept_for_future_ranking",
            reviewer="operator",
            operator_note="Useful enough to influence future ranking.",
            source_candidate_log_path=feedback_artifact.path,
            created_at="2026-04-30T03:45:00+01:00",
        )
        decision_artifact = persist_review_decision(self.tmp_root, decision)
        return {
            "feedback": feedback_candidate,
            "feedback_artifact": feedback_artifact,
            "personal_map": personal_candidate,
            "personal_artifact": personal_artifact,
            "repair": repair_candidate,
            "repair_artifact": repair_artifact,
            "decision": decision,
            "decision_artifact": decision_artifact,
        }

    def test_empty_snapshot_does_not_create_candidate_folders(self) -> None:
        snapshot = build_candidate_inspector_snapshot(self.tmp_root)

        self.assertEqual(snapshot.item_count, 0)
        self.assertEqual(discover_candidate_inspector_sources(self.tmp_root), [])
        self.assertFalse((self.tmp_root / "07_LOGS").exists())
        self.assertEqual(snapshot.writes, [])
        self.assertEqual(snapshot.inspector_status, "read_only")

    def test_snapshot_unifies_candidates_and_review_decisions(self) -> None:
        seeded = self._seed_all_lanes()
        before = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        snapshot = build_candidate_inspector_snapshot(self.tmp_root)
        after = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        self.assertEqual(before, after)
        self.assertEqual(snapshot.item_count, 4)
        self.assertEqual(snapshot.counts_by_kind["feedback_candidate"], 1)
        self.assertEqual(snapshot.counts_by_kind["personal_map_candidate"], 1)
        self.assertEqual(snapshot.counts_by_kind["execution_repair_candidate"], 1)
        self.assertEqual(snapshot.counts_by_kind["review_decision"], 1)
        self.assertEqual(
            snapshot.decision_counts_by_candidate_id,
            {seeded["feedback"].candidate_id: 1},
        )
        self.assertEqual(set(snapshot.to_dict()["blocked_effects"]), set(INSPECTOR_BLOCKED_EFFECTS))
        self.assertFalse(snapshot.canonical_writeback_allowed)
        self.assertFalse(snapshot.applies_effects)
        self.assertFalse(snapshot.second_datastore_write_allowed)
        self.assertEqual(snapshot.writes, [])

    def test_snapshot_carries_source_paths_and_runtime_refs(self) -> None:
        seeded = self._seed_all_lanes()

        snapshot = build_candidate_inspector_snapshot(self.tmp_root)
        source_paths = set(snapshot.source_log_paths)
        repair_items = [
            item for item in snapshot.items if item.item_kind == "execution_repair_candidate"
        ]
        decision_items = [item for item in snapshot.items if item.item_kind == "review_decision"]

        self.assertIn(seeded["feedback_artifact"].path, source_paths)
        self.assertIn(seeded["personal_artifact"].path, source_paths)
        self.assertIn(seeded["repair_artifact"].path, source_paths)
        self.assertIn(seeded["decision_artifact"].path, source_paths)
        self.assertEqual(repair_items[0].runtime_id, "openflow")
        self.assertEqual(repair_items[0].target_ref, "repair-openflow-001")
        self.assertEqual(decision_items[0].related_candidate_id, seeded["feedback"].candidate_id)
        self.assertEqual(decision_items[0].followup_signals, ("future_ranking_signal",))

    def test_filters_by_item_kind_candidate_kind_and_candidate_id(self) -> None:
        seeded = self._seed_all_lanes()

        repair_only = build_candidate_inspector_snapshot(
            self.tmp_root,
            item_kinds={"execution_repair_candidate"},
        )
        feedback_related = build_candidate_inspector_snapshot(
            self.tmp_root,
            candidate_id=seeded["feedback"].candidate_id,
        )
        personal_kind = build_candidate_inspector_snapshot(
            self.tmp_root,
            candidate_kinds={"personal_map"},
        )

        self.assertEqual(repair_only.item_count, 1)
        self.assertEqual(repair_only.items[0].runtime_id, "openflow")
        self.assertEqual(feedback_related.item_count, 2)
        self.assertEqual(
            {item.item_kind for item in feedback_related.items},
            {"feedback_candidate", "review_decision"},
        )
        self.assertEqual(personal_kind.item_count, 1)
        self.assertEqual(personal_kind.items[0].candidate_kind, "personal_map")

    def test_rejects_invalid_filters(self) -> None:
        with self.assertRaises(ValueError):
            build_candidate_inspector_snapshot(self.tmp_root, item_kinds={"apply_action"})
        with self.assertRaises(ValueError):
            build_candidate_inspector_snapshot(self.tmp_root, candidate_kinds={"knowledge"})

    def test_rejects_apply_or_second_datastore_flags_on_items(self) -> None:
        item = PulseCandidateInspectorItem(
            item_id="candidate-001",
            item_kind="feedback_candidate",
            record_id="candidate-001",
            status="pending_review",
            title="Feedback candidate",
        ).to_dict()

        for forbidden_flag in (
            "inspector_read_only",
            "applies_effects",
            "canonical_writeback_allowed",
            "mutates_canonical_state",
            "second_datastore_write_allowed",
        ):
            payload = dict(item)
            payload[forbidden_flag] = False if forbidden_flag == "inspector_read_only" else True
            with self.subTest(forbidden_flag=forbidden_flag):
                with self.assertRaises(ValueError):
                    PulseCandidateInspectorItem(**payload).validate()


if __name__ == "__main__":
    unittest.main()
