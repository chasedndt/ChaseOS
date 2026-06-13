"""Phase 11 operator companion direction packet.

This surface summarizes the current companion registry/status truth and previews
the operator decisions needed before any roster UI or selection executor work.
It does not choose for the operator, write companion-selection state, activate a
registry loader, consume approvals, dispatch runtimes, or call providers.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.phase11_multi_companion_registry_readiness import (
    build_phase11_multi_companion_registry_readiness,
)


MODEL_VERSION = "studio.phase11_operator_companion_direction.v1"
SURFACE_ID = "phase11_operator_companion_direction"
PASS_ID = "operator-companion-direction-before-roster-ui"
STATUS = "COMPLETE / READ-ONLY / VERIFIED / OPERATOR DIRECTION PACKET ONLY"
NEXT_RECOMMENDED_PASS_WHEN_UNANSWERED = "operator-answer-companion-direction-questions"
NEXT_RECOMMENDED_PASS_WHEN_READY = "phase11-companion-roster-ui-preview"

DECISION_FIELDS = [
    "companion_concept",
    "initial_roster",
    "naming_policy",
    "visual_style",
    "selection_scope",
    "effect_scope",
    "tone_level",
    "memory_scope",
    "switch_policy",
    "multi_companion_future",
]

DECISION_PROMPTS = {
    "companion_concept": {
        "prompt": "What are companions: runtime identities, AI personas, mascots, or mode/profile presets?",
        "recommended_default": "runtime_identity_with_personality_surface",
    },
    "initial_roster": {
        "prompt": "Should MVP start with Hermes/OpenClaw/Archon only, or add custom companions first?",
        "recommended_default": "start_with_hermes_openclaw_archon",
    },
    "naming_policy": {
        "prompt": "Keep Hermes/OpenClaw/Archon, rename them, or add aliases?",
        "recommended_default": "keep_runtime_names_and_allow_aliases_later",
    },
    "visual_style": {
        "prompt": "Use abstract runtime marks, generated avatars, initials, or character portraits?",
        "recommended_default": "abstract_runtime_marks_until_brand_pack_exists",
    },
    "selection_scope": {
        "prompt": "Should one active companion be global, per Chat session, or per surface?",
        "recommended_default": "per_chat_session",
    },
    "effect_scope": {
        "prompt": "Does selection change only tone/status, or also routing after separate approval?",
        "recommended_default": "tone_and_status_only_until_separate_routing_approval",
    },
    "tone_level": {
        "prompt": "Should companions be subtle status layer, conversational personality, or strong character presence?",
        "recommended_default": "conversational_personality_with_governance_boundaries",
    },
    "memory_scope": {
        "prompt": "Should companions have their own remembered preferences later?",
        "recommended_default": "separate_governed_memory_namespace_with_future_approval_executor",
    },
    "switch_policy": {
        "prompt": "Can the operator switch instantly after approval, or should every switch queue visible approval?",
        "recommended_default": "approval_gated_target_write_with_readonly_preview",
    },
    "multi_companion_future": {
        "prompt": "Do you want several companions responding together, or a roster with one active companion?",
        "recommended_default": "roster_with_one_active_companion_first",
    },
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _clean_decisions(operator_decisions: dict[str, Any] | None) -> dict[str, str]:
    source = operator_decisions or {}
    return {
        field: str(source.get(field) or "").strip()
        for field in DECISION_FIELDS
    }


def build_phase11_operator_companion_direction(
    vault_root: str | Path,
    *,
    operator_decisions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a read-only operator direction packet for companion planning."""

    vault = Path(vault_root).resolve()
    registry = build_phase11_multi_companion_registry_readiness(vault)
    registry_summary = registry.get("summary") or {}
    registry_cards = ((registry.get("registry") or {}).get("companions") or [])
    companion_options = [
        {
            "runtime_id": str(item.get("runtime_id") or ""),
            "companion_id": str(item.get("companion_id") or ""),
            "display_name": str(item.get("display_name") or ""),
            "status": str(item.get("status") or ""),
            "can_be_selected_after_governed_executor": bool(item.get("can_be_selected")),
            "supported_surfaces": list(item.get("supported_surfaces") or []),
        }
        for item in registry_cards
    ]
    decisions = _clean_decisions(operator_decisions)
    unanswered = [field for field, value in decisions.items() if not value]
    answered = [field for field, value in decisions.items() if value]
    ready_for_roster_ui = not unanswered and registry.get("ok") is True
    next_pass = NEXT_RECOMMENDED_PASS_WHEN_READY if ready_for_roster_ui else NEXT_RECOMMENDED_PASS_WHEN_UNANSWERED
    digest_material = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "registry_readiness_digest": ((registry.get("digest_proof") or {}).get("readiness_digest")),
        "answered_fields": answered,
        "unanswered_fields": unanswered,
        "companion_runtime_ids": [item["runtime_id"] for item in companion_options],
        "ready_for_roster_ui": ready_for_roster_ui,
    }

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "approval_gated": False,
        "summary": {
            "registry_readiness_ok": registry.get("ok") is True,
            "registry_companion_count": registry_summary.get("registry_companion_count"),
            "builtin_companion_count": registry_summary.get("builtin_companion_count"),
            "operator_decision_field_count": len(DECISION_FIELDS),
            "operator_decision_answered_count": len(answered),
            "operator_decision_unanswered_count": len(unanswered),
            "operator_direction_captured": ready_for_roster_ui,
            "ready_for_roster_ui_preview": ready_for_roster_ui,
            "roster_ui_built": False,
            "selection_target_written": False,
            "approval_consumed": False,
            "provider_call_performed": False,
            "runtime_dispatched": False,
            "agent_bus_task_written": False,
            "canonical_state_mutated": False,
            "next_recommended_pass": next_pass,
        },
        "companion_options": companion_options,
        "decision_questions": [
            {
                "field": field,
                "prompt": DECISION_PROMPTS[field]["prompt"],
                "recommended_default": DECISION_PROMPTS[field]["recommended_default"],
                "operator_answer": decisions[field],
                "answered": bool(decisions[field]),
            }
            for field in DECISION_FIELDS
        ],
        "operator_decisions": decisions,
        "unanswered_decisions": unanswered,
        "recommended_defaults": {
            field: DECISION_PROMPTS[field]["recommended_default"]
            for field in DECISION_FIELDS
        },
        "registry_readiness": {
            "surface": registry.get("surface"),
            "ok": registry.get("ok"),
            "status": registry.get("status"),
            "summary": registry_summary,
            "warnings": registry.get("warnings") or [],
            "blocked_reasons": registry.get("blocked_reasons") or [],
        },
        "digest_proof": {
            "direction_digest": _sha256_text(_canonical_json(digest_material)),
            "digest_material": digest_material,
        },
        "readiness": {
            "operator_companion_direction_packet_ready": True,
            "operator_direction_captured": ready_for_roster_ui,
            "ready_for_roster_ui_preview": ready_for_roster_ui,
            "registry_readiness_required": True,
            "registry_readiness_ok": registry.get("ok") is True,
            "roster_ui_blocked_until_direction": not ready_for_roster_ui,
            "selection_target_write_blocked": True,
            "approval_consumption_blocked": True,
            "provider_calls_blocked": True,
            "runtime_dispatch_blocked": True,
            "agent_bus_task_write_blocked": True,
            "canonical_mutation_blocked": True,
            "next_recommended_pass": next_pass,
        },
        "authority": {
            "read_only": True,
            "operator_decision_write_allowed": False,
            "registry_loader_activated": False,
            "companion_roster_ui_mutation_allowed": False,
            "approval_consumption_allowed": False,
            "approval_execution_allowed": False,
            "companion_selection_write_allowed": False,
            "runtime_control_allowed": False,
            "runtime_dispatch_allowed": False,
            "identity_ledger_mutation_allowed": False,
            "role_card_mutation_allowed": False,
            "profile_write_allowed": False,
            "provider_calls_allowed": False,
            "agent_bus_task_write_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "denied_by_this_surface": [
            "operator_decision_write",
            "registry_runtime_loader_activation",
            "companion_roster_ui_mutation",
            "approval_consumption",
            "approval_execution",
            "companion_selection_target_write",
            "runtime_control",
            "runtime_dispatch",
            "identity_ledger_mutation",
            "role_card_mutation",
            "profile_write",
            "provider_api_call",
            "agent_bus_task_write",
            "canonical_writeback",
        ],
        "blocked_reasons": [] if registry.get("ok") else list(registry.get("blocked_reasons") or []),
        "warnings": list(registry.get("warnings") or []),
    }


def format_phase11_operator_companion_direction(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "Phase 11 Operator Companion Direction Packet",
        f"Status: {payload.get('status')}",
        f"Companion options: {summary.get('registry_companion_count')}",
        f"Answered decisions: {summary.get('operator_decision_answered_count')}/{summary.get('operator_decision_field_count')}",
        f"Ready for roster UI preview: {summary.get('ready_for_roster_ui_preview')}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
        "Unanswered decisions:",
    ]
    unanswered = payload.get("unanswered_decisions") or []
    if unanswered:
        for field in unanswered:
            prompt = DECISION_PROMPTS.get(field, {}).get("prompt", field)
            default = DECISION_PROMPTS.get(field, {}).get("recommended_default", "")
            lines.append(f"- {field}: {prompt} Recommended default: {default}")
    else:
        lines.append("- none")
    lines.append(
        "Boundary: read-only direction packet only; no roster UI, no selection target write, "
        "no approval consumption/execution, no provider/runtime/Agent Bus/canonical mutation."
    )
    return "\n".join(lines)
