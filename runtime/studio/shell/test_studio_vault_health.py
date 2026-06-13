"""Tests for studio_vault_health.py.

Covers top-level shape, all six lanes, status strings, stub failures,
API envelope, panel registry flag, and CLI wiring.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

VAULT_ROOT = Path(__file__).resolve().parents[3]


def _build(vault: Path | None = None) -> dict[str, Any]:
    from runtime.studio.studio_vault_health import build_studio_vault_health
    return build_studio_vault_health(vault or VAULT_ROOT)


def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "00_HOME").mkdir()
    (vault / "00_HOME" / "Now.md").write_text("# Now\n", encoding="utf-8")
    (vault / "runtime" / "agent_bus").mkdir(parents=True)
    return vault


def _init_bus(vault: Path) -> None:
    from runtime.agent_bus.bus import init_db
    init_db(vault)


# ── TestTopLevelShape ─────────────────────────────────────────────────────────

class TestTopLevelShape:
    def test_returns_dict(self):
        assert isinstance(_build(), dict)

    def test_ok_always_true(self):
        assert _build()["ok"] is True

    def test_has_vault_healthy(self):
        result = _build()
        assert "vault_healthy" in result
        assert isinstance(result["vault_healthy"], bool)

    def test_pass_id(self):
        from runtime.studio.studio_vault_health import PASS_ID
        assert _build()["pass"] == PASS_ID
        assert _build()["pass"] == "studio-vault-health"

    def test_surface_id(self):
        from runtime.studio.studio_vault_health import SURFACE_ID
        assert _build()["surface"] == SURFACE_ID

    def test_model_version(self):
        assert _build()["model_version"] == "studio.studio_vault_health.v1"

    def test_required_top_level_keys(self):
        result = _build()
        for key in ("ok", "vault_healthy", "pass", "surface", "model_version",
                    "generated_at", "vault_root", "status", "lane_results",
                    "failing_lanes", "lanes", "operator_notes",
                    "next_recommended_pass", "authority"):
            assert key in result, f"missing key: {key}"

    def test_authority_read_only(self):
        auth = _build()["authority"]
        assert auth["read_only"] is True
        assert auth["builds_triggered"] is False
        assert auth["daemons_started"] is False
        assert auth["tasks_created"] is False
        assert auth["vault_mutations"] is False

    def test_next_recommended_pass(self):
        assert _build()["next_recommended_pass"] == "studio-live-operator-activation"


# ── TestLaneResults ───────────────────────────────────────────────────────────

class TestLaneResults:
    def test_six_lanes_present(self):
        lr = _build()["lane_results"]
        assert "graph_data_valid" in lr
        assert "bus_storage_healthy" in lr
        assert "dedup_registry_valid" in lr
        assert "memory_files_intact" in lr
        assert "schedule_config_valid" in lr
        assert "audit_logs_present" in lr

    def test_lanes_detail_present(self):
        lanes = _build()["lanes"]
        for name in ("graph_data_valid", "bus_storage_healthy", "dedup_registry_valid",
                     "memory_files_intact", "schedule_config_valid", "audit_logs_present"):
            assert name in lanes
            assert "ok" in lanes[name]

    def test_graph_lane_detail(self):
        lane = _build()["lanes"]["graph_data_valid"]
        assert "scanner_ok" in lane
        assert "node_count" in lane

    def test_bus_lane_detail(self):
        lane = _build()["lanes"]["bus_storage_healthy"]
        assert "wal_mode" in lane
        assert "all_tables_present" in lane
        assert "task_count" in lane

    def test_dedup_lane_detail(self):
        lane = _build()["lanes"]["dedup_registry_valid"]
        assert "exists" in lane

    def test_memory_lane_detail(self):
        lane = _build()["lanes"]["memory_files_intact"]
        assert "readable_profiles" in lane
        assert "runtime_status" in lane

    def test_schedule_lane_detail(self):
        lane = _build()["lanes"]["schedule_config_valid"]
        assert "schedule_count" in lane
        assert "enabled_count" in lane

    def test_audit_lane_detail(self):
        lane = _build()["lanes"]["audit_logs_present"]
        assert "dirs" in lane

    def test_graph_lane_passes_against_real_vault(self):
        lane = _build()["lanes"]["graph_data_valid"]
        assert lane["ok"] is True
        assert lane["scanner_ok"] is True
        assert lane["node_count"] > 0

    def test_bus_lane_passes_against_real_vault(self):
        lane = _build()["lanes"]["bus_storage_healthy"]
        assert lane["ok"] is True
        assert lane["all_tables_present"] is True
        assert lane["wal_mode"] is True

    def test_memory_lane_passes_against_real_vault(self):
        lane = _build()["lanes"]["memory_files_intact"]
        assert lane["ok"] is True
        assert lane["readable_profiles"] >= 1

    def test_schedule_lane_passes_against_real_vault(self):
        lane = _build()["lanes"]["schedule_config_valid"]
        assert lane["ok"] is True
        assert lane["schedule_count"] > 0

    def test_vault_healthy_against_real_vault(self):
        assert _build()["vault_healthy"] is True

    def test_failing_lanes_empty_against_real_vault(self):
        assert _build()["failing_lanes"] == []


# ── TestGraphLane ─────────────────────────────────────────────────────────────

class TestGraphLane:
    def test_node_count_positive(self):
        from runtime.studio.studio_vault_health import _check_graph_data_valid
        result = _check_graph_data_valid(VAULT_ROOT)
        assert result["node_count"] > 0

    def test_edge_count_present(self):
        from runtime.studio.studio_vault_health import _check_graph_data_valid
        result = _check_graph_data_valid(VAULT_ROOT)
        assert "edge_count" in result

    def test_scanner_error_returns_ok_false(self, monkeypatch):
        import runtime.studio.studio_vault_health as _mod
        monkeypatch.setattr(_mod, "_check_graph_data_valid",
            lambda _v: {"ok": False, "scanner_ok": False, "error": "graph_fail"})
        result = _build()
        assert result["vault_healthy"] is False
        assert "graph_data_valid" in result["failing_lanes"]


# ── TestBusLane ───────────────────────────────────────────────────────────────

class TestBusLane:
    def test_bus_wal_mode(self):
        from runtime.studio.studio_vault_health import _check_bus_storage_healthy
        result = _check_bus_storage_healthy(VAULT_ROOT)
        assert result["wal_mode"] is True

    def test_bus_tables_present(self):
        from runtime.studio.studio_vault_health import _check_bus_storage_healthy, _BUS_REQUIRED_TABLES
        result = _check_bus_storage_healthy(VAULT_ROOT)
        assert result["missing_tables"] == []

    def test_missing_bus_returns_ok_false(self, tmp_path):
        from runtime.studio.studio_vault_health import _check_bus_storage_healthy
        vault = tmp_path / "vault"
        vault.mkdir()
        result = _check_bus_storage_healthy(vault)
        assert result["ok"] is False

    def test_bus_failure_blocks_healthy(self, monkeypatch):
        import runtime.studio.studio_vault_health as _mod
        monkeypatch.setattr(_mod, "_check_bus_storage_healthy",
            lambda _v: {"ok": False, "error": "corrupt"})
        result = _build()
        assert result["vault_healthy"] is False
        assert "bus_storage_healthy" in result["failing_lanes"]


# ── TestDedupLane ─────────────────────────────────────────────────────────────

class TestDedupLane:
    def test_missing_registry_is_ok(self, tmp_path):
        """Registry is lazily created — missing is acceptable."""
        from runtime.studio.studio_vault_health import _check_dedup_registry_valid
        vault = tmp_path / "vault"
        vault.mkdir()
        result = _check_dedup_registry_valid(vault)
        assert result["ok"] is True
        assert result["exists"] is False

    def test_valid_registry_is_ok(self, tmp_path):
        from runtime.studio.studio_vault_health import _check_dedup_registry_valid
        vault = tmp_path / "vault"
        vault.mkdir()
        chaseos_dir = vault / ".chaseos"
        chaseos_dir.mkdir()
        (chaseos_dir / "dedup_registry.json").write_text(
            '{"abc123": {"captured_at": "2026-01-01"}}', encoding="utf-8"
        )
        result = _check_dedup_registry_valid(vault)
        assert result["ok"] is True
        assert result["entry_count"] == 1

    def test_corrupt_registry_is_not_ok(self, tmp_path):
        from runtime.studio.studio_vault_health import _check_dedup_registry_valid
        vault = tmp_path / "vault"
        vault.mkdir()
        chaseos_dir = vault / ".chaseos"
        chaseos_dir.mkdir()
        (chaseos_dir / "dedup_registry.json").write_text("NOT JSON{{{{", encoding="utf-8")
        result = _check_dedup_registry_valid(vault)
        assert result["ok"] is False


# ── TestMemoryLane ────────────────────────────────────────────────────────────

class TestMemoryLane:
    def test_readable_profiles_positive(self):
        from runtime.studio.studio_vault_health import _check_memory_files_intact
        result = _check_memory_files_intact(VAULT_ROOT)
        assert result["readable_profiles"] >= 1

    def test_known_runtimes_in_status(self):
        from runtime.studio.studio_vault_health import _check_memory_files_intact
        result = _check_memory_files_intact(VAULT_ROOT)
        status = result.get("runtime_status", {})
        assert len(status) >= 1

    def test_missing_adapters_dir_returns_ok_false(self, tmp_path):
        from runtime.studio.studio_vault_health import _check_memory_files_intact
        vault = tmp_path / "vault"
        vault.mkdir()
        result = _check_memory_files_intact(vault)
        assert result["ok"] is False


# ── TestStatusStrings ─────────────────────────────────────────────────────────

class TestStatusStrings:
    def test_status_is_string(self):
        assert isinstance(_build()["status"], str)

    def test_healthy_status_contains_vault_healthy(self):
        result = _build()
        if result["vault_healthy"]:
            assert "VAULT HEALTHY" in result["status"]

    def test_degraded_status_when_failing(self, monkeypatch):
        import runtime.studio.studio_vault_health as _mod
        monkeypatch.setattr(_mod, "_check_bus_storage_healthy",
            lambda _v: {"ok": False, "error": "corrupt"})
        result = _build()
        assert "VAULT DEGRADED" in result["status"]


# ── TestPanelRegistry ─────────────────────────────────────────────────────────

class TestPanelRegistry:
    def _registry(self, tmp_path):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry
        vault = _make_vault(tmp_path)
        return build_native_shell_panel_registry(vault)

    def test_flag_mounted(self, tmp_path):
        r = self._registry(tmp_path)
        assert r["readiness"].get("studio_vault_health_mounted") is True

    def test_all_prior_flags_still_set(self, tmp_path):
        readiness = self._registry(tmp_path)["readiness"]
        assert readiness.get("studio_live_operator_activation_mounted") is True
        assert readiness.get("studio_product_hardening_complete_mounted") is True
        assert readiness.get("studio_standalone_exe_packaging_readiness_mounted") is True

    def test_next_recommended_pass_unchanged(self, tmp_path):
        r = self._registry(tmp_path)
        assert r["readiness"].get("next_recommended_pass") == "ventureops-operator-readiness-gate"


# ── TestApiMethod ─────────────────────────────────────────────────────────────

class TestApiMethod:
    def test_method_exists(self):
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(str(VAULT_ROOT))
        assert hasattr(api, "get_studio_vault_health")
        assert callable(api.get_studio_vault_health)

    def test_returns_ok_envelope(self):
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_studio_vault_health()
        assert result["ok"] is True
        assert "data" in result

    def test_data_has_vault_healthy(self):
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_studio_vault_health()
        assert "vault_healthy" in (result.get("data") or {})

    def test_data_has_lane_results(self):
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_studio_vault_health()
        assert "lane_results" in (result.get("data") or {})


# ── TestCLI ───────────────────────────────────────────────────────────────────

def test_cli_command_importable():
    from runtime.cli.main import cmd_studio_vault_health
    assert callable(cmd_studio_vault_health)
