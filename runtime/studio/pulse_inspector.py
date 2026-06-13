"""
studio/pulse_inspector.py — Studio Pulse Inspector

Read-only surface for inspecting the ChaseOS Pulse candidate pipeline:
  - aggregate summary across decks, candidates, review decisions, and enqueue state
  - list all Pulse candidates and review decisions (any or filtered by kind)
  - enqueue pipeline status (approval requests, enqueue results by outcome)
  - list Pulse deck artifacts by audience

Governance:
  - Read-only: no candidate application, no decision writes, no bus mutations
  - Reads 07_LOGS/Pulse-Decks/ and Pulse JSONL logs only
  - Does not apply candidates, grant approvals, or trigger execution
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

_BOUNDARY = {
    "reads_pulse_deck_files": True,
    "reads_candidate_logs": True,
    "reads_review_decision_logs": True,
    "reads_enqueue_result_logs": True,
    "reads_approval_request_logs": True,
    "writes_candidate_logs": False,
    "writes_review_decisions": False,
    "applies_candidates": False,
    "grants_approvals": False,
    "triggers_execution": False,
    "canonical_mutation_allowed": False,
}

_PULSE_DECK_ROOT = "07_LOGS/Pulse-Decks"
_AUDIENCE_DIRS = {"users", "agents", "shared"}


def _load_deck_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _deck_summary(data: dict, path: Path) -> dict[str, Any]:
    return {
        "filename": path.name,
        "deck_id": data.get("deck_id"),
        "audience": data.get("audience"),
        "generated_at": data.get("generated_at"),
        "card_count": len(data.get("cards", [])),
        "deck_title": data.get("deck_title"),
        "sprint_label": data.get("sprint_label"),
    }


def _load_jsonl_records(path: Path) -> list[dict]:
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


# ── Public API ────────────────────────────────────────────────────────────────

def get_pulse_summary(vault_root: str | Path) -> dict[str, Any]:
    """
    Aggregate counts across all Pulse state.

    Returns deck counts by audience, candidate counts by item_kind,
    review decision counts, enqueue result counts by outcome, and
    approval request total.
    """
    vault = Path(vault_root).resolve()
    deck_root = vault / _PULSE_DECK_ROOT

    # Decks by audience
    decks_by_audience: dict[str, int] = {}
    total_decks = 0
    last_deck_at: Optional[str] = None
    all_deck_paths: list[Path] = []
    for audience in _AUDIENCE_DIRS:
        audience_dir = deck_root / audience
        if audience_dir.exists():
            paths = list(audience_dir.glob("*.json"))
            if paths:
                decks_by_audience[audience] = len(paths)
                total_decks += len(paths)
                all_deck_paths.extend(paths)

    if all_deck_paths:
        newest = max(all_deck_paths, key=lambda p: p.stat().st_mtime)
        data = _load_deck_json(newest)
        if data:
            last_deck_at = data.get("generated_at")

    # Candidates + review decisions via candidate_inspector
    counts_by_kind: dict[str, int] = {}
    total_candidates = 0
    total_decisions = 0
    try:
        from runtime.pulse.candidate_inspector import build_candidate_inspector_snapshot
        snapshot = build_candidate_inspector_snapshot(vault)
        counts_by_kind = snapshot.counts_by_kind
        total_candidates = sum(v for k, v in counts_by_kind.items() if k != "review_decision")
        total_decisions = counts_by_kind.get("review_decision", 0)
    except Exception:
        pass

    # Enqueue results by outcome
    enqueue_by_status: dict[str, int] = {}
    enqueue_root = deck_root / "agent-bus-enqueue-results"
    if enqueue_root.exists():
        for path in sorted(enqueue_root.glob("*-enqueue-results.jsonl")):
            for record in _load_jsonl_records(path):
                status = record.get("result_status") or "unknown"
                enqueue_by_status[status] = enqueue_by_status.get(status, 0) + 1

    # Approval requests total
    approval_total = 0
    approval_root = deck_root / "agent-bus-approval-requests"
    if approval_root.exists():
        for path in sorted(approval_root.glob("*-agent-bus-approval-requests.jsonl")):
            approval_total += len(_load_jsonl_records(path))

    return {
        "ok": True,
        "surface": "studio_pulse_inspector",
        "total_decks": total_decks,
        "decks_by_audience": decks_by_audience,
        "last_deck_generated_at": last_deck_at,
        "total_candidates": total_candidates,
        "total_review_decisions": total_decisions,
        "counts_by_kind": counts_by_kind,
        "enqueue_results_by_status": enqueue_by_status,
        "approval_requests_total": approval_total,
        "boundary": _BOUNDARY,
    }


def list_pulse_candidates(
    vault_root: str | Path,
    *,
    kind_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> dict[str, Any]:
    """
    List Pulse candidates and review decisions.

    Parameters
    ----------
    kind_filter : str, optional
        Filter by item_kind: "feedback_candidate", "personal_map_candidate",
        "execution_repair_candidate", or "review_decision".
    status_filter : str, optional
        Filter by status field value (e.g. "pending", "recorded").
    """
    vault = Path(vault_root).resolve()
    try:
        from runtime.pulse.candidate_inspector import (
            INSPECTOR_ITEM_KINDS,
            build_candidate_inspector_snapshot,
        )
        item_kinds: Optional[set[str]] = None
        if kind_filter is not None:
            if kind_filter not in INSPECTOR_ITEM_KINDS:
                return {
                    "ok": False,
                    "error": f"kind_filter must be one of {sorted(INSPECTOR_ITEM_KINDS)}",
                    "surface": "studio_pulse_inspector",
                    "candidates": [],
                    "candidate_count": 0,
                    "boundary": _BOUNDARY,
                }
            item_kinds = {kind_filter}

        snapshot = build_candidate_inspector_snapshot(vault, item_kinds=item_kinds)
        items = snapshot.items
        if status_filter:
            items = [i for i in items if i.status == status_filter]

        candidates = [
            {
                "item_id": i.item_id,
                "item_kind": i.item_kind,
                "candidate_kind": i.candidate_kind,
                "status": i.status,
                "title": i.title,
                "summary": i.summary,
                "candidate_id": i.candidate_id,
                "related_candidate_id": i.related_candidate_id,
                "decision_type": i.decision_type,
                "created_at": i.created_at,
                "source_log_path": i.source_log_path,
            }
            for i in items
        ]
    except Exception as exc:
        return {
            "ok": False,
            "error": f"Failed to load Pulse candidates: {exc}",
            "surface": "studio_pulse_inspector",
            "candidates": [],
            "candidate_count": 0,
            "boundary": _BOUNDARY,
        }

    return {
        "ok": True,
        "surface": "studio_pulse_inspector",
        "candidates": candidates,
        "candidate_count": len(candidates),
        "kind_filter": kind_filter,
        "status_filter": status_filter,
        "boundary": _BOUNDARY,
    }


def get_enqueue_pipeline_status(vault_root: str | Path) -> dict[str, Any]:
    """
    Summarize the Pulse Agent Bus enqueue pipeline state.

    Returns approval request records and enqueue result records with
    counts by outcome (enqueued/blocked/duplicate_skipped/bus_error) and
    task IDs for successfully enqueued candidates.
    """
    vault = Path(vault_root).resolve()
    deck_root = vault / _PULSE_DECK_ROOT

    # Approval requests
    approval_requests: list[dict] = []
    approval_root = deck_root / "agent-bus-approval-requests"
    if approval_root.exists():
        for path in sorted(approval_root.glob("*-agent-bus-approval-requests.jsonl")):
            for record in _load_jsonl_records(path):
                approval_requests.append({
                    "request_id": record.get("request_id"),
                    "candidate_id": record.get("candidate_id"),
                    "candidate_kind": record.get("candidate_kind"),
                    "requested_at": record.get("requested_at"),
                    "status": record.get("status"),
                })

    # Enqueue results
    enqueue_results: list[dict] = []
    enqueue_root = deck_root / "agent-bus-enqueue-results"
    if enqueue_root.exists():
        for path in sorted(enqueue_root.glob("*-enqueue-results.jsonl")):
            for record in _load_jsonl_records(path):
                enqueue_results.append({
                    "result_id": record.get("result_id"),
                    "candidate_id": record.get("candidate_id"),
                    "candidate_kind": record.get("candidate_kind"),
                    "result_status": record.get("result_status"),
                    "enqueued": record.get("enqueued"),
                    "enqueued_at": record.get("enqueued_at"),
                    "task_id": record.get("task_id"),
                    "recipient": record.get("recipient"),
                    "reason": record.get("reason"),
                    "duplicate_found": record.get("duplicate_found"),
                })

    enqueued = [r for r in enqueue_results if r.get("result_status") == "enqueued"]
    blocked = [r for r in enqueue_results if r.get("result_status") == "blocked"]
    duplicate = [r for r in enqueue_results if r.get("result_status") == "duplicate_skipped"]
    bus_error = [r for r in enqueue_results if r.get("result_status") == "bus_error"]

    return {
        "ok": True,
        "surface": "studio_pulse_inspector",
        "approval_requests_total": len(approval_requests),
        "approval_requests": approval_requests,
        "enqueue_results_total": len(enqueue_results),
        "enqueued_count": len(enqueued),
        "blocked_count": len(blocked),
        "duplicate_count": len(duplicate),
        "bus_error_count": len(bus_error),
        "enqueued_task_ids": [r["task_id"] for r in enqueued if r.get("task_id")],
        "enqueue_results": enqueue_results,
        "boundary": _BOUNDARY,
    }


def list_pulse_decks(
    vault_root: str | Path,
    *,
    audience_filter: Optional[str] = None,
) -> dict[str, Any]:
    """
    List Pulse deck artifacts by audience (newest first).

    Parameters
    ----------
    audience_filter : str, optional
        Filter by audience: "users", "agents", or "shared".
    """
    vault = Path(vault_root).resolve()
    deck_root = vault / _PULSE_DECK_ROOT

    if audience_filter is not None and audience_filter not in _AUDIENCE_DIRS:
        return {
            "ok": False,
            "error": f"audience_filter must be one of {sorted(_AUDIENCE_DIRS)}",
            "surface": "studio_pulse_inspector",
            "decks": [],
            "deck_count": 0,
            "boundary": _BOUNDARY,
        }

    audiences = {audience_filter} if audience_filter else _AUDIENCE_DIRS
    decks: list[dict] = []
    for audience in sorted(audiences):
        audience_dir = deck_root / audience
        if not audience_dir.exists():
            continue
        for json_path in sorted(audience_dir.glob("*.json")):
            data = _load_deck_json(json_path)
            if data is not None:
                decks.append(_deck_summary(data, json_path))

    decks.sort(key=lambda d: (d.get("generated_at") or ""), reverse=True)

    return {
        "ok": True,
        "surface": "studio_pulse_inspector",
        "decks": decks,
        "deck_count": len(decks),
        "audience_filter": audience_filter,
        "boundary": _BOUNDARY,
    }
