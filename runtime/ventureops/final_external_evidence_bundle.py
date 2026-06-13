"""Final external evidence bundle validation for VentureOps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.ventureops.validation import (
    discover_external_completion_artifacts,
    validate_client_safe_delivery_artifact,
    validate_live_client_workflow_proof_artifact,
    validate_live_delivery_proof_artifact,
    validate_live_revenue_evidence,
    validate_live_revenue_proof_artifact,
    validate_real_client_scope_evidence,
    validate_scope_evidence_approval_artifact,
    validate_scope_evidence_source_paths,
)


REQUIRED_BUNDLE_FIELDS = {
    "type",
    "scope_packet_path",
    "live_client_workflow_proof_path",
    "delivery_proof_path",
    "revenue_packet_path",
    "live_revenue_proof_path",
}


def _load_json_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not contain a JSON object")
    return data


def _relative_to_root(path_value: str, root: Path) -> str:
    raw = str(path_value or "").strip()
    if not raw:
        raise ValueError("path is empty")
    path = Path(raw)
    resolved = path.resolve() if path.is_absolute() else (root / path).resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{raw} escapes vault root") from exc
    return str(relative).replace("\\", "/")


def _load_optional_json(root: Path, relative_path: str, blockers: list[str], label: str) -> dict[str, Any] | None:
    target = root / relative_path
    if not target.is_file():
        blockers.append(f"{label} missing: {relative_path}")
        return None
    try:
        return _load_json_object(target)
    except Exception as exc:
        blockers.append(f"{label} unreadable: {relative_path}: {exc}")
        return None


def _append_errors(blockers: list[str], prefix: str, validation: dict[str, Any]) -> None:
    for error in validation.get("errors") or []:
        blockers.append(f"{prefix}: {error}")


def validate_final_external_evidence_bundle(
    vault_root: str | Path,
    *,
    bundle_path: str,
) -> dict[str, Any]:
    """Validate a single operator-supplied final external proof bundle.

    The bundle is a no-execution closeout validator. It checks that the final
    live-client and proof-only revenue artifacts, plus their prerequisite
    operator packets, are present and internally consistent before the operator
    reruns the completion audit.
    """
    root = Path(vault_root).resolve()
    blockers: list[str] = []
    warnings: list[str] = []
    bundle_relative = None
    bundle: dict[str, Any] | None = None
    field_paths: dict[str, str | None] = {field: None for field in REQUIRED_BUNDLE_FIELDS if field != "type"}

    try:
        bundle_relative = _relative_to_root(bundle_path, root)
    except ValueError as exc:
        blockers.append(str(exc))

    if bundle_relative:
        bundle_target = root / bundle_relative
        if not bundle_target.is_file():
            blockers.append("final evidence bundle missing")
        else:
            try:
                bundle = _load_json_object(bundle_target)
            except Exception as exc:
                blockers.append(f"final evidence bundle unreadable: {exc}")

    if bundle is not None:
        missing = sorted(field for field in REQUIRED_BUNDLE_FIELDS if field not in bundle)
        blockers.extend([f"missing required bundle field: {field}" for field in missing])
        if bundle.get("type") != "ventureops-final-external-evidence-bundle":
            blockers.append("bundle type must be ventureops-final-external-evidence-bundle")
        for field in field_paths:
            if field in bundle:
                try:
                    field_paths[field] = _relative_to_root(str(bundle.get(field)), root)
                except ValueError as exc:
                    blockers.append(f"{field}: {exc}")

    scope_validation: dict[str, Any] = {"ok": False, "errors": ["scope packet missing"]}
    approval_validation: dict[str, Any] = {"ok": False, "errors": ["scope packet missing"]}
    source_validation: dict[str, Any] = {"ok": False, "errors": ["scope packet missing"]}
    live_client_validation: dict[str, Any] = {"ok": False, "errors": ["live-client workflow proof missing"]}
    delivery_validation: dict[str, Any] = {"ok": False, "errors": ["delivery proof missing"]}
    client_safe_delivery_validation: dict[str, Any] = {
        "ok": False,
        "errors": ["client-safe delivery artifact missing"],
    }
    revenue_validation: dict[str, Any] = {"ok": False, "errors": ["revenue packet missing"]}
    live_revenue_validation: dict[str, Any] = {"ok": False, "errors": ["live revenue proof missing"]}

    scope_packet = None
    live_client_proof = None
    delivery_proof = None
    revenue_packet = None
    live_revenue_proof = None

    if field_paths["scope_packet_path"]:
        scope_packet = _load_optional_json(root, field_paths["scope_packet_path"] or "", blockers, "scope packet")
    if scope_packet is not None:
        scope_validation = validate_real_client_scope_evidence(scope_packet)
        if not scope_validation["ok"]:
            _append_errors(blockers, "scope packet invalid", scope_validation)
        else:
            approval_validation = validate_scope_evidence_approval_artifact(root, scope_packet)
            source_validation = validate_scope_evidence_source_paths(root, scope_validation["safe_read_paths"])
            if not approval_validation["ok"]:
                _append_errors(blockers, "scope approval artifact invalid", approval_validation)
            if not source_validation["ok"]:
                _append_errors(blockers, "scope source path invalid", source_validation)

    if field_paths["live_client_workflow_proof_path"]:
        live_client_proof = _load_optional_json(
            root,
            field_paths["live_client_workflow_proof_path"] or "",
            blockers,
            "live-client workflow proof",
        )
    if live_client_proof is not None:
        live_client_validation = validate_live_client_workflow_proof_artifact(live_client_proof)
        if not live_client_validation["ok"]:
            _append_errors(blockers, "live-client workflow proof invalid", live_client_validation)

    if field_paths["delivery_proof_path"]:
        delivery_proof = _load_optional_json(root, field_paths["delivery_proof_path"] or "", blockers, "delivery proof")
    if delivery_proof is not None:
        delivery_validation = validate_live_delivery_proof_artifact(delivery_proof)
        if not delivery_validation["ok"]:
            _append_errors(blockers, "delivery proof invalid", delivery_validation)
        else:
            client_safe_delivery_path = str(
                delivery_proof.get("client_safe_delivery_artifact_path") or ""
            ).replace("\\", "/").strip().lstrip("/")
            client_safe_delivery = _load_optional_json(
                root,
                client_safe_delivery_path,
                blockers,
                "client-safe delivery artifact",
            )
            if client_safe_delivery is not None:
                client_safe_delivery_validation = validate_client_safe_delivery_artifact(client_safe_delivery)
                if not client_safe_delivery_validation["ok"]:
                    _append_errors(
                        blockers,
                        "client-safe delivery artifact invalid",
                        client_safe_delivery_validation,
                    )

    if field_paths["revenue_packet_path"]:
        revenue_packet = _load_optional_json(root, field_paths["revenue_packet_path"] or "", blockers, "revenue packet")
    if revenue_packet is not None:
        revenue_validation = validate_live_revenue_evidence(revenue_packet)
        if not revenue_validation["ok"]:
            _append_errors(blockers, "revenue packet invalid", revenue_validation)

    if field_paths["live_revenue_proof_path"]:
        live_revenue_proof = _load_optional_json(
            root,
            field_paths["live_revenue_proof_path"] or "",
            blockers,
            "live revenue proof",
        )
    if live_revenue_proof is not None:
        live_revenue_validation = validate_live_revenue_proof_artifact(live_revenue_proof)
        if not live_revenue_validation["ok"]:
            _append_errors(blockers, "live revenue proof invalid", live_revenue_validation)

    live_client_path = field_paths.get("live_client_workflow_proof_path")
    delivery_path = field_paths.get("delivery_proof_path")
    if scope_packet and live_client_proof:
        proof_scope_packet_path = str(live_client_proof.get("scope_packet_path") or "").replace("\\", "/").strip().lstrip("/")
        if field_paths.get("scope_packet_path") != proof_scope_packet_path:
            blockers.append("scope packet path does not match live-client workflow proof scope_packet_path")
        if str(scope_packet.get("client_approved_scope_id") or "") != str(live_client_proof.get("client_approved_scope_id") or ""):
            blockers.append("scope packet client_approved_scope_id does not match live-client workflow proof")
        if str(scope_packet.get("client_label") or "") != str(live_client_proof.get("client_label") or ""):
            blockers.append("scope packet client_label does not match live-client workflow proof")
        if str(scope_packet.get("approval_id") or "") != str(live_client_proof.get("approval_id") or ""):
            blockers.append("scope packet approval_id does not match live-client workflow proof")
    if delivery_proof and live_client_path:
        delivery_live_client_path = str(delivery_proof.get("live_client_proof_path") or "").replace("\\", "/").strip().lstrip("/")
        if delivery_live_client_path != live_client_path:
            blockers.append("delivery proof live_client_proof_path does not match bundle live-client workflow proof path")
    if delivery_proof and client_safe_delivery_validation.get("ok"):
        if client_safe_delivery_validation.get("workflow_id") != str(delivery_proof.get("workflow_id") or ""):
            blockers.append("client-safe delivery artifact workflow_id does not match delivery proof")
        if client_safe_delivery_validation.get("client_label") != str(delivery_proof.get("client_label") or ""):
            blockers.append("client-safe delivery artifact client_label does not match delivery proof")
        if client_safe_delivery_validation.get("delivery_reference_id") != str(delivery_proof.get("delivery_reference_id") or ""):
            blockers.append("client-safe delivery artifact delivery_reference_id does not match delivery proof")
        if live_client_path and client_safe_delivery_validation.get("source_live_client_proof_path") != live_client_path:
            blockers.append(
                "client-safe delivery artifact source_live_client_proof_path does not match bundle live-client workflow proof path"
            )
    if revenue_packet and delivery_path:
        revenue_delivery_path = str(revenue_packet.get("delivery_proof_path") or "").replace("\\", "/").strip().lstrip("/")
        if revenue_delivery_path != delivery_path:
            blockers.append("revenue packet delivery_proof_path does not match bundle delivery proof path")
    if live_revenue_proof and live_client_path:
        proof_live_client_path = str(live_revenue_proof.get("live_client_proof_path") or "").replace("\\", "/").strip().lstrip("/")
        if proof_live_client_path != live_client_path:
            blockers.append("live revenue proof live_client_proof_path does not match bundle live-client workflow proof path")
    if live_revenue_proof and revenue_packet:
        proof_revenue_packet_path = str(live_revenue_proof.get("revenue_packet_path") or "").replace("\\", "/").strip().lstrip("/")
        if field_paths.get("revenue_packet_path") != proof_revenue_packet_path:
            blockers.append("revenue packet path does not match live revenue proof revenue_packet_path")
        for field in ("revenue_proof_id", "client_label", "workflow_id", "payment_reference_id", "payment_status"):
            if str(live_revenue_proof.get(field) or "") != str(revenue_packet.get(field) or ""):
                blockers.append(f"live revenue proof {field} does not match revenue packet")

    external_completion = discover_external_completion_artifacts(root)
    valid_live_client_paths = set(external_completion.get("valid_live_client_workflow_proof_artifacts") or [])
    valid_revenue_paths = set(external_completion.get("valid_live_revenue_proof_artifacts") or [])
    if live_client_path and live_client_path not in valid_live_client_paths:
        blockers.append("bundle live-client workflow proof is not valid in completion discovery")
    if field_paths.get("live_revenue_proof_path") and field_paths["live_revenue_proof_path"] not in valid_revenue_paths:
        blockers.append("bundle live revenue proof is not valid in completion discovery")

    ready = bool(
        bundle is not None
        and not blockers
        and scope_validation.get("ok")
        and approval_validation.get("ok")
        and source_validation.get("ok")
        and live_client_validation.get("ok")
        and delivery_validation.get("ok")
        and client_safe_delivery_validation.get("ok")
        and revenue_validation.get("ok")
        and live_revenue_validation.get("ok")
    )
    return {
        "ok": True,
        "validation_status": "ready_for_completion_audit" if ready else "blocked",
        "ready_for_completion_audit": ready,
        "bundle_path": bundle_relative,
        "bundle_fields": field_paths,
        "scope_evidence_valid": bool(scope_validation.get("ok")),
        "scope_validation": scope_validation,
        "scope_approval_artifact_valid": bool(approval_validation.get("scope_approval_artifact_valid")),
        "scope_approval_validation": approval_validation,
        "scope_sources_valid": bool(source_validation.get("ok")),
        "scope_source_validation": source_validation,
        "live_client_workflow_proof_valid": bool(live_client_validation.get("ok")),
        "live_client_workflow_proof_validation": live_client_validation,
        "delivery_proof_artifact_valid": bool(delivery_validation.get("ok")),
        "delivery_proof_validation": delivery_validation,
        "client_safe_delivery_artifact_valid": bool(client_safe_delivery_validation.get("ok")),
        "client_safe_delivery_artifact_validation": client_safe_delivery_validation,
        "revenue_evidence_valid": bool(revenue_validation.get("ok")),
        "revenue_validation": revenue_validation,
        "live_revenue_proof_valid": bool(live_revenue_validation.get("ok")),
        "live_revenue_proof_validation": live_revenue_validation,
        "external_completion_artifacts": external_completion,
        "blockers": blockers,
        "warnings": warnings,
        "next_command": (
            "chaseos ventureops feature-family-completion-audit --write-report --report-path PATH --json"
            if ready
            else "chaseos ventureops final-external-execution-runbook --json"
        ),
        "live_client_scope_proof_performed": False,
        "live_client_workflow_proof_performed": False,
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
            "final external evidence bundle validation only; validates supplied proof-chain artifacts "
            "without running live workflows, sending externally, mutating CRM/payment systems, calling "
            "providers/browsers, sending invoices, or making accounting/revenue claims"
        ),
    }


def _resolve_report_target(path: str | Path, root: Path) -> tuple[Path | None, str | None, str | None]:
    raw = Path(path)
    resolved = raw.resolve() if raw.is_absolute() else (root / raw).resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError:
        return None, None, f"report_path escapes vault root: {path}"
    return resolved, str(relative).replace("\\", "/"), None


def write_final_external_evidence_bundle_report(
    payload: dict[str, Any],
    path: str | Path,
    *,
    vault_root: str | Path = ".",
) -> dict[str, Any]:
    root = Path(vault_root).resolve()
    target, relative, error = _resolve_report_target(path, root)
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
        "report_path": str(target),
        "report_write_blocked": False,
        "errors": list(payload.get("errors") or []),
    }
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
