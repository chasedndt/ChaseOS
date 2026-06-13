"""Rendered visual QA for final Studio productization pages.

This harness opens the production Studio frontend with mocked local
``pywebview.api`` responses sourced from ``StudioAPI``. It captures desktop and
mobile screenshots for Chat, Workspaces, Missions, Extensions, Content,
Personal Memory, Graph Hygiene, Tasks & Runs, Agents / Runtimes, Agent Bus,
Schedules, copy polish, sidebar collapse, and route hygiene without provider calls,
runtime dispatch, browser control authority,
approval consumption, graph mutation, memory mutation, or installer/startup
mutation.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any


MODEL_VERSION = "studio.final_productization_visual_qa.v1"
SURFACE_ID = "studio_final_productization_visual_qa"
STATUS = "COMPLETE / RENDERED VISUAL QA / MOCKED LOCAL API / NO AUTHORITY EXPANSION"
DEFAULT_OUTPUT_DIR = Path("07_LOGS") / "Visual-QA" / "2026-05-28-studio-ui-product-copy-shell-spawn-polish"

PANELS = (
    {
        "id": "dashboard",
        "hash": "#/dashboard",
        "name": "Home",
        "selector": ".home-layout",
        "tokens": (
            "Home",
            "Quick Launch",
            "Active Runs",
            "Approvals",
            "Recent Chats",
        ),
    },
    {
        "id": "chat",
        "hash": "#/chat",
        "name": "Chat",
        "selector": ".phase11-chat-product-desk",
        "tokens": (
            "CHAT",
            "Runtime Chats",
            "+ Folder",
            "No messages yet",
            "Connected",
            "Send",
        ),
    },
    {
        "id": "project-workspace",
        "hash": "#/project-workspace",
        "name": "Workspaces",
        "selector": ".workspace-hub-hero",
        "tokens": (
            "WORKSPACE HUB",
            "Workspace Operating Context",
            "Workspace Readiness",
            "Current Sprint Focus",
            "Workspace Domains",
            "Open Tasks",
        ),
    },
    {
        "id": "workflow-packs",
        "hash": "#/workflow-packs",
        "name": "Missions",
        "selector": ".workflow-packs-context-panel",
        "tokens": (
            "Missions",
            "Mission Operating Context",
            "Mission Readiness",
            "Mission Pack Coverage",
            "Visual Product & Creative Studio",
            "Local only",
        ),
    },
    {
        "id": "chaser-forge",
        "hash": "#/chaser-forge",
        "name": "Extensions",
        "selector": ".chaser-forge-context-panel",
        "tokens": (
            "Extensions",
            "Extension Operating Context",
            "Extension Readiness",
            "Extension Capability Coverage",
            "Local Marketplace Library",
            "Local only",
        ),
    },
    {
        "id": "graph",
        "hash": "#/graph",
        "name": "Graph",
        "selector": "#panel-graph.active",
        "tokens": (
            "Graph",
            "Local Graph",
            "Filters",
            "Docs / Inspector",
        ),
    },
    {
        "id": "node-inspector",
        "hash": "#/node-inspector",
        "name": "Docs / Inspector",
        "selector": "#panel-node-inspector.active",
        "tokens": (
            "Docs / Inspector",
            "formatted Markdown",
            "Backlinks",
            "Provenance",
        ),
    },
    {
        "id": "graph-hygiene",
        "hash": "#/graph-hygiene",
        "name": "Graph Hygiene",
        "selector": ".graph-hygiene-hero",
        "tokens": (
            "GRAPH REVIEW WORKSPACE",
            "Review Queue",
            "Latest Scan",
            "Open Decision Drafts",
        ),
    },
    {
        "id": "provenance-explorer",
        "hash": "#/provenance-explorer",
        "name": "Provenance",
        "selector": "#panel-provenance-explorer.active",
        "tokens": (
            "Provenance Explorer",
            "No provenance records",
            "Details",
        ),
    },
    {
        "id": "app-launcher",
        "hash": "#/app-launcher",
        "name": "App Launcher",
        "selector": "#panel-app-launcher.active",
        "tokens": (
            "App Launcher",
            "Discover Studio pages",
            "Discovery",
            "Routes",
            "Review only",
        ),
    },
    {
        "id": "browser-runtime",
        "hash": "#/browser-runtime",
        "name": "Browser Runtime",
        "selector": "#panel-browser-runtime.active",
        "tokens": (
            "Browser Runtime",
            "Inspect browser automation readiness",
            "No browser control",
            "Authority",
        ),
    },
    {
        "id": "workspace-entry",
        "hash": "#/workspace-entry",
        "name": "Workspace Entry",
        "selector": "#panel-workspace-entry.active",
        "tokens": (
            "Workspace Entry",
            "Workspace detection",
            "No automatic migration",
            "Current workspace",
        ),
    },
    {
        "id": "settings",
        "hash": "#/settings",
        "name": "Settings",
        "selector": "#panel-settings.active",
        "tokens": (
            "Settings",
            "Local configuration posture",
            "Runtime Controls",
            "AI Providers",
        ),
    },
    {
        "id": "approval-center",
        "hash": "#/approval-center",
        "name": "Approvals",
        "selector": "#panel-approval-center.active",
        "tokens": (
            "Approvals",
            "Review governed requests",
            "Queue",
            "Decisions",
            "Decide in flow",
        ),
    },
    {
        "id": "agent-identity",
        "hash": "#/agent-identity",
        "name": "Agent Identity",
        "selector": "#panel-agent-identity.active",
        "tokens": (
            "Agent Identity",
            "Identity",
        ),
    },
    {
        "id": "runtime-navigation",
        "hash": "#/runtime-navigation",
        "name": "Runtime Navigation",
        "selector": "#panel-runtime-navigation.active",
        "tokens": (
            "Runtime Navigation Map",
            "Runtime read routes",
            "No routing change",
        ),
    },
    {
        "id": "runtime-support-loops",
        "hash": "#/runtime-support-loops",
        "name": "Support Loops",
        "selector": "#panel-runtime-support-loops.active",
        "tokens": (
            "Support Loops",
            "Support loops suggest and verify",
            "Suggest only",
            "Review only",
        ),
    },
    {
        "id": "intake",
        "hash": "#/intake",
        "name": "Intake",
        "selector": ".intake-panel",
        "tokens": (
            "Intake",
            "New captures",
            "Duplicate protection",
            "Approval required",
            "Review inbox",
        ),
    },
    {
        "id": "capture-markdown",
        "hash": "#/capture-markdown",
        "name": "Capture",
        "selector": ".capture-markdown-panel",
        "tokens": (
            "Capture",
            "CAPTURE",
            "Review",
            "Recent Captures",
            "No auto-run",
        ),
    },
    {
        "id": "acquisition",
        "hash": "#/acquisition",
        "name": "Sources",
        "selector": ".acquisition-panel",
        "tokens": (
            "Sources",
            "Source Packs",
            "Normalized Packs",
            "Briefing Inputs",
            "Provenance",
            "Advanced",
        ),
    },
    {
        "id": "sic",
        "hash": "#/sic",
        "name": "Research Collections",
        "selector": ".sic-panel",
        "tokens": (
            "Research Collections",
            "Source packages",
            "Retrieval posture",
            "Approval for changes",
            "Generated outputs",
        ),
    },
    {
        "id": "aor",
        "hash": "#/aor",
        "name": "Tasks & Runs",
        "selector": ".aor-context-panel",
        "tokens": (
            "Tasks & Runs",
            "Run Operating Context",
            "Run Readiness",
            "Board",
            "Review only",
        ),
    },
    {
        "id": "runtime-cockpit",
        "hash": "#/runtime-cockpit",
        "name": "Agents / Runtimes",
        "selector": ".runtime-feature-coverage",
        "tokens": (
            "Agents / Runtimes",
            "Runtime Operating Context",
            "Runtime Feature Coverage",
            "Runtime Capability Gates",
            "Hermes and OpenClaw live runtime sync",
            "No hidden actions",
        ),
    },
    {
        "id": "bus",
        "hash": "#/bus",
        "name": "Agent Bus",
        "selector": ".bus-context-panel",
        "tokens": (
            "Agent Bus",
            "Bus Operating Context",
            "Bus Readiness",
            "Agent Bus Feature Coverage",
            "Coordination Queue",
            "Review only",
        ),
    },
    {
        "id": "build-logs",
        "hash": "#/build-logs",
        "name": "History / Audit",
        "selector": ".build-logs-panel",
        "tokens": (
            "History / Audit",
            "Search activity history",
            "History stays unchanged",
        ),
    },
    {
        "id": "qa-proof",
        "hash": "#/qa-proof",
        "name": "Quality Review",
        "selector": ".qa-proof-panel",
        "tokens": (
            "Quality Review",
            "Visual review",
            "Review only",
        ),
    },
    {
        "id": "decision-ledger",
        "hash": "#/decision-ledger",
        "name": "Decisions",
        "selector": "#panel-decision-ledger.active",
        "tokens": (
            "Decisions",
            "Browse durable decisions",
            "Review only",
        ),
    },
    {
        "id": "pivot-log",
        "hash": "#/pivot-log",
        "name": "Pivot Log",
        "selector": "#panel-pivot-log.active",
        "tokens": (
            "Pivot Log",
        ),
    },
    {
        "id": "feature-filter",
        "hash": "#/feature-filter",
        "name": "Feature Audit",
        "selector": "#panel-feature-filter.active",
        "tokens": (
            "Feature Audit",
            "Review task-type boundaries",
            "Task Types",
            "Adoption Gate SOP",
        ),
    },
    {
        "id": "workflow-registry",
        "hash": "#/workflow-registry",
        "name": "Workflow Registry",
        "selector": "#panel-workflow-registry.active",
        "tokens": (
            "Workflow Registry",
            "Browse registered workflows",
            "Review only",
        ),
    },
    {
        "id": "role-cards",
        "hash": "#/role-cards",
        "name": "Role Cards",
        "selector": "#panel-role-cards.active",
        "tokens": (
            "Role Cards",
            "Inspect runtime role cards",
            "Review only",
        ),
    },
    {
        "id": "schedules",
        "hash": "#/schedules",
        "name": "Schedules",
        "selector": ".schedules-context-panel",
        "tokens": (
            "Schedules",
            "Schedule Operating Context",
            "Schedule Readiness",
            "Schedule Feature Coverage",
            "Schedule Intents",
            "Activation needs approval",
        ),
    },
    {
        "id": "siteops",
        "hash": "#/siteops",
        "name": "Site Skills",
        "selector": "#panel-siteops.active",
        "tokens": (
            "Site Skills",
            "Site-operation runs",
            "No deploy action",
            "Approvals",
        ),
    },
    {
        "id": "runtime-memory-inspector",
        "hash": "#/runtime-memory-inspector",
        "name": "Memory Manager",
        "selector": ".runtime-memory-inspector-panel",
        "tokens": (
            "Memory Manager",
            "Runtime profiles",
            "Memory context",
        ),
    },
    {
        "id": "memory-ledger",
        "hash": "#/memory-ledger",
        "name": "Memory Ledger",
        "selector": "#panel-memory-ledger .runtime-intelligence-panel",
        "tokens": (
            "Memory Ledger",
            "Memory records",
            "Review required",
            "Memory is observable here",
        ),
    },
    {
        "id": "context-import",
        "hash": "#/context-import",
        "name": "Context Import",
        "selector": "#panel-context-import .runtime-intelligence-panel",
        "tokens": (
            "Context Import",
            "Runtime refs only",
            "No memory apply",
            "Import personal context",
            "Authority",
        ),
    },
    {
        "id": "pulse-schedule-proof",
        "hash": "#/pulse-schedule-proof",
        "name": "Proactive Briefings",
        "selector": ".pulse-schedule-proof-panel",
        "tokens": (
            "Proactive Briefings",
            "Briefing Lanes",
            "No auto-trigger",
            "Available Controls",
        ),
    },
    {
        "id": "pulse-enqueue",
        "hash": "#/pulse-enqueue",
        "name": "Review Queue",
        "selector": ".pulse-enqueue-panel",
        "tokens": (
            "Review Queue",
            "Proposed actions",
            "Review only",
        ),
    },
)

VIEWPORTS = (
    ("desktop", {"width": 1440, "height": 1000}),
    ("mobile", {"width": 390, "height": 900}),
)

FORBIDDEN_VISIBLE_COPY = (
    ("read_only", re.compile(r"\bread[- ]only\b", re.IGNORECASE)),
    ("mvp", re.compile(r"\bMVP\b")),
    ("developer", re.compile(r"\bdevelopers?\b", re.IGNORECASE)),
    ("implementation", re.compile(r"\bimplementation\b", re.IGNORECASE)),
    ("logs_audit", re.compile(r"\b(?:Logs / Audit|Build Logs)\b", re.IGNORECASE)),
    ("proof", re.compile(r"\bproof\b", re.IGNORECASE)),
    ("approval_gated", re.compile(r"\bapproval-gated\b", re.IGNORECASE)),
    ("dashboard", re.compile(r"\bDashboard\b")),
    ("node_inspector", re.compile(r"\bNode Inspector\b")),
    ("python_command", re.compile(r"python -m runtime\.cli\.main", re.IGNORECASE)),
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip(".-") or "visual-qa"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_output_dir(vault: Path, output_dir: str | Path | None) -> Path:
    raw = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    resolved = raw if raw.is_absolute() else vault / raw
    resolved = resolved.resolve()
    try:
        resolved.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError("visual QA output directory must stay inside the vault") from exc
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def _relative_to_vault(vault: Path, path: str | Path | None) -> str | None:
    if path is None:
        return None
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = vault / resolved
    try:
        return resolved.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _ok_data(resp: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(resp, dict):
      return {"ok": False, "status": "error", "error": {"message": "non-dict response"}}
    return resp


def _build_api_mocks(vault: Path) -> dict[str, Any]:
    from runtime.studio.shell.api import StudioAPI

    api = StudioAPI(str(vault))
    aor_executions = _ok_data(api.get_aor_executions("", "", 20))
    aor_items = ((aor_executions.get("data") or {}).get("executions") or [])
    first_aor_filename = (aor_items[0] or {}).get("filename") if aor_items else ""
    aor_detail = _ok_data(api.get_aor_execution_detail(first_aor_filename)) if first_aor_filename else {
        "ok": True,
        "status": "ok",
        "surface": "aor_execution_detail",
        "data": {},
    }
    intake_panel = _ok_data(api.get_intake_panel("", 50))
    capture_panel = _ok_data(api.get_capture_to_markdown_panel(10))
    acquisition_summary = _ok_data(api.get_acquisition_summary())
    acquisition_runs = _ok_data(api.get_acquisition_runs(20))
    sources_product_model = _ok_data(api.get_sources_product_model(36))
    sic_workspaces = _ok_data(api.get_sic_workspaces())
    sic_items = ((sic_workspaces.get("data") or {}).get("workspaces") or [])
    first_sic_slug = (sic_items[0] or {}).get("slug") if sic_items else ""
    sic_detail = _ok_data(api.get_sic_workspace_detail(first_sic_slug)) if first_sic_slug else {
        "ok": True,
        "status": "ok",
        "surface": "sic_workspace_detail",
        "data": {},
    }
    runtime_memory_runtimes = _ok_data(api.get_runtime_memory_runtimes())
    runtime_memory_items = ((runtime_memory_runtimes.get("data") or {}).get("runtimes") or [])
    first_runtime_id = (runtime_memory_items[0] or {}).get("runtime_id") if runtime_memory_items else ""
    runtime_memory_detail = _ok_data(api.get_runtime_memory_detail(first_runtime_id)) if first_runtime_id else {
        "ok": True,
        "status": "ok",
        "surface": "runtime_memory_detail",
        "data": {},
    }
    return {
        "get_phase11_chat_panel_contract": _ok_data(
            api.get_phase11_chat_panel_contract("Summarize the current workspace", "", "hermes")
        ),
        "get_project_workspace_view": _ok_data(api.get_project_workspace_view()),
        "get_sprint_focus": _ok_data(api.get_sprint_focus()),
        "get_chaser_forge_panel": _ok_data(api.get_chaser_forge_panel()),
        "get_workflow_packs_panel": {
            "ok": True,
            "status": "ok",
            "surface": "workflow_packs_panel",
            "data": {
                "surface": "workflow_packs_panel",
                "status": "approval_resume_contract_ready",
                "summary": {
                    "pack_count": 4,
                    "run_count": 2,
                    "review_queue_count": 1,
                    "proof_card_count": 2,
                    "demo_manual_provider_ready": True,
                    "automation_audit_mvp_ready": True,
                    "creative_studio_mvp_ready": True,
                    "research_intelligence_mvp_ready": True,
                    "agent_governance_mvp_ready": True,
                    "approval_resume_contract_ready": True,
                    "approval_review_artifact_writer_ready": True,
                    "approval_consumption_dry_run_ready": True,
                    "approval_marker_reservation_ready": True,
                    "approved_local_resume_executor_ready": True,
                    "approval_consumption_built": True,
                    "resume_executor_built": True,
                    "external_actions_blocked": True,
                },
                "authority": {
                    "local_artifact_write_allowed": True,
                    "local_demo_run_write_allowed": True,
                    "approval_review_artifact_write_allowed": True,
                    "exact_once_marker_write_allowed": True,
                    "approved_local_resume_write_allowed": True,
                    "external_actions_allowed": False,
                    "provider_calls_allowed": False,
                    "browser_actions_allowed": False,
                    "agent_bus_task_write_allowed": False,
                    "runtime_dispatch_allowed": False,
                    "workflow_execution_allowed": False,
                    "approval_consumption_direct_allowed": False,
                    "canonical_mutation_allowed": False,
                },
                "operating_context": {
                    "title": "Mission Operating Context",
                    "description": "Local mission packs for turning operator intent into reviewable artifacts, proof cards, and gated local resume evidence.",
                    "source": "runtime/workflow_packs registry, local run store, review queue, and proof cards",
                    "safe_action": "Create local mission artifacts and inspect gates. External actions, provider calls, runtime dispatch, Agent Bus writes, graph promotion, and canonical mutation remain unavailable from this page.",
                    "cards": [
                        {"label": "Mission packs", "value": 4, "note": "Automation, creative, research, and agent governance", "status": "local-ready"},
                        {"label": "Local runs", "value": 2, "note": "artifact/proof runs in the local store", "status": "local-artifacts"},
                        {"label": "Review queue", "value": 1, "note": "approval gate waiting for operator review", "status": "review-gated"},
                        {"label": "Proof cards", "value": 2, "note": "public-safe/local evidence summaries", "status": "evidence"},
                    ],
                },
                "readiness": {
                    "summary": "Mission packs can create local artifacts and complete the existing approval/resume chain. Live external work remains blocked.",
                    "rows": [
                        {"label": "Pack registry", "status": "ready", "note": "Four user-facing mission packs are registered."},
                        {"label": "Local run and artifact store", "status": "ready", "note": "Manual/demo provider writes local run artifacts and proof cards only."},
                        {"label": "Approval review and exact-once marker", "status": "ready", "note": "Local approval artifacts and marker reservations are scoped to one gate."},
                        {"label": "External execution", "status": "blocked", "note": "No provider call, browser action, runtime dispatch, Agent Bus write, publication, or delivery is mounted."},
                    ],
                },
                "feature_family_coverage": [
                    {
                        "family": "VentureOps / Missions",
                        "capability": "Product Workflow Packs foundation",
                        "product_surface": "Main / Missions",
                        "status": "PARTIAL / VERIFIED LOCAL",
                        "evidence": "runtime.workflow_packs.registry, store, panel, proof cards",
                        "boundary": "Local artifact/proof lane only; no external/client execution.",
                    },
                    {
                        "family": "Product Workflow Packs",
                        "capability": "Automation Audit, Creative Studio, Research Intelligence, Agent Governance Kit",
                        "product_surface": "Main / Missions",
                        "status": "PARTIAL / VERIFIED LOCAL",
                        "evidence": "pack-specific workflow modules",
                        "boundary": "Pack outputs are local artifacts; no provider, browser, or publication authority.",
                    },
                    {
                        "family": "Governance",
                        "capability": "Approval review, exact-once marker, and approved local resume",
                        "product_surface": "Missions / Review Queue",
                        "status": "PARTIAL / VERIFIED LOCAL",
                        "evidence": "approval review, dry-run, marker, and resume executor modules",
                        "boundary": "Only one scoped local gate is consumed; no generic approval consumption.",
                    },
                ],
                "registry": {
                    "packs": [
                        {
                            "id": "visual_product_creative_studio",
                            "name": "Visual Product & Creative Studio",
                            "category": "creative",
                            "description": "Create local campaign briefs, copy packs, lightweight visual mockups, and proof cards from manual product or offer context.",
                            "artifact_types": ["brief", "copy_pack", "html_mockup", "proof_card"],
                            "safety_notes": ["No publishing, email sending, browser automation, or external design-provider calls in MVP."],
                        },
                        {
                            "id": "founder_personal_automation_audit",
                            "name": "Founder / Personal Automation Audit",
                            "category": "automation_audit",
                            "description": "Turn a guided local questionnaire into repeated-task findings, ranked automation opportunities, draft manifests, and a roadmap.",
                            "artifact_types": ["report", "scorecard", "manifest", "proof_card"],
                            "safety_notes": ["Recommendations are artifacts only; no workflow execution or tool connection occurs in MVP."],
                        },
                        {
                            "id": "research_to_product_intelligence",
                            "name": "Research-to-Product Intelligence Engine",
                            "category": "research_intelligence",
                            "description": "Convert pasted/manual source context into evidence packets, claim candidates, product decisions, implementation briefs, and proof cards.",
                            "artifact_types": ["report", "scorecard", "brief", "json", "proof_card"],
                            "safety_notes": ["No implementation or canonical promotion happens automatically."],
                        },
                        {
                            "id": "safe_agent_runtime_governance_kit",
                            "name": "Safe Agent Runtime Governance Kit",
                            "category": "agent_governance",
                            "description": "Manually inventory agents and permission surfaces, classify risk, draft approval policies, lint manifests, and produce safety proof.",
                            "artifact_types": ["report", "scorecard", "policy", "json", "proof_card"],
                            "safety_notes": ["Policy drafts are not applied live."],
                        },
                    ],
                },
                "runs": [
                    {
                        "id": "wfp-run-automation-audit",
                        "title": "Weekly operator automation audit",
                        "pack_id": "founder_personal_automation_audit",
                        "status": "artifact_ready",
                        "provider_mode": "demo_manual",
                        "created_at": "2026-05-24T00:20:00Z",
                    },
                    {
                        "id": "wfp-run-agent-governance",
                        "title": "Runtime permission review",
                        "pack_id": "safe_agent_runtime_governance_kit",
                        "status": "review_required",
                        "provider_mode": "demo_manual",
                        "created_at": "2026-05-24T00:18:00Z",
                    },
                ],
                "review_queue": [
                    {
                        "kind": "approval_gate",
                        "run_id": "wfp-run-agent-governance",
                        "pack_id": "safe_agent_runtime_governance_kit",
                        "item_id": "gate-local-resume",
                        "title": "local_resume",
                        "status": "pending",
                        "path": "runtime/workflow_packs/state/runs/wfp-run-agent-governance/approvals/gate-local-resume.json",
                    },
                ],
                "proof_cards": [
                    {
                        "id": "proof-automation-audit",
                        "title": "Automation Audit Proof",
                        "status": "review_required",
                        "pack_id": "founder_personal_automation_audit",
                        "approval_summary": {"pending_gate_count": 1},
                        "metrics": {"artifact_count": 4},
                    },
                    {
                        "id": "proof-agent-governance",
                        "title": "Agent Governance Proof",
                        "status": "review_required",
                        "pack_id": "safe_agent_runtime_governance_kit",
                        "approval_summary": {"pending_gate_count": 1},
                        "metrics": {"artifact_count": 5},
                    },
                ],
                "new_run": {
                    "default_pack_id": "founder_personal_automation_audit",
                    "provider_mode": "demo_manual",
                    "approved_local_resume_executor_api_method": "execute_workflow_pack_approved_local_resume",
                },
            },
        },
        "get_graph_hygiene_review_panel": _ok_data(api.get_graph_hygiene_review_panel()),
        "get_graph_hygiene_decision_drafts": _ok_data(api.get_graph_hygiene_decision_drafts()),
        "get_graph_hygiene_decision_logs": _ok_data(api.get_graph_hygiene_decision_logs()),
        "get_intake_panel": intake_panel,
        "get_capture_to_markdown_panel": capture_panel,
        "get_acquisition_summary": acquisition_summary,
        "get_acquisition_runs": acquisition_runs,
        "get_sources_product_model": sources_product_model,
        "get_sic_workspaces": sic_workspaces,
        "get_sic_workspace_detail": sic_detail,
        "get_memory_ledger_panel": _ok_data(api.get_memory_ledger_panel()),
        "get_personal_context_import_panel": _ok_data(api.get_personal_context_import_panel()),
        "get_runtime_memory_runtimes": runtime_memory_runtimes,
        "get_runtime_memory_detail": runtime_memory_detail,
        "get_pulse_schedule_proof_panel": _ok_data(api.get_pulse_schedule_proof_panel()),
        "get_pulse_agent_bus_enqueue_panel": _ok_data(api.get_pulse_agent_bus_enqueue_panel()),
        "get_panel_registry": _ok_data(api.get_panel_registry()),
        "get_runtime_status": _ok_data(api.get_runtime_status()),
        "get_runtime_cockpit_panel": _ok_data(api.get_runtime_cockpit_panel()),
        "get_aor_executions": aor_executions,
        "get_aor_summary": _ok_data(api.get_aor_summary()),
        "get_aor_execution_detail": aor_detail,
        "get_bus_diagnostics": {
            "ok": True,
            "status": "ok",
            "surface": "bus_diagnostics",
            "data": {
                "mode": "local",
                "db_path": str(vault / "runtime" / "agent_bus" / "agent_bus.sqlite"),
                "heartbeat_count": 2,
                "heartbeats": [
                    {
                        "runtime": "Hermes",
                        "runtime_instance_id": "hermes-wsl",
                        "heartbeat_scope": "runtime",
                        "status": "idle",
                        "health": "ok",
                        "last_seen": "2026-05-24T00:12:00Z",
                        "summary": "Gateway and Agent Bus heartbeat visible.",
                    },
                    {
                        "runtime": "OpenClaw",
                        "runtime_instance_id": "openclaw-windows",
                        "heartbeat_scope": "runtime",
                        "status": "busy",
                        "health": "ok",
                        "last_seen": "2026-05-24T00:11:45Z",
                        "summary": "Windows worker heartbeat visible.",
                    },
                ],
                "runtime_liveness": [
                    {
                        "runtime": "Hermes",
                        "runtime_name": "hermes",
                        "last_seen": "2026-05-24T00:12:00Z",
                        "status": "idle",
                        "health": "ok",
                        "age_seconds": 42,
                        "is_stale": False,
                        "stale_threshold_seconds": 900,
                    },
                    {
                        "runtime": "OpenClaw",
                        "runtime_name": "openclaw",
                        "last_seen": "2026-05-24T00:11:45Z",
                        "status": "busy",
                        "health": "ok",
                        "age_seconds": 57,
                        "is_stale": False,
                        "stale_threshold_seconds": 900,
                    },
                ],
                "total_tasks": 2,
                "open_task_count": 1,
                "active_task_count": 2,
                "tasks_by_status": {"open": 1, "claimed": 1},
                "authority": {
                    "read_only": True,
                    "writes_agent_bus_tasks": False,
                    "claims_tasks": False,
                    "dispatches_tasks": False,
                    "cancels_tasks": False,
                    "retries_tasks": False,
                    "workflow_execution": False,
                    "approval_consumption_allowed": False,
                    "provider_calls_allowed": False,
                    "canonical_mutation_allowed": False,
                },
                "operating_context": {
                    "title": "Bus Operating Context",
                    "description": "Local-first coordination desk for task packets, worker heartbeat evidence, and runtime routing posture.",
                    "source": "runtime.agent_bus.bus, runtime.agent_bus.router, and repo-local capability manifests",
                    "safe_action": "Inspect only. Task writes, claims, retries, dispatch, and approval consumption stay unmounted.",
                    "cards": [
                        {"label": "Visible queue", "value": 2, "note": "1 open; 2 active", "status": "read-only"},
                        {"label": "Registered workers", "value": 2, "note": "2 fresh; 0 stale or missing", "status": "heartbeat-evidence"},
                        {"label": "Heartbeat rows", "value": 2, "note": "runtime and instance scoped records", "status": "readback"},
                        {"label": "Authority posture", "value": "inspect", "note": "no write/claim/dispatch controls", "status": "blocked-by-design"},
                    ],
                },
                "readiness": {
                    "summary": "Read-only queue and heartbeat inspection is mounted. Coordination mutation remains blocked.",
                    "rows": [
                        {"label": "Queue readback", "status": "ready", "note": "Task packets can be listed without changing queue state."},
                        {"label": "Worker heartbeat readback", "status": "ready", "note": "Freshness is derived from capability stale thresholds."},
                        {"label": "Task write / claim / dispatch", "status": "blocked", "note": "No create, claim, retry, cancel, or dispatch controls are mounted from this page."},
                        {"label": "Approval consumption", "status": "blocked", "note": "Approval decisions are inspected in Governance; this page does not consume them."},
                    ],
                },
                "feature_family_coverage": [
                    {
                        "family": "Runtime",
                        "capability": "Agent Bus coordination queue",
                        "product_surface": "Runtime / Agent Bus",
                        "status": "READ-ONLY / CODE-OBSERVED",
                        "evidence": "get_bus_diagnostics, get_bus_tasks, get_bus_events",
                        "boundary": "No task writes, claims, dispatch, or runtime execution from Studio.",
                    },
                    {
                        "family": "Chat",
                        "capability": "Runtime dispatch substrate",
                        "product_surface": "Chat and Agent Bus",
                        "status": "GOVERNED / SEPARATE SEND PATH",
                        "evidence": "Phase 11 chat bridge routes through governed Agent Bus APIs",
                        "boundary": "Agent Bus page cannot send chat messages or create tasks.",
                    },
                    {
                        "family": "Governance",
                        "capability": "Audit trail and task event readback",
                        "product_surface": "Agent Bus and Logs / Audit",
                        "status": "READ-ONLY",
                        "evidence": "get_bus_events lists task events",
                        "boundary": "Audit events are displayed only; log writes remain outside this page.",
                    },
                ],
            },
        },
        "get_bus_tasks": {
            "ok": True,
            "status": "ok",
            "surface": "bus_tasks",
            "data": {
                "tasks": [
                    {
                        "task_id": "task-hermes-briefing",
                        "run_id": "run-hermes-briefing",
                        "sender": "Operator",
                        "recipient": "Hermes",
                        "intent": "workspace_briefing",
                        "task_type": "briefing",
                        "status": "open",
                        "priority": "normal",
                        "owner": None,
                        "created_at": "2026-05-24T00:10:00Z",
                        "request": "Prepare a workspace-aware briefing packet after approval.",
                    },
                    {
                        "task_id": "task-openclaw-hygiene",
                        "run_id": "run-openclaw-hygiene",
                        "sender": "ChaseOS",
                        "recipient": "OpenClaw",
                        "intent": "graph_hygiene",
                        "task_type": "hygiene_review",
                        "status": "claimed",
                        "priority": "high",
                        "owner": "OpenClaw",
                        "created_at": "2026-05-24T00:09:00Z",
                        "request": "Inspect pending graph hygiene candidates without mutating canonical graph state.",
                    },
                ],
                "task_count": 2,
                "status_filter": None,
                "runtime_filter": None,
                "limit": 20,
            },
        },
        "get_bus_events": {
            "ok": True,
            "status": "ok",
            "surface": "bus_events",
            "data": {
                "events": [
                    {
                        "task_id": "task-openclaw-hygiene",
                        "created_at": "2026-05-24T00:09:20Z",
                        "event_type": "claimed",
                        "sender": "OpenClaw",
                        "message": "OpenClaw claimed graph hygiene review.",
                    },
                    {
                        "task_id": "task-hermes-briefing",
                        "created_at": "2026-05-24T00:10:00Z",
                        "event_type": "created",
                        "sender": "Operator",
                        "message": "Briefing task packet created by governed path.",
                    },
                ],
                "event_count": 2,
                "limit": 30,
            },
        },
        "get_schedule_summary": {
            "ok": True,
            "status": "ok",
            "surface": "schedule_summary",
            "data": {
                "ok": True,
                "surface": "studio_schedule_inspector",
                "total": 2,
                "enabled": 1,
                "disabled": 1,
                "by_runtime_adapter_target": {"openclaw": 1, "hermes": 1},
                "by_cadence_type": {"cron": 2},
                "by_schedule_kind": {"workflow": 2},
                "last_state_change_utc": "2026-05-24T00:07:00Z",
                "authority": {
                    "read_only": True,
                    "writes_schedule_files": False,
                    "enables_or_disables_schedules": False,
                    "cron_mutation_allowed": False,
                    "external_scheduler_mutation_allowed": False,
                    "agent_bus_task_write_allowed": False,
                    "runtime_dispatch_allowed": False,
                    "workflow_execution": False,
                    "approval_consumption_allowed": False,
                    "provider_calls_allowed": False,
                    "canonical_mutation_allowed": False,
                },
                "operating_context": {
                    "title": "Schedule Operating Context",
                    "description": "Local-first view of schedule intents, cadence, runtime targets, and governed activation posture.",
                    "source": "runtime/schedules/*.yaml, runtime/schedules/index.yaml, and schedule state logs",
                    "safe_action": "Inspect schedule intent and readiness only. Enabling, disabling, cron mutation, workflow dispatch, and external delivery stay governed.",
                    "cards": [
                        {"label": "Schedule intents", "value": 2, "note": "1 enabled; 1 disabled", "status": "read-only"},
                        {"label": "Enabled intents", "value": 1, "note": "runtime adapter target is visible; no launch from Studio", "status": "governed"},
                        {"label": "Runtime targets", "value": 2, "note": "hermes, openclaw", "status": "readback"},
                        {"label": "Last state change", "value": "2026-05-24T00:07:00Z", "note": "schedule state log readback only", "status": "audit"},
                    ],
                },
                "readiness": {
                    "summary": "Schedule intent readback is mounted. Activation, cron mutation, Agent Bus task writes, runtime dispatch, and external delivery remain approval-gated or blocked from this page.",
                    "rows": [
                        {"label": "Intent readback", "status": "ready", "note": "Studio can list local schedule YAML intents without writing files."},
                        {"label": "State-change audit", "status": "ready", "note": "Latest state entry: 2026-05-24T00:07:00Z."},
                        {"label": "Enable / disable", "status": "approval-gated", "note": "Toggle requests route through approval preview and are not direct mutations."},
                        {"label": "Cron / runtime dispatch", "status": "blocked", "note": "This page does not mutate cron, start adapters, or execute workflows."},
                    ],
                },
                "feature_family_coverage": [
                    {
                        "family": "Scheduled Briefing Pipelines",
                        "capability": "Trigger schedule intent readback",
                        "product_surface": "Runtime / Schedules",
                        "status": "PARTIAL LIVE / READ-ONLY",
                        "evidence": "runtime.studio.schedule_inspector.list_schedules and runtime/schedules/*.yaml",
                        "boundary": "No workflow execution, cron mutation, or external delivery from Studio.",
                    },
                    {
                        "family": "Scheduling Intent Architecture",
                        "capability": "Native schedule intent store",
                        "product_surface": "Runtime / Schedules",
                        "status": "LIVE READBACK",
                        "evidence": "runtime/schedules/index.yaml and schedule loader contract",
                        "boundary": "Studio reads schedule files only; enable/disable remains approval-gated.",
                    },
                    {
                        "family": "Governance",
                        "capability": "Schedule state audit readback",
                        "product_surface": "Logs / Audit and Schedules",
                        "status": "READ-ONLY",
                        "evidence": "07_LOGS/Schedule-State/schedule_state_log.jsonl",
                        "boundary": "Audit readback only; canonical mutations are unavailable here.",
                    },
                ],
            },
        },
        "get_schedules": {
            "ok": True,
            "status": "ok",
            "surface": "schedules",
            "data": {
                "ok": True,
                "surface": "studio_schedule_inspector",
                "schedule_count": 2,
                "schedules": [
                    {
                        "schedule_id": "sch-operator-today-0700",
                        "schedule_kind": "workflow",
                        "workflow_id": "operator_today",
                        "command_id": None,
                        "enabled": True,
                        "status_label": "enabled intent",
                        "execution_posture": "runtime-governed intent",
                        "schedule_boundary": "Read-only schedule intent. Execution, cron mutation, Agent Bus writes, approval consumption, and external delivery are not available from Studio.",
                        "shadow_mode": False,
                        "owner": "operator",
                        "runtime_adapter_target": "openclaw",
                        "cadence_type": "cron",
                        "cron_expression": "0 7 * * 1-5",
                        "timezone": "Europe/London",
                        "approval_policy": "approval_required",
                        "allowed_workflow_task_types": ["operator-briefing"],
                        "vault_writeback_targets": ["07_LOGS/Daily/"],
                        "created_at": "2026-04-15T00:00:00Z",
                        "created_by": "operator",
                    },
                    {
                        "schedule_id": "sch-sbp-strikezone-digest-0600",
                        "schedule_kind": "workflow",
                        "workflow_id": "strikezone_digest",
                        "command_id": None,
                        "enabled": False,
                        "status_label": "disabled intent",
                        "execution_posture": "inactive intent",
                        "schedule_boundary": "Read-only schedule intent. Execution, cron mutation, Agent Bus writes, approval consumption, and external delivery are not available from Studio.",
                        "shadow_mode": True,
                        "owner": "operator",
                        "runtime_adapter_target": "hermes",
                        "cadence_type": "cron",
                        "cron_expression": "0 6 * * *",
                        "timezone": "Europe/London",
                        "approval_policy": "manual",
                        "allowed_workflow_task_types": ["briefing"],
                        "vault_writeback_targets": ["07_LOGS/Briefings/"],
                        "created_at": "2026-04-21T00:00:00Z",
                        "created_by": "operator",
                    },
                ],
            },
        },
        "get_schedule_detail": {
            "ok": True,
            "status": "ok",
            "surface": "schedule_detail",
            "data": {
                "ok": True,
                "surface": "studio_schedule_inspector",
                "schedule": {
                    "schedule_id": "sch-operator-today-0700",
                    "workflow_id": "operator_today",
                    "command_id": None,
                    "enabled": True,
                    "shadow_mode": False,
                    "runtime_adapter_target": "openclaw",
                    "cadence_type": "cron",
                    "cron_expression": "0 7 * * 1-5",
                    "timezone": "Europe/London",
                    "owner": "operator",
                    "approval_policy": "approval_required",
                    "allowed_workflow_task_types": ["operator-briefing"],
                    "vault_writeback_targets": ["07_LOGS/Daily/"],
                    "created_at": "2026-04-15T00:00:00Z",
                    "created_by": "operator",
                    "rationale": "Daily operator schedule is inspected here; activation and dispatch are governed elsewhere.",
                },
                "recent_state_changes": [
                    {"timestamp_utc": "2026-05-24T00:07:00Z", "action": "inspect", "changed_by": "Studio QA"},
                ],
                "state_changes_shown": 1,
            },
        },
        "get_graph_style_registry": _ok_data(api.get_graph_style_registry()),
        "get_graph_settings": _ok_data(api.get_graph_settings()),
        "list_graph_presets": _ok_data(api.list_graph_presets()),
        "get_chat_runtime_availability": {
            "ok": True,
            "status": "ok",
            "surface": "chat_runtime_availability",
            "data": {
                "any_runtime_online": True,
                "runtimes": [
                    {
                        "adapter_id": "hermes",
                        "bus_name": "Hermes",
                        "is_bus_runtime": True,
                        "online": True,
                        "heartbeat_online": True,
                        "dispatch_ready": True,
                        "runtime_can_receive_chat": True,
                        "gateway_port_online": True,
                        "gateway_port_listening": 9119,
                        "gateway_ports_checked": [9119],
                        "freshness": "fresh",
                        "pip_class": "pip--live",
                        "blocked_reasons": [],
                    },
                    {
                        "adapter_id": "openclaw",
                        "bus_name": "OpenClaw",
                        "is_bus_runtime": True,
                        "online": True,
                        "heartbeat_online": True,
                        "dispatch_ready": True,
                        "runtime_can_receive_chat": True,
                        "gateway_port_online": True,
                        "gateway_port_listening": 18789,
                        "gateway_ports_checked": [18789],
                        "freshness": "fresh",
                        "pip_class": "pip--live",
                        "blocked_reasons": [],
                    },
                ],
                "runtime_by_adapter": {
                    "hermes": {
                        "adapter_id": "hermes",
                        "bus_name": "Hermes",
                        "is_bus_runtime": True,
                        "online": True,
                        "heartbeat_online": True,
                        "dispatch_ready": True,
                        "runtime_can_receive_chat": True,
                        "gateway_port_online": True,
                        "gateway_port_listening": 9119,
                        "gateway_ports_checked": [9119],
                        "freshness": "fresh",
                        "pip_class": "pip--live",
                        "blocked_reasons": [],
                    },
                    "openclaw": {
                        "adapter_id": "openclaw",
                        "bus_name": "OpenClaw",
                        "is_bus_runtime": True,
                        "online": True,
                        "heartbeat_online": True,
                        "dispatch_ready": True,
                        "runtime_can_receive_chat": True,
                        "gateway_port_online": True,
                        "gateway_port_listening": 18789,
                        "gateway_ports_checked": [18789],
                        "freshness": "fresh",
                        "pip_class": "pip--live",
                        "blocked_reasons": [],
                    },
                },
            },
        },
        "get_daemon_status": {
            "ok": True,
            "status": "ok",
            "surface": "daemon_status",
            "data": {"running": False, "status": "not-running", "pid": None},
        },
        "send_chat_message": {
            "ok": False,
            "status": "blocked",
            "surface": "send_chat_message",
            "error": {"message": "visual QA does not dispatch runtime messages"},
        },
        "poll_chat_result": {
            "ok": False,
            "status": "blocked",
            "surface": "poll_chat_result",
            "error": {"message": "visual QA does not poll runtime results"},
        },
    }


def _fallback_response(method: str) -> dict[str, Any]:
    return {
        "ok": True,
        "status": "ok",
        "surface": method,
        "data": {},
        "warnings": [f"{method} returned visual-QA fallback data"],
    }


def _init_script(vault: Path, mocks: dict[str, Any]) -> str:
    payload = json.dumps(mocks)
    fallback = json.dumps({method: _fallback_response(method) for method in ()})
    return f"""
window.__CHASEOS_VAULT_ROOT__ = {json.dumps(str(vault))};
window.__CHASEOS_VISUAL_QA__ = true;
const chaseosMocks = {payload};
const chaseosFallbacks = {fallback};
window.pywebview = {{
  api: new Proxy({{}}, {{
    get(target, prop) {{
      if (!target[prop]) {{
        target[prop] = (...args) => {{
          if (Object.prototype.hasOwnProperty.call(chaseosMocks, prop)) {{
            return Promise.resolve(chaseosMocks[prop]);
          }}
          if (Object.prototype.hasOwnProperty.call(chaseosFallbacks, prop)) {{
            return Promise.resolve(chaseosFallbacks[prop]);
          }}
          return Promise.resolve({{
            ok: true,
            status: "ok",
            surface: String(prop),
            data: {{}},
            warnings: ["visual QA fallback response"]
          }});
        }};
      }}
      return target[prop];
    }}
  }})
}};
window.confirm = () => false;
window.alert = (message) => console.warn("visual-qa-alert", message);
"""


def _visible_copy_violations(text: str) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for name, pattern in FORBIDDEN_VISIBLE_COPY:
        matches = sorted({match.group(0) for match in pattern.finditer(text or "")})
        if matches:
            violations.append({"term": name, "matches": matches[:8]})
    return violations


def _product_object_interaction_check(
    page: Any,
    page_errors: list[str],
    *,
    panel_id: str,
    viewport_name: str,
    name: str,
    locator: str,
    count_key: str,
    expected_kicker: str,
    expected_fragments: tuple[str, ...],
    empty_fragment: str | None = None,
) -> dict[str, Any]:
    check: dict[str, Any] = {
        "panel": panel_id,
        "viewport": viewport_name,
        "name": name,
        "ok": False,
        count_key: 0,
        "empty_state_ok": False,
        "error": None,
    }
    try:
        cards = page.locator(locator)
        card_count = cards.count()
        check[count_key] = card_count
        if card_count:
            cards.first.click()
            page.wait_for_selector("[data-selected-product-object]", timeout=10_000)
            inspector_text = page.locator("#object-inspector-body").inner_text(timeout=10_000)
            kicker_text = page.locator("#object-inspector-kicker").inner_text(timeout=10_000)
            normalized_inspector = inspector_text.lower()
            check["ok"] = (
                expected_kicker.lower() in kicker_text.lower()
                and all(fragment.lower() in normalized_inspector for fragment in expected_fragments)
            )
        elif empty_fragment:
            body_text = page.locator("body").inner_text(timeout=10_000)
            check["empty_state_ok"] = empty_fragment.lower() in body_text.lower()
            check["ok"] = bool(check["empty_state_ok"])
        else:
            check["error"] = f"no_cards_found:{locator}"
    except Exception as exc:
        check["error"] = str(exc).splitlines()[0]
        page_errors.append(
            f"{panel_id}:{viewport_name}:{name}:{check['error']}"
        )
    return check


def _shell_navigation_check(browser: Any, frontend: Path, init_script: str, page_errors: list[str]) -> dict[str, Any]:
    check: dict[str, Any] = {
        "panel": "shell",
        "viewport": "desktop",
        "name": "sidebar_collapse_and_home_route_reset",
        "ok": False,
        "collapsed_width": None,
        "expanded_width": None,
        "active_panel_after_home": None,
        "node_inspector_leaked_on_home": None,
        "error": None,
    }
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    try:
        page.add_init_script(init_script + "\ntry { localStorage.removeItem('chaseos_sidebar_collapsed'); } catch (error) {}")
        page.goto(frontend.resolve().as_uri() + "#/node-inspector", wait_until="domcontentloaded")
        page.wait_for_selector("#panel-node-inspector.active", timeout=30_000)

        page.locator('.nav-btn[data-panel="dashboard"]').click()
        page.wait_for_selector("#panel-dashboard.active", timeout=10_000)
        page.wait_for_timeout(250)
        active_panel = page.evaluate(
            "() => (document.querySelector('.panel.active') || {}).id || ''"
        )
        inspector_text = page.locator("#object-inspector").inner_text(timeout=10_000)
        node_leaked = "Node Inspector" in inspector_text or "Selected Node" in inspector_text

        expanded_width = page.evaluate("() => document.getElementById('sidebar').getBoundingClientRect().width")
        page.locator("#sidebar-collapse-btn").click()
        page.wait_for_timeout(260)
        collapsed_width = page.evaluate("() => document.getElementById('sidebar').getBoundingClientRect().width")
        collapsed_state = page.evaluate(
            "() => ({ collapsed: document.getElementById('shell').classList.contains('sidebar-collapsed'), "
            "expanded: document.getElementById('sidebar-collapse-btn').getAttribute('aria-expanded'), "
            "columns: getComputedStyle(document.getElementById('shell')).gridTemplateColumns })"
        )
        page.locator("#sidebar-collapse-btn").click()
        page.wait_for_timeout(260)
        reopened_width = page.evaluate("() => document.getElementById('sidebar').getBoundingClientRect().width")
        reopened_state = page.evaluate(
            "() => ({ collapsed: document.getElementById('shell').classList.contains('sidebar-collapsed'), "
            "expanded: document.getElementById('sidebar-collapse-btn').getAttribute('aria-expanded'), "
            "columns: getComputedStyle(document.getElementById('shell')).gridTemplateColumns })"
        )

        check.update(
            {
                "collapsed_width": collapsed_width,
                "expanded_width": reopened_width,
                "active_panel_after_home": active_panel,
                "node_inspector_leaked_on_home": node_leaked,
                "collapsed_state": collapsed_state,
                "reopened_state": reopened_state,
            }
        )
        check["ok"] = (
            active_panel == "panel-dashboard"
            and not node_leaked
            and collapsed_state.get("collapsed") is True
            and collapsed_state.get("expanded") == "false"
            and reopened_state.get("collapsed") is False
            and reopened_state.get("expanded") == "true"
            and collapsed_width < expanded_width - 80
            and reopened_width > collapsed_width + 80
            and len(str(collapsed_state.get("columns") or "").split()) >= 3
        )
        if not check["ok"]:
            check["error"] = "route_or_sidebar_state_mismatch"
    except Exception as exc:
        check["error"] = str(exc).splitlines()[0]
        page_errors.append(f"shell:desktop:sidebar_route:{check['error']}")
    finally:
        page.close()
    return check


PRODUCT_INTERACTION_CHECKS = {
    "intake": {
        "name": "intake_item_selects_right_inspector",
        "locator": ".intake-item",
        "count_key": "intake_item_count",
        "expected_kicker": "Selected Intake Item",
        "expected_fragments": ("sent for approval", "will not file it into your knowledge base"),
        "empty_fragment": "Review inbox is clear",
    },
    "capture-markdown": {
        "name": "capture_record_selects_right_inspector",
        "locator": ".capture-markdown-recent-item",
        "count_key": "capture_record_count",
        "expected_kicker": "Selected Capture",
        "expected_fragments": ("raw quarantine", "canonical promotion remain governed"),
        "empty_fragment": "No captures yet",
    },
    "acquisition": {
        "name": "source_or_run_selects_right_inspector",
        "locator": ".acquisition-source-card, .acquisition-run-card",
        "count_key": "source_object_count",
        "expected_kicker": "Selected Source",
        "expected_fragments": ("external",),
        "empty_fragment": "No sources yet",
    },
    "sic": {
        "name": "research_collection_selects_right_inspector",
        "locator": ".sic-workspace-card",
        "count_key": "research_collection_count",
        "expected_kicker": "Selected Collection",
        "expected_fragments": ("Research collections can be opened", "approval consumption stay behind governed flows"),
        "empty_fragment": "No research collections found",
    },
    "runtime-memory-inspector": {
        "name": "runtime_memory_selects_right_inspector",
        "locator": ".runtime-memory-item",
        "count_key": "runtime_memory_item_count",
        "expected_kicker": "Selected Memory Runtime",
        "expected_fragments": ("runtime memory", "does not update runtime brain"),
        "empty_fragment": "No runtime memory adapters found",
    },
    "memory-ledger": {
        "name": "memory_ledger_runtime_selects_right_inspector",
        "locator": ".ml-runtime-card, .ml-task-item",
        "count_key": "memory_ledger_object_count",
        "expected_kicker": "Selected Memory",
        "expected_fragments": ("Inspect memory coverage", "canonical promotion remain governed"),
        "empty_fragment": "No memory records yet",
    },
    "pulse-schedule-proof": {
        "name": "briefing_lane_selects_right_inspector",
        "locator": ".pulse-schedule-proof-card, .pulse-schedule-proof-control",
        "count_key": "briefing_lane_count",
        "expected_kicker": "Selected Briefing Lane",
        "expected_fragments": ("inspectable",),
        "empty_fragment": "No briefing lanes found",
    },
    "pulse-enqueue": {
        "name": "review_queue_item_selects_right_inspector",
        "locator": "#panel-pulse-enqueue [data-pulse-queue-ref]",
        "count_key": "review_queue_item_count",
        "expected_kicker": "Selected Review Item",
        "expected_fragments": ("Agent Bus task writes", "approval consumption"),
        "empty_fragment": "No Pulse review-contract preflights found",
    },
}


def run_visual_qa(vault_root: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    out_dir = _resolve_output_dir(vault, output_dir)
    frontend = vault / "runtime" / "studio" / "shell" / "frontend" / "index.html"
    if not frontend.is_file():
        raise FileNotFoundError(f"Studio frontend not found: {frontend}")

    mocks = _build_api_mocks(vault)
    init_script = _init_script(vault, mocks)
    screenshots: list[dict[str, Any]] = []
    interaction_checks: list[dict[str, Any]] = []
    console_errors: list[str] = []
    page_errors: list[str] = []

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover - environment fallback
        raise RuntimeError("playwright is required for final productization visual QA") from exc

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            for viewport_name, viewport in VIEWPORTS:
                for panel in PANELS:
                    page = browser.new_page(viewport=viewport)
                    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
                    page.on("pageerror", lambda exc: page_errors.append(str(exc)))
                    page.add_init_script(init_script)
                    page.goto(frontend.resolve().as_uri() + panel["hash"], wait_until="domcontentloaded")
                    selector_visible = True
                    selector_error = None
                    try:
                        page.wait_for_selector(panel["selector"], timeout=30_000)
                    except Exception as exc:
                        selector_visible = False
                        selector_error = str(exc).splitlines()[0]
                        page_errors.append(f"{panel['id']}:{viewport_name}:{selector_error}")
                    page.wait_for_timeout(400)
                    text = page.locator("body").inner_text(timeout=10_000)
                    normalized_text = text.lower()
                    missing = [token for token in panel["tokens"] if token.lower() not in normalized_text]
                    forbidden_copy = _visible_copy_violations(text)
                    if panel["id"] == "project-workspace" and viewport_name == "desktop":
                        interaction_check = {
                            "panel": panel["id"],
                            "viewport": viewport_name,
                            "name": "workspace_project_card_selects_right_inspector",
                            "ok": False,
                            "project_card_count": 0,
                            "error": None,
                        }
                        try:
                            project_cards = page.locator('[data-project-workspace-card="project"]')
                            project_card_count = project_cards.count()
                            interaction_check["project_card_count"] = project_card_count
                            if project_card_count:
                                project_cards.first.click()
                                page.wait_for_selector('[data-selected-product-object^="workspace:"]', timeout=10_000)
                                inspector_text = page.locator("#object-inspector-body").inner_text(timeout=10_000)
                                kicker_text = page.locator("#object-inspector-kicker").inner_text(timeout=10_000)
                                interaction_check["ok"] = (
                                    "selected workspace" in kicker_text.lower()
                                    and "Workspace inspection is open safely" in inspector_text
                                )
                            else:
                                interaction_check["error"] = "no_project_cards_found"
                        except Exception as exc:
                            interaction_check["error"] = str(exc).splitlines()[0]
                            page_errors.append(
                                f"{panel['id']}:{viewport_name}:workspace_inspector_interaction:{interaction_check['error']}"
                            )
                        interaction_checks.append(interaction_check)
                    if panel["id"] == "workflow-packs" and viewport_name == "desktop":
                        interaction_check = {
                            "panel": panel["id"],
                            "viewport": viewport_name,
                            "name": "mission_pack_card_selects_right_inspector",
                            "ok": False,
                            "mission_pack_card_count": 0,
                            "error": None,
                        }
                        try:
                            mission_cards = page.locator('[data-mission-pack-card="pack"]')
                            mission_card_count = mission_cards.count()
                            interaction_check["mission_pack_card_count"] = mission_card_count
                            if mission_card_count:
                                mission_cards.first.click()
                                page.wait_for_selector('[data-selected-product-object^="workflow-packs:"]', timeout=10_000)
                                inspector_text = page.locator("#object-inspector-body").inner_text(timeout=10_000)
                                kicker_text = page.locator("#object-inspector-kicker").inner_text(timeout=10_000)
                                interaction_check["ok"] = (
                                    "selected mission pack" in kicker_text.lower()
                                    and "Mission selection is open safely" in inspector_text
                                    and "external execution" in inspector_text
                                )
                            else:
                                interaction_check["error"] = "no_mission_pack_cards_found"
                        except Exception as exc:
                            interaction_check["error"] = str(exc).splitlines()[0]
                            page_errors.append(
                                f"{panel['id']}:{viewport_name}:mission_inspector_interaction:{interaction_check['error']}"
                            )
                        interaction_checks.append(interaction_check)
                    if panel["id"] == "chaser-forge" and viewport_name == "desktop":
                        interaction_check = {
                            "panel": panel["id"],
                            "viewport": viewport_name,
                            "name": "extension_object_card_selects_right_inspector",
                            "ok": False,
                            "extension_object_card_count": 0,
                            "error": None,
                        }
                        try:
                            extension_cards = page.locator('[data-chaser-forge-object-card="extension"]')
                            extension_card_count = extension_cards.count()
                            interaction_check["extension_object_card_count"] = extension_card_count
                            if extension_card_count:
                                extension_cards.first.click()
                                page.wait_for_selector('[data-selected-product-object^="chaser-forge:"]', timeout=10_000)
                                inspector_text = page.locator("#object-inspector-body").inner_text(timeout=10_000)
                                kicker_text = page.locator("#object-inspector-kicker").inner_text(timeout=10_000)
                                interaction_check["ok"] = (
                                    "selected extension object" in kicker_text.lower()
                                    and "Extension selection is open safely" in inspector_text
                                    and "ambient remote exchange" in inspector_text
                                )
                            else:
                                interaction_check["error"] = "no_extension_object_cards_found"
                        except Exception as exc:
                            interaction_check["error"] = str(exc).splitlines()[0]
                            page_errors.append(
                                f"{panel['id']}:{viewport_name}:extension_inspector_interaction:{interaction_check['error']}"
                            )
                        interaction_checks.append(interaction_check)
                    if panel["id"] == "aor" and viewport_name == "desktop":
                        interaction_check = {
                            "panel": panel["id"],
                            "viewport": viewport_name,
                            "name": "aor_run_card_selects_right_inspector",
                            "ok": False,
                            "run_card_count": 0,
                            "error": None,
                        }
                        try:
                            run_cards = page.locator('[data-aor-run-card="run"]')
                            run_card_count = run_cards.count()
                            interaction_check["run_card_count"] = run_card_count
                            if run_card_count:
                                run_cards.first.click()
                                page.wait_for_selector('[data-selected-runtime-object]', timeout=10_000)
                                inspector_text = page.locator("#object-inspector-body").inner_text(timeout=10_000)
                                kicker_text = page.locator("#object-inspector-kicker").inner_text(timeout=10_000)
                                interaction_check["ok"] = (
                                    "selected run" in kicker_text.lower()
                                    and "Inspect verification trail" in inspector_text
                                )
                            else:
                                interaction_check["error"] = "no_run_cards_found"
                        except Exception as exc:
                            interaction_check["error"] = str(exc).splitlines()[0]
                            page_errors.append(
                                f"{panel['id']}:{viewport_name}:run_inspector_interaction:{interaction_check['error']}"
                            )
                        interaction_checks.append(interaction_check)
                    if panel["id"] == "runtime-cockpit" and viewport_name == "desktop":
                        interaction_check = {
                            "panel": panel["id"],
                            "viewport": viewport_name,
                            "name": "runtime_card_selects_right_inspector",
                            "ok": False,
                            "runtime_card_count": 0,
                            "error": None,
                        }
                        try:
                            runtime_cards = page.locator('[data-runtime-card="runtime"]')
                            runtime_card_count = runtime_cards.count()
                            interaction_check["runtime_card_count"] = runtime_card_count
                            if runtime_card_count:
                                runtime_cards.first.click()
                                page.wait_for_selector('[data-selected-runtime-object]', timeout=10_000)
                                inspector_text = page.locator("#object-inspector-body").inner_text(timeout=10_000)
                                kicker_text = page.locator("#object-inspector-kicker").inner_text(timeout=10_000)
                                interaction_check["ok"] = (
                                    "selected runtime" in kicker_text.lower()
                                    and "Heartbeat:" in inspector_text
                                    and "needs approval" in inspector_text
                                )
                            else:
                                interaction_check["error"] = "no_runtime_cards_found"
                        except Exception as exc:
                            interaction_check["error"] = str(exc).splitlines()[0]
                            page_errors.append(
                                f"{panel['id']}:{viewport_name}:runtime_inspector_interaction:{interaction_check['error']}"
                            )
                        interaction_checks.append(interaction_check)
                    if panel["id"] == "bus" and viewport_name == "desktop":
                        interaction_check = {
                            "panel": panel["id"],
                            "viewport": viewport_name,
                            "name": "agent_bus_task_card_selects_right_inspector",
                            "ok": False,
                            "task_card_count": 0,
                            "error": None,
                        }
                        try:
                            task_cards = page.locator('[data-agent-bus-task-card="task"]')
                            task_card_count = task_cards.count()
                            interaction_check["task_card_count"] = task_card_count
                            if task_card_count:
                                task_cards.first.click()
                                page.wait_for_selector('[data-selected-runtime-object]', timeout=10_000)
                                inspector_text = page.locator("#object-inspector-body").inner_text(timeout=10_000)
                                kicker_text = page.locator("#object-inspector-kicker").inner_text(timeout=10_000)
                                interaction_check["ok"] = (
                                    "selected bus task" in kicker_text.lower()
                                    and "Inspect queue item" in inspector_text
                                    and "Task writes" in inspector_text
                                )
                            else:
                                interaction_check["error"] = "no_bus_task_cards_found"
                        except Exception as exc:
                            interaction_check["error"] = str(exc).splitlines()[0]
                            page_errors.append(
                                f"{panel['id']}:{viewport_name}:bus_task_inspector_interaction:{interaction_check['error']}"
                            )
                        interaction_checks.append(interaction_check)
                    if panel["id"] == "schedules" and viewport_name == "desktop":
                        interaction_check = {
                            "panel": panel["id"],
                            "viewport": viewport_name,
                            "name": "schedule_card_selects_right_inspector",
                            "ok": False,
                            "schedule_card_count": 0,
                            "error": None,
                        }
                        try:
                            schedule_cards = page.locator('[data-schedule-card="schedule"]')
                            schedule_card_count = schedule_cards.count()
                            interaction_check["schedule_card_count"] = schedule_card_count
                            if schedule_card_count:
                                schedule_cards.first.click()
                                page.wait_for_selector('[data-selected-runtime-object]', timeout=10_000)
                                inspector_text = page.locator("#object-inspector-body").inner_text(timeout=10_000)
                                kicker_text = page.locator("#object-inspector-kicker").inner_text(timeout=10_000)
                                interaction_check["ok"] = (
                                    "selected schedule" in kicker_text.lower()
                                    and "Schedule inspection only" in inspector_text
                                    and "No schedule enable/disable" in inspector_text
                                )
                            else:
                                interaction_check["error"] = "no_schedule_cards_found"
                        except Exception as exc:
                            interaction_check["error"] = str(exc).splitlines()[0]
                            page_errors.append(
                                f"{panel['id']}:{viewport_name}:schedule_inspector_interaction:{interaction_check['error']}"
                            )
                        interaction_checks.append(interaction_check)
                    if panel["id"] in PRODUCT_INTERACTION_CHECKS and viewport_name == "desktop":
                        interaction_checks.append(
                            _product_object_interaction_check(
                                page,
                                page_errors,
                                panel_id=panel["id"],
                                viewport_name=viewport_name,
                                **PRODUCT_INTERACTION_CHECKS[panel["id"]],
                            )
                        )
                    page.evaluate(
                        "() => { const active = document.querySelector('.panel.active'); if (active) active.scrollTop = 0; }"
                    )
                    path = out_dir / f"{viewport_name}-{panel['id']}.png"
                    page.screenshot(path=str(path), full_page=True)
                    screenshots.append(
                        {
                            "panel": panel["id"],
                            "viewport": viewport_name,
                            "path": _relative_to_vault(vault, path),
                            "exists": path.is_file(),
                            "bytes": path.stat().st_size if path.is_file() else 0,
                            "not_blank": path.is_file() and path.stat().st_size > 10_000,
                            "missing_required_tokens": missing,
                            "forbidden_visible_copy": forbidden_copy,
                            "selector_visible": selector_visible,
                            "selector_error": selector_error,
                            "url_hash": panel["hash"],
                        }
                    )
                    page.close()
            interaction_checks.append(_shell_navigation_check(browser, frontend, init_script, page_errors))
        finally:
            browser.close()

    blockers: list[str] = []
    if console_errors:
        blockers.append("console_errors")
    if page_errors:
        blockers.append("page_errors")
    if len(screenshots) != len(PANELS) * len(VIEWPORTS):
        blockers.append("screenshot_count_mismatch")
    if any(not item["not_blank"] for item in screenshots):
        blockers.append("blank_or_tiny_screenshot")
    if any(item["missing_required_tokens"] for item in screenshots):
        blockers.append("required_tokens_missing")
    if any(item.get("forbidden_visible_copy") for item in screenshots):
        blockers.append("forbidden_visible_copy")
    if any(not item.get("selector_visible") for item in screenshots):
        blockers.append("selector_visibility_failed")
    if any(not item.get("ok") for item in interaction_checks):
        blockers.append("interaction_check_failed")

    report = {
        "ok": not blockers,
        "status": STATUS,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "output_dir": _relative_to_vault(vault, out_dir),
        "authority": {
            "provider_calls_allowed": False,
            "external_actions_allowed": False,
            "external_delivery_allowed": False,
            "runtime_dispatch_allowed": False,
            "workflow_execution_allowed": False,
            "browser_control_authority_expanded": False,
            "approval_consumption_allowed": False,
            "graph_mutation_allowed": False,
            "installer_or_startup_mutation_allowed": False,
            "schedule_mutation_allowed": False,
            "cron_mutation_allowed": False,
            "agent_bus_task_write_allowed": False,
            "evidence_writes_allowed": True,
        },
        "screenshots": screenshots,
        "interaction_checks": interaction_checks,
        "console_errors": console_errors[:20],
        "page_errors": page_errors[:20],
        "blocked_reasons": blockers,
    }
    json_path = out_dir / "final-productization-visual-qa.json"
    md_path = out_dir / "final-productization-visual-qa.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_markdown_report(report), encoding="utf-8")
    report["evidence"] = {
        "json": _relative_to_vault(vault, json_path),
        "markdown": _relative_to_vault(vault, md_path),
    }
    return report


def _markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Studio Final Productization Visual QA",
        "",
        f"- Status: {report.get('status')}",
        f"- OK: {report.get('ok')}",
        f"- Generated: {report.get('generated_at')}",
        f"- Output dir: {report.get('output_dir')}",
        f"- Blockers: {', '.join(report.get('blocked_reasons') or []) or 'none'}",
        "",
        "## Authority",
    ]
    for key, value in (report.get("authority") or {}).items():
        lines.append(f"- {key}: {value}")
    lines += ["", "## Screenshots"]
    for item in report.get("screenshots") or []:
        missing = ", ".join(item.get("missing_required_tokens") or []) or "none"
        forbidden = ", ".join(
            f"{entry.get('term')}={entry.get('matches')}"
            for entry in (item.get("forbidden_visible_copy") or [])
        ) or "none"
        lines.append(
            f"- {item.get('viewport')} / {item.get('panel')}: {item.get('path')} "
            f"({item.get('bytes')} bytes, missing tokens: {missing}; forbidden copy: {forbidden})"
        )
    lines += ["", "## Interaction Checks"]
    for item in report.get("interaction_checks") or []:
        card_count = item.get("project_card_count")
        if card_count is None:
            card_count = item.get("run_card_count")
        if card_count is None:
            card_count = item.get("runtime_card_count")
        if card_count is None:
            card_count = item.get("task_card_count")
        if card_count is None:
            card_count = item.get("schedule_card_count")
        if card_count is None:
            card_count = item.get("mission_pack_card_count")
        if card_count is None:
            card_count = item.get("extension_object_card_count")
        if card_count is None:
            card_count = item.get("intake_item_count")
        if card_count is None:
            card_count = item.get("capture_record_count")
        if card_count is None:
            card_count = item.get("source_object_count")
        if card_count is None:
            card_count = item.get("research_collection_count")
        if card_count is None:
            card_count = item.get("runtime_memory_item_count")
        if card_count is None:
            card_count = item.get("memory_ledger_object_count")
        if card_count is None:
            card_count = item.get("briefing_lane_count")
        if card_count is None:
            card_count = item.get("review_queue_item_count")
        lines.append(
            f"- {item.get('viewport')} / {item.get('panel')} / {item.get('name')}: "
            f"ok={item.get('ok')} cards={card_count} "
            f"error={item.get('error') or 'none'}"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Studio final productization visual QA.")
    parser.add_argument("--vault-root", default=str(_repo_root()))
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    report = run_visual_qa(args.vault_root, args.output_dir)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"ok={report['ok']} blockers={report['blocked_reasons']}")
        for item in report["screenshots"]:
            print(f"{item['viewport']} {item['panel']}: {item['path']} {item['bytes']} bytes")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
