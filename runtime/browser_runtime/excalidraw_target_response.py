"""No-execution Excalidraw local target response intake.

This module consumes the external runtime/operator response to the Excalidraw
target contract. It validates URL shape and loopback scope only. It does not
start servers, probe URLs, launch browsers, connect to CDP, invoke MCP, or
write trusted skill memory.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.browser_runtime.excalidraw_target_contract import (
    ALLOWED_TARGET_HOSTS,
    PROOF_GOAL,
)


EXCALIDRAW_TARGET_RESPONSE_VERSION = "browser.excalidraw_target_response.v1"
EXCALIDRAW_TARGET_RESPONSE_RECORD_TYPE = "excalidraw_local_target_response"
EXCALIDRAW_TARGET_RESPONSE_PENDING = "excalidraw_local_target_response_pending_external_runtime"
EXCALIDRAW_TARGET_RESPONSE_ACCEPTED = "excalidraw_local_target_response_accepted_no_probe"
EXCALIDRAW_TARGET_RESPONSE_BLOCKED_NONLOCAL = "blocked_excalidraw_target_response_nonlocal_url"
EXCALIDRAW_TARGET_RESPONSE_BLOCKED_BAD_SHAPE = "blocked_excalidraw_target_response_bad_url_shape"
EXCALIDRAW_TARGET_RESPONSE_BLOCKED_BAD_FILE = "blocked_excalidraw_target_response_bad_response_file"

EXCALIDRAW_TARGET_RESPONSE_PENDING_ARTIFACT = Path(
    "03_INPUTS/Browser-Target-Responses/_pending/excalidraw_local_target_response_20260503_pending.json"
)
EXCALIDRAW_TARGET_RESPONSE_ACCEPTED_ARTIFACT = Path(
    "03_INPUTS/Browser-Target-Responses/_pending/excalidraw_local_target_response_20260503_accepted.json"
)
EXCALIDRAW_TARGET_RESPONSE_BLOCKED_ARTIFACT = Path(
    "03_INPUTS/Browser-Target-Responses/_pending/excalidraw_local_target_response_20260503_blocked.json"
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


def _artifact_for_status(status: str) -> Path:
    if status == EXCALIDRAW_TARGET_RESPONSE_ACCEPTED:
        return EXCALIDRAW_TARGET_RESPONSE_ACCEPTED_ARTIFACT
    if status == EXCALIDRAW_TARGET_RESPONSE_PENDING:
        return EXCALIDRAW_TARGET_RESPONSE_PENDING_ARTIFACT
    return EXCALIDRAW_TARGET_RESPONSE_BLOCKED_ARTIFACT


def _input_artifact_path(vault: Path, relative_path: Path) -> Path:
    base = (vault / "03_INPUTS/Browser-Target-Responses/_pending").resolve()
    path = (vault / relative_path).resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"Excalidraw target response artifact escapes pending inputs: {path}") from exc
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
    return bool(target_url) and target_url.startswith(("http://", "https://")) and "://" in target_url


def _is_loopback(target_url: str) -> bool:
    return _target_host(target_url) in ALLOWED_TARGET_HOSTS


def _read_response_file(path: str | Path) -> tuple[str, dict[str, Any], list[str]]:
    response_path = Path(path)
    try:
        payload = json.loads(response_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return "", {}, [f"response_file_unreadable_or_invalid_json:{type(exc).__name__}"]
    if not isinstance(payload, dict):
        return "", {}, ["response_file_must_be_json_object"]
    target_url = str(payload.get("target_url") or "").strip()
    if not target_url:
        target = payload.get("target")
        if isinstance(target, dict):
            target_url = str(target.get("url") or "").strip()
    if not target_url:
        return "", payload, ["response_file_missing_target_url"]
    return target_url, payload, []


@dataclass(frozen=True)
class ExcalidrawTargetResponse:
    record_type: str
    schema_version: str
    generated_at: str
    status: str
    response_artifact_path: str
    response_artifact_written: bool
    target_url: str
    target_host: str
    allowed_target_hosts: tuple[str, ...]
    proof_goal: str
    source_response_file: str = ""
    source_response_payload: dict[str, Any] = field(default_factory=dict)
    blocked_reasons: tuple[str, ...] = ()
    readiness_rerun_command: str = ""
    external_runtime_handoff: dict[str, Any] = field(default_factory=dict)
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
        if self.record_type != EXCALIDRAW_TARGET_RESPONSE_RECORD_TYPE:
            raise ValueError("invalid Excalidraw target response record type")
        if self.schema_version != EXCALIDRAW_TARGET_RESPONSE_VERSION:
            raise ValueError("invalid Excalidraw target response schema version")
        if self.status not in {
            EXCALIDRAW_TARGET_RESPONSE_PENDING,
            EXCALIDRAW_TARGET_RESPONSE_ACCEPTED,
            EXCALIDRAW_TARGET_RESPONSE_BLOCKED_NONLOCAL,
            EXCALIDRAW_TARGET_RESPONSE_BLOCKED_BAD_SHAPE,
            EXCALIDRAW_TARGET_RESPONSE_BLOCKED_BAD_FILE,
        }:
            raise ValueError("invalid Excalidraw target response status")
        if self.status == EXCALIDRAW_TARGET_RESPONSE_ACCEPTED and self.blocked_reasons:
            raise ValueError("accepted target response cannot include blockers")
        if self.status.startswith("blocked_") and not self.blocked_reasons:
            raise ValueError("blocked target response requires blockers")
        if self.status == EXCALIDRAW_TARGET_RESPONSE_PENDING and self.target_url:
            raise ValueError("pending target response cannot include target URL")
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
            raise ValueError("Excalidraw target response attempted a forbidden effect")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["allowed_target_hosts"] = list(self.allowed_target_hosts)
        payload["blocked_reasons"] = list(self.blocked_reasons)
        payload["blocked_effects"] = list(self.blocked_effects)
        return payload


def build_excalidraw_target_response(
    vault_root: str | Path,
    *,
    target_url: str = "",
    response_file: str | Path = "",
    generated_at: str | None = None,
    write_response: bool = False,
) -> ExcalidrawTargetResponse:
    """Build and optionally persist a no-execution target response intake packet."""
    timestamp = generated_at or _now_utc()
    source_payload: dict[str, Any] = {}
    blockers: list[str] = []
    target = target_url.strip()
    source_file = str(response_file or "")
    if response_file:
        file_target, source_payload, file_blockers = _read_response_file(response_file)
        target = target or file_target
        blockers.extend(file_blockers)

    if blockers:
        status = EXCALIDRAW_TARGET_RESPONSE_BLOCKED_BAD_FILE
    elif not target:
        status = EXCALIDRAW_TARGET_RESPONSE_PENDING
    elif not _url_shape_ok(target):
        status = EXCALIDRAW_TARGET_RESPONSE_BLOCKED_BAD_SHAPE
        blockers.append("target_url_must_be_http_or_https")
    elif not _is_loopback(target):
        status = EXCALIDRAW_TARGET_RESPONSE_BLOCKED_NONLOCAL
        blockers.append("target_url_must_use_loopback_host")
    else:
        status = EXCALIDRAW_TARGET_RESPONSE_ACCEPTED

    vault = _vault_path(vault_root)
    artifact = _input_artifact_path(vault, _artifact_for_status(status))
    next_pass = (
        "excalidraw-local-browser-mcp-live-readiness-with-target"
        if status == EXCALIDRAW_TARGET_RESPONSE_ACCEPTED
        else "external-runtime-provide-excalidraw-target-url"
    )
    readiness_command = (
        "python -m runtime.browser_runtime.excalidraw_mcp_live_readiness "
        f"--vault-root . --local-target-url {target or '<loopback-url>'} --write-readiness --json"
    )
    packet = ExcalidrawTargetResponse(
        record_type=EXCALIDRAW_TARGET_RESPONSE_RECORD_TYPE,
        schema_version=EXCALIDRAW_TARGET_RESPONSE_VERSION,
        generated_at=timestamp,
        status=status,
        response_artifact_path=artifact.as_posix(),
        response_artifact_written=write_response,
        target_url=target,
        target_host=_target_host(target),
        allowed_target_hosts=ALLOWED_TARGET_HOSTS,
        proof_goal=PROOF_GOAL,
        source_response_file=source_file,
        source_response_payload=source_payload,
        blocked_reasons=tuple(blockers),
        readiness_rerun_command=readiness_command,
        external_runtime_handoff={
            "accepted_response_shape": {"target_url": "http://127.0.0.1:<port>/"},
            "response_store": "03_INPUTS/Browser-Target-Responses/_pending/",
            "safe_to_run_next": status == EXCALIDRAW_TARGET_RESPONSE_ACCEPTED,
            "chaseos_does_not": [
                "probe the target in this pass",
                "launch a browser in this pass",
                "invoke MCP in this pass",
                "write or activate trusted skills",
            ],
        },
        next_recommended_pass=next_pass,
    )
    packet.validate()
    if write_response:
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(json.dumps(packet.to_dict(), indent=2) + "\n", encoding="utf-8")
    return packet


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Consume Excalidraw local target response without execution.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--target-url", default="", help="Optional local loopback target URL.")
    parser.add_argument("--response-file", default="", help="Optional JSON response file from external runtime.")
    parser.add_argument("--write-response", action="store_true", help="Write pending response evidence under 03_INPUTS.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    packet = build_excalidraw_target_response(
        args.vault_root,
        target_url=args.target_url,
        response_file=args.response_file,
        write_response=args.write_response,
    )
    payload = packet.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {payload['status']}")
        for blocker in payload["blocked_reasons"]:
            print(f"blocker: {blocker}")
        print(f"response_artifact_written: {payload['response_artifact_written']}")
        print(f"next_recommended_pass: {payload['next_recommended_pass']}")
    return 0 if not packet.status.startswith("blocked_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
