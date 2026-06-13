from __future__ import annotations

from pathlib import Path

import pytest

from runtime.siteops.budgets import check_budget_policy
from runtime.siteops.errors import SiteOpsValidationError
from runtime.siteops.runner import run_siteops_dry_run
from runtime.siteops.tenancy import load_tenant, save_tenant


def test_paid_provider_requires_budget_policy(siteops_vault: Path) -> None:
    tenant = load_tenant(siteops_vault, "local")
    for binding in tenant["provider_account_bindings"]:
        if binding["provider_id"] == "gemini_image":
            binding["budget_policy_id"] = None
    save_tenant(siteops_vault, "local", tenant)

    with pytest.raises(SiteOpsValidationError, match="budget_policy"):
        run_siteops_dry_run(
            root=siteops_vault,
            workflow_id="gemini.image.edit",
            tenant_id="local",
            workspace_id="default",
            user_id="local-user",
            inputs={"source_image_path": "sample.png", "edit_prompt": "edit"},
        )


def test_provider_cost_above_threshold_requires_approval(siteops_vault: Path) -> None:
    decision = check_budget_policy(
        siteops_vault,
        tenant_id="local",
        provider_id="gemini_image",
        estimated_cost="0.0300",
    )

    assert decision["decision"] == "approval_required"
    assert decision["charged"] is False


def test_dry_run_estimates_cost_without_charge(siteops_vault: Path) -> None:
    result = run_siteops_dry_run(
        root=siteops_vault,
        workflow_id="gemini.image.edit",
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        inputs={"source_image_path": "sample.png", "edit_prompt": "edit"},
    )

    assert result["provider"]["estimated_cost_per_run"] == "0.0300"
    assert result["provider"]["charged"] is False
    assert result["run"]["cost_estimate"]["charged"] is False
