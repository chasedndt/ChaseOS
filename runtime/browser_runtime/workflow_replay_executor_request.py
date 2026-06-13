"""No-execution implementation request for a future workflow replay executor.

This module does not implement replay. It converts the existing replay-executor
design preflight into a review packet for a future ChaseOS-native patch.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.browser_runtime.workflow_replay_executor_design import (
    FORBIDDEN_EFFECTS,
    WORKFLOW_REPLAY_EXECUTOR_STATUS_READY,
    build_workflow_replay_executor_design,
)


WORKFLOW_REPLAY_IMPLEMENTATION_REQUEST_VERSION = "browser.workflow_replay_implementation_request.v1"
WORKFLOW_REPLAY_IMPLEMENTATION_REQUEST_READY = "workflow_replay_executor_implementation_request_ready_no_write"
WORKFLOW_REPLAY_IMPLEMENTATION_REQUEST_BLOCKED = "blocked_before_workflow_replay_executor_implementation_request"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _request_id(timestamp: str) -> str:
    clean = "".join(ch.lower() if ch.isalnum() else "-" for ch in timestamp)
    return "workflow-replay-executor-implementation-request-" + "-".join(part for part in clean.split("-") if part)


@dataclass(frozen=True)
class WorkflowReplayExecutorImplementationRequest:
    """Review packet for a future replay executor implementation pass."""

    record_type: str
    version: str
    generated_at: str
    request_id: str
    status: str
    design_status: str
    request_ready_no_write: bool
    implementation_allowed_in_this_pass: bool
    implementation_request_artifact_written: bool
    external_code_copied: bool
    workflow_use_reference_only: bool
    implementation_strategy: str
    readiness_checks: dict[str, dict[str, Any]] = field(default_factory=dict)
    proposed_patch_scope: list[str] = field(default_factory=list)
    required_tests: list[str] = field(default_factory=list)
    required_guardrails: list[str] = field(default_factory=list)
    future_write_flags_required: list[str] = field(default_factory=list)
    denied_effects: dict[str, bool] = field(default_factory=dict)
    next_step: str = "operator_review"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def validate(self) -> None:
        if self.implementation_allowed_in_this_pass:
            raise ValueError("implementation_allowed_in_this_pass must remain false")
        if self.implementation_request_artifact_written:
            raise ValueError("implementation_request_artifact_written must remain false")
        if self.external_code_copied:
            raise ValueError("external_code_copied must remain false")
        if not self.workflow_use_reference_only:
            raise ValueError("workflow_use_reference_only must remain true")
        for name in FORBIDDEN_EFFECTS:
            if self.denied_effects.get(name) is not False:
                raise ValueError(f"{name} must remain false")


def build_workflow_replay_executor_implementation_request(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
) -> WorkflowReplayExecutorImplementationRequest:
    """Build a no-write implementation request packet for operator review."""
    timestamp = generated_at or _now_utc()
    design = build_workflow_replay_executor_design(vault_root, generated_at=timestamp)
    design_ready = design.status == WORKFLOW_REPLAY_EXECUTOR_STATUS_READY
    no_external_code_copy = design.external_code_copied is False and design.workflow_use_reference_only is True
    implementation_disabled = True
    checks = {
        "design_preflight_ready": {
            "passed": design_ready,
            "status": design.status,
        },
        "native_cache_foundation_ready": {
            "passed": design.cache_status == "cache_foundation_ready",
            "status": design.cache_status,
        },
        "external_code_copy_forbidden": {
            "passed": no_external_code_copy,
            "strategy": design.implementation_strategy,
        },
        "implementation_still_disabled": {
            "passed": implementation_disabled,
            "implementation_allowed_in_this_pass": False,
        },
        "replay_execution_still_disabled": {
            "passed": True,
            "workflow_replay_attempted": False,
        },
    }
    request_ready = all(bool(item["passed"]) for item in checks.values())
    status = (
        WORKFLOW_REPLAY_IMPLEMENTATION_REQUEST_READY
        if request_ready
        else WORKFLOW_REPLAY_IMPLEMENTATION_REQUEST_BLOCKED
    )
    request = WorkflowReplayExecutorImplementationRequest(
        record_type="browser_workflow_replay_executor_implementation_request",
        version=WORKFLOW_REPLAY_IMPLEMENTATION_REQUEST_VERSION,
        generated_at=timestamp,
        request_id=_request_id(timestamp),
        status=status,
        design_status=design.status,
        request_ready_no_write=request_ready,
        implementation_allowed_in_this_pass=False,
        implementation_request_artifact_written=False,
        external_code_copied=False,
        workflow_use_reference_only=True,
        implementation_strategy=design.implementation_strategy,
        readiness_checks=checks,
        proposed_patch_scope=[
            "runtime/browser_runtime/workflow_replay_executor.py",
            "runtime/browser_runtime/test_workflow_replay_executor.py",
            "06_AGENTS/Browser-Workflow-Replay-Executor.md",
            "completion-status and tracker updates",
        ],
        required_tests=[
            "module import guard: no external workflow/browser automation/CDP imports in executor request",
            "blocked when workflow entry is inactive/unreviewed",
            "blocked when allowed domain check fails",
            "blocked when step requires credentials/cookies/real profile/payment/account mutation",
            "blocked when artifact target is outside Browser Run or Agent Activity logs",
            "no-execution smoke keeps all denied effects false",
        ],
        required_guardrails=[
            "operator approval required before implementation patch",
            "separate approval required before any execution-capable code path is enabled",
            "throwaway or isolated browser profile required for live trials",
            "AOR manifest and Gate allowance required before browser actions",
            "idempotency reservation required before any future replay run",
            "review-only repair candidate on mismatch or failure",
            "no external code copy from workflow-use or Browser Harness",
        ],
        future_write_flags_required=[
            "--write-replay-implementation-approval",
            "--enable-replay-executor",
            "--run-approved-workflow-replay",
        ],
        denied_effects={name: False for name in FORBIDDEN_EFFECTS},
        next_step="workflow-replay-executor-implementation-approval" if request_ready else "workflow-replay-executor-design-preflight",
    )
    request.validate()
    return request


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Report no-write Browser Workflow replay executor implementation request.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    request = build_workflow_replay_executor_implementation_request(args.vault_root)
    payload = request.as_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {request.status}")
        print(f"request_ready_no_write: {request.request_ready_no_write}")
        print(f"next_step: {request.next_step}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
