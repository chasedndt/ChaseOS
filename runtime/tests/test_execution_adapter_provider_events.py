"""Tests for execution-adapter provider-state ledger emission."""

from __future__ import annotations

import sys
import shutil
import urllib.error
import uuid
from pathlib import Path
from unittest.mock import patch


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.execution_adapters.execute import ExecutionAdapterError, execute_synthesis  # noqa: E402
from runtime.providers.state_ledger import (  # noqa: E402
    ProviderStateEvent,
    append_provider_state_event,
    load_provider_state_events,
)


def _write_openclaw_config(vault: Path) -> None:
    config_dir = vault / "runtime" / "openclaw"
    config_dir.mkdir(parents=True)
    (config_dir / "model_config.yaml").write_text(
        "\n".join(
            [
                "primary: claude-sonnet-4-6",
                "fallbacks:",
                "  - claude-haiku-4-5-20251001",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_openai_config(vault: Path) -> None:
    config_dir = vault / "runtime" / "openclaw"
    config_dir.mkdir(parents=True)
    (config_dir / "model_config.yaml").write_text(
        "\n".join(
            [
                "primary:",
                "  model_id: gpt-5.5",
                "  max_tokens: 512",
                "  temperature: 0.2",
                "fallbacks: []",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_openai_to_claude_fallback_config(vault: Path) -> None:
    config_dir = vault / "runtime" / "openclaw"
    config_dir.mkdir(parents=True)
    (config_dir / "model_config.yaml").write_text(
        "\n".join(
            [
                "primary:",
                "  model_id: gpt-5.5",
                "  max_tokens: 512",
                "  temperature: 0.2",
                "fallbacks:",
                "  - model_id: claude-haiku-4-5-20251001",
                "    max_tokens: 512",
                "    temperature: 0.2",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _make_vault() -> Path:
    vault = _VAULT_ROOT / ".codex_tmp_test" / "provider-adapter-events" / uuid.uuid4().hex / "vault"
    vault.mkdir(parents=True)
    return vault


def _cleanup_vault(vault: Path) -> None:
    root = (_VAULT_ROOT / ".codex_tmp_test" / "provider-adapter-events").resolve()
    target = vault.parent.resolve()
    if target.parent == root:
        shutil.rmtree(target, ignore_errors=True)


def _mock_response(text: str = "ok") -> dict:
    return {"text": text, "usage": {"input_tokens": 1, "output_tokens": 1}}


def _rate_limited_error() -> ExecutionAdapterError:
    http_error = urllib.error.HTTPError(
        "https://api.anthropic.com/v1/messages",
        429,
        "Too Many Requests",
        {"Retry-After": "30"},
        None,
    )
    error = ExecutionAdapterError("Anthropic API HTTP 429 for model 'claude-sonnet-4-6': rate_limit_error")
    error.__cause__ = http_error
    return error


def test_execute_synthesis_records_primary_request() -> None:
    vault = _make_vault()
    _write_openclaw_config(vault)

    try:
        with patch("runtime.execution_adapters.execute._get_api_key", return_value="key"):
            with patch("runtime.execution_adapters.execute._call_anthropic", return_value=_mock_response("primary")):
                result = execute_synthesis(
                    prompt_system="sys",
                    prompt_user="user",
                    execution_adapter="openclaw",
                    vault_root=vault,
                )

        events = load_provider_state_events(vault)
        assert result.text == "primary"
        assert [event["event_type"] for event in events] == ["provider.request"]
        assert events[0]["runtime"] == "openclaw"
        assert events[0]["provider_id"] == "claude"
        assert events[0]["model_id"] == "claude-sonnet-4-6"
        assert events[0]["data"]["role"] == "primary"
        assert events[0]["data"]["attempt_index"] == 0
    finally:
        _cleanup_vault(vault)


def test_execute_synthesis_records_rate_limit_and_fallback() -> None:
    vault = _make_vault()
    _write_openclaw_config(vault)
    call_count = {"n": 0}

    def fake_call(**_kwargs: object) -> dict:
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise _rate_limited_error()
        return _mock_response("fallback")

    try:
        with patch("runtime.execution_adapters.execute._get_api_key", return_value="key"):
            with patch("runtime.execution_adapters.execute._call_anthropic", side_effect=fake_call):
                result = execute_synthesis(
                    prompt_system="sys",
                    prompt_user="user",
                    execution_adapter="openclaw",
                    vault_root=vault,
                )

        events = load_provider_state_events(vault)
        assert result.text == "fallback"
        assert result.fallback_used is True
        assert [event["event_type"] for event in events] == [
            "provider.request",
            "provider.rate_limited",
            "provider.fallback_activated",
            "provider.request",
        ]
        assert events[1]["data"]["status_code"] == 429
        assert events[1]["data"]["retry_after_seconds"] == 30
        assert events[2]["data"]["reason"] == "rate_limit"
        assert events[2]["data"]["failed_model_id"] == "claude-sonnet-4-6"
        assert events[2]["data"]["fallback_model_id"] == "claude-haiku-4-5-20251001"
        assert events[3]["data"]["role"] == "fallback"
    finally:
        _cleanup_vault(vault)


def test_execute_synthesis_records_primary_recovery_after_active_fallback() -> None:
    vault = _make_vault()
    _write_openclaw_config(vault)

    try:
        append_provider_state_event(
            vault,
            ProviderStateEvent(
                event_type="provider.fallback_activated",
                runtime="openclaw",
                provider_id="claude",
                model_id="claude-haiku-4-5-20251001",
                source={"surface": "test"},
                data={
                    "primary_model_id": "claude-sonnet-4-6",
                    "fallback_model_id": "claude-haiku-4-5-20251001",
                    "reason": "rate_limit",
                },
            ),
        )

        with patch("runtime.execution_adapters.execute._get_api_key", return_value="key"):
            with patch("runtime.execution_adapters.execute._call_anthropic", return_value=_mock_response("primary")):
                result = execute_synthesis(
                    prompt_system="sys",
                    prompt_user="user",
                    execution_adapter="openclaw",
                    vault_root=vault,
                )

        events = load_provider_state_events(vault)
        assert result.fallback_used is False
        assert [event["event_type"] for event in events] == [
            "provider.fallback_activated",
            "provider.request",
            "provider.recovery_primary_completed",
        ]
        assert events[2]["model_id"] == "claude-sonnet-4-6"
        assert events[2]["data"]["previous_recovery_status"] == "fallback_active"
    finally:
        _cleanup_vault(vault)

def test_execute_synthesis_routes_openai_models_through_runtime_adapter(monkeypatch) -> None:
    vault = _make_vault()
    _write_openai_config(vault)

    try:
        monkeypatch.setenv("OPENAI_API_KEY", "fixture-secret-not-returned")
        with patch(
            "runtime.execution_adapters.execute._call_openai_chat_completions",
            return_value=_mock_response("openai-runtime"),
        ) as call_openai:
            result = execute_synthesis(
                prompt_system="sys",
                prompt_user="user",
                execution_adapter="openclaw",
                vault_root=vault,
            )

        events = load_provider_state_events(vault)
        assert result.text == "openai-runtime"
        assert result.model_id == "gpt-5.5"
        assert result.fallback_used is False
        assert call_openai.call_count == 1
        assert [event["event_type"] for event in events] == ["provider.request"]
        assert events[0]["provider_id"] == "openai"
        assert events[0]["model_id"] == "gpt-5.5"
    finally:
        _cleanup_vault(vault)


def test_execute_synthesis_missing_provider_secret_can_fall_back_to_next_runtime_model(monkeypatch) -> None:
    vault = _make_vault()
    _write_openai_to_claude_fallback_config(vault)

    try:
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "fixture-secret-not-returned")
        with patch(
            "runtime.execution_adapters.execute._call_anthropic",
            return_value=_mock_response("claude-fallback"),
        ):
            result = execute_synthesis(
                prompt_system="sys",
                prompt_user="user",
                execution_adapter="openclaw",
                vault_root=vault,
            )

        events = load_provider_state_events(vault)
        assert result.text == "claude-fallback"
        assert result.fallback_used is True
        assert [event["event_type"] for event in events] == [
            "provider.request",
            "provider.fallback_activated",
            "provider.request",
        ]
        assert events[0]["provider_id"] == "openai"
        assert events[1]["data"]["reason"] == "model_error"
        assert events[1]["data"]["failed_provider_id"] == "openai"
        assert events[1]["data"]["fallback_provider_id"] == "claude"
        assert events[2]["provider_id"] == "claude"
    finally:
        _cleanup_vault(vault)
