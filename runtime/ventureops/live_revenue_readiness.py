"""Readiness checks for the VentureOps live revenue proof."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.ventureops.validation import (
    audit_external_readiness_completion,
    validate_live_client_workflow_proof_artifact,
    validate_live_delivery_proof_artifact,
    validate_live_revenue_evidence,
)


def _load_revenue_packet(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not contain a JSON object")
    return data


def _resolve_under_root(root: Path, path_value: str) -> tuple[Path | None, str, list[str]]:
    path = Path(path_value)
    resolved = path.resolve() if path.is_absolute() else (root / path).resolve()
    errors: list[str] = []
    try:
        relative = resolved.relative_to(root)
    except ValueError:
        return None, str(path_value), [f"live client proof artifact path escapes vault root: {path_value}"]
    return resolved, str(relative).replace("\\", "/"), errors


def build_live_revenue_proof_readiness(
    vault_root: Path,
    *,
    revenue_packet_path: str | None = None,
    live_client_proof_path: str | None = None,
) -> dict[str, Any]:
    """Build a no-execution readiness report for future live revenue proof."""
    root = vault_root.resolve()
    audit = audit_external_readiness_completion(root)
    blockers: list[str] = []
    warnings: list[str] = []
    revenue_validation: dict[str, Any] = {
        "ok": False,
        "errors": ["live revenue evidence packet missing"],
        "amount": 0.0,
        "currency": "",
        "receipt_artifact_path": "",
        "delivery_proof_path": "",
    }
    live_client_proof_validation: dict[str, Any] = {
        "ok": False,
        "errors": ["live client proof artifact missing"],
    }
    live_client_proof_artifact_present = False
    live_client_proof_artifact_valid = False
    live_client_proof_relative_path: str | None = None
    delivery_proof_artifact_present = False
    delivery_proof_artifact_valid = False
    delivery_proof_validation: dict[str, Any] = {
        "ok": False,
        "errors": ["delivery proof artifact missing"],
    }

    missing = audit.get("missing_requirements") or []
    if not audit.get("ok"):
        blockers.append("external readiness audit failed")
    if "live client workflow proof missing" in missing and not live_client_proof_path:
        blockers.append("live client workflow proof missing")
    if audit.get("proof_chain_artifact_count") != audit.get("expected_proof_chain_artifact_count"):
        blockers.append("live client scope contract proof chain incomplete")

    if revenue_packet_path:
        packet_path = Path(revenue_packet_path)
        revenue_validation = validate_live_revenue_evidence(_load_revenue_packet(packet_path))
        if not revenue_validation["ok"]:
            blockers.extend(revenue_validation["errors"])
        else:
            delivery_path = root / str(revenue_validation.get("delivery_proof_path") or "")
            if not delivery_path.exists() or not delivery_path.is_file():
                delivery_relative = str(revenue_validation.get("delivery_proof_path") or "")
                blockers.append(f"delivery proof artifact missing: {delivery_relative}")
                delivery_proof_validation = {
                    "ok": False,
                    "errors": [f"delivery proof artifact missing: {delivery_relative}"],
                }
            else:
                delivery_proof_artifact_present = True
                delivery_data = json.loads(delivery_path.read_text(encoding="utf-8"))
                if not isinstance(delivery_data, dict):
                    delivery_proof_validation = {
                        "ok": False,
                        "errors": ["delivery proof artifact must be a JSON object"],
                    }
                else:
                    delivery_proof_validation = validate_live_delivery_proof_artifact(delivery_data)
                delivery_proof_artifact_valid = bool(delivery_proof_validation["ok"])
                if not delivery_proof_artifact_valid:
                    blockers.append("delivery proof artifact invalid")
                    blockers.extend(delivery_proof_validation["errors"])
    else:
        blockers.append("live revenue evidence packet missing")

    if live_client_proof_path:
        proof_path, live_client_proof_relative_path, path_errors = _resolve_under_root(root, live_client_proof_path)
        if path_errors:
            blockers.extend(path_errors)
            live_client_proof_validation = {"ok": False, "errors": path_errors}
        elif proof_path is None or not proof_path.exists():
            blockers.append(f"live client proof artifact missing: {live_client_proof_relative_path}")
            live_client_proof_validation = {
                "ok": False,
                "errors": [f"live client proof artifact missing: {live_client_proof_relative_path}"],
            }
        else:
            live_client_proof_artifact_present = True
            proof_data = json.loads(proof_path.read_text(encoding="utf-8"))
            if not isinstance(proof_data, dict):
                live_client_proof_validation = {"ok": False, "errors": ["live client proof artifact must be a JSON object"]}
            else:
                live_client_proof_validation = validate_live_client_workflow_proof_artifact(proof_data)
            live_client_proof_artifact_valid = bool(live_client_proof_validation["ok"])
            if not live_client_proof_artifact_valid:
                blockers.append("live client proof artifact invalid")
                blockers.extend(live_client_proof_validation["errors"])
    else:
        blockers.append("live client proof artifact path missing")

    if "live revenue workflow proof missing" not in missing:
        warnings.append("completion audit no longer reports live revenue workflow proof missing; re-check completion status")

    ready = not blockers
    return {
        "ok": True,
        "readiness_status": "ready_for_live_revenue_proof" if ready else "blocked",
        "ready_for_live_revenue_proof": ready,
        "revenue_packet_path": revenue_packet_path,
        "live_client_proof_path": live_client_proof_path,
        "live_client_proof_relative_path": live_client_proof_relative_path,
        "revenue_evidence_valid": bool(revenue_validation["ok"]),
        "revenue_validation": revenue_validation,
        "live_client_proof_artifact_present": live_client_proof_artifact_present,
        "live_client_proof_artifact_valid": live_client_proof_artifact_valid,
        "live_client_proof_validation": live_client_proof_validation,
        "delivery_proof_artifact_present": delivery_proof_artifact_present,
        "delivery_proof_artifact_valid": delivery_proof_artifact_valid,
        "delivery_proof_validation": delivery_proof_validation,
        "external_readiness_audit_ok": bool(audit.get("ok")),
        "completion_decision": audit.get("completion_decision"),
        "missing_requirements": missing,
        "blockers": blockers,
        "warnings": warnings,
        "recommended_order": [
            "complete live client workflow proof",
            "validate live revenue evidence packet",
            "write proof-only revenue scorecard",
            "keep payment/CRM mutation blocked unless separately approved",
        ],
        "payment_mutation_performed": False,
        "crm_mutation_performed": False,
        "provider_calls": 0,
        "browser_actions": 0,
        "external_send_performed": False,
        "revenue_claim_made": False,
        "boundary": (
            "readiness check only; validates packet and live-client workflow proof shape but does not prove live revenue, "
            "mutate CRM/payment systems, send invoices, call providers, control browsers, or make accounting claims"
        ),
    }
