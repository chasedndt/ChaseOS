"""Tests for the Studio Workspace Mode panel."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio import workspace_mode_panel
from runtime.studio.workspace_mode_panel import build_workspace_mode_studio_panel


def test_workspace_mode_panel_mounts_readonly_studio_connections(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        workspace_mode_panel,
        "build_workspace_mode_product_status",
        lambda vault_root: {
            "status": "COMPLETE",
            "wml_product_feature_complete": True,
            "core_runtime": {"core_runtime_complete": True},
            "profile_coverage": {
                "profiles_valid_count": 6,
                "expected_profile_count": 6,
                "profile_coverage_complete": True,
            },
            "approval_ledger_summary": {"total_artifacts": 5},
            "blockers": [],
        },
    )
    monkeypatch.setattr(
        workspace_mode_panel,
        "build_workspace_mode_approval_ledger",
        lambda vault_root: {"total_artifacts": 5, "read_only": True},
    )
    monkeypatch.setattr(
        workspace_mode_panel,
        "build_project_workspace_view",
        lambda vault_root: {
            "surface": "studio_project_workspace",
            "panel_id": "project-workspace",
            "route_hint": "#project-workspace",
            "project_count": 2,
            "domain_count": 2,
            "projects": [
                {
                    "project": "StrikeZone",
                    "domain": "Products",
                    "status": "active",
                    "updated": "2026-05-14",
                    "file_name": "StrikeZone-OS.md",
                    "domain_folder": "StrikeZone",
                    "parse_error": False,
                },
                {
                    "project": "Degree OS",
                    "domain": "University",
                    "status": "active",
                    "updated": "2026-05-14",
                    "file_name": "Degree-OS.md",
                    "domain_folder": "University",
                    "parse_error": False,
                },
            ],
            "domains": [],
            "readiness": {"sprint_focus_available": True},
        },
    )

    def route_preview(*, workspace_path: str, workflow_id: str | None, adapter: str, vault_root: Path) -> dict:
        return {
            "workspace_mode": "runtime_agent_ops",
            "profile_source": "nearest-workspace-profile",
            "profile_source_path": f"{workspace_path}/.workspace-mode.yaml",
            "workflow_allowed_by_profile": workflow_id == "operator_today",
            "ready_for_aor_dispatch": workflow_id == "operator_today",
            "dispatch_blockers": [],
            "adapter_ceiling": "tier-2",
            "approval_mode": "explicit",
            "default_write_targets": [],
        }

    monkeypatch.setattr(workspace_mode_panel, "build_aor_workspace_route_preview", route_preview)

    panel = build_workspace_mode_studio_panel(tmp_path)

    assert panel["ok"] is True
    assert panel["surface"] == "studio_workspace_mode_panel"
    assert panel["native_panel"]["panel_id"] == "workspace-mode"
    assert panel["native_panel"]["connected_surfaces"] == ["studio-dashboard", "project-workspace", "chat"]
    assert panel["summary"]["overall_status"] == "COMPLETE"
    assert panel["summary"]["profile_valid_count"] == 6
    assert panel["summary"]["profile_total_count"] == 6
    assert panel["summary"]["route_ready_count"] == 5
    assert panel["summary"]["approval_artifact_count"] == 5
    assert panel["summary"]["mode_option_count"] == 6
    assert panel["mode_selector"]["render_mode"] == "read-only-url-state-tabs"
    assert panel["mode_selector"]["selection_persists"] is True
    assert panel["mode_selector"]["query_param"] == "wml_mode"
    assert panel["mode_selector"]["selected_mode"] == "all"
    assert [item["id"] for item in panel["mode_options"]] == [
        "personal_os",
        "study_research",
        "founder_venture",
        "business_ops",
        "runtime_agent_ops",
        "unknown",
    ]
    assert {item["project"]: item["mode"] for item in panel["project_cards"]} == {
        "StrikeZone": "founder_venture",
        "Degree OS": "study_research",
    }
    assert panel["project_workspace_connection"]["projects"][0]["workspace_path"] == "01_PROJECTS/StrikeZone/StrikeZone-OS.md"
    assert panel["project_workspace_connection"]["mounted"] is True
    assert panel["chat_connection"]["context_visible"] is True
    assert panel["chat_connection"]["chat_can_execute_workspace_mode"] is False
    assert panel["authority"]["read_only"] is True
    assert panel["authority"]["profile_writes_allowed"] is False
    assert panel["authority"]["workflow_execution_allowed"] is False
    assert panel["authority"]["agent_bus_dispatch_allowed"] is False
    assert panel["authority"]["canonical_mutation_allowed"] is False
    assert panel["possible_writes"] == []
    assert panel["readiness"]["workspace_mode_panel_mounted"] is True
    assert panel["readiness"]["selector_state_contract_ready"] is True
    json.dumps(panel)


def test_workspace_mode_panel_filters_selected_mode_url_state(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        workspace_mode_panel,
        "build_workspace_mode_product_status",
        lambda vault_root: {
            "status": "COMPLETE",
            "wml_product_feature_complete": True,
            "core_runtime": {"core_runtime_complete": True},
            "profile_coverage": {
                "profiles_valid_count": 6,
                "expected_profile_count": 6,
                "profile_coverage_complete": True,
            },
            "blockers": [],
        },
    )
    monkeypatch.setattr(workspace_mode_panel, "build_workspace_mode_approval_ledger", lambda vault_root: {"total_artifacts": 0})
    monkeypatch.setattr(
        workspace_mode_panel,
        "build_project_workspace_view",
        lambda vault_root: {
            "surface": "studio_project_workspace",
            "panel_id": "project-workspace",
            "route_hint": "#project-workspace",
            "project_count": 2,
            "domain_count": 2,
            "projects": [
                {
                    "project": "StrikeZone",
                    "domain": "Products",
                    "status": "active",
                    "file_name": "StrikeZone-OS.md",
                    "domain_folder": "StrikeZone",
                },
                {
                    "project": "Degree OS",
                    "domain": "University",
                    "status": "active",
                    "file_name": "Degree-OS.md",
                    "domain_folder": "University",
                },
            ],
            "readiness": {},
        },
    )
    monkeypatch.setattr(
        workspace_mode_panel,
        "build_aor_workspace_route_preview",
        lambda **kwargs: {
            "workspace_mode": "unknown",
            "profile_source_path": None,
            "workflow_allowed_by_profile": False,
            "ready_for_aor_dispatch": False,
            "dispatch_blockers": ["workflow_not_allowed_by_explicit_profile"],
        },
    )

    panel = build_workspace_mode_studio_panel(tmp_path, selected_mode="founder-venture")

    assert panel["mode_selector"]["selected_mode"] == "founder_venture"
    assert panel["mode_selector"]["selected_mode_label"] == "Founder / Venture"
    assert panel["mode_selector"]["selection_persists"] is True
    assert panel["mode_selector"]["persistence_scope"] == "url_query"
    assert panel["selected_mode"]["visible_project_count"] == 1
    assert [item["project"] for item in panel["visible_project_cards"]] == ["StrikeZone"]
    assert [item["id"] for item in panel["visible_mode_options"]] == ["founder_venture"]
    assert next(item for item in panel["mode_selector"]["options"] if item["id"] == "founder_venture")["selected"] is True
    assert next(item for item in panel["mode_selector"]["options"] if item["id"] == "founder_venture")["url"] == "?wml_mode=founder_venture#workspace-mode"

    invalid = build_workspace_mode_studio_panel(tmp_path, selected_mode="not-a-mode")
    assert invalid["mode_selector"]["selected_mode"] == "all"
    assert invalid["mode_selector"]["selected_mode_valid"] is False
    assert "invalid_wml_mode_query_fell_back_to_all" in invalid["warnings"]
