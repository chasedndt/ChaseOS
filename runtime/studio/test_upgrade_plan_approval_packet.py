"""Tests for Phase 10F5 workspace upgrade approval packet."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.upgrade_plan_approval_packet import (
    APPROVAL_RECORD_TYPE,
    build_upgrade_plan_approval_packet,
)


def test_upgrade_plan_preview_computes_packet_without_writes(tmp_path: Path) -> None:
    model = build_upgrade_plan_approval_packet(tmp_path, target_path=tmp_path, workspace_name="Demo", write_approval=False)

    assert model["ok"] is True
    assert model["pass"] == "phase10f5-upgrade-plan-approval-packet"
    assert model["approval_packet"]["id"].startswith("workspace-upgrade-appr-")
    assert model["approval_packet"]["artifact_written"] is False
    assert model["approval_packet"]["artifact_exists"] is False
    assert model["planned_writes"]["directory_create_count"] >= 1
    assert model["planned_writes"]["anchor_file_create_count"] >= 1
    assert not (tmp_path / "00_HOME").exists()


def test_upgrade_plan_write_approval_writes_scoped_artifact_only(tmp_path: Path) -> None:
    model = build_upgrade_plan_approval_packet(tmp_path, target_path=tmp_path, workspace_name="Demo", write_approval=True)
    artifact = tmp_path / model["approval_packet"]["artifact_path"]

    assert model["ok"] is True
    assert model["approval_packet"]["artifact_written"] is True
    assert artifact.is_file()
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["record_type"] == APPROVAL_RECORD_TYPE
    assert payload["operator_decision"] == "approved"
    assert payload["approval_decision_consumed"] is False
    assert payload["target_workspace_writes_allowed_in_this_pass"] is False
    assert payload["proof_temp_only"] is True
    assert not (tmp_path / "00_HOME").exists()


def test_upgrade_plan_matching_approval_is_reused(tmp_path: Path) -> None:
    first = build_upgrade_plan_approval_packet(tmp_path, target_path=tmp_path, workspace_name="Demo", write_approval=True)
    second = build_upgrade_plan_approval_packet(tmp_path, target_path=tmp_path, workspace_name="Demo", write_approval=True)

    assert first["approval_packet"]["id"] == second["approval_packet"]["id"]
    assert second["approval_packet"]["artifact_reused"] is True
    assert second["approval_packet"]["artifact_written"] is False


def test_upgrade_plan_existing_marker_blocks(tmp_path: Path) -> None:
    preview = build_upgrade_plan_approval_packet(tmp_path, target_path=tmp_path, workspace_name="Demo", write_approval=False)
    marker = tmp_path / preview["exact_once_marker"]["path"]
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("{}", encoding="utf-8")

    blocked = build_upgrade_plan_approval_packet(tmp_path, target_path=tmp_path, workspace_name="Demo", write_approval=False)

    assert blocked["ok"] is False
    assert "exact-once-marker-already-present" in blocked["readiness"]["blockers"]


def test_upgrade_plan_target_file_collision_blocks(tmp_path: Path) -> None:
    target = tmp_path / "not-a-folder"
    target.write_text("x", encoding="utf-8")

    model = build_upgrade_plan_approval_packet(tmp_path, target_path=target, workspace_name="Demo", write_approval=False)

    assert model["ok"] is False
    assert "target-path-is-not-a-directory" in model["readiness"]["blockers"]
