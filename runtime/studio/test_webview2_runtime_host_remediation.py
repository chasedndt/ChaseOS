from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.cli.main import build_parser
from runtime.studio import webview2_runtime_host_remediation as remediation


def _write_minimal_report(root: Path, *, authority: dict[str, object] | None = None) -> Path:
    path = root / "07_LOGS" / "Studio-Graph-Views" / "pywebview-webview2-minimal-repro" / "minimal.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "surface": "studio_pywebview_webview2_minimal_repro",
                "status": "blocked_minimal_pywebview_webview2_runtime",
                "ok": False,
                "source_probe": {
                    "status": "blocked_minimal_pywebview_source_probe",
                    "launch": {
                        "runtime_error": {
                            "status": "webview2_initialization_failed",
                            "blocked": True,
                        }
                    },
                },
                "visual_probe": {
                    "status": "blocked_packaged_app_visual_qa",
                    "launch": {
                        "runtime_error": {
                            "status": "webview2_initialization_failed",
                            "blocked": True,
                        }
                    },
                },
                "authority": authority
                if authority is not None
                else {
                    "mutates_host_policy": False,
                    "installs_webview2": False,
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
                "next_recommended_pass": "pass10b-webview2-runtime-host-remediation",
            }
        ),
        encoding="utf-8",
    )
    return path


def test_webview2_runtime_host_remediation_ready_from_minimal_repro(tmp_path: Path) -> None:
    _write_minimal_report(tmp_path)

    report = remediation.build_webview2_runtime_host_remediation(tmp_path)

    assert report["ok"] is True
    assert report["status"] == "webview2_runtime_host_remediation_ready"
    assert report["latest_minimal_repro"]["source_runtime_error_status"] == "webview2_initialization_failed"
    assert report["latest_minimal_repro"]["packaged_runtime_error_status"] == "webview2_initialization_failed"
    assert report["authority"]["installs_webview2"] is False
    assert report["authority"]["repairs_webview2"] is False
    assert report["next_recommended_pass"] == "operator-remediate-webview2-runtime-then-pass10b-minimal-repro-rerun"


def test_webview2_runtime_host_remediation_blocks_without_minimal_report(tmp_path: Path) -> None:
    report = remediation.build_webview2_runtime_host_remediation(tmp_path)

    assert report["ok"] is False
    assert report["status"] == "webview2_runtime_host_remediation_blocked"
    assert "Minimal PyWebView/WebView2 repro report is missing or invalid." in report["blockers"]


def test_webview2_runtime_host_remediation_blocks_bad_authority(tmp_path: Path) -> None:
    _write_minimal_report(tmp_path, authority={"installs_webview2": True})

    report = remediation.build_webview2_runtime_host_remediation(tmp_path)

    assert report["ok"] is False
    assert "Minimal repro authority boundary is not acceptable for host-remediation handoff." in report["blockers"]


def test_webview2_runtime_host_remediation_writer_rejects_report_root_outside_vault(tmp_path: Path) -> None:
    report = remediation.build_webview2_runtime_host_remediation(tmp_path)

    with pytest.raises(ValueError, match="report root must stay inside"):
        remediation.write_webview2_runtime_host_remediation(
            tmp_path,
            report,
            report_root=tmp_path.parent / "outside-webview2-runtime-host-remediation",
        )


def test_webview2_runtime_host_remediation_parser_exposes_command() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "studio",
            "webview2-runtime-host-remediation",
            "--minimal-repro-report-path",
            "minimal.json",
            "--diagnostic-report-path",
            "diagnostic.json",
            "--policy-check-report-path",
            "policy.json",
            "--write-report",
            "--report-slug",
            "slug",
            "--report-root",
            "reports",
            "--vault-root",
            ".",
            "--json",
        ]
    )

    assert args.minimal_repro_report_path == "minimal.json"
    assert args.diagnostic_report_path == "diagnostic.json"
    assert args.policy_check_report_path == "policy.json"
    assert args.write_report is True
    assert args.report_slug == "slug"
    assert args.report_root == "reports"
    assert args.output_json is True
