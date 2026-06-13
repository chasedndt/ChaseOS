"""Prep-only Excalidraw browser/MCP proof contract.

This module prepares the next Browser Runtime production gate without running
it. It does not launch a browser, invoke MCP tools, navigate to Excalidraw, or
write skill memory unless the caller explicitly requests the prep evidence
artifact.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXCALIDRAW_MCP_PROOF_PREP_VERSION = "browser.excalidraw_mcp_proof_prep.v1"
EXCALIDRAW_MCP_PROOF_PREP_RECORD_TYPE = "excalidraw_local_browser_mcp_proof_prep"
EXCALIDRAW_MCP_PROOF_PREP_READY = "excalidraw_local_browser_mcp_proof_prep_ready_no_execution"
EXCALIDRAW_MCP_PROOF_PREP_ARTIFACT = Path(
    "07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_proof_prep_20260503_ready.json"
)

EXCALIDRAW_MCP_PROOF_PREP_BLOCKED_EFFECTS = (
    "browser_launch",
    "cdp_connection",
    "mcp_server_invocation",
    "mcp_tool_call",
    "network_navigation",
    "real_profile_access",
    "credential_or_cookie_read",
    "cookie_export",
    "browser_profile_sync",
    "public_tunnel",
    "browser_harness_use",
    "browser_use_cli_live_run",
    "workflow_use_code_copy",
    "trusted_skill_write",
    "skill_activation",
    "agent_bus_enqueue",
    "provider_call",
    "gate_mutation",
    "canonical_writeback",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _artifact_path(vault: Path) -> Path:
    base = (vault / "07_LOGS/Browser-Runs").resolve()
    path = (vault / EXCALIDRAW_MCP_PROOF_PREP_ARTIFACT).resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"Excalidraw prep artifact escapes Browser-Runs: {path}") from exc
    return path


@dataclass(frozen=True)
class ExcalidrawMCPProofPrepRequest:
    """Operator request for a prep-only Excalidraw browser/MCP proof packet."""

    operator_id: str = "operator"
    requested_by: str = "Codex"
    run_date: str = ""
    proof_goal: str = 'draw one rectangle and label it "ChaseOS"'
    preferred_target_mode: str = "local_mcp_or_local_canvas_first"
    public_excalidraw_fallback_requires_approval: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExcalidrawMCPProofPrep:
    """No-execution preparation packet for a future Excalidraw proof."""

    record_type: str
    schema_version: str
    generated_at: str
    status: str
    request: ExcalidrawMCPProofPrepRequest
    run_slug: str
    prep_artifact_path: str
    prep_artifact_written: bool
    preferred_target_mode: str
    target_options: list[dict[str, Any]] = field(default_factory=list)
    external_references: list[dict[str, str]] = field(default_factory=list)
    required_preconditions: list[str] = field(default_factory=list)
    planned_future_sequence: list[dict[str, Any]] = field(default_factory=list)
    expected_future_artifacts: dict[str, str] = field(default_factory=dict)
    skill_memory_rules: list[str] = field(default_factory=list)
    live_proof_allowed_in_this_pass: bool = False
    browser_launch_attempted: bool = False
    cdp_connection_attempted: bool = False
    mcp_server_invoked: bool = False
    mcp_tool_call_attempted: bool = False
    network_navigation_attempted: bool = False
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
    blocked_effects: tuple[str, ...] = EXCALIDRAW_MCP_PROOF_PREP_BLOCKED_EFFECTS
    next_recommended_pass: str = "excalidraw-local-browser-mcp-live-readiness"

    def validate(self) -> None:
        if self.status != EXCALIDRAW_MCP_PROOF_PREP_READY:
            raise ValueError("invalid Excalidraw proof prep status")
        if self.schema_version != EXCALIDRAW_MCP_PROOF_PREP_VERSION:
            raise ValueError("invalid Excalidraw proof prep schema version")
        if not self.run_slug:
            raise ValueError("run_slug is required")
        if not self.prep_artifact_path:
            raise ValueError("prep_artifact_path is required")
        if not self.target_options:
            raise ValueError("target_options are required")
        if not self.required_preconditions:
            raise ValueError("required_preconditions are required")
        if not self.planned_future_sequence:
            raise ValueError("planned_future_sequence is required")
        if not self.expected_future_artifacts:
            raise ValueError("expected_future_artifacts are required")
        if not self.skill_memory_rules:
            raise ValueError("skill_memory_rules are required")
        forbidden_flags = (
            self.live_proof_allowed_in_this_pass,
            self.browser_launch_attempted,
            self.cdp_connection_attempted,
            self.mcp_server_invoked,
            self.mcp_tool_call_attempted,
            self.network_navigation_attempted,
            self.real_profile_access_attempted,
            self.credential_or_cookie_read_attempted,
            self.cookie_export_attempted,
            self.browser_profile_sync_attempted,
            self.public_tunnel_attempted,
            self.browser_harness_used,
            self.browser_use_cli_live_used,
            self.workflow_use_code_copied,
            self.trusted_skill_write_attempted,
            self.skill_activation_attempted,
            self.agent_bus_enqueue_attempted,
            self.provider_call_attempted,
            self.gate_mutation_attempted,
            self.canonical_writeback_attempted,
        )
        if any(forbidden_flags):
            raise ValueError("Excalidraw proof prep attempted a forbidden effect")
        if not self.blocked_effects:
            raise ValueError("blocked effects must be declared")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["request"] = self.request.to_dict()
        payload["blocked_effects"] = list(self.blocked_effects)
        return payload


def build_excalidraw_mcp_proof_prep(
    vault_root: str | Path,
    request: ExcalidrawMCPProofPrepRequest | None = None,
    *,
    generated_at: str | None = None,
    write_prep: bool = False,
) -> ExcalidrawMCPProofPrep:
    """Build and optionally persist the prep-only Excalidraw proof packet."""
    timestamp = generated_at or _now_utc()
    prep_request = request or ExcalidrawMCPProofPrepRequest()
    run_date = prep_request.run_date or timestamp[:10].replace("-", "")
    run_slug = f"excalidraw-local-browser-mcp-proof-{run_date}"
    vault = _vault_path(vault_root)
    artifact = _artifact_path(vault)
    expected_artifacts = {
        "browser_run_log": f"07_LOGS/Browser-Runs/{run_slug}_success.json",
        "screenshot": f"07_LOGS/Browser-Runs/{run_slug}_screenshot.png",
        "agent_activity": f"07_LOGS/Agent-Activity/{run_date[:4]}-{run_date[4:6]}-{run_date[6:]}-browser-excalidraw-local-browser-mcp-proof.md",
        "draft_skill": f"06_AGENTS/Browser-Skills/_drafts/draft-{run_slug}.md",
        "untrusted_candidate": f"03_INPUTS/Browser-Skill-Candidates/excalidraw-com/{run_date}__candidate-{run_slug}.md",
    }
    packet = ExcalidrawMCPProofPrep(
        record_type=EXCALIDRAW_MCP_PROOF_PREP_RECORD_TYPE,
        schema_version=EXCALIDRAW_MCP_PROOF_PREP_VERSION,
        generated_at=timestamp,
        status=EXCALIDRAW_MCP_PROOF_PREP_READY,
        request=prep_request,
        run_slug=run_slug,
        prep_artifact_path=artifact.as_posix(),
        prep_artifact_written=write_prep,
        preferred_target_mode=prep_request.preferred_target_mode,
        target_options=[
            {
                "mode": "local_mcp_or_local_canvas_first",
                "allowed_hosts": ["127.0.0.1", "localhost"],
                "requires_public_network": False,
                "requires_account_login": False,
                "requires_public_tunnel": False,
                "notes": "Preferred future proof target. Bind local Excalidraw/MCP/canvas tooling to loopback only.",
            },
            {
                "mode": "public_excalidraw_fallback",
                "url": "https://excalidraw.com/",
                "allowed_domains": ["excalidraw.com"],
                "requires_explicit_operator_approval": True,
                "requires_throwaway_profile": True,
                "requires_account_login": False,
                "notes": "Fallback only if local target is unavailable; use no account and no collaboration/share link.",
            },
        ],
        external_references=[
            {
                "repo": "yctimlin/mcp_excalidraw",
                "url": "https://github.com/yctimlin/mcp_excalidraw",
                "chaseos_use": "Reference-only future local MCP/canvas candidate; no code copied or invoked in this pass.",
            },
            {
                "repo": "browser-use/browser-harness",
                "url": "https://github.com/browser-use/browser-harness",
                "chaseos_use": "Reference-only domain/interaction skill pattern; raw harness not adopted.",
            },
        ],
        required_preconditions=[
            "Operator selects local loopback target or explicitly approves public Excalidraw fallback.",
            "Browser launches with an isolated throwaway profile only.",
            "No account login, collaboration session, public share link, cookies export, or saved credentials.",
            "If MCP is used, the server must bind to 127.0.0.1 or localhost and expose no public tunnel.",
            "All output is limited to Browser Run evidence, Agent Activity, screenshot, draft skill, and untrusted candidate paths.",
            "Every learned canvas/site pattern remains draft-only until SiteOps/Gate review.",
        ],
        planned_future_sequence=[
            {"step": 1, "action": "preflight target", "effect": "verify local loopback or approved fallback target"},
            {"step": 2, "action": "launch isolated browser", "effect": "throwaway profile only, no real profile"},
            {"step": 3, "action": "open target", "effect": "navigate only to the approved Excalidraw target"},
            {"step": 4, "action": "inspect canvas bounds", "effect": "derive relative canvas coordinates, not durable raw pixels"},
            {"step": 5, "action": "perform harmless drawing", "effect": prep_request.proof_goal},
            {"step": 6, "action": "capture screenshot", "effect": "write evidence under 07_LOGS/Browser-Runs/"},
            {"step": 7, "action": "write draft memory", "effect": "draft-only skill and untrusted candidate linked to run evidence"},
        ],
        expected_future_artifacts=expected_artifacts,
        skill_memory_rules=[
            "Store durable canvas strategy, selectors, waits, traps, and verification rules only.",
            "Do not store secrets, cookies, session tokens, account state, collaboration links, or raw personal data.",
            "Do not store raw pixel coordinates as durable selectors; prefer canvas-bound-relative strategy.",
            "Generated memory remains draft or untrusted candidate only until SiteOps promotion review.",
        ],
    )
    packet.validate()
    if write_prep:
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(json.dumps(packet.to_dict(), indent=2) + "\n", encoding="utf-8")
    return packet


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare the Excalidraw browser/MCP proof without execution.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--operator-id", default="operator", help="Operator identifier for the prep packet.")
    parser.add_argument("--requested-by", default="Codex", help="Runtime requesting the prep packet.")
    parser.add_argument("--run-date", default="", help="YYYYMMDD run date for future artifact naming.")
    parser.add_argument("--write-prep", action="store_true", help="Write the prep evidence JSON under Browser-Runs.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    request = ExcalidrawMCPProofPrepRequest(
        operator_id=args.operator_id,
        requested_by=args.requested_by,
        run_date=args.run_date,
    )
    packet = build_excalidraw_mcp_proof_prep(args.vault_root, request, write_prep=args.write_prep)
    payload = packet.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {payload['status']}")
        print(f"run_slug: {payload['run_slug']}")
        print(f"prep_artifact_written: {payload['prep_artifact_written']}")
        print(f"next_recommended_pass: {payload['next_recommended_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
