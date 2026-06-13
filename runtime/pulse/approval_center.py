"""Read-only ChaseOS Pulse approval center readiness surface.

This module aggregates the existing Pulse candidate, feedback review, approval
request, approval-readiness, final-evidence-gate, deck inventory, and hardening
surfaces into one product-grade readiness packet. It does not grant approvals,
persist review decisions, apply candidates, write Agent Bus tasks, dispatch
runtimes, activate schedules, call providers/connectors, approve memory, or
mutate canonical state.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.approval_readiness_summary import (
    build_pulse_approval_readiness_summary,
)
from runtime.pulse.bus_enqueue_approval_request import (
    load_agent_bus_enqueue_approval_requests,
)
from runtime.pulse.candidate_inspector import build_candidate_inspector_snapshot
from runtime.pulse.card_schema import now_utc
from runtime.pulse.feedback_review_queue import build_feedback_review_queue
from runtime.pulse.final_evidence_gate import build_pulse_final_evidence_gate_status
from runtime.pulse.multi_audience_decks import build_pulse_deck_inventory


APPROVAL_CENTER_STATUS_READY = "ready_for_operator_review"
APPROVAL_CENTER_STATUS_EMPTY = "no_review_items"
APPROVAL_CENTER_STATUS_BLOCKED = "blocked_or_waiting_for_evidence"
APPROVAL_CENTER_STATUSES = {
    APPROVAL_CENTER_STATUS_READY,
    APPROVAL_CENTER_STATUS_EMPTY,
    APPROVAL_CENTER_STATUS_BLOCKED,
}

APPROVAL_CENTER_LANES = {
    "pulse_decks",
    "feedback_candidates",
    "memory_candidates",
    "execution_repair_candidates",
    "review_decisions",
    "agent_bus_approval_requests",
    "final_evidence_gate",
    "post_completion_hardening",
}

APPROVAL_CENTER_BLOCKED_EFFECTS = (
    "agent_bus_task_write",
    "approval_grant",
    "approval_execution",
    "candidate_apply",
    "canonical_writeback",
    "evidence_write",
    "feedback_application",
    "gate_policy_mutation",
    "memory_approval",
    "project_file_mutation",
    "provider_or_connector_call",
    "review_decision_write",
    "runtime_dispatch",
    "schedule_activation",
    "second_datastore_write",
)


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _read_hardening_status(vault: Path) -> tuple[str, int, int, int]:
    """Return a non-writing hardening lane signal.

    The full post-completion hardening report is a separate CLI surface. This
    approval-center packet must be safe against sparse temporary vaults, so it
    only checks whether the hardening module is present in the selected repo.
    """

    module_path = vault / "runtime" / "pulse" / "post_completion_hardening.py"
    if module_path.exists():
        return "available_read_only", 1, 1, 0
    return "not_configured", 0, 0, 0


@dataclass(frozen=True)
class PulseApprovalCenterLane:
    lane_id: str
    label: str
    item_count: int
    pending_count: int = 0
    ready_count: int = 0
    blocked_count: int = 0
    status: str = "read_only"
    source_refs: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.lane_id not in APPROVAL_CENTER_LANES:
            raise ValueError("invalid approval center lane_id")
        if not self.label:
            raise ValueError("approval center lane label is required")
        for value in (self.item_count, self.pending_count, self.ready_count, self.blocked_count):
            if value < 0:
                raise ValueError("approval center lane counts cannot be negative")
        if not self.status:
            raise ValueError("approval center lane status is required")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["source_refs"] = list(self.source_refs)
        return payload


@dataclass(frozen=True)
class PulseApprovalCenterActionPreview:
    action_id: str
    lane_id: str
    label: str
    action_type: str
    target_ref: str | None = None
    command_preview: tuple[str, ...] = ()
    enabled_for_display: bool = True
    execution_allowed: bool = False
    requires_operator_approval: bool = True
    writes_artifact: bool = False
    mutates_canonical_state: bool = False

    def validate(self) -> None:
        if not self.action_id:
            raise ValueError("approval center action_id is required")
        if self.lane_id not in APPROVAL_CENTER_LANES:
            raise ValueError("invalid approval center action lane")
        if not self.label:
            raise ValueError("approval center action label is required")
        if not self.action_type:
            raise ValueError("approval center action_type is required")
        if self.execution_allowed:
            raise ValueError("approval center action previews cannot allow execution")
        if self.writes_artifact:
            raise ValueError("approval center action previews cannot write artifacts")
        if self.mutates_canonical_state:
            raise ValueError("approval center action previews cannot mutate canonical state")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["command_preview"] = list(self.command_preview)
        return payload


@dataclass(frozen=True)
class PulseApprovalCenterReadinessSurface:
    generated_at: str
    approval_center_status: str
    lanes: tuple[PulseApprovalCenterLane, ...]
    action_previews: tuple[PulseApprovalCenterActionPreview, ...]
    source_refs: tuple[str, ...]
    latest_request_id: str | None = None
    approval_readiness_status: str | None = None
    final_gate_status: str | None = None
    hardening_status: str | None = None
    deck_count: int = 0
    candidate_item_count: int = 0
    pending_feedback_count: int = 0
    review_decision_count: int = 0
    approval_request_count: int = 0
    missing_approval_keys: tuple[str, ...] = ()
    read_only: bool = True
    local_only: bool = True
    writes_status_artifact: bool = False
    writes_review_decisions: bool = False
    writes_feedback_candidates: bool = False
    applies_candidates: bool = False
    grants_approvals: bool = False
    executes_approval: bool = False
    agent_bus_task_write_allowed: bool = False
    runtime_dispatch_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    schedule_activation_allowed: bool = False
    memory_approval_allowed: bool = False
    canonical_writeback_allowed: bool = False
    mutates_canonical_state: bool = False
    second_datastore_created: bool = False
    rd_workbook_update_allowed: bool = False
    blocked_effects: tuple[str, ...] = APPROVAL_CENTER_BLOCKED_EFFECTS

    @property
    def lane_count(self) -> int:
        return len(self.lanes)

    @property
    def action_count(self) -> int:
        return len(self.action_previews)

    def validate(self) -> None:
        if not self.generated_at:
            raise ValueError("generated_at is required")
        if self.approval_center_status not in APPROVAL_CENTER_STATUSES:
            raise ValueError("invalid approval center status")
        lane_ids = {lane.lane_id for lane in self.lanes}
        if lane_ids != APPROVAL_CENTER_LANES:
            raise ValueError("approval center surface must expose all lanes")
        for lane in self.lanes:
            lane.validate()
        for action in self.action_previews:
            action.validate()
        if self.deck_count < 0 or self.candidate_item_count < 0:
            raise ValueError("approval center counts cannot be negative")
        if self.pending_feedback_count < 0 or self.review_decision_count < 0:
            raise ValueError("approval center counts cannot be negative")
        if self.approval_request_count < 0:
            raise ValueError("approval request count cannot be negative")
        if self.approval_request_count and not self.latest_request_id:
            raise ValueError("latest_request_id is required when approval requests exist")
        if not self.read_only:
            raise ValueError("approval center surface must remain read-only")
        if not self.local_only:
            raise ValueError("approval center surface must remain local-only")
        if self.writes_status_artifact:
            raise ValueError("approval center cannot write status artifacts")
        if self.writes_review_decisions:
            raise ValueError("approval center cannot write review decisions")
        if self.writes_feedback_candidates:
            raise ValueError("approval center cannot write feedback candidates")
        if self.applies_candidates:
            raise ValueError("approval center cannot apply candidates")
        if self.grants_approvals or self.executes_approval:
            raise ValueError("approval center cannot grant or execute approvals")
        if self.agent_bus_task_write_allowed:
            raise ValueError("approval center cannot write Agent Bus tasks")
        if self.runtime_dispatch_allowed:
            raise ValueError("approval center cannot dispatch runtimes")
        if self.provider_or_connector_call_allowed:
            raise ValueError("approval center cannot call providers/connectors")
        if self.schedule_activation_allowed:
            raise ValueError("approval center cannot activate schedules")
        if self.memory_approval_allowed:
            raise ValueError("approval center cannot approve memory")
        if self.canonical_writeback_allowed:
            raise ValueError("approval center cannot allow canonical writeback")
        if self.mutates_canonical_state:
            raise ValueError("approval center cannot mutate canonical state")
        if self.second_datastore_created:
            raise ValueError("approval center cannot create a second datastore")
        if self.rd_workbook_update_allowed:
            raise ValueError("approval center cannot update the R&D workbook")
        if set(self.blocked_effects) != set(APPROVAL_CENTER_BLOCKED_EFFECTS):
            raise ValueError("approval center must declare blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "approval_center_status": self.approval_center_status,
            "lane_count": self.lane_count,
            "lanes": [lane.to_dict() for lane in self.lanes],
            "action_count": self.action_count,
            "action_previews": [action.to_dict() for action in self.action_previews],
            "source_refs": list(self.source_refs),
            "latest_request_id": self.latest_request_id,
            "approval_readiness_status": self.approval_readiness_status,
            "final_gate_status": self.final_gate_status,
            "hardening_status": self.hardening_status,
            "deck_count": self.deck_count,
            "candidate_item_count": self.candidate_item_count,
            "pending_feedback_count": self.pending_feedback_count,
            "review_decision_count": self.review_decision_count,
            "approval_request_count": self.approval_request_count,
            "missing_approval_keys": list(self.missing_approval_keys),
            "read_only": self.read_only,
            "local_only": self.local_only,
            "writes_status_artifact": self.writes_status_artifact,
            "writes_review_decisions": self.writes_review_decisions,
            "writes_feedback_candidates": self.writes_feedback_candidates,
            "applies_candidates": self.applies_candidates,
            "grants_approvals": self.grants_approvals,
            "executes_approval": self.executes_approval,
            "agent_bus_task_write_allowed": self.agent_bus_task_write_allowed,
            "runtime_dispatch_allowed": self.runtime_dispatch_allowed,
            "provider_or_connector_call_allowed": self.provider_or_connector_call_allowed,
            "schedule_activation_allowed": self.schedule_activation_allowed,
            "memory_approval_allowed": self.memory_approval_allowed,
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "mutates_canonical_state": self.mutates_canonical_state,
            "second_datastore_created": self.second_datastore_created,
            "rd_workbook_update_allowed": self.rd_workbook_update_allowed,
            "blocked_effects": list(self.blocked_effects),
        }


def _lane(
    lane_id: str,
    label: str,
    *,
    item_count: int,
    pending_count: int = 0,
    ready_count: int = 0,
    blocked_count: int = 0,
    status: str = "read_only",
    source_refs: tuple[str, ...] = (),
) -> PulseApprovalCenterLane:
    lane = PulseApprovalCenterLane(
        lane_id=lane_id,
        label=label,
        item_count=item_count,
        pending_count=pending_count,
        ready_count=ready_count,
        blocked_count=blocked_count,
        status=status,
        source_refs=source_refs,
    )
    lane.validate()
    return lane


def _action(
    action_id: str,
    lane_id: str,
    label: str,
    action_type: str,
    *,
    target_ref: str | None = None,
    command_preview: tuple[str, ...] = (),
    enabled_for_display: bool = True,
    requires_operator_approval: bool = True,
) -> PulseApprovalCenterActionPreview:
    action = PulseApprovalCenterActionPreview(
        action_id=action_id,
        lane_id=lane_id,
        label=label,
        action_type=action_type,
        target_ref=target_ref,
        command_preview=command_preview,
        enabled_for_display=enabled_for_display,
        requires_operator_approval=requires_operator_approval,
    )
    action.validate()
    return action


def build_pulse_approval_center_readiness(
    vault_root: str | Path,
    *,
    request_id: str | None = None,
    evidence_id: str | None = None,
    generated_at: str | None = None,
    bus_tasks: list[dict[str, Any]] | None = None,
) -> PulseApprovalCenterReadinessSurface:
    """Build a read-only approval center readiness surface."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or now_utc()
    candidate_snapshot = build_candidate_inspector_snapshot(vault)
    feedback_queue = build_feedback_review_queue(vault)
    approval_requests = load_agent_bus_enqueue_approval_requests(vault)
    deck_inventory = build_pulse_deck_inventory(vault)
    hardening_status, hardening_item_count, hardening_ready_count, hardening_blocked_count = (
        _read_hardening_status(vault)
    )

    latest_request_id = request_id or (approval_requests[-1].request_id if approval_requests else None)
    approval_readiness_status: str | None = None
    final_gate_status: str | None = None
    missing_approval_keys: tuple[str, ...] = ()
    final_gate_ready_count = 0
    final_gate_blocked_count = 0
    action_previews: list[PulseApprovalCenterActionPreview] = []

    if latest_request_id:
        readiness = build_pulse_approval_readiness_summary(
            vault,
            latest_request_id,
            evidence_id=evidence_id,
            generated_at=timestamp,
            bus_tasks=bus_tasks,
        )
        final_gate = build_pulse_final_evidence_gate_status(
            vault,
            latest_request_id,
            evidence_id=evidence_id,
            generated_at=timestamp,
            bus_tasks=bus_tasks,
        )
        approval_readiness_status = readiness.readiness_status
        final_gate_status = final_gate.gate_status
        missing_approval_keys = final_gate.missing_approvals
        final_gate_ready_count = 1 if final_gate.ready_for_live_enqueue else 0
        final_gate_blocked_count = 0 if final_gate.ready_for_live_enqueue else 1
        for slot in final_gate.missing_operator_action_slots:
            action_previews.append(
                _action(
                    f"capture-{slot['approval_key']}",
                    "agent_bus_approval_requests",
                    f"Capture evidence: {slot['label']}",
                    "capture_evidence_reference",
                    target_ref=latest_request_id,
                    command_preview=(str(slot["capture_command"]),),
                )
            )
        if final_gate.ready_for_live_enqueue:
            action_previews.append(
                _action(
                    "preview-supervised-live-enqueue",
                    "final_evidence_gate",
                    "Preview supervised live enqueue command",
                    "preview_supervised_command",
                    target_ref=latest_request_id,
                    command_preview=final_gate.supervised_live_command_preview,
                )
            )

    counts = candidate_snapshot.counts_by_kind
    source_refs = tuple(
        sorted(
            set(candidate_snapshot.source_log_paths)
            | {item.latest_json_path for item in deck_inventory if item.latest_json_path}
            | {"runtime/pulse/approval_center.py"}
        )
    )
    deck_count = sum(1 for item in deck_inventory if item.latest_json_path)
    memory_candidate_count = counts.get("personal_map_candidate", 0)
    repair_candidate_count = counts.get("execution_repair_candidate", 0)
    review_decision_count = counts.get("review_decision", 0)
    approval_request_count = len(approval_requests)
    pending_feedback_count = feedback_queue.pending_count

    action_previews.extend(
        [
            _action(
                "review-feedback-candidates",
                "feedback_candidates",
                "Review pending feedback candidates",
                "review_candidates",
                enabled_for_display=pending_feedback_count > 0,
                requires_operator_approval=False,
            ),
            _action(
                "inspect-memory-candidates",
                "memory_candidates",
                "Inspect Personal Map memory candidates",
                "inspect_candidates",
                enabled_for_display=memory_candidate_count > 0,
                requires_operator_approval=False,
            ),
            _action(
                "inspect-execution-repair-candidates",
                "execution_repair_candidates",
                "Inspect execution repair candidates",
                "inspect_candidates",
                enabled_for_display=repair_candidate_count > 0,
                requires_operator_approval=False,
            ),
            _action(
                "review-latest-decks",
                "pulse_decks",
                "Review latest Pulse deck artifacts",
                "review_artifacts",
                enabled_for_display=deck_count > 0,
                requires_operator_approval=False,
            ),
        ]
    )

    lanes = (
        _lane(
            "pulse_decks",
            "Pulse Decks",
            item_count=deck_count,
            ready_count=deck_count,
            source_refs=tuple(item.latest_json_path for item in deck_inventory if item.latest_json_path),
        ),
        _lane(
            "feedback_candidates",
            "Feedback Candidates",
            item_count=counts.get("feedback_candidate", 0),
            pending_count=pending_feedback_count,
            source_refs=tuple(feedback_queue.source_log_paths),
        ),
        _lane(
            "memory_candidates",
            "Memory Candidates",
            item_count=memory_candidate_count,
            pending_count=memory_candidate_count,
        ),
        _lane(
            "execution_repair_candidates",
            "Execution Repair Candidates",
            item_count=repair_candidate_count,
            pending_count=repair_candidate_count,
        ),
        _lane(
            "review_decisions",
            "Review Decisions",
            item_count=review_decision_count,
            ready_count=review_decision_count,
        ),
        _lane(
            "agent_bus_approval_requests",
            "Agent Bus Approval Requests",
            item_count=approval_request_count,
            pending_count=approval_request_count,
            blocked_count=1 if missing_approval_keys else 0,
        ),
        _lane(
            "final_evidence_gate",
            "Final Evidence Gate",
            item_count=1 if latest_request_id else 0,
            ready_count=final_gate_ready_count,
            blocked_count=final_gate_blocked_count,
            status=final_gate_status or "not_configured",
        ),
        _lane(
            "post_completion_hardening",
            "Post-Completion Hardening",
            item_count=hardening_item_count,
            ready_count=hardening_ready_count,
            blocked_count=hardening_blocked_count,
            status=hardening_status,
        ),
    )

    if pending_feedback_count or memory_candidate_count or repair_candidate_count or approval_request_count:
        status = (
            APPROVAL_CENTER_STATUS_BLOCKED
            if missing_approval_keys or final_gate_blocked_count
            else APPROVAL_CENTER_STATUS_READY
        )
    else:
        status = APPROVAL_CENTER_STATUS_EMPTY

    surface = PulseApprovalCenterReadinessSurface(
        generated_at=timestamp,
        approval_center_status=status,
        lanes=lanes,
        action_previews=tuple(action_previews),
        source_refs=source_refs,
        latest_request_id=latest_request_id,
        approval_readiness_status=approval_readiness_status,
        final_gate_status=final_gate_status,
        hardening_status=hardening_status,
        deck_count=deck_count,
        candidate_item_count=candidate_snapshot.item_count,
        pending_feedback_count=pending_feedback_count,
        review_decision_count=review_decision_count,
        approval_request_count=approval_request_count,
        missing_approval_keys=missing_approval_keys,
    )
    surface.validate()
    return surface
