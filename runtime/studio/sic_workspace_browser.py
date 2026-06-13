"""
studio/sic_workspace_browser.py — Studio SIC Workspace Browser

Read-only surface for browsing Source Intelligence Core (SIC) workspaces:
  - list all workspaces with summary metadata
  - inspect a single workspace (sources, index status, outputs)
  - search sources within a workspace by title, type, or domain

Governance:
  - Read-only: no workspace mutations, no index modifications
  - Does not trigger retrieval, embedding, or any SIC pipeline
  - Source package content never surfaced — only metadata/refs
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

_BOUNDARY = {
    "reads_workspace_files": True,
    "writes_workspace_files": False,
    "triggers_retrieval": False,
    "canonical_mutation_allowed": False,
}

_SIC_WORKSPACES_DIR = "runtime/source_intelligence/workspaces"
_WORKSPACE_FILENAME = "workspace.json"


def _load_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _summarize_workspace(ws: dict) -> dict[str, Any]:
    return {
        "slug": ws.get("slug"),
        "name": ws.get("name"),
        "description": ws.get("description"),
        "status": ws.get("status"),
        "domain": ws.get("domain"),
        "source_count": ws.get("source_count", 0),
        "index_status": ws.get("index_status"),
        "last_indexed_at": ws.get("last_indexed_at"),
        "output_count": ws.get("output_count", 0),
        "tags": ws.get("tags", []),
        "created_at": ws.get("created_at"),
        "updated_at": ws.get("updated_at"),
    }


def _summarize_source_ref(ref: dict) -> dict[str, Any]:
    return {
        "source_package_id": ref.get("source_package_id"),
        "title": ref.get("title"),
        "source_type": ref.get("source_type"),
        "domain": ref.get("domain"),
        "chunk_count": ref.get("chunk_count", 0),
        "extraction_status": ref.get("extraction_status"),
        "injection_scan_status": ref.get("injection_scan_status"),
        "user_trust_level": ref.get("user_trust_level"),
        "embedding_status": ref.get("embedding_status"),
        "package_created_date": ref.get("package_created_date"),
        "added_at": ref.get("added_at"),
    }


def _match_source(ref: dict, query: str) -> bool:
    q = query.lower()
    title = (ref.get("title") or "").lower()
    source_type = (ref.get("source_type") or "").lower()
    domain = (ref.get("domain") or "").lower()
    return q in title or q in source_type or q in domain


# ── Public API ────────────────────────────────────────────────────────────────

def list_sic_workspaces(vault_root: str | Path) -> dict[str, Any]:
    """
    List all SIC workspaces with summary metadata.
    """
    vault = Path(vault_root).resolve()
    workspaces_dir = vault / _SIC_WORKSPACES_DIR

    if not workspaces_dir.exists():
        return {
            "ok": True,
            "surface": "studio_sic_workspace_browser",
            "workspaces": [],
            "workspace_count": 0,
            "boundary": _BOUNDARY,
        }

    workspaces = []
    for d in sorted(workspaces_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("_") or d.name.startswith("."):
            continue
        ws_file = d / _WORKSPACE_FILENAME
        ws = _load_json(ws_file)
        if ws is None:
            continue
        workspaces.append(_summarize_workspace(ws))

    return {
        "ok": True,
        "surface": "studio_sic_workspace_browser",
        "workspaces": workspaces,
        "workspace_count": len(workspaces),
        "boundary": _BOUNDARY,
    }


def inspect_sic_workspace(
    vault_root: str | Path,
    workspace_slug: str,
) -> dict[str, Any]:
    """
    Return a detailed inspection model for a single SIC workspace.

    Includes all source refs (summarized), index info, and output list.
    Missing workspace returns ok=False.
    """
    vault = Path(vault_root).resolve()
    ws_dir = vault / _SIC_WORKSPACES_DIR / workspace_slug
    ws_file = ws_dir / _WORKSPACE_FILENAME

    if not ws_dir.exists() or not ws_file.exists():
        return {
            "ok": False,
            "error": f"Workspace '{workspace_slug}' not found.",
            "surface": "studio_sic_workspace_browser",
            "workspace_slug": workspace_slug,
            "boundary": _BOUNDARY,
        }

    ws = _load_json(ws_file)
    if ws is None:
        return {
            "ok": False,
            "error": f"workspace.json for '{workspace_slug}' could not be loaded.",
            "surface": "studio_sic_workspace_browser",
            "workspace_slug": workspace_slug,
            "boundary": _BOUNDARY,
        }

    source_refs_raw = ws.get("source_refs", {})
    source_refs = [_summarize_source_ref(ref) for ref in source_refs_raw.values()]

    return {
        "ok": True,
        "surface": "studio_sic_workspace_browser",
        "workspace_slug": workspace_slug,
        "id": ws.get("id"),
        "name": ws.get("name"),
        "description": ws.get("description"),
        "status": ws.get("status"),
        "domain": ws.get("domain"),
        "tags": ws.get("tags", []),
        "source_count": ws.get("source_count", 0),
        "source_refs": source_refs,
        "index_status": ws.get("index_status"),
        "index_path": ws.get("index_path"),
        "last_indexed_at": ws.get("last_indexed_at"),
        "embedding_model": ws.get("embedding_model"),
        "retrieval_top_k": ws.get("retrieval_top_k"),
        "output_count": ws.get("output_count", 0),
        "outputs": ws.get("outputs", []),
        "default_promotion_target": ws.get("default_promotion_target"),
        "promotion_requires_review": ws.get("promotion_requires_review"),
        "created_at": ws.get("created_at"),
        "updated_at": ws.get("updated_at"),
        "boundary": _BOUNDARY,
    }


def search_sic_sources(
    vault_root: str | Path,
    workspace_slug: str,
    query: str,
) -> dict[str, Any]:
    """
    Search source refs within a workspace by title, type, or domain.

    Case-insensitive substring match. Returns matching source summaries.
    """
    vault = Path(vault_root).resolve()
    ws_dir = vault / _SIC_WORKSPACES_DIR / workspace_slug
    ws_file = ws_dir / _WORKSPACE_FILENAME

    if not ws_dir.exists() or not ws_file.exists():
        return {
            "ok": False,
            "error": f"Workspace '{workspace_slug}' not found.",
            "surface": "studio_sic_workspace_browser",
            "workspace_slug": workspace_slug,
            "query": query,
            "boundary": _BOUNDARY,
        }

    ws = _load_json(ws_file)
    if ws is None:
        return {
            "ok": False,
            "error": f"workspace.json for '{workspace_slug}' could not be loaded.",
            "surface": "studio_sic_workspace_browser",
            "workspace_slug": workspace_slug,
            "query": query,
            "boundary": _BOUNDARY,
        }

    source_refs_raw = ws.get("source_refs", {})
    matches = [
        _summarize_source_ref(ref)
        for ref in source_refs_raw.values()
        if _match_source(ref, query)
    ]

    return {
        "ok": True,
        "surface": "studio_sic_workspace_browser",
        "workspace_slug": workspace_slug,
        "query": query,
        "matches": matches,
        "match_count": len(matches),
        "total_sources": ws.get("source_count", 0),
        "boundary": _BOUNDARY,
    }
