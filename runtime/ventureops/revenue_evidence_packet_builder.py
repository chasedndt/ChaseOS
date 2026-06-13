"""Guarded live-revenue evidence packet builder for VentureOps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.ventureops.validation import (
    validate_live_client_workflow_proof_artifact,
    validate_live_delivery_proof_artifact,
    validate_live_revenue_evidence,
)


def _relative_to_root(path_value: str | Path, root: Path) -> str:
    raw = Path(path_value)
    resolved = raw.resolve() if raw.is_absolute() else (root / raw).resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{path_value} escapes vault root") from exc
    return str(relative).replace("\\", "/")


def _add_relative_path(
    errors: list[str],
    field: str,
    path_value: str | Path,
    root: Path,
) -> str | None:
    try:
        return _relative_to_root(path_value, root)
    except ValueError:
        errors.append(f"{field} escapes vault root: {path_value}")
        return None


def _load_json_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not contain a JSON object")
    return data


def _is_file(root: Path, relative_path: str | None) -> bool:
    if relative_path is None:
        return False
    return (root / relative_path).exists() and (root / relative_path).is_file()


def build_revenue_evidence_packet(
    vault_root: str | Path,
    *,
    revenue_proof_id: str,
    client_label: str,
    payment_reference_id: str,
    payment_status: str,
    amount: str | float,
    currency: str,
    receipt_artifact_path: str,
    delivery_proof_path: str,
    crm_reference_id: str,
    approval_id: str,
    live_client_proof_path: str,
    output_path: str,
    operator_approved: bool,
    workflow_id: str = "agent_runtime_governance_audit",
) -> dict[str, Any]:
    """Write a revenue evidence packet from explicit operator-supplied fields.

    The packet is only an input to the proof-only revenue command. This builder
    validates prerequisite artifacts but never sends invoices, mutates payment
    or CRM systems, or records an accounting/revenue claim.
    """

    root = Path(vault_root).resolve()
    errors: list[str] = []
    if not operator_approved:
        errors.append("operator approval flag required")

    receipt_relative = _add_relative_path(errors, "receipt_artifact_path", receipt_artifact_path, root)
    delivery_relative = _add_relative_path(errors, "delivery_proof_path", delivery_proof_path, root)
    live_client_proof_relative = _add_relative_path(errors, "live_client_proof_path", live_client_proof_path, root)
    output_relative = _add_relative_path(errors, "output_path", output_path, root)
    output_available = False
    if output_relative is not None:
        output_available = not (root / output_relative).exists()
        if not output_available:
            errors.append(f"output path already exists: {output_relative}")

    receipt_present = _is_file(root, receipt_relative)
    delivery_present = _is_file(root, delivery_relative)
    live_client_proof_present = _is_file(root, live_client_proof_relative)
    if not receipt_present:
        errors.append(f"receipt artifact missing: {receipt_relative}")
    if not delivery_present:
        errors.append(f"delivery proof artifact missing: {delivery_relative}")
    if not live_client_proof_present:
        errors.append(f"live client proof artifact missing: {live_client_proof_relative}")

    live_client_proof_validation = {"ok": False, "errors": []}
    if live_client_proof_present:
        live_client_proof_validation = validate_live_client_workflow_proof_artifact(
            _load_json_object(root / live_client_proof_relative)
        )
        if not live_client_proof_validation.get("ok"):
            errors.extend(live_client_proof_validation.get("errors") or [])
    delivery_proof_validation = {"ok": False, "errors": []}
    if delivery_present:
        delivery_proof_validation = validate_live_delivery_proof_artifact(_load_json_object(root / delivery_relative))
        if not delivery_proof_validation.get("ok"):
            errors.append("delivery proof artifact invalid")
            errors.extend(delivery_proof_validation.get("errors") or [])

    try:
        amount_value = float(str(amount))
    except ValueError:
        amount_value = 0.0

    packet = {
        "type": "ventureops-live-revenue-evidence",
        "revenue_proof_id": revenue_proof_id,
        "workflow_id": workflow_id,
        "client_label": client_label,
        "payment_reference_id": payment_reference_id,
        "payment_status": str(payment_status).strip().lower(),
        "amount": amount_value,
        "currency": str(currency).strip().upper(),
        "receipt_artifact_path": receipt_relative or "",
        "delivery_proof_path": delivery_relative or "",
        "crm_reference_id": crm_reference_id,
        "approval_id": approval_id,
        "revenue_recognition_boundary": "proof_only_no_accounting_claim",
        "live_client_proof_path": live_client_proof_relative or "",
        "builder_boundary": (
            "operator-supplied revenue packet authoring only; validates receipt, delivery, "
            "and live-client proof artifacts without payment/CRM mutation or revenue claims"
        ),
    }
    packet_validation = validate_live_revenue_evidence(packet)
    if not packet_validation.get("ok"):
        errors.extend(packet_validation.get("errors") or [])

    base_payload = {
        "packet": packet,
        "packet_path": None,
        "revenue_evidence_valid": bool(packet_validation.get("ok") and not errors),
        "live_client_proof_path": live_client_proof_relative,
        "live_client_proof_artifact_valid": bool(live_client_proof_validation.get("ok")),
        "delivery_proof_artifact_valid": bool(delivery_proof_validation.get("ok")),
        "delivery_proof_validation": delivery_proof_validation,
        "receipt_artifact_present": receipt_present,
        "delivery_proof_present": delivery_present,
        "output_path_available": output_available,
        "errors": errors,
        "payment_mutation_performed": False,
        "crm_mutation_performed": False,
        "invoice_sent": False,
        "external_send_performed": False,
        "provider_calls": 0,
        "browser_actions": 0,
        "revenue_claim_made": False,
        "boundary": "revenue packet authoring only; no live workflow execution or external side effects",
    }
    if errors:
        return {
            **base_payload,
            "ok": False,
            "packet_written": False,
            "next_required_action": (
                "provide operator approval, redacted receipt/delivery artifacts, and a valid live-client workflow proof"
            ),
            "next_command": "chaseos ventureops revenue-evidence-packet --operator-approved --output PATH --json",
        }

    assert output_relative is not None
    target = root / output_relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(packet, indent=2), encoding="utf-8")

    return {
        **base_payload,
        "ok": True,
        "packet_written": True,
        "packet_path": output_relative,
        "next_required_action": "run live-revenue-proof with --execute-proof",
        "next_command": (
            f"chaseos ventureops live-revenue-proof --revenue-packet {output_relative} "
            f"--live-client-proof-path {live_client_proof_relative or 'PATH'} --execute-proof --json"
        ),
    }
