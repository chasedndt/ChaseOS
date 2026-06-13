"""Read-only ChaseOS Pulse completion status.

This module reports whether Pulse is done from repo-local evidence. It does not
write status artifacts, enqueue Agent Bus tasks, apply candidates, mutate
memory, activate schedules, call providers/connectors, or update the R&D
workbook.
"""

from __future__ import annotations

import json
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.bus_enqueue import load_enqueue_results
from runtime.pulse.bus_enqueue_evidence import load_agent_bus_enqueue_evidence_records
from runtime.pulse.card_schema import now_utc
from runtime.pulse.feedback import load_feedback_candidates
from runtime.pulse.review_decision_log import load_review_decisions


PULSE_COMPLETION_OVERALL_PARTIAL = "partial"
PULSE_COMPLETION_OVERALL_BACKEND_PROOF_PENDING = "backend_proof_pending"
PULSE_COMPLETION_OVERALL_PHASE10_UI_PENDING = "phase10_ui_pending"
PULSE_COMPLETION_OVERALL_COMPLETE = "complete"
PULSE_COMPLETION_STATUSES = {
    PULSE_COMPLETION_OVERALL_PARTIAL,
    PULSE_COMPLETION_OVERALL_BACKEND_PROOF_PENDING,
    PULSE_COMPLETION_OVERALL_PHASE10_UI_PENDING,
    PULSE_COMPLETION_OVERALL_COMPLETE,
}

PULSE_COMPLETION_BLOCKED_EFFECTS = (
    "agent_bus_task_write",
    "approval_grant",
    "approval_execution",
    "candidate_apply",
    "canonical_writeback",
    "memory_approval",
    "provider_or_connector_call",
    "rd_workbook_update",
    "runtime_dispatch",
    "schedule_activation",
)

POST_COMPLETION_APPROVAL_REQUIRED_FOR = (
    "schedule_activation",
    "provider_or_connector_call",
    "canonical_writeback",
    "rd_workbook_update",
    "full_studio_product_ui_or_deployment",
)

POST_APPLY_TRUTH_STATE_AUDIT_PATH = "06_AGENTS/ChaseOS-Pulse-Post-Apply-Truth-State-Audit.md"
RND_WORKBOOK_UPDATE_APPROVAL_PATH = "06_AGENTS/ChaseOS-Pulse-RnD-Workbook-Update-Approval.md"
NATIVE_SCHEDULE_ACTIVATION_CATCHUP_PROOF_PATH = (
    "06_AGENTS/ChaseOS-Pulse-Native-Schedule-Activation-Catchup-Proof.md"
)
PHASE10_UI_PROOF_PATH = "06_AGENTS/ChaseOS-Pulse-Phase10-UI-Proof.md"
PHASE10_UI_APP_PATH = "runtime/studio/shell/api.py"
RND_WORKBOOK_PATH = "99_ARCHIVE/Reporting/ChaseOS_RnD_Canonical_Full_2026-04-28.xlsx"
RND_WORKBOOK_SYNC_REQUIRED_TERMS = (
    "FR-028",
    "F176",
    "F198",
    "FIT-132",
    "FIT-139",
    "CH-1005",
    "ChaseOS Pulse",
)


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _exists(vault: Path, relative_path: str) -> bool:
    return (vault / relative_path).exists()


def _glob_exists(vault: Path, pattern: str) -> bool:
    return any(vault.glob(pattern))


def _load_applied_decision_ids(vault: Path) -> set[str]:
    path = vault / "07_LOGS" / "Pulse-Decks" / "apply-registry" / "applied-decisions.json"
    if not path.exists():
        return set()
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return set()
    raw_ids = parsed.get("applied_decision_ids") if isinstance(parsed, dict) else None
    if not isinstance(raw_ids, list):
        return set()
    return {str(item) for item in raw_ids if item}


def _xlsx_contains_terms(path: Path, terms: tuple[str, ...]) -> bool:
    if not path.exists():
        return False
    found: set[str] = set()
    try:
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if not name.endswith(".xml"):
                    continue
                text = archive.read(name).decode("utf-8", errors="ignore")
                for term in terms:
                    if term in text:
                        found.add(term)
                if len(found) == len(terms):
                    return True
    except Exception:
        return False
    return False


def _build_post_completion_hardening_status(feature_done: bool) -> dict[str, Any]:
    """Return the read-only post-completion hardening boundary."""
    return {
        "status": "ready" if feature_done else "blocked_until_feature_complete",
        "recommended_pass": "chaseos-pulse-post-completion-hardening" if feature_done else "complete-current-pulse-proof-chain-first",
        "read_only_hardening_allowed": bool(feature_done),
        "requires_operator_permission_for_read_only_hardening": False,
        "current_pass_permission_request": "not_required",
        "approval_required_for": list(POST_COMPLETION_APPROVAL_REQUIRED_FOR),
        "notes": (
            "Read-only post-completion hardening can inspect and reconcile proof surfaces without another permission request. "
            "Any schedule activation, provider/connector call, canonical writeback, workbook update, or broad Studio/product UI deployment still requires an explicit future approval."
            if feature_done
            else "Post-completion hardening waits until the current Pulse proof chain reports feature_done=true."
        ),
    }


@dataclass(frozen=True)
class PulseCompletionStatusItem:
    area: str
    status: str
    evidence: str
    complete_for_feature_done: bool
    notes: str = ""

    def validate(self) -> None:
        if not self.area:
            raise ValueError("completion item area is required")
        if self.status not in {"complete", "partial", "missing", "blocked", "not_built"}:
            raise ValueError("invalid completion item status")
        if not self.evidence:
            raise ValueError("completion item evidence is required")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class PulseCompletionStatus:
    generated_at: str
    overall_status: str
    feature_done: bool
    backend_control_plane_done: bool
    next_recommended_pass: str
    blocked_reasons: tuple[str, ...]
    items: tuple[PulseCompletionStatusItem, ...]
    approval_request_id: str | None = None
    evidence_id: str | None = None
    enqueue_result_count: int = 0
    review_decision_count: int = 0
    live_enqueue_proof_observed: bool = False
    agent_bus_task_write_proof_observed: bool = False
    review_decision_proof_observed: bool = False
    read_only: bool = True
    writes_status_artifact: bool = False
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
    blocked_effects: tuple[str, ...] = PULSE_COMPLETION_BLOCKED_EFFECTS
    post_completion_hardening: dict[str, Any] = field(default_factory=dict)

    @property
    def item_count(self) -> int:
        return len(self.items)

    def validate(self) -> None:
        if self.overall_status not in PULSE_COMPLETION_STATUSES:
            raise ValueError("invalid Pulse completion overall_status")
        if self.feature_done and self.overall_status != PULSE_COMPLETION_OVERALL_COMPLETE:
            raise ValueError("feature_done requires complete overall_status")
        if self.feature_done and not self.backend_control_plane_done:
            raise ValueError("feature_done requires backend_control_plane_done")
        if not self.next_recommended_pass:
            raise ValueError("next_recommended_pass is required")
        for item in self.items:
            item.validate()
        if not self.read_only:
            raise ValueError("Pulse completion status must remain read-only")
        if self.writes_status_artifact:
            raise ValueError("Pulse completion status cannot write status artifacts")
        if self.approval_granted:
            raise ValueError("Pulse completion status cannot grant approval")
        if self.live_enqueue_executed:
            raise ValueError("Pulse completion status cannot execute live enqueue")
        if self.agent_bus_task_written:
            raise ValueError("Pulse completion status cannot write Agent Bus tasks")
        if self.runtime_dispatch_allowed:
            raise ValueError("Pulse completion status cannot dispatch runtimes")
        if self.review_response_ingest_allowed:
            raise ValueError("Pulse completion status cannot ingest review responses")
        if self.candidate_apply_allowed:
            raise ValueError("Pulse completion status cannot apply candidates")
        if self.canonical_writeback_allowed:
            raise ValueError("Pulse completion status cannot allow canonical writeback")
        if self.mutates_canonical_state:
            raise ValueError("Pulse completion status cannot mutate canonical state")
        if self.provider_or_connector_call_allowed:
            raise ValueError("Pulse completion status cannot call providers or connectors")
        if self.schedule_activation_allowed:
            raise ValueError("Pulse completion status cannot activate schedules")
        if self.rd_workbook_update_allowed:
            raise ValueError("Pulse completion status cannot update the R&D workbook")
        if set(self.blocked_effects) != set(PULSE_COMPLETION_BLOCKED_EFFECTS):
            raise ValueError("Pulse completion status must declare blocked effects")
        if self.post_completion_hardening:
            hardening = self.post_completion_hardening
            if hardening.get("current_pass_permission_request") != "not_required":
                raise ValueError("post-completion hardening cannot claim a permission request")
            if hardening.get("requires_operator_permission_for_read_only_hardening"):
                raise ValueError("read-only post-completion hardening cannot require operator permission")
            if set(hardening.get("approval_required_for", ())) != set(POST_COMPLETION_APPROVAL_REQUIRED_FOR):
                raise ValueError("post-completion hardening must list approval-required followups")
            if hardening.get("read_only_hardening_allowed") and not self.feature_done:
                raise ValueError("read-only post-completion hardening requires feature_done")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "overall_status": self.overall_status,
            "feature_done": self.feature_done,
            "backend_control_plane_done": self.backend_control_plane_done,
            "next_recommended_pass": self.next_recommended_pass,
            "blocked_reasons": list(self.blocked_reasons),
            "item_count": self.item_count,
            "items": [item.to_dict() for item in self.items],
            "approval_request_id": self.approval_request_id,
            "evidence_id": self.evidence_id,
            "enqueue_result_count": self.enqueue_result_count,
            "review_decision_count": self.review_decision_count,
            "live_enqueue_proof_observed": self.live_enqueue_proof_observed,
            "agent_bus_task_write_proof_observed": self.agent_bus_task_write_proof_observed,
            "review_decision_proof_observed": self.review_decision_proof_observed,
            "read_only": self.read_only,
            "writes_status_artifact": self.writes_status_artifact,
            "approval_granted": self.approval_granted,
            "live_enqueue_executed": self.live_enqueue_executed,
            "agent_bus_task_written": self.agent_bus_task_written,
            "runtime_dispatch_allowed": self.runtime_dispatch_allowed,
            "review_response_ingest_allowed": self.review_response_ingest_allowed,
            "candidate_apply_allowed": self.candidate_apply_allowed,
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "mutates_canonical_state": self.mutates_canonical_state,
            "provider_or_connector_call_allowed": self.provider_or_connector_call_allowed,
            "schedule_activation_allowed": self.schedule_activation_allowed,
            "rd_workbook_update_allowed": self.rd_workbook_update_allowed,
            "blocked_effects": list(self.blocked_effects),
            "post_completion_hardening": self.post_completion_hardening,
        }


def build_pulse_completion_status(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
) -> PulseCompletionStatus:
    """Build a read-only completion status from repo-local Pulse evidence."""
    vault = _vault_path(vault_root)
    timestamp = generated_at or now_utc()

    feedback_candidates = load_feedback_candidates(vault)
    evidence_records = load_agent_bus_enqueue_evidence_records(vault)
    enqueue_results = load_enqueue_results(vault)
    review_decisions = load_review_decisions(vault)
    applied_decision_ids = _load_applied_decision_ids(vault)
    review_decision_ids = {decision.decision_id for decision in review_decisions}
    applied_review_decision_ids = applied_decision_ids & review_decision_ids
    candidate_apply_complete = bool(applied_review_decision_ids)
    post_apply_audit_complete = _exists(vault, POST_APPLY_TRUTH_STATE_AUDIT_PATH)
    rnd_workbook_approval_packet_complete = _exists(vault, RND_WORKBOOK_UPDATE_APPROVAL_PATH)
    rnd_workbook_sync_complete = _xlsx_contains_terms(
        vault / RND_WORKBOOK_PATH,
        RND_WORKBOOK_SYNC_REQUIRED_TERMS,
    )
    native_schedule_catchup_proof_complete = _exists(
        vault, NATIVE_SCHEDULE_ACTIVATION_CATCHUP_PROOF_PATH
    )
    phase10_ui_complete = _exists(vault, PHASE10_UI_PROOF_PATH) and _exists(
        vault, PHASE10_UI_APP_PATH
    )

    latest_evidence = evidence_records[-1] if evidence_records else None
    enqueued_results = [result for result in enqueue_results if result.enqueued]
    enqueued_results_with_task_ids = [result for result in enqueued_results if result.task_id]
    review_decision_proof_observed = bool(review_decisions)
    missing_approvals = (
        tuple(latest_evidence.validation_evidence.missing_approvals)
        if latest_evidence is not None
        else (
            "operator_enqueue_approval",
            "gate_policy_defined",
            "external_sender_allowance",
            "duplicate_work_fingerprint_review",
        )
    )

    items = (
        PulseCompletionStatusItem(
            area="architecture",
            status="partial" if _exists(vault, "06_AGENTS/ChaseOS-Pulse-Architecture.md") else "missing",
            evidence="06_AGENTS/ChaseOS-Pulse-Architecture.md",
            complete_for_feature_done=False,
            notes="Architecture exists but feature completion requires live proof.",
        ),
        PulseCompletionStatusItem(
            area="backend_deck",
            status="partial" if _glob_exists(vault, "07_LOGS/Pulse-Decks/users/*-user-pulse.json") else "missing",
            evidence="07_LOGS/Pulse-Decks/users/*-user-pulse.json",
            complete_for_feature_done=False,
            notes="Deck artifacts exist; generation breadth and live schedule proof remain partial.",
        ),
        PulseCompletionStatusItem(
            area="candidate_artifact_chain",
            status="partial" if feedback_candidates and latest_evidence else "missing",
            evidence="07_LOGS/Pulse-Decks/feedback-candidates/ + agent-bus-enqueue-evidence/",
            complete_for_feature_done=False,
            notes=f"{len(feedback_candidates)} feedback candidate(s), {len(evidence_records)} evidence record(s).",
        ),
        PulseCompletionStatusItem(
            area="approval_evidence",
            status="blocked" if missing_approvals else "complete",
            evidence="latest Pulse enqueue evidence record",
            complete_for_feature_done=not bool(missing_approvals),
            notes="missing=" + ",".join(missing_approvals) if missing_approvals else "all required approvals present",
        ),
        PulseCompletionStatusItem(
            area="agent_bus_review_enqueue",
            status="complete" if enqueued_results else "blocked",
            evidence="07_LOGS/Pulse-Decks/agent-bus-enqueue-results/",
            complete_for_feature_done=bool(enqueued_results),
            notes=f"{len(enqueued_results)} enqueued Pulse REVIEW result(s).",
        ),
        PulseCompletionStatusItem(
            area="review_response_ingest",
            status="complete" if review_decisions else "blocked",
            evidence="07_LOGS/Pulse-Decks/review-decisions/",
            complete_for_feature_done=bool(review_decisions),
            notes=f"{len(review_decisions)} review decision record(s).",
        ),
        PulseCompletionStatusItem(
            area="candidate_apply",
            status="complete" if candidate_apply_complete else "blocked",
            evidence="07_LOGS/Pulse-Decks/apply-registry/applied-decisions.json",
            complete_for_feature_done=candidate_apply_complete,
            notes=(
                f"{len(applied_review_decision_ids)} applied review decision(s) in "
                "non-canonical runtime-memory apply registry."
                if candidate_apply_complete
                else "No approved live Pulse candidate apply proof in this status."
            ),
        ),
        PulseCompletionStatusItem(
            area="post_apply_truth_state_audit",
            status="complete" if post_apply_audit_complete else "blocked",
            evidence=POST_APPLY_TRUTH_STATE_AUDIT_PATH,
            complete_for_feature_done=post_apply_audit_complete,
            notes=(
                "Post-apply truth-state audit exists."
                if post_apply_audit_complete
                else "Post-apply truth-state audit has not been recorded yet."
            ),
        ),
        PulseCompletionStatusItem(
            area="rd_workbook_approval_packet",
            status="complete" if rnd_workbook_approval_packet_complete else "blocked",
            evidence=RND_WORKBOOK_UPDATE_APPROVAL_PATH,
            complete_for_feature_done=False,
            notes=(
                "No-write R&D workbook approval packet exists and workbook sync row markers are present."
                if rnd_workbook_sync_complete
                else "No-write R&D workbook approval packet exists; workbook sync still requires explicit operator approval."
                if rnd_workbook_approval_packet_complete
                else "No-write R&D workbook approval packet has not been recorded yet."
            ),
        ),
        PulseCompletionStatusItem(
            area="native_schedule_activation_proof",
            status="complete" if native_schedule_catchup_proof_complete else "blocked",
            evidence=NATIVE_SCHEDULE_ACTIVATION_CATCHUP_PROOF_PATH,
            complete_for_feature_done=native_schedule_catchup_proof_complete,
            notes=(
                "Native schedule/catch-up proof packet exists; this is proof-only and does not activate schedules."
                if native_schedule_catchup_proof_complete
                else "Native schedule intent exists, but live schedule activation and missed-run/catch-up proof are not complete."
            ),
        ),
        PulseCompletionStatusItem(
            area="phase10_ui",
            status="complete" if phase10_ui_complete else "not_built",
            evidence=PHASE10_UI_PROOF_PATH,
            complete_for_feature_done=phase10_ui_complete,
            notes=(
                "Local Pulse deck app and UI proof exist; this closes the current Pulse UI foothold without claiming full Studio desktop."
                if phase10_ui_complete
                else "Full visual UI remains Phase 10."
            ),
        ),
        PulseCompletionStatusItem(
            area="rd_workbook",
            status="complete" if rnd_workbook_sync_complete else "blocked",
            evidence=RND_WORKBOOK_PATH,
            complete_for_feature_done=rnd_workbook_sync_complete,
            notes=(
                "R&D workbook contains the Pulse sync row markers."
                if rnd_workbook_sync_complete
                else "Workbook update is deferred until approval after live proof."
            ),
        ),
    )

    blocked_reasons: list[str] = []
    if missing_approvals:
        blocked_reasons.extend(f"missing:{approval}" for approval in missing_approvals)
    if not enqueued_results:
        blocked_reasons.append("no_live_pulse_review_enqueue")
    if not review_decisions:
        blocked_reasons.append("no_real_review_response_ingest")
    if not candidate_apply_complete:
        blocked_reasons.append("no_approved_candidate_apply")
    if not post_apply_audit_complete:
        blocked_reasons.append("post_apply_truth_state_audit_not_done")
    if not rnd_workbook_approval_packet_complete:
        blocked_reasons.append("rd_workbook_approval_packet_not_done")
    if not rnd_workbook_sync_complete:
        blocked_reasons.append("rd_workbook_not_updated")
    if not native_schedule_catchup_proof_complete:
        blocked_reasons.append("native_schedule_activation_catchup_proof_not_done")
    if not phase10_ui_complete:
        blocked_reasons.append("phase10_ui_not_built")

    backend_control_plane_done = (
        candidate_apply_complete
        and post_apply_audit_complete
        and rnd_workbook_approval_packet_complete
        and rnd_workbook_sync_complete
        and native_schedule_catchup_proof_complete
    )

    feature_done = backend_control_plane_done and phase10_ui_complete
    overall_status = PULSE_COMPLETION_OVERALL_BACKEND_PROOF_PENDING

    if feature_done:
        next_recommended_pass = "chaseos-pulse-post-completion-hardening"
        overall_status = PULSE_COMPLETION_OVERALL_COMPLETE
    elif backend_control_plane_done:
        next_recommended_pass = "chaseos-pulse-phase10-ui"
        overall_status = PULSE_COMPLETION_OVERALL_PHASE10_UI_PENDING
    elif (
        candidate_apply_complete
        and post_apply_audit_complete
        and rnd_workbook_approval_packet_complete
        and rnd_workbook_sync_complete
    ):
        next_recommended_pass = "chaseos-pulse-native-schedule-activation-catchup-proof"
    elif candidate_apply_complete and post_apply_audit_complete and rnd_workbook_approval_packet_complete:
        next_recommended_pass = "chaseos-pulse-rnd-workbook-sync-after-operator-approval"
    elif candidate_apply_complete and post_apply_audit_complete:
        next_recommended_pass = "chaseos-pulse-rnd-workbook-update-approval"
    elif candidate_apply_complete:
        next_recommended_pass = "chaseos-pulse-post-apply-truth-state-audit"
    elif review_decision_proof_observed:
        next_recommended_pass = "chaseos-pulse-candidate-apply-approval-contract"
    else:
        next_recommended_pass = "chaseos-pulse-review-response-ingest-and-apply-proof"

    status = PulseCompletionStatus(
        generated_at=timestamp,
        overall_status=overall_status,
        feature_done=feature_done,
        backend_control_plane_done=backend_control_plane_done,
        next_recommended_pass=next_recommended_pass,
        blocked_reasons=tuple(blocked_reasons),
        items=items,
        approval_request_id=(
            latest_evidence.request_id if latest_evidence is not None else None
        ),
        evidence_id=(latest_evidence.evidence_id if latest_evidence is not None else None),
        enqueue_result_count=len(enqueue_results),
        review_decision_count=len(review_decisions),
        live_enqueue_proof_observed=bool(enqueued_results),
        agent_bus_task_write_proof_observed=bool(enqueued_results_with_task_ids),
        review_decision_proof_observed=review_decision_proof_observed,
        post_completion_hardening=_build_post_completion_hardening_status(feature_done),
    )
    status.validate()
    return status
