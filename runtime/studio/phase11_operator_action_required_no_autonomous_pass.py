"""Phase 11 operator-action-required no-autonomous-pass gate.

This is the explicit read-only stop after the operator-governed handoff. It
does not select an executor lane, defer closeout on the operator's behalf, or
grant implementation authority. It only records that a human/operator decision
is the next required action.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from runtime.studio.phase11_operator_governed_executor_deferred_closeout import (
    build_phase11_operator_governed_executor_deferred_closeout,
)


MODEL_VERSION = "studio.phase11_operator_action_required_no_autonomous_pass.v1"
SURFACE_ID = "phase11_operator_action_required_no_autonomous_pass"
PASS_ID = "operator-action-required-no-autonomous-phase11-pass"
STATUS = "COMPLETE / READ-ONLY / VERIFIED / OPERATOR DECISION REQUIRED"
NEXT_RECOMMENDED_ACTION = "operator-select-governed-executor-lane-or-defer-closeout"
DEFAULT_EVIDENCE_ROOT = (
    Path("07_LOGS")
    / "Studio-Graph-Views"
    / "phase11-operator-action-required"
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _safe_slug(value: str | None) -> str:
    raw = value or datetime.now(timezone.utc).strftime(
        "%Y-%m-%d-phase11-operator-action-required-no-autonomous-pass"
    )
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", raw.strip()).strip(".-")
    return slug or "phase11-operator-action-required-no-autonomous-pass"


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
            "Phase 11 operator action evidence root must stay inside the vault workspace"
        ) from exc
    return root


def _authority() -> dict[str, Any]:
    return {
        "read_only": True,
        "operator_decision_gate_only": True,
        "evidence_write_allowed": True,
        "operator_selection_recorded": False,
        "deferred_closeout_selected": False,
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
            "operator_selection_recorded",
            "deferred_closeout_selected",
            "implementation_authority_granted",
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


def _available_decisions() -> list[dict[str, Any]]:
    return [
        {
            "decision_id": "select_governed_executor_lane",
            "title": "Select Governed Executor Lane",
            "selected_now": False,
            "implementation_authority_granted": False,
            "requires_explicit_operator_input": True,
            "effect_if_selected_later": "A separate bounded executor pass may be opened for one named lane only.",
        },
        {
            "decision_id": "defer_phase11_closeout",
            "title": "Defer Phase 11 Closeout",
            "selected_now": False,
            "implementation_authority_granted": False,
            "requires_explicit_operator_input": True,
            "effect_if_selected_later": "Phase 11 remains closed at the current read-only boundary.",
        },
    ]


def _decision_checklist(
    *,
    handoff: dict[str, Any],
    authority_bounded: bool,
    decisions: list[dict[str, Any]],
    lanes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    summary = handoff.get("summary") or {}
    no_lane_selected = all(item.get("selected_now") is False for item in decisions + lanes)
    lanes_governed = bool(lanes) and all(
        item.get("requires_operator_selection") is True
        and item.get("implementation_authority_granted") is False
        for item in lanes
    )
    return [
        {
            "id": "handoff_ready",
            "satisfied": handoff.get("ok") is True and summary.get("handoff_ready") is True,
            "evidence": "Operator-governed closeout handoff is complete.",
        },
        {
            "id": "zero_autonomous_phase11_passes_remaining",
            "satisfied": int(summary.get("substantial_no_hitl_passes_remaining") or 0) == 0
            and int(summary.get("substantial_handoff_passes_remaining") or 0) == 0,
            "evidence": "No substantial autonomous Phase 11 passes remain.",
        },
        {
            "id": "operator_decision_required",
            "satisfied": bool(decisions) and lanes_governed,
            "evidence": "Remaining lanes require explicit operator selection or deferral.",
        },
        {
            "id": "no_lane_selected_implicitly",
            "satisfied": no_lane_selected,
            "evidence": "This gate did not choose an executor lane or closeout deferral.",
        },
        {
            "id": "authority_bounded",
            "satisfied": authority_bounded,
            "evidence": "Decision gate grants no execution, approval, dispatch, write, or mutation authority.",
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
                "# Phase 11 Operator Action Required / No Autonomous Phase 11 Pass",
                "",
                f"- Status: {report.get('status')}",
                f"- Pass: {report.get('pass')}",
                f"- Decision gate ready: {summary.get('decision_gate_ready')}",
                f"- Autonomous Phase 11 passes remaining: {summary.get('autonomous_phase11_passes_remaining')}",
                f"- Operator decision required: {summary.get('operator_decision_required')}",
                f"- Selected lane: {summary.get('selected_lane_id')}",
                f"- Next recommended action: {summary.get('next_recommended_action')}",
                "",
                "Boundary: decision gate only; no executor lane selected, no approval consumption/execution, no provider/model call, no runtime/browser dispatch, no Agent Bus task write, no target mutation, and no canonical writeback.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return evidence


def build_phase11_operator_action_required_no_autonomous_pass(
    vault_root: str | Path,
    *,
    write_evidence: bool = False,
    evidence_root: str | Path | None = None,
    evidence_slug: str | None = None,
) -> dict[str, Any]:
    """Build the read-only operator decision gate after autonomous Phase 11 closure."""

    vault = _vault_path(vault_root)
    handoff = build_phase11_operator_governed_executor_deferred_closeout(vault)
    handoff_summary = handoff.get("summary") or {}
    lanes = handoff.get("operator_governed_lanes") or []
    decisions = _available_decisions()
    authority = _authority()
    bounded = _authority_bounded(authority)
    checklist = _decision_checklist(
        handoff=handoff,
        authority_bounded=bounded,
        decisions=decisions,
        lanes=lanes,
    )
    ready = all(item.get("satisfied") is True for item in checklist)

    report: dict[str, Any] = {
        "ok": ready,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "summary": {
            "decision_gate_ready": ready,
            "handoff_ready": handoff_summary.get("handoff_ready") is True,
            "autonomous_phase11_passes_remaining": 0,
            "substantial_no_hitl_passes_remaining": 0,
            "substantial_handoff_passes_remaining": 0,
            "operator_decision_required": True,
            "available_decision_count": len(decisions),
            "operator_governed_remaining_lane_count": len(lanes),
            "selected_lane_id": None,
            "deferred_closeout_selected": False,
            "operator_selection_recorded": False,
            "implementation_authority_granted": False,
            "next_recommended_action": NEXT_RECOMMENDED_ACTION,
            "writes_allowed_now": False,
            "live_execution_allowed_now": False,
            "approval_consumption_performed": False,
            "approval_execution_performed": False,
            "provider_call_performed": False,
            "model_call_performed": False,
            "runtime_dispatch_performed": False,
            "browser_action_performed": False,
            "target_mutation_performed": False,
            "agent_bus_task_written": False,
            "canonical_mutation_performed": False,
        },
        "decision_result": {
            "status": "OPERATOR_DECISION_REQUIRED / NO_AUTONOMOUS_PHASE11_PASS_REMAINS",
            "operator_decision_required": True,
            "next_recommended_action": NEXT_RECOMMENDED_ACTION,
            "selected_lane_id": None,
        },
        "available_decisions": decisions,
        "operator_governed_lanes": lanes,
        "decision_checklist": checklist,
        "source_handoff_summary": handoff_summary,
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
        "evidence": {
            "written": False,
            "json_path": None,
            "markdown_path": None,
        },
        "next_recommended_pass": NEXT_RECOMMENDED_ACTION,
    }

    if write_evidence:
        _write_evidence(
            vault=vault,
            report=report,
            evidence_root=evidence_root,
            evidence_slug=evidence_slug,
        )
    return report


def format_phase11_operator_action_required_no_autonomous_pass(model: dict[str, Any]) -> str:
    summary = model.get("summary") or {}
    authority = model.get("authority") or {}
    lines = [
        "Phase 11 Operator Action Required / No Autonomous Phase 11 Pass",
        f"  status: {model.get('status')}",
        f"  pass: {model.get('pass')}",
        f"  decision_gate_ready: {summary.get('decision_gate_ready')}",
        f"  autonomous_phase11_passes_remaining: {summary.get('autonomous_phase11_passes_remaining')}",
        f"  operator_decision_required: {summary.get('operator_decision_required')}",
        f"  selected_lane_id: {summary.get('selected_lane_id')}",
        f"  next_recommended_action: {summary.get('next_recommended_action')}",
        f"  provider_calls_allowed: {authority.get('provider_calls_allowed')}",
        f"  runtime_dispatch_allowed: {authority.get('runtime_dispatch_allowed')}",
        f"  browser_control_allowed: {authority.get('browser_control_allowed')}",
        "  Boundary: decision gate only; no executor lane selected, approval consumption/execution, provider/model call, runtime/browser dispatch, Agent Bus task write, target mutation, or canonical mutation.",
    ]
    evidence = model.get("evidence") or {}
    if evidence.get("written"):
        lines.append(f"  evidence: {evidence.get('markdown_path')}")
    return "\n".join(lines)
