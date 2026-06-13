from __future__ import annotations

from pathlib import Path

import pytest

from runtime.siteops.errors import SiteOpsNotFoundError, SiteOpsPolicyError, SiteOpsValidationError
from runtime.siteops.runner import run_siteops_dry_run
from runtime.siteops.tenancy import DEFAULT_LOCAL_SCOPE, assert_scope, load_local_tenant


def test_local_tenant_fixture_uses_production_scope_fields() -> None:
    tenant = load_local_tenant()

    assert tenant["tenant_id"] == "local"
    assert tenant["default_workspace_id"] == "default"
    assert tenant["default_user_id"] == "local-user"
    assert tenant["mode"] == "local_dev"


def test_run_missing_tenant_id_fails_closed(siteops_vault: Path) -> None:
    with pytest.raises(SiteOpsValidationError, match="tenant_id"):
        run_siteops_dry_run(
            root=siteops_vault,
            workflow_id="perplexity.research.capture",
            tenant_id=None,
            workspace_id="default",
            user_id="local-user",
            inputs={"query": "ETH"},
        )


def test_run_missing_user_id_fails_closed(siteops_vault: Path) -> None:
    with pytest.raises(SiteOpsValidationError, match="user_id"):
        run_siteops_dry_run(
            root=siteops_vault,
            workflow_id="perplexity.research.capture",
            tenant_id="local",
            workspace_id="default",
            user_id=None,
            inputs={"query": "ETH"},
        )


def test_user_cannot_access_workflow_without_runner_role(siteops_vault: Path) -> None:
    with pytest.raises(SiteOpsPolicyError, match="user is not allowed|role"):
        run_siteops_dry_run(
            root=siteops_vault,
            workflow_id="perplexity.research.capture",
            tenant_id="local",
            workspace_id="default",
            user_id="viewer-user",
            inputs={"query": "ETH"},
        )


def test_unknown_tenant_cannot_access_local_workflows(siteops_vault: Path) -> None:
    with pytest.raises(SiteOpsNotFoundError):
        run_siteops_dry_run(
            root=siteops_vault,
            workflow_id="perplexity.research.capture",
            tenant_id="other",
            workspace_id="default",
            user_id="local-user",
            inputs={"query": "ETH"},
        )


def test_default_local_scope_is_not_a_separate_architecture() -> None:
    assert DEFAULT_LOCAL_SCOPE == {
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
    }
    assert_scope(DEFAULT_LOCAL_SCOPE)
