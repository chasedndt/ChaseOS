"""Read-only runtime provider/fallback governance status aggregation.

This module intentionally composes existing ChaseOS substrates:
- runtime/{runtime}/model_config.yaml for primary/fallback model chains
- setup provider state for provider readiness
- agent-bus tasks and heartbeats for queue/liveness posture
- optional lifecycle health probes for adapter health

It does not mutate runtime state, switch providers, retry jobs, or control
cooldowns. Control paths belong in later governed commands.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.agent_bus.bus import list_heartbeats, list_tasks
from runtime.agent_bus.capabilities import CapabilityError, RuntimeCapabilities, load_all_capabilities
from runtime.agent_bus.router import RuntimeLiveness, get_runtime_liveness
from runtime.config.store import DEFAULT_CONFIG, load_config_store
from runtime.execution_adapters.model_config import (
    ModelConfigError,
    ModelSpec,
    RuntimeModelConfig,
    load_runtime_model_config,
)
from runtime.lifecycle.health_cli import check_health
from runtime.providers.adapter_health import build_adapter_health_rollup
from runtime.providers.registry import list_provider_status
from runtime.providers.state_ledger import provider_id_from_model_id, summarize_provider_state_ledger


STATUS_VERSION = "2026-04-28"
ACTIVE_TASK_STATES = {"claimed", "in_progress", "blocked", "review"}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _age_seconds(value: str | None, now: datetime) -> float | None:
    parsed = _parse_iso(value)
    if parsed is None:
        return None
    return max(0.0, (now - parsed).total_seconds())


def _copy_default_config() -> dict[str, Any]:
    return json.loads(json.dumps(DEFAULT_CONFIG))


def _load_operator_config(vault_root: Path) -> dict[str, Any]:
    config_path = vault_root / ".chaseos" / "config.yaml"
    if not config_path.exists():
        return _copy_default_config()
    return load_config_store(vault_root=vault_root)


def _provider_lookup(provider_statuses: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("provider_id")): item for item in provider_statuses if item.get("provider_id")}


def _model_spec_to_dict(
    spec: ModelSpec,
    *,
    provider_status_by_id: dict[str, dict[str, Any]],
    role: str,
    order: int,
) -> dict[str, Any]:
    provider_id = provider_id_from_model_id(spec.model_id)
    provider_status = provider_status_by_id.get(provider_id or "")
    return {
        "role": role,
        "order": order,
        "model_id": spec.model_id,
        "provider_id": provider_id,
        "provider_label": provider_status.get("label") if provider_status else None,
        "provider_configured": provider_status.get("configured") if provider_status else None,
        "provider_valid": provider_status.get("valid") if provider_status else None,
        "max_tokens": spec.max_tokens,
        "temperature": spec.temperature,
    }


def _model_config_to_dict(
    config: RuntimeModelConfig,
    *,
    provider_status_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    primary = _model_spec_to_dict(
        config.primary,
        provider_status_by_id=provider_status_by_id,
        role="primary",
        order=0,
    )
    fallbacks = [
        _model_spec_to_dict(
            spec,
            provider_status_by_id=provider_status_by_id,
            role="fallback",
            order=index + 1,
        )
        for index, spec in enumerate(config.fallbacks)
    ]
    return {
        "runtime_name": config.runtime_name,
        "primary": primary,
        "fallbacks": fallbacks,
        "fallback_count": len(fallbacks),
        "fallback_chain_configured": bool(fallbacks),
    }


def _runtime_aliases(caps: RuntimeCapabilities) -> set[str]:
    return {
        str(caps.runtime_name).lower(),
        str(caps.bus_name).lower(),
        str(caps.display_name).lower(),
    }


def _select_capabilities(
    all_caps: dict[str, RuntimeCapabilities],
    runtime_filter: str | None,
) -> list[RuntimeCapabilities]:
    if runtime_filter is None or str(runtime_filter).lower() == "all":
        return [all_caps[name] for name in sorted(all_caps)]
    needle = str(runtime_filter).strip().lower()
    matches = [caps for caps in all_caps.values() if needle in _runtime_aliases(caps)]
    if not matches:
        known = sorted(caps.bus_name for caps in all_caps.values())
        raise ValueError(f"Unknown runtime filter '{runtime_filter}'. Known runtimes: {known}")
    return sorted(matches, key=lambda item: item.bus_name)


def _task_summary(task: dict[str, Any], now: datetime) -> dict[str, Any]:
    request = str(task.get("request") or "")
    return {
        "task_id": task.get("task_id"),
        "status": task.get("status"),
        "recipient": task.get("recipient"),
        "owner": task.get("owner"),
        "owner_instance": task.get("owner_instance"),
        "priority": task.get("priority"),
        "updated_at": task.get("updated_at"),
        "age_seconds": _age_seconds(task.get("updated_at"), now),
        "artifact_count": len(task.get("artifacts") or []),
        "work_fingerprint": task.get("work_fingerprint"),
        "request_preview": request[:160],
    }


def _queue_summary(
    tasks: list[dict[str, Any]],
    runtimes: list[RuntimeCapabilities],
    *,
    now: datetime,
    stuck_after_seconds: int,
) -> dict[str, Any]:
    by_runtime: dict[str, dict[str, Any]] = {}
    stuck_jobs: list[dict[str, Any]] = []
    no_chunk_jobs: list[dict[str, Any]] = []

    for caps in runtimes:
        bus_name = caps.bus_name
        runtime_tasks = [
            task
            for task in tasks
            if task.get("recipient") == bus_name or task.get("owner") == bus_name
        ]
        queued = [task for task in runtime_tasks if task.get("status") == "open" and task.get("recipient") == bus_name]
        active = [
            task
            for task in runtime_tasks
            if task.get("status") in ACTIVE_TASK_STATES and (task.get("owner") == bus_name or task.get("recipient") == bus_name)
        ]
        runtime_stuck: list[dict[str, Any]] = []
        runtime_no_chunk: list[dict[str, Any]] = []
        for task in active:
            age = _age_seconds(task.get("updated_at"), now)
            if age is None or age < stuck_after_seconds:
                continue
            summary = _task_summary(task, now)
            runtime_stuck.append(summary)
            stuck_jobs.append(summary)
            if not task.get("artifacts"):
                runtime_no_chunk.append(summary)
                no_chunk_jobs.append(summary)

        by_runtime[bus_name] = {
            "queued_count": len(queued),
            "active_count": len(active),
            "stuck_count": len(runtime_stuck),
            "no_chunk_count": len(runtime_no_chunk),
            "queued_tasks": [_task_summary(task, now) for task in queued],
            "stuck_tasks": runtime_stuck,
            "no_chunk_tasks": runtime_no_chunk,
        }

    queued_all = [task for task in tasks if task.get("status") == "open"]
    active_all = [task for task in tasks if task.get("status") in ACTIVE_TASK_STATES]
    return {
        "task_count": len(tasks),
        "queued_count": len(queued_all),
        "active_count": len(active_all),
        "stuck_count": len(stuck_jobs),
        "no_chunk_count": len(no_chunk_jobs),
        "stuck_after_seconds": stuck_after_seconds,
        "stuck_definition": "active agent-bus task age >= stuck_after_seconds",
        "no_chunk_definition": "stuck active agent-bus task with no artifacts attached",
        "by_runtime": by_runtime,
        "stuck_jobs": stuck_jobs,
        "no_chunk_jobs": no_chunk_jobs,
    }


def _select_active_runtime(
    *,
    config: dict[str, Any],
    all_caps: dict[str, RuntimeCapabilities],
    liveness: dict[str, RuntimeLiveness],
) -> dict[str, Any]:
    default_runtime = config.get("default_runtime")
    if default_runtime:
        needle = str(default_runtime).strip().lower()
        for caps in all_caps.values():
            if needle in _runtime_aliases(caps):
                live = liveness.get(caps.bus_name)
                return {
                    "runtime_id": caps.bus_name,
                    "runtime_name": caps.runtime_name,
                    "source": "config.default_runtime",
                    "status": "configured",
                    "is_stale": live.is_stale if live else True,
                    "last_seen": live.last_seen if live else None,
                }
        return {
            "runtime_id": str(default_runtime),
            "runtime_name": None,
            "source": "config.default_runtime",
            "status": "configured_unknown_runtime",
            "is_stale": None,
            "last_seen": None,
        }

    live_rows = [
        live
        for live in liveness.values()
        if live.last_seen and live.is_stale is False
    ]
    live_rows.sort(key=lambda item: item.last_seen or "", reverse=True)
    if live_rows:
        live = live_rows[0]
        return {
            "runtime_id": live.runtime,
            "runtime_name": live.runtime_name,
            "source": "freshest_agent_bus_heartbeat",
            "status": "observed",
            "is_stale": live.is_stale,
            "last_seen": live.last_seen,
        }

    return {
        "runtime_id": None,
        "runtime_name": None,
        "source": "none",
        "status": "unknown",
        "is_stale": None,
        "last_seen": None,
    }


def _select_operator_default_provider(
    *,
    config: dict[str, Any],
    provider_statuses: list[dict[str, Any]],
) -> dict[str, Any]:
    provider_by_id = _provider_lookup(provider_statuses)
    configured_default = config.get("default_provider")
    if configured_default:
        provider_id = str(configured_default)
        status = provider_by_id.get(provider_id, {})
        return {
            "provider_id": provider_id,
            "source": "config.default_provider",
            "configured": status.get("configured"),
            "valid": status.get("valid"),
            "default_model": status.get("default_model"),
            "reasoning_policy": status.get("reasoning_policy"),
        }

    valid = [item for item in provider_statuses if item.get("valid")]
    if valid:
        item = valid[0]
        return {
            "provider_id": item.get("provider_id"),
            "source": "first_valid_provider_setup_state",
            "configured": item.get("configured"),
            "valid": item.get("valid"),
            "default_model": item.get("default_model"),
            "reasoning_policy": item.get("reasoning_policy"),
        }

    return {
        "provider_id": None,
        "source": "none",
        "configured": None,
        "valid": None,
        "default_model": None,
        "reasoning_policy": None,
    }


def _adapter_health(
    *,
    caps: RuntimeCapabilities,
    liveness: dict[str, RuntimeLiveness],
    heartbeats: list[dict[str, Any]],
    probe_health: bool,
    health_timeout_seconds: int,
) -> dict[str, Any]:
    live = liveness.get(caps.bus_name)
    runtime_heartbeats = [row for row in heartbeats if row.get("runtime") == caps.bus_name]
    payload: dict[str, Any] = {
        "bus_name": caps.bus_name,
        "heartbeat_status": live.status if live else None,
        "heartbeat_health": live.health if live else None,
        "last_seen": live.last_seen if live else None,
        "age_seconds": live.age_seconds if live else None,
        "is_stale": live.is_stale if live else True,
        "stale_threshold_seconds": live.stale_threshold_seconds if live else caps.heartbeat_stale_seconds,
        "heartbeat_instance_count": len(runtime_heartbeats),
        "lifecycle_probe_checked": probe_health,
        "lifecycle_probe": None,
    }
    if probe_health:
        try:
            probe = check_health(caps.runtime_name, timeout_seconds=health_timeout_seconds)
        except Exception as exc:  # health probes must not break status aggregation
            probe = {
                "runtime_id": caps.runtime_name,
                "healthy": False,
                "failure_reason": f"probe_error:{exc}",
            }
        payload["lifecycle_probe"] = probe
    return payload


def _runtime_status(
    *,
    caps: RuntimeCapabilities,
    vault_root: Path,
    provider_status_by_id: dict[str, dict[str, Any]],
    liveness: dict[str, RuntimeLiveness],
    heartbeats: list[dict[str, Any]],
    queue_by_runtime: dict[str, Any],
    probe_health: bool,
    health_timeout_seconds: int,
    provider_ledger: dict[str, Any],
) -> dict[str, Any]:
    try:
        model_config = load_runtime_model_config(caps.runtime_name, vault_root)
        model_binding = _model_config_to_dict(
            model_config,
            provider_status_by_id=provider_status_by_id,
        )
        model_error = None
    except ModelConfigError as exc:
        model_binding = None
        model_error = str(exc)

    fallback_count = 0
    if isinstance(model_binding, dict):
        fallback_count = int(model_binding.get("fallback_count") or 0)
    recovery_by_runtime = provider_ledger.get("recovery_by_runtime") or {}
    recovery_state = recovery_by_runtime.get(caps.bus_name)
    if recovery_state is None:
        for key, value in recovery_by_runtime.items():
            if str(key).lower() in _runtime_aliases(caps):
                recovery_state = value
                break
    if recovery_state is None:
        recovery_state = {
            "status": "no_events",
            "tracked": True,
            "source": "provider_state_ledger",
            "event_count": 0,
            "latest": None,
            "active_fallback_event": None,
        }
    fallback_event = recovery_state.get("active_fallback_event") if isinstance(recovery_state, dict) else None
    active_fallback_model = None
    if isinstance(fallback_event, dict):
        active_fallback_model = (
            (fallback_event.get("data") or {}).get("fallback_model_id")
            or fallback_event.get("model_id")
        )

    return {
        "runtime_name": caps.runtime_name,
        "bus_name": caps.bus_name,
        "display_name": caps.display_name,
        "description": caps.description,
        "capability_count": len(caps.handles),
        "max_concurrent_tasks": caps.max_concurrent_tasks,
        "priority_ceiling": caps.priority_ceiling,
        "adapter_health": _adapter_health(
            caps=caps,
            liveness=liveness,
            heartbeats=heartbeats,
            probe_health=probe_health,
            health_timeout_seconds=health_timeout_seconds,
        ),
        "queue": queue_by_runtime.get(caps.bus_name, {}),
        "model_binding": model_binding,
        "model_binding_error": model_error,
        "fallback_governance": {
            "fallback_chain_configured": fallback_count > 0,
            "fallback_count": fallback_count,
            "active_fallback_model": active_fallback_model,
            "active_fallback_source": "provider_state_ledger" if active_fallback_model else "no_active_fallback_event",
            "recovery_to_primary": recovery_state,
        },
    }


def _active_runtime_model_binding(
    active_runtime: dict[str, Any],
    runtime_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    active_bus_name = active_runtime.get("runtime_id")
    if not active_bus_name:
        return {
            "primary": None,
            "fallback": None,
            "source": "no active runtime selected",
        }
    row = next((item for item in runtime_rows if item.get("bus_name") == active_bus_name), None)
    binding = row.get("model_binding") if row else None
    if not isinstance(binding, dict):
        return {
            "primary": None,
            "fallback": None,
            "source": "active runtime has no readable model binding",
        }
    fallbacks = binding.get("fallbacks") or []
    return {
        "primary": binding.get("primary"),
        "fallback": fallbacks[0] if fallbacks else None,
        "source": "active_runtime_model_config",
    }


def _warnings(runtime_rows: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    for row in runtime_rows:
        binding = row.get("model_binding")
        if not isinstance(binding, dict):
            warnings.append(
                f"{row.get('bus_name')} model binding is unreadable: {row.get('model_binding_error')}"
            )
            continue
        for model in [binding.get("primary"), *(binding.get("fallbacks") or [])]:
            if not isinstance(model, dict):
                continue
            provider_id = model.get("provider_id") or "unknown"
            if model.get("provider_valid") is False:
                warnings.append(
                    f"{row.get('bus_name')} {model.get('role')} model provider '{provider_id}' is not valid/configured in setup state."
                )
            elif provider_id == "unknown":
                warnings.append(
                    f"{row.get('bus_name')} {model.get('role')} model '{model.get('model_id')}' has no provider inference rule."
                )
    return warnings


def _readiness_summary(
    *,
    provider_statuses: list[dict[str, Any]],
    runtime_rows: list[dict[str, Any]],
    queue: dict[str, Any],
    rate_limit_state: dict[str, Any],
    cooldown_state: dict[str, Any],
    adapter_health_rollup: dict[str, Any],
    warnings: list[str],
) -> dict[str, Any]:
    """Return a compact operator-facing provider/runtime readiness posture."""
    provider_count = len(provider_statuses)
    provider_configured_count = sum(1 for item in provider_statuses if item.get("configured"))
    provider_valid_count = sum(1 for item in provider_statuses if item.get("valid"))
    provider_invalid_count = sum(1 for item in provider_statuses if item.get("configured") and not item.get("valid"))
    runtime_count = len(runtime_rows)
    stale_runtime_count = sum(
        1
        for row in runtime_rows
        if (row.get("adapter_health") or {}).get("is_stale") is True
    )
    model_binding_error_count = sum(1 for row in runtime_rows if row.get("model_binding_error"))
    queue_stuck_count = int(queue.get("stuck_count") or 0)
    queue_no_chunk_count = int(queue.get("no_chunk_count") or 0)

    reasons: list[str] = []
    if provider_valid_count == 0:
        reasons.append("no_valid_providers")
    if provider_invalid_count:
        reasons.append("configured_provider_invalid")
    if model_binding_error_count:
        reasons.append("model_binding_errors")
    if stale_runtime_count:
        reasons.append("stale_runtime_heartbeats")
    if queue_stuck_count:
        reasons.append("stuck_jobs")
    if queue_no_chunk_count:
        reasons.append("no_chunk_jobs")
    if rate_limit_state.get("status") == "active":
        reasons.append("active_rate_limit")
    if cooldown_state.get("status") == "active":
        reasons.append("active_cooldown")
    if warnings:
        reasons.append("warnings_present")

    blocker_reasons = {"no_valid_providers", "model_binding_errors"}
    if blocker_reasons.intersection(reasons):
        posture = "blocked"
    elif reasons:
        posture = "degraded"
    else:
        posture = "ready"

    return {
        "posture": posture,
        "provider_count": provider_count,
        "provider_configured_count": provider_configured_count,
        "provider_valid_count": provider_valid_count,
        "provider_invalid_count": provider_invalid_count,
        "runtime_count": runtime_count,
        "stale_runtime_count": stale_runtime_count,
        "model_binding_error_count": model_binding_error_count,
        "queue_stuck_count": queue_stuck_count,
        "queue_no_chunk_count": queue_no_chunk_count,
        "adapter_health_status": adapter_health_rollup.get("status"),
        "adapter_health_event_count": (adapter_health_rollup.get("totals") or {}).get("event_count", 0),
        "adapter_health_failed_count": (adapter_health_rollup.get("totals") or {}).get("failed_count", 0),
        "adapter_health_affects_provider_fallback": False,
        "warning_count": len(warnings),
        "degradation_reasons": reasons,
        "read_only": True,
    }


def _label_model(model: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(model, dict) or not model.get("model_id"):
        return {
            "provider_id": None,
            "model_id": None,
            "label": "(none)",
        }
    provider_id = model.get("provider_id") or "unknown"
    model_id = model.get("model_id")
    return {
        "provider_id": provider_id,
        "model_id": model_id,
        "label": f"{provider_id}/{model_id}",
    }


def _attention_item(
    *,
    code: str,
    severity: str,
    source: str,
    summary: str,
    next_action: str,
    affects_provider_fallback: bool = False,
) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "source": source,
        "summary": summary,
        "next_action": next_action,
        "affects_provider_fallback": affects_provider_fallback,
    }


def _unique_actions(items: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    actions: list[str] = []
    for item in items:
        action = str(item.get("next_action") or "").strip()
        if not action or action in seen:
            continue
        seen.add(action)
        actions.append(action)
    return actions


def _reason_attention_items(
    *,
    readiness: dict[str, Any],
    warnings: list[str],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    reasons = set(readiness.get("degradation_reasons") or [])
    if "no_valid_providers" in reasons:
        items.append(
            _attention_item(
                code="no_valid_providers",
                severity="blocked",
                source="provider_setup_status",
                summary="No valid configured provider is available.",
                next_action="Run `chaseos setup provider list --json` and configure at least one provider before model execution.",
                affects_provider_fallback=True,
            )
        )
    if "configured_provider_invalid" in reasons:
        items.append(
            _attention_item(
                code="configured_provider_invalid",
                severity="attention",
                source="provider_setup_status",
                summary=f"{readiness.get('provider_invalid_count', 0)} configured provider(s) are invalid.",
                next_action="Inspect provider setup state before routing new runtime work.",
                affects_provider_fallback=True,
            )
        )
    if "model_binding_errors" in reasons:
        items.append(
            _attention_item(
                code="model_binding_errors",
                severity="blocked",
                source="runtime_model_config",
                summary=f"{readiness.get('model_binding_error_count', 0)} runtime model binding(s) could not be read.",
                next_action="Fix runtime model config before trusting primary/fallback model routing.",
                affects_provider_fallback=True,
            )
        )
    if "stale_runtime_heartbeats" in reasons:
        items.append(
            _attention_item(
                code="stale_runtime_heartbeats",
                severity="attention",
                source="agent_bus_heartbeats",
                summary=f"{readiness.get('stale_runtime_count', 0)} runtime heartbeat(s) are stale.",
                next_action="Inspect runtime liveness with `chaseos runtime status --runtime all --json`.",
            )
        )
    if "stuck_jobs" in reasons:
        items.append(
            _attention_item(
                code="stuck_jobs",
                severity="attention",
                source="agent_bus_tasks",
                summary=f"{readiness.get('queue_stuck_count', 0)} active task(s) are past the stuck threshold.",
                next_action="Inspect `chaseos agent-bus status --json` before reclaiming or retrying work.",
            )
        )
    if "no_chunk_jobs" in reasons:
        items.append(
            _attention_item(
                code="no_chunk_jobs",
                severity="attention",
                source="agent_bus_tasks",
                summary=f"{readiness.get('queue_no_chunk_count', 0)} stuck task(s) have no attached artifacts.",
                next_action="Check no-chunk tasks before treating the issue as a provider failure.",
            )
        )
    if "active_rate_limit" in reasons:
        items.append(
            _attention_item(
                code="active_rate_limit",
                severity="attention",
                source="provider_state_ledger",
                summary="Provider-state ledger reports an active rate-limit condition.",
                next_action="Let governed fallback evidence drive routing; do not clear rate-limit state manually.",
                affects_provider_fallback=True,
            )
        )
    if "active_cooldown" in reasons:
        items.append(
            _attention_item(
                code="active_cooldown",
                severity="attention",
                source="provider_state_ledger",
                summary="Provider-state ledger reports an active cooldown condition.",
                next_action="Wait for cooldown evidence or use a governed future control path.",
                affects_provider_fallback=True,
            )
        )
    if "warnings_present" in reasons:
        preview = warnings[0] if warnings else "Warnings are present."
        items.append(
            _attention_item(
                code="warnings_present",
                severity="attention",
                source="runtime_provider_status",
                summary=preview,
                next_action="Review provider-status warnings before starting new runtime work.",
            )
        )
    return items


def _operator_summary(
    *,
    readiness: dict[str, Any],
    active_runtime: dict[str, Any],
    operator_default_provider: dict[str, Any],
    active_binding: dict[str, Any],
    queue: dict[str, Any],
    rate_limit_state: dict[str, Any],
    cooldown_state: dict[str, Any],
    recovery_to_primary: dict[str, Any],
    provider_ledger: dict[str, Any],
    adapter_health_rollup: dict[str, Any],
    warnings: list[str],
) -> dict[str, Any]:
    """Return a Studio/operator-ready card for provider-status output."""
    items = _reason_attention_items(readiness=readiness, warnings=warnings)
    adapter_totals = adapter_health_rollup.get("totals") or {}
    adapter_status = adapter_health_rollup.get("status")
    if adapter_status not in (None, "healthy", "no_events"):
        items.append(
            _attention_item(
                code="adapter_health_attention",
                severity="attention" if adapter_status != "degraded" else "blocked",
                source="adapter_health_rollup",
                summary=(
                    "Adjacent adapter health reports "
                    f"status={adapter_status}, events={adapter_totals.get('event_count', 0)}, "
                    f"failed={adapter_totals.get('failed_count', 0)}."
                ),
                next_action=(
                    "Inspect `chaseos acquisition connector-health --json` and "
                    "`chaseos sbp delivery-health --json` before treating adapter issues as provider failures."
                ),
                affects_provider_fallback=False,
            )
        )

    recovery_status = recovery_to_primary.get("status")
    if recovery_status in {"fallback_active", "primary_recovery_eligible"}:
        items.append(
            _attention_item(
                code=str(recovery_status),
                severity="attention",
                source="provider_state_ledger",
                summary=f"Recovery-to-primary status is `{recovery_status}`.",
                next_action="Use provider-state evidence only when evaluating primary recovery.",
                affects_provider_fallback=True,
            )
        )

    blocked = any(item.get("severity") == "blocked" for item in items)
    if readiness.get("posture") == "blocked" or blocked:
        status = "blocked"
    elif readiness.get("posture") == "degraded" or items:
        status = "attention"
    else:
        status = "ready"

    reason_text = ", ".join(readiness.get("degradation_reasons") or [])
    if status == "blocked":
        headline = f"Runtime provider posture blocked: {reason_text or 'blocking evidence present'}"
    elif status == "attention":
        headline = f"Runtime provider posture needs attention: {reason_text or 'adjacent adapter health needs review'}"
    else:
        headline = "Runtime provider posture ready; no blocking evidence observed."

    primary = _label_model((active_binding.get("primary") if isinstance(active_binding, dict) else None))
    fallback = _label_model((active_binding.get("fallback") if isinstance(active_binding, dict) else None))
    return {
        "schema_version": 1,
        "status": status,
        "provider_runtime_posture": readiness.get("posture"),
        "headline": headline,
        "active_runtime": {
            "runtime_id": active_runtime.get("runtime_id"),
            "status": active_runtime.get("status"),
            "source": active_runtime.get("source"),
            "is_stale": active_runtime.get("is_stale"),
        },
        "operator_default_provider": {
            "provider_id": operator_default_provider.get("provider_id"),
            "valid": operator_default_provider.get("valid"),
            "source": operator_default_provider.get("source"),
        },
        "model_route": {
            "primary": primary,
            "fallback": fallback,
            "source": active_binding.get("source") if isinstance(active_binding, dict) else None,
        },
        "provider_governance": {
            "provider_state_event_count": provider_ledger.get("event_count", 0),
            "rate_limit_status": rate_limit_state.get("status"),
            "cooldown_status": cooldown_state.get("status"),
            "recovery_to_primary_status": recovery_to_primary.get("status"),
        },
        "queue": {
            "task_count": queue.get("task_count", 0),
            "queued_count": queue.get("queued_count", 0),
            "active_count": queue.get("active_count", 0),
            "stuck_count": queue.get("stuck_count", 0),
            "no_chunk_count": queue.get("no_chunk_count", 0),
        },
        "adapter_health": {
            "status": adapter_status,
            "event_count": adapter_totals.get("event_count", 0),
            "failed_count": adapter_totals.get("failed_count", 0),
            "skipped_count": adapter_totals.get("skipped_count", 0),
            "affects_provider_fallback": False,
        },
        "attention_items": items,
        "recommended_actions": _unique_actions(items),
        "read_only": True,
        "boundary": {
            "presentation_only": True,
            "controls_provider_switching": False,
            "controls_cooldowns": False,
            "controls_recovery_to_primary": False,
            "controls_adapter_retries": False,
        },
    }


def build_runtime_provider_status(
    *,
    vault_root: str | Path,
    runtime_filter: str | None = "all",
    stuck_after_seconds: int = 900,
    probe_health: bool = False,
    health_timeout_seconds: int = 5,
) -> dict[str, Any]:
    """Build a read-only provider/fallback governance status snapshot."""
    root = Path(vault_root)
    now = _now_utc()

    try:
        all_caps = load_all_capabilities(root)
    except CapabilityError as exc:
        raise ValueError(f"Cannot load runtime capabilities: {exc}") from exc

    selected_caps = _select_capabilities(all_caps, runtime_filter)
    config = _load_operator_config(root)
    provider_statuses = list_provider_status()
    provider_status_by_id = _provider_lookup(provider_statuses)
    tasks = list_tasks(root)
    heartbeats = list_heartbeats(root)
    liveness = get_runtime_liveness(root)
    provider_ledger = summarize_provider_state_ledger(
        root,
        runtime_filter=runtime_filter,
        now=now,
    )
    adapter_health_rollup = build_adapter_health_rollup(root)
    queue = _queue_summary(
        tasks,
        selected_caps,
        now=now,
        stuck_after_seconds=max(0, int(stuck_after_seconds)),
    )

    runtime_rows = [
        _runtime_status(
            caps=caps,
            vault_root=root,
            provider_status_by_id=provider_status_by_id,
            liveness=liveness,
            heartbeats=heartbeats,
            queue_by_runtime=queue["by_runtime"],
            probe_health=probe_health,
            health_timeout_seconds=health_timeout_seconds,
            provider_ledger=provider_ledger,
        )
        for caps in selected_caps
    ]
    active_runtime = _select_active_runtime(
        config=config,
        all_caps=all_caps,
        liveness=liveness,
    )
    active_binding = _active_runtime_model_binding(active_runtime, runtime_rows)
    warnings = _warnings(runtime_rows)
    combined_warnings = warnings + list(adapter_health_rollup.get("warnings") or [])
    rate_limit_state = provider_ledger["rate_limit_state"]
    cooldown_state = provider_ledger["cooldown_state"]
    recovery_to_primary = provider_ledger["recovery_to_primary"]
    readiness = _readiness_summary(
        provider_statuses=provider_statuses,
        runtime_rows=runtime_rows,
        queue=queue,
        rate_limit_state=rate_limit_state,
        cooldown_state=cooldown_state,
        adapter_health_rollup=adapter_health_rollup,
        warnings=combined_warnings,
    )
    operator_default_provider = _select_operator_default_provider(
        config=config,
        provider_statuses=provider_statuses,
    )

    return {
        "schema_version": 1,
        "status_version": STATUS_VERSION,
        "generated_at": now.isoformat(),
        "vault_root": str(root),
        "runtime_filter": runtime_filter or "all",
        "active_runtime": active_runtime,
        "operator_default_provider": operator_default_provider,
        "active_runtime_model_provider": active_binding,
        "provider_setup_status": provider_statuses,
        "queues": queue,
        "provider_state_ledger": {
            "ledger_path": provider_ledger.get("ledger_path"),
            "ledger_exists": provider_ledger.get("ledger_exists"),
            "event_count": provider_ledger.get("event_count"),
            "latest_event": provider_ledger.get("latest_event"),
        },
        "rate_limit_state": rate_limit_state,
        "cooldown_state": cooldown_state,
        "recovery_to_primary": recovery_to_primary,
        "adapter_health_rollup": adapter_health_rollup,
        "runtimes": runtime_rows,
        "warnings": combined_warnings,
        "readiness_summary": readiness,
        "operator_summary": _operator_summary(
            readiness=readiness,
            active_runtime=active_runtime,
            operator_default_provider=operator_default_provider,
            active_binding=active_binding,
            queue=queue,
            rate_limit_state=rate_limit_state,
            cooldown_state=cooldown_state,
            recovery_to_primary=recovery_to_primary,
            provider_ledger=provider_ledger,
            adapter_health_rollup=adapter_health_rollup,
            warnings=combined_warnings,
        ),
        "boundary": {
            "read_only": True,
            "controls_provider_switching": False,
            "controls_cooldowns": False,
            "controls_recovery_to_primary": False,
        },
    }


def format_runtime_provider_status(payload: dict[str, Any]) -> str:
    """Render a compact human-readable status report."""
    lines: list[str] = ["ChaseOS Runtime Provider Status"]
    operator = payload.get("operator_summary") or {}
    if operator:
        lines.append(f"  operator_status: {operator.get('status')}")
        lines.append(f"  headline: {operator.get('headline')}")
    readiness = payload.get("readiness_summary") or {}
    lines.append(
        "  readiness: "
        f"{readiness.get('posture') or '(unknown)'} "
        f"(reasons={','.join(readiness.get('degradation_reasons') or []) or 'none'})"
    )
    active = payload.get("active_runtime") or {}
    lines.append(f"  active_runtime: {active.get('runtime_id') or '(none)'} [{active.get('status')}]")
    default_provider = payload.get("operator_default_provider") or {}
    lines.append(
        "  operator_default_provider: "
        f"{default_provider.get('provider_id') or '(none)'} "
        f"(source={default_provider.get('source')})"
    )
    active_binding = payload.get("active_runtime_model_provider") or {}
    primary = active_binding.get("primary") or {}
    fallback = active_binding.get("fallback") or {}
    lines.append(
        "  active_primary: "
        f"{primary.get('provider_id') or '(none)'}/{primary.get('model_id') or '(none)'}"
    )
    lines.append(
        "  active_fallback: "
        f"{fallback.get('provider_id') or '(none)'}/{fallback.get('model_id') or '(none)'}"
    )

    attention_items = operator.get("attention_items") or []
    if attention_items:
        lines.append("")
        lines.append("Operator Attention")
        for item in attention_items[:6]:
            lines.append(
                f"  - [{item.get('severity')}] {item.get('code')}: {item.get('summary')}"
            )
    recommended_actions = operator.get("recommended_actions") or []
    if recommended_actions:
        lines.append("")
        lines.append("Recommended Actions")
        for action in recommended_actions[:6]:
            lines.append(f"  - {action}")

    queues = payload.get("queues") or {}
    lines.append("")
    lines.append("Queue")
    lines.append(f"  queued: {queues.get('queued_count', 0)}")
    lines.append(f"  active: {queues.get('active_count', 0)}")
    lines.append(f"  stuck: {queues.get('stuck_count', 0)}")
    lines.append(f"  no_chunk: {queues.get('no_chunk_count', 0)}")

    adapter_rollup = payload.get("adapter_health_rollup") or {}
    adapter_totals = adapter_rollup.get("totals") or {}
    lines.append("")
    lines.append("Adjacent Adapter Health")
    lines.append(
        "  status: "
        f"{adapter_rollup.get('status') or '(unknown)'} "
        f"events={adapter_totals.get('event_count', 0)} "
        f"failed={adapter_totals.get('failed_count', 0)}"
    )
    for lane_key, lane in sorted((adapter_rollup.get("lanes") or {}).items()):
        summary = lane.get("summary") or {}
        lines.append(
            f"  {lane_key}: status={lane.get('status')} "
            f"events={summary.get('event_count', 0)} exists={summary.get('exists')}"
        )

    lines.append("")
    lines.append("Runtimes")
    for runtime in payload.get("runtimes", []):
        health = runtime.get("adapter_health") or {}
        model = (runtime.get("model_binding") or {}).get("primary") or {}
        fallback_count = (runtime.get("model_binding") or {}).get("fallback_count", 0)
        queue = runtime.get("queue") or {}
        lines.append(f"- {runtime.get('bus_name')}")
        lines.append(
            "  health: "
            f"heartbeat={health.get('heartbeat_health')} stale={health.get('is_stale')}"
        )
        if health.get("lifecycle_probe_checked"):
            probe = health.get("lifecycle_probe") or {}
            lines.append(f"  lifecycle_probe_healthy: {probe.get('healthy')}")
        lines.append(
            "  primary: "
            f"{model.get('provider_id') or '(unknown)'}/{model.get('model_id') or '(none)'}"
        )
        lines.append(f"  fallbacks: {fallback_count}")
        lines.append(
            "  queue: "
            f"queued={queue.get('queued_count', 0)} active={queue.get('active_count', 0)} "
            f"stuck={queue.get('stuck_count', 0)} no_chunk={queue.get('no_chunk_count', 0)}"
        )

    lines.append("")
    lines.append(f"rate_limit_state: {payload.get('rate_limit_state', {}).get('status')}")
    lines.append(f"cooldown_state: {payload.get('cooldown_state', {}).get('status')}")
    lines.append(f"recovery_to_primary: {payload.get('recovery_to_primary', {}).get('status')}")
    ledger = payload.get("provider_state_ledger") or {}
    lines.append(
        "provider_state_ledger: "
        f"events={ledger.get('event_count', 0)} exists={ledger.get('ledger_exists')}"
    )
    for warning in payload.get("warnings") or []:
        lines.append(f"warning: {warning}")
    return "\n".join(lines)
