"""No-write approval packet for a future workflow replay executor patch.

This module does not implement replay. It records whether the existing
implementation request is ready for a later bounded implementation pass.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.browser_runtime.workflow_replay_executor_design import FORBIDDEN_EFFECTS
from runtime.browser_runtime.workflow_replay_executor_request import (
    WORKFLOW_REPLAY_IMPLEMENTATION_REQUEST_READY,
    build_workflow_replay_executor_implementation_request,
)


WORKFLOW_REPLAY_IMPLEMENTATION_APPROVAL_VERSION = "browser.workflow_replay_implementation_approval.v1"
WORKFLOW_REPLAY_IMPLEMENTATION_APPROVAL_READY = "workflow_replay_executor_implementation_approval_ready_no_write"
WORKFLOW_REPLAY_IMPLEMENTATION_APPROVAL_REJECTED = "workflow_replay_executor_implementation_rejected_no_write"
WORKFLOW_REPLAY_IMPLEMENTATION_APPROVAL_BLOCKED = "blocked_before_workflow_replay_executor_implementation_approval"
VALID_WORKFLOW_REPLAY_APPROVAL_DECISIONS = {"approve", "reject"}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _approval_id(timestamp: str, decision: str) -> str:
    clean = "".join(ch.lower() if ch.isalnum() else "-" for ch in timestamp)
    timestamp_part = "-".join(part for part in clean.split("-") if part)
    return f"workflow-replay-executor-implementation-{decision}-{timestamp_part}"


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            unique_values.append(value)
    return unique_values


@dataclass(frozen=True)
class WorkflowReplayExecutorImplementationApproval:
    """Review-only approval packet for a future replay executor implementation."""

    record_type: str
    version: str
    generated_at: str
    approval_id: str
    operator_id: str
    decision: str
    status: str
    implementation_request_id: str
    implementation_request_status: str
    implementation_request_ready_no_write: bool
    implementation_approved_for_future_patch: bool
    implementation_allowed_in_this_pass: bool
    approval_artifact_written: bool
    replay_execution_allowed: bool
    external_code_copied: bool
    workflow_use_reference_only: bool
    readiness_checks: dict[str, dict[str, Any]] = field(default_factory=dict)
    approved_patch_scope: list[str] = field(default_factory=list)
    required_preimplementation_checks: list[str] = field(default_factory=list)
    required_guardrails: list[str] = field(default_factory=list)
    future_write_flags_required: list[str] = field(default_factory=list)
    denied_effects: dict[str, bool] = field(default_factory=dict)
    next_step: str = "operator_review"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def validate(self) -> None:
        if self.decision not in VALID_WORKFLOW_REPLAY_APPROVAL_DECISIONS:
            raise ValueError("invalid workflow replay implementation approval decision")
        if self.implementation_allowed_in_this_pass:
            raise ValueError("implementation_allowed_in_this_pass must remain false")
        if self.approval_artifact_written:
            raise ValueError("approval_artifact_written must remain false")
        if self.replay_execution_allowed:
            raise ValueError("replay_execution_allowed must remain false")
        if self.external_code_copied:
            raise ValueError("external_code_copied must remain false")
        if not self.workflow_use_reference_only:
            raise ValueError("workflow_use_reference_only must remain true")
        for name in FORBIDDEN_EFFECTS:
            if self.denied_effects.get(name) is not False:
                raise ValueError(f"{name} must remain false")
        if self.implementation_approved_for_future_patch:
            request_ready = (
                self.decision == "approve"
                and self.implementation_request_ready_no_write
                and self.implementation_request_status == WORKFLOW_REPLAY_IMPLEMENTATION_REQUEST_READY
            )
            if not request_ready:
                raise ValueError("future patch approval requires a ready no-write implementation request")
        if self.decision == "reject" and self.approved_patch_scope:
            raise ValueError("rejected implementation approvals cannot include approved patch scope")


def build_workflow_replay_executor_implementation_approval(
    vault_root: str | Path,
    *,
    decision: str = "approve",
    operator_id: str = "operator",
    generated_at: str | None = None,
) -> WorkflowReplayExecutorImplementationApproval:
    """Build a no-write implementation approval packet for operator review."""
    timestamp = generated_at or _now_utc()
    normalized_decision = decision.strip().lower()
    if normalized_decision not in VALID_WORKFLOW_REPLAY_APPROVAL_DECISIONS:
        raise ValueError("decision must be approve or reject")

    request = build_workflow_replay_executor_implementation_request(
        vault_root,
        generated_at=timestamp,
    )
    request_ready = (
        request.status == WORKFLOW_REPLAY_IMPLEMENTATION_REQUEST_READY
        and request.request_ready_no_write is True
    )
    approve_decision = normalized_decision == "approve"
    approved_for_future_patch = approve_decision and request_ready
    checks = {
        "implementation_request_ready": {
            "passed": request_ready,
            "status": request.status,
        },
        "operator_decision_valid": {
            "passed": True,
            "decision": normalized_decision,
        },
        "approval_is_review_only": {
            "passed": True,
            "approval_artifact_written": False,
        },
        "implementation_still_disabled": {
            "passed": True,
            "implementation_allowed_in_this_pass": False,
        },
        "replay_execution_still_disabled": {
            "passed": True,
            "replay_execution_allowed": False,
        },
        "external_code_copy_forbidden": {
            "passed": request.external_code_copied is False and request.workflow_use_reference_only is True,
            "workflow_use_reference_only": True,
        },
    }
    if normalized_decision == "reject":
        status = WORKFLOW_REPLAY_IMPLEMENTATION_APPROVAL_REJECTED
        next_step = "workflow-replay-executor-implementation-request"
    elif approved_for_future_patch:
        status = WORKFLOW_REPLAY_IMPLEMENTATION_APPROVAL_READY
        next_step = "workflow-replay-executor-implementation-patch"
    else:
        status = WORKFLOW_REPLAY_IMPLEMENTATION_APPROVAL_BLOCKED
        next_step = "workflow-replay-executor-implementation-request"

    approval = WorkflowReplayExecutorImplementationApproval(
        record_type="browser_workflow_replay_executor_implementation_approval",
        version=WORKFLOW_REPLAY_IMPLEMENTATION_APPROVAL_VERSION,
        generated_at=timestamp,
        approval_id=_approval_id(timestamp, normalized_decision),
        operator_id=operator_id,
        decision=normalized_decision,
        status=status,
        implementation_request_id=request.request_id,
        implementation_request_status=request.status,
        implementation_request_ready_no_write=request_ready,
        implementation_approved_for_future_patch=approved_for_future_patch,
        implementation_allowed_in_this_pass=False,
        approval_artifact_written=False,
        replay_execution_allowed=False,
        external_code_copied=False,
        workflow_use_reference_only=True,
        readiness_checks=checks,
        approved_patch_scope=list(request.proposed_patch_scope) if approved_for_future_patch else [],
        required_preimplementation_checks=_unique(
            [
                "re-run implementation request and keep status ready_no_write",
                *request.required_tests,
                "separate execution approval remains required before any replay run",
            ]
        ),
        required_guardrails=_unique(
            [
                *request.required_guardrails,
                "approval packet remains review-only until an explicit write flag exists",
                "executor implementation must default to disabled/no execution",
            ]
        ),
        future_write_flags_required=_unique(
            [
                "--write-replay-implementation-approval",
                *request.future_write_flags_required,
            ]
        ),
        denied_effects={name: False for name in FORBIDDEN_EFFECTS},
        next_step=next_step,
    )
    approval.validate()
    return approval


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Report no-write Browser Workflow replay executor implementation approval.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--decision", choices=sorted(VALID_WORKFLOW_REPLAY_APPROVAL_DECISIONS), default="approve")
    parser.add_argument("--operator-id", default="operator", help="Operator identifier recorded in the review packet.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    approval = build_workflow_replay_executor_implementation_approval(
        args.vault_root,
        decision=args.decision,
        operator_id=args.operator_id,
    )
    payload = approval.as_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {approval.status}")
        print(f"implementation_approved_for_future_patch: {approval.implementation_approved_for_future_patch}")
        print(f"next_step: {approval.next_step}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
