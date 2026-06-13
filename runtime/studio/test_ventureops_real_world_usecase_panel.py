"""Tests for the Studio VentureOps real-world use case panel."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio import ventureops_real_world_usecase_panel as panel_module


def _fake_completion() -> dict:
    return {
        "ok": True,
        "feature_implementation_complete": True,
        "operator_evidence_required_for_tests": False,
        "real_world_delivery_revenue_complete": False,
        "safe_to_mark_real_world_delivery_revenue_complete": False,
        "real_world_missing_requirements": [
            "operator delivery attestation missing",
            "redacted receipt/payment artifact missing",
        ],
        "truth_boundary": {
            "external_send_performed": False,
            "provider_call_performed": False,
            "browser_action_performed": False,
            "crm_mutation_performed": False,
            "payment_mutation_performed": False,
            "invoice_sent": False,
            "revenue_claim_made": False,
            "accounting_claim_made": False,
            "credential_or_secret_read_performed": False,
            "canonical_promotion_performed": False,
        },
        "local_evidence_chain": {
            "scope_evidence": {"ok": True},
            "live_client_workflow_proof": {"ok": True},
            "client_safe_delivery_artifact": {"ok": True},
        },
    }


def test_ventureops_real_world_usecase_panel_separates_local_completion_from_revenue(
    tmp_path: Path,
    monkeypatch,
) -> None:
    guide_path = tmp_path / panel_module.GUIDE_PATH
    guide_path.parent.mkdir(parents=True, exist_ok=True)
    guide_path.write_text("# guide\n", encoding="utf-8")
    monkeypatch.setattr(
        panel_module,
        "build_autonomous_implementation_completion",
        lambda vault_root: _fake_completion(),
    )

    panel = panel_module.build_ventureops_real_world_usecase_panel(tmp_path)

    assert panel["surface"] == "studio_ventureops_real_world_usecase_panel"
    assert panel["status"] == "studio_ready_real_world_evidence_blocked"
    assert panel["summary"]["feature_implementation_complete"] is True
    assert panel["summary"]["operator_evidence_required_for_tests"] is False
    assert panel["summary"]["real_world_delivery_revenue_complete"] is False
    assert panel["summary"]["safe_to_mark_real_world_delivery_revenue_complete"] is False
    assert panel["summary"]["guide_exists"] is True
    assert panel["operator_guide"]["path"] == panel_module.GUIDE_PATH
    assert panel["real_world_test_usecase"]["id"] == "ai-runtime-governance-audit-client-service"
    assert "python -m runtime.cli.main studio dashboard-app --host 127.0.0.1 --port 8768 --dry-run --json" in panel["safe_commands"]
    checks = {item["id"]: item for item in panel["hardening_checks"]}
    assert checks["local_implementation_complete"]["ok"] is True
    assert checks["operator_evidence_not_required_for_local_tests"]["ok"] is True
    assert checks["real_world_gate_preserved"]["ok"] is True
    assert checks["external_effects_false"]["ok"] is True
    assert panel["authority"]["external_send_allowed"] is False
    assert panel["authority"]["provider_calls_allowed"] is False
    assert panel["authority"]["payment_mutation_allowed"] is False
    assert panel["authority"]["revenue_claim_allowed"] is False
    assert "operator delivery attestation missing" in json.dumps(panel)


def test_ventureops_real_world_usecase_panel_blocks_if_revenue_gate_is_weakened(
    tmp_path: Path,
    monkeypatch,
) -> None:
    payload = _fake_completion()
    payload["real_world_missing_requirements"] = []
    monkeypatch.setattr(
        panel_module,
        "build_autonomous_implementation_completion",
        lambda vault_root: payload,
    )

    panel = panel_module.build_ventureops_real_world_usecase_panel(tmp_path)
    checks = {item["id"]: item for item in panel["hardening_checks"]}

    assert panel["status"] == "implementation_incomplete"
    assert checks["real_world_gate_preserved"]["ok"] is False
    assert panel["summary"]["safe_to_mark_real_world_delivery_revenue_complete"] is False
