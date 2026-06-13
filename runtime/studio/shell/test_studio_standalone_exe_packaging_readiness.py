"""Tests for studio_standalone_exe_packaging_readiness.py.

Verifies the .exe packaging chain readiness surface — static file checks,
soft import checks, api.py envelope, panel_registry flag, and CLI wiring.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest


# ── helpers ──────────────────────────────────────────────────────────────────

def _build() -> dict[str, Any]:
    from runtime.studio.studio_standalone_exe_packaging_readiness import (
        build_studio_standalone_exe_packaging_readiness,
    )
    return build_studio_standalone_exe_packaging_readiness()


def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "00_HOME").mkdir()
    (vault / "00_HOME" / "Now.md").write_text("# Now\n", encoding="utf-8")
    (vault / "runtime" / "agent_bus").mkdir(parents=True)
    return vault


# ── TestTopLevelShape ─────────────────────────────────────────────────────────

class TestTopLevelShape:
    def test_returns_dict(self):
        assert isinstance(_build(), dict)

    def test_ok_always_true(self):
        """Probe itself always succeeds — ok=True even when packaging_ready=False."""
        assert _build()["ok"] is True

    def test_has_packaging_ready(self):
        result = _build()
        assert "packaging_ready" in result
        assert isinstance(result["packaging_ready"], bool)

    def test_pass_id(self):
        from runtime.studio.studio_standalone_exe_packaging_readiness import PASS_ID
        assert _build()["pass"] == PASS_ID
        assert _build()["pass"] == "studio-standalone-exe-packaging-readiness"

    def test_surface_id(self):
        from runtime.studio.studio_standalone_exe_packaging_readiness import SURFACE_ID
        assert _build()["surface"] == SURFACE_ID

    def test_model_version(self):
        assert _build()["model_version"] == "studio.standalone_exe_packaging_readiness.v1"

    def test_required_top_level_keys(self):
        result = _build()
        for key in ("ok", "packaging_ready", "pass", "surface", "model_version",
                    "generated_at", "status", "hard_checks", "soft_checks",
                    "blocked_reasons", "operator_actions", "details",
                    "next_recommended_pass", "authority"):
            assert key in result, f"missing key: {key}"

    def test_authority_read_only(self):
        auth = _build()["authority"]
        assert auth["read_only"] is True
        assert auth["build_triggered"] is False
        assert auth["files_written"] is False
        assert auth["vault_mutations"] is False


# ── TestHardChecks ────────────────────────────────────────────────────────────

class TestHardChecks:
    def test_hard_checks_keys_present(self):
        hard = _build()["hard_checks"]
        assert "spec_file_present_and_valid" in hard
        assert "build_script_present" in hard
        assert "frontend_assets_present" in hard
        assert "config_meipass_wired" in hard

    def test_spec_file_present(self):
        assert _build()["hard_checks"]["spec_file_present_and_valid"] is True

    def test_build_script_present(self):
        assert _build()["hard_checks"]["build_script_present"] is True

    def test_frontend_assets_present(self):
        assert _build()["hard_checks"]["frontend_assets_present"] is True

    def test_config_meipass_wired(self):
        assert _build()["hard_checks"]["config_meipass_wired"] is True

    def test_all_hard_checks_pass(self):
        hard = _build()["hard_checks"]
        failing = [k for k, v in hard.items() if not v]
        assert failing == [], f"Hard checks failed: {failing}"

    def test_packaging_ready_true_when_hard_checks_pass(self):
        result = _build()
        if all(result["hard_checks"].values()):
            assert result["packaging_ready"] is True

    def test_no_hard_blocked_reasons(self):
        assert _build()["blocked_reasons"] == []


# ── TestSoftChecks ────────────────────────────────────────────────────────────

class TestSoftChecks:
    def test_soft_checks_keys_present(self):
        soft = _build()["soft_checks"]
        assert "pywebview_importable" in soft
        assert "pyinstaller_importable" in soft

    def test_soft_checks_not_hard_blockers(self):
        """Soft check failures must not add to blocked_reasons."""
        result = _build()
        assert result["blocked_reasons"] == []

    def test_soft_check_false_does_not_prevent_packaging_ready(self):
        """packaging_ready can be True even when soft checks fail."""
        result = _build()
        # As long as hard checks pass, packaging_ready should be True
        # regardless of soft check values
        assert result["packaging_ready"] is True


# ── TestDetails ───────────────────────────────────────────────────────────────

class TestDetails:
    def test_spec_detail_structure(self):
        spec = _build()["details"]["spec_file"]
        assert "ok" in spec
        assert "path" in spec
        assert "exists" in spec
        assert "has_analysis_block" in spec
        assert "has_meipass_path_wired" in spec

    def test_spec_detail_values(self):
        spec = _build()["details"]["spec_file"]
        assert spec["exists"] is True
        assert spec["has_analysis_block"] is True
        assert spec["has_meipass_path_wired"] is True
        assert spec["size_bytes"] is not None
        assert spec["size_bytes"] > 0

    def test_build_script_detail_structure(self):
        bs = _build()["details"]["build_script"]
        assert "ok" in bs
        assert "path" in bs
        assert "exists" in bs
        assert "has_pyinstaller_call" in bs

    def test_build_script_detail_values(self):
        bs = _build()["details"]["build_script"]
        assert bs["exists"] is True
        assert bs["has_pyinstaller_call"] is True

    def test_frontend_detail_structure(self):
        fe = _build()["details"]["frontend_assets"]
        assert "index_html_present" in fe
        assert "app_js_present" in fe
        assert "styles_css_present" in fe
        assert "total_asset_count" in fe

    def test_frontend_detail_values(self):
        fe = _build()["details"]["frontend_assets"]
        assert fe["index_html_present"] is True
        assert fe["app_js_present"] is True
        assert fe["styles_css_present"] is True
        assert fe["total_asset_count"] > 0

    def test_config_meipass_detail_structure(self):
        cm = _build()["details"]["config_meipass"]
        assert "config_py_exists" in cm
        assert "meipass_lookup_present" in cm
        assert "studio_frontend_path_wired" in cm

    def test_config_meipass_detail_values(self):
        cm = _build()["details"]["config_meipass"]
        assert cm["config_py_exists"] is True
        assert cm["meipass_lookup_present"] is True
        assert cm["studio_frontend_path_wired"] is True

    def test_pywebview_detail_structure(self):
        pw = _build()["details"]["pywebview"]
        assert "ok" in pw

    def test_pyinstaller_detail_structure(self):
        pi = _build()["details"]["pyinstaller"]
        assert "ok" in pi

    def test_pyinstaller_advisory_note_when_absent(self):
        pi = _build()["details"]["pyinstaller"]
        if not pi["ok"]:
            assert "note" in pi
            # Must not be a hard blocker
            assert pi.get("is_hard_blocker") is not True


# ── TestStatusStrings ─────────────────────────────────────────────────────────

class TestStatusStrings:
    def test_status_is_string(self):
        assert isinstance(_build()["status"], str)
        assert len(_build()["status"]) > 0

    def test_spec_ready_or_build_ready_status(self):
        result = _build()
        # Since all hard checks pass, status must be SPEC READY or BUILD READY
        status = result["status"]
        assert "READY" in status, f"Expected READY in status, got: {status!r}"

    def test_next_recommended_pass(self):
        assert _build()["next_recommended_pass"] == "studio-product-hardening-complete"  # module-level constant unchanged


# ── TestStubChecks ────────────────────────────────────────────────────────────

class TestStubChecks:
    def test_missing_spec_blocks_packaging(self, monkeypatch):
        import runtime.studio.studio_standalone_exe_packaging_readiness as _mod
        monkeypatch.setattr(_mod, "_check_spec_file",
            lambda: {"ok": False, "path": "/missing", "exists": False,
                     "size_bytes": None, "has_analysis_block": False, "has_meipass_path_wired": False})
        result = _build()
        assert result["packaging_ready"] is False
        assert "spec_file_missing_or_invalid" in result["blocked_reasons"]
        assert "NOT READY" in result["status"]

    def test_missing_build_script_blocks_packaging(self, monkeypatch):
        import runtime.studio.studio_standalone_exe_packaging_readiness as _mod
        monkeypatch.setattr(_mod, "_check_build_script",
            lambda: {"ok": False, "path": "/missing", "exists": False,
                     "size_bytes": None, "has_pyinstaller_call": False})
        result = _build()
        assert result["packaging_ready"] is False
        assert "build_script_missing_or_invalid" in result["blocked_reasons"]

    def test_missing_frontend_blocks_packaging(self, monkeypatch):
        import runtime.studio.studio_standalone_exe_packaging_readiness as _mod
        monkeypatch.setattr(_mod, "_check_frontend_assets",
            lambda: {"ok": False, "frontend_dir": "/missing",
                     "index_html_present": False, "app_js_present": False,
                     "styles_css_present": False, "total_asset_count": 0})
        result = _build()
        assert result["packaging_ready"] is False
        assert "frontend_assets_incomplete" in result["blocked_reasons"]

    def test_pywebview_absent_does_not_block(self, monkeypatch):
        import runtime.studio.studio_standalone_exe_packaging_readiness as _mod
        monkeypatch.setattr(_mod, "_check_pywebview_importable",
            lambda: {"ok": False, "error": "No module named 'webview'"})
        result = _build()
        # pywebview is soft — must not block
        assert result["packaging_ready"] is True
        assert "pywebview_not_importable" not in result["blocked_reasons"]
        # But operator_actions should mention it
        actions_text = " ".join(result.get("operator_actions") or [])
        assert "pywebview" in actions_text.lower() or "webview" in actions_text.lower()

    def test_pyinstaller_absent_does_not_block(self, monkeypatch):
        import runtime.studio.studio_standalone_exe_packaging_readiness as _mod
        monkeypatch.setattr(_mod, "_check_pyinstaller_importable",
            lambda: {"ok": False, "error": "No module named 'PyInstaller'",
                     "note": "build_exe.ps1 installs it automatically", "is_hard_blocker": False})
        result = _build()
        assert result["packaging_ready"] is True
        assert "pyinstaller_not_importable" not in result["blocked_reasons"]


# ── TestApiMethod ─────────────────────────────────────────────────────────────

class TestApiMethod:
    def _api(self, tmp_path):
        from runtime.studio.shell.api import StudioAPI
        vault = _make_vault(tmp_path)
        return StudioAPI(str(vault))

    def test_method_exists(self, tmp_path):
        api = self._api(tmp_path)
        assert hasattr(api, "get_studio_standalone_exe_packaging_readiness")
        assert callable(api.get_studio_standalone_exe_packaging_readiness)

    def test_returns_dict(self, tmp_path):
        api = self._api(tmp_path)
        result = api.get_studio_standalone_exe_packaging_readiness()
        assert isinstance(result, dict)

    def test_envelope_ok(self, tmp_path):
        api = self._api(tmp_path)
        result = api.get_studio_standalone_exe_packaging_readiness()
        assert result["ok"] is True

    def test_envelope_surface(self, tmp_path):
        api = self._api(tmp_path)
        result = api.get_studio_standalone_exe_packaging_readiness()
        assert result.get("surface") == "get_studio_standalone_exe_packaging_readiness"

    def test_data_has_packaging_ready(self, tmp_path):
        api = self._api(tmp_path)
        result = api.get_studio_standalone_exe_packaging_readiness()
        assert "packaging_ready" in (result.get("data") or {})


# ── TestPanelRegistry ─────────────────────────────────────────────────────────

class TestPanelRegistry:
    def _registry(self, tmp_path):
        from runtime.studio.shell.panel_registry import build_native_shell_panel_registry
        vault = _make_vault(tmp_path)
        return build_native_shell_panel_registry(vault)

    def test_flag_mounted(self, tmp_path):
        r = self._registry(tmp_path)
        assert r["readiness"].get("studio_standalone_exe_packaging_readiness_mounted") is True

    def test_next_recommended_pass_advanced(self, tmp_path):
        r = self._registry(tmp_path)
        nxt = r["readiness"].get("next_recommended_pass", "")
        assert nxt == "ventureops-operator-readiness-gate"

    def test_prior_flags_still_set(self, tmp_path):
        r = self._registry(tmp_path)
        readiness = r["readiness"]
        assert readiness.get("agent_bus_canonical_writeback_readiness_mounted") is True
        assert readiness.get("phase11_production_operator_dispatch_readiness_mounted") is True


# ── TestCLI ───────────────────────────────────────────────────────────────────

def test_cli_command_importable():
    from runtime.cli.main import cmd_studio_standalone_exe_packaging_readiness
    assert callable(cmd_studio_standalone_exe_packaging_readiness)
