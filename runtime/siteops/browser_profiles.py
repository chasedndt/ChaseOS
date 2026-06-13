"""Opaque browser profile reference helpers for SiteOps."""

from __future__ import annotations

from typing import Any

from runtime.siteops.errors import SiteOpsNotFoundError, SiteOpsSecurityError, SiteOpsValidationError
from runtime.siteops.tenancy import load_tenant, objects_by_id
from runtime.siteops.validator import scan_secret_like_keys


def list_browser_profile_refs(root=None, tenant_id: str = "local", user_id: str | None = None) -> list[dict[str, Any]]:
    tenant = load_tenant(root, tenant_id)
    results: list[dict[str, Any]] = []
    for item in tenant.get("browser_profile_refs", []):
        if user_id and item.get("user_id") != user_id:
            continue
        results.append(
            {
                "browser_profile_ref_id": item["browser_profile_ref_id"],
                "tenant_id": item["tenant_id"],
                "user_id": item["user_id"],
                "provider": item["provider"],
                "allowed_domains": item.get("allowed_domains", []),
                "status": item["status"],
                "created_at": item.get("created_at"),
                "last_verified_at": item.get("last_verified_at"),
                "session_value_visible": False,
            }
        )
    return results


def check_browser_profile_ref(root=None, browser_profile_ref_id: str = "", tenant_id: str = "local", user_id: str | None = None) -> dict[str, Any]:
    if isinstance(root, dict):
        item = root
        errors = scan_secret_like_keys(item)
        if errors:
            raise SiteOpsSecurityError("; ".join(errors))
        if item.get("tenant_id") != tenant_id:
            raise SiteOpsSecurityError("Browser profile tenant mismatch")
        if user_id and item.get("user_id") != user_id:
            raise SiteOpsSecurityError("Browser profile user mismatch")
        return {
            "browser_profile_ref_id": item.get("browser_profile_ref_id"),
            "tenant_id": tenant_id,
            "user_id": item.get("user_id"),
            "provider": item.get("provider"),
            "allowed_domains": item.get("allowed_domains", []),
            "configured": str(item.get("status", "")).lower() in {"configured", "configured but unverified", "verified", "active"},
            "status": item.get("status"),
            "session_value_visible": False,
        }
    tenant = load_tenant(root, tenant_id)
    errors = scan_secret_like_keys(tenant.get("browser_profile_refs", []))
    if errors:
        raise SiteOpsValidationError("; ".join(errors))
    profiles = objects_by_id(tenant.get("browser_profile_refs", []), "browser_profile_ref_id")
    item = profiles.get(browser_profile_ref_id)
    if not item:
        raise SiteOpsNotFoundError(f"UserBrowserProfileRef not found: {browser_profile_ref_id}")
    if item.get("tenant_id") != tenant_id:
        raise SiteOpsValidationError("Browser profile tenant mismatch")
    if user_id and item.get("user_id") != user_id:
        raise SiteOpsValidationError("Browser profile user mismatch")
    return {
        "browser_profile_ref_id": browser_profile_ref_id,
        "tenant_id": tenant_id,
        "user_id": item.get("user_id"),
        "provider": item.get("provider"),
        "allowed_domains": item.get("allowed_domains", []),
        "configured": item.get("status") in {"CONFIGURED", "CONFIGURED BUT UNVERIFIED", "VERIFIED", "ACTIVE"},
        "status": item.get("status"),
        "session_value_visible": False,
        "opaque_session_ref_present": bool(item.get("opaque_session_store_ref")),
    }
