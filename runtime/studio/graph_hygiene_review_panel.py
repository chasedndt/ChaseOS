"""
graph_hygiene_review_panel.py — ChaseOS Studio

Read-only review center for os_hygiene_graph maintenance debt.

Parses the latest Maintain-Runs log and Graph-Reports review queue
to produce a structured contract for the Studio Graph Hygiene panel.

Authority:
  - canonical_mutation_allowed = False (always)
  - No delete, archive, replace, or graph-index writes
  - Read-only file access only: 07_LOGS/Maintain-Runs/ + 07_LOGS/Graph-Reports/

Contract output keys:
  surface, summary, latest_run, review_queue, decision_vocabulary,
  artifact_paths, authority, warnings
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def build_graph_hygiene_review_panel(vault_root: Path) -> dict:
    """
    Build the Graph Hygiene review panel contract.

    Parameters
    ----------
    vault_root : Path
        Absolute path to the vault root (no trailing slash required).

    Returns
    -------
    dict  — contract with keys: surface, summary, latest_run, review_queue,
            decision_vocabulary, artifact_paths, authority, warnings
    """
    vault_root = Path(vault_root)
    warnings: list[str] = []

    # -- Latest maintain-run log ------------------------------------------
    latest_run, run_path, run_warnings = _load_latest_maintain_run(vault_root)
    warnings.extend(run_warnings)

    # -- Latest review queue JSON -----------------------------------------
    review_queue, queue_path, queue_warnings = _load_latest_review_queue(vault_root)
    warnings.extend(queue_warnings)

    # -- Derive surface summary -------------------------------------------
    review_gated_loose_nodes = latest_run.get("review_gated_loose_nodes", 0)
    duplicate_candidates      = latest_run.get("duplicate_candidates", 0)
    loose_node_review_count   = review_queue.get("loose_node_review_count", 0)
    files_scanned             = review_queue.get("files_scanned", 0) or latest_run.get("files_scanned", 0)
    run_status                = latest_run.get("status", "unknown")

    summary = {
        "latest_run_status":        run_status,
        "review_gated_loose_nodes": review_gated_loose_nodes,
        "duplicate_candidates":     duplicate_candidates,
        "loose_node_review_count":  loose_node_review_count,
        "files_scanned":            files_scanned,
        "attention_required":       run_status == "blocked_review_required" or review_gated_loose_nodes > 0,
    }

    return {
        "surface": "graph_hygiene_review_panel",
        "summary": summary,
        "latest_run": latest_run,
        "review_queue": review_queue,
        "decision_vocabulary": review_queue.get("allowed_decisions", _DEFAULT_ALLOWED_DECISIONS),
        "delete_policy": review_queue.get("delete_policy", ""),
        "artifact_paths": {
            "maintain_run": str(run_path) if run_path else None,
            "review_queue": str(queue_path) if queue_path else None,
        },
        "authority": {
            "canonical_mutation_allowed": False,
            "delete_allowed":             False,
            "archive_allowed":            False,
            "graph_index_write_allowed":  False,
            "note": "Phase 1 read-only. Decision drafts and application are separate approval-gated flows.",
        },
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Internal: Maintain-Run log parser
# ---------------------------------------------------------------------------

_FM_KEY_RE        = re.compile(r"^(\w+):\s*(.+)$")
_STAGE_ROW_RE     = re.compile(
    r"\|\s*(Stage\s+\d+[^|]*)\|\s*([^|]+)\|\s*([^|]*)\|\s*([^|]*)\|"
)
_LOOSE_NODES_RE   = re.compile(r"review_gated_loose_nodes=(\d+)")
_DUPLICATES_RE    = re.compile(r"duplicate_candidates=(\d+)")


def _load_latest_maintain_run(vault_root: Path) -> tuple[dict, Path | None, list[str]]:
    """Parse the most-recent *-os-hygiene-graph-run.md file."""
    warnings: list[str] = []
    runs_dir = vault_root / "07_LOGS" / "Maintain-Runs"

    if not runs_dir.exists():
        warnings.append("07_LOGS/Maintain-Runs/ not found — no run data available")
        return {}, None, warnings

    run_files = sorted(
        runs_dir.glob("*-os-hygiene-graph-run.md"),
        key=lambda p: p.name,
        reverse=True,
    )
    if not run_files:
        warnings.append("No *-os-hygiene-graph-run.md files found in Maintain-Runs/")
        return {}, None, warnings

    latest = run_files[0]
    try:
        text = latest.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        warnings.append(f"Could not read {latest.name}: {exc}")
        return {}, latest, warnings

    # Parse YAML frontmatter
    fm = _parse_frontmatter(text)

    # Parse stage table
    stages = []
    review_gated_loose_nodes = 0
    duplicate_candidates = 0

    for line in text.splitlines():
        m = _STAGE_ROW_RE.search(line)
        if m:
            stage_label = m.group(1).strip()
            stage_status = m.group(2).strip()
            files_str   = m.group(3).strip()
            detail      = m.group(4).strip()

            # Extract counts from Stage 1 detail
            ln_m = _LOOSE_NODES_RE.search(detail)
            if ln_m:
                review_gated_loose_nodes = int(ln_m.group(1))
            dc_m = _DUPLICATES_RE.search(detail)
            if dc_m:
                duplicate_candidates = int(dc_m.group(1))

            try:
                files_scanned = int(files_str)
            except ValueError:
                files_scanned = 0

            stages.append({
                "label":  stage_label,
                "status": stage_status,
                "files_scanned": files_scanned,
                "detail": detail,
            })

    result = {
        "workflow_id":               fm.get("workflow_id", "os_hygiene_graph"),
        "run_date":                  fm.get("run_date", latest.name[:10]),
        "status":                    fm.get("status", "unknown"),
        "duration_seconds":          _safe_float(fm.get("duration_seconds")),
        "files_scanned":             stages[0].get("files_scanned", 0) if stages else 0,
        "stages":                    stages,
        "review_gated_loose_nodes":  review_gated_loose_nodes,
        "duplicate_candidates":      duplicate_candidates,
        "source_file":               latest.name,
    }
    return result, latest, warnings


# ---------------------------------------------------------------------------
# Internal: Review queue JSON parser
# ---------------------------------------------------------------------------

def _load_latest_review_queue(vault_root: Path) -> tuple[dict, Path | None, list[str]]:
    """Parse the most-recent *-loose-node-review-queue.json file."""
    warnings: list[str] = []
    reports_dir = vault_root / "07_LOGS" / "Graph-Reports"

    if not reports_dir.exists():
        warnings.append("07_LOGS/Graph-Reports/ not found — no review queue available")
        return {}, None, warnings

    queue_files = sorted(
        reports_dir.glob("*-loose-node-review-queue.json"),
        key=lambda p: p.name,
        reverse=True,
    )
    if not queue_files:
        warnings.append("No *-loose-node-review-queue.json files found in Graph-Reports/")
        return {}, None, warnings

    latest = queue_files[0]
    try:
        raw = json.loads(latest.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError) as exc:
        warnings.append(f"Could not parse {latest.name}: {exc}")
        return {}, latest, warnings

    # Keep only a bounded slice of the queue list (first 200 entries) for UI
    queue_items = raw.get("queue", [])
    truncated = len(queue_items) > 200
    result = {
        "status":                raw.get("status", "unknown"),
        "timestamp":             raw.get("timestamp"),
        "files_scanned":         raw.get("files_scanned", 0),
        "total_issues":          raw.get("total_issues", 0),
        "category_counts":       raw.get("category_counts", {}),
        "node_category_counts":  raw.get("node_category_counts", {}),
        "loose_node_review_count": raw.get("loose_node_review_count", 0),
        "allowed_decisions":     raw.get("allowed_decisions", _DEFAULT_ALLOWED_DECISIONS),
        "delete_policy":         raw.get("delete_policy", ""),
        "queue":                 queue_items[:200],
        "queue_total":           len(queue_items),
        "queue_truncated":       truncated,
        "source_file":           latest.name,
    }
    return result, latest, warnings


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _parse_frontmatter(text: str) -> dict[str, str]:
    """Extract YAML-ish frontmatter from --- delimiters."""
    fm: dict[str, str] = {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return fm
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = _FM_KEY_RE.match(line)
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return fm


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


_DEFAULT_ALLOWED_DECISIONS = [
    "keep_and_wire",
    "keep_excluded",
    "archive_after_review",
    "archive_noncanonical_artifact",
    "delete_after_review",
    "replace_with_canonical",
    "manual_investigation",
]
