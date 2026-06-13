"""Read-only Studio Runtime Brain dashboard contract.

This contract turns the Pulse memory/runtime readiness packet into a
Studio-facing Runtime Brain dashboard model. It remains display-only: no memory
application, Runtime Brain update, permission expansion, schedule activation, or
canonical writeback is performed here.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.memory.inspector import get_runtime_memory
from runtime.pulse.memory_runtime_readiness import build_pulse_memory_runtime_readiness


_SURFACE = "studio_runtime_brain_dashboard_contract"
_STATUS_READY = "runtime_brain_dashboard_contract_ready"
_STATUS_PARTIAL = "runtime_brain_dashboard_contract_partial"
_STATUS_EMPTY = "runtime_brain_dashboard_contract_empty"
_STATUS_BLOCKED = "runtime_brain_dashboard_contract_blocked"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _summaries(items: list[Any], key: str = "summary", limit: int = 5) -> list[str]:
    summaries: list[str] = []
    for item in items:
        if isinstance(item, str):
            summaries.append(item)
        elif isinstance(item, dict):
            text = item.get(key) or item.get("description") or item.get("notes") or item.get("id")
            if text:
                summaries.append(str(text))
        if len(summaries) >= limit:
            break
    return summaries


def _repair_counts(repair_memory: dict[str, Any]) -> dict[str, int]:
    return {
        "repair_pattern_count": len(_as_list(repair_memory.get("repair_patterns"))),
        "incident_candidate_count": len(_as_list(repair_memory.get("incident_candidates"))),
    }


def _scorecard_summary(scorecard: dict[str, Any]) -> dict[str, Any]:
    stats = scorecard.get("aggregate_stats") or {}
    return {
        "total_executions": int(stats.get("total_executions") or 0),
        "success_count": int(stats.get("success_count") or 0),
        "escalated_count": int(stats.get("escalated_count") or 0),
        "failed_count": int(stats.get("failed_count") or 0),
        "reliability_rate": stats.get("reliability_rate"),
        "overreach_rate": stats.get("overreach_rate"),
        "compliance_rate": stats.get("compliance_rate"),
        "last_updated": scorecard.get("last_updated"),
    }


def _runtime_action_hints(card: dict[str, Any], bundle: dict[str, Any]) -> list[dict[str, Any]]:
    hints: list[dict[str, Any]] = []
    for family in card.get("missing_families") or []:
        hints.append(
            {
                "action_id": f"inspect-missing-{card.get('runtime_id')}-{family}",
                "label": f"Inspect missing {family}",
                "action_type": "inspect_missing_memory_family",
                "requires_operator_review": True,
                "execution_allowed": False,
                "writes_memory": False,
            }
        )
    repair = bundle.get("layer_c", {}).get("repair_memory") or {}
    if _repair_counts(repair).get("incident_candidate_count", 0):
        hints.append(
            {
                "action_id": f"review-repair-candidates-{card.get('runtime_id')}",
                "label": "Review repair candidates",
                "action_type": "review_execution_repair_memory",
                "requires_operator_review": True,
                "execution_allowed": False,
                "writes_memory": False,
            }
        )
    identity = bundle.get("layer_c", {}).get("identity_ledger") or {}
    if _as_list(identity.get("drift_signals")):
        hints.append(
            {
                "action_id": f"inspect-drift-{card.get('runtime_id')}",
                "label": "Inspect drift signals",
                "action_type": "inspect_runtime_drift",
                "requires_operator_review": False,
                "execution_allowed": False,
                "writes_memory": False,
            }
        )
    return hints


def _runtime_dashboard_card(
    vault: Path,
    readiness_card: dict[str, Any],
) -> dict[str, Any]:
    runtime_id = str(readiness_card.get("runtime_id") or "")
    bundle = get_runtime_memory(runtime_id, vault)
    layer_c = bundle.get("layer_c") or {}
    profile = layer_c.get("profile") or {}
    identity = layer_c.get("identity_ledger") or {}
    nav_map = layer_c.get("navigation") or {}
    repair = layer_c.get("repair_memory") or {}
    scorecard = layer_c.get("scorecard") or {}
    behavioral = profile.get("behavioral_profile") or {}
    identity_summary = identity.get("identity_summary") or {}

    return {
        "runtime_id": runtime_id,
        "status": readiness_card.get("status"),
        "present_families": readiness_card.get("present_families") or [],
        "missing_families": readiness_card.get("missing_families") or [],
        "source_refs": readiness_card.get("source_refs") or [],
        "profile": {
            "status": profile.get("status"),
            "primary_role": behavioral.get("primary_role"),
            "strengths": _summaries(_as_list(behavioral.get("strengths")), limit=6),
            "known_weaknesses": _summaries(
                _as_list(behavioral.get("known_failure_modes")),
                key="description",
                limit=6,
            ),
            "routing_guidance": _summaries(_as_list(behavioral.get("routing_guidance")), limit=6),
            "confidence_signals": _summaries(_as_list(behavioral.get("confidence_signals")), limit=6),
        },
        "identity_ledger": {
            "status": identity.get("status"),
            "current_actor_posture": identity_summary.get("current_actor_posture"),
            "tendency_count": len(_as_list(identity.get("behavioral_tendencies"))),
            "drift_signal_count": len(_as_list(identity.get("drift_signals"))),
            "drift_signals": _summaries(_as_list(identity.get("drift_signals")), limit=4),
            "governance_boundary": identity.get("governance_boundary"),
        },
        "runtime_navigation": {
            "status": nav_map.get("status"),
            "preferred_route_count": len(_as_list(nav_map.get("preferred_read_routes"))),
            "trusted_zone_count": len(_as_list(nav_map.get("trusted_zones"))),
            "safe_write_path_count": len(_as_list(nav_map.get("safe_write_paths"))),
            "risk_zone_count": len(_as_list(nav_map.get("risk_zones"))),
            "escalation_point_count": len(_as_list(nav_map.get("escalation_points"))),
            "successful_route_pattern_count": len(_as_list(nav_map.get("successful_route_patterns"))),
        },
        "execution_repair_memory": {
            "status": repair.get("status"),
            **_repair_counts(repair),
            "governance_boundary": repair.get("governance_boundary"),
        },
        "scorecard": _scorecard_summary(scorecard),
        "action_hints": _runtime_action_hints(readiness_card, bundle),
        "authority": {
            "advisory_only": True,
            "identity_ledger_grants_authority": False,
            "runtime_navigation_updates_allowed": False,
            "repair_memory_apply_allowed": False,
            "permission_expansion_allowed": False,
            "self_upgrade_active": False,
        },
    }


def _filter_runtime_cards(cards: list[dict[str, Any]], runtime_id: str | None) -> list[dict[str, Any]]:
    if not runtime_id or runtime_id == "all":
        return cards
    return [card for card in cards if str(card.get("runtime_id")) == runtime_id]


def _dashboard_status(readiness_status: str, card_count: int) -> str:
    if readiness_status == "blocked":
        return _STATUS_BLOCKED
    if card_count == 0:
        return _STATUS_EMPTY
    if readiness_status == "ready":
        return _STATUS_READY
    return _STATUS_PARTIAL


def build_runtime_brain_dashboard_contract(
    vault_root: str | Path,
    *,
    runtime_id: str | None = None,
) -> dict[str, Any]:
    """Return the Studio-facing read-only Runtime Brain dashboard contract."""

    vault = _vault_path(vault_root)
    readiness = build_pulse_memory_runtime_readiness(vault)
    readiness_payload = readiness.to_dict()
    selected_cards = _filter_runtime_cards(
        list(readiness_payload.get("runtime_cards") or []),
        runtime_id,
    )
    cards = [_runtime_dashboard_card(vault, card) for card in selected_cards]
    missing_family_count = sum(len(card.get("missing_families") or []) for card in cards)
    drift_signal_count = sum(
        int((card.get("identity_ledger") or {}).get("drift_signal_count") or 0)
        for card in cards
    )
    repair_candidate_count = sum(
        int((card.get("execution_repair_memory") or {}).get("incident_candidate_count") or 0)
        for card in cards
    )
    action_hint_count = sum(len(card.get("action_hints") or []) for card in cards)

    return {
        "ok": readiness_payload.get("validation_error_count", 0) == 0,
        "surface": _SURFACE,
        "title": "Studio Runtime Brain Dashboard Contract",
        "status": _dashboard_status(str(readiness_payload.get("readiness_status")), len(cards)),
        "generated_at_utc": _utc_now_iso(),
        "vault_root": str(vault),
        "runtime_filter": runtime_id or "all",
        "source_surface": "runtime.pulse.memory_runtime_readiness",
        "pulse_memory_runtime_readiness": {
            "readiness_status": readiness_payload.get("readiness_status"),
            "memory_posture": readiness_payload.get("memory_posture"),
            "lane_count": readiness_payload.get("lane_count"),
            "runtime_count": readiness_payload.get("runtime_count"),
            "family_counts": readiness_payload.get("family_counts") or {},
            "feedback_rule_count": readiness_payload.get("feedback_rule_count"),
            "personal_map_candidate_count": readiness_payload.get("personal_map_candidate_count"),
            "execution_repair_candidate_count": readiness_payload.get("execution_repair_candidate_count"),
            "validation_error_count": readiness_payload.get("validation_error_count"),
        },
        "metrics": {
            "runtime_card_count": len(cards),
            "ready_runtime_count": sum(1 for card in cards if card.get("status") == "ready"),
            "partial_runtime_count": sum(1 for card in cards if card.get("status") == "partial"),
            "missing_family_count": missing_family_count,
            "drift_signal_count": drift_signal_count,
            "repair_incident_candidate_count": repair_candidate_count,
            "action_hint_count": action_hint_count,
        },
        "cards": cards,
        "views": [
            {
                "id": "runtime_brain_overview",
                "title": "Runtime Brain Overview",
                "status": "contract-ready",
                "source": "Pulse memory/runtime readiness",
            },
            {
                "id": "runtime_identity_ledger",
                "title": "Agent Identity Ledger",
                "status": "read-only-visible",
                "source": "runtime/memory/adapters/*/identity-ledger.json",
            },
            {
                "id": "runtime_navigation_map",
                "title": "Runtime Navigation Map",
                "status": "read-only-visible",
                "source": "runtime/memory/nav/*/nav-map.json",
            },
            {
                "id": "execution_repair_memory",
                "title": "Execution Repair Memory",
                "status": "read-only-visible",
                "source": "runtime/memory/repair/*.json",
            },
            {
                "id": "scorecard",
                "title": "Runtime Scorecard",
                "status": "read-only-visible",
                "source": "runtime/memory/scorecards/*.json",
            },
        ],
        "authority": {
            "read_only": True,
            "local_only": True,
            "writes_vault": False,
            "mutates_memory": False,
            "applies_feedback_rules": False,
            "applies_personal_map_candidates": False,
            "applies_execution_repair_candidates": False,
            "updates_runtime_brains": False,
            "updates_runtime_navigation_maps": False,
            "updates_agent_identity_ledgers": False,
            "grants_permissions": False,
            "self_upgrade_active": False,
            "agent_bus_task_write_allowed": False,
            "runtime_dispatch_allowed": False,
            "provider_or_connector_call_allowed": False,
            "schedule_activation_allowed": False,
            "canonical_writeback_allowed": False,
            "second_datastore_created": False,
            "rd_workbook_update_allowed": False,
        },
        "blocked_effects": [
            "runtime_brain_update",
            "runtime_navigation_map_update",
            "agent_identity_ledger_update",
            "repair_memory_application",
            "feedback_rule_application",
            "personal_map_mutation",
            "permission_expansion",
            "agent_bus_task_write",
            "runtime_dispatch",
            "schedule_activation",
            "provider_or_connector_call",
            "canonical_writeback",
            "second_datastore_write",
        ],
        "next_recommended_pass": "chaseos-pulse-final-product-readiness-audit",
    }
