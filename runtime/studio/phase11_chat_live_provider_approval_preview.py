"""Phase 11 Chat live-provider execution approval preview.

This pass previews the approval packet required before any Chat-originated
model/provider call. It deliberately does not call a provider, read credential
values, write an approval artifact, persist a conversation, or execute anything.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.providers.routing_consumer_contract import build_provider_routing_consumer_contract
from runtime.studio.phase11_chat_conversation_persistence_contract import (
    build_phase11_chat_conversation_persistence_contract,
)
from runtime.studio.phase11_chat_router_contract import MODEL_BOUND_INTENTS, build_phase11_chat_router_contract
from runtime.studio.provider_readiness import build_studio_provider_readiness


MODEL_VERSION = "studio.phase11_chat_live_provider_approval_preview.v1"
SURFACE_ID = "phase11_chat_live_provider_execution_approval_preview"
PASS_ID = "phase11-chat-live-provider-execution-approval-preview"
STATUS = "COMPLETE / READ-ONLY / VERIFIED / PROVIDER CALLS BLOCKED"
NEXT_RECOMMENDED_PASS = "phase11-chat-browser-dispatch-readiness-contract"
APPROVAL_CLASS = "studio_chat_live_provider_execution_approval_future"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(message: str | None) -> str:
    return " ".join(str(message or "").strip().split())


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value: str, length: int = 16) -> str:
    return _sha256_text(value)[:length]


def _provider_selection(provider_contract: dict[str, Any], readiness: dict[str, Any]) -> dict[str, Any]:
    selected = provider_contract.get("selected_candidate_preview")
    if isinstance(selected, dict):
        return {
            "role": selected.get("role") or "primary",
            "provider_id": selected.get("provider_id"),
            "model": selected.get("model"),
            "strength": selected.get("strength"),
            "route_ready": bool(selected.get("route_ready")),
        }
    active = readiness.get("active_profile") or {}
    return {
        "role": "primary",
        "provider_id": active.get("provider_id"),
        "model": active.get("model"),
        "strength": "strong",
        "route_ready": False,
    }


def _lower_phase_routing_notes() -> list[dict[str, str]]:
    return [
        {
            "missing_contract": "phase11_chat_live_provider_execution_contract",
            "affected_phase10_or_phase11_surface": "phase11_chat_live_provider_execution_approval_preview",
            "lower_phase_owner_or_surface": "RPGL/provider execution governance lane",
            "minimum_proof_needed": "approved provider execution contract with digest-bound approval consumption, credential-safe provider call, and conversation audit persistence",
            "blocked_action_reason": "live_provider_execution_not_supported_by_preview_surface",
        }
    ]


def _action_preview_card(
    *,
    intent: str,
    message: str,
    selection: dict[str, Any],
    conversation_descriptor: dict[str, Any],
    request_digest: str,
    blockers: list[str],
    approval_preview_ready: bool,
) -> dict[str, Any]:
    blocked_reasons = list(dict.fromkeys([*blockers, "future_operator_execution_approval_missing"]))
    return {
        "visible": approval_preview_ready,
        "preview_only": True,
        "copy": {
            "boundary": (
                "Provider action preview only — no approval artifact, queue write, provider call, credential read, "
                "conversation write, runtime dispatch, browser control, target write, or canonical mutation has run."
            ),
            "primary_action_label": "Review provider execution approval preview",
            "disabled_action_copy": "Direct provider calls, approval consumption, credential reads, conversation writes, runtime dispatch, browser control, and canonical mutation are disabled here.",
        },
        "summary_scope": {
            "intent_class": intent,
            "summary": "Preview future Phase 11 Chat provider call and required approval evidence.",
            "scope": message[:600],
            "model_bound_preview": True,
        },
        "affected_files_or_systems": {
            "conversation_target_path_preview": conversation_descriptor.get("target_path_preview"),
            "provider_system_preview": selection.get("provider_id"),
            "model_preview": selection.get("model"),
            "approval_artifact_path_preview": "runtime/studio/approvals/<future-provider-approval-id>.json",
            "target_vault_write_performed": False,
        },
        "risk": {
            "level": "approval_gated_live_provider_preview",
            "authority_risk": "live_provider_execution_requires_future_governed_approval",
            "unsafe_effects_blocked": [
                "provider_api_call",
                "credential_value_read",
                "approval_artifact_write",
                "approval_consumption",
                "conversation_log_write",
                "runtime_dispatch",
                "browser_control",
                "target_vault_file_write",
                "canonical_writeback",
            ],
        },
        "required_approvals": [APPROVAL_CLASS],
        "dry_run_preview": {
            "dry_run": True,
            "approval_request_created": False,
            "approval_queue_writer_called": False,
            "provider_call_performed": False,
            "credential_value_read": False,
            "conversation_log_written": False,
            "runtime_dispatch_performed": False,
            "browser_control_performed": False,
            "target_write_performed": False,
            "canonical_writeback_performed": False,
        },
        "blocked_state": {
            "blocked": True,
            "blocked_reasons": blocked_reasons,
        },
        "handback_route": {
            "route_type": "approval_preview_only",
            "next_surface": "future_phase11_provider_execution_approval_surface",
            "required_next_step": "operator-reviewed provider execution approval through governed RPGL contract",
            "direct_provider_call_button_enabled": False,
            "approval_consumption_button_enabled": False,
            "queue_writer_button_enabled_now": False,
        },
        "evidence_digest": {
            "request_digest": request_digest,
            "prompt_message_sha256": _sha256_text(message),
            "digest_required_for_future_approval_write": True,
        },
    }


def build_phase11_chat_live_provider_execution_approval_preview(
    vault_root: str | Path,
    *,
    message: str | None = None,
    explicit_intent: str | None = None,
    requested_provider_id: str | None = None,
    requested_model: str | None = None,
) -> dict[str, Any]:
    """Build a no-execution approval preview for a future Chat provider call."""

    vault = Path(vault_root).resolve()
    normalized_message = _norm(message)
    router = build_phase11_chat_router_contract(
        vault,
        message=normalized_message,
        explicit_intent=explicit_intent or "chat-answer",
    )
    intent = str((router.get("intent_result") or {}).get("intent_class") or "chat-answer")
    input_posture = router.get("input_posture") or {}
    provider_readiness = build_studio_provider_readiness(vault)
    provider_contract = build_provider_routing_consumer_contract(
        vault,
        phase11_intent=intent,
        requested_provider_id=requested_provider_id,
        requested_model=requested_model,
    )
    conversation_contract = build_phase11_chat_conversation_persistence_contract(
        vault,
        message=normalized_message,
        explicit_intent=intent,
    )
    selection = _provider_selection(provider_contract, provider_readiness)

    blockers: list[str] = []
    warnings: list[str] = []
    if not normalized_message:
        blockers.append("message_required_for_live_provider_approval_preview")
    if intent not in MODEL_BOUND_INTENTS:
        blockers.append("intent_not_model_bound_for_provider_execution")
    if input_posture.get("prompt_injection_suspected"):
        blockers.append("prompt_injection_indicator_present")
    if provider_contract.get("routing_status") != "route_contract_satisfied":
        blockers.append("provider_route_contract_not_satisfied")
    if (provider_readiness.get("summary") or {}).get("readiness_status") != "verified_by_last_probe_result":
        blockers.append("provider_readiness_not_verified_by_last_probe_result")
    credential = provider_readiness.get("credential_posture") or {}
    if not credential.get("primary_provider_env_present"):
        blockers.append("primary_provider_credential_or_environment_missing")
    conversation_descriptor = conversation_contract.get("conversation_descriptor") or {}
    if not conversation_descriptor.get("target_path_preview"):
        blockers.append("conversation_audit_target_preview_missing")
    if (conversation_contract.get("conversation_log_preview") or {}).get("target_file_written"):
        blockers.append("conversation_target_unexpectedly_written")

    prompt_material = {
        "system_boundary": "ChaseOS Phase 11 live provider execution requires explicit future approval.",
        "message_sha256": _sha256_text(normalized_message),
        "intent_class": intent,
        "provider_id": selection.get("provider_id"),
        "model": selection.get("model"),
        "task_class": provider_contract.get("task_class"),
        "required_provider_strength": provider_contract.get("required_provider_strength"),
        "conversation_target_path_preview": conversation_descriptor.get("target_path_preview"),
        "source_router_model_version": router.get("model_version"),
        "provider_contract_model_version": provider_contract.get("model_version"),
    }
    request_digest = _sha256_text(_canonical_json(prompt_material))
    approval_id_preview = f"chat-provider-exec-appr-{_digest(request_digest, 20)}"
    approval_preview_ready = bool(normalized_message) and intent in MODEL_BOUND_INTENTS and not input_posture.get(
        "prompt_injection_suspected"
    )
    execution_preconditions_met = approval_preview_ready and not blockers
    if approval_preview_ready and blockers:
        warnings.append("approval_preview_available_but_execution_preconditions_blocked")

    return {
        "ok": not any(
            blocker
            in {
                "message_required_for_live_provider_approval_preview",
                "intent_not_model_bound_for_provider_execution",
                "prompt_injection_indicator_present",
                "conversation_target_unexpectedly_written",
            }
            for blocker in blockers
        ),
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "approval_gated": True,
        "summary": {
            "message_present": bool(normalized_message),
            "intent_class": intent,
            "model_bound_intent": intent in MODEL_BOUND_INTENTS,
            "approval_preview_ready": approval_preview_ready,
            "execution_preconditions_met": execution_preconditions_met,
            "provider_route_status": provider_contract.get("routing_status"),
            "provider_readiness_status": (provider_readiness.get("summary") or {}).get("readiness_status"),
            "selected_provider_id": selection.get("provider_id"),
            "selected_model": selection.get("model"),
            "approval_request_created": False,
            "provider_call_performed": False,
            "conversation_log_written": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "blocker_count": len(list(dict.fromkeys(blockers))),
        },
        "request_digest_proof": {
            "request_digest": request_digest,
            "prompt_message_sha256": _sha256_text(normalized_message),
            "digest_material": prompt_material,
            "digest_required_for_future_approval_write": True,
        },
        "future_provider_execution_preview": {
            "provider_call_allowed_now": False,
            "provider_call_performed": False,
            "provider_executor_built": False,
            "model_output_generated": False,
            "selected_route_preview": selection,
            "task_class": provider_contract.get("task_class"),
            "task_family": provider_contract.get("task_family"),
            "required_provider_strength": provider_contract.get("required_provider_strength"),
            "prompt_preview": normalized_message[:1200],
            "prompt_preview_truncated": len(normalized_message) > 1200,
            "model_output_attribution_required": True,
            "future_output_must_record_provider": True,
            "future_output_must_record_model": True,
        },
        "future_approval_packet_preview": {
            "visible": True,
            "approval_id_preview": approval_id_preview,
            "approval_artifact_path_preview": f"runtime/studio/approvals/{approval_id_preview}.json",
            "approval_request_created": False,
            "approval_queue_writer_called": False,
            "required_approval_class": APPROVAL_CLASS,
            "future_status_if_written": "pending",
            "approval_consumption_allowed_now": False,
            "execution_allowed_after_preview": False,
            "action_spec_preview": {
                "action_type": "chat_provider_call",
                "target_path": None,
                "submitted_by": "studio-chat",
                "note": "Phase 11 Chat live provider execution approval preview",
                "content_sha256": request_digest,
                "metadata": {
                    "pass": PASS_ID,
                    "phase": "Phase 11",
                    "phase11_intent": intent,
                    "source_surface": "phase11_chat_panel",
                    "source_contract": SURFACE_ID,
                    "request_digest": request_digest,
                    "prompt_message_sha256": _sha256_text(normalized_message),
                    "provider_id_preview": selection.get("provider_id"),
                    "model_preview": selection.get("model"),
                    "conversation_target_path_preview": conversation_descriptor.get("target_path_preview"),
                    "provider_call_performed": False,
                    "approval_execution_deferred_until": "future_phase11_provider_execution_pass",
                },
            },
        },
        "provider_preflight": {
            "routing_contract": provider_contract,
            "provider_readiness": provider_readiness,
            "provider_route_contract_satisfied": provider_contract.get("routing_status") == "route_contract_satisfied",
            "provider_readiness_verified": (provider_readiness.get("summary") or {}).get("readiness_status")
            == "verified_by_last_probe_result",
            "execution_preconditions_met": execution_preconditions_met,
            "credential_values_included": False,
            "raw_credentials_included": False,
            "secret_values_visible": False,
            "provider_switch_allowed": False,
            "live_probe_execution_allowed": False,
        },
        "conversation_audit_preflight": {
            "conversation_contract": conversation_contract,
            "target_path_preview": conversation_descriptor.get("target_path_preview"),
            "conversation_audit_write_allowed_now": False,
            "conversation_log_written": False,
            "conversation_directory_created": False,
            "conversation_persistence_required_before_future_execution": True,
        },
        "action_preview_card": _action_preview_card(
            intent=intent,
            message=normalized_message,
            selection=selection,
            conversation_descriptor=conversation_descriptor,
            request_digest=request_digest,
            blockers=blockers,
            approval_preview_ready=approval_preview_ready,
        ),
        "lower_phase_routing_notes": _lower_phase_routing_notes(),
        "preflight_checks": {
            "message_present": bool(normalized_message),
            "intent_is_model_bound": intent in MODEL_BOUND_INTENTS,
            "prompt_injection_absent": not bool(input_posture.get("prompt_injection_suspected")),
            "provider_route_contract_satisfied": provider_contract.get("routing_status") == "route_contract_satisfied",
            "provider_readiness_verified_by_last_probe_result": (
                provider_readiness.get("summary") or {}
            ).get("readiness_status")
            == "verified_by_last_probe_result",
            "primary_provider_environment_present": bool(credential.get("primary_provider_env_present")),
            "conversation_audit_target_preview_present": bool(conversation_descriptor.get("target_path_preview")),
            "approval_packet_written": False,
            "provider_call_performed": False,
        },
        "authority": {
            "read_only": True,
            "approval_gated": True,
            "approval_preview_allowed": True,
            "approval_queue_write_allowed": False,
            "approval_execution_allowed": False,
            "provider_calls_allowed": False,
            "model_output_generation_allowed": False,
            "credential_values_visible": False,
            "provider_switch_allowed": False,
            "provider_config_write_allowed": False,
            "conversation_persistence_allowed": False,
            "target_vault_write_allowed": False,
            "runtime_dispatch_allowed": False,
            "browser_control_allowed": False,
            "agent_bus_task_write_allowed": False,
            "gate_mutation_allowed": False,
            "git_mutation_allowed": False,
            "workflow_execution_allowed": False,
            "host_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "denied_by_this_surface": [
            "provider_api_call",
            "model_output_generation",
            "credential_value_display",
            "provider_switch",
            "provider_config_write",
            "approval_artifact_write",
            "approval_grant_or_reject",
            "approval_execution",
            "conversation_log_write",
            "target_vault_file_write",
            "runtime_dispatch",
            "browser_control",
            "agent_bus_task_write",
            "gate_mutation",
            "git_mutation",
            "workflow_execution",
            "host_mutation",
            "canonical_writeback",
        ],
        "blocked_reasons": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def format_phase11_chat_live_provider_execution_approval_preview(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    digest = payload.get("request_digest_proof") or {}
    approval = payload.get("future_approval_packet_preview") or {}
    return "\n".join(
        [
            "Phase 11 Chat Live Provider Execution Approval Preview",
            f"  status: {payload.get('status')}",
            f"  intent: {summary.get('intent_class')}",
            f"  provider_route_status: {summary.get('provider_route_status')}",
            f"  provider_readiness_status: {summary.get('provider_readiness_status')}",
            f"  selected_provider: {summary.get('selected_provider_id')}",
            f"  selected_model: {summary.get('selected_model')}",
            f"  request_digest: {digest.get('request_digest')}",
            f"  approval_id_preview: {approval.get('approval_id_preview')}",
            f"  approval_request_created: {summary.get('approval_request_created')}",
            f"  provider_call_performed: {summary.get('provider_call_performed')}",
            f"  next: {summary.get('next_recommended_pass')}",
            "  Boundary: approval preview only; no approval artifact, provider call, credential value display, conversation write, target write, runtime dispatch, Agent Bus task, or canonical mutation.",
        ]
    )
