"""Tests for governed Chat/Studio browser-runtime dispatch lane."""

from __future__ import annotations

from pathlib import Path

from runtime.browser_runtime.cdp_executor_spec import (
    write_cdp_read_only_approval_decision,
    write_cdp_read_only_approval_request,
)
from runtime.studio.chat_browser_runtime_dispatch_lane import (
    TARGET_PROFILE_ID,
    build_chat_studio_browser_runtime_dispatch_lane_manifest,
    execute_chat_studio_browser_runtime_dispatch_lane_proof,
)


class _FakeCDPLauncher:
    def __init__(self) -> None:
        self.launched = False
        self.closed = False

    def launch(self) -> dict[str, object]:
        self.launched = True
        return {"cdp_endpoint": "http://127.0.0.1:9222", "browser_pid": 12345, "user_data_dir": "[REDACTED]"}

    def close(self) -> None:
        self.closed = True


class _FakeCDPClient:
    def __init__(self) -> None:
        self.connected = False
        self.navigated_to: str | None = None

    def connect(self, endpoint: str) -> None:
        self.connected = True
        self.endpoint = endpoint

    def navigate(self, target_url: str) -> None:
        self.navigated_to = target_url

    def read_state(self) -> dict[str, object]:
        return {
            "title": "Chat Studio Browser Dispatch Proof",
            "url": self.navigated_to,
            "visible_text": "Bounded Chat/Studio browser proof page",
            "dom_snapshot": {"nodes": [{"nodeName": "BODY", "text": "bounded proof"}]},
        }

    def capture_screenshot(self) -> bytes:
        return b"fake-chat-studio-browser-png"

    def close(self) -> None:
        self.connected = False


def _approved_request(root: Path, target_url: str = "http://127.0.0.1:4173") -> dict[str, object]:
    request = write_cdp_read_only_approval_request(
        root,
        target_url=target_url,
        runtime="Hermes",
        requested_by="StudioChat",
    )
    write_cdp_read_only_approval_decision(root, str(request["gate_approval_id"]), approved_by="operator")
    return request


def test_manifest_exposes_target_profile_policy_and_denies_missing_approval(tmp_path: Path) -> None:
    manifest = build_chat_studio_browser_runtime_dispatch_lane_manifest(
        tmp_path,
        target_url="http://127.0.0.1:4173",
        runtime="Hermes",
    )

    assert manifest["surface"] == "chat_studio_browser_runtime_dispatch_lane"
    assert manifest["target_profile"]["profile_id"] == TARGET_PROFILE_ID
    assert manifest["target_profile"]["operator_session_scope"] == "throwaway-local-only"
    assert manifest["target_profile"]["allow_authenticated_sessions"] is False
    assert manifest["target_profile"]["allow_credentials"] is False
    assert manifest["target_profile"]["allow_cookies"] is False
    assert manifest["readiness"]["approved_dispatch_ready"] is False
    assert "unapproved" in manifest["readiness"]["hard_denials"]
    assert manifest["denial_proofs"]["unapproved"]["browser_launch_attempted"] is False
    assert manifest["authority"]["chat_or_studio_direct_browser_authority"] is False
    assert manifest["visible_control_ux"]["required"] is True


def test_approved_lane_executes_bounded_cdp_proof_and_reports_evidence_paths(tmp_path: Path) -> None:
    request = _approved_request(tmp_path)
    launcher = _FakeCDPLauncher()
    client = _FakeCDPClient()

    proof = execute_chat_studio_browser_runtime_dispatch_lane_proof(
        tmp_path,
        gate_approval_id=str(request["gate_approval_id"]),
        target_url="http://127.0.0.1:4173",
        runtime="Hermes",
        launcher=launcher,
        cdp_client=client,
    )

    assert proof["ok"] is True
    assert proof["status"] == "chat_studio_browser_runtime_dispatch_lane_proof_complete"
    result = proof["bounded_navigation_action_execution_proof"]
    assert result["approval_consumed"] is True
    assert result["idempotency_marker_written"] is True
    assert result["browser_launch_attempted"] is True
    assert result["cdp_connection_attempted"] is True
    assert result["screenshot_attempted"] is True
    assert result["dom_snapshot_attempted"] is True
    assert result["credential_value_read"] is False
    assert result["cookie_or_session_read"] is False
    assert result["real_profile_used"] is False
    assert result["canonical_files_mutated"] is False
    assert launcher.launched is True
    assert launcher.closed is True
    assert client.navigated_to == "http://127.0.0.1:4173"
    for key in (
        "approval_ref",
        "consumption_ref",
        "idempotency_marker_ref",
        "browser_run_log_path",
        "agent_activity_log_path",
        "screenshot_path",
        "dom_snapshot_path",
        "skill_candidate_path",
    ):
        assert proof["evidence_paths_exist"][key] is True


def test_lane_denies_auth_session_scope_and_unknown_profile_before_browser_launch(tmp_path: Path) -> None:
    request = _approved_request(tmp_path)
    launcher = _FakeCDPLauncher()
    proof = execute_chat_studio_browser_runtime_dispatch_lane_proof(
        tmp_path,
        gate_approval_id=str(request["gate_approval_id"]),
        target_url="http://127.0.0.1:4173",
        runtime="Hermes",
        browser_target_profile="real-profile-browser",
        operator_session_scope="existing-user-session",
        browser_auth_ref="session:do-not-use",
        launcher=launcher,
        cdp_client=_FakeCDPClient(),
    )

    assert proof["ok"] is False
    assert proof["status"] == "blocked_chat_studio_browser_runtime_dispatch_lane_precondition_failed"
    assert proof["approval_consumed"] is False
    assert proof["browser_launch_attempted"] is False
    assert proof["cdp_connection_attempted"] is False
    assert launcher.launched is False
    hard_denials = set(proof["manifest"]["readiness"]["hard_denials"])
    assert hard_denials >= {
        "browser_auth_requested",
        "session_scope_missing_or_invalid",
        "unsupported_target_profile",
    }
    assert proof["denial_proofs"]["browser_auth_requested"]["credential_or_cookie_access_allowed"] is False
    assert proof["denial_proofs"]["session_scope_missing_or_invalid"]["real_profile_access_allowed"] is False
