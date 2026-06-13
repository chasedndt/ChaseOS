"""Tests for Studio MVP operator decision packet and closure gate."""

from __future__ import annotations

import json
from pathlib import Path

import runtime.studio.studio_mvp_operator_decision as decision_module
from runtime.studio.studio_mvp_operator_decision import (
    NEXT_RECOMMENDED_PASS,
    build_studio_mvp_closure_gate,
    build_studio_mvp_operator_decision_packet,
    format_studio_mvp_closure_gate,
    format_studio_mvp_operator_decision_packet,
)


def _fake_closeout() -> dict[str, object]:
    items = [
        {
            "id": "pass10b_installer_zip_proof",
            "title": "Pass 10B Installer ZIP Proof",
            "status": "COMPLETE / VERIFIED",
            "operator_required": False,
            "operator_input_types": [],
            "deferral_requirement": "Not deferrable.",
            "next_governed_surface": "pass10b-expansion-pack-completion-audit",
        },
        {
            "id": "branded_installer_logo_icon",
            "title": "Branded Installer Logo/Icon Packaging",
            "status": "PLANNED / OPERATOR BRAND DECISION REQUIRED",
            "operator_required": True,
            "operator_input_types": ["brand_asset_or_design_decision", "approval"],
            "deferral_requirement": "Operator must explicitly accept an unbranded MVP.",
            "next_governed_surface": "installer-plan",
        },
        {
            "id": "signing_chain",
            "title": "Code Signing Chain",
            "status": "BLOCKED / CREDENTIALS AND APPROVAL REQUIRED",
            "operator_required": True,
            "operator_input_types": ["credential_or_secret", "environment_variable", "approval"],
            "deferral_requirement": "Operator must explicitly accept unsigned artifacts.",
            "next_governed_surface": "signing-approval-preview",
        },
        {
            "id": "startup_autostart_host_mutation",
            "title": "Startup/Autostart Host Mutation",
            "status": "BLOCKED / HOST MUTATION APPROVAL REQUIRED",
            "operator_required": True,
            "operator_input_types": ["host_admin_action", "approval", "manual_test"],
            "deferral_requirement": "Operator must explicitly defer startup/autostart.",
            "next_governed_surface": "startup-autostart-approval-preview",
        },
        {
            "id": "release_promotion",
            "title": "Release Promotion",
            "status": "BLOCKED / RELEASE DECISION REQUIRED",
            "operator_required": True,
            "operator_input_types": ["operator_decision", "approval"],
            "deferral_requirement": "Operator must explicitly keep MVP internal.",
            "next_governed_surface": "release-promotion-approval-preview",
        },
        {
            "id": "real_install_launch_manual_test",
            "title": "Real Install/Launch Manual Test",
            "status": "BLOCKED / OPERATOR MANUAL TEST REQUIRED",
            "operator_required": True,
            "operator_input_types": ["manual_test", "approval"],
            "deferral_requirement": "Operator must explicitly accept automated packaging evidence.",
            "next_governed_surface": "packaged-app-launch-smoke",
        },
        {
            "id": "real_target_workspace_migration",
            "title": "Real Target Workspace Migration",
            "status": "BLOCKED / TARGET PATH AND APPROVAL REQUIRED",
            "operator_required": True,
            "operator_input_types": ["operator_selected_path", "approval", "manual_test"],
            "deferral_requirement": "Operator must explicitly defer real target migration.",
            "next_governed_surface": "approved-target-upgrade-executor",
        },
        {
            "id": "provider_model_live_calls",
            "title": "Provider/Model Live Calls",
            "status": "BLOCKED / ENV AND PROVIDER APPROVAL REQUIRED",
            "operator_required": True,
            "operator_input_types": ["environment_variable", "credential_or_secret", "approval"],
            "deferral_requirement": "Operator must explicitly keep live provider calls outside MVP.",
            "next_governed_surface": "phase11-chat-live-provider-execution-approval-preview",
        },
        {
            "id": "runtime_dispatch_activation",
            "title": "Runtime/Adapter Dispatch Activation",
            "status": "BLOCKED / RUNTIME AUTHORITY REQUIRED",
            "operator_required": True,
            "operator_input_types": ["operator_decision", "approval"],
            "deferral_requirement": "Operator must explicitly keep runtime dispatch disabled.",
            "next_governed_surface": "phase11-chat-runtime-dispatch-readiness-contract",
        },
        {
            "id": "browser_dispatch_activation",
            "title": "Browser Dispatch Activation",
            "status": "BLOCKED / TARGET URL OR PROFILE AND APPROVAL REQUIRED",
            "operator_required": True,
            "operator_input_types": ["external_target", "approval", "manual_test"],
            "deferral_requirement": "Operator must explicitly keep browser dispatch out of MVP.",
            "next_governed_surface": "phase11-chat-browser-dispatch-readiness-contract",
        },
        {
            "id": "companion_selection_executor",
            "title": "Companion Selection Approval Consumption Executor",
            "status": "BLOCKED / APPROVAL CONSUMPTION REQUIRED",
            "operator_required": True,
            "operator_input_types": ["operator_decision", "approval"],
            "deferral_requirement": "Operator must explicitly defer selection consumption.",
            "next_governed_surface": "phase11-chat-companion-selection-approval-consumption-readiness",
        },
        {
            "id": "persisted_graph_storage_durable_ids",
            "title": "Persisted Graph Storage/Durable IDs",
            "status": "PLANNED / PRODUCT SCOPE DECISION REQUIRED",
            "operator_required": True,
            "operator_input_types": ["operator_decision"],
            "deferral_requirement": "Operator must explicitly accept derived graph surfaces.",
            "next_governed_surface": "graph-index-contract",
        },
    ]
    return {
        "summary": {
            "pass10b_installer_zip_proof_complete": True,
            "operator_human_in_loop_required": True,
            "remaining_operator_required_count": 11,
        },
        "operator_human_in_loop_matrix": items,
        "must_not_be_auto_run": ["signing certificate/password/token handling"],
    }


def test_operator_decision_packet_acknowledges_deferrals_and_leaves_manual_gate(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(decision_module, "build_studio_mvp_deferral_closeout_audit", lambda *_args, **_kwargs: _fake_closeout())

    packet = build_studio_mvp_operator_decision_packet(
        tmp_path,
        acknowledge_preapproved_deferrals=True,
    )
    summary = packet["summary"]
    decisions = {item["id"]: item for item in packet["decisions"]}

    assert packet["closed"] is False
    assert summary["operator_deferrals_acknowledged"] is True
    assert summary["deferred_for_internal_portable_mvp_count"] == 10
    assert summary["remaining_required_items"] == ["real_install_launch_manual_test"]
    assert summary["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert decisions["pass10b_installer_zip_proof"]["decision"] == "accepted_existing_evidence"
    assert decisions["signing_chain"]["decision"] == "deferred_for_internal_portable_mvp"
    assert decisions["signing_chain"]["decision_status"] == "DEFERRED / OPERATOR ACKNOWLEDGED"
    assert decisions["real_install_launch_manual_test"]["decision"] == "selected_for_manual_acceptance"
    assert "decision_digest_sha256" in packet


def test_operator_decision_packet_requires_acknowledgement_before_write(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(decision_module, "build_studio_mvp_deferral_closeout_audit", lambda *_args, **_kwargs: _fake_closeout())

    try:
        build_studio_mvp_operator_decision_packet(tmp_path, write_decision=True)
    except ValueError as exc:
        assert "requires --acknowledge-preapproved-deferrals" in str(exc)
    else:
        raise AssertionError("write without acknowledgement should fail")


def test_operator_decision_packet_writes_decision_and_closure_gate_reports_manual_blocker(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(decision_module, "build_studio_mvp_deferral_closeout_audit", lambda *_args, **_kwargs: _fake_closeout())

    packet = build_studio_mvp_operator_decision_packet(
        tmp_path,
        acknowledge_preapproved_deferrals=True,
        write_decision=True,
        decision_slug="test-studio-mvp-operator-decision",
    )
    gate = build_studio_mvp_closure_gate(tmp_path, write_report=True, report_slug="test-studio-mvp-closure-gate")

    assert Path(tmp_path / packet["evidence"]["json_path"]).is_file()
    assert Path(tmp_path / packet["evidence"]["markdown_path"]).is_file()
    assert gate["closed"] is False
    assert gate["summary"]["operator_deferrals_acknowledged"] is True
    assert gate["summary"]["manual_acceptance_complete"] is False
    assert gate["blockers"] == ["manual_install_launch_acceptance_missing"]
    assert Path(tmp_path / gate["evidence"]["json_path"]).is_file()
    assert Path(tmp_path / gate["evidence"]["markdown_path"]).is_file()
    payload = json.loads(Path(tmp_path / packet["evidence"]["json_path"]).read_text(encoding="utf-8"))
    assert payload["summary"]["remaining_required_items"] == ["real_install_launch_manual_test"]


def test_operator_decision_packet_can_close_with_manual_acceptance_evidence(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(decision_module, "build_studio_mvp_deferral_closeout_audit", lambda *_args, **_kwargs: _fake_closeout())
    evidence = tmp_path / "07_LOGS" / "Manual-Acceptance" / "accepted.md"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("Operator accepted launch smoke.", encoding="utf-8")

    packet = build_studio_mvp_operator_decision_packet(
        tmp_path,
        acknowledge_preapproved_deferrals=True,
        manual_acceptance_status="accepted",
        manual_acceptance_evidence_path=evidence,
        write_decision=True,
        decision_slug="accepted-studio-mvp-operator-decision",
    )
    gate = build_studio_mvp_closure_gate(tmp_path)
    text = format_studio_mvp_closure_gate(gate)

    assert packet["closed"] is True
    assert gate["closed"] is False
    assert gate["blockers"] == ["manual_acceptance_evidence_invalid"]
    assert "manual_acceptance_evidence_invalid" in text


def test_operator_decision_formatters_show_boundaries(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(decision_module, "build_studio_mvp_deferral_closeout_audit", lambda *_args, **_kwargs: _fake_closeout())

    packet = build_studio_mvp_operator_decision_packet(tmp_path, acknowledge_preapproved_deferrals=True)
    gate = build_studio_mvp_closure_gate(tmp_path)
    packet_text = format_studio_mvp_operator_decision_packet(packet)
    gate_text = format_studio_mvp_closure_gate(gate)

    assert "Studio MVP Operator Decision Packet" in packet_text
    assert "no approval consumption/execution" in packet_text
    assert "real_install_launch_manual_test" in packet_text
    assert "Studio MVP Closure Gate" in gate_text
    assert "decision_packet_missing_or_invalid" in gate_text
