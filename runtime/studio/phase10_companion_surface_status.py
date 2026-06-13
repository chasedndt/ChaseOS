"""Phase 10 companion-surface read-only status aggregator.

This is the first bounded proof slice for the mobile/tablet/browser companion
surface. It aggregates existing read-only Studio/OSRIL/approval/brief posture
without granting mobile authority, writing approval artifacts, consuming
approvals, dispatching runtimes, calling gateways/providers, mutating
credentials/config, writing Agent Bus tasks, or promoting canonical truth.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.phase11_chat_companion_status import build_phase11_chat_companion_status

MODEL_VERSION = "studio.phase10_companion_surface_status.v1"
SURFACE_ID = "phase10_companion_surface_status_readonly"
PASS_ID = "phase10-companion-surface-status-readonly"
STATUS = "READY / READ-ONLY / LIVE AUTHORITY BLOCKED"

REQUIRED_BLOCKERS = frozenset(
    {
        "mobile_auth_session_boundary_missing",
        "gateway_mobile_delivery_path_missing",
        "approval_response_execution_blocked",
        "capture_trigger_request_path_missing",
        "runtime_dispatch_from_companion_blocked",
        "credential_access_blocked",
        "canonical_writeback_blocked",
    }
)

FORBIDDEN_AUTHORITY = {
    "approval_artifact_write_allowed": False,
    "approval_consumption_allowed": False,
    "target_companion_selection_write_allowed": False,
    "capture_execution_allowed": False,
    "runtime_dispatch_allowed": False,
    "provider_or_gateway_call_allowed": False,
    "credential_or_config_mutation_allowed": False,
    "agent_bus_write_allowed": False,
    "canonical_writeback_allowed": False,
    "mobile_session_mutation_allowed": False,
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return str(path)


def _latest_files(vault: Path, root: Path, patterns: tuple[str, ...], limit: int = 5) -> list[dict[str, Any]]:
    if not root.is_dir():
        return []
    files: list[Path] = []
    for pattern in patterns:
        files.extend(path for path in root.glob(pattern) if path.is_file())
    unique = sorted(set(files), key=lambda item: item.stat().st_mtime, reverse=True)
    return [
        {
            "path": _rel(vault, path),
            "name": path.name,
            "modified_at_epoch": path.stat().st_mtime,
        }
        for path in unique[:limit]
    ]


def _folder_summary(vault: Path, relative_path: str, *, patterns: tuple[str, ...] = ("*.md", "*.json")) -> dict[str, Any]:
    root = vault / relative_path
    latest = _latest_files(vault, root, patterns)
    file_count = 0
    if root.is_dir():
        seen: set[Path] = set()
        for pattern in patterns:
            seen.update(path for path in root.glob(pattern) if path.is_file())
        file_count = len(seen)
    return {
        "path": relative_path,
        "exists": root.is_dir(),
        "file_count": file_count,
        "latest_files": latest,
        "safe_summary_only": True,
    }


def _read_osril_summary(vault: Path) -> dict[str, Any]:
    from runtime.osril.inspector import list_sessions

    sessions = list_sessions(vault, limit=20)
    status_counts: dict[str, int] = {}
    runtime_counts: dict[str, int] = {}
    for item in sessions.get("sessions") or []:
        status = str(item.get("status") or "unknown")
        runtime_id = str(item.get("runtime_id") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        runtime_counts[runtime_id] = runtime_counts.get(runtime_id, 0) + 1
    return {
        "available": True,
        "source": "runtime.osril.inspector.list_sessions",
        "session_count": int(sessions.get("count") or 0),
        "status_counts": status_counts,
        "runtime_counts": runtime_counts,
        "latest_sessions": [
            {
                "session_id": item.get("session_id"),
                "runtime_id": item.get("runtime_id"),
                "workflow_id": item.get("workflow_id"),
                "status": item.get("status"),
                "last_event_at": item.get("last_event_at"),
            }
            for item in (sessions.get("sessions") or [])[:5]
        ],
        "read_only": True,
    }


def _read_approval_summary(vault: Path) -> dict[str, Any]:
    from runtime.studio.approval_center_panel import build_approval_center_panel

    approval_center = build_approval_center_panel(vault)
    summary = approval_center.get("summary") or {}
    groups = approval_center.get("source_groups") or []
    return {
        "available": True,
        "source": "runtime.studio.approval_center_panel.build_approval_center_panel",
        "total_item_count": int(summary.get("total_item_count") or 0),
        "pending_item_count": int(summary.get("pending_item_count") or 0),
        "blocked_item_count": int(summary.get("blocked_item_count") or 0),
        "artifact_count": int(summary.get("artifact_count") or 0),
        "source_groups": [
            {
                "id": group.get("id"),
                "status": group.get("status"),
                "item_count": group.get("item_count"),
                "pending_count": group.get("pending_count"),
                "blocked_count": group.get("blocked_count"),
            }
            for group in groups
        ],
        "read_only": True,
        "approval_execution_available": False,
    }


def build_phase10_companion_surface_status(
    vault_root: str | Path,
    *,
    requested_runtime: str | None = None,
) -> dict[str, Any]:
    """Build the read-only companion-surface status dashboard payload."""

    vault = Path(vault_root).resolve()
    warnings: list[str] = []
    companion_status = build_phase11_chat_companion_status(vault, requested_runtime=requested_runtime)

    try:
        osril = _read_osril_summary(vault)
    except Exception as exc:  # noqa: BLE001 - optional read surface must degrade closed
        osril = {
            "available": False,
            "source": "runtime.osril.inspector.list_sessions",
            "session_count": 0,
            "status_counts": {},
            "runtime_counts": {},
            "latest_sessions": [],
            "read_only": True,
        }
        warnings.append(f"osril_read_api_unavailable:{exc}")

    try:
        approvals = _read_approval_summary(vault)
    except Exception as exc:  # noqa: BLE001 - optional read surface must degrade closed
        approvals = {
            "available": False,
            "source": "runtime.studio.approval_center_panel.build_approval_center_panel",
            "total_item_count": 0,
            "pending_item_count": 0,
            "blocked_item_count": 0,
            "artifact_count": 0,
            "source_groups": [],
            "read_only": True,
            "approval_execution_available": False,
        }
        warnings.append(f"approval_read_api_unavailable:{exc}")

    briefs = {
        "operator_briefs": _folder_summary(vault, "07_LOGS/Operator-Briefs", patterns=("*.md", "*.json")),
        "workflow_outputs": _folder_summary(vault, "07_LOGS/Workflow-Outputs", patterns=("*.md", "*.json")),
        "agent_activity": _folder_summary(vault, "07_LOGS/Agent-Activity", patterns=("*.md", "*.json")),
    }

    companion_blockers = list(companion_status.get("blocked_reasons") or [])
    blocked_live_authority = sorted(set(REQUIRED_BLOCKERS).union(companion_blockers))

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "summary": {
            "selected_runtime_id": (companion_status.get("summary") or {}).get("selected_runtime_id"),
            "registered_companion_count": (companion_status.get("summary") or {}).get("registered_companion_count"),
            "osril_session_count": osril.get("session_count", 0),
            "pending_approval_count": approvals.get("pending_item_count", 0),
            "operator_brief_folder_present": briefs["operator_briefs"]["exists"],
            "workflow_output_folder_present": briefs["workflow_outputs"]["exists"],
            "blocked_live_authority_count": len(blocked_live_authority),
            "companion_personality_grants_authority": False,
            "mobile_tablet_actions_route_through": ["Gate", "AOR", "StudioService"],
        },
        "operator_notice": (
            "Companion personality/status is presentation state only and never grants authority; "
            "mobile/tablet actions must route through Gate/AOR/StudioService."
        ),
        "companion_status": companion_status,
        "osril": osril,
        "approvals": approvals,
        "briefs": briefs,
        "blocked_live_authority": blocked_live_authority,
        "authority": {
            "read_only": True,
            "allowed_actions": ["inspect_phase10_companion_surface_status"],
            "possible_writes": [],
            **FORBIDDEN_AUTHORITY,
        },
        "readiness": {
            "phase10_companion_surface_status_ready": True,
            "companion_status_aggregated": True,
            "osril_status_read_api_used_or_degraded": True,
            "approval_status_read_api_used_or_degraded": True,
            "operator_brief_summary_visible": True,
            "workflow_output_summary_visible": True,
            "companion_personality_authority_neutral": True,
            "mobile_tablet_actions_gate_aor_studioservice_routed": True,
            "live_authority_blocked": True,
            "approval_artifact_write_blocked": True,
            "approval_consumption_blocked": True,
            "target_companion_selection_write_blocked": True,
            "capture_execution_blocked": True,
            "runtime_dispatch_blocked": True,
            "provider_gateway_calls_blocked": True,
            "credential_config_mutation_blocked": True,
            "agent_bus_write_blocked": True,
            "canonical_writeback_blocked": True,
        },
        "warnings": warnings,
    }
