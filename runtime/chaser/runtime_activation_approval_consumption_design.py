"""No-mutation ChaserAgent runtime activation approval consumption design.

This is N20: it defines the future exact-once consumer marker, audit record,
and stop conditions after an approved N19 preflight. It never consumes an
approval, writes a marker, activates ChaserAgent, binds terminal tools, executes
terminal commands, writes Agent Bus state, calls providers, or mutates canonical
ChaseOS state.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.chaser.runtime_activation_approval_decision_preflight import (
    build_chaser_runtime_activation_approval_decision_preflight,
)


SURFACE = "chaser_runtime_activation_approval_consumption_design"
SCHEMA_VERSION = "chaser_runtime_activation_approval_consumption_design.v1"


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
        "activation_audit_write_now": False,
        "agent_bus_write_now": False,
        "agent_bus_claim_now": False,
        "provider_call_now": False,
        "canonical_writeback_now": False,
        "external_network_now": False,
        "host_mutation_now": False,
    }


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "required": True,
        "status": "passed" if passed else "blocked",
        "detail": detail,
    }


def _safe_component(value: str) -> str:
    text = "".join(c if c.isalnum() or c in {"-", "_"} else "-" for c in value)
    text = "-".join(part for part in text.split("-") if part)
    return text[:96] or "unknown"


def _marker_slug(approval_id: str, preview_id: str) -> str:
    digest = hashlib.sha256(f"{approval_id}|{preview_id}".encode("utf-8")).hexdigest()[:12]
    return f"chaser-activation-consumption-{_safe_component(approval_id)}-{digest}"


def _denied_effects() -> list[str]:
    return [
        "write activation approval consumption marker",
        "append activation approval consumption audit",
        "mutate approval request status",
        "consume activation approval request",
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


def build_chaser_runtime_activation_approval_consumption_design(
    vault_root: str | Path,
    approval_id: str,
    *,
    expected_preview_id: str = "",
    actor: str = "operator",
) -> dict[str, Any]:
    """Return a no-write design for the future activation approval consumer."""

    root = Path(vault_root).resolve()
    preflight = build_chaser_runtime_activation_approval_decision_preflight(
        root,
        approval_id,
        expected_preview_id=expected_preview_id,
    )
    requested_id = str(approval_id or "").strip()
    preview_id = str(preflight.get("activation_approval_preview_id") or "")
    marker_slug = _marker_slug(requested_id, preview_id)
    marker_path = (
        root
        / "runtime"
        / "chaser"
        / "activation-consumption-markers"
        / f"{marker_slug}.json"
    )
    audit_path = (
        root
        / "07_LOGS"
        / "Chaser-Activation"
        / "activation-approval-consumption.jsonl"
    )
    marker_rel = marker_path.relative_to(root).as_posix()
    audit_rel = audit_path.relative_to(root).as_posix()
    preflight_ok = preflight.get("ok") is True
    preflight_ready = preflight.get("ready_for_activation_consumer_next_pass") is True
    approval_status = str(preflight.get("approval_status") or "missing")
    marker_exists = marker_path.exists()
    checks = [
        _check(
            "decision_preflight_loaded",
            preflight_ok,
            str(preflight.get("decision_preflight_status") or "missing"),
        ),
        _check(
            "activation_approval_is_approved",
            approval_status == "approved",
            approval_status,
        ),
        _check(
            "decision_preflight_ready_for_consumer_review",
            preflight_ready,
            str(preflight.get("ready_for_activation_consumer_next_pass")),
        ),
        _check(
            "exact_once_marker_path_scoped_to_vault",
            marker_path.resolve().is_relative_to(root),
            marker_rel,
        ),
        _check(
            "exact_once_marker_not_written",
            not marker_exists,
            f"exists={marker_exists}",
        ),
        _check(
            "design_stops_before_runtime_activation",
            True,
            "future consumer design stops before activation/profile/toolset/binding executors",
        ),
        _check(
            "design_preserves_no_agent_bus_or_provider_authority",
            True,
            "Agent Bus mutation and provider dispatch require separate future gates",
        ),
    ]
    required_checks_pass = all(item["passed"] for item in checks if item.get("required"))
    if not preflight_ok:
        design_status = (
            "blocked_activation_approval_consumption_design_preflight_unavailable"
        )
        review_decision = "blocked_before_consumption_design"
    elif not preflight_ready:
        design_status = (
            "blocked_activation_approval_consumption_design_preflight_not_approved"
        )
        review_decision = "blocked_until_activation_approval_approved"
    elif marker_exists:
        design_status = "blocked_activation_approval_consumption_design_marker_exists"
        review_decision = "blocked_existing_consumption_marker"
    else:
        design_status = "activation_approval_consumption_design_ready_no_mutation"
        review_decision = "consumer_design_ready_for_future_write_guard"

    consumer_record_schema = {
        "record_type": "chaser_runtime_activation_approval_consumption",
        "schema_version": "chaser_runtime_activation_approval_consumption_marker.v1",
        "runtime_id": "chaser",
        "profile_id": preflight.get("profile_id"),
        "toolset_id": preflight.get("toolset_id"),
        "activation_approval_id": preflight.get("activation_approval_id") or requested_id,
        "activation_approval_preview_id": preview_id,
        "approval_status_required": "approved",
        "approval_consumed_at": "future_iso_timestamp",
        "approval_consumed_by": actor or "operator",
        "decision_preflight_status": (
            "activation_approval_decision_preflight_ready_no_mutation"
        ),
        "terminal_binding_mode": preflight.get("terminal_binding_mode"),
        "terminal_output_trusted": False,
        "trust_tier": "Tier 4",
        "runtime_activation_performed": False,
        "profile_activation_performed": False,
        "toolset_activation_performed": False,
        "terminal_binding_performed": False,
        "agent_bus_mutation_performed": False,
        "provider_call_performed": False,
        "canonical_writeback_performed": False,
    }
    future_consumer_sequence = [
        {
            "order": 1,
            "step_id": "rerun_activation_approval_decision_preflight",
            "effect": "read_only",
            "required": True,
            "allowed_in_this_pass": False,
        },
        {
            "order": 2,
            "step_id": "verify_approval_status_is_approved",
            "effect": "read_only",
            "required": True,
            "allowed_in_this_pass": False,
        },
        {
            "order": 3,
            "step_id": "create_exact_once_activation_consumption_marker",
            "effect": "future_scoped_write",
            "required": True,
            "allowed_in_this_pass": False,
        },
        {
            "order": 4,
            "step_id": "append_activation_consumption_audit_event",
            "effect": "future_scoped_audit_write",
            "required": True,
            "allowed_in_this_pass": False,
        },
        {
            "order": 5,
            "step_id": "stop_before_chaser_runtime_activation",
            "effect": "stop_condition",
            "required": True,
            "allowed_in_this_pass": False,
        },
    ]
    return {
        "ok": preflight_ok,
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "vault_root": str(root),
        "activation_approval_id": preflight.get("activation_approval_id") or requested_id,
        "activation_approval_preview_id": preview_id or None,
        "approval_path": preflight.get("approval_path"),
        "approval_status": approval_status,
        "profile_id": preflight.get("profile_id"),
        "toolset_id": preflight.get("toolset_id"),
        "actor": actor or "operator",
        "consumption_design_status": design_status,
        "review_decision": review_decision,
        "decision_preflight_status": preflight.get("decision_preflight_status"),
        "decision_preflight_ready": preflight_ready,
        "ready_for_activation_consumption_write_guard_next_pass": (
            required_checks_pass and design_status == "activation_approval_consumption_design_ready_no_mutation"
        ),
        "activation_approval_consumption_design_available": True,
        "activation_approval_consumption_executor_available": False,
        "activation_approval_consumption_available": False,
        "activation_consumer_implemented": False,
        "consumer_record_schema": consumer_record_schema,
        "consumer_marker_preview": {
            "path": marker_rel,
            "exists": marker_exists,
            "create_new_only": True,
            "exact_once": True,
            "written_in_this_pass": False,
        },
        "audit_event_preview": {
            "path": audit_rel,
            "event_type": "chaser_runtime_activation_approval_consumption",
            "append_only": True,
            "written_in_this_pass": False,
        },
        "future_consumer_sequence": future_consumer_sequence,
        "activation_stop_conditions": [
            "stop_after_marker_and_audit_before_runtime_activation",
            "profile_activation_requires_separate_future_state_writer",
            "toolset_activation_requires_separate_future_state_writer",
            "terminal_binding_requires_separate_future_executor",
            "agent_bus_mutation_requires_separate_future_gate",
            "provider_dispatch_requires_separate_future_gate",
        ],
        "consumption_design_checks": checks,
        "decision_preflight": {
            "surface": preflight.get("surface"),
            "ok": preflight.get("ok"),
            "decision_preflight_status": preflight.get("decision_preflight_status"),
            "approval_status": preflight.get("approval_status"),
            "ready_for_activation_consumer_next_pass": preflight.get(
                "ready_for_activation_consumer_next_pass"
            ),
            "blockers": preflight.get("blockers") or [],
        },
        "approval_decision_written": False,
        "approval_status_mutated": False,
        "approval_consumed": False,
        "activation_consumption_marker_written": False,
        "activation_audit_written": False,
        "activation_allowed": False,
        "activation_performed": False,
        "runtime_activation_now": False,
        "profile_activation_now": False,
        "toolset_activation_now": False,
        "terminal_binding_now": False,
        "writes_performed": False,
        "files_modified": False,
        "blocked_actions": _denied_effects(),
        "denied_effects": _denied_effects(),
        "authority": _authority(),
        "terminal_output_trusted": False,
        "trust_tier": "Tier 4",
        "warnings": [
            "consumption_design_only_no_marker_write",
            "no_approval_consumption",
            "no_chaser_runtime_activation",
            "no_profile_or_toolset_activation",
            "no_terminal_to_chaser_binding",
            "no_terminal_execution",
            "no_studio_execution",
            "no_agent_bus_write_or_claim",
            "no_provider_call",
            "terminal_output_remains_tier4_untrusted",
        ],
        "next_recommended_pass": (
            "terminal-n22-chaser-runtime-activation-post-consumption-readiness"
        ),
        "boundary": (
            "activation approval consumption design only; defines a future "
            "exact-once marker, append-only audit, stop conditions, and handoff "
            "requirements. It performs no approval consumption, marker write, "
            "activation, terminal binding, Agent Bus mutation, provider call, "
            "host mutation, or canonical writeback."
        ),
    }
