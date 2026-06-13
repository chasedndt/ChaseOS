"""ChaseOS Vault Hygiene — Loose Node Fixer + Graph Wiring Tool.

Scans the entire vault for:
  1. Loose markdown nodes not wikilinked from their parent index
  2. Backtick-wrapped wikilinks that Obsidian ignores for graph edges
  3. Orphan files at the vault root that don't belong
  4. Files in architecture-governed folders without proper routing
  5. Junk/placeholder files (empty canvases, duplicate transcripts, etc.)

For every issue found the script either:
  - AUTO-FIXES it (wires the node, strips backticks), or
  - FLAGS it in a human-review report for deletion/move

Uses the ChaseOS Runtime MCP audit logger to record all mutations.

Usage:
    python -m runtime.cli.vault_hygiene                     # dry-run (report only)
    python -m runtime.cli.vault_hygiene --fix               # apply fixes
    python -m runtime.cli.vault_hygiene --fix --delete-junk # apply fixes and delete confirmed junk
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Vault root detection
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
VAULT_ROOT = SCRIPT_DIR.parents[1]  # runtime/cli -> runtime -> vault root

if not (VAULT_ROOT / "CLAUDE.md").exists():
    print(f"ERROR: Could not find CLAUDE.md at {VAULT_ROOT}", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# MCP audit integration
# ---------------------------------------------------------------------------

sys.path.insert(0, str(VAULT_ROOT))


def _local_now() -> datetime:
    """Return an explicit timezone-aware local timestamp for operator-local file dating."""
    return datetime.now(timezone.utc).astimezone()


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)

try:
    from runtime.mcp.audit.logger import MCPAuditLogger
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

AUDIT_DIR = VAULT_ROOT / "07_LOGS" / "Agent-Activity"


def _mcp_audit(
    surface_id: str,
    outcome: str,
    files_read: list[str],
    files_written: list[str],
    detail: str | None = None,
) -> None:
    """Write an MCP audit record for a vault_hygiene mutation."""
    if not MCP_AVAILABLE:
        return
    logger = MCPAuditLogger(audit_dir=AUDIT_DIR)
    try:
        logger.log(
            request_id=f"req-{uuid.uuid4().hex[:12]}",
            surface_id=surface_id,
            surface_class="tool",
            runtime_id="vault_hygiene",
            trust_tier=1,
            safety_mode="draft_execution",
            outcome=outcome,
            outcome_detail=detail,
            files_read=files_read,
            files_written=files_written,
            error_code=None,
            error_message=None,
        )
    except Exception:
        pass  # fail-open: audit failure must not block hygiene
# ---------------------------------------------------------------------------
# Architecture ruleset -- folder -> index mapping
# ---------------------------------------------------------------------------

# Each entry: (folder_relative_path, index_filename, file_glob_pattern)
# The index file is expected to contain [[wikilinks]] to every .md file in the folder.
INDEXED_FOLDERS: list[tuple[str, str, str]] = [
    # -- 07_LOGS --
    ("07_LOGS/Build-Logs",            "Build-Logs-Index.md",            "*.md"),
    ("07_LOGS/Agent-Activity",        "Agent-Activity-Index.md",        "*.md"),
    ("07_LOGS/Daily",                 "Daily-Index.md",                 "*.md"),
    ("07_LOGS/Trading-Weekly",        "Trading-Weekly-Index.md",        "*.md"),
    ("07_LOGS/Trade-Journal",         "Trade-Journal-Index.md",         "*.md"),
    ("07_LOGS/Morning-Thesis",        "Morning-Thesis-Index.md",        "*.md"),
    ("07_LOGS/Decision-Ledger",       "Decision-Ledger-Index.md",       "*.md"),
    ("07_LOGS/Pivot-Log",             "Pivot-Log-Index.md",             "*.md"),
    ("07_LOGS/Hygiene-Reports",       "Hygiene-Reports-Index.md",       "*.md"),
    ("07_LOGS/Graduation-Proposals",  "Graduation-Proposals-Index.md",  "*.md"),
    ("07_LOGS/Operator-Briefs",       "Operator-Briefs-Index.md",       "*.md"),
    ("07_LOGS/Operator-Briefs/_drafts", "Drafts-Index.md",              "*.md"),
    ("07_LOGS/SBP-Runs",              "SBP-Runs-Index.md",              "*.md"),
    ("07_LOGS/Graph-Reports",         "Graph-Reports-Index.md",         "*.md"),
    ("07_LOGS/Graph-Snapshots",       "Graph-Snapshots-Index.md",       "*.md"),
    ("07_LOGS/Schedule-State",        "Schedule-State-Index.md",        "*.md"),
    ("07_LOGS/Maintain-Runs",         "Maintain-Runs-Index.md",         "*.md"),
    ("07_LOGS/Pulse-Decks",           "Pulse-Decks-Index.md",           "*.md"),
    ("07_LOGS/Studio-ARSL-Route-Review", "Studio-ARSL-Route-Review-Index.md", "*.md"),
    ("07_LOGS/Studio-Graph-Views",    "Studio-Graph-Views-Index.md",    "*.md"),
    ("07_LOGS/Browser-Runs",          "Browser-Runs-Index.md",          "*.md"),
    # -- 03_INPUTS --
    ("03_INPUTS/Digests",             "Digests-Index.md",               "*.md"),
    ("03_INPUTS/NotebookLM",          "NotebookLM-Index.md",            "*.md"),
    ("03_INPUTS/Transcript-Raw",      "Transcript-Raw-Index.md",        "*.md"),
    ("03_INPUTS/YouTube-Notes",       "YouTube-Notes-Index.md",         "*.md"),
    ("03_INPUTS/Sources",             "Sources-Index.md",               "*.md"),
    ("03_INPUTS/Clipboard",           "Clipboard-Index.md",             "*.md"),
    ("03_INPUTS/Journal-Raw",         "Journal-Raw-Index.md",           "*.md"),
    # -- 02_KNOWLEDGE --
    ("02_KNOWLEDGE",                  "Knowledge-Index.md",             "*.md"),
    # -- 99_ARCHIVE --
    ("99_ARCHIVE/Documentation-History", "Documentation-History-Index.md", "*.md"),
    ("99_ARCHIVE/Imported-Context",   "Imported-Context-Index.md",      "*.md"),
    ("99_ARCHIVE/Audits",             "Audits-Index.md",                "*.md"),
    ("99_ARCHIVE/Reporting",          "Reporting-Index.md",             "*.md"),
]

# Files to always skip (index files, READMEs that are index files, etc.)
ALWAYS_SKIP = {"README.md"}

# Folders that are NOT markdown content (skip entirely)
SKIP_DIRS = {
    ".obsidian", ".venv", ".claude", ".codex", ".codex-tmp", ".codex_tmp", ".codex_tmp_test",
    ".hermes", ".chaseos", ".pytest_cache", ".vscode", ".git",
    "__pycache__", "chaseos.egg-info", "node_modules", "build",
    "fixtures",
    "_tmp_tests", "_tmp_debug_closeout", "_tmp_acquisition_cockpit",
    # test fixture dirs -- never real vault content
    ".pytest_tmp_env", "pytest_tmp_env", ".pytest-tmp",
}

# Root-level files that are architecturally valid
VALID_ROOT_FILES = {
    "CLAUDE.md", "README.md", "ROADMAP.md", "PROJECT_FOUNDATION.md",
    "SOUL.md", "SOUL.template.md", "OPENAI.md", "LOCAL-OSS.md",
    "N8N.md", "OPENCLAW.md", "HERMES.md", "FORKING.md",
    "CORE_MANIFEST.md", "pyproject.toml", "chaseos.py",
    "AGENTS.md", "KNOWLEDGE-INDEX.md", "CLI-INSTALL-README.md",
    "NEXT-STEPS.md", "OPERATOR-BRIEF-INDEX.md", "RUNTIME-REGISTRY.md",
    "SETUP-INSTRUCTIONS.md", "STRIKEZONE-DISCORD-SETUP.md", "SYSTEM-STATUS.md",
    "uv.lock",
}


# Anchor documents: these are the canonical routing surfaces that should link
# to every file in their respective domains. If a file in one of these folders
# is orphaned, we wire it into the anchor.
ANCHOR_DOCS: dict[str, str] = {
    # folder prefix -> anchor file (relative to vault root)
    "06_AGENTS/":          "06_AGENTS/Vault-Map.md",
    "04_SOPS/":            "06_AGENTS/Vault-Map.md",
    "05_TEMPLATES/":       "06_AGENTS/Vault-Map.md",
    "00_HOME/":            "06_AGENTS/Vault-Map.md",
    "07_LOGS/":            "06_AGENTS/Vault-Map.md",
    "03_INPUTS/":          "06_AGENTS/Vault-Map.md",
    "02_KNOWLEDGE/":       "06_AGENTS/Vault-Map.md",
    "01_PROJECTS/":        "00_HOME/Dashboard.md",
    "99_ARCHIVE/":         "06_AGENTS/Vault-Map.md",
    "docs/":               "06_AGENTS/Vault-Map.md",
    "core_export/":        "06_AGENTS/Vault-Map.md",
    "core_templates/":     "06_AGENTS/Vault-Map.md",
    "runtime/openclaw/":   "06_AGENTS/OpenClaw-Runtime-Profile.md",
    "runtime/hermes/":     "06_AGENTS/Hermes-Runtime-Profile.md",
    "runtime/":            "runtime/README.md",
}

# Paths that are real files but should not be blindly wired into canonical
# operator navigation. They are generated/export/fixture-like surfaces that need
# classification, not generic graph repair.
REVIEW_ONLY_PREFIXES = (
    "core_export/",
    "core_templates/",
    "runtime/adapters/codex/runs/",
    "runtime/acquisition/_tmp_research_import_preview/",
)

CANONICAL_DUPLICATE_TARGETS = {
    "Agent-Control-Plane": "06_AGENTS/Agent-Control-Plane.md",
    "Adapter-Compliance-Checklist": "05_TEMPLATES/Adapter-Compliance-Checklist.md",
    "Adapter-Manifest-Standard": "06_AGENTS/Adapter-Manifest-Standard.md",
    "Agent-Audit-Log-Template": "05_TEMPLATES/Agent-Audit-Log-Template.md",
    "Agent-Failure-Ambiguity-SOP": "04_SOPS/Agent-Failure-Ambiguity-SOP.md",
    "Agent-Output-Conventions": "06_AGENTS/Agent-Output-Conventions.md",
    "Permission-Matrix": "06_AGENTS/Permission-Matrix.md",
    "Agent-Security-Model": "06_AGENTS/Agent-Security-Model.md",
    "Autonomous-Operator-Runtime": "06_AGENTS/Autonomous-Operator-Runtime.md",
    "Build-Log-SOP": "04_SOPS/Build-Log-SOP.md",
    "Trust-Tiers": "06_AGENTS/Trust-Tiers.md",
    "Vault-Map": "06_AGENTS/Vault-Map.md",
    "Agent-Registry": "06_AGENTS/Agent-Registry.md",
    "Backends-Supported": "06_AGENTS/Backends-Supported.md",
    "ChaseOS-Gate": "06_AGENTS/ChaseOS-Gate.md",
    "Credential-Boundaries-SOP": "04_SOPS/Credential-Boundaries-SOP.md",
    "Daily-Note-Template": "05_TEMPLATES/Daily-Note-Template.md",
    "Decision-Ledger-Entry-Template": "05_TEMPLATES/Decision-Ledger-Entry-Template.md",
    "Execution-Adapter-Standard": "06_AGENTS/Execution-Adapter-Standard.md",
    "Generated-Idea-Template": "05_TEMPLATES/Generated-Idea-Template.md",
    "Ingestion-Architecture": "06_AGENTS/Ingestion-Architecture.md",
    "Knowledge-Taxonomy": "06_AGENTS/Knowledge-Taxonomy.md",
    "Operator-Run-Audit-Template": "05_TEMPLATES/Operator-Run-Audit-Template.md",
    "Project-OS-Template": "05_TEMPLATES/Project-OS-Template.md",
    "Promotion-Session-SOP": "04_SOPS/Promotion-Session-SOP.md",
    "Research-Ingest-SOP": "04_SOPS/Research-Ingest-SOP.md",
    "Runtime-InterAgent-Coordination-Bus": "06_AGENTS/Runtime-InterAgent-Coordination-Bus.md",
    "SIC-Architecture": "06_AGENTS/SIC-Architecture.md",
    "Source-Note-Template": "05_TEMPLATES/Source-Note-Template.md",
    "Synthesis-Note-Template": "05_TEMPLATES/Synthesis-Note-Template.md",
    "Untrusted-Input-Handling-SOP": "04_SOPS/Untrusted-Input-Handling-SOP.md",
    "ROADMAP": "ROADMAP.md",
    "PROJECT_FOUNDATION": "PROJECT_FOUNDATION.md",
}

REVIEW_QUEUE_CATEGORIES = {
    "duplicate_candidate",
    "review_only_artifact",
    "technical_readme_loose",
    "runtime_markdown_loose",
    "empty_placeholder",
    "orphan_root",
    "junk",
}

DECISION_REGISTRY_REL = "runtime/graph/vault_hygiene_decisions.json"
DECISION_LOG_DIR_REL = "07_LOGS/Graph-Reports/Decision-Logs"
ARCHIVE_REVIEW_REL = "99_ARCHIVE/Vault-Hygiene-Review"
NONCANONICAL_ARTIFACT_ARCHIVE_REL = f"{ARCHIVE_REVIEW_REL}/Noncanonical-Artifacts"
NONCANONICAL_ARTIFACT_INDEX_REL = f"{NONCANONICAL_ARTIFACT_ARCHIVE_REL}/Noncanonical-Artifacts-Index.md"
REPLACED_DUPLICATES_INDEX_REL = f"{ARCHIVE_REVIEW_REL}/Replaced-Duplicates/Replaced-Duplicates-Index.md"
KEEP_EXCLUDED_INDEX_REL = f"{ARCHIVE_REVIEW_REL}/Keep-Excluded/Keep-Excluded-Index.md"
STRIKEZONE_RSS_STAGING_INDEX_REL = "runtime/acquisition/staging/strikezone/StrikeZone-RSS-Staging-Index.md"

ALLOWED_REVIEW_DECISIONS = {
    "keep_and_wire",
    "keep_excluded",
    "archive_after_review",
    "archive_noncanonical_artifact",
    "delete_after_review",
    "replace_with_canonical",
    "manual_investigation",
}

DESTRUCTIVE_REVIEW_DECISIONS = {
    "archive_after_review",
    "archive_noncanonical_artifact",
    "delete_after_review",
    "replace_with_canonical",
}

DEFAULT_PROPOSAL_CATEGORIES = (
    "duplicate_candidate",
    "empty_placeholder",
    "junk",
    "review_only_artifact",
    "technical_readme_loose",
    "runtime_markdown_loose",
)

PROTECTED_DESTRUCTIVE_PATHS = {
    "README.md",
    "PROJECT_FOUNDATION.md",
    "ROADMAP.md",
    "00_HOME/Now.md",
    "CLAUDE.md",
    "HERMES.md",
    "CODEX.md",
    "06_AGENTS/Agent-Control-Plane.md",
    "06_AGENTS/Permission-Matrix.md",
    "06_AGENTS/Trust-Tiers.md",
    "06_AGENTS/Vault-Map.md",
    "06_AGENTS/Agent-Registry.md",
    "06_AGENTS/Backends-Supported.md",
}

# File patterns that are confirmed junk (safe to flag for deletion)
JUNK_PATTERNS = [
    re.compile(r"^Untitled.*\.canvas$"),            # empty Obsidian canvases
    re.compile(r"^sample_transcript.*\.txt(\.txt)?$"),  # test artifacts
    re.compile(r"^\.DS_Store$"),
    re.compile(r"^Thumbs\.db$"),
    re.compile(r"^desktop\.ini$"),
]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Issue:
    """A single vault hygiene issue."""
    category: str       # "loose_node" | "backtick_wikilink" | "orphan_root" | "junk" | "graph_orphan"
    severity: str       # "auto_fix" | "review" | "junk"
    file_path: str      # relative to vault root
    index_path: str     # which index/anchor should own it (if applicable)
    description: str
    fixed: bool = False
    action: str = ""
    evidence: list[str] = field(default_factory=list)
    node_category: str = ""
    canonical_path: str = ""


@dataclass
class GraphFileState:
    """Resolved Obsidian-style graph state for one markdown file."""
    rel_path: str
    stem: str
    size_bytes: int
    inbound: set[str] = field(default_factory=set)
    outbound: set[str] = field(default_factory=set)
    unresolved_targets: set[str] = field(default_factory=set)
    ambiguous_targets: set[str] = field(default_factory=set)
    wikilink_count: int = 0
    heading_count: int = 0
    nonempty_line_count: int = 0


@dataclass
class HygieneReport:
    """Accumulated results of a vault hygiene scan."""
    issues: list[Issue] = field(default_factory=list)
    files_scanned: int = 0
    files_fixed: int = 0
    wikilinks_fixed: int = 0
    nodes_wired: int = 0
    junk_flagged: int = 0
    junk_deleted: int = 0
    indexes_created: int = 0
    review_artifacts: dict[str, str] = field(default_factory=dict)
    strict_gate_failed: bool = False
    strict_gate_review_count: int = 0
    strict_visible_graph_failed: bool = False
    strict_visible_graph_count: int = 0
    visible_graph_audit: dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionApplyResult:
    """Result of validating or applying operator loose-node decisions."""
    status: str
    executed: bool
    approval_preview_only: bool = False
    decisions_total: int = 0
    applied: int = 0
    skipped: int = 0
    blocked: int = 0
    files_written: list[str] = field(default_factory=list)
    files_deleted: list[str] = field(default_factory=list)
    files_moved: list[dict[str, str]] = field(default_factory=list)
    registry_path: str = DECISION_REGISTRY_REL
    decision_log_path: str = ""
    messages: list[dict[str, Any]] = field(default_factory=list)
    planned_actions: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "executed": self.executed,
            "approval_preview_only": self.approval_preview_only,
            "decisions_total": self.decisions_total,
            "applied": self.applied,
            "skipped": self.skipped,
            "blocked": self.blocked,
            "files_written": list(dict.fromkeys(self.files_written)),
            "files_deleted": list(dict.fromkeys(self.files_deleted)),
            "files_moved": self.files_moved,
            "registry_path": self.registry_path,
            "decision_log_path": self.decision_log_path,
            "messages": self.messages,
            "planned_actions": self.planned_actions,
        }


# ---------------------------------------------------------------------------
# Wikilink helpers
# ---------------------------------------------------------------------------

_WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
_BACKTICK_WIKILINK_RE = re.compile(r"`(\[\[[^\]]+\]\])`")
_BACKTICK_DATE_ENTRY_RE = re.compile(
    r"`((?:2\d{3}-\d{2}-\d{2}|antigravity)[^`]*?)(?:\.md)?`"
)


def extract_wikilink_stems(text: str) -> set[str]:
    """Return all [[target]] stems found in text (without .md extension)."""
    stems = set()
    for m in _WIKILINK_RE.finditer(text):
        target = m.group(1).split("|")[0].strip()  # handle [[target|alias]]
        if target.endswith(".md"):
            target = target[:-3]
        stems.add(target)
    return stems


def _wikilink_target_for_rel(rel_path: str) -> str:
    """Return a path-qualified wikilink target without the .md suffix."""
    norm = rel_path.replace("\\", "/")
    if norm.lower().endswith(".md"):
        norm = norm[:-3]
    return norm


def _wikilink_for_rel(rel_path: str, label: str | None = None) -> str:
    target = _wikilink_target_for_rel(rel_path)
    display = label or Path(rel_path).stem
    return f"[[{target}|{display}]]"


def _link_target_present(linked_targets: set[str], rel_path: str) -> bool:
    target = _wikilink_target_for_rel(rel_path)
    stem = Path(rel_path).stem
    return target in linked_targets or stem in linked_targets


def _split_wikilink_target(target: str) -> tuple[str, str, str]:
    """Return base target, heading suffix, and alias for a wikilink inner target."""
    target_part, alias = (target.split("|", 1) + [""])[:2] if "|" in target else (target, "")
    base, heading = (target_part.split("#", 1) + [""])[:2] if "#" in target_part else (target_part, "")
    return base.strip().replace("\\", "/").lstrip("./"), heading.strip(), alias.strip()


def _replace_wikilink_target(text: str, old_target: str, new_rel: str) -> tuple[str, int]:
    """Path-qualify exact wikilinks to a canonical target while preserving aliases."""
    old_base, _old_heading, _old_alias = _split_wikilink_target(old_target)
    canonical_target = _wikilink_target_for_rel(new_rel)
    count = 0

    def _replace(match: re.Match) -> str:
        nonlocal count
        inner = match.group(1)
        base, heading, alias = _split_wikilink_target(inner)
        if base != old_base:
            return match.group(0)
        target = canonical_target
        if heading:
            target = f"{target}#{heading}"
        display = alias or Path(base).name
        count += 1
        return f"[[{target}|{display}]]"

    return _WIKILINK_RE.sub(_replace, text), count


def file_sha256(path: Path) -> str:
    """Return SHA-256 for a file."""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_rel_path(rel_path: str) -> str:
    return rel_path.replace("\\", "/").lstrip("./")


def _resolve_within_vault(vault_root: Path, rel_path: str) -> Path:
    """Resolve a relative path and require that it stays inside the vault."""
    rel = _safe_rel_path(rel_path)
    if Path(rel).is_absolute() or rel.startswith("../") or "/../" in f"/{rel}/":
        raise ValueError(f"unsafe relative path: {rel_path}")
    root = vault_root.resolve()
    target = (root / rel).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes vault: {rel_path}") from exc
    return target


def strip_backtick_wikilinks(text: str) -> tuple[str, int]:
    """Convert `[[X]]` -> [[X]]. Returns (new_text, count_fixed)."""
    count = 0

    def _replace(m: re.Match) -> str:
        nonlocal count
        count += 1
        return m.group(1)

    result = _BACKTICK_WIKILINK_RE.sub(_replace, text)
    return result, count


def convert_backtick_entries_to_wikilinks(text: str) -> tuple[str, int]:
    """Convert `2026-MM-DD-filename.md` or `2026-MM-DD-filename` -> [[2026-MM-DD-filename]].

    Only matches date-prefixed entries typical of build logs, archive notes, etc.
    Returns (new_text, count_fixed).
    """
    count = 0

    def _replace(m: re.Match) -> str:
        nonlocal count
        stem = m.group(1)
        if stem.endswith(".md"):
            stem = stem[:-3]
        count += 1
        return f"[[{stem}]]"

    result = _BACKTICK_DATE_ENTRY_RE.sub(_replace, text)
    return result, count


# ---------------------------------------------------------------------------
# Index wiring
# ---------------------------------------------------------------------------

def compute_missing_from_index(
    folder_path: Path,
    index_path: Path,
    folder_rel: str,
    skip_names: set[str],
) -> tuple[list[str], str]:
    """Find files in folder_path not wikilinked from index_path.

    Returns (list_of_missing_stems, index_content).
    """
    if not index_path.exists():
        return [], ""

    try:
        index_content = index_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        index_content = index_path.read_text(encoding="utf-8", errors="replace")
    linked_stems = extract_wikilink_stems(index_content)

    # Also check for stems mentioned as backtick filenames (will be fixed later)
    backtick_stems: set[str] = set()
    for m in _BACKTICK_DATE_ENTRY_RE.finditer(index_content):
        s = m.group(1)
        if s.endswith(".md"):
            s = s[:-3]
        backtick_stems.add(s)

    all_linked = linked_stems | backtick_stems

    missing: list[str] = []
    for child in sorted(folder_path.iterdir()):
        if child.is_dir():
            continue
        if child.suffix not in (".md",):
            continue
        if child.name in skip_names or child.name == index_path.name:
            continue
        stem = child.stem
        rel_path = str(Path(folder_rel) / child.name).replace("\\", "/")
        if not _link_target_present(all_linked, rel_path):
            missing.append(stem)

    return missing, index_content


def generate_wiring_block(stems: list[str], folder_name: str) -> str:
    """Generate a markdown table block wiring loose nodes into the index."""
    dt = _local_now().strftime("%Y-%m-%d")
    lines = [
        "",
        "---",
        "",
        f"## Auto-Wired Entries ({dt} -- vault_hygiene)",
        "",
        "| Entry | Status |",
        "|-------|--------|",
    ]
    for stem in sorted(stems):
        lines.append(f"| [[{stem}]] | Auto-wired by vault_hygiene |")
    lines.append("")
    return "\n".join(lines)


def generate_path_wiring_block(rel_paths: list[str], folder_name: str) -> str:
    """Generate a markdown table block using path-qualified wikilinks."""
    dt = _local_now().strftime("%Y-%m-%d")
    lines = [
        "",
        "---",
        "",
        f"## Auto-Wired Entries ({dt} -- vault_hygiene)",
        "",
        "| Entry | Path | Status |",
        "|-------|------|--------|",
    ]
    for rel_path in sorted(rel_paths):
        lines.append(
            f"| {_wikilink_for_rel(rel_path)} | `{rel_path}` | Auto-wired by vault_hygiene |"
        )
    lines.append("")
    return "\n".join(lines)


def create_index_if_missing(folder_path: Path, index_name: str) -> bool:
    """Create a minimal index file if it doesn't exist. Returns True if created."""
    index_path = folder_path / index_name
    if index_path.exists():
        return False

    folder_label = folder_path.name
    dt = _local_now().strftime("%Y-%m-%d")
    content = f"""---
title: {folder_label} Index
type: index
created: {dt}
---

# {folder_label} Index

> Auto-generated index for `{folder_label}/`. Created by vault_hygiene on {dt}.

"""
    folder_path.mkdir(parents=True, exist_ok=True)
    index_path.write_text(content, encoding="utf-8")
    return True


# ---------------------------------------------------------------------------
# Full vault graph-based orphan detection
# ---------------------------------------------------------------------------

def _review_only_path(rel_path: str) -> bool:
    norm = rel_path.replace("\\", "/")
    return norm.startswith(REVIEW_ONLY_PREFIXES)


def _archive_review_path(rel_path: str) -> bool:
    norm = rel_path.replace("\\", "/")
    return norm == ARCHIVE_REVIEW_REL or norm.startswith(f"{ARCHIVE_REVIEW_REL}/")


def _archive_review_index_for(rel_path: str) -> str:
    norm = rel_path.replace("\\", "/")
    if norm.startswith(f"{NONCANONICAL_ARTIFACT_ARCHIVE_REL}/"):
        return NONCANONICAL_ARTIFACT_INDEX_REL
    if norm.startswith(f"{ARCHIVE_REVIEW_REL}/Replaced-Duplicates/"):
        return REPLACED_DUPLICATES_INDEX_REL
    if norm.startswith(f"{ARCHIVE_REVIEW_REL}/Keep-Excluded/"):
        return KEEP_EXCLUDED_INDEX_REL
    return "99_ARCHIVE/Documentation-History/Documentation-History-Index.md"


def _keep_excluded_index_header() -> str:
    dt = _local_now().strftime("%Y-%m-%d")
    return (
        "---\n"
        "title: Keep Excluded Graph Holding Index\n"
        "type: graph-hygiene-review-index\n"
        f"created: {dt}\n"
        "---\n\n"
        "# Keep Excluded Graph Holding Index\n\n"
        "> Hash-approved files listed here are kept outside canonical navigation "
        "but remain connected so the visible graph has no raw loose nodes.\n\n"
        "Governing links: [[Vault-Map]] . [[ChaseOS-Vault-Maintenance]] . "
        "[[Graph-Hygiene-CLI-and-OpenClaw-Cron-Runbook]]\n\n"
    )


def _strikezone_rss_staging_index_header() -> str:
    dt = _local_now().strftime("%Y-%m-%d")
    return (
        "---\n"
        "title: StrikeZone RSS Staging Index\n"
        "type: staged-source-index\n"
        "project: StrikeZone Crypto\n"
        "source_class: staged_capture\n"
        f"created: {dt}\n"
        "---\n\n"
        "# StrikeZone RSS Staging Index\n\n"
        "> Raw daily RSS captures for StrikeZone Crypto. These are upstream market-context "
        "inputs, not canonical trading notes or trade authority.\n\n"
        "Project links: [[StrikeZone-Crypto-OS]] . [[TradingSystems/TradingSystems-OS|Trading Systems / Market Ops]] . "
        "[[TradingSystems/CryptoPerps-OS|Crypto Perps]] . "
        "[[02_KNOWLEDGE/Trading-Systems/Trading-Systems-Engineering|Trading Systems Engineering]]\n\n"
        "Acquisition links: [[StrikeZone-Research-Import-Operator-Guide]] . "
        "[[ChaseOS-Vault-Maintenance]] . [[Graph-Hygiene-CLI-and-OpenClaw-Cron-Runbook]]\n\n"
    )


def _heading_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.lstrip().startswith("#"))


def _canonical_duplicate_evidence(vault_root: Path, canonical_target: str, candidate_size: int) -> list[str]:
    """Return evidence that helps the operator keep the canonical version."""
    canonical_path = vault_root / canonical_target
    if not canonical_path.exists():
        return [f"canonical_candidate={canonical_target}", "canonical_exists=false"]
    try:
        canonical_text = canonical_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        canonical_text = canonical_path.read_text(encoding="utf-8", errors="replace")
    canonical_size = canonical_path.stat().st_size
    evidence = [
        f"canonical_candidate={canonical_target}",
        "canonical_exists=true",
        f"canonical_size_bytes={canonical_size}",
        f"canonical_wikilinks={len(_WIKILINK_RE.findall(canonical_text))}",
        f"canonical_headings={_heading_count(canonical_text)}",
    ]
    if candidate_size and canonical_size > candidate_size:
        evidence.append("canonical_is_larger_than_candidate=true")
    return evidence


def _normalized_duplicate_key(path: Path) -> str:
    stem = path.stem
    for suffix in (".core", ".example", ".template"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
    return stem


def infer_node_category(rel_path: str) -> str:
    """Infer the ChaseOS bucket a markdown file most likely belongs to."""
    norm = rel_path.replace("\\", "/")
    name = Path(norm).name
    if norm in VALID_ROOT_FILES:
        return "root_canonical_doc"
    if norm.startswith("00_HOME/"):
        return "home_control_doc"
    if norm.startswith("01_PROJECTS/"):
        return "project_operating_doc"
    if norm.startswith("02_KNOWLEDGE/"):
        return "knowledge_doc"
    if norm.startswith("03_INPUTS/"):
        return "input_or_candidate_doc"
    if norm.startswith("04_SOPS/"):
        return "sop_doc"
    if norm.startswith("05_TEMPLATES/"):
        return "template_doc"
    if norm.startswith("06_AGENTS/Browser-Skills/_drafts/"):
        return "agent_draft_doc"
    if norm.startswith("06_AGENTS/"):
        if norm in set(CANONICAL_DUPLICATE_TARGETS.values()) or name in {
            "ChaseOS-Vault-Maintenance.md",
            "Codex-Runtime-Profile.md",
            "OpenClaw-Runtime-Profile.md",
            "Hermes-Runtime-Profile.md",
        }:
            return "agent_control_doc"
        if norm.startswith("06_AGENTS/runtime-profiles/") or name.endswith("-Runtime-Profile.md"):
            return "runtime_profile_doc"
        return "agent_draft_doc"
    if norm.startswith("07_LOGS/Build-Logs/"):
        return "build_log"
    if norm.startswith("07_LOGS/Agent-Activity/"):
        return "agent_activity_log"
    if norm.startswith("07_LOGS/Daily/"):
        return "daily_note"
    if norm.startswith("07_LOGS/Studio-Graph-Views/"):
        return "studio_graph_evidence"
    if norm.startswith("07_LOGS/"):
        return "log_artifact"
    if norm.startswith("99_ARCHIVE/Documentation-History/"):
        return "documentation_history_note"
    if norm.startswith("99_ARCHIVE/"):
        return "archive_doc"
    if norm.startswith("core_export/"):
        return "core_export_artifact"
    if norm.startswith("core_templates/"):
        return "core_template_artifact"
    if norm.startswith("runtime/adapters/codex/runs/"):
        return "codex_run_artifact"
    if norm.startswith("runtime/acquisition/staging/strikezone/") and name.startswith("20"):
        return "strikezone_staged_capture"
    if norm.startswith("runtime/") and (name.upper().endswith("README.MD") or name.endswith("-README.md")):
        return "runtime_readme"
    if norm.startswith("runtime/"):
        return "runtime_markdown_doc"
    if norm.startswith("docs/"):
        return "docs_artifact"
    return "unknown_markdown"


def _is_strikezone_rss_staged_capture(norm: str, vault_root: Path) -> bool:
    if not norm.startswith("runtime/acquisition/staging/strikezone/"):
        return False
    if not Path(norm).name.endswith(".md"):
        return False
    path = vault_root / norm
    if not path.exists():
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")
    return (
        "<!-- staged-capture" in text
        and "source_class: staged_capture" in text
        and "source_platform: rss" in text
        and "source_id: strikezone-rss-" in text
    )


def load_decision_registry(vault_root: Path) -> dict[str, Any]:
    """Load durable operator decisions for loose-node review handling."""
    path = vault_root / DECISION_REGISTRY_REL
    if not path.exists():
        return {"version": 1, "updated": None, "decisions": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"version": 1, "updated": None, "decisions": {}}
    if not isinstance(data, dict):
        return {"version": 1, "updated": None, "decisions": {}}
    data.setdefault("version", 1)
    data.setdefault("updated", None)
    data.setdefault("decisions", {})
    if not isinstance(data["decisions"], dict):
        data["decisions"] = {}
    return data


def _write_decision_registry(vault_root: Path, registry: dict[str, Any]) -> str:
    path = vault_root / DECISION_REGISTRY_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    registry["version"] = 1
    registry["updated"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    return DECISION_REGISTRY_REL


def _issue_hash(vault_root: Path, rel_path: str) -> str:
    try:
        path = _resolve_within_vault(vault_root, rel_path)
    except ValueError:
        return ""
    if not path.exists() or not path.is_file():
        return ""
    return file_sha256(path)


def _is_suppressed_by_decision(vault_root: Path, issue: Issue, registry: dict[str, Any]) -> bool:
    """Return true when an operator-approved keep-excluded decision still matches the file hash."""
    entry = registry.get("decisions", {}).get(issue.file_path)
    if not isinstance(entry, dict):
        return False
    if entry.get("decision") != "keep_excluded":
        return False
    recorded_hash = entry.get("file_sha256", "")
    current_hash = _issue_hash(vault_root, issue.file_path)
    return bool(recorded_hash and current_hash and recorded_hash == current_hash)


def _keep_excluded_hash_match(
    vault_root: Path,
    rel_path: str,
    registry: dict[str, Any] | None = None,
) -> bool:
    """Return true when rel_path has a current hash-matching keep_excluded decision."""
    active_registry = registry or load_decision_registry(vault_root)
    entry = active_registry.get("decisions", {}).get(rel_path)
    if not isinstance(entry, dict):
        return False
    if entry.get("decision") != "keep_excluded":
        return False
    recorded_hash = entry.get("file_sha256", "")
    current_hash = _issue_hash(vault_root, rel_path)
    return bool(recorded_hash and current_hash and recorded_hash == current_hash)


def _issue_evidence_int(issue: Issue, key: str) -> int | None:
    prefix = f"{key}="
    for value in issue.evidence:
        if value.startswith(prefix):
            try:
                return int(value[len(prefix):])
            except ValueError:
                return None
    return None


def _raw_zero_degree_issue(issue: Issue) -> bool:
    inbound = _issue_evidence_int(issue, "inbound")
    outbound = _issue_evidence_int(issue, "outbound")
    return inbound == 0 and outbound == 0


def _keep_excluded_visible_orphan_issue(issue: Issue) -> Issue:
    evidence = list(issue.evidence)
    _append_unique(evidence, "keep_excluded_hash_match=true")
    _append_unique(evidence, "visible_graph_connection_required=true")
    return Issue(
        category="keep_excluded_visible_orphan",
        severity="auto_fix",
        file_path=issue.file_path,
        index_path=KEEP_EXCLUDED_INDEX_REL,
        description=(
            "Hash-approved keep_excluded file is still raw-zero-degree in the visible graph; "
            "wire to the reversible keep-excluded holding index"
        ),
        action="wire_keep_excluded_to_holding_index",
        evidence=evidence,
        node_category=issue.node_category,
        canonical_path=issue.canonical_path,
    )


def apply_decision_registry_suppression(report: HygieneReport, vault_root: Path) -> None:
    """Remove operator-approved keep-excluded items from the active review queue."""
    registry = load_decision_registry(vault_root)
    if not registry.get("decisions"):
        return
    filtered: list[Issue] = []
    for issue in report.issues:
        if _is_suppressed_by_decision(vault_root, issue, registry):
            if _raw_zero_degree_issue(issue):
                filtered.append(_keep_excluded_visible_orphan_issue(issue))
            continue
        filtered.append(issue)
    report.issues = filtered


def _iter_markdown_paths(vault_root: Path) -> list[Path]:
    paths: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(vault_root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        dp = Path(dirpath)
        for fname in sorted(filenames):
            if fname.endswith(".md"):
                paths.append(dp / fname)
    return sorted(paths)


def _resolve_graph_target(
    target: str,
    source_rel: str,
    by_rel: dict[str, str],
    by_stem: dict[str, list[str]],
) -> tuple[str | None, bool]:
    normalized = target.split("|", 1)[0].split("#", 1)[0].strip()
    if not normalized or "://" in normalized:
        return None, False
    normalized = normalized.replace("\\", "/").lstrip("./")
    candidates = [normalized]
    if not normalized.lower().endswith(".md"):
        candidates.append(f"{normalized}.md")
    source_parent = Path(source_rel).parent.as_posix()
    if source_parent not in ("", "."):
        candidates.append(f"{source_parent}/{normalized}")
        if not normalized.lower().endswith(".md"):
            candidates.append(f"{source_parent}/{normalized}.md")

    for candidate in candidates:
        resolved = by_rel.get(candidate.lower())
        if resolved:
            return resolved, False

    stem = Path(normalized).stem.lower()
    stem_matches = by_stem.get(stem, [])
    if len(stem_matches) == 1:
        return stem_matches[0], False
    if len(stem_matches) > 1:
        return None, True
    return None, False


def _graph_target_indexes(vault_root: Path) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Return relative-path and stem lookup indexes for markdown graph targets."""
    by_rel: dict[str, str] = {}
    by_stem: dict[str, list[str]] = {}
    for path in _iter_markdown_paths(vault_root):
        try:
            rel = str(path.relative_to(vault_root)).replace("\\", "/")
        except ValueError:
            continue
        by_rel[rel.lower()] = rel
        by_stem.setdefault(path.stem.lower(), []).append(rel)
    return by_rel, by_stem


def _canonical_rel_for_ambiguous_target(
    target: str,
    by_stem: dict[str, list[str]],
) -> str | None:
    """Return a safe canonical path for ambiguous wikilinks when one is known."""
    base, _heading, _alias = _split_wikilink_target(target)
    stem = Path(base).stem
    canonical = CANONICAL_DUPLICATE_TARGETS.get(stem)
    if canonical and canonical in by_stem.get(stem.lower(), []):
        return canonical
    candidates = [
        rel for rel in by_stem.get(stem.lower(), [])
        if not _review_only_path(rel) and not _archive_review_path(rel)
    ]
    if len(candidates) == 1:
        return candidates[0]
    return None


def build_vault_graph_state(vault_root: Path) -> dict[str, GraphFileState]:
    """Build a path-resolved Obsidian wikilink graph for all vault markdown."""
    markdown_paths = _iter_markdown_paths(vault_root)
    by_rel: dict[str, str] = {}
    by_stem: dict[str, list[str]] = {}
    states: dict[str, GraphFileState] = {}
    texts: dict[str, str] = {}

    for path in markdown_paths:
        try:
            stat = path.stat()
            text = path.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            # Runtime temp files can disappear between os.walk discovery and read/stat.
            continue
        except OSError:
            continue
        rel = str(path.relative_to(vault_root)).replace("\\", "/")
        by_rel[rel.lower()] = rel
        by_stem.setdefault(path.stem.lower(), []).append(rel)
        texts[rel] = text
        states[rel] = GraphFileState(
            rel_path=rel,
            stem=path.stem,
            size_bytes=stat.st_size,
            heading_count=_heading_count(text),
            nonempty_line_count=sum(1 for line in text.splitlines() if line.strip()),
        )

    for source_rel, text in texts.items():
        state = states[source_rel]
        for target in extract_wikilink_stems(text):
            state.wikilink_count += 1
            resolved, ambiguous = _resolve_graph_target(target, source_rel, by_rel, by_stem)
            if resolved:
                state.outbound.add(resolved)
                states[resolved].inbound.add(source_rel)
            elif ambiguous:
                state.ambiguous_targets.add(target)
            else:
                state.unresolved_targets.add(target)
    return states


def _evidence_path(rel_path: str) -> bool:
    norm = rel_path.replace("\\", "/")
    return norm.startswith((
        "07_LOGS/Build-Logs/",
        "99_ARCHIVE/Documentation-History/",
        "07_LOGS/Agent-Activity/",
        "07_LOGS/Daily/",
        "07_LOGS/Hygiene-Reports/",
        "07_LOGS/Maintain-Runs/",
        "07_LOGS/Graph-Reports/",
        "07_LOGS/Studio-Graph-Views/",
        f"{ARCHIVE_REVIEW_REL}/",
    ))


def _major_graph_doc(rel_path: str) -> bool:
    norm = rel_path.replace("\\", "/")
    if norm.startswith(("07_LOGS/", "99_ARCHIVE/")):
        return False
    if norm.startswith((
        "06_AGENTS/",
        "runtime/studio/",
        "runtime/pulse/",
        "runtime/siteops/",
        "runtime/adapters/",
        "runtime/openclaw/",
        "runtime/hermes/",
        "runtime/codex/",
    )):
        return True
    return Path(norm).name in {
        "CLAUDE.md",
        "CODEX.md",
        "HERMES.md",
        "OPENAI.md",
        "OPENCLAW.md",
        "LOCAL-OSS.md",
        "N8N.md",
    }


SEMANTIC_HUB_DOCS = {
    "06_AGENTS/Agent-Control-Plane.md",
    "06_AGENTS/Permission-Matrix.md",
    "06_AGENTS/Trust-Tiers.md",
    "06_AGENTS/Agent-Registry.md",
    "06_AGENTS/Backends-Supported.md",
    "06_AGENTS/Vault-Map.md",
}


SEMANTIC_HUB_LINK_TARGETS = (
    "06_AGENTS/Agent-Control-Plane.md",
    "06_AGENTS/Vault-Map.md",
)


def _semantic_hub_gap_states(
    graph_states: dict[str, GraphFileState],
    vault_root: Path | None = None,
) -> list[GraphFileState]:
    """Return major docs that need an explicit outbound control-plane hub link."""
    registry = load_decision_registry(vault_root) if vault_root is not None else None
    gaps: list[GraphFileState] = []
    for rel, state in sorted(graph_states.items()):
        if rel in SEMANTIC_HUB_DOCS:
            continue
        if vault_root is not None and registry is not None and _keep_excluded_hash_match(vault_root, rel, registry):
            continue
        if not _major_graph_doc(rel):
            continue
        if any(hub in state.outbound for hub in SEMANTIC_HUB_DOCS):
            continue
        gaps.append(state)
    return gaps


def build_visible_graph_audit(
    graph_states: dict[str, GraphFileState],
    vault_root: Path | None = None,
) -> dict[str, Any]:
    """Return graph-visible hygiene counters beyond active review debt."""
    unresolved_targets: dict[str, list[str]] = {}
    ambiguous_targets: dict[str, list[str]] = {}
    zero_degree: list[dict[str, Any]] = []
    weak_degree: list[dict[str, Any]] = []
    by_stem: dict[str, list[str]] = {}

    for rel, state in sorted(graph_states.items()):
        by_stem.setdefault(state.stem.lower(), []).append(rel)
        degree = len(state.inbound) + len(state.outbound)
        if degree == 0:
            zero_degree.append({
                "file": rel,
                "node_category": infer_node_category(rel),
                "size_bytes": state.size_bytes,
                "wikilinks": state.wikilink_count,
            })
        elif degree == 1:
            weak_degree.append({
                "file": rel,
                "node_category": infer_node_category(rel),
                "inbound": len(state.inbound),
                "outbound": len(state.outbound),
                "wikilinks": state.wikilink_count,
            })
        for target in sorted(state.unresolved_targets):
            unresolved_targets.setdefault(target, []).append(rel)
        for target in sorted(state.ambiguous_targets):
            ambiguous_targets.setdefault(target, []).append(rel)

    duplicate_groups: list[dict[str, Any]] = []
    for stem, rels in sorted(by_stem.items()):
        visible_rels = [rel for rel in rels if not _evidence_path(rel)]
        if len(visible_rels) <= 1:
            continue
        duplicate_groups.append({
            "stem": stem,
            "count": len(visible_rels),
            "files": visible_rels[:8],
        })

    semantic_hub_gaps: list[dict[str, Any]] = []
    for state in _semantic_hub_gap_states(graph_states, vault_root):
        semantic_hub_gaps.append({
            "file": state.rel_path,
            "node_category": infer_node_category(state.rel_path),
            "degree": len(state.inbound) + len(state.outbound),
            "inbound": len(state.inbound),
            "outbound": len(state.outbound),
        })

    def _target_items(source_map: dict[str, list[str]]) -> list[dict[str, Any]]:
        rows = [
            {"target": target, "source_file_count": len(sources), "sources": sources[:6]}
            for target, sources in source_map.items()
        ]
        return sorted(rows, key=lambda item: (-int(item["source_file_count"]), str(item["target"])))[:30]

    return {
        "raw_zero_degree_count": len(zero_degree),
        "raw_zero_degree_files": zero_degree[:30],
        "weak_degree_1_count": len(weak_degree),
        "weak_degree_1_files": weak_degree[:30],
        "unresolved_link_target_count": len(unresolved_targets),
        "unresolved_link_source_file_count": sum(1 for state in graph_states.values() if state.unresolved_targets),
        "unresolved_link_targets": _target_items(unresolved_targets),
        "ambiguous_link_target_count": len(ambiguous_targets),
        "ambiguous_link_source_file_count": sum(1 for state in graph_states.values() if state.ambiguous_targets),
        "ambiguous_link_targets": _target_items(ambiguous_targets),
        "connected_duplicate_stem_count": len(duplicate_groups),
        "connected_duplicate_stem_groups": duplicate_groups[:30],
        "semantic_hub_gap_count": len(semantic_hub_gaps),
        "semantic_hub_gaps": semantic_hub_gaps[:30],
    }


def build_vault_graph(vault_root: Path) -> tuple[dict[str, str], dict[str, set[str]]]:
    """Build a compatibility view of the vault graph.

    Older callers receive the previous shape, but inbound values are now
    derived from path-resolved graph state instead of basename-only matching.
    """
    states = build_vault_graph_state(vault_root)
    all_stems = {state.stem: rel for rel, state in states.items()}
    inbound = {state.stem: {Path(src).stem for src in state.inbound} for state in states.values() if state.inbound}
    return all_stems, inbound


def find_graph_orphans(
    all_stems: dict[str, str],
    inbound: dict[str, set[str]],
) -> list[str]:
    """Find files with zero inbound wikilinks (true graph orphans)."""
    orphans: list[str] = []
    for stem, rel in sorted(all_stems.items()):
        if stem not in inbound:
            orphans.append(rel)
    return orphans


def classify_loose_markdown(
    state: GraphFileState,
    vault_root: Path,
) -> tuple[str, str, str, str, list[str], str, str]:
    """Classify a loose markdown node into the safest next action bucket."""
    norm = state.rel_path.replace("\\", "/")
    path = vault_root / norm
    duplicate_key = _normalized_duplicate_key(path)
    node_category = infer_node_category(norm)
    evidence = [
        f"inbound={len(state.inbound)}",
        f"outbound={len(state.outbound)}",
        f"wikilinks={state.wikilink_count}",
        f"size_bytes={state.size_bytes}",
        f"node_category={node_category}",
    ]

    if _is_strikezone_rss_staged_capture(norm, vault_root):
        return (
            "strikezone_staged_capture_orphan",
            "auto_fix",
            STRIKEZONE_RSS_STAGING_INDEX_REL,
            "wire_strikezone_staged_capture_to_project_index",
            evidence + [
                "source_class=staged_capture",
                "source_platform=rss",
                "project=StrikeZone Crypto",
                "domain=Trading Systems / Market Ops",
            ],
            node_category,
            "01_PROJECTS/StrikeZone/StrikeZone-Crypto-OS.md",
        )

    if norm.startswith("runtime/acquisition/manual/strikezone/templates/") and norm.endswith(".template.md"):
        return (
            "graph_orphan",
            "auto_fix",
            "runtime/acquisition/manual/strikezone/README.md",
            "wire_strikezone_manual_template_to_readme",
            evidence + [
                "project=StrikeZone Crypto",
                "source_class=manual_research_template",
                "anchor=runtime/acquisition/manual/strikezone/README.md",
            ],
            node_category,
            "",
        )
  
    if _review_only_path(norm):
        canonical_target = CANONICAL_DUPLICATE_TARGETS.get(duplicate_key)
        if canonical_target and norm != canonical_target:
            return (
                "duplicate_candidate",
                "review",
                canonical_target,
                "review_duplicate_then_archive_or_delete",
                evidence + _canonical_duplicate_evidence(vault_root, canonical_target, state.size_bytes),
                node_category,
                canonical_target,
            )
        if state.nonempty_line_count <= 1 or state.size_bytes <= 16:
            return (
                "empty_placeholder",
                "review",
                "(delete review)",
                "delete_candidate",
                evidence + ["content appears empty or placeholder-only"],
                node_category,
                "",
            )
        return (
            "review_only_artifact",
            "review",
            "(none)",
            "review_export_or_runtime_artifact",
            evidence + ["review-only path; do not auto-wire into canonical navigation"],
            node_category,
            "",
        )

    if Path(norm).name.upper().endswith("README.MD") or Path(norm).name.endswith("-README.md"):
        anchor = determine_anchor(norm, vault_root) or "runtime/README.md"
        return (
            "technical_readme_loose",
            "review",
            anchor,
            "review_readme_then_wire_or_exclude",
            evidence + ["README-like technical documentation"],
            node_category,
            "",
        )

    canonical_target = CANONICAL_DUPLICATE_TARGETS.get(duplicate_key)
    if canonical_target and norm != canonical_target:
        return (
            "duplicate_candidate",
            "review",
            canonical_target,
            "review_duplicate_then_archive_or_delete",
            evidence + _canonical_duplicate_evidence(vault_root, canonical_target, state.size_bytes),
            node_category,
            canonical_target,
        )

    if state.nonempty_line_count <= 1 or state.size_bytes <= 16:
        return (
            "empty_placeholder",
            "review",
            "(delete review)",
            "delete_candidate",
            evidence + ["content appears empty or placeholder-only"],
            node_category,
            "",
        )

    if norm.startswith("runtime/"):
        return (
            "runtime_markdown_loose",
            "review",
            "runtime/README.md",
            "review_runtime_doc_then_wire_or_exclude",
            evidence + ["runtime markdown/code documentation"],
            node_category,
            "",
        )

    anchor = determine_anchor(norm, vault_root)
    if anchor:
        return (
            "isolated_node",
            "auto_fix",
            anchor,
            "wire_to_anchor",
            evidence,
            node_category,
            "",
        )
    return (
        "isolated_node",
        "review",
        "(none)",
        "manual_route_or_delete_review",
        evidence,
        node_category,
        "",
    )


def determine_anchor(orphan_rel: str, vault_root: Path) -> str | None:
    """Given an orphan file's relative path, determine which anchor document should link to it."""
    norm = orphan_rel.replace("\\", "/")

    # Exact file match first (e.g. root-level md files)
    if norm in ANCHOR_DOCS:
        return ANCHOR_DOCS[norm]

    # Longest prefix match for folder-rooted entries
    best_anchor: str | None = None
    best_len = 0
    for prefix, anchor in ANCHOR_DOCS.items():
        if prefix.endswith("/") and norm.startswith(prefix) and len(prefix) > best_len:
            best_anchor = anchor
            best_len = len(prefix)
    return best_anchor


# ---------------------------------------------------------------------------
# Root-level orphan detection
# ---------------------------------------------------------------------------

def find_root_orphans(vault_root: Path) -> list[tuple[str, str]]:
    """Find files at vault root that don't belong. Returns [(filename, reason)]."""
    orphans: list[tuple[str, str]] = []
    for child in sorted(vault_root.iterdir()):
        if child.is_dir():
            continue
        name = child.name
        if name.startswith("."):
            continue
        if name in VALID_ROOT_FILES or name.endswith(".patch") or name in ("conftest.py", "NUL"):
            continue
        is_junk = any(p.match(name) for p in JUNK_PATTERNS)
        if is_junk:
            orphans.append((name, "junk"))
        else:
            orphans.append((name, "orphan_root"))
    return orphans


# ---------------------------------------------------------------------------
# Main scan + fix engine
# ---------------------------------------------------------------------------

def scan_vault(
    vault_root: Path,
    semantic_hub_fix_limit: int = 0,
    ambiguous_link_fix_limit: int = 0,
    ambiguous_link_review_limit: int = 0,
    unresolved_link_review_limit: int = 0,
) -> HygieneReport:
    """Full vault scan with graph-based orphan detection."""
    report = HygieneReport()

    # ---- 1. Scan indexed folders for loose nodes ----
    for folder_rel, index_name, _ in INDEXED_FOLDERS:
        folder_path = vault_root / folder_rel
        index_path = folder_path / index_name
        if not folder_path.exists():
            continue

        skip = ALWAYS_SKIP.copy()
        if index_name != "README.md":
            skip.add("README.md")

        # Check if index exists; if not, flag for creation
        if not index_path.exists():
            md_files = [f for f in folder_path.iterdir()
                        if f.suffix == ".md" and f.name not in skip]
            if md_files:
                report.issues.append(Issue(
                    category="missing_index",
                    severity="auto_fix",
                    file_path=str(Path(folder_rel) / index_name).replace("\\", "/"),
                    index_path=str(Path(folder_rel) / index_name).replace("\\", "/"),
                    description=f"Index file missing for {folder_rel}/ ({len(md_files)} unlinked .md files)",
                    node_category=infer_node_category(str(Path(folder_rel) / index_name)),
                ))
            continue

        missing, index_content = compute_missing_from_index(
            folder_path, index_path, folder_rel, skip
        )

        # Check for backtick-wrapped wikilinks in the index
        _, backtick_count = strip_backtick_wikilinks(index_content)
        _, entry_backtick_count = convert_backtick_entries_to_wikilinks(index_content)
        total_backticks = backtick_count + entry_backtick_count
        if total_backticks > 0:
            report.issues.append(Issue(
                category="backtick_wikilink",
                severity="auto_fix",
                file_path=str(Path(folder_rel) / index_name).replace("\\", "/"),
                index_path=str(Path(folder_rel) / index_name).replace("\\", "/"),
                description=f"{total_backticks} backtick-wrapped wikilinks preventing graph edges",
                action="fix_backtick_wikilinks",
                node_category=infer_node_category(str(Path(folder_rel) / index_name)),
            ))

        for stem in missing:
            report.issues.append(Issue(
                category="loose_node",
                severity="auto_fix",
                file_path=str(Path(folder_rel) / f"{stem}.md").replace("\\", "/"),
                index_path=str(Path(folder_rel) / index_name).replace("\\", "/"),
                description=f"File exists but not wikilinked from {index_name}",
                action="wire_to_index",
                node_category=infer_node_category(str(Path(folder_rel) / f"{stem}.md")),
            ))

    # ---- 2. Root-level orphans ----
    for name, reason in find_root_orphans(vault_root):
        report.issues.append(Issue(
            category=reason,
            severity="junk" if reason == "junk" else "review",
            file_path=name,
            index_path="(vault root)",
            description=f"Root-level file not in VALID_ROOT_FILES: {name}",
            action="delete_candidate" if reason == "junk" else "manual_route_or_delete_review",
            node_category="root_junk_or_orphan",
        ))

    # ---- 3. Full vault graph-based orphan detection ----
    graph_states = build_vault_graph_state(vault_root)
    _by_rel, by_stem = _graph_target_indexes(vault_root)
    report.visible_graph_audit = build_visible_graph_audit(graph_states, vault_root)
    graph_orphans = [
        state.rel_path
        for state in graph_states.values()
        if not state.inbound and not state.outbound
    ]

    # Filter out files already handled by indexed-folder scan
    handled_stems = set()
    for issue in report.issues:
        if issue.category in ("loose_node", "backtick_wikilink", "missing_index"):
            handled_stems.add(Path(issue.file_path).stem)

    for orphan_rel in graph_orphans:
        orphan_stem = Path(orphan_rel).stem
        if orphan_stem in handled_stems:
            continue

        if _archive_review_path(orphan_rel):
            report.issues.append(Issue(
                category="graph_orphan",
                severity="auto_fix",
                file_path=orphan_rel,
                index_path=_archive_review_index_for(orphan_rel),
                description="Archived graph hygiene review evidence with zero inbound links -- will wire to review archive index",
                action="wire_to_review_archive_index",
                node_category=infer_node_category(orphan_rel),
            ))
            continue

        state = graph_states.get(orphan_rel)
        if state is not None:
            category, severity, index_path, action, evidence, node_category, canonical_path = classify_loose_markdown(
                state, vault_root
            )
            if category != "isolated_node":
                report.issues.append(Issue(
                    category=category,
                    severity=severity,
                    file_path=orphan_rel,
                    index_path=index_path,
                    description=f"Loose markdown node classified as {category}; action={action}",
                    action=action,
                    evidence=evidence,
                    node_category=node_category,
                    canonical_path=canonical_path,
                ))
                continue

        # Skip index files themselves (they're anchors, not content)
        orphan_name = Path(orphan_rel).name
        if orphan_name.endswith("-Index.md") or orphan_name == "Index.md":
            # Index files that are themselves orphaned need wiring into their parent
            anchor = determine_anchor(orphan_rel, vault_root)
            if anchor:
                report.issues.append(Issue(
                    category="graph_orphan",
                    severity="auto_fix",
                    file_path=orphan_rel,
                    index_path=anchor,
                    description=f"Index file with zero inbound links -- needs wiring into anchor",
                    action="wire_index_to_anchor",
                    node_category=infer_node_category(orphan_rel),
                ))
            continue

        # Prefer local folder indexes over broad folder anchors. A Studio graph
        # evidence file belongs in Studio-Graph-Views-Index, not as another
        # generic Vault-Map entry.
        best_index: str | None = None
        best_prefix_len = 0
        norm = orphan_rel.replace("\\", "/")
        for folder_rel, index_name, _ in INDEXED_FOLDERS:
            prefix = folder_rel.replace("\\", "/").rstrip("/") + "/"
            if norm.startswith(prefix) and len(prefix) > best_prefix_len:
                best_index = f"{folder_rel}/{index_name}"
                best_prefix_len = len(prefix)

        if best_index:
            report.issues.append(Issue(
                category="graph_orphan",
                severity="auto_fix",
                file_path=orphan_rel,
                index_path=best_index,
                description=f"Zero inbound links -- will wire into {Path(best_index).name}",
                action="wire_to_index",
                node_category=infer_node_category(orphan_rel),
            ))
            continue

        anchor = determine_anchor(orphan_rel, vault_root)
        if anchor:
            report.issues.append(Issue(
                category="graph_orphan",
                severity="auto_fix",
                file_path=orphan_rel,
                index_path=anchor,
                description=f"Zero inbound wikilinks in vault graph -- will wire to anchor",
                action="wire_to_anchor",
                node_category=infer_node_category(orphan_rel),
            ))
        else:
            # --- Domain fallbacks ---
            if norm.startswith("01_PROJECTS/"):
                parts = norm.split("/")
                if len(parts) >= 3:
                    report.issues.append(Issue(
                        category="graph_orphan",
                        severity="auto_fix",
                        file_path=orphan_rel,
                        index_path="00_HOME/Dashboard.md",
                        description="Project file with zero inbound links -- will wire to Dashboard",
                        action="wire_to_dashboard",
                        node_category=infer_node_category(orphan_rel),
                    ))
                else:
                    report.issues.append(Issue(
                        category="graph_orphan",
                        severity="review",
                        file_path=orphan_rel,
                        index_path="(none)",
                        description="Orphaned project file -- needs manual placement",
                        action="manual_route_or_delete_review",
                        node_category=infer_node_category(orphan_rel),
                    ))

            elif norm.startswith("02_KNOWLEDGE/"):
                report.issues.append(Issue(
                    category="graph_orphan",
                    severity="auto_fix",
                    file_path=orphan_rel,
                    index_path="02_KNOWLEDGE/Knowledge-Index.md",
                    description="Knowledge note with zero inbound links",
                    action="wire_to_knowledge_index",
                    node_category=infer_node_category(orphan_rel),
                ))

            elif norm.startswith("99_ARCHIVE/"):
                report.issues.append(Issue(
                    category="graph_orphan",
                    severity="auto_fix",
                    file_path=orphan_rel,
                    index_path="99_ARCHIVE/Documentation-History/Documentation-History-Index.md",
                    description="Archive file with zero inbound links",
                    action="wire_to_archive_index",
                    node_category=infer_node_category(orphan_rel),
                ))

            elif norm.startswith("docs/changes/"):
                report.issues.append(Issue(
                    category="graph_orphan",
                    severity="auto_fix",
                    file_path=orphan_rel,
                    index_path="docs/changes/Changes-Index.md",
                    description="Change doc with zero inbound links -- will wire into Changes-Index",
                    action="wire_to_changes_index",
                    node_category=infer_node_category(orphan_rel),
                ))

            elif norm.startswith("docs/features/"):
                report.issues.append(Issue(
                    category="graph_orphan",
                    severity="auto_fix",
                    file_path=orphan_rel,
                    index_path="docs/features/Features-Index.md",
                    description="Feature doc with zero inbound links -- will wire into Features-Index",
                    action="wire_to_features_index",
                    node_category=infer_node_category(orphan_rel),
                ))

            elif norm.startswith("03_INPUTS/Browser-Skill-Candidates/"):
                report.issues.append(Issue(
                    category="graph_orphan",
                    severity="auto_fix",
                    file_path=orphan_rel,
                    index_path="03_INPUTS/Browser-Skill-Candidates/Browser-Skill-Candidates-Index.md",
                    description="Browser skill candidate with zero inbound links",
                    action="wire_to_input_index",
                    node_category=infer_node_category(orphan_rel),
                ))

            elif norm.startswith("03_INPUTS/"):
                # Find correct sub-folder index
                best_inp: str | None = None
                best_inp_len = 0
                for folder_rel, index_name, _ in INDEXED_FOLDERS:
                    prefix = folder_rel.replace("\\", "/").rstrip("/") + "/"
                    if norm.startswith(prefix) and len(prefix) > best_inp_len:
                        best_inp = f"{folder_rel}/{index_name}"
                        best_inp_len = len(prefix)
                if best_inp:
                    report.issues.append(Issue(
                        category="graph_orphan",
                        severity="auto_fix",
                        file_path=orphan_rel,
                        index_path=best_inp,
                        description=f"Input file with zero inbound links -- will wire into {Path(best_inp).name}",
                        action="wire_to_input_index",
                        node_category=infer_node_category(orphan_rel),
                    ))
                else:
                    report.issues.append(Issue(
                        category="graph_orphan",
                        severity="review",
                        file_path=orphan_rel,
                        index_path="(none)",
                        description="Input file with zero inbound links -- needs manual placement",
                        action="manual_route_or_delete_review",
                        node_category=infer_node_category(orphan_rel),
                    ))

            elif norm in VALID_ROOT_FILES or not "/" in norm:
                # Root-level doc files that are architecturally valid
                report.issues.append(Issue(
                    category="graph_orphan",
                    severity="auto_fix",
                    file_path=orphan_rel,
                    index_path="README.md",
                    description="Root-level doc with zero inbound links -- will wire into README",
                    action="wire_to_readme",
                    node_category=infer_node_category(orphan_rel),
                ))

            else:
                report.issues.append(Issue(
                    category="graph_orphan",
                    severity="review",
                    file_path=orphan_rel,
                    index_path="(none)",
                    description="Orphaned file with zero inbound links -- needs manual placement",
                    action="manual_route_or_delete_review",
                    node_category=infer_node_category(orphan_rel),
                ))

    if semantic_hub_fix_limit > 0:
        for state in _semantic_hub_gap_states(graph_states, vault_root)[:semantic_hub_fix_limit]:
            report.issues.append(Issue(
                category="semantic_hub_gap",
                severity="auto_fix",
                file_path=state.rel_path,
                index_path=";".join(SEMANTIC_HUB_LINK_TARGETS),
                description="Major graph doc lacks an outbound governance hub link",
                action="append_governance_links",
                evidence=[
                    f"inbound={len(state.inbound)}",
                    f"outbound={len(state.outbound)}",
                    f"wikilinks={state.wikilink_count}",
                    f"node_category={infer_node_category(state.rel_path)}",
                    "target_links="
                    + ",".join(_wikilink_target_for_rel(target) for target in SEMANTIC_HUB_LINK_TARGETS),
                ],
                node_category=infer_node_category(state.rel_path),
            ))

    if ambiguous_link_fix_limit > 0:
        emitted = 0
        for state in sorted(graph_states.values(), key=lambda item: item.rel_path):
            for target in sorted(state.ambiguous_targets):
                canonical_rel = _canonical_rel_for_ambiguous_target(target, by_stem)
                if not canonical_rel:
                    continue
                report.issues.append(Issue(
                    category="ambiguous_link_target",
                    severity="auto_fix",
                    file_path=state.rel_path,
                    index_path=canonical_rel,
                    description="Ambiguous wikilink can be safely path-qualified to a known canonical ChaseOS node",
                    action="path_qualify_ambiguous_link",
                    evidence=[
                        f"target={target}",
                        f"canonical_target={canonical_rel}",
                        f"node_category={infer_node_category(state.rel_path)}",
                    ],
                    node_category=infer_node_category(state.rel_path),
                    canonical_path=canonical_rel,
                ))
                emitted += 1
                if emitted >= ambiguous_link_fix_limit:
                    break
            if emitted >= ambiguous_link_fix_limit:
                break

    if ambiguous_link_review_limit > 0:
        emitted = 0
        for state in sorted(graph_states.values(), key=lambda item: item.rel_path):
            for target in sorted(state.ambiguous_targets):
                canonical_rel = _canonical_rel_for_ambiguous_target(target, by_stem)
                if canonical_rel:
                    continue
                candidates = sorted(by_stem.get(target.lower(), []))
                report.issues.append(Issue(
                    category="ambiguous_link_target_review",
                    severity="review",
                    file_path=state.rel_path,
                    index_path=target,
                    description="Ambiguous wikilink target has no safe canonical route; operator must choose path-qualified target or rename/link cleanup",
                    action="review_duplicate_stem_create_alias_or_path_qualify",
                    evidence=[
                        f"target={target}",
                        f"candidate_count={len(candidates)}",
                        "candidates=" + ",".join(candidates[:8]),
                        f"node_category={infer_node_category(state.rel_path)}",
                    ],
                    node_category=infer_node_category(state.rel_path),
                ))
                emitted += 1
                if emitted >= ambiguous_link_review_limit:
                    break
            if emitted >= ambiguous_link_review_limit:
                break

    if unresolved_link_review_limit > 0:
        emitted = 0
        for state in sorted(graph_states.values(), key=lambda item: item.rel_path):
            for target in sorted(state.unresolved_targets):
                report.issues.append(Issue(
                    category="unresolved_link_target",
                    severity="review",
                    file_path=state.rel_path,
                    index_path=target,
                    description="Wikilink target does not resolve to an existing markdown node",
                    action="review_target_create_rename_or_unlink",
                    evidence=[
                        f"target={target}",
                        f"node_category={infer_node_category(state.rel_path)}",
                    ],
                    node_category=infer_node_category(state.rel_path),
                ))
                emitted += 1
                if emitted >= unresolved_link_review_limit:
                    break
            if emitted >= unresolved_link_review_limit:
                break

    # Count scanned files
    report.files_scanned = len(graph_states)
    apply_decision_registry_suppression(report, vault_root)

    return report



def _semantic_hub_link_block(rel_path: str) -> str:
    dt = _local_now().strftime("%Y-%m-%d")
    links = " . ".join(_wikilink_for_rel(target) for target in SEMANTIC_HUB_LINK_TARGETS)
    return (
        "\n\n## Graph Hygiene Governance Links\n\n"
        f"*Auto-wired by vault_hygiene ({dt}): {links}*\n"
    )


def apply_fixes(vault_root: Path, report: HygieneReport, delete_junk: bool = False) -> None:
    """Apply all auto_fix issues and optionally delete junk."""
    files_written: list[str] = []
    files_read: list[str] = []

    # ---- 0. Create missing index files ----
    missing_index_issues = [i for i in report.issues if i.category == "missing_index"]
    for issue in missing_index_issues:
        idx_path = vault_root / issue.file_path
        folder_path = idx_path.parent
        index_name = idx_path.name
        if create_index_if_missing(folder_path, index_name):
            issue.fixed = True
            report.indexes_created += 1
            report.files_fixed += 1
            files_written.append(issue.file_path)

            # Now wire all .md files in that folder into the new index
            skip = ALWAYS_SKIP.copy()
            if index_name != "README.md":
                skip.add("README.md")
            stems_to_wire: list[str] = []
            for child in sorted(folder_path.iterdir()):
                if child.is_dir() or child.suffix != ".md":
                    continue
                if child.name in skip or child.name == index_name:
                    continue
                stems_to_wire.append(child.stem)
            if stems_to_wire:
                content = idx_path.read_text(encoding="utf-8")
                block = generate_wiring_block(stems_to_wire, folder_path.name)
                content += block
                idx_path.write_text(content, encoding="utf-8")
                report.nodes_wired += len(stems_to_wire)

    # ---- 1. Fix backtick wikilinks in index files ----
    backtick_issues = [i for i in report.issues if i.category == "backtick_wikilink"]
    for issue in backtick_issues:
        index_path = vault_root / issue.file_path
        if not index_path.exists():
            continue
        content = index_path.read_text(encoding="utf-8")
        files_read.append(issue.file_path)

        content, count1 = strip_backtick_wikilinks(content)
        content, count2 = convert_backtick_entries_to_wikilinks(content)
        total = count1 + count2

        if total > 0:
            index_path.write_text(content, encoding="utf-8")
            files_written.append(issue.file_path)
            report.wikilinks_fixed += total
            issue.fixed = True
            report.files_fixed += 1

    # ---- 2. Wire loose nodes into their indexes ----
    loose_by_index: dict[str, list[str]] = {}
    for issue in report.issues:
        if issue.category == "loose_node" and issue.severity == "auto_fix":
            loose_by_index.setdefault(issue.index_path, []).append(issue.file_path)

    for index_rel, rel_paths in loose_by_index.items():
        index_path = vault_root / index_rel

        # If the index doesn't exist, create it first (don't silently skip)
        if not index_path.exists():
            folder_path = index_path.parent
            index_name = index_path.name
            if create_index_if_missing(folder_path, index_name):
                report.indexes_created += 1
                files_written.append(index_rel)
            else:
                continue  # creation failed; truly skip

        content = index_path.read_text(encoding="utf-8")
        files_read.append(index_rel)

        linked = extract_wikilink_stems(content)
        still_missing = [rel for rel in rel_paths if not _link_target_present(linked, rel)]

        if not still_missing:
            for issue in report.issues:
                if issue.index_path == index_rel and issue.category == "loose_node":
                    if issue.file_path in rel_paths:
                        issue.fixed = True
                        issue.description += " (resolved by backtick fix)"
            continue

        folder_name = Path(index_rel).parent.name
        block = generate_path_wiring_block(still_missing, folder_name)

        if not content.endswith("\n"):
            content += "\n"
        content += block
        index_path.write_text(content, encoding="utf-8")
        files_written.append(index_rel)

        for issue in report.issues:
            if issue.index_path == index_rel and issue.category == "loose_node":
                if issue.file_path in still_missing:
                    issue.fixed = True
                    report.nodes_wired += 1

        report.files_fixed += 1

    # ---- 3. Wire graph orphans into their anchor documents ----
    orphans_by_anchor: dict[str, list[str]] = {}
    for issue in report.issues:
        if issue.category in {
            "graph_orphan",
            "keep_excluded_visible_orphan",
            "strikezone_staged_capture_orphan",
        } and issue.severity == "auto_fix":
            orphans_by_anchor.setdefault(issue.index_path, []).append(issue.file_path)

    for anchor_rel, rel_paths in orphans_by_anchor.items():
        anchor_path = vault_root / anchor_rel
        if not anchor_path.exists():
            # If the anchor doesn't exist (e.g. runtime/README.md), create it
            anchor_path.parent.mkdir(parents=True, exist_ok=True)
            if anchor_rel == KEEP_EXCLUDED_INDEX_REL:
                anchor_path.write_text(_keep_excluded_index_header(), encoding="utf-8")
            elif anchor_rel == STRIKEZONE_RSS_STAGING_INDEX_REL:
                anchor_path.write_text(_strikezone_rss_staging_index_header(), encoding="utf-8")
            else:
                dt = _local_now().strftime("%Y-%m-%d")
                anchor_path.write_text(
                    f"# {anchor_path.parent.name}\n\n"
                    f"> Auto-generated anchor by vault_hygiene on {dt}.\n\n",
                    encoding="utf-8",
                )
            files_written.append(anchor_rel)

        content = anchor_path.read_text(encoding="utf-8")
        files_read.append(anchor_rel)

        # Check which stems are already linked
        linked = extract_wikilink_stems(content)
        still_missing = [rel for rel in rel_paths if _wikilink_target_for_rel(rel) not in linked]

        if not still_missing:
            for issue in report.issues:
                if issue.index_path == anchor_rel and issue.category in {
                    "graph_orphan",
                    "keep_excluded_visible_orphan",
                    "strikezone_staged_capture_orphan",
                }:
                    if issue.file_path in rel_paths:
                        issue.fixed = True
                        issue.description += " (already linked)"
            continue

        # Append a graph-links block at the end of the anchor
        dt = _local_now().strftime("%Y-%m-%d")
        link_line = " . ".join(_wikilink_for_rel(rel) for rel in sorted(still_missing))
        graph_block = (
            f"\n\n*Graph links auto-wired by vault_hygiene ({dt}): "
            f"{link_line}*\n"
        )

        if not content.endswith("\n"):
            content += "\n"
        content += graph_block
        anchor_path.write_text(content, encoding="utf-8")
        files_written.append(anchor_rel)

        for issue in report.issues:
            if issue.index_path == anchor_rel and issue.category in {
                "graph_orphan",
                "keep_excluded_visible_orphan",
                "strikezone_staged_capture_orphan",
            }:
                if issue.file_path in still_missing:
                    issue.fixed = True
                    report.nodes_wired += 1

        report.files_fixed += 1

    # ---- 4. Append governance hub links to major docs missing control-plane routes ----
    semantic_hub_issues = [
        i for i in report.issues
        if i.category == "semantic_hub_gap" and i.severity == "auto_fix"
    ]
    for issue in semantic_hub_issues:
        target_path = vault_root / issue.file_path
        if not target_path.exists() or target_path.suffix.lower() != ".md":
            continue

        content = target_path.read_text(encoding="utf-8")
        files_read.append(issue.file_path)
        linked = extract_wikilink_stems(content)
        if any(_link_target_present(linked, target) for target in SEMANTIC_HUB_LINK_TARGETS):
            issue.fixed = True
            issue.description += " (already linked)"
            continue

        if "## Graph Hygiene Governance Links" not in content:
            if not content.endswith("\n"):
                content += "\n"
            content += _semantic_hub_link_block(issue.file_path)
            target_path.write_text(content, encoding="utf-8")
            files_written.append(issue.file_path)
            report.files_fixed += 1
            report.nodes_wired += 1

        issue.fixed = True

    # ---- 5. Path-qualify safe ambiguous wikilinks to known canonical docs ----
    ambiguous_link_issues = [
        i for i in report.issues
        if i.category == "ambiguous_link_target" and i.severity == "auto_fix"
    ]
    ambiguous_by_file: dict[str, list[Issue]] = {}
    for issue in ambiguous_link_issues:
        ambiguous_by_file.setdefault(issue.file_path, []).append(issue)

    for source_rel, issues in ambiguous_by_file.items():
        source_path = vault_root / source_rel
        if not source_path.exists() or source_path.suffix.lower() != ".md":
            continue
        content = source_path.read_text(encoding="utf-8")
        files_read.append(source_rel)
        total_count = 0
        for issue in issues:
            target_values = [
                value.split("=", 1)[1]
                for value in issue.evidence
                if value.startswith("target=")
            ]
            if not target_values or not issue.canonical_path:
                continue
            content, count = _replace_wikilink_target(
                content,
                target_values[0],
                issue.canonical_path,
            )
            if count:
                issue.fixed = True
                total_count += count
        if total_count:
            source_path.write_text(content, encoding="utf-8")
            files_written.append(source_rel)
            report.wikilinks_fixed += total_count
            report.files_fixed += 1

    # ---- 5.5 Auto-wire review items to Pending-Review-Index ----
    PENDING_REVIEW_INDEX_REL = "99_ARCHIVE/Vault-Hygiene-Review/Pending-Review-Index.md"
    pending_review_path = vault_root / PENDING_REVIEW_INDEX_REL
    
    review_file_issues = [
        i for i in report.issues 
        if i.severity == "review" and i.category in {
            "technical_readme_loose", "runtime_markdown_loose", 
            "duplicate_candidate", "empty_placeholder", "manual_route_or_delete_review"
        }
    ]
    
    if review_file_issues:
        pending_review_path.parent.mkdir(parents=True, exist_ok=True)
        if not pending_review_path.exists():
            dt = _local_now().strftime("%Y-%m-%d")
            pending_review_path.write_text(
                f"# Pending Hygiene Review\n\n> Auto-generated anchor by vault_hygiene on {dt} for review-gated nodes.\n\n",
                encoding="utf-8"
            )
        
        index_content = pending_review_path.read_text(encoding="utf-8")
        linked_in_index = extract_wikilink_stems(index_content)
        index_updated = False
        
        for issue in review_file_issues:
            target_path = vault_root / issue.file_path
            if not target_path.exists() or target_path.suffix.lower() != ".md":
                continue
                
            # 1. Wire the file to the index
            file_content = target_path.read_text(encoding="utf-8")
            linked_in_file = extract_wikilink_stems(file_content)
            
            if "Pending-Review-Index" not in linked_in_file and _wikilink_target_for_rel(PENDING_REVIEW_INDEX_REL) not in linked_in_file:
                if not file_content.endswith("\n"):
                    file_content += "\n"
                file_content += f"\n\n*Pending Graph Hygiene Review: [[{Path(PENDING_REVIEW_INDEX_REL).stem}]]*\n"
                target_path.write_text(file_content, encoding="utf-8")
                files_written.append(issue.file_path)
                report.nodes_wired += 1
                
            # 2. Wire the index to the file
            target_stem = Path(issue.file_path).stem
            if target_stem not in linked_in_index and _wikilink_target_for_rel(issue.file_path) not in linked_in_index:
                index_content += f"- [[{_wikilink_for_rel(issue.file_path)}]] ({issue.category})\n"
                index_updated = True
                
        if index_updated:
            pending_review_path.write_text(index_content, encoding="utf-8")
            files_written.append(PENDING_REVIEW_INDEX_REL)

    # ---- 6. Delete junk if requested ----
    if delete_junk:
        for issue in report.issues:
            if issue.severity == "junk":
                target = vault_root / issue.file_path
                # M-3 security fix: verify target resolves inside vault before deletion
                try:
                    target.resolve().relative_to(vault_root.resolve())
                except ValueError:
                    continue  # skip — resolved path escapes vault boundary
                if target.exists():
                    try:
                        target.unlink()
                        issue.fixed = True
                        report.junk_deleted += 1
                        files_written.append(issue.file_path)
                    except Exception:
                        pass
            if issue.severity == "junk":
                report.junk_flagged += 1

    # ---- MCP Audit ----
    _mcp_audit(
        surface_id="vault_hygiene.fix",
        outcome="success",
        files_read=files_read,
        files_written=files_written,
        detail=(
            f"wikilinks_fixed={report.wikilinks_fixed}; "
            f"nodes_wired={report.nodes_wired}; "
            f"indexes_created={report.indexes_created}; "
            f"junk_deleted={report.junk_deleted}"
        ),
    )


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

def render_report(report: HygieneReport, vault_root: Path) -> str:
    """Render the hygiene report as markdown."""
    dt = _local_now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# Vault Hygiene Report -- {dt}",
        "",
        f"**Vault root:** `{vault_root}`",
        f"**Files scanned:** {report.files_scanned}",
        f"**Issues found:** {len(report.issues)}",
        f"**Wikilinks fixed:** {report.wikilinks_fixed}",
        f"**Nodes wired:** {report.nodes_wired}",
        f"**Indexes created:** {report.indexes_created}",
        f"**Junk flagged:** {report.junk_flagged}",
        f"**Junk deleted:** {report.junk_deleted}",
        f"**Files modified:** {report.files_fixed}",
        "",
    ]
    if report.visible_graph_audit:
        visible = report.visible_graph_audit
        lines.extend([
            "## Visible Graph Audit",
            "",
            f"- Raw zero-degree files: `{visible.get('raw_zero_degree_count', 0)}`",
            f"- Weak degree-1 files: `{visible.get('weak_degree_1_count', 0)}`",
            f"- Unresolved draft-link targets: `{visible.get('unresolved_link_target_count', 0)}`",
            f"- Ambiguous duplicate-stem targets: `{visible.get('ambiguous_link_target_count', 0)}`",
            f"- Connected duplicate-stem groups: `{visible.get('connected_duplicate_stem_count', 0)}`",
            f"- Semantic hub-link gaps: `{visible.get('semantic_hub_gap_count', 0)}`",
            "",
        ])

    # Group by category
    categories: dict[str, list[Issue]] = {}
    for issue in report.issues:
        categories.setdefault(issue.category, []).append(issue)

    for cat, issues in sorted(categories.items()):
        fixed = sum(1 for i in issues if i.fixed)
        unfixed = len(issues) - fixed
        lines.append(f"## {cat.replace('_', ' ').title()} ({len(issues)} total, {fixed} fixed, {unfixed} remaining)")
        lines.append("")

        if cat in (
            "loose_node",
            "backtick_wikilink",
            "graph_orphan",
            "missing_index",
            "keep_excluded_visible_orphan",
            "strikezone_staged_capture_orphan",
        ):
            lines.append("| Status | File | Anchor/Index | Action | Node Category | Description |")
            lines.append("|--------|------|--------------|--------|---------------|-------------|")
            for issue in issues:
                status = "[FIXED]" if issue.fixed else "[PENDING]"
                action = issue.action or "auto_fix"
                category = issue.node_category or infer_node_category(issue.file_path)
                lines.append(f"| {status} | `{issue.file_path}` | `{issue.index_path}` | `{action}` | {category} | {issue.description} |")
        else:
            lines.append("| Status | File | Category | Node Category | Keep / Canonical | Action | Evidence | Description |")
            lines.append("|--------|------|----------|---------------|------------------|--------|----------|-------------|")
            for issue in issues:
                status = "[DELETED]" if issue.fixed else ("[REVIEW]" if issue.severity == "review" else "[JUNK]")
                action = issue.action or issue.severity
                evidence = "; ".join(issue.evidence[:5])
                node_category = issue.node_category or infer_node_category(issue.file_path)
                keep_path = issue.canonical_path or issue.index_path
                lines.append(f"| {status} | `{issue.file_path}` | {issue.severity} | {node_category} | `{keep_path}` | `{action}` | {evidence} | {issue.description} |")

        lines.append("")

    # Summary for unfixed review items
    review_items = [i for i in report.issues if not i.fixed and i.severity == "review"]
    if review_items:
        lines.append("## Items Requiring Manual Review")
        lines.append("")
        lines.append("> These files could not be auto-fixed. They may be redundant, misplaced, or need content review before deletion.")
        lines.append("")
        for item in review_items:
            lines.append(f"- `{item.file_path}` -- {item.description}")
        lines.append("")

    return "\n".join(lines)


def summarize_issues(report: HygieneReport) -> dict[str, int]:
    """Return issue counts by hygiene category."""
    counts: dict[str, int] = {}
    for issue in report.issues:
        counts[issue.category] = counts.get(issue.category, 0) + 1
    return dict(sorted(counts.items()))


def summarize_node_categories(report: HygieneReport) -> dict[str, int]:
    """Return issue counts by inferred vault node category."""
    counts: dict[str, int] = {}
    for issue in report.issues:
        category = issue.node_category or infer_node_category(issue.file_path)
        counts[category] = counts.get(category, 0) + 1
    return dict(sorted(counts.items()))


def infer_review_decision_hint(issue: Issue) -> str:
    """Suggest the safest first decision for an operator review queue item."""
    if issue.category == "duplicate_candidate" and issue.canonical_path:
        return "replace_with_canonical_after_review"
    if issue.category in ("empty_placeholder", "junk"):
        return "delete_after_review"
    if issue.category == "technical_readme_loose":
        return "keep_excluded_or_archive_noncanonical_after_review"
    if issue.category == "runtime_markdown_loose":
        return "archive_noncanonical_artifact_after_review"
    if issue.category == "review_only_artifact":
        return "archive_noncanonical_artifact_after_review"
    if issue.severity == "review":
        return "manual_investigation"
    return "auto_fix_candidate"


def build_loose_node_review_queue(report: HygieneReport, vault_root: Path | None = None) -> list[dict[str, Any]]:
    """Build an operator review queue for loose nodes that should not be auto-wired."""
    root = vault_root or VAULT_ROOT
    queue: list[dict[str, Any]] = []
    for issue in report.issues:
        if issue.fixed:
            continue
        if _archive_review_path(issue.file_path):
            continue
        if issue.category not in REVIEW_QUEUE_CATEGORIES:
            continue
        if issue.category == "graph_orphan" and issue.severity == "auto_fix":
            continue
        node_category = issue.node_category or infer_node_category(issue.file_path)
        keep_or_canonical = issue.canonical_path or issue.index_path
        queue.append({
            "file": issue.file_path,
            "file_sha256": _issue_hash(root, issue.file_path),
            "issue_category": issue.category,
            "node_category": node_category,
            "severity": issue.severity,
            "recommended_action": issue.action or issue.severity,
            "decision_hint": infer_review_decision_hint(issue),
            "keep_or_canonical": keep_or_canonical,
            "canonical_path": issue.canonical_path,
            "evidence": issue.evidence,
            "description": issue.description,
        })
    return queue


def summarize_review_queue_categories(queue: list[dict[str, Any]]) -> dict[str, int]:
    """Return issue-category counts for the active review queue."""
    counts: dict[str, int] = {}
    for item in queue:
        category = str(item.get("issue_category") or "unknown")
        counts[category] = counts.get(category, 0) + 1
    return dict(sorted(counts.items()))


def visible_graph_debt_count(report: HygieneReport) -> int:
    """Count graph-visible debt classes that can appear loose or misleading."""
    visible = report.visible_graph_audit or {}
    keys = (
        "raw_zero_degree_count",
        "unresolved_link_target_count",
        "ambiguous_link_target_count",
        "connected_duplicate_stem_count",
        "semantic_hub_gap_count",
    )
    return sum(int(visible.get(key) or 0) for key in keys)


def _table_cell(value: Any) -> str:
    """Sanitize a value for a compact markdown table cell."""
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def _ensure_graph_reports_index(
    vault_root: Path,
    md_rel: str,
    heading: str | None = None,
    status: str | None = None,
) -> None:
    """Ensure the generated markdown queue is linked from the Graph-Reports index."""
    index_rel = "07_LOGS/Graph-Reports/Graph-Reports-Index.md"
    index_path = vault_root / index_rel
    index_path.parent.mkdir(parents=True, exist_ok=True)
    if index_path.exists():
        content = index_path.read_text(encoding="utf-8")
    else:
        content = "# Graph Reports Index\n"

    link = f"[[{Path(md_rel).stem}]]"
    if link in content:
        return
    if not content.endswith("\n"):
        content += "\n"
    heading_text = heading or f"Loose Node Review Queue - {_local_now().strftime('%Y-%m-%d')}"
    status_text = status or "Generated by vault_hygiene review queue guard"
    content += (
        "\n---\n\n"
        f"## {heading_text}\n\n"
        "| Artifact | Status |\n"
        "|----------|--------|\n"
        f"| {link} | {status_text} |\n"
    )
    index_path.write_text(content, encoding="utf-8")


def _ensure_graph_reports_artifact_index_row(
    vault_root: Path,
    artifact_rel: str,
    heading: str | None = None,
    status: str | None = None,
) -> bool:
    """Ensure a non-markdown graph report artifact is listed from the reports index."""
    index_rel = "07_LOGS/Graph-Reports/Graph-Reports-Index.md"
    index_path = vault_root / index_rel
    index_path.parent.mkdir(parents=True, exist_ok=True)
    if index_path.exists():
        content = index_path.read_text(encoding="utf-8")
    else:
        content = "# Graph Reports Index\n"

    display_rel = artifact_rel
    prefix = "07_LOGS/Graph-Reports/"
    if display_rel.startswith(prefix):
        display_rel = display_rel[len(prefix):]
    if display_rel in content:
        return False

    if not content.endswith("\n"):
        content += "\n"
    heading_text = heading or f"Graph Report Artifact - {_local_now().strftime('%Y-%m-%d')}"
    status_text = status or "Generated by vault_hygiene"
    content += (
        "\n---\n\n"
        f"## {heading_text}\n\n"
        "| Artifact | Status |\n"
        "|----------|--------|\n"
        f"| {display_rel} | {status_text} |\n"
    )
    index_path.write_text(content, encoding="utf-8")
    return True


def write_loose_node_review_artifacts(
    report: HygieneReport,
    vault_root: Path,
    output_dir: str | None = None,
) -> dict[str, str]:
    """Write JSON and markdown review artifacts for operator-approved cleanup."""
    queue = build_loose_node_review_queue(report, vault_root)
    out_dir = vault_root / (output_dir or "07_LOGS/Graph-Reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = _local_now().strftime("%Y-%m-%d")
    stem = f"{stamp}-loose-node-review-queue"
    json_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "review_required" if queue else "clear",
        "files_scanned": report.files_scanned,
        "total_issues": len(report.issues),
        "category_counts": summarize_issues(report),
        "node_category_counts": summarize_node_categories(report),
        "review_queue_category_counts": summarize_review_queue_categories(queue),
        "loose_node_review_count": len(queue),
        "allowed_decisions": [
            "keep_and_wire",
            "keep_excluded",
            "archive_after_review",
            "archive_noncanonical_artifact",
            "delete_after_review",
            "replace_with_canonical",
            "manual_investigation",
        ],
        "delete_policy": "No delete/archive action is automatic. Operator approval must name the file and decision.",
        "queue": queue,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        f"# Loose Node Review Queue - {stamp}",
        "",
        f"**Status:** {'review required' if queue else 'clear'}",
        f"**Files scanned:** {report.files_scanned}",
        f"**Total hygiene issues:** {len(report.issues)}",
        f"**Review items:** {len(queue)}",
        "",
        "> This is a review queue, not an approval to delete. Each file requires an explicit operator decision before archive/delete/replace.",
        "",
        "## Decision Vocabulary",
        "",
        "- `keep_and_wire` - keep the file and connect it to the named index/anchor.",
        "- `keep_excluded` - keep the file as a technical/export/runtime artifact that should not enter canonical navigation.",
        "- `archive_after_review` - move/archive only after operator review.",
        "- `archive_noncanonical_artifact` - move a confirmed non-canonical artifact into the connected hygiene archive and index it.",
        "- `delete_after_review` - delete only after operator review.",
        "- `replace_with_canonical` - discard a weaker duplicate only after confirming the canonical path is the kept file.",
        "- `manual_investigation` - content needs human review before action.",
        "",
        "## Review Items",
        "",
        "| File | Issue | Node Category | Keep / Canonical | Decision Hint | Recommended Action | Evidence |",
        "|------|-------|---------------|------------------|---------------|--------------------|----------|",
    ]
    for item in queue:
        evidence = "; ".join(item.get("evidence", [])[:4])
        lines.append(
            "| "
            f"`{_table_cell(item.get('file'))}` | "
            f"{_table_cell(item.get('issue_category'))} | "
            f"{_table_cell(item.get('node_category'))} | "
            f"`{_table_cell(item.get('keep_or_canonical'))}` | "
            f"`{_table_cell(item.get('decision_hint'))}` | "
            f"`{_table_cell(item.get('recommended_action'))}` | "
            f"{_table_cell(evidence)} |"
        )
    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    try:
        md_rel = md_path.relative_to(vault_root).as_posix()
        json_rel = json_path.relative_to(vault_root).as_posix()
    except ValueError:
        md_rel = md_path.as_posix()
        json_rel = json_path.as_posix()
    _ensure_graph_reports_index(vault_root, md_rel)
    artifacts = {"json": json_rel, "markdown": md_rel}
    report.review_artifacts = artifacts
    return artifacts


def _unique_destination(path: Path) -> Path:
    """Return a non-existing destination path by adding a numeric suffix if needed."""
    if not path.exists():
        return path
    for idx in range(1, 1000):
        candidate = path.with_name(f"{path.stem}-{idx}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"could not find unique destination for {path}")


def _append_wikilink_if_missing(index_path: Path, target_stem: str) -> bool:
    """Append a wikilink to an index/anchor if not already present."""
    content = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
    linked = extract_wikilink_stems(content)
    if target_stem in linked:
        return False
    if not content.endswith("\n"):
        content += "\n"
    content += f"\n*Review decision link: [[{target_stem}]]*\n"
    index_path.write_text(content, encoding="utf-8")
    return True


def _append_noncanonical_artifact_index(
    vault_root: Path,
    original_rel: str,
    archive_rel: str,
    queue_item: dict[str, Any],
    reason: str,
) -> bool:
    """Connect an archived non-canonical artifact to the hygiene review index."""
    index_path = vault_root / NONCANONICAL_ARTIFACT_INDEX_REL
    index_path.parent.mkdir(parents=True, exist_ok=True)
    content = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
    if f"`{archive_rel}`" in content:
        return False

    if not content.strip():
        content = "\n".join([
            "---",
            "title: Noncanonical Artifacts Index",
            "type: graph-hygiene-noncanonical-artifact-index",
            "status: CURRENT",
            "---",
            "",
            "# Noncanonical Artifacts Index",
            "",
            "This index preserves graph visibility for files graph hygiene moved out of canonical navigation.",
            "",
            "*Graph links: [[ChaseOS-Vault-Maintenance]] - [[Graph-Reports-Index]]*",
            "",
        ])

    stamp = _local_now().strftime("%Y-%m-%d")
    if f"## {stamp}" not in content:
        if not content.endswith("\n"):
            content += "\n"
        content += f"\n## {stamp}\n"
    if not content.endswith("\n"):
        content += "\n"

    issue_category = str(queue_item.get("issue_category") or "")
    node_category = str(queue_item.get("node_category") or "")
    reason_text = reason.strip() or _decision_reason(queue_item, "archive_noncanonical_artifact")
    archive_link = f"[[{Path(archive_rel).stem}]]"
    content += (
        f"- `{original_rel}` -> {archive_link} (`{archive_rel}`) "
        f"- `{issue_category}` / `{node_category}`; {reason_text}\n"
    )
    index_path.write_text(content, encoding="utf-8")
    return True


def _write_decision_log(vault_root: Path, result: DecisionApplyResult) -> str:
    log_dir = vault_root / DECISION_LOG_DIR_REL
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = _local_now().strftime("%Y-%m-%dT%H%M%S%f")
    log_rel = f"{DECISION_LOG_DIR_REL}/{stamp}-loose-node-decision-apply.json"
    log_path = vault_root / log_rel
    result.decision_log_path = log_rel
    _append_unique(result.files_written, log_rel)
    if _ensure_graph_reports_artifact_index_row(
        vault_root,
        log_rel,
        heading=f"Loose Node Decision Execution Log - {_local_now().strftime('%Y-%m-%d')}",
        status="Production decision log generated by vault_hygiene review-decision execution",
    ):
        index_rel = "07_LOGS/Graph-Reports/Graph-Reports-Index.md"
        _append_unique(result.files_written, index_rel)
    log_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    return log_rel


def _decision_reason(item: dict[str, Any], decision: str) -> str:
    """Build a concise reason for a proposed review decision."""
    file_rel = item.get("file", "")
    if decision == "replace_with_canonical":
        return f"Candidate appears to duplicate canonical `{item.get('canonical_path')}`; review before archive replacement."
    if decision == "delete_after_review":
        return "Candidate is empty/junk/placeholder; review before deletion."
    if decision == "keep_excluded":
        return f"Technical/review-only artifact should stay outside canonical graph navigation unless operator decides to wire it: `{file_rel}`."
    if decision == "archive_noncanonical_artifact":
        return (
            "Confirmed non-canonical artifact should leave the active graph while remaining "
            f"connected as review evidence: `{file_rel}`."
        )
    return "Manual investigation required before action."


def _decision_from_queue_item(item: dict[str, Any]) -> str:
    issue_category = item.get("issue_category")
    if issue_category == "duplicate_candidate" and item.get("canonical_path"):
        return "replace_with_canonical"
    if issue_category in {"empty_placeholder", "junk"}:
        return "delete_after_review"
    if issue_category in {"review_only_artifact", "runtime_markdown_loose"}:
        return "archive_noncanonical_artifact"
    if issue_category == "technical_readme_loose":
        return "keep_excluded"
    return "manual_investigation"


def _decision_effect(item: dict[str, Any], decision: str) -> str:
    file_rel = str(item.get("file") or "")
    canonical = str(item.get("canonical_path") or item.get("keep_or_canonical") or "")
    if decision == "replace_with_canonical":
        return (
            f"keep `{canonical}`; archive reviewed duplicate under "
            f"`{ARCHIVE_REVIEW_REL}/Replaced-Duplicates/YYYY-MM-DD/{file_rel}`"
        )
    if decision == "delete_after_review":
        return "delete this file only after explicit operator approval and matching hash"
    if decision == "archive_noncanonical_artifact":
        return (
            f"move `{file_rel}` into "
            f"`{NONCANONICAL_ARTIFACT_ARCHIVE_REL}/YYYY-MM-DD/{file_rel}` and index it from "
            f"`{NONCANONICAL_ARTIFACT_INDEX_REL}`"
        )
    if decision == "keep_excluded":
        return "keep file in place; record hash-bound keep_excluded decision outside graph navigation"
    if decision == "keep_and_wire":
        return f"keep file and wire it to `{canonical}`"
    return "manual investigation before action"


def _pending_proposal_decisions(
    vault_root: Path,
    exclude_rel: str | None = None,
) -> dict[str, list[dict[str, str]]]:
    """Return pending unapproved proposal decisions by file."""
    proposal_dir = vault_root / "07_LOGS" / "Graph-Reports"
    if not proposal_dir.exists():
        return {}
    excluded = (exclude_rel or "").replace("\\", "/")
    decisions_by_file: dict[str, list[dict[str, str]]] = {}
    for proposal_path in sorted(proposal_dir.glob("*proposal*.json")):
        try:
            proposal_rel = proposal_path.relative_to(vault_root).as_posix()
        except ValueError:
            proposal_rel = proposal_path.as_posix()
        if proposal_rel == excluded:
            continue
        if proposal_path.name.endswith("-approved.json"):
            continue
        approved_sibling = proposal_path.with_name(f"{proposal_path.stem}-approved{proposal_path.suffix}")
        if approved_sibling.exists():
            try:
                approved_payload = json.loads(approved_sibling.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError):
                approved_payload = {}
            if bool(approved_payload.get("operator_approved")):
                continue
        try:
            payload = json.loads(proposal_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        if bool(payload.get("operator_approved")):
            continue
        if payload.get("proposal_only") is not True:
            continue
        decisions = payload.get("decisions")
        if not isinstance(decisions, list):
            continue
        for decision in decisions:
            if not isinstance(decision, dict):
                continue
            file_rel = _safe_rel_path(str(decision.get("file", "")))
            if not file_rel:
                continue
            decisions_by_file.setdefault(file_rel, []).append({
                "source": proposal_rel,
                "decision": str(decision.get("decision") or ""),
            })
    return decisions_by_file


def _pending_proposal_files(vault_root: Path, exclude_rel: str | None = None) -> tuple[set[str], dict[str, set[str]]]:
    """Return files already staged in unapproved decision proposal JSON artifacts."""
    pending_decisions = _pending_proposal_decisions(vault_root, exclude_rel=exclude_rel)
    staged_files = set(pending_decisions)
    sources_by_file: dict[str, set[str]] = {}
    for file_rel, decisions in pending_decisions.items():
        sources_by_file[file_rel] = {decision["source"] for decision in decisions if decision.get("source")}
    return staged_files, sources_by_file


def build_review_summary(report: HygieneReport, vault_root: Path, max_items: int = 20) -> dict[str, Any]:
    """Build a compact operator-facing preview of loose-node review work."""
    queue = build_loose_node_review_queue(report, vault_root)
    pending_files, pending_source_map = _pending_proposal_files(vault_root)
    active_issue_counts: dict[str, int] = {}
    decision_counts: dict[str, int] = {}
    items: list[dict[str, Any]] = []
    for item in queue:
        issue_category = str(item.get("issue_category") or "")
        decision = _decision_from_queue_item(item)
        active_issue_counts[issue_category] = active_issue_counts.get(issue_category, 0) + 1
        decision_counts[decision] = decision_counts.get(decision, 0) + 1
        if len(items) >= max_items:
            continue
        file_rel = str(item.get("file") or "")
        items.append({
            "file": file_rel,
            "issue_category": issue_category,
            "node_category": item.get("node_category", ""),
            "recommended_decision": decision,
            "canonical_or_keep": item.get("canonical_path") or item.get("keep_or_canonical") or "",
            "effect": _decision_effect(item, decision),
            "pending_proposal_sources": sorted(pending_source_map.get(file_rel, set())) if file_rel in pending_files else [],
            "evidence": item.get("evidence", [])[:4],
        })
    return {
        "files_scanned": report.files_scanned,
        "total_issues": len(report.issues),
        "review_count": len(queue),
        "raw_issue_counts": summarize_issues(report),
        "issue_counts": dict(sorted(active_issue_counts.items())),
        "active_review_issue_counts": dict(sorted(active_issue_counts.items())),
        "recommended_decision_counts": dict(sorted(decision_counts.items())),
        "visible_graph_audit": report.visible_graph_audit,
        "preview_limit": max_items,
        "items": items,
    }


def render_review_summary(summary: dict[str, Any]) -> str:
    """Render a compact human-readable review summary for CLI/demo use."""
    lines = [
        "ChaseOS Vault Hygiene Review Summary",
        "",
        f"Files scanned: {summary.get('files_scanned')}",
        f"Total issues: {summary.get('total_issues')}",
        f"Review-gated loose nodes: {summary.get('review_count')}",
        "",
        "Raw scan issue categories:",
    ]
    for category, count in (summary.get("raw_issue_counts") or {}).items():
        lines.append(f"  - {category}: {count}")
    lines.append("")
    lines.append("Active review-queue categories:")
    for category, count in (summary.get("active_review_issue_counts") or summary.get("issue_counts") or {}).items():
        lines.append(f"  - {category}: {count}")
    lines.append("")
    lines.append("Recommended decisions:")
    for decision, count in (summary.get("recommended_decision_counts") or {}).items():
        lines.append(f"  - {decision}: {count}")
    lines.append("")
    visible = summary.get("visible_graph_audit") or {}
    if visible:
        lines.append("Visible graph audit:")
        lines.append(f"  - raw_zero_degree_count: {visible.get('raw_zero_degree_count', 0)}")
        lines.append(f"  - weak_degree_1_count: {visible.get('weak_degree_1_count', 0)}")
        lines.append(f"  - unresolved_link_target_count: {visible.get('unresolved_link_target_count', 0)}")
        lines.append(f"  - ambiguous_link_target_count: {visible.get('ambiguous_link_target_count', 0)}")
        lines.append(f"  - connected_duplicate_stem_count: {visible.get('connected_duplicate_stem_count', 0)}")
        lines.append(f"  - semantic_hub_gap_count: {visible.get('semantic_hub_gap_count', 0)}")
        lines.append("")
    lines.append(f"Preview items (first {summary.get('preview_limit')}):")
    for item in summary.get("items") or []:
        pending = item.get("pending_proposal_sources") or []
        pending_text = f" | staged: {', '.join(pending)}" if pending else ""
        lines.append(
            f"- {item.get('file')} [{item.get('issue_category')} / {item.get('node_category')}]"
        )
        lines.append(f"  decision: {item.get('recommended_decision')}{pending_text}")
        lines.append(f"  target/effect: {item.get('effect')}")
        evidence = item.get("evidence") or []
        if evidence:
            lines.append(f"  evidence: {'; '.join(str(e) for e in evidence)}")
    return "\n".join(lines)


def _write_decision_proposal_markdown(
    vault_root: Path,
    json_rel: str,
    payload: dict[str, Any],
    md_path: Path,
) -> str:
    """Write a human-review companion for an unapproved decision proposal."""
    decisions = payload.get("decisions") or []
    selection = payload.get("selection") or {}
    lines = [
        "---",
        f"title: {md_path.stem}",
        "type: graph-hygiene-decision-proposal",
        f"generated_at: {payload.get('generated_at', '')}",
        "status: UNAPPROVED",
        "---",
        "",
        f"# {md_path.stem}",
        "",
        "> Review surface for an unapproved loose-node decision proposal. Edit the JSON file, not this note, before execution.",
        "",
        "## Operator Status",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| JSON proposal | `{_table_cell(json_rel)}` |",
        f"| Operator approved | `{_table_cell(payload.get('operator_approved'))}` |",
        f"| Proposal only | `{_table_cell(payload.get('proposal_only'))}` |",
        f"| Decision count | `{len(decisions)}` |",
        f"| Categories | `{_table_cell(', '.join(selection.get('categories') or []))}` |",
        f"| Max items | `{_table_cell(selection.get('max_items'))}` |",
        f"| Include pending conflicts | `{_table_cell(selection.get('include_pending_conflicts', False))}` |",
        f"| Pending conflicts included | `{_table_cell(selection.get('pending_conflicts_included', 0))}` |",
        f"| Include pending same decision | `{_table_cell(selection.get('include_pending_same_decision', False))}` |",
        f"| Pending same decisions included | `{_table_cell(selection.get('pending_same_decisions_included', 0))}` |",
        "",
        "## Execution Rule",
        "",
        "Do not execute this proposal until the JSON has `operator_approved: true` and every destructive row has `approved: true` plus a matching expected hash.",
        "",
        "## Decisions",
        "",
        "| # | File | Decision | Approved | Canonical / Keep Path | Reason |",
        "|---|------|----------|----------|------------------------|--------|",
    ]
    for idx, decision in enumerate(decisions, start=1):
        canonical = decision.get("canonical_path") or decision.get("keep_or_canonical") or ""
        lines.append(
            f"| {idx} | `{_table_cell(decision.get('file'))}` | "
            f"`{_table_cell(decision.get('decision'))}` | "
            f"`{_table_cell(decision.get('approved'))}` | "
            f"`{_table_cell(canonical)}` | "
            f"{_table_cell(decision.get('reason'))} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Graph links: [[Graph-Reports-Index]] · [[ChaseOS-Vault-Maintenance]]*")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    try:
        md_rel = md_path.relative_to(vault_root).as_posix()
    except ValueError:
        md_rel = md_path.as_posix()
    _ensure_graph_reports_index(
        vault_root,
        md_rel,
        heading=f"Loose Node Decision Proposal - {_local_now().strftime('%Y-%m-%d')}",
        status="Generated by vault_hygiene decision proposal guard",
    )
    return md_rel


def generate_markdown_handover(proposal: dict[str, Any], vault_root: Path, json_path: Path) -> Path:
    """Generate a human-readable markdown handover document from a proposal JSON."""
    dt = _local_now().strftime("%Y-%m-%d")
    out_name = f"{json_path.stem}-handover.md"
    out_path = vault_root / "07_LOGS/Graph-Reports" / out_name
    
    lines = [
        f"# Graph Hygiene Review Handover ({dt})",
        "",
        "> [!IMPORTANT]",
        "> This document lists files that require operator review.",
        f"> The programmatic decisions are staged in `{json_path.name}`.",
        "> Set `operator_approved: true` in that JSON to approve.",
        "",
        "## Pending Review Items",
        ""
    ]
    
    grouped: dict[str, list[dict]] = {}
    for item in proposal.get("decisions", []):
        cat = item.get("decision", "unknown")
        grouped.setdefault(cat, []).append(item)
        
    for cat, items in sorted(grouped.items()):
        lines.append(f"### {cat.replace('_', ' ').title()}")
        lines.append("")
        for item in items:
            file_path = item.get("file", "")
            target = item.get("link_target", "")
            if target:
                lines.append(f"- **File:** `{file_path}` -> **Broken Link:** `{target}`")
            else:
                lines.append(f"- **File:** `{file_path}`")
            reason = item.get("reason", "")
            if reason:
                lines.append(f"  - *Reason:* {reason}")
        lines.append("")
        
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def generate_consolidated_handover(report: HygieneReport, vault_root: Path) -> Path:
    """Generate a single, unified checklist-style handover document for all pending issues."""
    dt = _local_now().strftime("%Y-%m-%d")
    out_name = f"{dt}-Vault-Hygiene-Handover.md"
    out_path = vault_root / "07_LOGS/Graph-Reports" / out_name
    
    lines = [
        f"# Consolidated Hygiene Review Handover ({dt})",
        "",
        "> [!IMPORTANT]",
        "> This document lists all items across the vault that currently require operator review.",
        "> This includes loose nodes, unresolved links, and ambiguous targets.",
        "",
        "## Pending Review Items",
        ""
    ]
    
    grouped: dict[str, list[Issue]] = {}
    for issue in report.issues:
        if issue.severity == "review" or issue.category in {"unresolved_link_target", "ambiguous_link_target"}:
            grouped.setdefault(issue.category, []).append(issue)
            
    if not grouped:
        lines.append("No pending review items found.")
        lines.append("")
    else:
        for cat, issues in sorted(grouped.items()):
            lines.append(f"### {cat.replace('_', ' ').title()}")
            lines.append("")
            for issue in issues:
                target = issue.index_path or ""
                evidence_text = ""
                if issue.evidence:
                    evidence_text = f"  - *Evidence:* {'; '.join(issue.evidence[:3])}"
                
                if target:
                    lines.append(f"- **File:** `{issue.file_path}` -> **Target:** `{target}`")
                else:
                    lines.append(f"- **File:** `{issue.file_path}`")
                
                if evidence_text:
                    lines.append(evidence_text)
            lines.append("")
        
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def propose_review_decisions(
    report: HygieneReport,
    vault_root: Path,
    output_path: str | None = None,
    max_items: int = 20,
    categories: list[str] | None = None,
    include_pending_conflicts: bool = False,
    include_pending_same_decision: bool = False,
) -> dict[str, Any]:
    """Write a small unapproved operator decision proposal from the current review queue."""
    category_filter = set(categories or DEFAULT_PROPOSAL_CATEGORIES)
    out_rel = output_path or f"07_LOGS/Graph-Reports/{_local_now().strftime('%Y-%m-%d')}-loose-node-decision-proposal.json"
    out_path = _resolve_within_vault(vault_root, out_rel)
    try:
        out_rel = out_path.relative_to(vault_root).as_posix()
    except ValueError:
        out_rel = out_path.as_posix()
    pending_decision_map = _pending_proposal_decisions(vault_root, exclude_rel=out_rel)
    pending_files = set(pending_decision_map)
    pending_source_map = {
        file_rel: {decision["source"] for decision in decisions if decision.get("source")}
        for file_rel, decisions in pending_decision_map.items()
    }
    queue = build_loose_node_review_queue(report, vault_root)
    decisions: list[dict[str, Any]] = []
    skipped_pending = 0
    included_pending_conflicts = 0
    included_pending_same_decisions = 0
    used_pending_sources: set[str] = set()
    for item in queue:
        issue_category = str(item.get("issue_category") or "")
        if issue_category not in category_filter:
            continue
        item_file = str(item.get("file") or "")
        decision = _decision_from_queue_item(item)
        pending_include_mode = ""
        if item_file in pending_files:
            pending_decisions = pending_decision_map.get(item_file, [])
            pending_decision_values = {
                str(pending.get("decision") or "")
                for pending in pending_decisions
                if pending.get("decision")
            }
            pending_sources = pending_source_map.get(item_file, set())
            if include_pending_conflicts and decision not in pending_decision_values:
                included_pending_conflicts += 1
                pending_include_mode = "conflict"
                used_pending_sources.update(pending_sources)
            elif include_pending_same_decision and decision in pending_decision_values:
                included_pending_same_decisions += 1
                pending_include_mode = "same_decision"
                used_pending_sources.update(pending_sources)
            else:
                skipped_pending += 1
                used_pending_sources.update(pending_sources)
                continue
        if decision == "manual_investigation":
            continue
        decision_item: dict[str, Any] = {
            "file": item["file"],
            "decision": decision,
            "file_sha256": item.get("file_sha256", ""),
            "reason": _decision_reason(item, decision),
            "review_required": True,
        }
        if decision in DESTRUCTIVE_REVIEW_DECISIONS:
            decision_item["approved"] = False
            decision_item["expected_sha256"] = item.get("file_sha256", "")
        if decision == "replace_with_canonical":
            decision_item["canonical_path"] = item.get("canonical_path", "")
        if decision == "keep_excluded":
            decision_item["approved"] = False
        if item_file in pending_files and pending_include_mode == "conflict":
            pending_decisions = pending_decision_map.get(item_file, [])
            decision_item["supersedes_pending_proposal_sources"] = sorted(
                {pending["source"] for pending in pending_decisions if pending.get("source")}
            )
            decision_item["supersedes_pending_decisions"] = sorted(
                {pending["decision"] for pending in pending_decisions if pending.get("decision")}
            )
        if item_file in pending_files and pending_include_mode == "same_decision":
            pending_decisions = pending_decision_map.get(item_file, [])
            decision_item["consolidates_pending_proposal_sources"] = sorted(
                {pending["source"] for pending in pending_decisions if pending.get("source")}
            )
            decision_item["consolidates_pending_decisions"] = sorted(
                {pending["decision"] for pending in pending_decisions if pending.get("decision")}
            )
        decisions.append(decision_item)
        if len(decisions) >= max_items:
            break

    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "operator_approved": False,
        "approved_by": "",
        "proposal_only": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_review_queue": report.review_artifacts.get("json") or "current scan",
        "selection": {
            "max_items": max_items,
            "categories": sorted(category_filter),
            "pending_proposal_files_skipped": skipped_pending,
            "pending_proposal_sources": sorted(used_pending_sources),
            "pending_conflicts_included": included_pending_conflicts,
            "include_pending_conflicts": include_pending_conflicts,
            "pending_same_decisions_included": included_pending_same_decisions,
            "include_pending_same_decision": include_pending_same_decision,
        },
        "execution_note": "Do not execute until operator_approved=true and each destructive decision has approved=true.",
        "decisions": decisions,
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    try:
        rel = out_path.relative_to(vault_root).as_posix()
    except ValueError:
        rel = out_path.as_posix()
    md_rel = _write_decision_proposal_markdown(vault_root, rel, payload, out_path.with_suffix(".md"))
    
    # Generate the requested operator handover checklist document
    generate_markdown_handover(payload, vault_root, out_path)
    
    return {
        "proposal_path": rel,
        "proposal_markdown_path": md_rel,
        "proposal_count": len(decisions),
        "categories": sorted(category_filter),
        "pending_proposal_files_skipped": skipped_pending,
        "pending_proposal_sources": sorted(used_pending_sources),
        "pending_conflicts_included": included_pending_conflicts,
        "include_pending_conflicts": include_pending_conflicts,
        "pending_same_decisions_included": included_pending_same_decisions,
        "include_pending_same_decision": include_pending_same_decision,
        "operator_approved": False,
        "decisions": decisions,
    }


def _write_unresolved_link_proposal_markdown(
    vault_root: Path,
    json_rel: str,
    payload: dict[str, Any],
    md_path: Path,
) -> str:
    """Write a human-review companion for unresolved wikilink target proposals."""
    decisions = payload.get("decisions") or []
    selection = payload.get("selection") or {}
    lines = [
        "---",
        f"title: {md_path.stem}",
        "type: graph-hygiene-unresolved-link-proposal",
        f"generated_at: {payload.get('generated_at', '')}",
        "status: UNAPPROVED",
        "---",
        "",
        f"# {md_path.stem}",
        "",
        "> Review surface for unresolved wikilink targets. Edit the JSON file, not this note, before any follow-up execution feature consumes it.",
        "",
        "## Operator Status",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| JSON proposal | `{_table_cell(json_rel)}` |",
        f"| Operator approved | `{_table_cell(payload.get('operator_approved'))}` |",
        f"| Proposal only | `{_table_cell(payload.get('proposal_only'))}` |",
        f"| Proposal kind | `{_table_cell(payload.get('proposal_kind'))}` |",
        f"| Decision count | `{len(decisions)}` |",
        f"| Max items | `{_table_cell(selection.get('max_items'))}` |",
        "",
        "## Execution Rule",
        "",
        "This proposal is not executable by Graph Hygiene yet. Each row needs an operator decision: create the target node, rename the link to an existing node, remove the link, or defer it.",
        "",
        "## Decisions",
        "",
        "| # | Source File | Missing Target | Decision | Replacement / Create Path | Reason |",
        "|---|-------------|----------------|----------|---------------------------|--------|",
    ]
    for idx, decision in enumerate(decisions, start=1):
        target_path = decision.get("replacement_target") or decision.get("create_path") or ""
        lines.append(
            f"| {idx} | `{_table_cell(decision.get('file'))}` | "
            f"`{_table_cell(decision.get('link_target'))}` | "
            f"`{_table_cell(decision.get('decision'))}` | "
            f"`{_table_cell(target_path)}` | "
            f"{_table_cell(decision.get('reason'))} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Graph links: [[Graph-Reports-Index]] · [[ChaseOS-Vault-Maintenance]]*")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    try:
        md_rel = md_path.relative_to(vault_root).as_posix()
    except ValueError:
        md_rel = md_path.as_posix()
    _ensure_graph_reports_index(
        vault_root,
        md_rel,
        heading=f"Unresolved Link Proposal - {_local_now().strftime('%Y-%m-%d')}",
        status="Generated by vault_hygiene unresolved-link proposal guard",
    )
    return md_rel


def _pending_unresolved_link_proposal_keys(
    vault_root: Path,
    exclude_rel: str | None = None,
) -> set[tuple[str, str]]:
    """Return unresolved link rows already staged in unapproved proposal artifacts."""
    proposal_dir = vault_root / "07_LOGS" / "Graph-Reports"
    if not proposal_dir.exists():
        return set()
    excluded = (exclude_rel or "").replace("\\", "/")
    keys: set[tuple[str, str]] = set()
    for proposal_path in sorted(proposal_dir.glob("*unresolved*proposal*.json")):
        try:
            proposal_rel = proposal_path.relative_to(vault_root).as_posix()
        except ValueError:
            proposal_rel = proposal_path.as_posix()
        if proposal_rel == excluded:
            continue
        if proposal_path.name.endswith("-approved.json"):
            continue
        approved_sibling = proposal_path.with_name(f"{proposal_path.stem}-approved{proposal_path.suffix}")
        if approved_sibling.exists():
            try:
                approved_payload = json.loads(approved_sibling.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError):
                approved_payload = {}
            if bool(approved_payload.get("operator_approved")):
                continue
        try:
            payload = json.loads(proposal_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("proposal_kind") != "unresolved_link_target_review":
            continue
        if bool(payload.get("operator_approved")):
            continue
        decisions = payload.get("decisions")
        if not isinstance(decisions, list):
            continue
        for decision in decisions:
            if not isinstance(decision, dict):
                continue
            file_rel = _safe_rel_path(str(decision.get("file") or ""))
            link_target = str(decision.get("link_target") or "")
            if file_rel and link_target:
                keys.add((file_rel, link_target))
    return keys


def propose_unresolved_link_decisions(
    report: HygieneReport,
    vault_root: Path,
    output_path: str | None = None,
    max_items: int = 50,
    include_pending: bool = False,
) -> dict[str, Any]:
    """Write an unapproved proposal for unresolved wikilink target decisions."""
    out_rel = output_path or f"07_LOGS/Graph-Reports/{_local_now().strftime('%Y-%m-%d')}-unresolved-link-decision-proposal.json"
    out_path = _resolve_within_vault(vault_root, out_rel)
    try:
        out_rel = out_path.relative_to(vault_root).as_posix()
    except ValueError:
        out_rel = out_path.as_posix()

    pending_keys = _pending_unresolved_link_proposal_keys(vault_root, exclude_rel=out_rel)
    decisions: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    skipped_pending = 0
    for issue in report.issues:
        if issue.category != "unresolved_link_target":
            continue
        link_target = issue.index_path or ""
        key = (issue.file_path, link_target)
        if key in seen:
            continue
        if key in pending_keys and not include_pending:
            skipped_pending += 1
            seen.add(key)
            continue
        seen.add(key)
        decisions.append({
            "file": issue.file_path,
            "file_sha256": _issue_hash(vault_root, issue.file_path),
            "link_target": link_target,
            "decision": "review_target_create_rename_or_unlink",
            "allowed_decisions": [
                "create_target_node",
                "rename_link_to_existing_node",
                "remove_link",
                "defer",
            ],
            "approved": False,
            "replacement_target": "",
            "create_path": "",
            "reason": "Unresolved wikilink target requires operator decision; Graph Hygiene must not guess.",
            "review_required": True,
            "evidence": issue.evidence[:4],
        })
        if len(decisions) >= max_items:
            break

    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "operator_approved": False,
        "approved_by": "",
        "proposal_only": True,
        "proposal_kind": "unresolved_link_target_review",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "selection": {
            "max_items": max_items,
            "category": "unresolved_link_target",
            "include_pending": include_pending,
            "pending_unresolved_rows_skipped": skipped_pending,
        },
        "execution_note": "Proposal only. Do not execute until a future governed unresolved-link decision applier exists and the operator approves each row.",
        "decisions": decisions,
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_rel = _write_unresolved_link_proposal_markdown(vault_root, out_rel, payload, out_path.with_suffix(".md"))
    
    # Generate the requested operator handover checklist document
    generate_markdown_handover(payload, vault_root, out_path)
    
    return {
        "proposal_path": out_rel,
        "proposal_markdown_path": md_rel,
        "proposal_count": len(decisions),
        "proposal_kind": "unresolved_link_target_review",
        "pending_unresolved_rows_skipped": skipped_pending,
        "include_pending": include_pending,
        "operator_approved": False,
        "decisions": decisions,
    }


UNRESOLVED_LINK_ALLOWED_DECISIONS = {
    "create_target_node",
    "rename_link_to_existing_node",
    "remove_link",
    "defer",
}


def _unresolved_create_path_matches_target(create_path: str, link_target: str) -> bool:
    target_base, _heading, _alias = _split_wikilink_target(link_target)
    target_base = target_base.removesuffix(".md")
    create_target = _wikilink_target_for_rel(create_path)
    return create_target == target_base or Path(create_target).stem == Path(target_base).stem


def _validate_unresolved_decision_row(
    vault_root: Path,
    raw: dict[str, Any],
    operator_approved: bool,
) -> dict[str, Any]:
    file_rel = _safe_rel_path(str(raw.get("file") or ""))
    link_target = str(raw.get("link_target") or "")
    decision = str(raw.get("decision") or "")
    replacement_target = _safe_rel_path(str(raw.get("replacement_target") or ""))
    create_path = _safe_rel_path(str(raw.get("create_path") or ""))
    blockers: list[str] = []
    warnings: list[str] = []
    writes: list[str] = []

    if not file_rel:
        blockers.append("missing file")
    if not link_target:
        blockers.append("missing link_target")
    if not decision:
        blockers.append("decision must be set explicitly")
    elif decision == "review_target_create_rename_or_unlink":
        blockers.append("review placeholder decision is not executable; set decision to an allowed decision")
    elif decision not in UNRESOLVED_LINK_ALLOWED_DECISIONS:
        blockers.append(f"unsupported decision: {decision}")
    allowed_from_row = raw.get("allowed_decisions")
    if isinstance(allowed_from_row, list) and decision and decision not in allowed_from_row:
        blockers.append("decision is not listed in row allowed_decisions")
    if not operator_approved:
        blockers.append("operator_approved must be true")
    if not bool(raw.get("approved")):
        blockers.append("per-row approved must be true")

    current_hash = ""
    if file_rel:
        try:
            source_path = _resolve_within_vault(vault_root, file_rel)
        except ValueError as exc:
            blockers.append(str(exc))
            source_path = None
        if source_path is not None:
            if not source_path.exists():
                blockers.append("source file does not exist")
            else:
                current_hash = file_sha256(source_path)
                expected_hash = str(raw.get("file_sha256") or "")
                if expected_hash and expected_hash != current_hash:
                    blockers.append("source file hash does not match proposal")
    if file_rel and link_target and not _ambiguous_source_has_target(vault_root, file_rel, link_target):
        blockers.append("source file no longer contains the unresolved wikilink target")

    if decision == "create_target_node":
        if not create_path:
            blockers.append("create_path is required")
        elif not create_path.lower().endswith(".md"):
            blockers.append("create_path must end with .md")
        elif not _unresolved_create_path_matches_target(create_path, link_target):
            blockers.append("create_path must match the unresolved link target stem or path")
        else:
            try:
                target_path = _resolve_within_vault(vault_root, create_path)
            except ValueError as exc:
                blockers.append(str(exc))
                target_path = None
            if target_path is not None and target_path.exists():
                blockers.append("create_path already exists")
            writes.extend([file_rel, create_path])
    elif decision == "rename_link_to_existing_node":
        if not replacement_target:
            blockers.append("replacement_target is required")
        elif not replacement_target.lower().endswith(".md"):
            blockers.append("replacement_target must end with .md")
        else:
            try:
                replacement_path = _resolve_within_vault(vault_root, replacement_target)
            except ValueError as exc:
                blockers.append(str(exc))
                replacement_path = None
            if replacement_path is not None and not replacement_path.exists():
                blockers.append("replacement_target does not exist")
            if replacement_target and _wikilink_target_for_rel(replacement_target) == _split_wikilink_target(link_target)[0]:
                blockers.append("replacement_target must differ from the unresolved target")
            if replacement_target:
                writes.append(file_rel)
    elif decision == "remove_link":
        if not str(raw.get("reason") or "").strip():
            blockers.append("reason is required for remove_link")
        if file_rel:
            writes.append(file_rel)
    elif decision == "defer":
        warnings.append("defer records review debt only; no graph mutation should occur")

    effect = {
        "create_target_node": f"create target node {create_path} for {link_target} and keep/update {file_rel}",
        "rename_link_to_existing_node": f"rename {link_target} in {file_rel} to {replacement_target}",
        "remove_link": f"remove {link_target} from {file_rel}",
        "defer": "defer this unresolved link decision",
    }.get(decision, "")

    return {
        "file": file_rel,
        "link_target": link_target,
        "decision": decision,
        "approved": bool(raw.get("approved")),
        "operator_approved": operator_approved,
        "execution_ready": not blockers,
        "execution_blockers": blockers,
        "warnings": warnings,
        "current_sha256": current_hash,
        "replacement_target": replacement_target,
        "create_path": create_path,
        "effect": effect,
        "writes": sorted(set(writes)),
        "production_execution_allowed": False,
    }


def validate_unresolved_link_decisions(
    vault_root: Path,
    decisions_path: Path,
) -> dict[str, Any]:
    """Validate an operator-edited unresolved-link proposal without executing it."""
    try:
        payload = json.loads(decisions_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "status": "blocked",
            "valid": False,
            "production_execution_allowed": False,
            "errors": [f"could not load unresolved-link decision file: {exc}"],
            "decision_count": 0,
            "planned_actions": [],
        }

    errors: list[str] = []
    if payload.get("proposal_kind") != "unresolved_link_target_review":
        errors.append("proposal_kind must be unresolved_link_target_review")
    decisions = payload.get("decisions")
    if not isinstance(decisions, list):
        errors.append("decision file must contain a decisions list")
        decisions = []
    operator_approved = bool(payload.get("operator_approved"))
    if not operator_approved:
        errors.append("operator_approved must be true")
    if payload.get("proposal_only") is not True:
        errors.append("proposal_only must remain true")

    planned_actions = [
        _validate_unresolved_decision_row(vault_root, decision, operator_approved)
        for decision in decisions
        if isinstance(decision, dict)
    ]
    malformed_count = sum(1 for decision in decisions if not isinstance(decision, dict))
    if malformed_count:
        errors.append(f"{malformed_count} decision rows are not objects")

    blocked_count = sum(1 for action in planned_actions if not action["execution_ready"])
    warning_count = sum(len(action.get("warnings") or []) for action in planned_actions)
    status = "valid_non_executing" if not errors and not blocked_count else "blocked"
    return {
        "status": status,
        "valid": status == "valid_non_executing",
        "proposal_kind": payload.get("proposal_kind"),
        "operator_approved": operator_approved,
        "approval_preview_only": bool(payload.get("approval_preview_only")),
        "production_execution_allowed": False,
        "source_decision_file": decisions_path.relative_to(vault_root).as_posix()
        if decisions_path.is_relative_to(vault_root)
        else str(decisions_path),
        "decision_count": len(planned_actions),
        "blocked_count": blocked_count,
        "warning_count": warning_count,
        "errors": errors,
        "planned_actions": planned_actions,
    }


def write_unresolved_approval_preview_copy(
    vault_root: Path,
    decisions_path: Path,
    output_path: str | None = None,
    approved_by: str = "approval-preview",
) -> dict[str, Any]:
    """Write a non-executable approval-preview copy of an unresolved-link proposal."""
    payload = json.loads(decisions_path.read_text(encoding="utf-8-sig"))
    decisions = payload.get("decisions")
    if not isinstance(decisions, list):
        raise ValueError("decision file must contain a 'decisions' list")
    preview_payload = dict(payload)
    preview_payload["operator_approved"] = True
    preview_payload["approved_by"] = approved_by
    preview_payload["approval_preview_only"] = True
    preview_payload["production_execution_allowed"] = False
    preview_payload["generated_from"] = decisions_path.relative_to(vault_root).as_posix() if decisions_path.is_relative_to(vault_root) else str(decisions_path)
    preview_payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    preview_payload["execution_note"] = (
        "Unresolved-link approval-preview copy only. This validates the proposed "
        "post-approval shape and is not accepted by any production applier."
    )
    if output_path:
        out_path = Path(output_path)
        if not out_path.is_absolute():
            out_path = vault_root / out_path
    else:
        try:
            rel = decisions_path.relative_to(vault_root)
            out_path = vault_root / rel.with_name(f"{rel.stem}-approval-preview{rel.suffix}")
        except ValueError:
            out_path = decisions_path.with_name(f"{decisions_path.stem}-approval-preview{decisions_path.suffix}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(preview_payload, indent=2), encoding="utf-8")
    try:
        out_rel = out_path.relative_to(vault_root).as_posix()
    except ValueError:
        out_rel = out_path.as_posix()
    _ensure_graph_reports_artifact_index_row(
        vault_root,
        out_rel,
        heading=f"Unresolved Link Approval Preview - {_local_now().strftime('%Y-%m-%d')}",
        status="Non-executable approval-preview JSON; no production applier exists",
    )
    validation = validate_unresolved_link_decisions(vault_root, out_path)
    return {
        "approval_preview_path": out_rel,
        "approval_preview_only": True,
        "production_execution_allowed": False,
        "decisions": len(decisions),
        "validation": validation,
    }


def _parse_issue_evidence_value(issue: Issue, key: str) -> str:
    prefix = f"{key}="
    for value in issue.evidence:
        if value.startswith(prefix):
            return value[len(prefix):]
    return ""


def _parse_ambiguous_candidates(issue: Issue) -> list[str]:
    raw = _parse_issue_evidence_value(issue, "candidates")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _candidate_review_hint(source_rel: str, candidate_rel: str) -> str:
    source_parent = Path(source_rel).parent.as_posix()
    candidate_parent = Path(candidate_rel).parent.as_posix()
    if source_parent == candidate_parent:
        return "same_folder_candidate"
    if source_rel.split("/", 1)[0] == candidate_rel.split("/", 1)[0]:
        return "same_top_level_candidate"
    if candidate_rel.startswith("99_ARCHIVE/"):
        return "archive_candidate"
    if candidate_rel.startswith("core_export/"):
        return "core_export_candidate"
    return "cross_graph_candidate"


def _write_ambiguous_link_proposal_markdown(
    vault_root: Path,
    json_rel: str,
    payload: dict[str, Any],
    md_path: Path,
) -> str:
    """Write a human-review companion for ambiguous wikilink target proposals."""
    decisions = payload.get("decisions") or []
    selection = payload.get("selection") or {}
    lines = [
        "---",
        f"title: {md_path.stem}",
        "type: graph-hygiene-ambiguous-link-proposal",
        f"generated_at: {payload.get('generated_at', '')}",
        "status: UNAPPROVED",
        "---",
        "",
        f"# {md_path.stem}",
        "",
        "> Review surface for ambiguous duplicate-stem wikilinks. Edit the JSON file, not this note, before any follow-up execution feature consumes it.",
        "",
        "## Operator Status",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| JSON proposal | `{_table_cell(json_rel)}` |",
        f"| Operator approved | `{_table_cell(payload.get('operator_approved'))}` |",
        f"| Proposal only | `{_table_cell(payload.get('proposal_only'))}` |",
        f"| Proposal kind | `{_table_cell(payload.get('proposal_kind'))}` |",
        f"| Decision count | `{len(decisions)}` |",
        f"| Max items | `{_table_cell(selection.get('max_items'))}` |",
        "",
        "## Execution Rule",
        "",
        "This proposal is not executable by Graph Hygiene yet. Each row needs an operator decision: path-qualify the link to one existing node, create an alias node, rename/merge a duplicate, remove the link, or defer it.",
        "",
        "## Decisions",
        "",
        "| # | Source File | Ambiguous Target | Recommended Decision | Candidate Count | Selected Target / Alias Path | Reason |",
        "|---|-------------|------------------|----------------------|-----------------|------------------------------|--------|",
    ]
    for idx, decision in enumerate(decisions, start=1):
        target_path = decision.get("selected_target") or decision.get("alias_path") or ""
        lines.append(
            f"| {idx} | `{_table_cell(decision.get('file'))}` | "
            f"`{_table_cell(decision.get('link_target'))}` | "
            f"`{_table_cell(decision.get('recommended_decision'))}` | "
            f"`{_table_cell(decision.get('candidate_count'))}` | "
            f"`{_table_cell(target_path)}` | "
            f"{_table_cell(decision.get('reason'))} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Graph links: [[Graph-Reports-Index]] · [[ChaseOS-Vault-Maintenance]]*")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    try:
        md_rel = md_path.relative_to(vault_root).as_posix()
    except ValueError:
        md_rel = md_path.as_posix()
    _ensure_graph_reports_index(
        vault_root,
        md_rel,
        heading=f"Ambiguous Link Proposal - {_local_now().strftime('%Y-%m-%d')}",
        status="Generated by vault_hygiene ambiguous-link proposal guard",
    )
    return md_rel


def _pending_ambiguous_link_proposal_keys(
    vault_root: Path,
    exclude_rel: str | None = None,
) -> set[tuple[str, str]]:
    """Return ambiguous link rows already staged in unapproved proposal artifacts."""
    proposal_dir = vault_root / "07_LOGS" / "Graph-Reports"
    if not proposal_dir.exists():
        return set()
    excluded = (exclude_rel or "").replace("\\", "/")
    keys: set[tuple[str, str]] = set()
    for proposal_path in sorted(proposal_dir.glob("*ambiguous*proposal*.json")):
        try:
            proposal_rel = proposal_path.relative_to(vault_root).as_posix()
        except ValueError:
            proposal_rel = proposal_path.as_posix()
        if proposal_rel == excluded:
            continue
        if proposal_path.name.endswith("-approved.json"):
            continue
        approved_sibling = proposal_path.with_name(f"{proposal_path.stem}-approved{proposal_path.suffix}")
        if approved_sibling.exists():
            try:
                approved_payload = json.loads(approved_sibling.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError):
                approved_payload = {}
            if bool(approved_payload.get("operator_approved")):
                continue
        try:
            payload = json.loads(proposal_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("proposal_kind") != "ambiguous_link_target_review":
            continue
        if bool(payload.get("operator_approved")):
            continue
        decisions = payload.get("decisions")
        if not isinstance(decisions, list):
            continue
        for decision in decisions:
            if not isinstance(decision, dict):
                continue
            file_rel = _safe_rel_path(str(decision.get("file") or ""))
            link_target = str(decision.get("link_target") or "")
            if file_rel and link_target:
                keys.add((file_rel, link_target))
    return keys


def propose_ambiguous_link_decisions(
    report: HygieneReport,
    vault_root: Path,
    output_path: str | None = None,
    max_items: int = 50,
    include_pending: bool = False,
) -> dict[str, Any]:
    """Write an unapproved proposal for ambiguous duplicate-stem wikilink decisions."""
    out_rel = output_path or f"07_LOGS/Graph-Reports/{_local_now().strftime('%Y-%m-%d')}-ambiguous-link-decision-proposal.json"
    out_path = _resolve_within_vault(vault_root, out_rel)
    try:
        out_rel = out_path.relative_to(vault_root).as_posix()
    except ValueError:
        out_rel = out_path.as_posix()

    pending_keys = _pending_ambiguous_link_proposal_keys(vault_root, exclude_rel=out_rel)
    decisions: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    skipped_pending = 0
    for issue in report.issues:
        if issue.category != "ambiguous_link_target_review":
            continue
        link_target = issue.index_path or _parse_issue_evidence_value(issue, "target")
        key = (issue.file_path, link_target)
        if key in seen:
            continue
        if key in pending_keys and not include_pending:
            skipped_pending += 1
            seen.add(key)
            continue
        seen.add(key)
        candidates = _parse_ambiguous_candidates(issue)
        candidate_rows = [
            {
                "path": candidate,
                "sha256": _issue_hash(vault_root, candidate),
                "node_category": infer_node_category(candidate),
                "review_hint": _candidate_review_hint(issue.file_path, candidate),
            }
            for candidate in candidates
        ]
        decisions.append({
            "file": issue.file_path,
            "file_sha256": _issue_hash(vault_root, issue.file_path),
            "link_target": link_target,
            "recommended_decision": "operator_select_path_qualified_target",
            "allowed_decisions": [
                "path_qualify_to_existing_node",
                "create_alias_node",
                "rename_or_merge_duplicate_node",
                "remove_link",
                "defer",
            ],
            "approved": False,
            "selected_target": "",
            "alias_path": "",
            "candidate_count": len(candidate_rows),
            "candidates": candidate_rows,
            "reason": "Ambiguous wikilink resolves to multiple same-stem nodes; Graph Hygiene must not guess which node the operator intended.",
            "review_required": True,
            "evidence": issue.evidence[:4],
        })
        if len(decisions) >= max_items:
            break

    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "operator_approved": False,
        "approved_by": "",
        "proposal_only": True,
        "proposal_kind": "ambiguous_link_target_review",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "selection": {
            "max_items": max_items,
            "category": "ambiguous_link_target_review",
            "include_pending": include_pending,
            "pending_ambiguous_rows_skipped": skipped_pending,
        },
        "execution_note": "Proposal only. Do not execute until a future governed ambiguous-link decision applier exists and the operator approves each row.",
        "decisions": decisions,
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_rel = _write_ambiguous_link_proposal_markdown(vault_root, out_rel, payload, out_path.with_suffix(".md"))
    return {
        "proposal_path": out_rel,
        "proposal_markdown_path": md_rel,
        "proposal_count": len(decisions),
        "proposal_kind": "ambiguous_link_target_review",
        "pending_ambiguous_rows_skipped": skipped_pending,
        "include_pending": include_pending,
        "operator_approved": False,
        "decisions": decisions,
    }


AMBIGUOUS_LINK_ALLOWED_DECISIONS = {
    "path_qualify_to_existing_node",
    "create_alias_node",
    "rename_or_merge_duplicate_node",
    "remove_link",
    "defer",
}


def _candidate_by_path(decision: dict[str, Any]) -> dict[str, dict[str, Any]]:
    candidates = decision.get("candidates")
    rows: dict[str, dict[str, Any]] = {}
    if not isinstance(candidates, list):
        return rows
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        rel = _safe_rel_path(str(candidate.get("path") or ""))
        if rel:
            rows[rel] = candidate
    return rows


def _ambiguous_source_has_target(vault_root: Path, file_rel: str, link_target: str) -> bool:
    try:
        source_path = _resolve_within_vault(vault_root, file_rel)
    except ValueError:
        return False
    if not source_path.exists():
        return False
    try:
        linked = extract_wikilink_stems(source_path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return False
    target_base, _heading, _alias = _split_wikilink_target(link_target)
    return target_base in linked or Path(target_base).stem in linked


def _validate_ambiguous_decision_row(
    vault_root: Path,
    raw: dict[str, Any],
    operator_approved: bool,
) -> dict[str, Any]:
    file_rel = _safe_rel_path(str(raw.get("file") or ""))
    link_target = str(raw.get("link_target") or "")
    decision = str(raw.get("decision") or "")
    candidates = _candidate_by_path(raw)
    blockers: list[str] = []
    warnings: list[str] = []
    writes: list[str] = []
    selected_target = _safe_rel_path(str(raw.get("selected_target") or ""))
    alias_path = _safe_rel_path(str(raw.get("alias_path") or ""))

    if not file_rel:
        blockers.append("missing file")
    if not link_target:
        blockers.append("missing link_target")
    if not decision:
        blockers.append("decision must be set explicitly")
    elif decision == "operator_select_path_qualified_target":
        blockers.append("recommended_decision is not executable; set decision to an allowed decision")
    elif decision not in AMBIGUOUS_LINK_ALLOWED_DECISIONS:
        blockers.append(f"unsupported decision: {decision}")
    allowed_from_row = raw.get("allowed_decisions")
    if isinstance(allowed_from_row, list) and decision and decision not in allowed_from_row:
        blockers.append("decision is not listed in row allowed_decisions")
    if not operator_approved:
        blockers.append("operator_approved must be true")
    if not bool(raw.get("approved")):
        blockers.append("per-row approved must be true")

    current_hash = ""
    if file_rel:
        try:
            source_path = _resolve_within_vault(vault_root, file_rel)
        except ValueError as exc:
            blockers.append(str(exc))
            source_path = None
        if source_path is not None:
            if not source_path.exists():
                blockers.append("source file does not exist")
            else:
                current_hash = file_sha256(source_path)
                expected_hash = str(raw.get("file_sha256") or "")
                if expected_hash and expected_hash != current_hash:
                    blockers.append("source file hash does not match proposal")
    if file_rel and link_target and not _ambiguous_source_has_target(vault_root, file_rel, link_target):
        blockers.append("source file no longer contains the ambiguous wikilink target")

    if decision == "path_qualify_to_existing_node":
        if not selected_target:
            blockers.append("selected_target is required")
        elif selected_target not in candidates:
            blockers.append("selected_target must match one proposal candidate path")
        else:
            try:
                selected_path = _resolve_within_vault(vault_root, selected_target)
            except ValueError as exc:
                blockers.append(str(exc))
                selected_path = None
            if selected_path is not None:
                if not selected_path.exists():
                    blockers.append("selected_target does not exist")
                else:
                    candidate_hash = str(candidates[selected_target].get("sha256") or "")
                    current_candidate_hash = file_sha256(selected_path)
                    if candidate_hash and candidate_hash != current_candidate_hash:
                        blockers.append("selected_target hash does not match proposal candidate")
            if selected_target:
                writes.append(file_rel)
    elif decision == "create_alias_node":
        if not alias_path:
            blockers.append("alias_path is required")
        elif not alias_path.lower().endswith(".md"):
            blockers.append("alias_path must end with .md")
        else:
            try:
                alias_target = _resolve_within_vault(vault_root, alias_path)
            except ValueError as exc:
                blockers.append(str(exc))
                alias_target = None
            if alias_target is not None and alias_target.exists():
                blockers.append("alias_path already exists")
            writes.extend([file_rel, alias_path])
    elif decision == "rename_or_merge_duplicate_node":
        if not selected_target:
            blockers.append("selected_target is required")
        elif selected_target not in candidates:
            blockers.append("selected_target must match one proposal candidate path")
        if not str(raw.get("reason") or "").strip():
            blockers.append("reason is required for rename_or_merge_duplicate_node")
        if selected_target:
            warnings.append("rename_or_merge_duplicate_node remains manual-review only; no applier exists")
    elif decision == "remove_link":
        if not str(raw.get("reason") or "").strip():
            blockers.append("reason is required for remove_link")
        if file_rel:
            writes.append(file_rel)
    elif decision == "defer":
        warnings.append("defer records review debt only; no graph mutation should occur")

    effect = {
        "path_qualify_to_existing_node": f"path-qualify [[{link_target}]] in {file_rel} to {selected_target}",
        "create_alias_node": f"create alias node {alias_path} and update {file_rel}",
        "rename_or_merge_duplicate_node": f"manual rename/merge review for {selected_target}",
        "remove_link": f"remove [[{link_target}]] from {file_rel}",
        "defer": "defer this ambiguous link decision",
    }.get(decision, "")

    return {
        "file": file_rel,
        "link_target": link_target,
        "decision": decision,
        "approved": bool(raw.get("approved")),
        "operator_approved": operator_approved,
        "execution_ready": not blockers,
        "execution_blockers": blockers,
        "warnings": warnings,
        "current_sha256": current_hash,
        "selected_target": selected_target,
        "alias_path": alias_path,
        "candidate_count": len(candidates),
        "effect": effect,
        "writes": sorted(set(writes)),
        "production_execution_allowed": False,
    }


def validate_ambiguous_link_decisions(
    vault_root: Path,
    decisions_path: Path,
) -> dict[str, Any]:
    """Validate an operator-edited ambiguous-link proposal without executing it."""
    try:
        payload = json.loads(decisions_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "status": "blocked",
            "valid": False,
            "production_execution_allowed": False,
            "errors": [f"could not load ambiguous-link decision file: {exc}"],
            "decision_count": 0,
            "planned_actions": [],
        }

    errors: list[str] = []
    if payload.get("proposal_kind") != "ambiguous_link_target_review":
        errors.append("proposal_kind must be ambiguous_link_target_review")
    decisions = payload.get("decisions")
    if not isinstance(decisions, list):
        errors.append("decision file must contain a decisions list")
        decisions = []
    operator_approved = bool(payload.get("operator_approved"))
    if not operator_approved:
        errors.append("operator_approved must be true")
    if payload.get("proposal_only") is not True:
        errors.append("proposal_only must remain true")

    planned_actions = [
        _validate_ambiguous_decision_row(vault_root, decision, operator_approved)
        for decision in decisions
        if isinstance(decision, dict)
    ]
    malformed_count = sum(1 for decision in decisions if not isinstance(decision, dict))
    if malformed_count:
        errors.append(f"{malformed_count} decision rows are not objects")

    blocked_count = sum(1 for action in planned_actions if not action["execution_ready"])
    warning_count = sum(len(action.get("warnings") or []) for action in planned_actions)
    status = "valid_non_executing" if not errors and not blocked_count else "blocked"
    return {
        "status": status,
        "valid": status == "valid_non_executing",
        "proposal_kind": payload.get("proposal_kind"),
        "operator_approved": operator_approved,
        "approval_preview_only": bool(payload.get("approval_preview_only")),
        "production_execution_allowed": False,
        "source_decision_file": decisions_path.relative_to(vault_root).as_posix()
        if decisions_path.is_relative_to(vault_root)
        else str(decisions_path),
        "decision_count": len(planned_actions),
        "blocked_count": blocked_count,
        "warning_count": warning_count,
        "errors": errors,
        "planned_actions": planned_actions,
    }


def write_ambiguous_approval_preview_copy(
    vault_root: Path,
    decisions_path: Path,
    output_path: str | None = None,
    approved_by: str = "approval-preview",
) -> dict[str, Any]:
    """Write a non-executable approval-preview copy of an ambiguous-link proposal."""
    payload = json.loads(decisions_path.read_text(encoding="utf-8-sig"))
    decisions = payload.get("decisions")
    if not isinstance(decisions, list):
        raise ValueError("decision file must contain a 'decisions' list")
    preview_payload = dict(payload)
    preview_payload["operator_approved"] = True
    preview_payload["approved_by"] = approved_by
    preview_payload["approval_preview_only"] = True
    preview_payload["production_execution_allowed"] = False
    preview_payload["generated_from"] = decisions_path.relative_to(vault_root).as_posix() if decisions_path.is_relative_to(vault_root) else str(decisions_path)
    preview_payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    preview_payload["execution_note"] = (
        "Ambiguous-link approval-preview copy only. This validates the proposed "
        "post-approval shape and is not accepted by any production applier."
    )
    if output_path:
        out_path = Path(output_path)
        if not out_path.is_absolute():
            out_path = vault_root / out_path
    else:
        try:
            rel = decisions_path.relative_to(vault_root)
            out_path = vault_root / rel.with_name(f"{rel.stem}-approval-preview{rel.suffix}")
        except ValueError:
            out_path = decisions_path.with_name(f"{decisions_path.stem}-approval-preview{decisions_path.suffix}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(preview_payload, indent=2), encoding="utf-8")
    try:
        out_rel = out_path.relative_to(vault_root).as_posix()
    except ValueError:
        out_rel = out_path.as_posix()
    _ensure_graph_reports_artifact_index_row(
        vault_root,
        out_rel,
        heading=f"Ambiguous Link Approval Preview - {_local_now().strftime('%Y-%m-%d')}",
        status="Non-executable approval-preview JSON; no production applier exists",
    )
    validation = validate_ambiguous_link_decisions(vault_root, out_path)
    return {
        "approval_preview_path": out_rel,
        "approval_preview_only": True,
        "production_execution_allowed": False,
        "decisions": len(decisions),
        "validation": validation,
    }


def _decision_block(
    result: DecisionApplyResult,
    file_path: str,
    decision: str,
    reason: str,
) -> None:
    result.blocked += 1
    result.messages.append({
        "file": file_path,
        "decision": decision,
        "status": "blocked",
        "reason": reason,
    })


def _decision_skip(
    result: DecisionApplyResult,
    file_path: str,
    decision: str,
    reason: str,
) -> None:
    result.skipped += 1
    result.messages.append({
        "file": file_path,
        "decision": decision,
        "status": "skipped",
        "reason": reason,
    })


def _planned_review_action(
    vault_root: Path,
    raw_decision: dict[str, Any],
    queue_item: dict[str, Any],
    file_rel: str,
    decision: str,
    target_path: Path,
    current_hash: str,
    operator_approved: bool,
) -> dict[str, Any]:
    """Build a human/audit-friendly preview for one validated decision."""
    canonical_rel = _safe_rel_path(
        str(raw_decision.get("canonical_path") or queue_item.get("canonical_path") or "")
    )
    index_rel = _safe_rel_path(
        str(raw_decision.get("index_path") or queue_item.get("keep_or_canonical") or "")
    )
    approved = bool(raw_decision.get("approved"))
    expected_hash = str(raw_decision.get("expected_sha256") or raw_decision.get("file_sha256") or "")
    action: dict[str, Any] = {
        "file": file_rel,
        "decision": decision,
        "issue_category": queue_item.get("issue_category", ""),
        "node_category": queue_item.get("node_category", ""),
        "operator_approved": operator_approved,
        "per_decision_approved": approved,
        "hash_status": "matched" if expected_hash and expected_hash == current_hash else "not_required",
        "current_sha256": current_hash,
        "expected_sha256": expected_hash,
        "effect": _decision_effect(queue_item, decision),
        "reason": str(raw_decision.get("reason") or ""),
        "execution_ready": True,
        "execution_blockers": [],
        "writes": [],
        "moves": [],
        "deletes": [],
        "keeps": [],
    }
    blockers = action["execution_blockers"]
    if decision in DESTRUCTIVE_REVIEW_DECISIONS:
        if not operator_approved:
            blockers.append("operator_approved must be true")
        if not approved:
            blockers.append("per-decision approved must be true")
        if not expected_hash:
            blockers.append("expected_sha256 is required")
    elif decision in {"keep_and_wire", "keep_excluded"} and not operator_approved:
        blockers.append("operator_approved must be true")

    if decision == "keep_and_wire":
        action["keeps"].append(file_rel)
        if index_rel and index_rel not in {"(none)", "(delete review)", "(vault root)"}:
            action["writes"].append(index_rel)
            action["effect"] = f"keep `{file_rel}` and add `[[{target_path.stem}]]` to `{index_rel}`"
        else:
            blockers.append("no usable index/anchor path")
    elif decision in {"keep_excluded", "manual_investigation"}:
        action["keeps"].append(file_rel)
        action["writes"].append(DECISION_REGISTRY_REL)
    elif decision == "archive_noncanonical_artifact":
        archive_base = f"{NONCANONICAL_ARTIFACT_ARCHIVE_REL}/{_local_now().strftime('%Y-%m-%d')}"
        archive_rel = f"{archive_base}/{file_rel}"
        try:
            archive_path = _unique_destination(_resolve_within_vault(vault_root, archive_rel))
            action["moves"].append({
                "from": file_rel,
                "to": archive_path.relative_to(vault_root).as_posix(),
            })
        except ValueError as exc:
            blockers.append(str(exc))
        action["writes"].append(DECISION_REGISTRY_REL)
        action["writes"].append(NONCANONICAL_ARTIFACT_INDEX_REL)
    elif decision in {"archive_after_review", "replace_with_canonical"}:
        if decision == "replace_with_canonical":
            if canonical_rel:
                action["canonical_path"] = canonical_rel
                action["keeps"].append(canonical_rel)
                archive_base = f"{ARCHIVE_REVIEW_REL}/Replaced-Duplicates/{_local_now().strftime('%Y-%m-%d')}"
            else:
                blockers.append("missing canonical path")
                archive_base = f"{ARCHIVE_REVIEW_REL}/Replaced-Duplicates/{_local_now().strftime('%Y-%m-%d')}"
        else:
            archive_base = f"{ARCHIVE_REVIEW_REL}/Archived/{_local_now().strftime('%Y-%m-%d')}"
        archive_rel = f"{archive_base}/{file_rel}"
        try:
            archive_path = _unique_destination(_resolve_within_vault(vault_root, archive_rel))
            action["moves"].append({
                "from": file_rel,
                "to": archive_path.relative_to(vault_root).as_posix(),
            })
        except ValueError as exc:
            blockers.append(str(exc))
        action["writes"].append(DECISION_REGISTRY_REL)
    elif decision == "delete_after_review":
        action["deletes"].append(file_rel)
        action["writes"].append(DECISION_REGISTRY_REL)

    action["execution_ready"] = not blockers
    return action


def render_decision_apply_result(result: DecisionApplyResult, max_actions: int = 40) -> str:
    """Render validation/application result as an operator-facing execution plan."""
    mode = "EXECUTE" if result.executed else "VALIDATE ONLY"
    lines = [
        "ChaseOS Loose-Node Decision Plan",
        "",
        f"Mode: {mode}",
        f"Status: {result.status}",
        f"Approval preview only: {str(result.approval_preview_only).lower()}",
        f"Decisions: {result.decisions_total}",
        f"Validated/applied count: {result.applied}",
        f"Blocked: {result.blocked}",
        f"Skipped: {result.skipped}",
    ]
    if result.files_moved:
        lines.append(f"Files moved: {len(result.files_moved)}")
    if result.files_deleted:
        lines.append(f"Files deleted: {len(result.files_deleted)}")
    if result.files_written:
        lines.append(f"Files written: {len(result.files_written)}")
    lines.extend(["", f"Planned actions (first {max_actions}):"])
    for action in result.planned_actions[:max_actions]:
        lines.append(f"- {action.get('file')} [{action.get('issue_category')} / {action.get('node_category')}]")
        lines.append(f"  decision: {action.get('decision')}")
        lines.append(f"  execution_ready: {str(action.get('execution_ready')).lower()}")
        if action.get("execution_blockers"):
            lines.append(f"  blockers: {'; '.join(str(b) for b in action.get('execution_blockers') or [])}")
        if action.get("canonical_path"):
            lines.append(f"  canonical kept: {action.get('canonical_path')}")
        for move in action.get("moves") or []:
            lines.append(f"  move: {move.get('from')} -> {move.get('to')}")
        for delete_rel in action.get("deletes") or []:
            lines.append(f"  delete: {delete_rel}")
        for write_rel in action.get("writes") or []:
            lines.append(f"  write: {write_rel}")
        for keep_rel in action.get("keeps") or []:
            lines.append(f"  keep: {keep_rel}")
        lines.append(f"  hash: {action.get('hash_status')}")
        if action.get("effect"):
            lines.append(f"  effect: {action.get('effect')}")
    if result.messages:
        lines.extend(["", "Messages:"])
        for message in result.messages:
            reason = f" - {message.get('reason')}" if message.get("reason") else ""
            lines.append(
                f"- {message.get('status')}: {message.get('file')} [{message.get('decision')}]{reason}"
            )
    return "\n".join(lines)


def apply_review_decisions(
    vault_root: Path,
    decisions_path: Path,
    execute: bool = False,
) -> DecisionApplyResult:
    """Validate or apply explicit operator loose-node review decisions."""
    result = DecisionApplyResult(status="dry_run", executed=execute)
    try:
        decisions_data = json.loads(decisions_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        _decision_block(result, str(decisions_path), "(load)", f"could not load decision file: {exc}")
        result.status = "blocked"
        return result

    decisions = decisions_data.get("decisions")
    if not isinstance(decisions, list):
        _decision_block(result, str(decisions_path), "(schema)", "decision file must contain a 'decisions' list")
        result.status = "blocked"
        return result

    operator_approved = bool(decisions_data.get("operator_approved"))
    approved_by = str(decisions_data.get("approved_by") or "")
    result.approval_preview_only = bool(decisions_data.get("approval_preview_only"))
    result.decisions_total = len(decisions)
    if execute and result.approval_preview_only:
        _decision_block(
            result,
            str(decisions_path),
            "(approval_preview_only)",
            "approval-preview decision copy cannot be executed",
        )
        result.status = "blocked"
        return result
    report = scan_vault(vault_root)
    queue_by_file = {
        item["file"]: item
        for item in build_loose_node_review_queue(report, vault_root)
    }
    registry = load_decision_registry(vault_root)
    registry_decisions = registry.setdefault("decisions", {})

    validated: list[dict[str, Any]] = []
    for raw_decision in decisions:
        if not isinstance(raw_decision, dict):
            _decision_block(result, "(unknown)", "(schema)", "decision entry must be an object")
            continue
        file_rel = _safe_rel_path(str(raw_decision.get("file", "")))
        decision = str(raw_decision.get("decision", ""))
        if not file_rel:
            _decision_block(result, file_rel, decision, "missing file")
            continue
        if decision not in ALLOWED_REVIEW_DECISIONS:
            _decision_block(result, file_rel, decision, "unsupported decision")
            continue
        if file_rel in PROTECTED_DESTRUCTIVE_PATHS and decision in DESTRUCTIVE_REVIEW_DECISIONS:
            _decision_block(result, file_rel, decision, "protected canonical path cannot be handled destructively")
            continue
        item = queue_by_file.get(file_rel)
        if item is None:
            _decision_skip(result, file_rel, decision, "file is not in the current loose-node review queue")
            continue
        try:
            target_path = _resolve_within_vault(vault_root, file_rel)
        except ValueError as exc:
            _decision_block(result, file_rel, decision, str(exc))
            continue
        if not target_path.exists():
            _decision_skip(result, file_rel, decision, "file no longer exists")
            continue
        current_hash = file_sha256(target_path)
        expected_hash = str(raw_decision.get("expected_sha256") or raw_decision.get("file_sha256") or "")
        if expected_hash and current_hash != expected_hash:
            _decision_block(result, file_rel, decision, "file hash does not match decision file")
            continue
        if decision in DESTRUCTIVE_REVIEW_DECISIONS and not expected_hash:
            _decision_block(result, file_rel, decision, "destructive decisions require expected_sha256")
            continue
        if execute and decision in DESTRUCTIVE_REVIEW_DECISIONS:
            if not operator_approved or not bool(raw_decision.get("approved")):
                _decision_block(result, file_rel, decision, "destructive execution requires operator_approved=true and per-decision approved=true")
                continue
        if execute and decision in {"keep_and_wire", "keep_excluded"}:
            if not operator_approved:
                _decision_block(result, file_rel, decision, "execution requires operator_approved=true")
                continue
        validated.append({
            "raw": raw_decision,
            "item": item,
            "file_rel": file_rel,
            "decision": decision,
            "target_path": target_path,
            "current_hash": current_hash,
        })
        result.planned_actions.append(_planned_review_action(
            vault_root,
            raw_decision,
            item,
            file_rel,
            decision,
            target_path,
            current_hash,
            operator_approved,
        ))

    if result.blocked:
        result.status = "blocked"
        return result
    if not execute:
        result.status = "dry_run_valid"
        result.applied = len(validated)
        for item in validated:
            result.messages.append({
                "file": item["file_rel"],
                "decision": item["decision"],
                "status": "would_apply",
            })
        return result

    for item in validated:
        raw_decision = item["raw"]
        file_rel = item["file_rel"]
        decision = item["decision"]
        target_path = item["target_path"]
        current_hash = item["current_hash"]
        queue_item = item["item"]
        reason = str(raw_decision.get("reason") or "")
        registry_entry = {
            "decision": decision,
            "file_sha256": current_hash,
            "approved_by": approved_by,
            "reason": reason,
            "applied_at": datetime.now(timezone.utc).isoformat(),
            "source_decision_file": str(decisions_path),
        }

        if decision == "keep_and_wire":
            index_rel = _safe_rel_path(str(raw_decision.get("index_path") or queue_item.get("keep_or_canonical") or ""))
            if not index_rel or index_rel in {"(none)", "(delete review)", "(vault root)"}:
                _decision_skip(result, file_rel, decision, "no usable index/anchor path")
                continue
            try:
                index_path = _resolve_within_vault(vault_root, index_rel)
            except ValueError as exc:
                _decision_skip(result, file_rel, decision, str(exc))
                continue
            if not index_path.exists():
                _decision_skip(result, file_rel, decision, "index/anchor path does not exist")
                continue
            changed = _append_wikilink_if_missing(index_path, target_path.stem)
            if changed:
                result.files_written.append(index_rel)
            registry_entry["index_path"] = index_rel
            registry_decisions[file_rel] = registry_entry

        elif decision in {"keep_excluded", "manual_investigation"}:
            registry_decisions[file_rel] = registry_entry

        elif decision == "archive_noncanonical_artifact":
            archive_base = f"{NONCANONICAL_ARTIFACT_ARCHIVE_REL}/{_local_now().strftime('%Y-%m-%d')}"
            archive_rel = f"{archive_base}/{file_rel}"
            archive_path = _unique_destination(_resolve_within_vault(vault_root, archive_rel))
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(target_path), str(archive_path))
            moved_rel = archive_path.relative_to(vault_root).as_posix()
            result.files_moved.append({"from": file_rel, "to": moved_rel})
            registry_entry["archive_path"] = moved_rel
            registry_entry["artifact_index_path"] = NONCANONICAL_ARTIFACT_INDEX_REL
            registry_entry["issue_category"] = str(queue_item.get("issue_category") or "")
            registry_entry["node_category"] = str(queue_item.get("node_category") or "")
            registry_decisions[file_rel] = registry_entry
            if _append_noncanonical_artifact_index(vault_root, file_rel, moved_rel, queue_item, reason):
                _append_unique(result.files_written, NONCANONICAL_ARTIFACT_INDEX_REL)

        elif decision in {"archive_after_review", "replace_with_canonical"}:
            if decision == "replace_with_canonical":
                canonical_rel = _safe_rel_path(str(raw_decision.get("canonical_path") or queue_item.get("canonical_path") or ""))
                if not canonical_rel:
                    _decision_skip(result, file_rel, decision, "missing canonical path")
                    continue
                try:
                    canonical_path = _resolve_within_vault(vault_root, canonical_rel)
                except ValueError as exc:
                    _decision_skip(result, file_rel, decision, str(exc))
                    continue
                if not canonical_path.exists():
                    _decision_skip(result, file_rel, decision, "canonical path does not exist")
                    continue
                registry_entry["canonical_path"] = canonical_rel
                archive_base = f"{ARCHIVE_REVIEW_REL}/Replaced-Duplicates/{_local_now().strftime('%Y-%m-%d')}"
            else:
                archive_base = f"{ARCHIVE_REVIEW_REL}/Archived/{_local_now().strftime('%Y-%m-%d')}"
            archive_rel = f"{archive_base}/{file_rel}"
            archive_path = _unique_destination(_resolve_within_vault(vault_root, archive_rel))
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(target_path), str(archive_path))
            moved_rel = archive_path.relative_to(vault_root).as_posix()
            result.files_moved.append({"from": file_rel, "to": moved_rel})
            registry_entry["archive_path"] = moved_rel
            registry_decisions[file_rel] = registry_entry

        elif decision == "delete_after_review":
            target_path.unlink()
            result.files_deleted.append(file_rel)
            registry_decisions[file_rel] = registry_entry

        result.applied += 1
        result.messages.append({
            "file": file_rel,
            "decision": decision,
            "status": "applied",
        })

    result.registry_path = _write_decision_registry(vault_root, registry)
    _append_unique(result.files_written, result.registry_path)
    result.status = "applied"
    _write_decision_log(vault_root, result)
    return result


def write_approval_preview_copy(
    vault_root: Path,
    decisions_path: Path,
    output_path: str | None = None,
    approved_by: str = "approval-preview",
) -> dict[str, Any]:
    """Write a non-executable approval-preview copy of a decision proposal."""
    payload = json.loads(decisions_path.read_text(encoding="utf-8-sig"))
    decisions = payload.get("decisions")
    if not isinstance(decisions, list):
        raise ValueError("decision file must contain a 'decisions' list")
    preview_payload = dict(payload)
    preview_payload["operator_approved"] = True
    preview_payload["approved_by"] = approved_by
    preview_payload["approval_preview_only"] = True
    preview_payload["production_execution_allowed"] = False
    preview_payload["generated_from"] = decisions_path.relative_to(vault_root).as_posix() if decisions_path.is_relative_to(vault_root) else str(decisions_path)
    preview_payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    preview_payload["execution_note"] = (
        "Approval-preview copy only. This demonstrates the post-approval plan shape "
        "and is blocked from --execute-review-decisions."
    )
    preview_decisions: list[dict[str, Any]] = []
    for decision in decisions:
        if not isinstance(decision, dict):
            continue
        preview_decision = dict(decision)
        if preview_decision.get("decision") in DESTRUCTIVE_REVIEW_DECISIONS:
            preview_decision["approved"] = True
        preview_decisions.append(preview_decision)
    preview_payload["decisions"] = preview_decisions
    if output_path:
        out_path = Path(output_path)
        if not out_path.is_absolute():
            out_path = vault_root / out_path
    else:
        try:
            rel = decisions_path.relative_to(vault_root)
            out_path = vault_root / rel.with_name(f"{rel.stem}-approval-preview{rel.suffix}")
        except ValueError:
            out_path = decisions_path.with_name(f"{decisions_path.stem}-approval-preview{decisions_path.suffix}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(preview_payload, indent=2), encoding="utf-8")
    try:
        out_rel = out_path.relative_to(vault_root).as_posix()
    except ValueError:
        out_rel = out_path.as_posix()
    _ensure_graph_reports_artifact_index_row(
        vault_root,
        out_rel,
        heading=f"Loose Node Decision Approval Preview - {_local_now().strftime('%Y-%m-%d')}",
        status="Non-executable approval-preview JSON; blocked from --execute-review-decisions",
    )
    return {
        "approval_preview_path": out_rel,
        "approval_preview_only": True,
        "production_execution_allowed": False,
        "decisions": len(preview_decisions),
    }


def render_json_report(report: HygieneReport) -> str:
    """Render the report as machine-readable JSON."""
    review_queue = build_loose_node_review_queue(report)
    return json.dumps(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "files_scanned": report.files_scanned,
            "total_issues": len(report.issues),
            "category_counts": summarize_issues(report),
            "node_category_counts": summarize_node_categories(report),
            "review_queue_category_counts": summarize_review_queue_categories(review_queue),
            "loose_node_review_count": len(review_queue),
            "loose_node_review_queue": review_queue,
            "review_artifacts": report.review_artifacts,
            "strict_gate_failed": report.strict_gate_failed,
            "strict_gate_review_count": report.strict_gate_review_count,
            "strict_visible_graph_failed": report.strict_visible_graph_failed,
            "strict_visible_graph_count": report.strict_visible_graph_count,
            "visible_graph_audit": report.visible_graph_audit,
            "wikilinks_fixed": report.wikilinks_fixed,
            "nodes_wired": report.nodes_wired,
            "indexes_created": report.indexes_created,
            "junk_flagged": report.junk_flagged,
            "junk_deleted": report.junk_deleted,
            "issues": [
                {
                    "category": i.category,
                    "severity": i.severity,
                    "file": i.file_path,
                    "index": i.index_path,
                    "node_category": i.node_category or infer_node_category(i.file_path),
                    "canonical_path": i.canonical_path,
                    "description": i.description,
                    "action": i.action,
                    "evidence": i.evidence,
                    "fixed": i.fixed,
                }
                for i in report.issues
            ],
        },
        indent=2,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _print_orphan_summary(report: HygieneReport, fix: bool) -> None:
    """Print a structured, categorized terminal summary of all orphans found and fixed."""
    DIVIDER = "=" * 72
    mode = "[FIX]" if fix else "[DRY-RUN]"

    # Bucket issues by semantic category
    loose_nodes      = [i for i in report.issues if i.category == "loose_node"]
    backtick_links   = [i for i in report.issues if i.category == "backtick_wikilink"]
    missing_indexes  = [i for i in report.issues if i.category == "missing_index"]
    # graph orphans by domain bucket
    go_07logs        = [i for i in report.issues if i.category == "graph_orphan" and i.file_path.startswith("07_LOGS/")]
    go_03inputs      = [i for i in report.issues if i.category == "graph_orphan" and i.file_path.startswith("03_INPUTS/")]
    go_docs          = [i for i in report.issues if i.category == "graph_orphan" and i.file_path.startswith("docs/")]
    go_99archive     = [i for i in report.issues if i.category == "graph_orphan" and i.file_path.startswith("99_ARCHIVE/")]
    go_02knowledge   = [i for i in report.issues if i.category == "graph_orphan" and i.file_path.startswith("02_KNOWLEDGE/")]
    go_runtime       = [i for i in report.issues if i.category == "graph_orphan" and i.file_path.startswith("runtime/")]
    go_agents        = [i for i in report.issues if i.category == "graph_orphan" and i.file_path.startswith("06_AGENTS/")]
    classified_loose = [i for i in report.issues if i.category in REVIEW_QUEUE_CATEGORIES]
    go_other         = [i for i in report.issues if i.category == "graph_orphan"
                        and not any(i.file_path.startswith(p) for p in
                                    ("07_LOGS/","03_INPUTS/","docs/","99_ARCHIVE/","02_KNOWLEDGE/","runtime/","06_AGENTS/"))]
    manual_review    = [i for i in report.issues if i.severity == "review" and not i.fixed]
    junk_issues      = [i for i in report.issues if i.severity == "junk"]

    def _tally(items: list) -> str:
        if not fix:
            return f"{len(items)} found"
        fixed = sum(1 for i in items if i.fixed)
        return f"{len(items)} found  |  {fixed} fixed  |  {len(items)-fixed} remain"

    print()
    print(DIVIDER)
    print(f"  ChaseOS Vault Hygiene Report  {mode}")
    print(f"  Scanned {report.files_scanned} files  |  {len(report.issues)} total issues")
    print(DIVIDER)
    print()

    print("  STRUCTURAL (index wiring)")
    print(f"    Missing indexes       : {_tally(missing_indexes)}")
    print(f"    Loose nodes (unwired) : {_tally(loose_nodes)}")
    print(f"    Backtick wikilinks    : {_tally(backtick_links)}")
    print()

    print("  GRAPH ORPHANS by domain")
    buckets = [
        ("07_LOGS",       go_07logs),
        ("03_INPUTS",     go_03inputs),
        ("docs/changes",  go_docs),
        ("99_ARCHIVE",    go_99archive),
        ("02_KNOWLEDGE",  go_02knowledge),
        ("runtime",       go_runtime),
        ("06_AGENTS",     go_agents),
        ("other",         go_other),
    ]
    for label, bucket in buckets:
        if bucket:
            print(f"    {label:<22}: {_tally(bucket)}")
    print()

    if classified_loose:
        print("  CLASSIFIED LOOSE NODES (content/path review)")
        by_category: dict[str, list[Issue]] = {}
        for item in classified_loose:
            by_category.setdefault(item.category, []).append(item)
        for label, bucket in sorted(by_category.items()):
            print(f"    {label:<26}: {len(bucket)} found")
        print("    These are not auto-wired; review action/evidence in the report.")
        print()

    if manual_review:
        print("  MANUAL REVIEW REQUIRED (cannot be auto-wired)")
        for item in manual_review[:30]:
            anchor_hint = f"  -> suggest: {item.index_path}" if item.index_path != "(none)" else ""
            print(f"    - {item.file_path}{anchor_hint}")
        if len(manual_review) > 30:
            print(f"    ... and {len(manual_review)-30} more (see report file)")
        print()

    if junk_issues:
        print(f"  JUNK FILES : {len(junk_issues)} flagged")
        for j in junk_issues:
            status = "[DELETED]" if j.fixed else "[FLAGGED]"
            print(f"    {status} {j.file_path}")
        print()

    print("  TALLY")
    if fix:
        print(f"    Indexes created : {report.indexes_created}")
        print(f"    Nodes wired     : {report.nodes_wired}")
        print(f"    Wikilinks fixed : {report.wikilinks_fixed}")
        print(f"    Files modified  : {report.files_fixed}")
        remain = sum(1 for i in report.issues if not i.fixed)
        print(f"    Remaining open  : {remain}")
    else:
        auto_fixable = sum(1 for i in report.issues if i.severity == "auto_fix")
        print(f"    Auto-fixable    : {auto_fixable}")
        print(f"    Manual review   : {len(manual_review)}")
        print(f"    Run --fix to apply all auto-fixes.")
    print(DIVIDER)
    print()


def run(
    fix: bool = False,
    delete_junk: bool = False,
    json_output: bool = False,
    report_path: str | None = None,
    write_report: bool | None = None,
    write_review_queue: bool = False,
    strict_review_gate: bool = False,
    strict_visible_graph: bool = False,
    fix_semantic_hub_gaps: bool = False,
    semantic_hub_gap_limit: int = 50,
    fix_ambiguous_links: bool = False,
    ambiguous_link_limit: int = 50,
    review_ambiguous_links: bool = False,
    ambiguous_review_limit: int = 50,
    review_unresolved_links: bool = False,
    unresolved_link_limit: int = 50,
    vault_root: Path | None = None,
    audit: bool = True,
):
    """Main entry point for vault hygiene scan+fix. Returns HygieneReport."""
    root = Path(vault_root).resolve() if vault_root is not None else VAULT_ROOT
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    if write_report is None:
        write_report = not json_output

    if not json_output:
        print(f"[SCAN] Scanning vault: {root}")
        print()

    if audit:
        _mcp_audit(
            surface_id="vault_hygiene.scan",
            outcome="success",
            files_read=[],
            files_written=[],
            detail="Vault hygiene scan initiated",
        )

    report = scan_vault(
        root,
        semantic_hub_fix_limit=max(0, semantic_hub_gap_limit) if fix_semantic_hub_gaps else 0,
        ambiguous_link_fix_limit=max(0, ambiguous_link_limit) if fix_ambiguous_links else 0,
        ambiguous_link_review_limit=max(0, ambiguous_review_limit) if review_ambiguous_links else 0,
        unresolved_link_review_limit=max(0, unresolved_link_limit) if review_unresolved_links else 0,
    )

    if not json_output:
        print(f"[DONE] {report.files_scanned} files scanned  |  {len(report.issues)} issues found")
        print()

    if fix:
        if not json_output:
            print("[FIX] Applying fixes...")
        apply_fixes(root, report, delete_junk=delete_junk)
        if not json_output:
            print(f"   [OK] Indexes created : {report.indexes_created}")
            print(f"   [OK] Nodes wired     : {report.nodes_wired}")
            print(f"   [OK] Wikilinks fixed : {report.wikilinks_fixed}")
            if delete_junk:
                print(f"   [DEL] Junk deleted  : {report.junk_deleted}")
            print()

    review_queue = build_loose_node_review_queue(report, root)
    report.strict_gate_review_count = len(review_queue)
    report.strict_gate_failed = bool(strict_review_gate and review_queue)
    report.strict_visible_graph_count = visible_graph_debt_count(report)
    report.strict_visible_graph_failed = bool(strict_visible_graph and report.strict_visible_graph_count)

    if write_review_queue:
        artifacts = write_loose_node_review_artifacts(report, root)
        handover_path = generate_consolidated_handover(report, root)
        try:
            artifacts["handover"] = handover_path.relative_to(root).as_posix()
        except ValueError:
            artifacts["handover"] = handover_path.as_posix()
            
        if not json_output:
            print("[REVIEW] Loose-node review artifacts:")
            for kind, path in artifacts.items():
                print(f"   {kind}: {path}")
            print()

    # Write the full report to Graph-Reports unless machine-readable/no-report mode is requested.
    if write_report:
        full_report = render_report(report, root)
        if report_path:
            r_file = Path(report_path)
            if not r_file.is_absolute():
                r_file = root / r_file
            r_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            graph_dir = root / "07_LOGS" / "Graph-Reports"
            graph_dir.mkdir(parents=True, exist_ok=True)
            dt = _local_now().strftime("%Y-%m-%d")
            suffix = "" if fix else "-dry-run"
            r_file = graph_dir / f"{dt}-graph-hygiene-report{suffix}.md"
        r_file.write_text(full_report, encoding="utf-8")
        if not json_output:
            try:
                display_path = r_file.relative_to(root)
            except ValueError:
                display_path = r_file
            print(f"[REPORT] Full report -> {display_path}")

    if not json_output:
        # Print the structured summary to terminal (not the full wall of text)
        _print_orphan_summary(report, fix)
        if report.strict_gate_failed:
            print(f"[STRICT-GATE] BLOCKED: {report.strict_gate_review_count} review-gated loose nodes remain.")
        if report.strict_visible_graph_failed:
            print(f"[STRICT-VISIBLE-GRAPH] BLOCKED: {report.strict_visible_graph_count} graph-visible debt items remain.")
    else:
        print(render_json_report(report))

    return report


def main() -> None:
    import argparse

    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="ChaseOS Vault Hygiene — scan and fix loose nodes, backtick wikilinks, orphans, and junk.",
    )
    parser.add_argument("--fix", action="store_true", help="Apply auto-fixes")
    parser.add_argument("--dry-run", dest="fix", action="store_false",
                        help="Report only, no writes (default)")
    parser.set_defaults(fix=False)
    parser.add_argument("--delete-junk", action="store_true", help="Delete confirmed junk files")
    parser.add_argument("--json", action="store_true", help="Output report as JSON")
    parser.add_argument(
        "--review-loose-nodes",
        "--loose-node-review",
        action="store_true",
        dest="review_loose_nodes",
        help="Emit JSON review queue for duplicate, misplaced, runtime, and placeholder loose nodes",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Do not write a markdown report to 07_LOGS/Graph-Reports",
    )
    parser.add_argument(
        "--write-review-queue",
        action="store_true",
        help="Write JSON and markdown loose-node review queue artifacts under 07_LOGS/Graph-Reports",
    )
    parser.add_argument(
        "--strict-review-gate",
        action="store_true",
        help="Exit with code 2 when review-gated loose nodes remain",
    )
    parser.add_argument(
        "--strict-visible-graph",
        action="store_true",
        help="Exit with code 2 when graph-visible debt remains: raw zero-degree files, unresolved links, ambiguous targets, connected duplicate stems, or semantic hub gaps",
    )
    parser.add_argument(
        "--fix-semantic-hub-gaps",
        action="store_true",
        help="With --fix, append governance hub links to a bounded batch of major agent/runtime docs",
    )
    parser.add_argument(
        "--semantic-hub-gap-limit",
        type=int,
        default=50,
        help="Maximum number of semantic hub gaps to repair in one --fix pass",
    )
    parser.add_argument(
        "--fix-ambiguous-links",
        action="store_true",
        help="With --fix, path-qualify a bounded batch of ambiguous wikilinks when a known canonical target exists",
    )
    parser.add_argument(
        "--ambiguous-link-limit",
        type=int,
        default=50,
        help="Maximum number of safe ambiguous wikilinks to path-qualify in one --fix pass",
    )
    parser.add_argument(
        "--review-ambiguous-links",
        action="store_true",
        help="Include a bounded batch of ambiguous wikilinks with no safe canonical target as review issues",
    )
    parser.add_argument(
        "--ambiguous-review-limit",
        type=int,
        default=50,
        help="Maximum number of unsafe ambiguous wikilink targets to surface in one review pass",
    )
    parser.add_argument(
        "--review-unresolved-links",
        action="store_true",
        help="Include a bounded batch of unresolved wikilink targets as review issues",
    )
    parser.add_argument(
        "--unresolved-link-limit",
        type=int,
        default=50,
        help="Maximum number of unresolved wikilink targets to surface in one review pass",
    )
    parser.add_argument(
        "--review-summary",
        action="store_true",
        help="Print a compact non-mutating operator preview of loose-node categories, decisions, and target effects",
    )
    parser.add_argument(
        "--review-summary-limit",
        type=int,
        default=20,
        help="Maximum number of review items to show in --review-summary",
    )
    parser.add_argument(
        "--apply-review-decisions",
        type=str,
        default=None,
        metavar="PATH",
        help="Validate or apply an explicit loose-node decision JSON file",
    )
    parser.add_argument(
        "--execute-review-decisions",
        action="store_true",
        help="Execute approved review decisions; without this flag, decisions are validated only",
    )
    parser.add_argument(
        "--write-approval-preview-copy",
        type=str,
        default=None,
        metavar="PATH",
        help="Write a non-executable approval-preview copy of a decision/proposal JSON",
    )
    parser.add_argument(
        "--approval-preview-output",
        type=str,
        default=None,
        help="Output path for --write-approval-preview-copy",
    )
    parser.add_argument(
        "--propose-review-decisions",
        action="store_true",
        help="Write a small unapproved decision proposal JSON from the current loose-node review queue",
    )
    parser.add_argument(
        "--proposal-path",
        type=str,
        default=None,
        help="Output path for --propose-review-decisions",
    )
    parser.add_argument(
        "--proposal-max-items",
        type=int,
        default=20,
        help="Maximum number of decisions to include in a proposal",
    )
    parser.add_argument(
        "--proposal-categories",
        type=str,
        default=",".join(DEFAULT_PROPOSAL_CATEGORIES),
        help="Comma-separated issue categories to include in a proposal",
    )
    parser.add_argument(
        "--proposal-include-pending-conflicts",
        action="store_true",
        help="Include files already staged in older unapproved proposals when the current recommended decision differs; records supersedes metadata",
    )
    parser.add_argument(
        "--proposal-include-pending-same-decision",
        action="store_true",
        help="Include files already staged in older unapproved proposals when the current recommended decision matches; records consolidation metadata",
    )
    parser.add_argument(
        "--propose-unresolved-link-decisions",
        action="store_true",
        help="Write an unapproved proposal JSON/markdown for unresolved wikilink target decisions",
    )
    parser.add_argument(
        "--unresolved-proposal-path",
        type=str,
        default=None,
        help="Output path for --propose-unresolved-link-decisions",
    )
    parser.add_argument(
        "--unresolved-proposal-max-items",
        type=int,
        default=50,
        help="Maximum unresolved wikilink targets to include in an unresolved-link proposal",
    )
    parser.add_argument(
        "--unresolved-proposal-include-pending",
        action="store_true",
        help="Allow unresolved-link proposal rows already staged in older unapproved unresolved-link proposals",
    )
    parser.add_argument(
        "--validate-unresolved-link-decisions",
        type=str,
        default=None,
        metavar="PATH",
        help="Validate an operator-edited unresolved-link decision JSON without mutating vault links",
    )
    parser.add_argument(
        "--write-unresolved-approval-preview-copy",
        type=str,
        default=None,
        metavar="PATH",
        help="Write a non-executable approval-preview copy of an unresolved-link decision JSON",
    )
    parser.add_argument(
        "--unresolved-approval-preview-output",
        type=str,
        default=None,
        help="Output path for --write-unresolved-approval-preview-copy",
    )
    parser.add_argument(
        "--propose-ambiguous-link-decisions",
        action="store_true",
        help="Write an unapproved proposal JSON/markdown for ambiguous duplicate-stem wikilink decisions",
    )
    parser.add_argument(
        "--ambiguous-proposal-path",
        type=str,
        default=None,
        help="Output path for --propose-ambiguous-link-decisions",
    )
    parser.add_argument(
        "--ambiguous-proposal-max-items",
        type=int,
        default=50,
        help="Maximum ambiguous wikilink rows to include in an ambiguous-link proposal",
    )
    parser.add_argument(
        "--ambiguous-proposal-include-pending",
        action="store_true",
        help="Allow ambiguous-link proposal rows already staged in older unapproved ambiguous-link proposals",
    )
    parser.add_argument(
        "--validate-ambiguous-link-decisions",
        type=str,
        default=None,
        metavar="PATH",
        help="Validate an operator-edited ambiguous-link decision JSON without mutating vault links",
    )
    parser.add_argument(
        "--write-ambiguous-approval-preview-copy",
        type=str,
        default=None,
        metavar="PATH",
        help="Write a non-executable approval-preview copy of an ambiguous-link decision JSON",
    )
    parser.add_argument(
        "--ambiguous-approval-preview-output",
        type=str,
        default=None,
        help="Output path for --write-ambiguous-approval-preview-copy",
    )
    parser.add_argument("--report-path", type=str, default=None,
                        help="Override report output path")
    args = parser.parse_args()

    if args.review_summary:
        report = scan_vault(VAULT_ROOT)
        summary = build_review_summary(report, VAULT_ROOT, max_items=max(0, args.review_summary_limit))
        if args.json or args.review_loose_nodes:
            print(json.dumps(summary, indent=2))
        else:
            print(render_review_summary(summary))
        return

    if args.propose_review_decisions:
        report = scan_vault(VAULT_ROOT)
        proposal = propose_review_decisions(
            report,
            VAULT_ROOT,
            output_path=args.proposal_path,
            max_items=max(0, args.proposal_max_items),
            categories=[c.strip() for c in args.proposal_categories.split(",") if c.strip()],
            include_pending_conflicts=args.proposal_include_pending_conflicts,
            include_pending_same_decision=args.proposal_include_pending_same_decision,
        )
        if args.json or args.review_loose_nodes:
            print(json.dumps(proposal, indent=2))
        else:
            print(f"[PROPOSAL] {proposal['proposal_count']} decisions -> {proposal['proposal_path']}")
        return

    if args.propose_unresolved_link_decisions:
        max_items = max(0, args.unresolved_proposal_max_items)
        pending_count = 0
        if not args.unresolved_proposal_include_pending:
            pending_count = len(_pending_unresolved_link_proposal_keys(
                VAULT_ROOT,
                exclude_rel=args.unresolved_proposal_path,
            ))
        report = scan_vault(VAULT_ROOT, unresolved_link_review_limit=max_items + pending_count)
        proposal = propose_unresolved_link_decisions(
            report,
            VAULT_ROOT,
            output_path=args.unresolved_proposal_path,
            max_items=max_items,
            include_pending=args.unresolved_proposal_include_pending,
        )
        if args.json or args.review_loose_nodes:
            print(json.dumps(proposal, indent=2))
        else:
            print(f"[UNRESOLVED-PROPOSAL] {proposal['proposal_count']} decisions -> {proposal['proposal_path']}")
        return

    if args.validate_unresolved_link_decisions:
        decision_path = Path(args.validate_unresolved_link_decisions)
        if not decision_path.is_absolute():
            decision_path = VAULT_ROOT / decision_path
        validation = validate_unresolved_link_decisions(VAULT_ROOT, decision_path)
        if args.json or args.review_loose_nodes:
            print(json.dumps(validation, indent=2))
        else:
            print(
                "[UNRESOLVED-VALIDATION] "
                f"{validation['status']} "
                f"({validation['blocked_count']} blocked / {validation['decision_count']} decisions)"
            )
        if validation["status"] == "blocked":
            raise SystemExit(2)
        return

    if args.write_unresolved_approval_preview_copy:
        decision_path = Path(args.write_unresolved_approval_preview_copy)
        if not decision_path.is_absolute():
            decision_path = VAULT_ROOT / decision_path
        preview = write_unresolved_approval_preview_copy(
            VAULT_ROOT,
            decision_path,
            output_path=args.unresolved_approval_preview_output,
        )
        if args.json or args.review_loose_nodes:
            print(json.dumps(preview, indent=2))
        else:
            print(
                "[UNRESOLVED-APPROVAL-PREVIEW] "
                f"{preview['decisions']} decisions -> {preview['approval_preview_path']} "
                "(non-executable)"
            )
        if preview["validation"]["status"] == "blocked":
            raise SystemExit(2)
        return

    if args.propose_ambiguous_link_decisions:
        max_items = max(0, args.ambiguous_proposal_max_items)
        pending_count = 0
        if not args.ambiguous_proposal_include_pending:
            pending_count = len(_pending_ambiguous_link_proposal_keys(
                VAULT_ROOT,
                exclude_rel=args.ambiguous_proposal_path,
            ))
        report = scan_vault(VAULT_ROOT, ambiguous_link_review_limit=max_items + pending_count)
        proposal = propose_ambiguous_link_decisions(
            report,
            VAULT_ROOT,
            output_path=args.ambiguous_proposal_path,
            max_items=max_items,
            include_pending=args.ambiguous_proposal_include_pending,
        )
        if args.json or args.review_loose_nodes:
            print(json.dumps(proposal, indent=2))
        else:
            print(f"[AMBIGUOUS-PROPOSAL] {proposal['proposal_count']} decisions -> {proposal['proposal_path']}")
        return

    if args.validate_ambiguous_link_decisions:
        decision_path = Path(args.validate_ambiguous_link_decisions)
        if not decision_path.is_absolute():
            decision_path = VAULT_ROOT / decision_path
        validation = validate_ambiguous_link_decisions(VAULT_ROOT, decision_path)
        if args.json or args.review_loose_nodes:
            print(json.dumps(validation, indent=2))
        else:
            print(
                "[AMBIGUOUS-VALIDATION] "
                f"{validation['status']} "
                f"({validation['blocked_count']} blocked / {validation['decision_count']} decisions)"
            )
        if validation["status"] == "blocked":
            raise SystemExit(2)
        return

    if args.write_ambiguous_approval_preview_copy:
        decision_path = Path(args.write_ambiguous_approval_preview_copy)
        if not decision_path.is_absolute():
            decision_path = VAULT_ROOT / decision_path
        preview = write_ambiguous_approval_preview_copy(
            VAULT_ROOT,
            decision_path,
            output_path=args.ambiguous_approval_preview_output,
        )
        if args.json or args.review_loose_nodes:
            print(json.dumps(preview, indent=2))
        else:
            print(
                "[AMBIGUOUS-APPROVAL-PREVIEW] "
                f"{preview['decisions']} decisions -> {preview['approval_preview_path']} "
                "(non-executable)"
            )
        if preview["validation"]["status"] == "blocked":
            raise SystemExit(2)
        return

    if args.apply_review_decisions:
        decision_path = Path(args.apply_review_decisions)
        if not decision_path.is_absolute():
            decision_path = VAULT_ROOT / decision_path
        result = apply_review_decisions(
            VAULT_ROOT,
            decision_path,
            execute=args.execute_review_decisions,
        )
        if args.json or args.review_loose_nodes:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(render_decision_apply_result(result))
        if result.status == "blocked":
            raise SystemExit(2)
        return

    if args.write_approval_preview_copy:
        decision_path = Path(args.write_approval_preview_copy)
        if not decision_path.is_absolute():
            decision_path = VAULT_ROOT / decision_path
        preview = write_approval_preview_copy(
            VAULT_ROOT,
            decision_path,
            output_path=args.approval_preview_output,
        )
        if args.json or args.review_loose_nodes:
            print(json.dumps(preview, indent=2))
        else:
            print(
                "[APPROVAL-PREVIEW] "
                f"{preview['decisions']} decisions -> {preview['approval_preview_path']} "
                "(non-executable)"
            )
        return

    json_output = args.json or args.review_loose_nodes
    report = run(
        fix=args.fix,
        delete_junk=args.delete_junk,
        json_output=json_output,
        report_path=args.report_path,
        write_report=not args.no_report and not json_output,
        write_review_queue=args.write_review_queue,
        strict_review_gate=args.strict_review_gate,
        strict_visible_graph=args.strict_visible_graph,
        fix_semantic_hub_gaps=args.fix_semantic_hub_gaps,
        semantic_hub_gap_limit=args.semantic_hub_gap_limit,
        fix_ambiguous_links=args.fix_ambiguous_links,
        ambiguous_link_limit=args.ambiguous_link_limit,
        review_ambiguous_links=args.review_ambiguous_links,
        ambiguous_review_limit=args.ambiguous_review_limit,
        review_unresolved_links=args.review_unresolved_links,
        unresolved_link_limit=args.unresolved_link_limit,
    )
    if (args.strict_review_gate and report.strict_gate_failed) or (
        args.strict_visible_graph and report.strict_visible_graph_failed
    ):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
