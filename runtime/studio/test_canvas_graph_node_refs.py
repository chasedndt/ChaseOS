"""Tests for Phase 10E Canvas graph-node reference resolution."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.canvas_drafts import CANVAS_AUTHORITY_FLAGS, CANVAS_DRAFT_DIR
from runtime.studio.canvas_graph_node_refs import resolve_canvas_graph_node_refs
from runtime.studio.graph_index_contract import build_graph_index_contract


def _seed_notes(vault: Path) -> None:
    notes = vault / "notes"
    notes.mkdir(parents=True)
    (notes / "alpha.md").write_text("# Alpha\nLinks to [[Beta]].\n", encoding="utf-8")
    (notes / "beta.md").write_text("# Beta\nBack to [[Alpha]].\n", encoding="utf-8")


def _draft_payload(objects: list[dict]) -> dict:
    return {
        "schema_version": "studio_canvas.v1",
        "canvas_id": "canvas_refs",
        "title": "Reference board",
        "created_at": "2026-05-12T00:00:00Z",
        "updated_at": "2026-05-12T00:00:00Z",
        "workspace_root_ref": ".",
        "authority": dict(CANVAS_AUTHORITY_FLAGS),
        "objects": objects,
        "links": [],
        "view_state": {},
        "provenance": {},
    }


def _graph_ref(object_id: str, *, node_id: str, source_path: str, target_type: str = "graph_node") -> dict:
    return {
        "object_id": object_id,
        "kind": "graph_node_ref",
        "label": object_id,
        "position": {"x": 1, "y": 2},
        "size": {"width": 120, "height": 80},
        "style": {},
        "target_ref": {
            "type": target_type,
            "node_id": node_id,
            "source_path": source_path,
            "trust_state": "raw",
        },
        "draft_text": None,
        "created_by": "test",
        "updated_at": "2026-05-12T00:00:00Z",
    }


def _write_draft(vault: Path, objects: list[dict], name: str = "refs.json") -> None:
    root = vault / CANVAS_DRAFT_DIR
    root.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(json.dumps(_draft_payload(objects), indent=2), encoding="utf-8")


def _snapshot(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def _node_for(vault: Path, path: str) -> dict:
    graph = build_graph_index_contract(vault, folder_path="notes")
    return next(node for node in graph["graph"]["nodes"] if node["properties"].get("path") == path)


def test_resolver_returns_existing_graph_node_with_inspector_metadata_read_only(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    alpha = _node_for(vault, "alpha.md")
    _write_draft(vault, [_graph_ref("obj_alpha", node_id=alpha["id"], source_path="alpha.md")])
    before = _snapshot(vault)

    response = resolve_canvas_graph_node_refs(vault, "refs.json", folder_path="notes")

    assert _snapshot(vault) == before
    assert response["ok"] is True
    assert response["surface"] == "studio_canvas_graph_node_ref_resolver"
    assert response["authority"]["read_only"] is True
    assert response["authority"]["writes_node_ids"] is False
    assert response["authority"]["writes_graph_index"] is False
    result = response["references"][0]
    assert result["state"] == "existing_node"
    assert result["object_id"] == "obj_alpha"
    assert result["node_id"] == alpha["id"]
    assert result["source_path"] == "alpha.md"
    assert result["trust_source_posture"]["graph_trust_state"] == "raw"
    assert result["node_inspector_link"] == {
        "surface": "studio_node_inspector_contract",
        "read_only": True,
        "selector": {"selector_type": "node_id", "selector_value": alpha["id"]},
        "allowed_action": "inspect-node",
    }


def test_resolver_reports_missing_graph_node_explicitly(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    _write_draft(vault, [_graph_ref("obj_missing", node_id="studio:missing", source_path="missing.md")])

    response = resolve_canvas_graph_node_refs(vault, "refs.json", folder_path="notes")

    assert response["ok"] is True
    result = response["references"][0]
    assert result["state"] == "missing_node"
    assert result["node_id"] == "studio:missing"
    assert result["source_path"] == "missing.md"
    assert result["node_inspector_link"] is None
    assert "node-not-found" in result["warnings"]


def test_resolver_reports_stale_or_moved_source_path_without_rewriting_reference(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    alpha = _node_for(vault, "alpha.md")
    _write_draft(vault, [_graph_ref("obj_stale", node_id=alpha["id"], source_path="old/alpha.md")])
    before = _snapshot(vault)

    response = resolve_canvas_graph_node_refs(vault, "refs.json", folder_path="notes")

    assert _snapshot(vault) == before
    result = response["references"][0]
    assert result["state"] == "stale_node_source_path_moved"
    assert result["node_id"] == alpha["id"]
    assert result["source_path"] == "old/alpha.md"
    assert result["current_source_path"] == "alpha.md"
    assert result["node_inspector_link"]["selector"] == {"selector_type": "node_id", "selector_value": alpha["id"]}


def test_resolver_reports_malformed_or_unsupported_canvas_references(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    _write_draft(
        vault,
        [
            _graph_ref(
                "obj_bad_type",
                node_id="studio:any",
                source_path="alpha.md",
                target_type="artifact",
            )
        ],
    )

    response = resolve_canvas_graph_node_refs(vault, "refs.json", folder_path="notes")

    result = response["references"][0]
    assert result["state"] == "unsupported_target_type"
    assert result["node_id"] == "studio:any"
    assert result["source_path"] == "alpha.md"
    assert result["node_inspector_link"] is None
    assert "unsupported-target-type" in result["warnings"]
