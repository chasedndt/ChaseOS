"""Phase 11 Studio Chat panel contract.

The panel contract is a Studio-facing consumer of the Phase 11 chat router and
provider readiness contracts. It may render intent/provider/proposal posture
and, after Phase 11 queue-write proof, request one approval-gated queue artifact.
It must not generate chat answers, call providers, persist conversations,
execute approvals, dispatch runtimes, control browsers, or write target vault files.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.phase11_chat_router_contract import (
    SLASH_INTENT_MAP,
    build_phase11_chat_router_contract,
)
from runtime.studio.provider_readiness import build_studio_provider_readiness
from runtime.studio.phase11_chat_browser_dispatch_readiness import (
    build_phase11_chat_browser_dispatch_readiness,
)
from runtime.studio.phase11_chat_approval_consumption_readiness import (
    build_phase11_chat_approval_consumption_readiness,
)
from runtime.studio.phase11_chat_companion_status import build_phase11_chat_companion_status
from runtime.studio.phase11_chat_companion_selection_preview import (
    build_phase11_chat_companion_selection_preview,
)
from runtime.studio.phase11_chat_companion_selection_queue_write_readiness import (
    build_phase11_chat_companion_selection_queue_write_readiness,
)
from runtime.studio.phase11_chat_companion_selection_approval_consumption_readiness import (
    build_phase11_chat_companion_selection_approval_consumption_readiness,
)
from runtime.studio.phase11_companion_roster_ui_preview import build_phase11_companion_roster_ui_preview
from runtime.studio.phase11_companion_memory_boundary_contract import (
    build_phase11_companion_memory_boundary_contract,
)
from runtime.studio.phase11_companion_memory_approval_preview import (
    build_phase11_companion_memory_approval_preview,
)
from runtime.studio.phase11_companion_memory_approved_execution_proof import (
    NEXT_RECOMMENDED_PASS as COMPANION_MEMORY_EXECUTION_NEXT_PASS,
    PASS_ID as COMPANION_MEMORY_EXECUTION_PASS_ID,
    STATUS as COMPANION_MEMORY_EXECUTION_STATUS,
    SURFACE_ID as COMPANION_MEMORY_EXECUTION_SURFACE_ID,
)
from runtime.studio.phase11_companion_memory_readback_search_preview import (
    NEXT_RECOMMENDED_PASS as COMPANION_MEMORY_READBACK_NEXT_PASS,
    build_phase11_companion_memory_readback_search_preview,
)
from runtime.studio.phase11_companion_memory_ledger_write_approval_preview import (
    NEXT_RECOMMENDED_PASS as COMPANION_MEMORY_LEDGER_WRITE_NEXT_PASS,
    build_phase11_companion_memory_ledger_write_approval_preview,
)
from runtime.studio.phase11_companion_memory_approved_ledger_write_execution_proof import (
    NEXT_RECOMMENDED_PASS as COMPANION_MEMORY_LEDGER_EXECUTION_NEXT_PASS,
    PASS_ID as COMPANION_MEMORY_LEDGER_EXECUTION_PASS_ID,
    STATUS as COMPANION_MEMORY_LEDGER_EXECUTION_STATUS,
    SURFACE_ID as COMPANION_MEMORY_LEDGER_EXECUTION_SURFACE_ID,
)
from runtime.studio.phase11_companion_memory_ledger_read_model_preview import (
    NEXT_RECOMMENDED_PASS as COMPANION_MEMORY_LEDGER_READ_MODEL_NEXT_PASS,
    build_phase11_companion_memory_ledger_read_model_preview,
)
from runtime.studio.phase11_companion_memory_real_ledger_activation_closeout import (
    NEXT_RECOMMENDED_PASS as COMPANION_MEMORY_REAL_LEDGER_CLOSEOUT_NEXT_PASS,
    build_phase11_companion_memory_real_ledger_activation_closeout,
)
from runtime.studio.phase11_companion_memory_context_readiness_preview import (
    NEXT_RECOMMENDED_PASS as COMPANION_MEMORY_CONTEXT_READINESS_NEXT_PASS,
    build_phase11_companion_memory_context_readiness_preview,
)
from runtime.studio.phase11_chat_readonly_slash_command_responses import (
    NEXT_RECOMMENDED_PASS as READONLY_SLASH_COMMAND_RESPONSES_NEXT_PASS,
    build_phase11_chat_readonly_slash_command_responses,
)
from runtime.studio.phase11_chat_workspaces_foundation import build_phase11_chat_workspaces_foundation
from runtime.studio.phase11_chat_workspace_proposal_writer import build_phase11_chat_workspace_proposal_writer
from runtime.studio.phase11_chat_workspace_proposal_consumption_executor import (
    NEXT_RECOMMENDED_PASS as WORKSPACE_PROPOSAL_CONSUMPTION_NEXT_PASS,
    PASS_ID as WORKSPACE_PROPOSAL_CONSUMPTION_PASS_ID,
    STATUS as WORKSPACE_PROPOSAL_CONSUMPTION_STATUS,
    SURFACE_ID as WORKSPACE_PROPOSAL_CONSUMPTION_SURFACE_ID,
)
from runtime.studio.phase11_chat_workspace_target_state_executor import (
    NEXT_RECOMMENDED_PASS as WORKSPACE_TARGET_STATE_NEXT_PASS,
    PASS_ID as WORKSPACE_TARGET_STATE_PASS_ID,
    STATUS as WORKSPACE_TARGET_STATE_STATUS,
    SURFACE_ID as WORKSPACE_TARGET_STATE_SURFACE_ID,
)
from runtime.studio.phase11_chat_route_state_and_message_drafts import (
    NEXT_RECOMMENDED_PASS as CHAT_ROUTE_STATE_NEXT_PASS,
    PASS_ID as CHAT_ROUTE_STATE_PASS_ID,
    STATUS as CHAT_ROUTE_STATE_STATUS,
    SURFACE_ID as CHAT_ROUTE_STATE_SURFACE_ID,
    build_phase11_chat_route_state_and_message_drafts,
)
from runtime.studio.phase11_chat_runtime_board_handoff_proposal import (
    NEXT_RECOMMENDED_PASS as CHAT_RUNTIME_BOARD_HANDOFF_NEXT_PASS,
    PASS_ID as CHAT_RUNTIME_BOARD_HANDOFF_PASS_ID,
    STATUS_PREVIEW as CHAT_RUNTIME_BOARD_HANDOFF_STATUS,
    SURFACE_ID as CHAT_RUNTIME_BOARD_HANDOFF_SURFACE_ID,
    build_phase11_chat_runtime_board_handoff_proposal,
)
from runtime.studio.phase11_chat_schedule_proposal_packet import (
    NEXT_RECOMMENDED_PASS as CHAT_SCHEDULE_PROPOSAL_NEXT_PASS,
    PASS_ID as CHAT_SCHEDULE_PROPOSAL_PASS_ID,
    STATUS_PREVIEW as CHAT_SCHEDULE_PROPOSAL_STATUS,
    SURFACE_ID as CHAT_SCHEDULE_PROPOSAL_SURFACE_ID,
    build_phase11_chat_schedule_proposal_packet,
)
from runtime.studio.phase11_chat_schedule_proposal_consumption_executor import (
    NEXT_RECOMMENDED_PASS as CHAT_SCHEDULE_PROPOSAL_CONSUMPTION_NEXT_PASS,
    PASS_ID as CHAT_SCHEDULE_PROPOSAL_CONSUMPTION_PASS_ID,
    STATUS as CHAT_SCHEDULE_PROPOSAL_CONSUMPTION_STATUS,
    SURFACE_ID as CHAT_SCHEDULE_PROPOSAL_CONSUMPTION_SURFACE_ID,
)
from runtime.studio.phase11_chat_approved_schedule_intent_writer import (
    NEXT_RECOMMENDED_PASS as CHAT_APPROVED_SCHEDULE_INTENT_WRITER_NEXT_PASS,
    PASS_ID as CHAT_APPROVED_SCHEDULE_INTENT_WRITER_PASS_ID,
    STATUS as CHAT_APPROVED_SCHEDULE_INTENT_WRITER_STATUS,
    SURFACE_ID as CHAT_APPROVED_SCHEDULE_INTENT_WRITER_SURFACE_ID,
)
from runtime.studio.phase11_chat_schedule_intent_activation_readiness import (
    NEXT_RECOMMENDED_PASS as CHAT_SCHEDULE_INTENT_ACTIVATION_NEXT_PASS,
    PASS_ID as CHAT_SCHEDULE_INTENT_ACTIVATION_PASS_ID,
    STATUS_PREVIEW as CHAT_SCHEDULE_INTENT_ACTIVATION_STATUS,
    SURFACE_ID as CHAT_SCHEDULE_INTENT_ACTIVATION_SURFACE_ID,
)
from runtime.studio.phase11_chat_approved_schedule_activation_executor import (
    NEXT_RECOMMENDED_PASS as CHAT_APPROVED_SCHEDULE_ACTIVATION_NEXT_PASS,
    PASS_ID as CHAT_APPROVED_SCHEDULE_ACTIVATION_PASS_ID,
    STATUS as CHAT_APPROVED_SCHEDULE_ACTIVATION_STATUS,
    SURFACE_ID as CHAT_APPROVED_SCHEDULE_ACTIVATION_SURFACE_ID,
)
from runtime.studio.phase11_chat_schedule_adapter_export_readiness import (
    NEXT_RECOMMENDED_PASS as CHAT_SCHEDULE_ADAPTER_EXPORT_NEXT_PASS,
    PASS_ID as CHAT_SCHEDULE_ADAPTER_EXPORT_PASS_ID,
    STATUS_PREVIEW as CHAT_SCHEDULE_ADAPTER_EXPORT_STATUS,
    SURFACE_ID as CHAT_SCHEDULE_ADAPTER_EXPORT_SURFACE_ID,
)
from runtime.studio.phase11_chat_approved_schedule_adapter_export_packet_writer import (
    NEXT_RECOMMENDED_PASS as CHAT_APPROVED_SCHEDULE_ADAPTER_EXPORT_WRITER_NEXT_PASS,
    PASS_ID as CHAT_APPROVED_SCHEDULE_ADAPTER_EXPORT_WRITER_PASS_ID,
    STATUS as CHAT_APPROVED_SCHEDULE_ADAPTER_EXPORT_WRITER_STATUS,
    SURFACE_ID as CHAT_APPROVED_SCHEDULE_ADAPTER_EXPORT_WRITER_SURFACE_ID,
)
from runtime.studio.phase11_chat_schedule_ui_action_controls_and_readback import (
    NEXT_RECOMMENDED_PASS as CHAT_SCHEDULE_UI_ACTION_CONTROLS_NEXT_PASS,
    PASS_ID as CHAT_SCHEDULE_UI_ACTION_CONTROLS_PASS_ID,
    STATUS as CHAT_SCHEDULE_UI_ACTION_CONTROLS_STATUS,
    SURFACE_ID as CHAT_SCHEDULE_UI_ACTION_CONTROLS_SURFACE_ID,
    build_phase11_chat_schedule_ui_action_controls_and_readback,
)
from runtime.studio.phase11_chat_authority_tier_controls import (
    NEXT_RECOMMENDED_PASS as CHAT_AUTHORITY_TIER_CONTROLS_NEXT_PASS,
    PASS_ID as CHAT_AUTHORITY_TIER_CONTROLS_PASS_ID,
    STATUS as CHAT_AUTHORITY_TIER_CONTROLS_STATUS,
    SURFACE_ID as CHAT_AUTHORITY_TIER_CONTROLS_SURFACE_ID,
    build_phase11_chat_authority_tier_controls,
)
from runtime.studio.phase11_chat_authority_execution_controls import (
    NEXT_RECOMMENDED_PASS as CHAT_AUTHORITY_EXECUTION_CONTROLS_NEXT_PASS,
    PASS_ID as CHAT_AUTHORITY_EXECUTION_CONTROLS_PASS_ID,
    STATUS_PREVIEW as CHAT_AUTHORITY_EXECUTION_CONTROLS_STATUS,
    SURFACE_ID as CHAT_AUTHORITY_EXECUTION_CONTROLS_SURFACE_ID,
    build_phase11_chat_authority_execution_controls,
)
from runtime.studio.workspace_mode_panel import MODE_QUERY_PARAM, build_workspace_mode_studio_panel


MODEL_VERSION = "studio.phase11_chat_panel_contract.v1"
SURFACE_ID = "phase11_chat_panel_readonly_contract"
CLOSEOUT_STATUS = "COMPLETE / APPROVAL-GATED / VERIFIED / LIVE EXECUTION BLOCKED"
NEXT_RECOMMENDED_PASS = READONLY_SLASH_COMMAND_RESPONSES_NEXT_PASS

DENIED_ACTION_EXPLANATIONS: dict[str, dict[str, str]] = {
    "vault_write": {
        "missing_contract": "Phase 9/10 governed write contract with Gate approval and audit writeback is absent for chat.",
        "affected_phase10_or_phase11_surface": "Phase 11 Chat panel/router",
        "lower_phase_owner_or_surface": "Phase 9 AOR/Gate writeback policy and Phase 10 Studio service writer",
        "minimum_proof_needed": "approved lower-phase write contract, exact target scope, no-write preflight, and audit artifact proof",
        "blocked_action_reason": "Chat is explanation-only and cannot mutate vault files.",
    },
    "runtime_dispatch": {
        "missing_contract": "Agent Bus/AOR dispatch envelope is not consumable from this Phase 11 panel.",
        "affected_phase10_or_phase11_surface": "Phase 11 Chat runtime dispatch posture",
        "lower_phase_owner_or_surface": "runtime/agent_bus plus AOR workflow manifest",
        "minimum_proof_needed": "structured bus packet contract, approval envelope, idempotency proof, and dispatch executor review",
        "blocked_action_reason": "Chat may preview dispatch readiness but cannot create tasks or launch workflows.",
    },
    "browser_or_shell_or_connector_authority": {
        "missing_contract": "Browser, shell, connector, and provider execution authority is not granted to this surface.",
        "affected_phase10_or_phase11_surface": "Phase 11 Chat browser/provider execution posture",
        "lower_phase_owner_or_surface": "Phase 9 runtime adapter/Gate policy and explicit connector manifests",
        "minimum_proof_needed": "approved executor contract, scoped credentials, no-secret rendering proof, and operator approval",
        "blocked_action_reason": "Chat cannot launch browsers, run shell commands, call connectors, or call providers.",
    },
    "approval_consumption": {
        "missing_contract": "Approval consumption and exact-once marker writer are not enabled from chat.",
        "affected_phase10_or_phase11_surface": "Phase 11 Chat approval consumption readiness",
        "lower_phase_owner_or_surface": "Gate approval consumer and idempotency marker policy",
        "minimum_proof_needed": "approved consumption record contract, replay guard, marker path proof, and target no-mutation test",
        "blocked_action_reason": "Chat can explain approval state but cannot grant, reject, consume, or execute approvals.",
    },
    "protected_file_write": {
        "missing_contract": "Protected control document mutation requires explicit Gate/protected-file workflow approval.",
        "affected_phase10_or_phase11_surface": "Phase 11 Chat protected-file denial UX",
        "lower_phase_owner_or_surface": "Permission Matrix, Trust Tiers, Gate rules, and protected-file workflow",
        "minimum_proof_needed": "operator-approved protected-file change packet and canonical governance review",
        "blocked_action_reason": "Protected files are outside Chat authority.",
    },
    "hidden_memory_write": {
        "missing_contract": "Hidden/runtime memory write contract is absent for this panel.",
        "affected_phase10_or_phase11_surface": "Phase 11 Chat context display",
        "lower_phase_owner_or_surface": "ChaseOS memory boundary and future runtime memory policy",
        "minimum_proof_needed": "inspectable memory write contract, retention policy, and operator approval",
        "blocked_action_reason": "Chat renders context read-only and cannot silently persist memory.",
    },
    "credential_or_config_mutation": {
        "missing_contract": "Provider/credential/config mutation path is not exposed through chat.",
        "affected_phase10_or_phase11_surface": "Phase 11 Chat provider/settings posture",
        "lower_phase_owner_or_surface": "Studio Settings / Provider / Runtime Config panels under Gate policy",
        "minimum_proof_needed": "settings writer contract, redacted preview, approval, and rollback proof",
        "blocked_action_reason": "Chat cannot show or mutate credentials/configuration.",
    },
    "source_pack_promotion": {
        "missing_contract": "Source-pack creation/promotion contracts remain lower-phase and approval-gated.",
        "affected_phase10_or_phase11_surface": "Phase 11 Chat source-pack denial UX",
        "lower_phase_owner_or_surface": "Source-pack/Gate promotion pipeline",
        "minimum_proof_needed": "source-pack contract, validation proof, operator approval, and promotion audit",
        "blocked_action_reason": "Chat cannot create, apply, or promote source packs.",
    },
    "graph_mutation": {
        "missing_contract": "Graph mutation policy is not writable from chat.",
        "affected_phase10_or_phase11_surface": "Phase 11 Chat graph context display",
        "lower_phase_owner_or_surface": "graph mutation policy and canonical graph maintenance workflow",
        "minimum_proof_needed": "graph delta contract, protected-surface review, and no-canonical-bypass proof",
        "blocked_action_reason": "Chat can describe graph state but cannot mutate graph truth.",
    },
    "canonical_knowledge_promotion": {
        "missing_contract": "Canonical knowledge promotion requires Gate review outside this panel.",
        "affected_phase10_or_phase11_surface": "Phase 11 Chat canonical promotion denial UX",
        "lower_phase_owner_or_surface": "ChaseOS Gate and canonical knowledge promotion workflow",
        "minimum_proof_needed": "candidate artifact, provenance proof, Gate decision, and indexed Agent-Activity audit",
        "blocked_action_reason": "Chat cannot promote or mutate canonical knowledge.",
    },
}

POST_CLOSEOUT_FUTURE_WORK = [
    "chat_originated_approval_queue_write_surface",
    "conversation_persistence",
    "live_provider_execution",
    "approval_consumption_readiness",
    "browser_runtime_dispatch",
    "companion_status_readonly",
]

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
    "runtime-task": "studio_runtime_action_approval_future",
    "browser-task": "studio_browser_action_approval_future",
    "scheduled-workflow": "studio_schedule_mutation_approval_future",
    "approval-action": "studio_approval_action_review_future",
    "chat-answer": "chat_live_execution_approval_future",
    "model-chat": "chat_live_execution_approval_future",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(message: str | None) -> str:
    return " ".join(str(message or "").strip().split())


def _first_slash_token(message: str) -> str | None:
    if not message.startswith("/"):
        return None
    token = message.split(maxsplit=1)[0].strip().lower()
    return token or None


def _requested_companion_runtime(message: str) -> str | None:
    tokens = message.lower().split()
    for marker in {"/companion", "/pet"}:
        if marker in tokens:
            index = tokens.index(marker)
            if len(tokens) > index + 1 and tokens[index + 1] not in {"status", "list", "show"}:
                return tokens[index + 1]
    for runtime_id in {"hermes", "openclaw", "archon"}:
        if runtime_id in tokens:
            return runtime_id
    return None


def _requested_memory_class(message: str) -> str:
    lowered = str(message or "").lower()
    for memory_class in ("preference", "interaction_pattern", "tone_feedback", "operator_note", "session_observation"):
        if memory_class in lowered or memory_class.replace("_", " ") in lowered:
            return memory_class
    return "operator_note"


def _requested_memory_query(message: str) -> str:
    text = _norm(message).lower()
    for prefix in ("/memory search", "/memory readback", "/memory find"):
        if text.startswith(prefix):
            return _norm(text[len(prefix) :])
    if text.startswith("/memory"):
        parts = text.split(maxsplit=2)
        return parts[2] if len(parts) > 2 and parts[1] in {"search", "readback", "find"} else ""
    return text if "memory" in text and "search" in text else ""


def _requested_approval_id(message: str) -> str | None:
    for token in _norm(message).split():
        cleaned = token.strip(".,;:()[]{}<>")
        if cleaned.startswith("companion-memory-ledger-appr-"):
            return cleaned
        if len(cleaned) == 36 and cleaned.count("-") == 4:
            return cleaned
    return None


def _approval_class(intent: str, route: dict[str, Any]) -> str:
    if route.get("model_route_required"):
        return "chat_live_execution_approval_future"
    if route.get("approval_required") or route.get("proposal_required"):
        return APPROVAL_CLASS_BY_INTENT.get(intent, "studio_operator_approval_future")
    return "none_required_for_readonly_preview"


def _proposal_target_preview(intent: str) -> str:
    targets = {
        "project-create": "01_PROJECTS/_chat_proposals/<project-slug>.md",
        "project-update": "01_PROJECTS/<project>/PROJECT.md",
        "vault-node-create": "02_KNOWLEDGE/_chat_proposals/<node-slug>.md",
        "vault-node-update": "02_KNOWLEDGE/<node>.md",
        "source-note": "03_INPUTS/00_QUARANTINE/_chat_source_notes/<source-slug>.md",
        "synthesis-note": "07_LOGS/Operator-Briefs/_chat_synthesis/<brief-slug>.md",
        "rnd-entry": "07_LOGS/RD/_chat_entries/<entry-slug>.md",
        "roadmap-item": "ROADMAP.md",
        "memory-save": "runtime/memory/_chat_proposals/<memory-slug>.json",
        "handoff": "runtime/agent_bus/_chat_handoffs/<handoff-slug>.json",
        "archive": "99_ARCHIVE/_chat_proposals/<archive-slug>.md",
    }
    return targets.get(intent, "07_LOGS/Operator-Briefs/_chat_proposals/<proposal-slug>.md")


def _proposal_card(intent: str, route: dict[str, Any]) -> dict[str, Any] | None:
    if not route.get("proposal_required"):
        return None
    title = PROPOSAL_LABELS.get(intent, "Proposal preview")
    target_path = _proposal_target_preview(intent)
    approval_class = _approval_class(intent, route)
    blocked_reasons = list(
        dict.fromkeys(
            [
                *(route.get("blocked_reasons") or []),
                "operator_approval_missing",
                "approval_queue_write_blocked_from_chat",
                "dry_run_preview_only",
            ]
        )
    )
    return {
        "visible": True,
        "intent_class": intent,
        "title": title,
        "summary": {
            "headline": title,
            "one_line": f"Chat can prepare a reviewable {intent} proposal preview, but cannot queue or execute it.",
            "operator_control_copy": "Review only: operator approval and lower-phase contracts stay required before any mutation.",
        },
        "affected_files_systems": [
            {
                "kind": "target_artifact_preview",
                "path_preview": target_path,
                "write_allowed_now": False,
                "authority_required": approval_class,
            },
            {
                "kind": "approval_center",
                "system": "Studio Approval Center",
                "write_allowed_now": False,
                "authority_required": "future_approval_queue_handoff_contract",
            },
            {
                "kind": "governance",
                "system": "ChaseOS Gate / AOR",
                "write_allowed_now": False,
                "authority_required": "operator_gate_review",
            },
        ],
        "required_approval": {
            "required": bool(route.get("approval_required")),
            "class": approval_class,
            "approval_center_copy": "Approval required before any queue write, file mutation, runtime dispatch, or canonical promotion.",
            "operator_decision_allowed_from_chat": False,
            "approval_consumption_allowed_from_chat": False,
        },
        "blocked_reasons": blocked_reasons,
        "dry_run_preview": {
            "visible": True,
            "preview_only": True,
            "action_type": intent,
            "next_surface": route.get("next_surface"),
            "target_path_preview": target_path,
            "approval_request_created": False,
            "writes_queued": False,
            "target_file_written": False,
            "runtime_dispatch_started": False,
            "browser_or_shell_started": False,
            "canonical_mutation_allowed": False,
        },
        "handback_buttons": [
            {
                "label": "Revise request",
                "action": "revise_chat_request",
                "enabled": True,
                "side_effect": "none",
            },
            {
                "label": "Send to Approval Center",
                "action": "preview_approval_center_handoff",
                "enabled": False,
                "disabled_reason": "approval_queue_write_blocked_from_chat",
                "side_effect": "none_preview_only",
            },
            {
                "label": "Copy dry-run preview",
                "action": "copy_dry_run_preview",
                "enabled": True,
                "side_effect": "clipboard_only",
            },
            {
                "label": "Hand back to lower-phase owner",
                "action": "route_lower_phase_dependency",
                "enabled": False,
                "disabled_reason": "agent_bus_task_write_blocked_from_chat",
                "side_effect": "none_preview_only",
            },
        ],
        "preview_only": True,
        "writes_queued": False,
        "approval_request_created": False,
        "approval_required_before_mutation": bool(route.get("approval_required")),
        "required_approval_class": approval_class,
        "next_surface": route.get("next_surface"),
        "required_next_step": "future_approval_gated_proposal_surface",
        "post_closeout_future_work": "chat_originated_approval_queue_write_surface",
    }


def _workspace_mode_deeplink_selector(workspace_mode_panel: dict[str, Any]) -> dict[str, Any]:
    """Return Chat-safe WML mode links without granting execution authority."""

    selector = workspace_mode_panel.get("mode_selector") or {}
    options = list(selector.get("options") or [])
    cards: list[dict[str, Any]] = []
    for option in options:
        mode_id = str(option.get("id") or "")
        if not mode_id:
            continue
        studio_href = "/#workspace-mode" if mode_id == "all" else f"/?{MODE_QUERY_PARAM}={mode_id}#workspace-mode"
        json_href = (
            "/workspace-mode-panel.json"
            if mode_id == "all"
            else f"/workspace-mode-panel.json?{MODE_QUERY_PARAM}={mode_id}"
        )
        projects = list(option.get("projects") or [])
        domains = list(option.get("domains") or [])
        routes = list(option.get("routes") or [])
        cards.append(
            {
                "id": mode_id,
                "mode": mode_id,
                "label": option.get("label") or mode_id,
                "purpose": option.get("purpose") or "",
                "default_posture": option.get("default_posture") or "",
                "selected": bool(option.get("selected")),
                "read_only": True,
                "studio_href": studio_href,
                "json_href": json_href,
                "query_param": MODE_QUERY_PARAM,
                "project_count": int(option.get("project_count") or len(projects)),
                "domain_count": int(option.get("domain_count") or len(domains)),
                "route_count": int(option.get("route_count") or len(routes)),
                "ready_route_count": int(option.get("ready_route_count") or 0),
                "blocked_route_count": int(option.get("blocked_route_count") or 0),
                "project_previews": [
                    {
                        "name": project.get("name") or project.get("project") or project.get("id") or "project",
                        "domain": project.get("domain") or "unknown",
                        "status": project.get("status") or "unknown",
                    }
                    for project in projects[:4]
                ],
                "domain_previews": [
                    {
                        "name": domain.get("domain") or domain.get("name") or "domain",
                        "primary_mode": domain.get("primary_mode") or mode_id,
                        "project_count": int(domain.get("project_count") or 0),
                    }
                    for domain in domains[:4]
                ],
                "route_previews": [
                    {
                        "workspace_path": route.get("workspace_path") or "",
                        "workflow_id": route.get("workflow_id") or "",
                        "ready_for_aor_dispatch": bool(
                            route.get("ready_for_aor_dispatch") or route.get("ready")
                        ),
                    }
                    for route in routes[:4]
                ],
                "hidden_project_count": max(0, len(projects) - 4),
                "hidden_domain_count": max(0, len(domains) - 4),
                "hidden_route_count": max(0, len(routes) - 4),
                "navigation_only": True,
                "execution_allowed": False,
                "profile_write_allowed": False,
                "workflow_dispatch_allowed": False,
                "agent_bus_task_write_allowed": False,
                "canonical_mutation_allowed": False,
            }
        )

    return {
        "visible": True,
        "surface": "phase11_chat_workspace_mode_deeplink_selector",
        "source_surface": workspace_mode_panel.get("surface"),
        "read_only": True,
        "navigation_only": True,
        "query_param": MODE_QUERY_PARAM,
        "selected_mode": selector.get("selected_mode") or "all",
        "selected_mode_label": selector.get("selected_mode_label") or "All Modes",
        "card_count": len(cards),
        "cards": cards,
        "default_studio_href": "/#workspace-mode",
        "default_json_href": "/workspace-mode-panel.json",
        "chat_can_open_studio_workspace_mode": True,
        "chat_can_execute_workspace_mode": False,
        "chat_can_write_workspace_profiles": False,
        "chat_can_dispatch_workspace_workflows": False,
        "chat_can_write_agent_bus_tasks": False,
        "chat_can_mutate_canonical_state": False,
        "next_recommended_pass": "workspace-mode-chat-deeplink-selector-visual-qa",
    }


def _command_preview(message: str, intent: str, route: dict[str, Any]) -> dict[str, Any]:
    slash = _first_slash_token(message)
    known = bool(slash and slash in SLASH_INTENT_MAP)
    return {
        "visible": slash is not None,
        "slash_token": slash,
        "slash_command_known": known,
        "intent_class": intent if slash else None,
        "route_family": route.get("route_family") if slash else None,
        "next_surface": route.get("next_surface") if slash else None,
        "preview_only": True,
        "execution_allowed": False,
        "unknown_slash_commands_execute": False,
    }


def _conversation_rendering(message: str, intent: str | None) -> dict[str, Any]:
    user_text = message or "Open Phase 11 Chat"
    assistant_text = (
        "Runtime status is available as read-only context."
        if intent == "dashboard-query"
        else "This Phase 11 chat panel can explain state and route posture, but it cannot execute, write, dispatch, or consume approvals."
    )
    return {
        "visible": True,
        "source": "in_memory_fixture_preview",
        "read_only": True,
        "writeback_allowed": False,
        "conversation_log_writer_called": False,
        "message_count": 2,
        "messages": [
            {"role": "user", "content": user_text[:600], "rendered_from_fixture": True},
            {"role": "assistant", "content": assistant_text, "rendered_from_fixture": True},
        ],
    }


def _system_context_display(vault: Path) -> dict[str, Any]:
    return {
        "visible": True,
        "read_only": True,
        "chaseos_phase": "Phase 11",
        "surface": SURFACE_ID,
        "vault_root_visible": str(vault),
        "authority_boundary": "Phase 11 local Studio Chat sits under AOR/Gate governance and may explain current ChaseOS state only.",
        "runtime_lane_language": "Hermes/Optimus runtime lane may render bounded context; OpenClaw/Hermes execution remains lower-phase governed work.",
        "vault_writes_allowed": False,
        "runtime_dispatch_allowed": False,
        "browser_or_shell_or_connector_authority_allowed": False,
        "approval_consumption_allowed": False,
        "hidden_memory_write_allowed": False,
        "canonical_promotion_allowed": False,
    }


def _denied_action_rendering(input_posture: dict[str, Any], safety_policy: dict[str, Any] | None = None) -> dict[str, Any]:
    requested = list(input_posture.get("requested_denied_actions") or [])
    actions = {
        action: {"available_now": False, **details}
        for action, details in DENIED_ACTION_EXPLANATIONS.items()
        if not requested or action in requested
    }
    policy = safety_policy or {}
    return {
        "visible": True,
        "explanation_only": True,
        "all_denied_actions_unavailable": True,
        "requested_denied_actions": requested,
        "policy_status": policy.get("policy_status"),
        "all_capabilities_policy_aware": bool(policy.get("all_capabilities_policy_aware", True)),
        "authority_absent_fails_closed": bool(policy.get("authority_absent_fails_closed", True)),
        "denied_action_classes": policy.get("denied_action_classes", {}),
        "actions": actions,
        "copy": "Unavailable in Phase 11 Chat: this surface can explain state and missing lower-phase contracts, but cannot perform writes, dispatch, approval consumption, execution, hidden memory, or canonical mutation.",
    }


def _approval_handoff_preflight(intent: str, route: dict[str, Any], input_posture: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    if route.get("approval_required"):
        blockers.append("operator_approval_missing")
    if route.get("proposal_required"):
        blockers.append("proposal_surface_not_built_for_chat_execution")
    if route.get("model_route_required") and route.get("provider_route_status") != "route_contract_satisfied":
        blockers.append("provider_route_contract_not_satisfied")
    if input_posture.get("prompt_injection_suspected"):
        blockers.append("prompt_injection_indicator_present")
    blockers.append("chat_approval_handoff_writer_not_built")

    return {
        "preflight_visible": True,
        "approval_handoff_allowed_now": False,
        "approval_request_created": False,
        "approval_queue_write_allowed": False,
        "approval_queue_write_denied": True,
        "mutation_attempt_allowed": False,
        "mutation_write_authority_denied": True,
        "proposed_future_surface": route.get("next_surface") or "manual_review",
        "required_approval_class": _approval_class(intent, route),
        "missing_approval_blocker_present": "operator_approval_missing" in blockers,
        "provider_not_ready_blocker_present": "provider_route_contract_not_satisfied" in blockers,
        "prompt_injection_blocker_present": "prompt_injection_indicator_present" in blockers,
        "blocked_reasons": list(dict.fromkeys(blockers)),
        "future_route": "studio_approval_queue_after_explicit_chat_proposal_pass",
        "post_closeout_future_work": "chat_originated_approval_queue_write_surface",
    }


def _live_routing_gate(route: dict[str, Any], provider_readiness: dict[str, Any]) -> dict[str, Any]:
    provider_summary = provider_readiness.get("summary") or {}
    credential = provider_readiness.get("credential_posture") or {}
    live_probe = provider_readiness.get("live_probe_readiness") or {}
    last_marker = live_probe.get("last_probe_marker") or {}
    last_result = live_probe.get("last_probe_result") or {}
    provider_route_satisfied = route.get("provider_route_status") == "route_contract_satisfied"
    provider_readiness_verified = provider_summary.get("readiness_status") == "verified_by_last_probe_result"
    provider_env_present = bool(credential.get("primary_provider_env_present"))
    last_probe_marker_verified = bool(last_marker and last_result.get("ok"))
    blockers: list[str] = []
    if route.get("model_route_required") and not provider_route_satisfied:
        blockers.append("provider_route_contract_not_satisfied")
    if route.get("model_route_required") and not provider_env_present:
        blockers.append("provider_credential_or_environment_missing")
    if route.get("model_route_required") and not provider_readiness_verified:
        blockers.append("provider_readiness_not_verified_by_last_probe_result")
    if route.get("model_route_required") and not last_probe_marker_verified:
        blockers.append("provider_last_probe_marker_result_not_verified")
    blockers.extend(
        [
            "operator_chat_execution_approval_missing",
            "conversation_persistence_not_built",
        ]
    )

    return {
        "live_routing_allowed_now": False,
        "provider_route_contract_satisfied": provider_route_satisfied,
        "provider_credentials_environment_present": provider_env_present,
        "provider_readiness_verified_by_last_probe_result": provider_readiness_verified,
        "last_probe_marker_result_verified": last_probe_marker_verified,
        "provider_readiness_status": provider_summary.get("readiness_status"),
        "operator_chat_execution_approval_present": False,
        "chat_live_provider_executor_built": True,
        "conversation_persistence_allowed": False,
        "all_future_conditions_satisfied": False,
        "closeout_execution_blocked_by_design": False,
        "blocked_reasons": list(dict.fromkeys(blockers)),
        "live_smoke_allowed_from_chat": provider_env_present,
        "required_future_conditions": [
            "provider_route_contract_satisfied",
            "provider_readiness_verified_by_last_probe_result",
            "provider_credentials_environment_present",
            "operator_chat_execution_approval_present",
            "chat_live_provider_executor_built",
            "conversation_persistence_allowed",
        ],
    }


def build_phase11_chat_panel_contract(
    vault_root: str | Path,
    *,
    message: str | None = None,
    explicit_intent: str | None = None,
) -> dict[str, Any]:
    """Build the native Chat panel read-only contract."""

    vault = Path(vault_root).resolve()
    normalized_message = _norm(message)
    router = build_phase11_chat_router_contract(
        vault,
        message=normalized_message,
        explicit_intent=explicit_intent,
    )
    provider_readiness = build_studio_provider_readiness(vault)
    intent = (router.get("intent_result") or {}).get("intent_class")
    route = router.get("route_decision") or {}
    input_posture = router.get("input_posture") or {}
    provider_summary = provider_readiness.get("summary") or {}
    safety_policy = router.get("safety_policy") or {}
    live_probe = provider_readiness.get("live_probe_readiness") or {}
    queue = provider_readiness.get("queue_readiness") or {}
    last_marker = live_probe.get("last_probe_marker") or {}

    command_preview = _command_preview(normalized_message, str(intent or ""), route)
    readonly_slash_command_responses = build_phase11_chat_readonly_slash_command_responses(
        vault,
        message=normalized_message,
    )
    from runtime.studio.phase11_chat_approval_handoff_queue_contract import (
        build_phase11_chat_approval_handoff_queue_contract,
    )
    from runtime.studio.phase11_chat_conversation_persistence_contract import (
        build_phase11_chat_conversation_persistence_contract,
    )
    from runtime.studio.phase11_chat_approval_queue_write import (
        build_phase11_chat_approval_queue_write_execution_proof,
    )
    from runtime.studio.phase11_chat_live_provider_approval_preview import (
        build_phase11_chat_live_provider_execution_approval_preview,
    )
    from runtime.studio.phase11_chat_runtime_dispatch_readiness import (
        build_phase11_chat_runtime_dispatch_readiness,
        build_phase11_chat_runtime_status_explanation,
    )

    approval_queue_contract = build_phase11_chat_approval_handoff_queue_contract(
        vault,
        message=normalized_message,
        explicit_intent=explicit_intent,
    )
    conversation_persistence_contract = build_phase11_chat_conversation_persistence_contract(
        vault,
        message=normalized_message,
        explicit_intent=explicit_intent,
    )
    approval_queue_write_proof = build_phase11_chat_approval_queue_write_execution_proof(
        vault,
        message=normalized_message,
        explicit_intent=explicit_intent,
        write_approval=False,
    )
    live_provider_approval_preview = build_phase11_chat_live_provider_execution_approval_preview(
        vault,
        message=normalized_message,
        explicit_intent=explicit_intent or str(intent or "chat-answer"),
    )
    runtime_dispatch_intent = explicit_intent or (
        str(intent or "") if str(intent or "") in {"runtime-task", "handoff", "scheduled-workflow"} else "runtime-task"
    )
    runtime_dispatch_readiness = build_phase11_chat_runtime_dispatch_readiness(
        vault,
        message=normalized_message,
        explicit_intent=runtime_dispatch_intent,
    )
    chat_workspaces_foundation = build_phase11_chat_workspaces_foundation(
        vault,
        message=normalized_message,
        explicit_intent=explicit_intent,
    )
    chat_workspaces_summary = chat_workspaces_foundation.get("summary") or {}
    chat_workspace_proposal_writer = build_phase11_chat_workspace_proposal_writer(
        vault,
        message=normalized_message,
        proposal_kind=None,
        write_approval=False,
    )
    chat_workspace_proposal_summary = chat_workspace_proposal_writer.get("summary") or {}
    chat_workspace_proposal_consumption_executor = {
        "ok": True,
        "surface": WORKSPACE_PROPOSAL_CONSUMPTION_SURFACE_ID,
        "pass": WORKSPACE_PROPOSAL_CONSUMPTION_PASS_ID,
        "status": "AVAILABLE / APPROVAL-CONSUMPTION API / WORKSPACE PROPOSAL RECORD ONLY",
        "summary": {
            "executor_available": True,
            "approval_id_required": True,
            "expected_proposal_digest_required": True,
            "approval_consumption_allowed_through_explicit_executor": True,
            "ambient_chat_consumption_allowed": False,
            "generic_studio_service_execution_allowed": False,
            "target_workspace_proposal_write_allowed": True,
            "chat_workspace_create_allowed": False,
            "chat_folder_create_allowed": False,
            "chat_thread_create_allowed": False,
            "chat_message_send_allowed": False,
            "discord_api_calls_allowed": False,
            "discord_thread_create_allowed": False,
            "agent_bus_task_write_allowed": False,
            "runtime_board_write_allowed": False,
            "schedule_mutation_allowed": False,
            "provider_calls_allowed": False,
            "credential_values_visible": False,
            "canonical_mutation_allowed": False,
        },
        "api_method": "execute_phase11_chat_workspace_proposal_consumption",
        "next_recommended_pass": WORKSPACE_PROPOSAL_CONSUMPTION_NEXT_PASS,
        "execution_status": WORKSPACE_PROPOSAL_CONSUMPTION_STATUS,
    }
    chat_workspace_target_state_executor = {
        "ok": True,
        "surface": WORKSPACE_TARGET_STATE_SURFACE_ID,
        "pass": WORKSPACE_TARGET_STATE_PASS_ID,
        "status": "AVAILABLE / TARGET-STATE API / NATIVE CHAT STATE ONLY",
        "summary": {
            "executor_available": True,
            "proposal_path_or_id_required": True,
            "expected_proposal_digest_required": True,
            "operator_target_state_statement_required": True,
            "native_chat_workspace_state_write_allowed": True,
            "native_chat_folder_state_write_allowed": True,
            "native_chat_thread_state_write_allowed": True,
            "ambient_chat_target_state_execution_allowed": False,
            "chat_message_send_allowed": False,
            "chat_transcript_write_allowed": False,
            "discord_api_calls_allowed": False,
            "discord_thread_create_allowed": False,
            "webhook_calls_allowed": False,
            "agent_bus_task_write_allowed": False,
            "runtime_board_write_allowed": False,
            "runtime_dispatch_allowed": False,
            "schedule_mutation_allowed": False,
            "provider_calls_allowed": False,
            "credential_values_visible": False,
            "canonical_mutation_allowed": False,
        },
        "api_method": "execute_phase11_chat_workspace_target_state",
        "next_recommended_pass": WORKSPACE_TARGET_STATE_NEXT_PASS,
        "execution_status": WORKSPACE_TARGET_STATE_STATUS,
    }
    chat_route_state_and_message_drafts = build_phase11_chat_route_state_and_message_drafts(vault)
    chat_route_state_summary = chat_route_state_and_message_drafts.get("summary") or {}
    chat_runtime_board_handoff_proposal = build_phase11_chat_runtime_board_handoff_proposal(
        vault,
        selected_thread_id=str(chat_route_state_summary.get("selected_thread_id") or "") or None,
        message=normalized_message or None,
        write_approval=False,
    )
    chat_runtime_board_handoff_summary = chat_runtime_board_handoff_proposal.get("summary") or {}
    chat_schedule_proposal_packet = build_phase11_chat_schedule_proposal_packet(
        vault,
        selected_thread_id=str(chat_route_state_summary.get("selected_thread_id") or "") or None,
        message=normalized_message or None,
        write_approval=False,
    )
    chat_schedule_proposal_summary = chat_schedule_proposal_packet.get("summary") or {}
    chat_schedule_proposal_consumption_executor = {
        "ok": True,
        "surface": CHAT_SCHEDULE_PROPOSAL_CONSUMPTION_SURFACE_ID,
        "pass": CHAT_SCHEDULE_PROPOSAL_CONSUMPTION_PASS_ID,
        "status": "AVAILABLE / APPROVAL-CONSUMPTION API / STAGED SCHEDULE PROPOSAL ONLY",
        "summary": {
            "executor_available": True,
            "approval_id_required": True,
            "expected_schedule_digest_required": True,
            "operator_approval_statement_required_for_pending": True,
            "approval_consumption_allowed_through_explicit_executor": True,
            "ambient_chat_consumption_allowed": False,
            "generic_studio_service_execution_allowed": False,
            "staged_schedule_proposal_write_allowed": True,
            "schedule_intent_yaml_write_allowed": False,
            "schedule_index_regeneration_allowed": False,
            "schedule_enable_allowed": False,
            "external_scheduler_mutation_allowed": False,
            "openclaw_cron_mutation_allowed": False,
            "hermes_cron_mutation_allowed": False,
            "agent_bus_task_write_allowed": False,
            "runtime_dispatch_allowed": False,
            "workflow_dispatch_allowed": False,
            "discord_api_calls_allowed": False,
            "provider_calls_allowed": False,
            "credential_values_visible": False,
            "canonical_mutation_allowed": False,
        },
        "api_method": "execute_phase11_chat_schedule_proposal_consumption",
        "next_recommended_pass": CHAT_SCHEDULE_PROPOSAL_CONSUMPTION_NEXT_PASS,
        "execution_status": CHAT_SCHEDULE_PROPOSAL_CONSUMPTION_STATUS,
    }
    chat_approved_schedule_intent_writer = {
        "ok": True,
        "surface": CHAT_APPROVED_SCHEDULE_INTENT_WRITER_SURFACE_ID,
        "pass": CHAT_APPROVED_SCHEDULE_INTENT_WRITER_PASS_ID,
        "status": "AVAILABLE / APPROVED-SCHEDULE-INTENT WRITER / SCHEDULE YAML + INDEX ONLY",
        "summary": {
            "executor_available": True,
            "staged_proposal_path_or_schedule_id_required": True,
            "expected_schedule_digest_required": True,
            "operator_schedule_write_statement_required": True,
            "approval_consumption_required_first": True,
            "ambient_chat_schedule_write_allowed": False,
            "generic_studio_service_execution_allowed": False,
            "schedule_intent_yaml_write_allowed": True,
            "schedule_index_regeneration_allowed": True,
            "schedule_enable_allowed": False,
            "external_scheduler_mutation_allowed": False,
            "openclaw_cron_mutation_allowed": False,
            "hermes_cron_mutation_allowed": False,
            "agent_bus_task_write_allowed": False,
            "runtime_dispatch_allowed": False,
            "workflow_dispatch_allowed": False,
            "discord_api_calls_allowed": False,
            "provider_calls_allowed": False,
            "credential_values_visible": False,
        },
        "api_method": "execute_phase11_chat_approved_schedule_intent_writer",
        "next_recommended_pass": CHAT_APPROVED_SCHEDULE_INTENT_WRITER_NEXT_PASS,
        "execution_status": CHAT_APPROVED_SCHEDULE_INTENT_WRITER_STATUS,
    }
    chat_schedule_intent_activation_readiness = {
        "ok": True,
        "surface": CHAT_SCHEDULE_INTENT_ACTIVATION_SURFACE_ID,
        "pass": CHAT_SCHEDULE_INTENT_ACTIVATION_PASS_ID,
        "status": "AVAILABLE / ACTIVATION-READINESS API / ENABLEMENT BLOCKED",
        "summary": {
            "readiness_surface_available": True,
            "schedule_id_required": True,
            "activation_digest_required_for_queue_write": True,
            "approval_queue_write_allowed_with_digest": True,
            "ambient_chat_schedule_enable_allowed": False,
            "generic_studio_service_execution_allowed": False,
            "schedule_enable_allowed_now": False,
            "schedule_index_regeneration_allowed_now": False,
            "external_scheduler_mutation_allowed": False,
            "openclaw_cron_mutation_allowed": False,
            "hermes_cron_mutation_allowed": False,
            "agent_bus_task_write_allowed": False,
            "runtime_dispatch_allowed": False,
            "workflow_dispatch_allowed": False,
            "discord_api_calls_allowed": False,
            "provider_calls_allowed": False,
            "credential_values_visible": False,
        },
        "read_api_method": "get_phase11_chat_schedule_intent_activation_readiness",
        "write_api_method": "request_phase11_chat_schedule_intent_activation",
        "next_recommended_pass": CHAT_SCHEDULE_INTENT_ACTIVATION_NEXT_PASS,
        "execution_status": CHAT_SCHEDULE_INTENT_ACTIVATION_STATUS,
    }
    chat_approved_schedule_activation_executor = {
        "ok": True,
        "surface": CHAT_APPROVED_SCHEDULE_ACTIVATION_SURFACE_ID,
        "pass": CHAT_APPROVED_SCHEDULE_ACTIVATION_PASS_ID,
        "status": "AVAILABLE / APPROVED-SCHEDULE ACTIVATION EXECUTOR / ENABLE + INDEX ONLY",
        "summary": {
            "executor_available": True,
            "approval_id_required": True,
            "expected_activation_digest_required": True,
            "operator_activation_statement_required": True,
            "activation_approval_required_first": True,
            "ambient_chat_schedule_enable_allowed": False,
            "generic_studio_service_execution_allowed": False,
            "schedule_enable_allowed_through_explicit_executor": True,
            "schedule_index_regeneration_allowed_through_explicit_executor": True,
            "adapter_export_read_model_allowed": True,
            "external_scheduler_mutation_allowed": False,
            "openclaw_cron_mutation_allowed": False,
            "hermes_cron_mutation_allowed": False,
            "agent_bus_task_write_allowed": False,
            "runtime_dispatch_allowed": False,
            "workflow_dispatch_allowed": False,
            "discord_api_calls_allowed": False,
            "provider_calls_allowed": False,
            "credential_values_visible": False,
        },
        "api_method": "execute_phase11_chat_approved_schedule_activation",
        "next_recommended_pass": CHAT_APPROVED_SCHEDULE_ACTIVATION_NEXT_PASS,
        "execution_status": CHAT_APPROVED_SCHEDULE_ACTIVATION_STATUS,
    }
    chat_schedule_adapter_export_readiness = {
        "ok": True,
        "surface": CHAT_SCHEDULE_ADAPTER_EXPORT_SURFACE_ID,
        "pass": CHAT_SCHEDULE_ADAPTER_EXPORT_PASS_ID,
        "status": "AVAILABLE / ADAPTER-EXPORT READINESS / CRON MUTATION BLOCKED",
        "summary": {
            "readiness_surface_available": True,
            "runtime_adapter_target_required": True,
            "default_runtime_adapter_target": "openclaw",
            "schedule_id_filter_supported": True,
            "expected_export_digest_required_for_queue_write": True,
            "approval_queue_write_allowed_with_digest": True,
            "local_export_packet_write_allowed_now": False,
            "ambient_studio_execution_allowed": False,
            "external_scheduler_mutation_allowed": False,
            "openclaw_cron_mutation_allowed": False,
            "hermes_cron_mutation_allowed": False,
            "agent_bus_task_write_allowed": False,
            "runtime_dispatch_allowed": False,
            "workflow_dispatch_allowed": False,
            "discord_api_calls_allowed": False,
            "provider_calls_allowed": False,
            "credential_values_visible": False,
        },
        "read_api_method": "get_phase11_chat_schedule_adapter_export_readiness",
        "write_api_method": "request_phase11_chat_schedule_adapter_export",
        "next_recommended_pass": CHAT_SCHEDULE_ADAPTER_EXPORT_NEXT_PASS,
        "execution_status": CHAT_SCHEDULE_ADAPTER_EXPORT_STATUS,
    }
    chat_approved_schedule_adapter_export_packet_writer = {
        "ok": True,
        "surface": CHAT_APPROVED_SCHEDULE_ADAPTER_EXPORT_WRITER_SURFACE_ID,
        "pass": CHAT_APPROVED_SCHEDULE_ADAPTER_EXPORT_WRITER_PASS_ID,
        "status": "AVAILABLE / APPROVED ADAPTER-EXPORT PACKET WRITER / LOCAL JSON ONLY",
        "summary": {
            "writer_available": True,
            "approval_id_required": True,
            "expected_export_digest_required": True,
            "operator_export_write_statement_required": True,
            "adapter_export_approval_required_first": True,
            "ambient_studio_execution_allowed": False,
            "local_export_packet_write_allowed_through_explicit_writer": True,
            "external_scheduler_mutation_allowed": False,
            "openclaw_cron_mutation_allowed": False,
            "hermes_cron_mutation_allowed": False,
            "agent_bus_task_write_allowed": False,
            "runtime_dispatch_allowed": False,
            "workflow_dispatch_allowed": False,
            "discord_api_calls_allowed": False,
            "provider_calls_allowed": False,
            "credential_values_visible": False,
        },
        "api_method": "execute_phase11_chat_approved_schedule_adapter_export_packet_writer",
        "next_recommended_pass": CHAT_APPROVED_SCHEDULE_ADAPTER_EXPORT_WRITER_NEXT_PASS,
        "execution_status": CHAT_APPROVED_SCHEDULE_ADAPTER_EXPORT_WRITER_STATUS,
    }
    chat_schedule_ui_action_controls_and_readback = (
        build_phase11_chat_schedule_ui_action_controls_and_readback(
            vault,
            default_runtime_adapter_target="openclaw",
        )
    )
    chat_schedule_ui_summary = chat_schedule_ui_action_controls_and_readback.get("summary") or {}
    chat_authority_tier_controls = build_phase11_chat_authority_tier_controls(
        vault,
        message=normalized_message,
        explicit_intent=explicit_intent,
    )
    chat_authority_tier_summary = chat_authority_tier_controls.get("summary") or {}
    chat_authority_execution_controls = build_phase11_chat_authority_execution_controls(
        vault,
        message=normalized_message,
        explicit_intent=explicit_intent,
        execute=False,
    )
    chat_authority_execution_summary = chat_authority_execution_controls.get("summary") or {}
    runtime_status_explanation = build_phase11_chat_runtime_status_explanation(
        vault,
        message=normalized_message or "/runtime status",
        explicit_intent=runtime_dispatch_intent,
    )
    browser_dispatch_readiness = build_phase11_chat_browser_dispatch_readiness(
        vault,
        message=normalized_message,
        explicit_intent=explicit_intent or (str(intent or "") if str(intent or "") == "browser-task" else "browser-task"),
    )
    approval_consumption_readiness = build_phase11_chat_approval_consumption_readiness(
        vault,
        message=normalized_message,
        explicit_intent=explicit_intent or (
            str(intent or "") if str(intent or "") == "approval-action" else "approval-action"
        ),
    )
    companion_status = build_phase11_chat_companion_status(
        vault,
        requested_runtime=_requested_companion_runtime(normalized_message),
    )
    companion_roster_ui_preview = build_phase11_companion_roster_ui_preview(
        vault,
        requested_runtime=_requested_companion_runtime(normalized_message)
        or (companion_status.get("summary") or {}).get("selected_runtime_id"),
    )
    companion_memory_boundary_contract = build_phase11_companion_memory_boundary_contract(vault)
    companion_memory_approval_preview = build_phase11_companion_memory_approval_preview(
        vault,
        companion_id=_requested_companion_runtime(normalized_message) or "hermes",
        memory_class=_requested_memory_class(normalized_message),
        content=normalized_message or "Operator requested a companion-memory approval preview.",
        source_surface="phase11-chat-panel",
    )
    companion_memory_approved_execution_proof = {
        "ok": True,
        "surface": COMPANION_MEMORY_EXECUTION_SURFACE_ID,
        "pass": COMPANION_MEMORY_EXECUTION_PASS_ID,
        "status": "AVAILABLE / APPROVAL-CONSUMPTION API / PROOF-ONLY",
        "summary": {
            "execution_proof_available": True,
            "approval_id_required": True,
            "expected_memory_approval_digest_required": True,
            "execute_flag_required": True,
            "proof_only": True,
            "approval_consumption_allowed_through_explicit_executor": True,
            "ambient_chat_consumption_allowed": False,
            "generic_studio_service_execution_allowed": False,
            "memory_ledger_write_allowed": False,
            "memory_root_create_allowed": False,
            "provider_call_performed": False,
            "runtime_dispatch_performed": False,
            "agent_bus_task_written": False,
            "canonical_mutation_performed": False,
            "next_recommended_pass": COMPANION_MEMORY_EXECUTION_NEXT_PASS,
        },
        "api_method": "execute_phase11_companion_memory_approved_execution_proof",
        "authority": {
            "approval_consumption_allowed": True,
            "approval_status_mutation_allowed": True,
            "exact_once_marker_write_allowed": True,
            "proof_output_write_allowed": True,
            "memory_ledger_write_allowed": False,
            "memory_root_create_allowed": False,
            "provider_calls_allowed": False,
            "runtime_dispatch_allowed": False,
            "agent_bus_task_write_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "blocked_reasons": [],
        "notes": [
            COMPANION_MEMORY_EXECUTION_STATUS,
            "Chat panel renders readiness only; execution requires explicit API/CLI call with approval id, digest, and --execute.",
        ],
    }
    companion_memory_readback_search_preview = build_phase11_companion_memory_readback_search_preview(
        vault,
        companion_id=_requested_companion_runtime(normalized_message) or None,
        query=_requested_memory_query(normalized_message) or None,
        status_filter="proof_written" if "proof" in normalized_message.lower() else None,
        limit=8,
    )
    companion_memory_ledger_write_approval_preview = build_phase11_companion_memory_ledger_write_approval_preview(
        vault,
    )
    companion_memory_ledger_read_model_preview = build_phase11_companion_memory_ledger_read_model_preview(
        vault,
        companion_id=_requested_companion_runtime(normalized_message) or None,
        query=_requested_memory_query(normalized_message) or None,
        limit=8,
        include_proof_backfill=True,
    )
    companion_memory_real_ledger_activation_closeout = (
        build_phase11_companion_memory_real_ledger_activation_closeout(
            vault,
            approval_id=_requested_approval_id(normalized_message) or None,
            companion_id=_requested_companion_runtime(normalized_message) or None,
            query=_requested_memory_query(normalized_message) or None,
            limit=8,
        )
    )
    companion_memory_context_readiness_preview = build_phase11_companion_memory_context_readiness_preview(
        vault,
        companion_id=_requested_companion_runtime(normalized_message) or None,
        memory_class=(
            _requested_memory_class(normalized_message)
            if any(
                marker in normalized_message.lower()
                for marker in (
                    "preference",
                    "interaction pattern",
                    "tone feedback",
                    "operator note",
                    "session observation",
                )
            )
            else None
        ),
        query=_requested_memory_query(normalized_message) or None,
        limit=8,
        max_context_chars=2400,
        include_proof_backfill=True,
    )
    companion_memory_approved_ledger_write_execution_proof = {
        "ok": True,
        "surface": COMPANION_MEMORY_LEDGER_EXECUTION_SURFACE_ID,
        "pass": COMPANION_MEMORY_LEDGER_EXECUTION_PASS_ID,
        "status": "AVAILABLE / APPROVAL-CONSUMPTION API / REAL LEDGER WRITE",
        "summary": {
            "approved_ledger_write_executor_available": True,
            "approval_id_required": True,
            "expected_ledger_write_approval_digest_required": True,
            "execute_flag_required": True,
            "approval_consumption_allowed_through_explicit_executor": True,
            "memory_ledger_write_allowed_through_explicit_executor": True,
            "ambient_chat_ledger_write_allowed": False,
            "generic_studio_service_execution_allowed": False,
            "provider_call_performed": False,
            "runtime_dispatch_performed": False,
            "browser_control_performed": False,
            "agent_bus_task_written": False,
            "canonical_mutation_performed": False,
            "next_recommended_pass": COMPANION_MEMORY_LEDGER_EXECUTION_NEXT_PASS,
        },
        "api_method": "execute_phase11_companion_memory_approved_ledger_write_execution_proof",
        "authority": {
            "approval_consumption_allowed": True,
            "approval_status_mutation_allowed": True,
            "exact_once_marker_write_allowed": True,
            "memory_root_create_allowed": True,
            "memory_ledger_write_allowed": True,
            "single_jsonl_append_allowed": True,
            "ambient_chat_ledger_write_allowed": False,
            "provider_calls_allowed": False,
            "runtime_dispatch_allowed": False,
            "browser_control_allowed": False,
            "agent_bus_task_write_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "blocked_reasons": [],
        "notes": [
            COMPANION_MEMORY_LEDGER_EXECUTION_STATUS,
            "Chat panel renders readiness only; execution requires explicit API/CLI call with approval id, digest, and --execute.",
        ],
    }
    companion_selection_preview = build_phase11_chat_companion_selection_preview(
        vault,
        requested_runtime=_requested_companion_runtime(normalized_message) or "hermes",
        current_runtime=(companion_status.get("summary") or {}).get("selected_runtime_id") or "openclaw",
        message=normalized_message,
    )
    companion_selection_queue_write_readiness = build_phase11_chat_companion_selection_queue_write_readiness(
        vault,
        requested_runtime=_requested_companion_runtime(normalized_message) or "hermes",
        current_runtime=(companion_status.get("summary") or {}).get("selected_runtime_id") or "openclaw",
        message=normalized_message,
    )
    companion_selection_approval_consumption_readiness = (
        build_phase11_chat_companion_selection_approval_consumption_readiness(
            vault,
            message=normalized_message,
        )
    )
    from runtime.studio.phase11_post_closeout_planning import build_phase11_post_closeout_planning

    post_closeout_plan = build_phase11_post_closeout_planning(
        vault,
        message=normalized_message,
        explicit_intent=explicit_intent,
    )
    panel_blockers = list(route.get("blocked_reasons") or [])
    if command_preview["visible"] and not command_preview["slash_command_known"]:
        panel_blockers.append("unknown_slash_command_preview_only")

    workspace_mode_panel = build_workspace_mode_studio_panel(vault)
    workspace_mode_summary = workspace_mode_panel.get("summary") or {}
    workspace_mode_readiness = workspace_mode_panel.get("readiness") or {}
    workspace_mode_deeplink_selector = _workspace_mode_deeplink_selector(workspace_mode_panel)
    workspace_mode_context = {
        "visible": True,
        "surface": "studio_workspace_mode_panel",
        "read_only": True,
        "panel_mounted": bool(workspace_mode_panel.get("ok")),
        "mode_selector_visible": bool(workspace_mode_deeplink_selector.get("visible")),
        "mode_deeplink_count": int(workspace_mode_deeplink_selector.get("card_count") or 0),
        "selected_mode": workspace_mode_deeplink_selector.get("selected_mode"),
        "selected_mode_label": workspace_mode_deeplink_selector.get("selected_mode_label"),
        "selected_mode_query_param": workspace_mode_deeplink_selector.get("query_param"),
        "overall_status": workspace_mode_summary.get("overall_status"),
        "manual_testing_ready": bool(workspace_mode_summary.get("manual_testing_ready")),
        "route_ready_count": int(workspace_mode_summary.get("route_ready_count") or 0),
        "route_blocked_count": int(workspace_mode_summary.get("route_blocked_count") or 0),
        "profile_valid_count": int(workspace_mode_summary.get("profile_valid_count") or 0),
        "profile_total_count": int(workspace_mode_summary.get("profile_total_count") or 0),
        "approval_artifact_count": int(workspace_mode_summary.get("approval_artifact_count") or 0),
        "project_dashboard_connected": bool(
            (workspace_mode_panel.get("project_workspace_connection") or {}).get("mounted")
        ),
        "chat_can_execute_workspace_mode": False,
        "chat_can_write_workspace_profiles": False,
        "chat_can_dispatch_workspace_workflows": False,
        "chat_can_open_studio_workspace_mode": True,
        "chat_can_mutate_canonical_state": False,
        "blockers": list(workspace_mode_readiness.get("blockers") or []),
    }

    authority = {
        "read_only": True,
        "approval_gated": False,
        "model_calls_allowed": False,
        "provider_calls_allowed": False,
        "runtime_dispatch_allowed": False,
        "browser_control_allowed": False,
        "approval_execution_allowed": False,
        "approval_queue_write_allowed": False,
        "approval_queue_write_requires_expected_digest": False,
        "approval_artifact_writes_allowed": False,
        "vault_writes_allowed": False,
        "conversation_persistence_allowed": False,
        "agent_bus_task_write_allowed": False,
        "schedule_mutation_allowed": False,
        "provider_switch_allowed": False,
        "companion_selection_write_allowed": False,
        "chat_workspace_write_allowed": False,
        "chat_folder_write_allowed": False,
        "chat_thread_create_allowed": False,
        "local_chat_route_state_write_allowed": True,
        "local_chat_message_draft_write_allowed": True,
        "message_intent_state_write_allowed": True,
        "chat_message_send_allowed": False,
        "runtime_board_write_allowed": False,
        "workspace_mode_profile_write_allowed": False,
        "workspace_mode_workflow_execution_allowed": False,
        "credential_values_visible": False,
        "canonical_mutation_allowed": False,
    }

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "title": "ChaseOS Chat",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "approval_gated": False,
        "api_methods": [
            "get_phase11_chat_panel_contract",
            "get_phase11_chat_authority_tier_controls",
            "get_phase11_chat_authority_execution_controls",
            "execute_phase11_chat_authority_execution_controls",
            "get_phase11_chat_schedule_ui_action_controls_and_readback",
            "get_phase11_chat_live_provider_execution_approval_preview",
            "get_phase11_chat_runtime_dispatch_readiness",
        ],
        "summary": {
            "message_present": bool(normalized_message),
            "message_chars": len(normalized_message),
            "intent_class": intent,
            "route_family": route.get("route_family"),
            "next_surface": route.get("next_surface"),
            "route_execution_allowed": False,
            "safety_policy_status": safety_policy.get("policy_status"),
            "policy_allowed_action_class_count": (safety_policy.get("policy_fail_closed_summary") or {}).get(
                "allowed_action_class_count"
            ),
            "proposal_required": bool(route.get("proposal_required")),
            "approval_required": bool(route.get("approval_required")),
            "model_route_required": bool(route.get("model_route_required")),
            "provider_route_status": route.get("provider_route_status"),
            "provider_readiness_status": provider_summary.get("readiness_status"),
            "workspace_mode_status": workspace_mode_summary.get("overall_status"),
            "workspace_mode_route_ready_count": workspace_mode_summary.get("route_ready_count"),
            "chat_workspace_count": chat_workspaces_summary.get("workspace_count"),
            "chat_thread_count": chat_workspaces_summary.get("thread_count"),
            "chat_runtime_lane_count": chat_workspaces_summary.get("runtime_lane_count"),
            "native_chat_project_model_ready": chat_workspaces_summary.get("native_chat_project_model_ready"),
            "chat_route_state_persisted": chat_route_state_summary.get("current_route_state_persisted"),
            "chat_draft_count": chat_route_state_summary.get("draft_count"),
            "chat_workspace_proposal_kind": chat_workspace_proposal_summary.get("proposal_kind"),
            "chat_workspace_proposal_digest_ready": bool(
                (chat_workspace_proposal_writer.get("digest_proof") or {}).get("proposal_digest")
            ),
            "chat_runtime_board_handoff_digest_ready": bool(
                (chat_runtime_board_handoff_proposal.get("digest_proof") or {}).get("handoff_digest")
            ),
            "chat_runtime_board_handoff_runtime_id": chat_runtime_board_handoff_summary.get("runtime_id"),
            "chat_runtime_board_handoff_board_target": chat_runtime_board_handoff_summary.get("board_target_id"),
            "chat_schedule_proposal_digest_ready": bool(
                (chat_schedule_proposal_packet.get("digest_proof") or {}).get("schedule_digest")
            ),
            "chat_schedule_proposal_schedule_id": chat_schedule_proposal_summary.get("schedule_id"),
            "chat_schedule_proposal_workflow_id": chat_schedule_proposal_summary.get("workflow_id"),
            "chat_schedule_proposal_cron_expression": chat_schedule_proposal_summary.get("cron_expression"),
            "chat_schedule_proposal_consumption_executor_ready": (
                chat_schedule_proposal_consumption_executor.get("surface")
                == CHAT_SCHEDULE_PROPOSAL_CONSUMPTION_SURFACE_ID
            ),
            "chat_approved_schedule_intent_writer_ready": (
                chat_approved_schedule_intent_writer.get("surface")
                == CHAT_APPROVED_SCHEDULE_INTENT_WRITER_SURFACE_ID
            ),
            "chat_schedule_intent_activation_readiness_ready": (
                chat_schedule_intent_activation_readiness.get("surface")
                == CHAT_SCHEDULE_INTENT_ACTIVATION_SURFACE_ID
            ),
            "chat_approved_schedule_activation_executor_ready": (
                chat_approved_schedule_activation_executor.get("surface")
                == CHAT_APPROVED_SCHEDULE_ACTIVATION_SURFACE_ID
            ),
            "chat_schedule_adapter_export_readiness_ready": (
                chat_schedule_adapter_export_readiness.get("surface")
                == CHAT_SCHEDULE_ADAPTER_EXPORT_SURFACE_ID
            ),
            "chat_approved_schedule_adapter_export_packet_writer_ready": (
                chat_approved_schedule_adapter_export_packet_writer.get("surface")
                == CHAT_APPROVED_SCHEDULE_ADAPTER_EXPORT_WRITER_SURFACE_ID
            ),
            "chat_schedule_ui_action_controls_ready": chat_schedule_ui_summary.get("ui_controls_ready"),
            "chat_schedule_manual_ui_test_ready": chat_schedule_ui_summary.get("manual_ui_test_ready"),
            "chat_authority_tier_controls_ready": chat_authority_tier_summary.get("visible_in_chat"),
            "chat_authority_tier_lane_count": chat_authority_tier_summary.get("lane_count"),
            "chat_authority_execution_controls_ready": chat_authority_execution_summary.get("manual_test_ready"),
            "chat_authority_execution_lane_count": chat_authority_execution_summary.get("lane_count"),
            "degraded_reason": provider_summary.get("degraded_reason"),
            "last_probe_marker": last_marker.get("marker_ref") or last_marker.get("gate_approval_id"),
            "queued_retry_count": int(queue.get("queued_retry_count") or 0),
            "blocked_reason_count": len(list(dict.fromkeys(panel_blockers))),
            "readonly_slash_response_cards_ready": (
                readonly_slash_command_responses.get("summary") or {}
            ).get("response_cards_ready"),
        },
        "message_preview": {
            "text": normalized_message[:600],
            "truncated": len(normalized_message) > 600,
            "input_treated_as_untrusted": True,
        },
        "router_contract": router,
        "safety_policy": safety_policy,
        "provider_readiness": provider_readiness,
        "conversation_rendering": _conversation_rendering(normalized_message, str(intent or "")),
        "system_context_display": _system_context_display(vault),
        "chat_workspaces_foundation": chat_workspaces_foundation,
        "chat_workspace_proposal_writer": chat_workspace_proposal_writer,
        "chat_workspace_proposal_consumption_executor": chat_workspace_proposal_consumption_executor,
        "chat_workspace_target_state_executor": chat_workspace_target_state_executor,
        "chat_route_state_and_message_drafts": chat_route_state_and_message_drafts,
        "chat_runtime_board_handoff_proposal": chat_runtime_board_handoff_proposal,
        "chat_schedule_proposal_packet": chat_schedule_proposal_packet,
        "chat_schedule_proposal_consumption_executor": chat_schedule_proposal_consumption_executor,
        "chat_approved_schedule_intent_writer": chat_approved_schedule_intent_writer,
        "chat_schedule_intent_activation_readiness": chat_schedule_intent_activation_readiness,
        "chat_approved_schedule_activation_executor": chat_approved_schedule_activation_executor,
        "chat_schedule_adapter_export_readiness": chat_schedule_adapter_export_readiness,
        "chat_approved_schedule_adapter_export_packet_writer": chat_approved_schedule_adapter_export_packet_writer,
        "chat_schedule_ui_action_controls_and_readback": chat_schedule_ui_action_controls_and_readback,
        "chat_authority_tier_controls": chat_authority_tier_controls,
        "chat_authority_execution_controls": chat_authority_execution_controls,
        "workspace_mode_context": workspace_mode_context,
        "workspace_mode_deeplink_selector": workspace_mode_deeplink_selector,
        "workspace_mode_panel": workspace_mode_panel,
        "denied_action_rendering": _denied_action_rendering(input_posture, safety_policy),
        "command_preview": command_preview,
        "readonly_slash_command_responses": readonly_slash_command_responses,
        "proposal_card": _proposal_card(str(intent or ""), route),
        "approval_handoff_preflight": _approval_handoff_preflight(str(intent or ""), route, input_posture),
        "approval_handoff_queue_contract": approval_queue_contract,
        "conversation_persistence_contract": conversation_persistence_contract,
        "approval_queue_write_execution_proof": approval_queue_write_proof,
        "live_provider_execution_approval_preview": live_provider_approval_preview,
        "browser_dispatch_readiness_contract": browser_dispatch_readiness,
        "approval_consumption_readiness_contract": approval_consumption_readiness,
        "runtime_status_explanation": runtime_status_explanation,
        "post_closeout_planning": post_closeout_plan,
        "live_routing_gate": _live_routing_gate(route, provider_readiness),
        "closeout_evidence": {
            "original_objective_status": CLOSEOUT_STATUS,
            "phase11_chat_provider_readiness_foundation_closed": True,
            "preflight_only": True,
            "approval_queue_writes_added": True,
            "live_provider_approval_preview_built": True,
            "runtime_dispatch_readiness_contract_built": True,
            "browser_dispatch_readiness_contract_built": True,
            "approval_consumption_readiness_contract_built": True,
            "companion_status_contract_built": True,
            "companion_roster_ui_preview_built": True,
            "companion_memory_boundary_contract_built": True,
            "companion_memory_approval_preview_built": True,
            "companion_memory_approved_execution_proof_built": True,
            "companion_memory_readback_search_preview_built": True,
            "companion_memory_ledger_write_approval_preview_built": True,
            "companion_memory_approved_ledger_write_execution_proof_built": True,
            "companion_memory_ledger_read_model_preview_built": True,
            "companion_memory_real_ledger_activation_closeout_built": True,
            "companion_memory_context_readiness_preview_built": True,
            "companion_selection_approval_consumption_readiness_built": True,
            "runtime_status_explanation_built": True,
            "readonly_slash_command_responses_built": True,
            "studio_runtime_chat_workspaces_foundation_built": True,
            "studio_runtime_chat_workspace_proposal_writer_built": True,
            "studio_runtime_chat_workspace_proposal_consumption_executor_built": True,
            "studio_runtime_chat_workspace_target_state_executor_built": True,
            "studio_runtime_chat_route_state_and_message_drafts_built": True,
            "studio_runtime_chat_runtime_board_handoff_proposal_built": True,
            "studio_runtime_chat_schedule_proposal_packet_built": True,
            "studio_runtime_chat_schedule_proposal_consumption_executor_built": True,
            "studio_runtime_chat_approved_schedule_intent_writer_built": True,
            "studio_runtime_chat_schedule_intent_activation_readiness_built": True,
            "studio_runtime_chat_approved_schedule_activation_executor_built": True,
            "studio_runtime_chat_schedule_adapter_export_readiness_built": True,
            "studio_runtime_chat_approved_schedule_adapter_export_packet_writer_built": True,
            "studio_runtime_chat_schedule_ui_action_controls_and_readback_built": True,
            "studio_runtime_chat_authority_tier_controls_built": True,
            "studio_runtime_chat_authority_execution_controls_built": True,
            "workspace_mode_chat_deeplink_selector_built": True,
            "conversation_persistence_contract_built": True,
            "conversation_persistence_writes_added": False,
            "live_execution_added": True,
            "chat_panel_consumes_router_contract": True,
            "chat_panel_consumes_provider_readiness_contract": True,
            "provider_readiness_consumed_not_mutated": True,
            "denial_states_visible": True,
            "post_closeout_future_work": POST_CLOSEOUT_FUTURE_WORK,
        },
        "conversation_posture": {
            "conversation_log_visible": True,
            "conversation_persistence_allowed": False,
            "conversation_write_path": (
                conversation_persistence_contract.get("conversation_descriptor") or {}
            ).get("target_path_preview"),
            "retention_policy": (
                conversation_persistence_contract.get("conversation_descriptor") or {}
            ).get("retention_class", "operator-history"),
            "approval_required_before_write": True,
            "approval_request_created": False,
            "conversation_log_writer_called": False,
        },
        "approval_queue_write_posture": {
            "queue_write_proof_visible": True,
            "queue_write_contract_available": True,
            "queue_write_allowed_after_explicit_digest": False,
            "queue_write_requires_lower_phase_contract": True,
            "approval_request_created_in_preview": False,
            "approval_execution_allowed": False,
            "target_write_allowed": False,
            "action_digest": (approval_queue_write_proof.get("digest_proof") or {}).get("action_digest"),
        },
        "live_provider_execution_posture": {
            "approval_preview_visible": True,
            "approval_preview_ready": (live_provider_approval_preview.get("summary") or {}).get(
                "approval_preview_ready"
            ),
            "execution_preconditions_met": (live_provider_approval_preview.get("summary") or {}).get(
                "execution_preconditions_met"
            ),
            "request_digest": (live_provider_approval_preview.get("request_digest_proof") or {}).get(
                "request_digest"
            ),
            "approval_request_created": False,
            "provider_call_performed": False,
            "provider_call_allowed": False,
        },
        "runtime_dispatch_posture": {
            "dispatch_readiness_visible": True,
            "dispatch_preview_ready": (runtime_dispatch_readiness.get("summary") or {}).get(
                "dispatch_preview_ready"
            ),
            "dispatch_preconditions_met": (runtime_dispatch_readiness.get("summary") or {}).get(
                "dispatch_preconditions_met"
            ),
            "selected_runtime_id": (runtime_dispatch_readiness.get("summary") or {}).get("selected_runtime_id"),
            "selected_task_type": (runtime_dispatch_readiness.get("summary") or {}).get("selected_task_type"),
            "request_digest": (runtime_dispatch_readiness.get("request_digest_proof") or {}).get(
                "request_digest"
            ),
            "approval_request_created": False,
            "agent_bus_task_created": False,
            "workflow_dispatched": False,
            "runtime_dispatch_executor_ready": True,
            "runtime_dispatch_allowed": False,
            "approved_agent_bus_enqueue_available": True,
        },
        "runtime_dispatch_readiness_contract": runtime_dispatch_readiness,
        "chat_workspace_posture": {
            "workspace_surface_visible": True,
            "native_chat_project_model_ready": chat_workspaces_summary.get("native_chat_project_model_ready"),
            "workspace_count": chat_workspaces_summary.get("workspace_count"),
            "folder_count": chat_workspaces_summary.get("folder_count"),
            "tab_count": chat_workspaces_summary.get("tab_count"),
            "thread_count": chat_workspaces_summary.get("thread_count"),
            "runtime_lane_count": chat_workspaces_summary.get("runtime_lane_count"),
            "discord_binding_status": chat_workspaces_summary.get("discord_binding_status"),
            "route_state_persistence_built": chat_workspaces_summary.get("route_state_persisted") is not None,
            "route_state_persisted": chat_workspaces_summary.get("route_state_persisted"),
            "message_draft_state_persistence_built": True,
            "draft_count": chat_workspaces_summary.get("draft_count"),
            "chat_workspace_write_allowed": False,
            "chat_thread_create_allowed": False,
            "chat_message_send_allowed": False,
            "runtime_board_write_allowed": False,
            "schedule_mutation_allowed": False,
            "agent_bus_task_write_allowed": False,
        },
        "chat_workspace_proposal_writer_posture": {
            "proposal_writer_visible": True,
            "proposal_kind": chat_workspace_proposal_summary.get("proposal_kind"),
            "proposal_id": chat_workspace_proposal_summary.get("proposal_id"),
            "proposal_digest": (chat_workspace_proposal_writer.get("digest_proof") or {}).get("proposal_digest"),
            "queue_write_preview_ready": chat_workspace_proposal_summary.get("queue_write_preview_ready"),
            "approval_queue_write_allowed_with_digest": (
                chat_workspace_proposal_writer.get("authority") or {}
            ).get("approval_queue_write_allowed_with_digest"),
            "approval_request_created_in_panel_preview": False,
            "target_file_written": False,
            "chat_thread_created": False,
            "discord_api_called": False,
            "agent_bus_task_written": False,
            "runtime_board_written": False,
            "schedule_mutated": False,
        },
        "chat_workspace_proposal_consumption_posture": {
            "proposal_consumption_executor_visible": True,
            "executor_surface": WORKSPACE_PROPOSAL_CONSUMPTION_SURFACE_ID,
            "api_method": "execute_phase11_chat_workspace_proposal_consumption",
            "approval_id_required": True,
            "expected_proposal_digest_required": True,
            "target_workspace_proposal_write_allowed_after_approval": True,
            "generic_studio_service_execution_allowed": False,
            "ambient_chat_consumption_allowed": False,
            "target_workspace_proposal_written_in_panel_preview": False,
            "chat_workspace_created": False,
            "chat_folder_created": False,
            "chat_thread_created": False,
            "chat_message_sent": False,
            "discord_api_called": False,
            "discord_thread_created": False,
            "agent_bus_task_written": False,
            "runtime_board_written": False,
            "schedule_mutated": False,
            "provider_call_performed": False,
            "canonical_mutation_performed": False,
            "next_recommended_pass": WORKSPACE_PROPOSAL_CONSUMPTION_NEXT_PASS,
        },
        "chat_workspace_target_state_posture": {
            "target_state_executor_visible": True,
            "executor_surface": WORKSPACE_TARGET_STATE_SURFACE_ID,
            "api_method": "execute_phase11_chat_workspace_target_state",
            "proposal_path_or_id_required": True,
            "expected_proposal_digest_required": True,
            "operator_target_state_statement_required": True,
            "native_chat_workspace_state_write_allowed": True,
            "native_chat_folder_state_write_allowed": True,
            "native_chat_thread_state_write_allowed": True,
            "ambient_chat_target_state_execution_allowed": False,
            "target_state_written_in_panel_preview": False,
            "chat_message_sent": False,
            "chat_transcript_written": False,
            "discord_api_called": False,
            "discord_thread_created": False,
            "webhook_call_performed": False,
            "agent_bus_task_written": False,
            "runtime_board_written": False,
            "runtime_dispatched": False,
            "schedule_mutated": False,
            "provider_call_performed": False,
            "canonical_mutation_performed": False,
            "next_recommended_pass": WORKSPACE_TARGET_STATE_NEXT_PASS,
        },
        "chat_route_state_posture": {
            "route_state_surface_visible": True,
            "surface": CHAT_ROUTE_STATE_SURFACE_ID,
            "pass": CHAT_ROUTE_STATE_PASS_ID,
            "status": CHAT_ROUTE_STATE_STATUS,
            "api_methods": [
                "get_phase11_chat_route_state_and_message_drafts",
                "save_phase11_chat_route_state",
                "save_phase11_chat_message_draft",
            ],
            "local_chat_route_state_write_allowed": (
                chat_route_state_and_message_drafts.get("authority") or {}
            ).get("local_chat_route_state_write_allowed"),
            "local_chat_message_draft_write_allowed": (
                chat_route_state_and_message_drafts.get("authority") or {}
            ).get("local_chat_message_draft_write_allowed"),
            "message_intent_state_write_allowed": (
                chat_route_state_and_message_drafts.get("authority") or {}
            ).get("message_intent_state_write_allowed"),
            "route_state_persistence_built": chat_route_state_summary.get("route_state_persistence_built"),
            "message_draft_state_persistence_built": chat_route_state_summary.get(
                "message_draft_state_persistence_built"
            ),
            "message_intent_state_persistence_built": chat_route_state_summary.get(
                "message_intent_state_persistence_built"
            ),
            "route_state_persisted": chat_route_state_summary.get("current_route_state_persisted"),
            "draft_count": chat_route_state_summary.get("draft_count"),
            "selected_workspace_id": chat_route_state_summary.get("selected_workspace_id"),
            "selected_thread_id": chat_route_state_summary.get("selected_thread_id"),
            "selected_tab_id": chat_route_state_summary.get("selected_tab_id"),
            "route_preview": chat_route_state_summary.get("route_preview"),
            "route_state_written_in_panel_preview": False,
            "draft_written_in_panel_preview": False,
            "chat_message_sent": False,
            "chat_transcript_written": False,
            "conversation_log_written": False,
            "discord_api_called": False,
            "discord_thread_created": False,
            "agent_bus_task_written": False,
            "runtime_board_written": False,
            "runtime_dispatched": False,
            "schedule_mutated": False,
            "provider_call_performed": False,
            "credential_value_read": False,
            "canonical_mutation_performed": False,
            "next_recommended_pass": CHAT_ROUTE_STATE_NEXT_PASS,
        },
        "chat_runtime_board_handoff_posture": {
            "runtime_board_handoff_visible": True,
            "surface": CHAT_RUNTIME_BOARD_HANDOFF_SURFACE_ID,
            "pass": CHAT_RUNTIME_BOARD_HANDOFF_PASS_ID,
            "status": CHAT_RUNTIME_BOARD_HANDOFF_STATUS,
            "api_methods": [
                "get_phase11_chat_runtime_board_handoff_proposal",
                "request_phase11_chat_runtime_board_handoff_proposal",
            ],
            "handoff_id": chat_runtime_board_handoff_summary.get("handoff_id"),
            "runtime_id": chat_runtime_board_handoff_summary.get("runtime_id"),
            "thread_id": chat_runtime_board_handoff_summary.get("thread_id"),
            "board_target_id": chat_runtime_board_handoff_summary.get("board_target_id"),
            "board_lane": chat_runtime_board_handoff_summary.get("board_lane"),
            "handoff_digest": (
                chat_runtime_board_handoff_proposal.get("digest_proof") or {}
            ).get("handoff_digest"),
            "approval_queue_write_allowed_with_digest": (
                chat_runtime_board_handoff_proposal.get("authority") or {}
            ).get("approval_queue_write_allowed_with_digest"),
            "approval_request_created_in_panel_preview": False,
            "target_path_preview": chat_runtime_board_handoff_summary.get("target_path_preview"),
            "target_file_written": False,
            "runtime_board_written": False,
            "runtime_board_item_created": False,
            "agent_bus_task_written": False,
            "runtime_dispatched": False,
            "workflow_dispatched": False,
            "chat_message_sent": False,
            "conversation_log_written": False,
            "discord_api_called": False,
            "discord_thread_created": False,
            "schedule_mutated": False,
            "provider_call_performed": False,
            "credential_value_read": False,
            "canonical_mutation_performed": False,
            "next_recommended_pass": CHAT_RUNTIME_BOARD_HANDOFF_NEXT_PASS,
        },
        "chat_schedule_proposal_posture": {
            "schedule_proposal_visible": True,
            "surface": CHAT_SCHEDULE_PROPOSAL_SURFACE_ID,
            "pass": CHAT_SCHEDULE_PROPOSAL_PASS_ID,
            "status": CHAT_SCHEDULE_PROPOSAL_STATUS,
            "api_methods": [
                "get_phase11_chat_schedule_proposal_packet",
                "request_phase11_chat_schedule_proposal_packet",
            ],
            "schedule_proposal_id": chat_schedule_proposal_summary.get("schedule_proposal_id"),
            "schedule_id": chat_schedule_proposal_summary.get("schedule_id"),
            "schedule_kind": chat_schedule_proposal_summary.get("schedule_kind"),
            "workflow_id": chat_schedule_proposal_summary.get("workflow_id"),
            "command_id": chat_schedule_proposal_summary.get("command_id"),
            "cron_expression": chat_schedule_proposal_summary.get("cron_expression"),
            "timezone": chat_schedule_proposal_summary.get("timezone"),
            "runtime_adapter_target": chat_schedule_proposal_summary.get("runtime_adapter_target"),
            "schedule_digest": (
                chat_schedule_proposal_packet.get("digest_proof") or {}
            ).get("schedule_digest"),
            "approval_queue_write_allowed_with_digest": (
                chat_schedule_proposal_packet.get("authority") or {}
            ).get("approval_queue_write_allowed_with_digest"),
            "approval_request_created_in_panel_preview": False,
            "target_path_preview": chat_schedule_proposal_summary.get("target_path_preview"),
            "target_file_written": False,
            "schedule_intent_written": False,
            "schedule_index_regenerated": False,
            "schedule_enabled": False,
            "external_scheduler_changed": False,
            "agent_bus_task_written": False,
            "runtime_dispatched": False,
            "workflow_dispatched": False,
            "chat_message_sent": False,
            "discord_api_called": False,
            "provider_call_performed": False,
            "credential_value_read": False,
            "canonical_mutation_performed": False,
            "next_recommended_pass": CHAT_SCHEDULE_PROPOSAL_NEXT_PASS,
        },
        "chat_schedule_proposal_consumption_posture": {
            "schedule_proposal_consumption_executor_visible": True,
            "executor_surface": CHAT_SCHEDULE_PROPOSAL_CONSUMPTION_SURFACE_ID,
            "api_method": "execute_phase11_chat_schedule_proposal_consumption",
            "approval_id_required": True,
            "expected_schedule_digest_required": True,
            "operator_approval_statement_required_for_pending": True,
            "staged_schedule_proposal_write_allowed_after_approval": True,
            "generic_studio_service_execution_allowed": False,
            "ambient_chat_consumption_allowed": False,
            "staged_schedule_proposal_written_in_panel_preview": False,
            "target_schedule_yaml_written": False,
            "schedule_intent_written": False,
            "schedule_index_regenerated": False,
            "schedule_enabled": False,
            "external_scheduler_changed": False,
            "openclaw_cron_changed": False,
            "hermes_cron_changed": False,
            "agent_bus_task_written": False,
            "runtime_dispatched": False,
            "workflow_dispatched": False,
            "discord_api_called": False,
            "provider_call_performed": False,
            "credential_value_read": False,
            "canonical_mutation_performed": False,
            "next_recommended_pass": CHAT_SCHEDULE_PROPOSAL_CONSUMPTION_NEXT_PASS,
        },
        "chat_approved_schedule_intent_writer_posture": {
            "approved_schedule_intent_writer_visible": True,
            "executor_surface": CHAT_APPROVED_SCHEDULE_INTENT_WRITER_SURFACE_ID,
            "api_method": "execute_phase11_chat_approved_schedule_intent_writer",
            "staged_proposal_path_or_schedule_id_required": True,
            "expected_schedule_digest_required": True,
            "operator_schedule_write_statement_required": True,
            "approval_consumption_required_first": True,
            "generic_studio_service_execution_allowed": False,
            "ambient_chat_schedule_write_allowed": False,
            "schedule_intent_yaml_write_allowed_after_staged_approval": True,
            "schedule_index_regeneration_allowed_after_staged_approval": True,
            "target_schedule_yaml_written_in_panel_preview": False,
            "schedule_index_regenerated_in_panel_preview": False,
            "schedule_enabled": False,
            "external_scheduler_changed": False,
            "openclaw_cron_changed": False,
            "hermes_cron_changed": False,
            "agent_bus_task_written": False,
            "runtime_dispatched": False,
            "workflow_dispatched": False,
            "discord_api_called": False,
            "provider_call_performed": False,
            "credential_value_read": False,
            "next_recommended_pass": CHAT_APPROVED_SCHEDULE_INTENT_WRITER_NEXT_PASS,
        },
        "chat_schedule_intent_activation_readiness_posture": {
            "activation_readiness_visible": True,
            "surface": CHAT_SCHEDULE_INTENT_ACTIVATION_SURFACE_ID,
            "read_api_method": "get_phase11_chat_schedule_intent_activation_readiness",
            "write_api_method": "request_phase11_chat_schedule_intent_activation",
            "schedule_id_required": True,
            "activation_digest_required_for_queue_write": True,
            "approval_queue_write_allowed_with_digest": True,
            "activation_approval_artifact_execution_blocked": True,
            "generic_studio_service_execution_allowed": False,
            "schedule_enabled_in_panel_preview": False,
            "schedule_index_regenerated_in_panel_preview": False,
            "external_scheduler_changed": False,
            "openclaw_cron_changed": False,
            "hermes_cron_changed": False,
            "agent_bus_task_written": False,
            "runtime_dispatched": False,
            "workflow_dispatched": False,
            "discord_api_called": False,
            "provider_call_performed": False,
            "credential_value_read": False,
            "next_recommended_pass": CHAT_SCHEDULE_INTENT_ACTIVATION_NEXT_PASS,
        },
        "chat_approved_schedule_activation_executor_posture": {
            "approved_schedule_activation_executor_visible": True,
            "surface": CHAT_APPROVED_SCHEDULE_ACTIVATION_SURFACE_ID,
            "api_method": "execute_phase11_chat_approved_schedule_activation",
            "approval_id_required": True,
            "expected_activation_digest_required": True,
            "operator_activation_statement_required": True,
            "activation_approval_required_first": True,
            "generic_studio_service_execution_allowed": False,
            "ambient_chat_schedule_enable_allowed": False,
            "schedule_enable_allowed_after_activation_approval": True,
            "schedule_index_regeneration_allowed_after_activation_approval": True,
            "adapter_export_read_model_allowed": True,
            "schedule_enabled_in_panel_preview": False,
            "schedule_index_regenerated_in_panel_preview": False,
            "external_scheduler_changed": False,
            "openclaw_cron_changed": False,
            "hermes_cron_changed": False,
            "agent_bus_task_written": False,
            "runtime_dispatched": False,
            "workflow_dispatched": False,
            "discord_api_called": False,
            "provider_call_performed": False,
            "credential_value_read": False,
            "next_recommended_pass": CHAT_APPROVED_SCHEDULE_ACTIVATION_NEXT_PASS,
        },
        "chat_schedule_adapter_export_readiness_posture": {
            "adapter_export_readiness_visible": True,
            "surface": CHAT_SCHEDULE_ADAPTER_EXPORT_SURFACE_ID,
            "read_api_method": "get_phase11_chat_schedule_adapter_export_readiness",
            "write_api_method": "request_phase11_chat_schedule_adapter_export",
            "runtime_adapter_target_required": True,
            "schedule_id_filter_supported": True,
            "expected_export_digest_required_for_queue_write": True,
            "approval_queue_write_allowed_with_digest": True,
            "local_export_packet_write_allowed_now": False,
            "ambient_studio_execution_allowed": False,
            "external_scheduler_changed": False,
            "openclaw_cron_changed": False,
            "hermes_cron_changed": False,
            "agent_bus_task_written": False,
            "runtime_dispatched": False,
            "workflow_dispatched": False,
            "discord_api_called": False,
            "provider_call_performed": False,
            "credential_value_read": False,
            "next_recommended_pass": CHAT_SCHEDULE_ADAPTER_EXPORT_NEXT_PASS,
        },
        "chat_approved_schedule_adapter_export_packet_writer_posture": {
            "approved_schedule_adapter_export_packet_writer_visible": True,
            "surface": CHAT_APPROVED_SCHEDULE_ADAPTER_EXPORT_WRITER_SURFACE_ID,
            "api_method": "execute_phase11_chat_approved_schedule_adapter_export_packet_writer",
            "approval_id_required": True,
            "expected_export_digest_required": True,
            "operator_export_write_statement_required": True,
            "adapter_export_approval_required_first": True,
            "ambient_studio_execution_allowed": False,
            "local_export_packet_write_allowed_through_explicit_writer": True,
            "export_packet_written_in_panel_preview": False,
            "external_scheduler_changed": False,
            "openclaw_cron_changed": False,
            "hermes_cron_changed": False,
            "agent_bus_task_written": False,
            "runtime_dispatched": False,
            "workflow_dispatched": False,
            "discord_api_called": False,
            "provider_call_performed": False,
            "credential_value_read": False,
            "next_recommended_pass": CHAT_APPROVED_SCHEDULE_ADAPTER_EXPORT_WRITER_NEXT_PASS,
        },
        "chat_schedule_ui_action_controls_posture": {
            "schedule_ui_action_controls_visible": True,
            "surface": CHAT_SCHEDULE_UI_ACTION_CONTROLS_SURFACE_ID,
            "pass": CHAT_SCHEDULE_UI_ACTION_CONTROLS_PASS_ID,
            "status": CHAT_SCHEDULE_UI_ACTION_CONTROLS_STATUS,
            "api_method": "get_phase11_chat_schedule_ui_action_controls_and_readback",
            "render_function": "_phase11ChatScheduleUiActionControlsAndReadback",
            "event_handler": "_phase11ScheduleRunAction",
            "manual_ui_test_ready": chat_schedule_ui_summary.get("manual_ui_test_ready"),
            "control_step_count": chat_schedule_ui_summary.get("control_step_count"),
            "api_method_count": chat_schedule_ui_summary.get("api_method_count"),
            "default_runtime_adapter_target": chat_schedule_ui_summary.get("default_runtime_adapter_target"),
            "no_secret_fields_rendered": chat_schedule_ui_summary.get("no_secret_fields_rendered"),
            "external_scheduler_changed": False,
            "openclaw_cron_changed": False,
            "hermes_cron_changed": False,
            "agent_bus_task_written": False,
            "runtime_dispatched": False,
            "workflow_dispatched": False,
            "discord_api_called": False,
            "provider_call_performed": False,
            "credential_value_read": False,
            "next_recommended_pass": CHAT_SCHEDULE_UI_ACTION_CONTROLS_NEXT_PASS,
        },
        "chat_authority_tier_controls_posture": {
            "authority_tier_controls_visible": True,
            "surface": CHAT_AUTHORITY_TIER_CONTROLS_SURFACE_ID,
            "pass": CHAT_AUTHORITY_TIER_CONTROLS_PASS_ID,
            "status": CHAT_AUTHORITY_TIER_CONTROLS_STATUS,
            "api_method": "get_phase11_chat_authority_tier_controls",
            "render_function": "_phase11ChatAuthorityTierControls",
            "lane_count": chat_authority_tier_summary.get("lane_count"),
            "safe_preview_navigation_ready": chat_authority_tier_summary.get(
                "safe_preview_navigation_ready"
            ),
            "direct_execution_blocked": chat_authority_tier_summary.get("direct_execution_blocked"),
            "provider_lane_present": chat_authority_tier_summary.get("provider_lane_present"),
            "credential_lane_present": chat_authority_tier_summary.get("credential_lane_present"),
            "runtime_dispatch_lane_present": chat_authority_tier_summary.get("runtime_dispatch_lane_present"),
            "agent_bus_lane_present": chat_authority_tier_summary.get("agent_bus_lane_present"),
            "discord_lane_present": chat_authority_tier_summary.get("discord_lane_present"),
            "external_cron_apply_lane_present": chat_authority_tier_summary.get(
                "external_cron_apply_lane_present"
            ),
            "provider_call_performed": False,
            "credential_value_read": False,
            "discord_api_called": False,
            "agent_bus_task_written": False,
            "runtime_dispatched": False,
            "workflow_dispatched": False,
            "external_scheduler_changed": False,
            "openclaw_cron_changed": False,
            "hermes_cron_changed": False,
            "canonical_mutation_performed": False,
            "next_recommended_pass": CHAT_AUTHORITY_TIER_CONTROLS_NEXT_PASS,
        },
        "chat_authority_execution_controls_posture": {
            "authority_execution_controls_visible": True,
            "surface": CHAT_AUTHORITY_EXECUTION_CONTROLS_SURFACE_ID,
            "pass": CHAT_AUTHORITY_EXECUTION_CONTROLS_PASS_ID,
            "status": CHAT_AUTHORITY_EXECUTION_CONTROLS_STATUS,
            "api_methods": [
                "get_phase11_chat_authority_execution_controls",
                "execute_phase11_chat_authority_execution_controls",
            ],
            "render_function": "_phase11ChatAuthorityExecutionControls",
            "manual_test_ready": chat_authority_execution_summary.get("manual_test_ready"),
            "lane_count": chat_authority_execution_summary.get("lane_count"),
            "provider_digest_prepared": bool(
                (chat_authority_execution_controls.get("prepared_digests") or {}).get(
                    "expected_provider_digest"
                )
            ),
            "main_runtime_digest_prepared": bool(
                (chat_authority_execution_controls.get("prepared_digests") or {}).get(
                    "expected_main_runtime_digest"
                )
            ),
            "discord_control_digest_prepared": bool(
                (chat_authority_execution_controls.get("prepared_digests") or {}).get(
                    "expected_discord_control_digest"
                )
            ),
            "cron_control_digest_prepared": bool(
                (chat_authority_execution_controls.get("prepared_digests") or {}).get(
                    "expected_cron_control_digest"
                )
            ),
            "provider_calls_allowed_with_digest_and_statement": True,
            "credential_value_visible": False,
            "runtime_dispatch_allowed_with_digest_and_statement": True,
            "agent_bus_task_write_allowed_with_digest_and_statement": True,
            "discord_api_called_by_studio": False,
            "discord_control_handoff_to_runtime": True,
            "external_cron_mutation_by_studio": False,
            "cron_control_handoff_to_runtime": True,
            "runtime_task_claimed_by_studio": False,
            "canonical_mutation_performed": False,
            "next_recommended_pass": CHAT_AUTHORITY_EXECUTION_CONTROLS_NEXT_PASS,
        },
        "browser_dispatch_posture": {
            "dispatch_readiness_visible": True,
            "dispatch_preview_ready": (browser_dispatch_readiness.get("summary") or {}).get(
                "dispatch_preview_ready"
            ),
            "dispatch_preconditions_met": (browser_dispatch_readiness.get("summary") or {}).get(
                "dispatch_preconditions_met"
            ),
            "selected_target": (browser_dispatch_readiness.get("summary") or {}).get("selected_target"),
            "selected_browser_action": (browser_dispatch_readiness.get("summary") or {}).get("selected_browser_action"),
            "request_digest": (browser_dispatch_readiness.get("request_digest_proof") or {}).get(
                "request_digest"
            ),
            "approval_request_created": False,
            "browser_launch_started": False,
            "browser_navigation_started": False,
            "screenshot_captured": False,
            "browser_dispatch_allowed": False,
        },
        "browser_dispatch_readiness_contract": browser_dispatch_readiness,
        "approval_consumption_posture": {
            "consumption_readiness_visible": True,
            "consumption_preview_ready": (approval_consumption_readiness.get("summary") or {}).get(
                "consumption_preview_ready"
            ),
            "consumption_preconditions_met": (approval_consumption_readiness.get("summary") or {}).get(
                "consumption_preconditions_met"
            ),
            "selected_approval_id": (approval_consumption_readiness.get("summary") or {}).get(
                "selected_approval_id"
            ),
            "approval_status": (approval_consumption_readiness.get("summary") or {}).get("approval_status"),
            "consumption_digest": (approval_consumption_readiness.get("digest_proof") or {}).get(
                "consumption_digest"
            ),
            "approval_status_mutated": False,
            "approval_execution_called": False,
            "exact_once_marker_written": False,
            "target_write_performed": False,
            "approval_consumption_allowed": False,
        },
        "approval_consumption_readiness_contract": approval_consumption_readiness,
        "companion_status_posture": {
            "companion_status_visible": True,
            "selected_runtime_id": (companion_status.get("summary") or {}).get("selected_runtime_id"),
            "registered_companion_count": (companion_status.get("summary") or {}).get("registered_companion_count"),
            "authority_ceiling_visible": True,
            "runtime_control_allowed": False,
            "runtime_dispatch_allowed": False,
            "identity_ledger_mutation_allowed": False,
            "profile_write_allowed": False,
            "role_card_write_allowed": False,
        },
        "companion_status_contract": companion_status,
        "companion_roster_ui_posture": {
            "roster_ui_preview_visible": True,
            "roster_ui_preview_ready": (companion_roster_ui_preview.get("summary") or {}).get(
                "roster_ui_preview_ready"
            ),
            "active_runtime_id": (companion_roster_ui_preview.get("summary") or {}).get("active_runtime_id"),
            "roster_card_count": (companion_roster_ui_preview.get("summary") or {}).get("roster_card_count"),
            "active_companion_first": (companion_roster_ui_preview.get("summary") or {}).get(
                "active_companion_first"
            ),
            "abstract_visuals_only_until_brand_pack": (
                companion_roster_ui_preview.get("summary") or {}
            ).get("abstract_visuals_only_until_brand_pack"),
            "companion_selection_write_allowed": False,
            "runtime_dispatch_allowed": False,
            "provider_model_selection_granted": False,
            "memory_access_granted": False,
            "agent_bus_task_write_allowed": False,
        },
        "companion_roster_ui_preview": companion_roster_ui_preview,
        "companion_memory_boundary_posture": {
            "memory_boundary_visible": True,
            "separate_memory_namespace_declared": (
                companion_memory_boundary_contract.get("summary") or {}
            ).get("separate_memory_namespace_declared"),
            "memory_namespace_count": (
                companion_memory_boundary_contract.get("summary") or {}
            ).get("memory_namespace_count"),
            "memory_writes_allowed_now": False,
            "approval_required_for_memory_write": True,
            "memory_write_executor_built": False,
            "memory_files_written_by_this_surface": False,
            "memory_write_authority_granted": False,
            "canonical_mutation_allowed": False,
        },
        "companion_memory_boundary_contract": companion_memory_boundary_contract,
        "companion_memory_approval_posture": {
            "approval_preview_visible": True,
            "approval_preview_ready": (companion_memory_approval_preview.get("summary") or {}).get(
                "approval_preview_ready"
            ),
            "companion_id": (companion_memory_approval_preview.get("summary") or {}).get("companion_id"),
            "memory_class": (companion_memory_approval_preview.get("summary") or {}).get("memory_class"),
            "memory_approval_digest": (companion_memory_approval_preview.get("digest_proof") or {}).get(
                "memory_approval_digest"
            ),
            "approval_queue_write_allowed_after_digest": (
                companion_memory_approval_preview.get("authority") or {}
            ).get("approval_queue_write_allowed_with_digest"),
            "approval_request_created": (companion_memory_approval_preview.get("summary") or {}).get(
                "approval_request_created"
            ),
            "memory_write_allowed": False,
            "memory_file_written": False,
        },
        "companion_memory_approval_preview": companion_memory_approval_preview,
        "companion_memory_approved_execution_proof_posture": {
            "execution_proof_visible": True,
            "execution_proof_available": True,
            "api_method": "execute_phase11_companion_memory_approved_execution_proof",
            "approval_id_required": True,
            "expected_memory_approval_digest_required": True,
            "execute_flag_required": True,
            "approval_consumption_allowed_through_explicit_executor": True,
            "ambient_chat_consumption_allowed": False,
            "generic_studio_service_execution_allowed": False,
            "proof_only": True,
            "memory_ledger_write_allowed": False,
            "memory_root_create_allowed": False,
            "provider_calls_allowed": False,
            "runtime_dispatch_allowed": False,
            "agent_bus_task_write_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "companion_memory_approved_execution_proof": companion_memory_approved_execution_proof,
        "companion_memory_readback_search_posture": {
            "readback_search_visible": True,
            "readback_search_ready": (
                companion_memory_readback_search_preview.get("readiness") or {}
            ).get("companion_memory_readback_search_preview_ready"),
            "proof_index_ready": (
                companion_memory_readback_search_preview.get("readiness") or {}
            ).get("companion_memory_proof_index_ready"),
            "results_count": (companion_memory_readback_search_preview.get("summary") or {}).get(
                "results_count"
            ),
            "proof_record_count": (companion_memory_readback_search_preview.get("summary") or {}).get(
                "proof_record_count"
            ),
            "query": (companion_memory_readback_search_preview.get("filters") or {}).get("query"),
            "api_method": "get_phase11_companion_memory_readback_search_preview",
            "memory_ledger_write_allowed": False,
            "real_memory_ledger_read_allowed": False,
            "provider_calls_allowed": False,
            "runtime_dispatch_allowed": False,
            "agent_bus_task_write_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "companion_memory_readback_search_preview": companion_memory_readback_search_preview,
        "companion_memory_ledger_write_approval_posture": {
            "ledger_write_approval_preview_visible": True,
            "ledger_write_approval_preview_ready": (
                companion_memory_ledger_write_approval_preview.get("summary") or {}
            ).get("ledger_write_approval_preview_ready"),
            "source_approval_id": (
                companion_memory_ledger_write_approval_preview.get("summary") or {}
            ).get("source_approval_id"),
            "companion_id": (
                companion_memory_ledger_write_approval_preview.get("summary") or {}
            ).get("companion_id"),
            "memory_class": (
                companion_memory_ledger_write_approval_preview.get("summary") or {}
            ).get("memory_class"),
            "ledger_write_approval_digest": (
                companion_memory_ledger_write_approval_preview.get("digest_proof") or {}
            ).get("ledger_write_approval_digest"),
            "approval_queue_write_allowed_after_digest": (
                companion_memory_ledger_write_approval_preview.get("authority") or {}
            ).get("approval_queue_write_allowed_with_digest"),
            "approval_request_created": (
                companion_memory_ledger_write_approval_preview.get("summary") or {}
            ).get("approval_request_created"),
            "memory_ledger_write_allowed": False,
            "real_memory_ledger_read_allowed": False,
            "provider_calls_allowed": False,
            "runtime_dispatch_allowed": False,
            "agent_bus_task_write_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "companion_memory_ledger_write_approval_preview": companion_memory_ledger_write_approval_preview,
        "companion_memory_approved_ledger_write_execution_posture": {
            "approved_ledger_write_executor_visible": True,
            "api_method": "execute_phase11_companion_memory_approved_ledger_write_execution_proof",
            "approval_id_required": True,
            "expected_ledger_write_approval_digest_required": True,
            "execute_flag_required": True,
            "approval_consumption_allowed_through_explicit_executor": True,
            "memory_ledger_write_allowed_through_explicit_executor": True,
            "ambient_chat_ledger_write_allowed": False,
            "generic_studio_service_execution_allowed": False,
            "provider_calls_allowed": False,
            "runtime_dispatch_allowed": False,
            "browser_control_allowed": False,
            "agent_bus_task_write_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "companion_memory_approved_ledger_write_execution_proof": companion_memory_approved_ledger_write_execution_proof,
        "companion_memory_ledger_read_model_posture": {
            "ledger_read_model_visible": True,
            "ledger_read_model_ready": (
                companion_memory_ledger_read_model_preview.get("readiness") or {}
            ).get("companion_memory_ledger_read_model_preview_ready"),
            "real_memory_ledger_read_allowed": (
                companion_memory_ledger_read_model_preview.get("authority") or {}
            ).get("real_companion_memory_read_allowed"),
            "memory_ledger_write_allowed": False,
            "ledger_entry_count": (companion_memory_ledger_read_model_preview.get("summary") or {}).get(
                "ledger_entry_count"
            ),
            "proof_backfill_count": (companion_memory_ledger_read_model_preview.get("summary") or {}).get(
                "proof_backfill_count"
            ),
            "malformed_line_count": (companion_memory_ledger_read_model_preview.get("summary") or {}).get(
                "malformed_line_count"
            ),
            "results_count": (companion_memory_ledger_read_model_preview.get("summary") or {}).get("results_count"),
            "query": (companion_memory_ledger_read_model_preview.get("filters") or {}).get("query"),
            "api_method": "get_phase11_companion_memory_ledger_read_model_preview",
            "approval_queue_write_allowed": False,
            "approval_consumption_allowed": False,
            "provider_calls_allowed": False,
            "runtime_dispatch_allowed": False,
            "browser_control_allowed": False,
            "agent_bus_task_write_allowed": False,
            "canonical_mutation_allowed": False,
            "next_recommended_pass": COMPANION_MEMORY_LEDGER_READ_MODEL_NEXT_PASS,
        },
        "companion_memory_ledger_read_model_preview": companion_memory_ledger_read_model_preview,
        "companion_memory_real_ledger_activation_posture": {
            "real_ledger_activation_closeout_visible": True,
            "real_ledger_activation_closeout_ready": (
                companion_memory_real_ledger_activation_closeout.get("readiness") or {}
            ).get("companion_memory_real_ledger_activation_closeout_ready"),
            "real_ledger_active": (
                companion_memory_real_ledger_activation_closeout.get("summary") or {}
            ).get("real_ledger_active"),
            "approval_id": (
                companion_memory_real_ledger_activation_closeout.get("summary") or {}
            ).get("approval_id"),
            "approval_consumed": (
                companion_memory_real_ledger_activation_closeout.get("summary") or {}
            ).get("approval_consumed"),
            "exact_once_marker_exists": (
                companion_memory_real_ledger_activation_closeout.get("summary") or {}
            ).get("exact_once_marker_exists"),
            "evidence_outputs_present": (
                companion_memory_real_ledger_activation_closeout.get("summary") or {}
            ).get("evidence_outputs_present"),
            "ledger_line_count": (
                companion_memory_real_ledger_activation_closeout.get("summary") or {}
            ).get("ledger_line_count"),
            "duplicate_execution_would_block_before_append": (
                companion_memory_real_ledger_activation_closeout.get("summary") or {}
            ).get("duplicate_execution_would_block_before_append"),
            "api_method": "get_phase11_companion_memory_real_ledger_activation_closeout",
            "memory_ledger_write_allowed": (
                companion_memory_real_ledger_activation_closeout.get("authority") or {}
            ).get("memory_ledger_write_allowed"),
            "approval_consumption_allowed": (
                companion_memory_real_ledger_activation_closeout.get("authority") or {}
            ).get("approval_consumption_allowed"),
            "provider_calls_allowed": (
                companion_memory_real_ledger_activation_closeout.get("authority") or {}
            ).get("provider_calls_allowed"),
            "runtime_dispatch_allowed": (
                companion_memory_real_ledger_activation_closeout.get("authority") or {}
            ).get("runtime_dispatch_allowed"),
            "agent_bus_task_write_allowed": (
                companion_memory_real_ledger_activation_closeout.get("authority") or {}
            ).get("agent_bus_task_write_allowed"),
            "canonical_mutation_allowed": (
                companion_memory_real_ledger_activation_closeout.get("authority") or {}
            ).get("canonical_mutation_allowed"),
            "next_recommended_pass": COMPANION_MEMORY_REAL_LEDGER_CLOSEOUT_NEXT_PASS,
        },
        "companion_memory_real_ledger_activation_closeout": companion_memory_real_ledger_activation_closeout,
        "companion_memory_context_readiness_posture": {
            "context_readiness_visible": True,
            "context_readiness_ready": (
                companion_memory_context_readiness_preview.get("readiness") or {}
            ).get("companion_memory_context_readiness_preview_ready"),
            "context_packet_ready": (
                companion_memory_context_readiness_preview.get("summary") or {}
            ).get("context_packet_ready"),
            "context_item_count": (
                companion_memory_context_readiness_preview.get("summary") or {}
            ).get("context_item_count"),
            "source_record_count": (
                companion_memory_context_readiness_preview.get("summary") or {}
            ).get("source_record_count"),
            "context_chars": (
                companion_memory_context_readiness_preview.get("summary") or {}
            ).get("context_chars"),
            "packet_id": (
                companion_memory_context_readiness_preview.get("context_packet_preview") or {}
            ).get("packet_id"),
            "api_method": "get_phase11_companion_memory_context_readiness_preview",
            "provider_context_delivery_allowed": (
                companion_memory_context_readiness_preview.get("authority") or {}
            ).get("provider_context_delivery_allowed"),
            "provider_calls_allowed": (
                companion_memory_context_readiness_preview.get("authority") or {}
            ).get("provider_calls_allowed"),
            "model_calls_allowed": (
                companion_memory_context_readiness_preview.get("authority") or {}
            ).get("model_calls_allowed"),
            "approval_queue_write_allowed": (
                companion_memory_context_readiness_preview.get("authority") or {}
            ).get("approval_queue_write_allowed"),
            "memory_ledger_write_allowed": (
                companion_memory_context_readiness_preview.get("authority") or {}
            ).get("memory_ledger_write_allowed"),
            "conversation_persistence_allowed": (
                companion_memory_context_readiness_preview.get("authority") or {}
            ).get("conversation_persistence_allowed"),
            "runtime_dispatch_allowed": (
                companion_memory_context_readiness_preview.get("authority") or {}
            ).get("runtime_dispatch_allowed"),
            "agent_bus_task_write_allowed": (
                companion_memory_context_readiness_preview.get("authority") or {}
            ).get("agent_bus_task_write_allowed"),
            "canonical_mutation_allowed": (
                companion_memory_context_readiness_preview.get("authority") or {}
            ).get("canonical_mutation_allowed"),
            "requires_openai_secret_reference": (
                companion_memory_context_readiness_preview.get("readiness") or {}
            ).get("companion_memory_context_requires_openai_secret_reference"),
            "next_recommended_pass": COMPANION_MEMORY_CONTEXT_READINESS_NEXT_PASS,
        },
        "companion_memory_context_readiness_preview": companion_memory_context_readiness_preview,
        "companion_selection_posture": {
            "companion_selection_preview_visible": True,
            "requested_runtime_id": (companion_selection_preview.get("summary") or {}).get("requested_runtime_id"),
            "current_runtime_id": (companion_selection_preview.get("summary") or {}).get("current_runtime_id"),
            "approval_preview_ready": (companion_selection_preview.get("summary") or {}).get("approval_preview_ready"),
            "selection_change_requested": (companion_selection_preview.get("summary") or {}).get(
                "selection_change_requested"
            ),
            "selection_digest": (companion_selection_preview.get("digest_proof") or {}).get("selection_digest"),
            "approval_request_created": False,
            "approval_queue_writer_called": False,
            "companion_selection_write_allowed": False,
            "identity_ledger_mutation_allowed": False,
            "profile_write_allowed": False,
            "role_card_write_allowed": False,
        },
        "companion_selection_preview": companion_selection_preview,
        "companion_selection_queue_write_posture": {
            "queue_write_readiness_visible": True,
            "queue_write_readiness_ready": (companion_selection_queue_write_readiness.get("summary") or {}).get(
                "queue_write_readiness_ready"
            ),
            "requested_runtime_id": (companion_selection_queue_write_readiness.get("summary") or {}).get(
                "requested_runtime_id"
            ),
            "current_runtime_id": (companion_selection_queue_write_readiness.get("summary") or {}).get(
                "current_runtime_id"
            ),
            "selection_digest": (companion_selection_queue_write_readiness.get("digest_proof") or {}).get(
                "selection_digest"
            ),
            "queue_write_digest": (companion_selection_queue_write_readiness.get("digest_proof") or {}).get(
                "queue_write_digest"
            ),
            "approval_request_created": False,
            "approval_queue_writer_called": False,
            "approval_queue_write_allowed": False,
            "companion_selection_write_allowed": False,
            "target_write_performed": False,
        },
        "companion_selection_queue_write_readiness": companion_selection_queue_write_readiness,
        "companion_selection_queue_write_execution_posture": {
            "approval_queue_write_execution_visible": True,
            "approval_queue_write_execution_proof_ready": True,
            "approval_queue_write_allowed": True,
            "requires_exact_queue_write_digest": True,
            "queue_write_digest": (companion_selection_queue_write_readiness.get("digest_proof") or {}).get(
                "queue_write_digest"
            ),
            "approval_request_created_in_panel_preview": False,
            "approval_execution_allowed": False,
            "companion_selection_write_allowed": False,
            "target_write_performed": False,
            "runtime_control_allowed": False,
            "provider_calls_allowed": False,
            "agent_bus_task_write_allowed": False,
        },
        "companion_selection_approval_consumption_posture": {
            "consumption_readiness_visible": True,
            "consumption_executor_available": True,
            "ambient_chat_consumption_allowed": False,
            "required_executor_surface": "phase11-chat-companion-selection-approval-consumption-executor",
            "consumption_preview_ready": (
                companion_selection_approval_consumption_readiness.get("summary") or {}
            ).get("consumption_preview_ready"),
            "consumption_preconditions_met": (
                companion_selection_approval_consumption_readiness.get("summary") or {}
            ).get("consumption_preconditions_met"),
            "selected_approval_id": (
                companion_selection_approval_consumption_readiness.get("summary") or {}
            ).get("selected_approval_id"),
            "approval_status": (
                companion_selection_approval_consumption_readiness.get("summary") or {}
            ).get("approval_status"),
            "consumption_digest": (
                companion_selection_approval_consumption_readiness.get("digest_proof") or {}
            ).get("consumption_digest"),
            "approval_status_mutated": False,
            "approval_execution_called": False,
            "exact_once_marker_written": False,
            "exact_once_marker_write_allowed_through_executor_only": True,
            "companion_selection_write_allowed": False,
            "companion_selection_write_allowed_through_executor_only": True,
            "target_write_performed": False,
            "runtime_control_allowed": False,
            "provider_calls_allowed": False,
            "agent_bus_task_write_allowed": False,
            "approval_execution_allowed": False,
        },
        "companion_selection_approval_consumption_readiness": companion_selection_approval_consumption_readiness,
        "readonly_slash_command_response_posture": {
            "response_cards_visible": True,
            "response_cards_ready": (
                readonly_slash_command_responses.get("summary") or {}
            ).get("response_cards_ready"),
            "slash_token": (readonly_slash_command_responses.get("summary") or {}).get("slash_token"),
            "card_count": (readonly_slash_command_responses.get("summary") or {}).get("response_card_count"),
            "command_execution_allowed": False,
            "approval_execution_allowed": False,
            "runtime_dispatch_allowed": False,
            "browser_control_allowed": False,
            "provider_calls_allowed": False,
            "vault_writes_allowed": False,
            "agent_bus_task_write_allowed": False,
        },
        "authority": {**authority, **safety_policy.get("authority_matrix", {})},
        "denied_by_this_surface": [
            "slash_command_execution",
            "llm_intent_classification_call",
            "provider_api_call",
            "chat_response_generation_call",
            "live_provider_probe_execution",
            "provider_switch",
            "companion_selection_write",
            "credential_value_display",
            "runtime_dispatch",
            "browser_control",
            "approval_grant_or_reject",
            "approval_execution",
            "vault_file_write",
            "conversation_log_write",
            "workspace_mode_profile_write",
            "workspace_mode_workflow_execution",
            "chat_workspace_write",
            "chat_folder_write",
            "chat_thread_create",
            "chat_message_send",
            "runtime_board_write",
            "agent_bus_task_write",
            "schedule_mutation",
            "canonical_writeback",
        ],
        "blocked_reasons": list(dict.fromkeys(panel_blockers)),
        "native_panel": {
            "mounted": True,
            "panel_id": "chat",
            "frontend_target": "panel-chat",
            "route_hint": "#chat",
            "read_only": True,
            "write_mode": "local_ui_state_only_plus_approval_gated",
            "possible_writes": [
                "local_chat_schedule_ui_action_state",
                "local_chat_route_state",
                "local_chat_message_draft",
                "runtime_board_handoff_approval_queue_request",
                "schedule_proposal_approval_queue_request",
                "approved_chat_schedule_proposal_staged_record",
                "approved_chat_schedule_intent_yaml",
                "runtime_schedules_index_regeneration",
                "schedule_activation_approval_queue_request",
                "approved_chat_schedule_activation_enablement",
                "schedule_adapter_export_approval_queue_request",
                "approved_schedule_adapter_export_packet",
            ],
            "status": "mounted-local-ui-state-only",
        },
        "readiness": {
            "chat_panel_contract_ready": True,
            "safety_policy_ready": True,
            "all_chat_capabilities_policy_aware": bool(safety_policy.get("all_capabilities_policy_aware", True)),
            "authority_absent_fails_closed": bool(safety_policy.get("authority_absent_fails_closed", True)),
            "chat_panel_mounted": True,
            "router_contract_consumed": True,
            "provider_readiness_visible": True,
            "slash_command_preview_visible": True,
            "readonly_slash_command_responses_ready": True,
            "readonly_slash_command_response_ui_ready": True,
            "readonly_slash_command_execution_blocked": True,
            "workspace_mode_context_visible": True,
            "workspace_mode_deeplink_selector_visible": bool(workspace_mode_deeplink_selector.get("visible")),
            "workspace_mode_deeplink_selector_ready": bool(workspace_mode_deeplink_selector.get("card_count")),
            "workspace_mode_deeplink_navigation_only": True,
            "workspace_mode_deeplink_execution_blocked": True,
            "workspace_mode_panel_ready": bool(workspace_mode_context.get("panel_mounted")),
            "workspace_mode_project_dashboard_connected": bool(
                workspace_mode_context.get("project_dashboard_connected")
            ),
            "workspace_mode_chat_execution_blocked": True,
            "workspace_mode_profile_write_blocked": True,
            "studio_runtime_chat_workspaces_foundation_ready": (
                (chat_workspaces_foundation.get("readiness") or {}).get(
                    "studio_runtime_chat_workspaces_foundation_ready"
                )
                is True
            ),
            "studio_runtime_chat_workspace_proposal_writer_ready": (
                chat_workspace_proposal_writer.get("surface") == "phase11_chat_workspace_proposal_writer"
            ),
            "studio_runtime_chat_workspace_proposal_consumption_executor_ready": (
                chat_workspace_proposal_consumption_executor.get("surface")
                == WORKSPACE_PROPOSAL_CONSUMPTION_SURFACE_ID
            ),
            "studio_runtime_chat_workspace_target_state_executor_ready": (
                chat_workspace_target_state_executor.get("surface") == WORKSPACE_TARGET_STATE_SURFACE_ID
            ),
            "studio_runtime_chat_route_state_and_message_drafts_ready": (
                chat_route_state_and_message_drafts.get("surface") == CHAT_ROUTE_STATE_SURFACE_ID
            ),
            "studio_runtime_chat_runtime_board_handoff_proposal_ready": (
                chat_runtime_board_handoff_proposal.get("surface") == CHAT_RUNTIME_BOARD_HANDOFF_SURFACE_ID
            ),
            "studio_runtime_chat_schedule_proposal_packet_ready": (
                chat_schedule_proposal_packet.get("surface") == CHAT_SCHEDULE_PROPOSAL_SURFACE_ID
            ),
            "studio_runtime_chat_schedule_proposal_consumption_executor_ready": (
                chat_schedule_proposal_consumption_executor.get("surface")
                == CHAT_SCHEDULE_PROPOSAL_CONSUMPTION_SURFACE_ID
            ),
            "studio_runtime_chat_approved_schedule_intent_writer_ready": (
                chat_approved_schedule_intent_writer.get("surface")
                == CHAT_APPROVED_SCHEDULE_INTENT_WRITER_SURFACE_ID
            ),
            "studio_runtime_chat_schedule_intent_activation_readiness_ready": (
                chat_schedule_intent_activation_readiness.get("surface")
                == CHAT_SCHEDULE_INTENT_ACTIVATION_SURFACE_ID
            ),
            "studio_runtime_chat_approved_schedule_activation_executor_ready": (
                chat_approved_schedule_activation_executor.get("surface")
                == CHAT_APPROVED_SCHEDULE_ACTIVATION_SURFACE_ID
            ),
            "studio_runtime_chat_schedule_adapter_export_readiness_ready": (
                chat_schedule_adapter_export_readiness.get("surface")
                == CHAT_SCHEDULE_ADAPTER_EXPORT_SURFACE_ID
            ),
            "studio_runtime_chat_approved_schedule_adapter_export_packet_writer_ready": (
                chat_approved_schedule_adapter_export_packet_writer.get("surface")
                == CHAT_APPROVED_SCHEDULE_ADAPTER_EXPORT_WRITER_SURFACE_ID
            ),
            "studio_runtime_chat_schedule_ui_action_controls_and_readback_ready": (
                chat_schedule_ui_action_controls_and_readback.get("surface")
                == CHAT_SCHEDULE_UI_ACTION_CONTROLS_SURFACE_ID
            ),
            "studio_chat_authority_tier_controls_ready": (
                chat_authority_tier_controls.get("surface") == CHAT_AUTHORITY_TIER_CONTROLS_SURFACE_ID
            ),
            "studio_chat_authority_tier_controls_visible": True,
            "studio_chat_authority_tier_navigation_only": True,
            "studio_chat_authority_tier_direct_execution_blocked": True,
            "studio_chat_authority_tier_no_secret_values": True,
            "studio_chat_authority_tier_provider_calls_blocked": True,
            "studio_chat_authority_tier_discord_calls_blocked": True,
            "studio_chat_authority_tier_agent_bus_writes_blocked": True,
            "studio_chat_authority_tier_runtime_dispatch_blocked": True,
            "studio_chat_authority_tier_external_cron_blocked": True,
            "studio_chat_authority_execution_controls_ready": (
                chat_authority_execution_controls.get("surface") == CHAT_AUTHORITY_EXECUTION_CONTROLS_SURFACE_ID
            ),
            "studio_chat_authority_execution_controls_visible": True,
            "studio_chat_authority_execution_manual_test_ready": bool(
                chat_authority_execution_summary.get("manual_test_ready")
            ),
            "studio_chat_authority_execution_provider_executor_ready": True,
            "studio_chat_authority_execution_runtime_dispatch_executor_ready": True,
            "studio_chat_authority_execution_agent_bus_write_gated": True,
            "studio_chat_authority_execution_discord_control_runtime_handoff_ready": True,
            "studio_chat_authority_execution_cron_control_runtime_handoff_ready": True,
            "studio_chat_authority_execution_secret_values_hidden": True,
            "studio_chat_authority_execution_direct_discord_api_blocked": True,
            "studio_chat_authority_execution_external_cron_mutation_blocked": True,
            "studio_chat_schedule_ui_controls_rendered": True,
            "studio_chat_schedule_manual_ui_test_ready": True,
            "studio_chat_schedule_ui_readback_ready": True,
            "studio_chat_schedule_ui_no_secret_fields": True,
            "studio_chat_workspace_proposal_preview_ready": (
                chat_workspace_proposal_summary.get("queue_write_preview_ready") is True
            ),
            "studio_chat_workspace_proposal_requires_digest": True,
            "studio_chat_workspace_proposal_target_write_approval_gated": True,
            "studio_chat_workspace_proposal_target_write_blocked": True,
            "studio_chat_workspace_proposal_ambient_execution_blocked": True,
            "studio_chat_workspace_proposal_consumption_requires_approval_and_digest": True,
            "studio_chat_workspace_target_state_requires_proposal_digest_and_statement": True,
            "studio_chat_workspace_target_state_ambient_execution_blocked": True,
            "studio_chat_route_state_persistence_ready": True,
            "studio_chat_message_draft_state_ready": True,
            "studio_chat_message_intent_state_ready": True,
            "studio_chat_route_state_local_write_only": True,
            "studio_chat_message_draft_local_write_only": True,
            "studio_chat_runtime_board_handoff_digest_ready": bool(
                (chat_runtime_board_handoff_proposal.get("digest_proof") or {}).get("handoff_digest")
            ),
            "studio_chat_runtime_board_handoff_approval_queue_gated": True,
            "studio_chat_runtime_board_handoff_requires_digest": True,
            "studio_chat_runtime_board_handoff_ambient_execution_blocked": True,
            "studio_chat_runtime_board_write_still_blocked": True,
            "studio_chat_agent_bus_task_write_still_blocked": True,
            "studio_chat_runtime_dispatch_still_blocked": True,
            "studio_chat_schedule_proposal_digest_ready": bool(
                (chat_schedule_proposal_packet.get("digest_proof") or {}).get("schedule_digest")
            ),
            "studio_chat_schedule_proposal_approval_queue_gated": True,
            "studio_chat_schedule_proposal_requires_digest": True,
            "studio_chat_schedule_proposal_ambient_execution_blocked": True,
            "studio_chat_schedule_proposal_consumption_requires_approval_and_digest": True,
            "studio_chat_schedule_proposal_consumption_writes_staged_record_only": True,
            "studio_chat_schedule_proposal_consumption_schedule_yaml_write_blocked": True,
            "studio_chat_schedule_proposal_consumption_index_regeneration_blocked": True,
            "studio_chat_schedule_proposal_consumption_external_scheduler_blocked": True,
            "studio_chat_schedule_intent_write_still_blocked": True,
            "studio_chat_schedule_index_regeneration_still_blocked": True,
            "studio_chat_schedule_intent_write_explicit_writer_ready": True,
            "studio_chat_schedule_index_regeneration_explicit_writer_ready": True,
            "studio_chat_approved_schedule_intent_writer_requires_staged_record_digest_statement": True,
            "studio_chat_approved_schedule_intent_writer_schedule_yaml_write_approval_gated": True,
            "studio_chat_approved_schedule_intent_writer_index_regeneration_approval_gated": True,
            "studio_chat_approved_schedule_intent_writer_external_scheduler_blocked": True,
            "studio_chat_schedule_intent_activation_readiness_requires_schedule_id": True,
            "studio_chat_schedule_intent_activation_request_requires_digest": True,
            "studio_chat_schedule_intent_activation_approval_queue_gated": True,
            "studio_chat_schedule_intent_activation_execution_blocked": True,
            "studio_chat_schedule_enable_still_blocked": True,
            "studio_chat_schedule_enable_explicit_executor_ready": True,
            "studio_chat_approved_schedule_activation_requires_approval_and_digest": True,
            "studio_chat_approved_schedule_activation_enables_schedule_only": True,
            "studio_chat_approved_schedule_activation_external_scheduler_blocked": True,
            "studio_chat_approved_schedule_activation_cron_mutation_blocked": True,
            "studio_chat_schedule_adapter_export_readiness_requires_adapter": True,
            "studio_chat_schedule_adapter_export_request_requires_digest": True,
            "studio_chat_schedule_adapter_export_packet_write_blocked": False,
            "studio_chat_approved_schedule_adapter_export_requires_approval_and_digest": True,
            "studio_chat_approved_schedule_adapter_export_writes_local_packet_only": True,
            "studio_chat_approved_schedule_adapter_export_external_scheduler_blocked": True,
            "studio_chat_approved_schedule_adapter_export_cron_mutation_blocked": True,
            "studio_chat_schedule_adapter_export_external_scheduler_blocked": True,
            "studio_chat_schedule_adapter_export_cron_mutation_blocked": True,
            "studio_chat_schedule_external_cron_still_blocked": True,
            "studio_chat_schedule_runtime_dispatch_still_blocked": True,
            "studio_chat_schedule_activation_external_scheduler_blocked": True,
            "studio_chat_external_scheduler_mutation_still_blocked": True,
            "studio_chat_native_state_write_executor_ready": True,
            "studio_chat_workspace_threads_visible": True,
            "studio_chat_native_thread_creation_blocked": True,
            "studio_chat_message_send_blocked": True,
            "studio_chat_message_send_still_blocked": True,
            "studio_chat_transcript_write_still_blocked": True,
            "studio_chat_runtime_board_write_blocked": True,
            "studio_chat_cron_management_write_blocked": True,
            "proposal_card_preview_visible": True,
            "proposal_card_action_preview_ready": True,
            "proposal_card_handback_buttons_visible": True,
            "approval_handoff_preflight_visible": True,
            "approval_handoff_queue_contract_visible": True,
            "conversation_persistence_contract_visible": True,
            "post_closeout_planning_visible": True,
            "live_routing_gate_visible": True,
            "conversation_persistence_contract_built": True,
            "conversation_persistence_built": False,
            "live_model_execution_built": True,
            "approval_queue_write_built": True,
            "approval_queue_write_execution_proof_ready": True,
            "approval_queue_write_requires_expected_digest": True,
            "live_provider_execution_approval_preview_ready": True,
            "live_provider_calls_blocked": False,
            "live_provider_calls_digest_and_statement_gated": True,
            "runtime_dispatch_readiness_contract_ready": True,
            "runtime_dispatch_executor_ready": True,
            "runtime_dispatch_blocked": True,
            "browser_dispatch_readiness_contract_ready": True,
            "browser_dispatch_blocked": True,
            "approval_consumption_readiness_contract_ready": True,
            "approval_consumption_blocked": True,
            "runtime_status_explanation_ready": True,
            "companion_status_contract_ready": True,
            "companion_status_authority_neutral": True,
            "companion_roster_ui_preview_ready": (companion_roster_ui_preview.get("summary") or {}).get(
                "roster_ui_preview_ready"
            )
            is True,
            "companion_roster_ui_selection_write_blocked": True,
            "companion_roster_ui_provider_model_selection_blocked": True,
            "companion_roster_ui_memory_access_blocked": True,
            "companion_memory_boundary_contract_ready": (
                companion_memory_boundary_contract.get("readiness") or {}
            ).get("companion_memory_boundary_contract_ready")
            is True,
            "companion_memory_approval_preview_ready": (
                companion_memory_approval_preview.get("readiness") or {}
            ).get("companion_memory_approval_preview_ready")
            is True,
            "companion_memory_approved_execution_proof_ready": True,
            "companion_memory_readback_search_preview_ready": (
                companion_memory_readback_search_preview.get("readiness") or {}
            ).get("companion_memory_readback_search_preview_ready")
            is True,
            "companion_memory_proof_search_ready": (
                companion_memory_readback_search_preview.get("readiness") or {}
            ).get("companion_memory_proof_search_ready")
            is True,
            "companion_memory_ledger_write_approval_preview_ready": (
                companion_memory_ledger_write_approval_preview.get("readiness") or {}
            ).get("companion_memory_ledger_write_approval_preview_ready")
            is True,
            "companion_memory_ledger_write_approval_queue_write_gated": True,
            "companion_memory_approved_ledger_write_executor_required": False,
            "companion_memory_approved_ledger_write_execution_proof_ready": True,
            "companion_memory_ledger_read_model_preview_ready": (
                companion_memory_ledger_read_model_preview.get("readiness") or {}
            ).get("companion_memory_ledger_read_model_preview_ready")
            is True,
            "companion_memory_real_ledger_read_model_ready": (
                companion_memory_ledger_read_model_preview.get("readiness") or {}
            ).get("companion_memory_real_ledger_read_model_ready")
            is True,
            "companion_memory_real_ledger_activation_closeout_ready": (
                companion_memory_real_ledger_activation_closeout.get("readiness") or {}
            ).get("companion_memory_real_ledger_activation_closeout_ready")
            is True,
            "companion_memory_real_ledger_active": (
                companion_memory_real_ledger_activation_closeout.get("readiness") or {}
            ).get("companion_memory_real_ledger_active")
            is True,
            "companion_memory_duplicate_guard_verified": (
                companion_memory_real_ledger_activation_closeout.get("readiness") or {}
            ).get("companion_memory_duplicate_guard_verified")
            is True,
            "companion_memory_context_readiness_preview_ready": (
                companion_memory_context_readiness_preview.get("readiness") or {}
            ).get("companion_memory_context_readiness_preview_ready")
            is True,
            "companion_memory_context_packet_ready": (
                companion_memory_context_readiness_preview.get("readiness") or {}
            ).get("companion_memory_context_packet_ready")
            is True,
            "companion_memory_context_for_chat_ui_ready": (
                companion_memory_context_readiness_preview.get("readiness") or {}
            ).get("companion_memory_context_for_chat_ui_ready")
            is True,
            "companion_memory_context_provider_delivery_blocked": (
                companion_memory_context_readiness_preview.get("readiness") or {}
            ).get("companion_memory_context_provider_delivery_blocked")
            is True,
            "companion_memory_context_requires_openai_secret_reference": (
                companion_memory_context_readiness_preview.get("readiness") or {}
            ).get("companion_memory_context_requires_openai_secret_reference")
            is True,
            "companion_memory_real_ledger_write_approval_gated": True,
            "companion_memory_real_ledger_write_ambient_blocked": True,
            "companion_memory_real_ledger_read_blocked": False,
            "companion_memory_real_ledger_write_blocked": True,
            "companion_memory_approval_consumption_proof_only": True,
            "companion_memory_exact_once_marker_ready": True,
            "companion_memory_proof_outputs_ready": True,
            "companion_memory_ledger_writes_blocked": True,
            "companion_memory_approval_queue_write_gated": True,
            "companion_memory_separate_namespace_declared": (
                companion_memory_boundary_contract.get("summary") or {}
            ).get("separate_memory_namespace_declared")
            is True,
            "companion_memory_writes_blocked": True,
            "companion_memory_approval_required": True,
            "companion_selection_approval_preview_ready": True,
            "companion_selection_queue_write_readiness_ready": True,
            "companion_selection_queue_write_execution_proof_ready": True,
            "companion_selection_approval_consumption_readiness_ready": True,
            "companion_selection_approval_consumption_blocked": True,
            "companion_selection_queue_write_blocked": True,
            "companion_selection_target_write_blocked": True,
            "companion_selection_write_blocked": True,
            "companion_profile_writes_blocked": True,
            "companion_runtime_control_blocked": True,
            "approval_status_mutation_blocked": True,
            "exact_once_marker_write_blocked": True,
            "browser_launch_blocked": True,
            "browser_navigation_blocked": True,
            "browser_screenshot_capture_blocked": True,
            "agent_bus_task_write_blocked": True,
            "workflow_dispatch_blocked": True,
            "original_objective_closed": True,
            "original_objective_status": CLOSEOUT_STATUS,
            "no_direct_write_authority_expansion": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
    }
