"""Policy constants for ChaseOS Companion Layer v0.1."""

from __future__ import annotations

from pathlib import Path
from typing import Any


POLICY_VERSION = "chaseos.companion.policy.v0.1"
INITIAL_COMPANION_IDS = ("hermes", "openclaw", "claude-code", "chaser")
PLANNED_COMPANION_IDS = ("chaser",)
SELECTABLE_COMPANION_IDS = tuple(
    companion_id for companion_id in INITIAL_COMPANION_IDS
    if companion_id not in PLANNED_COMPANION_IDS
)
DEFAULT_COMPANION_ID = "hermes"
SELECTION_TARGET_PATH = Path("runtime/studio/chat/companion-selection.json")
SWITCH_LEDGER_PATH = Path("07_LOGS/Agent-Activity/companion-switch-ledger.jsonl")

ALLOWED_EFFECTS = (
    "visual_identity",
    "profile_card_metadata",
    "tone_preset",
    "status_narration",
    "read_only_runtime_card_display",
    "non_authoritative_commentary",
)

FORBIDDEN_EFFECTS = (
    "runtime_routing_changes",
    "model_provider_switching",
    "ungoverned_memory_access",
    "memory_write_authority_changes",
    "permission_changes",
    "tool_access_changes",
    "connector_access_changes",
    "protected_file_access_changes",
    "workflow_execution_changes",
    "canonical_state_mutation",
)

VISUAL_STATES = (
    "idle",
    "selected",
    "running",
    "waiting_for_approval",
    "blocked",
    "warning",
    "complete",
    "unavailable",
)

PERSONALITY_PRESETS: dict[str, dict[str, Any]] = {
    "operator_direct": {
        "description": "Direct operator phrasing with visible governance boundaries.",
        "authority_changes": False,
    },
    "strategist": {
        "description": "Architecture and decision-tradeoff framing.",
        "authority_changes": False,
    },
    "teacher": {
        "description": "Explanatory, patient, and context-building.",
        "authority_changes": False,
    },
    "security_reviewer": {
        "description": "Risk-first review language and approval reminders.",
        "authority_changes": False,
    },
    "calm_status": {
        "description": "Quiet status narration and progress posture.",
        "authority_changes": False,
    },
    "debugger": {
        "description": "Failure-oriented diagnostic commentary.",
        "authority_changes": False,
    },
}


def build_authority_report() -> dict[str, bool]:
    """Return the v0.1 authority posture for companion behavior."""

    return {
        "routing_changed": False,
        "memory_changed": False,
        "permissions_changed": False,
        "provider_model_changed": False,
        "tool_access_changed": False,
        "connector_access_changed": False,
        "protected_file_access_changed": False,
        "workflow_execution_changed": False,
        "canonical_state_mutated": False,
        "runtime_activated": False,
    }


def assert_v0_1_no_authority_change(report: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fail closed if a caller tries to attach authority changes to selection."""

    authority = build_authority_report()
    if report:
        authority.update({key: bool(value) for key, value in report.items() if key in authority})
    changed = [key for key, value in authority.items() if value is not False]
    return {
        "ok": not changed,
        "policy_version": POLICY_VERSION,
        "authority": authority,
        "blocked_reasons": [f"authority_change_forbidden:{key}" for key in changed],
    }


def classify_companion_comment(text: str, *, companion_id: str) -> dict[str, Any]:
    """Classify a companion comment as status/commentary, never instruction."""

    return {
        "companion_id": companion_id,
        "text": text,
        "classification": "non_authoritative_commentary",
        "is_executable_instruction": False,
        "grants_permission": False,
        "changes_routing": False,
        "writes_memory": False,
        "mutates_canonical_state": False,
    }
