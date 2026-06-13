"""Tests for SBP delivery health telemetry."""

from __future__ import annotations

import json
import urllib.error
import uuid
from pathlib import Path

from runtime.cli import main as cli
from runtime.sbp.delivery_adapters import DiscordDeliveryAdapter, WhopDeliveryAdapter
from runtime.sbp.delivery_health import (
    DeliveryHealthEvent,
    append_delivery_health_event,
    classify_delivery_failure,
    delivery_health_path,
    load_delivery_health_events,
    safe_error_preview,
    summarize_delivery_health,
)


class _FakeResponse:
    def __init__(self, status: int):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _vault_root() -> Path:
    root = Path(__file__).resolve().parents[2] / ".codex_tmp_test" / "delivery_health_tests" / uuid.uuid4().hex
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_delivery_health_event_round_trip():
    vault_root = _vault_root()
    event = DeliveryHealthEvent(
        event_type="delivery.attempt_succeeded",
        adapter_id="discord",
        provider="discord",
        surface="delivery.discord_webhook",
        pipeline_id="sbp-test",
        delivery_target="env:TEST_DISCORD_WEBHOOK",
        run_date="2026-04-28",
        data={"chunks_total": 1},
    )

    persisted = append_delivery_health_event(vault_root, event)
    events = load_delivery_health_events(vault_root)
    summary = summarize_delivery_health(vault_root)

    assert persisted["status"] == "succeeded"
    assert events == [persisted]
    assert summary["event_count"] == 1
    assert summary["adapters"]["discord"]["latest_event"]["pipeline_id"] == "sbp-test"


def test_delivery_error_preview_redacts_delivery_secrets():
    preview = safe_error_preview(
        "Bearer whop-secret https://discord.com/api/webhooks/WEBHOOK_ID/WEBHOOK_TOKEN"
    )

    assert "whop-secret" not in preview
    assert "secret-token" not in preview
    assert "Bearer [redacted]" in preview
    assert "discord.com/api/webhooks/[redacted]" in preview
    assert classify_delivery_failure("whop: HTTP 401 from API endpoint") == "api_error"
    assert classify_delivery_failure("discord: Gate blocked delivery: denied") == "gate_blocked"
    assert classify_delivery_failure("whop: channel_id not set") == "configuration_missing"


def test_discord_missing_webhook_records_delivery_health(monkeypatch):
    vault_root = _vault_root()
    monkeypatch.delenv("TEST_DISCORD_WEBHOOK", raising=False)
    context = {
        "vault_root": str(vault_root),
        "pipeline_id": "sbp-test",
        "date": "2026-04-28",
        "webhook_env_var": "TEST_DISCORD_WEBHOOK",
    }

    result = DiscordDeliveryAdapter().deliver("hello", context)
    events = load_delivery_health_events(vault_root)

    assert result["success"] is False
    assert len(events) == 1
    assert events[0]["adapter_id"] == "discord"
    assert events[0]["status"] == "failed"
    assert events[0]["failure_reason"] == "credential_missing"
    assert events[0]["delivery_target"] == "env:TEST_DISCORD_WEBHOOK"


def test_discord_success_records_delivery_health_without_webhook_secret(monkeypatch):
    vault_root = _vault_root()
    requests = []

    def fake_urlopen(req, timeout):
        requests.append(req)
        return _FakeResponse(204)

    monkeypatch.setenv("TEST_DISCORD_WEBHOOK", "https://discord.com/api/webhooks/WEBHOOK_ID/WEBHOOK_TOKEN")
    monkeypatch.setattr("runtime.sbp.delivery_adapters.urllib.request.urlopen", fake_urlopen)
    context = {
        "vault_root": str(vault_root),
        "pipeline_id": "sbp-test",
        "date": "2026-04-28",
        "webhook_env_var": "TEST_DISCORD_WEBHOOK",
    }

    result = DiscordDeliveryAdapter().deliver("hello", context)
    events = load_delivery_health_events(vault_root)
    ledger_text = delivery_health_path(vault_root).read_text(encoding="utf-8")

    assert result["success"] is True
    assert requests
    assert events[0]["status"] == "succeeded"
    assert events[0]["data"]["env_var"] == "TEST_DISCORD_WEBHOOK"
    assert "secret-token" not in ledger_text
    assert "api/webhooks/123456" not in ledger_text


def test_discord_http_error_records_api_failure(monkeypatch):
    vault_root = _vault_root()
    def fake_urlopen(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 429, "rate limit", hdrs=None, fp=None)

    monkeypatch.setenv("TEST_DISCORD_WEBHOOK", "https://discord.com/api/webhooks/WEBHOOK_ID/WEBHOOK_TOKEN")
    monkeypatch.setattr("runtime.sbp.delivery_adapters.urllib.request.urlopen", fake_urlopen)
    context = {
        "vault_root": str(vault_root),
        "pipeline_id": "sbp-test",
        "date": "2026-04-28",
        "webhook_env_var": "TEST_DISCORD_WEBHOOK",
    }

    result = DiscordDeliveryAdapter().deliver("hello", context)
    events = load_delivery_health_events(vault_root)

    assert result["success"] is False
    assert events[0]["status"] == "failed"
    assert events[0]["failure_reason"] == "api_error"


def test_whop_missing_key_and_channel_config_record_delivery_health(monkeypatch):
    vault_root = _vault_root()
    monkeypatch.delenv("TEST_WHOP_API_KEY", raising=False)
    missing_key_context = {
        "vault_root": str(vault_root),
        "pipeline_id": "sbp-test",
        "date": "2026-04-28",
        "webhook_env_var": "TEST_WHOP_API_KEY",
        "channel_id": "exp_test",
    }

    missing_key = WhopDeliveryAdapter().deliver("hello", missing_key_context)

    monkeypatch.setenv("TEST_WHOP_API_KEY", "whop-secret")
    missing_channel_context = {
        "vault_root": str(vault_root),
        "pipeline_id": "sbp-test",
        "date": "2026-04-28",
        "webhook_env_var": "TEST_WHOP_API_KEY",
    }
    missing_channel = WhopDeliveryAdapter().deliver("hello", missing_channel_context)
    events = load_delivery_health_events(vault_root)

    assert missing_key["success"] is False
    assert missing_channel["success"] is False
    assert [event["failure_reason"] for event in events] == [
        "credential_missing",
        "configuration_missing",
    ]


def test_whop_success_records_delivery_health_without_api_key_secret(monkeypatch):
    vault_root = _vault_root()
    requests = []

    def fake_urlopen(req, timeout):
        requests.append(req)
        return _FakeResponse(201)

    monkeypatch.setenv("TEST_WHOP_API_KEY", "whop-secret")
    monkeypatch.setattr("runtime.sbp.delivery_adapters.urllib.request.urlopen", fake_urlopen)
    context = {
        "vault_root": str(vault_root),
        "pipeline_id": "sbp-test",
        "date": "2026-04-28",
        "webhook_env_var": "TEST_WHOP_API_KEY",
        "channel_id": "exp_test",
    }

    result = WhopDeliveryAdapter().deliver("hello", context)
    events = load_delivery_health_events(vault_root)
    ledger_text = delivery_health_path(vault_root).read_text(encoding="utf-8")

    assert result["success"] is True
    assert requests
    assert events[0]["adapter_id"] == "whop"
    assert events[0]["status"] == "succeeded"
    assert events[0]["delivery_target"] == "whop-forum:exp_test"
    assert "whop-secret" not in ledger_text


def test_sbp_delivery_health_cli_reports_summary():
    vault_root = _vault_root()
    append_delivery_health_event(
        vault_root,
        DeliveryHealthEvent(
            event_type="delivery.attempt_failed",
            adapter_id="discord",
            provider="discord",
            surface="delivery.discord_webhook",
            pipeline_id="sbp-test",
            failure_reason="credential_missing",
            data={},
        ),
    )

    parser = cli.build_parser()
    args = parser.parse_args(["sbp", "delivery-health", "--vault-root", str(vault_root), "--json"])
    assert args.func(args) == 0

    events = load_delivery_health_events(vault_root, adapter_id="discord")
    assert json.loads(delivery_health_path(vault_root).read_text(encoding="utf-8").splitlines()[0])
    assert events[0]["pipeline_id"] == "sbp-test"
