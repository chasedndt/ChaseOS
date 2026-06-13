"""Guarded execution helper for the VentureOps live client scope proof gate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.aor import run_workflow
from runtime.ventureops.validation import (
    validate_real_client_scope_evidence,
    validate_scope_evidence_approval_artifact,
    validate_scope_evidence_source_paths,
)


WORKFLOW_ID = "agent_runtime_governance_audit"


def _load_scope_packet(path: Path) -> dict[str, Any]:
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


def build_live_client_scope_proof_inputs(
    *,
    scope_packet_relative_path: str,
    scope_validation: dict[str, Any],
    run_id: str,
    run_date: str,
) -> dict[str, Any]:
    """Build the AOR input packet for the no-external-send scope proof gate."""
    return {
        "run_id": run_id,
        "date": run_date,
        "source_paths": scope_validation["safe_read_paths"],
        "include_offer_packet": "true",
        "include_delivery_approval_contract": "true",
        "include_delivery_packet_preview": "true",
        "include_approval_request_artifact": "true",
        "include_approval_consumption_proof": "true",
        "include_exact_once_delivery_gate": "true",
        "include_external_send_dry_run": "true",
        "include_approved_external_send_proof": "true",
        "include_crm_draft": "true",
        "include_payment_invoice_draft": "true",
        "include_workflow_exchange_publication_preview": "true",
        "include_live_client_scope_contract": "true",
        "include_live_client_scope_proof_gate": "true",
        "real_client_scope_evidence_path": scope_packet_relative_path,
        "approval_request_run_id": run_id,
        "approval_decision_id": f"{run_id}-operator-decision",
        "approval_decision": "approved",
        "external_send_approval_id": f"{run_id}-local-proof-sink-approval",
        "external_send_approval_decision": "approved",
        "external_delivery_channel": "local-proof-sink",
        "external_recipient_route": "no-external-route.invalid",
    }


def run_live_client_scope_proof(
    vault_root: Path,
    *,
    scope_packet_path: str,
    run_id: str = "live-client-scope-proof",
    run_date: str,
    execute_proof: bool = False,
) -> dict[str, Any]:
    """Run the guarded scope proof gate only after explicit execute approval."""
    root = vault_root.resolve()
    if not execute_proof:
        return {
            "ok": False,
            "error": "live-client-scope-proof requires --execute-proof",
            "workflow_status": "not_run",
            "writes_performed": False,
            "files_written": [],
            "proof_gate_path": None,
            "live_client_scope_proof_gate_written": False,
            "live_client_scope_proof_performed": False,
            "live_client_data_ingested": False,
            "live_external_delivery_performed": False,
            "external_send_performed": False,
            "crm_mutation_performed": False,
            "payment_mutation_performed": False,
            "revenue_claim_made": False,
            "boundary": "blocked until explicit --execute-proof is supplied",
        }

    scope_packet_relative = _relative_to_root(scope_packet_path, root)
    scope_packet = _load_scope_packet(root / scope_packet_relative)
    scope_validation = validate_real_client_scope_evidence(scope_packet)
    if not scope_validation["ok"]:
        return {
            "ok": False,
            "error": "real client scope evidence invalid",
            "errors": scope_validation["errors"],
            "scope_packet_path": scope_packet_relative,
            "workflow_status": "not_run",
            "writes_performed": False,
            "files_written": [],
            "proof_gate_path": None,
            "live_client_scope_proof_gate_written": False,
            "live_client_scope_proof_performed": False,
            "live_client_data_ingested": False,
            "live_external_delivery_performed": False,
            "external_send_performed": False,
            "crm_mutation_performed": False,
            "payment_mutation_performed": False,
            "revenue_claim_made": False,
            "boundary": "invalid scope evidence; no workflow run performed",
        }
    approval_validation = validate_scope_evidence_approval_artifact(root, scope_packet)
    if not approval_validation["ok"]:
        return {
            "ok": False,
            "error": "real client scope approval artifact invalid",
            "errors": approval_validation["errors"],
            "scope_packet_path": scope_packet_relative,
            "workflow_status": "not_run",
            "writes_performed": False,
            "files_written": [],
            "proof_gate_path": None,
            "live_client_scope_proof_gate_written": False,
            "live_client_scope_proof_performed": False,
            "live_client_data_ingested": False,
            "live_external_delivery_performed": False,
            "external_send_performed": False,
            "crm_mutation_performed": False,
            "payment_mutation_performed": False,
            "revenue_claim_made": False,
            "boundary": "invalid scope approval artifact; no workflow run performed",
        }
    source_validation = validate_scope_evidence_source_paths(root, scope_validation["safe_read_paths"])
    if not source_validation["ok"]:
        return {
            "ok": False,
            "error": "approved scope source paths invalid",
            "errors": source_validation["errors"],
            "scope_packet_path": scope_packet_relative,
            "workflow_status": "not_run",
            "writes_performed": False,
            "files_written": [],
            "proof_gate_path": None,
            "live_client_scope_proof_gate_written": False,
            "live_client_scope_proof_performed": False,
            "live_client_data_ingested": False,
            "live_external_delivery_performed": False,
            "external_send_performed": False,
            "crm_mutation_performed": False,
            "payment_mutation_performed": False,
            "revenue_claim_made": False,
            "boundary": "approved scope source paths invalid; no workflow run performed",
        }

    expected_proof_gate_path = (
        f"07_LOGS/Workflow-Proofs/{run_date}_{WORKFLOW_ID}_{run_id}_live-client-scope-proof-gate.json"
    )
    if (root / expected_proof_gate_path).exists():
        return {
            "ok": False,
            "error": "proof output path already exists",
            "errors": [f"proof output path already exists: {expected_proof_gate_path}"],
            "workflow_status": "not_run",
            "scope_packet_path": scope_packet_relative,
            "scope_evidence_valid": True,
            "approved_read_path_count": scope_validation["approved_read_path_count"],
            "writes_performed": False,
            "files_written": [],
            "proof_gate_path": expected_proof_gate_path,
            "live_client_scope_proof_gate_written": False,
            "live_client_scope_proof_performed": False,
            "live_client_data_ingested": False,
            "live_external_delivery_performed": False,
            "external_send_performed": False,
            "crm_mutation_performed": False,
            "payment_mutation_performed": False,
            "revenue_claim_made": False,
            "boundary": "proof output collision; no workflow run performed",
        }

    workflow_inputs = build_live_client_scope_proof_inputs(
        scope_packet_relative_path=scope_packet_relative,
        scope_validation=scope_validation,
        run_id=run_id,
        run_date=run_date,
    )
    result = run_workflow(
        WORKFLOW_ID,
        inputs=workflow_inputs,
        vault_root=root,
        dry_run=False,
        runtime_id="codex",
    )
    run_outputs = result.outputs.get("run", {}) if isinstance(result.outputs, dict) else {}
    writeback = result.outputs.get("writeback", {}) if isinstance(result.outputs, dict) else {}
    files_written = list(writeback.get("files_written") or [])
    proof_gate_path = run_outputs.get("live_client_scope_proof_gate_path")
    scorecard = run_outputs.get("scorecard") if isinstance(run_outputs, dict) else {}
    metrics = scorecard.get("metrics", {}) if isinstance(scorecard, dict) else {}
    ok = result.status == "success" and bool(proof_gate_path)
    return {
        "ok": ok,
        "workflow_id": WORKFLOW_ID,
        "workflow_status": result.status,
        "audit_id": result.audit_id,
        "stage_reached": result.stage_reached,
        "error": result.error or result.escalation_reason,
        "scope_packet_path": scope_packet_relative,
        "scope_evidence_valid": True,
        "approved_read_path_count": scope_validation["approved_read_path_count"],
        "writes_performed": bool(files_written),
        "files_written": files_written,
        "proof_path": run_outputs.get("proof_path"),
        "client_report_path": run_outputs.get("client_report_path"),
        "scorecard_path": run_outputs.get("scorecard_path"),
        "proof_gate_path": proof_gate_path,
        "live_client_scope_proof_gate_written": proof_gate_path in files_written,
        "live_client_scope_proof_performed": bool(metrics.get("live_client_scope_proof_performed")),
        "live_client_data_ingested": bool(metrics.get("live_client_data_ingested")),
        "live_external_delivery_performed": bool(metrics.get("live_external_delivery_performed")),
        "external_send_performed": bool(metrics.get("external_send_performed")),
        "crm_mutation_performed": bool(metrics.get("crm_mutation_performed")),
        "payment_mutation_performed": bool(metrics.get("payment_mutation_performed")),
        "revenue_claim_made": bool(metrics.get("revenue_claim_made")),
        "boundary": (
            "AOR proof-gate execution only; validates real client scope evidence and writes local proof artifacts "
            "without live client data ingestion, external delivery, CRM/payment mutation, or revenue claim"
        ),
    }
