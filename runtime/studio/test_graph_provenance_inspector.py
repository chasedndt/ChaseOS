"""Tests for Phase 10Z graph provenance inspector."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.graph_provenance_inspector import (
    MODEL_VERSION,
    NEXT_RECOMMENDED_PASS,
    SURFACE_ID,
    build_graph_provenance_inspector,
)


def _snapshot(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def _seed_alpha(vault: Path) -> None:
    notes = vault / "notes"
    notes.mkdir(parents=True)
    (notes / "alpha.md").write_text(
        "---\nstatus: promoted\n---\n# Alpha\nLinks to [[Beta]].\n",
        encoding="utf-8",
    )
    (notes / "beta.md").write_text("# Beta\n", encoding="utf-8")


def test_graph_provenance_inspector_returns_present_chain_without_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_alpha(vault)
    sidecar = {
        "schema_version": "1.0",
        "capture_id": "cap-alpha",
        "content_filename": "alpha.md",
        "content_sha256": "abc123",
        "input_class": "digest",
        "source_platform": "local",
        "title": "Alpha",
        "captured_at": "2026-05-07T00:00:00Z",
        "capture_method": "test",
        "source_url": "https://example.com/a",
        "author": "tester",
        "knowledge_class": "source",
        "injection_scan": "clean",
        "promotion_status": "promoted",
        "quarantine_status": "reviewed",
        "domain_hint": "studio",
        "project_hint": "phase10",
        "workspace_hint": "test",
        "extra_metadata": {"note": "kept"},
    }
    (vault / "notes" / "alpha.meta.json").write_text(json.dumps(sidecar), encoding="utf-8")
    (vault / ".chaseos").mkdir()
    (vault / ".chaseos" / "dedup_registry.json").write_text(
        json.dumps({"abc123": {"first_seen": "2026-05-07"}}),
        encoding="utf-8",
    )
    before = _snapshot(vault)

    model = build_graph_provenance_inspector(
        vault,
        path="notes/alpha.md",
        folder_path="notes",
        max_nodes=50,
        max_edges=100,
    )

    assert _snapshot(vault) == before
    assert model["ok"] is True
    assert model["surface"] == SURFACE_ID
    assert model["model_version"] == MODEL_VERSION
    assert model["provenance_status"] == "present"
    assert model["readiness"]["graph_provenance_inspector_ready"] is True
    assert model["readiness"]["sidecar_provenance_present"] is True
    assert model["readiness"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert model["chain_sections"]["capture"]["capture_id"] == "cap-alpha"
    assert model["chain_sections"]["promotion"]["promotion_status"] == "promoted"
    assert model["chain_sections"]["dedup"]["dedup_status"] == "known"
    assert model["authority"]["writes_sidecar"] is False
    assert model["authority"]["canonical_mutation_allowed"] is False
    assert model["possible_writes"] == []


def test_graph_provenance_inspector_tolerates_missing_sidecar(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_alpha(vault)
    before = _snapshot(vault)

    model = build_graph_provenance_inspector(
        vault,
        path="notes/alpha.md",
        folder_path="notes",
        max_nodes=50,
        max_edges=100,
    )

    assert _snapshot(vault) == before
    assert model["ok"] is True
    assert model["provenance_status"] == "missing"
    assert model["readiness"]["missing_provenance_tolerated"] is True
    assert "sidecar-provenance-missing" in model["readiness"]["warnings"]
    assert model["chain_sections"]["audit"]["error"].startswith("No sidecar found")


def test_graph_provenance_inspector_tolerates_malformed_sidecar(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_alpha(vault)
    (vault / "notes" / "alpha.meta.json").write_text("{not-json", encoding="utf-8")

    model = build_graph_provenance_inspector(
        vault,
        path="notes/alpha.md",
        folder_path="notes",
        max_nodes=50,
        max_edges=100,
    )

    assert model["ok"] is True
    assert model["provenance_status"] == "malformed"
    assert model["readiness"]["malformed_sidecar_tolerated"] is True
    assert "sidecar-provenance-malformed" in model["readiness"]["warnings"]
    assert "Failed to read sidecar" in model["chain_sections"]["audit"]["error"]


def test_graph_provenance_inspector_missing_node_fails_cleanly(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_alpha(vault)

    model = build_graph_provenance_inspector(
        vault,
        path="notes/missing.md",
        folder_path="notes",
        max_nodes=50,
        max_edges=100,
    )

    assert model["ok"] is False
    assert model["provenance_status"] == "node_missing"
    assert model["readiness"]["graph_provenance_inspector_ready"] is False
    assert "graph-node-not-found" in model["readiness"]["blockers"]
