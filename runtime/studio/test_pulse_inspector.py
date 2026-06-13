"""Tests for Studio Pulse Inspector."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from runtime.studio import pulse_inspector as inspector


def _test_vault(name: str) -> Path:
    path = (
        Path(__file__).resolve().parents[2]
        / ".pytest-tmp"
        / "studio-pulse-inspector"
        / name
    )
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_deck(vault: Path, audience: str, filename: str, data: dict) -> None:
    d = vault / "07_LOGS" / "Pulse-Decks" / audience
    d.mkdir(parents=True, exist_ok=True)
    (d / filename).write_text(json.dumps(data), encoding="utf-8")


def _write_jsonl(vault: Path, subdir: str, filename: str, records: list[dict]) -> None:
    d = vault / "07_LOGS" / "Pulse-Decks" / subdir
    d.mkdir(parents=True, exist_ok=True)
    lines = "\n".join(json.dumps(r) for r in records)
    (d / filename).write_text(lines + "\n", encoding="utf-8")


# ── TestBoundarySentinel ──────────────────────────────────────────────────────

class TestBoundarySentinel(unittest.TestCase):
    def test_no_write_flags(self):
        b = inspector._BOUNDARY
        self.assertFalse(b["writes_candidate_logs"])
        self.assertFalse(b["writes_review_decisions"])
        self.assertFalse(b["applies_candidates"])
        self.assertFalse(b["grants_approvals"])
        self.assertFalse(b["triggers_execution"])
        self.assertFalse(b["canonical_mutation_allowed"])

    def test_read_flags(self):
        b = inspector._BOUNDARY
        self.assertTrue(b["reads_pulse_deck_files"])
        self.assertTrue(b["reads_candidate_logs"])
        self.assertTrue(b["reads_review_decision_logs"])
        self.assertTrue(b["reads_enqueue_result_logs"])
        self.assertTrue(b["reads_approval_request_logs"])


# ── TestLoadDeckJson ──────────────────────────────────────────────────────────

class TestLoadDeckJson(unittest.TestCase):
    def test_missing_file_returns_none(self, tmp_path=None):
        vault = _test_vault("load-deck-missing")
        result = inspector._load_deck_json(vault / "nonexistent.json")
        self.assertIsNone(result)

    def test_valid_json_returned(self):
        vault = _test_vault("load-deck-valid")
        p = vault / "deck.json"
        p.write_text(json.dumps({"deck_id": "d1", "cards": []}), encoding="utf-8")
        result = inspector._load_deck_json(p)
        self.assertEqual(result["deck_id"], "d1")

    def test_malformed_json_returns_none(self):
        vault = _test_vault("load-deck-malformed")
        p = vault / "deck.json"
        p.write_text("{not valid json", encoding="utf-8")
        result = inspector._load_deck_json(p)
        self.assertIsNone(result)


# ── TestLoadJsonlRecords ──────────────────────────────────────────────────────

class TestLoadJsonlRecords(unittest.TestCase):
    def test_missing_file_returns_empty(self):
        vault = _test_vault("jsonl-missing")
        result = inspector._load_jsonl_records(vault / "no.jsonl")
        self.assertEqual(result, [])

    def test_valid_lines_returned(self):
        vault = _test_vault("jsonl-valid")
        p = vault / "test.jsonl"
        p.write_text('{"a":1}\n{"b":2}\n', encoding="utf-8")
        result = inspector._load_jsonl_records(p)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["a"], 1)

    def test_malformed_lines_skipped(self):
        vault = _test_vault("jsonl-malformed")
        p = vault / "test.jsonl"
        p.write_text('{"a":1}\nnot json\n{"b":2}\n', encoding="utf-8")
        result = inspector._load_jsonl_records(p)
        self.assertEqual(len(result), 2)

    def test_empty_lines_skipped(self):
        vault = _test_vault("jsonl-empty-lines")
        p = vault / "test.jsonl"
        p.write_text('\n{"a":1}\n\n', encoding="utf-8")
        result = inspector._load_jsonl_records(p)
        self.assertEqual(len(result), 1)


# ── TestGetPulseSummary ───────────────────────────────────────────────────────

class TestGetPulseSummary(unittest.TestCase):
    def test_empty_vault_returns_ok(self):
        vault = _test_vault("summary-empty")
        result = inspector.get_pulse_summary(vault)
        self.assertTrue(result["ok"])
        self.assertEqual(result["surface"], "studio_pulse_inspector")
        self.assertEqual(result["total_decks"], 0)
        self.assertEqual(result["total_candidates"], 0)
        self.assertIn("boundary", result)

    def test_decks_counted_by_audience(self):
        vault = _test_vault("summary-decks")
        _write_deck(vault, "users", "d1.json", {"deck_id": "d1", "audience": "user", "cards": []})
        _write_deck(vault, "users", "d2.json", {"deck_id": "d2", "audience": "user", "cards": []})
        _write_deck(vault, "agents", "d3.json", {"deck_id": "d3", "audience": "agent", "cards": []})
        result = inspector.get_pulse_summary(vault)
        self.assertEqual(result["total_decks"], 3)
        self.assertEqual(result["decks_by_audience"].get("users"), 2)
        self.assertEqual(result["decks_by_audience"].get("agents"), 1)

    def test_enqueue_results_counted_by_status(self):
        vault = _test_vault("summary-enqueue")
        _write_jsonl(vault, "agent-bus-enqueue-results", "2026-05-02-enqueue-results.jsonl", [
            {"result_status": "enqueued", "candidate_id": "c1"},
            {"result_status": "enqueued", "candidate_id": "c2"},
            {"result_status": "blocked", "candidate_id": "c3"},
        ])
        result = inspector.get_pulse_summary(vault)
        self.assertEqual(result["enqueue_results_by_status"].get("enqueued"), 2)
        self.assertEqual(result["enqueue_results_by_status"].get("blocked"), 1)

    def test_approval_requests_counted(self):
        vault = _test_vault("summary-approval")
        _write_jsonl(vault, "agent-bus-approval-requests", "2026-05-02-agent-bus-approval-requests.jsonl", [
            {"request_id": "r1", "status": "approval_requested"},
            {"request_id": "r2", "status": "approval_requested"},
        ])
        result = inspector.get_pulse_summary(vault)
        self.assertEqual(result["approval_requests_total"], 2)

    def test_candidate_inspector_error_fails_open(self):
        vault = _test_vault("summary-inspector-error")
        with patch(
            "runtime.pulse.candidate_inspector.build_candidate_inspector_snapshot",
            side_effect=Exception("import error"),
        ):
            result = inspector.get_pulse_summary(vault)
        self.assertTrue(result["ok"])
        self.assertEqual(result["total_candidates"], 0)
        self.assertEqual(result["counts_by_kind"], {})

    def test_boundary_present(self):
        vault = _test_vault("summary-boundary")
        result = inspector.get_pulse_summary(vault)
        self.assertEqual(result["boundary"], inspector._BOUNDARY)


# ── TestListPulseCandidates ───────────────────────────────────────────────────

class TestListPulseCandidates(unittest.TestCase):
    def _make_mock_snapshot(self, items=None):
        snapshot = MagicMock()
        items = items or []
        snapshot.items = items
        return snapshot

    def test_empty_vault_returns_ok_empty(self):
        vault = _test_vault("candidates-empty")
        with patch("runtime.pulse.candidate_inspector.build_candidate_inspector_snapshot") as mock_snap:
            mock_snap.return_value = self._make_mock_snapshot()
            result = inspector.list_pulse_candidates(vault)
        self.assertTrue(result["ok"])
        self.assertEqual(result["candidate_count"], 0)
        self.assertEqual(result["candidates"], [])

    def test_invalid_kind_filter_returns_error(self):
        vault = _test_vault("candidates-invalid-kind")
        result = inspector.list_pulse_candidates(vault, kind_filter="not_a_real_kind")
        self.assertFalse(result["ok"])
        self.assertIn("kind_filter", result["error"])

    def test_kind_filter_passed_to_snapshot(self):
        vault = _test_vault("candidates-kind-filter")
        with patch(
            "runtime.pulse.candidate_inspector.build_candidate_inspector_snapshot"
        ) as mock_snap:
            mock_snap.return_value = self._make_mock_snapshot()
            inspector.list_pulse_candidates(vault, kind_filter="feedback_candidate")
            call_kwargs = mock_snap.call_args[1]
            self.assertEqual(call_kwargs["item_kinds"], {"feedback_candidate"})

    def test_status_filter_applied(self):
        vault = _test_vault("candidates-status-filter")
        item_a = MagicMock()
        item_a.status = "pending"
        item_a.item_id = "a"
        item_a.item_kind = "feedback_candidate"
        item_a.candidate_kind = "feedback"
        item_a.title = "A"
        item_a.summary = ""
        item_a.candidate_id = "a"
        item_a.related_candidate_id = None
        item_a.decision_type = None
        item_a.created_at = "2026-05-02T00:00:00Z"
        item_a.source_log_path = None

        item_b = MagicMock()
        item_b.status = "recorded"
        item_b.item_id = "b"
        item_b.item_kind = "review_decision"
        item_b.candidate_kind = "feedback"
        item_b.title = "B"
        item_b.summary = ""
        item_b.candidate_id = None
        item_b.related_candidate_id = "a"
        item_b.decision_type = "accept_for_future_ranking"
        item_b.created_at = "2026-05-02T00:00:00Z"
        item_b.source_log_path = None

        with patch(
            "runtime.pulse.candidate_inspector.build_candidate_inspector_snapshot"
        ) as mock_snap:
            mock_snap.return_value = self._make_mock_snapshot([item_a, item_b])
            result = inspector.list_pulse_candidates(vault, status_filter="pending")
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(result["candidates"][0]["item_id"], "a")

    def test_loader_error_returns_ok_false(self):
        vault = _test_vault("candidates-loader-error")
        with patch(
            "runtime.pulse.candidate_inspector.build_candidate_inspector_snapshot",
            side_effect=Exception("db gone"),
        ):
            result = inspector.list_pulse_candidates(vault)
        self.assertFalse(result["ok"])
        self.assertIn("Failed to load", result["error"])

    def test_surface_and_boundary_present(self):
        vault = _test_vault("candidates-boundary")
        with patch("runtime.pulse.candidate_inspector.build_candidate_inspector_snapshot") as mock_snap:
            mock_snap.return_value = self._make_mock_snapshot()
            result = inspector.list_pulse_candidates(vault)
        self.assertEqual(result["surface"], "studio_pulse_inspector")
        self.assertEqual(result["boundary"], inspector._BOUNDARY)

    def test_no_filter_passes_none_to_snapshot(self):
        vault = _test_vault("candidates-no-filter")
        with patch(
            "runtime.pulse.candidate_inspector.build_candidate_inspector_snapshot"
        ) as mock_snap:
            mock_snap.return_value = self._make_mock_snapshot()
            inspector.list_pulse_candidates(vault)
            call_kwargs = mock_snap.call_args[1]
            self.assertIsNone(call_kwargs["item_kinds"])


# ── TestGetEnqueuePipelineStatus ──────────────────────────────────────────────

class TestGetEnqueuePipelineStatus(unittest.TestCase):
    def test_empty_vault_returns_ok_zeros(self):
        vault = _test_vault("enqueue-empty")
        result = inspector.get_enqueue_pipeline_status(vault)
        self.assertTrue(result["ok"])
        self.assertEqual(result["enqueue_results_total"], 0)
        self.assertEqual(result["approval_requests_total"], 0)
        self.assertEqual(result["enqueued_count"], 0)

    def test_enqueued_results_counted(self):
        vault = _test_vault("enqueue-enqueued")
        _write_jsonl(vault, "agent-bus-enqueue-results", "2026-05-02-enqueue-results.jsonl", [
            {"result_id": "r1", "result_status": "enqueued", "enqueued": True, "task_id": "task-abc", "candidate_id": "c1", "candidate_kind": "feedback", "recipient": "Hermes"},
        ])
        result = inspector.get_enqueue_pipeline_status(vault)
        self.assertEqual(result["enqueued_count"], 1)
        self.assertIn("task-abc", result["enqueued_task_ids"])

    def test_blocked_results_counted(self):
        vault = _test_vault("enqueue-blocked")
        _write_jsonl(vault, "agent-bus-enqueue-results", "2026-05-02-enqueue-results.jsonl", [
            {"result_id": "r1", "result_status": "blocked", "enqueued": False, "task_id": None, "candidate_id": "c1", "candidate_kind": "feedback", "recipient": "Hermes"},
        ])
        result = inspector.get_enqueue_pipeline_status(vault)
        self.assertEqual(result["blocked_count"], 1)
        self.assertEqual(result["enqueued_count"], 0)

    def test_duplicate_and_bus_error_counted(self):
        vault = _test_vault("enqueue-dup-error")
        _write_jsonl(vault, "agent-bus-enqueue-results", "2026-05-02-enqueue-results.jsonl", [
            {"result_id": "r1", "result_status": "duplicate_skipped", "enqueued": False, "task_id": None, "candidate_id": "c1", "candidate_kind": "feedback", "recipient": "Hermes"},
            {"result_id": "r2", "result_status": "bus_error", "enqueued": False, "task_id": None, "candidate_id": "c2", "candidate_kind": "feedback", "recipient": "Hermes"},
        ])
        result = inspector.get_enqueue_pipeline_status(vault)
        self.assertEqual(result["duplicate_count"], 1)
        self.assertEqual(result["bus_error_count"], 1)

    def test_approval_requests_present(self):
        vault = _test_vault("enqueue-approval")
        _write_jsonl(vault, "agent-bus-approval-requests", "2026-05-02-agent-bus-approval-requests.jsonl", [
            {"request_id": "req-1", "candidate_id": "c1", "candidate_kind": "feedback", "status": "approval_requested"},
        ])
        result = inspector.get_enqueue_pipeline_status(vault)
        self.assertEqual(result["approval_requests_total"], 1)
        self.assertEqual(result["approval_requests"][0]["request_id"], "req-1")

    def test_surface_and_boundary(self):
        vault = _test_vault("enqueue-boundary")
        result = inspector.get_enqueue_pipeline_status(vault)
        self.assertEqual(result["surface"], "studio_pulse_inspector")
        self.assertEqual(result["boundary"], inspector._BOUNDARY)


# ── TestListPulseDecks ────────────────────────────────────────────────────────

class TestListPulseDecks(unittest.TestCase):
    def test_empty_vault_returns_ok_empty(self):
        vault = _test_vault("decks-empty")
        result = inspector.list_pulse_decks(vault)
        self.assertTrue(result["ok"])
        self.assertEqual(result["deck_count"], 0)
        self.assertEqual(result["decks"], [])

    def test_invalid_audience_filter_returns_error(self):
        vault = _test_vault("decks-invalid-audience")
        result = inspector.list_pulse_decks(vault, audience_filter="unknown_audience")
        self.assertFalse(result["ok"])
        self.assertIn("audience_filter", result["error"])

    def test_decks_listed_with_metadata(self):
        vault = _test_vault("decks-metadata")
        _write_deck(vault, "users", "2026-05-02-user-pulse.json", {
            "deck_id": "deck-u1",
            "audience": "user",
            "generated_at": "2026-05-02T10:00:00Z",
            "deck_title": "Daily Pulse",
            "sprint_label": "sprint-1",
            "cards": [{"card_id": "c1"}, {"card_id": "c2"}],
        })
        result = inspector.list_pulse_decks(vault)
        self.assertEqual(result["deck_count"], 1)
        deck = result["decks"][0]
        self.assertEqual(deck["deck_id"], "deck-u1")
        self.assertEqual(deck["card_count"], 2)
        self.assertEqual(deck["deck_title"], "Daily Pulse")

    def test_audience_filter_limits_results(self):
        vault = _test_vault("decks-audience-filter")
        _write_deck(vault, "users", "u.json", {"deck_id": "u1", "audience": "user", "cards": []})
        _write_deck(vault, "agents", "a.json", {"deck_id": "a1", "audience": "agent", "cards": []})
        result = inspector.list_pulse_decks(vault, audience_filter="users")
        self.assertEqual(result["deck_count"], 1)
        self.assertEqual(result["decks"][0]["deck_id"], "u1")

    def test_decks_sorted_newest_first(self):
        vault = _test_vault("decks-sort")
        _write_deck(vault, "users", "old.json", {
            "deck_id": "old",
            "audience": "user",
            "generated_at": "2026-04-01T00:00:00Z",
            "cards": [],
        })
        _write_deck(vault, "users", "new.json", {
            "deck_id": "new",
            "audience": "user",
            "generated_at": "2026-05-02T00:00:00Z",
            "cards": [],
        })
        result = inspector.list_pulse_decks(vault)
        self.assertEqual(result["decks"][0]["deck_id"], "new")

    def test_surface_and_boundary(self):
        vault = _test_vault("decks-boundary")
        result = inspector.list_pulse_decks(vault)
        self.assertEqual(result["surface"], "studio_pulse_inspector")
        self.assertEqual(result["boundary"], inspector._BOUNDARY)

    def test_malformed_deck_json_skipped(self):
        vault = _test_vault("decks-malformed")
        d = vault / "07_LOGS" / "Pulse-Decks" / "users"
        d.mkdir(parents=True, exist_ok=True)
        (d / "bad.json").write_text("{not json", encoding="utf-8")
        result = inspector.list_pulse_decks(vault)
        self.assertEqual(result["deck_count"], 0)


# ── TestLiveVaultSmoke ────────────────────────────────────────────────────────

class TestLiveVaultSmoke(unittest.TestCase):
    """Reads from the real vault. Validates shape only — no content assertions."""

    VAULT = Path(__file__).resolve().parents[2]

    def test_get_pulse_summary_ok(self):
        result = inspector.get_pulse_summary(self.VAULT)
        self.assertTrue(result["ok"])
        self.assertIn("total_decks", result)
        self.assertIn("total_candidates", result)
        self.assertIn("enqueue_results_by_status", result)
        self.assertIn("approval_requests_total", result)

    def test_list_pulse_decks_ok(self):
        result = inspector.list_pulse_decks(self.VAULT)
        self.assertTrue(result["ok"])
        self.assertIn("deck_count", result)
        self.assertIsInstance(result["decks"], list)

    def test_list_pulse_candidates_ok(self):
        result = inspector.list_pulse_candidates(self.VAULT)
        self.assertTrue(result["ok"])
        self.assertIn("candidate_count", result)
        self.assertIsInstance(result["candidates"], list)

    def test_get_enqueue_pipeline_status_ok(self):
        result = inspector.get_enqueue_pipeline_status(self.VAULT)
        self.assertTrue(result["ok"])
        self.assertIn("enqueue_results_total", result)
        self.assertIn("approval_requests_total", result)
        self.assertIn("enqueued_task_ids", result)

    def test_users_deck_present_in_live_vault(self):
        result = inspector.list_pulse_decks(self.VAULT, audience_filter="users")
        self.assertTrue(result["ok"])
        self.assertGreaterEqual(result["deck_count"], 1)
