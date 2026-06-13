"""Fail-closed start gate for external Studio Browser Runtime branches.

This module turns the broader external-runtime readiness report into a specific
yes/no branch-start decision. It does not install dependencies, start servers,
probe URLs, launch browsers, invoke Browser Use CLI, connect CDP, invoke MCP,
grant approvals, enqueue Agent Bus tasks, call providers/connectors, mutate
Gate, or write canonical ChaseOS state.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.browser_runtime.excalidraw_live_chain_readiness import (
    EXCALIDRAW_LIVE_CHAIN_READINESS_READY,
)
from runtime.studio.external_runtime_readiness import (
    DEFAULT_EVIDENCE_ROOT,
    FORBIDDEN_EFFECTS,
    STATUS_BLOCKED as READINESS_BLOCKED,
    build_studio_external_runtime_readiness,
)


RECORD_TYPE = "studio_external_runtime_branch_gate"
SCHEMA_VERSION = "studio.external_runtime_branch_gate.v1"
STATUS_READY = "external_runtime_branch_gate_ready"
STATUS_BLOCKED = "external_runtime_branch_gate_blocked"

BRANCH_BROWSER_USE = "browser-use-cli-external-runtime-validation"
BRANCH_EXCALIDRAW_TARGET = "excalidraw-target-and-readiness"
BRANCH_EXCALIDRAW_PROOF = "excalidraw-live-browser-mcp-proof"
BRANCH_CHOICES = (
    BRANCH_BROWSER_USE,
    BRANCH_EXCALIDRAW_TARGET,
    BRANCH_EXCALIDRAW_PROOF,
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _readiness_dict(readiness: Any) -> dict[str, Any]:
    if isinstance(readiness, dict):
        return readiness
    if hasattr(readiness, "to_dict"):
        return readiness.to_dict()
    raise TypeError("readiness must be a dict or expose to_dict()")


def _blocked_effect_map() -> dict[str, bool]:
    return {effect: False for effect in FORBIDDEN_EFFECTS}


def _branch_preconditions(branch: str) -> tuple[str, ...]:
    if branch == BRANCH_BROWSER_USE:
        return (
            "browser-use executable is discoverable outside ChaseOS",
            "Browser Runtime config remains throwaway-only and credential-free",
            "`chaseos studio external-runtime-readiness --json` reports browser_use_branch_ready=true",
            "operator separately approves any future no-account live validation run",
        )
    if branch == BRANCH_EXCALIDRAW_TARGET:
        return (
            "accepted local loopback Excalidraw target response exists",
            "`chaseos studio external-runtime-readiness --json` reports excalidraw_branch_ready=true",
            "target stays on localhost, 127.0.0.1, or ::1",
            "no live browser/MCP proof starts in this target/readiness branch",
        )
    if branch == BRANCH_EXCALIDRAW_PROOF:
        return (
            "accepted local loopback Excalidraw target response exists",
            "live-readiness evidence is ready",
            "execution approval contract is ready",
            "proof execution shell is ready no-execution before any live run",
            "operator separately approves the live proof execution pass",
        )
    raise ValueError("invalid external runtime branch")


def _allowed_scope(branch: str) -> tuple[str, ...]:
    if branch == BRANCH_BROWSER_USE:
        return (
            "no-account Browser Use CLI validation planning",
            "read-only CLI discoverability/config verification",
            "evidence writing only when an explicit evidence flag is used by that branch",
        )
    if branch == BRANCH_EXCALIDRAW_TARGET:
        return (
            "target response/readiness validation",
            "read-only chain status inspection",
            "approval/proof preview only; no live proof execution",
        )
    if branch == BRANCH_EXCALIDRAW_PROOF:
        return (
            "one separately approved local loopback throwaway-profile proof branch",
            "exact-once marker reservation only inside the future governed execution pass",
            "draft/untrusted skill outputs only after the future governed execution pass",
        )
    raise ValueError("invalid external runtime branch")


def _next_step(branch: str, can_start: bool) -> str:
    if can_start:
        return branch
    if branch == BRANCH_BROWSER_USE:
        return "external-runtime-provide-browser-use-cli"
    if branch == BRANCH_EXCALIDRAW_TARGET:
        return "external-runtime-provide-excalidraw-loopback-target"
    return "complete-excalidraw-target-readiness-and-approval-before-live-proof"


def _branch_decision(branch: str, readiness: dict[str, Any]) -> tuple[bool, tuple[str, ...]]:
    if branch == BRANCH_BROWSER_USE:
        if readiness.get("browser_use_branch_ready") is True:
            return True, ()
        blockers = [
            blocker
            for blocker in readiness.get("blockers", ())
            if str(blocker).startswith("browser_use:")
        ]
        return False, tuple(blockers or ("browser_use_branch_not_ready",))

    if branch == BRANCH_EXCALIDRAW_TARGET:
        if readiness.get("excalidraw_branch_ready") is True:
            return True, ()
        blockers = [
            blocker
            for blocker in readiness.get("blockers", ())
            if str(blocker).startswith("excalidraw_")
        ]
        return False, tuple(blockers or ("excalidraw_branch_not_ready",))

    if branch == BRANCH_EXCALIDRAW_PROOF:
        chain = readiness.get("excalidraw_live_chain", {})
        if chain.get("status") == EXCALIDRAW_LIVE_CHAIN_READINESS_READY:
            return True, ()
        blockers = [
            f"excalidraw_live_chain:{blocker}"
            for blocker in chain.get("blockers", ())
        ]
        if not blockers:
            blockers.append(f"excalidraw_live_chain_status:{chain.get('status')}")
        return False, tuple(blockers)

    raise ValueError("invalid external runtime branch")


def _markdown(gate: "StudioExternalRuntimeBranchGate") -> str:
    payload = gate.to_dict()
    lines = [
        "# Studio External Runtime Branch Gate",
        "",
        f"- Generated: {payload['generated_at']}",
        f"- Branch: {payload['branch']}",
        f"- Status: {payload['status']}",
        f"- Can start branch: {payload['can_start_branch']}",
        f"- Next allowed step: {payload['next_allowed_step']}",
        "",
        "## Blockers",
    ]
    for blocker in payload["blockers"]:
        lines.append(f"- {blocker}")
    if not payload["blockers"]:
        lines.append("- None")
    lines.extend(["", "## Required Preconditions"])
    for item in payload["required_preconditions"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Allowed Scope"])
    for item in payload["allowed_scope"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Boundaries",
            "- No dependency install, server start, network probe, browser launch, Browser Use CLI live run, CDP connection, MCP invocation, approval execution, provider/connector call, Agent Bus write, Gate mutation, or canonical writeback.",
            "",
        ]
    )
    return "\n".join(lines)


@dataclass(frozen=True)
class StudioExternalRuntimeBranchGate:
    record_type: str
    schema_version: str
    generated_at: str
    status: str
    vault_root: str
    branch: str
    can_start_branch: bool
    readiness_status: str
    readiness: dict[str, Any]
    blockers: tuple[str, ...]
    required_preconditions: tuple[str, ...]
    allowed_scope: tuple[str, ...]
    next_allowed_step: str
    read_only: bool = True
    writes_evidence: bool = False
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
    denied_effects: dict[str, bool] | None = None

    def validate(self) -> None:
        if self.record_type != RECORD_TYPE:
            raise ValueError("invalid Studio external runtime branch gate record type")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("invalid Studio external runtime branch gate schema version")
        if self.status not in {STATUS_READY, STATUS_BLOCKED}:
            raise ValueError("invalid Studio external runtime branch gate status")
        if self.branch not in BRANCH_CHOICES:
            raise ValueError("invalid external runtime branch")
        if not self.read_only:
            raise ValueError("external runtime branch gate must remain read-only")
        if self.status == STATUS_READY and not self.can_start_branch:
            raise ValueError("ready branch gate must allow branch start")
        if self.status == STATUS_BLOCKED and self.can_start_branch:
            raise ValueError("blocked branch gate cannot allow branch start")
        if self.status == STATUS_BLOCKED and not self.blockers:
            raise ValueError("blocked branch gate requires blockers")
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
            raise ValueError("Studio external runtime branch gate attempted a forbidden effect")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["blockers"] = list(self.blockers)
        payload["required_preconditions"] = list(self.required_preconditions)
        payload["allowed_scope"] = list(self.allowed_scope)
        payload["forbidden_effects"] = list(self.forbidden_effects)
        payload["denied_effects"] = self.denied_effects or _blocked_effect_map()
        return payload


def build_studio_external_runtime_branch_gate(
    vault_root: str | Path,
    *,
    branch: str,
    generated_at: str | None = None,
    readiness: Any | None = None,
) -> StudioExternalRuntimeBranchGate:
    if branch not in BRANCH_CHOICES:
        raise ValueError("invalid external runtime branch")
    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    readiness_payload = _readiness_dict(
        readiness
        if readiness is not None
        else build_studio_external_runtime_readiness(vault, generated_at=timestamp)
    )
    can_start, blockers = _branch_decision(branch, readiness_payload)
    if readiness_payload.get("status") == READINESS_BLOCKED and not blockers:
        blockers = tuple(readiness_payload.get("blockers", ())) or (
            "external_runtime_readiness_blocked",
        )
    status = STATUS_READY if can_start else STATUS_BLOCKED
    gate = StudioExternalRuntimeBranchGate(
        record_type=RECORD_TYPE,
        schema_version=SCHEMA_VERSION,
        generated_at=timestamp,
        status=status,
        vault_root=str(vault),
        branch=branch,
        can_start_branch=can_start,
        readiness_status=str(readiness_payload.get("status", "")),
        readiness=readiness_payload,
        blockers=tuple(blockers),
        required_preconditions=_branch_preconditions(branch),
        allowed_scope=_allowed_scope(branch),
        next_allowed_step=_next_step(branch, can_start),
        denied_effects=_blocked_effect_map(),
    )
    gate.validate()
    return gate


def write_studio_external_runtime_branch_gate_evidence(
    vault_root: str | Path,
    gate: StudioExternalRuntimeBranchGate,
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = Path(evidence_root) if evidence_root is not None else DEFAULT_EVIDENCE_ROOT
    if root.is_absolute():
        raise ValueError("evidence root must be vault-relative")
    slug = evidence_slug or datetime.now(timezone.utc).strftime(
        f"%Y-%m-%d-studio-external-runtime-branch-gate-{gate.branch}"
    )
    base = vault / root / slug
    json_path = base.with_suffix(".json")
    md_path = base.with_suffix(".md")
    _write_json(json_path, gate.to_dict())
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(_markdown(gate), encoding="utf-8")
    return {
        "written": True,
        "json_path": str(json_path),
        "markdown_path": str(md_path),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fail-closed start gate for external Browser Runtime branches."
    )
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument(
        "--branch",
        choices=BRANCH_CHOICES,
        required=True,
        help="External branch that wants to start.",
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
    gate = build_studio_external_runtime_branch_gate(
        args.vault_root,
        branch=args.branch,
    )
    payload = gate.to_dict()
    if args.write_evidence:
        payload["evidence_write"] = write_studio_external_runtime_branch_gate_evidence(
            args.vault_root,
            gate,
            evidence_slug=args.evidence_slug,
            evidence_root=args.evidence_root,
        )
        payload["writes_evidence"] = True
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {payload['status']}")
        print(f"branch: {payload['branch']}")
        print(f"can_start_branch: {payload['can_start_branch']}")
        print(f"next_allowed_step: {payload['next_allowed_step']}")
        for blocker in payload["blockers"]:
            print(f"blocker: {blocker}")
    return 0 if gate.can_start_branch else 1


if __name__ == "__main__":
    raise SystemExit(main())
