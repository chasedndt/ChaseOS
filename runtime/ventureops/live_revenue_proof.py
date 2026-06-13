"""Proof-only writer for guarded VentureOps live revenue evidence."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from runtime.ventureops.validation import (
    validate_live_client_workflow_proof_artifact,
    validate_live_delivery_proof_artifact,
    validate_live_revenue_evidence,
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


def _slug(value: Any) -> str:
    text = str(value or "live-revenue-proof").strip().lower()
    text = re.sub(r"[^a-z0-9._-]+", "-", text)
    text = text.strip("-._")
    return text or "live-revenue-proof"


def run_live_revenue_proof(
    vault_root: Path,
    *,
    revenue_packet_path: str,
    live_client_proof_path: str,
    run_date: str,
    execute_proof: bool = False,
) -> dict[str, Any]:
    """Write a local proof-only revenue artifact after explicit approval."""
    root = vault_root.resolve()
    if not execute_proof:
        return {
            "ok": False,
            "error": "live-revenue-proof requires --execute-proof",
            "live_revenue_proof_written": False,
            "proof_path": None,
            "payment_mutation_performed": False,
            "crm_mutation_performed": False,
            "invoice_sent": False,
            "external_send_performed": False,
            "revenue_claim_made": False,
            "boundary": "blocked until explicit --execute-proof is supplied",
        }

    revenue_packet_relative = _relative_to_root(revenue_packet_path, root)
    live_client_proof_relative = _relative_to_root(live_client_proof_path, root)
    revenue_packet = _load_json_object(root / revenue_packet_relative)
    validation = validate_live_revenue_evidence(revenue_packet)
    if not validation["ok"]:
        return {
            "ok": False,
            "error": "live revenue evidence invalid",
            "errors": validation["errors"],
            "revenue_packet_path": revenue_packet_relative,
            "live_client_proof_path": live_client_proof_relative,
            "live_revenue_proof_written": False,
            "proof_path": None,
            "payment_mutation_performed": False,
            "crm_mutation_performed": False,
            "invoice_sent": False,
            "external_send_performed": False,
            "revenue_claim_made": False,
            "boundary": "invalid revenue evidence; no proof artifact written",
        }

    receipt_path = validation["receipt_artifact_path"]
    delivery_path = validation["delivery_proof_path"]
    receipt_exists = (root / receipt_path).exists()
    delivery_exists = (root / delivery_path).exists()
    live_client_proof_exists = (root / live_client_proof_relative).exists()
    missing = []
    if not receipt_exists:
        missing.append(f"receipt artifact missing: {receipt_path}")
    if not delivery_exists:
        missing.append(f"delivery proof artifact missing: {delivery_path}")
    if not live_client_proof_exists:
        missing.append(f"live client proof artifact missing: {live_client_proof_relative}")
    if missing:
        return {
            "ok": False,
            "error": "required proof artifact missing",
            "errors": missing,
            "revenue_packet_path": revenue_packet_relative,
            "live_client_proof_path": live_client_proof_relative,
            "live_revenue_proof_written": False,
            "proof_path": None,
            "payment_mutation_performed": False,
            "crm_mutation_performed": False,
            "invoice_sent": False,
            "external_send_performed": False,
            "revenue_claim_made": False,
            "boundary": "missing prerequisite proof artifacts; no proof artifact written",
        }

    live_client_proof = _load_json_object(root / live_client_proof_relative)
    live_client_proof_validation = validate_live_client_workflow_proof_artifact(live_client_proof)
    if not live_client_proof_validation["ok"]:
        return {
            "ok": False,
            "error": "live client proof artifact invalid",
            "errors": live_client_proof_validation["errors"],
            "revenue_packet_path": revenue_packet_relative,
            "live_client_proof_path": live_client_proof_relative,
            "live_revenue_proof_written": False,
            "proof_path": None,
            "payment_mutation_performed": False,
            "crm_mutation_performed": False,
            "invoice_sent": False,
            "external_send_performed": False,
            "revenue_claim_made": False,
            "boundary": "invalid live client proof artifact; no proof artifact written",
        }

    delivery_proof = _load_json_object(root / delivery_path)
    delivery_proof_validation = validate_live_delivery_proof_artifact(delivery_proof)
    if not delivery_proof_validation["ok"]:
        return {
            "ok": False,
            "error": "delivery proof artifact invalid",
            "errors": delivery_proof_validation["errors"],
            "revenue_packet_path": revenue_packet_relative,
            "live_client_proof_path": live_client_proof_relative,
            "delivery_proof_path": delivery_path,
            "delivery_proof_artifact_valid": False,
            "live_revenue_proof_written": False,
            "proof_path": None,
            "payment_mutation_performed": False,
            "crm_mutation_performed": False,
            "invoice_sent": False,
            "external_send_performed": False,
            "revenue_claim_made": False,
            "boundary": "invalid delivery proof artifact; no proof artifact written",
        }

    revenue_proof_id = _slug(revenue_packet.get("revenue_proof_id"))
    proof_relative = f"07_LOGS/Revenue-Proofs/{run_date}_{revenue_proof_id}_live-revenue-proof.json"
    if (root / proof_relative).exists():
        return {
            "ok": False,
            "error": "proof output path already exists",
            "errors": [f"proof output path already exists: {proof_relative}"],
            "revenue_packet_path": revenue_packet_relative,
            "live_client_proof_path": live_client_proof_relative,
            "live_revenue_proof_written": False,
            "proof_path": proof_relative,
            "payment_mutation_performed": False,
            "crm_mutation_performed": False,
            "invoice_sent": False,
            "external_send_performed": False,
            "revenue_claim_made": False,
            "boundary": "proof output collision; no proof artifact written",
        }
    proof = {
        "type": "ventureops-live-revenue-proof",
        "status": "proof_only_recorded_no_accounting_claim",
        "date": run_date,
        "revenue_proof_id": revenue_packet.get("revenue_proof_id"),
        "revenue_packet_path": revenue_packet_relative,
        "workflow_id": revenue_packet.get("workflow_id"),
        "client_label": revenue_packet.get("client_label"),
        "payment_reference_id": revenue_packet.get("payment_reference_id"),
        "payment_status": str(revenue_packet.get("payment_status") or "").strip().lower(),
        "amount": validation["amount"],
        "currency": validation["currency"],
        "receipt_artifact_path": receipt_path,
        "delivery_proof_path": delivery_path,
        "live_client_proof_path": live_client_proof_relative,
        "crm_reference_id": revenue_packet.get("crm_reference_id"),
        "approval_id": revenue_packet.get("approval_id"),
        "revenue_recognition_boundary": "proof_only_no_accounting_claim",
        "receipt_artifact_exists": receipt_exists,
        "delivery_proof_exists": delivery_exists,
        "delivery_proof_artifact_valid": True,
        "live_client_proof_exists": live_client_proof_exists,
        "live_client_proof_artifact_valid": True,
        "payment_mutation_performed": False,
        "crm_mutation_performed": False,
        "invoice_sent": False,
        "external_send_performed": False,
        "revenue_claim_made": False,
        "boundary": (
            "proof-only local artifact; not an accounting claim, invoice send, payment mutation, "
            "CRM mutation, external delivery, provider call, or browser action"
        ),
    }
    target = root / proof_relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(proof, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "ok": True,
        "revenue_packet_path": revenue_packet_relative,
        "live_client_proof_path": live_client_proof_relative,
        "live_revenue_proof_written": True,
        "proof_path": proof_relative,
        "amount": validation["amount"],
        "currency": validation["currency"],
        "receipt_artifact_exists": receipt_exists,
        "delivery_proof_exists": delivery_exists,
        "delivery_proof_artifact_valid": True,
        "live_client_proof_exists": live_client_proof_exists,
        "live_client_proof_artifact_valid": True,
        "payment_mutation_performed": False,
        "crm_mutation_performed": False,
        "invoice_sent": False,
        "external_send_performed": False,
        "revenue_claim_made": False,
        "boundary": proof["boundary"],
    }
