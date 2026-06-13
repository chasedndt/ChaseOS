from __future__ import annotations

import json
from pathlib import Path

import runtime.cli.main as cli
from runtime.ventureops.mission_external_client_evidence_gate import (
    ACTION_LIVE_CLIENT_WORKFLOW_PROOF,
    build_mission_external_client_evidence_gate,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _dry_run_workspace() -> Path:
    return (
        _repo_root()
        / "07_LOGS"
        / "VentureOps-Missions"
        / "2026-05-13_mission-chase-ai-runtime-governance-kit-dry-run"
    )


def _internal_scope_packet() -> Path:
    return (
        _repo_root()
        / "07_LOGS"
        / "Workflow-Proofs"
        / "2026-05-13_chaseos-internal-runtime-security-audit_scope-evidence.json"
    )


def test_mission_external_client_evidence_gate_blocks_without_operator_evidence() -> None:
    result = build_mission_external_client_evidence_gate(
        _repo_root(),
        mission_workspace=_dry_run_workspace(),
    )

    assert result["ok"] is True
    assert result["status"] == "blocked_missing_external_client_evidence"
    assert result["mission_active_local"] is True
    assert "external_action_type_missing" in result["blockers"]
    assert "operator_approval_statement_missing" in result["blockers"]
    assert result["ready_for_external_send"] is False
    assert result["authority_boundary"]["external_send_performed"] is False
    assert result["authority_boundary"]["credential_or_secret_read_performed"] is False


def test_mission_external_client_evidence_gate_rejects_escaped_scope_packet() -> None:
    result = build_mission_external_client_evidence_gate(
        _repo_root(),
        mission_workspace=_dry_run_workspace(),
        external_action_type=ACTION_LIVE_CLIENT_WORKFLOW_PROOF,
        operator_approval_statement="Approve only the guarded local workflow proof readiness check.",
        scope_packet_path="../outside-scope-packet.json",
    )

    assert result["ok"] is True
    assert result["status"] == "blocked_missing_external_client_evidence"
    assert "scope_packet_path_escapes_vault_root:../outside-scope-packet.json" in result["blockers"]
    assert "real_client_scope_evidence_packet_missing" in result["blockers"]
    assert result["ready_for_guarded_live_client_workflow_proof"] is False
    assert result["ready_for_provider_or_browser_action"] is False


def test_mission_external_client_evidence_gate_can_clear_guarded_local_scope_proof_readiness() -> None:
    result = build_mission_external_client_evidence_gate(
        _repo_root(),
        mission_workspace=_dry_run_workspace(),
        external_action_type=ACTION_LIVE_CLIENT_WORKFLOW_PROOF,
        operator_approval_statement="Approve only the guarded local client workflow proof review path.",
        scope_packet_path=_internal_scope_packet(),
    )

    assert result["ok"] is True
    assert result["status"] == "ready_for_guarded_live_client_workflow_proof"
    assert result["blockers"] == []
    assert result["scope_evidence_valid"] is True
    assert result["scope_approval_artifact_valid"] is True
    assert result["scope_sources_valid"] is True
    assert result["ready_for_guarded_live_client_workflow_proof"] is True
    assert result["ready_for_external_send"] is False
    assert result["authority_boundary"]["crm_or_payment_mutation_performed"] is False


def test_mission_external_client_evidence_gate_cli_json_is_read_only(capsys) -> None:
    exit_code = cli.main(
        [
            "ventureops",
            "mission-external-client-evidence-gate",
            "--mission-workspace",
            str(_dry_run_workspace()),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "ventureops.mission-external-client-evidence-gate"
    assert result["status"] == "blocked_missing_external_client_evidence"
    assert result["report_written"] is False
    assert result["authority_boundary"]["external_send_performed"] is False
    assert result["authority_boundary"]["protected_file_edit_performed"] is False


def test_mission_external_client_evidence_gate_schema_declares_fail_closed_boundaries() -> None:
    schema = (
        _repo_root()
        / "runtime"
        / "ventureops"
        / "templates"
        / "mission_external_client_evidence_gate_schema.yaml"
    ).read_text(encoding="utf-8")

    assert "blocked_missing_external_client_evidence" in schema
    assert "operator_approval_statement_present" in schema
    assert "ready_for_external_send" in schema
    assert "credential reads" in schema
