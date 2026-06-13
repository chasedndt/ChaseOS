"""Closeout readiness composer for the final VentureOps external evidence pass."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.ventureops.evidence_intake import build_evidence_intake
from runtime.ventureops.validation import audit_external_readiness_completion


def _checklist_item(name: str, status: str, evidence: list[str], notes: str) -> dict[str, Any]:
    return {
        "requirement": name,
        "status": status,
        "evidence": evidence,
        "notes": notes,
    }


def _next_from_state(audit: dict[str, Any], intake: dict[str, Any]) -> tuple[str, str]:
    if audit.get("complete") is True:
        return ("completion audit passed", "chaseos ventureops external-readiness-audit --json")
    if intake.get("ready_for_live_revenue_proof") is True:
        return (str(intake.get("next_required_action")), str(intake.get("next_command")))
    if intake.get("ready_for_live_client_scope_proof_gate") is True:
        scope_packet = intake.get("scope_packet_path") or "PATH"
        return (
            "run live-client-workflow-proof with --execute-proof after operator approval",
            f"chaseos ventureops live-client-workflow-proof --scope-packet {scope_packet} --execute-proof --json",
        )
    return (
        "collect real-client scope inputs through real-client-input-manifest",
        (
            "chaseos ventureops real-client-input-manifest --client-label LABEL "
            "--scope-id ID --approval-id ID --approved-read-path PATH "
            "--approval-output PATH --scope-packet-output PATH --json"
        ),
    )


def build_real_evidence_closeout_readiness(
    vault_root: str | Path,
    *,
    scope_packet_path: str | None = None,
    revenue_packet_path: str | None = None,
    live_client_proof_path: str | None = None,
) -> dict[str, Any]:
    """Compose the current VentureOps final-external-feature readiness state.

    This is a no-execution closeout view. It reviews the exact typo-compatible
    handover, canonical passover, completion audit, and optional operator
    packets, then reports the next guarded command without marking completion
    unless the external readiness audit is already complete.
    """
    root = Path(vault_root).resolve()
    audit = audit_external_readiness_completion(root)
    intake = build_evidence_intake(
        root,
        scope_packet_path=scope_packet_path,
        revenue_packet_path=revenue_packet_path,
        live_client_proof_path=live_client_proof_path,
    )
    next_required_action, next_command = _next_from_state(audit, intake)
    missing_requirements = list(audit.get("missing_requirements") or [])
    live_client_workflow_proof_present = "live client workflow proof missing" not in missing_requirements
    live_revenue_workflow_proof_present = "live revenue workflow proof missing" not in missing_requirements
    ready_for_completion = bool(audit.get("complete") is True and not missing_requirements)
    readiness_status = "ready_for_completion" if ready_for_completion else "blocked"
    reviewed_surfaces = [
        str(audit.get("requested_handover_path") or "06_AGENTS/VentureOps-externaal-Readiness-Handover.md"),
        str(audit.get("handover_path") or "06_AGENTS/VentureOps-External-Readiness-Handover.md"),
        str(audit.get("passover_path") or "06_AGENTS/VentureOps-External-Readiness-Passover.md"),
        "runtime.ventureops.validation.audit_external_readiness_completion",
        "runtime.ventureops.evidence_intake.build_evidence_intake",
    ]
    closeout_checklist = [
        _checklist_item(
            "requested typo handover reviewed",
            "verified" if audit.get("requested_handover_alias_valid") else "failed",
            [str(audit.get("requested_handover_path"))] if audit.get("requested_handover_alias_valid") else [],
            "Reviews the exact operator-requested VentureOps-externaal handover alias.",
        ),
        _checklist_item(
            "canonical passover valid",
            "verified" if audit.get("passover_valid") else "failed",
            [str(audit.get("passover_path"))] if audit.get("passover_valid") else [],
            "Canonical passover remains the source of truth for final external blockers.",
        ),
        _checklist_item(
            "external audit current",
            "verified" if audit.get("ok") else "failed",
            ["chaseos ventureops external-readiness-audit --json"],
            "Completion decision comes from the canonical external readiness audit.",
        ),
        _checklist_item(
            "evidence intake current",
            "verified" if intake.get("ok") else "failed",
            ["chaseos ventureops evidence-intake --json"],
            "Optional operator packets are composed without running live workflows.",
        ),
        _checklist_item(
            "live client workflow proof",
            "verified" if live_client_workflow_proof_present else "missing",
            [],
            "Requires a real client-approved scope packet and guarded local workflow proof.",
        ),
        _checklist_item(
            "live revenue workflow proof",
            "verified" if live_revenue_workflow_proof_present else "missing",
            [],
            "Requires live-client workflow proof plus redacted revenue evidence.",
        ),
        _checklist_item(
            "final completion decision",
            "verified" if ready_for_completion else "blocked",
            [],
            "This closeout does not mark VentureOps complete unless the external audit is complete.",
        ),
    ]

    return {
        "ok": bool(audit.get("ok") and intake.get("ok")),
        "readiness_status": readiness_status,
        "ready_for_completion": ready_for_completion,
        "completion_decision": "complete" if ready_for_completion else "not_complete",
        "status": audit.get("status"),
        "reviewed_surfaces": reviewed_surfaces,
        "requested_handover_alias_valid": bool(audit.get("requested_handover_alias_valid")),
        "handover_alias_valid": bool(audit.get("handover_alias_valid")),
        "passover_valid": bool(audit.get("passover_valid")),
        "external_audit_ok": bool(audit.get("ok")),
        "external_audit_complete": bool(audit.get("complete")),
        "evidence_intake_status": intake.get("intake_status"),
        "scope_packet_present": bool(intake.get("scope_packet_present")),
        "scope_evidence_valid": bool(intake.get("scope_evidence_valid")),
        "scope_sources_valid": bool(intake.get("scope_sources_valid")),
        "revenue_packet_present": bool(intake.get("revenue_packet_present")),
        "revenue_evidence_valid": bool(intake.get("revenue_evidence_valid")),
        "live_client_proof_artifact_present": bool(intake.get("live_client_proof_artifact_present")),
        "live_client_proof_artifact_valid": bool(intake.get("live_client_proof_artifact_valid")),
        "ready_for_live_client_scope_proof_gate": bool(intake.get("ready_for_live_client_scope_proof_gate")),
        "ready_for_live_revenue_proof": bool(intake.get("ready_for_live_revenue_proof")),
        "live_client_workflow_proof_present": live_client_workflow_proof_present,
        "live_revenue_workflow_proof_present": live_revenue_workflow_proof_present,
        "missing_requirements": missing_requirements,
        "errors": list(audit.get("errors") or []),
        "blockers": list(intake.get("blockers") or []) + missing_requirements,
        "warnings": list(intake.get("warnings") or []),
        "next_required_real_use_pass": audit.get("next_required_real_use_pass"),
        "next_guarded_command": audit.get("next_guarded_command"),
        "next_required_inputs": audit.get("next_required_inputs") or [],
        "next_required_action": next_required_action,
        "next_command": next_command,
        "closeout_checklist": closeout_checklist,
        "report_written": False,
        "report_path": None,
        "live_client_scope_proof_performed": False,
        "live_client_data_ingested": False,
        "live_external_delivery_performed": False,
        "external_send_performed": False,
        "crm_mutation_performed": False,
        "payment_mutation_performed": False,
        "invoice_sent": False,
        "provider_calls": 0,
        "browser_actions": 0,
        "revenue_claim_made": False,
        "boundary": (
            "closeout readiness only; reviews handover/passover/audit/intake state and recommends the next "
            "guarded command without running live client workflows, sending externally, mutating CRM/payment, "
            "calling providers/browsers, sending invoices, or making revenue/accounting claims"
        ),
    }
