from __future__ import annotations

from pathlib import Path

import pytest
import runtime.workflow_packs.store as store_module
from runtime.studio.shell.api import StudioAPI
from runtime.studio.shell.panel_registry import build_native_shell_panel_registry
from runtime.workflow_packs.panel import build_workflow_packs_panel


REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _short_workflow_pack_state_root(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(store_module, "STATE_ROOT", Path("wfp_state"))


def test_workflow_packs_panel_model_starts_empty_but_ready(tmp_path: Path) -> None:
    panel = build_workflow_packs_panel(tmp_path)

    assert panel["status"] == "approval_resume_contract_ready"
    assert panel["summary"]["pack_count"] == 4
    assert panel["summary"]["run_count"] == 0
    assert panel["summary"]["demo_manual_provider_ready"] is True
    assert panel["summary"]["automation_audit_mvp_ready"] is True
    assert panel["summary"]["creative_studio_mvp_ready"] is True
    assert panel["summary"]["research_intelligence_mvp_ready"] is True
    assert panel["summary"]["agent_governance_mvp_ready"] is True
    assert panel["summary"]["approval_resume_contract_ready"] is True
    assert panel["summary"]["approval_review_artifact_writer_ready"] is True
    assert panel["summary"]["approval_consumption_dry_run_ready"] is True
    assert panel["summary"]["approval_consumption_exact_once_marker_dry_run_ready"] is True
    assert panel["summary"]["approval_marker_reservation_ready"] is True
    assert panel["summary"]["approved_local_resume_executor_ready"] is True
    assert panel["summary"]["approval_review_artifact_consumption_built"] is True
    assert panel["summary"]["approval_review_artifact_exact_once_marker_built"] is True
    assert panel["summary"]["approval_consumption_marker_writer_built"] is True
    assert panel["summary"]["approval_consumption_built"] is True
    assert panel["summary"]["resume_executor_built"] is True
    assert panel["authority"]["external_actions_allowed"] is False
    assert panel["authority"]["provider_calls_allowed"] is False
    assert panel["authority"]["agent_bus_task_write_allowed"] is False
    assert panel["authority"]["runtime_dispatch_allowed"] is False
    assert panel["operating_context"]["title"] == "Mission Operating Context"
    assert panel["readiness"]["rows"][0]["label"] == "Pack registry"
    assert panel["feature_family_coverage"]
    assert panel["approval_resume"]["status"] == "blocked_missing_run_id"
    assert panel["safety"]["external_actions_performed"] is False
    assert panel["safety"]["approval_consumption_performed"] is False


def test_studio_api_exposes_workflow_packs_panel_and_demo_run(tmp_path: Path) -> None:
    api = StudioAPI(tmp_path)

    panel = api.get_workflow_packs_panel()
    assert panel["ok"] is True
    assert panel["surface"] == "workflow_packs_panel"
    assert panel["data"]["summary"]["pack_count"] == 4

    created = api.create_workflow_pack_demo_run(
        "founder_personal_automation_audit",
        "Audit demo",
        "Find the first workflow to automate",
    )
    assert created["ok"] is True
    assert created["data"]["run"]["title"] == "Audit demo"
    assert created["data"]["approval_check"]["blocked"] is True

    refreshed = api.get_workflow_packs_panel()
    assert refreshed["data"]["summary"]["run_count"] == 1
    assert refreshed["data"]["summary"]["proof_card_count"] == 1

    audit = api.create_automation_audit_run(
        "Guided audit",
        "Find the safest first automation",
        "Draft weekly report\nSend client follow-up emails\nReview intake queue",
        "ops, sales",
        "manual and easy to forget",
    )
    assert audit["ok"] is True
    assert audit["data"]["automation_audit"]["draft_manifests"]
    assert audit["data"]["approval_check"]["blocked"] is True

    creative = api.create_creative_studio_run(
        "Launch pack",
        "Create a campaign for a local consulting offer",
        "local_business_campaign",
        "Quiet expert brand with strong proof from client work",
        "Founder ops consult",
        "solo founders",
        "clear and confident",
        "landing page, social, email",
        "Book a consult",
    )
    assert creative["ok"] is True
    assert creative["data"]["creative_studio"]["creative_brief"]["offer"] == "Founder ops consult"
    assert creative["data"]["approval_check"]["blocked"] is True
    assert creative["data"]["publishing_performed"] is False

    research = api.create_research_intelligence_run(
        "Research scout",
        "Decide whether to build a source-to-feature engine",
        "feature integration",
        "Founders need evidence-based product decisions from messy AI tool research.",
        "https://github.com/example/research-tool",
        "ChaseOS workflow packs",
        "Adopt useful local foundations and defer risky external automation",
        "founders and developers",
        "implementation brief and R&D export",
    )
    assert research["ok"] is True
    assert research["data"]["research_intelligence"]["claims"]
    assert research["data"]["approval_check"]["blocked"] is True
    assert research["data"]["graph_promotion_performed"] is False

    governance = api.create_agent_governance_run(
        "Agent governance",
        "Audit Codex before live workflow execution",
        "Codex",
        "agent bus worker",
        "configured but unverified",
        "repo.inspect\ncode.patch\ntest.run",
        "operator prompt\nruntime/codex/capabilities.yaml",
        "runtime/workflow_packs/state",
        "send_email\nbrowser_action",
        "repo files\napproval queue\nbrowser control",
        "actions:\n  - send_email\nbrowser: click pages\nsources: all files",
        "review required before sensitive action",
    )
    assert governance["ok"] is True
    assert governance["data"]["agent_governance"]["permission_matrix"]
    assert governance["data"]["agent_governance"]["manifest_lint"]["findings"]
    assert governance["data"]["approval_check"]["blocked"] is True
    assert governance["data"]["policy_applied_live"] is False
    assert governance["data"]["hermes_permission_escalation_performed"] is False
    assert governance["data"]["openclaw_permission_escalation_performed"] is False

    contract = api.get_workflow_pack_approval_resume_contract(
        governance["data"]["run"]["id"],
        governance["data"]["approval_gate"]["id"],
    )
    assert contract["ok"] is True
    assert contract["surface"] == "workflow_pack_approval_resume_contract"
    assert contract["data"]["summary"]["contract_preview_ready"] is True
    assert contract["data"]["summary"]["approval_consumption_performed"] is False
    assert contract["data"]["summary"]["resume_execution_performed"] is False
    assert contract["data"]["checks"]["execution_allowed_now"] is False

    review = api.review_workflow_pack_approval_artifact(
        governance["data"]["run"]["id"],
        governance["data"]["approval_gate"]["id"],
        contract["data"]["summary"]["request_digest"],
    )
    assert review["ok"] is True
    assert review["surface"] == "workflow_pack_approval_review_artifact"
    assert review["data"]["summary"]["approval_artifact_ready"] is True
    assert review["data"]["summary"]["approval_artifact_written"] is False
    assert review["data"]["summary"]["approval_decision_consumed"] is False
    assert review["data"]["summary"]["resume_execution_performed"] is False
    assert review["data"]["writes_performed"] is False

    written = api.review_workflow_pack_approval_artifact(
        governance["data"]["run"]["id"],
        governance["data"]["approval_gate"]["id"],
        contract["data"]["summary"]["request_digest"],
        "operator-test",
        review["data"]["approval_artifact"]["required_operator_statement"],
        "approved",
        True,
    )
    assert written["ok"] is True
    assert written["data"]["summary"]["approval_artifact_written"] is True
    assert written["data"]["summary"]["approval_decision_consumed"] is False
    assert written["data"]["summary"]["exact_once_marker_reserved"] is False
    assert written["data"]["summary"]["resume_execution_performed"] is False
    assert written["data"]["summary"]["agent_bus_dispatch_performed"] is False

    consumption = api.get_workflow_pack_approval_consumption_dry_run(
        governance["data"]["run"]["id"],
        governance["data"]["approval_gate"]["id"],
        contract["data"]["summary"]["request_digest"],
        written["data"]["approval_artifact"]["path"],
        "approved",
    )
    assert consumption["ok"] is True
    assert consumption["surface"] == "workflow_pack_approval_consumption_dry_run"
    assert consumption["data"]["summary"]["approval_consumption_dry_run_ready"] is True
    assert consumption["data"]["summary"]["approval_decision_consumed"] is False
    assert consumption["data"]["summary"]["approval_consumption_performed"] is False
    assert consumption["data"]["summary"]["exact_once_marker_reserved"] is False
    assert consumption["data"]["summary"]["resume_execution_performed"] is False
    assert consumption["data"]["writes_performed"] is False

    marker_preview = api.reserve_workflow_pack_exact_once_marker(
        governance["data"]["run"]["id"],
        governance["data"]["approval_gate"]["id"],
        contract["data"]["summary"]["request_digest"],
        written["data"]["approval_artifact"]["path"],
        "approved",
    )
    assert marker_preview["ok"] is True
    assert marker_preview["surface"] == "workflow_pack_approval_marker_reservation"
    assert marker_preview["data"]["summary"]["approval_marker_reservation_ready"] is True
    assert marker_preview["data"]["summary"]["approval_decision_consumed"] is False
    assert marker_preview["data"]["summary"]["exact_once_marker_reserved"] is False
    assert marker_preview["data"]["writes_performed"] is False

    marker_written = api.reserve_workflow_pack_exact_once_marker(
        governance["data"]["run"]["id"],
        governance["data"]["approval_gate"]["id"],
        contract["data"]["summary"]["request_digest"],
        written["data"]["approval_artifact"]["path"],
        "approved",
        True,
        marker_preview["data"]["exact_once_marker"]["required_operator_statement"],
        "operator-test",
    )
    assert marker_written["ok"] is True, marker_written
    assert marker_written["data"]["summary"]["exact_once_marker_reserved"] is True
    assert marker_written["data"]["summary"]["approval_decision_consumed"] is False
    assert marker_written["data"]["summary"]["approval_consumption_performed"] is False
    assert marker_written["data"]["summary"]["resume_execution_performed"] is False
    assert marker_written["data"]["writes_performed"] is True

    resume_preview = api.execute_workflow_pack_approved_local_resume(
        governance["data"]["run"]["id"],
        governance["data"]["approval_gate"]["id"],
        contract["data"]["summary"]["request_digest"],
        written["data"]["approval_artifact"]["path"],
        marker_written["data"]["exact_once_marker"]["path"],
        "approved",
    )
    assert resume_preview["ok"] is True
    assert resume_preview["surface"] == "workflow_pack_approved_local_resume_executor"
    assert resume_preview["data"]["summary"]["approved_local_resume_ready"] is True
    assert resume_preview["data"]["summary"]["approval_decision_consumed"] is False
    assert resume_preview["data"]["summary"]["resume_execution_performed"] is False
    assert resume_preview["data"]["writes_performed"] is False

    resumed = api.execute_workflow_pack_approved_local_resume(
        governance["data"]["run"]["id"],
        governance["data"]["approval_gate"]["id"],
        contract["data"]["summary"]["request_digest"],
        written["data"]["approval_artifact"]["path"],
        marker_written["data"]["exact_once_marker"]["path"],
        "approved",
        True,
        resume_preview["data"]["local_resume_evidence"]["required_operator_statement"],
        "operator-test",
    )
    assert resumed["ok"] is True, resumed
    assert resumed["data"]["summary"]["approval_decision_consumed"] is True
    assert resumed["data"]["summary"]["approval_consumption_performed"] is True
    assert resumed["data"]["summary"]["resume_execution_performed"] is True
    assert resumed["data"]["summary"]["external_actions_performed"] is False
    assert resumed["data"]["writes_performed"] is True

    refreshed_after_resume = api.get_workflow_packs_panel()
    assert refreshed_after_resume["ok"] is True
    assert all(
        item["item_id"] != governance["data"]["approval_gate"]["id"]
        for item in refreshed_after_resume["data"]["review_queue"]
    )
    resumed_run = next(
        run
        for run in refreshed_after_resume["data"]["runs"]
        if run["id"] == governance["data"]["run"]["id"]
    )
    assert resumed_run["status"] == "approved"


def test_panel_registry_marks_workflow_packs_mounted(tmp_path: Path) -> None:
    registry = build_native_shell_panel_registry(tmp_path)
    panels = {panel["id"]: panel for panel in registry["panels"]}

    assert "workflow-packs" in panels
    assert panels["workflow-packs"]["frontend_target"] == "panel-workflow-packs"
    assert panels["workflow-packs"]["api_methods"] == [
        "get_workflow_packs_panel",
        "create_workflow_pack_demo_run",
        "create_automation_audit_run",
        "create_creative_studio_run",
        "create_research_intelligence_run",
        "create_agent_governance_run",
        "get_workflow_pack_approval_resume_contract",
        "review_workflow_pack_approval_artifact",
        "get_workflow_pack_approval_consumption_dry_run",
        "reserve_workflow_pack_exact_once_marker",
        "execute_workflow_pack_approved_local_resume",
    ]
    assert panels["workflow-packs"]["read_only"] is False
    assert panels["workflow-packs"]["write_mode"] == "approval_gated"
    assert registry["readiness"]["workflow_packs_panel_mounted"] is True
    assert registry["readiness"]["workflow_packs_demo_manual_provider_ready"] is True
    assert registry["readiness"]["workflow_packs_automation_audit_mvp_ready"] is True
    assert registry["readiness"]["workflow_packs_creative_studio_mvp_ready"] is True
    assert registry["readiness"]["workflow_packs_research_intelligence_mvp_ready"] is True
    assert registry["readiness"]["workflow_packs_agent_governance_mvp_ready"] is True
    assert registry["readiness"]["workflow_packs_approval_resume_contract_ready"] is True
    assert registry["readiness"]["workflow_packs_approval_review_artifact_writer_ready"] is True
    assert registry["readiness"]["workflow_packs_approval_consumption_dry_run_ready"] is True
    assert registry["readiness"]["workflow_packs_approval_consumption_exact_once_marker_dry_run_ready"] is True
    assert registry["readiness"]["workflow_packs_approval_marker_reservation_ready"] is True
    assert registry["readiness"]["workflow_packs_approved_local_resume_executor_ready"] is True
    assert registry["readiness"]["workflow_packs_approval_review_artifact_consumption_blocked"] is False
    assert registry["readiness"]["workflow_packs_approval_review_artifact_exact_once_marker_built"] is True
    assert registry["readiness"]["workflow_packs_approval_consumption_marker_writer_built"] is True
    assert registry["readiness"]["workflow_packs_approval_consumption_built"] is True
    assert registry["readiness"]["workflow_packs_resume_executor_built"] is True
    assert registry["readiness"]["workflow_packs_external_actions_blocked"] is True


def test_frontend_static_hooks_for_workflow_packs_panel() -> None:
    frontend_root = REPO_ROOT / "runtime" / "studio" / "shell" / "frontend"
    index_html = (frontend_root / "index.html").read_text(encoding="utf-8")
    app_js = (frontend_root / "app.js").read_text(encoding="utf-8")
    styles_css = (frontend_root / "styles.css").read_text(encoding="utf-8")

    assert 'data-panel="workflow-packs"' in index_html
    assert 'id="panel-workflow-packs"' in index_html
    assert "get_workflow_packs_panel" in app_js
    assert "create_workflow_pack_demo_run" in app_js
    assert "create_automation_audit_run" in app_js
    assert "create_creative_studio_run" in app_js
    assert "create_research_intelligence_run" in app_js
    assert "create_agent_governance_run" in app_js
    assert "execute_workflow_pack_approved_local_resume" in app_js
    assert "runWorkflowPackLocalResume" in app_js
    assert "workflow-pack-approval-action" in app_js
    assert "Approve Local" in app_js
    assert "Reject Local" in app_js
    assert "Mission Operating Context" in app_js
    assert "Mission Readiness" in app_js
    assert "Mission Capabilities" in app_js
    assert "renderWorkflowPacksMissionBoard" in app_js
    assert 'data-mission-pack-card="pack"' in app_js
    assert 'data-mission-run-card="run"' in app_js
    assert "renderWorkflowPackInspectorContext" in app_js
    assert "defaultPackId" in app_js
    assert "loadWorkflowPacksPanel" in app_js
    assert "workflow-packs-tabs" in index_html
    assert "Missions" in index_html
    assert "workflow-packs-operating-context" in index_html
    assert "workflow-packs-board" in index_html
    assert "workflow-packs-readiness" in index_html
    assert "workflow-packs-feature-coverage" in index_html
    assert "workflow-packs-automation-audit-fields" in index_html
    assert "workflow-packs-creative-studio-fields" in index_html
    assert "workflow-packs-research-intelligence-fields" in index_html
    assert "workflow-packs-agent-governance-fields" in index_html
    assert ".workflow-packs-panel" in styles_css
    assert ".workflow-packs-context-panel" in styles_css
    assert ".workflow-packs-board-panel" in styles_css
    assert ".workflow-packs-board-lane" in styles_css
    assert ".workflow-packs-readiness-panel" in styles_css
    assert ".workflow-packs-feature-coverage" in styles_css
    assert ".workflow-pack-boundary" in styles_css
    assert ".workflow-packs-automation-audit-fields" in styles_css
    assert ".workflow-packs-creative-studio-fields" in styles_css
    assert ".workflow-packs-research-intelligence-fields" in styles_css
    assert ".workflow-packs-agent-governance-fields" in styles_css
    assert ".workflow-pack-approval-actions" in styles_css
    assert ".workflow-pack-approval-result" in styles_css
