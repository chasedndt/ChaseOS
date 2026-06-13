"""Tests for Phase 10AA controlled node create/edit backend."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.studio.controlled_node_write import (
    CONTROLLED_NODE_TYPES,
    EDITABLE_METADATA_FIELDS,
    build_create_node_preview,
    build_node_metadata_edit_model,
    queue_create_node_approval,
    queue_metadata_update_approval,
)
from runtime.studio.shell.api import StudioAPI
from runtime.studio.service import ActionResult, StudioService, StudioServiceError


def _vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    for rel in [
        "00_HOME",
        "01_PROJECTS/general",
        "02_KNOWLEDGE/general",
        "03_INPUTS/00_QUARANTINE/generated",
        "03_INPUTS/00_QUARANTINE/ai-generated",
        "04_SOPS/general",
        "06_AGENTS",
        "07_LOGS/Build-Logs",
        "07_LOGS/Decision-Ledger",
        "07_LOGS/Agent-Activity",
    ]:
        (vault / rel).mkdir(parents=True, exist_ok=True)
    return vault


def _approval_files(vault: Path) -> list[Path]:
    root = vault / StudioService.APPROVAL_DIR
    return sorted(root.glob("*.json")) if root.is_dir() else []


def _note(frontmatter: str = "title: Old\nstatus: draft\n", body: str = "# Old\n\nBody text.\n") -> str:
    return f"---\n{frontmatter}---\n\n{body}"


def _contains_key(value: object, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(_contains_key(item, key) for item in value.values())
    if isinstance(value, list):
        return any(_contains_key(item, key) for item in value)
    return False


def test_create_node_queues_approval_and_writes_no_markdown_before_approval(tmp_path: Path) -> None:
    vault = _vault(tmp_path)

    result = queue_create_node_approval(vault, "knowledge_doc", "Alpha Node", "general")

    assert result["ok"] is True
    assert result["status"] == "requires_approval"
    assert result["target_path"] == "02_KNOWLEDGE/general/alpha-node.md"
    assert not (vault / result["target_path"]).exists()
    approval_files = _approval_files(vault)
    assert len(approval_files) == 1
    payload = json.loads(approval_files[0].read_text(encoding="utf-8"))
    assert payload["status"] == "pending"
    assert payload["action_spec"]["metadata"]["pass"] == "phase10aa-controlled-node-create-edit"
    assert "trust_state: raw" in payload["action_spec"]["content"]
    packet = result["preview"]["proposal_packet"]
    assert packet["operation_type"] == "create_node"
    assert packet["target_path"] == "02_KNOWLEDGE/general/alpha-node.md"
    assert packet["approval_scope"]["requires_approval"] is True
    assert packet["execution_boundary"]["executor_contract_required"] is True
    assert packet["denied_direct_mutation_flags"]["canonical_graph_writeback_allowed"] is False
    assert result["preview"]["safe_diff_summary"]["content_stripped"] is True
    assert result["preview"]["safe_diff_summary"]["frontmatter_keys"]


def test_create_node_collision_blocks_without_approval_artifact(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    target = vault / "02_KNOWLEDGE/general/alpha-node.md"
    target.write_text("# Existing", encoding="utf-8")

    result = queue_create_node_approval(vault, "knowledge_doc", "Alpha Node", "general")

    assert result["ok"] is False
    assert result["code"] == "target_collision"
    assert _approval_files(vault) == []
    assert target.read_text(encoding="utf-8") == "# Existing"


@pytest.mark.parametrize(
    ("node_type", "title", "domain"),
    [
        ("not-a-type", "Valid Title", "general"),
        ("knowledge_doc", "../bad", "general"),
        ("knowledge_doc", "Valid Title", "../bad"),
    ],
)
def test_invalid_create_node_input_blocks(node_type: str, title: str, domain: str, tmp_path: Path) -> None:
    vault = _vault(tmp_path)

    result = queue_create_node_approval(vault, node_type, title, domain)

    assert result["ok"] is False
    assert result["code"] == "invalid_create_node_input"
    assert _approval_files(vault) == []


def test_all_controlled_node_types_map_to_valid_target_paths(tmp_path: Path) -> None:
    vault = _vault(tmp_path)

    for node_type in CONTROLLED_NODE_TYPES:
        preview = build_create_node_preview(vault, node_type, f"{node_type} sample", "General Domain")
        assert preview["ok"] is True, node_type
        assert preview["target_path"].endswith(".md")
        assert ".." not in preview["target_path"]
        assert preview["target_path"] == preview["target_path"].replace("\\", "/")


def test_metadata_edit_queues_approval_preserves_body_after_execution(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    rel = "02_KNOWLEDGE/general/edit-me.md"
    path = vault / rel
    path.write_text(_note(body="# Old\n\nBody text.\n"), encoding="utf-8")

    result = queue_metadata_update_approval(
        vault,
        file_path=rel,
        fields={"title": "New Title", "tags": "alpha, beta", "summary": "Short summary"},
    )

    assert result["ok"] is True
    assert result["status"] == "requires_approval"
    assert path.read_text(encoding="utf-8").startswith("---\ntitle: Old")
    assert result["safe_diff_summary"]["field_changes"]["title"] == {"before": "Old", "after": "New Title"}
    assert result["proposal_packet"]["operation_type"] == "edit_metadata"
    assert result["proposal_packet"]["before_after_summary"]["field_changes"]["summary"]["after"] == "Short summary"

    svc = StudioService(vault)
    svc.approve(result["approval_id"])
    action = svc.execute_approved(result["approval_id"])

    assert action.status == "completed"
    rendered = path.read_text(encoding="utf-8")
    assert "title: New Title" in rendered
    assert "- alpha" in rendered
    assert "summary: Short summary" in rendered
    assert "# Old\n\nBody text.\n" in rendered
    assert svc.get_approval(result["approval_id"]).status == "executed"


def test_metadata_edit_same_target_same_field_pending_conflict_blocks(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    rel = "02_KNOWLEDGE/general/edit-me.md"
    path = vault / rel
    path.write_text(_note(), encoding="utf-8")

    first = queue_metadata_update_approval(vault, file_path=rel, fields={"title": "First"})
    second = queue_metadata_update_approval(vault, file_path=rel, fields={"title": "Second"})

    assert first["ok"] is True
    assert second["ok"] is False
    assert second["code"] == "pending_target_collision"
    assert second["conflict_state"]["conflicted"] is True
    assert second["conflict_state"]["conflict_type"] == "pending_target_collision"
    assert second["conflict_state"]["overlapping_fields"] == ["title"]
    assert len(_approval_files(vault)) == 1


def test_api_metadata_edit_pending_conflict_preserves_bounded_evidence_without_content(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    rel = "02_KNOWLEDGE/general/edit-me.md"
    path = vault / rel
    path.write_text(_note(), encoding="utf-8")
    api = StudioAPI(vault)

    first = api.update_node_metadata("", {"title": "First"}, file_path=rel)
    second = api.update_node_metadata("", {"title": "Second"}, file_path=rel)

    assert first["status"] == "requires_approval"
    assert second["ok"] is False
    assert second["error"]["code"] == "pending_target_collision"
    data = second["data"]
    assert data["conflict_state"]["conflicted"] is True
    assert data["conflict_state"]["overlapping_fields"] == ["title"]
    assert data["safe_diff_summary"]["content_stripped"] is True
    assert data["safe_diff_summary"]["field_changes"]["title"] == {"before": "Old", "after": "Second"}
    assert data["proposal_packet"]["operation_type"] == "edit_metadata"
    assert data["proposal_packet"]["conflict_state"]["conflict_type"] == "pending_target_collision"
    assert data["proposal_packet"]["before_after_summary"]["content_stripped"] is True
    assert not _contains_key(data, "content")
    assert len(_approval_files(vault)) == 1


def test_metadata_edit_restricted_fields_are_blocked(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    rel = "02_KNOWLEDGE/general/edit-me.md"
    (vault / rel).write_text(_note(), encoding="utf-8")

    result = queue_metadata_update_approval(vault, file_path=rel, fields={"trust_state": "canonical"})

    assert result["ok"] is False
    assert result["code"] == "restricted_fields"
    assert _approval_files(vault) == []


def test_metadata_edit_malformed_frontmatter_blocks_cleanly(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    rel = "02_KNOWLEDGE/general/bad.md"
    (vault / rel).write_text("---\ntitle: [bad\n---\n# Bad\n", encoding="utf-8")

    result = queue_metadata_update_approval(vault, file_path=rel, fields={"title": "Fixed"})

    assert result["ok"] is False
    assert result["code"] == "malformed_frontmatter"
    assert _approval_files(vault) == []


def test_metadata_edit_missing_frontmatter_is_prepended_after_approval(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    rel = "02_KNOWLEDGE/general/plain.md"
    path = vault / rel
    path.write_text("# Plain\n\nBody stays.\n", encoding="utf-8")

    result = queue_metadata_update_approval(vault, file_path=rel, fields={"title": "Plain Title"})
    assert result["ok"] is True

    svc = StudioService(vault)
    svc.approve(result["approval_id"])
    svc.execute_approved(result["approval_id"])

    rendered = path.read_text(encoding="utf-8")
    assert rendered.startswith("---\ntitle: Plain Title\n---\n# Plain")
    assert "Body stays." in rendered


def test_metadata_edit_missing_node_fails_cleanly(tmp_path: Path) -> None:
    vault = _vault(tmp_path)

    result = queue_metadata_update_approval(vault, node_id="missing-node", fields={"title": "Nope"})

    assert result["ok"] is False
    assert result["code"] == "node_not_found"
    assert _approval_files(vault) == []


def test_metadata_edit_model_returns_allowed_fields(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    rel = "02_KNOWLEDGE/general/edit-me.md"
    (vault / rel).write_text(_note("title: Old\ntags:\n- one\naliases:\n- a\n"), encoding="utf-8")

    model = build_node_metadata_edit_model(vault, file_path=rel)

    assert model["ok"] is True
    assert tuple(model["editable_fields"]) == EDITABLE_METADATA_FIELDS
    assert model["current"]["title"] == "Old"
    assert model["current"]["tags"] == ["one"]
    assert model["write_mode"] == "approval_gated"
    assert model["authority_boundary"]["direct_write_allowed"] is False


def test_protected_file_metadata_edit_is_gate_blocked(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    readme = vault / "README.md"
    readme.write_text("# Readme\n", encoding="utf-8")

    result = queue_metadata_update_approval(vault, file_path="README.md", fields={"title": "Blocked"})

    assert result["ok"] is False
    assert result["code"] == "validation_blocked"
    assert "protected file" in " ".join(result["errors"]).lower()
    assert _approval_files(vault) == []


def test_approval_execution_marks_executed_and_duplicate_blocks(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    result = queue_create_node_approval(vault, "knowledge_doc", "Executable Node", "general")
    svc = StudioService(vault)

    svc.approve(result["approval_id"])
    action = svc.execute_approved(result["approval_id"])

    assert action.status == "completed"
    assert (vault / result["target_path"]).is_file()
    loaded = svc.get_approval(result["approval_id"])
    assert loaded.status == "executed"
    assert loaded.execution_status == "completed"
    assert loaded.result_action_id == action.action_id
    with pytest.raises(StudioServiceError, match="Only 'approved'"):
        svc.execute_approved(result["approval_id"])


def test_approval_execution_reserves_executing_state_before_writes(tmp_path: Path, monkeypatch) -> None:
    vault = _vault(tmp_path)
    result = queue_create_node_approval(vault, "knowledge_doc", "Reserve First", "general")
    observed_statuses: list[str] = []

    def fake_execute(self: StudioService, spec, approval_id=None):  # noqa: ANN001
        approval_path = self._approval_path(approval_id)
        observed_statuses.append(json.loads(approval_path.read_text(encoding="utf-8"))["status"])
        return ActionResult(
            action_id="fake-action",
            action_type=spec.action_type,
            target_path=spec.target_path,
            status="completed",
            submitted_by=spec.submitted_by,
            executed_at="2026-05-07T00:00:00Z",
            approval_id=approval_id,
            writes=[spec.target_path],
        )

    monkeypatch.setattr(StudioService, "_execute", fake_execute)
    svc = StudioService(vault)

    svc.approve(result["approval_id"])
    svc.execute_approved(result["approval_id"])

    assert observed_statuses == ["executing"]
    assert svc.get_approval(result["approval_id"]).status == "executed"
