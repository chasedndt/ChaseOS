"""Tests for the Phase 11 read-only operator dashboard aggregate audit."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase11_readonly_operator_dashboard_aggregate_audit import (
    NEXT_RECOMMENDED_PASS,
    build_phase11_readonly_operator_dashboard_aggregate_audit,
    format_phase11_readonly_operator_dashboard_aggregate_audit,
)


EXPECTED_SOURCE_IDS = {
    "slash_dashboard_response",
    "approval_center",
    "provider_readiness",
    "runtime_status",
    "companion_status",
    "recent_build_logs",
    "slash_catalog",
}

EXPECTED_CARD_IDS = {
    "dashboard-summary",
    "approval-center",
    "provider-status",
    "companion-status",
    "recent-build-logs",
    "runtime-status",
}


def _seed_vault(vault: Path) -> None:
    (vault / "README.md").write_text("# Test Vault\n\nSee [[Runtime Status]].\n", encoding="utf-8")
    logs = vault / "07_LOGS" / "Build-Logs"
    logs.mkdir(parents=True)
    (logs / "2026-05-12-ChaseOS-test.md").write_text("# Test Build Log\n", encoding="utf-8")
    profile = vault / "06_AGENTS" / "Hermes-Runtime-Profile.md"
    profile.parent.mkdir(parents=True)
    profile.write_text(
        "---\ntitle: Hermes Runtime Profile\nruntime: hermes\nstatus: active test lane\n---\n# Hermes\n",
        encoding="utf-8",
    )


def test_dashboard_aggregate_audit_covers_readonly_sources_without_execution(tmp_path: Path) -> None:
    _seed_vault(tmp_path)

    audit = build_phase11_readonly_operator_dashboard_aggregate_audit(tmp_path)

    summary = audit["summary"]
    source_ids = {item["source_id"] for item in audit["source_audits"]}
    card_ids = set(summary["aggregate_card_ids"])

    assert audit["ok"] is True
    assert audit["surface"] == "phase11_readonly_operator_dashboard_aggregate_audit"
    assert audit["pass"] == "phase11-chat-readonly-operator-dashboard-aggregate-audit"
    assert audit["status"] == "COMPLETE / READ-ONLY / VERIFIED / OPERATOR DASHBOARD AGGREGATE AUDIT"
    assert summary["aggregate_audit_ready"] is True
    assert summary["dashboard_response_ready"] is True
    assert summary["source_cards_covered"] is True
    assert summary["source_count"] >= len(EXPECTED_SOURCE_IDS)
    assert EXPECTED_SOURCE_IDS.issubset(source_ids)
    assert EXPECTED_CARD_IDS.issubset(card_ids)
    assert summary["selected_next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert NEXT_RECOMMENDED_PASS == "phase11-chat-no-hitl-lane-completion-audit"

    for item in audit["source_audits"]:
        assert item["source_ready"] is True, item["source_id"]
        assert item["read_only"] is True, item["source_id"]
        assert item["writes_performed"] is False, item["source_id"]
        assert item["approval_execution_performed"] is False, item["source_id"]
        assert item["provider_call_performed"] is False, item["source_id"]
        assert item["runtime_dispatch_performed"] is False, item["source_id"]
        assert item["browser_action_performed"] is False, item["source_id"]
        assert item["agent_bus_task_written"] is False, item["source_id"]
        assert item["canonical_mutation_performed"] is False, item["source_id"]


def test_dashboard_aggregate_audit_cross_checks_source_summaries(tmp_path: Path) -> None:
    _seed_vault(tmp_path)

    audit = build_phase11_readonly_operator_dashboard_aggregate_audit(tmp_path)
    by_id = {item["source_id"]: item for item in audit["source_audits"]}

    assert by_id["approval_center"]["summary_fields"]["source_group_count"] >= 1
    assert by_id["provider_readiness"]["summary_fields"]["readiness_status"] in {
        "blocked",
        "ready_for_cli_guarded_live_probe",
        "verified_by_last_probe_result",
    }
    assert by_id["runtime_status"]["summary_fields"]["no_dispatch_performed"] is True
    assert by_id["companion_status"]["summary_fields"]["registered_companion_count"] >= 3
    assert by_id["recent_build_logs"]["summary_fields"]["log_count"] >= 1
    assert by_id["slash_catalog"]["summary_fields"]["supported_readonly_command_count"] >= 9
    assert audit["readiness"]["approval_provider_runtime_companion_log_sources_covered"] is True
    assert audit["readiness"]["slash_catalog_consumed"] is True


def test_dashboard_aggregate_audit_authority_is_bounded_and_formatted(tmp_path: Path) -> None:
    _seed_vault(tmp_path)

    audit = build_phase11_readonly_operator_dashboard_aggregate_audit(tmp_path)
    authority = audit["authority"]
    text = format_phase11_readonly_operator_dashboard_aggregate_audit(audit)

    assert authority["read_only"] is True
    assert authority["dashboard_aggregate_audit_only"] is True
    assert authority["command_execution_allowed"] is False
    assert authority["approval_queue_write_allowed"] is False
    assert authority["approval_consumption_allowed"] is False
    assert authority["approval_execution_allowed"] is False
    assert authority["provider_calls_allowed"] is False
    assert authority["runtime_dispatch_allowed"] is False
    assert authority["browser_control_allowed"] is False
    assert authority["target_mutation_allowed"] is False
    assert authority["vault_writes_allowed"] is False
    assert authority["agent_bus_task_write_allowed"] is False
    assert authority["canonical_mutation_allowed"] is False
    assert "Boundary: dashboard aggregate audit only" in text


def test_dashboard_aggregate_audit_writes_bounded_json_and_markdown_evidence(tmp_path: Path) -> None:
    _seed_vault(tmp_path)

    audit = build_phase11_readonly_operator_dashboard_aggregate_audit(
        tmp_path,
        write_evidence=True,
        evidence_slug="test-phase11-readonly-operator-dashboard-aggregate-audit",
    )
    evidence = audit["evidence"]

    assert evidence["written"] is True
    assert evidence["json_path"].endswith("test-phase11-readonly-operator-dashboard-aggregate-audit.json")
    assert evidence["markdown_path"].endswith("test-phase11-readonly-operator-dashboard-aggregate-audit.md")
    json_path = tmp_path / evidence["json_path"]
    markdown_path = tmp_path / evidence["markdown_path"]
    assert json_path.is_file()
    assert markdown_path.is_file()
    written = json.loads(json_path.read_text(encoding="utf-8"))
    assert written["surface"] == "phase11_readonly_operator_dashboard_aggregate_audit"
    assert "Phase 11 Read-Only Operator Dashboard Aggregate Audit" in markdown_path.read_text(encoding="utf-8")
