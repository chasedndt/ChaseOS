"""No-execution Excalidraw live-readiness bridge from target response.

This module consumes the untrusted target response artifact and, only when it
contains an accepted loopback URL, builds the existing Excalidraw live-readiness
packet from that URL. It does not probe URLs, launch browsers, connect to CDP,
invoke MCP, or write trusted skill memory.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.browser_runtime.browser_controller_setup_readiness import BrowserControllerSetupReadiness
from runtime.browser_runtime.excalidraw_mcp_live_readiness import (
    EXCALIDRAW_MCP_LIVE_READINESS_READY,
    build_excalidraw_mcp_live_readiness,
)
from runtime.browser_runtime.excalidraw_target_response_resolver import (
    resolve_excalidraw_target_response,
)


EXCALIDRAW_READINESS_FROM_RESPONSE_VERSION = "browser.excalidraw_readiness_from_response.v1"
EXCALIDRAW_READINESS_FROM_RESPONSE_RECORD_TYPE = "excalidraw_readiness_from_target_response"
EXCALIDRAW_READINESS_FROM_RESPONSE_READY = (
    "excalidraw_readiness_from_target_response_ready_no_execution"
)
EXCALIDRAW_READINESS_FROM_RESPONSE_BLOCKED_PENDING = (
    "blocked_excalidraw_readiness_from_response_pending_external_runtime"
)
EXCALIDRAW_READINESS_FROM_RESPONSE_BLOCKED_MISSING = (
    "blocked_excalidraw_readiness_from_response_missing_artifact"
)
EXCALIDRAW_READINESS_FROM_RESPONSE_BLOCKED_UNACCEPTED = (
    "blocked_excalidraw_readiness_from_response_unaccepted_target"
)
EXCALIDRAW_READINESS_FROM_RESPONSE_BLOCKED_READINESS = (
    "blocked_excalidraw_readiness_from_response_live_readiness_not_ready"
)

EXCALIDRAW_READINESS_FROM_RESPONSE_READY_ARTIFACT = Path(
    "07_LOGS/Browser-Runs/excalidraw_readiness_from_target_response_20260503_ready.json"
)
EXCALIDRAW_READINESS_FROM_RESPONSE_BLOCKED_ARTIFACT = Path(
    "07_LOGS/Browser-Runs/excalidraw_readiness_from_target_response_20260503_blocked_pending.json"
)

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


def _browser_runs_path(vault: Path, relative_path: Path) -> Path:
    base = (vault / "07_LOGS/Browser-Runs").resolve()
    path = (vault / relative_path).resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"Excalidraw response-readiness artifact escapes Browser-Runs: {path}") from exc
    return path


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _find_response_payload(vault: Path, response_path: str | Path = "") -> tuple[str, dict[str, Any] | None]:
    resolution = resolve_excalidraw_target_response(vault, response_path=response_path)
    if resolution.selected_response_path:
        path = Path(resolution.selected_response_path)
        return path.as_posix(), _read_json(path)
    return "", None


@dataclass(frozen=True)
class ExcalidrawReadinessFromResponse:
    record_type: str
    schema_version: str
    generated_at: str
    status: str
    bridge_artifact_path: str
    bridge_artifact_written: bool
    source_response_path: str
    source_response_status: str
    target_url: str
    target_host: str
    live_readiness_status: str
    live_readiness_artifact_path: str
    live_readiness_would_write: bool
    blockers: tuple[str, ...] = ()
    source_response_payload_summary: dict[str, Any] = field(default_factory=dict)
    next_recommended_pass: str = "external-runtime-provide-excalidraw-target-url"
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

    def validate(self) -> None:
        if self.record_type != EXCALIDRAW_READINESS_FROM_RESPONSE_RECORD_TYPE:
            raise ValueError("invalid Excalidraw response-readiness record type")
        if self.schema_version != EXCALIDRAW_READINESS_FROM_RESPONSE_VERSION:
            raise ValueError("invalid Excalidraw response-readiness schema version")
        if self.status not in {
            EXCALIDRAW_READINESS_FROM_RESPONSE_READY,
            EXCALIDRAW_READINESS_FROM_RESPONSE_BLOCKED_PENDING,
            EXCALIDRAW_READINESS_FROM_RESPONSE_BLOCKED_MISSING,
            EXCALIDRAW_READINESS_FROM_RESPONSE_BLOCKED_UNACCEPTED,
            EXCALIDRAW_READINESS_FROM_RESPONSE_BLOCKED_READINESS,
        }:
            raise ValueError("invalid Excalidraw response-readiness status")
        if self.status == EXCALIDRAW_READINESS_FROM_RESPONSE_READY and self.blockers:
            raise ValueError("ready response-readiness cannot include blockers")
        if self.status != EXCALIDRAW_READINESS_FROM_RESPONSE_READY and not self.blockers:
            raise ValueError("blocked response-readiness requires blockers")
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
            raise ValueError("Excalidraw response-readiness attempted a forbidden effect")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["blockers"] = list(self.blockers)
        payload["blocked_effects"] = list(self.blocked_effects)
        return payload


def build_excalidraw_readiness_from_response(
    vault_root: str | Path,
    *,
    response_path: str | Path = "",
    generated_at: str | None = None,
    write_bridge: bool = False,
    write_live_readiness: bool = False,
    controller_readiness: BrowserControllerSetupReadiness | None = None,
) -> ExcalidrawReadinessFromResponse:
    """Build and optionally persist a no-execution response-to-readiness bridge."""
    timestamp = generated_at or _now_utc()
    vault = _vault_path(vault_root)
    source_path, response_payload = _find_response_payload(vault, response_path)
    source_status = ""
    target_url = ""
    target_host = ""
    live_status = ""
    live_artifact = ""
    blockers: list[str] = []
    status = EXCALIDRAW_READINESS_FROM_RESPONSE_BLOCKED_MISSING

    if not isinstance(response_payload, dict):
        blockers.append("excalidraw_target_response_artifact_missing_or_invalid")
    else:
        source_status = str(response_payload.get("status") or "")
        target_url = str(response_payload.get("target_url") or "")
        target_host = str(response_payload.get("target_host") or "")
        if source_status == "excalidraw_local_target_response_pending_external_runtime":
            status = EXCALIDRAW_READINESS_FROM_RESPONSE_BLOCKED_PENDING
            blockers.append("excalidraw_target_response_pending_external_runtime")
        elif source_status != "excalidraw_local_target_response_accepted_no_probe":
            status = EXCALIDRAW_READINESS_FROM_RESPONSE_BLOCKED_UNACCEPTED
            blockers.append("excalidraw_target_response_not_accepted")
        else:
            readiness = build_excalidraw_mcp_live_readiness(
                vault,
                local_target_url=target_url,
                write_readiness=write_live_readiness,
                controller_readiness=controller_readiness,
            )
            live_payload = readiness.to_dict()
            live_status = str(live_payload.get("status") or "")
            live_artifact = str(live_payload.get("readiness_artifact_path") or "")
            if live_status == EXCALIDRAW_MCP_LIVE_READINESS_READY:
                status = EXCALIDRAW_READINESS_FROM_RESPONSE_READY
            else:
                status = EXCALIDRAW_READINESS_FROM_RESPONSE_BLOCKED_READINESS
                blockers.append(f"live_readiness_not_ready:{live_status}")

    artifact = _browser_runs_path(
        vault,
        EXCALIDRAW_READINESS_FROM_RESPONSE_READY_ARTIFACT
        if status == EXCALIDRAW_READINESS_FROM_RESPONSE_READY
        else EXCALIDRAW_READINESS_FROM_RESPONSE_BLOCKED_ARTIFACT,
    )
    next_pass = (
        "excalidraw-local-browser-mcp-proof-execution-approval"
        if status == EXCALIDRAW_READINESS_FROM_RESPONSE_READY
        else (
            "excalidraw-local-browser-mcp-live-readiness-with-target"
            if target_url
            else "external-runtime-provide-excalidraw-target-url"
        )
    )
    packet = ExcalidrawReadinessFromResponse(
        record_type=EXCALIDRAW_READINESS_FROM_RESPONSE_RECORD_TYPE,
        schema_version=EXCALIDRAW_READINESS_FROM_RESPONSE_VERSION,
        generated_at=timestamp,
        status=status,
        bridge_artifact_path=artifact.as_posix(),
        bridge_artifact_written=write_bridge,
        source_response_path=source_path,
        source_response_status=source_status,
        target_url=target_url,
        target_host=target_host,
        live_readiness_status=live_status,
        live_readiness_artifact_path=live_artifact,
        live_readiness_would_write=write_live_readiness,
        blockers=tuple(blockers),
        source_response_payload_summary={
            "record_type": response_payload.get("record_type") if isinstance(response_payload, dict) else "",
            "schema_version": response_payload.get("schema_version") if isinstance(response_payload, dict) else "",
            "status": source_status,
            "target_url_present": bool(target_url),
        },
        next_recommended_pass=next_pass,
    )
    packet.validate()
    if write_bridge:
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(json.dumps(packet.to_dict(), indent=2) + "\n", encoding="utf-8")
    return packet


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Excalidraw readiness from target response without execution.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--response-path", default="", help="Optional target response artifact path.")
    parser.add_argument("--write-bridge", action="store_true", help="Write bridge evidence under Browser-Runs.")
    parser.add_argument(
        "--write-live-readiness",
        action="store_true",
        help="If response is accepted, also write the no-execution live-readiness artifact.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    packet = build_excalidraw_readiness_from_response(
        args.vault_root,
        response_path=args.response_path,
        write_bridge=args.write_bridge,
        write_live_readiness=args.write_live_readiness,
    )
    payload = packet.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {payload['status']}")
        for blocker in payload["blockers"]:
            print(f"blocker: {blocker}")
        print(f"bridge_artifact_written: {payload['bridge_artifact_written']}")
        print(f"next_recommended_pass: {payload['next_recommended_pass']}")
    return 0 if payload["status"] == EXCALIDRAW_READINESS_FROM_RESPONSE_READY else 1


if __name__ == "__main__":
    raise SystemExit(main())
