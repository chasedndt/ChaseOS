"""Tests for the approved Phase 11 Chat live-provider execution contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.studio.phase11_chat_live_provider_execution_contract import (
    build_phase11_chat_live_provider_execution_contract,
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _seed_verified_provider(root: Path) -> None:
    _write_json(
        root / "runtime/providers/provider_target_profile.json",
        {
            "default_primary_model": "gpt-5.5",
            "local_fallback": {"provider_id": "local_oss", "model": "phi4-mini:latest", "enabled": False},
        },
    )
    _write_json(
        root / "07_LOGS/Agent-Activity/_rpgl_provider_approvals/fixture.json",
        {"gate_approval_id": "fixture-approval", "status": "approved"},
    )
    _write_json(
        root / "07_LOGS/Agent-Activity/_rpgl_provider_live_probe_decisions/fixture.json",
        {"gate_approval_id": "fixture-approval", "decision": "approved"},
    )
    _write_json(
        root / "07_LOGS/Agent-Activity/_rpgl_provider_live_probe_consumers/fixture.json",
        {"gate_approval_id": "fixture-approval", "consumer_status": "written"},
    )
    _write_json(
        root / "runtime/providers/state/provider_live_probe_markers/fixture.json",
        {"gate_approval_id": "fixture-approval", "target": "primary", "marker_status": "reserved"},
    )
    _write_json(
        root / "runtime/providers/state/provider_live_probe_results/fixture.json",
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


def _approve(root: Path, approval_id: str) -> None:
    path = root / "runtime/studio/approvals/chat-provider-executions" / f"{approval_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["status"] = "approved"
    payload["reviewed_by"] = "operator-fixture"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_preview_and_approval_packet_are_digest_bound_without_provider_call(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-secret-not-returned")
    _seed_verified_provider(tmp_path)

    preview = build_phase11_chat_live_provider_execution_contract(
        tmp_path,
        message="Summarize the current ChaseOS provider status",
        explicit_intent="model-chat",
    )
    digest = preview["request_digest_proof"]["request_digest"]
    written = build_phase11_chat_live_provider_execution_contract(
        tmp_path,
        message="Summarize the current ChaseOS provider status",
        explicit_intent="model-chat",
        expected_request_digest=digest,
        write_approval=True,
    )
    encoded = json.dumps(written)

    assert preview["summary"]["approval_packet_ready"] is True
    assert preview["summary"]["provider_call_performed"] is False
    assert written["summary"]["approval_request_created"] is True
    assert written["approval_packet"]["status"] == "pending"
    assert written["approval_packet"]["provider_id"] == "openai"
    assert written["approval_packet"]["credential_env_ref"] == "OPENAI_API_KEY"
    assert written["approval_packet"]["secret_reference_metadata_only"] is True
    assert "fixture-secret-not-returned" not in encoded
    assert not (tmp_path / "07_LOGS/Conversations").exists()


def test_execute_requires_approved_packet_and_missing_approval_fails_closed(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-secret-not-returned")
    _seed_verified_provider(tmp_path)

    result = build_phase11_chat_live_provider_execution_contract(
        tmp_path,
        message="Summarize status",
        explicit_intent="model-chat",
        approval_id="missing-approval",
        execute=True,
        provider_runner=lambda request: {"text": "should not run"},
    )

    assert result["ok"] is False
    assert "approval_packet_missing" in result["blocked_reasons"]
    assert result["summary"]["provider_call_performed"] is False
    assert result["summary"]["conversation_log_written"] is False
    assert not (tmp_path / "07_LOGS/Conversations").exists()


def test_approved_execution_uses_credential_ref_only_persists_conversation_and_agent_activity(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-secret-not-returned")
    _seed_verified_provider(tmp_path)
    message = "Summarize provider status without secrets"
    preview = build_phase11_chat_live_provider_execution_contract(tmp_path, message=message, explicit_intent="model-chat")
    digest = preview["request_digest_proof"]["request_digest"]
    written = build_phase11_chat_live_provider_execution_contract(
        tmp_path,
        message=message,
        explicit_intent="model-chat",
        expected_request_digest=digest,
        write_approval=True,
    )
    approval_id = written["approval_packet"]["approval_id"]
    _approve(tmp_path, approval_id)
    seen_request: dict[str, Any] = {}

    def runner(request: dict[str, Any]) -> dict[str, str]:
        seen_request.update(request)
        return {"text": "Provider status is verified and ready."}

    executed = build_phase11_chat_live_provider_execution_contract(
        tmp_path,
        message=message,
        explicit_intent="model-chat",
        approval_id=approval_id,
        expected_request_digest=digest,
        execute=True,
        provider_runner=runner,
    )
    encoded = json.dumps(executed)

    assert executed["ok"] is True
    assert executed["summary"]["provider_call_performed"] is True
    assert executed["summary"]["conversation_log_written"] is True
    assert executed["summary"]["agent_activity_audit_written"] is True
    assert seen_request["credential_env_ref"] == "OPENAI_API_KEY"
    assert "credential_value" not in seen_request
    assert seen_request["max_output_chars"] <= 2000
    assert Path(tmp_path / executed["conversation_audit"]["conversation_path"]).exists()
    assert Path(tmp_path / executed["agent_activity_audit"]["audit_path"]).exists()
    assert "fixture-secret-not-returned" not in encoded
    assert "fixture-secret-not-returned" not in Path(tmp_path / executed["conversation_audit"]["conversation_path"]).read_text(encoding="utf-8")


def test_missing_credential_and_requested_provider_mismatch_fail_before_call(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    _seed_verified_provider(tmp_path)

    result = build_phase11_chat_live_provider_execution_contract(
        tmp_path,
        message="Summarize status",
        explicit_intent="model-chat",
        requested_provider_id="anthropic",
        execute=True,
        provider_runner=lambda request: {"text": "should not run"},
    )

    assert result["ok"] is False
    assert "provider_route_contract_not_satisfied" in result["blocked_reasons"]
    assert "primary_provider_credential_or_environment_missing" in result["blocked_reasons"]
    assert result["summary"]["provider_call_performed"] is False


def test_secret_like_operator_prompt_is_blocked_before_approval_write_or_provider_call(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-secret-not-returned")
    _seed_verified_provider(tmp_path)
    message = "Please explain this key test-key-livepromptsecret12345 without leaking it."

    preview = build_phase11_chat_live_provider_execution_contract(
        tmp_path,
        message=message,
        explicit_intent="model-chat",
    )
    digest = preview["request_digest_proof"]["request_digest"]
    blocked_write = build_phase11_chat_live_provider_execution_contract(
        tmp_path,
        message=message,
        explicit_intent="model-chat",
        expected_request_digest=digest,
        write_approval=True,
    )
    called = False

    def runner(request: dict[str, Any]) -> dict[str, str]:
        nonlocal called
        called = True
        return {"text": "should not run"}

    blocked_execute = build_phase11_chat_live_provider_execution_contract(
        tmp_path,
        message=message,
        explicit_intent="model-chat",
        approval_id="missing-because-secret-prompt",
        expected_request_digest=digest,
        execute=True,
        provider_runner=runner,
    )
    encoded = json.dumps({"preview": preview, "write": blocked_write, "execute": blocked_execute})

    assert preview["ok"] is False
    assert preview["summary"]["approval_packet_ready"] is False
    assert preview["summary"]["operator_prompt_secret_like_detected"] is True
    assert "operator_prompt_failed_secret_exposure_scan" in preview["blocked_reasons"]
    assert blocked_write["ok"] is False
    assert blocked_write["summary"]["approval_request_created"] is False
    assert blocked_execute["ok"] is False
    assert blocked_execute["summary"]["provider_call_performed"] is False
    assert blocked_execute["conversation_audit"]["secret_values_persisted"] is False
    assert called is False
    assert "test-key-livepromptsecret12345" not in encoded
    assert not (tmp_path / "runtime/studio/approvals/chat-provider-executions").exists()
    assert not (tmp_path / "07_LOGS/Conversations").exists()


def test_secret_like_provider_output_is_blocked_and_not_persisted(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-secret-not-returned")
    _seed_verified_provider(tmp_path)
    message = "Try to produce a secret-looking response"
    preview = build_phase11_chat_live_provider_execution_contract(tmp_path, message=message, explicit_intent="model-chat")
    digest = preview["request_digest_proof"]["request_digest"]
    written = build_phase11_chat_live_provider_execution_contract(
        tmp_path,
        message=message,
        explicit_intent="model-chat",
        expected_request_digest=digest,
        write_approval=True,
    )
    approval_id = written["approval_packet"]["approval_id"]
    _approve(tmp_path, approval_id)

    blocked = build_phase11_chat_live_provider_execution_contract(
        tmp_path,
        message=message,
        explicit_intent="model-chat",
        approval_id=approval_id,
        expected_request_digest=digest,
        execute=True,
        provider_runner=lambda request: {"text": "leak fixture-secret-not-returned"},
    )
    encoded = json.dumps(blocked)

    assert blocked["ok"] is False
    assert "provider_output_failed_secret_exposure_scan" in blocked["blocked_reasons"]
    assert blocked["summary"]["provider_call_performed"] is True
    assert blocked["summary"]["conversation_log_written"] is False
    assert "fixture-secret-not-returned" not in encoded
    assert not (tmp_path / "07_LOGS/Conversations").exists()
