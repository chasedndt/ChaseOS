"""Tests for Phase 10AB visual link approval backend."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.studio.service import StudioService, StudioServiceError
from runtime.studio.shell.api import StudioAPI
from runtime.studio.visual_link_approval import (
    DEFAULT_OVERLAY_LIMIT,
    PASS_ID,
    build_visual_link_approval_flow_status,
    build_visual_link_overlay,
    build_visual_link_preview,
    build_visual_link_note_patch,
    queue_visual_link_approval,
)


def _vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    for rel in [
        "02_KNOWLEDGE/general",
        "07_LOGS/Agent-Activity",
    ]:
        (vault / rel).mkdir(parents=True, exist_ok=True)
    return vault


def _note(title: str) -> str:
    return f"---\ntitle: {title}\n---\n\n# {title}\n\nBody.\n"


def _write_note(vault: Path, rel: str, title: str) -> None:
    path = vault / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_note(title), encoding="utf-8")


def _approval_files(vault: Path) -> list[Path]:
    root = vault / StudioService.APPROVAL_DIR
    return sorted(root.glob("*.json")) if root.is_dir() else []


def _contains_key(value: object, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(_contains_key(item, key) for item in value.values())
    if isinstance(value, list):
        return any(_contains_key(item, key) for item in value)
    return False


def test_visual_link_preview_resolves_paths_and_builds_noncanonical_edge(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    _write_note(vault, "02_KNOWLEDGE/general/source.md", "Source")
    _write_note(vault, "02_KNOWLEDGE/general/target.md", "Target")

    preview = build_visual_link_preview(
        vault,
        source_path="02_KNOWLEDGE/general/source.md",
        target_path="02_KNOWLEDGE/general/target.md",
        source_label="Source",
        target_label="Target",
        edge_layer="suggested",
        relation_type="supports",
    )

    assert preview["ok"] is True
    assert preview["requires_approval"] is True
    assert preview["preview_edge"]["non_canonical"] is True
    assert preview["preview_edge"]["edge_layer"] == "suggested"
    assert preview["preview_edge"]["relation_type"] == "supports"
    assert preview["performance_contract"]["does_not_duplicate_full_graph_payload"] is True
    assert preview["performance_contract"]["pending_edges_render_as_overlay"] is True
    assert "[[02_KNOWLEDGE/general/target|Target]]" in preview["content"]
    packet = preview["proposal_packet"]
    assert packet["operation_type"] == "visual_link"
    assert packet["source_path"] == "02_KNOWLEDGE/general/source.md"
    assert packet["target_path"] == "02_KNOWLEDGE/general/target.md"
    assert packet["non_canonical_preview_edges"] == [preview["preview_edge"]]
    assert preview["safe_patch_summary"]["content_stripped"] is False


def test_queue_visual_link_approval_writes_no_markdown_before_approval(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    source_rel = "02_KNOWLEDGE/general/source.md"
    target_rel = "02_KNOWLEDGE/general/target.md"
    _write_note(vault, source_rel, "Source")
    _write_note(vault, target_rel, "Target")
    original = (vault / source_rel).read_text(encoding="utf-8")

    result = queue_visual_link_approval(
        vault,
        source_path=source_rel,
        target_path=target_rel,
        source_label="Source",
        target_label="Target",
        edge_layer="explicit",
        relation_type="related",
    )

    assert result["ok"] is True
    assert result["status"] == "requires_approval"
    assert result["target_path"] == source_rel
    assert (vault / source_rel).read_text(encoding="utf-8") == original
    approval_files = _approval_files(vault)
    assert len(approval_files) == 1
    payload = json.loads(approval_files[0].read_text(encoding="utf-8"))
    assert payload["status"] == "pending"
    assert payload["action_spec"]["metadata"]["pass"] == PASS_ID
    assert payload["action_spec"]["metadata"]["visual_link"] is True
    assert payload["action_spec"]["metadata"]["proposal_packet"]["operation_type"] == "visual_link"
    assert result["preview"]["safe_patch_summary"]["content_stripped"] is True


def test_approved_visual_link_execution_appends_link_and_marks_executed(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    source_rel = "02_KNOWLEDGE/general/source.md"
    target_rel = "02_KNOWLEDGE/general/target.md"
    _write_note(vault, source_rel, "Source")
    _write_note(vault, target_rel, "Target")

    result = queue_visual_link_approval(
        vault,
        source_path=source_rel,
        target_path=target_rel,
        source_label="Source",
        target_label="Target",
    )
    svc = StudioService(vault)
    svc.approve(result["approval_id"])
    action = svc.execute_approved(result["approval_id"])

    assert action.status == "completed"
    rendered = (vault / source_rel).read_text(encoding="utf-8")
    assert "## Studio Links" in rendered
    assert "[[02_KNOWLEDGE/general/target|Target]]" in rendered
    assert svc.get_approval(result["approval_id"]).status == "executed"
    with pytest.raises(StudioServiceError, match="Only 'approved'"):
        svc.execute_approved(result["approval_id"])


def test_duplicate_pending_visual_link_blocks_without_second_artifact(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    source_rel = "02_KNOWLEDGE/general/source.md"
    target_rel = "02_KNOWLEDGE/general/target.md"
    _write_note(vault, source_rel, "Source")
    _write_note(vault, target_rel, "Target")

    first = queue_visual_link_approval(vault, source_path=source_rel, target_path=target_rel)
    second = queue_visual_link_approval(vault, source_path=source_rel, target_path=target_rel)

    assert first["ok"] is True
    assert second["ok"] is False
    assert second["code"] == "pending_link_collision"
    assert len(_approval_files(vault)) == 1


def test_existing_markdown_link_blocks_without_approval(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    source_rel = "02_KNOWLEDGE/general/source.md"
    target_rel = "02_KNOWLEDGE/general/target.md"
    _write_note(vault, target_rel, "Target")
    (vault / source_rel).write_text("# Source\n\n- [[02_KNOWLEDGE/general/target|Target]]\n", encoding="utf-8")

    result = queue_visual_link_approval(vault, source_path=source_rel, target_path=target_rel)

    assert result["ok"] is False
    assert result["code"] == "link_already_exists"
    assert _approval_files(vault) == []


def test_api_preview_visual_link_existing_wikilink_preserves_conflict_evidence_without_content(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    source_rel = "02_KNOWLEDGE/general/source.md"
    target_rel = "02_KNOWLEDGE/general/target.md"
    _write_note(vault, target_rel, "Target")
    (vault / source_rel).write_text("# Source\n\n- [[02_KNOWLEDGE/general/target|Target]]\n", encoding="utf-8")

    response = StudioAPI(vault).preview_visual_link(source_path=source_rel, target_path=target_rel)

    assert response["ok"] is False
    assert response["error"]["code"] == "link_already_exists"
    data = response["data"]
    assert data["conflict_state"] == {
        "conflicted": True,
        "conflict_type": "existing_link",
        "evidence": "raw_wikilink",
        "source_path": source_rel,
        "target_path": target_rel,
    }
    assert data["performance_contract"]["selected_markdown_reads"] == 1
    assert not _contains_key(data, "content")
    assert _approval_files(vault) == []


def test_api_create_link_existing_wikilink_preserves_conflict_evidence_without_content(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    source_rel = "02_KNOWLEDGE/general/source.md"
    target_rel = "02_KNOWLEDGE/general/target.md"
    _write_note(vault, target_rel, "Target")
    (vault / source_rel).write_text("# Source\n\n- [[02_KNOWLEDGE/general/target|Target]]\n", encoding="utf-8")

    response = StudioAPI(vault).create_link("", "", source_path=source_rel, target_path=target_rel)

    assert response["ok"] is False
    assert response["error"]["code"] == "link_already_exists"
    data = response["data"]
    assert data["requires_approval"] is False
    assert data["conflict_state"]["conflict_type"] == "existing_link"
    assert data["conflict_state"]["evidence"] == "raw_wikilink"
    assert not _contains_key(data, "content")
    assert _approval_files(vault) == []


def test_existing_derived_markdown_link_blocks_without_approval(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    source_rel = "02_KNOWLEDGE/general/source.md"
    target_rel = "02_KNOWLEDGE/general/target.md"
    _write_note(vault, target_rel, "Target")
    (vault / source_rel).write_text("# Source\n\n[Target](target.md)\n", encoding="utf-8")

    result = queue_visual_link_approval(vault, source_path=source_rel, target_path=target_rel)

    assert result["ok"] is False
    assert result["code"] == "link_already_exists"
    assert result["conflict_state"]["conflict_type"] == "existing_link"
    assert result["conflict_state"]["evidence"] == "derived_graph_edge"
    assert _approval_files(vault) == []


def test_api_preview_visual_link_derived_link_preserves_conflict_evidence_without_content(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    source_rel = "02_KNOWLEDGE/general/source.md"
    target_rel = "02_KNOWLEDGE/general/target.md"
    _write_note(vault, target_rel, "Target")
    (vault / source_rel).write_text("# Source\n\n[Target](target.md)\n", encoding="utf-8")

    response = StudioAPI(vault).preview_visual_link(source_path=source_rel, target_path=target_rel)

    assert response["ok"] is False
    assert response["error"]["code"] == "link_already_exists"
    data = response["data"]
    assert data["conflict_state"]["conflicted"] is True
    assert data["conflict_state"]["conflict_type"] == "existing_link"
    assert data["conflict_state"]["evidence"] == "derived_graph_edge"
    assert data["conflict_state"]["source_path"] == source_rel
    assert data["conflict_state"]["target_path"] == target_rel
    assert not _contains_key(data, "content")
    assert _approval_files(vault) == []


def test_invalid_visual_link_inputs_block(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    _write_note(vault, "02_KNOWLEDGE/general/source.md", "Source")
    _write_note(vault, "02_KNOWLEDGE/general/target.md", "Target")

    result = queue_visual_link_approval(
        vault,
        source_path="02_KNOWLEDGE/general/source.md",
        target_path="02_KNOWLEDGE/general/target.md",
        edge_layer="structural",
        relation_type="not-supported",
    )

    assert result["ok"] is False
    assert result["code"] == "invalid_visual_link_input"
    assert _approval_files(vault) == []


def test_missing_and_self_link_targets_fail_cleanly(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    rel = "02_KNOWLEDGE/general/source.md"
    _write_note(vault, rel, "Source")

    missing = queue_visual_link_approval(vault, source_path=rel, target_path="02_KNOWLEDGE/general/missing.md")
    self_link = queue_visual_link_approval(vault, source_path=rel, target_path=rel)

    assert missing["ok"] is False
    assert missing["selector"] == "target"
    assert self_link["ok"] is False
    assert self_link["code"] == "self_link_blocked"
    assert _approval_files(vault) == []


def test_protected_source_file_is_gate_blocked(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    (vault / "README.md").write_text("# Readme\n", encoding="utf-8")
    _write_note(vault, "02_KNOWLEDGE/general/target.md", "Target")

    result = queue_visual_link_approval(
        vault,
        source_path="README.md",
        target_path="02_KNOWLEDGE/general/target.md",
    )

    assert result["ok"] is False
    assert result["code"] == "validation_blocked"
    assert "protected file" in " ".join(result["errors"]).lower()
    assert _approval_files(vault) == []


def test_visual_link_overlay_reads_approvals_only_and_caps_results(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    approvals = vault / StudioService.APPROVAL_DIR
    approvals.mkdir(parents=True)
    for index in range(DEFAULT_OVERLAY_LIMIT + 25):
        payload = {
            "approval_id": f"appr-{index}",
            "status": "pending",
            "action_spec": {
                "action_type": "write_file",
                "target_path": f"02_KNOWLEDGE/general/source-{index}.md",
                "content": "",
                "metadata": {
                    "pass": PASS_ID,
                    "visual_link": True,
                    "link_fingerprint": f"fp-{index}",
                    "source_node_id": f"source-{index}",
                    "target_node_id": f"target-{index}",
                    "source_path": f"02_KNOWLEDGE/general/source-{index}.md",
                    "target_path": f"02_KNOWLEDGE/general/target-{index}.md",
                    "source_label": f"Source {index}",
                    "target_label": f"Target {index}",
                    "edge_layer": "suggested",
                    "relation_type": "related",
                },
            },
        }
        (approvals / f"appr-{index}.json").write_text(json.dumps(payload), encoding="utf-8")

    overlay = build_visual_link_overlay(vault)

    assert overlay["ok"] is True
    assert overlay["overlay_edge_count"] == DEFAULT_OVERLAY_LIMIT
    assert overlay["matching_approval_count"] == DEFAULT_OVERLAY_LIMIT + 25
    assert overlay["overlay_truncated"] is True
    assert overlay["performance_contract"]["selected_markdown_reads"] == 0
    assert overlay["performance_contract"]["does_not_rebuild_graph_for_pending_overlay"] is True


def test_status_declares_approval_gated_memory_posture(tmp_path: Path) -> None:
    vault = _vault(tmp_path)

    status = build_visual_link_approval_flow_status(vault)

    assert status["ok"] is True
    assert status["status"] == "COMPLETE / APPROVAL-GATED / VERIFIED"
    assert status["next_recommended_pass"] == "phase10ac-runtime-cockpit-action-readiness"
    assert status["authority_boundary"]["direct_write_allowed"] is False
    assert status["authority_boundary"]["approved_execution_writes_source_markdown"] is True
    assert status["performance_contract"]["pending_edges_render_as_overlay"] is True


def test_visual_link_note_patch_preserves_body_and_adds_studio_links_section() -> None:
    rendered = build_visual_link_note_patch(
        "# Source\n\nBody.\n",
        target={
            "node_id": "target",
            "path": "02_KNOWLEDGE/general/target.md",
            "label": "Target",
            "node_type": "knowledge_doc",
        },
        relation_type="related",
        label="important",
    )

    assert rendered.startswith("# Source\n\nBody.")
    assert "## Studio Links" in rendered
    assert "- [[02_KNOWLEDGE/general/target|Target]] - important" in rendered
