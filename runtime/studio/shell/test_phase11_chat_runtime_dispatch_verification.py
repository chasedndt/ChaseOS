"""Tests for Phase 11 Chat Runtime Dispatch Verification pass.

Covers:
  - build_chat_runtime_availability() freshness logic
  - build_phase11_chat_runtime_dispatch_verification() import/dispatch checks
  - api.py get_chat_runtime_availability() method envelope
  - panel_registry verification flags
  - Frontend index.html offline banner element present
  - CSS pip classes present
"""
from __future__ import annotations

import json
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "00_HOME").mkdir()
    (vault / "00_HOME" / "Now.md").write_text("# Now\n", encoding="utf-8")
    bus_dir = vault / "runtime" / "agent_bus"
    bus_dir.mkdir(parents=True)
    return vault


def _make_vault_with_bus(tmp_path: Path, *, hermes_age_s: float | None = None, openclaw_age_s: float | None = None) -> Path:
    vault = _make_vault(tmp_path)
    db_path = vault / "runtime" / "agent_bus" / "agent_bus.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS heartbeats "
        "(id INTEGER PRIMARY KEY, runtime TEXT, runtime_instance_id TEXT, "
        "heartbeat_scope TEXT, control_surface TEXT, control_surface_key TEXT, "
        "last_seen TEXT, status TEXT)"
    )
    conn.execute("CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY)")
    now = datetime.now(timezone.utc)
    if hermes_age_s is not None:
        ts = (now - timedelta(seconds=hermes_age_s)).isoformat().replace("+00:00", "Z")
        conn.execute(
            "INSERT INTO heartbeats (runtime, last_seen, status) VALUES (?, ?, ?)",
            ("Hermes", ts, "active"),
        )
    if openclaw_age_s is not None:
        ts = (now - timedelta(seconds=openclaw_age_s)).isoformat().replace("+00:00", "Z")
        conn.execute(
            "INSERT INTO heartbeats (runtime, last_seen, status) VALUES (?, ?, ?)",
            ("OpenClaw", ts, "active"),
        )
    conn.commit()
    conn.close()
    return vault


# ── Freshness logic ───────────────────────────────────────────────────────────

class TestHeartbeatFreshness:
    def test_fresh_under_120s(self):
        from runtime.studio.phase11_chat_runtime_dispatch_verification import _heartbeat_freshness
        assert _heartbeat_freshness(60.0) == "fresh"

    def test_fresh_at_boundary(self):
        from runtime.studio.phase11_chat_runtime_dispatch_verification import _heartbeat_freshness
        assert _heartbeat_freshness(119.9) == "fresh"

    def test_recent_between_120_and_900(self):
        from runtime.studio.phase11_chat_runtime_dispatch_verification import _heartbeat_freshness
        assert _heartbeat_freshness(300.0) == "recent"

    def test_stale_over_900(self):
        from runtime.studio.phase11_chat_runtime_dispatch_verification import _heartbeat_freshness
        assert _heartbeat_freshness(901.0) == "stale"

    def test_offline_when_none(self):
        from runtime.studio.phase11_chat_runtime_dispatch_verification import _heartbeat_freshness
        assert _heartbeat_freshness(None) == "offline"


# ── build_chat_runtime_availability ──────────────────────────────────────────

class TestBuildChatRuntimeAvailability:
    def test_no_bus_storage_all_offline(self, tmp_path, monkeypatch):
        import runtime.studio.phase11_chat_runtime_dispatch_verification as _m
        monkeypatch.setattr(_m, "_check_gateway_ports",
            lambda a: {"gateway_port_online": False, "gateway_port_listening": None, "gateway_ports_checked": []})
        vault = _make_vault(tmp_path)
        from runtime.studio.phase11_chat_runtime_dispatch_verification import build_chat_runtime_availability
        result = build_chat_runtime_availability(vault)
        assert result["ok"] is True
        assert result["any_runtime_online"] is False
        by_adapter = result["runtime_by_adapter"]
        assert by_adapter["hermes"]["freshness"] == "offline"
        assert by_adapter["openclaw"]["freshness"] == "offline"
        assert by_adapter["claude-code"]["freshness"] == "offline"

    def test_direct_provider_not_a_bus_runtime(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.studio.phase11_chat_runtime_dispatch_verification import build_chat_runtime_availability
        result = build_chat_runtime_availability(vault)
        dp = result["runtime_by_adapter"]["direct-provider"]
        assert dp["is_bus_runtime"] is False
        assert dp["freshness"] == "n/a"
        assert dp["online"] is None

    def test_hermes_fresh_heartbeat(self, tmp_path):
        vault = _make_vault_with_bus(tmp_path, hermes_age_s=30)
        from runtime.studio.phase11_chat_runtime_dispatch_verification import build_chat_runtime_availability
        result = build_chat_runtime_availability(vault)
        assert result["any_runtime_online"] is True
        hermes = result["runtime_by_adapter"]["hermes"]
        assert hermes["freshness"] == "fresh"
        assert hermes["online"] is True
        assert hermes["pip_class"] == "pip--live"

    def test_hermes_recent_heartbeat(self, tmp_path):
        vault = _make_vault_with_bus(tmp_path, hermes_age_s=300)
        from runtime.studio.phase11_chat_runtime_dispatch_verification import build_chat_runtime_availability
        result = build_chat_runtime_availability(vault)
        hermes = result["runtime_by_adapter"]["hermes"]
        assert hermes["freshness"] == "recent"
        assert hermes["online"] is True
        assert hermes["pip_class"] == "pip--recent"

    def test_hermes_stale_heartbeat(self, tmp_path, monkeypatch):
        import runtime.studio.phase11_chat_runtime_dispatch_verification as _m
        monkeypatch.setattr(_m, "_check_gateway_ports",
            lambda a: {"gateway_port_online": False, "gateway_port_listening": None, "gateway_ports_checked": []})
        vault = _make_vault_with_bus(tmp_path, hermes_age_s=1800)
        from runtime.studio.phase11_chat_runtime_dispatch_verification import build_chat_runtime_availability
        result = build_chat_runtime_availability(vault)
        hermes = result["runtime_by_adapter"]["hermes"]
        assert hermes["freshness"] == "stale"
        assert hermes["online"] is False
        assert hermes["pip_class"] == "pip--stale"

    def test_openclaw_online_hermes_offline(self, tmp_path, monkeypatch):
        import runtime.studio.phase11_chat_runtime_dispatch_verification as _m
        # Only openclaw heartbeat seeded; port probe disabled so hermes stays offline
        monkeypatch.setattr(_m, "_check_gateway_ports",
            lambda a: {"gateway_port_online": False, "gateway_port_listening": None, "gateway_ports_checked": []})
        vault = _make_vault_with_bus(tmp_path, openclaw_age_s=60)
        from runtime.studio.phase11_chat_runtime_dispatch_verification import build_chat_runtime_availability
        result = build_chat_runtime_availability(vault)
        assert result["any_runtime_online"] is True
        assert result["runtime_by_adapter"]["hermes"]["online"] is False
        assert result["runtime_by_adapter"]["openclaw"]["online"] is True

    def test_returns_all_adapter_ids(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.studio.phase11_chat_runtime_dispatch_verification import build_chat_runtime_availability
        result = build_chat_runtime_availability(vault)
        assert set(result["runtime_by_adapter"].keys()) == {"hermes", "openclaw", "claude-code", "direct-provider"}

    def test_read_only_flag(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.studio.phase11_chat_runtime_dispatch_verification import build_chat_runtime_availability
        result = build_chat_runtime_availability(vault)
        assert result["read_only"] is True

    def test_offline_pip_class(self, tmp_path, monkeypatch):
        import runtime.studio.phase11_chat_runtime_dispatch_verification as _m
        monkeypatch.setattr(_m, "_check_gateway_ports",
            lambda a: {"gateway_port_online": False, "gateway_port_listening": None, "gateway_ports_checked": []})
        vault = _make_vault(tmp_path)
        from runtime.studio.phase11_chat_runtime_dispatch_verification import build_chat_runtime_availability
        result = build_chat_runtime_availability(vault)
        assert result["runtime_by_adapter"]["hermes"]["pip_class"] == "pip--offline"

    def test_chat_page_availability_does_not_probe_wsl_processes_by_default(self, tmp_path, monkeypatch):
        import runtime.studio.phase11_chat_runtime_dispatch_verification as _m
        import runtime.studio.runtime_live_status as _live

        monkeypatch.setattr(_m, "_check_gateway_ports",
            lambda a: {"gateway_port_online": False, "gateway_port_listening": None, "gateway_ports_checked": []})

        def fail_if_called(runtime_id):
            raise AssertionError("Chat availability must not spawn wsl.exe process probes on page load")

        monkeypatch.setattr(_live, "_wsl_process_status", fail_if_called)
        vault = _make_vault(tmp_path)
        (vault / "runtime" / "lifecycle").mkdir(parents=True, exist_ok=True)

        from runtime.studio.phase11_chat_runtime_dispatch_verification import build_chat_runtime_availability
        result = build_chat_runtime_availability(vault)
        assert result["ok"] is True
        assert result["runtime_by_adapter"]["hermes"]["wsl_process_probe_enabled"] is False


# ── build_phase11_chat_runtime_dispatch_verification ─────────────────────────

class TestBuildDispatchVerification:
    def test_dispatch_chain_wired(self, tmp_path):
        vault = _make_vault_with_bus(tmp_path)
        from runtime.studio.phase11_chat_runtime_dispatch_verification import (
            build_phase11_chat_runtime_dispatch_verification,
        )
        result = build_phase11_chat_runtime_dispatch_verification(vault)
        assert result["ok"] is True
        assert result["summary"]["dispatch_chain_wired"] is True
        assert result["summary"]["send_message_wired"] is True
        assert result["summary"]["poll_result_wired"] is True

    def test_agent_bus_check(self, tmp_path):
        vault = _make_vault_with_bus(tmp_path)
        from runtime.studio.phase11_chat_runtime_dispatch_verification import (
            build_phase11_chat_runtime_dispatch_verification,
        )
        result = build_phase11_chat_runtime_dispatch_verification(vault)
        assert result["dispatch_checks"]["agent_bus_storage_accessible"] is True

    def test_no_bus_still_wired(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.studio.phase11_chat_runtime_dispatch_verification import (
            build_phase11_chat_runtime_dispatch_verification,
        )
        result = build_phase11_chat_runtime_dispatch_verification(vault)
        assert result["ok"] is True  # import checks pass regardless of bus
        assert result["dispatch_checks"]["agent_bus_storage_accessible"] is False
        assert "agent_bus_storage_not_present" in result["blocked_reasons"]

    def test_no_runtime_online_blocker(self, tmp_path, monkeypatch):
        import runtime.studio.phase11_chat_runtime_dispatch_verification as _m
        monkeypatch.setattr(_m, "_check_gateway_ports",
            lambda a: {"gateway_port_online": False, "gateway_port_listening": None, "gateway_ports_checked": []})
        vault = _make_vault_with_bus(tmp_path)
        from runtime.studio.phase11_chat_runtime_dispatch_verification import (
            build_phase11_chat_runtime_dispatch_verification,
        )
        result = build_phase11_chat_runtime_dispatch_verification(vault)
        assert "no_runtime_daemon_heartbeat_present" in result["blocked_reasons"]

    def test_runtime_online_clears_heartbeat_blocker(self, tmp_path):
        vault = _make_vault_with_bus(tmp_path, hermes_age_s=30)
        from runtime.studio.phase11_chat_runtime_dispatch_verification import (
            build_phase11_chat_runtime_dispatch_verification,
        )
        result = build_phase11_chat_runtime_dispatch_verification(vault)
        assert "no_runtime_daemon_heartbeat_present" not in result["blocked_reasons"]
        assert result["summary"]["any_runtime_online"] is True

    def test_read_only_authority(self, tmp_path):
        vault = _make_vault_with_bus(tmp_path)
        from runtime.studio.phase11_chat_runtime_dispatch_verification import (
            build_phase11_chat_runtime_dispatch_verification,
        )
        result = build_phase11_chat_runtime_dispatch_verification(vault)
        auth = result["authority"]
        assert auth["read_only"] is True
        assert auth["agent_bus_task_write_performed"] is False
        assert auth["approval_consumed"] is False
        assert auth["canonical_mutation_performed"] is False

    def test_status_awaiting_active_runtime(self, tmp_path, monkeypatch):
        import runtime.studio.phase11_chat_runtime_dispatch_verification as _m
        monkeypatch.setattr(_m, "_check_gateway_ports",
            lambda a: {"gateway_port_online": False, "gateway_port_listening": None, "gateway_ports_checked": []})
        vault = _make_vault_with_bus(tmp_path)
        from runtime.studio.phase11_chat_runtime_dispatch_verification import (
            build_phase11_chat_runtime_dispatch_verification,
        )
        result = build_phase11_chat_runtime_dispatch_verification(vault)
        assert "AWAITING ACTIVE RUNTIME" in result["status"]

    def test_status_runtime_online(self, tmp_path):
        vault = _make_vault_with_bus(tmp_path, hermes_age_s=30)
        from runtime.studio.phase11_chat_runtime_dispatch_verification import (
            build_phase11_chat_runtime_dispatch_verification,
        )
        result = build_phase11_chat_runtime_dispatch_verification(vault)
        assert "RUNTIME ONLINE" in result["status"]

    def test_pass_id_and_surface(self, tmp_path):
        vault = _make_vault_with_bus(tmp_path)
        from runtime.studio.phase11_chat_runtime_dispatch_verification import (
            build_phase11_chat_runtime_dispatch_verification,
            PASS_ID,
            SURFACE_ID,
        )
        result = build_phase11_chat_runtime_dispatch_verification(vault)
        assert result["pass"] == PASS_ID
        assert result["surface"] == SURFACE_ID


# ── api.py envelope ───────────────────────────────────────────────────────────

class TestApiGetChatRuntimeAvailability:
    def _api(self, tmp_path):
        vault = _make_vault_with_bus(tmp_path)
        from runtime.studio.shell.api import StudioAPI
        return StudioAPI(str(vault))

    def test_returns_ok_envelope(self, tmp_path):
        api = self._api(tmp_path)
        result = api.get_chat_runtime_availability()
        assert result["ok"] is True
        assert "data" in result

    def test_data_has_runtime_by_adapter(self, tmp_path):
        api = self._api(tmp_path)
        result = api.get_chat_runtime_availability()
        data = result["data"]
        assert "runtime_by_adapter" in data
        assert "hermes" in data["runtime_by_adapter"]

    def test_data_has_any_runtime_online(self, tmp_path):
        api = self._api(tmp_path)
        result = api.get_chat_runtime_availability()
        assert "any_runtime_online" in result["data"]

    def test_data_has_runtimes_list(self, tmp_path):
        api = self._api(tmp_path)
        result = api.get_chat_runtime_availability()
        assert isinstance(result["data"]["runtimes"], list)
        assert len(result["data"]["runtimes"]) == 4  # hermes, openclaw, claude-code, direct-provider

    def test_with_fresh_hermes(self, tmp_path):
        vault = _make_vault_with_bus(tmp_path, hermes_age_s=15)
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(str(vault))
        result = api.get_chat_runtime_availability()
        hermes = result["data"]["runtime_by_adapter"]["hermes"]
        assert hermes["freshness"] == "fresh"
        assert hermes["online"] is True


# ── panel_registry flags ──────────────────────────────────────────────────────

class TestPanelRegistryVerificationFlags:
    def _registry(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry
        import tempfile, os
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            (vault / "runtime" / "agent_bus").mkdir(parents=True)
            return build_native_shell_panel_registry(str(vault))

    def test_verification_surface_ready(self):
        r = self._registry()
        assert r["readiness"]["phase11_chat_runtime_dispatch_verification_surface_ready"] is True

    def test_availability_wired(self):
        r = self._registry()
        assert r["readiness"]["phase11_chat_runtime_availability_wired"] is True

    def test_send_wiring_verified(self):
        r = self._registry()
        assert r["readiness"]["phase11_chat_runtime_send_wiring_verified"] is True

    def test_poll_wiring_verified(self):
        r = self._registry()
        assert r["readiness"]["phase11_chat_runtime_poll_wiring_verified"] is True

    def test_adapter_pip_status_wired(self):
        r = self._registry()
        assert r["readiness"]["phase11_chat_adapter_pip_status_wired"] is True

    def test_offline_banner_wired(self):
        r = self._registry()
        assert r["readiness"]["phase11_chat_offline_banner_wired"] is True

    def test_phase11_next_recommended_pass_advanced(self):
        r = self._registry()
        assert r["readiness"]["phase11_next_recommended_pass"] == "phase11-chat-post-e2e-hardening"

    def test_global_next_recommended_pass_advanced(self):
        r = self._registry()
        assert r["readiness"]["next_recommended_pass"] == "ventureops-operator-readiness-gate"


# ── Frontend HTML ─────────────────────────────────────────────────────────────

class TestFrontendOfflineBanner:
    def _html(self):
        p = Path(__file__).parent / "frontend" / "index.html"
        return p.read_text(encoding="utf-8")

    def test_offline_banner_element_present(self):
        assert 'id="chat-runtime-offline-banner"' in self._html()

    def test_offline_banner_css_class(self):
        assert 'chat-runtime-offline-banner' in self._html()

    def test_adapter_pip_hermes_present(self):
        assert 'id="adapter-pip-hermes"' in self._html()

    def test_adapter_pip_openclaw_present(self):
        assert 'id="adapter-pip-openclaw"' in self._html()

    def test_adapter_pip_claude_code_absent(self):
        # Archon/claude-code is session-scoped, not a persistent 24/7 runtime —
        # no pip rendered in the chat panel for it.
        assert 'id="adapter-pip-claude-code"' not in self._html()


# ── CSS pip classes ───────────────────────────────────────────────────────────

class TestCssPipClasses:
    def _css(self):
        p = Path(__file__).parent / "frontend" / "styles.css"
        return p.read_text(encoding="utf-8")

    def test_pip_live(self):
        assert 'pip--live' in self._css()

    def test_pip_recent(self):
        assert 'pip--recent' in self._css()

    def test_pip_stale(self):
        assert 'pip--stale' in self._css()

    def test_pip_offline(self):
        assert 'pip--offline' in self._css()

    def test_pip_na(self):
        assert 'pip--na' in self._css()

    def test_offline_banner_css(self):
        assert 'chat-runtime-offline-banner' in self._css()
