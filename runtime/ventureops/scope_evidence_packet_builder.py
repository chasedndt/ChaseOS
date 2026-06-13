"""Guarded real-client scope evidence packet builder for VentureOps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.ventureops.validation import (
    validate_real_client_scope_approval_artifact,
    validate_real_client_scope_evidence,
    validate_scope_evidence_source_paths,
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


def build_scope_evidence_packet(
    vault_root: str | Path,
    *,
    client_label: str,
    client_approved_scope_id: str,
    approval_id: str,
    approval_artifact_path: str,
    approved_read_paths: list[str],
    output_path: str,
    operator_approved: bool,
    redaction_policy: str = "client_safe_summary_only",
    delivery_boundary: str = "no_external_delivery",
) -> dict[str, Any]:
    """Write a scope evidence packet from explicit operator-supplied fields.

    This command helps author the packet required by the guarded live-client
    proof lane, but it does not prove the live-client workflow by itself.
    """

    root = Path(vault_root).resolve()
    errors: list[str] = []
    if not operator_approved:
        errors.append("operator approval flag required")
    if not approved_read_paths:
        errors.append("at least one approved read path is required")

    approval_artifact_relative = _add_relative_path(errors, "approval_artifact_path", approval_artifact_path, root)
    output_relative = _add_relative_path(errors, "output_path", output_path, root)
    output_available = False
    if output_relative is not None:
        output_available = not (root / output_relative).exists()
        if not output_available:
            errors.append(f"output path already exists: {output_relative}")
    safe_read_paths: list[str] = []
    for path in approved_read_paths:
        if (relative := _add_relative_path(errors, "approved_read_paths", path, root)) is not None:
            safe_read_paths.append(relative)

    if not _is_file(root, approval_artifact_relative):
        errors.append(f"approval artifact missing: {approval_artifact_relative}")

    approval_validation: dict[str, Any] = {
        "ok": False,
        "errors": ["scope approval artifact missing"],
        "safe_read_paths": [],
    }
    if _is_file(root, approval_artifact_relative):
        try:
            approval_validation = validate_real_client_scope_approval_artifact(
                _load_json_object(root / approval_artifact_relative)
            )
        except (json.JSONDecodeError, ValueError) as exc:
            approval_validation = {
                "ok": False,
                "errors": [f"scope approval artifact invalid JSON: {exc}"],
                "safe_read_paths": [],
            }
        if not approval_validation.get("ok"):
            errors.append("scope approval artifact invalid")
            errors.extend(approval_validation.get("errors") or [])
        else:
            if str(approval_validation.get("approval_id")) != approval_id:
                errors.append("scope approval artifact approval_id does not match packet approval_id")
            if str(approval_validation.get("client_approved_scope_id")) != client_approved_scope_id:
                errors.append("scope approval artifact scope id does not match packet scope id")
            if str(approval_validation.get("client_label")) != client_label:
                errors.append("scope approval artifact client label does not match packet client label")
            approved_from_artifact = sorted(str(path) for path in approval_validation.get("safe_read_paths") or [])
            approved_from_args = sorted(safe_read_paths)
            if approved_from_artifact != approved_from_args:
                errors.append("scope approval artifact approved read paths do not match packet read paths")

    source_validation = validate_scope_evidence_source_paths(root, safe_read_paths)
    if not source_validation.get("ok"):
        errors.extend(source_validation.get("errors") or [])

    packet = {
        "type": "ventureops-real-client-scope-evidence",
        "client_approved_scope_id": client_approved_scope_id,
        "client_label": client_label,
        "approval_id": approval_id,
        "approval_status": "approved" if operator_approved else "pending",
        "approval_artifact_path": approval_artifact_relative or "",
        "approved_read_paths": safe_read_paths,
        "redaction_policy": redaction_policy,
        "delivery_boundary": delivery_boundary,
        "builder_boundary": (
            "operator-supplied scope packet authoring only; validates approval/source artifact paths "
            "and writes a packet without running live workflows or external side effects"
        ),
    }
    packet_validation = validate_real_client_scope_evidence(packet)
    if not packet_validation.get("ok"):
        errors.extend(packet_validation.get("errors") or [])

    if errors:
        return {
            "ok": False,
            "packet_written": False,
            "packet_path": None,
            "packet": packet,
            "scope_evidence_valid": False,
            "scope_sources_valid": bool(source_validation.get("ok")),
            "scope_approval_artifact_valid": bool(approval_validation.get("ok")),
            "scope_approval_validation": approval_validation,
            "approval_artifact_present": _is_file(root, approval_artifact_relative),
            "output_path_available": output_available,
            "errors": errors,
            "next_required_action": "provide operator approval, approval artifact, and existing approved source files",
            "next_command": "chaseos ventureops scope-evidence-packet --operator-approved --output PATH --json",
            "live_client_workflow_proof_performed": False,
            "live_client_data_ingested": False,
            "live_external_delivery_performed": False,
            "external_send_performed": False,
            "payment_mutation_performed": False,
            "crm_mutation_performed": False,
            "provider_calls": 0,
            "browser_actions": 0,
            "revenue_claim_made": False,
            "boundary": "scope packet authoring only; no live workflow execution or external side effects",
        }

    assert output_relative is not None
    target = root / output_relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(packet, indent=2), encoding="utf-8")

    return {
        "ok": True,
        "packet_written": True,
        "packet_path": output_relative,
        "packet": packet,
        "scope_evidence_valid": True,
        "scope_sources_valid": True,
        "scope_approval_artifact_valid": True,
        "scope_approval_validation": approval_validation,
        "approval_artifact_present": True,
        "output_path_available": True,
        "errors": [],
        "next_required_action": "run live-client-workflow-proof with --execute-proof",
        "next_command": (
            f"chaseos ventureops live-client-workflow-proof --scope-packet {output_relative} "
            "--execute-proof --json"
        ),
        "live_client_workflow_proof_performed": False,
        "live_client_data_ingested": False,
        "live_external_delivery_performed": False,
        "external_send_performed": False,
        "payment_mutation_performed": False,
        "crm_mutation_performed": False,
        "provider_calls": 0,
        "browser_actions": 0,
        "revenue_claim_made": False,
        "boundary": "scope packet authoring only; no live workflow execution or external side effects",
    }
