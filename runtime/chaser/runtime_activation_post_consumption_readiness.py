"""N22 ChaserAgent runtime activation post-consumption readiness.

This read-only surface inspects the N21 activation approval consumption marker
and append-only audit event. It proves whether the marker/audit pair is present
and internally consistent, then stops before runtime/profile/toolset activation
or terminal binding.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.chaser.runtime_activation_approval_consumption_design import (
    build_chaser_runtime_activation_approval_consumption_design,
)
from runtime.chaser.runtime_activation_approval_consumption_write_guard import (
    AUDIT_SCHEMA_VERSION,
    MARKER_SCHEMA_VERSION,
    SURFACE as WRITE_GUARD_SURFACE,
)


SURFACE = "chaser_runtime_activation_post_consumption_readiness"
SCHEMA_VERSION = "chaser_runtime_activation_post_consumption_readiness.v1"
NEXT_PASS = "terminal-n23-chaser-runtime-activation-executor-design"


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
        "activation_audit_write_now": False,
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
        "activate ChaserAgent runtime",
        "activate Chaser profile",
        "activate Chaser toolset",
        "bind terminal tools to ChaserAgent",
        "execute terminal command",
        "expose Studio terminal execution",
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
    marker_rel: str,
) -> dict[str, Any] | None:
    for event in reversed(events):
        if event.get("event_type") != "chaser_runtime_activation_approval_consumption":
            continue
        if event.get("schema_version") != AUDIT_SCHEMA_VERSION:
            continue
        if event.get("surface") != WRITE_GUARD_SURFACE:
            continue
        if event.get("activation_approval_id") != activation_approval_id:
            continue
        if (
            activation_approval_preview_id
            and event.get("activation_approval_preview_id") != activation_approval_preview_id
        ):
            continue
        if event.get("marker_path") != marker_rel:
            continue
        return event
    return None


_EFFECT_KEYS = (
    "runtime_activation_performed",
    "profile_activation_performed",
    "toolset_activation_performed",
    "terminal_binding_performed",
    "terminal_execution_performed",
    "studio_execution_performed",
    "agent_bus_mutation_performed",
    "provider_call_performed",
    "canonical_writeback_performed",
)


def _effect_flags_false(source: dict[str, Any], keys: tuple[str, ...]) -> list[str]:
    return [key for key in keys if source.get(key) is not False]


def build_chaser_runtime_activation_post_consumption_readiness(
    vault_root: str | Path,
    approval_id: str,
    *,
    expected_preview_id: str = "",
    actor: str = "operator",
) -> dict[str, Any]:
    """Inspect existing N21 marker/audit evidence without writing or activating."""

    root = Path(vault_root).resolve()
    requested_id = str(approval_id or "").strip()
    actor_value = actor or "operator"
    design = build_chaser_runtime_activation_approval_consumption_design(
        root,
        requested_id,
        expected_preview_id=expected_preview_id,
        actor=actor_value,
    )
    marker_preview = design.get("consumer_marker_preview")
    if not isinstance(marker_preview, dict):
        marker_preview = {}
    audit_preview = design.get("audit_event_preview")
    if not isinstance(audit_preview, dict):
        audit_preview = {}

    activation_approval_id = str(design.get("activation_approval_id") or requested_id)
    activation_approval_preview_id = design.get("activation_approval_preview_id")
    marker_rel = str(marker_preview.get("path") or "")
    audit_rel = str(audit_preview.get("path") or "")
    blockers: list[str] = []

    if design.get("ok") is not True and design.get("approval_status") != "approved":
        blockers.append("activation_consumption_design_unavailable")
    if design.get("decision_preflight_status") != (
        "activation_approval_decision_preflight_ready_no_mutation"
    ):
        blockers.append(
            str(
                design.get("decision_preflight_status")
                or "activation_approval_decision_preflight_not_ready"
            )
        )
    if design.get("approval_status") != "approved":
        blockers.append("activation_approval_not_approved")

    marker_path, marker_path_error = _scoped_path(root, marker_rel, "marker")
    audit_path, audit_path_error = _scoped_path(root, audit_rel, "audit")
    if marker_path_error:
        blockers.append(marker_path_error)
    if audit_path_error:
        blockers.append(audit_path_error)

    marker_data: dict[str, Any] | None = None
    marker_error: str | None = None
    if marker_path is not None:
        marker_data, marker_error = _load_json(marker_path)
        if marker_error == "missing":
            blockers.append("activation_consumption_marker_missing")
        elif marker_error:
            blockers.append(f"activation_consumption_marker_{marker_error}")

    audit_events: list[dict[str, Any]] = []
    audit_error: str | None = None
    matching_event: dict[str, Any] | None = None
    if audit_path is not None:
        audit_events, audit_error = _load_audit_events(audit_path)
        if audit_error == "missing":
            blockers.append("activation_consumption_audit_missing")
        elif audit_error:
            blockers.append(f"activation_consumption_audit_{audit_error}")
        else:
            matching_event = _matching_audit_event(
                audit_events,
                activation_approval_id=activation_approval_id,
                activation_approval_preview_id=str(activation_approval_preview_id or ""),
                marker_rel=marker_rel,
            )
            if matching_event is None:
                blockers.append("matching_activation_consumption_audit_event_missing")

    marker_checks: list[dict[str, Any]] = []
    if marker_data is not None:
        marker_checks = [
            {
                "name": "marker_schema_version",
                "ok": marker_data.get("schema_version") == MARKER_SCHEMA_VERSION,
            },
            {
                "name": "marker_status_consumed_activation_blocked",
                "ok": marker_data.get("status")
                == "consumed_marker_written_activation_still_blocked",
            },
            {
                "name": "marker_activation_approval_id_matches",
                "ok": marker_data.get("activation_approval_id") == activation_approval_id,
            },
            {
                "name": "marker_activation_approval_preview_id_matches",
                "ok": (
                    not activation_approval_preview_id
                    or marker_data.get("activation_approval_preview_id")
                    == activation_approval_preview_id
                ),
            },
            {
                "name": "marker_effects_false",
                "ok": not _effect_flags_false(marker_data, _EFFECT_KEYS),
            },
        ]
        for check in marker_checks:
            if check["ok"] is not True:
                blockers.append(f"marker_check_failed:{check['name']}")

    audit_checks: list[dict[str, Any]] = []
    if matching_event is not None:
        audit_checks = [
            {
                "name": "audit_schema_version",
                "ok": matching_event.get("schema_version") == AUDIT_SCHEMA_VERSION,
            },
            {
                "name": "audit_surface_write_guard",
                "ok": matching_event.get("surface") == WRITE_GUARD_SURFACE,
            },
            {
                "name": "audit_marker_path_matches",
                "ok": matching_event.get("marker_path") == marker_rel,
            },
            {
                "name": "audit_effects_false",
                "ok": not _effect_flags_false(matching_event, _EFFECT_KEYS),
            },
        ]
        for check in audit_checks:
            if check["ok"] is not True:
                blockers.append(f"audit_check_failed:{check['name']}")

    ready = not blockers and marker_data is not None and matching_event is not None
    status = (
        "activation_post_consumption_readiness_ready_activation_still_blocked"
        if ready
        else "blocked_activation_post_consumption_readiness"
    )
    return {
        "ok": ready,
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "vault_root": str(root),
        "activation_approval_id": activation_approval_id,
        "activation_approval_preview_id": activation_approval_preview_id,
        "approval_path": design.get("approval_path"),
        "approval_status": design.get("approval_status"),
        "profile_id": design.get("profile_id"),
        "toolset_id": design.get("toolset_id"),
        "actor": actor_value,
        "post_consumption_readiness_status": status,
        "blockers": blockers,
        "ready_for_activation_executor_next_pass": ready,
        "activation_post_consumption_readiness_available": True,
        "activation_executor_available": False,
        "activation_allowed": False,
        "activation_performed": False,
        "runtime_activation_now": False,
        "profile_activation_now": False,
        "toolset_activation_now": False,
        "terminal_binding_now": False,
        "writes_performed": False,
        "files_modified": False,
        "approval_status_mutated": False,
        "approval_consumed_now": False,
        "activation_consumption_marker_written_now": False,
        "activation_audit_written_now": False,
        "exact_once_marker": {
            "path": marker_rel,
            "exists": marker_path.exists() if marker_path is not None else False,
            "loaded": marker_data is not None,
            "schema_version": (marker_data or {}).get("schema_version"),
            "status": (marker_data or {}).get("status"),
            "approval_consumed_at": (marker_data or {}).get("approval_consumed_at"),
            "approval_consumed_by": (marker_data or {}).get("approval_consumed_by"),
        },
        "activation_audit": {
            "path": audit_rel,
            "exists": audit_path.exists() if audit_path is not None else False,
            "event_count": len(audit_events),
            "matching_event_found": matching_event is not None,
            "matching_event_type": (matching_event or {}).get("event_type"),
            "matching_event_generated_at": (matching_event or {}).get("generated_at"),
        },
        "marker_checks": marker_checks,
        "audit_checks": audit_checks,
        "design": {
            "surface": design.get("surface"),
            "ok": design.get("ok"),
            "consumption_design_status": design.get("consumption_design_status"),
            "decision_preflight_status": design.get("decision_preflight_status"),
            "approval_status": design.get("approval_status"),
        },
        "blocked_actions": _blocked_actions(),
        "denied_effects": _blocked_actions(),
        "authority": _authority(),
        "terminal_output_trusted": False,
        "trust_tier": "Tier 4",
        "warnings": [
            "post_consumption_readiness_only_no_runtime_activation",
            "no_profile_or_toolset_activation",
            "no_terminal_to_chaser_binding",
            "no_terminal_execution",
            "no_studio_execution",
            "no_agent_bus_write_or_claim",
            "no_provider_call",
            "terminal_output_remains_tier4_untrusted",
        ],
        "next_recommended_pass": NEXT_PASS,
        "boundary": (
            "activation post-consumption readiness only; reads the exact-once "
            "consumption marker and append-only audit event, then stops before "
            "runtime activation, profile/toolset activation, terminal binding, "
            "terminal execution, Agent Bus mutation, provider calls, host "
            "mutation, or canonical writeback."
        ),
    }
