"""
test_studio_sic_workspace_browser.py — Tests for Studio SIC Workspace Browser

Covers:
  TestListWorkspaces   (5 tests) — list_sic_workspaces
  TestInspectErrors    (3 tests) — missing workspace, bad json
  TestInspectWorkspace (6 tests) — inspect_sic_workspace full model
  TestSearchSources    (5 tests) — search_sic_sources query matching
  TestBoundary         (2 tests) — _BOUNDARY sentinel in all paths
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.studio.sic_workspace_browser import (
    list_sic_workspaces,
    inspect_sic_workspace,
    search_sic_sources,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    (vault / "runtime" / "source_intelligence" / "workspaces").mkdir(parents=True)
    return vault


def _make_workspace(vault: Path, slug: str) -> Path:
    ws_dir = vault / "runtime" / "source_intelligence" / "workspaces" / slug
    ws_dir.mkdir(parents=True, exist_ok=True)
    return ws_dir


def _write_workspace(ws_dir: Path, slug: str = "test-ws", **overrides) -> Path:
    data = {
        "id": "aaa-bbb-ccc",
        "slug": slug,
        "name": f"Workspace {slug}",
        "description": "Test workspace",
        "created_at": "2026-04-01T00:00:00Z",
        "updated_at": "2026-04-30T00:00:00Z",
        "status": "active",
        "domain": "TradingSystems",
        "tags": ["alpha", "beta"],
        "source_package_ids": [],
        "source_count": 0,
        "source_refs": {},
        "index_status": "not-indexed",
        "index_path": None,
        "last_indexed_at": None,
        "embedding_model": None,
        "retrieval_top_k": 5,
        "output_count": 0,
        "outputs": [],
        "default_promotion_target": "02_KNOWLEDGE/TradingSystems/",
        "promotion_requires_review": True,
    }
    data.update(overrides)
    path = ws_dir / "workspace.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _make_source_ref(
    source_package_id: str = "src-001",
    title: str = "Test Source",
    source_type: str = "research-digest",
    domain: str = "TradingSystems",
) -> dict:
    return {
        "source_package_id": source_package_id,
        "title": title,
        "source_type": source_type,
        "domain": domain,
        "chunk_count": 4,
        "extraction_status": "complete",
        "injection_scan_status": "not-scanned",
        "user_trust_level": "untrusted",
        "embedding_status": "not-embedded",
        "package_created_date": "2026-04-01",
        "added_at": "2026-04-01T00:00:00Z",
    }


# ── TestListWorkspaces ────────────────────────────────────────────────────────

class TestListWorkspaces:
    def test_empty_when_no_workspaces_dir(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        result = list_sic_workspaces(vault)
        assert result["ok"] is True
        assert result["workspace_count"] == 0
        assert result["workspaces"] == []

    def test_empty_when_no_workspace_json(self, tmp_path):
        vault = _make_vault(tmp_path)
        ws_dir = _make_workspace(vault, "empty-ws")
        # no workspace.json written
        result = list_sic_workspaces(vault)
        assert result["workspace_count"] == 0

    def test_detects_workspace(self, tmp_path):
        vault = _make_vault(tmp_path)
        ws_dir = _make_workspace(vault, "alpha")
        _write_workspace(ws_dir, slug="alpha")
        result = list_sic_workspaces(vault)
        assert result["workspace_count"] == 1
        assert result["workspaces"][0]["slug"] == "alpha"

    def test_multiple_workspaces(self, tmp_path):
        vault = _make_vault(tmp_path)
        for name in ("alpha", "beta", "gamma"):
            ws_dir = _make_workspace(vault, name)
            _write_workspace(ws_dir, slug=name)
        result = list_sic_workspaces(vault)
        assert result["workspace_count"] == 3
        slugs = {w["slug"] for w in result["workspaces"]}
        assert slugs == {"alpha", "beta", "gamma"}

    def test_summary_fields_present(self, tmp_path):
        vault = _make_vault(tmp_path)
        ws_dir = _make_workspace(vault, "alpha")
        _write_workspace(ws_dir, slug="alpha", domain="AI", source_count=3, index_status="indexed")
        result = list_sic_workspaces(vault)
        w = result["workspaces"][0]
        assert w["domain"] == "AI"
        assert w["source_count"] == 3
        assert w["index_status"] == "indexed"


# ── TestInspectErrors ─────────────────────────────────────────────────────────

class TestInspectErrors:
    def test_missing_workspace_returns_error(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = inspect_sic_workspace(vault, "ghost-ws")
        assert result["ok"] is False
        assert "not found" in result["error"]

    def test_error_surface(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = inspect_sic_workspace(vault, "ghost-ws")
        assert result["surface"] == "studio_sic_workspace_browser"

    def test_corrupt_json_returns_error(self, tmp_path):
        vault = _make_vault(tmp_path)
        ws_dir = _make_workspace(vault, "corrupt-ws")
        (ws_dir / "workspace.json").write_text("NOT JSON", encoding="utf-8")
        result = inspect_sic_workspace(vault, "corrupt-ws")
        assert result["ok"] is False


# ── TestInspectWorkspace ──────────────────────────────────────────────────────

class TestInspectWorkspace:
    def test_ok_result(self, tmp_path):
        vault = _make_vault(tmp_path)
        ws_dir = _make_workspace(vault, "alpha")
        _write_workspace(ws_dir, slug="alpha")
        result = inspect_sic_workspace(vault, "alpha")
        assert result["ok"] is True

    def test_basic_fields(self, tmp_path):
        vault = _make_vault(tmp_path)
        ws_dir = _make_workspace(vault, "alpha")
        _write_workspace(ws_dir, slug="alpha", domain="TradingSystems", status="active")
        result = inspect_sic_workspace(vault, "alpha")
        assert result["domain"] == "TradingSystems"
        assert result["status"] == "active"
        assert result["workspace_slug"] == "alpha"

    def test_source_refs_empty(self, tmp_path):
        vault = _make_vault(tmp_path)
        ws_dir = _make_workspace(vault, "alpha")
        _write_workspace(ws_dir, slug="alpha")
        result = inspect_sic_workspace(vault, "alpha")
        assert result["source_refs"] == []
        assert result["source_count"] == 0

    def test_source_refs_summarized(self, tmp_path):
        vault = _make_vault(tmp_path)
        ws_dir = _make_workspace(vault, "alpha")
        ref = _make_source_ref(title="Funding Rates Study")
        _write_workspace(ws_dir, slug="alpha", source_refs={"src-001": ref}, source_count=1)
        result = inspect_sic_workspace(vault, "alpha")
        assert len(result["source_refs"]) == 1
        assert result["source_refs"][0]["title"] == "Funding Rates Study"

    def test_index_status_reflected(self, tmp_path):
        vault = _make_vault(tmp_path)
        ws_dir = _make_workspace(vault, "alpha")
        _write_workspace(ws_dir, slug="alpha", index_status="indexed", last_indexed_at="2026-04-30T10:00:00Z")
        result = inspect_sic_workspace(vault, "alpha")
        assert result["index_status"] == "indexed"
        assert result["last_indexed_at"] == "2026-04-30T10:00:00Z"

    def test_promotion_fields(self, tmp_path):
        vault = _make_vault(tmp_path)
        ws_dir = _make_workspace(vault, "alpha")
        _write_workspace(ws_dir, slug="alpha", default_promotion_target="02_KNOWLEDGE/AI/", promotion_requires_review=True)
        result = inspect_sic_workspace(vault, "alpha")
        assert result["default_promotion_target"] == "02_KNOWLEDGE/AI/"
        assert result["promotion_requires_review"] is True


# ── TestSearchSources ─────────────────────────────────────────────────────────

class TestSearchSources:
    def _make_ws_with_sources(self, tmp_path):
        vault = _make_vault(tmp_path)
        ws_dir = _make_workspace(vault, "alpha")
        refs = {
            "src-001": _make_source_ref("src-001", "Crypto Funding Rates", "research-digest", "TradingSystems"),
            "src-002": _make_source_ref("src-002", "Order Flow Lecture", "transcript-verbatim", "TradingSystems"),
            "src-003": _make_source_ref("src-003", "Multi Agent Patterns", "research-digest", "AI"),
        }
        _write_workspace(ws_dir, slug="alpha", source_refs=refs, source_count=3)
        return vault

    def test_match_by_title(self, tmp_path):
        vault = self._make_ws_with_sources(tmp_path)
        result = search_sic_sources(vault, "alpha", "funding")
        assert result["ok"] is True
        assert result["match_count"] == 1
        assert result["matches"][0]["title"] == "Crypto Funding Rates"

    def test_match_by_type(self, tmp_path):
        vault = self._make_ws_with_sources(tmp_path)
        result = search_sic_sources(vault, "alpha", "transcript")
        assert result["match_count"] == 1
        assert result["matches"][0]["source_type"] == "transcript-verbatim"

    def test_match_by_domain(self, tmp_path):
        vault = self._make_ws_with_sources(tmp_path)
        result = search_sic_sources(vault, "alpha", "ai")
        assert result["match_count"] == 1
        assert result["matches"][0]["domain"] == "AI"

    def test_no_match_returns_empty(self, tmp_path):
        vault = self._make_ws_with_sources(tmp_path)
        result = search_sic_sources(vault, "alpha", "nonexistent_xyz")
        assert result["ok"] is True
        assert result["match_count"] == 0
        assert result["matches"] == []

    def test_missing_workspace_error(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = search_sic_sources(vault, "ghost-ws", "query")
        assert result["ok"] is False
        assert "not found" in result["error"]


# ── TestBoundary ──────────────────────────────────────────────────────────────

class TestBoundary:
    def test_list_has_boundary(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = list_sic_workspaces(vault)
        assert result["boundary"]["writes_workspace_files"] is False
        assert result["boundary"]["canonical_mutation_allowed"] is False

    def test_inspect_has_boundary(self, tmp_path):
        vault = _make_vault(tmp_path)
        ws_dir = _make_workspace(vault, "alpha")
        _write_workspace(ws_dir, slug="alpha")
        result = inspect_sic_workspace(vault, "alpha")
        assert result["boundary"]["triggers_retrieval"] is False
        assert result["boundary"]["writes_workspace_files"] is False
