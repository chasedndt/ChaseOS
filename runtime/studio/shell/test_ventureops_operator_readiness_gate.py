"""Tests for ventureops-operator-readiness-gate pass."""
from __future__ import annotations

from pathlib import Path

import pytest

from runtime.studio.ventureops_operator_readiness_gate import (
    NEXT_RECOMMENDED_PASS,
    PASS_ID,
    build_ventureops_operator_readiness_gate,
)
from runtime.studio.shell.api import StudioAPI
from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

VAULT_ROOT = Path(__file__).resolve().parents[3]


# ── Module constants ──────────────────────────────────────────────────────────

def test_pass_id():
    assert PASS_ID == "ventureops-operator-readiness-gate"


def test_next_recommended_pass_loops_to_self():
    assert NEXT_RECOMMENDED_PASS == "ventureops-operator-readiness-gate"


# ── Build output structure ────────────────────────────────────────────────────

class TestBuildVentureopsOperatorReadinessGate:

    @pytest.fixture(scope="class")
    def result(self):
        return build_ventureops_operator_readiness_gate(VAULT_ROOT)

    def test_ok_always_true(self, result):
        assert result["ok"] is True

    def test_pass_id_correct(self, result):
        assert result["pass"] == "ventureops-operator-readiness-gate"

    def test_surface_correct(self, result):
        assert result["surface"] == "ventureops_operator_readiness_gate"

    def test_next_recommended_pass_terminal(self, result):
        assert result["next_recommended_pass"] == "ventureops-operator-readiness-gate"

    def test_model_version_present(self, result):
        assert result.get("model_version", "").startswith("studio.ventureops_operator_readiness_gate")

    def test_generated_at_present(self, result):
        assert result.get("generated_at")

    def test_status_string_present(self, result):
        assert isinstance(result.get("status"), str)
        assert len(result["status"]) > 0

    def test_check_results_keys_present(self, result):
        checks = result.get("check_results") or {}
        assert "local_implementation_complete" in checks
        assert "studio_surface_accessible" in checks
        assert "real_world_gate_preserved" in checks
        assert "external_effects_clear" in checks

    def test_check_results_all_bool(self, result):
        for val in (result.get("check_results") or {}).values():
            assert isinstance(val, bool)

    def test_failing_checks_list(self, result):
        assert isinstance(result.get("failing_checks"), list)

    def test_summary_block_present(self, result):
        summary = result.get("summary") or {}
        assert "feature_implementation_complete" in summary
        assert "studio_surface_ok" in summary
        assert "real_world_gate_preserved" in summary

    def test_real_world_missing_list(self, result):
        assert isinstance(result.get("real_world_missing_requirements"), list)

    def test_operator_notes_list(self, result):
        assert isinstance(result.get("operator_notes"), list)

    def test_authority_block_all_false(self, result):
        authority = result.get("authority") or {}
        # read_only should be True; all others False
        assert authority.get("read_only") is True
        assert authority.get("builds_triggered") is False
        assert authority.get("external_calls_made") is False
        assert authority.get("vault_mutations") is False
        assert authority.get("evidence_packets_created") is False
        assert authority.get("revenue_claim_made") is False

    def test_warnings_list(self, result):
        assert isinstance(result.get("warnings"), list)

    def test_vault_root_in_output(self, result):
        assert str(VAULT_ROOT) in result.get("vault_root", "")

    def test_operator_ready_bool(self, result):
        assert isinstance(result.get("operator_ready"), bool)

    def test_real_world_complete_bool(self, result):
        assert isinstance(result.get("real_world_complete"), bool)


# ── Local implementation should be complete ───────────────────────────────────

class TestVentureopsGateExpectedState:

    @pytest.fixture(scope="class")
    def result(self):
        return build_ventureops_operator_readiness_gate(VAULT_ROOT)

    def test_local_implementation_complete(self, result):
        """feature_implementation_complete should be True on this vault."""
        assert result["check_results"]["local_implementation_complete"] is True

    def test_real_world_gate_preserved(self, result):
        """real_world_delivery_revenue_complete should still be False."""
        assert result["check_results"]["real_world_gate_preserved"] is True
        assert result.get("real_world_complete") is False

    def test_external_effects_clear(self, result):
        assert result["check_results"]["external_effects_clear"] is True

    def test_operator_ready_true(self, result):
        """On this vault with full implementation, operator_ready should be True."""
        assert result.get("operator_ready") is True

    def test_status_contains_operator_ready(self, result):
        assert "OPERATOR_READY" in result.get("status", "") or "REAL_WORLD_COMPLETE" in result.get("status", "")


# ── API envelope ─────────────────────────────────────────────────────────────

class TestApiEnvelope:

    @pytest.fixture(scope="class")
    def api(self):
        return StudioAPI(VAULT_ROOT)

    def test_api_ok(self, api):
        resp = api.get_ventureops_operator_readiness_gate()
        assert resp.get("ok") is True

    def test_api_surface(self, api):
        resp = api.get_ventureops_operator_readiness_gate()
        assert resp.get("surface") == "get_ventureops_operator_readiness_gate"

    def test_api_data_has_pass(self, api):
        resp = api.get_ventureops_operator_readiness_gate()
        assert (resp.get("data") or {}).get("pass") == "ventureops-operator-readiness-gate"

    def test_api_data_authority_read_only(self, api):
        resp = api.get_ventureops_operator_readiness_gate()
        authority = (resp.get("data") or {}).get("authority") or {}
        assert authority.get("read_only") is True


# ── Panel registry ────────────────────────────────────────────────────────────

class TestPanelRegistryFlags:

    @pytest.fixture(scope="class")
    def registry(self):
        return build_native_shell_panel_registry(VAULT_ROOT)

    def test_flag_mounted(self, registry):
        assert registry["readiness"].get("ventureops_operator_readiness_gate_mounted") is True

    def test_next_recommended_pass_advanced(self, registry):
        assert registry["readiness"]["next_recommended_pass"] == "ventureops-operator-readiness-gate"


# ── CLI importable ────────────────────────────────────────────────────────────

def test_cli_command_importable():
    from runtime.cli.main import cmd_studio_ventureops_operator_readiness_gate  # noqa: F401
    assert callable(cmd_studio_ventureops_operator_readiness_gate)
