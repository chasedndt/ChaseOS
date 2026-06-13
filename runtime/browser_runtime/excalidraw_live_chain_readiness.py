"""No-execution readiness reporter for the Excalidraw browser/MCP proof chain.

This module composes the resolver, response-readiness bridge, approval contract,
and proof execution shell into one read-only report. It does not probe targets,
launch browsers, connect CDP, invoke MCP, write approvals, reserve markers, or
write browser/skill artifacts.
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
from runtime.browser_runtime.excalidraw_mcp_proof_execution import (
    EXCALIDRAW_MCP_PROOF_EXECUTION_READY_NO_EXECUTION,
    ExcalidrawMCPProofExecutionRequest,
    build_excalidraw_mcp_proof_execution_shell,
)
from runtime.browser_runtime.excalidraw_readiness_from_response import (
    EXCALIDRAW_READINESS_FROM_RESPONSE_READY,
    build_excalidraw_readiness_from_response,
)
from runtime.browser_runtime.excalidraw_target_response_resolver import (
    EXCALIDRAW_TARGET_RESPONSE_RESOLVER_ACCEPTED,
    resolve_excalidraw_target_response,
)


EXCALIDRAW_LIVE_CHAIN_READINESS_VERSION = "browser.excalidraw_live_chain_readiness.v1"
EXCALIDRAW_LIVE_CHAIN_READINESS_RECORD_TYPE = "excalidraw_live_chain_readiness"
EXCALIDRAW_LIVE_CHAIN_READINESS_READY = "excalidraw_live_chain_readiness_ready_no_execution"
EXCALIDRAW_LIVE_CHAIN_READINESS_BLOCKED_TARGET = (
    "blocked_excalidraw_live_chain_readiness_target_response_not_accepted"
)
EXCALIDRAW_LIVE_CHAIN_READINESS_BLOCKED_READINESS = (
    "blocked_excalidraw_live_chain_readiness_bridge_not_ready"
)
EXCALIDRAW_LIVE_CHAIN_READINESS_BLOCKED_APPROVAL = (
    "blocked_excalidraw_live_chain_readiness_approval_not_ready"
)
EXCALIDRAW_LIVE_CHAIN_READINESS_BLOCKED_SHELL = (
    "blocked_excalidraw_live_chain_readiness_execution_shell_not_ready"
)

BLOCKED_EFFECTS = (
    "dependency_install",
    "server_start",
    "network_probe",
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
    "draft_skill_written",
    "untrusted_candidate_written",
    "trusted_skill_write_attempted",
    "skill_activation_attempted",
    "real_profile_access_attempted",
    "credential_or_cookie_read_attempted",
    "cookie_export_attempted",
    "browser_profile_sync_attempted",
    "public_tunnel_attempted",
    "browser_harness_used",
    "browser_use_cli_live_used",
    "workflow_use_code_copied",
    "agent_bus_enqueue_attempted",
    "provider_call_attempted",
    "gate_mutation_attempted",
    "canonical_writeback_attempted",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


@dataclass(frozen=True)
class ExcalidrawLiveChainReadiness:
    record_type: str
    schema_version: str
    generated_at: str
    status: str
    response_path: str
    selected_response_path: str
    selected_response_status: str
    target_url: str
    target_host: str
    readiness_status: str
    approval_status: str
    proof_shell_status: str
    approval_request_id: str
    run_id: str
    blockers: tuple[str, ...] = ()
    chain_steps: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    next_recommended_pass: str = "external-runtime-provide-excalidraw-target-url"
    read_only: bool = True
    blocked_effects: tuple[str, ...] = BLOCKED_EFFECTS
    dependency_install_attempted: bool = False
    server_start_attempted: bool = False
    network_probe_attempted: bool = False
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
    draft_skill_written: bool = False
    untrusted_candidate_written: bool = False
    trusted_skill_write_attempted: bool = False
    skill_activation_attempted: bool = False
    real_profile_access_attempted: bool = False
    credential_or_cookie_read_attempted: bool = False
    cookie_export_attempted: bool = False
    browser_profile_sync_attempted: bool = False
    public_tunnel_attempted: bool = False
    browser_harness_used: bool = False
    browser_use_cli_live_used: bool = False
    workflow_use_code_copied: bool = False
    agent_bus_enqueue_attempted: bool = False
    provider_call_attempted: bool = False
    gate_mutation_attempted: bool = False
    canonical_writeback_attempted: bool = False

    def validate(self) -> None:
        if self.record_type != EXCALIDRAW_LIVE_CHAIN_READINESS_RECORD_TYPE:
            raise ValueError("invalid Excalidraw live-chain readiness record type")
        if self.schema_version != EXCALIDRAW_LIVE_CHAIN_READINESS_VERSION:
            raise ValueError("invalid Excalidraw live-chain readiness schema version")
        if self.status not in {
            EXCALIDRAW_LIVE_CHAIN_READINESS_READY,
            EXCALIDRAW_LIVE_CHAIN_READINESS_BLOCKED_TARGET,
            EXCALIDRAW_LIVE_CHAIN_READINESS_BLOCKED_READINESS,
            EXCALIDRAW_LIVE_CHAIN_READINESS_BLOCKED_APPROVAL,
            EXCALIDRAW_LIVE_CHAIN_READINESS_BLOCKED_SHELL,
        }:
            raise ValueError("invalid Excalidraw live-chain readiness status")
        if self.status == EXCALIDRAW_LIVE_CHAIN_READINESS_READY and self.blockers:
            raise ValueError("ready live-chain readiness cannot include blockers")
        if self.status != EXCALIDRAW_LIVE_CHAIN_READINESS_READY and not self.blockers:
            raise ValueError("blocked live-chain readiness requires blockers")
        forbidden_flags = (
            self.dependency_install_attempted,
            self.server_start_attempted,
            self.network_probe_attempted,
            self.approval_request_written,
            self.approval_decision_written,
            self.approval_decision_consumed,
            self.idempotency_marker_written,
            self.execution_attempted,
            self.browser_launch_attempted,
            self.cdp_connection_attempted,
            self.mcp_invocation_attempted,
            self.mcp_tool_call_attempted,
            self.target_navigation_attempted,
            self.screenshot_attempted,
            self.browser_run_log_written,
            self.agent_activity_log_written,
            self.draft_skill_written,
            self.untrusted_candidate_written,
            self.trusted_skill_write_attempted,
            self.skill_activation_attempted,
            self.real_profile_access_attempted,
            self.credential_or_cookie_read_attempted,
            self.cookie_export_attempted,
            self.browser_profile_sync_attempted,
            self.public_tunnel_attempted,
            self.browser_harness_used,
            self.browser_use_cli_live_used,
            self.workflow_use_code_copied,
            self.agent_bus_enqueue_attempted,
            self.provider_call_attempted,
            self.gate_mutation_attempted,
            self.canonical_writeback_attempted,
        )
        if any(forbidden_flags):
            raise ValueError("Excalidraw live-chain readiness attempted a forbidden effect")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["blockers"] = list(self.blockers)
        payload["chain_steps"] = list(self.chain_steps)
        payload["blocked_effects"] = list(self.blocked_effects)
        return payload


def build_excalidraw_live_chain_readiness(
    vault_root: str | Path,
    *,
    response_path: str | Path = "",
    generated_at: str | None = None,
    controller_readiness: BrowserControllerSetupReadiness | None = None,
) -> ExcalidrawLiveChainReadiness:
    """Build a read-only report over the current Excalidraw proof chain."""
    timestamp = generated_at or _now_utc()
    vault = _vault_path(vault_root)
    resolution = resolve_excalidraw_target_response(
        vault,
        response_path=response_path,
        generated_at=timestamp,
    )
    readiness = build_excalidraw_readiness_from_response(
        vault,
        response_path=response_path,
        generated_at=timestamp,
        controller_readiness=controller_readiness,
    )
    approval_request = ExcalidrawMCPExecutionApprovalRequest(response_path=str(response_path or ""))
    approval = build_excalidraw_mcp_execution_approval(
        vault,
        approval_request,
        generated_at=timestamp,
        controller_readiness=controller_readiness,
    )
    shell_request = ExcalidrawMCPProofExecutionRequest(response_path=str(response_path or ""))
    shell = build_excalidraw_mcp_proof_execution_shell(
        vault,
        shell_request,
        generated_at=timestamp,
        controller_readiness=controller_readiness,
    )

    chain_steps = (
        {
            "step": "target_response_resolution",
            "status": resolution.status,
            "ready": resolution.status == EXCALIDRAW_TARGET_RESPONSE_RESOLVER_ACCEPTED,
        },
        {
            "step": "response_to_live_readiness",
            "status": readiness.status,
            "ready": readiness.status == EXCALIDRAW_READINESS_FROM_RESPONSE_READY,
        },
        {
            "step": "execution_approval_contract",
            "status": approval.status,
            "ready": approval.status == EXCALIDRAW_MCP_EXECUTION_APPROVAL_READY,
        },
        {
            "step": "proof_execution_shell",
            "status": shell.status,
            "ready": shell.status == EXCALIDRAW_MCP_PROOF_EXECUTION_READY_NO_EXECUTION,
        },
    )
    blockers: list[str] = []
    if resolution.status != EXCALIDRAW_TARGET_RESPONSE_RESOLVER_ACCEPTED:
        status = EXCALIDRAW_LIVE_CHAIN_READINESS_BLOCKED_TARGET
        blockers.append(f"target_response_not_accepted:{resolution.status}")
        next_step = resolution.next_recommended_pass
    elif readiness.status != EXCALIDRAW_READINESS_FROM_RESPONSE_READY:
        status = EXCALIDRAW_LIVE_CHAIN_READINESS_BLOCKED_READINESS
        blockers.append(f"readiness_bridge_not_ready:{readiness.status}")
        next_step = readiness.next_recommended_pass
    elif approval.status != EXCALIDRAW_MCP_EXECUTION_APPROVAL_READY:
        status = EXCALIDRAW_LIVE_CHAIN_READINESS_BLOCKED_APPROVAL
        blockers.append(f"approval_contract_not_ready:{approval.status}")
        next_step = approval.next_step
    elif shell.status != EXCALIDRAW_MCP_PROOF_EXECUTION_READY_NO_EXECUTION:
        status = EXCALIDRAW_LIVE_CHAIN_READINESS_BLOCKED_SHELL
        blockers.append(f"proof_shell_not_ready:{shell.status}")
        next_step = shell.next_step
    else:
        status = EXCALIDRAW_LIVE_CHAIN_READINESS_READY
        next_step = "operator-review-before-excalidraw-live-canvas-execution"

    packet = ExcalidrawLiveChainReadiness(
        record_type=EXCALIDRAW_LIVE_CHAIN_READINESS_RECORD_TYPE,
        schema_version=EXCALIDRAW_LIVE_CHAIN_READINESS_VERSION,
        generated_at=timestamp,
        status=status,
        response_path=str(response_path or ""),
        selected_response_path=resolution.selected_response_path,
        selected_response_status=resolution.selected_response_status,
        target_url=resolution.target_url,
        target_host=resolution.target_host,
        readiness_status=readiness.status,
        approval_status=approval.status,
        proof_shell_status=shell.status,
        approval_request_id=approval.approval_request_id,
        run_id=shell.run_id,
        blockers=tuple(blockers),
        chain_steps=chain_steps,
        next_recommended_pass=next_step,
    )
    packet.validate()
    return packet


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Report Excalidraw browser/MCP proof chain readiness without execution.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--response-path", default="", help="Optional target response artifact path.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    packet = build_excalidraw_live_chain_readiness(args.vault_root, response_path=args.response_path)
    payload = packet.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {payload['status']}")
        for blocker in payload["blockers"]:
            print(f"blocker: {blocker}")
        print(f"next_recommended_pass: {payload['next_recommended_pass']}")
    return 0 if payload["status"] == EXCALIDRAW_LIVE_CHAIN_READINESS_READY else 1


if __name__ == "__main__":
    raise SystemExit(main())
