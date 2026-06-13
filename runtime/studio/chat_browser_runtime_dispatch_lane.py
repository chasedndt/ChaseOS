"""Governed Chat/Studio browser-runtime dispatch lane proof.

This module is a lower-phase adapter contract that lets Chat/Studio browser-bound
intents bind to the existing Browser CDP read-only proof executor without giving
Chat or Studio direct browser authority. Chat/Studio may render the manifest and
proof posture; only an approved, exact-once Browser CDP proof may execute.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.browser_runtime.cdp_executor_spec import (
    BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID,
    BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
    build_cdp_read_only_executor_spec,
    execute_cdp_read_only_proof,
    validate_cdp_read_only_approval_artifact,
)

MODEL_VERSION = "studio.chat_browser_runtime_dispatch_lane.v1"
SURFACE_ID = "chat_studio_browser_runtime_dispatch_lane"
TARGET_PROFILE_ID = "siteops.browser_cdp_read_only_loopback.v1"
MANIFEST_ID = "chat-studio-browser-runtime-dispatch-lane.v1"
SUPPORTED_ACTIONS = ("navigate", "read-title", "read-url", "read-visible-text", "capture-screenshot", "capture-dom-snapshot")


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _path_exists(path: str | None) -> bool:
    return bool(path) and Path(path).exists()


def build_chat_studio_browser_runtime_dispatch_lane_manifest(
    vault_root: str | Path,
    *,
    target_url: str,
    runtime: str = "Hermes",
    gate_approval_id: str | None = None,
    requested_by_surface: str = "StudioChat",
    browser_target_profile: str = TARGET_PROFILE_ID,
    operator_session_scope: str = "throwaway-local-only",
    browser_auth_ref: str | None = None,
) -> dict[str, Any]:
    """Return the governed lane manifest/readiness packet without execution."""

    vault = Path(vault_root).resolve()
    approval = validate_cdp_read_only_approval_artifact(
        vault,
        gate_approval_id,
        expected_target_url=target_url,
        expected_runtime=runtime,
    )
    executor_spec = build_cdp_read_only_executor_spec(
        vault_root=vault,
        target_url=target_url,
        runtime=runtime,
        gate_approval_id=gate_approval_id,
        source_command="chat/studio browser-runtime dispatch lane manifest",
    )

    denied_cases: dict[str, dict[str, Any]] = {
        "unapproved": {
            "denied": approval.get("approval_status") != "approved",
            "reason": "approved Browser CDP approval artifact required before dispatch",
            "browser_launch_attempted": False,
            "cdp_connection_attempted": False,
            "screenshot_attempted": False,
        },
        "browser_auth_requested": {
            "denied": bool(browser_auth_ref),
            "reason": "authenticated/browser-session flows are outside this read-only loopback target profile",
            "credential_or_cookie_access_allowed": False,
            "real_profile_access_allowed": False,
        },
        "session_scope_missing_or_invalid": {
            "denied": operator_session_scope != "throwaway-local-only",
            "reason": "operator_session_scope must be throwaway-local-only for this proof lane",
            "real_profile_access_allowed": False,
        },
        "unsupported_target_profile": {
            "denied": browser_target_profile != TARGET_PROFILE_ID,
            "reason": f"browser_target_profile must be {TARGET_PROFILE_ID}",
        },
    }
    hard_denials = [key for key, value in denied_cases.items() if value.get("denied")]
    approved_ready = not hard_denials and bool(approval.get("structurally_valid"))

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "manifest_id": MANIFEST_ID,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "requested_by_surface": requested_by_surface,
        "target_profile": {
            "profile_id": TARGET_PROFILE_ID,
            "selected_profile_id": browser_target_profile,
            "siteops_policy": "Browser CDP read-only proof; loopback/local target only; throwaway profile only",
            "operator_session_scope": operator_session_scope,
            "allowed_target_url": target_url,
            "allowed_actions": list(SUPPORTED_ACTIONS),
            "visible_control_ux_required": True,
            "browser_auth_ref_supplied": bool(browser_auth_ref),
            "allow_authenticated_sessions": False,
            "allow_real_profile": False,
            "allow_credentials": False,
            "allow_cookies": False,
            "allow_downloads_uploads_forms_dom_mutation": False,
        },
        "lower_phase_executor": {
            "operation": BROWSER_CDP_READ_ONLY_PROOF_OPERATION,
            "approval_schema_id": BROWSER_CDP_READ_ONLY_PROOF_APPROVAL_SCHEMA_ID,
            "executor_status": executor_spec.get("executor_status"),
            "execution_enabled_by_executor_spec": executor_spec.get("execution_enabled"),
            "gate_policy": executor_spec.get("gate_policy"),
        },
        "approval_record": {
            "gate_approval_id": gate_approval_id,
            "artifact_supplied": approval.get("artifact_supplied"),
            "artifact_ref": approval.get("artifact_ref"),
            "structurally_valid": approval.get("structurally_valid"),
            "approval_status": approval.get("approval_status"),
            "approved_by": approval.get("approved_by"),
            "approved_at": approval.get("approved_at"),
            "request_digest_sha256": approval.get("request_digest_sha256"),
        },
        "readiness": {
            "approved_dispatch_ready": approved_ready,
            "browser_target_profile_ready": browser_target_profile == TARGET_PROFILE_ID,
            "operator_session_scope_ready": operator_session_scope == "throwaway-local-only",
            "browser_auth_session_absent": not bool(browser_auth_ref),
            "hard_denials": hard_denials,
        },
        "denial_proofs": denied_cases,
        "authority": {
            "chat_or_studio_direct_browser_authority": False,
            "requires_lower_phase_executor": True,
            "requires_gate_approval_id": True,
            "approval_consumption_allowed_only_in_executor": True,
            "idempotency_marker_required": True,
            "local_loopback_only": True,
            "throwaway_profile_only": True,
            "credential_or_cookie_access_allowed": False,
            "real_profile_access_allowed": False,
            "provider_call_allowed": False,
            "agent_bus_task_write_allowed": False,
            "canonical_writeback_allowed": False,
        },
        "visible_control_ux": {
            "required": True,
            "operator_must_see_target_url": target_url,
            "operator_must_see_target_profile": TARGET_PROFILE_ID,
            "operator_must_see_approval_id": gate_approval_id,
            "operator_must_see_denial_reasons": hard_denials,
        },
        "executor_spec": executor_spec,
    }


def execute_chat_studio_browser_runtime_dispatch_lane_proof(
    vault_root: str | Path,
    *,
    gate_approval_id: str,
    target_url: str,
    runtime: str = "Hermes",
    requested_by_surface: str = "StudioChat",
    browser_target_profile: str = TARGET_PROFILE_ID,
    operator_session_scope: str = "throwaway-local-only",
    browser_auth_ref: str | None = None,
    launcher: Any | None = None,
    cdp_client: Any | None = None,
) -> dict[str, Any]:
    """Execute one approved lower-phase browser proof for Chat/Studio handoff."""

    manifest = build_chat_studio_browser_runtime_dispatch_lane_manifest(
        vault_root,
        target_url=target_url,
        runtime=runtime,
        gate_approval_id=gate_approval_id,
        requested_by_surface=requested_by_surface,
        browser_target_profile=browser_target_profile,
        operator_session_scope=operator_session_scope,
        browser_auth_ref=browser_auth_ref,
    )
    if manifest["readiness"]["hard_denials"]:
        return {
            "ok": False,
            "status": "blocked_chat_studio_browser_runtime_dispatch_lane_precondition_failed",
            "manifest": manifest,
            "denial_proofs": manifest["denial_proofs"],
            "approval_consumed": False,
            "idempotency_marker_written": False,
            "browser_launch_attempted": False,
            "cdp_connection_attempted": False,
            "screenshot_attempted": False,
            "dom_snapshot_attempted": False,
        }

    result = execute_cdp_read_only_proof(
        vault_root,
        gate_approval_id,
        target_url=target_url,
        runtime=runtime,
        launcher=launcher,
        cdp_client=cdp_client,
        source_command="chat/studio governed browser-runtime dispatch lane proof",
    )
    evidence = {
        "approval_ref": manifest["approval_record"].get("artifact_ref"),
        "consumption_ref": result.get("consumption_ref"),
        "idempotency_marker_ref": result.get("idempotency_marker_ref"),
        "browser_run_log_path": result.get("browser_run_log_path"),
        "agent_activity_log_path": result.get("agent_activity_log_path"),
        "screenshot_path": result.get("screenshot_path"),
        "dom_snapshot_path": result.get("dom_snapshot_path"),
        "skill_candidate_path": result.get("skill_candidate_path"),
    }
    return {
        "ok": bool(result.get("ok")),
        "status": (
            "chat_studio_browser_runtime_dispatch_lane_proof_complete"
            if result.get("ok")
            else result.get("status", "blocked_browser_runtime_executor")
        ),
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "manifest": manifest,
        "bounded_navigation_action_execution_proof": result,
        "evidence_paths": evidence,
        "evidence_paths_exist": {key: _path_exists(value) for key, value in evidence.items()},
        "authority": {
            **manifest["authority"],
            "chat_or_studio_direct_browser_authority": False,
            "lower_phase_executor_invoked": True,
            "credential_or_cookie_access_allowed": False,
            "real_profile_access_allowed": False,
            "canonical_writeback_allowed": False,
        },
    }
