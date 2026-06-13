"""Read-only ChaserAgent runtime wiring readiness review.

This surface consolidates the current terminal, board, gateway, profile, and
toolset contracts before live ChaserAgent runtime wiring. It does not activate
ChaserAgent, bind terminal tools, write Agent Bus tasks, consume approvals,
execute shell commands, call providers, or mutate canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.chaser.board import board_authority
from runtime.chaser.gateway import build_gateway_ingress_contract
from runtime.chaser.policies import build_no_authority_report, build_policy_snapshot
from runtime.chaser.profiles import list_profiles, validate_profile_view
from runtime.chaser.terminal_authority_audit import build_terminal_authority_audit
from runtime.chaser.toolsets import list_toolsets, validate_toolset_view


SURFACE = "chaser_runtime_readiness_review"
SCHEMA_VERSION = "chaser_runtime_readiness_review.v1"

_SAFETY_AUTHORITY_KEYS = (
    "studio_execution_now",
    "terminal_execution_now",
    "approval_queue_write_now",
    "approval_consumption_now",
    "agent_bus_write_now",
    "provider_call_now",
    "canonical_writeback_now",
    "host_mutation_now",
)

_LIVE_WIRING_BLOCKERS = (
    "chaser_runtime_adapter_not_installed",
    "terminal_toolset_binding_not_implemented",
    "agent_bus_task_mutation_from_chaser_not_authorized",
    "provider_runtime_dispatch_not_authorized",
    "external_gateway_ingress_not_implemented",
    "live_runtime_activation_approval_gate_not_implemented",
)


def _authority_flags() -> dict[str, bool]:
    return {
        "chaser_agent_live_runtime_wired": False,
        "profile_activation_allowed": False,
        "toolset_activation_allowed": False,
        "terminal_toolset_runtime_binding_allowed": False,
        "studio_execution_now": False,
        "terminal_execution_now": False,
        "approval_queue_write_now": False,
        "approval_consumption_now": False,
        "agent_bus_write_now": False,
        "provider_call_now": False,
        "canonical_writeback_now": False,
        "host_mutation_now": False,
        "external_network_now": False,
    }


def _check(
    name: str,
    ok: bool,
    detail: str,
    *,
    evidence: dict[str, Any] | None = None,
    blockers: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "ok": bool(ok),
        "status": "passed" if ok else "blocked",
        "detail": detail,
        "blockers": list(blockers or []),
        "evidence": dict(evidence or {}),
    }


def _all_false(source: dict[str, Any], keys: tuple[str, ...]) -> tuple[bool, list[str]]:
    true_keys = [key for key in keys if source.get(key) is True]
    return not true_keys, true_keys


def _count_by(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


def build_chaser_runtime_readiness(vault_root: str | Path) -> dict[str, Any]:
    """Build a no-mutation readiness review for future ChaserAgent wiring."""

    root = Path(vault_root).resolve()
    profiles = list_profiles()
    toolsets = list_toolsets()
    profile_validations = [
        {"profile_id": profile.get("profile_id"), **validate_profile_view(profile)}
        for profile in profiles
    ]
    toolset_validations = [
        {"toolset_id": toolset.get("toolset_id"), **validate_toolset_view(toolset)}
        for toolset in toolsets
    ]

    policy = build_policy_snapshot()
    board = board_authority()
    gateway = build_gateway_ingress_contract(root)
    audit = build_terminal_authority_audit(root)

    policy_ok = policy.get("available_for_runtime_activation") is False and all(
        value is False for value in (policy.get("authority") or {}).values()
    )
    board_ok, board_true = _all_false(
        board,
        (
            "terminal_execution",
            "write_capable_terminal_lane",
            "approval_queue_write",
            "approval_consumption",
            "agent_bus_writes",
            "provider_calls",
            "canonical_writeback",
            "profile_activation",
            "toolset_activation",
        ),
    )
    gateway_authority = gateway.get("authority") if isinstance(gateway.get("authority"), dict) else {}
    gateway_ok, gateway_true = _all_false(gateway_authority, _SAFETY_AUTHORITY_KEYS)
    audit_authority = audit.get("authority") if isinstance(audit.get("authority"), dict) else {}
    audit_authority_ok, audit_true = _all_false(audit_authority, _SAFETY_AUTHORITY_KEYS)
    profiles_ok = all(item.get("ok") is True for item in profile_validations)
    toolsets_ok = all(item.get("ok") is True for item in toolset_validations)

    contract_checks = [
        _check(
            "phase_a_policy_is_no_authority",
            policy_ok,
            "Chaser policy snapshot is descriptive only and unavailable for runtime activation.",
            evidence={"status": policy.get("status"), "available_for_runtime_activation": policy.get("available_for_runtime_activation")},
        ),
        _check(
            "board_authority_preserves_no_execution",
            board_ok,
            "Chaser board authority remains read-only/proposal-only.",
            evidence={"authority_summary": board},
            blockers=[f"board_authority_claims:{key}" for key in board_true],
        ),
        _check(
            "gateway_contract_preserves_no_runtime_mutation",
            gateway_ok,
            "N7 gateway contract does not expose live runtime, provider, Studio execution, or Agent Bus mutation authority.",
            evidence={"mode": gateway.get("mode"), "surface": gateway.get("surface")},
            blockers=[f"gateway_authority_claims:{key}" for key in gateway_true],
        ),
        _check(
            "terminal_authority_audit_passes",
            bool(audit.get("ok")) and audit_authority_ok,
            "N8 terminal authority audit confirms no execution or mutation side effects for inspected surfaces.",
            evidence={"summary": audit.get("summary"), "side_effects": audit.get("side_effects")},
            blockers=[f"terminal_authority_audit_claims:{key}" for key in audit_true],
        ),
        _check(
            "profile_views_descriptive_only",
            profiles_ok,
            "All Chaser profile views validate as descriptive only.",
            evidence={"profile_count": len(profiles), "statuses": _count_by(profiles, "status")},
            blockers=[
                f"profile_invalid:{item.get('profile_id')}:{','.join(item.get('errors') or [])}"
                for item in profile_validations
                if item.get("ok") is not True
            ],
        ),
        _check(
            "toolset_views_descriptive_only",
            toolsets_ok,
            "All Chaser toolset views validate as non-executing/non-writing views.",
            evidence={"toolset_count": len(toolsets), "statuses": _count_by(toolsets, "status")},
            blockers=[
                f"toolset_invalid:{item.get('toolset_id')}:{','.join(item.get('errors') or [])}"
                for item in toolset_validations
                if item.get("ok") is not True
            ],
        ),
    ]

    activation_gates = [
        {
            "name": "live_chaser_runtime_adapter",
            "satisfied": False,
            "blocker": "chaser_runtime_adapter_not_installed",
            "detail": "No live ChaserAgent runtime adapter is installed or activated.",
        },
        {
            "name": "profile_toolset_activation_design",
            "satisfied": True,
            "blocker": "",
            "detail": "Read-only profile/toolset activation design is available; it grants no runtime authority.",
        },
        {
            "name": "profile_toolset_activation_write_guard",
            "satisfied": True,
            "blocker": "",
            "detail": "Guarded profile/toolset activation marker/state/audit writer is available; it does not activate live runtime authority.",
        },
        {
            "name": "profile_toolset_activation_readiness",
            "satisfied": True,
            "blocker": "",
            "detail": "Read-only profile/toolset activation marker/state/audit readiness validator is available; it does not activate live runtime authority.",
        },
        {
            "name": "terminal_toolset_runtime_binding",
            "satisfied": False,
            "blocker": "terminal_toolset_binding_not_implemented",
            "detail": "No ChaserAgent tool binding may invoke terminal execution; terminal work is redirected to the human Studio terminal lane first.",
        },
        {
            "name": "agent_bus_mutation_gate",
            "satisfied": False,
            "blocker": "agent_bus_task_mutation_from_chaser_not_authorized",
            "detail": "ChaserAgent does not claim, write, or mutate Agent Bus tasks.",
        },
        {
            "name": "provider_runtime_dispatch_gate",
            "satisfied": False,
            "blocker": "provider_runtime_dispatch_not_authorized",
            "detail": "No provider/model dispatch is authorized for ChaserAgent runtime wiring.",
        },
        {
            "name": "external_gateway_ingress_gate",
            "satisfied": False,
            "blocker": "external_gateway_ingress_not_implemented",
            "detail": "Gateway ingress remains internal structured routing, not a network server.",
        },
        {
            "name": "live_runtime_activation_approval_gate",
            "satisfied": False,
            "blocker": "live_runtime_activation_approval_gate_not_implemented",
            "detail": "No approval workflow exists for enabling a live ChaserAgent runtime lane.",
        },
    ]

    failed_contracts = [item["name"] for item in contract_checks if item.get("ok") is not True]
    contract_ok = not failed_contracts
    no_authority = build_no_authority_report()

    return {
        "ok": contract_ok,
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "vault_root": str(root),
        "review_status": (
            "readiness_review_complete_live_wiring_blocked"
            if contract_ok
            else "readiness_review_contract_failure"
        ),
        "live_runtime_ready": False,
        "ready_for_runtime_activation": False,
        "read_only_review_available": True,
        "activation_gate_design_available": True,
        "activation_gate_design_surface": "chaser_runtime_activation_gate_design",
        "activation_approval_preview_available": True,
        "activation_approval_preview_surface": "chaser_runtime_activation_approval_preview",
        "activation_approval_request_write_available": True,
        "activation_approval_request_write_surface": (
            "chaser_runtime_activation_approval_request_write_gate"
        ),
        "activation_approval_decision_preflight_available": True,
        "activation_approval_decision_preflight_surface": (
            "chaser_runtime_activation_approval_decision_preflight"
        ),
        "activation_approval_consumption_design_available": True,
        "activation_approval_consumption_design_surface": (
            "chaser_runtime_activation_approval_consumption_design"
        ),
        "activation_approval_consumption_write_guard_available": True,
        "activation_approval_consumption_write_guard_surface": (
            "chaser_runtime_activation_approval_consumption_write_guard"
        ),
        "activation_post_consumption_readiness_available": True,
        "activation_post_consumption_readiness_surface": (
            "chaser_runtime_activation_post_consumption_readiness"
        ),
        "activation_executor_design_available": True,
        "activation_executor_design_surface": (
            "chaser_runtime_activation_executor_design"
        ),
        "activation_executor_write_guard_available": True,
        "activation_executor_write_guard_surface": (
            "chaser_runtime_activation_executor_write_guard"
        ),
        "activation_state_readiness_available": True,
        "activation_state_readiness_surface": (
            "chaser_runtime_activation_state_readiness"
        ),
        "profile_toolset_activation_design_available": True,
        "profile_toolset_activation_design_surface": (
            "chaser_runtime_profile_toolset_activation_design"
        ),
        "profile_toolset_activation_write_guard_available": True,
        "profile_toolset_activation_write_guard_surface": (
            "chaser_runtime_profile_toolset_activation_write_guard"
        ),
        "profile_toolset_activation_readiness_available": True,
        "profile_toolset_activation_readiness_surface": (
            "chaser_runtime_profile_toolset_activation_readiness"
        ),
        "terminal_toolset_binding_design_available": False,
        "terminal_toolset_binding_design_surface": "",
        "terminal_toolset_binding_write_guard_available": False,
        "terminal_toolset_binding_runtime_binding_available": False,
        "terminal_output_trusted": False,
        "trust_tier": "Tier 4",
        "authority": _authority_flags(),
        "chaser_no_authority": no_authority,
        "contract_summary": {
            "checks_total": len(contract_checks),
            "checks_passed": len(contract_checks) - len(failed_contracts),
            "checks_failed": len(failed_contracts),
            "failed_checks": failed_contracts,
            "status": "passed" if contract_ok else "blocked",
        },
        "contract_checks": contract_checks,
        "activation_posture": {
            "chaser_agent_live_runtime_wired": False,
            "studio_execution_allowed": False,
            "terminal_execution_allowed": False,
            "terminal_write_capable_lane_available_to_chaser": False,
            "approval_queue_write_allowed": True,
            "approval_queue_write_scope": "chaser_runtime_activation_approval_request_only",
            "approval_decision_preflight_allowed": True,
            "approval_decision_preflight_scope": "chaser_runtime_activation_approval_request_only",
            "approval_consumption_design_allowed": True,
            "approval_consumption_design_scope": "chaser_runtime_activation_approval_request_only",
            "approval_consumption_write_guard_allowed": True,
            "approval_consumption_write_guard_scope": (
                "exact_once_marker_and_append_only_audit_only"
            ),
            "approval_consumption_allowed": True,
            "approval_consumption_scope": "exact_once_marker_and_append_only_audit_only",
            "post_consumption_readiness_allowed": True,
            "post_consumption_readiness_scope": "read_only_marker_and_audit_validation_only",
            "activation_executor_design_allowed": True,
            "activation_executor_design_scope": "read_only_fail_closed_design_only",
            "activation_executor_write_guard_allowed": True,
            "activation_executor_write_guard_scope": (
                "exact_once_activation_marker_state_and_audit_only"
            ),
            "activation_state_readiness_allowed": True,
            "activation_state_readiness_scope": (
                "read_only_activation_marker_state_and_audit_validation_only"
            ),
            "profile_toolset_activation_design_allowed": True,
            "profile_toolset_activation_design_scope": (
                "read_only_profile_toolset_activation_design_only"
            ),
            "profile_toolset_activation_write_guard_allowed": True,
            "profile_toolset_activation_write_guard_scope": (
                "exact_once_marker_profile_state_toolset_state_and_append_only_audit_only"
            ),
            "profile_toolset_activation_readiness_allowed": True,
            "profile_toolset_activation_readiness_scope": (
                "read_only_profile_toolset_marker_state_and_audit_validation_only"
            ),
            "terminal_toolset_binding_design_allowed": False,
            "terminal_toolset_binding_design_scope": (
                "deferred_until_human_studio_terminal_foundation_exists"
            ),
            "terminal_toolset_binding_write_guard_allowed": False,
            "agent_bus_mutation_allowed": False,
            "provider_call_allowed": False,
            "canonical_writeback_allowed": False,
            "profile_activation_allowed": False,
            "toolset_activation_allowed": False,
            "network_gateway_server_allowed": False,
        },
        "activation_gates": activation_gates,
        "blockers_for_live_wiring": list(_LIVE_WIRING_BLOCKERS),
        "profiles": profiles,
        "profile_validations": profile_validations,
        "toolsets": toolsets,
        "toolset_validations": toolset_validations,
        "gateway_contract": {
            "surface": gateway.get("surface"),
            "mode": gateway.get("mode"),
            "authority": gateway_authority,
            "supported_intents": gateway.get("supported_intents") or [],
        },
        "terminal_authority_audit": {
            "ok": audit.get("ok"),
            "surface": audit.get("surface"),
            "summary": audit.get("summary"),
            "authority": audit_authority,
            "side_effects": audit.get("side_effects"),
        },
        "warnings": [
            "readiness_review_only_no_chaser_runtime_activation",
            "no_studio_execution_api_added",
            "chaser_terminal_toolset_binding_deferred_until_human_studio_terminal",
            "no_agent_bus_writes_or_provider_calls",
            "terminal_output_and_terminal_intent_remain_tier_4_untrusted",
        ],
        "next_recommended_pass": (
            "terminal-n29-studio-full-terminal-product-contract"
        ),
    }
