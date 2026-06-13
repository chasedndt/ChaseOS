"""No-execution setup request for external Browser Runtime branches.

This module turns the Studio external-runtime readiness gate into a precise
operator/runtime handoff. It does not install dependencies, start targets,
probe URLs, launch browsers, invoke MCP, run Browser Use CLI, grant approvals,
write skills, enqueue Agent Bus work, call providers/connectors, mutate Gate,
or write canonical ChaseOS state.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.external_runtime_readiness import (
    DEFAULT_EVIDENCE_ROOT,
    FORBIDDEN_EFFECTS,
    STATUS_BLOCKED,
    STATUS_READY_BOTH,
    STATUS_READY_BROWSER_USE,
    STATUS_READY_EXCALIDRAW,
    build_studio_external_runtime_readiness,
)


RECORD_TYPE = "studio_external_runtime_setup_request"
SCHEMA_VERSION = "studio.external_runtime_setup_request.v1"
STATUS_REQUEST_READY = "external_runtime_setup_request_ready_for_operator"
STATUS_NO_REQUEST_NEEDED = "external_runtime_setup_not_needed_readiness_already_open"
BRANCH_AUTO = "auto"
BRANCH_BROWSER_USE = "browser-use"
BRANCH_EXCALIDRAW = "excalidraw"
BRANCH_BOTH = "both"
BRANCH_CHOICES = (BRANCH_AUTO, BRANCH_BROWSER_USE, BRANCH_EXCALIDRAW, BRANCH_BOTH)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _branch_list(branch: str, readiness: dict[str, Any]) -> tuple[str, ...]:
    if branch == BRANCH_BROWSER_USE:
        return (BRANCH_BROWSER_USE,)
    if branch == BRANCH_EXCALIDRAW:
        return (BRANCH_EXCALIDRAW,)
    if branch == BRANCH_BOTH:
        return (BRANCH_BROWSER_USE, BRANCH_EXCALIDRAW)
    if readiness.get("status") == STATUS_READY_BROWSER_USE:
        return (BRANCH_EXCALIDRAW,)
    if readiness.get("status") == STATUS_READY_EXCALIDRAW:
        return (BRANCH_BROWSER_USE,)
    if readiness.get("status") == STATUS_READY_BOTH:
        return ()
    return (BRANCH_BROWSER_USE, BRANCH_EXCALIDRAW)


def _browser_use_request() -> dict[str, Any]:
    return {
        "branch": BRANCH_BROWSER_USE,
        "objective": "make browser-use executable discoverable outside ChaseOS for a later no-account validation pass",
        "external_operator_actions": [
            "Install or expose the browser-use CLI outside the ChaseOS repository.",
            "Use no real browser profile, no credentials, no cookies, no synced profile, and no public tunnel.",
            "Do not edit native Studio shell files, command contracts, shared indexes, Gate policy, or canonical state.",
            "After setup, rerun the read-only readiness gate before any live validation.",
        ],
        "required_evidence": [
            "browser-use executable is on PATH for the runtime that will perform validation",
            "Browser Runtime config remains throwaway-only and credential-free",
            "fresh `chaseos studio external-runtime-readiness --json` result with browser_use_branch_ready=true",
        ],
        "handoff_commands": [
            "python -m runtime.browser_runtime.browser_use_cli_validation --vault-root . --json",
            "python -m chaseos studio external-runtime-readiness --json",
        ],
        "forbidden": [
            "dependency install by ChaseOS",
            "real profile or credential use",
            "Browser Use CLI live run before operator approval",
            "trusted skill write or activation",
            "provider/connector call",
            "Agent Bus enqueue",
            "Gate mutation",
            "canonical writeback",
        ],
    }


def _excalidraw_request() -> dict[str, Any]:
    return {
        "branch": BRANCH_EXCALIDRAW,
        "objective": "provide an accepted local loopback Excalidraw/MCP/canvas target response",
        "external_operator_actions": [
            "Start or identify a safe local Excalidraw/MCP/canvas target outside this pass.",
            "Keep the target on loopback only: 127.0.0.1, localhost, or ::1.",
            "Use no accounts, credentials, cookies, real profiles, public tunnels, or external network exposure.",
            "Record the target through the existing no-probe target response intake.",
            "Rerun Studio external-runtime readiness before any live proof.",
        ],
        "accepted_response_shape": {
            "target_url": "http://127.0.0.1:<port>/"
        },
        "response_store": "03_INPUTS/Browser-Target-Responses/_pending/",
        "handoff_commands": [
            "python -m runtime.browser_runtime.excalidraw_target_response --vault-root . --target-url http://127.0.0.1:<port>/ --write-response --json",
            "python -m chaseos studio external-runtime-readiness --json",
        ],
        "required_evidence": [
            "accepted loopback target response under 03_INPUTS/Browser-Target-Responses/_pending/",
            "fresh `chaseos studio external-runtime-readiness --json` result with excalidraw_branch_ready=true",
            "separate approval/readiness evidence before any live browser/MCP proof",
        ],
        "forbidden": [
            "server start by this ChaseOS pass",
            "network probe by this setup request",
            "browser launch",
            "CDP connection",
            "MCP invocation",
            "target navigation",
            "approval execution",
            "trusted skill write or activation",
            "provider/connector call",
            "Agent Bus enqueue",
            "Gate mutation",
            "canonical writeback",
        ],
    }


def _markdown(packet: "StudioExternalRuntimeSetupRequest") -> str:
    payload = packet.to_dict()
    lines = [
        "# Studio External Runtime Setup Request",
        "",
        f"- Generated: {payload['generated_at']}",
        f"- Status: {payload['status']}",
        f"- Requested branches: {', '.join(payload['requested_branches']) or 'none'}",
        f"- Next operator action: {payload['next_operator_action']}",
        "",
        "## Current Readiness",
        f"- Readiness status: {payload['readiness']['status']}",
        f"- Browser Use branch ready: {payload['readiness']['browser_use_branch_ready']}",
        f"- Excalidraw branch ready: {payload['readiness']['excalidraw_branch_ready']}",
        "",
        "## Blockers",
    ]
    for blocker in payload["readiness"].get("blockers", []):
        lines.append(f"- {blocker}")
    if not payload["readiness"].get("blockers"):
        lines.append("- None")
    lines.extend(["", "## Requests"])
    for request in payload["setup_requests"]:
        lines.append(f"### {request['branch']}")
        lines.append(f"- Objective: {request['objective']}")
        lines.append("- Handoff commands:")
        for command in request.get("handoff_commands", []):
            lines.append(f"  - `{command}`")
        lines.append("- Forbidden:")
        for forbidden in request.get("forbidden", []):
            lines.append(f"  - {forbidden}")
        lines.append("")
    lines.extend(
        [
            "## Boundaries",
            "- No dependency install.",
            "- No server start, network probe, browser launch, CDP connection, MCP invocation, or target navigation.",
            "- No Browser Use CLI live run, approval execution, trusted skill write, skill activation, Agent Bus write, provider/connector call, Gate mutation, or canonical writeback.",
            "",
        ]
    )
    return "\n".join(lines)


@dataclass(frozen=True)
class StudioExternalRuntimeSetupRequest:
    record_type: str
    schema_version: str
    generated_at: str
    status: str
    vault_root: str
    requested_branches: tuple[str, ...]
    readiness: dict[str, Any]
    setup_requests: tuple[dict[str, Any], ...]
    next_operator_action: str
    read_only: bool = True
    writes_evidence: bool = False
    proposal_packet_only: bool = True
    governed_proposal_packet: dict[str, Any] = field(
        default_factory=lambda: {
            "packet_type": "external_runtime_setup_request",
            "governed_by": "ChaseOS Gate/AOR lower-phase approval contracts",
            "studio_executes_request": False,
            "approval_consumed": False,
            "config_mutation_attempted": False,
            "credential_write_attempted": False,
            "runtime_dispatch_attempted": False,
            "canonical_promotion_attempted": False,
            "lower_phase_browser_runtime_dispatch_lane": {
                "manifest": "runtime/studio/chat_browser_runtime_dispatch_lane.py",
                "target_profile": "siteops.browser_cdp_read_only_loopback.v1",
                "approval_required": True,
                "visible_control_ux_required": True,
                "direct_studio_browser_authority": False,
                "credential_or_session_access_allowed": False,
            },
        }
    )
    dependency_install_attempted: bool = False
    subprocess_probe_attempted: bool = False
    server_start_attempted: bool = False
    network_probe_attempted: bool = False
    browser_launch_attempted: bool = False
    browser_use_cli_live_run_attempted: bool = False
    cdp_connection_attempted: bool = False
    mcp_invocation_attempted: bool = False
    mcp_tool_call_attempted: bool = False
    target_navigation_attempted: bool = False
    screenshot_capture_attempted: bool = False
    approval_grant_attempted: bool = False
    approval_execution_attempted: bool = False
    approval_decision_consumed: bool = False
    idempotency_marker_written: bool = False
    real_profile_access_attempted: bool = False
    credential_or_cookie_read_attempted: bool = False
    cookie_export_attempted: bool = False
    browser_profile_sync_attempted: bool = False
    public_tunnel_attempted: bool = False
    trusted_skill_write_attempted: bool = False
    skill_activation_attempted: bool = False
    agent_bus_enqueue_attempted: bool = False
    provider_call_attempted: bool = False
    connector_call_attempted: bool = False
    gate_mutation_attempted: bool = False
    canonical_writeback_attempted: bool = False
    forbidden_effects: tuple[str, ...] = FORBIDDEN_EFFECTS

    def validate(self) -> None:
        if self.record_type != RECORD_TYPE:
            raise ValueError("invalid Studio external runtime setup request record type")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("invalid Studio external runtime setup request schema version")
        if self.status not in {STATUS_REQUEST_READY, STATUS_NO_REQUEST_NEEDED}:
            raise ValueError("invalid Studio external runtime setup request status")
        if not self.read_only:
            raise ValueError("external runtime setup request must remain read-only")
        if not self.proposal_packet_only:
            raise ValueError("external runtime setup request must remain proposal-packet-only")
        if self.governed_proposal_packet.get("studio_executes_request") is not False:
            raise ValueError("Studio setup request packets must not execute requests")
        if self.governed_proposal_packet.get("approval_consumed") is not False:
            raise ValueError("Studio setup request packets must not consume approvals")
        for branch in self.requested_branches:
            if branch not in {BRANCH_BROWSER_USE, BRANCH_EXCALIDRAW}:
                raise ValueError("invalid requested setup branch")
        if self.status == STATUS_REQUEST_READY and not self.setup_requests:
            raise ValueError("setup request status requires setup requests")
        forbidden_flags = (
            self.dependency_install_attempted,
            self.subprocess_probe_attempted,
            self.server_start_attempted,
            self.network_probe_attempted,
            self.browser_launch_attempted,
            self.browser_use_cli_live_run_attempted,
            self.cdp_connection_attempted,
            self.mcp_invocation_attempted,
            self.mcp_tool_call_attempted,
            self.target_navigation_attempted,
            self.screenshot_capture_attempted,
            self.approval_grant_attempted,
            self.approval_execution_attempted,
            self.approval_decision_consumed,
            self.idempotency_marker_written,
            self.real_profile_access_attempted,
            self.credential_or_cookie_read_attempted,
            self.cookie_export_attempted,
            self.browser_profile_sync_attempted,
            self.public_tunnel_attempted,
            self.trusted_skill_write_attempted,
            self.skill_activation_attempted,
            self.agent_bus_enqueue_attempted,
            self.provider_call_attempted,
            self.connector_call_attempted,
            self.gate_mutation_attempted,
            self.canonical_writeback_attempted,
        )
        if any(forbidden_flags):
            raise ValueError("Studio external runtime setup request attempted a forbidden effect")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["requested_branches"] = list(self.requested_branches)
        payload["setup_requests"] = list(self.setup_requests)
        payload["forbidden_effects"] = list(self.forbidden_effects)
        return payload


def build_studio_external_runtime_setup_request(
    vault_root: str | Path,
    *,
    branch: str = BRANCH_AUTO,
    generated_at: str | None = None,
    readiness: Any | None = None,
) -> StudioExternalRuntimeSetupRequest:
    """Build a no-execution external setup handoff from current readiness."""

    if branch not in BRANCH_CHOICES:
        raise ValueError("invalid external setup branch")
    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    readiness_payload = (
        readiness.to_dict()
        if hasattr(readiness, "to_dict")
        else readiness
        if isinstance(readiness, dict)
        else build_studio_external_runtime_readiness(vault, generated_at=timestamp).to_dict()
    )
    requested = _branch_list(branch, readiness_payload)
    requests: list[dict[str, Any]] = []
    if BRANCH_BROWSER_USE in requested:
        requests.append(_browser_use_request())
    if BRANCH_EXCALIDRAW in requested:
        requests.append(_excalidraw_request())

    status = STATUS_REQUEST_READY if requests else STATUS_NO_REQUEST_NEEDED
    if status == STATUS_NO_REQUEST_NEEDED:
        next_action = "Readiness already reports both external branches available; choose the governed validation/proof branch."
    else:
        next_action = (
            "Have the external runtime/operator complete one requested setup branch, then rerun "
            "`chaseos studio external-runtime-readiness --json`."
        )
    packet = StudioExternalRuntimeSetupRequest(
        record_type=RECORD_TYPE,
        schema_version=SCHEMA_VERSION,
        generated_at=timestamp,
        status=status,
        vault_root=str(vault),
        requested_branches=requested,
        readiness=readiness_payload,
        setup_requests=tuple(requests),
        next_operator_action=next_action,
    )
    packet.validate()
    return packet


def write_studio_external_runtime_setup_request_evidence(
    vault_root: str | Path,
    packet: StudioExternalRuntimeSetupRequest,
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = Path(evidence_root) if evidence_root is not None else DEFAULT_EVIDENCE_ROOT
    if root.is_absolute():
        raise ValueError("evidence root must be vault-relative")
    slug = evidence_slug or datetime.now(timezone.utc).strftime(
        "%Y-%m-%d-studio-external-runtime-setup-request"
    )
    base = vault / root / slug
    json_path = base.with_suffix(".json")
    md_path = base.with_suffix(".md")
    _write_json(json_path, packet.to_dict())
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(_markdown(packet), encoding="utf-8")
    return {
        "written": True,
        "json_path": str(json_path),
        "markdown_path": str(md_path),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write or print a no-execution external runtime setup request."
    )
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument(
        "--branch",
        choices=BRANCH_CHOICES,
        default=BRANCH_AUTO,
        help="External branch request to produce; auto requests only currently blocked branches.",
    )
    parser.add_argument("--write-evidence", action="store_true", help="Write JSON/Markdown evidence.")
    parser.add_argument("--evidence-slug", default=None, metavar="SLUG")
    parser.add_argument(
        "--evidence-root",
        default=None,
        metavar="PATH",
        help="Vault-relative evidence root; defaults to 07_LOGS/Studio-Graph-Views",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    packet = build_studio_external_runtime_setup_request(args.vault_root, branch=args.branch)
    payload = packet.to_dict()
    if args.write_evidence:
        payload["evidence_write"] = write_studio_external_runtime_setup_request_evidence(
            args.vault_root,
            packet,
            evidence_slug=args.evidence_slug,
            evidence_root=args.evidence_root,
        )
        payload["writes_evidence"] = True
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {payload['status']}")
        print(f"requested_branches: {', '.join(payload['requested_branches']) or 'none'}")
        print(f"next_operator_action: {payload['next_operator_action']}")
        print(f"readiness_status: {payload['readiness']['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
