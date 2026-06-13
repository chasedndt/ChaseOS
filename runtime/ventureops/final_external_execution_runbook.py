"""No-execution runbook for the remaining VentureOps external proof steps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.ventureops.real_evidence_closeout_readiness import build_real_evidence_closeout_readiness
from runtime.ventureops.validation import audit_external_readiness_completion


REQUIRED_OPERATOR_INPUTS = [
    "typed real-client scope approval artifact",
    "real client-approved scope evidence packet",
    "approved scope source files inside the vault root",
    "valid live-client workflow proof artifact",
    "client-safe delivery artifact",
    "redacted live revenue evidence packet",
]

REAL_CLIENT_INPUT_MANIFEST_COMMAND = (
    "chaseos ventureops real-client-input-manifest --client-label LABEL "
    "--scope-id ID --approval-id ID --approved-read-path PATH "
    "--approval-output PATH --scope-packet-output PATH --json"
)

FINAL_EVIDENCE_BUNDLE_COMMAND = (
    "chaseos ventureops final-evidence-bundle --bundle PATH "
    "--write-report --report-path PATH --json"
)
FINAL_EVIDENCE_BUNDLE_PACKET_COMMAND = (
    "chaseos ventureops final-evidence-bundle-packet --scope-packet-path PATH "
    "--live-client-workflow-proof-path PATH --delivery-proof-path PATH --revenue-packet-path PATH "
    "--live-revenue-proof-path PATH --output PATH --json"
)
FINAL_FEATURE_FAMILY_AUDIT_COMMAND = (
    "chaseos ventureops feature-family-completion-audit --write-report --report-path PATH --json"
)


def _step(
    stage: str,
    command: str,
    status: str,
    required_before: list[str],
    writes: list[str],
    notes: str,
) -> dict[str, Any]:
    return {
        "stage": stage,
        "command": command,
        "status": status,
        "required_before": required_before,
        "writes": writes,
        "notes": notes,
        "forbidden_side_effects": [
            "external_send",
            "crm_mutation",
            "payment_mutation",
            "invoice_send",
            "provider_call",
            "browser_action",
            "accounting_claim",
            "revenue_claim",
        ],
    }


def _checklist_item(requirement: str, status: str, evidence: list[str], notes: str) -> dict[str, Any]:
    return {
        "requirement": requirement,
        "status": status,
        "evidence": evidence,
        "notes": notes,
    }


def _status(ready: bool) -> str:
    return "ready" if ready else "blocked"


def build_final_external_execution_runbook(
    vault_root: str | Path,
    *,
    scope_packet_path: str | None = None,
    revenue_packet_path: str | None = None,
    live_client_proof_path: str | None = None,
) -> dict[str, Any]:
    """Build the exact remaining external VentureOps command runbook.

    This function intentionally does not execute any proof command. It composes
    the validated passover, typo-compatible handover, external readiness audit,
    and optional evidence-intake state into the ordered operator sequence needed
    to close the real live-client and live-revenue blockers.
    """
    root = Path(vault_root).resolve()
    audit = audit_external_readiness_completion(root)
    closeout = build_real_evidence_closeout_readiness(
        root,
        scope_packet_path=scope_packet_path,
        revenue_packet_path=revenue_packet_path,
        live_client_proof_path=live_client_proof_path,
    )

    scope_packet = scope_packet_path or "PATH"
    revenue_packet = revenue_packet_path or "PATH"
    live_client_proof = live_client_proof_path or "PATH"
    scope_ready = bool(closeout.get("scope_evidence_valid") and closeout.get("scope_sources_valid"))
    revenue_packet_valid = bool(closeout.get("revenue_evidence_valid"))
    live_client_proof_ready = bool(closeout.get("live_client_proof_artifact_valid"))
    revenue_ready = bool(revenue_packet_valid and live_client_proof_ready)

    command_sequence = [
        _step(
            "current completion audit",
            "chaseos ventureops external-readiness-audit --json",
            "available",
            [],
            [],
            "Confirms the current passover/handover state and missing live proof requirements.",
        ),
        _step(
            "whole objective audit",
            "chaseos ventureops feature-family-completion-audit --json",
            "available",
            [],
            [],
            "Maps the full VentureOps goal to repo evidence before any real-use execution.",
        ),
        _step(
            "evidence discovery preflight",
            "chaseos ventureops evidence-discovery-preflight --json",
            "available",
            [],
            [],
            "Scans bounded repo-local evidence roots, rejects template-only packets, and recommends the next guarded command without executing workflows.",
        ),
        _step(
            "real-client input manifest",
            REAL_CLIENT_INPUT_MANIFEST_COMMAND,
            "available",
            ["client label", "scope id", "approval id", "approved source files inside the vault root"],
            ["no-execution real-client input manifest"],
            "Checks the exact real-client scope inputs and recommends the next scope approval or scope packet command; does not run live workflows.",
        ),
        _step(
            "scope evidence packet scaffold",
            "chaseos ventureops evidence-template --kind scope --output PATH --json",
            "available",
            [],
            ["operator-selected scope packet path"],
            "Creates a template only; operator must replace placeholders and remove template_only after real approval.",
        ),
        _step(
            "scope approval artifact authoring",
            (
                "chaseos ventureops scope-approval-packet --approval-id ID --client-label LABEL "
                "--scope-id ID --approved-read-path PATH --output PATH --operator-approved "
                "--operator-attested-scope-approved --json"
            ),
            "available",
            ["operator approval for scope proof", "approved source files inside the vault root"],
            ["operator-selected scope approval artifact path"],
            "Writes a typed no-side-effect scope approval artifact and does not run live workflows, ingest client data, or authorize external side effects.",
        ),
        _step(
            "scope evidence packet authoring",
            (
                "chaseos ventureops scope-evidence-packet --client-label LABEL --scope-id ID "
                "--approval-id ID --approval-artifact-path PATH --approved-read-path PATH "
                "--output PATH --operator-approved --json"
            ),
            "available",
            ["operator approval artifact", "approved source files inside the vault root"],
            ["operator-selected scope packet path"],
            "Writes a scope packet from explicit operator-supplied approval/source fields without running the workflow.",
        ),
        _step(
            "scope evidence validation",
            f"chaseos ventureops validate-scope-evidence --packet {scope_packet} --vault-root VAULT_ROOT --json",
            _status(scope_ready),
            ["real client-approved scope evidence packet"],
            [],
            "Validates packet shape, the typed approval artifact, and approved source files without ingesting client data or running the workflow.",
        ),
        _step(
            "live client proof readiness",
            f"chaseos ventureops live-client-proof-readiness --scope-packet {scope_packet} --json",
            _status(scope_ready),
            ["valid scope evidence packet", "approved source files inside the vault root"],
            [],
            "Checks source-path readiness for the guarded live-client proof lanes.",
        ),
        _step(
            "live client scope proof gate",
            f"chaseos ventureops live-client-scope-proof --scope-packet {scope_packet} --execute-proof --json",
            _status(scope_ready),
            ["valid scope evidence packet", "operator approval to execute proof"],
            ["local live-client scope proof-gate artifact"],
            "Writes a local proof-gate artifact only; it is not a completed client workflow.",
        ),
        _step(
            "live client workflow proof",
            f"chaseos ventureops live-client-workflow-proof --scope-packet {scope_packet} --execute-proof --json",
            _status(scope_ready),
            ["valid scope evidence packet", "approved source files", "operator approval to execute proof"],
            ["local live-client workflow proof artifact", "client-safe report", "scorecard"],
            "Runs the scoped local workflow proof without external delivery, provider/browser action, CRM/payment mutation, or revenue claims.",
        ),
        _step(
            "revenue evidence packet scaffold",
            "chaseos ventureops evidence-template --kind revenue --output PATH --json",
            "available",
            ["live-client workflow proof artifact exists"],
            ["operator-selected revenue packet path"],
            "Creates a template only; operator must replace placeholders with redacted receipt/delivery evidence.",
        ),
        _step(
            "delivery proof packet authoring",
            (
                "chaseos ventureops delivery-proof-packet --delivery-proof-id ID --client-label LABEL "
                "--delivery-reference-id ID --client-safe-delivery-artifact-path PATH "
                "--live-client-proof-path PATH --output PATH --operator-approved "
                "--operator-attested-delivery-performed --json"
            ),
            "available",
            [
                "operator approval for delivery proof authoring",
                "client-safe delivery artifact",
                "valid live-client workflow proof artifact",
            ],
            ["operator-selected delivery proof artifact path"],
            "Writes an operator-attested delivery proof artifact and does not perform external delivery, CRM/payment mutation, invoice send, provider/browser action, or revenue claim.",
        ),
        _step(
            "revenue evidence packet authoring",
            (
                "chaseos ventureops revenue-evidence-packet --revenue-proof-id ID --client-label LABEL "
                "--payment-reference-id ID --payment-status received --amount AMOUNT --currency USD "
                "--receipt-artifact-path PATH --delivery-proof-path PATH --crm-reference-id ID "
                "--approval-id ID --live-client-proof-path PATH --output PATH --operator-approved --json"
            ),
            "available",
            [
                "operator approval for revenue evidence packet authoring",
                "redacted receipt artifact",
                "valid delivery proof artifact",
                "valid live-client workflow proof artifact",
            ],
            ["operator-selected revenue packet path"],
            "Writes a revenue packet from explicit operator-supplied proof fields without payment/CRM mutation, invoice send, accounting claim, or revenue claim.",
        ),
        _step(
            "revenue evidence validation",
            f"chaseos ventureops validate-revenue-evidence --packet {revenue_packet} --json",
            _status(revenue_packet_valid),
            ["redacted live revenue evidence packet"],
            [],
            "Validates packet shape without payment/CRM mutation or accounting claims.",
        ),
        _step(
            "live revenue readiness",
            (
                "chaseos ventureops live-revenue-proof-readiness "
                f"--revenue-packet {revenue_packet} --live-client-proof-path {live_client_proof} --json"
            ),
            _status(revenue_ready),
            ["valid revenue packet", "valid live-client workflow proof artifact"],
            [],
            "Checks proof-only revenue prerequisites before any revenue artifact write.",
        ),
        _step(
            "proof-only live revenue artifact",
            (
                "chaseos ventureops live-revenue-proof "
                f"--revenue-packet {revenue_packet} --live-client-proof-path {live_client_proof} "
                "--execute-proof --json"
            ),
            _status(revenue_ready),
            ["valid revenue packet", "valid live-client workflow proof artifact", "operator approval to execute proof"],
            ["local proof-only revenue artifact"],
            "Writes proof-only local revenue evidence without invoice send, payment/CRM mutation, accounting claim, or revenue claim.",
        ),
        _step(
            "final evidence bundle packet authoring",
            FINAL_EVIDENCE_BUNDLE_PACKET_COMMAND,
            "blocked" if not audit.get("complete") else "ready",
            [
                "final scope packet",
                "live-client workflow proof",
                "delivery proof",
                "revenue packet",
                "proof-only live revenue artifact",
                "unused output path",
            ],
            ["operator-selected final evidence bundle path"],
            "Writes the final evidence bundle envelope for validator intake; does not execute live workflows, create proof evidence, send externally, mutate CRM/payment systems, call providers/browsers, send invoices, or make revenue claims.",
        ),
        _step(
            "final evidence bundle validation",
            FINAL_EVIDENCE_BUNDLE_COMMAND,
            "blocked" if not audit.get("complete") else "ready",
            [
                "final scope packet",
                "live-client workflow proof",
                "delivery proof",
                "revenue packet",
                "proof-only live revenue artifact",
                "unused final evidence bundle validation report path",
            ],
            ["operator-selected final evidence bundle validation report path"],
            "Validates the complete final proof-chain bundle and writes the ready validation report required before audit rerun; does not execute live workflows, create proof evidence, send externally, mutate CRM/payment systems, call providers/browsers, send invoices, or make revenue claims.",
        ),
        _step(
            "final audit rerun",
            FINAL_FEATURE_FAMILY_AUDIT_COMMAND,
            "blocked" if not audit.get("complete") else "ready",
            [
                "live client workflow proof",
                "proof-only live revenue artifact",
                "ready final evidence bundle validation report",
            ],
            ["operator-selected final feature-family completion audit report path"],
            "Rerun only after real proof artifacts exist and the final evidence bundle validator reports ready_for_completion_audit=true; writes a durable completion audit report and current repo still reports not_complete.",
        ),
    ]

    passover_verified = bool(
        audit.get("passover_valid")
        and audit.get("handover_alias_valid")
        and audit.get("requested_handover_alias_valid")
    )
    runbook_checklist = [
        _checklist_item(
            "validated final external passover",
            "verified" if passover_verified else "failed",
            [
                str(audit.get("passover_path")),
                str(audit.get("handover_path")),
                str(audit.get("requested_handover_path")),
            ]
            if passover_verified
            else [],
            "The canonical passover and exact typo-compatible handover alias are valid.",
        ),
        _checklist_item(
            "real client workflow execution input",
            _status(scope_ready),
            [str(scope_packet_path)] if scope_packet_path and scope_ready else [],
            "Requires real client-approved scope evidence and existing approved source files.",
        ),
        _checklist_item(
            "live revenue workflow execution input",
            _status(revenue_ready),
            [str(revenue_packet_path), str(live_client_proof_path)] if revenue_ready else [],
            "Requires redacted revenue evidence and a valid live-client workflow proof artifact.",
        ),
        _checklist_item(
            "final evidence bundle validation",
            "blocked" if not audit.get("complete") else "ready",
            [],
            "Requires `chaseos ventureops final-evidence-bundle --bundle PATH --write-report --report-path PATH --json` to report ready_for_completion_audit=true before final completion audit rerun.",
        ),
        _checklist_item(
            "final evidence bundle validation report writeback",
            "blocked" if not audit.get("complete") else "ready",
            [],
            "Requires `--write-report --report-path PATH` so the completion audit can discover and revalidate a ready final evidence bundle validation report.",
        ),
        _checklist_item(
            "final evidence bundle packet authoring",
            "blocked" if not audit.get("complete") else "ready",
            [],
            "Requires `chaseos ventureops final-evidence-bundle-packet` to write the bundle envelope from the final proof-chain paths.",
        ),
        _checklist_item(
            "final completion audit report writeback",
            "blocked" if not audit.get("complete") else "ready",
            [],
            "Requires `chaseos ventureops feature-family-completion-audit --write-report --report-path PATH --json` so final completion has a durable audit report artifact.",
        ),
        _checklist_item(
            "no external side effects preserved",
            "verified",
            [],
            "This runbook does not execute live workflows, external sends, CRM/payment mutations, provider calls, browser actions, invoices, or revenue claims.",
        ),
    ]
    failed = [item["requirement"] for item in runbook_checklist if item["status"] == "failed"]
    complete = bool(audit.get("complete") and not failed)
    if scope_ready:
        next_command = closeout.get("next_command")
        next_required_action = closeout.get("next_required_action")
    else:
        next_command = REAL_CLIENT_INPUT_MANIFEST_COMMAND
        next_required_action = "collect real-client scope inputs through real-client-input-manifest"

    return {
        "ok": not failed and bool(audit.get("ok") and closeout.get("ok")),
        "complete": complete,
        "readiness_status": "ready_for_completion" if complete else "blocked",
        "completion_decision": "complete" if complete else "not_complete",
        "status": audit.get("status"),
        "passover_path": audit.get("passover_path"),
        "handover_path": audit.get("handover_path"),
        "requested_handover_path": audit.get("requested_handover_path"),
        "passover_valid": bool(audit.get("passover_valid")),
        "handover_alias_valid": bool(audit.get("handover_alias_valid")),
        "requested_handover_alias_valid": bool(audit.get("requested_handover_alias_valid")),
        "missing_requirements": list(audit.get("missing_requirements") or []),
        "next_required_real_use_pass": closeout.get("next_required_real_use_pass"),
        "next_guarded_command": closeout.get("next_guarded_command"),
        "next_required_inputs": closeout.get("next_required_inputs") or [],
        "ready_for_live_client_workflow_proof": scope_ready,
        "ready_for_live_revenue_proof": revenue_ready,
        "final_evidence_bundle_validation_required": True,
        "ready_for_final_audit_rerun": complete,
        "required_operator_inputs": REQUIRED_OPERATOR_INPUTS,
        "command_sequence": command_sequence,
        "runbook_stage_count": len(command_sequence),
        "runbook_checklist": runbook_checklist,
        "next_required_action": next_required_action,
        "next_command": next_command,
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
            "operator runbook only; validates and orders the remaining external proof commands but does not "
            "execute live workflows, send externally, mutate CRM/payment systems, call providers/browsers, "
            "send invoices, or make accounting/revenue claims"
        ),
    }


def write_final_external_execution_runbook_report(payload: dict[str, Any], path: str | Path) -> dict[str, Any]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {**payload, "report_written": True, "report_path": str(target)}
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
