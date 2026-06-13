"""Tests for the Full Studio desktop/card UI inventory proof packet."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.full_desktop_card_ui_inventory_proof import (
    SURFACE_ID,
    build_full_desktop_card_ui_inventory_proof,
    write_full_desktop_card_ui_inventory_proof,
)

VAULT_ROOT = Path(__file__).resolve().parents[2]


def test_full_desktop_card_ui_inventory_proof_enumerates_live_registry_truth() -> None:
    packet = build_full_desktop_card_ui_inventory_proof(
        VAULT_ROOT,
        generated_at="2026-05-12T02:00:00Z",
    )

    assert packet["ok"] is True
    assert packet["surface"] == SURFACE_ID
    assert packet["claim_decision"]["full_desktop_card_ui_closed"] is False
    assert packet["summary"]["live_registry_mounted_panel_count"] == len(
        packet["card_inventory"]["mounted_native_ui"]
    )
    assert packet["summary"]["live_registry_mounted_panel_count"] >= 30
    assert packet["summary"]["approval_gated_panel_count"] == 4
    assert {panel["id"] for panel in packet["card_inventory"]["approval_gated"]} == {
        "graph",
        "node-inspector",
        "chat",
        "runtime-cockpit",
    }
    assert packet["card_inventory"]["preview_or_proof_only"]
    assert packet["card_inventory"]["blocked_or_non_executable"]


def test_full_desktop_card_ui_inventory_proof_preserves_newer_blocked_pass10b_audit_and_boundaries() -> None:
    packet = build_full_desktop_card_ui_inventory_proof(
        VAULT_ROOT,
        generated_at="2026-05-12T02:00:00Z",
    )

    audit = packet["source_references"]["latest_pass10b_completion_audit"]
    installer_audit = packet["source_references"]["installer_lane_preferred_pass10b_completion_audit"]
    assert audit["exists"] is True
    assert audit["ok"] is False
    assert audit["status"] == "PARTIAL / BLOCKED_NATIVE_PACKAGED_VISUAL_QA"
    assert audit["path"] == (
        "07_LOGS/Studio-Graph-Views/pass10b-completion-audits/"
        "2026-05-12-pass10b-webview2-no-remediation-current-audit.json"
    )
    assert audit["selection_source"] == "latest_current_pass10b_audit_newer_blocked_evidence"
    assert installer_audit["ok"] is True
    assert installer_audit["status"] == "COMPLETE / VERIFIED"
    assert installer_audit["selection_source"] == "studio_installer_plan_preferred_pass10b_audit"
    assert packet["summary"]["pass10b_current_ok"] is False
    assert packet["summary"]["pass10b_current_status"] == "PARTIAL / BLOCKED_NATIVE_PACKAGED_VISUAL_QA"
    assert packet["summary"]["roadmap_item_should_remain_open"] is True
    assert packet["claim_decision"]["full_desktop_card_ui_closed"] is False
    assert packet["product_lane"]["native_lane_command"] == "chaseos studio shell"
    assert packet["product_lane"]["legacy_compatibility_qa_lane_command"] == "chaseos studio desktop-shell-app"
    assert all(value is False for value in packet["authority"].values())
    assert any(check["name"] == "pass10b_current_audit_state_preserved" and check["ok"] for check in packet["checks"])
    assert packet["status"] == "card_inventory_packet_ready_pass10b_still_blocked"
    assert packet["next_recommended_pass"] == "operator-remediate-webview2-runtime-then-pass10b-minimal-repro-rerun"


def test_full_desktop_card_ui_inventory_write_report_creates_readonly_json_packet(tmp_path: Path) -> None:
    output_path = tmp_path / "inventory-proof.json"
    packet = write_full_desktop_card_ui_inventory_proof(
        VAULT_ROOT,
        generated_at="2026-05-12T02:00:00Z",
        output_path=output_path,
    )

    assert output_path.is_file()
    saved = json.loads(output_path.read_text(encoding="utf-8"))
    expected_report = output_path.relative_to(VAULT_ROOT).as_posix()
    assert saved["written_report"] == expected_report
    assert saved["surface"] == SURFACE_ID
    assert saved["claim_decision"]["full_desktop_card_ui_closed"] is False
    assert saved["summary"]["approval_gated_panel_count"] == 4
    assert packet["written_report"] == expected_report
