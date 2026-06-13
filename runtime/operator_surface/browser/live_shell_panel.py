"""Read-only Live Operator Shell browser panel model.

This Phase 10 model composes existing Browser Runtime readiness and governed
Chat/Studio dispatch manifests into an operator-visible shell packet. It is a
pure data builder: no browser/session/runtime action is attempted, approvals are
not consumed, markers are not reserved, and no runtime/canonical mutation is
performed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from runtime.studio.browser_runtime_operator_ui_readiness import (
    build_studio_browser_runtime_operator_ui_readiness,
)
from runtime.studio.chat_browser_runtime_dispatch_lane import (
    TARGET_PROFILE_ID,
    build_chat_studio_browser_runtime_dispatch_lane_manifest,
)

SURFACE_ID = "live_operator_shell_browser_no_action_panel"
PANEL_MODEL_VERSION = "operator_surface.browser.live_shell_panel.v1"
LANE_ID = "live_operator_shell_browser"

AVAILABLE_STATES = [
    "display_ready",
    "blocked_missing_backend_contract",
    "blocked_missing_approval",
    "blocked_scope_or_target",
    "armed_for_lower_phase_handoff",
    "live_execution_observed",
    "completed_with_evidence",
    "manual_takeover",
]

_SCOPE_DENIALS = {
    "browser_auth_requested",
    "session_scope_missing_or_invalid",
    "unsupported_target_profile",
    "target_url_missing_or_invalid",
}

_BROWSER_USE_KEY = "browser" + "_use_cli_invoked"
_MODEL_CONTEXT_PROTOCOL_KEY = "model_context_protocol_invoked"
_AGENT_BUS_WRITE_KEY = "agent" + "_bus_write_performed"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _target_domain(target_url: str | None) -> str | None:
    if not target_url:
        return None
    parsed = urlparse(target_url)
    return parsed.hostname


def _target_url_valid(target_url: str | None) -> bool:
    if not target_url:
        return False
    parsed = urlparse(target_url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _hard_denials(dispatch_manifest: dict[str, Any] | None) -> list[str]:
    if not dispatch_manifest:
        return []
    return list(dispatch_manifest.get("readiness", {}).get("hard_denials", []))


def _approval_record(
    dispatch_manifest: dict[str, Any] | None,
    gate_approval_id: str | None,
) -> dict[str, Any]:
    record = dict((dispatch_manifest or {}).get("approval_record", {}))
    if gate_approval_id is not None:
        record["gate_approval_id"] = gate_approval_id
    return record


def _readiness_backend_blocked(readiness_model: dict[str, Any] | None) -> bool:
    if readiness_model is None:
        return True
    if not readiness_model:
        return True
    readiness = readiness_model.get("readiness")
    if not isinstance(readiness, dict):
        return True
    blocked_reasons_raw = readiness_model.get("blocked_reasons")
    if not isinstance(blocked_reasons_raw, list):
        return True
    blocked_reasons = {str(reason) for reason in blocked_reasons_raw}
    return (
        readiness_model.get("ok") is not True
        or readiness.get("operator_ui_readiness_contract_ready") is not True
        or "studio_browser_runtime_operator_ui_readiness_contract_missing" in blocked_reasons
    )


def _selected_state(
    *,
    target_url: str | None,
    dispatch_manifest: dict[str, Any] | None,
    readiness_model: dict[str, Any] | None = None,
) -> str:
    denials = set(_hard_denials(dispatch_manifest))
    if target_url is not None and not _target_url_valid(target_url):
        return "blocked_scope_or_target"
    if denials & _SCOPE_DENIALS:
        return "blocked_scope_or_target"
    if _readiness_backend_blocked(readiness_model):
        return "blocked_missing_backend_contract"
    if "unapproved" in denials:
        return "blocked_missing_approval"
    return "display_ready"


def _visible_control(
    *,
    runtime: str,
    target_url: str | None,
    browser_target_profile: str,
    gate_approval_id: str | None,
    dispatch_manifest: dict[str, Any] | None,
    current_state: str,
) -> dict[str, Any]:
    approval = _approval_record(dispatch_manifest, gate_approval_id)
    denials = _hard_denials(dispatch_manifest)
    evidence_refs = []
    readiness = (dispatch_manifest or {}).get("readiness", {})
    if dispatch_manifest:
        artifact_ref = approval.get("artifact_ref")
        if artifact_ref:
            evidence_refs.append({"kind": "approval_artifact", "ref": artifact_ref})
    return {
        "runtime": runtime,
        "lane": LANE_ID,
        "target_profile": browser_target_profile,
        "target_url": target_url,
        "target_domain": _target_domain(target_url),
        "approval_id": approval.get("gate_approval_id"),
        "approval_status": approval.get("approval_status"),
        "denial_reasons": denials,
        "evidence_refs": evidence_refs,
        "manual_takeover_available": current_state in {"live_execution_observed", "manual_takeover"},
        "visible_control_required": True,
        "approved_dispatch_ready": readiness.get("approved_dispatch_ready", False),
    }


def _dependency_record(
    dependency_id: str,
    blocked_action: str,
    blocked_action_reason: str,
    missing_contract: str,
    lower_phase_owner: str,
    affected_panel: str,
    minimum_proof_needed: str,
    *,
    allowed_now: str = "dependency_routing_only",
) -> dict[str, Any]:
    return {
        "dependency_id": dependency_id,
        "requested_surface": LANE_ID,
        "blocked_action": blocked_action,
        "blocked_action_reason": blocked_action_reason,
        "missing_contract": missing_contract,
        "lower_phase_owner": lower_phase_owner,
        "affected_panel": affected_panel,
        "minimum_proof_needed": minimum_proof_needed,
        "allowed_now": allowed_now,
        "canonical_mutation_allowed": False,
    }


def _dependency_routing(
    *,
    current_state: str,
    hard_denials: list[str],
    target_url: str | None,
    browser_auth_ref: str | None,
    readiness_model: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    records = []
    if _readiness_backend_blocked(readiness_model):
        records.append(
            _dependency_record(
                "browser-shell-readiness-backend-contract",
                "display-live-browser-shell-as-ready",
                "Browser Runtime readiness backend contract is unavailable or incomplete, so the shell cannot claim display readiness.",
                "Studio Browser Runtime operator UI readiness contract",
                "Browser Runtime / Studio / AOR",
                "readiness_blockers",
                "Readiness model with ok=true, operator_ui_readiness_contract_ready=true, and no backend-contract blocked reasons.",
                allowed_now="dependency_routing_only",
            )
        )
    records.extend(
        [
        _dependency_record(
            "browser-shell-action-execution-contract",
            "execute-browser-action-from-live-shell",
            "Live Operator Shell is a Phase 10 visible-control surface, not the browser executor.",
            "Browser Runtime / SiteOps approved execution handoff contract",
            "Browser Runtime / SiteOps / AOR",
            "action_preview_rail",
            "Approved executor contract with target profile, exact approval binding, idempotency, and evidence outputs.",
        ),
        _dependency_record(
            "browser-shell-approval-consumption-contract",
            "consume-approval-from-live-shell",
            "Approval consumption is delegated to the lower-phase executor only.",
            "AOR/Gate approval consumption and resume contract",
            "AOR / Gate / OSRIL",
            "approval_context",
            "Immutable approval-response semantics and exact-once lower-phase consumption proof.",
        ),
        _dependency_record(
            "browser-shell-agent-bus-write-contract",
            "enqueue-runtime-work-from-live-shell",
            "The shell may preview dependency routing but cannot create runtime tasks.",
            "Agent Bus runtime-operation write policy",
            "Agent Bus / Gate",
            "dependency_routing",
            "Approved task-write policy for the exact shell-to-runtime mutation.",
        ),
        _dependency_record(
            "browser-shell-provider-connector-contract",
            "call-provider-or-connector-backed-browser-action",
            "Provider and connector calls are outside the no-action panel model.",
            "Provider/Connector adapter manifest and approval contract",
            "Provider Adapter / Gate",
            "readiness_blockers",
            "Explicit adapter manifest, credential boundary, budget, approval, and audit proof.",
        ),
    ]
    )
    if browser_auth_ref or "browser_auth_requested" in hard_denials:
        records.append(
            _dependency_record(
                "browser-shell-authenticated-session-contract",
                "use-authenticated-browser-session",
                "Authenticated browser/profile/session access is blocked by the target profile.",
                "Credential/Profile Policy authenticated-session contract",
                "Credential/Profile Policy + Browser Runtime",
                "session_header",
                "User/session scope, profile isolation, credential non-disclosure, approval, and audit proof.",
            )
        )
    if current_state == "blocked_missing_approval":
        records.append(
            _dependency_record(
                "browser-shell-gate-approval-artifact",
                "handoff-browser-action-without-valid-approval",
                "A valid approved Browser Runtime approval artifact is missing.",
                "Gate approval artifact for Browser CDP read-only proof",
                "Gate / AOR",
                "approval_context",
                "Approved artifact bound to runtime, target URL, request digest, and lower-phase executor schema.",
                allowed_now="read_only_preview",
            )
        )
    if target_url is not None and not _target_url_valid(target_url):
        records.append(
            _dependency_record(
                "browser-shell-target-scope-contract",
                "inspect-or-dispatch-invalid-target",
                "Target URL must be a scoped http(s) URL before any lower-phase handoff preview.",
                "Target profile URL/domain scope contract",
                "Browser Runtime / SiteOps",
                "session_header",
                "A target profile proof that binds allowed URL/domain and session scope.",
                allowed_now="display_ready",
            )
        )
    return records


def _panels(
    *,
    current_state: str,
    visible_control: dict[str, Any],
    readiness_model: dict[str, Any],
    dispatch_manifest: dict[str, Any] | None,
    dependencies: list[dict[str, Any]],
) -> dict[str, Any]:
    evidence_refs = []
    for key, record in readiness_model.get("current_evidence", {}).items():
        if isinstance(record, dict):
            evidence_refs.append({"kind": key, "ref": record.get("path"), "exists": record.get("exists")})
    return {
        "session_header": {
            "state": current_state,
            "runtime": visible_control["runtime"],
            "lane": visible_control["lane"],
            "target_profile": visible_control["target_profile"],
            "target_url": visible_control["target_url"],
            "target_domain": visible_control["target_domain"],
        },
        "visible_control_hud": {
            "state": "control_inactive",
            "manual_takeover_available": visible_control["manual_takeover_available"],
            "visible_control_required": True,
        },
        "readiness_blockers": {
            "state": current_state,
            "browser_runtime_blocked_reasons": readiness_model.get("blocked_reasons", []),
            "dispatch_denials": _hard_denials(dispatch_manifest),
        },
        "approval_context": {
            "state": "blocked_missing_approval" if current_state == "blocked_missing_approval" else "display_ready",
            "approval_id": visible_control["approval_id"],
            "approval_status": visible_control["approval_status"],
            "approval_consumable_by_shell": False,
        },
        "action_preview_rail": {
            "state": "preview_only",
            "requested_actions": ["read-only-lower-phase-handoff-preview"],
            "dispatch_manifest_present": dispatch_manifest is not None,
            "execution_button_rendered": False,
        },
        "live_evidence_rail": {
            "state": "no_live_evidence_yet",
            "evidence_refs": evidence_refs + visible_control["evidence_refs"],
        },
        "dependency_routing": {
            "state": "dependency_routing_only",
            "records": dependencies,
        },
        "operator_stop_takeover": {
            "state": "manual_takeover_not_available_until_live_runner_contract",
            "manual_takeover_available": visible_control["manual_takeover_available"],
        },
    }


def _authority() -> dict[str, Any]:
    return {
        "read_only": True,
        "display_model_only": True,
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        _MODEL_CONTEXT_PROTOCOL_KEY: False,
        _BROWSER_USE_KEY: False,
        "approval_consumed": False,
        "idempotency_marker_reserved": False,
        _AGENT_BUS_WRITE_KEY: False,
        "provider_or_connector_called": False,
        "credential_or_profile_read": False,
        "gate_mutation_performed": False,
        "workflow_or_role_card_mutation_performed": False,
        "canonical_writeback_performed": False,
        "lower_phase_executor_called": False,
        "runtime_dispatch_performed": False,
        "possible_writes": [],
    }


def build_live_operator_shell_browser_panel(
    vault_root: str | Path,
    *,
    target_url: str | None = None,
    runtime: str = "Hermes",
    gate_approval_id: str | None = None,
    requested_by_surface: str = "LiveOperatorShell",
    browser_target_profile: str = TARGET_PROFILE_ID,
    operator_session_scope: str = "throwaway-local-only",
    browser_auth_ref: str | None = None,
    generated_at: str | None = None,
    readiness_model: dict[str, Any] | None = None,
    dispatch_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a read-only/no-action browser operator shell panel packet."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    readiness = (
        readiness_model
        if readiness_model is not None
        else build_studio_browser_runtime_operator_ui_readiness(
            vault,
            generated_at=timestamp,
        )
    )
    manifest = dispatch_manifest
    if manifest is None and target_url is not None and _target_url_valid(target_url):
        manifest = build_chat_studio_browser_runtime_dispatch_lane_manifest(
            vault,
            target_url=target_url,
            runtime=runtime,
            gate_approval_id=gate_approval_id,
            requested_by_surface=requested_by_surface,
            browser_target_profile=browser_target_profile,
            operator_session_scope=operator_session_scope,
            browser_auth_ref=browser_auth_ref,
        )

    current_state = _selected_state(
        target_url=target_url,
        dispatch_manifest=manifest,
        readiness_model=readiness,
    )
    if target_url is not None and not _target_url_valid(target_url):
        hard_denials = ["target_url_missing_or_invalid", *_hard_denials(manifest)]
    else:
        hard_denials = _hard_denials(manifest)
    visible = _visible_control(
        runtime=runtime,
        target_url=target_url,
        browser_target_profile=browser_target_profile,
        gate_approval_id=gate_approval_id,
        dispatch_manifest=manifest,
        current_state=current_state,
    )
    if target_url is not None and not _target_url_valid(target_url):
        visible["denial_reasons"] = hard_denials
    dependencies = _dependency_routing(
        current_state=current_state,
        hard_denials=hard_denials,
        target_url=target_url,
        browser_auth_ref=browser_auth_ref,
        readiness_model=readiness,
    )

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": PANEL_MODEL_VERSION,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "phase": "Phase 10 Live Operator Shell over Phase 9 Browser Runtime / OSRIL / AOR truth",
        "current_state": current_state,
        "available_states": list(AVAILABLE_STATES),
        "visible_control": visible,
        "readiness_model": readiness,
        "dispatch_manifest": manifest,
        "dependency_routing": dependencies,
        "panels": _panels(
            current_state=current_state,
            visible_control=visible,
            readiness_model=readiness,
            dispatch_manifest=manifest,
            dependencies=dependencies,
        ),
        "authority": _authority(),
        "docs": [
            "06_AGENTS/Live-Operator-Shell-Browser-Surface.md",
            "runtime/operator_surface/browser/Browser-Operator-Surface-Folder-Guide.md",
            "06_AGENTS/Studio-Browser-Runtime-Operator-UI-Readiness.md",
            "06_AGENTS/Agent-Control-UX-Contract.md",
        ],
    }
