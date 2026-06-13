"""No-execution Excalidraw browser/MCP live-readiness gate.

This module checks whether the next Excalidraw browser/MCP proof can be
scheduled safely. It does not launch a browser, connect to CDP, invoke MCP,
navigate to Excalidraw, install dependencies, or write skill memory.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from runtime.browser_runtime.browser_controller_setup_readiness import (
    BrowserControllerSetupReadiness,
    evaluate_browser_controller_setup_readiness,
)


EXCALIDRAW_MCP_LIVE_READINESS_VERSION = "browser.excalidraw_mcp_live_readiness.v1"
EXCALIDRAW_MCP_LIVE_READINESS_RECORD_TYPE = "excalidraw_local_browser_mcp_live_readiness"
EXCALIDRAW_MCP_LIVE_READINESS_READY = "excalidraw_local_browser_mcp_live_readiness_ready_no_execution"
EXCALIDRAW_MCP_LIVE_READINESS_BLOCKED_MISSING_TARGET = (
    "blocked_excalidraw_live_readiness_missing_local_target"
)
EXCALIDRAW_MCP_LIVE_READINESS_BLOCKED_NONLOCAL_TARGET = (
    "blocked_excalidraw_live_readiness_nonlocal_target"
)
EXCALIDRAW_MCP_LIVE_READINESS_BLOCKED_PREP = "blocked_excalidraw_live_readiness_prep_missing_or_unsafe"
EXCALIDRAW_MCP_LIVE_READINESS_BLOCKED_BROWSER = "blocked_excalidraw_live_readiness_browser_controller_unavailable"

EXCALIDRAW_MCP_PROOF_PREP_ARTIFACT = Path(
    "07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_proof_prep_20260503_ready.json"
)
EXCALIDRAW_MCP_LIVE_READINESS_ARTIFACT_MISSING_TARGET = Path(
    "07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_live_readiness_20260503_blocked_missing_local_target.json"
)
EXCALIDRAW_MCP_LIVE_READINESS_ARTIFACT_READY = Path(
    "07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_live_readiness_20260503_ready.json"
)
EXCALIDRAW_MCP_LIVE_READINESS_ARTIFACT_NONLOCAL = Path(
    "07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_live_readiness_20260503_blocked_nonlocal_target.json"
)

LOCAL_TARGET_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _browser_runs_path(vault: Path, relative_path: Path) -> Path:
    base = (vault / "07_LOGS/Browser-Runs").resolve()
    path = (vault / relative_path).resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"Excalidraw readiness artifact escapes Browser-Runs: {path}") from exc
    return path


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _prep_evidence_ok(vault: Path) -> bool:
    payload = _read_json(vault / EXCALIDRAW_MCP_PROOF_PREP_ARTIFACT)
    if not isinstance(payload, dict):
        return False
    forbidden_false = (
        "live_proof_allowed_in_this_pass",
        "browser_launch_attempted",
        "cdp_connection_attempted",
        "mcp_server_invoked",
        "mcp_tool_call_attempted",
        "network_navigation_attempted",
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
    return (
        payload.get("record_type") == "excalidraw_local_browser_mcp_proof_prep"
        and payload.get("schema_version") == "browser.excalidraw_mcp_proof_prep.v1"
        and payload.get("status") == "excalidraw_local_browser_mcp_proof_prep_ready_no_execution"
        and payload.get("prep_artifact_written") is True
        and all(payload.get(key) is False for key in forbidden_false)
    )


def _target_host(target_url: str) -> str:
    parsed = urlparse(target_url)
    return (parsed.hostname or "").lower()


def _is_local_target(target_url: str) -> bool:
    parsed = urlparse(target_url)
    return (
        parsed.scheme in {"http", "https"}
        and parsed.hostname is not None
        and parsed.hostname.lower() in LOCAL_TARGET_HOSTS
    )


@dataclass(frozen=True)
class ExcalidrawMCPLiveReadiness:
    record_type: str
    schema_version: str
    generated_at: str
    status: str
    run_slug: str
    readiness_artifact_path: str
    readiness_artifact_written: bool
    prep_artifact_path: str
    prep_evidence_ready: bool
    browser_controller_ready: bool
    selected_browser_executable: str
    local_target_url: str
    local_target_host: str
    allowed_target_hosts: tuple[str, ...]
    blockers: tuple[str, ...]
    planned_future_sequence: list[dict[str, Any]] = field(default_factory=list)
    expected_future_artifacts: dict[str, str] = field(default_factory=dict)
    operator_handoff: dict[str, str] = field(default_factory=dict)
    browser_launch_attempted: bool = False
    cdp_connection_attempted: bool = False
    mcp_server_invoked: bool = False
    mcp_tool_call_attempted: bool = False
    network_navigation_attempted: bool = False
    dependency_install_attempted: bool = False
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
    next_recommended_pass: str = "excalidraw-local-target-setup-instructions"

    def validate(self) -> None:
        if self.record_type != EXCALIDRAW_MCP_LIVE_READINESS_RECORD_TYPE:
            raise ValueError("invalid Excalidraw live-readiness record type")
        if self.schema_version != EXCALIDRAW_MCP_LIVE_READINESS_VERSION:
            raise ValueError("invalid Excalidraw live-readiness schema version")
        if self.status not in {
            EXCALIDRAW_MCP_LIVE_READINESS_READY,
            EXCALIDRAW_MCP_LIVE_READINESS_BLOCKED_MISSING_TARGET,
            EXCALIDRAW_MCP_LIVE_READINESS_BLOCKED_NONLOCAL_TARGET,
            EXCALIDRAW_MCP_LIVE_READINESS_BLOCKED_PREP,
            EXCALIDRAW_MCP_LIVE_READINESS_BLOCKED_BROWSER,
        }:
            raise ValueError("invalid Excalidraw live-readiness status")
        forbidden_flags = (
            self.browser_launch_attempted,
            self.cdp_connection_attempted,
            self.mcp_server_invoked,
            self.mcp_tool_call_attempted,
            self.network_navigation_attempted,
            self.dependency_install_attempted,
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
            raise ValueError("Excalidraw live-readiness attempted a forbidden effect")
        if self.status == EXCALIDRAW_MCP_LIVE_READINESS_READY and self.blockers:
            raise ValueError("ready status cannot include blockers")
        if self.status != EXCALIDRAW_MCP_LIVE_READINESS_READY and not self.blockers:
            raise ValueError("blocked readiness status requires blockers")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["allowed_target_hosts"] = list(self.allowed_target_hosts)
        payload["blockers"] = list(self.blockers)
        return payload


def build_excalidraw_mcp_live_readiness(
    vault_root: str | Path,
    *,
    local_target_url: str = "",
    generated_at: str | None = None,
    write_readiness: bool = False,
    controller_readiness: BrowserControllerSetupReadiness | None = None,
) -> ExcalidrawMCPLiveReadiness:
    """Build and optionally persist a no-execution live-readiness packet."""
    timestamp = generated_at or _now_utc()
    vault = _vault_path(vault_root)
    target = local_target_url.strip()
    prep_ready = _prep_evidence_ok(vault)
    controller = controller_readiness or evaluate_browser_controller_setup_readiness()
    controller_ready = controller.status == "browser_controller_setup_ready_no_launch"
    target_host = _target_host(target) if target else ""
    local_target_ok = _is_local_target(target) if target else False

    blockers: list[str] = []
    status = EXCALIDRAW_MCP_LIVE_READINESS_READY
    artifact_relative = EXCALIDRAW_MCP_LIVE_READINESS_ARTIFACT_READY

    if not prep_ready:
        blockers.append("excalidraw_mcp_proof_prep_missing_or_unsafe")
        status = EXCALIDRAW_MCP_LIVE_READINESS_BLOCKED_PREP
        artifact_relative = EXCALIDRAW_MCP_LIVE_READINESS_ARTIFACT_MISSING_TARGET
    elif not controller_ready:
        blockers.append("browser_controller_setup_not_ready")
        status = EXCALIDRAW_MCP_LIVE_READINESS_BLOCKED_BROWSER
        artifact_relative = EXCALIDRAW_MCP_LIVE_READINESS_ARTIFACT_MISSING_TARGET
    elif not target:
        blockers.append("local_excalidraw_target_url_not_provided")
        status = EXCALIDRAW_MCP_LIVE_READINESS_BLOCKED_MISSING_TARGET
        artifact_relative = EXCALIDRAW_MCP_LIVE_READINESS_ARTIFACT_MISSING_TARGET
    elif not local_target_ok:
        blockers.append("local_excalidraw_target_url_must_be_loopback")
        status = EXCALIDRAW_MCP_LIVE_READINESS_BLOCKED_NONLOCAL_TARGET
        artifact_relative = EXCALIDRAW_MCP_LIVE_READINESS_ARTIFACT_NONLOCAL

    run_slug = "excalidraw-local-browser-mcp-live-readiness-20260503"
    artifact = _browser_runs_path(vault, artifact_relative)
    next_pass = (
        "excalidraw-local-browser-mcp-proof-execution-approval"
        if status == EXCALIDRAW_MCP_LIVE_READINESS_READY
        else "excalidraw-local-target-setup-instructions"
    )
    readiness = ExcalidrawMCPLiveReadiness(
        record_type=EXCALIDRAW_MCP_LIVE_READINESS_RECORD_TYPE,
        schema_version=EXCALIDRAW_MCP_LIVE_READINESS_VERSION,
        generated_at=timestamp,
        status=status,
        run_slug=run_slug,
        readiness_artifact_path=artifact.as_posix(),
        readiness_artifact_written=write_readiness,
        prep_artifact_path=(vault / EXCALIDRAW_MCP_PROOF_PREP_ARTIFACT).resolve().as_posix(),
        prep_evidence_ready=prep_ready,
        browser_controller_ready=controller_ready,
        selected_browser_executable=controller.selected_executable,
        local_target_url=target,
        local_target_host=target_host,
        allowed_target_hosts=tuple(sorted(LOCAL_TARGET_HOSTS)),
        blockers=tuple(blockers),
        planned_future_sequence=[
            {"step": 1, "action": "confirm local loopback target", "effect": "no public network target"},
            {"step": 2, "action": "request explicit live proof approval", "effect": "no execution in readiness pass"},
            {"step": 3, "action": "launch isolated throwaway browser", "effect": "future pass only"},
            {"step": 4, "action": "optionally invoke local MCP/canvas helper", "effect": "future pass only"},
            {"step": 5, "action": "write draft-only memory", "effect": "future pass only after evidence"},
        ],
        expected_future_artifacts={
            "browser_run_log": "07_LOGS/Browser-Runs/excalidraw-local-browser-mcp-proof-20260503_success.json",
            "screenshot": "07_LOGS/Browser-Runs/excalidraw-local-browser-mcp-proof-20260503_screenshot.png",
            "agent_activity": "07_LOGS/Agent-Activity/2026-05-03-browser-excalidraw-local-browser-mcp-proof.md",
            "draft_skill": "06_AGENTS/Browser-Skills/_drafts/draft-excalidraw-local-browser-mcp-proof-20260503.md",
            "untrusted_candidate": "03_INPUTS/Browser-Skill-Candidates/excalidraw-com/20260503__candidate-excalidraw-local-browser-mcp-proof-20260503.md",
        },
        operator_handoff={
            "required_target": "Start or provide a local loopback Excalidraw/canvas target, then rerun with --local-target-url.",
            "example_command": (
                "python -m runtime.browser_runtime.excalidraw_mcp_live_readiness "
                "--vault-root . --local-target-url http://127.0.0.1:<port>/ --json"
            ),
            "profile_policy": "throwaway_only; no real profile, saved credentials, cookies, sync, or browser history.",
            "mcp_policy": "local loopback only; no public tunnel; no invocation in this readiness pass.",
            "skill_policy": "draft/candidate only in future proof; no trusted activation.",
        },
        next_recommended_pass=next_pass,
    )
    readiness.validate()
    if write_readiness:
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(json.dumps(readiness.to_dict(), indent=2) + "\n", encoding="utf-8")
    return readiness


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check Excalidraw browser/MCP live readiness without execution.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--local-target-url", default="", help="Local loopback Excalidraw/canvas target URL.")
    parser.add_argument("--write-readiness", action="store_true", help="Write readiness evidence under Browser-Runs.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    packet = build_excalidraw_mcp_live_readiness(
        args.vault_root,
        local_target_url=args.local_target_url,
        write_readiness=args.write_readiness,
    )
    payload = packet.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {payload['status']}")
        for blocker in payload["blockers"]:
            print(f"blocker: {blocker}")
        print(f"readiness_artifact_written: {payload['readiness_artifact_written']}")
        print(f"next_recommended_pass: {payload['next_recommended_pass']}")
    return 0 if packet.status == EXCALIDRAW_MCP_LIVE_READINESS_READY else 1


if __name__ == "__main__":
    raise SystemExit(main())
