from __future__ import annotations

from pathlib import Path

from runtime.workflow_packs.creative_studio import create_creative_studio_run
from runtime.workflow_packs.store import WorkflowPackStore


def test_creative_studio_run_creates_brief_copy_mockups_gates_and_proof(tmp_path: Path) -> None:
    result = create_creative_studio_run(
        tmp_path,
        title="Consulting launch pack",
        user_goal="Create a local launch campaign for founder ops consulting",
        campaign_type="local_business_campaign",
        brand_profile="Calm expert operator with strong delivery proof.",
        offer="Founder ops consulting sprint",
        audience="solo founders and small teams",
        tone="clear and confident",
        channels="landing page, social, email",
        primary_cta="Book a consult",
    )

    creative = result["creative_studio"]
    run_id = result["run"]["id"]
    store = WorkflowPackStore(tmp_path)
    artifacts = store.list_artifacts(run_id)
    gates = store.list_approval_gates(run_id)

    assert result["status"] == "creative_studio_created"
    assert result["external_actions_performed"] is False
    assert result["publishing_performed"] is False
    assert result["email_send_performed"] is False
    assert result["provider_calls_performed"] is False
    assert result["image_provider_calls_performed"] is False
    assert creative["creative_brief"]["offer"] == "Founder ops consulting sprint"
    assert creative["copy_pack"]["landing_cta"] == "Book a consult"
    assert creative["visual_mockup"]["format"] == "local_html_card"
    assert creative["landing_section_mockup"]["format"] == "local_html_section"
    assert {artifact.artifact_type for artifact in artifacts} >= {"report", "brief", "copy_pack", "html_mockup"}
    assert len([artifact for artifact in artifacts if artifact.artifact_type == "html_mockup"]) == 2
    assert {gate.action_type for gate in gates} == {"publish_content", "send_email"}
    assert result["approval_check"]["blocked"] is True
    assert result["proof_card"]["status"] == "review_required"
    assert (tmp_path / result["proof_paths"]["proof_card_json_path"]).is_file()

    copy_pack = next(artifact for artifact in artifacts if artifact.artifact_type == "copy_pack")
    copy_text = (tmp_path / copy_pack.local_path).read_text(encoding="utf-8")
    assert "No send or publish action should happen until this copy is approved." in copy_text

    visual_mockup = next(artifact for artifact in artifacts if artifact.title == "Visual Card Mockup")
    visual_html = (tmp_path / visual_mockup.local_path).read_text(encoding="utf-8")
    assert "Approval required before publish" in visual_html
    assert "Founder ops consulting sprint" in visual_html

    run = store.get_run(run_id)
    audit_log = (tmp_path / run.audit_log_ref).read_text(encoding="utf-8")
    assert "creative_studio_intake_ingested" in audit_log
    assert "creative_studio_artifacts_created" in audit_log
    assert "creative_studio_approval_gates_created" in audit_log


def test_creative_studio_uses_safe_defaults_when_questionnaire_is_empty(tmp_path: Path) -> None:
    result = create_creative_studio_run(tmp_path)
    creative = result["creative_studio"]

    assert creative["campaign_type"] == "local_business_campaign"
    assert creative["channels"] == ["landing page", "social caption", "email draft"]
    assert creative["safe_boundaries"]["external_actions_performed"] is False
    assert creative["safe_boundaries"]["mockups_are_local_static_html_only"] is True
    assert creative["safe_boundaries"]["forbidden_actions"] == [
        "publish_content",
        "send_email",
        "browser_action",
        "external_api_call",
        "runtime_execution",
    ]
