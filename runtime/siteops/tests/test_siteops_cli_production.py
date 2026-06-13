from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.cli import main as cli_main
from runtime.siteops.tenancy import load_tenant, save_tenant


def _result(capsys: pytest.CaptureFixture[str]) -> dict:
    return json.loads(capsys.readouterr().out)["result"]


def test_catalog_list_works(siteops_vault: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = cli_main.main(["siteops", "catalog", "list", "--vault-root", str(siteops_vault), "--json"])

    payload = _result(capsys)
    assert code == 0
    assert payload["ok"] is True
    assert payload["count"] >= 5


def test_skill_install_for_local_tenant_works(siteops_vault: Path, capsys: pytest.CaptureFixture[str]) -> None:
    tenant = load_tenant(siteops_vault, "local")
    tenant["site_skill_installations"] = [
        item
        for item in tenant["site_skill_installations"]
        if item["skill_template_id"] != "perplexity.research.capture"
    ]
    save_tenant(siteops_vault, "local", tenant)

    code = cli_main.main([
        "siteops",
        "skills",
        "install",
        "perplexity.research.capture",
        "--tenant",
        "local",
        "--vault-root",
        str(siteops_vault),
        "--json",
    ])

    payload = _result(capsys)
    assert code == 0
    assert payload["status"] == "installed"
    assert payload["installation"]["tenant_id"] == "local"


def test_workflow_dry_run_requires_tenant_and_user() -> None:
    with pytest.raises(SystemExit) as exc:
        cli_main.main([
            "siteops",
            "workflows",
            "dry-run",
            "perplexity.research.capture",
            "--tenant",
            "local",
            "--input",
            "query=ETH",
            "--json",
        ])

    assert exc.value.code == 2


def test_approval_list_works(siteops_vault: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = cli_main.main(["siteops", "approvals", "list", "--tenant", "local", "--vault-root", str(siteops_vault), "--json"])

    payload = _result(capsys)
    assert code == 0
    assert payload["ok"] is True
    assert payload["approvals"] == []


def test_credential_check_does_not_reveal_secret(siteops_vault: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = cli_main.main([
        "siteops",
        "credentials",
        "check",
        "local-perplexity-api-credential",
        "--tenant",
        "local",
        "--user",
        "local-user",
        "--vault-root",
        str(siteops_vault),
        "--json",
    ])

    payload = _result(capsys)
    assert code == 0
    assert payload["credential"]["secret_value_visible"] is False
    assert "PERPLEXITY_API_KEY" not in json.dumps(payload)


def test_browser_profile_check_does_not_reveal_session(siteops_vault: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = cli_main.main([
        "siteops",
        "browser-profiles",
        "check",
        "local-user-perplexity-browser",
        "--tenant",
        "local",
        "--user",
        "local-user",
        "--vault-root",
        str(siteops_vault),
        "--json",
    ])

    payload = _result(capsys)
    assert code == 0
    assert payload["browser_profile"]["session_value_visible"] is False
    assert "opaque_session_store_ref" not in json.dumps(payload)


def test_budget_check_estimates_without_charge(siteops_vault: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = cli_main.main([
        "siteops",
        "budgets",
        "check",
        "--provider",
        "perplexity_api",
        "--tenant",
        "local",
        "--estimated-cost",
        "0.0050",
        "--vault-root",
        str(siteops_vault),
        "--json",
    ])

    payload = _result(capsys)
    assert code == 0
    assert payload["budget"]["decision"] == "allow"
    assert payload["budget"]["charged"] is False
