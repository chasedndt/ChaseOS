"""Persisted approval-request records for Pulse Agent Bus enqueue intent.

This module records operator-reviewable intent for a future Pulse REVIEW task
handoff. It does not approve the request, write Agent Bus tasks, dispatch
runtimes, ingest review responses, apply candidates, or mutate canonical state.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.bus_enqueue_design import (
    PULSE_BUS_ENQUEUE_BLOCKED_EFFECTS,
    PULSE_BUS_ENQUEUE_REQUIRED_APPROVALS,
    PulseAgentBusEnqueuePreflight,
    build_agent_bus_enqueue_preflight_for_candidate,
)
from runtime.pulse.card_schema import now_utc


PULSE_BUS_APPROVAL_REQUEST_ROOT = (
    Path("07_LOGS") / "Pulse-Decks" / "agent-bus-approval-requests"
)
PULSE_BUS_APPROVAL_REQUEST_STATUS = "approval_requested"
PULSE_BUS_APPROVAL_LEDGER_STATUS = "read_only"
PULSE_BUS_APPROVAL_OPERATION = "pulse.agent_bus.enqueue_review"
PULSE_BUS_APPROVAL_BLOCKED_EFFECTS = tuple(
    sorted(
        set(PULSE_BUS_ENQUEUE_BLOCKED_EFFECTS)
        | {
            "approval_grant",
            "approval_execution",
            "bus_status_update",
            "live_agent_bus_handoff",
        }
    )
)


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _assert_inside(child: Path, parent: Path, message: str) -> None:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError as exc:
        raise ValueError(message) from exc


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return str(path.resolve())


def _date_slug(created_at: str) -> str:
    candidate = (created_at or now_utc())[:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", candidate):
        return now_utc()[:10]
    return candidate


def _id(prefix: str, *parts: str) -> str:
    seed = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


@dataclass
class PulseAgentBusEnqueueApprovalRequest:
    """A persisted request for future operator/Gate approval.

    This is request state only. It is not an approval decision and cannot
    perform the underlying bus handoff.
    """

    request_id: str
    preflight_id: str
    contract_id: str
    candidate_id: str
    candidate_kind: str
    operation: str
    sender: str
    recipient: str
    intent: str
    priority: str
    request_text: str
    expected_output: str
    notes: str
    work_fingerprint: str
    task_payload_preview: dict[str, Any]
    required_approvals: tuple[str, ...] = PULSE_BUS_ENQUEUE_REQUIRED_APPROVALS
    requested_by: str = "operator"
    requested_at: str = field(default_factory=now_utc)
    status: str = PULSE_BUS_APPROVAL_REQUEST_STATUS
    source_log_path: str | None = None
    source_deck_path: str | None = None
    source_card_id: str | None = None
    target_ref: str | None = None
    runtime_id: str | None = None
    approval_request_only: bool = True
    persisted_request: bool = True
    approval_granted: bool = False
    gate_policy_defined: bool = False
    duplicate_check_performed: bool = False
    live_agent_bus_handoff_allowed: bool = False
    agent_bus_task_written: bool = False
    approval_executed: bool = False
    review_response_ingest_allowed: bool = False
    candidate_apply_allowed: bool = False
    canonical_writeback_allowed: bool = False
    mutates_canonical_state: bool = False
    second_datastore_write_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    schedule_activation_allowed: bool = False
    blocked_effects: tuple[str, ...] = PULSE_BUS_APPROVAL_BLOCKED_EFFECTS

    def validate(self) -> None:
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
        if self.operation != PULSE_BUS_APPROVAL_OPERATION:
            raise ValueError("Pulse Agent Bus approval requests must use enqueue review operation")
        if self.intent != "REVIEW":
            raise ValueError("Pulse Agent Bus approval requests must preserve REVIEW intent")
        if self.priority not in {"low", "normal", "high"}:
            raise ValueError("Pulse Agent Bus approval request priority must be low, normal, or high")
        if not self.request_text:
            raise ValueError("request_text is required")
        if not self.expected_output:
            raise ValueError("expected_output is required")
        if not self.work_fingerprint:
            raise ValueError("work_fingerprint is required")
        if not self.task_payload_preview:
            raise ValueError("task_payload_preview is required")
        if set(self.required_approvals) != set(PULSE_BUS_ENQUEUE_REQUIRED_APPROVALS):
            raise ValueError("Pulse Agent Bus approval requests must declare required approvals")
        if not self.requested_by:
            raise ValueError("requested_by is required")
        if self.status != PULSE_BUS_APPROVAL_REQUEST_STATUS:
            raise ValueError("Pulse Agent Bus approval requests must remain approval_requested")
        if not self.approval_request_only:
            raise ValueError("Pulse Agent Bus approval requests must remain request-only")
        if not self.persisted_request:
            raise ValueError("Pulse Agent Bus approval requests in this lane are persisted requests")
        if self.approval_granted:
            raise ValueError("Pulse Agent Bus approval requests cannot grant approval")
        if self.gate_policy_defined:
            raise ValueError("Pulse Agent Bus approval requests cannot claim Gate policy definition")
        if self.duplicate_check_performed:
            raise ValueError("Pulse Agent Bus approval requests cannot claim duplicate checks")
        if self.live_agent_bus_handoff_allowed:
            raise ValueError("Pulse Agent Bus approval requests cannot allow live handoff")
        if self.agent_bus_task_written:
            raise ValueError("Pulse Agent Bus approval requests cannot write bus tasks")
        if self.approval_executed:
            raise ValueError("Pulse Agent Bus approval requests cannot execute approval")
        if self.review_response_ingest_allowed:
            raise ValueError("Pulse Agent Bus approval requests cannot ingest review responses")
        if self.candidate_apply_allowed:
            raise ValueError("Pulse Agent Bus approval requests cannot apply candidates")
        if self.canonical_writeback_allowed:
            raise ValueError("Pulse Agent Bus approval requests cannot allow canonical writeback")
        if self.mutates_canonical_state:
            raise ValueError("Pulse Agent Bus approval requests cannot mutate canonical state")
        if self.second_datastore_write_allowed:
            raise ValueError("Pulse Agent Bus approval requests cannot write a second datastore")
        if self.provider_or_connector_call_allowed:
            raise ValueError("Pulse Agent Bus approval requests cannot call providers or connectors")
        if self.schedule_activation_allowed:
            raise ValueError("Pulse Agent Bus approval requests cannot activate schedules")
        if set(self.blocked_effects) != set(PULSE_BUS_APPROVAL_BLOCKED_EFFECTS):
            raise ValueError("Pulse Agent Bus approval requests must declare blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["required_approvals"] = list(self.required_approvals)
        payload["blocked_effects"] = list(self.blocked_effects)
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PulseAgentBusEnqueueApprovalRequest":
        request = cls(
            request_id=str(data.get("request_id") or ""),
            preflight_id=str(data.get("preflight_id") or ""),
            contract_id=str(data.get("contract_id") or ""),
            candidate_id=str(data.get("candidate_id") or ""),
            candidate_kind=str(data.get("candidate_kind") or ""),
            operation=str(data.get("operation") or ""),
            sender=str(data.get("sender") or ""),
            recipient=str(data.get("recipient") or ""),
            intent=str(data.get("intent") or ""),
            priority=str(data.get("priority") or ""),
            request_text=str(data.get("request_text") or ""),
            expected_output=str(data.get("expected_output") or ""),
            notes=str(data.get("notes") or ""),
            work_fingerprint=str(data.get("work_fingerprint") or ""),
            task_payload_preview=dict(data.get("task_payload_preview") or {}),
            required_approvals=tuple(data.get("required_approvals", ())),
            requested_by=str(data.get("requested_by") or "operator"),
            requested_at=str(data.get("requested_at") or now_utc()),
            status=str(data.get("status") or PULSE_BUS_APPROVAL_REQUEST_STATUS),
            source_log_path=data.get("source_log_path"),
            source_deck_path=data.get("source_deck_path"),
            source_card_id=data.get("source_card_id"),
            target_ref=data.get("target_ref"),
            runtime_id=data.get("runtime_id"),
            approval_request_only=bool(data.get("approval_request_only", True)),
            persisted_request=bool(data.get("persisted_request", True)),
            approval_granted=bool(data.get("approval_granted", False)),
            gate_policy_defined=bool(data.get("gate_policy_defined", False)),
            duplicate_check_performed=bool(data.get("duplicate_check_performed", False)),
            live_agent_bus_handoff_allowed=bool(
                data.get("live_agent_bus_handoff_allowed", False)
            ),
            agent_bus_task_written=bool(data.get("agent_bus_task_written", False)),
            approval_executed=bool(data.get("approval_executed", False)),
            review_response_ingest_allowed=bool(
                data.get("review_response_ingest_allowed", False)
            ),
            candidate_apply_allowed=bool(data.get("candidate_apply_allowed", False)),
            canonical_writeback_allowed=bool(data.get("canonical_writeback_allowed", False)),
            mutates_canonical_state=bool(data.get("mutates_canonical_state", False)),
            second_datastore_write_allowed=bool(
                data.get("second_datastore_write_allowed", False)
            ),
            provider_or_connector_call_allowed=bool(
                data.get("provider_or_connector_call_allowed", False)
            ),
            schedule_activation_allowed=bool(data.get("schedule_activation_allowed", False)),
            blocked_effects=tuple(data.get("blocked_effects", PULSE_BUS_APPROVAL_BLOCKED_EFFECTS)),
        )
        request.validate()
        return request


@dataclass
class PulseAgentBusEnqueueApprovalArtifact:
    path: str
    request_id: str
    preflight_id: str
    candidate_id: str
    status: str = PULSE_BUS_APPROVAL_REQUEST_STATUS
    approval_granted: bool = False
    agent_bus_task_written: bool = False
    canonical_writeback_allowed: bool = False
    second_datastore_write_allowed: bool = False

    def validate(self) -> None:
        if not self.path:
            raise ValueError("approval artifact path is required")
        if not self.request_id:
            raise ValueError("request_id is required")
        if not self.preflight_id:
            raise ValueError("preflight_id is required")
        if not self.candidate_id:
            raise ValueError("candidate_id is required")
        if self.status != PULSE_BUS_APPROVAL_REQUEST_STATUS:
            raise ValueError("approval artifacts must remain approval_requested")
        if self.approval_granted:
            raise ValueError("approval artifacts cannot grant approval")
        if self.agent_bus_task_written:
            raise ValueError("approval artifacts cannot write bus tasks")
        if self.canonical_writeback_allowed:
            raise ValueError("approval artifacts cannot allow canonical writeback")
        if self.second_datastore_write_allowed:
            raise ValueError("approval artifacts cannot write a second datastore")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass
class PulseAgentBusEnqueueApprovalLedger:
    generated_at: str = field(default_factory=now_utc)
    requests: list[PulseAgentBusEnqueueApprovalRequest] = field(default_factory=list)
    source_log_paths: list[str] = field(default_factory=list)
    ledger_status: str = PULSE_BUS_APPROVAL_LEDGER_STATUS
    writes: list[str] = field(default_factory=list)
    approval_granted: bool = False
    agent_bus_task_written: bool = False
    approval_executed: bool = False
    canonical_writeback_allowed: bool = False
    second_datastore_write_allowed: bool = False
    blocked_effects: tuple[str, ...] = PULSE_BUS_APPROVAL_BLOCKED_EFFECTS

    @property
    def request_count(self) -> int:
        return len(self.requests)

    def validate(self) -> None:
        if self.ledger_status != PULSE_BUS_APPROVAL_LEDGER_STATUS:
            raise ValueError("Pulse Agent Bus approval ledgers are read-only")
        if self.writes:
            raise ValueError("Pulse Agent Bus approval ledgers cannot declare writes")
        if self.approval_granted:
            raise ValueError("Pulse Agent Bus approval ledgers cannot grant approval")
        if self.agent_bus_task_written:
            raise ValueError("Pulse Agent Bus approval ledgers cannot write bus tasks")
        if self.approval_executed:
            raise ValueError("Pulse Agent Bus approval ledgers cannot execute approval")
        if self.canonical_writeback_allowed:
            raise ValueError("Pulse Agent Bus approval ledgers cannot allow canonical writeback")
        if self.second_datastore_write_allowed:
            raise ValueError("Pulse Agent Bus approval ledgers cannot write a second datastore")
        if set(self.blocked_effects) != set(PULSE_BUS_APPROVAL_BLOCKED_EFFECTS):
            raise ValueError("Pulse Agent Bus approval ledgers must declare blocked effects")
        for request in self.requests:
            request.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "ledger_status": self.ledger_status,
            "request_count": self.request_count,
            "source_log_paths": list(self.source_log_paths),
            "writes": list(self.writes),
            "approval_granted": self.approval_granted,
            "agent_bus_task_written": self.agent_bus_task_written,
            "approval_executed": self.approval_executed,
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "second_datastore_write_allowed": self.second_datastore_write_allowed,
            "blocked_effects": list(self.blocked_effects),
            "requests": [request.to_dict() for request in self.requests],
        }


def build_agent_bus_enqueue_approval_request(
    preflight: PulseAgentBusEnqueuePreflight,
    *,
    requested_by: str = "operator",
    requested_at: str | None = None,
) -> PulseAgentBusEnqueueApprovalRequest:
    """Build a persisted-request payload from a non-writing enqueue preflight."""
    preflight.validate()
    timestamp = requested_at or now_utc()
    request = PulseAgentBusEnqueueApprovalRequest(
        request_id=_id(
            "pulse-bus-enqueue-approval",
            preflight.preflight_id,
            preflight.contract_id,
            preflight.candidate_id,
            preflight.recipient,
            requested_by,
            timestamp,
        ),
        preflight_id=preflight.preflight_id,
        contract_id=preflight.contract_id,
        candidate_id=preflight.candidate_id,
        candidate_kind=preflight.candidate_kind,
        operation=PULSE_BUS_APPROVAL_OPERATION,
        sender=preflight.sender,
        recipient=preflight.recipient,
        intent=preflight.intent,
        priority=preflight.priority,
        request_text=preflight.request,
        expected_output=preflight.expected_output,
        notes=(
            f"{preflight.notes} Approval request only: this record does not "
            "grant approval or perform live Agent Bus handoff."
        ),
        work_fingerprint=preflight.work_fingerprint,
        task_payload_preview=preflight.to_task_payload_preview(),
        requested_by=requested_by,
        requested_at=timestamp,
        source_log_path=preflight.source_log_path,
        source_deck_path=preflight.source_deck_path,
        source_card_id=preflight.source_card_id,
        target_ref=preflight.target_ref,
        runtime_id=preflight.runtime_id,
    )
    request.validate()
    return request


def build_agent_bus_enqueue_approval_request_for_candidate(
    vault_root: str | Path,
    candidate_id: str,
    *,
    recipient: str = "Hermes",
    requested_by: str = "operator",
    priority: str = "normal",
    requested_at: str | None = None,
) -> PulseAgentBusEnqueueApprovalRequest:
    """Load a candidate read-only and build its approval-request payload."""
    preflight = build_agent_bus_enqueue_preflight_for_candidate(
        vault_root,
        candidate_id,
        recipient=recipient,
        requested_by=requested_by,
        priority=priority,
        created_at=requested_at,
    )
    return build_agent_bus_enqueue_approval_request(
        preflight,
        requested_by=requested_by,
        requested_at=requested_at,
    )


def approval_request_log_path(
    vault_root: str | Path,
    *,
    requested_at: str | None = None,
) -> Path:
    vault = _vault_path(vault_root)
    root = (vault / PULSE_BUS_APPROVAL_REQUEST_ROOT).resolve()
    path = root / f"{_date_slug(requested_at or now_utc())}-agent-bus-approval-requests.jsonl"
    _assert_inside(
        path,
        root,
        "Pulse Agent Bus approval request logs must stay inside agent-bus-approval-requests/",
    )
    return path


def persist_agent_bus_enqueue_approval_request(
    vault_root: str | Path,
    request: PulseAgentBusEnqueueApprovalRequest,
) -> PulseAgentBusEnqueueApprovalArtifact:
    """Append one approval-request record under the governed Pulse log tree."""
    request.validate()
    vault = _vault_path(vault_root)
    path = approval_request_log_path(vault, requested_at=request.requested_at)
    root = (vault / PULSE_BUS_APPROVAL_REQUEST_ROOT).resolve()
    _assert_inside(
        path,
        root,
        "Pulse Agent Bus approval request logs must stay inside agent-bus-approval-requests/",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(request.to_dict(), sort_keys=True))
        handle.write("\n")

    artifact = PulseAgentBusEnqueueApprovalArtifact(
        path=_relative_to_vault(vault, path),
        request_id=request.request_id,
        preflight_id=request.preflight_id,
        candidate_id=request.candidate_id,
    )
    artifact.validate()
    return artifact


def load_agent_bus_enqueue_approval_requests(
    vault_root: str | Path,
    *,
    log_path: str | Path | None = None,
    candidate_id: str | None = None,
) -> list[PulseAgentBusEnqueueApprovalRequest]:
    """Load approval-request records without applying or executing them."""
    vault = _vault_path(vault_root)
    root = (vault / PULSE_BUS_APPROVAL_REQUEST_ROOT).resolve()
    if log_path is None:
        paths = sorted(root.glob("*-agent-bus-approval-requests.jsonl")) if root.exists() else []
    else:
        target = Path(log_path)
        target = target if target.is_absolute() else vault / target
        _assert_inside(
            target,
            root,
            "Pulse Agent Bus approval request logs must stay inside agent-bus-approval-requests/",
        )
        paths = [target]

    requests: list[PulseAgentBusEnqueueApprovalRequest] = []
    for path in paths:
        if not path.exists():
            continue
        _assert_inside(
            path,
            root,
            "Pulse Agent Bus approval request logs must stay inside agent-bus-approval-requests/",
        )
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            request = PulseAgentBusEnqueueApprovalRequest.from_dict(json.loads(line))
            if candidate_id is not None and request.candidate_id != candidate_id:
                continue
            requests.append(request)
    return requests


def _source_log_paths(vault: Path, log_path: str | Path | None) -> list[str]:
    root = (vault / PULSE_BUS_APPROVAL_REQUEST_ROOT).resolve()
    if log_path is not None:
        target = Path(log_path)
        target = target if target.is_absolute() else vault / target
        return [_relative_to_vault(vault, target)]
    if not root.exists():
        return []
    return [
        _relative_to_vault(vault, path)
        for path in sorted(root.glob("*-agent-bus-approval-requests.jsonl"))
    ]


def build_agent_bus_enqueue_approval_ledger(
    vault_root: str | Path,
    *,
    log_path: str | Path | None = None,
    candidate_id: str | None = None,
) -> PulseAgentBusEnqueueApprovalLedger:
    """Build a read-only ledger snapshot of approval-request records."""
    vault = _vault_path(vault_root)
    ledger = PulseAgentBusEnqueueApprovalLedger(
        requests=load_agent_bus_enqueue_approval_requests(
            vault,
            log_path=log_path,
            candidate_id=candidate_id,
        ),
        source_log_paths=_source_log_paths(vault, log_path),
    )
    ledger.validate()
    return ledger
