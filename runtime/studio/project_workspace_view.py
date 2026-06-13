"""Read-only Studio project/workspace view.

Reads 01_PROJECTS/ to build a domain-grouped project list.
Reads 00_HOME/Now.md for the current sprint focus block.
No vault writes, no provider calls, no connector calls.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


MODEL_VERSION = "studio.project_workspace_view.v1"
SURFACE_ID = "studio_project_workspace_view"
PANEL_ID = "studio-project-workspace"
ROUTE_HINT = "#projects"
TITLE = "ChaseOS Studio Project Workspace"

_PROJECTS_DIR = "01_PROJECTS"
_NOW_PATH = "00_HOME/Now.md"
_FM_FENCE = re.compile(r"^---\s*$", re.MULTILINE)
_FIELD_RE = {
    "project": re.compile(r"^project:\s*(.+)$", re.MULTILINE | re.IGNORECASE),
    "domain": re.compile(r"^domain:\s*(.+)$", re.MULTILINE | re.IGNORECASE),
    "status": re.compile(r"^status:\s*(.+)$", re.MULTILINE | re.IGNORECASE),
    "updated": re.compile(r"^updated:\s*(.+)$", re.MULTILINE | re.IGNORECASE),
    "type": re.compile(r"^type:\s*(.+)$", re.MULTILINE | re.IGNORECASE),
}


def _extract_frontmatter(text: str) -> str:
    parts = _FM_FENCE.split(text, maxsplit=2)
    return parts[1] if len(parts) >= 3 else ""


def _fm_val(field: str, fm: str) -> str | None:
    m = _FIELD_RE[field].search(fm)
    return m.group(1).strip() if m else None


def _parse_project_os(file_path: Path) -> dict[str, Any]:
    try:
        text = file_path.read_text(encoding="utf-8")
    except Exception:
        return {
            "project": file_path.parent.name,
            "domain": "unknown",
            "status": "unknown",
            "updated": None,
            "file_name": file_path.name,
            "parse_error": True,
        }
    fm = _extract_frontmatter(text)
    return {
        "project": _fm_val("project", fm) or file_path.parent.name,
        "domain": _fm_val("domain", fm) or "unknown",
        "status": (_fm_val("status", fm) or "unknown").strip(),
        "updated": _fm_val("updated", fm),
        "file_name": file_path.name,
        "parse_error": False,
    }


def _read_sprint_focus(vault: Path) -> str | None:
    now_path = vault / _NOW_PATH
    if not now_path.exists():
        return None
    try:
        lines = now_path.read_text(encoding="utf-8").splitlines()
        in_section = False
        section: list[str] = []
        for line in lines[:150]:
            if re.match(r"^##\s+Current Phase", line):
                in_section = True
                section.append(line)
                continue
            if in_section:
                if line.startswith("## ") and not re.match(r"^##\s+Current Phase", line):
                    break
                section.append(line)
        if section:
            return "\n".join(section).strip()
        return "\n".join(lines[:60]).strip() or None
    except Exception:
        return None


def build_project_workspace_view(vault_root: str | Path) -> dict[str, Any]:
    """Return a domain-grouped project list with sprint focus from Now.md.

    Reads 01_PROJECTS/ directory and 00_HOME/Now.md only. No writes.
    """
    vault = Path(vault_root).resolve()
    projects_dir = vault / _PROJECTS_DIR
    projects: list[dict[str, Any]] = []
    warnings: list[str] = []

    if not projects_dir.exists():
        warnings.append("01_PROJECTS_dir_missing")
    else:
        for domain_folder in sorted(projects_dir.iterdir()):
            if not domain_folder.is_dir():
                continue
            os_files = sorted(domain_folder.glob("*-OS.md"))
            if not os_files:
                continue
            record = _parse_project_os(os_files[0])
            record["domain_folder"] = domain_folder.name
            projects.append(record)

    # Group by domain label
    domain_map: dict[str, list[dict]] = {}
    for proj in projects:
        key = proj.get("domain") or "unknown"
        domain_map.setdefault(key, []).append(proj)

    domains = [
        {"domain": k, "projects": v, "project_count": len(v)}
        for k, v in sorted(domain_map.items())
    ]

    sprint_focus = _read_sprint_focus(vault)
    active_count = sum(1 for p in projects if "active" in p.get("status", "").lower())
    paused_count = sum(
        1 for p in projects
        if any(kw in p.get("status", "").lower() for kw in ("pause", "parked", "deferred"))
    )
    parse_error_count = sum(1 for p in projects if p.get("parse_error") is True)
    if parse_error_count:
        warnings.append("project_os_parse_errors_present")

    empty_state = {
        "is_empty": len(projects) == 0,
        "message": (
            "No project OS records were found in 01_PROJECTS; Studio can only inspect the workspace until lower-phase project/write contracts exist."
            if len(projects) == 0
            else "Project map is available for read-only Studio inspection; workspace/project writes remain blocked."
        ),
    }
    authority = {
        "read_only": True,
        "writes_vault": False,
        "provider_calls_allowed": False,
        "connector_calls_allowed": False,
        "gate_mutation_allowed": False,
        "canonical_writeback_allowed": False,
        "project_status_mutation_allowed": False,
        "source_pack_promotion_allowed": False,
    }

    return {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "title": TITLE,
        "surface_label": "Project Workspace",
        "panel_id": PANEL_ID,
        "route_hint": ROUTE_HINT,
        "vault_root": str(vault),
        "sprint_focus": sprint_focus,
        "sprint_focus_source": str(vault / _NOW_PATH),
        "project_count": len(projects),
        "active_count": active_count,
        "paused_count": paused_count,
        "parse_error_count": parse_error_count,
        "domain_count": len(domains),
        "domains": domains,
        "projects": projects,
        "warnings": warnings,
        "empty_state": empty_state,
        "authority": authority,
        "allowed_actions": ["inspect-project-workspace-readiness"],
        "possible_writes": [],
        "readiness": {
            "projects_dir_found": projects_dir.exists(),
            "now_md_found": (vault / _NOW_PATH).exists(),
            "sprint_focus_available": sprint_focus is not None,
            "project_count_ok": len(projects) > 0,
            "read_only": True,
            "writes_vault": False,
            "provider_calls": False,
            "connector_calls": False,
        },
    }
