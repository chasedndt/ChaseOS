from __future__ import annotations

from pathlib import Path

import yaml  # type: ignore

from runtime.ventureops.evolution import build_workflow_evolution_proposal
from runtime.ventureops.mission_state import build_initial_mission_state
from runtime.ventureops.missions import build_mission_manifest
from runtime.ventureops.recommendations import build_mission_recommendations
from runtime.ventureops.site_profiles import build_site_profile_candidate
from runtime.ventureops.sub_agents import build_sub_agent_plan
from runtime.ventureops.validation import (
    validate_domain_goal_profile,
    validate_mission_manifest,
    validate_mission_recommendation,
    validate_mission_review,
    validate_mission_state,
    validate_schema_templates,
    validate_site_profile,
    validate_sub_agent_plan,
    validate_workflow_evolution_proposal,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_registry(root: Path) -> None:
    source_root = Path(__file__).resolve().parents[2]
    src = source_root / "runtime" / "workflows" / "registry" / "use_case_registry.yaml"
    dst = root / "runtime" / "workflows" / "registry" / "use_case_registry.yaml"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def test_mission_mode_schema_templates_validate_current_repo() -> None:
    root = Path(__file__).resolve().parents[2]

    schemas = validate_schema_templates(root)

    assert schemas["ok"], schemas["errors"]


def test_mission_manifest_defaults_to_approval_gated_evolution() -> None:
    manifest = build_mission_manifest(
        mission_id="mission-runtime-governance",
        name="Runtime Governance Mission",
        owner="operator",
        objective="Review runtime setups over repeated proof passes.",
        domain="runtime_governance",
        target_user="operator",
        workflow_packs=[{"workflow_id": "agent_runtime_governance_audit", "version": "0.1", "role": "primary"}],
        sub_agent_roles=["mission_supervisor", "security_reviewer", "critic_validator"],
    )

    validation = validate_mission_manifest(manifest)

    assert validation["ok"], validation["errors"]
    assert manifest["mission_mode"]["auto_apply_evolution"] is False
    assert manifest["evolution_policy"]["allow_auto_apply"] is False
    assert "workflow_evolution_activation" in manifest["approval_required_for"]


def test_sub_agent_plan_unknown_runtime_fails_closed() -> None:
    plan = build_sub_agent_plan("mission-test", roles=["mission_supervisor", "unknown_role"])

    validation = validate_sub_agent_plan(plan)

    assert validation["ok"] is False
    assert any("unknown runtime_preference" in error for error in validation["errors"])
    unknown = next(agent for agent in plan["sub_agents"] if agent["role"] == "unknown_role")
    assert unknown["authority"] == "blocked"


def test_mission_recommendations_sparse_workspace_gets_questions_not_hallucinated(tmp_path: Path) -> None:
    _seed_registry(tmp_path)
    _write(tmp_path / "note.md", "hello\n")

    result = build_mission_recommendations(tmp_path)

    assert result["status"] == "insufficient_evidence"
    assert result["mission_recommendations"] == []
    assert len(result["discovery_questions"]) >= 3


def test_mission_recommendations_are_evidence_backed_and_crypto_optional(tmp_path: Path) -> None:
    _seed_registry(tmp_path)
    _write(tmp_path / "00_HOME" / "Now.md", "TradeSync and StrikeZone trading analysis are active, but live trading is blocked.\n")
    _write(tmp_path / "Projects" / "Runtime.md", "Runtime agent permission Gate audit and MCP security proof artifacts.\n")

    result = build_mission_recommendations(tmp_path)
    recommendations = result["mission_recommendations"]

    assert recommendations
    assert result["crypto_trading_policy"]["live_trading_allowed"] is False
    ids = {item["recommended_workflow_packs"][0] for item in recommendations}
    assert "tradesync_strikezone_supply_engine" in ids
    for recommendation in recommendations:
        validation = validate_mission_recommendation(recommendation)
        assert validation["ok"], validation["errors"]
        assert recommendation["evidence_files"]
        assert recommendation["authority_boundary"]["runs_workflows"] is False


def test_non_crypto_mission_recommendations_do_not_add_trading(tmp_path: Path) -> None:
    _seed_registry(tmp_path)
    _write(tmp_path / "Dashboard.md", "Creator content, CTA reviews, newsletter funnel, local client proof cards.\n")

    result = build_mission_recommendations(tmp_path)
    ids = {item["recommended_workflow_packs"][0] for item in result["mission_recommendations"]}

    assert "creator_content_to_market_batch" in ids
    assert "tradesync_strikezone_supply_engine" not in ids


def test_workflow_evolution_requires_proof_and_scorecards_when_evidence_backed() -> None:
    proposal = build_workflow_evolution_proposal(
        proposal_id="evo-test-001",
        mission_id="mission-test",
        workflow_id="creator_content_to_market_batch",
        current_version="0.1",
        proposed_version="0.2",
        proposal_type="new_required_input",
        reason="Repeated mission reviews found missing CTA targets.",
        dry_run_plan="Require CTA target in dry-run for three passes.",
    )

    assert validate_workflow_evolution_proposal(proposal)["ok"] is True

    proposal["evidence_backed"] = True
    blocked = validate_workflow_evolution_proposal(proposal)
    assert blocked["ok"] is False
    assert any("proof_cards and scorecards" in error for error in blocked["errors"])

    proposal["evidence"] = {
        "proof_cards": ["07_LOGS/Workflow-Proofs/proof.md"],
        "run_logs": ["07_LOGS/Agent-Activity/run.md"],
        "scorecards": ["07_LOGS/Workflow-Proofs/scorecard.json"],
        "source_files": ["00_HOME/Now.md"],
    }
    proposal["status"] = "pending_review"
    assert validate_workflow_evolution_proposal(proposal)["ok"] is True

    proposal["review_runtime"] = "weak_model"
    weak = validate_workflow_evolution_proposal(proposal)
    assert weak["ok"] is False
    assert any("weak-provider" in error for error in weak["errors"])


def test_site_profile_browser_learning_is_candidate_only() -> None:
    profile = build_site_profile_candidate(
        site_name="Example Marketplace",
        domain="example.com",
        purpose="Draft marketplace listing research observations.",
        workflow_use_cases=["listing_pricing_review"],
    )

    validation = validate_site_profile(profile)

    assert validation["ok"], validation["errors"]
    assert profile["status"] == "candidate"
    assert profile["browser_skill_activation_allowed"] is False

    profile["browser_skill_activation_allowed"] = True
    blocked = validate_site_profile(profile)
    assert blocked["ok"] is False
    assert any("activate browser skills" in error for error in blocked["errors"])


def test_domain_goal_profile_and_mission_state_validate() -> None:
    profile = {
        "domain": "crypto_trading",
        "user_goal": "Review trading plans in paper mode.",
        "current_assets": ["trade journal"],
        "current_constraints": ["no live exchange access"],
        "preferred_tools": ["markdown scan"],
        "forbidden_tools": ["live execution", "exchange order placement"],
        "risk_tolerance": "low",
        "approval_preferences": ["human-approved execution only"],
        "success_metrics": ["risk review completed"],
        "available_capital": "none for automation",
        "available_time": "operator-defined",
        "current_workflows": ["paper review"],
        "known_strategies": [],
        "known_failure_patterns": [],
        "recommended_workflow_packs": ["tradesync_strikezone_supply_engine"],
        "missing_context": [],
        "readiness_level": "needs_approval_policy",
    }
    state = build_initial_mission_state(mission_id="mission-test")

    assert validate_domain_goal_profile(profile)["ok"] is True
    assert validate_mission_state(state)["ok"] is True
    assert state["authority_boundary"]["does_not_replace_project_truth"] is True


def test_mission_review_requires_approvals_for_proposed_changes() -> None:
    review = {
        "mission_id": "mission-test",
        "review_id": "review-001",
        "period": "2026-05-13",
        "runs_reviewed": ["run-001"],
        "proof_cards": ["proof.md"],
        "scorecards": ["scorecard.json"],
        "what_worked": ["proof artifact was produced"],
        "what_failed": [],
        "repeated_patterns": ["missing CTA target"],
        "proposed_changes": ["require CTA target"],
        "approvals_needed": [],
        "next_pass": "draft evolution proposal",
    }

    blocked = validate_mission_review(review)
    assert blocked["ok"] is False
    assert any("approvals_needed" in error for error in blocked["errors"])
    review["approvals_needed"] = ["workflow_evolution_activation"]
    assert validate_mission_review(review)["ok"] is True


def test_example_mission_manifests_validate() -> None:
    root = Path(__file__).resolve().parents[2]
    examples = sorted((root / "runtime" / "ventureops" / "examples" / "mission_manifests").glob("*.yaml"))

    assert examples
    for path in examples:
        manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
        validation = validate_mission_manifest(manifest)
        assert validation["ok"], (path.name, validation["errors"])
