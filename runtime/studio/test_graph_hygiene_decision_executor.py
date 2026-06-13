"""
Tests for graph_hygiene_decision_executor.py (Phase 3).

Coverage:
- execute_approved_decisions: annotation-only, archive, soft-delete, path traversal
- Already-applied draft is rejected
- Missing draft is rejected
- Decision log is written
- list_decision_logs: empty, populated, malformed
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.studio.graph_hygiene_decision_draft import (
    DRAFT_DIR_REL,
    create_decision_draft,
)
from runtime.studio.graph_hygiene_decision_executor import (
    LOG_DIR_REL,
    ARCHIVE_BASE,
    execute_approved_decisions,
    list_decision_logs,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_vault(tmp_path: Path) -> Path:
    """Return a vault root with one real source file and a populated draft."""
    vault = tmp_path / "vault"
    vault.mkdir()
    # Create a real source file that can be archived
    src_dir = vault / "02_KNOWLEDGE"
    src_dir.mkdir(parents=True)
    real_file = src_dir / "loose_note.md"
    real_file.write_text("# Loose Note\nContent here.", encoding="utf-8")
    return vault


def _create_draft(vault: Path, decisions: list[dict]) -> str:
    """Create a draft and return its relative path."""
    r = create_decision_draft(vault, "07_LOGS/Graph-Reports/queue.json", decisions)
    assert r["ok"] is True
    return r["draft_path"]


FAKE_APPROVAL_ID = "approval-test-00001"


# ---------------------------------------------------------------------------
# execute_approved_decisions: annotation-only decisions
# ---------------------------------------------------------------------------

class TestAnnotationOnlyDecisions:
    def test_keep_and_wire_produces_annotation_record(self, tmp_path):
        vault = _make_vault(tmp_path)
        draft_path = _create_draft(vault, [
            {"path": "02_KNOWLEDGE/loose_note.md", "decision": "keep_and_wire"},
        ])
        result = execute_approved_decisions(vault, draft_path, FAKE_APPROVAL_ID)
        assert result["ok"] is True
        assert result["applied_count"] == 1
        assert result["results"][0]["action"] == "annotation_written"
        # Source file should still exist
        assert (vault / "02_KNOWLEDGE/loose_note.md").exists()

    def test_keep_excluded_produces_annotation_record(self, tmp_path):
        vault = _make_vault(tmp_path)
        draft_path = _create_draft(vault, [
            {"path": "02_KNOWLEDGE/loose_note.md", "decision": "keep_excluded"},
        ])
        result = execute_approved_decisions(vault, draft_path, FAKE_APPROVAL_ID)
        assert result["ok"] is True
        assert result["results"][0]["action"] == "annotation_written"
        assert (vault / "02_KNOWLEDGE/loose_note.md").exists()

    def test_manual_investigation_produces_annotation_record(self, tmp_path):
        vault = _make_vault(tmp_path)
        draft_path = _create_draft(vault, [
            {"path": "02_KNOWLEDGE/loose_note.md", "decision": "manual_investigation"},
        ])
        result = execute_approved_decisions(vault, draft_path, FAKE_APPROVAL_ID)
        assert result["ok"] is True
        assert result["results"][0]["action"] == "annotation_written"

    def test_replace_with_canonical_produces_annotation_record(self, tmp_path):
        vault = _make_vault(tmp_path)
        draft_path = _create_draft(vault, [
            {"path": "02_KNOWLEDGE/loose_note.md", "decision": "replace_with_canonical"},
        ])
        result = execute_approved_decisions(vault, draft_path, FAKE_APPROVAL_ID)
        assert result["ok"] is True
        assert result["results"][0]["action"] == "annotation_written"


# ---------------------------------------------------------------------------
# execute_approved_decisions: archive actions
# ---------------------------------------------------------------------------

class TestArchiveActions:
    def test_archive_after_review_moves_file(self, tmp_path):
        vault = _make_vault(tmp_path)
        src = vault / "02_KNOWLEDGE" / "loose_note.md"
        assert src.exists()

        draft_path = _create_draft(vault, [
            {"path": "02_KNOWLEDGE/loose_note.md", "decision": "archive_after_review"},
        ])
        result = execute_approved_decisions(vault, draft_path, FAKE_APPROVAL_ID)
        assert result["ok"] is True
        assert result["applied_count"] == 1
        assert result["results"][0]["action"] == "archived"
        # File no longer at source
        assert not src.exists()
        # File exists in archive
        dest = result["results"][0].get("dest", "")
        assert dest
        assert (vault / dest).exists()

    def test_archive_noncanonical_artifact_moves_file(self, tmp_path):
        vault = _make_vault(tmp_path)
        draft_path = _create_draft(vault, [
            {"path": "02_KNOWLEDGE/loose_note.md", "decision": "archive_noncanonical_artifact"},
        ])
        result = execute_approved_decisions(vault, draft_path, FAKE_APPROVAL_ID)
        assert result["ok"] is True
        assert result["results"][0]["action"] == "archived"
        assert not (vault / "02_KNOWLEDGE/loose_note.md").exists()

    def test_archive_missing_file_produces_skipped_not_found(self, tmp_path):
        vault = _make_vault(tmp_path)
        draft_path = _create_draft(vault, [
            {"path": "02_KNOWLEDGE/nonexistent.md", "decision": "archive_after_review"},
        ])
        result = execute_approved_decisions(vault, draft_path, FAKE_APPROVAL_ID)
        assert result["ok"] is True
        assert result["skipped_count"] == 1
        assert result["results"][0]["action"] == "skipped_not_found"


# ---------------------------------------------------------------------------
# execute_approved_decisions: soft-delete
# ---------------------------------------------------------------------------

class TestSoftDelete:
    def test_delete_after_review_moves_to_deleted_subdir(self, tmp_path):
        vault = _make_vault(tmp_path)
        draft_path = _create_draft(vault, [
            {"path": "02_KNOWLEDGE/loose_note.md", "decision": "delete_after_review"},
        ])
        result = execute_approved_decisions(vault, draft_path, FAKE_APPROVAL_ID)
        assert result["ok"] is True
        assert result["applied_count"] == 1
        assert result["results"][0]["action"] == "soft_deleted"
        # File no longer at source
        assert not (vault / "02_KNOWLEDGE/loose_note.md").exists()
        # Ends up under Archive/YYYYMMDD/Deleted/
        dest = result["results"][0].get("dest", "")
        assert "Deleted" in dest
        assert (vault / dest).exists()


# ---------------------------------------------------------------------------
# execute_approved_decisions: path traversal guard
# ---------------------------------------------------------------------------

class TestPathTraversalGuard:
    def test_rejects_path_outside_vault(self, tmp_path):
        vault = _make_vault(tmp_path)
        # Manually write a draft with a path-traversal target
        draft_dir = vault / DRAFT_DIR_REL
        draft_dir.mkdir(parents=True)
        draft_data = {
            "surface": "studio_graph_hygiene_decision_draft",
            "model_version": "test",
            "draft_id": "ghd-test",
            "created_at": "2026-01-01T00:00:00+00:00",
            "created_by": "test",
            "source_queue_path": "q.json",
            "operator_note": "",
            "status": "draft_pending_operator_review",
            "decision_count": 1,
            "decisions": [{"path": "../../etc/passwd", "issue": "loose_node", "decision": "archive_after_review"}],
            "authority": {"applied": False, "canonical_mutation_allowed": False},
        }
        bad_draft_path = draft_dir / "2026-01-01T000000-graph-hygiene-decision-draft.json"
        bad_draft_path.write_text(json.dumps(draft_data), encoding="utf-8")
        rel = str(DRAFT_DIR_REL / bad_draft_path.name)

        result = execute_approved_decisions(vault, rel, FAKE_APPROVAL_ID)
        assert result["ok"] is True  # overall ok (executor ran)
        assert result["applied_count"] == 0
        assert result["skipped_count"] == 1
        assert "outside_vault" in result["results"][0]["action"]


# ---------------------------------------------------------------------------
# execute_approved_decisions: guard conditions
# ---------------------------------------------------------------------------

class TestGuardConditions:
    def test_rejects_missing_draft(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = execute_approved_decisions(
            vault, str(DRAFT_DIR_REL / "nonexistent.json"), FAKE_APPROVAL_ID
        )
        assert result["ok"] is False
        assert "not found" in result["error"].lower()

    def test_rejects_already_applied_draft(self, tmp_path):
        vault = _make_vault(tmp_path)
        draft_path = _create_draft(vault, [
            {"path": "02_KNOWLEDGE/loose_note.md", "decision": "keep_and_wire"},
        ])
        # First execution
        r1 = execute_approved_decisions(vault, draft_path, FAKE_APPROVAL_ID)
        assert r1["ok"] is True
        # Second execution on same draft — should be rejected
        r2 = execute_approved_decisions(vault, draft_path, FAKE_APPROVAL_ID)
        assert r2["ok"] is False
        assert "applied" in r2["error"].lower()


# ---------------------------------------------------------------------------
# Decision log
# ---------------------------------------------------------------------------

class TestDecisionLog:
    def test_decision_log_written_after_execution(self, tmp_path):
        vault = _make_vault(tmp_path)
        draft_path = _create_draft(vault, [
            {"path": "02_KNOWLEDGE/loose_note.md", "decision": "keep_and_wire"},
        ])
        result = execute_approved_decisions(vault, draft_path, FAKE_APPROVAL_ID)
        assert result["ok"] is True

        log_path = vault / result["log_path"]
        assert log_path.exists()
        log_data = json.loads(log_path.read_text())
        assert log_data["surface"] == "studio_graph_hygiene_decision_log"
        assert log_data["approval_id"] == FAKE_APPROVAL_ID
        assert log_data["applied_count"] == 1

    def test_draft_marked_applied_after_execution(self, tmp_path):
        vault = _make_vault(tmp_path)
        draft_path = _create_draft(vault, [
            {"path": "02_KNOWLEDGE/loose_note.md", "decision": "keep_and_wire"},
        ])
        execute_approved_decisions(vault, draft_path, FAKE_APPROVAL_ID)
        draft_data = json.loads((vault / draft_path).read_text())
        assert draft_data["authority"]["applied"] is True
        assert draft_data["status"] == "applied"

    def test_before_and_after_counts_in_result(self, tmp_path):
        vault = _make_vault(tmp_path)
        draft_path = _create_draft(vault, [
            {"path": "02_KNOWLEDGE/loose_note.md", "decision": "keep_and_wire"},
        ])
        result = execute_approved_decisions(vault, draft_path, FAKE_APPROVAL_ID)
        assert result["before_count"] == 1
        assert result["applied_count"] == 1


# ---------------------------------------------------------------------------
# list_decision_logs
# ---------------------------------------------------------------------------

class TestListDecisionLogs:
    def test_empty_when_no_log_dir(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        result = list_decision_logs(vault)
        assert result["logs"] == []
        assert result["total"] == 0

    def test_lists_logs_after_execution(self, tmp_path):
        vault = _make_vault(tmp_path)
        draft_path = _create_draft(vault, [
            {"path": "02_KNOWLEDGE/loose_note.md", "decision": "keep_and_wire"},
        ])
        execute_approved_decisions(vault, draft_path, FAKE_APPROVAL_ID)
        result = list_decision_logs(vault)
        assert result["total"] == 1
        assert result["logs"][0]["applied_count"] == 1

    def test_handles_malformed_log_gracefully(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        log_dir = vault / LOG_DIR_REL
        log_dir.mkdir(parents=True)
        (log_dir / "2026-01-01T000000-graph-hygiene-decision-log.json").write_text("BAD")
        result = list_decision_logs(vault)
        assert result["total"] == 1
        assert result["logs"][0]["status"] == "malformed"
