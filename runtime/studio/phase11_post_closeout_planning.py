"""Read-only Phase 11 post-closeout implementation plan contract.

The Phase 11 Chat/router/provider/approval-handoff foundation is already
closed. This module turns the remaining conversational command-center work into
a dependency-aware, machine-readable next-pass map without granting any new
runtime, provider, browser, approval, queue, or vault-write authority.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.phase11_chat_approval_handoff_queue_contract import (
    build_phase11_chat_approval_handoff_queue_contract,
)


MODEL_VERSION = "studio.phase11_post_closeout_planning.v1"
SURFACE_ID = "phase11_post_closeout_planning"
PASS_ID = "phase11-conversational-command-center-post-closeout-planning"
STATUS = "COMPLETE / READ-ONLY / VERIFIED / POST-CLOSEOUT PLAN READY"
CONVERSATION_PERSISTENCE_PASS = "phase11-chat-conversation-persistence-approval-contract"
APPROVAL_QUEUE_WRITE_PASS = "phase11-chat-approval-queue-write-execution-proof"
LIVE_PROVIDER_APPROVAL_PREVIEW_PASS = "phase11-chat-live-provider-execution-approval-preview"
RUNTIME_DISPATCH_READINESS_PASS = "phase11-chat-runtime-dispatch-readiness-contract"
BROWSER_DISPATCH_READINESS_PASS = "phase11-chat-browser-dispatch-readiness-contract"
APPROVAL_CONSUMPTION_READINESS_PASS = "phase11-chat-approval-consumption-readiness-contract"
COMPANION_STATUS_READONLY_PASS = "phase11-chat-companion-status-readonly"
COMPANION_STATUS_UI_SHELL_PASS = "phase11-chat-companion-status-ui-shell"
COMPANION_SELECTION_APPROVAL_PREVIEW_PASS = "phase11-chat-companion-selection-approval-preview"
COMPANION_SELECTION_QUEUE_WRITE_READINESS_PASS = "phase11-chat-companion-selection-queue-write-readiness"
COMPANION_SELECTION_QUEUE_WRITE_EXECUTION_PROOF_PASS = "phase11-chat-companion-selection-queue-write-execution-proof"
COMPANION_SELECTION_APPROVAL_CONSUMPTION_READINESS_PASS = (
    "phase11-chat-companion-selection-approval-consumption-readiness"
)
READONLY_SLASH_COMMAND_RESPONSES_PASS = "phase11-chat-readonly-slash-command-responses"
READONLY_SLASH_COMMAND_RESPONSE_UI_PASS = "phase11-chat-readonly-slash-command-response-ui"
READONLY_CARD_VISUAL_QA_PASS = "phase11-chat-readonly-card-visual-qa"
NO_HITL_FEATURE_FAMILY_SELECTION_AUDIT_PASS = "phase11-chat-no-hitl-feature-family-selection-audit"
READONLY_SLASH_COMMAND_CATALOG_AUDIT_PASS = "phase11-chat-readonly-slash-command-catalog-audit"
READONLY_OPERATOR_DASHBOARD_AGGREGATE_AUDIT_PASS = "phase11-chat-readonly-operator-dashboard-aggregate-audit"
NO_HITL_LANE_COMPLETION_AUDIT_PASS = "phase11-chat-no-hitl-lane-completion-audit"
OPERATOR_GOVERNED_EXECUTOR_OR_DEFERRED_CLOSEOUT_PASS = "operator-selected-governed-executor-or-deferred-closeout"
OPERATOR_ACTION_REQUIRED_NO_AUTONOMOUS_PASS = "operator-action-required-no-autonomous-phase11-pass"
NEXT_RECOMMENDED_PASS = OPERATOR_ACTION_REQUIRED_NO_AUTONOMOUS_PASS


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _pass(
    pass_id: str,
    *,
    title: str,
    status: str,
    depends_on: list[str],
    purpose: str,
    likely_files: list[str],
    backend_contract: list[str],
    ui_behavior: list[str],
    authority_boundary: list[str],
    tests: list[str],
    can_parallelize_with: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "pass_id": pass_id,
        "title": title,
        "status": status,
        "depends_on": depends_on,
        "purpose": purpose,
        "likely_files": likely_files,
        "backend_contract": backend_contract,
        "ui_behavior": ui_behavior,
        "authority_boundary": authority_boundary,
        "tests": tests,
        "can_parallelize_with": can_parallelize_with or [],
    }


def _remaining_passes() -> list[dict[str, Any]]:
    return [
        _pass(
            NEXT_RECOMMENDED_PASS,
            title="Operator Action Required / No Autonomous Phase 11 Pass",
            status="COMPLETE / READ-ONLY / VERIFIED / OPERATOR DECISION REQUIRED",
            depends_on=[OPERATOR_GOVERNED_EXECUTOR_OR_DEFERRED_CLOSEOUT_PASS],
            purpose="Record that the operator-governed handoff is complete and that the next action is an explicit operator decision rather than another autonomous implementation pass.",
            likely_files=[
                "runtime/studio/phase11_operator_action_required_no_autonomous_pass.py",
                "runtime/studio/phase11_operator_governed_executor_deferred_closeout.py",
                "runtime/studio/phase11_chat_approval_consumption_executor.py",
                "runtime/studio/phase11_chat_live_provider_execution.py",
                "runtime/studio/phase11_chat_runtime_dispatch_executor.py",
                "runtime/studio/phase11_chat_browser_dispatch_executor.py",
                "06_AGENTS/ChaseOS-Phase11-Architecture.md",
                "07_LOGS/Build-Logs/",
            ],
            backend_contract=[
                "Return operator-decision-required status without choosing a lane.",
                "Expose available governed executor/deferred closeout choices as unselected options only.",
                "Require explicit operator selection before any approval consumption, live provider call, runtime/browser dispatch, Agent Bus task write, or target mutation.",
            ],
            ui_behavior=[
                "No automatic UI action is selected.",
                "If surfaced later, render the executor/live/target options as operator-governed choices only.",
            ],
            authority_boundary=[
                "No autonomous approval consumption or execution.",
                "No autonomous provider or model call.",
                "No autonomous runtime or browser dispatch.",
                "No autonomous Agent Bus task write.",
                "No autonomous target vault/profile/role-card/canonical mutation.",
            ],
            tests=[
                "operator must select executor or defer closeout",
                "requires operator decision before executor/live/target-mutation work",
                "confirm no no-HITL pass remains",
                "confirm executor/live/target-mutation lanes require explicit human/operator gate",
                "confirm next-pass marker is an operator decision gate, not an implementation grant",
            ],
            can_parallelize_with=[],
        ),
    ]


def build_phase11_post_closeout_planning(
    vault_root: str | Path,
    *,
    message: str | None = None,
    explicit_intent: str | None = None,
) -> dict[str, Any]:
    """Build the read-only post-closeout plan for Phase 11 work."""

    vault = Path(vault_root).resolve()
    queue_contract = build_phase11_chat_approval_handoff_queue_contract(
        vault,
        message=message or "Create a new project from chat",
        explicit_intent=explicit_intent,
    )
    passes = _remaining_passes()
    next_pass = passes[0]
    blocked_authority = [
        "conversation_log_write",
        "studio_approval_queue_write",
        "approval_grant_or_execution",
        "provider_api_call",
        "runtime_dispatch",
        "browser_control",
        "agent_bus_task_write",
        "vault_file_write",
        "canonical_writeback",
    ]
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "summary": {
            "foundation_closed": True,
            "queue_handoff_contract_closed": True,
            "operator_feature_selection_required": True,
            "implementation_authority_granted": False,
            "remaining_pass_count": len(passes),
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "conversation_persistence_contract_ready": True,
            "runtime_dispatch_readiness_contract_ready": True,
            "browser_dispatch_readiness_contract_ready": True,
            "approval_consumption_readiness_contract_ready": True,
            "companion_status_readonly_contract_ready": True,
            "companion_status_ui_shell_ready": True,
            "companion_selection_approval_preview_ready": True,
            "companion_selection_queue_write_readiness_ready": True,
            "companion_selection_queue_write_execution_proof_ready": True,
            "companion_selection_approval_consumption_readiness_ready": True,
            "readonly_slash_command_responses_ready": True,
            "readonly_slash_command_response_ui_ready": True,
            "readonly_card_visual_qa_ready": True,
            "no_hitl_feature_family_selection_audit_ready": True,
            "readonly_slash_command_catalog_audit_ready": True,
            "readonly_operator_dashboard_aggregate_audit_ready": True,
            "no_hitl_lane_completion_audit_ready": True,
            "no_hitl_lane_complete": True,
            "eligible_no_hitl_remaining_count": 0,
            "operator_governed_executor_deferred_closeout_handoff_ready": True,
            "operator_action_required_no_autonomous_pass_ready": True,
            "next_pass_reason": "The operator-governed handoff is complete; remaining Phase 11 work requires an explicit operator decision to select a governed executor/live/target-mutation lane or defer closeout.",
            "can_start_next_pass_now": False,
            "writes_allowed_now": False,
            "live_execution_allowed_now": False,
        },
        "selection_gate": {
            "required": True,
            "default_selection": NEXT_RECOMMENDED_PASS,
            "selection_source": "repo_truth_next_pass_marker",
            "selected_pass": NEXT_RECOMMENDED_PASS,
        },
        "completed_foundation": [
            {
                "pass_id": "phase11-chat-router-readonly-intent-contract",
                "status": "COMPLETE / READ-ONLY / VERIFIED",
                "authority": "intent preview only",
            },
            {
                "pass_id": "phase11-chat-panel-shell-contract",
                "status": "COMPLETE / APPROVAL-GATED / VERIFIED / LIVE EXECUTION BLOCKED",
                "authority": "native Chat preview plus exact-digest approval queue request only",
            },
            {
                "pass_id": CONVERSATION_PERSISTENCE_PASS,
                "status": "COMPLETE / READ-ONLY / VERIFIED / CONVERSATION WRITES BLOCKED",
                "authority": "conversation persistence approval preview only",
            },
            {
                "pass_id": APPROVAL_QUEUE_WRITE_PASS,
                "status": "COMPLETE / APPROVAL-QUEUE-WRITE / VERIFIED / EXECUTION BLOCKED",
                "authority": "Chat proposal queue artifact write only after exact digest confirmation",
            },
            {
                "pass_id": LIVE_PROVIDER_APPROVAL_PREVIEW_PASS,
                "status": "COMPLETE / READ-ONLY / VERIFIED / PROVIDER CALLS BLOCKED",
                "authority": "future provider-call approval preview only",
            },
            {
                "pass_id": RUNTIME_DISPATCH_READINESS_PASS,
                "status": "COMPLETE / READ-ONLY / VERIFIED / RUNTIME DISPATCH BLOCKED",
                "authority": "future Agent Bus/AOR dispatch readiness preview only",
            },
            {
                "pass_id": BROWSER_DISPATCH_READINESS_PASS,
                "status": "COMPLETE / READ-ONLY / VERIFIED / BROWSER DISPATCH BLOCKED",
                "authority": "future browser dispatch readiness preview only",
            },
            {
                "pass_id": APPROVAL_CONSUMPTION_READINESS_PASS,
                "status": "COMPLETE / READ-ONLY / VERIFIED / APPROVAL CONSUMPTION BLOCKED",
                "authority": "future Chat approval consumption readiness preview only",
            },
            {
                "pass_id": COMPANION_STATUS_READONLY_PASS,
                "status": "COMPLETE / READ-ONLY / VERIFIED / AUTHORITY NEUTRAL",
                "authority": "companion status inspection without runtime control, profile writes, or identity mutation",
            },
            {
                "pass_id": COMPANION_STATUS_UI_SHELL_PASS,
                "status": "COMPLETE / READ-ONLY / VERIFIED / STATIC QA COVERED",
                "authority": "Chat UI companion status rendering without companion selection writeback",
            },
            {
                "pass_id": COMPANION_SELECTION_APPROVAL_PREVIEW_PASS,
                "status": "COMPLETE / APPROVAL-PREVIEW ONLY / VERIFIED / SELECTION WRITES BLOCKED",
                "authority": "companion selection digest and future approval preview without queue writes or selection mutation",
            },
            {
                "pass_id": COMPANION_SELECTION_QUEUE_WRITE_READINESS_PASS,
                "status": "COMPLETE / APPROVAL-QUEUE WRITE READINESS / VERIFIED / SELECTION WRITES BLOCKED",
                "authority": "companion selection queue-write readiness without selection state writes",
            },
            {
                "pass_id": COMPANION_SELECTION_QUEUE_WRITE_EXECUTION_PROOF_PASS,
                "status": "COMPLETE / APPROVAL-QUEUE-WRITE PROOF / VERIFIED / TARGET WRITES BLOCKED",
                "authority": "exact-digest companion selection approval queue write proof only",
            },
            {
                "pass_id": COMPANION_SELECTION_APPROVAL_CONSUMPTION_READINESS_PASS,
                "status": "COMPLETE / READ-ONLY / VERIFIED / APPROVAL CONSUMPTION BLOCKED",
                "authority": "future companion selection approval consumption readiness without target mutation",
            },
            {
                "pass_id": READONLY_SLASH_COMMAND_RESPONSES_PASS,
                "status": "COMPLETE / READ-ONLY / VERIFIED / NO COMMAND EXECUTION",
                "authority": "read-only slash response cards without command execution or writes",
            },
            {
                "pass_id": READONLY_SLASH_COMMAND_RESPONSE_UI_PASS,
                "status": "COMPLETE / READ-ONLY / VERIFIED / STATIC QA COVERED",
                "authority": "native Chat rendering of read-only slash response cards without authority expansion",
            },
            {
                "pass_id": READONLY_CARD_VISUAL_QA_PASS,
                "status": "COMPLETE / VISUAL QA VERIFIED / NO COMMAND EXECUTION",
                "authority": "static HTML and loopback screenshot evidence for read-only cards without command execution",
            },
            {
                "pass_id": NO_HITL_FEATURE_FAMILY_SELECTION_AUDIT_PASS,
                "status": "COMPLETE / READ-ONLY / VERIFIED / NO-HITL SELECTION AUDIT",
                "authority": "deterministic feature-family selection audit with log-only evidence writeback",
            },
            {
                "pass_id": READONLY_SLASH_COMMAND_CATALOG_AUDIT_PASS,
                "status": "COMPLETE / READ-ONLY / VERIFIED / SLASH COMMAND CATALOG AUDIT",
                "authority": "read-only slash catalog coverage audit with log-only evidence writeback",
            },
            {
                "pass_id": READONLY_OPERATOR_DASHBOARD_AGGREGATE_AUDIT_PASS,
                "status": "COMPLETE / READ-ONLY / VERIFIED / OPERATOR DASHBOARD AGGREGATE AUDIT",
                "authority": "read-only operator dashboard aggregate source audit with log-only evidence writeback",
            },
            {
                "pass_id": NO_HITL_LANE_COMPLETION_AUDIT_PASS,
                "status": "COMPLETE / READ-ONLY / VERIFIED / NO-HITL LANE COMPLETION AUDIT",
                "authority": "read-only lane completion audit with log-only evidence writeback; no further autonomous no-HITL pass remains",
            },
            {
                "pass_id": OPERATOR_GOVERNED_EXECUTOR_OR_DEFERRED_CLOSEOUT_PASS,
                "status": "COMPLETE / READ-ONLY / VERIFIED / OPERATOR HANDOFF READY",
                "authority": "read-only operator-governed handoff; no lane selected and no executor authority granted",
            },
            {
                "pass_id": "phase11-chat-approval-handoff-queue-contract",
                "status": "COMPLETE / READ-ONLY / VERIFIED / QUEUE WRITES BLOCKED",
                "authority": "approval queue preview only",
            },
        ],
        "dependency_rules": [
            "Conversation persistence approval contract precedes live provider execution.",
            "Chat-originated approval queue write proof precedes approval consumption or target writes.",
            "Runtime and browser dispatch readiness stay read-only before any dispatch executor.",
            "Companion UX is always authority-neutral and can run beside read-only readiness work.",
            "Read-only slash response UI precedes visual viewport QA; visual QA precedes no-HITL feature-family selection; selection precedes the read-only slash command catalog audit; catalog audit precedes the operator dashboard aggregate audit; dashboard aggregate audit precedes the no-HITL lane completion audit; the completed no-HITL lane precedes the operator-governed handoff, and the handoff precedes the operator-action-required decision gate.",
            "Shared truth files and indexes are serialized after implementation verification.",
        ],
        "remaining_passes": passes,
        "post_closeout_tracks": [
            {
                "track_id": "conversation_persistence",
                "selected_next": False,
                "status": "COMPLETE / READ-ONLY / VERIFIED / WRITES BLOCKED",
                "recommended_before": [
                    "approval_queue_write_surface",
                ],
                "blocked_now": [
                    "no_conversation_log_write",
                    "no_approval_packet_write",
                    "no_provider_api_call",
                ],
            },
            {
                "track_id": "approval_queue_write_surface",
                "selected_next": False,
                "recommended_before": ["approval_consumption"],
                "blocked_now": [
                    "no_target_vault_write",
                    "no_approval_execution",
                ],
                "status": "COMPLETE / APPROVAL-QUEUE-WRITE / EXECUTION BLOCKED",
            },
            {
                "track_id": "live_provider_execution",
                "selected_next": False,
                "status": "RETIRED / ARCHITECTURE VIOLATION / USE AGENT BUS INSTEAD",
                "retired": True,
                "retired_reason": "architecture_violation: studio_never_calls_providers_directly",
                "recommended_before": [],
                "blocked_now": [
                    "no_provider_api_call",
                    "no_chat_live_executor",
                    "no_operator_provider_execution_approval",
                    "studio_must_route_via_agent_bus_to_runtime",
                ],
            },
            {
                "track_id": "runtime_dispatch_readiness",
                "selected_next": False,
                "status": "COMPLETE / READ-ONLY / VERIFIED / RUNTIME DISPATCH BLOCKED",
                "recommended_before": ["browser_runtime_dispatch", "approval_consumption"],
                "blocked_now": [
                    "no_workflow_dispatch",
                    "no_agent_bus_task_write",
                    "no_runtime_lifecycle_mutation",
                ],
            },
            {
                "track_id": "approval_consumption",
                "selected_next": False,
                "status": "COMPLETE / READ-ONLY / VERIFIED / CONSUMPTION BLOCKED",
                "recommended_before": ["target_mutation"],
                "blocked_now": [
                    "no_approval_execution",
                    "no_approval_status_mutation",
                    "no_exact_once_marker_write",
                    "no_target_vault_write",
                ],
            },
            {
                "track_id": "browser_runtime_dispatch",
                "selected_next": False,
                "status": "COMPLETE / READ-ONLY / VERIFIED / BROWSER DISPATCH BLOCKED",
                "recommended_before": ["approval_consumption"],
                "blocked_now": [
                    "no_browser_control_from_chat",
                    "no_browser_dispatch_executor",
                    "no_cdp_connection",
                ],
            },
            {
                "track_id": "companion_status",
                "selected_next": False,
                "status": "COMPLETE / READ-ONLY / VERIFIED / AUTHORITY NEUTRAL",
                "recommended_before": ["live_execution"],
                "blocked_now": [
                    "no_runtime_control",
                    "no_identity_ledger_mutation",
                    "no_permission_or_role_card_mutation",
                ],
            },
            {
                "track_id": "companion_status_ui_shell",
                "selected_next": False,
                "status": "COMPLETE / READ-ONLY / VERIFIED / STATIC QA COVERED",
                "recommended_before": ["live_execution"],
                "blocked_now": [
                    "no_runtime_control",
                    "no_identity_ledger_mutation",
                    "no_companion_selection_writeback",
                ],
            },
            {
                "track_id": "companion_selection_approval_preview",
                "selected_next": False,
                "status": "COMPLETE / APPROVAL-PREVIEW ONLY / SELECTION WRITES BLOCKED",
                "recommended_before": ["companion_selection_writeback", "live_execution"],
                "blocked_now": [
                    "no_companion_selection_writeback",
                    "no_runtime_identity_mutation",
                    "no_role_card_or_profile_write",
                ],
            },
            {
                "track_id": "companion_selection_queue_write_readiness",
                "selected_next": False,
                "status": "COMPLETE / APPROVAL-QUEUE WRITE READINESS / VERIFIED",
                "recommended_before": ["companion_selection_queue_write", "companion_selection_writeback"],
                "blocked_now": [
                    "no_approval_queue_artifact_write",
                    "no_companion_selection_writeback",
                    "no_runtime_identity_mutation",
                ],
            },
            {
                "track_id": "readonly_slash_command_response_ui",
                "selected_next": False,
                "status": "COMPLETE / READ-ONLY / VERIFIED / STATIC QA COVERED",
                "recommended_before": ["readonly_card_visual_qa"],
                "blocked_now": [
                    "no_command_execution",
                    "no_provider_call",
                    "no_runtime_dispatch",
                    "no_vault_write",
                ],
            },
            {
                "track_id": "readonly_card_visual_qa",
                "selected_next": False,
                "status": "COMPLETE / VISUAL QA VERIFIED / NO COMMAND EXECUTION",
                "recommended_before": ["no_hitl_feature_family_selection_audit"],
                "blocked_now": [
                    "no_command_execution",
                    "no_approval_consumption",
                    "no_agent_bus_task_write",
                    "no_canonical_mutation",
                ],
            },
            {
                "track_id": "no_hitl_feature_family_selection_audit",
                "selected_next": False,
                "status": "COMPLETE / READ-ONLY / VERIFIED / NO-HITL SELECTION AUDIT",
                "recommended_before": ["readonly_slash_command_catalog_audit"],
                "blocked_now": [
                    "no_approval_consumption",
                    "no_provider_call",
                    "no_runtime_or_browser_dispatch",
                    "no_target_mutation",
                ],
            },
            {
                "track_id": "readonly_slash_command_catalog_audit",
                "selected_next": False,
                "status": "COMPLETE / READ-ONLY / VERIFIED / SLASH COMMAND CATALOG AUDIT",
                "recommended_before": ["readonly_operator_dashboard_aggregate_audit"],
                "blocked_now": [
                    "no_command_execution",
                    "no_approval_consumption",
                    "no_provider_call",
                    "no_runtime_or_browser_dispatch",
                    "no_target_mutation",
                ],
            },
            {
                "track_id": "readonly_operator_dashboard_aggregate_audit",
                "selected_next": False,
                "status": "COMPLETE / READ-ONLY / VERIFIED / OPERATOR DASHBOARD AGGREGATE AUDIT",
                "recommended_before": ["no_hitl_lane_completion_audit"],
                "blocked_now": [
                    "no_command_execution",
                    "no_approval_consumption",
                    "no_provider_call",
                    "no_runtime_or_browser_dispatch",
                    "no_target_mutation",
                ],
            },
            {
                "track_id": "no_hitl_lane_completion_audit",
                "selected_next": False,
                "status": "COMPLETE / READ-ONLY / VERIFIED / NO-HITL LANE COMPLETION AUDIT",
                "recommended_before": ["operator_selected_live_execution_or_deferred_closeout"],
                "blocked_now": [
                    "no_command_execution",
                    "no_approval_consumption",
                    "no_provider_call",
                    "no_runtime_or_browser_dispatch",
                    "no_target_mutation",
                ],
            },
            {
                "track_id": "operator_selected_governed_executor_or_deferred_closeout",
                "selected_next": True,
                "status": "COMPLETE / READ-ONLY / VERIFIED / OPERATOR HANDOFF READY / AWAITING OPERATOR DECISION",
                "recommended_before": [],
                "blocked_now": [
                    "requires_operator_selection",
                    "requires_approval_consumption_or_live_execution_authority",
                    "requires_explicit_target_mutation_boundary_if_selected",
                ],
            },
        ],
        "next_pass": next_pass,
        "source_contracts": {
            "approval_handoff_queue_contract": {
                "surface": queue_contract.get("surface"),
                "status": queue_contract.get("status"),
                "queue_write_allowed_now": (queue_contract.get("summary") or {}).get("queue_write_allowed_now"),
                "next_recommended_pass": (queue_contract.get("final_closeout_evidence") or {}).get("next_recommended_pass"),
            }
        },
        "authority": {
            "read_only": True,
            "planning_only": True,
            "implementation_authority_granted": False,
            "queue_writes_allowed": False,
            "conversation_persistence_allowed": False,
            "approval_queue_write_allowed": False,
            "approval_consumption_allowed": False,
            "approval_execution_allowed": False,
            "provider_calls_allowed": False,
            "runtime_dispatch_allowed": False,
            "browser_control_allowed": False,
            "agent_bus_task_write_allowed": False,
            "vault_writes_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "denied_by_this_surface": blocked_authority,
        "blocked_authority": blocked_authority,
        "verification_expectations": [
            "focused backend planning contract tests",
            "shell/API/Chat panel visibility tests",
            "static QA no-write proof",
            "CLI command contract and generated docs check",
            "broad Studio/CLI/runtime regression after implementation",
        ],
    }


def format_phase11_post_closeout_planning(model: dict[str, Any]) -> str:
    summary = model.get("summary") or {}
    lines = [
        "Phase 11 Post-Closeout Planning",
        f"  status: {model.get('status')}",
        f"  pass: {model.get('pass')}",
        f"  remaining_passes: {summary.get('remaining_pass_count')}",
        f"  next: {summary.get('next_recommended_pass')}",
        f"  writes_allowed_now: {summary.get('writes_allowed_now')}",
        f"  live_execution_allowed_now: {summary.get('live_execution_allowed_now')}",
    ]
    return "\n".join(lines)
