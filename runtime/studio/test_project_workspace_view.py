"""Tests for runtime/studio/project_workspace_view.py (Pass 10D)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from runtime.studio.project_workspace_view import (
    MODEL_VERSION,
    SURFACE_ID,
    _extract_frontmatter,
    _fm_val,
    _parse_project_os,
    _read_sprint_focus,
    build_project_workspace_view,
)


# ── Frontmatter helpers ───────────────────────────────────────────────────────

class TestExtractFrontmatter:
    def test_extracts_between_fences(self):
        text = "---\nproject: Foo\n---\nbody"
        fm = _extract_frontmatter(text)
        assert "project: Foo" in fm

    def test_empty_when_no_fence(self):
        text = "just body text"
        assert _extract_frontmatter(text) == ""

    def test_partial_fence(self):
        text = "---\nproject: Foo\nbody"
        assert _extract_frontmatter(text) == ""

    def test_extracts_all_fields(self):
        text = "---\nproject: Test\ndomain: A\nstatus: Active\n---"
        fm = _extract_frontmatter(text)
        assert "project: Test" in fm
        assert "domain: A" in fm
        assert "status: Active" in fm


class TestFmVal:
    def test_project_field(self):
        fm = "project: MyProject\ndomain: X\n"
        assert _fm_val("project", fm) == "MyProject"

    def test_domain_field(self):
        fm = "domain: A — System Infrastructure\n"
        assert _fm_val("domain", fm) == "A — System Infrastructure"

    def test_status_field(self):
        fm = "status: Active / Ongoing\n"
        assert _fm_val("status", fm) == "Active / Ongoing"

    def test_missing_field_returns_none(self):
        fm = "project: X\n"
        assert _fm_val("updated", fm) is None

    def test_case_insensitive(self):
        fm = "PROJECT: CaseTest\n"
        assert _fm_val("project", fm) == "CaseTest"


# ── _parse_project_os ─────────────────────────────────────────────────────────

class TestParseProjectOs:
    def test_parses_valid_os_file(self, tmp_path):
        os_file = tmp_path / "ChaseOS-OS.md"
        os_file.write_text(
            "---\ntype: project-os\nproject: ChaseOS\ndomain: A — System\nstatus: Active\nupdated: 2026-05-05\n---\n# Body",
            encoding="utf-8",
        )
        result = _parse_project_os(os_file)
        assert result["project"] == "ChaseOS"
        assert result["domain"] == "A — System"
        assert result["status"] == "Active"
        assert result["updated"] == "2026-05-05"
        assert result["parse_error"] is False

    def test_fallback_to_folder_name_when_no_frontmatter(self, tmp_path):
        os_file = tmp_path / "MyProject-OS.md"
        os_file.write_text("# No frontmatter", encoding="utf-8")
        result = _parse_project_os(os_file)
        assert result["project"] == tmp_path.name
        assert result["domain"] == "unknown"
        assert result["parse_error"] is False

    def test_handles_missing_file(self, tmp_path):
        os_file = tmp_path / "Missing-OS.md"
        result = _parse_project_os(os_file)
        assert result["parse_error"] is True
        assert result["project"] == tmp_path.name

    def test_strips_trailing_whitespace_from_status(self, tmp_path):
        os_file = tmp_path / "Test-OS.md"
        os_file.write_text("---\nstatus:   Active / Ongoing  \n---", encoding="utf-8")
        result = _parse_project_os(os_file)
        assert result["status"] == "Active / Ongoing"


# ── _read_sprint_focus ────────────────────────────────────────────────────────

class TestReadSprintFocus:
    def test_extracts_current_phase_section(self, tmp_path):
        now = tmp_path / "00_HOME" / "Now.md"
        now.parent.mkdir(parents=True)
        now.write_text(
            "# Now\n\n## Current Phase\n\nPhase 10 active.\n\nSomething.\n\n## Other Section\n\nOther content.",
            encoding="utf-8",
        )
        result = _read_sprint_focus(tmp_path)
        assert result is not None
        assert "Phase 10 active" in result
        assert "Other content" not in result

    def test_returns_none_when_now_md_missing(self, tmp_path):
        result = _read_sprint_focus(tmp_path)
        assert result is None

    def test_falls_back_to_first_lines_when_no_section(self, tmp_path):
        now = tmp_path / "00_HOME" / "Now.md"
        now.parent.mkdir(parents=True)
        now.write_text("Line 1\nLine 2\nLine 3", encoding="utf-8")
        result = _read_sprint_focus(tmp_path)
        assert result is not None
        assert "Line 1" in result

    def test_returns_none_when_file_is_empty(self, tmp_path):
        now = tmp_path / "00_HOME" / "Now.md"
        now.parent.mkdir(parents=True)
        now.write_text("", encoding="utf-8")
        result = _read_sprint_focus(tmp_path)
        assert result is None


# ── build_project_workspace_view ─────────────────────────────────────────────

def _make_vault(tmp_path: Path) -> Path:
    projects = tmp_path / "01_PROJECTS"
    projects.mkdir()
    home = tmp_path / "00_HOME"
    home.mkdir()
    return tmp_path


def _add_project(
    vault: Path,
    folder_name: str,
    project: str,
    domain: str = "A",
    status: str = "Active",
) -> None:
    folder = vault / "01_PROJECTS" / folder_name
    folder.mkdir(parents=True, exist_ok=True)
    os_file = folder / f"{folder_name}-OS.md"
    os_file.write_text(
        f"---\ntype: project-os\nproject: {project}\ndomain: {domain}\nstatus: {status}\n---",
        encoding="utf-8",
    )


class TestBuildProjectWorkspaceView:
    def test_basic_shape(self, tmp_path):
        _make_vault(tmp_path)
        _add_project(tmp_path, "ChaseOS", "ChaseOS", "A — System")
        result = build_project_workspace_view(tmp_path)
        assert result["surface"] == SURFACE_ID
        assert result["model_version"] == MODEL_VERSION
        assert result["title"] == "ChaseOS Studio Project Workspace"
        assert result["panel_id"] == "studio-project-workspace"
        assert result["route_hint"] == "#projects"
        assert result["project_count"] >= 1
        assert isinstance(result["domains"], list)
        assert isinstance(result["projects"], list)

    def test_counts_active_projects(self, tmp_path):
        _make_vault(tmp_path)
        _add_project(tmp_path, "Proj1", "Proj1", status="Active / Ongoing")
        _add_project(tmp_path, "Proj2", "Proj2", status="Active")
        _add_project(tmp_path, "Proj3", "Proj3", status="Paused")
        result = build_project_workspace_view(tmp_path)
        assert result["active_count"] == 2
        assert result["paused_count"] == 1

    def test_groups_by_domain(self, tmp_path):
        _make_vault(tmp_path)
        _add_project(tmp_path, "Proj1", "Proj1", domain="A — System")
        _add_project(tmp_path, "Proj2", "Proj2", domain="A — System")
        _add_project(tmp_path, "Proj3", "Proj3", domain="B — Trading")
        result = build_project_workspace_view(tmp_path)
        domain_map = {d["domain"]: d for d in result["domains"]}
        assert "A — System" in domain_map
        assert domain_map["A — System"]["project_count"] == 2
        assert "B — Trading" in domain_map

    def test_includes_sprint_focus_when_now_md_present(self, tmp_path):
        _make_vault(tmp_path)
        now = tmp_path / "00_HOME" / "Now.md"
        now.write_text("## Current Phase\n\nPhase 10 active.\n\n## Other\n\nOther.", encoding="utf-8")
        result = build_project_workspace_view(tmp_path)
        assert result["sprint_focus"] is not None
        assert "Phase 10 active" in result["sprint_focus"]
        assert result["readiness"]["sprint_focus_available"] is True

    def test_sprint_focus_none_when_now_md_missing(self, tmp_path):
        _make_vault(tmp_path)
        result = build_project_workspace_view(tmp_path)
        assert result["sprint_focus"] is None
        assert result["readiness"]["sprint_focus_available"] is False

    def test_warns_when_projects_dir_missing(self, tmp_path):
        result = build_project_workspace_view(tmp_path)
        assert "01_PROJECTS_dir_missing" in result["warnings"]
        assert result["readiness"]["projects_dir_found"] is False

    def test_empty_vault_returns_zero_projects(self, tmp_path):
        _make_vault(tmp_path)
        result = build_project_workspace_view(tmp_path)
        assert result["project_count"] == 0
        assert result["domain_count"] == 0
        assert result["domains"] == []

    def test_skips_non_directory_entries(self, tmp_path):
        _make_vault(tmp_path)
        projects = tmp_path / "01_PROJECTS"
        (projects / "Hub.md").write_text("hub", encoding="utf-8")
        _add_project(tmp_path, "Real", "Real")
        result = build_project_workspace_view(tmp_path)
        assert result["project_count"] == 1

    def test_skips_folders_without_os_file(self, tmp_path):
        _make_vault(tmp_path)
        empty_folder = tmp_path / "01_PROJECTS" / "Empty"
        empty_folder.mkdir()
        result = build_project_workspace_view(tmp_path)
        assert result["project_count"] == 0

    def test_read_only_authority(self, tmp_path):
        _make_vault(tmp_path)
        result = build_project_workspace_view(tmp_path)
        assert result["allowed_actions"] == ["inspect-project-workspace-readiness"]
        assert result["possible_writes"] == []
        assert result["authority"]["read_only"] is True
        assert result["authority"]["writes_vault"] is False
        assert result["authority"]["canonical_writeback_allowed"] is False
        assert result["authority"]["gate_mutation_allowed"] is False
        readiness = result["readiness"]
        assert readiness["read_only"] is True
        assert readiness["writes_vault"] is False
        assert readiness["provider_calls"] is False
        assert readiness["connector_calls"] is False

    def test_parse_error_project_rows_surface_warning_without_writes(self, tmp_path, monkeypatch):
        _make_vault(tmp_path)
        project_dir = tmp_path / "01_PROJECTS" / "Broken"
        project_dir.mkdir(parents=True)
        os_file = project_dir / "Broken-OS.md"
        os_file.write_text("---\nproject: Broken\n---", encoding="utf-8")

        def fake_parse(path: Path) -> dict:
            return {
                "project": path.parent.name,
                "domain": "unknown",
                "status": "unknown",
                "updated": None,
                "file_name": path.name,
                "parse_error": True,
            }

        monkeypatch.setattr("runtime.studio.project_workspace_view._parse_project_os", fake_parse)

        result = build_project_workspace_view(tmp_path)

        assert result["parse_error_count"] == 1
        assert "project_os_parse_errors_present" in result["warnings"]
        assert result["empty_state"]["message"].startswith("Project map is available")
        assert result["possible_writes"] == []
        assert result["authority"]["writes_vault"] is False

    def test_domain_count_matches_unique_domains(self, tmp_path):
        _make_vault(tmp_path)
        _add_project(tmp_path, "P1", "P1", domain="A")
        _add_project(tmp_path, "P2", "P2", domain="A")
        _add_project(tmp_path, "P3", "P3", domain="B")
        _add_project(tmp_path, "P4", "P4", domain="C")
        result = build_project_workspace_view(tmp_path)
        assert result["domain_count"] == 3
        assert result["project_count"] == 4

    def test_parked_counted_in_paused(self, tmp_path):
        _make_vault(tmp_path)
        _add_project(tmp_path, "P1", "P1", status="PARKED")
        _add_project(tmp_path, "P2", "P2", status="Deferred")
        result = build_project_workspace_view(tmp_path)
        assert result["paused_count"] == 2

    def test_vault_root_in_result(self, tmp_path):
        _make_vault(tmp_path)
        result = build_project_workspace_view(tmp_path)
        assert str(tmp_path.resolve()) in result["vault_root"]

    def test_live_vault_root_returns_valid_shape(self):
        from pathlib import Path
        vault = Path(__file__).parent.parent.parent
        if not (vault / "01_PROJECTS").exists():
            pytest.skip("01_PROJECTS not found in live vault")
        result = build_project_workspace_view(vault)
        assert result["surface"] == SURFACE_ID
        assert result["project_count"] >= 0
        assert isinstance(result["domains"], list)
