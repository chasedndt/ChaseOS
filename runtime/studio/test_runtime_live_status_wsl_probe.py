"""Regression tests for Studio runtime WSL probing.

The Chat page polls runtime availability; WSL process probing must not create
visible or transient terminal windows when it is explicitly used by diagnostics.
"""
from __future__ import annotations

import subprocess


def test_wsl_process_probe_uses_create_no_window_on_windows(monkeypatch) -> None:
    import runtime.studio.runtime_live_status as live_status

    captured: dict[str, object] = {}

    monkeypatch.setattr(live_status.os, "name", "nt", raising=False)
    monkeypatch.setattr(live_status.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)

    def fake_run(args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(args, 0, stdout=" 123 hermes gateway\n", stderr="")

    monkeypatch.setattr(live_status.subprocess, "run", fake_run)

    result = live_status._wsl_process_status("hermes")

    assert result["process_alive"] is True
    assert captured["args"] == ["wsl.exe", "--", "ps", "-eo", "pid=,args="]
    assert captured["kwargs"]["creationflags"] == 0x08000000


def test_wsl_process_probe_remains_unsupported_off_windows(monkeypatch) -> None:
    import runtime.studio.runtime_live_status as live_status

    monkeypatch.setattr(live_status.os, "name", "posix", raising=False)
    result = live_status._wsl_process_status("hermes")

    assert result["status"] == "unsupported"
    assert result["process_alive"] is False
