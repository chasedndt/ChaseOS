"""Approved Phase 11 operator companion direction answers.

This surface reads the operator-approved v0.1 companion direction artifact and
validates that the policy is complete while preserving the authority boundary:
the direction can unlock a roster UI preview, but it cannot grant routing,
memory, provider, tool, runtime, Agent Bus, or canonical write authority.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.phase11_operator_companion_direction import (
    DECISION_FIELDS,
    build_phase11_operator_companion_direction,
)


MODEL_VERSION = "studio.phase11_operator_companion_direction_answers.v1"
SURFACE_ID = "phase11_operator_companion_direction_answers"
PASS_ID = "operator-answer-companion-direction-questions"
STATUS = "COMPLETE / OPERATOR-APPROVED / READ-ONLY POLICY CAPTURE / NO AUTHORITY EXPANSION"
NEXT_RECOMMENDED_PASS = "phase11-companion-roster-ui-preview"
OPERATOR_DIRECTION_RELATIVE_PATH = Path("runtime/studio/chat/companions/operator-direction.v0.1.json")

REQUIRED_ROSTER = ["hermes", "openclaw", "claude-code"]
REQUIRED_ALLOWED_EFFECTS = [
    "ui_identity",
    "tone_preset",
    "status_narration",
    "read_only_runtime_card_display",
    "non_authoritative_companion_comments",
]
REQUIRED_BLOCKED_EFFECTS = [
    "execution_routing",
    "provider_model_selection",
    "permission_scope",
    "writeback_authority",
    "memory_write_authority",
    "tool_access",
    "protected_file_access",
]
REQUIRED_DESCRIPTIVE_METADATA = ["rarity", "stats", "personality"]
AUTHORITY_FIELDS = [
    "routing_granted",
    "tool_access_granted",
    "memory_access_granted",
    "write_authority_granted",
    "provider_model_selection_granted",
    "permission_scope_granted",
    "protected_file_access_granted",
    "runtime_dispatch_granted",
    "agent_bus_task_write_granted",
    "canonical_mutation_granted",
]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _load_policy(vault: Path, direction_path: str | Path | None = None) -> tuple[dict[str, Any], Path, list[str]]:
    path = Path(direction_path) if direction_path else OPERATOR_DIRECTION_RELATIVE_PATH
    resolved = path if path.is_absolute() else vault / path
    warnings: list[str] = []
    if not resolved.exists():
        return {}, resolved, [f"operator_direction_policy_missing:{resolved}"]
    try:
        return json.loads(resolved.read_text(encoding="utf-8")), resolved, warnings
    except json.JSONDecodeError as exc:
        return {}, resolved, [f"operator_direction_policy_invalid_json:{exc}"]


def _contains_all(values: Any, required: list[str]) -> bool:
    return set(required).issubset({str(item) for item in (values or [])})


def build_phase11_operator_companion_direction_answers(
    vault_root: str | Path,
    *,
    direction_path: str | Path | None = None,
) -> dict[str, Any]:
    """Validate the operator-approved v0.1 companion direction policy."""

    vault = Path(vault_root).resolve()
    policy, resolved_policy_path, warnings = _load_policy(vault, direction_path)
    decisions = {
        field: str((policy.get("operator_decisions") or {}).get(field) or "").strip()
        for field in DECISION_FIELDS
    }
    direction_packet = build_phase11_operator_companion_direction(vault, operator_decisions=decisions)
    authority = policy.get("authority") or {}
    future = policy.get("future_boundaries") or {}
    blocked_reasons: list[str] = list(warnings)

    if not policy:
        blocked_reasons.append("operator_direction_policy_not_loaded")
    if policy.get("status") != "OPERATOR_APPROVED_WITH_AMENDMENTS / UI_ONLY / NO_AUTHORITY_EXPANSION":
        blocked_reasons.append("operator_direction_status_not_approved_with_amendments")
    if any(not decisions[field] for field in DECISION_FIELDS):
        blocked_reasons.append("operator_direction_decision_fields_incomplete")
    if not _contains_all(policy.get("initial_roster"), REQUIRED_ROSTER):
        blocked_reasons.append("operator_direction_initial_roster_missing_required_companions")
    if not _contains_all(policy.get("v0_1_affects"), REQUIRED_ALLOWED_EFFECTS):
        blocked_reasons.append("operator_direction_allowed_effects_incomplete")
    if not _contains_all(policy.get("v0_1_does_not_affect"), REQUIRED_BLOCKED_EFFECTS):
        blocked_reasons.append("operator_direction_blocked_effects_incomplete")
    if not _contains_all(policy.get("descriptive_metadata_only"), REQUIRED_DESCRIPTIVE_METADATA):
        blocked_reasons.append("operator_direction_descriptive_metadata_policy_incomplete")
    if any(authority.get(field) is not False for field in AUTHORITY_FIELDS):
        blocked_reasons.append("operator_direction_authority_expansion_detected")
    if future.get("companion_memory_boundary_contract_defined") is not True:
        blocked_reasons.append("operator_direction_missing_memory_boundary_contract")
    if future.get("companion_memory_writes_require_future_approval_executor") is not True:
        blocked_reasons.append("operator_direction_missing_memory_write_executor_future_gate")
    if future.get("runtime_capability_changes_require_future_governed_routing_pass") is not True:
        blocked_reasons.append("operator_direction_missing_routing_future_gate")

    ok = not blocked_reasons and direction_packet.get("summary", {}).get("ready_for_roster_ui_preview") is True
    digest_material = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "direction_id": policy.get("direction_id"),
        "policy_digest": _sha256_text(_canonical_json(policy)) if policy else "",
        "direction_packet_digest": ((direction_packet.get("digest_proof") or {}).get("direction_digest")),
        "required_roster": REQUIRED_ROSTER,
        "allowed_effects": policy.get("v0_1_affects") or [],
        "blocked_effects": policy.get("v0_1_does_not_affect") or [],
        "authority_fields": {field: authority.get(field) for field in AUTHORITY_FIELDS},
    }

    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS if ok else "BLOCKED / OPERATOR DIRECTION POLICY INVALID",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "policy_path": str(resolved_policy_path),
        "policy_vault_relative_path": (
            resolved_policy_path.relative_to(vault).as_posix()
            if resolved_policy_path.is_relative_to(vault)
            else str(resolved_policy_path)
        ),
        "read_only": True,
        "approval_gated": False,
        "summary": {
            "operator_direction_policy_loaded": bool(policy),
            "operator_direction_captured": ok,
            "operator_approved_with_amendments": policy.get("status")
            == "OPERATOR_APPROVED_WITH_AMENDMENTS / UI_ONLY / NO_AUTHORITY_EXPANSION",
            "operator_decision_field_count": len(DECISION_FIELDS),
            "operator_decision_answered_count": sum(1 for field in DECISION_FIELDS if decisions[field]),
            "operator_decision_unanswered_count": sum(1 for field in DECISION_FIELDS if not decisions[field]),
            "initial_roster_count": len(policy.get("initial_roster") or []),
            "allowed_v0_1_effect_count": len(policy.get("v0_1_affects") or []),
            "blocked_v0_1_effect_count": len(policy.get("v0_1_does_not_affect") or []),
            "ready_for_roster_ui_preview": ok,
            "separate_companion_memory_allowed": True,
            "companion_memory_boundary_contract_defined": future.get("companion_memory_boundary_contract_defined") is True,
            "companion_memory_writes_require_future_approval_executor": (
                future.get("companion_memory_writes_require_future_approval_executor") is True
            ),
            "roster_ui_built": False,
            "operator_direction_artifact_written_by_this_surface": False,
            "selection_target_written_by_this_surface": False,
            "approval_consumed_by_this_surface": False,
            "provider_call_performed": False,
            "runtime_dispatched": False,
            "agent_bus_task_written": False,
            "canonical_state_mutated": False,
            "blocker_count": len(blocked_reasons),
            "next_recommended_pass": NEXT_RECOMMENDED_PASS if ok else PASS_ID,
        },
        "policy": policy,
        "direction_packet": {
            "surface": direction_packet.get("surface"),
            "ok": direction_packet.get("ok"),
            "status": direction_packet.get("status"),
            "summary": direction_packet.get("summary") or {},
            "readiness": direction_packet.get("readiness") or {},
            "authority": direction_packet.get("authority") or {},
        },
        "operator_decisions": decisions,
        "allowed_v0_1_effects": policy.get("v0_1_affects") or [],
        "blocked_v0_1_effects": policy.get("v0_1_does_not_affect") or [],
        "descriptive_metadata_only": policy.get("descriptive_metadata_only") or [],
        "future_boundaries": future,
        "digest_proof": {
            "answers_digest": _sha256_text(_canonical_json(digest_material)),
            "digest_material": digest_material,
        },
        "readiness": {
            "operator_companion_direction_answers_ready": ok,
            "operator_direction_captured": ok,
            "ready_for_roster_ui_preview": ok,
            "roster_ui_blocked_until_direction": not ok,
            "selection_target_write_requires_existing_governed_executor": True,
            "provider_calls_blocked": True,
            "runtime_dispatch_blocked": True,
            "memory_boundary_contract_defined": future.get("companion_memory_boundary_contract_defined") is True,
            "memory_write_executor_required_before_companion_memory_writes": True,
            "governed_routing_pass_required_before_capability_change": True,
            "agent_bus_task_write_blocked": True,
            "canonical_mutation_blocked": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS if ok else PASS_ID,
        },
        "authority": {
            "read_only": True,
            "operator_direction_artifact_write_allowed": False,
            "operator_decision_write_allowed": False,
            "companion_roster_ui_mutation_allowed": False,
            "companion_selection_write_allowed_by_this_surface": False,
            "approval_consumption_allowed_by_this_surface": False,
            "approval_execution_allowed": False,
            "routing_granted": False,
            "tool_access_granted": False,
            "memory_access_granted": False,
            "write_authority_granted": False,
            "provider_model_selection_granted": False,
            "permission_scope_granted": False,
            "protected_file_access_granted": False,
            "runtime_dispatch_allowed": False,
            "agent_bus_task_write_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "blocked_reasons": blocked_reasons,
        "warnings": warnings,
    }


def format_phase11_operator_companion_direction_answers(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "Phase 11 Operator Companion Direction Answers",
        f"Status: {payload.get('status')}",
        f"Policy: {payload.get('policy_vault_relative_path')}",
        f"Answered decisions: {summary.get('operator_decision_answered_count')}/{summary.get('operator_decision_field_count')}",
        f"Ready for roster UI preview: {summary.get('ready_for_roster_ui_preview')}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
        "Allowed v0.1 effects:",
    ]
    for item in payload.get("allowed_v0_1_effects") or []:
        lines.append(f"- {item}")
    lines.append("Blocked v0.1 effects:")
    for item in payload.get("blocked_v0_1_effects") or []:
        lines.append(f"- {item}")
    if payload.get("blocked_reasons"):
        lines.append("Blocked reasons:")
        for item in payload.get("blocked_reasons") or []:
            lines.append(f"- {item}")
    lines.append(
        "Boundary: approved direction only; no roster UI mutation, no companion selection write by this surface, "
        "no approval consumption/execution, no provider/model routing, no runtime dispatch, no Agent Bus task write, "
        "and no canonical mutation."
    )
    return "\n".join(lines)
