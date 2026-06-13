"""Phase 11 operator-governed executor/deferred closeout handoff.

This surface is the read-only stop sign after the no-HITL lane completion
audit. It does not choose or execute a live lane; it records that any remaining
executor, provider, runtime, browser, target-mutation, Agent Bus, or canonical
writeback work requires explicit operator selection or formal deferral.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from runtime.studio.phase11_no_hitl_lane_completion_audit import (
    build_phase11_no_hitl_lane_completion_audit,
)


MODEL_VERSION = "studio.phase11_operator_governed_executor_deferred_closeout.v1"
SURFACE_ID = "phase11_operator_governed_executor_deferred_closeout"
PASS_ID = "operator-selected-governed-executor-or-deferred-closeout"
STATUS = "COMPLETE / READ-ONLY / VERIFIED / OPERATOR HANDOFF READY"
NEXT_OPERATOR_ACTION = "operator-select-governed-executor-or-defer-closeout"
NEXT_RECOMMENDED_PASS = "operator-action-required-no-autonomous-phase11-pass"
DEFAULT_EVIDENCE_ROOT = (
    Path("07_LOGS")
    / "Studio-Graph-Views"
    / "phase11-operator-handoff"
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _safe_slug(value: str | None) -> str:
    raw = value or datetime.now(timezone.utc).strftime(
        "%Y-%m-%d-phase11-operator-governed-executor-deferred-closeout"
    )
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", raw.strip()).strip(".-")
    return slug or "phase11-operator-governed-executor-deferred-closeout"


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
            "Phase 11 operator-governed closeout evidence root must stay inside the vault workspace"
        ) from exc
    return root


def _authority() -> dict[str, Any]:
    return {
        "read_only": True,
        "operator_handoff_only": True,
        "evidence_write_allowed": True,
        "implementation_authority_granted": False,
        "operator_selection_recorded": False,
        "deferred_closeout_selected": False,
        "command_execution_allowed": False,
        "approval_queue_write_allowed": False,
        "approval_consumption_allowed": False,
        "approval_execution_allowed": False,
        "approval_action_allowed": False,
        "approval_status_mutation_allowed": False,
        "exact_once_marker_write_allowed": False,
        "provider_calls_allowed": False,
        "model_calls_allowed": False,
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


def _authority_bounded(authority: dict[str, Any]) -> bool:
    return all(
        authority.get(key) is False
        for key in [
            "implementation_authority_granted",
            "operator_selection_recorded",
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
            "conversation_persistence_allowed",
            "vault_writes_allowed",
            "agent_bus_task_write_allowed",
            "canonical_mutation_allowed",
        ]
    )


def _operator_lanes(completion: dict[str, Any]) -> list[dict[str, Any]]:
    lanes: list[dict[str, Any]] = []
    for lane in completion.get("deferred_lanes") or []:
        lane_id = str(lane.get("lane_id") or "")
        lanes.append(
            {
                "lane_id": lane_id,
                "title": lane.get("title"),
                "requires_operator_selection": True,
                "eligible_for_autonomous_execution": False,
                "selected_now": False,
                "implementation_authority_granted": False,
                "approval_consumption_required": bool(lane.get("requires_approval_consumption")),
                "provider_or_external_call_required": bool(lane.get("requires_provider_or_external_call")),
                "runtime_dispatch_required": bool(lane.get("requires_runtime_dispatch")),
                "browser_control_required": bool(lane.get("requires_browser_control")),
                "target_mutation_required": bool(lane.get("requires_target_mutation")),
                "deferred_reason": lane.get("deferred_reason"),
                "operator_instruction": "Select this lane only through an explicit governed approval/executor pass.",
            }
        )
    return lanes


def _handoff_checklist(
    *,
    completion: dict[str, Any],
    operator_lanes: list[dict[str, Any]],
    authority_bounded: bool,
) -> list[dict[str, Any]]:
    completion_summary = completion.get("summary") or {}
    no_hitl_complete = completion_summary.get("no_hitl_lane_complete") is True
    no_autonomous_remaining = int(completion_summary.get("eligible_no_hitl_remaining_count") or 0) == 0
    lanes_governed = bool(operator_lanes) and all(
        lane.get("requires_operator_selection") is True
        and lane.get("eligible_for_autonomous_execution") is False
        for lane in operator_lanes
    )
    return [
        {
            "id": "no_hitl_lane_completion_verified",
            "satisfied": no_hitl_complete,
            "evidence": "No-HITL lane completion audit returned complete.",
        },
        {
            "id": "no_autonomous_phase11_passes_remaining",
            "satisfied": no_autonomous_remaining,
            "evidence": "Eligible no-HITL remaining count is zero.",
        },
        {
            "id": "operator_selection_required_before_executor_work",
            "satisfied": lanes_governed,
            "evidence": "Remaining executor/live/target lanes are marked operator-selected only.",
        },
        {
            "id": "deferred_closeout_path_available",
            "satisfied": True,
            "evidence": "Operator may defer closeout instead of selecting an executor lane.",
        },
        {
            "id": "handoff_is_read_only",
            "satisfied": authority_bounded,
            "evidence": "Handoff grants no execution, approval consumption, dispatch, or mutation authority.",
        },
    ]


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
                "# Phase 11 Operator-Governed Executor / Deferred Closeout",
                "",
                f"- Status: {report.get('status')}",
                f"- Pass: {report.get('pass')}",
                f"- No-HITL lane complete: {summary.get('no_hitl_lane_complete')}",
                f"- Substantial no-HITL passes remaining: {summary.get('substantial_no_hitl_passes_remaining')}",
                f"- Operator selection required: {summary.get('operator_selection_required')}",
                f"- Operator-governed remaining lanes: {summary.get('operator_governed_remaining_lane_count')}",
                f"- Next operator action: {summary.get('next_operator_action')}",
                "",
                "Boundary: operator handoff only; no command execution, approval consumption/execution, provider/model call, runtime/browser dispatch, Agent Bus task write, target mutation, or canonical writeback.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return evidence


def build_phase11_operator_governed_executor_deferred_closeout(
    vault_root: str | Path,
    *,
    write_evidence: bool = False,
    evidence_root: str | Path | None = None,
    evidence_slug: str | None = None,
) -> dict[str, Any]:
    """Build the read-only operator-governed executor/deferred closeout handoff."""

    vault = _vault_path(vault_root)
    completion = build_phase11_no_hitl_lane_completion_audit(vault)
    completion_summary = completion.get("summary") or {}
    operator_lanes = _operator_lanes(completion)
    authority = _authority()
    bounded = _authority_bounded(authority)
    checklist = _handoff_checklist(
        completion=completion,
        operator_lanes=operator_lanes,
        authority_bounded=bounded,
    )
    handoff_ready = completion.get("ok") is True and all(
        item.get("satisfied") is True for item in checklist
    )

    report: dict[str, Any] = {
        "ok": handoff_ready,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "summary": {
            "handoff_ready": handoff_ready,
            "no_hitl_lane_complete": completion_summary.get("no_hitl_lane_complete") is True,
            "substantial_no_hitl_passes_remaining": 0,
            "substantial_handoff_passes_remaining": 0,
            "operator_governed_remaining_lane_count": len(operator_lanes),
            "retired_lane_count": len(completion.get("retired_lanes") or []),
            "operator_selection_required": True,
            "deferred_closeout_available": True,
            "implementation_authority_granted": False,
            "operator_selection_recorded": False,
            "next_operator_action": NEXT_OPERATOR_ACTION,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
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
        "handoff_result": {
            "status": "AWAITING_OPERATOR_SELECTION / NO_AUTONOMOUS_PHASE11_PASS_REMAINS",
            "next_operator_action": NEXT_OPERATOR_ACTION,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "operator_decision_required": True,
        },
        "no_hitl_completion_summary": completion_summary,
        "operator_governed_lanes": operator_lanes,
        "retired_lanes": completion.get("retired_lanes") or [],
        "handoff_checklist": checklist,
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
            "red-first backend operator handoff tests",
            "QA runner static no-write proof",
            "CLI preview and log-only evidence write proof",
            "CLI command contract/generated docs check",
            "truth docs state zero autonomous no-HITL passes remain",
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


def format_phase11_operator_governed_executor_deferred_closeout(model: dict[str, Any]) -> str:
    summary = model.get("summary") or {}
    authority = model.get("authority") or {}
    lines = [
        "Phase 11 Operator-Governed Executor / Deferred Closeout",
        f"  status: {model.get('status')}",
        f"  pass: {model.get('pass')}",
        f"  handoff_ready: {summary.get('handoff_ready')}",
        f"  substantial_no_hitl_passes_remaining: {summary.get('substantial_no_hitl_passes_remaining')}",
        f"  operator_selection_required: {summary.get('operator_selection_required')}",
        f"  operator_governed_remaining_lanes: {summary.get('operator_governed_remaining_lane_count')}",
        f"  next_operator_action: {summary.get('next_operator_action')}",
        f"  provider_calls_allowed: {authority.get('provider_calls_allowed')}",
        f"  runtime_dispatch_allowed: {authority.get('runtime_dispatch_allowed')}",
        f"  browser_control_allowed: {authority.get('browser_control_allowed')}",
        "  Boundary: operator handoff only; no command execution, approval consumption/execution, provider/model call, runtime/browser dispatch, Agent Bus task write, target mutation, or canonical mutation.",
    ]
    evidence = model.get("evidence") or {}
    if evidence.get("written"):
        lines.append(f"  evidence: {evidence.get('markdown_path')}")
    return "\n".join(lines)
