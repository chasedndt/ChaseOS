"""Tests for packaged Studio WebView2 diagnostics."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from runtime.studio import packaged_app_webview2_diagnostic as diagnostic


class _FakeCompletedProcess:
    returncode = 0
    stdout = "{}"
    stderr = ""


def test_webview2_diagnostic_blocks_when_runtime_not_detected(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    monkeypatch.setattr(
        diagnostic,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(diagnostic, "_module_available", lambda _name: True)
    monkeypatch.setattr(diagnostic, "_package_version", lambda _name: "6.2.1")
    monkeypatch.setattr(
        diagnostic,
        "_detect_windows_webview2_runtime",
        lambda: {"runtime_detected": False, "status": "not_detected", "registry_clients": [], "runtime_files": []},
    )
    monkeypatch.setattr(diagnostic.platform, "system", lambda: "Windows")

    report = diagnostic.build_packaged_app_webview2_diagnostic(tmp_path, executable_path=exe)

    assert report["ok"] is False
    assert report["status"] == "blocked_webview2_diagnostic"
    assert "WebView2 runtime was not detected by registry/file probe." in report["blockers"]
    assert report["next_recommended_pass"] == "pass10b-install-or-repair-webview2-runtime"
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["webview2_runtime_detected"]["ok"] is False
    assert report["authority"]["installs_webview2"] is False


def test_webview2_diagnostic_passes_workspace_user_data_to_visual_probe(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "ChaseOS-Studio.exe"
    exe.write_bytes(b"fake exe")
    captured_kwargs = {}
    monkeypatch.setattr(
        diagnostic,
        "build_studio_local_packaging_proof",
        lambda _vault: {"status": "ready", "outputs": {"executable_exists": True, "executable_sha256": "abc"}},
    )
    monkeypatch.setattr(diagnostic, "_module_available", lambda _name: True)
    monkeypatch.setattr(diagnostic, "_package_version", lambda _name: "6.2.1")
    monkeypatch.setattr(
        diagnostic,
        "_detect_windows_webview2_runtime",
        lambda: {"runtime_detected": True, "status": "detected", "registry_clients": [], "runtime_files": []},
    )

    def fake_visual_qa(*_args, **kwargs):
        captured_kwargs.update(kwargs)
        return {
            "ok": False,
            "status": "blocked_packaged_app_visual_qa",
            "launch": {
                "runtime_error": {
                    "status": "webview2_initialization_failed",
                    "blocked": True,
                }
            },
            "screenshot": {"exists": False},
        }

    monkeypatch.setattr(diagnostic, "build_packaged_app_visual_qa", fake_visual_qa)

    report = diagnostic.build_packaged_app_webview2_diagnostic(
        tmp_path,
        executable_path=exe,
        probe_launch=True,
        user_data_root="webview2-user-data",
    )

    assert captured_kwargs["env_overrides"]["WEBVIEW2_USER_DATA_FOLDER"] == str(tmp_path / "webview2-user-data")
    assert captured_kwargs["env_overrides"]["TEMP"] == str(tmp_path / ".pytest_tmp_env" / "studio-webview2-diagnostic" / "temp")
    assert captured_kwargs["env_overrides"]["TMP"] == str(tmp_path / ".pytest_tmp_env" / "studio-webview2-diagnostic" / "temp")
    assert report["status"] == "blocked_webview2_initialization_with_workspace_runtime_dirs"
    assert "WebView2 initialization still fails with workspace-owned WebView2 user-data and temp folders." in report["blockers"]
    assert report["next_recommended_pass"] == "pass10b-system-temp-permission-or-webview2-policy-check"


def test_temp_write_probe_creates_child_with_os_mkdir(monkeypatch, tmp_path: Path) -> None:
    calls: list[Path] = []
    original_mkdir = diagnostic.os.mkdir
    monkeypatch.setattr(diagnostic.tempfile, "gettempdir", lambda: str(tmp_path))

    def tracked_mkdir(path: str | bytes | os.PathLike, mode: int = 0o777, *, dir_fd: int | None = None) -> None:
        selected = Path(path)
        if selected.name.startswith("chaseos-webview2-diagnostic-"):
            calls.append(selected)
        if dir_fd is None:
            original_mkdir(path, mode)
        else:  # pragma: no cover - pathlib does not use dir_fd in this probe.
            original_mkdir(path, mode, dir_fd=dir_fd)

    monkeypatch.setattr(diagnostic.os, "mkdir", tracked_mkdir)

    probe = diagnostic._temp_write_probe()

    assert probe["writable"] is True
    assert probe["cleanup_ok"] is True
    assert Path(probe["path"]).exists() is False
    assert calls


def test_webview2_diagnostic_rejects_user_data_root_outside_vault(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-webview2-user-data"

    with pytest.raises(ValueError, match="user-data root must stay inside"):
        diagnostic.build_packaged_app_webview2_diagnostic(
            tmp_path,
            user_data_root=outside,
        )


def test_webview2_diagnostic_powershell_probe_uses_hidden_window(monkeypatch) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(diagnostic.os, "name", "nt", raising=False)
    monkeypatch.setattr(diagnostic.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)

    def fake_run(_args, **kwargs):
        captured.update(kwargs)
        return _FakeCompletedProcess()

    monkeypatch.setattr(diagnostic.subprocess, "run", fake_run)

    result = diagnostic._run_powershell_json("$true")

    assert result["ok"] is True
    assert captured["shell"] is False
    assert captured["creationflags"] == 0x08000000


def test_webview2_diagnostic_writer_rejects_report_root_outside_vault(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-webview2-report"

    with pytest.raises(ValueError, match="report root must stay inside"):
        diagnostic.write_packaged_app_webview2_diagnostic(
            tmp_path,
            {"ok": False, "status": "blocked", "checks": [], "authority": {}},
            report_root=outside,
        )


def test_webview2_diagnostic_parser_exposes_probe_launch() -> None:
    from runtime.cli.main import _build_parser

    parser = _build_parser()
    args = parser.parse_args(
        [
            "studio",
            "packaged-app-webview2-diagnostic",
            "--probe-launch",
            "--settle-seconds",
            "2",
            "--window-timeout-seconds",
            "3",
            "--terminate-timeout-seconds",
            "4",
            "--write-report",
            "--report-slug",
            "diag-test",
        ]
    )

    assert args.probe_launch is True
    assert args.settle_seconds == 2
    assert args.window_timeout_seconds == 3
    assert args.terminate_timeout_seconds == 4
    assert args.write_report is True
    assert args.report_slug == "diag-test"
