"""Tests for Pass 10B visual-proof completion audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from runtime.studio import pass10b_visual_proof_completion_audit as audit


def _prepare_basic_audit_repo(monkeypatch, tmp_path: Path) -> None:
    evidence = tmp_path / audit.BROWSER_NONBLANK_EVIDENCE
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_bytes(b"png")
    (tmp_path / audit.PASS10B_TEST_PATH).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / audit.PASS10B_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    (tmp_path / audit.DESKTOP_SHELL_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    monkeypatch.setattr(
        audit,
        "analyze_png_nonblank",
        lambda *_args, **_kwargs: {
            "ok": True,
            "reason": "passed",
            "unique_color_count": 12,
            "dominant_color_ratio": 0.5,
        },
    )
    monkeypatch.setattr(
        audit,
        "build_packaged_app_host_policy_unblock_readiness",
        lambda *_args, **_kwargs: {
            "status": "blocked_by_windows_application_control",
            "host_policy": {"status": "blocked_by_windows_application_control"},
            "readiness": {
                "host_policy_probe_performed": True,
                "host_policy_allows_launch": False,
                "native_visual_qa_complete": False,
            },
            "authority": {
                "mutates_host_policy": False,
                "signs_executable": False,
                "allowlists_executable": False,
                "writes_installer": False,
                "writes_host_startup": False,
                "executes_approval_decisions": False,
                "provider_calls_allowed": False,
                "connector_calls_allowed": False,
                "writes_agent_bus_tasks": False,
                "canonical_mutation_allowed": False,
            },
        },
    )


def _write_blocked_visual_qa_report(root: Path) -> Path:
    path = root / "blocked-packaged-visual-qa.json"
    path.write_text(
        json.dumps(
            {
                "ok": False,
                "surface": "studio_packaged_app_visual_qa",
                "model_version": "studio.packaged_app_visual_qa.v1",
                "status": "blocked_packaged_app_visual_qa",
                "launch": {
                    "started": True,
                    "process_alive_before_capture": True,
                    "host_policy": {
                        "status": "not_applicable",
                        "blocked_by_windows_application_control": False,
                    },
                    "runtime_error": {
                        "status": "webview2_initialization_failed",
                        "blocked": True,
                    },
                },
                "screenshot": {
                    "exists": False,
                    "size_bytes": 0,
                    "visual_verification": {"ok": False, "reason": "file-missing"},
                },
                "termination": {"terminated": True},
                "authority": {"canonical_mutation_allowed": False},
                "checks": [
                    {"name": "host_policy_allows_launch", "ok": True, "detail": "not_applicable"},
                    {"name": "window_capture_ok", "ok": False, "detail": "missing"},
                    {"name": "screenshot_nonblank", "ok": False, "detail": "file-missing"},
                    {"name": "window_bounds_valid", "ok": True, "detail": "900 x 700"},
                    {"name": "no_markdown_writes", "ok": True, "detail": "unchanged"},
                    {"name": "no_approval_artifact_writes", "ok": True, "detail": "unchanged"},
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def _write_webview2_host_remediation_report(root: Path) -> Path:
    path = root / audit.WEBVIEW2_RUNTIME_HOST_REMEDIATION_REPORT_ROOT / "handoff.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "ok": True,
                "surface": "studio_webview2_runtime_host_remediation",
                "status": "webview2_runtime_host_remediation_ready",
                "latest_minimal_repro": {
                    "source_runtime_error_status": "webview2_initialization_failed",
                    "packaged_runtime_error_status": "webview2_initialization_failed",
                },
                "operator_handoff": {
                    "required_external_actions": ["Repair WebView2 Runtime."],
                    "acceptance_criteria": ["Minimal repro opens."],
                    "minimal_repro_command": "python -m chaseos studio pywebview-webview2-minimal-repro --json",
                    "packaged_visual_qa_command": "python -m chaseos studio packaged-app-visual-qa --json",
                },
                "authority": {
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
                },
                "next_recommended_pass": "operator-remediate-webview2-runtime-then-pass10b-minimal-repro-rerun",
            }
        ),
        encoding="utf-8",
    )
    return path


def _write_webview2_remediation_evidence_report(root: Path) -> Path:
    path = root / audit.WEBVIEW2_RUNTIME_REMEDIATION_EVIDENCE_REPORT_ROOT / "evidence.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "report_type": "webview2_runtime_remediation_evidence_intake",
                "ok": True,
                "surface": "studio_webview2_runtime_remediation_evidence",
                "status": "webview2_runtime_remediation_evidence_supplied",
                "remediation": {
                    "status": "performed",
                    "operator": "Host admin",
                    "summary": "WebView2 Runtime repair completed.",
                    "evidence_reference": "ticket CHASEOS-10B",
                },
                "readiness": {
                    "operator_remediation_evidence_supplied": True,
                    "remediation_effect_verified": False,
                    "next_recommended_pass": "pass10b-pywebview-webview2-minimal-repro-rerun-after-operator-remediation",
                },
                "authority": {
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
                },
                "next_recommended_pass": "pass10b-pywebview-webview2-minimal-repro-rerun-after-operator-remediation",
            }
        ),
        encoding="utf-8",
    )
    return path


def test_pass10b_visual_proof_completion_audit_reports_native_blocker(monkeypatch, tmp_path: Path) -> None:
    evidence = tmp_path / audit.BROWSER_NONBLANK_EVIDENCE
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"png")
    (tmp_path / audit.PASS10B_TEST_PATH).parent.mkdir(parents=True)
    (tmp_path / audit.PASS10B_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    (tmp_path / audit.DESKTOP_SHELL_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    monkeypatch.setattr(
        audit,
        "analyze_png_nonblank",
        lambda *_args, **_kwargs: {
            "ok": True,
            "reason": "passed",
            "unique_color_count": 12,
            "dominant_color_ratio": 0.5,
        },
    )
    monkeypatch.setattr(
        audit,
        "build_packaged_app_host_policy_unblock_readiness",
        lambda *_args, **_kwargs: {
            "status": "blocked_by_windows_application_control",
            "host_policy": {"status": "blocked_by_windows_application_control"},
            "readiness": {
                "host_policy_probe_performed": True,
                "host_policy_allows_launch": False,
                "native_visual_qa_complete": False,
            },
            "authority": {
                "mutates_host_policy": False,
                "signs_executable": False,
                "allowlists_executable": False,
                "writes_installer": False,
                "writes_host_startup": False,
                "executes_approval_decisions": False,
                "provider_calls_allowed": False,
                "connector_calls_allowed": False,
                "writes_agent_bus_tasks": False,
                "canonical_mutation_allowed": False,
            },
        },
    )

    report = audit.build_pass10b_visual_proof_completion_audit(
        tmp_path,
        probe_native_host_policy=True,
    )

    checklist = {item["id"]: item for item in report["prompt_to_artifact_checklist"]}
    assert report["ok"] is False
    assert report["status"] == "PARTIAL / BLOCKED_NATIVE_PACKAGED_VISUAL_QA"
    assert checklist["browser_graph_route_nonblank_verified"]["ok"] is True
    assert checklist["native_host_policy_allows_launch"]["ok"] is False
    assert checklist["native_packaged_visual_qa_complete"]["status"] == "BLOCKED"
    assert checklist["supplemental_native_screenshot_evidence_verified"]["status"] == "NOT_SUPPLIED"
    assert report["next_recommended_pass"] == "pass10b-native-host-policy-unblock"


def test_pass10b_visual_proof_completion_audit_marks_webview2_remediation_evidence_not_supplied(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _prepare_basic_audit_repo(monkeypatch, tmp_path)
    visual_report = _write_blocked_visual_qa_report(tmp_path)
    _write_webview2_host_remediation_report(tmp_path)

    report = audit.build_pass10b_visual_proof_completion_audit(
        tmp_path,
        packaged_visual_qa_report_path=visual_report,
    )

    checklist = {item["id"]: item for item in report["prompt_to_artifact_checklist"]}
    evidence_report = report["webview2_runtime_remediation_evidence_report_evidence"]
    assert report["ok"] is False
    assert evidence_report["status"] == "NOT_SUPPLIED"
    assert checklist["webview2_runtime_remediation_evidence_supplied"]["ok"] is False
    assert checklist["webview2_runtime_remediation_evidence_supplied"]["status"] == "NOT_SUPPLIED"
    assert report["next_recommended_pass"] == "operator-remediate-webview2-runtime-then-pass10b-minimal-repro-rerun"


def test_pass10b_visual_proof_completion_audit_routes_to_minimal_repro_after_webview2_evidence(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _prepare_basic_audit_repo(monkeypatch, tmp_path)
    visual_report = _write_blocked_visual_qa_report(tmp_path)
    _write_webview2_host_remediation_report(tmp_path)
    supplied = _write_webview2_remediation_evidence_report(tmp_path)

    report = audit.build_pass10b_visual_proof_completion_audit(
        tmp_path,
        packaged_visual_qa_report_path=visual_report,
        webview2_remediation_evidence_path=supplied,
    )

    checklist = {item["id"]: item for item in report["prompt_to_artifact_checklist"]}
    evidence_report = report["webview2_runtime_remediation_evidence_report_evidence"]
    assert report["ok"] is False
    assert evidence_report["ok"] is True
    assert evidence_report["remediation_effect_verified"] is False
    assert checklist["webview2_runtime_remediation_evidence_supplied"]["ok"] is True
    assert checklist["webview2_runtime_remediation_evidence_review_only"]["ok"] is True
    assert report["next_recommended_pass"] == "pass10b-pywebview-webview2-minimal-repro-rerun-after-operator-remediation"


def test_pass10b_visual_proof_completion_audit_includes_supplemental_native_evidence(
    monkeypatch, tmp_path: Path
) -> None:
    evidence = tmp_path / audit.BROWSER_NONBLANK_EVIDENCE
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"png")
    (tmp_path / audit.PASS10B_TEST_PATH).parent.mkdir(parents=True)
    (tmp_path / audit.PASS10B_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    (tmp_path / audit.DESKTOP_SHELL_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    supplied = tmp_path / "native.png"
    supplied.write_bytes(b"png")
    monkeypatch.setattr(
        audit,
        "analyze_png_nonblank",
        lambda *_args, **_kwargs: {
            "ok": True,
            "reason": "passed",
            "unique_color_count": 12,
            "dominant_color_ratio": 0.5,
        },
    )
    monkeypatch.setattr(
        audit,
        "build_packaged_app_host_policy_unblock_readiness",
        lambda *_args, **_kwargs: {
            "status": "blocked_by_windows_application_control",
            "host_policy": {"status": "blocked_by_windows_application_control"},
            "readiness": {
                "host_policy_probe_performed": True,
                "host_policy_allows_launch": False,
                "native_visual_qa_complete": False,
            },
            "authority": {
                "mutates_host_policy": False,
                "signs_executable": False,
                "allowlists_executable": False,
                "writes_installer": False,
                "writes_host_startup": False,
                "executes_approval_decisions": False,
                "provider_calls_allowed": False,
                "connector_calls_allowed": False,
                "writes_agent_bus_tasks": False,
                "canonical_mutation_allowed": False,
            },
        },
    )
    monkeypatch.setattr(
        audit,
        "build_pass10b_native_screenshot_evidence_intake",
        lambda *_args, **_kwargs: {
            "ok": True,
            "status": "SUPPLEMENTAL_NATIVE_SCREENSHOT_EVIDENCE_VERIFIED",
            "readiness": {
                "supplemental_native_screenshot_evidence_verified": True,
                "can_close_pass10b_native_visual_proof": False,
            },
        },
    )

    report = audit.build_pass10b_visual_proof_completion_audit(
        tmp_path,
        probe_native_host_policy=True,
        native_screenshot_path=supplied,
        native_screenshot_source="operator-native-packaged-window",
    )

    checklist = {item["id"]: item for item in report["prompt_to_artifact_checklist"]}
    assert report["ok"] is False
    assert checklist["supplemental_native_screenshot_evidence_checked"]["ok"] is True
    assert checklist["supplemental_native_screenshot_evidence_verified"]["ok"] is True
    assert checklist["supplemental_evidence_does_not_complete_automated_qa"]["ok"] is True
    assert checklist["native_packaged_visual_qa_complete"]["ok"] is False


def test_pass10b_visual_proof_completion_audit_reads_saved_native_evidence_report(
    monkeypatch, tmp_path: Path
) -> None:
    evidence = tmp_path / audit.BROWSER_NONBLANK_EVIDENCE
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"png")
    (tmp_path / audit.PASS10B_TEST_PATH).parent.mkdir(parents=True)
    (tmp_path / audit.PASS10B_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    (tmp_path / audit.DESKTOP_SHELL_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    saved_report = tmp_path / "saved-native-evidence.json"
    saved_report.write_text(
        json.dumps(
            {
                "report_type": "pass10b_native_screenshot_evidence_intake",
                "status": "VISUAL_EVIDENCE_NONBLANK_BUT_NOT_NATIVE",
                "ok": False,
                "screenshot": {
                    "path": "07_LOGS/Operator-Screenshots/browser-route.png",
                    "declared_source": "browser-static-route",
                },
                "readiness": {
                    "supplemental_native_screenshot_evidence_verified": False,
                    "automated_packaged_visual_qa_complete": False,
                    "can_close_pass10b_native_visual_proof": False,
                },
                "authority_note": (
                    "This evidence is supplemental and cannot complete automated packaged visual QA. "
                    "It does not launch or capture the packaged executable, mutate host policy, sign or allowlist "
                    "files, write installer/startup state, execute approvals, call providers/connectors, write "
                    "Agent Bus tasks, or mutate canonical state."
                ),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        audit,
        "analyze_png_nonblank",
        lambda *_args, **_kwargs: {
            "ok": True,
            "reason": "passed",
            "unique_color_count": 12,
            "dominant_color_ratio": 0.5,
        },
    )
    monkeypatch.setattr(
        audit,
        "build_packaged_app_host_policy_unblock_readiness",
        lambda *_args, **_kwargs: {
            "status": "blocked_by_windows_application_control",
            "host_policy": {"status": "blocked_by_windows_application_control"},
            "readiness": {
                "host_policy_probe_performed": True,
                "host_policy_allows_launch": False,
                "native_visual_qa_complete": False,
            },
            "authority": {
                "mutates_host_policy": False,
                "signs_executable": False,
                "allowlists_executable": False,
                "writes_installer": False,
                "writes_host_startup": False,
                "executes_approval_decisions": False,
                "provider_calls_allowed": False,
                "connector_calls_allowed": False,
                "writes_agent_bus_tasks": False,
                "canonical_mutation_allowed": False,
            },
        },
    )

    report = audit.build_pass10b_visual_proof_completion_audit(
        tmp_path,
        probe_native_host_policy=True,
        native_evidence_report_path=saved_report,
    )

    checklist = {item["id"]: item for item in report["prompt_to_artifact_checklist"]}
    saved = report["saved_native_screenshot_evidence_report"]
    assert report["ok"] is False
    assert saved["ok"] is True
    assert saved["report_type_valid"] is True
    assert saved["automated_qa_stays_incomplete"] is True
    assert checklist["supplemental_native_screenshot_evidence_report_valid"]["ok"] is True
    assert checklist["supplemental_native_screenshot_evidence_verified"]["ok"] is False
    assert checklist["supplemental_evidence_does_not_complete_automated_qa"]["ok"] is True
    assert checklist["native_packaged_visual_qa_complete"]["ok"] is False


def test_pass10b_visual_proof_completion_audit_accepts_saved_packaged_visual_qa_report(
    monkeypatch, tmp_path: Path
) -> None:
    evidence = tmp_path / audit.BROWSER_NONBLANK_EVIDENCE
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"png")
    (tmp_path / audit.PASS10B_TEST_PATH).parent.mkdir(parents=True)
    (tmp_path / audit.PASS10B_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    (tmp_path / audit.DESKTOP_SHELL_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    visual_report = tmp_path / "packaged-visual-qa.json"
    visual_report.write_text(
        json.dumps(
            {
                "ok": True,
                "surface": "studio_packaged_app_visual_qa",
                "model_version": "studio.packaged_app_visual_qa.v1",
                "status": "packaged_app_visual_qa_complete",
                "launch": {
                    "started": True,
                    "process_alive_before_capture": True,
                    "host_policy": {
                        "status": "not_applicable",
                        "blocked_by_windows_application_control": False,
                    },
                },
                "screenshot": {
                    "path": ".pytest_tmp_env/studio-packaged-app-visual-qa/native.png",
                    "exists": True,
                    "size_bytes": 4096,
                    "visual_verification": {"ok": True, "reason": "nonblank"},
                    "studio_content_sentinel": {"ok": True, "reason": "studio-content-sentinel-present"},
                },
                "termination": {"terminated": True},
                "authority": {
                    "launches_packaged_executable": True,
                    "captures_native_screenshot": True,
                    "terminates_owned_process": True,
                    "writes_visual_evidence": True,
                    "writes_installer": False,
                    "writes_host_startup": False,
                    "mutates_gate": False,
                    "grants_approvals": False,
                    "executes_approval_decisions": False,
                    "executes_workflows": False,
                    "provider_calls_allowed": False,
                    "connector_calls_allowed": False,
                    "writes_agent_bus_tasks": False,
                    "canonical_mutation_allowed": False,
                },
                "checks": [
                    {"name": "host_policy_allows_launch", "ok": True, "detail": "not_applicable"},
                    {"name": "window_capture_ok", "ok": True, "detail": "window screenshot captured"},
                    {"name": "screenshot_nonblank", "ok": True, "detail": "nonblank"},
                    {"name": "screenshot_studio_content_sentinel", "ok": True, "detail": "studio-content-sentinel-present"},
                    {"name": "window_bounds_valid", "ok": True, "detail": "900 x 700"},
                    {"name": "no_markdown_writes", "ok": True, "detail": "unchanged"},
                    {"name": "no_approval_artifact_writes", "ok": True, "detail": "unchanged"},
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        audit,
        "analyze_png_nonblank",
        lambda *_args, **_kwargs: {
            "ok": True,
            "reason": "passed",
            "unique_color_count": 12,
            "dominant_color_ratio": 0.5,
        },
    )
    monkeypatch.setattr(
        audit,
        "build_packaged_app_host_policy_unblock_readiness",
        lambda *_args, **_kwargs: {
            "status": "probe_not_requested",
            "host_policy": {"status": "not_applicable"},
            "readiness": {
                "host_policy_probe_performed": False,
                "host_policy_allows_launch": False,
                "native_visual_qa_complete": False,
            },
            "authority": {
                "mutates_host_policy": False,
                "signs_executable": False,
                "allowlists_executable": False,
                "writes_installer": False,
                "writes_host_startup": False,
                "executes_approval_decisions": False,
                "provider_calls_allowed": False,
                "connector_calls_allowed": False,
                "writes_agent_bus_tasks": False,
                "canonical_mutation_allowed": False,
            },
        },
    )

    report = audit.build_pass10b_visual_proof_completion_audit(
        tmp_path,
        packaged_visual_qa_report_path=visual_report,
    )

    checklist = {item["id"]: item for item in report["prompt_to_artifact_checklist"]}
    saved = report["packaged_visual_qa_report_evidence"]
    assert report["ok"] is True
    assert report["status"] == "COMPLETE / VERIFIED"
    assert saved["ok"] is True
    assert checklist["native_host_policy_probe_performed"]["ok"] is True
    assert checklist["native_host_policy_allows_launch"]["ok"] is True
    assert checklist["native_packaged_visual_qa_complete"]["ok"] is True
    assert checklist["packaged_visual_qa_saved_report_valid"]["ok"] is True


def test_pass10b_visual_proof_completion_audit_rejects_saved_packaged_visual_qa_without_content_sentinel(
    tmp_path: Path,
) -> None:
    visual_report = tmp_path / "packaged-visual-qa-without-content-sentinel.json"
    visual_report.write_text(
        json.dumps(
            {
                "ok": True,
                "surface": "studio_packaged_app_visual_qa",
                "model_version": "studio.packaged_app_visual_qa.v1",
                "status": "packaged_app_visual_qa_complete",
                "launch": {
                    "started": True,
                    "process_alive_before_capture": True,
                    "host_policy": {
                        "status": "not_applicable",
                        "blocked_by_windows_application_control": False,
                    },
                },
                "screenshot": {
                    "path": ".pytest_tmp_env/studio-packaged-app-visual-qa/native.png",
                    "exists": True,
                    "size_bytes": 4096,
                    "visual_verification": {"ok": True, "reason": "nonblank"},
                    "studio_content_sentinel": {"ok": False, "reason": "studio-content-sentinel-missing"},
                },
                "termination": {"terminated": True},
                "authority": {
                    "writes_installer": False,
                    "writes_host_startup": False,
                    "mutates_gate": False,
                    "grants_approvals": False,
                    "executes_approval_decisions": False,
                    "executes_workflows": False,
                    "provider_calls_allowed": False,
                    "connector_calls_allowed": False,
                    "writes_agent_bus_tasks": False,
                    "canonical_mutation_allowed": False,
                },
                "checks": [
                    {"name": "host_policy_allows_launch", "ok": True, "detail": "not_applicable"},
                    {"name": "window_capture_ok", "ok": True, "detail": "window screenshot captured"},
                    {"name": "screenshot_nonblank", "ok": True, "detail": "nonblank"},
                    {"name": "screenshot_studio_content_sentinel", "ok": False, "detail": "studio-content-sentinel-missing"},
                    {"name": "window_bounds_valid", "ok": True, "detail": "900 x 700"},
                    {"name": "no_markdown_writes", "ok": True, "detail": "unchanged"},
                    {"name": "no_approval_artifact_writes", "ok": True, "detail": "unchanged"},
                ],
            }
        ),
        encoding="utf-8",
    )

    saved = audit._inspect_packaged_visual_qa_report(tmp_path, visual_report)

    assert saved["ok"] is False
    assert saved["native_visual_qa_complete"] is False
    assert saved["studio_content_sentinel_verified"] is False
    assert saved["status"] == "PARTIAL"


def test_pass10b_visual_proof_completion_audit_rejects_blocked_packaged_visual_qa_report(
    monkeypatch, tmp_path: Path
) -> None:
    evidence = tmp_path / audit.BROWSER_NONBLANK_EVIDENCE
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"png")
    (tmp_path / audit.PASS10B_TEST_PATH).parent.mkdir(parents=True)
    (tmp_path / audit.PASS10B_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    (tmp_path / audit.DESKTOP_SHELL_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    visual_report = tmp_path / "blocked-packaged-visual-qa.json"
    visual_report.write_text(
        json.dumps(
            {
                "ok": False,
                "surface": "studio_packaged_app_visual_qa",
                "model_version": "studio.packaged_app_visual_qa.v1",
                "status": "blocked_packaged_app_visual_qa",
                "launch": {
                    "started": False,
                    "process_alive_before_capture": False,
                    "host_policy": {
                        "status": "blocked_by_windows_application_control",
                        "blocked_by_windows_application_control": True,
                    },
                },
                "screenshot": {
                    "exists": False,
                    "size_bytes": 0,
                    "visual_verification": {"ok": False, "reason": "file-missing"},
                },
                "termination": {"terminated": False},
                "authority": {"canonical_mutation_allowed": False},
                "checks": [
                    {"name": "host_policy_allows_launch", "ok": False, "detail": "blocked"},
                    {"name": "window_capture_ok", "ok": False, "detail": "missing"},
                    {"name": "screenshot_nonblank", "ok": False, "detail": "file-missing"},
                    {"name": "window_bounds_valid", "ok": False, "detail": "none"},
                    {"name": "no_markdown_writes", "ok": True, "detail": "unchanged"},
                    {"name": "no_approval_artifact_writes", "ok": True, "detail": "unchanged"},
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        audit,
        "analyze_png_nonblank",
        lambda *_args, **_kwargs: {
            "ok": True,
            "reason": "passed",
            "unique_color_count": 12,
            "dominant_color_ratio": 0.5,
        },
    )
    monkeypatch.setattr(
        audit,
        "build_packaged_app_host_policy_unblock_readiness",
        lambda *_args, **_kwargs: {
            "status": "blocked_by_windows_application_control",
            "host_policy": {"status": "blocked_by_windows_application_control"},
            "readiness": {
                "host_policy_probe_performed": True,
                "host_policy_allows_launch": False,
                "native_visual_qa_complete": False,
            },
            "authority": {
                "mutates_host_policy": False,
                "signs_executable": False,
                "allowlists_executable": False,
                "writes_installer": False,
                "writes_host_startup": False,
                "executes_approval_decisions": False,
                "provider_calls_allowed": False,
                "connector_calls_allowed": False,
                "writes_agent_bus_tasks": False,
                "canonical_mutation_allowed": False,
            },
        },
    )

    report = audit.build_pass10b_visual_proof_completion_audit(
        tmp_path,
        probe_native_host_policy=True,
        packaged_visual_qa_report_path=visual_report,
    )

    checklist = {item["id"]: item for item in report["prompt_to_artifact_checklist"]}
    assert report["ok"] is False
    assert report["packaged_visual_qa_report_evidence"]["ok"] is False
    assert checklist["packaged_visual_qa_saved_report_valid"]["ok"] is False
    assert checklist["native_packaged_visual_qa_complete"]["ok"] is False


def test_pass10b_visual_proof_completion_audit_recommends_webview2_diagnostic_for_runtime_blocker(
    monkeypatch, tmp_path: Path
) -> None:
    evidence = tmp_path / audit.BROWSER_NONBLANK_EVIDENCE
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"png")
    (tmp_path / audit.PASS10B_TEST_PATH).parent.mkdir(parents=True)
    (tmp_path / audit.PASS10B_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    (tmp_path / audit.DESKTOP_SHELL_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    visual_report = tmp_path / "webview2-blocked-packaged-visual-qa.json"
    visual_report.write_text(
        json.dumps(
            {
                "ok": False,
                "surface": "studio_packaged_app_visual_qa",
                "model_version": "studio.packaged_app_visual_qa.v1",
                "status": "blocked_packaged_app_visual_qa",
                "launch": {
                    "started": True,
                    "process_alive_before_capture": True,
                    "host_policy": {
                        "status": "not_applicable",
                        "blocked_by_windows_application_control": False,
                    },
                    "runtime_error": {
                        "status": "webview2_initialization_failed",
                        "blocked": True,
                    },
                },
                "screenshot": {
                    "exists": False,
                    "size_bytes": 0,
                    "visual_verification": {"ok": False, "reason": "file-missing"},
                },
                "termination": {"terminated": True},
                "authority": {"canonical_mutation_allowed": False},
                "checks": [
                    {"name": "host_policy_allows_launch", "ok": True, "detail": "not_applicable"},
                    {"name": "window_capture_ok", "ok": False, "detail": "window_handle_not_found"},
                    {"name": "screenshot_nonblank", "ok": False, "detail": "file-missing"},
                    {"name": "window_bounds_valid", "ok": False, "detail": "none"},
                    {"name": "no_markdown_writes", "ok": True, "detail": "unchanged"},
                    {"name": "no_approval_artifact_writes", "ok": True, "detail": "unchanged"},
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        audit,
        "analyze_png_nonblank",
        lambda *_args, **_kwargs: {
            "ok": True,
            "reason": "passed",
            "unique_color_count": 12,
            "dominant_color_ratio": 0.5,
        },
    )
    monkeypatch.setattr(
        audit,
        "build_packaged_app_host_policy_unblock_readiness",
        lambda *_args, **_kwargs: {
            "status": "host_policy_unblocked_visual_qa_retry_needed",
            "host_policy": {"status": "not_applicable"},
            "readiness": {
                "host_policy_probe_performed": True,
                "host_policy_allows_launch": True,
                "native_visual_qa_complete": False,
            },
            "authority": {
                "mutates_host_policy": False,
                "signs_executable": False,
                "allowlists_executable": False,
                "writes_installer": False,
                "writes_host_startup": False,
                "executes_approval_decisions": False,
                "provider_calls_allowed": False,
                "connector_calls_allowed": False,
                "writes_agent_bus_tasks": False,
                "canonical_mutation_allowed": False,
            },
        },
    )

    report = audit.build_pass10b_visual_proof_completion_audit(
        tmp_path,
        probe_native_host_policy=True,
        packaged_visual_qa_report_path=visual_report,
    )

    checklist = {item["id"]: item for item in report["prompt_to_artifact_checklist"]}
    assert report["ok"] is False
    assert report["packaged_visual_qa_report_evidence"]["runtime_error"]["blocked"] is True
    assert checklist["packaged_visual_qa_saved_report_valid"]["ok"] is False
    assert report["next_recommended_pass"] == "pass10b-webview2-runtime-diagnostic"


def test_pass10b_visual_proof_completion_audit_uses_latest_webview2_diagnostic_next_pass(
    monkeypatch, tmp_path: Path
) -> None:
    evidence = tmp_path / audit.BROWSER_NONBLANK_EVIDENCE
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"png")
    (tmp_path / audit.PASS10B_TEST_PATH).parent.mkdir(parents=True)
    (tmp_path / audit.PASS10B_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    (tmp_path / audit.DESKTOP_SHELL_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    visual_report = tmp_path / "webview2-blocked-packaged-visual-qa.json"
    visual_report.write_text(
        json.dumps(
            {
                "ok": False,
                "surface": "studio_packaged_app_visual_qa",
                "model_version": "studio.packaged_app_visual_qa.v1",
                "status": "blocked_packaged_app_visual_qa",
                "launch": {
                    "started": True,
                    "process_alive_before_capture": True,
                    "host_policy": {
                        "status": "not_applicable",
                        "blocked_by_windows_application_control": False,
                    },
                    "runtime_error": {
                        "status": "webview2_initialization_failed",
                        "blocked": True,
                    },
                },
                "screenshot": {
                    "exists": False,
                    "size_bytes": 0,
                    "visual_verification": {"ok": False, "reason": "file-missing"},
                },
                "termination": {"terminated": True},
                "authority": {"canonical_mutation_allowed": False},
                "checks": [
                    {"name": "host_policy_allows_launch", "ok": True, "detail": "not_applicable"},
                    {"name": "window_capture_ok", "ok": False, "detail": "window_handle_not_found"},
                    {"name": "screenshot_nonblank", "ok": False, "detail": "file-missing"},
                    {"name": "window_bounds_valid", "ok": False, "detail": "none"},
                    {"name": "no_markdown_writes", "ok": True, "detail": "unchanged"},
                    {"name": "no_approval_artifact_writes", "ok": True, "detail": "unchanged"},
                ],
            }
        ),
        encoding="utf-8",
    )
    diagnostic_root = tmp_path / audit.WEBVIEW2_DIAGNOSTIC_REPORT_ROOT
    diagnostic_root.mkdir(parents=True)
    diagnostic_report = diagnostic_root / "webview2-diagnostic.json"
    diagnostic_report.write_text(
        json.dumps(
            {
                "surface": "studio_packaged_app_webview2_diagnostic",
                "ok": False,
                "status": "blocked_webview2_initialization_with_workspace_runtime_dirs",
                "next_recommended_pass": "pass10b-system-temp-permission-or-webview2-policy-check",
                "authority": {
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
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        audit,
        "analyze_png_nonblank",
        lambda *_args, **_kwargs: {
            "ok": True,
            "reason": "passed",
            "unique_color_count": 12,
            "dominant_color_ratio": 0.5,
        },
    )
    monkeypatch.setattr(
        audit,
        "build_packaged_app_host_policy_unblock_readiness",
        lambda *_args, **_kwargs: {
            "status": "host_policy_unblocked_visual_qa_retry_needed",
            "host_policy": {"status": "not_applicable"},
            "readiness": {
                "host_policy_probe_performed": True,
                "host_policy_allows_launch": True,
                "native_visual_qa_complete": False,
            },
            "authority": {
                "mutates_host_policy": False,
                "signs_executable": False,
                "allowlists_executable": False,
                "writes_installer": False,
                "writes_host_startup": False,
                "executes_approval_decisions": False,
                "provider_calls_allowed": False,
                "connector_calls_allowed": False,
                "writes_agent_bus_tasks": False,
                "canonical_mutation_allowed": False,
            },
        },
    )

    report = audit.build_pass10b_visual_proof_completion_audit(
        tmp_path,
        probe_native_host_policy=True,
        packaged_visual_qa_report_path=visual_report,
    )

    checklist = {item["id"]: item for item in report["prompt_to_artifact_checklist"]}
    assert report["webview2_diagnostic_report_evidence"]["ok"] is True
    assert checklist["webview2_diagnostic_report_checked"]["ok"] is True
    assert report["next_recommended_pass"] == "pass10b-system-temp-permission-or-webview2-policy-check"


def test_pass10b_visual_proof_completion_audit_uses_latest_webview2_policy_check_next_pass(
    monkeypatch, tmp_path: Path
) -> None:
    evidence = tmp_path / audit.BROWSER_NONBLANK_EVIDENCE
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"png")
    (tmp_path / audit.PASS10B_TEST_PATH).parent.mkdir(parents=True)
    (tmp_path / audit.PASS10B_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    (tmp_path / audit.DESKTOP_SHELL_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    visual_report = tmp_path / "webview2-blocked-packaged-visual-qa.json"
    visual_report.write_text(
        json.dumps(
            {
                "ok": False,
                "surface": "studio_packaged_app_visual_qa",
                "model_version": "studio.packaged_app_visual_qa.v1",
                "status": "blocked_packaged_app_visual_qa",
                "launch": {
                    "started": True,
                    "process_alive_before_capture": True,
                    "host_policy": {"status": "not_applicable", "blocked_by_windows_application_control": False},
                    "runtime_error": {"status": "webview2_initialization_failed", "blocked": True},
                },
                "screenshot": {"exists": False, "size_bytes": 0, "visual_verification": {"ok": False}},
                "termination": {"terminated": True},
                "authority": {"canonical_mutation_allowed": False},
                "checks": [
                    {"name": "host_policy_allows_launch", "ok": True, "detail": "not_applicable"},
                    {"name": "window_capture_ok", "ok": False, "detail": "window_handle_not_found"},
                    {"name": "screenshot_nonblank", "ok": False, "detail": "file-missing"},
                    {"name": "window_bounds_valid", "ok": False, "detail": "none"},
                    {"name": "no_markdown_writes", "ok": True, "detail": "unchanged"},
                    {"name": "no_approval_artifact_writes", "ok": True, "detail": "unchanged"},
                ],
            }
        ),
        encoding="utf-8",
    )
    diagnostic_root = tmp_path / audit.WEBVIEW2_DIAGNOSTIC_REPORT_ROOT
    diagnostic_root.mkdir(parents=True)
    (diagnostic_root / "webview2-diagnostic.json").write_text(
        json.dumps(
            {
                "surface": "studio_packaged_app_webview2_diagnostic",
                "ok": False,
                "status": "blocked_webview2_initialization_with_workspace_runtime_dirs",
                "next_recommended_pass": "pass10b-system-temp-permission-or-webview2-policy-check",
                "authority": {
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
            }
        ),
        encoding="utf-8",
    )
    policy_root = tmp_path / audit.WEBVIEW2_POLICY_CHECK_REPORT_ROOT
    policy_root.mkdir(parents=True)
    (policy_root / "webview2-policy-check.json").write_text(
        json.dumps(
            {
                "surface": "studio_packaged_app_webview2_policy_check",
                "ok": False,
                "status": "blocked_temp_permission_and_cleanup_error",
                "next_recommended_pass": "pass10b-pywebview-temp-cleanup-diagnostic",
                "authority": {
                    "mutates_temp_acl": False,
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
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        audit,
        "analyze_png_nonblank",
        lambda *_args, **_kwargs: {"ok": True, "reason": "passed"},
    )
    monkeypatch.setattr(
        audit,
        "build_packaged_app_host_policy_unblock_readiness",
        lambda *_args, **_kwargs: {
            "status": "host_policy_unblocked_visual_qa_retry_needed",
            "readiness": {
                "host_policy_probe_performed": True,
                "host_policy_allows_launch": True,
                "native_visual_qa_complete": False,
            },
            "authority": {
                "mutates_host_policy": False,
                "signs_executable": False,
                "allowlists_executable": False,
                "writes_installer": False,
                "writes_host_startup": False,
                "executes_approval_decisions": False,
                "provider_calls_allowed": False,
                "connector_calls_allowed": False,
                "writes_agent_bus_tasks": False,
                "canonical_mutation_allowed": False,
            },
        },
    )

    report = audit.build_pass10b_visual_proof_completion_audit(
        tmp_path,
        probe_native_host_policy=True,
        packaged_visual_qa_report_path=visual_report,
    )

    checklist = {item["id"]: item for item in report["prompt_to_artifact_checklist"]}
    assert report["webview2_policy_check_report_evidence"]["ok"] is True
    assert checklist["webview2_policy_check_report_checked"]["ok"] is True
    assert report["next_recommended_pass"] == "pass10b-pywebview-temp-cleanup-diagnostic"


def test_pass10b_visual_proof_completion_audit_uses_minimal_repro_next_pass(
    monkeypatch, tmp_path: Path
) -> None:
    evidence = tmp_path / audit.BROWSER_NONBLANK_EVIDENCE
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"png")
    (tmp_path / audit.PASS10B_TEST_PATH).parent.mkdir(parents=True)
    (tmp_path / audit.PASS10B_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    (tmp_path / audit.DESKTOP_SHELL_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    visual_report = tmp_path / "webview2-blocked-packaged-visual-qa.json"
    visual_report.write_text(
        json.dumps(
            {
                "ok": False,
                "surface": "studio_packaged_app_visual_qa",
                "status": "blocked_packaged_app_visual_qa",
                "launch": {
                    "started": True,
                    "process_alive_before_capture": True,
                    "host_policy": {"status": "not_applicable", "blocked_by_windows_application_control": False},
                    "runtime_error": {"status": "webview2_initialization_failed", "blocked": True},
                },
                "screenshot": {"exists": False, "size_bytes": 0, "visual_verification": {"ok": False}},
                "termination": {"terminated": True},
                "authority": {"canonical_mutation_allowed": False},
                "checks": [
                    {"name": "host_policy_allows_launch", "ok": True, "detail": "not_applicable"},
                    {"name": "window_capture_ok", "ok": False, "detail": "window_handle_not_found"},
                    {"name": "screenshot_nonblank", "ok": False, "detail": "file-missing"},
                    {"name": "window_bounds_valid", "ok": False, "detail": "none"},
                    {"name": "no_markdown_writes", "ok": True, "detail": "unchanged"},
                    {"name": "no_approval_artifact_writes", "ok": True, "detail": "unchanged"},
                ],
            }
        ),
        encoding="utf-8",
    )
    policy_root = tmp_path / audit.WEBVIEW2_POLICY_CHECK_REPORT_ROOT
    policy_root.mkdir(parents=True)
    (policy_root / "webview2-policy-check.json").write_text(
        json.dumps(
            {
                "surface": "studio_packaged_app_webview2_policy_check",
                "ok": False,
                "status": "blocked_webview2_runtime_unexplained_after_temp_policy_check",
                "next_recommended_pass": "pass10b-pywebview-webview2-minimal-repro",
                "authority": {
                    "mutates_temp_acl": False,
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
            }
        ),
        encoding="utf-8",
    )
    minimal_root = tmp_path / audit.PYWEBVIEW_MINIMAL_REPRO_REPORT_ROOT
    minimal_root.mkdir(parents=True)
    (minimal_root / "minimal-repro.json").write_text(
        json.dumps(
            {
                "surface": "studio_pywebview_webview2_minimal_repro",
                "ok": False,
                "status": "blocked_minimal_pywebview_webview2_runtime",
                "source_probe": {
                    "status": "blocked_minimal_pywebview_source_probe",
                    "launch": {"runtime_error": {"status": "webview2_initialization_failed", "blocked": True}},
                },
                "visual_probe": {
                    "status": "blocked_packaged_app_visual_qa",
                    "launch": {"runtime_error": {"status": "webview2_initialization_failed", "blocked": True}},
                },
                "next_recommended_pass": "pass10b-webview2-runtime-host-remediation",
                "authority": {
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
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(audit, "analyze_png_nonblank", lambda *_args, **_kwargs: {"ok": True, "reason": "passed"})
    monkeypatch.setattr(
        audit,
        "build_packaged_app_host_policy_unblock_readiness",
        lambda *_args, **_kwargs: {
            "status": "host_policy_unblocked_visual_qa_retry_needed",
            "readiness": {
                "host_policy_probe_performed": True,
                "host_policy_allows_launch": True,
                "native_visual_qa_complete": False,
            },
            "authority": {
                "mutates_host_policy": False,
                "signs_executable": False,
                "allowlists_executable": False,
                "writes_installer": False,
                "writes_host_startup": False,
                "executes_approval_decisions": False,
                "provider_calls_allowed": False,
                "connector_calls_allowed": False,
                "writes_agent_bus_tasks": False,
                "canonical_mutation_allowed": False,
            },
        },
    )

    report = audit.build_pass10b_visual_proof_completion_audit(
        tmp_path,
        probe_native_host_policy=True,
        packaged_visual_qa_report_path=visual_report,
    )

    checklist = {item["id"]: item for item in report["prompt_to_artifact_checklist"]}
    assert report["pywebview_minimal_repro_report_evidence"]["ok"] is True
    assert checklist["pywebview_webview2_minimal_repro_report_checked"]["ok"] is True
    assert report["next_recommended_pass"] == "pass10b-webview2-runtime-host-remediation"


def test_pass10b_visual_proof_completion_audit_uses_webview2_remediation_next_pass(
    monkeypatch, tmp_path: Path
) -> None:
    evidence = tmp_path / audit.BROWSER_NONBLANK_EVIDENCE
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"png")
    (tmp_path / audit.PASS10B_TEST_PATH).parent.mkdir(parents=True)
    (tmp_path / audit.PASS10B_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    (tmp_path / audit.DESKTOP_SHELL_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    visual_report = tmp_path / "webview2-blocked-packaged-visual-qa.json"
    visual_report.write_text(
        json.dumps(
            {
                "ok": False,
                "surface": "studio_packaged_app_visual_qa",
                "status": "blocked_packaged_app_visual_qa",
                "launch": {
                    "started": True,
                    "process_alive_before_capture": True,
                    "host_policy": {"status": "not_applicable", "blocked_by_windows_application_control": False},
                    "runtime_error": {"status": "webview2_initialization_failed", "blocked": True},
                },
                "screenshot": {"exists": False, "size_bytes": 0, "visual_verification": {"ok": False}},
                "termination": {"terminated": True},
                "authority": {"canonical_mutation_allowed": False},
                "checks": [
                    {"name": "host_policy_allows_launch", "ok": True, "detail": "not_applicable"},
                    {"name": "window_capture_ok", "ok": False, "detail": "window_handle_not_found"},
                    {"name": "screenshot_nonblank", "ok": False, "detail": "file-missing"},
                    {"name": "window_bounds_valid", "ok": False, "detail": "none"},
                    {"name": "no_markdown_writes", "ok": True, "detail": "unchanged"},
                    {"name": "no_approval_artifact_writes", "ok": True, "detail": "unchanged"},
                ],
            }
        ),
        encoding="utf-8",
    )
    policy_root = tmp_path / audit.WEBVIEW2_POLICY_CHECK_REPORT_ROOT
    policy_root.mkdir(parents=True)
    (policy_root / "webview2-policy-check.json").write_text(
        json.dumps(
            {
                "surface": "studio_packaged_app_webview2_policy_check",
                "ok": False,
                "status": "blocked_webview2_runtime_unexplained_after_temp_policy_check",
                "next_recommended_pass": "pass10b-pywebview-webview2-minimal-repro",
                "authority": {
                    "mutates_temp_acl": False,
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
            }
        ),
        encoding="utf-8",
    )
    minimal_root = tmp_path / audit.PYWEBVIEW_MINIMAL_REPRO_REPORT_ROOT
    minimal_root.mkdir(parents=True)
    (minimal_root / "minimal-repro.json").write_text(
        json.dumps(
            {
                "surface": "studio_pywebview_webview2_minimal_repro",
                "ok": False,
                "status": "blocked_minimal_pywebview_webview2_runtime",
                "source_probe": {
                    "status": "blocked_minimal_pywebview_source_probe",
                    "launch": {"runtime_error": {"status": "webview2_initialization_failed", "blocked": True}},
                },
                "visual_probe": {
                    "status": "blocked_packaged_app_visual_qa",
                    "launch": {"runtime_error": {"status": "webview2_initialization_failed", "blocked": True}},
                },
                "next_recommended_pass": "pass10b-webview2-runtime-host-remediation",
                "authority": {
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
            }
        ),
        encoding="utf-8",
    )
    remediation_root = tmp_path / audit.WEBVIEW2_RUNTIME_HOST_REMEDIATION_REPORT_ROOT
    remediation_root.mkdir(parents=True)
    (remediation_root / "remediation.json").write_text(
        json.dumps(
            {
                "surface": "studio_webview2_runtime_host_remediation",
                "ok": True,
                "status": "webview2_runtime_host_remediation_ready",
                "latest_minimal_repro": {
                    "source_runtime_error_status": "webview2_initialization_failed",
                    "packaged_runtime_error_status": "webview2_initialization_failed",
                },
                "operator_handoff": {
                    "required_external_actions": ["Repair WebView2 runtime outside Codex."],
                    "acceptance_criteria": ["Minimal repro captures a nonblank screenshot."],
                    "minimal_repro_command": "python -m chaseos studio pywebview-webview2-minimal-repro --json",
                    "packaged_visual_qa_command": "python -m chaseos studio packaged-app-visual-qa --json",
                },
                "authority": {
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
                },
                "next_recommended_pass": "operator-remediate-webview2-runtime-then-pass10b-minimal-repro-rerun",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(audit, "analyze_png_nonblank", lambda *_args, **_kwargs: {"ok": True, "reason": "passed"})
    monkeypatch.setattr(
        audit,
        "build_packaged_app_host_policy_unblock_readiness",
        lambda *_args, **_kwargs: {
            "status": "host_policy_unblocked_visual_qa_retry_needed",
            "readiness": {
                "host_policy_probe_performed": True,
                "host_policy_allows_launch": True,
                "native_visual_qa_complete": False,
            },
            "authority": {
                "mutates_host_policy": False,
                "signs_executable": False,
                "allowlists_executable": False,
                "writes_installer": False,
                "writes_host_startup": False,
                "executes_approval_decisions": False,
                "provider_calls_allowed": False,
                "connector_calls_allowed": False,
                "writes_agent_bus_tasks": False,
                "canonical_mutation_allowed": False,
            },
        },
    )

    report = audit.build_pass10b_visual_proof_completion_audit(
        tmp_path,
        probe_native_host_policy=True,
        packaged_visual_qa_report_path=visual_report,
    )

    checklist = {item["id"]: item for item in report["prompt_to_artifact_checklist"]}
    assert report["webview2_runtime_host_remediation_report_evidence"]["ok"] is True
    assert checklist["webview2_runtime_host_remediation_review_only"]["ok"] is True
    assert report["next_recommended_pass"] == "operator-remediate-webview2-runtime-then-pass10b-minimal-repro-rerun"


def test_pass10b_visual_proof_completion_audit_uses_latest_workspace_temp_acl_next_pass(
    monkeypatch, tmp_path: Path
) -> None:
    evidence = tmp_path / audit.BROWSER_NONBLANK_EVIDENCE
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"png")
    (tmp_path / audit.PASS10B_TEST_PATH).parent.mkdir(parents=True)
    (tmp_path / audit.PASS10B_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    (tmp_path / audit.DESKTOP_SHELL_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    visual_report = tmp_path / "webview2-blocked-packaged-visual-qa.json"
    visual_report.write_text(
        json.dumps(
            {
                "ok": False,
                "surface": "studio_packaged_app_visual_qa",
                "model_version": "studio.packaged_app_visual_qa.v1",
                "status": "blocked_packaged_app_visual_qa",
                "launch": {
                    "started": True,
                    "process_alive_before_capture": True,
                    "host_policy": {"status": "not_applicable", "blocked_by_windows_application_control": False},
                    "runtime_error": {"status": "webview2_initialization_failed", "blocked": True},
                },
                "screenshot": {"exists": False, "size_bytes": 0, "visual_verification": {"ok": False}},
                "termination": {"terminated": True},
                "authority": {"canonical_mutation_allowed": False},
                "checks": [
                    {"name": "host_policy_allows_launch", "ok": True, "detail": "not_applicable"},
                    {"name": "window_capture_ok", "ok": False, "detail": "window_handle_not_found"},
                    {"name": "screenshot_nonblank", "ok": False, "detail": "file-missing"},
                    {"name": "window_bounds_valid", "ok": False, "detail": "none"},
                    {"name": "no_markdown_writes", "ok": True, "detail": "unchanged"},
                    {"name": "no_approval_artifact_writes", "ok": True, "detail": "unchanged"},
                ],
            }
        ),
        encoding="utf-8",
    )
    diagnostic_root = tmp_path / audit.WEBVIEW2_DIAGNOSTIC_REPORT_ROOT
    diagnostic_root.mkdir(parents=True)
    (diagnostic_root / "webview2-diagnostic.json").write_text(
        json.dumps(
            {
                "surface": "studio_packaged_app_webview2_diagnostic",
                "ok": False,
                "status": "blocked_webview2_initialization_with_workspace_runtime_dirs",
                "next_recommended_pass": "pass10b-system-temp-permission-or-webview2-policy-check",
                "authority": {
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
            }
        ),
        encoding="utf-8",
    )
    policy_root = tmp_path / audit.WEBVIEW2_POLICY_CHECK_REPORT_ROOT
    policy_root.mkdir(parents=True)
    (policy_root / "webview2-policy-check.json").write_text(
        json.dumps(
            {
                "surface": "studio_packaged_app_webview2_policy_check",
                "ok": False,
                "status": "blocked_system_and_workspace_temp_permission",
                "next_recommended_pass": "pass10b-workspace-temp-acl-cleanup-diagnostic",
                "authority": {
                    "mutates_temp_acl": False,
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
            }
        ),
        encoding="utf-8",
    )
    workspace_root = tmp_path / audit.WORKSPACE_TEMP_ACL_DIAGNOSTIC_REPORT_ROOT
    workspace_root.mkdir(parents=True)
    (workspace_root / "workspace-temp-diagnostic.json").write_text(
        json.dumps(
            {
                "surface": "studio_workspace_temp_acl_cleanup_diagnostic",
                "ok": False,
                "status": "blocked_prior_workspace_python_temp_override_failure",
                "next_recommended_pass": "pass10b-pyinstaller-pywebview-temp-minimal-repro",
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
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(audit, "analyze_png_nonblank", lambda *_args, **_kwargs: {"ok": True, "reason": "passed"})
    monkeypatch.setattr(
        audit,
        "build_packaged_app_host_policy_unblock_readiness",
        lambda *_args, **_kwargs: {
            "status": "host_policy_unblocked_visual_qa_retry_needed",
            "readiness": {
                "host_policy_probe_performed": True,
                "host_policy_allows_launch": True,
                "native_visual_qa_complete": False,
            },
            "authority": {
                "mutates_host_policy": False,
                "signs_executable": False,
                "allowlists_executable": False,
                "writes_installer": False,
                "writes_host_startup": False,
                "executes_approval_decisions": False,
                "provider_calls_allowed": False,
                "connector_calls_allowed": False,
                "writes_agent_bus_tasks": False,
                "canonical_mutation_allowed": False,
            },
        },
    )

    report = audit.build_pass10b_visual_proof_completion_audit(
        tmp_path,
        probe_native_host_policy=True,
        packaged_visual_qa_report_path=visual_report,
    )

    checklist = {item["id"]: item for item in report["prompt_to_artifact_checklist"]}
    assert report["workspace_temp_acl_diagnostic_report_evidence"]["ok"] is True
    assert checklist["workspace_temp_acl_diagnostic_report_checked"]["ok"] is True
    assert report["next_recommended_pass"] == "pass10b-pyinstaller-pywebview-temp-minimal-repro"


def test_pass10b_visual_proof_completion_audit_rejects_outside_native_evidence_report(
    tmp_path: Path,
) -> None:
    outside = tmp_path.parent / "outside-native-evidence.json"
    outside.write_text("{}", encoding="utf-8")

    report = audit._inspect_native_screenshot_evidence_report(
        tmp_path,
        outside,
    )

    assert report["ok"] is False
    assert report["status"] == "OUTSIDE_VAULT"
    outside.unlink()


def test_pass10b_visual_proof_completion_audit_includes_host_policy_handoff(
    monkeypatch, tmp_path: Path
) -> None:
    evidence = tmp_path / audit.BROWSER_NONBLANK_EVIDENCE
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"png")
    (tmp_path / audit.PASS10B_TEST_PATH).parent.mkdir(parents=True)
    (tmp_path / audit.PASS10B_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    (tmp_path / audit.DESKTOP_SHELL_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    handoff = tmp_path / "handoff.md"
    handoff.write_text(
        "\n".join(
            [
                "# Pass 10B Native Host Policy Unblock Handoff",
                "Windows Application Control blocked: True",
                "## Acceptance Criteria",
                "- Visual QA: `python -m chaseos studio packaged-app-visual-qa --json`",
                "## Authority Boundary",
                "- This handoff is review-only.",
                "- It does not mutate Windows Application Control, approval, Agent Bus, graph, or canonical state.",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        audit,
        "analyze_png_nonblank",
        lambda *_args, **_kwargs: {
            "ok": True,
            "reason": "passed",
            "unique_color_count": 12,
            "dominant_color_ratio": 0.5,
        },
    )
    monkeypatch.setattr(
        audit,
        "build_packaged_app_host_policy_unblock_readiness",
        lambda *_args, **_kwargs: {
            "status": "blocked_by_windows_application_control",
            "host_policy": {"status": "blocked_by_windows_application_control"},
            "readiness": {
                "host_policy_probe_performed": True,
                "host_policy_allows_launch": False,
                "native_visual_qa_complete": False,
            },
            "authority": {
                "mutates_host_policy": False,
                "signs_executable": False,
                "allowlists_executable": False,
                "writes_installer": False,
                "writes_host_startup": False,
                "executes_approval_decisions": False,
                "provider_calls_allowed": False,
                "connector_calls_allowed": False,
                "writes_agent_bus_tasks": False,
                "canonical_mutation_allowed": False,
            },
        },
    )

    report = audit.build_pass10b_visual_proof_completion_audit(
        tmp_path,
        probe_native_host_policy=True,
        host_policy_handoff_path=handoff,
    )

    checklist = {item["id"]: item for item in report["prompt_to_artifact_checklist"]}
    assert report["ok"] is False
    assert report["host_policy_handoff_evidence"]["ok"] is True
    assert checklist["host_policy_unblock_handoff_artifact_checked"]["ok"] is True
    assert checklist["host_policy_unblock_handoff_review_only"]["ok"] is True
    assert checklist["native_packaged_visual_qa_complete"]["ok"] is False


def test_pass10b_visual_proof_completion_audit_includes_workspace_temp_operator_handoff(
    monkeypatch,
    tmp_path: Path,
) -> None:
    evidence = tmp_path / audit.BROWSER_NONBLANK_EVIDENCE
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"png")
    (tmp_path / audit.PASS10B_TEST_PATH).parent.mkdir(parents=True)
    (tmp_path / audit.PASS10B_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    (tmp_path / audit.DESKTOP_SHELL_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    handoff = tmp_path / "workspace-temp-handoff.json"
    handoff.write_text(
        json.dumps(
            {
                "handoff_type": "pass10b_workspace_temp_acl_operator_handoff",
                "status": "workspace_temp_acl_operator_handoff_ready",
                "blocked_paths": [".pytest_tmp_env/studio-webview2-diagnostic/temp/tmp145s58f5"],
                "operator_handoff": {
                    "acceptance_criteria": ["`owned_probe_file_write_ok=true`"],
                    "visual_qa_command": "python -m chaseos studio packaged-app-visual-qa --json",
                },
                "authority": {
                    "review_only": True,
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
                "next_recommended_pass": "operator-repair-workspace-temp-acl-then-pass10b-native-visual-qa-rerun",
                "note": "This handoff is review-only. Workspace temp ACL blocker. Visual QA rerun required.",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        audit,
        "analyze_png_nonblank",
        lambda *_args, **_kwargs: {
            "ok": True,
            "reason": "passed",
            "unique_color_count": 12,
            "dominant_color_ratio": 0.5,
        },
    )
    monkeypatch.setattr(
        audit,
        "build_packaged_app_host_policy_unblock_readiness",
        lambda *_args, **_kwargs: {
            "status": "host_policy_unblocked_visual_qa_retry_needed",
            "host_policy": {"status": "not_applicable"},
            "readiness": {
                "host_policy_probe_performed": True,
                "host_policy_allows_launch": True,
                "native_visual_qa_complete": False,
            },
            "authority": {
                "mutates_host_policy": False,
                "signs_executable": False,
                "allowlists_executable": False,
                "writes_installer": False,
                "writes_host_startup": False,
                "executes_approval_decisions": False,
                "provider_calls_allowed": False,
                "connector_calls_allowed": False,
                "writes_agent_bus_tasks": False,
                "canonical_mutation_allowed": False,
            },
        },
    )
    monkeypatch.setattr(
        audit,
        "_inspect_packaged_visual_qa_report",
        lambda *_args, **_kwargs: {
            "ok": False,
            "status": "PARTIAL",
            "runtime_error": {"blocked": True, "status": "webview2_initialization_failed"},
            "host_policy_allows_launch": True,
            "native_visual_qa_complete": False,
        },
    )
    monkeypatch.setattr(
        audit,
        "_inspect_webview2_diagnostic_report",
        lambda *_args, **_kwargs: {
            "ok": True,
            "artifact_present": True,
            "status": "VERIFIED",
            "report_status": "blocked_webview2_initialization_with_workspace_runtime_dirs",
            "next_recommended_pass": "pass10b-system-temp-permission-or-webview2-policy-check",
        },
    )
    monkeypatch.setattr(
        audit,
        "_inspect_webview2_policy_check_report",
        lambda *_args, **_kwargs: {
            "ok": True,
            "artifact_present": True,
            "status": "VERIFIED",
            "report_status": "blocked_system_and_workspace_temp_permission",
            "next_recommended_pass": "pass10b-workspace-temp-acl-cleanup-diagnostic",
        },
    )
    monkeypatch.setattr(
        audit,
        "_inspect_workspace_temp_acl_diagnostic_report",
        lambda *_args, **_kwargs: {
            "ok": True,
            "artifact_present": True,
            "status": "VERIFIED",
            "report_status": "blocked_workspace_temp_probe_write",
            "next_recommended_pass": "pass10b-workspace-temp-acl-operator-handoff",
        },
    )

    report = audit.build_pass10b_visual_proof_completion_audit(
        tmp_path,
        probe_native_host_policy=True,
        workspace_temp_handoff_path=handoff,
    )

    checklist = {item["id"]: item for item in report["prompt_to_artifact_checklist"]}
    assert report["workspace_temp_acl_operator_handoff_evidence"]["ok"] is True
    assert checklist["workspace_temp_acl_operator_handoff_artifact_checked"]["ok"] is True
    assert checklist["workspace_temp_acl_operator_handoff_review_only"]["ok"] is True
    assert report["next_recommended_pass"] == "operator-repair-workspace-temp-acl-then-pass10b-native-visual-qa-rerun"
    assert report["ok"] is False


def test_pass10b_visual_proof_completion_audit_routes_host_policy_probe_to_saved_report_executable(
    monkeypatch,
    tmp_path: Path,
) -> None:
    evidence = tmp_path / audit.BROWSER_NONBLANK_EVIDENCE
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"png")
    (tmp_path / audit.PASS10B_TEST_PATH).parent.mkdir(parents=True)
    (tmp_path / audit.PASS10B_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    (tmp_path / audit.DESKTOP_SHELL_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    explicit_exe = ".pytest_tmp_env/custom-proof/dist/ChaseOS-Studio/ChaseOS-Studio.exe"
    visual_report = tmp_path / "saved-packaged-visual-qa.json"
    visual_report.write_text(
        json.dumps(
            {
                "ok": False,
                "surface": "studio_packaged_app_visual_qa",
                "model_version": "studio.packaged_app_visual_qa.v1",
                "status": "blocked_packaged_app_visual_qa",
                "executable": {"path": explicit_exe, "exists": True, "sha256": "abc123"},
                "launch": {
                    "started": True,
                    "process_alive_before_capture": True,
                    "host_policy": {
                        "status": "not_applicable",
                        "blocked_by_windows_application_control": False,
                    },
                    "runtime_error": {
                        "status": "webview2_initialization_failed",
                        "blocked": True,
                    },
                },
                "screenshot": {
                    "exists": False,
                    "size_bytes": 0,
                    "visual_verification": {"ok": False, "reason": "file-missing"},
                },
                "termination": {"terminated": True},
                "authority": {
                    "writes_installer": False,
                    "writes_host_startup": False,
                    "mutates_gate": False,
                    "grants_approvals": False,
                    "executes_approval_decisions": False,
                    "executes_workflows": False,
                    "provider_calls_allowed": False,
                    "connector_calls_allowed": False,
                    "writes_agent_bus_tasks": False,
                    "canonical_mutation_allowed": False,
                },
                "checks": [
                    {"name": "host_policy_allows_launch", "ok": True, "detail": "not_applicable"},
                    {"name": "window_capture_ok", "ok": False, "detail": "missing"},
                    {"name": "screenshot_nonblank", "ok": False, "detail": "file-missing"},
                    {"name": "window_bounds_valid", "ok": False, "detail": "none"},
                    {"name": "no_markdown_writes", "ok": True, "detail": "unchanged"},
                    {"name": "no_approval_artifact_writes", "ok": True, "detail": "unchanged"},
                ],
            }
        ),
        encoding="utf-8",
    )
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        audit,
        "analyze_png_nonblank",
        lambda *_args, **_kwargs: {
            "ok": True,
            "reason": "passed",
            "unique_color_count": 12,
            "dominant_color_ratio": 0.5,
        },
    )

    def fake_readiness(*_args, **kwargs):
        captured.update(kwargs)
        return {
            "status": "host_policy_unblocked_visual_qa_retry_needed",
            "host_policy": {"status": "not_applicable"},
            "readiness": {
                "host_policy_probe_performed": True,
                "host_policy_allows_launch": True,
                "native_visual_qa_complete": False,
            },
            "authority": {
                "mutates_host_policy": False,
                "signs_executable": False,
                "allowlists_executable": False,
                "writes_installer": False,
                "writes_host_startup": False,
                "executes_approval_decisions": False,
                "provider_calls_allowed": False,
                "connector_calls_allowed": False,
                "writes_agent_bus_tasks": False,
                "canonical_mutation_allowed": False,
            },
        }

    monkeypatch.setattr(audit, "build_packaged_app_host_policy_unblock_readiness", fake_readiness)

    report = audit.build_pass10b_visual_proof_completion_audit(
        tmp_path,
        probe_native_host_policy=True,
        packaged_visual_qa_report_path=visual_report,
    )

    assert captured["executable_path"] == explicit_exe
    assert report["packaged_visual_qa_report_evidence"]["executable_path"] == explicit_exe
    assert report["packaged_visual_qa_report_evidence"]["executable_path_valid"] is True
    assert report["native_probe_config"]["host_policy_probe_executable_source"] == "packaged_visual_qa_report"
    assert report["native_probe_config"]["host_policy_probe_executable_path"] == explicit_exe


def test_pass10b_visual_proof_completion_audit_passes_native_probe_timing(
    monkeypatch, tmp_path: Path
) -> None:
    evidence = tmp_path / audit.BROWSER_NONBLANK_EVIDENCE
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"png")
    (tmp_path / audit.PASS10B_TEST_PATH).parent.mkdir(parents=True)
    (tmp_path / audit.PASS10B_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    (tmp_path / audit.DESKTOP_SHELL_TEST_PATH).write_text("# tests\n", encoding="utf-8")
    captured: dict[str, float | bool] = {}
    monkeypatch.setattr(
        audit,
        "analyze_png_nonblank",
        lambda *_args, **_kwargs: {
            "ok": True,
            "reason": "passed",
            "unique_color_count": 12,
            "dominant_color_ratio": 0.5,
        },
    )

    def fake_readiness(*_args, **kwargs):
        captured.update(kwargs)
        return {
            "status": "blocked_by_windows_application_control",
            "host_policy": {"status": "blocked_by_windows_application_control"},
            "readiness": {
                "host_policy_probe_performed": True,
                "host_policy_allows_launch": False,
                "native_visual_qa_complete": False,
            },
            "authority": {
                "mutates_host_policy": False,
                "signs_executable": False,
                "allowlists_executable": False,
                "writes_installer": False,
                "writes_host_startup": False,
                "executes_approval_decisions": False,
                "provider_calls_allowed": False,
                "connector_calls_allowed": False,
                "writes_agent_bus_tasks": False,
                "canonical_mutation_allowed": False,
            },
        }

    monkeypatch.setattr(audit, "build_packaged_app_host_policy_unblock_readiness", fake_readiness)

    report = audit.build_pass10b_visual_proof_completion_audit(
        tmp_path,
        probe_native_host_policy=True,
        native_probe_settle_seconds=3.0,
        native_probe_window_timeout_seconds=10.0,
        native_probe_terminate_timeout_seconds=5.0,
    )

    assert captured["probe_launch"] is True
    assert captured["settle_seconds"] == 3.0
    assert captured["window_timeout_seconds"] == 10.0
    assert captured["terminate_timeout_seconds"] == 5.0
    assert report["native_probe_config"]["settle_seconds"] == 3.0
    assert report["native_probe_config"]["window_timeout_seconds"] == 10.0
    assert report["native_probe_config"]["terminate_timeout_seconds"] == 5.0


def test_pass10b_visual_proof_completion_audit_report_writer_stays_in_vault(tmp_path: Path) -> None:
    report = {
        "ok": False,
        "status": "PARTIAL / BLOCKED_NATIVE_PACKAGED_VISUAL_QA",
        "objective": "continue development on the pass 10b expansion pack",
        "success_criteria": ["Native screenshot must pass the nonblank gate."],
        "prompt_to_artifact_checklist": [
            {
                "id": "native_packaged_visual_qa_complete",
                "ok": False,
                "status": "BLOCKED",
                "evidence": "host_policy_readiness_status=blocked_by_windows_application_control",
            }
        ],
        "browser_visual_verification": {"ok": True},
        "host_policy_handoff_evidence": {
            "path": "handoff.md",
            "status": "VERIFIED",
            "review_only_boundary": True,
        },
        "native_probe_config": {"settle_seconds": 3.0},
        "missing_or_blocked": [
            {
                "id": "native_packaged_visual_qa_complete",
                "status": "BLOCKED",
                "evidence": "host_policy_readiness_status=blocked_by_windows_application_control",
            }
        ],
        "next_recommended_pass": "pass10b-native-host-policy-unblock",
    }

    evidence = audit.write_pass10b_visual_proof_completion_audit_report(
        tmp_path,
        report,
        report_slug="audit-test",
    )

    json_path = tmp_path / evidence["json_path"]
    markdown_path = tmp_path / evidence["markdown_path"]
    assert evidence["written"] is True
    assert json_path.is_file()
    assert markdown_path.is_file()
    assert "evidence-only" in markdown_path.read_text(encoding="utf-8")


def test_pass10b_visual_proof_completion_audit_report_writer_rejects_slug_escape_from_report_root(
    tmp_path: Path,
) -> None:
    report = {
        "ok": False,
        "status": "PARTIAL / BLOCKED_NATIVE_PACKAGED_VISUAL_QA",
        "objective": "continue development on the pass 10b expansion pack",
        "success_criteria": ["Native screenshot must pass the nonblank gate."],
        "prompt_to_artifact_checklist": [
            {
                "id": "native_packaged_visual_qa_complete",
                "ok": False,
                "status": "BLOCKED",
                "evidence": "host_policy_readiness_status=blocked_by_windows_application_control",
            }
        ],
        "browser_visual_verification": {"ok": True},
        "host_policy_handoff_evidence": {
            "path": "handoff.md",
            "status": "VERIFIED",
            "review_only_boundary": True,
        },
        "native_probe_config": {"settle_seconds": 3.0},
        "missing_or_blocked": [
            {
                "id": "native_packaged_visual_qa_complete",
                "status": "BLOCKED",
                "evidence": "host_policy_readiness_status=blocked_by_windows_application_control",
            }
        ],
        "next_recommended_pass": "pass10b-native-host-policy-unblock",
    }

    with pytest.raises(ValueError, match="report output must stay inside the report root"):
        audit.write_pass10b_visual_proof_completion_audit_report(
            tmp_path,
            report,
            report_root="reports",
            report_slug="../vault-local-but-outside-report-root",
        )
    assert (tmp_path / "reports").exists() is False
    assert (tmp_path / "vault-local-but-outside-report-root.json").exists() is False
    assert (tmp_path / "vault-local-but-outside-report-root.md").exists() is False


def test_pass10b_visual_proof_completion_audit_cli_returns_json_error_for_report_slug_escape(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    from runtime.cli.main import cmd_studio_pass10b_visual_proof_completion_audit

    monkeypatch.setattr(
        audit,
        "build_pass10b_visual_proof_completion_audit",
        lambda *_args, **_kwargs: {
            "ok": False,
            "status": "PARTIAL / BLOCKED_NATIVE_PACKAGED_VISUAL_QA",
            "objective": "continue development on the pass 10b expansion pack",
            "success_criteria": ["Native screenshot must pass the nonblank gate."],
            "prompt_to_artifact_checklist": [],
            "missing_or_blocked": [],
            "next_recommended_pass": "pass10b-native-host-policy-unblock",
        },
    )

    exit_code = cmd_studio_pass10b_visual_proof_completion_audit(
        argparse.Namespace(
            vault_root=str(tmp_path),
            probe_native_host_policy=False,
            native_probe_settle_seconds=1.0,
            native_probe_window_timeout_seconds=1.0,
            native_probe_terminate_timeout_seconds=1.0,
            native_screenshot_path=None,
            native_screenshot_source="unknown",
            native_evidence_report_path=None,
            packaged_visual_qa_report_path=None,
            host_policy_handoff_path=None,
            workspace_temp_handoff_path=None,
            write_report=True,
            report_root="reports",
            report_slug="../vault-local-but-outside-report-root",
            output_json=True,
        )
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 1
    assert payload["ok"] is False
    assert "report output must stay inside the report root" in payload["error"]
    assert captured.err == ""
    assert (tmp_path / "reports").exists() is False


def test_pass10b_visual_proof_completion_audit_parser_exposes_probe_screenshot_handoff_timing_and_report_flags() -> None:
    from runtime.cli.main import _build_parser

    parser = _build_parser()
    args = parser.parse_args(
        [
            "studio",
            "pass10b-visual-proof-completion-audit",
            "--probe-native-host-policy",
            "--native-probe-settle-seconds",
            "3",
            "--native-probe-window-timeout-seconds",
            "10",
            "--native-probe-terminate-timeout-seconds",
            "5",
            "--native-screenshot-path",
            "native.png",
            "--native-screenshot-source",
            "operator-native-packaged-window",
            "--host-policy-handoff-path",
            "handoff.md",
            "--workspace-temp-handoff-path",
            "workspace-handoff.json",
            "--native-evidence-report-path",
            "native-evidence.json",
            "--packaged-visual-qa-report-path",
            "packaged-visual-qa.json",
            "--webview2-remediation-evidence-path",
            "webview2-remediation-evidence.json",
            "--write-report",
            "--report-slug",
            "audit-report",
            "--report-root",
            "reports",
        ]
    )

    assert args.probe_native_host_policy is True
    assert args.native_probe_settle_seconds == 3.0
    assert args.native_probe_window_timeout_seconds == 10.0
    assert args.native_probe_terminate_timeout_seconds == 5.0
    assert args.native_screenshot_path == "native.png"
    assert args.native_screenshot_source == "operator-native-packaged-window"
    assert args.host_policy_handoff_path == "handoff.md"
    assert args.workspace_temp_handoff_path == "workspace-handoff.json"
    assert args.native_evidence_report_path == "native-evidence.json"
    assert args.packaged_visual_qa_report_path == "packaged-visual-qa.json"
    assert args.webview2_remediation_evidence_path == "webview2-remediation-evidence.json"
    assert args.write_report is True
    assert args.report_slug == "audit-report"
    assert args.report_root == "reports"
