"""Vault-local provider runtime state ledger.

The ledger records facts emitted by execution adapters about provider attempts,
rate limits, cooldown windows, fallback activation, and recovery-to-primary.
It is append-only JSONL and intentionally does not control provider switching.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
LEDGER_RELATIVE_PATH = Path("runtime/providers/state/provider_state_events.jsonl")
VALID_EVENT_TYPES = {
    "provider.request",
    "provider.rate_limited",
    "provider.cooldown_started",
    "provider.cooldown_ended",
    "provider.fallback_activated",
    "provider.recovery_primary_eligible",
    "provider.recovery_primary_completed",
}


class ProviderStateLedgerError(RuntimeError):
    """Fail-closed provider-state ledger error."""


def provider_id_from_model_id(model_id: str | None) -> str | None:
    """Infer the configured provider id from a model identifier."""
    text = str(model_id or "").strip().lower()
    if not text:
        return None
    if text.startswith(("anthropic/", "claude/", "claude")):
        return "claude"
    if text.startswith(("openai/", "gpt", "o1", "o3", "o4")):
        return "openai"
    if text.startswith("grok"):
        return "xai"
    local_markers = ("phi", "llama", "mistral", "qwen", "deepseek", "ollama", "local")
    if text.startswith(local_markers):
        return "local_oss"
    return None


@dataclass(frozen=True)
class ProviderStateEvent:
    event_type: str
    runtime: str
    provider_id: str
    model_id: str | None = None
    task_id: str | None = None
    source: dict[str, Any] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: str | None = None
    event_id: str | None = None
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        event_type = _validate_event_type(self.event_type)
        runtime = _validate_non_empty(self.runtime, "runtime")
        provider_id = _validate_non_empty(self.provider_id, "provider_id")
        timestamp = self.timestamp or _utc_now()
        _parse_timestamp(timestamp, "timestamp")
        if not isinstance(self.source, dict):
            raise ProviderStateLedgerError("source must be an object")
        if not isinstance(self.data, dict):
            raise ProviderStateLedgerError("data must be an object")
        return {
            "schema_version": self.schema_version,
            "event_id": self.event_id or f"provider-state-{uuid.uuid4().hex[:12]}",
            "timestamp": timestamp,
            "event_type": event_type,
            "runtime": runtime,
            "provider_id": provider_id,
            "model_id": self.model_id,
            "task_id": self.task_id,
            "source": dict(self.source),
            "data": dict(self.data),
        }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: Any, field_name: str) -> datetime:
    if not value:
        raise ProviderStateLedgerError(f"{field_name} is required")
    text = str(value)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProviderStateLedgerError(f"{field_name} is not ISO-8601: {text!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _validate_non_empty(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ProviderStateLedgerError(f"{field_name} is required")
    return text


def _validate_event_type(event_type: Any) -> str:
    text = _validate_non_empty(event_type, "event_type")
    if text not in VALID_EVENT_TYPES:
        raise ProviderStateLedgerError(
            f"Unsupported provider state event_type {text!r}; expected one of {sorted(VALID_EVENT_TYPES)}"
        )
    return text


def ledger_path(vault_root: str | Path) -> Path:
    return Path(vault_root) / LEDGER_RELATIVE_PATH


def _validate_event_dict(data: dict[str, Any], *, path: Path | None = None, line_number: int | None = None) -> dict[str, Any]:
    location = ""
    if path is not None:
        location = f" at {path}"
        if line_number is not None:
            location += f":{line_number}"

    required = [
        "schema_version",
        "event_id",
        "timestamp",
        "event_type",
        "runtime",
        "provider_id",
        "source",
        "data",
    ]
    missing = [field_name for field_name in required if field_name not in data]
    if missing:
        raise ProviderStateLedgerError(f"Provider state event{location} missing fields: {missing}")
    if str(data.get("schema_version")) != SCHEMA_VERSION:
        raise ProviderStateLedgerError(
            f"Provider state event{location} has unsupported schema_version {data.get('schema_version')!r}"
        )
    _validate_non_empty(data.get("event_id"), "event_id")
    _parse_timestamp(data.get("timestamp"), "timestamp")
    _validate_event_type(data.get("event_type"))
    _validate_non_empty(data.get("runtime"), "runtime")
    _validate_non_empty(data.get("provider_id"), "provider_id")
    if not isinstance(data.get("source"), dict):
        raise ProviderStateLedgerError(f"Provider state event{location} source must be an object")
    if not isinstance(data.get("data"), dict):
        raise ProviderStateLedgerError(f"Provider state event{location} data must be an object")
    return dict(data)


def append_provider_state_event(vault_root: str | Path, event: ProviderStateEvent | dict[str, Any]) -> dict[str, Any]:
    """Append one validated provider-state event and return the persisted dict."""
    payload = event.to_dict() if isinstance(event, ProviderStateEvent) else dict(event)
    payload = _validate_event_dict(payload)
    path = ledger_path(vault_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    return payload


def load_provider_state_events(
    vault_root: str | Path,
    *,
    runtime_filter: str | None = None,
    provider_id: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Load provider-state events in timestamp order."""
    path = ledger_path(vault_root)
    if not path.exists():
        return []

    events: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            text = line.strip()
            if not text:
                continue
            try:
                data = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ProviderStateLedgerError(f"Invalid provider state JSONL at {path}:{line_number}: {exc}") from exc
            if not isinstance(data, dict):
                raise ProviderStateLedgerError(f"Provider state event at {path}:{line_number} is not an object")
            event = _validate_event_dict(data, path=path, line_number=line_number)
            if runtime_filter and str(runtime_filter).lower() != "all":
                if str(event.get("runtime", "")).lower() != str(runtime_filter).lower():
                    continue
            if provider_id and str(event.get("provider_id", "")).lower() != str(provider_id).lower():
                continue
            events.append(event)

    events.sort(key=lambda item: item.get("timestamp", ""))
    if limit is not None and limit >= 0:
        return events[-int(limit):]
    return events


def _event_time(event: dict[str, Any]) -> datetime:
    return _parse_timestamp(event.get("timestamp"), "timestamp")


def _event_summary(event: dict[str, Any] | None) -> dict[str, Any] | None:
    if event is None:
        return None
    return {
        "event_id": event.get("event_id"),
        "timestamp": event.get("timestamp"),
        "event_type": event.get("event_type"),
        "runtime": event.get("runtime"),
        "provider_id": event.get("provider_id"),
        "model_id": event.get("model_id"),
        "task_id": event.get("task_id"),
        "data": event.get("data") or {},
    }


def _retry_until(event: dict[str, Any]) -> str | None:
    data = event.get("data") or {}
    explicit = data.get("retry_at") or data.get("rate_limit_reset_at")
    if explicit:
        _parse_timestamp(explicit, "rate_limit_reset_at")
        return str(explicit)
    retry_after = data.get("retry_after_seconds")
    if retry_after is None:
        return None
    try:
        seconds = max(0, int(retry_after))
    except (TypeError, ValueError):
        return None
    return (_event_time(event) + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def _cooldown_until(event: dict[str, Any]) -> str | None:
    data = event.get("data") or {}
    explicit = data.get("cooldown_until")
    if explicit:
        _parse_timestamp(explicit, "cooldown_until")
        return str(explicit)
    cooldown_seconds = data.get("cooldown_seconds")
    if cooldown_seconds is None:
        return None
    try:
        seconds = max(0, int(cooldown_seconds))
    except (TypeError, ValueError):
        return None
    return (_event_time(event) + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def _is_future_timestamp(value: str | None, now: datetime) -> bool:
    if not value:
        return False
    return _parse_timestamp(value, "timestamp") > now


def _latest_by_key(events: list[dict[str, Any]], fields: tuple[str, ...]) -> dict[tuple[str, ...], dict[str, Any]]:
    latest: dict[tuple[str, ...], dict[str, Any]] = {}
    for event in events:
        key = tuple(str(event.get(field) or "") for field in fields)
        latest[key] = event
    return latest


def _rate_limit_state(events: list[dict[str, Any]], now: datetime) -> dict[str, Any]:
    rate_events = [event for event in events if event.get("event_type") == "provider.rate_limited"]
    latest_by_provider = _latest_by_key(rate_events, ("runtime", "provider_id"))
    active: list[dict[str, Any]] = []
    observed: list[dict[str, Any]] = []
    for event in latest_by_provider.values():
        retry_until = _retry_until(event)
        summary = _event_summary(event) or {}
        summary["retry_until"] = retry_until
        if _is_future_timestamp(retry_until, now):
            active.append(summary)
        else:
            observed.append(summary)
    if active:
        status = "active"
    elif rate_events:
        status = "observed"
    else:
        status = "no_events"
    return {
        "status": status,
        "tracked": True,
        "source": "provider_state_ledger",
        "event_count": len(rate_events),
        "active_count": len(active),
        "active": active,
        "latest": _event_summary(rate_events[-1] if rate_events else None),
        "latest_by_runtime_provider": active + observed,
    }


def _cooldown_state(events: list[dict[str, Any]], now: datetime) -> dict[str, Any]:
    cooldown_events = [
        event
        for event in events
        if event.get("event_type") in {"provider.cooldown_started", "provider.cooldown_ended"}
    ]
    latest_by_provider = _latest_by_key(cooldown_events, ("runtime", "provider_id"))
    active: list[dict[str, Any]] = []
    inactive: list[dict[str, Any]] = []
    for event in latest_by_provider.values():
        summary = _event_summary(event) or {}
        if event.get("event_type") == "provider.cooldown_started":
            until = _cooldown_until(event)
            summary["cooldown_until"] = until
            if until is None or _is_future_timestamp(until, now):
                active.append(summary)
            else:
                inactive.append(summary)
        else:
            inactive.append(summary)
    if active:
        status = "active"
    elif cooldown_events:
        status = "inactive"
    else:
        status = "no_events"
    return {
        "status": status,
        "tracked": True,
        "source": "provider_state_ledger",
        "event_count": len(cooldown_events),
        "active_count": len(active),
        "active": active,
        "latest": _event_summary(cooldown_events[-1] if cooldown_events else None),
        "latest_by_runtime_provider": active + inactive,
    }


def _runtime_recovery_state(events: list[dict[str, Any]], runtime: str | None = None) -> dict[str, Any]:
    relevant = [
        event
        for event in events
        if event.get("event_type")
        in {
            "provider.fallback_activated",
            "provider.recovery_primary_eligible",
            "provider.recovery_primary_completed",
        }
        and (runtime is None or str(event.get("runtime", "")).lower() == str(runtime).lower())
    ]
    latest = relevant[-1] if relevant else None
    if latest is None:
        status = "no_events"
    elif latest.get("event_type") == "provider.fallback_activated":
        status = "fallback_active"
    elif latest.get("event_type") == "provider.recovery_primary_eligible":
        status = "primary_recovery_eligible"
    elif latest.get("event_type") == "provider.recovery_primary_completed":
        status = "primary_recovered"
    else:
        status = "unknown"
    fallback_event = None
    if status != "primary_recovered":
        fallback_events = [
            event
            for event in relevant
            if event.get("event_type") == "provider.fallback_activated"
        ]
        fallback_event = fallback_events[-1] if fallback_events else None
    return {
        "status": status,
        "tracked": True,
        "source": "provider_state_ledger",
        "event_count": len(relevant),
        "latest": _event_summary(latest),
        "active_fallback_event": _event_summary(fallback_event),
    }


def summarize_provider_state_ledger(
    vault_root: str | Path,
    *,
    runtime_filter: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Summarize the provider-state ledger for provider-status output."""
    current = now or datetime.now(timezone.utc)
    events = load_provider_state_events(vault_root, runtime_filter=runtime_filter)
    runtime_ids = sorted({str(event.get("runtime")) for event in events if event.get("runtime")})
    recovery_by_runtime = {
        runtime_id: _runtime_recovery_state(events, runtime_id)
        for runtime_id in runtime_ids
    }
    return {
        "schema_version": 1,
        "ledger_version": SCHEMA_VERSION,
        "ledger_path": str(ledger_path(vault_root)),
        "ledger_exists": ledger_path(vault_root).exists(),
        "event_count": len(events),
        "latest_event": _event_summary(events[-1] if events else None),
        "rate_limit_state": _rate_limit_state(events, current),
        "cooldown_state": _cooldown_state(events, current),
        "recovery_to_primary": _runtime_recovery_state(events),
        "recovery_by_runtime": recovery_by_runtime,
    }
