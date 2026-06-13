"""Initial companion roster for ChaseOS Companion Layer v0.1."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from runtime.companion.policy import (
    ALLOWED_EFFECTS,
    FORBIDDEN_EFFECTS,
    INITIAL_COMPANION_IDS,
    PERSONALITY_PRESETS,
    VISUAL_STATES,
    classify_companion_comment,
)
from runtime.companion.schema import validate_companion_profile


CORE_COMPANION_METADATA: dict[str, dict[str, Any]] = {
    "hermes": {
        "display_name": "Hermes",
        "role": "bounded runtime coordination companion",
        "style": "precise, governance-aware, coordination-heavy",
        "preset": "calm_status",
        "visual_mark": "H",
        "mark_shape": "diamond",
        "border_style": "signal-violet",
        "status_badge": "coordinator",
        "animation_preset": "soft-pulse",
        "stats": {"clarity": 92, "governance": 96, "tempo": 74},
        "role_card_hints": ["hermes"],
    },
    "openclaw": {
        "display_name": "OpenClaw",
        "role": "local operator/runtime control companion",
        "style": "operational, tool-aware, safety-bounded",
        "preset": "operator_direct",
        "visual_mark": "O",
        "mark_shape": "hex",
        "border_style": "control-blue",
        "status_badge": "operator",
        "animation_preset": "steady-scan",
        "stats": {"operations": 94, "safety": 91, "tooling": 88},
        "role_card_hints": ["openclaw", "openai"],
    },
    "claude-code": {
        "display_name": "Claude Code",  # overridden at runtime by name_loader
        "role": "personal Claude Code engineering runtime",
        "style": "systems-focused, implementation-oriented",
        "preset": "strategist",
        "visual_mark": "C",
        "mark_shape": "square",
        "border_style": "systems-green",
        "status_badge": "architect",
        "animation_preset": "quiet-grid",
        "stats": {"architecture": 95, "implementation": 90, "analysis": 89},
        "role_card_hints": ["archon", "claude-code", "engineering"],
    },
    "chaser": {
        "display_name": "Chaser Agent",
        "role": "planned internal ChaserAgent companion and gateway diagnostic surface",
        "style": "planned, diagnostic, session-aware, governance-bounded",
        "preset": "debugger",
        "visual_mark": "Ch",
        "mark_shape": "circle",
        "border_style": "gateway-teal",
        "status_badge": "coming-soon",
        "animation_preset": "quiet-scan",
        "stats": {"diagnostic": 72, "sessions": 58, "runtime_readiness": 24},
        "role_card_hints": ["chaser", "chaser-agent", "gateway", "diagnostic"],
    },
}


def _stat(value: int) -> dict[str, Any]:
    return {
        "value": value,
        "cosmetic_only": True,
        "changes_capability": False,
    }


def _base_profile(companion_id: str, *, preset: str, visual_mark: str, border_style: str, animation: str) -> dict[str, Any]:
    builtin = CORE_COMPANION_METADATA[companion_id]
    return {
        "companion_id": companion_id,
        "display_name": builtin["display_name"],
        "runtime_identity": companion_id,
        "short_description": builtin["style"],
        "role_summary": builtin["role"],
        "personality_preset": preset,
        "tone_profile": PERSONALITY_PRESETS[preset]["description"],
        "visual_mark": {
            "kind": "abstract_runtime_mark",
            "token": visual_mark,
            "asset_path": "",
            "final_brand_asset_required": False,
        },
        "border_style": border_style,
        "animation_preset": animation,
        "status_states": list(VISUAL_STATES),
        "rarity": {
            "label": "built-in",
            "cosmetic_only": True,
            "changes_capability": False,
        },
        "capability_summary": (
            "Companion profile metadata does not grant runtime authority, routing, "
            "provider/model access, tools, permissions, memory write authority, or writeback."
        ),
        "governance_boundary": "Companion identity is not runtime authority.",
        "memory_scope": (
            "Separate companion memory is allowed only as governed, approval-gated, "
            "non-authoritative companion memory. It does not change routing, permissions, "
            "provider/model access, tools, or canonical state."
        ),
        "routing_effect": "none",
        "permission_effect": "none",
        "current_status": "available",
        "allowed_effects": list(ALLOWED_EFFECTS),
        "forbidden_effects": list(FORBIDDEN_EFFECTS),
        "commentary_policy": {
            "classification": "non_authoritative_commentary",
            "can_trigger_tools": False,
            "can_override_policy": False,
            "can_write_memory": False,
            "can_mutate_canonical_state": False,
        },
    }


def _profiles() -> dict[str, dict[str, Any]]:
    hermes_meta = CORE_COMPANION_METADATA["hermes"]
    hermes = _base_profile(
        "hermes",
        preset=str(hermes_meta["preset"]),
        visual_mark=str(hermes_meta["visual_mark"]),
        border_style=str(hermes_meta["border_style"]),
        animation=str(hermes_meta["animation_preset"]),
    )
    hermes["stats"] = {key: _stat(value) for key, value in hermes_meta["stats"].items()}
    hermes["commentary_examples"] = [
        classify_companion_comment(
            "Shadow output generated. No canonical writeback detected.",
            companion_id="hermes",
        )
    ]

    openclaw_meta = CORE_COMPANION_METADATA["openclaw"]
    openclaw = _base_profile(
        "openclaw",
        preset=str(openclaw_meta["preset"]),
        visual_mark=str(openclaw_meta["visual_mark"]),
        border_style=str(openclaw_meta["border_style"]),
        animation=str(openclaw_meta["animation_preset"]),
    )
    openclaw["stats"] = {key: _stat(value) for key, value in openclaw_meta["stats"].items()}
    openclaw["commentary_examples"] = [
        classify_companion_comment(
            "This touches a protected surface. Keep this gated.",
            companion_id="openclaw",
        )
    ]

    cc_meta = CORE_COMPANION_METADATA["claude-code"]
    claude_code = _base_profile(
        "claude-code",
        preset=str(cc_meta["preset"]),
        visual_mark=str(cc_meta["visual_mark"]),
        border_style=str(cc_meta["border_style"]),
        animation=str(cc_meta["animation_preset"]),
    )
    claude_code["stats"] = {key: _stat(value) for key, value in cc_meta["stats"].items()}
    claude_code["commentary_examples"] = [
        classify_companion_comment(
            "This looks like a planning task, not an execution pass.",
            companion_id="claude-code",
        )
    ]
    chaser_meta = CORE_COMPANION_METADATA["chaser"]
    chaser = _base_profile(
        "chaser",
        preset=str(chaser_meta["preset"]),
        visual_mark=str(chaser_meta["visual_mark"]),
        border_style=str(chaser_meta["border_style"]),
        animation=str(chaser_meta["animation_preset"]),
    )
    chaser["stats"] = {key: _stat(value) for key, value in chaser_meta["stats"].items()}
    chaser["current_status"] = "planned"
    chaser["capability_summary"] = (
        "Chaser Agent companion metadata is prepared for a coming-soon surface only. "
        "It does not grant runtime authority, routing, provider/model access, tools, "
        "permissions, memory write authority, workflow execution, or writeback."
    )
    chaser["governance_boundary"] = (
        "Chaser Agent is not an active companion runtime. Current Chaser code is limited "
        "to read-only diagnostic/session/export footholds until agent and board modules are built."
    )
    chaser["commentary_examples"] = [
        classify_companion_comment(
            "Chaser Agent is prepared as a coming-soon profile; no runtime activation is available.",
            companion_id="chaser",
        )
    ]
    return {
        "hermes": hermes,
        "openclaw": openclaw,
        "claude-code": claude_code,
        "chaser": chaser,
    }


def list_companions() -> list[dict[str, Any]]:
    """Return the initial v0.1 roster as validated profile dictionaries."""

    return [deepcopy(_profiles()[companion_id]) for companion_id in INITIAL_COMPANION_IDS]


def get_companion(companion_id: str) -> dict[str, Any]:
    """Return one companion profile or raise ValueError for unknown IDs."""

    normalized = str(companion_id or "").strip().lower()
    profiles = _profiles()
    if normalized not in profiles:
        raise ValueError(f"invalid companion id: {companion_id}")
    return deepcopy(profiles[normalized])


def get_companion_status_metadata(companion_id: str) -> dict[str, Any]:
    """Return compact metadata used by Studio status/registry surfaces."""

    normalized = str(companion_id or "").strip().lower()
    if normalized not in CORE_COMPANION_METADATA:
        raise ValueError(f"invalid companion id: {companion_id}")
    item = CORE_COMPANION_METADATA[normalized]
    return {
        "display_name": item["display_name"],
        "role": item["role"],
        "style": item["style"],
        "role_card_hints": list(item["role_card_hints"]),
        "visual_mark": item["visual_mark"],
        "mark_shape": item["mark_shape"],
        "border_style": item["border_style"],
        "status_badge": item["status_badge"],
        "animation_preset": item["animation_preset"],
        "stats": deepcopy(item["stats"]),
    }


def get_companion_display_name(companion_id: str, vault_root: str | Path | None = None) -> str:
    """Return the display name for a companion, reading from its runtime profile if possible."""
    from pathlib import Path as _Path

    if vault_root is not None:
        try:
            from runtime.companion.name_loader import load_companion_display_name
            return load_companion_display_name(companion_id, vault_root)
        except Exception:
            pass

    normalized = str(companion_id or "").strip().lower()
    if normalized in CORE_COMPANION_METADATA:
        return str(CORE_COMPANION_METADATA[normalized]["display_name"])
    return normalized.replace("-", " ").title()


def validate_roster() -> dict[str, Any]:
    """Validate all initial roster profiles."""

    profile_reports = {
        profile["companion_id"]: validate_companion_profile(profile)
        for profile in list_companions()
    }
    errors = {
        companion_id: report["errors"]
        for companion_id, report in profile_reports.items()
        if report["errors"]
    }
    return {
        "valid": not errors,
        "profile_reports": profile_reports,
        "errors": errors,
    }
