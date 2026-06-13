"""Localhost-only Studio App Launcher / Discovery Registry.

This module provides an inspection surface for existing ChaseOS Studio local
apps. It intentionally does not start child apps, execute workflows, call
providers, automate browsers, deliver messages, mutate schedulers, or promote
canonical knowledge. Operators can use it to see which Studio apps exist, what
starts them, and which authority boundaries apply before launching an app
explicitly.
"""

from __future__ import annotations

from datetime import UTC, datetime
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from typing import Any
from urllib import error, request
from urllib.parse import urlparse

_APP_SURFACE = "studio_app_launcher_local_app"
_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 8769
_HEALTH_PROBE_TIMEOUT_SECONDS = 0.2
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
_STATUS_LEGEND = {
    "registered": "Declared in the Studio app registry; this is inventory, not liveness.",
    "offline": "Registered but no local health endpoint answered; launch manually if needed.",
    "reachable": "Registered and the local status probe answered without the launcher starting it.",
    "broken": "Registered and reachable enough to answer, but health returned an error status.",
    "not_checked": "Probe disabled for this response; no liveness conclusion was attempted.",
}
_SUPPORT_PORT_GROUP = {
    "title": "Advanced / Support ports",
    "advanced": True,
    "collapsed_by_default": True,
    "reason": "Support ports are noisy diagnostics, not primary Studio apps.",
}


class StudioAppLauncherError(RuntimeError):
    """Raised when the Studio App Launcher cannot proceed safely."""


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _require_loopback(host: str) -> None:
    if host not in _LOOPBACK_HOSTS:
        raise StudioAppLauncherError("studio app launcher must bind to localhost/loopback only")


def _escape(value: Any) -> str:
    return html.escape(str(value))


def _now_utc_label() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _action_contracts(app: dict[str, Any]) -> list[dict[str, Any]]:
    """Return non-executing user-facing launcher actions for one app card."""

    launch = app.get("operator_launch") or {}
    write_capable = bool(app.get("write_capable"))
    return [
        {
            "id": "open",
            "label": "Open",
            "kind": "link",
            "href": app.get("default_url"),
            "enabled_when": "runtime_status.state == reachable",
            "executes_in_launcher": False,
        },
        {
            "id": "start_request",
            "label": "Launch Guide",
            "kind": "confirmation_gated_request",
            "requires_confirmation": True,
            "write_capable": write_capable,
            "approved_backend_contract_only": True,
            "contract": "operator_terminal_only_launch_guidance",
            "request_summary": "Prepare a confirmed launch guide; this launcher never executes the command itself.",
            "executes_in_launcher": False,
            "launcher_executes": False,
            "health_url": launch.get("health_url"),
            "default_url": launch.get("default_url"),
        },
        {
            "id": "health",
            "label": "Health",
            "kind": "link",
            "href": launch.get("health_url"),
            "read_only_probe": True,
            "executes_in_launcher": False,
        },
        {
            "id": "authority",
            "label": "Authority",
            "kind": "disclosure",
            "summary": _authority_badge(app),
            "executes_in_launcher": False,
        },
    ]


def _probe_health_url(health_url: str) -> dict[str, Any]:
    """Probe a local health URL with a short inspection GET."""

    checked_at = _now_utc_label()
    probe = request.Request(health_url, method="GET")
    try:
        with request.urlopen(probe, timeout=_HEALTH_PROBE_TIMEOUT_SECONDS) as response:
            status = int(getattr(response, "status", 0) or 0)
    except error.HTTPError as exc:
        status = int(getattr(exc, "code", 0) or 0)
        return {
            "checked": True,
            "state": "broken" if status >= 500 else "reachable",
            "health_url": health_url,
            "http_status": status,
            "starts_child_app": False,
            "read_only_probe": True,
            "last_checked": checked_at,
            "reason": "http_error_status",
        }
    except (OSError, error.URLError, TimeoutError, ValueError):
        return {
            "checked": True,
            "state": "offline",
            "health_url": health_url,
            "http_status": None,
            "starts_child_app": False,
            "read_only_probe": True,
            "last_checked": checked_at,
        }
    return {
        "checked": True,
        "state": "reachable" if 200 <= status < 500 else "broken",
        "health_url": health_url,
        "http_status": status,
        "starts_child_app": False,
        "read_only_probe": True,
        "last_checked": checked_at,
    }


def _probe_app_health(app: dict[str, Any]) -> dict[str, Any]:
    """Probe a child Studio app health endpoint without starting anything."""

    health_url = f"http://{app['default_host']}:{int(app['default_port'])}{app['health_path']}"
    return _probe_health_url(health_url)


def _probe_support_port_health(entry: dict[str, Any]) -> dict[str, Any]:
    """Probe a support port endpoint without starting or supervising the process."""

    return _probe_health_url(str(entry["health_url"]))


def _operator_launch(command: str, *, host: str, port: int, health_path: str) -> dict[str, Any]:
    """Return copyable operator-terminal launch guidance without executing it."""

    health_url = f"http://{host}:{int(port)}{health_path}"
    default_url = f"http://{host}:{int(port)}/"
    return {
        "execution_mode": "operator_terminal_only",
        "copyable": True,
        "launcher_executes": False,
        "browser_auto_open": False,
        "command": f"{command} --host {host} --port {int(port)}",
        "health_command": f"curl -fsS --max-time 2 {health_url}",
        "open_url_command": f"Open {default_url} in your browser after health is reachable.",
        "health_url": health_url,
        "default_url": default_url,
    }


def _studio_app_registry(*, host: str) -> list[dict[str, Any]]:
    """Return the bounded local Studio app discovery registry.

    Ports are discovery metadata only. This launcher never starts the child apps;
    each app must be launched explicitly by an operator using its command.
    """

    return [
        {
            "id": "approval-center-app",
            "title": "ChaseOS Pulse Approval Center",
            "summary": "Local approval-center mount over Pulse decks, candidates, review decisions, approval requests, and final evidence gate state.",
            "command": "chaseos studio approval-center-app",
            "default_host": host,
            "default_port": 8773,
            "default_url": f"http://{host}:8773/",
            "health_path": "/health.json",
            "local_only": True,
            "read_only": True,
            "write_capable": False,
            "requires_confirmation_for_writes": False,
            "starts_workflows": False,
            "status": "available",
            "module": "runtime.studio.approval_center_app",
            "approval_center_mount": True,
            "payoff": "Gives Studio a unified Pulse review surface without granting approval execution, Agent Bus enqueue, provider calls, schedule activation, candidate apply, memory approval, or canonical writeback.",
            "operator_launch": _operator_launch("chaseos studio approval-center-app", host=host, port=8773, health_path="/health.json"),
        },
        {
            "id": "vincisos-product-ui-test-target",
            "title": "ChaseOS Studio Product UI Test Target",
            "summary": "Local safe-mode product UI target for Browser Runtime proofing with tabs, tables, approval posture, and a harmless client-side action.",
            "command": "chaseos studio product-ui-test-app",
            "default_host": host,
            "default_port": 8770,
            "default_url": f"http://{host}:8770/",
            "health_path": "/health.json",
            "local_only": True,
            "read_only": True,
            "write_capable": False,
            "requires_confirmation_for_writes": False,
            "starts_workflows": False,
            "status": "available",
            "module": "runtime.studio.product_ui_test_app",
            "target_family": "vincisos-product-ui browser-runtime-product-target",
            "browser_proof_target": True,
            "payoff": "Gives Browser Runtime a realistic but synthetic ChaseOS Studio product UI target without account, credential, workflow, provider, Gate, Agent Bus, trusted-write, or canonical authority.",
            "operator_launch": _operator_launch("chaseos studio product-ui-test-app", host=host, port=8770, health_path="/health.json"),
        },
        {
            "id": "studio-desktop-shell-app",
            "title": "ChaseOS Studio Shell",
            "summary": "Local Studio product shell that mounts Agents / Runtimes, App Launcher, Approvals, and Personal Memory surfaces without granting new mutation authority.",
            "command": "chaseos studio desktop-shell-app",
            "default_host": host,
            "default_port": 8772,
            "default_url": f"http://{host}:8772/",
            "health_path": "/health.json",
            "local_only": True,
            "read_only": True,
            "write_capable": False,
            "requires_confirmation_for_writes": False,
            "starts_workflows": False,
            "status": "available",
            "module": "runtime.studio.desktop_shell_app",
            "studio_shell_mvp": True,
            "runtime_cockpit_mount": True,
            "payoff": "Provides the Studio shell integration point for Agents / Runtimes, App Launcher, Approvals, and Personal Memory while desktop packaging, executable approvals, and governed settings remain controlled.",
            "operator_launch": _operator_launch("chaseos studio desktop-shell-app", host=host, port=8772, health_path="/health.json"),
        },
        {
            "id": "studio-dashboard-app",
            "title": "Studio Home",
            "summary": "Visual overview of schedules, Agent Bus, quarantine, graph, memory, approvals, Pulse, and runtime startup readiness.",
            "command": "chaseos studio dashboard-app",
            "default_host": host,
            "default_port": 8768,
            "default_url": f"http://{host}:8768/",
            "health_path": "/health.json",
            "local_only": True,
            "read_only": True,
            "write_capable": False,
            "requires_confirmation_for_writes": False,
            "starts_workflows": False,
            "status": "available",
            "module": "runtime.studio.dashboard_app",
            "payoff": "Fast operator summary for Hermes/OpenClaw handoffs and ChaseOS status checks without granting Home mutation authority.",
            "operator_launch": _operator_launch("chaseos studio dashboard-app", host=host, port=8768, health_path="/health.json"),
        },
        {
            "id": "runtime-cockpit-app",
            "title": "Agents / Runtimes",
            "summary": "Local runtime mount over the Studio runtime contract, startup posture, approval readiness, and app registry.",
            "command": "chaseos studio runtime-cockpit-app",
            "default_host": host,
            "default_port": 8771,
            "default_url": f"http://{host}:8771/",
            "health_path": "/health.json",
            "local_only": True,
            "read_only": True,
            "write_capable": False,
            "requires_confirmation_for_writes": False,
            "starts_workflows": False,
            "status": "available",
            "module": "runtime.studio.runtime_cockpit_app",
            "payoff": "Mounts the runtime contract for Studio without granting host startup mutation, workflow execution, provider calls, delivery, or canonical writeback.",
            "operator_launch": _operator_launch("chaseos studio runtime-cockpit-app", host=host, port=8771, health_path="/health.json"),
        },
        {
            "id": "studio-app-launcher",
            "title": "Studio App Launcher",
            "summary": "Discovery and readiness manager for registered ChaseOS Studio local apps and support ports.",
            "command": "chaseos studio app-launcher",
            "default_host": host,
            "default_port": 8769,
            "default_url": f"http://{host}:8769/",
            "health_path": "/health.json",
            "local_only": True,
            "read_only": True,
            "write_capable": False,
            "requires_confirmation_for_writes": False,
            "starts_workflows": False,
            "status": "available",
            "module": "runtime.studio.app_launcher",
            "self_inventory_surface": True,
            "payoff": "Gives the operator one bounded place to see every registered ChaseOS app port and live/offline status without auto-starting child apps.",
            "operator_launch": _operator_launch("chaseos studio app-launcher", host=host, port=8769, health_path="/health.json"),
        },
    ]


def _support_operator_launch(command: str, *, health_url: str, default_url: str | None = None) -> dict[str, Any]:
    return {
        "execution_mode": "operator_terminal_only",
        "copyable": True,
        "launcher_executes": False,
        "browser_auto_open": False,
        "command": command,
        "health_command": f"curl -fsS --max-time 2 {health_url}",
        "open_url_command": f"Open {default_url} in your browser after health is reachable." if default_url else "No browser open command; use the health endpoint for readiness.",
        "health_url": health_url,
        "default_url": default_url,
    }


def _support_port_registry(*, host: str) -> list[dict[str, Any]]:
    """Return observed/support local ports that are not registered Studio child apps."""

    entries = [
        (8780, "current-session-override-shell", "Current session override shell", "Session-local override shell when explicitly launched for a Studio run.", "operator-managed override shell", "/health.json", "inspection/status; may front a separately confirmed local shell", None),
        (8781, "static-artifact-server", "Static artifact server", "Local static artifact server used for Studio evidence files and screenshots.", "operator-managed static artifact server", "/health.json", "inspection/static artifact serving", None),
        (9119, "hermes-kanban-dashboard", "Hermes Kanban", "Hermes dashboard and Kanban board surface when the Hermes dashboard service is running.", "hermes dashboard operator service", "/health.json", "inspection status from this launcher", None),
        (11434, "ollama-local-models", "Ollama local models", "Ollama API if local model serving is running.", "ollama serve", "/api/tags", "local model API; external to Studio launcher", None),
        (9222, "chrome-cdp", "Chrome CDP", "Chrome DevTools Protocol endpoint if Chromium was launched for browser proofing.", "chromium --remote-debugging-port=9222", "/json/version", "browser debug endpoint; this launcher only probes readiness", None),
        (4173, "browser-runtime-local-target", "Browser/runtime local target example", "Common Vite/browser-runtime draft target port used by local evidence runs.", "operator-managed draft server", "/", "inspection readiness probe", None),
        (3002, "excalidraw-canvas-loopback", "Excalidraw/canvas loopback example", "Optional Excalidraw/canvas loopback used by visual/canvas experiments.", "operator-managed canvas loopback", "/", "inspection readiness probe", None),
        (8787, "historical-override-8787", "Historical override / smoke port 8787", "Historical compatibility or smoke override port retained for operator visibility.", "operator-managed compatibility server", "/health.json", "inspection readiness probe", None),
        (8788, "historical-override-8788", "Historical override / smoke port 8788", "Historical compatibility or smoke override port retained for operator visibility.", "operator-managed compatibility server", "/health.json", "inspection readiness probe", None),
        (8789, "historical-override-8789", "Historical override / smoke port 8789", "Historical compatibility or smoke override port retained for operator visibility.", "operator-managed compatibility server", "/health.json", "inspection readiness probe", None),
    ]
    support: list[dict[str, Any]] = []
    for port, entry_id, title, summary, command, health_path, authority, default_path in entries:
        default_url = f"http://{host}:{port}{default_path or '/'}"
        health_url = f"http://{host}:{port}{health_path}"
        support.append(
            {
                "id": entry_id,
                "title": title,
                "summary": summary,
                "command": command,
                "host": host,
                "port": port,
                "default_url": default_url,
                "health_path": health_path,
                "health_url": health_url,
                "authority": authority,
                "local_only": True,
                "read_only_probe": True,
                "starts_child_app": False,
                "starts_workflows": False,
                "operator_launch": _support_operator_launch(command, health_url=health_url, default_url=default_url),
            }
        )
    return support


def _liveness_label(*, registered: bool, state: str) -> str:
    registration = "Registered app" if registered else "Support port"
    return f"{registration} · {state.replace('_', ' ').title()}"


def _app_liveness_counts(apps: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"registered": len(apps), "reachable": 0, "offline": 0, "broken": 0, "not_checked": 0}
    for app in apps:
        state = str((app.get("runtime_status") or {}).get("state") or "not_checked")
        counts[state] = counts.get(state, 0) + 1
    return counts


def build_studio_app_launcher_plan(
    vault_root: str | Path,
    *,
    host: str = _DEFAULT_HOST,
    port: int = _DEFAULT_PORT,
    probe_health: bool = True,
    current_launcher_running: bool = False,
) -> dict[str, Any]:
    """Return the local launcher plan without starting a server or child app."""

    _require_loopback(host)
    vault = _vault_path(vault_root)
    apps = []
    seen_app_ids: set[str] = set()
    for app in _studio_app_registry(host=host):
        app_id = str(app.get("id") or "")
        if app_id in seen_app_ids:
            continue
        seen_app_ids.add(app_id)
        apps.append(app)
    support_ports = _support_port_registry(host=host)
    for app in apps:
        if probe_health:
            if (
                current_launcher_running
                and app.get("id") == "studio-app-launcher"
                and str(app.get("default_host")) == host
                and int(app.get("default_port")) == int(port)
            ):
                app["runtime_status"] = {
                    "checked": True,
                    "state": "reachable",
                    "health_url": f"http://{host}:{int(port)}{app['health_path']}",
                    "http_status": 200,
                    "starts_child_app": False,
                    "read_only_probe": True,
                    "reason": "current_launcher_server",
                    "last_checked": _now_utc_label(),
                }
            else:
                app["runtime_status"] = _probe_app_health(app)
        else:
            app["runtime_status"] = {
                "checked": False,
                "state": "not_checked",
                "health_url": f"http://{app['default_host']}:{int(app['default_port'])}{app['health_path']}",
                "http_status": None,
                "starts_child_app": False,
                "read_only_probe": True,
                "reason": "health_probe_disabled",
                "last_checked": None,
            }
        app["actions"] = _action_contracts(app)
        app["registration_status"] = "registered"
        app["liveness_label"] = _liveness_label(
            registered=True,
            state=str(app["runtime_status"].get("state", "unknown")),
        )
    for entry in support_ports:
        if probe_health:
            entry["runtime_status"] = _probe_support_port_health(entry)
        else:
            entry["runtime_status"] = {
                "checked": False,
                "state": "not_checked",
                "health_url": entry["health_url"],
                "http_status": None,
                "starts_child_app": False,
                "read_only_probe": True,
                "reason": "health_probe_disabled",
            }
        entry["liveness_label"] = _liveness_label(
            registered=False,
            state=str(entry["runtime_status"].get("state", "unknown")),
        )
    return {
        "ok": True,
        "surface": _APP_SURFACE,
        "title": "ChaseOS Studio App Launcher",
        "host": host,
        "port": int(port),
        "url": f"http://{host}:{int(port)}/",
        "local_only": True,
        "authority": {
            "binds_loopback_only": True,
            "read_only": True,
            "starts_child_apps": False,
            "writes_vault": False,
            "browser_automation": False,
            "mcp_scope_changed": False,
            "provider_calls_allowed": False,
            "delivery_allowed": False,
            "scheduler_changed": False,
            "canonical_mutation_allowed": False,
            "workflow_execution_allowed": False,
        },
        "reads": [
            "static Studio app discovery registry",
            "observed ChaseOS support/local port registry",
            "existing Studio app command contracts as operator guidance",
            "localhost child-app and support-port health endpoints using short inspection GET probes",
        ],
        "health_probe": {
            "enabled": bool(probe_health),
            "read_only": True,
            "starts_child_apps": False,
            "timeout_seconds": _HEALTH_PROBE_TIMEOUT_SECONDS,
        },
        "status_legend": dict(_STATUS_LEGEND),
        "liveness_counts": _app_liveness_counts(apps),
        "support_port_group": dict(_SUPPORT_PORT_GROUP),
        "possible_writes": [],
        "allowed_actions": [],
        "apps": apps,
        "app_count": len(apps),
        "support_ports": support_ports,
        "support_port_count": len(support_ports),
        "port_inventory": {
            "registered_app_ports": [int(app["default_port"]) for app in apps],
            "support_ports": [int(entry["port"]) for entry in support_ports],
            "all_ports": sorted({int(app["default_port"]) for app in apps} | {int(entry["port"]) for entry in support_ports}),
        },
        "vault_root": str(vault),
    }


def _authority_badge(app: dict[str, Any]) -> str:
    if app.get("read_only"):
        return "Inspect only"
    if app.get("requires_confirmation_for_writes"):
        return "Confirmed action"
    if app.get("write_capable"):
        return "Action capable"
    return "Bounded"


def _render_app_card(app: dict[str, Any]) -> str:
    status = app.get("runtime_status") or {}
    actions = {action.get("id"): action for action in app.get("actions", [])}
    open_action = actions.get("open") or {}
    start_action = actions.get("start_request") or {}
    health_action = actions.get("health") or {}
    authority_action = actions.get("authority") or {}
    launch = app.get("operator_launch") or {}
    source_refs = app.get("source_reference_examples") or []
    source_refs_html = ""
    if source_refs:
        source_refs_html = "<p><strong>Source references:</strong> " + ", ".join(f"<code>{_escape(ref)}</code>" for ref in source_refs) + "</p>"
    return f"""
      <section class=\"app-card state-{_escape(status.get('state', 'unknown'))}\">
        <div class=\"badge\">{_escape(_authority_badge(app))}</div>
        <div class=\"liveness-badge\">{_escape(app.get('liveness_label') or _liveness_label(registered=True, state=str(status.get('state', 'unknown'))))}</div>
        <h2>{_escape(app.get('title'))}</h2>
        <p><strong>Description:</strong> {_escape(app.get('summary'))}</p>
        <p class=\"payoff\">{_escape(app.get('payoff'))}</p>
        {source_refs_html}
        <div class=\"actions\" aria-label=\"{_escape(app.get('title'))} actions\">
          <a class=\"button primary\" href=\"{_escape(open_action.get('href', app.get('default_url')))}\">Open</a>
          <button class=\"button\" type=\"button\" data-action=\"start-request\" data-confirmation-required=\"{_escape(start_action.get('requires_confirmation', True)).lower()}\" data-approved-backend-contract-only=\"{_escape(start_action.get('approved_backend_contract_only', True)).lower()}\" data-executes-in-launcher=\"{_escape(start_action.get('executes_in_launcher', False)).lower()}\">Launch Guide</button>
          <a class=\"button\" href=\"{_escape(health_action.get('href', status.get('health_url', '#')))}\">Health</a>
          <details class=\"authority-detail\"><summary class=\"button subtle\">Authority</summary><p>{_escape(authority_action.get('summary', _authority_badge(app)))}</p><p>Write capable: {_escape(app.get('write_capable'))}; confirmation required: {_escape(app.get('requires_confirmation_for_writes'))}; launcher executes: false.</p></details>
        </div>
        <dl>
          <dt>Registration</dt><dd>{_escape(app.get('registration_status', 'registered'))}</dd>
          <dt>Port</dt><dd>{_escape(app.get('default_port'))}</dd>
          <dt>Status</dt><dd>{_escape(status.get('state', 'unknown'))}</dd>
          <dt>Last Checked</dt><dd>{_escape(status.get('last_checked') or 'not checked')}</dd>
          <dt>Health</dt><dd><code>{_escape(status.get('health_url') or launch.get('health_url') or '')}</code></dd>
          <dt>Local only</dt><dd>{_escape(app.get('local_only'))}</dd>
          <dt>Starts workflows</dt><dd>{_escape(app.get('starts_workflows'))}</dd>
        </dl>
        <details class=\"launch-guidance\"><summary>Manual launch guide</summary><p>Use this only if you choose to start or check this local surface yourself. Studio never runs it from this page.</p><p><strong>Launch command</strong></p><code>{_escape(launch.get('command', app.get('command')))}</code><p><strong>Health check</strong></p><code>{_escape(launch.get('health_command', ''))}</code></details>
      </section>
    """


def render_studio_app_launcher_html(plan: dict[str, Any]) -> str:
    """Render the launcher/discovery page."""

    apps_html = "".join(_render_app_card(app) for app in plan.get("apps", []))
    authority_rows = "".join(
        f"<tr><th>{_escape(key)}</th><td>{_escape(value)}</td></tr>"
        for key, value in (plan.get("authority") or {}).items()
    )
    support_group = plan.get("support_port_group") or _SUPPORT_PORT_GROUP
    support_rows = "".join(
        f"""
        <tr>
          <td>{_escape(entry.get('port'))}</td>
          <td>{_escape(entry.get('title'))}</td>
          <td><code>{_escape(entry.get('health_url'))}</code></td>
          <td>{_escape(entry.get('liveness_label') or (entry.get('runtime_status') or {}).get('state', 'unknown'))}</td>
          <td>{_escape(entry.get('authority'))}</td>
          <td><code>{_escape(entry.get('command'))}</code></td>
        </tr>
        """
        for entry in plan.get("support_ports", [])
    )

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>{_escape(plan.get('title'))}</title>
  <style>
    :root {{ color-scheme: dark; font-family: Inter, Segoe UI, sans-serif; background: #070b12; color: #e6edf7; }}
    body {{ margin: 0; padding: 28px; }}
    header {{ margin-bottom: 22px; }}
    h1 {{ margin: 0 0 8px; font-size: 32px; }}
    .muted {{ color: #94a3b8; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; }}
    .app-card, .panel {{ background: #101827; border: 1px solid #263449; border-radius: 14px; padding: 18px; box-shadow: 0 10px 24px rgba(0,0,0,.22); }}
    .app-card h2, .panel h2 {{ margin: 8px 0 10px; color: #93c5fd; }}
    .badge, .liveness-badge {{ display: inline-block; background: #172554; color: #bfdbfe; border: 1px solid #1d4ed8; border-radius: 999px; padding: 4px 10px; font-size: 12px; margin-right: 6px; }}
    .liveness-badge {{ background: #1f2937; border-color: #475569; color: #e5e7eb; }}
    .state-reachable .liveness-badge {{ background: #052e16; border-color: #16a34a; color: #bbf7d0; }}
    .state-offline .liveness-badge {{ background: #422006; border-color: #d97706; color: #fed7aa; }}
    .state-broken .liveness-badge {{ background: #450a0a; border-color: #dc2626; color: #fecaca; }}
    .payoff {{ color: #c4b5fd; }}
    .actions {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 12px 0 14px; }}
    .button {{ display: inline-block; border: 1px solid #3b82f6; background: #102342; color: #dbeafe; border-radius: 9px; padding: 8px 11px; text-decoration: none; font: inherit; cursor: pointer; }}
    .button.primary {{ background: #1d4ed8; color: white; }}
    .button.subtle {{ background: #111827; }}
    .debug-detail, .authority-detail {{ color: #cbd5e1; }}
    code {{ color: #f8fafc; background: #0f172a; padding: 2px 5px; border-radius: 5px; }}
    dl {{ display: grid; grid-template-columns: 110px 1fr; gap: 7px 10px; }}
    dt {{ color: #93c5fd; }}
    dd {{ margin: 0; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #263449; }}
    th {{ color: #93c5fd; width: 42%; }}
  </style>
</head>
<body>
  <header>
    <h1>{_escape(plan.get('title'))}</h1>
    <div class=\"muted\">Local-only URL: <code>{_escape(plan.get('url'))}</code> · Registry: <code>/apps.json</code> · Health: <code>/health.json</code></div>
    <p>This discovery page does not start child apps, execute workflows, mutate files, or call providers. Launch commands must be run explicitly outside this page.</p>
    <p>No provider, browser, delivery, scheduler, or canonical writeback authority is present here.</p>
  </header>
  <main>
    <section class=\"grid\">{apps_html}</section>
    <details class=\"panel advanced-support\" style=\"margin-top: 14px;\"><summary><h2>{_escape(support_group.get('title', 'Advanced / Support ports'))}</h2><span class=\"muted\">{_escape(support_group.get('reason', 'Support diagnostics'))}</span></summary><table><thead><tr><th>Port</th><th>Surface</th><th>Health endpoint</th><th>Reachability</th><th>Authority</th><th>Command</th></tr></thead><tbody>{support_rows}</tbody></table></details>
    <section class=\"panel\" style=\"margin-top: 14px;\"><h2>Launcher authority</h2><table>{authority_rows}</table></section>
  </main>
</body>
</html>"""


class _LauncherHandler(BaseHTTPRequestHandler):
    vault_root: Path
    host: str
    port: int

    def _write(self, status: int, body: str | bytes, *, content_type: str) -> None:
        payload = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            if path == "/health.json":
                plan = build_studio_app_launcher_plan(
                    self.vault_root,
                    host=self.host,
                    port=self.port,
                    probe_health=False,
                    current_launcher_running=True,
                )
                plan["self_health"] = {
                    "ok": True,
                    "fast_path": True,
                    "reason": "launcher self-health does not probe child or support ports",
                    "advertised_command_budget_seconds": 2,
                }
                self._write(200, json.dumps(plan, indent=2, default=str), content_type="application/json")
                return
            plan = build_studio_app_launcher_plan(
                self.vault_root,
                host=self.host,
                port=self.port,
                current_launcher_running=True,
            )
        except StudioAppLauncherError as exc:
            self._write(500, json.dumps({"ok": False, "error": str(exc)}), content_type="application/json")
            return
        if path == "/apps.json":
            self._write(200, json.dumps(plan, indent=2, default=str), content_type="application/json")
            return
        if path == "/":
            self._write(200, render_studio_app_launcher_html(plan), content_type="text/html; charset=utf-8")
            return
        self._write(404, "not found", content_type="text/plain; charset=utf-8")

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        return


def make_studio_app_launcher_handler(
    vault_root: str | Path,
    *,
    host: str = _DEFAULT_HOST,
    port: int = _DEFAULT_PORT,
) -> type[BaseHTTPRequestHandler]:
    """Return a configured request handler for tests or local serving."""

    _require_loopback(host)
    vault = _vault_path(vault_root)

    class Handler(_LauncherHandler):
        pass

    Handler.vault_root = vault
    Handler.host = host
    Handler.port = int(port)
    return Handler


def serve_studio_app_launcher(
    vault_root: str | Path,
    *,
    host: str = _DEFAULT_HOST,
    port: int = _DEFAULT_PORT,
) -> None:
    """Serve the Studio App Launcher on a loopback interface."""

    _require_loopback(host)
    handler = make_studio_app_launcher_handler(vault_root, host=host, port=port)
    server = ThreadingHTTPServer((host, int(port)), handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()
