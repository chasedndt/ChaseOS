"""Final closeout verifier for the 10A0 Pulse Acquisition Cockpit scope.

The closeout is intentionally scoped. It verifies the Pulse-facing 10A0 cockpit
controls, evidence gates, proof/live-runner lanes, and authority boundaries. It
does not claim broader Studio desktop work, real workflow execution, or schedule
daemon activation is complete.
"""

from __future__ import annotations

import importlib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.card_schema import now_utc


SCOPE_STATUS_CLOSED = "closed_for_10a0_pulse_cockpit_scope"
SCOPE_STATUS_BLOCKED = "blocked_for_10a0_pulse_cockpit_scope"

REQUIRED_MODULES = {
    "agent_bus_enqueue_pipeline": "runtime.pulse.pipeline_runner",
    "native_schedule_activation_gate": "runtime.pulse.native_schedule_activation_gate",
    "native_schedule_live_runner": "runtime.pulse.native_schedule_live_runner",
    "native_schedule_runtime_dispatch_proof": "runtime.pulse.native_schedule_runtime_dispatch_proof",
    "native_schedule_run_queue_audit_proof": "runtime.pulse.native_schedule_run_queue_audit_proof",
    "native_schedule_supervised_activation_execution": (
        "runtime.pulse.native_schedule_supervised_activation_execution"
    ),
    "studio_acquisition_cockpit": "runtime.studio.acquisition_cockpit",
}

REQUIRED_CONTROL_IDS = (
    "pulse_schedule_runner_status",
    "pulse_schedule_live_runner_preview",
    "pulse_schedule_live_runner_execute",
    "pulse_schedule_runtime_dispatch_proof",
    "pulse_schedule_runtime_dispatch_write_proof",
    "pulse_schedule_activation_gate",
    "pulse_schedule_activation_request",
    "pulse_schedule_run_queue_audit_proof",
    "pulse_schedule_run_queue_audit_write_proof",
    "pulse_schedule_supervised_activation_execution_proof",
    "pulse_schedule_supervised_activation_execution_write_proof",
    "pulse_enqueue_preview",
    "pulse_enqueue_approved",
)

READ_ONLY_CONTROL_IDS = (
    "pulse_schedule_runner_status",
    "pulse_schedule_live_runner_preview",
    "pulse_schedule_runtime_dispatch_proof",
    "pulse_schedule_activation_gate",
    "pulse_schedule_run_queue_audit_proof",
    "pulse_schedule_supervised_activation_execution_proof",
    "pulse_enqueue_preview",
)

CONFIRMED_WRITE_CONTROL_IDS = (
    "pulse_schedule_live_runner_execute",
    "pulse_schedule_runtime_dispatch_write_proof",
    "pulse_schedule_activation_request",
    "pulse_schedule_run_queue_audit_write_proof",
    "pulse_schedule_supervised_activation_execution_write_proof",
    "pulse_enqueue_approved",
)

EXPECTED_WRITE_ROOTS = {
    "pulse_schedule_live_runner_execute": (
        "07_LOGS/Pulse-Decks/native-schedule-run-queue/",
        "07_LOGS/Pulse-Decks/native-schedule-audit/",
        "07_LOGS/Pulse-Decks/native-schedule-runs/",
    ),
    "pulse_schedule_runtime_dispatch_write_proof": (
        "07_LOGS/Pulse-Decks/native-schedule-runtime-dispatch-proof/",
    ),
    "pulse_schedule_activation_request": (
        "07_LOGS/Pulse-Decks/native-schedule-activation-requests/",
    ),
    "pulse_schedule_run_queue_audit_write_proof": (
        "07_LOGS/Pulse-Decks/native-schedule-run-queue-audit-proof/",
    ),
    "pulse_schedule_supervised_activation_execution_write_proof": (
        "07_LOGS/Pulse-Decks/native-schedule-activation-executions/",
    ),
    "pulse_enqueue_approved": (
        "07_LOGS/Pulse-Decks/agent-bus-approval-requests/",
        "07_LOGS/Pulse-Decks/agent-bus-enqueue-results/",
        "runtime/agent_bus/",
    ),
}

REQUIRED_ENQUEUE_EVIDENCE_FLAGS = (
    "--operator-approved",
    "--gate-policy-defined",
    "--external-sender-allowance-present",
    "--duplicate-work-fingerprint-reviewed",
)

REQUIRED_SCHEDULE_EVIDENCE_FLAGS = (
    "--operator-approval-ref",
    "--permission-envelope-ref",
    "--run-queue-scope-ref",
    "--audit-identity-ref",
    "--runtime-adapter-scope-ref",
    "--rollback-plan-ref",
    "--external-scheduler-denial-ref",
    "--canonical-writeback-denial-ref",
)

REQUIRED_TRUE_AUTHORITY_FLAGS = (
    "local_only",
    "operator_approval_required_for_live_enqueue",
    "agent_bus_task_write_allowed_only_for_approved_action",
    "activation_request_write_allowed_only_for_confirmed_action",
    "run_queue_write_allowed_only_for_confirmed_live_runner",
    "real_audit_event_write_allowed_only_for_confirmed_live_runner",
    "runtime_dispatch_proof_built",
    "runtime_dispatch_proof_write_allowed_only_for_confirmed_action",
    "run_queue_audit_proof_write_allowed_only_for_confirmed_action",
    "activation_execution_proof_write_allowed_only_for_confirmed_action",
)

FORBIDDEN_TRUE_AUTHORITY_FLAGS = (
    "schedule_activation_allowed",
    "schedule_manifest_write_allowed",
    "schedule_daemon_start_allowed",
    "schedule_activation_execution_allowed",
    "supervised_activation_execute_action_exposed",
    "candidate_apply_allowed",
    "review_response_ingest_allowed",
    "canonical_writeback_allowed",
    "provider_or_connector_call_allowed",
)

FORBIDDEN_TRUE_MODEL_AUTHORITY_FLAGS = (
    "canonical_mutation_allowed",
    "delivery_changed",
    "cron_or_scheduler_changed",
    "live_provider_calls_allowed",
)

NON_10A0_SCOPE_REMAINING = (
    "Full broad Studio desktop/card UI beyond the mounted local panels.",
    "Governed feedback review/apply UI and candidate apply effects beyond persisted decision records.",
    "Real schedule daemon start, runtime dispatch execution, and workflow execution.",
    "Real-file acquisition cleanup called out in Phase 10A0 operator-correction notes.",
    "R&D workbook or canonical Pulse memory writeback.",
)


@dataclass(frozen=True)
class PulseTenA0CockpitCloseout:
    generated_at: str
    surface: str
    roadmap_item: str
    vault_root: str
    scope_status: str
    closed: bool
    no_further_10a0_pulse_cockpit_pass_required: bool
    model_error: str | None
    module_checks: dict[str, dict[str, Any]] = field(default_factory=dict)
    missing_modules: list[str] = field(default_factory=list)
    controls_present: list[str] = field(default_factory=list)
    missing_controls: list[str] = field(default_factory=list)
    invalid_read_only_controls: list[dict[str, Any]] = field(default_factory=list)
    invalid_confirmed_write_controls: list[dict[str, Any]] = field(default_factory=list)
    invalid_execution_controls: list[dict[str, Any]] = field(default_factory=list)
    missing_required_authority_claims: list[str] = field(default_factory=list)
    unexpected_true_forbidden_authority_flags: list[str] = field(default_factory=list)
    unexpected_true_model_authority_flags: list[str] = field(default_factory=list)
    unexpected_model_writes: list[str] = field(default_factory=list)
    implementation_evidence: dict[str, Any] = field(default_factory=dict)
    out_of_scope_remaining: list[str] = field(default_factory=list)
    closeout_failures: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _module_checks() -> tuple[dict[str, dict[str, Any]], list[str]]:
    checks: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    for label, module_name in REQUIRED_MODULES.items():
        try:
            importlib.import_module(module_name)
            checks[label] = {
                "module": module_name,
                "importable": True,
                "error": None,
            }
        except Exception as exc:  # noqa: BLE001 - closeout should report all failures.
            checks[label] = {
                "module": module_name,
                "importable": False,
                "error": str(exc),
            }
            missing.append(label)
    return checks, sorted(missing)


def _controls_by_id(model: dict[str, Any]) -> dict[str, dict[str, Any]]:
    controls: dict[str, dict[str, Any]] = {}
    for control in model.get("controls") or []:
        control_id = str(control.get("id") or "")
        if control_id:
            controls[control_id] = control
    for control in (model.get("pulse_roadmap_controls") or {}).get("controls") or []:
        control_id = str(control.get("id") or "")
        if control_id:
            controls[control_id] = control
    return controls


def _invalid_read_only_controls(controls: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    invalid: list[dict[str, Any]] = []
    for control_id in READ_ONLY_CONTROL_IDS:
        control = controls.get(control_id)
        if not control:
            continue
        reasons: list[str] = []
        if bool(control.get("write_action")):
            reasons.append("write_action_must_be_false")
        if bool(control.get("requires_confirmation")):
            reasons.append("requires_confirmation_must_be_false")
        if reasons:
            invalid.append({"control_id": control_id, "reasons": reasons})
    return invalid


def _missing_items(actual: list[Any] | tuple[Any, ...], expected: tuple[str, ...]) -> list[str]:
    actual_values = {str(item) for item in actual}
    return [item for item in expected if item not in actual_values]


def _invalid_confirmed_write_controls(controls: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    invalid: list[dict[str, Any]] = []
    for control_id in CONFIRMED_WRITE_CONTROL_IDS:
        control = controls.get(control_id)
        if not control:
            continue
        reasons: list[str] = []
        if not bool(control.get("write_action")):
            reasons.append("write_action_must_be_true")
        if not bool(control.get("requires_confirmation")):
            reasons.append("requires_confirmation_must_be_true")
        if control.get("confirmation_flag") != "--confirm-action":
            reasons.append("confirmation_flag_must_be_--confirm-action")
        missing_roots = _missing_items(control.get("writes_only") or [], EXPECTED_WRITE_ROOTS.get(control_id, ()))
        if missing_roots:
            reasons.append("missing_write_roots:" + ",".join(missing_roots))
        if control_id == "pulse_enqueue_approved":
            missing_flags = _missing_items(
                control.get("required_evidence_flags") or [],
                REQUIRED_ENQUEUE_EVIDENCE_FLAGS,
            )
            if missing_flags:
                reasons.append("missing_enqueue_evidence_flags:" + ",".join(missing_flags))
        if control_id in {
            "pulse_schedule_activation_request",
            "pulse_schedule_run_queue_audit_write_proof",
            "pulse_schedule_supervised_activation_execution_write_proof",
        }:
            missing_flags = _missing_items(
                control.get("required_evidence_ref_flags") or [],
                REQUIRED_SCHEDULE_EVIDENCE_FLAGS,
            )
            if missing_flags:
                reasons.append("missing_schedule_evidence_ref_flags:" + ",".join(missing_flags))
        if reasons:
            invalid.append({"control_id": control_id, "reasons": reasons})
    return invalid


def _invalid_execution_controls(controls: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    invalid: list[dict[str, Any]] = []
    for control_id in ("pulse_schedule_runtime_dispatch_proof", "pulse_schedule_runtime_dispatch_write_proof"):
        control = controls.get(control_id)
        if control and bool(control.get("execute_dispatch_exposed")):
            invalid.append({"control_id": control_id, "reason": "execute_dispatch_exposed_must_be_false"})
    for control_id in (
        "pulse_schedule_supervised_activation_execution_proof",
        "pulse_schedule_supervised_activation_execution_write_proof",
    ):
        control = controls.get(control_id)
        if control and bool(control.get("execute_activation_exposed")):
            invalid.append({"control_id": control_id, "reason": "execute_activation_exposed_must_be_false"})
    return invalid


def _closeout_failures(
    *,
    model_error: str | None,
    missing_modules: list[str],
    missing_controls: list[str],
    invalid_read_only_controls: list[dict[str, Any]],
    invalid_confirmed_write_controls: list[dict[str, Any]],
    invalid_execution_controls: list[dict[str, Any]],
    missing_required_authority_claims: list[str],
    unexpected_true_forbidden_authority_flags: list[str],
    unexpected_true_model_authority_flags: list[str],
    unexpected_model_writes: list[str],
) -> list[str]:
    failures: list[str] = []
    if model_error:
        failures.append("studio_acquisition_cockpit_model_unavailable")
    if missing_modules:
        failures.append("missing_modules:" + ",".join(missing_modules))
    if missing_controls:
        failures.append("missing_controls:" + ",".join(missing_controls))
    if invalid_read_only_controls:
        failures.append("invalid_read_only_controls")
    if invalid_confirmed_write_controls:
        failures.append("invalid_confirmed_write_controls")
    if invalid_execution_controls:
        failures.append("invalid_execution_controls")
    if missing_required_authority_claims:
        failures.append("missing_required_authority_claims:" + ",".join(missing_required_authority_claims))
    if unexpected_true_forbidden_authority_flags:
        failures.append("unexpected_authority:" + ",".join(unexpected_true_forbidden_authority_flags))
    if unexpected_true_model_authority_flags:
        failures.append("unexpected_model_authority:" + ",".join(unexpected_true_model_authority_flags))
    if unexpected_model_writes:
        failures.append("unexpected_model_writes")
    return failures


def build_pulse_ten_a0_cockpit_closeout(
    vault_root: str | Path,
    *,
    profile: str = "strikezone",
) -> PulseTenA0CockpitCloseout:
    """Build the final closeout status for the 10A0 Pulse cockpit scope."""

    vault = _vault_path(vault_root)
    module_checks, missing_modules = _module_checks()
    model: dict[str, Any] = {}
    model_error: str | None = None
    try:
        from runtime.studio.acquisition_cockpit import build_acquisition_cockpit_model

        model = build_acquisition_cockpit_model(vault, profile=profile)
    except Exception as exc:  # noqa: BLE001 - closeout reports, not masks, model failure.
        model_error = str(exc)

    controls = _controls_by_id(model)
    controls_present = sorted(control_id for control_id in REQUIRED_CONTROL_IDS if control_id in controls)
    missing_controls = sorted(set(REQUIRED_CONTROL_IDS) - set(controls_present))
    invalid_read_only_controls = _invalid_read_only_controls(controls)
    invalid_confirmed_write_controls = _invalid_confirmed_write_controls(controls)
    invalid_execution_controls = _invalid_execution_controls(controls)

    pulse = model.get("pulse_roadmap_controls") or {}
    authority = pulse.get("authority") or {}
    missing_required_authority_claims = [
        flag for flag in REQUIRED_TRUE_AUTHORITY_FLAGS if authority.get(flag) is not True
    ]
    unexpected_true_forbidden_authority_flags = [
        flag for flag in FORBIDDEN_TRUE_AUTHORITY_FLAGS if bool(authority.get(flag))
    ]

    model_authority = model.get("authority") or {}
    unexpected_true_model_authority_flags = [
        flag for flag in FORBIDDEN_TRUE_MODEL_AUTHORITY_FLAGS if bool(model_authority.get(flag))
    ]
    unexpected_model_writes = [str(item) for item in model.get("writes") or []]

    implementation_evidence = {
        "cockpit_surface": model.get("surface"),
        "cockpit_writes": list(model.get("writes") or []),
        "pulse_roadmap_status": pulse.get("status"),
        "live_runner_status": (pulse.get("live_schedule_runner") or {}).get("status"),
        "live_runner_built": bool(authority.get("live_schedule_runner_built")),
        "runtime_dispatch_status": (pulse.get("schedule_runtime_dispatch_proof") or {}).get("dispatch_status"),
        "runtime_dispatch_ready_count": int(authority.get("runtime_dispatch_proof_ready_count", 0) or 0),
        "agent_bus_enqueue_available": bool((pulse.get("agent_bus_enqueue") or {}).get("available")),
        "agent_bus_enqueue_preflight_count": int((pulse.get("agent_bus_enqueue") or {}).get("preflight_count", 0) or 0),
        "approved_enqueue_action_id": (pulse.get("agent_bus_enqueue") or {}).get("approved_action_id"),
        "local_only": bool(authority.get("local_only")),
        "authority_expanded": False,
    }

    failures = _closeout_failures(
        model_error=model_error,
        missing_modules=missing_modules,
        missing_controls=missing_controls,
        invalid_read_only_controls=invalid_read_only_controls,
        invalid_confirmed_write_controls=invalid_confirmed_write_controls,
        invalid_execution_controls=invalid_execution_controls,
        missing_required_authority_claims=missing_required_authority_claims,
        unexpected_true_forbidden_authority_flags=unexpected_true_forbidden_authority_flags,
        unexpected_true_model_authority_flags=unexpected_true_model_authority_flags,
        unexpected_model_writes=unexpected_model_writes,
    )
    closed = not failures

    return PulseTenA0CockpitCloseout(
        generated_at=now_utc(),
        surface="pulse_ten_a0_cockpit_closeout",
        roadmap_item="10A0 - Studio Acquisition Intake Cockpit",
        vault_root=str(vault),
        scope_status=SCOPE_STATUS_CLOSED if closed else SCOPE_STATUS_BLOCKED,
        closed=closed,
        no_further_10a0_pulse_cockpit_pass_required=closed,
        model_error=model_error,
        module_checks=module_checks,
        missing_modules=missing_modules,
        controls_present=controls_present,
        missing_controls=missing_controls,
        invalid_read_only_controls=invalid_read_only_controls,
        invalid_confirmed_write_controls=invalid_confirmed_write_controls,
        invalid_execution_controls=invalid_execution_controls,
        missing_required_authority_claims=missing_required_authority_claims,
        unexpected_true_forbidden_authority_flags=unexpected_true_forbidden_authority_flags,
        unexpected_true_model_authority_flags=unexpected_true_model_authority_flags,
        unexpected_model_writes=unexpected_model_writes,
        implementation_evidence=implementation_evidence,
        out_of_scope_remaining=list(NON_10A0_SCOPE_REMAINING),
        closeout_failures=failures,
    )
