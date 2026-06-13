from __future__ import annotations

from datetime import datetime, timezone
import json
import shutil
from pathlib import Path

import pytest

from runtime.cli import main as cli_main
from runtime.siteops.registry import (
    SiteOpsRegistryError,
    build_dry_run_plan,
    parse_cli_inputs,
    validate_registry,
)


ROOT = Path(__file__).resolve().parents[2]


def _copy_siteops_registry() -> Path:
    vault = ROOT / "runtime" / "siteops" / "_tmp_test_vault"
    if vault.exists():
        shutil.rmtree(vault)
    source = ROOT / "runtime" / "siteops" / "registry"
    target = vault / "runtime" / "siteops" / "registry"
    shutil.copytree(source, target)
    return vault


def test_siteops_registry_validates_seed_objects() -> None:
    report = validate_registry(ROOT)

    assert report["ok"] is True
    assert report["counts"] == {
        "site": 3,
        "provider": 3,
        "workflow": 5,
        "skill": 5,
    }
    assert report["errors"] == []


def test_dry_run_plan_never_executes_live_surfaces() -> None:
    plan = build_dry_run_plan(
        "perplexity.research.capture",
        inputs={"query": "ETH 4H setup"},
        vault_root=ROOT,
        now=datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc),
    )

    assert plan["would_execute"] is False
    assert plan["mode"] == "dry_run"
    assert plan["live_execution_status"] == "NOT BUILT"
    assert "paid_provider_call" in plan["approval_gates"]
    assert "automatic_canonical_writeback" in plan["blocked_actions"]
    assert plan["audit_path"] is None


def test_dry_run_requires_declared_inputs() -> None:
    with pytest.raises(SiteOpsRegistryError, match="Missing required workflow inputs"):
        build_dry_run_plan("canva.poster.magic_layers", inputs={}, vault_root=ROOT)


def test_write_audit_record_uses_website_workflow_runs() -> None:
    vault = _copy_siteops_registry()
    try:
        plan = build_dry_run_plan(
            "tradingview.idea.capture",
            inputs={"idea_url": "https://www.tradingview.com/chart/example"},
            vault_root=vault,
            write_audit=True,
            now=datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc),
        )

        audit_path = Path(plan["audit_path"])
        assert audit_path.exists()
        assert audit_path.parent == vault / "07_LOGS" / "Website-Workflow-Runs"
        record = json.loads(audit_path.read_text(encoding="utf-8"))
        assert record["record_type"] == "siteops_run_record"
        assert record["workflow_id"] == "tradingview.idea.capture"
        assert record["would_execute"] is False
    finally:
        if vault.exists():
            shutil.rmtree(vault)


def test_parse_cli_inputs_rejects_unstructured_values() -> None:
    assert parse_cli_inputs(["query=ETH", "domain_hint=trading"]) == {
        "query": "ETH",
        "domain_hint": "trading",
    }
    with pytest.raises(SiteOpsRegistryError):
        parse_cli_inputs(["query"])


def test_siteops_cli_json_smoke(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli_main.main(
        [
            "siteops",
            "dry-run",
            "perplexity.research.capture",
            "--tenant",
            "local",
            "--user",
            "local-user",
            "--input",
            "query=ETH",
            "--json",
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["action"] == "siteops.dry-run"
    assert payload["result"]["dry_run"]["workflow_id"] == "perplexity.research.capture"
    assert payload["result"]["dry_run"]["would_execute"] is False
