"""Supervised activation gate for ChaseOS Pulse native schedules.

This module builds the review packet required before a future live Pulse
schedule activation. It can optionally write a pending operator-review request
artifact, but it cannot enable schedule manifests, start a daemon, write a run
queue, dispatch runtimes, execute workflows, grant approvals, or mutate
canonical state.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.card_schema import now_utc
from runtime.pulse.native_schedule_runner_proof import (
    BLOCKED_EFFECTS as RUNNER_BLOCKED_EFFECTS,
    DEFAULT_SCHEDULE_IDS,
    PulseNativeScheduleRunnerTarget,
    build_pulse_native_schedule_runner_proof,
)


GATE_STATUS_BLOCKED = "blocked_missing_activation_evidence"
GATE_STATUS_READY = "ready_for_operator_supervised_activation"
GATE_STATUSES = {GATE_STATUS_BLOCKED, GATE_STATUS_READY}

REQUEST_STATUS_PENDING = "pending_operator_review"
REQUEST_STATUSES = {REQUEST_STATUS_PENDING}

ALLOWED_WRITE_ROOT = "07_LOGS/Pulse-Decks/native-schedule-activation-requests/"
NEXT_RECOMMENDED_PASS = "chaseos-pulse-native-schedule-run-queue-audit-proof"

REQUIRED_EVIDENCE_SLOTS = (
    "operator_approval_ref",
    "permission_envelope_ref",
    "run_queue_scope_ref",
    "audit_identity_ref",
    "runtime_adapter_scope_ref",
    "rollback_plan_ref",
    "external_scheduler_denial_ref",
    "canonical_writeback_denial_ref",
)

BLOCKED_EFFECTS = tuple(
    sorted(
        set(RUNNER_BLOCKED_EFFECTS)
        | {
            "approval_grant",
            "approval_request_execution",
            "run_queue_write",
            "schedule_manifest_write",
            "supervised_activation_execution",
        }
    )
)


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _date_slug(generated_at: str) -> str:
    date = generated_at[:10]
    return date if len(date) == 10 else now_utc()[:10]


def _slug(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in value).strip("-")


def _normalize_schedule_ids(schedule_ids: tuple[str, ...] | None) -> tuple[str, ...]:
    ids = tuple(item.strip() for item in (schedule_ids or DEFAULT_SCHEDULE_IDS) if item.strip())
    if not ids:
        raise ValueError("at least one schedule_id is required")
    return ids


def _real_ref(value: str | None) -> bool:
    text = (value or "").strip()
    if not text:
        return False
    lowered = text.lower()
    if any(marker in lowered for marker in ("placeholder", "todo", "tbd", "example", "real-ref")):
        return False
    if "<" in text or ">" in text:
        return False
    return True


@dataclass(frozen=True)
class PulseNativeScheduleActivationEvidenceSlot:
    slot_id: str
    label: str
    ref: str | None
    satisfied: bool
    authority_class: str
    runtime_self_satisfiable: bool = False
    placeholder_ref_rejected: bool = True

    def validate(self) -> None:
        if self.slot_id not in REQUIRED_EVIDENCE_SLOTS:
            raise ValueError("invalid native schedule activation evidence slot")
        if not self.label:
            raise ValueError("evidence slot label is required")
        if not self.authority_class:
            raise ValueError("evidence slot authority class is required")
        if self.satisfied != _real_ref(self.ref):
            raise ValueError("evidence slot satisfaction must reflect real ref status")
        if self.runtime_self_satisfiable:
            raise ValueError("Pulse native schedule activation evidence requires operator/Gate authority")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class PulseNativeScheduleActivationRequest:
    request_id: str
    generated_at: str
    status: str
    schedule_ids: tuple[str, ...]
    requested_capability: str
    required_evidence_slots: tuple[str, ...]
    missing_evidence_slots: tuple[str, ...]
    activation_command_preview: tuple[str, ...]
    approval_granted: bool = False
    execution_allowed: bool = False
    writes_artifact_only: bool = True
    mutates_canonical_state: bool = False

    def validate(self) -> None:
        if not self.request_id:
            raise ValueError("activation request_id is required")
        if self.status not in REQUEST_STATUSES:
            raise ValueError("invalid activation request status")
        if not self.schedule_ids:
            raise ValueError("activation request requires schedule_ids")
        if self.required_evidence_slots != REQUIRED_EVIDENCE_SLOTS:
            raise ValueError("activation request must declare required evidence slots")
        if not self.requested_capability:
            raise ValueError("activation request capability is required")
        if self.approval_granted or self.execution_allowed:
            raise ValueError("activation request cannot grant or execute approval")
        if not self.writes_artifact_only:
            raise ValueError("activation request must be artifact-only")
        if self.mutates_canonical_state:
            raise ValueError("activation request cannot mutate canonical state")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "request_id": self.request_id,
            "generated_at": self.generated_at,
            "status": self.status,
            "schedule_ids": list(self.schedule_ids),
            "requested_capability": self.requested_capability,
            "required_evidence_slots": list(self.required_evidence_slots),
            "missing_evidence_slots": list(self.missing_evidence_slots),
            "activation_command_preview": list(self.activation_command_preview),
            "approval_granted": self.approval_granted,
            "execution_allowed": self.execution_allowed,
            "writes_artifact_only": self.writes_artifact_only,
            "mutates_canonical_state": self.mutates_canonical_state,
        }


@dataclass(frozen=True)
class PulseNativeScheduleActivationGate:
    generated_at: str
    gate_status: str
    schedule_ids: tuple[str, ...]
    schedule_count: int
    ready_schedule_count: int
    enabled_schedule_count: int
    evidence_slots: tuple[PulseNativeScheduleActivationEvidenceSlot, ...]
    missing_evidence_slots: tuple[str, ...]
    activation_targets: tuple[PulseNativeScheduleRunnerTarget, ...]
    activation_command_preview: tuple[str, ...]
    write_requested: bool = False
    write_executed: bool = False
    writes: tuple[str, ...] = ()
    activation_request: PulseNativeScheduleActivationRequest | None = None
    next_recommended_pass: str = NEXT_RECOMMENDED_PASS
    read_only: bool = True
    local_only: bool = True
    writes_artifacts: bool = False
    approval_granted: bool = False
    approval_execution_allowed: bool = False
    schedule_activation_allowed: bool = False
    schedule_manifest_write_allowed: bool = False
    schedule_daemon_started: bool = False
    run_queue_written: bool = False
    agent_bus_task_write_allowed: bool = False
    runtime_dispatch_allowed: bool = False
    workflow_execution_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    external_scheduler_install_allowed: bool = False
    canonical_writeback_allowed: bool = False
    mutates_canonical_state: bool = False
    rd_workbook_update_allowed: bool = False
    allowed_write_root: str = ALLOWED_WRITE_ROOT
    blocked_effects: tuple[str, ...] = BLOCKED_EFFECTS
    notes: tuple[str, ...] = field(
        default_factory=lambda: (
            "This is a supervised activation gate packet, not a schedule activator.",
            "The next pass must still prove run queue/audit behavior before any recurring execution.",
        )
    )

    def validate(self) -> None:
        if self.gate_status not in GATE_STATUSES:
            raise ValueError("invalid native schedule activation gate status")
        if self.schedule_count != len(self.activation_targets):
            raise ValueError("schedule_count must match activation target count")
        if self.ready_schedule_count < 0 or self.enabled_schedule_count < 0:
            raise ValueError("schedule counts cannot be negative")
        if tuple(slot.slot_id for slot in self.evidence_slots) != REQUIRED_EVIDENCE_SLOTS:
            raise ValueError("activation gate must preserve required evidence slot order")
        for slot in self.evidence_slots:
            slot.validate()
        expected_missing = tuple(slot.slot_id for slot in self.evidence_slots if not slot.satisfied)
        if self.missing_evidence_slots != expected_missing:
            raise ValueError("missing evidence slots must match unsatisfied evidence slots")
        expected_status = GATE_STATUS_READY if not self.missing_evidence_slots else GATE_STATUS_BLOCKED
        if self.gate_status != expected_status:
            raise ValueError("activation gate status must reflect missing evidence")
        for target in self.activation_targets:
            target.validate()
        if self.write_executed and not self.write_requested:
            raise ValueError("write_executed requires write_requested")
        if self.write_executed and self.read_only:
            raise ValueError("written activation gate cannot be read_only")
        if self.write_executed and not self.writes_artifacts:
            raise ValueError("written activation gate must report writes_artifacts")
        if self.activation_request is not None:
            self.activation_request.validate()
        if self.approval_granted or self.approval_execution_allowed:
            raise ValueError("activation gate cannot grant or execute approval")
        if self.schedule_activation_allowed or self.schedule_manifest_write_allowed:
            raise ValueError("activation gate cannot activate or write schedule manifests")
        if self.schedule_daemon_started:
            raise ValueError("activation gate cannot start a schedule daemon")
        if self.run_queue_written:
            raise ValueError("activation gate cannot write run queue entries")
        if self.agent_bus_task_write_allowed:
            raise ValueError("activation gate cannot write Agent Bus tasks")
        if self.runtime_dispatch_allowed or self.workflow_execution_allowed:
            raise ValueError("activation gate cannot dispatch runtimes or execute workflows")
        if self.provider_or_connector_call_allowed:
            raise ValueError("activation gate cannot call providers/connectors")
        if self.external_scheduler_install_allowed:
            raise ValueError("activation gate cannot install external schedulers")
        if self.canonical_writeback_allowed or self.mutates_canonical_state:
            raise ValueError("activation gate cannot mutate canonical state")
        if self.rd_workbook_update_allowed:
            raise ValueError("activation gate cannot update the R&D workbook")
        for written in self.writes:
            if not written.replace("\\", "/").startswith(self.allowed_write_root):
                raise ValueError("activation gate writes must stay under native schedule activation requests")
        if set(self.blocked_effects) != set(BLOCKED_EFFECTS):
            raise ValueError("activation gate must declare blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "gate_status": self.gate_status,
            "schedule_ids": list(self.schedule_ids),
            "schedule_count": self.schedule_count,
            "ready_schedule_count": self.ready_schedule_count,
            "enabled_schedule_count": self.enabled_schedule_count,
            "evidence_slots": [slot.to_dict() for slot in self.evidence_slots],
            "missing_evidence_slots": list(self.missing_evidence_slots),
            "activation_targets": [target.to_dict() for target in self.activation_targets],
            "activation_command_preview": list(self.activation_command_preview),
            "write_requested": self.write_requested,
            "write_executed": self.write_executed,
            "writes": list(self.writes),
            "activation_request": self.activation_request.to_dict() if self.activation_request else None,
            "next_recommended_pass": self.next_recommended_pass,
            "read_only": self.read_only,
            "local_only": self.local_only,
            "writes_artifacts": self.writes_artifacts,
            "approval_granted": self.approval_granted,
            "approval_execution_allowed": self.approval_execution_allowed,
            "schedule_activation_allowed": self.schedule_activation_allowed,
            "schedule_manifest_write_allowed": self.schedule_manifest_write_allowed,
            "schedule_daemon_started": self.schedule_daemon_started,
            "run_queue_written": self.run_queue_written,
            "agent_bus_task_write_allowed": self.agent_bus_task_write_allowed,
            "runtime_dispatch_allowed": self.runtime_dispatch_allowed,
            "workflow_execution_allowed": self.workflow_execution_allowed,
            "provider_or_connector_call_allowed": self.provider_or_connector_call_allowed,
            "external_scheduler_install_allowed": self.external_scheduler_install_allowed,
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "mutates_canonical_state": self.mutates_canonical_state,
            "rd_workbook_update_allowed": self.rd_workbook_update_allowed,
            "allowed_write_root": self.allowed_write_root,
            "blocked_effects": list(self.blocked_effects),
            "notes": list(self.notes),
        }


def _evidence_slots(evidence_refs: dict[str, str | None]) -> tuple[PulseNativeScheduleActivationEvidenceSlot, ...]:
    labels = {
        "operator_approval_ref": "Operator approval",
        "permission_envelope_ref": "Schedule activation permission envelope",
        "run_queue_scope_ref": "Run queue write scope",
        "audit_identity_ref": "Schedule audit identity",
        "runtime_adapter_scope_ref": "Runtime adapter execution scope",
        "rollback_plan_ref": "Rollback and disable plan",
        "external_scheduler_denial_ref": "External scheduler ownership denial",
        "canonical_writeback_denial_ref": "Canonical writeback denial",
    }
    return tuple(
        PulseNativeScheduleActivationEvidenceSlot(
            slot_id=slot_id,
            label=labels[slot_id],
            ref=evidence_refs.get(slot_id),
            satisfied=_real_ref(evidence_refs.get(slot_id)),
            authority_class="operator_gate",
        )
        for slot_id in REQUIRED_EVIDENCE_SLOTS
    )


def _activation_command_preview(schedule_ids: tuple[str, ...]) -> tuple[str, ...]:
    schedule_args = " ".join(f"--schedule-id {schedule_id}" for schedule_id in schedule_ids)
    return (
        "Future supervised activation remains unimplemented in this pass.",
        (
            "future: chaseos pulse native-schedule-run-queue-audit-proof "
            f"{schedule_args} --operator-approval-ref <real-ref> --json"
        ),
        "Do not use OpenClaw cron, Windows Task Scheduler, or external runtimes as schedule owners.",
    )


def build_pulse_native_schedule_activation_gate(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    schedule_ids: tuple[str, ...] | None = None,
    evidence_refs: dict[str, str | None] | None = None,
) -> PulseNativeScheduleActivationGate:
    """Build a non-executing supervised activation gate packet."""

    vault = _vault_path(vault_root)
    generated = generated_at or now_utc()
    ids = _normalize_schedule_ids(schedule_ids)
    runner = build_pulse_native_schedule_runner_proof(
        vault,
        generated_at=generated,
        schedule_ids=ids,
        simulate_missed_run=True,
    )
    slots = _evidence_slots(evidence_refs or {})
    missing = tuple(slot.slot_id for slot in slots if not slot.satisfied)
    status = GATE_STATUS_READY if not missing else GATE_STATUS_BLOCKED
    model = PulseNativeScheduleActivationGate(
        generated_at=generated,
        gate_status=status,
        schedule_ids=ids,
        schedule_count=runner.schedule_count,
        ready_schedule_count=runner.ready_schedule_count,
        enabled_schedule_count=runner.enabled_schedule_count,
        evidence_slots=slots,
        missing_evidence_slots=missing,
        activation_targets=runner.schedules,
        activation_command_preview=_activation_command_preview(ids),
    )
    model.validate()
    return model


def write_pulse_native_schedule_activation_request(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    schedule_ids: tuple[str, ...] | None = None,
    evidence_refs: dict[str, str | None] | None = None,
    output_path: str | Path | None = None,
) -> PulseNativeScheduleActivationGate:
    """Write a pending operator-review request for future activation work."""

    vault = _vault_path(vault_root)
    generated = generated_at or now_utc()
    base = build_pulse_native_schedule_activation_gate(
        vault,
        generated_at=generated,
        schedule_ids=schedule_ids,
        evidence_refs=evidence_refs,
    )
    schedule_slug = _slug("-".join(base.schedule_ids))
    request = PulseNativeScheduleActivationRequest(
        request_id=f"pulse_native_schedule_activation_{_date_slug(generated)}_{schedule_slug}",
        generated_at=generated,
        status=REQUEST_STATUS_PENDING,
        schedule_ids=base.schedule_ids,
        requested_capability="pulse_native_schedule_supervised_activation",
        required_evidence_slots=REQUIRED_EVIDENCE_SLOTS,
        missing_evidence_slots=base.missing_evidence_slots,
        activation_command_preview=base.activation_command_preview,
    )
    request.validate()

    if output_path is None:
        target_path = vault / ALLOWED_WRITE_ROOT / f"{_date_slug(generated)}-activation-request-{schedule_slug}.json"
    else:
        target_path = Path(output_path)
        if not target_path.is_absolute():
            target_path = vault / target_path
    target_path = target_path.resolve()
    allowed_root = (vault / ALLOWED_WRITE_ROOT).resolve()
    try:
        target_path.relative_to(allowed_root)
    except ValueError as exc:
        raise ValueError("native schedule activation request must be written under 07_LOGS/Pulse-Decks/native-schedule-activation-requests/") from exc

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(request.to_dict(), indent=2), encoding="utf-8")
    rel_path = target_path.relative_to(vault).as_posix()

    model = PulseNativeScheduleActivationGate(
        generated_at=base.generated_at,
        gate_status=base.gate_status,
        schedule_ids=base.schedule_ids,
        schedule_count=base.schedule_count,
        ready_schedule_count=base.ready_schedule_count,
        enabled_schedule_count=base.enabled_schedule_count,
        evidence_slots=base.evidence_slots,
        missing_evidence_slots=base.missing_evidence_slots,
        activation_targets=base.activation_targets,
        activation_command_preview=base.activation_command_preview,
        write_requested=True,
        write_executed=True,
        writes=(rel_path,),
        activation_request=request,
        read_only=False,
        writes_artifacts=True,
    )
    model.validate()
    return model
