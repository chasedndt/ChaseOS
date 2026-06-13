"""ChaseOS Studio — write surface helpers (Pass 10C).

Pure functions for building vault-safe markdown content and resolving write targets.
No I/O — all output is passed to StudioService by the caller.

Runtime identity: Archon / Claude Code Engineering Runtime
"""
from __future__ import annotations

import re
import yaml
from datetime import date
from pathlib import Path
from typing import Any


# ── Slug / filename helpers ───────────────────────────────────────────────────

def slug_title(title: str) -> str:
    """Convert a title to a vault-safe filename stem."""
    s = title.strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = s.strip("-").lower()
    return s[:80] or "untitled"


# ── Target path routing ───────────────────────────────────────────────────────

_NODE_TYPE_PATH_MAP: dict[str, str] = {
    "project":           "01_PROJECTS/{domain}",
    "project_doc":       "01_PROJECTS/{domain}",
    "domain":            "02_KNOWLEDGE/{domain}",
    "knowledge":         "02_KNOWLEDGE/{domain}",
    "knowledge_doc":     "02_KNOWLEDGE/{domain}",
    "source":            "02_KNOWLEDGE/{domain}",
    "synthesis":         "02_KNOWLEDGE/{domain}",
    "sop_template":      "04_SOPS",
    "workflow":          "04_SOPS/{domain}",
    "decision":          "07_LOGS/Decision-Ledger",
    "log_audit":         "07_LOGS/Build-Logs",
    "intake":            "03_INPUTS/00_QUARANTINE/generated",
    "generated_artifact":"03_INPUTS/00_QUARANTINE/ai-generated",
    "agent":             "06_AGENTS",
}

_DEFAULT_PATH_TEMPLATE = "02_KNOWLEDGE/{domain}"


def build_target_path(node_type: str, title: str, domain: str = "general") -> str:
    """Return the relative vault path for a new node of the given type."""
    safe_domain = slug_title(domain) or "general"
    template = _NODE_TYPE_PATH_MAP.get(node_type, _DEFAULT_PATH_TEMPLATE)
    folder = template.format(domain=safe_domain)
    filename = slug_title(title) + ".md"
    return f"{folder}/{filename}"


# ── Content builders ──────────────────────────────────────────────────────────

def build_knowledge_note(
    title: str,
    node_type: str = "knowledge_doc",
    domain: str = "general",
    tags: list[str] | None = None,
    project: str | None = None,
    created_by: str = "archon",
) -> str:
    """Build frontmatter + body for a new vault note."""
    today = date.today().isoformat()
    frontmatter: dict[str, Any] = {
        "title": title,
        "node_type": node_type,
        "domain": domain,
        "trust_state": "raw",
        "created": today,
        "modified": today,
        "created_by": created_by,
        "runtime_node": "[[Archon-Runtime-Profile]]",
    }
    if tags:
        frontmatter["tags"] = [t.strip() for t in tags if t.strip()]
    if project:
        frontmatter["project"] = project

    fm_str = yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return f"---\n{fm_str}---\n\n# {title}\n\n"


def build_link_note_patch(existing_content: str, target_title: str) -> str:
    """Append a wikilink to an existing markdown file's content."""
    link = f"- [[{target_title}]]"
    if existing_content.endswith("\n"):
        return existing_content + link + "\n"
    return existing_content + "\n" + link + "\n"


# ── Frontmatter patching ──────────────────────────────────────────────────────

_FM_FENCE_RE = re.compile(r"^---\n(.+?)---\n", re.DOTALL)


def patch_frontmatter(content: str, updates: dict[str, Any]) -> str:
    """
    Update YAML frontmatter fields in an existing markdown file.
    Preserves the body. Adds fields that don't exist. Removes fields whose
    value is explicitly set to None.
    """
    match = _FM_FENCE_RE.match(content)
    if not match:
        # No frontmatter — prepend it
        fm_str = yaml.dump(updates, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return f"---\n{fm_str}---\n\n{content}"

    existing_yaml = match.group(1)
    body = content[match.end():]
    try:
        fm: dict = yaml.safe_load(existing_yaml) or {}
    except yaml.YAMLError:
        fm = {}

    for k, v in updates.items():
        if v is None:
            fm.pop(k, None)
        else:
            fm[k] = v

    fm_str = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return f"---\n{fm_str}---\n{body}"


# ── Node file resolution ──────────────────────────────────────────────────────

def resolve_node_file_path(vault_root: Path, node_id: str) -> Path | None:
    """
    Try to resolve a node_id to its vault file.

    Tries the graph index stable_key → file path mapping first.
    Falls back to a direct vault glob for filenames containing the ID suffix.
    Returns None if no match found.
    """
    vault_root = vault_root.resolve()

    # Attempt 1: parse stable_key suffix as a relative path hint
    # stable_key format: "chaseos:path:{hex}" or "chaseos:{rel_path}"
    parts = str(node_id).split(":", 2)
    if len(parts) >= 3:
        path_part = parts[2]
        # Decode URL-encoded path
        from urllib.parse import unquote
        decoded = unquote(path_part.replace("--", "/"))
        candidate = vault_root / decoded
        if candidate.exists() and candidate.is_file():
            return candidate
        # Try with .md suffix
        candidate_md = vault_root / (decoded + ".md")
        if candidate_md.exists():
            return candidate_md

    # Attempt 2: search graph index snapshot
    try:
        from runtime.studio.graph_view import _load_snapshot
        snapshot = _load_snapshot(vault_root)
        nodes = snapshot.get("nodes", [])
        for n in nodes:
            if str(n.get("id", "")) == str(node_id):
                path_val = (n.get("properties") or {}).get("path") or n.get("path")
                if path_val:
                    candidate = vault_root / path_val
                    if candidate.exists():
                        return candidate
    except Exception:
        pass

    return None
