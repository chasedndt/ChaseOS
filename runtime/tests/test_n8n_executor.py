"""
test_n8n_executor.py — n8n Live Workflow Executor Tests

Tests:
  - execute_n8n_workflow() connection gate (deployment.enabled=false blocks)
  - Policy gate: blocked workflow, unknown workflow, caller not allowed, production without approval
  - Webhook trigger: success, HTTP error, network error
  - MCP tool trigger: success, missing token, HTTP error
  - Fail-open: network errors return ok=False dict, not exception
  - Result structure (ok, live_http_call, trigger_type, policy, executed_at_utc, etc.)
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import urllib.error
import urllib.request

import runtime.adapters.n8n.executor as _executor_mod
from runtime.adapters.n8n.executor import N8NExecutionError, execute_n8n_workflow


# ── Fixtures and helpers ───────────────────────────────────────────────────────

_N8N_CONFIG = Path(_ROOT / "runtime/policy/adapters/n8n_config.yaml")
_N8N_REGISTRY = Path(_ROOT / "runtime/policy/adapters/n8n_workflows.yaml")


def _live_env() -> dict[str, str]:
    """Minimal env that satisfies connection gating."""
    return {
        "N8N_BASE_URL": "http://localhost:5678",
        "N8N_MCP_ACCESS_TOKEN": "tok_test_abc",
    }


def _live_config(tmp_path: Path) -> Path:
    """Write an n8n_config.yaml with deployment.enabled=true."""
    content = """\
config_id: "n8n-test-config"
adapter_id: "n8n-workflow"
status: "live"
owner: "ChaseOS"

deployment:
  enabled: true
  base_url_env_var: "N8N_BASE_URL"
  mcp_access_token_env_var: "N8N_MCP_ACCESS_TOKEN"
  mcp_http_path: "/mcp-server/http"
  local_only: true
  live_probe_requires_explicit_flag: false
  secrets_configured: true
"""
    path = tmp_path / "n8n_config.yaml"
    path.write_text(content, encoding="utf-8")
    return path


def _registry_with(tmp_path: Path, *workflows: dict) -> Path:
    """Write an n8n_workflows.yaml with the given workflow entries."""
    lines = ["registry_id: test", "status: test", "owner: ChaseOS",
             "default_exposed_to_mcp: false", "default_approval_required: true", "workflows:"]
    for wf in workflows:
        lines.append(f"  - workflow_id: \"{wf['workflow_id']}\"")
        lines.append(f"    purpose: \"{wf.get('purpose', 'test purpose')}\"")
        lines.append(f"    exposed_to_mcp: {str(wf.get('exposed_to_mcp', False)).lower()}")
        lines.append(f"    trigger_type: \"{wf.get('trigger_type', 'webhook')}\"")
        lines.append(f"    approval_required: {str(wf.get('approval_required', True)).lower()}")
        callers = wf.get('allowed_callers', ['chaseos'])
        lines.append(f"    allowed_callers: [{', '.join(repr(c) for c in callers)}]")
        lines.append("    reads: []")
        lines.append("    writes: []")
        lines.append("    secrets_required: []")
        lines.append(f"    current_status: \"{wf.get('current_status', 'production_enabled')}\"")
    path = tmp_path / "n8n_workflows.yaml"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _fake_urlopen(status: int = 200, body: dict | None = None):
    """Returns a fake urlopen callable. Patch against _executor_mod.urlopen."""
    resp = MagicMock()
    resp.status = status
    resp.read.return_value = json.dumps(body or {"ok": True}).encode()
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return lambda req, timeout=10: resp


# ── TestConnectionGate ─────────────────────────────────────────────────────────

class TestConnectionGate:

    def test_blocked_when_deployment_disabled(self, tmp_path):
        # Use the real config (deployment.enabled=false)
        registry = _registry_with(tmp_path, {"workflow_id": "test_wf", "allowed_callers": ["chaseos"]})
        with pytest.raises(N8NExecutionError, match="blocked"):
            execute_n8n_workflow(
                "test_wf",
                caller="chaseos",
                config_path=_N8N_CONFIG,
                registry_path=registry,
                environ=_live_env(),
            )

    def test_blocked_when_base_url_not_set(self, tmp_path):
        config = _live_config(tmp_path)
        registry = _registry_with(tmp_path, {"workflow_id": "test_wf", "allowed_callers": ["chaseos"]})
        env = {"N8N_MCP_ACCESS_TOKEN": "tok_abc"}  # missing N8N_BASE_URL
        with pytest.raises(N8NExecutionError, match="blocked"):
            execute_n8n_workflow(
                "test_wf",
                caller="chaseos",
                config_path=config,
                registry_path=registry,
                environ=env,
            )

    def test_blocked_when_token_not_set(self, tmp_path):
        config = _live_config(tmp_path)
        registry = _registry_with(tmp_path, {"workflow_id": "test_wf", "allowed_callers": ["chaseos"]})
        env = {"N8N_BASE_URL": "http://localhost:5678"}  # missing token
        with pytest.raises(N8NExecutionError, match="blocked"):
            execute_n8n_workflow(
                "test_wf",
                caller="chaseos",
                config_path=config,
                registry_path=registry,
                environ=env,
            )

    def test_error_message_lists_reasons(self, tmp_path):
        config = _live_config(tmp_path)
        registry = _registry_with(tmp_path, {"workflow_id": "test_wf", "allowed_callers": ["chaseos"]})
        env: dict[str, str] = {}
        with pytest.raises(N8NExecutionError) as exc_info:
            execute_n8n_workflow(
                "test_wf",
                caller="chaseos",
                config_path=config,
                registry_path=registry,
                environ=env,
            )
        assert "N8N_BASE_URL" in str(exc_info.value)


# ── TestPolicyGate ─────────────────────────────────────────────────────────────

class TestPolicyGate:

    def test_unknown_workflow_raises(self, tmp_path):
        config = _live_config(tmp_path)
        registry = _registry_with(tmp_path, {"workflow_id": "real_wf", "allowed_callers": ["chaseos"]})
        with pytest.raises(N8NExecutionError, match="unknown"):
            execute_n8n_workflow(
                "nonexistent_wf",
                caller="chaseos",
                config_path=config,
                registry_path=registry,
                environ=_live_env(),
            )

    def test_caller_not_allowed_raises(self, tmp_path):
        config = _live_config(tmp_path)
        registry = _registry_with(tmp_path, {
            "workflow_id": "secure_wf",
            "allowed_callers": ["trusted_caller"],
        })
        with pytest.raises(N8NExecutionError, match="not allowed"):
            execute_n8n_workflow(
                "secure_wf",
                caller="untrusted_caller",
                config_path=config,
                registry_path=registry,
                environ=_live_env(),
            )

    def test_blocked_workflow_raises(self, tmp_path):
        config = _live_config(tmp_path)
        registry = _registry_with(tmp_path, {
            "workflow_id": "execute_trade_order",
            "purpose": "placeholder blocked",
            "current_status": "blocked",
            "exposed_to_mcp": False,
            "approval_required": True,
            "allowed_callers": ["chaseos"],
        })
        with pytest.raises(N8NExecutionError, match="blocked"):
            execute_n8n_workflow(
                "execute_trade_order",
                caller="chaseos",
                config_path=config,
                registry_path=registry,
                environ=_live_env(),
                production=True,
                approved=True,
            )

    def test_production_without_approval_raises(self, tmp_path):
        config = _live_config(tmp_path)
        registry = _registry_with(tmp_path, {
            "workflow_id": "prod_wf",
            "approval_required": True,
            "allowed_callers": ["chaseos"],
        })
        with pytest.raises(N8NExecutionError, match="policy blocked"):
            execute_n8n_workflow(
                "prod_wf",
                caller="chaseos",
                config_path=config,
                registry_path=registry,
                environ=_live_env(),
                production=True,
                approved=False,
            )


# ── TestWebhookTrigger ─────────────────────────────────────────────────────────

class TestWebhookTrigger:

    def _run_webhook(self, tmp_path, monkeypatch, *, status=200, body=None):
        config = _live_config(tmp_path)
        registry = _registry_with(tmp_path, {
            "workflow_id": "send_alert",
            "trigger_type": "webhook",
            "approval_required": False,
            "allowed_callers": ["chaseos"],
        })
        monkeypatch.setattr(_executor_mod, "urlopen", _fake_urlopen(status, body))
        return execute_n8n_workflow(
            "send_alert",
            caller="chaseos",
            config_path=config,
            registry_path=registry,
            environ=_live_env(),
        )

    def test_success_200(self, tmp_path, monkeypatch):
        result = self._run_webhook(tmp_path, monkeypatch, status=200)
        assert result["ok"] is True
        assert result["live_http_call"] is True
        assert result["http_status"] == 200
        assert result["trigger_type"] == "webhook"

    def test_result_structure(self, tmp_path, monkeypatch):
        result = self._run_webhook(tmp_path, monkeypatch)
        assert "workflow_id" in result
        assert "caller" in result
        assert "executed_at_utc" in result
        assert "policy" in result
        assert "reads" in result["policy"]
        assert "writes" in result["policy"]

    def test_http_error_returns_ok_false(self, tmp_path, monkeypatch):
        def fake(req, timeout=10):
            raise urllib.error.HTTPError(url="", code=401, msg="Unauthorized", hdrs=None, fp=MagicMock(read=lambda: b""))
        monkeypatch.setattr(_executor_mod, "urlopen", fake)
        config = _live_config(tmp_path)
        registry = _registry_with(tmp_path, {
            "workflow_id": "wf",
            "trigger_type": "webhook",
            "approval_required": False,
            "allowed_callers": ["chaseos"],
        })
        result = execute_n8n_workflow(
            "wf",
            caller="chaseos",
            config_path=config,
            registry_path=registry,
            environ=_live_env(),
        )
        assert result["ok"] is False
        assert result["http_status"] == 401
        assert result["live_http_call"] is True

    def test_network_error_returns_ok_false(self, tmp_path, monkeypatch):
        def fake(req, timeout=10):
            raise urllib.error.URLError("connection refused")
        monkeypatch.setattr(_executor_mod, "urlopen", fake)
        config = _live_config(tmp_path)
        registry = _registry_with(tmp_path, {
            "workflow_id": "wf",
            "trigger_type": "webhook",
            "approval_required": False,
            "allowed_callers": ["chaseos"],
        })
        result = execute_n8n_workflow(
            "wf",
            caller="chaseos",
            config_path=config,
            registry_path=registry,
            environ=_live_env(),
        )
        assert result["ok"] is False
        assert result["error"] == "url_error"
        assert result["live_http_call"] is True

    def test_payload_sent_in_request_body(self, tmp_path, monkeypatch):
        captured = {}

        def fake(req, timeout=10):
            captured["body"] = json.loads(req.data.decode())
            resp = MagicMock()
            resp.status = 200
            resp.read.return_value = b"{}"
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        monkeypatch.setattr(_executor_mod, "urlopen", fake)
        config = _live_config(tmp_path)
        registry = _registry_with(tmp_path, {
            "workflow_id": "wf",
            "trigger_type": "webhook",
            "approval_required": False,
            "allowed_callers": ["chaseos"],
        })
        execute_n8n_workflow(
            "wf",
            caller="chaseos",
            config_path=config,
            registry_path=registry,
            environ=_live_env(),
            payload={"message": "hello"},
        )
        assert captured["body"] == {"message": "hello"}


# ── TestMcpToolTrigger ─────────────────────────────────────────────────────────

class TestMcpToolTrigger:

    def _run_mcp(self, tmp_path, monkeypatch, *, status=200, body=None, env_override=None):
        config = _live_config(tmp_path)
        registry = _registry_with(tmp_path, {
            "workflow_id": "send_discord_draft_alert",
            "trigger_type": "mcp_tool",
            "approval_required": False,
            "allowed_callers": ["chaseos"],
        })
        env = env_override or _live_env()
        monkeypatch.setattr(_executor_mod, "urlopen", _fake_urlopen(status, body))
        return execute_n8n_workflow(
            "send_discord_draft_alert",
            caller="chaseos",
            config_path=config,
            registry_path=registry,
            environ=env,
        )

    def test_success_200(self, tmp_path, monkeypatch):
        result = self._run_mcp(tmp_path, monkeypatch)
        assert result["ok"] is True
        assert result["trigger_type"] == "mcp_tool"
        assert result["live_http_call"] is True

    def test_mcp_request_uses_tools_call_method(self, tmp_path, monkeypatch):
        captured = {}

        def fake(req, timeout=10):
            captured["body"] = json.loads(req.data.decode())
            resp = MagicMock()
            resp.status = 200
            resp.read.return_value = b"{}"
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        monkeypatch.setattr(_executor_mod, "urlopen", fake)
        config = _live_config(tmp_path)
        registry = _registry_with(tmp_path, {
            "workflow_id": "mcp_wf",
            "trigger_type": "mcp_tool",
            "approval_required": False,
            "allowed_callers": ["chaseos"],
        })
        execute_n8n_workflow(
            "mcp_wf",
            caller="chaseos",
            config_path=config,
            registry_path=registry,
            environ=_live_env(),
        )
        assert captured["body"]["method"] == "tools/call"
        assert captured["body"]["params"]["name"] == "mcp_wf"

    def test_mcp_request_includes_bearer_token(self, tmp_path, monkeypatch):
        captured = {}

        def fake(req, timeout=10):
            captured["headers"] = dict(req.headers)
            resp = MagicMock()
            resp.status = 200
            resp.read.return_value = b"{}"
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        monkeypatch.setattr(_executor_mod, "urlopen", fake)
        config = _live_config(tmp_path)
        registry = _registry_with(tmp_path, {
            "workflow_id": "mcp_wf",
            "trigger_type": "mcp_tool",
            "approval_required": False,
            "allowed_callers": ["chaseos"],
        })
        execute_n8n_workflow(
            "mcp_wf",
            caller="chaseos",
            config_path=config,
            registry_path=registry,
            environ=_live_env(),
        )
        assert "tok_test_abc" in captured["headers"].get("Authorization", "")

    def test_http_error_returns_ok_false(self, tmp_path, monkeypatch):
        def fake(req, timeout=10):
            raise urllib.error.HTTPError(url="", code=503, msg="Unavailable", hdrs=None, fp=MagicMock(read=lambda: b""))
        monkeypatch.setattr(_executor_mod, "urlopen", fake)
        config = _live_config(tmp_path)
        registry = _registry_with(tmp_path, {
            "workflow_id": "mcp_wf",
            "trigger_type": "mcp_tool",
            "approval_required": False,
            "allowed_callers": ["chaseos"],
        })
        result = execute_n8n_workflow(
            "mcp_wf",
            caller="chaseos",
            config_path=config,
            registry_path=registry,
            environ=_live_env(),
        )
        assert result["ok"] is False
        assert result["http_status"] == 503


# ── TestResultStructure ────────────────────────────────────────────────────────

class TestResultStructure:

    def test_result_always_has_required_keys(self, tmp_path, monkeypatch):
        config = _live_config(tmp_path)
        registry = _registry_with(tmp_path, {
            "workflow_id": "wf",
            "trigger_type": "webhook",
            "approval_required": False,
            "allowed_callers": ["chaseos"],
        })
        monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(200))
        result = execute_n8n_workflow(
            "wf",
            caller="chaseos",
            config_path=config,
            registry_path=registry,
            environ=_live_env(),
        )
        for key in ("ok", "live_http_call", "workflow_id", "caller", "trigger_type",
                    "production", "approved", "executed_at_utc", "policy"):
            assert key in result, f"missing key: {key}"

    def test_production_and_approved_reflected_in_result(self, tmp_path, monkeypatch):
        config = _live_config(tmp_path)
        registry = _registry_with(tmp_path, {
            "workflow_id": "wf",
            "trigger_type": "webhook",
            "approval_required": True,
            "allowed_callers": ["chaseos"],
        })
        monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(200))
        result = execute_n8n_workflow(
            "wf",
            caller="chaseos",
            config_path=config,
            registry_path=registry,
            environ=_live_env(),
            production=True,
            approved=True,
        )
        assert result["production"] is True
        assert result["approved"] is True

    def test_policy_block_includes_reads_and_writes(self, tmp_path, monkeypatch):
        config = _live_config(tmp_path)
        registry = _registry_with(tmp_path, {
            "workflow_id": "wf",
            "trigger_type": "webhook",
            "approval_required": False,
            "allowed_callers": ["chaseos"],
        })
        monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(200))
        result = execute_n8n_workflow(
            "wf",
            caller="chaseos",
            config_path=config,
            registry_path=registry,
            environ=_live_env(),
        )
        assert isinstance(result["policy"]["reads"], list)
        assert isinstance(result["policy"]["writes"], list)
        assert "current_status" in result["policy"]

    def test_executed_at_utc_is_iso_format(self, tmp_path, monkeypatch):
        config = _live_config(tmp_path)
        registry = _registry_with(tmp_path, {
            "workflow_id": "wf",
            "trigger_type": "webhook",
            "approval_required": False,
            "allowed_callers": ["chaseos"],
        })
        monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(200))
        result = execute_n8n_workflow(
            "wf",
            caller="chaseos",
            config_path=config,
            registry_path=registry,
            environ=_live_env(),
        )
        ts = result["executed_at_utc"]
        assert "T" in ts and "Z" in ts
