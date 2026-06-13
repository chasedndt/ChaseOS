"""Tests for studio_live_operator_activation.py.

Covers top-level shape, all six lanes, status strings, stub failures,
API envelope, panel registry flag, and CLI wiring.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pytest

VAULT_ROOT = Path(__file__).resolve().parents[3]


def _build(vault: Path | None = None) -> dict[str, Any]:
    from runtime.studio.studio_live_operator_activation import (
        build_studio_live_operator_activation,
    )
    return build_studio_live_operator_activation(vault or VAULT_ROOT)


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
        """Probe itself always succeeds."""
        assert _build()["ok"] is True

    def test_has_operator_activated(self):
        result = _build()
        assert "operator_activated" in result
        assert isinstance(result["operator_activated"], bool)

    def test_has_fully_live(self):
        result = _build()
        assert "fully_live" in result
        assert isinstance(result["fully_live"], bool)

    def test_pass_id(self):
        from runtime.studio.studio_live_operator_activation import PASS_ID
        assert _build()["pass"] == PASS_ID
        assert _build()["pass"] == "studio-live-operator-activation"

    def test_surface_id(self):
        from runtime.studio.studio_live_operator_activation import SURFACE_ID
        assert _build()["surface"] == SURFACE_ID

    def test_model_version(self):
        assert _build()["model_version"] == "studio.studio_live_operator_activation.v1"

    def test_required_top_level_keys(self):
        result = _build()
        for key in ("ok", "operator_activated", "fully_live", "pass", "surface",
                    "model_version", "generated_at", "vault_root", "status",
                    "lane_results", "failing_lanes", "lanes",
                    "operator_notes", "next_recommended_pass", "authority"):
            assert key in result, f"missing key: {key}"

    def test_authority_read_only(self):
        auth = _build()["authority"]
        assert auth["read_only"] is True
        assert auth["builds_triggered"] is False
        assert auth["daemons_started"] is False
        assert auth["tasks_created"] is False
        assert auth["vault_mutations"] is False


# ── TestLaneResults ───────────────────────────────────────────────────────────

class TestLaneResults:
    def test_six_lanes_present(self):
        lr = _build()["lane_results"]
        assert "shell_launch_ready" in lr
        assert "dispatch_chain" in lr
        assert "daemon_liveness" in lr
        assert "schedules_configured" in lr
        assert "recent_operator_activity" in lr
        assert "bus_traffic" in lr

    def test_lanes_detail_present(self):
        lanes = _build()["lanes"]
        for name in ("shell_launch_ready", "dispatch_chain", "daemon_liveness",
                     "schedules_configured", "recent_operator_activity", "bus_traffic"):
            assert name in lanes
            assert "ok" in lanes[name]

    def test_shell_launch_lane_detail(self):
        lane = _build()["lanes"]["shell_launch_ready"]
        assert "config_importable" in lane
        assert "api_importable" in lane
        assert "frontend_assets_present" in lane

    def test_dispatch_chain_lane_detail(self):
        lane = _build()["lanes"]["dispatch_chain"]
        assert "bus_storage_accessible" in lane
        assert "send_poll_importable" in lane
        assert "provider_agnostic_confirmed" in lane

    def test_daemon_liveness_lane_detail(self):
        lane = _build()["lanes"]["daemon_liveness"]
        assert "any_live" in lane
        assert "live_runtimes" in lane
        assert "runtime_states" in lane

    def test_schedules_lane_detail(self):
        lane = _build()["lanes"]["schedules_configured"]
        assert "core_schedules_enabled" in lane
        assert "enabled_schedule_count" in lane

    def test_activity_lane_detail(self):
        lane = _build()["lanes"]["recent_operator_activity"]
        assert "any_recent_activity" in lane
        assert "recent_operator_briefs" in lane
        assert "window_days" in lane

    def test_bus_traffic_lane_detail(self):
        lane = _build()["lanes"]["bus_traffic"]
        assert "recent_task_count" in lane
        assert "window_days" in lane

    def test_shell_launch_ready_against_real_vault(self):
        lane = _build()["lanes"]["shell_launch_ready"]
        assert lane["ok"] is True
        assert lane["config_importable"] is True
        assert lane["api_importable"] is True
        assert lane["frontend_assets_present"] is True

    def test_dispatch_chain_against_real_vault(self):
        lane = _build()["lanes"]["dispatch_chain"]
        assert lane["ok"] is True
        assert lane["bus_storage_accessible"] is True
        assert lane["send_poll_importable"] is True

    def test_schedules_against_real_vault(self):
        """operator_today and operator_close_day are enabled."""
        lane = _build()["lanes"]["schedules_configured"]
        assert lane["ok"] is True
        assert lane["core_schedules_enabled"] is True
        assert lane["enabled_schedule_count"] >= 1

    def test_operator_activated_against_real_vault(self):
        """Static chain (shell + dispatch) is always wired."""
        assert _build()["operator_activated"] is True


# ── TestStatusStrings ─────────────────────────────────────────────────────────

class TestStatusStrings:
    def test_status_is_string(self):
        assert isinstance(_build()["status"], str)

    def test_activated_or_fully_live_status(self):
        result = _build()
        if result["fully_live"]:
            assert "FULLY LIVE" in result["status"] or "ACTIVATED" in result["status"]
        elif result["operator_activated"]:
            assert "ACTIVATED" in result["status"]
        else:
            assert "NOT ACTIVATED" in result["status"]

    def test_next_recommended_pass_loops(self):
        assert _build()["next_recommended_pass"] == "studio-live-operator-activation"


# ── TestStubFailures ──────────────────────────────────────────────────────────

class TestStubFailures:
    def test_failing_shell_blocks_activated(self, monkeypatch):
        import runtime.studio.studio_live_operator_activation as _mod
        monkeypatch.setattr(_mod, "_check_shell_launch_ready",
            lambda _v: {"ok": False, "error": "config missing"})
        result = _build()
        assert result["operator_activated"] is False
        assert "shell_launch_ready" in result["failing_lanes"]
        assert "NOT ACTIVATED" in result["status"]

    def test_failing_dispatch_blocks_activated(self, monkeypatch):
        import runtime.studio.studio_live_operator_activation as _mod
        monkeypatch.setattr(_mod, "_check_dispatch_chain",
            lambda _v: {"ok": False, "bus_storage_accessible": False})
        result = _build()
        assert result["operator_activated"] is False
        assert "dispatch_chain" in result["failing_lanes"]

    def test_failing_daemon_does_not_block_activated(self, monkeypatch):
        """Daemon liveness failure makes fully_live=False but not operator_activated=False."""
        import runtime.studio.studio_live_operator_activation as _mod
        monkeypatch.setattr(_mod, "_check_daemon_liveness",
            lambda _v: {"ok": False, "any_live": False, "live_runtimes": []})
        result = _build()
        assert result["operator_activated"] is True  # shell + dispatch still ok
        assert result["fully_live"] is False
        assert "daemon_liveness" in result["failing_lanes"]

    def test_operator_note_when_daemon_not_live(self, monkeypatch):
        import runtime.studio.studio_live_operator_activation as _mod
        monkeypatch.setattr(_mod, "_check_daemon_liveness",
            lambda _v: {"ok": False, "any_live": False, "live_runtimes": []})
        result = _build()
        notes = " ".join(result.get("operator_notes") or [])
        assert "daemon" in notes.lower() or "hermes" in notes.lower() or "openclaw" in notes.lower()

    def test_operator_note_when_exe_not_built(self, monkeypatch):
        import runtime.studio.studio_live_operator_activation as _mod
        orig = _mod._check_shell_launch_ready
        def _patched(v):
            r = orig(v)
            r["exe_built"] = False
            return r
        monkeypatch.setattr(_mod, "_check_shell_launch_ready", _patched)
        result = _build()
        notes = " ".join(result.get("operator_notes") or [])
        assert "exe" in notes.lower() or "build_exe" in notes.lower()

    def test_failing_all_lanes_not_activated(self, monkeypatch):
        import runtime.studio.studio_live_operator_activation as _mod
        monkeypatch.setattr(_mod, "_check_shell_launch_ready",
            lambda _v: {"ok": False, "error": "no shell"})
        monkeypatch.setattr(_mod, "_check_dispatch_chain",
            lambda _v: {"ok": False, "error": "no bus"})
        result = _build()
        assert result["operator_activated"] is False
        assert result["fully_live"] is False


# ── TestShellLaneLive ─────────────────────────────────────────────────────────

class TestShellLaneLive:
    def test_config_importable(self):
        from runtime.studio.shell import config  # noqa: F401

    def test_api_importable(self):
        from runtime.studio.shell.api import StudioAPI  # noqa: F401

    def test_frontend_files_exist(self):
        from pathlib import Path
        shell_dir = Path(__file__).resolve().parent
        assert (shell_dir / "frontend" / "index.html").exists()
        assert (shell_dir / "frontend" / "app.js").exists()
        assert (shell_dir / "frontend" / "styles.css").exists()


# ── TestPanelRegistry ─────────────────────────────────────────────────────────

class TestPanelRegistry:
    def _registry(self, tmp_path):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry
        vault = _make_vault(tmp_path)
        return build_native_shell_panel_registry(vault)

    def test_flag_mounted(self, tmp_path):
        r = self._registry(tmp_path)
        assert r["readiness"].get("studio_live_operator_activation_mounted") is True

    def test_all_prior_flags_still_set(self, tmp_path):
        readiness = self._registry(tmp_path)["readiness"]
        assert readiness.get("studio_product_hardening_complete_mounted") is True
        assert readiness.get("studio_standalone_exe_packaging_readiness_mounted") is True
        assert readiness.get("phase11_production_operator_dispatch_readiness_mounted") is True
        assert readiness.get("agent_bus_canonical_writeback_readiness_mounted") is True

    def test_next_recommended_pass_still_self(self, tmp_path):
        r = self._registry(tmp_path)
        assert r["readiness"].get("next_recommended_pass") == "ventureops-operator-readiness-gate"


# ── TestApiMethod ─────────────────────────────────────────────────────────────

class TestApiMethod:
    def test_method_exists(self):
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(str(VAULT_ROOT))
        assert hasattr(api, "get_studio_live_operator_activation")
        assert callable(api.get_studio_live_operator_activation)

    def test_returns_ok_envelope(self):
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_studio_live_operator_activation()
        assert result["ok"] is True
        assert "data" in result

    def test_data_has_operator_activated(self):
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_studio_live_operator_activation()
        assert "operator_activated" in (result.get("data") or {})

    def test_data_has_lane_results(self):
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_studio_live_operator_activation()
        assert "lane_results" in (result.get("data") or {})


# ── TestCLI ───────────────────────────────────────────────────────────────────

def test_cli_command_importable():
    from runtime.cli.main import cmd_studio_live_operator_activation
    assert callable(cmd_studio_live_operator_activation)
