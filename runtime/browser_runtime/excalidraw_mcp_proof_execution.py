"""Fail-closed execution shell for the future Excalidraw browser/MCP proof.

This module is the governed entry point a later live pass will use after the
local target response, readiness bridge, and approval/idempotency contract are
ready. In this pass it validates those prerequisites and refuses all execution.
It does not write approval records, reserve markers, launch a browser, connect
to CDP, invoke MCP, navigate, capture screenshots, or write skill memory.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.browser_runtime.browser_controller_setup_readiness import BrowserControllerSetupReadiness
from runtime.browser_runtime.excalidraw_mcp_execution_approval import (
    EXCALIDRAW_MCP_EXECUTION_APPROVAL_READY,
    ExcalidrawMCPExecutionApprovalRequest,
    build_excalidraw_mcp_execution_approval,
)
from runtime.browser_runtime.models import domain_from_url, slugify


EXCALIDRAW_MCP_PROOF_EXECUTION_VERSION = "browser.excalidraw_mcp_proof_execution.v1"
EXCALIDRAW_MCP_PROOF_EXECUTION_RECORD_TYPE = "excalidraw_local_browser_mcp_proof_execution_shell"
EXCALIDRAW_MCP_PROOF_EXECUTION_READY_NO_EXECUTION = (
    "excalidraw_mcp_proof_execution_shell_ready_no_execution"
)
EXCALIDRAW_MCP_PROOF_EXECUTION_BLOCKED = "blocked_excalidraw_mcp_proof_execution_shell"
EXCALIDRAW_MCP_PROOF_EXECUTION_BLOCKED_APPROVAL = (
    "blocked_excalidraw_mcp_proof_execution_approval_not_ready"
)
EXCALIDRAW_MCP_PROOF_EXECUTION_BLOCKED_MARKER_EXISTS = (
    "blocked_excalidraw_mcp_proof_execution_idempotency_marker_exists"
)
EXCALIDRAW_MCP_PROOF_EXECUTION_BLOCKED_EXECUTOR_DISABLED = (
    "blocked_excalidraw_mcp_proof_execution_executor_disabled"
)

LOCAL_ONLY_DOMAINS = {"127.0.0.1", "localhost", "::1"}

BLOCKED_EFFECTS = (
    "approval_request_written",
    "approval_decision_written",
    "approval_decision_consumed",
    "idempotency_marker_written",
    "execution_attempted",
    "browser_launch_attempted",
    "cdp_connection_attempted",
    "mcp_invocation_attempted",
    "mcp_tool_call_attempted",
    "target_navigation_attempted",
    "screenshot_attempted",
    "browser_run_log_written",
    "agent_activity_log_written",
    "screenshot_artifact_written",
    "draft_skill_written",
    "untrusted_candidate_written",
    "trusted_skill_write_attempted",
    "skill_activation_attempted",
    "real_profile_access_attempted",
    "credential_or_cookie_read_attempted",
    "cookie_export_attempted",
    "browser_profile_sync_attempted",
    "browser_history_import_attempted",
    "public_tunnel_attempted",
    "browser_harness_used",
    "browser_use_cli_live_used",
    "workflow_use_code_copied",
    "shell_execution_from_browser_runtime_attempted",
    "agent_bus_enqueue_attempted",
    "provider_call_attempted",
    "gate_mutation_attempted",
    "canonical_writeback_attempted",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _run_id(target_url: str, generated_at: str) -> str:
    stamp = generated_at[:10].replace("-", "")
    target = slugify(domain_from_url(target_url), "local-target")
    return f"excalidraw_mcp_proof_execution_{stamp}_{target}"


def _future_artifact_plan(vault: Path, run_id: str, target_domain: str) -> dict[str, str]:
    domain_slug = slugify(target_domain, "local-target")
    date_slug = run_id.split("_")[4] if len(run_id.split("_")) > 4 else "20260503"
    return {
        "approval_request": (
            "07_LOGS/Agent-Activity/_excalidraw_mcp_approvals/"
            "<approval_request_id>.json"
        ),
        "idempotency_marker": (
            "07_LOGS/Agent-Activity/_excalidraw_mcp_approvals/"
            "_execution_markers/<approval_request_id>.json"
        ),
        "browser_run_log": f"07_LOGS/Browser-Runs/{run_id}_success.json",
        "screenshot": f"07_LOGS/Browser-Runs/{run_id}_screenshot.png",
        "agent_activity": f"07_LOGS/Agent-Activity/{date_slug}-browser-{run_id}.md",
        "draft_skill": f"06_AGENTS/Browser-Skills/_drafts/draft-{run_id}.md",
        "untrusted_candidate": (
            f"03_INPUTS/Browser-Skill-Candidates/{domain_slug}/"
            f"{date_slug}__candidate-{run_id}.md"
        ),
        "vault_root": vault.as_posix(),
    }


@dataclass(frozen=True)
class ExcalidrawMCPProofExecutionRequest:
    """Request for the Excalidraw proof execution shell."""

    response_path: str = ""
    requested_by: str = "Codex"
    operator_id: str = "operator"
    execution_mode: str = "shadow_local_canvas_trial"
    execute_local_canvas_proof: bool = False
    live_executor_enabled: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExcalidrawMCPProofExecutionShell:
    """Fail-closed plan/result for one future Excalidraw browser/MCP proof."""

    record_type: str
    schema_version: str
    generated_at: str
    status: str
    run_id: str
    target_url: str
    target_domain: str
    approval_request_id: str
    request_digest_sha256: str
    approval_request_path: str
    idempotency_marker_path: str
    approval_status: str
    idempotency_marker_exists: bool
    request: ExcalidrawMCPProofExecutionRequest
    checks: dict[str, dict[str, Any]] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    future_artifact_plan: dict[str, str] = field(default_factory=dict)
    execution_contract: dict[str, Any] = field(default_factory=dict)
    approval_request_written: bool = False
    approval_decision_written: bool = False
    approval_decision_consumed: bool = False
    idempotency_marker_written: bool = False
    execution_attempted: bool = False
    browser_launch_attempted: bool = False
    cdp_connection_attempted: bool = False
    mcp_invocation_attempted: bool = False
    mcp_tool_call_attempted: bool = False
    target_navigation_attempted: bool = False
    screenshot_attempted: bool = False
    browser_run_log_written: bool = False
    agent_activity_log_written: bool = False
    screenshot_artifact_written: bool = False
    draft_skill_written: bool = False
    untrusted_candidate_written: bool = False
    trusted_skill_write_attempted: bool = False
    skill_activation_attempted: bool = False
    real_profile_access_attempted: bool = False
    credential_or_cookie_read_attempted: bool = False
    cookie_export_attempted: bool = False
    browser_profile_sync_attempted: bool = False
    browser_history_import_attempted: bool = False
    public_tunnel_attempted: bool = False
    browser_harness_used: bool = False
    browser_use_cli_live_used: bool = False
    workflow_use_code_copied: bool = False
    shell_execution_from_browser_runtime_attempted: bool = False
    agent_bus_enqueue_attempted: bool = False
    provider_call_attempted: bool = False
    gate_mutation_attempted: bool = False
    canonical_writeback_attempted: bool = False
    denied_effects: dict[str, bool] = field(default_factory=dict)
    next_step: str = "external-runtime-provide-excalidraw-target-url"

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["request"] = self.request.as_dict()
        return payload

    def validate(self) -> None:
        if self.record_type != EXCALIDRAW_MCP_PROOF_EXECUTION_RECORD_TYPE:
            raise ValueError("invalid Excalidraw proof execution record type")
        if self.schema_version != EXCALIDRAW_MCP_PROOF_EXECUTION_VERSION:
            raise ValueError("invalid Excalidraw proof execution schema version")
        if self.status not in {
            EXCALIDRAW_MCP_PROOF_EXECUTION_READY_NO_EXECUTION,
            EXCALIDRAW_MCP_PROOF_EXECUTION_BLOCKED,
            EXCALIDRAW_MCP_PROOF_EXECUTION_BLOCKED_APPROVAL,
            EXCALIDRAW_MCP_PROOF_EXECUTION_BLOCKED_MARKER_EXISTS,
            EXCALIDRAW_MCP_PROOF_EXECUTION_BLOCKED_EXECUTOR_DISABLED,
        }:
            raise ValueError("invalid Excalidraw proof execution status")
        if self.status == EXCALIDRAW_MCP_PROOF_EXECUTION_READY_NO_EXECUTION and self.blockers:
            raise ValueError("ready no-execution shell cannot include blockers")
        if self.status != EXCALIDRAW_MCP_PROOF_EXECUTION_READY_NO_EXECUTION and not self.blockers:
            raise ValueError("blocked execution shell requires blockers")
        for name in BLOCKED_EFFECTS:
            if getattr(self, name, False):
                raise ValueError(f"{name} must remain false")
            if self.denied_effects.get(name) is not False:
                raise ValueError(f"{name} denied effect must be false")


def build_excalidraw_mcp_proof_execution_shell(
    vault_root: str | Path,
    request: ExcalidrawMCPProofExecutionRequest | None = None,
    *,
    generated_at: str | None = None,
    controller_readiness: BrowserControllerSetupReadiness | None = None,
) -> ExcalidrawMCPProofExecutionShell:
    """Build a fail-closed shell for a future local Excalidraw canvas proof."""
    timestamp = generated_at or _now_utc()
    vault = _vault_path(vault_root)
    shell_request = request or ExcalidrawMCPProofExecutionRequest()
    approval_request = ExcalidrawMCPExecutionApprovalRequest(
        response_path=shell_request.response_path,
        requested_by=shell_request.requested_by,
        operator_id=shell_request.operator_id,
        execution_mode=shell_request.execution_mode,
    )
    approval = build_excalidraw_mcp_execution_approval(
        vault,
        approval_request,
        generated_at=timestamp,
        controller_readiness=controller_readiness,
    )
    target_url = approval.target_url
    target_domain = approval.target_domain or domain_from_url(target_url)
    run_id = _run_id(target_url, timestamp)
    checks = {
        "approval_ready_no_execution": {
            "passed": approval.status == EXCALIDRAW_MCP_EXECUTION_APPROVAL_READY,
            "status": approval.status,
            "blockers": list(approval.blockers),
        },
        "target_domain_local_only": {
            "passed": target_domain in LOCAL_ONLY_DOMAINS,
            "target_domain": target_domain,
            "allowed_local_domains": sorted(LOCAL_ONLY_DOMAINS),
        },
        "idempotency_marker_absent": {
            "passed": approval.idempotency_marker_exists is False,
            "idempotency_marker_path": approval.idempotency_marker_path,
            "idempotency_marker_exists": approval.idempotency_marker_exists,
        },
        "execute_flag_requested": {
            "passed": shell_request.execute_local_canvas_proof is True,
            "execute_local_canvas_proof": shell_request.execute_local_canvas_proof,
        },
        "live_executor_enabled": {
            "passed": shell_request.live_executor_enabled is True,
            "live_executor_enabled": shell_request.live_executor_enabled,
        },
    }
    blockers = [name for name, check in checks.items() if not bool(check["passed"])]
    if approval.idempotency_marker_exists:
        status = EXCALIDRAW_MCP_PROOF_EXECUTION_BLOCKED_MARKER_EXISTS
        next_step = "review_existing_excalidraw_execution_marker"
    elif approval.status != EXCALIDRAW_MCP_EXECUTION_APPROVAL_READY:
        status = EXCALIDRAW_MCP_PROOF_EXECUTION_BLOCKED_APPROVAL
        next_step = approval.next_step
    elif not shell_request.execute_local_canvas_proof:
        status = EXCALIDRAW_MCP_PROOF_EXECUTION_READY_NO_EXECUTION
        blockers = []
        next_step = "operator-review-before-excalidraw-live-canvas-execution"
    elif not shell_request.live_executor_enabled:
        status = EXCALIDRAW_MCP_PROOF_EXECUTION_BLOCKED_EXECUTOR_DISABLED
        next_step = "implement-or-enable-approved-excalidraw-live-executor"
    else:
        status = EXCALIDRAW_MCP_PROOF_EXECUTION_BLOCKED
        blockers.append("excalidraw_live_executor_not_implemented_in_this_pass")
        next_step = "excalidraw-live-canvas-proof-implementation"

    result = ExcalidrawMCPProofExecutionShell(
        record_type=EXCALIDRAW_MCP_PROOF_EXECUTION_RECORD_TYPE,
        schema_version=EXCALIDRAW_MCP_PROOF_EXECUTION_VERSION,
        generated_at=timestamp,
        status=status,
        run_id=run_id,
        target_url=target_url,
        target_domain=target_domain,
        approval_request_id=approval.approval_request_id,
        request_digest_sha256=approval.request_digest_sha256,
        approval_request_path=approval.approval_request_path,
        idempotency_marker_path=approval.idempotency_marker_path,
        approval_status=approval.status,
        idempotency_marker_exists=approval.idempotency_marker_exists,
        request=shell_request,
        checks=checks,
        blockers=blockers,
        future_artifact_plan=_future_artifact_plan(vault, run_id, target_domain),
        execution_contract={
            "browser_profile_policy": "throwaway_only",
            "target_policy": "local_loopback_only",
            "mcp_policy": "local_only_optional; no public tunnel",
            "canvas_goal": 'draw one rectangle and label it "ChaseOS"',
            "skill_memory_policy": "draft_and_untrusted_candidate_only",
            "must_reserve_marker_before": "browser_launch",
            "must_write_browser_run_log": True,
            "must_write_agent_activity_log": True,
            "trusted_skill_activation_allowed": False,
            "canonical_writeback_allowed": False,
        },
        denied_effects={name: False for name in BLOCKED_EFFECTS},
        next_step=next_step,
    )
    result.validate()
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Report fail-closed Excalidraw browser/MCP proof execution shell.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--response-path", default="", help="Optional target response artifact path.")
    parser.add_argument("--requested-by", default="Codex")
    parser.add_argument("--operator-id", default="operator")
    parser.add_argument("--execution-mode", default="shadow_local_canvas_trial")
    parser.add_argument("--execute-local-canvas-proof", action="store_true")
    parser.add_argument("--live-executor-enabled", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    result = build_excalidraw_mcp_proof_execution_shell(
        args.vault_root,
        ExcalidrawMCPProofExecutionRequest(
            response_path=args.response_path,
            requested_by=args.requested_by,
            operator_id=args.operator_id,
            execution_mode=args.execution_mode,
            execute_local_canvas_proof=args.execute_local_canvas_proof,
            live_executor_enabled=args.live_executor_enabled,
        ),
    )
    payload = result.as_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {result.status}")
        print(f"run_id: {result.run_id}")
        print(f"approval_request_id: {result.approval_request_id}")
        print(f"next_step: {result.next_step}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
