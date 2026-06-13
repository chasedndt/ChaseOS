"""Opaque credential reference helpers for SiteOps."""

from __future__ import annotations

from typing import Any

from runtime.siteops.errors import SiteOpsNotFoundError, SiteOpsSecurityError, SiteOpsValidationError
from runtime.siteops.tenancy import load_tenant, objects_by_id
from runtime.siteops.validator import scan_secret_like_keys


CONFIGURED_STATUSES = {"CONFIGURED", "CONFIGURED BUT UNVERIFIED", "VERIFIED", "ACTIVE"}


def list_credential_refs(root=None, tenant_id: str = "local") -> list[dict[str, Any]]:
    tenant = load_tenant(root, tenant_id)
    results: list[dict[str, Any]] = []
    for item in tenant.get("credential_refs", []):
        results.append(
            {
                "credential_ref_id": item["credential_ref_id"],
                "tenant_id": item["tenant_id"],
                "user_id": item.get("user_id"),
                "provider_id": item["provider_id"],
                "credential_type": item["credential_type"],
                "status": item["status"],
                "last_verified_at": item.get("last_verified_at"),
                "secret_store_ref_present": bool(item.get("secret_store_ref")),
            }
        )
    return results


def validate_no_secret_fields(payload: Any) -> None:
    errors = scan_secret_like_keys(payload)
    if errors:
        raise SiteOpsSecurityError("; ".join(errors))


def check_credential_ref(root=None, credential_ref_id: Any = "", tenant_id: str = "local", user_id: str | None = None) -> dict[str, Any]:
    if isinstance(root, dict):
        item = root
        if item.get("tenant_id") != tenant_id:
            raise SiteOpsSecurityError("CredentialRef tenant mismatch")
        if user_id and item.get("user_id") not in (None, user_id):
            raise SiteOpsSecurityError("CredentialRef user mismatch")
        validate_no_secret_fields({k: v for k, v in item.items() if k != "secret_store_ref"})
        return {
            "credential_ref_id": item.get("credential_ref_id"),
            "provider_id": item.get("provider_id"),
            "configured": str(item.get("status", "")).lower() in {"configured", "configured but unverified", "verified", "active"},
            "status": item.get("status"),
        }
    tenant = load_tenant(root, tenant_id)
    errors = scan_secret_like_keys(tenant.get("credential_refs", []))
    if errors:
        raise SiteOpsValidationError("; ".join(errors))
    credentials = objects_by_id(tenant.get("credential_refs", []), "credential_ref_id")
    item = credentials.get(credential_ref_id)
    if not item:
        raise SiteOpsNotFoundError(f"CredentialRef not found: {credential_ref_id}")
    if item.get("tenant_id") != tenant_id:
        raise SiteOpsValidationError("CredentialRef tenant mismatch")
    if user_id and item.get("user_id") not in (None, user_id):
        raise SiteOpsValidationError("CredentialRef user mismatch")
    return {
        "credential_ref_id": credential_ref_id,
        "tenant_id": tenant_id,
        "user_id": item.get("user_id"),
        "provider_id": item.get("provider_id"),
        "credential_type": item.get("credential_type"),
        "configured": item.get("status") in CONFIGURED_STATUSES and bool(item.get("secret_store_ref")),
        "status": item.get("status"),
        "secret_value_visible": False,
        "secret_store_ref_present": bool(item.get("secret_store_ref")),
    }
