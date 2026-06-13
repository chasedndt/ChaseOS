"""Pulse Agent Bus enqueue pipeline runner.

Orchestrates the full Pulse→Bus submission flow:
  1. Build an enqueue plan (candidate → contracts → preflights)
  2. In dry_run mode: return previews only — no bus calls, no approval writes
  3. In live mode: persist approval requests, validate explicit evidence, call
     bus.create_task() for each candidate only if validation is ready

All governance flags on PulseEnqueuePipelineResult are immutably False:
candidate apply, canonical writeback, memory mutation, provider calls, and
schedule activation are not pipeline runner concerns.

Governance constraints:
- dry_run=True (default) performs zero writes
- live mode persists approval requests, then validates four separate evidence
  flags: operator approval, Gate policy, external-sender allowance, and
  duplicate-work-fingerprint review
- operator_approved=True proves only the operator-approval evidence flag; it
  does not imply Gate policy, external-sender allowance, or duplicate review
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.bus_enqueue import (
    PulseAgentBusEnqueueResult,
    enqueue_pulse_review_task,
)
from runtime.pulse.bus_enqueue_approval_request import (
    build_agent_bus_enqueue_approval_request,
    persist_agent_bus_enqueue_approval_request,
)
from runtime.pulse.bus_enqueue_approval_validation import (
    PulseAgentBusApprovalValidationEvidence,
    validate_agent_bus_enqueue_approval_request,
)
from runtime.pulse.bus_enqueue_design import (
    PULSE_BUS_ALLOWED_REVIEW_RECIPIENTS,
    build_agent_bus_enqueue_plan,
)
from runtime.pulse.card_schema import now_utc


PULSE_PIPELINE_RUNNER_STATUS_DRY_RUN = "dry_run"
PULSE_PIPELINE_RUNNER_STATUS_LIVE = "live"
PULSE_PIPELINE_RUNNER_STATUSES = {
    PULSE_PIPELINE_RUNNER_STATUS_DRY_RUN,
    PULSE_PIPELINE_RUNNER_STATUS_LIVE,
}


@dataclass
class PulseEnqueuePipelineResult:
    """Summary result for one pipeline runner invocation."""

    run_at: str
    pipeline_status: str
    dry_run: bool
    operator_approved: bool
    plan_preflight_count: int
    gate_policy_defined: bool = False
    external_sender_allowance_present: bool = False
    duplicate_work_fingerprint_reviewed: bool = False
    enqueue_results: list[PulseAgentBusEnqueueResult] = field(default_factory=list)
    dry_run_previews: list[dict[str, Any]] = field(default_factory=list)

    # Governance flags — always False
    candidate_apply_allowed: bool = False
    canonical_writeback_allowed: bool = False
    mutates_canonical_state: bool = False
    second_datastore_write_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    schedule_activation_allowed: bool = False
    review_response_ingest_allowed: bool = False

    @property
    def enqueued_count(self) -> int:
        return sum(1 for r in self.enqueue_results if r.result_status == "enqueued")

    @property
    def blocked_count(self) -> int:
        return sum(1 for r in self.enqueue_results if r.result_status == "blocked")

    @property
    def duplicate_count(self) -> int:
        return sum(1 for r in self.enqueue_results if r.result_status == "duplicate_skipped")

    @property
    def bus_error_count(self) -> int:
        return sum(1 for r in self.enqueue_results if r.result_status == "bus_error")

    def validate(self) -> None:
        if self.pipeline_status not in PULSE_PIPELINE_RUNNER_STATUSES:
            raise ValueError("invalid pipeline_status")
        if self.dry_run and self.enqueue_results:
            raise ValueError("dry_run pipeline cannot have live enqueue results")
        if not self.dry_run and self.dry_run_previews:
            raise ValueError("live pipeline should not populate dry_run_previews")
        if self.candidate_apply_allowed:
            raise ValueError("pipeline runner cannot apply candidates")
        if self.canonical_writeback_allowed:
            raise ValueError("pipeline runner cannot allow canonical writeback")
        if self.mutates_canonical_state:
            raise ValueError("pipeline runner cannot mutate canonical state")
        if self.second_datastore_write_allowed:
            raise ValueError("pipeline runner cannot write a second datastore")
        if self.provider_or_connector_call_allowed:
            raise ValueError("pipeline runner cannot call providers or connectors")
        if self.schedule_activation_allowed:
            raise ValueError("pipeline runner cannot activate schedules")
        if self.review_response_ingest_allowed:
            raise ValueError("pipeline runner cannot ingest review responses")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "run_at": self.run_at,
            "pipeline_status": self.pipeline_status,
            "dry_run": self.dry_run,
            "operator_approved": self.operator_approved,
            "gate_policy_defined": self.gate_policy_defined,
            "external_sender_allowance_present": self.external_sender_allowance_present,
            "duplicate_work_fingerprint_reviewed": self.duplicate_work_fingerprint_reviewed,
            "plan_preflight_count": self.plan_preflight_count,
            "enqueued_count": self.enqueued_count,
            "blocked_count": self.blocked_count,
            "duplicate_count": self.duplicate_count,
            "bus_error_count": self.bus_error_count,
            "enqueue_results": [r.to_dict() for r in self.enqueue_results],
            "dry_run_previews": self.dry_run_previews,
            "candidate_apply_allowed": self.candidate_apply_allowed,
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "mutates_canonical_state": self.mutates_canonical_state,
            "second_datastore_write_allowed": self.second_datastore_write_allowed,
            "provider_or_connector_call_allowed": self.provider_or_connector_call_allowed,
            "schedule_activation_allowed": self.schedule_activation_allowed,
            "review_response_ingest_allowed": self.review_response_ingest_allowed,
        }


def _pipeline_evidence(
    run_at: str,
    *,
    operator_approved: bool,
    gate_policy_defined: bool,
    external_sender_allowance_present: bool,
    duplicate_work_fingerprint_reviewed: bool,
) -> PulseAgentBusApprovalValidationEvidence:
    return PulseAgentBusApprovalValidationEvidence(
        operator_enqueue_approval_present=operator_approved,
        gate_policy_defined=gate_policy_defined,
        external_sender_allowance_present=external_sender_allowance_present,
        duplicate_work_fingerprint_reviewed=duplicate_work_fingerprint_reviewed,
        reviewer="operator",
        evidence_note=(
            "pipeline evidence flags at "
            f"{run_at}: operator_approved={operator_approved}, "
            f"gate_policy_defined={gate_policy_defined}, "
            "external_sender_allowance_present="
            f"{external_sender_allowance_present}, "
            "duplicate_work_fingerprint_reviewed="
            f"{duplicate_work_fingerprint_reviewed}"
        ),
    )


def run_pulse_enqueue_pipeline(
    vault_root: str | Path,
    *,
    operator_approved: bool = False,
    gate_policy_defined: bool = False,
    external_sender_allowance_present: bool = False,
    duplicate_work_fingerprint_reviewed: bool = False,
    dry_run: bool = True,
    candidate_kinds: set[str] | None = None,
    candidate_id: str | None = None,
    default_recipient: str = "Hermes",
    recipient_by_candidate_kind: dict[str, str] | None = None,
    limit: int | None = None,
    skip_duplicate_check: bool = False,
    run_at: str | None = None,
) -> PulseEnqueuePipelineResult:
    """Run the Pulse Agent Bus enqueue pipeline.

    Args:
        vault_root: ChaseOS vault root path.
        operator_approved: If True, sets only the operator-approval evidence
            flag. Gate policy, external-sender allowance, and duplicate-review
            evidence must be provided separately.
        gate_policy_defined: Evidence flag for the required Gate policy.
        external_sender_allowance_present: Evidence flag for allowing the
            Operator sender handoff into Agent Bus REVIEW tasks.
        duplicate_work_fingerprint_reviewed: Evidence flag that duplicate-work
            fingerprint handling was reviewed before live enqueue.
        dry_run: If True (default), only builds the enqueue plan and returns
            task payload previews — no bus calls, no approval request writes.
        candidate_kinds: Filter preflights by candidate kind. None = all kinds.
        candidate_id: Filter to a single candidate. None = all candidates.
        default_recipient: Default review recipient for candidates. Must be one
            of PULSE_BUS_ALLOWED_REVIEW_RECIPIENTS.
        recipient_by_candidate_kind: Override recipient per candidate kind.
        limit: Cap on number of preflights to process.
        skip_duplicate_check: Passed through to enqueue_pulse_review_task().
        run_at: ISO timestamp override (for testing).
    """
    if default_recipient not in PULSE_BUS_ALLOWED_REVIEW_RECIPIENTS:
        raise ValueError(
            f"default_recipient must be one of {PULSE_BUS_ALLOWED_REVIEW_RECIPIENTS}"
        )

    timestamp = run_at or now_utc()

    plan = build_agent_bus_enqueue_plan(
        vault_root,
        candidate_kinds=candidate_kinds,
        candidate_id=candidate_id,
        default_recipient=default_recipient,
        recipient_by_candidate_kind=recipient_by_candidate_kind,
        limit=limit,
        created_at=timestamp,
    )

    if dry_run:
        previews = [preflight.to_task_payload_preview() for preflight in plan.preflights]
        result = PulseEnqueuePipelineResult(
            run_at=timestamp,
            pipeline_status=PULSE_PIPELINE_RUNNER_STATUS_DRY_RUN,
            dry_run=True,
            operator_approved=operator_approved,
            gate_policy_defined=gate_policy_defined,
            external_sender_allowance_present=external_sender_allowance_present,
            duplicate_work_fingerprint_reviewed=duplicate_work_fingerprint_reviewed,
            plan_preflight_count=plan.preflight_count,
            dry_run_previews=previews,
        )
        result.validate()
        return result

    # Live mode: persist approval request + validate + enqueue for each preflight
    evidence = _pipeline_evidence(
        timestamp,
        operator_approved=operator_approved,
        gate_policy_defined=gate_policy_defined,
        external_sender_allowance_present=external_sender_allowance_present,
        duplicate_work_fingerprint_reviewed=duplicate_work_fingerprint_reviewed,
    )

    enqueue_results: list[PulseAgentBusEnqueueResult] = []
    for preflight in plan.preflights:
        try:
            request = build_agent_bus_enqueue_approval_request(
                preflight,
                requested_by="operator",
                requested_at=timestamp,
            )
            persist_agent_bus_enqueue_approval_request(vault_root, request)
            validation = validate_agent_bus_enqueue_approval_request(
                request,
                evidence=evidence,
                validated_at=timestamp,
            )
            enqueue_result = enqueue_pulse_review_task(
                vault_root,
                validation,
                enqueued_at=timestamp,
                skip_duplicate_check=skip_duplicate_check,
            )
        except Exception as exc:  # noqa: BLE001
            from runtime.pulse.bus_enqueue import (
                PULSE_BUS_ENQUEUE_RESULT_STATUS_BUS_ERROR,
                PulseAgentBusEnqueueResult,
            )
            enqueue_result = PulseAgentBusEnqueueResult(
                result_id=f"pipeline-error-{preflight.preflight_id[:16]}",
                candidate_id=preflight.candidate_id,
                candidate_kind=preflight.candidate_kind,
                request_id=f"pipeline-error-{preflight.preflight_id[:16]}",
                validation_id=f"pipeline-error-{preflight.preflight_id[:16]}",
                recipient=preflight.recipient,
                work_fingerprint=preflight.work_fingerprint,
                result_status=PULSE_BUS_ENQUEUE_RESULT_STATUS_BUS_ERROR,
                enqueued=False,
                enqueued_at=timestamp,
                reason=str(exc),
            )
            enqueue_result.validate()
            _persist_error_result(vault_root, enqueue_result)

        enqueue_results.append(enqueue_result)

    result = PulseEnqueuePipelineResult(
        run_at=timestamp,
        pipeline_status=PULSE_PIPELINE_RUNNER_STATUS_LIVE,
        dry_run=False,
        operator_approved=operator_approved,
        gate_policy_defined=gate_policy_defined,
        external_sender_allowance_present=external_sender_allowance_present,
        duplicate_work_fingerprint_reviewed=duplicate_work_fingerprint_reviewed,
        plan_preflight_count=plan.preflight_count,
        enqueue_results=enqueue_results,
    )
    result.validate()
    return result


def _persist_error_result(
    vault_root: str | Path,
    result: PulseAgentBusEnqueueResult,
) -> None:
    """Persist a pipeline-level error result to the enqueue results JSONL."""
    import json
    from runtime.pulse.bus_enqueue import (
        _enqueue_result_log_path,
    )
    path = _enqueue_result_log_path(Path(vault_root), result.enqueued_at)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(result.to_dict(), sort_keys=True))
        handle.write("\n")
