"""Tenant/workspace/user scope helpers for SiteOps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.mcp.yaml_compat import safe_load

from runtime.siteops.errors import SiteOpsNotFoundError, SiteOpsValidationError
from runtime.siteops.models import SiteOpsScope

DEFAULT_LOCAL_SCOPE = {
    "tenant_id": "local",
    "workspace_id": "default",
    "user_id": "local-user",
}

CATALOG_FILES = {
    "site_skill_templates": "site_skill_templates.yaml",
    "workflow_templates": "workflow_templates.yaml",
    "provider_templates": "provider_templates.yaml",
    "policy_packs": "policy_packs.yaml",
}


def vault_root(root: Path | str | None = None) -> Path:
    return Path(root).resolve() if root else Path(__file__).resolve().parents[2]


def siteops_root(root: Path | str | None = None) -> Path:
    return vault_root(root) / "runtime" / "siteops"


def assert_scope(scope: dict[str, Any]) -> dict[str, str]:
    required = ("tenant_id", "workspace_id", "user_id")
    missing = [field for field in required if not str(scope.get(field) or "").strip()]
    if missing:
        raise SiteOpsValidationError(f"SiteOps scope missing required field(s): {', '.join(missing)}")
    return {field: str(scope[field]).strip() for field in required}


def require_scope(*, tenant_id: str | None, workspace_id: str | None, user_id: str | None) -> SiteOpsScope:
    scope = assert_scope({"tenant_id": tenant_id, "workspace_id": workspace_id, "user_id": user_id})
    return SiteOpsScope(**scope)


def normalize_scope(*, tenant_id: str | None, workspace_id: str | None, user_id: str | None) -> dict[str, str]:
    return require_scope(tenant_id=tenant_id, workspace_id=workspace_id, user_id=user_id).as_dict()


def _load_yaml(path: Path) -> Any:
    if not path.exists():
        raise SiteOpsNotFoundError(f"SiteOps YAML file not found: {path}")
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return safe_load(text) or []


def _write_yaml(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_catalog(root: Path | str | None = None) -> dict[str, list[dict[str, Any]]]:
    base = siteops_root(root) / "catalog"
    catalog: dict[str, list[dict[str, Any]]] = {}
    for key, filename in CATALOG_FILES.items():
        value = _load_yaml(base / filename)
        if isinstance(value, dict):
            value = value.get(key, [])
        if not isinstance(value, list):
            raise SiteOpsValidationError(f"catalog/{filename} must contain a list")
        catalog[key] = value
    return catalog


def load_tenant(root: Path | str | None = None, tenant_id: str = "local") -> dict[str, Any]:
    path = siteops_root(root) / "tenants" / f"{tenant_id}.yaml"
    payload = _load_yaml(path)
    if not isinstance(payload, dict):
        raise SiteOpsValidationError(f"tenant file must contain a mapping: {path}")
    tenant_meta = payload.get("tenant", payload)
    if tenant_meta.get("tenant_id") != tenant_id:
        raise SiteOpsValidationError(f"tenant_id mismatch in {path}")
    return payload


def save_tenant(root: Path | str | None = None, tenant_id: str = "local", payload: dict[str, Any] | None = None) -> Path:
    if payload is None:
        raise SiteOpsValidationError("tenant payload is required")
    path = siteops_root(root) / "tenants" / f"{tenant_id}.yaml"
    tenant_meta = payload.get("tenant", payload)
    if tenant_meta.get("tenant_id") != tenant_id:
        raise SiteOpsValidationError(f"tenant_id mismatch for save target: {tenant_id}")
    _write_yaml(path, payload)
    return path


def list_tenants(root: Path | str | None = None) -> list[dict[str, Any]]:
    base = siteops_root(root) / "tenants"
    if not base.exists():
        return []
    tenants: list[dict[str, Any]] = []
    for path in sorted(base.glob("*.yaml")):
        payload = _load_yaml(path)
        if not isinstance(payload, dict):
            continue
        meta = payload.get("tenant", payload)
        item = dict(meta)
        item["tenant_ref"] = str(path)
        tenants.append(item)
    return tenants


def load_local_tenant(vault_root: Path | str | None = None) -> dict[str, Any]:
    tenant = load_tenant(vault_root, "local")
    meta = tenant.get("tenant", tenant)
    return {
        **meta,
        "tenant_id": meta.get("tenant_id"),
        "default_workspace_id": meta.get("default_workspace_id"),
        "default_user_id": meta.get("default_user_id"),
        "mode": meta.get("mode"),
    }


def objects_by_id(items: list[dict[str, Any]], id_field: str) -> dict[str, dict[str, Any]]:
    return {str(item[id_field]): item for item in items if isinstance(item, dict) and item.get(id_field)}


def user_roles(tenant: dict[str, Any], user_id: str) -> list[str]:
    roles = []
    raw_roles = tenant.get("roles", [])
    if isinstance(raw_roles, dict):
        return list(raw_roles.get(user_id, []))
    for item in raw_roles:
        if item.get("user_id") == user_id:
            roles.extend(item.get("roles", []))
    return roles


def has_any_role(tenant: dict[str, Any], user_id: str, allowed_roles: list[str]) -> bool:
    return bool(set(user_roles(tenant, user_id)) & set(allowed_roles))
