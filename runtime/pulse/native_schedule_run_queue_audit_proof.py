"""Proof-only Pulse native schedule run-queue and audit packet.

This module models the run-queue entry and audit-event shapes required before a
future supervised Pulse schedule activation. It can write a proof artifact under
Pulse logs, but it cannot write the real schedule run queue, enable manifests,
dispatch runtimes, execute workflows, grant approvals, or mutate canonical
state.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.card_schema import now_utc
from runtime.pulse.native_schedule_activation_gate import (
    BLOCKED_EFFECTS as GATE_BLOCKED_EFFECTS,
    GATE_STATUS_READY,
    REQUIRED_EVIDENCE_SLOTS,
    build_pulse_native_schedule_activation_gate,
)
from runtime.pulse.native_schedule_runner_proof import DEFAULT_SCHEDULE_IDS


PROOF_STATUS_BLOCKED = "blocked_activation_gate_not_ready"
PROOF_STATUS_READY = "run_queue_audit_proof_ready"
PROOF_STATUSES = {PROOF_STATUS_BLOCKED, PROOF_STATUS_READY}

QUEUE_STATUS_PROOF_ONLY = "proof_only_not_enqueued"
AUDIT_EVENT_TYPE = "pulse_native_schedule_run_queue_audit_proof"
RUN_REASON_MISSED_RUN_CATCHUP = "missed_run_catch_up"
TRIGGER_SOURCE = "native_chaseos_schedule_intent"

ALLOWED_WRITE_ROOT = "07_LOGS/Pulse-Decks/native-schedule-run-queue-audit-proof/"
NEXT_RECOMMENDED_PASS = "chaseos-pulse-supervised-native-schedule-activation-execution-proof"

BLOCKED_EFFECTS = tuple(
    sorted(
        set(GATE_BLOCKED_EFFECTS)
        | {
            "audit_identity_consumption",
            "real_audit_event_write",
            "real_run_queue_write",
            "schedule_run_execution",
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


@dataclass(frozen=True)
class PulseNativeScheduleRunQueueEntryProof:
    queue_entry_id: str
    schedule_id: str
    workflow_id: str
    audience: str
    output_root: str
    run_reason: str
    queue_status: str
    requested_for: str
    executor_adapter: str
    schedule_owner: str
    approval_ref: str
    permission_envelope_ref: str
    audit_identity_ref: str
    run_queue_scope_ref: str
    idempotency_key: str
    agent_bus_task_write_allowed: bool = False
    runtime_dispatch_allowed: bool = False
    workflow_execution_allowed: bool = False
    canonical_writeback_allowed: bool = False

    def validate(self) -> None:
        if not self.queue_entry_id or not self.schedule_id or not self.workflow_id:
            raise ValueError("run queue proof entry requires ids")
        if self.run_reason != RUN_REASON_MISSED_RUN_CATCHUP:
            raise ValueError("run queue proof entry has invalid run reason")
        if self.queue_status != QUEUE_STATUS_PROOF_ONLY:
            raise ValueError("run queue proof entry must remain proof-only")
        if self.schedule_owner != "chaseos":
            raise ValueError("run queue proof entry requires ChaseOS schedule ownership")
        if not self.approval_ref or not self.permission_envelope_ref:
            raise ValueError("run queue proof entry requires approval and permission refs")
        if not self.audit_identity_ref or not self.run_queue_scope_ref:
            raise ValueError("run queue proof entry requires audit and run-queue refs")
        if (
            self.agent_bus_task_write_allowed
            or self.runtime_dispatch_allowed
            or self.workflow_execution_allowed
            or self.canonical_writeback_allowed
        ):
            raise ValueError("run queue proof entry cannot enable execution authority")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class PulseNativeScheduleAuditEventProof:
    event_id: str
    event_type: str
    schedule_id: str
    queue_entry_id: str
    trigger_source: str
    schedule_owner: str
    executor_is_adapter_only: bool
    audit_identity_ref: str
    run_queue_scope_ref: str
    rollback_plan_ref: str
    external_scheduler_denial_ref: str
    canonical_writeback_denial_ref: str
    audit_status: str = QUEUE_STATUS_PROOF_ONLY
    real_audit_event_written: bool = False
    approval_execution_allowed: bool = False
    schedule_activation_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    canonical_writeback_allowed: bool = False

    def validate(self) -> None:
        if not self.event_id or not self.queue_entry_id:
            raise ValueError("audit proof event requires ids")
        if self.event_type != AUDIT_EVENT_TYPE:
            raise ValueError("invalid audit proof event type")
        if self.trigger_source != TRIGGER_SOURCE:
            raise ValueError("audit proof event requires native ChaseOS trigger source")
        if self.schedule_owner != "chaseos" or not self.executor_is_adapter_only:
            raise ValueError("audit proof event requires ChaseOS ownership and adapter-only executor")
        if self.audit_status != QUEUE_STATUS_PROOF_ONLY:
            raise ValueError("audit proof event must remain proof-only")
        if not self.rollback_plan_ref or not self.external_scheduler_denial_ref:
            raise ValueError("audit proof event requires rollback and external-scheduler denial refs")
        if not self.canonical_writeback_denial_ref:
            raise ValueError("audit proof event requires canonical writeback denial ref")
        if (
            self.real_audit_event_written
            or self.approval_execution_allowed
            or self.schedule_activation_allowed
            or self.provider_or_connector_call_allowed
            or self.canonical_writeback_allowed
        ):
            raise ValueError("audit proof event cannot enable execution authority")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class PulseNativeScheduleRunQueueAuditProof:
    generated_at: str
    proof_status: str
    gate_status: str
    schedule_ids: tuple[str, ...]
    schedule_count: int
    proof_queue_entry_count: int
    proof_audit_event_count: int
    missing_evidence_slots: tuple[str, ...]
    run_queue_entries: tuple[PulseNativeScheduleRunQueueEntryProof, ...]
    audit_events: tuple[PulseNativeScheduleAuditEventProof, ...]
    write_requested: bool = False
    write_executed: bool = False
    writes: tuple[str, ...] = ()
    next_recommended_pass: str = NEXT_RECOMMENDED_PASS
    local_only: bool = True
    read_only: bool = True
    writes_artifacts: bool = False
    real_run_queue_written: bool = False
    real_audit_event_written: bool = False
    schedule_activation_allowed: bool = False
    schedule_manifest_write_allowed: bool = False
    schedule_daemon_started: bool = False
    agent_bus_task_write_allowed: bool = False
    runtime_dispatch_allowed: bool = False
    workflow_execution_allowed: bool = False
    approval_execution_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    external_scheduler_install_allowed: bool = False
    canonical_writeback_allowed: bool = False
    mutates_canonical_state: bool = False
    rd_workbook_update_allowed: bool = False
    allowed_write_root: str = ALLOWED_WRITE_ROOT
    blocked_effects: tuple[str, ...] = BLOCKED_EFFECTS
    notes: tuple[str, ...] = field(
        default_factory=lambda: (
            "This is a run-queue/audit proof packet, not a real scheduler queue write.",
            "Future schedule activation still requires separate supervised execution approval.",
        )
    )

    def validate(self) -> None:
        if self.proof_status not in PROOF_STATUSES:
            raise ValueError("invalid run queue audit proof status")
        if self.gate_status not in {"blocked_missing_activation_evidence", GATE_STATUS_READY}:
            raise ValueError("invalid source activation gate status")
        if self.schedule_count != len(self.schedule_ids):
            raise ValueError("schedule_count must match schedule_ids")
        if self.proof_queue_entry_count != len(self.run_queue_entries):
            raise ValueError("proof_queue_entry_count must match run queue entries")
        if self.proof_audit_event_count != len(self.audit_events):
            raise ValueError("proof_audit_event_count must match audit events")
        expected_status = PROOF_STATUS_READY if self.gate_status == GATE_STATUS_READY else PROOF_STATUS_BLOCKED
        if self.proof_status != expected_status:
            raise ValueError("run queue audit proof status must reflect activation gate status")
        if self.proof_status == PROOF_STATUS_BLOCKED and self.run_queue_entries:
            raise ValueError("blocked proof cannot build run queue entries")
        if self.proof_status == PROOF_STATUS_BLOCKED and self.audit_events:
            raise ValueError("blocked proof cannot build audit events")
        for entry in self.run_queue_entries:
            entry.validate()
        for event in self.audit_events:
            event.validate()
        if self.write_executed and not self.write_requested:
            raise ValueError("write_executed requires write_requested")
        if self.write_executed and self.read_only:
            raise ValueError("written run queue audit proof cannot be read_only")
        if self.write_executed and not self.writes_artifacts:
            raise ValueError("written run queue audit proof must report writes_artifacts")
        if self.real_run_queue_written or self.real_audit_event_written:
            raise ValueError("run queue audit proof cannot write real queue/audit state")
        if self.schedule_activation_allowed or self.schedule_manifest_write_allowed:
            raise ValueError("run queue audit proof cannot activate or write schedules")
        if self.schedule_daemon_started:
            raise ValueError("run queue audit proof cannot start a schedule daemon")
        if self.agent_bus_task_write_allowed:
            raise ValueError("run queue audit proof cannot write Agent Bus tasks")
        if self.runtime_dispatch_allowed or self.workflow_execution_allowed:
            raise ValueError("run queue audit proof cannot dispatch or execute workflows")
        if self.approval_execution_allowed:
            raise ValueError("run queue audit proof cannot execute approvals")
        if self.provider_or_connector_call_allowed:
            raise ValueError("run queue audit proof cannot call providers/connectors")
        if self.external_scheduler_install_allowed:
            raise ValueError("run queue audit proof cannot install external schedulers")
        if self.canonical_writeback_allowed or self.mutates_canonical_state:
            raise ValueError("run queue audit proof cannot mutate canonical state")
        if self.rd_workbook_update_allowed:
            raise ValueError("run queue audit proof cannot update the R&D workbook")
        for written in self.writes:
            if not written.replace("\\", "/").startswith(self.allowed_write_root):
                raise ValueError("run queue audit proof writes must stay under Pulse run-queue/audit proof logs")
        if set(self.blocked_effects) != set(BLOCKED_EFFECTS):
            raise ValueError("run queue audit proof must declare blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "proof_status": self.proof_status,
            "gate_status": self.gate_status,
            "schedule_ids": list(self.schedule_ids),
            "schedule_count": self.schedule_count,
            "proof_queue_entry_count": self.proof_queue_entry_count,
            "proof_audit_event_count": self.proof_audit_event_count,
            "missing_evidence_slots": list(self.missing_evidence_slots),
            "run_queue_entries": [entry.to_dict() for entry in self.run_queue_entries],
            "audit_events": [event.to_dict() for event in self.audit_events],
            "write_requested": self.write_requested,
            "write_executed": self.write_executed,
            "writes": list(self.writes),
            "next_recommended_pass": self.next_recommended_pass,
            "local_only": self.local_only,
            "read_only": self.read_only,
            "writes_artifacts": self.writes_artifacts,
            "real_run_queue_written": self.real_run_queue_written,
            "real_audit_event_written": self.real_audit_event_written,
            "schedule_activation_allowed": self.schedule_activation_allowed,
            "schedule_manifest_write_allowed": self.schedule_manifest_write_allowed,
            "schedule_daemon_started": self.schedule_daemon_started,
            "agent_bus_task_write_allowed": self.agent_bus_task_write_allowed,
            "runtime_dispatch_allowed": self.runtime_dispatch_allowed,
            "workflow_execution_allowed": self.workflow_execution_allowed,
            "approval_execution_allowed": self.approval_execution_allowed,
            "provider_or_connector_call_allowed": self.provider_or_connector_call_allowed,
            "external_scheduler_install_allowed": self.external_scheduler_install_allowed,
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "mutates_canonical_state": self.mutates_canonical_state,
            "rd_workbook_update_allowed": self.rd_workbook_update_allowed,
            "allowed_write_root": self.allowed_write_root,
            "blocked_effects": list(self.blocked_effects),
            "notes": list(self.notes),
        }


def _evidence_refs(evidence_refs: dict[str, str | None] | None) -> dict[str, str | None]:
    refs = evidence_refs or {}
    return {slot: refs.get(slot) for slot in REQUIRED_EVIDENCE_SLOTS}


def _build_entries(
    *,
    generated_at: str,
    evidence_refs: dict[str, str | None],
    activation_targets: tuple[Any, ...],
) -> tuple[
    tuple[PulseNativeScheduleRunQueueEntryProof, ...],
    tuple[PulseNativeScheduleAuditEventProof, ...],
]:
    date = _date_slug(generated_at)
    queue_entries: list[PulseNativeScheduleRunQueueEntryProof] = []
    audit_events: list[PulseNativeScheduleAuditEventProof] = []
    for target in activation_targets:
        schedule_slug = _slug(target.schedule_id)
        queue_id = f"pulse_run_queue_proof_{date}_{schedule_slug}"
        idempotency_key = f"{target.schedule_id}:{date}:{RUN_REASON_MISSED_RUN_CATCHUP}:proof"
        entry = PulseNativeScheduleRunQueueEntryProof(
            queue_entry_id=queue_id,
            schedule_id=target.schedule_id,
            workflow_id=target.workflow_id,
            audience=target.audience,
            output_root=target.output_root,
            run_reason=RUN_REASON_MISSED_RUN_CATCHUP,
            queue_status=QUEUE_STATUS_PROOF_ONLY,
            requested_for=generated_at,
            executor_adapter=target.executor_adapter,
            schedule_owner=target.schedule_owner,
            approval_ref=str(evidence_refs["operator_approval_ref"]),
            permission_envelope_ref=str(evidence_refs["permission_envelope_ref"]),
            audit_identity_ref=str(evidence_refs["audit_identity_ref"]),
            run_queue_scope_ref=str(evidence_refs["run_queue_scope_ref"]),
            idempotency_key=idempotency_key,
        )
        event = PulseNativeScheduleAuditEventProof(
            event_id=f"pulse_schedule_audit_proof_{date}_{schedule_slug}",
            event_type=AUDIT_EVENT_TYPE,
            schedule_id=target.schedule_id,
            queue_entry_id=queue_id,
            trigger_source=TRIGGER_SOURCE,
            schedule_owner=target.schedule_owner,
            executor_is_adapter_only=target.executor_is_adapter_only,
            audit_identity_ref=str(evidence_refs["audit_identity_ref"]),
            run_queue_scope_ref=str(evidence_refs["run_queue_scope_ref"]),
            rollback_plan_ref=str(evidence_refs["rollback_plan_ref"]),
            external_scheduler_denial_ref=str(evidence_refs["external_scheduler_denial_ref"]),
            canonical_writeback_denial_ref=str(evidence_refs["canonical_writeback_denial_ref"]),
        )
        entry.validate()
        event.validate()
        queue_entries.append(entry)
        audit_events.append(event)
    return tuple(queue_entries), tuple(audit_events)


def build_pulse_native_schedule_run_queue_audit_proof(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    schedule_ids: tuple[str, ...] | None = None,
    evidence_refs: dict[str, str | None] | None = None,
) -> PulseNativeScheduleRunQueueAuditProof:
    """Build a non-executing Pulse native schedule run-queue/audit proof."""

    vault = _vault_path(vault_root)
    generated = generated_at or now_utc()
    ids = _normalize_schedule_ids(schedule_ids)
    refs = _evidence_refs(evidence_refs)
    gate = build_pulse_native_schedule_activation_gate(
        vault,
        generated_at=generated,
        schedule_ids=ids,
        evidence_refs=refs,
    )
    if gate.gate_status == GATE_STATUS_READY:
        queue_entries, audit_events = _build_entries(
            generated_at=generated,
            evidence_refs=refs,
            activation_targets=gate.activation_targets,
        )
    else:
        queue_entries = ()
        audit_events = ()
    proof = PulseNativeScheduleRunQueueAuditProof(
        generated_at=generated,
        proof_status=PROOF_STATUS_READY if gate.gate_status == GATE_STATUS_READY else PROOF_STATUS_BLOCKED,
        gate_status=gate.gate_status,
        schedule_ids=ids,
        schedule_count=gate.schedule_count,
        proof_queue_entry_count=len(queue_entries),
        proof_audit_event_count=len(audit_events),
        missing_evidence_slots=gate.missing_evidence_slots,
        run_queue_entries=queue_entries,
        audit_events=audit_events,
    )
    proof.validate()
    return proof


def write_pulse_native_schedule_run_queue_audit_proof(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    schedule_ids: tuple[str, ...] | None = None,
    evidence_refs: dict[str, str | None] | None = None,
    output_path: str | Path | None = None,
) -> PulseNativeScheduleRunQueueAuditProof:
    """Write a proof-only run-queue/audit packet under Pulse logs."""

    vault = _vault_path(vault_root)
    generated = generated_at or now_utc()
    base = build_pulse_native_schedule_run_queue_audit_proof(
        vault,
        generated_at=generated,
        schedule_ids=schedule_ids,
        evidence_refs=evidence_refs,
    )
    schedule_slug = _slug("-".join(base.schedule_ids))
    if output_path is None:
        target_path = vault / ALLOWED_WRITE_ROOT / f"{_date_slug(generated)}-run-queue-audit-proof-{schedule_slug}.json"
    else:
        target_path = Path(output_path)
        if not target_path.is_absolute():
            target_path = vault / target_path
    target_path = target_path.resolve()
    allowed_root = (vault / ALLOWED_WRITE_ROOT).resolve()
    try:
        target_path.relative_to(allowed_root)
    except ValueError as exc:
        raise ValueError("native schedule run-queue/audit proof must be written under 07_LOGS/Pulse-Decks/native-schedule-run-queue-audit-proof/") from exc

    rel_path = target_path.relative_to(vault).as_posix()
    model = PulseNativeScheduleRunQueueAuditProof(
        generated_at=base.generated_at,
        proof_status=base.proof_status,
        gate_status=base.gate_status,
        schedule_ids=base.schedule_ids,
        schedule_count=base.schedule_count,
        proof_queue_entry_count=base.proof_queue_entry_count,
        proof_audit_event_count=base.proof_audit_event_count,
        missing_evidence_slots=base.missing_evidence_slots,
        run_queue_entries=base.run_queue_entries,
        audit_events=base.audit_events,
        write_requested=True,
        write_executed=True,
        writes=(rel_path,),
        read_only=False,
        writes_artifacts=True,
    )
    model.validate()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(model.to_dict(), indent=2), encoding="utf-8")
    return model
