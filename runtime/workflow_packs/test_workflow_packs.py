from __future__ import annotations

from pathlib import Path

from runtime.workflow_packs.approvals import action_allowed
from runtime.workflow_packs.demo_provider import create_demo_workflow_run
from runtime.workflow_packs.panel import build_workflow_packs_panel
from runtime.workflow_packs.registry import list_workflow_packs, validate_registry
from runtime.workflow_packs.store import WorkflowPackStore


def test_registry_contains_four_product_facing_packs() -> None:
    packs = list_workflow_packs()
    ids = {pack.id for pack in packs}

    assert ids == {
        "visual_product_creative_studio",
        "founder_personal_automation_audit",
        "research_to_product_intelligence",
        "safe_agent_runtime_governance_kit",
    }
    assert all(pack.user_facing for pack in packs)
    assert validate_registry()["valid"] is True


def test_run_creation_persists_local_state(tmp_path: Path) -> None:
    store = WorkflowPackStore(tmp_path)

    run = store.create_run(
        pack_id="founder_personal_automation_audit",
        title="Audit onboarding",
        user_goal="Find repeated admin work",
    )

    loaded = store.get_run(run.id)
    assert loaded.pack_id == "founder_personal_automation_audit"
    assert loaded.input["user_goal"] == "Find repeated admin work"
    assert loaded.provider_mode == "demo_manual"
    assert (tmp_path / loaded.audit_log_ref).is_file()


def test_artifact_creation_persists_metadata_and_content(tmp_path: Path) -> None:
    store = WorkflowPackStore(tmp_path)
    run = store.create_run(
        pack_id="visual_product_creative_studio",
        title="Creative run",
        user_goal="Launch a service",
    )

    artifact = store.create_artifact(
        run_id=run.id,
        artifact_type="brief",
        title="Brief",
        content="# Brief\nLocal artifact",
    )

    assert artifact.review_status == "pending_review"
    assert (tmp_path / artifact.local_path).read_text(encoding="utf-8").startswith("# Brief")
    loaded = store.get_run(run.id)
    assert loaded.artifact_refs[0].id == artifact.id
    assert loaded.status == "artifact_ready"


def test_demo_provider_generates_artifacts_proof_and_pending_gate(tmp_path: Path) -> None:
    result = create_demo_workflow_run(
        tmp_path,
        pack_id="founder_personal_automation_audit",
        user_goal="Decide what to automate first",
    )

    assert result["status"] == "demo_run_created"
    assert result["external_actions_performed"] is False
    assert result["provider_calls_performed"] is False
    assert result["approval_gate"]["status"] == "pending"
    assert result["proof_card"]["status"] == "review_required"
    assert (tmp_path / result["proof_paths"]["proof_card_json_path"]).is_file()
    assert (tmp_path / result["proof_paths"]["proof_card_markdown_path"]).is_file()


def test_demo_provider_supports_all_four_phase1_packs(tmp_path: Path) -> None:
    for pack in list_workflow_packs():
        result = create_demo_workflow_run(tmp_path, pack_id=pack.id)
        store = WorkflowPackStore(tmp_path)
        artifacts = store.list_artifacts(result["run"]["id"])

        assert result["status"] == "demo_run_created"
        assert result["pack"]["id"] == pack.id
        assert result["approval_gate"]["status"] == "pending"
        assert artifacts
        assert all(artifact.review_status == "pending_review" for artifact in artifacts)


def test_approval_blocking_for_external_action(tmp_path: Path) -> None:
    result = create_demo_workflow_run(tmp_path, pack_id="visual_product_creative_studio")
    store = WorkflowPackStore(tmp_path)
    run_id = result["run"]["id"]
    gates = store.list_approval_gates(run_id)

    decision = action_allowed("publish_content", gates)

    assert decision["allowed"] is False
    assert decision["blocked"] is True
    assert decision["reason"] == "human_approval_required_before_external_or_sensitive_action"


def test_panel_model_exposes_new_run_runs_review_queue_and_proof_cards(tmp_path: Path) -> None:
    create_demo_workflow_run(tmp_path, pack_id="safe_agent_runtime_governance_kit")

    panel = build_workflow_packs_panel(tmp_path)

    assert panel["surface"] == "workflow_packs_panel"
    assert panel["summary"]["pack_count"] == 4
    assert panel["summary"]["run_count"] == 1
    assert panel["summary"]["review_queue_count"] >= 1
    assert panel["summary"]["proof_card_count"] == 1
    assert panel["new_run"]["provider_mode"] == "demo_manual"
    assert panel["safety"]["external_actions_blocked"] is True
    assert panel["authority"]["external_actions_allowed"] is False
    assert panel["authority"]["agent_bus_task_write_allowed"] is False
    assert panel["operating_context"]["title"] == "Mission Operating Context"
    assert panel["readiness"]["rows"]
    capabilities = {row["capability"] for row in panel["feature_family_coverage"]}
    assert "Product Workflow Packs foundation" in capabilities
    assert "Approval review, exact-once marker, and approved local resume" in capabilities
