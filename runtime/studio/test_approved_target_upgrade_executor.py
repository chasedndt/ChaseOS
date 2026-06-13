"""Tests for Phase 10 temp-target approved upgrade executor proof."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from runtime.studio.approved_target_upgrade_executor import (
    APPROVAL_SCOPE,
    COMPLETE_STATUS,
    DUPLICATE_BLOCKED_STATUS,
    ROLLBACK_SUCCEEDED_STATUS,
    build_approved_target_upgrade_executor,
)


def _canonical_json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _digest(payload: dict) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _target_fingerprint(target: Path) -> dict:
    fingerprint = {"exists": target.exists(), "is_dir": target.is_dir()}
    if target.exists():
        stat_result = target.stat()
        fingerprint["st_dev"] = stat_result.st_dev
        fingerprint["st_ino"] = stat_result.st_ino
    return fingerprint


def _approval_path(vault: Path, packet_id: str) -> Path:
    return vault / "07_LOGS" / "Agent-Activity" / "_workspace_upgrade_approvals" / f"{packet_id}.json"


def _write_target_approval(
    vault: Path,
    target: Path,
    *,
    packet_id: str = "target-upgrade-appr-test",
    approval_scope: str = APPROVAL_SCOPE,
    proof_temp_only: bool = False,
    target_writes_allowed: bool = True,
    planned_writes: list[dict] | None = None,
    target_fingerprint: dict | None = None,
) -> str:
    material = {
        "operation": "workspace_upgrade_target_execution",
        "target_path": str(target.resolve()),
        "target_fingerprint": target_fingerprint if target_fingerprint is not None else _target_fingerprint(target),
        "planned_writes": planned_writes
        or [
            {"operation": "create_directory", "relative_path": "00_HOME"},
            {
                "operation": "create_anchor_file",
                "relative_path": "README.md",
                "content_preview": "# Temp Target\n\nCreated by approved temp-target proof.\n",
            },
            {
                "operation": "create_anchor_file",
                "relative_path": "00_HOME/Now.md",
                "content_preview": "# Now\n\nCreated by approved temp-target proof.\n",
            },
        ],
    }
    request_digest = _digest(material)
    payload = {
        "record_type": "workspace_upgrade_approval_artifact",
        "schema_version": "studio.approved_target_upgrade_executor.test.v1",
        "approval_packet_id": packet_id,
        "request_digest_sha256": request_digest,
        "operator_decision": "approved",
        "approval_scope": approval_scope,
        "approved_material": material,
        "approval_decision_consumed": False,
        "proof_temp_only": proof_temp_only,
        "target_workspace_writes_allowed": target_writes_allowed,
        "target_workspace_writes_allowed_in_this_pass": target_writes_allowed,
    }
    path = _approval_path(vault, packet_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return packet_id


def test_preview_reports_planned_writes_and_writes_nothing(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    packet_id = _write_target_approval(tmp_path, target)

    model = build_approved_target_upgrade_executor(tmp_path, approval_packet_id=packet_id, target_path=target, execute=False)

    assert model["ok"] is False
    assert model["status"] == "preview_only"
    assert model["planned_write_count"] == 3
    assert model["authority_boundary"]["preview_writes_performed"] is False
    assert (target / "README.md").exists() is False
    assert (tmp_path / model["exact_once_marker"]["path"]).exists() is False


def test_execute_rejects_proof_temp_approval_scope(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    packet_id = _write_target_approval(
        tmp_path,
        target,
        approval_scope="one_workspace_upgrade_proof_only",
        proof_temp_only=True,
        target_writes_allowed=False,
    )

    model = build_approved_target_upgrade_executor(tmp_path, approval_packet_id=packet_id, target_path=target, execute=True)

    assert model["ok"] is False
    assert "approval_scope_valid" in model["readiness"]["blockers"]
    assert "proof_temp_only_false" in model["readiness"]["blockers"]
    assert (target / "README.md").exists() is False


def test_execute_accepts_real_target_scope_and_creates_missing_temp_bootstrap_anchors(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    packet_id = _write_target_approval(tmp_path, target)

    model = build_approved_target_upgrade_executor(tmp_path, approval_packet_id=packet_id, target_path=target, execute=True)

    assert model["ok"] is True
    assert model["status"] == COMPLETE_STATUS
    assert model["exact_once_marker"]["reserved_before_target_writes"] is True
    assert (target / "00_HOME").is_dir()
    assert (target / "README.md").read_text(encoding="utf-8").startswith("# Temp Target")
    assert (target / "00_HOME" / "Now.md").is_file()
    approval_payload = json.loads(_approval_path(tmp_path, packet_id).read_text(encoding="utf-8"))
    assert approval_payload["approval_decision_consumed"] is True
    assert model["target_effect_audit"]["created_file_count"] == 2
    assert model["target_effect_audit"]["created_dir_count"] == 1


def test_existing_target_fingerprint_requires_platform_identity_before_writes(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    packet_id = _write_target_approval(tmp_path, target, target_fingerprint={"exists": True, "is_dir": True})

    model = build_approved_target_upgrade_executor(tmp_path, approval_packet_id=packet_id, target_path=target, execute=True)

    assert model["ok"] is False
    assert "target_fingerprint_has_required_platform_identity" in model["readiness"]["blockers"]
    assert (target / "README.md").exists() is False
    assert (tmp_path / model["exact_once_marker"]["path"]).exists() is False


def test_stale_target_fingerprint_blocks_before_marker_evidence_and_target_writes(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    packet_id = _write_target_approval(tmp_path, target, target_fingerprint={"exists": False, "is_dir": False})
    approval_before = json.loads(_approval_path(tmp_path, packet_id).read_text(encoding="utf-8"))

    model = build_approved_target_upgrade_executor(
        tmp_path,
        approval_packet_id=packet_id,
        target_path=target,
        execute=True,
        rollback_after_execute=True,
    )

    assert model["ok"] is False
    assert "target_fingerprint_matches_current_target" in model["readiness"]["blockers"]
    assert (target / "README.md").exists() is False
    assert (tmp_path / model["exact_once_marker"]["path"]).exists() is False
    assert (tmp_path / model["evidence_outputs"]["preflight_report"]["path"]).exists() is False
    approval_after = json.loads(_approval_path(tmp_path, packet_id).read_text(encoding="utf-8"))
    assert approval_after == approval_before


def test_existing_evidence_output_blocks_before_marker_approval_and_target_writes(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    packet_id = _write_target_approval(tmp_path, target, packet_id="evidence-collision-test")
    evidence_root = tmp_path / "07_LOGS" / "Studio-Graph-Views" / "target-upgrade-executions" / packet_id
    evidence_root.mkdir(parents=True)
    existing_preflight = evidence_root / "preflight-report.json"
    existing_preflight.write_text('{"operator":"existing evidence"}', encoding="utf-8")
    approval_before = json.loads(_approval_path(tmp_path, packet_id).read_text(encoding="utf-8"))

    model = build_approved_target_upgrade_executor(tmp_path, approval_packet_id=packet_id, target_path=target, execute=True)

    assert model["ok"] is False
    assert "evidence-output-already-exists:preflight_report" in model["readiness"]["blockers"]
    assert existing_preflight.read_text(encoding="utf-8") == '{"operator":"existing evidence"}'
    assert (target / "README.md").exists() is False
    assert (tmp_path / model["exact_once_marker"]["path"]).exists() is False
    approval_after = json.loads(_approval_path(tmp_path, packet_id).read_text(encoding="utf-8"))
    assert approval_after == approval_before


def test_duplicate_marker_blocks_before_target_writes(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    packet_id = _write_target_approval(tmp_path, target)
    first = build_approved_target_upgrade_executor(tmp_path, approval_packet_id=packet_id, target_path=target, execute=True)
    marker_mtime = (tmp_path / first["exact_once_marker"]["path"]).stat().st_mtime
    readme_mtime = (target / "README.md").stat().st_mtime

    second = build_approved_target_upgrade_executor(tmp_path, approval_packet_id=packet_id, target_path=target, execute=True)

    assert second["ok"] is False
    assert second["status"] == DUPLICATE_BLOCKED_STATUS
    assert "exact-once-marker-already-present" in second["readiness"]["blockers"]
    assert (tmp_path / first["exact_once_marker"]["path"]).stat().st_mtime == marker_mtime
    assert (target / "README.md").stat().st_mtime == readme_mtime


def test_existing_files_are_not_overwritten(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    (target / "README.md").write_text("operator content", encoding="utf-8")
    packet_id = _write_target_approval(tmp_path, target)

    model = build_approved_target_upgrade_executor(tmp_path, approval_packet_id=packet_id, target_path=target, execute=True)

    assert model["ok"] is False
    assert "write-would-overwrite-existing-path:README.md" in model["readiness"]["blockers"]
    assert (target / "README.md").read_text(encoding="utf-8") == "operator content"


def test_path_policy_blocks_protected_foreign_absolute_and_symlink_escape_operations(tmp_path: Path) -> None:
    target = tmp_path / "target"
    foreign = tmp_path / "foreign"
    target.mkdir()
    foreign.mkdir()
    (target / "linked").symlink_to(foreign, target_is_directory=True)
    packet_id = _write_target_approval(
        tmp_path,
        target,
        planned_writes=[
            {"operation": "create_anchor_file", "relative_path": "06_AGENTS/Permission-Matrix.md", "content_preview": "x"},
            {"operation": "create_anchor_file", "relative_path": "../foreign/escape.md", "content_preview": "x"},
            {"operation": "create_anchor_file", "relative_path": str((target / "absolute.md").resolve()), "content_preview": "x"},
            {"operation": "create_anchor_file", "relative_path": "linked/escape.md", "content_preview": "x"},
        ],
    )

    model = build_approved_target_upgrade_executor(tmp_path, approval_packet_id=packet_id, target_path=target, execute=True)

    assert model["ok"] is False
    blockers = model["readiness"]["blockers"]
    assert "protected-path-blocked:06_AGENTS/Permission-Matrix.md" in blockers
    assert "path-escapes-target-root:../foreign/escape.md" in blockers
    assert any(item.startswith("absolute-planned-target-path-blocked:") for item in blockers)
    assert "path-escapes-target-root:linked/escape.md" in blockers
    assert list(foreign.iterdir()) == []


def test_rollback_plan_and_result_remove_only_created_paths(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    (target / "operator.md").write_text("keep", encoding="utf-8")
    packet_id = _write_target_approval(tmp_path, target)

    model = build_approved_target_upgrade_executor(
        tmp_path,
        approval_packet_id=packet_id,
        target_path=target,
        execute=True,
        rollback_after_execute=True,
    )

    assert model["ok"] is True
    assert model["status"] == ROLLBACK_SUCCEEDED_STATUS
    assert model["rollback_plan"]["generated_before_target_writes"] is True
    assert (target / "README.md").exists() is False
    assert (target / "00_HOME" / "Now.md").exists() is False
    assert (target / "00_HOME").exists() is False
    assert (target / "operator.md").read_text(encoding="utf-8") == "keep"
    assert model["rollback_result"]["removed_file_count"] == 2
    assert model["rollback_result"]["removed_dir_count"] == 1
