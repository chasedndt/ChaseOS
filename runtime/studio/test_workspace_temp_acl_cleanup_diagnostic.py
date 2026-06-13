"""Tests for Pass 10B workspace temp ACL cleanup diagnostics."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from runtime.studio import workspace_temp_acl_cleanup_diagnostic as temp_diag


class _FakeCompletedProcess:
    returncode = 0
    stdout = "{}"
    stderr = ""


def _policy_payload(tmp_path: Path) -> dict:
    cleanup_path = tmp_path / ".pytest_tmp_env" / "studio-webview2-diagnostic" / "temp" / "tmpabc"
    return {
        "surface": "studio_packaged_app_webview2_policy_check",
        "ok": False,
        "status": "blocked_system_and_workspace_temp_permission",
        "next_recommended_pass": "pass10b-workspace-temp-acl-cleanup-diagnostic",
        "workspace_temp_probe": {
            "root": ".pytest_tmp_env/studio-webview2-policy-check/temp",
            "python_temp_probe": {
                "ok": False,
                "payload": {"tempdir": str(tmp_path / ".pytest_tmp_env" / "studio-webview2-policy-check" / "temp"), "error": "PermissionError"},
            },
        },
        "workspace_cleanup_error": {
            "detected": True,
            "path": str(cleanup_path),
            "path_inside_vault": True,
        },
        "packaged_runtime_error": {
            "blocked": True,
            "status": "webview2_initialization_failed",
        },
        "authority": {
            "mutates_temp_acl": False,
            "canonical_mutation_allowed": False,
        },
    }


def test_workspace_temp_diagnostic_classifies_stale_cleanup_artifact(monkeypatch, tmp_path: Path) -> None:
    policy_path = tmp_path / "policy.json"
    payload = _policy_payload(tmp_path)
    cleanup_path = Path(payload["workspace_cleanup_error"]["path"])
    cleanup_path.mkdir(parents=True)
    policy_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(temp_diag, "_powershell_acl_snapshot", lambda path: {"ok": True, "exists": path.exists(), "path": str(path)})

    report = temp_diag.build_workspace_temp_acl_cleanup_diagnostic(tmp_path, policy_check_report_path=policy_path)

    assert report["ok"] is False
    assert report["status"] == "blocked_workspace_temp_stale_cleanup_artifact"
    assert report["next_recommended_pass"] == "pass10b-workspace-temp-stale-artifact-operator-handoff"
    assert report["authority"]["mutates_temp_acl"] is False
    assert report["authority"]["deletes_existing_temp_artifacts"] is False
    assert cleanup_path.exists() is True


def test_workspace_temp_diagnostic_routes_prior_python_temp_failure_when_stale_artifact_absent(
    monkeypatch, tmp_path: Path
) -> None:
    policy_path = tmp_path / "policy.json"
    payload = _policy_payload(tmp_path)
    policy_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(temp_diag, "_powershell_acl_snapshot", lambda path: {"ok": True, "exists": path.exists(), "path": str(path)})

    report = temp_diag.build_workspace_temp_acl_cleanup_diagnostic(tmp_path, policy_check_report_path=policy_path)

    assert report["status"] == "blocked_prior_workspace_python_temp_override_failure"
    assert report["next_recommended_pass"] == "pass10b-pyinstaller-pywebview-temp-minimal-repro"
    assert "Prior workspace Python temp override probe failed." in report["blockers"]


def test_workspace_temp_diagnostic_clear_routes_to_native_qa_rerun(monkeypatch, tmp_path: Path) -> None:
    policy_path = tmp_path / "policy.json"
    payload = _policy_payload(tmp_path)
    payload["workspace_temp_probe"]["python_temp_probe"] = {"ok": True, "payload": {"tempdir": str(tmp_path / "temp")}}
    payload["workspace_cleanup_error"] = {"detected": False, "path": None}
    payload["packaged_runtime_error"] = {"blocked": False, "status": "not_applicable"}
    policy_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(temp_diag, "_powershell_acl_snapshot", lambda path: {"ok": True, "exists": path.exists(), "path": str(path)})

    report = temp_diag.build_workspace_temp_acl_cleanup_diagnostic(tmp_path, policy_check_report_path=policy_path)

    assert report["ok"] is True
    assert report["status"] == "workspace_temp_acl_cleanup_diagnostic_clear"
    assert report["next_recommended_pass"] == "pass10b-native-visual-qa-rerun"


def test_owned_cleanup_probe_creates_child_with_os_mkdir(monkeypatch, tmp_path: Path) -> None:
    calls: list[Path] = []
    original_mkdir = temp_diag.os.mkdir

    def tracked_mkdir(path: str | bytes | os.PathLike, mode: int = 0o777, *, dir_fd: int | None = None) -> None:
        selected = Path(path)
        if selected.name.startswith("chaseos-owned-cleanup-"):
            calls.append(selected)
        if dir_fd is None:
            original_mkdir(path, mode)
        else:  # pragma: no cover - pathlib does not use dir_fd in this probe.
            original_mkdir(path, mode, dir_fd=dir_fd)

    monkeypatch.setattr(temp_diag.os, "mkdir", tracked_mkdir)

    probe = temp_diag._owned_cleanup_probe(tmp_path, tmp_path / "probes")

    assert probe["file_write_ok"] is True
    assert probe["owned_cleanup_ok"] is True
    assert probe["leftover_exists"] is False
    assert calls


def test_workspace_temp_diagnostic_rejects_probe_root_outside_vault(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="probe root must stay inside"):
        temp_diag.build_workspace_temp_acl_cleanup_diagnostic(
            tmp_path,
            policy_check_report_path=tmp_path / "missing.json",
            probe_root=tmp_path.parent / "outside-probe",
        )


def test_workspace_temp_diagnostic_writer_rejects_report_root_outside_vault(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="report root must stay inside"):
        temp_diag.write_workspace_temp_acl_cleanup_diagnostic(
            tmp_path,
            {"ok": False, "status": "blocked", "checks": [], "authority": {}},
            report_root=tmp_path.parent / "outside-report",
        )


def test_workspace_temp_diagnostic_powershell_probe_uses_hidden_window(monkeypatch) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(temp_diag.os, "name", "nt", raising=False)
    monkeypatch.setattr(temp_diag.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)

    def fake_run(_args, **kwargs):
        captured.update(kwargs)
        return _FakeCompletedProcess()

    monkeypatch.setattr(temp_diag.subprocess, "run", fake_run)

    result = temp_diag._run_powershell_json("$true")

    assert result["ok"] is True
    assert captured["shell"] is False
    assert captured["creationflags"] == 0x08000000


def test_workspace_temp_diagnostic_parser_exposes_arguments() -> None:
    from runtime.cli.main import _build_parser

    parser = _build_parser()
    args = parser.parse_args(
        [
            "studio",
            "workspace-temp-acl-cleanup-diagnostic",
            "--policy-check-report-path",
            "policy.json",
            "--probe-root",
            ".pytest_tmp_env/temp-probe",
            "--write-report",
            "--report-slug",
            "temp-diag",
        ]
    )

    assert args.policy_check_report_path == "policy.json"
    assert args.probe_root == ".pytest_tmp_env/temp-probe"
    assert args.write_report is True
    assert args.report_slug == "temp-diag"
