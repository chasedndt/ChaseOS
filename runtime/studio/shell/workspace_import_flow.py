"""ChaseOS Studio — Workspace Import Flow (Pass 10E).

Provides the backend logic for:
  - Open Folder → scan → mode detection → routing
  - Compatibility mode analysis (best-effort type inference for non-ChaseOS vaults)
  - Bootstrap wizard step plan (read-only plan; execution is a future governed pass)

All operations are read-only. No files are created, moved, or modified.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_CHASEOS_DIRS = [
    "00_HOME", "01_PROJECTS", "02_KNOWLEDGE", "03_INPUTS",
    "04_SOPS", "05_TEMPLATES", "06_AGENTS", "07_LOGS", "99_ARCHIVE", "runtime",
]

_CHASEOS_FILES = [
    "README.md", "PROJECT_FOUNDATION.md", "ROADMAP.md",
    "00_HOME/Now.md", "06_AGENTS/ChaseOS-Studio-Architecture.md",
]

_IGNORED_DIRS = {".git", "__pycache__", ".venv", "node_modules", ".obsidian"}

_BOOTSTRAP_STEPS = [
    {
        "step": 1,
        "id": "create-folders",
        "title": "Create ChaseOS folder structure",
        "description": "Creates the 10-directory ChaseOS vault skeleton (00_HOME through 99_ARCHIVE + runtime/).",
        "cli": "mkdir 00_HOME 01_PROJECTS 02_KNOWLEDGE 03_INPUTS 04_SOPS 05_TEMPLATES 06_AGENTS 07_LOGS 99_ARCHIVE runtime",
        "writes": ["00_HOME/", "01_PROJECTS/", "02_KNOWLEDGE/", "03_INPUTS/", "04_SOPS/", "05_TEMPLATES/", "06_AGENTS/", "07_LOGS/", "99_ARCHIVE/", "runtime/"],
        "required": True,
    },
    {
        "step": 2,
        "id": "create-now",
        "title": "Create Now.md (sprint focus file)",
        "description": "Creates 00_HOME/Now.md with a Phase 1 sprint focus block. This is the canonical sprint state file read by every ChaseOS runtime.",
        "cli": None,
        "writes": ["00_HOME/Now.md"],
        "required": True,
    },
    {
        "step": 3,
        "id": "create-readme",
        "title": "Create README.md",
        "description": "Creates the root README.md with ChaseOS vault front-door text.",
        "cli": None,
        "writes": ["README.md"],
        "required": True,
    },
    {
        "step": 4,
        "id": "create-claude-md",
        "title": "Create CLAUDE.md",
        "description": "Creates CLAUDE.md — the Claude Code routing anchor and protected-file list for this vault.",
        "cli": None,
        "writes": ["CLAUDE.md"],
        "required": True,
    },
    {
        "step": 5,
        "id": "create-assistant-contract",
        "title": "Create Assistant Contract",
        "description": "Creates 00_HOME/Assistant-Contract.md — the binding agent permission contract for this vault.",
        "cli": None,
        "writes": ["00_HOME/Assistant-Contract.md"],
        "required": True,
    },
    {
        "step": 6,
        "id": "create-agent-files",
        "title": "Create agent registry and vault map",
        "description": "Creates 06_AGENTS/Agent-Registry.md and 06_AGENTS/Vault-Map.md — the agent and file routing maps.",
        "cli": None,
        "writes": ["06_AGENTS/Agent-Registry.md", "06_AGENTS/Vault-Map.md"],
        "required": False,
    },
]

_NODE_TYPE_INFERENCE_RULES: list[dict] = [
    {"pattern": r"00_HOME", "node_type": "home_doc", "label": "Home / OS file"},
    {"pattern": r"01_PROJECTS", "node_type": "project_doc", "label": "Project file"},
    {"pattern": r"02_KNOWLEDGE", "node_type": "knowledge_doc", "label": "Knowledge note"},
    {"pattern": r"03_INPUTS", "node_type": "markdown_note", "label": "Input / quarantine"},
    {"pattern": r"04_SOPS", "node_type": "chaseos_markdown_doc", "label": "SOP"},
    {"pattern": r"05_TEMPLATES", "node_type": "chaseos_markdown_doc", "label": "Template"},
    {"pattern": r"06_AGENTS", "node_type": "agent_control_doc", "label": "Agent control doc"},
    {"pattern": r"07_LOGS.Build-Logs", "node_type": "build_log", "label": "Build log"},
    {"pattern": r"07_LOGS.Daily", "node_type": "daily_note", "label": "Daily note"},
    {"pattern": r"07_LOGS", "node_type": "build_log", "label": "Log file"},
    {"pattern": r"99_ARCHIVE.Documentation-History", "node_type": "documentation_history_note", "label": "Archive note"},
    {"pattern": r"99_ARCHIVE", "node_type": "documentation_history_note", "label": "Archive note"},
    {"pattern": r"README", "node_type": "system_root_doc", "label": "Root readme"},
]

_MAX_COMPAT_SCAN = 300
_MAX_COMPAT_SAMPLE = 50
_MAX_MARKDOWN_COUNT = 1200


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _is_scan_ignored(path: Path) -> bool:
    return any(part in _IGNORED_DIRS for part in path.parts)


def _bounded_markdown_count(folder: Path) -> tuple[int, bool]:
    if not folder.is_dir():
        return 0, False
    count = 0
    truncated = False
    for md_path in folder.rglob("*.md"):
        if not md_path.is_file():
            continue
        if _is_scan_ignored(md_path.relative_to(folder)):
            continue
        if count >= _MAX_MARKDOWN_COUNT:
            truncated = True
            break
        count += 1
    return count, truncated


def infer_compatibility_types(folder_path: str | Path) -> dict:
    """
    Best-effort node-type inference for a non-ChaseOS vault.
    Infers node family from path patterns, directory names, and filename conventions.
    Returns a sample of typed nodes for compatibility-mode graph rendering.
    Read-only: inspects paths only, does not read file contents.
    """
    root = Path(folder_path).resolve()
    if not root.exists() or not root.is_dir():
        return {"ok": False, "error": "folder_not_found", "nodes": [], "type_counts": {}}

    nodes: list[dict] = []
    type_counts: dict[str, int] = {}
    truncated = False
    total = 0

    for md_path in root.rglob("*.md"):
        if not md_path.is_file():
            continue
        if _is_scan_ignored(md_path.relative_to(root)):
            continue
        if total >= _MAX_COMPAT_SCAN:
            truncated = True
            break
        total += 1

        rel = _rel(md_path, root)
        rel_posix = rel.replace("\\", "/")
        node_type = "markdown_note"
        label = "Markdown note"

        for rule in _NODE_TYPE_INFERENCE_RULES:
            if re.search(rule["pattern"], rel_posix):
                node_type = rule["node_type"]
                label = rule["label"]
                break

        type_counts[node_type] = type_counts.get(node_type, 0) + 1
        if len(nodes) < _MAX_COMPAT_SAMPLE:
            nodes.append({
                "path": rel,
                "node_type": node_type,
                "label": label,
                "stem": md_path.stem,
            })

    return {
        "ok": True,
        "total_scanned": total,
        "truncated": truncated,
        "scan_limit": _MAX_COMPAT_SCAN,
        "sample_limit": _MAX_COMPAT_SAMPLE,
        "nodes": nodes,
        "type_counts": type_counts,
        "dominant_type": max(type_counts, key=type_counts.get) if type_counts else None,
    }


def _detect_mode(folder: Path) -> str:
    if not folder.exists():
        return "invalid_missing"
    if not folder.is_dir():
        return "invalid_not_directory"

    present_dirs = sum(1 for d in _CHASEOS_DIRS if (folder / d).exists())
    present_files = sum(1 for f in _CHASEOS_FILES if (folder / f).exists())

    if present_dirs >= len(_CHASEOS_DIRS) and present_files >= len(_CHASEOS_FILES):
        return "chaseos_native"
    if present_dirs >= 3 or present_files >= 2:
        return "chaseos_partial"
    if (folder / ".obsidian").is_dir() or any(folder.glob("*.md")):
        return "general_markdown"
    return "empty_or_unknown"


def _missing_dirs(folder: Path) -> list[str]:
    return [d for d in _CHASEOS_DIRS if not (folder / d).exists()]


def _missing_files(folder: Path) -> list[str]:
    return [f for f in _CHASEOS_FILES if not (folder / f).exists()]


def _upgrade_recommendations(folder: Path, mode: str) -> list[dict]:
    if mode == "chaseos_native":
        return []
    recs: list[dict] = []
    missing_d = _missing_dirs(folder)
    missing_f = _missing_files(folder)
    if missing_d:
        recs.append({
            "id": "add-missing-dirs",
            "title": f"Create {len(missing_d)} missing ChaseOS director{'ies' if len(missing_d)!=1 else 'y'}",
            "items": missing_d,
            "priority": "high" if len(missing_d) > 5 else "medium",
        })
    if missing_f:
        recs.append({
            "id": "add-missing-files",
            "title": f"Create {len(missing_f)} missing ChaseOS anchor file{'s' if len(missing_f)!=1 else ''}",
            "items": missing_f,
            "priority": "high",
        })
    if not (folder / "CLAUDE.md").exists():
        recs.append({
            "id": "add-claude-md",
            "title": "Create CLAUDE.md routing anchor",
            "items": ["CLAUDE.md"],
            "priority": "high",
        })
    if not (folder / "00_HOME" / "Assistant-Contract.md").exists():
        recs.append({
            "id": "add-assistant-contract",
            "title": "Create Assistant Contract",
            "items": ["00_HOME/Assistant-Contract.md"],
            "priority": "medium",
        })
    return recs


def scan_folder_for_import(folder_path: str | Path) -> dict:
    """
    Run a complete import-readiness scan for a given folder.
    Returns mode, shape analysis, upgrade recommendations, and compatibility analysis.
    Read-only: no writes.
    """
    folder = Path(folder_path).resolve()
    mode = _detect_mode(folder)

    present_dirs = [d for d in _CHASEOS_DIRS if (folder / d).exists()]
    present_files = [f for f in _CHASEOS_FILES if (folder / f).exists()]
    missing_dirs = _missing_dirs(folder)
    missing_files = _missing_files(folder)

    compat_analysis: dict | None = None
    if mode in {"general_markdown", "chaseos_partial"}:
        compat_analysis = infer_compatibility_types(folder)

    upgrade_recs = _upgrade_recommendations(folder, mode)

    md_count, md_count_truncated = _bounded_markdown_count(folder)
    has_obsidian = (folder / ".obsidian").is_dir() if folder.is_dir() else False

    return {
        "ok": mode not in {"invalid_missing", "invalid_not_directory"},
        "folder": str(folder),
        "mode": mode,
        "mode_label": {
            "chaseos_native": "ChaseOS Native",
            "chaseos_partial": "ChaseOS Partial",
            "general_markdown": "General Markdown / Obsidian",
            "empty_or_unknown": "Empty / Unknown",
            "invalid_missing": "Folder Not Found",
            "invalid_not_directory": "Not a Directory",
        }.get(mode, mode),
        "relaunch_command": f"chaseos studio shell --vault-root \"{folder}\"" if mode in {"chaseos_native", "chaseos_partial", "general_markdown"} else None,
        "shape": {
            "present_dirs": present_dirs,
            "missing_dirs": missing_dirs,
            "present_files": present_files,
            "missing_files": missing_files,
        },
        "signals": {
            "markdown_file_count": md_count,
            "markdown_count_truncated": md_count_truncated,
            "markdown_count_limit": _MAX_MARKDOWN_COUNT,
            "has_obsidian_config": has_obsidian,
        },
        "upgrade_recommendations": upgrade_recs,
        "compatibility_analysis": compat_analysis,
        "warnings": (
            ["chaseos-structure-incomplete"] if missing_dirs or missing_files else []
        ),
    }


def get_bootstrap_wizard_plan(target_dir: str | Path, workspace_name: str = "my-chaseos-vault") -> dict:
    """
    Return the read-only bootstrap wizard step plan for creating a new ChaseOS workspace.
    Does not create any files. Shows what would be done.
    """
    target = Path(target_dir).resolve()
    existing = [s for s in _BOOTSTRAP_STEPS if (target / (s["writes"][0].rstrip("/"))).exists()]
    pending = [s for s in _BOOTSTRAP_STEPS if s["id"] not in {e["id"] for e in existing}]

    return {
        "ok": True,
        "target_dir": str(target),
        "workspace_name": workspace_name,
        "total_steps": len(_BOOTSTRAP_STEPS),
        "completed_steps": len(existing),
        "pending_steps": len(pending),
        "steps": _BOOTSTRAP_STEPS,
        "existing_step_ids": [s["id"] for s in existing],
        "cli_launch_command": f"chaseos studio shell --vault-root \"{target}\"",
        "authority": {
            "read_only": True,
            "writes_performed": False,
            "writes_require": "governed_executor_or_operator_confirmation",
        },
    }
