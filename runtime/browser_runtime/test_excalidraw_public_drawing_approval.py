"""Tests for public Excalidraw drawing proof approval packets."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.browser_runtime.excalidraw_public_drawing_approval import (
    EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_BLOCKED,
    EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_READY,
    EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_WRITTEN,
    ExcalidrawPublicDrawingApprovalRequest,
    build_excalidraw_public_drawing_approval,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_public_reachability(root: Path) -> None:
    screenshot = root / "07_LOGS/Browser-Runs/excalidraw_live_proof_20260505-174413.png"
    screenshot.parent.mkdir(parents=True, exist_ok=True)
    screenshot.write_bytes(b"png")
    _write_json(
        root / "07_LOGS/Browser-Runs/excalidraw_live_proof_20260505-174413.json",
        {
            "ok": True,
            "status": "excalidraw_live_browser_proof_complete",
            "target_url": "https://excalidraw.com",
            "canvas_found": True,
            "screenshot_path": "07_LOGS/Browser-Runs/excalidraw_live_proof_20260505-174413.png",
            "authority": {
                "target_registered_in_chaseos": True,
                "target_registry_id": "excalidraw",
                "env_var_required": False,
                "no_login_profile_cookies": True,
                "no_browser_use_cli": True,
                "no_agent_bus_writes": True,
                "no_gate_mutation": True,
                "no_canonical_mutation": True,
                "no_provider_calls": True,
            },
        },
    )


def _seed_legacy_public_reachability(root: Path) -> None:
    screenshot = root / "07_LOGS/Browser-Runs/excalidraw_live_proof_20260505-174413.png"
    screenshot.parent.mkdir(parents=True, exist_ok=True)
    screenshot.write_bytes(b"png")
    _write_json(
        root / "07_LOGS/Browser-Runs/excalidraw_live_proof_20260505-174413.json",
        {
            "ok": True,
            "status": "excalidraw_live_browser_proof_complete",
            "target_url": "https://excalidraw.com",
            "canvas_found": True,
            "screenshot_path": "07_LOGS/Browser-Runs/excalidraw_live_proof_20260505-174413.png",
            "authority": {
                "target_hardcoded": True,
                "env_var_required": False,
                "no_login_profile_cookies": True,
                "no_browser_use_cli": True,
                "no_agent_bus_writes": True,
                "no_gate_mutation": True,
                "no_canonical_mutation": True,
                "no_provider_calls": True,
            },
        },
    )


def test_blocks_without_public_reachability_evidence(tmp_path: Path) -> None:
    result = build_excalidraw_public_drawing_approval(tmp_path)

    assert result.status == EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_BLOCKED
    assert "public_reachability_evidence_ready" in result.blockers
    assert result.future_single_run_approved is False
    assert result.browser_launch_attempted is False
    assert result.drawing_action_attempted is False
    assert result.canonical_writeback_attempted is False


def test_ready_no_execution_with_public_reachability_evidence(tmp_path: Path) -> None:
    _seed_public_reachability(tmp_path)

    result = build_excalidraw_public_drawing_approval(tmp_path)

    assert result.status == EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_READY
    assert result.target_registry_id == "excalidraw"
    assert result.target_url == "https://excalidraw.com"
    assert result.approval_artifact_written is False
    assert result.future_single_run_approved is False
    assert result.execution_allowed_in_this_pass is False
    assert result.next_step == "excalidraw-public-browser-drawing-proof-run"


def test_ready_accepts_legacy_public_reachability_evidence(tmp_path: Path) -> None:
    _seed_legacy_public_reachability(tmp_path)

    result = build_excalidraw_public_drawing_approval(tmp_path)

    assert result.status == EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_READY
    assert result.source_reachability_evidence_path.endswith(
        "excalidraw_live_proof_20260505-174413.json"
    )


def test_write_approval_creates_only_approval_artifact(tmp_path: Path) -> None:
    _seed_public_reachability(tmp_path)

    result = build_excalidraw_public_drawing_approval(
        tmp_path,
        ExcalidrawPublicDrawingApprovalRequest(write_approval=True),
    )

    assert result.status == EXCALIDRAW_PUBLIC_DRAWING_APPROVAL_WRITTEN
    assert result.approval_artifact_written is True
    assert result.future_single_run_approved is True
    assert result.browser_launch_attempted is False
    assert result.target_navigation_attempted is False
    assert result.drawing_action_attempted is False
    assert result.mcp_invocation_attempted is False

    artifact = tmp_path / result.approval_artifact_path
    assert artifact.is_file()
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["approval_id"] == result.approval_id
    assert payload["future_single_run_approved"] is True
    assert payload["execution_allowed_in_this_pass"] is False


def test_write_approval_reuses_matching_existing_artifact(tmp_path: Path) -> None:
    _seed_public_reachability(tmp_path)

    first = build_excalidraw_public_drawing_approval(
        tmp_path,
        ExcalidrawPublicDrawingApprovalRequest(write_approval=True),
    )
    second = build_excalidraw_public_drawing_approval(
        tmp_path,
        ExcalidrawPublicDrawingApprovalRequest(write_approval=True),
    )

    assert first.approval_id == second.approval_id
    assert second.approval_artifact_write_status == "existing_matching_approval_reused"


def test_custom_drawing_label_is_bound_to_digest(tmp_path: Path) -> None:
    _seed_public_reachability(tmp_path)

    first = build_excalidraw_public_drawing_approval(
        tmp_path,
        ExcalidrawPublicDrawingApprovalRequest(drawing_label="ChaseOS proof"),
    )
    second = build_excalidraw_public_drawing_approval(
        tmp_path,
        ExcalidrawPublicDrawingApprovalRequest(drawing_label="Different proof"),
    )

    assert first.approval_id != second.approval_id
    assert second.action_plan["allowed_actions"][2]["text"] == "Different proof"
