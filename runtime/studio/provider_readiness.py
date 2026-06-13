"""Read-only Studio provider readiness model.

This module is a Studio-facing consumer of RPGL evidence. It intentionally reads
non-secret provider posture and marker/result metadata only; it does not call the
RPGL builders that append audit events, execute probes, or mutate provider state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import re
from pathlib import Path
from typing import Any

from runtime.providers.governance_layer import (
    LEGACY_DEFAULT_PRIMARY_MODEL,
    LOCAL_FALLBACK_SAFE_NUM_CTX,
    SCHEMA_VERSION,
)
from runtime.providers.state_ledger import provider_id_from_model_id


MODEL_VERSION = "studio.provider_readiness.v1"
SURFACE_ID = "studio_provider_readiness"

_TARGET_PROFILE_RELATIVE_PATH = Path("runtime/providers/provider_target_profile.json")
_QUEUE_RELATIVE_PATH = Path("runtime/providers/state/provider_queue.json")
_LIVE_PROBE_MARKER_RELATIVE_DIR = Path("runtime/providers/state/provider_live_probe_markers")
_LIVE_PROBE_RESULT_RELATIVE_DIR = Path("runtime/providers/state/provider_live_probe_results")
_LIVE_PROBE_APPROVAL_RELATIVE_DIR = Path("07_LOGS/Agent-Activity/_rpgl_provider_approvals")
_LIVE_PROBE_DECISION_RELATIVE_DIR = Path("07_LOGS/Agent-Activity/_rpgl_provider_live_probe_decisions")
_LIVE_PROBE_CONSUMER_RELATIVE_DIR = Path("07_LOGS/Agent-Activity/_rpgl_provider_live_probe_consumers")

_PROVIDER_ENV_REFS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "xai": "XAI_API_KEY",
    "perplexity": "PERPLEXITY_API_KEY",
    "local_oss": "OLLAMA_HOST",
}

_OPEN_RETRY_STATUSES = {"queued", "waiting_for_primary", "ready_for_retry", "needs_operator_approval"}
_REDACTED_PROVIDER_METADATA = "[redacted-sensitive-provider-metadata]"
_SECRET_LIKE_PATTERN = re.compile(
    r"(?i)(sk-[a-z0-9][a-z0-9._-]{8,}|[a-z0-9._-]{8,}[-_](?:secret|token|password|credential)[-_][a-z0-9._-]{4,})"
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _json_records(directory: Path) -> list[dict[str, Any]]:
    if not directory.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        payload = _read_json(path, {})
        if isinstance(payload, dict) and payload:
            item = dict(payload)
            item["record_ref"] = str(path)
            records.append(item)
    return records


def _env_present(env_ref: str | None) -> bool:
    if not env_ref:
        return False
    value = os.environ.get(env_ref)
    return value is not None and value != ""


def _provider_env_ref(provider_id: str | None) -> str | None:
    return _PROVIDER_ENV_REFS.get(str(provider_id or "").lower())


def _binding_label(provider_id: Any, model: Any) -> str:
    provider_text = str(provider_id or "unknown_provider")
    model_text = str(model or "unknown_model")
    return f"{provider_text} / {model_text}"


def _known_secret_values() -> tuple[str, ...]:
    values: list[str] = []
    for env_ref in _PROVIDER_ENV_REFS.values():
        value = os.environ.get(env_ref)
        if value and len(value) >= 8:
            values.append(value)
    return tuple(values)


def _redact_provider_metadata(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    if any(secret in value for secret in _known_secret_values()):
        return _REDACTED_PROVIDER_METADATA
    if _SECRET_LIKE_PATTERN.search(value):
        return _REDACTED_PROVIDER_METADATA
    return value


def _target_profile(vault: Path) -> dict[str, Any]:
    path = vault / _TARGET_PROFILE_RELATIVE_PATH
    raw = _read_json(path, {})
    exists = path.exists() and isinstance(raw, dict)
    default_primary_model = str(
        (raw.get("default_primary_model") if exists else None)
        or (raw.get("expected_primary_model") if exists else None)
        or LEGACY_DEFAULT_PRIMARY_MODEL
    )
    provider_id = provider_id_from_model_id(default_primary_model) or "openai"
    runtime_targets = raw.get("runtime_targets") if exists and isinstance(raw.get("runtime_targets"), dict) else {}
    fallback_raw = raw.get("local_fallback") if exists and isinstance(raw.get("local_fallback"), dict) else {}
    fallback_provider_id = str(fallback_raw.get("provider_id") or "local_oss")
    fallback_model = str(fallback_raw.get("model") or "phi4-mini:latest")
    fallback_enabled = bool(fallback_raw.get("enabled", False))
    fallback_num_ctx = int(fallback_raw.get("num_ctx") or LOCAL_FALLBACK_SAFE_NUM_CTX)

    return {
        "profile_ref": str(path),
        "profile_exists": exists,
        "profile_source": str(path) if exists else "legacy_default_expected_primary_model",
        "active_profile": {
            "provider_id": provider_id,
            "model": default_primary_model,
            "binding_label": _binding_label(provider_id, default_primary_model),
            "profile_source": str(path) if exists else "legacy_default_expected_primary_model",
            "runtime_target_count": len(runtime_targets),
            "is_legacy_compatibility_default": not exists and default_primary_model == LEGACY_DEFAULT_PRIMARY_MODEL,
        },
        "fallback_profile": {
            "provider_id": fallback_provider_id,
            "model": fallback_model,
            "binding_label": _binding_label(fallback_provider_id, fallback_model),
            "strength": str(fallback_raw.get("strength") or "weak"),
            "enabled": fallback_enabled,
            "authority": str(fallback_raw.get("authority") or "recovery_assistant_only"),
            "num_ctx": fallback_num_ctx,
            "safe_num_ctx": LOCAL_FALLBACK_SAFE_NUM_CTX,
            "context_limit_safe": fallback_num_ctx <= LOCAL_FALLBACK_SAFE_NUM_CTX,
        },
    }


def _queue_readiness(vault: Path) -> dict[str, Any]:
    payload = _read_json(vault / _QUEUE_RELATIVE_PATH, {})
    items = payload.get("items") if isinstance(payload, dict) and isinstance(payload.get("items"), list) else []
    open_items = [item for item in items if isinstance(item, dict) and item.get("retry_status") in _OPEN_RETRY_STATUSES]
    return {
        "queued_retry_count": len(open_items),
        "needs_operator_approval_count": len(
            [item for item in open_items if item.get("retry_status") == "needs_operator_approval"]
        ),
        "next_eligible_retry": next(
            (item.get("cooldown_until") for item in open_items if item.get("cooldown_until")),
            None,
        ),
        "items_visible_to_studio": [
            {
                "task_id": item.get("task_id"),
                "task_class": item.get("task_class"),
                "retry_status": item.get("retry_status"),
                "required_provider_strength": item.get("required_provider_strength"),
                "safe_next_step": item.get("safe_next_step"),
            }
            for item in open_items[:10]
        ],
    }


def _last_probe_marker(vault: Path) -> dict[str, Any] | None:
    markers = _json_records(vault / _LIVE_PROBE_MARKER_RELATIVE_DIR)
    if not markers:
        return None
    marker = sorted(markers, key=lambda item: str(item.get("created_at") or item.get("generated_at") or ""))[-1]
    return {
        "gate_approval_id": marker.get("gate_approval_id"),
        "target": _redact_provider_metadata(marker.get("target")),
        "marker_status": marker.get("marker_status") or marker.get("status"),
        "created_at": marker.get("created_at") or marker.get("generated_at"),
        "marker_ref": marker.get("record_ref"),
    }


def _last_probe_result(vault: Path) -> dict[str, Any] | None:
    results = _json_records(vault / _LIVE_PROBE_RESULT_RELATIVE_DIR)
    if not results:
        return None
    result = sorted(results, key=lambda item: str(item.get("created_at") or item.get("generated_at") or ""))[-1]
    outcome = result.get("probe_outcome") if isinstance(result.get("probe_outcome"), dict) else {}
    return {
        "gate_approval_id": result.get("gate_approval_id"),
        "target": _redact_provider_metadata(result.get("target")),
        "result_status": result.get("result_status"),
        "ok": bool(outcome.get("ok")),
        "error_type": _redact_provider_metadata(outcome.get("error_type")),
        "reason": _redact_provider_metadata(outcome.get("reason")),
        "live_network_call_attempted": bool(outcome.get("live_network_call_attempted")),
        "secret_value_read": bool(outcome.get("secret_value_read")),
        "result_ref": result.get("record_ref"),
    }


def _approval_chain_counts(vault: Path) -> dict[str, Any]:
    approvals = _json_records(vault / _LIVE_PROBE_APPROVAL_RELATIVE_DIR)
    decisions = _json_records(vault / _LIVE_PROBE_DECISION_RELATIVE_DIR)
    consumers = _json_records(vault / _LIVE_PROBE_CONSUMER_RELATIVE_DIR)
    markers = _json_records(vault / _LIVE_PROBE_MARKER_RELATIVE_DIR)
    return {
        "approval_request_count": len(approvals),
        "approved_decision_count": len(
            [
                item
                for item in decisions
                if item.get("decision") == "approved" or item.get("approval_decision") == "approved"
            ]
        ),
        "consumer_record_count": len(consumers),
        "marker_count": len(markers),
        "result_record_count": len(_json_records(vault / _LIVE_PROBE_RESULT_RELATIVE_DIR)),
        "approval_chain_complete_for_probe_attempt": bool(approvals and decisions and consumers and markers),
    }


def build_studio_provider_readiness(vault_root: str | Path) -> dict[str, Any]:
    """Build a non-mutating provider readiness payload for Studio Settings."""

    vault = Path(vault_root).resolve()
    target = _target_profile(vault)
    active = target["active_profile"]
    fallback = target["fallback_profile"]
    queue = _queue_readiness(vault)
    approval_chain = _approval_chain_counts(vault)
    last_marker = _last_probe_marker(vault)
    last_result = _last_probe_result(vault)

    primary_env_ref = _provider_env_ref(active.get("provider_id"))
    fallback_env_ref = _provider_env_ref(fallback.get("provider_id"))
    primary_env_present = _env_present(primary_env_ref)
    fallback_env_present = _env_present(fallback_env_ref) if fallback.get("enabled") else False

    blockers: list[str] = []
    if not primary_env_present:
        blockers.append("primary_provider_credential_or_environment_missing")
    if not approval_chain["approval_chain_complete_for_probe_attempt"]:
        blockers.append("live_probe_approval_decision_consumer_marker_chain_incomplete")
    if fallback.get("enabled") and not fallback_env_present:
        blockers.append("fallback_provider_environment_missing")
    if last_result and last_result.get("ok") is False:
        blockers.append("last_live_probe_result_failed")
    if fallback.get("context_limit_safe") is False:
        blockers.append("fallback_context_limit_above_safe_max")

    if last_result and last_result.get("ok") and not blockers:
        readiness_status = "verified_by_last_probe_result"
    elif blockers:
        readiness_status = "blocked"
    else:
        readiness_status = "ready_for_cli_guarded_live_probe"

    degraded_reason = "; ".join(blockers) if blockers else None

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "summary": {
            "readiness_status": readiness_status,
            "active_provider_id": active.get("provider_id"),
            "active_model": active.get("model"),
            "active_binding_label": active.get("binding_label"),
            "fallback_provider_id": fallback.get("provider_id"),
            "fallback_model": fallback.get("model"),
            "fallback_binding_label": fallback.get("binding_label"),
            "fallback_enabled": fallback.get("enabled"),
            "degraded": bool(blockers),
            "degraded_reason": degraded_reason,
            "last_probe_marker_present": last_marker is not None,
            "last_probe_result_status": (last_result or {}).get("result_status"),
            "queued_retry_count": queue["queued_retry_count"],
        },
        "active_profile": active,
        "fallback_profile": fallback,
        "credential_posture": {
            "primary_provider_env_ref": primary_env_ref,
            "primary_provider_env_present": primary_env_present,
            "fallback_provider_env_ref": fallback_env_ref,
            "fallback_provider_env_present": fallback_env_present,
            "secret_values_included": False,
            "raw_credentials_included": False,
            "raw_credential_values_displayed": False,
            "secret_reference_metadata_only": True,
        },
        "live_probe_readiness": {
            "status": readiness_status,
            "approval_gated": True,
            "studio_executes_live_probe": False,
            "cli_guarded_executor_route": "chaseos runtime provider live-probe-executor primary --gate-approval-id <id> --execute-live-probe --json",
            "live_smoke_execution_allowed_now": readiness_status == "ready_for_cli_guarded_live_probe",
            "blocked_reasons": blockers,
            "approval_chain": approval_chain,
            "last_probe_marker": last_marker,
            "last_probe_result": last_result,
        },
        "queue_readiness": queue,
        "authority": {
            "read_only": True,
            "writes_provider_config": False,
            "writes_target_profile": False,
            "writes_approval_artifacts": False,
            "writes_decisions": False,
            "writes_consumers": False,
            "writes_markers": False,
            "writes_results": False,
            "executes_live_probe": False,
            "provider_calls_allowed": False,
            "provider_switch_allowed": False,
            "secret_values_visible": False,
            "canonical_mutation_allowed": False,
        },
        "evidence_refs": {
            "target_profile_ref": target["profile_ref"],
            "queue_ref": str(vault / _QUEUE_RELATIVE_PATH),
            "approval_dir": str(vault / _LIVE_PROBE_APPROVAL_RELATIVE_DIR),
            "decision_dir": str(vault / _LIVE_PROBE_DECISION_RELATIVE_DIR),
            "consumer_dir": str(vault / _LIVE_PROBE_CONSUMER_RELATIVE_DIR),
            "marker_dir": str(vault / _LIVE_PROBE_MARKER_RELATIVE_DIR),
            "result_dir": str(vault / _LIVE_PROBE_RESULT_RELATIVE_DIR),
        },
        "denied_by_this_surface": [
            "credential_value_display",
            "provider_config_write",
            "provider_target_profile_write",
            "provider_switch",
            "approval_grant_or_decision",
            "approval_consumption",
            "live_provider_probe_execution",
            "provider_state_mutation",
            "queue_retry_or_drain",
            "canonical_writeback",
        ],
    }
