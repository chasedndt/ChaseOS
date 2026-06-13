"""Operator/Gate approval UI contract for Pulse Agent Bus handoff.

This module turns a non-live handoff preflight into a presentable approval
contract for a future UI/operator surface. It is contract-only: no visual UI,
no approval grant, no Gate mutation, no Agent Bus task creation, no candidate
apply, and no canonical writeback.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.bus_enqueue_evidence import (
    PulseAgentBusEnqueueEvidenceRecord,
    load_agent_bus_enqueue_evidence_record_by_id,
)
from runtime.pulse.bus_handoff_preflight import (
    PULSE_BUS_HANDOFF_PREFLIGHT_STATUS_READY,
    PulseAgentBusHandoffPreflight,
    build_agent_bus_handoff_preflight,
)
from runtime.pulse.card_schema import now_utc


PULSE_OPERATOR_GATE_CONTRACT_STATUS_READY = "ready_for_operator_gate_decision"
PULSE_OPERATOR_GATE_CONTRACT_STATUS_BLOCKED = "blocked_preflight_not_ready"
PULSE_OPERATOR_GATE_CONTRACT_STATUSES = {
    PULSE_OPERATOR_GATE_CONTRACT_STATUS_READY,
    PULSE_OPERATOR_GATE_CONTRACT_STATUS_BLOCKED,
}
PULSE_OPERATOR_GATE_DECISIONS = (
    "approve_supervised_live_enqueue",
    "reject_handoff",
    "request_more_evidence",
    "refresh_handoff_preflight",
)
PULSE_OPERATOR_GATE_VISIBLE_EVIDENCE_FIELDS = (
    "request_id",
    "evidence_id",
    "handoff_status",
    "validation_status",
    "satisfied_approvals",
    "missing_approvals",
    "approval_evidence_slots",
    "duplicate_found",
    "active_duplicate_task_ids",
    "target_recipient",
    "target_active_task_count",
    "blocked_reasons",
)
PULSE_OPERATOR_GATE_BLOCKED_EFFECTS = (
    "agent_bus_task_write",
    "approval_grant",
    "approval_execution",
    "candidate_apply",
    "canonical_writeback",
    "gate_policy_mutation",
    "provider_or_connector_call",
    "runtime_dispatch",
    "schedule_activation",
    "visual_ui_render",
)


def _contract_id(preflight_id: str, generated_at: str) -> str:
    digest = hashlib.sha256(f"{preflight_id}|{generated_at}".encode("utf-8")).hexdigest()[:12]
    return f"pulse-operator-gate-contract-{digest}"


def _live_enqueue_command_preview(preflight: PulseAgentBusHandoffPreflight) -> tuple[str, ...]:
    if not preflight.ready_for_supervised_live_command or not preflight.evidence_id:
        return ()
    return (
        "python",
        "-m",
        "chaseos",
        "pulse",
        "enqueue-candidate",
        preflight.request_id,
        "--evidence-id",
        preflight.evidence_id,
        "--json",
    )


_APPROVAL_EVIDENCE_SLOT_DEFINITIONS = (
    (
        "operator_enqueue_approval",
        "Operator enqueue approval",
        "operator-approval-ref",
        "operator_enqueue_approval_present",
        "evidence_note",
        "--operator-approved --note <operator-approval-ref>",
        "operator_decision",
        False,
    ),
    (
        "gate_policy_defined",
        "Gate policy defined",
        "gate-policy-ref",
        "gate_policy_defined",
        "gate_policy_ref",
        "--gate-policy-defined --gate-policy-ref <gate-policy-ref>",
        "gate_policy",
        False,
    ),
    (
        "external_sender_allowance",
        "External sender allowance",
        "allowance-ref",
        "external_sender_allowance_present",
        "external_sender_allowance_ref",
        "--external-sender-allowance-present --external-sender-allowance-ref <allowance-ref>",
        "external_sender_policy",
        False,
    ),
    (
        "duplicate_work_fingerprint_review",
        "Duplicate work_fingerprint review",
        "duplicate-review-ref",
        "duplicate_work_fingerprint_reviewed",
        "duplicate_review_ref",
        "--duplicate-work-fingerprint-reviewed --duplicate-review-ref <duplicate-review-ref>",
        "queue_inspection",
        True,
    ),
)


def _approval_evidence_slots(
    request_id: str,
    evidence_record: PulseAgentBusEnqueueEvidenceRecord | None,
) -> tuple[dict[str, Any], ...]:
    slots: list[dict[str, Any]] = []
    for (
        approval_key,
        label,
        required_ref,
        flag_name,
        ref_name,
        capture_args,
        authority_class,
        runtime_self_satisfiable,
    ) in _APPROVAL_EVIDENCE_SLOT_DEFINITIONS:
        satisfied = bool(getattr(evidence_record, flag_name, False)) if evidence_record else False
        ref = getattr(evidence_record, ref_name, None) if evidence_record and satisfied else None
        slots.append(
            {
                "approval_key": approval_key,
                "label": label,
                "satisfied": satisfied,
                "required_ref": required_ref,
                "ref": ref or None,
                "ref_placeholder": f"<{required_ref}>",
                "requires_real_ref": True,
                "placeholder_ref_rejected": True,
                "authority_class": authority_class,
                "runtime_self_satisfiable": runtime_self_satisfiable,
                "capture_command": f"chaseos pulse enqueue-evidence {request_id} {capture_args}",
            }
        )
    return tuple(slots)


@dataclass(frozen=True)
class PulseOperatorGateDecisionControl:
    decision_type: str
    label: str
    enabled: bool
    requires_operator_confirmation: bool = True
    reason: str = ""

    def validate(self) -> None:
        if self.decision_type not in PULSE_OPERATOR_GATE_DECISIONS:
            raise ValueError("invalid operator/Gate decision type")
        if not self.label:
            raise ValueError("decision label is required")
        if self.enabled and not self.requires_operator_confirmation:
            raise ValueError("enabled decisions require operator confirmation")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class PulseOperatorGateApprovalUIContract:
    contract_id: str
    request_id: str
    preflight_id: str
    generated_at: str
    contract_status: str
    handoff_preflight: PulseAgentBusHandoffPreflight
    evidence_id: str | None = None
    allowed_decisions: tuple[str, ...] = PULSE_OPERATOR_GATE_DECISIONS
    visible_evidence_fields: tuple[str, ...] = PULSE_OPERATOR_GATE_VISIBLE_EVIDENCE_FIELDS
    decision_controls: tuple[PulseOperatorGateDecisionControl, ...] = field(default_factory=tuple)
    approval_evidence_slots: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    supervised_live_command_preview: tuple[str, ...] = field(default_factory=tuple)
    blocked_reasons: tuple[str, ...] = field(default_factory=tuple)
    safety_warnings: tuple[str, ...] = field(default_factory=tuple)
    ui_contract_only: bool = True
    visual_ui_built: bool = False
    persisted_contract: bool = False
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
    blocked_effects: tuple[str, ...] = PULSE_OPERATOR_GATE_BLOCKED_EFFECTS

    @property
    def ready_for_operator_gate_decision(self) -> bool:
        return self.contract_status == PULSE_OPERATOR_GATE_CONTRACT_STATUS_READY

    def validate(self) -> None:
        if not self.contract_id:
            raise ValueError("contract_id is required")
        if not self.request_id:
            raise ValueError("request_id is required")
        if not self.preflight_id:
            raise ValueError("preflight_id is required")
        if self.contract_status not in PULSE_OPERATOR_GATE_CONTRACT_STATUSES:
            raise ValueError("invalid operator/Gate contract status")
        self.handoff_preflight.validate()
        if set(self.allowed_decisions) != set(PULSE_OPERATOR_GATE_DECISIONS):
            raise ValueError("operator/Gate contract must declare allowed decisions")
        if set(self.visible_evidence_fields) != set(PULSE_OPERATOR_GATE_VISIBLE_EVIDENCE_FIELDS):
            raise ValueError("operator/Gate contract must declare visible evidence fields")
        for control in self.decision_controls:
            control.validate()
        slot_keys = {str(slot.get("approval_key") or "") for slot in self.approval_evidence_slots}
        expected_slot_keys = {item[0] for item in _APPROVAL_EVIDENCE_SLOT_DEFINITIONS}
        if slot_keys != expected_slot_keys:
            raise ValueError("operator/Gate contract must expose approval evidence slots")
        for slot in self.approval_evidence_slots:
            if "satisfied" not in slot or "capture_command" not in slot:
                raise ValueError("approval evidence slots must expose status and capture command")
        if self.contract_status == PULSE_OPERATOR_GATE_CONTRACT_STATUS_READY:
            if self.blocked_reasons:
                raise ValueError("ready operator/Gate contracts cannot list blocked reasons")
            if self.handoff_preflight.handoff_status != PULSE_BUS_HANDOFF_PREFLIGHT_STATUS_READY:
                raise ValueError("ready operator/Gate contracts require ready handoff preflight")
            if not self.supervised_live_command_preview:
                raise ValueError("ready operator/Gate contracts require command preview")
        else:
            if not self.blocked_reasons:
                raise ValueError("blocked operator/Gate contracts must list blocked reasons")
            if self.supervised_live_command_preview:
                raise ValueError("blocked operator/Gate contracts cannot expose live command preview")
        if not self.ui_contract_only:
            raise ValueError("operator/Gate approval UI contracts must remain contract-only")
        if self.visual_ui_built:
            raise ValueError("operator/Gate approval UI contract cannot claim visual UI")
        if self.persisted_contract:
            raise ValueError("operator/Gate approval UI contracts are not persisted in this pass")
        if self.approval_granted:
            raise ValueError("operator/Gate approval UI contracts cannot grant approval")
        if self.approval_executed:
            raise ValueError("operator/Gate approval UI contracts cannot execute approval")
        if self.gate_policy_mutated:
            raise ValueError("operator/Gate approval UI contracts cannot mutate Gate policy")
        if self.live_agent_bus_handoff_allowed:
            raise ValueError("operator/Gate approval UI contracts cannot allow live handoff")
        if self.agent_bus_task_written:
            raise ValueError("operator/Gate approval UI contracts cannot write Agent Bus tasks")
        if self.runtime_dispatch_allowed:
            raise ValueError("operator/Gate approval UI contracts cannot dispatch runtimes")
        if self.review_response_ingest_allowed:
            raise ValueError("operator/Gate approval UI contracts cannot ingest review responses")
        if self.candidate_apply_allowed:
            raise ValueError("operator/Gate approval UI contracts cannot apply candidates")
        if self.canonical_writeback_allowed:
            raise ValueError("operator/Gate approval UI contracts cannot allow canonical writeback")
        if self.mutates_canonical_state:
            raise ValueError("operator/Gate approval UI contracts cannot mutate canonical state")
        if self.second_datastore_write_allowed:
            raise ValueError("operator/Gate approval UI contracts cannot write a second datastore")
        if self.provider_or_connector_call_allowed:
            raise ValueError("operator/Gate approval UI contracts cannot call providers or connectors")
        if self.schedule_activation_allowed:
            raise ValueError("operator/Gate approval UI contracts cannot activate schedules")
        if set(self.blocked_effects) != set(PULSE_OPERATOR_GATE_BLOCKED_EFFECTS):
            raise ValueError("operator/Gate approval UI contracts must declare blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "contract_id": self.contract_id,
            "request_id": self.request_id,
            "preflight_id": self.preflight_id,
            "generated_at": self.generated_at,
            "contract_status": self.contract_status,
            "ready_for_operator_gate_decision": self.ready_for_operator_gate_decision,
            "evidence_id": self.evidence_id,
            "allowed_decisions": list(self.allowed_decisions),
            "visible_evidence_fields": list(self.visible_evidence_fields),
            "decision_controls": [control.to_dict() for control in self.decision_controls],
            "approval_evidence_slots": [dict(slot) for slot in self.approval_evidence_slots],
            "supervised_live_command_preview": list(self.supervised_live_command_preview),
            "blocked_reasons": list(self.blocked_reasons),
            "safety_warnings": list(self.safety_warnings),
            "handoff_preflight": self.handoff_preflight.to_dict(),
            "ui_contract_only": self.ui_contract_only,
            "visual_ui_built": self.visual_ui_built,
            "persisted_contract": self.persisted_contract,
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


def _decision_controls(ready: bool) -> tuple[PulseOperatorGateDecisionControl, ...]:
    return (
        PulseOperatorGateDecisionControl(
            decision_type="approve_supervised_live_enqueue",
            label="Approve supervised live enqueue",
            enabled=ready,
            reason="enabled only when handoff preflight is ready",
        ),
        PulseOperatorGateDecisionControl(
            decision_type="reject_handoff",
            label="Reject handoff",
            enabled=True,
            reason="operator may reject a ready or blocked handoff",
        ),
        PulseOperatorGateDecisionControl(
            decision_type="request_more_evidence",
            label="Request more evidence",
            enabled=True,
            reason="operator may request more evidence before any live command",
        ),
        PulseOperatorGateDecisionControl(
            decision_type="refresh_handoff_preflight",
            label="Refresh handoff preflight",
            enabled=True,
            reason="operator may refresh duplicate and target posture",
        ),
    )


def build_operator_gate_approval_ui_contract(
    vault_root: str | Path,
    request_id: str,
    *,
    evidence_id: str | None = None,
    generated_at: str | None = None,
    bus_tasks: list[dict[str, Any]] | None = None,
) -> PulseOperatorGateApprovalUIContract:
    """Build a contract-only operator/Gate approval UI packet."""
    timestamp = generated_at or now_utc()
    preflight = build_agent_bus_handoff_preflight(
        vault_root,
        request_id,
        evidence_id=evidence_id,
        checked_at=timestamp,
        bus_tasks=bus_tasks,
    )
    evidence_record = (
        load_agent_bus_enqueue_evidence_record_by_id(vault_root, preflight.evidence_id)
        if preflight.evidence_id
        else None
    )
    ready = preflight.ready_for_supervised_live_command
    status = (
        PULSE_OPERATOR_GATE_CONTRACT_STATUS_READY
        if ready
        else PULSE_OPERATOR_GATE_CONTRACT_STATUS_BLOCKED
    )
    warnings = (
        "This contract is not an approval grant.",
        "Run the supervised live command only after explicit operator approval.",
        "The contract does not apply candidates or write canonical state.",
    )
    contract = PulseOperatorGateApprovalUIContract(
        contract_id=_contract_id(preflight.preflight_id, timestamp),
        request_id=preflight.request_id,
        preflight_id=preflight.preflight_id,
        generated_at=timestamp,
        contract_status=status,
        handoff_preflight=preflight,
        evidence_id=preflight.evidence_id,
        decision_controls=_decision_controls(ready),
        approval_evidence_slots=_approval_evidence_slots(preflight.request_id, evidence_record),
        supervised_live_command_preview=_live_enqueue_command_preview(preflight),
        blocked_reasons=tuple(preflight.blocked_reasons),
        safety_warnings=warnings,
    )
    contract.validate()
    return contract
