from __future__ import annotations

from pathlib import Path

from runtime.chaser import terminal_authority_audit as audit


def test_terminal_authority_audit_passes_without_runtime_side_effects(tmp_path: Path) -> None:
    result = audit.build_terminal_authority_audit(tmp_path)

    assert result["ok"] is True
    assert result["surface"] == "chaser_terminal_authority_audit"
    assert result["summary"]["checks_failed"] == 0
    assert result["authority"]["studio_execution_now"] is False
    assert result["authority"]["terminal_execution_now"] is False
    assert result["authority"]["approval_queue_write_now"] is False
    assert result["authority"]["approval_consumption_now"] is False
    assert result["authority"]["agent_bus_write_now"] is False
    assert result["authority"]["provider_call_now"] is False
    assert result["authority"]["canonical_writeback_now"] is False
    assert result["side_effects"]["approval_files_unchanged"] is True
    assert result["side_effects"]["marker_files_unchanged"] is True
    assert result["side_effects"]["terminal_run_files_unchanged"] is True
    assert result["side_effects"]["terminal_session_files_unchanged"] is True
    assert result["side_effects"]["agent_bus_files_unchanged"] is True
    assert result["side_effects"]["probe_target_not_created"] is True
    assert not (tmp_path / result["probe"]["target_path"]).exists()
    assert not (tmp_path / "runtime" / "studio" / "approvals").exists()
    assert not (tmp_path / "runtime" / "agent_bus").exists()
    assert not (tmp_path / "07_LOGS" / "Terminal-Runs").exists()
    assert not (tmp_path / "07_LOGS" / "Terminal-Sessions").exists()


def test_terminal_authority_audit_fails_closed_when_gateway_claims_authority(
    tmp_path: Path,
    monkeypatch,
) -> None:
    def bad_gateway_contract(root: Path) -> dict:
        return {
            "ok": True,
            "surface": "chaser_gateway_ingress",
            "supported_intents": [
                {"intent": "terminal.propose"},
                {"intent": "terminal.approval_request_preview"},
                {"intent": "terminal.approval_request_write"},
                {"intent": "terminal.executor_readiness"},
                {"intent": "terminal.execute_approval"},
            ],
            "authority": {
                "studio_execution_now": True,
                "terminal_execution_now": False,
                "approval_consumption_now": False,
                "approval_queue_write_now": False,
                "agent_bus_write_now": False,
                "provider_call_now": False,
                "canonical_writeback_now": False,
                "host_mutation_now": False,
            },
        }

    monkeypatch.setattr(audit, "build_gateway_ingress_contract", bad_gateway_contract)

    result = audit.build_terminal_authority_audit(tmp_path)

    assert result["ok"] is False
    assert "gateway_contract_preserves_terminal_gates" in result["summary"]["failed_checks"]
    assert not (tmp_path / result["probe"]["target_path"]).exists()
