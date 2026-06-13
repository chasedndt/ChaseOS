"""Tests for pending-review execution repair memory candidate storage."""

from __future__ import annotations

import shutil
import unittest
from pathlib import Path

from runtime.agents.execution_repair_memory import ExecutionRepairMemoryEntry, RepairPattern
from runtime.agents.repair_candidate_store import (
    REPAIR_BLOCKED_EFFECTS,
    ExecutionRepairMemoryCandidate,
    build_execution_repair_memory_candidate,
    build_execution_repair_memory_candidate_queue,
    load_execution_repair_memory_candidates,
    persist_execution_repair_memory_candidate,
)


_TMP_ROOT = Path(__file__).resolve().parent / "_tmp_repair_candidate_store"


class ExecutionRepairCandidateStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = _TMP_ROOT
        self._clean_tmp_root()
        self.tmp_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._clean_tmp_root()

    def _clean_tmp_root(self) -> None:
        if self.tmp_root.exists():
            resolved = self.tmp_root.resolve()
            if resolved.name != "_tmp_repair_candidate_store":
                raise AssertionError(f"refusing to remove unexpected path: {resolved}")
            shutil.rmtree(resolved)

    def _entry(self, runtime_id: str = "codex") -> ExecutionRepairMemoryEntry:
        return ExecutionRepairMemoryEntry(
            repair_id="repair-codex-001",
            runtime_id=runtime_id,
            workflow_id="pulse_candidate_store_scaffold",
            failure_surface="repo",
            failure_type="missing_candidate_store",
            failure_summary="Pulse had schema candidates but no pending-review repair store.",
            resolution_summary="Append a repair candidate for operator review only.",
            repair_pattern=RepairPattern(
                trigger="runtime finds a reusable repo-work workaround",
                workaround="write a pending-review repair memory candidate",
                recommended_response=["surface as Agent Pulse card"],
                future_prevention=["review before runtime memory mutation"],
            ),
            source_logs=["07_LOGS/Agent-Activity/2026-04-30-codex-example.md"],
        )

    def test_persists_and_loads_repair_candidate(self) -> None:
        candidate = build_execution_repair_memory_candidate(
            self._entry(),
            reason="Runtime repair pattern should be reviewed before memory mutation.",
            source_card_id="pulse-agent-card-001",
            created_at="2026-04-30T02:30:00+01:00",
        )

        artifact = persist_execution_repair_memory_candidate(self.tmp_root, candidate)
        loaded = load_execution_repair_memory_candidates(self.tmp_root, runtime_id="codex")

        self.assertEqual(
            artifact.path,
            "07_LOGS/Pulse-Decks/memory-candidates/runtime-repair/codex/"
            "2026-04-30-repair-candidates.jsonl",
        )
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].runtime_id, "codex")
        self.assertEqual(loaded[0].entry.failure_surface, "repo")
        self.assertTrue(loaded[0].review_required)
        self.assertTrue(loaded[0].candidate_only)
        self.assertFalse(loaded[0].applied_to_runtime_memory)
        self.assertFalse(loaded[0].updates_runtime_navigation_map)
        self.assertFalse(loaded[0].updates_agent_identity_ledger)
        self.assertFalse(loaded[0].creates_sop)
        self.assertFalse(loaded[0].grants_tool_or_connector)
        self.assertFalse(loaded[0].expands_permissions)
        self.assertFalse(loaded[0].canonical_writeback_allowed)
        self.assertFalse(loaded[0].second_datastore_write_allowed)

    def test_queue_is_read_only_and_declares_blocked_effects(self) -> None:
        persist_execution_repair_memory_candidate(
            self.tmp_root,
            build_execution_repair_memory_candidate(
                self._entry(),
                reason="Queue visibility check.",
                created_at="2026-04-30T03:00:00+01:00",
            ),
        )
        before = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        queue = build_execution_repair_memory_candidate_queue(self.tmp_root)
        after = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        self.assertEqual(before, after)
        self.assertEqual(queue.queue_status, "read_only")
        self.assertEqual(queue.item_count, 1)
        self.assertEqual(queue.pending_count, 1)
        self.assertEqual(set(queue.to_dict()["blocked_effects"]), set(REPAIR_BLOCKED_EFFECTS))
        self.assertEqual(queue.writes, [])
        self.assertFalse(queue.canonical_writeback_allowed)

    def test_empty_queue_does_not_create_candidate_folder(self) -> None:
        queue = build_execution_repair_memory_candidate_queue(self.tmp_root)

        self.assertEqual(queue.item_count, 0)
        self.assertFalse((self.tmp_root / "07_LOGS").exists())

    def test_rejects_apply_permission_or_canonical_flags(self) -> None:
        base = build_execution_repair_memory_candidate(
            self._entry(),
            reason="Rejected flag check.",
            created_at="2026-04-30T04:00:00+01:00",
        ).to_dict()

        for forbidden_flag in (
            "canonical_writeback_allowed",
            "applied_to_runtime_memory",
            "updates_runtime_navigation_map",
            "updates_agent_identity_ledger",
            "creates_sop",
            "grants_tool_or_connector",
            "expands_permissions",
            "mutates_canonical_state",
            "second_datastore_write_allowed",
        ):
            payload = dict(base)
            payload[forbidden_flag] = True
            with self.subTest(forbidden_flag=forbidden_flag):
                with self.assertRaises(ValueError):
                    ExecutionRepairMemoryCandidate.from_dict(payload)

    def test_rejects_runtime_mismatch(self) -> None:
        payload = build_execution_repair_memory_candidate(
            self._entry(runtime_id="codex"),
            reason="Runtime mismatch check.",
            created_at="2026-04-30T05:00:00+01:00",
        ).to_dict()
        payload["runtime_id"] = "hermes"

        with self.assertRaises(ValueError):
            ExecutionRepairMemoryCandidate.from_dict(payload)

    def test_rejects_candidate_log_path_outside_runtime_repair_root(self) -> None:
        outside = self.tmp_root.parent / "outside-repair-candidates.jsonl"

        with self.assertRaises(ValueError):
            load_execution_repair_memory_candidates(self.tmp_root, log_path=outside)


if __name__ == "__main__":
    unittest.main()
