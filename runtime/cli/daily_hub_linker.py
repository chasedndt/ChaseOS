"""ChaseOS Daily Hub Linker — Chronological Graph Integrity Engine.

Scans the entire vault for YYYY-MM-DD-prefixed markdown files and ensures
every active date has a corresponding Daily Note hub that links to all
files produced on that day, categorised by domain stream.

The Daily Note acts as a chronological anchor in the Obsidian graph,
preventing automated outputs (operator briefs, build logs, SBP runs,
archive docs) from floating as disconnected nodes.

Integrates with the ChaseOS Runtime MCP audit logger to record all
vault mutations.

Usage:
    python -m runtime.cli.daily_hub_linker                 # dry-run (report only)
    python -m runtime.cli.daily_hub_linker --fix           # create/update daily notes
    python -m runtime.cli.daily_hub_linker --fix --update-index  # also update Daily-Index

Safety:
    - Dry-run by default — never mutates without --fix
    - Never overwrites human-written daily note content
    - Appends only via clearly-demarcated auto-wired blocks
    - All mutations logged via MCP audit trail
    - Backlinks injected into wired files for bidirectional connectivity
"""

from __future__ import annotations

import os
import re
import sys
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

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
    """Return an explicit timezone-aware local timestamp for operator-local daily hub dating."""
    return datetime.now(timezone.utc).astimezone()

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
    """Write an MCP audit record for a daily_hub_linker mutation."""
    if not MCP_AVAILABLE:
        return
    logger = MCPAuditLogger(audit_dir=AUDIT_DIR)
    try:
        logger.log(
            request_id=f"req-{uuid.uuid4().hex[:12]}",
            surface_id=surface_id,
            surface_class="tool",
            runtime_id="daily_hub_linker",
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
        pass  # fail-open: audit failure must not block linker


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Valid date prefix regex  YYYY-MM-DD
DATE_RE = re.compile(r"^(202[0-9]-[0-1][0-9]-[0-3][0-9])(?:[-_].+)?\.md$")

# Wikilink extraction
WIKILINK_RE = re.compile(r"\[\[([^\]\|]+)(?:\|[^\]]*)?\]\]")

# Directories to skip during scan
SKIP_DIRS = {
    ".obsidian", ".venv", ".claude", ".codex", ".codex_tmp_test",
    ".hermes", ".chaseos", ".pytest_cache", ".vscode", ".git",
    "__pycache__", "chaseos.egg-info", "node_modules", "build",
    "core_export", "core_templates", "fixtures", "_tmp_acquisition_cockpit",
}

# Auto-wired block sentinel — used to detect and replace existing auto-blocks
AUTO_BLOCK_HEADER = "## Auto-Wired Activity Hub"
def _find_auto_block_range(content: str) -> tuple[int, int] | None:
    """Find the byte-offset range of an existing auto-wired block.

    Returns (start, end) where content[start:end] is the block to replace,
    or None if no block exists.  Boundaries:
      - start = newline before '## Auto-Wired Activity Hub'
      - end   = position of the next top-level '## ' heading (not ###),
                or '*Graph links:', or EOF
    """
    idx = content.find(AUTO_BLOCK_HEADER)
    if idx == -1:
        return None

    # Walk back to the preceding newline
    start = content.rfind("\n", 0, idx)
    if start == -1:
        start = 0

    # Scan forward from the header line-by-line
    search_from = idx + len(AUTO_BLOCK_HEADER)
    end = len(content)
    pos = search_from
    first_line = True
    for line in content[search_from:].split("\n"):
        if first_line:
            first_line = False
            pos += len(line) + 1
            continue
        # Top-level heading (## but not ###)
        if line.startswith("## ") and not line.startswith("### "):
            end = pos
            break
        if line.strip().startswith("*Graph links:"):
            end = pos
            break
        pos += len(line) + 1

    return (start, end)

# Folder -> domain stream categorisation
# Order matters: more specific prefixes first
STREAM_CATEGORIES: list[tuple[str, str]] = [
    ("07_LOGS/Build-Logs/",               "Build Logs"),
    ("07_LOGS/Agent-Activity/",           "Agent Activity"),
    ("07_LOGS/Operator-Briefs/_drafts/",  "Operator Briefs (Drafts)"),
    ("07_LOGS/Operator-Briefs/",          "Operator Briefs"),
    ("07_LOGS/SBP-Runs/",                 "SBP Pipeline Runs"),
    ("07_LOGS/Morning-Thesis/",           "Morning Thesis"),
    ("07_LOGS/Trade-Journal/",            "Trade Journal"),
    ("07_LOGS/Trading-Weekly/",           "Trading Weekly"),
    ("07_LOGS/Decision-Ledger/",          "Decision Ledger"),
    ("07_LOGS/Pivot-Log/",                "Pivot Log"),
    ("07_LOGS/Graph-Reports/",            "Graph Reports"),
    ("07_LOGS/Hygiene-Reports/",          "Hygiene Reports"),
    ("07_LOGS/Daily/",                    "_SKIP_"),  # skip daily notes themselves
    ("07_LOGS/Code-Audit-Log/",           "Code Audit"),
    ("99_ARCHIVE/Documentation-History/", "Documentation History"),
    ("99_ARCHIVE/Reporting/",             "Archive Reports"),
]

DAILY_DIR = VAULT_ROOT / "07_LOGS" / "Daily"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class DatedFile:
    """A single date-prefixed file found in the vault."""
    stem: str
    rel_path: str       # forward-slash relative path from vault root
    date: str           # YYYY-MM-DD
    stream: str         # categorised domain stream name
    folder: str         # parent folder relative path


@dataclass
class DailyHubReport:
    """Tracks all operations performed by the linker."""
    dates_found: int = 0
    files_scanned: int = 0
    notes_created: int = 0
    notes_updated: int = 0
    backlinks_added: int = 0
    index_updated: bool = False
    details: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

def categorise_stream(rel_path: str) -> str:
    """Determine the domain stream from a file's relative path."""
    normalised = rel_path.replace("\\", "/")
    for prefix, stream in STREAM_CATEGORIES:
        if normalised.startswith(prefix):
            return stream
    return "Other"


def scan_dated_files() -> dict[str, list[DatedFile]]:
    """Walk the vault and collect all YYYY-MM-DD-prefixed .md files, grouped by date."""
    date_map: dict[str, list[DatedFile]] = defaultdict(list)

    for dp, dns, fns in os.walk(VAULT_ROOT):
        dns[:] = sorted(d for d in dns if d not in SKIP_DIRS)
        for fn in sorted(fns):
            if not fn.endswith(".md"):
                continue

            match = DATE_RE.match(fn)
            if not match:
                continue

            date_str = match.group(1)
            filepath = Path(dp) / fn
            rel_path = filepath.relative_to(VAULT_ROOT).as_posix()
            stream = categorise_stream(rel_path)

            # Skip daily notes themselves — we're building them, not linking them
            if stream == "_SKIP_":
                continue

            date_map[date_str].append(DatedFile(
                stem=filepath.stem,
                rel_path=rel_path,
                date=date_str,
                stream=stream,
                folder=Path(dp).relative_to(VAULT_ROOT).as_posix(),
            ))

    return date_map


# ---------------------------------------------------------------------------
# Wikilink helpers
# ---------------------------------------------------------------------------

def extract_wikilink_stems(text: str) -> set[str]:
    """Return all [[target]] stems found in text.

    Handles:
      - Simple: [[stem]]
      - Aliased: [[stem|display]]
      - Path-prefixed: [[../../folder/stem|display]]
    """
    stems = set()
    for m in WIKILINK_RE.finditer(text):
        target = m.group(1).strip()
        if target.endswith(".md"):
            target = target[:-3]
        # Handle path-prefixed wikilinks — extract final component
        if "/" in target or "\\" in target:
            target = target.replace("\\", "/").rsplit("/", 1)[-1]
        stems.add(target)
    return stems


# ---------------------------------------------------------------------------
# Daily note builder
# ---------------------------------------------------------------------------

def build_auto_block(files: list[DatedFile], date_str: str) -> str:
    """Build a well-structured auto-wired activity hub block, categorised by stream."""
    dt = _local_now().strftime("%Y-%m-%d")

    # Group by stream, preserving order
    streams: dict[str, list[DatedFile]] = {}
    for f in files:
        streams.setdefault(f.stream, []).append(f)

    lines = [f"\n\n{AUTO_BLOCK_HEADER} ({dt})\n"]
    lines.append(f"> Auto-generated by `daily_hub_linker` — links all vault activity for {date_str}.\n")

    for stream_name, stream_files in streams.items():
        lines.append(f"\n### {stream_name}\n")
        lines.append("| File |")
        lines.append("|------|")
        for f in sorted(stream_files, key=lambda x: x.stem):
            lines.append(f"| [[{f.stem}]] |")

    lines.append("")
    return "\n".join(lines)


def build_stub_daily_note(date_str: str) -> str:
    """Build a minimal daily note stub for dates with no human-written note."""
    return (
        f"---\n"
        f"type: daily-note\n"
        f"date: {date_str}\n"
        f"auto_generated: true\n"
        f"---\n\n"
        f"# {date_str} — Daily Note\n\n"
        f"> Auto-generated daily hub node. Automated outputs were produced "
        f"on this day without a corresponding human daily note.\n\n"
        f"---\n\n"
        f"*Graph links: [[Daily-Index]] · [[Build-Logs-Index]] · "
        f"[[Operator-Briefs-Index]] · [[Documentation-History-Index]]*\n"
    )


def inject_auto_block(existing_content: str, auto_block: str) -> str:
    """Safely inject or replace the auto-wired block in a daily note.

    Rules:
      - If an existing auto-wired block exists, replace it entirely.
      - If a *Graph links: footer exists, insert the block BEFORE the
        LAST occurrence.
      - Otherwise, append to end.
      - Never touches human-written content above or below the block.
    """
    # If existing auto block found, replace it
    block_range = _find_auto_block_range(existing_content)
    if block_range:
        start, end = block_range
        return existing_content[:start] + auto_block + existing_content[end:]

    # Find the LAST *Graph links: footer
    graph_link_positions = [
        m.start() for m in re.finditer(r"\n\*Graph links:", existing_content)
    ]

    if graph_link_positions:
        pos = graph_link_positions[-1]
        return existing_content[:pos] + auto_block + existing_content[pos:]

    # No graph links footer — append
    return existing_content.rstrip() + auto_block + "\n"


# ---------------------------------------------------------------------------
# Backlink injector
# ---------------------------------------------------------------------------

def inject_backlink(filepath: Path, daily_stem: str, report: DailyHubReport) -> bool:
    """Add a [[YYYY-MM-DD]] backlink to a file if it doesn't already have one.

    Returns True if the file was modified.
    """
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False

    # Check if the daily note stem is already linked anywhere
    existing_stems = extract_wikilink_stems(content)
    if daily_stem in existing_stems:
        return False

    # Inject backlink — append to graph links if present, or add footer
    backlink = f"[[{daily_stem}]]"

    if "*Graph links:" in content:
        # Add to the FIRST graph links line (the canonical one)
        content = content.replace(
            "*Graph links:",
            f"*Graph links: {backlink} ·",
            1,
        )
    else:
        content = content.rstrip() + f"\n\n*Graph links: {backlink}*\n"

    filepath.write_text(content, encoding="utf-8")
    report.backlinks_added += 1
    return True


# ---------------------------------------------------------------------------
# Daily-Index updater
# ---------------------------------------------------------------------------

def update_daily_index(date_map: dict[str, list[DatedFile]], report: DailyHubReport) -> list[str]:
    """Ensure the Daily-Index.md references every daily note.

    Returns list of files written.
    """
    index_path = DAILY_DIR / "Daily-Index.md"
    if not index_path.exists():
        return []

    content = index_path.read_text(encoding="utf-8")
    existing_stems = extract_wikilink_stems(content)
    files_written = []

    missing_dates = []
    for date_str in sorted(date_map.keys()):
        daily_stem = date_str  # stem of YYYY-MM-DD.md
        if daily_stem not in existing_stems:
            missing_dates.append(date_str)

    if not missing_dates:
        return []

    # Build a simple supplementary table for dates not yet in the index
    dt = _local_now().strftime("%Y-%m-%d")
    block = (
        f"\n\n## Auto-Wired Daily Notes ({dt})\n\n"
        f"| Date | Notes |\n"
        f"|------|-------|\n"
    )
    for date_str in missing_dates:
        block += f"| [[{date_str}]] | Auto-generated hub |\n"

    # Insert before the last graph links footer
    graph_positions = [m.start() for m in re.finditer(r"\n\*Graph links:", content)]
    if graph_positions:
        pos = graph_positions[-1]
        content = content[:pos] + block + content[pos:]
    else:
        content += block

    index_path.write_text(content, encoding="utf-8")
    files_written.append("07_LOGS/Daily/Daily-Index.md")
    report.index_updated = True
    report.details.append(f"Daily-Index.md updated with {len(missing_dates)} new dates")

    return files_written


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

def run(*, fix: bool = False, update_index: bool = False, vault_root: Path | None = None) -> DailyHubReport:
    """Execute the daily hub linker.

    Args:
        fix: If True, create/update daily notes. If False, report only.
        update_index: If True and fix=True, also update Daily-Index.md.
    """
    if vault_root is not None:
        global VAULT_ROOT, AUDIT_DIR, DAILY_DIR
        root = Path(vault_root).resolve()
        original_root = VAULT_ROOT
        original_audit_dir = AUDIT_DIR
        original_daily_dir = DAILY_DIR
        VAULT_ROOT = root
        AUDIT_DIR = root / "07_LOGS" / "Agent-Activity"
        DAILY_DIR = root / "07_LOGS" / "Daily"
        try:
            return run(fix=fix, update_index=update_index)
        finally:
            VAULT_ROOT = original_root
            AUDIT_DIR = original_audit_dir
            DAILY_DIR = original_daily_dir

    report = DailyHubReport()
    files_read: list[str] = []
    files_written: list[str] = []

    # --- 1. Scan ---
    print(f"[SCAN] Scanning vault: {VAULT_ROOT}")
    date_map = scan_dated_files()
    report.dates_found = len(date_map)

    total_files = sum(len(v) for v in date_map.values())
    print(f"[DONE] Found {total_files} dated files across {len(date_map)} unique dates")

    if not fix:
        # Dry-run: report what would happen
        for date_str in sorted(date_map.keys()):
            daily_path = DAILY_DIR / f"{date_str}.md"
            files = date_map[date_str]
            exists = daily_path.exists()

            if exists:
                content = daily_path.read_text(encoding="utf-8", errors="replace")
                existing_stems = extract_wikilink_stems(content)
                missing = [f for f in files if f.stem not in existing_stems]
                if missing:
                    streams = defaultdict(int)
                    for f in missing:
                        streams[f.stream] += 1
                    stream_summary = ", ".join(f"{k}: {v}" for k, v in streams.items())
                    print(f"  [UPDATE] {date_str}.md — {len(missing)} missing links ({stream_summary})")
            else:
                streams = defaultdict(int)
                for f in files:
                    streams[f.stream] += 1
                stream_summary = ", ".join(f"{k}: {v}" for k, v in streams.items())
                print(f"  [CREATE] {date_str}.md — {len(files)} files ({stream_summary})")

        print(f"\n[DRY-RUN] No changes made. Run with --fix to apply.")
        return report

    # --- 2. Fix: create/update daily notes ---
    print(f"[FIX] Applying daily hub links...")
    DAILY_DIR.mkdir(parents=True, exist_ok=True)

    for date_str in sorted(date_map.keys()):
        daily_path = DAILY_DIR / f"{date_str}.md"
        files = date_map[date_str]
        daily_stem = date_str  # stem of YYYY-MM-DD.md
        is_new = False

        # --- 2a. Create stub if missing ---
        if not daily_path.exists():
            stub = build_stub_daily_note(date_str)
            daily_path.write_text(stub, encoding="utf-8")
            files_written.append(f"07_LOGS/Daily/{date_str}.md")
            report.notes_created += 1
            is_new = True
            report.details.append(f"Created {date_str}.md (new hub for {len(files)} files)")
        elif daily_path.stat().st_size == 0:
            # Handle empty 0-byte files that may have been moved here
            stub = build_stub_daily_note(date_str)
            daily_path.write_text(stub, encoding="utf-8")
            files_written.append(f"07_LOGS/Daily/{date_str}.md")
            report.notes_created += 1
            is_new = True
            report.details.append(f"Populated empty {date_str}.md (was 0 bytes)")

        # --- 2b. Read current content and determine if update needed ---
        content = daily_path.read_text(encoding="utf-8", errors="replace")
        files_read.append(f"07_LOGS/Daily/{date_str}.md")

        # Check what the human-written part already covers (excluding auto block)
        # We strip the auto-block before checking so we only count human refs
        content_without_auto = content
        block_range = _find_auto_block_range(content)
        if block_range:
            s, e = block_range
            content_without_auto = content[:s] + content[e:]

        existing_stems = extract_wikilink_stems(content_without_auto)
        missing = [f for f in files if f.stem not in existing_stems]

        if not missing and AUTO_BLOCK_HEADER not in content:
            # Nothing to do — human content already covers everything
            continue

        if missing or AUTO_BLOCK_HEADER in content:
            # --- 2c. Build auto-block with ALL files for this date ---
            # The block always contains the complete set so it's stable
            # across re-runs (idempotent)
            auto_block = build_auto_block(files, date_str)
            content = inject_auto_block(content, auto_block)
            daily_path.write_text(content, encoding="utf-8")
            if f"07_LOGS/Daily/{date_str}.md" not in files_written:
                files_written.append(f"07_LOGS/Daily/{date_str}.md")

            if not is_new:
                report.notes_updated += 1

            stream_counts = defaultdict(int)
            for f in files:
                stream_counts[f.stream] += 1
            stream_summary = ", ".join(f"{k}: {v}" for k, v in stream_counts.items())
            report.details.append(
                f"{'Created' if is_new else 'Updated'} {date_str}.md — "
                f"hub for {len(files)} files ({stream_summary})"
            )

        # --- 2d. Inject backlinks from linked files -> daily note ---
        for f in files:
            file_path = VAULT_ROOT / f.rel_path.replace("/", os.sep)
            if file_path.exists():
                modified = inject_backlink(file_path, daily_stem, report)
                if modified:
                    files_written.append(f.rel_path)

    # --- 3. Update Daily-Index if requested ---
    if update_index:
        idx_files = update_daily_index(date_map, report)
        files_written.extend(idx_files)

    # --- 4. MCP Audit ---
    _mcp_audit(
        surface_id="daily_hub_linker.fix",
        outcome="success",
        files_read=files_read,
        files_written=files_written,
        detail=(
            f"dates={report.dates_found}; "
            f"created={report.notes_created}; "
            f"updated={report.notes_updated}; "
            f"backlinks={report.backlinks_added}; "
            f"index_updated={report.index_updated}"
        ),
    )

    # --- 5. Summary ---
    print(f"\n{'=' * 72}")
    print(f"Daily Hub Linker — Complete")
    print(f"{'=' * 72}")
    print(f"  Dates with activity:     {report.dates_found}")
    print(f"  Daily notes created:     {report.notes_created}")
    print(f"  Daily notes updated:     {report.notes_updated}")
    print(f"  Backlinks injected:      {report.backlinks_added}")
    print(f"  Daily-Index updated:     {'yes' if report.index_updated else 'no'}")
    print()

    if report.details:
        for d in report.details:
            print(f"  {d}")

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="ChaseOS Daily Hub Linker — chronological graph integrity engine",
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="Apply fixes (create/update daily notes). Without this flag, dry-run only.",
    )
    parser.add_argument(
        "--update-index", action="store_true",
        help="Also update Daily-Index.md with any new daily notes (requires --fix).",
    )
    args = parser.parse_args()

    if args.update_index and not args.fix:
        parser.error("--update-index requires --fix")

    run(fix=args.fix, update_index=args.update_index)


if __name__ == "__main__":
    main()
