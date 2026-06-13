"""Tests for the read-only Phase 10E Studio Canvas shell panel."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.canvas_drafts import CANVAS_AUTHORITY_FLAGS, CANVAS_DRAFT_DIR
from runtime.studio.canvas_shell_panel import build_canvas_panel_contract
from runtime.studio.desktop_shell_app import build_studio_desktop_shell_app_plan, render_studio_desktop_shell_app_html


def _canvas_payload() -> dict:
    return {
        "schema_version": "studio_canvas.v1",
        "canvas_id": "canvas_fixture",
        "title": "Canvas fixture",
        "created_at": "2026-05-12T00:00:00Z",
        "updated_at": "2026-05-12T00:00:00Z",
        "workspace_root_ref": ".",
        "authority": dict(CANVAS_AUTHORITY_FLAGS),
        "objects": [
            {
                "object_id": "obj_graph",
                "kind": "graph_node_ref",
                "label": "Hermes Runtime Profile",
                "position": {"x": 120, "y": 80},
                "size": {"width": 220, "height": 96},
                "style": {"color": "runtime"},
                "target_ref": {"type": "graph_node", "node_id": "derived-hermes-runtime-profile", "source_path": "06_AGENTS/Hermes-Runtime-Profile.md", "trust_state": "derived"},
                "draft_text": None,
                "created_by": "test",
                "updated_at": "2026-05-12T00:00:00Z",
            },
            {
                "object_id": "obj_note",
                "kind": "note_card",
                "label": "Draft note",
                "position": {"x": 420, "y": 120},
                "size": {"width": 200, "height": 120},
                "style": {},
                "target_ref": None,
                "draft_text": "Workspace-local thought only.",
                "created_by": "test",
                "updated_at": "2026-05-12T00:00:00Z",
            },
            {
                "object_id": "obj_artifact",
                "kind": "artifact_ref",
                "label": "Build log",
                "position": {"x": 120, "y": 280},
                "size": {"width": 220, "height": 96},
                "style": {},
                "target_ref": {"type": "artifact", "path": "07_LOGS/Build-Logs/canvas.md"},
                "draft_text": None,
                "created_by": "test",
                "updated_at": "2026-05-12T00:00:00Z",
            },
            {
                "object_id": "obj_group",
                "kind": "group",
                "label": "Investigation group",
                "position": {"x": 90, "y": 60},
                "size": {"width": 620, "height": 360},
                "style": {},
                "target_ref": None,
                "draft_text": None,
                "created_by": "test",
                "updated_at": "2026-05-12T00:00:00Z",
            },
            {
                "object_id": "obj_proposal",
                "kind": "proposal_card",
                "label": "Propose graph link",
                "position": {"x": 680, "y": 180},
                "size": {"width": 240, "height": 120},
                "style": {},
                "target_ref": {"type": "proposal", "proposal_surface": "visual-link-approval-flow"},
                "draft_text": "Preview only; requires approval.",
                "created_by": "test",
                "updated_at": "2026-05-12T00:00:00Z",
            },
        ],
        "links": [
            {
                "link_id": "link_visual",
                "source_object_id": "obj_graph",
                "target_object_id": "obj_note",
                "label": "related hypothesis",
                "kind": "canvas_visual_link",
                "canonical_edge_ref": None,
                "conversion": {"can_propose_graph_link": True, "requires_approval": True, "proposal_surface": "visual-link-approval-flow"},
            }
        ],
        "view_state": {"zoom": 1.0},
        "provenance": {},
    }


def _seed_canvas(vault: Path, name: str = "fixture_canvas.json") -> None:
    root = vault / CANVAS_DRAFT_DIR
    root.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(json.dumps(_canvas_payload(), indent=2), encoding="utf-8")


def _snapshot(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def test_canvas_panel_contract_is_read_only_and_badges_all_canvas_object_families(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_canvas(vault)
    before = _snapshot(vault)

    model = build_canvas_panel_contract(vault, draft_name="fixture_canvas.json")

    assert _snapshot(vault) == before
    assert model["ok"] is True
    assert model["surface"] == "studio_canvas_panel_contract"
    assert model["panel"]["panel_id"] == "studio.canvas.panel"
    assert model["panel"]["label"] == "Canvas / Whiteboard"
    assert model["panel"]["mount_target"] == "desktop-shell-app:workspace-main-panel"
    assert model["panel"]["draft_name"] == "fixture_canvas.json"
    assert model["boundary_banner"] == "Workspace-local canvas draft. This board does not mutate graph truth or canonical knowledge. Promotion and graph writes require Gate approval."
    assert model["authority"]["read_only"] is True
    assert model["authority"]["canvas_draft_save_allowed"] is False
    assert model["authority"]["graph_mutation_allowed"] is False
    assert model["authority"]["canonical_mutation_allowed"] is False
    assert model["authority"]["browser_control_allowed"] is False
    assert model["possible_writes"] == []
    assert model["allowed_actions"] == ["open-read-only-node-inspector"]
    assert model["readiness"]["canvas_panel_contract_ready"] is True
    assert model["summary"]["object_count"] == 5
    badges = {badge["object_id"]: badge for badge in model["source_badges"]}
    assert badges["obj_graph"]["badge"] == "derived/existing graph node"
    assert badges["obj_note"]["badge"] == "workspace-local draft"
    assert badges["obj_artifact"]["badge"] == "audit/log/proof artifact"
    assert badges["obj_group"]["badge"] == "workspace-local draft group"
    assert badges["obj_proposal"]["badge"] == "approval-required proposal preview"


def test_canvas_panel_mounts_in_desktop_shell_as_visualization_without_save_edit_or_browser_actions(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    _seed_canvas(vault, "phase10e_seed_canvas.json")

    plan = build_studio_desktop_shell_app_plan(vault, planning_mode="full", panel_timeout_seconds=10)
    html = render_studio_desktop_shell_app_html(plan)

    assert plan["shell"]["canvas_panel_mounted"] is True
    assert plan["shell"]["canvas_panel_contract_ready"] is True
    assert plan["canvas_panel"]["ok"] is True
    assert plan["canvas_panel"]["authority"]["canvas_draft_save_allowed"] is False
    assert "/canvas-panel.json" in plan["routes"]
    view = next(view for view in plan["views"] if view["id"] == "canvas")
    assert view["title"] == "Canvas / Whiteboard"
    assert view["read_only"] is True
    assert view["mounted"] is True
    assert 'data-testid="canvas-panel-mount"' in html
    assert 'href="#canvas"' in html
    assert "Workspace-local canvas draft" in html
    assert "derived/existing graph node" in html
    assert "workspace-local draft" in html
    assert "audit/log/proof artifact" in html
    assert "approval-required proposal preview" in html
    forbidden = ["save canvas", "edit canvas", "drag-save", "canonical write", "browser control", "excalidraw control"]
    lower = html.lower()
    for token in forbidden:
        assert token not in lower
    assert lower.count("<script") == 0
