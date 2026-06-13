"""Tests for approved public Excalidraw drawing proof runner."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from runtime.browser_runtime.excalidraw_public_drawing_approval import (
    ExcalidrawPublicDrawingApprovalRequest,
    build_excalidraw_public_drawing_approval,
)
from runtime.browser_runtime.excalidraw_public_drawing_proof import (
    EXCALIDRAW_PUBLIC_DRAWING_PROOF_BLOCKED,
    EXCALIDRAW_PUBLIC_DRAWING_PROOF_COMPLETE,
    run_excalidraw_public_drawing_proof,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_reachability(root: Path) -> None:
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


def _seed_approval(root: Path) -> str:
    _seed_reachability(root)
    approval = build_excalidraw_public_drawing_approval(
        root,
        ExcalidrawPublicDrawingApprovalRequest(write_approval=True),
    )
    return approval.approval_id


def _approval_marker_path(root: Path, approval_id: str) -> Path:
    payload = json.loads(
        (
            root
            / "07_LOGS/Agent-Activity/_excalidraw_public_drawing_approvals"
            / f"{approval_id}.json"
        ).read_text(encoding="utf-8")
    )
    return root / payload["idempotency_marker_path"]


def _mock_playwright() -> MagicMock:
    mock_canvas = MagicMock()
    mock_canvas.bounding_box.return_value = {"x": 0, "y": 0, "width": 1280, "height": 800}
    mock_page = MagicMock()
    mock_page.title.return_value = "Excalidraw Whiteboard"
    mock_page.query_selector_all.return_value = [mock_canvas]

    screenshots = [b"before", b"after"]

    def _screenshot(*args, **kwargs):
        data = screenshots.pop(0) if screenshots else b"after"
        if kwargs.get("path"):
            Path(kwargs["path"]).write_bytes(data)
        return data

    mock_page.screenshot.side_effect = _screenshot
    mock_page.evaluate.return_value = {
        "local_storage_key_count": 1,
        "local_storage_keys": ["excalidraw"],
        "contains_label": True,
        "contains_rectangle": True,
    }
    mock_context = MagicMock()
    mock_context.new_page.return_value = mock_page
    mock_browser = MagicMock()
    mock_browser.new_context.return_value = mock_context
    mock_pw = MagicMock()
    mock_pw.chromium.launch.return_value = mock_browser
    mock_sync = MagicMock()
    mock_sync.__enter__ = MagicMock(return_value=mock_pw)
    mock_sync.__exit__ = MagicMock(return_value=False)
    return mock_sync


def test_blocks_without_approval(tmp_path: Path) -> None:
    result = run_excalidraw_public_drawing_proof(tmp_path, write_evidence=False)

    assert result["status"] == EXCALIDRAW_PUBLIC_DRAWING_PROOF_BLOCKED
    assert "valid_public_drawing_approval_not_found" in result["blockers"]
    assert result["browser_launch_attempted"] is False


def test_blocks_when_marker_exists(tmp_path: Path) -> None:
    approval_id = _seed_approval(tmp_path)
    marker = _approval_marker_path(tmp_path, approval_id)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("{}", encoding="utf-8")

    result = run_excalidraw_public_drawing_proof(tmp_path, write_evidence=False)

    assert result["status"] == EXCALIDRAW_PUBLIC_DRAWING_PROOF_BLOCKED
    assert "idempotency_marker_already_exists" in result["blockers"]
    assert result["browser_launch_attempted"] is False


def test_success_writes_evidence_and_marker(tmp_path: Path) -> None:
    approval_id = _seed_approval(tmp_path)
    mock_sync = _mock_playwright()
    with (
        patch("runtime.browser_runtime.excalidraw_public_drawing_proof._PLAYWRIGHT_AVAILABLE", True),
        patch("runtime.browser_runtime.excalidraw_public_drawing_proof.sync_playwright", return_value=mock_sync),
    ):
        result = run_excalidraw_public_drawing_proof(
            tmp_path,
            approval_id=approval_id,
            run_slug="test-proof",
        )

    assert result["ok"] is True
    assert result["status"] == EXCALIDRAW_PUBLIC_DRAWING_PROOF_COMPLETE
    assert result["approval_id"] == approval_id
    assert result["browser_launch_attempted"] is True
    assert result["target_navigation_attempted"] is True
    assert result["drawing_action_attempted"] is True
    assert result["mcp_invocation_attempted"] is False
    assert result["provider_call_attempted"] is False
    assert result["canonical_writeback_attempted"] is False
    assert (tmp_path / result["evidence_json_path"]).is_file()
    assert (tmp_path / result["agent_activity_evidence_path"]).is_file()
    marker = tmp_path / result["idempotency_marker_path"]
    assert marker.is_file()
    marker_payload = json.loads(marker.read_text(encoding="utf-8"))
    assert marker_payload["status"] == "completed"


def test_playwright_failure_writes_failed_marker(tmp_path: Path) -> None:
    approval_id = _seed_approval(tmp_path)
    mock_sync = MagicMock()
    mock_sync.__enter__ = MagicMock(side_effect=RuntimeError("browser unavailable"))
    mock_sync.__exit__ = MagicMock(return_value=False)
    with (
        patch("runtime.browser_runtime.excalidraw_public_drawing_proof._PLAYWRIGHT_AVAILABLE", True),
        patch("runtime.browser_runtime.excalidraw_public_drawing_proof.sync_playwright", return_value=mock_sync),
    ):
        result = run_excalidraw_public_drawing_proof(
            tmp_path,
            approval_id=approval_id,
            run_slug="fail-proof",
        )

    assert result["ok"] is False
    assert any("playwright_drawing_error" in blocker for blocker in result["blockers"])
    marker = tmp_path / result["idempotency_marker_path"]
    marker_payload = json.loads(marker.read_text(encoding="utf-8"))
    assert marker_payload["status"] == "failed"
