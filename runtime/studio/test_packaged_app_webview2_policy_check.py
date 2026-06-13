"""Tests for packaged Studio WebView2 temp/policy checks."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.studio import packaged_app_webview2_policy_check as policy_check


class _FakeCompletedProcess:
    returncode = 0
    stdout = "{}"
    stderr = ""


def _diagnostic_payload() -> dict:
    return {
        "surface": "studio_packaged_app_webview2_diagnostic",
        "status": "blocked_webview2_initialization_with_workspace_runtime_dirs",
        "next_recommended_pass": "pass10b-system-temp-permission-or-webview2-policy-check",
        "system_temp": {"writable": False, "error": "permission denied"},
        "probe_launch": {
            "visual_qa_report": {
                "launch": {
                    "stderr_tail": (
                        "PermissionError: [WinError 5] Access is denied: "
                        "'C:\\\\workspace\\\\.pytest_tmp_env\\\\studio-webview2-diagnostic\\\\temp\\\\tmpabc'\n"
                    ),
                    "runtime_error": {
                        "blocked": True,
                        "status": "webview2_initialization_failed",
                    },
                }
            }
        },
    }


def test_policy_check_classifies_temp_permission_and_cleanup_error(monkeypatch, tmp_path: Path) -> None:
    report_path = tmp_path / "diag.json"
    payload = _diagnostic_payload()
    payload["probe_launch"]["visual_qa_report"]["launch"]["stderr_tail"] = (
        f"PermissionError: [WinError 5] Access is denied: '{tmp_path}\\\\.pytest_tmp_env\\\\tmpabc'\n"
    )
    report_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(
        policy_check,
        "_detect_webview2_policies",
        lambda: {"policy_detected": False, "policies": [], "probe": {"ok": True}},
    )
    monkeypatch.setattr(
        policy_check,
        "_python_temp_probe",
        lambda root: {"ok": True, "payload": {"tempdir": str(root), "cleanup_ok": True}},
    )

    report = policy_check.build_packaged_app_webview2_policy_check(tmp_path, diagnostic_report_path=report_path)

    assert report["ok"] is False
    assert report["status"] == "blocked_temp_permission_and_cleanup_error"
    assert report["next_recommended_pass"] == "pass10b-pywebview-temp-cleanup-diagnostic"
    assert report["workspace_cleanup_error"]["detected"] is True
    assert "System temp write probe is denied or unavailable." in report["blockers"]
    assert report["authority"]["mutates_temp_acl"] is False


def test_policy_check_routes_policy_values_to_review(monkeypatch, tmp_path: Path) -> None:
    report_path = tmp_path / "diag.json"
    payload = _diagnostic_payload()
    payload["probe_launch"]["visual_qa_report"]["launch"]["stderr_tail"] = ""
    report_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(
        policy_check,
        "_detect_webview2_policies",
        lambda: {"policy_detected": True, "policies": [{"name": "UserDataFolder", "value": "blocked"}], "probe": {"ok": True}},
    )
    monkeypatch.setattr(
        policy_check,
        "_python_temp_probe",
        lambda root: {"ok": True, "payload": {"tempdir": str(root), "cleanup_ok": True}},
    )

    report = policy_check.build_packaged_app_webview2_policy_check(tmp_path, diagnostic_report_path=report_path)

    assert report["status"] == "blocked_webview2_policy_review_required"
    assert report["next_recommended_pass"] == "pass10b-webview2-policy-remediation-handoff"
    assert report["checks"][4]["name"] == "webview2_policy_absent"
    assert report["checks"][4]["ok"] is False


def test_policy_check_classifies_system_and_workspace_temp_failure(monkeypatch, tmp_path: Path) -> None:
    report_path = tmp_path / "diag.json"
    payload = _diagnostic_payload()
    payload["probe_launch"]["visual_qa_report"]["launch"]["stderr_tail"] = (
        f"PermissionError: [WinError 5] Access is denied: '{tmp_path}\\\\.pytest_tmp_env\\\\tmpabc'\n"
    )
    report_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(
        policy_check,
        "_detect_webview2_policies",
        lambda: {"policy_detected": False, "policies": [], "probe": {"ok": True}},
    )
    monkeypatch.setattr(
        policy_check,
        "_python_temp_probe",
        lambda root: {"ok": False, "payload": {"tempdir": str(root), "error": "PermissionError"}},
    )

    report = policy_check.build_packaged_app_webview2_policy_check(tmp_path, diagnostic_report_path=report_path)

    assert report["status"] == "blocked_system_and_workspace_temp_permission"
    assert report["next_recommended_pass"] == "pass10b-workspace-temp-acl-cleanup-diagnostic"
    assert "Workspace Python temp override probe cannot create and clean up a temp directory." in report["blockers"]


def test_python_temp_probe_creates_writable_cleanup_child_under_override(tmp_path: Path) -> None:
    root = tmp_path / "workspace-temp"

    probe = policy_check._python_temp_probe(root)
    payload = probe["payload"]

    assert probe["ok"] is True
    assert payload["cleanup_ok"] is True
    assert Path(payload["tempdir"]).resolve() == root.resolve()
    assert Path(payload["created"]).parent.resolve() == root.resolve()
    assert Path(payload["created"]).exists() is False


def test_policy_check_powershell_probe_uses_hidden_window(monkeypatch) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(policy_check.os, "name", "nt", raising=False)
    monkeypatch.setattr(policy_check.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)

    def fake_run(_args, **kwargs):
        captured.update(kwargs)
        return _FakeCompletedProcess()

    monkeypatch.setattr(policy_check.subprocess, "run", fake_run)

    result = policy_check._run_powershell_json("$true")

    assert result["ok"] is True
    assert captured["shell"] is False
    assert captured["creationflags"] == 0x08000000


def test_policy_check_rejects_workspace_temp_outside_vault(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-temp"

    with pytest.raises(ValueError, match="workspace temp root must stay inside"):
        policy_check.build_packaged_app_webview2_policy_check(tmp_path, workspace_temp_root=outside)


def test_policy_check_writer_rejects_report_root_outside_vault(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-report"

    with pytest.raises(ValueError, match="report root must stay inside"):
        policy_check.write_packaged_app_webview2_policy_check(
            tmp_path,
            {"ok": False, "status": "blocked", "checks": [], "authority": {}},
            report_root=outside,
        )


def test_policy_check_parser_exposes_arguments() -> None:
    from runtime.cli.main import _build_parser

    parser = _build_parser()
    args = parser.parse_args(
        [
            "studio",
            "packaged-app-webview2-policy-check",
            "--diagnostic-report-path",
            "diag.json",
            "--workspace-temp-root",
            ".pytest_tmp_env/policy-temp",
            "--write-report",
            "--report-slug",
            "policy-test",
        ]
    )

    assert args.diagnostic_report_path == "diag.json"
    assert args.workspace_temp_root == ".pytest_tmp_env/policy-temp"
    assert args.write_report is True
    assert args.report_slug == "policy-test"
