from __future__ import annotations

import json
from pathlib import Path

from runtime.workflow_packs.automation_audit import create_automation_audit_run
from runtime.workflow_packs.store import WorkflowPackStore


def test_automation_audit_run_creates_scorecard_manifests_gates_and_proof(tmp_path: Path) -> None:
    result = create_automation_audit_run(
        tmp_path,
        title="Founder workflow audit",
        user_goal="Find repeatable founder admin automations",
        work_domains="ops, sales",
        repeated_tasks="\n".join(
            [
                "Draft weekly status report from scattered notes",
                "Send client follow-up emails after meetings",
                "Review new intake requests and decide next action",
            ]
        ),
        pain_points="Manual updates are slow and easy to forget.",
    )

    audit = result["automation_audit"]
    run_id = result["run"]["id"]
    store = WorkflowPackStore(tmp_path)
    artifacts = store.list_artifacts(run_id)
    gates = store.list_approval_gates(run_id)

    assert result["status"] == "automation_audit_created"
    assert result["external_actions_performed"] is False
    assert result["runtime_execution_performed"] is False
    assert result["provider_calls_performed"] is False
    assert len(audit["top_opportunities"]) == 3
    assert len(audit["draft_manifests"]) == 3
    assert {artifact.artifact_type for artifact in artifacts} >= {"report", "scorecard", "manifest", "brief"}
    assert {gate.action_type for gate in gates} >= {"runtime_execution", "send_email"}
    assert result["approval_check"]["blocked"] is True
    assert result["proof_card"]["status"] == "review_required"
    assert (tmp_path / result["proof_paths"]["proof_card_json_path"]).is_file()

    scorecard = next(artifact for artifact in artifacts if artifact.artifact_type == "scorecard")
    scorecard_data = json.loads((tmp_path / scorecard.local_path).read_text(encoding="utf-8"))
    assert scorecard_data["schema"] == "workflow_packs.automation_audit.scorecard.v1"
    assert len(scorecard_data["items"]) == 3
    assert all(item["automation_score"] > 0 for item in scorecard_data["items"])

    manifest = next(artifact for artifact in artifacts if artifact.artifact_type == "manifest")
    manifest_text = (tmp_path / manifest.local_path).read_text(encoding="utf-8")
    assert manifest_text.count("  - id: automation_audit_") == 3
    assert "runtime_execution" in manifest_text

    run = store.get_run(run_id)
    audit_log = (tmp_path / run.audit_log_ref).read_text(encoding="utf-8")
    assert "automation_audit_questionnaire_ingested" in audit_log
    assert "automation_audit_artifacts_created" in audit_log
    assert "automation_audit_approval_gates_created" in audit_log


def test_automation_audit_uses_safe_defaults_when_questionnaire_is_empty(tmp_path: Path) -> None:
    result = create_automation_audit_run(tmp_path)
    audit = result["automation_audit"]

    assert len(audit["repeated_tasks"]) >= 3
    assert len(audit["draft_manifests"]) == 3
    assert audit["safe_boundaries"]["external_actions_performed"] is False
    assert audit["safe_boundaries"]["generated_manifests_are_drafts_only"] is True
