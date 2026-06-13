"""N28 ChaserAgent profile/toolset activation readiness.

This read-only surface validates the N27 profile/toolset activation marker,
profile state record, toolset state record, and append-only audit event. It
proves the record set is present and internally consistent, then stops before
terminal binding, executable profile/toolset activation, or live runtime
authority.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.chaser.runtime_profile_toolset_activation_design import (
    build_chaser_runtime_profile_toolset_activation_design,
)
from runtime.chaser.runtime_profile_toolset_activation_write_guard import (
    AUDIT_SCHEMA_VERSION,
    MARKER_SCHEMA_VERSION,
    PROFILE_STATE_SCHEMA_VERSION,
    SURFACE as WRITE_GUARD_SURFACE,
    TOOLSET_STATE_SCHEMA_VERSION,
)


SURFACE = "chaser_runtime_profile_toolset_activation_readiness"
SCHEMA_VERSION = "chaser_runtime_profile_toolset_activation_readiness.v1"
NEXT_PASS = "terminal-n29-studio-full-terminal-product-contract"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _authority() -> dict[str, bool]:
    return {
        "runtime_activation_now": False,
        "profile_activation_now": False,
        "toolset_activation_now": False,
        "terminal_toolset_binding_now": False,
        "studio_execution_now": False,
        "terminal_execution_now": False,
        "approval_queue_write_now": False,
        "approval_decision_write_now": False,
        "approval_consumption_now": False,
        "exact_once_marker_write_now": False,
        "profile_activation_state_write_now": False,
        "toolset_activation_state_write_now": False,
        "profile_toolset_activation_audit_write_now": False,
        "agent_bus_write_now": False,
        "agent_bus_claim_now": False,
        "provider_call_now": False,
        "canonical_writeback_now": False,
        "external_network_now": False,
        "host_mutation_now": False,
    }


def _blocked_actions() -> list[str]:
    return [
        "mutate approval request status",
        "consume approvals",
        "activate live ChaserAgent runtime",
        "activate Chaser profile as executable authority",
        "activate Chaser toolset as executable authority",
        "bind terminal tools to ChaserAgent",
        "execute terminal command",
        "expose Studio terminal execution",
        "write profile/toolset activation marker or state",
        "write or claim Agent Bus tasks",
        "call provider or model APIs",
        "write canonical ChaseOS memory/state",
        "mutate host startup/autostart/service state",
    ]


def _scoped_path(root: Path, rel_path: str, label: str) -> tuple[Path | None, str | None]:
    if not rel_path:
        return None, f"{label}_path_missing"
    path = (root / rel_path).resolve(strict=False)
    try:
        path.relative_to(root)
    except ValueError:
        return None, f"{label}_path_escapes_vault"
    return path, None


def _load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, "missing"
    except json.JSONDecodeError:
        return None, "invalid_json"
    if not isinstance(data, dict):
        return None, "invalid_json_object"
    return data, None


def _load_audit_events(path: Path) -> tuple[list[dict[str, Any]], str | None]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return [], "missing"
    events: list[dict[str, Any]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            return [], "invalid_jsonl"
        if isinstance(event, dict):
            events.append(event)
    return events, None


def _matching_audit_event(
    events: list[dict[str, Any]],
    *,
    activation_approval_id: str,
    activation_approval_preview_id: str | None,
    profile_id: str,
    toolset_id: str,
    marker_rel: str,
    profile_state_rel: str,
    toolset_state_rel: str,
) -> dict[str, Any] | None:
    for event in reversed(events):
        if event.get("event_type") != "chaser_profile_toolset_activation_write_guard":
            continue
        if event.get("schema_version") != AUDIT_SCHEMA_VERSION:
            continue
        if event.get("surface") != WRITE_GUARD_SURFACE:
            continue
        if event.get("activation_approval_id") != activation_approval_id:
            continue
        if (
            activation_approval_preview_id
            and event.get("activation_approval_preview_id")
            != activation_approval_preview_id
        ):
            continue
        if event.get("profile_id") != profile_id:
            continue
        if event.get("toolset_id") != toolset_id:
            continue
        if event.get("marker_path") != marker_rel:
            continue
        if event.get("profile_state_path") != profile_state_rel:
            continue
        if event.get("toolset_state_path") != toolset_state_rel:
            continue
        return event
    return None


_EFFECT_KEYS = (
    "live_runtime_activated",
    "runtime_activation_performed",
    "profile_activation_performed",
    "toolset_activation_performed",
    "terminal_binding_performed",
    "terminal_execution_performed",
    "studio_execution_performed",
    "agent_bus_mutation_performed",
    "provider_call_performed",
    "canonical_writeback_performed",
    "external_network_performed",
    "host_mutation_performed",
    "terminal_output_trusted",
)


def _effect_flags_false(source: dict[str, Any]) -> list[str]:
    return [key for key in _EFFECT_KEYS if source.get(key) is not False]


def _check(name: str, ok: bool, detail: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "ok": bool(ok),
        "status": "passed" if ok else "blocked",
        "detail": detail,
    }


def _artifact(design: dict[str, Any], key: str) -> dict[str, Any]:
    artifacts = design.get("future_profile_toolset_activation_artifacts")
    if not isinstance(artifacts, dict):
        return {}
    value = artifacts.get(key)
    return value if isinstance(value, dict) else {}


def build_chaser_runtime_profile_toolset_activation_readiness(
    vault_root: str | Path,
    approval_id: str,
    *,
    expected_preview_id: str = "",
    expected_profile_id: str = "",
    expected_toolset_id: str = "",
    actor: str = "operator",
) -> dict[str, Any]:
    """Inspect existing N27 marker/state/audit evidence without writing."""

    root = Path(vault_root).resolve()
    requested_id = str(approval_id or "").strip()
    actor_value = actor or "operator"
    design = build_chaser_runtime_profile_toolset_activation_design(
        root,
        requested_id,
        expected_preview_id=expected_preview_id,
        expected_profile_id=expected_profile_id,
        expected_toolset_id=expected_toolset_id,
        actor=actor_value,
    )
    marker_preview = _artifact(design, "profile_toolset_activation_marker")
    profile_state_preview = _artifact(design, "profile_activation_state")
    toolset_state_preview = _artifact(design, "toolset_activation_state")
    audit_preview = _artifact(design, "profile_toolset_activation_audit")

    activation_approval_id = str(design.get("activation_approval_id") or requested_id)
    activation_approval_preview_id = design.get("activation_approval_preview_id")
    profile_id = str(design.get("profile_id") or "")
    toolset_id = str(design.get("toolset_id") or "")
    marker_rel = str(marker_preview.get("path") or "")
    profile_state_rel = str(profile_state_preview.get("path") or "")
    toolset_state_rel = str(toolset_state_preview.get("path") or "")
    audit_rel = str(audit_preview.get("path") or "")
    blockers: list[str] = []

    if design.get("ok") is not True:
        blockers.append("profile_toolset_activation_design_not_ready")
        blockers.extend(str(item) for item in design.get("blockers") or [])
    if design.get("ready_for_profile_toolset_activation_write_guard_next_pass") is not True:
        blockers.append(
            str(
                design.get("profile_toolset_activation_design_status")
                or "blocked_profile_toolset_activation_design"
            )
        )
    if design.get("approval_status") != "approved":
        blockers.append("activation_approval_not_approved")

    marker_path, marker_path_error = _scoped_path(root, marker_rel, "marker")
    profile_state_path, profile_state_path_error = _scoped_path(
        root, profile_state_rel, "profile_state"
    )
    toolset_state_path, toolset_state_path_error = _scoped_path(
        root, toolset_state_rel, "toolset_state"
    )
    audit_path, audit_path_error = _scoped_path(root, audit_rel, "audit")
    if marker_path_error:
        blockers.append(marker_path_error)
    if profile_state_path_error:
        blockers.append(profile_state_path_error)
    if toolset_state_path_error:
        blockers.append(toolset_state_path_error)
    if audit_path_error:
        blockers.append(audit_path_error)

    marker_data: dict[str, Any] | None = None
    marker_error: str | None = None
    if marker_path is not None:
        marker_data, marker_error = _load_json(marker_path)
        if marker_error == "missing":
            blockers.append("profile_toolset_activation_marker_missing")
        elif marker_error:
            blockers.append(f"profile_toolset_activation_marker_{marker_error}")

    profile_state_data: dict[str, Any] | None = None
    profile_state_error: str | None = None
    if profile_state_path is not None:
        profile_state_data, profile_state_error = _load_json(profile_state_path)
        if profile_state_error == "missing":
            blockers.append("profile_activation_state_missing")
        elif profile_state_error:
            blockers.append(f"profile_activation_state_{profile_state_error}")

    toolset_state_data: dict[str, Any] | None = None
    toolset_state_error: str | None = None
    if toolset_state_path is not None:
        toolset_state_data, toolset_state_error = _load_json(toolset_state_path)
        if toolset_state_error == "missing":
            blockers.append("toolset_activation_state_missing")
        elif toolset_state_error:
            blockers.append(f"toolset_activation_state_{toolset_state_error}")

    audit_events: list[dict[str, Any]] = []
    audit_error: str | None = None
    matching_event: dict[str, Any] | None = None
    if audit_path is not None:
        audit_events, audit_error = _load_audit_events(audit_path)
        if audit_error == "missing":
            blockers.append("profile_toolset_activation_audit_missing")
        elif audit_error:
            blockers.append(f"profile_toolset_activation_audit_{audit_error}")
        else:
            matching_event = _matching_audit_event(
                audit_events,
                activation_approval_id=activation_approval_id,
                activation_approval_preview_id=str(
                    activation_approval_preview_id or ""
                ),
                profile_id=profile_id,
                toolset_id=toolset_id,
                marker_rel=marker_rel,
                profile_state_rel=profile_state_rel,
                toolset_state_rel=toolset_state_rel,
            )
            if matching_event is None:
                blockers.append("matching_profile_toolset_activation_audit_event_missing")

    marker_checks: list[dict[str, Any]] = []
    if marker_data is not None:
        marker_checks = [
            _check("marker_schema_version", marker_data.get("schema_version") == MARKER_SCHEMA_VERSION),
            _check("marker_record_type", marker_data.get("record_type") == "chaser_profile_toolset_activation_marker"),
            _check("marker_status", marker_data.get("status") == "profile_toolset_activation_marker_written_live_runtime_still_blocked"),
            _check("marker_approval_id_matches", marker_data.get("activation_approval_id") == activation_approval_id),
            _check(
                "marker_preview_id_matches",
                not activation_approval_preview_id
                or marker_data.get("activation_approval_preview_id")
                == activation_approval_preview_id,
            ),
            _check("marker_profile_id_matches", marker_data.get("profile_id") == profile_id),
            _check("marker_toolset_id_matches", marker_data.get("toolset_id") == toolset_id),
            _check("marker_profile_state_path_matches", marker_data.get("profile_activation_state_path") == profile_state_rel),
            _check("marker_toolset_state_path_matches", marker_data.get("toolset_activation_state_path") == toolset_state_rel),
            _check("marker_audit_path_matches", marker_data.get("profile_toolset_activation_audit_path") == audit_rel),
            _check("marker_write_guard_surface", marker_data.get("write_guard_surface") == WRITE_GUARD_SURFACE),
            _check("marker_effects_false", not _effect_flags_false(marker_data)),
        ]
        for check in marker_checks:
            if check["ok"] is not True:
                blockers.append(f"marker_check_failed:{check['name']}")

    profile_state_checks: list[dict[str, Any]] = []
    if profile_state_data is not None:
        profile_state_checks = [
            _check("profile_state_schema_version", profile_state_data.get("schema_version") == PROFILE_STATE_SCHEMA_VERSION),
            _check("profile_state_record_type", profile_state_data.get("record_type") == "chaser_profile_activation_state"),
            _check("profile_state_status", profile_state_data.get("status") == "profile_activation_state_written_executable_activation_still_blocked"),
            _check("profile_state_approval_id_matches", profile_state_data.get("activation_approval_id") == activation_approval_id),
            _check("profile_state_profile_id_matches", profile_state_data.get("profile_id") == profile_id),
            _check("profile_state_toolset_id_matches", profile_state_data.get("toolset_id") == toolset_id),
            _check("profile_state_marker_path_matches", profile_state_data.get("profile_toolset_activation_marker_path") == marker_rel),
            _check("profile_state_toolset_path_matches", profile_state_data.get("toolset_activation_state_path") == toolset_state_rel),
            _check("profile_state_audit_path_matches", profile_state_data.get("profile_toolset_activation_audit_path") == audit_rel),
            _check("profile_state_write_guard_surface", profile_state_data.get("write_guard_surface") == WRITE_GUARD_SURFACE),
            _check("profile_state_effects_false", not _effect_flags_false(profile_state_data)),
        ]
        for check in profile_state_checks:
            if check["ok"] is not True:
                blockers.append(f"profile_state_check_failed:{check['name']}")

    toolset_state_checks: list[dict[str, Any]] = []
    if toolset_state_data is not None:
        toolset_state_checks = [
            _check("toolset_state_schema_version", toolset_state_data.get("schema_version") == TOOLSET_STATE_SCHEMA_VERSION),
            _check("toolset_state_record_type", toolset_state_data.get("record_type") == "chaser_toolset_activation_state"),
            _check("toolset_state_status", toolset_state_data.get("status") == "toolset_activation_state_written_executable_activation_still_blocked"),
            _check("toolset_state_approval_id_matches", toolset_state_data.get("activation_approval_id") == activation_approval_id),
            _check("toolset_state_profile_id_matches", toolset_state_data.get("profile_id") == profile_id),
            _check("toolset_state_toolset_id_matches", toolset_state_data.get("toolset_id") == toolset_id),
            _check("toolset_state_marker_path_matches", toolset_state_data.get("profile_toolset_activation_marker_path") == marker_rel),
            _check("toolset_state_profile_path_matches", toolset_state_data.get("profile_activation_state_path") == profile_state_rel),
            _check("toolset_state_audit_path_matches", toolset_state_data.get("profile_toolset_activation_audit_path") == audit_rel),
            _check("toolset_state_write_guard_surface", toolset_state_data.get("write_guard_surface") == WRITE_GUARD_SURFACE),
            _check("toolset_state_effects_false", not _effect_flags_false(toolset_state_data)),
        ]
        for check in toolset_state_checks:
            if check["ok"] is not True:
                blockers.append(f"toolset_state_check_failed:{check['name']}")

    audit_checks: list[dict[str, Any]] = []
    if matching_event is not None:
        audit_checks = [
            _check("audit_schema_version", matching_event.get("schema_version") == AUDIT_SCHEMA_VERSION),
            _check("audit_surface_write_guard", matching_event.get("surface") == WRITE_GUARD_SURFACE),
            _check("audit_marker_path_matches", matching_event.get("marker_path") == marker_rel),
            _check("audit_profile_state_path_matches", matching_event.get("profile_state_path") == profile_state_rel),
            _check("audit_toolset_state_path_matches", matching_event.get("toolset_state_path") == toolset_state_rel),
            _check("audit_effects_false", not _effect_flags_false(matching_event)),
        ]
        for check in audit_checks:
            if check["ok"] is not True:
                blockers.append(f"audit_check_failed:{check['name']}")

    ready = (
        not blockers
        and marker_data is not None
        and profile_state_data is not None
        and toolset_state_data is not None
        and matching_event is not None
    )
    status = (
        "profile_toolset_activation_readiness_ready_terminal_binding_still_blocked"
        if ready
        else "blocked_profile_toolset_activation_readiness"
    )
    return {
        "ok": ready,
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "vault_root": str(root),
        "activation_approval_id": activation_approval_id,
        "activation_approval_preview_id": activation_approval_preview_id,
        "approval_status": design.get("approval_status"),
        "profile_id": profile_id,
        "toolset_id": toolset_id,
        "actor": actor_value,
        "profile_toolset_activation_readiness_status": status,
        "blockers": blockers,
        "ready_for_terminal_toolset_binding_design_next_pass": ready,
        "profile_toolset_activation_readiness_available": True,
        "terminal_toolset_binding_design_available": False,
        "terminal_toolset_binding_design_required": True,
        "activation_allowed": False,
        "activation_performed": False,
        "live_runtime_activated": False,
        "runtime_activation_now": False,
        "profile_activation_now": False,
        "toolset_activation_now": False,
        "terminal_binding_now": False,
        "terminal_binding_performed": False,
        "terminal_execution_performed": False,
        "writes_performed": False,
        "files_modified": False,
        "approval_status_mutated": False,
        "approval_consumed_now": False,
        "profile_toolset_activation_marker_written_now": False,
        "profile_activation_state_written_now": False,
        "toolset_activation_state_written_now": False,
        "profile_toolset_activation_audit_written_now": False,
        "profile_toolset_activation_marker": {
            "path": marker_rel,
            "exists": marker_path.exists() if marker_path is not None else False,
            "loaded": marker_data is not None,
            "schema_version": (marker_data or {}).get("schema_version"),
            "status": (marker_data or {}).get("status"),
            "activation_recorded_at": (marker_data or {}).get("activation_recorded_at"),
            "activation_recorded_by": (marker_data or {}).get("activation_recorded_by"),
        },
        "profile_activation_state": {
            "path": profile_state_rel,
            "exists": profile_state_path.exists() if profile_state_path is not None else False,
            "loaded": profile_state_data is not None,
            "schema_version": (profile_state_data or {}).get("schema_version"),
            "status": (profile_state_data or {}).get("status"),
            "activation_recorded_at": (profile_state_data or {}).get("activation_recorded_at"),
            "activation_recorded_by": (profile_state_data or {}).get("activation_recorded_by"),
        },
        "toolset_activation_state": {
            "path": toolset_state_rel,
            "exists": toolset_state_path.exists() if toolset_state_path is not None else False,
            "loaded": toolset_state_data is not None,
            "schema_version": (toolset_state_data or {}).get("schema_version"),
            "status": (toolset_state_data or {}).get("status"),
            "activation_recorded_at": (toolset_state_data or {}).get("activation_recorded_at"),
            "activation_recorded_by": (toolset_state_data or {}).get("activation_recorded_by"),
        },
        "profile_toolset_activation_audit": {
            "path": audit_rel,
            "exists": audit_path.exists() if audit_path is not None else False,
            "event_count": len(audit_events),
            "matching_event_found": matching_event is not None,
            "matching_event_type": (matching_event or {}).get("event_type"),
            "matching_event_generated_at": (matching_event or {}).get("generated_at"),
        },
        "marker_checks": marker_checks,
        "profile_state_checks": profile_state_checks,
        "toolset_state_checks": toolset_state_checks,
        "audit_checks": audit_checks,
        "design": {
            "surface": design.get("surface"),
            "ok": design.get("ok"),
            "profile_toolset_activation_design_status": design.get(
                "profile_toolset_activation_design_status"
            ),
            "approval_status": design.get("approval_status"),
        },
        "blocked_actions": _blocked_actions(),
        "denied_effects": _blocked_actions(),
        "authority": _authority(),
        "terminal_output_trusted": False,
        "trust_tier": "Tier 4",
        "warnings": [
            "profile_toolset_activation_readiness_read_only_no_activation",
            "no_live_chaser_runtime_activation",
            "no_profile_or_toolset_executable_activation",
            "no_terminal_to_chaser_binding",
            "no_terminal_execution",
            "no_studio_execution",
            "no_agent_bus_write_or_claim",
            "no_provider_call",
            "terminal_output_remains_tier4_untrusted",
        ],
        "next_recommended_pass": NEXT_PASS,
        "boundary": (
            "profile/toolset activation readiness only; reads and validates the "
            "N27 marker, profile state, toolset state, and append-only audit "
            "event. It performs no live runtime activation, executable "
            "profile/toolset activation, terminal binding, terminal execution, "
            "Agent Bus mutation, provider call, host mutation, or canonical "
            "writeback."
        ),
    }
