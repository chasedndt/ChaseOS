"""Approval-gated Runtime Cockpit action-readiness model.

This module turns the existing read-only Runtime Cockpit into an actionable
readiness surface without granting execution authority. Requests only create
Studio approval packets. They do not start runtimes, write Agent Bus tasks,
consume approvals, call providers/connectors, or mutate host startup state.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.runtime_cockpit import build_runtime_cockpit_contract
from runtime.studio.service import ActionSpec, StudioService


MODEL_VERSION = "studio.runtime_cockpit_action_readiness.v1"
SURFACE_ID = "studio_runtime_cockpit_action_readiness"
PASS_ID = "phase10ac-runtime-cockpit-action-readiness"
STATUS = "COMPLETE / APPROVAL-GATED / VERIFIED"
NEXT_RECOMMENDED_PASS = "phase10f1-open-folder-compatibility-readiness"
REQUEST_ROOT = "07_LOGS/Agent-Activity/_studio_runtime_action_requests"


class RuntimeCockpitActionReadinessError(ValueError):
    """Raised when a requested runtime action is not requestable."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_slug(value: str) -> str:
    normalized = "".join(ch.lower() if ch.isalnum() else "-" for ch in str(value or ""))
    normalized = "-".join(part for part in normalized.split("-") if part)
    return normalized[:80] or "runtime-action"


def _request_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _authority_boundary() -> dict[str, Any]:
    return {
        "write_mode": "approval_gated",
        "direct_runtime_execution_allowed": False,
        "runtime_start_allowed": False,
        "runtime_stop_allowed": False,
        "runtime_restart_allowed": False,
        "startup_host_mutation_allowed": False,
        "approval_packet_request_allowed": True,
        "approval_execution_allowed": False,
        "provider_calls_allowed": False,
        "connector_calls_allowed": False,
        "agent_bus_task_writes_allowed": False,
        "workflow_execution_allowed": False,
        "gate_mutation_allowed": False,
        "host_mutation_allowed": False,
        "canonical_mutation_allowed": False,
        "shows_secrets": False,
        "writes_on_request": ["runtime/studio/approvals/<approval-id>.json"],
        "writes_after_approval": [f"{REQUEST_ROOT}/<request-id>.json"],
        "approval_does_not_execute_runtime_action": True,
    }


def _base_action(
    *,
    action_id: str,
    runtime_id: str,
    label: str,
    category: str,
    status: str,
    approval_required: bool,
    approval_packet_requestable: bool,
    entrypoint_command: str | None,
    preview_command: str | None,
    future_execute_command: str | None,
    blockers: list[str] | None = None,
    evidence_needed: list[str] | None = None,
    surface_id: str | None = None,
    current_state: str | None = None,
    target_state: str | None = None,
    approval_status: str | None = None,
) -> dict[str, Any]:
    return {
        "action_id": action_id,
        "runtime_id": runtime_id,
        "surface_id": surface_id,
        "label": label,
        "category": category,
        "status": status,
        "current_state": current_state,
        "target_state": target_state,
        "approval_required": approval_required,
        "approval_packet_requestable": approval_packet_requestable,
        "approval_status": approval_status or ("required" if approval_required else "not-required"),
        "entrypoint_command": entrypoint_command,
        "preview_command": preview_command,
        "future_execute_command": future_execute_command,
        "blockers": blockers or [],
        "evidence_needed": evidence_needed or [],
        "authority_boundary": {
            "request_writes_approval_packet_only": bool(approval_packet_requestable),
            "executes_runtime_action": False,
            "writes_host_startup": False,
            "writes_agent_bus_task": False,
            "calls_provider": False,
            "calls_connector": False,
            "mutates_canonical_state": False,
        },
    }


def _startup_actions(panel: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    runtime_startup = panel.get("runtime_startup") or {}
    for card in runtime_startup.get("cards") or []:
        runtime_id = str(card.get("runtime_id") or "").strip().lower()
        if not runtime_id:
            continue
        surface_id = str(card.get("surface_id") or "").strip()
        commands = card.get("commands") or {}
        approval = card.get("approval_readiness") or {}
        approval_summary = card.get("approval_summary") or {}
        for intent in ("enable", "disable"):
            intent_commands = commands.get(intent) if isinstance(commands.get(intent), dict) else {}
            preview_command = (intent_commands or {}).get("studio_preview") or commands.get(f"{intent}_dry_run")
            toggle_command = (intent_commands or {}).get("studio_toggle") or commands.get(f"{intent}_toggle")
            readiness = approval.get(intent) if isinstance(approval.get(intent), dict) else {}
            artifact = readiness.get("approval_artifact") if isinstance(readiness.get("approval_artifact"), dict) else {}
            can_request = bool(card.get("studio_control_enabled"))
            blockers = []
            if not can_request:
                blockers.append("startup-surface-not-studio-manageable")
            blockers.extend(
                [
                    "host-mutation-executor-disabled",
                    "approval-consumption-not-mounted-in-studio",
                    "runtime-action-execution-deferred",
                ]
            )
            actions.append(
                _base_action(
                    action_id=f"startup:{runtime_id}:{surface_id}:{intent}",
                    runtime_id=runtime_id,
                    surface_id=surface_id,
                    label=f"{intent.title()} {card.get('runtime_name') or runtime_id} / {card.get('ui_label') or surface_id}",
                    category="startup-surface",
                    status="requestable" if can_request else "blocked",
                    approval_required=True,
                    approval_packet_requestable=can_request,
                    entrypoint_command=f"StudioAPI.request_runtime_cockpit_action('startup:{runtime_id}:{surface_id}:{intent}')",
                    preview_command=preview_command,
                    future_execute_command=toggle_command,
                    blockers=blockers,
                    evidence_needed=[
                        "operator approval packet",
                        "matching plan digest",
                        "executor-readiness proof",
                        "host-boundary policy proof",
                        "rollback/audit evidence",
                    ],
                    current_state=card.get("current_state"),
                    target_state=(card.get("target_states") or {}).get(intent),
                    approval_status=artifact.get("status") if artifact else approval_summary.get(f"{intent}_artifact_status") or "missing",
                )
            )
    return actions


def _lifecycle_actions(panel: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    runtime_health = panel.get("runtime_health") or {}
    profiles = runtime_health.get("profiles") or []
    for profile in profiles:
        runtime_id = str(profile.get("runtime_id") or "").strip().lower()
        if not runtime_id:
            continue
        for intent in ("start", "stop", "restart"):
            actions.append(
                _base_action(
                    action_id=f"lifecycle:{runtime_id}:{intent}",
                    runtime_id=runtime_id,
                    label=f"{intent.title()} {runtime_id}",
                    category="runtime-lifecycle",
                    status="blocked",
                    approval_required=True,
                    approval_packet_requestable=False,
                    entrypoint_command=None,
                    preview_command=f"chaseos runtime lifecycle {intent} --runtime {runtime_id} --dry-run --json",
                    future_execute_command=f"chaseos runtime lifecycle {intent} --runtime {runtime_id} --confirm --json",
                    blockers=[
                        "runtime-lifecycle-executor-not-mounted-in-studio",
                        "approval-consumption-chain-not-built-for-lifecycle-action",
                        "runtime-process-control-deferred",
                    ],
                    evidence_needed=[
                        "lifecycle executor readiness proof",
                        "approval consumption dry-run",
                        "exact-once execution marker",
                        "rollback/recovery proof",
                    ],
                )
            )
    return actions


def _cross_runtime_actions(panel: dict[str, Any]) -> list[dict[str, Any]]:
    runtime_ids = {
        str(card.get("runtime_id") or "").strip().lower()
        for card in ((panel.get("runtime_startup") or {}).get("cards") or [])
        if str(card.get("runtime_id") or "").strip()
    }
    runtime_ids.update(
        str(profile.get("runtime_id") or "").strip().lower()
        for profile in ((panel.get("runtime_health") or {}).get("profiles") or [])
        if str(profile.get("runtime_id") or "").strip()
    )
    actions: list[dict[str, Any]] = []
    for runtime_id in sorted(runtime_ids):
        actions.append(
            _base_action(
                action_id=f"readiness:{runtime_id}:agent-bus-review",
                runtime_id=runtime_id,
                label=f"Review {runtime_id} Agent Bus readiness",
                category="agent-bus-readiness",
                status="blocked",
                approval_required=True,
                approval_packet_requestable=False,
                entrypoint_command=None,
                preview_command=f"chaseos agent-bus readiness --runtime {runtime_id} --json",
                future_execute_command=None,
                blockers=[
                    "agent-bus-task-write-not-mounted-from-runtime-cockpit",
                    "runtime-dispatch-remains-separate-governed-lane",
                ],
                evidence_needed=["bus readiness report", "operator-scoped handoff packet"],
            )
        )
        actions.append(
            _base_action(
                action_id=f"readiness:{runtime_id}:provider-config-review",
                runtime_id=runtime_id,
                label=f"Review {runtime_id} provider/config readiness",
                category="provider-config-readiness",
                status="blocked",
                approval_required=True,
                approval_packet_requestable=False,
                entrypoint_command=None,
                preview_command=f"chaseos runtime provider completion-status --runtime {runtime_id} --json",
                future_execute_command=None,
                blockers=[
                    "provider-config-apply-not-mounted-from-runtime-cockpit",
                    "secret-values-not-readable-from-studio",
                    "provider-calls-forbidden",
                ],
                evidence_needed=["non-secret config validation", "approval packet", "provider apply dry-run"],
            )
        )
    return actions


def build_runtime_cockpit_action_readiness(
    vault_root: str | Path,
    *,
    runtime_id: str | None = None,
    probe_child_apps: bool = False,
) -> dict[str, Any]:
    """Build the 10AC Runtime Cockpit action-readiness matrix."""

    vault = Path(vault_root).resolve()
    panel = build_runtime_cockpit_contract(vault, runtime_id=runtime_id, probe_child_apps=probe_child_apps)
    actions = _startup_actions(panel) + _lifecycle_actions(panel) + _cross_runtime_actions(panel)
    if runtime_id and str(runtime_id).strip().lower() not in {"all", "*"}:
        wanted = str(runtime_id).strip().lower()
        actions = [item for item in actions if item.get("runtime_id") == wanted]

    requestable = [item for item in actions if item.get("approval_packet_requestable")]
    blocked = [item for item in actions if item.get("status") == "blocked"]
    by_category: dict[str, int] = {}
    for action in actions:
        category = str(action.get("category") or "unknown")
        by_category[category] = by_category.get(category, 0) + 1

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "title": "Studio Runtime Cockpit Action Readiness",
        "status": STATUS,
        "pass": PASS_ID,
        "generated_at_utc": _utc_now_iso(),
        "vault_root": str(vault),
        "runtime_filter": runtime_id or "all",
        "write_mode": "approval_gated",
        "summary": {
            "action_count": len(actions),
            "requestable_action_count": len(requestable),
            "blocked_action_count": len(blocked),
            "category_counts": by_category,
            "approval_packets_can_be_requested": bool(requestable),
            "runtime_execution_allowed": False,
            "host_mutation_allowed": False,
            "agent_bus_task_writes_allowed": False,
            "provider_calls_allowed": False,
        },
        "action_readiness": actions,
        "requestable_actions": requestable,
        "authority_boundary": _authority_boundary(),
        "readiness": {
            "runtime_cockpit_action_readiness_ready": True,
            "runtime_cockpit_contract_consumed": panel.get("ok") is True,
            "approval_packet_request_surface_ready": True,
            "blocked_actions_are_explicit": all(bool(item.get("blockers")) for item in blocked),
            "no_direct_runtime_execution": True,
            "no_host_mutation": True,
            "no_agent_bus_task_write": True,
            "no_provider_or_connector_calls": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "source_panel_summary": panel.get("summary") or {},
        "warnings": list(panel.get("warnings") or []),
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }


def _find_action(model: dict[str, Any], action_id: str) -> dict[str, Any]:
    wanted = str(action_id or "").strip()
    for action in model.get("action_readiness") or []:
        if action.get("action_id") == wanted:
            return action
    raise RuntimeCockpitActionReadinessError(f"Unknown runtime cockpit action_id: {action_id!r}")


def queue_runtime_cockpit_action_request(
    vault_root: str | Path,
    *,
    action_id: str,
    note: str = "",
    requested_by: str = "studio",
) -> dict[str, Any]:
    """Queue a Studio approval packet for a requestable runtime-cockpit action."""

    vault = Path(vault_root).resolve()
    model = build_runtime_cockpit_action_readiness(vault)
    action = _find_action(model, action_id)
    if not action.get("approval_packet_requestable"):
        raise RuntimeCockpitActionReadinessError(
            f"Runtime cockpit action is not requestable from Studio: {action_id}"
        )

    packet = {
        "type": "studio-runtime-action-request",
        "phase": PASS_ID,
        "created_at_utc": _utc_now_iso(),
        "requested_by": requested_by or "studio",
        "operator_note": note or "",
        "action": action,
        "boundary": _authority_boundary(),
        "execution_posture": {
            "approval_packet_only": True,
            "runtime_action_executed": False,
            "host_mutation_attempted": False,
            "agent_bus_task_written": False,
            "provider_or_connector_called": False,
        },
    }
    digest = _request_digest(packet)
    request_id = f"runtime-action-{_safe_slug(action_id)}-{digest[:12]}-{uuid.uuid4().hex[:8]}"
    target_path = f"{REQUEST_ROOT}/{request_id}.json"
    packet["request_id"] = request_id
    packet["request_digest_sha256"] = digest
    packet["target_path"] = target_path

    spec = ActionSpec(
        action_type="create_file",
        target_path=target_path,
        content=json.dumps(packet, indent=2, sort_keys=True),
        metadata={
            "phase": PASS_ID,
            "runtime_id": action.get("runtime_id"),
            "surface_id": action.get("surface_id"),
            "runtime_action_id": action.get("action_id"),
            "runtime_action_category": action.get("category"),
            "approval_packet_only": True,
            "executes_runtime_action": False,
            "writes_host_startup": False,
            "writes_agent_bus_task": False,
        },
        submitted_by=requested_by or "studio",
        note=note or "Runtime Cockpit action request; approval packet only.",
    )

    svc = StudioService(vault)
    validation = svc.validate_action(spec)
    if validation.gate_blocked:
        raise RuntimeCockpitActionReadinessError("; ".join(validation.errors))
    req = svc.queue_for_approval(spec)

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "status": "requires_approval",
        "requires_approval": True,
        "approval_id": req.approval_id,
        "target_path": target_path,
        "request_id": request_id,
        "request_digest_sha256": digest,
        "action": action,
        "boundary": _authority_boundary(),
    }
