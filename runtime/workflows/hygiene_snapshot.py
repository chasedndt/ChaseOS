"""
hygiene_snapshot.py — Pre-mutation snapshot and diff-log for os_hygiene_graph.

Provides a bounded snapshot of all files that apply_fixes() may write, written
to 07_LOGS/Maintain-Runs/_snapshots/YYYY-MM-DD-pre-hygiene/ before any vault
mutations occur. After the run, a per-file diff log records what actually changed.

This is a safety net: if the hygiene workflow produces incorrect output, the
operator can inspect or restore from the snapshot directory.

Public API:
  collect_pre_snapshot   — hash fixable-issue files from a HygieneReport
  write_snapshot_dir     — copy those files to the snapshot directory
  compute_diff_records   — re-hash same files after mutations, return diff list
  write_diff_json        — persist diff_log.json to the snapshot directory

All functions fail open: errors produce empty results rather than crashing the
caller workflow.

Bounds:
  MAX_SNAPSHOT_FILES      = 500 files per run
  MAX_SNAPSHOT_FILE_BYTES = 2 MB per file
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from runtime.cli.vault_hygiene import HygieneReport

SNAPSHOT_ROOT = Path("07_LOGS") / "Maintain-Runs" / "_snapshots"
MAX_SNAPSHOT_FILES = 500
MAX_SNAPSHOT_FILE_BYTES = 2 * 1024 * 1024  # 2 MB


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    """Return hex SHA-256 of path. Returns '' on any read error."""
    try:
        h = hashlib.sha256()
        h.update(path.read_bytes())
        return h.hexdigest()
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Pre-mutation snapshot
# ---------------------------------------------------------------------------

def collect_pre_snapshot(
    vault_root: Path,
    report: "HygieneReport",
) -> dict[str, str]:
    """
    Return {rel_path: sha256} for every file apply_fixes() may write.

    Candidates: issues with severity="auto_fix" that reference existing files.
    Hard ceiling: MAX_SNAPSHOT_FILES entries.
    Files larger than MAX_SNAPSHOT_FILE_BYTES are skipped.
    """
    seen: set[str] = set()
    result: dict[str, str] = {}

    for issue in report.issues:
        if issue.severity != "auto_fix":
            continue
        rel = issue.file_path
        if not rel or rel in seen:
            continue
        seen.add(rel)
        if len(result) >= MAX_SNAPSHOT_FILES:
            break
        abs_path = vault_root / rel
        if not abs_path.is_file():
            continue
        try:
            if abs_path.stat().st_size > MAX_SNAPSHOT_FILE_BYTES:
                continue
        except Exception:
            continue
        h = sha256_file(abs_path)
        if h:
            result[rel] = h

    return result


def write_snapshot_dir(
    vault_root: Path,
    snapshots: dict[str, str],
    date_str: str,
) -> Path:
    """
    Write file copies and a manifest to _snapshots/YYYY-MM-DD-pre-hygiene/.

    Relative paths are flattened using '__' as separator so nested paths
    map to a single filename level inside the snapshot directory.

    The manifest (snapshot_manifest.json) records:
      {date, files: [{rel_path, sha256_before, snapshot_file}]}

    Returns the snapshot directory path. Fails open on per-file copy errors.
    """
    snapshot_dir = vault_root / SNAPSHOT_ROOT / f"{date_str}-pre-hygiene"
    try:
        snapshot_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        return snapshot_dir  # fail open — caller handles absent dir

    manifest: list[dict] = []
    for rel, sha in snapshots.items():
        abs_src = vault_root / rel
        if not abs_src.is_file():
            continue
        flat_name = rel.replace("/", "__").replace("\\", "__")
        dest = snapshot_dir / flat_name
        try:
            dest.write_bytes(abs_src.read_bytes())
            manifest.append({
                "rel_path": rel,
                "sha256_before": sha,
                "snapshot_file": flat_name,
            })
        except Exception:
            pass  # individual copy failures don't abort snapshot

    try:
        (snapshot_dir / "snapshot_manifest.json").write_text(
            json.dumps({"date": date_str, "files": manifest}, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass

    return snapshot_dir


# ---------------------------------------------------------------------------
# Post-mutation diff
# ---------------------------------------------------------------------------

def compute_diff_records(
    vault_root: Path,
    before: dict[str, str],
) -> list[dict]:
    """
    Re-hash snapshot candidates and return per-file diff records.

    Each record: {path, old_sha256, new_sha256, change_type}
    change_type values: "modified" | "unchanged" | "deleted"
    """
    records: list[dict] = []
    for rel, old_sha in before.items():
        abs_path = vault_root / rel
        if not abs_path.exists():
            records.append({
                "path": rel,
                "old_sha256": old_sha,
                "new_sha256": "",
                "change_type": "deleted",
            })
            continue
        new_sha = sha256_file(abs_path)
        change_type = "unchanged" if new_sha == old_sha else "modified"
        records.append({
            "path": rel,
            "old_sha256": old_sha,
            "new_sha256": new_sha,
            "change_type": change_type,
        })
    return records


def write_diff_json(snapshot_dir: Path, diff_records: list[dict]) -> Path:
    """
    Write diff_log.json to snapshot_dir. Returns the file path.

    Structure: {total_files_snapshotted, modified_count, deleted_count, records}
    """
    modified = [r for r in diff_records if r["change_type"] == "modified"]
    deleted = [r for r in diff_records if r["change_type"] == "deleted"]
    diff_path = snapshot_dir / "diff_log.json"
    try:
        diff_path.write_text(
            json.dumps({
                "total_files_snapshotted": len(diff_records),
                "modified_count": len(modified),
                "deleted_count": len(deleted),
                "records": diff_records,
            }, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass  # fail open
    return diff_path
