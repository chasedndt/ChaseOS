"""Startup surface declaration/report tests for ChaseOS runtime lifecycle."""

from __future__ import annotations

from runtime.lifecycle import startup_surfaces


def _startup_toggle_test_dir(name: str) -> "startup_surfaces.Path":
    path = startup_surfaces.ROOT / ".pytest-tmp" / "startup-surface-toggle-tests" / name
    if path.exists():
        for child in sorted(path.rglob("*"), reverse=True):
            if child.is_file() or child.is_symlink():
                child.unlink()
            else:
                child.rmdir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _surfaces_by_id(report: dict) -> dict[str, dict]:
    return {surface["surface_id"]: surface for surface in report["surfaces"]}


def test_lifecycle_records_declare_startup_surfaces_for_studio():
    openclaw = startup_surfaces.load_startup_surfaces_config("openclaw")
    hermes = startup_surfaces.load_startup_surfaces_config("hermes")

    for runtime_surfaces in [openclaw, hermes]:
        assert set(runtime_surfaces) >= {
            "gateway",
            "coordination_watch_supervisor",
            "coordination_watch_bootstrap",
        }
        for surface in runtime_surfaces.values():
            assert surface["supported"] is True
            assert surface["toggle_supported"] is True
            assert surface["mutation_status"] == "studio-local-app-built-approval-artifacts-built-host-executor-pending"

    assert hermes["gateway"]["launcher_path"].endswith("Hermes Gateway.cmd")
    assert openclaw["gateway"]["launcher_path"].endswith("OpenClaw Gateway.cmd")
    assert hermes["gateway"]["path_resolution"] == "dynamic-user"
    assert openclaw["gateway"]["path_resolution"] == "dynamic-user"
    assert "{windows_userprofile}" in hermes["gateway"]["target_path"]
    assert "{windows_userprofile}" in openclaw["gateway"]["target_path"]
    assert "C:\\Users\\chaseos" not in openclaw["gateway"]["launcher_path"]
    assert "C:\\Users\\chaseos" not in openclaw["gateway"]["target_path"]
    assert hermes["gateway"]["launch_kind"] == "wsl"
    assert hermes["gateway"]["wsl_distro"] == "Ubuntu"
    assert hermes["gateway"]["wsl_user"] == ""
    assert hermes["gateway"]["wsl_workdir"] == "{wsl_vault_path}"
    assert "HERMES_HOME" in hermes["gateway"]["wsl_command"]
    assert "${HOME}/runtimes/hermes-home" in hermes["gateway"]["wsl_command"]
    assert "${HOME}/.local/bin/hermes gateway run" in hermes["gateway"]["wsl_command"]
    assert int(hermes["gateway"]["retry_attempts"]) >= 2


def test_hermes_managed_gateway_launcher_is_idempotent():
    config = startup_surfaces.load_startup_surfaces_config("hermes")["gateway"]
    contents = startup_surfaces._gateway_target_launcher_contents(config)

    assert contents is not None
    assert "HERMES_DAEMON_PROBE" in contents
    assert "$_.ProcessId -ne $PID" in contents
    assert "hermes-daemon-loop.cmd" in contents
    assert "Hermes daemon already running" in contents
    assert 'pgrep -af "hermes gateway run"' in contents
    assert "Hermes gateway already running" in contents
    assert "HERMES_WSL_USER_ARG" in contents
    assert "exec ${HOME}/.local/bin/hermes gateway run" in contents
    assert "--runtime hermes --daemon-interval 30 --vault-root" in contents
    assert "--synthesize" in contents
    assert "<WSL_HOME>/.local/bin/hermes" not in contents


def test_dynamic_gateway_config_resolves_current_host_without_launching_wsl(monkeypatch, tmp_path):
    monkeypatch.setenv("USERPROFILE", "C:\\Users\\alice")
    monkeypatch.setenv("APPDATA", "C:\\Users\\alice\\AppData\\Roaming")
    monkeypatch.setenv("CHASEOS_HERMES_WSL_DISTRO", "Ubuntu-24.04")
    monkeypatch.delenv("CHASEOS_HERMES_WSL_USER", raising=False)
    config = {
        "path_resolution": "dynamic-user",
        "current_state_source": "host_startup_file",
        "launcher_path": "{windows_startup_dir}\\Hermes Gateway.cmd",
        "target_path": "{windows_userprofile}\\.hermes\\gateway.cmd",
        "wsl_distro": "Ubuntu",
        "wsl_user": "",
        "wsl_workdir": "{wsl_vault_path}",
        "wsl_command": "export HERMES_HOME=${CHASEOS_HERMES_HOME:-${HERMES_HOME:-${HOME}/runtimes/hermes-home}} && exec ${HOME}/.local/bin/hermes gateway run",
        "diagnostic_log_path": "{windows_userprofile}\\.hermes\\gateway-startup.log",
    }

    resolved = startup_surfaces.resolve_gateway_surface_config(config, tmp_path)

    assert resolved["launcher_path"] == "C:\\Users\\alice\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\Hermes Gateway.cmd"
    assert resolved["target_path"] == "C:\\Users\\alice\\.hermes\\gateway.cmd"
    assert resolved["wsl_distro"] == "Ubuntu-24.04"
    assert resolved["wsl_user"] == ""
    assert resolved["path_resolution_context"]["wsl_user_mode"] == "default-wsl-user"
    assert resolved["path_resolution_context"]["launches_wsl_during_resolution"] is False
    assert resolved["path_resolution_context"]["reads_private_hermes_env"] is False


def test_dynamic_gateway_config_infers_windows_paths_from_wsl_vault_without_env(monkeypatch):
    monkeypatch.delenv("USERPROFILE", raising=False)
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.delenv("CHASEOS_HERMES_WSL_DISTRO", raising=False)
    config = {
        "path_resolution": "dynamic-user",
        "launcher_path": "{windows_startup_dir}\\Hermes Gateway.cmd",
        "target_path": "{windows_userprofile}\\.hermes\\gateway.cmd",
        "windows_vault_path": "{windows_vault_path}",
        "wsl_workdir": "{wsl_vault_path}",
        "wsl_distro": "Ubuntu",
    }

    resolved = startup_surfaces.resolve_gateway_surface_config(
        config,
        startup_surfaces.Path("<VAULT_ROOT>"),
    )

    assert resolved["target_path"] == "C:\\Users\\chaseos\\.hermes\\gateway.cmd"
    assert resolved["launcher_path"].startswith("C:\\Users\\chaseos\\AppData\\Roaming")
    assert resolved["windows_vault_path"] == "C:\\Users\\chaseos\\Documents\\chaseos_obsidian"
    assert resolved["wsl_workdir"] == "<VAULT_ROOT>"
    assert "<WSL_HOME>" not in resolved["target_path"]


def test_runtime_startup_surfaces_report_maps_declared_sources(monkeypatch):
    monkeypatch.setattr(startup_surfaces, "_path_present", lambda raw_path: bool(raw_path))
    monkeypatch.setattr(startup_surfaces, "_gateway_launcher_drift", lambda config: None)
    monkeypatch.setattr(
        startup_surfaces,
        "get_supervised_coordination_watch_status",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "supervision_enabled": True,
            "running": True,
            "stale_state": False,
            "state_present": True,
            "state_file": "runtime/lifecycle/run/hermes-coordination-watch.json",
            "log_file": "runtime/lifecycle/run/hermes-coordination-watch.log",
            "pid": 1234,
            "started_at": "2026-04-30T20:00:00Z",
        },
    )
    monkeypatch.setattr(
        startup_surfaces,
        "build_coordination_watch_activation_report",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "task_name": "ChaseOS-Hermes-Coordination-Watch",
            "registration_kind": "windows-task-scheduler",
            "activation_state": "running",
            "proof_ready": True,
            "proof_complete": False,
            "checks": {
                "installed": True,
                "scheduler_registered": True,
                "supervisor_running": True,
                "heartbeat_fresh": True,
            },
            "activation_proof": {
                "missing_evidence": [],
                "evidence_paths": {
                    "success_record_path": "runtime/lifecycle/run/hermes-coordination-watch-bootstrap-success.json"
                },
            },
        },
    )

    report = startup_surfaces.build_runtime_startup_surfaces_report("hermes")
    surfaces = _surfaces_by_id(report)

    assert report["read_only"] is True
    assert report["mutation_enabled"] is False
    assert surfaces["gateway"]["state"] == "registered"
    assert surfaces["gateway"]["registered"] is True
    assert surfaces["gateway"]["evidence"]["launch_profile"]["wsl_distro"] == "Ubuntu"
    assert surfaces["gateway"]["evidence"]["launch_profile"]["wsl_user"] == ""
    assert surfaces["gateway"]["evidence"]["path_resolution"]["launches_wsl_during_resolution"] is False
    assert surfaces["coordination_watch_supervisor"]["state"] == "running"
    assert surfaces["coordination_watch_bootstrap"]["state"] == "running"


def test_startup_surface_report_can_skip_process_probes_for_passive_page_load(monkeypatch):
    def fail_supervisor_status(runtime_id):
        raise AssertionError("Passive startup surface report must not probe supervised process status")

    def fail_activation_report(runtime_id):
        raise AssertionError("Passive startup surface report must not probe bootstrap activation status")

    monkeypatch.setattr(startup_surfaces, "get_supervised_coordination_watch_status", fail_supervisor_status)
    monkeypatch.setattr(startup_surfaces, "build_coordination_watch_activation_report", fail_activation_report)

    report = startup_surfaces.build_startup_surfaces_report("hermes", probe_processes=False)
    surfaces = _surfaces_by_id(report["runtimes"][0])

    assert report["process_probe_enabled"] is False
    assert report["runtimes"][0]["process_probe_enabled"] is False
    supervisor = surfaces["coordination_watch_supervisor"]
    bootstrap = surfaces["coordination_watch_bootstrap"]
    assert supervisor["proof_state"] == "declared-only-live-process-probe-skipped"
    assert bootstrap["proof_state"] == "declared-only-live-process-probe-skipped"
    assert supervisor["evidence"]["live_process_probe_skipped"] is True
    assert bootstrap["evidence"]["live_process_probe_skipped"] is True


def test_startup_surface_settings_exposes_wsl_managed_gateway_launcher(monkeypatch):
    monkeypatch.setattr(startup_surfaces, "_path_present", lambda raw_path: bool(raw_path))
    monkeypatch.setattr(
        startup_surfaces,
        "_read_text_if_present",
        lambda raw_path: startup_surfaces._gateway_target_launcher_contents(
            startup_surfaces.load_startup_surfaces_config("hermes")["gateway"]
        )
        if raw_path and str(raw_path).endswith("gateway.cmd")
        else None,
    )
    monkeypatch.setattr(
        startup_surfaces,
        "get_supervised_coordination_watch_status",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "supervision_enabled": True,
            "running": True,
            "stale_state": False,
            "state_present": True,
        },
    )
    monkeypatch.setattr(
        startup_surfaces,
        "build_coordination_watch_activation_report",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "proof_complete": False,
            "checks": {
                "installed": True,
                "scheduler_registered": False,
                "supervisor_running": True,
                "heartbeat_fresh": True,
            },
            "activation_proof": {},
        },
    )

    report = startup_surfaces.build_startup_surface_settings_report("hermes")
    runtime = report["runtimes"][0]
    settings = {entry["surface_id"]: entry for entry in runtime["settings"]}
    gateway = settings["gateway"]

    assert report["action"] == "startup-surface-settings"
    assert report["read_only"] is True
    assert report["settings_write_enabled"] is True
    assert gateway["user_manageable"] is True
    assert gateway["cli_mutation_enabled"] is True
    assert gateway["studio_cli_control_enabled"] is True
    assert gateway["studio_local_app_control_enabled"] is True
    assert gateway["studio_visual_toggle_built"] is True
    assert gateway["studio_mutation_enabled"] is False
    assert gateway["startup_registration_kind"] == "windows-startup-folder"
    assert "startup-surface-toggle" in gateway["commands"]["enable"]
    assert "--confirm" in gateway["commands"]["disable"]
    assert gateway["launch_profile"]["launch_kind"] == "wsl"
    assert gateway["launch_profile"]["wsl_distro"] == "Ubuntu"
    assert gateway["launch_profile"]["wsl_user"] == ""
    expected = gateway["managed_target_launcher"]["expected_contents"]
    assert "wsl.exe -d %HERMES_WSL_DISTRO% %HERMES_WSL_USER_ARG%" in expected
    assert 'wsl.exe -d "%HERMES_WSL_DISTRO%"' not in expected
    assert "gateway-startup.log" in expected
    assert "ChaseOS Hermes Daemon" in expected
    assert "start /b \"ChaseOS Hermes Daemon\"" in expected
    assert ".venv-win314\\Scripts\\python.exe" in expected
    assert ".venv-win\\Scripts\\python.exe" in expected
    assert "start /min" not in expected
    assert "title ChaseOS Hermes Gateway" in expected
    assert "WSLService" in expected
    assert "LxssManager" in expected
    assert "timeout /t" not in expected
    assert "ping -n" in expected
    assert 'bash -lc "cd %HERMES_WSL_WORKDIR% && true"' in expected
    assert gateway["managed_target_launcher"]["matches_expected"] is True


def test_startup_surface_toggle_gateway_disable_removes_startup_launcher(monkeypatch):
    tmp_path = _startup_toggle_test_dir("disable")
    launcher = tmp_path / "Startup" / "Hermes Gateway.cmd"
    target = tmp_path / ".hermes" / "gateway.cmd"
    launcher.parent.mkdir(parents=True, exist_ok=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    launcher.write_text('@echo off\ncall "old"\n', encoding="utf-8")
    target.write_text("@echo off\nrem existing\n", encoding="utf-8")

    record = {
        "runtime_id": "hermes",
        "platform": "windows",
        "lifecycle_mode": "test",
        "coordination_watch": {"runtime_name": "Hermes"},
        "startup_surfaces": {
            "gateway": {
                "surface_id": "gateway",
                "ui_label": "Hermes Gateway",
                "supported": True,
                "toggle_supported": True,
                "current_state_source": "host_startup_file",
                "startup_registration_kind": "windows-startup-folder",
                "launcher_path": str(launcher),
                "target_path": str(target),
                "status_command": "chaseos runtime startup-surfaces --runtime hermes --json",
            }
        },
    }
    monkeypatch.setattr(startup_surfaces, "load_lifecycle_record", lambda runtime_id: record)
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_MUTATION_DIR", tmp_path / "mutations")

    result = startup_surfaces.execute_startup_surface_toggle(
        "hermes",
        "gateway",
        "disable",
        confirm=True,
    )

    assert result["action"] == "startup-surface-toggle"
    assert result["executes_mutation"] is True
    assert result["before_state"] == "registered"
    assert result["after_state"] == "off"
    assert result["target_reached"] is True
    assert not launcher.exists()
    assert target.exists()
    assert (tmp_path / "mutations" / "events.jsonl").exists()
    assert result["marker_path"]


def test_resolve_path_handles_windows_drive_paths_for_current_host():
    resolved = startup_surfaces._resolve_path("C:\\Users\\chaseos\\.hermes\\gateway.cmd")

    if startup_surfaces.os.name == "nt":
        assert str(resolved) == "C:\\Users\\chaseos\\.hermes\\gateway.cmd"
    else:
        assert str(resolved).replace("\\", "/") == "<WINDOWS_USER_HOME_WSL>/.hermes/gateway.cmd"


def test_windows_drive_path_to_wsl_mount_translation_is_available_for_wsl_contexts():
    resolved = startup_surfaces._windows_drive_path_to_wsl("C:\\Users\\chaseos\\.hermes\\gateway.cmd")

    assert str(resolved).replace("\\", "/") == "<WINDOWS_USER_HOME_WSL>/.hermes/gateway.cmd"


def test_wsl_mount_path_to_windows_translation_supports_host_side_launchers():
    resolved = startup_surfaces._wsl_mount_path_to_windows("<VAULT_ROOT>")

    assert resolved == "C:\\Users\\chaseos\\Documents\\chaseos_obsidian"


def test_startup_surface_toggle_gateway_enable_writes_managed_wsl_launcher(monkeypatch):
    tmp_path = _startup_toggle_test_dir("enable")
    launcher = tmp_path / "Startup" / "Hermes Gateway.cmd"
    target = tmp_path / ".hermes" / "gateway.cmd"
    if launcher.exists():
        launcher.unlink()
    if target.exists():
        target.unlink()
    record = {
        "runtime_id": "hermes",
        "platform": "windows",
        "lifecycle_mode": "test",
        "coordination_watch": {"runtime_name": "Hermes"},
        "startup_surfaces": {
            "gateway": {
                "surface_id": "gateway",
                "ui_label": "Hermes Gateway",
                "supported": True,
                "toggle_supported": True,
                "current_state_source": "host_startup_file",
                "startup_registration_kind": "windows-startup-folder",
                "launcher_path": str(launcher),
                "target_path": str(target),
                "launcher_template_version": "test-wsl",
                "launch_kind": "wsl",
                "wsl_distro": "Ubuntu",
                "wsl_user": "chaseos",
                "wsl_workdir": "<VAULT_ROOT>",
                "wsl_command": "exec <WSL_HOME>/.local/bin/hermes gateway run",
                "diagnostic_log_path": str(tmp_path / "gateway-startup.log"),
                "retry_attempts": 2,
                "retry_delay_seconds": 1,
                "status_command": "chaseos runtime startup-surfaces --runtime hermes --json",
            }
        },
    }
    monkeypatch.setattr(startup_surfaces, "load_lifecycle_record", lambda runtime_id: record)
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_MUTATION_DIR", tmp_path / "mutations")

    result = startup_surfaces.execute_startup_surface_toggle(
        "hermes",
        "gateway",
        "enable",
        confirm=True,
    )

    assert result["before_state"] == "off"
    assert result["after_state"] == "registered"
    assert result["target_reached"] is True
    assert result["approval_required"] is True
    assert result["approval_recorded"] is True
    assert result["approval_record"]["approval_kind"] == "inline_operator_confirmation"
    assert launcher.exists()
    assert target.exists()
    assert "call" in launcher.read_text(encoding="utf-8")
    target_text = target.read_text(encoding="utf-8")
    assert "wsl.exe -d %HERMES_WSL_DISTRO% %HERMES_WSL_USER_ARG%" in target_text
    assert 'wsl.exe -d "%HERMES_WSL_DISTRO%"' not in target_text
    assert "gateway-startup.log" in target_text
    assert "ChaseOS Hermes Daemon" in target_text
    assert "start /b \"ChaseOS Hermes Daemon\"" in target_text
    assert ".venv-win314\\Scripts\\python.exe" in target_text
    assert ".venv-win\\Scripts\\python.exe" in target_text
    assert "start /min" not in target_text
    assert "title ChaseOS Hermes Gateway" in target_text
    assert "WSLService" in target_text
    assert "LxssManager" in target_text
    assert "timeout /t" not in target_text
    assert "ping -n" in target_text
    assert 'bash -lc "cd %HERMES_WSL_WORKDIR% && true"' in target_text


def test_startup_surface_toggle_requires_confirm(monkeypatch):
    tmp_path = _startup_toggle_test_dir("requires-confirm")
    record = {
        "runtime_id": "hermes",
        "platform": "windows",
        "lifecycle_mode": "test",
        "coordination_watch": {"runtime_name": "Hermes"},
        "startup_surfaces": {
            "gateway": {
                "surface_id": "gateway",
                "supported": True,
                "toggle_supported": True,
                "current_state_source": "host_startup_file",
                "startup_registration_kind": "windows-startup-folder",
                "launcher_path": str(tmp_path / "Hermes Gateway.cmd"),
                "target_path": str(tmp_path / "gateway.cmd"),
            }
        },
    }
    monkeypatch.setattr(startup_surfaces, "load_lifecycle_record", lambda runtime_id: record)

    try:
        startup_surfaces.execute_startup_surface_toggle("hermes", "gateway", "disable")
    except ValueError as exc:
        assert "--confirm" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_startup_surfaces_report_handles_all_runtimes(monkeypatch):
    monkeypatch.setattr(startup_surfaces, "list_lifecycle_runtime_ids", lambda: ["hermes", "openclaw"])
    monkeypatch.setattr(startup_surfaces, "_path_present", lambda raw_path: False)
    monkeypatch.setattr(
        startup_surfaces,
        "get_supervised_coordination_watch_status",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "supervision_enabled": True,
            "running": False,
            "stale_state": False,
            "state_present": False,
        },
    )
    monkeypatch.setattr(
        startup_surfaces,
        "build_coordination_watch_activation_report",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "proof_complete": False,
            "checks": {
                "installed": False,
                "scheduler_registered": False,
                "supervisor_running": False,
                "heartbeat_fresh": False,
            },
            "activation_proof": {},
        },
    )

    report = startup_surfaces.build_startup_surfaces_report("all")

    assert report["action"] == "startup-surfaces"
    assert report["schema_version"] == 1
    assert report["read_only"] is True
    assert report["mutation_enabled"] is False
    assert report["runtime_count"] == 2
    assert report["surface_count"] == 6
    assert report["toggle_supported_count"] == 6


def test_startup_surface_toggle_plan_is_read_only(monkeypatch):
    monkeypatch.setattr(startup_surfaces, "_path_present", lambda raw_path: bool(raw_path))
    monkeypatch.setattr(
        startup_surfaces,
        "get_supervised_coordination_watch_status",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "supervision_enabled": True,
            "running": True,
            "stale_state": False,
            "state_present": True,
        },
    )
    monkeypatch.setattr(
        startup_surfaces,
        "build_coordination_watch_activation_report",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "proof_complete": False,
            "checks": {
                "installed": True,
                "scheduler_registered": False,
                "supervisor_running": True,
                "heartbeat_fresh": True,
            },
            "activation_proof": {},
        },
    )

    plan = startup_surfaces.build_startup_surface_toggle_plan("hermes", "gateway", "enable")

    assert plan["action"] == "startup-surface-toggle-plan"
    assert plan["schema_version"] == 1
    assert plan["runtime_id"] == "hermes"
    assert plan["surface_id"] == "gateway"
    assert plan["intent"] == "enable"
    assert plan["read_only"] is True
    assert plan["mutation_enabled"] is False
    assert plan["executes_mutation"] is False
    assert plan["future_mutation_required"] is True
    assert any(step["step_id"] == "register-startup-launcher" for step in plan["steps"])


def test_startup_surface_mutation_contract_blocks_executor(monkeypatch):
    monkeypatch.setattr(startup_surfaces, "_path_present", lambda raw_path: bool(raw_path))
    monkeypatch.setattr(
        startup_surfaces,
        "get_supervised_coordination_watch_status",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "supervision_enabled": True,
            "running": True,
            "stale_state": False,
            "state_present": True,
        },
    )
    monkeypatch.setattr(
        startup_surfaces,
        "build_coordination_watch_activation_report",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "proof_complete": False,
            "checks": {
                "installed": True,
                "scheduler_registered": True,
                "supervisor_running": True,
                "heartbeat_fresh": True,
            },
            "activation_proof": {},
        },
    )

    contract = startup_surfaces.build_startup_surface_mutation_contract(
        "hermes",
        "coordination_watch_bootstrap",
        "disable",
    )

    assert contract["action"] == "startup-surface-mutation-contract"
    assert contract["schema_version"] == 1
    assert contract["read_only"] is True
    assert contract["mutation_enabled"] is False
    assert contract["execution_enabled"] is False
    assert contract["executor_implemented"] is True
    assert contract["required_gate_operation"] == "lifecycle.startup_surface.coordination_watch_bootstrap.disable"
    assert contract["gate_operation_allowlisted"] is True
    assert contract["external_api"] == "host.scheduler"
    assert contract["external_side_effect"] is True
    assert "approval-driven-host-mutation-executor-not-built" in contract["blocked_reasons"]
    assert contract["rollback_plan"]["inverse_intent"] == "enable"
    assert any("startup-surfaces" in command for command in contract["verification_commands"])
    assert all(
        step.get("requires_gate_operation") == contract["required_gate_operation"]
        for step in contract["execution_steps"]
        if step.get("mutates")
    )


def _test_approval_dir() -> "startup_surfaces.Path":
    approval_dir = startup_surfaces.ROOT / "runtime" / "lifecycle" / "run" / "test-startup-surface-approvals"
    approval_dir.mkdir(parents=True, exist_ok=True)
    for path in approval_dir.glob("*.json"):
        path.unlink()
    for child_dir in [approval_dir / "decisions", approval_dir / "consumptions", approval_dir / "markers"]:
        child_dir.mkdir(parents=True, exist_ok=True)
        for path in child_dir.glob("*.json"):
            path.unlink()
    return approval_dir


def test_startup_surface_approval_request_writes_pending_artifact(monkeypatch):
    approval_dir = _test_approval_dir()
    monkeypatch.setattr(startup_surfaces, "_path_present", lambda raw_path: bool(raw_path))
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(
        startup_surfaces,
        "get_supervised_coordination_watch_status",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "supervision_enabled": True,
            "running": True,
            "stale_state": False,
            "state_present": True,
        },
    )
    monkeypatch.setattr(
        startup_surfaces,
        "build_coordination_watch_activation_report",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "proof_complete": False,
            "checks": {
                "installed": True,
                "scheduler_registered": True,
                "supervisor_running": True,
                "heartbeat_fresh": True,
            },
            "activation_proof": {},
        },
    )

    preview = startup_surfaces.build_startup_surface_approval_request(
        "hermes",
        "gateway",
        "disable",
        gate_approval_id="startup-appr-request-test",
        requested_by="codex-test",
    )
    assert preview["action"] == "startup-surface-approval-request"
    assert preview["written"] is False
    assert preview["source_contract"]["external_api_allowlisted"] is True
    assert preview["approval_request"]["approval_status"] == "pending"
    assert preview["approval_request"]["requested_by"] == "codex-test"
    assert not (approval_dir / "startup-appr-request-test.json").exists()

    written = startup_surfaces.build_startup_surface_approval_request(
        "hermes",
        "gateway",
        "disable",
        gate_approval_id="startup-appr-request-test",
        requested_by="codex-test",
        write=True,
    )
    payload = startup_surfaces.json.loads((approval_dir / "startup-appr-request-test.json").read_text(encoding="utf-8"))
    assert written["written"] is True
    assert payload["approval_status"] == "pending"
    assert payload["runtime_id"] == "hermes"
    assert payload["surface_id"] == "gateway"
    assert payload["intent"] == "disable"
    assert payload["approval_consumed"] is False


def test_startup_surface_approval_decision_feeds_preflight_without_consumption(monkeypatch):
    approval_dir = _test_approval_dir()
    marker_dir = approval_dir / "markers"
    monkeypatch.setattr(startup_surfaces, "_path_present", lambda raw_path: bool(raw_path))
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_MUTATION_DIR", marker_dir)
    monkeypatch.setattr(
        startup_surfaces,
        "get_supervised_coordination_watch_status",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "supervision_enabled": True,
            "running": True,
            "stale_state": False,
            "state_present": True,
        },
    )
    monkeypatch.setattr(
        startup_surfaces,
        "build_coordination_watch_activation_report",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "proof_complete": False,
            "checks": {
                "installed": True,
                "scheduler_registered": True,
                "supervisor_running": True,
                "heartbeat_fresh": True,
            },
            "activation_proof": {},
        },
    )

    request = startup_surfaces.build_startup_surface_approval_request(
        "hermes",
        "gateway",
        "disable",
        gate_approval_id="startup-appr-decision-test",
        requested_by="codex-test",
        write=True,
    )
    decision = startup_surfaces.build_startup_surface_approval_decision(
        "startup-appr-decision-test",
        "approved",
        decided_by="operator",
        reason="targeted pytest",
        write=True,
    )
    preflight = startup_surfaces.build_startup_surface_executor_preflight(
        "hermes",
        "gateway",
        "disable",
        gate_approval_id="startup-appr-decision-test",
        plan_digest=request["plan_digest_sha256"],
    )

    assert decision["written"] is True
    assert (approval_dir / "decisions" / "startup-appr-decision-test.json").exists()
    assert preflight["approval_artifact"]["status"] == "approved"
    assert preflight["approval_consumption_preflight"]["ready"] is True
    assert preflight["approval_consumption_preflight"]["consumption_enabled"] is False
    assert preflight["approval_consumed"] is False
    assert preflight["host_mutation_attempted"] is False


def test_startup_surface_executor_preflight_validates_approval_without_execution(monkeypatch):
    approval_dir = _test_approval_dir()
    monkeypatch.setattr(startup_surfaces, "_path_present", lambda raw_path: bool(raw_path))
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(
        startup_surfaces,
        "get_supervised_coordination_watch_status",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "supervision_enabled": True,
            "running": True,
            "stale_state": False,
            "state_present": True,
        },
    )
    monkeypatch.setattr(
        startup_surfaces,
        "build_coordination_watch_activation_report",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "proof_complete": False,
            "checks": {
                "installed": True,
                "scheduler_registered": True,
                "supervisor_running": True,
                "heartbeat_fresh": True,
            },
            "activation_proof": {},
        },
    )

    contract = startup_surfaces.build_startup_surface_mutation_contract("hermes", "gateway", "enable")
    digest = startup_surfaces._json_digest(startup_surfaces._plan_digest_payload(contract))
    approval_id = "startup-appr-test"
    (approval_dir / f"{approval_id}.json").write_text(
        startup_surfaces.json.dumps(
            {
                "gate_approval_id": approval_id,
                "approval_status": "approved",
                "runtime_id": "hermes",
                "surface_id": "gateway",
                "intent": "enable",
                "required_gate_operation": "lifecycle.startup_surface.gateway.enable",
                "plan_digest_sha256": digest,
            }
        ),
        encoding="utf-8",
    )

    preflight = startup_surfaces.build_startup_surface_executor_preflight(
        "hermes",
        "gateway",
        "enable",
        gate_approval_id=approval_id,
        plan_digest=digest,
    )

    checks = {check["check_id"]: check for check in preflight["checks"]}
    assert preflight["action"] == "startup-surface-executor-preflight"
    assert preflight["read_only"] is True
    assert preflight["mutation_enabled"] is False
    assert preflight["execution_enabled"] is False
    assert preflight["executor_invocation_allowed"] is False
    assert preflight["approval_consumed"] is False
    assert preflight["idempotency_marker_written"] is False
    assert preflight["host_mutation_attempted"] is False
    assert checks["approval-artifact-present"]["passed"] is True
    assert checks["approval-plan-digest-match"]["passed"] is True
    assert checks["requested-plan-digest-current"]["passed"] is True
    assert checks["executor-implemented"]["passed"] is True
    assert preflight["approval_consumption_preflight"]["ready"] is True
    assert preflight["approval_consumption_preflight"]["would_consume_approval"] is True
    assert preflight["approval_consumption_preflight"]["consumption_enabled"] is False
    assert preflight["approval_consumption_preflight"]["consumption_attempted"] is False
    assert preflight["idempotency_marker_contract"]["ready"] is True
    assert preflight["idempotency_marker_contract"]["would_write_marker"] is True
    assert preflight["idempotency_marker_contract"]["write_enabled"] is False
    assert preflight["idempotency_marker_contract"]["write_attempted"] is False
    assert preflight["idempotency_marker_contract"]["atomic_write_rule"] == "create-new-only"
    assert preflight["idempotency_marker_contract"]["marker_payload_preview"]["gate_approval_id"] == approval_id
    assert preflight["execution_gate"]["would_execute_mutation"] is False
    assert preflight["execution_gate"]["all_preconditions_met_except_execution_enabled"] is True
    assert "startup-surface-approval-preflight-only" in preflight["blocked_reasons"]


def test_startup_surface_transaction_order_report_models_future_sequence_without_mutation(monkeypatch):
    approval_dir = _test_approval_dir()
    marker_dir = approval_dir / "markers"
    monkeypatch.setattr(startup_surfaces, "_path_present", lambda raw_path: bool(raw_path))
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_MUTATION_DIR", marker_dir)
    monkeypatch.setattr(
        startup_surfaces,
        "get_supervised_coordination_watch_status",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "supervision_enabled": True,
            "running": True,
            "stale_state": False,
            "state_present": True,
        },
    )
    monkeypatch.setattr(
        startup_surfaces,
        "build_coordination_watch_activation_report",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "proof_complete": False,
            "checks": {
                "installed": True,
                "scheduler_registered": True,
                "supervisor_running": True,
                "heartbeat_fresh": True,
            },
            "activation_proof": {},
        },
    )
    request = startup_surfaces.build_startup_surface_approval_request(
        "hermes",
        "gateway",
        "disable",
        gate_approval_id="startup-transaction-order-test",
        requested_by="optimus-test",
        write=True,
    )
    startup_surfaces.build_startup_surface_approval_decision(
        "startup-transaction-order-test",
        "approved",
        decided_by="operator",
        write=True,
    )

    report = startup_surfaces.build_startup_surface_transaction_order_report(
        "hermes",
        "gateway",
        "disable",
        gate_approval_id="startup-transaction-order-test",
        plan_digest=request["plan_digest_sha256"],
    )

    assert report["action"] == "startup-surface-transaction-order-report"
    assert report["read_only"] is True
    assert report["execution_enabled"] is False
    assert report["host_mutation_attempted"] is False
    assert report["approval_consumed"] is False
    assert report["idempotency_marker_written"] is False
    assert report["transaction_status"] == "ready_for_future_executor_blocked_now"
    step_ids = [step["step_id"] for step in report["transaction_order"]]
    assert step_ids == [
        "validate-approval",
        "validate-idempotency-marker-absence",
        "execute-host-startup-mutation",
        "verify-target-state",
        "write-or-retain-idempotency-marker",
        "emit-agent-activity-audit",
    ]
    mutation_step = next(step for step in report["transaction_order"] if step["step_id"] == "execute-host-startup-mutation")
    assert mutation_step["would_mutate_host_when_enabled"] is True
    assert mutation_step["enabled_now"] is False
    assert report["failure_policy"]["host_mutation_failure"]["write_success_marker"] is False
    assert report["verification_gate"]["would_verify_after_mutation"] is True
    assert report["source_preflight"]["approval_consumption_preflight"]["ready"] is True
    assert not any(marker_dir.glob("*.json"))
    assert not (approval_dir / "consumptions" / "startup-transaction-order-test.json").exists()


def test_startup_surface_transaction_order_report_blocks_when_marker_exists(monkeypatch):
    approval_dir = _test_approval_dir()
    marker_dir = approval_dir / "markers"
    monkeypatch.setattr(startup_surfaces, "_path_present", lambda raw_path: bool(raw_path))
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_MUTATION_DIR", marker_dir)
    request = startup_surfaces.build_startup_surface_approval_request(
        "hermes",
        "gateway",
        "enable",
        gate_approval_id="startup-transaction-duplicate-test",
        requested_by="optimus-test",
        write=True,
    )
    startup_surfaces.build_startup_surface_approval_decision(
        "startup-transaction-duplicate-test",
        "approved",
        decided_by="operator",
        write=True,
    )
    preflight = startup_surfaces.build_startup_surface_executor_preflight(
        "hermes",
        "gateway",
        "enable",
        gate_approval_id="startup-transaction-duplicate-test",
        plan_digest=request["plan_digest_sha256"],
    )
    marker_path = startup_surfaces.Path(preflight["idempotency_marker_path"])
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text('{"existing": true}\n', encoding="utf-8")

    report = startup_surfaces.build_startup_surface_transaction_order_report(
        "hermes",
        "gateway",
        "enable",
        gate_approval_id="startup-transaction-duplicate-test",
        plan_digest=request["plan_digest_sha256"],
    )

    assert report["transaction_status"] == "blocked"
    assert report["duplicate_replay_blocked"] is True
    assert "idempotency-marker-absent" in report["blocked_reasons"]
    assert report["host_mutation_attempted"] is False


def test_startup_surface_executor_readiness_packet_is_fail_closed_without_host_mutation(monkeypatch):
    approval_dir = _test_approval_dir()
    marker_dir = approval_dir / "markers"
    monkeypatch.setattr(startup_surfaces, "_path_present", lambda raw_path: bool(raw_path))
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_MUTATION_DIR", marker_dir)
    monkeypatch.setattr(
        startup_surfaces,
        "get_supervised_coordination_watch_status",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "supervision_enabled": True,
            "running": True,
            "stale_state": False,
            "state_present": True,
        },
    )
    monkeypatch.setattr(
        startup_surfaces,
        "build_coordination_watch_activation_report",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "proof_complete": False,
            "checks": {
                "installed": True,
                "scheduler_registered": True,
                "supervisor_running": True,
                "heartbeat_fresh": True,
            },
            "activation_proof": {},
        },
    )
    request = startup_surfaces.build_startup_surface_approval_request(
        "hermes",
        "gateway",
        "disable",
        gate_approval_id="startup-executor-readiness-test",
        requested_by="optimus-test",
        write=True,
    )
    startup_surfaces.build_startup_surface_approval_decision(
        "startup-executor-readiness-test",
        "approved",
        decided_by="operator",
        write=True,
    )

    readiness = startup_surfaces.build_startup_surface_executor_readiness_report(
        "hermes",
        "gateway",
        "disable",
        gate_approval_id="startup-executor-readiness-test",
        plan_digest=request["plan_digest_sha256"],
    )

    assert readiness["action"] == "startup-surface-executor-readiness"
    assert readiness["read_only"] is True
    assert readiness["executor_enabled_now"] is False
    assert readiness["eligible_for_future_enablement"] is False
    assert readiness["startup_folder_mutation_enabled"] is False
    assert readiness["task_scheduler_mutation_enabled"] is False
    assert readiness["host_mutation_attempted"] is False
    assert readiness["approval_consumed"] is False
    assert readiness["idempotency_marker_written"] is False
    assert readiness["transaction_order"]["ready"] is True
    assert readiness["prerequisites"]["approval_gate"]["ready"] is True
    assert readiness["prerequisites"]["exact_once_idempotency"]["ready"] is True
    assert readiness["prerequisites"]["host_mutation_backend_enabled"]["ready"] is False
    assert "host-mutation-backend-not-enabled" in readiness["blocked_reasons"]
    assert "operator-confirmation-policy-not-finalized" in readiness["blocked_reasons"]
    assert "wsl-windows-host-boundary-policy-not-finalized" in readiness["blocked_reasons"]
    assert not any(marker_dir.glob("*.json"))
    assert not (approval_dir / "consumptions" / "startup-executor-readiness-test.json").exists()


def test_startup_surface_executor_readiness_blocks_without_transaction_material(monkeypatch):
    approval_dir = _test_approval_dir()
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_APPROVAL_DIR", approval_dir)

    readiness = startup_surfaces.build_startup_surface_executor_readiness_report("hermes", "gateway", "disable")

    assert readiness["read_only"] is True
    assert readiness["executor_enabled_now"] is False
    assert readiness["eligible_for_future_enablement"] is False
    assert readiness["transaction_order"]["ready"] is False
    assert "transaction-order-material-missing" in readiness["blocked_reasons"]
    assert readiness["approval_consumed"] is False
    assert readiness["idempotency_marker_written"] is False
    assert readiness["host_mutation_attempted"] is False


def test_startup_surface_host_boundary_policy_packet_models_wsl_windows_constraints_without_mutation(monkeypatch):
    approval_dir = _test_approval_dir()
    marker_dir = approval_dir / "markers"
    monkeypatch.setattr(startup_surfaces, "_path_present", lambda raw_path: bool(raw_path))
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_MUTATION_DIR", marker_dir)
    request = startup_surfaces.build_startup_surface_approval_request(
        "hermes",
        "gateway",
        "disable",
        gate_approval_id="startup-host-boundary-test",
        requested_by="optimus-test",
        write=True,
    )
    startup_surfaces.build_startup_surface_approval_decision(
        "startup-host-boundary-test",
        "approved",
        decided_by="operator",
        write=True,
    )

    policy = startup_surfaces.build_startup_surface_host_boundary_policy_report(
        "hermes",
        "gateway",
        "disable",
        gate_approval_id="startup-host-boundary-test",
        plan_digest=request["plan_digest_sha256"],
    )

    assert policy["action"] == "startup-surface-host-boundary-policy"
    assert policy["read_only"] is True
    assert policy["policy_status"] == "blocked"
    assert policy["host_mutation_attempted"] is False
    assert policy["approval_consumed"] is False
    assert policy["idempotency_marker_written"] is False
    assert policy["allowed_host_apis"]["selected_api"] == "host.startup_folder"
    assert policy["allowed_host_apis"]["api_allowlisted_by_contract"] is True
    assert policy["wsl_windows_boundary"]["windows_target_paths_translated_for_wsl"] is True
    assert policy["wsl_windows_boundary"]["host_executor_must_run_on_windows_side"] is True
    assert policy["operator_confirmation_policy"]["finalized"] is False
    assert "I understand this may change Windows startup behavior" in policy["operator_confirmation_policy"]["required_confirmation_phrase"]
    assert policy["rollback_policy"]["automatic_rollback_enabled"] is False
    assert policy["verification_evidence"]["required_before_success_marker"] is True
    assert "operator-confirmation-wording-not-approved" in policy["blocked_reasons"]
    assert "wsl-windows-host-boundary-policy-not-approved" in policy["blocked_reasons"]
    assert not any(marker_dir.glob("*.json"))
    assert not (approval_dir / "consumptions" / "startup-host-boundary-test.json").exists()


def test_startup_surface_host_boundary_policy_fails_closed_without_transaction_material():
    policy = startup_surfaces.build_startup_surface_host_boundary_policy_report("hermes", "gateway", "disable")

    assert policy["read_only"] is True
    assert policy["policy_status"] == "blocked"
    assert policy["transaction_order"]["provided"] is False
    assert policy["host_mutation_attempted"] is False
    assert "transaction-order-material-missing" in policy["blocked_reasons"]


def test_startup_surface_host_mutation_audit_template_packet_defines_required_agent_activity_evidence_without_mutation(monkeypatch):
    approval_dir = _test_approval_dir()
    marker_dir = approval_dir / "markers"
    monkeypatch.setattr(startup_surfaces, "_path_present", lambda raw_path: bool(raw_path))
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_MUTATION_DIR", marker_dir)
    request = startup_surfaces.build_startup_surface_approval_request(
        "hermes",
        "gateway",
        "disable",
        gate_approval_id="startup-audit-template-test",
        requested_by="optimus-test",
        write=True,
    )
    startup_surfaces.build_startup_surface_approval_decision(
        "startup-audit-template-test",
        "approved",
        decided_by="operator",
        write=True,
    )

    audit = startup_surfaces.build_startup_surface_host_mutation_audit_template_report(
        "hermes",
        "gateway",
        "disable",
        gate_approval_id="startup-audit-template-test",
        plan_digest=request["plan_digest_sha256"],
    )

    assert audit["action"] == "startup-surface-host-mutation-audit-template"
    assert audit["read_only"] is True
    assert audit["audit_template_status"] == "blocked"
    assert audit["host_mutation_attempted"] is False
    assert audit["approval_consumed"] is False
    assert audit["idempotency_marker_written"] is False
    assert audit["success_marker_acceptance"]["allowed_now"] is False
    assert audit["agent_activity_template"]["filename_slug"] == "hermes-optimus-runtime-startup-surface-mutation-hermes-gateway"
    assert "[[Hermes-Runtime-Profile]]" in audit["agent_activity_template"]["required_graph_links"]
    assert "[[HERMES]]" in audit["agent_activity_template"]["required_graph_links"]
    assert "[[Agent-Activity-Index]]" in audit["agent_activity_template"]["required_graph_links"]
    assert "before_state" in audit["required_evidence_fields"]
    assert "after_state" in audit["required_evidence_fields"]
    assert "target_reached" in audit["required_evidence_fields"]
    assert "rollback_result" in audit["required_evidence_fields"]
    assert audit["host_boundary_policy"]["policy_status"] == "blocked"
    assert "audit-template-not-approved" in audit["blocked_reasons"]
    assert not any(marker_dir.glob("*.json"))
    assert not (approval_dir / "consumptions" / "startup-audit-template-test.json").exists()


def test_startup_surface_host_mutation_audit_template_fails_closed_without_transaction_material():
    audit = startup_surfaces.build_startup_surface_host_mutation_audit_template_report("hermes", "gateway", "disable")

    assert audit["read_only"] is True
    assert audit["audit_template_status"] == "blocked"
    assert audit["transaction_order"]["provided"] is False
    assert audit["success_marker_acceptance"]["allowed_now"] is False
    assert audit["host_mutation_attempted"] is False
    assert "transaction-order-material-missing" in audit["blocked_reasons"]


def test_startup_surface_success_marker_evidence_verifier_rejects_missing_candidate_without_mutation(monkeypatch):
    approval_dir = _test_approval_dir()
    marker_dir = approval_dir / "markers"
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_MUTATION_DIR", marker_dir)

    verification = startup_surfaces.build_startup_surface_success_marker_evidence_verifier_report(
        "hermes",
        "gateway",
        "disable",
    )

    assert verification["action"] == "startup-surface-success-marker-evidence-verifier"
    assert verification["read_only"] is True
    assert verification["verifier_status"] == "rejected"
    assert verification["candidate_evidence_present"] is False
    assert verification["success_marker_acceptance"]["allowed_now"] is False
    assert verification["success_marker_acceptance"]["decision"] == "deny"
    assert verification["host_mutation_attempted"] is False
    assert verification["approval_consumed"] is False
    assert verification["idempotency_marker_written"] is False
    assert "candidate-evidence-missing" in verification["blocked_reasons"]
    assert "audit-template-not-approved" in verification["blocked_reasons"]
    assert not any(marker_dir.glob("*.json"))


def test_startup_surface_success_marker_evidence_verifier_scores_candidate_but_keeps_acceptance_blocked(monkeypatch):
    approval_dir = _test_approval_dir()
    marker_dir = approval_dir / "markers"
    monkeypatch.setattr(startup_surfaces, "_path_present", lambda raw_path: bool(raw_path))
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_MUTATION_DIR", marker_dir)
    request = startup_surfaces.build_startup_surface_approval_request(
        "hermes",
        "gateway",
        "disable",
        gate_approval_id="startup-success-marker-verifier-test",
        requested_by="optimus-test",
        write=True,
    )
    startup_surfaces.build_startup_surface_approval_decision(
        "startup-success-marker-verifier-test",
        "approved",
        decided_by="operator",
        write=True,
    )
    audit_template = startup_surfaces.build_startup_surface_host_mutation_audit_template_report(
        "hermes",
        "gateway",
        "disable",
        gate_approval_id="startup-success-marker-verifier-test",
        plan_digest=request["plan_digest_sha256"],
    )
    candidate = {field: f"candidate-{field}" for field in audit_template["required_evidence_fields"]}
    candidate.update(
        {
            "runtime_id": "hermes",
            "surface_id": "gateway",
            "intent": "disable",
            "gate_approval_id": "startup-success-marker-verifier-test",
            "plan_digest_sha256": request["plan_digest_sha256"],
            "host_boundary_policy_status": "blocked",
            "target_reached": True,
            "verification_result": {"ok": True},
            "rollback_result": {"required": True, "status": "not-needed"},
            "host_mutation_attempted": True,
            "startup_surface_mutation_executed": True,
            "agent_activity_graph_links": [
                "[[Hermes-Runtime-Profile]]",
                "[[HERMES]]",
                "[[Agent-Activity-Index]]",
            ],
            "agent_activity_sections": audit_template["agent_activity_template"]["required_sections"],
        }
    )

    verification = startup_surfaces.build_startup_surface_success_marker_evidence_verifier_report(
        "hermes",
        "gateway",
        "disable",
        gate_approval_id="startup-success-marker-verifier-test",
        plan_digest=request["plan_digest_sha256"],
        candidate_evidence=candidate,
    )

    assert verification["candidate_evidence_present"] is True
    assert verification["evidence_check"]["required_fields_present"] is True
    assert verification["evidence_check"]["graph_links_present"] is True
    assert verification["evidence_check"]["sections_present"] is True
    assert verification["evidence_check"]["target_reached_verified"] is True
    assert verification["evidence_check"]["candidate_matches_transaction"] is True
    assert verification["success_marker_acceptance"]["allowed_now"] is False
    assert verification["success_marker_acceptance"]["decision"] == "deny"
    assert verification["host_mutation_attempted"] is False
    assert verification["approval_consumed"] is False
    assert verification["idempotency_marker_written"] is False
    assert "success-marker-acceptance-policy-not-approved" in verification["blocked_reasons"]
    assert not any(marker_dir.glob("*.json"))
    assert not (approval_dir / "consumptions" / "startup-success-marker-verifier-test.json").exists()


def test_startup_surface_success_marker_acceptance_policy_packet_denies_missing_verified_evidence_without_mutation(monkeypatch):
    approval_dir = _test_approval_dir()
    marker_dir = approval_dir / "markers"
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_MUTATION_DIR", marker_dir)

    policy = startup_surfaces.build_startup_surface_success_marker_acceptance_policy_report(
        "hermes",
        "gateway",
        "disable",
    )

    assert policy["action"] == "startup-surface-success-marker-acceptance-policy"
    assert policy["read_only"] is True
    assert policy["acceptance_policy_status"] == "blocked"
    assert policy["success_marker_acceptance"]["allowed_now"] is False
    assert policy["success_marker_acceptance"]["decision"] == "deny"
    assert policy["success_marker_acceptance"]["marker_write_allowed"] is False
    assert policy["policy_requirements"]["verified_evidence_required"] is True
    assert policy["policy_requirements"]["gate_policy_approval_required"] is True
    assert policy["policy_requirements"]["operator_final_confirmation_required"] is True
    assert policy["evidence_verifier"]["candidate_evidence_present"] is False
    assert policy["host_mutation_attempted"] is False
    assert policy["approval_consumed"] is False
    assert policy["idempotency_marker_written"] is False
    assert "verified-evidence-missing" in policy["blocked_reasons"]
    assert "success-marker-acceptance-policy-not-approved" in policy["blocked_reasons"]
    assert not any(marker_dir.glob("*.json"))


def test_startup_surface_success_marker_acceptance_policy_scores_verified_candidate_but_keeps_writes_blocked(monkeypatch):
    approval_dir = _test_approval_dir()
    marker_dir = approval_dir / "markers"
    monkeypatch.setattr(startup_surfaces, "_path_present", lambda raw_path: bool(raw_path))
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_MUTATION_DIR", marker_dir)
    request = startup_surfaces.build_startup_surface_approval_request(
        "hermes",
        "gateway",
        "disable",
        gate_approval_id="startup-success-marker-policy-test",
        requested_by="optimus-test",
        write=True,
    )
    startup_surfaces.build_startup_surface_approval_decision(
        "startup-success-marker-policy-test",
        "approved",
        decided_by="operator",
        write=True,
    )
    audit_template = startup_surfaces.build_startup_surface_host_mutation_audit_template_report(
        "hermes",
        "gateway",
        "disable",
        gate_approval_id="startup-success-marker-policy-test",
        plan_digest=request["plan_digest_sha256"],
    )
    candidate = {field: f"candidate-{field}" for field in audit_template["required_evidence_fields"]}
    candidate.update(
        {
            "runtime_id": "hermes",
            "surface_id": "gateway",
            "intent": "disable",
            "gate_approval_id": "startup-success-marker-policy-test",
            "plan_digest_sha256": request["plan_digest_sha256"],
            "target_reached": True,
            "verification_result": {"ok": True},
            "rollback_result": {"required": True, "status": "not-needed"},
            "agent_activity_graph_links": [
                "[[Hermes-Runtime-Profile]]",
                "[[HERMES]]",
                "[[Agent-Activity-Index]]",
            ],
            "agent_activity_sections": audit_template["agent_activity_template"]["required_sections"],
        }
    )

    policy = startup_surfaces.build_startup_surface_success_marker_acceptance_policy_report(
        "hermes",
        "gateway",
        "disable",
        gate_approval_id="startup-success-marker-policy-test",
        plan_digest=request["plan_digest_sha256"],
        candidate_evidence=candidate,
    )

    assert policy["evidence_verifier"]["evidence_check"]["evidence_complete"] is True
    assert policy["success_marker_acceptance"]["would_accept_if_policy_enabled"] is True
    assert policy["success_marker_acceptance"]["allowed_now"] is False
    assert policy["success_marker_acceptance"]["marker_write_allowed"] is False
    assert policy["success_marker_acceptance"]["marker_path"]
    assert policy["host_mutation_attempted"] is False
    assert policy["approval_consumed"] is False
    assert policy["idempotency_marker_written"] is False
    assert policy["success_marker_written"] is False
    assert "success-marker-acceptance-policy-not-approved" in policy["blocked_reasons"]
    assert not any(marker_dir.glob("*.json"))
    assert not (approval_dir / "consumptions" / "startup-success-marker-policy-test.json").exists()


def test_startup_surface_approval_consumer_writes_consumption_and_marker_without_host_mutation(monkeypatch):
    approval_dir = _test_approval_dir()
    marker_dir = approval_dir / "markers"
    monkeypatch.setattr(startup_surfaces, "_path_present", lambda raw_path: bool(raw_path))
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_MUTATION_DIR", marker_dir)
    monkeypatch.setattr(
        startup_surfaces,
        "get_supervised_coordination_watch_status",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "supervision_enabled": True,
            "running": True,
            "stale_state": False,
            "state_present": True,
        },
    )
    monkeypatch.setattr(
        startup_surfaces,
        "build_coordination_watch_activation_report",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "proof_complete": False,
            "checks": {
                "installed": True,
                "scheduler_registered": True,
                "supervisor_running": True,
                "heartbeat_fresh": True,
            },
            "activation_proof": {},
        },
    )

    request = startup_surfaces.build_startup_surface_approval_request(
        "hermes",
        "gateway",
        "disable",
        gate_approval_id="startup-appr-consume-test",
        requested_by="codex-test",
        write=True,
    )
    startup_surfaces.build_startup_surface_approval_decision(
        "startup-appr-consume-test",
        "approved",
        decided_by="operator",
        reason="targeted pytest",
        write=True,
    )

    preview = startup_surfaces.build_startup_surface_approval_consumption(
        "hermes",
        "gateway",
        "disable",
        gate_approval_id="startup-appr-consume-test",
        plan_digest=request["plan_digest_sha256"],
    )
    assert preview["write_enabled"] is False
    assert preview["approval_would_be_consumed"] is True
    assert preview["idempotency_marker_would_be_written"] is True
    assert preview["approval_consumed"] is False
    assert preview["idempotency_marker_written"] is False
    assert preview["host_mutation_attempted"] is False
    assert not (approval_dir / "consumptions" / "startup-appr-consume-test.json").exists()

    written = startup_surfaces.build_startup_surface_approval_consumption(
        "hermes",
        "gateway",
        "disable",
        gate_approval_id="startup-appr-consume-test",
        plan_digest=request["plan_digest_sha256"],
        write=True,
    )
    marker_path = startup_surfaces.Path(written["idempotency_marker_path"])
    consumption_path = startup_surfaces.Path(written["approval_consumption_path"])
    marker_payload = startup_surfaces.json.loads(marker_path.read_text(encoding="utf-8"))
    consumption_payload = startup_surfaces.json.loads(consumption_path.read_text(encoding="utf-8"))

    assert written["approval_consumed"] is True
    assert written["idempotency_marker_written"] is True
    assert written["executes_mutation"] is False
    assert written["host_mutation_attempted"] is False
    assert written["startup_surface_mutation_executed"] is False
    assert consumption_payload["gate_approval_id"] == "startup-appr-consume-test"
    assert consumption_payload["plan_digest_sha256"] == request["plan_digest_sha256"]
    assert marker_payload["gate_approval_id"] == "startup-appr-consume-test"
    assert marker_payload["atomic_write_rule"] == "create-new-only"

    consumed_preflight = startup_surfaces.build_startup_surface_executor_preflight(
        "hermes",
        "gateway",
        "disable",
        gate_approval_id="startup-appr-consume-test",
        plan_digest=request["plan_digest_sha256"],
    )
    assert consumed_preflight["approval_consumption_preflight"]["ready"] is False
    assert "approval-not-consumed" in consumed_preflight["blocked_reasons"]
    assert "idempotency-marker-absent" in consumed_preflight["blocked_reasons"]


def test_startup_surface_approval_consumer_refuses_duplicate_marker(monkeypatch):
    approval_dir = _test_approval_dir()
    marker_dir = approval_dir / "markers"
    monkeypatch.setattr(startup_surfaces, "_path_present", lambda raw_path: bool(raw_path))
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_MUTATION_DIR", marker_dir)
    monkeypatch.setattr(
        startup_surfaces,
        "get_supervised_coordination_watch_status",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "supervision_enabled": True,
            "running": True,
            "stale_state": False,
            "state_present": True,
        },
    )
    monkeypatch.setattr(
        startup_surfaces,
        "build_coordination_watch_activation_report",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "proof_complete": False,
            "checks": {
                "installed": True,
                "scheduler_registered": True,
                "supervisor_running": True,
                "heartbeat_fresh": True,
            },
            "activation_proof": {},
        },
    )
    request = startup_surfaces.build_startup_surface_approval_request(
        "hermes",
        "gateway",
        "enable",
        gate_approval_id="startup-appr-duplicate-consume-test",
        requested_by="codex-test",
        write=True,
    )
    startup_surfaces.build_startup_surface_approval_decision(
        "startup-appr-duplicate-consume-test",
        "approved",
        decided_by="operator",
        write=True,
    )
    first = startup_surfaces.build_startup_surface_approval_consumption(
        "hermes",
        "gateway",
        "enable",
        gate_approval_id="startup-appr-duplicate-consume-test",
        plan_digest=request["plan_digest_sha256"],
        write=True,
    )

    try:
        startup_surfaces.build_startup_surface_approval_consumption(
            "hermes",
            "gateway",
            "enable",
            gate_approval_id="startup-appr-duplicate-consume-test",
            plan_digest=request["plan_digest_sha256"],
            write=True,
        )
    except ValueError as exc:
        assert "already consumed" in str(exc) or "idempotency marker already exists" in str(exc)
    else:
        raise AssertionError("duplicate consumption unexpectedly succeeded")
    assert startup_surfaces.Path(first["idempotency_marker_path"]).exists()


def test_startup_surface_executor_preflight_blocks_consumption_when_marker_exists(monkeypatch):
    approval_dir = _test_approval_dir()
    marker_dir = approval_dir / "markers"
    marker_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_MUTATION_DIR", marker_dir)
    monkeypatch.setattr(
        startup_surfaces,
        "get_supervised_coordination_watch_status",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "supervision_enabled": True,
            "running": True,
            "stale_state": False,
            "state_present": True,
        },
    )
    monkeypatch.setattr(
        startup_surfaces,
        "build_coordination_watch_activation_report",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "proof_complete": False,
            "checks": {
                "installed": True,
                "scheduler_registered": True,
                "supervisor_running": True,
                "heartbeat_fresh": True,
            },
            "activation_proof": {},
        },
    )

    contract = startup_surfaces.build_startup_surface_mutation_contract("hermes", "gateway", "enable")
    digest = startup_surfaces._json_digest(startup_surfaces._plan_digest_payload(contract))
    approval_id = "startup-appr-marker-present"
    (approval_dir / f"{approval_id}.json").write_text(
        startup_surfaces.json.dumps(
            {
                "gate_approval_id": approval_id,
                "approval_status": "approved",
                "runtime_id": "hermes",
                "surface_id": "gateway",
                "intent": "enable",
                "required_gate_operation": "lifecycle.startup_surface.gateway.enable",
                "plan_digest_sha256": digest,
            }
        ),
        encoding="utf-8",
    )
    marker_path = marker_dir / f"hermes-gateway-enable-{digest[:12]}.json"
    marker_path.write_text('{"existing": true}', encoding="utf-8")
    try:
        preflight = startup_surfaces.build_startup_surface_executor_preflight(
            "hermes",
            "gateway",
            "enable",
            gate_approval_id=approval_id,
            plan_digest=digest,
        )
    finally:
        marker_path.unlink(missing_ok=True)

    assert preflight["idempotency_marker_present"] is True
    assert preflight["approval_consumption_preflight"]["ready"] is False
    assert preflight["approval_consumption_preflight"]["would_consume_approval"] is False
    assert preflight["idempotency_marker_contract"]["ready"] is False
    assert preflight["idempotency_marker_contract"]["would_write_marker"] is False
    assert preflight["idempotency_marker_contract"]["duplicate_replay_blocked"] is True
    assert "idempotency-marker-absent" in preflight["blocked_reasons"]


def test_startup_surface_executor_preflight_reports_missing_approval(monkeypatch):
    approval_dir = _test_approval_dir()
    monkeypatch.setattr(startup_surfaces, "_path_present", lambda raw_path: bool(raw_path))
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(
        startup_surfaces,
        "get_supervised_coordination_watch_status",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "supervision_enabled": True,
            "running": False,
            "stale_state": False,
            "state_present": False,
        },
    )
    monkeypatch.setattr(
        startup_surfaces,
        "build_coordination_watch_activation_report",
        lambda runtime_id: {
            "runtime_id": runtime_id,
            "proof_complete": False,
            "checks": {
                "installed": False,
                "scheduler_registered": False,
                "supervisor_running": False,
                "heartbeat_fresh": False,
            },
            "activation_proof": {},
        },
    )

    preflight = startup_surfaces.build_startup_surface_executor_preflight(
        "hermes",
        "gateway",
        "enable",
        gate_approval_id="missing-approval",
        plan_digest="0" * 64,
    )

    checks = {check["check_id"]: check for check in preflight["checks"]}
    assert checks["approval-artifact-present"]["passed"] is False
    assert checks["requested-plan-digest-current"]["passed"] is False
    assert "approval-artifact-present" in preflight["blocked_reasons"]


def test_startup_surface_toggle_plan_rejects_all_runtime():
    try:
        startup_surfaces.build_startup_surface_toggle_plan("all", "gateway", "enable")
    except ValueError as exc:
        assert "one concrete --runtime" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_startup_surface_host_mutation_executor_stays_disabled_by_default_after_valid_approval(monkeypatch):
    approval_dir = _test_approval_dir()
    marker_dir = approval_dir / "markers"
    tmp_path = _startup_toggle_test_dir("gated-executor-disabled")
    launcher = tmp_path / "Startup" / "Hermes Gateway.cmd"
    target = tmp_path / "Hermes Gateway Target.cmd"
    record = {
        "runtime_id": "hermes",
        "name": "Hermes",
        "startup_surfaces": {
            "gateway": {
                "surface_id": "gateway",
                "surface_type": "gateway",
                "ui_label": "Hermes Gateway",
                "supported": True,
                "toggle_supported": True,
                "current_state_source": "host_startup_file",
                "startup_registration_kind": "windows-startup-folder",
                "launcher_path": str(launcher),
                "target_path": str(target),
                "launch_kind": "wsl",
                "launcher_template_version": "test",
                "wsl_distro": "Ubuntu",
                "wsl_user": "chaseos",
                "wsl_workdir": "<WSL_HOME>/runtimes/hermes-home",
                "wsl_command": "hermes gateway run",
                "diagnostic_log_path": str(tmp_path / "gateway-startup.log"),
                "status_command": "chaseos runtime startup-surfaces --runtime hermes --json",
            }
        },
    }
    monkeypatch.setattr(startup_surfaces, "load_lifecycle_record", lambda runtime_id: record)
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_MUTATION_DIR", marker_dir)

    request = startup_surfaces.build_startup_surface_approval_request(
        "hermes",
        "gateway",
        "enable",
        gate_approval_id="startup-host-exec-disabled-test",
        requested_by="optimus-test",
        write=True,
    )
    startup_surfaces.build_startup_surface_approval_decision(
        "startup-host-exec-disabled-test",
        "approved",
        decided_by="operator",
        write=True,
    )

    result = startup_surfaces.execute_startup_surface_host_mutation(
        "hermes",
        "gateway",
        "enable",
        gate_approval_id="startup-host-exec-disabled-test",
        plan_digest=request["plan_digest_sha256"],
        operator_confirmation=(
            "I approve startup host mutation for hermes/gateway enable via "
            "startup-host-exec-disabled-test plan "
            f"{request['plan_digest_sha256']}"
        ),
    )

    assert result["action"] == "startup-surface-host-mutation-executor"
    assert result["executor_enabled"] is False
    assert result["execution_enabled"] is False
    assert result["host_mutation_attempted"] is False
    assert result["approval_consumed"] is False
    assert result["idempotency_marker_written"] is False
    assert "host-executor-disabled-by-default" in result["blocked_reasons"]
    assert result["preflight"]["approval_consumption_preflight"]["ready"] is True
    assert not launcher.exists()
    assert not target.exists()


def test_startup_surface_host_mutation_executor_refuses_live_writes_until_final_policy_gates(monkeypatch):
    approval_dir = _test_approval_dir()
    marker_dir = approval_dir / "markers"
    tmp_path = _startup_toggle_test_dir("gated-executor-final-policy-blocked")
    launcher = tmp_path / "Startup" / "Hermes Gateway.cmd"
    target = tmp_path / "Hermes Gateway Target.cmd"
    record = {
        "runtime_id": "hermes",
        "name": "Hermes",
        "startup_surfaces": {
            "gateway": {
                "surface_id": "gateway",
                "surface_type": "gateway",
                "ui_label": "Hermes Gateway",
                "supported": True,
                "toggle_supported": True,
                "current_state_source": "host_startup_file",
                "startup_registration_kind": "windows-startup-folder",
                "launcher_path": str(launcher),
                "target_path": str(target),
                "launch_kind": "wsl",
                "launcher_template_version": "test",
                "wsl_distro": "Ubuntu",
                "wsl_user": "chaseos",
                "wsl_workdir": "<WSL_HOME>/runtimes/hermes-home",
                "wsl_command": "hermes gateway run",
                "diagnostic_log_path": str(tmp_path / "gateway-startup.log"),
                "status_command": "chaseos runtime startup-surfaces --runtime hermes --json",
            }
        },
    }
    monkeypatch.setattr(startup_surfaces, "load_lifecycle_record", lambda runtime_id: record)
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_APPROVAL_DIR", approval_dir)
    monkeypatch.setattr(startup_surfaces, "STARTUP_SURFACE_MUTATION_DIR", marker_dir)

    request = startup_surfaces.build_startup_surface_approval_request(
        "hermes",
        "gateway",
        "enable",
        gate_approval_id="startup-host-exec-final-policy-test",
        requested_by="optimus-test",
        write=True,
    )
    startup_surfaces.build_startup_surface_approval_decision(
        "startup-host-exec-final-policy-test",
        "approved",
        decided_by="operator",
        write=True,
    )

    confirmation = (
        "I approve startup host mutation for hermes/gateway enable via "
        "startup-host-exec-final-policy-test plan "
        f"{request['plan_digest_sha256']}"
    )
    result = startup_surfaces.execute_startup_surface_host_mutation(
        "hermes",
        "gateway",
        "enable",
        gate_approval_id="startup-host-exec-final-policy-test",
        plan_digest=request["plan_digest_sha256"],
        operator_confirmation=confirmation,
        executor_enabled=True,
        live_smoke_approved=True,
        requested_by="optimus-test",
    )

    assert result["executor_enabled"] is True
    assert result["execution_enabled"] is False
    assert result["host_mutation_attempted"] is False
    assert result["startup_surface_mutation_executed"] is False
    assert result["approval_consumed"] is False
    assert result["idempotency_marker_written"] is False
    assert result["selected_adapter"] == "windows-startup-folder"
    assert result["task_scheduler_mutation_attempted"] is False
    assert result["preflight"]["approval_consumption_preflight"]["ready"] is True
    assert result["host_boundary_policy"]["policy_status"] == "blocked"
    assert result["agent_activity_audit_template"]["audit_template_status"] == "blocked"
    assert result["final_policy_gates"]["all_finalized"] is False
    assert result["final_policy_gates"]["host_boundary_policy_finalized"] is False
    assert result["final_policy_gates"]["operator_confirmation_policy_finalized"] is False
    assert result["final_policy_gates"]["rollback_policy_finalized"] is False
    assert result["final_policy_gates"]["post_mutation_verification_policy_finalized"] is False
    assert result["final_policy_gates"]["production_approval_to_mutation_envelope_enabled"] is False
    assert result["final_policy_gates"]["agent_activity_audit_template_finalized"] is False
    assert set(result["blocked_reasons"]) >= {
        "wsl-windows-host-boundary-policy-not-finalized",
        "operator-confirmation-policy-not-finalized",
        "rollback-recovery-policy-not-finalized",
        "post-mutation-verification-policy-not-finalized",
        "production-approval-to-mutation-envelope-not-enabled",
        "agent-activity-audit-template-not-finalized",
    }
    assert not launcher.exists()
    assert not target.exists()
    assert not (approval_dir / "consumptions" / "startup-host-exec-final-policy-test.json").exists()
    assert len(list(marker_dir.glob("*.json"))) == 0
