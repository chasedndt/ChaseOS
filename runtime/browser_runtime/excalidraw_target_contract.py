"""No-execution Excalidraw local target contract/request packet.

This module defines the machine-readable contract an external runtime must
satisfy before ChaseOS reruns Excalidraw live-readiness with a target URL. It
does not start servers, probe URLs, launch browsers, connect to CDP, invoke MCP,
or write skill memory.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXCALIDRAW_TARGET_CONTRACT_VERSION = "browser.excalidraw_target_contract.v1"
EXCALIDRAW_TARGET_CONTRACT_RECORD_TYPE = "excalidraw_local_target_contract"
EXCALIDRAW_TARGET_CONTRACT_REQUEST_READY = (
    "excalidraw_local_target_contract_request_ready_no_execution"
)
EXCALIDRAW_TARGET_CONTRACT_READY = "excalidraw_local_target_contract_ready_no_probe"
EXCALIDRAW_TARGET_CONTRACT_BLOCKED_NONLOCAL = "blocked_excalidraw_target_contract_nonlocal_url"
EXCALIDRAW_TARGET_CONTRACT_BLOCKED_BAD_SHAPE = "blocked_excalidraw_target_contract_bad_url_shape"

EXCALIDRAW_TARGET_CONTRACT_REQUEST_ARTIFACT = Path(
    "07_LOGS/Browser-Runs/excalidraw_local_target_contract_request_20260503_ready.json"
)
EXCALIDRAW_TARGET_CONTRACT_READY_ARTIFACT = Path(
    "07_LOGS/Browser-Runs/excalidraw_local_target_contract_20260503_ready.json"
)
EXCALIDRAW_TARGET_CONTRACT_BLOCKED_ARTIFACT = Path(
    "07_LOGS/Browser-Runs/excalidraw_local_target_contract_20260503_blocked.json"
)

ALLOWED_TARGET_HOSTS = ("127.0.0.1", "localhost", "::1")
PROOF_GOAL = 'draw one rectangle and label it "ChaseOS"'

BLOCKED_EFFECTS = (
    "dependency_install",
    "server_start",
    "network_probe",
    "browser_launch",
    "cdp_connection",
    "mcp_invocation",
    "mcp_tool_call",
    "target_navigation",
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


def _target_artifact(status: str) -> Path:
    if status == EXCALIDRAW_TARGET_CONTRACT_READY:
        return EXCALIDRAW_TARGET_CONTRACT_READY_ARTIFACT
    if status == EXCALIDRAW_TARGET_CONTRACT_REQUEST_READY:
        return EXCALIDRAW_TARGET_CONTRACT_REQUEST_ARTIFACT
    return EXCALIDRAW_TARGET_CONTRACT_BLOCKED_ARTIFACT


def _artifact_path(vault: Path, relative_path: Path) -> Path:
    base = (vault / "07_LOGS/Browser-Runs").resolve()
    path = (vault / relative_path).resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"Excalidraw target contract artifact escapes Browser-Runs: {path}") from exc
    return path


def _target_host(target_url: str) -> str:
    if target_url.startswith("http://[::1]"):
        return "::1"
    if not target_url.startswith(("http://", "https://")):
        return ""
    without_scheme = target_url.split("://", 1)[1]
    authority = without_scheme.split("/", 1)[0]
    return authority.split(":", 1)[0].lower()


def _url_shape_ok(target_url: str) -> bool:
    if not target_url:
        return True
    return target_url.startswith(("http://", "https://")) and "://" in target_url


def _is_local_target(target_url: str) -> bool:
    if not target_url:
        return False
    return _target_host(target_url) in ALLOWED_TARGET_HOSTS


@dataclass(frozen=True)
class ExcalidrawTargetContract:
    record_type: str
    schema_version: str
    generated_at: str
    status: str
    contract_artifact_path: str
    contract_artifact_written: bool
    target_url: str
    target_host: str
    allowed_target_hosts: tuple[str, ...]
    proof_goal: str
    external_runtime_request: dict[str, Any] = field(default_factory=dict)
    target_requirements: tuple[str, ...] = ()
    readiness_rerun_command: str = ""
    blocked_reasons: tuple[str, ...] = ()
    expected_future_artifacts: dict[str, str] = field(default_factory=dict)
    blocked_effects: tuple[str, ...] = BLOCKED_EFFECTS
    dependency_install_attempted: bool = False
    server_start_attempted: bool = False
    network_probe_attempted: bool = False
    browser_launch_attempted: bool = False
    cdp_connection_attempted: bool = False
    mcp_invocation_attempted: bool = False
    mcp_tool_call_attempted: bool = False
    target_navigation_attempted: bool = False
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
    next_recommended_pass: str = "external-runtime-provide-excalidraw-target-url"

    def validate(self) -> None:
        if self.record_type != EXCALIDRAW_TARGET_CONTRACT_RECORD_TYPE:
            raise ValueError("invalid Excalidraw target contract record type")
        if self.schema_version != EXCALIDRAW_TARGET_CONTRACT_VERSION:
            raise ValueError("invalid Excalidraw target contract schema version")
        if self.status not in {
            EXCALIDRAW_TARGET_CONTRACT_REQUEST_READY,
            EXCALIDRAW_TARGET_CONTRACT_READY,
            EXCALIDRAW_TARGET_CONTRACT_BLOCKED_NONLOCAL,
            EXCALIDRAW_TARGET_CONTRACT_BLOCKED_BAD_SHAPE,
        }:
            raise ValueError("invalid Excalidraw target contract status")
        if self.status == EXCALIDRAW_TARGET_CONTRACT_READY and self.blocked_reasons:
            raise ValueError("ready target contract cannot include blockers")
        if self.status.startswith("blocked_") and not self.blocked_reasons:
            raise ValueError("blocked target contract requires blockers")
        if not self.target_requirements:
            raise ValueError("target requirements are required")
        if not self.external_runtime_request:
            raise ValueError("external runtime request is required")
        forbidden_flags = (
            self.dependency_install_attempted,
            self.server_start_attempted,
            self.network_probe_attempted,
            self.browser_launch_attempted,
            self.cdp_connection_attempted,
            self.mcp_invocation_attempted,
            self.mcp_tool_call_attempted,
            self.target_navigation_attempted,
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
            raise ValueError("Excalidraw target contract attempted a forbidden effect")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["allowed_target_hosts"] = list(self.allowed_target_hosts)
        payload["target_requirements"] = list(self.target_requirements)
        payload["blocked_reasons"] = list(self.blocked_reasons)
        payload["blocked_effects"] = list(self.blocked_effects)
        return payload


def build_excalidraw_target_contract(
    vault_root: str | Path,
    *,
    target_url: str = "",
    generated_at: str | None = None,
    write_contract: bool = False,
) -> ExcalidrawTargetContract:
    """Build and optionally persist the no-execution Excalidraw target contract."""
    timestamp = generated_at or _now_utc()
    target = target_url.strip()
    host = _target_host(target)
    blockers: list[str] = []
    if target and not _url_shape_ok(target):
        status = EXCALIDRAW_TARGET_CONTRACT_BLOCKED_BAD_SHAPE
        blockers.append("target_url_must_be_http_or_https")
    elif target and not _is_local_target(target):
        status = EXCALIDRAW_TARGET_CONTRACT_BLOCKED_NONLOCAL
        blockers.append("target_url_must_use_loopback_host")
    elif target:
        status = EXCALIDRAW_TARGET_CONTRACT_READY
    else:
        status = EXCALIDRAW_TARGET_CONTRACT_REQUEST_READY

    vault = _vault_path(vault_root)
    artifact = _artifact_path(vault, _target_artifact(status))
    next_pass = (
        "excalidraw-local-browser-mcp-live-readiness-with-target"
        if status == EXCALIDRAW_TARGET_CONTRACT_READY
        else "external-runtime-provide-excalidraw-target-url"
    )
    packet = ExcalidrawTargetContract(
        record_type=EXCALIDRAW_TARGET_CONTRACT_RECORD_TYPE,
        schema_version=EXCALIDRAW_TARGET_CONTRACT_VERSION,
        generated_at=timestamp,
        status=status,
        contract_artifact_path=artifact.as_posix(),
        contract_artifact_written=write_contract,
        target_url=target,
        target_host=host,
        allowed_target_hosts=ALLOWED_TARGET_HOSTS,
        proof_goal=PROOF_GOAL,
        external_runtime_request={
            "request_type": "provide_local_excalidraw_canvas_target",
            "target_url_required": not bool(target),
            "accepted_url_examples": [
                "http://127.0.0.1:<port>/",
                "http://localhost:<port>/",
            ],
            "chaseos_receives": "loopback URL only",
            "chaseos_does_not": [
                "install dependencies",
                "start the target",
                "probe the target",
                "launch browser",
                "invoke MCP",
            ],
        },
        target_requirements=(
            "Bind only to 127.0.0.1, localhost, or ::1.",
            "Require no account login, collaboration link, saved cookies, or browser profile.",
            "Expose a visible canvas or Excalidraw-compatible drawing surface.",
            "Allow a harmless rectangle plus label proof.",
            "Do not expose a public tunnel or remote browser.",
            "Return only a local target URL to ChaseOS before live-readiness rerun.",
        ),
        readiness_rerun_command=(
            "python -m runtime.browser_runtime.excalidraw_mcp_live_readiness "
            "--vault-root . --local-target-url <loopback-url> --write-readiness --json"
        ),
        blocked_reasons=tuple(blockers),
        expected_future_artifacts={
            "target_contract_ready": "07_LOGS/Browser-Runs/excalidraw_local_target_contract_20260503_ready.json",
            "readiness_ready": "07_LOGS/Browser-Runs/excalidraw_local_browser_mcp_live_readiness_20260503_ready.json",
            "future_proof_run": "07_LOGS/Browser-Runs/excalidraw-local-browser-mcp-proof-20260503_success.json",
            "future_draft_skill": "06_AGENTS/Browser-Skills/_drafts/draft-excalidraw-local-browser-mcp-proof-20260503.md",
        },
        next_recommended_pass=next_pass,
    )
    packet.validate()
    if write_contract:
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(json.dumps(packet.to_dict(), indent=2) + "\n", encoding="utf-8")
    return packet


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Excalidraw local target contract without execution.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--target-url", default="", help="Optional local loopback target URL.")
    parser.add_argument("--write-contract", action="store_true", help="Write contract evidence under Browser-Runs.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    packet = build_excalidraw_target_contract(
        args.vault_root,
        target_url=args.target_url,
        write_contract=args.write_contract,
    )
    payload = packet.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {payload['status']}")
        for blocker in payload["blocked_reasons"]:
            print(f"blocker: {blocker}")
        print(f"contract_artifact_written: {payload['contract_artifact_written']}")
        print(f"next_recommended_pass: {payload['next_recommended_pass']}")
    return 0 if not packet.status.startswith("blocked_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
