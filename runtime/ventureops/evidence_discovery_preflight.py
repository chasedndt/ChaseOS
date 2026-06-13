"""Bounded evidence discovery preflight for VentureOps external closeout."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.ventureops.validation import (
    validate_live_client_scope_proof_artifact,
    validate_live_client_workflow_proof_artifact,
    validate_live_delivery_proof_artifact,
    validate_live_revenue_evidence,
    validate_real_client_scope_evidence,
    validate_scope_evidence_approval_artifact,
    validate_scope_evidence_source_paths,
)


DEFAULT_SCAN_ROOTS = (
    "runtime/ventureops/fixtures",
    "03_INPUTS",
    "07_LOGS/Workflow-Proofs",
    "07_LOGS/Revenue-Proofs",
)


def _load_json_object(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _relative_to_root(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _resolve_scan_root(root: Path, value: str | Path) -> Path:
    raw = Path(value)
    resolved = raw.resolve() if raw.is_absolute() else (root / raw).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"scan root escapes vault root: {value}") from exc
    return resolved


def _json_paths(scan_roots: list[Path]) -> list[Path]:
    paths: list[Path] = []
    for scan_root in scan_roots:
        if scan_root.is_file() and scan_root.suffix.lower() == ".json":
            paths.append(scan_root)
        elif scan_root.is_dir():
            paths.extend(path for path in scan_root.rglob("*.json") if path.is_file())
    return sorted(set(paths), key=lambda path: str(path).lower())


def _candidate(
    *,
    path: Path,
    root: Path,
    artifact_type: str,
    classification: str,
    validation: dict[str, Any],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "path": _relative_to_root(path, root),
        "type": artifact_type,
        "classification": classification,
        "valid": bool(validation.get("ok")),
        "errors": list(validation.get("errors") or []),
    }
    if extra:
        payload.update(extra)
    return payload


def _selected_scope_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    for candidate in candidates:
        if candidate.get("valid") and candidate.get("approval_artifact_valid") and candidate.get("source_paths_valid"):
            return candidate
    return None


def _selected_revenue_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    for candidate in candidates:
        if (
            candidate.get("valid")
            and candidate.get("receipt_artifact_present")
            and candidate.get("delivery_proof_artifact_present")
            and candidate.get("delivery_proof_artifact_valid")
        ):
            return candidate
    return None


def _selected_valid_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    for candidate in candidates:
        if candidate.get("valid"):
            return candidate
    return None


def _validate_internal_closeout_artifact(
    artifact: dict[str, Any],
    *,
    root: Path,
) -> dict[str, Any]:
    errors: list[str] = []
    if artifact.get("internal_workflow_proof_closed") is not True:
        errors.append("internal_workflow_proof_closed must be true")
    if artifact.get("live_revenue_deferred") is not True:
        errors.append("live_revenue_deferred must be true")
    if artifact.get("revenue_evidence_required_for_closeout") is not False:
        errors.append("revenue_evidence_required_for_closeout must be false")
    proof_path = str(artifact.get("live_client_workflow_proof_path") or "").strip()
    proof_validation: dict[str, Any] = {"ok": False, "errors": ["live client workflow proof path missing"]}
    if not proof_path:
        errors.append("live_client_workflow_proof_path is required")
    else:
        resolved = (root / proof_path).resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            errors.append("live_client_workflow_proof_path escapes vault root")
        if not errors:
            proof_artifact = _load_json_object(resolved)
            if not isinstance(proof_artifact, dict):
                errors.append("live_client_workflow_proof_path must reference a JSON object")
            else:
                proof_validation = validate_live_client_workflow_proof_artifact(proof_artifact)
                if not proof_validation.get("ok"):
                    errors.append("referenced live-client workflow proof is invalid")
    return {
        "ok": not errors,
        "errors": errors,
        "live_client_workflow_proof_path": proof_path,
        "live_client_workflow_proof_valid": bool(proof_validation.get("ok")),
    }


def build_evidence_discovery_preflight(
    vault_root: str | Path,
    *,
    scan_roots: list[str | Path] | None = None,
) -> dict[str, Any]:
    """Scan approved repo-local evidence roots and recommend the next guarded command.

    The preflight only reads bounded JSON artifacts. It does not execute client
    workflows, send externally, mutate CRM/payment systems, call providers, call
    browsers, send invoices, or make revenue/accounting claims.
    """

    root = Path(vault_root).resolve()
    requested_roots = scan_roots or list(DEFAULT_SCAN_ROOTS)
    resolved_roots = [_resolve_scan_root(root, value) for value in requested_roots]
    existing_roots = [path for path in resolved_roots if path.exists()]

    scope_candidates: list[dict[str, Any]] = []
    revenue_candidates: list[dict[str, Any]] = []
    live_client_workflow_candidates: list[dict[str, Any]] = []
    insufficient_live_client_artifacts: list[dict[str, Any]] = []
    internal_closeout_candidates: list[dict[str, Any]] = []
    template_only_candidates: list[dict[str, Any]] = []
    unknown_json_count = 0

    for path in _json_paths(existing_roots):
        artifact = _load_json_object(path)
        if artifact is None:
            continue
        artifact_type = str(artifact.get("type") or "")

        if artifact_type == "ventureops-real-client-scope-evidence":
            validation = validate_real_client_scope_evidence(artifact)
            approval_validation = {
                "ok": False,
                "errors": ["scope evidence invalid"],
                "scope_approval_artifact_valid": False,
            }
            source_validation = {
                "ok": False,
                "errors": ["scope evidence invalid"],
                "existing_source_count": 0,
                "existing_sources": [],
            }
            if validation.get("ok"):
                approval_validation = validate_scope_evidence_approval_artifact(root, artifact)
                source_validation = validate_scope_evidence_source_paths(root, validation.get("safe_read_paths") or [])
            candidate = _candidate(
                path=path,
                root=root,
                artifact_type=artifact_type,
                classification="real_client_scope_evidence",
                validation=validation,
                extra={
                    "approval_artifact_valid": bool(approval_validation.get("scope_approval_artifact_valid")),
                    "approval_artifact_errors": list(approval_validation.get("errors") or []),
                    "source_paths_valid": bool(source_validation.get("ok")),
                    "source_path_errors": list(source_validation.get("errors") or []),
                    "approved_read_path_count": validation.get("approved_read_path_count", 0),
                },
            )
            scope_candidates.append(candidate)
            if artifact.get("template_only") is True:
                template_only_candidates.append({**candidate, "classification": "template_only_scope_evidence"})
            continue

        if artifact_type == "ventureops-live-revenue-evidence":
            validation = validate_live_revenue_evidence(artifact)
            receipt_path = str(validation.get("receipt_artifact_path") or "")
            delivery_path = str(validation.get("delivery_proof_path") or "")
            delivery_present = bool(delivery_path) and (root / delivery_path).exists()
            delivery_validation = {"ok": False, "errors": ["delivery proof artifact missing"]}
            if delivery_present:
                delivery_data = _load_json_object(root / delivery_path)
                if isinstance(delivery_data, dict):
                    delivery_validation = validate_live_delivery_proof_artifact(delivery_data)
                else:
                    delivery_validation = {
                        "ok": False,
                        "errors": ["delivery proof artifact must be a JSON object"],
                    }
            candidate = _candidate(
                path=path,
                root=root,
                artifact_type=artifact_type,
                classification="live_revenue_evidence",
                validation=validation,
                extra={
                    "receipt_artifact_present": bool(receipt_path) and (root / receipt_path).exists(),
                    "delivery_proof_artifact_present": delivery_present,
                    "delivery_proof_artifact_valid": bool(delivery_validation.get("ok")),
                    "delivery_proof_errors": list(delivery_validation.get("errors") or []),
                    "amount": validation.get("amount", 0.0),
                    "currency": validation.get("currency", ""),
                },
            )
            revenue_candidates.append(candidate)
            if artifact.get("template_only") is True:
                template_only_candidates.append({**candidate, "classification": "template_only_revenue_evidence"})
            continue

        if artifact_type == "ventureops-live-client-workflow-proof":
            validation = validate_live_client_workflow_proof_artifact(artifact)
            live_client_workflow_candidates.append(
                _candidate(
                    path=path,
                    root=root,
                    artifact_type=artifact_type,
                    classification="live_client_workflow_proof",
                    validation=validation,
                    extra={
                        "client_approved_scope_id": validation.get("client_approved_scope_id", ""),
                        "approved_read_path_count": validation.get("approved_read_path_count", 0),
                    },
                )
            )
            continue

        if artifact_type == "ventureops-live-client-scope-proof-gate":
            validation = validate_live_client_scope_proof_artifact(artifact)
            insufficient_live_client_artifacts.append(
                _candidate(
                    path=path,
                    root=root,
                    artifact_type=artifact_type,
                    classification="scope_gate_only_insufficient_for_revenue",
                    validation=validation,
                    extra={
                        "reason": "valid scope-gate artifacts are not live-client workflow proof artifacts",
                    },
                )
            )
            continue

        if artifact_type == "ventureops-internal-workflow-proof-closeout":
            validation = _validate_internal_closeout_artifact(artifact, root=root)
            internal_closeout_candidates.append(
                _candidate(
                    path=path,
                    root=root,
                    artifact_type=artifact_type,
                    classification="internal_workflow_proof_closeout",
                    validation=validation,
                    extra={
                        "workflow_id": str(artifact.get("workflow_id") or ""),
                        "workflow_alias": str(artifact.get("workflow_alias") or ""),
                        "client_label": str(artifact.get("client_label") or ""),
                        "live_client_workflow_proof_path": validation.get("live_client_workflow_proof_path", ""),
                        "live_client_workflow_proof_valid": bool(validation.get("live_client_workflow_proof_valid")),
                        "live_revenue_deferred": artifact.get("live_revenue_deferred") is True,
                        "revenue_evidence_required_for_closeout": artifact.get("revenue_evidence_required_for_closeout") is True,
                    },
                )
            )
            continue

        unknown_json_count += 1

    selected_scope = _selected_scope_candidate(scope_candidates)
    selected_revenue = _selected_revenue_candidate(revenue_candidates)
    selected_live_client_workflow = _selected_valid_candidate(live_client_workflow_candidates)
    selected_internal_closeout = _selected_valid_candidate(internal_closeout_candidates)

    ready_for_live_client_workflow = selected_scope is not None
    ready_for_live_revenue = selected_revenue is not None and selected_live_client_workflow is not None

    if selected_internal_closeout is not None:
        discovery_status = "internal_workflow_proof_closed_revenue_deferred"
        next_required_action = "no revenue evidence required for internal closeout"
        next_command = "future real-world VentureOps use case: author fresh scope packet if revenue is in scope"
    elif ready_for_live_revenue:
        discovery_status = "ready_for_live_revenue_proof"
        next_required_action = "run live-revenue-proof with --execute-proof"
        next_command = (
            "chaseos ventureops live-revenue-proof "
            f"--revenue-packet {selected_revenue['path']} "
            f"--live-client-proof-path {selected_live_client_workflow['path']} "
            "--execute-proof --json"
        )
    elif selected_live_client_workflow is not None:
        discovery_status = "ready_for_revenue_evidence"
        next_required_action = "provide valid live revenue evidence with redacted receipt and delivery proof"
        next_command = "chaseos ventureops evidence-template --kind revenue --output PATH --json"
    elif ready_for_live_client_workflow:
        discovery_status = "ready_for_live_client_workflow_proof"
        next_required_action = "run live-client-workflow-proof with --execute-proof"
        next_command = (
            "chaseos ventureops live-client-workflow-proof "
            f"--scope-packet {selected_scope['path']} --execute-proof --json"
        )
    else:
        discovery_status = "blocked_no_real_evidence_found"
        next_required_action = "collect real-client scope inputs through real-client-input-manifest"
        next_command = (
            "chaseos ventureops real-client-input-manifest --client-label LABEL "
            "--scope-id ID --approval-id ID --approved-read-path PATH "
            "--approval-output PATH --scope-packet-output PATH --json"
        )

    blockers: list[str] = []
    if selected_scope is None and selected_live_client_workflow is None:
        blockers.append("valid real client scope evidence packet missing")
    if selected_live_client_workflow is None:
        blockers.append("valid live client workflow proof artifact missing")
    if selected_revenue is None and selected_internal_closeout is None:
        blockers.append("valid live revenue evidence packet with receipt and delivery proof missing")

    return {
        "ok": True,
        "discovery_status": discovery_status,
        "scan_roots": [_relative_to_root(path, root) for path in resolved_roots],
        "existing_scan_roots": [_relative_to_root(path, root) for path in existing_roots],
        "json_artifact_count": len(_json_paths(existing_roots)),
        "unknown_json_count": unknown_json_count,
        "scope_candidates": scope_candidates,
        "scope_candidate_count": len(scope_candidates),
        "revenue_candidates": revenue_candidates,
        "revenue_candidate_count": len(revenue_candidates),
        "live_client_workflow_candidates": live_client_workflow_candidates,
        "live_client_workflow_candidate_count": len(live_client_workflow_candidates),
        "insufficient_live_client_artifacts": insufficient_live_client_artifacts,
        "scope_gate_only_candidate_count": len(insufficient_live_client_artifacts),
        "internal_closeout_candidates": internal_closeout_candidates,
        "internal_closeout_candidate_count": len(internal_closeout_candidates),
        "template_only_candidates": template_only_candidates,
        "template_only_candidate_count": len(template_only_candidates),
        "selected_scope_packet_path": selected_scope["path"] if selected_scope else None,
        "selected_revenue_packet_path": selected_revenue["path"] if selected_revenue else None,
        "selected_live_client_workflow_proof_path": selected_live_client_workflow["path"] if selected_live_client_workflow else None,
        "selected_internal_closeout_path": selected_internal_closeout["path"] if selected_internal_closeout else None,
        "ready_for_live_client_workflow_proof": ready_for_live_client_workflow,
        "ready_for_live_revenue_proof": ready_for_live_revenue,
        "internal_workflow_proof_closed": selected_internal_closeout is not None,
        "live_revenue_deferred": selected_internal_closeout is not None,
        "revenue_evidence_required_for_closeout": False if selected_internal_closeout is not None else None,
        "next_required_action": next_required_action,
        "next_command": next_command,
        "blockers": blockers,
        "live_client_scope_proof_performed": False,
        "live_client_workflow_proof_performed": False,
        "live_revenue_proof_performed": False,
        "live_client_data_ingested": False,
        "live_external_delivery_performed": False,
        "external_send_performed": False,
        "payment_mutation_performed": False,
        "crm_mutation_performed": False,
        "invoice_sent": False,
        "provider_calls": 0,
        "browser_actions": 0,
        "revenue_claim_made": False,
        "boundary": (
            "bounded evidence discovery only; scans approved repo-local JSON evidence roots and recommends "
            "the next guarded command without executing live workflows, ingesting live client data, sending "
            "externally, mutating CRM/payment systems, calling providers/browsers, sending invoices, or "
            "making revenue/accounting claims"
        ),
    }


def write_evidence_discovery_preflight_report(payload: dict[str, Any], report_path: str | Path) -> dict[str, Any]:
    target = Path(report_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {**payload, "report_written": True, "report_path": str(target)}
    target.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return payload
