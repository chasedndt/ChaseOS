"""Read-only MVP boundary for browser, host, and full system control.

The MVP may reference browser/system-control futures, but it must not turn them
on while provider and real-client workflow proof are still blocked.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.browser_runtime.cdp_executor_spec import build_cdp_read_only_executor_spec


MODEL_VERSION = "chaseos.mvp_system_control_boundary.v1"
SURFACE_ID = "chaseos_mvp_system_control_boundary"

EVIDENCE_REFS = [
    "06_AGENTS/Permission-Matrix.md",
    "06_AGENTS/Trust-Tiers.md",
    "runtime/browser_runtime/cdp_executor_spec.py",
    "runtime/browser_runtime/workflow_replay_execution_readiness.py",
    "06_AGENTS/ChaseOS-MVP-Operator-Unblock-Packet.md",
]

FORBIDDEN_MVP_CONTROL_CLASSES = [
    "ambient_desktop_control",
    "host_startup_or_autostart_mutation",
    "real_browser_profile_access",
    "browser_history_or_session_read",
    "credential_cookie_or_token_read",
    "external_form_submission",
    "payment_crm_invoice_or_revenue_mutation",
    "trusted_browser_skill_activation",
    "raw_cdp_passthrough",
    "autonomous_workflow_replay",
]


def _path_exists(root: Path, relative: str) -> bool:
    return (root / relative).exists()


def _precondition_map(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = spec.get("preconditions") if isinstance(spec.get("preconditions"), list) else []
    mapped: dict[str, dict[str, Any]] = {}
    for row in rows:
        if isinstance(row, dict) and row.get("precondition_id"):
            mapped[str(row["precondition_id"])] = row
    return mapped


def build_mvp_system_control_boundary(vault_root: str | Path = ".") -> dict[str, Any]:
    """Return the current MVP browser/system-control boundary without side effects."""

    root = Path(vault_root).resolve()
    present = [ref for ref in EVIDENCE_REFS if _path_exists(root, ref)]
    missing = [ref for ref in EVIDENCE_REFS if ref not in present]

    cdp_spec = build_cdp_read_only_executor_spec(
        vault_root=root,
        target_url="http://127.0.0.1:<port>",
        cdp_endpoint="http://127.0.0.1:<port>",
        runtime="Codex",
        gate_approval_id=None,
        source_command="python -m runtime.cli.main mvp readiness-gate --json",
    )
    preconditions = _precondition_map(cdp_spec)
    approval_supplied = preconditions.get("approval_artifact_supplied", {})
    approval_approved = preconditions.get("approval_status_approved", {})

    boundary_ready = len(present) >= 3 and not bool(cdp_spec.get("execution_enabled"))
    status = "parked_and_gated_until_mvp_proven" if boundary_ready else "partial_or_unverified"
    blockers = [] if boundary_ready else ["system_control_boundary_evidence_sparse_or_execution_enabled"]

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "read_only": True,
        "mvp_decision": "exclude_broad_system_control_from_first_usable_mvp",
        "allowed_now": [
            "read_only_boundary_reports",
            "no_execution_executor_specs",
            "separate_operator_approval_request_previews",
        ],
        "future_allowed_scope_after_separate_approval": [
            "local_loopback_read_only_cdp_proof",
            "isolated_throwaway_browser_context",
            "redacted_browser_run_log",
            "operator_visible_agent_activity_log",
            "untrusted_browser_skill_candidate_output",
        ],
        "forbidden_in_mvp": FORBIDDEN_MVP_CONTROL_CLASSES,
        "authority": {
            "read_only": True,
            "broad_system_control_allowed": False,
            "browser_system_automation_allowed_now": False,
            "host_mutation_allowed_now": False,
            "workflow_replay_allowed_now": False,
            "provider_calls_allowed": False,
            "approval_execution_allowed": False,
            "approval_consumption_allowed": False,
            "agent_bus_task_write_allowed": False,
            "credential_value_read_allowed": False,
            "cookie_or_session_read_allowed": False,
            "real_browser_profile_allowed": False,
            "trusted_skill_write_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "cdp_read_only_boundary": {
            "operation": cdp_spec.get("operation"),
            "executor_status": cdp_spec.get("executor_status"),
            "execution_enabled": bool(cdp_spec.get("execution_enabled")),
            "cdp_read_only_proof_allowed": bool(cdp_spec.get("cdp_read_only_proof_allowed")),
            "approval_artifact_supplied": bool(approval_supplied.get("passed")),
            "approval_artifact_status": approval_supplied.get("status"),
            "approval_status_approved": bool(approval_approved.get("passed")),
            "approval_status": approval_approved.get("status"),
            "blocked_reasons": list(cdp_spec.get("blocked_reasons") or []),
            "browser_launch_attempted": bool(cdp_spec.get("browser_launch_attempted")),
            "cdp_connection_attempted": bool(cdp_spec.get("cdp_connection_attempted")),
            "credential_value_read": bool(cdp_spec.get("credential_value_read")),
            "cookie_or_session_read": bool(cdp_spec.get("cookie_or_session_read")),
            "real_profile_used": bool(cdp_spec.get("real_profile_used")),
            "trusted_skill_written": bool(cdp_spec.get("trusted_skill_written")),
            "canonical_files_mutated": bool(cdp_spec.get("canonical_files_mutated")),
            "approval_request_written": bool(cdp_spec.get("approval_request_written")),
            "files_modified": bool(cdp_spec.get("files_modified")),
        },
        "evidence_refs": present,
        "missing_evidence_refs": missing,
        "blockers": blockers,
    }


def format_mvp_system_control_boundary(payload: dict[str, Any]) -> str:
    lines = [
        "ChaseOS MVP Full System Control Boundary",
        f"  status: {payload.get('status')}",
        f"  mvp_decision: {payload.get('mvp_decision')}",
        "  allowed_now:",
    ]
    for item in payload.get("allowed_now") or []:
        lines.append(f"    - {item}")
    lines.append("  forbidden_in_mvp:")
    for item in payload.get("forbidden_in_mvp") or []:
        lines.append(f"    - {item}")
    lines.append(
        "  boundary: no browser launch, no CDP connection, no host mutation, no credential/session/profile read, no approval consumption."
    )
    return "\n".join(lines)
