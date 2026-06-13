"""Read-only Pulse approval readiness summary.

This module compresses the Pulse Agent Bus approval chain into a small operator
summary. It does not record evidence, grant approval, enqueue Agent Bus tasks,
dispatch runtimes, ingest reviews, apply candidates, or mutate canonical state.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.bus_enqueue_approval_request import (
    load_agent_bus_enqueue_approval_requests,
)
from runtime.pulse.card_schema import now_utc
from runtime.pulse.bus_enqueue_evidence import (
    PulseAgentBusEnqueueEvidenceRecord,
    load_agent_bus_enqueue_evidence_record_by_id,
)
from runtime.pulse.completion_status import build_pulse_completion_status
from runtime.pulse.supervised_live_enqueue_rehearsal import (
    build_supervised_live_enqueue_rehearsal,
)


PULSE_APPROVAL_READINESS_STATUS_READY = "ready_for_operator_approved_live_enqueue"
PULSE_APPROVAL_READINESS_STATUS_BLOCKED = "blocked_missing_required_evidence"
PULSE_APPROVAL_READINESS_STATUSES = {
    PULSE_APPROVAL_READINESS_STATUS_READY,
    PULSE_APPROVAL_READINESS_STATUS_BLOCKED,
}
PULSE_APPROVAL_READINESS_BLOCKED_EFFECTS = (
    "agent_bus_task_write",
    "approval_grant",
    "approval_execution",
    "candidate_apply",
    "canonical_writeback",
    "evidence_write",
    "gate_policy_mutation",
    "memory_approval",
    "provider_or_connector_call",
    "review_response_ingest",
    "runtime_dispatch",
    "schedule_activation",
)


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _latest_request_id(vault_root: str | Path) -> str:
    requests = load_agent_bus_enqueue_approval_requests(vault_root)
    if not requests:
        raise ValueError("no Pulse Agent Bus approval requests found")
    return requests[-1].request_id


def _missing_evidence_commands(request_id: str, missing: tuple[str, ...]) -> tuple[str, ...]:
    commands: list[str] = []
    if "operator_enqueue_approval" in missing:
        commands.append(
            f"chaseos pulse enqueue-evidence {request_id} --operator-approved --note <operator-approval-ref>"
        )
    if "gate_policy_defined" in missing:
        commands.append(
            f"chaseos pulse enqueue-evidence {request_id} --gate-policy-defined --gate-policy-ref <gate-policy-ref>"
        )
    if "external_sender_allowance" in missing:
        commands.append(
            f"chaseos pulse enqueue-evidence {request_id} --external-sender-allowance-present --external-sender-allowance-ref <allowance-ref>"
        )
    if "duplicate_work_fingerprint_review" in missing:
        commands.append(
            f"chaseos pulse enqueue-evidence {request_id} --duplicate-work-fingerprint-reviewed --duplicate-review-ref <duplicate-review-ref>"
        )
    return tuple(commands)


def _approval_evidence_slots(
    request_id: str,
    missing: tuple[str, ...],
    evidence: PulseAgentBusEnqueueEvidenceRecord | None,
) -> tuple[dict[str, Any], ...]:
    """Return structured operator-facing evidence slots without mutating state."""
    missing_set = set(missing)
    definitions = (
        (
            "operator_enqueue_approval",
            "Operator enqueue approval",
            "operator-approval-ref",
            "--operator-approved --note <operator-approval-ref>",
            evidence.evidence_note if evidence and evidence.operator_enqueue_approval_present else None,
            "operator_decision",
            False,
        ),
        (
            "gate_policy_defined",
            "Gate policy defined",
            "gate-policy-ref",
            "--gate-policy-defined --gate-policy-ref <gate-policy-ref>",
            evidence.gate_policy_ref if evidence and evidence.gate_policy_defined else None,
            "gate_policy",
            False,
        ),
        (
            "external_sender_allowance",
            "External sender allowance",
            "allowance-ref",
            "--external-sender-allowance-present --external-sender-allowance-ref <allowance-ref>",
            (
                evidence.external_sender_allowance_ref
                if evidence and evidence.external_sender_allowance_present
                else None
            ),
            "external_sender_policy",
            False,
        ),
        (
            "duplicate_work_fingerprint_review",
            "Duplicate work_fingerprint review",
            "duplicate-review-ref",
            "--duplicate-work-fingerprint-reviewed --duplicate-review-ref <duplicate-review-ref>",
            (
                evidence.duplicate_review_ref
                if evidence and evidence.duplicate_work_fingerprint_reviewed
                else None
            ),
            "queue_inspection",
            True,
        ),
    )
    return tuple(
        {
            "approval_key": key,
            "label": label,
            "satisfied": key not in missing_set,
            "required_ref": required_ref,
            "ref": ref,
            "ref_placeholder": f"<{required_ref}>",
            "requires_real_ref": True,
            "placeholder_ref_rejected": True,
            "capture_command": f"chaseos pulse enqueue-evidence {request_id} {flags}",
            "authority_class": authority_class,
            "runtime_self_satisfiable": runtime_self_satisfiable,
        }
        for key, label, required_ref, flags, ref, authority_class, runtime_self_satisfiable in definitions
    )


@dataclass(frozen=True)
class PulseApprovalReadinessSummary:
    generated_at: str
    request_id: str
    readiness_status: str
    feature_done: bool
    backend_control_plane_done: bool
    completion_status: str
    next_recommended_pass: str
    candidate_id: str
    candidate_kind: str
    recipient: str
    work_fingerprint: str
    evidence_id: str | None
    ready_for_operator_gate_decision: bool
    ready_for_manual_enqueue: bool
    handoff_status: str
    validation_status: str
    satisfied_approvals: tuple[str, ...]
    missing_approvals: tuple[str, ...]
    duplicate_found: bool
    active_duplicate_task_ids: tuple[str, ...]
    target_bus_snapshot_status: str
    target_active_task_count: int
    target_review_task_count: int
    blocked_reasons: tuple[str, ...]
    readiness_reasons: tuple[str, ...]
    required_operator_steps: tuple[str, ...]
    evidence_capture_command_hints: tuple[str, ...]
    approval_evidence_slots: tuple[dict[str, Any], ...]
    supervised_live_command_preview: tuple[str, ...] = field(default_factory=tuple)
    read_only: bool = True
    writes_status_artifact: bool = False
    evidence_write_allowed: bool = False
    approval_granted: bool = False
    live_enqueue_executed: bool = False
    agent_bus_task_written: bool = False
    runtime_dispatch_allowed: bool = False
    review_response_ingest_allowed: bool = False
    candidate_apply_allowed: bool = False
    canonical_writeback_allowed: bool = False
    mutates_canonical_state: bool = False
    provider_or_connector_call_allowed: bool = False
    schedule_activation_allowed: bool = False
    rd_workbook_update_allowed: bool = False
    blocked_effects: tuple[str, ...] = PULSE_APPROVAL_READINESS_BLOCKED_EFFECTS

    def validate(self) -> None:
        if not self.generated_at:
            raise ValueError("generated_at is required")
        if not self.request_id:
            raise ValueError("request_id is required")
        if self.readiness_status not in PULSE_APPROVAL_READINESS_STATUSES:
            raise ValueError("invalid readiness_status")
        if not self.next_recommended_pass:
            raise ValueError("next_recommended_pass is required")
        if not self.approval_evidence_slots:
            raise ValueError("approval_evidence_slots are required")
        for slot in self.approval_evidence_slots:
            if not slot.get("approval_key"):
                raise ValueError("approval evidence slots require approval_key")
            if not slot.get("capture_command"):
                raise ValueError("approval evidence slots require capture_command")
        if not self.candidate_id:
            raise ValueError("candidate_id is required")
        if not self.candidate_kind:
            raise ValueError("candidate_kind is required")
        if not self.recipient:
            raise ValueError("recipient is required")
        if not self.work_fingerprint:
            raise ValueError("work_fingerprint is required")
        if self.ready_for_manual_enqueue and self.missing_approvals:
            raise ValueError("manual enqueue readiness requires no missing approvals")
        if self.ready_for_manual_enqueue and not self.supervised_live_command_preview:
            raise ValueError("ready manual enqueue requires command preview")
        if not self.ready_for_manual_enqueue and self.supervised_live_command_preview:
            raise ValueError("blocked approval readiness cannot expose live command preview")
        if self.readiness_status == PULSE_APPROVAL_READINESS_STATUS_READY:
            if not self.ready_for_operator_gate_decision or not self.ready_for_manual_enqueue:
                raise ValueError("ready approval summary requires ready contract and rehearsal")
            if self.blocked_reasons:
                raise ValueError("ready approval summary cannot list blocked reasons")
        else:
            if not self.blocked_reasons:
                raise ValueError("blocked approval summary must list blocked reasons")
        if not self.read_only:
            raise ValueError("approval readiness summary must remain read-only")
        if self.writes_status_artifact:
            raise ValueError("approval readiness summary cannot write status artifacts")
        if self.evidence_write_allowed:
            raise ValueError("approval readiness summary cannot write evidence")
        if self.approval_granted:
            raise ValueError("approval readiness summary cannot grant approval")
        if self.live_enqueue_executed:
            raise ValueError("approval readiness summary cannot execute live enqueue")
        if self.agent_bus_task_written:
            raise ValueError("approval readiness summary cannot write Agent Bus tasks")
        if self.runtime_dispatch_allowed:
            raise ValueError("approval readiness summary cannot dispatch runtimes")
        if self.review_response_ingest_allowed:
            raise ValueError("approval readiness summary cannot ingest review responses")
        if self.candidate_apply_allowed:
            raise ValueError("approval readiness summary cannot apply candidates")
        if self.canonical_writeback_allowed:
            raise ValueError("approval readiness summary cannot allow canonical writeback")
        if self.mutates_canonical_state:
            raise ValueError("approval readiness summary cannot mutate canonical state")
        if self.provider_or_connector_call_allowed:
            raise ValueError("approval readiness summary cannot call providers or connectors")
        if self.schedule_activation_allowed:
            raise ValueError("approval readiness summary cannot activate schedules")
        if self.rd_workbook_update_allowed:
            raise ValueError("approval readiness summary cannot update the R&D workbook")
        if set(self.blocked_effects) != set(PULSE_APPROVAL_READINESS_BLOCKED_EFFECTS):
            raise ValueError("approval readiness summary must declare blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        for key in (
            "satisfied_approvals",
            "missing_approvals",
            "active_duplicate_task_ids",
            "blocked_reasons",
            "readiness_reasons",
            "required_operator_steps",
            "evidence_capture_command_hints",
            "approval_evidence_slots",
            "supervised_live_command_preview",
            "blocked_effects",
        ):
            payload[key] = list(payload[key])
        return payload


def build_pulse_approval_readiness_summary(
    vault_root: str | Path,
    request_id: str | None = None,
    *,
    evidence_id: str | None = None,
    generated_at: str | None = None,
    bus_tasks: list[dict[str, Any]] | None = None,
) -> PulseApprovalReadinessSummary:
    """Build a read-only operator summary for the Pulse approval chain."""
    vault = _vault_path(vault_root)
    timestamp = generated_at or now_utc()
    resolved_request_id = request_id or _latest_request_id(vault)
    completion = build_pulse_completion_status(vault, generated_at=timestamp)
    rehearsal = build_supervised_live_enqueue_rehearsal(
        vault,
        resolved_request_id,
        evidence_id=evidence_id,
        generated_at=timestamp,
        bus_tasks=bus_tasks,
    )
    contract = rehearsal.operator_gate_contract
    preflight = contract.handoff_preflight
    validation = preflight.validation
    missing = tuple(validation.missing_approvals)
    ready = contract.ready_for_operator_gate_decision and rehearsal.ready_for_manual_enqueue
    evidence_record = (
        load_agent_bus_enqueue_evidence_record_by_id(vault, preflight.evidence_id)
        if preflight.evidence_id
        else None
    )

    summary = PulseApprovalReadinessSummary(
        generated_at=timestamp,
        request_id=resolved_request_id,
        readiness_status=(
            PULSE_APPROVAL_READINESS_STATUS_READY
            if ready
            else PULSE_APPROVAL_READINESS_STATUS_BLOCKED
        ),
        feature_done=completion.feature_done,
        backend_control_plane_done=completion.backend_control_plane_done,
        completion_status=completion.overall_status,
        next_recommended_pass=completion.next_recommended_pass,
        candidate_id=preflight.request.candidate_id,
        candidate_kind=preflight.request.candidate_kind,
        recipient=preflight.request.recipient,
        work_fingerprint=preflight.request.work_fingerprint,
        evidence_id=preflight.evidence_id,
        ready_for_operator_gate_decision=contract.ready_for_operator_gate_decision,
        ready_for_manual_enqueue=rehearsal.ready_for_manual_enqueue,
        handoff_status=preflight.handoff_status,
        validation_status=validation.validation_status,
        satisfied_approvals=tuple(validation.satisfied_approvals),
        missing_approvals=missing,
        duplicate_found=preflight.duplicate_posture.duplicate_found,
        active_duplicate_task_ids=tuple(preflight.duplicate_posture.active_duplicate_task_ids),
        target_bus_snapshot_status=preflight.target_posture.bus_snapshot_status,
        target_active_task_count=preflight.target_posture.active_task_count,
        target_review_task_count=preflight.target_posture.review_task_count,
        blocked_reasons=() if ready else tuple(rehearsal.blocked_reasons),
        readiness_reasons=tuple(preflight.readiness_reasons),
        required_operator_steps=tuple(rehearsal.required_operator_steps),
        evidence_capture_command_hints=_missing_evidence_commands(resolved_request_id, missing),
        approval_evidence_slots=_approval_evidence_slots(
            resolved_request_id,
            missing,
            evidence_record,
        ),
        supervised_live_command_preview=(
            tuple(rehearsal.manual_command_preview) if ready else ()
        ),
    )
    summary.validate()
    return summary
