from __future__ import annotations

import json
from pathlib import Path

from runtime.workflow_packs.research_intelligence import create_research_intelligence_run
from runtime.workflow_packs.store import WorkflowPackStore


def test_research_intelligence_run_creates_sources_claims_decisions_export_gates_and_proof(tmp_path: Path) -> None:
    result = create_research_intelligence_run(
        tmp_path,
        title="Research scout",
        user_goal="Decide whether to build a source-to-feature engine",
        research_mode="feature integration",
        source_material=(
            "Founders are overloaded by AI tool launches and need evidence-based product decisions. "
            "A local markdown and JSON proof packet can make research decisions demoable. "
            "Browser scraping and repo cloning add security and license risk."
        ),
        source_urls="https://github.com/example/research-tool\nhttps://example.com/product-note",
        product_context="ChaseOS workflow packs and Source Intelligence Core",
        decision_goal="Adopt useful local foundations and defer risky external automation",
        audience="founders and developers",
        output_focus="implementation brief and R&D register export",
    )

    research = result["research_intelligence"]
    run_id = result["run"]["id"]
    store = WorkflowPackStore(tmp_path)
    artifacts = store.list_artifacts(run_id)
    gates = store.list_approval_gates(run_id)

    assert result["status"] == "research_intelligence_created"
    assert result["external_actions_performed"] is False
    assert result["web_scraping_performed"] is False
    assert result["github_api_calls_performed"] is False
    assert result["repo_cloning_performed"] is False
    assert result["graph_promotion_performed"] is False
    assert result["autonomous_implementation_performed"] is False
    assert len(result["run"]["source_refs"]) == 3
    assert {source["provenance_status"] for source in result["run"]["source_refs"]} == {"raw"}
    assert research["claims"]
    assert research["scorecard"]["items"]
    assert research["decisions"]
    assert all(item["evidence_quality_score"] >= 0 for item in research["scorecard"]["items"])
    assert all(item["product_relevance_score"] >= 0 for item in research["scorecard"]["items"])
    assert all(item["risk_score"] >= 0 for item in research["scorecard"]["items"])
    assert {decision["decision"] for decision in research["decisions"]} & {
        "adopt",
        "watchlist",
        "defer",
        "needs security review",
    }
    assert research["status_model"]["canonical_status"] == "not_promoted"
    assert research["rd_register_export"]["writeback_performed"] is False
    assert {artifact.artifact_type for artifact in artifacts} >= {"report", "scorecard", "brief", "json"}
    assert {gate.action_type for gate in gates} == {"graph_promotion", "runtime_execution"}
    assert result["approval_check"]["blocked"] is True
    assert result["proof_card"]["status"] == "review_required"
    assert (tmp_path / result["proof_paths"]["proof_card_json_path"]).is_file()

    rd_export = next(artifact for artifact in artifacts if artifact.title == "R&D Register Style Export")
    export_data = json.loads((tmp_path / rd_export.local_path).read_text(encoding="utf-8"))
    assert export_data["status"] == "draft_review_required"
    assert export_data["canonical_promotion_performed"] is False
    assert export_data["entries"]

    run = store.get_run(run_id)
    audit_log = (tmp_path / run.audit_log_ref).read_text(encoding="utf-8")
    assert "research_intelligence_intake_ingested" in audit_log
    assert "research_intelligence_claims_extracted" in audit_log
    assert "research_intelligence_artifacts_created" in audit_log
    assert "research_intelligence_approval_gates_created" in audit_log


def test_research_intelligence_uses_safe_defaults_when_source_material_is_empty(tmp_path: Path) -> None:
    result = create_research_intelligence_run(tmp_path, user_goal="Evaluate a technical repo idea")
    research = result["research_intelligence"]

    assert research["questionnaire"]["research_mode"] == "technical research"
    assert research["source_records"][0]["source_type"] == "manual_goal_note"
    assert research["source_records"][0]["provenance_status"] == "raw"
    assert research["claims"]
    assert research["safe_boundaries"]["source_records_are_raw_or_candidate"] is True
    assert research["safe_boundaries"]["forbidden_actions"] == [
        "browser_action",
        "external_api_call",
        "runtime_execution",
        "graph_promotion",
        "publish_content",
        "send_email",
    ]
