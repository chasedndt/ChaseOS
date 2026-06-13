"""No-write approval and idempotency contract for workflow replay execution.

This module prepares the governance shape for one future local workflow replay
trial. It validates the selected workflow through the existing no-execution
readiness path, builds a pending approval-request preview, and computes the
single-attempt idempotency marker path. It does not write either artifact and it
does not execute browser actions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.browser_runtime.models import domain_from_url, slugify
from runtime.browser_runtime.workflow_replay_execution_readiness import (
    WORKFLOW_REPLAY_EXECUTION_READINESS_READY,
    WorkflowReplayExecutionReadinessRequest,
    build_workflow_replay_execution_readiness,
)
from runtime.browser_runtime.workflow_replay_executor import (
    WORKFLOW_REPLAY_EXECUTOR_READY_NO_EXECUTION,
    WorkflowReplayExecutorRequest,
    build_workflow_replay_executor_result,
)
from runtime.browser_runtime.workflow_replay_executor_design import FORBIDDEN_EFFECTS


WORKFLOW_REPLAY_EXECUTION_APPROVAL_VERSION = "browser.workflow_replay_execution_approval.v1"
WORKFLOW_REPLAY_EXECUTION_APPROVAL_READY = "workflow_replay_execution_approval_ready_no_execution"
WORKFLOW_REPLAY_EXECUTION_APPROVAL_BLOCKED = "blocked_workflow_replay_execution_approval"
WORKFLOW_REPLAY_EXECUTION_APPROVAL_BLOCKED_MARKER_EXISTS = (
    "workflow_replay_execution_approval_blocked_idempotency_marker_exists"
)
WORKFLOW_REPLAY_EXECUTION_APPROVAL_RECORD_TYPE = "browser_workflow_replay_execution_approval_contract"
WORKFLOW_REPLAY_EXECUTION_APPROVAL_REQUEST_RECORD_TYPE = (
    "browser_workflow_replay_execution_approval_request"
)
APPROVAL_RELATIVE_DIR = Path("07_LOGS/Agent-Activity/_browser_workflow_replay_approvals")
IDEMPOTENCY_MARKER_RELATIVE_DIR = APPROVAL_RELATIVE_DIR / "_execution_markers"
LOCAL_ONLY_DOMAINS = {"127.0.0.1", "localhost", "::1"}

LOCAL_DENIED_EFFECTS = (
    "approval_request_written",
    "approval_decision_written",
    "approval_decision_consumed",
    "idempotency_marker_written",
    "execution_approval_written",
    "workflow_replay_attempted",
    "browser_launch_attempted",
    "cdp_connection_attempted",
    "browser_run_log_written",
    "agent_activity_log_written",
    "screenshot_artifact_written",
    "draft_skill_written",
    "trusted_skill_write_attempted",
    "skill_activation_attempted",
    "canonical_writeback_attempted",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _entry_record(path: str) -> dict[str, Any] | None:
    if not path:
        return None
    try:
        record = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return record if isinstance(record, dict) else None


def _approval_identity_material(
    *,
    workflow_id: str,
    workflow_entry_path: str,
    target_url: str,
    allowed_domains: list[str],
    requested_by: str,
    execution_mode: str,
) -> dict[str, Any]:
    return {
        "version": WORKFLOW_REPLAY_EXECUTION_APPROVAL_VERSION,
        "operation": "browser_workflow_replay_execution_trial",
        "workflow_id": workflow_id,
        "workflow_entry_path": workflow_entry_path,
        "target_url": target_url,
        "target_domain": domain_from_url(target_url),
        "allowed_domains": sorted(set(allowed_domains)),
        "requested_by": requested_by,
        "execution_mode": execution_mode,
        "browser_profile_policy": "throwaway_only",
        "allow_credentials": False,
        "allow_real_profile": False,
        "allow_cookies_export": False,
        "trusted_write_allowed": False,
        "activation_allowed": False,
    }


def _approval_request_id(material: dict[str, Any]) -> str:
    digest = _sha256(material)
    workflow_slug = slugify(str(material.get("workflow_id") or "workflow"), "workflow")
    return f"browser-workflow-replay-appr-{workflow_slug}-{digest[:16]}"


def _safe_relative_json_path(base: Path, identifier: str) -> Path:
    safe_id = slugify(identifier, "browser-workflow-replay-approval")
    return base / f"{safe_id}.json"


def _artifact_path(vault: Path, base_relative: Path, identifier: str) -> Path:
    base = (vault / base_relative).resolve()
    path = (vault / _safe_relative_json_path(base_relative, identifier)).resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"workflow replay approval path escapes base directory: {path}") from exc
    return path


def workflow_replay_approval_request_path(vault_root: str | Path, approval_request_id: str) -> Path:
    """Return the future approval-request artifact path without creating it."""
    return _artifact_path(_vault_path(vault_root), APPROVAL_RELATIVE_DIR, approval_request_id)


def workflow_replay_idempotency_marker_path(vault_root: str | Path, approval_request_id: str) -> Path:
    """Return the future idempotency marker path without creating it."""
    return _artifact_path(_vault_path(vault_root), IDEMPOTENCY_MARKER_RELATIVE_DIR, approval_request_id)


def _build_approval_request_preview(
    *,
    generated_at: str,
    approval_request_id: str,
    request_digest_sha256: str,
    workflow_id: str,
    workflow_entry_path: str,
    target_url: str,
    target_domain: str,
    allowed_domains: list[str],
    requested_by: str,
    operator_id: str,
    execution_mode: str,
) -> dict[str, Any]:
    record = {
        "record_type": WORKFLOW_REPLAY_EXECUTION_APPROVAL_REQUEST_RECORD_TYPE,
        "schema_version": WORKFLOW_REPLAY_EXECUTION_APPROVAL_VERSION,
        "approval_request_id": approval_request_id,
        "status": "pending_preview_not_written",
        "operation": "browser_workflow_replay_execution_trial",
        "requested_by": requested_by,
        "operator_id": operator_id,
        "requested_at": generated_at,
        "workflow_id": workflow_id,
        "workflow_entry_path": workflow_entry_path,
        "target_url": target_url,
        "target_domain": target_domain,
        "allowed_domains": list(allowed_domains),
        "execution_mode": execution_mode,
        "browser_profile_policy": "throwaway_only",
        "allow_real_profile": False,
        "allow_credentials": False,
        "allow_cookie_export": False,
        "allow_browser_history_import": False,
        "allow_public_tunnel": False,
        "activation_allowed": False,
        "trusted_write_allowed": False,
        "skill_activation_allowed": False,
        "canonical_writeback_allowed": False,
        "future_write_targets_after_separate_approval": [
            "07_LOGS/Browser-Runs/<approved-run>.json",
            "07_LOGS/Agent-Activity/<approved-run>.md",
            "07_LOGS/Browser-Runs/<approved-run>-screenshot.png",
            "06_AGENTS/Browser-Skills/_drafts/<draft-only>.md",
            "03_INPUTS/Browser-Skill-Candidates/<domain>/<candidate>.md",
        ],
        "approval_effect": (
            "Preview only. A future approval artifact may authorize one local, "
            "throwaway-profile workflow replay trial after a separate execution pass."
        ),
        "request_digest_sha256": request_digest_sha256,
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        "workflow_replay_attempted": False,
        "approval_request_written": False,
        "approval_decision_consumed": False,
        "idempotency_marker_written": False,
    }
    record["preview_digest_sha256"] = _sha256(record)
    return record


@dataclass(frozen=True)
class WorkflowReplayExecutionApprovalRequest:
    """Read-only request to build a future replay execution approval contract."""

    workflow_id: str = ""
    target_url: str = ""
    allowed_domains: list[str] = field(default_factory=list)
    requested_by: str = "Codex"
    operator_id: str = "operator"
    execution_mode: str = "shadow_local_trial"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowReplayExecutionApproval:
    """No-write approval/idempotency contract for one future replay trial."""

    record_type: str
    version: str
    generated_at: str
    status: str
    workflow_id: str
    workflow_entry_path: str
    target_url: str
    target_domain: str
    allowed_domains: list[str]
    approval_request_id: str
    request_digest_sha256: str
    approval_request_path: str
    idempotency_marker_path: str
    idempotency_marker_exists: bool
    request: WorkflowReplayExecutionApprovalRequest
    readiness_status: str
    executor_status: str
    readiness_checks: dict[str, dict[str, Any]] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    approval_request_preview: dict[str, Any] = field(default_factory=dict)
    idempotency_marker_contract: dict[str, Any] = field(default_factory=dict)
    required_future_approval_fields: list[str] = field(default_factory=list)
    required_future_execution_checks: list[str] = field(default_factory=list)
    approval_request_written: bool = False
    approval_decision_written: bool = False
    approval_decision_consumed: bool = False
    idempotency_marker_written: bool = False
    execution_allowed: bool = False
    workflow_replay_attempted: bool = False
    browser_launch_attempted: bool = False
    cdp_connection_attempted: bool = False
    real_profile_access_attempted: bool = False
    credential_or_cookie_read_attempted: bool = False
    trusted_skill_write_attempted: bool = False
    skill_activation_attempted: bool = False
    canonical_writeback_attempted: bool = False
    agent_bus_enqueue_attempted: bool = False
    provider_call_attempted: bool = False
    gate_mutation_attempted: bool = False
    external_code_copied: bool = False
    workflow_use_reference_only: bool = True
    denied_effects: dict[str, bool] = field(default_factory=dict)
    next_step: str = "operator_review"

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["request"] = self.request.as_dict()
        return payload

    def validate(self) -> None:
        if self.approval_request_written:
            raise ValueError("approval_request_written must remain false")
        if self.approval_decision_written:
            raise ValueError("approval_decision_written must remain false")
        if self.approval_decision_consumed:
            raise ValueError("approval_decision_consumed must remain false")
        if self.idempotency_marker_written:
            raise ValueError("idempotency_marker_written must remain false")
        if self.execution_allowed:
            raise ValueError("execution_allowed must remain false")
        if self.workflow_replay_attempted:
            raise ValueError("workflow_replay_attempted must remain false")
        if self.browser_launch_attempted:
            raise ValueError("browser_launch_attempted must remain false")
        if self.cdp_connection_attempted:
            raise ValueError("cdp_connection_attempted must remain false")
        if self.real_profile_access_attempted:
            raise ValueError("real_profile_access_attempted must remain false")
        if self.credential_or_cookie_read_attempted:
            raise ValueError("credential_or_cookie_read_attempted must remain false")
        if self.trusted_skill_write_attempted:
            raise ValueError("trusted_skill_write_attempted must remain false")
        if self.skill_activation_attempted:
            raise ValueError("skill_activation_attempted must remain false")
        if self.canonical_writeback_attempted:
            raise ValueError("canonical_writeback_attempted must remain false")
        if self.agent_bus_enqueue_attempted:
            raise ValueError("agent_bus_enqueue_attempted must remain false")
        if self.provider_call_attempted:
            raise ValueError("provider_call_attempted must remain false")
        if self.gate_mutation_attempted:
            raise ValueError("gate_mutation_attempted must remain false")
        if self.external_code_copied:
            raise ValueError("external_code_copied must remain false")
        if not self.workflow_use_reference_only:
            raise ValueError("workflow_use_reference_only must remain true")
        for name in (*FORBIDDEN_EFFECTS, *LOCAL_DENIED_EFFECTS):
            if self.denied_effects.get(name) is not False:
                raise ValueError(f"{name} must remain false")
        if self.status == WORKFLOW_REPLAY_EXECUTION_APPROVAL_READY:
            if self.blockers:
                raise ValueError("ready approval contract cannot include blockers")
            if self.idempotency_marker_exists:
                raise ValueError("ready approval contract cannot reuse an idempotency marker")
            if self.readiness_status != WORKFLOW_REPLAY_EXECUTION_READINESS_READY:
                raise ValueError("ready approval contract requires replay readiness")
            if self.executor_status != WORKFLOW_REPLAY_EXECUTOR_READY_NO_EXECUTION:
                raise ValueError("ready approval contract requires no-execution executor readiness")


def build_workflow_replay_execution_approval(
    vault_root: str | Path,
    request: WorkflowReplayExecutionApprovalRequest | None = None,
    *,
    generated_at: str | None = None,
) -> WorkflowReplayExecutionApproval:
    """Build a no-write approval/idempotency contract for a future replay trial."""
    timestamp = generated_at or _now_utc()
    vault = _vault_path(vault_root)
    approval_request = request or WorkflowReplayExecutionApprovalRequest()
    requested_domains = list(approval_request.allowed_domains)
    readiness_request = WorkflowReplayExecutionReadinessRequest(
        workflow_id=approval_request.workflow_id,
        target_url=approval_request.target_url,
        allowed_domains=requested_domains,
        requested_by=approval_request.requested_by,
        enable_validation=True,
        request_live_replay=False,
    )
    readiness = build_workflow_replay_execution_readiness(vault, readiness_request, generated_at=timestamp)
    executor_result = build_workflow_replay_executor_result(
        vault,
        WorkflowReplayExecutorRequest(
            workflow_id=approval_request.workflow_id,
            target_url=approval_request.target_url,
            allowed_domains=requested_domains,
            requested_by=approval_request.requested_by,
            enable_replay_executor=True,
            run_approved_workflow_replay=False,
        ),
        generated_at=timestamp,
    )
    entry = _entry_record(executor_result.workflow_entry_path)
    effective_target_url = executor_result.target_url or approval_request.target_url
    target_domain = executor_result.target_domain or domain_from_url(effective_target_url)
    entry_source_url = str(entry.get("source_url") or "") if isinstance(entry, dict) else ""
    allowed_domains = requested_domains or list(entry.get("allowed_domains") or []) if isinstance(entry, dict) else []
    material = _approval_identity_material(
        workflow_id=approval_request.workflow_id,
        workflow_entry_path=executor_result.workflow_entry_path,
        target_url=effective_target_url,
        allowed_domains=allowed_domains,
        requested_by=approval_request.requested_by,
        execution_mode=approval_request.execution_mode,
    )
    approval_id = _approval_request_id(material)
    digest = _sha256(material)
    approval_path = workflow_replay_approval_request_path(vault, approval_id)
    marker_path = workflow_replay_idempotency_marker_path(vault, approval_id)
    marker_exists = marker_path.exists()

    checks = {
        "readiness_ready_no_execution": {
            "passed": readiness.status == WORKFLOW_REPLAY_EXECUTION_READINESS_READY,
            "status": readiness.status,
            "blockers": readiness.blockers,
        },
        "executor_ready_no_execution": {
            "passed": executor_result.status == WORKFLOW_REPLAY_EXECUTOR_READY_NO_EXECUTION,
            "status": executor_result.status,
            "stop_reasons": executor_result.stop_reasons,
        },
        "workflow_entry_bound": {
            "passed": bool(executor_result.workflow_entry_path),
            "workflow_entry_path": executor_result.workflow_entry_path,
        },
        "target_url_matches_reviewed_source": {
            "passed": bool(effective_target_url) and effective_target_url == entry_source_url,
            "target_url": effective_target_url,
            "entry_source_url": entry_source_url,
        },
        "target_domain_local_only": {
            "passed": target_domain in LOCAL_ONLY_DOMAINS,
            "target_domain": target_domain,
            "allowed_local_domains": sorted(LOCAL_ONLY_DOMAINS),
        },
        "target_domain_allowed": {
            "passed": bool(target_domain) and target_domain in allowed_domains,
            "target_domain": target_domain,
            "allowed_domains": allowed_domains,
        },
        "idempotency_marker_absent": {
            "passed": marker_exists is False,
            "idempotency_marker_path": marker_path.as_posix(),
            "idempotency_marker_exists": marker_exists,
        },
        "approval_request_preview_only": {
            "passed": True,
            "approval_request_path": approval_path.as_posix(),
            "approval_request_written": False,
        },
        "no_side_effects_in_this_contract": {
            "passed": True,
            "workflow_replay_attempted": False,
            "browser_launch_attempted": False,
            "cdp_connection_attempted": False,
            "idempotency_marker_written": False,
        },
    }
    blockers = [name for name, check in checks.items() if not bool(check["passed"])]
    if marker_exists:
        status = WORKFLOW_REPLAY_EXECUTION_APPROVAL_BLOCKED_MARKER_EXISTS
        next_step = "review_existing_idempotency_marker_before_any_replay"
    elif blockers:
        status = WORKFLOW_REPLAY_EXECUTION_APPROVAL_BLOCKED
        next_step = "repair_workflow_replay_execution_approval_contract"
    else:
        status = WORKFLOW_REPLAY_EXECUTION_APPROVAL_READY
        next_step = "safe-local-workflow-replay-execution-proof"

    approval_preview = _build_approval_request_preview(
        generated_at=timestamp,
        approval_request_id=approval_id,
        request_digest_sha256=digest,
        workflow_id=approval_request.workflow_id,
        workflow_entry_path=executor_result.workflow_entry_path,
        target_url=effective_target_url,
        target_domain=target_domain,
        allowed_domains=allowed_domains,
        requested_by=approval_request.requested_by,
        operator_id=approval_request.operator_id,
        execution_mode=approval_request.execution_mode,
    )
    marker_contract = {
        "record_type": "browser_workflow_replay_execution_idempotency_marker",
        "schema_version": WORKFLOW_REPLAY_EXECUTION_APPROVAL_VERSION,
        "approval_request_id": approval_id,
        "marker_path": marker_path.as_posix(),
        "marker_exists": marker_exists,
        "marker_written": False,
        "marker_write_allowed_in_this_pass": False,
        "execution_must_abort_if_exists": True,
        "marker_write_timing": "future_executor_must_reserve_before_browser_launch",
        "required_fields": [
            "record_type",
            "schema_version",
            "approval_request_id",
            "workflow_id",
            "target_url",
            "request_digest_sha256",
            "reserved_at",
            "reserved_by",
            "run_id",
        ],
        "request_digest_sha256": digest,
    }
    contract = WorkflowReplayExecutionApproval(
        record_type=WORKFLOW_REPLAY_EXECUTION_APPROVAL_RECORD_TYPE,
        version=WORKFLOW_REPLAY_EXECUTION_APPROVAL_VERSION,
        generated_at=timestamp,
        status=status,
        workflow_id=approval_request.workflow_id,
        workflow_entry_path=executor_result.workflow_entry_path,
        target_url=effective_target_url,
        target_domain=target_domain,
        allowed_domains=allowed_domains,
        approval_request_id=approval_id,
        request_digest_sha256=digest,
        approval_request_path=approval_path.as_posix(),
        idempotency_marker_path=marker_path.as_posix(),
        idempotency_marker_exists=marker_exists,
        request=approval_request,
        readiness_status=readiness.status,
        executor_status=executor_result.status,
        readiness_checks=checks,
        blockers=blockers,
        approval_request_preview=approval_preview,
        idempotency_marker_contract=marker_contract,
        required_future_approval_fields=[
            "approval_request_id",
            "operator_id",
            "approved_by",
            "approved_at",
            "approved_status",
            "workflow_id",
            "target_url",
            "request_digest_sha256",
            "bounded_write_targets",
            "forbidden_effect_acknowledgement",
        ],
        required_future_execution_checks=[
            "approval artifact exists and status is approved",
            "approval digest matches selected workflow, target, and domains",
            "idempotency marker does not already exist",
            "idempotency marker is reserved before browser launch",
            "target remains local-only and matches reviewed workflow source_url",
            "throwaway browser profile is used",
            "no credentials, cookies, browser history, public tunnels, trusted skills, or canonical writeback",
        ],
        approval_request_written=False,
        approval_decision_written=False,
        approval_decision_consumed=False,
        idempotency_marker_written=False,
        execution_allowed=False,
        workflow_replay_attempted=False,
        browser_launch_attempted=False,
        cdp_connection_attempted=False,
        real_profile_access_attempted=False,
        credential_or_cookie_read_attempted=False,
        trusted_skill_write_attempted=False,
        skill_activation_attempted=False,
        canonical_writeback_attempted=False,
        agent_bus_enqueue_attempted=False,
        provider_call_attempted=False,
        gate_mutation_attempted=False,
        external_code_copied=False,
        workflow_use_reference_only=True,
        denied_effects={name: False for name in (*FORBIDDEN_EFFECTS, *LOCAL_DENIED_EFFECTS)},
        next_step=next_step,
    )
    contract.validate()
    return contract


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Report no-write Browser Workflow replay execution approval contract.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--workflow-id", default="", help="Reviewed workflow id to bind.")
    parser.add_argument("--target-url", default="", help="Local target URL to bind.")
    parser.add_argument("--allowed-domain", action="append", default=[], help="Allowed local target domain. May be repeated.")
    parser.add_argument("--requested-by", default="Codex", help="Runtime/operator requesting the approval contract.")
    parser.add_argument("--operator-id", default="operator", help="Operator identifier for the preview.")
    parser.add_argument("--execution-mode", default="shadow_local_trial", help="Future bounded execution mode label.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    request = WorkflowReplayExecutionApprovalRequest(
        workflow_id=args.workflow_id,
        target_url=args.target_url,
        allowed_domains=list(args.allowed_domain or []),
        requested_by=args.requested_by,
        operator_id=args.operator_id,
        execution_mode=args.execution_mode,
    )
    contract = build_workflow_replay_execution_approval(args.vault_root, request)
    payload = contract.as_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {contract.status}")
        print(f"approval_request_id: {contract.approval_request_id}")
        print(f"idempotency_marker_exists: {contract.idempotency_marker_exists}")
        print(f"next_step: {contract.next_step}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
