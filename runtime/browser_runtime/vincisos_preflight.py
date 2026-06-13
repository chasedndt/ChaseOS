"""Fail-closed readiness preflight for a future VincisOS browser proof.

This module does not launch a browser, connect to CDP, inspect screenshots, or
write skill artifacts. It only validates whether a proposed VincisOS target is
safe enough to be handed to a later Browser Runtime Adapter pass.
"""

from __future__ import annotations

import argparse
import json
import socket
from dataclasses import asdict, dataclass, field
from typing import Any
from urllib.parse import urlparse


LOCAL_BROWSER_HOSTS = ("127.0.0.1", "localhost", "::1")


@dataclass(frozen=True)
class VincisOSBrowserPreflightRequest:
    """Inputs for a non-executing VincisOS browser readiness check."""

    target_url: str | None = None
    target_name: str = "VincisOS"
    mode: str = "shadow"
    allowed_hosts: list[str] = field(default_factory=lambda: list(LOCAL_BROWSER_HOSTS))
    require_running_target: bool = False
    probe_reachability: bool = False
    allow_real_profile: bool = False
    allow_credentials: bool = False
    allow_cdp: bool = False
    allow_canonical_writeback: bool = False
    allow_skill_activation: bool = False


@dataclass(frozen=True)
class VincisOSBrowserPreflightResult:
    """Machine-readable result for the readiness gate."""

    ok: bool
    status: str
    target_name: str
    target_url: str | None
    blockers: list[dict[str, str]]
    checks: dict[str, Any]
    future_shadow_test_ready: bool
    next_allowed_step: str | None
    browser_launch_attempted: bool = False
    cdp_connection_attempted: bool = False
    screenshot_attempted: bool = False
    profile_access_attempted: bool = False
    credentials_read: bool = False
    skill_activation_attempted: bool = False
    canonical_writeback_attempted: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _blocker(blocker_id: str, message: str) -> dict[str, str]:
    return {"blocker_id": blocker_id, "message": message}


def _parse_port(parsed) -> int | None:
    try:
        return parsed.port
    except ValueError:
        return None


def _probe_local_socket(host: str, port: int, timeout_seconds: float = 0.5) -> tuple[bool, str | None]:
    """Check that a local port accepts TCP without sending an HTTP request."""
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True, None
    except OSError as exc:
        return False, str(exc)


def evaluate_vincisos_browser_preflight(
    request: VincisOSBrowserPreflightRequest | None = None,
) -> VincisOSBrowserPreflightResult:
    """Evaluate whether a future VincisOS browser proof may proceed.

    The function intentionally performs no browser work. Optional reachability
    probing is restricted to a local TCP connect check and is off by default.
    """
    req = request or VincisOSBrowserPreflightRequest()
    blockers: list[dict[str, str]] = []
    checks: dict[str, Any] = {
        "allowed_hosts": list(req.allowed_hosts),
        "mode": req.mode,
        "browser_execution_allowed_by_this_preflight": False,
        "throwaway_profile_required": True,
        "real_profile_allowed": False,
        "credentials_allowed": False,
        "cdp_allowed": False,
        "canonical_writeback_allowed": False,
        "skill_activation_allowed": False,
    }

    if req.mode != "shadow":
        blockers.append(_blocker("mode_not_shadow", "Only shadow readiness mode is accepted."))
    if req.allow_real_profile:
        blockers.append(_blocker("real_profile_forbidden", "Real browser profiles are forbidden."))
    if req.allow_credentials:
        blockers.append(_blocker("credentials_forbidden", "Saved credentials and credential reads are forbidden."))
    if req.allow_cdp:
        blockers.append(_blocker("cdp_execution_forbidden", "CDP connection/execution is not authorized here."))
    if req.allow_canonical_writeback:
        blockers.append(
            _blocker("canonical_writeback_forbidden", "Canonical ChaseOS writeback is forbidden for this preflight.")
        )
    if req.allow_skill_activation:
        blockers.append(_blocker("skill_activation_forbidden", "Skill activation is forbidden for this preflight."))

    parsed = None
    host = ""
    port = None
    if not req.target_url:
        blockers.append(
            _blocker(
                "vincisos_target_url_missing",
                "No explicit local VincisOS target URL was supplied or discovered.",
            )
        )
    else:
        parsed = urlparse(req.target_url)
        host = (parsed.hostname or "").lower()
        port = _parse_port(parsed)
        checks.update(
            {
                "scheme": parsed.scheme,
                "host": host,
                "port": port,
                "path": parsed.path or "/",
            }
        )
        if parsed.scheme not in {"http", "https"}:
            blockers.append(_blocker("unsupported_scheme", "Only http/https local UI targets are allowed."))
        if host not in {item.lower() for item in req.allowed_hosts}:
            blockers.append(_blocker("target_host_not_local_allowlisted", "Target host is not local/allowlisted."))
        if port is None:
            blockers.append(_blocker("target_port_missing", "A local dev-server port must be declared."))

    if req.require_running_target and not req.probe_reachability:
        blockers.append(
            _blocker(
                "running_target_unverified",
                "A running target was required, but local reachability probing was not enabled.",
            )
        )

    if req.probe_reachability:
        if host not in {item.lower() for item in req.allowed_hosts} or port is None:
            blockers.append(
                _blocker("reachability_probe_not_safe", "Reachability probe requires a local allowlisted host and port.")
            )
            checks["local_socket_reachable"] = False
        else:
            reachable, error = _probe_local_socket(host, port)
            checks["local_socket_reachable"] = reachable
            if error:
                checks["local_socket_error"] = error
            if req.require_running_target and not reachable:
                blockers.append(_blocker("local_target_not_reachable", "Local target port did not accept TCP."))

    checks["url_is_local"] = bool(req.target_url and host in {item.lower() for item in req.allowed_hosts})
    checks["target_url_declared"] = bool(req.target_url)
    checks["target_port_declared"] = port is not None
    checks["browser_launch_attempted"] = False
    checks["cdp_connection_attempted"] = False
    checks["screenshot_attempted"] = False

    ok = not blockers
    status = "ready_for_future_vincisos_shadow_browser_test_no_execution" if ok else "blocked_vincisos_browser_preflight"
    next_step = (
        "A later pass may run a local-only shadow browser proof with a throwaway profile and draft-only artifacts."
        if ok
        else None
    )
    return VincisOSBrowserPreflightResult(
        ok=ok,
        status=status,
        target_name=req.target_name,
        target_url=req.target_url,
        blockers=blockers,
        checks=checks,
        future_shadow_test_ready=ok,
        next_allowed_step=next_step,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the non-executing VincisOS browser readiness preflight.")
    parser.add_argument("--target-url", default=None, help="Local VincisOS URL, e.g. http://127.0.0.1:4173")
    parser.add_argument("--target-name", default="VincisOS")
    parser.add_argument("--require-running-target", action="store_true")
    parser.add_argument("--probe-reachability", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print JSON output. Text output is not implemented.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    result = evaluate_vincisos_browser_preflight(
        VincisOSBrowserPreflightRequest(
            target_url=args.target_url,
            target_name=args.target_name,
            require_running_target=args.require_running_target,
            probe_reachability=args.probe_reachability,
        )
    )
    print(json.dumps(result.as_dict(), indent=2))
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
