"""
test_phase9_sbp_pass1d.py — SBP Pass 1D: StrikeZone Discord Delivery
======================================================================

Tests for:
  1. Per-pipeline webhook_env_var on SBPDeliveryAdapterConfig (manifest schema)
  2. DiscordDeliveryAdapter webhook URL resolution (per-pipeline var > global fallback)
  3. Multi-embed chunking for long content
  4. base_handler/generic runner delivery context includes webhook_env_var
  5. sbp_strikezone_digest.yaml declares STRIKEZONE_DISCORD_WEBHOOK_URL

Run:
    .venv/Scripts/python.exe -m pytest runtime/aor/test_phase9_sbp_pass1d.py -q
"""

from __future__ import annotations

import json
import shutil
import sys
import urllib.error
import urllib.request
import uuid
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.sbp.manifest import (
    validate_sbp_config,
    load_sbp_config,
    SBPDeliveryAdapterConfig,
)
from runtime.sbp.delivery_adapters import DiscordDeliveryAdapter
from runtime.sbp.runner import run_sbp_pipeline


# ── Fixtures ───────────────────────────────────────────────────────────────────

def _minimal_sbp_config(delivery_adapters: list[dict]) -> dict:
    return {
        "trigger": {"type": "cron", "cron_expression": "0 6 * * 1-5"},
        "input_adapters": [{"type": "vault-notes", "trust_tier": 1, "paths": ["00_HOME/Now.md"]}],
        "execution_adapter": "openclaw",
        "delivery_adapters": delivery_adapters,
        "guardrail": {
            "permission_ceiling": "no_protected_file_writes",
            "write_scope": ["07_LOGS/SBP-Runs/"],
        },
    }


# ── Schema: webhook_env_var field ──────────────────────────────────────────────

class TestWebhookEnvVarSchema:
    def test_webhook_env_var_parsed_from_manifest(self):
        cfg = validate_sbp_config(
            _minimal_sbp_config([
                {"type": "discord", "channel_hint": "#test", "webhook_env_var": "MY_WEBHOOK_URL"},
            ]),
            "test-pipeline",
        )
        da = cfg.delivery_adapters[0]
        assert da.webhook_env_var == "MY_WEBHOOK_URL"

    def test_webhook_env_var_defaults_to_none(self):
        cfg = validate_sbp_config(
            _minimal_sbp_config([{"type": "discord"}]),
            "test-pipeline",
        )
        assert cfg.delivery_adapters[0].webhook_env_var is None

    def test_channel_hint_and_webhook_env_var_coexist(self):
        cfg = validate_sbp_config(
            _minimal_sbp_config([
                {
                    "type": "discord",
                    "channel_hint": "#strikezone-signals",
                    "webhook_env_var": "STRIKEZONE_DISCORD_WEBHOOK_URL",
                }
            ]),
            "sbp_strikezone_digest",
        )
        da = cfg.delivery_adapters[0]
        assert da.channel_hint == "#strikezone-signals"
        assert da.webhook_env_var == "STRIKEZONE_DISCORD_WEBHOOK_URL"

    def test_empty_string_webhook_env_var_becomes_none(self):
        cfg = validate_sbp_config(
            _minimal_sbp_config([{"type": "discord", "webhook_env_var": ""}]),
            "test",
        )
        assert cfg.delivery_adapters[0].webhook_env_var is None

    def test_vault_local_adapter_ignores_webhook_env_var(self):
        cfg = validate_sbp_config(
            _minimal_sbp_config([{"type": "vault-local"}]),
            "test",
        )
        assert cfg.delivery_adapters[0].webhook_env_var is None


def test_generic_runner_delivery_context_includes_delivery_adapter_fields(
    monkeypatch: pytest.MonkeyPatch,
):
    vault_root = (
        Path(__file__).resolve().parents[2]
        / ".codex_tmp_test"
        / f"sbp-runner-context-{uuid.uuid4().hex}"
    )
    observed_context: dict = {}

    class FakeDeliveryAdapter:
        def deliver(self, content: str, context: dict) -> dict:
            observed_context.update(context)
            return {"success": True, "details": "fake delivery", "stub": False}

    try:
        now_path = vault_root / "00_HOME" / "Now.md"
        now_path.parent.mkdir(parents=True)
        now_path.write_text("# Now\n\nRunner context test.", encoding="utf-8")

        manifest = {
            "id": "sbp_runner_context_test",
            "writeback_targets": ["07_LOGS/SBP-Runs/"],
            "sbp_config": _minimal_sbp_config([
                {
                    "type": "discord",
                    "channel_hint": "#runner-signals",
                    "webhook_env_var": "RUNNER_DISCORD_WEBHOOK_URL",
                    "channel_id": "ignored-for-discord",
                }
            ]),
        }

        monkeypatch.setattr(
            "runtime.sbp.runner.get_delivery_adapter",
            lambda adapter_type: FakeDeliveryAdapter(),
        )

        result = run_sbp_pipeline(manifest=manifest, inputs={}, vault_root=vault_root)

        assert result["delivery_results"][0]["success"] is True
        assert observed_context["pipeline_id"] == "sbp_runner_context_test"
        assert observed_context["channel_hint"] == "#runner-signals"
        assert observed_context["webhook_env_var"] == "RUNNER_DISCORD_WEBHOOK_URL"
        assert observed_context["channel_id"] == "ignored-for-discord"
    finally:
        shutil.rmtree(vault_root, ignore_errors=True)


# ── DiscordDeliveryAdapter: webhook resolution ─────────────────────────────────

class TestDiscordWebhookResolution:
    def test_uses_per_pipeline_env_var_when_declared(self, monkeypatch):
        monkeypatch.setenv("STRIKEZONE_DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/strikezone")
        monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)

        adapter = DiscordDeliveryAdapter()
        url, env_var = adapter._resolve_webhook_url({"webhook_env_var": "STRIKEZONE_DISCORD_WEBHOOK_URL"})
        assert url == "https://discord.com/api/webhooks/strikezone"
        assert env_var == "STRIKEZONE_DISCORD_WEBHOOK_URL"

    def test_falls_back_to_global_env_var_when_no_pipeline_var(self, monkeypatch):
        monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/global")
        monkeypatch.delenv("STRIKEZONE_DISCORD_WEBHOOK_URL", raising=False)

        adapter = DiscordDeliveryAdapter()
        url, env_var = adapter._resolve_webhook_url({})
        assert url == "https://discord.com/api/webhooks/global"
        assert env_var == "DISCORD_WEBHOOK_URL"

    def test_per_pipeline_var_takes_precedence_over_global(self, monkeypatch):
        monkeypatch.setenv("STRIKEZONE_DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/strikezone")
        monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/ops")

        adapter = DiscordDeliveryAdapter()
        url, _ = adapter._resolve_webhook_url({"webhook_env_var": "STRIKEZONE_DISCORD_WEBHOOK_URL"})
        assert url == "https://discord.com/api/webhooks/strikezone"

    def test_returns_empty_url_when_env_var_not_set(self, monkeypatch):
        monkeypatch.delenv("STRIKEZONE_DISCORD_WEBHOOK_URL", raising=False)
        monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)

        adapter = DiscordDeliveryAdapter()
        url, env_var = adapter._resolve_webhook_url({"webhook_env_var": "STRIKEZONE_DISCORD_WEBHOOK_URL"})
        assert url == ""
        assert env_var == "STRIKEZONE_DISCORD_WEBHOOK_URL"

    def test_deliver_returns_failure_with_env_var_name_when_unset(self, monkeypatch, capsys):
        monkeypatch.delenv("STRIKEZONE_DISCORD_WEBHOOK_URL", raising=False)
        monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)

        adapter = DiscordDeliveryAdapter()
        result = adapter.deliver("content", {"webhook_env_var": "STRIKEZONE_DISCORD_WEBHOOK_URL"})
        assert result["success"] is False
        assert "STRIKEZONE_DISCORD_WEBHOOK_URL" in result["details"]


# ── DiscordDeliveryAdapter: chunking ──────────────────────────────────────────

class TestDiscordChunking:
    def test_short_content_is_single_chunk(self):
        adapter = DiscordDeliveryAdapter()
        chunks = adapter._chunk_content("Hello world")
        assert len(chunks) == 1
        assert chunks[0] == "Hello world"

    def test_content_at_limit_is_single_chunk(self):
        adapter = DiscordDeliveryAdapter()
        content = "x" * adapter.EMBED_CHAR_LIMIT
        chunks = adapter._chunk_content(content)
        assert len(chunks) == 1

    def test_content_over_limit_splits_into_multiple_chunks(self):
        adapter = DiscordDeliveryAdapter()
        content = "x" * (adapter.EMBED_CHAR_LIMIT + 100)
        chunks = adapter._chunk_content(content)
        assert len(chunks) == 2

    def test_chunks_prefer_newline_boundaries(self):
        adapter = DiscordDeliveryAdapter()
        line = "a" * 500 + "\n"
        # Build content that requires splitting but has newline boundaries
        content = line * (adapter.EMBED_CHAR_LIMIT // 501 + 2)
        chunks = adapter._chunk_content(content)
        assert len(chunks) >= 2
        # Each chunk should be within the limit
        for chunk in chunks:
            assert len(chunk) <= adapter.EMBED_CHAR_LIMIT

    def test_all_content_preserved_across_chunks(self):
        adapter = DiscordDeliveryAdapter()
        content = "line\n" * 2000
        chunks = adapter._chunk_content(content)
        reassembled = "\n".join(chunks)
        # All original words should be present
        assert "line" in reassembled

    def test_long_digest_produces_multiple_embeds(self, monkeypatch):
        """Multi-chunk content sends multiple webhook POSTs."""
        adapter = DiscordDeliveryAdapter()
        monkeypatch.setenv("STRIKEZONE_DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test")

        posts_captured = []

        def fake_urlopen(req, timeout=None):
            posts_captured.append(json.loads(req.data.decode()))
            resp = MagicMock()
            resp.status = 204
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

        long_content = "## Section\n\n" + ("word " * 400 + "\n") * 20
        result = adapter.deliver(long_content, {
            "pipeline_id": "sbp_strikezone_digest",
            "date": "2026-04-27",
            "webhook_env_var": "STRIKEZONE_DISCORD_WEBHOOK_URL",
        })

        assert result["success"] is True
        assert result["chunks_total"] > 1
        assert result["chunks_sent"] == result["chunks_total"]
        assert len(posts_captured) == result["chunks_total"]

    def test_first_chunk_uses_main_title(self, monkeypatch):
        adapter = DiscordDeliveryAdapter()
        monkeypatch.setenv("STRIKEZONE_DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test")

        posts_captured = []

        def fake_urlopen(req, timeout=None):
            posts_captured.append(json.loads(req.data.decode()))
            resp = MagicMock()
            resp.status = 204
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

        long_content = "x" * (adapter.EMBED_CHAR_LIMIT + 100)
        adapter.deliver(long_content, {
            "pipeline_id": "sbp_strikezone_digest",
            "date": "2026-04-27",
            "webhook_env_var": "STRIKEZONE_DISCORD_WEBHOOK_URL",
        })

        first_embed_title = posts_captured[0]["embeds"][0]["title"]
        assert "2026-04-27" in first_embed_title
        # Second chunk has "cont." marker
        if len(posts_captured) > 1:
            second_embed_title = posts_captured[1]["embeds"][0]["title"]
            assert "cont." in second_embed_title


# ── DiscordDeliveryAdapter: successful delivery ────────────────────────────────

class TestDiscordSuccessfulDelivery:
    def test_single_chunk_delivers_successfully(self, monkeypatch):
        monkeypatch.setenv("STRIKEZONE_DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test")

        def fake_urlopen(req, timeout=None):
            resp = MagicMock()
            resp.status = 204
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

        adapter = DiscordDeliveryAdapter()
        result = adapter.deliver("short content", {
            "pipeline_id": "sbp_strikezone_digest",
            "date": "2026-04-27",
            "webhook_env_var": "STRIKEZONE_DISCORD_WEBHOOK_URL",
        })

        assert result["success"] is True
        assert "STRIKEZONE_DISCORD_WEBHOOK_URL" in result["details"]
        assert result["stub"] is False

    def test_gate_blocks_before_webhook_post(self, monkeypatch):
        monkeypatch.setenv("STRIKEZONE_DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test")
        called = {"urlopen": False}

        def fake_urlopen(req, timeout=None):
            called["urlopen"] = True
            raise AssertionError("urlopen should not be called when Gate blocks")

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        monkeypatch.setattr(
            "runtime.sbp.delivery_adapters.check_runtime_operation",
            lambda *args, **kwargs: (False, "blocked-by-test"),
        )

        adapter = DiscordDeliveryAdapter()
        result = adapter.deliver("short content", {
            "pipeline_id": "sbp_strikezone_digest",
            "date": "2026-04-27",
            "webhook_env_var": "STRIKEZONE_DISCORD_WEBHOOK_URL",
        })

        assert result["success"] is False
        assert called["urlopen"] is False
        assert "Gate blocked delivery" in result["details"]
        assert "blocked-by-test" in result["details"]

    def test_http_error_returns_failure(self, monkeypatch):
        monkeypatch.setenv("STRIKEZONE_DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test")

        def fake_urlopen(req, timeout=None):
            raise urllib.error.HTTPError(None, 400, "Bad Request", {}, None)

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

        adapter = DiscordDeliveryAdapter()
        result = adapter.deliver("content", {
            "webhook_env_var": "STRIKEZONE_DISCORD_WEBHOOK_URL",
            "pipeline_id": "test",
            "date": "2026-04-27",
        })

        assert result["success"] is False
        assert "400" in result["details"]

    def test_channel_hint_appears_in_embed_title(self, monkeypatch):
        monkeypatch.setenv("STRIKEZONE_DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test")

        posts_captured = []

        def fake_urlopen(req, timeout=None):
            posts_captured.append(json.loads(req.data.decode()))
            resp = MagicMock()
            resp.status = 204
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

        adapter = DiscordDeliveryAdapter()
        adapter.deliver("content", {
            "pipeline_id": "sbp_strikezone_digest",
            "date": "2026-04-27",
            "channel_hint": "#strikezone-signals",
            "webhook_env_var": "STRIKEZONE_DISCORD_WEBHOOK_URL",
        })

        title = posts_captured[0]["embeds"][0]["title"]
        assert "#strikezone-signals" in title


# ── Manifest: strikezone digest declares correct env var ──────────────────────

class TestStrikeZoneManifestDelivery:
    def _load_manifest(self) -> dict:
        import yaml
        manifest_path = (
            Path(__file__).resolve().parents[2]
            / "runtime" / "workflows" / "registry" / "sbp_strikezone_digest.yaml"
        )
        with open(manifest_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_manifest_declares_strikezone_webhook_env_var(self):
        manifest = self._load_manifest()
        discord_adapters = [
            da for da in manifest["sbp_config"]["delivery_adapters"]
            if da.get("type") == "discord"
        ]
        assert discord_adapters, "no discord delivery adapter in manifest"
        da = discord_adapters[0]
        assert da.get("webhook_env_var") == "STRIKEZONE_DISCORD_WEBHOOK_URL"

    def test_manifest_still_declares_vault_local(self):
        manifest = self._load_manifest()
        types = [da["type"] for da in manifest["sbp_config"]["delivery_adapters"]]
        assert "vault-local" in types

    def test_manifest_passes_sbp_config_validation(self):
        manifest = self._load_manifest()
        cfg = load_sbp_config(manifest)
        discord_da = next((da for da in cfg.delivery_adapters if da.type == "discord"), None)
        assert discord_da is not None
        assert discord_da.webhook_env_var == "STRIKEZONE_DISCORD_WEBHOOK_URL"
        assert discord_da.channel_hint == "#strikezone-signals"

    def test_manifest_channel_hint_is_strikezone_signals(self):
        manifest = self._load_manifest()
        discord_adapters = [
            da for da in manifest["sbp_config"]["delivery_adapters"]
            if da.get("type") == "discord"
        ]
        assert discord_adapters[0].get("channel_hint") == "#strikezone-signals"
