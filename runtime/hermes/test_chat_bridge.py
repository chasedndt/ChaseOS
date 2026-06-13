from __future__ import annotations

import shutil
import subprocess


def test_hermes_chat_bridge_calls_hermes_cli_without_shell(monkeypatch, tmp_path):
    from runtime.hermes.chat_bridge import call_hermes_chat_bridge

    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0, stdout="hello\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(shutil, "which", lambda name: name if name == "hermes" else None)

    result = call_hermes_chat_bridge(
        "hi",
        session_id="runtime-ops-hermes-chat",
        vault_root=tmp_path,
        timeout_seconds=12,
    )

    assert result["ok"] is True
    assert result["text"] == "hello"
    assert result["runtime"] == "Hermes"
    assert result["session_id"] == "runtime-ops-hermes-chat"
    assert result["provider_detail_redacted"] is True
    cmd, kwargs = calls[0]
    assert cmd[0] == "hermes"
    assert cmd[1] == "-z"
    assert "hi" in cmd[2]
    assert "--toolsets" in cmd
    assert "safe" in cmd
    assert "--ignore-rules" in cmd
    assert kwargs["shell"] is False
    assert kwargs["timeout"] == 12
    assert kwargs["cwd"] == str(tmp_path)
    assert kwargs["env"]["HERMES_QUIET"] == "1"


def test_hermes_chat_bridge_sanitizes_parent_gateway_session_env(monkeypatch, tmp_path):
    from runtime.hermes.chat_bridge import call_hermes_chat_bridge

    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0, stdout="hello\n", stderr="")

    monkeypatch.setenv("HERMES_SESSION_ID", "gateway-session")
    monkeypatch.setenv("HERMES_SESSION_KEY", "secret-session-key")
    monkeypatch.setenv("HERMES_SESSION_CHAT_ID", "chat-id")
    monkeypatch.setenv("HERMES_GATEWAY_BUSY_INPUT_MODE", "interrupt")
    monkeypatch.setenv("HERMES_EXEC_ASK", "1")
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(shutil, "which", lambda name: name if name == "hermes" else None)

    result = call_hermes_chat_bridge("hi", vault_root=tmp_path)

    assert result["ok"] is True
    env = calls[0][1]["env"]
    assert env["HERMES_QUIET"] == "1"
    assert "HERMES_SESSION_ID" not in env
    assert "HERMES_SESSION_KEY" not in env
    assert "HERMES_SESSION_CHAT_ID" not in env
    assert "HERMES_GATEWAY_BUSY_INPUT_MODE" not in env
    assert "HERMES_EXEC_ASK" not in env


def test_hermes_chat_bridge_returns_safe_error_on_timeout(monkeypatch, tmp_path):
    from runtime.hermes.chat_bridge import call_hermes_chat_bridge

    def fake_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(shutil, "which", lambda name: name if name == "hermes" else None)

    result = call_hermes_chat_bridge("hi", vault_root=tmp_path, timeout_seconds=1)

    assert result["ok"] is False
    assert result["error"] == "backend_timeout"
    assert "Hermes" in result["safe_message"]
    assert "hi" not in result["safe_message"]


def test_hermes_chat_bridge_builds_wsl_command_when_windows_has_no_hermes(monkeypatch, tmp_path):
    from runtime.hermes import chat_bridge

    monkeypatch.setattr(chat_bridge.os, "name", "nt")
    monkeypatch.setattr(chat_bridge.shutil, "which", lambda name: None)
    monkeypatch.setattr(chat_bridge, "_windows_path_to_wsl", lambda path, distro="Ubuntu": "/mnt/c/vault")
    monkeypatch.setattr(chat_bridge, "_wsl_home", lambda distro="Ubuntu": "/home/tester")

    cmd, cwd, label = chat_bridge._hermes_command_for_host(tmp_path, "prompt text")

    assert cmd[:4] == ["wsl.exe", "-d", "Ubuntu", "--"]
    assert "env" in cmd
    assert "hermes" in cmd
    assert "HERMES_HOME=/home/tester/runtimes/hermes-home" in cmd
    assert "-z" in cmd
    assert "prompt text" in cmd
    assert "--toolsets" in cmd
    assert "safe" in cmd
    assert cwd == str(tmp_path)
    assert label == "hermes_wsl_cli_z"


def test_hermes_chat_bridge_prefers_configured_windows_cli(monkeypatch, tmp_path):
    from runtime.hermes import chat_bridge

    monkeypatch.setenv("CHASEOS_HERMES_CLI", "C:/Hermes/hermes.exe")
    monkeypatch.setattr(chat_bridge.shutil, "which", lambda name: None)

    cmd, cwd, label = chat_bridge._hermes_command_for_host(tmp_path, "prompt text")

    assert cmd[0] == "C:/Hermes/hermes.exe"
    assert "-z" in cmd
    assert "prompt text" in cmd
    assert cwd == str(tmp_path)
    assert label == "hermes_configured_cli_z"


def test_hermes_chat_bridge_uses_wsl_shell_bridge_when_preflight_is_denied(monkeypatch, tmp_path):
    from runtime.hermes import chat_bridge

    monkeypatch.setattr(chat_bridge.os, "name", "nt")
    monkeypatch.setattr(chat_bridge.shutil, "which", lambda name: None)
    monkeypatch.setattr(chat_bridge, "_windows_path_to_wsl", lambda path, distro="Ubuntu": None)
    monkeypatch.setattr(chat_bridge, "_wsl_home", lambda distro="Ubuntu": None)

    cmd, cwd, label = chat_bridge._hermes_command_for_host(tmp_path, "prompt text")

    assert cmd[:4] == ["wsl.exe", "-d", "Ubuntu", "--"]
    assert "sh" in cmd
    assert "-lc" in cmd
    script = cmd[cmd.index("-lc") + 1]
    assert "prompt text" not in script
    assert "prompt text" in cmd
    assert cwd == str(tmp_path)
    assert label == "hermes_wsl_shell_bridge_z"


def test_hermes_runtime_chat_uses_native_bridge_before_shared_adapter(monkeypatch, tmp_path):
    from runtime.workflows import hermes_watch

    monkeypatch.setattr(
        hermes_watch,
        "call_hermes_chat_bridge",
        lambda message, session_id="", vault_root=None, timeout_seconds=90: {
            "ok": True,
            "text": "hello",
            "runtime": "Hermes",
            "session_id": session_id,
            "provider_detail_redacted": True,
        },
    )

    assert hermes_watch._hermes_runtime_chat("hi", session_id="s1", vault_root=tmp_path) == "hello"


def test_hermes_runtime_chat_result_surfaces_bridge_blocker(monkeypatch, tmp_path):
    from runtime.execution_adapters import execute as execution_execute
    from runtime.workflows import hermes_watch

    monkeypatch.setattr(
        hermes_watch,
        "call_hermes_chat_bridge",
        lambda message, session_id="", vault_root=None, timeout_seconds=90: {
            "ok": False,
            "error": "backend_nonzero_exit",
            "safe_message": "Hermes chat backend exited without a usable live reply.",
            "exit_code": 4294967295,
            "stdout_preview": "Access is denied. Error code: Wsl/Service/E_ACCESSDENIED",
            "bridge": "hermes_wsl_shell_bridge_z",
        },
    )

    def fail_synthesis(**_kwargs):
        raise RuntimeError("adapter unavailable")

    monkeypatch.setattr(execution_execute, "execute_synthesis", fail_synthesis)

    reply, blocker = hermes_watch._hermes_runtime_chat_result("hi", session_id="s1", vault_root=tmp_path)

    assert reply is None
    assert "Bridge detail" in blocker
    assert "Access is denied" in blocker
    assert "bridge=hermes_wsl_shell_bridge_z" in blocker
