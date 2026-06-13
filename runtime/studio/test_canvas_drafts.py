"""Tests for Phase 10E workspace-local Canvas draft loader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.studio.canvas_drafts import (
    CANVAS_AUTHORITY_FLAGS,
    CANVAS_DRAFT_DIR,
    CanvasDraftError,
    CanvasDocument,
    CanvasLink,
    CanvasObject,
    load_canvas_draft,
    load_canvas_draft_response,
    save_canvas_draft_response,
)
from runtime.studio.shell.api import StudioAPI


def _vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    return vault


def _canvas_payload() -> dict:
    return {
        "schema_version": "studio_canvas.v1",
        "canvas_id": "canvas_fixture",
        "title": "Investigation board",
        "created_at": "2026-05-12T00:00:00Z",
        "updated_at": "2026-05-12T00:00:00Z",
        "workspace_root_ref": ".",
        "authority": dict(CANVAS_AUTHORITY_FLAGS),
        "objects": [
            {
                "object_id": "obj_runtime_profile",
                "kind": "graph_node_ref",
                "label": "Hermes Runtime Profile",
                "position": {"x": 120, "y": 80},
                "size": {"width": 220, "height": 96},
                "style": {"color": "runtime", "locked": False},
                "target_ref": {
                    "type": "graph_node",
                    "node_id": "derived-hermes-runtime-profile",
                    "source_path": "06_AGENTS/Hermes-Runtime-Profile.md",
                    "trust_state": "derived",
                },
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
        ],
        "links": [
            {
                "link_id": "link_visual",
                "source_object_id": "obj_runtime_profile",
                "target_object_id": "obj_note",
                "label": "related hypothesis",
                "kind": "canvas_visual_link",
                "canonical_edge_ref": None,
                "conversion": {
                    "can_propose_graph_link": True,
                    "requires_approval": True,
                    "proposal_surface": "visual-link-approval-flow",
                },
            }
        ],
        "view_state": {"zoom": 1.0},
        "provenance": {},
    }


def _write_canvas(vault: Path, name: str = "fixture_canvas.json", payload: dict | None = None) -> Path:
    root = vault / CANVAS_DRAFT_DIR
    root.mkdir(parents=True, exist_ok=True)
    path = root / name
    path.write_text(json.dumps(payload or _canvas_payload(), indent=2), encoding="utf-8")
    return path


def _file_snapshot(vault: Path) -> dict[str, str]:
    return {
        path.relative_to(vault).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(vault.rglob("*"))
        if path.is_file()
    }


def _assert_canvas_authority(data: dict) -> None:
    assert data["authority"] == {
        "canonical_mutation_allowed": False,
        "graph_mutation_allowed": False,
        "promotion_requires_gate": True,
        "browser_control_allowed": False,
    }


def test_canvas_models_are_json_serializable_and_validate_authority_flags() -> None:
    obj = CanvasObject(
        object_id="obj_1",
        kind="note_card",
        label="Scratch thought",
        position={"x": 1, "y": 2},
        size={"width": 120, "height": 80},
        style={},
        target_ref=None,
        draft_text="Draft only",
        created_by="test",
        updated_at="2026-05-12T00:00:00Z",
    )
    link = CanvasLink(
        link_id="link_1",
        source_object_id="obj_1",
        target_object_id="obj_1",
        label="self reference",
        kind="canvas_visual_link",
        canonical_edge_ref=None,
        conversion={"can_propose_graph_link": True, "requires_approval": True},
    )
    document = CanvasDocument(
        schema_version="studio_canvas.v1",
        canvas_id="canvas_unit",
        title="Unit canvas",
        created_at="2026-05-12T00:00:00Z",
        updated_at="2026-05-12T00:00:00Z",
        workspace_root_ref=".",
        authority=dict(CANVAS_AUTHORITY_FLAGS),
        objects=[obj],
        links=[link],
        view_state={},
        provenance={},
    )

    encoded = json.dumps(document.to_dict(), sort_keys=True)

    assert "canvas_unit" in encoded
    _assert_canvas_authority(document.to_dict())


def test_load_seeded_fixture_canvas_draft_read_only_and_reports_authority(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    _write_canvas(vault)
    before = _file_snapshot(vault)

    response = load_canvas_draft_response(vault, "fixture_canvas.json")

    assert response["ok"] is True
    assert response["status"] == "ok"
    assert response["surface"] == "studio_canvas_draft_loader"
    _assert_canvas_authority(response)
    _assert_canvas_authority(response["document"])
    assert response["document"]["canvas_id"] == "canvas_fixture"
    assert response["document"]["objects"][0]["kind"] == "graph_node_ref"
    assert response["document"]["links"][0]["kind"] == "canvas_visual_link"
    assert response["read_only"] is True
    assert response["draft_path"] == f"{CANVAS_DRAFT_DIR}/fixture_canvas.json"
    assert response["blocked_authority"] == [
        "canonical_mutation",
        "graph_mutation",
        "provenance_write",
        "source_package_write",
        "browser_control",
    ]
    assert _file_snapshot(vault) == before


def test_loader_rejects_path_traversal_and_non_json_inputs(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    _write_canvas(vault)
    (vault / CANVAS_DRAFT_DIR / "not_json.txt").write_text("{}", encoding="utf-8")

    with pytest.raises(CanvasDraftError, match="path_traversal"):
        load_canvas_draft(vault, "../fixture_canvas.json")
    with pytest.raises(CanvasDraftError, match="json_only"):
        load_canvas_draft(vault, "not_json.txt")

    traversal_response = load_canvas_draft_response(vault, "../fixture_canvas.json")
    non_json_response = load_canvas_draft_response(vault, "not_json.txt")

    assert traversal_response["ok"] is False
    assert traversal_response["error"]["code"] == "path_traversal"
    _assert_canvas_authority(traversal_response)
    assert non_json_response["ok"] is False
    assert non_json_response["error"]["code"] == "json_only"
    _assert_canvas_authority(non_json_response)


def test_loader_rejects_invalid_authority_or_link_endpoints(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    invalid_authority = _canvas_payload()
    invalid_authority["authority"] = dict(CANVAS_AUTHORITY_FLAGS) | {"graph_mutation_allowed": True}
    _write_canvas(vault, "invalid_authority.json", invalid_authority)

    invalid_link = _canvas_payload()
    invalid_link["links"][0]["target_object_id"] = "obj_missing"
    _write_canvas(vault, "invalid_link.json", invalid_link)

    with pytest.raises(CanvasDraftError, match="authority_boundary_violation"):
        load_canvas_draft(vault, "invalid_authority.json")
    with pytest.raises(CanvasDraftError, match="missing_canvas_object"):
        load_canvas_draft(vault, "invalid_link.json")


def test_repo_seeded_canvas_fixture_loads_read_only() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    response = load_canvas_draft_response(repo_root, "phase10e_seed_canvas.json")

    assert response["ok"] is True
    _assert_canvas_authority(response)
    _assert_canvas_authority(response["document"])
    assert response["draft_path"] == f"{CANVAS_DRAFT_DIR}/phase10e_seed_canvas.json"
    assert response["read_only"] is True
    assert response["document"]["canvas_id"] == "canvas_phase10e_seed"


def test_loader_does_not_create_markdown_graph_provenance_source_package_browser_or_canonical_writes(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    _write_canvas(vault)
    before = _file_snapshot(vault)

    response = load_canvas_draft_response(vault, "fixture_canvas.json")

    assert response["ok"] is True
    assert _file_snapshot(vault) == before
    assert list(vault.rglob("*.md")) == []
    assert not (vault / "runtime/studio/graph_snapshots").exists()
    assert not (vault / "runtime/studio/provenance").exists()
    assert not (vault / "runtime/source_packages").exists()
    assert not (vault / "02_KNOWLEDGE").exists()
    assert not (vault / "07_LOGS/Agent-Activity").exists()
    assert response["write_contract"] == {
        "markdown_writes": False,
        "graph_snapshot_writes": False,
        "provenance_writes": False,
        "source_package_writes": False,
        "browser_actions": False,
        "canonical_writes": False,
    }


def test_save_canvas_draft_allows_json_draft_only_under_canvas_drafts(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    payload = _canvas_payload()

    response = save_canvas_draft_response(vault, "local_saved_canvas.json", payload)

    assert response["ok"] is True
    assert response["surface"] == "studio_canvas_draft_save"
    assert response["status"] == "ok"
    assert response["draft_path"] == f"{CANVAS_DRAFT_DIR}/local_saved_canvas.json"
    assert response["write_policy"]["allowed_local_draft_write"] is True
    assert response["write_policy"]["approval_required_for_canonical_conversion"] is True
    assert response["write_contract"]["canvas_draft_json_writes"] is True
    assert response["write_contract"]["markdown_writes"] is False
    _assert_canvas_authority(response)
    saved = json.loads((vault / CANVAS_DRAFT_DIR / "local_saved_canvas.json").read_text(encoding="utf-8"))
    assert saved["canvas_id"] == "canvas_fixture"
    assert saved["authority"] == CANVAS_AUTHORITY_FLAGS


def test_save_canvas_draft_rejects_canonical_markdown_graph_provenance_and_source_targets_before_mutation(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    payload = _canvas_payload()
    protected_targets = [
        ("../02_KNOWLEDGE/Canvas.md", "path_traversal"),
        ("../../07_LOGS/Agent-Activity/canvas.json", "path_traversal"),
        ("../runtime/studio/graph_snapshots/canvas.json", "path_traversal"),
        ("../runtime/studio/provenance/canvas.json", "path_traversal"),
        ("../runtime/source_packages/canvas.json", "path_traversal"),
        ("canvas_export.md", "json_only"),
    ]

    before = _file_snapshot(vault)
    for target, code in protected_targets:
        response = save_canvas_draft_response(vault, target, payload)
        assert response["ok"] is False
        assert response["surface"] == "studio_canvas_draft_save"
        assert response["error"]["code"] == code
        assert response["write_policy"]["allowed_local_draft_write"] is True
        assert response["write_policy"]["approval_required_for_canonical_conversion"] is True
        assert response["blocked_authority_reasons"]["markdown_note_conversion"] == "blocked: markdown note conversion requires approval and remains preview-only"
        assert response["blocked_authority_reasons"]["canonical_knowledge_write"] == "blocked: canonical knowledge writes require Gate approval and remain preview-only"
        assert response["target_block_reason"]
        assert "markdown_note_conversion" in response["blocked_authority"]
        assert "graph_snapshot_write" in response["blocked_authority"]
        assert "provenance_write" in response["blocked_authority"]
        assert "source_package_write" in response["blocked_authority"]
        assert "canonical_knowledge_write" in response["blocked_authority"]
        _assert_canvas_authority(response)

    assert _file_snapshot(vault) == before
    assert not (vault / "02_KNOWLEDGE").exists()
    assert not (vault / "07_LOGS/Agent-Activity").exists()
    assert not (vault / "runtime/studio/graph_snapshots").exists()
    assert not (vault / "runtime/studio/provenance").exists()
    assert not (vault / "runtime/source_packages").exists()


def test_save_canvas_draft_rejects_payload_that_attempts_conversion_authority_before_mutation(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    payload = _canvas_payload()
    payload["authority"] = dict(CANVAS_AUTHORITY_FLAGS) | {"canonical_mutation_allowed": True}

    response = save_canvas_draft_response(vault, "bad_authority.json", payload)

    assert response["ok"] is False
    assert response["error"]["code"] == "authority_boundary_violation"
    assert not (vault / CANVAS_DRAFT_DIR / "bad_authority.json").exists()
    _assert_canvas_authority(response)


def test_studio_api_load_and_save_canvas_draft_wrap_every_response_with_authority_flags(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    _write_canvas(vault)
    api = StudioAPI(vault)

    ok_response = api.load_canvas_draft("fixture_canvas.json")
    err_response = api.load_canvas_draft("missing.json")
    save_response = api.save_canvas_draft("api_saved_canvas.json", _canvas_payload())
    blocked_save = api.save_canvas_draft("../02_KNOWLEDGE/canvas.md", _canvas_payload())

    assert ok_response["ok"] is True
    assert ok_response["surface"] == "studio_canvas_draft_loader"
    _assert_canvas_authority(ok_response)
    _assert_canvas_authority(ok_response["data"])
    assert err_response["ok"] is False
    assert err_response["error"]["code"] == "missing_canvas_draft"
    _assert_canvas_authority(err_response)
    assert save_response["ok"] is True
    assert save_response["surface"] == "studio_canvas_draft_save"
    _assert_canvas_authority(save_response)
    _assert_canvas_authority(save_response["data"])
    assert blocked_save["ok"] is False
    assert blocked_save["error"]["code"] == "path_traversal"
    _assert_canvas_authority(blocked_save)
