"""
runtime.chaser.policies

Fail-closed policy helpers for ChaserAgent Phase A.

These helpers describe what ChaserAgent may preview. They do not grant runtime
authority, execute tools, call providers, write memory, or mutate canonical
state.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


CHASER_RUNTIME_ID = "chaser"
CHASER_PHASE = "phase_a_core_foundation"
CHASER_STATUS = "planned_profile_prepared_not_live"

ALLOWED_RESULT_SHAPES = ("proposal", "patch", "risk", "blocked", "complete")

FORBIDDEN_AUTHORITY_FLAGS = (
    "runtime_activated",
    "agent_bus_task_claimed",
    "agent_bus_task_written",
    "provider_called",
    "tool_executed",
    "shell_executed",
    "memory_written",
    "canonical_state_mutated",
    "protected_file_mutated",
    "credential_read",
    "external_network_called",
)


def build_no_authority_report() -> dict[str, bool]:
    """Return the binding no-authority posture for ChaserAgent Phase A."""

    return {flag: False for flag in FORBIDDEN_AUTHORITY_FLAGS}


def assert_no_authority_change(report: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fail closed if a caller tries to attach authority to a Chaser preview."""

    authority = build_no_authority_report()
    if isinstance(report, dict):
        for key in authority:
            if key in report:
                authority[key] = bool(report[key])
    changed = [key for key, value in authority.items() if value is not False]
    return {
        "ok": not changed,
        "runtime_id": CHASER_RUNTIME_ID,
        "phase": CHASER_PHASE,
        "status": CHASER_STATUS,
        "authority": authority,
        "blocked_reasons": [f"authority_change_forbidden:{key}" for key in changed],
    }


def validate_result_shape(result_shape: str) -> dict[str, Any]:
    """Validate the standard ChaseOS Agent Bus result shape vocabulary."""

    shape = str(result_shape or "").strip().lower()
    valid = shape in ALLOWED_RESULT_SHAPES
    return {
        "ok": valid,
        "result_shape": shape,
        "allowed_result_shapes": list(ALLOWED_RESULT_SHAPES),
        "blocked_reasons": [] if valid else ["invalid_result_shape"],
    }


def build_policy_snapshot() -> dict[str, Any]:
    """Return a read-only policy snapshot for ChaserAgent display surfaces."""

    return {
        "runtime_id": CHASER_RUNTIME_ID,
        "phase": CHASER_PHASE,
        "status": CHASER_STATUS,
        "read_only": True,
        "available_for_runtime_activation": False,
        "allowed_result_shapes": list(ALLOWED_RESULT_SHAPES),
        "authority": build_no_authority_report(),
        "boundary": (
            "ChaserAgent Phase A may build proposals, board cards, profile views, "
            "toolset views, memory-boundary previews, and artifact manifests only."
        ),
    }


def merge_authority_evidence(*reports: dict[str, Any]) -> dict[str, Any]:
    """Combine authority reports and fail closed if any forbidden flag is true."""

    merged = build_no_authority_report()
    for report in reports:
        if not isinstance(report, dict):
            continue
        source = report.get("authority") if isinstance(report.get("authority"), dict) else report
        for key in merged:
            if bool(source.get(key, False)):
                merged[key] = True
    result = assert_no_authority_change(deepcopy(merged))
    result["merged"] = True
    return result
