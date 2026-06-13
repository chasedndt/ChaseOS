"""Non-live Pulse Agent Bus handoff preflight.

This module composes a persisted approval request, an optional persisted
evidence artifact, approval validation, duplicate-work posture, and Agent Bus
target posture. It is read-only: no task creation, no approval grant, no
candidate apply, no runtime dispatch, and no canonical writeback.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.bus_enqueue import _ACTIVE_TASK_STATES
from runtime.pulse.bus_enqueue_approval_request import (
    PULSE_BUS_APPROVAL_BLOCKED_EFFECTS,
    PulseAgentBusEnqueueApprovalRequest,
    load_agent_bus_enqueue_approval_requests,
)
from runtime.pulse.bus_enqueue_approval_validation import (
    PULSE_BUS_APPROVAL_VALIDATION_STATUS_READY,
    PulseAgentBusApprovalValidationResult,
    validate_agent_bus_enqueue_approval_request,
)
from runtime.pulse.bus_enqueue_evidence import (
    PulseAgentBusEnqueueEvidenceRecord,
    load_agent_bus_enqueue_evidence_record_by_id,
    load_agent_bus_enqueue_evidence_records,
)
from runtime.pulse.card_schema import now_utc


PULSE_BUS_HANDOFF_PREFLIGHT_STATUS_READY = "ready_for_supervised_live_enqueue_review"
PULSE_BUS_HANDOFF_PREFLIGHT_STATUS_MISSING_EVIDENCE = "blocked_missing_required_evidence"
PULSE_BUS_HANDOFF_PREFLIGHT_STATUS_DUPLICATE = "blocked_duplicate_active_task"
PULSE_BUS_HANDOFF_PREFLIGHT_STATUS_BUS_UNAVAILABLE = "blocked_bus_snapshot_unavailable"
PULSE_BUS_HANDOFF_PREFLIGHT_STATUSES = {
    PULSE_BUS_HANDOFF_PREFLIGHT_STATUS_READY,
    PULSE_BUS_HANDOFF_PREFLIGHT_STATUS_MISSING_EVIDENCE,
    PULSE_BUS_HANDOFF_PREFLIGHT_STATUS_DUPLICATE,
    PULSE_BUS_HANDOFF_PREFLIGHT_STATUS_BUS_UNAVAILABLE,
}
PULSE_BUS_HANDOFF_PREFLIGHT_BLOCKED_EFFECTS = tuple(
    sorted(
        set(PULSE_BUS_APPROVAL_BLOCKED_EFFECTS)
        | {
            "agent_bus_task_write",
            "approval_grant",
            "approval_execution",
            "candidate_apply",
            "canonical_writeback",
            "gate_policy_mutation",
            "provider_or_connector_call",
            "runtime_dispatch",
            "schedule_activation",
        }
    )
)


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _preflight_id(request_id: str, evidence_id: str | None, checked_at: str) -> str:
    seed = "|".join([request_id, evidence_id or "no-evidence", checked_at])
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    return f"pulse-bus-handoff-preflight-{digest}"


def _find_request(
    vault_root: str | Path,
    request_id: str,
) -> PulseAgentBusEnqueueApprovalRequest:
    if not request_id:
        raise ValueError("request_id is required")
    for request in load_agent_bus_enqueue_approval_requests(vault_root):
        if request.request_id == request_id:
            return request
    raise ValueError(f"Pulse Agent Bus approval request not found: {request_id}")


def _latest_evidence_for_request(
    vault_root: str | Path,
    request_id: str,
) -> PulseAgentBusEnqueueEvidenceRecord | None:
    records = load_agent_bus_enqueue_evidence_records(vault_root, request_id=request_id)
    return records[-1] if records else None


def _load_evidence(
    vault_root: str | Path,
    request_id: str,
    evidence_id: str | None,
) -> PulseAgentBusEnqueueEvidenceRecord | None:
    if evidence_id:
        record = load_agent_bus_enqueue_evidence_record_by_id(vault_root, evidence_id)
        if record.request_id != request_id:
            raise ValueError("Pulse Agent Bus evidence record does not match request_id")
        return record
    return _latest_evidence_for_request(vault_root, request_id)


def _read_agent_bus_tasks(
    vault_root: Path,
    recipient: str,
    supplied_tasks: list[dict[str, Any]] | None,
) -> tuple[str, list[dict[str, Any]], str | None]:
    if supplied_tasks is not None:
        return "supplied", list(supplied_tasks), None
    try:
        from runtime.agent_bus import bus

        return "live_read_only", list(bus.list_tasks(vault_root, recipient=recipient)), None
    except Exception as exc:
        return "unavailable", [], str(exc)


@dataclass(frozen=True)
class PulseAgentBusDuplicatePosture:
    work_fingerprint: str
    duplicate_check_status: str
    duplicate_found: bool = False
    active_duplicate_task_ids: tuple[str, ...] = field(default_factory=tuple)
    active_duplicate_statuses: tuple[str, ...] = field(default_factory=tuple)
    query_error: str | None = None

    def validate(self) -> None:
        if not self.work_fingerprint:
            raise ValueError("work_fingerprint is required")
        if self.duplicate_check_status not in {"supplied", "live_read_only", "unavailable"}:
            raise ValueError("invalid duplicate_check_status")
        if self.duplicate_found and not self.active_duplicate_task_ids:
            raise ValueError("duplicate posture must list duplicate task ids")
        if self.duplicate_check_status == "unavailable" and not self.query_error:
            raise ValueError("unavailable duplicate posture requires query_error")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["active_duplicate_task_ids"] = list(self.active_duplicate_task_ids)
        payload["active_duplicate_statuses"] = list(self.active_duplicate_statuses)
        return payload


@dataclass(frozen=True)
class PulseAgentBusTargetPosture:
    recipient: str
    bus_snapshot_status: str
    task_count: int = 0
    active_task_count: int = 0
    review_task_count: int = 0
    counts_by_status: dict[str, int] = field(default_factory=dict)
    query_error: str | None = None

    def validate(self) -> None:
        if not self.recipient:
            raise ValueError("recipient is required")
        if self.bus_snapshot_status not in {"supplied", "live_read_only", "unavailable"}:
            raise ValueError("invalid bus_snapshot_status")
        if self.task_count < 0 or self.active_task_count < 0 or self.review_task_count < 0:
            raise ValueError("task counts cannot be negative")
        if self.bus_snapshot_status == "unavailable" and not self.query_error:
            raise ValueError("unavailable target posture requires query_error")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class PulseAgentBusHandoffPreflight:
    preflight_id: str
    request_id: str
    checked_at: str
    handoff_status: str
    request: PulseAgentBusEnqueueApprovalRequest
    validation: PulseAgentBusApprovalValidationResult
    duplicate_posture: PulseAgentBusDuplicatePosture
    target_posture: PulseAgentBusTargetPosture
    evidence_id: str | None = None
    evidence_record_present: bool = False
    readiness_reasons: tuple[str, ...] = field(default_factory=tuple)
    blocked_reasons: tuple[str, ...] = field(default_factory=tuple)
    preflight_record_only: bool = True
    persisted_preflight: bool = False
    approval_granted: bool = False
    approval_executed: bool = False
    gate_policy_mutated: bool = False
    live_agent_bus_handoff_allowed: bool = False
    agent_bus_task_written: bool = False
    runtime_dispatch_allowed: bool = False
    review_response_ingest_allowed: bool = False
    candidate_apply_allowed: bool = False
    canonical_writeback_allowed: bool = False
    mutates_canonical_state: bool = False
    second_datastore_write_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    schedule_activation_allowed: bool = False
    blocked_effects: tuple[str, ...] = PULSE_BUS_HANDOFF_PREFLIGHT_BLOCKED_EFFECTS

    @property
    def ready_for_supervised_live_command(self) -> bool:
        return self.handoff_status == PULSE_BUS_HANDOFF_PREFLIGHT_STATUS_READY

    def validate(self) -> None:
        if not self.preflight_id:
            raise ValueError("preflight_id is required")
        if not self.request_id:
            raise ValueError("request_id is required")
        if self.handoff_status not in PULSE_BUS_HANDOFF_PREFLIGHT_STATUSES:
            raise ValueError("invalid handoff_status")
        self.request.validate()
        self.validation.validate()
        self.duplicate_posture.validate()
        self.target_posture.validate()
        if self.evidence_record_present and not self.evidence_id:
            raise ValueError("evidence_id is required when evidence is present")
        if self.handoff_status == PULSE_BUS_HANDOFF_PREFLIGHT_STATUS_READY:
            if self.blocked_reasons:
                raise ValueError("ready handoff preflights cannot list blocked reasons")
            if self.validation.validation_status != PULSE_BUS_APPROVAL_VALIDATION_STATUS_READY:
                raise ValueError("ready handoff preflights require ready validation")
            if self.duplicate_posture.duplicate_found:
                raise ValueError("ready handoff preflights cannot have duplicates")
            if self.target_posture.bus_snapshot_status == "unavailable":
                raise ValueError("ready handoff preflights require bus target posture")
        else:
            if not self.blocked_reasons:
                raise ValueError("blocked handoff preflights must list blocked reasons")
        if not self.preflight_record_only:
            raise ValueError("handoff preflights must remain record-only")
        if self.persisted_preflight:
            raise ValueError("handoff preflights are not persisted in this pass")
        if self.approval_granted:
            raise ValueError("handoff preflights cannot grant approval")
        if self.approval_executed:
            raise ValueError("handoff preflights cannot execute approval")
        if self.gate_policy_mutated:
            raise ValueError("handoff preflights cannot mutate Gate policy")
        if self.live_agent_bus_handoff_allowed:
            raise ValueError("handoff preflights cannot allow live handoff")
        if self.agent_bus_task_written:
            raise ValueError("handoff preflights cannot write Agent Bus tasks")
        if self.runtime_dispatch_allowed:
            raise ValueError("handoff preflights cannot dispatch runtimes")
        if self.review_response_ingest_allowed:
            raise ValueError("handoff preflights cannot ingest review responses")
        if self.candidate_apply_allowed:
            raise ValueError("handoff preflights cannot apply candidates")
        if self.canonical_writeback_allowed:
            raise ValueError("handoff preflights cannot allow canonical writeback")
        if self.mutates_canonical_state:
            raise ValueError("handoff preflights cannot mutate canonical state")
        if self.second_datastore_write_allowed:
            raise ValueError("handoff preflights cannot write a second datastore")
        if self.provider_or_connector_call_allowed:
            raise ValueError("handoff preflights cannot call providers or connectors")
        if self.schedule_activation_allowed:
            raise ValueError("handoff preflights cannot activate schedules")
        if set(self.blocked_effects) != set(PULSE_BUS_HANDOFF_PREFLIGHT_BLOCKED_EFFECTS):
            raise ValueError("handoff preflights must declare blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "preflight_id": self.preflight_id,
            "request_id": self.request_id,
            "checked_at": self.checked_at,
            "handoff_status": self.handoff_status,
            "ready_for_supervised_live_command": self.ready_for_supervised_live_command,
            "evidence_id": self.evidence_id,
            "evidence_record_present": self.evidence_record_present,
            "readiness_reasons": list(self.readiness_reasons),
            "blocked_reasons": list(self.blocked_reasons),
            "request": self.request.to_dict(),
            "validation": self.validation.to_dict(),
            "duplicate_posture": self.duplicate_posture.to_dict(),
            "target_posture": self.target_posture.to_dict(),
            "preflight_record_only": self.preflight_record_only,
            "persisted_preflight": self.persisted_preflight,
            "approval_granted": self.approval_granted,
            "approval_executed": self.approval_executed,
            "gate_policy_mutated": self.gate_policy_mutated,
            "live_agent_bus_handoff_allowed": self.live_agent_bus_handoff_allowed,
            "agent_bus_task_written": self.agent_bus_task_written,
            "runtime_dispatch_allowed": self.runtime_dispatch_allowed,
            "review_response_ingest_allowed": self.review_response_ingest_allowed,
            "candidate_apply_allowed": self.candidate_apply_allowed,
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "mutates_canonical_state": self.mutates_canonical_state,
            "second_datastore_write_allowed": self.second_datastore_write_allowed,
            "provider_or_connector_call_allowed": self.provider_or_connector_call_allowed,
            "schedule_activation_allowed": self.schedule_activation_allowed,
            "blocked_effects": list(self.blocked_effects),
        }


def _build_duplicate_posture(
    request: PulseAgentBusEnqueueApprovalRequest,
    tasks: list[dict[str, Any]],
    status: str,
    query_error: str | None,
) -> PulseAgentBusDuplicatePosture:
    duplicates = [
        task
        for task in tasks
        if task.get("work_fingerprint") == request.work_fingerprint
        and task.get("status") in _ACTIVE_TASK_STATES
    ]
    posture = PulseAgentBusDuplicatePosture(
        work_fingerprint=request.work_fingerprint,
        duplicate_check_status=status,
        duplicate_found=bool(duplicates),
        active_duplicate_task_ids=tuple(str(task.get("task_id") or "") for task in duplicates),
        active_duplicate_statuses=tuple(str(task.get("status") or "") for task in duplicates),
        query_error=query_error,
    )
    posture.validate()
    return posture


def _build_target_posture(
    recipient: str,
    tasks: list[dict[str, Any]],
    status: str,
    query_error: str | None,
) -> PulseAgentBusTargetPosture:
    counts: dict[str, int] = {}
    for task in tasks:
        task_status = str(task.get("status") or "unknown")
        counts[task_status] = counts.get(task_status, 0) + 1
    posture = PulseAgentBusTargetPosture(
        recipient=recipient,
        bus_snapshot_status=status,
        task_count=len(tasks),
        active_task_count=sum(
            1 for task in tasks if task.get("status") in _ACTIVE_TASK_STATES
        ),
        review_task_count=sum(1 for task in tasks if task.get("intent") == "REVIEW"),
        counts_by_status=counts,
        query_error=query_error,
    )
    posture.validate()
    return posture


def build_agent_bus_handoff_preflight(
    vault_root: str | Path,
    request_id: str,
    *,
    evidence_id: str | None = None,
    checked_at: str | None = None,
    bus_tasks: list[dict[str, Any]] | None = None,
) -> PulseAgentBusHandoffPreflight:
    """Build a non-live handoff readiness preflight for one request."""
    vault = _vault_path(vault_root)
    timestamp = checked_at or now_utc()
    request = _find_request(vault, request_id)
    evidence = _load_evidence(vault, request_id, evidence_id)
    validation = validate_agent_bus_enqueue_approval_request(
        request,
        evidence=evidence.validation_evidence if evidence else None,
        validated_at=timestamp,
    )
    bus_status, tasks, bus_error = _read_agent_bus_tasks(vault, request.recipient, bus_tasks)
    duplicate_posture = _build_duplicate_posture(request, tasks, bus_status, bus_error)
    target_posture = _build_target_posture(request.recipient, tasks, bus_status, bus_error)

    blocked: list[str] = []
    ready: list[str] = []
    if not evidence:
        blocked.append("no_persisted_evidence_record")
    else:
        ready.append("persisted_evidence_record_loaded")
    if validation.validation_status != PULSE_BUS_APPROVAL_VALIDATION_STATUS_READY:
        blocked.append("approval_validation_not_ready")
        blocked.extend(f"missing:{item}" for item in validation.missing_approvals)
    else:
        ready.append("approval_validation_ready")
    if duplicate_posture.duplicate_found:
        blocked.append("active_duplicate_work_fingerprint")
    else:
        ready.append("no_active_duplicate_work_fingerprint")
    if target_posture.bus_snapshot_status == "unavailable":
        blocked.append("agent_bus_target_snapshot_unavailable")
    else:
        ready.append("agent_bus_target_snapshot_available")

    if target_posture.bus_snapshot_status == "unavailable":
        status = PULSE_BUS_HANDOFF_PREFLIGHT_STATUS_BUS_UNAVAILABLE
    elif duplicate_posture.duplicate_found:
        status = PULSE_BUS_HANDOFF_PREFLIGHT_STATUS_DUPLICATE
    elif validation.validation_status != PULSE_BUS_APPROVAL_VALIDATION_STATUS_READY or not evidence:
        status = PULSE_BUS_HANDOFF_PREFLIGHT_STATUS_MISSING_EVIDENCE
    else:
        status = PULSE_BUS_HANDOFF_PREFLIGHT_STATUS_READY

    preflight = PulseAgentBusHandoffPreflight(
        preflight_id=_preflight_id(
            request.request_id,
            evidence.evidence_id if evidence else None,
            timestamp,
        ),
        request_id=request.request_id,
        checked_at=timestamp,
        handoff_status=status,
        request=request,
        validation=validation,
        duplicate_posture=duplicate_posture,
        target_posture=target_posture,
        evidence_id=evidence.evidence_id if evidence else None,
        evidence_record_present=evidence is not None,
        readiness_reasons=tuple(ready),
        blocked_reasons=tuple(blocked),
    )
    preflight.validate()
    return preflight
