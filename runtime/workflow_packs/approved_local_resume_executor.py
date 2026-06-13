"""Approved local resume executor for Workflow Pack approval packets.

This executor consumes one scoped Workflow Pack approval review artifact after
an exact-once marker has been reserved. It only mutates the matching local
run/gate state and writes a local evidence record. It does not call providers,
drive a browser, send email, publish content, dispatch Agent Bus work, mutate
policy, or promote graph/canonical state.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .approval_marker_reservation import (
    MARKER_RECORD_TYPE,
    MODEL_VERSION as MARKER_MODEL_VERSION,
)
from .approval_resume_contract import (
    BLOCKED_AUTHORITY,
    build_approval_resume_contract,
)
from .approval_review_artifact import (
    APPROVAL_RECORD_TYPE,
    MODEL_VERSION as REVIEW_ARTIFACT_MODEL_VERSION,
)
from .models import ApprovalGate, WorkflowRun
from .store import WorkflowPackStore


MODEL_VERSION = "workflow_packs.approved_local_resume_executor.v1"
SURFACE_ID = "workflow_packs_approved_local_resume_executor"
RESUME_RECORD_TYPE = "workflow_pack_approved_local_resume_execution"
READY_STATUS = "workflow_pack_approved_local_resume_ready"
REJECTION_READY_STATUS = "workflow_pack_rejected_local_resume_ready"
EXECUTED_STATUS = "workflow_pack_approved_local_resume_completed"
REJECTED_STATUS = "workflow_pack_rejected_local_resume_completed"
BLOCKED_STATUS = "blocked_workflow_pack_approved_local_resume"
NEXT_VERIFICATION_PASS = "product-workflow-packs-local-approval-resume-verified"
BLOCKED_PASS = "product-workflow-packs-approved-local-resume-executor"

_FALSE_REVIEW_FLAGS = [
    "approval_decision_consumed",
    "idempotency_marker_reserved",
    "exact_once_marker_reserved",
    "resume_execution_performed",
    "runtime_execution_performed",
    "external_actions_performed",
    "provider_calls_performed",
    "browser_actions_performed",
    "agent_bus_dispatch_performed",
    "email_send_performed",
    "publish_content_performed",
    "canonical_promotion_performed",
    "policy_mutation_performed",
    "secret_or_credential_accessed",
    "mutates_approval_gate",
    "mutates_workflow_run",
]

_FALSE_MARKER_FLAGS = [
    "approval_decision_consumed",
    "approval_consumption_performed",
    "resume_execution_performed",
    "runtime_execution_performed",
    "external_actions_performed",
    "provider_calls_performed",
    "browser_actions_performed",
    "agent_bus_dispatch_performed",
    "email_send_performed",
    "publish_content_performed",
    "canonical_promotion_performed",
    "policy_mutation_performed",
    "secret_or_credential_accessed",
    "mutates_approval_gate",
    "mutates_workflow_run",
]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _resolve_vault_relative_path(vault: Path, path_value: str, *, field_name: str) -> Path:
    raw = str(path_value or "").strip()
    if not raw:
        raise ValueError(f"{field_name} is empty.")
    path = Path(raw)
    resolved = path.resolve() if path.is_absolute() else (vault / path).resolve()
    try:
        resolved.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError(f"Workflow Pack {field_name} escapes vault: {path_value}") from exc
    return resolved


def _read_json(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _write_json_create_only(path: Path, payload: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
    except FileExistsError as exc:
        raise ValueError(f"Workflow Pack local resume evidence already exists: {path}") from exc
    return "local_resume_evidence_written"


def _normalize_expected_decision(expected_decision: str) -> str:
    normalized = str(expected_decision or "").strip().lower()
    if normalized == "approve":
        return "approved"
    if normalized in {"reject", "deny", "denied"}:
        return "rejected"
    return normalized


def _select_gate(gates: list[ApprovalGate], gate_id: str) -> ApprovalGate | None:
    if gate_id:
        return next((gate for gate in gates if gate.id == gate_id), None)
    pending = next((gate for gate in gates if gate.status == "pending"), None)
    return pending or gates[0] if gates else None


def _find_packet_file(
    run_dir: Path,
    folder_name: str,
    *,
    request_digest: str,
    gate_id: str,
) -> Path | None:
    if not request_digest:
        return None
    folder = run_dir / folder_name
    if not folder.exists():
        return None
    for path in sorted(folder.glob("*.json")):
        payload = _read_json(path)
        if not payload:
            continue
        if payload.get("request_digest") != request_digest:
            continue
        if gate_id and payload.get("gate_id") != gate_id:
            continue
        return path
    return None


def required_local_resume_statement(*, approval_packet_id: str, request_digest: str) -> str:
    """Return the exact operator statement required before local resume."""

    return f"CONSUME WORKFLOW PACK LOCAL DECISION ONLY: {approval_packet_id} {request_digest}"


def build_approved_local_resume_executor(
    vault_root: str | Path,
    *,
    run_id: str = "",
    gate_id: str = "",
    request_digest: str = "",
    approval_artifact_path: str = "",
    exact_once_marker_path: str = "",
    expected_decision: str = "",
    execute_resume: bool = False,
    operator_statement: str = "",
    executed_by: str = "operator",
    generated_at: str = "",
) -> dict[str, Any]:
    """Preview or execute the local approval-decision consumption/resume path."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    requested_run_id = str(run_id or "").strip()
    requested_gate_id = str(gate_id or "").strip()
    requested_digest = str(request_digest or "").strip()
    normalized_expected_decision = _normalize_expected_decision(expected_decision)
    provided_statement = str(operator_statement or "").strip()
    executor = str(executed_by or "").strip()
    blockers: list[str] = []

    if normalized_expected_decision and normalized_expected_decision not in {"approved", "rejected"}:
        blockers.append("expected_decision must be approve/approved or reject/rejected/deny/denied.")
    if not requested_digest:
        blockers.append("request_digest is required before local approval resume execution.")

    store = WorkflowPackStore(vault)
    run: WorkflowRun | None = None
    gate: ApprovalGate | None = None
    gates: list[ApprovalGate] = []
    try:
        run = store.get_run(requested_run_id) if requested_run_id else None
    except FileNotFoundError:
        blockers.append(f"Workflow Pack run was not found: {requested_run_id}")
    except ValueError as exc:
        blockers.append(str(exc))

    if run is None and not requested_run_id:
        blockers.append("run_id is required before local approval resume execution.")

    if run is not None:
        gates = store.list_approval_gates(run.id)
        gate = _select_gate(gates, requested_gate_id)
        if gate is None:
            blockers.append(f"Approval gate was not found for run {run.id}: {requested_gate_id}")

    contract = (
        build_approval_resume_contract(vault, run_id=run.id, gate_id=gate.id)
        if run is not None and gate is not None
        else {}
    )
    contract_summary = contract.get("summary") or {}
    contract_packet = contract.get("future_resume_packet_preview") or {}
    contract_digest = str(contract_summary.get("request_digest") or contract_packet.get("request_digest") or "")
    contract_packet_id = str(
        contract_summary.get("approval_packet_id") or contract_packet.get("approval_packet_id") or ""
    )

    approval_path: Path | None = None
    marker_path: Path | None = None
    if approval_artifact_path:
        try:
            approval_path = _resolve_vault_relative_path(
                vault,
                approval_artifact_path,
                field_name="approval_artifact_path",
            )
        except ValueError as exc:
            blockers.append(str(exc))
    if exact_once_marker_path:
        try:
            marker_path = _resolve_vault_relative_path(
                vault,
                exact_once_marker_path,
                field_name="exact_once_marker_path",
            )
        except ValueError as exc:
            blockers.append(str(exc))

    if run is not None:
        run_dir = store.run_dir(run.id)
        if approval_path is None:
            approval_path = _find_packet_file(
                run_dir,
                "approval_reviews",
                request_digest=requested_digest,
                gate_id=gate.id if gate else requested_gate_id,
            )
        if marker_path is None:
            marker_path = _find_packet_file(
                run_dir,
                "approval_execution_markers",
                request_digest=requested_digest,
                gate_id=gate.id if gate else requested_gate_id,
            )
        if approval_path is None and contract_packet_id:
            approval_path = run_dir / "approval_reviews" / f"{contract_packet_id}.json"
        if marker_path is None and contract_packet_id:
            marker_path = run_dir / "approval_execution_markers" / f"{contract_packet_id}.json"

    approval_payload = _read_json(approval_path)
    marker_payload = _read_json(marker_path)
    if approval_path is None or not approval_path.exists():
        blockers.append("Workflow Pack approval review artifact is missing.")
    elif approval_payload is None:
        blockers.append("Workflow Pack approval review artifact is not readable JSON.")
    if marker_path is None or not marker_path.exists():
        blockers.append("Workflow Pack exact-once marker is missing.")
    elif marker_payload is None:
        blockers.append("Workflow Pack exact-once marker is not readable JSON.")

    packet_id = str(
        (marker_payload or {}).get("approval_packet_id")
        or (approval_payload or {}).get("approval_packet_id")
        or contract_packet_id
        or ""
    )
    approval_decision = str((approval_payload or {}).get("operator_decision") or normalized_expected_decision or "")
    marker_decision = str((marker_payload or {}).get("operator_decision") or "")
    resume_path = (
        store.run_dir(run.id) / "approval_local_resumes" / f"{packet_id}.json"
        if run is not None and packet_id
        else None
    )
    existing_resume_payload = _read_json(resume_path) if resume_path and resume_path.exists() else None
    if existing_resume_payload is not None:
        blockers.append("Workflow Pack local resume evidence already exists.")

    approval_rel = _relative_to_vault(vault, approval_path)
    marker_rel = _relative_to_vault(vault, marker_path)
    resume_rel = _relative_to_vault(vault, resume_path)
    expected_statement = (
        required_local_resume_statement(approval_packet_id=packet_id, request_digest=requested_digest)
        if packet_id and requested_digest
        else ""
    )

    checks = _validation_checks(
        run=run,
        gate=gate,
        approval_payload=approval_payload,
        marker_payload=marker_payload,
        request_digest=requested_digest,
        expected_decision=normalized_expected_decision,
        approval_decision=approval_decision,
        marker_decision=marker_decision,
        approval_path=approval_path,
        marker_path=marker_path,
        approval_rel=approval_rel,
        marker_rel=marker_rel,
        contract_digest=contract_digest,
        gate_was_pending=(gate is not None and gate.status == "pending"),
        execute_resume=execute_resume,
        provided_statement=provided_statement,
        expected_statement=expected_statement,
        executed_by=executor,
        existing_resume_payload=existing_resume_payload,
    )
    blockers.extend(name for name, passed in checks.items() if not passed)
    blockers = list(dict.fromkeys(blockers))

    after_gate_status = approval_decision if approval_decision in {"approved", "rejected"} else ""
    after_run_status = "approved" if approval_decision == "approved" else "cancelled" if approval_decision == "rejected" else ""
    run_status_before = run.status if run is not None else ""
    gate_status_before = gate.status if gate is not None else ""
    approval_ref_status_before = _approval_ref_status(run, gate.id if gate else "")
    approval_ref_status_after = approval_decision if approval_decision in {"approved", "rejected"} else ""

    evidence_payload = _resume_evidence_payload(
        generated_at=timestamp,
        packet_id=packet_id,
        request_digest=requested_digest,
        run=run,
        gate=gate,
        approval_decision=approval_decision,
        approval_artifact_path=approval_rel,
        marker_path=marker_rel,
        resume_path=resume_rel,
        executed_by=executor or "operator",
        operator_statement=expected_statement,
        before_state={
            "run_status": run_status_before,
            "gate_status": gate_status_before,
            "approval_ref_status": approval_ref_status_before,
        },
        after_state={
            "run_status": after_run_status,
            "gate_status": after_gate_status,
            "approval_ref_status": approval_ref_status_after,
        },
    )

    writes_performed = False
    state_mutations_performed = False
    write_status = "not_requested"
    audit_event_written = False
    if not blockers and execute_resume and run is not None and gate is not None and resume_path is not None:
        updated_gate = replace(
            gate,
            status=approval_decision,  # type: ignore[arg-type]
            approved_by=executor if approval_decision == "approved" else gate.approved_by,
            approved_at=timestamp if approval_decision == "approved" else gate.approved_at,
        )
        updated_refs = [
            replace(ref, status=approval_decision) if ref.id == gate.id else ref
            for ref in run.approval_refs
        ]
        updated_run = replace(
            run,
            status=after_run_status,  # type: ignore[arg-type]
            approval_refs=updated_refs,
        )
        store.save_approval_gate(updated_gate)
        store.save_run(updated_run)
        state_mutations_performed = True
        try:
            write_status = _write_json_create_only(resume_path, evidence_payload)
            writes_performed = True
        except ValueError as exc:
            blockers.append(str(exc))
            write_status = "blocked_existing_local_resume_evidence"
        if writes_performed:
            store.append_audit_event(
                run.id,
                "workflow_pack_approval_local_resume_executed",
                {
                    "approval_packet_id": packet_id,
                    "request_digest": requested_digest,
                    "gate_id": gate.id,
                    "operator_decision": approval_decision,
                    "run_status_after": after_run_status,
                    "gate_status_after": after_gate_status,
                    "local_resume_evidence_path": resume_rel,
                    "external_actions_performed": False,
                    "provider_calls_performed": False,
                    "browser_actions_performed": False,
                    "agent_bus_dispatch_performed": False,
                    "canonical_promotion_performed": False,
                    "policy_mutation_performed": False,
                },
            )
            audit_event_written = True

    ok = not blockers
    executed = ok and writes_performed and state_mutations_performed
    status = (
        REJECTED_STATUS
        if executed and approval_decision == "rejected"
        else EXECUTED_STATUS
        if executed
        else REJECTION_READY_STATUS
        if ok and approval_decision == "rejected"
        else READY_STATUS
        if ok
        else BLOCKED_STATUS
    )
    authority = {
        **dict(BLOCKED_AUTHORITY),
        "approval_resume_contract_preview_only": False,
        "approved_local_resume_executor": True,
        "validates_approval_artifact": True,
        "validates_exact_once_marker": True,
        "creates_approval_artifact": False,
        "writes_approval_artifact": False,
        "grants_approval": False,
        "approval_status_mutation": state_mutations_performed,
        "approval_decision_consumption": executed,
        "approval_consumption_performed": executed,
        "resume_execution": executed,
        "mutates_approval_gate": state_mutations_performed,
        "mutates_workflow_run": state_mutations_performed,
        "writes_local_resume_evidence": writes_performed,
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

    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "summary": {
            "run_id": run.id if run else requested_run_id,
            "pack_id": run.pack_id if run else "",
            "gate_id": gate.id if gate else requested_gate_id,
            "action_type": gate.action_type if gate else str((approval_payload or {}).get("action_type") or ""),
            "approval_packet_id": packet_id,
            "request_digest": requested_digest,
            "operator_decision": approval_decision,
            "approved_local_resume_ready": ok,
            "approval_consumption_built": True,
            "resume_executor_built": True,
            "approval_decision_consumed": executed,
            "approval_consumption_performed": executed,
            "resume_execution_performed": executed,
            "local_resume_execution_performed": executed,
            "state_mutations_performed": state_mutations_performed,
            "run_status_before": run_status_before,
            "gate_status_before": gate_status_before,
            "approval_ref_status_before": approval_ref_status_before,
            "run_status_after": after_run_status if executed else run_status_before,
            "gate_status_after": after_gate_status if executed else gate_status_before,
            "approval_ref_status_after": approval_ref_status_after if executed else approval_ref_status_before,
            "exact_once_marker_reserved": marker_payload is not None,
            "local_resume_evidence_written": writes_performed,
            "audit_event_written": audit_event_written,
            "external_actions_performed": False,
            "runtime_execution_performed": False,
            "provider_calls_performed": False,
            "browser_actions_performed": False,
            "agent_bus_dispatch_performed": False,
            "email_send_performed": False,
            "publish_content_performed": False,
            "canonical_promotion_performed": False,
            "policy_mutation_performed": False,
            "secret_or_credential_accessed": False,
            "writes_performed": writes_performed,
            "next_recommended_pass": NEXT_VERIFICATION_PASS if executed else BLOCKED_PASS if not ok else SURFACE_ID,
        },
        "source_contract": contract,
        "approval_artifact": {
            "path": approval_rel,
            "exists": bool(approval_path and approval_path.is_file()),
            "record_type": (approval_payload or {}).get("record_type"),
            "model_version": (approval_payload or {}).get("model_version"),
            "approval_packet_id": (approval_payload or {}).get("approval_packet_id"),
            "request_digest": (approval_payload or {}).get("request_digest"),
            "operator_decision": approval_decision,
            "consumed_in_this_pass": executed,
            "mutated_in_this_pass": False,
        },
        "exact_once_marker": {
            "path": marker_rel,
            "exists": bool(marker_path and marker_path.is_file()),
            "record_type": (marker_payload or {}).get("record_type"),
            "model_version": (marker_payload or {}).get("model_version"),
            "approval_packet_id": (marker_payload or {}).get("approval_packet_id"),
            "request_digest": (marker_payload or {}).get("request_digest"),
            "reserved_before_resume": marker_payload is not None,
            "mutated_in_this_pass": False,
        },
        "local_resume_evidence": {
            "path": resume_rel,
            "exists_before": existing_resume_payload is not None,
            "exists_after": bool(resume_path and resume_path.exists()),
            "write_requested": bool(execute_resume),
            "write_status": write_status,
            "written_in_this_pass": writes_performed,
            "record_type": RESUME_RECORD_TYPE if evidence_payload else "",
            "required_operator_statement": expected_statement,
            "write_mode": "atomic_create_new_only_after_marker_before_duplicate_resume",
            "duplicate_policy": "block_existing_local_resume_evidence_or_non_pending_gate",
        },
        "local_resume_evidence_payload": evidence_payload,
        "checks": checks,
        "authority": authority,
        "blocked_authority": [key for key, value in authority.items() if value is False],
        "safety": {
            "approved_local_resume_executor": True,
            "local_resume_only": True,
            "validates_approval_artifact": True,
            "validates_exact_once_marker": True,
            "creates_approval_artifact": False,
            "writes_approval_artifact": False,
            "grants_approval": False,
            "mutates_approval_gate": state_mutations_performed,
            "mutates_workflow_run": state_mutations_performed,
            "consumes_approval_decision": executed,
            "approval_consumption_performed": executed,
            "executes_resume": executed,
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
            "external_actions_blocked": True,
        },
        "blockers": blockers,
        "unverified": [
            "No provider, browser, email, publishing, Agent Bus, runtime, graph/canonical, policy, secret, or credential action was attempted by this local executor.",
            "External action executors remain outside this local approval-to-resume scope.",
        ],
        "writes_performed": writes_performed,
        "next_recommended_pass": NEXT_VERIFICATION_PASS if executed else BLOCKED_PASS if not ok else SURFACE_ID,
    }


def _validation_checks(
    *,
    run: WorkflowRun | None,
    gate: ApprovalGate | None,
    approval_payload: dict[str, Any] | None,
    marker_payload: dict[str, Any] | None,
    request_digest: str,
    expected_decision: str,
    approval_decision: str,
    marker_decision: str,
    approval_path: Path | None,
    marker_path: Path | None,
    approval_rel: str,
    marker_rel: str,
    contract_digest: str,
    gate_was_pending: bool,
    execute_resume: bool,
    provided_statement: str,
    expected_statement: str,
    executed_by: str,
    existing_resume_payload: dict[str, Any] | None,
) -> dict[str, bool]:
    approval = approval_payload or {}
    marker = marker_payload or {}
    return {
        "run_selected": run is not None,
        "gate_selected": gate is not None,
        "request_digest_provided": bool(request_digest),
        "current_pending_contract_digest_matches": (
            not gate_was_pending or not contract_digest or request_digest == contract_digest
        ),
        "approval_artifact_present": bool(approval_path and approval_path.is_file()),
        "approval_artifact_json_readable": approval_payload is not None,
        "approval_record_type_valid": approval.get("record_type") == APPROVAL_RECORD_TYPE,
        "approval_model_version_valid": approval.get("model_version") == REVIEW_ARTIFACT_MODEL_VERSION,
        "approval_request_digest_matches": bool(request_digest) and approval.get("request_digest") == request_digest,
        "approval_packet_id_present": bool(approval.get("approval_packet_id")),
        "approval_run_id_matches": run is not None and approval.get("run_id") == run.id,
        "approval_pack_id_matches": run is not None and approval.get("pack_id") == run.pack_id,
        "approval_gate_id_matches": gate is not None and approval.get("gate_id") == gate.id,
        "approval_action_type_matches": gate is not None and approval.get("action_type") == gate.action_type,
        "approval_scope_one_gate": approval.get("approval_scope") == "one_workflow_pack_gate_only",
        "approval_decision_supported": approval_decision in {"approved", "rejected"},
        "approval_decision_matches_expected": (not expected_decision) or approval_decision == expected_decision,
        "approval_review_false_authority_flags": all(approval.get(key) is False for key in _FALSE_REVIEW_FLAGS),
        "marker_present": bool(marker_path and marker_path.is_file()),
        "marker_json_readable": marker_payload is not None,
        "marker_record_type_valid": marker.get("record_type") == MARKER_RECORD_TYPE,
        "marker_model_version_valid": marker.get("model_version") == MARKER_MODEL_VERSION,
        "marker_request_digest_matches": bool(request_digest) and marker.get("request_digest") == request_digest,
        "marker_packet_id_matches_approval": bool(marker.get("approval_packet_id"))
        and marker.get("approval_packet_id") == approval.get("approval_packet_id"),
        "marker_run_id_matches": run is not None and marker.get("run_id") == run.id,
        "marker_pack_id_matches": run is not None and marker.get("pack_id") == run.pack_id,
        "marker_gate_id_matches": gate is not None and marker.get("gate_id") == gate.id,
        "marker_action_type_matches": gate is not None and marker.get("action_type") == gate.action_type,
        "marker_decision_matches_approval": bool(marker_decision) and marker_decision == approval_decision,
        "marker_scope_one_gate": marker.get("marker_scope") == "one_workflow_pack_gate_only",
        "marker_reserved": marker.get("exact_once_marker_reserved") is True,
        "marker_false_authority_flags": all(marker.get(key) is False for key in _FALSE_MARKER_FLAGS),
        "approval_artifact_path_matches_marker": (
            bool(approval_rel)
            and (
                not marker.get("approval_artifact_path")
                or str(marker.get("approval_artifact_path")) == approval_rel
            )
        ),
        "exact_once_marker_path_matches_artifact": (
            bool(marker_rel)
            and (
                not approval.get("exact_once_marker_path")
                or str(approval.get("exact_once_marker_path")) == marker_rel
            )
            and (
                not marker.get("exact_once_marker_path")
                or str(marker.get("exact_once_marker_path")) == marker_rel
            )
        ),
        "current_gate_still_pending": gate_was_pending,
        "local_resume_not_already_recorded": existing_resume_payload is None,
        "operator_statement_matches": (not execute_resume) or provided_statement == expected_statement,
        "executed_by_present": (not execute_resume) or bool(executed_by),
    }


def _approval_ref_status(run: WorkflowRun | None, gate_id: str) -> str:
    if run is None or not gate_id:
        return ""
    ref = next((item for item in run.approval_refs if item.id == gate_id), None)
    return ref.status if ref else ""


def _resume_evidence_payload(
    *,
    generated_at: str,
    packet_id: str,
    request_digest: str,
    run: WorkflowRun | None,
    gate: ApprovalGate | None,
    approval_decision: str,
    approval_artifact_path: str,
    marker_path: str,
    resume_path: str,
    executed_by: str,
    operator_statement: str,
    before_state: dict[str, Any],
    after_state: dict[str, Any],
) -> dict[str, Any]:
    return {
        "record_type": RESUME_RECORD_TYPE,
        "model_version": MODEL_VERSION,
        "generated_at": generated_at,
        "status": REJECTED_STATUS if approval_decision == "rejected" else EXECUTED_STATUS,
        "approval_packet_id": packet_id,
        "request_digest": request_digest,
        "run_id": run.id if run else "",
        "pack_id": run.pack_id if run else "",
        "gate_id": gate.id if gate else "",
        "action_type": gate.action_type if gate else "",
        "operator_decision": approval_decision,
        "approval_scope": "one_workflow_pack_gate_only",
        "approval_artifact_path": approval_artifact_path,
        "exact_once_marker_path": marker_path,
        "local_resume_evidence_path": resume_path,
        "consumed_by": executed_by,
        "consumed_at": generated_at,
        "resumed_by": executed_by,
        "resumed_at": generated_at,
        "operator_statement": operator_statement,
        "before_state": before_state,
        "after_state": after_state,
        "approval_decision_consumed": True,
        "approval_consumption_performed": True,
        "idempotency_marker_reserved": True,
        "exact_once_marker_reserved": True,
        "resume_execution_performed": True,
        "local_resume_execution_performed": True,
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
        "mutates_approval_gate": True,
        "mutates_workflow_run": True,
        "local_resume_only": True,
        "duplicate_policy": "block_existing_local_resume_evidence_or_non_pending_gate",
        "next_recommended_pass": NEXT_VERIFICATION_PASS,
    }
