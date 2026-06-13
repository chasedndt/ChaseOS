"""Audit guard tests for the Pulse Agent Bus review queue preview."""

from __future__ import annotations

import inspect
import shutil
import unittest
from pathlib import Path

import runtime.pulse.bus_review_queue as queue_module
from runtime.agents.execution_repair_memory import ExecutionRepairMemoryEntry, RepairPattern
from runtime.agents.repair_candidate_store import (
    build_execution_repair_memory_candidate,
    persist_execution_repair_memory_candidate,
)
from runtime.memory.candidate_store import build_personal_map_node_candidate, persist_personal_map_candidate
from runtime.memory.personal_map import PersonalMapNode
from runtime.pulse.bus_review_queue import build_agent_bus_review_queue_preview
from runtime.pulse.feedback import PulseFeedbackRecord, persist_feedback_candidate
from runtime.pulse.review_decision_log import build_review_decision, persist_review_decision


_TMP_ROOT = Path(__file__).resolve().parent / "_tmp_bus_review_queue_audit"


class PulseBusReviewQueueAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = _TMP_ROOT
        self._clean_tmp_root()
        self.tmp_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._clean_tmp_root()

    def _clean_tmp_root(self) -> None:
        if self.tmp_root.exists():
            resolved = self.tmp_root.resolve()
            if resolved.name != "_tmp_bus_review_queue_audit":
                raise AssertionError(f"refusing to remove unexpected path: {resolved}")
            shutil.rmtree(resolved)

    def _seed_feedback_candidate(self):
        deck_path = self.tmp_root / "07_LOGS" / "Pulse-Decks" / "users" / "2026-04-30-user-pulse.json"
        deck_path.parent.mkdir(parents=True, exist_ok=True)
        deck_path.write_text('{"deck_id": "pulse-deck-test", "cards": []}', encoding="utf-8")
        return persist_feedback_candidate(
            self.tmp_root,
            PulseFeedbackRecord(
                feedback_id="feedback-audit-001",
                card_id="pulse-card-audit-001",
                feedback_type="show_more_like_this",
                operator_note="Keep this runtime blocker visible.",
                created_at="2026-04-30T08:40:00+01:00",
            ),
            source_deck_path=deck_path,
        )

    def _seed_personal_map_candidate(self):
        candidate = build_personal_map_node_candidate(
            PersonalMapNode(
                node_id="personal_domain_business_os",
                node_type="business_os",
                label="Business OS",
                summary="Business domain candidate.",
            ),
            reason="Pulse inferred a domain candidate.",
            source_card_id="pulse-card-audit-002",
            source_deck_path="07_LOGS/Pulse-Decks/users/2026-04-30-user-pulse.json",
            created_at="2026-04-30T08:41:00+01:00",
        )
        return persist_personal_map_candidate(self.tmp_root, candidate)

    def _seed_repair_candidate(self):
        entry = ExecutionRepairMemoryEntry(
            repair_id="repair-openflow-audit-001",
            runtime_id="openflow",
            workflow_id="shopify_upload",
            failure_surface="browser",
            failure_type="missing_product_assets",
            failure_summary="Upload could not continue without product images.",
            resolution_summary="Runtime stopped and requested manual input.",
            repair_pattern=RepairPattern(
                trigger="missing product images",
                workaround="request assets before continuing",
                recommended_response=["create Manual Input Needed card"],
                future_prevention=["add image preflight check"],
            ),
            source_logs=["07_LOGS/Agent-Activity/openflow/audit-example.md"],
        )
        candidate = build_execution_repair_memory_candidate(
            entry,
            reason="Reusable execution repair candidate.",
            source_card_id="pulse-agent-card-audit-001",
            source_deck_path="07_LOGS/Pulse-Decks/users/2026-04-30-user-pulse.json",
            created_at="2026-04-30T08:42:00+01:00",
        )
        return persist_execution_repair_memory_candidate(self.tmp_root, candidate)

    def test_queue_preview_module_does_not_import_agent_bus_writer_or_backend(self) -> None:
        source = inspect.getsource(queue_module)

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

    def test_queue_preview_is_in_memory_only_for_all_candidate_lanes(self) -> None:
        self._seed_feedback_candidate()
        self._seed_personal_map_candidate()
        self._seed_repair_candidate()
        before = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        preview = build_agent_bus_review_queue_preview(
            self.tmp_root,
            recipient_by_candidate_kind={"execution_repair": "OpenClaw"},
            requested_by="codex-audit",
            created_at="2026-04-30T08:45:00+01:00",
        )
        after = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        self.assertEqual(before, after)
        self.assertEqual(preview.queue_status, "read_only")
        self.assertEqual(preview.contract_count, 3)
        self.assertEqual(preview.counts_by_recipient, {"Hermes": 2, "OpenClaw": 1})
        self.assertEqual(preview.writes, [])
        self.assertFalse(preview.bus_task_creation_allowed)
        self.assertFalse(preview.bus_tasks_written)
        self.assertFalse(preview.approval_requests_written)
        self.assertFalse(preview.writes_performed)
        self.assertFalse(preview.candidate_apply_allowed)
        self.assertFalse(preview.live_runtime_dispatch_allowed)
        self.assertFalse(preview.canonical_writeback_allowed)
        self.assertFalse(preview.second_datastore_write_allowed)
        self.assertFalse((self.tmp_root / ".chaseos").exists())

    def test_task_previews_remain_non_enqueueable(self) -> None:
        self._seed_feedback_candidate()

        preview = build_agent_bus_review_queue_preview(self.tmp_root)
        task_preview = preview.agent_bus_task_previews[0]
        contract = preview.contracts[0]

        self.assertEqual(task_preview["intent"], "REVIEW")
        self.assertEqual(task_preview["sender"], "Operator")
        self.assertEqual(task_preview["recipient"], "Hermes")
        self.assertTrue(task_preview["allow_external_sender_required"])
        self.assertFalse(task_preview["bus_task_creation_allowed"])
        self.assertFalse(contract.bus_task_creation_allowed)
        self.assertFalse(contract.bus_task_written)
        self.assertFalse(contract.approval_request_written)
        self.assertIn("Do not apply", contract.request)

    def test_review_decisions_do_not_create_additional_review_contracts(self) -> None:
        feedback_artifact = self._seed_feedback_candidate()
        candidate_preview = build_agent_bus_review_queue_preview(self.tmp_root)
        candidate_id = candidate_preview.contracts[0].candidate_id

        from runtime.pulse.feedback import load_feedback_candidates

        feedback_candidate = load_feedback_candidates(self.tmp_root)[0]
        decision = build_review_decision(
            feedback_candidate,
            decision_type="request_more_context",
            reviewer="operator",
            operator_note="Ask for better evidence before any future apply.",
            source_candidate_log_path=feedback_artifact.path,
            created_at="2026-04-30T08:46:00+01:00",
        )
        persist_review_decision(self.tmp_root, decision)

        preview = build_agent_bus_review_queue_preview(self.tmp_root, candidate_id=candidate_id)

        self.assertEqual(preview.contract_count, 1)
        self.assertEqual(preview.contracts[0].candidate_id, candidate_id)
        self.assertEqual(preview.contracts[0].source_item_kind, "feedback_candidate")

    def test_empty_read_does_not_create_queue_or_candidate_folders(self) -> None:
        preview = build_agent_bus_review_queue_preview(self.tmp_root)

        self.assertEqual(preview.contract_count, 0)
        self.assertEqual(preview.source_log_paths, [])
        self.assertFalse((self.tmp_root / "07_LOGS").exists())
        self.assertFalse((self.tmp_root / ".chaseos").exists())


if __name__ == "__main__":
    unittest.main()
