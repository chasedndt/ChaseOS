from __future__ import annotations

import json
from pathlib import Path

from runtime.workflow_packs.agent_governance import create_agent_governance_run
from runtime.workflow_packs.store import WorkflowPackStore


def test_agent_governance_run_creates_matrix_risks_policy_lint_tests_gates_and_proof(tmp_path: Path) -> None:
    result = create_agent_governance_run(
        tmp_path,
        title="Codex governance audit",
        user_goal="Audit the Codex bus worker before live use",
        agent_name="Codex",
        runtime="agent bus worker",
        runtime_status="configured but unverified",
        tools="repo.inspect\ncode.patch\nbrowser_action\nexternal_api_call",
        reads_from="operator-provided manifest\n.env metadata",
        writes_to="runtime/workflow_packs/state\nrepo root",
        external_actions="send_email\npublish_content",
        permission_surfaces="repo files\nbrowser control\nemail\ncanonical graph\nsecrets",
        workflow_manifest="""id: unsafe_governance_candidate
steps:
  - read .env values
  - send_email to operator
  - browser scrape all pages
  - promote generated claim to canonical graph
  - write output to C:\\Users\\chaseos
""",
        approval_expectations="Human approval before every send, publish, browser, execution, policy, or graph action.",
    )

    governance = result["agent_governance"]
    run_id = result["run"]["id"]
    store = WorkflowPackStore(tmp_path)
    artifacts = store.list_artifacts(run_id)
    gates = store.list_approval_gates(run_id)

    assert result["status"] == "agent_governance_created"
    assert result["external_actions_performed"] is False
    assert result["runtime_execution_performed"] is False
    assert result["policy_applied_live"] is False
    assert result["permission_escalation_performed"] is False
    assert result["hermes_permission_escalation_performed"] is False
    assert result["openclaw_permission_escalation_performed"] is False
    assert result["deep_filesystem_scan_performed"] is False
    assert result["secret_scanning_performed"] is False

    assert governance["agent_inventory"]["agent_name"] == "Codex"
    assert governance["permission_matrix"][0]["access_secrets"] is True
    assert governance["permission_matrix"][0]["browser_control"] is True
    assert governance["permission_matrix"][0]["send_messages"] is True
    assert governance["permission_matrix"][0]["publish_content"] is True
    assert governance["permission_matrix"][0]["mutate_canonical"] is True
    assert {finding["severity"] for finding in governance["risk_findings"]} >= {"critical", "high"}
    assert governance["approval_policy"]["applied_live"] is False
    assert {gate["action_type"] for gate in governance["approval_policy"]["required_gates"]} >= {
        "agent_policy_change",
        "runtime_execution",
        "send_email",
        "publish_content",
        "browser_action",
        "graph_promotion",
        "external_api_call",
    }
    assert governance["manifest_lint"]["status"] == "failed"
    assert {item["rule_id"] for item in governance["manifest_lint"]["findings"]} >= {
        "external_action_missing_approval",
        "browser_automation_without_scope",
        "canonical_promotion_without_review",
        "broad_filesystem_path",
    }
    assert len(governance["prompt_injection_tests"]) == 5
    assert all(test["executed_against_live_agent"] is False for test in governance["prompt_injection_tests"])

    assert {artifact.artifact_type for artifact in artifacts} >= {"report", "scorecard", "policy", "json"}
    assert {gate.action_type for gate in gates} >= {
        "agent_policy_change",
        "runtime_execution",
        "send_email",
        "publish_content",
        "browser_action",
        "graph_promotion",
        "external_api_call",
    }
    assert result["approval_check"]["blocked"] is True
    assert result["proof_card"]["status"] == "review_required"
    assert (tmp_path / result["proof_paths"]["proof_card_json_path"]).is_file()

    matrix_artifact = next(artifact for artifact in artifacts if artifact.title == "Permission Matrix")
    matrix_data = json.loads((tmp_path / matrix_artifact.local_path).read_text(encoding="utf-8"))
    assert matrix_data["schema"] == "workflow_packs.agent_governance.permission_matrix.v1"
    assert matrix_data["rows"][0]["agent"] == "Codex"

    run = store.get_run(run_id)
    audit_log = (tmp_path / run.audit_log_ref).read_text(encoding="utf-8")
    assert "agent_governance_inventory_ingested" in audit_log
    assert "agent_governance_matrix_generated" in audit_log
    assert "agent_governance_artifacts_created" in audit_log
    assert "agent_governance_approval_gates_created" in audit_log


def test_agent_governance_safe_defaults_do_not_apply_live_policy(tmp_path: Path) -> None:
    result = create_agent_governance_run(tmp_path)
    governance = result["agent_governance"]

    assert governance["agent_inventory"]["runtime"] == "manual_provider"
    assert governance["manifest_lint"]["status"] == "passed_with_review"
    assert governance["approval_policy"]["status"] == "draft_review_required"
    assert governance["safe_boundaries"]["operator_provided_inventory_only"] is True
    assert governance["safe_boundaries"]["policy_applied_live"] is False
    assert governance["safe_boundaries"]["deep_filesystem_scan_performed"] is False
    assert result["approval_check"]["blocked"] is True
