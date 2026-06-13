"""Tests for Phase 11 Production Operator Dispatch Readiness pass.

Covers:
  - build_phase11_production_operator_dispatch_readiness() core structure
  - operator_ready signal with/without daemons live
  - checks dict keys and values
  - authority block (always read-only)
  - daemon_runtimes dict structure
  - blocked_reasons and operator_actions when no daemon live
  - api.py envelope
  - panel_registry flag
  - CLI import contract
  - next_recommended_pass value
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
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


def _make_vault_with_bus(tmp_path: Path, *, hermes_age_s: float | None = None) -> Path:
    """Create a minimal vault with an initialised agent_bus.sqlite."""
    from datetime import datetime, timedelta, timezone
    vault = _make_vault(tmp_path)
    db = vault / "runtime" / "agent_bus" / "agent_bus.sqlite"
    conn = sqlite3.connect(str(db))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS heartbeats "
        "(id INTEGER PRIMARY KEY, runtime TEXT, runtime_instance_id TEXT, "
        "heartbeat_scope TEXT, control_surface TEXT, control_surface_key TEXT, "
        "last_seen TEXT, status TEXT)"
    )
    conn.execute("CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY)")
    if hermes_age_s is not None:
        ts = (datetime.now(timezone.utc) - timedelta(seconds=hermes_age_s)).isoformat().replace("+00:00", "Z")
        conn.execute(
            "INSERT INTO heartbeats (runtime, last_seen, status) VALUES (?, ?, ?)",
            ("Hermes", ts, "active"),
        )
    conn.commit()
    conn.close()
    return vault


def _make_vault_with_pid(tmp_path: Path, runtime_name: str) -> Path:
    """Create a vault with a PID file pointing to the current process (always alive)."""
    vault = _make_vault_with_bus(tmp_path)
    pid_dir = vault / "runtime" / "lifecycle" / "run"
    pid_dir.mkdir(parents=True, exist_ok=True)
    (pid_dir / f"{runtime_name}-chat-daemon.pid").write_text(str(os.getpid()), encoding="utf-8")
    return vault


# ── Core module tests ─────────────────────────────────────────────────────────

class TestBuildPhase11ProductionOperatorDispatchReadiness:
    def _build(self, vault: Path):
        from runtime.studio.phase11_production_operator_dispatch_readiness import (
            build_phase11_production_operator_dispatch_readiness,
        )
        return build_phase11_production_operator_dispatch_readiness(vault)

    def test_returns_dict(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        assert isinstance(result, dict)

    def test_ok_always_true(self, tmp_path):
        """The probe itself always succeeds — ok=True even when operator_ready=False."""
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        assert result["ok"] is True

    def test_has_operator_ready(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        assert "operator_ready" in result
        assert isinstance(result["operator_ready"], bool)

    def test_no_daemon_no_bus_not_ready(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        assert result["operator_ready"] is False

    def test_no_daemon_with_bus_not_ready(self, tmp_path):
        vault = _make_vault_with_bus(tmp_path)
        result = self._build(vault)
        assert result["operator_ready"] is False
        assert "no_daemon_runtime_live" in result["blocked_reasons"]

    def test_live_pid_makes_ready(self, tmp_path):
        vault = _make_vault_with_bus(tmp_path)
        result = self._build(vault)
        # Without PID + heartbeat → not ready (checked above)
        # Now add a live PID
        (tmp_path / "v2").mkdir(exist_ok=True)
        vault2 = _make_vault_with_pid(tmp_path / "v2", "hermes")
        result2 = self._build(vault2)
        assert result2["operator_ready"] is True

    def test_fresh_heartbeat_makes_live(self, tmp_path):
        """A fresh hermes heartbeat (5s old) should count as live."""
        vault = _make_vault_with_bus(tmp_path, hermes_age_s=5)
        result = self._build(vault)
        # Heartbeat alone counts as live (recent < 900s)
        assert result["daemon_runtimes"]["hermes"]["is_live"] is True

    def test_checks_keys_present(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        checks = result["checks"]
        assert "bus_storage_accessible" in checks
        assert "any_daemon_runtime_live" in checks
        assert "send_poll_chain_callable" in checks
        assert "provider_agnostic_routing_confirmed" in checks

    def test_provider_agnostic_always_true(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        assert result["checks"]["provider_agnostic_routing_confirmed"] is True

    def test_daemon_runtimes_has_hermes_and_openclaw(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        assert "hermes" in result["daemon_runtimes"]
        assert "openclaw" in result["daemon_runtimes"]

    def test_daemon_runtime_structure(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        for runtime_name, d in result["daemon_runtimes"].items():
            assert "daemon_process_status" in d
            assert "heartbeat_freshness" in d
            assert "is_live" in d

    def test_blocked_reasons_is_list(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        assert isinstance(result["blocked_reasons"], list)

    def test_operator_actions_is_list(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        assert isinstance(result["operator_actions"], list)

    def test_no_daemon_has_operator_action(self, tmp_path):
        vault = _make_vault_with_bus(tmp_path)
        result = self._build(vault)
        assert len(result["operator_actions"]) > 0

    def test_authority_read_only(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        auth = result["authority"]
        assert auth["read_only"] is True
        assert auth["tasks_created"] is False
        assert auth["approvals_consumed"] is False
        assert auth["vault_mutations"] is False
        assert auth["daemon_started"] is False

    def test_next_recommended_pass(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        assert result["next_recommended_pass"] == "studio-standalone-exe-packaging-readiness"

    def test_pass_id(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        from runtime.studio.phase11_production_operator_dispatch_readiness import PASS_ID
        assert result["pass"] == PASS_ID
        assert result["pass"] == "phase11-production-operator-dispatch-readiness"

    def test_has_status_string(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        assert isinstance(result["status"], str)
        assert len(result["status"]) > 0

    def test_ready_status_production_ready(self, tmp_path):
        vault = _make_vault_with_pid(tmp_path, "hermes")
        result = self._build(vault)
        assert "PRODUCTION READY" in result["status"] or result["operator_ready"] is True

    def test_not_ready_status_awaiting_daemon(self, tmp_path):
        vault = _make_vault_with_bus(tmp_path)
        result = self._build(vault)
        assert "AWAITING" in result["status"] or "NOT READY" in result["status"]

    def test_bus_storage_section_present(self, tmp_path):
        vault = _make_vault_with_bus(tmp_path)
        result = self._build(vault)
        assert "bus_storage" in result
        assert result["bus_storage"]["accessible"] is True

    def test_bus_not_present(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        assert result["bus_storage"]["accessible"] is False

    def test_message_param_accepted(self, tmp_path):
        """message param is accepted for API parity even though unused."""
        vault = _make_vault(tmp_path)
        from runtime.studio.phase11_production_operator_dispatch_readiness import (
            build_phase11_production_operator_dispatch_readiness,
        )
        result = build_phase11_production_operator_dispatch_readiness(vault, message="hello")
        assert result["ok"] is True


# ── api.py envelope ──────────────────────────────────────────────────────────

class TestApiEnvelope:
    def _api(self, tmp_path):
        vault = _make_vault_with_bus(tmp_path)
        from runtime.studio.shell.api import StudioAPI
        return StudioAPI(str(vault))

    def test_returns_ok_envelope(self, tmp_path):
        api = self._api(tmp_path)
        result = api.get_phase11_production_operator_dispatch_readiness()
        assert result["ok"] is True
        assert "data" in result

    def test_data_has_operator_ready(self, tmp_path):
        api = self._api(tmp_path)
        result = api.get_phase11_production_operator_dispatch_readiness()
        assert "operator_ready" in result["data"]

    def test_data_has_checks(self, tmp_path):
        api = self._api(tmp_path)
        result = api.get_phase11_production_operator_dispatch_readiness()
        assert "checks" in result["data"]

    def test_data_has_daemon_runtimes(self, tmp_path):
        api = self._api(tmp_path)
        result = api.get_phase11_production_operator_dispatch_readiness()
        assert "daemon_runtimes" in result["data"]


# ── panel_registry flags ─────────────────────────────────────────────────────

class TestPanelRegistryFlags:
    def _registry(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            (vault / "runtime" / "agent_bus").mkdir(parents=True)
            return build_native_shell_panel_registry(str(vault))

    def test_flag_mounted(self):
        r = self._registry()
        assert r["readiness"]["phase11_production_operator_dispatch_readiness_mounted"] is True

    def test_next_recommended_pass_advanced(self):
        r = self._registry()
        assert r["readiness"]["next_recommended_pass"] == "ventureops-operator-readiness-gate"

    def test_prior_flags_still_set(self):
        r = self._registry()
        assert r["readiness"]["agent_bus_canonical_writeback_readiness_mounted"] is True
        assert r["readiness"]["runtime_bus_response_check_mounted"] is True


# ── CLI import ───────────────────────────────────────────────────────────────

def test_cli_command_importable():
    from runtime.cli.main import cmd_studio_phase11_production_operator_dispatch_readiness
    assert callable(cmd_studio_phase11_production_operator_dispatch_readiness)
