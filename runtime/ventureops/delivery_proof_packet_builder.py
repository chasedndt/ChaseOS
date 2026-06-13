"""Guarded live-delivery proof artifact builder for VentureOps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.ventureops.validation import (
    validate_client_safe_delivery_artifact,
    validate_live_client_workflow_proof_artifact,
    validate_live_delivery_proof_artifact,
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


def _is_file(root: Path, relative_path: str | None) -> bool:
    if relative_path is None:
        return False
    return (root / relative_path).exists() and (root / relative_path).is_file()


def _load_json_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not contain a JSON object")
    return data


def build_delivery_proof_packet(
    vault_root: str | Path,
    *,
    delivery_proof_id: str,
    client_label: str,
    delivery_reference_id: str,
    client_safe_delivery_artifact_path: str,
    live_client_proof_path: str,
    output_path: str,
    operator_approved: bool,
    operator_attested_delivery_performed: bool,
    workflow_id: str = "agent_runtime_governance_audit",
    delivery_status: str = "delivered",
) -> dict[str, Any]:
    """Write an operator-attested delivery proof artifact.

    This builder records a proof artifact from explicit operator-supplied
    fields. It does not deliver externally, mutate CRM/payment systems, send
    invoices, call providers/browsers, or make revenue/accounting claims.
    """

    root = Path(vault_root).resolve()
    errors: list[str] = []
    if not operator_approved:
        errors.append("operator approval flag required")
    if not operator_attested_delivery_performed:
        errors.append("operator delivery attestation required")

    delivery_artifact_relative = _add_relative_path(
        errors,
        "client_safe_delivery_artifact_path",
        client_safe_delivery_artifact_path,
        root,
    )
    live_client_proof_relative = _add_relative_path(errors, "live_client_proof_path", live_client_proof_path, root)
    output_relative = _add_relative_path(errors, "output_path", output_path, root)
    output_available = False
    if output_relative is not None:
        output_available = not (root / output_relative).exists()
        if not output_available:
            errors.append(f"output path already exists: {output_relative}")

    delivery_artifact_present = _is_file(root, delivery_artifact_relative)
    live_client_proof_present = _is_file(root, live_client_proof_relative)
    if not delivery_artifact_present:
        errors.append(f"client-safe delivery artifact missing: {delivery_artifact_relative}")
    if not live_client_proof_present:
        errors.append(f"live client proof artifact missing: {live_client_proof_relative}")

    client_safe_delivery_validation = {"ok": False, "errors": ["client-safe delivery artifact missing"]}
    if delivery_artifact_present:
        try:
            client_safe_delivery_artifact = _load_json_object(root / str(delivery_artifact_relative))
        except Exception as exc:
            errors.append(f"client-safe delivery artifact unreadable: {delivery_artifact_relative}: {exc}")
        else:
            client_safe_delivery_validation = validate_client_safe_delivery_artifact(client_safe_delivery_artifact)
            if not client_safe_delivery_validation.get("ok"):
                errors.append("client-safe delivery artifact invalid")
                errors.extend(client_safe_delivery_validation.get("errors") or [])
            else:
                if client_safe_delivery_validation.get("workflow_id") != workflow_id:
                    errors.append("client-safe delivery artifact workflow_id does not match delivery proof")
                if client_safe_delivery_validation.get("client_label") != client_label:
                    errors.append("client-safe delivery artifact client_label does not match delivery proof")
                if client_safe_delivery_validation.get("delivery_reference_id") != delivery_reference_id:
                    errors.append("client-safe delivery artifact delivery_reference_id does not match delivery proof")
                if client_safe_delivery_validation.get("source_live_client_proof_path") != live_client_proof_relative:
                    errors.append(
                        "client-safe delivery artifact source_live_client_proof_path does not match live_client_proof_path"
                    )

    live_client_proof_validation = {"ok": False, "errors": []}
    if live_client_proof_present:
        live_client_proof_validation = validate_live_client_workflow_proof_artifact(
            _load_json_object(root / live_client_proof_relative)
        )
        if not live_client_proof_validation.get("ok"):
            errors.append("live client proof artifact invalid")
            errors.extend(live_client_proof_validation.get("errors") or [])

    packet = {
        "type": "ventureops-live-delivery-proof",
        "status": "operator_attested_delivery_recorded",
        "delivery_proof_id": delivery_proof_id,
        "workflow_id": workflow_id,
        "client_label": client_label,
        "delivery_reference_id": delivery_reference_id,
        "delivery_status": str(delivery_status).strip().lower(),
        "client_safe_delivery_artifact_path": delivery_artifact_relative or "",
        "live_client_proof_path": live_client_proof_relative or "",
        "delivery_boundary": "operator_attested_delivery_no_chaseos_external_send",
        "operator_attested_delivery_performed": bool(operator_attested_delivery_performed),
        "external_send_performed_by_chaseos": False,
        "crm_mutation_performed": False,
        "payment_mutation_performed": False,
        "invoice_sent": False,
        "provider_calls": 0,
        "browser_actions": 0,
        "revenue_claim_made": False,
        "builder_boundary": (
            "operator-attested delivery proof artifact authoring only; validates delivery and "
            "live-client proof artifacts without external delivery, CRM/payment mutation, "
            "invoice send, provider/browser action, or revenue claims"
        ),
    }
    packet_validation = validate_live_delivery_proof_artifact(packet)
    if not packet_validation.get("ok"):
        errors.extend(packet_validation.get("errors") or [])

    base_payload = {
        "packet": packet,
        "packet_path": None,
        "delivery_proof_artifact_valid": bool(packet_validation.get("ok") and not errors),
        "client_safe_delivery_artifact_valid": bool(client_safe_delivery_validation.get("ok")),
        "client_safe_delivery_artifact_validation": client_safe_delivery_validation,
        "live_client_proof_path": live_client_proof_relative,
        "live_client_proof_artifact_valid": bool(live_client_proof_validation.get("ok")),
        "delivery_artifact_present": delivery_artifact_present,
        "live_client_proof_artifact_present": live_client_proof_present,
        "output_path_available": output_available,
        "errors": errors,
        "external_send_performed_by_chaseos": False,
        "external_send_performed": False,
        "payment_mutation_performed": False,
        "crm_mutation_performed": False,
        "invoice_sent": False,
        "provider_calls": 0,
        "browser_actions": 0,
        "revenue_claim_made": False,
        "boundary": "delivery proof artifact authoring only; no live workflow execution or external side effects",
    }
    if errors:
        return {
            **base_payload,
            "ok": False,
            "packet_written": False,
            "next_required_action": (
                "provide operator approval, delivery attestation, client-safe delivery artifact, "
                "and valid live-client workflow proof"
            ),
            "next_command": "chaseos ventureops delivery-proof-packet --operator-approved --output PATH --json",
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
        "next_required_action": "author revenue evidence packet with receipt and delivery proof",
        "next_command": (
            "chaseos ventureops revenue-evidence-packet --revenue-proof-id ID --client-label LABEL "
            "--payment-reference-id ID --payment-status received --amount AMOUNT --currency USD "
            f"--receipt-artifact-path PATH --delivery-proof-path {output_relative} "
            f"--crm-reference-id ID --approval-id ID --live-client-proof-path {live_client_proof_relative or 'PATH'} "
            "--output PATH --operator-approved --json"
        ),
    }
