from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path

from runtime.browser_runtime.media_editor_autonomy_proof import (
    MEDIA_EDITOR_AUTONOMY_PROOF_BLOCKED_MARKER_EXISTS,
    MEDIA_EDITOR_AUTONOMY_PROOF_BLOCKED_NO_EXECUTION,
    MEDIA_EDITOR_AUTONOMY_PROOF_COMPLETE,
    MediaEditorAutonomyProofRequest,
    main,
    run_media_editor_autonomy_proof,
)


class FakeMediaController:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.state = {
            "mediaLayerAdded": False,
            "textLayerAdded": False,
            "shapeLayerAdded": False,
            "filterApplied": False,
            "exportBlocked": False,
            "accountSettingsBlocked": False,
            "layers": [],
        }

    def ensure_available(self) -> dict[str, object]:
        self.calls.append("ensure_available")
        return {"available": True}

    def open(self, url: str) -> dict[str, object]:
        self.calls.append("open")
        return {"opened_url": url, "profile_policy": "throwaway_only"}

    def read_state(self) -> dict[str, object]:
        self.calls.append("read_state")
        return {
            "title": "SiteOps Local Media Editor Shadow Target",
            "url": "http://127.0.0.1:9999/siteops_media_editor_shadow.html",
            "visible_text": "Local Media Editor",
            "editor_state": dict(self.state),
        }

    def click_testid(self, testid: str) -> dict[str, object]:
        self.calls.append(f"click:{testid}")
        if testid == "add-media-layer":
            self.state["mediaLayerAdded"] = True
            self.state["layers"].append("media")
        elif testid == "add-text-layer":
            self.state["textLayerAdded"] = True
            self.state["layers"].append("title")
        elif testid == "add-shape-layer":
            self.state["shapeLayerAdded"] = True
            self.state["layers"].append("shape")
        elif testid == "apply-filter":
            self.state["filterApplied"] = True
        elif testid == "export-file":
            self.state["exportBlocked"] = True
        elif testid == "account-settings":
            self.state["accountSettingsBlocked"] = True
        return {"ok": True, "testid": testid, "state": dict(self.state)}

    def capture_screenshot(self) -> bytes:
        self.calls.append("capture_screenshot")
        return b"fake-media-editor-png"

    def close(self) -> None:
        self.calls.append("close")


def _request(**overrides: object) -> MediaEditorAutonomyProofRequest:
    payload = {
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
        "requested_by": "Codex",
        "operator_id": "local-user",
        "execute_browser": True,
        "run_slug": "media-editor-proof-test",
    }
    payload.update(overrides)
    return MediaEditorAutonomyProofRequest(**payload)


def test_no_execute_blocks_without_writes(tmp_path: Path) -> None:
    result = run_media_editor_autonomy_proof(
        tmp_path,
        _request(execute_browser=False),
        generated_at="2026-05-04T15:00:00Z",
        controller=FakeMediaController(),
    )

    assert result.status == MEDIA_EDITOR_AUTONOMY_PROOF_BLOCKED_NO_EXECUTION
    assert result.browser_launch_attempted is False
    assert not list(tmp_path.rglob("*"))


def test_injected_media_editor_proof_writes_scoped_artifacts(tmp_path: Path) -> None:
    controller = FakeMediaController()
    result = run_media_editor_autonomy_proof(
        tmp_path,
        _request(),
        generated_at="2026-05-04T15:05:00Z",
        controller=controller,
    )

    assert result.status == MEDIA_EDITOR_AUTONOMY_PROOF_COMPLETE
    assert result.scope == {"tenant_id": "local", "workspace_id": "default", "user_id": "local-user"}
    assert result.approval_record_written is True
    assert result.idempotency_marker_written is True
    assert result.browser_launch_attempted is True
    assert result.cdp_connection_attempted is True
    assert result.browser_actions_attempted is True
    assert result.screenshot_artifact_written is True
    assert result.final_editor_state["mediaLayerAdded"] is True
    assert result.final_editor_state["textLayerAdded"] is True
    assert result.final_editor_state["shapeLayerAdded"] is True
    assert result.final_editor_state["filterApplied"] is True
    assert result.final_editor_state["exportBlocked"] is True
    assert result.final_editor_state["accountSettingsBlocked"] is True
    assert Path(result.approval_record_path).exists()
    assert Path(result.idempotency_marker_path).exists()
    assert Path(result.browser_run_log_path).exists()
    assert Path(result.agent_activity_log_path).exists()
    assert Path(result.siteops_run_path).exists()
    assert Path(result.siteops_audit_path).exists()
    assert Path(result.screenshot_path).read_bytes() == b"fake-media-editor-png"
    assert all(value is False for value in result.denied_effects.values())
    assert "click:export-file" in controller.calls
    assert "click:account-settings" in controller.calls


def test_duplicate_marker_blocks_before_browser(tmp_path: Path) -> None:
    run_media_editor_autonomy_proof(
        tmp_path,
        _request(),
        generated_at="2026-05-04T15:05:00Z",
        controller=FakeMediaController(),
    )
    controller = FakeMediaController()
    result = run_media_editor_autonomy_proof(
        tmp_path,
        _request(),
        generated_at="2026-05-04T15:05:00Z",
        controller=controller,
    )

    assert result.status == MEDIA_EDITOR_AUTONOMY_PROOF_BLOCKED_MARKER_EXISTS
    assert result.browser_launch_attempted is False
    assert controller.calls == []


def test_cli_json_emits_media_editor_proof(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "runtime.browser_runtime.media_editor_autonomy_proof.LiveCDPMediaEditorController",
        FakeMediaController,
    )
    stream = io.StringIO()
    with redirect_stdout(stream):
        code = main(
            [
                "--vault-root",
                str(tmp_path),
                "--execute-browser",
                "--run-slug",
                "media-editor-cli-proof-test",
                "--json",
            ]
        )

    payload = json.loads(stream.getvalue())
    assert code == 0
    assert payload["status"] == MEDIA_EDITOR_AUTONOMY_PROOF_COMPLETE
    assert payload["final_editor_state"]["exportBlocked"] is True
    assert payload["canonical_writeback_attempted"] is False if "canonical_writeback_attempted" in payload else True
