"""
studio/siteops_inspector.py — Studio SiteOps Inspector

Read-only surface for inspecting the ChaseOS SiteOps workflow layer:
  - aggregate summary: run counts by status, approval counts by status,
    candidate promotion pipeline state
  - list run records with workflow, mode, status, and timing
  - list approval records with action, risk level, and decision state
  - inspect a single run record with its full audit event trail

Governance:
  - Read-only: no run mutations, no approval decisions, no browser execution
  - Reads 07_LOGS/SiteOps-Runs/, SiteOps-Audits/, SiteOps-Approvals/ only
  - Does not execute workflows, decide approvals, or modify canonical state
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

_BOUNDARY = {
    "reads_run_records": True,
    "reads_audit_events": True,
    "reads_approval_records": True,
    "writes_run_records": False,
    "writes_approval_decisions": False,
    "executes_workflows": False,
    "triggers_browser": False,
    "canonical_mutation_allowed": False,
}

_RUNS_ROOT = "07_LOGS/SiteOps-Runs"
_AUDITS_ROOT = "07_LOGS/SiteOps-Audits"
_APPROVALS_ROOT = "07_LOGS/SiteOps-Approvals"

_CANDIDATE_WORKFLOW_ID = "browser_skill_candidate.promotion"


def _load_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records: list[dict] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except Exception:
                continue
    except Exception:
        pass
    return records


def _iter_json_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.rglob("*.json"))


def _run_summary(record: dict, path: Path) -> dict[str, Any]:
    return {
        "run_id": record.get("run_id"),
        "workflow_id": record.get("workflow_id"),
        "skill_id": record.get("skill_id"),
        "mode": record.get("mode"),
        "status": record.get("status"),
        "started_at": record.get("started_at"),
        "ended_at": record.get("ended_at"),
        "tenant_id": record.get("tenant_id"),
        "workspace_id": record.get("workspace_id"),
        "filename": path.name,
    }


def _approval_summary(record: dict, path: Path) -> dict[str, Any]:
    return {
        "approval_id": record.get("approval_id"),
        "run_id": record.get("run_id"),
        "workflow_id": record.get("workflow_id"),
        "action": record.get("action"),
        "risk_level": record.get("risk_level"),
        "status": record.get("status"),
        "requested_by": record.get("requested_by"),
        "decided_by": record.get("decided_by"),
        "decided_at": record.get("decided_at"),
        "tenant_id": record.get("tenant_id"),
        "workspace_id": record.get("workspace_id"),
        "filename": path.name,
    }


# ── Public API ────────────────────────────────────────────────────────────────

def get_siteops_summary(vault_root: str | Path) -> dict[str, Any]:
    """
    Aggregate counts across SiteOps runs, approvals, and candidate pipeline.

    Returns run counts by status, approval counts by status, candidate
    promotion run count, and pending approval count.
    """
    vault = Path(vault_root).resolve()

    runs_by_status: dict[str, int] = {}
    candidate_run_count = 0
    latest_run_at: Optional[str] = None

    for path in _iter_json_files(vault / _RUNS_ROOT):
        record = _load_json(path)
        if not record:
            continue
        status = record.get("status") or "unknown"
        runs_by_status[status] = runs_by_status.get(status, 0) + 1
        if record.get("workflow_id") == _CANDIDATE_WORKFLOW_ID:
            candidate_run_count += 1
        started = record.get("started_at") or ""
        if started and (latest_run_at is None or started > latest_run_at):
            latest_run_at = started

    approvals_by_status: dict[str, int] = {}
    pending_count = 0

    for path in _iter_json_files(vault / _APPROVALS_ROOT):
        record = _load_json(path)
        if not record:
            continue
        status = record.get("status") or "unknown"
        approvals_by_status[status] = approvals_by_status.get(status, 0) + 1
        if status == "pending":
            pending_count += 1

    total_runs = sum(runs_by_status.values())
    total_approvals = sum(approvals_by_status.values())

    return {
        "ok": True,
        "surface": "studio_siteops_inspector",
        "total_runs": total_runs,
        "runs_by_status": runs_by_status,
        "candidate_promotion_runs": candidate_run_count,
        "latest_run_at": latest_run_at,
        "total_approvals": total_approvals,
        "approvals_by_status": approvals_by_status,
        "pending_approvals": pending_count,
        "boundary": _BOUNDARY,
    }


def list_siteops_runs(
    vault_root: str | Path,
    *,
    workflow_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 50,
) -> dict[str, Any]:
    """
    List SiteOps run records (newest first).

    Parameters
    ----------
    workflow_filter : str, optional
        Filter by workflow_id substring match.
    status_filter : str, optional
        Filter by exact status value (e.g. "approval_needed", "succeeded").
    limit : int
        Maximum number of run records to return (default 50).
    """
    vault = Path(vault_root).resolve()
    runs: list[dict] = []

    for path in _iter_json_files(vault / _RUNS_ROOT):
        record = _load_json(path)
        if not record:
            continue
        if workflow_filter and workflow_filter not in (record.get("workflow_id") or ""):
            continue
        if status_filter and record.get("status") != status_filter:
            continue
        runs.append(_run_summary(record, path))

    runs.sort(key=lambda r: (r.get("started_at") or ""), reverse=True)
    runs = runs[:limit]

    return {
        "ok": True,
        "surface": "studio_siteops_inspector",
        "runs": runs,
        "run_count": len(runs),
        "workflow_filter": workflow_filter,
        "status_filter": status_filter,
        "limit": limit,
        "boundary": _BOUNDARY,
    }


def list_siteops_approvals(
    vault_root: str | Path,
    *,
    status_filter: Optional[str] = None,
) -> dict[str, Any]:
    """
    List SiteOps approval records.

    Parameters
    ----------
    status_filter : str, optional
        Filter by exact status value (e.g. "pending", "approved", "rejected").
    """
    vault = Path(vault_root).resolve()
    approvals: list[dict] = []

    for path in _iter_json_files(vault / _APPROVALS_ROOT):
        record = _load_json(path)
        if not record:
            continue
        if status_filter and record.get("status") != status_filter:
            continue
        approvals.append(_approval_summary(record, path))

    approvals.sort(key=lambda a: (a.get("approval_id") or ""))

    return {
        "ok": True,
        "surface": "studio_siteops_inspector",
        "approvals": approvals,
        "approval_count": len(approvals),
        "status_filter": status_filter,
        "boundary": _BOUNDARY,
    }


def inspect_siteops_run(
    vault_root: str | Path,
    run_id: str,
    *,
    audit_event_limit: int = 20,
) -> dict[str, Any]:
    """
    Return full detail for a single SiteOps run plus its recent audit events.

    Parameters
    ----------
    run_id : str
        The run_id to inspect (e.g. "siteops_candidate_20260430_063855_...").
    audit_event_limit : int
        Maximum audit events to include (newest first, default 20).
    """
    vault = Path(vault_root).resolve()
    run_record: Optional[dict] = None
    run_path: Optional[Path] = None

    for path in _iter_json_files(vault / _RUNS_ROOT):
        record = _load_json(path)
        if record and record.get("run_id") == run_id:
            run_record = record
            run_path = path
            break

    if run_record is None:
        return {
            "ok": False,
            "error": f"Run '{run_id}' not found.",
            "surface": "studio_siteops_inspector",
            "run_id": run_id,
            "boundary": _BOUNDARY,
        }

    # Locate matching audit JSONL — same stem under SiteOps-Audits
    audit_events: list[dict] = []
    audit_root = vault / _AUDITS_ROOT
    if audit_root.exists():
        for audit_path in audit_root.rglob(f"{run_id}.jsonl"):
            audit_events = _load_jsonl(audit_path)
            break

    recent_events = list(reversed(audit_events))[:audit_event_limit]

    # Matching approval records for this run
    run_approvals: list[dict] = []
    for path in _iter_json_files(vault / _APPROVALS_ROOT):
        record = _load_json(path)
        if record and record.get("run_id") == run_id:
            run_approvals.append(_approval_summary(record, path))

    return {
        "ok": True,
        "surface": "studio_siteops_inspector",
        "run": run_record,
        "audit_events": recent_events,
        "audit_events_shown": len(recent_events),
        "approvals": run_approvals,
        "approval_count": len(run_approvals),
        "boundary": _BOUNDARY,
    }
