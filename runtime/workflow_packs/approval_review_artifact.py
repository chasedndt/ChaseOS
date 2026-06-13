"""Scoped operator-review approval artifact writer for Workflow Packs.

This pass may write one create-only review artifact for a single Workflow Pack
run/gate approval packet. It does not consume the approval, mutate the gate,
reserve exact-once markers, resume a run, dispatch Agent Bus work, call
providers, drive a browser, send/publish anything, promote graph/canonical
state, or change policy.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from .approval_resume_contract import (
    BLOCKED_AUTHORITY,
    NO_OP_BOUNDARIES,
    build_approval_resume_contract,
)
from .store import WorkflowPackStore


MODEL_VERSION = "workflow_packs.approval_review_artifact.v1"
SURFACE_ID = "workflow_packs_approval_review_artifact"
APPROVAL_RECORD_TYPE = "workflow_pack_approval_resume_artifact"
READY_STATUS = "ready_to_write_workflow_pack_approval_review_artifact"
WRITTEN_STATUS = "workflow_pack_approval_review_artifact_written_no_execution"
EXISTING_STATUS = "workflow_pack_approval_review_artifact_existing_matching_no_execution"
BLOCKED_STATUS = "blocked_workflow_pack_approval_review_artifact"
NEXT_OPERATOR_REVIEW_PASS = "product-workflow-packs-approval-review-artifact-writer"
NEXT_CONSUMPTION_DRY_RUN_PASS = "product-workflow-packs-approval-consumption-exact-once-dry-run"

_SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9_.-]+$")


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _write_json_create_only(path: Path, payload: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = _read_json(path)
        if existing and _approval_artifact_matches(
            existing,
            packet_id=str(payload.get("approval_packet_id") or ""),
            request_digest=str(payload.get("request_digest") or ""),
            decision=str(payload.get("operator_decision") or ""),
        ):
            return "existing_matching_approval_present"
        raise ValueError(f"Workflow Pack approval review artifact already exists with different content: {path}")
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return "approval_artifact_written"


def _normalize_decision(decision: str) -> str:
    normalized = str(decision or "").strip().lower()
    if normalized == "approve":
        return "approved"
    if normalized in {"reject", "deny", "denied"}:
        return "rejected"
    return normalized or "approved"


def required_operator_statement(*, decision: str, approval_packet_id: str, request_digest: str) -> str:
    """Return the exact statement required before a review artifact write."""

    normalized = _normalize_decision(decision)
    verb = "APPROVE" if normalized == "approved" else "REJECT"
    return f"{verb} WORKFLOW PACK GATE ONLY: {approval_packet_id} {request_digest}"


def build_approval_review_artifact(
    vault_root: str | Path,
    *,
    run_id: str = "",
    gate_id: str = "",
    request_digest: str = "",
    reviewer_id: str = "operator",
    operator_statement: str = "",
    decision: str = "approved",
    write_approval: bool = False,
    generated_at: str = "",
) -> dict[str, Any]:
    """Preview or write a scoped Workflow Pack approval review artifact."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    normalized_decision = _normalize_decision(decision)
    requested_digest = str(request_digest or "").strip()
    reviewer = str(reviewer_id or "").strip()
    provided_statement = str(operator_statement or "").strip()

    contract = build_approval_resume_contract(vault, run_id=str(run_id or ""), gate_id=str(gate_id or ""))
    future_packet = contract.get("future_resume_packet_preview") or {}
    summary = contract.get("summary") or {}
    selected_gate = contract.get("selected_gate") or {}
    selected_run = contract.get("selected_run") or {}
    packet_id = str(future_packet.get("approval_packet_id") or summary.get("approval_packet_id") or "")
    contract_digest = str(future_packet.get("request_digest") or summary.get("request_digest") or "")
    selected_run_id = str(future_packet.get("run_id") or selected_run.get("id") or run_id or "")
    selected_gate_id = str(future_packet.get("gate_id") or selected_gate.get("id") or gate_id or "")
    gate_status = str(future_packet.get("gate_status") or selected_gate.get("status") or "")
    expected_statement = (
        required_operator_statement(
            decision=normalized_decision,
            approval_packet_id=packet_id,
            request_digest=contract_digest,
        )
        if packet_id and contract_digest
        else ""
    )

    blockers: list[str] = []
    if normalized_decision not in {"approved", "rejected"}:
        blockers.append("Operator decision must be approve/approved or reject/rejected/deny/denied.")
    if not future_packet:
        blockers.append("Workflow Pack approval/resume packet preview is not available for this run/gate.")
    if not packet_id or not contract_digest:
        blockers.append("Workflow Pack approval packet id or request digest is missing.")
    if packet_id and not _SAFE_COMPONENT.fullmatch(packet_id):
        blockers.append("Workflow Pack approval packet id is not a safe path component.")
    if requested_digest and requested_digest != contract_digest:
        blockers.append("Requested request_digest does not match the current Workflow Pack approval packet.")
    if write_approval and not requested_digest:
        blockers.append("request_digest is required before writing a Workflow Pack approval review artifact.")
    if write_approval and not reviewer:
        blockers.append("reviewer_id is required before writing a Workflow Pack approval review artifact.")
    if write_approval and provided_statement != expected_statement:
        blockers.append("operator_statement must exactly match the required Workflow Pack approval review statement.")
    if write_approval and gate_status != "pending":
        blockers.append("Only pending Workflow Pack approval gates can receive a new review artifact.")

    store = WorkflowPackStore(vault)
    approval_path: Path | None = None
    marker_path: Path | None = None
    existing_payload: dict[str, Any] | None = None
    existing_matches = False
    if selected_run_id and packet_id and _SAFE_COMPONENT.fullmatch(packet_id):
        try:
            approval_path = store.run_dir(selected_run_id) / "approval_reviews" / f"{packet_id}.json"
            marker_path = store.run_dir(selected_run_id) / "approval_execution_markers" / f"{packet_id}.json"
        except ValueError as exc:
            blockers.append(str(exc))

    if approval_path is not None and approval_path.exists():
        existing_payload = _read_json(approval_path)
        existing_matches = bool(
            existing_payload
            and _approval_artifact_matches(
                existing_payload,
                packet_id=packet_id,
                request_digest=contract_digest,
                decision=normalized_decision,
            )
        )
        if not existing_matches:
            blockers.append("Existing Workflow Pack approval review artifact does not match the current packet.")

    payload = (
        _artifact_payload(
            generated_at=timestamp,
            contract=contract,
            future_packet=future_packet,
            approval_packet_id=packet_id,
            request_digest=contract_digest,
            reviewer_id=reviewer,
            operator_statement=expected_statement,
            decision=normalized_decision,
            approval_path=_relative_to_vault(vault, approval_path) if approval_path else "",
            marker_path=_relative_to_vault(vault, marker_path) if marker_path else "",
        )
        if packet_id and contract_digest and selected_run_id and selected_gate_id
        else {}
    )

    write_status = "not_requested"
    writes_performed = False
    artifact_present = existing_matches
    status = READY_STATUS
    next_pass = NEXT_OPERATOR_REVIEW_PASS
    if blockers:
        status = BLOCKED_STATUS
    elif existing_matches:
        status = EXISTING_STATUS
        write_status = "existing_matching_approval_present"
        artifact_present = True
        next_pass = NEXT_CONSUMPTION_DRY_RUN_PASS
    elif write_approval and approval_path is not None:
        write_status = _write_json_create_only(approval_path, payload)
        writes_performed = write_status == "approval_artifact_written"
        artifact_present = True
        status = WRITTEN_STATUS if writes_performed else EXISTING_STATUS
        next_pass = NEXT_CONSUMPTION_DRY_RUN_PASS

    ok = status != BLOCKED_STATUS
    approved = normalized_decision == "approved" and artifact_present
    rejected = normalized_decision == "rejected" and artifact_present
    authority = {
        **dict(BLOCKED_AUTHORITY),
        "approval_resume_contract_preview_only": False,
        "approval_review_artifact_writer": True,
        "creates_approval_artifact": bool(writes_performed),
        "writes_approval_artifact": bool(writes_performed),
        "grants_approval": False,
        "mutates_approval_gate": False,
        "consumes_approval_decision": False,
        "reserves_exact_once_marker": False,
        "executes_resume": False,
    }
    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "summary": {
            "run_id": selected_run_id,
            "pack_id": str(future_packet.get("pack_id") or summary.get("pack_id") or ""),
            "gate_id": selected_gate_id,
            "gate_status_at_review": gate_status,
            "action_type": str(future_packet.get("action_type") or summary.get("selected_action_type") or ""),
            "approval_packet_id": packet_id,
            "request_digest": contract_digest,
            "operator_decision": normalized_decision,
            "approval_artifact_ready": ok,
            "approval_artifact_written": artifact_present,
            "approval_artifact_write_status": write_status,
            "future_single_workflow_pack_gate_approved": approved,
            "future_single_workflow_pack_gate_rejected": rejected,
            "approval_decision_consumed": False,
            "approval_consumption_performed": False,
            "exact_once_marker_reserved": False,
            "resume_execution_performed": False,
            "external_actions_performed": False,
            "provider_calls_performed": False,
            "browser_actions_performed": False,
            "agent_bus_dispatch_performed": False,
            "canonical_promotion_performed": False,
            "policy_mutation_performed": False,
            "writes_performed": writes_performed,
            "next_recommended_pass": next_pass,
        },
        "source_contract": contract,
        "approval_artifact_payload": payload,
        "approval_artifact": {
            "path": _relative_to_vault(vault, approval_path) if approval_path else "",
            "exists_before": bool(existing_payload),
            "exists_after": bool(approval_path and approval_path.exists()),
            "matches_current_packet": artifact_present,
            "write_requested": bool(write_approval),
            "write_status": write_status,
            "written_in_this_pass": writes_performed,
            "required_operator_statement": expected_statement,
        },
        "exact_once_marker_contract": {
            "path": _relative_to_vault(vault, marker_path) if marker_path else "",
            "exists": bool(marker_path and marker_path.exists()),
            "reserved_in_this_pass": False,
            "future_write_mode": "exclusive_create_before_future_resume_execution",
        },
        "checks": {
            "contract_preview_ready": bool(future_packet),
            "request_digest_matches": (not requested_digest) or requested_digest == contract_digest,
            "operator_decision_supported": normalized_decision in {"approved", "rejected"},
            "operator_statement_matches": (not write_approval) or provided_statement == expected_statement,
            "approval_artifact_absent_or_matching": not bool(existing_payload) or existing_matches,
            "gate_pending": gate_status == "pending",
            "approval_decision_consumed": False,
            "exact_once_marker_reserved": False,
            "resume_execution_performed": False,
            "no_execution_in_this_pass": True,
        },
        "authority": authority,
        "safety": {
            "approval_review_artifact_writer": True,
            "creates_approval_artifact": bool(writes_performed),
            "writes_approval_artifact": bool(writes_performed),
            "grants_approval": False,
            "mutates_approval_gate": False,
            "consumes_approval_decision": False,
            "reserves_exact_once_marker": False,
            "executes_resume": False,
            "external_actions_performed": False,
            "provider_calls_performed": False,
            "browser_actions_performed": False,
            "agent_bus_dispatch_performed": False,
            "canonical_promotion_performed": False,
            "blocked_authority": dict(BLOCKED_AUTHORITY),
            "no_op_boundaries": list(NO_OP_BOUNDARIES),
        },
        "blockers": blockers,
        "unverified": [
            "No approval decision was consumed in this review pass.",
            "No exact-once marker was reserved in this review pass.",
            "No Workflow Pack run was resumed in this review pass.",
            "No runtime, Agent Bus, provider, browser, email, publish, graph, canonical, policy, secret, or credential action was attempted.",
        ],
        "writes_performed": writes_performed,
        "next_recommended_pass": next_pass,
    }


def _artifact_payload(
    *,
    generated_at: str,
    contract: dict[str, Any],
    future_packet: dict[str, Any],
    approval_packet_id: str,
    request_digest: str,
    reviewer_id: str,
    operator_statement: str,
    decision: str,
    approval_path: str,
    marker_path: str,
) -> dict[str, Any]:
    reviewed_key = "approved" if decision == "approved" else "rejected"
    return {
        "record_type": APPROVAL_RECORD_TYPE,
        "model_version": MODEL_VERSION,
        "generated_at": generated_at,
        "status": WRITTEN_STATUS,
        "approval_packet_id": approval_packet_id,
        "request_digest": request_digest,
        "run_id": str(future_packet.get("run_id") or ""),
        "pack_id": str(future_packet.get("pack_id") or ""),
        "run_title": str(future_packet.get("run_title") or ""),
        "gate_id": str(future_packet.get("gate_id") or ""),
        "action_type": str(future_packet.get("action_type") or ""),
        "gate_status_at_review": str(future_packet.get("gate_status") or ""),
        "reviewed_by": reviewer_id,
        "reviewed_at": generated_at,
        "operator_decision": decision,
        f"{reviewed_key}_by": reviewer_id,
        f"{reviewed_key}_at": generated_at,
        "operator_statement": operator_statement,
        "approval_scope": "one_workflow_pack_gate_only",
        "approval_artifact_path": approval_path,
        "exact_once_marker_path": marker_path,
        "exact_once_marker_exists": False,
        "preview_artifact_refs": list(future_packet.get("preview_artifact_refs") or []),
        "preview_artifacts": list(future_packet.get("preview_artifacts") or []),
        "risk_flag_ids": list(future_packet.get("risk_flag_ids") or []),
        "exact_match_requirements": dict(future_packet.get("exact_match_requirements") or {}),
        "future_scope": dict(future_packet.get("future_scope") or {}),
        "approval_consumption_required": True,
        "approval_consumption_allowed": False,
        "resume_execution_allowed": False,
        "future_single_workflow_pack_gate_approved": decision == "approved",
        "future_single_workflow_pack_gate_rejected": decision == "rejected",
        "approval_decision_consumed": False,
        "idempotency_marker_reserved": False,
        "exact_once_marker_reserved": False,
        "resume_execution_performed": False,
        "runtime_execution_performed": False,
        "external_actions_performed": False,
        "provider_calls_performed": False,
        "browser_actions_performed": False,
        "agent_bus_dispatch_performed": False,
        "email_send_performed": False,
        "publish_content_performed": False,
        "canonical_promotion_performed": False,
        "policy_mutation_performed": False,
        "secret_or_credential_accessed": False,
        "mutates_approval_gate": False,
        "mutates_workflow_run": False,
        "source_contract_status": str(contract.get("status") or ""),
        "source_contract_summary": dict(contract.get("summary") or {}),
        "no_op_boundaries": list(NO_OP_BOUNDARIES),
        "next_recommended_pass": NEXT_CONSUMPTION_DRY_RUN_PASS,
    }


def _approval_artifact_matches(
    payload: dict[str, Any],
    *,
    packet_id: str,
    request_digest: str,
    decision: str,
) -> bool:
    return (
        payload.get("record_type") == APPROVAL_RECORD_TYPE
        and payload.get("approval_packet_id") == packet_id
        and payload.get("request_digest") == request_digest
        and payload.get("operator_decision") == decision
        and payload.get("approval_scope") == "one_workflow_pack_gate_only"
        and payload.get("approval_decision_consumed") is False
        and payload.get("exact_once_marker_reserved") is False
        and payload.get("resume_execution_performed") is False
        and payload.get("external_actions_performed") is False
        and payload.get("provider_calls_performed") is False
        and payload.get("browser_actions_performed") is False
        and payload.get("agent_bus_dispatch_performed") is False
        and payload.get("canonical_promotion_performed") is False
        and payload.get("policy_mutation_performed") is False
    )
