"""Read-only readiness preflight for future Browser Workflow replay execution.

This module does not execute workflows. It inspects the native ChaseOS workflow
cache and the disabled replay executor, then reports what still blocks a future
approved replay run.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.browser_runtime.workflow_replay_executor import (
    WORKFLOW_REPLAY_EXECUTOR_READY_NO_EXECUTION,
    WorkflowReplayExecutorRequest,
    build_workflow_replay_executor_result,
)
from runtime.browser_runtime.workflow_replay_executor_design import FORBIDDEN_EFFECTS
from runtime.browser_runtime.workflows import (
    WORKFLOW_CACHE_ENTRY_RECORD_TYPE,
    WORKFLOW_CACHE_SCHEMA_VERSION,
    read_workflow_cache_metadata,
    summarize_workflow_cache,
    workflow_cache_entries_dir,
)


WORKFLOW_REPLAY_EXECUTION_READINESS_VERSION = "browser.workflow_replay_execution_readiness.v1"
WORKFLOW_REPLAY_EXECUTION_READINESS_READY = "workflow_replay_execution_readiness_ready_no_execution"
WORKFLOW_REPLAY_EXECUTION_READINESS_BLOCKED_NO_WORKFLOW_AVAILABLE = (
    "workflow_replay_execution_readiness_blocked_no_reviewed_workflow_available"
)
WORKFLOW_REPLAY_EXECUTION_READINESS_BLOCKED_NO_WORKFLOW_SELECTED = (
    "workflow_replay_execution_readiness_blocked_no_workflow_selected"
)
WORKFLOW_REPLAY_EXECUTION_READINESS_BLOCKED = "blocked_workflow_replay_execution_readiness"

REPLAY_READY_WORKFLOW_STATUSES = {
    "reviewed_for_trial",
    "operator_reviewed_inactive",
    "reviewed_inactive",
}

LOCAL_DENIED_EFFECTS = (
    "execution_approval_written",
    "workflow_cache_entry_written",
    "browser_run_log_written",
    "agent_activity_log_written",
    "live_replay_executor_enabled",
    "workflow_replay_execution_attempted",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _entry_paths(vault: Path) -> list[Path]:
    metadata = read_workflow_cache_metadata(vault)
    paths: list[Path] = []
    for item in metadata.get("workflows", []):
        if isinstance(item, dict) and item.get("path"):
            path = Path(str(item["path"]))
            paths.append(path if path.is_absolute() else vault / path)
    entries_dir = workflow_cache_entries_dir(vault)
    if entries_dir.exists():
        paths.extend(sorted(entries_dir.glob("*.workflow.json")))

    unique_paths: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        marker = path.resolve().as_posix() if path.exists() else path.as_posix()
        if marker not in seen:
            unique_paths.append(path)
            seen.add(marker)
    return unique_paths


def _reviewed_replay_workflow_ids(vault: Path) -> list[str]:
    workflow_ids: list[str] = []
    for path in _entry_paths(vault):
        entry = _load_json(path)
        if not isinstance(entry, dict):
            continue
        if (
            entry.get("record_type") == WORKFLOW_CACHE_ENTRY_RECORD_TYPE
            and entry.get("schema_version") == WORKFLOW_CACHE_SCHEMA_VERSION
            and entry.get("status") in REPLAY_READY_WORKFLOW_STATUSES
            and entry.get("replay_allowed") is True
            and entry.get("activation_allowed") is False
            and entry.get("trusted_write_allowed") is False
            and entry.get("external_code_copied") is False
        ):
            workflow_id = str(entry.get("workflow_id") or "")
            if workflow_id:
                workflow_ids.append(workflow_id)
    return sorted(set(workflow_ids))


@dataclass(frozen=True)
class WorkflowReplayExecutionReadinessRequest:
    """Read-only future replay execution readiness request."""

    workflow_id: str = ""
    target_url: str = ""
    allowed_domains: list[str] = field(default_factory=list)
    approval_id: str = ""
    requested_by: str = "Codex"
    enable_validation: bool = True
    request_live_replay: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowReplayExecutionReadiness:
    """Read-only readiness result for a later approved replay execution pass."""

    record_type: str
    version: str
    generated_at: str
    status: str
    workflow_id: str
    target_url: str
    cache_status: str
    workflow_count: int
    reviewed_replay_workflow_ids: list[str]
    executor_status: str
    executor_next_step: str
    request: WorkflowReplayExecutionReadinessRequest
    readiness_checks: dict[str, dict[str, Any]] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    execution_allowed: bool = False
    workflow_replay_attempted: bool = False
    browser_launch_attempted: bool = False
    cdp_connection_attempted: bool = False
    browser_harness_used: bool = False
    browser_use_cli_live_used: bool = False
    real_profile_access_attempted: bool = False
    credential_or_cookie_read_attempted: bool = False
    agent_bus_enqueue_attempted: bool = False
    provider_call_attempted: bool = False
    gate_mutation_attempted: bool = False
    trusted_skill_write_attempted: bool = False
    skill_activation_attempted: bool = False
    canonical_writeback_attempted: bool = False
    external_code_copied: bool = False
    workflow_use_reference_only: bool = True
    denied_effects: dict[str, bool] = field(default_factory=dict)
    next_step: str = "operator_review"

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["request"] = self.request.as_dict()
        return payload

    def validate(self) -> None:
        if self.execution_allowed:
            raise ValueError("execution_allowed must remain false")
        if self.workflow_replay_attempted:
            raise ValueError("workflow_replay_attempted must remain false")
        if self.browser_launch_attempted:
            raise ValueError("browser_launch_attempted must remain false")
        if self.cdp_connection_attempted:
            raise ValueError("cdp_connection_attempted must remain false")
        if self.browser_harness_used:
            raise ValueError("browser_harness_used must remain false")
        if self.browser_use_cli_live_used:
            raise ValueError("browser_use_cli_live_used must remain false")
        if self.real_profile_access_attempted:
            raise ValueError("real_profile_access_attempted must remain false")
        if self.credential_or_cookie_read_attempted:
            raise ValueError("credential_or_cookie_read_attempted must remain false")
        if self.agent_bus_enqueue_attempted:
            raise ValueError("agent_bus_enqueue_attempted must remain false")
        if self.provider_call_attempted:
            raise ValueError("provider_call_attempted must remain false")
        if self.gate_mutation_attempted:
            raise ValueError("gate_mutation_attempted must remain false")
        if self.trusted_skill_write_attempted:
            raise ValueError("trusted_skill_write_attempted must remain false")
        if self.skill_activation_attempted:
            raise ValueError("skill_activation_attempted must remain false")
        if self.canonical_writeback_attempted:
            raise ValueError("canonical_writeback_attempted must remain false")
        if self.external_code_copied:
            raise ValueError("external_code_copied must remain false")
        if not self.workflow_use_reference_only:
            raise ValueError("workflow_use_reference_only must remain true")
        for name in (*FORBIDDEN_EFFECTS, *LOCAL_DENIED_EFFECTS):
            if self.denied_effects.get(name) is not False:
                raise ValueError(f"{name} must remain false")


def build_workflow_replay_execution_readiness(
    vault_root: str | Path,
    request: WorkflowReplayExecutionReadinessRequest | None = None,
    *,
    generated_at: str | None = None,
) -> WorkflowReplayExecutionReadiness:
    """Report future workflow replay execution readiness without execution."""
    timestamp = generated_at or _now_utc()
    vault = _vault_path(vault_root)
    readiness_request = request or WorkflowReplayExecutionReadinessRequest()
    cache = summarize_workflow_cache(vault)
    reviewed_workflow_ids = _reviewed_replay_workflow_ids(vault)
    executor_request = WorkflowReplayExecutorRequest(
        workflow_id=readiness_request.workflow_id,
        target_url=readiness_request.target_url,
        allowed_domains=list(readiness_request.allowed_domains),
        approval_id=readiness_request.approval_id,
        requested_by=readiness_request.requested_by,
        enable_replay_executor=readiness_request.enable_validation,
        run_approved_workflow_replay=readiness_request.request_live_replay,
    )
    executor_result = build_workflow_replay_executor_result(
        vault,
        executor_request,
        generated_at=timestamp,
    )
    cache_ready = cache.get("status") == "cache_foundation_ready"
    workflow_selected = bool(readiness_request.workflow_id)
    reviewed_workflow_available = bool(reviewed_workflow_ids)
    executor_ready = executor_result.status == WORKFLOW_REPLAY_EXECUTOR_READY_NO_EXECUTION
    live_replay_not_requested = readiness_request.request_live_replay is False

    checks = {
        "cache_foundation_ready": {
            "passed": cache_ready,
            "status": cache.get("status"),
        },
        "reviewed_replay_workflow_available": {
            "passed": reviewed_workflow_available,
            "workflow_ids": reviewed_workflow_ids,
        },
        "workflow_selected": {
            "passed": workflow_selected,
            "workflow_id": readiness_request.workflow_id,
        },
        "executor_ready_no_execution": {
            "passed": executor_ready,
            "executor_status": executor_result.status,
            "executor_stop_reasons": executor_result.stop_reasons,
        },
        "live_replay_not_requested": {
            "passed": live_replay_not_requested,
            "request_live_replay": readiness_request.request_live_replay,
        },
        "separate_execution_approval_required": {
            "passed": True,
            "approval_id": readiness_request.approval_id,
        },
        "no_side_effects_in_this_preflight": {
            "passed": True,
            "workflow_replay_attempted": False,
            "browser_launch_attempted": False,
            "cdp_connection_attempted": False,
            "browser_run_log_written": False,
            "agent_activity_log_written": False,
        },
    }
    blockers = [name for name, check in checks.items() if not check["passed"]]
    if not cache_ready:
        status = WORKFLOW_REPLAY_EXECUTION_READINESS_BLOCKED
        next_step = "repair_browser_workflow_cache_foundation"
    elif not reviewed_workflow_available and not workflow_selected:
        status = WORKFLOW_REPLAY_EXECUTION_READINESS_BLOCKED_NO_WORKFLOW_AVAILABLE
        next_step = "create_reviewed_local_workflow_trial_candidate"
    elif not workflow_selected:
        status = WORKFLOW_REPLAY_EXECUTION_READINESS_BLOCKED_NO_WORKFLOW_SELECTED
        next_step = "select_reviewed_workflow_entry_for_trial"
    elif executor_ready and live_replay_not_requested:
        status = WORKFLOW_REPLAY_EXECUTION_READINESS_READY
        next_step = "request_separate_live_workflow_replay_execution_approval"
    else:
        status = WORKFLOW_REPLAY_EXECUTION_READINESS_BLOCKED
        next_step = executor_result.next_step

    readiness = WorkflowReplayExecutionReadiness(
        record_type="browser_workflow_replay_execution_readiness",
        version=WORKFLOW_REPLAY_EXECUTION_READINESS_VERSION,
        generated_at=timestamp,
        status=status,
        workflow_id=readiness_request.workflow_id,
        target_url=readiness_request.target_url,
        cache_status=str(cache.get("status")),
        workflow_count=int(cache.get("workflow_count") or 0),
        reviewed_replay_workflow_ids=reviewed_workflow_ids,
        executor_status=executor_result.status,
        executor_next_step=executor_result.next_step,
        request=readiness_request,
        readiness_checks=checks,
        blockers=blockers,
        execution_allowed=False,
        workflow_replay_attempted=False,
        browser_launch_attempted=False,
        cdp_connection_attempted=False,
        browser_harness_used=False,
        browser_use_cli_live_used=False,
        real_profile_access_attempted=False,
        credential_or_cookie_read_attempted=False,
        agent_bus_enqueue_attempted=False,
        provider_call_attempted=False,
        gate_mutation_attempted=False,
        trusted_skill_write_attempted=False,
        skill_activation_attempted=False,
        canonical_writeback_attempted=False,
        external_code_copied=False,
        workflow_use_reference_only=True,
        denied_effects={name: False for name in (*FORBIDDEN_EFFECTS, *LOCAL_DENIED_EFFECTS)},
        next_step=next_step,
    )
    readiness.validate()
    return readiness


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Report read-only Browser Workflow replay execution readiness.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--workflow-id", default="", help="Reviewed workflow id to preflight for future replay.")
    parser.add_argument("--target-url", default="", help="Optional future replay target URL.")
    parser.add_argument("--allowed-domain", action="append", default=[], help="Allowed future target domain. May be repeated.")
    parser.add_argument("--approval-id", default="", help="Optional future execution approval reference.")
    parser.add_argument("--requested-by", default="Codex", help="Runtime/operator requesting readiness.")
    parser.add_argument("--disable-validation", action="store_true", help="Do not enable the disabled executor's validation posture.")
    parser.add_argument("--request-live-replay", action="store_true", help="Declare a future live replay request; still blocked here.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    request = WorkflowReplayExecutionReadinessRequest(
        workflow_id=args.workflow_id,
        target_url=args.target_url,
        allowed_domains=list(args.allowed_domain or []),
        approval_id=args.approval_id,
        requested_by=args.requested_by,
        enable_validation=not args.disable_validation,
        request_live_replay=args.request_live_replay,
    )
    readiness = build_workflow_replay_execution_readiness(args.vault_root, request)
    payload = readiness.as_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {readiness.status}")
        print(f"workflow_count: {readiness.workflow_count}")
        print(f"reviewed_replay_workflow_ids: {len(readiness.reviewed_replay_workflow_ids)}")
        print(f"next_step: {readiness.next_step}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
