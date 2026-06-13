"""Read-only Phase 11 Chat approval handoff queue contract.

This module previews how a future Chat proposal would become a StudioService
approval request. It never calls ``queue_for_approval`` and never writes an
approval artifact.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import re
from pathlib import Path
from typing import Any

from runtime.studio.phase11_chat_router_contract import build_phase11_chat_router_contract
from runtime.studio.provider_readiness import build_studio_provider_readiness


MODEL_VERSION = "studio.phase11_chat_approval_handoff_queue_contract.v1"
SURFACE_ID = "phase11_chat_approval_handoff_queue_contract"
FINAL_CLOSEOUT_STATUS = "COMPLETE / READ-ONLY / VERIFIED / QUEUE WRITES BLOCKED"
NEXT_RECOMMENDED_PASS = "phase11-conversational-command-center-post-closeout-planning"

QUEUEABLE_INTENTS = {
    "project-create",
    "project-update",
    "vault-node-create",
    "vault-node-update",
    "source-note",
    "synthesis-note",
    "rnd-entry",
    "roadmap-item",
    "memory-save",
    "handoff",
    "archive",
}

INTENT_TO_TARGET_ROOT = {
    "project-create": "01_PROJECTS/_chat_proposals",
    "project-update": "01_PROJECTS/_chat_proposals",
    "vault-node-create": "02_KNOWLEDGE/_chat_proposals",
    "vault-node-update": "02_KNOWLEDGE/_chat_proposals",
    "source-note": "02_KNOWLEDGE/_chat_proposals",
    "synthesis-note": "02_KNOWLEDGE/_chat_proposals",
    "rnd-entry": "07_LOGS/RD-Proposals/_chat_proposals",
    "roadmap-item": "07_LOGS/Roadmap-Proposals/_chat_proposals",
    "memory-save": "07_LOGS/Memory-Proposals/_chat_proposals",
    "handoff": "07_LOGS/Handoff-Proposals/_chat_proposals",
    "archive": "99_ARCHIVE/Chat-Proposals",
}

PROPOSAL_LABELS = {
    "project-create": "Project creation proposal",
    "project-update": "Project update proposal",
    "vault-node-create": "Vault node creation proposal",
    "vault-node-update": "Vault node update proposal",
    "source-note": "Source note proposal",
    "synthesis-note": "Synthesis note proposal",
    "rnd-entry": "R&D entry proposal",
    "roadmap-item": "Roadmap item proposal",
    "memory-save": "Memory save proposal",
    "handoff": "Runtime handoff proposal",
    "archive": "Archive proposal",
}

APPROVAL_CLASS_BY_INTENT = {
    "project-create": "studio_project_creation_approval_future",
    "project-update": "studio_project_update_approval_future",
    "vault-node-create": "studio_vault_node_create_approval_future",
    "vault-node-update": "studio_vault_node_update_approval_future",
    "source-note": "studio_source_note_approval_future",
    "synthesis-note": "studio_synthesis_note_approval_future",
    "rnd-entry": "studio_rnd_entry_approval_future",
    "roadmap-item": "studio_roadmap_item_approval_future",
    "memory-save": "studio_memory_write_approval_future",
    "handoff": "studio_runtime_handoff_approval_future",
    "archive": "studio_archive_approval_future",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(message: str | None) -> str:
    return " ".join(str(message or "").strip().split())


def _slug(value: str, fallback: str = "chat-proposal") -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return (text or fallback)[:80].strip("-") or fallback


def _digest(value: str, length: int = 12) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def _approval_class(intent: str) -> str:
    return APPROVAL_CLASS_BY_INTENT.get(intent, f"studio_{intent.replace('-', '_')}_approval_future")


def _action_spec_preview(intent: str, message: str) -> dict[str, Any] | None:
    if intent not in QUEUEABLE_INTENTS:
        return None
    slug = _slug(message, fallback=intent)
    target_root = INTENT_TO_TARGET_ROOT[intent]
    target_path = f"{target_root}/{slug}-{_digest(intent + ':' + message)}.md"
    content_preview = "\n".join(
        [
            "---",
            "generated_by: studio-chat-preview",
            f"phase11_intent: {intent}",
            "approval_required: true",
            "chat_queue_contract_only: true",
            "---",
            "",
            f"# {PROPOSAL_LABELS.get(intent) or 'Chat Proposal'}",
            "",
            message or "(empty message)",
            "",
        ]
    )
    return {
        "action_type": "create_file",
        "target_path": target_path,
        "submitted_by": "studio-chat",
        "note": f"Phase 11 Chat proposal preview for {intent}",
        "content_preview": content_preview[:1200],
        "content_sha256": hashlib.sha256(content_preview.encode("utf-8")).hexdigest(),
        "metadata": {
            "pass": "phase11-chat-approval-handoff-queue-contract",
            "phase11_intent": intent,
            "required_approval_class": _approval_class(intent),
            "source_surface": "phase11_chat_panel_readonly_contract",
            "chat_generated_proposal": True,
            "queue_contract_only": True,
        },
    }


def _lower_phase_routing_notes(intent: str, action_spec: dict[str, Any] | None, message: str = "") -> list[dict[str, str]]:
    if action_spec is not None:
        return []
    message_lc = message.lower()
    if intent == "browser-action" or "browser" in message_lc:
        return [
            {
                "missing_contract": "phase11_chat_browser_action_governed_queue_contract",
                "affected_phase10_or_phase11_surface": SURFACE_ID,
                "lower_phase_owner_or_surface": "AOR/Gate/browser-dispatch governance lane",
                "minimum_proof_needed": "approved read-only browser action queue contract with digest-bound preflight and no live browser launch",
                "blocked_action_reason": "browser_action_queue_preview_not_supported_by_this_contract",
            }
        ]
    return [
        {
            "missing_contract": "phase11_chat_governed_queue_contract_for_intent",
            "affected_phase10_or_phase11_surface": SURFACE_ID,
            "lower_phase_owner_or_surface": "AOR/Gate approval-routing governance lane",
            "minimum_proof_needed": "approved read-only proposal queue contract for this intent with digest-bound preflight and no live mutation",
            "blocked_action_reason": "intent_queue_preview_not_supported_by_this_contract",
        }
    ]


def _proposal_card_preview(
    *,
    intent: str,
    message: str,
    action_spec: dict[str, Any] | None,
    blockers: list[str],
    route: dict[str, Any],
) -> dict[str, Any]:
    target_path = (action_spec or {}).get("target_path")
    content_sha256 = (action_spec or {}).get("content_sha256")
    required_approval = _approval_class(intent)
    return {
        "visible": action_spec is not None,
        "preview_only": True,
        "copy": {
            "boundary": (
                "Proposal preview only — no approval artifact, queue write, provider call, runtime dispatch, "
                "browser control, conversation write, protected-file write, or canonical mutation has run."
            ),
            "primary_action_label": "Queue proposal request preview (governed handback only)",
            "disabled_action_copy": "Direct execution, approval consumption, provider/browser calls, dispatch, writes, and canonical mutation are disabled here.",
        },
        "summary_scope": {
            "intent_class": intent,
            "summary": PROPOSAL_LABELS.get(intent, "Unsupported proposal preview"),
            "scope": message[:600],
            "proposal_required": bool(route.get("proposal_required")),
        },
        "affected_files_or_systems": {
            "target_path_preview": target_path,
            "target_root_preview": INTENT_TO_TARGET_ROOT.get(intent),
            "approval_queue_artifact_preview": "runtime/studio/approvals/<future-approval-id>.json" if action_spec else None,
            "protected_or_canonical_write_performed": False,
        },
        "risk": {
            "level": "approval_gated_mutation_preview",
            "authority_risk": "mutation_requires_future_governed_approval",
            "unsafe_effects_blocked": [
                "approval_artifact_write",
                "queue_writer_call",
                "provider_api_call",
                "runtime_dispatch",
                "browser_control",
                "conversation_log_write",
                "protected_file_write",
                "canonical_writeback",
            ],
        },
        "required_approvals": [required_approval] if action_spec else [],
        "dry_run_preview": {
            "dry_run": True,
            "target_path_preview": target_path,
            "approval_request_created": False,
            "queue_writer_called": False,
            "vault_write_performed": False,
            "provider_call_performed": False,
            "runtime_dispatch_performed": False,
            "browser_control_performed": False,
            "conversation_write_performed": False,
            "canonical_writeback_performed": False,
        },
        "blocked_state": {
            "blocked": True,
            "blocked_reasons": list(dict.fromkeys(blockers)),
        },
        "handback_route": {
            "route_type": "governed_queue_preview_only",
            "next_surface": route.get("next_surface") or "future_approval_gated_proposal_surface",
            "required_next_step": "operator-reviewed approval queue write through existing governed contract",
            "queue_writer_contract": "runtime.studio.service.StudioService.queue_for_approval",
            "direct_execution_button_enabled": False,
            "enqueue_button_enabled_now": False,
        },
        "evidence_digest": {
            "content_sha256": content_sha256,
            "digest_required_for_future_queue_write": True,
            "source_message_sha256": hashlib.sha256(message.encode("utf-8")).hexdigest(),
        },
    }


def build_phase11_chat_approval_handoff_queue_contract(
    vault_root: str | Path,
    *,
    message: str | None = None,
    explicit_intent: str | None = None,
) -> dict[str, Any]:
    """Build the read-only queue handoff contract for a Chat proposal."""

    vault = Path(vault_root).resolve()
    normalized_message = _norm(message)
    router = build_phase11_chat_router_contract(
        vault,
        message=normalized_message,
        explicit_intent=explicit_intent,
    )
    provider_readiness = build_studio_provider_readiness(vault)
    route = router.get("route_decision") or {}
    input_posture = router.get("input_posture") or {}
    intent = str((router.get("intent_result") or {}).get("intent_class") or "")
    proposal_card_present = intent in QUEUEABLE_INTENTS and bool(route.get("proposal_required"))
    action_spec = _action_spec_preview(intent, normalized_message)

    blockers: list[str] = []
    if intent not in QUEUEABLE_INTENTS:
        blockers.append("intent_not_supported_for_chat_approval_queue_handoff")
    if not proposal_card_present:
        blockers.append("proposal_card_not_available")
    if not route.get("approval_required"):
        blockers.append("operator_approval_not_required_for_readonly_preview")
    if input_posture.get("prompt_injection_suspected"):
        blockers.append("prompt_injection_indicator_present")
    if route.get("model_route_required") and route.get("provider_route_status") != "route_contract_satisfied":
        blockers.append("provider_route_contract_not_satisfied")
    blockers.extend(
        [
            "operator_explicit_queue_write_approval_missing",
            "chat_approval_queue_writer_not_enabled",
            "approval_execution_not_enabled",
        ]
    )

    preview_ready = bool(action_spec) and "prompt_injection_indicator_present" not in blockers

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "status": FINAL_CLOSEOUT_STATUS,
        "summary": {
            "intent_class": intent,
            "message_present": bool(normalized_message),
            "proposal_handoff_preview_ready": preview_ready,
            "queue_write_allowed_now": False,
            "approval_request_created": False,
            "approval_execution_allowed": False,
            "target_path_preview": (action_spec or {}).get("target_path"),
            "blocker_count": len(list(dict.fromkeys(blockers))),
        },
        "source_contracts": {
            "chat_panel_contract": {
                "surface": "phase11_chat_panel_readonly_contract",
                "model_version": "studio.phase11_chat_panel_contract.v1",
                "readiness": {
                    "chat_panel_contract_ready": True,
                    "approval_handoff_queue_contract_visible": True,
                },
            },
            "router_contract": {
                "surface": router.get("surface"),
                "model_version": router.get("model_version"),
            },
            "provider_readiness_contract": {
                "surface": provider_readiness.get("surface"),
                "model_version": provider_readiness.get("model_version"),
            },
        },
        "handoff_queue_preview": {
            "visible": True,
            "queue_contract_ready": True,
            "queue_write_allowed_now": False,
            "approval_request_created": False,
            "approval_artifact_path_preview": "runtime/studio/approvals/<future-approval-id>.json",
            "queue_writer": "runtime.studio.service.StudioService.queue_for_approval",
            "queue_writer_called": False,
            "future_status_if_written": "pending",
            "required_approval_class": _approval_class(intent),
            "future_operator_action": "explicit_chat_queue_write_request_required",
        },
        "future_action_spec_preview": action_spec,
        "proposal_card_preview": _proposal_card_preview(
            intent=intent,
            message=normalized_message,
            action_spec=action_spec,
            blockers=blockers,
            route=route,
        ),
        "lower_phase_routing_notes": _lower_phase_routing_notes(intent, action_spec, normalized_message),
        "preflight_checks": {
            "chat_panel_contract_ready": True,
            "proposal_card_present": proposal_card_present,
            "approval_required": bool(route.get("approval_required")),
            "prompt_injection_absent": not bool(input_posture.get("prompt_injection_suspected")),
            "provider_route_ready_if_required": (
                route.get("provider_route_status") == "route_contract_satisfied"
                if route.get("model_route_required")
                else True
            ),
            "live_routing_allowed_now": False,
            "mutation_target_preview_safe": bool(action_spec and str(action_spec.get("target_path", "")).endswith(".md")),
        },
        "blocked_reasons": list(dict.fromkeys(blockers)),
        "authority": {
            "read_only": True,
            "queue_write_allowed": False,
            "approval_request_write_allowed": False,
            "approval_execution_allowed": False,
            "vault_writes_allowed": False,
            "provider_calls_allowed": False,
            "runtime_dispatch_allowed": False,
            "browser_control_allowed": False,
            "conversation_persistence_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "denied_by_this_surface": [
            "studio_service_queue_for_approval_call",
            "approval_artifact_write",
            "approval_grant_or_reject",
            "approval_execution",
            "vault_file_write",
            "provider_api_call",
            "runtime_dispatch",
            "browser_control",
            "conversation_log_write",
            "canonical_writeback",
        ],
        "final_closeout_evidence": {
            "original_phase11_chat_objective_closed": True,
            "approval_handoff_queue_contract_closed": True,
            "queue_write_contract_previewed": True,
            "queue_write_performed": False,
            "approval_request_created": False,
            "live_execution_performed": False,
            "remaining_work_is_post_closeout": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
    }
