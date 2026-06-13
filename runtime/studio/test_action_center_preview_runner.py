from __future__ import annotations

import subprocess
from pathlib import Path

from runtime.studio import action_center_preview_runner


def test_action_center_preview_runner_uses_hidden_window_flag(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(action_center_preview_runner.os, "name", "nt", raising=False)
    monkeypatch.setattr(action_center_preview_runner.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)

    def fake_run(args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(args, 0, stdout='{"ok": true, "summary": {}}', stderr="")

    monkeypatch.setattr(action_center_preview_runner.subprocess, "run", fake_run)

    result = action_center_preview_runner._run_preview(("studio", "noop"), tmp_path, 2)

    assert result["returncode"] == 0
    assert captured["kwargs"]["creationflags"] == 0x08000000
    assert captured["args"][:3] == (action_center_preview_runner.sys.executable, "-m", "runtime.cli.main")
