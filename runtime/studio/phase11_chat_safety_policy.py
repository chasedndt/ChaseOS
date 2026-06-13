"""Phase 11 Chat safety and action-class policy.

This contract is intentionally fail-closed.  It centralizes the denied action
classes used by the Chat router and panel so Phase 11 can explain policy without
becoming a second control plane.  The builder never writes files, never consumes
approvals, and never executes runtime/browser/provider work.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODEL_VERSION = "studio.phase11_chat_safety_policy.v1"
SURFACE_ID = "phase11_chat_safety_policy"

DENIED_ACTION_CLASS_CATALOG: dict[str, dict[str, str]] = {
    "llm_intent_classification_call": {
        "authority_family": "model_execution",
        "missing_contract": "LLM intent-classifier execution approval and prompt-injection boundary",
        "blocked_action_reason": "Phase 11 Chat uses deterministic classification only.",
        "lower_phase_owner_or_surface": "provider routing / model execution governance",
    },
    "provider_api_call": {
        "authority_family": "provider_execution",
        "missing_contract": "live provider execution approval and exact request digest",
        "blocked_action_reason": "Provider calls are approval-preview only from Chat.",
        "lower_phase_owner_or_surface": "runtime/providers and Gate provider execution lane",
    },
    "chat_response_generation_call": {
        "authority_family": "provider_execution",
        "missing_contract": "approved model route plus conversation audit persistence policy",
        "blocked_action_reason": "Chat may render readiness, not generate live model responses.",
        "lower_phase_owner_or_surface": "Phase 9 provider executor / Phase 10 service writer",
    },
    "runtime_dispatch": {
        "authority_family": "runtime_dispatch",
        "missing_contract": "Agent Bus/AOR dispatch envelope and executor contract",
        "blocked_action_reason": "Runtime dispatch must route through lower-phase structured state.",
        "lower_phase_owner_or_surface": "runtime/agent_bus and AOR workflow manifests",
    },
    "browser_control": {
        "authority_family": "external_control",
        "missing_contract": "browser/CDP execution contract and operator approval",
        "blocked_action_reason": "Chat cannot launch, navigate, click, or screenshot browsers.",
        "lower_phase_owner_or_surface": "SiteOps browser policy / Phase 9 adapter governance",
    },
    "shell_execution": {
        "authority_family": "external_control",
        "missing_contract": "shell execution contract, scope, and audit guard",
        "blocked_action_reason": "Chat cannot run shell or terminal commands.",
        "lower_phase_owner_or_surface": "Phase 9 shell/runtime adapter policy",
    },
    "connector_call": {
        "authority_family": "external_control",
        "missing_contract": "connector manifest, credential scope, and approval policy",
        "blocked_action_reason": "Chat cannot call connectors or external APIs.",
        "lower_phase_owner_or_surface": "connector governance / provider policy",
    },
    "approval_grant_or_reject": {
        "authority_family": "approval_action",
        "missing_contract": "approval decision writer contract",
        "blocked_action_reason": "Chat cannot grant, reject, or deny approvals.",
        "lower_phase_owner_or_surface": "Gate approval decision lane",
    },
    "approval_consumption": {
        "authority_family": "approval_action",
        "missing_contract": "exact-once approval consumer and replay marker policy",
        "blocked_action_reason": "Chat cannot consume approvals or execute approved targets.",
        "lower_phase_owner_or_surface": "Gate approval consumer policy",
    },
    "vault_file_write": {
        "authority_family": "vault_write",
        "missing_contract": "governed writeback contract and audit proof",
        "blocked_action_reason": "Chat cannot write vault files.",
        "lower_phase_owner_or_surface": "Phase 9/10 governed writeback service",
    },
    "conversation_log_write": {
        "authority_family": "vault_write",
        "missing_contract": "conversation persistence approval and retention policy",
        "blocked_action_reason": "Conversation persistence is blocked until approved separately.",
        "lower_phase_owner_or_surface": "conversation persistence writer lane",
    },
    "agent_bus_task_write": {
        "authority_family": "runtime_dispatch",
        "missing_contract": "Agent Bus task creation contract and write approval",
        "blocked_action_reason": "Chat may preview packets but cannot write Agent Bus tasks.",
        "lower_phase_owner_or_surface": "runtime/agent_bus governed enqueue lane",
    },
    "schedule_mutation": {
        "authority_family": "runtime_dispatch",
        "missing_contract": "schedule/cron mutation approval and rollback policy",
        "blocked_action_reason": "Chat cannot create or mutate schedules.",
        "lower_phase_owner_or_surface": "AOR scheduler governance",
    },
    "hidden_memory_write": {
        "authority_family": "memory_write",
        "missing_contract": "inspectable runtime memory write policy",
        "blocked_action_reason": "Chat cannot silently persist memory.",
        "lower_phase_owner_or_surface": "ChaseOS memory boundary / runtime memory policy",
    },
    "credential_or_config_mutation": {
        "authority_family": "credential_config",
        "missing_contract": "redacted config mutation and rollback contract",
        "blocked_action_reason": "Chat cannot read, expose, set, or mutate credentials/config.",
        "lower_phase_owner_or_surface": "Studio Settings / provider config governance",
    },
    "protected_file_write": {
        "authority_family": "protected_governance_write",
        "missing_contract": "protected-file Gate workflow",
        "blocked_action_reason": "Protected control docs are outside Phase 11 Chat authority.",
        "lower_phase_owner_or_surface": "Permission Matrix / Trust Tiers / Gate rules workflow",
    },
    "source_pack_promotion": {
        "authority_family": "canonical_promotion",
        "missing_contract": "source-pack creation/promotion Gate contract",
        "blocked_action_reason": "Chat cannot create, apply, or promote source packs.",
        "lower_phase_owner_or_surface": "source-pack promotion pipeline and Gate",
    },
    "graph_mutation": {
        "authority_family": "canonical_promotion",
        "missing_contract": "canonical graph mutation contract",
        "blocked_action_reason": "Chat cannot mutate graph truth.",
        "lower_phase_owner_or_surface": "graph mutation policy / canonical maintenance workflow",
    },
    "canonical_writeback": {
        "authority_family": "canonical_promotion",
        "missing_contract": "canonical knowledge promotion Gate contract",
        "blocked_action_reason": "Chat cannot promote or mutate canonical knowledge.",
        "lower_phase_owner_or_surface": "ChaseOS Gate and canonical knowledge promotion workflow",
    },
}

AFFECTED_SURFACE_BY_ACTION_CLASS: dict[str, str] = {
    "llm_intent_classification_call": "Phase 11 Chat router deterministic intent classification surface",
    "provider_api_call": "Phase 11 Chat provider-route preview surface",
    "chat_response_generation_call": "Phase 11 Chat response-rendering surface",
    "runtime_dispatch": "Phase 11 Chat runtime-dispatch preview surface",
    "browser_control": "Phase 11 Chat browser-dispatch readiness surface",
    "shell_execution": "Phase 11 Chat command/action preview surface",
    "connector_call": "Phase 11 Chat external-connector preview surface",
    "approval_grant_or_reject": "Phase 11 Chat approval action preview surface",
    "approval_consumption": "Phase 11 Chat approval-consumption readiness surface",
    "vault_file_write": "Phase 11 Chat proposal and vault-write preview surface",
    "conversation_log_write": "Phase 11 Chat conversation persistence preview surface",
    "agent_bus_task_write": "Phase 11 Chat Agent Bus handoff preview surface",
    "schedule_mutation": "Phase 11 Chat scheduled-workflow preview surface",
    "hidden_memory_write": "Phase 11 Chat memory-save preview surface",
    "credential_or_config_mutation": "Phase 11 Chat settings/config preview surface",
    "protected_file_write": "Phase 11 Chat protected-governance-write preview surface",
    "source_pack_promotion": "Phase 11 Chat source-pack promotion preview surface",
    "graph_mutation": "Phase 11 Chat graph-mutation preview surface",
    "canonical_writeback": "Phase 11 Chat canonical-knowledge promotion preview surface",
}

MINIMUM_PROOF_NEEDED_BY_ACTION_CLASS: dict[str, str] = {
    "llm_intent_classification_call": "approved classifier route, prompt-injection boundary proof, and no-secret prompt audit",
    "provider_api_call": "approved provider execution envelope, exact request digest, and no-secret response audit",
    "chat_response_generation_call": "approved model route, conversation audit persistence policy, and output provenance proof",
    "runtime_dispatch": "validated AOR/Agent Bus dispatch envelope plus executor and audit-writeback proof",
    "browser_control": "approved browser/CDP execution envelope, scope guard, and operator-visible audit proof",
    "shell_execution": "approved shell scope contract, command allowlist, rollback plan, and audit proof",
    "connector_call": "approved connector manifest, credential scope proof, and redacted request/response audit",
    "approval_grant_or_reject": "Gate decision-writer contract, operator identity proof, and append-only approval audit",
    "approval_consumption": "exact-once approval consumer proof, replay marker, and target execution audit",
    "vault_file_write": "governed writeback contract, target-path approval, dry-run diff, and audit proof",
    "conversation_log_write": "approved retention policy, redaction proof, and conversation-log writer audit",
    "agent_bus_task_write": "governed Agent Bus enqueue contract, schema validation, and duplicate-prevention proof",
    "schedule_mutation": "approved scheduler mutation envelope, rollback proof, and operator-visible audit record",
    "hidden_memory_write": "inspectable memory write policy, export/delete path, and redacted audit proof",
    "credential_or_config_mutation": "redacted config mutation contract, rollback proof, and secret-nonexposure audit",
    "protected_file_write": "protected-file Gate approval, diff review, and promotion audit proof",
    "source_pack_promotion": "source-pack Gate approval, provenance validation, and promotion audit proof",
    "graph_mutation": "canonical graph mutation approval, validation report, and rollback/audit proof",
    "canonical_writeback": "canonical promotion Gate approval, provenance validation, and Agent-Activity audit proof",
}

REQUESTED_ACTION_TO_CLASS = {
    "vault_write": "vault_file_write",
    "lifecycle_execution": "runtime_dispatch",
    "runtime_dispatch": "runtime_dispatch",
    "browser_or_shell_or_connector_authority": "browser_control",
    "approval_consumption": "approval_consumption",
    "protected_file_write": "protected_file_write",
    "hidden_memory_write": "hidden_memory_write",
    "credential_or_config_mutation": "credential_or_config_mutation",
    "source_pack_promotion": "source_pack_promotion",
    "graph_mutation": "graph_mutation",
    "canonical_knowledge_promotion": "canonical_writeback",
}

INTENT_TO_CLASS = {
    "chat-answer": "chat_response_generation_call",
    "model-chat": "provider_api_call",
    "synthesis-note": "provider_api_call",
    "runtime-task": "runtime_dispatch",
    "browser-task": "browser_control",
    "scheduled-workflow": "schedule_mutation",
    "approval-action": "approval_grant_or_reject",
    "memory-save": "hidden_memory_write",
    "handoff": "agent_bus_task_write",
    "archive": "conversation_log_write",
    "source-note": "source_pack_promotion",
    "vault-node-create": "canonical_writeback",
    "vault-node-update": "canonical_writeback",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _policy_entry(action_class: str, *, triggered_by_request: bool, triggered_by_intent: bool) -> dict[str, Any]:
    details = DENIED_ACTION_CLASS_CATALOG[action_class]
    return {
        "action_class": action_class,
        "authority_family": details["authority_family"],
        "policy_decision": "deny",
        "available_now": False,
        "allowed_now": False,
        "deny_default_gate": True,
        "fail_closed_when_authority_absent": True,
        "triggered_by_request": triggered_by_request,
        "triggered_by_intent": triggered_by_intent,
        "missing_contract": details["missing_contract"],
        "affected_phase10_or_phase11_surface": AFFECTED_SURFACE_BY_ACTION_CLASS[action_class],
        "lower_phase_owner_or_surface": details["lower_phase_owner_or_surface"],
        "minimum_proof_needed": MINIMUM_PROOF_NEEDED_BY_ACTION_CLASS[action_class],
        "blocked_action_reason": details["blocked_action_reason"],
    }


def build_phase11_chat_safety_policy(
    vault_root: str | Path,
    *,
    intent_class: str | None = None,
    requested_denied_actions: list[str] | None = None,
    prompt_injection_suspected: bool = False,
    blocked_reasons: list[str] | None = None,
) -> dict[str, Any]:
    """Build a centralized deny-default action-class policy report."""

    vault = Path(vault_root).resolve()
    requested = list(requested_denied_actions or [])
    intent_action_class = INTENT_TO_CLASS.get(str(intent_class or ""))
    requested_classes = [REQUESTED_ACTION_TO_CLASS[action] for action in requested if action in REQUESTED_ACTION_TO_CLASS]
    triggered_classes = list(dict.fromkeys([c for c in [intent_action_class, *requested_classes] if c]))
    denied_action_classes = {
        action_class: _policy_entry(
            action_class,
            triggered_by_request=action_class in requested_classes,
            triggered_by_intent=action_class == intent_action_class,
        )
        for action_class in DENIED_ACTION_CLASS_CATALOG
    }
    policy_blockers = list(blocked_reasons or [])
    if prompt_injection_suspected:
        policy_blockers.append("prompt_injection_indicator_present")
    if requested:
        policy_blockers.append("denied_side_effect_prompt_present")
    if triggered_classes:
        policy_blockers.append("action_class_requires_lower_phase_authority")
    policy_blockers.append("phase11_chat_deny_default_policy_active")

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "policy_status": "denied_fail_closed" if requested or prompt_injection_suspected else "blocked_preview_only",
        "execution_allowed": False,
        "mutation_allowed": False,
        "writes_allowed": False,
        "authority_absent_fails_closed": True,
        "all_capabilities_policy_aware": True,
        "triggered_action_classes": triggered_classes,
        "requested_denied_actions": requested,
        "denied_action_classes": denied_action_classes,
        "authority_matrix": {
            "model_calls_allowed": False,
            "provider_calls_allowed": False,
            "runtime_dispatch_allowed": False,
            "browser_control_allowed": False,
            "shell_execution_allowed": False,
            "connector_calls_allowed": False,
            "approval_execution_allowed": False,
            "approval_consumption_allowed": False,
            "vault_writes_allowed": False,
            "conversation_persistence_allowed": False,
            "agent_bus_task_write_allowed": False,
            "schedule_mutation_allowed": False,
            "hidden_memory_write_allowed": False,
            "credential_or_config_mutation_allowed": False,
            "protected_file_write_allowed": False,
            "source_pack_promotion_allowed": False,
            "graph_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "policy_fail_closed_summary": {
            "action_class_count": len(DENIED_ACTION_CLASS_CATALOG),
            "allowed_action_class_count": 0,
            "denied_action_class_count": len(DENIED_ACTION_CLASS_CATALOG),
            "triggered_action_class_count": len(triggered_classes),
            "fail_closed_when_authority_absent": True,
            "second_control_plane_prevented": True,
            "lower_phase_dependency_routing_required": True,
        },
        "blocked_reasons": list(dict.fromkeys(policy_blockers)),
        "next_route": "lower-phase owner must provide an explicit Gate/AOR/provider/browser/approval/writeback contract before any action class can execute",
    }


def format_phase11_chat_safety_policy(payload: dict[str, Any]) -> str:
    summary = payload.get("policy_fail_closed_summary") or {}
    lines = [
        "Phase 11 Chat Safety Policy",
        f"- policy_status: {payload.get('policy_status')}",
        f"- execution_allowed: {payload.get('execution_allowed')}",
        f"- authority_absent_fails_closed: {payload.get('authority_absent_fails_closed')}",
        f"- denied_action_class_count: {summary.get('denied_action_class_count')}",
        f"- allowed_action_class_count: {summary.get('allowed_action_class_count')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("blocked_reasons:")
        lines.extend(f"- {reason}" for reason in blockers)
    lines.append("Boundary: policy report only; no provider call, runtime dispatch, browser/shell/connector action, approval consumption, vault write, or canonical writeback.")
    return "\n".join(lines)
