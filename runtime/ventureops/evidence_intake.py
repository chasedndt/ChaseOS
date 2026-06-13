"""Combined operator evidence intake for VentureOps proof sequencing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.ventureops.validation import (
    validate_live_client_workflow_proof_artifact,
    validate_live_delivery_proof_artifact,
    validate_live_revenue_evidence,
    validate_real_client_scope_evidence,
    validate_scope_evidence_approval_artifact,
    validate_scope_evidence_source_paths,
)


def _load_json_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not contain a JSON object")
    return data


def _relative_to_root(path_value: str, root: Path) -> str:
    path = Path(path_value)
    resolved = path.resolve() if path.is_absolute() else (root / path).resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{path_value} escapes vault root") from exc
    return str(relative).replace("\\", "/")


def build_evidence_intake(
    vault_root: Path,
    *,
    scope_packet_path: str | None = None,
    revenue_packet_path: str | None = None,
    live_client_proof_path: str | None = None,
) -> dict[str, Any]:
    """Validate supplied operator packets and return the next safe proof step.

    This function is deliberately intake-only. It does not run workflows, send
    externally, mutate CRM/payment systems, or create revenue/accounting claims.
    """
    root = vault_root.resolve()
    blockers: list[str] = []
    warnings: list[str] = []
    scope_validation: dict[str, Any] = {
        "ok": False,
        "errors": ["real client scope evidence packet missing"],
        "approved_read_path_count": 0,
        "safe_read_paths": [],
    }
    approval_validation: dict[str, Any] = {
        "ok": False,
        "errors": ["real client scope evidence packet missing"],
        "scope_approval_artifact_valid": False,
    }
    source_validation: dict[str, Any] = {
        "ok": False,
        "errors": ["real client scope evidence packet missing"],
        "existing_source_count": 0,
        "existing_sources": [],
    }
    revenue_validation: dict[str, Any] = {
        "ok": False,
        "errors": ["live revenue evidence packet missing"],
        "amount": 0.0,
        "currency": "",
        "receipt_artifact_path": "",
        "delivery_proof_path": "",
    }
    scope_packet_relative = None
    revenue_packet_relative = None
    live_client_proof_relative = None
    live_client_proof_validation: dict[str, Any] = {
        "ok": False,
        "errors": ["live client proof artifact missing"],
        "client_approved_scope_id": "",
        "approved_read_path_count": 0,
        "safe_read_paths": [],
    }
    delivery_proof_validation: dict[str, Any] = {
        "ok": False,
        "errors": ["delivery proof artifact missing"],
    }

    if scope_packet_path:
        scope_packet_relative = _relative_to_root(scope_packet_path, root)
        scope_packet = _load_json_object(root / scope_packet_relative)
        scope_validation = validate_real_client_scope_evidence(scope_packet)
        blockers.extend(scope_validation["errors"])
        if scope_validation["ok"]:
            approval_validation = validate_scope_evidence_approval_artifact(root, scope_packet)
            if not approval_validation["ok"]:
                blockers.extend(approval_validation["errors"])
            source_validation = validate_scope_evidence_source_paths(root, scope_validation["safe_read_paths"])
            if not source_validation["ok"]:
                blockers.extend(source_validation["errors"])
    else:
        blockers.append("real client scope evidence packet missing")

    if revenue_packet_path:
        revenue_packet_relative = _relative_to_root(revenue_packet_path, root)
        revenue_validation = validate_live_revenue_evidence(_load_json_object(root / revenue_packet_relative))
        blockers.extend(revenue_validation["errors"])

    if live_client_proof_path:
        live_client_proof_relative = _relative_to_root(live_client_proof_path, root)

    receipt_path = str(revenue_validation.get("receipt_artifact_path") or "")
    delivery_path = str(revenue_validation.get("delivery_proof_path") or "")
    receipt_present = bool(receipt_path) and (root / receipt_path).exists()
    delivery_present = bool(delivery_path) and (root / delivery_path).exists()
    delivery_valid = False
    if delivery_present:
        delivery_proof_validation = validate_live_delivery_proof_artifact(_load_json_object(root / delivery_path))
        delivery_valid = bool(delivery_proof_validation["ok"])
    live_client_proof_present = bool(live_client_proof_relative) and (root / live_client_proof_relative).exists()
    if live_client_proof_present:
        live_client_proof_validation = validate_live_client_workflow_proof_artifact(
            _load_json_object(root / str(live_client_proof_relative))
        )

    if revenue_packet_path and revenue_validation["ok"]:
        if not receipt_present:
            blockers.append(f"receipt artifact missing: {receipt_path}")
        if not delivery_present:
            blockers.append(f"delivery proof artifact missing: {delivery_path}")
        elif not delivery_valid:
            blockers.append("delivery proof artifact invalid")
            blockers.extend(delivery_proof_validation["errors"])
        if not live_client_proof_present:
            blockers.append("live client proof artifact missing")
        elif not live_client_proof_validation["ok"]:
            blockers.extend(live_client_proof_validation["errors"])
    elif not revenue_packet_path:
        warnings.append("live revenue evidence packet not supplied")

    scope_ready = bool(scope_validation["ok"] and approval_validation["ok"] and source_validation["ok"])
    revenue_ready = bool(
        revenue_packet_path
        and revenue_validation["ok"]
        and receipt_present
        and delivery_present
        and delivery_valid
        and live_client_proof_present
        and live_client_proof_validation["ok"]
    )
    if revenue_ready:
        intake_status = "ready_for_live_revenue_proof"
        next_required_action = "run live-revenue-proof with --execute-proof"
        next_command = (
            "chaseos ventureops live-revenue-proof "
            f"--revenue-packet {revenue_packet_relative} "
            f"--live-client-proof-path {live_client_proof_relative} "
            "--execute-proof --json"
        )
    elif scope_ready:
        intake_status = "ready_for_live_client_workflow_proof"
        next_required_action = "run live-client-workflow-proof with --execute-proof"
        next_command = (
            "chaseos ventureops live-client-workflow-proof "
            f"--scope-packet {scope_packet_relative} --execute-proof --json"
        )
    else:
        intake_status = "blocked"
        next_required_action = "collect real-client scope inputs through real-client-input-manifest"
        next_command = (
            "chaseos ventureops real-client-input-manifest --client-label LABEL "
            "--scope-id ID --approval-id ID --approved-read-path PATH "
            "--approval-output PATH --scope-packet-output PATH --json"
        )

    return {
        "ok": True,
        "intake_status": intake_status,
        "scope_packet_present": bool(scope_packet_path),
        "scope_packet_path": scope_packet_relative,
        "scope_evidence_valid": bool(scope_validation["ok"]),
        "scope_validation": scope_validation,
        "scope_approval_artifact_valid": bool(approval_validation.get("scope_approval_artifact_valid")),
        "scope_approval_validation": approval_validation,
        "scope_sources_valid": bool(source_validation["ok"]),
        "scope_source_validation": source_validation,
        "revenue_packet_present": bool(revenue_packet_path),
        "revenue_packet_path": revenue_packet_relative,
        "revenue_evidence_valid": bool(revenue_validation["ok"]),
        "revenue_validation": revenue_validation,
        "receipt_artifact_present": receipt_present,
        "delivery_proof_artifact_present": delivery_present,
        "delivery_proof_artifact_valid": delivery_valid,
        "delivery_proof_validation": delivery_proof_validation,
        "live_client_proof_path": live_client_proof_relative,
        "live_client_proof_artifact_present": live_client_proof_present,
        "live_client_proof_artifact_valid": bool(live_client_proof_validation["ok"]),
        "live_client_proof_validation": live_client_proof_validation,
        "ready_for_live_client_scope_proof_gate": scope_ready,
        "ready_for_live_client_workflow_proof": scope_ready,
        "ready_for_live_revenue_proof": revenue_ready,
        "next_required_action": next_required_action,
        "next_command": next_command,
        "blockers": blockers,
        "warnings": warnings,
        "live_client_scope_proof_performed": False,
        "live_client_workflow_proof_performed": False,
        "live_client_data_ingested": False,
        "live_external_delivery_performed": False,
        "external_send_performed": False,
        "payment_mutation_performed": False,
        "crm_mutation_performed": False,
        "invoice_sent": False,
        "provider_calls": 0,
        "browser_actions": 0,
        "revenue_claim_made": False,
        "boundary": (
            "operator evidence intake only; validates packet/prerequisite shape and recommends the next guarded "
            "command without running live client or revenue workflows, sending externally, mutating CRM/payment, "
            "calling providers/browsers, sending invoices, or making revenue/accounting claims"
        ),
    }
