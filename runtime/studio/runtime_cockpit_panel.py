"""Read-only native Studio Runtime Cockpit panel model."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.studio.runtime_cockpit import build_runtime_cockpit_contract
from runtime.studio.runtime_cockpit_action_readiness import (
    build_runtime_cockpit_action_readiness,
)


MODEL_VERSION = "studio.runtime_cockpit_panel.v1"
SURFACE_ID = "studio_runtime_cockpit_panel"
NEXT_NATIVE_PASS = "phase10f1-open-folder-compatibility-readiness"


def _authority() -> dict[str, Any]:
    return {
        "read_only": False,
        "write_mode": "approval_gated",
        "writes_vault": False,
        "writes_approval_artifacts": True,
        "writes_host_startup": False,
        "starts_child_apps": False,
        "starts_runtimes": False,
        "stops_runtimes": False,
        "restarts_runtimes": False,
        "executes_runtime_actions": False,
        "executes_workflows": False,
        "writes_agent_bus_tasks": False,
        "approval_execution_allowed": False,
        "provider_calls_allowed": False,
        "connector_calls_allowed": False,
        "canonical_mutation_allowed": False,
        "shows_secrets": False,
        "shows_raw_credentials": False,
        "approval_packet_request_allowed": True,
    }


def _runtime_ids(profiles: list[dict[str, Any]]) -> list[str]:
    ids: list[str] = []
    for profile in profiles:
        runtime_id = str(profile.get("runtime_id") or "").strip()
        if runtime_id:
            ids.append(runtime_id)
    return ids


def _fresh_heartbeat_count(profiles: list[dict[str, Any]]) -> int:
    return sum(
        1
        for profile in profiles
        if ((profile.get("bus_heartbeat") or {}).get("freshness") in {"fresh", "recent"})
    )


def _operating_context(
    *,
    runtime_health: dict[str, Any],
    action_readiness: dict[str, Any],
) -> dict[str, Any]:
    profiles = list(runtime_health.get("profiles") or [])
    runtime_ids = _runtime_ids(profiles)
    live_count = int(runtime_health.get("live_runtime_count") or 0)
    fresh_count = _fresh_heartbeat_count(profiles)
    action_summary = action_readiness.get("summary") or {}
    blocked_actions = int(action_summary.get("blocked_action_count") or 0)
    requestable_actions = int(action_summary.get("requestable_action_count") or 0)
    runtime_label = ", ".join(runtime_ids) if runtime_ids else "No runtime profiles found"

    return {
        "title": "Runtime Operating Context",
        "description": (
            "Local-first runtime control desk for workers, heartbeats, daemon posture, "
            "and approval-gated runtime requests."
        ),
        "safe_action": "Inspect runtime health and request approval packets only.",
        "source": "runtime/lifecycle/*.lifecycle.yaml + Agent Bus heartbeats + Runtime Cockpit contracts",
        "cards": [
            {
                "label": "Runtime profiles",
                "value": len(profiles),
                "note": runtime_label,
                "status": "visible" if profiles else "missing",
            },
            {
                "label": "Live workers",
                "value": live_count,
                "note": "Gateway/process/heartbeat evidence is read-only.",
                "status": "live" if live_count else "idle",
            },
            {
                "label": "Fresh heartbeats",
                "value": fresh_count,
                "note": "Chat dispatch readiness stays stricter than gateway liveness.",
                "status": "fresh" if fresh_count else "heartbeat-required",
            },
            {
                "label": "Capability gates",
                "value": blocked_actions + requestable_actions,
                "note": f"{requestable_actions} requestable approval packet(s), {blocked_actions} blocked action(s).",
                "status": "approval-gated",
            },
        ],
    }


def _feature_family_coverage(
    *,
    runtime_health: dict[str, Any],
    coordination_watch: dict[str, Any],
    action_readiness: dict[str, Any],
) -> list[dict[str, Any]]:
    profiles = list(runtime_health.get("profiles") or [])
    runtime_ids = _runtime_ids(profiles)
    runtime_label = ", ".join(runtime_ids) if runtime_ids else "none"
    fresh_count = _fresh_heartbeat_count(profiles)
    live_count = int(runtime_health.get("live_runtime_count") or 0)
    action_summary = action_readiness.get("summary") or {}
    requestable_actions = int(action_summary.get("requestable_action_count") or 0)
    blocked_actions = int(action_summary.get("blocked_action_count") or 0)

    def row(
        family: str,
        capability: str,
        status: str,
        evidence: str,
        boundary: str,
        surface: str = "Agents / Runtimes",
    ) -> dict[str, Any]:
        return {
            "family": family,
            "capability": capability,
            "product_surface": surface,
            "status": status,
            "evidence": evidence,
            "boundary": boundary,
        }

    return [
        row(
            "Runtime",
            "Runtime profiles and worker posture",
            "VISIBLE / READ-ONLY HEALTH",
            f"{len(profiles)} lifecycle profile(s): {runtime_label}",
            "No direct start, stop, restart, or dispatch from this overview.",
        ),
        row(
            "Runtime",
            "Hermes and OpenClaw live runtime sync",
            "LIVE SIGNAL VISIBLE" if live_count else "CONFIGURED / HEARTBEAT REQUIRED",
            f"{live_count} live runtime(s), {fresh_count} fresh/recent heartbeat(s).",
            "Gateway liveness remains separate from dispatch authority.",
        ),
        row(
            "Runtime",
            "Agent Bus heartbeat and coordination watch",
            "FRESH HEARTBEAT OBSERVED" if fresh_count else "HEARTBEAT REQUIRED",
            f"{coordination_watch.get('artifact_count', 0)} coordination-watch artifact(s).",
            "This page reads bus posture; it does not write, claim, or enqueue tasks.",
        ),
        row(
            "Runtime",
            "Runtime lifecycle and startup controls",
            "APPROVAL-GATED / EXECUTION DEFERRED",
            f"{requestable_actions} requestable approval packet(s), {blocked_actions} blocked runtime action(s).",
            "Approval packets can be requested; approval consumption and host mutation are not executed here.",
        ),
        row(
            "Main",
            "Phase 11 Chat runtime dispatch readiness",
            "REPRESENTED / DISPATCH NOT TRIGGERED",
            "Chat owns message dispatch; runtime cockpit exposes supporting heartbeat and daemon facts.",
            "No provider/model call or chat message dispatch is performed from this page.",
            surface="Chat + Agents / Runtimes",
        ),
        row(
            "Personal Memory",
            "Runtime memory, profiles, and context posture",
            "LINKED / MUTATION BLOCKED",
            "Runtime profile posture is visible; memory details remain on Personal Memory surfaces.",
            "No memory ledger write, Personal Map mutation, or canonical memory promotion occurs here.",
            surface="Personal Memory + Agents / Runtimes",
        ),
        row(
            "Governance",
            "Approvals, audit, and provider configuration boundaries",
            "VISIBLE / GOVERNED",
            "Authority flags and action-readiness blockers are surfaced in product language.",
            "No approval decision, approval consumption, secret read, provider call, or policy mutation is granted.",
            surface="Governance + Agents / Runtimes",
        ),
        row(
            "Runtime",
            "Advanced browser, SiteOps, MCP, and tool surfaces",
            "ADVANCED / GATED",
            "Advanced runtime surfaces stay separate from MVP runtime health.",
            "No browser control, MCP tool execution, external delivery, or host/release mutation is mounted here.",
            surface="Advanced Runtime",
        ),
    ]


def build_runtime_cockpit_panel(
    vault_root: str | Path,
    *,
    runtime_id: str | None = None,
    probe_child_apps: bool = True,
) -> dict[str, Any]:
    """Return the native shell panel wrapper for the Runtime Cockpit contract."""

    contract = build_runtime_cockpit_contract(
        vault_root,
        runtime_id=runtime_id,
        probe_child_apps=probe_child_apps,
    )
    runtime_startup = contract.get("runtime_startup") or {}
    runtime_health = contract.get("runtime_health") or {}
    coordination_watch = contract.get("coordination_watch") or {}
    logs_and_audit = contract.get("logs_and_audit") or {}
    post_reboot = contract.get("post_reboot") or {}
    readiness = contract.get("readiness") or {}
    action_readiness = build_runtime_cockpit_action_readiness(
        vault_root,
        runtime_id=runtime_id,
        probe_child_apps=False,
    )
    operating_context = _operating_context(
        runtime_health=runtime_health,
        action_readiness=action_readiness,
    )
    feature_family_coverage = _feature_family_coverage(
        runtime_health=runtime_health,
        coordination_watch=coordination_watch,
        action_readiness=action_readiness,
    )

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at_utc": contract.get("generated_at_utc"),
        "vault_root": contract.get("vault_root"),
        "native_panel": {
            "mounted": True,
            "panel_id": "runtime-cockpit",
            "frontend_target": "panel-runtime-cockpit",
            "route_hint": "#runtime-cockpit",
            "read_only": False,
            "write_mode": "approval_gated",
            "status": "mounted-approval-gated",
        },
        "summary": {
            "overall_status": contract.get("status"),
            "runtime_count": runtime_startup.get("runtime_count"),
            "surface_count": runtime_startup.get("surface_count"),
            "manageable_surface_count": runtime_startup.get("manageable_surface_count"),
            "runtime_profile_count": runtime_health.get("runtime_profile_count", 0),
            "coordination_watch_artifact_count": coordination_watch.get("artifact_count", 0),
            "log_group_count": logs_and_audit.get("group_count", 0),
            "post_reboot_indicator_count": post_reboot.get("indicator_count", 0),
            "start_stop_restart_available": False,
            "runtime_action_count": (action_readiness.get("summary") or {}).get("action_count", 0),
            "runtime_action_requestable_count": (action_readiness.get("summary") or {}).get("requestable_action_count", 0),
            "runtime_action_blocked_count": (action_readiness.get("summary") or {}).get("blocked_action_count", 0),
        },
        "runtime_startup": runtime_startup,
        "runtime_health": runtime_health,
        "coordination_watch": coordination_watch,
        "startup_drift": contract.get("startup_drift") or {},
        "logs_and_audit": logs_and_audit,
        "post_reboot": post_reboot,
        "available_surfaces": contract.get("available_surfaces") or [],
        "views": contract.get("views") or [],
        "actions": contract.get("actions") or [],
        "action_readiness": action_readiness,
        "operating_context": operating_context,
        "feature_family_coverage": feature_family_coverage,
        "authority": _authority(),
        "allowed_actions": ["inspect-runtime-cockpit-panel", "request-runtime-action-approval"],
        "possible_writes": ["runtime_action_approval_request"],
        "readiness": {
            "runtime_cockpit_panel_mounted": True,
            "runtime_cockpit_action_readiness_ready": True,
            "runtime_cockpit_contract_ready": readiness.get("runtime_cockpit_contract_ready") is True,
            "health_depth_visible": readiness.get("runtime_health_depth_visible") is True,
            "coordination_watch_visible": readiness.get("coordination_watch_visible") is True,
            "startup_drift_visible": readiness.get("startup_drift_visible") is True,
            "logs_visible": readiness.get("logs_and_audit_visible") is True,
            "post_reboot_indicators_visible": readiness.get("post_reboot_indicators_visible") is True,
            "no_start_stop_restart_authority": True,
            "approval_request_only": True,
            "runtime_actions_do_not_execute": True,
            "next_recommended_pass": NEXT_NATIVE_PASS,
        },
        "contract": {
            "surface": contract.get("surface"),
            "status": contract.get("status"),
            "integration_contract": contract.get("integration_contract") or {},
            "boundary": contract.get("boundary") or {},
            "errors": contract.get("errors") or [],
        },
        "warnings": list(contract.get("errors") or []),
    }
