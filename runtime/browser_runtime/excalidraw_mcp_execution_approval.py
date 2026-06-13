"""No-write approval/idempotency contract for Excalidraw browser/MCP proof.

This module prepares the governance shape for one future local Excalidraw
browser/MCP canvas proof. It reads the existing no-execution readiness bridge,
builds a pending approval-request preview, and computes an exact-once marker
path. It does not write approvals, reserve markers, launch browsers, connect to
CDP, invoke MCP, navigate to a target, or write skill memory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.browser_runtime.browser_controller_setup_readiness import BrowserControllerSetupReadiness
from runtime.browser_runtime.excalidraw_readiness_from_response import (
    EXCALIDRAW_READINESS_FROM_RESPONSE_READY,
    build_excalidraw_readiness_from_response,
)
from runtime.browser_runtime.models import domain_from_url, slugify


EXCALIDRAW_MCP_EXECUTION_APPROVAL_VERSION = "browser.excalidraw_mcp_execution_approval.v1"
EXCALIDRAW_MCP_EXECUTION_APPROVAL_RECORD_TYPE = (
    "excalidraw_local_browser_mcp_execution_approval_contract"
)
EXCALIDRAW_MCP_EXECUTION_APPROVAL_REQUEST_RECORD_TYPE = (
    "excalidraw_local_browser_mcp_execution_approval_request"
)
EXCALIDRAW_MCP_EXECUTION_APPROVAL_READY = (
    "excalidraw_mcp_execution_approval_ready_no_execution"
)
EXCALIDRAW_MCP_EXECUTION_APPROVAL_BLOCKED = "blocked_excalidraw_mcp_execution_approval"
EXCALIDRAW_MCP_EXECUTION_APPROVAL_BLOCKED_MARKER_EXISTS = (
    "blocked_excalidraw_mcp_execution_approval_idempotency_marker_exists"
)

APPROVAL_RELATIVE_DIR = Path("07_LOGS/Agent-Activity/_excalidraw_mcp_approvals")
IDEMPOTENCY_MARKER_RELATIVE_DIR = APPROVAL_RELATIVE_DIR / "_execution_markers"
LOCAL_ONLY_DOMAINS = {"127.0.0.1", "localhost", "::1"}

DENIED_EFFECTS = (
    "approval_request_written",
    "approval_decision_written",
    "approval_decision_consumed",
    "idempotency_marker_written",
    "execution_allowed",
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


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _safe_json_path(vault: Path, base_relative: Path, identifier: str) -> Path:
    base = (vault / base_relative).resolve()
    safe_id = slugify(identifier, "excalidraw-mcp-approval")
    path = (vault / base_relative / f"{safe_id}.json").resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"Excalidraw approval path escapes base directory: {path}") from exc
    return path


def excalidraw_mcp_approval_request_path(vault_root: str | Path, approval_request_id: str) -> Path:
    """Return the future approval-request artifact path without creating it."""
    return _safe_json_path(_vault_path(vault_root), APPROVAL_RELATIVE_DIR, approval_request_id)


def excalidraw_mcp_idempotency_marker_path(vault_root: str | Path, approval_request_id: str) -> Path:
    """Return the future idempotency marker path without creating it."""
    return _safe_json_path(_vault_path(vault_root), IDEMPOTENCY_MARKER_RELATIVE_DIR, approval_request_id)


def _approval_identity_material(
    *,
    target_url: str,
    target_domain: str,
    source_response_path: str,
    live_readiness_artifact_path: str,
    requested_by: str,
    execution_mode: str,
) -> dict[str, Any]:
    return {
        "version": EXCALIDRAW_MCP_EXECUTION_APPROVAL_VERSION,
        "operation": "excalidraw_local_browser_mcp_canvas_proof",
        "target_url": target_url,
        "target_domain": target_domain,
        "allowed_domains": [target_domain] if target_domain else [],
        "source_response_path": source_response_path,
        "live_readiness_artifact_path": live_readiness_artifact_path,
        "requested_by": requested_by,
        "execution_mode": execution_mode,
        "browser_profile_policy": "throwaway_only",
        "allow_credentials": False,
        "allow_real_profile": False,
        "allow_cookie_export": False,
        "allow_public_tunnel": False,
        "trusted_write_allowed": False,
        "activation_allowed": False,
        "canonical_writeback_allowed": False,
    }


def _approval_request_id(material: dict[str, Any]) -> str:
    digest = _sha256(material)
    target_slug = slugify(str(material.get("target_domain") or "local-target"), "local-target")
    return f"excalidraw-mcp-appr-{target_slug}-{digest[:16]}"


def _build_approval_request_preview(
    *,
    generated_at: str,
    approval_request_id: str,
    request_digest_sha256: str,
    target_url: str,
    target_domain: str,
    source_response_path: str,
    live_readiness_artifact_path: str,
    requested_by: str,
    operator_id: str,
    execution_mode: str,
) -> dict[str, Any]:
    record = {
        "record_type": EXCALIDRAW_MCP_EXECUTION_APPROVAL_REQUEST_RECORD_TYPE,
        "schema_version": EXCALIDRAW_MCP_EXECUTION_APPROVAL_VERSION,
        "approval_request_id": approval_request_id,
        "status": "pending_preview_not_written",
        "operation": "excalidraw_local_browser_mcp_canvas_proof",
        "requested_by": requested_by,
        "operator_id": operator_id,
        "requested_at": generated_at,
        "target_url": target_url,
        "target_domain": target_domain,
        "source_response_path": source_response_path,
        "live_readiness_artifact_path": live_readiness_artifact_path,
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
            "07_LOGS/Browser-Runs/<approved-excalidraw-run>.json",
            "07_LOGS/Agent-Activity/<approved-excalidraw-run>.md",
            "07_LOGS/Browser-Runs/<approved-excalidraw-run>-screenshot.png",
            "06_AGENTS/Browser-Skills/_drafts/<draft-only-excalidraw-skill>.md",
            "03_INPUTS/Browser-Skill-Candidates/<domain>/<candidate>.md",
        ],
        "approval_effect": (
            "Preview only. A future approval artifact may authorize one local, "
            "throwaway-profile Excalidraw browser/MCP proof after a separate execution pass."
        ),
        "request_digest_sha256": request_digest_sha256,
        "approval_request_written": False,
        "approval_decision_consumed": False,
        "idempotency_marker_written": False,
        "browser_launch_attempted": False,
        "cdp_connection_attempted": False,
        "mcp_invocation_attempted": False,
        "target_navigation_attempted": False,
    }
    record["preview_digest_sha256"] = _sha256(record)
    return record


@dataclass(frozen=True)
class ExcalidrawMCPExecutionApprovalRequest:
    """Read-only request for a future Excalidraw execution approval contract."""

    response_path: str = ""
    requested_by: str = "Codex"
    operator_id: str = "operator"
    execution_mode: str = "shadow_local_canvas_trial"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExcalidrawMCPExecutionApproval:
    """No-write approval/idempotency contract for one future Excalidraw proof."""

    record_type: str
    schema_version: str
    generated_at: str
    status: str
    approval_request_id: str
    request_digest_sha256: str
    approval_request_path: str
    idempotency_marker_path: str
    idempotency_marker_exists: bool
    target_url: str
    target_domain: str
    source_response_path: str
    source_response_status: str
    live_readiness_status: str
    live_readiness_artifact_path: str
    request: ExcalidrawMCPExecutionApprovalRequest
    checks: dict[str, dict[str, Any]] = field(default_factory=dict)
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
    browser_launch_attempted: bool = False
    cdp_connection_attempted: bool = False
    mcp_invocation_attempted: bool = False
    mcp_tool_call_attempted: bool = False
    target_navigation_attempted: bool = False
    screenshot_attempted: bool = False
    real_profile_access_attempted: bool = False
    credential_or_cookie_read_attempted: bool = False
    cookie_export_attempted: bool = False
    browser_profile_sync_attempted: bool = False
    public_tunnel_attempted: bool = False
    browser_harness_used: bool = False
    browser_use_cli_live_used: bool = False
    workflow_use_code_copied: bool = False
    trusted_skill_write_attempted: bool = False
    skill_activation_attempted: bool = False
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
        if self.record_type != EXCALIDRAW_MCP_EXECUTION_APPROVAL_RECORD_TYPE:
            raise ValueError("invalid Excalidraw execution approval record type")
        if self.schema_version != EXCALIDRAW_MCP_EXECUTION_APPROVAL_VERSION:
            raise ValueError("invalid Excalidraw execution approval schema version")
        if self.status not in {
            EXCALIDRAW_MCP_EXECUTION_APPROVAL_READY,
            EXCALIDRAW_MCP_EXECUTION_APPROVAL_BLOCKED,
            EXCALIDRAW_MCP_EXECUTION_APPROVAL_BLOCKED_MARKER_EXISTS,
        }:
            raise ValueError("invalid Excalidraw execution approval status")
        if self.status == EXCALIDRAW_MCP_EXECUTION_APPROVAL_READY and self.blockers:
            raise ValueError("ready approval contract cannot include blockers")
        if self.status != EXCALIDRAW_MCP_EXECUTION_APPROVAL_READY and not self.blockers:
            raise ValueError("blocked approval contract requires blockers")
        if self.status == EXCALIDRAW_MCP_EXECUTION_APPROVAL_READY and self.execution_allowed:
            raise ValueError("ready no-execution contract cannot allow execution")
        for name in DENIED_EFFECTS:
            if getattr(self, name, False):
                raise ValueError(f"{name} must remain false")
            if self.denied_effects.get(name) is not False:
                raise ValueError(f"{name} denied effect must be false")


def build_excalidraw_mcp_execution_approval(
    vault_root: str | Path,
    request: ExcalidrawMCPExecutionApprovalRequest | None = None,
    *,
    generated_at: str | None = None,
    controller_readiness: BrowserControllerSetupReadiness | None = None,
) -> ExcalidrawMCPExecutionApproval:
    """Build a no-write approval/idempotency contract for a future canvas proof."""
    timestamp = generated_at or _now_utc()
    vault = _vault_path(vault_root)
    approval_request = request or ExcalidrawMCPExecutionApprovalRequest()
    readiness = build_excalidraw_readiness_from_response(
        vault,
        response_path=approval_request.response_path,
        generated_at=timestamp,
        write_bridge=False,
        write_live_readiness=False,
        controller_readiness=controller_readiness,
    )
    readiness_payload = readiness.to_dict()
    target_url = str(readiness_payload.get("target_url") or "")
    target_domain = domain_from_url(target_url)
    source_response_path = str(readiness_payload.get("source_response_path") or "")
    live_readiness_artifact_path = str(readiness_payload.get("live_readiness_artifact_path") or "")
    material = _approval_identity_material(
        target_url=target_url,
        target_domain=target_domain,
        source_response_path=source_response_path,
        live_readiness_artifact_path=live_readiness_artifact_path,
        requested_by=approval_request.requested_by,
        execution_mode=approval_request.execution_mode,
    )
    approval_id = _approval_request_id(material)
    request_digest = _sha256(material)
    approval_path = excalidraw_mcp_approval_request_path(vault, approval_id)
    marker_path = excalidraw_mcp_idempotency_marker_path(vault, approval_id)
    marker_exists = marker_path.exists()

    checks = {
        "readiness_from_response_ready_no_execution": {
            "passed": readiness.status == EXCALIDRAW_READINESS_FROM_RESPONSE_READY,
            "status": readiness.status,
            "blockers": list(readiness.blockers),
        },
        "live_readiness_ready_no_execution": {
            "passed": readiness.live_readiness_status
            == "excalidraw_local_browser_mcp_live_readiness_ready_no_execution",
            "status": readiness.live_readiness_status,
            "artifact_path": live_readiness_artifact_path,
        },
        "target_url_present": {
            "passed": bool(target_url),
            "target_url_present": bool(target_url),
        },
        "target_domain_local_only": {
            "passed": target_domain in LOCAL_ONLY_DOMAINS,
            "target_domain": target_domain,
            "allowed_local_domains": sorted(LOCAL_ONLY_DOMAINS),
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
            "browser_launch_attempted": False,
            "cdp_connection_attempted": False,
            "mcp_invocation_attempted": False,
            "idempotency_marker_written": False,
        },
    }
    blockers = [name for name, check in checks.items() if not bool(check["passed"])]
    if marker_exists:
        status = EXCALIDRAW_MCP_EXECUTION_APPROVAL_BLOCKED_MARKER_EXISTS
        next_step = "review_existing_excalidraw_idempotency_marker_before_any_execution"
    elif blockers:
        status = EXCALIDRAW_MCP_EXECUTION_APPROVAL_BLOCKED
        next_step = (
            "excalidraw-local-browser-mcp-live-readiness-with-target"
            if target_url
            else "external-runtime-provide-excalidraw-target-url"
        )
    else:
        status = EXCALIDRAW_MCP_EXECUTION_APPROVAL_READY
        next_step = "excalidraw-local-browser-mcp-proof-execution"

    preview = _build_approval_request_preview(
        generated_at=timestamp,
        approval_request_id=approval_id,
        request_digest_sha256=request_digest,
        target_url=target_url,
        target_domain=target_domain,
        source_response_path=source_response_path,
        live_readiness_artifact_path=live_readiness_artifact_path,
        requested_by=approval_request.requested_by,
        operator_id=approval_request.operator_id,
        execution_mode=approval_request.execution_mode,
    )
    result = ExcalidrawMCPExecutionApproval(
        record_type=EXCALIDRAW_MCP_EXECUTION_APPROVAL_RECORD_TYPE,
        schema_version=EXCALIDRAW_MCP_EXECUTION_APPROVAL_VERSION,
        generated_at=timestamp,
        status=status,
        approval_request_id=approval_id,
        request_digest_sha256=request_digest,
        approval_request_path=approval_path.as_posix(),
        idempotency_marker_path=marker_path.as_posix(),
        idempotency_marker_exists=marker_exists,
        target_url=target_url,
        target_domain=target_domain,
        source_response_path=source_response_path,
        source_response_status=str(readiness_payload.get("source_response_status") or ""),
        live_readiness_status=str(readiness_payload.get("live_readiness_status") or ""),
        live_readiness_artifact_path=live_readiness_artifact_path,
        request=approval_request,
        checks=checks,
        blockers=blockers,
        approval_request_preview=preview,
        idempotency_marker_contract={
            "path": marker_path.as_posix(),
            "marker_written": False,
            "future_write_mode": "exclusive_create_before_browser_launch",
            "duplicate_policy": "block_before_browser_launch",
        },
        required_future_approval_fields=[
            "approval_request_id",
            "request_digest_sha256",
            "target_url",
            "source_response_path",
            "live_readiness_artifact_path",
            "operator_decision: approved",
        ],
        required_future_execution_checks=[
            "approval decision matches request digest",
            "idempotency marker absent before reservation",
            "marker reserved before browser launch",
            "throwaway browser profile only",
            "local loopback target only",
            "draft skill and untrusted candidate outputs only",
        ],
        denied_effects={name: False for name in DENIED_EFFECTS},
        next_step=next_step,
    )
    result.validate()
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Report no-write Excalidraw browser/MCP approval contract.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--response-path", default="", help="Optional target response artifact path.")
    parser.add_argument("--requested-by", default="Codex", help="Runtime/operator requesting the contract.")
    parser.add_argument("--operator-id", default="operator", help="Operator identifier for the preview.")
    parser.add_argument("--execution-mode", default="shadow_local_canvas_trial", help="Future execution mode label.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    request = ExcalidrawMCPExecutionApprovalRequest(
        response_path=args.response_path,
        requested_by=args.requested_by,
        operator_id=args.operator_id,
        execution_mode=args.execution_mode,
    )
    contract = build_excalidraw_mcp_execution_approval(args.vault_root, request)
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
