from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.siteops.approvals import decide_approval_request, show_approval_request
from runtime.siteops.errors import SiteOpsValidationError
from runtime.siteops.runner import run_siteops_dry_run


def test_approval_required_action_returns_approval_needed_and_creates_object(siteops_vault: Path) -> None:
    result = run_siteops_dry_run(
        root=siteops_vault,
        workflow_id="perplexity.research.capture",
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        inputs={"query": "ETH setup"},
        action="external_share",
    )

    assert result["run"]["status"] == "approval_needed"
    assert result["would_execute"] is False
    assert result["approval"]["status"] == "pending"
    approval = show_approval_request(siteops_vault, result["approval"]["approval_id"], tenant_id="local")
    assert approval["status"] == "pending"


def test_approved_action_records_approval_event_in_dry_run_simulation(siteops_vault: Path) -> None:
    result = run_siteops_dry_run(
        root=siteops_vault,
        workflow_id="perplexity.research.capture",
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        inputs={"query": "ETH setup"},
        action="external_share",
    )

    approval = decide_approval_request(
        siteops_vault,
        result["approval"]["approval_id"],
        actor="local-user",
        status="approved",
        tenant_id="local",
    )

    assert approval["status"] == "approved"
    audit_events = [json.loads(line) for line in Path(result["audit_ref"]).read_text(encoding="utf-8").splitlines()]
    assert any(event["event_type"] == "approval_decision" and event["policy_decision"] == "approved" for event in audit_events)


def test_rejected_approval_blocks_second_resume_attempt(siteops_vault: Path) -> None:
    result = run_siteops_dry_run(
        root=siteops_vault,
        workflow_id="perplexity.research.capture",
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        inputs={"query": "ETH setup"},
        action="external_share",
    )

    rejected = decide_approval_request(
        siteops_vault,
        result["approval"]["approval_id"],
        actor="local-user",
        status="rejected",
        tenant_id="local",
    )

    assert rejected["status"] == "rejected"
    with pytest.raises(SiteOpsValidationError, match="not pending"):
        decide_approval_request(
            siteops_vault,
            result["approval"]["approval_id"],
            actor="local-user",
            status="approved",
            tenant_id="local",
        )


def test_actor_without_approver_role_cannot_approve(siteops_vault: Path) -> None:
    result = run_siteops_dry_run(
        root=siteops_vault,
        workflow_id="perplexity.research.capture",
        tenant_id="local",
        workspace_id="default",
        user_id="local-user",
        inputs={"query": "ETH setup"},
        action="external_share",
    )

    with pytest.raises(SiteOpsValidationError, match="approval role"):
        decide_approval_request(
            siteops_vault,
            result["approval"]["approval_id"],
            actor="viewer-user",
            status="approved",
            tenant_id="local",
        )
