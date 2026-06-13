"""N26 ChaserAgent profile/toolset activation design.

This read-only surface designs the next guarded profile/toolset activation
contract after N25 activation-state readiness. It reads existing readiness and
descriptive profile/toolset views, previews future activation artifacts, and
stops before any runtime/profile/toolset activation, terminal binding, Agent Bus
mutation, provider dispatch, or canonical writeback.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.chaser.profiles import list_profiles, validate_profile_view
from runtime.chaser.runtime_activation_state_readiness import (
    build_chaser_runtime_activation_state_readiness,
)
from runtime.chaser.toolsets import list_toolsets, validate_toolset_view


SURFACE = "chaser_runtime_profile_toolset_activation_design"
SCHEMA_VERSION = "chaser_runtime_profile_toolset_activation_design.v1"
NEXT_PASS = "terminal-n28-chaser-runtime-profile-toolset-activation-readiness"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _authority() -> dict[str, bool]:
    return {
        "runtime_activation_now": False,
        "profile_activation_now": False,
        "toolset_activation_now": False,
        "terminal_toolset_binding_now": False,
        "studio_execution_now": False,
        "terminal_execution_now": False,
        "approval_queue_write_now": False,
        "approval_decision_write_now": False,
        "approval_consumption_now": False,
        "exact_once_marker_write_now": False,
        "profile_activation_state_write_now": False,
        "toolset_activation_state_write_now": False,
        "profile_toolset_activation_audit_write_now": False,
        "agent_bus_write_now": False,
        "agent_bus_claim_now": False,
        "provider_call_now": False,
        "canonical_writeback_now": False,
        "external_network_now": False,
        "host_mutation_now": False,
    }


def _blocked_actions() -> list[str]:
    return [
        "mutate approval request status",
        "consume approvals",
        "activate live ChaserAgent runtime",
        "activate Chaser profile as executable authority",
        "activate Chaser toolset as executable authority",
        "bind terminal tools to ChaserAgent",
        "execute terminal command",
        "expose Studio terminal execution",
        "write profile/toolset activation marker or state",
        "write or claim Agent Bus tasks",
        "call provider or model APIs",
        "write canonical ChaseOS memory/state",
        "mutate host startup/autostart/service state",
    ]


def _profile_map() -> dict[str, dict[str, Any]]:
    return {str(item.get("profile_id") or ""): item for item in list_profiles()}


def _toolset_map() -> dict[str, dict[str, Any]]:
    return {str(item.get("toolset_id") or ""): item for item in list_toolsets()}


def _safe_slug(value: str) -> str:
    cleaned = []
    for char in str(value or "").strip().lower():
        if char.isalnum() or char in {"-", "_"}:
            cleaned.append(char)
        else:
            cleaned.append("-")
    slug = "".join(cleaned).strip("-")
    return slug or "unknown"


def _activation_digest(approval_id: str, profile_id: str, toolset_id: str) -> str:
    payload = f"{approval_id}|{profile_id}|{toolset_id}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def _future_paths(
    approval_id: str,
    profile_id: str,
    toolset_id: str,
) -> dict[str, str]:
    digest = _activation_digest(approval_id, profile_id, toolset_id)
    profile_slug = _safe_slug(profile_id)
    toolset_slug = _safe_slug(toolset_id)
    stem = f"chaser-pta-{profile_slug}-{toolset_slug}-{digest}"
    return {
        "marker": f"runtime/chaser/profile-toolset-activation-markers/{stem}.json",
        "profile_state": f"runtime/chaser/profile-activation-state/{stem}.json",
        "toolset_state": f"runtime/chaser/toolset-activation-state/{stem}.json",
        "audit": "07_LOGS/Chaser-Activation/profile-toolset-activation.jsonl",
    }


def _path_exists(root: Path, rel_path: str) -> bool:
    path = (root / rel_path).resolve(strict=False)
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return path.exists()


def _check(name: str, ok: bool, detail: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "ok": bool(ok),
        "status": "passed" if ok else "blocked",
        "detail": detail,
    }


def _terminal_binding_design(toolset_id: str) -> dict[str, Any]:
    terminal_related = toolset_id == "terminal-preview"
    return {
        "toolset_id": toolset_id,
        "terminal_related": terminal_related,
        "terminal_binding_allowed_now": False,
        "terminal_execution_allowed_now": False,
        "studio_terminal_execution_allowed_now": False,
        "future_binding_mode": (
            "read_only_policy_preview_and_audit_history_only"
            if terminal_related
            else "no_terminal_binding_requested"
        ),
        "write_capable_terminal_lane": (
            "dedicated_cli_approval_lane_only_until_separately_gated"
            if terminal_related
            else "not_requested"
        ),
        "must_preserve": [
            "no_unrestricted_shell",
            "no_studio_execute_or_run_button",
            "terminal_output_remains_tier_4_untrusted",
            "terminal_tool_binding_requires_separate_write_guard",
            "agent_bus_mutation_requires_separate_gate",
            "provider_dispatch_requires_separate_gate",
        ],
    }


def build_chaser_runtime_profile_toolset_activation_design(
    vault_root: str | Path,
    approval_id: str,
    *,
    expected_preview_id: str = "",
    expected_profile_id: str = "",
    expected_toolset_id: str = "",
    actor: str = "operator",
) -> dict[str, Any]:
    """Design the future profile/toolset activation write guard without writing."""

    root = Path(vault_root).resolve()
    actor_value = actor or "operator"
    requested_id = str(approval_id or "").strip()
    readiness = build_chaser_runtime_activation_state_readiness(
        root,
        requested_id,
        expected_preview_id=expected_preview_id,
        actor=actor_value,
    )
    activation_approval_id = str(readiness.get("activation_approval_id") or requested_id)
    activation_preview_id = readiness.get("activation_approval_preview_id")
    profile_id = str(readiness.get("profile_id") or "").strip().lower()
    toolset_id = str(readiness.get("toolset_id") or "").strip().lower()

    blockers: list[str] = []
    if readiness.get("ok") is not True:
        blockers.append("activation_state_readiness_not_ready")
        blockers.extend(str(item) for item in readiness.get("blockers") or [])
    if (
        readiness.get("ready_for_profile_toolset_activation_design_next_pass")
        is not True
    ):
        blockers.append(
            str(
                readiness.get("activation_state_readiness_status")
                or "blocked_activation_state_readiness"
            )
        )

    expected_profile = str(expected_profile_id or "").strip().lower()
    expected_toolset = str(expected_toolset_id or "").strip().lower()
    if expected_profile and profile_id and expected_profile != profile_id:
        blockers.append(f"profile_id_mismatch:{expected_profile}!={profile_id}")
    if expected_toolset and toolset_id and expected_toolset != toolset_id:
        blockers.append(f"toolset_id_mismatch:{expected_toolset}!={toolset_id}")

    profiles = _profile_map()
    toolsets = _toolset_map()
    profile = profiles.get(profile_id)
    toolset = toolsets.get(toolset_id)
    if not profile_id:
        blockers.append("profile_id_missing_from_activation_state")
    elif profile is None:
        blockers.append(f"unknown_profile:{profile_id}")
    if not toolset_id:
        blockers.append("toolset_id_missing_from_activation_state")
    elif toolset is None:
        blockers.append(f"unknown_toolset:{toolset_id}")

    profile_validation = (
        validate_profile_view(profile)
        if profile is not None
        else {"ok": False, "errors": ["profile_missing"]}
    )
    toolset_validation = (
        validate_toolset_view(toolset)
        if toolset is not None
        else {"ok": False, "errors": ["toolset_missing"]}
    )
    if profile_validation.get("ok") is not True:
        blockers.append(
            f"profile_not_descriptive_only:{profile_id or 'missing'}"
        )
    if toolset_validation.get("ok") is not True:
        blockers.append(f"toolset_not_non_executing:{toolset_id or 'missing'}")

    future_paths = _future_paths(
        activation_approval_id,
        profile_id or "missing",
        toolset_id or "missing",
    )
    future_artifacts = {
        "profile_toolset_activation_marker": {
            "schema_version": "chaser_profile_toolset_activation_marker.v1",
            "path": future_paths["marker"],
            "exists": _path_exists(root, future_paths["marker"]),
            "written_in_this_pass": False,
            "record_type": "chaser_profile_toolset_activation_marker",
            "status": "future_write_guard_required",
        },
        "profile_activation_state": {
            "schema_version": "chaser_profile_activation_state.v1",
            "path": future_paths["profile_state"],
            "exists": _path_exists(root, future_paths["profile_state"]),
            "written_in_this_pass": False,
            "record_type": "chaser_profile_activation_state",
            "status": "future_write_guard_required",
        },
        "toolset_activation_state": {
            "schema_version": "chaser_toolset_activation_state.v1",
            "path": future_paths["toolset_state"],
            "exists": _path_exists(root, future_paths["toolset_state"]),
            "written_in_this_pass": False,
            "record_type": "chaser_toolset_activation_state",
            "status": "future_write_guard_required",
        },
        "profile_toolset_activation_audit": {
            "schema_version": "chaser_profile_toolset_activation_audit.v1",
            "path": future_paths["audit"],
            "exists": _path_exists(root, future_paths["audit"]),
            "written_in_this_pass": False,
            "event_type": "chaser_profile_toolset_activation_design_preview",
        },
    }
    design_checks = [
        _check(
            "activation_state_readiness_ready",
            readiness.get("ok") is True,
            str(readiness.get("activation_state_readiness_status") or ""),
        ),
        _check(
            "profile_view_descriptive_only",
            profile_validation.get("ok") is True,
            ",".join(profile_validation.get("errors") or []),
        ),
        _check(
            "toolset_view_non_executing",
            toolset_validation.get("ok") is True,
            ",".join(toolset_validation.get("errors") or []),
        ),
        _check(
            "terminal_binding_still_future_gated",
            _terminal_binding_design(toolset_id).get("terminal_binding_allowed_now")
            is False,
        ),
        _check(
            "agent_bus_provider_canonical_authority_false",
            all(value is False for value in _authority().values()),
        ),
    ]
    ready = not blockers
    status = (
        "profile_toolset_activation_design_ready_no_activation"
        if ready
        else "blocked_profile_toolset_activation_design"
    )
    return {
        "ok": ready,
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "vault_root": str(root),
        "actor": actor_value,
        "activation_approval_id": activation_approval_id,
        "activation_approval_preview_id": activation_preview_id,
        "approval_status": readiness.get("approval_status"),
        "profile_id": profile_id,
        "toolset_id": toolset_id,
        "profile_toolset_activation_design_status": status,
        "blockers": blockers,
        "ready_for_profile_toolset_activation_write_guard_next_pass": ready,
        "profile_toolset_activation_design_available": True,
        "profile_toolset_activation_write_guard_available": True,
        "terminal_toolset_binding_design_available": False,
        "activation_allowed": False,
        "activation_performed": False,
        "live_runtime_activated": False,
        "runtime_activation_now": False,
        "profile_activation_now": False,
        "toolset_activation_now": False,
        "terminal_binding_now": False,
        "writes_performed": False,
        "files_modified": False,
        "approval_status_mutated": False,
        "approval_consumed_now": False,
        "profile_activation_marker_written_now": False,
        "profile_activation_state_written_now": False,
        "toolset_activation_state_written_now": False,
        "profile_toolset_activation_audit_written_now": False,
        "profile_view": profile or {},
        "toolset_view": toolset or {},
        "profile_validation": profile_validation,
        "toolset_validation": toolset_validation,
        "activation_state_readiness": {
            "surface": readiness.get("surface"),
            "ok": readiness.get("ok"),
            "status": readiness.get("activation_state_readiness_status"),
            "ready_for_next_pass": readiness.get(
                "ready_for_profile_toolset_activation_design_next_pass"
            ),
            "runtime_activation_marker": readiness.get("runtime_activation_marker"),
            "runtime_activation_state": readiness.get("runtime_activation_state"),
            "runtime_activation_audit": readiness.get("runtime_activation_audit"),
        },
        "future_profile_toolset_activation_artifacts": future_artifacts,
        "future_write_guard_contract": {
            "contract_status": "design_complete_write_guard_available",
            "exact_once_marker_required": True,
            "operator_confirmation_required": True,
            "approval_status_mutation_allowed": False,
            "approval_consumption_allowed": False,
            "runtime_activation_allowed": False,
            "profile_activation_state_write_scope": (
                "future_marker_profile_state_toolset_state_and_append_only_audit_only"
            ),
            "must_verify_before_write": [
                "activation_state_readiness_ok",
                "runtime_activation_marker_loaded",
                "runtime_activation_state_loaded",
                "runtime_activation_executor_audit_event_found",
                "profile_view_descriptive_only",
                "toolset_view_non_executing",
                "terminal_binding_still_future_gated",
                "no_agent_bus_or_provider_scope_requested",
            ],
        },
        "design_checks": design_checks,
        "terminal_binding_design": _terminal_binding_design(toolset_id),
        "blocked_actions": _blocked_actions(),
        "denied_effects": _blocked_actions(),
        "authority": _authority(),
        "terminal_output_trusted": False,
        "trust_tier": "Tier 4",
        "warnings": [
            "profile_toolset_activation_design_only_no_activation",
            "no_profile_or_toolset_executable_activation",
            "no_terminal_to_chaser_binding",
            "no_terminal_execution",
            "no_studio_execution",
            "no_agent_bus_write_or_claim",
            "no_provider_call",
            "terminal_output_remains_tier4_untrusted",
        ],
        "next_recommended_pass": NEXT_PASS,
        "boundary": (
            "profile/toolset activation design only; reads N25 readiness and "
            "descriptive profile/toolset views, previews future write-guard "
            "artifacts, and performs no activation, terminal binding, terminal "
            "execution, Agent Bus mutation, provider call, host mutation, or "
            "canonical writeback."
        ),
    }
