"""Tests for Phase 11 Live Daemon Integration Test pass.

Covers:
  - build_phase11_live_daemon_integration_test() core structure
  - integration_ready signal with/without live daemons
  - checks dict keys
  - daemon_runtimes structure
  - authority block (read-only by default, operator_approved changes it)
  - live_probe dry_run behavior
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
    vault = _make_vault_with_bus(tmp_path)
    pid_dir = vault / "runtime" / "lifecycle" / "run"
    pid_dir.mkdir(parents=True, exist_ok=True)
    (pid_dir / f"{runtime_name}-chat-daemon.pid").write_text(str(os.getpid()), encoding="utf-8")
    return vault


# ── Core module tests ─────────────────────────────────────────────────────────

class TestBuildPhase11LiveDaemonIntegrationTest:
    def _build(self, vault: Path, **kwargs):
        from runtime.studio.phase11_live_daemon_integration_test import (
            build_phase11_live_daemon_integration_test,
        )
        return build_phase11_live_daemon_integration_test(vault, **kwargs)

    def test_returns_dict(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        assert isinstance(result, dict)

    def test_ok_always_true(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        assert result["ok"] is True

    def test_has_integration_ready(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        assert "integration_ready" in result
        assert isinstance(result["integration_ready"], bool)

    def test_no_daemon_not_ready(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        assert result["integration_ready"] is False

    def test_checks_keys_present(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        checks = result["checks"]
        assert "hermes_pid_or_heartbeat_live" in checks
        assert "openclaw_pid_or_heartbeat_live" in checks
        assert "bus_storage_accessible" in checks
        assert "send_poll_chain_importable" in checks

    def test_daemon_runtimes_structure(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        dr = result["daemon_runtimes"]
        assert "hermes" in dr
        assert "openclaw" in dr
        for name, d in dr.items():
            assert "is_live" in d
            assert "daemon_process_status" in d
            assert "heartbeat_freshness" in d

    def test_blocked_reasons_is_list(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        assert isinstance(result["blocked_reasons"], list)

    def test_operator_actions_is_list(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        assert isinstance(result["operator_actions"], list)

    def test_no_daemon_has_blocked_reasons(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        blocked = result["blocked_reasons"]
        assert "hermes_not_live" in blocked
        assert "openclaw_not_live" in blocked

    def test_live_probe_default_not_attempted(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        assert result["live_probe"]["probe_attempted"] is False

    def test_live_probe_dry_run_explicitly(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault, operator_approved=False)
        assert result["live_probe"]["probe_attempted"] is False

    def test_authority_read_only_default(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        auth = result["authority"]
        assert auth["read_only"] is True
        assert auth["tasks_created"] is False
        assert auth["approvals_consumed"] is False
        assert auth["vault_mutations"] is False
        assert auth["daemon_started"] is False
        assert auth["operator_approved_probe"] is False

    def test_authority_operator_approved_changes_read_only(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault, operator_approved=True)
        assert result["authority"]["read_only"] is False
        assert result["authority"]["operator_approved_probe"] is True

    def test_next_recommended_pass(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        assert result["next_recommended_pass"] == "ventureops-operator-readiness-gate"

    def test_pass_id(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        from runtime.studio.phase11_live_daemon_integration_test import PASS_ID
        assert result["pass"] == PASS_ID
        assert result["pass"] == "phase11-live-daemon-integration-test"

    def test_has_status_string(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        assert isinstance(result["status"], str)
        assert len(result["status"]) > 0

    def test_awaiting_status_when_no_daemon(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = self._build(vault)
        assert "AWAITING" in result["status"] or "NOT READY" in result["status"]

    def test_fresh_heartbeat_makes_hermes_live(self, tmp_path):
        vault = _make_vault_with_bus(tmp_path, hermes_age_s=5)
        result = self._build(vault)
        assert result["daemon_runtimes"]["hermes"]["is_live"] is True

    def test_live_pid_integration_ready_hermes(self, tmp_path):
        vault = _make_vault_with_pid(tmp_path, "hermes")
        result = self._build(vault)
        assert result["daemon_runtimes"]["hermes"]["is_live"] is True

    def test_message_param_accepted(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.studio.phase11_live_daemon_integration_test import (
            build_phase11_live_daemon_integration_test,
        )
        result = build_phase11_live_daemon_integration_test(vault, message="hello")
        assert result["ok"] is True

    def test_operator_approved_without_bus_skips_probe(self, tmp_path):
        vault = _make_vault(tmp_path)  # no bus sqlite
        result = self._build(vault, operator_approved=True)
        # Bus not accessible → probe skipped, not failed
        probe = result["live_probe"]
        assert probe["probe_attempted"] is False
        assert probe.get("skipped_reason") is not None


# ── api.py envelope ──────────────────────────────────────────────────────────

class TestApiEnvelope:
    def _api(self, tmp_path):
        vault = _make_vault_with_bus(tmp_path)
        from runtime.studio.shell.api import StudioAPI
        return StudioAPI(str(vault))

    def test_returns_ok_envelope(self, tmp_path):
        api = self._api(tmp_path)
        result = api.get_phase11_live_daemon_integration_test()
        assert result["ok"] is True
        assert "data" in result

    def test_data_has_integration_ready(self, tmp_path):
        api = self._api(tmp_path)
        result = api.get_phase11_live_daemon_integration_test()
        assert "integration_ready" in result["data"]

    def test_data_has_checks(self, tmp_path):
        api = self._api(tmp_path)
        result = api.get_phase11_live_daemon_integration_test()
        assert "checks" in result["data"]

    def test_data_has_daemon_runtimes(self, tmp_path):
        api = self._api(tmp_path)
        result = api.get_phase11_live_daemon_integration_test()
        assert "daemon_runtimes" in result["data"]


# ── panel_registry flag ───────────────────────────────────────────────────────

class TestPanelRegistryFlags:
    def _registry(self):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            (vault / "runtime" / "agent_bus").mkdir(parents=True)
            return build_native_shell_panel_registry(str(vault))

    def test_flag_mounted(self):
        r = self._registry()
        assert r["readiness"]["phase11_live_daemon_integration_test_mounted"] is True

    def test_prior_flags_still_set(self):
        r = self._registry()
        assert r["readiness"]["phase11_production_operator_dispatch_readiness_mounted"] is True
        assert r["readiness"]["studio_standalone_exe_packaging_readiness_mounted"] is True


# ── CLI import ───────────────────────────────────────────────────────────────

def test_cli_command_importable():
    from runtime.cli.main import cmd_studio_phase11_live_daemon_integration_test
    assert callable(cmd_studio_phase11_live_daemon_integration_test)
