"""ChaseOS Provenance Linker — Runtime Anchor Enforcement.

Scans the vault to ensure AI-generated output (agent activity,
operator briefs, build logs) reliably links back to its architect/author.
Enforces bi-directional graph connectivity for runtime profiles.

Rules:
    - Files containing 'hermes' or 'claude' -> [[Hermes-Runtime-Profile]]
    - Files containing 'operator', 'optimus', 'openclaw', 'sygnal' -> [[OpenClaw-Runtime-Profile]]
    - Files in 07_LOGS/Agent-Activity -> [[Agent-Activity-Index]]
    
Usage:
    python -m runtime.cli.provenance_linker       # dry-run
    python -m runtime.cli.provenance_linker --fix # execute
"""

from __future__ import annotations

import os
import re
import sys
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VAULT_ROOT = SCRIPT_DIR.parents[1]

if not (VAULT_ROOT / "CLAUDE.md").exists():
    print(f"ERROR: Could not find CLAUDE.md at {VAULT_ROOT}", file=sys.stderr)
    sys.exit(1)

# MCP Audit Logging
sys.path.insert(0, str(VAULT_ROOT))
try:
    from runtime.mcp.audit.logger import MCPAuditLogger
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

AUDIT_DIR = VAULT_ROOT / "07_LOGS" / "Agent-Activity"

# Directories to skip
SKIP_DIRS = {
    ".obsidian", ".venv", ".claude", ".codex", ".codex_tmp_test",
    ".hermes", ".chaseos", ".pytest_cache", ".vscode", ".git",
    "__pycache__", "chaseos.egg-info", "node_modules", "build",
    "core_export", "core_templates", "fixtures", "_tmp_acquisition_cockpit",
}

# Regex for finding wikilinks
WIKILINK_RE = re.compile(r"\[\[([^\]\|]+)(?:\|[^\]]*)?\]\]")

@dataclass
class ScanReport:
    files_scanned: int = 0
    files_modified: int = 0
    links_added: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    details: list[str] = field(default_factory=list)

def _mcp_audit(outcome: str, files_read: list[str], files_written: list[str], detail: str):
    if not MCP_AVAILABLE:
        return
    logger = MCPAuditLogger(audit_dir=AUDIT_DIR)
    try:
        logger.log(
            request_id=f"req-{uuid.uuid4().hex[:12]}",
            surface_id="provenance_linker.fix",
            surface_class="tool",
            runtime_id="provenance_linker",
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
        pass


def extract_wikilink_stems(text: str) -> set[str]:
    stems = set()
    for m in WIKILINK_RE.finditer(text):
        target = m.group(1).strip()
        if target.endswith(".md"):
            target = target[:-3]
        if "/" in target or "\\" in target:
            target = target.replace("\\", "/").rsplit("/", 1)[-1]
        stems.add(target)
    return stems


def get_required_links(filepath: Path) -> list[str]:
    """Determine what links a file MUST have based on provenance rules."""
    req = []
    fname = filepath.name.lower()
    rel_path = filepath.relative_to(VAULT_ROOT).as_posix()
    
    # Ignore indexes themselves or templates
    if fname.endswith("-index.md") or fname == "index.md" or "05_TEMPLATES" in rel_path:
        return []

    # 1. Folder rules
    if rel_path.startswith("07_LOGS/Agent-Activity/"):
        req.append("Agent-Activity-Index")
        
    # 2. Runtime/Author rules based on filename
    if "hermes" in fname or "claude" in fname or "sygnal" in fname:
        req.append("Hermes-Runtime-Profile")
        
    if any(k in fname for k in ["operator", "optimus", "openclaw"]):
        req.append("OpenClaw-Runtime-Profile")

    return req


def inject_links(content: str, links: list[str]) -> str:
    """Inject missing links into the graph-links footer."""
    if not links:
        return content

    links_str = " · ".join(f"[[{l}]]" for l in links)
    
    # If there is already a graph links footer, append to the first one
    if "*Graph links:" in content:
        content = content.replace(
            "*Graph links:",
            f"*Graph links: {links_str} ·",
            1
        )
    else:
        # Append to the end of the file
        content = content.rstrip() + f"\n\n*Graph links: {links_str}*\n"
        
    return content


def run(fix: bool = False, vault_root: Path | None = None):
    if vault_root is not None:
        global VAULT_ROOT, AUDIT_DIR
        root = Path(vault_root).resolve()
        original_root = VAULT_ROOT
        original_audit_dir = AUDIT_DIR
        VAULT_ROOT = root
        AUDIT_DIR = root / "07_LOGS" / "Agent-Activity"
        try:
            return run(fix=fix)
        finally:
            VAULT_ROOT = original_root
            AUDIT_DIR = original_audit_dir

    report = ScanReport()
    files_read = []
    files_written = []
    
    print(f"[SCAN] Scanning vault: {VAULT_ROOT}")
    
    for dp, dns, fns in os.walk(VAULT_ROOT):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for fn in fns:
            if not fn.endswith(".md"):
                continue
            
            p = Path(dp) / fn
            report.files_scanned += 1
            
            required_links = get_required_links(p)
            if not required_links:
                continue
                
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
                files_read.append(p.relative_to(VAULT_ROOT).as_posix())
            except Exception:
                continue
                
            existing_stems = extract_wikilink_stems(content)
            missing = [L for L in required_links if L not in existing_stems]
            
            if missing:
                if fix:
                    new_content = inject_links(content, missing)
                    p.write_text(new_content, encoding="utf-8")
                    files_written.append(p.relative_to(VAULT_ROOT).as_posix())
                    report.files_modified += 1
                    for m in missing:
                        report.links_added[m] += 1
                    report.details.append(f"Updated {fn} -> {missing}")
                else:
                    print(f"  [MISSING] {fn} is missing links: {missing}")

    if not fix:
        print("\n[DRY-RUN] Run with --fix to apply.")
        return report

    _mcp_audit(
        outcome="success",
        files_read=files_read,
        files_written=files_written,
        detail=f"Scanned {report.files_scanned}, modified {report.files_modified}"
    )

    print(f"\n{'=' * 72}")
    print("Runtime Provenance Linker — Complete")
    print(f"{'=' * 72}")
    print(f"  Files scanned:   {report.files_scanned}")
    print(f"  Files modified:  {report.files_modified}")
    for link, count in report.links_added.items():
        print(f"    - Added [[{link}]] x {count}")

    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="ChaseOS Runtime Provenance Linker")
    parser.add_argument("--fix", action="store_true", help="Apply missing links")
    args = parser.parse_args()
    run(fix=args.fix)

if __name__ == "__main__":
    main()
