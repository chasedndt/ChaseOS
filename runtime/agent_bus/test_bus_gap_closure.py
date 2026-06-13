"""
test_bus_gap_closure.py — Small Bus Gap Closure Tests
======================================================

Tests for the three gap-closure items added in the 2026-04-26 small gaps pass:

  1. list_heartbeats() public API on bus.py (was backend-only)
  2. get_bus_mode() public API on bus.py
  3. cmd_agent_bus_mode CLI handler
  4. cmd_agent_bus_heartbeats CLI handler

Run:
    .venv/Scripts/python.exe -m pytest runtime/agent_bus/test_bus_gap_closure.py -q
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.agent_bus.bus import (
    list_heartbeats,
    get_bus_mode,
    init_db,
    upsert_heartbeat,
)
from runtime.cli.agent_bus_commands import cmd_agent_bus_mode, cmd_agent_bus_heartbeats


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _upsert(vault, runtime, status="idle"):
    upsert_heartbeat(
        vault,
        runtime=runtime,
        status=status,
        health="ok",
    )


def _make_vault(tmp_path: Path, *, bus_config: str | None = None) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "CLAUDE.md").write_text("# test vault", encoding="utf-8")
    (vault / "00_HOME").mkdir()
    (vault / "00_HOME" / "Now.md").write_text("# Now", encoding="utf-8")
    bus_dir = vault / "runtime" / "agent_bus"
    bus_dir.mkdir(parents=True)
    if bus_config:
        (bus_dir / "bus_config.yaml").write_text(bus_config, encoding="utf-8")
    else:
        (bus_dir / "bus_config.yaml").write_text("mode: local\n", encoding="utf-8")
    return vault


# ── list_heartbeats() public API ──────────────────────────────────────────────

class TestListHeartbeats:
    def test_returns_empty_list_on_fresh_db(self, tmp_path):
        vault = _make_vault(tmp_path)
        init_db(vault)
        rows = list_heartbeats(vault)
        assert rows == []

    def test_returns_heartbeat_after_upsert(self, tmp_path):
        vault = _make_vault(tmp_path)
        init_db(vault)
        _upsert(vault, "Hermes")
        rows = list_heartbeats(vault)
        assert len(rows) == 1
        assert rows[0]["runtime"] == "Hermes"

    def test_returns_all_runtimes_when_no_filter(self, tmp_path):
        vault = _make_vault(tmp_path)
        init_db(vault)
        for runtime in ("Hermes", "OpenClaw"):
            _upsert(vault, runtime)
        rows = list_heartbeats(vault)
        runtimes = {r["runtime"] for r in rows}
        assert runtimes == {"Hermes", "OpenClaw"}

    def test_runtime_filter_returns_only_matching(self, tmp_path):
        vault = _make_vault(tmp_path)
        init_db(vault)
        for runtime in ("Hermes", "OpenClaw"):
            _upsert(vault, runtime)
        rows = list_heartbeats(vault, runtime="Hermes")
        assert len(rows) == 1
        assert rows[0]["runtime"] == "Hermes"

    def test_runtime_filter_no_match_returns_empty(self, tmp_path):
        vault = _make_vault(tmp_path)
        init_db(vault)
        _upsert(vault, "Hermes")
        rows = list_heartbeats(vault, runtime="UnknownRuntime")
        assert rows == []

    def test_each_row_has_expected_keys(self, tmp_path):
        vault = _make_vault(tmp_path)
        init_db(vault)
        _upsert(vault, "Hermes")
        rows = list_heartbeats(vault)
        row = rows[0]
        assert "runtime" in row
        assert "status" in row

    def test_upsert_updates_existing_heartbeat(self, tmp_path):
        vault = _make_vault(tmp_path)
        init_db(vault)
        _upsert(vault, "Hermes", status="idle")
        _upsert(vault, "Hermes", status="blocked")
        rows = list_heartbeats(vault)
        assert len(rows) == 1
        assert rows[0]["status"] == "blocked"

    def test_vault_root_none_uses_default(self, tmp_path, monkeypatch):
        """list_heartbeats(vault_root=None) should not raise (uses repo root detection)."""
        vault = _make_vault(tmp_path)
        init_db(vault)

        import runtime.agent_bus.bus as bus_module

        original = bus_module._repo_root_from_module

        def fake_root():
            return vault

        monkeypatch.setattr(bus_module, "_repo_root_from_module", fake_root)
        rows = list_heartbeats()
        assert isinstance(rows, list)


# ── get_bus_mode() public API ─────────────────────────────────────────────────

class TestGetBusMode:
    def test_returns_local_for_default_config(self, tmp_path):
        vault = _make_vault(tmp_path, bus_config="mode: local\n")
        mode = get_bus_mode(vault)
        assert mode == "local"

    def test_returns_server_when_configured(self, tmp_path):
        vault = _make_vault(tmp_path, bus_config="mode: server\n")
        mode = get_bus_mode(vault)
        assert mode == "server"

    def test_returns_local_when_config_missing(self, tmp_path):
        vault = _make_vault(tmp_path)
        (vault / "runtime" / "agent_bus" / "bus_config.yaml").unlink()
        mode = get_bus_mode(vault)
        assert mode == "local"

    def test_returns_local_when_config_corrupt(self, tmp_path):
        vault = _make_vault(tmp_path, bus_config=": : bad yaml {{ {{\n")
        mode = get_bus_mode(vault)
        assert mode == "local"

    def test_returns_string_type(self, tmp_path):
        vault = _make_vault(tmp_path)
        mode = get_bus_mode(vault)
        assert isinstance(mode, str)


# ── cmd_agent_bus_mode CLI ────────────────────────────────────────────────────

class TestCmdAgentBusMode:
    def _args(self, vault_root, *, output_json=False):
        return argparse.Namespace(
            vault_root=str(vault_root),
            output_json=output_json,
        )

    def test_returns_zero_exit_code(self, tmp_path, capsys):
        vault = _make_vault(tmp_path)
        result = cmd_agent_bus_mode(self._args(vault))
        assert result == 0

    def test_prints_mode_in_plain_output(self, tmp_path, capsys):
        vault = _make_vault(tmp_path, bus_config="mode: local\n")
        cmd_agent_bus_mode(self._args(vault))
        out = capsys.readouterr().out
        assert "local" in out

    def test_json_output_contains_mode(self, tmp_path, capsys):
        vault = _make_vault(tmp_path, bus_config="mode: local\n")
        cmd_agent_bus_mode(self._args(vault, output_json=True))
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["mode"] == "local"

    def test_json_output_contains_config_path(self, tmp_path, capsys):
        vault = _make_vault(tmp_path)
        cmd_agent_bus_mode(self._args(vault, output_json=True))
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "config_path" in data
        assert "bus_config.yaml" in data["config_path"]

    def test_plain_output_shows_storage_path_for_local(self, tmp_path, capsys):
        vault = _make_vault(tmp_path, bus_config="mode: local\n")
        cmd_agent_bus_mode(self._args(vault))
        out = capsys.readouterr().out
        assert "agent_bus.sqlite" in out

    def test_plain_output_shows_server_note_for_server_mode(self, tmp_path, capsys):
        vault = _make_vault(tmp_path, bus_config="mode: server\n")
        cmd_agent_bus_mode(self._args(vault))
        out = capsys.readouterr().out
        assert "server" in out.lower()


# ── cmd_agent_bus_heartbeats CLI ──────────────────────────────────────────────

class TestCmdAgentBusHeartbeats:
    def _args(self, vault_root, *, runtime=None, output_json=False):
        return argparse.Namespace(
            vault_root=str(vault_root),
            runtime=runtime,
            output_json=output_json,
        )

    def test_returns_zero_exit_code_on_empty(self, tmp_path, capsys):
        vault = _make_vault(tmp_path)
        init_db(vault)
        result = cmd_agent_bus_heartbeats(self._args(vault))
        assert result == 0

    def test_prints_no_records_message_on_empty(self, tmp_path, capsys):
        vault = _make_vault(tmp_path)
        init_db(vault)
        cmd_agent_bus_heartbeats(self._args(vault))
        out = capsys.readouterr().out
        assert "no heartbeat" in out.lower()

    def test_lists_heartbeat_after_upsert(self, tmp_path, capsys):
        vault = _make_vault(tmp_path)
        init_db(vault)
        _upsert(vault, "Hermes")
        cmd_agent_bus_heartbeats(self._args(vault))
        out = capsys.readouterr().out
        assert "Hermes" in out

    def test_json_output_contains_heartbeats_key(self, tmp_path, capsys):
        vault = _make_vault(tmp_path)
        init_db(vault)
        _upsert(vault, "Hermes")
        cmd_agent_bus_heartbeats(self._args(vault, output_json=True))
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "heartbeats" in data
        assert data["count"] == 1

    def test_runtime_filter_passed_through(self, tmp_path, capsys):
        vault = _make_vault(tmp_path)
        init_db(vault)
        for runtime in ("Hermes", "OpenClaw"):
            _upsert(vault, runtime)
        cmd_agent_bus_heartbeats(self._args(vault, runtime="Hermes", output_json=True))
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["count"] == 1
        assert data["heartbeats"][0]["runtime"] == "Hermes"

    def test_runtime_filter_no_match_returns_empty_json(self, tmp_path, capsys):
        vault = _make_vault(tmp_path)
        init_db(vault)
        _upsert(vault, "Hermes")
        cmd_agent_bus_heartbeats(self._args(vault, runtime="Ghost", output_json=True))
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["count"] == 0
        assert data["heartbeats"] == []
