from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.cli.main import build_parser
from runtime.studio import webview2_operator_remediation_packet as packet


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
                "operator_handoff": {
                    "required_external_actions": ["Repair or reinstall WebView2 outside Codex."],
                    "acceptance_criteria": ["Minimal repro captures a nonblank window."],
                },
                "authority": _authority(),
                "next_recommended_pass": "operator-remediate-webview2-runtime-then-pass10b-minimal-repro-rerun",
            }
        ),
        encoding="utf-8",
    )
    return path


def _write_remediation_evidence(root: Path, *, performed: bool = False) -> Path:
    path = root / "07_LOGS" / "Studio-Graph-Views" / "webview2-runtime-remediation-evidence" / "evidence.json"
    path.parent.mkdir(parents=True, exist_ok=True)
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
                    "status": "performed" if performed else "not_performed",
                    "operator": "Host admin" if performed else "Codex",
                    "evidence_reference": "ticket CHASEOS-10B" if performed else "",
                },
                "readiness": {
                    "operator_remediation_evidence_supplied": performed,
                    "remediation_effect_verified": False,
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


def _write_rerun_readiness(root: Path, *, ready: bool = False) -> Path:
    path = root / "07_LOGS" / "Studio-Graph-Views" / "webview2-post-remediation-rerun-readiness" / "readiness.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "ok": ready,
                "surface": "studio_webview2_post_remediation_rerun_readiness",
                "status": (
                    "webview2_post_remediation_rerun_ready"
                    if ready
                    else "blocked_webview2_post_remediation_rerun_readiness"
                ),
                "rerun_plan": {
                    "ready": ready,
                    "minimal_repro_command": "python -m runtime.cli.main studio pywebview-webview2-minimal-repro --probe-source --probe-launch --write-report --json",
                    "packaged_visual_qa_command": "python -m runtime.cli.main studio packaged-app-visual-qa --settle-seconds 12 --window-timeout-seconds 30 --terminate-timeout-seconds 5 --json",
                    "completion_audit_command": "python -m runtime.cli.main studio pass10b-visual-proof-completion-audit --write-report --json",
                },
                "blockers": [] if ready else ["Operator/admin WebView2 remediation evidence has not been supplied."],
                "authority": {**_authority(), "executes_reruns": False},
                "next_recommended_pass": (
                    "pass10b-pywebview-webview2-minimal-repro-rerun-after-operator-remediation"
                    if ready
                    else "operator-remediate-webview2-runtime-then-pass10b-minimal-repro-rerun"
                ),
            }
        ),
        encoding="utf-8",
    )
    return path


def test_webview2_operator_remediation_packet_ready_for_operator_while_rerun_blocked(tmp_path: Path) -> None:
    _write_host_handoff(tmp_path)
    _write_remediation_evidence(tmp_path, performed=False)
    _write_rerun_readiness(tmp_path, ready=False)

    report = packet.build_webview2_operator_remediation_packet(tmp_path)

    assert report["ok"] is True
    assert report["status"] == "webview2_operator_remediation_packet_ready_for_operator"
    assert report["operator_packet"]["rerun_gate"]["ready"] is False
    assert report["authority"]["repairs_webview2"] is False
    assert report["authority"]["executes_reruns"] is False
    assert "webview2-runtime-remediation-evidence" in report["operator_packet"]["evidence_intake_command"]
    assert "--evidence-file" in report["operator_packet"]["evidence_file_intake_command"]
    assert report["operator_packet"]["evidence_file_template"]["remediation_status"] == "performed"
    assert report["next_recommended_pass"] == "operator-remediate-webview2-runtime-then-pass10b-minimal-repro-rerun"


def test_webview2_operator_remediation_packet_marks_rerun_ready_after_readiness_gate(tmp_path: Path) -> None:
    _write_host_handoff(tmp_path)
    _write_remediation_evidence(tmp_path, performed=True)
    _write_rerun_readiness(tmp_path, ready=True)

    report = packet.build_webview2_operator_remediation_packet(tmp_path)

    assert report["ok"] is True
    assert report["status"] == "webview2_operator_remediation_packet_rerun_ready"
    assert report["operator_packet"]["rerun_gate"]["ready"] is True
    assert "Reruns are permitted" in report["operator_packet"]["rerun_gate"]["instruction"]


def test_webview2_operator_remediation_packet_blocks_without_source_reports(tmp_path: Path) -> None:
    report = packet.build_webview2_operator_remediation_packet(tmp_path)

    assert report["ok"] is False
    assert report["status"] == "blocked_webview2_operator_remediation_packet"
    assert "WebView2 runtime host-remediation handoff/report is missing or invalid." in report["blockers"]


def test_webview2_operator_remediation_packet_writer_rejects_report_root_outside_vault(tmp_path: Path) -> None:
    _write_host_handoff(tmp_path)
    _write_remediation_evidence(tmp_path)
    _write_rerun_readiness(tmp_path)
    report = packet.build_webview2_operator_remediation_packet(tmp_path)

    with pytest.raises(ValueError, match="packet root must stay inside"):
        packet.write_webview2_operator_remediation_packet(
            tmp_path,
            report,
            report_root=tmp_path.parent / "outside-webview2-operator-packet",
        )


def test_webview2_operator_remediation_packet_writer_preserves_review_only_boundary(tmp_path: Path) -> None:
    _write_host_handoff(tmp_path)
    _write_remediation_evidence(tmp_path)
    _write_rerun_readiness(tmp_path)
    report = packet.build_webview2_operator_remediation_packet(tmp_path)

    written = packet.write_webview2_operator_remediation_packet(tmp_path, report, report_slug="packet")
    payload = json.loads((tmp_path / written["json_path"]).read_text(encoding="utf-8"))

    assert payload["surface"] == "studio_webview2_operator_remediation_packet"
    assert payload["authority"]["review_only"] is True
    assert payload["authority"]["installs_webview2"] is False
    assert payload["authority"]["repairs_webview2"] is False
    assert payload["authority"]["executes_reruns"] is False
    assert payload["operator_packet"]["rerun_gate"]["ready"] is False


def test_webview2_operator_remediation_packet_parser_exposes_command() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "studio",
            "webview2-operator-remediation-packet",
            "--host-remediation-report-path",
            "handoff.json",
            "--remediation-evidence-path",
            "evidence.json",
            "--post-remediation-readiness-path",
            "readiness.json",
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

    assert args.host_remediation_report_path == "handoff.json"
    assert args.remediation_evidence_path == "evidence.json"
    assert args.post_remediation_readiness_path == "readiness.json"
    assert args.write_report is True
    assert args.report_slug == "slug"
    assert args.report_root == "reports"
    assert args.output_json is True
