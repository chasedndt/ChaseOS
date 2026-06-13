"""Guarded final evidence bundle packet builder for VentureOps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _relative_to_root(path_value: str | Path, root: Path) -> str:
    raw = Path(path_value)
    resolved = raw.resolve() if raw.is_absolute() else (root / raw).resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{path_value} escapes vault root") from exc
    return str(relative).replace("\\", "/")


def _is_file(root: Path, relative_path: str) -> bool:
    return (root / relative_path).exists() and (root / relative_path).is_file()


def _add_relative_path(
    field_paths: dict[str, str | None],
    errors: list[str],
    field: str,
    path_value: str,
    root: Path,
) -> None:
    try:
        field_paths[field] = _relative_to_root(path_value, root)
    except ValueError:
        errors.append(f"{field} escapes vault root: {path_value}")


def build_final_evidence_bundle_packet(
    vault_root: str | Path,
    *,
    scope_packet_path: str,
    live_client_workflow_proof_path: str,
    delivery_proof_path: str,
    revenue_packet_path: str,
    live_revenue_proof_path: str,
    output_path: str,
) -> dict[str, Any]:
    """Write a final external evidence bundle from explicit proof paths.

    This builder only creates the bundle envelope consumed by
    `final-evidence-bundle`. It does not validate the full proof chain and does
    not run workflows or perform external side effects.
    """
    root = Path(vault_root).resolve()
    errors: list[str] = []
    field_paths: dict[str, str | None] = {
        "scope_packet_path": None,
        "live_client_workflow_proof_path": None,
        "delivery_proof_path": None,
        "revenue_packet_path": None,
        "live_revenue_proof_path": None,
    }
    _add_relative_path(field_paths, errors, "scope_packet_path", scope_packet_path, root)
    _add_relative_path(
        field_paths,
        errors,
        "live_client_workflow_proof_path",
        live_client_workflow_proof_path,
        root,
    )
    _add_relative_path(field_paths, errors, "delivery_proof_path", delivery_proof_path, root)
    _add_relative_path(field_paths, errors, "revenue_packet_path", revenue_packet_path, root)
    _add_relative_path(field_paths, errors, "live_revenue_proof_path", live_revenue_proof_path, root)

    output_relative: str | None = None
    output_available = False
    try:
        output_relative = _relative_to_root(output_path, root)
        output_available = not (root / output_relative).exists()
        if not output_available:
            errors.append(f"output path already exists: {output_relative}")
    except ValueError:
        errors.append(f"output_path escapes vault root: {output_path}")

    for field, relative_path in field_paths.items():
        if relative_path is not None and not _is_file(root, relative_path):
            errors.append(f"{field} missing: {relative_path}")

    packet = {
        "type": "ventureops-final-external-evidence-bundle",
        **{field: path for field, path in field_paths.items() if path is not None},
        "builder_boundary": (
            "final evidence bundle packet authoring only; writes a pointer bundle for validation "
            "without executing live workflows, creating proof evidence, sending externally, mutating "
            "CRM/payment systems, calling providers/browsers, sending invoices, or making revenue claims"
        ),
    }
    base_payload = {
        "packet": packet,
        "packet_path": None,
        "output_path_available": output_available,
        "errors": errors,
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
        "boundary": "final evidence bundle packet authoring only; no live workflow execution or external side effects",
    }
    if errors:
        return {
            **base_payload,
            "ok": False,
            "packet_written": False,
            "next_required_action": "provide existing final proof-chain artifact paths and an unused output path",
            "next_command": "chaseos ventureops final-evidence-bundle-packet --output PATH --json",
        }

    assert output_relative is not None
    target = root / output_relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(packet, indent=2), encoding="utf-8")

    return {
        **base_payload,
        "ok": True,
        "packet_written": True,
        "packet_path": output_relative,
        "next_required_action": "validate final evidence bundle before completion audit rerun",
        "next_command": f"chaseos ventureops final-evidence-bundle --bundle {output_relative} --json",
    }
