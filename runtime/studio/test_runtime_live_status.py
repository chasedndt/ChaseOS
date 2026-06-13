"""Tests for Studio read-only runtime liveness detection."""

from __future__ import annotations

import json
import socket
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from runtime.studio.service import StudioService
from runtime.studio.runtime_live_status import (
    build_runtime_live_status,
    candidate_gateway_ports,
)


def _listening_socket() -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    sock.listen(1)
    return sock


def _write_heartbeat(vault: Path, runtime_name: str) -> None:
    bus = vault / "runtime" / "agent_bus"
    bus.mkdir(parents=True)
    conn = sqlite3.connect(str(bus / "agent_bus.sqlite"))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS heartbeats "
        "(id INTEGER PRIMARY KEY, runtime TEXT, runtime_instance_id TEXT, "
        "heartbeat_scope TEXT, control_surface TEXT, control_surface_key TEXT, "
        "last_seen TEXT, status TEXT)"
    )
    conn.execute(
        "INSERT INTO heartbeats (runtime, last_seen, status) VALUES (?, ?, ?)",
        (runtime_name, datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "active"),
    )
    conn.commit()
    conn.close()


def test_env_gateway_port_marks_hermes_gateway_live_without_dispatch_ready(tmp_path: Path, monkeypatch) -> None:
    with _listening_socket() as sock:
        port = sock.getsockname()[1]
        monkeypatch.setenv("CHASEOS_HERMES_PORT", str(port))

        status = build_runtime_live_status(tmp_path, "hermes")

    assert status["status"] == "running"
    assert status["status_source"] == "gateway_port"
    assert status["gateway_port_listening"] == port
    assert status["gateway_port_online"] is True
    assert status["heartbeat_online"] is False
    assert status["dispatch_ready"] is False
    assert status["coordination_state"] == "gateway_live_heartbeat_required"


def test_fresh_agent_bus_heartbeat_marks_dispatch_ready(tmp_path: Path) -> None:
    _write_heartbeat(tmp_path, "Hermes")

    status = build_runtime_live_status(tmp_path, "hermes", probe_wsl_processes=True)

    assert status["status"] == "running"
    assert status["status_source"] == "agent_bus_heartbeat"
    assert status["heartbeat_online"] is True
    assert status["dispatch_ready"] is True
    assert status["runtime_can_receive_chat"] is True


def test_runtime_registry_port_is_candidate(tmp_path: Path) -> None:
    registry_dir = tmp_path / "runtime" / "lifecycle"
    registry_dir.mkdir(parents=True)
    (registry_dir / "runtime-registry.json").write_text(
        json.dumps({"runtimes": {"hermes": {"gateway_port": 9119}}}),
        encoding="utf-8",
    )

    assert 9119 in candidate_gateway_ports(tmp_path, "hermes")


def test_runtime_run_state_port_is_candidate_and_marks_gateway_live(tmp_path: Path) -> None:
    run_dir = tmp_path / "runtime" / "lifecycle" / "run"
    run_dir.mkdir(parents=True)
    with _listening_socket() as sock:
        port = sock.getsockname()[1]
        (run_dir / "hermes-daemon.log").write_text(
            f"Hermes gateway listening on http://127.0.0.1:{port}/health\n",
            encoding="utf-8",
        )

        status = build_runtime_live_status(tmp_path, "hermes")

    assert port in candidate_gateway_ports(tmp_path, "hermes")
    assert status["status"] == "running"
    assert status["status_source"] == "gateway_port"
    assert status["gateway_port_listening"] == port
    assert status["gateway_port_online"] is True
    assert status["dispatch_ready"] is False


def test_wsl_process_marks_runtime_running_without_dispatch_ready(tmp_path: Path, monkeypatch) -> None:
    import runtime.studio.runtime_live_status as live_status

    (tmp_path / "runtime" / "lifecycle").mkdir(parents=True)
    monkeypatch.setattr(
        live_status,
        "_wsl_process_status",
        lambda runtime_id: {
            "status": "process_found",
            "process_alive": runtime_id == "hermes",
            "pid": 822,
            "command_preview": "<WSL_HOME>/.local/bin/hermes gateway",
        },
    )

    status = build_runtime_live_status(tmp_path, "hermes", probe_wsl_processes=True)

    assert status["status"] == "running"
    assert status["status_source"] == "wsl_process"
    assert status["wsl_process_alive"] is True
    assert status["heartbeat_online"] is False
    assert status["gateway_port_online"] is False
    assert status["dispatch_ready"] is False
    assert status["coordination_state"] == "wsl_process_live_heartbeat_required"
    assert "wsl_runtime_process_running_without_gateway_port" in status["blocked_reasons"]


def test_runtime_live_status_does_not_probe_wsl_by_default(tmp_path: Path, monkeypatch) -> None:
    import runtime.studio.runtime_live_status as live_status

    (tmp_path / "runtime" / "lifecycle").mkdir(parents=True)

    def fail_if_called(_runtime_id: str) -> dict:
        raise AssertionError("Runtime live status must not spawn WSL probes by default")

    monkeypatch.setattr(live_status, "_wsl_process_status", fail_if_called)

    status = build_runtime_live_status(tmp_path, "hermes")

    assert status["status"] == "not_running"
    assert status["wsl_process_probe_enabled"] is False
    assert status["wsl_process"]["status"] == "skipped"


def test_status_probe_is_read_only_when_no_runtime_files_exist(tmp_path: Path) -> None:
    before = set(tmp_path.rglob("*"))

    status = build_runtime_live_status(tmp_path, "openclaw")

    after = set(tmp_path.rglob("*"))
    assert status["read_only"] is True
    assert status["status"] == "not_running"
    assert before == after


def test_get_daemon_status_uses_gateway_liveness_for_openclaw(tmp_path: Path, monkeypatch) -> None:
    from runtime.studio.shell.api import StudioAPI

    with _listening_socket() as sock:
        port = sock.getsockname()[1]
        monkeypatch.setenv("OPENCLAW_GATEWAY_PORT", str(port))
        result = StudioAPI(tmp_path).get_daemon_status("openclaw")

    assert result["ok"] is True
    assert result["data"]["status"] == "running"
    assert result["data"]["status_source"] == "gateway_port"
    assert result["data"]["gateway_port_listening"] == port


def test_get_daemon_status_is_passive_for_chat_page_polling(tmp_path: Path, monkeypatch) -> None:
    import runtime.studio.runtime_live_status as live_status
    from runtime.studio.shell.api import StudioAPI

    (tmp_path / "runtime" / "lifecycle").mkdir(parents=True)

    def fail_if_called(_runtime_id: str) -> dict:
        raise AssertionError("Chat/runtime page polling must not spawn wsl.exe probes")

    monkeypatch.setattr(live_status, "_wsl_process_status", fail_if_called)

    result = StudioAPI(tmp_path).get_daemon_status("hermes")

    assert result["ok"] is True
    assert result["data"]["wsl_process_probe_enabled"] is False
    assert result["data"]["process_probe_enabled"] is False


def test_stale_coordination_watch_state_is_visible_blocker(tmp_path: Path) -> None:
    run_dir = tmp_path / "runtime" / "lifecycle" / "run"
    run_dir.mkdir(parents=True)
    (run_dir / "hermes-coordination-watch.json").write_text(
        json.dumps(
            {
                "runtime": "hermes",
                "pid": 999999,
                "status": "starting",
                "started_at": "2026-05-21T11:48:54Z",
                "interval_seconds": 30,
            }
        ),
        encoding="utf-8",
    )

    status = build_runtime_live_status(tmp_path, "hermes")

    assert status["coordination_watch_state_stale"] is True
    assert status["coordination_watch"]["state_present"] is True
    assert status["coordination_watch"]["pid"] == 999999
    assert "coordination_watch_state_stale" in status["blocked_reasons"]


def test_done_coordination_watch_state_is_not_treated_as_stale(tmp_path: Path) -> None:
    run_dir = tmp_path / "runtime" / "lifecycle" / "run"
    run_dir.mkdir(parents=True)
    (run_dir / "openclaw-coordination-watch.json").write_text(
        json.dumps(
            {
                "runtime": "openclaw",
                "pid": 999999,
                "status": "done",
                "started_at": "2026-05-21T11:48:54Z",
                "ended_at": "2026-05-21T11:49:01Z",
                "cycles_run": 1,
            }
        ),
        encoding="utf-8",
    )

    status = build_runtime_live_status(tmp_path, "openclaw")

    assert status["coordination_watch_state_stale"] is False
    assert status["coordination_watch"]["status"] == "done"
    assert "coordination_watch_state_stale" not in status["blocked_reasons"]


def test_studio_runtime_daemon_command_binds_selected_vault(tmp_path: Path) -> None:
    from runtime.studio.shell.api import StudioAPI

    command = StudioAPI(tmp_path)._runtime_daemon_command("hermes", synthesize=True)

    assert command[:5] == [command[0], "-m", "runtime.cli.main", "runtime", "daemon"]
    assert "--runtime" in command
    assert command[command.index("--runtime") + 1] == "hermes"
    assert "--vault-root" in command
    assert command[command.index("--vault-root") + 1] == str(tmp_path.resolve())
    assert "--synthesize" in command


def _approved_daemon_start_id(api, vault: Path, runtime_id: str = "hermes") -> str:
    requested = api.start_runtime_daemon(runtime_id)
    approval_id = requested["approval"]["approval_id"]
    StudioService(vault).approve(approval_id, reviewed_by="test")
    return approval_id


def test_start_runtime_daemon_skips_spawn_when_selected_vault_heartbeat_is_fresh(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from runtime.studio.shell.api import StudioAPI

    _write_heartbeat(tmp_path, "Hermes")
    api = StudioAPI(tmp_path)
    approval_id = _approved_daemon_start_id(api, tmp_path)

    def fail_popen(*_args, **_kwargs):
        raise AssertionError("fresh selected-vault heartbeat must not spawn a duplicate daemon")

    monkeypatch.setattr(subprocess, "Popen", fail_popen)
    result = api.start_runtime_daemon("hermes", approval_id=approval_id)

    assert result["ok"] is True
    assert result["data"]["status"] == "already_running"
    assert result["data"]["status_source"] == "agent_bus_heartbeat"
    assert result["data"]["dispatch_ready"] is True


def test_start_runtime_daemon_cleans_stale_selected_vault_watch_state_before_spawn(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from runtime.studio.shell.api import StudioAPI

    run_dir = tmp_path / "runtime" / "lifecycle" / "run"
    run_dir.mkdir(parents=True)
    stale_state = run_dir / "openclaw-coordination-watch.json"
    stale_state.write_text(
        json.dumps(
            {
                "runtime": "openclaw",
                "pid": 999999,
                "status": "starting",
                "started_at": "2026-05-21T11:48:54Z",
                "interval_seconds": 30,
            }
        ),
        encoding="utf-8",
    )

    captured: dict[str, object] = {}

    class FakeProcess:
        pid = 43210

    def fake_popen(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["cwd"] = kwargs.get("cwd")
        return FakeProcess()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    api = StudioAPI(tmp_path)
    approval_id = _approved_daemon_start_id(api, tmp_path, "openclaw")
    result = api.start_runtime_daemon("openclaw", approval_id=approval_id)

    assert result["ok"] is True
    assert result["data"]["status"] == "started"
    assert result["data"]["pid"] == 43210
    assert result["data"]["stale_coordination_state_cleaned"] is True
    assert result["data"]["cleaned_coordination_state_paths"] == [str(stale_state)]
    assert result["data"]["vault_root"] == str(tmp_path.resolve())
    assert captured["cmd"][captured["cmd"].index("--vault-root") + 1] == str(tmp_path.resolve())
    assert captured["cwd"] == str(tmp_path.resolve())
    assert not stale_state.exists()
