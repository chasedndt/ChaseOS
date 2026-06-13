"""Tests for studio_product_hardening_complete.py.

Covers the six-lane hardening aggregator, all-lanes-ok signal,
api.py envelope, panel_registry flag, and CLI wiring.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pytest

VAULT_ROOT = Path(__file__).resolve().parents[3]


def _build(vault: Path | None = None) -> dict[str, Any]:
    from runtime.studio.studio_product_hardening_complete import (
        build_studio_product_hardening_complete,
    )
    return build_studio_product_hardening_complete(vault or VAULT_ROOT)


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

    def test_has_all_hardening_passes_complete(self):
        result = _build()
        assert "all_hardening_passes_complete" in result
        assert isinstance(result["all_hardening_passes_complete"], bool)

    def test_pass_id(self):
        from runtime.studio.studio_product_hardening_complete import PASS_ID
        assert _build()["pass"] == PASS_ID
        assert _build()["pass"] == "studio-product-hardening-complete"

    def test_surface_id(self):
        from runtime.studio.studio_product_hardening_complete import SURFACE_ID
        assert _build()["surface"] == SURFACE_ID

    def test_model_version(self):
        assert _build()["model_version"] == "studio.studio_product_hardening_complete.v1"

    def test_required_top_level_keys(self):
        result = _build()
        for key in ("ok", "all_hardening_passes_complete", "pass", "surface",
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
        assert "panel_registry" in lr
        assert "phase10_packaging" in lr
        assert "phase10_product_hardening" in lr
        assert "agent_bus_canonical_writeback" in lr
        assert "production_operator_dispatch_chain" in lr
        assert "standalone_exe_packaging" in lr

    def test_all_lanes_pass_against_real_vault(self):
        lr = _build()["lane_results"]
        failing = [k for k, v in lr.items() if not v]
        assert failing == [], f"These hardening lanes are failing: {failing}"

    def test_all_hardening_complete_true(self):
        assert _build()["all_hardening_passes_complete"] is True

    def test_failing_lanes_empty(self):
        assert _build()["failing_lanes"] == []

    def test_lanes_detail_present(self):
        lanes = _build()["lanes"]
        for name in ("panel_registry", "phase10_packaging", "phase10_product_hardening",
                     "agent_bus_canonical_writeback", "production_operator_dispatch_chain",
                     "standalone_exe_packaging"):
            assert name in lanes
            assert "ok" in lanes[name]

    def test_panel_registry_lane_detail(self):
        lane = _build()["lanes"]["panel_registry"]
        assert lane["ok"] is True
        assert lane.get("panel_registry_ready") is True
        assert lane.get("phase11_flags_ok") is True
        assert lane.get("missing_phase11_flags") == []

    def test_exe_packaging_lane_detail(self):
        lane = _build()["lanes"]["standalone_exe_packaging"]
        assert lane["ok"] is True
        assert lane.get("packaging_ready") is True

    def test_dispatch_chain_lane_detail(self):
        lane = _build()["lanes"]["production_operator_dispatch_chain"]
        assert lane["ok"] is True
        assert lane.get("chain_ready") is True

    def test_agent_bus_writeback_lane_detail(self):
        lane = _build()["lanes"]["agent_bus_canonical_writeback"]
        assert lane["ok"] is True
        assert lane.get("writeback_lane_ok") is True


# ── TestStatusStrings ─────────────────────────────────────────────────────────

class TestStatusStrings:
    def test_status_is_string(self):
        assert isinstance(_build()["status"], str)

    def test_hardening_complete_status(self):
        result = _build()
        if result["all_hardening_passes_complete"]:
            assert "HARDENING COMPLETE" in result["status"]

    def test_next_recommended_pass(self):
        assert _build()["next_recommended_pass"] == "studio-live-operator-activation"


# ── TestStubFailures ──────────────────────────────────────────────────────────

class TestStubFailures:
    def test_failing_registry_lane_blocks_complete(self, monkeypatch):
        import runtime.studio.studio_product_hardening_complete as _mod
        monkeypatch.setattr(_mod, "_check_panel_registry",
            lambda _v: {"ok": False, "error": "registry check failed"})
        result = _build()
        assert result["all_hardening_passes_complete"] is False
        assert "panel_registry" in result["failing_lanes"]
        assert "INCOMPLETE" in result["status"]

    def test_failing_exe_lane_blocks_complete(self, monkeypatch):
        import runtime.studio.studio_product_hardening_complete as _mod
        monkeypatch.setattr(_mod, "_check_exe_packaging",
            lambda: {"ok": False, "packaging_ready": False, "error": "spec missing"})
        result = _build()
        assert result["all_hardening_passes_complete"] is False
        assert "standalone_exe_packaging" in result["failing_lanes"]

    def test_failing_hardening_lane_blocks_complete(self, monkeypatch):
        import runtime.studio.studio_product_hardening_complete as _mod
        monkeypatch.setattr(_mod, "_check_phase10_product_hardening",
            lambda _v: {"ok": False, "status": "blocked", "error": "missing evidence"})
        result = _build()
        assert result["all_hardening_passes_complete"] is False

    def test_operator_note_when_no_daemon(self, monkeypatch):
        import runtime.studio.studio_product_hardening_complete as _mod
        monkeypatch.setattr(_mod, "_check_production_dispatch",
            lambda _v: {"ok": True, "chain_ready": True, "any_daemon_live": False,
                        "operator_ready": False, "status": "AWAITING DAEMON START"})
        result = _build()
        notes = " ".join(result.get("operator_notes") or [])
        assert "daemon" in notes.lower() or "hermes" in notes.lower() or "openclaw" in notes.lower()


# ── TestPanelRegistry ─────────────────────────────────────────────────────────

class TestPanelRegistry:
    def _registry(self, tmp_path):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry
        vault = _make_vault(tmp_path)
        return build_native_shell_panel_registry(vault)

    def test_flag_mounted(self, tmp_path):
        r = self._registry(tmp_path)
        assert r["readiness"].get("studio_product_hardening_complete_mounted") is True

    def test_next_recommended_pass_advanced(self, tmp_path):
        r = self._registry(tmp_path)
        assert r["readiness"].get("next_recommended_pass") == "ventureops-operator-readiness-gate"

    def test_all_prior_flags_still_set(self, tmp_path):
        r = self._registry(tmp_path)
        readiness = r["readiness"]
        assert readiness.get("agent_bus_canonical_writeback_readiness_mounted") is True
        assert readiness.get("phase11_production_operator_dispatch_readiness_mounted") is True
        assert readiness.get("studio_standalone_exe_packaging_readiness_mounted") is True


# ── TestApiMethod ─────────────────────────────────────────────────────────────

class TestApiMethod:
    def test_method_exists(self):
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(str(VAULT_ROOT))
        assert hasattr(api, "get_studio_product_hardening_complete")
        assert callable(api.get_studio_product_hardening_complete)

    def test_returns_ok_envelope(self):
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_studio_product_hardening_complete()
        assert result["ok"] is True
        assert "data" in result

    def test_data_has_all_hardening_passes_complete(self):
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_studio_product_hardening_complete()
        assert "all_hardening_passes_complete" in (result.get("data") or {})

    def test_data_has_lane_results(self):
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(str(VAULT_ROOT))
        result = api.get_studio_product_hardening_complete()
        assert "lane_results" in (result.get("data") or {})


# ── TestCLI ───────────────────────────────────────────────────────────────────

def test_cli_command_importable():
    from runtime.cli.main import cmd_studio_product_hardening_complete
    assert callable(cmd_studio_product_hardening_complete)
