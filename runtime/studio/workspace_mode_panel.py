"""Read-only Studio Workspace Mode Layer panel.

This panel brings WML into Studio as an operator-facing product surface. It
reads WML product status, approval ledger, and route previews, then connects
that state to the Project Workspace and Chat surfaces without granting write,
approval-consumption, Agent Bus, workflow, provider, browser, or canonical
authority.
"""

from __future__ import annotations

from datetime import datetime, timezone
from copy import deepcopy
from pathlib import Path
from typing import Any

from runtime.studio.project_workspace_view import build_project_workspace_view
from runtime.workspace_modes.aor_routing_preview import build_aor_workspace_route_preview
from runtime.workspace_modes.inference import infer_workspace_mode
from runtime.workspace_modes.product_status import (
    build_workspace_mode_approval_ledger,
    build_workspace_mode_product_status,
)


MODEL_VERSION = "studio.workspace_mode_panel.v1"
SURFACE_ID = "studio_workspace_mode_panel"
PANEL_ID = "workspace-mode"
FRONTEND_TARGET = "panel-workspace-mode"
ROUTE_HINT = "#workspace-mode"
NEXT_RECOMMENDED_PASS = "workspace-mode-studio-selector-state-contract"
MODE_QUERY_PARAM = "wml_mode"
ALL_MODES_ID = "all"

MODE_CATALOG: tuple[dict[str, str], ...] = (
    {
        "id": "personal_os",
        "label": "Personal OS",
        "purpose": "Personal life, goals, doctrine, routines, journaling, planning, and private knowledge.",
        "default_posture": "Conservative private-context inspection; no durable writeback from Studio.",
    },
    {
        "id": "study_research",
        "label": "Study / Research",
        "purpose": "University, research, lectures, PDFs, labs, revision, and evidence synthesis.",
        "default_posture": "Source and provenance first; citation context visible before workflow execution.",
    },
    {
        "id": "founder_venture",
        "label": "Founder / Venture",
        "purpose": "Startups, products, R&D, market research, roadmap proposals, and experiments.",
        "default_posture": "Strict project and roadmap truth; proposals remain inspect-only in Studio.",
    },
    {
        "id": "business_ops",
        "label": "Business Ops",
        "purpose": "SOPs, customer/process operations, fulfillment, support drafts, and audit packets.",
        "default_posture": "No external sends or customer-impacting actions from this surface.",
    },
    {
        "id": "runtime_agent_ops",
        "label": "Runtime / Agent Ops",
        "purpose": "ChaseOS runtime governance, AOR, OpenClaw, Hermes, Codex, policies, workflows, and logs.",
        "default_posture": "Very strict; preview routes only, no Agent Bus dispatch or canonical mutation.",
    },
    {
        "id": "unknown",
        "label": "Unknown",
        "purpose": "Fallback for paths without enough context to classify safely.",
        "default_posture": "Fail closed; inspect, summarize, propose a mode, or ask the operator.",
    },
)

_MODE_BY_ID = {item["id"]: item for item in MODE_CATALOG}
_VALID_SELECTIONS = {ALL_MODES_ID, *[item["id"] for item in MODE_CATALOG]}

_DEFAULT_ROUTE_CONTEXTS: tuple[dict[str, str], ...] = (
    {
        "id": "runtime_operator_today",
        "label": "Runtime operations",
        "workspace_path": "runtime/aor/engine.py",
        "workflow_id": "operator_today",
        "adapter": "codex",
    },
    {
        "id": "founder_venture_operator_today",
        "label": "Founder / venture",
        "workspace_path": "01_PROJECTS/StrikeZone/StrikeZone-OS.md",
        "workflow_id": "operator_today",
        "adapter": "codex",
    },
    {
        "id": "business_ops_operator_today",
        "label": "Business ops",
        "workspace_path": "04_SOPS/Build-Log-SOP.md",
        "workflow_id": "operator_today",
        "adapter": "codex",
    },
    {
        "id": "study_research_operator_today",
        "label": "Study/research",
        "workspace_path": "01_PROJECTS/University/Degree-OS.md",
        "workflow_id": "operator_today",
        "adapter": "codex",
    },
    {
        "id": "personal_os_operator_today",
        "label": "Personal OS",
        "workspace_path": "00_HOME/Now.md",
        "workflow_id": "operator_today",
        "adapter": "codex",
    },
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _authority() -> dict[str, Any]:
    return {
        "read_only": True,
        "writes_vault": False,
        "writes_profiles": False,
        "writes_approval_artifacts": False,
        "consumes_approvals": False,
        "executes_workflows": False,
        "dispatches_aor": False,
        "writes_agent_bus_tasks": False,
        "provider_calls_allowed": False,
        "browser_control_allowed": False,
        "external_actions_allowed": False,
        "canonical_mutation_allowed": False,
        "project_status_mutation_allowed": False,
        "chat_execution_allowed": False,
        "profile_writes_allowed": False,
        "workflow_execution_allowed": False,
        "agent_bus_dispatch_allowed": False,
    }


def _route_card(vault: Path, context: dict[str, str]) -> dict[str, Any]:
    inferred_mode = infer_workspace_mode(context["workspace_path"], vault_root=vault)
    preview = build_aor_workspace_route_preview(
        workspace_path=context["workspace_path"],
        workflow_id=context.get("workflow_id"),
        adapter=context.get("adapter", "codex"),
        vault_root=vault,
    )
    return {
        "id": context["id"],
        "label": context["label"],
        "workspace_path": context["workspace_path"],
        "path": context["workspace_path"],
        "workflow_id": context.get("workflow_id"),
        "adapter": context.get("adapter", "codex"),
        "workspace_mode": preview.get("workspace_mode"),
        "routing_workspace_mode": preview.get("workspace_mode"),
        "inferred_workspace_mode": inferred_mode,
        "mode": inferred_mode if preview.get("workspace_mode") == "unknown" and inferred_mode != "unknown" else preview.get("workspace_mode"),
        "profile_source": preview.get("profile_source"),
        "profile_source_path": preview.get("profile_source_path"),
        "profile_path": preview.get("profile_source_path"),
        "workflow_allowed_by_profile": bool(preview.get("workflow_allowed_by_profile")),
        "ready_for_aor_dispatch": bool(preview.get("ready_for_aor_dispatch")),
        "ready": bool(preview.get("ready_for_aor_dispatch")),
        "dispatch_blockers": list(preview.get("dispatch_blockers") or []),
        "blockers": list(preview.get("dispatch_blockers") or []),
        "adapter_ceiling": preview.get("adapter_ceiling"),
        "approval_mode": preview.get("approval_mode"),
        "default_write_targets": list(preview.get("default_write_targets") or []),
        "preview": preview,
    }


def _mode_anchor(mode_id: str) -> str:
    return f"workspace-mode-mode-{mode_id.replace('_', '-')}"


def _normalize_selected_mode(selected_mode: str | None) -> tuple[str, bool]:
    if not selected_mode:
        return ALL_MODES_ID, False
    normalized = selected_mode.strip().lower().replace("-", "_")
    if normalized in _VALID_SELECTIONS:
        return normalized, False
    return ALL_MODES_ID, True


def _project_workspace_path(project: dict[str, Any]) -> str:
    domain_folder = str(project.get("domain_folder") or project.get("domain") or "unknown").strip() or "unknown"
    file_name = str(project.get("file_name") or "").strip()
    if not file_name:
        project_name = str(project.get("project") or domain_folder).strip() or domain_folder
        file_name = f"{project_name.replace(' ', '-')}-OS.md"
    return f"01_PROJECTS/{domain_folder}/{file_name}"


def _project_card(vault: Path, project: dict[str, Any]) -> dict[str, Any]:
    workspace_path = _project_workspace_path(project)
    mode = infer_workspace_mode(workspace_path, vault_root=vault)
    mode_info = _MODE_BY_ID.get(mode, _MODE_BY_ID["unknown"])
    return {
        "project": project.get("project") or project.get("domain_folder") or "unknown",
        "domain": project.get("domain") or "unknown",
        "status": project.get("status") or "unknown",
        "updated": project.get("updated"),
        "file_name": project.get("file_name"),
        "domain_folder": project.get("domain_folder"),
        "workspace_path": workspace_path,
        "workspace_mode": mode,
        "mode": mode,
        "mode_label": mode_info["label"],
        "mode_anchor": _mode_anchor(mode),
        "read_only": True,
        "parse_error": bool(project.get("parse_error")),
    }


def _domain_cards(project_cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    domains: dict[str, dict[str, Any]] = {}
    for project in project_cards:
        key = str(project.get("domain") or "unknown")
        bucket = domains.setdefault(
            key,
            {
                "domain": key,
                "project_count": 0,
                "projects": [],
                "mode_counts": {item["id"]: 0 for item in MODE_CATALOG},
                "primary_mode": "unknown",
                "primary_mode_label": _MODE_BY_ID["unknown"]["label"],
            },
        )
        bucket["projects"].append(project)
        bucket["project_count"] += 1
        mode = str(project.get("mode") or "unknown")
        bucket["mode_counts"][mode] = int(bucket["mode_counts"].get(mode, 0)) + 1

    cards = []
    for card in domains.values():
        primary_mode = max(card["mode_counts"].items(), key=lambda item: item[1])[0]
        card["primary_mode"] = primary_mode
        card["primary_mode_label"] = _MODE_BY_ID.get(primary_mode, _MODE_BY_ID["unknown"])["label"]
        cards.append(card)
    return sorted(cards, key=lambda item: (item["domain"].lower(), item["primary_mode"]))


def _mode_options(project_cards: list[dict[str, Any]], domain_cards: list[dict[str, Any]], route_cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    options: list[dict[str, Any]] = []
    for mode_info in MODE_CATALOG:
        mode_id = mode_info["id"]
        projects = [item for item in project_cards if item.get("mode") == mode_id]
        domains = [
            item
            for item in domain_cards
            if item.get("primary_mode") == mode_id or int((item.get("mode_counts") or {}).get(mode_id, 0)) > 0
        ]
        routes = [item for item in route_cards if item.get("mode") == mode_id]
        options.append(
            {
                **mode_info,
                "anchor": _mode_anchor(mode_id),
                "project_count": len(projects),
                "domain_count": len(domains),
                "route_count": len(routes),
                "ready_route_count": sum(1 for item in routes if item.get("ready")),
                "blocked_route_count": sum(1 for item in routes if not item.get("ready")),
                "projects": projects,
                "domains": domains,
                "routes": routes,
                "selectable": True,
                "read_only": True,
            }
        )
    return options


def _with_selected_mode(panel: dict[str, Any], selected_mode: str | None) -> dict[str, Any]:
    selected, invalid = _normalize_selected_mode(selected_mode)
    panel = deepcopy(panel)
    mode_options = list(panel.get("mode_options") or [])
    project_cards = list(panel.get("project_cards") or [])
    domain_cards = list(panel.get("domain_cards") or [])
    route_cards = list(panel.get("route_cards") or [])
    selected_option = next((item for item in mode_options if item.get("id") == selected), None)
    selected_label = "All Modes" if selected == ALL_MODES_ID else (selected_option or {}).get("label") or selected
    visible_modes = mode_options if selected == ALL_MODES_ID else [item for item in mode_options if item.get("id") == selected]
    visible_projects = project_cards if selected == ALL_MODES_ID else [item for item in project_cards if item.get("mode") == selected]
    visible_domains = (
        domain_cards
        if selected == ALL_MODES_ID
        else [
            item
            for item in domain_cards
            if item.get("primary_mode") == selected or int((item.get("mode_counts") or {}).get(selected, 0)) > 0
        ]
    )
    visible_routes = route_cards if selected == ALL_MODES_ID else [item for item in route_cards if item.get("mode") == selected]
    all_mode_option = {
        "id": ALL_MODES_ID,
        "label": "All Modes",
        "purpose": "Show every WML mode, project/domain group, and route preview.",
        "default_posture": "Read-only overview across all Workspace Mode contexts.",
        "anchor": "workspace-mode",
        "project_count": len(project_cards),
        "domain_count": len(domain_cards),
        "route_count": len(route_cards),
        "ready_route_count": sum(1 for item in route_cards if item.get("ready")),
        "blocked_route_count": sum(1 for item in route_cards if not item.get("ready")),
        "projects": project_cards,
        "domains": domain_cards,
        "routes": route_cards,
        "selectable": True,
        "read_only": True,
    }
    selection_options = [all_mode_option, *mode_options]
    for option in selection_options:
        option["selected"] = option.get("id") == selected
        option["url"] = (
            "#workspace-mode"
            if option.get("id") == ALL_MODES_ID
            else f"?{MODE_QUERY_PARAM}={option.get('id')}#workspace-mode"
        )

    panel["mode_selector"] = {
        **(panel.get("mode_selector") or {}),
        "render_mode": "read-only-url-state-tabs",
        "query_param": MODE_QUERY_PARAM,
        "default_mode": ALL_MODES_ID,
        "selected_mode": selected,
        "selected_mode_label": selected_label,
        "selected_mode_valid": not invalid,
        "invalid_requested_mode": selected_mode if invalid else None,
        "selection_persists": True,
        "persistence_scope": "url_query",
        "profile_writes_allowed": False,
        "workflow_execution_allowed": False,
        "options": selection_options,
    }
    panel["selected_mode"] = {
        "mode": selected,
        "label": selected_label,
        "valid": not invalid,
        "query_param": MODE_QUERY_PARAM,
        "visible_mode_count": len(visible_modes),
        "visible_project_count": len(visible_projects),
        "visible_domain_count": len(visible_domains),
        "visible_route_count": len(visible_routes),
        "visible_ready_route_count": sum(1 for item in visible_routes if item.get("ready")),
    }
    panel["visible_mode_options"] = visible_modes
    panel["visible_project_cards"] = visible_projects
    panel["visible_domain_cards"] = visible_domains
    panel["visible_route_cards"] = visible_routes
    panel["summary"] = {
        **(panel.get("summary") or {}),
        "selected_mode": selected,
        "selected_mode_label": selected_label,
        "selected_mode_valid": not invalid,
        "visible_project_count": len(visible_projects),
        "visible_domain_count": len(visible_domains),
        "visible_route_count": len(visible_routes),
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }
    readiness = panel.get("readiness") or {}
    readiness["selector_state_contract_ready"] = True
    readiness["selector_state_persistence"] = "url_query"
    readiness["selected_mode_valid"] = not invalid
    readiness["next_recommended_pass"] = NEXT_RECOMMENDED_PASS
    panel["readiness"] = readiness
    if invalid:
        warnings = list(panel.get("warnings") or [])
        warnings.append("invalid_wml_mode_query_fell_back_to_all")
        panel["warnings"] = warnings
    return panel


def apply_workspace_mode_selection(panel: dict[str, Any], selected_mode: str | None = None) -> dict[str, Any]:
    """Return a read-only panel copy with URL-state mode selection applied."""

    return _with_selected_mode(panel, selected_mode)


def build_workspace_mode_studio_panel(
    vault_root: str | Path,
    *,
    route_contexts: list[dict[str, str]] | None = None,
    selected_mode: str | None = None,
) -> dict[str, Any]:
    """Return the read-only WML Studio panel model."""

    vault = Path(vault_root).resolve()
    product_status = build_workspace_mode_product_status(vault_root=vault)
    approval_ledger = build_workspace_mode_approval_ledger(vault_root=vault)
    project_workspace = build_project_workspace_view(vault)
    contexts = route_contexts if route_contexts is not None else [dict(item) for item in _DEFAULT_ROUTE_CONTEXTS]
    route_cards = [_route_card(vault, item) for item in contexts]
    project_cards = [_project_card(vault, item) for item in list(project_workspace.get("projects") or [])]
    domain_cards = _domain_cards(project_cards)
    mode_options = _mode_options(project_cards, domain_cards, route_cards)
    ready_count = sum(1 for item in route_cards if item["ready_for_aor_dispatch"])
    blocked_count = len(route_cards) - ready_count
    profile_coverage = product_status.get("profile_coverage") or {}
    ledger_summary = product_status.get("approval_ledger_summary") or {}
    blockers = list(product_status.get("blockers") or [])

    panel = {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "native_panel": {
            "mounted": True,
            "panel_id": PANEL_ID,
            "frontend_target": FRONTEND_TARGET,
            "route_hint": ROUTE_HINT,
            "read_only": True,
            "status": "mounted-read-only",
            "connected_surfaces": ["studio-dashboard", "project-workspace", "chat"],
        },
        "summary": {
            "overall_status": product_status.get("status"),
            "wml_product_feature_complete": bool(product_status.get("wml_product_feature_complete")),
            "core_runtime_complete": bool((product_status.get("core_runtime") or {}).get("core_runtime_complete")),
            "profiles_valid_count": int(profile_coverage.get("profiles_valid_count") or 0),
            "expected_profile_count": int(profile_coverage.get("expected_profile_count") or 0),
            "profile_valid_count": int(profile_coverage.get("profiles_valid_count") or 0),
            "profile_total_count": int(profile_coverage.get("expected_profile_count") or 0),
            "profile_coverage_complete": bool(profile_coverage.get("profile_coverage_complete")),
            "approval_artifact_count": int(approval_ledger.get("total_artifacts") or 0),
            "route_context_count": len(route_cards),
            "route_ready_count": ready_count,
            "route_blocked_count": blocked_count,
            "project_count": int(project_workspace.get("project_count") or 0),
            "domain_count": int(project_workspace.get("domain_count") or 0),
            "mode_option_count": len(mode_options),
            "selectable_mode_count": len([item for item in mode_options if item.get("selectable")]),
            "project_mode_count": len({item.get("mode") for item in project_cards if item.get("mode")}),
            "manual_testing_ready": product_status.get("status") == "COMPLETE" and not blockers,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "product_status": product_status,
        "approval_ledger": approval_ledger,
        "route_cards": route_cards,
        "mode_selector": {
            "render_mode": "read-only-anchor-tabs",
            "default_mode": "runtime_agent_ops",
            "selected_mode": "runtime_agent_ops",
            "selection_persists": False,
            "profile_writes_allowed": False,
            "workflow_execution_allowed": False,
            "options": mode_options,
        },
        "mode_options": mode_options,
        "project_cards": project_cards,
        "domain_cards": domain_cards,
        "project_workspace_connection": {
            "surface": project_workspace.get("surface"),
            "panel_id": project_workspace.get("panel_id"),
            "route_hint": project_workspace.get("route_hint"),
            "mounted": True,
            "source": "runtime.studio.project_workspace_view.build_project_workspace_view",
            "project_count": project_workspace.get("project_count"),
            "domain_count": project_workspace.get("domain_count"),
            "projects": project_cards,
            "domains": domain_cards,
            "sprint_focus_available": (project_workspace.get("readiness") or {}).get("sprint_focus_available"),
            "read_only": True,
        },
        "chat_connection": {
            "surface": "phase11_chat_panel_readonly_contract",
            "context_visible": True,
            "visible_in_chat_context": True,
            "suggested_slash_commands": ["/runtime status", "/dashboard"],
            "chat_can_explain_wml": True,
            "chat_can_execute_wml": False,
            "chat_can_execute_workspace_mode": False,
            "chat_can_write_profiles": False,
            "chat_can_write_workspace_profiles": False,
            "chat_can_consume_approvals": False,
        },
        "authority": _authority(),
        "allowed_actions": ["inspect-workspace-mode-panel", "preview-workspace-route"],
        "possible_writes": [],
        "readiness": {
            "workspace_mode_panel_mounted": True,
            "dashboard_connection_ready": True,
            "project_workspace_connection_ready": True,
            "chat_context_connection_ready": True,
            "product_status_visible": True,
            "approval_ledger_visible": True,
            "route_previews_visible": True,
            "manual_testing_ready": product_status.get("status") == "COMPLETE" and not blockers,
            "no_profile_write_authority": True,
            "no_workflow_execution_authority": True,
            "no_approval_consumption_authority": True,
            "no_agent_bus_task_write": True,
            "no_canonical_mutation": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "warnings": blockers,
    }
    return _with_selected_mode(panel, selected_mode)
