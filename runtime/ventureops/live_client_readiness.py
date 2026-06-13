"""Readiness checks for the VentureOps live client scope proof gate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.ventureops.validation import (
    audit_external_readiness_completion,
    validate_real_client_scope_evidence,
    validate_scope_evidence_approval_artifact,
    validate_scope_evidence_source_paths,
)


def _load_scope_packet(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not contain a JSON object")
    return data


def _manifest_gate_declared(vault_root: Path) -> bool:
    manifest = vault_root / "runtime" / "workflows" / "registry" / "agent_runtime_governance_audit.yaml"
    if not manifest.exists():
        return False
    text = manifest.read_text(encoding="utf-8", errors="replace")
    return (
        "include_live_client_scope_proof_gate" in text
        and "real_client_scope_evidence_path" in text
        and "live_client_scope_proof_gate_path" in text
    )


def build_live_client_scope_proof_readiness(
    vault_root: Path,
    *,
    scope_packet_path: str | None = None,
) -> dict[str, Any]:
    """Build a no-execution readiness report for the live client scope proof gate."""
    root = vault_root.resolve()
    audit = audit_external_readiness_completion(root)
    manifest_gate_declared = _manifest_gate_declared(root)
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

    if not audit.get("ok"):
        blockers.append("external readiness audit failed")
    if audit.get("proof_chain_artifact_count") != audit.get("expected_proof_chain_artifact_count"):
        blockers.append("live client scope contract proof chain incomplete")
    if not manifest_gate_declared:
        blockers.append("agent_runtime_governance_audit manifest does not declare live client scope proof gate")

    if scope_packet_path:
        packet_path = Path(scope_packet_path)
        scope_packet = _load_scope_packet(packet_path)
        scope_validation = validate_real_client_scope_evidence(scope_packet)
        if not scope_validation["ok"]:
            blockers.extend(scope_validation["errors"])
        else:
            approval_validation = validate_scope_evidence_approval_artifact(root, scope_packet)
            if not approval_validation["ok"]:
                blockers.extend(approval_validation["errors"])
            source_validation = validate_scope_evidence_source_paths(root, scope_validation["safe_read_paths"])
            if not source_validation["ok"]:
                blockers.extend(source_validation["errors"])
    else:
        blockers.append("real client scope evidence packet missing")

    if "live client workflow proof missing" not in audit.get("missing_requirements", []):
        warnings.append("completion audit no longer reports live client workflow proof missing; re-check completion status")

    ready_for_gate = not blockers
    ready_for_workflow_proof = ready_for_gate
    if ready_for_workflow_proof:
        next_required_action = "run live-client-workflow-proof with --execute-proof"
        next_command = (
            "chaseos ventureops live-client-workflow-proof "
            f"--scope-packet {scope_packet_path} --execute-proof --json"
        )
    else:
        next_required_action = "collect real-client scope inputs through real-client-input-manifest"
        next_command = (
            "chaseos ventureops real-client-input-manifest --client-label LABEL "
            "--scope-id ID --approval-id ID --approved-read-path PATH "
            "--approval-output PATH --scope-packet-output PATH --json"
        )
    recommended_inputs = {
        "include_live_client_scope_contract": True,
        "include_live_client_scope_proof_gate": True,
        "include_live_client_workflow_proof": ready_for_workflow_proof,
        "real_client_scope_evidence_path": scope_packet_path,
    }
    return {
        "ok": True,
        "readiness_status": "ready_for_scope_proof_gate" if ready_for_gate else "blocked",
        "ready_for_live_client_scope_proof_gate": ready_for_gate,
        "ready_for_live_client_workflow": ready_for_workflow_proof,
        "ready_for_live_client_workflow_proof": ready_for_workflow_proof,
        "next_required_action": next_required_action,
        "next_command": next_command,
        "scope_packet_path": scope_packet_path,
        "scope_evidence_valid": bool(scope_validation["ok"]),
        "scope_validation": scope_validation,
        "scope_approval_artifact_valid": bool(approval_validation.get("scope_approval_artifact_valid")),
        "scope_approval_validation": approval_validation,
        "scope_sources_valid": bool(source_validation["ok"]),
        "scope_source_validation": source_validation,
        "manifest_gate_declared": manifest_gate_declared,
        "external_readiness_audit_ok": bool(audit.get("ok")),
        "completion_decision": audit.get("completion_decision"),
        "missing_requirements": audit.get("missing_requirements") or [],
        "blockers": blockers,
        "warnings": warnings,
        "recommended_workflow_id": "agent_runtime_governance_audit",
        "recommended_workflow_inputs": recommended_inputs,
        "live_client_scope_proof_performed": False,
        "live_client_data_ingested": False,
        "live_external_delivery_performed": False,
        "provider_calls": 0,
        "browser_actions": 0,
        "crm_mutation_performed": False,
        "payment_mutation_performed": False,
        "revenue_claim_made": False,
        "boundary": (
            "readiness check only; does not run the live client workflow, ingest client data, "
            "send externally, mutate CRM/payment systems, call providers, control browsers, or make revenue claims"
        ),
    }
