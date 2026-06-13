"""
test_phase9_sbp_whop.py — SBP Whop Delivery Adapter Tests (Phase 9 Pass 1F)

Tests:
  - WhopDeliveryAdapter credential resolution (per-pipeline env var + global fallback)
  - Missing API key fail-open behaviour
  - Missing channel_id fail-open behaviour
  - Content chunking (single, multi-chunk, exact-boundary)
  - _post_whop success / HTTP error / network error paths
  - Full deliver() success path (single + multi-chunk)
  - manifest.py: channel_id field parsed and stored on SBPDeliveryAdapterConfig
  - Registry: get_delivery_adapter("whop") returns WhopDeliveryAdapter (not stub)
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from runtime.sbp.delivery_adapters import (
    WhopDeliveryAdapter,
    get_delivery_adapter,
)
from runtime.sbp.manifest import validate_sbp_config


# ── Helpers ────────────────────────────────────────────────────────────────────

def _adapter() -> WhopDeliveryAdapter:
    return WhopDeliveryAdapter()


def _ctx(**overrides) -> dict:
    base = {
        "pipeline_id": "test_pipeline",
        "date": "2026-04-28",
        "channel_hint": "#test-channel",
        "channel_id": "exp_testforum123",
        "webhook_env_var": None,
    }
    base.update(overrides)
    return base


def _fake_urlopen(status: int = 201):
    resp = MagicMock()
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return lambda req, timeout=10: resp


def _minimal_sbp_config(delivery_adapters: list[dict]) -> dict:
    return {
        "trigger": {"type": "manual"},
        "input_adapters": [{"type": "vault-notes", "trust_tier": 1}],
        "execution_adapter": "openclaw",
        "delivery_adapters": delivery_adapters,
        "guardrail": {
            "permission_ceiling": "no_protected_file_writes",
            "human_in_loop": "optional",
            "fail_behavior": "halt_and_log",
        },
    }


# ── TestWhopApiKeyResolution ───────────────────────────────────────────────────

class TestWhopApiKeyResolution:

    def test_uses_per_pipeline_env_var_when_declared(self, monkeypatch):
        monkeypatch.setenv("MY_WHOP_KEY", "key_abc")
        key, var = _adapter()._resolve_api_key({"webhook_env_var": "MY_WHOP_KEY"})
        assert key == "key_abc"
        assert var == "MY_WHOP_KEY"

    def test_falls_back_to_default_env_var(self, monkeypatch):
        monkeypatch.setenv("WHOP_API_KEY", "key_global")
        monkeypatch.delenv("MY_WHOP_KEY", raising=False)
        key, var = _adapter()._resolve_api_key({"webhook_env_var": None})
        assert key == "key_global"
        assert var == "WHOP_API_KEY"

    def test_empty_string_when_neither_env_var_set(self, monkeypatch):
        monkeypatch.delenv("WHOP_API_KEY", raising=False)
        key, var = _adapter()._resolve_api_key({"webhook_env_var": None})
        assert key == ""
        assert var == "WHOP_API_KEY"

    def test_per_pipeline_var_takes_precedence_over_global(self, monkeypatch):
        monkeypatch.setenv("WHOP_API_KEY", "key_global")
        monkeypatch.setenv("STRIKEZONE_WHOP_KEY", "key_pipeline")
        key, var = _adapter()._resolve_api_key({"webhook_env_var": "STRIKEZONE_WHOP_KEY"})
        assert key == "key_pipeline"
        assert var == "STRIKEZONE_WHOP_KEY"

    def test_strips_whitespace_from_env_var_value(self, monkeypatch):
        monkeypatch.setenv("WHOP_API_KEY", "  key_spaces  ")
        key, _ = _adapter()._resolve_api_key({"webhook_env_var": None})
        assert key == "key_spaces"


# ── TestWhopFailOpen ───────────────────────────────────────────────────────────

class TestWhopFailOpen:

    def test_missing_api_key_returns_success_false(self, monkeypatch):
        monkeypatch.delenv("WHOP_API_KEY", raising=False)
        result = _adapter().deliver("content", _ctx(webhook_env_var=None))
        assert result["success"] is False
        assert result["stub"] is False
        assert "WHOP_API_KEY" in result["details"]
        assert "not set" in result["details"]

    def test_missing_channel_id_returns_success_false(self, monkeypatch):
        monkeypatch.setenv("WHOP_API_KEY", "key_abc")
        result = _adapter().deliver("content", _ctx(channel_id=None, webhook_env_var=None))
        assert result["success"] is False
        assert result["stub"] is False
        assert "channel_id" in result["details"]

    def test_empty_channel_id_returns_success_false(self, monkeypatch):
        monkeypatch.setenv("WHOP_API_KEY", "key_abc")
        result = _adapter().deliver("content", _ctx(channel_id="", webhook_env_var=None))
        assert result["success"] is False
        assert "channel_id" in result["details"]

    def test_per_pipeline_env_var_name_in_missing_key_message(self, monkeypatch):
        monkeypatch.delenv("MY_WHOP_KEY", raising=False)
        result = _adapter().deliver("content", _ctx(webhook_env_var="MY_WHOP_KEY"))
        assert result["success"] is False
        assert "MY_WHOP_KEY" in result["details"]


# ── TestWhopChunking ───────────────────────────────────────────────────────────

class TestWhopChunking:

    def test_short_content_is_single_chunk(self):
        chunks = _adapter()._chunk_content("hello world")
        assert chunks == ["hello world"]

    def test_content_at_exact_limit_is_single_chunk(self):
        a = _adapter()
        content = "x" * a.POST_CHAR_LIMIT
        assert a._chunk_content(content) == [content]

    def test_content_over_limit_splits_into_multiple_chunks(self):
        a = _adapter()
        content = "x" * (a.POST_CHAR_LIMIT + 100)
        chunks = a._chunk_content(content)
        assert len(chunks) == 2
        for c in chunks:
            assert len(c) <= a.POST_CHAR_LIMIT

    def test_splits_on_newline_boundary(self):
        a = _adapter()
        line = "a" * 100 + "\n"
        content = line * (a.POST_CHAR_LIMIT // 101 + 5)
        chunks = a._chunk_content(content)
        for c in chunks:
            assert len(c) <= a.POST_CHAR_LIMIT

    def test_no_chunk_exceeds_limit(self):
        a = _adapter()
        content = "line\n" * 5000
        for c in a._chunk_content(content):
            assert len(c) <= a.POST_CHAR_LIMIT

    def test_three_chunk_content(self):
        a = _adapter()
        content = "z" * (a.POST_CHAR_LIMIT * 2 + 500)
        chunks = a._chunk_content(content)
        assert len(chunks) == 3


# ── TestWhopPostMethod ─────────────────────────────────────────────────────────

class TestWhopPostMethod:

    def test_success_201(self, monkeypatch):
        monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(201))
        ok, detail = _adapter()._post_whop("key", "exp_123", "Title", "body")
        assert ok is True
        assert "201" in detail

    def test_success_200(self, monkeypatch):
        monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(200))
        ok, detail = _adapter()._post_whop("key", "exp_123", "Title", "body")
        assert ok is True
        assert "200" in detail

    def test_http_error_returns_failure(self, monkeypatch):
        def fake_urlopen(req, timeout=10):
            raise urllib.error.HTTPError(url="", code=401, msg="Unauthorized", hdrs=None, fp=None)
        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        ok, detail = _adapter()._post_whop("key", "exp_123", "Title", "body")
        assert ok is False
        assert "401" in detail

    def test_network_error_returns_failure(self, monkeypatch):
        def fake_urlopen(req, timeout=10):
            raise urllib.error.URLError("connection refused")
        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        ok, detail = _adapter()._post_whop("key", "exp_123", "Title", "body")
        assert ok is False
        assert "network error" in detail

    def test_unexpected_status_returns_failure(self, monkeypatch):
        monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(500))
        ok, detail = _adapter()._post_whop("key", "exp_123", "Title", "body")
        assert ok is False
        assert "500" in detail

    def test_request_includes_authorization_header(self, monkeypatch):
        captured = {}

        def fake_urlopen(req, timeout=10):
            captured["headers"] = dict(req.headers)
            resp = MagicMock()
            resp.status = 201
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        _adapter()._post_whop("my_api_key", "exp_123", "Title", "body")
        assert "Authorization" in captured["headers"]
        assert "my_api_key" in captured["headers"]["Authorization"]

    def test_request_body_contains_forum_id_and_content(self, monkeypatch):
        captured = {}

        def fake_urlopen(req, timeout=10):
            captured["body"] = json.loads(req.data.decode())
            resp = MagicMock()
            resp.status = 201
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        _adapter()._post_whop("key", "exp_abc", "My Title", "My body")
        assert captured["body"]["forum_experience_id"] == "exp_abc"
        assert captured["body"]["title"] == "My Title"
        assert captured["body"]["content"] == "My body"


# ── TestWhopDeliverSuccess ─────────────────────────────────────────────────────

class TestWhopDeliverSuccess:

    def test_single_chunk_success(self, monkeypatch):
        monkeypatch.setenv("WHOP_API_KEY", "key_live")
        monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(201))
        result = _adapter().deliver("short content", _ctx(webhook_env_var=None))
        assert result["success"] is True
        assert result["stub"] is False
        assert result["posts_sent"] == 1
        assert result["posts_total"] == 1
        assert "exp_testforum123" in result["details"]

    def test_gate_blocks_before_whop_post(self, monkeypatch):
        monkeypatch.setenv("WHOP_API_KEY", "key_live")
        called = {"urlopen": False}

        def fake_urlopen(req, timeout=10):
            called["urlopen"] = True
            raise AssertionError("urlopen should not be called when Gate blocks")

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        monkeypatch.setattr(
            "runtime.sbp.delivery_adapters.check_runtime_operation",
            lambda *args, **kwargs: (False, "blocked-by-test"),
        )

        result = _adapter().deliver("short content", _ctx(webhook_env_var=None))

        assert result["success"] is False
        assert called["urlopen"] is False
        assert "Gate blocked delivery" in result["details"]
        assert "blocked-by-test" in result["details"]

    def test_multi_chunk_success(self, monkeypatch):
        monkeypatch.setenv("WHOP_API_KEY", "key_live")
        monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(201))
        a = _adapter()
        content = "line\n" * (a.POST_CHAR_LIMIT // 5 + 100)
        result = a.deliver(content, _ctx(webhook_env_var=None))
        assert result["success"] is True
        assert result["posts_sent"] == result["posts_total"]
        assert result["posts_total"] >= 2

    def test_delivery_failure_mid_chunk_returns_partial_result(self, monkeypatch):
        monkeypatch.setenv("WHOP_API_KEY", "key_live")
        call_count = [0]

        def fake_urlopen(req, timeout=10):
            call_count[0] += 1
            if call_count[0] == 1:
                resp = MagicMock()
                resp.status = 201
                resp.__enter__ = lambda s: s
                resp.__exit__ = MagicMock(return_value=False)
                return resp
            raise urllib.error.HTTPError(url="", code=403, msg="Forbidden", hdrs=None, fp=None)

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        a = _adapter()
        content = "x" * (a.POST_CHAR_LIMIT * 2 + 500)
        result = a.deliver(content, _ctx(webhook_env_var=None))
        assert result["success"] is False
        assert result["posts_sent"] == 1
        assert result["posts_total"] >= 2

    def test_env_var_name_in_success_message(self, monkeypatch):
        monkeypatch.setenv("STRIKEZONE_WHOP_KEY", "key_sz")
        monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(201))
        result = _adapter().deliver("content", _ctx(webhook_env_var="STRIKEZONE_WHOP_KEY"))
        assert result["success"] is True
        assert "STRIKEZONE_WHOP_KEY" in result["details"]

    def test_continuation_title_for_second_chunk(self, monkeypatch):
        monkeypatch.setenv("WHOP_API_KEY", "key_live")
        captured_titles = []

        def fake_urlopen(req, timeout=10):
            body = json.loads(req.data.decode())
            captured_titles.append(body["title"])
            resp = MagicMock()
            resp.status = 201
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        a = _adapter()
        content = "x" * (a.POST_CHAR_LIMIT + 100)
        a.deliver(content, _ctx(webhook_env_var=None))
        assert len(captured_titles) == 2
        assert "cont." in captured_titles[1]


# ── TestManifestChannelId ──────────────────────────────────────────────────────

class TestManifestChannelId:

    def test_channel_id_parsed_from_manifest(self):
        config = validate_sbp_config(_minimal_sbp_config([
            {"type": "whop", "channel_id": "exp_abc123", "webhook_env_var": "WHOP_API_KEY"}
        ]), "test")
        assert config.delivery_adapters[0].channel_id == "exp_abc123"

    def test_channel_id_none_when_not_declared(self):
        config = validate_sbp_config(_minimal_sbp_config([
            {"type": "whop"}
        ]), "test")
        assert config.delivery_adapters[0].channel_id is None

    def test_channel_id_none_when_empty_string(self):
        config = validate_sbp_config(_minimal_sbp_config([
            {"type": "whop", "channel_id": ""}
        ]), "test")
        assert config.delivery_adapters[0].channel_id is None

    def test_channel_id_coexists_with_webhook_env_var_and_channel_hint(self):
        config = validate_sbp_config(_minimal_sbp_config([
            {
                "type": "whop",
                "channel_id": "exp_xyz",
                "webhook_env_var": "MY_WHOP_KEY",
                "channel_hint": "#my-channel",
            }
        ]), "test")
        da = config.delivery_adapters[0]
        assert da.channel_id == "exp_xyz"
        assert da.webhook_env_var == "MY_WHOP_KEY"
        assert da.channel_hint == "#my-channel"

    def test_channel_id_on_discord_adapter_ignored_gracefully(self):
        config = validate_sbp_config(_minimal_sbp_config([
            {"type": "discord", "channel_id": "not_used", "webhook_env_var": "DISCORD_WEBHOOK_URL"}
        ]), "test")
        assert config.delivery_adapters[0].channel_id == "not_used"


# ── TestRegistryEntry ──────────────────────────────────────────────────────────

class TestRegistryEntry:

    def test_get_delivery_adapter_whop_returns_real_adapter(self):
        a = get_delivery_adapter("whop")
        assert isinstance(a, WhopDeliveryAdapter)

    def test_whop_adapter_stub_is_false_on_missing_key(self, monkeypatch):
        monkeypatch.delenv("WHOP_API_KEY", raising=False)
        result = get_delivery_adapter("whop").deliver("x", _ctx(webhook_env_var=None))
        assert result["stub"] is False
