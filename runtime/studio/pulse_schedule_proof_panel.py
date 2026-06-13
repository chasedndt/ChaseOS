"""Read-only Pulse schedule proof panel model for ChaseOS Studio."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.acquisition_cockpit import build_acquisition_cockpit_model


MODEL_VERSION = "studio.pulse_schedule_proof_panel.v1"
SURFACE_ID = "studio_pulse_schedule_proof_panel"
PANEL_ID = "studio.pulse.schedule_proof.panel"
FRONTEND_PANEL_ID = "pulse-schedule-proof"
FRONTEND_TARGET = "panel-pulse-schedule-proof"


_SCHEDULE_CONTROL_PREFIX = "pulse_schedule_"
_PULSE_ENQUEUE_CONTROL_IDS = {"pulse_enqueue_preview", "pulse_enqueue_approved"}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value is None:
        return []
    return [value]


def _control_summary(control: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(control.get("id") or ""),
        "label": str(control.get("label") or ""),
        "command": str(control.get("command") or ""),
        "studio_action": str(control.get("studio_action") or ""),
        "studio_command": str(control.get("studio_command") or ""),
        "write_action": bool(control.get("write_action")),
        "requires_confirmation": bool(control.get("requires_confirmation")),
        "enabled": bool(control.get("enabled")),
        "confirmation_flag": control.get("confirmation_flag"),
        "writes_only": _as_list(control.get("writes_only")),
        "required_evidence_ref_flags": _as_list(
            control.get("required_evidence_ref_flags") or control.get("required_evidence_flags")
        ),
        "reason_if_disabled": control.get("reason_if_disabled"),
        "shell_action_available": False,
        "shell_action_reason": "Native shell panel displays proof metadata only.",
    }


def _display_controls(controls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    display: list[dict[str, Any]] = []
    for control in controls:
        control_id = str(control.get("id") or "")
        if control_id in _PULSE_ENQUEUE_CONTROL_IDS:
            continue
        if not control_id.startswith(_SCHEDULE_CONTROL_PREFIX):
            continue
        display.append(_control_summary(control))
    return display


def _status_value(source: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = source.get(key)
        if value:
            return str(value)
    return "unknown"


def _proof_lane(
    lane_id: str,
    label: str,
    source: dict[str, Any],
    controls_by_id: dict[str, dict[str, Any]],
    *,
    command_control_id: str,
    write_control_id: str | None = None,
    status_keys: tuple[str, ...] = ("status",),
) -> dict[str, Any]:
    command_control = controls_by_id.get(command_control_id, {})
    write_control = controls_by_id.get(write_control_id or "", {})
    return {
        "id": lane_id,
        "label": label,
        "surface": source.get("surface"),
        "available": bool(source.get("available")),
        "status": _status_value(source, *status_keys),
        "schedule_count": _as_int(source.get("schedule_count")),
        "ready_schedule_count": _as_int(source.get("ready_schedule_count")),
        "enabled_schedule_count": _as_int(source.get("enabled_schedule_count")),
        "missing_evidence_count": _as_int(source.get("missing_evidence_count")),
        "missing_evidence_slots": _as_list(source.get("missing_evidence_slots")),
        "command_control_id": command_control_id,
        "command": command_control.get("command"),
        "studio_command": command_control.get("studio_command"),
        "write_action_id": write_control_id,
        "write_action_displayed": bool(write_control),
        "write_root": source.get("write_root"),
        "write_shell_action_available": False,
        "live_execution_allowed": False,
        "schedule_activation_allowed": False,
        "schedule_daemon_started": False,
        "real_run_queue_written": bool(source.get("real_run_queue_written")),
        "real_audit_event_written": bool(source.get("real_audit_event_written")),
        "workflow_execution_allowed": False,
        "canonical_writeback_allowed": False,
        "error": source.get("error"),
        "next_recommended_pass": source.get("next_recommended_pass"),
    }


def _blocked_panel(
    vault: Path,
    profile: str,
    error: str,
) -> dict[str, Any]:
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "title": "Pulse Schedule Proofs",
        "phase": "Phase 10A0 - Studio Pulse schedule proof shell integration",
        "status": "BLOCKED / READ-ONLY NATIVE SHELL PANEL",
        "vault_root": str(vault),
        "profile": profile,
        "native_panel": {
            "mounted": True,
            "panel_id": FRONTEND_PANEL_ID,
            "frontend_target": FRONTEND_TARGET,
            "route_hint": "#pulse-schedule-proof",
            "read_only": True,
            "status": "mounted-read-only",
        },
        "summary": {
            "schedule_count": 0,
            "ready_schedule_count": 0,
            "missing_evidence_count": 0,
            "proof_lane_count": 0,
            "displayed_control_count": 0,
            "write_control_count": 0,
            "execution_action_exposed": False,
            "activation_allowed": False,
        },
        "proof_lanes": [],
        "display_controls": [],
        "source_cockpit": {},
        "readiness": {
            "pulse_schedule_proof_panel_ready": False,
            "native_shell_mount_ready": True,
            "schedule_runner_status_available": False,
            "activation_gate_status_available": False,
            "run_queue_audit_proof_status_available": False,
            "supervised_activation_execution_status_available": False,
            "interactive_execution_controls_ready": False,
            "warnings": ["pulse_schedule_proof_panel_source_unavailable"],
            "blockers": [error],
            "next_recommended_pass": "phase10s-pivot-log",
        },
        "authority": _authority(),
        "possible_writes": [],
        "allowed_actions": ["inspect-pulse-schedule-proof-panel"],
        "docs": _docs(),
    }


def _authority() -> dict[str, Any]:
    return {
        "read_only": True,
        "local_only": True,
        "runs_cli_commands": False,
        "writes_vault": False,
        "writes_proof_artifacts_from_shell": False,
        "activates_schedules": False,
        "exposes_execute_activation": False,
        "patches_manifests": False,
        "starts_daemon": False,
        "writes_real_run_queue": False,
        "writes_real_audit_events": False,
        "writes_agent_bus_tasks": False,
        "dispatches_runtimes": False,
        "executes_workflows": False,
        "provider_calls_allowed": False,
        "connector_calls_allowed": False,
        "canonical_mutation_allowed": False,
    }


def _docs() -> list[str]:
    return [
        "ROADMAP.md#10a0---studio-acquisition-intake-cockpit",
        "06_AGENTS/ChaseOS-Pulse-UI-and-Runtime-Handoff.md",
        "06_AGENTS/ChaseOS-Studio-Phase10-Implementation-Tracker.md",
    ]


def build_pulse_schedule_proof_panel(
    vault_root: str | Path,
    *,
    profile: str = "strikezone",
) -> dict[str, Any]:
    """Build the read-only Studio shell Pulse schedule proof panel model."""

    vault = Path(vault_root).resolve()
    try:
        cockpit = build_acquisition_cockpit_model(vault, profile=profile)
    except Exception as exc:  # noqa: BLE001 - shell panel must degrade without writes.
        return _blocked_panel(vault, profile, str(exc))

    controls_model = cockpit.get("pulse_roadmap_controls") or {}
    raw_controls = controls_model.get("controls") or []
    display_controls = _display_controls(raw_controls)
    controls_by_id = {control["id"]: control for control in display_controls}
    schedule = controls_model.get("live_schedule_runner") or {}
    activation = controls_model.get("schedule_activation_gate") or {}
    run_queue = controls_model.get("schedule_run_queue_audit_proof") or {}
    supervised_execution = controls_model.get("schedule_supervised_activation_execution") or {}

    proof_lanes = [
        _proof_lane(
            "runner",
            "Runner proof status",
            schedule,
            controls_by_id,
            command_control_id="pulse_schedule_runner_status",
            status_keys=("status", "live_runner_status"),
        ),
        _proof_lane(
            "activation_gate",
            "Activation gate proof",
            activation,
            controls_by_id,
            command_control_id="pulse_schedule_activation_gate",
            write_control_id="pulse_schedule_activation_request",
            status_keys=("gate_status", "status"),
        ),
        _proof_lane(
            "run_queue_audit_proof",
            "Run-queue/audit proof",
            run_queue,
            controls_by_id,
            command_control_id="pulse_schedule_run_queue_audit_proof",
            write_control_id="pulse_schedule_run_queue_audit_write_proof",
            status_keys=("proof_status", "gate_status", "status"),
        ),
        _proof_lane(
            "supervised_activation_execution",
            "Supervised activation execution proof",
            supervised_execution,
            controls_by_id,
            command_control_id="pulse_schedule_supervised_activation_execution_proof",
            write_control_id="pulse_schedule_supervised_activation_execution_write_proof",
            status_keys=("execution_status", "gate_status", "run_queue_proof_status", "status"),
        ),
    ]

    warnings: list[str] = []
    if not display_controls:
        warnings.append("pulse_schedule_controls_missing")
    for lane in proof_lanes:
        if not lane["available"]:
            warnings.append(f"{lane['id']}_unavailable")

    schedule_count = max((_as_int(lane.get("schedule_count")) for lane in proof_lanes), default=0)
    ready_schedule_count = max((_as_int(lane.get("ready_schedule_count")) for lane in proof_lanes), default=0)
    missing_evidence_count = sum(_as_int(lane.get("missing_evidence_count")) for lane in proof_lanes)
    write_control_count = sum(1 for control in display_controls if control.get("write_action"))

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "title": "Pulse Schedule Proofs",
        "phase": "Phase 10A0 - Studio Pulse schedule proof shell integration",
        "status": "PARTIAL / READ-ONLY NATIVE SHELL PANEL",
        "vault_root": str(vault),
        "profile": profile,
        "native_panel": {
            "mounted": True,
            "panel_id": FRONTEND_PANEL_ID,
            "frontend_target": FRONTEND_TARGET,
            "route_hint": "#pulse-schedule-proof",
            "read_only": True,
            "status": "mounted-read-only",
        },
        "summary": {
            "schedule_count": schedule_count,
            "ready_schedule_count": ready_schedule_count,
            "missing_evidence_count": missing_evidence_count,
            "proof_lane_count": len(proof_lanes),
            "displayed_control_count": len(display_controls),
            "write_control_count": write_control_count,
            "execution_action_exposed": False,
            "activation_allowed": False,
        },
        "proof_lanes": proof_lanes,
        "display_controls": display_controls,
        "source_cockpit": {
            "surface": controls_model.get("surface"),
            "status": controls_model.get("status"),
            "roadmap_item": controls_model.get("roadmap_item"),
        },
        "readiness": {
            "pulse_schedule_proof_panel_ready": True,
            "native_shell_mount_ready": True,
            "schedule_runner_status_available": bool(schedule.get("available")),
            "activation_gate_status_available": bool(activation.get("available")),
            "run_queue_audit_proof_status_available": bool(run_queue.get("available")),
            "supervised_activation_execution_status_available": bool(supervised_execution.get("available")),
            "interactive_execution_controls_ready": False,
            "warnings": warnings,
            "blockers": [],
            "next_recommended_pass": "phase10s-pivot-log",
        },
        "authority": _authority(),
        "possible_writes": [],
        "allowed_actions": ["inspect-pulse-schedule-proof-panel"],
        "docs": _docs(),
    }
