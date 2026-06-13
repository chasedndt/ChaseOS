"""Profile validation for ChaseOS Companion Layer v0.1."""

from __future__ import annotations

from typing import Any

from runtime.companion.policy import ALLOWED_EFFECTS, FORBIDDEN_EFFECTS, INITIAL_COMPANION_IDS, VISUAL_STATES


REQUIRED_PROFILE_FIELDS = (
    "companion_id",
    "display_name",
    "runtime_identity",
    "short_description",
    "role_summary",
    "personality_preset",
    "tone_profile",
    "visual_mark",
    "border_style",
    "animation_preset",
    "status_states",
    "rarity",
    "stats",
    "capability_summary",
    "governance_boundary",
    "memory_scope",
    "routing_effect",
    "permission_effect",
    "current_status",
    "allowed_effects",
    "forbidden_effects",
    "commentary_policy",
)


def _missing_or_empty(profile: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for field in REQUIRED_PROFILE_FIELDS:
        value = profile.get(field)
        if value is None or value == "" or value == [] or value == {}:
            missing.append(field)
    return missing


def _stats_are_cosmetic(stats: Any) -> bool:
    if not isinstance(stats, dict):
        return False
    for value in stats.values():
        if not isinstance(value, dict):
            return False
        if value.get("changes_capability") is not False:
            return False
        if value.get("cosmetic_only") is not True:
            return False
    return True


def validate_companion_profile(profile: dict[str, Any]) -> dict[str, Any]:
    """Validate a v0.1 companion profile without external dependencies."""

    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(profile, dict):
        return {
            "valid": False,
            "errors": ["profile_not_object"],
            "warnings": [],
        }

    missing = _missing_or_empty(profile)
    errors.extend(f"missing_required_field:{field}" for field in missing)

    companion_id = str(profile.get("companion_id") or "").strip().lower()
    if companion_id not in INITIAL_COMPANION_IDS:
        errors.append("companion_id_not_in_initial_roster")

    allowed = tuple(profile.get("allowed_effects") or ())
    forbidden = tuple(profile.get("forbidden_effects") or ())
    if not set(allowed).issubset(ALLOWED_EFFECTS):
        errors.append("allowed_effects_include_unapproved_effect")
    if set(FORBIDDEN_EFFECTS) - set(forbidden):
        errors.append("forbidden_effects_missing_required_boundary")

    if profile.get("routing_effect") != "none":
        errors.append("routing_effect_must_be_none")
    if profile.get("permission_effect") != "none":
        errors.append("permission_effect_must_be_none")

    memory_scope = str(profile.get("memory_scope") or "").lower()
    if "separate companion memory" not in memory_scope:
        errors.append("memory_scope_must_state_separate_companion_memory")
    if "governed" not in memory_scope or "approval" not in memory_scope:
        errors.append("memory_scope_must_state_governed_approval_boundary")
    if "non-authoritative" not in memory_scope and "non authoritative" not in memory_scope:
        errors.append("memory_scope_must_state_non_authoritative_memory")

    rarity = profile.get("rarity")
    if not isinstance(rarity, dict) or rarity.get("changes_capability") is not False:
        errors.append("rarity_must_be_cosmetic")
    if not _stats_are_cosmetic(profile.get("stats")):
        errors.append("stats_must_be_cosmetic")

    status_states = tuple(profile.get("status_states") or ())
    if not set(status_states).issubset(VISUAL_STATES):
        errors.append("status_states_include_unknown_state")

    commentary = profile.get("commentary_policy") or {}
    if commentary.get("classification") != "non_authoritative_commentary":
        errors.append("commentary_policy_must_be_non_authoritative")
    if commentary.get("can_trigger_tools") is not False:
        errors.append("commentary_policy_must_not_trigger_tools")
    if commentary.get("can_override_policy") is not False:
        errors.append("commentary_policy_must_not_override_policy")
    if commentary.get("can_write_memory") is not False:
        errors.append("commentary_policy_must_not_write_memory")

    if profile.get("capability_summary") and "does not grant" not in str(profile["capability_summary"]).lower():
        warnings.append("capability_summary_should_explicitly_state_no_authority_grant")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
    }
