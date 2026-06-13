"""
test_studio_provenance.py — Tests for Studio Provenance Inspector

Covers:
  TestInspectProvenanceErrors  (4 tests) — missing file, missing sidecar, bad JSON
  TestInspectProvenance        (6 tests) — sidecar reading, chain fields, dedup, trust
  TestTrustState               (4 tests) — trust state derivation
  TestListQuarantine           (5 tests) — quarantine listing + filtering
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.studio.provenance import inspect_provenance, list_quarantine_provenance


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    (vault / "03_INPUTS" / "00_QUARANTINE").mkdir(parents=True)
    (vault / ".chaseos").mkdir(parents=True)
    return vault


def _write_sidecar(path: Path, **overrides) -> dict:
    sidecar = {
        "schema_version": "8.3",
        "capture_id": "test-cap-001",
        "content_filename": path.name,
        "content_sha256": "abc123def456",
        "input_class": "digest",
        "source_platform": "perplexity",
        "title": "Test Capture",
        "captured_at": "2026-04-30T10:00:00Z",
        "capture_method": "api",
        "injection_scan": "not-scanned",
        "promotion_status": "quarantine",
        "extra_metadata": {},
    }
    sidecar.update(overrides)
    meta_path = path.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(sidecar), encoding="utf-8")
    return sidecar


# ── TestInspectProvenanceErrors ───────────────────────────────────────────────

class TestInspectProvenanceErrors:
    def test_missing_file_returns_error(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = inspect_provenance(vault, vault / "nonexistent.md")
        assert result["ok"] is False
        assert "not found" in result["error"].lower()
        assert result["surface"] == "studio_provenance_inspector"

    def test_missing_sidecar_returns_error(self, tmp_path):
        vault = _make_vault(tmp_path)
        content = vault / "03_INPUTS" / "00_QUARANTINE" / "note.md"
        content.write_text("content", encoding="utf-8")
        result = inspect_provenance(vault, content)
        assert result["ok"] is False
        assert "sidecar" in result["error"].lower()

    def test_corrupt_sidecar_returns_error(self, tmp_path):
        vault = _make_vault(tmp_path)
        content = vault / "03_INPUTS" / "00_QUARANTINE" / "note.md"
        content.write_text("content", encoding="utf-8")
        meta = content.with_suffix(".meta.json")
        meta.write_text("{bad json", encoding="utf-8")
        result = inspect_provenance(vault, content)
        assert result["ok"] is False

    def test_error_model_has_boundary(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = inspect_provenance(vault, vault / "ghost.md")
        assert result["boundary"]["writes_vault"] is False
        assert result["boundary"]["canonical_mutation_allowed"] is False


# ── TestInspectProvenance ─────────────────────────────────────────────────────

class TestInspectProvenance:
    def test_returns_ok_for_valid_sidecar(self, tmp_path):
        vault = _make_vault(tmp_path)
        content = vault / "03_INPUTS" / "00_QUARANTINE" / "note.md"
        content.write_text("content", encoding="utf-8")
        _write_sidecar(content)
        result = inspect_provenance(vault, content)
        assert result["ok"] is True

    def test_chain_contains_sidecar_fields(self, tmp_path):
        vault = _make_vault(tmp_path)
        content = vault / "03_INPUTS" / "00_QUARANTINE" / "note.md"
        content.write_text("content", encoding="utf-8")
        _write_sidecar(content, title="My Test Note", source_platform="grok")
        result = inspect_provenance(vault, content)
        assert result["chain"]["title"] == "My Test Note"
        assert result["chain"]["source_platform"] == "grok"
        assert result["chain"]["input_class"] == "digest"

    def test_sha256_shown_in_chain(self, tmp_path):
        vault = _make_vault(tmp_path)
        content = vault / "03_INPUTS" / "00_QUARANTINE" / "note.md"
        content.write_text("content", encoding="utf-8")
        _write_sidecar(content, content_sha256="deadbeef1234")
        result = inspect_provenance(vault, content)
        assert result["chain"]["content_sha256"] == "deadbeef1234"

    def test_dedup_status_not_in_registry(self, tmp_path):
        vault = _make_vault(tmp_path)
        content = vault / "03_INPUTS" / "00_QUARANTINE" / "note.md"
        content.write_text("content", encoding="utf-8")
        _write_sidecar(content)
        result = inspect_provenance(vault, content)
        assert result["dedup_status"] == "not_in_registry"

    def test_dedup_status_known_when_sha_in_registry(self, tmp_path):
        vault = _make_vault(tmp_path)
        content = vault / "03_INPUTS" / "00_QUARANTINE" / "note.md"
        content.write_text("content", encoding="utf-8")
        sha = "abc123def456"
        _write_sidecar(content, content_sha256=sha)
        registry = {sha: {"capture_id": "test-cap-001", "captured_at": "2026-04-30"}}
        (vault / ".chaseos" / "dedup_registry.json").write_text(
            json.dumps(registry), encoding="utf-8"
        )
        result = inspect_provenance(vault, content)
        assert result["dedup_status"] == "known"
        assert result["dedup_entry"]["capture_id"] == "test-cap-001"

    def test_injection_scan_and_promotion_status_surfaced(self, tmp_path):
        vault = _make_vault(tmp_path)
        content = vault / "03_INPUTS" / "00_QUARANTINE" / "note.md"
        content.write_text("content", encoding="utf-8")
        _write_sidecar(content, injection_scan="clean", promotion_status="quarantine")
        result = inspect_provenance(vault, content)
        assert result["injection_scan"] == "clean"
        assert result["promotion_status"] == "quarantine"


# ── TestTrustState ────────────────────────────────────────────────────────────

class TestTrustState:
    def test_promoted_status(self, tmp_path):
        vault = _make_vault(tmp_path)
        content = vault / "03_INPUTS" / "00_QUARANTINE" / "note.md"
        content.write_text("x", encoding="utf-8")
        _write_sidecar(content, promotion_status="promoted")
        result = inspect_provenance(vault, content)
        assert result["trust_state"] == "promoted"

    def test_scanned_clean(self, tmp_path):
        vault = _make_vault(tmp_path)
        content = vault / "03_INPUTS" / "00_QUARANTINE" / "note.md"
        content.write_text("x", encoding="utf-8")
        _write_sidecar(content, injection_scan="clean", promotion_status="quarantine")
        result = inspect_provenance(vault, content)
        assert result["trust_state"] == "scanned-clean"

    def test_flagged(self, tmp_path):
        vault = _make_vault(tmp_path)
        content = vault / "03_INPUTS" / "00_QUARANTINE" / "note.md"
        content.write_text("x", encoding="utf-8")
        _write_sidecar(content, injection_scan="flagged")
        result = inspect_provenance(vault, content)
        assert result["trust_state"] == "flagged"

    def test_unscanned_quarantine(self, tmp_path):
        vault = _make_vault(tmp_path)
        content = vault / "03_INPUTS" / "00_QUARANTINE" / "note.md"
        content.write_text("x", encoding="utf-8")
        _write_sidecar(content, injection_scan="not-scanned", promotion_status="quarantine")
        result = inspect_provenance(vault, content)
        assert result["trust_state"] == "unscanned-quarantine"


# ── TestListQuarantine ────────────────────────────────────────────────────────

class TestListQuarantine:
    def test_empty_quarantine(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = list_quarantine_provenance(vault)
        assert result["ok"] is True
        assert result["result_count"] == 0
        assert result["results"] == []

    def test_lists_captures(self, tmp_path):
        vault = _make_vault(tmp_path)
        q = vault / "03_INPUTS" / "00_QUARANTINE"
        for i in range(3):
            f = q / f"note{i}.md"
            f.write_text("x", encoding="utf-8")
            _write_sidecar(f, input_class="digest", title=f"Note {i}")
        result = list_quarantine_provenance(vault)
        assert result["result_count"] == 3
        assert all("title" in r for r in result["results"])

    def test_filters_by_input_class(self, tmp_path):
        vault = _make_vault(tmp_path)
        q = vault / "03_INPUTS" / "00_QUARANTINE"
        for cls, name in [("digest", "d1"), ("source", "s1"), ("digest", "d2")]:
            f = q / f"{name}.md"
            f.write_text("x", encoding="utf-8")
            _write_sidecar(f, input_class=cls)
        result = list_quarantine_provenance(vault, input_class="digest")
        classes = {r["input_class"] for r in result["results"]}
        assert classes == {"digest"}
        assert result["result_count"] == 2

    def test_limit_respected(self, tmp_path):
        vault = _make_vault(tmp_path)
        q = vault / "03_INPUTS" / "00_QUARANTINE"
        for i in range(10):
            f = q / f"note{i:02d}.md"
            f.write_text("x", encoding="utf-8")
            _write_sidecar(f)
        result = list_quarantine_provenance(vault, limit=3)
        assert result["result_count"] == 3

    def test_sha256_truncated_in_listing(self, tmp_path):
        vault = _make_vault(tmp_path)
        q = vault / "03_INPUTS" / "00_QUARANTINE"
        f = q / "note.md"
        f.write_text("x", encoding="utf-8")
        _write_sidecar(f, content_sha256="aabbccddeeff112233445566")
        result = list_quarantine_provenance(vault)
        sha_shown = result["results"][0]["sha256"]
        assert sha_shown is not None
        assert len(sha_shown) < 30
        assert "…" in sha_shown
