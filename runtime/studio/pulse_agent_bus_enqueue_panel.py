"""Read-only Studio panel model for Pulse Agent Bus enqueue readiness.

This surface wraps the existing Pulse review-contract enqueue chain for native
Studio inspection. It deliberately exposes no shell action for live enqueue,
approval grants, Gate mutation, runtime dispatch, candidate apply, or canonical
writeback.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.pulse.bus_enqueue_design import (
    PULSE_BUS_ALLOWED_REVIEW_RECIPIENTS,
    PULSE_BUS_ENQUEUE_REQUIRED_APPROVALS,
    build_agent_bus_enqueue_plan,
)
from runtime.pulse.bus_enqueue_approval_request import (
    load_agent_bus_enqueue_approval_requests,
)
from runtime.pulse.bus_enqueue_evidence import (
    load_agent_bus_enqueue_evidence_records,
)
from runtime.pulse.operator_gate_approval_contract import (
    build_operator_gate_approval_ui_contract,
)


MODEL_VERSION = "studio.pulse_agent_bus_enqueue_panel.v1"
SURFACE_ID = "studio_pulse_agent_bus_enqueue_panel"
PANEL_ID = "pulse-enqueue"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _compact_preflight(preflight: dict[str, Any]) -> dict[str, Any]:
    payload = dict(preflight.get("task_payload_preview") or {})
    return {
        "preflight_id": preflight.get("preflight_id"),
        "contract_id": preflight.get("contract_id"),
        "candidate_id": preflight.get("candidate_id"),
        "candidate_kind": preflight.get("candidate_kind"),
        "recipient": preflight.get("recipient"),
        "intent": preflight.get("intent"),
        "priority": preflight.get("priority"),
        "work_fingerprint": preflight.get("work_fingerprint"),
        "required_approvals": list(preflight.get("required_approvals") or []),
        "task_payload_preview": {
            "sender": payload.get("sender"),
            "recipient": payload.get("recipient"),
            "intent": payload.get("intent"),
            "priority": payload.get("priority"),
            "request": payload.get("request"),
            "expected_output": payload.get("expected_output"),
            "work_fingerprint": payload.get("work_fingerprint"),
            "enqueue_allowed": bool(payload.get("enqueue_allowed")),
            "agent_bus_task_written": bool(payload.get("agent_bus_task_written")),
        },
        "shell_action_available": False,
        "live_enqueue_allowed": False,
        "agent_bus_task_written": False,
    }


def _evidence_by_request(vault: Path) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in load_agent_bus_enqueue_evidence_records(vault):
        payload = record.to_dict()
        grouped.setdefault(record.request_id, []).append(payload)
    for records in grouped.values():
        records.sort(key=lambda item: (str(item.get("created_at") or ""), str(item.get("evidence_id") or "")))
    return grouped


def _request_row(
    vault: Path,
    request: Any,
    evidence_records: list[dict[str, Any]],
) -> dict[str, Any]:
    latest_evidence = evidence_records[-1] if evidence_records else None
    evidence_id = latest_evidence.get("evidence_id") if latest_evidence else None
    row: dict[str, Any] = {
        "request_id": request.request_id,
        "candidate_id": request.candidate_id,
        "candidate_kind": request.candidate_kind,
        "recipient": request.recipient,
        "intent": request.intent,
        "priority": request.priority,
        "requested_at": request.requested_at,
        "work_fingerprint": request.work_fingerprint,
        "status": request.status,
        "evidence_count": len(evidence_records),
        "latest_evidence_id": evidence_id,
        "ready_for_supervised_live_command": False,
        "handoff_status": "unknown",
        "contract_status": "unknown",
        "approval_evidence_slots": [],
        "blocked_reasons": [],
        "supervised_live_command_preview": [],
        "shell_action_available": False,
        "agent_bus_task_written": False,
        "live_enqueue_executed": False,
    }
    try:
        contract = build_operator_gate_approval_ui_contract(
            vault,
            request.request_id,
            evidence_id=evidence_id,
        ).to_dict()
        preflight = dict(contract.get("handoff_preflight") or {})
        row.update(
            {
                "contract_status": contract.get("contract_status"),
                "handoff_status": preflight.get("handoff_status"),
                "ready_for_supervised_live_command": bool(
                    preflight.get("ready_for_supervised_live_command")
                ),
                "approval_evidence_slots": list(contract.get("approval_evidence_slots") or []),
                "blocked_reasons": list(contract.get("blocked_reasons") or []),
                "supervised_live_command_preview": list(
                    contract.get("supervised_live_command_preview") or []
                ),
                "target_posture": dict(preflight.get("target_posture") or {}),
                "duplicate_posture": dict(preflight.get("duplicate_posture") or {}),
                "safety_warnings": list(contract.get("safety_warnings") or []),
            }
        )
    except Exception as exc:  # noqa: BLE001 - panel must degrade read-only.
        row["contract_status"] = "unavailable"
        row["handoff_status"] = "unavailable"
        row["blocked_reasons"] = [str(exc)]
    return row


def build_pulse_agent_bus_enqueue_panel(
    vault_root: str | Path,
    *,
    limit: int = 5,
    recipient: str = "Hermes",
) -> dict[str, Any]:
    """Build a native-shell read-only Pulse Agent Bus enqueue review panel."""

    vault = _vault_path(vault_root)
    warnings: list[str] = []
    preflights: list[dict[str, Any]] = []
    plan_status = "unavailable"
    plan_error: str | None = None
    safe_limit = max(1, min(int(limit or 5), 25))
    safe_recipient = recipient if recipient in PULSE_BUS_ALLOWED_REVIEW_RECIPIENTS else "Hermes"

    try:
        plan = build_agent_bus_enqueue_plan(
            vault,
            default_recipient=safe_recipient,
            limit=safe_limit,
        ).to_dict()
        plan_status = str(plan.get("plan_status") or "read_only")
        preflights = [_compact_preflight(item) for item in plan.get("preflights", [])]
    except Exception as exc:  # noqa: BLE001 - unavailable Pulse queue should not break Studio.
        plan_error = str(exc)
        warnings.append("pulse_enqueue_plan_unavailable")

    requests = load_agent_bus_enqueue_approval_requests(vault)
    requests.sort(key=lambda item: (item.requested_at, item.request_id), reverse=True)
    grouped_evidence = _evidence_by_request(vault)
    request_rows = [
        _request_row(vault, request, grouped_evidence.get(request.request_id, []))
        for request in requests[:safe_limit]
    ]
    ready_rows = [
        row for row in request_rows if row.get("ready_for_supervised_live_command")
    ]
    missing_evidence_rows = [
        row for row in request_rows if row.get("handoff_status") == "blocked_missing_required_evidence"
    ]
    duplicate_rows = [
        row for row in request_rows if row.get("handoff_status") == "blocked_duplicate_active_task"
    ]

    return {
        "ok": plan_error is None,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "native_panel": {
            "mounted": True,
            "panel_id": PANEL_ID,
            "frontend_target": "panel-pulse-enqueue",
            "route_hint": "#pulse-enqueue",
            "read_only": True,
            "status": "mounted-read-only",
        },
        "roadmap_item": "10A0 - Studio Acquisition Intake Cockpit",
        "summary": {
            "plan_status": plan_status,
            "preflight_count": len(preflights),
            "approval_request_count": len(requests),
            "displayed_request_count": len(request_rows),
            "evidence_record_count": sum(len(items) for items in grouped_evidence.values()),
            "ready_for_supervised_live_count": len(ready_rows),
            "missing_evidence_count": len(missing_evidence_rows),
            "active_duplicate_count": len(duplicate_rows),
            "allowed_recipients": list(PULSE_BUS_ALLOWED_REVIEW_RECIPIENTS),
        },
        "preflight_preview": preflights,
        "approval_requests": request_rows,
        "required_approvals": list(PULSE_BUS_ENQUEUE_REQUIRED_APPROVALS),
        "future_cli_commands": {
            "dry_run_preview": f"chaseos pulse run-pipeline --limit {safe_limit} --json",
            "evidence_capture": "chaseos pulse enqueue-evidence <request-id> <evidence flags> --json",
            "handoff_preflight": "chaseos pulse handoff-preflight <request-id> --evidence-id <evidence-id> --json",
            "operator_gate_contract": "chaseos pulse operator-gate-contract <request-id> --evidence-id <evidence-id> --json",
            "supervised_rehearsal": "chaseos pulse supervised-enqueue-rehearsal <request-id> --evidence-id <evidence-id> --json",
            "manual_live_enqueue": "chaseos pulse enqueue-candidate <request-id> --evidence-id <evidence-id> --json",
        },
        "readiness": {
            "pulse_enqueue_panel_ready": plan_error is None,
            "plan_error": plan_error,
            "warnings": warnings,
        },
        "authority": {
            "read_only": True,
            "shell_action_available": False,
            "approval_grant_from_shell": False,
            "approval_request_write_from_shell": False,
            "evidence_write_from_shell": False,
            "live_enqueue_from_shell": False,
            "agent_bus_task_write_from_shell": False,
            "runtime_dispatch_from_shell": False,
            "candidate_apply_allowed": False,
            "review_response_ingest_allowed": False,
            "schedule_activation_allowed": False,
            "provider_or_connector_call_allowed": False,
            "canonical_writeback_allowed": False,
        },
        "allowed_actions": ["inspect-pulse-agent-bus-enqueue-panel"],
        "possible_writes": [],
    }
