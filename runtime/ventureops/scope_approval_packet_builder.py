"""Guarded real-client scope approval artifact builder for VentureOps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.ventureops.validation import (
    validate_real_client_scope_approval_artifact,
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


def build_scope_approval_packet(
    vault_root: str | Path,
    *,
    approval_id: str,
    client_label: str,
    client_approved_scope_id: str,
    approved_read_paths: list[str],
    output_path: str,
    operator_approved: bool,
    operator_attested_scope_approved: bool,
    redaction_policy: str = "client_safe_summary_only",
    delivery_boundary: str = "no_external_delivery",
) -> dict[str, Any]:
    """Write a typed operator approval artifact for real-client scope evidence."""

    root = Path(vault_root).resolve()
    errors: list[str] = []
    if not operator_approved:
        errors.append("operator approval flag required")
    if not operator_attested_scope_approved:
        errors.append("operator scope approval attestation required")
    if not approved_read_paths:
        errors.append("at least one approved read path is required")

    safe_read_paths = [
        relative
        for path in approved_read_paths
        if (relative := _add_relative_path(errors, "approved_read_paths", path, root)) is not None
    ]
    output_relative = _add_relative_path(errors, "output_path", output_path, root)
    output_available = False
    if output_relative is not None:
        output_available = not (root / output_relative).exists()
        if not output_available:
            errors.append(f"output path already exists: {output_relative}")
    source_validation = (
        validate_scope_evidence_source_paths(root, safe_read_paths)
        if safe_read_paths
        else {"ok": False, "errors": ["approved read paths did not resolve inside vault root"]}
    )
    if not source_validation.get("ok"):
        errors.extend(source_validation.get("errors") or [])

    artifact = {
        "type": "ventureops-real-client-scope-approval",
        "approval_id": approval_id,
        "client_label": client_label,
        "client_approved_scope_id": client_approved_scope_id,
        "approval_status": "approved" if operator_approved else "pending",
        "approval_decision": "approved" if operator_approved else "pending",
        "approved_read_paths": safe_read_paths,
        "redaction_policy": redaction_policy,
        "delivery_boundary": delivery_boundary,
        "operator_attested_scope_approved": operator_attested_scope_approved,
        "external_send_authorized": False,
        "payment_mutation_authorized": False,
        "crm_mutation_authorized": False,
        "provider_calls_authorized": False,
        "browser_actions_authorized": False,
        "revenue_claim_authorized": False,
        "builder_boundary": (
            "operator-supplied scope approval artifact authoring only; records approval for declared "
            "scope/source paths without running live workflows or granting external side effects"
        ),
    }
    artifact_validation = validate_real_client_scope_approval_artifact(artifact)
    if not artifact_validation.get("ok"):
        errors.extend(artifact_validation.get("errors") or [])

    if errors:
        return {
            "ok": False,
            "approval_artifact_written": False,
            "approval_artifact_path": None,
            "artifact": artifact,
            "scope_approval_artifact_valid": False,
            "scope_sources_valid": bool(source_validation.get("ok")),
            "output_path_available": output_available,
            "errors": errors,
            "next_required_action": "provide operator approval, attestation, and existing approved source files",
            "next_command": "chaseos ventureops scope-approval-packet --operator-approved --operator-attested-scope-approved --output PATH --json",
            "external_send_authorized": False,
            "payment_mutation_authorized": False,
            "crm_mutation_authorized": False,
            "provider_calls_authorized": False,
            "browser_actions_authorized": False,
            "revenue_claim_authorized": False,
            "boundary": "scope approval artifact authoring only; no live workflow execution or external side effects",
        }

    assert output_relative is not None
    target = root / output_relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(artifact, indent=2), encoding="utf-8")

    return {
        "ok": True,
        "approval_artifact_written": True,
        "approval_artifact_path": output_relative,
        "artifact": artifact,
        "scope_approval_artifact_valid": True,
        "scope_sources_valid": True,
        "output_path_available": True,
        "errors": [],
        "next_required_action": "build real-client scope evidence packet",
        "next_command": (
            "chaseos ventureops scope-evidence-packet "
            f"--approval-artifact-path {output_relative} --operator-approved --output PATH --json"
        ),
        "external_send_authorized": False,
        "payment_mutation_authorized": False,
        "crm_mutation_authorized": False,
        "provider_calls_authorized": False,
        "browser_actions_authorized": False,
        "revenue_claim_authorized": False,
        "boundary": "scope approval artifact authoring only; no live workflow execution or external side effects",
    }
