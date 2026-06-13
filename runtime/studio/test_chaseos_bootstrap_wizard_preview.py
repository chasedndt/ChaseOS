"""Tests for Phase 10F4 ChaseOS bootstrap wizard preview."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.chaseos_bootstrap_wizard_preview import (
    NEXT_RECOMMENDED_PASS,
    build_chaseos_bootstrap_wizard_preview,
)


def _snapshot(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): path.read_text(encoding="utf-8")
        for path in root.rglob("*")
        if path.is_file()
    }


def test_empty_folder_returns_read_only_bootstrap_plan(tmp_path: Path) -> None:
    before = _snapshot(tmp_path)

    model = build_chaseos_bootstrap_wizard_preview(tmp_path, workspace_name="Test Brain")

    assert model["ok"] is True
    assert model["pass"] == "phase10f4-chaseos-bootstrap-wizard-preview"
    assert model["target"]["state"] == "empty_directory"
    assert model["summary"]["preview_ready"] is True
    assert model["target_folders"]["required_count"] >= 10
    assert model["target_files"]["required_count"] >= 8
    assert len(model["steps"]) >= 6
    assert model["readiness"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert model["authority_boundary"]["writes_selected_folder"] is False
    assert model["authority_boundary"]["writes_approval_artifacts"] is False
    assert model["authority_boundary"]["invokes_scaffold_generator"] is False
    assert _snapshot(tmp_path) == before


def test_missing_child_target_is_preview_ready_when_parent_exists(tmp_path: Path) -> None:
    target = tmp_path / "New ChaseOS"

    model = build_chaseos_bootstrap_wizard_preview(tmp_path, target_path=target, workspace_name="New ChaseOS")

    assert model["ok"] is True
    assert model["target"]["exists"] is False
    assert model["target"]["state"] == "missing_ready_to_create"
    assert model["summary"]["would_create_folder_count"] >= 10
    assert model["scaffold_command_contract"]["invoked_by_preview"] is False


def test_existing_chaseos_folder_is_detected_without_execution(tmp_path: Path) -> None:
    for rel in ("00_HOME", "01_PROJECTS", "06_AGENTS", "07_LOGS"):
        (tmp_path / rel).mkdir(parents=True)
    for rel in ("README.md", "PROJECT_FOUNDATION.md", "ROADMAP.md", "CLAUDE.md"):
        (tmp_path / rel).write_text("# Anchor\n", encoding="utf-8")

    model = build_chaseos_bootstrap_wizard_preview(tmp_path)

    assert model["ok"] is True
    assert model["target"]["state"] == "existing_partial_chaseos"
    assert "partial-chaseos-shape-present" in model["readiness"]["warnings"]
    assert model["readiness"]["bootstrap_execution_available"] is False


def test_file_target_blocks_cleanly(tmp_path: Path) -> None:
    file_target = tmp_path / "not-a-folder.md"
    file_target.write_text("# File\n", encoding="utf-8")

    model = build_chaseos_bootstrap_wizard_preview(tmp_path, target_path=file_target)

    assert model["ok"] is False
    assert model["target"]["state"] == "blocked_file_collision"
    assert "target-path-is-not-a-directory" in model["readiness"]["blockers"]
    assert model["authority_boundary"]["writes_target_files"] is False


def test_missing_parent_blocks_cleanly(tmp_path: Path) -> None:
    target = tmp_path / "missing-parent" / "child"

    model = build_chaseos_bootstrap_wizard_preview(tmp_path, target_path=target)

    assert model["ok"] is False
    assert model["target"]["state"] == "blocked_missing_parent"
    assert "target-parent-does-not-exist" in model["readiness"]["blockers"]
