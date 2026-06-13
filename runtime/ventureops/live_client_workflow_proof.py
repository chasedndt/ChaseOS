"""Guarded local proof helper for a scoped VentureOps live-client workflow."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.ventureops.live_client_scope_proof import run_live_client_scope_proof
from runtime.ventureops.validation import (
    validate_live_client_workflow_proof_artifact,
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


def _source_digests(root: Path, safe_read_paths: list[str]) -> list[dict[str, Any]]:
    digests: list[dict[str, Any]] = []
    for relative in safe_read_paths:
        source_path = root / relative
        data = source_path.read_bytes()
        digests.append(
            {
                "path": relative,
                "sha256": hashlib.sha256(data).hexdigest(),
                "byte_count": len(data),
            }
        )
    return digests


def run_live_client_workflow_proof(
    vault_root: Path,
    *,
    scope_packet_path: str,
    run_id: str = "live-client-workflow-proof",
    run_date: str,
    execute_proof: bool = False,
) -> dict[str, Any]:
    """Run a scoped local live-client workflow proof after explicit execution approval."""
    root = vault_root.resolve()
    if not execute_proof:
        return {
            "ok": False,
            "error": "live-client-workflow-proof requires --execute-proof",
            "workflow_status": "not_run",
            "writes_performed": False,
            "files_written": [],
            "workflow_proof_path": None,
            "live_client_workflow_proof_written": False,
            "live_client_workflow_proof_performed": False,
            "scoped_client_data_ingested": False,
            "broad_client_data_ingested": False,
            "live_external_delivery_performed": False,
            "external_send_performed": False,
            "crm_mutation_performed": False,
            "payment_mutation_performed": False,
            "provider_calls": 0,
            "browser_actions": 0,
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
            "workflow_proof_path": None,
            "live_client_workflow_proof_written": False,
            "live_client_workflow_proof_performed": False,
            "scoped_client_data_ingested": False,
            "broad_client_data_ingested": False,
            "live_external_delivery_performed": False,
            "external_send_performed": False,
            "crm_mutation_performed": False,
            "payment_mutation_performed": False,
            "provider_calls": 0,
            "browser_actions": 0,
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
            "workflow_proof_path": None,
            "live_client_workflow_proof_written": False,
            "live_client_workflow_proof_performed": False,
            "scoped_client_data_ingested": False,
            "broad_client_data_ingested": False,
            "live_external_delivery_performed": False,
            "external_send_performed": False,
            "crm_mutation_performed": False,
            "payment_mutation_performed": False,
            "provider_calls": 0,
            "browser_actions": 0,
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
            "workflow_proof_path": None,
            "live_client_workflow_proof_written": False,
            "live_client_workflow_proof_performed": False,
            "scoped_client_data_ingested": False,
            "broad_client_data_ingested": False,
            "live_external_delivery_performed": False,
            "external_send_performed": False,
            "crm_mutation_performed": False,
            "payment_mutation_performed": False,
            "provider_calls": 0,
            "browser_actions": 0,
            "revenue_claim_made": False,
            "boundary": "approved scope source paths invalid; no workflow run performed",
        }

    workflow_proof_path = (
        f"07_LOGS/Workflow-Proofs/{run_date}_{WORKFLOW_ID}_{run_id}_live-client-workflow-proof.json"
    )
    if (root / workflow_proof_path).exists():
        return {
            "ok": False,
            "error": "proof output path already exists",
            "errors": [f"proof output path already exists: {workflow_proof_path}"],
            "scope_packet_path": scope_packet_relative,
            "workflow_status": "not_run",
            "writes_performed": False,
            "files_written": [],
            "workflow_proof_path": workflow_proof_path,
            "live_client_workflow_proof_written": False,
            "live_client_workflow_proof_performed": False,
            "scoped_client_data_ingested": False,
            "broad_client_data_ingested": False,
            "live_external_delivery_performed": False,
            "external_send_performed": False,
            "crm_mutation_performed": False,
            "payment_mutation_performed": False,
            "provider_calls": 0,
            "browser_actions": 0,
            "revenue_claim_made": False,
            "boundary": "proof output collision; no workflow run performed",
        }

    scope_result = run_live_client_scope_proof(
        root,
        scope_packet_path=scope_packet_relative,
        run_id=run_id,
        run_date=run_date,
        execute_proof=True,
    )
    if not scope_result.get("ok"):
        return {
            **scope_result,
            "workflow_proof_path": None,
            "live_client_workflow_proof_written": False,
            "live_client_workflow_proof_performed": False,
            "scoped_client_data_ingested": False,
            "broad_client_data_ingested": False,
            "provider_calls": 0,
            "browser_actions": 0,
        }

    source_digests = _source_digests(root, scope_validation["safe_read_paths"])
    artifact = {
        "type": "ventureops-live-client-workflow-proof",
        "status": "live_client_workflow_proof_written",
        "workflow_id": WORKFLOW_ID,
        "run_id": run_id,
        "date": run_date,
        "scope_packet_path": scope_packet_relative,
        "client_approved_scope_id": str(scope_packet.get("client_approved_scope_id") or ""),
        "client_label": str(scope_packet.get("client_label") or ""),
        "approval_id": str(scope_packet.get("approval_id") or ""),
        "approval_status": str(scope_packet.get("approval_status") or ""),
        "approved_read_paths": scope_validation["safe_read_paths"],
        "approved_read_path_count": scope_validation["approved_read_path_count"],
        "source_digest_count": len(source_digests),
        "source_digests": source_digests,
        "scope_proof_gate_path": scope_result.get("proof_gate_path"),
        "proof_path": scope_result.get("proof_path"),
        "client_report_path": scope_result.get("client_report_path"),
        "scorecard_path": scope_result.get("scorecard_path"),
        "live_client_workflow_proof_performed": True,
        "scoped_client_data_ingested": True,
        "broad_client_data_ingested": False,
        "live_external_delivery_performed": False,
        "external_send_performed": False,
        "crm_mutation_performed": False,
        "payment_mutation_performed": False,
        "provider_calls": 0,
        "browser_actions": 0,
        "revenue_claim_made": False,
        "boundary": (
            "scoped local live-client workflow proof only; reads approved scope paths, writes local proof artifacts, "
            "and performs no external delivery, CRM/payment mutation, provider/browser action, or revenue claim"
        ),
    }
    artifact_validation = validate_live_client_workflow_proof_artifact(artifact)
    if not artifact_validation["ok"]:
        return {
            **scope_result,
            "ok": False,
            "error": "live client workflow proof artifact invalid",
            "errors": artifact_validation["errors"],
            "workflow_proof_path": None,
            "live_client_workflow_proof_written": False,
            "live_client_workflow_proof_performed": False,
        }

    target = root / workflow_proof_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    files_written = list(scope_result.get("files_written") or [])
    files_written.append(workflow_proof_path)
    return {
        **scope_result,
        "ok": True,
        "scope_packet_path": scope_packet_relative,
        "files_written": files_written,
        "workflow_proof_path": workflow_proof_path,
        "live_client_workflow_proof_written": True,
        "live_client_workflow_proof_performed": True,
        "scoped_client_data_ingested": True,
        "broad_client_data_ingested": False,
        "live_external_delivery_performed": False,
        "external_send_performed": False,
        "crm_mutation_performed": False,
        "payment_mutation_performed": False,
        "provider_calls": 0,
        "browser_actions": 0,
        "revenue_claim_made": False,
        "boundary": artifact["boundary"],
    }
