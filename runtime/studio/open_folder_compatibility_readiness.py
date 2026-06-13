"""Phase 10F1 read-only Open Folder compatibility readiness.

This is the productized compatibility gate for the Studio workspace-entry lane.
It inspects folder shape, bounded path inventory, and compatibility signals
without reading Markdown contents or writing any files.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODEL_VERSION = "studio.open_folder_compatibility_readiness.v1"
SURFACE_ID = "studio_open_folder_compatibility_readiness"
PASS_ID = "phase10f1-open-folder-compatibility-readiness"

CHASEOS_REQUIRED_DIRS = (
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
)

CHASEOS_REQUIRED_FILES = (
    "README.md",
    "PROJECT_FOUNDATION.md",
    "ROADMAP.md",
    "00_HOME/Now.md",
    "06_AGENTS/Agent-Control-Plane.md",
    "06_AGENTS/Permission-Matrix.md",
    "06_AGENTS/Vault-Map.md",
)

OBSIDIAN_MARKERS = (
    ".obsidian",
    ".obsidian/app.json",
    ".obsidian/workspace.json",
    ".obsidian/community-plugins.json",
    ".obsidian/plugins",
    ".obsidian/snippets",
)

IGNORED_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".pytest-tmp",
    ".pytest_tmp",
    ".pytest_tmp_env",
    ".codex-tmp",
    ".codex_tmp",
    ".codex_tmp_test",
    ".codex-pytest-osril",
    ".tmp",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    "dist",
    "build",
}

COMMON_ATTACHMENT_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
    ".pdf",
    ".docx",
    ".xlsx",
    ".csv",
    ".tsv",
}

MAX_DIRECTORY_VISITS = 900
MAX_FILE_VISITS = 2500
MAX_MARKDOWN_COUNT = 1200
MAX_SAMPLE = 40


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _resolve_target(vault_root: str | Path, folder_path: str | Path | None = None) -> tuple[Path, Path]:
    vault = Path(vault_root).resolve()
    if folder_path is None or str(folder_path).strip() == "":
        return vault, vault
    candidate = Path(folder_path)
    if not candidate.is_absolute():
        candidate = vault / candidate
    return vault, candidate.resolve()


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _exists(root: Path, rel_path: str) -> bool:
    return (root / rel_path).exists()


def _shape_signals(target: Path) -> dict[str, Any]:
    if not target.exists() or not target.is_dir():
        present_dirs: list[str] = []
        present_files: list[str] = []
        obsidian_markers: list[str] = []
    else:
        present_dirs = [item for item in CHASEOS_REQUIRED_DIRS if _exists(target, item)]
        present_files = [item for item in CHASEOS_REQUIRED_FILES if _exists(target, item)]
        obsidian_markers = [item for item in OBSIDIAN_MARKERS if _exists(target, item)]

    missing_dirs = [item for item in CHASEOS_REQUIRED_DIRS if item not in present_dirs]
    missing_files = [item for item in CHASEOS_REQUIRED_FILES if item not in present_files]
    return {
        "chaseos_marker_count": len(present_dirs) + len(present_files),
        "chaseos_required_marker_count": len(CHASEOS_REQUIRED_DIRS) + len(CHASEOS_REQUIRED_FILES),
        "present_chaseos_dirs": present_dirs,
        "missing_chaseos_dirs": missing_dirs,
        "present_chaseos_files": present_files,
        "missing_chaseos_files": missing_files,
        "obsidian_marker_count": len(obsidian_markers),
        "present_obsidian_markers": obsidian_markers,
        "chaseos_native_shape_complete": not missing_dirs and not missing_files,
        "has_obsidian_config": ".obsidian" in obsidian_markers,
    }


def _bounded_inventory(target: Path) -> dict[str, Any]:
    inventory = {
        "directory_visit_limit": MAX_DIRECTORY_VISITS,
        "file_visit_limit": MAX_FILE_VISITS,
        "markdown_count_limit": MAX_MARKDOWN_COUNT,
        "directories_visited": 0,
        "files_visited": 0,
        "markdown_file_count": 0,
        "canvas_file_count": 0,
        "attachment_file_count": 0,
        "top_level_entries": [],
        "markdown_sample": [],
        "canvas_sample": [],
        "attachment_sample": [],
        "ignored_directory_names": sorted(IGNORED_DIR_NAMES),
        "truncated": False,
        "truncation_reasons": [],
        "errors": [],
    }
    if not target.exists() or not target.is_dir():
        return inventory

    try:
        for child in sorted(target.iterdir(), key=lambda item: item.name.lower()):
            if len(inventory["top_level_entries"]) >= MAX_SAMPLE:
                break
            try:
                is_dir = child.is_dir()
                is_file = child.is_file()
            except OSError as exc:
                inventory["errors"].append(f"{child.name}: {exc}")
                continue
            inventory["top_level_entries"].append(
                {
                    "name": child.name,
                    "kind": "directory" if is_dir else "file",
                    "suffix": child.suffix.lower() if is_file else None,
                }
            )
    except OSError as exc:
        inventory["errors"].append(str(exc))

    queue: deque[Path] = deque([target])
    while queue:
        folder = queue.popleft()
        inventory["directories_visited"] += 1
        if inventory["directories_visited"] > MAX_DIRECTORY_VISITS:
            inventory["truncated"] = True
            inventory["truncation_reasons"].append("directory_visit_limit_reached")
            break
        try:
            children = sorted(folder.iterdir(), key=lambda item: item.name.lower())
        except OSError as exc:
            inventory["errors"].append(f"{_rel(folder, target)}: {exc}")
            continue
        for child in children:
            try:
                is_dir = child.is_dir()
                is_file = child.is_file()
            except OSError as exc:
                inventory["errors"].append(f"{_rel(child, target)}: {exc}")
                continue
            if is_dir:
                if child.name in IGNORED_DIR_NAMES:
                    continue
                queue.append(child)
                continue
            if not is_file:
                continue
            inventory["files_visited"] += 1
            if inventory["files_visited"] > MAX_FILE_VISITS:
                inventory["truncated"] = True
                inventory["truncation_reasons"].append("file_visit_limit_reached")
                queue.clear()
                break
            suffix = child.suffix.lower()
            rel = _rel(child, target)
            if suffix == ".md":
                if inventory["markdown_file_count"] < MAX_MARKDOWN_COUNT:
                    inventory["markdown_file_count"] += 1
                    if len(inventory["markdown_sample"]) < MAX_SAMPLE:
                        inventory["markdown_sample"].append(rel)
                else:
                    inventory["truncated"] = True
                    if "markdown_count_limit_reached" not in inventory["truncation_reasons"]:
                        inventory["truncation_reasons"].append("markdown_count_limit_reached")
            elif suffix == ".canvas":
                inventory["canvas_file_count"] += 1
                if len(inventory["canvas_sample"]) < MAX_SAMPLE:
                    inventory["canvas_sample"].append(rel)
            elif suffix in COMMON_ATTACHMENT_SUFFIXES:
                inventory["attachment_file_count"] += 1
                if len(inventory["attachment_sample"]) < MAX_SAMPLE:
                    inventory["attachment_sample"].append(rel)

    return inventory


def _classify(target: Path, shape: dict[str, Any], inventory: dict[str, Any]) -> str:
    if not target.exists():
        return "invalid_missing"
    if not target.is_dir():
        return "invalid_not_directory"
    if shape["chaseos_native_shape_complete"]:
        return "chaseos_native"
    if shape["chaseos_marker_count"] >= 4:
        return "chaseos_partial"
    if shape["has_obsidian_config"]:
        return "obsidian_vault"
    if inventory["markdown_file_count"] > 0:
        return "general_markdown"
    if not inventory["top_level_entries"]:
        return "empty_folder"
    return "unknown_folder"


def _readiness(mode: str, shape: dict[str, Any], inventory: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    if mode == "invalid_missing":
        blockers.append("target-folder-does-not-exist")
    elif mode == "invalid_not_directory":
        blockers.append("target-path-is-not-a-directory")
    elif mode == "empty_folder":
        warnings.append("empty-folder-bootstrap-preview-required")
    elif mode == "unknown_folder":
        warnings.append("no-chaseos-obsidian-or-markdown-signals-detected")

    if mode in {"obsidian_vault", "general_markdown"}:
        warnings.append("not-chaseos-native-preview-only")
    if mode == "chaseos_partial":
        warnings.append("partial-chaseos-shape-review-required")
    if inventory["truncated"]:
        warnings.append("bounded-scan-truncated")
    if inventory["errors"]:
        warnings.append("scan-errors-present")

    can_open = not blockers
    can_preview = mode in {
        "chaseos_native",
        "chaseos_partial",
        "obsidian_vault",
        "general_markdown",
        "empty_folder",
        "unknown_folder",
    }
    return {
        "ok": can_open,
        "folder_selectable": can_open,
        "compatibility_preview_ready": can_preview and can_open,
        "mode": mode,
        "mode_label": {
            "chaseos_native": "ChaseOS Native",
            "chaseos_partial": "Partial ChaseOS",
            "obsidian_vault": "Obsidian Vault",
            "general_markdown": "General Markdown",
            "empty_folder": "Empty Folder",
            "unknown_folder": "Unknown Folder",
            "invalid_missing": "Missing Folder",
            "invalid_not_directory": "Not a Directory",
        }[mode],
        "recommended_open_mode": {
            "chaseos_native": "open-native",
            "chaseos_partial": "open-readonly-partial-review",
            "obsidian_vault": "open-readonly-obsidian-compatibility-preview",
            "general_markdown": "open-readonly-markdown-compatibility-preview",
            "empty_folder": "start-new-bootstrap-preview",
            "unknown_folder": "inspect-readonly-before-bootstrap",
            "invalid_missing": "not-ready",
            "invalid_not_directory": "not-ready",
        }[mode],
        "blockers": blockers,
        "warnings": warnings,
        "next_recommended_pass": "phase10f5-upgrade-plan-approval-packet",
        "migration_requires_future_approval_packet": True,
        "upgrade_execution_available": False,
    }


def build_open_folder_compatibility_readiness(
    vault_root: str | Path,
    folder_path: str | Path | None = None,
) -> dict[str, Any]:
    """Return a read-only compatibility report for a selected folder."""

    vault, target = _resolve_target(vault_root, folder_path)
    shape = _shape_signals(target)
    inventory = _bounded_inventory(target)
    mode = _classify(target, shape, inventory)
    readiness = _readiness(mode, shape, inventory)
    return {
        "ok": readiness["ok"],
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": "COMPLETE / READ-ONLY / VERIFIED",
        "generated_at": _now_utc(),
        "title": "ChaseOS Studio Open Folder Compatibility Readiness",
        "vault_root": str(vault),
        "target": {
            "requested_path": str(folder_path) if folder_path is not None else None,
            "resolved_path": str(target),
            "exists": target.exists(),
            "is_directory": target.is_dir() if target.exists() else False,
            "mode": mode,
        },
        "summary": {
            "mode": mode,
            "mode_label": readiness["mode_label"],
            "markdown_file_count": inventory["markdown_file_count"],
            "canvas_file_count": inventory["canvas_file_count"],
            "attachment_file_count": inventory["attachment_file_count"],
            "chaseos_marker_count": shape["chaseos_marker_count"],
            "obsidian_marker_count": shape["obsidian_marker_count"],
            "truncated": inventory["truncated"],
        },
        "signals": {
            "shape": shape,
            "inventory": inventory,
        },
        "readiness": readiness,
        "performance_contract": {
            "bounded_scan": True,
            "reads_markdown_contents": False,
            "counts_are_upper_bounded_when_truncated": True,
            "does_not_build_graph": True,
            "does_not_persist_index": True,
            "directory_visit_limit": MAX_DIRECTORY_VISITS,
            "file_visit_limit": MAX_FILE_VISITS,
            "markdown_count_limit": MAX_MARKDOWN_COUNT,
        },
        "authority_boundary": {
            "read_only": True,
            "writes_selected_folder": False,
            "writes_vault": False,
            "writes_approval_artifacts": False,
            "migration_writer_built": False,
            "upgrade_executor_built": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "workflow_execution_allowed": False,
            "agent_bus_task_writes_allowed": False,
            "gate_mutation_allowed": False,
            "git_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "allowed_actions": ["inspect-open-folder-compatibility-readiness"],
        "possible_writes": [],
        "future_passes": [
            "10F4-chaseos-bootstrap-wizard-preview",
            "10F5-upgrade-plan-approval-packet",
            "10F6-approved-upgrade-execution-proof",
        ],
    }
