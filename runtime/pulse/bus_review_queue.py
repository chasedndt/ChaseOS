"""Read-only queue preview for Pulse Agent Bus review contracts.

The queue preview aggregates existing Pulse candidate inspector rows into
non-mutating Agent Bus REVIEW request contracts. It is an in-memory view only:
no Agent Bus tasks, approval requests, derived queue files, candidate applies,
or canonical writes are created here.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.bus_review_contract import (
    PULSE_BUS_DEFAULT_RECIPIENT,
    PULSE_BUS_REVIEW_BLOCKED_EFFECTS,
    PulseAgentBusReviewRequestContract,
    build_agent_bus_review_request_contract,
)
from runtime.pulse.card_schema import now_utc
from runtime.pulse.candidate_inspector import (
    INSPECTOR_CANDIDATE_KINDS,
    PulseCandidateInspectorItem,
    build_candidate_inspector_snapshot,
)


PULSE_BUS_REVIEW_QUEUE_STATUS = "read_only"
PULSE_BUS_REVIEW_QUEUE_BLOCKED_EFFECTS = tuple(
    sorted(
        set(PULSE_BUS_REVIEW_BLOCKED_EFFECTS)
        | {
            "derived_queue_persistence",
            "approval_queue_persistence",
            "agent_bus_enqueue",
        }
    )
)


def _valid_limit(limit: int | None) -> int | None:
    if limit is None:
        return None
    if limit < 0:
        raise ValueError("limit must be zero or greater")
    return limit


def _candidate_items(items: list[PulseCandidateInspectorItem]) -> list[PulseCandidateInspectorItem]:
    return [item for item in items if item.item_kind != "review_decision"]


def _recipient_for_item(
    item: PulseCandidateInspectorItem,
    *,
    default_recipient: str,
    recipient_by_candidate_kind: dict[str, str] | None,
) -> str:
    if recipient_by_candidate_kind and item.candidate_kind in recipient_by_candidate_kind:
        return recipient_by_candidate_kind[item.candidate_kind or ""]
    return default_recipient


@dataclass
class PulseAgentBusReviewQueuePreview:
    """In-memory queue preview over Pulse Agent Bus review contracts."""

    generated_at: str = field(default_factory=now_utc)
    contracts: list[PulseAgentBusReviewRequestContract] = field(default_factory=list)
    source_log_paths: list[str] = field(default_factory=list)
    queue_status: str = PULSE_BUS_REVIEW_QUEUE_STATUS
    requested_by: str = "operator"
    default_recipient: str = PULSE_BUS_DEFAULT_RECIPIENT
    writes: list[str] = field(default_factory=list)
    bus_task_creation_allowed: bool = False
    bus_tasks_written: bool = False
    approval_requests_written: bool = False
    writes_performed: bool = False
    candidate_apply_allowed: bool = False
    live_runtime_dispatch_allowed: bool = False
    canonical_writeback_allowed: bool = False
    mutates_canonical_state: bool = False
    second_datastore_write_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    schedule_activation_allowed: bool = False
    blocked_effects: tuple[str, ...] = PULSE_BUS_REVIEW_QUEUE_BLOCKED_EFFECTS

    @property
    def contract_count(self) -> int:
        return len(self.contracts)

    @property
    def counts_by_candidate_kind(self) -> dict[str, int]:
        counts = {kind: 0 for kind in sorted(INSPECTOR_CANDIDATE_KINDS)}
        for contract in self.contracts:
            if contract.candidate_kind in counts:
                counts[contract.candidate_kind] += 1
        return counts

    @property
    def counts_by_recipient(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for contract in self.contracts:
            counts[contract.recipient] = counts.get(contract.recipient, 0) + 1
        return counts

    @property
    def agent_bus_task_previews(self) -> list[dict[str, Any]]:
        return [contract.to_task_preview() for contract in self.contracts]

    def validate(self) -> None:
        if self.queue_status != PULSE_BUS_REVIEW_QUEUE_STATUS:
            raise ValueError("Pulse bus review queue previews are read-only")
        if not self.default_recipient:
            raise ValueError("default_recipient is required")
        if self.writes:
            raise ValueError("Pulse bus review queue previews cannot declare writes")
        if self.bus_task_creation_allowed:
            raise ValueError("Pulse bus review queue previews cannot allow task creation")
        if self.bus_tasks_written:
            raise ValueError("Pulse bus review queue previews cannot write bus tasks")
        if self.approval_requests_written:
            raise ValueError("Pulse bus review queue previews cannot persist approval requests")
        if self.writes_performed:
            raise ValueError("Pulse bus review queue previews cannot perform writes")
        if self.candidate_apply_allowed:
            raise ValueError("Pulse bus review queue previews cannot apply candidates")
        if self.live_runtime_dispatch_allowed:
            raise ValueError("Pulse bus review queue previews cannot dispatch runtimes")
        if self.canonical_writeback_allowed:
            raise ValueError("Pulse bus review queue previews cannot allow canonical writeback")
        if self.mutates_canonical_state:
            raise ValueError("Pulse bus review queue previews cannot mutate canonical state")
        if self.second_datastore_write_allowed:
            raise ValueError("Pulse bus review queue previews cannot write a second datastore")
        if self.provider_or_connector_call_allowed:
            raise ValueError("Pulse bus review queue previews cannot call providers or connectors")
        if self.schedule_activation_allowed:
            raise ValueError("Pulse bus review queue previews cannot activate schedules")
        if set(self.blocked_effects) != set(PULSE_BUS_REVIEW_QUEUE_BLOCKED_EFFECTS):
            raise ValueError("Pulse bus review queue previews must declare blocked effects")
        for contract in self.contracts:
            contract.validate()
            if contract.bus_task_creation_allowed or contract.bus_task_written:
                raise ValueError("Pulse bus review queue contracts must not create bus tasks")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["contracts"] = [contract.to_dict() for contract in self.contracts]
        payload["blocked_effects"] = list(self.blocked_effects)
        payload["contract_count"] = self.contract_count
        payload["counts_by_candidate_kind"] = self.counts_by_candidate_kind
        payload["counts_by_recipient"] = self.counts_by_recipient
        payload["agent_bus_task_previews"] = self.agent_bus_task_previews
        return payload


def build_agent_bus_review_queue_preview(
    vault_root: str | Path,
    *,
    candidate_kinds: set[str] | None = None,
    candidate_id: str | None = None,
    default_recipient: str = PULSE_BUS_DEFAULT_RECIPIENT,
    recipient_by_candidate_kind: dict[str, str] | None = None,
    requested_by: str = "operator",
    priority: str = "normal",
    limit: int | None = None,
    created_at: str | None = None,
) -> PulseAgentBusReviewQueuePreview:
    """Build a read-only queue preview over current Pulse candidates."""
    valid_limit = _valid_limit(limit)
    snapshot = build_candidate_inspector_snapshot(
        vault_root,
        candidate_kinds=candidate_kinds,
        candidate_id=candidate_id,
    )
    items = _candidate_items(snapshot.items)
    if valid_limit is not None:
        items = items[:valid_limit]

    contracts = [
        build_agent_bus_review_request_contract(
            item,
            recipient=_recipient_for_item(
                item,
                default_recipient=default_recipient,
                recipient_by_candidate_kind=recipient_by_candidate_kind,
            ),
            requested_by=requested_by,
            priority=priority,
            created_at=created_at,
        )
        for item in items
    ]
    preview = PulseAgentBusReviewQueuePreview(
        generated_at=created_at or now_utc(),
        contracts=contracts,
        source_log_paths=list(snapshot.source_log_paths),
        requested_by=requested_by,
        default_recipient=default_recipient,
    )
    preview.validate()
    return preview
