"""Dry-run supervised live-enqueue rehearsal for Pulse Agent Bus handoff.

This module turns an operator/Gate approval contract into an operator-facing
rehearsal packet. It does not execute the enqueue command, grant approval,
write Agent Bus tasks, apply candidates, or mutate canonical state.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.card_schema import now_utc
from runtime.pulse.operator_gate_approval_contract import (
    PulseOperatorGateApprovalUIContract,
    build_operator_gate_approval_ui_contract,
)


PULSE_SUPERVISED_REHEARSAL_STATUS_READY = "ready_for_manual_enqueue"
PULSE_SUPERVISED_REHEARSAL_STATUS_BLOCKED = "blocked_operator_gate_contract_not_ready"
PULSE_SUPERVISED_REHEARSAL_STATUSES = {
    PULSE_SUPERVISED_REHEARSAL_STATUS_READY,
    PULSE_SUPERVISED_REHEARSAL_STATUS_BLOCKED,
}
PULSE_SUPERVISED_REHEARSAL_BLOCKED_EFFECTS = (
    "agent_bus_task_write",
    "approval_grant",
    "approval_execution",
    "candidate_apply",
    "canonical_writeback",
    "gate_policy_mutation",
    "provider_or_connector_call",
    "runtime_dispatch",
    "schedule_activation",
)


def _rehearsal_id(request_id: str, generated_at: str) -> str:
    digest = hashlib.sha256(f"{request_id}|{generated_at}".encode("utf-8")).hexdigest()[:12]
    return f"pulse-supervised-enqueue-rehearsal-{digest}"


def _operator_steps(ready: bool) -> tuple[str, ...]:
    if not ready:
        return (
            "Review blocked_reasons.",
            "Record or correct missing operator/Gate evidence.",
            "Refresh handoff preflight before any live enqueue.",
        )
    return (
        "Review visible evidence and safety warnings.",
        "Confirm the duplicate-work posture is still clear.",
        "Run the supervised enqueue command manually from the CLI.",
        "Inspect the enqueue result record and Agent Bus task ID.",
        "Wait for the review runtime response before any candidate apply step.",
    )


@dataclass(frozen=True)
class PulseSupervisedLiveEnqueueRehearsal:
    rehearsal_id: str
    request_id: str
    generated_at: str
    rehearsal_status: str
    operator_gate_contract: PulseOperatorGateApprovalUIContract
    evidence_id: str | None = None
    manual_command_preview: tuple[str, ...] = field(default_factory=tuple)
    required_operator_steps: tuple[str, ...] = field(default_factory=tuple)
    blocked_reasons: tuple[str, ...] = field(default_factory=tuple)
    rehearsal_record_only: bool = True
    persisted_rehearsal: bool = False
    live_enqueue_executed: bool = False
    approval_granted: bool = False
    approval_executed: bool = False
    gate_policy_mutated: bool = False
    agent_bus_task_written: bool = False
    runtime_dispatch_allowed: bool = False
    review_response_ingest_allowed: bool = False
    candidate_apply_allowed: bool = False
    canonical_writeback_allowed: bool = False
    mutates_canonical_state: bool = False
    second_datastore_write_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    schedule_activation_allowed: bool = False
    blocked_effects: tuple[str, ...] = PULSE_SUPERVISED_REHEARSAL_BLOCKED_EFFECTS

    @property
    def ready_for_manual_enqueue(self) -> bool:
        return self.rehearsal_status == PULSE_SUPERVISED_REHEARSAL_STATUS_READY

    def validate(self) -> None:
        if not self.rehearsal_id:
            raise ValueError("rehearsal_id is required")
        if not self.request_id:
            raise ValueError("request_id is required")
        if self.rehearsal_status not in PULSE_SUPERVISED_REHEARSAL_STATUSES:
            raise ValueError("invalid rehearsal_status")
        self.operator_gate_contract.validate()
        if self.rehearsal_status == PULSE_SUPERVISED_REHEARSAL_STATUS_READY:
            if not self.operator_gate_contract.ready_for_operator_gate_decision:
                raise ValueError("ready rehearsal requires ready operator/Gate contract")
            if not self.manual_command_preview:
                raise ValueError("ready rehearsal requires manual command preview")
            if self.blocked_reasons:
                raise ValueError("ready rehearsal cannot list blocked reasons")
        else:
            if self.manual_command_preview:
                raise ValueError("blocked rehearsal cannot expose manual command preview")
            if not self.blocked_reasons:
                raise ValueError("blocked rehearsal must list blocked reasons")
        if not self.required_operator_steps:
            raise ValueError("required_operator_steps are required")
        if not self.rehearsal_record_only:
            raise ValueError("supervised enqueue rehearsal must remain record-only")
        if self.persisted_rehearsal:
            raise ValueError("supervised enqueue rehearsal cannot persist artifacts")
        if self.live_enqueue_executed:
            raise ValueError("supervised enqueue rehearsal cannot execute live enqueue")
        if self.approval_granted:
            raise ValueError("supervised enqueue rehearsal cannot grant approval")
        if self.approval_executed:
            raise ValueError("supervised enqueue rehearsal cannot execute approval")
        if self.gate_policy_mutated:
            raise ValueError("supervised enqueue rehearsal cannot mutate Gate policy")
        if self.agent_bus_task_written:
            raise ValueError("supervised enqueue rehearsal cannot write Agent Bus tasks")
        if self.runtime_dispatch_allowed:
            raise ValueError("supervised enqueue rehearsal cannot dispatch runtimes")
        if self.review_response_ingest_allowed:
            raise ValueError("supervised enqueue rehearsal cannot ingest review responses")
        if self.candidate_apply_allowed:
            raise ValueError("supervised enqueue rehearsal cannot apply candidates")
        if self.canonical_writeback_allowed:
            raise ValueError("supervised enqueue rehearsal cannot allow canonical writeback")
        if self.mutates_canonical_state:
            raise ValueError("supervised enqueue rehearsal cannot mutate canonical state")
        if self.second_datastore_write_allowed:
            raise ValueError("supervised enqueue rehearsal cannot write a second datastore")
        if self.provider_or_connector_call_allowed:
            raise ValueError("supervised enqueue rehearsal cannot call providers or connectors")
        if self.schedule_activation_allowed:
            raise ValueError("supervised enqueue rehearsal cannot activate schedules")
        if set(self.blocked_effects) != set(PULSE_SUPERVISED_REHEARSAL_BLOCKED_EFFECTS):
            raise ValueError("supervised enqueue rehearsal must declare blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["ready_for_manual_enqueue"] = self.ready_for_manual_enqueue
        payload["operator_gate_contract"] = self.operator_gate_contract.to_dict()
        payload["manual_command_preview"] = list(self.manual_command_preview)
        payload["required_operator_steps"] = list(self.required_operator_steps)
        payload["blocked_reasons"] = list(self.blocked_reasons)
        payload["blocked_effects"] = list(self.blocked_effects)
        return payload


def build_supervised_live_enqueue_rehearsal(
    vault_root: str | Path,
    request_id: str,
    *,
    evidence_id: str | None = None,
    generated_at: str | None = None,
    bus_tasks: list[dict[str, Any]] | None = None,
) -> PulseSupervisedLiveEnqueueRehearsal:
    """Build a dry-run rehearsal packet for manual supervised enqueue."""
    timestamp = generated_at or now_utc()
    contract = build_operator_gate_approval_ui_contract(
        vault_root,
        request_id,
        evidence_id=evidence_id,
        generated_at=timestamp,
        bus_tasks=bus_tasks,
    )
    ready = contract.ready_for_operator_gate_decision
    blocked_reasons = tuple(contract.blocked_reasons)
    if not ready and not blocked_reasons:
        blocked_reasons = ("operator_gate_contract_not_ready",)
    rehearsal = PulseSupervisedLiveEnqueueRehearsal(
        rehearsal_id=_rehearsal_id(contract.request_id, timestamp),
        request_id=contract.request_id,
        generated_at=timestamp,
        rehearsal_status=(
            PULSE_SUPERVISED_REHEARSAL_STATUS_READY
            if ready
            else PULSE_SUPERVISED_REHEARSAL_STATUS_BLOCKED
        ),
        operator_gate_contract=contract,
        evidence_id=contract.evidence_id,
        manual_command_preview=contract.supervised_live_command_preview if ready else (),
        required_operator_steps=_operator_steps(ready),
        blocked_reasons=() if ready else blocked_reasons,
    )
    rehearsal.validate()
    return rehearsal
