"""Append-only evidence artifacts for Pulse Agent Bus enqueue review.

This layer records operator/Gate evidence for a persisted enqueue approval
request. It does not grant approval, validate a request, write Agent Bus tasks,
dispatch runtimes, apply candidates, or mutate canonical state.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.bus_enqueue_approval_request import (
    PULSE_BUS_APPROVAL_BLOCKED_EFFECTS,
    load_agent_bus_enqueue_approval_requests,
)
from runtime.pulse.bus_enqueue_approval_validation import (
    PulseAgentBusApprovalValidationEvidence,
)
from runtime.pulse.card_schema import now_utc


PULSE_BUS_ENQUEUE_EVIDENCE_ROOT = (
    Path("07_LOGS") / "Pulse-Decks" / "agent-bus-enqueue-evidence"
)
PULSE_BUS_ENQUEUE_EVIDENCE_STATUS = "evidence_recorded"
PULSE_BUS_ENQUEUE_EVIDENCE_LEDGER_STATUS = "read_only"
PULSE_BUS_ENQUEUE_EVIDENCE_BLOCKED_EFFECTS = tuple(
    sorted(
        set(PULSE_BUS_APPROVAL_BLOCKED_EFFECTS)
        | {
            "approval_grant",
            "approval_execution",
            "agent_bus_task_write",
            "candidate_apply",
            "canonical_writeback",
            "gate_policy_mutation",
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


def _is_placeholder_ref(value: str | None) -> bool:
    ref = (value or "").strip()
    return bool(re.fullmatch(r"<[^<>]+>", ref))


def _evidence_id(
    request_id: str,
    reviewer: str,
    created_at: str,
    satisfied_approvals: tuple[str, ...],
) -> str:
    seed = "|".join(
        [request_id, reviewer, created_at, ",".join(sorted(satisfied_approvals))]
    )
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    return f"pulse-bus-enqueue-evidence-{digest}"


@dataclass(frozen=True)
class PulseAgentBusEnqueueEvidenceRecord:
    """Persisted evidence record for one enqueue approval request."""

    evidence_id: str
    request_id: str
    created_at: str = field(default_factory=now_utc)
    reviewer: str = "operator"
    operator_enqueue_approval_present: bool = False
    gate_policy_defined: bool = False
    external_sender_allowance_present: bool = False
    duplicate_work_fingerprint_reviewed: bool = False
    evidence_note: str = ""
    gate_policy_ref: str | None = None
    external_sender_allowance_ref: str | None = None
    duplicate_review_ref: str | None = None
    status: str = PULSE_BUS_ENQUEUE_EVIDENCE_STATUS
    evidence_record_only: bool = True
    approval_granted: bool = False
    approval_executed: bool = False
    gate_policy_mutated: bool = False
    agent_bus_task_written: bool = False
    live_agent_bus_handoff_allowed: bool = False
    review_response_ingest_allowed: bool = False
    candidate_apply_allowed: bool = False
    canonical_writeback_allowed: bool = False
    mutates_canonical_state: bool = False
    second_datastore_write_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    schedule_activation_allowed: bool = False
    blocked_effects: tuple[str, ...] = PULSE_BUS_ENQUEUE_EVIDENCE_BLOCKED_EFFECTS

    @property
    def validation_evidence(self) -> PulseAgentBusApprovalValidationEvidence:
        return PulseAgentBusApprovalValidationEvidence(
            operator_enqueue_approval_present=self.operator_enqueue_approval_present,
            gate_policy_defined=self.gate_policy_defined,
            external_sender_allowance_present=self.external_sender_allowance_present,
            duplicate_work_fingerprint_reviewed=self.duplicate_work_fingerprint_reviewed,
            reviewer=self.reviewer,
            evidence_note=self.evidence_note,
        )

    def validate(self) -> None:
        if not self.evidence_id:
            raise ValueError("evidence_id is required")
        if not self.request_id:
            raise ValueError("request_id is required")
        if not self.reviewer:
            raise ValueError("reviewer is required")
        if self.status != PULSE_BUS_ENQUEUE_EVIDENCE_STATUS:
            raise ValueError("Pulse Agent Bus evidence records must remain evidence_recorded")
        if not self.evidence_record_only:
            raise ValueError("Pulse Agent Bus evidence records must remain record-only")
        if self.approval_granted:
            raise ValueError("Pulse Agent Bus evidence records cannot grant approval")
        if self.approval_executed:
            raise ValueError("Pulse Agent Bus evidence records cannot execute approval")
        if self.gate_policy_mutated:
            raise ValueError("Pulse Agent Bus evidence records cannot mutate Gate policy")
        if self.agent_bus_task_written:
            raise ValueError("Pulse Agent Bus evidence records cannot write bus tasks")
        if self.live_agent_bus_handoff_allowed:
            raise ValueError("Pulse Agent Bus evidence records cannot allow live handoff")
        if self.review_response_ingest_allowed:
            raise ValueError("Pulse Agent Bus evidence records cannot ingest review responses")
        if self.candidate_apply_allowed:
            raise ValueError("Pulse Agent Bus evidence records cannot apply candidates")
        if self.canonical_writeback_allowed:
            raise ValueError("Pulse Agent Bus evidence records cannot allow canonical writeback")
        if self.mutates_canonical_state:
            raise ValueError("Pulse Agent Bus evidence records cannot mutate canonical state")
        if self.second_datastore_write_allowed:
            raise ValueError("Pulse Agent Bus evidence records cannot write a second datastore")
        if self.provider_or_connector_call_allowed:
            raise ValueError("Pulse Agent Bus evidence records cannot call providers or connectors")
        if self.schedule_activation_allowed:
            raise ValueError("Pulse Agent Bus evidence records cannot activate schedules")
        if set(self.blocked_effects) != set(PULSE_BUS_ENQUEUE_EVIDENCE_BLOCKED_EFFECTS):
            raise ValueError("Pulse Agent Bus evidence records must declare blocked effects")
        if self.operator_enqueue_approval_present:
            if not self.evidence_note.strip():
                raise ValueError("operator approval evidence requires --note")
            if _is_placeholder_ref(self.evidence_note):
                raise ValueError("operator approval evidence requires a real --note ref")
        if self.gate_policy_defined:
            if not (self.gate_policy_ref or "").strip():
                raise ValueError("Gate policy evidence requires gate_policy_ref")
            if _is_placeholder_ref(self.gate_policy_ref):
                raise ValueError("Gate policy evidence requires a real gate_policy_ref")
        if self.external_sender_allowance_present:
            if not (self.external_sender_allowance_ref or "").strip():
                raise ValueError(
                    "external sender allowance evidence requires external_sender_allowance_ref"
                )
            if _is_placeholder_ref(self.external_sender_allowance_ref):
                raise ValueError(
                    "external sender allowance evidence requires a real external_sender_allowance_ref"
                )
        if self.duplicate_work_fingerprint_reviewed:
            if not (self.duplicate_review_ref or "").strip():
                raise ValueError(
                    "duplicate work_fingerprint evidence requires duplicate_review_ref"
                )
            if _is_placeholder_ref(self.duplicate_review_ref):
                raise ValueError(
                    "duplicate work_fingerprint evidence requires a real duplicate_review_ref"
                )
        self.validation_evidence.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["blocked_effects"] = list(self.blocked_effects)
        payload["satisfied_approvals"] = list(
            self.validation_evidence.satisfied_approvals
        )
        payload["missing_approvals"] = list(self.validation_evidence.missing_approvals)
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PulseAgentBusEnqueueEvidenceRecord":
        record = cls(
            evidence_id=str(data.get("evidence_id") or ""),
            request_id=str(data.get("request_id") or ""),
            created_at=str(data.get("created_at") or now_utc()),
            reviewer=str(data.get("reviewer") or "operator"),
            operator_enqueue_approval_present=bool(
                data.get("operator_enqueue_approval_present", False)
            ),
            gate_policy_defined=bool(data.get("gate_policy_defined", False)),
            external_sender_allowance_present=bool(
                data.get("external_sender_allowance_present", False)
            ),
            duplicate_work_fingerprint_reviewed=bool(
                data.get("duplicate_work_fingerprint_reviewed", False)
            ),
            evidence_note=str(data.get("evidence_note") or ""),
            gate_policy_ref=data.get("gate_policy_ref"),
            external_sender_allowance_ref=data.get("external_sender_allowance_ref"),
            duplicate_review_ref=data.get("duplicate_review_ref"),
            status=str(data.get("status") or PULSE_BUS_ENQUEUE_EVIDENCE_STATUS),
            evidence_record_only=bool(data.get("evidence_record_only", True)),
            approval_granted=bool(data.get("approval_granted", False)),
            approval_executed=bool(data.get("approval_executed", False)),
            gate_policy_mutated=bool(data.get("gate_policy_mutated", False)),
            agent_bus_task_written=bool(data.get("agent_bus_task_written", False)),
            live_agent_bus_handoff_allowed=bool(
                data.get("live_agent_bus_handoff_allowed", False)
            ),
            review_response_ingest_allowed=bool(
                data.get("review_response_ingest_allowed", False)
            ),
            candidate_apply_allowed=bool(data.get("candidate_apply_allowed", False)),
            canonical_writeback_allowed=bool(
                data.get("canonical_writeback_allowed", False)
            ),
            mutates_canonical_state=bool(data.get("mutates_canonical_state", False)),
            second_datastore_write_allowed=bool(
                data.get("second_datastore_write_allowed", False)
            ),
            provider_or_connector_call_allowed=bool(
                data.get("provider_or_connector_call_allowed", False)
            ),
            schedule_activation_allowed=bool(
                data.get("schedule_activation_allowed", False)
            ),
            blocked_effects=tuple(
                data.get("blocked_effects", PULSE_BUS_ENQUEUE_EVIDENCE_BLOCKED_EFFECTS)
            ),
        )
        record.validate()
        return record


@dataclass(frozen=True)
class PulseAgentBusEnqueueEvidenceArtifact:
    path: str
    evidence_id: str
    request_id: str
    status: str = PULSE_BUS_ENQUEUE_EVIDENCE_STATUS
    approval_granted: bool = False
    agent_bus_task_written: bool = False
    canonical_writeback_allowed: bool = False

    def validate(self) -> None:
        if not self.path:
            raise ValueError("evidence artifact path is required")
        if not self.evidence_id:
            raise ValueError("evidence_id is required")
        if not self.request_id:
            raise ValueError("request_id is required")
        if self.status != PULSE_BUS_ENQUEUE_EVIDENCE_STATUS:
            raise ValueError("evidence artifacts must remain evidence_recorded")
        if self.approval_granted:
            raise ValueError("evidence artifacts cannot grant approval")
        if self.agent_bus_task_written:
            raise ValueError("evidence artifacts cannot write bus tasks")
        if self.canonical_writeback_allowed:
            raise ValueError("evidence artifacts cannot allow canonical writeback")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass
class PulseAgentBusEnqueueEvidenceLedger:
    generated_at: str = field(default_factory=now_utc)
    records: list[PulseAgentBusEnqueueEvidenceRecord] = field(default_factory=list)
    source_log_paths: list[str] = field(default_factory=list)
    ledger_status: str = PULSE_BUS_ENQUEUE_EVIDENCE_LEDGER_STATUS
    writes: list[str] = field(default_factory=list)
    approval_granted: bool = False
    agent_bus_task_written: bool = False
    canonical_writeback_allowed: bool = False
    second_datastore_write_allowed: bool = False

    @property
    def record_count(self) -> int:
        return len(self.records)

    def validate(self) -> None:
        if self.ledger_status != PULSE_BUS_ENQUEUE_EVIDENCE_LEDGER_STATUS:
            raise ValueError("Pulse Agent Bus evidence ledgers are read-only")
        if self.writes:
            raise ValueError("Pulse Agent Bus evidence ledgers cannot declare writes")
        if self.approval_granted:
            raise ValueError("Pulse Agent Bus evidence ledgers cannot grant approval")
        if self.agent_bus_task_written:
            raise ValueError("Pulse Agent Bus evidence ledgers cannot write bus tasks")
        if self.canonical_writeback_allowed:
            raise ValueError("Pulse Agent Bus evidence ledgers cannot allow canonical writeback")
        if self.second_datastore_write_allowed:
            raise ValueError("Pulse Agent Bus evidence ledgers cannot write a second datastore")
        for record in self.records:
            record.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "ledger_status": self.ledger_status,
            "record_count": self.record_count,
            "source_log_paths": list(self.source_log_paths),
            "writes": list(self.writes),
            "approval_granted": self.approval_granted,
            "agent_bus_task_written": self.agent_bus_task_written,
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "second_datastore_write_allowed": self.second_datastore_write_allowed,
            "records": [record.to_dict() for record in self.records],
        }


def build_agent_bus_enqueue_evidence_record(
    request_id: str,
    *,
    reviewer: str = "operator",
    operator_enqueue_approval_present: bool = False,
    gate_policy_defined: bool = False,
    external_sender_allowance_present: bool = False,
    duplicate_work_fingerprint_reviewed: bool = False,
    evidence_note: str = "",
    gate_policy_ref: str | None = None,
    external_sender_allowance_ref: str | None = None,
    duplicate_review_ref: str | None = None,
    created_at: str | None = None,
) -> PulseAgentBusEnqueueEvidenceRecord:
    """Build one evidence record without validating or executing handoff."""
    timestamp = created_at or now_utc()
    evidence = PulseAgentBusApprovalValidationEvidence(
        operator_enqueue_approval_present=operator_enqueue_approval_present,
        gate_policy_defined=gate_policy_defined,
        external_sender_allowance_present=external_sender_allowance_present,
        duplicate_work_fingerprint_reviewed=duplicate_work_fingerprint_reviewed,
        reviewer=reviewer,
        evidence_note=evidence_note,
    )
    evidence.validate()
    record = PulseAgentBusEnqueueEvidenceRecord(
        evidence_id=_evidence_id(
            request_id,
            reviewer,
            timestamp,
            evidence.satisfied_approvals,
        ),
        request_id=request_id,
        created_at=timestamp,
        reviewer=reviewer,
        operator_enqueue_approval_present=operator_enqueue_approval_present,
        gate_policy_defined=gate_policy_defined,
        external_sender_allowance_present=external_sender_allowance_present,
        duplicate_work_fingerprint_reviewed=duplicate_work_fingerprint_reviewed,
        evidence_note=evidence_note,
        gate_policy_ref=gate_policy_ref,
        external_sender_allowance_ref=external_sender_allowance_ref,
        duplicate_review_ref=duplicate_review_ref,
    )
    record.validate()
    return record


def evidence_log_path(vault_root: str | Path, *, created_at: str | None = None) -> Path:
    vault = _vault_path(vault_root)
    root = (vault / PULSE_BUS_ENQUEUE_EVIDENCE_ROOT).resolve()
    path = root / f"{_date_slug(created_at or now_utc())}-agent-bus-enqueue-evidence.jsonl"
    _assert_inside(
        path,
        root,
        "Pulse Agent Bus evidence logs must stay inside agent-bus-enqueue-evidence/",
    )
    return path


def persist_agent_bus_enqueue_evidence_record(
    vault_root: str | Path,
    record: PulseAgentBusEnqueueEvidenceRecord,
) -> PulseAgentBusEnqueueEvidenceArtifact:
    """Append one evidence record under the governed Pulse log tree."""
    record.validate()
    vault = _vault_path(vault_root)
    path = evidence_log_path(vault, created_at=record.created_at)
    root = (vault / PULSE_BUS_ENQUEUE_EVIDENCE_ROOT).resolve()
    _assert_inside(
        path,
        root,
        "Pulse Agent Bus evidence logs must stay inside agent-bus-enqueue-evidence/",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.to_dict(), sort_keys=True))
        handle.write("\n")
    artifact = PulseAgentBusEnqueueEvidenceArtifact(
        path=_relative_to_vault(vault, path),
        evidence_id=record.evidence_id,
        request_id=record.request_id,
    )
    artifact.validate()
    return artifact


def create_agent_bus_enqueue_evidence_record(
    vault_root: str | Path,
    request_id: str,
    *,
    reviewer: str = "operator",
    operator_enqueue_approval_present: bool = False,
    gate_policy_defined: bool = False,
    external_sender_allowance_present: bool = False,
    duplicate_work_fingerprint_reviewed: bool = False,
    evidence_note: str = "",
    gate_policy_ref: str | None = None,
    external_sender_allowance_ref: str | None = None,
    duplicate_review_ref: str | None = None,
    created_at: str | None = None,
) -> tuple[PulseAgentBusEnqueueEvidenceRecord, PulseAgentBusEnqueueEvidenceArtifact]:
    """Create and persist evidence only if the approval request exists."""
    if not request_id:
        raise ValueError("request_id is required")
    requests = load_agent_bus_enqueue_approval_requests(vault_root)
    if not any(request.request_id == request_id for request in requests):
        raise ValueError(f"Pulse Agent Bus approval request not found: {request_id}")
    record = build_agent_bus_enqueue_evidence_record(
        request_id,
        reviewer=reviewer,
        operator_enqueue_approval_present=operator_enqueue_approval_present,
        gate_policy_defined=gate_policy_defined,
        external_sender_allowance_present=external_sender_allowance_present,
        duplicate_work_fingerprint_reviewed=duplicate_work_fingerprint_reviewed,
        evidence_note=evidence_note,
        gate_policy_ref=gate_policy_ref,
        external_sender_allowance_ref=external_sender_allowance_ref,
        duplicate_review_ref=duplicate_review_ref,
        created_at=created_at,
    )
    artifact = persist_agent_bus_enqueue_evidence_record(vault_root, record)
    return record, artifact


def load_agent_bus_enqueue_evidence_records(
    vault_root: str | Path,
    *,
    evidence_id: str | None = None,
    request_id: str | None = None,
    log_path: str | Path | None = None,
) -> list[PulseAgentBusEnqueueEvidenceRecord]:
    """Load evidence records read-only."""
    vault = _vault_path(vault_root)
    root = (vault / PULSE_BUS_ENQUEUE_EVIDENCE_ROOT).resolve()
    if log_path is None:
        paths = sorted(root.glob("*-agent-bus-enqueue-evidence.jsonl")) if root.exists() else []
    else:
        target = Path(log_path)
        target = target if target.is_absolute() else vault / target
        _assert_inside(
            target,
            root,
            "Pulse Agent Bus evidence logs must stay inside agent-bus-enqueue-evidence/",
        )
        paths = [target]

    records: list[PulseAgentBusEnqueueEvidenceRecord] = []
    for path in paths:
        if not path.exists():
            continue
        _assert_inside(
            path,
            root,
            "Pulse Agent Bus evidence logs must stay inside agent-bus-enqueue-evidence/",
        )
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                record = PulseAgentBusEnqueueEvidenceRecord.from_dict(json.loads(line))
            except (json.JSONDecodeError, ValueError):
                continue
            if evidence_id is not None and record.evidence_id != evidence_id:
                continue
            if request_id is not None and record.request_id != request_id:
                continue
            records.append(record)
    return records


def load_agent_bus_enqueue_evidence_record_by_id(
    vault_root: str | Path,
    evidence_id: str,
) -> PulseAgentBusEnqueueEvidenceRecord:
    """Load one evidence record by ID or raise."""
    if not evidence_id:
        raise ValueError("evidence_id is required")
    records = load_agent_bus_enqueue_evidence_records(vault_root, evidence_id=evidence_id)
    if not records:
        raise ValueError(f"Pulse Agent Bus evidence record not found: {evidence_id}")
    return records[-1]


def build_agent_bus_enqueue_evidence_ledger(
    vault_root: str | Path,
    *,
    request_id: str | None = None,
    evidence_id: str | None = None,
) -> PulseAgentBusEnqueueEvidenceLedger:
    """Build a read-only ledger snapshot of evidence records."""
    vault = _vault_path(vault_root)
    root = (vault / PULSE_BUS_ENQUEUE_EVIDENCE_ROOT).resolve()
    source_log_paths = (
        [_relative_to_vault(vault, path) for path in sorted(root.glob("*-agent-bus-enqueue-evidence.jsonl"))]
        if root.exists()
        else []
    )
    ledger = PulseAgentBusEnqueueEvidenceLedger(
        records=load_agent_bus_enqueue_evidence_records(
            vault,
            evidence_id=evidence_id,
            request_id=request_id,
        ),
        source_log_paths=source_log_paths,
    )
    ledger.validate()
    return ledger
