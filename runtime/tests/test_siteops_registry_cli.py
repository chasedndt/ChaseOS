"""Tests for the first ChaseOS SiteOps registry and dry-run CLI slice."""

from __future__ import annotations

import json
import sys
from pathlib import Path


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

import runtime.cli.main as cli  # noqa: E402
from runtime.siteops.registry import (  # noqa: E402
    SITEOPS_REGISTRY_REL,
    load_siteops_registry,
    validate_siteops_registry,
    dry_run_siteops_workflow,
)


def test_siteops_registry_loads_seed_site_profiles_workflows_and_provider_stubs() -> None:
    registry = load_siteops_registry(_VAULT_ROOT)

    assert registry["feature_family"] == "ChaseOS SiteOps"
    assert registry["technical_registry"] == "Website Workflow Index"
    assert registry["user_facing_tab"] == "Site Skills"
    assert {site["site_id"] for site in registry["sites"]} >= {"canva", "tradingview", "perplexity"}
    assert {provider["provider_id"] for provider in registry["providers"]} >= {"gemini_image", "seedream_future"}
    assert {workflow["workflow_id"] for workflow in registry["workflows"]} >= {
        "canva.poster.magic_layers",
        "tradingview.idea.capture",
        "tradingview.indicator.review",
        "gemini.image.edit",
        "perplexity.research.capture",
    }


def test_siteops_registry_validation_blocks_secrets_and_requires_approval_boundaries() -> None:
    errors = validate_siteops_registry(_VAULT_ROOT)

    assert errors == []

    registry = load_siteops_registry(_VAULT_ROOT)
    canva = next(site for site in registry["sites"] if site["site_id"] == "canva")
    assert "password" not in json.dumps(canva).lower()
    assert "publish_publicly" in canva["blocked_actions"]
    assert "change_billing" in canva["blocked_actions"]
    assert "before_export" in next(
        workflow for workflow in registry["workflows"] if workflow["workflow_id"] == "canva.poster.magic_layers"
    )["approval_required"]


def test_siteops_dry_run_returns_bounded_plan_without_execution_or_writeback() -> None:
    result = dry_run_siteops_workflow(
        _VAULT_ROOT,
        "canva.poster.magic_layers",
        inputs={"source_image_path": "sample.png", "edit_prompt": "make it ChaseOS branded"},
    )

    assert result["ok"] is True
    assert result["mode"] == "dry_run"
    assert result["workflow_id"] == "canva.poster.magic_layers"
    assert result["site_profile"] == "canva"
    assert result["would_execute"] is False
    assert result["audit_target"].startswith("07_LOGS/Website-Workflow-Runs/")
    assert "publish_publicly" in result["blocked_actions"]
    assert "before_export" in result["approval_required"]
    assert result["input_status"]["source_image_path"] == "provided"
    assert result["input_status"]["edit_prompt"] == "provided"


def test_siteops_cli_list_show_validate_and_dry_run_are_json_enveloped() -> None:
    list_code = cli.main(["siteops", "list", "--json"])
    assert list_code == 0

    show_code = cli.main(["siteops", "show", "canva.poster.magic_layers", "--json"])
    assert show_code == 0

    validate_code = cli.main(["siteops", "validate", "--json"])
    assert validate_code == 0

    dry_run_code = cli.main(
        [
            "siteops",
            "dry-run",
            "canva.poster.magic_layers",
            "--tenant",
            "local",
            "--user",
            "local-user",
            "--input",
            "source_image_path=sample.png",
            "--input",
            "edit_prompt=make it ChaseOS branded",
            "--json",
        ]
    )
    assert dry_run_code == 0


def test_siteops_registry_location_is_runtime_local_not_canonical_knowledge() -> None:
    assert SITEOPS_REGISTRY_REL == "runtime/siteops"
