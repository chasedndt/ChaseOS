"""Read-only approval-consumption dry-run for Workflow Packs.

This pass validates that a written Workflow Pack approval review artifact is
ready for a future exact-once consumption pass. It performs no writes, does not
reserve the marker, does not mutate the approval gate, and does not resume a
Workflow Pack run.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .approval_resume_contract import (
    BLOCKED_AUTHORITY,
    NO_OP_BOUNDARIES,
    build_approval_resume_contract,
)
from .approval_review_artifact import (
    APPROVAL_RECORD_TYPE,
    MODEL_VERSION as REVIEW_ARTIFACT_MODEL_VERSION,
)
from .store import WorkflowPackStore


MODEL_VERSION = "workflow_packs.approval_consumption_dry_run.v1"
SURFACE_ID = "workflow_packs_approval_consumption_dry_run"
READY_STATUS = "workflow_pack_approval_consumption_dry_run_ready_no_execution"
REJECTION_READY_STATUS = "workflow_pack_rejection_consumption_dry_run_ready_no_execution"
BLOCKED_STATUS = "blocked_workflow_pack_approval_consumption_dry_run"
NEXT_EXACT_ONCE_MARKER_PASS = "product-workflow-packs-approval-consumption-exact-once-marker-reservation"
BLOCKED_PASS = "product-workflow-packs-approval-review-artifact-writer"


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


def _resolve_vault_relative_path(vault: Path, path_value: str) -> Path:
    raw = str(path_value or "").strip()
    if not raw:
        raise ValueError("approval_artifact_path is empty.")
    path = Path(raw)
    resolved = path.resolve() if path.is_absolute() else (vault / path).resolve()
    try:
        resolved.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError(f"Workflow Pack approval artifact path escapes vault: {path_value}") from exc
    return resolved


def _marker_reservation_dry_run(marker_exists: bool) -> dict[str, Any]:
    first_reservation_allowed = not marker_exists
    return {
        "proof_mode": "in_memory_no_real_marker_write",
        "real_marker_written": False,
        "real_marker_reserved": False,
        "marker_exists_before": bool(marker_exists),
        "first_reservation_allowed": first_reservation_allowed,
        "first_reservation_status": "would_reserve_exclusively" if first_reservation_allowed else "blocked_existing_marker",
        "duplicate_reservation_blocked": True,
        "duplicate_reservation_status": "blocked_prior_marker_exists",
        "required_future_write_mode": "atomic_create_new_only_before_any_workflow_pack_resume",
        "proof_passed": first_reservation_allowed,
    }


def _approval_validation_checks(
    *,
    approval_payload: dict[str, Any] | None,
    approval_path: Path | None,
    expected_approval_path: Path | None,
    marker_path: Path | None,
    contract: dict[str, Any],
    request_digest: str,
    expected_decision: str,
) -> dict[str, bool]:
    summary = contract.get("summary") or {}
    selected_run = contract.get("selected_run") or {}
    selected_gate = contract.get("selected_gate") or {}
    future_packet = contract.get("future_resume_packet_preview") or {}
    payload = approval_payload or {}
    expected_packet_id = str(summary.get("approval_packet_id") or future_packet.get("approval_packet_id") or "")
    expected_digest = str(summary.get("request_digest") or future_packet.get("request_digest") or "")
    expected_run_id = str(selected_run.get("id") or future_packet.get("run_id") or "")
    expected_pack_id = str(selected_run.get("pack_id") or future_packet.get("pack_id") or "")
    expected_gate_id = str(selected_gate.get("id") or future_packet.get("gate_id") or "")
    expected_action_type = str(selected_gate.get("action_type") or future_packet.get("action_type") or "")
    decision = str(payload.get("operator_decision") or "")
    blocked_flags_false = all(
        payload.get(key) is False
        for key in [
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
    )

    return {
        "contract_preview_ready": bool(future_packet),
        "request_digest_provided": bool(request_digest),
        "request_digest_matches": bool(request_digest) and request_digest == expected_digest,
        "approval_artifact_path_expected": bool(
            approval_path and expected_approval_path and approval_path.resolve() == expected_approval_path.resolve()
        ),
        "approval_artifact_present": bool(approval_path and approval_path.is_file()),
        "approval_artifact_json_readable": approval_payload is not None,
        "approval_record_type_valid": payload.get("record_type") == APPROVAL_RECORD_TYPE,
        "approval_model_version_valid": payload.get("model_version") == REVIEW_ARTIFACT_MODEL_VERSION,
        "approval_packet_id_matches": payload.get("approval_packet_id") == expected_packet_id,
        "approval_request_digest_matches": payload.get("request_digest") == expected_digest,
        "approval_run_id_matches": payload.get("run_id") == expected_run_id,
        "approval_pack_id_matches": payload.get("pack_id") == expected_pack_id,
        "approval_gate_id_matches": payload.get("gate_id") == expected_gate_id,
        "approval_action_type_matches": payload.get("action_type") == expected_action_type,
        "approval_scope_one_gate": payload.get("approval_scope") == "one_workflow_pack_gate_only",
        "approval_consumption_required": payload.get("approval_consumption_required") is True,
        "approval_consumption_not_allowed_in_review": payload.get("approval_consumption_allowed") is False,
        "operator_decision_supported": decision in {"approved", "rejected"},
        "operator_decision_matches_expected": (not expected_decision) or decision == expected_decision,
        "future_single_gate_decision_consistent": (
            (decision == "approved" and payload.get("future_single_workflow_pack_gate_approved") is True)
            or (decision == "rejected" and payload.get("future_single_workflow_pack_gate_rejected") is True)
        ),
        "approval_not_already_consumed": payload.get("approval_decision_consumed") is False,
        "exact_once_marker_not_reserved_in_artifact": payload.get("exact_once_marker_reserved") is False,
        "resume_not_performed_in_artifact": payload.get("resume_execution_performed") is False,
        "review_artifact_authority_flags_blocked": blocked_flags_false,
        "current_gate_still_pending": str(selected_gate.get("status") or "") == "pending",
        "real_exact_once_marker_absent": bool(marker_path and not marker_path.exists()),
    }


def _normalize_expected_decision(expected_decision: str) -> str:
    normalized = str(expected_decision or "").strip().lower()
    if normalized == "approve":
        return "approved"
    if normalized in {"reject", "deny", "denied"}:
        return "rejected"
    return normalized


def build_approval_consumption_dry_run(
    vault_root: str | Path,
    *,
    run_id: str = "",
    gate_id: str = "",
    request_digest: str = "",
    approval_artifact_path: str = "",
    expected_decision: str = "",
    generated_at: str = "",
) -> dict[str, Any]:
    """Validate future Workflow Pack approval consumption readiness without writes."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    requested_digest = str(request_digest or "").strip()
    normalized_expected_decision = _normalize_expected_decision(expected_decision)
    blockers: list[str] = []

    if normalized_expected_decision and normalized_expected_decision not in {"approved", "rejected"}:
        blockers.append("expected_decision must be approve/approved or reject/rejected/deny/denied.")

    contract = build_approval_resume_contract(vault, run_id=str(run_id or ""), gate_id=str(gate_id or ""))
    summary = contract.get("summary") or {}
    future_packet = contract.get("future_resume_packet_preview") or {}
    selected_run = contract.get("selected_run") or {}
    selected_gate = contract.get("selected_gate") or {}
    selected_run_id = str(summary.get("run_id") or selected_run.get("id") or run_id or "")
    selected_gate_id = str(summary.get("selected_gate_id") or selected_gate.get("id") or gate_id or "")
    packet_id = str(summary.get("approval_packet_id") or future_packet.get("approval_packet_id") or "")
    expected_digest = str(summary.get("request_digest") or future_packet.get("request_digest") or "")

    store = WorkflowPackStore(vault)
    expected_approval_path: Path | None = None
    marker_path: Path | None = None
    approval_path: Path | None = None
    approval_payload: dict[str, Any] | None = None
    if selected_run_id and packet_id:
        try:
            run_dir = store.run_dir(selected_run_id)
            expected_approval_path = run_dir / "approval_reviews" / f"{packet_id}.json"
            marker_path = run_dir / "approval_execution_markers" / f"{packet_id}.json"
        except ValueError as exc:
            blockers.append(str(exc))

    if not requested_digest:
        blockers.append("request_digest is required before approval consumption dry-run validation.")
    elif expected_digest and requested_digest != expected_digest:
        blockers.append("request_digest does not match the current Workflow Pack approval packet.")

    if not future_packet:
        blockers.append("Workflow Pack approval/resume packet preview is not available for this run/gate.")
    if not packet_id or not expected_digest:
        blockers.append("Workflow Pack approval packet id or request digest is missing.")
    if not selected_run_id or not selected_gate_id:
        blockers.append("Workflow Pack run_id or gate_id is missing.")

    if approval_artifact_path:
        try:
            approval_path = _resolve_vault_relative_path(vault, approval_artifact_path)
        except ValueError as exc:
            blockers.append(str(exc))
    else:
        approval_path = expected_approval_path

    if approval_path is not None and expected_approval_path is not None:
        if approval_path.resolve() != expected_approval_path.resolve():
            blockers.append("approval_artifact_path must match the current Workflow Pack approval packet path.")

    if approval_path and approval_path.exists():
        approval_payload = _read_json(approval_path)
        if approval_payload is None:
            blockers.append("Workflow Pack approval artifact is not readable JSON.")
    else:
        blockers.append("Workflow Pack approval review artifact is missing.")

    checks = _approval_validation_checks(
        approval_payload=approval_payload,
        approval_path=approval_path,
        expected_approval_path=expected_approval_path,
        marker_path=marker_path,
        contract=contract,
        request_digest=requested_digest,
        expected_decision=normalized_expected_decision,
    )
    marker_proof = _marker_reservation_dry_run(bool(marker_path and marker_path.exists()))
    checks.update(
        {
            "marker_reservation_proof_passed": bool(marker_proof.get("proof_passed")),
            "duplicate_marker_blocked": bool(marker_proof.get("duplicate_reservation_blocked")),
            "no_real_marker_write_in_this_pass": marker_proof.get("real_marker_written") is False,
            "no_gate_mutation_in_this_pass": True,
            "no_resume_execution_in_this_pass": True,
            "no_external_action_in_this_pass": True,
        }
    )

    blockers.extend(name for name, passed in checks.items() if not passed)
    blockers = list(dict.fromkeys(blockers))
    ok = not blockers
    payload_decision = str((approval_payload or {}).get("operator_decision") or normalized_expected_decision or "")
    ready_status = REJECTION_READY_STATUS if payload_decision == "rejected" else READY_STATUS
    status = ready_status if ok else BLOCKED_STATUS
    authority = {
        **dict(BLOCKED_AUTHORITY),
        "approval_resume_contract_preview_only": False,
        "approval_review_artifact_writer": False,
        "approval_consumption_dry_run_only": True,
        "validates_approval_artifact": True,
        "simulates_marker_reservation": True,
        "simulates_duplicate_consumption_block": True,
        "creates_approval_artifact": False,
        "writes_approval_artifact": False,
        "grants_approval": False,
        "mutates_approval_gate": False,
        "consumes_approval_decision": False,
        "reserves_exact_once_marker": False,
        "writes_exact_once_marker": False,
        "executes_resume": False,
    }

    approved_ready = ok and payload_decision == "approved"
    rejected_ready = ok and payload_decision == "rejected"
    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "summary": {
            "run_id": selected_run_id,
            "pack_id": str(summary.get("pack_id") or selected_run.get("pack_id") or ""),
            "gate_id": selected_gate_id,
            "gate_status": str(selected_gate.get("status") or summary.get("selected_gate_status") or ""),
            "action_type": str(summary.get("selected_action_type") or selected_gate.get("action_type") or ""),
            "approval_packet_id": packet_id,
            "request_digest": expected_digest,
            "operator_decision": payload_decision,
            "approval_consumption_dry_run_ready": ok,
            "approval_artifact_present": checks.get("approval_artifact_present"),
            "approval_digest_matches": checks.get("approval_request_digest_matches"),
            "approval_scope_valid": checks.get("approval_scope_one_gate"),
            "future_single_workflow_pack_gate_approved": approved_ready,
            "future_single_workflow_pack_gate_rejected": rejected_ready,
            "exact_once_marker_absent": checks.get("real_exact_once_marker_absent"),
            "exact_once_marker_required": True,
            "exact_once_marker_reservation_ready": ok,
            "marker_reservation_proof_passed": checks.get("marker_reservation_proof_passed"),
            "duplicate_consumption_blocked": checks.get("duplicate_marker_blocked"),
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
            "writes_performed": False,
            "next_recommended_pass": NEXT_EXACT_ONCE_MARKER_PASS if ok else BLOCKED_PASS,
        },
        "source_contract": contract,
        "approval_artifact": {
            "path": _relative_to_vault(vault, approval_path) if approval_path else "",
            "expected_path": _relative_to_vault(vault, expected_approval_path) if expected_approval_path else "",
            "exists": bool(approval_path and approval_path.is_file()),
            "json_readable": approval_payload is not None,
            "record_type": approval_payload.get("record_type") if approval_payload else None,
            "model_version": approval_payload.get("model_version") if approval_payload else None,
            "approval_packet_id": approval_payload.get("approval_packet_id") if approval_payload else None,
            "request_digest": approval_payload.get("request_digest") if approval_payload else None,
            "operator_decision": approval_payload.get("operator_decision") if approval_payload else None,
            "approval_scope": approval_payload.get("approval_scope") if approval_payload else None,
            "consumed_in_this_pass": False,
            "mutated_in_this_pass": False,
        },
        "exact_once_marker_contract": {
            "path": _relative_to_vault(vault, marker_path) if marker_path else "",
            "exists": bool(marker_path and marker_path.exists()),
            "reserved_in_this_pass": False,
            "written_in_this_pass": False,
            "future_write_mode": "atomic_create_new_only_before_any_workflow_pack_resume",
            "duplicate_policy": "block_before_any_workflow_pack_resume",
        },
        "marker_reservation_dry_run": marker_proof,
        "dry_run_plan": [
            {"step": "load_scoped_approval_review_artifact", "effect_now": "read_only_validation", "required": True},
            {"step": "validate_packet_digest_and_scope", "effect_now": "read_only_validation", "required": True},
            {"step": "verify_current_gate_is_still_pending", "effect_now": "read_only_validation", "required": True},
            {"step": "verify_real_exact_once_marker_absent", "effect_now": "read_only_validation", "required": True},
            {"step": "simulate_exclusive_marker_reservation", "effect_now": "in_memory_no_write", "required": True},
            {"step": "simulate_duplicate_consumption_block", "effect_now": "in_memory_no_write", "required": True},
            {"step": "stop_before_marker_gate_mutation_or_resume", "effect_now": "execution_block", "required": True},
        ],
        "checks": checks,
        "authority": authority,
        "blocked_authority": [key for key, value in authority.items() if value is False],
        "safety": {
            "approval_consumption_dry_run_only": True,
            "validates_approval_artifact": True,
            "simulates_marker_reservation": True,
            "creates_approval_artifact": False,
            "writes_approval_artifact": False,
            "grants_approval": False,
            "mutates_approval_gate": False,
            "consumes_approval_decision": False,
            "reserves_exact_once_marker": False,
            "writes_exact_once_marker": False,
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
            "No approval decision was consumed in this dry-run pass.",
            "No real exact-once marker was reserved or written in this dry-run pass.",
            "No Workflow Pack run was resumed in this dry-run pass.",
            "No runtime, Agent Bus, provider, browser, email, publish, graph, canonical, policy, secret, or credential action was attempted.",
        ],
        "writes_performed": False,
        "next_recommended_pass": NEXT_EXACT_ONCE_MARKER_PASS if ok else BLOCKED_PASS,
    }
