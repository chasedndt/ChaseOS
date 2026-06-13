from __future__ import annotations

import json
from pathlib import Path

from runtime.siteops.runner import run_siteops_dry_run


def test_scoped_dry_run_emits_run_and_audit_metadata(siteops_vault: Path) -> None:
    result = run_siteops_dry_run(
        root=siteops_vault,
        workflow_id="perplexity.research.capture",
        inputs={"query": "ETH setup"},
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
    )

    assert result["scope"] == {
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
    }
    assert result["run"]["status"] == "planned"
    assert result["would_execute"] is False
    assert result["live_execution_status"] == "NOT BUILT"
    assert Path(result["run_ref"]).exists()
    assert Path(result["audit_ref"]).exists()


def test_audit_metadata_is_scoped_and_secret_redacted(siteops_vault: Path) -> None:
    result = run_siteops_dry_run(
        root=siteops_vault,
        workflow_id="perplexity.research.capture",
        inputs={"query": "ETH setup", "api_key": "should-redact"},
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
    )

    events = [json.loads(line) for line in Path(result["audit_ref"]).read_text(encoding="utf-8").splitlines()]
    assert events
    assert all(event["tenant_id"] == "local" for event in events)
    assert all(event["workspace_id"] == "default" for event in events)
    assert "should-redact" not in json.dumps(events)
    assert "[REDACTED]" in json.dumps(events)


def test_dry_run_output_reports_provider_and_browser_status_only(siteops_vault: Path) -> None:
    result = run_siteops_dry_run(
        root=siteops_vault,
        workflow_id="perplexity.research.capture",
        inputs={"query": "ETH setup"},
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
    )

    assert result["provider"]["provider_adapter_id"] == "perplexity_api"
    assert result["provider"]["estimated_cost_per_run"] == "0.0050"
    assert result["provider"]["credentials_configured"] is True
    assert result["provider"]["charged"] is False
    assert result["browser_profile"]["session_value_visible"] is False
