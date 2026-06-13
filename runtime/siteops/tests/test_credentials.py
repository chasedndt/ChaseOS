from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.siteops.credentials import check_credential_ref, list_credential_refs
from runtime.siteops.errors import SiteOpsNotFoundError, SiteOpsSecretError
from runtime.siteops.tenancy import load_tenant, save_tenant
from runtime.siteops.validator import validate_production_siteops


def test_credential_ref_check_returns_status_without_secret_value(siteops_vault: Path) -> None:
    result = check_credential_ref(
        siteops_vault,
        credential_ref_id="local-perplexity-api-credential",
        tenant_id="local",
        user_id="local-user",
    )

    assert result["configured"] is True
    assert result["secret_value_visible"] is False
    assert "PERPLEXITY_API_KEY" not in json.dumps(result)


def test_credential_list_does_not_expose_secret_store_values(siteops_vault: Path) -> None:
    credentials = list_credential_refs(siteops_vault, tenant_id="local")

    assert credentials
    assert all("secret_store_ref" not in item for item in credentials)
    assert all(item["secret_store_ref_present"] is True for item in credentials)


def test_yaml_containing_raw_api_key_fails_validation(siteops_vault: Path) -> None:
    tenant = load_tenant(siteops_vault, "local")
    tenant["credential_refs"][0]["api_key"] = "not-real"
    save_tenant(siteops_vault, "local", tenant)

    with pytest.raises(SiteOpsSecretError, match="api_key"):
        validate_production_siteops(siteops_vault, "local")


def test_missing_credential_ref_returns_missing_not_secret(siteops_vault: Path) -> None:
    with pytest.raises(SiteOpsNotFoundError):
        check_credential_ref(siteops_vault, credential_ref_id="missing", tenant_id="local", user_id="local-user")
