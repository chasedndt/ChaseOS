"""Tests for Phase 10E Canvas visual-link approval proposal bridge."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.canvas_drafts import CANVAS_AUTHORITY_FLAGS, CANVAS_DRAFT_DIR
from runtime.studio.canvas_visual_link_proposals import build_canvas_visual_link_proposals
from runtime.studio.graph_index_contract import build_graph_index_contract


def _seed_notes(vault: Path) -> None:
    notes = vault / "notes"
    notes.mkdir(parents=True)
    (notes / "alpha.md").write_text("# Alpha\n\nBody.\n", encoding="utf-8")
    (notes / "beta.md").write_text("# Beta\n\nBody.\n", encoding="utf-8")


def _node_for(vault: Path, path: str) -> dict:
    graph = build_graph_index_contract(str(vault), folder_path="notes")
    return next(node for node in graph["graph"]["nodes"] if node["properties"].get("path") == path)


def _graph_ref(object_id: str, *, node_id: str, source_path: str) -> dict:
    return {
        "object_id": object_id,
        "kind": "graph_node_ref",
        "label": object_id,
        "position": {"x": 1, "y": 2},
        "size": {"width": 120, "height": 80},
        "style": {},
        "target_ref": {
            "type": "graph_node",
            "node_id": node_id,
            "source_path": source_path,
            "trust_state": "raw",
        },
        "draft_text": None,
        "created_by": "test",
        "updated_at": "2026-05-12T00:00:00Z",
    }


def _link(link_id: str, source: str, target: str, *, label: str = "supports") -> dict:
    return {
        "link_id": link_id,
        "source_object_id": source,
        "target_object_id": target,
        "label": label,
        "kind": "canvas_visual_link",
        "conversion": {
            "proposal_surface": "visual-link-approval-flow",
            "relation_type": "supports",
            "edge_layer": "suggested",
            "evidence": "canvas visual connection",
        },
    }


def _write_draft(vault: Path, *, objects: list[dict], links: list[dict], name: str = "links.json") -> None:
    root = vault / CANVAS_DRAFT_DIR
    root.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "studio_canvas.v1",
        "canvas_id": "canvas_links",
        "title": "Visual link board",
        "created_at": "2026-05-12T00:00:00Z",
        "updated_at": "2026-05-12T00:00:00Z",
        "workspace_root_ref": ".",
        "authority": dict(CANVAS_AUTHORITY_FLAGS),
        "objects": objects,
        "links": links,
        "view_state": {},
        "provenance": {},
    }
    (root / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_canvas_visual_link_preview_reuses_visual_link_flow_without_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    alpha = _node_for(vault, "alpha.md")
    beta = _node_for(vault, "beta.md")
    _write_draft(
        vault,
        objects=[
            _graph_ref("obj_alpha", node_id=alpha["id"], source_path="alpha.md"),
            _graph_ref("obj_beta", node_id=beta["id"], source_path="beta.md"),
        ],
        links=[_link("canvas-link-1", "obj_alpha", "obj_beta")],
    )
    before = _snapshot(vault)

    response = build_canvas_visual_link_proposals(vault, "links.json", folder_path="notes")

    assert _snapshot(vault) == before
    assert response["ok"] is True
    assert response["surface"] == "studio_canvas_visual_link_proposal_bridge"
    assert response["authority"]["preview_only"] is True
    assert response["authority"]["queues_approval_artifacts"] is False
    assert response["write_contract"]["markdown_writes"] is False
    assert response["write_contract"]["graph_link_writes"] is False
    assert response["write_contract"]["graph_snapshot_writes"] is False
    proposal = response["proposals"][0]
    assert proposal["canvas_link_id"] == "canvas-link-1"
    assert proposal["graph_edge_id"] == proposal["visual_link_preview"]["preview_edge"]["id"]
    assert proposal["canvas_link_id"] != proposal["graph_edge_id"]
    assert proposal["approval_posture"] == {
        "proposal_surface": "visual-link-approval-flow",
        "preview_only": True,
        "approval_required_for_execution": True,
        "queued_approval_artifact": False,
        "approved_execution_owned_by": "studio_visual_link_approval_flow",
    }
    assert proposal["source_ref"]["object_id"] == "obj_alpha"
    assert proposal["source_ref"]["state"] == "existing_node"
    assert proposal["source_ref"]["node_id"] == alpha["id"]
    assert proposal["target_ref"]["object_id"] == "obj_beta"
    assert proposal["target_ref"]["state"] == "existing_node"
    assert proposal["target_ref"]["node_id"] == beta["id"]
    assert proposal["visual_link_preview"]["requires_approval"] is True
    assert proposal["visual_link_preview"]["edge_layer"] == "suggested"
    assert proposal["visual_link_preview"]["relation_type"] == "supports"
    assert "content" not in proposal["visual_link_preview"]


def test_canvas_visual_link_preview_reports_stale_and_missing_nodes_without_flow_execution(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_notes(vault)
    alpha = _node_for(vault, "alpha.md")
    _write_draft(
        vault,
        objects=[
            _graph_ref("obj_stale", node_id=alpha["id"], source_path="old/alpha.md"),
            _graph_ref("obj_missing", node_id="studio:missing", source_path="missing.md"),
        ],
        links=[_link("canvas-link-stale", "obj_stale", "obj_missing")],
    )
    before = _snapshot(vault)

    response = build_canvas_visual_link_proposals(vault, "links.json", folder_path="notes")

    assert _snapshot(vault) == before
    proposal = response["proposals"][0]
    assert proposal["state"] == "blocked_unresolved_graph_nodes"
    assert proposal["source_ref"]["state"] == "stale_node_source_path_moved"
    assert proposal["source_ref"]["current_source_path"] == "alpha.md"
    assert proposal["target_ref"]["state"] == "missing_node"
    assert proposal["visual_link_preview"] is None
    assert proposal["graph_edge_id"] is None
    assert proposal["warnings"] == ["source-ref-stale", "target-ref-missing"]
