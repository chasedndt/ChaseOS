"""Read-only final evidence gate for ChaseOS Pulse.

This module answers the last practical question before a live Pulse Agent Bus
handoff: are all required approval refs present, and if not, which authority
must supply them? It does not record evidence, grant approval, enqueue tasks,
dispatch runtimes, ingest reviews, apply candidates, or mutate canonical state.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from runtime.pulse.approval_readiness_summary import (
    build_pulse_approval_readiness_summary,
)
from runtime.pulse.card_schema import now_utc
from runtime.pulse.completion_status import build_pulse_completion_status


PULSE_FINAL_GATE_STATUS_READY = "ready_for_explicit_operator_live_enqueue"
PULSE_FINAL_GATE_STATUS_BLOCKED = "blocked_required_evidence_missing"
PULSE_FINAL_GATE_STATUSES = {
    PULSE_FINAL_GATE_STATUS_READY,
    PULSE_FINAL_GATE_STATUS_BLOCKED,
}
PULSE_FINAL_GATE_CLOSURE_STATUS_READY = "ready_for_supervised_live_enqueue"
PULSE_FINAL_GATE_CLOSURE_STATUS_AUTHORITY_BLOCKED = "blocked_by_external_authority"
PULSE_FINAL_GATE_CLOSURE_STATUS_RUNTIME_ACTION = "runtime_self_satisfiable_evidence_missing"
PULSE_FINAL_GATE_CLOSURE_STATUS_ACTIVE_DUPLICATE = "blocked_by_active_duplicate"
PULSE_FINAL_GATE_CLOSURE_STATUSES = {
    PULSE_FINAL_GATE_CLOSURE_STATUS_READY,
    PULSE_FINAL_GATE_CLOSURE_STATUS_AUTHORITY_BLOCKED,
    PULSE_FINAL_GATE_CLOSURE_STATUS_RUNTIME_ACTION,
    PULSE_FINAL_GATE_CLOSURE_STATUS_ACTIVE_DUPLICATE,
}
PULSE_FINAL_GATE_BLOCKED_EFFECTS = (
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


def _missing_operator_slots(slots: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "approval_key": slot["approval_key"],
            "label": slot["label"],
            "required_ref": slot["required_ref"],
            "ref_placeholder": slot["ref_placeholder"],
            "authority_class": slot["authority_class"],
            "runtime_self_satisfiable": slot["runtime_self_satisfiable"],
            "capture_command": slot["capture_command"],
        }
        for slot in slots
        if not bool(slot.get("satisfied"))
    )


def _partition_missing_slots(
    missing_slots: tuple[dict[str, Any], ...]
) -> tuple[tuple[dict[str, Any], ...], tuple[dict[str, Any], ...]]:
    authority_slots = tuple(
        slot for slot in missing_slots if not bool(slot.get("runtime_self_satisfiable"))
    )
    runtime_slots = tuple(
        slot for slot in missing_slots if bool(slot.get("runtime_self_satisfiable"))
    )
    return authority_slots, runtime_slots


def _unique_slot_values(slots: tuple[dict[str, Any], ...], key: str) -> tuple[str, ...]:
    values: list[str] = []
    for slot in slots:
        value = str(slot.get(key) or "")
        if value and value not in values:
            values.append(value)
    return tuple(values)


def _closure_status(
    ready: bool,
    authority_slots: tuple[dict[str, Any], ...],
    runtime_slots: tuple[dict[str, Any], ...],
    *,
    duplicate_found: bool,
) -> str:
    if ready:
        return PULSE_FINAL_GATE_CLOSURE_STATUS_READY
    if authority_slots:
        return PULSE_FINAL_GATE_CLOSURE_STATUS_AUTHORITY_BLOCKED
    if runtime_slots:
        return PULSE_FINAL_GATE_CLOSURE_STATUS_RUNTIME_ACTION
    if duplicate_found:
        return PULSE_FINAL_GATE_CLOSURE_STATUS_ACTIVE_DUPLICATE
    raise ValueError("blocked final gate must identify authority, runtime, or duplicate closure work")


def _operator_action_steps(missing_slots: tuple[dict[str, Any], ...]) -> tuple[str, ...]:
    if not missing_slots:
        return (
            "Run the supervised live enqueue command only after explicit operator confirmation.",
            "Keep the resulting Agent Bus task under REVIEW and do not apply candidates automatically.",
        )
    steps: list[str] = []
    for slot in missing_slots:
        key = slot["approval_key"]
        if key == "operator_enqueue_approval":
            steps.append("Record a real operator enqueue approval reference.")
        elif key == "gate_policy_defined":
            steps.append("Record a real Gate policy reference for this Pulse handoff.")
        elif key == "external_sender_allowance":
            steps.append("Record a real external sender allowance reference for the target runtime.")
        elif key == "duplicate_work_fingerprint_review":
            steps.append("Record a real duplicate work_fingerprint review reference.")
        else:
            steps.append(f"Record a real approval reference for {key}.")
    steps.append("Rerun `chaseos pulse approval-readiness --json` after recording evidence.")
    steps.append("Rerun this final evidence gate before any live enqueue.")
    return tuple(steps)


@dataclass(frozen=True)
class PulseFinalEvidenceGateStatus:
    generated_at: str
    gate_status: str
    request_id: str
    evidence_id: str | None
    candidate_id: str
    candidate_kind: str
    recipient: str
    work_fingerprint: str
    completion_status: str
    feature_done: bool
    backend_control_plane_done: bool
    next_recommended_pass: str
    readiness_status: str
    ready_for_operator_gate_decision: bool
    ready_for_manual_enqueue: bool
    ready_for_live_enqueue: bool
    operator_action_required: bool
    can_runtime_self_satisfy_remaining: bool
    closure_status: str
    closure_authority_classes: tuple[str, ...]
    closure_runtime_action_keys: tuple[str, ...]
    satisfied_approvals: tuple[str, ...]
    missing_approvals: tuple[str, ...]
    missing_operator_action_slots: tuple[dict[str, Any], ...]
    missing_authority_action_slots: tuple[dict[str, Any], ...]
    missing_runtime_self_satisfiable_slots: tuple[dict[str, Any], ...]
    approval_evidence_slots: tuple[dict[str, Any], ...]
    evidence_capture_command_hints: tuple[str, ...]
    next_required_actions: tuple[str, ...]
    final_feature_blockers: tuple[str, ...]
    supervised_live_command_preview: tuple[str, ...]
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
    blocked_effects: tuple[str, ...] = PULSE_FINAL_GATE_BLOCKED_EFFECTS

    def validate(self) -> None:
        if not self.generated_at:
            raise ValueError("generated_at is required")
        if self.gate_status not in PULSE_FINAL_GATE_STATUSES:
            raise ValueError("invalid final evidence gate_status")
        if not self.request_id:
            raise ValueError("request_id is required")
        if not self.candidate_id:
            raise ValueError("candidate_id is required")
        if not self.candidate_kind:
            raise ValueError("candidate_kind is required")
        if not self.recipient:
            raise ValueError("recipient is required")
        if not self.work_fingerprint:
            raise ValueError("work_fingerprint is required")
        if not self.approval_evidence_slots:
            raise ValueError("approval_evidence_slots are required")
        if tuple(self.missing_authority_action_slots) + tuple(
            self.missing_runtime_self_satisfiable_slots
        ) != tuple(self.missing_operator_action_slots):
            raise ValueError("missing slot partitions must match missing operator action slots")
        for slot in self.missing_authority_action_slots:
            if bool(slot.get("runtime_self_satisfiable")):
                raise ValueError("authority action slots cannot be runtime-self-satisfiable")
        for slot in self.missing_runtime_self_satisfiable_slots:
            if not bool(slot.get("runtime_self_satisfiable")):
                raise ValueError("runtime-self-satisfiable slots must be marked self-satisfiable")
        if self.operator_action_required != bool(self.missing_authority_action_slots):
            raise ValueError("operator_action_required must reflect missing authority slots")
        if self.can_runtime_self_satisfy_remaining != (
            bool(self.missing_runtime_self_satisfiable_slots)
            and not self.missing_authority_action_slots
        ):
            raise ValueError("runtime self-satisfaction flag must reflect missing runtime slots")
        if self.closure_status not in PULSE_FINAL_GATE_CLOSURE_STATUSES:
            raise ValueError("invalid final evidence closure_status")
        expected_authority_classes = _unique_slot_values(
            self.missing_authority_action_slots, "authority_class"
        )
        if self.closure_authority_classes != expected_authority_classes:
            raise ValueError("closure authority classes must reflect missing authority slots")
        expected_runtime_keys = list(
            _unique_slot_values(self.missing_runtime_self_satisfiable_slots, "approval_key")
        )
        if self.closure_status == PULSE_FINAL_GATE_CLOSURE_STATUS_ACTIVE_DUPLICATE:
            expected_runtime_keys.append("active_duplicate_work_fingerprint")
        if self.closure_runtime_action_keys != tuple(expected_runtime_keys):
            raise ValueError("closure runtime action keys must reflect missing runtime slots")
        expected_closure_status = _closure_status(
            self.ready_for_live_enqueue,
            self.missing_authority_action_slots,
            self.missing_runtime_self_satisfiable_slots,
            duplicate_found="active_duplicate_work_fingerprint" in self.closure_runtime_action_keys,
        )
        if self.closure_status != expected_closure_status:
            raise ValueError("closure_status must reflect final gate closure state")
        if not self.next_required_actions:
            raise ValueError("next_required_actions are required")
        if self.ready_for_live_enqueue != self.ready_for_manual_enqueue:
            raise ValueError("ready_for_live_enqueue mirrors manual enqueue readiness")
        if self.ready_for_live_enqueue:
            if self.missing_approvals or self.missing_operator_action_slots:
                raise ValueError("live enqueue readiness requires no missing approvals")
            if self.operator_action_required:
                raise ValueError("ready live enqueue cannot require missing operator action")
            if not self.supervised_live_command_preview:
                raise ValueError("ready live enqueue requires supervised command preview")
            if self.gate_status != PULSE_FINAL_GATE_STATUS_READY:
                raise ValueError("ready live enqueue requires ready gate status")
        else:
            if not self.missing_approvals and self.closure_status != PULSE_FINAL_GATE_CLOSURE_STATUS_ACTIVE_DUPLICATE:
                raise ValueError("blocked final gate must list missing approvals or active duplicate")
            if (
                not self.operator_action_required
                and not self.can_runtime_self_satisfy_remaining
                and self.closure_status != PULSE_FINAL_GATE_CLOSURE_STATUS_ACTIVE_DUPLICATE
            ):
                raise ValueError("blocked final gate requires resolvable missing evidence or duplicate")
            if self.supervised_live_command_preview:
                raise ValueError("blocked final gate cannot expose live command preview")
            if self.gate_status != PULSE_FINAL_GATE_STATUS_BLOCKED:
                raise ValueError("blocked final gate requires blocked gate status")
        if self.can_runtime_self_satisfy_remaining and self.operator_action_required:
            raise ValueError("runtime cannot self-satisfy operator-required slots")
        if not self.read_only:
            raise ValueError("final evidence gate must remain read-only")
        if self.writes_status_artifact:
            raise ValueError("final evidence gate cannot write status artifacts")
        if self.evidence_write_allowed:
            raise ValueError("final evidence gate cannot write evidence")
        if self.approval_granted:
            raise ValueError("final evidence gate cannot grant approval")
        if self.live_enqueue_executed:
            raise ValueError("final evidence gate cannot execute live enqueue")
        if self.agent_bus_task_written:
            raise ValueError("final evidence gate cannot write Agent Bus tasks")
        if self.runtime_dispatch_allowed:
            raise ValueError("final evidence gate cannot dispatch runtimes")
        if self.review_response_ingest_allowed:
            raise ValueError("final evidence gate cannot ingest review responses")
        if self.candidate_apply_allowed:
            raise ValueError("final evidence gate cannot apply candidates")
        if self.canonical_writeback_allowed:
            raise ValueError("final evidence gate cannot allow canonical writeback")
        if self.mutates_canonical_state:
            raise ValueError("final evidence gate cannot mutate canonical state")
        if self.provider_or_connector_call_allowed:
            raise ValueError("final evidence gate cannot call providers or connectors")
        if self.schedule_activation_allowed:
            raise ValueError("final evidence gate cannot activate schedules")
        if self.rd_workbook_update_allowed:
            raise ValueError("final evidence gate cannot update the R&D workbook")
        if set(self.blocked_effects) != set(PULSE_FINAL_GATE_BLOCKED_EFFECTS):
            raise ValueError("final evidence gate must declare blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        for key in (
            "satisfied_approvals",
            "missing_approvals",
            "closure_authority_classes",
            "closure_runtime_action_keys",
            "missing_operator_action_slots",
            "missing_authority_action_slots",
            "missing_runtime_self_satisfiable_slots",
            "approval_evidence_slots",
            "evidence_capture_command_hints",
            "next_required_actions",
            "final_feature_blockers",
            "supervised_live_command_preview",
            "blocked_effects",
        ):
            payload[key] = list(payload[key])
        return payload


def build_pulse_final_evidence_gate_status(
    vault_root: str | Path,
    request_id: str | None = None,
    *,
    evidence_id: str | None = None,
    generated_at: str | None = None,
    bus_tasks: list[dict[str, Any]] | None = None,
) -> PulseFinalEvidenceGateStatus:
    """Build a read-only final gate packet for Pulse live-enqueue readiness."""
    vault = _vault_path(vault_root)
    timestamp = generated_at or now_utc()
    readiness = build_pulse_approval_readiness_summary(
        vault,
        request_id,
        evidence_id=evidence_id,
        generated_at=timestamp,
        bus_tasks=bus_tasks,
    )
    completion = build_pulse_completion_status(vault, generated_at=timestamp)
    missing_slots = _missing_operator_slots(readiness.approval_evidence_slots)
    authority_slots, runtime_self_satisfiable_slots = _partition_missing_slots(
        missing_slots
    )
    operator_action_required = bool(authority_slots)
    can_runtime_self_satisfy = bool(runtime_self_satisfiable_slots) and not authority_slots
    ready = readiness.ready_for_manual_enqueue
    runtime_action_keys = list(_unique_slot_values(runtime_self_satisfiable_slots, "approval_key"))
    if readiness.duplicate_found and "active_duplicate_work_fingerprint" not in runtime_action_keys:
        runtime_action_keys.append("active_duplicate_work_fingerprint")
    closure_status = _closure_status(
        ready,
        authority_slots,
        runtime_self_satisfiable_slots,
        duplicate_found=readiness.duplicate_found,
    )

    status = PulseFinalEvidenceGateStatus(
        generated_at=timestamp,
        gate_status=(
            PULSE_FINAL_GATE_STATUS_READY if ready else PULSE_FINAL_GATE_STATUS_BLOCKED
        ),
        request_id=readiness.request_id,
        evidence_id=readiness.evidence_id,
        candidate_id=readiness.candidate_id,
        candidate_kind=readiness.candidate_kind,
        recipient=readiness.recipient,
        work_fingerprint=readiness.work_fingerprint,
        completion_status=completion.overall_status,
        feature_done=completion.feature_done,
        backend_control_plane_done=completion.backend_control_plane_done,
        next_recommended_pass=completion.next_recommended_pass,
        readiness_status=readiness.readiness_status,
        ready_for_operator_gate_decision=readiness.ready_for_operator_gate_decision,
        ready_for_manual_enqueue=readiness.ready_for_manual_enqueue,
        ready_for_live_enqueue=ready,
        operator_action_required=operator_action_required,
        can_runtime_self_satisfy_remaining=can_runtime_self_satisfy,
        closure_status=closure_status,
        closure_authority_classes=_unique_slot_values(authority_slots, "authority_class"),
        closure_runtime_action_keys=tuple(runtime_action_keys),
        satisfied_approvals=readiness.satisfied_approvals,
        missing_approvals=readiness.missing_approvals,
        missing_operator_action_slots=missing_slots,
        missing_authority_action_slots=authority_slots,
        missing_runtime_self_satisfiable_slots=runtime_self_satisfiable_slots,
        approval_evidence_slots=readiness.approval_evidence_slots,
        evidence_capture_command_hints=readiness.evidence_capture_command_hints,
        next_required_actions=_operator_action_steps(missing_slots),
        final_feature_blockers=completion.blocked_reasons,
        supervised_live_command_preview=readiness.supervised_live_command_preview,
    )
    status.validate()
    return status
