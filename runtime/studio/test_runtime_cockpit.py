"""Tests for the Studio Runtime Cockpit contract model."""

from __future__ import annotations

from pathlib import Path
from threading import Event
from time import monotonic

from runtime.studio import runtime_cockpit


def _startup_model() -> dict:
    return {
        "ok": True,
        "surface": "studio_runtime_startup_controls",
        "runtime_count": 1,
        "surface_count": 1,
        "mutation_actions_enabled": True,
        "approval_boundary": {
            "approval_required_before_confirmed_mutation": True,
            "executor_enabled_now": False,
        },
        "surface_cards": [
            {
                "runtime_id": "hermes",
                "runtime_name": "Hermes",
                "surface_id": "gateway",
                "ui_label": "Hermes Gateway",
                "current_state": "registered",
                "target_states": {"enable": "registered", "disable": "off"},
                "user_manageable": True,
                "studio_control_enabled": True,
                "studio_visual_toggle_built": True,
                "requires_confirm_action": True,
                "startup_registration_kind": "windows-startup-folder",
                "launch_profile": {"launch_kind": "wsl", "wsl_distro": "Ubuntu"},
                "commands": {
                    "enable": {
                        "studio_preview": "chaseos studio runtime-startup-controls --runtime hermes --surface gateway --intent enable --action dry-run --json",
                        "studio_toggle": "chaseos studio runtime-startup-controls --runtime hermes --surface gateway --intent enable --action toggle --confirm-action",
                    },
                    "disable": {
                        "studio_preview": "chaseos studio runtime-startup-controls --runtime hermes --surface gateway --intent disable --action dry-run --json",
                        "studio_toggle": "chaseos studio runtime-startup-controls --runtime hermes --surface gateway --intent disable --action toggle --confirm-action",
                    },
                },
                "approval_readiness": {
                    "enable": {
                        "approval_required": True,
                        "approval_artifact": {"status": "missing"},
                        "executor_readiness": {"executor_enabled_now": False},
                        "success_marker_evidence_verifier": {"verifier_status": "blocked"},
                    },
                    "disable": {
                        "approval_required": True,
                        "approval_artifact": {"status": "missing"},
                        "executor_readiness": {"executor_enabled_now": False},
                        "success_marker_evidence_verifier": {"verifier_status": "blocked"},
                    },
                },
            }
        ],
    }


def test_runtime_cockpit_contract_aggregates_existing_service_models(monkeypatch, tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        runtime_cockpit,
        "get_dashboard",
        lambda vault_root, *, probe_child_apps=True: {
            "ok": True,
            "surface": "studio_dashboard",
            "runtime_startup_panel": {},
            "app_launcher_panel": {},
            "panel_errors": [],
        },
    )

    def fake_startup(vault_root, runtime_id=None):
        captured["runtime_id"] = runtime_id
        return _startup_model()

    monkeypatch.setattr(runtime_cockpit, "build_runtime_startup_controls_model", fake_startup)
    monkeypatch.setattr(
        runtime_cockpit,
        "build_studio_app_launcher_plan",
        lambda vault_root, *, host="127.0.0.1", port=8769, probe_health=True: {
            "ok": True,
            "surface": "studio_app_launcher_local_app",
            "app_count": 2,
            "authority": {"read_only": True, "starts_child_apps": False},
            "apps": [
                {
                    "id": "runtime-cockpit-app",
                    "title": "Runtime Cockpit",
                    "command": "chaseos studio runtime-cockpit-app",
                    "status": "available",
                    "default_url": "http://127.0.0.1:8771/",
                    "read_only": True,
                    "write_capable": False,
                    "requires_confirmation_for_writes": False,
                    "runtime_status": {"state": "offline"},
                },
                {
                    "id": "runtime-startup-controls-app",
                    "title": "Runtime Startup Controls",
                    "command": "chaseos studio runtime-startup-controls-app",
                    "status": "available",
                    "default_url": "http://127.0.0.1:8766/",
                    "read_only": False,
                    "write_capable": True,
                    "requires_confirmation_for_writes": True,
                    "runtime_status": {"state": "offline"},
                }
            ],
        },
    )

    model = runtime_cockpit.build_runtime_cockpit_contract(vault, runtime_id="hermes")

    assert model["ok"] is True
    assert model["surface"] == "studio_runtime_cockpit_contract"
    assert model["status"] == "contract_ready_local_mount_built_studio_shell_mvp_built"
    assert model["desktop"]["contract_model_built"] is True
    assert model["desktop"]["desktop_runtime_cockpit_built"] is True
    assert model["desktop"]["desktop_runtime_cockpit_native_panel_built"] is True
    assert model["desktop"]["native_panel_mounted"] is True
    assert model["desktop"]["studio_shell_mvp_built"] is True
    assert model["desktop"]["studio_shell_mvp_command"] == "chaseos studio desktop-shell-app --dry-run --json"
    assert model["desktop"]["local_app_built"] is True
    assert model["desktop"]["local_app_url"] == "http://127.0.0.1:8771/"
    assert captured["runtime_id"] == "hermes"
    assert model["runtime_startup"]["surface_count"] == 1
    assert model["runtime_startup"]["manageable_surface_count"] == 1
    assert model["runtime_startup"]["readiness_summary"]["readiness_packet_count"] == 2
    assert model["runtime_startup"]["readiness_summary"]["host_mutation_allowed_now"] is False
    card = model["runtime_startup"]["cards"][0]
    assert card["runtime_id"] == "hermes"
    assert card["launch_profile"]["launch_kind"] == "wsl"
    assert "--confirm-action" in card["commands"]["disable_toggle"]
    assert model["boundary"]["writes_host_startup"] is False
    assert model["boundary"]["starts_studio_child_apps"] is False
    assert model["boundary"]["starts_runtimes"] is False
    assert model["boundary"]["executes_runtime_actions"] is False
    assert model["integration_contract"]["desktop_shell_mount"] == "NATIVE-PANEL-MOUNTED"
    assert model["integration_contract"]["native_runtime_cockpit_panel"] == "MOUNTED-READ-ONLY"
    assert model["integration_contract"]["logs_and_audit_panel"] == "READ-ONLY-EXPANDED"
    assert model["integration_contract"]["full_desktop_shell"] == "PLANNED"
    assert model["runtime_health"]["status"] == "read-only-visible"
    assert model["coordination_watch"]["opens_watch_loops"] is False
    assert model["startup_drift"]["live_toggle_blocked_until_governed_executor"] is True
    assert model["logs_and_audit"]["writes_audit_logs"] is False
    assert model["post_reboot"]["writes_bootstrap_state"] is False
    assert model["readiness"]["runtime_cockpit_native_panel_mounted"] is True
    assert model["readiness"]["no_start_stop_restart_authority"] is True
    assert {surface["id"] for surface in model["available_surfaces"]} >= {
        "studio-runtime-cockpit-contract",
        "runtime-cockpit-app",
        "runtime-startup-controls-app",
    }


def test_runtime_cockpit_contract_is_fail_open(monkeypatch, tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    def broken_dashboard(vault_root, *, probe_child_apps=True):
        raise RuntimeError("dashboard unavailable")

    monkeypatch.setattr(runtime_cockpit, "get_dashboard", broken_dashboard)
    monkeypatch.setattr(runtime_cockpit, "build_runtime_startup_controls_model", lambda vault_root, runtime_id=None: _startup_model())
    monkeypatch.setattr(
        runtime_cockpit,
        "build_studio_app_launcher_plan",
        lambda vault_root, *, host="127.0.0.1", port=8769, probe_health=True: {"ok": True, "surface": "studio_app_launcher_local_app", "apps": []},
    )

    model = runtime_cockpit.build_runtime_cockpit_contract(vault)

    assert model["ok"] is True
    assert model["status"] == "contract_ready_local_mount_built_with_panel_errors_studio_shell_mvp_built"
    assert model["errors"] == ["dashboard: dashboard unavailable"]


def test_runtime_cockpit_contract_surfaces_live_lifecycle_runtime_truth(monkeypatch, tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    lifecycle = vault / "runtime" / "lifecycle"
    lifecycle.mkdir(parents=True)
    (lifecycle / "hermes.lifecycle.yaml").write_text(
        """
runtime_id: hermes
platform: wsl
lifecycle_mode: wsl-process
coordination_watch:
  runtime_name: Hermes
health:
  kind: http
  probe_label: hermes-local-http
  candidate_ports:
    - 18790
ownership: chaseos-managed-runtime-lane
""".strip(),
        encoding="utf-8",
    )
    (lifecycle / "openclaw.lifecycle.yaml").write_text(
        """
runtime_id: openclaw
platform: windows
lifecycle_mode: windows-process
coordination_watch:
  runtime_name: OpenClaw
health:
  kind: heartbeat
ownership: chaseos-managed-runtime-lane
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        runtime_cockpit,
        "get_dashboard",
        lambda vault_root, *, probe_child_apps=True: {"ok": True, "surface": "studio_dashboard", "panel_errors": []},
    )
    monkeypatch.setattr(
        runtime_cockpit,
        "build_runtime_startup_controls_model",
        lambda vault_root, runtime_id=None: {
            "ok": True,
            "surface": "studio_runtime_startup_controls",
            "runtime_count": 0,
            "surface_count": 0,
            "surface_cards": [],
        },
    )
    monkeypatch.setattr(
        runtime_cockpit,
        "build_studio_app_launcher_plan",
        lambda vault_root, *, host="127.0.0.1", port=8769, probe_health=True: {"ok": True, "surface": "studio_app_launcher_local_app", "apps": []},
    )

    def fake_check_health(runtime_id: str, timeout_seconds: int = 5, vault_root=None):
        assert vault_root == vault.resolve()
        if runtime_id == "hermes":
            return {
                "runtime_id": "hermes",
                "status": "healthy",
                "healthy": True,
                "detected_url": "http://127.0.0.1:18790/",
                "probe_label": "hermes-local-http",
                "candidate_ports": [18790],
                "blocked_reason": None,
                "errors": [],
            }
        return {
            "runtime_id": runtime_id,
            "status": "unavailable",
            "healthy": False,
            "blocked_reason": "heartbeat_stale",
            "errors": [{"code": "heartbeat_stale", "message": "heartbeat_stale"}],
        }

    monkeypatch.setattr(runtime_cockpit, "check_health", fake_check_health, raising=False)

    model = runtime_cockpit.build_runtime_cockpit_contract(vault, service_timeout_seconds=1.0)

    health = model["runtime_health"]
    assert health["runtime_profile_count"] == 2
    assert health["live_runtime_count"] == 1
    assert health["blocked_runtime_count"] == 1
    profiles = {profile["runtime_id"]: profile for profile in health["profiles"]}
    assert profiles["hermes"]["runtime_name"] == "Hermes"
    assert profiles["hermes"]["status"] == "live"
    assert profiles["hermes"]["detected_url"] == "http://127.0.0.1:18790/"
    assert profiles["hermes"]["authority_ceiling"] == "chaseos-managed-runtime-lane"
    assert profiles["openclaw"]["runtime_name"] == "OpenClaw"
    assert profiles["openclaw"]["status"] == "blocked"
    assert profiles["openclaw"]["blocked_reason"] == "heartbeat_stale"
    cards = {card["runtime_id"]: card for card in model["runtime_startup"]["cards"]}
    assert cards["hermes"]["surface_id"] == "runtime-profile"
    assert cards["hermes"]["health_status"] == "live"
    assert cards["hermes"]["blocked_reason"] is None
    assert cards["openclaw"]["health_status"] == "blocked"
    assert cards["openclaw"]["blocked_reason"] == "heartbeat_stale"


def test_runtime_cockpit_contract_prefers_read_only_process_evidence_when_http_probe_times_out(monkeypatch, tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    lifecycle = vault / "runtime" / "lifecycle"
    lifecycle.mkdir(parents=True)
    (lifecycle / "hermes.lifecycle.yaml").write_text(
        """
runtime_id: hermes
platform: wsl
lifecycle_mode: wsl-process
coordination_watch:
  runtime_name: Hermes
start:
  kind: command
  command: hermes gateway
health:
  kind: http
  probe_label: hermes-local-http
  urls:
    - http://127.0.0.1:18790/
ownership: chaseos-managed-runtime-lane
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        runtime_cockpit,
        "check_health",
        lambda runtime_id, timeout_seconds=5, vault_root=None: {
            "runtime_id": runtime_id,
            "status": "unknown",
            "healthy": False,
            "timed_out": True,
            "blocked_reason": "health_probe_timeout",
            "errors": [{"code": "health_probe_timeout", "message": "bounded Runtime Cockpit probe timed out"}],
        },
    )
    monkeypatch.setattr(
        runtime_cockpit,
        "_list_runtime_processes",
        lambda runtime_id, record: [
            {"pid": 959, "command": "<WSL_HOME>/.local/bin/hermes gateway"},
            {"pid": 53394, "command": "<WSL_HOME>/.local/bin/hermes -p ops chat"},
        ],
    )

    health = runtime_cockpit._runtime_health(
        vault,
        health_probe_timeout_seconds=0.01,
        probe_processes=True,
    )

    assert health["runtime_profile_count"] == 1
    assert health["live_runtime_count"] == 1
    profile = health["profiles"][0]
    assert profile["runtime_id"] == "hermes"
    assert profile["status"] == "live"
    assert profile["health_status"] == "process-live"
    assert profile["blocked_reason"] is None
    assert profile["evidence"]["process_count"] == 2
    assert profile["evidence"]["process_probe"] == "wsl-read-only-ps"
    assert any(item["source"] == "process" for item in profile["evidence"]["evidence_sources"])


def test_runtime_cockpit_health_does_not_probe_processes_by_default(
    tmp_path: Path,
    monkeypatch,
) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    lifecycle = vault / "runtime" / "lifecycle"
    lifecycle.mkdir(parents=True)
    (lifecycle / "hermes.lifecycle.yaml").write_text(
        "\n".join(
            [
                "runtime_id: hermes",
                "runtime_name: Hermes",
                "platform: wsl",
                "lifecycle_mode: wsl-process",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        runtime_cockpit,
        "check_health",
        lambda runtime_id, timeout_seconds=5, vault_root=None: {
            "runtime_id": runtime_id,
            "status": "unknown",
            "healthy": False,
            "timed_out": True,
            "blocked_reason": "health_probe_timeout",
        },
    )

    def fail_process_probe(*_args, **_kwargs):
        raise AssertionError("Runtime Cockpit page load must not spawn host process probes")

    monkeypatch.setattr(runtime_cockpit, "_list_runtime_processes", fail_process_probe)

    health = runtime_cockpit._runtime_health(vault, health_probe_timeout_seconds=0.01)

    assert health["host_process_probe_enabled"] is False
    assert health["profiles"][0]["health_status"] == "unknown"


def test_runtime_cockpit_process_probe_uses_hidden_window_flag(monkeypatch) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(runtime_cockpit.os, "name", "nt", raising=False)
    monkeypatch.setattr(runtime_cockpit.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)

    def fake_run(args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return runtime_cockpit.subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(runtime_cockpit.subprocess, "run", fake_run)

    result = runtime_cockpit._list_runtime_processes(
        "hermes",
        {
            "platform": "wsl",
            "lifecycle_mode": "wsl-process",
            "coordination_watch": {"runtime_name": "Hermes"},
        },
    )

    assert result == []
    assert captured["args"] == ["ps", "-eo", "pid=,comm=,args="]
    assert captured["kwargs"]["creationflags"] == 0x08000000


def test_runtime_cockpit_contract_bounds_heavy_service_models(monkeypatch, tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    never_finishes = Event()

    def slow_dashboard(*args, **kwargs) -> dict:
        never_finishes.wait(5)
        return {"ok": True}

    monkeypatch.setattr(runtime_cockpit, "get_dashboard", slow_dashboard)
    monkeypatch.setattr(runtime_cockpit, "build_runtime_startup_controls_model", lambda *args, **kwargs: _startup_model())
    monkeypatch.setattr(
        runtime_cockpit,
        "build_studio_app_launcher_plan",
        lambda *args, **kwargs: {"ok": True, "surface": "studio_app_launcher_local_app", "apps": []},
    )

    started = monotonic()
    model = runtime_cockpit.build_runtime_cockpit_contract(vault, service_timeout_seconds=0.01)
    elapsed = monotonic() - started

    assert elapsed < 2.0
    assert model["ok"] is True
    assert "dashboard: timed out after 0.01s" in model["errors"]
    assert model["studio_dashboard"]["source_surface"] is None
    assert model["boundary"]["executes_runtime_actions"] is False


def test_runtime_cockpit_zero_budget_does_not_start_heavy_service_models(monkeypatch, tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    def forbidden_service(*args, **kwargs) -> dict:
        raise AssertionError("zero-budget Runtime Cockpit smoke must not start heavy services")

    monkeypatch.setattr(runtime_cockpit, "get_dashboard", forbidden_service)
    monkeypatch.setattr(runtime_cockpit, "build_runtime_startup_controls_model", forbidden_service)
    monkeypatch.setattr(runtime_cockpit, "build_studio_app_launcher_plan", forbidden_service)

    model = runtime_cockpit.build_runtime_cockpit_contract(vault, service_timeout_seconds=0.0)

    assert model["ok"] is True
    assert "dashboard: timed out after 0s" in model["errors"]
    assert "runtime_startup_controls: timed out after 0s" in model["errors"]
    assert "app_launcher: timed out after 0s" in model["errors"]
    assert model["boundary"]["starts_runtimes"] is False
