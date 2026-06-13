"""Fail-closed preflight for a future full VincisOS product UI browser proof.

This module does not launch a browser, connect to CDP, take screenshots, click
UI, or write skill artifacts. It only decides whether a declared local target is
safe enough for a later, separate full UI proof pass.
"""

from __future__ import annotations

import argparse
import json
import socket
from dataclasses import asdict, dataclass, field
from typing import Any
from urllib.parse import urlparse

from runtime.browser_runtime.vincisos_preflight import LOCAL_BROWSER_HOSTS


STATIC_FIXTURE_PATHS = ("vincisos_shadow.html",)


@dataclass(frozen=True)
class VincisOSFullUISafeModePreflightRequest:
    """Inputs for the non-executing full VincisOS UI readiness gate."""

    target_url: str | None = None
    target_name: str = "VincisOS product UI"
    target_kind: str = "product_ui"
    mode: str = "shadow"
    safe_mode_asserted: bool = False
    allowed_hosts: list[str] = field(default_factory=lambda: list(LOCAL_BROWSER_HOSTS))
    require_running_target: bool = False
    probe_reachability: bool = False
    allow_real_profile: bool = False
    allow_credentials: bool = False
    allow_cdp: bool = False
    allow_browser_harness: bool = False
    allow_browser_use_cli_live: bool = False
    allow_trusted_skill_write: bool = False
    allow_skill_activation: bool = False
    allow_agent_bus_enqueue: bool = False
    allow_provider_call: bool = False
    allow_gate_mutation: bool = False
    allow_canonical_writeback: bool = False


@dataclass(frozen=True)
class VincisOSFullUISafeModePreflightResult:
    """Machine-readable result for the full UI preflight."""

    ok: bool
    status: str
    target_name: str
    target_url: str | None
    blockers: list[dict[str, str]]
    checks: dict[str, Any]
    future_full_ui_shadow_proof_ready: bool
    next_allowed_step: str | None
    browser_launch_attempted: bool = False
    cdp_connection_attempted: bool = False
    browser_harness_used: bool = False
    browser_use_cli_live_used: bool = False
    screenshot_attempted: bool = False
    profile_access_attempted: bool = False
    credentials_read: bool = False
    trusted_skill_write_attempted: bool = False
    skill_activation_attempted: bool = False
    agent_bus_enqueue_attempted: bool = False
    provider_call_attempted: bool = False
    gate_mutation_attempted: bool = False
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
    """Check local TCP reachability without sending an HTTP request."""
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True, None
    except OSError as exc:
        return False, str(exc)


def _is_static_fixture_path(path: str) -> bool:
    normalized = path.lower().strip("/")
    return any(normalized.endswith(item) for item in STATIC_FIXTURE_PATHS)


def evaluate_vincisos_full_ui_safe_mode_preflight(
    request: VincisOSFullUISafeModePreflightRequest | None = None,
) -> VincisOSFullUISafeModePreflightResult:
    """Evaluate readiness for a future full VincisOS product UI proof.

    The function is intentionally non-executing. Reachability probing is local
    TCP only, optional, and never attempts browser or HTTP inspection.
    """
    req = request or VincisOSFullUISafeModePreflightRequest()
    blockers: list[dict[str, str]] = []
    checks: dict[str, Any] = {
        "allowed_hosts": list(req.allowed_hosts),
        "target_kind": req.target_kind,
        "mode": req.mode,
        "safe_mode_asserted": req.safe_mode_asserted,
        "browser_execution_allowed_by_this_preflight": False,
        "throwaway_profile_required": True,
        "real_profile_allowed": False,
        "credentials_allowed": False,
        "cdp_allowed": False,
        "browser_harness_allowed": False,
        "browser_use_cli_live_allowed": False,
        "trusted_skill_write_allowed": False,
        "skill_activation_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_call_allowed": False,
        "gate_mutation_allowed": False,
        "canonical_writeback_allowed": False,
    }

    if req.target_kind != "product_ui":
        blockers.append(_blocker("target_kind_not_product_ui", "Full UI proof requires target_kind=product_ui."))
    if req.mode != "shadow":
        blockers.append(_blocker("mode_not_shadow", "Only shadow readiness mode is accepted."))
    if not req.safe_mode_asserted:
        blockers.append(_blocker("safe_mode_not_asserted", "The target must be explicitly declared safe/test mode."))

    forbidden_flags = {
        "real_profile_forbidden": (req.allow_real_profile, "Real browser profiles are forbidden."),
        "credentials_forbidden": (req.allow_credentials, "Saved credentials and credential reads are forbidden."),
        "cdp_execution_forbidden": (req.allow_cdp, "CDP connection/execution is not authorized here."),
        "browser_harness_forbidden": (req.allow_browser_harness, "Browser Harness is not authorized here."),
        "browser_use_cli_live_forbidden": (
            req.allow_browser_use_cli_live,
            "Live Browser Use CLI execution is not authorized here.",
        ),
        "trusted_skill_write_forbidden": (
            req.allow_trusted_skill_write,
            "Trusted Browser Skill or SiteOps Skill Card writes are forbidden.",
        ),
        "skill_activation_forbidden": (req.allow_skill_activation, "Skill activation is forbidden."),
        "agent_bus_enqueue_forbidden": (req.allow_agent_bus_enqueue, "Agent Bus enqueue is forbidden."),
        "provider_call_forbidden": (req.allow_provider_call, "Provider/API calls are forbidden."),
        "gate_mutation_forbidden": (req.allow_gate_mutation, "Gate mutation is forbidden."),
        "canonical_writeback_forbidden": (
            req.allow_canonical_writeback,
            "Canonical ChaseOS writeback is forbidden.",
        ),
    }
    for blocker_id, (flag_enabled, message) in forbidden_flags.items():
        if flag_enabled:
            blockers.append(_blocker(blocker_id, message))

    host = ""
    port = None
    if not req.target_url:
        blockers.append(_blocker("full_ui_target_url_missing", "No explicit local VincisOS product UI URL supplied."))
    else:
        parsed = urlparse(req.target_url)
        host = (parsed.hostname or "").lower()
        port = _parse_port(parsed)
        path = parsed.path or "/"
        is_static_fixture = _is_static_fixture_path(path)
        checks.update(
            {
                "scheme": parsed.scheme,
                "host": host,
                "port": port,
                "path": path,
                "static_fixture_detected": is_static_fixture,
            }
        )
        if parsed.scheme not in {"http", "https"}:
            blockers.append(_blocker("unsupported_scheme", "Only http/https local UI targets are allowed."))
        if host not in {item.lower() for item in req.allowed_hosts}:
            blockers.append(_blocker("target_host_not_local_allowlisted", "Target host is not local/allowlisted."))
        if port is None:
            blockers.append(_blocker("target_port_missing", "A local dev-server port must be declared."))
        if is_static_fixture:
            blockers.append(
                _blocker(
                    "static_fixture_is_not_product_ui",
                    "The repo-local vincisos_shadow.html fixture cannot satisfy the full product UI gate.",
                )
            )

    if req.require_running_target and not req.probe_reachability:
        blockers.append(
            _blocker(
                "running_target_unverified",
                "A running product UI target was required, but local reachability probing was not enabled.",
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
                blockers.append(_blocker("local_target_not_reachable", "Local product UI port did not accept TCP."))

    checks["url_is_local"] = bool(req.target_url and host in {item.lower() for item in req.allowed_hosts})
    checks["target_url_declared"] = bool(req.target_url)
    checks["target_port_declared"] = port is not None
    checks["browser_launch_attempted"] = False
    checks["cdp_connection_attempted"] = False
    checks["screenshot_attempted"] = False

    ok = not blockers
    status = (
        "ready_for_future_vincisos_full_ui_shadow_proof_no_execution"
        if ok
        else "blocked_vincisos_full_ui_safe_mode_preflight"
    )
    next_step = (
        "A later pass may run a local-only full UI shadow proof with isolated browser state and draft-only artifacts."
        if ok
        else None
    )
    return VincisOSFullUISafeModePreflightResult(
        ok=ok,
        status=status,
        target_name=req.target_name,
        target_url=req.target_url,
        blockers=blockers,
        checks=checks,
        future_full_ui_shadow_proof_ready=ok,
        next_allowed_step=next_step,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the non-executing VincisOS full UI safe-mode preflight.")
    parser.add_argument("--target-url", default=None, help="Local VincisOS product UI URL, e.g. http://127.0.0.1:5173")
    parser.add_argument("--target-name", default="VincisOS product UI")
    parser.add_argument("--target-kind", default="product_ui")
    parser.add_argument("--safe-mode-asserted", action="store_true")
    parser.add_argument("--require-running-target", action="store_true")
    parser.add_argument("--probe-reachability", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print JSON output. Text output is not implemented.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    result = evaluate_vincisos_full_ui_safe_mode_preflight(
        VincisOSFullUISafeModePreflightRequest(
            target_url=args.target_url,
            target_name=args.target_name,
            target_kind=args.target_kind,
            safe_mode_asserted=args.safe_mode_asserted,
            require_running_target=args.require_running_target,
            probe_reachability=args.probe_reachability,
        )
    )
    print(json.dumps(result.as_dict(), indent=2))
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
