"""Tests for Studio runtime daemon/gateway controls."""

from __future__ import annotations

from pathlib import Path

from runtime.studio import runtime_gateway_controls as controls


class _FakeProcess:
    pid = 43210


class _FakeCompletedProcess:
    returncode = 0
    stdout = ""
    stderr = ""


def _not_running_status(vault: Path, runtime_id: str, component_id: str, **kwargs) -> dict:
    return {
        "component_id": component_id,
        "status": "not_running",
        "running": False,
        "status_source": "none",
    }


def test_runtime_gateway_process_probe_uses_hidden_window(monkeypatch) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(controls.os, "name", "nt", raising=False)
    monkeypatch.setattr(controls.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)

    def fake_run(_args, **kwargs):
        captured.update(kwargs)
        return _FakeCompletedProcess()

    monkeypatch.setattr(controls.subprocess, "run", fake_run)

    result = controls._run_process_probe(["powershell.exe", "-NoProfile", "-Command", "$true"])

    assert result.returncode == 0
    assert captured["creationflags"] == 0x08000000


def test_runtime_gateway_popen_never_forces_new_console(monkeypatch) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(controls.os, "name", "nt", raising=False)
    monkeypatch.setattr(controls.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)
    monkeypatch.setattr(controls.subprocess, "CREATE_NEW_CONSOLE", 0x00000010, raising=False)

    def fake_popen(_args, **kwargs):
        captured.update(kwargs)
        return _FakeProcess()

    monkeypatch.setattr(controls.subprocess, "Popen", fake_popen)

    controls._popen(["gateway.cmd"], visible=True)

    assert not (captured["creationflags"] & 0x00000010)


def test_runtime_gateway_controls_model_exposes_daemon_and_gateway(monkeypatch, tmp_path):
    monkeypatch.setattr(controls, "_component_status", _not_running_status)
    monkeypatch.setattr(controls, "_system_start_registered", lambda vault, runtime_id: runtime_id == "openclaw")
    monkeypatch.setattr(
        controls,
        "build_hermes_gateway_config_control_model",
        lambda vault, probe_wsl=False: {
            "ok": True,
            "surface": "hermes_gateway_config_controls",
            "raw_values_included": False,
        },
    )

    model = controls.build_runtime_gateway_controls_model(Path.cwd())

    assert model["ok"] is True
    assert model["surface"] == "studio_runtime_gateway_controls"
    assert model["component_count"] == 4
    assert model["authority"]["starts_gateways"] is True
    assert model["authority"]["writes_studio_preferences"] is True
    assert model["authority"]["writes_private_hermes_gateway_config"] is True
    assert model["security"]["secret_values_included"] is False
    assert model["hermes_gateway_config"]["raw_values_included"] is False
    hermes = next(item for item in model["runtimes"] if item["runtime_id"] == "hermes")
    assert [item["component_id"] for item in hermes["components"]] == ["daemon", "gateway"]
    gateway = next(item for item in hermes["components"] if item["component_id"] == "gateway")
    assert gateway["startup_modes"] == ["manual", "chaseos_start", "system_start"]


def test_runtime_gateway_controls_model_skips_process_probes_when_disabled(
    monkeypatch,
    tmp_path,
):
    def fake_lifecycle_record(runtime_id, vault):
        return {
            "platform": "windows",
            "lifecycle_mode": "manual",
            "coordination_watch": {"runtime_name": runtime_id},
            "startup_surfaces": {"gateway": {"target_path": str(tmp_path / "gateway.cmd")}},
        }

    def fake_live_status(vault, runtime_id, **kwargs):
        return {
            "pid": None,
            "pid_file": str(tmp_path / "runtime" / "lifecycle" / "run" / f"{runtime_id}.pid"),
            "pid_alive": False,
            "heartbeat_online": False,
            "heartbeat_freshness": "offline",
            "coordination_watch_running": False,
            "coordination_watch": {"pid": None},
            "gateway_port_online": False,
            "gateway_port_listening": False,
            "gateway_ports_checked": [],
            "blocked_reasons": [],
        }

    def fail_process_probe(*args, **kwargs):
        raise AssertionError("passive Settings load must not run process probes")

    monkeypatch.setattr(controls, "load_lifecycle_record", fake_lifecycle_record)
    monkeypatch.setattr(controls, "build_runtime_live_status", fake_live_status)
    monkeypatch.setattr(controls, "_gateway_target_path", lambda vault, runtime_id: None)
    monkeypatch.setattr(controls, "_system_start_registered", lambda vault, runtime_id: False)
    monkeypatch.setattr(controls, "_daemon_process_evidence", fail_process_probe)
    monkeypatch.setattr(controls, "_gateway_process_evidence", fail_process_probe)
    monkeypatch.setattr(
        controls,
        "build_hermes_gateway_config_control_model",
        lambda vault, probe_wsl=False: {
            "ok": True,
            "surface": "hermes_gateway_config_controls",
            "raw_values_included": False,
        },
    )

    model = controls.build_runtime_gateway_controls_model(tmp_path, probe_processes=False)

    assert model["ok"] is True
    for runtime in model["runtimes"]:
        for component in runtime["components"]:
            process_evidence = component["status"]["process_evidence"]
            assert process_evidence["skipped"] is True
            assert process_evidence["process_live"] is False


def test_studio_api_runtime_gateway_controls_uses_passive_process_model(
    monkeypatch,
    tmp_path,
):
    from runtime.studio.shell import api as shell_api

    captured: dict[str, object] = {}

    def fake_model(vault_root, *, probe_processes=True):
        captured["vault_root"] = vault_root
        captured["probe_processes"] = probe_processes
        return {
            "ok": True,
            "surface": "studio_runtime_gateway_controls",
            "security": {"sensitive_key_scan_passed": True},
            "runtimes": [],
        }

    monkeypatch.setattr(controls, "build_runtime_gateway_controls_model", fake_model)

    response = shell_api.StudioAPI(str(tmp_path)).get_runtime_gateway_controls()

    assert response["ok"] is True
    assert captured["vault_root"] == str(tmp_path)
    assert captured["probe_processes"] is False


def test_set_runtime_component_startup_mode_writes_chaseos_start_preference(tmp_path):
    result = controls.set_runtime_component_startup_mode(
        tmp_path,
        "hermes",
        "gateway",
        "chaseos_start",
    )

    prefs = controls.load_runtime_gateway_preferences(tmp_path)
    component = prefs["runtimes"]["hermes"]["gateway"]
    assert result["ok"] is True
    assert component["startup_mode"] == "chaseos_start"
    assert component["launch_on_chaseos_start"] is True
    assert component["approval_record"]["approval_recorded"] is True
    assert component["approval_record"]["starts_wsl"] is True
    assert result["approval_recorded"] is True
    assert Path(result["preferences_path"]).exists()


def test_set_gateway_system_mode_routes_to_startup_surface_toggle(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_toggle(vault, runtime_id, enable):
        captured.update(
            {
                "vault": vault,
                "runtime_id": runtime_id,
                "enable": enable,
            }
        )
        return {"ok": True, "intent": "enable" if enable else "disable", "approval_recorded": True}

    monkeypatch.setattr(controls, "_toggle_gateway_system_start", fake_toggle)

    result = controls.set_runtime_component_startup_mode(
        tmp_path,
        "openclaw",
        "gateway",
        "system_start",
        apply_system_start=True,
    )

    assert result["writes_host_startup"] is True
    assert result["system_start_action"]["approval_recorded"] is True
    assert captured == {
        "vault": tmp_path.resolve(),
        "runtime_id": "openclaw",
        "enable": True,
    }


def test_gateway_system_start_delegates_to_lifecycle_toggle(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_execute(runtime_id, surface_id, intent, *, confirm=False, requested_by="operator"):
        captured.update(
            {
                "runtime_id": runtime_id,
                "surface_id": surface_id,
                "intent": intent,
                "confirm": confirm,
                "requested_by": requested_by,
            }
        )
        return {
            "execution": {
                "launcher_path": str(tmp_path / "Startup" / "Hermes Gateway.cmd"),
                "target_path": str(tmp_path / ".hermes" / "gateway.cmd"),
                "actions": [{"action": "write-startup-folder-launcher"}],
            },
            "after_state": "registered",
            "approval_required": True,
            "approval_recorded": True,
            "approval_record": {"approval_kind": "inline_operator_confirmation"},
        }

    monkeypatch.setattr(controls, "execute_startup_surface_toggle", fake_execute)

    result = controls._toggle_gateway_system_start(tmp_path, "hermes", True)

    assert captured == {
        "runtime_id": "hermes",
        "surface_id": "gateway",
        "intent": "enable",
        "confirm": True,
        "requested_by": "studio-runtime-gateway-controls",
    }
    assert result["approval_required"] is True
    assert result["approval_recorded"] is True
    assert result["delegated_lifecycle_toggle"]["approval_record"]["approval_kind"] == "inline_operator_confirmation"


def test_launch_gateway_uses_declared_launcher(monkeypatch, tmp_path):
    launcher = tmp_path / "gateway.cmd"
    launcher.write_text("@echo off\n", encoding="utf-8")
    captured: dict[str, object] = {}

    def fake_popen(args, *, cwd=None, visible=True):
        captured.update({"args": args, "cwd": cwd, "visible": visible})
        return _FakeProcess()

    monkeypatch.setattr(controls, "_component_status", _not_running_status)
    monkeypatch.setattr(controls, "_gateway_target_path", lambda vault, runtime_id: str(launcher))

    result = controls.launch_runtime_component(
        tmp_path,
        "hermes",
        "gateway",
        popen=fake_popen,
    )

    assert result["status"] == "started"
    assert result["pid"] == _FakeProcess.pid
    assert captured["args"][:3] == ["cmd.exe", "/d", "/c"] if controls.os.name == "nt" else True
    assert captured["args"][-1] == str(launcher)
    assert captured["visible"] is False
    assert result["approval_required"] is True
    assert result["approval_recorded"] is True
    assert result["approval_record"]["starts_wsl"] is True
    assert result["writes_runtime_lifecycle"] is False


def test_launch_daemon_writes_pid_file(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_popen(args, *, cwd=None, visible=True):
        captured.update({"args": args, "cwd": cwd, "visible": visible})
        return _FakeProcess()

    monkeypatch.setattr(controls, "_component_status", _not_running_status)

    result = controls.launch_runtime_component(
        tmp_path,
        "openclaw",
        "daemon",
        popen=fake_popen,
    )

    pid_path = tmp_path / "runtime" / "lifecycle" / "run" / "openclaw-chat-daemon.pid"
    assert result["status"] == "started"
    assert pid_path.read_text(encoding="utf-8") == str(_FakeProcess.pid)
    assert "--runtime" in captured["args"]
    assert "openclaw" in captured["args"]
    assert captured["visible"] is False
    assert result["writes_runtime_lifecycle"] is True


def test_studio_api_launch_runtime_component_is_headless(monkeypatch, tmp_path):
    from runtime.studio.shell import api as shell_api

    captured: dict[str, object] = {}

    def fake_launch(vault_root, runtime_id, component_id, **kwargs):
        captured.update(
            {
                "vault_root": vault_root,
                "runtime_id": runtime_id,
                "component_id": component_id,
                **kwargs,
            }
        )
        return {
            "ok": True,
            "surface": "studio_runtime_gateway_controls",
            "status": "started",
            "runtime_id": runtime_id,
            "component_id": component_id,
        }

    monkeypatch.setattr(controls, "launch_runtime_component", fake_launch)

    response = shell_api.StudioAPI(str(tmp_path)).launch_runtime_component("hermes", "gateway")

    assert response["ok"] is True
    assert captured["visible"] is False
    assert captured["requested_by"] == "studio-runtime-gateway-controls"


def test_daemon_status_requires_process_or_coordination_watch_not_heartbeat_only(monkeypatch, tmp_path):
    monkeypatch.setattr(
        controls,
        "build_runtime_live_status",
        lambda vault, runtime_id, **kwargs: {
            "pid": None,
            "pid_file": str(tmp_path / "runtime" / "lifecycle" / "run" / "hermes-chat-daemon.pid"),
            "pid_alive": False,
            "heartbeat_online": True,
            "heartbeat_freshness": "fresh",
            "coordination_watch_running": False,
            "coordination_watch": {"pid": None},
            "blocked_reasons": [],
        },
    )
    monkeypatch.setattr(
        controls,
        "_daemon_process_evidence",
        lambda runtime_id: {
            "process_probe_available": True,
            "process_count": 0,
            "processes": [],
            "process_live": False,
        },
    )

    status = controls._component_status(tmp_path, "hermes", "daemon")

    assert status["running"] is False
    assert status["status_source"] == "none"
    assert status["heartbeat_freshness"] == "fresh"


def test_daemon_status_prefers_coordination_watch_pid(monkeypatch, tmp_path):
    monkeypatch.setattr(
        controls,
        "build_runtime_live_status",
        lambda vault, runtime_id, **kwargs: {
            "pid": 111,
            "pid_file": str(tmp_path / "runtime" / "lifecycle" / "run" / "hermes-chat-daemon.pid"),
            "pid_alive": False,
            "heartbeat_online": False,
            "heartbeat_freshness": "offline",
            "coordination_watch_running": True,
            "coordination_watch": {"pid": 222},
            "blocked_reasons": [],
        },
    )
    monkeypatch.setattr(
        controls,
        "_daemon_process_evidence",
        lambda runtime_id: {
            "process_probe_available": True,
            "process_count": 1,
            "processes": [{"pid": 333, "name": "python.exe", "command": "runtime daemon"}],
            "process_live": True,
        },
    )

    status = controls._component_status(tmp_path, "hermes", "daemon")

    assert status["running"] is True
    assert status["status_source"] == "coordination_watch"
    assert status["pid"] == 222
    assert status["pid_file_pid"] == 111


def test_apply_chaseos_start_preferences_launches_selected_components(monkeypatch, tmp_path):
    controls.set_runtime_component_startup_mode(tmp_path, "hermes", "gateway", "chaseos_start")
    controls.set_runtime_component_startup_mode(tmp_path, "openclaw", "daemon", "manual")
    launched: list[tuple[str, str, bool]] = []

    def fake_launch(vault_root, runtime_id, component_id, *, visible=True, dry_run=False):
        launched.append((runtime_id, component_id, visible))
        return {
            "ok": True,
            "status": "started",
            "runtime_id": runtime_id,
            "component_id": component_id,
            "dry_run": dry_run,
        }

    monkeypatch.setattr(controls, "launch_runtime_component", fake_launch)

    result = controls.apply_chaseos_start_preferences(tmp_path)

    assert result["launch_count"] == 1
    assert launched == [("hermes", "gateway", False)]


def test_apply_chaseos_start_preferences_skips_recent_attempt_without_spawning(monkeypatch, tmp_path):
    controls.set_runtime_component_startup_mode(tmp_path, "hermes", "gateway", "chaseos_start")
    state = controls.load_runtime_gateway_preferences(tmp_path)
    state["runtimes"]["hermes"]["gateway"]["last_launch_attempt_at_utc"] = controls._now_utc()
    controls._write_preferences(tmp_path.resolve(), state)

    def fail_launch(*args, **kwargs):
        raise AssertionError("recent ChaseOS-start retry must not spawn another terminal")

    monkeypatch.setattr(controls, "launch_runtime_component", fail_launch)

    result = controls.apply_chaseos_start_preferences(tmp_path)

    assert result["launch_count"] == 1
    assert result["starts_process"] is False
    assert result["launches"][0]["status"] == "recent_launch_attempt_skipped"
    assert result["launches"][0]["starts_process"] is False


def test_apply_hermes_gateway_config_control_adds_operator(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_config_action(action, **kwargs):
        captured.update({"action": action, **kwargs})
        return {
            "ok": True,
            "action": "apply",
            "allowed_user_addition_count": 1,
            "redacted_status_only": True,
        }

    monkeypatch.setattr(controls, "run_hermes_gateway_config_action", fake_config_action)

    result = controls.apply_hermes_gateway_config_control(
        tmp_path,
        action="add_chaseos_operator",
    )

    assert result["ok"] is True
    assert captured["action"] == "apply"
    assert captured["use_chaseos_operator"] is True
    assert captured["confirm"] is True
    assert captured["requested_by"] == "studio-runtime-gateway-controls"


def test_apply_hermes_gateway_config_control_status_does_not_apply(monkeypatch, tmp_path):
    captured: dict[str, object] = {}

    def fake_config_action(action, **kwargs):
        captured.update({"action": action, **kwargs})
        return {"ok": True, "action": "status", "redacted_status_only": True}

    monkeypatch.setattr(controls, "run_hermes_gateway_config_action", fake_config_action)

    result = controls.apply_hermes_gateway_config_control(tmp_path, action="check_status")

    assert result["ok"] is True
    assert captured["action"] == "status"
    assert "use_chaseos_operator" not in captured
