"""Tests for the Studio MVP deferral closeout audit."""

from __future__ import annotations

import json
from pathlib import Path

import runtime.studio.studio_mvp_deferral_closeout_audit as audit_module
from runtime.studio.studio_mvp_deferral_closeout_audit import (
    NEXT_RECOMMENDED_PASS,
    PASS_ID,
    build_studio_mvp_deferral_closeout_audit,
    format_studio_mvp_deferral_closeout_audit,
)


def _fake_pass10b_report() -> dict[str, object]:
    return {
        "ok": True,
        "complete": True,
        "status": "COMPLETE / VERIFIED",
        "next_recommended_pass": "studio-signing-approval-preview",
        "summary": {
            "approval_packet_id": "studio-installer-build-appr-test",
            "current_pass10b_visual_proof_verified": True,
            "approved_execution_performed": True,
            "installer_outputs_present": True,
            "no_forbidden_mutation_detected": True,
            "next_recommended_pass": "studio-signing-approval-preview",
        },
    }


def _fake_partial_pass10b_with_installer_zip_report() -> dict[str, object]:
    report = _fake_pass10b_report()
    report["ok"] = False
    report["complete"] = False
    report["status"] = "BLOCKED / EVIDENCE INCOMPLETE"
    report["summary"]["card_ui_inventory_current"] = False
    report["summary"]["full_desktop_card_ui_closed"] = False
    return report


def test_mvp_deferral_audit_classifies_operator_required_inputs(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        audit_module,
        "build_pass10b_expansion_pack_completion_audit",
        lambda *_args, **_kwargs: _fake_pass10b_report(),
    )

    audit = build_studio_mvp_deferral_closeout_audit(tmp_path)
    summary = audit["summary"]
    items = {item["id"]: item for item in audit["operator_human_in_loop_matrix"]}

    assert audit["ok"] is True
    assert audit["closed"] is False
    assert audit["surface"] == "studio_mvp_deferral_closeout_audit"
    assert audit["pass"] == PASS_ID
    assert summary["mvp_closed"] is False
    assert summary["pass10b_installer_zip_proof_complete"] is True
    assert summary["operator_human_in_loop_required"] is True
    assert summary["machine_can_continue_without_operator"] is False
    assert summary["next_recommended_pass"] == NEXT_RECOMMENDED_PASS

    assert items["pass10b_installer_zip_proof"]["operator_required"] is False
    assert items["signing_chain"]["operator_required"] is True
    assert "credential_or_secret" in items["signing_chain"]["operator_input_types"]
    assert "environment_variable" in items["signing_chain"]["operator_input_types"]
    assert "operator_selected_path" in items["real_target_workspace_migration"]["operator_input_types"]
    assert "manual_test" in items["real_install_launch_manual_test"]["operator_input_types"]
    assert "external_target" in items["browser_dispatch_activation"]["operator_input_types"]
    assert "brand_asset_or_design_decision" in items["branded_installer_logo_icon"]["operator_input_types"]


def test_mvp_deferral_audit_separates_installer_zip_proof_from_full_pass10b_expansion(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        audit_module,
        "build_pass10b_expansion_pack_completion_audit",
        lambda *_args, **_kwargs: _fake_partial_pass10b_with_installer_zip_report(),
    )

    audit = build_studio_mvp_deferral_closeout_audit(tmp_path)
    items = {item["id"]: item for item in audit["operator_human_in_loop_matrix"]}

    assert audit["summary"]["pass10b_installer_zip_proof_complete"] is True
    assert items["pass10b_installer_zip_proof"]["status"] == "COMPLETE / VERIFIED"
    assert items["pass10b_installer_zip_proof"]["evidence"]["full_pass10b_expansion_pack_complete"] is False


def test_mvp_deferral_audit_deferral_candidates_require_operator_decision(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        audit_module,
        "build_pass10b_expansion_pack_completion_audit",
        lambda *_args, **_kwargs: _fake_pass10b_report(),
    )

    audit = build_studio_mvp_deferral_closeout_audit(tmp_path)
    deferrals = {item["id"]: item for item in audit["deferral_candidates"]}

    assert audit["summary"]["all_remaining_items_can_be_deferred_with_operator_decision"] is True
    assert "signing_chain" in deferrals
    assert "real_target_workspace_migration" in deferrals
    assert "provider_model_live_calls" in deferrals
    assert "Operator must explicitly" in deferrals["signing_chain"]["deferral_requirement"]
    assert audit["summary"]["credential_or_secret_required"] is True
    assert audit["summary"]["environment_variable_required"] is True
    assert audit["summary"]["manual_testing_required"] is True
    assert audit["summary"]["target_path_required"] is True
    assert audit["summary"]["host_mutation_approval_required"] is True


def test_mvp_deferral_audit_authority_is_report_only_and_formatted(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        audit_module,
        "build_pass10b_expansion_pack_completion_audit",
        lambda *_args, **_kwargs: _fake_pass10b_report(),
    )

    audit = build_studio_mvp_deferral_closeout_audit(tmp_path)
    authority = audit["authority"]
    text = format_studio_mvp_deferral_closeout_audit(audit)

    assert authority["read_only"] is True
    assert authority["approval_consumption_allowed"] is False
    assert authority["signing_allowed"] is False
    assert authority["reads_credentials_or_secrets"] is False
    assert authority["provider_calls_allowed"] is False
    assert authority["runtime_dispatch_allowed"] is False
    assert authority["browser_control_allowed"] is False
    assert authority["host_mutation_allowed"] is False
    assert authority["target_mutation_allowed"] is False
    assert authority["canonical_mutation_allowed"] is False
    assert "Operator-required items:" in text
    assert "signing_chain" in text
    assert "credential_or_secret" in text
    assert "Boundary: report-only audit" in text


def test_mvp_deferral_audit_writes_bounded_json_and_markdown_report(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        audit_module,
        "build_pass10b_expansion_pack_completion_audit",
        lambda *_args, **_kwargs: _fake_pass10b_report(),
    )

    audit = build_studio_mvp_deferral_closeout_audit(
        tmp_path,
        write_report=True,
        report_slug="test-studio-mvp-deferral-closeout-audit",
    )

    assert audit["evidence"]["written"] is True
    assert audit["evidence"]["json_path"].endswith("test-studio-mvp-deferral-closeout-audit.json")
    assert audit["evidence"]["markdown_path"].endswith("test-studio-mvp-deferral-closeout-audit.md")
    json_path = tmp_path / audit["evidence"]["json_path"]
    markdown_path = tmp_path / audit["evidence"]["markdown_path"]
    assert json_path.is_file()
    assert markdown_path.is_file()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["surface"] == "studio_mvp_deferral_closeout_audit"
    assert payload["summary"]["operator_human_in_loop_required"] is True
    assert "Studio MVP Deferral Closeout Audit" in markdown_path.read_text(encoding="utf-8")
