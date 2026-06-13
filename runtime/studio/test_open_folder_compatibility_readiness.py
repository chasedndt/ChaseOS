"""Tests for Phase 10F1 Open Folder compatibility readiness."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.open_folder_compatibility_readiness import (
    MAX_DIRECTORY_VISITS,
    MODEL_VERSION,
    PASS_ID,
    SURFACE_ID,
    build_open_folder_compatibility_readiness,
)


def _seed_chaseos_native(root: Path) -> None:
    for folder in [
        "00_HOME",
        "01_PROJECTS",
        "02_KNOWLEDGE",
        "03_INPUTS",
        "04_SOPS",
        "05_TEMPLATES",
        "06_AGENTS",
        "07_LOGS",
        "99_ARCHIVE",
        "runtime",
    ]:
        (root / folder).mkdir(parents=True, exist_ok=True)
    for rel_path in [
        "README.md",
        "PROJECT_FOUNDATION.md",
        "ROADMAP.md",
        "00_HOME/Now.md",
        "06_AGENTS/Agent-Control-Plane.md",
        "06_AGENTS/Permission-Matrix.md",
        "06_AGENTS/Vault-Map.md",
    ]:
        path = root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("seed\n", encoding="utf-8")


def test_detects_chaseos_native_without_writes(tmp_path: Path) -> None:
    _seed_chaseos_native(tmp_path)
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))

    report = build_open_folder_compatibility_readiness(tmp_path)

    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    assert report["ok"] is True
    assert report["surface"] == SURFACE_ID
    assert report["model_version"] == MODEL_VERSION
    assert report["pass"] == PASS_ID
    assert report["target"]["mode"] == "chaseos_native"
    assert report["summary"]["chaseos_marker_count"] == report["signals"]["shape"]["chaseos_required_marker_count"]
    assert report["readiness"]["recommended_open_mode"] == "open-native"
    assert report["authority_boundary"]["writes_selected_folder"] is False
    assert before == after


def test_detects_obsidian_vault(tmp_path: Path) -> None:
    (tmp_path / ".obsidian").mkdir()
    (tmp_path / ".obsidian" / "app.json").write_text("{}", encoding="utf-8")
    (tmp_path / "Notes").mkdir()
    (tmp_path / "Notes" / "Alpha.md").write_text("# Alpha\n", encoding="utf-8")
    (tmp_path / "Board.canvas").write_text("{}", encoding="utf-8")

    report = build_open_folder_compatibility_readiness(tmp_path)

    assert report["ok"] is True
    assert report["target"]["mode"] == "obsidian_vault"
    assert report["summary"]["obsidian_marker_count"] >= 2
    assert report["summary"]["markdown_file_count"] == 1
    assert report["summary"]["canvas_file_count"] == 1
    assert report["readiness"]["recommended_open_mode"] == "open-readonly-obsidian-compatibility-preview"
    assert "not-chaseos-native-preview-only" in report["readiness"]["warnings"]


def test_detects_general_markdown_without_reading_contents(tmp_path: Path) -> None:
    (tmp_path / "notes").mkdir()
    (tmp_path / "notes" / "Alpha.md").write_text("[[Beta]]\n", encoding="utf-8")
    (tmp_path / "media.pdf").write_text("fake", encoding="utf-8")

    report = build_open_folder_compatibility_readiness(tmp_path)

    assert report["ok"] is True
    assert report["target"]["mode"] == "general_markdown"
    assert report["summary"]["markdown_file_count"] == 1
    assert report["summary"]["attachment_file_count"] == 1
    assert report["performance_contract"]["reads_markdown_contents"] is False
    assert report["performance_contract"]["does_not_build_graph"] is True


def test_partial_chaseos_classification(tmp_path: Path) -> None:
    for folder in ["00_HOME", "06_AGENTS", "07_LOGS"]:
        (tmp_path / folder).mkdir()
    (tmp_path / "README.md").write_text("seed\n", encoding="utf-8")

    report = build_open_folder_compatibility_readiness(tmp_path)

    assert report["ok"] is True
    assert report["target"]["mode"] == "chaseos_partial"
    assert "partial-chaseos-shape-review-required" in report["readiness"]["warnings"]


def test_empty_folder_is_previewable_not_migrated(tmp_path: Path) -> None:
    report = build_open_folder_compatibility_readiness(tmp_path)

    assert report["ok"] is True
    assert report["target"]["mode"] == "empty_folder"
    assert report["readiness"]["recommended_open_mode"] == "start-new-bootstrap-preview"
    assert report["authority_boundary"]["migration_writer_built"] is False
    assert report["authority_boundary"]["upgrade_executor_built"] is False


def test_missing_and_file_targets_block_cleanly(tmp_path: Path) -> None:
    missing = build_open_folder_compatibility_readiness(tmp_path, tmp_path / "missing")
    file_path = tmp_path / "file.md"
    file_path.write_text("x", encoding="utf-8")
    file_report = build_open_folder_compatibility_readiness(tmp_path, file_path)

    assert missing["ok"] is False
    assert missing["target"]["mode"] == "invalid_missing"
    assert missing["readiness"]["blockers"] == ["target-folder-does-not-exist"]
    assert file_report["ok"] is False
    assert file_report["target"]["mode"] == "invalid_not_directory"
    assert file_report["readiness"]["blockers"] == ["target-path-is-not-a-directory"]


def test_large_folder_scan_is_bounded(tmp_path: Path) -> None:
    for idx in range(MAX_DIRECTORY_VISITS + 8):
        folder = tmp_path / f"d{idx:04d}"
        folder.mkdir()
        (folder / "note.md").write_text("x\n", encoding="utf-8")

    report = build_open_folder_compatibility_readiness(tmp_path)

    inventory = report["signals"]["inventory"]
    assert inventory["truncated"] is True
    assert "directory_visit_limit_reached" in inventory["truncation_reasons"]
    assert inventory["directories_visited"] == MAX_DIRECTORY_VISITS + 1
    assert report["summary"]["truncated"] is True
    assert "bounded-scan-truncated" in report["readiness"]["warnings"]

