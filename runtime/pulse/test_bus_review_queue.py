"""Tests for read-only Pulse Agent Bus review queue previews."""

from __future__ import annotations

import shutil
import unittest
from pathlib import Path

from runtime.agents.execution_repair_memory import ExecutionRepairMemoryEntry, RepairPattern
from runtime.agents.repair_candidate_store import (
    build_execution_repair_memory_candidate,
    persist_execution_repair_memory_candidate,
)
from runtime.memory.candidate_store import build_personal_map_node_candidate, persist_personal_map_candidate
from runtime.memory.personal_map import PersonalMapNode
from runtime.pulse.bus_review_queue import (
    PULSE_BUS_REVIEW_QUEUE_BLOCKED_EFFECTS,
    PulseAgentBusReviewQueuePreview,
    build_agent_bus_review_queue_preview,
)
from runtime.pulse.feedback import PulseFeedbackRecord, persist_feedback_candidate
from runtime.pulse.review_decision_log import build_review_decision, persist_review_decision


_TMP_ROOT = Path(__file__).resolve().parent / "_tmp_bus_review_queue"


class PulseAgentBusReviewQueuePreviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = _TMP_ROOT
        self._clean_tmp_root()
        self.tmp_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._clean_tmp_root()

    def _clean_tmp_root(self) -> None:
        if self.tmp_root.exists():
            resolved = self.tmp_root.resolve()
            if resolved.name != "_tmp_bus_review_queue":
                raise AssertionError(f"refusing to remove unexpected path: {resolved}")
            shutil.rmtree(resolved)

    def _seed_feedback_candidate(self):
        deck_path = self.tmp_root / "07_LOGS" / "Pulse-Decks" / "users" / "2026-04-30-user-pulse.json"
        deck_path.parent.mkdir(parents=True, exist_ok=True)
        deck_path.write_text('{"deck_id": "pulse-deck-test", "cards": []}', encoding="utf-8")
        return persist_feedback_candidate(
            self.tmp_root,
            PulseFeedbackRecord(
                feedback_id="feedback-001",
                card_id="pulse-card-001",
                feedback_type="show_less_like_this",
                operator_note="Reduce low-value repeats.",
                created_at="2026-04-30T06:00:00+01:00",
            ),
            source_deck_path=deck_path,
        )

    def _seed_personal_map_candidate(self):
        candidate = build_personal_map_node_candidate(
            PersonalMapNode(
                node_id="personal_domain_business_os",
                node_type="business_os",
                label="Business OS",
                summary="Business operating domain candidate.",
            ),
            reason="Pulse inferred a repeated operating domain.",
            source_card_id="pulse-card-002",
            source_deck_path="07_LOGS/Pulse-Decks/users/2026-04-30-user-pulse.json",
            created_at="2026-04-30T06:05:00+01:00",
        )
        return persist_personal_map_candidate(self.tmp_root, candidate)

    def _seed_repair_candidate(self):
        entry = ExecutionRepairMemoryEntry(
            repair_id="repair-openflow-001",
            runtime_id="openflow",
            workflow_id="shopify_upload",
            failure_surface="browser",
            failure_type="missing_product_assets",
            failure_summary="Upload could not continue without product media.",
            resolution_summary="Runtime stopped and requested manual input.",
            repair_pattern=RepairPattern(
                trigger="missing product images",
                workaround="request assets before upload",
                recommended_response=["create Manual Input Needed card"],
                future_prevention=["add preflight asset check"],
            ),
            source_logs=["07_LOGS/Agent-Activity/openflow/example.md"],
        )
        candidate = build_execution_repair_memory_candidate(
            entry,
            reason="Reusable runtime repair pattern.",
            source_card_id="pulse-agent-card-001",
            source_deck_path="07_LOGS/Pulse-Decks/users/2026-04-30-user-pulse.json",
            created_at="2026-04-30T06:10:00+01:00",
        )
        return persist_execution_repair_memory_candidate(self.tmp_root, candidate)

    def test_empty_queue_preview_does_not_create_candidate_or_bus_state(self) -> None:
        preview = build_agent_bus_review_queue_preview(self.tmp_root)

        self.assertEqual(preview.contract_count, 0)
        self.assertEqual(preview.queue_status, "read_only")
        self.assertEqual(preview.writes, [])
        self.assertEqual(preview.source_log_paths, [])
        self.assertFalse((self.tmp_root / "07_LOGS").exists())
        self.assertFalse((self.tmp_root / ".chaseos").exists())
        self.assertFalse(preview.bus_task_creation_allowed)
        self.assertFalse(preview.bus_tasks_written)
        self.assertEqual(set(preview.blocked_effects), set(PULSE_BUS_REVIEW_QUEUE_BLOCKED_EFFECTS))

    def test_queue_preview_builds_contracts_from_all_candidate_lanes(self) -> None:
        self._seed_feedback_candidate()
        self._seed_personal_map_candidate()
        self._seed_repair_candidate()
        before = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        preview = build_agent_bus_review_queue_preview(
            self.tmp_root,
            requested_by="codex",
            created_at="2026-04-30T06:20:00+01:00",
        )
        after = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        self.assertEqual(before, after)
        self.assertEqual(preview.contract_count, 3)
        self.assertEqual(preview.counts_by_candidate_kind["feedback"], 1)
        self.assertEqual(preview.counts_by_candidate_kind["personal_map"], 1)
        self.assertEqual(preview.counts_by_candidate_kind["execution_repair"], 1)
        self.assertEqual(preview.counts_by_recipient, {"Hermes": 3})
        self.assertEqual(len(preview.agent_bus_task_previews), 3)
        self.assertTrue(all(contract.intent == "REVIEW" for contract in preview.contracts))
        self.assertTrue(all(not contract.bus_task_creation_allowed for contract in preview.contracts))

    def test_queue_preview_filters_and_routes_by_candidate_kind(self) -> None:
        self._seed_feedback_candidate()
        self._seed_personal_map_candidate()
        self._seed_repair_candidate()

        preview = build_agent_bus_review_queue_preview(
            self.tmp_root,
            candidate_kinds={"execution_repair"},
            recipient_by_candidate_kind={"execution_repair": "OpenClaw"},
            requested_by="codex",
            created_at="2026-04-30T06:25:00+01:00",
        )

        self.assertEqual(preview.contract_count, 1)
        self.assertEqual(preview.contracts[0].candidate_kind, "execution_repair")
        self.assertEqual(preview.contracts[0].recipient, "OpenClaw")
        self.assertEqual(preview.contracts[0].runtime_id, "openflow")
        self.assertFalse(preview.live_runtime_dispatch_allowed)

    def test_queue_preview_excludes_review_decisions_from_contract_list(self) -> None:
        feedback_artifact = self._seed_feedback_candidate()
        preview_before = build_agent_bus_review_queue_preview(self.tmp_root)
        candidate_id = preview_before.contracts[0].candidate_id
        decision_candidate = next(
            item for item in preview_before.contracts if item.candidate_id == candidate_id
        )
        # Build the review decision from the candidate record loaded through the inspector
        from runtime.pulse.candidate_inspector import build_candidate_inspector_snapshot
        from runtime.pulse.feedback import load_feedback_candidates

        feedback_candidate = load_feedback_candidates(self.tmp_root)[0]
        decision = build_review_decision(
            feedback_candidate,
            decision_type="request_more_context",
            reviewer="operator",
            operator_note="Ask Hermes for stronger evidence.",
            source_candidate_log_path=feedback_artifact.path,
            created_at="2026-04-30T06:30:00+01:00",
        )
        persist_review_decision(self.tmp_root, decision)
        snapshot = build_candidate_inspector_snapshot(self.tmp_root, candidate_id=candidate_id)

        preview_after = build_agent_bus_review_queue_preview(self.tmp_root, candidate_id=candidate_id)

        self.assertEqual(snapshot.item_count, 2)
        self.assertEqual(preview_after.contract_count, 1)
        self.assertEqual(preview_after.contracts[0].candidate_id, decision_candidate.candidate_id)

    def test_limit_and_candidate_id_filter_are_read_only(self) -> None:
        feedback_artifact = self._seed_feedback_candidate()
        self._seed_personal_map_candidate()
        before = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        limited = build_agent_bus_review_queue_preview(self.tmp_root, limit=1)
        candidate_filtered = build_agent_bus_review_queue_preview(
            self.tmp_root,
            candidate_id=limited.contracts[0].candidate_id,
        )
        after = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        self.assertEqual(before, after)
        self.assertEqual(limited.contract_count, 1)
        self.assertEqual(candidate_filtered.contract_count, 1)
        self.assertIn(feedback_artifact.path, limited.source_log_paths)

    def test_invalid_limit_and_forbidden_flags_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_agent_bus_review_queue_preview(self.tmp_root, limit=-1)

        base = build_agent_bus_review_queue_preview(self.tmp_root).to_dict()
        base.pop("contract_count")
        base.pop("counts_by_candidate_kind")
        base.pop("counts_by_recipient")
        base.pop("agent_bus_task_previews")

        for forbidden_flag in (
            "bus_task_creation_allowed",
            "bus_tasks_written",
            "approval_requests_written",
            "writes_performed",
            "candidate_apply_allowed",
            "live_runtime_dispatch_allowed",
            "canonical_writeback_allowed",
            "mutates_canonical_state",
            "second_datastore_write_allowed",
            "provider_or_connector_call_allowed",
            "schedule_activation_allowed",
        ):
            payload = dict(base)
            payload[forbidden_flag] = True
            with self.subTest(forbidden_flag=forbidden_flag):
                with self.assertRaises(ValueError):
                    PulseAgentBusReviewQueuePreview(**payload).validate()


if __name__ == "__main__":
    unittest.main()
