"""Tests for the Studio provider readiness model."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.provider_readiness import build_studio_provider_readiness


def test_provider_readiness_blocks_without_credential_or_approval(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    panel = build_studio_provider_readiness(tmp_path)

    assert panel["ok"] is True
    assert panel["read_only"] is True
    assert panel["summary"]["readiness_status"] == "blocked"
    assert panel["summary"]["active_model"] == "gpt-5.5"
    assert panel["credential_posture"]["primary_provider_env_present"] is False
    assert panel["credential_posture"]["secret_values_included"] is False
    assert panel["live_probe_readiness"]["approval_gated"] is True
    assert panel["live_probe_readiness"]["studio_executes_live_probe"] is False
    assert "primary_provider_credential_or_environment_missing" in panel["live_probe_readiness"]["blocked_reasons"]
    assert "live_probe_approval_decision_consumer_marker_chain_incomplete" in panel["live_probe_readiness"]["blocked_reasons"]
    assert panel["authority"]["provider_calls_allowed"] is False
    assert panel["authority"]["provider_switch_allowed"] is False
    assert not (tmp_path / "runtime/providers/state/provider_audit.jsonl").exists()


def test_provider_readiness_uses_non_secret_fixture_evidence(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-secret-not-returned")
    profile_path = tmp_path / "runtime/providers/provider_target_profile.json"
    profile_path.parent.mkdir(parents=True)
    profile_path.write_text(
        json.dumps(
            {
                "default_primary_model": "gpt-5.5",
                "runtime_targets": {"codex": {"primary_model": "gpt-5.5"}},
                "local_fallback": {
                    "provider_id": "local_oss",
                    "model": "phi4-mini:latest",
                    "strength": "weak",
                    "enabled": False,
                    "num_ctx": 16384,
                    "authority": "recovery_assistant_only",
                },
            }
        ),
        encoding="utf-8",
    )
    queue_path = tmp_path / "runtime/providers/state/provider_queue.json"
    queue_path.parent.mkdir(parents=True)
    queue_path.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "task_id": "rpglq-fixture",
                        "task_class": "repo_development",
                        "retry_status": "waiting_for_primary",
                        "required_provider_strength": "strong",
                        "safe_next_step": "Retry after primary provider recovers.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    for directory, payload in [
        (
            tmp_path / "07_LOGS/Agent-Activity/_rpgl_provider_approvals",
            {"gate_approval_id": "fixture-approval", "approval_status": "approved"},
        ),
        (
            tmp_path / "07_LOGS/Agent-Activity/_rpgl_provider_live_probe_decisions",
            {"gate_approval_id": "fixture-approval", "decision": "approved"},
        ),
        (
            tmp_path / "07_LOGS/Agent-Activity/_rpgl_provider_live_probe_consumers",
            {"gate_approval_id": "fixture-approval", "consumer_status": "written"},
        ),
        (
            tmp_path / "runtime/providers/state/provider_live_probe_markers",
            {
                "gate_approval_id": "fixture-approval",
                "target": "primary",
                "marker_status": "reserved",
                "created_at": "2026-05-08T00:00:00Z",
            },
        ),
    ]:
        directory.mkdir(parents=True)
        (directory / "fixture.json").write_text(json.dumps(payload), encoding="utf-8")

    panel = build_studio_provider_readiness(tmp_path)
    encoded = json.dumps(panel)

    assert panel["summary"]["readiness_status"] == "ready_for_cli_guarded_live_probe"
    assert panel["summary"]["queued_retry_count"] == 1
    assert panel["credential_posture"]["primary_provider_env_present"] is True
    assert panel["credential_posture"]["raw_credential_values_displayed"] is False
    assert "fixture-secret-not-returned" not in encoded
    assert panel["live_probe_readiness"]["live_smoke_execution_allowed_now"] is True
    assert panel["live_probe_readiness"]["approval_chain"]["approval_chain_complete_for_probe_attempt"] is True
    assert panel["live_probe_readiness"]["last_probe_marker"]["gate_approval_id"] == "fixture-approval"
    assert panel["authority"]["executes_live_probe"] is False
    assert panel["authority"]["writes_markers"] is False


def test_provider_readiness_redacts_secret_like_probe_metadata(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-fixture-secret-token-value")
    for directory, payload in [
        (
            tmp_path / "07_LOGS/Agent-Activity/_rpgl_provider_approvals",
            {"gate_approval_id": "fixture-approval", "approval_status": "approved"},
        ),
        (
            tmp_path / "07_LOGS/Agent-Activity/_rpgl_provider_live_probe_decisions",
            {"gate_approval_id": "fixture-approval", "decision": "approved"},
        ),
        (
            tmp_path / "07_LOGS/Agent-Activity/_rpgl_provider_live_probe_consumers",
            {"gate_approval_id": "fixture-approval", "consumer_status": "written"},
        ),
        (
            tmp_path / "runtime/providers/state/provider_live_probe_markers",
            {
                "gate_approval_id": "fixture-approval",
                "target": "primary test-key-fixture-secret-token-value",
                "marker_status": "reserved",
                "created_at": "2026-05-08T00:00:00Z",
            },
        ),
        (
            tmp_path / "runtime/providers/state/provider_live_probe_results",
            {
                "gate_approval_id": "fixture-approval",
                "target": "primary",
                "result_status": "failed",
                "created_at": "2026-05-08T00:01:00Z",
                "probe_outcome": {
                    "ok": False,
                    "error_type": "auth test-key-fixture-secret-token-value",
                    "reason": "provider returned test-key-fixture-secret-token-value",
                    "live_network_call_attempted": True,
                    "secret_value_read": True,
                },
            },
        ),
    ]:
        directory.mkdir(parents=True)
        (directory / "fixture.json").write_text(json.dumps(payload), encoding="utf-8")

    panel = build_studio_provider_readiness(tmp_path)
    encoded = json.dumps(panel)

    assert "test-key-fixture-secret-token-value" not in encoded
    assert panel["credential_posture"]["secret_values_included"] is False
    assert panel["live_probe_readiness"]["last_probe_marker"]["target"] == "[redacted-sensitive-provider-metadata]"
    assert panel["live_probe_readiness"]["last_probe_result"]["reason"] == "[redacted-sensitive-provider-metadata]"
    assert panel["live_probe_readiness"]["last_probe_result"]["secret_value_read"] is True


def test_provider_readiness_exposes_readable_binding_labels(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    panel = build_studio_provider_readiness(tmp_path)

    assert panel["summary"]["active_binding_label"] == "openai / gpt-5.5"
    assert panel["summary"]["fallback_binding_label"] == "local_oss / phi4-mini:latest"
