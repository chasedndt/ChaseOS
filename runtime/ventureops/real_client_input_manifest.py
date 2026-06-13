"""Read-only operator manifest for VentureOps real-client scope inputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.ventureops.validation import (
    validate_real_client_scope_approval_artifact,
    validate_scope_evidence_source_paths,
)


def _clean(value: str | None) -> str:
    return str(value or "").strip()


def _relative_to_root(path_value: str | Path, root: Path) -> str:
    raw = Path(path_value)
    resolved = raw.resolve() if raw.is_absolute() else (root / raw).resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{path_value} escapes vault root") from exc
    return str(relative).replace("\\", "/")


def _safe_relative(value: str | Path | None, root: Path, errors: list[str], field_name: str) -> str:
    if not value:
        return ""
    try:
        return _relative_to_root(value, root)
    except ValueError as exc:
        display_value = str(value).replace("\\", "/")
        errors.append(f"{field_name} escapes vault root: {display_value}")
        return ""


def _load_json_object(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _quote_command_value(value: str) -> str:
    return f'"{value}"' if any(char.isspace() for char in value) else value


def _scope_approval_command(
    *,
    client_label: str,
    client_approved_scope_id: str,
    approval_id: str,
    approved_read_paths: list[str],
    approval_output_path: str,
) -> str:
    parts = [
        "chaseos ventureops scope-approval-packet",
        "--approval-id",
        _quote_command_value(approval_id or "ID"),
        "--client-label",
        _quote_command_value(client_label or "LABEL"),
        "--scope-id",
        _quote_command_value(client_approved_scope_id or "ID"),
    ]
    for path in approved_read_paths or ["PATH"]:
        parts.extend(["--approved-read-path", _quote_command_value(path)])
    parts.extend([
        "--output",
        _quote_command_value(approval_output_path or "PATH"),
        "--operator-approved",
        "--operator-attested-scope-approved",
        "--json",
    ])
    return " ".join(parts)


def _scope_evidence_command(
    *,
    client_label: str,
    client_approved_scope_id: str,
    approval_id: str,
    approval_artifact_path: str,
    approved_read_paths: list[str],
    scope_packet_output_path: str,
) -> str:
    parts = [
        "chaseos ventureops scope-evidence-packet",
        "--client-label",
        _quote_command_value(client_label or "LABEL"),
        "--scope-id",
        _quote_command_value(client_approved_scope_id or "ID"),
        "--approval-id",
        _quote_command_value(approval_id or "ID"),
        "--approval-artifact-path",
        _quote_command_value(approval_artifact_path or "PATH"),
    ]
    for path in approved_read_paths or ["PATH"]:
        parts.extend(["--approved-read-path", _quote_command_value(path)])
    parts.extend([
        "--output",
        _quote_command_value(scope_packet_output_path or "PATH"),
        "--operator-approved",
        "--json",
    ])
    return " ".join(parts)


def _manifest_scope_packet_output_command(
    *,
    client_label: str,
    client_approved_scope_id: str,
    approval_id: str,
    approval_artifact_path: str,
    approved_read_paths: list[str],
) -> str:
    parts = [
        "chaseos ventureops real-client-input-manifest",
        "--client-label",
        _quote_command_value(client_label or "LABEL"),
        "--scope-id",
        _quote_command_value(client_approved_scope_id or "ID"),
        "--approval-id",
        _quote_command_value(approval_id or "ID"),
        "--approval-artifact-path",
        _quote_command_value(approval_artifact_path or "PATH"),
    ]
    for path in approved_read_paths or ["PATH"]:
        parts.extend(["--approved-read-path", _quote_command_value(path)])
    parts.extend(["--scope-packet-output", "PATH", "--json"])
    return " ".join(parts)


def build_real_client_input_manifest(
    vault_root: str | Path,
    *,
    client_label: str | None = None,
    client_approved_scope_id: str | None = None,
    approval_id: str | None = None,
    approved_read_paths: list[str] | None = None,
    approval_output_path: str | None = None,
    approval_artifact_path: str | None = None,
    scope_packet_output_path: str | None = None,
) -> dict[str, Any]:
    """Inspect the operator inputs needed for the first real-client proof pass.

    This manifest is read-only. It does not write approval artifacts, scope
    packets, run workflows, ingest client data, send externally, mutate
    CRM/payment systems, call providers/browsers, or make revenue claims.
    """

    root = Path(vault_root).resolve()
    errors: list[str] = []
    normalized_sources = [
        relative
        for path in approved_read_paths or []
        if str(path or "").strip()
        for relative in [_safe_relative(path, root, errors, "approved_read_paths")]
        if relative
    ]
    approval_output_relative = _safe_relative(approval_output_path, root, errors, "approval_output_path")
    approval_artifact_relative = _safe_relative(approval_artifact_path, root, errors, "approval_artifact_path")
    scope_packet_output_relative = _safe_relative(scope_packet_output_path, root, errors, "scope_packet_output_path")

    label = _clean(client_label)
    scope_id = _clean(client_approved_scope_id)
    approval = _clean(approval_id)

    source_validation = validate_scope_evidence_source_paths(root, normalized_sources) if normalized_sources else {
        "ok": False,
        "errors": ["approved_read_paths required"],
        "existing_source_count": 0,
        "existing_sources": [],
    }

    missing_inputs: list[str] = []
    if not label:
        missing_inputs.append("client_label")
    if not scope_id:
        missing_inputs.append("client_approved_scope_id")
    if not approval:
        missing_inputs.append("approval_id")
    if not normalized_sources:
        missing_inputs.append("approved_read_paths")
    if not approval_output_relative and not approval_artifact_relative:
        missing_inputs.append("approval_output_path or approval_artifact_path")

    approval_validation: dict[str, Any] = {
        "ok": False,
        "errors": ["approval artifact not supplied"],
        "safe_read_paths": [],
    }
    approval_artifact_present = False
    approval_matches_inputs = False
    if approval_artifact_relative:
        approval_path = root / approval_artifact_relative
        approval_artifact_present = approval_path.exists() and approval_path.is_file()
        if not approval_artifact_present:
            approval_validation = {
                "ok": False,
                "errors": [f"approval artifact missing: {approval_artifact_relative}"],
                "safe_read_paths": [],
            }
        else:
            approval_data = _load_json_object(approval_path)
            if approval_data is None:
                approval_validation = {
                    "ok": False,
                    "errors": [f"approval artifact must be a JSON object: {approval_artifact_relative}"],
                    "safe_read_paths": [],
                }
            else:
                approval_validation = validate_real_client_scope_approval_artifact(approval_data)
                approved_from_artifact = sorted(str(path) for path in approval_validation.get("safe_read_paths") or [])
                approved_from_inputs = sorted(normalized_sources)
                approval_matches_inputs = bool(
                    approval_validation.get("ok")
                    and str(approval_validation.get("approval_id")) == approval
                    and str(approval_validation.get("client_label")) == label
                    and str(approval_validation.get("client_approved_scope_id")) == scope_id
                    and approved_from_artifact == approved_from_inputs
                )
                if approval_validation.get("ok") and not approval_matches_inputs:
                    approval_validation = {
                        **approval_validation,
                        "ok": False,
                        "errors": list(approval_validation.get("errors") or [])
                        + ["approval artifact fields do not match supplied manifest inputs"],
                    }
    if approval_matches_inputs and not scope_packet_output_relative:
        missing_inputs.append("scope_packet_output_path")

    if approval_artifact_relative and not approval_validation.get("ok"):
        errors.extend(str(error) for error in approval_validation.get("errors") or [])
    if normalized_sources and not source_validation.get("ok"):
        errors.extend(str(error) for error in source_validation.get("errors") or [])

    core_inputs_present = bool(label and scope_id and approval and normalized_sources)
    source_paths_valid = bool(source_validation.get("ok"))
    ready_to_author_scope_approval = bool(
        core_inputs_present and source_paths_valid and (approval_output_relative or approval_matches_inputs)
    )
    ready_to_author_scope_packet = bool(
        core_inputs_present
        and source_paths_valid
        and approval_artifact_relative
        and approval_matches_inputs
        and scope_packet_output_relative
    )

    if ready_to_author_scope_packet:
        manifest_status = "ready_to_author_scope_packet"
        next_required_action = "write real-client scope evidence packet from typed approval artifact"
        next_command = _scope_evidence_command(
            client_label=label,
            client_approved_scope_id=scope_id,
            approval_id=approval,
            approval_artifact_path=approval_artifact_relative,
            approved_read_paths=normalized_sources,
            scope_packet_output_path=scope_packet_output_relative,
        )
    elif approval_matches_inputs and not scope_packet_output_relative:
        manifest_status = "blocked_missing_real_client_inputs"
        next_required_action = "provide scope packet output path"
        next_command = _manifest_scope_packet_output_command(
            client_label=label,
            client_approved_scope_id=scope_id,
            approval_id=approval,
            approval_artifact_path=approval_artifact_relative,
            approved_read_paths=normalized_sources,
        )
    elif ready_to_author_scope_approval:
        manifest_status = "ready_to_author_scope_approval"
        next_required_action = "write typed real-client scope approval artifact"
        next_command = _scope_approval_command(
            client_label=label,
            client_approved_scope_id=scope_id,
            approval_id=approval,
            approved_read_paths=normalized_sources,
            approval_output_path=approval_output_relative,
        )
    else:
        manifest_status = "blocked_missing_real_client_inputs"
        next_required_action = "provide real client label, scope id, approval id, approved source files, and approval output path"
        next_command = _scope_approval_command(
            client_label=label,
            client_approved_scope_id=scope_id,
            approval_id=approval,
            approved_read_paths=normalized_sources,
            approval_output_path=approval_output_relative,
        )

    return {
        "ok": True,
        "manifest_status": manifest_status,
        "vault_root": str(root),
        "provided_inputs": {
            "client_label": bool(label),
            "client_approved_scope_id": bool(scope_id),
            "approval_id": bool(approval),
            "approved_read_paths": bool(normalized_sources),
            "approval_output_path": bool(approval_output_relative),
            "approval_artifact_path": bool(approval_artifact_relative),
            "scope_packet_output_path": bool(scope_packet_output_relative),
        },
        "missing_inputs": missing_inputs,
        "client_label": label,
        "client_approved_scope_id": scope_id,
        "approval_id": approval,
        "approved_read_paths": normalized_sources,
        "approval_output_path": approval_output_relative or None,
        "approval_artifact_path": approval_artifact_relative or None,
        "approval_artifact_present": approval_artifact_present,
        "scope_packet_output_path": scope_packet_output_relative or None,
        "source_paths_valid": source_paths_valid,
        "source_validation": source_validation,
        "scope_approval_artifact_valid": bool(approval_matches_inputs),
        "scope_approval_validation": approval_validation,
        "ready_to_author_scope_approval": ready_to_author_scope_approval,
        "ready_to_author_scope_packet": ready_to_author_scope_packet,
        "ready_for_live_client_workflow_proof": False,
        "next_required_action": next_required_action,
        "next_command": next_command,
        "errors": errors,
        "report_written": False,
        "report_path": None,
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
            "real-client input manifest only; no approval artifact write, no scope packet write, "
            "no live workflow execution, no external send, no CRM/payment mutation, no provider/browser "
            "action, no invoice send, and no revenue/accounting claim"
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


def write_real_client_input_manifest_report(
    payload: dict[str, Any],
    report_path: str | Path,
    *,
    vault_root: str | Path = ".",
) -> dict[str, Any]:
    root = Path(vault_root).resolve()
    target, relative, error = _resolve_report_target(report_path, root)
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
        "report_path": str(report_path),
        "report_write_blocked": False,
        "errors": list(payload.get("errors") or []),
    }
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
