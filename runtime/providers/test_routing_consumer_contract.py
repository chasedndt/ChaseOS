"""Tests for the Phase 11 provider routing consumer contract."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.providers.routing_consumer_contract import build_provider_routing_consumer_contract


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_routing_consumer_blocks_without_readiness_evidence(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    contract = build_provider_routing_consumer_contract(tmp_path, phase11_intent="model-chat")

    assert contract["ok"] is True
    assert contract["read_only"] is True
    assert contract["routing_status"] == "blocked"
    assert contract["route_execution_allowed"] is False
    assert "provider_readiness_not_verified" in contract["blocked_reasons"]
    assert "primary_provider_credential_or_environment_missing" in contract["blocked_reasons"]
    assert contract["consumer_contract"]["must_fail_closed_when_blocked"] is True
    assert contract["authority"]["provider_calls_allowed"] is False
    assert contract["authority"]["provider_switch_allowed"] is False
    assert contract["authority"]["credential_values_visible"] is False
    assert not (tmp_path / "runtime/providers/state/provider_audit.jsonl").exists()


def test_routing_consumer_allows_contract_preview_with_non_secret_fixture(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-secret-not-returned")
    _write_json(
        tmp_path / "runtime/providers/provider_target_profile.json",
        {
            "default_primary_model": "gpt-5.5",
            "runtime_targets": {"phase11-chat": {"primary_model": "gpt-5.5"}},
            "local_fallback": {"provider_id": "local_oss", "model": "phi4-mini:latest", "enabled": False},
        },
    )
    _write_json(
        tmp_path / "07_LOGS/Agent-Activity/_rpgl_provider_approvals/fixture.json",
        {"gate_approval_id": "fixture-approval", "status": "approved"},
    )
    _write_json(
        tmp_path / "07_LOGS/Agent-Activity/_rpgl_provider_live_probe_decisions/fixture.json",
        {"gate_approval_id": "fixture-approval", "decision": "approved"},
    )
    _write_json(
        tmp_path / "07_LOGS/Agent-Activity/_rpgl_provider_live_probe_consumers/fixture.json",
        {"gate_approval_id": "fixture-approval", "consumer_status": "written"},
    )
    _write_json(
        tmp_path / "runtime/providers/state/provider_live_probe_markers/fixture.json",
        {"gate_approval_id": "fixture-approval", "target": "primary", "marker_status": "reserved"},
    )
    _write_json(
        tmp_path / "runtime/providers/state/provider_live_probe_results/fixture.json",
        {
            "gate_approval_id": "fixture-approval",
            "target": "primary",
            "result_status": "probe_succeeded",
            "probe_outcome": {
                "ok": True,
                "live_network_call_attempted": True,
                "secret_value_read": False,
            },
        },
    )

    contract = build_provider_routing_consumer_contract(tmp_path, phase11_intent="model-chat")
    encoded = json.dumps(contract)

    assert contract["routing_status"] == "route_contract_satisfied"
    assert contract["route_execution_allowed"] is False
    assert contract["selected_candidate_preview"]["provider_id"] == "openai"
    assert contract["selected_candidate_preview"]["model"] == "gpt-5.5"
    assert contract["consumer_contract"]["may_execute_provider_call"] is False
    assert contract["consumer_contract"]["must_attribute_model_outputs"] is True
    assert "fixture-secret-not-returned" not in encoded


def test_routing_consumer_blocks_requested_provider_drift(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-secret-not-returned")
    _write_json(
        tmp_path / "runtime/providers/provider_target_profile.json",
        {"default_primary_model": "gpt-5.5"},
    )
    _write_json(
        tmp_path / "runtime/providers/state/provider_live_probe_results/fixture.json",
        {"target": "primary", "result_status": "probe_succeeded", "probe_outcome": {"ok": True}},
    )

    contract = build_provider_routing_consumer_contract(
        tmp_path,
        phase11_intent="model-chat",
        requested_provider_id="anthropic",
    )

    assert contract["routing_status"] == "blocked"
    assert "requested_provider_does_not_match_active_profile" in contract["blocked_reasons"]
