"""Phase 11 read-only slash command catalog audit.

This surface inventories the safe slash commands already handled by the
read-only response-card lane and proves write/execution commands still stop at
help or boundary cards. It writes optional log evidence only; it does not execute
commands, consume approvals, call providers, dispatch runtimes, or mutate target
state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from runtime.studio.phase11_chat_readonly_slash_command_responses import (
    build_phase11_chat_readonly_slash_command_responses,
)


MODEL_VERSION = "studio.phase11_readonly_slash_command_catalog_audit.v1"
SURFACE_ID = "phase11_readonly_slash_command_catalog_audit"
PASS_ID = "phase11-chat-readonly-slash-command-catalog-audit"
STATUS = "COMPLETE / READ-ONLY / VERIFIED / SLASH COMMAND CATALOG AUDIT"
NEXT_RECOMMENDED_PASS = "phase11-chat-readonly-operator-dashboard-aggregate-audit"
DEFAULT_EVIDENCE_ROOT = (
    Path("07_LOGS") / "Studio-Graph-Views" / "phase11-readonly-slash-command-catalog-audits"
)

SUPPORTED_READONLY_COMMAND_CATALOG = [
    {
        "command": "/dashboard",
        "message": "/dashboard",
        "feature_family": "Operator Dashboard + Configuration",
        "expected_card_ids": ["dashboard-summary", "approval-center", "provider-status", "companion-status"],
    },
    {
        "command": "/map",
        "message": "/map README",
        "feature_family": "Slash Commands",
        "expected_card_ids": ["map-summary"],
    },
    {
        "command": "/vault",
        "message": "/vault README",
        "feature_family": "Slash Commands",
        "expected_card_ids": ["map-summary"],
    },
    {
        "command": "/runtime status",
        "message": "/runtime status",
        "feature_family": "Runtime Control Surface",
        "expected_card_ids": ["runtime-status", "companion-status"],
    },
    {
        "command": "/models",
        "message": "/models",
        "feature_family": "Multi-Model Provider Router",
        "expected_card_ids": ["provider-status"],
    },
    {
        "command": "/provider",
        "message": "/provider",
        "feature_family": "Multi-Model Provider Router",
        "expected_card_ids": ["provider-status"],
    },
    {
        "command": "/log",
        "message": "/log",
        "feature_family": "Operator Dashboard + Configuration",
        "expected_card_ids": ["recent-build-logs"],
    },
    {
        "command": "/memory show",
        "message": "/memory show",
        "feature_family": "Memory Save/Search",
        "expected_card_ids": ["memory-summary"],
    },
    {
        "command": "/pet",
        "message": "/pet hermes",
        "feature_family": "Agent Companion System",
        "expected_card_ids": ["companion-status"],
    },
]

BLOCKED_OR_UNKNOWN_COMMAND_CATALOG = [
    {
        "command": "/approve",
        "message": "/approve approval-123",
        "feature_family": "Slash Commands",
        "expected_help_card_id": "slash-command-boundary",
    },
    {
        "command": "/reject",
        "message": "/reject approval-123",
        "feature_family": "Slash Commands",
        "expected_help_card_id": "slash-command-boundary",
    },
    {
        "command": "/run",
        "message": "/run operator_today",
        "feature_family": "Runtime Control Surface",
        "expected_help_card_id": "slash-command-boundary",
    },
    {
        "command": "/browser",
        "message": "/browser open https://example.com",
        "feature_family": "Browser-Use Integration",
        "expected_help_card_id": "slash-command-boundary",
    },
    {
        "command": "/memory save",
        "message": "/memory save remember this context",
        "feature_family": "Memory Save/Search",
        "expected_help_card_id": "slash-command-boundary",
    },
    {
        "command": "/rnd",
        "message": "/rnd create feature idea",
        "feature_family": "R&D Entry System",
        "expected_help_card_id": "slash-command-boundary",
    },
    {
        "command": "/new-project",
        "message": "/new-project Project Alpha",
        "feature_family": "Autogenesis Engine",
        "expected_help_card_id": "slash-command-boundary",
    },
    {
        "command": "/unknown",
        "message": "/dance now",
        "feature_family": "Slash Commands",
        "expected_help_card_id": "slash-command-help",
    },
]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _safe_slug(value: str | None) -> str:
    raw = value or datetime.now(timezone.utc).strftime(
        "%Y-%m-%d-phase11-readonly-slash-command-catalog-audit"
    )
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", raw.strip()).strip(".-")
    return slug or "phase11-readonly-slash-command-catalog-audit"


def _relative_to_vault(vault: Path, path: str | Path | None) -> str | None:
    if path is None:
        return None
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = vault / resolved
    try:
        return resolved.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _resolve_evidence_dir(vault: Path, evidence_root: str | Path | None) -> Path:
    root_input = Path(evidence_root) if evidence_root else DEFAULT_EVIDENCE_ROOT
    root = root_input if root_input.is_absolute() else vault / root_input
    root = root.resolve()
    try:
        root.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError("Phase 11 slash command catalog audit evidence root must stay inside the vault workspace") from exc
    return root


def _authority() -> dict[str, Any]:
    return {
        "read_only": True,
        "catalog_audit_only": True,
        "evidence_write_allowed": True,
        "implementation_authority_granted": False,
        "command_execution_allowed": False,
        "approval_queue_write_allowed": False,
        "approval_consumption_allowed": False,
        "approval_execution_allowed": False,
        "approval_action_allowed": False,
        "approval_status_mutation_allowed": False,
        "exact_once_marker_write_allowed": False,
        "provider_calls_allowed": False,
        "model_calls_allowed": False,
        "provider_switch_allowed": False,
        "runtime_control_allowed": False,
        "runtime_dispatch_allowed": False,
        "browser_control_allowed": False,
        "browser_launch_allowed": False,
        "target_mutation_allowed": False,
        "conversation_persistence_allowed": False,
        "vault_writes_allowed": False,
        "graph_index_write_allowed": False,
        "node_id_write_allowed": False,
        "agent_bus_task_write_allowed": False,
        "schedule_mutation_allowed": False,
        "gate_policy_mutation_allowed": False,
        "workflow_execution_allowed": False,
        "host_mutation_allowed": False,
        "credential_values_visible": False,
        "canonical_mutation_allowed": False,
    }


def _side_effect_free(summary: dict[str, Any]) -> bool:
    return not any(
        bool(summary.get(key))
        for key in [
            "command_execution_performed",
            "approval_action_performed",
            "approval_execution_performed",
            "approval_status_mutated",
            "provider_call_performed",
            "model_call_performed",
            "runtime_dispatch_performed",
            "browser_action_performed",
            "vault_write_performed",
            "conversation_write_performed",
            "graph_index_write_performed",
            "node_id_write_performed",
            "agent_bus_task_written",
            "canonical_mutation_performed",
        ]
    )


def _catalog_item_from_response(
    *,
    vault: Path,
    spec: dict[str, Any],
    max_nodes: int,
    expected_supported: bool,
) -> dict[str, Any]:
    response = build_phase11_chat_readonly_slash_command_responses(
        vault,
        message=str(spec["message"]),
        max_nodes=max_nodes,
    )
    summary = response.get("summary") or {}
    cards = response.get("cards") or []
    card_ids = [str(card.get("id") or "") for card in cards]
    expected_card_ids = [str(item) for item in spec.get("expected_card_ids") or []]
    help_card = response.get("help_card") or {}
    router_contract = response.get("router_contract") or {}
    intent = (router_contract.get("intent_result") or {}).get("intent_class")
    missing_expected_card_ids = [item for item in expected_card_ids if item not in card_ids]

    item = {
        "command": spec["command"],
        "message": spec["message"],
        "feature_family": spec["feature_family"],
        "slash_token": summary.get("slash_token"),
        "subcommand": summary.get("subcommand"),
        "query": summary.get("query"),
        "router_intent": intent,
        "slash_command_known": summary.get("slash_command_known"),
        "slash_command_read_only_supported": summary.get("slash_command_read_only_supported"),
        "response_surface_ok": response.get("ok") is True,
        "read_only_response_ready": summary.get("response_cards_ready") is True,
        "response_card_count": int(summary.get("response_card_count") or 0),
        "response_card_ids": card_ids,
        "expected_card_ids": expected_card_ids,
        "missing_expected_card_ids": missing_expected_card_ids,
        "help_card_id": help_card.get("id"),
        "blocked_reasons": list(response.get("blocked_reasons") or []),
        "command_execution_performed": bool(summary.get("command_execution_performed")),
        "approval_action_performed": bool(summary.get("approval_action_performed")),
        "approval_execution_performed": bool(summary.get("approval_execution_performed")),
        "approval_status_mutated": bool(summary.get("approval_status_mutated")),
        "provider_call_performed": bool(summary.get("provider_call_performed")),
        "model_call_performed": bool(summary.get("model_call_performed")),
        "runtime_dispatch_performed": bool(summary.get("runtime_dispatch_performed")),
        "browser_action_performed": bool(summary.get("browser_action_performed")),
        "vault_write_performed": bool(summary.get("vault_write_performed")),
        "conversation_write_performed": bool(summary.get("conversation_write_performed")),
        "graph_index_write_performed": bool(summary.get("graph_index_write_performed")),
        "node_id_write_performed": bool(summary.get("node_id_write_performed")),
        "agent_bus_task_written": bool(summary.get("agent_bus_task_written")),
        "canonical_mutation_performed": bool(summary.get("canonical_mutation_performed")),
        "side_effect_free": _side_effect_free(summary),
    }
    if expected_supported:
        item["catalog_entry_ok"] = (
            item["response_surface_ok"]
            and item["read_only_response_ready"]
            and item["response_card_count"] >= 1
            and not missing_expected_card_ids
            and item["side_effect_free"]
        )
    else:
        item["expected_help_card_id"] = spec.get("expected_help_card_id")
        item["catalog_entry_ok"] = (
            not item["response_surface_ok"]
            and not item["read_only_response_ready"]
            and item["response_card_count"] == 0
            and item["help_card_id"] == spec.get("expected_help_card_id")
            and item["side_effect_free"]
        )
    return item


def _authority_bounded(authority: dict[str, Any]) -> bool:
    return all(
        authority.get(key) is False
        for key in [
            "command_execution_allowed",
            "approval_queue_write_allowed",
            "approval_consumption_allowed",
            "approval_execution_allowed",
            "approval_action_allowed",
            "approval_status_mutation_allowed",
            "exact_once_marker_write_allowed",
            "provider_calls_allowed",
            "model_calls_allowed",
            "runtime_dispatch_allowed",
            "browser_control_allowed",
            "browser_launch_allowed",
            "target_mutation_allowed",
            "vault_writes_allowed",
            "agent_bus_task_write_allowed",
            "canonical_mutation_allowed",
        ]
    )


def _write_evidence(
    *,
    vault: Path,
    report: dict[str, Any],
    evidence_root: str | Path | None,
    evidence_slug: str | None,
) -> dict[str, Any]:
    evidence_dir = _resolve_evidence_dir(vault, evidence_root)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    slug = _safe_slug(evidence_slug)
    json_path = evidence_dir / f"{slug}.json"
    markdown_path = evidence_dir / f"{slug}.md"
    evidence = {
        "written": True,
        "json_path": _relative_to_vault(vault, json_path),
        "markdown_path": _relative_to_vault(vault, markdown_path),
    }
    report["evidence"] = evidence
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    summary = report.get("summary") or {}
    markdown_path.write_text(
        "\n".join(
            [
                "# Phase 11 Read-Only Slash Command Catalog Audit",
                "",
                f"- Status: {report.get('status')}",
                f"- Pass: {report.get('pass')}",
                f"- Supported read-only commands: {summary.get('supported_readonly_command_count')}",
                f"- Blocked/unknown commands checked: {summary.get('blocked_or_unknown_command_count')}",
                f"- Supported commands covered: {summary.get('supported_readonly_commands_covered')}",
                f"- Write/execution commands blocked: {summary.get('write_and_execution_commands_blocked')}",
                f"- Next recommended pass: {summary.get('selected_next_recommended_pass')}",
                f"- Command execution allowed: {(report.get('authority') or {}).get('command_execution_allowed')}",
                f"- Provider calls allowed: {(report.get('authority') or {}).get('provider_calls_allowed')}",
                f"- Runtime dispatch allowed: {(report.get('authority') or {}).get('runtime_dispatch_allowed')}",
                f"- Browser control allowed: {(report.get('authority') or {}).get('browser_control_allowed')}",
                "",
                "Boundary: catalog audit only; no slash command execution, approval consumption, provider call, runtime/browser dispatch, Agent Bus task write, target mutation, or canonical writeback.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return evidence


def build_phase11_readonly_slash_command_catalog_audit(
    vault_root: str | Path,
    *,
    max_nodes: int = 80,
    write_evidence: bool = False,
    evidence_root: str | Path | None = None,
    evidence_slug: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic audit of safe and blocked Phase 11 slash commands."""

    vault = _vault_path(vault_root)
    bounded_max_nodes = max(1, min(int(max_nodes or 80), 200))
    supported = [
        _catalog_item_from_response(
            vault=vault,
            spec=spec,
            max_nodes=bounded_max_nodes,
            expected_supported=True,
        )
        for spec in SUPPORTED_READONLY_COMMAND_CATALOG
    ]
    blocked = [
        _catalog_item_from_response(
            vault=vault,
            spec=spec,
            max_nodes=bounded_max_nodes,
            expected_supported=False,
        )
        for spec in BLOCKED_OR_UNKNOWN_COMMAND_CATALOG
    ]
    authority = _authority()
    supported_ok = all(item["catalog_entry_ok"] for item in supported)
    blocked_ok = all(item["catalog_entry_ok"] for item in blocked)
    unknown_help_only = any(
        item["command"] == "/unknown"
        and item["help_card_id"] == "slash-command-help"
        and "unknown_slash_command" in item["blocked_reasons"]
        for item in blocked
    )
    bounded = _authority_bounded(authority)
    catalog_ready = supported_ok and blocked_ok and unknown_help_only and bounded
    report: dict[str, Any] = {
        "ok": catalog_ready,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "summary": {
            "catalog_audit_ready": catalog_ready,
            "supported_readonly_commands_covered": supported_ok,
            "write_and_execution_commands_blocked": blocked_ok,
            "unknown_commands_help_only": unknown_help_only,
            "supported_readonly_command_count": len(supported),
            "blocked_or_unknown_command_count": len(blocked),
            "catalog_entry_count": len(supported) + len(blocked),
            "no_human_in_loop_required": False,
            "can_continue_without_human_in_loop": True,
            "selected_next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "writes_allowed_now": False,
            "live_execution_allowed_now": False,
            "command_execution_performed": False,
            "approval_action_performed": False,
            "approval_consumption_performed": False,
            "approval_execution_performed": False,
            "provider_call_performed": False,
            "model_call_performed": False,
            "runtime_dispatch_performed": False,
            "browser_action_performed": False,
            "target_mutation_performed": False,
            "vault_write_performed": False,
            "agent_bus_task_written": False,
            "canonical_mutation_performed": False,
        },
        "supported_readonly_commands": supported,
        "blocked_or_unknown_commands": blocked,
        "authority": authority,
        "blocked_authority": [
            "slash_command_execution",
            "approval_queue_write",
            "approval_consumption",
            "approval_execution",
            "provider_or_model_call",
            "runtime_dispatch",
            "browser_control",
            "target_mutation",
            "agent_bus_task_write",
            "canonical_mutation",
        ],
        "verification_expectations": [
            "red-first backend catalog audit tests",
            "QA runner static no-write proof",
            "CLI preview and log-only evidence write proof",
            "CLI command contract/generated docs check",
            "post-closeout planner advances to the next read-only dashboard aggregate audit",
        ],
        "evidence": {
            "written": False,
            "json_path": None,
            "markdown_path": None,
        },
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }
    if write_evidence:
        _write_evidence(
            vault=vault,
            report=report,
            evidence_root=evidence_root,
            evidence_slug=evidence_slug,
        )
    return report


def format_phase11_readonly_slash_command_catalog_audit(model: dict[str, Any]) -> str:
    summary = model.get("summary") or {}
    authority = model.get("authority") or {}
    lines = [
        "Phase 11 Read-Only Slash Command Catalog Audit",
        f"  status: {model.get('status')}",
        f"  pass: {model.get('pass')}",
        f"  catalog_audit_ready: {summary.get('catalog_audit_ready')}",
        f"  supported_readonly_commands: {summary.get('supported_readonly_command_count')}",
        f"  blocked_or_unknown_commands: {summary.get('blocked_or_unknown_command_count')}",
        f"  supported_covered: {summary.get('supported_readonly_commands_covered')}",
        f"  write_execution_blocked: {summary.get('write_and_execution_commands_blocked')}",
        f"  command_execution_allowed: {authority.get('command_execution_allowed')}",
        f"  provider_calls_allowed: {authority.get('provider_calls_allowed')}",
        f"  runtime_dispatch_allowed: {authority.get('runtime_dispatch_allowed')}",
        f"  browser_control_allowed: {authority.get('browser_control_allowed')}",
        f"  next: {summary.get('selected_next_recommended_pass')}",
        "  Boundary: catalog audit only; no slash command execution, approval consumption, provider call, runtime/browser dispatch, Agent Bus task write, target mutation, or canonical mutation.",
    ]
    evidence = model.get("evidence") or {}
    if evidence.get("written"):
        lines.append(f"  evidence: {evidence.get('markdown_path')}")
    return "\n".join(lines)
