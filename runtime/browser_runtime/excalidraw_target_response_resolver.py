"""No-execution resolver for the latest Excalidraw target response.

This module reads only the untrusted Excalidraw target-response intake folder
and selects the latest usable response artifact. It does not probe URLs, start
servers, launch browsers, connect to CDP, invoke MCP, or write artifacts.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.browser_runtime.excalidraw_target_contract import ALLOWED_TARGET_HOSTS
from runtime.browser_runtime.excalidraw_target_response import (
    EXCALIDRAW_TARGET_RESPONSE_ACCEPTED,
    EXCALIDRAW_TARGET_RESPONSE_PENDING,
    EXCALIDRAW_TARGET_RESPONSE_RECORD_TYPE,
    EXCALIDRAW_TARGET_RESPONSE_VERSION,
)


EXCALIDRAW_TARGET_RESPONSE_RESOLVER_VERSION = "browser.excalidraw_target_response_resolution.v1"
EXCALIDRAW_TARGET_RESPONSE_RESOLVER_RECORD_TYPE = "excalidraw_target_response_resolution"
EXCALIDRAW_TARGET_RESPONSE_RESOLVER_ACCEPTED = (
    "excalidraw_target_response_resolution_accepted_no_probe"
)
EXCALIDRAW_TARGET_RESPONSE_RESOLVER_PENDING = (
    "excalidraw_target_response_resolution_pending_external_runtime"
)
EXCALIDRAW_TARGET_RESPONSE_RESOLVER_MISSING = (
    "blocked_excalidraw_target_response_resolution_missing"
)
EXCALIDRAW_TARGET_RESPONSE_RESOLVER_INVALID = (
    "blocked_excalidraw_target_response_resolution_invalid"
)

EXCALIDRAW_TARGET_RESPONSE_PENDING_DIR = Path("03_INPUTS/Browser-Target-Responses/_pending")
EXCALIDRAW_TARGET_RESPONSE_PATTERN = "excalidraw_local_target_response_*.json"

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


def _pending_root(vault: Path) -> Path:
    return (vault / EXCALIDRAW_TARGET_RESPONSE_PENDING_DIR).resolve()


def _path_under_pending(vault: Path, candidate: str | Path) -> Path:
    path = Path(candidate)
    if not path.is_absolute():
        path = vault / path
    resolved = path.resolve()
    try:
        resolved.relative_to(_pending_root(vault))
    except ValueError as exc:
        raise ValueError(f"Excalidraw target response path escapes pending inputs: {resolved}") from exc
    return resolved


def _target_host(target_url: str) -> str:
    if target_url.startswith("http://[::1]"):
        return "::1"
    if not target_url.startswith(("http://", "https://")):
        return ""
    authority = target_url.split("://", 1)[1].split("/", 1)[0]
    return authority.split(":", 1)[0].lower()


def _is_loopback(target_url: str) -> bool:
    return _target_host(target_url) in ALLOWED_TARGET_HOSTS


def _read_json(path: Path) -> tuple[dict[str, Any] | None, str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"unreadable_or_invalid_json:{type(exc).__name__}"
    if not isinstance(payload, dict):
        return None, "payload_must_be_json_object"
    return payload, ""


def _candidate_summary(path: Path, payload: dict[str, Any] | None, blocker: str = "") -> dict[str, Any]:
    status = str(payload.get("status") or "") if isinstance(payload, dict) else ""
    target_url = str(payload.get("target_url") or "") if isinstance(payload, dict) else ""
    generated_at = str(payload.get("generated_at") or "") if isinstance(payload, dict) else ""
    return {
        "path": path.as_posix(),
        "name": path.name,
        "status": status,
        "generated_at": generated_at,
        "target_url_present": bool(target_url),
        "target_host": _target_host(target_url),
        "candidate_blocker": blocker,
    }


def _response_usable(payload: dict[str, Any]) -> tuple[bool, str]:
    if payload.get("record_type") != EXCALIDRAW_TARGET_RESPONSE_RECORD_TYPE:
        return False, "record_type_not_excalidraw_target_response"
    if payload.get("schema_version") != EXCALIDRAW_TARGET_RESPONSE_VERSION:
        return False, "schema_version_not_excalidraw_target_response_v1"
    status = str(payload.get("status") or "")
    if status == EXCALIDRAW_TARGET_RESPONSE_ACCEPTED:
        target_url = str(payload.get("target_url") or "")
        if not target_url:
            return False, "accepted_response_missing_target_url"
        if not _is_loopback(target_url):
            return False, "accepted_response_target_not_loopback"
        return True, ""
    if status == EXCALIDRAW_TARGET_RESPONSE_PENDING:
        if payload.get("target_url"):
            return False, "pending_response_must_not_include_target_url"
        return True, ""
    return False, f"response_status_not_selectable:{status}"


def _sort_key(candidate: dict[str, Any]) -> tuple[str, str]:
    return (
        str(candidate.get("generated_at") or ""),
        str(candidate.get("name") or ""),
    )


@dataclass(frozen=True)
class ExcalidrawTargetResponseResolution:
    record_type: str
    schema_version: str
    generated_at: str
    status: str
    selected_response_path: str
    selected_response_status: str
    target_url: str
    target_host: str
    candidates_inspected: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    blockers: tuple[str, ...] = ()
    next_recommended_pass: str = "external-runtime-provide-excalidraw-target-url"
    read_only: bool = True
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
        if self.record_type != EXCALIDRAW_TARGET_RESPONSE_RESOLVER_RECORD_TYPE:
            raise ValueError("invalid Excalidraw target-response resolution record type")
        if self.schema_version != EXCALIDRAW_TARGET_RESPONSE_RESOLVER_VERSION:
            raise ValueError("invalid Excalidraw target-response resolution schema version")
        if self.status not in {
            EXCALIDRAW_TARGET_RESPONSE_RESOLVER_ACCEPTED,
            EXCALIDRAW_TARGET_RESPONSE_RESOLVER_PENDING,
            EXCALIDRAW_TARGET_RESPONSE_RESOLVER_MISSING,
            EXCALIDRAW_TARGET_RESPONSE_RESOLVER_INVALID,
        }:
            raise ValueError("invalid Excalidraw target-response resolution status")
        if self.status in {
            EXCALIDRAW_TARGET_RESPONSE_RESOLVER_ACCEPTED,
            EXCALIDRAW_TARGET_RESPONSE_RESOLVER_PENDING,
        } and not self.selected_response_path:
            raise ValueError("selected response path is required for selected target response")
        if self.status == EXCALIDRAW_TARGET_RESPONSE_RESOLVER_ACCEPTED and not self.target_url:
            raise ValueError("accepted target-response resolution requires target URL")
        if self.status.startswith("blocked_") and not self.blockers:
            raise ValueError("blocked target-response resolution requires blockers")
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
            raise ValueError("Excalidraw target-response resolver attempted a forbidden effect")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["candidates_inspected"] = list(self.candidates_inspected)
        payload["blockers"] = list(self.blockers)
        payload["blocked_effects"] = list(self.blocked_effects)
        return payload


def resolve_excalidraw_target_response(
    vault_root: str | Path,
    *,
    response_path: str | Path = "",
    generated_at: str | None = None,
) -> ExcalidrawTargetResponseResolution:
    """Resolve the latest accepted or pending target response without execution."""
    timestamp = generated_at or _now_utc()
    vault = _vault_path(vault_root)
    pending = _pending_root(vault)
    blockers: list[str] = []
    summaries: list[dict[str, Any]] = []
    usable: list[dict[str, Any]] = []

    if response_path:
        try:
            paths = [_path_under_pending(vault, response_path)]
        except ValueError as exc:
            blockers.append(str(exc))
            paths = []
    elif pending.is_dir():
        paths = sorted(path.resolve() for path in pending.glob(EXCALIDRAW_TARGET_RESPONSE_PATTERN) if path.is_file())
    else:
        paths = []

    for path in paths:
        payload, read_blocker = _read_json(path)
        blocker = read_blocker
        if payload is not None:
            usable_ok, usable_blocker = _response_usable(payload)
            blocker = usable_blocker
            if usable_ok:
                status = str(payload.get("status") or "")
                target_url = str(payload.get("target_url") or "")
                candidate = _candidate_summary(path, payload, "")
                candidate["payload"] = payload
                candidate["selection_status"] = status
                candidate["target_url"] = target_url
                usable.append(candidate)
        summaries.append(_candidate_summary(path, payload, blocker))

    accepted = [candidate for candidate in usable if candidate["selection_status"] == EXCALIDRAW_TARGET_RESPONSE_ACCEPTED]
    pending_candidates = [
        candidate for candidate in usable if candidate["selection_status"] == EXCALIDRAW_TARGET_RESPONSE_PENDING
    ]
    selected_pool = accepted or pending_candidates
    selected = sorted(selected_pool, key=_sort_key)[-1] if selected_pool else None

    if selected:
        selected_status = str(selected["selection_status"])
        target_url = str(selected.get("target_url") or "")
        status = (
            EXCALIDRAW_TARGET_RESPONSE_RESOLVER_ACCEPTED
            if selected_status == EXCALIDRAW_TARGET_RESPONSE_ACCEPTED
            else EXCALIDRAW_TARGET_RESPONSE_RESOLVER_PENDING
        )
        next_pass = (
            "excalidraw-local-browser-mcp-live-readiness-with-target"
            if status == EXCALIDRAW_TARGET_RESPONSE_RESOLVER_ACCEPTED
            else "external-runtime-provide-excalidraw-target-url"
        )
        selected_path = str(selected["path"])
    else:
        target_url = ""
        selected_status = ""
        selected_path = ""
        if not paths:
            status = EXCALIDRAW_TARGET_RESPONSE_RESOLVER_MISSING
            blockers.append("excalidraw_target_response_artifact_missing")
        else:
            status = EXCALIDRAW_TARGET_RESPONSE_RESOLVER_INVALID
            blockers.append("no_accepted_or_pending_excalidraw_target_response_found")
        next_pass = "external-runtime-provide-excalidraw-target-url"

    packet = ExcalidrawTargetResponseResolution(
        record_type=EXCALIDRAW_TARGET_RESPONSE_RESOLVER_RECORD_TYPE,
        schema_version=EXCALIDRAW_TARGET_RESPONSE_RESOLVER_VERSION,
        generated_at=timestamp,
        status=status,
        selected_response_path=selected_path,
        selected_response_status=selected_status,
        target_url=target_url,
        target_host=_target_host(target_url),
        candidates_inspected=tuple(summaries),
        blockers=tuple(blockers),
        next_recommended_pass=next_pass,
    )
    packet.validate()
    return packet


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resolve latest Excalidraw target response without execution.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--response-path", default="", help="Optional explicit response artifact path under pending inputs.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    packet = resolve_excalidraw_target_response(args.vault_root, response_path=args.response_path)
    payload = packet.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {payload['status']}")
        print(f"selected_response_path: {payload['selected_response_path']}")
        print(f"target_url: {payload['target_url']}")
        for blocker in payload["blockers"]:
            print(f"blocker: {blocker}")
        print(f"next_recommended_pass: {payload['next_recommended_pass']}")
    return 0 if not payload["status"].startswith("blocked_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
