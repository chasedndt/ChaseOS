"""Validation helpers for the SiteOps production scaffold."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.siteops.errors import SiteOpsSecretError, SiteOpsValidationError
from runtime.siteops.tenancy import load_catalog, load_tenant, objects_by_id


SECRET_KEY_PATTERNS = (
    "api_key",
    "password",
    "token",
    "cookie",
    "session_key",
    "private_key",
    "seed_phrase",
)

SECRET_KEY_ALLOWLIST = {
    "credential_ref_id",
    "credential_ref_ids",
    "credential_type",
    "secret_store_ref",
    "secret_store_refs",
    "browser_profile_ref_id",
    "browser_profile_binding",
    "provider_account_binding",
    "provider_account_binding_id",
    "required_env_vars",
}


def scan_secret_like_keys(value: Any, *, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            text = str(key)
            lower = text.lower()
            if lower not in SECRET_KEY_ALLOWLIST and any(pattern in lower for pattern in SECRET_KEY_PATTERNS):
                errors.append(f"{path}.{text}: raw secret-like field is forbidden in SiteOps config")
            errors.extend(scan_secret_like_keys(item, path=f"{path}.{text}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(scan_secret_like_keys(item, path=f"{path}[{index}]"))
    return errors


def _require_fields(obj: dict[str, Any], fields: tuple[str, ...], label: str, errors: list[str]) -> None:
    for field in fields:
        if field not in obj or obj[field] in (None, ""):
            errors.append(f"{label}: missing required field '{field}'")


def _validate_scope(obj: dict[str, Any], label: str, errors: list[str], *, require_workspace: bool = False, require_user: bool = False) -> None:
    _require_fields(obj, ("tenant_id",), label, errors)
    if require_workspace:
        _require_fields(obj, ("workspace_id",), label, errors)
    if require_user:
        _require_fields(obj, ("user_id",), label, errors)


def validate_catalog(root: Path | str | None = None) -> list[str]:
    catalog = load_catalog(root)
    errors: list[str] = []

    for item in catalog["site_skill_templates"]:
        _require_fields(
            item,
            (
                "skill_template_id",
                "display_name",
                "category",
                "workflow_template_ids",
                "required_approvals",
                "version",
                "status",
            ),
            f"site_skill_template:{item.get('skill_template_id', '<unknown>')}",
            errors,
        )
        if item.get("owner_type") != "system" or item.get("visibility") != "public_catalog":
            errors.append(f"site_skill_template:{item.get('skill_template_id')}: must be system-owned public_catalog")

    for item in catalog["workflow_templates"]:
        _require_fields(
            item,
            (
                "workflow_template_id",
                "workflow_type",
                "default_mode",
                "inputs_schema",
                "steps",
                "approval_required",
                "blocked_actions",
                "output_schema",
                "audit_required",
                "version",
                "status",
            ),
            f"workflow_template:{item.get('workflow_template_id', '<unknown>')}",
            errors,
        )

    for item in catalog["provider_templates"]:
        _require_fields(
            item,
            (
                "provider_adapter_id",
                "display_name",
                "provider_type",
                "capabilities",
                "cost_mode",
                "estimated_cost_per_run",
                "supports_dry_run",
                "supports_stub",
                "requires_paid_credits",
                "version",
                "status",
            ),
            f"provider_template:{item.get('provider_adapter_id', '<unknown>')}",
            errors,
        )

    for item in catalog["policy_packs"]:
        _require_fields(
            item,
            ("policy_pack_id", "version", "status", "blocked_actions", "approval_required_actions"),
            f"policy_pack:{item.get('policy_pack_id', '<unknown>')}",
            errors,
        )

    errors.extend(scan_secret_like_keys(catalog))
    return errors


def validate_tenant(root: Path | str | None = None, tenant_id: str = "local") -> list[str]:
    tenant = load_tenant(root, tenant_id)
    catalog = load_catalog(root)
    errors: list[str] = []

    errors.extend(scan_secret_like_keys(tenant))

    tenant_meta = tenant.get("tenant", {})
    _require_fields(tenant_meta, ("tenant_id", "display_name", "default_workspace_id", "default_user_id", "mode", "status"), "tenant", errors)

    skill_templates = set(objects_by_id(catalog["site_skill_templates"], "skill_template_id"))
    workflow_templates = set(objects_by_id(catalog["workflow_templates"], "workflow_template_id"))
    provider_templates = set(objects_by_id(catalog["provider_templates"], "provider_adapter_id"))

    credentials = objects_by_id(tenant.get("credential_refs", []), "credential_ref_id")
    browser_profiles = objects_by_id(tenant.get("browser_profile_refs", []), "browser_profile_ref_id")
    budget_policies = objects_by_id(tenant.get("budget_policies", []), "budget_policy_id")
    provider_bindings = objects_by_id(tenant.get("provider_account_bindings", []), "provider_account_binding_id")

    for role in tenant.get("roles", []):
        _validate_scope(role, f"role:{role.get('user_id', '<unknown>')}", errors, require_user=True)

    for item in tenant.get("site_skill_installations", []):
        label = f"site_skill_installation:{item.get('installation_id', '<unknown>')}"
        _validate_scope(item, label, errors)
        _require_fields(item, ("installation_id", "skill_template_id", "enabled", "allowed_workspaces", "allowed_roles", "created_by", "status"), label, errors)
        if item.get("skill_template_id") not in skill_templates:
            errors.append(f"{label}: unknown skill_template_id '{item.get('skill_template_id')}'")

    for item in tenant.get("workflow_installations", []):
        label = f"workflow_installation:{item.get('workflow_installation_id', '<unknown>')}"
        _validate_scope(item, label, errors)
        _require_fields(item, ("workflow_installation_id", "workflow_template_id", "enabled", "allowed_users", "allowed_roles", "status"), label, errors)
        if item.get("workflow_template_id") not in workflow_templates:
            errors.append(f"{label}: unknown workflow_template_id '{item.get('workflow_template_id')}'")
        if item.get("provider_account_binding") and item["provider_account_binding"] not in provider_bindings:
            errors.append(f"{label}: unknown provider_account_binding '{item['provider_account_binding']}'")
        if item.get("browser_profile_binding") and item["browser_profile_binding"] not in browser_profiles:
            errors.append(f"{label}: unknown browser_profile_binding '{item['browser_profile_binding']}'")

    for item in tenant.get("credential_refs", []):
        label = f"credential_ref:{item.get('credential_ref_id', '<unknown>')}"
        _validate_scope(item, label, errors)
        _require_fields(item, ("credential_ref_id", "provider_id", "credential_type", "secret_store_ref", "status"), label, errors)
        if item.get("provider_id") not in provider_templates and item.get("provider_id") not in {"canva", "tradingview"}:
            errors.append(f"{label}: unknown provider_id '{item.get('provider_id')}'")

    for item in tenant.get("browser_profile_refs", []):
        label = f"browser_profile_ref:{item.get('browser_profile_ref_id', '<unknown>')}"
        _validate_scope(item, label, errors, require_user=True)
        _require_fields(item, ("browser_profile_ref_id", "provider", "allowed_domains", "status", "created_at"), label, errors)

    for item in tenant.get("provider_account_bindings", []):
        label = f"provider_account_binding:{item.get('provider_account_binding_id', '<unknown>')}"
        _validate_scope(item, label, errors)
        _require_fields(item, ("provider_account_binding_id", "provider_id", "credential_ref_id", "budget_policy_id", "allowed_capabilities", "status"), label, errors)
        if item.get("credential_ref_id") not in credentials:
            errors.append(f"{label}: unknown credential_ref_id '{item.get('credential_ref_id')}'")
        if item.get("budget_policy_id") not in budget_policies:
            errors.append(f"{label}: unknown budget_policy_id '{item.get('budget_policy_id')}'")

    for item in tenant.get("budget_policies", []):
        label = f"budget_policy:{item.get('budget_policy_id', '<unknown>')}"
        _validate_scope(item, label, errors)
        _require_fields(item, ("budget_policy_id", "max_cost_per_run", "max_cost_per_day", "max_cost_per_month", "require_approval_above", "dry_run_required", "status"), label, errors)

    return errors


def validate_production_siteops(root: Path | str | None = None, tenant_id: str = "local") -> dict[str, Any]:
    errors = validate_catalog(root)
    errors.extend(validate_tenant(root, tenant_id))
    if errors:
        for error in errors:
            if "raw secret-like field" in error:
                raise SiteOpsSecretError("; ".join(errors))
    return {
        "ok": not errors,
        "tenant_id": tenant_id,
        "errors": errors,
    }
