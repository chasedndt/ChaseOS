"""
runtime/tests/test_l2_actor_validation.py

Tests for L-2: approval_decision_actor / external_send_approval_actor validated
against runtime/memory/adapters/*/identity-ledger.json in
agent_runtime_governance_audit.py.  Fail closed if actor not registered.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.workflows.agent_runtime_governance_audit import (  # noqa: E402
    WorkflowExecutionError,
    _load_registered_actors,
    _validate_actor,
    build_agent_runtime_governance_audit,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ledger_dir(tmp_path: Path, runtimes: list[str]) -> Path:
    """Create identity-ledger.json files for the given runtime IDs."""
    adapters = tmp_path / "runtime" / "memory" / "adapters"
    for rt in runtimes:
        d = adapters / rt
        d.mkdir(parents=True, exist_ok=True)
        (d / "identity-ledger.json").write_text(
            json.dumps({"schema_version": "1.0", "runtime_id": rt}),
            encoding="utf-8",
        )
    return tmp_path


def _minimal_vault(tmp_path: Path) -> Path:
    """Create a minimal vault with the required source files."""
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "CLAUDE.md").write_text("# stub", encoding="utf-8")
    agents = vault / "06_AGENTS"
    agents.mkdir()
    (agents / "Agent-Control-Plane.md").write_text("# Agent Control Plane\nApproval required.\n", encoding="utf-8")
    (agents / "Permission-Matrix.md").write_text("# Permission Matrix\nSecret path: blocked.\n", encoding="utf-8")
    (agents / "Trust-Tiers.md").write_text("# Trust Tiers\nProvider: bounded.\n", encoding="utf-8")
    (agents / "Backends-Supported.md").write_text("# Backends\nBrowser: bounded.\n", encoding="utf-8")
    codex = vault / "runtime" / "codex"
    codex.mkdir(parents=True)
    (codex / "capabilities.yaml").write_text("version: '1.0'\n", encoding="utf-8")
    reg = vault / "runtime" / "workflows" / "registry"
    reg.mkdir(parents=True)
    (reg / "use_case_registry.yaml").write_text("use_cases: []\n", encoding="utf-8")
    return vault


def _approval_inputs(actor: str = "operator") -> dict:
    """Minimal inputs to trigger include_approval_consumption_proof path."""
    return {
        "include_offer_packet": True,
        "include_delivery_approval_contract": True,
        "include_delivery_packet_preview": True,
        "include_approval_request_artifact": True,
        "include_approval_consumption_proof": True,
        "approval_request_run_id": "2026-05-11-internal-run",
        "run_id": "2026-05-11-internal-run",
        "approval_decision_id": "appr-001",
        "approval_decision": "approved",
        "approval_decision_actor": actor,
    }


def _approved_send_inputs(actor: str = "operator") -> dict:
    """Minimal inputs to trigger include_approved_external_send_proof path."""
    base = _approval_inputs()
    base.update({
        "include_exact_once_delivery_gate": True,
        "include_external_send_dry_run": True,
        "include_approved_external_send_proof": True,
        "external_delivery_channel": "email",
        "external_recipient_route": "test@example.com",
        "external_send_approval_id": "esap-001",
        "external_send_approval_decision": "approved",
        "external_send_approval_actor": actor,
    })
    return base


# ---------------------------------------------------------------------------
# 1 — _load_registered_actors
# ---------------------------------------------------------------------------

class TestLoadRegisteredActors:
    def test_operator_always_present_no_ledger_dir(self, tmp_path):
        result = _load_registered_actors(tmp_path)
        assert "operator" in result

    def test_returns_frozenset(self, tmp_path):
        result = _load_registered_actors(tmp_path)
        assert isinstance(result, frozenset)

    def test_loads_single_runtime_id(self, tmp_path):
        _make_ledger_dir(tmp_path, ["hermes"])
        result = _load_registered_actors(tmp_path)
        assert "hermes" in result
        assert "operator" in result

    def test_loads_multiple_runtime_ids(self, tmp_path):
        _make_ledger_dir(tmp_path, ["hermes", "openclaw", "archon"])
        result = _load_registered_actors(tmp_path)
        assert {"operator", "hermes", "openclaw", "archon"}.issubset(result)

    def test_skips_malformed_ledger(self, tmp_path):
        adapters = tmp_path / "runtime" / "memory" / "adapters"
        bad = adapters / "broken"
        bad.mkdir(parents=True)
        (bad / "identity-ledger.json").write_text("not json {{{{", encoding="utf-8")
        result = _load_registered_actors(tmp_path)
        assert "operator" in result
        assert "broken" not in result

    def test_skips_ledger_with_missing_runtime_id(self, tmp_path):
        adapters = tmp_path / "runtime" / "memory" / "adapters"
        noid = adapters / "noid"
        noid.mkdir(parents=True)
        (noid / "identity-ledger.json").write_text(
            json.dumps({"schema_version": "1.0"}), encoding="utf-8"
        )
        result = _load_registered_actors(tmp_path)
        assert "operator" in result
        assert "noid" not in result

    def test_skips_ledger_with_empty_runtime_id(self, tmp_path):
        adapters = tmp_path / "runtime" / "memory" / "adapters"
        empty = adapters / "empty_id"
        empty.mkdir(parents=True)
        (empty / "identity-ledger.json").write_text(
            json.dumps({"runtime_id": "  "}), encoding="utf-8"
        )
        result = _load_registered_actors(tmp_path)
        assert "" not in result
        assert "  " not in result

    def test_real_vault_has_known_runtimes(self):
        result = _load_registered_actors(_VAULT_ROOT)
        assert "operator" in result
        assert "openclaw" in result
        assert "hermes" in result
        assert "archon" in result
        assert "claude" in result


# ---------------------------------------------------------------------------
# 2 — _validate_actor
# ---------------------------------------------------------------------------

class TestValidateActor:
    def test_operator_passes_no_ledgers(self, tmp_path):
        _validate_actor("operator", tmp_path)  # no raise

    def test_registered_runtime_passes(self, tmp_path):
        _make_ledger_dir(tmp_path, ["hermes"])
        _validate_actor("hermes", tmp_path)  # no raise

    def test_unknown_actor_raises(self, tmp_path):
        _make_ledger_dir(tmp_path, ["hermes"])
        with pytest.raises(WorkflowExecutionError, match="not a registered operator or runtime"):
            _validate_actor("unknown-actor", tmp_path)

    def test_error_message_includes_actor_name(self, tmp_path):
        with pytest.raises(WorkflowExecutionError, match="evil-bot"):
            _validate_actor("evil-bot", tmp_path)

    def test_error_message_includes_field_name(self, tmp_path):
        with pytest.raises(WorkflowExecutionError, match="external_send_approval_actor"):
            _validate_actor("bad", tmp_path, field_name="external_send_approval_actor")

    def test_error_message_includes_registered_actors(self, tmp_path):
        _make_ledger_dir(tmp_path, ["hermes"])
        with pytest.raises(WorkflowExecutionError, match="hermes"):
            _validate_actor("nothermes", tmp_path)

    def test_operator_always_valid_even_with_ledgers(self, tmp_path):
        _make_ledger_dir(tmp_path, ["hermes", "openclaw"])
        _validate_actor("operator", tmp_path)  # no raise


# ---------------------------------------------------------------------------
# 3 — build_agent_runtime_governance_audit: approval_decision_actor validation
# ---------------------------------------------------------------------------

class TestApprovalActorInBuild:
    def test_default_operator_actor_passes(self, tmp_path):
        vault = _minimal_vault(tmp_path)
        inputs = _approval_inputs(actor="operator")
        result = build_agent_runtime_governance_audit(inputs=inputs, vault_root=vault)
        assert result["approval_consumption_proof"]["approval_decision_actor"] == "operator"

    def test_registered_actor_passes(self, tmp_path):
        vault = _minimal_vault(tmp_path)
        _make_ledger_dir(vault, ["hermes"])
        inputs = _approval_inputs(actor="hermes")
        result = build_agent_runtime_governance_audit(inputs=inputs, vault_root=vault)
        assert result["approval_consumption_proof"]["approval_decision_actor"] == "hermes"

    def test_unregistered_actor_raises(self, tmp_path):
        vault = _minimal_vault(tmp_path)
        inputs = _approval_inputs(actor="malicious-agent")
        with pytest.raises(WorkflowExecutionError, match="malicious-agent"):
            build_agent_runtime_governance_audit(inputs=inputs, vault_root=vault)

    def test_unregistered_actor_raises_correct_field_name(self, tmp_path):
        vault = _minimal_vault(tmp_path)
        inputs = _approval_inputs(actor="bad")
        with pytest.raises(WorkflowExecutionError, match="approval_decision_actor"):
            build_agent_runtime_governance_audit(inputs=inputs, vault_root=vault)

    def test_actor_not_validated_when_proof_not_included(self, tmp_path):
        vault = _minimal_vault(tmp_path)
        inputs = {
            "approval_decision_actor": "totally-unknown-actor",
            "include_approval_consumption_proof": False,
        }
        result = build_agent_runtime_governance_audit(inputs=inputs, vault_root=vault)
        assert "approval_consumption_proof" not in result or result.get("approval_consumption_proof") == {}


# ---------------------------------------------------------------------------
# 4 — build_agent_runtime_governance_audit: external_send_approval_actor validation
# ---------------------------------------------------------------------------

class TestExternalSendActorInBuild:
    def test_default_operator_actor_passes(self, tmp_path):
        vault = _minimal_vault(tmp_path)
        inputs = _approved_send_inputs(actor="operator")
        result = build_agent_runtime_governance_audit(inputs=inputs, vault_root=vault)
        assert result["approved_external_send_proof"]["external_send_approval_actor"] == "operator"

    def test_registered_actor_passes(self, tmp_path):
        vault = _minimal_vault(tmp_path)
        _make_ledger_dir(vault, ["openclaw"])
        inputs = _approved_send_inputs(actor="openclaw")
        result = build_agent_runtime_governance_audit(inputs=inputs, vault_root=vault)
        assert result["approved_external_send_proof"]["external_send_approval_actor"] == "openclaw"

    def test_unregistered_actor_raises(self, tmp_path):
        vault = _minimal_vault(tmp_path)
        inputs = _approved_send_inputs(actor="unauthorized-runtime")
        with pytest.raises(WorkflowExecutionError, match="unauthorized-runtime"):
            build_agent_runtime_governance_audit(inputs=inputs, vault_root=vault)

    def test_unregistered_actor_raises_correct_field_name(self, tmp_path):
        vault = _minimal_vault(tmp_path)
        inputs = _approved_send_inputs(actor="bad")
        with pytest.raises(WorkflowExecutionError, match="external_send_approval_actor"):
            build_agent_runtime_governance_audit(inputs=inputs, vault_root=vault)

    def test_external_send_actor_not_validated_when_not_included(self, tmp_path):
        vault = _minimal_vault(tmp_path)
        inputs = {
            "external_send_approval_actor": "totally-unknown-actor",
            "include_approved_external_send_proof": False,
        }
        result = build_agent_runtime_governance_audit(inputs=inputs, vault_root=vault)
        assert "approved_external_send_proof" not in result or result.get("approved_external_send_proof") == {}
