"""Tests for runtime.studio.shell.workspace_import_flow — Pass 10E."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from runtime.studio.shell.workspace_import_flow import (
    _detect_mode,
    _missing_dirs,
    _missing_files,
    _upgrade_recommendations,
    infer_compatibility_types,
    scan_folder_for_import,
    get_bootstrap_wizard_plan,
    _CHASEOS_DIRS,
    _CHASEOS_FILES,
)


# ── _detect_mode ──────────────────────────────────────────────────────────────

class TestDetectMode:
    def test_missing_folder(self, tmp_path):
        assert _detect_mode(tmp_path / "nonexistent") == "invalid_missing"

    def test_file_not_dir(self, tmp_path):
        f = tmp_path / "file.md"
        f.write_text("x")
        assert _detect_mode(f) == "invalid_not_directory"

    def test_empty_folder(self, tmp_path):
        assert _detect_mode(tmp_path) == "empty_or_unknown"

    def test_chaseos_native(self, tmp_path):
        for d in _CHASEOS_DIRS:
            (tmp_path / d).mkdir()
        for f in _CHASEOS_FILES:
            p = tmp_path / f
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("x")
        assert _detect_mode(tmp_path) == "chaseos_native"

    def test_chaseos_partial_dirs(self, tmp_path):
        for d in _CHASEOS_DIRS[:4]:
            (tmp_path / d).mkdir()
        assert _detect_mode(tmp_path) == "chaseos_partial"

    def test_chaseos_partial_files(self, tmp_path):
        for f in _CHASEOS_FILES[:3]:
            p = tmp_path / f
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("x")
        assert _detect_mode(tmp_path) == "chaseos_partial"

    def test_obsidian_vault(self, tmp_path):
        (tmp_path / ".obsidian").mkdir()
        assert _detect_mode(tmp_path) == "general_markdown"

    def test_markdown_files_present(self, tmp_path):
        (tmp_path / "note.md").write_text("hello")
        assert _detect_mode(tmp_path) == "general_markdown"


# ── _missing_dirs / _missing_files ───────────────────────────────────────────

class TestMissingShapeHelpers:
    def test_all_dirs_present(self, tmp_path):
        for d in _CHASEOS_DIRS:
            (tmp_path / d).mkdir()
        assert _missing_dirs(tmp_path) == []

    def test_some_dirs_missing(self, tmp_path):
        (tmp_path / "00_HOME").mkdir()
        missing = _missing_dirs(tmp_path)
        assert "00_HOME" not in missing
        assert "01_PROJECTS" in missing

    def test_all_files_present(self, tmp_path):
        for f in _CHASEOS_FILES:
            p = tmp_path / f
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("x")
        assert _missing_files(tmp_path) == []

    def test_some_files_missing(self, tmp_path):
        (tmp_path / "README.md").write_text("x")
        missing = _missing_files(tmp_path)
        assert "README.md" not in missing
        assert "PROJECT_FOUNDATION.md" in missing


# ── _upgrade_recommendations ─────────────────────────────────────────────────

class TestUpgradeRecommendations:
    def test_native_has_no_recs(self, tmp_path):
        for d in _CHASEOS_DIRS:
            (tmp_path / d).mkdir()
        for f in _CHASEOS_FILES:
            p = tmp_path / f
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("x")
        assert _upgrade_recommendations(tmp_path, "chaseos_native") == []

    def test_empty_folder_has_recs(self, tmp_path):
        recs = _upgrade_recommendations(tmp_path, "empty_or_unknown")
        assert len(recs) > 0

    def test_missing_claude_md_rec(self, tmp_path):
        recs = _upgrade_recommendations(tmp_path, "general_markdown")
        ids = [r["id"] for r in recs]
        assert "add-claude-md" in ids

    def test_missing_assistant_contract_rec(self, tmp_path):
        recs = _upgrade_recommendations(tmp_path, "general_markdown")
        ids = [r["id"] for r in recs]
        assert "add-assistant-contract" in ids

    def test_recs_have_required_keys(self, tmp_path):
        recs = _upgrade_recommendations(tmp_path, "general_markdown")
        for r in recs:
            assert "id" in r
            assert "title" in r
            assert "items" in r
            assert "priority" in r


# ── infer_compatibility_types ─────────────────────────────────────────────────

class TestInferCompatibilityTypes:
    def test_missing_folder(self, tmp_path):
        result = infer_compatibility_types(tmp_path / "nonexistent")
        assert result["ok"] is False

    def test_empty_folder(self, tmp_path):
        result = infer_compatibility_types(tmp_path)
        assert result["ok"] is True
        assert result["total_scanned"] == 0
        assert result["nodes"] == []

    def test_markdown_note_inferred(self, tmp_path):
        (tmp_path / "note.md").write_text("# Hello")
        result = infer_compatibility_types(tmp_path)
        assert result["total_scanned"] == 1
        assert result["nodes"][0]["node_type"] == "markdown_note"

    def test_project_doc_inferred(self, tmp_path):
        proj = tmp_path / "01_PROJECTS"
        proj.mkdir()
        (proj / "Foo-OS.md").write_text("x")
        result = infer_compatibility_types(tmp_path)
        assert any(n["node_type"] == "project_doc" for n in result["nodes"])

    def test_build_log_inferred(self, tmp_path):
        logs = tmp_path / "07_LOGS" / "Build-Logs"
        logs.mkdir(parents=True)
        (logs / "2026-01-01-foo.md").write_text("x")
        result = infer_compatibility_types(tmp_path)
        assert any(n["node_type"] == "build_log" for n in result["nodes"])

    def test_home_doc_inferred(self, tmp_path):
        home = tmp_path / "00_HOME"
        home.mkdir()
        (home / "Now.md").write_text("x")
        result = infer_compatibility_types(tmp_path)
        assert any(n["node_type"] == "home_doc" for n in result["nodes"])

    def test_agent_doc_inferred(self, tmp_path):
        agents = tmp_path / "06_AGENTS"
        agents.mkdir()
        (agents / "Vault-Map.md").write_text("x")
        result = infer_compatibility_types(tmp_path)
        assert any(n["node_type"] == "agent_control_doc" for n in result["nodes"])

    def test_type_counts_returned(self, tmp_path):
        (tmp_path / "a.md").write_text("x")
        (tmp_path / "b.md").write_text("x")
        result = infer_compatibility_types(tmp_path)
        assert isinstance(result["type_counts"], dict)
        assert sum(result["type_counts"].values()) == 2

    def test_dominant_type_returned(self, tmp_path):
        (tmp_path / "a.md").write_text("x")
        result = infer_compatibility_types(tmp_path)
        assert result["dominant_type"] is not None

    def test_ignored_dirs_skipped(self, tmp_path):
        git = tmp_path / ".git"
        git.mkdir()
        (git / "notes.md").write_text("x")
        result = infer_compatibility_types(tmp_path)
        assert result["total_scanned"] == 0


# ── scan_folder_for_import ────────────────────────────────────────────────────

class TestScanFolderForImport:
    def test_missing_folder(self, tmp_path):
        result = scan_folder_for_import(tmp_path / "nonexistent")
        assert result["ok"] is False
        assert result["mode"] == "invalid_missing"

    def test_empty_folder(self, tmp_path):
        result = scan_folder_for_import(tmp_path)
        assert "mode" in result
        assert "shape" in result
        assert "signals" in result
        assert "upgrade_recommendations" in result

    def test_native_vault_detected(self, tmp_path):
        for d in _CHASEOS_DIRS:
            (tmp_path / d).mkdir()
        for f in _CHASEOS_FILES:
            p = tmp_path / f
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("x")
        result = scan_folder_for_import(tmp_path)
        assert result["ok"] is True
        assert result["mode"] == "chaseos_native"
        assert result["mode_label"] == "ChaseOS Native"

    def test_relaunch_command_present_for_valid_folder(self, tmp_path):
        (tmp_path / "note.md").write_text("x")
        result = scan_folder_for_import(tmp_path)
        assert "chaseos studio shell" in (result["relaunch_command"] or "")

    def test_no_relaunch_for_invalid(self, tmp_path):
        result = scan_folder_for_import(tmp_path / "missing")
        assert result["relaunch_command"] is None

    def test_compat_analysis_for_general_markdown(self, tmp_path):
        (tmp_path / "note.md").write_text("x")
        result = scan_folder_for_import(tmp_path)
        assert result.get("compatibility_analysis") is not None

    def test_no_compat_analysis_for_native(self, tmp_path):
        for d in _CHASEOS_DIRS:
            (tmp_path / d).mkdir()
        for f in _CHASEOS_FILES:
            p = tmp_path / f
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("x")
        result = scan_folder_for_import(tmp_path)
        assert result.get("compatibility_analysis") is None

    def test_result_has_all_required_keys(self, tmp_path):
        result = scan_folder_for_import(tmp_path)
        for key in ("ok", "folder", "mode", "mode_label", "shape", "signals",
                    "upgrade_recommendations", "warnings"):
            assert key in result, f"missing key: {key}"

    def test_shape_keys_present(self, tmp_path):
        result = scan_folder_for_import(tmp_path)
        shape = result["shape"]
        for key in ("present_dirs", "missing_dirs", "present_files", "missing_files"):
            assert key in shape


# ── get_bootstrap_wizard_plan ─────────────────────────────────────────────────

class TestGetBootstrapWizardPlan:
    def test_returns_ok(self, tmp_path):
        result = get_bootstrap_wizard_plan(tmp_path)
        assert result["ok"] is True

    def test_steps_returned(self, tmp_path):
        result = get_bootstrap_wizard_plan(tmp_path)
        assert isinstance(result["steps"], list)
        assert len(result["steps"]) > 0

    def test_steps_have_required_keys(self, tmp_path):
        result = get_bootstrap_wizard_plan(tmp_path)
        for step in result["steps"]:
            assert "step" in step
            assert "id" in step
            assert "title" in step
            assert "description" in step
            assert "writes" in step

    def test_workspace_name_stored(self, tmp_path):
        result = get_bootstrap_wizard_plan(tmp_path, "test-vault")
        assert result["workspace_name"] == "test-vault"

    def test_target_dir_stored(self, tmp_path):
        result = get_bootstrap_wizard_plan(tmp_path)
        assert result["target_dir"] == str(tmp_path)

    def test_cli_launch_command_present(self, tmp_path):
        result = get_bootstrap_wizard_plan(tmp_path)
        assert "chaseos studio shell" in result["cli_launch_command"]

    def test_existing_step_ids_detected(self, tmp_path):
        (tmp_path / "00_HOME").mkdir()
        result = get_bootstrap_wizard_plan(tmp_path)
        assert "create-folders" in result["existing_step_ids"]

    def test_pending_step_count(self, tmp_path):
        result = get_bootstrap_wizard_plan(tmp_path)
        assert result["pending_steps"] == result["total_steps"] - result["completed_steps"]

    def test_authority_read_only(self, tmp_path):
        result = get_bootstrap_wizard_plan(tmp_path)
        assert result["authority"]["read_only"] is True
        assert result["authority"]["writes_performed"] is False


# ── API integration ───────────────────────────────────────────────────────────

class TestAPIIntegration:
    def test_scan_folder_via_api(self, tmp_path):
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(tmp_path)
        result = api.scan_folder(str(tmp_path))
        assert result["ok"] is True
        assert "scan" in result["data"]

    def test_get_bootstrap_wizard_plan_via_api(self, tmp_path):
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(tmp_path)
        result = api.get_bootstrap_wizard_plan(str(tmp_path), "test-vault")
        assert result["ok"] is True
        assert "steps" in result["data"]

    def test_open_folder_and_scan_cancelled_when_no_window(self, tmp_path):
        from runtime.studio.shell.api import StudioAPI
        api = StudioAPI(tmp_path)
        result = api.open_folder_and_scan()
        assert result["ok"] is False
        assert result["error"]["code"] == "no_window"
