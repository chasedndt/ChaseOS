"""Create a real Pulse approval-artifact chain without live enqueue.

This module turns an existing user Pulse deck into a governed feedback
candidate, Agent Bus approval request, enqueue evidence record, and supervised
enqueue rehearsal packet. It is intentionally conservative: default evidence
does not claim operator/Gate approval, so the final rehearsal remains blocked
until real approval evidence exists.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.bus_enqueue_approval_request import (
    PulseAgentBusEnqueueApprovalArtifact,
    build_agent_bus_enqueue_approval_request_for_candidate,
    persist_agent_bus_enqueue_approval_request,
)
from runtime.pulse.bus_enqueue_evidence import (
    PulseAgentBusEnqueueEvidenceArtifact,
    create_agent_bus_enqueue_evidence_record,
)
from runtime.pulse.card_schema import FEEDBACK_TYPES, now_utc
from runtime.pulse.feedback import (
    PulseFeedbackCandidateArtifact,
    PulseFeedbackRecord,
    persist_feedback_candidate,
)
from runtime.pulse.supervised_live_enqueue_rehearsal import (
    PulseSupervisedLiveEnqueueRehearsal,
    build_supervised_live_enqueue_rehearsal,
)


USER_DECK_ROOT = Path("07_LOGS") / "Pulse-Decks" / "users"
PULSE_REAL_APPROVAL_REHEARSAL_STATUS_READY = "ready_for_operator_manual_enqueue"
PULSE_REAL_APPROVAL_REHEARSAL_STATUS_BLOCKED = "blocked_pending_operator_gate_approval"
PULSE_REAL_APPROVAL_REHEARSAL_STATUSES = {
    PULSE_REAL_APPROVAL_REHEARSAL_STATUS_READY,
    PULSE_REAL_APPROVAL_REHEARSAL_STATUS_BLOCKED,
}
PULSE_REAL_APPROVAL_REHEARSAL_BLOCKED_EFFECTS = (
    "agent_bus_task_write",
    "approval_grant",
    "approval_execution",
    "candidate_apply",
    "canonical_writeback",
    "gate_policy_mutation",
    "memory_approval",
    "provider_or_connector_call",
    "runtime_dispatch",
    "schedule_activation",
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


def _latest_user_deck(vault: Path) -> Path:
    root = (vault / USER_DECK_ROOT).resolve()
    if not root.exists():
        raise ValueError("no user Pulse deck directory exists")
    decks = sorted(root.glob("*-user-pulse.json"), key=lambda path: path.stat().st_mtime)
    if not decks:
        raise ValueError("no user Pulse deck JSON artifacts found")
    deck = decks[-1].resolve()
    _assert_inside(deck, root, "user Pulse deck must stay inside users deck root")
    return deck


def _load_first_card_id(deck_path: Path) -> str:
    data = json.loads(deck_path.read_text(encoding="utf-8"))
    cards = data.get("cards") or []
    if not isinstance(cards, list) or not cards:
        raise ValueError("user Pulse deck has no cards")
    first = cards[0]
    if not isinstance(first, dict):
        raise ValueError("user Pulse deck first card is invalid")
    card_id = str(first.get("card_id") or "")
    if not card_id:
        raise ValueError("user Pulse deck first card has no card_id")
    return card_id


def _run_id(generated_at: str, source_deck_path: str, source_card_id: str) -> str:
    seed = f"{generated_at}|{source_deck_path}|{source_card_id}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    return f"pulse-real-approval-artifact-rehearsal-{digest}"


def _feedback_id(generated_at: str, source_card_id: str) -> str:
    seed = f"real-approval-artifact-rehearsal|{generated_at}|{source_card_id}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    return f"pulse-rehearsal-feedback-{digest}"


@dataclass(frozen=True)
class PulseRealApprovalArtifactRehearsal:
    """Summary of one governed artifact-chain rehearsal."""

    rehearsal_run_id: str
    generated_at: str
    status: str
    source_deck_path: str
    source_card_id: str
    feedback_type: str
    recipient: str
    feedback_candidate_artifact: PulseFeedbackCandidateArtifact
    approval_request_artifact: PulseAgentBusEnqueueApprovalArtifact
    evidence_artifact: PulseAgentBusEnqueueEvidenceArtifact
    supervised_rehearsal: PulseSupervisedLiveEnqueueRehearsal
    created_artifact_paths: tuple[str, ...] = field(default_factory=tuple)
    operator_enqueue_approval_present: bool = False
    gate_policy_defined: bool = False
    external_sender_allowance_present: bool = False
    duplicate_work_fingerprint_reviewed: bool = False
    artifact_chain_created: bool = True
    approval_granted: bool = False
    approval_executed: bool = False
    live_enqueue_executed: bool = False
    agent_bus_task_written: bool = False
    runtime_dispatch_allowed: bool = False
    review_response_ingest_allowed: bool = False
    candidate_apply_allowed: bool = False
    canonical_writeback_allowed: bool = False
    mutates_canonical_state: bool = False
    second_datastore_write_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    schedule_activation_allowed: bool = False
    blocked_effects: tuple[str, ...] = PULSE_REAL_APPROVAL_REHEARSAL_BLOCKED_EFFECTS

    @property
    def ready_for_manual_enqueue(self) -> bool:
        return self.status == PULSE_REAL_APPROVAL_REHEARSAL_STATUS_READY

    def validate(self) -> None:
        if not self.rehearsal_run_id:
            raise ValueError("rehearsal_run_id is required")
        if self.status not in PULSE_REAL_APPROVAL_REHEARSAL_STATUSES:
            raise ValueError("invalid real approval artifact rehearsal status")
        if not self.source_deck_path:
            raise ValueError("source_deck_path is required")
        if not self.source_card_id:
            raise ValueError("source_card_id is required")
        if self.feedback_type not in FEEDBACK_TYPES:
            raise ValueError("invalid feedback_type")
        if not self.recipient:
            raise ValueError("recipient is required")
        self.feedback_candidate_artifact.validate()
        self.approval_request_artifact.validate()
        self.evidence_artifact.validate()
        self.supervised_rehearsal.validate()
        if self.status == PULSE_REAL_APPROVAL_REHEARSAL_STATUS_READY:
            if not self.supervised_rehearsal.ready_for_manual_enqueue:
                raise ValueError("ready artifact rehearsal requires ready supervised rehearsal")
        else:
            if self.supervised_rehearsal.ready_for_manual_enqueue:
                raise ValueError("blocked artifact rehearsal cannot contain ready supervised rehearsal")
        if not self.created_artifact_paths:
            raise ValueError("created_artifact_paths are required")
        if not self.artifact_chain_created:
            raise ValueError("artifact rehearsal must create its artifact chain")
        if self.approval_granted:
            raise ValueError("artifact rehearsal cannot grant approval")
        if self.approval_executed:
            raise ValueError("artifact rehearsal cannot execute approval")
        if self.live_enqueue_executed:
            raise ValueError("artifact rehearsal cannot execute live enqueue")
        if self.agent_bus_task_written:
            raise ValueError("artifact rehearsal cannot write Agent Bus tasks")
        if self.runtime_dispatch_allowed:
            raise ValueError("artifact rehearsal cannot dispatch runtimes")
        if self.review_response_ingest_allowed:
            raise ValueError("artifact rehearsal cannot ingest review responses")
        if self.candidate_apply_allowed:
            raise ValueError("artifact rehearsal cannot apply candidates")
        if self.canonical_writeback_allowed:
            raise ValueError("artifact rehearsal cannot allow canonical writeback")
        if self.mutates_canonical_state:
            raise ValueError("artifact rehearsal cannot mutate canonical state")
        if self.second_datastore_write_allowed:
            raise ValueError("artifact rehearsal cannot write a second datastore")
        if self.provider_or_connector_call_allowed:
            raise ValueError("artifact rehearsal cannot call providers or connectors")
        if self.schedule_activation_allowed:
            raise ValueError("artifact rehearsal cannot activate schedules")
        if set(self.blocked_effects) != set(PULSE_REAL_APPROVAL_REHEARSAL_BLOCKED_EFFECTS):
            raise ValueError("artifact rehearsal must declare blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["ready_for_manual_enqueue"] = self.ready_for_manual_enqueue
        payload["feedback_candidate_artifact"] = self.feedback_candidate_artifact.to_dict()
        payload["approval_request_artifact"] = self.approval_request_artifact.to_dict()
        payload["evidence_artifact"] = self.evidence_artifact.to_dict()
        payload["supervised_rehearsal"] = self.supervised_rehearsal.to_dict()
        payload["created_artifact_paths"] = list(self.created_artifact_paths)
        payload["blocked_effects"] = list(self.blocked_effects)
        return payload


def run_real_approval_artifact_rehearsal(
    vault_root: str | Path,
    *,
    source_deck_path: str | Path | None = None,
    source_card_id: str | None = None,
    feedback_type: str = "show_more_like_this",
    operator_note: str | None = None,
    recipient: str = "Hermes",
    requested_by: str = "codex",
    reviewer: str = "operator",
    operator_enqueue_approval_present: bool = False,
    gate_policy_defined: bool = False,
    external_sender_allowance_present: bool = False,
    duplicate_work_fingerprint_reviewed: bool = False,
    generated_at: str | None = None,
) -> PulseRealApprovalArtifactRehearsal:
    """Create candidate/request/evidence artifacts and run dry rehearsal.

    Defaults intentionally leave all approval evidence flags false. Passing
    them as true should only be done by an explicitly approved operator flow.
    """
    vault = _vault_path(vault_root)
    timestamp = generated_at or now_utc()

    deck = Path(source_deck_path) if source_deck_path is not None else _latest_user_deck(vault)
    deck = deck if deck.is_absolute() else vault / deck
    deck = deck.resolve()
    _assert_inside(
        deck,
        (vault / USER_DECK_ROOT).resolve(),
        "real approval rehearsal source deck must stay inside user Pulse deck root",
    )
    if not deck.exists() or not deck.is_file():
        raise ValueError("real approval rehearsal source deck does not exist")

    card_id = source_card_id or _load_first_card_id(deck)
    deck_ref = _relative_to_vault(vault, deck)
    note = operator_note or (
        "Codex-created rehearsal feedback candidate for Pulse Agent Bus approval "
        "artifact chain. This is pending review and does not claim approval."
    )

    record = PulseFeedbackRecord(
        feedback_id=_feedback_id(timestamp, card_id),
        card_id=card_id,
        feedback_type=feedback_type,
        operator_note=note,
        created_at=timestamp,
    )
    feedback_artifact = persist_feedback_candidate(
        vault,
        record,
        source_deck_path=deck_ref,
    )

    request = build_agent_bus_enqueue_approval_request_for_candidate(
        vault,
        feedback_artifact.candidate_id,
        recipient=recipient,
        requested_by=requested_by,
        requested_at=timestamp,
    )
    request_artifact = persist_agent_bus_enqueue_approval_request(vault, request)

    evidence_note = (
        "Real artifact-chain rehearsal evidence. Approval flags reflect only "
        "explicit inputs; default run records missing operator/Gate approval."
    )
    evidence_record, evidence_artifact = create_agent_bus_enqueue_evidence_record(
        vault,
        request.request_id,
        reviewer=reviewer,
        operator_enqueue_approval_present=operator_enqueue_approval_present,
        gate_policy_defined=gate_policy_defined,
        external_sender_allowance_present=external_sender_allowance_present,
        duplicate_work_fingerprint_reviewed=duplicate_work_fingerprint_reviewed,
        evidence_note=evidence_note,
        gate_policy_ref=(
            "06_AGENTS/Pulse-Feedback-Policy.md#next-pass"
            if gate_policy_defined
            else None
        ),
        external_sender_allowance_ref=(
            "HERMES.md#current-local-truth"
            if external_sender_allowance_present
            else None
        ),
        duplicate_review_ref=(
            "07_LOGS/Agent-Activity/pulse-duplicate-fingerprint-review.md"
            if duplicate_work_fingerprint_reviewed
            else None
        ),
        created_at=timestamp,
    )

    supervised = build_supervised_live_enqueue_rehearsal(
        vault,
        request.request_id,
        evidence_id=evidence_record.evidence_id,
        generated_at=timestamp,
        bus_tasks=[],
    )
    status = (
        PULSE_REAL_APPROVAL_REHEARSAL_STATUS_READY
        if supervised.ready_for_manual_enqueue
        else PULSE_REAL_APPROVAL_REHEARSAL_STATUS_BLOCKED
    )
    result = PulseRealApprovalArtifactRehearsal(
        rehearsal_run_id=_run_id(timestamp, deck_ref, card_id),
        generated_at=timestamp,
        status=status,
        source_deck_path=deck_ref,
        source_card_id=card_id,
        feedback_type=feedback_type,
        recipient=recipient,
        feedback_candidate_artifact=feedback_artifact,
        approval_request_artifact=request_artifact,
        evidence_artifact=evidence_artifact,
        supervised_rehearsal=supervised,
        created_artifact_paths=(
            feedback_artifact.path,
            request_artifact.path,
            evidence_artifact.path,
        ),
        operator_enqueue_approval_present=operator_enqueue_approval_present,
        gate_policy_defined=gate_policy_defined,
        external_sender_allowance_present=external_sender_allowance_present,
        duplicate_work_fingerprint_reviewed=duplicate_work_fingerprint_reviewed,
    )
    result.validate()
    return result
