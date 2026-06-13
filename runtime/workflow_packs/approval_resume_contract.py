"""Read-only approval consumption and resume contract for Workflow Packs.

This module previews the approval-resume packet shape without granting approval
consumption or execution authority in this preview pass. The separate approved
local resume executor performs the bounded local mutation path after a scoped
review artifact and exact-once marker exist.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .models import ApprovalGate, WorkflowRun
from .store import WorkflowPackStore


MODEL_VERSION = "workflow_packs.approval_resume_contract.v1"
SURFACE_ID = "workflow_packs_approval_resume_contract"

BLOCKED_AUTHORITY: dict[str, bool] = {
    "approval_grant": False,
    "approval_status_mutation": False,
    "approval_decision_consumption": False,
    "resume_execution": False,
    "runtime_execution": False,
    "agent_bus_dispatch": False,
    "provider_calls": False,
    "browser_actions": False,
    "external_api_calls": False,
    "send_email": False,
    "publish_content": False,
    "agent_policy_change": False,
    "graph_or_canonical_promotion": False,
    "secret_or_credential_access": False,
}

REQUIRED_FUTURE_APPROVAL_FIELDS = [
    "record_type: workflow_pack_approval_resume_artifact",
    "model_version",
    "approval_packet_id",
    "request_digest",
    "run_id",
    "pack_id",
    "gate_id",
    "action_type",
    "approved_by",
    "approved_at",
    "approval_scope: one_workflow_pack_gate_only",
    "approval_decision_consumed: false",
]

NO_OP_BOUNDARIES = [
    "No approval gate status is changed by this contract preview.",
    "No approval decision is consumed by this contract preview.",
    "No Workflow Pack run is resumed by this contract preview.",
    "No runtime, Agent Bus, provider, browser, email, publish, graph, or policy action is executed.",
]


def build_approval_resume_contract(
    vault_root: str | Path,
    *,
    run_id: str = "",
    gate_id: str = "",
) -> dict[str, Any]:
    """Build a read-only future approval/resume contract for a Workflow Pack gate."""

    store = WorkflowPackStore(vault_root)
    requested_run_id = str(run_id or "").strip()
    requested_gate_id = str(gate_id or "").strip()
    runs = store.list_runs()

    if not requested_run_id:
        return _blocked_without_run(store, runs)

    try:
        run = store.get_run(requested_run_id)
    except FileNotFoundError:
        return _blocked_contract(
            store,
            status="blocked_run_not_found",
            blockers=[f"Workflow Pack run was not found: {requested_run_id}"],
            requested_run_id=requested_run_id,
            requested_gate_id=requested_gate_id,
            runs=runs,
        )

    gates = store.list_approval_gates(run.id)
    if not gates:
        return _contract_for_run_without_gates(store, run, requested_gate_id, runs)

    selected_gate = _select_gate(gates, requested_gate_id)
    if selected_gate is None:
        return _blocked_contract(
            store,
            status="blocked_gate_not_found",
            blockers=[f"Approval gate was not found for run {run.id}: {requested_gate_id}"],
            requested_run_id=run.id,
            requested_gate_id=requested_gate_id,
            runs=runs,
            run=run,
            gates=gates,
        )

    artifacts = [artifact.to_dict() for artifact in store.list_artifacts(run.id)]
    artifacts_by_id = {artifact["id"]: artifact for artifact in artifacts}
    selected_preview_artifacts = [
        artifacts_by_id[artifact_id]
        for artifact_id in selected_gate.preview_artifact_refs
        if artifact_id in artifacts_by_id
    ]
    gate_previews = [
        _gate_preview(gate, artifacts_by_id, selected=gate.id == selected_gate.id)
        for gate in gates
    ]

    blockers = _gate_blockers(selected_gate)
    packet_material = _packet_material(
        run=run,
        gate=selected_gate,
        artifacts=selected_preview_artifacts,
        blockers=blockers,
    )
    request_digest = _digest(packet_material)
    approval_packet_id = f"wfpr-{request_digest[:16]}"
    future_packet = {
        **packet_material,
        "approval_packet_id": approval_packet_id,
        "request_digest": request_digest,
        "status": "preview_only_not_consumable",
        "required_future_approval_fields": list(REQUIRED_FUTURE_APPROVAL_FIELDS),
        "exact_match_requirements": {
            "run_id": run.id,
            "pack_id": run.pack_id,
            "gate_id": selected_gate.id,
            "action_type": selected_gate.action_type,
            "request_digest": request_digest,
            "preview_artifact_refs": list(selected_gate.preview_artifact_refs),
            "approval_scope": "one_workflow_pack_gate_only",
            "approval_decision_consumed": False,
        },
        "future_resume_steps": [
            {"step": "operator_reviews_artifacts_and_gate", "effect_now": "preview_only"},
            {"step": "separate_review_pass_writes_scoped_approval_artifact", "effect_now": "not_written_here"},
            {"step": "marker_reservation_pass_writes_exact_once_marker", "effect_now": "not_written_here"},
            {"step": "approved_local_resume_executor_consumes_single_gate", "effect_now": "blocked_here"},
        ],
        "no_op_boundaries": list(NO_OP_BOUNDARIES),
    }

    return {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": _contract_status(selected_gate),
        "summary": _summary(
            store,
            runs=runs,
            run=run,
            gates=gates,
            selected_gate=selected_gate,
            blockers=blockers,
            approval_packet_id=approval_packet_id,
            request_digest=request_digest,
        ),
        "selected_run": run.to_dict(),
        "selected_gate": selected_gate.to_dict(),
        "selected_preview_artifacts": selected_preview_artifacts,
        "gate_previews": gate_previews,
        "future_resume_packet_preview": future_packet,
        "checks": _checks(selected_gate, blockers),
        "blockers": blockers,
        "safety": _safety(),
        "state_root": str(store.state_root),
    }


def build_approval_resume_contract_summary(vault_root: str | Path) -> dict[str, Any]:
    """Return a compact read-only approval/resume readiness summary."""

    contract = build_approval_resume_contract(vault_root)
    summary = dict(contract.get("summary") or {})
    return {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": contract.get("status"),
        "summary": summary,
        "safety": contract.get("safety") or _safety(),
        "blocked_authority": dict(BLOCKED_AUTHORITY),
    }


def _blocked_without_run(store: WorkflowPackStore, runs: list[WorkflowRun]) -> dict[str, Any]:
    pending_gates: list[dict[str, Any]] = []
    for run in runs:
        for gate in store.list_approval_gates(run.id):
            if gate.status == "pending":
                pending_gates.append(
                    {
                        "run_id": run.id,
                        "pack_id": run.pack_id,
                        "run_title": run.title,
                        "gate_id": gate.id,
                        "action_type": gate.action_type,
                        "status": gate.status,
                    }
                )
    return _blocked_contract(
        store,
        status="blocked_missing_run_id",
        blockers=["A run_id is required before a future approval-resume packet can be previewed."],
        requested_run_id="",
        requested_gate_id="",
        runs=runs,
        extra={"pending_gate_queue": pending_gates[:25]},
    )


def _contract_for_run_without_gates(
    store: WorkflowPackStore,
    run: WorkflowRun,
    requested_gate_id: str,
    runs: list[WorkflowRun],
) -> dict[str, Any]:
    return _blocked_contract(
        store,
        status="blocked_no_approval_gates",
        blockers=[f"Workflow Pack run has no approval gates: {run.id}"],
        requested_run_id=run.id,
        requested_gate_id=requested_gate_id,
        runs=runs,
        run=run,
        gates=[],
    )


def _blocked_contract(
    store: WorkflowPackStore,
    *,
    status: str,
    blockers: list[str],
    requested_run_id: str,
    requested_gate_id: str,
    runs: list[WorkflowRun],
    run: WorkflowRun | None = None,
    gates: list[ApprovalGate] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    selected_gate: ApprovalGate | None = None
    gates = gates or []
    if run is not None and gates:
        selected_gate = _select_gate(gates, requested_gate_id)
    base = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "summary": _summary(
            store,
            runs=runs,
            run=run,
            gates=gates,
            selected_gate=selected_gate,
            blockers=blockers,
            approval_packet_id="",
            request_digest="",
        )
        | {
            "requested_run_id": requested_run_id,
            "requested_gate_id": requested_gate_id,
        },
        "selected_run": run.to_dict() if run else None,
        "selected_gate": selected_gate.to_dict() if selected_gate else None,
        "selected_preview_artifacts": [],
        "gate_previews": [
            _gate_preview(gate, {}, selected=selected_gate is not None and gate.id == selected_gate.id)
            for gate in gates
        ],
        "future_resume_packet_preview": None,
        "checks": _checks(selected_gate, blockers),
        "blockers": blockers,
        "safety": _safety(),
        "state_root": str(store.state_root),
    }
    if extra:
        base.update(extra)
    return base


def _select_gate(gates: list[ApprovalGate], gate_id: str) -> ApprovalGate | None:
    if gate_id:
        return next((gate for gate in gates if gate.id == gate_id), None)
    pending = next((gate for gate in gates if gate.status == "pending"), None)
    return pending or gates[0]


def _gate_preview(
    gate: ApprovalGate,
    artifacts_by_id: dict[str, dict[str, Any]],
    *,
    selected: bool,
) -> dict[str, Any]:
    artifacts = [
        artifacts_by_id[artifact_id]
        for artifact_id in gate.preview_artifact_refs
        if artifact_id in artifacts_by_id
    ]
    return {
        "gate_id": gate.id,
        "run_id": gate.run_id,
        "action_type": gate.action_type,
        "status": gate.status,
        "selected": selected,
        "review_only_ready": gate.status == "pending",
        "approved_gate_present": gate.status == "approved",
        "approval_consumption_allowed_now": False,
        "resume_execution_allowed_now": False,
        "reason": gate.reason,
        "preview_artifact_refs": list(gate.preview_artifact_refs),
        "preview_artifacts": artifacts,
        "risk_flags": [flag.to_dict() for flag in gate.risk_flags],
    }


def _packet_material(
    *,
    run: WorkflowRun,
    gate: ApprovalGate,
    artifacts: list[dict[str, Any]],
    blockers: list[str],
) -> dict[str, Any]:
    return {
        "record_type": "workflow_pack_approval_resume_packet_preview",
        "model_version": MODEL_VERSION,
        "run_id": run.id,
        "pack_id": run.pack_id,
        "run_title": run.title,
        "gate_id": gate.id,
        "action_type": gate.action_type,
        "gate_status": gate.status,
        "requested_by": gate.requested_by,
        "requested_at": gate.requested_at,
        "reason": gate.reason,
        "preview_artifact_refs": list(gate.preview_artifact_refs),
        "preview_artifacts": [
            {
                "id": artifact.get("id"),
                "title": artifact.get("title"),
                "artifact_type": artifact.get("artifact_type"),
                "local_path": artifact.get("local_path"),
                "review_status": artifact.get("review_status"),
            }
            for artifact in artifacts
        ],
        "risk_flag_ids": [flag.id for flag in gate.risk_flags],
        "future_scope": {
            "scope": "one_workflow_pack_gate_only",
            "approval_artifact_required": True,
            "exact_digest_match_required": True,
            "exact_once_marker_required": True,
            "resume_executor_built": True,
            "approval_consumption_built": True,
            "execution_allowed_now": False,
        },
        "blockers": list(blockers),
    }


def _digest(material: dict[str, Any]) -> str:
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _contract_status(gate: ApprovalGate) -> str:
    if gate.status == "pending":
        return "ready_for_operator_approval_review_only"
    if gate.status == "approved":
        return "approved_gate_present_local_resume_consumed_or_duplicate_blocked"
    return "blocked_gate_not_approved"


def _gate_blockers(gate: ApprovalGate) -> list[str]:
    blockers = [
        "A scoped approval review artifact is required before local approval consumption.",
        "An exact-once marker is required before local approval resume execution.",
        "This contract preview cannot grant, consume, mutate, execute, send, publish, dispatch, or promote.",
    ]
    if gate.status == "pending":
        blockers.append("Selected approval gate is still pending operator approval.")
    elif gate.status == "approved":
        blockers.append("Selected approval gate is already approved; duplicate local resume is blocked.")
    elif gate.status == "rejected":
        blockers.append("Selected approval gate was rejected.")
    elif gate.status == "expired":
        blockers.append("Selected approval gate is expired.")
    else:
        blockers.append(f"Selected approval gate has unsupported status: {gate.status}")
    return blockers


def _summary(
    store: WorkflowPackStore,
    *,
    runs: list[WorkflowRun],
    run: WorkflowRun | None,
    gates: list[ApprovalGate],
    selected_gate: ApprovalGate | None,
    blockers: list[str],
    approval_packet_id: str,
    request_digest: str,
) -> dict[str, Any]:
    pending_count = sum(1 for gate in gates if gate.status == "pending")
    approved_count = sum(1 for gate in gates if gate.status == "approved")
    rejected_count = sum(1 for gate in gates if gate.status == "rejected")
    expired_count = sum(1 for gate in gates if gate.status == "expired")
    total_pending_across_runs = 0
    for candidate in runs:
        total_pending_across_runs += sum(1 for gate in store.list_approval_gates(candidate.id) if gate.status == "pending")

    return {
        "run_count": len(runs),
        "pending_gate_count_all_runs": total_pending_across_runs,
        "run_id": run.id if run else "",
        "pack_id": run.pack_id if run else "",
        "gate_count": len(gates),
        "pending_gate_count": pending_count,
        "approved_gate_count": approved_count,
        "rejected_gate_count": rejected_count,
        "expired_gate_count": expired_count,
        "selected_gate_id": selected_gate.id if selected_gate else "",
        "selected_action_type": selected_gate.action_type if selected_gate else "",
        "selected_gate_status": selected_gate.status if selected_gate else "",
        "approval_packet_id": approval_packet_id,
        "request_digest": request_digest,
        "contract_preview_ready": run is not None and selected_gate is not None,
        "approval_consumption_built": True,
        "resume_executor_built": True,
        "approval_execution_allowed": False,
        "approval_decision_consumed": False,
        "approval_consumption_performed": False,
        "resume_execution_performed": False,
        "external_actions_performed": False,
        "provider_calls_performed": False,
        "browser_actions_performed": False,
        "agent_bus_dispatch_performed": False,
        "canonical_promotion_performed": False,
        "policy_mutation_performed": False,
        "writes_performed": False,
        "blocker_count": len(blockers),
    }


def _checks(gate: ApprovalGate | None, blockers: list[str]) -> dict[str, bool]:
    return {
        "run_selected": gate is not None,
        "gate_selected": gate is not None,
        "gate_pending_or_approved": gate is not None and gate.status in {"pending", "approved"},
        "future_approval_artifact_required": True,
        "future_exact_digest_match_required": True,
        "future_exact_once_marker_required": True,
        "approval_consumption_available": True,
        "resume_executor_available": True,
        "execution_allowed_now": False,
        "blocked": bool(blockers),
    }


def _safety() -> dict[str, Any]:
    return {
        "approval_resume_contract_preview_only": True,
        "creates_approval_artifact": False,
        "writes_approval_artifact": False,
        "grants_approval": False,
        "mutates_approval_gate": False,
        "consumes_approval_decision": False,
        "executes_resume": False,
        "external_actions_performed": False,
        "provider_calls_performed": False,
        "browser_actions_performed": False,
        "agent_bus_dispatch_performed": False,
        "canonical_promotion_performed": False,
        "blocked_authority": dict(BLOCKED_AUTHORITY),
        "no_op_boundaries": list(NO_OP_BOUNDARIES),
    }
