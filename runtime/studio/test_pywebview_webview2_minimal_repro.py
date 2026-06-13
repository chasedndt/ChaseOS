"""Tests for the Pass 10B minimal PyWebView/WebView2 repro."""

from __future__ import annotations

from pathlib import Path

import pytest

from runtime.studio import pywebview_webview2_minimal_repro as repro


def test_minimal_repro_ready_to_build_without_mutation(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(repro, "_module_available", lambda _name: True)

    report = repro.build_pywebview_webview2_minimal_repro(tmp_path)

    assert report["ok"] is True
    assert report["status"] == "minimal_pywebview_webview2_repro_ready_to_build"
    assert report["build_inputs"]["written"] is False
    assert Path(tmp_path / repro.DEFAULT_OUTPUT_ROOT).exists() is False
    assert report["next_recommended_pass"] == "pass10b-pywebview-webview2-minimal-repro"


def test_minimal_repro_execute_build_writes_source_spec_and_executable(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(repro, "_module_available", lambda _name: True)

    def fake_run_command(args, *, cwd: Path, timeout_seconds: float):
        expected = tmp_path / "out" / "dist" / repro.APP_NAME / f"{repro.APP_NAME}.exe"
        expected.parent.mkdir(parents=True, exist_ok=True)
        expected.write_bytes(b"fake exe")
        return {"ok": True, "returncode": 0, "stdout_tail": "", "stderr_tail": "", "timed_out": False}

    monkeypatch.setattr(repro, "_run_command", fake_run_command)
    monkeypatch.setattr(repro.sys, "platform", "win32")

    report = repro.build_pywebview_webview2_minimal_repro(
        tmp_path,
        execute_build=True,
        output_root="out",
    )

    assert report["ok"] is True
    assert report["status"] == "minimal_pywebview_webview2_repro_ready_for_probe"
    assert report["build_inputs"]["written"] is True
    assert (tmp_path / "out" / "src" / "minimal_pywebview_webview2_repro.py").is_file()
    assert (tmp_path / "out" / "minimal-pywebview-webview2-repro.spec").is_file()
    assert report["outputs"]["executable_exists"] is True
    assert report["authority"]["builds_minimal_packaged_executable"] is True


def test_minimal_repro_visual_probe_success_routes_to_studio_differential(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "out" / "dist" / repro.APP_NAME / f"{repro.APP_NAME}.exe"
    exe.parent.mkdir(parents=True, exist_ok=True)
    exe.write_bytes(b"fake exe")
    captured = {}
    monkeypatch.setattr(repro, "_module_available", lambda _name: True)
    monkeypatch.setattr(repro.sys, "platform", "win32")

    def fake_visual_probe(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return {
            "ok": True,
            "status": "packaged_app_visual_qa_complete",
            "launch": {"runtime_error": {"blocked": False, "status": "not_applicable"}},
            "screenshot": {"exists": True, "path": "out/minimal-repro-screenshot.png"},
            "termination": {"attempted": True, "terminated": True},
        }

    monkeypatch.setattr(repro, "build_packaged_app_visual_qa", fake_visual_probe)

    report = repro.build_pywebview_webview2_minimal_repro(
        tmp_path,
        output_root="out",
        probe_launch=True,
        webview2_user_data_root="runtime/user-data",
        temp_root="runtime/temp",
    )

    assert report["ok"] is True
    assert report["status"] == "minimal_pywebview_webview2_repro_visual_qa_complete"
    assert report["next_recommended_pass"] == "pass10b-studio-shell-webview-startup-differential"
    assert captured["kwargs"]["webview2_user_data_root"] == "runtime/user-data"
    assert captured["kwargs"]["temp_root"] == "runtime/temp"


def test_minimal_repro_visual_probe_runtime_failure_routes_to_host_remediation(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "out" / "dist" / repro.APP_NAME / f"{repro.APP_NAME}.exe"
    exe.parent.mkdir(parents=True, exist_ok=True)
    exe.write_bytes(b"fake exe")
    monkeypatch.setattr(repro, "_module_available", lambda _name: True)
    monkeypatch.setattr(repro.sys, "platform", "win32")
    monkeypatch.setattr(
        repro,
        "build_packaged_app_visual_qa",
        lambda *_args, **_kwargs: {
            "ok": False,
            "status": "blocked_packaged_app_visual_qa",
            "launch": {"runtime_error": {"blocked": True, "status": "webview2_initialization_failed"}},
            "screenshot": {"exists": False},
            "termination": {"attempted": True, "terminated": True},
        },
    )

    report = repro.build_pywebview_webview2_minimal_repro(
        tmp_path,
        output_root="out",
        probe_launch=True,
    )

    assert report["ok"] is False
    assert report["status"] == "blocked_minimal_pywebview_webview2_runtime"
    assert report["next_recommended_pass"] == "pass10b-webview2-runtime-host-remediation"


def test_minimal_repro_packaged_host_policy_block_routes_to_host_policy(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "out" / "dist" / repro.APP_NAME / f"{repro.APP_NAME}.exe"
    exe.parent.mkdir(parents=True, exist_ok=True)
    exe.write_bytes(b"fake exe")
    monkeypatch.setattr(repro, "_module_available", lambda _name: True)
    monkeypatch.setattr(repro.sys, "platform", "win32")
    monkeypatch.setattr(
        repro,
        "build_packaged_app_visual_qa",
        lambda *_args, **_kwargs: {
            "ok": False,
            "status": "blocked_packaged_app_visual_qa",
            "launch": {
                "host_policy": {
                    "status": "blocked_by_windows_application_control",
                    "blocked_by_windows_application_control": True,
                },
                "runtime_error": {"blocked": False, "status": "not_applicable"},
            },
            "screenshot": {"exists": False},
            "termination": {"attempted": False, "terminated": False},
        },
    )

    report = repro.build_pywebview_webview2_minimal_repro(
        tmp_path,
        output_root="out",
        probe_launch=True,
    )

    assert report["ok"] is False
    assert report["status"] == "blocked_minimal_pywebview_packaged_host_policy"
    assert report["next_recommended_pass"] == "pass10b-minimal-packaged-host-policy-unblock"


def test_minimal_repro_source_probe_success_routes_to_packaged_probe(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(repro, "_module_available", lambda _name: True)
    monkeypatch.setattr(
        repro,
        "_build_source_probe",
        lambda *_args, **_kwargs: {
            "ok": True,
            "status": "minimal_pywebview_source_probe_complete",
            "launch": {"runtime_error": {"blocked": False, "status": "not_applicable"}, "started": True},
            "screenshot": {"exists": True},
            "termination": {"attempted": True, "terminated": True},
        },
    )

    report = repro.build_pywebview_webview2_minimal_repro(
        tmp_path,
        output_root="out",
        probe_source=True,
    )

    assert report["ok"] is True
    assert report["status"] == "minimal_pywebview_source_repro_complete_packaged_probe_pending"
    assert report["source_probe"]["ok"] is True
    assert report["next_recommended_pass"] == "pass10b-pywebview-webview2-minimal-repro-packaged-probe"


def test_minimal_repro_rejects_output_root_outside_vault(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-minimal-repro"

    with pytest.raises(ValueError, match="output root must stay inside"):
        repro.build_pywebview_webview2_minimal_repro(tmp_path, output_root=outside)


def test_minimal_repro_writer_rejects_report_root_outside_vault(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-minimal-repro-report"

    with pytest.raises(ValueError, match="report root must stay inside"):
        repro.write_pywebview_webview2_minimal_repro(
            tmp_path,
            {"ok": False, "status": "blocked", "outputs": {}, "checks": [], "authority": {}},
            report_root=outside,
        )


def test_minimal_repro_parser_exposes_build_probe_and_report_options() -> None:
    from runtime.cli.main import _build_parser

    parser = _build_parser()
    args = parser.parse_args(
        [
            "studio",
            "pywebview-webview2-minimal-repro",
            "--execute-build",
            "--output-root",
            ".pytest_tmp_env/minimal",
            "--build-timeout-seconds",
            "2",
            "--probe-source",
            "--probe-launch",
            "--webview2-user-data-root",
            ".pytest_tmp_env/minimal/user-data",
            "--temp-root",
            ".pytest_tmp_env/minimal/temp",
            "--settle-seconds",
            "3",
            "--window-timeout-seconds",
            "4",
            "--terminate-timeout-seconds",
            "5",
            "--write-report",
            "--report-slug",
            "minimal-test",
        ]
    )

    assert args.execute_build is True
    assert args.output_root == ".pytest_tmp_env/minimal"
    assert args.build_timeout_seconds == 2
    assert args.probe_source is True
    assert args.probe_launch is True
    assert args.webview2_user_data_root == ".pytest_tmp_env/minimal/user-data"
    assert args.temp_root == ".pytest_tmp_env/minimal/temp"
    assert args.settle_seconds == 3
    assert args.window_timeout_seconds == 4
    assert args.terminate_timeout_seconds == 5
    assert args.write_report is True
    assert args.report_slug == "minimal-test"
