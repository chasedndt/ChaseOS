"""N23 ChaserAgent runtime activation executor design.

This read-only surface composes N22 post-consumption readiness and defines the
future activation executor contract. It performs no runtime/profile/toolset
activation, writes no activation state, binds no terminal tools, executes no
terminal command, writes no Agent Bus state, calls no provider, and mutates no
canonical state.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.chaser.runtime_activation_post_consumption_readiness import (
    build_chaser_runtime_activation_post_consumption_readiness,
)


SURFACE = "chaser_runtime_activation_executor_design"
SCHEMA_VERSION = "chaser_runtime_activation_executor_design.v1"
NEXT_PASS = "terminal-n24-chaser-runtime-activation-executor-write-guard"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_component(value: str) -> str:
    text = "".join(c if c.isalnum() or c in {"-", "_"} else "-" for c in value)
    text = "-".join(part for part in text.split("-") if part)
    return text[:96] or "unknown"


def _activation_slug(approval_id: str, preview_id: str) -> str:
    digest = hashlib.sha256(f"{approval_id}|{preview_id}".encode("utf-8")).hexdigest()[:12]
    return f"chaser-runtime-activation-{_safe_component(approval_id)}-{digest}"


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
        "activation_state_write_now": False,
        "activation_audit_write_now": False,
        "agent_bus_write_now": False,
        "agent_bus_claim_now": False,
        "provider_call_now": False,
        "canonical_writeback_now": False,
        "external_network_now": False,
        "host_mutation_now": False,
    }


def _blocked_actions() -> list[str]:
    return [
        "write activation state",
        "write runtime activation marker",
        "append runtime activation audit event",
        "mutate approval request status",
        "activate ChaserAgent runtime",
        "activate Chaser profile",
        "activate Chaser toolset",
        "bind terminal tools to ChaserAgent",
        "execute terminal command",
        "expose Studio terminal execution",
        "write or claim Agent Bus tasks",
        "call provider or model APIs",
        "write canonical ChaseOS memory/state",
        "mutate host startup/autostart/service state",
    ]


def _rel(root: Path, *parts: str) -> str:
    return (root.joinpath(*parts)).relative_to(root).as_posix()


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "required": True,
        "status": "passed" if passed else "blocked",
        "detail": detail,
    }


def build_chaser_runtime_activation_executor_design(
    vault_root: str | Path,
    approval_id: str,
    *,
    expected_preview_id: str = "",
    actor: str = "operator",
    request_agent_bus_mutation: bool = False,
    request_provider_dispatch: bool = False,
) -> dict[str, Any]:
    """Design the future activation executor without writing or activating."""

    root = Path(vault_root).resolve()
    requested_id = str(approval_id or "").strip()
    actor_value = actor or "operator"
    readiness = build_chaser_runtime_activation_post_consumption_readiness(
        root,
        requested_id,
        expected_preview_id=expected_preview_id,
        actor=actor_value,
    )
    activation_approval_id = str(readiness.get("activation_approval_id") or requested_id)
    preview_id = str(readiness.get("activation_approval_preview_id") or "")
    profile_id = str(readiness.get("profile_id") or "unknown")
    toolset_id = str(readiness.get("toolset_id") or "unknown")
    slug = _activation_slug(activation_approval_id, preview_id)
    marker_rel = _rel(root, "runtime", "chaser", "runtime-activation-markers", f"{slug}.json")
    state_rel = _rel(root, "runtime", "chaser", "activation-state", f"{slug}.json")
    audit_rel = _rel(root, "07_LOGS", "Chaser-Activation", "runtime-activation-executor.jsonl")

    blockers: list[str] = []
    if readiness.get("ok") is not True:
        blockers.append("post_consumption_readiness_not_ready")
        blockers.extend(str(item) for item in readiness.get("blockers") or [])
    if request_agent_bus_mutation:
        blockers.append("agent_bus_mutation_not_in_activation_executor_scope")
    if request_provider_dispatch:
        blockers.append("provider_dispatch_not_in_activation_executor_scope")

    checks = [
        _check(
            "post_consumption_readiness_ready",
            readiness.get("ok") is True,
            str(readiness.get("post_consumption_readiness_status") or "missing"),
        ),
        _check(
            "activation_approval_is_approved",
            readiness.get("approval_status") == "approved",
            str(readiness.get("approval_status") or "missing"),
        ),
        _check(
            "consumption_marker_loaded",
            (readiness.get("exact_once_marker") or {}).get("loaded") is True,
            str((readiness.get("exact_once_marker") or {}).get("path") or ""),
        ),
        _check(
            "consumption_audit_matching_event_found",
            (readiness.get("activation_audit") or {}).get("matching_event_found") is True,
            str((readiness.get("activation_audit") or {}).get("path") or ""),
        ),
        _check(
            "terminal_binding_excluded_from_activation_executor",
            True,
            "terminal binding remains a separate future gate",
        ),
        _check(
            "agent_bus_and_provider_excluded",
            not request_agent_bus_mutation and not request_provider_dispatch,
            "Agent Bus mutation and provider dispatch require separate future gates",
        ),
    ]
    ready_for_next = not blockers and all(item["passed"] for item in checks)
    status = (
        "activation_executor_design_ready_no_activation"
        if ready_for_next
        else "blocked_activation_executor_design"
    )
    future_activation_record_schema = {
        "record_type": "chaser_runtime_activation_state",
        "schema_version": "chaser_runtime_activation_state.v1",
        "runtime_id": "chaser",
        "profile_id": profile_id,
        "toolset_id": toolset_id,
        "activation_approval_id": activation_approval_id,
        "activation_approval_preview_id": preview_id or None,
        "post_consumption_readiness_status": readiness.get(
            "post_consumption_readiness_status"
        ),
        "terminal_binding_performed": False,
        "terminal_execution_performed": False,
        "agent_bus_mutation_performed": False,
        "provider_call_performed": False,
        "canonical_writeback_performed": False,
        "activated_at": "future_iso_timestamp",
        "activated_by": actor_value,
    }
    return {
        "ok": ready_for_next,
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "vault_root": str(root),
        "activation_approval_id": activation_approval_id,
        "activation_approval_preview_id": preview_id or None,
        "approval_path": readiness.get("approval_path"),
        "approval_status": readiness.get("approval_status"),
        "profile_id": profile_id,
        "toolset_id": toolset_id,
        "actor": actor_value,
        "activation_executor_design_status": status,
        "blockers": blockers,
        "ready_for_activation_executor_write_guard_next_pass": ready_for_next,
        "activation_executor_design_available": True,
        "activation_executor_available": False,
        "activation_executor_write_guard_available": True,
        "activation_allowed": False,
        "activation_performed": False,
        "runtime_activation_now": False,
        "profile_activation_now": False,
        "toolset_activation_now": False,
        "terminal_binding_now": False,
        "terminal_binding_allowed_in_activation_executor": False,
        "terminal_execution_allowed_in_activation_executor": False,
        "studio_execution_allowed_in_activation_executor": False,
        "writes_performed": False,
        "files_modified": False,
        "approval_status_mutated": False,
        "approval_consumed_now": False,
        "future_activation_marker_preview": {
            "path": marker_rel,
            "exists": (root / marker_rel).exists(),
            "create_new_only": True,
            "exact_once": True,
            "written_in_this_pass": False,
        },
        "future_activation_state_preview": {
            "path": state_rel,
            "exists": (root / state_rel).exists(),
            "write_scope": "future_activation_state_record_only",
            "written_in_this_pass": False,
        },
        "future_activation_audit_preview": {
            "path": audit_rel,
            "event_type": "chaser_runtime_activation_executor",
            "append_only": True,
            "written_in_this_pass": False,
        },
        "future_activation_record_schema": future_activation_record_schema,
        "future_executor_sequence": [
            {
                "order": 1,
                "step_id": "rerun_post_consumption_readiness",
                "effect": "read_only",
                "allowed_in_this_pass": True,
            },
            {
                "order": 2,
                "step_id": "create_exact_once_runtime_activation_marker",
                "effect": "future_scoped_write",
                "allowed_in_this_pass": False,
            },
            {
                "order": 3,
                "step_id": "write_runtime_activation_state_record",
                "effect": "future_scoped_write",
                "allowed_in_this_pass": False,
            },
            {
                "order": 4,
                "step_id": "append_runtime_activation_audit_event",
                "effect": "future_scoped_audit_write",
                "allowed_in_this_pass": False,
            },
            {
                "order": 5,
                "step_id": "stop_before_terminal_binding",
                "effect": "stop_condition",
                "allowed_in_this_pass": True,
            },
        ],
        "executor_design_checks": checks,
        "post_consumption_readiness": {
            "surface": readiness.get("surface"),
            "ok": readiness.get("ok"),
            "post_consumption_readiness_status": readiness.get(
                "post_consumption_readiness_status"
            ),
            "approval_status": readiness.get("approval_status"),
            "ready_for_activation_executor_next_pass": readiness.get(
                "ready_for_activation_executor_next_pass"
            ),
            "blockers": readiness.get("blockers") or [],
        },
        "activation_stop_conditions": [
            "terminal_binding_requires_separate_future_gate",
            "terminal_execution_requires_separate_terminal_tool_binding_gate",
            "studio_execution_remains_unavailable",
            "agent_bus_mutation_requires_separate_future_gate",
            "provider_dispatch_requires_separate_future_gate",
            "canonical_writeback_requires_separate_future_gate",
        ],
        "blocked_actions": _blocked_actions(),
        "denied_effects": _blocked_actions(),
        "authority": _authority(),
        "terminal_output_trusted": False,
        "trust_tier": "Tier 4",
        "warnings": [
            "activation_executor_design_only_no_activation",
            "no_activation_state_write",
            "no_profile_or_toolset_activation",
            "no_terminal_to_chaser_binding",
            "no_terminal_execution",
            "no_studio_execution",
            "no_agent_bus_write_or_claim",
            "no_provider_call",
            "terminal_output_remains_tier4_untrusted",
        ],
        "next_recommended_pass": NEXT_PASS,
        "boundary": (
            "activation executor design only; reads N22 post-consumption "
            "readiness and defines future exact-once activation marker, state "
            "record, and audit writes. It performs no activation, terminal "
            "binding, terminal execution, Agent Bus mutation, provider call, "
            "host mutation, or canonical writeback."
        ),
    }
