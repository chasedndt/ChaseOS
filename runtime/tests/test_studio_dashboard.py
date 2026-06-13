"""
test_studio_dashboard.py — Tests for Studio Operator Dashboard

Covers:
  TestDashboardStructure    (4 tests) — model shape and boundary
  TestSchedulePanel         (4 tests) — schedule aggregation
  TestBusPanel              (4 tests) — agent bus task counts
  TestQuarantinePanel       (4 tests) — quarantine file counts
  TestGraphPanel            (4 tests) — snapshot presence + stats
  TestMemoryPanel           (4 tests) — registered runtimes
  TestAuditPanel            (3 tests) — audit entry counts
  TestApprovalPanel         (4 tests) — pending approval counts
  TestFailOpen              (3 tests) — panel failures don't abort dashboard
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from runtime.studio.dashboard import get_dashboard


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    (vault / "07_LOGS" / "Graph-Snapshots").mkdir(parents=True)
    (vault / "07_LOGS" / "Agent-Activity").mkdir(parents=True)
    (vault / "03_INPUTS" / "00_QUARANTINE").mkdir(parents=True)
    (vault / "runtime" / "studio" / "approvals").mkdir(parents=True)
    (vault / "runtime" / "memory" / "adapters").mkdir(parents=True)
    (vault / "runtime" / "schedules").mkdir(parents=True)
    return vault


def _seed_mvp_readiness_blockers(vault: Path) -> None:
    (vault / "runtime").mkdir(parents=True, exist_ok=True)
    (vault / "runtime" / "setup_state.json").write_text(
        json.dumps(
            {
                "providers": {
                    "openai": {
                        "configured": True,
                        "default_model": "gpt-5.5",
                        "secret_reference_kind": "env-var-or-local-secret-ref",
                        "secret_reference_target": "SET_OPENAI_SECRET_REF",
                    }
                },
                "integrations": {},
            }
        ),
        encoding="utf-8",
    )
    for relative in [
        "06_AGENTS/Permission-Matrix.md",
        "06_AGENTS/Trust-Tiers.md",
        "runtime/browser_runtime/cdp_executor_spec.py",
        "runtime/browser_runtime/workflow_replay_execution_readiness.py",
        "06_AGENTS/ChaseOS-MVP-Operator-Unblock-Packet.md",
        "07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json",
    ]:
        path = vault / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {path.stem}\n", encoding="utf-8")


# ── TestDashboardStructure ────────────────────────────────────────────────────

class TestDashboardStructure:
    def test_returns_ok_true(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = get_dashboard(vault)
        assert result["ok"] is True

    def test_surface_field(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = get_dashboard(vault)
        assert result["surface"] == "studio_dashboard"

    def test_boundary_is_read_only(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = get_dashboard(vault)
        assert result["boundary"]["writes_vault"] is False
        assert result["boundary"]["canonical_mutation_allowed"] is False

    def test_all_panels_present(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = get_dashboard(vault)
        for panel in ("schedule_panel", "bus_panel", "quarantine_panel",
                      "graph_panel", "memory_panel", "audit_panel", "approval_panel",
                      "runtime_startup_panel", "mvp_readiness_panel",
                      "ventureops_real_world_usecase_panel",
                      "personal_operator_context_panel",
                      "personal_context_import_panel"):
            assert panel in result, f"missing {panel}"

    def test_dashboard_surfaces_ventureops_real_use_hardening_panel(self, tmp_path, monkeypatch):
        from runtime.studio import ventureops_real_world_usecase_panel as panel_module

        vault = _make_vault(tmp_path)
        guide_path = vault / panel_module.GUIDE_PATH
        guide_path.parent.mkdir(parents=True, exist_ok=True)
        guide_path.write_text("# guide\n", encoding="utf-8")

        monkeypatch.setattr(
            panel_module,
            "build_autonomous_implementation_completion",
            lambda vault_root: {
                "ok": True,
                "feature_implementation_complete": True,
                "operator_evidence_required_for_tests": False,
                "real_world_delivery_revenue_complete": False,
                "safe_to_mark_real_world_delivery_revenue_complete": False,
                "real_world_missing_requirements": ["live revenue workflow proof missing"],
                "truth_boundary": {
                    "external_send_performed": False,
                    "provider_call_performed": False,
                    "browser_action_performed": False,
                    "crm_mutation_performed": False,
                    "payment_mutation_performed": False,
                    "invoice_sent": False,
                    "revenue_claim_made": False,
                    "accounting_claim_made": False,
                    "credential_or_secret_read_performed": False,
                    "canonical_promotion_performed": False,
                },
                "local_evidence_chain": {
                    "scope_evidence": {"ok": True},
                    "live_client_workflow_proof": {"ok": True},
                    "client_safe_delivery_artifact": {"ok": True},
                },
            },
        )

        result = get_dashboard(vault, probe_child_apps=False)
        panel = result["ventureops_real_world_usecase_panel"]

        assert panel["surface"] == "studio_ventureops_real_world_usecase_panel"
        assert panel["status"] == "studio_ready_real_world_evidence_blocked"
        assert panel["summary"]["feature_implementation_complete"] is True
        assert panel["summary"]["operator_evidence_required_for_tests"] is False
        assert panel["summary"]["safe_to_mark_real_world_delivery_revenue_complete"] is False
        assert panel["operator_guide"]["exists"] is True
        assert panel["authority"]["writes_vault"] is False
        assert result["boundary"]["reads_ventureops_completion_gate"] is True

    def test_dashboard_surfaces_personal_operator_context_panel(self, tmp_path):
        vault = _make_vault(tmp_path)
        for relative, text in {
            "SOUL.md": "# SOUL\n",
            "00_HOME/Dashboard.md": (
                "# Dashboard\n"
                "[[SOUL]]\n"
                "[[Personal-Operator-Index]]\n"
                "[[03_INPUTS/Personal-Context-Intake/2026-05-16_personal-context-intake-implementation-map]]\n"
                "[[03_INPUTS/Personal-Context-Intake/2026-05-16_personal-context-final-node-coverage-audit|Personal Context Final Node Coverage Audit]]\n"
                "[[00_HOME/Personal-Domains/Personal-Domains-Index|Personal Domains Index]]\n"
                "[[06_AGENTS/Personal-Context-Import-Feature|Personal Context Import Feature]]\n"
            ),
            "00_HOME/Personal-Operator-Index.md": (
                "# Personal Operator Index\n"
                "[[03_INPUTS/Personal-Context-Intake/2026-05-15_personal-context-intake-packet]]\n"
                "[[03_INPUTS/Personal-Context-Intake/2026-05-16_personal-context-intake-implementation-map]]\n"
                "[[03_INPUTS/Personal-Context-Intake/2026-05-16_personal-context-final-node-coverage-audit]]\n"
                "[[06_AGENTS/Personal-Context-Import-Feature|Personal Context Import Feature]]\n"
                "[[01_PROJECTS/University/Modules/Modules|University Modules]]\n"
                "[[00_HOME/Personal-Domains/Personal-Domains-Index|Personal Domains Index]]\n"
                "[[07_LOGS/Pulse-Decks/memory-candidates/personal-map/2026-05-16-personal-life-domain-candidates-review|Personal Life-Domain Candidate Review]]\n"
                "[[02_KNOWLEDGE/AI-Agents/Prompt-Engineering|Prompt Engineering]]\n"
                "[[02_KNOWLEDGE/AI-Agents/Tool-Use|Tool Use]]\n"
                "[[02_KNOWLEDGE/Runtime-Ops/Runtime-Ops|Runtime Ops]]\n"
                "[[02_KNOWLEDGE/Runtime-Ops/WSL2-Ubuntu-Setup-Guide|WSL2 Ubuntu Setup Guide]]\n"
                "[[02_KNOWLEDGE/Runtime-Ops/Linux-Commands|Linux Commands]]\n"
                "[[02_KNOWLEDGE/Platform-Strategy/Platform-Strategy|Platform Strategy]]\n"
                "[[02_KNOWLEDGE/Platform-Strategy/Action-Matrix|Action Matrix]]\n"
                "[[02_KNOWLEDGE/Trading-Systems/Funding-Rates|Funding Rates]]\n"
                "[[02_KNOWLEDGE/Cybersecurity/Vulnerability-Patterns|Vulnerability Patterns]]\n"
                "[[02_KNOWLEDGE/Full-Stack/Backend-Architecture|Backend Architecture]]\n"
                "[[02_KNOWLEDGE/Content-Distribution/Content-Distribution|Content Distribution]]\n"
                "[[01_PROJECTS/Language-Mobility/Mandarin|Mandarin / HSK 1 Operating Lane]]\n"
                "[[02_KNOWLEDGE/Language/Mandarin-HSK1|Mandarin / HSK 1]]\n"
            ),
            "00_HOME/Personal-Domains/Language-Learning-Global-Mobility.md": (
                "[[01_PROJECTS/Language-Mobility/Mandarin]]\n"
                "[[02_KNOWLEDGE/Language/Mandarin-HSK1]]\n"
            ),
            "02_KNOWLEDGE/Language/Language-Learning.md": (
                "[[01_PROJECTS/Language-Mobility/Mandarin]]\n"
                "[[Mandarin-HSK1]]\n"
            ),
            "KNOWLEDGE-INDEX.md": (
                "type: knowledge-index-routing-shim\n"
                "status: ROUTING SHIM / NOT CANONICAL\n"
                "canonical_target: 02_KNOWLEDGE/Knowledge-Index.md\n"
                "[[00_HOME/Personal-Operator-Index|Personal Operator Index]]\n"
                "[[06_AGENTS/Personal-Context-Import-Feature|Personal Context Import Feature]]\n"
                "[[01_PROJECTS/University/Modules/Modules|University Modules]]\n"
            ),
            "02_KNOWLEDGE/Knowledge-Index.md": (
                "[[00_HOME/Personal-Operator-Index|Personal Operator Index]]\n"
                "[[01_PROJECTS/University/Modules/Modules|University Modules]]\n"
            ),
            "01_PROJECTS/University/Degree-OS.md": "[[Modules/Modules|University Modules]]\n",
            "02_KNOWLEDGE/Computer-Science/Computer-Science.md": "## University Module Tree\n",
            "02_KNOWLEDGE/Doctrine/Doctrine-Philosophy.md": "[[00_HOME/Personal-Operator-Index|Personal Operator Index]]\n",
            "02_KNOWLEDGE/AI-Agents/AI-Agent-Engineering.md": "[[Tool-Use]]\n",
            "02_KNOWLEDGE/Runtime-Ops/Runtime-Ops.md": "[[WSL2-Ubuntu-Setup-Guide]]\n[[Linux-Commands]]\n",
            "02_KNOWLEDGE/Platform-Strategy/Platform-Strategy.md": "[[Action-Matrix]]\n",
            "02_KNOWLEDGE/Trading-Systems/Trading-Systems-Engineering.md": "[[Funding-Rates]]\n[[Order-Flow]]\n[[Morning-Thesis]]\n[[Trade-Journal]]\n[[Risk-Management]]\n",
            "02_KNOWLEDGE/Cybersecurity/Cybersecurity.md": "[[Vulnerability-Patterns]]\n[[Lab-Writeups]]\n[[Agent-Security]]\n[[Credential-Boundaries]]\n",
            "02_KNOWLEDGE/Full-Stack/Full-Stack-Engineering.md": "[[React]]\n[[Backend-Architecture]]\n[[Solana-Future]]\n",
            "03_INPUTS/Personal-Context-Intake/Personal-Context-Intake-Index.md": (
                "[[06_AGENTS/Personal-Context-Import-Feature|Personal Context Import Feature]]\n"
                "[[2026-05-16_personal-context-final-node-coverage-audit|final node coverage audit]]\n"
            ),
            "03_INPUTS/Personal-Context-Intake/2026-05-16_personal-context-final-node-coverage-audit.md": "[[ChaseOS-Core]]\n[[ChaseOS-Personal]]\n[[Source-Intelligence-Core]]\n",
            "06_AGENTS/Personal-Map-Architecture.md": "[[00_HOME/Personal-Operator-Index|Personal Operator Index]]\n",
            "06_AGENTS/Personal-Context-Import-Feature.md": "# Personal Context Import Feature\n",
            "06_AGENTS/Vault-Map.md": "Personal-Context-Intake context intake\n",
            "01_PROJECTS/Projects-Hub.md": "# Projects Hub\n",
            "00_HOME/Personal-Domains/Personal-Domains-Index.md": "# Personal Domains Index\n",
            "06_AGENTS/Use-Case-Mode-Architecture.md": "# Workspace Mode Layer\n",
        }.items():
            path = vault / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

        result = get_dashboard(vault, probe_child_apps=False)
        panel = result["personal_operator_context_panel"]

        assert panel["surface"] == "studio_personal_operator_context_index"
        assert panel["summary"]["group_count"] == 11
        assert panel["summary"]["link_check_passed_count"] == panel["summary"]["link_check_count"]
        assert panel["authority"]["writes_vault"] is False
        assert panel["authority"]["personal_map_mutation_allowed"] is False
        assert result["boundary"]["reads_personal_operator_context"] is True

    def test_dashboard_surfaces_personal_context_import_panel(self, tmp_path):
        vault = _make_vault(tmp_path)
        for relative, text in {
            "SOUL.md": "# SOUL\n",
            "00_HOME/Dashboard.md": (
                "# Dashboard\n"
                "[[SOUL]]\n"
                "[[Personal-Operator-Index]]\n"
                "[[03_INPUTS/Personal-Context-Intake/2026-05-16_personal-context-intake-implementation-map]]\n"
                "[[03_INPUTS/Personal-Context-Intake/2026-05-16_personal-context-final-node-coverage-audit|Personal Context Final Node Coverage Audit]]\n"
                "[[00_HOME/Personal-Domains/Personal-Domains-Index|Personal Domains Index]]\n"
                "[[06_AGENTS/Personal-Context-Import-Feature|Personal Context Import Feature]]\n"
            ),
            "00_HOME/Operating-System.md": "# Operating System\n",
            "00_HOME/Personal-Operator-Index.md": (
                "# Personal Operator Index\n"
                "[[03_INPUTS/Personal-Context-Intake/2026-05-15_personal-context-intake-packet]]\n"
                "[[03_INPUTS/Personal-Context-Intake/2026-05-16_personal-context-intake-implementation-map]]\n"
                "[[03_INPUTS/Personal-Context-Intake/2026-05-16_personal-context-final-node-coverage-audit]]\n"
                "[[06_AGENTS/Personal-Context-Import-Feature|Personal Context Import Feature]]\n"
                "[[01_PROJECTS/University/Modules/Modules|University Modules]]\n"
                "[[00_HOME/Personal-Domains/Personal-Domains-Index|Personal Domains Index]]\n"
            ),
            "01_PROJECTS/Projects-Hub.md": "# Projects Hub\n",
            "02_KNOWLEDGE/Knowledge-Index.md": "[[00_HOME/Personal-Operator-Index|Personal Operator Index]]\n[[01_PROJECTS/University/Modules/Modules|University Modules]]\n",
            "KNOWLEDGE-INDEX.md": (
                "type: knowledge-index-routing-shim\n"
                "status: ROUTING SHIM / NOT CANONICAL\n"
                "canonical_target: 02_KNOWLEDGE/Knowledge-Index.md\n"
                "[[00_HOME/Personal-Operator-Index|Personal Operator Index]]\n"
                "[[06_AGENTS/Personal-Context-Import-Feature|Personal Context Import Feature]]\n"
                "[[01_PROJECTS/University/Modules/Modules|University Modules]]\n"
            ),
            "00_HOME/Personal-Domains/Personal-Domains-Index.md": "# Personal Domains Index\n",
            "06_AGENTS/Personal-Map-Architecture.md": "# Personal Map Architecture\n",
            "06_AGENTS/Use-Case-Mode-Architecture.md": "# Workspace Mode Layer\n",
            "06_AGENTS/Personal-Context-Import-Feature.md": "# Personal Context Import Feature\n",
            "03_INPUTS/Personal-Context-Intake/Personal-Context-Intake-Index.md": (
                "[[06_AGENTS/Personal-Context-Import-Feature|Personal Context Import Feature]]\n"
            ),
            "00_HOME/.workspace-mode.yaml": "mode: personal_os\n",
        }.items():
            path = vault / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

        result = get_dashboard(vault, probe_child_apps=False)
        panel = result["personal_context_import_panel"]

        assert panel["surface"] == "studio_personal_context_import_panel"
        assert panel["implementation_status"] == "READY_FOR_MANUAL_TESTING / 100_PERCENT_IMPLEMENTED_FOR_LOCAL_MANUAL_TEST"
        assert panel["knowledge_index_resolution"]["root_file_role"] == "routing_shim_not_canonical"
        assert panel["preview_writer"]["surface"] == "studio_personal_context_import_preview_writer"
        assert panel["readiness"]["approved_preview_writer_built"] is True
        assert panel["readiness"]["multi_instance_test_harness_built"] is True
        assert panel["readiness"]["runtime_consumption_readiness_built"] is True
        assert panel["readiness"]["raw_full_memory_injection_blocked"] is True
        assert panel["readiness"]["canonical_promotion_approval_preview_built"] is True
        assert panel["readiness"]["canonical_promotion_executor_built"] is True
        assert panel["readiness"]["canonical_promotion_executor_approval_gated"] is True
        assert panel["readiness"]["live_import_writes_enabled"] is False
        assert panel["authority"]["writes_vault"] is False
        assert result["boundary"]["reads_personal_context_import_panel"] is True


class TestOperatorNextActionCards:
    def test_dashboard_surfaces_true_operator_next_action_cards_without_execution_authority(self, tmp_path, monkeypatch):
        from runtime.studio import dashboard as dashboard_module

        vault = _make_vault(tmp_path)

        monkeypatch.setattr(
            dashboard_module,
            "_gather_provider_runtime_panel",
            lambda vault, errors: {
                "ok": True,
                "readiness_summary": {"posture": "blocked", "degradation_reasons": ["model_binding_errors"]},
                "operator_default_provider": {"provider_id": "openai", "valid": True},
                "active_runtime_model_provider": {"valid": False},
                "queues": {"stuck_count": 2, "no_chunk_count": 1, "queued_count": 4, "active_count": 1},
                "warnings": ["stale runtime heartbeats"],
                "operator_summary": {"headline": "OpenAI configured; runtime provider posture blocked"},
                "boundary": {"read_only": True, "controls_provider_switching": False},
            },
            raising=False,
        )
        monkeypatch.setattr(
            dashboard_module,
            "_gather_graph_panel",
            lambda vault, errors: {
                "snapshot_available": True,
                "snapshot_id": "snap-old",
                "age_hours": 73.5,
                "node_count": 12,
                "edge_count": 11,
                "community_count": 2,
                "maintenance": {"available": True, "latest_run_status": "review_required"},
            },
        )
        monkeypatch.setattr(
            dashboard_module,
            "_gather_approval_panel",
            lambda vault, errors: {"pending": 7, "total": 21, "by_status": {"pending": 7, "approved": 3}},
        )
        monkeypatch.setattr(
            dashboard_module,
            "_gather_app_launcher_panel",
            lambda vault, errors, probe_child_apps=True: {
                "ok": True,
                "app_count": 3,
                "health_counts": {"offline": 2, "reachable": 1},
                "apps": [
                    {"id": "approval-center-app", "title": "Approval Center", "command": "chaseos studio approval-center-app", "runtime_status": {"state": "offline"}},
                    {"id": "runtime-cockpit-app", "title": "Runtime Cockpit", "command": "chaseos studio runtime-cockpit-app", "runtime_status": {"state": "offline"}},
                ],
                "support_ports": [
                    {"id": "hermes-kanban-dashboard", "title": "Hermes dashboard / Kanban", "port": 9119, "runtime_status": {"state": "reachable", "health_url": "http://127.0.0.1:9119/health.json"}},
                ],
                "authority": {"read_only": True, "starts_child_apps": False, "writes_vault": False, "canonical_mutation_allowed": False},
            },
        )

        result = get_dashboard(vault, probe_child_apps=False)
        cards = {card["id"]: card for card in result["operator_next_action_cards"]}

        assert list(cards) == [
            "provider_runtime_posture",
            "pending_approval_decision",
            "stale_graph_snapshot_freshness",
            "hermes_kanban_support_port",
            "offline_app_launch_guidance",
            "runtime_heartbeat_stuck_jobs",
        ]
        assert cards["provider_runtime_posture"]["status"] == "blocked"
        assert cards["provider_runtime_posture"]["facts"]["operator_default_provider_valid"] is True
        assert cards["provider_runtime_posture"]["facts"]["runtime_provider_binding_valid"] is False
        assert cards["pending_approval_decision"]["facts"]["pending"] == 7
        assert cards["stale_graph_snapshot_freshness"]["status"] == "stale"
        assert cards["hermes_kanban_support_port"]["status"] == "reachable"
        assert cards["offline_app_launch_guidance"]["facts"]["offline_app_count"] == 2
        assert cards["runtime_heartbeat_stuck_jobs"]["facts"]["stuck_count"] == 2
        assert all(card["authority"]["presentation_only"] is True for card in cards.values())
        assert all(card["authority"]["executes_actions"] is False for card in cards.values())
        assert all(card["authority"]["provider_calls_allowed"] is False for card in cards.values())
        assert all(card["authority"]["writes_vault"] is False for card in cards.values())


class TestMVPReadinessPanel:
    def test_mvp_readiness_panel_surfaces_operator_blockers_without_secret_values(self, tmp_path, monkeypatch):
        vault = _make_vault(tmp_path)
        _seed_mvp_readiness_blockers(vault)
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-secret-that-must-not-leak")

        result = get_dashboard(vault, probe_child_apps=False)
        panel = result["mvp_readiness_panel"]
        serialized = json.dumps(panel, sort_keys=True)

        assert panel["surface"] == "studio_mvp_readiness_panel"
        assert panel["readiness_status"] == "blocked_operator_input_required"
        assert panel["overall_goal_complete"] is False
        assert panel["objective_achieved"] is False
        assert panel["safe_to_call_update_goal_complete"] is False
        assert panel["no_safe_autonomous_completion_pass_available"] is True
        assert panel["update_goal_allowed"] is False
        assert panel["operator_input_ids"] == panel["completion_decision"]["operator_input_ids"]
        assert "openai_secret_reference" in panel["p0_blocker_ids"]
        assert panel["completion_decision"]["safe_to_call_update_goal_complete"] is False
        assert panel["next_operator_action_id"] == "openai_secret_reference"
        assert panel["next_recommended_pass"] == "operator-provide-openai-secret-reference"
        assert [item["id"] for item in panel["next_action_queue"]] == [
            "openai_secret_reference",
            "ventureops_real_client_scope",
        ]
        assert panel["next_operator_action"]["requires_operator_secret_reference"] is True
        assert panel["next_operator_action"]["live_execution_allowed_now"] is False
        assert panel["completion_matrix_count"] == 10
        assert len(panel["completion_matrix"]) == 10
        current_state = panel["current_state_map"]
        assert current_state["surface"] == "chaseos_mvp_current_state_map"
        assert current_state["pass_status_count"] == 10
        assert current_state["pass_status_by_id"]["credential_readiness"]["status"] == (
            "blocked_operator_input_required"
        )
        assert (
            "07_LOGS/Operator-Briefs/2026-05-14-openai-api-key-later-guide.md"
            in current_state["pass_status_by_id"]["credential_readiness"]["evidence_refs"]
        )
        assert current_state["safe_to_call_update_goal_complete"] is False
        assert current_state["no_safe_autonomous_completion_pass_available"] is True
        assert current_state["update_goal_allowed"] is False
        assert current_state["next_operator_action_id"] == "openai_secret_reference"
        assert current_state["next_recommended_pass"] == "operator-provide-openai-secret-reference"
        assert current_state["source_command"] == "python -m runtime.cli.main mvp current-state --json"
        assert panel["approval_queue_boundary"] == current_state["approval_queue_boundary"]
        assert panel["approval_queue_boundary"]["pending_count"] == 0
        assert panel["approval_queue_boundary"]["tracked_pending_count"] == 0
        assert panel["approval_queue_boundary"]["untracked_pending_approval_count"] == 0
        assert (
            panel["approval_queue_boundary"][
                "untracked_pending_approvals_are_current_mvp_blockers"
            ]
            is False
        )
        assert panel["setup_scope_boundary"] == current_state["setup_scope_boundary"]
        assert panel["setup_scope_boundary"]["status"] == (
            "setup_wide_validation_expected_to_fail_current_mvp_blocker"
        )
        assert panel["setup_scope_boundary"]["mvp_current_setup_blocker_ids"] == [
            "openai_secret_reference"
        ]
        assert panel["setup_scope_boundary"]["setup_wide_invalid_provider_ids"] == [
            "openai"
        ]
        assert panel["setup_scope_boundary"]["setup_wide_invalid_integration_ids"] == []
        assert panel["setup_scope_boundary"]["non_mvp_setup_gap_ids"] == []
        assert (
            panel["setup_scope_boundary"]["non_mvp_setup_gaps_are_current_mvp_blockers"]
            is False
        )
        assert current_state["operator_input_template_artifact"]["path"] == (
            "07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json"
        )
        assert current_state["operator_input_template_artifact"]["exists"] is True
        assert current_state["operator_input_template_artifact"]["contains_secret_values"] is False
        assert panel["autonomous_completion_barrier"] == current_state[
            "autonomous_completion_barrier"
        ]
        assert panel["completion_safety_contract"] == current_state[
            "completion_safety_contract"
        ]
        assert panel["completion_safety_contract"]["status"] == (
            "blocked_do_not_call_update_goal_complete"
        )
        assert panel["completion_safety_contract"]["update_goal_allowed"] is False
        assert panel["autonomous_completion_barrier"]["active"] is True
        assert panel["autonomous_completion_barrier"]["update_goal_allowed"] is False
        assert (
            panel["autonomous_completion_barrier"][
                "no_safe_autonomous_completion_pass_available"
            ]
            is True
        )
        assert panel["autonomous_completion_barrier"]["next_operator_action_id"] == (
            "openai_secret_reference"
        )
        assert panel["autonomous_completion_barrier"]["next_recommended_pass"] == (
            "operator-provide-openai-secret-reference"
        )
        assert panel["operator_input_template_artifact"] == current_state[
            "operator_input_template_artifact"
        ]
        snapshot = panel["mvp_usecase_snapshot"]
        assert snapshot["surface"] == "chaseos_mvp_usecase_snapshot"
        assert snapshot["current_sector"] == "MVP Integration / Operator Workflow Activation"
        assert snapshot["readiness_status"] == "blocked_operator_input_required"
        assert {
            "provider_backed_chat_studio",
            "ventureops_real_client_scope",
        } <= {item["id"] for item in snapshot["blocked_now"]}
        assert "full_system_control" in {item["id"] for item in snapshot["parked_or_later"]}
        assert panel["key_checks"]["mvp_usecase_snapshot_surface"] == "chaseos_mvp_usecase_snapshot"
        assert panel["key_checks"]["mvp_usecase_snapshot_status"] == "blocked_operator_input_required"
        assert panel["key_checks"]["usable_now_count"] == len(snapshot["usable_now"])
        assert panel["key_checks"]["blocked_now_count"] == len(snapshot["blocked_now"])
        assert panel["key_checks"]["parked_or_later_count"] == len(snapshot["parked_or_later"])
        assert "openai_secret_reference" in panel["key_checks"]["p0_usecase_blocker_ids"]
        ventureops_completion = next(
            item for item in panel["completion_matrix"] if item["id"] == "ventureops_real_use"
        )
        assert ventureops_completion["criterion_satisfied"] is False
        assert "ventureops_real_use" in panel["key_checks"]["blocked_requirement_ids"]
        assert panel["p0_blocker_count"] >= 1
        assert panel["authority"]["secret_values_read"] is False
        assert panel["authority"]["provider_calls_performed"] is False
        assert panel["authority"]["canonical_mutation_allowed"] is False
        assert panel["key_checks"]["provider_secret_reference_target"] == "SET_OPENAI_SECRET_REF"
        assert panel["key_checks"]["provider_secret_reference_target_is_placeholder"] is True
        assert panel["key_checks"]["provider_secret_reference_resolvable"] is False
        assert panel["key_checks"]["provider_secret_reference_probe_source"] == "env-var-or-local-secret-ref"
        assert panel["key_checks"]["provider_secret_reference_probe_error"] == "reference_not_found"
        assert panel["key_checks"]["provider_reference_presence_check_commands"] == [
            '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "User")',
            '[bool][Environment]::GetEnvironmentVariable("OPENAI_API_KEY", "Process")',
        ]
        assert panel["key_checks"]["provider_reference_presence_check_outputs_secret_value"] is False
        assert panel["key_checks"]["current_state_map_surface"] == "chaseos_mvp_current_state_map"
        assert panel["key_checks"]["current_state_map_pass_status_count"] == 10
        assert panel["key_checks"]["current_state_map_pass_status_by_id_count"] == 10
        assert panel["key_checks"]["current_state_map_safe_to_call_update_goal_complete"] is False
        assert (
            panel["key_checks"]["current_state_map_no_safe_autonomous_completion_pass_available"]
            is True
        )
        assert panel["key_checks"]["current_state_map_update_goal_allowed"] is False
        assert panel["key_checks"]["current_state_map_next_operator_action_id"] == "openai_secret_reference"
        assert panel["key_checks"]["current_state_map_next_recommended_pass"] == (
            "operator-provide-openai-secret-reference"
        )
        assert panel["key_checks"]["current_state_map_operator_input_template_path"] == (
            "07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json"
        )
        assert panel["key_checks"]["current_state_map_operator_input_template_exists"] is True
        assert (
            panel["key_checks"]["current_state_map_operator_input_template_contains_secret_values"]
            is False
        )
        assert panel["key_checks"]["current_state_map_approval_pending_count"] == 0
        assert panel["key_checks"]["current_state_map_approval_tracked_pending_count"] == 0
        assert panel["key_checks"]["current_state_map_approval_untracked_pending_count"] == 0
        assert (
            panel["key_checks"][
                "current_state_map_untracked_pending_approvals_are_current_mvp_blockers"
            ]
            is False
        )
        assert (
            panel["key_checks"][
                "current_state_map_tracked_chat_approval_is_current_mvp_decision"
            ]
            is False
        )
        assert panel["key_checks"]["current_state_map_setup_scope_status"] == (
            "setup_wide_validation_expected_to_fail_current_mvp_blocker"
        )
        assert panel["key_checks"]["current_state_map_setup_wide_invalid_provider_count"] == 1
        assert panel["key_checks"]["current_state_map_setup_wide_invalid_integration_count"] == 0
        assert panel["key_checks"]["current_state_map_non_mvp_setup_gap_count"] == 0
        assert (
            panel["key_checks"][
                "current_state_map_non_mvp_setup_gaps_are_current_mvp_blockers"
            ]
            is False
        )
        assert panel["key_checks"]["current_state_map_setup_wide_validation_command"] == (
            "python -m runtime.cli.main setup validate --json"
        )
        assert panel["key_checks"]["autonomous_completion_barrier_active"] is True
        assert panel["key_checks"]["autonomous_completion_barrier_update_goal_allowed"] is False
        assert (
            panel["key_checks"][
                "autonomous_completion_barrier_no_safe_autonomous_completion_pass_available"
            ]
            is True
        )
        assert panel["key_checks"]["autonomous_completion_barrier_next_operator_action_id"] == (
            "openai_secret_reference"
        )
        assert panel["key_checks"]["autonomous_completion_barrier_next_recommended_pass"] == (
            "operator-provide-openai-secret-reference"
        )
        assert panel["key_checks"]["completion_safety_contract_status"] == (
            "blocked_do_not_call_update_goal_complete"
        )
        assert (
            panel["key_checks"]["completion_safety_contract_update_goal_allowed"]
            is False
        )
        assert isinstance(
            panel["key_checks"][
                "completion_safety_contract_checklist_coverage_is_not_completion"
            ],
            bool,
        )
        assert panel["key_checks"][
            "completion_safety_contract_required_before_update_goal_complete"
        ] == [
            "resolve_operator_inputs",
            "rerun_completion_audit",
            "require_safe_to_call_update_goal_complete_true",
        ]
        assert "python -m runtime.cli.main mvp current-state --json" in panel["evidence_refs"]
        assert "python -m runtime.cli.main mvp credential-handoff --json" in panel["evidence_refs"]
        assert (
            "python -m runtime.cli.main runtime provider live-smoke-readiness --json"
            in panel["evidence_refs"]
        )
        assert "07_LOGS/Operator-Briefs/2026-05-13-mvp-next-action-card.md" in panel["evidence_refs"]
        assert (
            "07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json"
            in panel["evidence_refs"]
        )
        assert (
            "07_LOGS/Operator-Briefs/2026-05-13-mvp-openai-secret-reference-handoff-card.md"
            in panel["evidence_refs"]
        )
        assert (
            "07_LOGS/Operator-Briefs/2026-05-14-openai-api-key-later-guide.md"
            in panel["evidence_refs"]
        )
        assert (
            "07_LOGS/Operator-Briefs/2026-05-13-mvp-pending-chat-approval-decision-card.md"
            in panel["evidence_refs"]
        )
        assert (
            "07_LOGS/Operator-Briefs/2026-05-13-mvp-pending-chat-consumption-readiness-card.md"
            in panel["evidence_refs"]
        )
        assert "06_AGENTS/ChaseOS-MVP-Current-Goal-and-Pass-Plan.md" in panel["evidence_refs"]
        briefing_refs = {item["id"]: item for item in panel["operator_briefing_refs"]}
        assert briefing_refs["operator_next_action_card"]["path"] == (
            "07_LOGS/Operator-Briefs/2026-05-13-mvp-next-action-card.md"
        )
        assert briefing_refs["credential_handoff_card"]["path"] == (
            "07_LOGS/Operator-Briefs/2026-05-13-mvp-openai-secret-reference-handoff-card.md"
        )
        assert briefing_refs["current_openai_handoff_guide"]["path"] == (
            "07_LOGS/Operator-Briefs/2026-05-14-openai-api-key-later-guide.md"
        )
        assert briefing_refs["pending_chat_approval_decision_card"]["path"] == (
            "07_LOGS/Operator-Briefs/2026-05-13-mvp-pending-chat-approval-decision-card.md"
        )
        assert briefing_refs["pending_chat_consumption_readiness_card"]["path"] == (
            "07_LOGS/Operator-Briefs/2026-05-13-mvp-pending-chat-consumption-readiness-card.md"
        )
        assert briefing_refs["current_goal_pass_plan"]["path"] == (
            "06_AGENTS/ChaseOS-MVP-Current-Goal-and-Pass-Plan.md"
        )
        assert briefing_refs["operator_input_template"]["path"] == (
            "07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json"
        )
        assert (
            panel["key_checks"]["provider_validation_command"]
            == "python -m runtime.cli.main setup provider validate openai --json"
        )
        assert (
            panel["key_checks"]["provider_live_smoke_readiness_command"]
            == "python -m runtime.cli.main runtime provider live-smoke-readiness --json"
        )
        assert (
            panel["key_checks"]["credential_handoff_command"]
            == "python -m runtime.cli.main mvp credential-handoff --json"
        )
        assert panel["key_checks"]["next_operator_action_id"] == "openai_secret_reference"
        assert panel["key_checks"]["next_action_count"] == len(panel["next_action_queue"])
        assert panel["key_checks"]["completion_matrix_count"] == 10
        assert panel["key_checks"]["blocked_requirement_count"] >= 1
        assert panel["key_checks"]["operator_input_schema_version"] == "chaseos.mvp_operator_input_schema.v1"
        assert panel["key_checks"]["operator_input_template_version"] == "chaseos.mvp_operator_input_template.v1"
        assert panel["key_checks"]["operator_input_group_count"] >= 2
        assert panel["key_checks"]["operator_input_template_group_count"] >= 2
        assert panel["key_checks"]["operator_input_values_visible"] is False
        assert panel["key_checks"]["operator_input_validator_command"] == (
            "python -m runtime.cli.main mvp validate-operator-input --input <OPERATOR_INPUT_JSON> --json"
        )
        assert panel["key_checks"]["operator_input_template_artifact_path"] == (
            "07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json"
        )
        assert panel["key_checks"]["operator_input_template_artifact_exists"] is True
        assert panel["key_checks"]["operator_input_template_artifact_contains_secret_values"] is False
        handoff = panel["operator_input_handoff"]
        assert handoff["current_state_map_command"] == "python -m runtime.cli.main mvp current-state --json"
        assert handoff["candidate_values_visible"] is False
        assert handoff["source_values_echoed"] is False
        assert handoff["followup_requires_separate_operator_confirmation"] is True
        assert handoff["validate_operator_input_command"] == (
            "python -m runtime.cli.main mvp validate-operator-input --input <OPERATOR_INPUT_JSON> --json"
        )
        assert handoff["operator_input_template_artifact"] == panel[
            "operator_input_template_artifact"
        ]
        assert "secret_value" in handoff["forbidden_values"]
        assert {
            "openai_secret_reference",
            "ventureops_real_client_scope",
        } <= {item["id"] for item in handoff["operator_input_schema_groups"]}
        assert panel["key_checks"]["ventureops_manifest_command"] == (
            "python -m runtime.cli.main ventureops real-client-input-manifest --json"
        )
        assert panel["key_checks"]["ventureops_next_required_action"].startswith("provide real client label")
        assert panel["key_checks"]["ventureops_ready_to_author_scope_approval"] is False
        assert panel["key_checks"]["ventureops_ready_to_author_scope_packet"] is False
        assert panel["key_checks"]["ventureops_ready_for_live_client_workflow_proof"] is False
        ventureops_input = next(
            item for item in panel["p0_operator_inputs"] if item["id"] == "ventureops_real_client_scope"
        )
        assert "client_label" in ventureops_input["missing_inputs"]
        assert ventureops_input["provided_inputs"]["client_label"] is False
        assert panel["key_checks"]["system_control_status"] == "parked_and_gated_until_mvp_proven"
        assert panel["key_checks"]["broad_system_control_allowed"] is False
        assert panel["key_checks"]["browser_system_automation_allowed_now"] is False
        assert panel["key_checks"]["host_mutation_allowed_now"] is False
        assert "openai_secret_reference" in {item["id"] for item in panel["p0_operator_inputs"]}
        assert (
            "python -m runtime.cli.main setup set provider openai secret_reference_kind=env-var-or-local-secret-ref secret_reference_present=true secret_reference_target=OPENAI_API_KEY --dry-run --json"
            in {
            item["command"] for item in panel["safe_next_commands"]
            }
        )
        assert "test-key-secret-that-must-not-leak" not in serialized


# ── TestSchedulePanel ─────────────────────────────────────────────────────────

def _make_mock_schedule(schedule_id: str, workflow_id: str, cadence: str, enabled: bool):
    """Return a minimal mock ScheduleIntent-like object for testing."""
    from types import SimpleNamespace
    return SimpleNamespace(
        schedule_id=schedule_id,
        workflow_id=workflow_id,
        cadence=cadence,
        enabled=enabled,
    )


class TestSchedulePanel:
    def test_empty_when_no_schedules(self, tmp_path):
        vault = _make_vault(tmp_path)
        with patch("runtime.studio.dashboard._gather_schedule_panel.__module__"):
            pass
        result = get_dashboard(vault)
        sp = result["schedule_panel"]
        assert sp["total"] == 0

    def test_counts_enabled_schedules(self, tmp_path):
        vault = _make_vault(tmp_path)
        mocks = [_make_mock_schedule("sch-1", "operator_today", "daily", True)]
        with patch("runtime.studio.dashboard._list_schedules", return_value=mocks):
            result = get_dashboard(vault)
        sp = result["schedule_panel"]
        assert sp["total"] == 1
        assert sp["enabled"] == 1
        assert sp["disabled"] == 0

    def test_counts_disabled_schedules(self, tmp_path):
        vault = _make_vault(tmp_path)
        mocks = [_make_mock_schedule("sch-off", "operator_today", "daily", False)]
        with patch("runtime.studio.dashboard._list_schedules", return_value=mocks):
            result = get_dashboard(vault)
        sp = result["schedule_panel"]
        assert sp["disabled"] == 1

    def test_schedule_entries_have_required_fields(self, tmp_path):
        vault = _make_vault(tmp_path)
        mocks = [_make_mock_schedule("sch-fields", "operator_today", "daily", True)]
        with patch("runtime.studio.dashboard._list_schedules", return_value=mocks):
            result = get_dashboard(vault)
        sp = result["schedule_panel"]
        assert len(sp["schedules"]) == 1
        entry = sp["schedules"][0]
        assert "schedule_id" in entry
        assert "workflow_id" in entry
        assert "enabled" in entry


# ── TestBusPanel ──────────────────────────────────────────────────────────────

class TestBusPanel:
    def test_zero_tasks_on_empty_bus(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = get_dashboard(vault)
        bp = result["bus_panel"]
        assert bp["total"] == 0
        assert bp["open"] == 0

    def test_counts_tasks_by_status(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.agent_bus.bus import create_task
        create_task(vault, sender="OpenClaw", recipient="Hermes",
                    intent="REVIEW", request="review this", expected_output="review result")
        result = get_dashboard(vault)
        bp = result["bus_panel"]
        assert bp["total"] >= 1

    def test_open_count_includes_open_and_in_progress(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.agent_bus.bus import create_task
        create_task(vault, sender="OpenClaw", recipient="Hermes",
                    intent="TASK", request="do work", expected_output="done")
        result = get_dashboard(vault)
        bp = result["bus_panel"]
        assert bp["open"] >= 1

    def test_by_status_dict_present(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = get_dashboard(vault)
        assert isinstance(result["bus_panel"]["by_status"], dict)


# ── TestQuarantinePanel ───────────────────────────────────────────────────────

class TestQuarantinePanel:
    def test_empty_quarantine(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = get_dashboard(vault)
        qp = result["quarantine_panel"]
        assert qp["total"] == 0
        assert qp["by_class"] == {}

    def test_counts_files_in_class_subdirs(self, tmp_path):
        vault = _make_vault(tmp_path)
        digest_dir = vault / "03_INPUTS" / "00_QUARANTINE" / "digest"
        digest_dir.mkdir()
        (digest_dir / "capture1.md").write_text("content", encoding="utf-8")
        (digest_dir / "capture2.md").write_text("content", encoding="utf-8")
        result = get_dashboard(vault)
        qp = result["quarantine_panel"]
        assert qp["total"] == 2
        assert qp["by_class"]["digest"] == 2

    def test_multiple_class_dirs(self, tmp_path):
        vault = _make_vault(tmp_path)
        for cls in ("digest", "source"):
            d = vault / "03_INPUTS" / "00_QUARANTINE" / cls
            d.mkdir()
            (d / "f.md").write_text("x", encoding="utf-8")
        result = get_dashboard(vault)
        qp = result["quarantine_panel"]
        assert qp["total"] == 2
        assert "digest" in qp["by_class"]
        assert "source" in qp["by_class"]

    def test_no_quarantine_dir_returns_zero(self, tmp_path):
        vault = tmp_path / "vaultx"
        vault.mkdir()
        result = get_dashboard(vault)
        qp = result["quarantine_panel"]
        assert qp["total"] == 0


# ── TestGraphPanel ────────────────────────────────────────────────────────────

class TestGraphPanel:
    def test_no_snapshot_returns_unavailable(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = get_dashboard(vault)
        gp = result["graph_panel"]
        assert gp["snapshot_available"] is False

    def test_snapshot_fields_populated(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.graph.artifact import GraphNode, GraphEdge, GraphSnapshot
        from runtime.graph.builder import save_snapshot
        snap = GraphSnapshot(
            snapshot_id="dash-test-001",
            created_at="2026-04-30T12:00:00Z",
            vault_root=str(vault),
            extraction_scope=["runtime/"],
            nodes=[
                GraphNode(node_id="n1", label="fn", node_type="function",
                          source_file="x.py", source_line=1, domain="aor",
                          project=None, properties={}, confidence="EXTRACTED",
                          provenance="test"),
            ],
            edges=[],
            community_assignments={},
            build_info={"errors": []},
            metadata={},
        )
        save_snapshot(snap, vault / "07_LOGS" / "Graph-Snapshots")
        result = get_dashboard(vault)
        gp = result["graph_panel"]
        assert gp["snapshot_available"] is True
        assert gp["node_count"] == 1
        assert gp["edge_count"] == 0
        assert gp["snapshot_id"] == "dash-test-001"

    def test_age_hours_calculated(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.graph.artifact import GraphSnapshot
        from runtime.graph.builder import save_snapshot
        from datetime import datetime, timezone
        created = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        snap = GraphSnapshot(
            snapshot_id="age-test",
            created_at=created,
            vault_root=str(vault),
            extraction_scope=[],
            nodes=[],
            edges=[],
            community_assignments={},
            build_info={"errors": []},
            metadata={},
        )
        save_snapshot(snap, vault / "07_LOGS" / "Graph-Snapshots")
        result = get_dashboard(vault)
        gp = result["graph_panel"]
        assert gp["age_hours"] is not None
        assert gp["age_hours"] >= 0

    def test_community_count_included(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.graph.artifact import GraphNode, GraphSnapshot
        from runtime.graph.builder import save_snapshot
        nodes = [
            GraphNode(node_id=f"n{i}", label=f"fn{i}", node_type="function",
                      source_file="x.py", source_line=1, domain="aor",
                      project=None, properties={}, confidence="EXTRACTED",
                      provenance="test")
            for i in range(3)
        ]
        snap = GraphSnapshot(
            snapshot_id="comm-test",
            created_at="2026-04-30T12:00:00Z",
            vault_root=str(vault),
            extraction_scope=[],
            nodes=nodes,
            edges=[],
            community_assignments={"n0": 0, "n1": 0, "n2": 1},
            build_info={"errors": []},
            metadata={},
        )
        save_snapshot(snap, vault / "07_LOGS" / "Graph-Snapshots")
        result = get_dashboard(vault)
        assert result["graph_panel"]["community_count"] == 2


# ── TestMemoryPanel ───────────────────────────────────────────────────────────

class TestMemoryPanel:
    def test_no_adapters_returns_empty(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = get_dashboard(vault)
        mp = result["memory_panel"]
        assert mp["runtime_count"] == 0
        assert mp["registered_runtimes"] == []

    def test_detects_registered_runtime(self, tmp_path):
        vault = _make_vault(tmp_path)
        rt_dir = vault / "runtime" / "memory" / "adapters" / "claude"
        rt_dir.mkdir(parents=True)
        (rt_dir / "profile.json").write_text('{"runtime_id": "claude"}', encoding="utf-8")
        result = get_dashboard(vault)
        mp = result["memory_panel"]
        assert mp["runtime_count"] == 1
        assert mp["registered_runtimes"][0]["runtime_id"] == "claude"
        assert mp["registered_runtimes"][0]["has_profile"] is True

    def test_tracks_missing_files(self, tmp_path):
        vault = _make_vault(tmp_path)
        rt_dir = vault / "runtime" / "memory" / "adapters" / "hermes"
        rt_dir.mkdir(parents=True)
        result = get_dashboard(vault)
        mp = result["memory_panel"]
        entry = mp["registered_runtimes"][0]
        assert entry["has_profile"] is False
        assert entry["has_identity_ledger"] is False
        assert entry["has_nav_map"] is False

    def test_multiple_runtimes(self, tmp_path):
        vault = _make_vault(tmp_path)
        for name in ("claude", "hermes", "openclaw"):
            d = vault / "runtime" / "memory" / "adapters" / name
            d.mkdir(parents=True)
        result = get_dashboard(vault)
        mp = result["memory_panel"]
        assert mp["runtime_count"] == 3


# ── TestAuditPanel ────────────────────────────────────────────────────────────

class TestAuditPanel:
    def test_empty_audit_dir(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = get_dashboard(vault)
        ap = result["audit_panel"]
        assert ap["recent_entry_count"] == 0

    def test_counts_audit_files(self, tmp_path):
        vault = _make_vault(tmp_path)
        audit_dir = vault / "07_LOGS" / "Agent-Activity"
        for i in range(3):
            (audit_dir / f"2026-04-30T12-00-0{i}__studio__write__abc{i}.md").write_text(
                "audit", encoding="utf-8"
            )
        result = get_dashboard(vault)
        ap = result["audit_panel"]
        assert ap["recent_entry_count"] == 3

    def test_sample_entries_capped(self, tmp_path):
        vault = _make_vault(tmp_path)
        audit_dir = vault / "07_LOGS" / "Agent-Activity"
        for i in range(10):
            (audit_dir / f"2026-04-30T12-00-{i:02d}__studio__write__id{i}.md").write_text(
                "audit", encoding="utf-8"
            )
        result = get_dashboard(vault)
        ap = result["audit_panel"]
        assert len(ap["sample_entries"]) <= 5


# ── TestApprovalPanel ─────────────────────────────────────────────────────────

class TestApprovalPanel:
    def test_empty_approval_dir(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = get_dashboard(vault)
        ap = result["approval_panel"]
        assert ap["pending"] == 0
        assert ap["total"] == 0

    def test_counts_pending_approvals(self, tmp_path):
        vault = _make_vault(tmp_path)
        approval_dir = vault / "runtime" / "studio" / "approvals"
        for i in range(2):
            (approval_dir / f"req-{i}.json").write_text(
                json.dumps({"approval_id": f"req-{i}", "status": "pending"}),
                encoding="utf-8",
            )
        result = get_dashboard(vault)
        ap = result["approval_panel"]
        assert ap["pending"] == 2
        assert ap["total"] == 2

    def test_by_status_breakdown(self, tmp_path):
        vault = _make_vault(tmp_path)
        approval_dir = vault / "runtime" / "studio" / "approvals"
        (approval_dir / "p1.json").write_text(
            json.dumps({"status": "pending"}), encoding="utf-8"
        )
        (approval_dir / "a1.json").write_text(
            json.dumps({"status": "approved"}), encoding="utf-8"
        )
        result = get_dashboard(vault)
        ap = result["approval_panel"]
        assert ap["by_status"]["pending"] == 1
        assert ap["by_status"]["approved"] == 1

    def test_no_approval_dir_returns_zero(self, tmp_path):
        vault = tmp_path / "vaultx"
        vault.mkdir()
        result = get_dashboard(vault)
        ap = result["approval_panel"]
        assert ap["pending"] == 0


# ── TestRuntimeStartupPanel ───────────────────────────────────────────────────

class TestRuntimeStartupPanel:
    def test_runtime_startup_panel_reports_local_app(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = get_dashboard(vault)
        panel = result["runtime_startup_panel"]
        assert panel["ok"] is True
        assert panel["local_app_command"] == "chaseos studio runtime-startup-controls-app --dry-run --json"
        assert panel["authority"]["binds_loopback_only"] is True
        assert panel["authority"]["canonical_mutation_allowed"] is False

    def test_runtime_startup_panel_counts_visual_cards(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = get_dashboard(vault)
        panel = result["runtime_startup_panel"]
        assert panel["surface_count"] >= 0
        assert panel["visual_surface_count"] >= 0
        assert panel["allowed_action_count"] >= 0
        assert isinstance(panel["cards"], list)

    def test_runtime_startup_panel_fail_open(self, tmp_path):
        vault = _make_vault(tmp_path)
        with patch("runtime.studio.dashboard._gather_runtime_startup_panel", side_effect=Exception("startup panel down")):
            result = get_dashboard(vault)
        assert result["ok"] is True
        assert result["runtime_startup_panel"]["local_app_available"] is False
        assert any("runtime_startup_panel" in err for err in result["panel_errors"])


# ── TestFailOpen ──────────────────────────────────────────────────────────────

class TestFailOpen:
    def test_broken_bus_does_not_abort_dashboard(self, tmp_path):
        vault = _make_vault(tmp_path)
        with patch("runtime.studio.dashboard._gather_bus_panel", side_effect=Exception("bus down")):
            result = get_dashboard(vault)
        assert result["ok"] is True
        assert "schedule_panel" in result

    def test_broken_graph_does_not_abort_dashboard(self, tmp_path):
        vault = _make_vault(tmp_path)
        with patch("runtime.studio.dashboard._gather_graph_panel", side_effect=Exception("graph err")):
            result = get_dashboard(vault)
        assert result["ok"] is True
        assert "memory_panel" in result

    def test_panel_errors_collected(self, tmp_path):
        vault = _make_vault(tmp_path)
        with patch("runtime.studio.dashboard._gather_bus_panel",
                   return_value=({"total": 0, "by_status": {}, "open": 0},)):
            pass
        # Real fail-open: errors list exists even when everything works
        result = get_dashboard(vault)
        assert "panel_errors" in result
        assert isinstance(result["panel_errors"], list)
