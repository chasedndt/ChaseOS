"""Live Pulse Agent Bus enqueue.

This is the only Pulse module that imports the Agent Bus writer and calls
bus.create_task(). It requires a fully-validated approval result with
status=ready_for_final_handoff_review before any bus write occurs.

Governance sequence:
  1. Require validation_status == ready_for_final_handoff_review
  2. Perform live duplicate fingerprint check against Agent Bus
  3. Call bus.create_task() with allow_external_sender=True for Operator sender
  4. Write a JSONL result record under 07_LOGS/Pulse-Decks/agent-bus-enqueue-results/
  5. Return PulseAgentBusEnqueueResult

This module does NOT: apply candidates, mutate canonical ChaseOS state, ingest
review responses, call providers/connectors, or grant approvals.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.bus_enqueue_approval_validation import (
    PULSE_BUS_APPROVAL_VALIDATION_STATUS_READY,
    PulseAgentBusApprovalValidationEvidence,
    PulseAgentBusApprovalValidationResult,
    validate_agent_bus_enqueue_approval_request_by_id,
)
from runtime.pulse.card_schema import now_utc


PULSE_BUS_ENQUEUE_RESULTS_ROOT = (
    Path("07_LOGS") / "Pulse-Decks" / "agent-bus-enqueue-results"
)
PULSE_BUS_ENQUEUE_RESULT_STATUS_ENQUEUED = "enqueued"
PULSE_BUS_ENQUEUE_RESULT_STATUS_BLOCKED = "blocked"
PULSE_BUS_ENQUEUE_RESULT_STATUS_DUPLICATE = "duplicate_skipped"
PULSE_BUS_ENQUEUE_RESULT_STATUS_BUS_ERROR = "bus_error"
PULSE_BUS_ENQUEUE_RESULT_STATUSES = {
    PULSE_BUS_ENQUEUE_RESULT_STATUS_ENQUEUED,
    PULSE_BUS_ENQUEUE_RESULT_STATUS_BLOCKED,
    PULSE_BUS_ENQUEUE_RESULT_STATUS_DUPLICATE,
    PULSE_BUS_ENQUEUE_RESULT_STATUS_BUS_ERROR,
}

# Status values that mean a task is still active (not finished).
_ACTIVE_TASK_STATES = {"open", "claimed", "in_progress", "blocked", "review"}


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


def _date_slug(ts: str) -> str:
    candidate = (ts or now_utc())[:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", candidate):
        return now_utc()[:10]
    return candidate


def _result_id(validation_id: str, candidate_id: str, recipient: str, ts: str) -> str:
    seed = "|".join([validation_id, candidate_id, recipient, ts])
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    return f"pulse-bus-enqueue-result-{digest}"


@dataclass
class PulseAgentBusEnqueueResult:
    """Outcome of one live Pulse Agent Bus enqueue attempt."""

    result_id: str
    validation_id: str
    request_id: str
    candidate_id: str
    candidate_kind: str
    recipient: str
    work_fingerprint: str
    result_status: str
    enqueued: bool
    enqueued_at: str = field(default_factory=now_utc)
    task_id: str | None = None
    reason: str = ""
    duplicate_found: bool = False
    duplicate_task_id: str | None = None
    # Immutable governance flags — these never change.
    candidate_apply_allowed: bool = False
    canonical_writeback_allowed: bool = False
    review_response_ingest_allowed: bool = False
    mutates_canonical_state: bool = False
    second_datastore_write_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    schedule_activation_allowed: bool = False

    def validate(self) -> None:
        if not self.result_id:
            raise ValueError("result_id is required")
        if not self.validation_id:
            raise ValueError("validation_id is required")
        if not self.request_id:
            raise ValueError("request_id is required")
        if not self.candidate_id:
            raise ValueError("candidate_id is required")
        if not self.candidate_kind:
            raise ValueError("candidate_kind is required")
        if not self.recipient:
            raise ValueError("recipient is required")
        if self.result_status not in PULSE_BUS_ENQUEUE_RESULT_STATUSES:
            raise ValueError(f"invalid result_status: {self.result_status}")
        if self.enqueued and not self.task_id:
            raise ValueError("enqueued results must have a task_id")
        if not self.enqueued and self.task_id:
            raise ValueError("non-enqueued results must not have a task_id")
        if self.candidate_apply_allowed:
            raise ValueError("Pulse enqueue results cannot allow candidate apply")
        if self.canonical_writeback_allowed:
            raise ValueError("Pulse enqueue results cannot allow canonical writeback")
        if self.review_response_ingest_allowed:
            raise ValueError("Pulse enqueue results cannot allow review response ingest")
        if self.mutates_canonical_state:
            raise ValueError("Pulse enqueue results cannot mutate canonical state")
        if self.second_datastore_write_allowed:
            raise ValueError("Pulse enqueue results cannot write a second datastore")
        if self.provider_or_connector_call_allowed:
            raise ValueError("Pulse enqueue results cannot call providers or connectors")
        if self.schedule_activation_allowed:
            raise ValueError("Pulse enqueue results cannot activate schedules")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


def _enqueue_result_log_path(vault: Path, enqueued_at: str) -> Path:
    root = (vault / PULSE_BUS_ENQUEUE_RESULTS_ROOT).resolve()
    path = root / f"{_date_slug(enqueued_at)}-enqueue-results.jsonl"
    _assert_inside(
        path,
        root,
        "Pulse enqueue result logs must stay inside agent-bus-enqueue-results/",
    )
    return path


def _persist_enqueue_result(vault: Path, result: PulseAgentBusEnqueueResult) -> str:
    """Append result record to governed log. Returns relative vault path."""
    result.validate()
    path = _enqueue_result_log_path(vault, result.enqueued_at)
    root = (vault / PULSE_BUS_ENQUEUE_RESULTS_ROOT).resolve()
    _assert_inside(
        path,
        root,
        "Pulse enqueue result logs must stay inside agent-bus-enqueue-results/",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(result.to_dict(), sort_keys=True))
        handle.write("\n")
    return _relative_to_vault(vault, path)


def _duplicate_check(
    vault_root: Path,
    work_fingerprint: str,
    recipient: str,
) -> dict[str, Any] | None:
    """Return the first active task matching this work_fingerprint, or None."""
    if not work_fingerprint:
        return None
    try:
        from runtime.agent_bus import bus
        tasks = bus.list_tasks(vault_root, recipient=recipient)
        for task in tasks:
            if task.get("work_fingerprint") == work_fingerprint:
                if task.get("status") in _ACTIVE_TASK_STATES:
                    return task
    except Exception:
        pass
    return None


def enqueue_pulse_review_task(
    vault_root: str | Path,
    validation_result: PulseAgentBusApprovalValidationResult,
    *,
    enqueued_at: str | None = None,
    skip_duplicate_check: bool = False,
) -> PulseAgentBusEnqueueResult:
    """Enqueue one Pulse REVIEW task after validation passes.

    Requires validation_status == ready_for_final_handoff_review.
    Performs a live duplicate fingerprint check before calling create_task().
    Writes a JSONL result record regardless of enqueue outcome.
    """
    validation_result.validate()
    vault = _vault_path(vault_root)
    ts = enqueued_at or now_utc()

    def _blocked(reason: str) -> PulseAgentBusEnqueueResult:
        result = PulseAgentBusEnqueueResult(
            result_id=_result_id(
                validation_result.validation_id,
                validation_result.candidate_id,
                validation_result.recipient,
                ts,
            ),
            validation_id=validation_result.validation_id,
            request_id=validation_result.request_id,
            candidate_id=validation_result.candidate_id,
            candidate_kind=validation_result.candidate_kind,
            recipient=validation_result.recipient,
            work_fingerprint=validation_result.work_fingerprint,
            result_status=PULSE_BUS_ENQUEUE_RESULT_STATUS_BLOCKED,
            enqueued=False,
            enqueued_at=ts,
            reason=reason,
        )
        result.validate()
        _persist_enqueue_result(vault, result)
        return result

    if validation_result.validation_status != PULSE_BUS_APPROVAL_VALIDATION_STATUS_READY:
        return _blocked(
            f"validation_status is {validation_result.validation_status!r}; "
            f"must be {PULSE_BUS_APPROVAL_VALIDATION_STATUS_READY!r}. "
            f"Missing approvals: {list(validation_result.missing_approvals)}"
        )

    # Duplicate fingerprint check.
    if not skip_duplicate_check and validation_result.work_fingerprint:
        existing = _duplicate_check(vault, validation_result.work_fingerprint, validation_result.recipient)
        if existing is not None:
            result = PulseAgentBusEnqueueResult(
                result_id=_result_id(
                    validation_result.validation_id,
                    validation_result.candidate_id,
                    validation_result.recipient,
                    ts,
                ),
                validation_id=validation_result.validation_id,
                request_id=validation_result.request_id,
                candidate_id=validation_result.candidate_id,
                candidate_kind=validation_result.candidate_kind,
                recipient=validation_result.recipient,
                work_fingerprint=validation_result.work_fingerprint,
                result_status=PULSE_BUS_ENQUEUE_RESULT_STATUS_DUPLICATE,
                enqueued=False,
                enqueued_at=ts,
                duplicate_found=True,
                duplicate_task_id=str(existing.get("task_id") or ""),
                reason=(
                    f"Active task with same work_fingerprint already exists: "
                    f"{existing.get('task_id')} (status={existing.get('status')})"
                ),
            )
            result.validate()
            _persist_enqueue_result(vault, result)
            return result

    # Live bus write.
    try:
        from runtime.agent_bus import bus

        bus_result = bus.create_task(
            vault,
            sender="Operator",
            recipient=validation_result.recipient,
            intent="REVIEW",
            priority="normal",
            request=f"Pulse candidate review: {validation_result.candidate_id} "
                    f"({validation_result.candidate_kind}). "
                    f"Validation ID: {validation_result.validation_id}.",
            expected_output=(
                "Review the Pulse candidate. Record the review decision "
                "in the Agent Bus task result. Do not apply candidates without "
                "explicit operator confirmation."
            ),
            notes=(
                f"pulse_candidate_id={validation_result.candidate_id} "
                f"pulse_candidate_kind={validation_result.candidate_kind} "
                f"pulse_validation_id={validation_result.validation_id} "
                f"pulse_request_id={validation_result.request_id}"
            ),
            work_fingerprint=validation_result.work_fingerprint or None,
            allow_external_sender=True,
        )
    except Exception as exc:
        result = PulseAgentBusEnqueueResult(
            result_id=_result_id(
                validation_result.validation_id,
                validation_result.candidate_id,
                validation_result.recipient,
                ts,
            ),
            validation_id=validation_result.validation_id,
            request_id=validation_result.request_id,
            candidate_id=validation_result.candidate_id,
            candidate_kind=validation_result.candidate_kind,
            recipient=validation_result.recipient,
            work_fingerprint=validation_result.work_fingerprint,
            result_status=PULSE_BUS_ENQUEUE_RESULT_STATUS_BUS_ERROR,
            enqueued=False,
            enqueued_at=ts,
            reason=f"bus.create_task raised: {exc}",
        )
        result.validate()
        _persist_enqueue_result(vault, result)
        return result

    if not bus_result.get("created"):
        result = PulseAgentBusEnqueueResult(
            result_id=_result_id(
                validation_result.validation_id,
                validation_result.candidate_id,
                validation_result.recipient,
                ts,
            ),
            validation_id=validation_result.validation_id,
            request_id=validation_result.request_id,
            candidate_id=validation_result.candidate_id,
            candidate_kind=validation_result.candidate_kind,
            recipient=validation_result.recipient,
            work_fingerprint=validation_result.work_fingerprint,
            result_status=PULSE_BUS_ENQUEUE_RESULT_STATUS_BUS_ERROR,
            enqueued=False,
            enqueued_at=ts,
            reason=f"bus.create_task returned not-created: {bus_result.get('reason', 'unknown')}",
        )
        result.validate()
        _persist_enqueue_result(vault, result)
        return result

    result = PulseAgentBusEnqueueResult(
        result_id=_result_id(
            validation_result.validation_id,
            validation_result.candidate_id,
            validation_result.recipient,
            ts,
        ),
        validation_id=validation_result.validation_id,
        request_id=validation_result.request_id,
        candidate_id=validation_result.candidate_id,
        candidate_kind=validation_result.candidate_kind,
        recipient=validation_result.recipient,
        work_fingerprint=validation_result.work_fingerprint,
        result_status=PULSE_BUS_ENQUEUE_RESULT_STATUS_ENQUEUED,
        enqueued=True,
        enqueued_at=ts,
        task_id=str(bus_result["task_id"]),
        reason="Task created on Agent Bus.",
    )
    result.validate()
    _persist_enqueue_result(vault, result)
    return result


def enqueue_pulse_review_task_by_request_id(
    vault_root: str | Path,
    request_id: str,
    *,
    evidence: PulseAgentBusApprovalValidationEvidence | None = None,
    enqueued_at: str | None = None,
    skip_duplicate_check: bool = False,
) -> PulseAgentBusEnqueueResult:
    """Load a persisted approval request by ID, validate, then enqueue."""
    validation_result = validate_agent_bus_enqueue_approval_request_by_id(
        vault_root,
        request_id,
        evidence=evidence,
        validated_at=enqueued_at,
    )
    return enqueue_pulse_review_task(
        vault_root,
        validation_result,
        enqueued_at=enqueued_at,
        skip_duplicate_check=skip_duplicate_check,
    )


def load_enqueue_results(
    vault_root: str | Path,
    *,
    candidate_id: str | None = None,
    recipient: str | None = None,
    result_status: str | None = None,
) -> list[PulseAgentBusEnqueueResult]:
    """Load enqueue result records read-only. No mutations."""
    vault = _vault_path(vault_root)
    root = (vault / PULSE_BUS_ENQUEUE_RESULTS_ROOT).resolve()
    if not root.exists():
        return []
    results: list[PulseAgentBusEnqueueResult] = []
    for path in sorted(root.glob("*-enqueue-results.jsonl")):
        if not path.exists():
            continue
        _assert_inside(
            path,
            root,
            "Pulse enqueue result logs must stay inside agent-bus-enqueue-results/",
        )
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            r = PulseAgentBusEnqueueResult(
                result_id=str(data.get("result_id") or ""),
                validation_id=str(data.get("validation_id") or ""),
                request_id=str(data.get("request_id") or ""),
                candidate_id=str(data.get("candidate_id") or ""),
                candidate_kind=str(data.get("candidate_kind") or ""),
                recipient=str(data.get("recipient") or ""),
                work_fingerprint=str(data.get("work_fingerprint") or ""),
                result_status=str(data.get("result_status") or ""),
                enqueued=bool(data.get("enqueued", False)),
                enqueued_at=str(data.get("enqueued_at") or now_utc()),
                task_id=data.get("task_id"),
                reason=str(data.get("reason") or ""),
                duplicate_found=bool(data.get("duplicate_found", False)),
                duplicate_task_id=data.get("duplicate_task_id"),
            )
            if candidate_id is not None and r.candidate_id != candidate_id:
                continue
            if recipient is not None and r.recipient != recipient:
                continue
            if result_status is not None and r.result_status != result_status:
                continue
            results.append(r)
    return results
