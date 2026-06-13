from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.siteops.policy import evaluate_siteops_policy, select_policy_pack
from runtime.siteops.runner import run_siteops_dry_run
from runtime.siteops.tenancy import load_catalog, load_tenant, objects_by_id, require_scope


def test_blocked_action_denies(siteops_vault: Path) -> None:
    result = run_siteops_dry_run(
        root=siteops_vault,
        workflow_id="canva.poster.magic_layers",
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        inputs={"source_image_path": "sample.png", "edit_prompt": "brand it"},
        action="purchase",
    )

    assert result["run"]["status"] == "blocked"
    assert result["policy_decisions"][0]["decision"] == "deny"


def test_domain_not_allowlisted_denies(siteops_vault: Path) -> None:
    catalog = load_catalog(siteops_vault)
    tenant = load_tenant(siteops_vault, "local")
    workflow_installation = objects_by_id(tenant["workflow_installations"], "workflow_template_id")["canva.poster.magic_layers"]
    workflow_template = objects_by_id(catalog["workflow_templates"], "workflow_template_id")["canva.poster.magic_layers"]
    skill_installation = objects_by_id(tenant["site_skill_installations"], "skill_template_id")["canva.poster.magic_layers"]
    browser_profile_ref = objects_by_id(tenant["browser_profile_refs"], "browser_profile_ref_id")["local-user-canva-browser"]
    policy_pack = select_policy_pack(catalog, "siteops_default_v1")

    result = evaluate_siteops_policy(
        root=siteops_vault,
        run_id="run_domain_test",
        scope=require_scope(tenant_id="local", workspace_id="default", user_id="local-user"),
        tenant=tenant,
        skill_installation=skill_installation,
        workflow_installation=workflow_installation,
        workflow_template=workflow_template,
        provider_template=None,
        provider_binding=None,
        credential_ref=None,
        browser_profile_ref=browser_profile_ref,
        budget_policy=None,
        policy_pack_version=policy_pack["version"],
        action="dry_run",
        target_domain="evil.example",
    )

    assert result["status"] == "blocked"
    assert result["decisions"][0].decision == "deny"


def test_budget_above_threshold_returns_approval_required(siteops_vault: Path) -> None:
    result = run_siteops_dry_run(
        root=siteops_vault,
        workflow_id="gemini.image.edit",
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        inputs={"source_image_path": "sample.png", "edit_prompt": "make ad variations"},
    )

    assert result["run"]["status"] == "approval_needed"
    assert result["approval"]["status"] == "pending"
    assert any(decision["decision"] == "approval_required" for decision in result["policy_decisions"])


def test_policy_decision_is_logged(siteops_vault: Path) -> None:
    result = run_siteops_dry_run(
        root=siteops_vault,
        workflow_id="perplexity.research.capture",
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        inputs={"query": "ETH"},
    )

    audit_path = Path(result["audit_ref"])
    assert audit_path.exists()
    events = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
    assert any(event["event_type"] == "policy_decision" for event in events)
    assert "secret" not in json.dumps(events).lower()
