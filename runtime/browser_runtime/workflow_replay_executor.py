"""Disabled-by-default Browser Workflow replay executor.

This is the first ChaseOS-native executor implementation patch. It validates
cached workflow entries and reports what would be required before replay, but it
does not execute browser actions or write run artifacts.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.browser_runtime.models import domain_from_url, slugify
from runtime.browser_runtime.workflow_replay_executor_design import FORBIDDEN_EFFECTS
from runtime.browser_runtime.workflows import (
    FORBIDDEN_ACTION_TYPES,
    WORKFLOW_CACHE_ENTRY_RECORD_TYPE,
    WORKFLOW_CACHE_SCHEMA_VERSION,
    read_workflow_cache_metadata,
    summarize_workflow_cache,
    workflow_cache_entries_dir,
)


WORKFLOW_REPLAY_EXECUTOR_VERSION = "browser.workflow_replay_executor.v1"
WORKFLOW_REPLAY_EXECUTOR_DISABLED_NO_WORKFLOW = "workflow_replay_executor_disabled_no_workflow_selected"
WORKFLOW_REPLAY_EXECUTOR_DISABLED_NO_EXECUTION = "workflow_replay_executor_disabled_no_execution"
WORKFLOW_REPLAY_EXECUTOR_READY_NO_EXECUTION = "workflow_replay_executor_ready_no_execution"
WORKFLOW_REPLAY_EXECUTOR_BLOCKED = "blocked_workflow_replay_executor"
WORKFLOW_REPLAY_EXECUTOR_EXECUTION_DEFERRED = "blocked_live_workflow_replay_execution_deferred"

REVIEWED_WORKFLOW_STATUSES = {
    "reviewed_inactive",
    "operator_reviewed_inactive",
    "reviewed_for_trial",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _workflow_run_id(workflow_id: str, timestamp: str) -> str:
    clean_time = "".join(ch.lower() if ch.isalnum() else "-" for ch in timestamp)
    return "workflow-replay-" + slugify(workflow_id, "unselected-workflow") + "-" + slugify(clean_time, "time")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _candidate_entry_paths(vault: Path, workflow_id: str, metadata: dict[str, Any]) -> list[Path]:
    paths: list[Path] = []
    for item in metadata.get("workflows", []):
        if isinstance(item, dict) and item.get("workflow_id") == workflow_id and item.get("path"):
            candidate = Path(str(item["path"]))
            paths.append(candidate if candidate.is_absolute() else vault / candidate)
    paths.append(workflow_cache_entries_dir(vault) / f"{slugify(workflow_id, 'browser-workflow')}.workflow.json")
    return paths


def _load_workflow_entry(vault: Path, workflow_id: str) -> tuple[dict[str, Any] | None, str]:
    if not workflow_id:
        return None, ""
    metadata = read_workflow_cache_metadata(vault)
    for path in _candidate_entry_paths(vault, workflow_id, metadata):
        try:
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8")), path.as_posix()
        except (OSError, json.JSONDecodeError):
            return None, path.as_posix()
    return None, ""


def _target_domain(entry: dict[str, Any] | None, target_url: str) -> str:
    if target_url:
        return domain_from_url(target_url)
    if isinstance(entry, dict):
        source_url = str(entry.get("source_url") or "")
        return domain_from_url(source_url) or str(entry.get("domain") or "")
    return ""


@dataclass(frozen=True)
class WorkflowReplayExecutorRequest:
    """Read-only request for the disabled replay executor."""

    workflow_id: str = ""
    target_url: str = ""
    allowed_domains: list[str] = field(default_factory=list)
    approval_id: str = ""
    requested_by: str = "Codex"
    enable_replay_executor: bool = False
    run_approved_workflow_replay: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowReplayStepPlan:
    """One planned workflow step that remains unexecuted."""

    step_id: str
    action_type: str
    target: str
    source_action_index: int
    status: str = "planned_not_executed"
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowReplayExecutorResult:
    """Read-only replay executor result."""

    record_type: str
    version: str
    generated_at: str
    status: str
    run_id: str
    workflow_id: str
    workflow_entry_path: str
    target_url: str
    target_domain: str
    request: WorkflowReplayExecutorRequest
    checks: dict[str, dict[str, Any]] = field(default_factory=dict)
    stop_reasons: list[str] = field(default_factory=list)
    planned_steps: list[WorkflowReplayStepPlan] = field(default_factory=list)
    executor_enabled: bool = False
    execution_requested: bool = False
    execution_allowed: bool = False
    workflow_replay_attempted: bool = False
    replay_artifacts_written: bool = False
    external_code_copied: bool = False
    workflow_use_reference_only: bool = True
    denied_effects: dict[str, bool] = field(default_factory=dict)
    next_step: str = "operator_review"

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["request"] = self.request.as_dict()
        payload["planned_steps"] = [step.as_dict() for step in self.planned_steps]
        return payload

    def validate(self) -> None:
        if self.execution_allowed:
            raise ValueError("execution_allowed must remain false")
        if self.workflow_replay_attempted:
            raise ValueError("workflow_replay_attempted must remain false")
        if self.replay_artifacts_written:
            raise ValueError("replay_artifacts_written must remain false")
        if self.external_code_copied:
            raise ValueError("external_code_copied must remain false")
        if not self.workflow_use_reference_only:
            raise ValueError("workflow_use_reference_only must remain true")
        for name in FORBIDDEN_EFFECTS:
            if self.denied_effects.get(name) is not False:
                raise ValueError(f"{name} must remain false")


def build_workflow_replay_executor_result(
    vault_root: str | Path,
    request: WorkflowReplayExecutorRequest,
    *,
    generated_at: str | None = None,
) -> WorkflowReplayExecutorResult:
    """Validate a cached workflow for replay without executing it."""
    timestamp = generated_at or _now_utc()
    vault = _vault_path(vault_root)
    cache = summarize_workflow_cache(vault)
    entry, entry_path = _load_workflow_entry(vault, request.workflow_id)
    target_domain = _target_domain(entry, request.target_url)
    entry_domains = list(entry.get("allowed_domains") or []) if isinstance(entry, dict) else []
    allowed_domains = request.allowed_domains or entry_domains
    steps = entry.get("steps", []) if isinstance(entry, dict) else []
    forbidden_step_actions = [
        str(step.get("action_type"))
        for step in steps
        if isinstance(step, dict) and step.get("action_type") in FORBIDDEN_ACTION_TYPES
    ]
    planned_steps = [
        WorkflowReplayStepPlan(
            step_id=str(step.get("step_id") or f"step_{index + 1:02d}"),
            action_type=str(step.get("action_type") or ""),
            target=str(step.get("target") or ""),
            source_action_index=int(step.get("source_action_index") or index),
            notes=str(step.get("notes") or ""),
        )
        for index, step in enumerate(steps)
        if isinstance(step, dict)
    ]
    checks = {
        "cache_foundation_ready": {
            "passed": cache.get("status") == "cache_foundation_ready",
            "status": cache.get("status"),
        },
        "workflow_selected": {
            "passed": bool(request.workflow_id),
            "workflow_id": request.workflow_id,
        },
        "workflow_entry_found": {
            "passed": isinstance(entry, dict),
            "path": entry_path,
        },
        "workflow_entry_schema_valid": {
            "passed": isinstance(entry, dict)
            and entry.get("record_type") == WORKFLOW_CACHE_ENTRY_RECORD_TYPE
            and entry.get("schema_version") == WORKFLOW_CACHE_SCHEMA_VERSION,
            "record_type": entry.get("record_type") if isinstance(entry, dict) else None,
            "schema_version": entry.get("schema_version") if isinstance(entry, dict) else None,
        },
        "workflow_entry_reviewed": {
            "passed": isinstance(entry, dict) and entry.get("status") in REVIEWED_WORKFLOW_STATUSES,
            "status": entry.get("status") if isinstance(entry, dict) else None,
        },
        "workflow_entry_replay_allowed": {
            "passed": isinstance(entry, dict) and entry.get("replay_allowed") is True,
            "replay_allowed": entry.get("replay_allowed") if isinstance(entry, dict) else None,
        },
        "target_domain_allowed": {
            "passed": bool(target_domain) and target_domain in allowed_domains,
            "target_domain": target_domain,
            "allowed_domains": allowed_domains,
        },
        "forbidden_steps_absent": {
            "passed": not forbidden_step_actions,
            "forbidden_step_actions": forbidden_step_actions,
        },
        "executor_enabled": {
            "passed": request.enable_replay_executor,
            "enable_replay_executor": request.enable_replay_executor,
        },
        "live_execution_deferred": {
            "passed": not request.run_approved_workflow_replay,
            "run_approved_workflow_replay": request.run_approved_workflow_replay,
        },
    }
    stop_reasons = [name for name, check in checks.items() if not check["passed"]]
    if not request.workflow_id:
        status = WORKFLOW_REPLAY_EXECUTOR_DISABLED_NO_WORKFLOW
        next_step = "select_reviewed_workflow_entry"
    elif any(reason not in {"executor_enabled", "live_execution_deferred"} for reason in stop_reasons):
        status = WORKFLOW_REPLAY_EXECUTOR_BLOCKED
        next_step = "repair_or_review_workflow_entry"
    elif not request.enable_replay_executor:
        status = WORKFLOW_REPLAY_EXECUTOR_DISABLED_NO_EXECUTION
        next_step = "operator_enable_replay_executor_for_no_execution_trial"
    elif request.run_approved_workflow_replay:
        status = WORKFLOW_REPLAY_EXECUTOR_EXECUTION_DEFERRED
        next_step = "separate_execution_approval_and_live_executor_pass"
    else:
        status = WORKFLOW_REPLAY_EXECUTOR_READY_NO_EXECUTION
        next_step = "separate_workflow_replay_execution_approval"

    result = WorkflowReplayExecutorResult(
        record_type="browser_workflow_replay_executor_result",
        version=WORKFLOW_REPLAY_EXECUTOR_VERSION,
        generated_at=timestamp,
        status=status,
        run_id=_workflow_run_id(request.workflow_id, timestamp),
        workflow_id=request.workflow_id,
        workflow_entry_path=entry_path,
        target_url=request.target_url or (str(entry.get("source_url") or "") if isinstance(entry, dict) else ""),
        target_domain=target_domain,
        request=request,
        checks=checks,
        stop_reasons=stop_reasons,
        planned_steps=planned_steps,
        executor_enabled=request.enable_replay_executor,
        execution_requested=request.run_approved_workflow_replay,
        execution_allowed=False,
        workflow_replay_attempted=False,
        replay_artifacts_written=False,
        external_code_copied=False,
        workflow_use_reference_only=True,
        denied_effects={name: False for name in FORBIDDEN_EFFECTS},
        next_step=next_step,
    )
    result.validate()
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a cached Browser Workflow replay request without executing it.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--workflow-id", default="", help="Workflow cache entry id to validate.")
    parser.add_argument("--target-url", default="", help="Optional replay target URL.")
    parser.add_argument("--allowed-domain", action="append", default=[], help="Allowed target domain. May be repeated.")
    parser.add_argument("--approval-id", default="", help="Future approval id reference.")
    parser.add_argument("--requested-by", default="Codex", help="Runtime/operator requesting validation.")
    parser.add_argument("--enable-replay-executor", action="store_true", help="Enable validation posture only; still no execution.")
    parser.add_argument("--run-approved-workflow-replay", action="store_true", help="Request live replay; blocked in this pass.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    request = WorkflowReplayExecutorRequest(
        workflow_id=args.workflow_id,
        target_url=args.target_url,
        allowed_domains=list(args.allowed_domain or []),
        approval_id=args.approval_id,
        requested_by=args.requested_by,
        enable_replay_executor=args.enable_replay_executor,
        run_approved_workflow_replay=args.run_approved_workflow_replay,
    )
    result = build_workflow_replay_executor_result(args.vault_root, request)
    payload = result.as_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {result.status}")
        print(f"workflow_id: {result.workflow_id or '<none>'}")
        print(f"next_step: {result.next_step}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
