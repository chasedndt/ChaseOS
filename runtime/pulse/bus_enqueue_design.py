"""Design-only Pulse Agent Bus enqueue preflight contracts.

This module sits one step above the read-only Pulse Agent Bus review queue. It
describes the approval and duplicate-review facts required before a future pass
may hand a Pulse REVIEW contract to the live Agent Bus. It deliberately stays
schema-only: no bus backend import, no persisted approval request, no runtime
dispatch, and no candidate apply effect.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.bus_review_contract import (
    PULSE_BUS_DEFAULT_SENDER,
    PULSE_BUS_REVIEW_INTENT,
    PulseAgentBusReviewRequestContract,
    build_agent_bus_review_request_contract_for_candidate,
)
from runtime.pulse.bus_review_queue import (
    PULSE_BUS_REVIEW_QUEUE_BLOCKED_EFFECTS,
    PulseAgentBusReviewQueuePreview,
    build_agent_bus_review_queue_preview,
)
from runtime.pulse.card_schema import now_utc


PULSE_BUS_ENQUEUE_DESIGN_STATUS = "design_only"
PULSE_BUS_ENQUEUE_PREFLIGHT_STATUS = "ready_for_operator_approval"
PULSE_BUS_ENQUEUE_PLAN_STATUS = "read_only"
PULSE_BUS_ALLOWED_REVIEW_RECIPIENTS = ("Hermes", "OpenClaw")
PULSE_BUS_ENQUEUE_REQUIRED_APPROVALS = (
    "operator_enqueue_approval",
    "gate_policy_defined",
    "external_sender_allowance",
    "duplicate_work_fingerprint_review",
)
PULSE_BUS_ENQUEUE_BLOCKED_EFFECTS = tuple(
    sorted(
        set(PULSE_BUS_REVIEW_QUEUE_BLOCKED_EFFECTS)
        | {
            "agent_bus_task_write",
            "approval_request_persistence",
            "candidate_apply",
            "live_enqueue",
            "review_response_ingest",
            "runtime_task_claim",
        }
    )
)


def _clean_text(value: str | None, fallback: str) -> str:
    cleaned = " ".join(str(value or "").split())
    return cleaned or fallback


@dataclass(frozen=True)
class PulseAgentBusEnqueueDesign:
    """Static policy boundary for a future operator-approved enqueue surface."""

    design_status: str = PULSE_BUS_ENQUEUE_DESIGN_STATUS
    allowed_review_recipients: tuple[str, ...] = PULSE_BUS_ALLOWED_REVIEW_RECIPIENTS
    required_approvals: tuple[str, ...] = PULSE_BUS_ENQUEUE_REQUIRED_APPROVALS
    allowed: bool = False
    approval_required: bool = True
    live_enqueue_allowed: bool = False
    agent_bus_write_allowed: bool = False
    approval_request_write_allowed: bool = False
    writes_performed: bool = False
    candidate_apply_allowed: bool = False
    review_response_ingest_allowed: bool = False
    canonical_writeback_allowed: bool = False
    mutates_canonical_state: bool = False
    second_datastore_write_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    schedule_activation_allowed: bool = False
    blocked_effects: tuple[str, ...] = PULSE_BUS_ENQUEUE_BLOCKED_EFFECTS

    def validate(self) -> None:
        if self.design_status != PULSE_BUS_ENQUEUE_DESIGN_STATUS:
            raise ValueError("Pulse Agent Bus enqueue design must remain design_only")
        if not self.allowed_review_recipients:
            raise ValueError("At least one bounded review recipient must be declared")
        if set(self.required_approvals) != set(PULSE_BUS_ENQUEUE_REQUIRED_APPROVALS):
            raise ValueError("Pulse Agent Bus enqueue design must declare required approvals")
        if self.allowed:
            raise ValueError("Pulse Agent Bus enqueue design cannot allow enqueue")
        if not self.approval_required:
            raise ValueError("Pulse Agent Bus enqueue design requires operator approval")
        if self.live_enqueue_allowed:
            raise ValueError("Pulse Agent Bus enqueue design cannot allow live enqueue")
        if self.agent_bus_write_allowed:
            raise ValueError("Pulse Agent Bus enqueue design cannot allow bus writes")
        if self.approval_request_write_allowed:
            raise ValueError("Pulse Agent Bus enqueue design cannot persist approval requests")
        if self.writes_performed:
            raise ValueError("Pulse Agent Bus enqueue design cannot perform writes")
        if self.candidate_apply_allowed:
            raise ValueError("Pulse Agent Bus enqueue design cannot apply candidates")
        if self.review_response_ingest_allowed:
            raise ValueError("Pulse Agent Bus enqueue design cannot ingest review responses")
        if self.canonical_writeback_allowed:
            raise ValueError("Pulse Agent Bus enqueue design cannot allow canonical writeback")
        if self.mutates_canonical_state:
            raise ValueError("Pulse Agent Bus enqueue design cannot mutate canonical state")
        if self.second_datastore_write_allowed:
            raise ValueError("Pulse Agent Bus enqueue design cannot write a second datastore")
        if self.provider_or_connector_call_allowed:
            raise ValueError("Pulse Agent Bus enqueue design cannot call providers or connectors")
        if self.schedule_activation_allowed:
            raise ValueError("Pulse Agent Bus enqueue design cannot activate schedules")
        if set(self.blocked_effects) != set(PULSE_BUS_ENQUEUE_BLOCKED_EFFECTS):
            raise ValueError("Pulse Agent Bus enqueue design must declare blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["allowed_review_recipients"] = list(self.allowed_review_recipients)
        payload["required_approvals"] = list(self.required_approvals)
        payload["blocked_effects"] = list(self.blocked_effects)
        return payload


@dataclass
class PulseAgentBusEnqueuePreflight:
    """One-contract preview for a future, separately approved bus handoff."""

    preflight_id: str
    contract_id: str
    candidate_id: str
    candidate_kind: str
    sender: str
    recipient: str
    intent: str
    priority: str
    request: str
    expected_output: str
    notes: str
    work_fingerprint: str
    created_at: str = field(default_factory=now_utc)
    requested_by: str = "operator"
    preflight_status: str = PULSE_BUS_ENQUEUE_PREFLIGHT_STATUS
    required_approvals: tuple[str, ...] = PULSE_BUS_ENQUEUE_REQUIRED_APPROVALS
    allowed_review_recipients: tuple[str, ...] = PULSE_BUS_ALLOWED_REVIEW_RECIPIENTS
    source_log_path: str | None = None
    source_deck_path: str | None = None
    source_card_id: str | None = None
    target_ref: str | None = None
    runtime_id: str | None = None
    artifacts: tuple[str, ...] = field(default_factory=tuple)
    allow_external_sender_required: bool = True
    duplicate_policy: str = "work_fingerprint_required"
    duplicate_check_performed: bool = False
    enqueue_allowed: bool = False
    agent_bus_task_written: bool = False
    approval_request_written: bool = False
    writes_performed: bool = False
    live_runtime_dispatch_allowed: bool = False
    candidate_apply_allowed: bool = False
    review_response_ingest_allowed: bool = False
    canonical_writeback_allowed: bool = False
    mutates_canonical_state: bool = False
    second_datastore_write_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    schedule_activation_allowed: bool = False
    blocked_effects: tuple[str, ...] = PULSE_BUS_ENQUEUE_BLOCKED_EFFECTS

    def validate(self) -> None:
        if not self.preflight_id:
            raise ValueError("preflight_id is required")
        if not self.contract_id:
            raise ValueError("contract_id is required")
        if not self.candidate_id:
            raise ValueError("candidate_id is required")
        if not self.candidate_kind:
            raise ValueError("candidate_kind is required")
        if self.sender != PULSE_BUS_DEFAULT_SENDER:
            raise ValueError("Pulse Agent Bus enqueue preflights must use Operator sender")
        if self.recipient not in self.allowed_review_recipients:
            raise ValueError("recipient is not an allowed Pulse review recipient")
        if self.intent != PULSE_BUS_REVIEW_INTENT:
            raise ValueError("Pulse Agent Bus enqueue preflights must use REVIEW intent")
        if self.priority not in {"low", "normal", "high"}:
            raise ValueError("Pulse Agent Bus enqueue preflight priority must be low, normal, or high")
        if not self.request:
            raise ValueError("request is required")
        if not self.expected_output:
            raise ValueError("expected_output is required")
        if not self.work_fingerprint:
            raise ValueError("work_fingerprint is required for duplicate review")
        if self.preflight_status != PULSE_BUS_ENQUEUE_PREFLIGHT_STATUS:
            raise ValueError("Pulse Agent Bus enqueue preflights must remain ready_for_operator_approval")
        if set(self.required_approvals) != set(PULSE_BUS_ENQUEUE_REQUIRED_APPROVALS):
            raise ValueError("Pulse Agent Bus enqueue preflights must declare required approvals")
        if not self.allow_external_sender_required:
            raise ValueError("Operator sender requires explicit external-sender allowance")
        if self.duplicate_policy != "work_fingerprint_required":
            raise ValueError("Pulse Agent Bus enqueue preflights require work-fingerprint duplicate policy")
        if self.duplicate_check_performed:
            raise ValueError("Pulse Agent Bus enqueue preflights cannot claim live duplicate checks")
        if self.enqueue_allowed:
            raise ValueError("Pulse Agent Bus enqueue preflights cannot allow enqueue")
        if self.agent_bus_task_written:
            raise ValueError("Pulse Agent Bus enqueue preflights cannot write bus tasks")
        if self.approval_request_written:
            raise ValueError("Pulse Agent Bus enqueue preflights cannot persist approval requests")
        if self.writes_performed:
            raise ValueError("Pulse Agent Bus enqueue preflights cannot perform writes")
        if self.live_runtime_dispatch_allowed:
            raise ValueError("Pulse Agent Bus enqueue preflights cannot dispatch runtimes")
        if self.candidate_apply_allowed:
            raise ValueError("Pulse Agent Bus enqueue preflights cannot apply candidates")
        if self.review_response_ingest_allowed:
            raise ValueError("Pulse Agent Bus enqueue preflights cannot ingest review responses")
        if self.canonical_writeback_allowed:
            raise ValueError("Pulse Agent Bus enqueue preflights cannot allow canonical writeback")
        if self.mutates_canonical_state:
            raise ValueError("Pulse Agent Bus enqueue preflights cannot mutate canonical state")
        if self.second_datastore_write_allowed:
            raise ValueError("Pulse Agent Bus enqueue preflights cannot write a second datastore")
        if self.provider_or_connector_call_allowed:
            raise ValueError("Pulse Agent Bus enqueue preflights cannot call providers or connectors")
        if self.schedule_activation_allowed:
            raise ValueError("Pulse Agent Bus enqueue preflights cannot activate schedules")
        if set(self.blocked_effects) != set(PULSE_BUS_ENQUEUE_BLOCKED_EFFECTS):
            raise ValueError("Pulse Agent Bus enqueue preflights must declare blocked effects")

    def to_task_payload_preview(self) -> dict[str, Any]:
        """Return the task payload a future approved command could hand off."""
        self.validate()
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "intent": self.intent,
            "priority": self.priority,
            "request": self.request,
            "expected_output": self.expected_output,
            "notes": self.notes,
            "work_fingerprint": self.work_fingerprint,
            "allow_external_sender_required": self.allow_external_sender_required,
            "required_approvals": list(self.required_approvals),
            "enqueue_allowed": self.enqueue_allowed,
            "agent_bus_task_written": self.agent_bus_task_written,
        }

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["required_approvals"] = list(self.required_approvals)
        payload["allowed_review_recipients"] = list(self.allowed_review_recipients)
        payload["artifacts"] = list(self.artifacts)
        payload["blocked_effects"] = list(self.blocked_effects)
        payload["task_payload_preview"] = self.to_task_payload_preview()
        return payload


@dataclass
class PulseAgentBusEnqueuePlan:
    """Read-only plan over enqueue preflights from a queue preview."""

    generated_at: str = field(default_factory=now_utc)
    preflights: list[PulseAgentBusEnqueuePreflight] = field(default_factory=list)
    source_log_paths: list[str] = field(default_factory=list)
    plan_status: str = PULSE_BUS_ENQUEUE_PLAN_STATUS
    requested_by: str = "operator"
    writes: list[str] = field(default_factory=list)
    enqueue_allowed: bool = False
    agent_bus_tasks_written: bool = False
    approval_requests_written: bool = False
    writes_performed: bool = False
    candidate_apply_allowed: bool = False
    review_response_ingest_allowed: bool = False
    live_runtime_dispatch_allowed: bool = False
    canonical_writeback_allowed: bool = False
    mutates_canonical_state: bool = False
    second_datastore_write_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    schedule_activation_allowed: bool = False
    blocked_effects: tuple[str, ...] = PULSE_BUS_ENQUEUE_BLOCKED_EFFECTS

    @property
    def preflight_count(self) -> int:
        return len(self.preflights)

    @property
    def counts_by_recipient(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for preflight in self.preflights:
            counts[preflight.recipient] = counts.get(preflight.recipient, 0) + 1
        return counts

    @property
    def task_payload_previews(self) -> list[dict[str, Any]]:
        return [preflight.to_task_payload_preview() for preflight in self.preflights]

    def validate(self) -> None:
        if self.plan_status != PULSE_BUS_ENQUEUE_PLAN_STATUS:
            raise ValueError("Pulse Agent Bus enqueue plans must remain read_only")
        if self.writes:
            raise ValueError("Pulse Agent Bus enqueue plans cannot declare writes")
        if self.enqueue_allowed:
            raise ValueError("Pulse Agent Bus enqueue plans cannot allow enqueue")
        if self.agent_bus_tasks_written:
            raise ValueError("Pulse Agent Bus enqueue plans cannot write bus tasks")
        if self.approval_requests_written:
            raise ValueError("Pulse Agent Bus enqueue plans cannot persist approval requests")
        if self.writes_performed:
            raise ValueError("Pulse Agent Bus enqueue plans cannot perform writes")
        if self.candidate_apply_allowed:
            raise ValueError("Pulse Agent Bus enqueue plans cannot apply candidates")
        if self.review_response_ingest_allowed:
            raise ValueError("Pulse Agent Bus enqueue plans cannot ingest review responses")
        if self.live_runtime_dispatch_allowed:
            raise ValueError("Pulse Agent Bus enqueue plans cannot dispatch runtimes")
        if self.canonical_writeback_allowed:
            raise ValueError("Pulse Agent Bus enqueue plans cannot allow canonical writeback")
        if self.mutates_canonical_state:
            raise ValueError("Pulse Agent Bus enqueue plans cannot mutate canonical state")
        if self.second_datastore_write_allowed:
            raise ValueError("Pulse Agent Bus enqueue plans cannot write a second datastore")
        if self.provider_or_connector_call_allowed:
            raise ValueError("Pulse Agent Bus enqueue plans cannot call providers or connectors")
        if self.schedule_activation_allowed:
            raise ValueError("Pulse Agent Bus enqueue plans cannot activate schedules")
        if set(self.blocked_effects) != set(PULSE_BUS_ENQUEUE_BLOCKED_EFFECTS):
            raise ValueError("Pulse Agent Bus enqueue plans must declare blocked effects")
        for preflight in self.preflights:
            preflight.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["preflights"] = [preflight.to_dict() for preflight in self.preflights]
        payload["blocked_effects"] = list(self.blocked_effects)
        payload["preflight_count"] = self.preflight_count
        payload["counts_by_recipient"] = self.counts_by_recipient
        payload["task_payload_previews"] = self.task_payload_previews
        return payload


def build_agent_bus_enqueue_preflight(
    contract: PulseAgentBusReviewRequestContract,
    *,
    requested_by: str = "operator",
    created_at: str | None = None,
    allowed_review_recipients: tuple[str, ...] = PULSE_BUS_ALLOWED_REVIEW_RECIPIENTS,
) -> PulseAgentBusEnqueuePreflight:
    """Build a non-writing enqueue preflight from one review contract."""
    contract.validate()
    clean_requested_by = _clean_text(requested_by, "operator")
    preflight = PulseAgentBusEnqueuePreflight(
        preflight_id=f"pulse-bus-enqueue-preflight-{contract.contract_id}",
        contract_id=contract.contract_id,
        candidate_id=contract.candidate_id,
        candidate_kind=contract.candidate_kind,
        sender=contract.sender,
        recipient=contract.recipient,
        intent=contract.intent,
        priority=contract.priority,
        request=contract.request,
        expected_output=contract.expected_output,
        notes=(
            f"{contract.notes} Enqueue preflight only: operator approval, Gate "
            "policy, external-sender allowance, and duplicate fingerprint review "
            "are required before any live task handoff."
        ),
        work_fingerprint=contract.work_fingerprint or "",
        created_at=created_at or now_utc(),
        requested_by=clean_requested_by,
        allowed_review_recipients=allowed_review_recipients,
        source_log_path=contract.source_log_path,
        source_deck_path=contract.source_deck_path,
        source_card_id=contract.source_card_id,
        target_ref=contract.target_ref,
        runtime_id=contract.runtime_id,
        artifacts=contract.artifacts,
    )
    preflight.validate()
    return preflight


def build_agent_bus_enqueue_preflight_for_candidate(
    vault_root: str | Path,
    candidate_id: str,
    *,
    recipient: str = "Hermes",
    requested_by: str = "operator",
    priority: str = "normal",
    created_at: str | None = None,
) -> PulseAgentBusEnqueuePreflight:
    """Load a Pulse candidate read-only and build its enqueue preflight."""
    contract = build_agent_bus_review_request_contract_for_candidate(
        vault_root,
        candidate_id,
        recipient=recipient,
        requested_by=requested_by,
        priority=priority,
        created_at=created_at,
    )
    return build_agent_bus_enqueue_preflight(
        contract,
        requested_by=requested_by,
        created_at=created_at,
    )


def build_agent_bus_enqueue_plan(
    vault_root: str | Path,
    *,
    candidate_kinds: set[str] | None = None,
    candidate_id: str | None = None,
    default_recipient: str = "Hermes",
    recipient_by_candidate_kind: dict[str, str] | None = None,
    requested_by: str = "operator",
    priority: str = "normal",
    limit: int | None = None,
    created_at: str | None = None,
) -> PulseAgentBusEnqueuePlan:
    """Build a read-only enqueue plan from current Pulse review queue state."""
    queue_preview: PulseAgentBusReviewQueuePreview = build_agent_bus_review_queue_preview(
        vault_root,
        candidate_kinds=candidate_kinds,
        candidate_id=candidate_id,
        default_recipient=default_recipient,
        recipient_by_candidate_kind=recipient_by_candidate_kind,
        requested_by=requested_by,
        priority=priority,
        limit=limit,
        created_at=created_at,
    )
    preflights = [
        build_agent_bus_enqueue_preflight(
            contract,
            requested_by=requested_by,
            created_at=created_at,
        )
        for contract in queue_preview.contracts
    ]
    plan = PulseAgentBusEnqueuePlan(
        generated_at=created_at or now_utc(),
        preflights=preflights,
        source_log_paths=list(queue_preview.source_log_paths),
        requested_by=requested_by,
    )
    plan.validate()
    return plan
