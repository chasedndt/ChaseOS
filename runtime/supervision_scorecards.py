"""Runtime-agnostic ChaseOS supervision scorecards.

This module is intentionally read-only. It turns existing Agent-Activity audit
records and Studio runtime-event JSONL records into a compact supervision model
that can be consumed by the CLI, Studio, Hermes, OpenClaw, Codex, or future
runtime lanes without granting any new runtime authority.
"""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any

from runtime.studio.phase11_chat_native_state import STATE_ROOT
from runtime.studio.phase11_chat_runtime_events import validate_runtime_event

SURFACE_ID = "runtime_supervision_scorecards"
MODEL_VERSION = "runtime.supervision_scorecards.v1"
AUDIT_DIR = Path("07_LOGS/Agent-Activity")
RUNTIME_EVENTS_DIR = STATE_ROOT / "runtime-events"
CHAT_EVENTS_DB = STATE_ROOT / "chat_events.sqlite"

SUCCESS_STATUSES = {"success", "succeeded", "completed", "complete", "ok"}
FAILED_STATUSES = {"failed", "failure", "error", "escalated"}
BLOCKED_STATUSES = {"blocked", "waiting-approval", "approval_required", "review-required"}
APPROVAL_EVENT_TYPES = {"approval.requested"}
FAILURE_EVENT_TYPES = {"run.failed"}
SUCCESS_EVENT_TYPES = {"run.completed"}
BLOCKED_EVENT_TYPES = {"approval.requested"}

AUTHORITY = {
    "visibility_only": True,
    "reads_agent_activity": True,
    "reads_runtime_events": True,
    "writes_files": False,
    "provider_calls_performed": False,
    "runtime_dispatch_performed": False,
    "approval_consumed": False,
    "memory_written": False,
    "canonical_state_written": False,
    "external_action_performed": False,
}

RUNTIME_ROW_DEFAULTS = {
    "hermes": {
        "display_name": "Hermes",
        "runtime_status": "available",
        "runtime_authority_active": True,
        "workflow_dispatch_allowed": False,
    },
    "openclaw": {
        "display_name": "OpenClaw",
        "runtime_status": "available",
        "runtime_authority_active": True,
        "workflow_dispatch_allowed": False,
    },
    "claude-code": {
        "display_name": "Claude Code / Archon",
        "runtime_status": "available",
        "runtime_authority_active": True,
        "workflow_dispatch_allowed": False,
    },
    "codex": {
        "display_name": "Codex",
        "runtime_status": "available",
        "runtime_authority_active": True,
        "workflow_dispatch_allowed": False,
    },
    "chaser": {
        "display_name": "Chaser Agent",
        "runtime_status": "planned",
        "runtime_authority_active": False,
        "workflow_dispatch_allowed": False,
    },
}


def _empty_bucket(runtime_id: str) -> dict[str, Any]:
    return {
        "runtime_id": runtime_id,
        "workflow_ids": set(),
        "runs_total": 0,
        "success_count": 0,
        "failed_count": 0,
        "approval_required_count": 0,
        "blocked_action_count": 0,
        "runtime_event_count": 0,
        "audit_record_count": 0,
        "estimated_cost_usd": 0.0,
        "latest_activity_at": "",
        "blocked_reasons": set(),
        "sources": set(),
    }


def _runtime_id_from_audit(record: dict[str, Any], filename: str) -> str:
    for key in ("runtime_id", "runtime", "adapter_id", "adapter", "agent_id"):
        value = str(record.get(key) or "").strip().lower()
        if value:
            return value
    lowered = filename.lower()
    for candidate in ("hermes", "openclaw", "codex", "claude", "chaser"):
        if candidate in lowered:
            return candidate
    return "unknown"


def _runtime_id_from_event(event: dict[str, Any]) -> str:
    payload = event.get("payload_json") if isinstance(event.get("payload_json"), dict) else {}
    for value in (
        payload.get("runtime_id"),
        event.get("adapter"),
        event.get("actor_id"),
    ):
        text = str(value or "").strip().lower()
        if text:
            return "agent-bus" if text in {"bus", "agent_bus"} else text
    thread_id = str(event.get("thread_id") or "").strip().lower()
    if thread_id.startswith("runtime-ops-") and thread_id.endswith("-chat"):
        return thread_id.removeprefix("runtime-ops-").removesuffix("-chat")
    return "unknown"


def _status_text(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "-").replace("_", "-")


def _iter_agent_activity_records(vault: Path, limit: int) -> list[tuple[Path, dict[str, Any]]]:
    root = vault / AUDIT_DIR
    if not root.exists():
        return []
    records: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(root.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            records.append((path, payload))
        if len(records) >= limit:
            break
    return records


def _iter_runtime_events(vault: Path, limit: int) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    db_path = vault / CHAT_EVENTS_DB
    if db_path.exists():
        try:
            uri = f"file:{db_path.as_posix()}?mode=ro"
            conn = sqlite3.connect(uri, uri=True)
            conn.row_factory = sqlite3.Row
            try:
                rows = conn.execute(
                    "SELECT event_json FROM runtime_events ORDER BY seq DESC LIMIT ?",
                    (max(1, int(limit)),),
                ).fetchall()
            finally:
                conn.close()
        except sqlite3.Error:
            rows = []
        for row in rows:
            try:
                payload = json.loads(row["event_json"])
            except (TypeError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict) and not validate_runtime_event(payload):
                events.append(payload)
            if len(events) >= limit:
                return events

    root = vault / RUNTIME_EVENTS_DIR
    if not root.exists():
        return events
    for path in sorted(root.glob("*.jsonl"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in reversed(lines):
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict) and not validate_runtime_event(payload):
                events.append(payload)
            if len(events) >= limit:
                return events
    return events


def _cost_usd(record: dict[str, Any]) -> float:
    candidates = [record.get("cost_usd")]
    cost = record.get("cost")
    if isinstance(cost, dict):
        candidates.extend([cost.get("usd"), cost.get("estimated_usd")])
    usage = record.get("usage")
    if isinstance(usage, dict):
        candidates.extend([usage.get("cost_usd"), usage.get("estimated_cost_usd")])
    for candidate in candidates:
        try:
            if candidate is not None and str(candidate) != "":
                return max(0.0, float(candidate))
        except (TypeError, ValueError):
            continue
    return 0.0


def _record_latest(bucket: dict[str, Any], value: Any) -> None:
    text = str(value or "")
    if text and text > bucket["latest_activity_at"]:
        bucket["latest_activity_at"] = text


def _add_blocked_reasons(bucket: dict[str, Any], payload: dict[str, Any]) -> None:
    for key in ("blocked_reasons", "denied_reasons", "risk_reasons"):
        raw = payload.get(key)
        if isinstance(raw, list):
            for item in raw:
                text = str(item or "").strip()
                if text:
                    bucket["blocked_reasons"].add(text)
        elif isinstance(raw, str) and raw.strip():
            bucket["blocked_reasons"].add(raw.strip())


def _boundary_score(bucket: dict[str, Any]) -> int:
    penalties = (bucket["blocked_action_count"] * 20) + (bucket["failed_count"] * 10) + (bucket["approval_required_count"] * 5)
    return max(0, 100 - penalties)


def _finalize_bucket(bucket: dict[str, Any]) -> dict[str, Any]:
    runs_total = int(bucket["runs_total"])
    success_count = int(bucket["success_count"])
    failed_count = int(bucket["failed_count"])
    return {
        "runtime_id": bucket["runtime_id"],
        "workflow_ids": sorted(bucket["workflow_ids"]),
        "runs_total": runs_total,
        "success_count": success_count,
        "failed_count": failed_count,
        "approval_required_count": int(bucket["approval_required_count"]),
        "blocked_action_count": int(bucket["blocked_action_count"]),
        "runtime_event_count": int(bucket["runtime_event_count"]),
        "audit_record_count": int(bucket["audit_record_count"]),
        "success_rate": round(success_count / runs_total, 4) if runs_total else None,
        "estimated_cost_usd": round(float(bucket["estimated_cost_usd"]), 6),
        "boundary_compliance_score": _boundary_score(bucket),
        "latest_activity_at": bucket["latest_activity_at"],
        "blocked_reasons": sorted(bucket["blocked_reasons"]),
        "sources": sorted(bucket["sources"]),
    }


def _display_name(runtime_id: str) -> str:
    default = RUNTIME_ROW_DEFAULTS.get(runtime_id)
    if default:
        return str(default["display_name"])
    return runtime_id.replace("-", " ").replace("_", " ").title()


def _runtime_rows(scorecards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {str(card.get("runtime_id") or ""): card for card in scorecards}
    ordered_ids = list(RUNTIME_ROW_DEFAULTS)
    for runtime_id in sorted(by_id):
        if runtime_id and runtime_id not in ordered_ids:
            ordered_ids.append(runtime_id)

    rows: list[dict[str, Any]] = []
    for runtime_id in ordered_ids:
        card = by_id.get(runtime_id) or {}
        defaults = RUNTIME_ROW_DEFAULTS.get(runtime_id) or {}
        has_evidence = bool(card)
        rows.append(
            {
                "runtime_id": runtime_id,
                "display_name": _display_name(runtime_id),
                "runtime_status": defaults.get("runtime_status")
                or ("observed" if has_evidence else "unknown"),
                "runtime_authority_active": bool(defaults.get("runtime_authority_active", has_evidence)),
                "workflow_dispatch_allowed": bool(defaults.get("workflow_dispatch_allowed", False)),
                "scorecard_available": has_evidence,
                "runs_total": int(card.get("runs_total") or 0),
                "success_rate": card.get("success_rate"),
                "failed_count": int(card.get("failed_count") or 0),
                "blocked_action_count": int(card.get("blocked_action_count") or 0),
                "approval_required_count": int(card.get("approval_required_count") or 0),
                "estimated_cost_usd": float(card.get("estimated_cost_usd") or 0.0),
                "boundary_compliance_score": card.get("boundary_compliance_score"),
                "latest_activity_at": card.get("latest_activity_at") or "",
                "notes": "planned/non-live row; no runtime activation authority"
                if runtime_id == "chaser"
                else "read-only supervision row",
            }
        )
    return rows


def build_runtime_supervision_scorecards(vault_root: str | Path, *, limit: int = 200) -> dict[str, Any]:
    """Build read-only, runtime-agnostic supervision scorecards.

    The function only reads existing local audit/event artifacts. It performs no
    provider calls, runtime dispatch, Agent Bus writes, approval consumption,
    memory writes, or canonical mutation.
    """
    vault = Path(vault_root).resolve()
    buckets: dict[str, dict[str, Any]] = defaultdict(lambda: _empty_bucket("unknown"))
    warnings: list[str] = []

    for path, record in _iter_agent_activity_records(vault, limit):
        runtime_id = _runtime_id_from_audit(record, path.name)
        if buckets[runtime_id]["runtime_id"] == "unknown":
            buckets[runtime_id] = _empty_bucket(runtime_id)
        bucket = buckets[runtime_id]
        bucket["audit_record_count"] += 1
        bucket["runs_total"] += 1
        bucket["sources"].add("agent_activity")
        workflow_id = str(record.get("workflow_id") or "").strip()
        if workflow_id:
            bucket["workflow_ids"].add(workflow_id)
        status = _status_text(record.get("status"))
        if status in SUCCESS_STATUSES:
            bucket["success_count"] += 1
        if status in FAILED_STATUSES:
            bucket["failed_count"] += 1
        if status in BLOCKED_STATUSES:
            bucket["blocked_action_count"] += 1
        bucket["estimated_cost_usd"] += _cost_usd(record)
        _record_latest(bucket, record.get("timestamp_utc") or record.get("created_at"))
        _add_blocked_reasons(bucket, record)

    for event in _iter_runtime_events(vault, limit):
        runtime_id = _runtime_id_from_event(event)
        if buckets[runtime_id]["runtime_id"] == "unknown":
            buckets[runtime_id] = _empty_bucket(runtime_id)
        bucket = buckets[runtime_id]
        bucket["runtime_event_count"] += 1
        bucket["sources"].add("runtime_events")
        event_type = str(event.get("event_type") or "")
        status = _status_text(event.get("status"))
        payload = event.get("payload_json") if isinstance(event.get("payload_json"), dict) else {}
        workflow_id = str(payload.get("workflow_id") or "").strip()
        if workflow_id:
            bucket["workflow_ids"].add(workflow_id)
        if event_type in SUCCESS_EVENT_TYPES:
            bucket["success_count"] += 1
        if event_type in FAILURE_EVENT_TYPES or status in FAILED_STATUSES:
            bucket["failed_count"] += 1
        if event_type in APPROVAL_EVENT_TYPES:
            bucket["approval_required_count"] += 1
        if event_type in BLOCKED_EVENT_TYPES or status in BLOCKED_STATUSES or payload.get("blocked_reasons"):
            bucket["blocked_action_count"] += 1
        _record_latest(bucket, event.get("created_at"))
        _add_blocked_reasons(bucket, payload)

    scorecards = sorted(
        (_finalize_bucket(bucket) for bucket in buckets.values() if bucket["runtime_id"] != "unknown"),
        key=lambda item: (-item["blocked_action_count"], item["runtime_id"]),
    )
    runtime_rows = _runtime_rows(scorecards)
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "summary": {
            "runtime_count": len(scorecards),
            "runtime_row_count": len(runtime_rows),
            "audit_record_count": sum(item["audit_record_count"] for item in scorecards),
            "runtime_event_count": sum(item["runtime_event_count"] for item in scorecards),
            "blocked_action_count": sum(item["blocked_action_count"] for item in scorecards),
            "approval_required_count": sum(item["approval_required_count"] for item in scorecards),
            "failed_count": sum(item["failed_count"] for item in scorecards),
            "estimated_cost_usd": round(sum(item["estimated_cost_usd"] for item in scorecards), 6),
        },
        "scorecards": scorecards,
        "runtime_rows": runtime_rows,
        "authority": dict(AUTHORITY),
        "warnings": warnings,
    }
