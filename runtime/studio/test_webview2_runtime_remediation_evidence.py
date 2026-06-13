from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.cli.main import build_parser
from runtime.studio import webview2_runtime_remediation_evidence as evidence


def test_webview2_runtime_remediation_evidence_records_performed_operator_evidence(tmp_path: Path) -> None:
    report = evidence.build_webview2_runtime_remediation_evidence(
        tmp_path,
        remediation_status="performed",
        operator="Host admin",
        remediation_summary="Repaired Microsoft Edge WebView2 Runtime from Apps and Features.",
        evidence_reference="ticket CHASEOS-10B",
        webview2_version="123.0.0.0",
    )

    assert report["ok"] is True
    assert report["status"] == "webview2_runtime_remediation_evidence_supplied"
    assert report["readiness"]["operator_remediation_evidence_supplied"] is True
    assert report["readiness"]["remediation_effect_verified"] is False
    assert report["next_recommended_pass"] == "pass10b-pywebview-webview2-minimal-repro-rerun-after-operator-remediation"
    assert report["authority"]["repairs_webview2"] is False


def test_webview2_runtime_remediation_evidence_blocks_when_not_performed(tmp_path: Path) -> None:
    report = evidence.build_webview2_runtime_remediation_evidence(
        tmp_path,
        remediation_status="not_performed",
        operator="Codex",
        remediation_summary="No operator/admin WebView2 remediation evidence supplied in this pass.",
    )

    assert report["ok"] is False
    assert report["status"] == "webview2_runtime_remediation_evidence_not_supplied"
    assert "Operator/admin WebView2 runtime remediation has not been recorded as performed." in report["blockers"]
    assert report["next_recommended_pass"] == "operator-remediate-webview2-runtime-then-pass10b-minimal-repro-rerun"


def test_webview2_runtime_remediation_evidence_requires_reference_when_performed(tmp_path: Path) -> None:
    report = evidence.build_webview2_runtime_remediation_evidence(
        tmp_path,
        remediation_status="performed",
        operator="Host admin",
        remediation_summary="Repair completed.",
    )

    assert report["ok"] is False
    assert "Performed remediation requires an evidence reference." in report["blockers"]


def test_webview2_runtime_remediation_evidence_rejects_report_root_outside_vault(tmp_path: Path) -> None:
    report = evidence.build_webview2_runtime_remediation_evidence(
        tmp_path,
        remediation_status="performed",
        operator="Host admin",
        remediation_summary="Repair completed.",
        evidence_reference="ticket",
    )

    with pytest.raises(ValueError, match="evidence root must stay inside"):
        evidence.write_webview2_runtime_remediation_evidence(
            tmp_path,
            report,
            report_root=tmp_path.parent / "outside-webview2-remediation-evidence",
        )


def test_webview2_runtime_remediation_evidence_writer_preserves_review_only_boundary(tmp_path: Path) -> None:
    report = evidence.build_webview2_runtime_remediation_evidence(
        tmp_path,
        remediation_status="performed",
        operator="Host admin",
        remediation_summary="Repair completed.",
        evidence_reference="ticket",
    )

    written = evidence.write_webview2_runtime_remediation_evidence(tmp_path, report, report_slug="evidence")
    payload = json.loads((tmp_path / written["json_path"]).read_text(encoding="utf-8"))

    assert payload["report_type"] == "webview2_runtime_remediation_evidence_intake"
    assert payload["authority"]["review_only"] is True
    assert payload["authority"]["installs_webview2"] is False
    assert payload["authority"]["repairs_webview2"] is False
    assert payload["readiness"]["remediation_effect_verified"] is False


def test_webview2_runtime_remediation_evidence_loads_vault_scoped_file(tmp_path: Path) -> None:
    evidence_file = tmp_path / "operator-webview2-remediation.json"
    evidence_file.write_text(
        json.dumps(
            {
                "remediation_status": "performed",
                "operator": "Host admin",
                "remediation_summary": "Repaired WebView2 runtime through Windows Apps repair.",
                "evidence_reference": "ticket CHASEOS-10B",
                "webview2_version": "147.0.3912.98",
                "remediation_timestamp": "2026-05-12T02:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    loaded = evidence.load_webview2_runtime_remediation_evidence_file(tmp_path, evidence_file)
    report = evidence.build_webview2_runtime_remediation_evidence(tmp_path, **loaded)

    assert loaded["remediation_status"] == "performed"
    assert report["ok"] is True
    assert report["readiness"]["operator_remediation_evidence_supplied"] is True
    assert report["authority"]["repairs_webview2"] is False


def test_webview2_runtime_remediation_evidence_file_can_use_nested_remediation_payload(tmp_path: Path) -> None:
    evidence_file = tmp_path / "operator-webview2-remediation.json"
    evidence_file.write_text(
        json.dumps(
            {
                "remediation": {
                    "status": "performed",
                    "operator": "Host admin",
                    "summary": "Repair completed.",
                    "evidence_reference": "ticket",
                }
            }
        ),
        encoding="utf-8",
    )

    loaded = evidence.load_webview2_runtime_remediation_evidence_file(tmp_path, "operator-webview2-remediation.json")

    assert loaded["remediation_status"] == "performed"
    assert loaded["operator"] == "Host admin"
    assert loaded["remediation_summary"] == "Repair completed."
    assert loaded["evidence_reference"] == "ticket"


def test_webview2_runtime_remediation_evidence_file_rejects_path_outside_vault(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-webview2-remediation.json"
    outside.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="must stay inside the vault workspace"):
        evidence.load_webview2_runtime_remediation_evidence_file(tmp_path, outside)


def test_webview2_runtime_remediation_evidence_parser_exposes_command() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "studio",
            "webview2-runtime-remediation-evidence",
            "--evidence-file",
            "operator-webview2-remediation.json",
            "--remediation-status",
            "performed",
            "--operator",
            "Host admin",
            "--remediation-summary",
            "Repair completed.",
            "--evidence-reference",
            "ticket",
            "--webview2-version",
            "123.0.0.0",
            "--remediation-timestamp",
            "2026-05-11T20:00:00Z",
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

    assert args.evidence_file == "operator-webview2-remediation.json"
    assert args.remediation_status == "performed"
    assert args.operator == "Host admin"
    assert args.remediation_summary == "Repair completed."
    assert args.evidence_reference == "ticket"
    assert args.webview2_version == "123.0.0.0"
    assert args.remediation_timestamp == "2026-05-11T20:00:00Z"
    assert args.write_report is True
    assert args.report_slug == "slug"
    assert args.output_json is True
