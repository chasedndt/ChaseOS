"""Tests for the read-only Studio MVP shell app."""

from __future__ import annotations

import argparse
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Event, Thread
from time import monotonic
from urllib.request import urlopen

import pytest

from runtime.studio import desktop_shell_app
from runtime.studio.desktop_shell_app import (
    StudioDesktopShellAppError,
    build_studio_desktop_shell_app_plan,
    make_studio_desktop_shell_app_handler,
    render_studio_desktop_shell_app_html,
    run_node_inspector_shell_panel_qa_runner,
    serve_studio_desktop_shell_app,
    smoke_test_studio_desktop_shell_app,
)


def _vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    (vault / "runtime" / "studio").mkdir(parents=True)
    return vault


def _write_graph_artifact(vault: Path) -> None:
    artifact = vault / "07_LOGS" / "Studio-Graph-Views" / "2026-05-03T09-39-25-844850Z-graph-view-static.html"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("<html><body><svg class='graph'></svg></body></html>", encoding="utf-8")


def _contract() -> dict:
    return {
        "ok": True,
        "surface": "studio_runtime_cockpit_contract",
        "status": "contract_ready_local_mount_built_studio_shell_mvp_built",
        "dashboard": {"panel_errors": []},
        "runtime_startup": {
            "surface_count": 1,
            "manageable_surface_count": 1,
            "visual_surface_count": 1,
            "readiness_summary": {
                "readiness_packet_count": 2,
                "approval_missing_count": 1,
            },
            "cards": [
                {
                    "runtime_id": "hermes",
                    "runtime_name": "Hermes",
                    "current_state": "registered",
                    "health_status": "live",
                    "studio_visual_toggle_built": True,
                    "launch_profile": {"launch_kind": "wsl", "wsl_distro": "Ubuntu"},
                    "readiness_summary": {"approval_missing_count": 1},
                    "commands": {
                        "enable_dry_run": "chaseos studio runtime-startup-controls --runtime hermes --intent enable --action dry-run --json"
                    },
                }
            ],
        },
        "runtime_health": {
            "runtime_profile_count": 1,
            "live_runtime_count": 1,
            "offline_runtime_count": 0,
            "blocked_runtime_count": 0,
            "unknown_runtime_count": 0,
            "profiles": [{"runtime_id": "hermes", "runtime_name": "Hermes", "status": "live"}],
        },
    }


def _launcher() -> dict:
    return {
        "ok": True,
        "surface": "studio_app_launcher_local_app",
        "apps": [
            {
                "id": "runtime-cockpit-app",
                "title": "Runtime Cockpit",
                "command": "chaseos studio runtime-cockpit-app",
                "read_only": True,
                "write_capable": False,
                "runtime_status": {"state": "not_checked"},
            },
            {
                "id": "runtime-startup-controls-app",
                "title": "Runtime Startup Controls",
                "command": "chaseos studio runtime-startup-controls-app",
                "read_only": False,
                "write_capable": True,
                "runtime_status": {"state": "not_checked"},
            },
            {
                "id": "approval-center-app",
                "title": "ChaseOS Pulse Approval Center",
                "command": "chaseos studio approval-center-app",
                "read_only": True,
                "write_capable": False,
                "runtime_status": {"state": "not_checked"},
            },
        ],
    }


def _pulse_panel() -> dict:
    return {
        "ok": True,
        "surface": "studio_pulse_product_shell_panel_contract",
        "status": "PARTIAL / PULSE PRODUCT SHELL PANEL CONTRACT BUILT / READ-ONLY STUDIO MOUNT BUILT",
        "panel": {
            "panel_id": "studio.pulse.product_shell.panel",
            "label": "Pulse",
            "source_artifact_path": "07_LOGS/Pulse-Decks/product-shell/2026-05-03-pulse-product-shell.html",
            "source_artifact_uri": "file:///C:/vault/07_LOGS/Pulse-Decks/product-shell/2026-05-03-pulse-product-shell.html",
        },
        "summary": {
            "panel_count": 7,
            "card_count": 12,
            "blocker_count": 0,
        },
        "readiness": {
            "pulse_product_shell_panel_contract_ready": True,
            "desktop_shell_mount_ready": True,
            "blockers": [],
        },
        "authority": {
            "read_only": True,
            "submits_feedback": False,
            "executes_approvals": False,
            "applies_candidates": False,
            "activates_schedules": False,
            "canonical_mutation_allowed": False,
        },
    }


def _graph_panel() -> dict:
    return {
        "ok": True,
        "surface": "studio_graph_view_shell_panel_contract",
        "status": "PARTIAL / GRAPH SHELL PANEL CONTRACT BUILT / READ-ONLY STUDIO MOUNT BUILT",
        "panel": {
            "panel_id": "studio.graph_view.shell_panel",
            "label": "Graph View",
            "source_artifact_path": "07_LOGS/Studio-Graph-Views/2026-05-03T09-39-25-844850Z-graph-view-static.html",
            "source_artifact_uri": "file:///C:/vault/07_LOGS/Studio-Graph-Views/2026-05-03T09-39-25-844850Z-graph-view-static.html",
        },
        "summary": {
            "visible_node_count": 20,
            "visible_edge_count": 15,
            "source_node_count": 80,
            "blocker_count": 0,
        },
        "readiness": {
            "graph_view_shell_panel_contract_ready": True,
            "desktop_shell_mount_ready": True,
            "blockers": [],
        },
        "authority": {
            "read_only": True,
            "writes_graph_index": False,
            "writes_node_ids": False,
            "canonical_mutation_allowed": False,
        },
    }


def _node_panel() -> dict:
    return {
        "ok": True,
        "surface": "studio_node_inspector_shell_panel_contract",
        "status": "COMPLETE TARGETED / NODE INSPECTOR SHELL PANEL CONTRACT BUILT / READ-ONLY STUDIO MOUNT BUILT",
        "panel": {
            "panel_id": "studio.node_inspector.shell_panel",
            "label": "Node Inspector",
            "surface_route": "#node-inspector",
            "selection_source": "derived-from-rebuildable-graph-contract",
            "selected_node_id": "node-alpha",
            "selected_node_label": "Alpha",
            "selected_node_type": "chaseos_markdown_doc",
            "selected_node_path": "alpha.md",
        },
        "summary": {
            "selected_node_found": True,
            "selected_node_label": "Alpha",
            "selected_node_type": "chaseos_markdown_doc",
            "source_path": "alpha.md",
            "incoming_edge_count": 1,
            "outgoing_edge_count": 2,
            "related_node_count": 3,
            "source_excerpt_available": True,
            "blocker_count": 0,
        },
        "source_node_inspector": {
            "selected_node": {
                "id": "node-alpha",
                "label": "Alpha",
                "node_type": "chaseos_markdown_doc",
                "properties": {"path": "alpha.md"},
            },
            "edge_context": {
                "related_nodes": [
                    {"label": "Beta", "node_type": "chaseos_markdown_doc"},
                ],
            },
            "source_excerpt": {
                "available": True,
                "text": "# Alpha\nLinks to Beta.",
                "bytes_read": 23,
                "truncated": False,
            },
        },
        "readiness": {
            "node_inspector_shell_panel_contract_ready": True,
            "desktop_shell_mount_ready": True,
            "blockers": [],
        },
        "authority": {
            "read_only": True,
            "writes_node_ids": False,
            "writes_graph_index": False,
            "node_editing_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }


def _approval_queue_panel() -> dict:
    return {
        "ok": True,
        "surface": "studio_pulse_approval_queue_panel_contract",
        "status": "PARTIAL / APPROVAL QUEUE PANEL CONTRACT BUILT / READ-ONLY STUDIO MOUNT BUILT",
        "panel": {
            "panel_id": "studio.pulse.approval_queue.panel",
            "label": "Approval Queue",
            "source_artifact_path": "07_LOGS/Pulse-Decks/approval-queue/2026-05-03-approval-queue.html",
            "source_artifact_uri": "file:///C:/vault/07_LOGS/Pulse-Decks/approval-queue/2026-05-03-approval-queue.html",
        },
        "summary": {
            "lane_count": 8,
            "candidate_row_count": 4,
            "action_count": 5,
            "missing_approval_key_count": 2,
            "blocker_count": 0,
        },
        "readiness": {
            "approval_queue_panel_contract_ready": True,
            "desktop_shell_mount_ready": True,
            "blockers": [],
        },
        "authority": {
            "read_only": True,
            "grants_approvals": False,
            "executes_approvals": False,
            "applies_candidates": False,
            "canonical_mutation_allowed": False,
        },
    }


def _arsl_route_review_panel() -> dict:
    return {
        "ok": True,
        "surface": "studio_arsl_route_review_panel_contract",
        "status": "PARTIAL / ARSL ROUTE REVIEW PANEL CONTRACT BUILT / READ-ONLY STUDIO MOUNT BUILT",
        "panel": {
            "panel_id": "studio.arsl.route_review.panel",
            "label": "ARSL Route Review",
            "surface_route": "#arsl-route-review",
            "source_command": "chaseos runtime surfaces route-review --capability browser.click --json",
        },
        "summary": {
            "requested_capability": "browser.click",
            "review_row_count": 3,
            "gate_required_rows": 2,
            "explicit_or_conditional_approval_rows": 2,
            "preview_decision": "approval_required",
            "selected_surface": "browser.playwright.operator",
            "authority_layer": "runtime/operator_surface/",
            "approval_required": "explicit",
        },
        "source_route_review": {
            "route_preview": {
                "decision": "approval_required",
                "gate_required": True,
                "audit_required": True,
                "ledger_written": False,
            },
            "review_rows": [
                {
                    "surface_id": "browser.playwright.operator",
                    "capability_id": "browser.click",
                    "policy_decision": "approval_required",
                    "risk_class": "medium_risk_write",
                    "approval_required": "explicit",
                    "gate_required": True,
                }
            ],
            "safety": {
                "execution_performed": False,
                "ledger_written": False,
                "browser_control_performed": False,
                "raw_manifest_exposed": False,
            },
        },
        "readiness": {
            "arsl_route_review_panel_contract_ready": True,
            "desktop_shell_mount_ready": True,
            "blockers": [],
        },
        "authority": {
            "read_only": True,
            "executes_routes": False,
            "writes_routing_ledger": False,
            "grants_approvals": False,
            "mutates_gate_policy": False,
            "provider_calls_allowed": False,
            "browser_control_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }


def _browser_runtime_panel() -> dict:
    return {
        "ok": True,
        "surface": "studio_browser_runtime_operator_ui_readiness_contract",
        "status": "PARTIAL / READ-ONLY OPERATOR UI READINESS CONTRACT BUILT / FULL UI NOT BUILT",
        "panel_group": {
            "panel_group_id": "studio.browser_runtime.operator",
            "label": "Browser Runtime",
            "surface_route": "#browser-runtime",
            "panel_count": 8,
            "required_panel_ids": [
                "browser-runtime-completion-summary",
                "browser-runtime-remaining-passes",
                "browser-runtime-external-dependencies",
                "browser-runtime-excalidraw-chain",
                "browser-runtime-provider-validation",
                "browser-runtime-site-skill-memory",
                "browser-runtime-approval-queue",
                "browser-runtime-run-evidence",
            ],
        },
        "summary": {
            "overall_status": "mvp_done_production_blocked",
            "bounded_mvp_done": True,
            "production_feature_done": False,
            "next_recommended_pass": "studio-browser-runtime-panel-browser-qa",
            "blocker_count": 3,
            "remaining_major_passes_min": 5,
            "remaining_major_passes_max": 9,
        },
        "panels": [
            {"panel_id": "browser-runtime-completion-summary", "label": "Completion", "ready_for_studio_mount": True, "render_mode": "read-only-data-contract"},
            {"panel_id": "browser-runtime-remaining-passes", "label": "Remaining Passes", "ready_for_studio_mount": True, "render_mode": "read-only-data-contract"},
            {"panel_id": "browser-runtime-external-dependencies", "label": "External Dependencies", "ready_for_studio_mount": True, "render_mode": "read-only-data-contract"},
            {"panel_id": "browser-runtime-excalidraw-chain", "label": "Excalidraw Chain", "ready_for_studio_mount": True, "render_mode": "read-only-data-contract"},
            {"panel_id": "browser-runtime-provider-validation", "label": "Provider Validation", "ready_for_studio_mount": True, "render_mode": "read-only-data-contract"},
            {"panel_id": "browser-runtime-site-skill-memory", "label": "Site Skills", "ready_for_studio_mount": True, "render_mode": "read-only-data-contract"},
            {"panel_id": "browser-runtime-approval-queue", "label": "Approvals", "ready_for_studio_mount": False, "render_mode": "read-only-data-contract"},
            {"panel_id": "browser-runtime-run-evidence", "label": "Run Evidence", "ready_for_studio_mount": True, "render_mode": "read-only-data-contract"},
        ],
        "remaining_passes": [],
        "external_dependencies": [
            {"label": "Browser Use CLI", "status": "external-setup-required", "next_action": "validate outside ChaseOS"}
        ],
        "blocked_reasons": ["browser_use_cli_external_validation_deferred"],
        "current_evidence": {
            "browser_run_logs_root": {"path": "07_LOGS/Browser-Runs", "exists": True},
            "agent_activity_root": {"path": "07_LOGS/Agent-Activity", "exists": True},
        },
        "readiness": {
            "operator_ui_readiness_contract_ready": True,
            "studio_operator_ui_built": False,
            "next_recommended_pass": "studio-browser-runtime-panel-browser-qa",
        },
        "authority": {
            "read_only": True,
            "starts_servers": False,
            "opens_browser": False,
            "launches_browser": False,
            "connects_cdp": False,
            "invokes_mcp": False,
            "runs_browser_use_cli_live": False,
            "activates_skills": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "gate_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "possible_writes": [],
    }


def _canvas_panel() -> dict:
    return {
        "ok": True,
        "surface": "studio_canvas_panel_contract",
        "status": "PARTIAL / READ-ONLY CANVAS PANEL CONTRACT BUILT",
        "summary": {
            "object_count": 2,
            "link_count": 1,
            "graph_node_ref_count": 1,
        },
        "readiness": {
            "canvas_panel_contract_ready": True,
            "desktop_shell_mount_ready": True,
        },
        "authority": {
            "read_only": True,
            "writes_canvas_state": False,
            "canonical_mutation_allowed": False,
        },
        "objects": [],
        "links": [],
    }


def _workspace_mode_panel() -> dict:
    return {
        "ok": True,
        "surface": "studio_workspace_mode_panel",
        "status": "COMPLETE / READ-ONLY STUDIO MOUNT",
        "native_panel": {
            "mounted": True,
            "panel_id": "workspace-mode",
            "route_hint": "#workspace-mode",
            "connected_surfaces": ["studio-dashboard", "project-workspace", "chat"],
        },
        "summary": {
            "overall_status": "COMPLETE",
            "profile_valid_count": 6,
            "profile_total_count": 6,
            "route_ready_count": 3,
            "route_blocked_count": 1,
            "approval_artifact_count": 5,
            "project_count": 4,
            "domain_count": 3,
            "manual_testing_ready": True,
        },
        "route_cards": [
            {
                "path": "runtime/aor/engine.py",
                "workspace_path": "runtime/aor/engine.py",
                "label": "Runtime operations",
                "mode": "runtime_agent_ops",
                "ready": True,
                "profile_path": "runtime/.workspace-mode.yaml",
                "blockers": [],
            },
            {
                "path": "04_SOPS/Build-Log-SOP.md",
                "workspace_path": "04_SOPS/Build-Log-SOP.md",
                "label": "Business ops",
                "mode": "business_ops",
                "ready": False,
                "profile_path": "04_SOPS/.workspace-mode.yaml",
                "blockers": ["workflow_not_allowed_by_explicit_profile"],
            },
        ],
        "mode_options": [
            {
                "id": "personal_os",
                "label": "Personal OS",
                "purpose": "Personal life and private knowledge.",
                "default_posture": "Conservative private-context inspection.",
                "anchor": "workspace-mode-mode-personal-os",
                "project_count": 0,
                "domain_count": 0,
                "route_count": 0,
                "ready_route_count": 0,
                "projects": [],
                "domains": [],
                "routes": [],
            },
            {
                "id": "founder_venture",
                "label": "Founder / Venture",
                "purpose": "Startups, products, R&D, market research, roadmap proposals, and experiments.",
                "default_posture": "Strict project and roadmap truth.",
                "anchor": "workspace-mode-mode-founder-venture",
                "project_count": 1,
                "domain_count": 1,
                "route_count": 0,
                "ready_route_count": 0,
                "projects": [
                    {
                        "project": "StrikeZone",
                        "domain": "Products",
                        "status": "active",
                        "workspace_path": "01_PROJECTS/StrikeZone/StrikeZone-OS.md",
                        "mode": "founder_venture",
                    }
                ],
                "domains": [{"domain": "Products", "project_count": 1, "primary_mode": "founder_venture"}],
                "routes": [],
            },
            {
                "id": "runtime_agent_ops",
                "label": "Runtime / Agent Ops",
                "purpose": "ChaseOS runtime governance, policies, workflows, and logs.",
                "default_posture": "Very strict preview routes only.",
                "anchor": "workspace-mode-mode-runtime-agent-ops",
                "project_count": 0,
                "domain_count": 0,
                "route_count": 1,
                "ready_route_count": 1,
                "projects": [],
                "domains": [],
                "routes": [
                    {
                        "path": "runtime/aor/engine.py",
                        "mode": "runtime_agent_ops",
                        "ready": True,
                    }
                ],
            },
        ],
        "project_cards": [
            {
                "project": "StrikeZone",
                "domain": "Products",
                "status": "active",
                "workspace_path": "01_PROJECTS/StrikeZone/StrikeZone-OS.md",
                "mode": "founder_venture",
            }
        ],
        "domain_cards": [{"domain": "Products", "project_count": 1, "primary_mode": "founder_venture"}],
        "project_workspace_connection": {
            "mounted": True,
            "source": "runtime.studio.project_workspace_view.build_project_workspace_view",
            "project_count": 4,
            "domain_count": 3,
        },
        "chat_connection": {
            "context_visible": True,
            "surface": "phase11_chat_panel_readonly_contract",
            "chat_can_execute_workspace_mode": False,
            "chat_can_write_workspace_profiles": False,
        },
        "readiness": {
            "workspace_mode_panel_mounted": True,
            "blockers": [],
        },
        "authority": {
            "read_only": True,
            "profile_writes_allowed": False,
            "workflow_execution_allowed": False,
            "agent_bus_dispatch_allowed": False,
            "provider_calls_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "possible_writes": [],
    }


def test_desktop_shell_plan_mounts_runtime_cockpit_read_only(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    captured: dict[str, object] = {}

    def fake_contract(vault_root, *, runtime_id=None, probe_child_apps=True):
        captured["runtime_id"] = runtime_id
        captured["probe_child_apps"] = probe_child_apps
        return _contract()

    def fake_launcher(vault_root, *, host="127.0.0.1", port=8769, probe_health=True):
        captured["launcher_probe_health"] = probe_health
        return _launcher()

    def fake_graph_panel(vault_root):
        captured["graph_panel"] = True
        return _graph_panel()

    def fake_node_panel(vault_root):
        captured["node_panel"] = True
        return _node_panel()

    def fake_pulse_panel(vault_root):
        captured["pulse_panel"] = True
        return _pulse_panel()

    def fake_approval_queue_panel(vault_root):
        captured["approval_queue_panel"] = True
        return _approval_queue_panel()

    def fake_arsl_route_review_panel(vault_root):
        captured["arsl_route_review_panel"] = True
        return _arsl_route_review_panel()

    def fake_browser_runtime_panel(vault_root):
        captured["browser_runtime_panel"] = True
        return _browser_runtime_panel()

    def fake_workspace_mode_panel(vault_root):
        captured["workspace_mode_panel"] = True
        return _workspace_mode_panel()

    monkeypatch.setattr(desktop_shell_app, "build_runtime_cockpit_contract", fake_contract)
    monkeypatch.setattr(desktop_shell_app, "build_studio_app_launcher_plan", fake_launcher)
    monkeypatch.setattr(desktop_shell_app, "build_graph_view_shell_panel_contract", fake_graph_panel)
    monkeypatch.setattr(desktop_shell_app, "build_node_inspector_shell_panel_contract", fake_node_panel)
    monkeypatch.setattr(desktop_shell_app, "build_pulse_product_shell_panel_contract", fake_pulse_panel)
    monkeypatch.setattr(desktop_shell_app, "build_studio_approval_queue_panel_contract", fake_approval_queue_panel)
    monkeypatch.setattr(desktop_shell_app, "build_arsl_route_review_panel_contract", fake_arsl_route_review_panel)
    monkeypatch.setattr(
        desktop_shell_app,
        "build_studio_browser_runtime_operator_ui_readiness",
        fake_browser_runtime_panel,
    )
    monkeypatch.setattr(desktop_shell_app, "build_workspace_mode_studio_panel", fake_workspace_mode_panel)

    plan = build_studio_desktop_shell_app_plan(vault, runtime_id="hermes")

    assert plan["ok"] is True
    assert plan["surface"] == "studio_desktop_shell_mvp_app"
    assert plan["url"] == "http://127.0.0.1:8772/"
    assert plan["runtime_filter"] == "hermes"
    assert captured == {
        "runtime_id": "hermes",
        "probe_child_apps": False,
        "launcher_probe_health": False,
        "graph_panel": True,
        "node_panel": True,
        "pulse_panel": True,
        "approval_queue_panel": True,
        "arsl_route_review_panel": True,
        "browser_runtime_panel": True,
        "workspace_mode_panel": True,
    }
    assert plan["shell"]["kind"] == "read_only_studio_shell_mvp"
    assert plan["shell"]["full_desktop_shell_built"] is False
    assert plan["shell"]["studio_shell_mvp_built"] is True
    assert plan["shell"]["runtime_cockpit_mounted"] is True
    assert plan["shell"]["approval_center_local_mount_built"] is True
    assert plan["shell"]["graph_view_shell_panel_mounted"] is True
    assert plan["shell"]["graph_view_shell_panel_contract_ready"] is True
    assert plan["shell"]["node_inspector_shell_panel_mounted"] is True
    assert plan["shell"]["node_inspector_shell_panel_contract_ready"] is True
    assert plan["shell"]["interactive_graph_controls_built"] is False
    assert plan["shell"]["graph_persistence_built"] is False
    assert plan["shell"]["graph_node_editing_built"] is False
    assert plan["shell"]["pulse_product_shell_mounted"] is True
    assert plan["shell"]["pulse_product_shell_panel_contract_ready"] is True
    assert plan["shell"]["approval_queue_panel_mounted"] is True
    assert plan["shell"]["approval_queue_panel_contract_ready"] is True
    assert plan["shell"]["arsl_route_review_panel_mounted"] is True
    assert plan["shell"]["arsl_route_review_panel_contract_ready"] is True
    assert plan["shell"]["browser_runtime_panel_mounted"] is True
    assert plan["shell"]["browser_runtime_panel_contract_ready"] is True
    assert plan["shell"]["workspace_mode_panel_mounted"] is True
    assert plan["shell"]["workspace_mode_panel_contract_ready"] is True
    assert plan["shell"]["approval_execution_built"] is False
    assert plan["shell"]["interactive_pulse_controls_built"] is False
    assert plan["shell"]["candidate_apply_ui_built"] is False
    assert plan["shell"]["schedule_activation_ui_built"] is False
    assert plan["shell"]["route_execution_ui_built"] is False
    assert plan["shell"]["route_approval_grant_ui_built"] is False
    assert plan["shell"]["route_ledger_write_ui_built"] is False
    assert plan["authority"]["binds_loopback_only"] is True
    assert plan["authority"]["read_only"] is True
    assert plan["authority"]["mounts_existing_graph_artifact_only"] is True
    assert plan["authority"]["starts_child_apps"] is False
    assert plan["authority"]["writes_host_startup"] is False
    assert plan["authority"]["writes_graph_index"] is False
    assert plan["authority"]["writes_node_ids"] is False
    assert plan["authority"]["edits_graph_nodes"] is False
    assert plan["authority"]["edits_inspected_node"] is False
    assert plan["authority"]["submits_feedback"] is False
    assert plan["authority"]["executes_approvals"] is False
    assert plan["authority"]["applies_candidates"] is False
    assert plan["authority"]["writes_agent_bus_tasks"] is False
    assert plan["authority"]["dispatches_runtimes"] is False
    assert plan["authority"]["executes_routes"] is False
    assert plan["authority"]["commits_route_proposals"] is False
    assert plan["authority"]["writes_routing_ledger"] is False
    assert plan["authority"]["grants_route_approvals"] is False
    assert plan["authority"]["mutates_gate_policy"] is False
    assert plan["authority"]["activates_schedules"] is False
    assert plan["authority"]["workflow_execution_allowed"] is False
    assert plan["possible_writes"] == []
    assert plan["allowed_actions"] == []
    assert plan["metrics"]["runtime_surface_count"] == 1
    assert plan["metrics"]["app_count"] == 3
    assert plan["metrics"]["graph_visible_node_count"] == 20
    assert plan["metrics"]["graph_visible_edge_count"] == 15
    assert plan["metrics"]["node_inspector_selected_node_found"] is True
    assert plan["metrics"]["node_inspector_outgoing_edge_count"] == 2
    assert plan["metrics"]["pulse_panel_count"] == 7
    assert plan["metrics"]["pulse_card_count"] == 12
    assert plan["metrics"]["approval_queue_lane_count"] == 8
    assert plan["metrics"]["approval_queue_candidate_row_count"] == 4
    assert plan["metrics"]["arsl_route_review_row_count"] == 3
    assert plan["metrics"]["arsl_route_review_gate_required_rows"] == 2
    assert plan["metrics"]["arsl_route_review_approval_rows"] == 2
    assert plan["metrics"]["browser_runtime_remaining_passes_min"] == 5
    assert plan["metrics"]["browser_runtime_remaining_passes_max"] == 9
    assert plan["metrics"]["browser_runtime_panel_count"] == 8
    assert plan["metrics"]["workspace_mode_route_ready_count"] == 3
    assert plan["metrics"]["workspace_mode_route_blocked_count"] == 1
    assert plan["metrics"]["workspace_mode_profile_valid_count"] == 6
    assert [card["id"] for card in plan["kpi_cards"]] == [
        "system-health",
        "active-runtimes",
        "approvals-pending",
        "apps-live-offline",
        "memory-candidates",
        "graph-provenance-health",
        "workspace-mode",
        "blocked-dependencies",
        "recent-proof",
    ]
    assert plan["kpi_cards"][0]["source"] == "plan.panel_statuses + plan.metrics.ready_panel_count/degraded_panel_count"
    assert {card["id"]: card["href"] for card in plan["kpi_cards"]}["approvals-pending"] == "#approval-queue"
    kpi_values = {card["id"]: card["value"] for card in plan["kpi_cards"]}
    assert kpi_values["approvals-pending"] == 5
    assert kpi_values["apps-live-offline"] == "0 / 0"
    assert kpi_values["recent-proof"] == plan["metrics"]["ready_panel_count"]
    assert plan["graph_view_shell_panel_url"] == "http://127.0.0.1:8772/graph-view-shell-panel.json"
    assert plan["node_inspector_shell_panel_url"] == "http://127.0.0.1:8772/node-inspector-shell-panel.json"
    assert plan["browser_runtime_panel_url"] == "http://127.0.0.1:8772/browser-runtime-panel.json"
    assert plan["workspace_mode_panel_url"] == "http://127.0.0.1:8772/workspace-mode-panel.json"
    assert "/graph-view-shell-panel.json" in plan["routes"]
    assert "/node-inspector-shell-panel.json" in plan["routes"]
    assert "/pulse-product-shell.json" in plan["routes"]
    assert "/approval-queue.json" in plan["routes"]
    assert "/arsl-route-review.json" in plan["routes"]
    assert "/browser-runtime-panel.json" in plan["routes"]
    assert "/workspace-mode-panel.json" in plan["routes"]
    assert {view["id"]: view["status"] for view in plan["views"]}["runtime-cockpit"] == "mounted-read-only"
    assert {view["id"]: view["status"] for view in plan["views"]}["approval-center"] == "mounted-read-only"
    assert {view["id"]: view["status"] for view in plan["views"]}["graph-view"] == "mounted-read-only"
    assert {view["id"]: view["status"] for view in plan["views"]}["node-inspector"] == "mounted-read-only"
    assert {view["id"]: view["status"] for view in plan["views"]}["approval-queue"] == "mounted-read-only"
    assert {view["id"]: view["status"] for view in plan["views"]}["arsl-route-review"] == "mounted-read-only"
    assert {view["id"]: view["status"] for view in plan["views"]}["pulse"] == "mounted-read-only"
    assert {view["id"]: view["status"] for view in plan["views"]}["browser-runtime"] == "mounted-read-only"
    assert {view["id"]: view["status"] for view in plan["views"]}["workspace-mode"] == "mounted-read-only"
    assert [view["id"] for view in plan["views"][:3]] == ["dashboard", "app-launcher", "approval-center"]


def test_desktop_shell_fast_plan_uses_user_facing_ready_route_fallbacks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    vault = _vault(tmp_path)
    _write_graph_artifact(vault)
    called: list[str] = []

    def forbidden_builder(name: str):
        def _builder(*args, **kwargs):
            called.append(name)
            raise AssertionError(f"{name} should be skipped during fast shell planning")
        return _builder

    monkeypatch.setattr(desktop_shell_app, "build_runtime_cockpit_contract", forbidden_builder("runtime_cockpit"))
    monkeypatch.setattr(
        desktop_shell_app,
        "build_runtime_cockpit_fast_contract",
        lambda vault_root, *, runtime_id=None: _contract(),
        raising=False,
    )
    monkeypatch.setattr(desktop_shell_app, "build_graph_view_shell_panel_contract", forbidden_builder("graph"))
    monkeypatch.setattr(desktop_shell_app, "build_node_inspector_shell_panel_contract", forbidden_builder("node"))
    monkeypatch.setattr(desktop_shell_app, "build_pulse_product_shell_panel_contract", forbidden_builder("pulse"))
    monkeypatch.setattr(desktop_shell_app, "build_studio_approval_queue_panel_contract", forbidden_builder("approval_queue"))
    monkeypatch.setattr(desktop_shell_app, "build_arsl_route_review_panel_contract", forbidden_builder("arsl"))
    monkeypatch.setattr(desktop_shell_app, "build_studio_browser_runtime_operator_ui_readiness", forbidden_builder("browser_runtime"))
    monkeypatch.setattr(desktop_shell_app, "build_studio_app_launcher_plan", lambda *args, **kwargs: _launcher())
    monkeypatch.setattr(
        desktop_shell_app,
        "_collect_host_runtime_processes",
        lambda: {
            "available": True,
            "source": "/proc/*/cmdline read-only host observation",
            "processes": [{"pid": 123, "kind": "hermes", "command": "hermes gateway"}],
            "counts": {"hermes": 1},
            "total": 1,
        },
    )
    monkeypatch.setattr(
        desktop_shell_app,
        "_collect_kanban_snapshot",
        lambda: {
            "available": True,
            "source": "/tmp/kanban.db",
            "counts": {"ready": 2, "running": 1, "blocked": 1},
            "total": 4,
            "attention": [],
        },
    )

    plan = build_studio_desktop_shell_app_plan(vault, planning_mode="fast")

    assert called == []
    assert plan["ok"] is True
    assert plan["planning"]["mode"] == "fast"
    assert plan["planning"]["fast_shell_plan"] is True
    assert plan["metrics"]["runtime_surface_count"] == 1
    assert plan["runtime_cockpit_contract"]["runtime_startup"]["cards"][0]["runtime_name"] == "Hermes"
    assert {card["id"]: card["value"] for card in plan["kpi_cards"]}["active-runtimes"] == 1
    assert plan["operator_dashboard"]["summary"]["observed_runtime_processes"] == 1
    assert plan["operator_dashboard"]["summary"]["kanban_ready"] == 2
    assert plan["operator_dashboard"]["blocked_panels"] == []
    html = render_studio_desktop_shell_app_html(plan)
    assert "Operator Overview" in html
    assert "skipped-fast-plan" not in html.lower()
    assert "skipped_fast_plan" not in html.lower()
    assert "skipped fast plan" not in html.lower()
    assert "read-only host process observations as signals" in html
    assert plan["metrics"]["degraded_panel_count"] == 0
    assert plan["panel_statuses"]["graph-view"]["state"] == "ready"
    assert plan["panel_statuses"]["node-inspector"]["state"] == "ready"
    assert plan["panel_statuses"]["pulse"]["state"] == "ready"
    assert plan["panel_statuses"]["browser-runtime"]["state"] == "ready"
    assert plan["panel_statuses"]["runtime-cockpit"]["state"] == "ready"
    views = {view["id"]: view for view in plan["views"]}
    assert views["graph-view"]["status"] == "mounted-read-only"
    assert views["node-inspector"]["status"] == "mounted-read-only"
    assert views["pulse"]["status"] == "mounted-read-only"
    assert views["settings"]["status"] == "mounted-read-only"
    assert views["settings"]["mounted"] is True
    assert 'data-testid="settings-panel-mount"' in html


def test_default_fast_plan_uses_lightweight_runtime_truth_instead_of_empty_placeholder(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    vault = _vault(tmp_path)
    lifecycle = vault / "runtime" / "lifecycle"
    lifecycle.mkdir(parents=True, exist_ok=True)
    (lifecycle / "hermes.lifecycle.yaml").write_text(
        """
runtime_id: hermes
platform: wsl
lifecycle_mode: wsl-process
coordination_watch:
  runtime_name: Hermes
start:
  kind: command
  command: hermes gateway
health:
  kind: http
  urls:
    - http://127.0.0.1:18790/
ownership: chaseos-managed-runtime-lane
""".strip(),
        encoding="utf-8",
    )

    def forbidden_builder(name: str):
        def _builder(*args, **kwargs):
            raise AssertionError(f"{name} should be skipped during fast shell planning")
        return _builder

    monkeypatch.setattr(desktop_shell_app, "build_runtime_cockpit_contract", forbidden_builder("runtime_cockpit"))
    monkeypatch.setattr(desktop_shell_app, "build_graph_view_shell_panel_contract", forbidden_builder("graph"))
    monkeypatch.setattr(desktop_shell_app, "build_node_inspector_shell_panel_contract", forbidden_builder("node"))
    monkeypatch.setattr(desktop_shell_app, "build_pulse_product_shell_panel_contract", forbidden_builder("pulse"))
    monkeypatch.setattr(desktop_shell_app, "build_studio_approval_queue_panel_contract", forbidden_builder("approval_queue"))
    monkeypatch.setattr(desktop_shell_app, "build_arsl_route_review_panel_contract", forbidden_builder("arsl"))
    monkeypatch.setattr(desktop_shell_app, "build_studio_browser_runtime_operator_ui_readiness", forbidden_builder("browser_runtime"))
    monkeypatch.setattr(desktop_shell_app, "build_canvas_panel_contract", forbidden_builder("canvas"))
    monkeypatch.setattr(desktop_shell_app, "build_studio_app_launcher_plan", lambda *args, **kwargs: _launcher())
    monkeypatch.setattr(
        desktop_shell_app,
        "_collect_host_runtime_processes",
        lambda: {"available": True, "source": "/proc", "processes": [{"pid": 123, "kind": "hermes"}], "counts": {"hermes": 1}, "total": 1},
    )
    monkeypatch.setattr(
        desktop_shell_app,
        "_collect_kanban_snapshot",
        lambda: {"available": False, "source": "no readable Hermes kanban.db found", "counts": {}, "attention": []},
    )
    monkeypatch.setattr(
        desktop_shell_app.runtime_cockpit,
        "_list_runtime_processes",
        lambda runtime_id, record: [{"pid": 123, "command": "hermes gateway"}] if runtime_id == "hermes" else [],
    )

    plan = build_studio_desktop_shell_app_plan(vault, planning_mode="fast")
    kpis = {card["id"]: card for card in plan["kpi_cards"]}

    assert plan["runtime_cockpit_contract"]["status"] == "fast_runtime_truth_ready"
    assert plan["metrics"]["runtime_surface_count_unknown"] is False
    assert plan["metrics"]["runtime_profile_count"] == 1
    assert plan["metrics"]["live_runtime_count"] == 1
    assert plan["runtime_cockpit_contract"]["runtime_startup"]["cards"][0]["runtime_name"] == "Hermes"
    assert kpis["active-runtimes"]["value"] == 1
    html = render_studio_desktop_shell_app_html(plan)
    assert "Hermes" in html
    assert "No runtime cards found" not in html


def test_static_graph_artifact_route_reuses_planned_artifact_without_rescanning(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    vault = _vault(tmp_path)
    _write_graph_artifact(vault)
    monkeypatch.setattr(desktop_shell_app, "build_runtime_cockpit_contract", lambda *args, **kwargs: _contract())
    monkeypatch.setattr(desktop_shell_app, "build_studio_app_launcher_plan", lambda *args, **kwargs: _launcher())
    monkeypatch.setattr(desktop_shell_app, "build_graph_view_shell_panel_contract", lambda *args, **kwargs: _graph_panel())
    monkeypatch.setattr(desktop_shell_app, "build_node_inspector_shell_panel_contract", lambda *args, **kwargs: _node_panel())
    monkeypatch.setattr(desktop_shell_app, "build_pulse_product_shell_panel_contract", lambda *args, **kwargs: _pulse_panel())
    monkeypatch.setattr(desktop_shell_app, "build_studio_approval_queue_panel_contract", lambda *args, **kwargs: _approval_queue_panel())
    monkeypatch.setattr(desktop_shell_app, "build_arsl_route_review_panel_contract", lambda *args, **kwargs: _arsl_route_review_panel())
    monkeypatch.setattr(desktop_shell_app, "build_studio_browser_runtime_operator_ui_readiness", lambda *args, **kwargs: _browser_runtime_panel())
    monkeypatch.setattr(desktop_shell_app, "build_canvas_panel_contract", lambda *args, **kwargs: _canvas_panel())
    plan = build_studio_desktop_shell_app_plan(vault, planning_mode="full", panel_timeout_seconds=0.1)

    def slow_rescan(vault_root: Path):
        Event().wait(0.5)
        return None

    monkeypatch.setattr(desktop_shell_app, "latest_static_graph_artifact", slow_rescan)
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        make_studio_desktop_shell_app_handler(vault, host="127.0.0.1", port=0, plan=plan),
    )
    host, port = server.server_address[:2]
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        started = monotonic()
        with urlopen(f"http://{host}:{port}/graph-view-static-artifact.html", timeout=2) as response:
            body = response.read().decode("utf-8", errors="replace")
        elapsed = monotonic() - started
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)

    assert elapsed < 0.3
    assert "<svg class='graph'>" in body


def test_run_panel_builder_hard_timeout_fails_open_without_waiting_for_return() -> None:
    never_finishes = Event()

    def slow_builder() -> dict:
        never_finishes.wait(5)
        return {"ok": True}

    started = monotonic()
    panel, status = desktop_shell_app._run_panel_builder(
        "slow-panel",
        "Slow Panel",
        "studio_slow_panel_contract",
        slow_builder,
        planning_mode="full",
        timeout_seconds=0.01,
    )
    elapsed = monotonic() - started

    assert elapsed < 0.5
    assert panel["ok"] is False
    assert panel["status"] == "SKIPPED TIMEOUT"
    assert status["state"] == "skipped_timeout"
    assert status["ready"] is False
    assert "hard timeout" in status["reason"]


def test_desktop_shell_smoke_full_plan_uses_hard_panel_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    _write_graph_artifact(vault)
    never_finishes = Event()

    def slow_runtime_builder(*args, **kwargs) -> dict:
        never_finishes.wait(5)
        return _contract()

    monkeypatch.setattr(desktop_shell_app, "build_runtime_cockpit_contract", slow_runtime_builder)
    monkeypatch.setattr(desktop_shell_app, "build_studio_app_launcher_plan", lambda *args, **kwargs: _launcher())
    monkeypatch.setattr(desktop_shell_app, "build_graph_view_shell_panel_contract", lambda *args, **kwargs: _graph_panel())
    monkeypatch.setattr(desktop_shell_app, "build_node_inspector_shell_panel_contract", lambda *args, **kwargs: _node_panel())
    monkeypatch.setattr(desktop_shell_app, "build_pulse_product_shell_panel_contract", lambda *args, **kwargs: _pulse_panel())
    monkeypatch.setattr(desktop_shell_app, "build_studio_approval_queue_panel_contract", lambda *args, **kwargs: _approval_queue_panel())
    monkeypatch.setattr(desktop_shell_app, "build_arsl_route_review_panel_contract", lambda *args, **kwargs: _arsl_route_review_panel())
    monkeypatch.setattr(desktop_shell_app, "build_studio_browser_runtime_operator_ui_readiness", lambda *args, **kwargs: _browser_runtime_panel())
    monkeypatch.setattr(desktop_shell_app, "build_canvas_panel_contract", lambda *args, **kwargs: _canvas_panel())

    started = monotonic()
    smoke = smoke_test_studio_desktop_shell_app(
        vault,
        port=0,
        timeout_seconds=2,
        planning_mode="full",
        panel_timeout_seconds=0.01,
    )
    elapsed = monotonic() - started

    assert elapsed < 0.8
    assert smoke["ok"] is True
    assert smoke["server_stopped"] is True
    shell_check = next(check for check in smoke["checks"] if check["route"] == "/shell.json")
    assert shell_check["ok"] is True


def test_desktop_shell_cli_smoke_full_plan_builds_once(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from runtime.cli import main as cli_main

    vault = _vault(tmp_path)
    _write_graph_artifact(vault)
    original_builder = desktop_shell_app.build_studio_desktop_shell_app_plan
    build_calls = []

    monkeypatch.setattr(desktop_shell_app, "build_runtime_cockpit_contract", lambda *args, **kwargs: _contract())
    monkeypatch.setattr(desktop_shell_app, "build_studio_app_launcher_plan", lambda *args, **kwargs: _launcher())
    monkeypatch.setattr(desktop_shell_app, "build_graph_view_shell_panel_contract", lambda *args, **kwargs: _graph_panel())
    monkeypatch.setattr(desktop_shell_app, "build_node_inspector_shell_panel_contract", lambda *args, **kwargs: _node_panel())
    monkeypatch.setattr(desktop_shell_app, "build_pulse_product_shell_panel_contract", lambda *args, **kwargs: _pulse_panel())
    monkeypatch.setattr(desktop_shell_app, "build_studio_approval_queue_panel_contract", lambda *args, **kwargs: _approval_queue_panel())
    monkeypatch.setattr(desktop_shell_app, "build_arsl_route_review_panel_contract", lambda *args, **kwargs: _arsl_route_review_panel())
    monkeypatch.setattr(desktop_shell_app, "build_studio_browser_runtime_operator_ui_readiness", lambda *args, **kwargs: _browser_runtime_panel())
    monkeypatch.setattr(desktop_shell_app, "build_canvas_panel_contract", lambda *args, **kwargs: _canvas_panel())

    def counted_builder(*args, **kwargs):
        build_calls.append(kwargs.get("planning_mode"))
        return original_builder(*args, **kwargs)

    monkeypatch.setattr(desktop_shell_app, "build_studio_desktop_shell_app_plan", counted_builder)

    result = cli_main.cmd_studio_desktop_shell_app(
        argparse.Namespace(
            vault_root=str(vault),
            host="127.0.0.1",
            port=8772,
            runtime_id=None,
            dry_run=False,
            smoke=True,
            qa_runner=False,
            planning_mode="full",
            use_requested_port=False,
            smoke_timeout=2.0,
            output_json=True,
            serve_seconds=None,
            write_qa_evidence=False,
            qa_evidence_slug=None,
        )
    )
    output = capsys.readouterr().out
    smoke = json.loads(output)

    assert result == 0
    assert smoke["ok"] is True
    assert build_calls == ["full"]


def test_desktop_shell_cli_full_dry_run_waits_for_readiness_proof(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from runtime.cli import main as cli_main

    vault = _vault(tmp_path)
    timeout_values = []

    def proof_builder(*args, **kwargs):
        timeout_values.append(kwargs.get("panel_timeout_seconds"))
        return {"ok": True, "planning": {"mode": kwargs.get("planning_mode")}, "url": "http://127.0.0.1:8772/"}

    monkeypatch.setattr(desktop_shell_app, "build_studio_desktop_shell_app_plan", proof_builder)

    result = cli_main.cmd_studio_desktop_shell_app(
        argparse.Namespace(
            vault_root=str(vault),
            host="127.0.0.1",
            port=8772,
            runtime_id=None,
            dry_run=True,
            smoke=False,
            qa_runner=False,
            planning_mode="full",
            use_requested_port=False,
            smoke_timeout=2.0,
            output_json=True,
            serve_seconds=None,
            write_qa_evidence=False,
            qa_evidence_slug=None,
        )
    )
    plan = json.loads(capsys.readouterr().out)

    assert result == 0
    assert plan["planning"]["mode"] == "full"
    assert timeout_values == [None]


def test_desktop_shell_lazy_server_full_plan_uses_hard_panel_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    never_finishes = Event()

    def slow_runtime_builder(*args, **kwargs) -> dict:
        never_finishes.wait(5)
        return _contract()

    monkeypatch.setattr(desktop_shell_app, "build_runtime_cockpit_contract", slow_runtime_builder)
    monkeypatch.setattr(desktop_shell_app, "build_studio_app_launcher_plan", lambda *args, **kwargs: _launcher())
    monkeypatch.setattr(desktop_shell_app, "build_graph_view_shell_panel_contract", lambda *args, **kwargs: _graph_panel())
    monkeypatch.setattr(desktop_shell_app, "build_node_inspector_shell_panel_contract", lambda *args, **kwargs: _node_panel())
    monkeypatch.setattr(desktop_shell_app, "build_pulse_product_shell_panel_contract", lambda *args, **kwargs: _pulse_panel())
    monkeypatch.setattr(desktop_shell_app, "build_studio_approval_queue_panel_contract", lambda *args, **kwargs: _approval_queue_panel())
    monkeypatch.setattr(desktop_shell_app, "build_arsl_route_review_panel_contract", lambda *args, **kwargs: _arsl_route_review_panel())
    monkeypatch.setattr(desktop_shell_app, "build_studio_browser_runtime_operator_ui_readiness", lambda *args, **kwargs: _browser_runtime_panel())
    monkeypatch.setattr(desktop_shell_app, "build_canvas_panel_contract", lambda *args, **kwargs: _canvas_panel())
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        make_studio_desktop_shell_app_handler(
            vault,
            host="127.0.0.1",
            port=0,
            planning_mode="full",
            panel_timeout_seconds=0.01,
        ),
    )
    host, port = server.server_address[:2]
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        started = monotonic()
        with urlopen(f"http://{host}:{port}/shell.json", timeout=2) as response:
            body = response.read().decode("utf-8")
        elapsed = monotonic() - started
        plan = json.loads(body)
        assert response.status == 200
        assert elapsed < 0.8
        assert plan["panel_statuses"]["runtime-cockpit"]["state"] == "skipped_timeout"
        assert plan["planning"]["panel_timeout_seconds"] == 0.01
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_desktop_shell_full_plan_hard_timeout_keeps_shell_ok(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    never_finishes = Event()

    def slow_runtime_builder(*args, **kwargs) -> dict:
        never_finishes.wait(5)
        return _contract()

    monkeypatch.setattr(desktop_shell_app, "build_runtime_cockpit_contract", slow_runtime_builder)
    monkeypatch.setattr(desktop_shell_app, "build_studio_app_launcher_plan", lambda *args, **kwargs: _launcher())
    monkeypatch.setattr(desktop_shell_app, "build_graph_view_shell_panel_contract", lambda *args, **kwargs: _graph_panel())
    monkeypatch.setattr(desktop_shell_app, "build_node_inspector_shell_panel_contract", lambda *args, **kwargs: _node_panel())
    monkeypatch.setattr(desktop_shell_app, "build_pulse_product_shell_panel_contract", lambda *args, **kwargs: _pulse_panel())
    monkeypatch.setattr(desktop_shell_app, "build_studio_approval_queue_panel_contract", lambda *args, **kwargs: _approval_queue_panel())
    monkeypatch.setattr(desktop_shell_app, "build_arsl_route_review_panel_contract", lambda *args, **kwargs: _arsl_route_review_panel())
    monkeypatch.setattr(desktop_shell_app, "build_studio_browser_runtime_operator_ui_readiness", lambda *args, **kwargs: _browser_runtime_panel())
    monkeypatch.setattr(desktop_shell_app, "build_canvas_panel_contract", lambda *args, **kwargs: _canvas_panel())

    started = monotonic()
    plan = build_studio_desktop_shell_app_plan(vault, panel_timeout_seconds=0.01)
    elapsed = monotonic() - started

    assert elapsed < 0.5
    assert plan["ok"] is True
    assert plan["panel_statuses"]["runtime-cockpit"]["state"] == "skipped_timeout"
    assert {view["id"]: view["status"] for view in plan["views"]}["runtime-cockpit"] == "skipped-timeout"
    assert plan["metrics"]["degraded_panel_count"] >= 1

def test_desktop_shell_full_plan_degrades_when_panel_builder_fails(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    monkeypatch.setattr(desktop_shell_app, "build_runtime_cockpit_contract", lambda *args, **kwargs: _contract())
    monkeypatch.setattr(desktop_shell_app, "build_studio_app_launcher_plan", lambda *args, **kwargs: _launcher())
    monkeypatch.setattr(desktop_shell_app, "build_graph_view_shell_panel_contract", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("graph too slow")))
    monkeypatch.setattr(desktop_shell_app, "build_node_inspector_shell_panel_contract", lambda *args, **kwargs: _node_panel())
    monkeypatch.setattr(desktop_shell_app, "build_pulse_product_shell_panel_contract", lambda *args, **kwargs: _pulse_panel())
    monkeypatch.setattr(desktop_shell_app, "build_studio_approval_queue_panel_contract", lambda *args, **kwargs: _approval_queue_panel())
    monkeypatch.setattr(desktop_shell_app, "build_arsl_route_review_panel_contract", lambda *args, **kwargs: _arsl_route_review_panel())
    monkeypatch.setattr(desktop_shell_app, "build_studio_browser_runtime_operator_ui_readiness", lambda *args, **kwargs: _browser_runtime_panel())

    plan = build_studio_desktop_shell_app_plan(vault)

    assert plan["ok"] is True
    assert plan["panel_statuses"]["graph-view"]["state"] == "degraded_error"
    assert "graph too slow" in plan["panel_statuses"]["graph-view"]["reason"]
    assert {view["id"]: view["status"] for view in plan["views"]}["graph-view"] == "degraded-error"
    assert plan["metrics"]["degraded_panel_count"] == 1


def test_desktop_shell_rejects_non_loopback_host(tmp_path: Path) -> None:
    vault = _vault(tmp_path)

    with pytest.raises(StudioDesktopShellAppError, match="loopback"):
        build_studio_desktop_shell_app_plan(vault, host="0.0.0.0")


def test_desktop_shell_html_renders_shell_without_script(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    monkeypatch.setattr(desktop_shell_app, "build_runtime_cockpit_contract", lambda *args, **kwargs: _contract())
    monkeypatch.setattr(desktop_shell_app, "build_studio_app_launcher_plan", lambda *args, **kwargs: _launcher())
    monkeypatch.setattr(desktop_shell_app, "build_graph_view_shell_panel_contract", lambda *args, **kwargs: _graph_panel())
    monkeypatch.setattr(desktop_shell_app, "build_node_inspector_shell_panel_contract", lambda *args, **kwargs: _node_panel())
    monkeypatch.setattr(desktop_shell_app, "build_pulse_product_shell_panel_contract", lambda *args, **kwargs: _pulse_panel())
    monkeypatch.setattr(desktop_shell_app, "build_studio_approval_queue_panel_contract", lambda *args, **kwargs: _approval_queue_panel())
    monkeypatch.setattr(desktop_shell_app, "build_arsl_route_review_panel_contract", lambda *args, **kwargs: _arsl_route_review_panel())
    monkeypatch.setattr(
        desktop_shell_app,
        "build_studio_browser_runtime_operator_ui_readiness",
        lambda *args, **kwargs: _browser_runtime_panel(),
    )
    monkeypatch.setattr(desktop_shell_app, "build_workspace_mode_studio_panel", lambda *args, **kwargs: _workspace_mode_panel())

    plan = build_studio_desktop_shell_app_plan(vault)
    html = render_studio_desktop_shell_app_html(plan)

    assert 'data-testid="studio-desktop-shell-root"' in html
    assert 'data-testid="desktop-nav-graph-view"' in html
    assert 'data-testid="desktop-nav-node-inspector"' in html
    assert 'data-testid="desktop-nav-runtime-cockpit"' in html
    assert 'data-testid="desktop-nav-pulse"' in html
    assert 'data-testid="desktop-nav-approval-queue"' in html
    assert 'data-testid="desktop-nav-arsl-route-review"' in html
    assert 'data-testid="desktop-nav-browser-runtime"' in html
    assert 'data-testid="desktop-nav-workspace-mode"' in html
    assert 'data-testid="runtime-cockpit-mount"' in html
    assert 'data-testid="graph-view-panel-mount"' in html
    assert 'data-testid="node-inspector-panel-mount"' in html
    assert 'data-testid="pulse-product-shell-mount"' in html
    assert 'data-testid="approval-queue-panel-mount"' in html
    assert 'data-testid="arsl-route-review-panel-mount"' in html
    assert 'data-testid="browser-runtime-panel-mount"' in html
    assert 'data-testid="workspace-mode-panel-mount"' in html
    assert "ChaseOS Studio MVP" in html
    assert "Product shell · governance-visible MVP" in html
    assert "Read-only Studio Shell MVP" in html
    assert "Governance color legend" in html
    assert "Desktop Shell Mock" not in html
    assert "read_only_desktop_shell_mock" not in html
    assert 'data-testid="studio-kpi-system-health"' in html
    assert 'data-testid="studio-kpi-approvals-pending"' in html
    assert "Source: plan.panel_statuses" in html
    assert "MVP proxy for personal-memory/operator-memory candidate load" in html
    assert "Mounted Views" not in html
    assert "Runtime Surfaces" not in html
    assert "Studio Graph View" in html
    assert "Node Inspector" in html
    assert "Alpha" in html
    assert "ChaseOS Pulse Product Shell" in html
    assert "Pulse Approval Queue" in html
    assert "ARSL Route Review" in html
    assert "Browser Runtime" in html
    assert "Workspace Mode" in html
    assert "studio_workspace_mode_panel" in html
    assert 'data-testid="workspace-mode-option-founder_venture"' in html
    assert 'data-testid="workspace-mode-section-founder_venture"' in html
    assert "Mode Selector" in html
    assert "Founder / Venture" in html
    assert "StrikeZone" in html
    assert "01_PROJECTS/StrikeZone/StrikeZone-OS.md" in html
    assert "workflow_not_allowed_by_explicit_profile" in html
    assert "Profile writes: false" in html
    assert "mvp_done_production_blocked" in html
    assert "Browser Use CLI" in html
    assert "browser.playwright.operator" in html
    assert "2026-05-03T09-39-25-844850Z-graph-view-static.html" in html
    assert 'src="/graph-view-static-artifact.html"' in html
    assert 'title="ChaseOS Studio Graph View" src="/graph-view-static-artifact.html" sandbox="" loading="eager"' in html
    assert "2026-05-03-pulse-product-shell.html" in html
    assert "2026-05-03-approval-queue.html" in html
    assert "writes_graph_index" in html
    assert "writes_node_ids" in html
    assert "edits_graph_nodes" in html
    assert "edits_inspected_node" in html
    assert "interactive_graph_controls_built" in html
    assert "submits_feedback" in html
    assert "executes_approvals" in html
    assert "applies_candidates" in html
    assert "activates_schedules" in html
    assert "executes_routes" in html
    assert "writes_routing_ledger" in html
    assert "mutates_gate_policy" in html
    assert "runs_browser_use_cli_live" in html
    assert "canonical_mutation_allowed" in html
    assert "Hermes" in html
    assert "Runtime Cockpit" in html
    assert "Runtime Startup Controls" in html
    assert "ChaseOS Pulse Approval Center" in html
    assert "chaseos studio approval-center-app" in html
    assert "chaseos studio runtime-cockpit-app" in html
    assert "full_desktop_shell_built" in html
    assert "approval_center_local_mount_built" in html
    assert "writes_host_startup" in html
    assert "mount-frame graph" in html
    assert "overflow-x: hidden" in html
    assert "@media (max-width: 900px)" in html
    assert "overflow-wrap: anywhere" in html
    assert "<script" not in html.lower()

    selected_html = render_studio_desktop_shell_app_html(plan, workspace_mode_selected_mode="founder_venture")
    assert "?wml_mode=founder_venture#workspace-mode" in selected_html
    assert 'data-testid="workspace-mode-option-all"' in selected_html
    assert 'data-testid="workspace-mode-option-founder_venture"' in selected_html
    assert 'data-testid="workspace-mode-section-founder_venture"' in selected_html
    assert 'data-testid="workspace-mode-section-runtime_agent_ops"' not in selected_html
    assert 'aria-current="true"' in selected_html
    assert "wml_mode" in selected_html
    assert "visible projects" in selected_html
    assert "<script" not in selected_html.lower()


def test_desktop_shell_smoke_starts_probes_and_stops(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    _write_graph_artifact(vault)
    monkeypatch.setattr(desktop_shell_app, "build_runtime_cockpit_contract", lambda *args, **kwargs: _contract())
    monkeypatch.setattr(desktop_shell_app, "build_studio_app_launcher_plan", lambda *args, **kwargs: _launcher())
    monkeypatch.setattr(desktop_shell_app, "build_graph_view_shell_panel_contract", lambda *args, **kwargs: _graph_panel())
    monkeypatch.setattr(desktop_shell_app, "build_node_inspector_shell_panel_contract", lambda *args, **kwargs: _node_panel())
    monkeypatch.setattr(desktop_shell_app, "build_pulse_product_shell_panel_contract", lambda *args, **kwargs: _pulse_panel())
    monkeypatch.setattr(desktop_shell_app, "build_studio_approval_queue_panel_contract", lambda *args, **kwargs: _approval_queue_panel())
    monkeypatch.setattr(desktop_shell_app, "build_arsl_route_review_panel_contract", lambda *args, **kwargs: _arsl_route_review_panel())
    monkeypatch.setattr(
        desktop_shell_app,
        "build_studio_browser_runtime_operator_ui_readiness",
        lambda *args, **kwargs: _browser_runtime_panel(),
    )
    monkeypatch.setattr(desktop_shell_app, "build_workspace_mode_studio_panel", lambda *args, **kwargs: _workspace_mode_panel())

    smoke = smoke_test_studio_desktop_shell_app(vault, port=0, timeout_seconds=2)

    assert smoke["ok"] is True
    assert smoke["mode"] == "bounded_http_smoke"
    assert smoke["server_stopped"] is True
    assert smoke["writes_performed"] is False
    checks = {check["route"]: check for check in smoke["checks"]}
    assert checks["/"]["shell_root_present"] is True
    assert checks["/"]["graph_mount_present"] is True
    assert checks["/"]["node_inspector_mount_present"] is True
    assert checks["/"]["arsl_route_review_mount_present"] is True
    assert checks["/"]["browser_runtime_mount_present"] is True
    assert checks["/"]["workspace_mode_mount_present"] is True
    assert checks["/"]["workspace_mode_route_present"] is True
    assert checks["/"]["graph_iframe_title_present"] is True
    assert checks["/"]["script_tags"] == 0
    assert checks["/graph-view-static-artifact.html"]["graph_svg_present"] is True
    assert checks["/graph-view-static-artifact.html"]["script_tags"] == 0
    assert checks["/graph-view-shell-panel.json"]["desktop_shell_mount_ready"] is True
    assert checks["/graph-view-shell-panel.json"]["writes_graph_index"] is False
    assert checks["/graph-view-shell-panel.json"]["writes_node_ids"] is False
    assert checks["/graph-view-shell-panel.json"]["canonical_mutation_allowed"] is False
    assert checks["/node-inspector-shell-panel.json"]["node_panel_ok"] is True
    assert checks["/node-inspector-shell-panel.json"]["selected_node_present"] is True
    assert checks["/node-inspector-shell-panel.json"]["writes_node_ids"] is False
    assert checks["/node-inspector-shell-panel.json"]["node_editing_allowed"] is False
    assert checks["/node-inspector-shell-panel.json"]["canonical_mutation_allowed"] is False
    assert checks["/arsl-route-review.json"]["arsl_panel_ok"] is True
    assert checks["/arsl-route-review.json"]["executes_routes"] is False
    assert checks["/arsl-route-review.json"]["writes_routing_ledger"] is False
    assert checks["/arsl-route-review.json"]["grants_approvals"] is False
    assert checks["/arsl-route-review.json"]["mutates_gate_policy"] is False
    assert checks["/arsl-route-review.json"]["browser_control_allowed"] is False
    assert checks["/arsl-route-review.json"]["canonical_mutation_allowed"] is False
    assert checks["/browser-runtime-panel.json"]["browser_runtime_panel_ok"] is True
    assert checks["/browser-runtime-panel.json"]["browser_runtime_required_sections_present"] is True
    assert checks["/browser-runtime-panel.json"]["read_only"] is True
    assert checks["/browser-runtime-panel.json"]["launches_browser"] is False
    assert checks["/browser-runtime-panel.json"]["connects_cdp"] is False
    assert checks["/browser-runtime-panel.json"]["runs_browser_use_cli_live"] is False
    assert checks["/browser-runtime-panel.json"]["canonical_mutation_allowed"] is False
    assert checks["/workspace-mode-panel.json"]["workspace_mode_panel_ok"] is True
    assert checks["/workspace-mode-panel.json"]["workspace_mode_panel_mounted"] is True
    assert checks["/workspace-mode-panel.json"]["read_only"] is True
    assert checks["/workspace-mode-panel.json"]["profile_writes_allowed"] is False
    assert checks["/workspace-mode-panel.json"]["workflow_execution_allowed"] is False
    assert checks["/workspace-mode-panel.json"]["agent_bus_dispatch_allowed"] is False
    assert checks["/workspace-mode-panel.json"]["canonical_mutation_allowed"] is False


def test_node_inspector_shell_panel_qa_runner_writes_bounded_evidence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    vault = _vault(tmp_path)
    _write_graph_artifact(vault)
    monkeypatch.setattr(desktop_shell_app, "build_runtime_cockpit_contract", lambda *args, **kwargs: _contract())
    monkeypatch.setattr(desktop_shell_app, "build_studio_app_launcher_plan", lambda *args, **kwargs: _launcher())
    monkeypatch.setattr(desktop_shell_app, "build_graph_view_shell_panel_contract", lambda *args, **kwargs: _graph_panel())
    monkeypatch.setattr(desktop_shell_app, "build_node_inspector_shell_panel_contract", lambda *args, **kwargs: _node_panel())
    monkeypatch.setattr(desktop_shell_app, "build_pulse_product_shell_panel_contract", lambda *args, **kwargs: _pulse_panel())
    monkeypatch.setattr(desktop_shell_app, "build_studio_approval_queue_panel_contract", lambda *args, **kwargs: _approval_queue_panel())
    monkeypatch.setattr(desktop_shell_app, "build_arsl_route_review_panel_contract", lambda *args, **kwargs: _arsl_route_review_panel())
    monkeypatch.setattr(
        desktop_shell_app,
        "build_studio_browser_runtime_operator_ui_readiness",
        lambda *args, **kwargs: _browser_runtime_panel(),
    )

    before = sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))
    qa = run_node_inspector_shell_panel_qa_runner(
        vault,
        timeout_seconds=2,
        write_evidence=True,
        evidence_slug="2026-05-04-node-inspector-shell-panel-qa-runner-test",
    )

    assert qa["ok"] is True
    assert qa["mode"] == "bounded_internal_http_qa_runner"
    assert qa["server_stopped"] is True
    assert qa["visual_browser_qa_complete"] is False
    assert qa["visual_screenshot_required"] is True
    assert qa["checks"]["node_inspector_mount_present"] is True
    assert qa["checks"]["node_inspector_route_present"] is True
    assert qa["checks"]["selected_node_present"] is True
    assert qa["checks"]["script_tags"] == 0
    assert qa["checks"]["writes_node_ids"] is False
    assert qa["checks"]["writes_graph_index"] is False
    assert qa["checks"]["node_editing_allowed"] is False
    assert qa["checks"]["canonical_mutation_allowed"] is False
    assert qa["evidence"]["written"] is True
    assert qa["evidence"]["json_path"] == (
        "07_LOGS/Studio-Graph-Views/2026-05-04-node-inspector-shell-panel-qa-runner-test.json"
    )
    assert qa["evidence"]["markdown_path"] == (
        "07_LOGS/Studio-Graph-Views/2026-05-04-node-inspector-shell-panel-qa-runner-test.md"
    )
    assert (vault / qa["evidence"]["json_path"]).is_file()
    assert (vault / qa["evidence"]["markdown_path"]).is_file()
    after = sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))
    assert sorted(set(after) - set(before)) == [
        "07_LOGS/Studio-Graph-Views/2026-05-04-node-inspector-shell-panel-qa-runner-test.json",
        "07_LOGS/Studio-Graph-Views/2026-05-04-node-inspector-shell-panel-qa-runner-test.md",
    ]


def test_desktop_shell_health_binds_before_plan_build(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    vault = _vault(tmp_path)

    def fail_plan(*args, **kwargs):
        raise AssertionError("full shell plan should not build for health")

    monkeypatch.setattr(desktop_shell_app, "build_studio_desktop_shell_app_plan", fail_plan)
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        make_studio_desktop_shell_app_handler(vault, host="127.0.0.1", port=0),
    )
    host, port = server.server_address[:2]
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(f"http://{host}:{port}/health.json", timeout=2) as response:
            body = response.read().decode("utf-8")
        assert response.status == 200
        assert '"plan_ready": false' in body
        assert '"read_only": true' in body
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_desktop_shell_static_graph_route_serves_before_plan_build(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    vault = _vault(tmp_path)
    _write_graph_artifact(vault)

    def fail_plan(*args, **kwargs):
        raise AssertionError("full shell plan should not build for static graph artifact")

    monkeypatch.setattr(desktop_shell_app, "build_studio_desktop_shell_app_plan", fail_plan)
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        make_studio_desktop_shell_app_handler(vault, host="127.0.0.1", port=0),
    )
    host, port = server.server_address[:2]
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(f"http://{host}:{port}/graph-view-static-artifact.html", timeout=2) as response:
            body = response.read().decode("utf-8")
        assert response.status == 200
        assert "<svg class='graph'>" in body
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_desktop_shell_bounded_serve_returns_without_request(tmp_path: Path) -> None:
    vault = _vault(tmp_path)

    serve_studio_desktop_shell_app(vault, port=0, serve_seconds=0.01)
