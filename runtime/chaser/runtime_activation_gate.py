"""Read-only ChaserAgent runtime activation gate design.

This module defines the approval-gated contract that must exist before any
future ChaserAgent runtime/profile/toolset activation can be implemented. It is
design/readback only: it writes no approvals, consumes no approvals, activates
no runtime, binds no terminal toolset, writes no Agent Bus tasks, calls no
provider, and mutates no canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.chaser.profiles import list_profiles, validate_profile_view
from runtime.chaser.runtime_readiness import build_chaser_runtime_readiness
from runtime.chaser.toolsets import list_toolsets, validate_toolset_view


SURFACE = "chaser_runtime_activation_gate_design"
SCHEMA_VERSION = "chaser_runtime_activation_gate_design.v1"


def _authority() -> dict[str, bool]:
    return {
        "runtime_activation_now": False,
        "profile_activation_now": False,
        "toolset_activation_now": False,
        "terminal_toolset_binding_now": False,
        "studio_execution_now": False,
        "terminal_execution_now": False,
        "approval_queue_write_now": False,
        "approval_consumption_now": False,
        "agent_bus_write_now": False,
        "agent_bus_claim_now": False,
        "provider_call_now": False,
        "canonical_writeback_now": False,
        "external_network_now": False,
        "host_mutation_now": False,
    }


def _profile_map() -> dict[str, dict[str, Any]]:
    return {str(item.get("profile_id") or ""): item for item in list_profiles()}


def _toolset_map() -> dict[str, dict[str, Any]]:
    return {str(item.get("toolset_id") or ""): item for item in list_toolsets()}


def _normalize(value: str | None, default: str) -> str:
    return str(value or default).strip().lower()


def _terminal_binding_contract(toolset_id: str) -> dict[str, Any]:
    terminal_related = toolset_id == "terminal-preview"
    return {
        "toolset_id": toolset_id,
        "terminal_related": terminal_related,
        "terminal_binding_allowed_now": False,
        "terminal_execution_allowed_now": False,
        "studio_terminal_execution_allowed_now": False,
        "allowed_future_terminal_mode": (
            "read_only_policy_preview_and_audit_history_only"
            if terminal_related
            else "no_terminal_access_requested"
        ),
        "write_capable_terminal_lane": (
            "future_separate_n6_gate_required"
            if terminal_related
            else "not_requested"
        ),
        "must_preserve": [
            "no_unrestricted_shell",
            "no_shell_operators_or_elevation",
            "terminal_output_remains_tier_4_untrusted",
            "studio_cannot_execute_terminal_commands",
            "approved_terminal_writes_remain_dedicated_cli_or_separately_gated_runtime_lane",
            "agent_bus_mutation_requires_separate_gate",
            "provider_dispatch_requires_separate_gate",
        ],
    }


def build_chaser_runtime_activation_gate_design(
    vault_root: str | Path,
    *,
    profile_id: str = "ops",
    toolset_id: str = "terminal-preview",
) -> dict[str, Any]:
    """Return the no-write activation gate design for future ChaserAgent wiring."""

    root = Path(vault_root).resolve()
    requested_profile = _normalize(profile_id, "ops")
    requested_toolset = _normalize(toolset_id, "terminal-preview")
    profiles = _profile_map()
    toolsets = _toolset_map()
    readiness = build_chaser_runtime_readiness(root)

    blockers: list[str] = []
    profile = profiles.get(requested_profile)
    toolset = toolsets.get(requested_toolset)
    if profile is None:
        blockers.append(f"unknown_profile:{requested_profile}")
    if toolset is None:
        blockers.append(f"unknown_toolset:{requested_toolset}")

    if profile is not None and validate_profile_view(profile).get("ok") is not True:
        blockers.append(f"profile_not_descriptive_only:{requested_profile}")
    if toolset is not None and validate_toolset_view(toolset).get("ok") is not True:
        blockers.append(f"toolset_not_non_executing:{requested_toolset}")
    if readiness.get("ok") is not True:
        blockers.append("runtime_readiness_contract_not_ok")

    design_ok = not blockers
    future_gate_blockers = [
        "terminal_toolset_binding_design_not_implemented",
        "terminal_toolset_binding_executor_not_implemented",
        "agent_bus_mutation_gate_not_implemented",
        "provider_dispatch_gate_not_implemented",
    ]

    return {
        "ok": design_ok,
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "vault_root": str(root),
        "design_status": "design_ready_no_activation" if design_ok else "design_blocked",
        "live_runtime_ready": False,
        "ready_for_activation_now": False,
        "ready_to_write_activation_request_now": design_ok,
        "activation_request_write_available": True,
        "activation_approval_decision_preflight_available": True,
        "activation_approval_consumption_design_available": True,
        "activation_approval_consumption_write_guard_available": True,
        "activation_post_consumption_readiness_available": True,
        "activation_executor_design_available": True,
        "activation_executor_write_guard_available": True,
        "activation_state_readiness_available": True,
        "profile_toolset_activation_design_available": True,
        "profile_toolset_activation_write_guard_available": True,
        "profile_toolset_activation_readiness_available": True,
        "terminal_toolset_binding_design_available": False,
        "terminal_toolset_binding_write_guard_available": False,
        "activation_approval_consumption_available": True,
        "activation_approval_consumption_scope": (
            "exact_once_marker_and_append_only_audit_only"
        ),
        "authority": _authority(),
        "requested_activation": {
            "runtime_id": "chaser",
            "profile_id": requested_profile,
            "toolset_id": requested_toolset,
            "profile_known": profile is not None,
            "toolset_known": toolset is not None,
            "profile_status": (profile or {}).get("status"),
            "toolset_status": (toolset or {}).get("status"),
        },
        "readiness_dependency": {
            "surface": readiness.get("surface"),
            "ok": readiness.get("ok"),
            "review_status": readiness.get("review_status"),
            "contract_summary": readiness.get("contract_summary"),
            "live_runtime_ready": readiness.get("live_runtime_ready"),
            "blockers_for_live_wiring": readiness.get("blockers_for_live_wiring") or [],
        },
        "activation_gate_contract": {
            "contract_status": "design_only",
            "approval_required_before_any_activation": True,
            "approval_request_writer_available_now": True,
            "approval_decision_preflight_available_now": True,
            "approval_consumption_design_available_now": True,
            "approval_consumption_write_guard_available_now": True,
            "approval_consumption_available_now": True,
            "approval_consumption_scope": (
                "exact_once_marker_and_append_only_audit_only"
            ),
            "activation_executor_design_available_now": True,
            "activation_executor_write_guard_available_now": True,
            "activation_state_readiness_available_now": True,
            "profile_toolset_activation_design_available_now": True,
            "profile_toolset_activation_write_guard_available_now": True,
            "profile_toolset_activation_readiness_available_now": True,
            "terminal_toolset_binding_design_available_now": False,
            "terminal_toolset_binding_write_guard_available_now": False,
            "exact_once_marker_required": True,
            "operator_confirmation_required": True,
            "hermes_or_codex_review_recommended": True,
            "studio_may_preview_only": True,
            "allowed_future_request_fields": [
                "runtime_id",
                "profile_id",
                "toolset_id",
                "operator_intent",
                "activation_scope",
                "terminal_binding_mode",
                "agent_bus_mutation_requested",
                "provider_dispatch_requested",
                "evidence_refs",
                "authority_ceiling",
            ],
            "required_evidence_refs": [
                "chaser_runtime_readiness_ok",
                "terminal_authority_audit_pass",
                "profile_view_validation_ok",
                "toolset_view_validation_ok",
                "operator_activation_intent",
                "no_studio_execution_contract",
                "no_provider_or_agent_bus_mutation_without_separate_gate",
            ],
        },
        "gate_phases": [
            {
                "phase": "design_readback",
                "implemented_now": True,
                "writes_now": False,
                "executes_now": False,
            },
            {
                "phase": "activation_approval_request_preview",
                "implemented_now": True,
                "writes_now": False,
                "executes_now": False,
            },
            {
                "phase": "activation_approval_request_write",
                "implemented_now": True,
                "writes_now": True,
                "executes_now": False,
            },
            {
                "phase": "activation_approval_decision_preflight",
                "implemented_now": True,
                "writes_now": False,
                "executes_now": False,
            },
            {
                "phase": "activation_approval_consumption_design",
                "implemented_now": True,
                "writes_now": False,
                "executes_now": False,
            },
            {
                "phase": "activation_approval_consumption_write_guard",
                "implemented_now": True,
                "writes_now": True,
                "executes_now": False,
            },
            {
                "phase": "activation_post_consumption_readiness",
                "implemented_now": True,
                "writes_now": False,
                "executes_now": False,
            },
            {
                "phase": "activation_executor_design",
                "implemented_now": True,
                "writes_now": False,
                "executes_now": False,
            },
            {
                "phase": "activation_executor_write_guard",
                "implemented_now": True,
                "writes_now": True,
                "executes_now": False,
            },
            {
                "phase": "activation_state_readiness",
                "implemented_now": True,
                "writes_now": False,
                "executes_now": False,
            },
            {
                "phase": "profile_toolset_activation_design",
                "implemented_now": True,
                "writes_now": False,
                "executes_now": False,
            },
            {
                "phase": "profile_toolset_activation_write_guard",
                "implemented_now": True,
                "writes_now": True,
                "executes_now": False,
            },
            {
                "phase": "profile_toolset_activation_readiness",
                "implemented_now": True,
                "writes_now": False,
                "executes_now": False,
            },
            {
                "phase": "terminal_toolset_binding_design",
                "implemented_now": False,
                "writes_now": False,
                "executes_now": False,
            },
            {
                "phase": "terminal_toolset_binding_write_guard",
                "implemented_now": False,
                "writes_now": False,
                "executes_now": False,
            },
        ],
        "terminal_binding_contract": _terminal_binding_contract(requested_toolset),
        "future_gate_blockers": list(future_gate_blockers),
        "blockers": blockers,
        "warnings": [
            "design_only_no_runtime_activation",
            "no_activation_approval_request_written",
            "no_approval_consumption",
            "chaser_terminal_toolset_binding_deferred_until_human_studio_terminal",
            "no_agent_bus_or_provider_authority",
            "terminal_output_and_tool_output_remain_tier_4_untrusted",
        ],
        "next_recommended_pass": (
            "terminal-n29-studio-full-terminal-product-contract"
        ),
    }
