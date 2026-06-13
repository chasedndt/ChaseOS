"""Fail-closed external/client evidence gate for VentureOps Mission Mode."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.ventureops.evidence_intake import build_evidence_intake
from runtime.ventureops.mission_activation_readiness import build_mission_activation_readiness
from runtime.ventureops.validation import validate_live_delivery_proof_artifact


SURFACE_ID = "ventureops_mission_external_client_evidence_gate"
ACTION_LIVE_CLIENT_WORKFLOW_PROOF = "live-client-workflow-proof"
ACTION_OPERATOR_ATTESTED_DELIVERY_PROOF = "operator-attested-delivery-proof"
ACTION_LIVE_REVENUE_PROOF = "live-revenue-proof"
ACTION_TYPES = (
    ACTION_LIVE_CLIENT_WORKFLOW_PROOF,
    ACTION_OPERATOR_ATTESTED_DELIVERY_PROOF,
    ACTION_LIVE_REVENUE_PROOF,
)


def _vault_relative(path: Path, vault_root: Path) -> str:
    try:
        return path.resolve().relative_to(vault_root.resolve()).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _normalize_optional_path(
    vault_root: Path,
    value: str | Path | None,
    *,
    field: str,
    require_file: bool = True,
) -> tuple[str | None, list[str]]:
    if value is None or str(value).strip() == "":
        return None, []
    raw = Path(value)
    resolved = raw.resolve() if raw.is_absolute() else (vault_root / raw).resolve()
    try:
        relative = resolved.relative_to(vault_root)
    except ValueError:
        return None, [f"{field}_escapes_vault_root:{value}"]
    relative_text = relative.as_posix()
    errors: list[str] = []
    if require_file:
        if not resolved.exists():
            errors.append(f"{field}_missing:{relative_text}")
        elif not resolved.is_file():
            errors.append(f"{field}_not_file:{relative_text}")
    return relative_text, errors


def _load_json_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not contain a JSON object")
    return data


def _authority_boundary() -> dict[str, Any]:
    return {
        "readiness_only": True,
        "mission_external_client_action_performed": False,
        "live_client_workflow_proof_performed": False,
        "live_external_delivery_performed": False,
        "external_send_performed": False,
        "provider_call_performed": False,
        "browser_action_performed": False,
        "browser_skill_activated": False,
        "crm_or_payment_mutation_performed": False,
        "payment_mutation_performed": False,
        "invoice_sent": False,
        "live_trading_performed": False,
        "workflow_evolution_applied": False,
        "protected_file_edit_performed": False,
        "credential_or_secret_read_performed": False,
        "canonical_promotion_performed": False,
        "revenue_claim_made": False,
    }


def _required_evidence() -> dict[str, list[str]]:
    return {
        ACTION_LIVE_CLIENT_WORKFLOW_PROOF: [
            "external_action_type=live-client-workflow-proof",
            "operator_approval_statement explicitly approving this guarded proof step",
            "typed ventureops-real-client-scope-approval artifact",
            "typed ventureops-real-client-scope-evidence packet",
            "existing approved_read_paths inside the vault root",
        ],
        ACTION_OPERATOR_ATTESTED_DELIVERY_PROOF: [
            "external_action_type=operator-attested-delivery-proof",
            "operator_approval_statement explicitly approving delivery-proof review",
            "typed ventureops-real-client-scope-evidence packet for the original approved scope",
            "typed live-client workflow proof artifact",
            "typed operator-attested delivery proof artifact",
            "client-safe delivery artifact referenced by the delivery proof",
        ],
        ACTION_LIVE_REVENUE_PROOF: [
            "external_action_type=live-revenue-proof",
            "operator_approval_statement explicitly approving proof-only revenue review",
            "typed ventureops-real-client-scope-evidence packet for the original approved scope",
            "typed live-client workflow proof artifact",
            "typed operator-attested delivery proof artifact",
            "typed live revenue evidence packet",
            "redacted receipt artifact referenced by the revenue packet",
        ],
    }


def _next_command(
    action_type: str | None,
    *,
    scope_packet_path: str | None,
    revenue_packet_path: str | None,
    live_client_proof_path: str | None,
) -> str:
    if action_type == ACTION_LIVE_CLIENT_WORKFLOW_PROOF and scope_packet_path:
        return (
            "chaseos ventureops live-client-workflow-proof "
            f"--scope-packet {scope_packet_path} --execute-proof --json"
        )
    if action_type == ACTION_LIVE_REVENUE_PROOF and revenue_packet_path and live_client_proof_path:
        return (
            "chaseos ventureops live-revenue-proof "
            f"--revenue-packet {revenue_packet_path} "
            f"--live-client-proof-path {live_client_proof_path} --execute-proof --json"
        )
    return (
        "chaseos ventureops mission-external-client-evidence-gate "
        "--external-action-type ACTION --operator-approval-statement TEXT --scope-packet PATH --json"
    )


def build_mission_external_client_evidence_gate(
    vault_root: str | Path,
    *,
    mission_workspace: str | Path | None = None,
    external_action_type: str | None = None,
    operator_approval_statement: str | None = None,
    scope_packet_path: str | Path | None = None,
    revenue_packet_path: str | Path | None = None,
    live_client_proof_path: str | Path | None = None,
    delivery_proof_path: str | Path | None = None,
) -> dict[str, Any]:
    """Evaluate Mission Mode external/client evidence without executing anything."""

    root = Path(vault_root).resolve()
    action_type = str(external_action_type or "").strip() or None
    blockers: list[str] = []
    warnings: list[str] = []
    if action_type is None:
        blockers.append("external_action_type_missing")
    elif action_type not in ACTION_TYPES:
        blockers.append(f"external_action_type_invalid:{action_type}")

    statement = " ".join(str(operator_approval_statement or "").strip().split())
    if not statement:
        blockers.append("operator_approval_statement_missing")

    mission_readiness = build_mission_activation_readiness(
        root,
        mission_workspace=mission_workspace,
    )
    mission_active = mission_readiness.get("readiness_status") == "mission_active_local"
    if not mission_active:
        blockers.append(f"mission_not_active_local:{mission_readiness.get('readiness_status')}")
    if mission_readiness.get("blockers"):
        blockers.append("mission_activation_readiness_has_blockers")

    path_resolution_errors: list[str] = []
    scope_rel, path_errors = _normalize_optional_path(root, scope_packet_path, field="scope_packet_path")
    blockers.extend(path_errors)
    path_resolution_errors.extend(path_errors)
    revenue_rel, path_errors = _normalize_optional_path(root, revenue_packet_path, field="revenue_packet_path")
    blockers.extend(path_errors)
    path_resolution_errors.extend(path_errors)
    live_client_rel, path_errors = _normalize_optional_path(root, live_client_proof_path, field="live_client_proof_path")
    blockers.extend(path_errors)
    path_resolution_errors.extend(path_errors)
    delivery_rel, path_errors = _normalize_optional_path(root, delivery_proof_path, field="delivery_proof_path")
    blockers.extend(path_errors)
    path_resolution_errors.extend(path_errors)

    if action_type == ACTION_LIVE_CLIENT_WORKFLOW_PROOF and scope_rel is None:
        blockers.append("real_client_scope_evidence_packet_missing")
    if action_type == ACTION_OPERATOR_ATTESTED_DELIVERY_PROOF:
        if live_client_rel is None:
            blockers.append("live_client_workflow_proof_artifact_missing")
        if delivery_rel is None:
            blockers.append("operator_attested_delivery_proof_artifact_missing")
    if action_type == ACTION_LIVE_REVENUE_PROOF:
        if revenue_rel is None:
            blockers.append("live_revenue_evidence_packet_missing")
        if live_client_rel is None:
            blockers.append("live_client_workflow_proof_artifact_missing")

    evidence_intake: dict[str, Any] = {
        "ok": True,
        "intake_status": "not_run",
        "blockers": [],
        "warnings": [],
    }
    if not path_resolution_errors:
        try:
            evidence_intake = build_evidence_intake(
                root,
                scope_packet_path=scope_rel,
                revenue_packet_path=revenue_rel,
                live_client_proof_path=live_client_rel,
            )
        except Exception as exc:
            blockers.append(f"evidence_intake_failed:{exc}")
    else:
        evidence_intake["blockers"] = [
            "evidence intake skipped until supplied evidence paths resolve to files"
        ]

    if evidence_intake.get("blockers"):
        blockers.extend(str(blocker) for blocker in evidence_intake.get("blockers") or [])
    warnings.extend(str(warning) for warning in evidence_intake.get("warnings") or [])

    delivery_proof_validation: dict[str, Any] = {
        "ok": False,
        "errors": ["delivery proof artifact not supplied"],
    }
    if delivery_rel:
        try:
            delivery_proof_validation = validate_live_delivery_proof_artifact(
                _load_json_object(root / delivery_rel)
            )
        except Exception as exc:
            delivery_proof_validation = {
                "ok": False,
                "errors": [f"delivery proof artifact unreadable: {exc}"],
            }
        if action_type == ACTION_OPERATOR_ATTESTED_DELIVERY_PROOF and not delivery_proof_validation.get("ok"):
            blockers.extend(str(error) for error in delivery_proof_validation.get("errors") or [])

    scope_ready = bool(
        evidence_intake.get("scope_evidence_valid")
        and evidence_intake.get("scope_approval_artifact_valid")
        and evidence_intake.get("scope_sources_valid")
    )
    revenue_ready = bool(evidence_intake.get("ready_for_live_revenue_proof"))
    delivery_ready = bool(
        action_type == ACTION_OPERATOR_ATTESTED_DELIVERY_PROOF
        and evidence_intake.get("live_client_proof_artifact_valid")
        and delivery_proof_validation.get("ok")
    )

    if action_type == ACTION_LIVE_CLIENT_WORKFLOW_PROOF and not scope_ready:
        blockers.append("real_client_scope_evidence_not_ready")
    if action_type == ACTION_LIVE_REVENUE_PROOF and not revenue_ready:
        blockers.append("live_revenue_evidence_not_ready")
    if action_type == ACTION_OPERATOR_ATTESTED_DELIVERY_PROOF and not delivery_ready:
        blockers.append("operator_attested_delivery_evidence_not_ready")

    deduped_blockers = list(dict.fromkeys(str(blocker) for blocker in blockers))
    ready_for_next_guarded_command = not deduped_blockers
    status = (
        "ready_for_guarded_live_client_workflow_proof"
        if ready_for_next_guarded_command and action_type == ACTION_LIVE_CLIENT_WORKFLOW_PROOF
        else "ready_for_operator_attested_delivery_review"
        if ready_for_next_guarded_command and action_type == ACTION_OPERATOR_ATTESTED_DELIVERY_PROOF
        else "ready_for_proof_only_live_revenue_gate"
        if ready_for_next_guarded_command and action_type == ACTION_LIVE_REVENUE_PROOF
        else "blocked_missing_external_client_evidence"
    )

    return {
        "ok": True,
        "schema_version": "0.1",
        "surface": SURFACE_ID,
        "status": status,
        "mission_id": mission_readiness.get("mission_id"),
        "mission_workspace_path": mission_readiness.get("mission_workspace_path"),
        "mission_active_local": mission_active,
        "mission_readiness_status": mission_readiness.get("readiness_status"),
        "external_action_type": action_type,
        "operator_approval_statement_present": bool(statement),
        "scope_packet_path": scope_rel,
        "revenue_packet_path": revenue_rel,
        "live_client_proof_path": live_client_rel,
        "delivery_proof_path": delivery_rel,
        "required_external_evidence": _required_evidence(),
        "evidence_intake_status": evidence_intake.get("intake_status"),
        "scope_evidence_valid": bool(evidence_intake.get("scope_evidence_valid")),
        "scope_approval_artifact_valid": bool(evidence_intake.get("scope_approval_artifact_valid")),
        "scope_sources_valid": bool(evidence_intake.get("scope_sources_valid")),
        "live_client_proof_artifact_valid": bool(evidence_intake.get("live_client_proof_artifact_valid")),
        "delivery_proof_artifact_valid": bool(delivery_proof_validation.get("ok")),
        "revenue_evidence_valid": bool(evidence_intake.get("revenue_evidence_valid")),
        "ready_for_guarded_live_client_workflow_proof": (
            ready_for_next_guarded_command and action_type == ACTION_LIVE_CLIENT_WORKFLOW_PROOF
        ),
        "ready_for_operator_attested_delivery_review": (
            ready_for_next_guarded_command and action_type == ACTION_OPERATOR_ATTESTED_DELIVERY_PROOF
        ),
        "ready_for_proof_only_live_revenue_gate": (
            ready_for_next_guarded_command and action_type == ACTION_LIVE_REVENUE_PROOF
        ),
        "ready_for_external_send": False,
        "ready_for_crm_or_payment_mutation": False,
        "ready_for_provider_or_browser_action": False,
        "ready_for_workflow_evolution_apply": False,
        "blockers": deduped_blockers,
        "warnings": list(dict.fromkeys(warnings)),
        "mission_readiness": {
            "readiness_status": mission_readiness.get("readiness_status"),
            "mission_active": mission_readiness.get("mission_active"),
            "blockers": list(mission_readiness.get("blockers") or []),
            "authority_boundary": mission_readiness.get("authority_boundary") or {},
        },
        "evidence_intake": evidence_intake,
        "delivery_proof_validation": delivery_proof_validation,
        "next_required_action": (
            "run the next guarded proof command only if the operator still approves this action"
            if ready_for_next_guarded_command
            else "supply explicit operator approval and typed external/client evidence artifacts"
        ),
        "next_command": _next_command(
            action_type,
            scope_packet_path=scope_rel,
            revenue_packet_path=revenue_rel,
            live_client_proof_path=live_client_rel,
        ),
        "safe_followup_plan": [
            "keep Mission Mode external/client action blocked until this gate reports a ready state",
            "use only typed evidence artifacts whose paths resolve inside the vault root",
            "run only the next guarded proof command; do not perform external sends, provider/browser actions, CRM/payment mutation, credential reads, protected edits, workflow evolution apply, live trading, or canonical promotion from this gate",
        ],
        "authority_boundary": _authority_boundary(),
        "report_written": False,
        "report_path": None,
    }
