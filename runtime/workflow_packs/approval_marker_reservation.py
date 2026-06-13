"""Exact-once marker reservation for Workflow Pack approval packets.

This pass creates one scoped marker for a validated Workflow Pack approval
review artifact. It does not consume the approval decision, mutate the approval
gate, mutate the workflow run, or resume any Workflow Pack execution.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .approval_consumption_dry_run import (
    build_approval_consumption_dry_run,
)
from .approval_resume_contract import BLOCKED_AUTHORITY, NO_OP_BOUNDARIES


MODEL_VERSION = "workflow_packs.approval_marker_reservation.v1"
SURFACE_ID = "workflow_packs_approval_marker_reservation"
MARKER_RECORD_TYPE = "workflow_pack_approval_consumption_exact_once_marker"
READY_STATUS = "ready_to_reserve_workflow_pack_exact_once_marker_no_resume"
WRITTEN_STATUS = "workflow_pack_exact_once_marker_reserved_no_resume"
BLOCKED_STATUS = "blocked_workflow_pack_exact_once_marker_reservation"
MARKER_RESERVATION_PASS = "product-workflow-packs-approval-consumption-exact-once-marker-reservation"
NEXT_RESUME_PASS = "product-workflow-packs-approved-local-resume-executor"
BLOCKED_PASS = "product-workflow-packs-approval-consumption-exact-once-dry-run"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _resolve_vault_relative_path(vault: Path, path_value: str) -> Path:
    raw = str(path_value or "").strip()
    if not raw:
        raise ValueError("exact_once_marker_path is empty.")
    path = Path(raw)
    resolved = path.resolve() if path.is_absolute() else (vault / path).resolve()
    try:
        resolved.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError(f"Workflow Pack exact-once marker path escapes vault: {path_value}") from exc
    return resolved


def _read_json(path: Path) -> dict[str, Any] | None:
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
        raise ValueError(f"Workflow Pack exact-once marker already exists: {path}") from exc
    return "exact_once_marker_written"


def required_marker_reservation_statement(*, approval_packet_id: str, request_digest: str) -> str:
    """Return the exact statement required before reserving an exact-once marker."""

    return f"RESERVE WORKFLOW PACK EXACT-ONCE MARKER ONLY: {approval_packet_id} {request_digest}"


def build_approval_marker_reservation(
    vault_root: str | Path,
    *,
    run_id: str = "",
    gate_id: str = "",
    request_digest: str = "",
    approval_artifact_path: str = "",
    expected_decision: str = "",
    reserve_marker: bool = False,
    operator_statement: str = "",
    reserved_by: str = "operator",
    generated_at: str = "",
) -> dict[str, Any]:
    """Preview or create one exact-once marker without approval consumption or resume."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    reserver = str(reserved_by or "").strip()
    provided_statement = str(operator_statement or "").strip()

    dry_run = build_approval_consumption_dry_run(
        vault,
        run_id=str(run_id or ""),
        gate_id=str(gate_id or ""),
        request_digest=str(request_digest or ""),
        approval_artifact_path=str(approval_artifact_path or ""),
        expected_decision=str(expected_decision or ""),
        generated_at=timestamp,
    )
    dry_summary = dry_run.get("summary") or {}
    marker_contract = dry_run.get("exact_once_marker_contract") or {}
    approval_artifact = dry_run.get("approval_artifact") or {}
    packet_id = str(dry_summary.get("approval_packet_id") or "")
    digest = str(dry_summary.get("request_digest") or "")
    expected_statement = (
        required_marker_reservation_statement(approval_packet_id=packet_id, request_digest=digest)
        if packet_id and digest
        else ""
    )

    blockers = list(dry_run.get("blockers") or [])
    if not dry_run.get("ok"):
        blockers.append("Workflow Pack approval-consumption dry-run is not ready for marker reservation.")
    if reserve_marker and provided_statement != expected_statement:
        blockers.append("operator_statement must exactly match the required Workflow Pack marker reservation statement.")
    if reserve_marker and not reserver:
        blockers.append("reserved_by is required before reserving a Workflow Pack exact-once marker.")

    marker_path: Path | None = None
    marker_path_value = str(marker_contract.get("path") or "")
    if marker_path_value:
        try:
            marker_path = _resolve_vault_relative_path(vault, marker_path_value)
        except ValueError as exc:
            blockers.append(str(exc))
    else:
        blockers.append("Workflow Pack exact-once marker path is missing.")

    existing_marker_payload = _read_json(marker_path) if marker_path and marker_path.exists() else None
    if existing_marker_payload is not None:
        blockers.append("Workflow Pack exact-once marker already exists.")

    blockers = list(dict.fromkeys(blockers))

    marker_payload = (
        _marker_payload(
            generated_at=timestamp,
            dry_run=dry_run,
            marker_path=_relative_to_vault(vault, marker_path) if marker_path else "",
            operator_statement=expected_statement,
            reserved_by=reserver or "operator",
        )
        if packet_id and digest
        else {}
    )

    write_status = "not_requested"
    writes_performed = False
    if not blockers and reserve_marker and marker_path is not None:
        try:
            write_status = _write_json_create_only(marker_path, marker_payload)
            writes_performed = True
        except ValueError as exc:
            blockers.append(str(exc))
            write_status = "blocked_existing_marker"

    ok = not blockers
    status = WRITTEN_STATUS if ok and writes_performed else READY_STATUS if ok else BLOCKED_STATUS
    marker_exists_after = bool(marker_path and marker_path.exists())
    marker_reserved = bool(writes_performed and marker_exists_after)
    authority = {
        **dict(BLOCKED_AUTHORITY),
        "approval_resume_contract_preview_only": False,
        "approval_review_artifact_writer": False,
        "approval_consumption_dry_run_only": False,
        "approval_marker_reservation": True,
        "validates_approval_artifact": True,
        "creates_approval_artifact": False,
        "writes_approval_artifact": False,
        "grants_approval": False,
        "mutates_approval_gate": False,
        "mutates_workflow_run": False,
        "consumes_approval_decision": False,
        "reserves_exact_once_marker": marker_reserved,
        "writes_exact_once_marker": marker_reserved,
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
            "run_id": str(dry_summary.get("run_id") or ""),
            "pack_id": str(dry_summary.get("pack_id") or ""),
            "gate_id": str(dry_summary.get("gate_id") or ""),
            "gate_status": str(dry_summary.get("gate_status") or ""),
            "action_type": str(dry_summary.get("action_type") or ""),
            "approval_packet_id": packet_id,
            "request_digest": digest,
            "operator_decision": str(dry_summary.get("operator_decision") or ""),
            "approval_marker_reservation_ready": ok,
            "approval_artifact_present": bool(dry_summary.get("approval_artifact_present")),
            "approval_digest_matches": bool(dry_summary.get("approval_digest_matches")),
            "approval_scope_valid": bool(dry_summary.get("approval_scope_valid")),
            "future_single_workflow_pack_gate_approved": bool(
                dry_summary.get("future_single_workflow_pack_gate_approved")
            ),
            "future_single_workflow_pack_gate_rejected": bool(
                dry_summary.get("future_single_workflow_pack_gate_rejected")
            ),
            "exact_once_marker_required": True,
            "exact_once_marker_absent_before": bool(dry_summary.get("exact_once_marker_absent")),
            "exact_once_marker_reserved": marker_reserved,
            "exact_once_marker_written": writes_performed,
            "marker_write_status": write_status,
            "approval_decision_consumed": False,
            "approval_consumption_performed": False,
            "resume_execution_performed": False,
            "external_actions_performed": False,
            "provider_calls_performed": False,
            "browser_actions_performed": False,
            "agent_bus_dispatch_performed": False,
            "canonical_promotion_performed": False,
            "policy_mutation_performed": False,
            "writes_performed": writes_performed,
            "next_recommended_pass": (
                NEXT_RESUME_PASS if marker_reserved else MARKER_RESERVATION_PASS if ok else BLOCKED_PASS
            ),
        },
        "source_dry_run": dry_run,
        "approval_artifact": {
            "path": str(approval_artifact.get("path") or ""),
            "exists": bool(approval_artifact.get("exists")),
            "consumed_in_this_pass": False,
            "mutated_in_this_pass": False,
        },
        "exact_once_marker": {
            "path": _relative_to_vault(vault, marker_path) if marker_path else marker_path_value,
            "exists_before": existing_marker_payload is not None,
            "exists_after": marker_exists_after,
            "write_requested": bool(reserve_marker),
            "write_status": write_status,
            "reserved_in_this_pass": marker_reserved,
            "written_in_this_pass": writes_performed,
            "record_type": MARKER_RECORD_TYPE if marker_payload else "",
            "required_operator_statement": expected_statement,
            "write_mode": "atomic_create_new_only_before_any_workflow_pack_resume",
            "duplicate_policy": "block_before_any_workflow_pack_resume",
        },
        "exact_once_marker_payload": marker_payload,
        "checks": {
            "source_dry_run_ready": dry_run.get("ok") is True,
            "request_digest_matches": bool(dry_summary.get("approval_digest_matches")),
            "approval_scope_valid": bool(dry_summary.get("approval_scope_valid")),
            "marker_path_available": bool(marker_path),
            "marker_absent_before_write": existing_marker_payload is None and bool(
                dry_summary.get("exact_once_marker_absent")
            ),
            "operator_statement_matches": (not reserve_marker) or provided_statement == expected_statement,
            "reserved_by_present": (not reserve_marker) or bool(reserver),
            "marker_reserved_in_this_pass": marker_reserved,
            "approval_decision_consumed": False,
            "approval_consumption_performed": False,
            "resume_execution_performed": False,
            "no_gate_mutation_in_this_pass": True,
            "no_run_mutation_in_this_pass": True,
            "no_external_action_in_this_pass": True,
        },
        "authority": authority,
        "blocked_authority": [key for key, value in authority.items() if value is False],
        "safety": {
            "approval_marker_reservation_only": True,
            "validates_approval_artifact": True,
            "creates_approval_artifact": False,
            "writes_approval_artifact": False,
            "grants_approval": False,
            "mutates_approval_gate": False,
            "mutates_workflow_run": False,
            "consumes_approval_decision": False,
            "reserves_exact_once_marker": marker_reserved,
            "writes_exact_once_marker": marker_reserved,
            "executes_resume": False,
            "external_actions_performed": False,
            "provider_calls_performed": False,
            "browser_actions_performed": False,
            "agent_bus_dispatch_performed": False,
            "email_send_performed": False,
            "publish_content_performed": False,
            "canonical_promotion_performed": False,
            "policy_mutation_performed": False,
            "secret_or_credential_accessed": False,
            "blocked_authority": dict(BLOCKED_AUTHORITY),
            "no_op_boundaries": list(NO_OP_BOUNDARIES),
        },
        "blockers": blockers,
        "unverified": [
            "No approval decision was consumed in this marker-reservation pass.",
            "No Workflow Pack run was resumed in this marker-reservation pass.",
            "No approval gate or Workflow Pack run state was mutated.",
            "No runtime, Agent Bus, provider, browser, email, publish, graph, canonical, policy, secret, or credential action was attempted.",
        ],
        "writes_performed": writes_performed,
        "next_recommended_pass": NEXT_RESUME_PASS if marker_reserved else MARKER_RESERVATION_PASS if ok else BLOCKED_PASS,
    }


def _marker_payload(
    *,
    generated_at: str,
    dry_run: dict[str, Any],
    marker_path: str,
    operator_statement: str,
    reserved_by: str,
) -> dict[str, Any]:
    summary = dry_run.get("summary") or {}
    approval_artifact = dry_run.get("approval_artifact") or {}
    return {
        "record_type": MARKER_RECORD_TYPE,
        "model_version": MODEL_VERSION,
        "generated_at": generated_at,
        "status": WRITTEN_STATUS,
        "approval_packet_id": str(summary.get("approval_packet_id") or ""),
        "request_digest": str(summary.get("request_digest") or ""),
        "run_id": str(summary.get("run_id") or ""),
        "pack_id": str(summary.get("pack_id") or ""),
        "gate_id": str(summary.get("gate_id") or ""),
        "gate_status_at_reservation": str(summary.get("gate_status") or ""),
        "action_type": str(summary.get("action_type") or ""),
        "operator_decision": str(summary.get("operator_decision") or ""),
        "approval_artifact_path": str(approval_artifact.get("path") or ""),
        "exact_once_marker_path": marker_path,
        "approval_scope": "one_workflow_pack_gate_only",
        "marker_scope": "one_workflow_pack_gate_only",
        "reserved_by": reserved_by,
        "reserved_at": generated_at,
        "operator_statement": operator_statement,
        "approval_consumption_required": True,
        "approval_consumption_allowed": False,
        "approval_consumption_performed": False,
        "approval_decision_consumed": False,
        "idempotency_marker_reserved": True,
        "exact_once_marker_reserved": True,
        "marker_reserved_in_this_pass": True,
        "resume_execution_allowed": False,
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
        "source_dry_run_status": str(dry_run.get("status") or ""),
        "source_dry_run_summary": dict(summary),
        "no_op_boundaries": list(NO_OP_BOUNDARIES),
        "next_recommended_pass": NEXT_RESUME_PASS,
    }
