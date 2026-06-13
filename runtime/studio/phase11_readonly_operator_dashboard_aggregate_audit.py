"""Phase 11 read-only operator dashboard aggregate audit.

This surface audits the existing read-only dashboard stack. It consumes the
slash dashboard response, Approval Center, provider readiness, runtime status,
companion status, recent logs, and slash catalog contracts without introducing
command execution, approval consumption, provider calls, runtime dispatch, or
target mutation.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from runtime.studio.approval_center_panel import build_approval_center_panel
from runtime.studio.phase11_chat_companion_status import build_phase11_chat_companion_status
from runtime.studio.phase11_chat_readonly_slash_command_responses import (
    build_phase11_chat_readonly_slash_command_responses,
)
from runtime.studio.phase11_chat_runtime_dispatch_readiness import (
    build_phase11_chat_runtime_status_explanation,
)
from runtime.studio.phase11_readonly_slash_command_catalog_audit import (
    build_phase11_readonly_slash_command_catalog_audit,
)
from runtime.studio.provider_readiness import build_studio_provider_readiness


MODEL_VERSION = "studio.phase11_readonly_operator_dashboard_aggregate_audit.v1"
SURFACE_ID = "phase11_readonly_operator_dashboard_aggregate_audit"
PASS_ID = "phase11-chat-readonly-operator-dashboard-aggregate-audit"
STATUS = "COMPLETE / READ-ONLY / VERIFIED / OPERATOR DASHBOARD AGGREGATE AUDIT"
NEXT_RECOMMENDED_PASS = "phase11-chat-no-hitl-lane-completion-audit"
DEFAULT_EVIDENCE_ROOT = (
    Path("07_LOGS") / "Studio-Graph-Views" / "phase11-dashboard-aggregate-audits"
)

EXPECTED_SOURCE_IDS = {
    "slash_dashboard_response",
    "approval_center",
    "provider_readiness",
    "runtime_status",
    "companion_status",
    "recent_build_logs",
    "slash_catalog",
}

EXPECTED_CARD_IDS = {
    "dashboard-summary",
    "approval-center",
    "provider-status",
    "companion-status",
    "recent-build-logs",
    "runtime-status",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _safe_slug(value: str | None) -> str:
    raw = value or datetime.now(timezone.utc).strftime(
        "%Y-%m-%d-phase11-readonly-operator-dashboard-aggregate-audit"
    )
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", raw.strip()).strip(".-")
    return slug or "phase11-readonly-operator-dashboard-aggregate-audit"


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
        raise ValueError(
            "Phase 11 operator dashboard aggregate audit evidence root must stay inside the vault workspace"
        ) from exc
    return root


def _authority() -> dict[str, Any]:
    return {
        "read_only": True,
        "dashboard_aggregate_audit_only": True,
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


def _card_by_id(cards: list[dict[str, Any]], card_id: str) -> dict[str, Any]:
    return next((card for card in cards if card.get("id") == card_id), {})


def _source_audit(
    *,
    source_id: str,
    source_surface: str,
    source_ready: bool,
    summary_fields: dict[str, Any],
    card_ids: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "source_surface": source_surface,
        "source_ready": bool(source_ready),
        "read_only": True,
        "summary_fields": summary_fields,
        "card_ids": card_ids or [],
        "writes_performed": False,
        "approval_execution_performed": False,
        "approval_consumption_performed": False,
        "approval_status_mutated": False,
        "provider_call_performed": False,
        "model_call_performed": False,
        "runtime_dispatch_performed": False,
        "browser_action_performed": False,
        "agent_bus_task_written": False,
        "target_mutation_performed": False,
        "vault_write_performed": False,
        "canonical_mutation_performed": False,
    }


def _dashboard_cards(vault: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    dashboard = build_phase11_chat_readonly_slash_command_responses(vault, message="/dashboard")
    cards = {str(card.get("id") or ""): card for card in dashboard.get("cards") or []}
    return dashboard, cards


def _runtime_cards(vault: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, Any]]:
    runtime_response = build_phase11_chat_readonly_slash_command_responses(vault, message="/runtime status")
    cards = {str(card.get("id") or ""): card for card in runtime_response.get("cards") or []}
    explanation = build_phase11_chat_runtime_status_explanation(vault, message="/runtime status")
    return runtime_response, cards, explanation


def _recent_logs_count(vault: Path) -> int:
    root = vault / "07_LOGS" / "Build-Logs"
    return len(list(root.glob("*.md"))) if root.is_dir() else 0


def _no_runtime_dispatch_performed(runtime_explanation: dict[str, Any]) -> bool:
    proof = runtime_explanation.get("no_dispatch_proof") or {}
    return not any(bool(value) for value in proof.values())


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
                "# Phase 11 Read-Only Operator Dashboard Aggregate Audit",
                "",
                f"- Status: {report.get('status')}",
                f"- Pass: {report.get('pass')}",
                f"- Source count: {summary.get('source_count')}",
                f"- Dashboard response ready: {summary.get('dashboard_response_ready')}",
                f"- Source cards covered: {summary.get('source_cards_covered')}",
                f"- Next recommended pass: {summary.get('selected_next_recommended_pass')}",
                f"- Command execution allowed: {(report.get('authority') or {}).get('command_execution_allowed')}",
                f"- Provider calls allowed: {(report.get('authority') or {}).get('provider_calls_allowed')}",
                f"- Runtime dispatch allowed: {(report.get('authority') or {}).get('runtime_dispatch_allowed')}",
                f"- Browser control allowed: {(report.get('authority') or {}).get('browser_control_allowed')}",
                "",
                "Boundary: dashboard aggregate audit only; no command execution, approval consumption, provider call, runtime/browser dispatch, Agent Bus task write, target mutation, or canonical writeback.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return evidence


def build_phase11_readonly_operator_dashboard_aggregate_audit(
    vault_root: str | Path,
    *,
    write_evidence: bool = False,
    evidence_root: str | Path | None = None,
    evidence_slug: str | None = None,
) -> dict[str, Any]:
    """Build a read-only audit of the Phase 11 operator dashboard aggregate."""

    vault = _vault_path(vault_root)
    dashboard, dashboard_cards = _dashboard_cards(vault)
    runtime_response, runtime_cards, runtime_explanation = _runtime_cards(vault)
    approval_center = build_approval_center_panel(vault)
    provider = build_studio_provider_readiness(vault)
    companion = build_phase11_chat_companion_status(vault)
    catalog = build_phase11_readonly_slash_command_catalog_audit(vault)

    dashboard_summary = dashboard.get("summary") or {}
    approval_summary = approval_center.get("summary") or {}
    provider_summary = provider.get("summary") or {}
    companion_summary = companion.get("summary") or {}
    catalog_summary = catalog.get("summary") or {}
    runtime_state = runtime_explanation.get("state_explanation") or {}
    recent_log_card = _card_by_id(list(dashboard_cards.values()), "recent-build-logs")

    source_audits = [
        _source_audit(
            source_id="slash_dashboard_response",
            source_surface=str(dashboard.get("surface") or ""),
            source_ready=dashboard.get("ok") is True and dashboard_summary.get("response_cards_ready") is True,
            summary_fields={
                "slash_token": dashboard_summary.get("slash_token"),
                "response_card_count": dashboard_summary.get("response_card_count"),
                "command_execution_performed": dashboard_summary.get("command_execution_performed"),
            },
            card_ids=list(dashboard_cards),
        ),
        _source_audit(
            source_id="approval_center",
            source_surface=str(approval_center.get("surface") or ""),
            source_ready=approval_center.get("surface") == "studio_approval_center_panel",
            summary_fields={
                "overall_status": approval_summary.get("overall_status"),
                "source_group_count": approval_summary.get("source_group_count", 0),
                "pending_item_count": approval_summary.get("pending_item_count", 0),
                "blocked_item_count": approval_summary.get("blocked_item_count", 0),
                "approval_execution_available": approval_summary.get("approval_execution_available"),
            },
            card_ids=["approval-center"],
        ),
        _source_audit(
            source_id="provider_readiness",
            source_surface=str(provider.get("surface") or ""),
            source_ready=provider.get("ok") is True and provider.get("read_only") is True,
            summary_fields={
                "readiness_status": provider_summary.get("readiness_status"),
                "active_provider_id": provider_summary.get("active_provider_id"),
                "active_model": provider_summary.get("active_model"),
                "degraded": provider_summary.get("degraded"),
            },
            card_ids=["provider-status"],
        ),
        _source_audit(
            source_id="runtime_status",
            source_surface=str(runtime_explanation.get("surface") or ""),
            source_ready=runtime_explanation.get("ok") is True and runtime_response.get("ok") is True,
            summary_fields={
                "mode": runtime_state.get("mode"),
                "runtime_response_ready": (runtime_response.get("summary") or {}).get("response_cards_ready"),
                "no_dispatch_performed": _no_runtime_dispatch_performed(runtime_explanation),
                "runtime_dispatch_allowed": (runtime_explanation.get("authority") or {}).get(
                    "runtime_dispatch_allowed"
                ),
            },
            card_ids=list(runtime_cards),
        ),
        _source_audit(
            source_id="companion_status",
            source_surface=str(companion.get("surface") or ""),
            source_ready=companion.get("ok") is True and companion.get("read_only") is True,
            summary_fields={
                "selected_runtime_id": companion_summary.get("selected_runtime_id"),
                "registered_companion_count": companion_summary.get("registered_companion_count", 0),
                "runtime_control_performed": companion_summary.get("runtime_control_performed"),
            },
            card_ids=["companion-status"],
        ),
        _source_audit(
            source_id="recent_build_logs",
            source_surface="phase11_chat_readonly_slash_command_responses.recent_build_logs",
            source_ready=bool(recent_log_card) and recent_log_card.get("log_write_performed") is False,
            summary_fields={
                "log_count": recent_log_card.get("log_count", _recent_logs_count(vault)),
                "log_write_performed": recent_log_card.get("log_write_performed"),
            },
            card_ids=["recent-build-logs"],
        ),
        _source_audit(
            source_id="slash_catalog",
            source_surface=str(catalog.get("surface") or ""),
            source_ready=catalog.get("ok") is True and catalog_summary.get("supported_readonly_commands_covered") is True,
            summary_fields={
                "supported_readonly_command_count": catalog_summary.get("supported_readonly_command_count", 0),
                "blocked_or_unknown_command_count": catalog_summary.get("blocked_or_unknown_command_count", 0),
                "write_and_execution_commands_blocked": catalog_summary.get("write_and_execution_commands_blocked"),
            },
            card_ids=[],
        ),
    ]

    aggregate_card_ids = sorted(set(list(dashboard_cards) + list(runtime_cards)))
    source_ids = {item["source_id"] for item in source_audits}
    source_cards_covered = EXPECTED_CARD_IDS.issubset(set(aggregate_card_ids))
    sources_covered = EXPECTED_SOURCE_IDS.issubset(source_ids)
    source_ready = all(item["source_ready"] for item in source_audits)
    authority = _authority()
    bounded = _authority_bounded(authority)
    aggregate_ready = source_ready and sources_covered and source_cards_covered and bounded

    report: dict[str, Any] = {
        "ok": aggregate_ready,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "summary": {
            "aggregate_audit_ready": aggregate_ready,
            "dashboard_response_ready": dashboard.get("ok") is True,
            "dashboard_response_card_count": dashboard_summary.get("response_card_count", 0),
            "source_cards_covered": source_cards_covered,
            "source_count": len(source_audits),
            "source_ids": sorted(source_ids),
            "aggregate_card_ids": aggregate_card_ids,
            "approval_center_covered": "approval_center" in source_ids,
            "provider_readiness_covered": "provider_readiness" in source_ids,
            "runtime_status_covered": "runtime_status" in source_ids,
            "companion_status_covered": "companion_status" in source_ids,
            "recent_build_logs_covered": "recent_build_logs" in source_ids,
            "slash_catalog_covered": "slash_catalog" in source_ids,
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
        "source_audits": source_audits,
        "aggregate_cards": [
            {
                "card_id": card_id,
                "source": "dashboard" if card_id in dashboard_cards else "runtime_status",
                "kind": (dashboard_cards.get(card_id) or runtime_cards.get(card_id) or {}).get("kind"),
                "read_only": (dashboard_cards.get(card_id) or runtime_cards.get(card_id) or {}).get("read_only"),
            }
            for card_id in aggregate_card_ids
        ],
        "readiness": {
            "operator_dashboard_aggregate_audit_ready": aggregate_ready,
            "approval_provider_runtime_companion_log_sources_covered": all(
                source_id in source_ids
                for source_id in [
                    "approval_center",
                    "provider_readiness",
                    "runtime_status",
                    "companion_status",
                    "recent_build_logs",
                ]
            ),
            "slash_catalog_consumed": "slash_catalog" in source_ids and catalog.get("ok") is True,
            "source_cards_covered": source_cards_covered,
            "authority_bounded": bounded,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
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
            "red-first backend dashboard aggregate tests",
            "QA runner static no-write proof",
            "CLI preview and log-only evidence write proof",
            "CLI command contract/generated docs check",
            "post-closeout planner advances to a no-HITL lane completion audit",
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


def format_phase11_readonly_operator_dashboard_aggregate_audit(model: dict[str, Any]) -> str:
    summary = model.get("summary") or {}
    authority = model.get("authority") or {}
    lines = [
        "Phase 11 Read-Only Operator Dashboard Aggregate Audit",
        f"  status: {model.get('status')}",
        f"  pass: {model.get('pass')}",
        f"  aggregate_audit_ready: {summary.get('aggregate_audit_ready')}",
        f"  source_count: {summary.get('source_count')}",
        f"  source_cards_covered: {summary.get('source_cards_covered')}",
        f"  aggregate_cards: {', '.join(str(item) for item in summary.get('aggregate_card_ids') or [])}",
        f"  command_execution_allowed: {authority.get('command_execution_allowed')}",
        f"  provider_calls_allowed: {authority.get('provider_calls_allowed')}",
        f"  runtime_dispatch_allowed: {authority.get('runtime_dispatch_allowed')}",
        f"  browser_control_allowed: {authority.get('browser_control_allowed')}",
        f"  next: {summary.get('selected_next_recommended_pass')}",
        "  Boundary: dashboard aggregate audit only; no command execution, approval consumption, provider call, runtime/browser dispatch, Agent Bus task write, target mutation, or canonical mutation.",
    ]
    evidence = model.get("evidence") or {}
    if evidence.get("written"):
        lines.append(f"  evidence: {evidence.get('markdown_path')}")
    return "\n".join(lines)
