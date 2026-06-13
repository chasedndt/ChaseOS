"""Read-only Studio Open Folder readiness contract.

This module gives Phase 10A a bounded folder-readiness model for the future
Studio Start New / Open Folder entry flow. It inspects path shape and shallow
workspace signals only. It does not parse file contents, infer a full graph,
write metadata, start apps, execute workflows, call providers/connectors, or
mutate canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.graph_view_browser_qa import (
    STATIC_GRAPH_BROWSER_QA_PASS,
    next_graph_view_pass_after_browser_qa,
    static_graph_browser_qa_evidence_built,
)


MODEL_VERSION = "studio.open_folder_readiness.v1"
SURFACE_ID = "studio_open_folder_readiness_contract"

_CHASEOS_DIRS = [
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
]

_CHASEOS_FILES = [
    "README.md",
    "PROJECT_FOUNDATION.md",
    "ROADMAP.md",
    "00_HOME/Now.md",
    "06_AGENTS/ChaseOS-Studio-Architecture.md",
]

_TOP_LEVEL_SAMPLE_LIMIT = 24
_MARKDOWN_SCAN_LIMIT = 500
_MARKDOWN_SAMPLE_LIMIT = 20


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _resolve_target(vault_root: str | Path, folder_path: str | Path | None) -> tuple[Path, Path]:
    vault = Path(vault_root).resolve()
    if folder_path is None:
        return vault, vault
    candidate = Path(folder_path)
    if not candidate.is_absolute():
        candidate = vault / candidate
    return vault, candidate.resolve()


def _rel_exists(root: Path, rel_path: str) -> bool:
    return (root / rel_path).exists()


def _relative_to(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _top_level_sample(target: Path) -> dict[str, Any]:
    if not target.exists() or not target.is_dir():
        return {
            "sample_limit": _TOP_LEVEL_SAMPLE_LIMIT,
            "entries": [],
            "truncated": False,
            "errors": [],
        }

    entries: list[dict[str, Any]] = []
    errors: list[str] = []
    truncated = False
    try:
        for child in sorted(target.iterdir(), key=lambda item: item.name.lower()):
            if len(entries) >= _TOP_LEVEL_SAMPLE_LIMIT:
                truncated = True
                break
            entries.append(
                {
                    "name": child.name,
                    "kind": "directory" if child.is_dir() else "file",
                    "markdown": child.is_file() and child.suffix.lower() == ".md",
                }
            )
    except OSError as exc:
        errors.append(str(exc))

    return {
        "sample_limit": _TOP_LEVEL_SAMPLE_LIMIT,
        "entries": entries,
        "truncated": truncated,
        "errors": errors,
    }


def _markdown_inventory(target: Path) -> dict[str, Any]:
    if not target.exists() or not target.is_dir():
        return {
            "scan_limit": _MARKDOWN_SCAN_LIMIT,
            "markdown_file_count": 0,
            "sample": [],
            "truncated": False,
            "errors": [],
        }

    count = 0
    sample: list[str] = []
    errors: list[str] = []
    truncated = False
    try:
        for path in target.rglob("*.md"):
            if not path.is_file():
                continue
            if count >= _MARKDOWN_SCAN_LIMIT:
                truncated = True
                break
            count += 1
            if len(sample) < _MARKDOWN_SAMPLE_LIMIT:
                sample.append(_relative_to(path, target))
    except OSError as exc:
        errors.append(str(exc))

    return {
        "scan_limit": _MARKDOWN_SCAN_LIMIT,
        "markdown_file_count": count,
        "sample_limit": _MARKDOWN_SAMPLE_LIMIT,
        "sample": sample,
        "truncated": truncated,
        "errors": errors,
    }


def _chaseos_shape(target: Path) -> dict[str, Any]:
    if not target.exists() or not target.is_dir():
        present_dirs: list[str] = []
        present_files: list[str] = []
    else:
        present_dirs = [path for path in _CHASEOS_DIRS if _rel_exists(target, path)]
        present_files = [path for path in _CHASEOS_FILES if _rel_exists(target, path)]

    missing_dirs = [path for path in _CHASEOS_DIRS if path not in present_dirs]
    missing_files = [path for path in _CHASEOS_FILES if path not in present_files]
    return {
        "required_dir_count": len(_CHASEOS_DIRS),
        "present_dir_count": len(present_dirs),
        "present_dirs": present_dirs,
        "missing_dirs": missing_dirs,
        "required_file_count": len(_CHASEOS_FILES),
        "present_file_count": len(present_files),
        "present_files": present_files,
        "missing_files": missing_files,
        "native_required_shape_complete": not missing_dirs and not missing_files,
    }


def _classify_target(
    target: Path,
    chaseos_shape: dict[str, Any],
    markdown_inventory: dict[str, Any],
) -> str:
    if not target.exists():
        return "invalid_missing"
    if not target.is_dir():
        return "invalid_not_directory"
    if chaseos_shape["native_required_shape_complete"]:
        return "chaseos_native_detected"
    if chaseos_shape["present_dir_count"] >= 3 or chaseos_shape["present_file_count"] >= 2:
        return "chaseos_partial_detected"
    if (target / ".obsidian").is_dir() or markdown_inventory["markdown_file_count"] > 0:
        return "general_markdown_or_obsidian"
    return "empty_or_unknown"


def _next_studio_pass(
    *,
    vault_root: str | Path | None,
    markdown_scan_contract_built: bool,
    graph_index_contract_built: bool,
    node_inspector_contract_built: bool,
    graph_view_contract_built: bool,
    static_graph_renderer_built: bool,
    static_graph_browser_qa_built: bool,
) -> str:
    if not markdown_scan_contract_built:
        return "phase10-studio-markdown-scan-contract"
    if not graph_index_contract_built:
        return "phase10-studio-graph-index-contract"
    if not node_inspector_contract_built:
        return "phase10-studio-node-inspector-readonly"
    if not graph_view_contract_built:
        return "phase10-studio-graph-view-readonly-contract"
    if not static_graph_renderer_built:
        return "phase10-studio-graph-view-local-static-render"
    if not static_graph_browser_qa_built:
        return STATIC_GRAPH_BROWSER_QA_PASS
    return next_graph_view_pass_after_browser_qa(vault_root)


def _readiness(
    mode: str,
    chaseos_shape: dict[str, Any],
    vault_root: str | Path | None,
    markdown_scan_contract_built: bool,
    graph_index_contract_built: bool,
    node_inspector_contract_built: bool,
    graph_view_contract_built: bool,
    static_graph_renderer_built: bool,
    static_graph_browser_qa_built: bool,
) -> dict[str, Any]:
    folder_selectable = mode not in {"invalid_missing", "invalid_not_directory"}
    chaseos_native_ready = mode == "chaseos_native_detected"
    general_markdown_ready = mode == "general_markdown_or_obsidian"
    partial_ready = mode == "chaseos_partial_detected"
    workspace_import_ready = chaseos_native_ready or general_markdown_ready or partial_ready

    blockers: list[str] = []
    warnings: list[str] = []
    if mode == "invalid_missing":
        blockers.append("target-folder-does-not-exist")
    elif mode == "invalid_not_directory":
        blockers.append("target-path-is-not-a-directory")
    elif mode == "empty_or_unknown":
        warnings.append("no-chaseos-or-markdown-signals-detected")

    if folder_selectable and not chaseos_native_ready:
        warnings.append("not-a-complete-chaseos-native-workspace")
    if chaseos_shape["missing_dirs"]:
        warnings.append("missing-chaseos-required-directories")
    if chaseos_shape["missing_files"]:
        warnings.append("missing-chaseos-required-files")

    if chaseos_native_ready:
        recommended_mode = "chaseos-native"
        next_pass = _next_studio_pass(
            vault_root=vault_root,
            markdown_scan_contract_built=markdown_scan_contract_built,
            graph_index_contract_built=graph_index_contract_built,
            node_inspector_contract_built=node_inspector_contract_built,
            graph_view_contract_built=graph_view_contract_built,
            static_graph_renderer_built=static_graph_renderer_built,
            static_graph_browser_qa_built=static_graph_browser_qa_built,
        )
    elif partial_ready:
        recommended_mode = "chaseos-partial-review"
        next_pass = _next_studio_pass(
            vault_root=vault_root,
            markdown_scan_contract_built=markdown_scan_contract_built,
            graph_index_contract_built=graph_index_contract_built,
            node_inspector_contract_built=node_inspector_contract_built,
            graph_view_contract_built=graph_view_contract_built,
            static_graph_renderer_built=static_graph_renderer_built,
            static_graph_browser_qa_built=static_graph_browser_qa_built,
        )
    elif general_markdown_ready:
        recommended_mode = "general-markdown-compatible"
        next_pass = _next_studio_pass(
            vault_root=vault_root,
            markdown_scan_contract_built=markdown_scan_contract_built,
            graph_index_contract_built=graph_index_contract_built,
            node_inspector_contract_built=node_inspector_contract_built,
            graph_view_contract_built=graph_view_contract_built,
            static_graph_renderer_built=static_graph_renderer_built,
            static_graph_browser_qa_built=static_graph_browser_qa_built,
        )
    elif folder_selectable:
        recommended_mode = "empty-or-unknown-readonly"
        next_pass = "phase10-studio-start-new-bootstrap-contract"
    else:
        recommended_mode = "not-ready"
        next_pass = "phase10-studio-open-folder-error-handling"

    return {
        "folder_selectable": folder_selectable,
        "open_folder_ready": folder_selectable,
        "workspace_import_ready": workspace_import_ready,
        "chaseos_native_ready": chaseos_native_ready,
        "general_markdown_ready": general_markdown_ready,
        "recommended_mode": recommended_mode,
        "blockers": blockers,
        "warnings": warnings,
        "next_recommended_pass": next_pass,
    }


def build_open_folder_readiness(
    vault_root: str | Path,
    folder_path: str | Path | None = None,
) -> dict[str, Any]:
    """Return the read-only Phase 10A Open Folder readiness contract."""

    vault, target = _resolve_target(vault_root, folder_path)
    shape = _chaseos_shape(target)
    markdown = _markdown_inventory(target)
    mode = _classify_target(target, shape, markdown)
    markdown_scan_contract_built = _rel_exists(vault, "runtime/studio/markdown_scan_contract.py")
    graph_index_contract_built = _rel_exists(vault, "runtime/studio/graph_index_contract.py")
    node_inspector_contract_built = _rel_exists(vault, "runtime/studio/node_inspector_contract.py")
    graph_view_contract_built = _rel_exists(vault, "runtime/studio/graph_view_contract.py")
    static_graph_renderer_built = _rel_exists(vault, "runtime/studio/graph_view_static_renderer.py")
    static_graph_browser_qa_built = static_graph_browser_qa_evidence_built(vault)
    readiness = _readiness(
        mode,
        shape,
        vault,
        markdown_scan_contract_built,
        graph_index_contract_built,
        node_inspector_contract_built,
        graph_view_contract_built,
        static_graph_renderer_built,
        static_graph_browser_qa_built,
    )
    return {
        "ok": not readiness["blockers"],
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "title": "ChaseOS Studio Open Folder Readiness",
        "phase": "Phase 10A - Studio Core Shell",
        "status": "PARTIAL / READ-ONLY OPEN FOLDER READINESS CONTRACT BUILT / FULL FLOW NOT BUILT",
        "vault_root": str(vault),
        "target": {
            "requested_path": str(folder_path) if folder_path is not None else None,
            "resolved_path": str(target),
            "exists": target.exists(),
            "is_directory": target.is_dir() if target.exists() else False,
            "mode": mode,
            "has_obsidian_config": (target / ".obsidian").is_dir() if target.exists() and target.is_dir() else False,
        },
        "chaseos_shape": shape,
        "folder_sample": _top_level_sample(target),
        "markdown_inventory": markdown,
        "readiness": readiness,
        "flow_truth": {
            "readiness_contract_built": True,
            "start_new_flow_built": False,
            "open_folder_ui_built": False,
            "markdown_scan_contract_built": markdown_scan_contract_built,
            "graph_index_contract_built": graph_index_contract_built,
            "node_inspector_contract_built": node_inspector_contract_built,
            "graph_view_contract_built": graph_view_contract_built,
            "static_graph_renderer_built": static_graph_renderer_built,
            "static_graph_browser_qa_built": static_graph_browser_qa_built,
            "graph_view_built": False,
            "file_scanner_markdown_parser_built": False,
            "frontmatter_parser_built": False,
            "wikilink_detector_built": False,
            "graph_index_built": False,
            "node_inspector_built": False,
            "workspace_upgrade_writer_built": False,
        },
        "authority": {
            "read_only": True,
            "reads_file_contents": False,
            "bounded_markdown_path_inventory": True,
            "starts_servers": False,
            "starts_child_apps": False,
            "writes_opened_folder": False,
            "writes_vault": False,
            "writes_settings": False,
            "writes_node_ids": False,
            "workflow_execution_allowed": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "browser_automation_allowed": False,
            "scheduler_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "possible_writes": [],
        "allowed_actions": ["inspect-open-folder-readiness"],
        "docs": [
            "ROADMAP.md",
            "06_AGENTS/ChaseOS-Studio-Architecture.md",
            "07_LOGS/Build-Logs/2026-05-02-ChaseOS-phase10-studio-open-folder-readiness-contract.md",
        ],
    }
