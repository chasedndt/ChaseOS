"""Read-only Phase 11 provider routing consumer contract.

This contract tells future Phase 11 chat/model-routing consumers which RPGL and
Studio readiness fields must be inspected before any provider route is allowed.
It is not a router and it never calls providers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.providers.governance_layer import (
    ALL_TASK_CLASSES,
    AUTHORITY_MATRIX,
    HIGH_AUTHORITY_TASK_CLASSES,
    MEDIUM_TASK_CLASSES,
    WEAK_SAFE_TASK_CLASSES,
    normalize_task_class,
)
from runtime.studio.provider_readiness import build_studio_provider_readiness


MODEL_VERSION = "provider.routing_consumer_contract.v1"
SURFACE_ID = "provider_routing_consumer_contract"

PHASE11_INTENT_TO_TASK_CLASS = {
    "chat-answer": "read_only_analysis",
    "model-chat": "read_only_analysis",
    "dashboard-query": "provider_status_summary",
    "runtime-status": "provider_status_summary",
    "research-capture": "read_only_analysis",
    "runtime-task": "runtime_config_change",
    "browser-task": "deployment_action",
    "code-task": "repo_development",
    "memory-save": "canonical_doc_write",
    "approval-action": "provider_status_summary",
}

ROUTING_REQUIRED_EVIDENCE = [
    "active_profile",
    "fallback_profile",
    "credential_posture",
    "live_probe_readiness.approval_chain",
    "live_probe_readiness.last_probe_marker",
    "live_probe_readiness.last_probe_result",
    "queue_readiness.queued_retry_count",
    "authority.provider_calls_allowed_false_for_contract",
]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normal_task_class(phase11_intent: str | None, task_class: str | None) -> str:
    if task_class:
        return normalize_task_class(task_class)
    mapped = PHASE11_INTENT_TO_TASK_CLASS.get(str(phase11_intent or "").strip(), "read_only_analysis")
    return normalize_task_class(mapped)


def _task_family(task_class: str) -> str:
    if task_class in HIGH_AUTHORITY_TASK_CLASSES:
        return "high_authority"
    if task_class in MEDIUM_TASK_CLASSES:
        return "medium"
    if task_class in WEAK_SAFE_TASK_CLASSES:
        return "weak_safe"
    return "unknown"


def _strength_allowed(task_class: str, strength: str) -> bool:
    return AUTHORITY_MATRIX.get(task_class, {}).get(strength, "denied").startswith("allowed")


def _required_strength(task_class: str) -> str:
    family = _task_family(task_class)
    if family == "high_authority":
        return "strong"
    if family == "medium":
        return "medium_or_strong"
    if family == "weak_safe":
        return "weak_or_better"
    return "strong"


def _candidate_rows(readiness: dict[str, Any], task_class: str) -> list[dict[str, Any]]:
    active = readiness.get("active_profile") or {}
    fallback = readiness.get("fallback_profile") or {}
    credential = readiness.get("credential_posture") or {}
    live_probe = readiness.get("live_probe_readiness") or {}
    active_strength = "strong"
    fallback_strength = str(fallback.get("strength") or "weak")

    active_blockers: list[str] = []
    if not credential.get("primary_provider_env_present"):
        active_blockers.append("primary_provider_credential_or_environment_missing")
    if readiness.get("summary", {}).get("readiness_status") != "verified_by_last_probe_result":
        active_blockers.append("provider_live_probe_not_verified_for_routing")

    fallback_blockers: list[str] = []
    if not fallback.get("enabled"):
        fallback_blockers.append("fallback_profile_disabled")
    if fallback.get("enabled") and not credential.get("fallback_provider_env_present"):
        fallback_blockers.append("fallback_provider_environment_missing")
    if not _strength_allowed(task_class, fallback_strength):
        fallback_blockers.append("fallback_strength_not_allowed_for_task_class")

    return [
        {
            "role": "primary",
            "provider_id": active.get("provider_id"),
            "model": active.get("model"),
            "strength": active_strength,
            "allowed_for_task_class": _strength_allowed(task_class, active_strength),
            "credential_or_environment_present": bool(credential.get("primary_provider_env_present")),
            "live_probe_verified": bool((live_probe.get("last_probe_result") or {}).get("ok")),
            "route_ready": not active_blockers and _strength_allowed(task_class, active_strength),
            "blocked_reasons": active_blockers,
        },
        {
            "role": "fallback",
            "provider_id": fallback.get("provider_id"),
            "model": fallback.get("model"),
            "strength": fallback_strength,
            "allowed_for_task_class": _strength_allowed(task_class, fallback_strength),
            "credential_or_environment_present": bool(credential.get("fallback_provider_env_present")),
            "live_probe_verified": False,
            "route_ready": not fallback_blockers,
            "blocked_reasons": fallback_blockers,
        },
    ]


def build_provider_routing_consumer_contract(
    vault_root: str | Path,
    *,
    phase11_intent: str = "model-chat",
    task_class: str | None = None,
    requested_provider_id: str | None = None,
    requested_model: str | None = None,
) -> dict[str, Any]:
    """Build the no-execution provider routing consumer contract."""

    vault = Path(vault_root).resolve()
    normalized_task_class = _normal_task_class(phase11_intent, task_class)
    provider_readiness = build_studio_provider_readiness(vault)
    candidates = _candidate_rows(provider_readiness, normalized_task_class)
    primary = next(item for item in candidates if item["role"] == "primary")

    blockers: list[str] = []
    if normalized_task_class not in ALL_TASK_CLASSES:
        blockers.append("unknown_task_class")
    if provider_readiness.get("summary", {}).get("readiness_status") != "verified_by_last_probe_result":
        blockers.append("provider_readiness_not_verified")
    if not primary["credential_or_environment_present"]:
        blockers.append("primary_provider_credential_or_environment_missing")
    if not primary["allowed_for_task_class"]:
        blockers.append("primary_strength_not_allowed_for_task_class")
    if requested_provider_id and requested_provider_id != primary.get("provider_id"):
        blockers.append("requested_provider_does_not_match_active_profile")
    if requested_model and requested_model != primary.get("model"):
        blockers.append("requested_model_does_not_match_active_profile")

    routing_status = "route_contract_satisfied" if not blockers else "blocked"
    selected_candidate = primary if routing_status == "route_contract_satisfied" else None

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "phase11_intent": phase11_intent,
        "task_class": normalized_task_class,
        "task_family": _task_family(normalized_task_class),
        "required_provider_strength": _required_strength(normalized_task_class),
        "requested_provider_id": requested_provider_id,
        "requested_model": requested_model,
        "routing_status": routing_status,
        "route_execution_allowed": False,
        "selected_candidate_preview": selected_candidate,
        "candidate_routes": candidates,
        "blocked_reasons": list(dict.fromkeys(blockers)),
        "required_evidence": ROUTING_REQUIRED_EVIDENCE,
        "provider_readiness_summary": provider_readiness.get("summary") or {},
        "provider_readiness_ref": {
            "surface": provider_readiness.get("surface"),
            "model_version": provider_readiness.get("model_version"),
            "readiness_status": (provider_readiness.get("summary") or {}).get("readiness_status"),
        },
        "consumer_contract": {
            "may_display_provider_options": True,
            "may_display_credential_status": True,
            "may_display_degraded_reason": True,
            "may_display_fallback_state": True,
            "may_execute_provider_call": False,
            "must_use_python_bridge_not_js": True,
            "must_attribute_model_outputs": True,
            "must_fail_closed_when_blocked": True,
            "must_not_read_secret_values": True,
            "must_not_switch_provider_directly": True,
            "must_not_mutate_provider_config": True,
        },
        "authority": {
            "read_only": True,
            "provider_calls_allowed": False,
            "credential_values_visible": False,
            "provider_switch_allowed": False,
            "writes_provider_config": False,
            "writes_target_profile": False,
            "writes_approval_artifacts": False,
            "writes_markers": False,
            "writes_results": False,
            "queue_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "denied_by_this_surface": [
            "provider_api_call",
            "direct_js_model_call",
            "credential_value_display",
            "provider_switch",
            "provider_config_write",
            "target_profile_write",
            "approval_decision_or_consumption",
            "live_probe_execution",
            "queue_retry_or_drain",
            "canonical_writeback",
        ],
        "next_action": (
            "phase11_router_may_consume_contract_without_executing_provider_call"
            if routing_status == "route_contract_satisfied"
            else "resolve_provider_readiness_before_phase11_live_routing"
        ),
    }


def format_provider_routing_consumer_contract(payload: dict[str, Any]) -> str:
    lines = [
        "Phase 11 Provider Routing Consumer Contract",
        f"- routing_status: {payload.get('routing_status')}",
        f"- phase11_intent: {payload.get('phase11_intent')}",
        f"- task_class: {payload.get('task_class')}",
        f"- required_provider_strength: {payload.get('required_provider_strength')}",
        f"- route_execution_allowed: {payload.get('route_execution_allowed')}",
        f"- provider_readiness_status: {(payload.get('provider_readiness_ref') or {}).get('readiness_status')}",
    ]
    for candidate in payload.get("candidate_routes") or []:
        lines.append(
            f"- {candidate.get('role')}: provider={candidate.get('provider_id')} "
            f"model={candidate.get('model')} ready={candidate.get('route_ready')}"
        )
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("blocked_reasons:")
        for reason in blockers:
            lines.append(f"- {reason}")
    lines.append(f"- next_action: {payload.get('next_action')}")
    return "\n".join(lines)
