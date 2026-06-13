"""Read-only runtime overlay adapters for shared graph models."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any

from runtime.graph.graph_models import RuntimeOverlayEvent, normalize_overlay_event_type, stable_digest


RUNTIME_ACTIVITY_EVENT_TYPE_MAP = {
    "runtime.heartbeat": "runtime_heartbeat",
    "run.started": "task_started",
    "run.completed": "run_completed",
    "run.failed": "run_failed",
    "approval.requested": "approval_requested",
    "approval.denied": "approval_blocked",
    "file.read": "node_read_finished",
    "file.written": "node_edit_finished",
    "patch.proposed": "node_edit_started",
    "artifact.created": "artifact_generated",
    "audit.written": "log_written",
}

RUNTIME_DISPLAY_IDS = {
    "aor": "AOR",
    "archon": "Archon",
    "claude": "Claude",
    "claude-code": "Codex",
    "codex": "Codex",
    "hermes": "Hermes",
    "openclaw": "OpenClaw",
}


def _first_text(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
        if value not in (None, "", [], {}, ()):
            text = str(value).strip()
            if text:
                return text
    return None


def _dict_value(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = data.get(key)
        if value not in (None, "", [], {}, ()):
            return value
    return None


def _payload_dict(row: dict[str, Any]) -> dict[str, Any]:
    for key in ("payload_json", "payload", "metadata"):
        payload = row.get(key)
        if isinstance(payload, dict):
            return payload
        if isinstance(payload, str) and payload.strip():
            try:
                decoded = json.loads(payload)
            except Exception:
                decoded = None
            if isinstance(decoded, dict):
                return decoded
    return {}


def _artifact_refs(row: dict[str, Any]) -> list[Any]:
    refs = row.get("artifact_refs")
    if isinstance(refs, list):
        return refs
    if isinstance(refs, str) and refs.strip():
        try:
            decoded = json.loads(refs)
        except Exception:
            decoded = []
        if isinstance(decoded, list):
            return decoded
    return []


def _first_path_value(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, dict):
        for key in ("path", "file_path", "artifact_path", "target_path", "relative_path"):
            found = _first_path_value(value.get(key))
            if found:
                return found
    if isinstance(value, list):
        for item in value:
            found = _first_path_value(item)
            if found:
                return found
    return None


def _runtime_display_id(value: Any) -> str | None:
    raw = _first_text(value)
    if not raw:
        return None
    return RUNTIME_DISPLAY_IDS.get(raw.lower(), raw)


def _runtime_activity_event_type(row: dict[str, Any], payload: dict[str, Any]) -> str:
    raw = _first_text(row.get("event_type"), payload.get("event_type"))
    if not raw:
        return "unknown"
    mapped = RUNTIME_ACTIVITY_EVENT_TYPE_MAP.get(raw.strip().lower())
    return mapped or normalize_overlay_event_type(raw)


def _runtime_activity_file_path(row: dict[str, Any], payload: dict[str, Any]) -> str | None:
    direct = _first_path_value(
        _dict_value(
            payload,
            "file_path",
            "path",
            "target_path",
            "artifact_path",
            "read_targets",
            "write_targets",
            "files",
            "file",
        )
    )
    if direct:
        return direct
    row_path = _first_path_value(
        _dict_value(
            row,
            "file_path",
            "path",
            "target_path",
            "artifact_path",
            "read_targets",
            "write_targets",
            "files",
            "file",
        )
    )
    if row_path:
        return row_path
    return _first_path_value(_artifact_refs(row))


def overlay_event_from_runtime_activity(
    row: dict[str, Any],
    *,
    source: str = "runtime.activity",
) -> RuntimeOverlayEvent:
    """Map a visibility-only runtime activity record into a Graph overlay event.

    The input may be a Phase 11 Chat RuntimeEvent, an adapter spool envelope, or
    a future direct file-touch row. This function only normalizes already
    supplied data; it does not read stores, emit events, or grant authority.
    """

    payload = _payload_dict(row)
    event_type = _runtime_activity_event_type(row, payload)
    timestamp = str(
        row.get("created_at")
        or row.get("timestamp")
        or payload.get("created_at")
        or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    runtime_id = _runtime_display_id(
        row.get("runtime_id")
        or row.get("adapter")
        or row.get("adapter_id")
        or row.get("actor_id")
        or payload.get("runtime_id")
        or payload.get("adapter_id")
    )
    node_id = _first_text(
        row.get("node_id"),
        payload.get("node_id"),
        payload.get("graph_node_id"),
        payload.get("target_node_id"),
    )
    file_path = _runtime_activity_file_path(row, payload)
    source_event_id = _first_text(
        row.get("source_event_id"),
        row.get("event_id"),
        row.get("id"),
        payload.get("adapter_event_id"),
    )
    event_id = f"overlay-{stable_digest(['runtime_activity', source_event_id, event_type, runtime_id, node_id, file_path, timestamp], length=18)}"
    effective_authority = payload.get("chaseos_effective_authority")
    if not isinstance(effective_authority, dict):
        effective_authority = {
            "visibility_event_only": True,
            "approval_consumed": False,
            "provider_call_performed": False,
            "canonical_mutation_allowed": False,
        }
    metadata = {
        "source_event_id": source_event_id,
        "source_event_type": _first_text(row.get("event_type"), payload.get("event_type")),
        "source_status": row.get("status"),
        "summary": row.get("summary"),
        "redaction_state": row.get("redaction_state"),
        "artifact_refs": _artifact_refs(row),
        "payload_keys": sorted(str(key) for key in payload.keys()),
        "chaseos_effective_authority": effective_authority,
    }
    confidence = _first_text(payload.get("source_confidence"), row.get("confidence"))
    if confidence is None and str(row.get("event_type") or "").strip().lower() in {"file.read", "file.written", "artifact.created", "patch.proposed"}:
        confidence = "runtime_claim"
    return RuntimeOverlayEvent(
        event_id=event_id,
        timestamp=timestamp,
        runtime_id=runtime_id,
        agent_id=_first_text(row.get("actor_id"), payload.get("actor_id")),
        event_type=event_type,
        node_id=node_id,
        file_path=file_path,
        task_id=_first_text(row.get("task_id"), payload.get("task_id")),
        run_id=_first_text(row.get("run_id"), payload.get("run_id")),
        status=_first_text(row.get("status"), payload.get("status")),
        confidence=confidence or "observed",
        source=source,
        ttl_seconds=int(row.get("ttl_seconds") or payload.get("ttl_seconds") or 3600),
        metadata=metadata,
    )


def runtime_overlay_events_from_runtime_activity_rows(
    rows: list[dict[str, Any]] | None,
    *,
    source: str = "runtime.activity",
) -> list[RuntimeOverlayEvent]:
    return [overlay_event_from_runtime_activity(row, source=source) for row in rows or []]


def _maybe_artifacts(row: dict[str, Any]) -> list[Any]:
    artifacts = row.get("artifacts")
    if isinstance(artifacts, list):
        return artifacts
    raw = row.get("artifacts_json")
    if isinstance(raw, str) and raw.strip():
        try:
            decoded = json.loads(raw)
        except Exception:
            decoded = []
        if isinstance(decoded, list):
            return decoded
    return []


def _first_artifact_path(row: dict[str, Any]) -> str | None:
    for item in _maybe_artifacts(row):
        if isinstance(item, str) and item.strip():
            return item.strip()
        if isinstance(item, dict):
            for key in ("path", "file_path", "artifact_path", "target_path"):
                value = item.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
    return None


def overlay_event_from_heartbeat(row: dict[str, Any], *, source: str = "agent_bus.heartbeat") -> RuntimeOverlayEvent:
    runtime_id = str(row.get("runtime") or row.get("runtime_id") or "")
    timestamp = str(
        row.get("updated_at")
        or row.get("last_seen_at")
        or row.get("last_seen")
        or row.get("timestamp")
        or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    current_task_id = row.get("current_task_id")
    event_id = f"overlay-{stable_digest(['heartbeat', runtime_id, row.get('runtime_instance_id'), timestamp, current_task_id], length=18)}"
    return RuntimeOverlayEvent(
        event_id=event_id,
        timestamp=timestamp,
        runtime_id=runtime_id or None,
        agent_id=row.get("runtime_instance_id"),
        event_type="runtime_heartbeat",
        task_id=current_task_id,
        status=row.get("status"),
        confidence="observed",
        source=source,
        ttl_seconds=int(row.get("ttl_seconds") or row.get("heartbeat_stale_seconds") or 900),
        metadata=dict(row),
    )


def overlay_event_from_task(row: dict[str, Any], *, source: str = "agent_bus.task") -> RuntimeOverlayEvent:
    status = str(row.get("status") or "unknown")
    runtime_id = str(row.get("owner") or row.get("recipient") or "")
    timestamp = str(row.get("updated_at") or row.get("created_at") or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    task_id = str(row.get("task_id") or "")
    event_id = f"overlay-{stable_digest(['task', task_id, status, runtime_id, timestamp], length=18)}"
    return RuntimeOverlayEvent(
        event_id=event_id,
        timestamp=timestamp,
        runtime_id=runtime_id or None,
        agent_id=row.get("owner_instance"),
        event_type=normalize_overlay_event_type(status),
        file_path=_first_artifact_path(row),
        task_id=task_id or None,
        run_id=row.get("run_id"),
        status=status,
        confidence="observed",
        source=source,
        ttl_seconds=3600,
        metadata=dict(row),
    )


def overlay_event_from_bus_event(row: dict[str, Any], *, source: str = "agent_bus.event") -> RuntimeOverlayEvent:
    event_type = str(row.get("event_type") or "unknown")
    runtime_id = str(row.get("sender") or row.get("runtime") or row.get("runtime_id") or "")
    timestamp = str(row.get("created_at") or row.get("timestamp") or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    task_id = str(row.get("task_id") or "")
    event_id = str(row.get("event_id") or "") or f"overlay-{stable_digest(['bus_event', task_id, event_type, runtime_id, timestamp], length=18)}"
    normalized_event_type = {
        "created": "unknown",
        "claimed": "task_claimed",
        "started": "task_started",
        "blocked": "approval_blocked",
        "review_requested": "approval_requested",
        "review_completed": "run_completed",
        "result_attached": "artifact_generated",
        "completed": "run_completed",
        "cancelled": "run_failed",
        "expired": "run_failed",
        "notice": "unknown",
    }.get(event_type, normalize_overlay_event_type(event_type))
    return RuntimeOverlayEvent(
        event_id=f"overlay-{stable_digest(['bus_event', event_id], length=18)}",
        timestamp=timestamp,
        runtime_id=runtime_id or None,
        event_type=normalized_event_type,
        file_path=_first_artifact_path(row),
        task_id=task_id or None,
        run_id=row.get("run_id"),
        status=event_type,
        confidence="observed",
        source=source,
        ttl_seconds=3600,
        metadata=dict(row),
    )


def runtime_overlay_events_from_agent_bus_rows(
    *,
    heartbeats: list[dict[str, Any]] | None = None,
    tasks: list[dict[str, Any]] | None = None,
    events: list[dict[str, Any]] | None = None,
) -> list[RuntimeOverlayEvent]:
    overlay_events: list[RuntimeOverlayEvent] = []
    for row in heartbeats or []:
        overlay_events.append(overlay_event_from_heartbeat(row))
    for row in tasks or []:
        overlay_events.append(overlay_event_from_task(row))
    for row in events or []:
        overlay_events.append(overlay_event_from_bus_event(row))
    return overlay_events
