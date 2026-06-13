from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.siteops.browser_profiles import check_browser_profile_ref, list_browser_profile_refs
from runtime.siteops.errors import SiteOpsSecretError, SiteOpsValidationError
from runtime.siteops.tenancy import load_tenant, save_tenant
from runtime.siteops.validator import validate_production_siteops


def test_browser_profile_ref_validates_without_session_contents(siteops_vault: Path) -> None:
    result = check_browser_profile_ref(
        siteops_vault,
        browser_profile_ref_id="local-user-canva-browser",
        tenant_id="local",
        user_id="local-user",
    )

    assert result["configured"] is True
    assert result["session_value_visible"] is False
    assert "opaque_session_store_ref" not in json.dumps(result)


def test_browser_profile_cannot_cross_user(siteops_vault: Path) -> None:
    with pytest.raises(SiteOpsValidationError, match="user mismatch"):
        check_browser_profile_ref(
            siteops_vault,
            browser_profile_ref_id="local-user-canva-browser",
            tenant_id="local",
            user_id="viewer-user",
        )


def test_browser_profile_cannot_cross_tenant(siteops_vault: Path) -> None:
    tenant = load_tenant(siteops_vault, "local")
    tenant["browser_profile_refs"][0]["tenant_id"] = "other"
    save_tenant(siteops_vault, "local", tenant)

    with pytest.raises(SiteOpsValidationError, match="tenant mismatch"):
        check_browser_profile_ref(
            siteops_vault,
            browser_profile_ref_id="local-user-canva-browser",
            tenant_id="local",
            user_id="local-user",
        )


def test_raw_cookies_in_browser_profile_yaml_fail_validation(siteops_vault: Path) -> None:
    tenant = load_tenant(siteops_vault, "local")
    tenant["browser_profile_refs"][0]["cookie"] = "session=not-real"
    save_tenant(siteops_vault, "local", tenant)

    with pytest.raises(SiteOpsSecretError, match="cookie"):
        validate_production_siteops(siteops_vault, "local")


def test_browser_profile_list_filters_to_user_without_session_data(siteops_vault: Path) -> None:
    profiles = list_browser_profile_refs(siteops_vault, tenant_id="local", user_id="local-user")

    assert profiles
    assert all(item["user_id"] == "local-user" for item in profiles)
    assert "opaque_session_store_ref" not in json.dumps(profiles)
