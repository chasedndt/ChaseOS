from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.cli.main import build_parser
from runtime.studio import webview2_post_remediation_rerun_readiness as readiness


def _authority() -> dict[str, object]:
    return {
        "review_only": True,
        "mutates_host_policy": False,
        "installs_webview2": False,
        "repairs_webview2": False,
        "signs_executable": False,
        "allowlists_executable": False,
        "writes_installer": False,
        "writes_host_startup": False,
        "launches_packaged_executable": False,
        "captures_native_screenshot": False,
        "grants_approvals": False,
        "executes_approval_decisions": False,
        "provider_calls_allowed": False,
        "connector_calls_allowed": False,
        "writes_agent_bus_tasks": False,
        "canonical_mutation_allowed": False,
    }


def _write_host_handoff(root: Path) -> Path:
    path = root / "07_LOGS" / "Studio-Graph-Views" / "webview2-runtime-host-remediation" / "handoff.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "ok": True,
                "surface": "studio_webview2_runtime_host_remediation",
                "status": "webview2_runtime_host_remediation_ready",
                "authority": _authority(),
                "next_recommended_pass": "operator-remediate-webview2-runtime-then-pass10b-minimal-repro-rerun",
            }
        ),
        encoding="utf-8",
    )
    return path


def _write_remediation_evidence(root: Path, *, performed: bool = True, effect_verified: bool = False) -> Path:
    path = root / "07_LOGS" / "Studio-Graph-Views" / "webview2-runtime-remediation-evidence" / "evidence.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    status = "performed" if performed else "not_performed"
    path.write_text(
        json.dumps(
            {
                "ok": performed,
                "surface": "studio_webview2_runtime_remediation_evidence",
                "status": (
                    "webview2_runtime_remediation_evidence_supplied"
                    if performed
                    else "webview2_runtime_remediation_evidence_not_supplied"
                ),
                "remediation": {
                    "status": status,
                    "operator": "Host admin",
                    "evidence_reference": "ticket CHASEOS-10B" if performed else "",
                },
                "readiness": {
                    "operator_remediation_evidence_supplied": performed,
                    "remediation_effect_verified": effect_verified,
                    "next_recommended_pass": (
                        "pass10b-pywebview-webview2-minimal-repro-rerun-after-operator-remediation"
                        if performed
                        else "operator-remediate-webview2-runtime-then-pass10b-minimal-repro-rerun"
                    ),
                },
                "authority": _authority(),
                "next_recommended_pass": (
                    "pass10b-pywebview-webview2-minimal-repro-rerun-after-operator-remediation"
                    if performed
                    else "operator-remediate-webview2-runtime-then-pass10b-minimal-repro-rerun"
                ),
            }
        ),
        encoding="utf-8",
    )
    return path


def test_post_remediation_rerun_readiness_ready_after_performed_evidence(tmp_path: Path) -> None:
    _write_host_handoff(tmp_path)
    _write_remediation_evidence(tmp_path, performed=True)

    report = readiness.build_webview2_post_remediation_rerun_readiness(tmp_path)

    assert report["ok"] is True
    assert report["status"] == "webview2_post_remediation_rerun_ready"
    assert report["rerun_plan"]["ready"] is True
    assert report["authority"]["executes_reruns"] is False
    assert report["next_recommended_pass"] == "pass10b-pywebview-webview2-minimal-repro-rerun-after-operator-remediation"


def test_post_remediation_rerun_readiness_blocks_without_performed_evidence(tmp_path: Path) -> None:
    _write_host_handoff(tmp_path)
    _write_remediation_evidence(tmp_path, performed=False)

    report = readiness.build_webview2_post_remediation_rerun_readiness(tmp_path)

    assert report["ok"] is False
    assert report["status"] == "blocked_webview2_post_remediation_rerun_readiness"
    assert "Operator/admin WebView2 remediation evidence has not been supplied." in report["blockers"]
    assert report["next_recommended_pass"] == "operator-remediate-webview2-runtime-then-pass10b-minimal-repro-rerun"


def test_post_remediation_rerun_readiness_blocks_preclaimed_effect_verification(tmp_path: Path) -> None:
    _write_host_handoff(tmp_path)
    _write_remediation_evidence(tmp_path, performed=True, effect_verified=True)

    report = readiness.build_webview2_post_remediation_rerun_readiness(tmp_path)

    assert report["ok"] is False
    assert "Remediation evidence intake must not claim rerun verification before reruns execute." in report["blockers"]


def test_post_remediation_rerun_readiness_rejects_report_root_outside_vault(tmp_path: Path) -> None:
    report = readiness.build_webview2_post_remediation_rerun_readiness(tmp_path)

    with pytest.raises(ValueError, match="readiness root must stay inside"):
        readiness.write_webview2_post_remediation_rerun_readiness(
            tmp_path,
            report,
            report_root=tmp_path.parent / "outside-readiness",
        )


def test_post_remediation_rerun_readiness_parser_exposes_command() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "studio",
            "webview2-post-remediation-rerun-readiness",
            "--remediation-evidence-path",
            "evidence.json",
            "--host-remediation-report-path",
            "handoff.json",
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

    assert args.remediation_evidence_path == "evidence.json"
    assert args.host_remediation_report_path == "handoff.json"
    assert args.write_report is True
    assert args.report_slug == "slug"
    assert args.report_root == "reports"
    assert args.output_json is True
