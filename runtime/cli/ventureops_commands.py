"""VentureOps command handlers for the canonical ChaseOS CLI."""

from __future__ import annotations

import argparse
from datetime import date
import json
import sys
from pathlib import Path

from runtime.ventureops.validation import (
    audit_external_readiness_completion,
    validate_live_revenue_evidence,
    validate_real_client_scope_evidence,
    validate_scope_evidence_approval_artifact,
    validate_scope_evidence_source_paths,
)
from runtime.ventureops.evidence_intake import build_evidence_intake
from runtime.ventureops.evidence_discovery_preflight import (
    build_evidence_discovery_preflight,
    write_evidence_discovery_preflight_report,
)
from runtime.ventureops.feature_family_completion_audit import (
    build_feature_family_completion_audit,
    write_feature_family_completion_audit_report,
)
from runtime.ventureops.final_external_execution_runbook import (
    build_final_external_execution_runbook,
    write_final_external_execution_runbook_report,
)
from runtime.ventureops.final_external_evidence_bundle import (
    validate_final_external_evidence_bundle,
    write_final_external_evidence_bundle_report,
)
from runtime.ventureops.final_evidence_bundle_packet_builder import build_final_evidence_bundle_packet
from runtime.ventureops.live_client_readiness import build_live_client_scope_proof_readiness
from runtime.ventureops.live_client_scope_proof import run_live_client_scope_proof
from runtime.ventureops.live_client_workflow_proof import run_live_client_workflow_proof
from runtime.ventureops.mission_activation_approval_consumption import consume_mission_activation_approval
from runtime.ventureops.mission_activation_approval_packet import build_mission_activation_approval_packet
from runtime.ventureops.mission_activation_gate import consume_mission_activation_gate
from runtime.ventureops.mission_activation_readiness import build_mission_activation_readiness
from runtime.ventureops.mission_agent_bus_enqueue_gate import consume_mission_agent_bus_enqueue_gate
from runtime.ventureops.mission_external_client_evidence_gate import (
    build_mission_external_client_evidence_gate,
)
from runtime.ventureops.mission_manifest_promotion_review_gate import (
    consume_mission_manifest_promotion_review_gate,
)
from runtime.ventureops.mission_runtime_claim_result_gate import consume_mission_runtime_claim_result_gate
from runtime.ventureops.real_evidence_closeout_readiness import build_real_evidence_closeout_readiness
from runtime.ventureops.real_client_input_manifest import (
    build_real_client_input_manifest,
    write_real_client_input_manifest_report,
)
from runtime.ventureops.live_revenue_proof import run_live_revenue_proof
from runtime.ventureops.live_revenue_readiness import build_live_revenue_proof_readiness
from runtime.ventureops.scope_approval_packet_builder import build_scope_approval_packet
from runtime.ventureops.scope_evidence_packet_builder import build_scope_evidence_packet
from runtime.ventureops.revenue_evidence_packet_builder import build_revenue_evidence_packet
from runtime.ventureops.delivery_proof_packet_builder import build_delivery_proof_packet
from runtime.ventureops.autonomous_implementation_completion import (
    build_autonomous_implementation_completion,
)


def _load_json_packet(path: str) -> dict:
    packet_path = Path(path)
    data = json.loads(packet_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{packet_path} did not contain a JSON object")
    return data


def _default_proof_date() -> str:
    return date.today().isoformat()


def _next_available_default_report_path(vault_root: Path, base_name: str) -> Path:
    base = Path("07_LOGS") / "Workflow-Proofs" / base_name
    candidate = base
    suffix = 2
    while (vault_root / candidate).exists():
        candidate = base.with_name(f"{base.stem}-{suffix}{base.suffix}")
        suffix += 1
    return candidate


def _resolve_guarded_report_target(path: str | Path, vault_root: Path) -> tuple[Path | None, str | None, str | None]:
    raw = Path(path)
    resolved = raw.resolve() if raw.is_absolute() else (vault_root / raw).resolve()
    try:
        relative = resolved.relative_to(vault_root)
    except ValueError:
        return None, None, f"report_path escapes vault root: {path}"
    return resolved, str(relative).replace("\\", "/"), None


def _write_guarded_json_report(payload: dict, report_path: str | Path, *, vault_root: Path) -> dict:
    target, relative, error = _resolve_guarded_report_target(report_path, vault_root)
    if error:
        return {
            **payload,
            "ok": False,
            "report_written": False,
            "report_path": None,
            "report_write_blocked": True,
            "errors": [*list(payload.get("errors") or []), error],
        }
    assert target is not None
    assert relative is not None
    if target.exists():
        return {
            **payload,
            "ok": False,
            "report_written": False,
            "report_path": None,
            "report_write_blocked": True,
            "errors": [
                *list(payload.get("errors") or []),
                f"report path already exists: {relative}",
            ],
        }
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        **payload,
        "report_written": True,
        "report_path": str(report_path) if not Path(report_path).is_absolute() else str(target),
        "report_write_blocked": False,
        "errors": list(payload.get("errors") or []),
    }
    target.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return payload


def _write_guarded_json_packet(payload: dict, packet_path: str | Path, *, vault_root: Path) -> dict:
    target, relative, error = _resolve_guarded_report_target(packet_path, vault_root)
    if error:
        return {
            **payload,
            "ok": False,
            "packet_written": False,
            "packet_path": None,
            "packet_write_blocked": True,
            "errors": [*list(payload.get("errors") or []), error.replace("report_path", "packet_path")],
        }
    assert target is not None
    assert relative is not None
    if target.exists():
        return {
            **payload,
            "ok": False,
            "packet_written": False,
            "packet_path": None,
            "packet_write_blocked": True,
            "errors": [
                *list(payload.get("errors") or []),
                f"packet path already exists: {relative}",
            ],
        }
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        **payload,
        "packet_written": True,
        "packet_path": str(packet_path) if not Path(packet_path).is_absolute() else str(target),
        "packet_write_blocked": False,
        "errors": list(payload.get("errors") or []),
    }
    target.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return payload


def _write_readiness_report(payload: dict, report_path: str | None, default_name: str) -> dict:
    target = Path(report_path) if report_path else Path("07_LOGS") / "Workflow-Proofs" / default_name
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {**payload, "report_written": True, "report_path": str(target)}
    target.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return payload


def _build_evidence_template(kind: str) -> tuple[dict, str, str]:
    normalized = kind.strip().lower()
    if normalized == "scope":
        return (
            {
                "type": "ventureops-real-client-scope-evidence",
                "template_only": True,
                "client_approved_scope_id": "",
                "client_label": "",
                "approval_id": "",
                "approval_status": "",
                "approval_artifact_path": "",
                "approved_read_paths": [],
                "redaction_policy": "client_safe_summary_only",
                "delivery_boundary": "no_external_delivery",
                "notes": "Replace placeholders with explicit real client-approved scope evidence before validation.",
            },
            "chaseos ventureops validate-scope-evidence --packet PATH --vault-root VAULT_ROOT --json",
            "Template only; not ready for validation until real client-approved scope fields are filled.",
        )
    if normalized == "revenue":
        return (
            {
                "type": "ventureops-live-revenue-evidence",
                "template_only": True,
                "revenue_proof_id": "",
                "workflow_id": "agent_runtime_governance_audit",
                "client_label": "",
                "payment_reference_id": "",
                "payment_status": "",
                "amount": 0,
                "currency": "",
                "receipt_artifact_path": "",
                "delivery_proof_path": "",
                "crm_reference_id": "",
                "approval_id": "",
                "revenue_recognition_boundary": "proof_only_no_accounting_claim",
                "notes": "Replace placeholders with redacted receipt and delivery proof evidence after live client workflow proof exists.",
            },
            "chaseos ventureops validate-revenue-evidence --packet PATH --json",
            "Template only; not ready for validation until live delivery and redacted payment evidence fields are filled.",
        )
    raise ValueError("kind must be scope or revenue")


def cmd_ventureops_evidence_template(args: argparse.Namespace) -> int:
    """chaseos ventureops evidence-template --kind scope|revenue [--output PATH] [--json]."""
    try:
        kind = str(getattr(args, "kind"))
        template, validator_command, boundary = _build_evidence_template(kind)
        output_path = getattr(args, "output", None)
        template_written = False
        if output_path:
            target = Path(output_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(template, indent=2), encoding="utf-8")
            template_written = True
        payload = {
            "ok": True,
            "kind": kind.strip().lower(),
            "template_written": template_written,
            "output_path": str(output_path) if output_path else None,
            "ready_for_validation": False,
            "validator_command": validator_command,
            "packet_template": template,
            "boundary": boundary,
            "live_client_scope_proof_performed": False,
            "live_client_data_ingested": False,
            "payment_mutation_performed": False,
            "crm_mutation_performed": False,
            "revenue_claim_made": False,
        }
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0

    print(f"VentureOps {payload['kind']} evidence template")
    if payload["template_written"]:
        print(f"  wrote: {payload['output_path']}")
    print(f"  validator: {payload['validator_command']}")
    print(f"  boundary: {payload['boundary']}")
    return 0


def cmd_ventureops_external_readiness_audit(args: argparse.Namespace) -> int:
    """chaseos ventureops external-readiness-audit [--vault-root PATH] [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = audit_external_readiness_completion(vault_root)
        if getattr(args, "write_report", False):
            report_path = getattr(args, "report_path", None)
            if not report_path:
                report_path = _next_available_default_report_path(
                    vault_root,
                    f"{_default_proof_date()}_ventureops-external-readiness-audit-report.json",
                )
            payload = _write_guarded_json_report(payload, report_path, vault_root=vault_root)
        else:
            payload = {**payload, "report_written": False, "report_path": None}
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0 if payload.get("ok") else 1

    print(f"VentureOps external readiness: {payload.get('completion_decision')}")
    print(f"  complete: {payload.get('complete')}")
    print(f"  status:   {payload.get('status')}")
    for missing in payload.get("missing_requirements") or []:
        print(f"  missing:  {missing}")
    print("  boundary: read-only audit; no live client run, external send, CRM/payment mutation, or revenue claim.")
    return 0 if payload.get("ok") else 1


def cmd_ventureops_validate_scope_evidence(args: argparse.Namespace) -> int:
    """chaseos ventureops validate-scope-evidence --packet PATH [--vault-root PATH] [--json]."""
    try:
        packet_path = str(getattr(args, "packet"))
        packet = _load_json_packet(packet_path)
        validation = validate_real_client_scope_evidence(packet)
        payload = {
            **validation,
            "packet_path": packet_path,
            "scope_evidence_valid": validation["ok"],
            "full_scope_validation_performed": False,
            "live_client_scope_proof_performed": False,
            "live_client_data_ingested": False,
            "external_delivery_performed": False,
            "boundary": "packet validation only; does not prove a live client workflow",
        }
        vault_root_arg = getattr(args, "vault_root", None)
        if vault_root_arg:
            vault_root = Path(vault_root_arg).resolve()
            approval_validation = validate_scope_evidence_approval_artifact(vault_root, packet)
            source_validation = validate_scope_evidence_source_paths(
                vault_root,
                validation.get("safe_read_paths") or [],
            )
            errors = list(validation.get("errors") or [])
            for error in approval_validation.get("errors") or []:
                if error not in errors:
                    errors.append(error)
            for error in source_validation.get("errors") or []:
                if error not in errors:
                    errors.append(error)
            payload = {
                **payload,
                "ok": bool(validation["ok"] and approval_validation["ok"] and source_validation["ok"]),
                "errors": errors,
                "vault_root": str(vault_root),
                "full_scope_validation_performed": True,
                "scope_approval_artifact_valid": bool(approval_validation.get("scope_approval_artifact_valid")),
                "scope_approval_validation": approval_validation.get("scope_approval_validation"),
                "scope_sources_valid": bool(source_validation.get("ok")),
                "scope_source_validation": source_validation,
                "boundary": (
                    "full scope validation only; validates packet, typed approval artifact, and approved source files "
                    "without proving a live client workflow"
                ),
            }
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0 if payload["ok"] else 1

    print(f"VentureOps real client scope evidence valid: {payload['scope_evidence_valid']}")
    print(f"  approved_read_paths: {payload.get('approved_read_path_count', 0)}")
    if payload.get("full_scope_validation_performed"):
        print(f"  scope approval artifact valid: {payload.get('scope_approval_artifact_valid')}")
        print(f"  approved source files valid: {payload.get('scope_sources_valid')}")
    if payload.get("errors"):
        print("  errors:")
        for error in payload["errors"]:
            print(f"    - {error}")
    print(f"  boundary: {payload['boundary']}")
    return 0 if payload["ok"] else 1


def cmd_ventureops_validate_revenue_evidence(args: argparse.Namespace) -> int:
    """chaseos ventureops validate-revenue-evidence --packet PATH [--json]."""
    try:
        packet_path = str(getattr(args, "packet"))
        validation = validate_live_revenue_evidence(_load_json_packet(packet_path))
        payload = {
            **validation,
            "packet_path": packet_path,
            "revenue_evidence_valid": validation["ok"],
            "revenue_claim_made": False,
            "payment_mutation_performed": False,
            "crm_mutation_performed": False,
            "boundary": "packet validation only; not an accounting claim and not live revenue proof by itself",
        }
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0 if payload["ok"] else 1

    print(f"VentureOps live revenue evidence valid: {payload['revenue_evidence_valid']}")
    print(f"  amount: {payload.get('amount')} {payload.get('currency')}")
    if payload.get("errors"):
        print("  errors:")
        for error in payload["errors"]:
            print(f"    - {error}")
    print("  boundary: packet validation only; no CRM/payment mutation or revenue claim.")
    return 0 if payload["ok"] else 1


def cmd_ventureops_evidence_intake(args: argparse.Namespace) -> int:
    """chaseos ventureops evidence-intake [--scope-packet PATH] [--revenue-packet PATH] [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = build_evidence_intake(
            vault_root,
            scope_packet_path=getattr(args, "scope_packet", None),
            revenue_packet_path=getattr(args, "revenue_packet", None),
            live_client_proof_path=getattr(args, "live_client_proof_path", None),
        )
        if getattr(args, "write_report", False):
            report_path = getattr(args, "report_path", None)
            if not report_path:
                report_path = _next_available_default_report_path(
                    vault_root,
                    f"{_default_proof_date()}_ventureops-evidence-intake-report.json",
                )
            payload = _write_guarded_json_report(payload, report_path, vault_root=vault_root)
        else:
            payload = {**payload, "report_written": False, "report_path": None}
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0 if payload.get("ok") else 1

    print(f"VentureOps evidence intake: {payload['intake_status']}")
    print(f"  scope_evidence_valid: {payload['scope_evidence_valid']}")
    print(f"  revenue_evidence_valid: {payload['revenue_evidence_valid']}")
    print(f"  next: {payload['next_required_action']}")
    if payload.get("blockers"):
        print("  blockers:")
        for blocker in payload["blockers"]:
            print(f"    - {blocker}")
    print("  boundary: intake only; no live workflow, external send, CRM/payment mutation, or revenue claim.")
    return 0 if payload.get("ok") else 1


def cmd_ventureops_evidence_discovery_preflight(args: argparse.Namespace) -> int:
    """chaseos ventureops evidence-discovery-preflight [--vault-root PATH] [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = build_evidence_discovery_preflight(
            vault_root,
            scan_roots=getattr(args, "scan_root", None),
        )
        if getattr(args, "write_report", False):
            report_path = getattr(args, "report_path", None) or (
                Path("07_LOGS") / "Workflow-Proofs" / "ventureops-evidence-discovery-preflight.json"
            )
            payload = write_evidence_discovery_preflight_report(payload, report_path)
        else:
            payload = {**payload, "report_written": False, "report_path": None}
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0 if payload.get("ok") else 1

    print(f"VentureOps evidence discovery preflight: {payload['discovery_status']}")
    print(f"  selected_scope_packet_path: {payload.get('selected_scope_packet_path')}")
    print(f"  selected_live_client_workflow_proof_path: {payload.get('selected_live_client_workflow_proof_path')}")
    print(f"  selected_revenue_packet_path: {payload.get('selected_revenue_packet_path')}")
    print(f"  next: {payload['next_required_action']}")
    if payload.get("blockers"):
        print("  blockers:")
        for blocker in payload["blockers"]:
            print(f"    - {blocker}")
    print("  boundary: discovery only; no live workflow, external send, CRM/payment mutation, or revenue claim.")
    return 0 if payload.get("ok") else 1


def cmd_ventureops_real_client_input_manifest(args: argparse.Namespace) -> int:
    """chaseos ventureops real-client-input-manifest [--client-label LABEL] [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = build_real_client_input_manifest(
            vault_root,
            client_label=getattr(args, "client_label", None),
            client_approved_scope_id=getattr(args, "scope_id", None),
            approval_id=getattr(args, "approval_id", None),
            approved_read_paths=list(getattr(args, "approved_read_path") or []),
            approval_output_path=getattr(args, "approval_output", None),
            approval_artifact_path=getattr(args, "approval_artifact_path", None),
            scope_packet_output_path=getattr(args, "scope_packet_output", None),
        )
        if getattr(args, "write_report", False):
            report_path = getattr(args, "report_path", None)
            if not report_path:
                report_path = _next_available_default_report_path(
                    vault_root,
                    f"{_default_proof_date()}_ventureops-real-client-input-manifest.json",
                )
            payload = write_real_client_input_manifest_report(payload, report_path, vault_root=vault_root)
        else:
            payload = {**payload, "report_written": False, "report_path": None}
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0 if payload.get("ok") else 1

    print(f"VentureOps real-client input manifest: {payload['manifest_status']}")
    print(f"  source_paths_valid: {payload.get('source_paths_valid')}")
    print(f"  scope_approval_artifact_valid: {payload.get('scope_approval_artifact_valid')}")
    print(f"  next: {payload['next_required_action']}")
    print(f"  command: {payload['next_command']}")
    if payload.get("errors"):
        print("  errors:")
        for error in payload["errors"]:
            print(f"    - {error}")
    print("  boundary: manifest only; no live workflow, external send, CRM/payment mutation, or revenue claim.")
    return 0 if payload.get("ok") else 1


def cmd_ventureops_scope_approval_packet(args: argparse.Namespace) -> int:
    """chaseos ventureops scope-approval-packet --output PATH [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = build_scope_approval_packet(
            vault_root,
            approval_id=str(getattr(args, "approval_id")),
            client_label=str(getattr(args, "client_label")),
            client_approved_scope_id=str(getattr(args, "scope_id")),
            approved_read_paths=list(getattr(args, "approved_read_path") or []),
            output_path=str(getattr(args, "output")),
            operator_approved=bool(getattr(args, "operator_approved", False)),
            operator_attested_scope_approved=bool(getattr(args, "operator_attested_scope_approved", False)),
        )
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0 if payload.get("ok") else 1

    if payload.get("ok"):
        print("VentureOps scope approval artifact: written")
        print(f"  approval_artifact_path: {payload.get('approval_artifact_path')}")
    else:
        print("VentureOps scope approval artifact blocked")
        for error in payload.get("errors") or []:
            print(f"  - {error}")
    print("  boundary: approval artifact authoring only; no live workflow or external side effect.")
    return 0 if payload.get("ok") else 1


def cmd_ventureops_scope_evidence_packet(args: argparse.Namespace) -> int:
    """chaseos ventureops scope-evidence-packet --output PATH [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = build_scope_evidence_packet(
            vault_root,
            client_label=str(getattr(args, "client_label")),
            client_approved_scope_id=str(getattr(args, "scope_id")),
            approval_id=str(getattr(args, "approval_id")),
            approval_artifact_path=str(getattr(args, "approval_artifact_path")),
            approved_read_paths=list(getattr(args, "approved_read_path") or []),
            output_path=str(getattr(args, "output")),
            operator_approved=bool(getattr(args, "operator_approved", False)),
        )
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0 if payload.get("ok") else 1

    if payload.get("ok"):
        print("VentureOps scope evidence packet: written")
        print(f"  packet_path: {payload.get('packet_path')}")
    else:
        print("VentureOps scope evidence packet blocked")
        for error in payload.get("errors") or []:
            print(f"  - {error}")
    print("  boundary: packet authoring only; no live workflow, external send, CRM/payment mutation, or revenue claim.")
    return 0 if payload.get("ok") else 1


def cmd_ventureops_revenue_evidence_packet(args: argparse.Namespace) -> int:
    """chaseos ventureops revenue-evidence-packet --output PATH [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = build_revenue_evidence_packet(
            vault_root,
            revenue_proof_id=str(getattr(args, "revenue_proof_id")),
            client_label=str(getattr(args, "client_label")),
            payment_reference_id=str(getattr(args, "payment_reference_id")),
            payment_status=str(getattr(args, "payment_status")),
            amount=str(getattr(args, "amount")),
            currency=str(getattr(args, "currency")),
            receipt_artifact_path=str(getattr(args, "receipt_artifact_path")),
            delivery_proof_path=str(getattr(args, "delivery_proof_path")),
            crm_reference_id=str(getattr(args, "crm_reference_id")),
            approval_id=str(getattr(args, "approval_id")),
            live_client_proof_path=str(getattr(args, "live_client_proof_path")),
            output_path=str(getattr(args, "output")),
            operator_approved=bool(getattr(args, "operator_approved", False)),
        )
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0 if payload.get("ok") else 1

    if payload.get("ok"):
        print("VentureOps revenue evidence packet: written")
        print(f"  packet_path: {payload.get('packet_path')}")
    else:
        print("VentureOps revenue evidence packet blocked")
        for error in payload.get("errors") or []:
            print(f"  - {error}")
    print("  boundary: packet authoring only; no payment/CRM mutation, invoice send, external send, or revenue claim.")
    return 0 if payload.get("ok") else 1


def cmd_ventureops_delivery_proof_packet(args: argparse.Namespace) -> int:
    """chaseos ventureops delivery-proof-packet --output PATH [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = build_delivery_proof_packet(
            vault_root,
            delivery_proof_id=str(getattr(args, "delivery_proof_id")),
            client_label=str(getattr(args, "client_label")),
            delivery_reference_id=str(getattr(args, "delivery_reference_id")),
            client_safe_delivery_artifact_path=str(getattr(args, "client_safe_delivery_artifact_path")),
            live_client_proof_path=str(getattr(args, "live_client_proof_path")),
            output_path=str(getattr(args, "output")),
            operator_approved=bool(getattr(args, "operator_approved", False)),
            operator_attested_delivery_performed=bool(
                getattr(args, "operator_attested_delivery_performed", False)
            ),
            delivery_status=str(getattr(args, "delivery_status", "delivered")),
        )
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0 if payload.get("ok") else 1

    if payload.get("ok"):
        print("VentureOps delivery proof artifact: written")
        print(f"  packet_path: {payload.get('packet_path')}")
    else:
        print("VentureOps delivery proof artifact blocked")
        for error in payload.get("errors") or []:
            print(f"  - {error}")
    print("  boundary: delivery proof authoring only; no external send, CRM/payment mutation, invoice send, or revenue claim.")
    return 0 if payload.get("ok") else 1


def cmd_ventureops_real_evidence_closeout_readiness(args: argparse.Namespace) -> int:
    """chaseos ventureops real-evidence-closeout-readiness [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = build_real_evidence_closeout_readiness(
            vault_root,
            scope_packet_path=getattr(args, "scope_packet", None),
            revenue_packet_path=getattr(args, "revenue_packet", None),
            live_client_proof_path=getattr(args, "live_client_proof_path", None),
        )
        if getattr(args, "write_report", False):
            report_path = getattr(args, "report_path", None)
            if not report_path:
                report_path = _next_available_default_report_path(
                    vault_root,
                    f"{_default_proof_date()}_ventureops-real-evidence-closeout-readiness-report.json",
                )
            payload = _write_guarded_json_report(payload, report_path, vault_root=vault_root)
        else:
            payload = {**payload, "report_written": False, "report_path": None}
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0 if payload.get("ok") else 1

    print(f"VentureOps real evidence closeout readiness: {payload['readiness_status']}")
    print(f"  completion_decision: {payload['completion_decision']}")
    print(f"  ready_for_completion: {payload['ready_for_completion']}")
    for missing in payload.get("missing_requirements") or []:
        print(f"  missing: {missing}")
    print(f"  next: {payload['next_required_action']}")
    print("  boundary: closeout readiness only; no live workflow, external send, CRM/payment mutation, or revenue claim.")
    return 0 if payload.get("ok") else 1


def cmd_ventureops_feature_family_completion_audit(args: argparse.Namespace) -> int:
    """chaseos ventureops feature-family-completion-audit [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = build_feature_family_completion_audit(vault_root)
        if getattr(args, "write_report", False):
            report_path = getattr(args, "report_path", None)
            if not report_path:
                report_path = _next_available_default_report_path(
                    vault_root,
                    f"{_default_proof_date()}_ventureops-feature-family-completion-audit-report.json",
                )
            payload = write_feature_family_completion_audit_report(payload, report_path, vault_root=vault_root)
        else:
            payload = {**payload, "report_written": False, "report_path": None}
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0 if payload.get("ok") else 1

    print(f"VentureOps feature-family completion audit: {payload['completion_decision']}")
    print(f"  complete: {payload['complete']}")
    print(f"  registry_workflow_count: {payload['registry_workflow_count']}")
    for missing in payload.get("missing_requirements") or []:
        print(f"  missing: {missing}")
    print("  boundary: audit only; no live workflow, external send, CRM/payment mutation, or revenue claim.")
    return 0 if payload.get("ok") else 1


def cmd_ventureops_autonomous_implementation_completion(args: argparse.Namespace) -> int:
    """chaseos ventureops autonomous-implementation-completion [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = build_autonomous_implementation_completion(vault_root)
        if getattr(args, "write_report", False):
            report_path = getattr(args, "report_path", None)
            if not report_path:
                report_path = _next_available_default_report_path(
                    vault_root,
                    f"{_default_proof_date()}_ventureops-autonomous-implementation-completion-report.json",
                )
            payload = _write_guarded_json_report(payload, report_path, vault_root=vault_root)
        else:
            payload = {**payload, "report_written": False, "report_path": None}
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0 if payload.get("ok") else 1

    print(f"VentureOps autonomous implementation completion: {payload['completion_decision']}")
    print(f"  feature_implementation_complete: {payload['feature_implementation_complete']}")
    print(f"  operator_evidence_required_for_tests: {payload['operator_evidence_required_for_tests']}")
    print(f"  real_world_delivery_revenue_complete: {payload['real_world_delivery_revenue_complete']}")
    for missing in payload.get("real_world_missing_requirements") or []:
        print(f"  real-world missing: {missing}")
    print("  boundary: implementation audit only; no live workflow, external send, CRM/payment mutation, or revenue claim.")
    return 0 if payload.get("ok") else 1


def cmd_ventureops_final_external_execution_runbook(args: argparse.Namespace) -> int:
    """chaseos ventureops final-external-execution-runbook [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = build_final_external_execution_runbook(
            vault_root,
            scope_packet_path=getattr(args, "scope_packet", None),
            revenue_packet_path=getattr(args, "revenue_packet", None),
            live_client_proof_path=getattr(args, "live_client_proof_path", None),
        )
        if getattr(args, "write_report", False):
            report_path = getattr(args, "report_path", None)
            if not report_path:
                report_path = _next_available_default_report_path(
                    vault_root,
                    f"{_default_proof_date()}_ventureops-final-external-execution-runbook-report.json",
                )
            payload = _write_guarded_json_report(payload, report_path, vault_root=vault_root)
        else:
            payload = {**payload, "report_written": False, "report_path": None}
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0 if payload.get("ok") else 1

    print(f"VentureOps final external execution runbook: {payload['completion_decision']}")
    print(f"  readiness_status: {payload['readiness_status']}")
    print(f"  stages: {payload['runbook_stage_count']}")
    print(f"  next: {payload['next_required_action']}")
    for missing in payload.get("missing_requirements") or []:
        print(f"  missing: {missing}")
    print("  boundary: runbook only; no live workflow, external send, CRM/payment mutation, or revenue claim.")
    return 0 if payload.get("ok") else 1


def cmd_ventureops_final_evidence_bundle(args: argparse.Namespace) -> int:
    """chaseos ventureops final-evidence-bundle --bundle PATH [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = validate_final_external_evidence_bundle(
            vault_root,
            bundle_path=str(getattr(args, "bundle")),
        )
        if getattr(args, "write_report", False):
            report_path = getattr(args, "report_path", None)
            if not report_path:
                report_path = _next_available_default_report_path(
                    vault_root,
                    f"{_default_proof_date()}_ventureops-final-evidence-bundle-validation-report.json",
                )
            payload = write_final_external_evidence_bundle_report(
                payload,
                report_path,
                vault_root=vault_root,
            )
        else:
            payload = {**payload, "report_written": False, "report_path": None}
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0 if payload.get("ok") else 1

    print(f"VentureOps final evidence bundle: {payload['validation_status']}")
    print(f"  ready_for_completion_audit: {payload['ready_for_completion_audit']}")
    for blocker in payload.get("blockers") or []:
        print(f"  blocker: {blocker}")
    print(f"  next: {payload['next_command']}")
    print("  boundary: validation only; no live workflow, external send, CRM/payment mutation, or revenue claim.")
    return 0 if payload.get("ok") else 1


def cmd_ventureops_final_evidence_bundle_packet(args: argparse.Namespace) -> int:
    """chaseos ventureops final-evidence-bundle-packet --output PATH [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = build_final_evidence_bundle_packet(
            vault_root,
            scope_packet_path=str(getattr(args, "scope_packet_path")),
            live_client_workflow_proof_path=str(getattr(args, "live_client_workflow_proof_path")),
            delivery_proof_path=str(getattr(args, "delivery_proof_path")),
            revenue_packet_path=str(getattr(args, "revenue_packet_path")),
            live_revenue_proof_path=str(getattr(args, "live_revenue_proof_path")),
            output_path=str(getattr(args, "output")),
        )
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0 if payload.get("ok") else 1

    print(f"VentureOps final evidence bundle packet: {'written' if payload['packet_written'] else 'blocked'}")
    for error in payload.get("errors") or []:
        print(f"  error: {error}")
    print(f"  next: {payload['next_command']}")
    print("  boundary: packet authoring only; no live workflow, external send, CRM/payment mutation, or revenue claim.")
    return 0 if payload.get("ok") else 1


def cmd_ventureops_live_client_proof_readiness(args: argparse.Namespace) -> int:
    """chaseos ventureops live-client-proof-readiness [--scope-packet PATH] [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = build_live_client_scope_proof_readiness(
            vault_root,
            scope_packet_path=getattr(args, "scope_packet", None),
        )
        if getattr(args, "write_report", False):
            report_path = getattr(args, "report_path", None)
            if not report_path:
                report_path = _next_available_default_report_path(
                    vault_root,
                    f"{_default_proof_date()}_ventureops-live-client-proof-readiness-report.json",
                )
            payload = _write_guarded_json_report(payload, report_path, vault_root=vault_root)
        else:
            payload = {**payload, "report_written": False, "report_path": None}
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0

    print(f"VentureOps live client proof readiness: {payload['readiness_status']}")
    print(f"  ready_for_scope_proof_gate: {payload['ready_for_live_client_scope_proof_gate']}")
    print(f"  ready_for_live_client_workflow: {payload['ready_for_live_client_workflow']}")
    if payload.get("blockers"):
        print("  blockers:")
        for blocker in payload["blockers"]:
            print(f"    - {blocker}")
    print("  boundary: readiness only; no live client workflow, external send, CRM/payment mutation, or revenue claim.")
    return 0


def cmd_ventureops_mission_activation_readiness(args: argparse.Namespace) -> int:
    """chaseos ventureops mission-activation-readiness [--mission-workspace PATH] [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = build_mission_activation_readiness(
            vault_root,
            mission_workspace=getattr(args, "mission_workspace", None),
        )
        if getattr(args, "write_report", False):
            report_path = getattr(args, "report_path", None)
            if not report_path:
                report_path = _next_available_default_report_path(
                    vault_root,
                    f"{_default_proof_date()}_ventureops-mission-activation-readiness-report.json",
                )
            payload = _write_guarded_json_report(payload, report_path, vault_root=vault_root)
        else:
            payload = {**payload, "report_written": False, "report_path": None}
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0

    print(f"VentureOps mission activation readiness: {payload['readiness_status']}")
    print(f"  ready_for_activation: {payload['ready_for_activation']}")
    print(f"  ready_for_aor_dispatch: {payload['ready_for_aor_dispatch']}")
    print(f"  mission_workspace: {payload['mission_workspace_path']}")
    if payload.get("blockers"):
        print("  blockers:")
        for blocker in payload["blockers"]:
            print(f"    - {blocker}")
    print("  boundary: readiness only; no mission activation, AOR dispatch, Agent Bus task, provider/browser action, external send, CRM/payment mutation, or workflow evolution apply.")
    return 0


def cmd_ventureops_mission_activation_approval_packet(args: argparse.Namespace) -> int:
    """chaseos ventureops mission-activation-approval-packet [--mission-workspace PATH] [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = build_mission_activation_approval_packet(
            vault_root,
            mission_workspace=getattr(args, "mission_workspace", None),
        )
        if getattr(args, "write_packet", False):
            packet_path = getattr(args, "output", None) or payload["recommended_packet_path"]
            payload = _write_guarded_json_packet(payload, packet_path, vault_root=vault_root)
        else:
            payload = {**payload, "packet_written": False, "packet_path": None}
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0

    packet = payload.get("packet") or {}
    print(f"VentureOps mission activation approval packet: {payload['packet_status']}")
    print(f"  ready_for_operator_review: {payload['ready_for_operator_review']}")
    print(f"  ready_for_activation: {payload['ready_for_activation']}")
    print(f"  ready_for_aor_dispatch: {payload['ready_for_aor_dispatch']}")
    print(f"  recommended_packet_path: {payload['recommended_packet_path']}")
    if packet.get("readiness_blockers"):
        print("  blockers:")
        for blocker in packet["readiness_blockers"]:
            print(f"    - {blocker}")
    print("  boundary: draft packet and design only; no approval consumption, mission activation, AOR dispatch, Agent Bus task, provider/browser action, external send, CRM/payment mutation, or workflow evolution apply.")
    return 0


def cmd_ventureops_mission_activation_approval_consume(args: argparse.Namespace) -> int:
    """chaseos ventureops mission-activation-approval-consume [--mission-workspace PATH] [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = consume_mission_activation_approval(
            vault_root,
            mission_workspace=getattr(args, "mission_workspace", None),
            approval_path=getattr(args, "approval_path", None),
            marker_path=getattr(args, "marker_path", None),
            approval_id=getattr(args, "approval_id", None),
            approved_by=getattr(args, "approved_by", "operator"),
            operator_approval_statement=getattr(args, "operator_approval_statement", None),
            write_approval=bool(getattr(args, "write_approval", False)),
            consume=bool(getattr(args, "consume", False)),
        )
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0

    print(f"VentureOps mission activation approval consumption: {payload['status']}")
    print(f"  approval_id: {payload.get('approval_id')}")
    print(f"  approval_artifact_written: {payload['approval_artifact_written']}")
    print(f"  approval_consumed: {payload['approval_consumed']}")
    print(f"  exact_once_marker_written: {payload['exact_once_marker_written']}")
    print(f"  mission_activation_performed: {payload['authority_boundary']['mission_activation_performed']}")
    if payload.get("blockers"):
        print("  blockers:")
        for blocker in payload["blockers"]:
            print(f"    - {blocker}")
    print("  boundary: approval gate consumption only; no mission activation, AOR dispatch, Agent Bus task, provider/browser action, external send, CRM/payment mutation, or workflow evolution apply.")
    return 0


def cmd_ventureops_mission_manifest_promotion_review_gate(args: argparse.Namespace) -> int:
    """chaseos ventureops mission-manifest-promotion-review-gate [--mission-workspace PATH] [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = consume_mission_manifest_promotion_review_gate(
            vault_root,
            mission_workspace=getattr(args, "mission_workspace", None),
            review_path=getattr(args, "review_path", None),
            marker_path=getattr(args, "marker_path", None),
            review_id=getattr(args, "review_id", None),
            approved_by=getattr(args, "approved_by", "operator"),
            operator_approval_statement=getattr(args, "operator_approval_statement", None),
            write_review=bool(getattr(args, "write_review", False)),
            consume=bool(getattr(args, "consume", False)),
        )
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0

    print(f"VentureOps mission manifest promotion review gate: {payload['status']}")
    print(f"  review_id: {payload.get('review_id')}")
    print(f"  review_artifact_written: {payload['review_artifact_written']}")
    print(f"  review_consumed: {payload['review_consumed']}")
    print(f"  exact_once_marker_written: {payload['exact_once_marker_written']}")
    print(f"  mission_activation_performed: {payload['authority_boundary']['mission_activation_performed']}")
    if payload.get("blockers"):
        print("  blockers:")
        for blocker in payload["blockers"]:
            print(f"    - {blocker}")
    print("  boundary: review gate only; no manifest file mutation, mission activation, AOR dispatch, Agent Bus task, provider/browser action, external send, CRM/payment mutation, or workflow evolution apply.")
    return 0


def cmd_ventureops_mission_agent_bus_enqueue_gate(args: argparse.Namespace) -> int:
    """chaseos ventureops mission-agent-bus-enqueue-gate [--mission-workspace PATH] [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = consume_mission_agent_bus_enqueue_gate(
            vault_root,
            mission_workspace=getattr(args, "mission_workspace", None),
            approval_path=getattr(args, "approval_path", None),
            marker_path=getattr(args, "marker_path", None),
            enqueue_id=getattr(args, "approval_id", None),
            approved_by=getattr(args, "approved_by", "operator"),
            operator_approval_statement=getattr(args, "operator_approval_statement", None),
            recipient=getattr(args, "recipient", "Codex"),
            priority=getattr(args, "priority", "normal"),
            write_approval=bool(getattr(args, "write_approval", False)),
            consume=bool(getattr(args, "consume", False)),
            enqueue_task=bool(getattr(args, "enqueue_task", False)),
        )
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0 if payload.get("ok") else 1

    print(f"VentureOps mission Agent Bus enqueue gate: {payload['status']}")
    print(f"  enqueue_id: {payload.get('enqueue_id')}")
    print(f"  recipient: {payload.get('recipient')}")
    print(f"  agent_bus_task_id: {payload.get('agent_bus_task_id')}")
    print(f"  approval_artifact_written: {payload['approval_artifact_written']}")
    print(f"  enqueue_consumed: {payload['enqueue_consumed']}")
    print(f"  exact_once_marker_written: {payload['exact_once_marker_written']}")
    print(f"  agent_bus_task_written: {payload['agent_bus_task_written']}")
    print(f"  runtime_task_claimed: {payload['runtime_task_claimed']}")
    print(f"  workflow_dispatched: {payload['workflow_dispatched']}")
    if payload.get("blockers"):
        print("  blockers:")
        for blocker in payload["blockers"]:
            print(f"    - {blocker}")
    print("  boundary: exact-once local Agent Bus task write only; no task claim, runtime process start, AOR dispatch, mission activation, provider/browser action, external send, CRM/payment mutation, live trading, credential read, or canonical promotion.")
    return 0 if payload.get("ok") else 1


def cmd_ventureops_mission_runtime_claim_result_gate(args: argparse.Namespace) -> int:
    """chaseos ventureops mission-runtime-claim-result-gate [--mission-workspace PATH] [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = consume_mission_runtime_claim_result_gate(
            vault_root,
            mission_workspace=getattr(args, "mission_workspace", None),
            approval_path=getattr(args, "approval_path", None),
            marker_path=getattr(args, "marker_path", None),
            result_path=getattr(args, "result_path", None),
            approval_id=getattr(args, "approval_id", None),
            approved_by=getattr(args, "approved_by", "operator"),
            operator_approval_statement=getattr(args, "operator_approval_statement", None),
            runtime=getattr(args, "runtime", "Codex"),
            runtime_instance_id=getattr(args, "runtime_instance_id", "Axiom-Codex"),
            stale_after_seconds=int(getattr(args, "stale_after_seconds", 86400) or 86400),
            write_approval=bool(getattr(args, "write_approval", False)),
            consume=bool(getattr(args, "consume", False)),
            claim_task_flag=bool(getattr(args, "claim_task", False)),
            dispatch_aor=bool(getattr(args, "dispatch_aor", False)),
            ingest_result=bool(getattr(args, "ingest_result", False)),
            close_task=bool(getattr(args, "close_task", False)),
        )
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0 if payload.get("ok") else 1

    print(f"VentureOps mission runtime claim/result gate: {payload['status']}")
    print(f"  approval_id: {payload.get('approval_id')}")
    print(f"  agent_bus_task_id: {payload.get('agent_bus_task_id')}")
    print(f"  runtime: {payload.get('runtime')}")
    print(f"  approval_artifact_written: {payload['approval_artifact_written']}")
    print(f"  claim_result_consumed: {payload['claim_result_consumed']}")
    print(f"  runtime_task_claimed: {payload['runtime_task_claimed']}")
    print(f"  aor_dispatch_performed: {payload['aor_dispatch_performed']}")
    print(f"  mission_result_ingested: {payload['mission_result_ingested']}")
    print(f"  agent_bus_task_closed: {payload['agent_bus_task_closed']}")
    if payload.get("blockers"):
        print("  blockers:")
        for blocker in payload["blockers"]:
            print(f"    - {blocker}")
    print("  boundary: local task claim, AOR dry-review dispatch, result ingestion, and task close only; no mission activation, provider/browser action, external send, CRM/payment mutation, live trading, credential read, workflow evolution apply, protected edit, or canonical promotion.")
    return 0 if payload.get("ok") else 1


def cmd_ventureops_mission_activation_gate(args: argparse.Namespace) -> int:
    """chaseos ventureops mission-activation-gate [--mission-workspace PATH] [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = consume_mission_activation_gate(
            vault_root,
            mission_workspace=getattr(args, "mission_workspace", None),
            approval_path=getattr(args, "approval_path", None),
            marker_path=getattr(args, "marker_path", None),
            activation_id=getattr(args, "approval_id", None),
            approved_by=getattr(args, "approved_by", "operator"),
            operator_approval_statement=getattr(args, "operator_approval_statement", None),
            write_approval=bool(getattr(args, "write_approval", False)),
            consume=bool(getattr(args, "consume", False)),
            activate=bool(getattr(args, "activate", False)),
        )
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0 if payload.get("ok") else 1

    print(f"VentureOps mission activation gate: {payload['status']}")
    print(f"  activation_id: {payload.get('activation_id')}")
    print(f"  approval_artifact_written: {payload['approval_artifact_written']}")
    print(f"  activation_consumed: {payload['activation_consumed']}")
    print(f"  exact_once_marker_written: {payload['exact_once_marker_written']}")
    print(f"  mission_activation_performed: {payload['mission_activation_performed']}")
    if payload.get("blockers"):
        print("  blockers:")
        for blocker in payload["blockers"]:
            print(f"    - {blocker}")
    print("  boundary: local mission activation only; no external delivery, provider/browser action, credential read, workflow evolution apply, protected edit, CRM/payment mutation, live trading, or canonical promotion.")
    return 0 if payload.get("ok") else 1


def cmd_ventureops_mission_external_client_evidence_gate(args: argparse.Namespace) -> int:
    """chaseos ventureops mission-external-client-evidence-gate [--mission-workspace PATH] [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = build_mission_external_client_evidence_gate(
            vault_root,
            mission_workspace=getattr(args, "mission_workspace", None),
            external_action_type=getattr(args, "external_action_type", None),
            operator_approval_statement=getattr(args, "operator_approval_statement", None),
            scope_packet_path=getattr(args, "scope_packet", None),
            revenue_packet_path=getattr(args, "revenue_packet", None),
            live_client_proof_path=getattr(args, "live_client_proof_path", None),
            delivery_proof_path=getattr(args, "delivery_proof_path", None),
        )
        if getattr(args, "write_report", False):
            report_path = getattr(args, "report_path", None)
            if not report_path:
                report_path = _next_available_default_report_path(
                    vault_root,
                    f"{_default_proof_date()}_ventureops-mission-external-client-evidence-gate-report.json",
                )
            payload = _write_guarded_json_report(payload, report_path, vault_root=vault_root)
        else:
            payload = {**payload, "report_written": False, "report_path": None}
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0 if payload.get("ok") else 1

    print(f"VentureOps mission external/client evidence gate: {payload['status']}")
    print(f"  mission_active_local: {payload['mission_active_local']}")
    print(f"  external_action_type: {payload.get('external_action_type')}")
    print(f"  ready_for_guarded_live_client_workflow_proof: {payload['ready_for_guarded_live_client_workflow_proof']}")
    print(f"  ready_for_operator_attested_delivery_review: {payload['ready_for_operator_attested_delivery_review']}")
    print(f"  ready_for_proof_only_live_revenue_gate: {payload['ready_for_proof_only_live_revenue_gate']}")
    if payload.get("blockers"):
        print("  blockers:")
        for blocker in payload["blockers"]:
            print(f"    - {blocker}")
    print(
        "  boundary: readiness only; no external send, provider/browser action, CRM/payment mutation, "
        "credential read, protected edit, workflow evolution apply, live trading, or canonical promotion."
    )
    return 0 if payload.get("ok") else 1


def cmd_ventureops_live_client_scope_proof(args: argparse.Namespace) -> int:
    """chaseos ventureops live-client-scope-proof --scope-packet PATH --execute-proof [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = run_live_client_scope_proof(
            vault_root,
            scope_packet_path=str(getattr(args, "scope_packet")),
            run_id=str(getattr(args, "run_id") or "live-client-scope-proof"),
            run_date=str(getattr(args, "date") or _default_proof_date()),
            execute_proof=bool(getattr(args, "execute_proof", False)),
        )
    except Exception as exc:
        payload = {
            "ok": False,
            "error": str(exc),
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
        }

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0 if payload.get("ok") else 1

    if payload.get("ok"):
        print("VentureOps live client scope proof gate: written")
        print(f"  proof_gate_path: {payload.get('proof_gate_path')}")
    else:
        print(f"VentureOps live client scope proof gate blocked: {payload.get('error')}", file=sys.stderr)
    print("  boundary: local proof-gate only; no live client data ingestion, external send, CRM/payment mutation, or revenue claim.")
    return 0 if payload.get("ok") else 1


def cmd_ventureops_live_client_workflow_proof(args: argparse.Namespace) -> int:
    """chaseos ventureops live-client-workflow-proof --scope-packet PATH --execute-proof [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = run_live_client_workflow_proof(
            vault_root,
            scope_packet_path=str(getattr(args, "scope_packet")),
            run_id=str(getattr(args, "run_id") or "live-client-workflow-proof"),
            run_date=str(getattr(args, "date") or _default_proof_date()),
            execute_proof=bool(getattr(args, "execute_proof", False)),
        )
    except Exception as exc:
        payload = {
            "ok": False,
            "error": str(exc),
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
        }

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0 if payload.get("ok") else 1

    if payload.get("ok"):
        print("VentureOps live client workflow proof: written")
        print(f"  workflow_proof_path: {payload.get('workflow_proof_path')}")
    else:
        print(f"VentureOps live client workflow proof blocked: {payload.get('error')}", file=sys.stderr)
    print("  boundary: scoped local proof only; no external send, CRM/payment mutation, provider/browser action, or revenue claim.")
    return 0 if payload.get("ok") else 1


def cmd_ventureops_live_revenue_proof_readiness(args: argparse.Namespace) -> int:
    """chaseos ventureops live-revenue-proof-readiness [--revenue-packet PATH] [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = build_live_revenue_proof_readiness(
            vault_root,
            revenue_packet_path=getattr(args, "revenue_packet", None),
            live_client_proof_path=getattr(args, "live_client_proof_path", None),
        )
        if getattr(args, "write_report", False):
            report_path = getattr(args, "report_path", None)
            if not report_path:
                report_path = _next_available_default_report_path(
                    vault_root,
                    f"{_default_proof_date()}_ventureops-live-revenue-proof-readiness-report.json",
                )
            payload = _write_guarded_json_report(payload, report_path, vault_root=vault_root)
        else:
            payload = {**payload, "report_written": False, "report_path": None}
    except Exception as exc:
        if getattr(args, "output_json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0

    print(f"VentureOps live revenue proof readiness: {payload['readiness_status']}")
    print(f"  ready_for_live_revenue_proof: {payload['ready_for_live_revenue_proof']}")
    if payload.get("blockers"):
        print("  blockers:")
        for blocker in payload["blockers"]:
            print(f"    - {blocker}")
    print("  boundary: readiness only; no payment/CRM mutation, invoice send, or revenue claim.")
    return 0


def cmd_ventureops_live_revenue_proof(args: argparse.Namespace) -> int:
    """chaseos ventureops live-revenue-proof --revenue-packet PATH --live-client-proof-path PATH --execute-proof [--json]."""
    try:
        vault_root = Path(getattr(args, "vault_root", None) or ".").resolve()
        payload = run_live_revenue_proof(
            vault_root,
            revenue_packet_path=str(getattr(args, "revenue_packet")),
            live_client_proof_path=str(getattr(args, "live_client_proof_path")),
            run_date=str(getattr(args, "date") or _default_proof_date()),
            execute_proof=bool(getattr(args, "execute_proof", False)),
        )
    except Exception as exc:
        payload = {
            "ok": False,
            "error": str(exc),
            "live_revenue_proof_written": False,
            "proof_path": None,
            "payment_mutation_performed": False,
            "crm_mutation_performed": False,
            "invoice_sent": False,
            "external_send_performed": False,
            "revenue_claim_made": False,
        }

    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
        return 0 if payload.get("ok") else 1

    if payload.get("ok"):
        print("VentureOps live revenue proof artifact: written")
        print(f"  proof_path: {payload.get('proof_path')}")
    else:
        print(f"VentureOps live revenue proof blocked: {payload.get('error')}", file=sys.stderr)
    print("  boundary: proof-only local artifact; no payment/CRM mutation, invoice send, external send, or revenue claim.")
    return 0 if payload.get("ok") else 1
