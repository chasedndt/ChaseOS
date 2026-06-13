"""Phase 11 companion roster UI preview.

This surface builds the first read-only roster view after operator companion
direction is captured. It may render companion cards and future approval-preview
metadata, but it must not write selection state, consume approvals, route
execution, call providers, expand memory/tool access, or mutate canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.companion.policy import INITIAL_COMPANION_IDS
from runtime.companion.policy import SELECTION_TARGET_PATH as CORE_SELECTION_TARGET_PATH
from runtime.companion.roster import get_companion, get_companion_status_metadata, validate_roster
from runtime.studio.phase11_chat_companion_status import BUILTIN_COMPANIONS, build_phase11_chat_companion_status
from runtime.studio.phase11_multi_companion_registry_readiness import (
    DEFAULT_REGISTRY_PATH,
    PREFERRED_REGISTRY_PATH,
    build_phase11_multi_companion_registry_readiness,
)
from runtime.studio.phase11_operator_companion_direction_answers import (
    build_phase11_operator_companion_direction_answers,
)


MODEL_VERSION = "studio.phase11_companion_roster_ui_preview.v1"
SURFACE_ID = "phase11_companion_roster_ui_preview"
PASS_ID = "phase11-companion-roster-ui-preview"
STATUS = "COMPLETE / READ-ONLY / ROSTER UI PREVIEW / NO AUTHORITY EXPANSION"
NEXT_RECOMMENDED_PASS = "phase11-companion-memory-boundary-contract"
SELECTION_TARGET_PATH = CORE_SELECTION_TARGET_PATH.as_posix()

CARD_PRESETS: dict[str, dict[str, Any]] = {
    companion_id: {
        "runtime_mark": get_companion_status_metadata(companion_id)["visual_mark"],
        "mark_shape": get_companion_status_metadata(companion_id)["mark_shape"],
        "border_preset": get_companion_status_metadata(companion_id)["border_style"],
        "status_badge": get_companion_status_metadata(companion_id)["status_badge"],
        "animation_preset": get_companion_status_metadata(companion_id)["animation_preset"],
        "rarity": "built-in",
        "stats": get_companion_status_metadata(companion_id)["stats"],
        "personality": get_companion_status_metadata(companion_id)["style"],
    }
    for companion_id in INITIAL_COMPANION_IDS
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _load_json(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.is_file():
        return {}, [f"json_missing:{path}"]
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {}, [f"json_read_failed:{path}:{exc}"]


def _registry_payload(vault: Path) -> tuple[dict[str, Any], Path, list[str]]:
    preferred = vault / PREFERRED_REGISTRY_PATH
    path = preferred if preferred.is_file() else vault / DEFAULT_REGISTRY_PATH
    payload, warnings = _load_json(path)
    return payload, path, warnings


def _current_selection(vault: Path) -> tuple[dict[str, Any], list[str]]:
    path = vault / SELECTION_TARGET_PATH
    payload, warnings = _load_json(path)
    if not payload:
        return {
            "selection_file_present": False,
            "selected_runtime_id": "hermes",
            "previous_runtime_id": "",
            "selection_digest": "",
            "selection_source": "default_preview_when_selection_file_missing",
        }, warnings
    selected = str(payload.get("selected_runtime_id") or "").strip().lower()
    return {
        "selection_file_present": True,
        "selected_runtime_id": selected,
        "previous_runtime_id": str(payload.get("previous_runtime_id") or "").strip().lower(),
        "selection_digest": str(payload.get("selection_digest") or ""),
        "queue_write_digest": str(payload.get("queue_write_digest") or ""),
        "selection_source": SELECTION_TARGET_PATH,
    }, warnings


def _registry_companions(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    companions = registry.get("companions") if isinstance(registry, dict) else []
    result: dict[str, dict[str, Any]] = {}
    for item in companions if isinstance(companions, list) else []:
        if not isinstance(item, dict):
            continue
        runtime_id = str(item.get("runtime_id") or "").strip().lower()
        if runtime_id:
            result[runtime_id] = item
    return result


def _compact_stats(profile: dict[str, Any]) -> dict[str, int]:
    stats = profile.get("stats") if isinstance(profile.get("stats"), dict) else {}
    compact: dict[str, int] = {}
    for key, value in stats.items():
        if isinstance(value, dict):
            compact[str(key)] = int(value.get("value") or 0)
    return compact


def _build_card(
    *,
    runtime_id: str,
    registry_card: dict[str, Any],
    status_card: dict[str, Any],
    active_runtime_id: str,
) -> dict[str, Any]:
    core_profile = get_companion(runtime_id)
    preset = CARD_PRESETS.get(runtime_id, {})
    tone_tags = registry_card.get("tone_tags") if isinstance(registry_card.get("tone_tags"), list) else []
    selection = registry_card.get("selection") if isinstance(registry_card.get("selection"), dict) else {}
    core_profile_digest = _sha256_text(_canonical_json(core_profile))
    digest_material = {
        "runtime_id": runtime_id,
        "display_name": registry_card.get("display_name") or status_card.get("display_name"),
        "tone_tags": tone_tags,
        "preset": preset,
        "core_profile_digest": core_profile_digest,
        "active": runtime_id == active_runtime_id,
        "selection_target_path": SELECTION_TARGET_PATH,
    }
    return {
        "companion_id": registry_card.get("companion_id") or f"{runtime_id}-companion",
        "runtime_id": runtime_id,
        "display_name": registry_card.get("display_name") or status_card.get("display_name") or runtime_id.title(),
        "role": status_card.get("runtime_role") or BUILTIN_COMPANIONS.get(runtime_id, {}).get("role", ""),
        "tone_preset": tone_tags or [str(core_profile.get("personality_preset") or "")],
        "status": "active" if runtime_id == active_runtime_id else "inactive",
        "is_active": runtime_id == active_runtime_id,
        "can_preview_selection": selection.get("can_be_selected") is True,
        "selection_requires_approval": True,
        "selection_target_path": SELECTION_TARGET_PATH,
        "core_companion_package_used": True,
        "core_profile_digest": core_profile_digest,
        "abstract_visual": {
            "kind": "runtime_mark",
            "runtime_mark": core_profile.get("visual_mark", {}).get("token") or preset.get("runtime_mark", runtime_id[:1].upper()),
            "mark_shape": preset.get("mark_shape", "badge"),
            "border_preset": core_profile.get("border_style") or preset.get("border_preset", "neutral"),
            "status_badge": preset.get("status_badge", "companion"),
            "animation_preset": core_profile.get("animation_preset") or preset.get("animation_preset", "none"),
            "brand_pack_required_before_final_asset": True,
        },
        "descriptive_metadata": {
            "rarity": (core_profile.get("rarity") or {}).get("label") or preset.get("rarity", "built-in"),
            "stats": _compact_stats(core_profile),
            "stats_are_cosmetic": True,
            "personality": core_profile.get("short_description") or preset.get("personality") or status_card.get("style_hint") or "",
            "metadata_changes_capability": False,
        },
        "authority": {
            "routing_granted": False,
            "tool_access_granted": False,
            "memory_access_granted": False,
            "separate_memory_namespace_declared": True,
            "memory_write_authority_granted": False,
            "write_authority_granted": False,
            "provider_model_selection_granted": False,
            "permission_scope_granted": False,
            "protected_file_access_granted": False,
            "runtime_dispatch_granted": False,
            "agent_bus_task_write_granted": False,
            "canonical_mutation_granted": False,
        },
        "future_selection_preview": {
            "approval_preview_required": True,
            "approval_queue_write_required": True,
            "selection_write_requires_governed_executor": True,
            "approval_request_created": False,
            "selection_target_written": False,
        },
        "card_digest": _sha256_text(_canonical_json(digest_material)),
    }


def build_phase11_companion_roster_ui_preview(
    vault_root: str | Path,
    *,
    requested_runtime: str | None = None,
) -> dict[str, Any]:
    """Build the read-only companion roster UI preview payload."""

    vault = Path(vault_root).resolve()
    direction = build_phase11_operator_companion_direction_answers(vault)
    registry_readiness = build_phase11_multi_companion_registry_readiness(vault)
    core_roster_validation = validate_roster()
    registry, registry_path, registry_warnings = _registry_payload(vault)
    current_selection, selection_warnings = _current_selection(vault)
    selected_runtime = str(requested_runtime or current_selection.get("selected_runtime_id") or "hermes").strip().lower()
    if selected_runtime not in BUILTIN_COMPANIONS:
        selected_runtime = "hermes"
    status = build_phase11_chat_companion_status(vault, requested_runtime=selected_runtime)
    status_cards = {card.get("runtime_id"): card for card in status.get("companion_cards") or []}
    registry_cards = _registry_companions(registry)
    initial_roster = list(INITIAL_COMPANION_IDS)
    runtime_order = [selected_runtime] + [runtime_id for runtime_id in initial_roster if runtime_id != selected_runtime]
    cards = [
        _build_card(
            runtime_id=runtime_id,
            registry_card=registry_cards.get(runtime_id, {}),
            status_card=status_cards.get(runtime_id, {}),
            active_runtime_id=selected_runtime,
        )
        for runtime_id in runtime_order
    ]
    active = next((card for card in cards if card.get("is_active")), cards[0] if cards else {})
    blockers: list[str] = []
    if direction.get("ok") is not True:
        blockers.append("operator_direction_answers_not_ready")
    if registry_readiness.get("ok") is not True:
        blockers.append("multi_companion_registry_not_ready")
    if set(initial_roster) - set(registry_cards):
        blockers.append("initial_roster_missing_registry_cards")
    if len(cards) != 3:
        blockers.append("roster_card_count_mismatch")

    digest_material = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "policy_digest": ((direction.get("digest_proof") or {}).get("digest_material") or {}).get("policy_digest"),
        "registry_path": _rel(vault, registry_path),
        "selected_runtime": selected_runtime,
        "card_digests": [card.get("card_digest") for card in cards],
    }
    ok = not blockers
    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS if ok else "BLOCKED / ROSTER UI PREVIEW NOT READY",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "approval_gated": False,
        "summary": {
            "operator_direction_captured": direction.get("ok") is True,
            "registry_readiness_ok": registry_readiness.get("ok") is True,
            "core_companion_package_used": True,
            "core_roster_valid": core_roster_validation["valid"] is True,
            "roster_ui_preview_ready": ok,
            "roster_cards_visible": ok,
            "active_runtime_id": active.get("runtime_id") or selected_runtime,
            "roster_card_count": len(cards),
            "active_companion_first": True,
            "inactive_roster_browsing_supported": True,
            "multiple_visible_companions_supported_now": False,
            "abstract_visuals_only_until_brand_pack": True,
            "selection_target_written_by_this_surface": False,
            "approval_consumed_by_this_surface": False,
            "provider_call_performed": False,
            "runtime_dispatched": False,
            "agent_bus_task_written": False,
            "canonical_state_mutated": False,
            "blocker_count": len(blockers),
            "next_recommended_pass": NEXT_RECOMMENDED_PASS if ok else "operator-answer-companion-direction-questions",
        },
        "current_selection": current_selection,
        "registry": {
            "path": _rel(vault, registry_path),
            "fallback_example_used": registry_path.name == DEFAULT_REGISTRY_PATH.name,
            "readiness_status": registry_readiness.get("status"),
        },
        "active_card": active,
        "roster_cards": cards,
        "ui_preview": {
            "surface": "chat_panel_companion_roster",
            "source": "runtime/companion core roster",
            "layout": "active_companion_first_then_inactive_roster",
            "card_count": len(cards),
            "uses_abstract_runtime_marks": True,
            "uses_status_badges": True,
            "uses_border_presets": True,
            "uses_lightweight_animation_presets": True,
            "uses_generated_or_final_brand_assets": False,
            "selection_preview_only": True,
            "approval_gated_write_required_for_switch": True,
        },
        "selection_flow_preview": {
            "read_only_preview_first": True,
            "approval_gated_write_to_selected_companion_target": True,
            "target_path": SELECTION_TARGET_PATH,
            "approval_request_created": False,
            "selection_target_written": False,
            "required_existing_executor": "phase11-chat-companion-selection-approval-consumption-executor",
        },
        "authority": {
            "read_only": True,
            "companion_roster_ui_preview_allowed": True,
            "companion_roster_ui_mutation_allowed": False,
            "companion_selection_write_allowed_by_this_surface": False,
            "approval_consumption_allowed_by_this_surface": False,
            "approval_execution_allowed": False,
            "routing_granted": False,
            "tool_access_granted": False,
            "memory_access_granted": False,
            "separate_memory_namespace_declared": True,
            "memory_write_authority_granted": False,
            "write_authority_granted": False,
            "provider_model_selection_granted": False,
            "permission_scope_granted": False,
            "protected_file_access_granted": False,
            "runtime_dispatch_allowed": False,
            "agent_bus_task_write_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "readiness": {
            "companion_roster_ui_preview_ready": ok,
            "runtime_companion_core_adapter_synced": True,
            "operator_direction_answers_required": True,
            "operator_direction_answers_ok": direction.get("ok") is True,
            "registry_readiness_required": True,
            "registry_readiness_ok": registry_readiness.get("ok") is True,
            "selection_target_write_blocked": True,
            "provider_calls_blocked": True,
            "runtime_dispatch_blocked": True,
            "memory_boundary_defined_for_companion_memory": True,
            "memory_boundary_contract_required_before_companion_memory_writes": True,
            "separate_companion_memory_namespace_declared": True,
            "companion_memory_writes_blocked": True,
            "governed_routing_pass_required_before_capability_change": True,
            "agent_bus_task_write_blocked": True,
            "canonical_mutation_blocked": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS if ok else "operator-answer-companion-direction-questions",
        },
        "digest_proof": {
            "roster_preview_digest": _sha256_text(_canonical_json(digest_material)),
            "digest_material": digest_material,
        },
        "blocked_reasons": blockers,
        "warnings": list(dict.fromkeys(registry_warnings + selection_warnings)),
    }


def format_phase11_companion_roster_ui_preview(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    active = payload.get("active_card") or {}
    lines = [
        "Phase 11 Companion Roster UI Preview",
        f"Status: {payload.get('status')}",
        f"Active companion: {active.get('display_name') or summary.get('active_runtime_id')}",
        f"Roster cards: {summary.get('roster_card_count')}",
        f"Ready: {summary.get('roster_ui_preview_ready')}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
        "Boundary: read-only roster preview only; no selection write, no approval consumption, no provider/model routing, no runtime dispatch, no Agent Bus task write, and no canonical mutation.",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers)
    return "\n".join(lines)
