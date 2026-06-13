"""Phase 11 Chat browser-dispatch readiness contract.

This pass lets the Chat panel preview whether a browser-bound request could be
prepared for a future governed Browser Runtime handoff. It does not launch a
browser, invoke Browser Use, connect CDP/MCP, navigate, capture screenshots,
write approvals, dispatch runtimes, or mutate ChaseOS state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.chat_browser_runtime_dispatch_lane import (
    build_chat_studio_browser_runtime_dispatch_lane_manifest,
)
from runtime.studio.external_runtime_readiness import build_studio_external_runtime_readiness
from runtime.studio.phase11_chat_router_contract import build_phase11_chat_router_contract


MODEL_VERSION = "studio.phase11_chat_browser_dispatch_readiness.v1"
SURFACE_ID = "phase11_chat_browser_dispatch_readiness_contract"
PASS_ID = "phase11-chat-browser-dispatch-readiness-contract"
STATUS = "COMPLETE / READ-ONLY / VERIFIED / BROWSER DISPATCH BLOCKED"
NEXT_RECOMMENDED_PASS = "phase11-chat-approval-consumption-readiness-contract"
APPROVAL_CLASS = "studio_chat_browser_dispatch_approval_future"

BROWSER_BOUND_INTENTS = {"browser-task"}
BROWSER_TARGET_HINTS = {
    "excalidraw": "excalidraw",
    "whiteboard": "excalidraw",
    "browser use": "browser-use-cli",
    "browser-use": "browser-use-cli",
}

POLICY_DOCS_CHECKED = [
    "06_AGENTS/ChaseOS-Deny-Default-Runtime-Policy.md",
    "06_AGENTS/Permission-Matrix.md",
    "06_AGENTS/Agent-Security-Model.md",
    "06_AGENTS/Browser-Operator-Policy.md",
    "06_AGENTS/Trust-Tiers.md",
    "runtime/policy/gateway_allowlists.json",
    "runtime/policy/protected_files.yaml",
]

_DENIED_ACTION_TO_DEPENDENCY_KEY = {
    "vault_write": "protected_file_write",
    "lifecycle_execution": "lifecycle_execution",
    "runtime_dispatch": "runtime_dispatch",
    "browser_or_shell_or_connector_authority": "browser_shell_connector_authority",
    "approval_consumption": "approval_consumption_execution",
    "protected_file_write": "protected_file_write",
    "hidden_memory_write": "canonical_knowledge_promotion",
    "credential_or_config_mutation": "credential_config_mutation",
    "source_pack_promotion": "source_pack_creation_promotion",
    "graph_mutation": "graph_canonical_mutation",
    "canonical_knowledge_promotion": "canonical_knowledge_promotion",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(message: str | None) -> str:
    return " ".join(str(message or "").strip().split())


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _target_selection(message: str, requested_target: str | None) -> dict[str, Any]:
    requested = str(requested_target or "").strip()
    if requested:
        return {
            "requested_target": requested,
            "selected_target": requested,
            "selection_reason": "operator_requested_target",
            "known_target": requested in {"excalidraw", "browser-use-cli", "loopback"},
        }
    lowered = message.lower()
    for hint, target in BROWSER_TARGET_HINTS.items():
        if hint in lowered:
            return {
                "requested_target": "",
                "selected_target": target,
                "selection_reason": f"message_mentions_{hint.replace(' ', '_')}",
                "known_target": True,
            }
    return {
        "requested_target": "",
        "selected_target": "browser-use-cli",
        "selection_reason": "default_browser_runtime_preview",
        "known_target": True,
    }


def _action_selection(message: str, requested_action: str | None) -> dict[str, Any]:
    requested = str(requested_action or "").strip()
    allowed_actions = {"open", "inspect", "draw-proof-preview", "screenshot-preview"}
    if requested:
        return {
            "requested_action": requested,
            "selected_browser_action": requested,
            "selection_reason": "operator_requested_action",
            "action_supported_by_contract": requested in allowed_actions,
        }
    lowered = message.lower()
    selected = "draw-proof-preview" if "draw" in lowered or "whiteboard" in lowered else "open" if "open" in lowered else "inspect"
    return {
        "requested_action": "",
        "selected_browser_action": selected,
        "selection_reason": "message_inferred_browser_action",
        "action_supported_by_contract": selected in allowed_actions,
    }


def _external_readiness(vault: Path) -> dict[str, Any]:
    try:
        return build_studio_external_runtime_readiness(vault).to_dict()
    except Exception as exc:
        return {
            "status": "blocked_external_runtime_readiness_unavailable",
            "browser_use_branch_ready": False,
            "excalidraw_branch_ready": False,
            "blockers": [f"external_runtime_readiness_unavailable:{exc}"],
        }


def _policy_gate_report(router: dict[str, Any], *, surface: str) -> dict[str, Any]:
    input_posture = router.get("input_posture") or {}
    action_spec = router.get("action_spec") or {}
    ambiguity = action_spec.get("ambiguity") or {}
    denied_actions = list(input_posture.get("requested_denied_actions") or [])
    message = str(action_spec.get("normalized_command") or "").lower()
    if "browser_or_shell_or_connector_authority" in denied_actions and not any(
        token in message for token in ["connector", "cdp", "mcp", "shell", "terminal", "api call", "launch browser", "control browser"]
    ):
        denied_actions.remove("browser_or_shell_or_connector_authority")
    dependencies = list(router.get("backend_dependencies") or [])
    by_dependency_key = {str(item.get("dependency_key") or ""): item for item in dependencies}
    missing_by_action: dict[str, str] = {}
    blocked_action_reasons: list[dict[str, Any]] = []
    for action in denied_actions:
        dependency = by_dependency_key.get(_DENIED_ACTION_TO_DEPENDENCY_KEY.get(action, ""), {})
        reason = str(dependency.get("blocked_action_reason") or "missing_or_insufficient_lower_phase_authority")
        missing = str(dependency.get("missing_contract") or "missing backend contract")
        missing_by_action[action] = f"{missing}: {reason}"
        blocked_action_reasons.append(
            {
                "action_class": action,
                "denied": True,
                "missing_or_insufficient_authority": missing,
                "blocked_action_reason": reason,
            }
        )
    if ambiguity.get("requires_operator_clarification"):
        blocked_action_reasons.append(
            {
                "action_class": "ambiguous_command",
                "denied": True,
                "missing_or_insufficient_authority": "operator clarification required before routing",
                "blocked_action_reason": "ambiguous Phase 11 Chat command cannot launch, navigate, capture, or write",
            }
        )
    fail_closed = bool(denied_actions) or bool(ambiguity.get("requires_operator_clarification"))
    return {
        "surface": surface,
        "deny_default_runtime_policy_applied": True,
        "browser_operator_policy_applied": True,
        "policy_docs_checked": POLICY_DOCS_CHECKED,
        "phase10_11_surface_only": True,
        "not_canonical_truth_engine": True,
        "fail_closed": fail_closed,
        "side_effects_performed": False,
        "execution_allowed": False,
        "denied_action_classes": denied_actions,
        "ambiguous_command": ambiguity,
        "backend_dependency_reports": dependencies,
        "missing_or_insufficient_authority_by_action": missing_by_action,
        "blocked_action_reasons": blocked_action_reasons,
    }


def build_phase11_chat_browser_dispatch_readiness(
    vault_root: str | Path,
    *,
    message: str | None = None,
    explicit_intent: str | None = None,
    requested_target: str | None = None,
    requested_action: str | None = None,
) -> dict[str, Any]:
    """Build a read-only readiness preview for future Chat browser dispatch."""

    vault = Path(vault_root).resolve()
    normalized_message = _norm(message)
    router = build_phase11_chat_router_contract(
        vault,
        message=normalized_message,
        explicit_intent=explicit_intent or "browser-task",
    )
    intent = str((router.get("intent_result") or {}).get("intent_class") or "browser-task")
    input_posture = router.get("input_posture") or {}
    action_spec = router.get("action_spec") or {}
    ambiguity = action_spec.get("ambiguity") or {}
    policy_gate = _policy_gate_report(router, surface=SURFACE_ID)
    external = _external_readiness(vault)
    target = _target_selection(normalized_message, requested_target)
    action = _action_selection(normalized_message, requested_action)

    blockers: list[str] = []
    if not normalized_message:
        blockers.append("message_required_for_browser_dispatch_readiness")
    if intent not in BROWSER_BOUND_INTENTS:
        blockers.append("intent_not_browser_bound_for_dispatch")
    if input_posture.get("prompt_injection_suspected"):
        blockers.append("prompt_injection_indicator_present")
    if policy_gate["denied_action_classes"]:
        blockers.append("denied_side_effect_prompt_present")
        blockers.append("policy_gate_denied_side_effect_request")
    if ambiguity.get("requires_operator_clarification"):
        blockers.append("ambiguous_command_requires_operator_clarification")
        blockers.append("policy_gate_ambiguous_command")
    if not target.get("known_target"):
        blockers.append("requested_or_selected_browser_target_not_registered")
    if not action.get("action_supported_by_contract"):
        blockers.append("selected_browser_action_not_supported_by_contract")

    browser_use_ready = bool(external.get("browser_use_branch_ready"))
    excalidraw_ready = bool(external.get("excalidraw_branch_ready"))
    selected_target = str(target.get("selected_target") or "")
    readiness_satisfied = (
        browser_use_ready if selected_target == "browser-use-cli" else excalidraw_ready if selected_target == "excalidraw" else False
    )
    if not readiness_satisfied:
        blockers.append("selected_browser_runtime_branch_not_ready")
        blockers.extend(f"external_runtime:{item}" for item in external.get("blockers", [])[:8])

    blockers.extend(
        [
            "operator_browser_dispatch_approval_missing",
            "chat_browser_dispatch_executor_not_built",
            "browser_launch_blocked_by_readonly_contract",
            "browser_navigation_blocked_by_readonly_contract",
            "screenshot_capture_blocked_by_readonly_contract",
        ]
    )

    preview_ready = (
        bool(normalized_message)
        and intent in BROWSER_BOUND_INTENTS
        and not input_posture.get("prompt_injection_suspected")
        and not policy_gate["denied_action_classes"]
        and not ambiguity.get("requires_operator_clarification")
        and bool(target.get("known_target"))
        and bool(action.get("action_supported_by_contract"))
    )
    material = {
        "pass": PASS_ID,
        "message_sha256": _sha256_text(normalized_message),
        "intent_class": intent,
        "selected_target": target.get("selected_target"),
        "selected_browser_action": action.get("selected_browser_action"),
        "approval_class": APPROVAL_CLASS,
        "external_runtime_status": external.get("status"),
        "router_model_version": router.get("model_version"),
    }
    digest = _sha256_text(_canonical_json(material))
    packet_id = f"chat-browser-dispatch-{digest[:20]}"
    lower_phase_dispatch_lane_manifest = build_chat_studio_browser_runtime_dispatch_lane_manifest(
        vault,
        target_url="http://127.0.0.1:4173",
        runtime="Hermes",
        requested_by_surface="StudioChat",
    )

    hard_blockers = {
        "message_required_for_browser_dispatch_readiness",
        "intent_not_browser_bound_for_dispatch",
        "prompt_injection_indicator_present",
        "denied_side_effect_prompt_present",
        "policy_gate_denied_side_effect_request",
        "ambiguous_command_requires_operator_clarification",
        "policy_gate_ambiguous_command",
        "requested_or_selected_browser_target_not_registered",
        "selected_browser_action_not_supported_by_contract",
    }

    return {
        "ok": not any(blocker in hard_blockers for blocker in blockers),
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
            "browser_bound_intent": intent in BROWSER_BOUND_INTENTS,
            "dispatch_preview_ready": preview_ready,
            "dispatch_preconditions_met": False,
            "selected_target": target.get("selected_target"),
            "selected_browser_action": action.get("selected_browser_action"),
            "browser_use_branch_ready": browser_use_ready,
            "excalidraw_branch_ready": excalidraw_ready,
            "approval_request_created": False,
            "browser_launch_started": False,
            "browser_navigation_started": False,
            "screenshot_captured": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "blocker_count": len(list(dict.fromkeys(blockers))),
        },
        "router_contract": router,
        "policy_gate_report": policy_gate,
        "target_selection": target,
        "action_selection": action,
        "external_runtime_readiness": external,
        "lower_phase_browser_runtime_dispatch_lane": lower_phase_dispatch_lane_manifest,
        "request_digest_proof": {
            "request_digest": digest,
            "prompt_message_sha256": _sha256_text(normalized_message),
            "digest_material": material,
            "digest_required_for_future_browser_dispatch_approval": True,
        },
        "future_browser_dispatch_packet_preview": {
            "visible": True,
            "dispatch_packet_id_preview": packet_id,
            "approval_id_preview": f"chat-browser-dispatch-appr-{digest[:20]}",
            "approval_artifact_path_preview": f"runtime/studio/approvals/chat-browser-dispatch-appr-{digest[:20]}.json",
            "browser_run_artifact_path_preview": f"07_LOGS/Browser-Runs/{packet_id}.json",
            "approval_request_created": False,
            "approval_queue_writer_called": False,
            "browser_use_cli_invoked": False,
            "browser_process_started": False,
            "cdp_connection_opened": False,
            "mcp_invoked": False,
            "target_navigation_started": False,
            "screenshot_captured": False,
            "agent_bus_task_created": False,
            "required_approval_class": APPROVAL_CLASS,
            "dispatch_allowed_after_preview": False,
            "browser_packet_preview": {
                "sender": "StudioChat",
                "target": target.get("selected_target"),
                "browser_action": action.get("selected_browser_action"),
                "request": normalized_message[:1200],
                "execution_constraints": {
                    "allow_real_profile": False,
                    "allow_credentials": False,
                    "allow_cookies": False,
                    "allow_public_tunnel": False,
                    "allowed_write_paths": [],
                },
            },
        },
        "preflight_checks": {
            "message_present": bool(normalized_message),
            "intent_is_browser_bound": intent in BROWSER_BOUND_INTENTS,
            "prompt_injection_absent": not bool(input_posture.get("prompt_injection_suspected")),
            "selected_target_registered": bool(target.get("known_target")),
            "selected_action_supported": bool(action.get("action_supported_by_contract")),
            "selected_browser_runtime_branch_ready": readiness_satisfied,
            "approval_packet_written": False,
            "browser_started": False,
            "navigation_started": False,
            "screenshot_written": False,
        },
        "authority": {
            "read_only": True,
            "approval_gated": True,
            "dispatch_preview_allowed": True,
            "approval_queue_write_allowed": False,
            "approval_execution_allowed": False,
            "browser_dispatch_allowed": False,
            "browser_control_allowed": False,
            "browser_launch_allowed": False,
            "browser_navigation_allowed": False,
            "screenshot_capture_allowed": False,
            "browser_use_cli_allowed": False,
            "cdp_connection_allowed": False,
            "mcp_invocation_allowed": False,
            "real_profile_access_allowed": False,
            "credential_or_cookie_access_allowed": False,
            "provider_calls_allowed": False,
            "agent_bus_task_write_allowed": False,
            "target_vault_write_allowed": False,
            "gate_mutation_allowed": False,
            "git_mutation_allowed": False,
            "host_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "denied_by_this_surface": [
            "approval_artifact_write",
            "approval_execution",
            "browser_dispatch",
            "browser_launch",
            "browser_navigation",
            "browser_use_cli_invocation",
            "cdp_connection",
            "mcp_invocation",
            "screenshot_capture",
            "real_profile_access",
            "credential_or_cookie_access",
            "provider_api_call",
            "agent_bus_task_write",
            "target_vault_file_write",
            "gate_mutation",
            "git_mutation",
            "host_mutation",
            "canonical_writeback",
        ],
        "blocked_reasons": list(dict.fromkeys(blockers)),
        "warnings": [],
    }


def format_phase11_chat_browser_dispatch_readiness(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    digest = payload.get("request_digest_proof") or {}
    preview = payload.get("future_browser_dispatch_packet_preview") or {}
    return "\n".join(
        [
            "Phase 11 Chat Browser Dispatch Readiness Contract",
            f"  status: {payload.get('status')}",
            f"  intent: {summary.get('intent_class')}",
            f"  selected_target: {summary.get('selected_target')}",
            f"  selected_browser_action: {summary.get('selected_browser_action')}",
            f"  request_digest: {digest.get('request_digest')}",
            f"  dispatch_packet_id_preview: {preview.get('dispatch_packet_id_preview')}",
            f"  approval_request_created: {summary.get('approval_request_created')}",
            f"  browser_launch_started: {summary.get('browser_launch_started')}",
            f"  screenshot_captured: {summary.get('screenshot_captured')}",
            f"  next: {summary.get('next_recommended_pass')}",
            "  Boundary: read-only readiness only; no approval artifact, browser launch, navigation, screenshot, Browser Use/CDP/MCP call, Agent Bus task, or canonical mutation.",
        ]
    )
