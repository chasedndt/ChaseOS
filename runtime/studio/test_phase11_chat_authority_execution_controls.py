"""Tests for Studio Chat authority execution controls."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.phase11_chat_authority_execution_controls import (
    build_phase11_chat_authority_execution_controls,
    format_phase11_chat_authority_execution_controls,
)
from runtime.studio.phase11_chat_live_provider_execution_executor import (
    execute_phase11_chat_live_provider_execution,
)
from runtime.studio.phase11_chat_panel_contract import build_phase11_chat_panel_contract
from runtime.studio.shell.api import StudioAPI


def _write_runtime_capabilities(vault: Path) -> None:
    hermes = vault / "runtime" / "hermes"
    openclaw = vault / "runtime" / "openclaw"
    hermes.mkdir(parents=True, exist_ok=True)
    openclaw.mkdir(parents=True, exist_ok=True)
    hermes.joinpath("capabilities.yaml").write_text(
        "\n".join(
            [
                "runtime: hermes",
                "bus_name: Hermes",
                "display_name: Hermes",
                "handles:",
                "  - task_type: planning",
                "    priority: primary",
                "priority_ceiling: high",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    openclaw.joinpath("capabilities.yaml").write_text(
        "\n".join(
            [
                "runtime: openclaw",
                "bus_name: OpenClaw",
                "display_name: OpenClaw",
                "handles:",
                "  - task_type: operator-briefing",
                "    priority: primary",
                "priority_ceiling: normal",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_authority_execution_controls_prepare_all_lanes(tmp_path: Path) -> None:
    _write_runtime_capabilities(tmp_path)

    payload = build_phase11_chat_authority_execution_controls(
        tmp_path,
        message="Ask Hermes to plan and send the update to Discord.",
    )

    assert payload["ok"] is True
    assert payload["surface"] == "phase11_chat_authority_execution_controls"
    assert payload["summary"]["manual_test_ready"] is True
    assert payload["summary"]["lane_count"] == 4
    assert payload["prepared_digests"]["expected_provider_digest"]
    assert payload["prepared_digests"]["expected_main_runtime_digest"]
    assert payload["prepared_digests"]["expected_discord_control_digest"]
    assert payload["prepared_digests"]["expected_cron_control_digest"]
    assert payload["authority"]["discord_api_calls_allowed_from_studio"] is False
    assert payload["authority"]["discord_control_handoff_to_runtime_allowed"] is True
    assert payload["authority"]["external_scheduler_mutation_allowed_from_studio"] is False
    assert payload["authority"]["credential_values_visible"] is False


def test_authority_execution_controls_embedded_in_chat_panel(tmp_path: Path) -> None:
    _write_runtime_capabilities(tmp_path)

    contract = build_phase11_chat_panel_contract(tmp_path, message="run this through Hermes and OpenClaw")

    controls = contract["chat_authority_execution_controls"]
    assert controls["surface"] == "phase11_chat_authority_execution_controls"
    assert contract["readiness"]["studio_chat_authority_execution_controls_ready"] is True
    assert contract["readiness"]["studio_chat_authority_execution_provider_executor_ready"] is True
    assert "execute_phase11_chat_authority_execution_controls" in contract["api_methods"]


def test_live_provider_executor_blocks_without_env(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    preview = build_phase11_chat_authority_execution_controls(tmp_path, message="answer this")
    digest = preview["prepared_digests"]["expected_provider_digest"]

    result = execute_phase11_chat_live_provider_execution(
        tmp_path,
        message="answer this",
        expected_provider_digest=digest,
        operator_approval_statement="Approved provider call.",
    )

    assert result["ok"] is False
    assert "provider_credential_environment_missing" in result["blocked_reasons"]
    assert result["provider_call"]["provider_call_performed"] is False


def test_live_provider_executor_uses_env_without_returning_secret(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-test-not-real")

    def fake_call(**kwargs):
        assert kwargs["api_key"] == "test-key-test-not-real"
        return {
            "ok": True,
            "status_code": 200,
            "response_id": "resp_test",
            "output_text": "Hermes-style response",
            "raw_response_included": False,
        }

    monkeypatch.setattr(
        "runtime.studio.phase11_chat_live_provider_execution_executor._call_provider_api",
        fake_call,
    )
    preview = build_phase11_chat_authority_execution_controls(tmp_path, message="answer this")
    digest = preview["prepared_digests"]["expected_provider_digest"]

    result = execute_phase11_chat_live_provider_execution(
        tmp_path,
        message="answer this",
        expected_provider_digest=digest,
        operator_approval_statement="Approved provider call.",
    )

    assert result["ok"] is True
    assert result["summary"]["provider_call_performed"] is True
    assert result["summary"]["credential_env_reference_used"] is True
    assert result["summary"]["credential_value_displayed"] is False
    assert "test-key-test-not-real" not in str(result)


def test_authority_execution_controls_api_wraps_prepare_payload(tmp_path: Path) -> None:
    _write_runtime_capabilities(tmp_path)

    response = StudioAPI(tmp_path).get_phase11_chat_authority_execution_controls(
        "manual full-stack test",
        "chat-answer",
    )

    assert response["ok"] is True
    assert response["data"]["surface"] == "phase11_chat_authority_execution_controls"
    assert response["data"]["prepared_digests"]["expected_main_runtime_digest"]


def test_authority_execution_controls_format_lists_digests(tmp_path: Path) -> None:
    formatted = format_phase11_chat_authority_execution_controls(
        build_phase11_chat_authority_execution_controls(tmp_path, message="manual test")
    )

    assert "provider_digest" in formatted
    assert "main_runtime_digest" in formatted
    assert "discord_digest" in formatted
