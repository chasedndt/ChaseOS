"""Non-executing validation for Pulse Agent Bus enqueue approval requests.

The validation layer checks whether an approval-request record has the evidence
needed for a later handoff review. It does not approve requests, write Agent Bus
tasks, dispatch runtimes, ingest review responses, apply candidates, or persist
validation state.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.bus_enqueue_approval_request import (
    PULSE_BUS_APPROVAL_BLOCKED_EFFECTS,
    PULSE_BUS_ENQUEUE_REQUIRED_APPROVALS,
    PulseAgentBusEnqueueApprovalRequest,
    load_agent_bus_enqueue_approval_requests,
)
from runtime.pulse.card_schema import now_utc


PULSE_BUS_APPROVAL_VALIDATION_LEDGER_STATUS = "read_only"
PULSE_BUS_APPROVAL_VALIDATION_STATUS_READY = "ready_for_final_handoff_review"
PULSE_BUS_APPROVAL_VALIDATION_STATUS_BLOCKED = "blocked_missing_required_evidence"
PULSE_BUS_APPROVAL_VALIDATION_STATUSES = {
    PULSE_BUS_APPROVAL_VALIDATION_STATUS_READY,
    PULSE_BUS_APPROVAL_VALIDATION_STATUS_BLOCKED,
}
PULSE_BUS_APPROVAL_VALIDATION_BLOCKED_EFFECTS = tuple(
    sorted(
        set(PULSE_BUS_APPROVAL_BLOCKED_EFFECTS)
        | {
            "approval_validation_persistence",
            "approval_state_transition",
            "agent_bus_duplicate_query",
            "gate_policy_mutation",
            "operator_approval_grant",
        }
    )
)


@dataclass(frozen=True)
class PulseAgentBusApprovalValidationEvidence:
    """Evidence flags supplied by a future reviewer or Gate surface."""

    operator_enqueue_approval_present: bool = False
    gate_policy_defined: bool = False
    external_sender_allowance_present: bool = False
    duplicate_work_fingerprint_reviewed: bool = False
    reviewer: str = "operator"
    evidence_note: str = ""

    @property
    def satisfied_approvals(self) -> tuple[str, ...]:
        satisfied: list[str] = []
        if self.operator_enqueue_approval_present:
            satisfied.append("operator_enqueue_approval")
        if self.gate_policy_defined:
            satisfied.append("gate_policy_defined")
        if self.external_sender_allowance_present:
            satisfied.append("external_sender_allowance")
        if self.duplicate_work_fingerprint_reviewed:
            satisfied.append("duplicate_work_fingerprint_review")
        return tuple(satisfied)

    @property
    def missing_approvals(self) -> tuple[str, ...]:
        satisfied = set(self.satisfied_approvals)
        return tuple(
            approval
            for approval in PULSE_BUS_ENQUEUE_REQUIRED_APPROVALS
            if approval not in satisfied
        )

    def validate(self) -> None:
        if not self.reviewer:
            raise ValueError("reviewer is required")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["satisfied_approvals"] = list(self.satisfied_approvals)
        payload["missing_approvals"] = list(self.missing_approvals)
        return payload


@dataclass
class PulseAgentBusApprovalValidationResult:
    """In-memory validation result for one approval request."""

    validation_id: str
    request_id: str
    preflight_id: str
    contract_id: str
    candidate_id: str
    candidate_kind: str
    recipient: str
    work_fingerprint: str
    validation_status: str
    validated_at: str = field(default_factory=now_utc)
    reviewer: str = "operator"
    satisfied_approvals: tuple[str, ...] = field(default_factory=tuple)
    missing_approvals: tuple[str, ...] = field(default_factory=tuple)
    evidence_note: str = ""
    validation_record_only: bool = True
    persisted_validation: bool = False
    approval_granted: bool = False
    approval_executed: bool = False
    gate_policy_mutated: bool = False
    duplicate_query_performed: bool = False
    live_agent_bus_handoff_allowed: bool = False
    agent_bus_task_written: bool = False
    review_response_ingest_allowed: bool = False
    candidate_apply_allowed: bool = False
    canonical_writeback_allowed: bool = False
    mutates_canonical_state: bool = False
    second_datastore_write_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    schedule_activation_allowed: bool = False
    blocked_effects: tuple[str, ...] = PULSE_BUS_APPROVAL_VALIDATION_BLOCKED_EFFECTS

    def validate(self) -> None:
        if not self.validation_id:
            raise ValueError("validation_id is required")
        if not self.request_id:
            raise ValueError("request_id is required")
        if not self.preflight_id:
            raise ValueError("preflight_id is required")
        if not self.contract_id:
            raise ValueError("contract_id is required")
        if not self.candidate_id:
            raise ValueError("candidate_id is required")
        if not self.candidate_kind:
            raise ValueError("candidate_kind is required")
        if not self.recipient:
            raise ValueError("recipient is required")
        if not self.work_fingerprint:
            raise ValueError("work_fingerprint is required")
        if self.validation_status not in PULSE_BUS_APPROVAL_VALIDATION_STATUSES:
            raise ValueError("invalid Pulse Agent Bus approval validation status")
        if not self.reviewer:
            raise ValueError("reviewer is required")
        if set(self.satisfied_approvals) | set(self.missing_approvals) != set(
            PULSE_BUS_ENQUEUE_REQUIRED_APPROVALS
        ):
            raise ValueError("validation result must account for every required approval")
        if set(self.satisfied_approvals) & set(self.missing_approvals):
            raise ValueError("validation result cannot both satisfy and miss the same approval")
        if (
            self.validation_status == PULSE_BUS_APPROVAL_VALIDATION_STATUS_READY
            and self.missing_approvals
        ):
            raise ValueError("ready validation results cannot have missing approvals")
        if (
            self.validation_status == PULSE_BUS_APPROVAL_VALIDATION_STATUS_BLOCKED
            and not self.missing_approvals
        ):
            raise ValueError("blocked validation results must list missing approvals")
        if not self.validation_record_only:
            raise ValueError("approval validations must remain record-only")
        if self.persisted_validation:
            raise ValueError("approval validations are not persisted in this pass")
        if self.approval_granted:
            raise ValueError("approval validations cannot grant approval")
        if self.approval_executed:
            raise ValueError("approval validations cannot execute approval")
        if self.gate_policy_mutated:
            raise ValueError("approval validations cannot mutate Gate policy")
        if self.duplicate_query_performed:
            raise ValueError("approval validations cannot query live Agent Bus duplicates")
        if self.live_agent_bus_handoff_allowed:
            raise ValueError("approval validations cannot allow live handoff")
        if self.agent_bus_task_written:
            raise ValueError("approval validations cannot write bus tasks")
        if self.review_response_ingest_allowed:
            raise ValueError("approval validations cannot ingest review responses")
        if self.candidate_apply_allowed:
            raise ValueError("approval validations cannot apply candidates")
        if self.canonical_writeback_allowed:
            raise ValueError("approval validations cannot allow canonical writeback")
        if self.mutates_canonical_state:
            raise ValueError("approval validations cannot mutate canonical state")
        if self.second_datastore_write_allowed:
            raise ValueError("approval validations cannot write a second datastore")
        if self.provider_or_connector_call_allowed:
            raise ValueError("approval validations cannot call providers or connectors")
        if self.schedule_activation_allowed:
            raise ValueError("approval validations cannot activate schedules")
        if set(self.blocked_effects) != set(PULSE_BUS_APPROVAL_VALIDATION_BLOCKED_EFFECTS):
            raise ValueError("approval validations must declare blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["satisfied_approvals"] = list(self.satisfied_approvals)
        payload["missing_approvals"] = list(self.missing_approvals)
        payload["blocked_effects"] = list(self.blocked_effects)
        return payload


@dataclass
class PulseAgentBusApprovalValidationLedger:
    generated_at: str = field(default_factory=now_utc)
    validations: list[PulseAgentBusApprovalValidationResult] = field(default_factory=list)
    ledger_status: str = PULSE_BUS_APPROVAL_VALIDATION_LEDGER_STATUS
    writes: list[str] = field(default_factory=list)
    approval_granted: bool = False
    agent_bus_task_written: bool = False
    approval_executed: bool = False
    canonical_writeback_allowed: bool = False
    second_datastore_write_allowed: bool = False
    blocked_effects: tuple[str, ...] = PULSE_BUS_APPROVAL_VALIDATION_BLOCKED_EFFECTS

    @property
    def validation_count(self) -> int:
        return len(self.validations)

    @property
    def counts_by_status(self) -> dict[str, int]:
        counts = {status: 0 for status in sorted(PULSE_BUS_APPROVAL_VALIDATION_STATUSES)}
        for validation in self.validations:
            counts[validation.validation_status] += 1
        return counts

    def validate(self) -> None:
        if self.ledger_status != PULSE_BUS_APPROVAL_VALIDATION_LEDGER_STATUS:
            raise ValueError("approval validation ledgers are read-only")
        if self.writes:
            raise ValueError("approval validation ledgers cannot declare writes")
        if self.approval_granted:
            raise ValueError("approval validation ledgers cannot grant approval")
        if self.agent_bus_task_written:
            raise ValueError("approval validation ledgers cannot write bus tasks")
        if self.approval_executed:
            raise ValueError("approval validation ledgers cannot execute approval")
        if self.canonical_writeback_allowed:
            raise ValueError("approval validation ledgers cannot allow canonical writeback")
        if self.second_datastore_write_allowed:
            raise ValueError("approval validation ledgers cannot write a second datastore")
        if set(self.blocked_effects) != set(PULSE_BUS_APPROVAL_VALIDATION_BLOCKED_EFFECTS):
            raise ValueError("approval validation ledgers must declare blocked effects")
        for validation in self.validations:
            validation.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "ledger_status": self.ledger_status,
            "validation_count": self.validation_count,
            "counts_by_status": self.counts_by_status,
            "writes": list(self.writes),
            "approval_granted": self.approval_granted,
            "agent_bus_task_written": self.agent_bus_task_written,
            "approval_executed": self.approval_executed,
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "second_datastore_write_allowed": self.second_datastore_write_allowed,
            "blocked_effects": list(self.blocked_effects),
            "validations": [validation.to_dict() for validation in self.validations],
        }


def _validation_id(
    request: PulseAgentBusEnqueueApprovalRequest,
    evidence: PulseAgentBusApprovalValidationEvidence,
    validated_at: str,
) -> str:
    seed = "|".join(
        [
            request.request_id,
            request.preflight_id,
            request.candidate_id,
            request.work_fingerprint,
            ",".join(evidence.satisfied_approvals),
            ",".join(evidence.missing_approvals),
            evidence.reviewer,
            validated_at,
        ]
    )
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    return f"pulse-bus-approval-validation-{digest}"


def validate_agent_bus_enqueue_approval_request(
    request: PulseAgentBusEnqueueApprovalRequest,
    *,
    evidence: PulseAgentBusApprovalValidationEvidence | None = None,
    validated_at: str | None = None,
) -> PulseAgentBusApprovalValidationResult:
    """Validate one request without approving or executing it."""
    request.validate()
    evidence = evidence or PulseAgentBusApprovalValidationEvidence()
    evidence.validate()
    timestamp = validated_at or now_utc()
    missing = evidence.missing_approvals
    status = (
        PULSE_BUS_APPROVAL_VALIDATION_STATUS_READY
        if not missing
        else PULSE_BUS_APPROVAL_VALIDATION_STATUS_BLOCKED
    )
    validation = PulseAgentBusApprovalValidationResult(
        validation_id=_validation_id(request, evidence, timestamp),
        request_id=request.request_id,
        preflight_id=request.preflight_id,
        contract_id=request.contract_id,
        candidate_id=request.candidate_id,
        candidate_kind=request.candidate_kind,
        recipient=request.recipient,
        work_fingerprint=request.work_fingerprint,
        validation_status=status,
        validated_at=timestamp,
        reviewer=evidence.reviewer,
        satisfied_approvals=evidence.satisfied_approvals,
        missing_approvals=missing,
        evidence_note=evidence.evidence_note,
    )
    validation.validate()
    return validation


def validate_agent_bus_enqueue_approval_request_by_id(
    vault_root: str | Path,
    request_id: str,
    *,
    evidence: PulseAgentBusApprovalValidationEvidence | None = None,
    validated_at: str | None = None,
) -> PulseAgentBusApprovalValidationResult:
    """Load approval requests read-only and validate one by ID."""
    if not request_id:
        raise ValueError("request_id is required")
    requests = load_agent_bus_enqueue_approval_requests(vault_root)
    for request in requests:
        if request.request_id == request_id:
            return validate_agent_bus_enqueue_approval_request(
                request,
                evidence=evidence,
                validated_at=validated_at,
            )
    raise ValueError(f"Pulse Agent Bus approval request not found: {request_id}")


def build_agent_bus_enqueue_approval_validation_ledger(
    vault_root: str | Path,
    *,
    evidence_by_request_id: dict[str, PulseAgentBusApprovalValidationEvidence] | None = None,
    validated_at: str | None = None,
) -> PulseAgentBusApprovalValidationLedger:
    """Build a read-only validation ledger for persisted approval requests."""
    requests = load_agent_bus_enqueue_approval_requests(vault_root)
    validations = [
        validate_agent_bus_enqueue_approval_request(
            request,
            evidence=(evidence_by_request_id or {}).get(request.request_id),
            validated_at=validated_at,
        )
        for request in requests
    ]
    ledger = PulseAgentBusApprovalValidationLedger(
        generated_at=validated_at or now_utc(),
        validations=validations,
    )
    ledger.validate()
    return ledger
