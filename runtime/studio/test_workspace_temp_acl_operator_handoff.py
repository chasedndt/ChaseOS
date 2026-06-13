"""Tests for workspace temp ACL operator handoff."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.studio import workspace_temp_acl_operator_handoff as handoff


def _write_diagnostic(tmp_path: Path, *, next_pass: str = "pass10b-workspace-temp-acl-operator-handoff") -> Path:
    report = {
        "surface": "studio_workspace_temp_acl_cleanup_diagnostic",
        "ok": False,
        "status": "blocked_workspace_temp_probe_write",
        "next_recommended_pass": next_pass,
        "workspace_temp_paths": [
            {
                "path": ".pytest_tmp_env/studio-webview2-diagnostic/temp/tmp145s58f5",
                "exists": True,
                "error": "PermissionError(13, 'Access is denied')",
            }
        ],
        "owned_cleanup_probe": {
            "created": ".pytest_tmp_env/studio-workspace-temp-acl-cleanup-diagnostic/probes/chaseos-owned-cleanup-test",
            "file_write_ok": False,
            "owned_cleanup_ok": False,
            "error": "PermissionError(13, 'Permission denied')",
        },
        "prior_workspace_cleanup_error": {
            "detected": True,
            "path": str(tmp_path / ".pytest_tmp_env/studio-webview2-diagnostic/temp/tmp145s58f5"),
            "path_inside_vault": True,
        },
        "authority": {
            "deletes_existing_temp_artifacts": False,
            "mutates_temp_acl": False,
            "mutates_host_policy": False,
            "installs_webview2": False,
            "launches_packaged_executable": False,
            "captures_native_screenshot": False,
            "signs_executable": False,
            "allowlists_executable": False,
            "writes_installer": False,
            "writes_host_startup": False,
            "grants_approvals": False,
            "executes_approval_decisions": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "writes_agent_bus_tasks": False,
            "canonical_mutation_allowed": False,
        },
        "checks": [{"name": "owned_probe_file_write_ok", "ok": False, "detail": "probe"}],
        "blockers": ["Owned workspace temp diagnostic probe cannot write its marker file."],
    }
    path = tmp_path / "diagnostic.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    return path


def test_workspace_temp_acl_operator_handoff_builds_review_only_handoff(tmp_path: Path) -> None:
    diagnostic = _write_diagnostic(tmp_path)

    report = handoff.build_workspace_temp_acl_operator_handoff(
        tmp_path,
        diagnostic_report_path=diagnostic,
    )

    checks = {item["name"]: item for item in report["checks"]}
    assert report["ok"] is True
    assert report["status"] == "workspace_temp_acl_operator_handoff_ready"
    assert report["surface"] == "studio_workspace_temp_acl_operator_handoff"
    assert report["authority"]["review_only"] is True
    assert report["authority"]["deletes_existing_temp_artifacts"] is False
    assert report["authority"]["mutates_temp_acl"] is False
    assert checks["diagnostic_routes_to_operator_handoff"]["ok"] is True
    assert report["blocked_paths"]
    assert "owned_probe_file_write_ok=true" in report["operator_handoff"]["acceptance_criteria"][0]
    assert report["next_recommended_pass"] == "operator-repair-workspace-temp-acl-then-pass10b-native-visual-qa-rerun"


def test_workspace_temp_acl_operator_handoff_writer_stays_in_vault(tmp_path: Path) -> None:
    diagnostic = _write_diagnostic(tmp_path)
    report = handoff.build_workspace_temp_acl_operator_handoff(tmp_path, diagnostic_report_path=diagnostic)

    write = handoff.write_workspace_temp_acl_operator_handoff(
        tmp_path,
        report,
        handoff_slug="handoff-test",
    )

    assert write["written"] is True
    assert (tmp_path / write["json_path"]).is_file()
    markdown = tmp_path / write["markdown_path"]
    assert markdown.is_file()
    text = markdown.read_text(encoding="utf-8")
    assert "review-only" in text
    assert "does not mutate temp ACLs" in text


def test_workspace_temp_acl_operator_handoff_writer_rejects_slug_escape(tmp_path: Path) -> None:
    diagnostic = _write_diagnostic(tmp_path)
    report = handoff.build_workspace_temp_acl_operator_handoff(tmp_path, diagnostic_report_path=diagnostic)

    with pytest.raises(ValueError, match="handoff output must stay inside the handoff root"):
        handoff.write_workspace_temp_acl_operator_handoff(
            tmp_path,
            report,
            handoff_root="handoffs",
            handoff_slug="../outside",
        )

    assert (tmp_path / "handoffs").exists() is False
    assert (tmp_path / "outside.json").exists() is False


def test_workspace_temp_acl_operator_handoff_parser_exposes_write_flags() -> None:
    from runtime.cli.main import _build_parser

    parser = _build_parser()
    args = parser.parse_args(
        [
            "studio",
            "workspace-temp-acl-operator-handoff",
            "--diagnostic-report-path",
            "diagnostic.json",
            "--write-handoff",
            "--handoff-slug",
            "handoff-test",
            "--handoff-root",
            "handoffs",
            "--json",
        ]
    )

    assert args.diagnostic_report_path == "diagnostic.json"
    assert args.write_handoff is True
    assert args.handoff_slug == "handoff-test"
    assert args.handoff_root == "handoffs"
    assert args.output_json is True
