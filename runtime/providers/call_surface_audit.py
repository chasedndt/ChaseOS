"""Provider call-surface audit loader.

This module keeps the provider-status boundary machine-readable: runtime model
execution surfaces can be distinguished from connector, Source Intelligence,
delivery, lifecycle, and dry-run control-plane surfaces.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CALL_SURFACE_AUDIT_RELATIVE_PATH = Path("runtime/providers/provider_call_surfaces.json")

VALID_PROVIDER_STATE_POLICIES = {
    "emit_provider_state_ledger",
    "emit_provider_state_ledger_via_shared_adapter",
    "source_intelligence_telemetry",
    "connector_health_telemetry",
    "delivery_health_telemetry",
    "runtime_health_telemetry",
    "dry_run_control_plane_audit",
}

VALID_STATUSES = {
    "VERIFIED",
    "IMPLEMENTED",
    "PARTIAL",
    "PLANNED",
    "NOT BUILT",
    "DOCS-ONLY",
    "CONFIGURED BUT UNVERIFIED",
    "DEFERRED",
}

REQUIRED_SURFACE_FIELDS = {
    "id",
    "path",
    "related_paths",
    "layer",
    "call_kind",
    "providers",
    "credential_refs",
    "entry_points",
    "evidence_markers",
    "provider_state_policy",
    "provider_state_ledger_status",
    "telemetry_owner",
    "status",
    "notes",
}

LIST_FIELDS = {
    "related_paths",
    "providers",
    "credential_refs",
    "entry_points",
    "evidence_markers",
}

PROVIDER_STATE_LEDGER_POLICIES = {
    "emit_provider_state_ledger",
    "emit_provider_state_ledger_via_shared_adapter",
}


class ProviderCallSurfaceAuditError(RuntimeError):
    """Raised when the provider call-surface audit artifact is invalid."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def call_surface_audit_path(vault_root: str | Path | None = None) -> Path:
    root = Path(vault_root) if vault_root is not None else _repo_root()
    return root / CALL_SURFACE_AUDIT_RELATIVE_PATH


def load_provider_call_surface_audit(
    vault_root: str | Path | None = None,
    *,
    require_files: bool = True,
) -> dict[str, Any]:
    """Load and validate the provider call-surface audit artifact."""
    root = Path(vault_root) if vault_root is not None else _repo_root()
    path = call_surface_audit_path(root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProviderCallSurfaceAuditError(f"Provider call-surface audit missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ProviderCallSurfaceAuditError(f"Provider call-surface audit is invalid JSON: {exc}") from exc

    return validate_provider_call_surface_audit(data, vault_root=root, require_files=require_files)


def validate_provider_call_surface_audit(
    data: dict[str, Any],
    *,
    vault_root: str | Path | None = None,
    require_files: bool = True,
) -> dict[str, Any]:
    """Validate a provider call-surface audit mapping and return it unchanged."""
    if not isinstance(data, dict):
        raise ProviderCallSurfaceAuditError("Provider call-surface audit must be an object")
    if data.get("schema_version") != 1:
        raise ProviderCallSurfaceAuditError("Provider call-surface audit schema_version must be 1")
    surfaces = data.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        raise ProviderCallSurfaceAuditError("Provider call-surface audit requires a non-empty surfaces list")

    root = Path(vault_root) if vault_root is not None else _repo_root()
    seen_ids: set[str] = set()
    for index, surface in enumerate(surfaces):
        if not isinstance(surface, dict):
            raise ProviderCallSurfaceAuditError(f"surface[{index}] must be an object")
        _validate_surface(surface, index=index, seen_ids=seen_ids, vault_root=root, require_files=require_files)
    return data


def _validate_surface(
    surface: dict[str, Any],
    *,
    index: int,
    seen_ids: set[str],
    vault_root: Path,
    require_files: bool,
) -> None:
    missing = sorted(REQUIRED_SURFACE_FIELDS.difference(surface))
    if missing:
        raise ProviderCallSurfaceAuditError(f"surface[{index}] missing fields: {missing}")

    surface_id = _require_text(surface["id"], f"surface[{index}].id")
    if surface_id in seen_ids:
        raise ProviderCallSurfaceAuditError(f"duplicate provider call-surface id: {surface_id}")
    seen_ids.add(surface_id)

    rel_path = _require_text(surface["path"], f"{surface_id}.path")
    if rel_path.startswith("/") or ":" in Path(rel_path).parts[0]:
        raise ProviderCallSurfaceAuditError(f"{surface_id}.path must be repo-relative")
    if require_files and not (vault_root / rel_path).is_file():
        raise ProviderCallSurfaceAuditError(f"{surface_id}.path does not exist: {rel_path}")

    for field_name in LIST_FIELDS:
        if not isinstance(surface[field_name], list):
            raise ProviderCallSurfaceAuditError(f"{surface_id}.{field_name} must be a list")

    policy = _require_text(surface["provider_state_policy"], f"{surface_id}.provider_state_policy")
    if policy not in VALID_PROVIDER_STATE_POLICIES:
        raise ProviderCallSurfaceAuditError(
            f"{surface_id}.provider_state_policy {policy!r} is not one of {sorted(VALID_PROVIDER_STATE_POLICIES)}"
        )

    status = _require_text(surface["status"], f"{surface_id}.status")
    if status not in VALID_STATUSES:
        raise ProviderCallSurfaceAuditError(f"{surface_id}.status {status!r} is not valid")

    for text_field in ("layer", "call_kind", "provider_state_ledger_status", "telemetry_owner", "notes"):
        _require_text(surface[text_field], f"{surface_id}.{text_field}")


def _require_text(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ProviderCallSurfaceAuditError(f"{field_name} is required")
    return text


def provider_state_ledger_surfaces(audit: dict[str, Any]) -> list[dict[str, Any]]:
    """Return surfaces that directly or indirectly emit provider-state ledger events."""
    surfaces = audit.get("surfaces") or []
    return [
        surface
        for surface in surfaces
        if surface.get("provider_state_policy") in PROVIDER_STATE_LEDGER_POLICIES
    ]


def surfaces_by_policy(audit: dict[str, Any], policy: str) -> list[dict[str, Any]]:
    """Return surfaces with a given provider_state_policy."""
    surfaces = audit.get("surfaces") or []
    return [surface for surface in surfaces if surface.get("provider_state_policy") == policy]
