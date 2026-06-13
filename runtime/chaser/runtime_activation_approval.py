"""Preview-only ChaserAgent runtime activation approval request.

This module builds the request packet shape a future approval writer would use,
but it never writes the request, consumes an approval, activates ChaserAgent,
binds terminal tools, writes Agent Bus state, calls providers, or mutates
canonical ChaseOS state.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.chaser.runtime_activation_gate import (
    build_chaser_runtime_activation_gate_design,
)


SURFACE = "chaser_runtime_activation_approval_preview"
SCHEMA_VERSION = "chaser_runtime_activation_approval_preview.v1"


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


def _normalize(value: str | None, default: str) -> str:
    text = str(value or default).strip()
    return text or default


def _normalize_id(value: str | None, default: str) -> str:
    return _normalize(value, default).lower()


def _preview_id(packet_basis: dict[str, Any]) -> str:
    raw = json.dumps(packet_basis, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()[:16]
    return f"chaser-activation-preview-{digest}"


def _compact_gate_design(gate: dict[str, Any]) -> dict[str, Any]:
    requested = gate.get("requested_activation")
    readiness = gate.get("readiness_dependency")
    return {
        "surface": gate.get("surface"),
        "schema_version": gate.get("schema_version"),
        "ok": gate.get("ok"),
        "design_status": gate.get("design_status"),
        "ready_for_activation_now": gate.get("ready_for_activation_now"),
        "ready_to_write_activation_request_now": gate.get(
            "ready_to_write_activation_request_now"
        ),
        "requested_activation": requested if isinstance(requested, dict) else {},
        "readiness_dependency": readiness if isinstance(readiness, dict) else {},
        "blockers": list(gate.get("blockers") or []),
        "future_gate_blockers": list(gate.get("future_gate_blockers") or []),
    }


def build_chaser_runtime_activation_approval_preview(
    vault_root: str | Path,
    *,
    profile_id: str = "ops",
    toolset_id: str = "terminal-preview",
    operator_intent: str = "",
    activation_scope: str = "local_preview_only",
    terminal_binding_mode: str = "read_only_policy_preview_and_audit_history_only",
    agent_bus_mutation_requested: bool = False,
    provider_dispatch_requested: bool = False,
) -> dict[str, Any]:
    """Return a no-write activation approval request preview."""

    root = Path(vault_root).resolve()
    requested_profile = _normalize_id(profile_id, "ops")
    requested_toolset = _normalize_id(toolset_id, "terminal-preview")
    requested_intent = _normalize(
        operator_intent,
        "Preview future Chaser runtime activation approval packet only.",
    )
    requested_scope = _normalize_id(activation_scope, "local_preview_only")
    requested_binding_mode = _normalize_id(
        terminal_binding_mode,
        "read_only_policy_preview_and_audit_history_only",
    )

    gate = build_chaser_runtime_activation_gate_design(
        root,
        profile_id=requested_profile,
        toolset_id=requested_toolset,
    )

    blockers: list[str] = []
    if gate.get("ok") is not True:
        blockers.append("activation_gate_design_not_ready")
        blockers.extend(str(item) for item in gate.get("blockers") or [])
    if agent_bus_mutation_requested:
        blockers.append("agent_bus_mutation_requires_separate_gate")
    if provider_dispatch_requested:
        blockers.append("provider_dispatch_requires_separate_gate")
    if requested_scope not in {"local_preview_only", "local_runtime_activation"}:
        blockers.append(f"unsupported_activation_scope:{requested_scope}")
    if requested_binding_mode not in {
        "read_only_policy_preview_and_audit_history_only",
        "no_terminal_access_requested",
    }:
        blockers.append(f"unsupported_terminal_binding_mode:{requested_binding_mode}")

    preview_basis = {
        "runtime_id": "chaser",
        "profile_id": requested_profile,
        "toolset_id": requested_toolset,
        "operator_intent": requested_intent,
        "activation_scope": requested_scope,
        "terminal_binding_mode": requested_binding_mode,
        "agent_bus_mutation_requested": bool(agent_bus_mutation_requested),
        "provider_dispatch_requested": bool(provider_dispatch_requested),
        "gate_design_surface": gate.get("surface"),
        "gate_design_ok": gate.get("ok"),
    }
    preview_id = _preview_id(preview_basis)
    evidence_refs = {
        "chaser_runtime_readiness_ok": "readiness_dependency.ok",
        "terminal_authority_audit_pass": "readiness_dependency.contract_summary.checks_failed == 0",
        "profile_view_validation_ok": f"profile:{requested_profile}",
        "toolset_view_validation_ok": f"toolset:{requested_toolset}",
        "operator_activation_intent": requested_intent,
        "no_studio_execution_contract": "studio_execution_now=false",
        "no_provider_or_agent_bus_mutation_without_separate_gate": (
            "agent_bus_mutation_requested=false and provider_dispatch_requested=false"
        ),
    }
    approval_request_preview = {
        "preview_id": preview_id,
        "action_type": "chaser_runtime_activation",
        "request_status": "preview_only_not_written",
        "runtime_id": "chaser",
        "profile_id": requested_profile,
        "toolset_id": requested_toolset,
        "operator_intent": requested_intent,
        "activation_scope": requested_scope,
        "terminal_binding_mode": requested_binding_mode,
        "agent_bus_mutation_requested": bool(agent_bus_mutation_requested),
        "provider_dispatch_requested": bool(provider_dispatch_requested),
        "evidence_refs": evidence_refs,
        "authority_ceiling": {
            "runtime": "ChaserAgent",
            "terminal": "read_only_preview_and_audit_readback_only",
            "terminal_output_trust_tier": "Tier 4",
            "approval_write_requires_future_gate": True,
            "approval_consumption_requires_future_gate": True,
            "agent_bus_mutation_requires_separate_gate": True,
            "provider_dispatch_requires_separate_gate": True,
        },
        "required_review": [
            "operator_confirmation",
            "exact_once_consumption_plan",
            "terminal_authority_audit_pass",
            "profile_and_toolset_activation_scope_review",
        ],
    }

    ok = not blockers
    return {
        "ok": ok,
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "vault_root": str(root),
        "preview_status": "preview_ready_no_write" if ok else "preview_blocked",
        "approval_request_written": False,
        "ready_to_write_activation_request_now": False,
        "activation_approval_consumption_available": False,
        "activation_approval_id": None,
        "activation_approval_preview_id": preview_id,
        "approval_request_preview": approval_request_preview,
        "future_approval_metadata": {
            "future_approval_queue_path": "runtime/studio/approvals/chaser-runtime-activation/",
            "future_exact_once_marker_path": (
                f"runtime/chaser/activation-markers/{preview_id}.json"
            ),
            "future_decision_preflight_required": True,
            "future_consumption_executor_required": True,
            "preview_is_not_authorization": True,
        },
        "gate_design": _compact_gate_design(gate),
        "terminal_binding_contract": gate.get("terminal_binding_contract") or {},
        "authority": _authority(),
        "blockers": blockers,
        "warnings": [
            "preview_only_no_approval_request_written",
            "no_chaser_runtime_activation",
            "no_profile_or_toolset_activation",
            "no_terminal_to_chaser_binding",
            "no_studio_terminal_execution",
            "no_agent_bus_write_or_claim",
            "no_provider_call",
            "terminal_output_remains_tier_4_untrusted",
        ],
        "next_recommended_pass": (
            "terminal-n18-chaser-runtime-activation-approval-request-write-gate"
        ),
    }
