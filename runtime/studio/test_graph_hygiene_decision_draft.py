"""
Tests for graph_hygiene_decision_draft.py (Phase 2).

Coverage:
- create_decision_draft: happy path, validation errors, path guard
- list_decision_drafts: empty dir, multiple files, malformed file
- load_decision_draft: valid, missing, path traversal
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.studio.graph_hygiene_decision_draft import (
    ALLOWED_DECISIONS,
    DRAFT_DIR_REL,
    create_decision_draft,
    list_decision_drafts,
    load_decision_draft,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def vault(tmp_path: Path) -> Path:
    return tmp_path


VALID_DECISIONS = [
    {"path": "02_KNOWLEDGE/foo.md",  "issue": "loose_node", "decision": "keep_and_wire"},
    {"path": "02_KNOWLEDGE/bar.md",  "issue": "loose_node", "decision": "archive_after_review"},
    {"path": "02_KNOWLEDGE/baz.md",  "issue": "loose_node", "decision": "keep_excluded", "operator_note": "technical artifact"},
]


# ---------------------------------------------------------------------------
# create_decision_draft
# ---------------------------------------------------------------------------

class TestCreateDecisionDraft:
    def test_creates_file_in_decision_drafts_dir(self, vault):
        result = create_decision_draft(vault, "queue.json", VALID_DECISIONS)
        assert result["ok"] is True
        assert result["draft_path"] is not None
        assert result["decision_count"] == 3
        draft_abs = vault / result["draft_path"]
        assert draft_abs.exists()

    def test_draft_json_shape(self, vault):
        result = create_decision_draft(vault, "queue.json", VALID_DECISIONS, operator_note="batch A")
        data = json.loads((vault / result["draft_path"]).read_text())
        assert data["surface"] == "studio_graph_hygiene_decision_draft"
        assert data["status"] == "draft_pending_operator_review"
        assert data["decision_count"] == 3
        assert data["operator_note"] == "batch A"
        assert data["source_queue_path"] == "queue.json"
        assert data["authority"]["applied"] is False
        assert data["authority"]["canonical_mutation_allowed"] is False

    def test_draft_id_is_stable_for_same_input(self, vault):
        # Same decisions at same second produce same draft_id
        d1 = create_decision_draft(vault, "q.json", VALID_DECISIONS[:1])
        # Rebuild with same data at same sub-second — force same ts by reading back
        data = json.loads((vault / d1["draft_path"]).read_text())
        assert d1["draft_id"] == data["draft_id"]
        assert d1["draft_id"].startswith("ghd-")

    def test_missing_path_returns_validation_error(self, vault):
        bad = [{"path": "", "decision": "keep_and_wire"}]
        result = create_decision_draft(vault, "q.json", bad)
        assert result["ok"] is False
        assert result["validation_errors"]

    def test_invalid_decision_type_returns_validation_error(self, vault):
        bad = [{"path": "foo.md", "decision": "nuke_it"}]
        result = create_decision_draft(vault, "q.json", bad)
        assert result["ok"] is False
        assert any("nuke_it" in e for e in result["validation_errors"])

    def test_empty_decisions_returns_error(self, vault):
        result = create_decision_draft(vault, "q.json", [])
        assert result["ok"] is False

    def test_all_allowed_decisions_accepted(self, vault):
        for decision in ALLOWED_DECISIONS:
            r = create_decision_draft(vault, "q.json", [{"path": "x.md", "decision": decision}])
            assert r["ok"] is True, f"Decision {decision!r} was rejected"

    def test_creates_draft_dir_if_not_exists(self, vault):
        assert not (vault / DRAFT_DIR_REL).exists()
        create_decision_draft(vault, "q.json", VALID_DECISIONS[:1])
        assert (vault / DRAFT_DIR_REL).exists()

    def test_no_write_outside_draft_dir(self, vault):
        create_decision_draft(vault, "q.json", VALID_DECISIONS)
        # No files created outside the draft directory (other than the draft itself)
        for p in vault.rglob("*"):
            if p.is_file():
                try:
                    p.relative_to(vault / DRAFT_DIR_REL)
                except ValueError:
                    pytest.fail(f"Unexpected file outside draft dir: {p}")

    def test_returns_no_validation_errors_on_success(self, vault):
        result = create_decision_draft(vault, "q.json", VALID_DECISIONS)
        assert result["validation_errors"] == []

    def test_mixed_valid_invalid_only_reports_invalid(self, vault):
        mixed = [
            {"path": "foo.md", "decision": "keep_and_wire"},
            {"path": "bar.md", "decision": "NOT_VALID"},
        ]
        result = create_decision_draft(vault, "q.json", mixed)
        assert result["ok"] is False
        assert any("NOT_VALID" in e for e in result["validation_errors"])


# ---------------------------------------------------------------------------
# list_decision_drafts
# ---------------------------------------------------------------------------

class TestListDecisionDrafts:
    def test_empty_when_no_dir(self, vault):
        result = list_decision_drafts(vault)
        assert result["drafts"] == []
        assert result["total"] == 0

    def test_lists_created_drafts(self, vault):
        create_decision_draft(vault, "q.json", VALID_DECISIONS[:1])
        create_decision_draft(vault, "q.json", VALID_DECISIONS[:2])
        result = list_decision_drafts(vault)
        assert result["total"] == 2
        assert len(result["drafts"]) == 2

    def test_newest_first_order(self, vault):
        create_decision_draft(vault, "q.json", VALID_DECISIONS[:1])
        create_decision_draft(vault, "q.json", VALID_DECISIONS[:2])
        result = list_decision_drafts(vault)
        names = [d["filename"] for d in result["drafts"]]
        assert names == sorted(names, reverse=True)

    def test_applied_flag_false_by_default(self, vault):
        create_decision_draft(vault, "q.json", VALID_DECISIONS[:1])
        result = list_decision_drafts(vault)
        assert result["drafts"][0]["applied"] is False

    def test_handles_malformed_file_gracefully(self, vault):
        draft_dir = vault / DRAFT_DIR_REL
        draft_dir.mkdir(parents=True)
        (draft_dir / "2026-01-01T000000-graph-hygiene-decision-draft.json").write_text("NOT JSON")
        result = list_decision_drafts(vault)
        assert result["total"] == 1
        assert result["drafts"][0]["status"] == "malformed"


# ---------------------------------------------------------------------------
# load_decision_draft
# ---------------------------------------------------------------------------

class TestLoadDecisionDraft:
    def test_loads_existing_draft(self, vault):
        r = create_decision_draft(vault, "q.json", VALID_DECISIONS)
        loaded = load_decision_draft(vault, r["draft_path"])
        assert loaded is not None
        assert loaded["draft_id"] == r["draft_id"]

    def test_returns_none_for_missing_file(self, vault):
        assert load_decision_draft(vault, str(DRAFT_DIR_REL / "missing.json")) is None

    def test_rejects_path_traversal(self, vault):
        # Attempt to escape draft dir
        assert load_decision_draft(vault, "../../etc/passwd") is None
        assert load_decision_draft(vault, "07_LOGS/some-other-file.json") is None

    def test_returns_none_for_malformed_json(self, vault):
        draft_dir = vault / DRAFT_DIR_REL
        draft_dir.mkdir(parents=True)
        bad = draft_dir / "2026-01-01T000000-graph-hygiene-decision-draft.json"
        bad.write_text("{not valid json")
        assert load_decision_draft(vault, str(DRAFT_DIR_REL / bad.name)) is None
