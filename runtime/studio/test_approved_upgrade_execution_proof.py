"""Tests for Phase 10F6 approved upgrade execution proof."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.approved_upgrade_execution_proof import (
    COMPLETE_STATUS,
    DUPLICATE_BLOCKED_STATUS,
    build_approved_upgrade_execution_proof,
)
from runtime.studio.upgrade_plan_approval_packet import build_upgrade_plan_approval_packet


def _write_approval(tmp_path: Path) -> str:
    model = build_upgrade_plan_approval_packet(tmp_path, target_path=tmp_path, workspace_name="Demo", write_approval=True)
    assert model["ok"] is True
    return str(model["approval_packet"]["id"])


def test_approved_upgrade_execution_requires_execute(tmp_path: Path) -> None:
    packet_id = _write_approval(tmp_path)

    model = build_approved_upgrade_execution_proof(tmp_path, approval_packet_id=packet_id, execute=False)

    assert model["ok"] is False
    assert "execute-flag-required" in model["readiness"]["blockers"]
    assert (tmp_path / model["exact_once_marker"]["path"]).exists() is False


def test_approved_upgrade_execution_blocks_missing_approval(tmp_path: Path) -> None:
    model = build_approved_upgrade_execution_proof(
        tmp_path,
        approval_packet_id="workspace-upgrade-appr-missing",
        execute=True,
    )

    assert model["ok"] is False
    assert "approval_artifact_present" in model["readiness"]["blockers"]


def test_approved_upgrade_execution_writes_marker_before_outputs_and_no_target_writes(tmp_path: Path) -> None:
    packet_id = _write_approval(tmp_path)

    model = build_approved_upgrade_execution_proof(tmp_path, approval_packet_id=packet_id, execute=True)

    assert model["ok"] is True
    assert model["status"] == COMPLETE_STATUS
    assert model["exact_once_marker"]["reserved_before_outputs"] is True
    assert model["authority_boundary"]["writes_proof_outputs"] is True
    assert model["readiness"]["target_workspace_writes_performed"] is False
    assert (tmp_path / model["exact_once_marker"]["path"]).is_file()
    approval_payload = json.loads((tmp_path / model["approval_artifact"]["path"]).read_text(encoding="utf-8"))
    assert approval_payload["approval_decision_consumed"] is True
    assert approval_payload["consumed_by_pass"] == "phase10f6-approved-upgrade-execution-proof"
    assert all(item["exists"] for item in model["proof_outputs"].values())
    assert not (tmp_path / "00_HOME").exists()


def test_approved_upgrade_duplicate_execution_blocks_before_writes(tmp_path: Path) -> None:
    packet_id = _write_approval(tmp_path)
    first = build_approved_upgrade_execution_proof(tmp_path, approval_packet_id=packet_id, execute=True)
    output_times = {
        key: (tmp_path / value["path"]).stat().st_mtime
        for key, value in first["proof_outputs"].items()
    }

    second = build_approved_upgrade_execution_proof(tmp_path, approval_packet_id=packet_id, execute=True)

    assert second["ok"] is False
    assert second["status"] == DUPLICATE_BLOCKED_STATUS
    assert "exact-once-marker-already-present" in second["readiness"]["blockers"]
    assert {
        key: (tmp_path / value["path"]).stat().st_mtime
        for key, value in first["proof_outputs"].items()
    } == output_times
