"""Tests for the read-only Studio App Launcher / Discovery Registry."""

from __future__ import annotations

import http.client
import json
from pathlib import Path
import threading
from http.server import ThreadingHTTPServer
from urllib.error import URLError

import pytest

from runtime.studio import app_launcher
from runtime.studio.app_launcher import (
    StudioAppLauncherError,
    build_studio_app_launcher_plan,
    render_studio_app_launcher_html,
)


def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    (vault / "runtime" / "studio").mkdir(parents=True)
    (vault / "07_LOGS" / "Agent-Activity").mkdir(parents=True)
    return vault


def test_launcher_registry_is_local_only_read_only_and_lists_known_apps(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)

    plan = build_studio_app_launcher_plan(vault)

    assert plan["ok"] is True
    assert plan["surface"] == "studio_app_launcher_local_app"
    assert plan["local_only"] is True
    assert plan["authority"]["binds_loopback_only"] is True
    assert plan["authority"]["read_only"] is True
    assert plan["authority"]["starts_child_apps"] is False
    assert plan["authority"]["workflow_execution_allowed"] is False
    assert plan["allowed_actions"] == []
    assert plan["possible_writes"] == []
    assert plan["health_probe"] == {
        "enabled": True,
        "read_only": True,
        "starts_child_apps": False,
        "timeout_seconds": 0.2,
    }

    apps = {entry["id"]: entry for entry in plan["apps"]}
    assert len(apps) == len(plan["apps"])
    assert set(apps) >= {
        "studio-dashboard-app",
        "studio-app-launcher",
        "vincisos-product-ui-test-target",
        "runtime-cockpit-app",
        "studio-desktop-shell-app",
        "approval-center-app",
    }
    assert {entry["default_port"] for entry in apps.values()} >= {8768, 8769, 8770, 8771, 8772, 8773}
    assert apps["studio-app-launcher"]["command"] == "chaseos studio app-launcher"
    assert apps["studio-app-launcher"]["default_port"] == 8769
    assert apps["studio-app-launcher"]["read_only"] is True
    assert apps["studio-app-launcher"]["write_capable"] is False
    assert apps["studio-app-launcher"]["runtime_status"]["starts_child_app"] is False
    assert apps["approval-center-app"]["command"] == "chaseos studio approval-center-app"
    assert apps["approval-center-app"]["default_port"] == 8773
    assert apps["approval-center-app"]["approval_center_mount"] is True
    assert apps["approval-center-app"]["read_only"] is True
    assert apps["approval-center-app"]["write_capable"] is False
    assert apps["vincisos-product-ui-test-target"]["command"] == "chaseos studio product-ui-test-app"
    assert apps["vincisos-product-ui-test-target"]["browser_proof_target"] is True
    assert apps["vincisos-product-ui-test-target"]["target_family"] == "vincisos-product-ui browser-runtime-product-target"
    assert apps["vincisos-product-ui-test-target"]["default_port"] == 8770
    assert apps["vincisos-product-ui-test-target"]["read_only"] is True
    assert apps["vincisos-product-ui-test-target"]["write_capable"] is False
    assert apps["studio-desktop-shell-app"]["command"] == "chaseos studio desktop-shell-app"
    assert apps["studio-desktop-shell-app"]["default_port"] == 8772
    assert apps["studio-desktop-shell-app"]["studio_shell_mvp"] is True
    assert apps["studio-desktop-shell-app"]["runtime_cockpit_mount"] is True
    assert apps["studio-desktop-shell-app"]["read_only"] is True
    assert apps["studio-desktop-shell-app"]["write_capable"] is False
    assert apps["studio-dashboard-app"]["command"] == "chaseos studio dashboard-app"
    assert apps["studio-dashboard-app"]["read_only"] is True
    assert apps["runtime-cockpit-app"]["command"] == "chaseos studio runtime-cockpit-app"
    assert apps["runtime-cockpit-app"]["default_port"] == 8771
    assert apps["runtime-cockpit-app"]["read_only"] is True
    assert apps["runtime-cockpit-app"]["write_capable"] is False
    assert apps["runtime-cockpit-app"]["requires_confirmation_for_writes"] is False
    assert all(entry["write_capable"] is False for entry in apps.values())
    assert all(entry["local_only"] is True for entry in apps.values())
    assert all(entry["runtime_status"]["checked"] is True for entry in apps.values())
    assert all(entry["runtime_status"]["starts_child_app"] is False for entry in apps.values())
    assert {entry["runtime_status"]["state"] for entry in apps.values()} <= {"reachable", "offline", "broken"}
    assert apps["studio-dashboard-app"]["operator_launch"] == {
        "execution_mode": "operator_terminal_only",
        "copyable": True,
        "launcher_executes": False,
        "browser_auto_open": False,
        "command": "chaseos studio dashboard-app --host 127.0.0.1 --port 8768",
        "health_command": "curl -fsS --max-time 2 http://127.0.0.1:8768/health.json",
        "open_url_command": "Open http://127.0.0.1:8768/ in your browser after health is reachable.",
        "health_url": "http://127.0.0.1:8768/health.json",
        "default_url": "http://127.0.0.1:8768/",
    }
    assert apps["vincisos-product-ui-test-target"]["operator_launch"]["command"] == (
        "chaseos studio product-ui-test-app --host 127.0.0.1 --port 8770"
    )
    assert all(entry["operator_launch"]["launcher_executes"] is False for entry in apps.values())


def test_launcher_lists_observed_support_ports_without_starting_processes(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)

    plan = build_studio_app_launcher_plan(vault, probe_health=False)

    support_ports = {entry["port"]: entry for entry in plan["support_ports"]}
    assert set(support_ports) >= {8780, 8781, 9119, 11434, 9222, 4173, 3002, 8787, 8788, 8789}
    assert support_ports[8780]["id"] == "current-session-override-shell"
    assert support_ports[8781]["id"] == "static-artifact-server"
    assert support_ports[9119]["id"] == "hermes-kanban-dashboard"
    assert support_ports[11434]["id"] == "ollama-local-models"
    assert support_ports[9222]["id"] == "chrome-cdp"
    assert all(entry["runtime_status"]["starts_child_app"] is False for entry in support_ports.values())
    assert all(entry["operator_launch"]["launcher_executes"] is False for entry in support_ports.values())
    assert all(entry["read_only_probe"] is True for entry in support_ports.values())


def test_launcher_support_port_probe_reports_reachable_and_offline(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)

    class _Response:
        status = 204

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(request, timeout: float):
        if request.full_url == "http://127.0.0.1:9119/health.json":
            return _Response()
        raise URLError("offline")

    monkeypatch.setattr(app_launcher.request, "urlopen", fake_urlopen)

    plan = build_studio_app_launcher_plan(vault)
    support_ports = {entry["port"]: entry for entry in plan["support_ports"]}

    assert support_ports[9119]["runtime_status"]["state"] == "reachable"
    assert support_ports[9119]["runtime_status"]["http_status"] == 204
    assert support_ports[9222]["runtime_status"]["state"] == "offline"
    assert support_ports[9222]["runtime_status"]["starts_child_app"] is False


def test_launcher_server_marks_current_launcher_reachable_without_recursive_self_probe(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    vault = _make_vault(tmp_path)
    requested_urls: list[str] = []

    def fake_urlopen(request, timeout: float):
        requested_urls.append(request.full_url)
        raise URLError("offline")

    monkeypatch.setattr(app_launcher.request, "urlopen", fake_urlopen)

    plan = build_studio_app_launcher_plan(vault, current_launcher_running=True)
    apps = {entry["id"]: entry for entry in plan["apps"]}

    assert "http://127.0.0.1:8769/health.json" not in requested_urls
    assert apps["studio-app-launcher"]["runtime_status"]["checked"] is True
    assert apps["studio-app-launcher"]["runtime_status"]["state"] == "reachable"
    assert apps["studio-app-launcher"]["runtime_status"]["health_url"] == "http://127.0.0.1:8769/health.json"
    assert apps["studio-app-launcher"]["runtime_status"]["http_status"] == 200
    assert apps["studio-app-launcher"]["runtime_status"]["starts_child_app"] is False
    assert apps["studio-app-launcher"]["runtime_status"]["read_only_probe"] is True
    assert apps["studio-app-launcher"]["runtime_status"]["reason"] == "current_launcher_server"
    assert apps["studio-app-launcher"]["runtime_status"]["last_checked"].endswith("Z")


def test_launcher_health_endpoint_is_fast_self_health_without_child_probes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    vault = _make_vault(tmp_path)
    requested_urls: list[str] = []

    def fake_urlopen(request, timeout: float):
        requested_urls.append(request.full_url)
        raise AssertionError("/health.json must not probe child or support ports")

    monkeypatch.setattr(app_launcher.request, "urlopen", fake_urlopen)
    handler = app_launcher.make_studio_app_launcher_handler(vault, host="127.0.0.1", port=0)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=2)
        conn.request("GET", "/health.json")
        response = conn.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
        conn.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert response.status == 200
    assert requested_urls == []
    assert payload["ok"] is True
    assert payload["self_health"]["fast_path"] is True
    assert payload["health_probe"]["enabled"] is False
    assert payload["app_count"] >= 6
    assert payload["support_port_count"] >= 10
    assert all(entry["runtime_status"]["checked"] is False for entry in payload["apps"])
    assert all(entry["runtime_status"]["checked"] is False for entry in payload["support_ports"])


def test_launcher_health_probe_reports_reachable_without_starting_child_apps(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    requested_urls: list[str] = []

    class _Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(request, timeout: float):
        requested_urls.append(request.full_url)
        if request.full_url == "http://127.0.0.1:8768/health.json":
            return _Response()
        raise URLError("offline")

    monkeypatch.setattr(app_launcher.request, "urlopen", fake_urlopen)

    plan = build_studio_app_launcher_plan(vault)
    apps = {entry["id"]: entry for entry in plan["apps"]}

    assert requested_urls == [
        "http://127.0.0.1:8773/health.json",
        "http://127.0.0.1:8770/health.json",
        "http://127.0.0.1:8772/health.json",
        "http://127.0.0.1:8768/health.json",
        "http://127.0.0.1:8771/health.json",
        "http://127.0.0.1:8769/health.json",
        "http://127.0.0.1:8780/health.json",
        "http://127.0.0.1:8781/health.json",
        "http://127.0.0.1:9119/health.json",
        "http://127.0.0.1:11434/api/tags",
        "http://127.0.0.1:9222/json/version",
        "http://127.0.0.1:4173/",
        "http://127.0.0.1:3002/",
        "http://127.0.0.1:8787/health.json",
        "http://127.0.0.1:8788/health.json",
        "http://127.0.0.1:8789/health.json",
    ]
    assert apps["studio-dashboard-app"]["runtime_status"]["state"] == "reachable"
    assert apps["studio-dashboard-app"]["runtime_status"]["http_status"] == 200
    assert apps["approval-center-app"]["runtime_status"]["state"] == "offline"


def test_launcher_rejects_non_loopback_host(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)

    with pytest.raises(StudioAppLauncherError, match="loopback"):
        build_studio_app_launcher_plan(vault, host="0.0.0.0")


def test_launcher_liveness_model_distinguishes_registered_offline_reachable_and_broken(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    vault = _make_vault(tmp_path)

    class _Response:
        def __init__(self, status: int):
            self.status = status

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(request, timeout: float):
        if request.full_url == "http://127.0.0.1:8768/health.json":
            return _Response(200)
        if request.full_url == "http://127.0.0.1:8771/health.json":
            return _Response(503)
        raise URLError("offline")

    monkeypatch.setattr(app_launcher.request, "urlopen", fake_urlopen)

    plan = build_studio_app_launcher_plan(vault)
    apps = {entry["id"]: entry for entry in plan["apps"]}

    assert plan["status_legend"] == {
        "registered": "Declared in the Studio app registry; this is inventory, not liveness.",
        "offline": "Registered but no local health endpoint answered; launch manually if needed.",
        "reachable": "Registered and the local status probe answered without the launcher starting it.",
        "broken": "Registered and reachable enough to answer, but health returned an error status.",
        "not_checked": "Probe disabled for this response; no liveness conclusion was attempted.",
    }
    assert plan["liveness_counts"]["registered"] == 6
    assert plan["liveness_counts"]["reachable"] == 1
    assert plan["liveness_counts"]["broken"] == 1
    assert plan["liveness_counts"]["offline"] == 4
    assert apps["studio-dashboard-app"]["registration_status"] == "registered"
    assert apps["studio-dashboard-app"]["runtime_status"]["state"] == "reachable"
    assert apps["studio-dashboard-app"]["liveness_label"] == "Registered app · Reachable"
    assert apps["runtime-cockpit-app"]["runtime_status"]["state"] == "broken"
    assert apps["runtime-cockpit-app"]["runtime_status"]["http_status"] == 503
    assert apps["runtime-cockpit-app"]["liveness_label"] == "Registered app · Broken"
    assert apps["approval-center-app"]["runtime_status"]["state"] == "offline"
    assert apps["approval-center-app"]["liveness_label"] == "Registered app · Offline"
    assert all(entry["operator_launch"]["copyable"] is True for entry in apps.values())
    assert plan["support_port_group"] == {
        "title": "Advanced / Support ports",
        "advanced": True,
        "collapsed_by_default": True,
        "reason": "Support ports are noisy diagnostics, not primary Studio apps.",
    }


def test_launcher_plan_exposes_user_facing_actions_and_last_checked(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)

    plan = build_studio_app_launcher_plan(vault)
    apps = {entry["id"]: entry for entry in plan["apps"]}

    for app in apps.values():
        status = app["runtime_status"]
        assert status["checked"] is True
        assert status["last_checked"]
        assert status["state"] in {"reachable", "offline", "broken"}
        actions = {action["id"]: action for action in app["actions"]}
        assert set(actions) == {"open", "start_request", "health", "authority"}
        assert actions["open"]["kind"] == "link"
        assert actions["open"]["href"] == app["default_url"]
        assert actions["health"]["kind"] == "link"
        assert actions["health"]["href"] == status["health_url"]
        assert actions["authority"]["kind"] == "disclosure"
        assert actions["start_request"]["kind"] == "confirmation_gated_request"
        assert actions["start_request"]["executes_in_launcher"] is False
        assert actions["start_request"]["requires_confirmation"] is True
        assert actions["start_request"]["approved_backend_contract_only"] is True
        assert "command" not in actions["start_request"]

    assert all(entry["actions"][1]["write_capable"] is False for entry in apps.values())
    assert apps["studio-dashboard-app"]["actions"][1]["write_capable"] is False


def test_launcher_html_renders_app_cards_and_boundaries(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    plan = build_studio_app_launcher_plan(vault)

    html = render_studio_app_launcher_html(plan)

    assert "ChaseOS Studio App Launcher" in html
    assert "ChaseOS Pulse Approval Center" in html
    assert "ChaseOS Studio Product UI Test Target" in html
    assert "ChaseOS Studio Shell" in html
    assert "Studio Home" in html
    assert "Agents / Runtimes" in html
    assert "chaseos studio app-launcher --host 127.0.0.1 --port 8769" in html
    assert "chaseos studio dashboard-app" in html
    assert "chaseos studio runtime-cockpit-app" in html
    assert "chaseos studio desktop-shell-app" in html
    assert "chaseos studio approval-center-app" in html
    assert "chaseos studio product-ui-test-app" in html
    assert "Open" in html
    assert "Launch Guide" in html
    assert "Health" in html
    assert "Authority" in html
    assert "Description" in html
    assert "Port" in html
    assert "Status" in html
    assert "Last Checked" in html
    assert "Manual launch guide" in html
    assert "Launch command" in html
    assert "Health check" in html
    assert "Registered app · Offline" in html
    assert "Advanced / Support ports" in html
    assert "Support ports are noisy diagnostics" in html
    assert "class=\"panel advanced-support\"" in html
    assert "chaseos studio dashboard-app --host 127.0.0.1 --port 8768" in html
    assert "curl -fsS --max-time 2 http://127.0.0.1:8768/health.json" in html
    assert "chaseos studio runtime-cockpit-app --host 127.0.0.1 --port 8771" in html
    assert "chaseos studio desktop-shell-app --host 127.0.0.1 --port 8772" in html
    assert "data-confirmation-required=\"true\"" in html
    assert "data-executes-in-launcher=\"false\"" in html
    assert "No provider, browser, delivery, scheduler, or canonical writeback authority" in html
    assert "<script" not in html.lower()
