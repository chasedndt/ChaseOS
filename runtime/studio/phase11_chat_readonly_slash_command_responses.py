"""Phase 11 Chat read-only slash command response cards.

This surface turns safe slash commands into bounded response cards for the Chat
panel. It deliberately stays below the execution line: no approval action,
runtime dispatch, browser control, provider/model call, Agent Bus task write,
conversation persistence, vault write, or canonical mutation is performed.
"""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any

from runtime.studio.approval_center_panel import build_approval_center_panel
from runtime.studio.graph_view_contract import build_graph_view_contract
from runtime.studio.phase11_chat_companion_status import build_phase11_chat_companion_status
from runtime.studio.phase11_chat_router_contract import SLASH_INTENT_MAP, build_phase11_chat_router_contract
from runtime.studio.phase11_chat_runtime_dispatch_readiness import build_phase11_chat_runtime_status_explanation
from runtime.studio.provider_readiness import build_studio_provider_readiness


MODEL_VERSION = "studio.phase11_chat_readonly_slash_command_responses.v1"
SURFACE_ID = "phase11_chat_readonly_slash_command_responses"
PASS_ID = "phase11-chat-readonly-slash-command-responses"
STATUS = "COMPLETE / READ-ONLY / VERIFIED / NO COMMAND EXECUTION"
NEXT_RECOMMENDED_PASS = "phase11-chat-readonly-card-visual-qa"

READ_ONLY_TOKENS = {
    "/dashboard",
    "/map",
    "/vault",
    "/runtime",
    "/models",
    "/provider",
    "/log",
    "/pet",
}
WRITE_OR_EXECUTION_TOKENS = {
    "/run",
    "/agent",
    "/browser",
    "/schedule",
    "/approve",
    "/reject",
    "/new-project",
    "/new-node",
    "/handoff",
    "/archive",
    "/rnd",
    "/companion",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(value: str | None) -> str:
    return " ".join(str(value or "").strip().split())


def _parse_slash(message: str) -> dict[str, str]:
    if not message.startswith("/"):
        return {"slash_token": "", "subcommand": "", "query": ""}
    parts = message.split()
    token = parts[0].lower() if parts else ""
    args = parts[1:]
    subcommand = ""
    query = " ".join(args).strip()
    if token in {"/runtime", "/memory"} and args:
        subcommand = args[0].lower()
        query = " ".join(args[1:]).strip()
    return {"slash_token": token, "subcommand": subcommand, "query": query}


def _authority() -> dict[str, Any]:
    return {
        "read_only": True,
        "slash_response_preview_allowed": True,
        "command_execution_allowed": False,
        "approval_action_allowed": False,
        "approval_execution_allowed": False,
        "approval_status_mutation_allowed": False,
        "approval_artifact_write_allowed": False,
        "runtime_control_allowed": False,
        "runtime_dispatch_allowed": False,
        "browser_control_allowed": False,
        "browser_launch_allowed": False,
        "provider_calls_allowed": False,
        "model_calls_allowed": False,
        "provider_switch_allowed": False,
        "vault_writes_allowed": False,
        "conversation_persistence_allowed": False,
        "graph_index_write_allowed": False,
        "node_id_write_allowed": False,
        "profile_write_allowed": False,
        "role_card_mutation_allowed": False,
        "identity_ledger_mutation_allowed": False,
        "agent_bus_task_write_allowed": False,
        "schedule_mutation_allowed": False,
        "credential_values_visible": False,
        "canonical_mutation_allowed": False,
    }


def _is_supported_readonly_command(token: str, subcommand: str) -> bool:
    if token == "/runtime":
        return subcommand in {"", "status"}
    if token == "/memory":
        return subcommand == "show"
    return token in READ_ONLY_TOKENS


def _blocked_command_reason(token: str, subcommand: str) -> str:
    if token == "/memory" and subcommand != "show":
        return "slash_command_requires_approval_or_executor"
    if token in WRITE_OR_EXECUTION_TOKENS:
        return "slash_command_requires_approval_or_executor"
    return "slash_command_not_supported_by_readonly_response_surface"


def _command_surface_explainer() -> dict[str, Any]:
    """Explain where Studio Chat command shortcuts come from and where CLI fits.

    This is user-facing product metadata, not runtime authority. Keeping it in the
    backend payload lets downloaded GitHub builds render the same explanation
    without relying on private docs or the current operator's local setup.
    """

    return {
        "surface_id": "studio_chat_slash_command_surface",
        "defined_inside_chaseos": True,
        "source_modules": [
            "runtime.studio.phase11_chat_router_contract",
            "runtime.studio.phase11_chat_readonly_slash_command_responses",
            "runtime.hermes.studio_chat_capabilities",
            "runtime.cli.main",
        ],
        "chat_surface_role": "friendly Studio Chat shortcut and preview surface",
        "terminal_cli_role": "operator-facing terminal command surface for explicit ChaseOS commands",
        "embedded_buttons_available": True,
        "typing_required_for_common_previews": False,
        "terminal_cli_recommended": True,
        "terminal_cli_boundary": "operator-facing command surface, not a Studio Chat provider bypass",
        "slash_commands_execute_shell": False,
        "slash_commands_consume_approvals": False,
        "slash_commands_dispatch_runtimes": False,
        "slash_commands_write_agent_bus_tasks": False,
        "approval_effects_require": [
            "approval packet",
            "exact-once approval consumption marker",
            "runtime-owned executor or AOR workflow",
            "Agent Bus/audit result",
        ],
        "operator_guidance": (
            "Use buttons for common read-only Chat previews; use terminal CLI for explicit operator commands; "
            "use governed approval/executor paths for real effects."
        ),
    }


def _slash_command_catalog() -> dict[str, Any]:
    """Return the Studio Chat slash-command autocomplete catalog.

    This catalog is deliberately an autofill/read-only UX model. It documents
    supported preview commands and blocked action-envelope commands without
    granting execution, runtime dispatch, Agent Bus writes, vault writes, or
    approval consumption.
    """

    specs = [
        ("/dashboard", "Dashboard", "Open the read-only operator dashboard cards.", "read-only", "dashboard", False),
        ("/runtime status", "Runtime status", "Show runtime/daemon readiness and companion status without dispatch.", "read-only", "runtime", False),
        ("/models", "Models", "Show provider/model readiness without calling a provider.", "read-only", "providers", False),
        ("/provider", "Provider readiness", "Show provider readiness and blocked provider-call posture.", "read-only", "providers", False),
        ("/map", "Vault map", "Preview bounded vault graph/map context without writing graph indexes.", "read-only", "vault", False),
        ("/vault", "Vault search", "Preview bounded vault context for a query without writing files.", "read-only", "vault", False),
        ("/log", "Latest logs", "Show recent log/build activity context without mutating logs.", "read-only", "logs", False),
        ("/memory show", "Memory show", "Show memory/readiness context without saving hidden memory.", "read-only", "memory", False),
        ("/pet hermes", "Companion", "Show Hermes companion/runtime profile context without profile mutation.", "read-only", "runtime", False),
        ("/approve", "Approval preview", "Preview the approval path; Chat does not approve or consume approvals.", "action-envelope-preview", "approval", True),
        ("/reject", "Rejection preview", "Preview rejection requirements; Chat does not mutate approval status.", "action-envelope-preview", "approval", True),
        ("/shell", "Shell preview", "Explain required shell executor/approval; Chat never runs shell commands.", "action-envelope-preview", "execution", True),
        ("/run", "Runtime task preview", "Preview runtime task dispatch requirements without creating Agent Bus tasks.", "action-envelope-preview", "runtime", True),
        ("/agent", "Agent task preview", "Preview agent-task handoff requirements without runtime dispatch.", "action-envelope-preview", "runtime", True),
        ("/browser", "Browser preview", "Preview browser executor requirements without launching a browser.", "action-envelope-preview", "browser", True),
        ("/schedule", "Schedule preview", "Preview schedule intent/activation requirements without mutating schedules.", "action-envelope-preview", "schedule", True),
        ("/promote", "Promotion preview", "Preview Gate/canonical promotion requirements without canonical mutation.", "action-envelope-preview", "canonical", True),
        ("/send", "External send preview", "Preview external-send approval requirements without sending anything.", "action-envelope-preview", "external", True),
        ("/handoff", "Handoff preview", "Preview handoff packet requirements without writing runtime boards.", "action-envelope-preview", "runtime", True),
        ("/capabilities", "Capabilities", "Show local Chat/runtime capability posture when the runtime capability layer is available.", "read-only", "runtime", False),
        ("/readiness", "Readiness", "Show runtime readiness posture when the runtime capability layer is available.", "read-only", "runtime", False),
        ("/authority", "Authority", "Show authority/blocked-action catalog without expanding permissions.", "read-only", "governance", False),
    ]
    commands = []
    for message, label, description, kind, category, requires_executor in specs:
        commands.append(
            {
                "message": message,
                "label": label,
                "description": description,
                "kind": kind,
                "category": category,
                "preview_only": True,
                "autofill_only": True,
                "requires_approval_or_executor": requires_executor,
                "command_execution_allowed": False,
                "approval_consumed": False,
                "runtime_dispatch_allowed": False,
                "agent_bus_task_write_allowed": False,
                "vault_write_allowed": False,
                "canonical_mutation_allowed": False,
            }
        )
    return {
        "surface_id": "studio_chat_slash_command_autocomplete",
        "trigger": "/",
        "visible_when_input_starts_with": "/",
        "keyboard_navigation": ["ArrowDown", "ArrowUp", "Enter", "Tab", "Escape"],
        "autofill_only": True,
        "preview_only": True,
        "command_execution_allowed": False,
        "approval_consumed": False,
        "runtime_dispatch_allowed": False,
        "agent_bus_task_write_allowed": False,
        "vault_write_allowed": False,
        "canonical_mutation_allowed": False,
        "operator_text": "Typing / opens read-only slash command suggestions. Arrow keys scroll; Enter/Tab/click autofills the composer.",
        "commands": commands,
    }


def _embedded_action_envelopes() -> list[dict[str, Any]]:
    """Return safe Chat UI button envelopes for slash-command previews.

    These are not executors. They are product-shell affordances that populate the
    Chat composer with the same read-only slash messages an operator could type.
    The backend keeps the authority metadata beside the labels so downloaded
    GitHub builds render buttons without accidentally adding execution rights.
    """

    specs = [
        ("chat-action-dashboard", "Dashboard", "/dashboard", "chat-readonly-slash-response", "operator-dashboard"),
        ("chat-action-runtime-status", "Runtime status", "/runtime status", "chat-readonly-slash-response", "runtime-status"),
        ("chat-action-approval-center", "Approval center", "/dashboard", "approval-center", "approval-center"),
        ("chat-action-models", "Models", "/models", "chat-readonly-slash-response", "provider-status"),
        ("chat-action-map", "Map", "/map", "chat-readonly-slash-response", "map-summary"),
        ("chat-action-memory-show", "Memory show", "/memory show", "chat-readonly-slash-response", "memory-summary"),
        ("chat-action-pet", "Companion", "/pet hermes", "chat-readonly-slash-response", "companion-status"),
    ]
    return [
        {
            "id": action_id,
            "kind": "chat_readonly_action_envelope",
            "label": label,
            "message": message,
            "target_surface": target_surface,
            "target_card": target_card,
            "button_text": "Run read-only preview",
            "preview_only": True,
            "read_only": True,
            "command_execution_allowed": False,
            "approval_consumed": False,
            "approval_execution_allowed": False,
            "runtime_dispatch_allowed": False,
            "browser_control_allowed": False,
            "provider_call_allowed": False,
            "vault_write_allowed": False,
            "agent_bus_task_write_allowed": False,
            "canonical_mutation_allowed": False,
            "operator_text": "Populates Studio Chat with a read-only slash preview; it does not approve, dispatch, write, or call a provider.",
        }
        for action_id, label, message, target_surface, target_card in specs
    ]


def _help_card(*, known: bool, blocked: bool, token: str) -> dict[str, Any]:
    return {
        "id": "slash-command-boundary" if blocked else "slash-command-help",
        "kind": "slash_help",
        "slash_token": token,
        "known_command": known,
        "read_only": True,
        "operator_text": (
            "That slash command needs an approval or executor surface before it can do anything."
            if blocked
            else "This read-only surface supports /dashboard, /map, /vault, /runtime status, /models, /provider, /log, /memory show, and /pet."
        ),
        "safe_commands": [
            "/dashboard",
            "/map [query]",
            "/vault [query]",
            "/runtime status",
            "/models",
            "/provider",
            "/log",
            "/memory show",
            "/pet [runtime]",
        ],
        "execution_performed": False,
    }


def _dashboard_card(approval_center: dict[str, Any], provider: dict[str, Any]) -> dict[str, Any]:
    approval_summary = approval_center.get("summary") or {}
    provider_summary = provider.get("summary") or {}
    return {
        "id": "dashboard-summary",
        "kind": "operator_dashboard",
        "read_only": True,
        "overall_status": approval_summary.get("overall_status"),
        "pending_approval_count": approval_summary.get("pending_item_count", 0),
        "blocked_approval_count": approval_summary.get("blocked_item_count", 0),
        "provider_readiness_status": provider_summary.get("readiness_status"),
        "provider_degraded": provider_summary.get("degraded"),
        "approval_execution_allowed": False,
        "provider_call_performed": False,
        "vault_write_performed": False,
    }


def _approval_center_card(approval_center: dict[str, Any]) -> dict[str, Any]:
    summary = approval_center.get("summary") or {}
    return {
        "id": "approval-center",
        "kind": "approval_center",
        "read_only": True,
        "overall_status": summary.get("overall_status"),
        "total_item_count": summary.get("total_item_count", 0),
        "pending_item_count": summary.get("pending_item_count", 0),
        "blocked_item_count": summary.get("blocked_item_count", 0),
        "approval_execution_allowed": False,
        "operator_decision_controls_present": False,
    }


def _companion_card(companion_status: dict[str, Any]) -> dict[str, Any]:
    selected = companion_status.get("selected_companion") or {}
    summary = companion_status.get("summary") or {}
    return {
        "id": "companion-status",
        "kind": "companion_status",
        "read_only": True,
        "selected_runtime_id": summary.get("selected_runtime_id"),
        "registered_companion_count": summary.get("registered_companion_count", 0),
        "display_name": selected.get("display_name"),
        "runtime_profile_path": selected.get("runtime_profile_path", ""),
        "authority_ceiling": selected.get("authority_ceiling"),
        "runtime_control_allowed": False,
        "runtime_dispatch_allowed": False,
        "profile_write_allowed": False,
        "identity_ledger_mutation_allowed": False,
    }


def _runtime_status_card(vault: Path, message: str) -> dict[str, Any]:
    status = build_phase11_chat_runtime_status_explanation(
        vault,
        message=message or "/runtime status",
        explicit_intent="runtime-task",
    )
    state = status.get("state_explanation") or {}
    no_dispatch = status.get("no_dispatch_proof") or {}
    cockpit = status.get("runtime_cockpit_alignment") or {}
    return {
        "id": "runtime-status",
        "kind": "runtime_status",
        "read_only": True,
        "mode": state.get("mode"),
        "operator_text": state.get("operator_text"),
        "runtime_cockpit_alignment": cockpit.get("shares_runtime_cockpit_wording"),
        "runtime_dispatch_allowed": False,
        "agent_bus_task_created": bool(no_dispatch.get("agent_bus_task_created")),
        "workflow_dispatched": bool(no_dispatch.get("workflow_dispatched")),
        "approval_consumed": False,
    }


def _map_card(vault: Path, query: str, *, max_nodes: int) -> dict[str, Any]:
    """Return a bounded read-only map summary without invoking broad graph scans.

    The slash-command QA path must stay fast on Windows-backed WSL vaults. The
    full graph contract remains available to graph-specific surfaces; this Chat
    card only needs a small operator-facing preview and no-write proof.
    """

    query_text = (query or "").strip().lower()
    limit = max(1, min(int(max_nodes or 1), 24))
    visible_nodes: list[str] = []
    stack = [vault]
    skipped_roots = {".git", ".pytest_tmp_env", "node_modules", "07_LOGS/Studio-Graph-Views"}

    while stack and len(visible_nodes) < limit:
        current = stack.pop()
        rel_current = current.relative_to(vault).as_posix() if current != vault else ""
        if rel_current in skipped_roots:
            continue
        try:
            entries = sorted(os.scandir(current), key=lambda entry: entry.name)
        except OSError:
            continue
        directories: list[Path] = []
        for entry in entries:
            try:
                if entry.is_dir(follow_symlinks=False):
                    child_dir = Path(entry.path)
                    rel_dir = child_dir.relative_to(vault).as_posix()
                    if rel_dir not in skipped_roots and not entry.name.startswith("."):
                        directories.append(child_dir)
                    continue
                if not entry.is_file(follow_symlinks=False):
                    continue
            except OSError:
                continue
            child = Path(entry.path)
            if child.suffix.lower() != ".md":
                continue
            rel = child.relative_to(vault).as_posix()
            if query_text and query_text not in rel.lower():
                continue
            visible_nodes.append(rel)
            if len(visible_nodes) >= limit:
                break
        stack.extend(reversed(directories))

    return {
        "id": "map-summary",
        "kind": "vault_map",
        "read_only": True,
        "query": query,
        "visible_node_count": len(visible_nodes),
        "visible_edge_count": 0,
        "source_node_count": len(visible_nodes),
        "source_edge_count": 0,
        "visible_nodes": visible_nodes,
        "graph_view_ready": True,
        "warnings": ["bounded_chat_map_preview"],
        "blockers": [],
        "graph_index_write_performed": False,
        "node_id_write_performed": False,
        "vault_write_performed": False,
    }


def _provider_card(provider: dict[str, Any]) -> dict[str, Any]:
    summary = provider.get("summary") or {}
    credential = provider.get("credential_posture") or {}
    return {
        "id": "provider-status",
        "kind": "provider_status",
        "read_only": True,
        "readiness_status": summary.get("readiness_status"),
        "active_provider_id": summary.get("active_provider_id"),
        "active_model": summary.get("active_model"),
        "fallback_provider_id": summary.get("fallback_provider_id"),
        "fallback_model": summary.get("fallback_model"),
        "credential_values_visible": False,
        "primary_provider_env_present": credential.get("primary_provider_env_present"),
        "provider_call_performed": False,
        "provider_switch_allowed": False,
    }


def _log_card(vault: Path) -> dict[str, Any]:
    root = vault / "07_LOGS" / "Build-Logs"
    files = sorted(root.glob("*.md"), key=lambda path: path.name, reverse=True)[:5] if root.is_dir() else []
    return {
        "id": "recent-build-logs",
        "kind": "build_logs",
        "read_only": True,
        "log_count": len(files),
        "latest_logs": [path.relative_to(vault).as_posix() for path in files],
        "log_write_performed": False,
    }


def _memory_card(vault: Path) -> dict[str, Any]:
    profile_count = len(list((vault / "06_AGENTS").glob("*-Runtime-Profile.md"))) if (vault / "06_AGENTS").is_dir() else 0
    return {
        "id": "memory-summary",
        "kind": "memory_show",
        "read_only": True,
        "runtime_profile_count": profile_count,
        "memory_write_performed": False,
        "hidden_memory_write_performed": False,
        "canonical_mutation_performed": False,
    }


def _cards_for_command(vault: Path, token: str, subcommand: str, query: str, message: str, *, max_nodes: int) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    if token == "/dashboard":
        approval_center = build_approval_center_panel(vault)
        provider = build_studio_provider_readiness(vault)
        companion = build_phase11_chat_companion_status(vault)
        cards.extend(
            [
                _dashboard_card(approval_center, provider),
                _approval_center_card(approval_center),
                _provider_card(provider),
                _companion_card(companion),
                _log_card(vault),
            ]
        )
    elif token in {"/map", "/vault"}:
        cards.append(_map_card(vault, query, max_nodes=max_nodes))
    elif token == "/runtime":
        cards.append(_runtime_status_card(vault, message))
        cards.append(_companion_card(build_phase11_chat_companion_status(vault)))
    elif token in {"/models", "/provider"}:
        cards.append(_provider_card(build_studio_provider_readiness(vault)))
    elif token == "/log":
        cards.append(_log_card(vault))
    elif token == "/memory" and subcommand == "show":
        cards.append(_memory_card(vault))
    elif token == "/pet":
        requested = query or subcommand or None
        cards.append(_companion_card(build_phase11_chat_companion_status(vault, requested_runtime=requested)))
    return cards


def build_phase11_chat_readonly_slash_command_responses(
    vault_root: str | Path,
    *,
    message: str | None = None,
    max_nodes: int = 80,
) -> dict[str, Any]:
    """Build read-only response cards for safe Phase 11 Chat slash commands."""

    vault = Path(vault_root).resolve()
    normalized_message = _norm(message)
    parsed = _parse_slash(normalized_message)
    token = parsed["slash_token"]
    subcommand = parsed["subcommand"]
    query = parsed["query"]
    router = build_phase11_chat_router_contract(vault, message=normalized_message)
    input_posture = router.get("input_posture") or {}
    known = token in set(SLASH_INTENT_MAP)
    supported = _is_supported_readonly_command(token, subcommand) if known else False

    blockers: list[str] = []
    if not token:
        blockers.append("slash_command_required")
    elif not known:
        blockers.append("unknown_slash_command")
    elif not supported:
        blockers.append(_blocked_command_reason(token, subcommand))
    if input_posture.get("prompt_injection_suspected"):
        blockers.append("prompt_injection_indicator_present")
    if input_posture.get("denied_side_effect_prompt_present"):
        blockers.append("denied_side_effect_prompt_present")

    cards: list[dict[str, Any]] = []
    if supported and not blockers:
        bounded_max_nodes = max(1, min(int(max_nodes or 80), 200))
        cards = _cards_for_command(
            vault,
            token,
            subcommand,
            query,
            normalized_message,
            max_nodes=bounded_max_nodes,
        )

    help_card = None
    if blockers:
        help_card = _help_card(
            known=known,
            blocked=known and not supported,
            token=token,
        )

    selected_runtime_id = ""
    companion_card = next((card for card in cards if card.get("id") == "companion-status"), None)
    if companion_card:
        selected_runtime_id = str(companion_card.get("selected_runtime_id") or "")
    embedded_action_envelopes = _embedded_action_envelopes()
    command_surface_explainer = _command_surface_explainer()
    slash_command_catalog = _slash_command_catalog()

    readiness = {
        "readonly_slash_command_responses_ready": supported and not blockers and bool(cards),
        "read_only_command_allowlist_applied": True,
        "write_or_execution_commands_blocked": True,
        "unknown_commands_return_help_only": True,
        "prompt_injection_fails_closed": True,
        "embedded_action_envelopes_ready": bool(embedded_action_envelopes),
        "embedded_action_envelopes_preview_only": True,
        "embedded_action_envelopes_execute_nothing": True,
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }
    summary = {
        "slash_token": token,
        "subcommand": subcommand,
        "query": query,
        "slash_command_known": known,
        "slash_command_read_only_supported": supported,
        "response_cards_ready": supported and not blockers and bool(cards),
        "response_card_count": len(cards),
        "embedded_action_envelope_count": len(embedded_action_envelopes),
        "slash_command_catalog_count": len(slash_command_catalog.get("commands") or []),
        "selected_runtime_id": selected_runtime_id,
        "command_execution_performed": False,
        "approval_action_performed": False,
        "approval_execution_performed": False,
        "approval_status_mutated": False,
        "provider_call_performed": False,
        "model_call_performed": False,
        "runtime_dispatch_performed": False,
        "browser_action_performed": False,
        "vault_write_performed": False,
        "conversation_write_performed": False,
        "graph_index_write_performed": False,
        "node_id_write_performed": False,
        "agent_bus_task_written": False,
        "canonical_mutation_performed": False,
        "blocker_count": len(list(dict.fromkeys(blockers))),
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }

    return {
        "ok": supported and not blockers and bool(cards),
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "approval_gated": False,
        "summary": summary,
        "router_contract": router,
        "cards": cards,
        "help_card": help_card,
        "embedded_action_envelopes": embedded_action_envelopes,
        "command_surface_explainer": command_surface_explainer,
        "slash_command_catalog": slash_command_catalog,
        "authority": _authority(),
        "denied_by_this_surface": [
            "slash_command_execution",
            "approval_grant_or_reject",
            "approval_execution",
            "approval_status_mutation",
            "approval_artifact_write",
            "runtime_control",
            "runtime_dispatch",
            "browser_control",
            "provider_api_call",
            "model_output_generation",
            "provider_switch",
            "vault_file_write",
            "conversation_log_write",
            "graph_index_write",
            "node_id_write",
            "profile_write",
            "role_card_mutation",
            "identity_ledger_mutation",
            "agent_bus_task_write",
            "schedule_mutation",
            "credential_value_display",
            "canonical_writeback",
        ],
        "blocked_reasons": list(dict.fromkeys(blockers)),
        "readiness": readiness,
    }


def format_phase11_chat_readonly_slash_command_responses(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    authority = payload.get("authority") or {}
    lines = [
        "Phase 11 Chat Read-Only Slash Command Responses",
        f"  status: {payload.get('status')}",
        f"  slash_token: {summary.get('slash_token') or '(none)'}",
        f"  subcommand: {summary.get('subcommand') or '(none)'}",
        f"  known: {summary.get('slash_command_known')}",
        f"  read_only_supported: {summary.get('slash_command_read_only_supported')}",
        f"  response_cards_ready: {summary.get('response_cards_ready')}",
        f"  response_card_count: {summary.get('response_card_count')}",
        f"  runtime_dispatch_allowed: {authority.get('runtime_dispatch_allowed')}",
        f"  approval_execution_allowed: {authority.get('approval_execution_allowed')}",
        f"  vault_writes_allowed: {authority.get('vault_writes_allowed')}",
        f"  next: {summary.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append(f"  blockers: {', '.join(str(item) for item in blockers)}")
    lines.append(
        "  Boundary: read-only slash response cards only; no command execution, approval action, "
        "runtime dispatch, browser control, provider/model call, Agent Bus task write, vault write, or canonical mutation."
    )
    return "\n".join(lines)
