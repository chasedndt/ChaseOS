"""No-execution local-target setup instructions for Excalidraw proof.

This module converts the previous blocked Excalidraw live-readiness result into
an operator handoff. It does not install dependencies, start an MCP server,
launch a browser, connect to CDP, navigate, enqueue Agent Bus work, or write
skill memory.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXCALIDRAW_TARGET_SETUP_VERSION = "browser.excalidraw_target_setup_instructions.v1"
EXCALIDRAW_TARGET_SETUP_RECORD_TYPE = "excalidraw_local_target_setup_instructions"
EXCALIDRAW_TARGET_SETUP_READY = "excalidraw_local_target_setup_instructions_ready_no_execution"
EXCALIDRAW_TARGET_SETUP_BLOCKED_READINESS = (
    "blocked_excalidraw_target_setup_missing_or_unsafe_readiness"
)

EXCALIDRAW_MCP_LIVE_READINESS_BLOCKED_TARGET_ARTIFACT = Path(
    "07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_live_readiness_20260503_blocked_missing_local_target.json"
)
EXCALIDRAW_TARGET_SETUP_ARTIFACT = Path(
    "07_LOGS/Browser-Runs/excalidraw_local_target_setup_instructions_20260503_ready.json"
)

ALLOWED_TARGET_HOSTS = ("127.0.0.1", "::1", "localhost")

FORBIDDEN_PREVIOUS_READINESS_TRUE_KEYS = (
    "browser_launch_attempted",
    "cdp_connection_attempted",
    "mcp_server_invoked",
    "mcp_tool_call_attempted",
    "network_navigation_attempted",
    "dependency_install_attempted",
    "real_profile_access_attempted",
    "credential_or_cookie_read_attempted",
    "cookie_export_attempted",
    "browser_profile_sync_attempted",
    "public_tunnel_attempted",
    "browser_harness_used",
    "browser_use_cli_live_used",
    "workflow_use_code_copied",
    "trusted_skill_write_attempted",
    "skill_activation_attempted",
    "agent_bus_enqueue_attempted",
    "provider_call_attempted",
    "gate_mutation_attempted",
    "canonical_writeback_attempted",
)

BLOCKED_EFFECTS = (
    "dependency_install",
    "mcp_server_start",
    "mcp_tool_call",
    "browser_launch",
    "cdp_connection",
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
    path = (vault / EXCALIDRAW_TARGET_SETUP_ARTIFACT).resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"Excalidraw setup artifact escapes Browser-Runs: {path}") from exc
    return path


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _previous_readiness_safe(vault: Path) -> bool:
    payload = _read_json(vault / EXCALIDRAW_MCP_LIVE_READINESS_BLOCKED_TARGET_ARTIFACT)
    if not isinstance(payload, dict):
        return False
    return (
        payload.get("record_type") == "excalidraw_local_browser_mcp_live_readiness"
        and payload.get("schema_version") == "browser.excalidraw_mcp_live_readiness.v1"
        and payload.get("status") == "blocked_excalidraw_live_readiness_missing_local_target"
        and payload.get("readiness_artifact_written") is True
        and payload.get("prep_evidence_ready") is True
        and payload.get("browser_controller_ready") is True
        and "local_excalidraw_target_url_not_provided" in payload.get("blockers", [])
        and all(payload.get(key) is False for key in FORBIDDEN_PREVIOUS_READINESS_TRUE_KEYS)
    )


@dataclass(frozen=True)
class ExcalidrawTargetSetupInstructions:
    record_type: str
    schema_version: str
    generated_at: str
    status: str
    setup_artifact_path: str
    setup_artifact_written: bool
    previous_readiness_artifact_path: str
    previous_readiness_safe: bool
    allowed_target_hosts: tuple[str, ...]
    preferred_target_mode: str
    setup_modes: list[dict[str, Any]] = field(default_factory=list)
    runtime_handoff: dict[str, Any] = field(default_factory=dict)
    readiness_rerun_command: str = ""
    live_proof_command_not_authorized: str = ""
    expected_future_artifacts: dict[str, str] = field(default_factory=dict)
    security_constraints: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    blocked_effects: tuple[str, ...] = BLOCKED_EFFECTS
    dependency_install_attempted: bool = False
    mcp_server_start_attempted: bool = False
    mcp_tool_call_attempted: bool = False
    browser_launch_attempted: bool = False
    cdp_connection_attempted: bool = False
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
    next_recommended_pass: str = "excalidraw-local-browser-mcp-live-readiness-with-target"

    def validate(self) -> None:
        if self.record_type != EXCALIDRAW_TARGET_SETUP_RECORD_TYPE:
            raise ValueError("invalid Excalidraw target setup record type")
        if self.schema_version != EXCALIDRAW_TARGET_SETUP_VERSION:
            raise ValueError("invalid Excalidraw target setup schema version")
        if self.status not in {
            EXCALIDRAW_TARGET_SETUP_READY,
            EXCALIDRAW_TARGET_SETUP_BLOCKED_READINESS,
        }:
            raise ValueError("invalid Excalidraw target setup status")
        if self.status == EXCALIDRAW_TARGET_SETUP_READY and self.blockers:
            raise ValueError("ready setup instructions cannot include blockers")
        if self.status != EXCALIDRAW_TARGET_SETUP_READY and not self.blockers:
            raise ValueError("blocked setup instructions require blockers")
        if not self.setup_modes:
            raise ValueError("setup modes are required")
        if not self.runtime_handoff:
            raise ValueError("runtime handoff is required")
        if not self.readiness_rerun_command:
            raise ValueError("readiness rerun command is required")
        if not self.security_constraints:
            raise ValueError("security constraints are required")
        forbidden_flags = (
            self.dependency_install_attempted,
            self.mcp_server_start_attempted,
            self.mcp_tool_call_attempted,
            self.browser_launch_attempted,
            self.cdp_connection_attempted,
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
            raise ValueError("Excalidraw target setup instructions attempted a forbidden effect")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["allowed_target_hosts"] = list(self.allowed_target_hosts)
        payload["security_constraints"] = list(self.security_constraints)
        payload["blockers"] = list(self.blockers)
        payload["blocked_effects"] = list(self.blocked_effects)
        return payload


def build_excalidraw_target_setup_instructions(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    write_instructions: bool = False,
) -> ExcalidrawTargetSetupInstructions:
    """Build and optionally persist Excalidraw target setup instructions."""
    timestamp = generated_at or _now_utc()
    vault = _vault_path(vault_root)
    artifact = _artifact_path(vault)
    previous_path = (vault / EXCALIDRAW_MCP_LIVE_READINESS_BLOCKED_TARGET_ARTIFACT).resolve()
    previous_safe = _previous_readiness_safe(vault)
    blockers = () if previous_safe else ("previous_excalidraw_live_readiness_missing_or_unsafe",)
    status = EXCALIDRAW_TARGET_SETUP_READY if previous_safe else EXCALIDRAW_TARGET_SETUP_BLOCKED_READINESS

    packet = ExcalidrawTargetSetupInstructions(
        record_type=EXCALIDRAW_TARGET_SETUP_RECORD_TYPE,
        schema_version=EXCALIDRAW_TARGET_SETUP_VERSION,
        generated_at=timestamp,
        status=status,
        setup_artifact_path=artifact.as_posix(),
        setup_artifact_written=write_instructions,
        previous_readiness_artifact_path=previous_path.as_posix(),
        previous_readiness_safe=previous_safe,
        allowed_target_hosts=ALLOWED_TARGET_HOSTS,
        preferred_target_mode="local_loopback_canvas_or_local_mcp_target",
        setup_modes=[
            {
                "mode": "local_static_canvas_fixture",
                "recommended_for": "first target availability proof",
                "host_policy": "loopback only",
                "account_required": False,
                "operator_action": (
                    "Ask an external runtime to serve a local HTML canvas or Excalidraw-compatible "
                    "test page on 127.0.0.1 or localhost, then provide the URL to ChaseOS."
                ),
            },
            {
                "mode": "local_excalidraw_mcp_target",
                "recommended_for": "future browser/MCP canvas proof",
                "host_policy": "loopback only, no public tunnel",
                "account_required": False,
                "operator_action": (
                    "Ask an external runtime to install and start a local Excalidraw MCP/canvas "
                    "target outside ChaseOS; ChaseOS receives only the loopback URL."
                ),
            },
            {
                "mode": "public_excalidraw_fallback",
                "recommended_for": "later explicit fallback only",
                "host_policy": "requires separate approval",
                "account_required": False,
                "operator_action": (
                    "Do not use as the next pass unless local targets are unavailable and the "
                    "operator separately approves a no-account public-site trial."
                ),
            },
        ],
        runtime_handoff={
            "handoff_target": "external_agent_runtime_or_operator",
            "target_url_variable": "CHASEOS_EXCALIDRAW_TARGET_URL",
            "target_url_required_shape": "http://127.0.0.1:<port>/ or http://localhost:<port>/",
            "target_must_be_available_before_next_pass": True,
            "chaseos_does_not_install_or_start_target": True,
            "approval_needed_after_target_ready": "separate live proof execution approval",
            "proof_goal": 'draw one rectangle and label it "ChaseOS"',
        },
        readiness_rerun_command=(
            "python -m runtime.browser_runtime.excalidraw_mcp_live_readiness "
            "--vault-root . --local-target-url http://127.0.0.1:<port>/ "
            "--write-readiness --json"
        ),
        live_proof_command_not_authorized=(
            "No live proof command is authorized by this setup-instructions pass."
        ),
        expected_future_artifacts={
            "readiness_ready": "07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_live_readiness_20260503_ready.json",
            "proof_run_log": "07_LOGS/Browser-Runs/excalidraw-local-browser-mcp-proof-20260503_success.json",
            "proof_screenshot": "07_LOGS/Browser-Runs/excalidraw-local-browser-mcp-proof-20260503_screenshot.png",
            "draft_skill": "06_AGENTS/Browser-Skills/_drafts/draft-excalidraw-local-browser-mcp-proof-20260503.md",
            "untrusted_candidate": "03_INPUTS/Browser-Skill-Candidates/excalidraw-com/20260503__candidate-excalidraw-local-browser-mcp-proof-20260503.md",
        },
        security_constraints=(
            "no dependency install from ChaseOS",
            "no browser launch in this pass",
            "no CDP connection in this pass",
            "no MCP server invocation in this pass",
            "no public tunnel",
            "no real browser profile",
            "no saved credentials, cookies, session tokens, or browser history",
            "no real accounts",
            "no trusted skill write or skill activation",
            "no Agent Bus enqueue, provider call, Gate mutation, or canonical writeback",
            "future skill memory must stay draft/untrusted and link back to Browser Run evidence",
        ),
        blockers=blockers,
    )
    packet.validate()
    if write_instructions:
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(json.dumps(packet.to_dict(), indent=2) + "\n", encoding="utf-8")
    return packet


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write no-execution Excalidraw local-target setup instructions."
    )
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument(
        "--write-instructions",
        action="store_true",
        help="Write setup-instructions evidence under Browser-Runs.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    packet = build_excalidraw_target_setup_instructions(
        args.vault_root,
        write_instructions=args.write_instructions,
    )
    payload = packet.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {payload['status']}")
        for blocker in payload["blockers"]:
            print(f"blocker: {blocker}")
        print(f"setup_artifact_written: {payload['setup_artifact_written']}")
        print(f"next_recommended_pass: {payload['next_recommended_pass']}")
    return 0 if packet.status == EXCALIDRAW_TARGET_SETUP_READY else 1


if __name__ == "__main__":
    raise SystemExit(main())
