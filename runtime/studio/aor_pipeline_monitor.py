"""
studio/aor_pipeline_monitor.py — Studio AOR Pipeline Monitor

Read-only surface for inspecting recent AOR pipeline executions:
  - list recent audit records with status, workflow, timing
  - inspect a single audit record in detail
  - summarize execution history by workflow and status

Governance:
  - Read-only: no audit record mutations, no pipeline triggers
  - Reads 07_LOGS/Agent-Activity/*.json audit files only
  - Does not trigger or replay any workflow execution
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

_BOUNDARY = {
    "reads_audit_files": True,
    "writes_audit_files": False,
    "triggers_pipelines": False,
    "canonical_mutation_allowed": False,
}

_AUDIT_DIR = "07_LOGS/Agent-Activity"
_JSON_GLOB = "*.json"


def _load_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _summarize_record(record: dict, filename: str) -> dict[str, Any]:
    return {
        "filename": filename,
        "audit_id": record.get("audit_id"),
        "workflow_id": record.get("workflow_id"),
        "timestamp_utc": record.get("timestamp_utc"),
        "status": record.get("status"),
        "stage_reached": record.get("stage_reached"),
        "escalation_reason": record.get("escalation_reason"),
        "error": record.get("error"),
    }


# ── Public API ────────────────────────────────────────────────────────────────

def list_recent_executions(
    vault_root: str | Path,
    *,
    limit: int = 20,
    workflow_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> dict[str, Any]:
    """
    List recent AOR pipeline executions from audit records.

    Sorted newest-first by filename (YYYYMMDD-HHMMSS prefix). Returns
    summaries only — no raw output payloads.
    """
    vault = Path(vault_root).resolve()
    audit_dir = vault / _AUDIT_DIR

    if not audit_dir.exists():
        return {
            "ok": True,
            "surface": "studio_aor_pipeline_monitor",
            "executions": [],
            "execution_count": 0,
            "limit": limit,
            "workflow_filter": workflow_filter,
            "status_filter": status_filter,
            "boundary": _BOUNDARY,
        }

    records = []
    for path in sorted(audit_dir.glob(_JSON_GLOB), reverse=True):
        record = _load_json(path)
        if record is None:
            continue
        summary = _summarize_record(record, path.name)

        if workflow_filter and workflow_filter not in (summary["workflow_id"] or ""):
            continue
        if status_filter and summary["status"] != status_filter:
            continue

        records.append(summary)
        if len(records) >= limit:
            break

    return {
        "ok": True,
        "surface": "studio_aor_pipeline_monitor",
        "executions": records,
        "execution_count": len(records),
        "limit": limit,
        "workflow_filter": workflow_filter,
        "status_filter": status_filter,
        "boundary": _BOUNDARY,
    }


def inspect_execution(
    vault_root: str | Path,
    filename: str,
) -> dict[str, Any]:
    """
    Return full detail for a single audit record by filename.

    Includes inputs_summary, outputs summary (keys only, not full content),
    and all top-level fields. Raw output values are not surfaced.
    """
    vault = Path(vault_root).resolve()
    audit_dir = vault / _AUDIT_DIR
    path = (audit_dir / filename).resolve()

    # Path traversal guard — filename must not escape audit_dir
    try:
        path.relative_to(audit_dir.resolve())
    except ValueError:
        return {
            "ok": False,
            "error": "Filename escapes audit directory boundary.",
            "surface": "studio_aor_pipeline_monitor",
            "filename": filename,
            "boundary": _BOUNDARY,
        }

    if not path.exists():
        return {
            "ok": False,
            "error": f"Audit record '{filename}' not found.",
            "surface": "studio_aor_pipeline_monitor",
            "filename": filename,
            "boundary": _BOUNDARY,
        }

    record = _load_json(path)
    if record is None:
        return {
            "ok": False,
            "error": f"Audit record '{filename}' could not be loaded.",
            "surface": "studio_aor_pipeline_monitor",
            "filename": filename,
            "boundary": _BOUNDARY,
        }

    outputs_raw = record.get("outputs") or {}
    outputs_keys = list(outputs_raw.keys()) if isinstance(outputs_raw, dict) else []

    return {
        "ok": True,
        "surface": "studio_aor_pipeline_monitor",
        "filename": filename,
        "audit_id": record.get("audit_id"),
        "workflow_id": record.get("workflow_id"),
        "timestamp_utc": record.get("timestamp_utc"),
        "status": record.get("status"),
        "stage_reached": record.get("stage_reached"),
        "escalation_reason": record.get("escalation_reason"),
        "error": record.get("error"),
        "inputs_summary": record.get("inputs_summary"),
        "outputs_keys": outputs_keys,
        "boundary": _BOUNDARY,
    }


def get_execution_summary(
    vault_root: str | Path,
    *,
    limit: int = 100,
) -> dict[str, Any]:
    """
    Aggregate execution counts by workflow_id and status.

    Reads up to `limit` recent audit records and returns per-workflow
    stats: total, success, escalated, failed counts.
    """
    vault = Path(vault_root).resolve()
    audit_dir = vault / _AUDIT_DIR

    if not audit_dir.exists():
        return {
            "ok": True,
            "surface": "studio_aor_pipeline_monitor",
            "total_scanned": 0,
            "by_workflow": {},
            "by_status": {},
            "boundary": _BOUNDARY,
        }

    by_workflow: dict[str, dict[str, int]] = {}
    by_status: dict[str, int] = {}
    scanned = 0

    for path in sorted(audit_dir.glob(_JSON_GLOB), reverse=True):
        if scanned >= limit:
            break
        record = _load_json(path)
        if record is None:
            continue
        scanned += 1

        wf = record.get("workflow_id") or "unknown"
        st = record.get("status") or "unknown"

        if wf not in by_workflow:
            by_workflow[wf] = {"total": 0, "success": 0, "escalated": 0, "failed": 0}
        by_workflow[wf]["total"] += 1
        if st in by_workflow[wf]:
            by_workflow[wf][st] += 1

        by_status[st] = by_status.get(st, 0) + 1

    return {
        "ok": True,
        "surface": "studio_aor_pipeline_monitor",
        "total_scanned": scanned,
        "by_workflow": by_workflow,
        "by_status": by_status,
        "boundary": _BOUNDARY,
    }
