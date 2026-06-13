"""Read-only launch-readiness check for a future VincisOS product UI proof.

This module discovers whether ChaseOS currently has a registered local product
UI launch surface that can satisfy the VincisOS browser-proof target. It does
not start servers, open browsers, connect CDP, invoke shell commands, or write
artifacts.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from runtime.studio.app_launcher import build_studio_app_launcher_plan


READINESS_VERSION = "vincisos.product_ui_launch_readiness.v1"
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
TARGET_TERMS = ("vincisos", "product-ui", "product ui", "browser-runtime-product-target")


@dataclass(frozen=True)
class VincisOSProductUILaunchReadinessResult:
    """Machine-readable launch-readiness result for the future product UI proof."""

    ok: bool
    status: str
    readiness_version: str
    blockers: list[dict[str, str]]
    checks: dict[str, Any]
    discovered_apps: list[dict[str, Any]]
    candidate_apps: list[dict[str, Any]]
    next_allowed_step: str | None
    starts_server_attempted: bool = False
    shell_command_attempted: bool = False
    browser_launch_attempted: bool = False
    cdp_connection_attempted: bool = False
    browser_harness_used: bool = False
    browser_use_cli_live_used: bool = False
    profile_access_attempted: bool = False
    credentials_read: bool = False
    cookie_or_session_read: bool = False
    trusted_skill_write_attempted: bool = False
    skill_activation_attempted: bool = False
    agent_bus_enqueue_attempted: bool = False
    provider_call_attempted: bool = False
    gate_mutation_attempted: bool = False
    canonical_writeback_attempted: bool = False
    files_modified: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _blocker(blocker_id: str, message: str) -> dict[str, str]:
    return {"blocker_id": blocker_id, "message": message}


def _app_text(app: dict[str, Any]) -> str:
    fields = (
        app.get("id"),
        app.get("title"),
        app.get("summary"),
        app.get("module"),
        app.get("target_family"),
    )
    return " ".join(str(item).lower() for item in fields if item is not None)


def _is_vincisos_product_candidate(app: dict[str, Any]) -> bool:
    text = _app_text(app)
    return any(term in text for term in TARGET_TERMS)


def _sanitize_app(app: dict[str, Any]) -> dict[str, Any]:
    operator_launch = app.get("operator_launch") if isinstance(app.get("operator_launch"), dict) else {}
    runtime_status = app.get("runtime_status") if isinstance(app.get("runtime_status"), dict) else {}
    return {
        "id": app.get("id"),
        "title": app.get("title"),
        "module": app.get("module"),
        "default_host": app.get("default_host"),
        "default_port": app.get("default_port"),
        "default_url": app.get("default_url"),
        "health_path": app.get("health_path"),
        "local_only": app.get("local_only"),
        "read_only": app.get("read_only"),
        "write_capable": app.get("write_capable"),
        "starts_workflows": app.get("starts_workflows"),
        "operator_launch": {
            "execution_mode": operator_launch.get("execution_mode"),
            "launcher_executes": operator_launch.get("launcher_executes"),
            "browser_auto_open": operator_launch.get("browser_auto_open"),
            "default_url": operator_launch.get("default_url"),
            "health_url": operator_launch.get("health_url"),
        },
        "runtime_status": {
            "checked": runtime_status.get("checked"),
            "state": runtime_status.get("state"),
            "starts_child_app": runtime_status.get("starts_child_app"),
            "read_only_probe": runtime_status.get("read_only_probe"),
        },
    }


def _app_blockers(app: dict[str, Any]) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    app_id = str(app.get("id") or "unknown")
    host = str(app.get("default_host") or "").lower()
    operator_launch = app.get("operator_launch") if isinstance(app.get("operator_launch"), dict) else {}
    runtime_status = app.get("runtime_status") if isinstance(app.get("runtime_status"), dict) else {}

    if app.get("local_only") is not True:
        blockers.append(_blocker(f"{app_id}_not_local_only", "VincisOS product UI target must be local-only."))
    if host not in LOOPBACK_HOSTS:
        blockers.append(_blocker(f"{app_id}_host_not_loopback", "VincisOS product UI target must bind to loopback."))
    if app.get("default_port") in {None, ""}:
        blockers.append(_blocker(f"{app_id}_port_missing", "VincisOS product UI target must declare a local port."))
    if operator_launch.get("launcher_executes") is not False:
        blockers.append(_blocker(f"{app_id}_launcher_executes", "Launch registry must not execute child apps."))
    if operator_launch.get("browser_auto_open") is not False:
        blockers.append(_blocker(f"{app_id}_browser_auto_open", "Launch registry must not auto-open browsers."))
    if runtime_status.get("starts_child_app") is True:
        blockers.append(_blocker(f"{app_id}_health_probe_starts_app", "Health probe must not start child apps."))
    if app.get("starts_workflows") is True:
        blockers.append(_blocker(f"{app_id}_starts_workflows", "Product UI launch target must not start workflows."))
    return blockers


def build_vincisos_product_ui_launch_readiness(
    vault_root: str | Path = ".",
    *,
    host: str = "127.0.0.1",
    apps: Iterable[dict[str, Any]] | None = None,
) -> VincisOSProductUILaunchReadinessResult:
    """Report whether a VincisOS product UI launch surface exists without starting it."""
    if apps is None:
        plan = build_studio_app_launcher_plan(vault_root, host=host)
        raw_apps = list(plan.get("apps") or [])
        registry_available = True
    else:
        raw_apps = list(apps)
        registry_available = True

    discovered_apps = [_sanitize_app(app) for app in raw_apps if isinstance(app, dict)]
    candidates_raw = [app for app in raw_apps if isinstance(app, dict) and _is_vincisos_product_candidate(app)]
    candidate_apps = [_sanitize_app(app) for app in candidates_raw]
    blockers: list[dict[str, str]] = []

    if not candidate_apps:
        blockers.append(
            _blocker(
                "vincisos_product_ui_launch_target_not_registered",
                "No registered local app is marked as a VincisOS/product UI browser-proof target.",
            )
        )
    for candidate in candidates_raw:
        blockers.extend(_app_blockers(candidate))

    checks: dict[str, Any] = {
        "registry_available": registry_available,
        "discovered_app_count": len(discovered_apps),
        "candidate_app_count": len(candidate_apps),
        "launch_readiness_only": True,
        "starts_server_allowed_by_this_check": False,
        "shell_execution_allowed_by_this_check": False,
        "browser_execution_allowed_by_this_check": False,
        "cdp_allowed_by_this_check": False,
        "files_modified": False,
    }

    ok = not blockers
    status = (
        "vincisos_product_ui_launch_target_ready_no_start"
        if ok
        else "blocked_vincisos_product_ui_launch_readiness"
    )
    next_step = (
        "Operator may start the registered local app separately, then rerun the target availability probe."
        if ok
        else None
    )
    return VincisOSProductUILaunchReadinessResult(
        ok=ok,
        status=status,
        readiness_version=READINESS_VERSION,
        blockers=blockers,
        checks=checks,
        discovered_apps=discovered_apps,
        candidate_apps=candidate_apps,
        next_allowed_step=next_step,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check VincisOS product UI launch readiness without starting servers or browsers."
    )
    parser.add_argument("--vault-root", default=".", help="Path to ChaseOS vault root.")
    parser.add_argument("--host", default="127.0.0.1", help="Loopback host used for Studio app registry metadata.")
    parser.add_argument("--json", action="store_true", help="Print JSON output. Text output is not implemented.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    result = build_vincisos_product_ui_launch_readiness(args.vault_root, host=args.host)
    print(json.dumps(result.as_dict(), indent=2))
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
