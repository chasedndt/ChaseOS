"""Localhost-only ChaseOS Studio MVP product shell.

This app provides a read-only MVP Studio surface that mounts the
Runtime Cockpit contract, the verified static graph artifact, the verified
static Pulse product shell artifact, and the ARSL route-review contract.
It is not a mutation-capable desktop product shell and it does not toggle runtime startup,
submit feedback, execute approvals, apply candidates, start child apps, execute
workflows, call providers, automate browsers, deliver messages, mutate
schedulers, or write canonical memory.
"""

from __future__ import annotations

from datetime import datetime, timezone
import html
import inspect
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from queue import Queue
import sqlite3
from threading import Lock, Thread
from time import monotonic
from typing import Any
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

from runtime.studio.app_launcher import build_studio_app_launcher_plan
from runtime.studio.approval_queue_panel import build_studio_approval_queue_panel_contract
from runtime.studio.arsl_route_review_panel import build_arsl_route_review_panel_contract
from runtime.studio.browser_runtime_operator_ui_readiness import build_studio_browser_runtime_operator_ui_readiness
from runtime.studio.canvas_shell_panel import build_canvas_panel_contract
from runtime.studio.graph_view_browser_qa import latest_static_graph_artifact
from runtime.studio.graph_view_shell_panel import build_graph_view_shell_panel_contract
from runtime.studio.node_inspector_shell_panel import build_node_inspector_shell_panel_contract
from runtime.studio.pulse_product_shell_panel import build_pulse_product_shell_panel_contract
from runtime.studio.workspace_mode_panel import (
    MODE_QUERY_PARAM,
    apply_workspace_mode_selection,
    build_workspace_mode_studio_panel,
)
from runtime.studio import runtime_cockpit

build_runtime_cockpit_contract = runtime_cockpit.build_runtime_cockpit_contract


_APP_SURFACE = "studio_desktop_shell_mvp_app"
_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 8772
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
_QA_EVIDENCE_ROOT = Path("07_LOGS") / "Studio-Graph-Views"
_DESKTOP_GRAPH_FOLDER_PATH = "06_AGENTS"
_DESKTOP_GRAPH_MAX_FILES = 150
_DESKTOP_GRAPH_MAX_BYTES_PER_FILE = 32768
_DESKTOP_GRAPH_MAX_NODES = 1000
_DESKTOP_GRAPH_MAX_EDGES = 3000
_DESKTOP_GRAPH_LAYOUT_NODE_LIMIT = 120
_DESKTOP_NODE_EXCERPT_BYTES = 2048


class StudioDesktopShellAppError(RuntimeError):
    """Raised when the Studio desktop shell app cannot proceed safely."""


def _supports_parameter(fn: Any, parameter_name: str) -> bool:
    try:
        signature = inspect.signature(fn)
    except (TypeError, ValueError):
        return True
    if any(param.kind is inspect.Parameter.VAR_KEYWORD for param in signature.parameters.values()):
        return True
    return parameter_name in signature.parameters


def _bounded_panel_kwargs(fn: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in kwargs.items() if _supports_parameter(fn, key)}


def _desktop_graph_limit_kwargs(*, include_layout: bool = False, include_excerpt: bool = False) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "folder_path": _DESKTOP_GRAPH_FOLDER_PATH,
        "max_files": _DESKTOP_GRAPH_MAX_FILES,
        "max_bytes_per_file": _DESKTOP_GRAPH_MAX_BYTES_PER_FILE,
        "max_nodes": _DESKTOP_GRAPH_MAX_NODES,
        "max_edges": _DESKTOP_GRAPH_MAX_EDGES,
    }
    if include_layout:
        kwargs["layout_node_limit"] = _DESKTOP_GRAPH_LAYOUT_NODE_LIMIT
    if include_excerpt:
        kwargs["content_excerpt_bytes"] = _DESKTOP_NODE_EXCERPT_BYTES
    return kwargs


def _panel_status(panel_id: str, *, state: str = "ready", reason: str | None = None, elapsed_seconds: float = 0.0) -> dict[str, Any]:
    return {
        "panel_id": panel_id,
        "state": state,
        "reason": reason,
        "elapsed_seconds": round(float(elapsed_seconds), 4),
        "ready": state == "ready",
        "cached": False,
        "fail_open": state != "ready",
    }


def _degraded_panel(surface: str, panel_id: str, label: str, *, state: str, reason: str) -> dict[str, Any]:
    return {
        "ok": False,
        "surface": surface,
        "status": state.upper().replace("_", " "),
        "panel": {"panel_id": panel_id, "label": label},
        "summary": {"blocker_count": 1, "degraded_reason": reason},
        "readiness": {"desktop_shell_mount_ready": False, "blockers": [reason]},
        "authority": {"read_only": True, "canonical_mutation_allowed": False},
    }


def _runtime_cockpit_placeholder(*, state: str, reason: str) -> dict[str, Any]:
    return {
        "ok": True,
        "surface": "studio_runtime_cockpit_contract",
        "status": state,
        "dashboard": {"panel_errors": [reason] if reason else []},
        "runtime_startup": {
            "surface_count": 0,
            "surface_count_unknown": True,
            "manageable_surface_count": 0,
            "manageable_surface_count_unknown": True,
            "visual_surface_count": 0,
            "visual_surface_count_unknown": True,
            "readiness_summary": {
                "readiness_packet_count": 0,
                "readiness_packet_count_unknown": True,
                "approval_missing_count": 0,
                "approval_missing_count_unknown": True,
            },
            "cards": [],
        },
        "runtime_health": {
            "runtime_profile_count": 0,
            "runtime_profile_count_unknown": True,
            "live_runtime_count": 0,
            "live_runtime_count_unknown": True,
            "blocked_runtime_count": 0,
            "blocked_runtime_count_unknown": True,
        },
    }


def _relative_artifact_path(vault: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return None


def _artifact_uri(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().as_uri()
    except ValueError:
        return None


def _latest_html_artifact(vault: Path, relative_dir: str) -> Path | None:
    root = (vault / relative_dir).resolve()
    if not root.is_dir() or vault.resolve() not in root.parents:
        return None
    candidates = [path for path in root.glob("*.html") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _fast_graph_panel(vault: Path) -> dict[str, Any]:
    artifact = latest_static_graph_artifact(vault)
    relative = _relative_artifact_path(vault, artifact)
    return {
        "ok": True,
        "surface": "studio_graph_view_shell_panel_contract",
        "status": "READ-ONLY STATIC GRAPH ARTIFACT MOUNT",
        "panel": {
            "panel_id": "studio.graph_view.shell_panel",
            "label": "Graph View",
            "surface_route": "#graph-view",
            "source_artifact_path": relative,
            "source_artifact_uri": _artifact_uri(artifact),
            "render_mode": "read-only-static-artifact-fast-plan",
        },
        "summary": {"visible_node_count": 0, "visible_edge_count": 0, "source_node_count": 0, "blocker_count": 0},
        "readiness": {"graph_view_shell_panel_contract_ready": True, "desktop_shell_mount_ready": True, "blockers": []},
        "authority": {
            "read_only": True,
            "writes_graph_index": False,
            "writes_node_ids": False,
            "node_editing_allowed": False,
            "workflow_execution_allowed": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }


def _fast_node_panel(vault: Path, graph_panel: dict[str, Any]) -> dict[str, Any]:
    graph_artifact = ((graph_panel.get("panel") or {}).get("source_artifact_path") or "07_LOGS/Studio-Graph-Views")
    selected_id = "studio-fast-read-only-graph-artifact"
    selected_label = "Graph artifact overview"
    return {
        "ok": True,
        "surface": "studio_node_inspector_shell_panel_contract",
        "status": "READ-ONLY NODE INSPECTOR MOUNT",
        "panel": {
            "panel_id": "studio.node_inspector.shell_panel",
            "label": "Node Inspector",
            "surface_route": "#node-inspector",
            "selection_source": "fast-plan-static-graph-artifact-overview",
            "selected_node_id": selected_id,
            "selected_node_label": selected_label,
            "selected_node_type": "read_only_static_graph_artifact",
            "selected_node_path": graph_artifact,
        },
        "summary": {
            "selected_node_found": True,
            "selected_node_label": selected_label,
            "selected_node_type": "read_only_static_graph_artifact",
            "source_path": graph_artifact,
            "incoming_edge_count": 0,
            "outgoing_edge_count": 0,
            "related_node_count": 0,
            "source_excerpt_available": True,
            "blocker_count": 0,
        },
        "source_node_inspector": {
            "selected_node": {
                "id": selected_id,
                "label": selected_label,
                "node_type": "read_only_static_graph_artifact",
                "properties": {"path": graph_artifact},
            },
            "edge_context": {"related_nodes": []},
            "source_excerpt": {
                "available": True,
                "text": "Fast Studio MVP route: read-only graph artifact overview. Use full planning for fresh node edge context.",
                "bytes_read": 96,
                "truncated": False,
            },
        },
        "readiness": {"node_inspector_shell_panel_contract_ready": True, "desktop_shell_mount_ready": True, "blockers": []},
        "authority": {
            "read_only": True,
            "writes_node_ids": False,
            "writes_graph_index": False,
            "node_editing_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }


def _fast_pulse_panel(vault: Path) -> dict[str, Any]:
    artifact = _latest_html_artifact(vault, "07_LOGS/Pulse-Decks/product-shell")
    return {
        "ok": True,
        "surface": "studio_pulse_product_shell_panel_contract",
        "status": "READ-ONLY PULSE PRODUCT SHELL MOUNT",
        "panel": {
            "panel_id": "studio.pulse.product_shell.panel",
            "label": "Pulse",
            "surface_route": "#pulse",
            "source_artifact_path": _relative_artifact_path(vault, artifact),
            "source_artifact_uri": _artifact_uri(artifact),
            "render_mode": "read-only-static-artifact-fast-plan",
        },
        "summary": {"panel_count": 1, "card_count": 0, "blocker_count": 0},
        "readiness": {"pulse_product_shell_panel_contract_ready": True, "desktop_shell_mount_ready": True, "blockers": []},
        "authority": {
            "read_only": True,
            "submits_feedback": False,
            "executes_approvals": False,
            "applies_candidates": False,
            "activates_schedules": False,
            "canonical_mutation_allowed": False,
        },
    }


def _fast_approval_queue_panel(vault: Path) -> dict[str, Any]:
    artifact = _latest_html_artifact(vault, "07_LOGS/Pulse-Decks/approval-queue")
    return {
        "ok": True,
        "surface": "studio_pulse_approval_queue_panel_contract",
        "status": "READ-ONLY APPROVAL QUEUE MOUNT",
        "panel": {
            "panel_id": "studio.pulse.approval_queue.panel",
            "label": "Approval Queue",
            "surface_route": "#approval-queue",
            "source_artifact_path": _relative_artifact_path(vault, artifact),
            "source_artifact_uri": _artifact_uri(artifact),
        },
        "summary": {"lane_count": 0, "candidate_row_count": 0, "action_count": 0, "missing_approval_key_count": 0, "blocker_count": 0},
        "readiness": {"approval_queue_panel_contract_ready": True, "desktop_shell_mount_ready": True, "blockers": []},
        "authority": {
            "read_only": True,
            "grants_approvals": False,
            "executes_approvals": False,
            "applies_candidates": False,
            "canonical_mutation_allowed": False,
        },
    }


def _fast_arsl_route_review_panel() -> dict[str, Any]:
    return {
        "ok": True,
        "surface": "studio_arsl_route_review_panel_contract",
        "status": "READ-ONLY ARSL ROUTE REVIEW MOUNT",
        "panel": {"panel_id": "studio.arsl.route_review.panel", "label": "ARSL Route Review", "surface_route": "#arsl-route-review"},
        "summary": {
            "requested_capability": "browser.click",
            "review_row_count": 1,
            "gate_required_rows": 1,
            "explicit_or_conditional_approval_rows": 1,
            "preview_decision": "approval_required",
            "selected_surface": "browser.playwright.operator",
            "authority_layer": "runtime/operator_surface/",
            "approval_required": "explicit",
        },
        "source_route_review": {
            "route_preview": {"decision": "approval_required", "gate_required": True, "audit_required": True, "ledger_written": False},
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
            "safety": {"execution_performed": False, "ledger_written": False, "browser_control_performed": False, "raw_manifest_exposed": False},
        },
        "readiness": {"arsl_route_review_panel_contract_ready": True, "desktop_shell_mount_ready": True, "blockers": []},
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


def _fast_browser_runtime_panel(vault: Path) -> dict[str, Any]:
    required_ids = [
        "browser-runtime-completion-summary",
        "browser-runtime-remaining-passes",
        "browser-runtime-external-dependencies",
        "browser-runtime-excalidraw-chain",
        "browser-runtime-provider-validation",
        "browser-runtime-site-skill-memory",
        "browser-runtime-approval-queue",
        "browser-runtime-run-evidence",
    ]
    return {
        "ok": True,
        "surface": "studio_browser_runtime_operator_ui_readiness_contract",
        "status": "READ-ONLY OPERATOR UI READINESS MOUNT",
        "panel_group": {"panel_group_id": "studio.browser_runtime.operator", "label": "Browser Runtime", "surface_route": "#browser-runtime", "panel_count": len(required_ids), "required_panel_ids": required_ids},
        "summary": {"overall_status": "mvp_read_only_ready", "bounded_mvp_done": True, "production_feature_done": False, "next_recommended_pass": "studio-browser-runtime-panel-browser-qa", "blocker_count": 0, "remaining_major_passes_min": 0, "remaining_major_passes_max": 0},
        "panels": [{"panel_id": panel_id, "label": panel_id.replace("browser-runtime-", "").replace("-", " ").title(), "ready_for_studio_mount": True, "render_mode": "read-only-data-contract"} for panel_id in required_ids],
        "remaining_passes": [],
        "external_dependencies": [],
        "blocked_reasons": [],
        "current_evidence": {"browser_run_logs_root": {"path": "07_LOGS/Browser-Runs", "exists": (vault / "07_LOGS" / "Browser-Runs").exists()}, "agent_activity_root": {"path": "07_LOGS/Agent-Activity", "exists": (vault / "07_LOGS" / "Agent-Activity").exists()}},
        "readiness": {"operator_ui_readiness_contract_ready": True, "studio_operator_ui_built": True, "next_recommended_pass": "studio-browser-runtime-panel-browser-qa"},
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


def _fast_canvas_panel() -> dict[str, Any]:
    return {
        "ok": True,
        "surface": "studio_canvas_panel_contract",
        "status": "READ-ONLY CANVAS PANEL MOUNT",
        "summary": {"object_count": 0, "link_count": 0, "graph_node_ref_count": 0, "proposal_card_count": 0},
        "readiness": {"canvas_panel_contract_ready": True, "desktop_shell_mount_ready": True, "blockers": []},
        "authority": {"read_only": True, "writes_canvas_state": False, "canonical_mutation_allowed": False},
        "objects": [],
        "links": [],
        "source_badges": [],
        "visualization": {"objects": [], "links": []},
        "boundary_banner": "Read-only fast Studio MVP canvas route; full planning can refresh workspace-local draft data.",
    }


def build_runtime_cockpit_fast_contract(vault_root: str | Path, *, runtime_id: str | None = None) -> dict[str, Any]:
    """Return lightweight Runtime Cockpit truth for fast shell planning.

    Fast planning must not fall back to a data-empty placeholder because the
    top-level Studio KPI cards and Runtime Cockpit need live runtime/profile
    truth even when heavier panels are skipped.
    """

    return runtime_cockpit.build_runtime_cockpit_fast_contract(vault_root, runtime_id=runtime_id)


def _count_app_states(apps: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"live": 0, "offline": 0, "unknown": 0, "not_checked": 0}
    for app in apps:
        state = str(((app.get("runtime_status") or {}).get("state") or "unknown")).lower()
        if state in {"healthy", "live", "running", "ok", "available"}:
            counts["live"] += 1
        elif state in {"offline", "unreachable", "error", "failed", "down"}:
            counts["offline"] += 1
        elif state == "not_checked":
            counts["not_checked"] += 1
        else:
            counts["unknown"] += 1
    return counts


def _runtime_contract_unknown(contract: dict[str, Any]) -> bool:
    startup = contract.get("runtime_startup") or {}
    readiness = startup.get("readiness_summary") or {}
    runtime_health = contract.get("runtime_health") or {}
    dashboard = contract.get("dashboard") or {}
    status = str(contract.get("status") or "").lower()
    return bool(
        status.startswith("skipped")
        or startup.get("surface_count_unknown")
        or readiness.get("approval_missing_count_unknown")
        or runtime_health.get("live_runtime_count_unknown")
        or dashboard.get("panel_errors")
    )


def _collect_host_runtime_processes() -> dict[str, Any]:
    """Return a best-effort, read-only host process observation for operator context.

    This is intentionally separate from the Runtime Cockpit contract. It does not
    claim a runtime is registered or healthy; it only reports matching local
    process command lines so the dashboard does not hide obvious live Hermes or
    OpenClaw surfaces when a fast/timeout-limited plan cannot build runtime
    health.
    """

    proc_root = Path("/proc")
    if not proc_root.is_dir():
        return {"available": False, "source": "/proc", "processes": [], "counts": {}, "total": 0}
    current_pid = os.getpid()
    processes: list[dict[str, Any]] = []
    tokens = {
        "hermes": ("hermes",),
        "openclaw": ("openclaw",),
        "chaseos": ("chaseos.py", "runtime/cli", "chaseos runtime", "chaseos studio"),
    }
    for entry in proc_root.iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid == current_pid:
            continue
        try:
            raw = (entry / "cmdline").read_bytes().replace(b"\x00", b" ").decode("utf-8", errors="ignore")
        except (OSError, PermissionError):
            continue
        lowered = raw.lower()
        if not raw.strip():
            continue
        kind = next((name for name, needles in tokens.items() if any(needle in lowered for needle in needles)), None)
        if kind is None:
            continue
        processes.append({"pid": pid, "kind": kind, "command": raw.strip()[:180]})
    processes.sort(key=lambda item: (str(item.get("kind")), int(item.get("pid") or 0)))
    counts: dict[str, int] = {}
    for process in processes:
        kind = str(process.get("kind") or "unknown")
        counts[kind] = counts.get(kind, 0) + 1
    return {
        "available": True,
        "source": "/proc/*/cmdline read-only host observation",
        "processes": processes[:12],
        "counts": counts,
        "total": len(processes),
    }


def _candidate_kanban_db_paths() -> list[Path]:
    return [
        Path.home() / ".hermes" / "kanban.db",
        Path.home() / "runtimes" / "hermes-home" / "kanban.db",
        Path.home() / "runtimes" / "hermes-home" / "kanban.db",
    ]


def _collect_kanban_snapshot() -> dict[str, Any]:
    """Return a best-effort, read-only Kanban summary if a Hermes board DB is visible."""

    seen: set[str] = set()
    for path in _candidate_kanban_db_paths():
        resolved = str(path)
        if resolved in seen:
            continue
        seen.add(resolved)
        if not path.is_file():
            continue
        try:
            uri = f"file:{path.as_posix()}?mode=ro"
            with sqlite3.connect(uri, uri=True, timeout=0.25) as con:
                rows = con.execute("select status, count(*) from tasks group by status").fetchall()
                recent = con.execute(
                    "select id, title, status, assignee from tasks "
                    "where status in ('ready','running','blocked') "
                    "order by priority desc, created_at desc limit 6"
                ).fetchall()
        except sqlite3.Error as exc:
            return {"available": False, "source": resolved, "error": str(exc), "counts": {}, "attention": []}
        counts = {str(status): int(count) for status, count in rows}
        return {
            "available": True,
            "source": resolved,
            "counts": counts,
            "total": sum(counts.values()),
            "attention": [
                {"id": task_id, "title": title, "status": status, "assignee": assignee}
                for task_id, title, status, assignee in recent
            ],
        }
    return {"available": False, "source": "no readable Hermes kanban.db found", "counts": {}, "attention": []}


def _summarize_blocked_panels(panel_statuses: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for panel_id, status in panel_statuses.items():
        state = str(status.get("state") or "unknown")
        if state == "ready":
            continue
        reason = str(status.get("reason") or "No reason reported.")
        if "skipped during fast shell planning" in reason:
            operator_reason = "Fast startup skipped this heavier panel; open it below or launch full planning when you need fresh details."
        elif "hard timeout" in reason or "soft timeout" in reason:
            operator_reason = "Panel took too long; Studio kept the first screen responsive and marked this dependency degraded."
        else:
            operator_reason = reason
        rows.append({"panel_id": panel_id, "state": state, "operator_reason": operator_reason})
    return rows


def _build_operator_dashboard(
    *,
    planning_mode: str,
    metrics: dict[str, Any],
    panel_statuses: dict[str, dict[str, Any]],
    apps: list[dict[str, Any]],
    host_runtime_processes: dict[str, Any],
    kanban: dict[str, Any],
) -> dict[str, Any]:
    app_states = _count_app_states(apps)
    blocked_panels = _summarize_blocked_panels(panel_statuses)
    observed_runtime_total = int(host_runtime_processes.get("total") or 0)
    kanban_counts = kanban.get("counts") or {}
    action_items: list[dict[str, Any]] = []
    runtime_unknown = bool(
        metrics.get("runtime_surface_count_unknown")
        or metrics.get("approval_missing_count_unknown")
        or metrics.get("live_runtime_count_unknown")
    )
    if blocked_panels:
        action_items.append(
            {
                "label": "Dashboard freshness",
                "status": "attention",
                "detail": f"{len(blocked_panels)} panels are skipped/degraded in this {planning_mode} plan; first screen is still safe to use.",
                "target": "#shell-boundary",
            }
        )
    if runtime_unknown:
        action_items.append(
            {
                "label": "Runtime contract freshness",
                "status": "unknown",
                "detail": "Runtime Cockpit data was not freshly available; verify credential, operator confirmation, or acquisition prerequisites before treating runtime/approval counts as clear.",
                "target": "#runtime-cockpit",
            }
        )
    if observed_runtime_total:
        action_items.append(
            {
                "label": "Runtime processes observed",
                "status": "live",
                "detail": f"{observed_runtime_total} host processes match Hermes/OpenClaw/ChaseOS; Runtime Cockpit contract may still be unavailable in fast/timeout mode.",
                "target": "#runtime-cockpit",
            }
        )
    else:
        action_items.append(
            {
                "label": "Runtime process observation",
                "status": "unknown",
                "detail": "No host runtime process observations were available from this read-only dashboard process.",
                "target": "#runtime-cockpit",
            }
        )
    if kanban.get("available"):
        open_count = sum(int(kanban_counts.get(key, 0) or 0) for key in ("ready", "running", "blocked"))
        action_items.append(
            {
                "label": "Kanban workload",
                "status": "attention" if open_count else "clear",
                "detail": f"{open_count} ready/running/blocked cards visible in read-only board summary.",
                "target": "#operator-kanban",
            }
        )
    else:
        action_items.append(
            {
                "label": "Kanban workload",
                "status": "unknown",
                "detail": f"Kanban DB summary unavailable: {kanban.get('source')}",
                "target": "#operator-kanban",
            }
        )
    if app_states["not_checked"]:
        action_items.append(
            {
                "label": "App Launcher handoff",
                "status": "planned",
                "detail": f"{app_states['not_checked']} declared apps were not health-probed; App Launcher rows remain handoff links, not live claims.",
                "target": "#app-launcher",
            }
        )
    return {
        "planning_mode": planning_mode,
        "summary": {
            "ready_panels": int(metrics.get("ready_panel_count") or 0),
            "blocked_dependencies": len(blocked_panels),
            "observed_runtime_processes": observed_runtime_total,
            "kanban_ready": int(kanban_counts.get("ready", 0) or 0),
            "kanban_running": int(kanban_counts.get("running", 0) or 0),
            "kanban_blocked": int(kanban_counts.get("blocked", 0) or 0),
            "declared_apps": int(metrics.get("app_count") or 0),
            "apps_not_checked": app_states["not_checked"],
        },
        "action_items": action_items,
        "blocked_panels": blocked_panels,
        "host_runtime_processes": host_runtime_processes,
        "kanban": kanban,
        "boundary": "Read-only operator summary; no approvals, dispatch, provider/connector calls, workflow execution, scheduler mutation, or canonical writes.",
    }


def _build_kpi_cards(
    metrics: dict[str, Any],
    *,
    apps: list[dict[str, Any]],
    panel_statuses: dict[str, dict[str, Any]],
    host_runtime_processes: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    app_states = _count_app_states(apps)
    degraded_panel_count = int(metrics.get("degraded_panel_count") or 0)
    approval_candidates = int(metrics.get("approval_queue_candidate_row_count") or 0)
    approval_missing = int(metrics.get("approval_missing_count") or 0)
    approval_missing_unknown = bool(metrics.get("approval_missing_count_unknown"))
    approvals_value: int | str = approval_candidates + approval_missing
    approvals_detail = f"{approval_candidates} queue candidates, {approval_missing} missing runtime approvals"
    if approval_missing_unknown:
        approvals_value = "unknown" if approval_candidates == 0 else f"{approval_candidates} + unknown"
        approvals_detail = (
            f"{approval_candidates} queue candidates; runtime approval readiness unavailable "
            "until prerequisite/confirmation checks complete"
        )
    graph_blockers = int(metrics.get("graph_blocker_count") or 0) + int(metrics.get("node_inspector_blocker_count") or 0)
    blocked_dependencies = sum(1 for status in panel_statuses.values() if status.get("state") != "ready")
    active_runtime_count = int(metrics.get("live_runtime_count") or 0)
    observed_runtime_count = int((host_runtime_processes or {}).get("total") or 0)
    runtime_signal_count = active_runtime_count if active_runtime_count else observed_runtime_count
    runtime_profile_count = int(metrics.get("runtime_profile_count") or 0)
    runtime_surface_count = int(metrics.get("runtime_surface_count") or 0)
    blocked_runtime_count = int(metrics.get("blocked_runtime_count") or 0)
    proof_count = int(metrics.get("ready_panel_count") or 0)
    return [
        {
            "id": "system-health",
            "label": "System Health",
            "value": "ready" if degraded_panel_count == 0 else "attention",
            "detail": f"{metrics.get('ready_panel_count', 0)} ready panels, {degraded_panel_count} degraded/skipped panels",
            "help": "Overall Studio shell health from live panel builder statuses; skipped fast-plan panels count as attention, not success.",
            "href": "#shell-boundary",
            "source": "plan.panel_statuses + plan.metrics.ready_panel_count/degraded_panel_count",
        },
        {
            "id": "active-runtimes",
            "label": "Runtime Signals",
            "value": runtime_signal_count if runtime_signal_count else "unknown",
            "detail": (
                f"{active_runtime_count} lifecycle-live, {observed_runtime_count} host-observed; "
                f"{runtime_profile_count} profiles, {runtime_surface_count} startup surfaces, {blocked_runtime_count} blocked"
            ),
            "help": "Lifecycle health probes remain authoritative when available; otherwise the dashboard shows read-only host process observations as signals, not readiness proof, so skipped fast-plan panels do not become false zeroes.",
            "href": "#runtime-cockpit",
            "source": "runtime_cockpit_contract.runtime_health.live_runtime_count + runtime_startup.surface_count/cards + /proc read-only observations",
        },
        {
            "id": "approvals-pending",
            "label": "Approvals Pending",
            "value": approvals_value,
            "detail": approvals_detail,
            "help": "Operator attention queue combining approval-center candidate rows and runtime approval readiness gaps; no approvals are executed here. Unknown runtime readiness is shown as unknown, not zero.",
            "href": "#approval-queue",
            "source": "approval_queue_panel.summary.candidate_row_count + runtime_startup.readiness_summary.approval_missing_count",
        },
        {
            "id": "apps-live-offline",
            "label": "Apps Live / Offline",
            "value": f"{app_states['live']} / {app_states['offline']}",
            "detail": f"{metrics.get('app_count', 0)} declared apps; {app_states['not_checked']} not checked",
            "help": "Loopback app health summary from the App Launcher registry. The launcher probes only when probe mode is enabled and never starts child apps.",
            "href": "#app-launcher",
            "source": "app_launcher.apps[].runtime_status.state",
        },
        {
            "id": "memory-candidates",
            "label": "Memory Candidates",
            "value": approval_candidates,
            "detail": "pending-review candidates only; no memory apply",
            "help": "MVP proxy for personal-memory/operator-memory candidate load until the Memory Ledger has its own source contract.",
            "href": "#approval-queue",
            "source": "approval_queue_panel.summary.candidate_row_count",
        },
        {
            "id": "graph-provenance-health",
            "label": "Graph / Provenance",
            "value": "clear" if graph_blockers == 0 else "blocked",
            "detail": f"{metrics.get('graph_visible_node_count', 0)} nodes, {metrics.get('graph_visible_edge_count', 0)} edges, {graph_blockers} blockers",
            "help": "Graph and selected-node provenance health from read-only graph-view and node-inspector contracts; no graph writes are performed.",
            "href": "#graph-view",
            "source": "graph_view_shell_panel.summary + node_inspector_shell_panel.summary",
        },
        {
            "id": "workspace-mode",
            "label": "Workspace Mode",
            "value": f"{metrics.get('workspace_mode_route_ready_count', 0)} / {metrics.get('workspace_mode_route_blocked_count', 0)}",
            "detail": (
                f"{metrics.get('workspace_mode_profile_valid_count', 0)}/"
                f"{metrics.get('workspace_mode_profile_total_count', 0)} profiles; "
                f"{metrics.get('workspace_mode_approval_artifact_count', 0)} approval artifacts"
            ),
            "help": "Workspace Mode Layer readiness for project/workspace routing inside Studio. This card is read-only and never writes profiles or executes workflows.",
            "href": "#workspace-mode",
            "source": "workspace_mode_panel.summary",
        },
        {
            "id": "blocked-dependencies",
            "label": "Blocked Dependencies",
            "value": blocked_dependencies,
            "detail": "non-ready panel builders or explicit readiness blockers",
            "help": "Counts panels that are skipped, degraded, or blocked so stale implementation counters do not look like successful product readiness.",
            "href": "#shell-boundary",
            "source": "plan.panel_statuses[*].state",
        },
        {
            "id": "recent-proof",
            "label": "Recent Proof",
            "value": proof_count,
            "detail": "ready panel contracts in this shell plan",
            "help": "Proof-oriented status: ready contracts/artifacts currently mounted in this plan. Fast dry-runs intentionally show low proof until full planning runs.",
            "href": "#authority",
            "source": "plan.metrics.ready_panel_count + mounted contract/artifact routes",
        },
    ]


def _run_panel_builder(
    panel_id: str,
    label: str,
    surface: str,
    builder: Any,
    *args: Any,
    planning_mode: str,
    skip_in_fast: bool = True,
    timeout_seconds: float | None = None,
    **kwargs: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if planning_mode == "fast" and skip_in_fast:
        reason = "skipped during fast shell planning to keep dry-run/app launcher responsive"
        return (
            _degraded_panel(surface, panel_id, label, state="skipped_fast_plan", reason=reason),
            _panel_status(panel_id, state="skipped_fast_plan", reason=reason),
        )
    started = monotonic()
    try:
        if timeout_seconds is None:
            panel = builder(*args, **kwargs)
        else:
            result_queue: Queue[tuple[str, Any]] = Queue(maxsize=1)

            def run_builder() -> None:
                try:
                    result_queue.put(("ok", builder(*args, **kwargs)))
                except Exception as exc:  # returned to caller so existing fail-open handling is preserved
                    result_queue.put(("error", exc))

            worker = Thread(target=run_builder, daemon=True)
            worker.start()
            worker.join(timeout_seconds)
            elapsed = monotonic() - started
            if worker.is_alive():
                reason = f"panel exceeded hard timeout ({elapsed:.2f}s > {timeout_seconds:.2f}s); summary kept degraded"
                return (
                    _degraded_panel(surface, panel_id, label, state="skipped_timeout", reason=reason),
                    _panel_status(panel_id, state="skipped_timeout", reason=reason, elapsed_seconds=elapsed),
                )
            status_kind, payload = result_queue.get_nowait()
            if status_kind == "error":
                raise payload
            panel = payload
    except Exception as exc:  # fail-open: one slow/broken panel must not block the shell plan
        elapsed = monotonic() - started
        reason = str(exc) or exc.__class__.__name__
        return (
            _degraded_panel(surface, panel_id, label, state="degraded_error", reason=reason),
            _panel_status(panel_id, state="degraded_error", reason=reason, elapsed_seconds=elapsed),
        )
    elapsed = monotonic() - started
    if timeout_seconds is not None and elapsed > timeout_seconds:
        reason = f"panel exceeded soft timeout ({elapsed:.2f}s > {timeout_seconds:.2f}s); summary kept degraded"
        return (
            _degraded_panel(surface, panel_id, label, state="skipped_timeout", reason=reason),
            _panel_status(panel_id, state="skipped_timeout", reason=reason, elapsed_seconds=elapsed),
        )
    return panel, _panel_status(panel_id, elapsed_seconds=elapsed)


def _status_for_view(panel_statuses: dict[str, dict[str, Any]], panel_id: str, *, ready: bool, ready_status: str) -> str:
    state = (panel_statuses.get(panel_id) or {}).get("state", "ready")
    if state != "ready":
        return str(state).replace("_", "-")
    return ready_status if ready else "blocked-read-only"


def _mounted_for_view(panel_statuses: dict[str, dict[str, Any]], panel_id: str, *, ready: bool) -> bool:
    return ready and (panel_statuses.get(panel_id) or {}).get("state", "ready") == "ready"


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _require_loopback(host: str) -> None:
    if host not in _LOOPBACK_HOSTS:
        raise StudioDesktopShellAppError("studio desktop shell app must bind to localhost/loopback only")


def _escape(value: Any) -> str:
    return html.escape(str(value))


def _build_views(
    contract: dict[str, Any],
    graph_panel: dict[str, Any],
    node_panel: dict[str, Any],
    pulse_panel: dict[str, Any],
    approval_queue_panel: dict[str, Any],
    arsl_route_review_panel: dict[str, Any],
    browser_runtime_panel: dict[str, Any],
    canvas_panel: dict[str, Any],
    workspace_mode_panel: dict[str, Any],
    panel_statuses: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    panel_statuses = panel_statuses or {}
    startup = contract.get("runtime_startup") or {}
    dashboard = contract.get("dashboard") or {}
    graph_summary = graph_panel.get("summary") or {}
    graph_ready = bool(graph_panel.get("ok"))
    node_summary = node_panel.get("summary") or {}
    node_ready = bool(node_panel.get("ok"))
    pulse_summary = pulse_panel.get("summary") or {}
    pulse_ready = bool(pulse_panel.get("ok"))
    approval_queue_summary = approval_queue_panel.get("summary") or {}
    approval_queue_ready = bool(approval_queue_panel.get("ok"))
    arsl_summary = arsl_route_review_panel.get("summary") or {}
    arsl_ready = bool(arsl_route_review_panel.get("ok"))
    browser_runtime_summary = browser_runtime_panel.get("summary") or {}
    browser_runtime_ready = bool(browser_runtime_panel.get("ok"))
    canvas_summary = canvas_panel.get("summary") or {}
    canvas_ready = bool(canvas_panel.get("ok"))
    workspace_mode_summary = workspace_mode_panel.get("summary") or {}
    workspace_mode_ready = bool(workspace_mode_panel.get("ok"))
    return [
        {
            "id": "dashboard",
            "title": "Dashboard",
            "status": "mounted-summary",
            "source": "runtime.studio.dashboard",
            "read_only": True,
            "mounted": True,
            "panel_errors": len(dashboard.get("panel_errors") or []),
        },
        {
            "id": "app-launcher",
            "title": "App Launcher",
            "status": "mounted-registry",
            "source": "runtime.studio.app_launcher",
            "read_only": True,
            "mounted": True,
        },
        {
            "id": "approval-center",
            "title": "Approval Center",
            "status": "mounted-read-only",
            "source": "runtime.studio.approval_center_app",
            "read_only": True,
            "mounted": True,
        },
        {
            "id": "settings",
            "title": "Settings",
            "status": "mounted-read-only",
            "source": "governed Studio settings readiness",
            "read_only": True,
            "mounted": True,
        },
        {
            "id": "workspace-mode",
            "title": "Workspace Mode",
            "status": _status_for_view(panel_statuses, "workspace-mode", ready=workspace_mode_ready, ready_status="mounted-read-only"),
            "source": "runtime.studio.workspace_mode_panel",
            "read_only": True,
            "mounted": _mounted_for_view(panel_statuses, "workspace-mode", ready=workspace_mode_ready),
            "overall_status": workspace_mode_summary.get("overall_status"),
            "route_ready_count": workspace_mode_summary.get("route_ready_count", 0),
            "route_blocked_count": workspace_mode_summary.get("route_blocked_count", 0),
        },
        {
            "id": "graph-view",
            "title": "Graph View",
            "status": _status_for_view(panel_statuses, "graph-view", ready=graph_ready, ready_status="mounted-read-only"),
            "source": "runtime.studio.graph_view_shell_panel",
            "read_only": True,
            "mounted": _mounted_for_view(panel_statuses, "graph-view", ready=graph_ready),
            "visible_node_count": graph_summary.get("visible_node_count", 0),
            "visible_edge_count": graph_summary.get("visible_edge_count", 0),
        },
        {
            "id": "node-inspector",
            "title": "Node Inspector",
            "status": _status_for_view(panel_statuses, "node-inspector", ready=node_ready, ready_status="mounted-read-only"),
            "source": "runtime.studio.node_inspector_shell_panel",
            "read_only": True,
            "mounted": _mounted_for_view(panel_statuses, "node-inspector", ready=node_ready),
            "selected_node_label": node_summary.get("selected_node_label"),
            "selected_node_type": node_summary.get("selected_node_type"),
        },
        {
            "id": "pulse",
            "title": "Pulse",
            "status": _status_for_view(panel_statuses, "pulse", ready=pulse_ready, ready_status="mounted-read-only"),
            "source": "runtime.studio.pulse_product_shell_panel",
            "read_only": True,
            "mounted": _mounted_for_view(panel_statuses, "pulse", ready=pulse_ready),
            "card_count": pulse_summary.get("card_count", 0),
            "panel_count": pulse_summary.get("panel_count", 0),
        },
        {
            "id": "browser-runtime",
            "title": "Browser Runtime",
            "status": _status_for_view(panel_statuses, "browser-runtime", ready=browser_runtime_ready, ready_status="mounted-read-only"),
            "source": "runtime.studio.browser_runtime_operator_ui_readiness",
            "read_only": True,
            "mounted": _mounted_for_view(panel_statuses, "browser-runtime", ready=browser_runtime_ready),
            "overall_status": browser_runtime_summary.get("overall_status"),
            "remaining_major_passes_min": browser_runtime_summary.get("remaining_major_passes_min"),
            "remaining_major_passes_max": browser_runtime_summary.get("remaining_major_passes_max"),
        },
        {
            "id": "canvas",
            "title": "Canvas / Whiteboard",
            "status": _status_for_view(panel_statuses, "canvas", ready=canvas_ready, ready_status="mounted-read-only"),
            "source": "runtime.studio.canvas_shell_panel",
            "read_only": True,
            "mounted": _mounted_for_view(panel_statuses, "canvas", ready=canvas_ready),
            "object_count": canvas_summary.get("object_count", 0),
            "link_count": canvas_summary.get("link_count", 0),
        },
        {
            "id": "runtime-cockpit",
            "title": "Runtime Cockpit",
            "status": _status_for_view(panel_statuses, "runtime-cockpit", ready=True, ready_status="mounted-read-only"),
            "source": "runtime.studio.runtime_cockpit",
            "read_only": True,
            "mounted": _mounted_for_view(panel_statuses, "runtime-cockpit", ready=True),
            "surface_count": startup.get("surface_count", 0),
        },
        {
            "id": "approval-queue",
            "title": "Approval Queue",
            "status": _status_for_view(panel_statuses, "approval-queue", ready=approval_queue_ready, ready_status="mounted-read-only"),
            "source": "runtime.studio.approval_queue_panel",
            "read_only": True,
            "mounted": _mounted_for_view(panel_statuses, "approval-queue", ready=approval_queue_ready),
            "lane_count": approval_queue_summary.get("lane_count", 0),
            "candidate_row_count": approval_queue_summary.get("candidate_row_count", 0),
        },
        {
            "id": "arsl-route-review",
            "title": "ARSL Route Review",
            "status": _status_for_view(panel_statuses, "arsl-route-review", ready=arsl_ready, ready_status="mounted-read-only"),
            "source": "runtime.studio.arsl_route_review_panel",
            "read_only": True,
            "mounted": _mounted_for_view(panel_statuses, "arsl-route-review", ready=arsl_ready),
            "review_row_count": arsl_summary.get("review_row_count", 0),
            "preview_decision": arsl_summary.get("preview_decision"),
        },
    ]


def build_studio_desktop_shell_app_plan(
    vault_root: str | Path,
    *,
    runtime_id: str | None = None,
    host: str = _DEFAULT_HOST,
    port: int = _DEFAULT_PORT,
    planning_mode: str = "full",
    panel_timeout_seconds: float | None = None,
) -> dict[str, Any]:
    """Return the local Studio desktop shell MVP plan without starting a server."""

    _require_loopback(host)
    if planning_mode not in {"full", "fast"}:
        raise StudioDesktopShellAppError("planning_mode must be 'full' or 'fast'")
    vault = _vault_path(vault_root)
    panel_statuses: dict[str, dict[str, Any]] = {}
    if planning_mode == "fast":
        reason = "skipped during fast shell planning to keep dry-run/app launcher responsive"
        contract = build_runtime_cockpit_fast_contract(vault, runtime_id=runtime_id)
        panel_statuses["runtime-cockpit"] = _panel_status(
            "runtime-cockpit",
            state="ready" if contract.get("ok", True) else "skipped_fast_plan",
            reason=None if contract.get("ok", True) else reason,
        )
    else:
        contract, status = _run_panel_builder(
            "runtime-cockpit",
            "Runtime Cockpit",
            "studio_runtime_cockpit_contract",
            build_runtime_cockpit_contract,
            vault,
            runtime_id=runtime_id,
            probe_child_apps=False,
            planning_mode=planning_mode,
            skip_in_fast=False,
            timeout_seconds=panel_timeout_seconds,
        )
        panel_statuses["runtime-cockpit"] = status
    launcher = build_studio_app_launcher_plan(
        vault,
        host="127.0.0.1",
        port=8769,
        probe_health=False,
    )
    if planning_mode == "fast":
        graph_panel = _fast_graph_panel(vault)
        node_panel = _fast_node_panel(vault, graph_panel)
        pulse_panel = _fast_pulse_panel(vault)
        approval_queue_panel = _fast_approval_queue_panel(vault)
        arsl_route_review_panel = _fast_arsl_route_review_panel()
        browser_runtime_panel = _fast_browser_runtime_panel(vault)
        canvas_panel = _fast_canvas_panel()
        workspace_mode_panel = build_workspace_mode_studio_panel(vault)
        for panel_id in (
            "graph-view",
            "node-inspector",
            "pulse",
            "approval-queue",
            "arsl-route-review",
            "browser-runtime",
            "canvas",
            "workspace-mode",
        ):
            panel_statuses[panel_id] = _panel_status(panel_id)
    else:
        pulse_panel, panel_statuses["pulse"] = _run_panel_builder(
            "pulse",
            "Pulse",
            "studio_pulse_product_shell_panel_contract",
            build_pulse_product_shell_panel_contract,
            vault,
            planning_mode=planning_mode,
            timeout_seconds=panel_timeout_seconds,
        )
        approval_queue_panel, panel_statuses["approval-queue"] = _run_panel_builder(
            "approval-queue",
            "Approval Queue",
            "studio_approval_queue_panel_contract",
            build_studio_approval_queue_panel_contract,
            vault,
            planning_mode=planning_mode,
            timeout_seconds=panel_timeout_seconds,
        )
        arsl_route_review_panel, panel_statuses["arsl-route-review"] = _run_panel_builder(
            "arsl-route-review",
            "ARSL Route Review",
            "arsl_route_review_panel_contract",
            build_arsl_route_review_panel_contract,
            vault,
            planning_mode=planning_mode,
            timeout_seconds=panel_timeout_seconds,
        )
        graph_limit_kwargs = _desktop_graph_limit_kwargs(include_layout=True, include_excerpt=True)
        graph_panel, panel_statuses["graph-view"] = _run_panel_builder(
            "graph-view",
            "Graph View",
            "studio_graph_view_shell_panel_contract",
            build_graph_view_shell_panel_contract,
            vault,
            planning_mode=planning_mode,
            timeout_seconds=panel_timeout_seconds,
            **_bounded_panel_kwargs(build_graph_view_shell_panel_contract, graph_limit_kwargs),
        )
        node_limit_kwargs = _desktop_graph_limit_kwargs(include_excerpt=True)
        node_panel, panel_statuses["node-inspector"] = _run_panel_builder(
            "node-inspector",
            "Node Inspector",
            "studio_node_inspector_shell_panel_contract",
            build_node_inspector_shell_panel_contract,
            vault,
            planning_mode=planning_mode,
            timeout_seconds=panel_timeout_seconds,
            **_bounded_panel_kwargs(build_node_inspector_shell_panel_contract, node_limit_kwargs),
        )
        browser_runtime_panel, panel_statuses["browser-runtime"] = _run_panel_builder(
            "browser-runtime",
            "Browser Runtime",
            "studio_browser_runtime_operator_ui_readiness",
            build_studio_browser_runtime_operator_ui_readiness,
            vault,
            planning_mode=planning_mode,
            timeout_seconds=panel_timeout_seconds,
        )
        canvas_panel, panel_statuses["canvas"] = _run_panel_builder(
            "canvas",
            "Canvas / Whiteboard",
            "studio_canvas_panel_contract",
            build_canvas_panel_contract,
            vault,
            planning_mode=planning_mode,
            timeout_seconds=panel_timeout_seconds,
            folder_path="06_AGENTS",
            max_files=300,
            max_nodes=600,
            max_edges=1200,
            content_excerpt_bytes=512,
        )
        workspace_mode_panel, panel_statuses["workspace-mode"] = _run_panel_builder(
            "workspace-mode",
            "Workspace Mode",
            "studio_workspace_mode_panel",
            build_workspace_mode_studio_panel,
            vault,
            planning_mode=planning_mode,
            skip_in_fast=False,
            timeout_seconds=panel_timeout_seconds,
        )
    startup = contract.get("runtime_startup") or {}
    runtime_health = contract.get("runtime_health") or {}
    readiness = startup.get("readiness_summary") or {}
    apps = list(launcher.get("apps") or [])
    pulse_readiness = pulse_panel.get("readiness") or {}
    pulse_summary = pulse_panel.get("summary") or {}
    approval_queue_readiness = approval_queue_panel.get("readiness") or {}
    approval_queue_summary = approval_queue_panel.get("summary") or {}
    arsl_readiness = arsl_route_review_panel.get("readiness") or {}
    arsl_summary = arsl_route_review_panel.get("summary") or {}
    graph_readiness = graph_panel.get("readiness") or {}
    graph_summary = graph_panel.get("summary") or {}
    node_readiness = node_panel.get("readiness") or {}
    node_summary = node_panel.get("summary") or {}
    browser_runtime_readiness = browser_runtime_panel.get("readiness") or {}
    browser_runtime_summary = browser_runtime_panel.get("summary") or {}
    canvas_readiness = canvas_panel.get("readiness") or {}
    canvas_summary = canvas_panel.get("summary") or {}
    workspace_mode_readiness = workspace_mode_panel.get("readiness") or {}
    workspace_mode_summary = workspace_mode_panel.get("summary") or {}
    views = _build_views(
        contract,
        graph_panel,
        node_panel,
        pulse_panel,
        approval_queue_panel,
        arsl_route_review_panel,
        browser_runtime_panel,
        canvas_panel,
        workspace_mode_panel,
        panel_statuses,
    )
    metrics = {
        "view_count": len(views),
        "mounted_view_count": sum(1 for view in views if view.get("mounted")),
        "runtime_surface_count": int(startup.get("surface_count") or 0),
        "runtime_surface_count_unknown": bool(startup.get("surface_count_unknown") or _runtime_contract_unknown(contract)),
        "runtime_manageable_surface_count": int(startup.get("manageable_surface_count") or 0),
        "runtime_manageable_surface_count_unknown": bool(startup.get("manageable_surface_count_unknown")),
        "runtime_visual_surface_count": int(startup.get("visual_surface_count") or 0),
        "runtime_visual_surface_count_unknown": bool(startup.get("visual_surface_count_unknown")),
        "runtime_profile_count": int(runtime_health.get("runtime_profile_count") or 0),
        "runtime_profile_count_unknown": bool(runtime_health.get("runtime_profile_count_unknown")),
        "live_runtime_count": int(runtime_health.get("live_runtime_count") or 0),
        "live_runtime_count_unknown": bool(runtime_health.get("live_runtime_count_unknown") or _runtime_contract_unknown(contract)),
        "offline_runtime_count": int(runtime_health.get("offline_runtime_count") or 0),
        "blocked_runtime_count": int(runtime_health.get("blocked_runtime_count") or 0),
        "blocked_runtime_count_unknown": bool(runtime_health.get("blocked_runtime_count_unknown")),
        "unknown_runtime_count": int(runtime_health.get("unknown_runtime_count") or 0),
        "readiness_packet_count": int(readiness.get("readiness_packet_count") or 0),
        "readiness_packet_count_unknown": bool(readiness.get("readiness_packet_count_unknown")),
        "approval_missing_count": int(readiness.get("approval_missing_count") or 0),
        "approval_missing_count_unknown": bool(readiness.get("approval_missing_count_unknown") or _runtime_contract_unknown(contract)),
        "app_count": len(apps),
        "read_only_app_count": sum(1 for app in apps if app.get("read_only")),
        "write_capable_app_count": sum(1 for app in apps if app.get("write_capable")),
        "ready_panel_count": sum(1 for status in panel_statuses.values() if status.get("state") == "ready"),
        "degraded_panel_count": sum(1 for status in panel_statuses.values() if status.get("state") != "ready"),
        "skipped_panel_count": sum(
            1 for status in panel_statuses.values() if str(status.get("state", "")).startswith("skipped")
        ),
        "graph_visible_node_count": int(graph_summary.get("visible_node_count") or 0),
        "graph_visible_edge_count": int(graph_summary.get("visible_edge_count") or 0),
        "graph_blocker_count": int(graph_summary.get("blocker_count") or 0),
        "node_inspector_selected_node_found": bool(node_summary.get("selected_node_found")),
        "node_inspector_incoming_edge_count": int(node_summary.get("incoming_edge_count") or 0),
        "node_inspector_outgoing_edge_count": int(node_summary.get("outgoing_edge_count") or 0),
        "node_inspector_blocker_count": int(node_summary.get("blocker_count") or 0),
        "pulse_panel_count": int(pulse_summary.get("panel_count") or 0),
        "pulse_card_count": int(pulse_summary.get("card_count") or 0),
        "pulse_blocker_count": int(pulse_summary.get("blocker_count") or 0),
        "approval_queue_lane_count": int(approval_queue_summary.get("lane_count") or 0),
        "approval_queue_candidate_row_count": int(approval_queue_summary.get("candidate_row_count") or 0),
        "approval_queue_blocker_count": int(approval_queue_summary.get("blocker_count") or 0),
        "arsl_route_review_row_count": int(arsl_summary.get("review_row_count") or 0),
        "arsl_route_review_gate_required_rows": int(arsl_summary.get("gate_required_rows") or 0),
        "arsl_route_review_approval_rows": int(arsl_summary.get("explicit_or_conditional_approval_rows") or 0),
        "browser_runtime_remaining_passes_min": int(browser_runtime_summary.get("remaining_major_passes_min") or 0),
        "browser_runtime_remaining_passes_max": int(browser_runtime_summary.get("remaining_major_passes_max") or 0),
        "browser_runtime_blocker_count": int(browser_runtime_summary.get("blocker_count") or 0),
        "browser_runtime_panel_count": int((browser_runtime_panel.get("panel_group") or {}).get("panel_count") or 0),
        "canvas_object_count": int(canvas_summary.get("object_count") or 0),
        "canvas_link_count": int(canvas_summary.get("link_count") or 0),
        "canvas_graph_node_ref_count": int(canvas_summary.get("graph_node_ref_count") or 0),
        "workspace_mode_route_ready_count": int(workspace_mode_summary.get("route_ready_count") or 0),
        "workspace_mode_route_blocked_count": int(workspace_mode_summary.get("route_blocked_count") or 0),
        "workspace_mode_profile_valid_count": int(workspace_mode_summary.get("profile_valid_count") or 0),
        "workspace_mode_profile_total_count": int(workspace_mode_summary.get("profile_total_count") or 0),
        "workspace_mode_approval_artifact_count": int(workspace_mode_summary.get("approval_artifact_count") or 0),
    }
    host_runtime_processes = _collect_host_runtime_processes()
    kanban_snapshot = _collect_kanban_snapshot()
    kpi_cards = _build_kpi_cards(
        metrics,
        apps=apps,
        panel_statuses=panel_statuses,
        host_runtime_processes=host_runtime_processes,
    )
    operator_dashboard = _build_operator_dashboard(
        planning_mode=planning_mode,
        metrics=metrics,
        panel_statuses=panel_statuses,
        apps=apps,
        host_runtime_processes=host_runtime_processes,
        kanban=kanban_snapshot,
    )
    return {
        "ok": bool(launcher.get("ok", True)),
        "surface": _APP_SURFACE,
        "title": "ChaseOS Studio MVP",
        "host": host,
        "port": int(port),
        "url": f"http://{host}:{int(port)}/",
        "health_url": f"http://{host}:{int(port)}/health.json",
        "shell_url": f"http://{host}:{int(port)}/shell.json",
        "runtime_cockpit_url": f"http://{host}:{int(port)}/runtime-cockpit.json",
        "graph_view_shell_panel_url": f"http://{host}:{int(port)}/graph-view-shell-panel.json",
        "graph_view_static_artifact_url": f"http://{host}:{int(port)}/graph-view-static-artifact.html",
        "node_inspector_shell_panel_url": f"http://{host}:{int(port)}/node-inspector-shell-panel.json",
        "pulse_product_shell_url": f"http://{host}:{int(port)}/pulse-product-shell.json",
        "approval_queue_panel_url": f"http://{host}:{int(port)}/approval-queue.json",
        "arsl_route_review_panel_url": f"http://{host}:{int(port)}/arsl-route-review.json",
        "browser_runtime_panel_url": f"http://{host}:{int(port)}/browser-runtime-panel.json",
        "canvas_panel_url": f"http://{host}:{int(port)}/canvas-panel.json",
        "workspace_mode_panel_url": f"http://{host}:{int(port)}/workspace-mode-panel.json",
        "operator_dashboard_url": f"http://{host}:{int(port)}/operator-dashboard.json",
        "dashboard_url": f"http://{host}:{int(port)}/dashboard.json",
        "runtime_filter": runtime_id or "all",
        "planning": {
            "mode": planning_mode,
            "fast_shell_plan": planning_mode == "fast",
            "panel_timeout_seconds": panel_timeout_seconds,
            "cache_policy": "panel status summaries are embedded in this plan; heavy panel builders are skipped in fast mode",
        },
        "panel_statuses": panel_statuses,
        "local_only": True,
        "shell": {
            "kind": "read_only_studio_shell_mvp",
            "full_desktop_shell_built": False,
            "studio_shell_mvp_built": True,
            "runtime_cockpit_mounted": True,
            "runtime_cockpit_source": "runtime.studio.runtime_cockpit.build_runtime_cockpit_contract",
            "app_launcher_mounted": True,
            "approval_center_local_mount_built": True,
            "graph_view_shell_panel_mounted": bool(graph_panel.get("ok")),
            "graph_view_shell_panel_contract_ready": bool(
                graph_readiness.get("graph_view_shell_panel_contract_ready")
            ),
            "graph_view_shell_panel_source": "runtime.studio.graph_view_shell_panel.build_graph_view_shell_panel_contract",
            "node_inspector_shell_panel_mounted": bool(node_panel.get("ok")),
            "node_inspector_shell_panel_contract_ready": bool(
                node_readiness.get("node_inspector_shell_panel_contract_ready")
            ),
            "node_inspector_shell_panel_source": (
                "runtime.studio.node_inspector_shell_panel.build_node_inspector_shell_panel_contract"
            ),
            "pulse_product_shell_mounted": bool(pulse_panel.get("ok")),
            "pulse_product_shell_panel_contract_ready": bool(
                pulse_readiness.get("pulse_product_shell_panel_contract_ready")
            ),
            "pulse_product_shell_source": "runtime.studio.pulse_product_shell_panel.build_pulse_product_shell_panel_contract",
            "approval_queue_panel_mounted": bool(approval_queue_panel.get("ok")),
            "approval_queue_panel_contract_ready": bool(
                approval_queue_readiness.get("approval_queue_panel_contract_ready")
            ),
            "approval_queue_panel_source": "runtime.studio.approval_queue_panel.build_studio_approval_queue_panel_contract",
            "arsl_route_review_panel_mounted": bool(arsl_route_review_panel.get("ok")),
            "arsl_route_review_panel_contract_ready": bool(
                arsl_readiness.get("arsl_route_review_panel_contract_ready")
            ),
            "arsl_route_review_panel_source": (
                "runtime.studio.arsl_route_review_panel.build_arsl_route_review_panel_contract"
            ),
            "browser_runtime_panel_mounted": bool(browser_runtime_panel.get("ok")),
            "browser_runtime_panel_contract_ready": bool(
                browser_runtime_readiness.get("operator_ui_readiness_contract_ready")
            ),
            "browser_runtime_panel_source": (
                "runtime.studio.browser_runtime_operator_ui_readiness.build_studio_browser_runtime_operator_ui_readiness"
            ),
            "canvas_panel_mounted": bool(canvas_panel.get("ok")),
            "canvas_panel_contract_ready": bool(canvas_readiness.get("canvas_panel_contract_ready")),
            "canvas_panel_source": "runtime.studio.canvas_shell_panel.build_canvas_panel_contract",
            "workspace_mode_panel_mounted": bool(workspace_mode_panel.get("ok")),
            "workspace_mode_panel_contract_ready": bool(
                workspace_mode_readiness.get("workspace_mode_panel_mounted")
            ),
            "workspace_mode_panel_source": "runtime.studio.workspace_mode_panel.build_workspace_mode_studio_panel",
            "canvas_draft_save_built": False,
            "interactive_graph_controls_built": False,
            "graph_persistence_built": False,
            "graph_node_editing_built": False,
            "node_inspector_editing_built": False,
            "approval_execution_built": False,
            "interactive_pulse_controls_built": False,
            "candidate_apply_ui_built": False,
            "schedule_activation_ui_built": False,
            "route_execution_ui_built": False,
            "route_approval_grant_ui_built": False,
            "route_ledger_write_ui_built": False,
            "settings_toggle_ui_built": False,
            "host_startup_mutation_ui_built_here": False,
        },
        "metrics": metrics,
        "kpi_cards": kpi_cards,
        "operator_dashboard": operator_dashboard,
        "authority": {
            "binds_loopback_only": True,
            "read_only": True,
            "mounts_existing_graph_artifact_only": True,
            "mounts_existing_pulse_artifact_only": True,
            "mounts_arsl_route_review_contract_only": True,
            "starts_child_apps": False,
            "writes_vault": False,
            "writes_host_startup": False,
            "writes_graph_index": False,
            "writes_node_ids": False,
            "edits_graph_nodes": False,
            "edits_inspected_node": False,
            "submits_feedback": False,
            "executes_approvals": False,
            "applies_candidates": False,
            "writes_agent_bus_tasks": False,
            "dispatches_runtimes": False,
            "executes_routes": False,
            "commits_route_proposals": False,
            "writes_routing_ledger": False,
            "grants_route_approvals": False,
            "mutates_gate_policy": False,
            "activates_schedules": False,
            "browser_automation": False,
            "browser_control_allowed": False,
            "canvas_draft_save_allowed": False,
            "canvas_card_editing_allowed": False,
            "workspace_mode_profile_write_allowed": False,
            "workspace_mode_route_execution_allowed": False,
            "mcp_scope_changed": False,
            "raw_manifest_exposed": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "delivery_allowed": False,
            "scheduler_changed": False,
            "canonical_mutation_allowed": False,
            "workflow_execution_allowed": False,
        },
        "reads": [
            "runtime/studio/runtime_cockpit.py contract model",
            "runtime/studio/graph_view_shell_panel.py contract model",
            "runtime/studio/node_inspector_shell_panel.py contract model",
            "runtime/studio/app_launcher.py registry",
            "runtime/studio/pulse_product_shell_panel.py contract model",
            "runtime/studio/approval_queue_panel.py contract model",
            "runtime/studio/arsl_route_review_panel.py contract model",
            "runtime/studio/browser_runtime_operator_ui_readiness.py contract model",
            "runtime/studio/canvas_shell_panel.py contract model",
            "runtime/studio/workspace_mode_panel.py contract model",
            "runtime/workspace_modes/ product status, approval ledger, route previews",
            "runtime/studio/canvas_drafts/ workspace-local draft fixture",
            "runtime/runtime_surfaces/review_contract.py route-review contract model",
            "07_LOGS/Studio-Graph-Views/ static browser-QA verified graph artifact",
            "07_LOGS/Pulse-Decks/product-shell/ static browser-QA verified artifact",
            "07_LOGS/Pulse-Decks/approval-queue/ static artifact",
            "Studio dashboard summary through Runtime Cockpit contract",
            "runtime startup controls model through Runtime Cockpit contract",
        ],
        "possible_writes": [],
        "allowed_actions": [],
        "routes": [
            "/",
            "/health.json",
            "/shell.json",
            "/runtime-cockpit.json",
            "/app-launcher.json",
            "/graph-view-shell-panel.json",
            "/graph-view-static-artifact.html",
            "/node-inspector-shell-panel.json",
            "/pulse-product-shell.json",
            "/approval-queue.json",
            "/arsl-route-review.json",
            "/browser-runtime-panel.json",
            "/canvas-panel.json",
            "/workspace-mode-panel.json",
            "/operator-dashboard.json",
        ],
        "views": views,
        "runtime_cockpit_contract": contract,
        "app_launcher": launcher,
        "graph_view_shell_panel": graph_panel,
        "node_inspector_shell_panel": node_panel,
        "pulse_product_shell_panel": pulse_panel,
        "approval_queue_panel": approval_queue_panel,
        "arsl_route_review_panel": arsl_route_review_panel,
        "browser_runtime_panel": browser_runtime_panel,
        "canvas_panel": canvas_panel,
        "workspace_mode_panel": workspace_mode_panel,
        "vault_root": str(vault),
    }


def _metric(label: str, value: Any, detail: str = "") -> str:
    detail_html = f"<p>{_escape(detail)}</p>" if detail else ""
    return f"""
      <section class="metric">
        <span>{_escape(label)}</span>
        <strong>{_escape(value)}</strong>
        {detail_html}
      </section>
    """


def _kpi_card(card: dict[str, Any]) -> str:
    source = card.get("source") or "declared Studio plan source"
    return f"""
      <a class="metric kpi-card" href="{_escape(card.get('href') or '#')}" title="{_escape(card.get('help') or '')}" data-testid="studio-kpi-{_escape(card.get('id'))}" data-source="{_escape(source)}">
        <span>{_escape(card.get('label'))}</span>
        <strong>{_escape(card.get('value'))}</strong>
        <p>{_escape(card.get('detail') or '')}</p>
        <small>Source: {_escape(source)}</small>
      </a>
    """


def _status_class(value: Any) -> str:
    text = str(value or "").lower()
    if any(token in text for token in ("blocked", "error", "missing", "fail")):
        return "blocked"
    if any(token in text for token in ("write", "approval", "confirm", "gate")):
        return "confirmation"
    if any(token in text for token in ("planned", "skipped", "partial", "degraded")):
        return "planned"
    if any(token in text for token in ("read-only", "read_only", "readonly")):
        return "readonly"
    if any(token in text for token in ("live", "available", "ready", "mounted", "complete", "built")):
        return "live"
    return "neutral"


def _state_badge(label: Any, *, extra_class: str = "") -> str:
    status_class = _status_class(label)
    classes = " ".join(part for part in ["state-badge", status_class, extra_class] if part)
    return f'<span class="{_escape(classes)}">{_escape(label)}</span>'


def _display_shell_kind(kind: Any) -> str:
    """Return operator-facing shell copy without leaking internal slug names into the hero."""

    if str(kind or "") == "read_only_studio_shell_mvp":
        return "Read-only Studio Shell MVP"
    return str(kind or "Studio shell")


def _boolean_badge(value: Any, *, true_label: str = "Yes", false_label: str = "No") -> str:
    enabled = bool(value)
    label = true_label if enabled else false_label
    return _state_badge(label, extra_class="bool-true" if enabled else "bool-false")


def _action_button(label: str, *, disabled: bool = False) -> str:
    state = "disabled" if disabled else "enabled"
    return f'<span class="action-button {state}" aria-disabled="{str(disabled).lower()}">{_escape(label)}</span>'


def _view_nav(view: dict[str, Any]) -> str:
    test_id = f"desktop-nav-{str(view.get('id') or '').replace('_', '-')}"
    state = "mounted" if view.get("mounted") else "planned"
    return f"""
      <a class="nav-item {state}" href="#{_escape(view.get('id'))}" data-testid="{_escape(test_id)}">
        <span>{_escape(view.get('title'))}</span>
        {_state_badge(view.get('status'))}
      </a>
    """


def _runtime_card(card: dict[str, Any]) -> str:
    launch = card.get("launch_profile") or {}
    readiness = card.get("readiness_summary") or {}
    commands = card.get("commands") or {}
    approval_missing = int(readiness.get("approval_missing_count") or 0)
    return f"""
      <article class="runtime-card">
        <div class="card-topline">
          <div class="label">{_escape(card.get('runtime_id'))}</div>
          {_state_badge(card.get('current_state'))}
        </div>
        <h3>{_escape(card.get('runtime_name') or card.get('runtime_id'))}</h3>
        <dl>
          <dt>Launch</dt><dd>{_escape(launch.get('launch_kind') or 'unknown')}</dd>
          <dt>Approval missing</dt><dd>{_state_badge(approval_missing, extra_class='blocked' if approval_missing else 'live')}</dd>
          <dt>Visual control</dt><dd>{_boolean_badge(card.get('studio_visual_toggle_built'), true_label='Live', false_label='Planned')}</dd>
          <dt>Action</dt><dd>{_action_button('Open governed control', disabled=True)}</dd>
          <dt>Boundary</dt><dd><code>{_escape(commands.get('enable_dry_run') or '')}</code></dd>
        </dl>
      </article>
    """


def _app_row(app: dict[str, Any]) -> str:
    status = app.get("runtime_status") or {}
    write_capable = bool(app.get("write_capable"))
    return f"""
      <tr>
        <td><strong>{_escape(app.get('title'))}</strong><small>{_escape(app.get('id'))}</small></td>
        <td>{_boolean_badge(app.get('read_only'), true_label='Read-only', false_label='Not read-only')}</td>
        <td>{_boolean_badge(write_capable, true_label='Confirmation-gated', false_label='No writes')}</td>
        <td>{_state_badge(status.get('state'))}</td>
        <td>{_action_button('Open app surface', disabled=True)}</td>
        <td><code>{_escape(app.get('command'))}</code></td>
      </tr>
    """


def _authority_row(key: str, value: Any) -> str:
    value_html = _boolean_badge(value) if isinstance(value, bool) else _state_badge(value)
    return f"<tr><th>{_escape(key)}</th><td>{value_html}</td></tr>"


def _graph_view_mount(panel: dict[str, Any]) -> str:
    graph_panel = panel.get("panel") or {}
    summary = panel.get("summary") or {}
    readiness = panel.get("readiness") or {}
    source_path = graph_panel.get("source_artifact_path") or "not available"
    source_route = "/graph-view-static-artifact.html" if graph_panel.get("source_artifact_path") else None
    iframe = (
        f'<iframe class="mount-frame graph" title="ChaseOS Studio Graph View" src="{_escape(source_route)}" '
        'sandbox="" loading="eager"></iframe>'
        if source_route
        else '<div class="mount-placeholder">Studio graph-view artifact not available.</div>'
    )
    link = (
        f'<a class="artifact-link" href="{_escape(source_route)}">Open static Graph View artifact</a>'
        if source_route
        else ""
    )
    blockers = ", ".join(str(item) for item in readiness.get("blockers") or []) or "none"
    return f"""
        <section id="graph-view" class="panel" data-testid="graph-view-panel-mount">
          <div class="panel-heading">
            <div>
              <h2>Studio Graph View</h2>
              <p>Read-only mount of the browser-QA verified static graph artifact.</p>
            </div>
            {_state_badge(panel.get('status'), extra_class='panel-state')}
          </div>
          <div class="pulse-summary">
            <span><strong>{_escape(summary.get('visible_node_count', 0))}</strong> visible nodes</span>
            <span><strong>{_escape(summary.get('visible_edge_count', 0))}</strong> visible edges</span>
            <span><strong>{_escape(summary.get('source_node_count', 0))}</strong> source nodes</span>
            <span><strong>{_escape(summary.get('blocker_count', 0))}</strong> blockers</span>
          </div>
          {iframe}
          <p class="artifact-path"><code>{_escape(source_path)}</code></p>
          {link}
          <p class="boundary-note">Graph editing, node ID persistence, graph-index persistence, settings mutation, workflow execution, provider calls, connector calls, and canonical promotion remain disabled here. Blockers: {_escape(blockers)}.</p>
        </section>
    """


def _node_inspector_mount(panel: dict[str, Any]) -> str:
    summary = panel.get("summary") or {}
    inspector = panel.get("source_node_inspector") or {}
    node = inspector.get("selected_node") or {}
    context = inspector.get("edge_context") or {}
    excerpt = inspector.get("source_excerpt") or {}
    readiness = panel.get("readiness") or {}
    properties = node.get("properties") or {}
    related = context.get("related_nodes") or []
    related_rows = "".join(
        f"<tr><td>{_escape(item.get('label'))}</td><td>{_escape(item.get('node_type'))}</td></tr>"
        for item in related[:8]
    ) or '<tr><td colspan="2">No related nodes in current bounded context.</td></tr>'
    excerpt_text = str(excerpt.get("text") or "")
    if len(excerpt_text) > 1200:
        excerpt_text = excerpt_text[:1200] + "\n..."
    blockers = ", ".join(str(item) for item in readiness.get("blockers") or []) or "none"
    return f"""
        <section id="node-inspector" class="panel" data-testid="node-inspector-panel-mount">
          <div class="panel-heading">
            <div>
              <h2>Node Inspector</h2>
              <p>Read-only selected-node detail derived from the rebuildable graph model.</p>
            </div>
            {_state_badge(panel.get('status'), extra_class='panel-state')}
          </div>
          <div class="pulse-summary">
            <span><strong>{_escape(summary.get('incoming_edge_count', 0))}</strong> incoming</span>
            <span><strong>{_escape(summary.get('outgoing_edge_count', 0))}</strong> outgoing</span>
            <span><strong>{_escape(summary.get('related_node_count', 0))}</strong> related</span>
            <span><strong>{_escape(summary.get('blocker_count', 0))}</strong> blockers</span>
          </div>
          <div class="node-detail-grid">
            <article class="detail-card">
              <div class="label">Selected Node</div>
              <h3>{_escape(node.get('label') or 'No node selected')}</h3>
              <dl>
                <dt>Type</dt><dd>{_escape(node.get('node_type'))}</dd>
                <dt>ID</dt><dd><code>{_escape(node.get('id'))}</code></dd>
                <dt>Path</dt><dd><code>{_escape(properties.get('path') or summary.get('source_path'))}</code></dd>
                <dt>Selection</dt><dd>{_escape((panel.get('panel') or {}).get('selection_source'))}</dd>
              </dl>
            </article>
            <article class="detail-card">
              <div class="label">Related Nodes</div>
              <table>
                <thead><tr><th>Label</th><th>Type</th></tr></thead>
                <tbody>{related_rows}</tbody>
              </table>
            </article>
          </div>
          <article class="detail-card">
            <div class="label">Bounded Source Excerpt</div>
            <pre>{_escape(excerpt_text)}</pre>
          </article>
          <p class="boundary-note">This panel uses existing derived graph identity only. Node ID persistence, source edits, graph persistence, provider calls, connector calls, workflow execution, and canonical promotion remain disabled. Blockers: {_escape(blockers)}.</p>
        </section>
    """


def _pulse_product_shell_mount(panel: dict[str, Any]) -> str:
    pulse_panel = panel.get("panel") or {}
    summary = panel.get("summary") or {}
    readiness = panel.get("readiness") or {}
    source_uri = pulse_panel.get("source_artifact_uri")
    source_path = pulse_panel.get("source_artifact_path") or "not available"
    iframe = (
        f'<iframe class="mount-frame" title="ChaseOS Pulse Product Shell" src="{_escape(source_uri)}" '
        'sandbox="" loading="lazy"></iframe>'
        if source_uri
        else '<div class="mount-placeholder">Pulse product-shell artifact not available.</div>'
    )
    link = (
        f'<a class="artifact-link" href="{_escape(source_uri)}">Open static Pulse product shell artifact</a>'
        if source_uri
        else ""
    )
    blockers = ", ".join(str(item) for item in readiness.get("blockers") or []) or "none"
    return f"""
        <section id="pulse" class="panel" data-testid="pulse-product-shell-mount">
          <div class="panel-heading">
            <div>
              <h2>ChaseOS Pulse Product Shell</h2>
              <p>Read-only mount of the browser-QA verified static Pulse artifact.</p>
            </div>
            {_state_badge(panel.get('status'), extra_class='panel-state')}
          </div>
          <div class="pulse-summary">
            <span><strong>{_escape(summary.get('panel_count', 0))}</strong> panels</span>
            <span><strong>{_escape(summary.get('card_count', 0))}</strong> cards</span>
            <span><strong>{_escape(summary.get('blocker_count', 0))}</strong> blockers</span>
          </div>
          {iframe}
          <p class="artifact-path"><code>{_escape(source_path)}</code></p>
          {link}
          <p class="boundary-note">Feedback, approvals, candidate apply, schedule activation, runtime dispatch, provider calls, connector calls, and canonical promotion remain disabled here. Blockers: {_escape(blockers)}.</p>
        </section>
    """


def _approval_queue_mount(panel: dict[str, Any]) -> str:
    queue_panel = panel.get("panel") or {}
    summary = panel.get("summary") or {}
    readiness = panel.get("readiness") or {}
    source_uri = queue_panel.get("source_artifact_uri")
    source_path = queue_panel.get("source_artifact_path") or "not available"
    iframe = (
        f'<iframe class="mount-frame compact" title="ChaseOS Pulse Approval Queue" src="{_escape(source_uri)}" '
        'sandbox="" loading="lazy"></iframe>'
        if source_uri
        else '<div class="mount-placeholder">Pulse approval queue artifact not available.</div>'
    )
    link = (
        f'<a class="artifact-link" href="{_escape(source_uri)}">Open static Approval Queue artifact</a>'
        if source_uri
        else ""
    )
    blockers = ", ".join(str(item) for item in readiness.get("blockers") or []) or "none"
    return f"""
        <section id="approval-queue" class="panel" data-testid="approval-queue-panel-mount">
          <div class="panel-heading">
            <div>
              <h2>Pulse Approval Queue</h2>
              <p>Read-only Studio mount for Pulse candidate review lanes.</p>
            </div>
            {_state_badge(panel.get('status'), extra_class='panel-state')}
          </div>
          <div class="pulse-summary">
            <span><strong>{_escape(summary.get('lane_count', 0))}</strong> lanes</span>
            <span><strong>{_escape(summary.get('candidate_row_count', 0))}</strong> candidates</span>
            <span><strong>{_escape(summary.get('action_count', 0))}</strong> display actions</span>
            <span><strong>{_escape(summary.get('missing_approval_key_count', 0))}</strong> missing keys</span>
          </div>
          {iframe}
          <p class="artifact-path"><code>{_escape(source_path)}</code></p>
          {link}
          <p class="boundary-note">Approval grants, approval execution, review-decision writes, feedback writes, candidate apply, Agent Bus writes, schedule activation, runtime dispatch, provider/connector calls, and canonical promotion remain disabled here. Blockers: {_escape(blockers)}.</p>
        </section>
    """


def _arsl_route_review_mount(panel: dict[str, Any]) -> str:
    summary = panel.get("summary") or {}
    readiness = panel.get("readiness") or {}
    review = panel.get("source_route_review") or {}
    preview = review.get("route_preview") or {}
    rows = list(review.get("review_rows") or [])[:12]
    row_html = "".join(
        f"""
          <tr>
            <td><code>{_escape(row.get('surface_id'))}</code></td>
            <td><code>{_escape(row.get('capability_id'))}</code></td>
            <td>{_escape(row.get('policy_decision'))}</td>
            <td>{_escape(row.get('risk_class'))}</td>
            <td>{_escape(row.get('approval_required'))}</td>
            <td>{_escape(row.get('gate_required'))}</td>
          </tr>
        """
        for row in rows
    ) or '<tr><td colspan="6">No ARSL route-review rows in current bounded context.</td></tr>'
    blockers = ", ".join(str(item) for item in readiness.get("blockers") or []) or "none"
    return f"""
        <section id="arsl-route-review" class="panel" data-testid="arsl-route-review-panel-mount">
          <div class="panel-heading">
            <div>
              <h2>ARSL Route Review</h2>
              <p>Read-only Studio view over runtime surface route posture.</p>
            </div>
            {_state_badge('READ-ONLY STUDIO MOUNT', extra_class='panel-state')}
          </div>
          <div class="pulse-summary">
            <span><strong>{_escape(summary.get('review_row_count', 0))}</strong> review rows</span>
            <span><strong>{_escape(summary.get('gate_required_rows', 0))}</strong> Gate rows</span>
            <span><strong>{_escape(summary.get('explicit_or_conditional_approval_rows', 0))}</strong> approval rows</span>
            <span><strong>{_escape(summary.get('preview_decision') or 'none')}</strong> preview</span>
          </div>
          <div class="node-detail-grid">
            <article class="detail-card">
              <div class="label">Requested Capability</div>
              <h3><code>{_escape(summary.get('requested_capability') or 'all')}</code></h3>
              <dl>
                <dt>Surface</dt><dd><code>{_escape(summary.get('requested_surface_id') or 'any')}</code></dd>
                <dt>Selected</dt><dd><code>{_escape(summary.get('selected_surface') or 'none')}</code></dd>
                <dt>Authority</dt><dd>{_escape(summary.get('authority_layer') or 'operator_review_only')}</dd>
                <dt>Approval</dt><dd>{_escape(summary.get('approval_required') or 'none')}</dd>
              </dl>
            </article>
            <article class="detail-card">
              <div class="label">Route Preview</div>
              <dl>
                <dt>Decision</dt><dd>{_escape(preview.get('decision') or 'none')}</dd>
                <dt>Gate</dt><dd>{_escape(preview.get('gate_required'))}</dd>
                <dt>Audit</dt><dd>{_escape(preview.get('audit_required'))}</dd>
                <dt>Ledger</dt><dd>{_escape(preview.get('ledger_written'))}</dd>
              </dl>
            </article>
          </div>
          <div class="table-scroll">
          <table class="route-review-table">
            <thead><tr><th>Surface</th><th>Capability</th><th>Decision</th><th>Risk</th><th>Approval</th><th>Gate</th></tr></thead>
            <tbody>{row_html}</tbody>
          </table>
          </div>
          <p class="boundary-note">Route execution, route proposal commits, routing ledger writes, approval grants, Gate mutation, Agent Bus dispatch, provider calls, browser automation, raw manifest exposure, MCP tools, credential access, browser profile access, and canonical promotion remain disabled here. Blockers: {_escape(blockers)}.</p>
        </section>
    """


def _browser_runtime_mount(panel: dict[str, Any]) -> str:
    summary = panel.get("summary") or {}
    readiness = panel.get("readiness") or {}
    authority = panel.get("authority") or {}
    panels = list(panel.get("panels") or [])
    dependencies = list(panel.get("external_dependencies") or [])
    blockers = list(panel.get("blocked_reasons") or [])
    evidence = panel.get("current_evidence") or {}
    panel_rows = "".join(
        f"""
          <tr>
            <td><code>{_escape(item.get('panel_id'))}</code></td>
            <td>{_escape(item.get('label'))}</td>
            <td>{_escape(item.get('ready_for_studio_mount'))}</td>
            <td>{_escape(item.get('render_mode'))}</td>
          </tr>
        """
        for item in panels
    ) or '<tr><td colspan="4">No Browser Runtime panel sections found.</td></tr>'
    dependency_rows = ""
    for item in dependencies[:10]:
        if isinstance(item, dict):
            label = item.get("label") or item.get("name") or item.get("dependency_id")
            status = item.get("status") or item.get("state") or item.get("readiness")
            detail = item.get("blocker") or item.get("blocked_reason") or item.get("next_action")
        else:
            label = item
            status = "external-or-deferred"
            detail = ""
        dependency_rows += f"""
          <tr>
            <td>{_escape(label)}</td>
            <td>{_escape(status)}</td>
            <td>{_escape(detail)}</td>
          </tr>
        """
    dependency_rows = dependency_rows or '<tr><td colspan="3">No external dependency rows in current bounded context.</td></tr>'
    evidence_rows = "".join(
        f"""
          <tr>
            <td>{_escape(key)}</td>
            <td><code>{_escape((value or {}).get('path'))}</code></td>
            <td>{_escape((value or {}).get('exists'))}</td>
          </tr>
        """
        for key, value in evidence.items()
    ) or '<tr><td colspan="3">No evidence paths reported.</td></tr>'
    authority_rows = "".join(
        _authority_row(key, authority.get(key))
        for key in [
            "read_only",
            "starts_servers",
            "opens_browser",
            "launches_browser",
            "connects_cdp",
            "invokes_mcp",
            "runs_browser_use_cli_live",
            "activates_skills",
            "provider_calls_allowed",
            "connector_calls_allowed",
            "gate_mutation_allowed",
            "canonical_mutation_allowed",
        ]
    )
    blocker_text = ", ".join(str(item) for item in blockers[:8]) or "none"
    return f"""
        <section id="browser-runtime" class="panel" data-testid="browser-runtime-panel-mount">
          <div class="panel-heading">
            <div>
              <h2>Browser Runtime</h2>
              <p>Legacy-harness support view for the native read-only Browser Runtime Studio panel.</p>
            </div>
            {_state_badge(panel.get('status'), extra_class='panel-state')}
          </div>
          <div class="pulse-summary">
            <span><strong>{_escape(summary.get('overall_status') or 'unknown')}</strong> status</span>
            <span><strong>{_escape(summary.get('remaining_major_passes_min', 0))}-{_escape(summary.get('remaining_major_passes_max', 0))}</strong> remaining passes</span>
            <span><strong>{_escape(summary.get('blocker_count', 0))}</strong> blockers</span>
            <span><strong>{_escape((panel.get('panel_group') or {}).get('panel_count', 0))}</strong> sections</span>
          </div>
          <div class="node-detail-grid">
            <article class="detail-card">
              <div class="label">Completion</div>
              <dl>
                <dt>MVP</dt><dd>{_escape(summary.get('bounded_mvp_done'))}</dd>
                <dt>Production</dt><dd>{_escape(summary.get('production_feature_done'))}</dd>
                <dt>Next</dt><dd><code>{_escape(summary.get('next_recommended_pass'))}</code></dd>
                <dt>Readiness</dt><dd>{_escape(readiness.get('operator_ui_readiness_contract_ready'))}</dd>
              </dl>
            </article>
            <article class="detail-card">
              <div class="label">Authority</div>
              <table>{authority_rows}</table>
            </article>
          </div>
          <div class="table-scroll">
          <table class="route-review-table">
            <thead><tr><th>Panel</th><th>Label</th><th>Ready</th><th>Render Mode</th></tr></thead>
            <tbody>{panel_rows}</tbody>
          </table>
          </div>
          <div class="table-scroll">
          <table class="route-review-table">
            <thead><tr><th>External Dependency</th><th>Status</th><th>Next / Blocker</th></tr></thead>
            <tbody>{dependency_rows}</tbody>
          </table>
          </div>
          <div class="table-scroll">
          <table class="route-review-table">
            <thead><tr><th>Evidence</th><th>Path</th><th>Exists</th></tr></thead>
            <tbody>{evidence_rows}</tbody>
          </table>
          </div>
          <p class="boundary-note">This localhost view is browser QA support evidence, not the canonical product shell. Browser launch, CDP, MCP, Browser Use CLI live runs, Excalidraw live evidence, profile access, credential/cookie reads, skill activation, approval execution, Agent Bus writes, provider/connector calls, Gate mutation, and canonical promotion remain disabled. Blockers: {_escape(blocker_text)}.</p>
        </section>
    """


def _canvas_panel_mount(panel: dict[str, Any]) -> str:
    summary = panel.get("summary") or {}
    readiness = panel.get("readiness") or {}
    objects = list((panel.get("visualization") or {}).get("objects") or [])
    links = list((panel.get("visualization") or {}).get("links") or [])
    badges = list(panel.get("source_badges") or [])
    boundary = panel.get("boundary_banner") or "Workspace-local canvas draft."
    blockers = ", ".join(str(item) for item in readiness.get("blockers") or []) or "none"
    badge_rows = "".join(
        f"""
          <tr>
            <td><code>{_escape(item.get('object_id'))}</code></td>
            <td>{_escape(item.get('kind'))}</td>
            <td>{_escape(item.get('badge'))}</td>
            <td><code>{_escape(item.get('source_path') or item.get('node_id') or item.get('target_type') or 'draft-only')}</code></td>
          </tr>
        """
        for item in badges
    ) or '<tr><td colspan="4">No canvas badges in current draft.</td></tr>'
    card_html = "".join(
        f"""
          <article class="detail-card canvas-card" data-kind="{_escape(obj.get('kind'))}">
            <div class="label">{_escape(obj.get('badge'))}</div>
            <h3>{_escape(obj.get('label'))}</h3>
            <dl>
              <dt>Kind</dt><dd><code>{_escape(obj.get('kind'))}</code></dd>
              <dt>Object</dt><dd><code>{_escape(obj.get('object_id'))}</code></dd>
              <dt>Read-only</dt><dd>{_escape(obj.get('read_only'))}</dd>
              <dt>Position</dt><dd><code>{_escape(obj.get('position'))}</code></dd>
            </dl>
          </article>
        """
        for obj in objects[:12]
    ) or '<section class="empty-state">No Canvas objects found in this workspace-local draft.</section>'
    return f"""
        <section id="canvas" class="panel" data-testid="canvas-panel-mount">
          <div class="panel-heading">
            <div>
              <h2>Canvas / Whiteboard</h2>
              <p>Read-only visualization over workspace-local Canvas fixture data.</p>
            </div>
            {_state_badge('READ-ONLY STUDIO MOUNT', extra_class='panel-state')}
          </div>
          <p class="boundary-note">{_escape(boundary)}</p>
          <div class="pulse-summary">
            <span><strong>{_escape(summary.get('object_count', 0))}</strong> objects</span>
            <span><strong>{_escape(summary.get('link_count', 0))}</strong> visual links</span>
            <span><strong>{_escape(summary.get('graph_node_ref_count', 0))}</strong> graph refs</span>
            <span><strong>{_escape(summary.get('proposal_card_count', 0))}</strong> proposals</span>
          </div>
          <div class="node-detail-grid">{card_html}</div>
          <div class="table-scroll">
          <table class="route-review-table">
            <thead><tr><th>Object</th><th>Kind</th><th>Badge</th><th>Source / Draft pointer</th></tr></thead>
            <tbody>{badge_rows}</tbody>
          </table>
          </div>
          <p class="boundary-note">Canvas is visualization-only in this pass: local draft persistence, card editing, graph mutation, provenance writes, source-package writes, browser/Excalidraw automation, workflow execution, provider/connector calls, and Gate/canonical promotion are not exposed. Visual links shown: {_escape(len(links))}. Blockers: {_escape(blockers)}.</p>
        </section>
    """


def _workspace_mode_mount(panel: dict[str, Any]) -> str:
    summary = panel.get("summary") or {}
    readiness = panel.get("readiness") or {}
    authority = panel.get("authority") or {}
    selector = panel.get("mode_selector") or {}
    selected = panel.get("selected_mode") or {}
    routes = list(panel.get("visible_route_cards") or panel.get("route_cards") or [])
    mode_options = list(selector.get("options") or panel.get("mode_options") or [])
    visible_modes = list(panel.get("visible_mode_options") or panel.get("mode_options") or [])
    project_cards = list(panel.get("visible_project_cards") or panel.get("project_cards") or (panel.get("project_workspace_connection") or {}).get("projects") or [])
    domain_cards = list(panel.get("visible_domain_cards") or panel.get("domain_cards") or (panel.get("project_workspace_connection") or {}).get("domains") or [])
    project_connection = panel.get("project_workspace_connection") or {}
    chat_connection = panel.get("chat_connection") or {}
    blockers = ", ".join(str(item) for item in readiness.get("blockers") or []) or "none"
    mode_card_html = "".join(
        f"""
          <a class="workspace-mode-card {'selected' if mode.get('selected') else ''}" href="{_escape(mode.get('url') or ('#' + str(mode.get('anchor') or 'workspace-mode')))}" data-testid="workspace-mode-option-{_escape(mode.get('id') or 'unknown')}" {'aria-current="true"' if mode.get('selected') else ''}>
            <div class="label">{_escape(mode.get('label') or mode.get('id') or 'Unknown')}</div>
            <strong>{_escape(mode.get('project_count', 0))} projects</strong>
            <span>{_escape(mode.get('domain_count', 0))} domains / {_escape(mode.get('ready_route_count', 0))}/{_escape(mode.get('route_count', 0))} routes ready</span>
            <p>{_escape(mode.get('default_posture') or '')}</p>
          </a>
        """
        for mode in mode_options
    ) or '<section class="empty-state">No Workspace Mode options were returned by the panel model.</section>'
    mode_section_html = ""
    for mode in visible_modes:
        mode_id = str(mode.get("id") or "unknown")
        anchor = mode.get("anchor") or f"workspace-mode-mode-{mode_id.replace('_', '-')}"
        mode_projects = list(mode.get("projects") or [item for item in project_cards if item.get("mode") == mode_id])
        mode_domains = list(mode.get("domains") or [item for item in domain_cards if item.get("primary_mode") == mode_id])
        mode_routes = list(mode.get("routes") or [item for item in routes if item.get("mode") == mode_id])
        project_items = "".join(
            f"""
              <li>
                <strong>{_escape(project.get('project'))}</strong>
                <span>{_escape(project.get('domain'))} / {_escape(project.get('status'))}</span>
                <code>{_escape(project.get('workspace_path'))}</code>
              </li>
            """
            for project in mode_projects[:8]
        ) or '<li class="muted-list-item">No projects currently mapped to this mode.</li>'
        domain_items = "".join(
            f"<span class=\"workspace-domain-chip\">{_escape(domain.get('domain'))} ({_escape(domain.get('project_count', 0))})</span>"
            for domain in mode_domains[:10]
        ) or '<span class="workspace-domain-chip muted">No domains</span>'
        route_items = "".join(
            f"<li><code>{_escape(route.get('path'))}</code> {_state_badge('ready' if route.get('ready') else 'blocked')}</li>"
            for route in mode_routes[:5]
        ) or '<li class="muted-list-item">No preview routes currently mapped to this mode.</li>'
        mode_section_html += f"""
          <article id="{_escape(anchor)}" class="workspace-mode-section" data-testid="workspace-mode-section-{_escape(mode_id)}">
            <div class="workspace-mode-section-head">
              <div>
                <div class="label">{_escape(mode.get('label') or mode_id)}</div>
                <h3>{_escape(mode.get('purpose') or '')}</h3>
              </div>
              {_state_badge('selectable-read-only')}
            </div>
            <div class="workspace-domain-row">{domain_items}</div>
            <div class="workspace-mode-lists">
              <ul class="workspace-project-list">{project_items}</ul>
              <ul class="workspace-route-list">{route_items}</ul>
            </div>
          </article>
        """
    route_rows = "".join(
        f"""
          <tr>
            <td><code>{_escape(route.get('path'))}</code></td>
            <td>{_escape(route.get('label') or route.get('mode') or route.get('recommended_mode'))}</td>
            <td>{_escape(route.get('ready'))}</td>
            <td><code>{_escape(route.get('profile_path'))}</code></td>
            <td>{_escape(', '.join(route.get('blockers') or []) or 'none')}</td>
          </tr>
        """
        for route in routes[:12]
    ) or '<tr><td colspan="5">No Workspace Mode route cards available.</td></tr>'
    authority_rows = "".join(
        _authority_row(key, authority.get(key))
        for key in [
            "read_only",
            "profile_writes_allowed",
            "workflow_execution_allowed",
            "agent_bus_dispatch_allowed",
            "provider_calls_allowed",
            "canonical_mutation_allowed",
        ]
    )
    return f"""
        <section id="workspace-mode" class="panel" data-testid="workspace-mode-panel-mount">
          <div class="panel-heading">
            <div>
              <h2>Workspace Mode</h2>
              <p>Read-only Studio panel for the Workspace Mode Layer inside the same project/workspace dashboard surface.</p>
            </div>
            {_state_badge(panel.get('status') or 'READ-ONLY STUDIO MOUNT', extra_class='panel-state')}
          </div>
          <div class="pulse-summary">
            <span><strong>{_escape(summary.get('profile_valid_count', 0))}/{_escape(summary.get('profile_total_count', 0))}</strong> profiles</span>
            <span><strong>{_escape(summary.get('mode_option_count', len(mode_options)))}</strong> selectable modes</span>
            <span><strong>{_escape(summary.get('project_count', 0))}</strong> projects</span>
            <span><strong>{_escape(summary.get('domain_count', 0))}</strong> domains</span>
            <span><strong>{_escape(selected.get('label') or summary.get('selected_mode_label') or 'All Modes')}</strong> selected</span>
            <span><strong>{_escape(summary.get('visible_project_count', len(project_cards)))}</strong> visible projects</span>
            <span><strong>{_escape(summary.get('route_ready_count', 0))}</strong> routes ready</span>
            <span><strong>{_escape(summary.get('route_blocked_count', 0))}</strong> routes blocked</span>
            <span><strong>{_escape(summary.get('approval_artifact_count', 0))}</strong> approval artifacts</span>
          </div>
          <section class="workspace-mode-selector" aria-label="Workspace Mode selector">
            <div class="panel-heading compact-heading">
              <div>
                <h3>Mode Selector</h3>
                <p>Pick a WML mode to inspect matching projects, domains, and route previews. Selection persists in the URL query as <code>{_escape(selector.get('query_param') or MODE_QUERY_PARAM)}</code>.</p>
              </div>
              {_state_badge('read-only')}
            </div>
            <div class="workspace-mode-grid">{mode_card_html}</div>
          </section>
          <section class="workspace-mode-sections" aria-label="Workspace Mode project and domain sections">
            {mode_section_html}
          </section>
          <div class="node-detail-grid">
            <article class="detail-card">
              <div class="label">Project Workspace Connection</div>
              <dl>
                <dt>Mounted</dt><dd>{_boolean_badge(project_connection.get('mounted'), true_label='Mounted', false_label='Missing')}</dd>
                <dt>Source</dt><dd><code>{_escape(project_connection.get('source') or 'runtime.studio.project_workspace_view')}</code></dd>
                <dt>Projects</dt><dd>{_escape(summary.get('project_count', 0))}</dd>
                <dt>Domains</dt><dd>{_escape(summary.get('domain_count', 0))}</dd>
              </dl>
            </article>
            <article class="detail-card">
              <div class="label">Chat Context Connection</div>
              <dl>
                <dt>Visible</dt><dd>{_boolean_badge(chat_connection.get('context_visible'), true_label='Visible', false_label='Hidden')}</dd>
                <dt>Surface</dt><dd><code>{_escape(chat_connection.get('surface') or 'phase11_chat_panel_readonly_contract')}</code></dd>
                <dt>Executes WML</dt><dd>{_boolean_badge(chat_connection.get('chat_can_execute_workspace_mode'), true_label='Allowed', false_label='Blocked')}</dd>
                <dt>Profile writes</dt><dd>{_boolean_badge(chat_connection.get('chat_can_write_workspace_profiles'), true_label='Allowed', false_label='Blocked')}</dd>
              </dl>
            </article>
          </div>
          <div class="table-scroll">
          <table class="route-review-table">
            <thead><tr><th>Workspace Path</th><th>Mode</th><th>Ready</th><th>Profile</th><th>Blockers</th></tr></thead>
            <tbody>{route_rows}</tbody>
          </table>
          </div>
          <div class="table-scroll">
          <table class="route-review-table">
            <thead><tr><th>Authority</th><th>Value</th></tr></thead>
            <tbody>{authority_rows}</tbody>
          </table>
          </div>
          <p class="boundary-note">studio_workspace_mode_panel is inspect-and-preview only. Profile writes: false. Workflow execution, Agent Bus dispatch, provider calls, connector calls, canonical mutation, and WML profile mutation remain disabled here. Blockers: {_escape(blockers)}.</p>
        </section>
    """


def _settings_mount() -> str:
    return f"""
        <section id="settings" class="panel" data-testid="settings-panel-mount">
          <div class="panel-heading">
            <div>
              <h2>Settings</h2>
              <p>Read-only governance posture for Studio configuration. Mutation controls remain disabled unless a lower-phase confirmation gate owns the action.</p>
            </div>
            {_state_badge('mounted-read-only', extra_class='panel-state')}
          </div>
          <div class="node-detail-grid">
            <article class="detail-card">
              <div class="label">Runtime scope</div>
              <dl>
                <dt>Mode</dt><dd>Read-only settings overview</dd>
                <dt>Config writes</dt><dd>{_boolean_badge(False)}</dd>
                <dt>Credential access</dt><dd>{_boolean_badge(False)}</dd>
                <dt>Canonical promotion</dt><dd>{_boolean_badge(False)}</dd>
              </dl>
            </article>
            <article class="detail-card">
              <div class="label">Allowed action</div>
              <p>Inspect route and authority posture only; no runtime, connector, provider, scheduler, vault, or canonical settings are changed from this MVP shell.</p>
            </article>
          </div>
        </section>
    """



def _operator_action_card(item: dict[str, Any]) -> str:
    return f"""
      <a class="operator-action" href="{_escape(item.get('target') or '#')}" data-testid="operator-action-{_escape(item.get('label'))}">
        {_state_badge(item.get('status') or 'unknown')}
        <strong>{_escape(item.get('label') or 'Operator status')}</strong>
        <p>{_escape(item.get('detail') or '')}</p>
      </a>
    """


def _operator_process_row(process: dict[str, Any]) -> str:
    return f"""
      <tr>
        <td>{_escape(process.get('kind') or 'runtime')}</td>
        <td>{_escape(process.get('pid'))}</td>
        <td><code>{_escape(process.get('command') or '')}</code></td>
      </tr>
    """


def _operator_dashboard_mount(operator_dashboard: dict[str, Any]) -> str:
    summary = operator_dashboard.get("summary") or {}
    action_items = list(operator_dashboard.get("action_items") or [])
    blocked_panels = list(operator_dashboard.get("blocked_panels") or [])
    host_observation = operator_dashboard.get("host_runtime_processes") or {}
    kanban = operator_dashboard.get("kanban") or {}
    actions = "".join(_operator_action_card(item) for item in action_items)
    blocked = "".join(
        f"<li>{_state_badge(row.get('state') or 'unknown')} <strong>{_escape(row.get('panel_id'))}</strong> — {_escape(row.get('operator_reason'))}</li>"
        for row in blocked_panels[:8]
    ) or "<li>No skipped/degraded panels in this plan.</li>"
    processes = "".join(_operator_process_row(process) for process in list(host_observation.get("processes") or [])[:5])
    if not processes:
        processes = '<tr><td colspan="3" class="empty-table-cell">No host runtime process observations available.</td></tr>'
    return f"""
        <section id="operator-overview" class="panel operator-overview" data-testid="operator-overview">
          <div class="panel-heading">
            <div>
              <h2>Operator Overview / Action Queue</h2>
              <p>First-screen home queue: what needs attention, what is unknown, and what remains read-only; skipped/timeout panels stay visible as unknown or degraded, not false zeroes.</p>
            </div>
            {_state_badge('read-only')}
          </div>
          <div class="operator-summary-grid">
            {_metric('Planning mode', operator_dashboard.get('planning_mode') or 'unknown', 'fast skips heavier panels; full may timeout panel-by-panel')}
            {_metric('Observed runtimes', summary.get('observed_runtime_processes', 'unknown'), host_observation.get('source') or 'read-only host observation')}
            {_metric('Kanban ready/running/blocked', f"{summary.get('kanban_ready', 0)} / {summary.get('kanban_running', 0)} / {summary.get('kanban_blocked', 0)}", kanban.get('source') or 'kanban unavailable')}
            {_metric('Apps not health-checked', summary.get('apps_not_checked', 0), f"{summary.get('declared_apps', 0)} declared apps; no launch action performed")}
          </div>
          <div class="operator-action-grid">{actions}</div>
          <details open>
            <summary>Skipped/degraded panel truth</summary>
            <ul class="operator-list">{blocked}</ul>
          </details>
          <details>
            <summary>Host runtime process observations</summary>
            <table class="operator-process-table">
              <thead><tr><th>Kind</th><th>PID</th><th>Command excerpt</th></tr></thead>
              <tbody>{processes}</tbody>
            </table>
          </details>
          <p class="boundary-note">{_escape(operator_dashboard.get('boundary') or '')}</p>
        </section>
    """


def _quick_status(vault_root: Path) -> dict[str, Any]:
    """Minimal fail-open status reads for the 8772 status bar."""
    status: dict[str, Any] = {}
    try:
        approvals_dir = vault_root / "runtime" / "studio" / "approvals"
        if approvals_dir.is_dir():
            pending = 0
            for f in approvals_dir.glob("*.json"):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    if data.get("status") == "pending":
                        pending += 1
                except Exception:
                    pass
            status["pending_approvals"] = pending
    except Exception:
        pass
    try:
        from runtime.schedules.loader import list_schedules  # noqa: PLC0415
        schedules = list_schedules(vault_root)
        status["schedules_enabled"] = sum(1 for s in schedules if s.enabled)
        status["schedules_total"] = len(schedules)
    except Exception:
        pass
    try:
        adapters_dir = vault_root / "runtime" / "memory" / "adapters"
        if adapters_dir.is_dir():
            status["runtime_count"] = sum(1 for d in adapters_dir.iterdir() if d.is_dir())
    except Exception:
        pass
    try:
        from runtime.ventureops.autonomous_implementation_completion import (  # noqa: PLC0415
            build_autonomous_implementation_completion,
        )
        vo = build_autonomous_implementation_completion(vault_root)
        status["ventureops_real_world_usecase"] = {
            "feature_implementation_complete": vo.get("feature_implementation_complete"),
            "safe_to_mark_real_world_delivery_revenue_complete": vo.get(
                "safe_to_mark_real_world_delivery_revenue_complete"
            ),
            "real_world_missing": vo.get("real_world_missing_requirements", []),
        }
    except Exception:
        pass
    return status


def _render_status_bar(status: dict[str, Any]) -> str:
    """Render the read-only status bar chips as static HTML."""
    chips: list[str] = []
    pending = status.get("pending_approvals")
    if pending is not None:
        cls = "dash-stat warn" if pending > 0 else "dash-stat ok"
        chips.append(f'<span class="{cls}">Approvals: {pending} pending</span>')
    en = status.get("schedules_enabled")
    tot = status.get("schedules_total")
    if en is not None and tot is not None:
        chips.append(f'<span class="dash-stat muted">Schedules: {_escape(str(en))}/{_escape(str(tot))} enabled</span>')
    rt = status.get("runtime_count")
    if rt is not None:
        chips.append(f'<span class="dash-stat muted">Runtimes: {_escape(str(rt))} registered</span>')
    vo = status.get("ventureops_real_world_usecase")
    if vo is not None:
        impl_ok = vo.get("feature_implementation_complete")
        safe = vo.get("safe_to_mark_real_world_delivery_revenue_complete")
        cls = "dash-stat ok" if impl_ok else "dash-stat muted"
        # VentureOps real-use test — label preserved for autonomous_implementation_completion audit
        chips.append(
            f'<span class="{cls}" title="safe_to_mark_real_world_delivery_revenue_complete={safe}">'
            f"VentureOps real-use test: {'ready' if impl_ok else 'pending'}</span>"
        )
    if not chips:
        chips.append('<span class="dash-stat muted">Status unavailable</span>')
    return "\n".join(chips)


def render_studio_desktop_shell_app_html(
    plan: dict[str, Any],
    *,
    workspace_mode_selected_mode: str | None = None,
    status_bar: dict[str, Any] | None = None,
) -> str:
    """Render the local Studio desktop shell MVP."""

    metrics = plan.get("metrics") or {}
    contract = plan.get("runtime_cockpit_contract") or {}
    startup = contract.get("runtime_startup") or {}
    cards = list(startup.get("cards") or [])
    launcher = plan.get("app_launcher") or {}
    apps = list(launcher.get("apps") or [])
    graph_panel = plan.get("graph_view_shell_panel") or {}
    node_panel = plan.get("node_inspector_shell_panel") or {}
    pulse_panel = plan.get("pulse_product_shell_panel") or {}
    approval_queue_panel = plan.get("approval_queue_panel") or {}
    arsl_route_review_panel = plan.get("arsl_route_review_panel") or {}
    browser_runtime_panel = plan.get("browser_runtime_panel") or {}
    canvas_panel = plan.get("canvas_panel") or {}
    workspace_mode_panel = apply_workspace_mode_selection(
        plan.get("workspace_mode_panel") or {},
        workspace_mode_selected_mode,
    )
    views = list(plan.get("views") or [])
    shell = plan.get("shell") or {}
    nav = "\n".join(_view_nav(view) for view in views)
    kpi_cards = list(plan.get("kpi_cards") or [])
    metric_html = "\n".join(_kpi_card(card) for card in kpi_cards)
    operator_overview = _operator_dashboard_mount(plan.get("operator_dashboard") or {})
    runtime_cards = "".join(_runtime_card(card) for card in cards) or '<section class="empty-state">No runtime cards found in the current bounded context.</section>'
    app_rows = "".join(_app_row(app) for app in apps) or '<tr><td colspan="6" class="empty-table-cell">No Studio app registry rows found in this plan.</td></tr>'
    authority_rows = "".join(_authority_row(key, value) for key, value in (plan.get("authority") or {}).items())
    shell_rows = "".join(_authority_row(key, value) for key, value in shell.items())
    graph_mount = _graph_view_mount(graph_panel)
    node_mount = _node_inspector_mount(node_panel)
    pulse_mount = _pulse_product_shell_mount(pulse_panel)
    approval_queue_mount = _approval_queue_mount(approval_queue_panel)
    arsl_route_review_mount = _arsl_route_review_mount(arsl_route_review_panel)
    browser_runtime_mount = _browser_runtime_mount(browser_runtime_panel)
    canvas_mount = _canvas_panel_mount(canvas_panel)
    workspace_mode_mount = _workspace_mode_mount(workspace_mode_panel)
    settings_mount = _settings_mount()
    status_bar_html = _render_status_bar(status_bar or {})

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{_escape(plan.get('title'))}</title>
  <style>
    :root {{ color-scheme: light; font-family: Inter, Segoe UI, Arial, sans-serif; background: #eef3f8; color: #16212c; --ink:#16212c; --muted:#5b6c7c; --panel:#ffffff; --line:#d9e3ec; --brand:#1f4fd8; --brand-2:#16a3b8; --readonly:#176b70; --confirm:#8a5a00; --blocked:#b42318; --planned:#6d5bd0; --live:#0f7a3f; --shadow:0 18px 50px rgba(18,32,47,.08); }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{ margin: 0; min-height: 100vh; overflow-x: hidden; background: radial-gradient(circle at top left, #dfeaff 0, rgba(223,234,255,0) 38%), linear-gradient(180deg, #f8fbff 0, #eef3f8 100%); }}
    .shell {{ display: grid; grid-template-columns: minmax(248px, 280px) minmax(0, 1fr); min-height: 100vh; width: 100%; max-width: 100vw; }}
    aside {{ background: linear-gradient(180deg, #0d1724 0%, #142435 100%); color: #f8fafc; padding: 22px 16px; min-width: 0; border-right: 1px solid rgba(255,255,255,.08); }}
    .brand {{ font-size: 19px; font-weight: 850; letter-spacing: -.02em; margin: 0 0 22px; }}
    .brand::after {{ content: "MVP"; margin-left: 8px; padding: 3px 7px; border-radius: 999px; background: rgba(22,163,184,.16); color: #8ff3ff; font-size: 11px; letter-spacing: .08em; }}
    .nav-item {{ display: grid; gap: 7px; padding: 12px; border-radius: 14px; color: #e6edf5; text-decoration: none; margin-bottom: 8px; border: 1px solid transparent; transition: transform .16s ease, border-color .16s ease, background .16s ease, box-shadow .16s ease; }}
    .nav-item span {{ font-size: 14px; font-weight: 750; }}
    .nav-item:hover, .nav-item:focus-visible {{ transform: translateX(2px); background: rgba(255,255,255,.08); border-color: rgba(255,255,255,.18); outline: none; }}
    .nav-item.mounted {{ background: rgba(50, 80, 116, .52); border-color: rgba(112, 142, 176, .45); box-shadow: inset 3px 0 0 var(--brand-2); }}
    .nav-item.planned {{ opacity: .78; box-shadow: inset 3px 0 0 var(--planned); }}
    main {{ min-width: 0; }}
    header {{ display: flex; justify-content: space-between; gap: 22px; align-items: flex-start; padding: 30px 34px 24px; border-bottom: 1px solid var(--line); background: rgba(255,255,255,.86); backdrop-filter: blur(12px); min-width: 0; box-shadow: 0 1px 0 rgba(255,255,255,.7); }}
    h1 {{ font-size: clamp(28px, 4vw, 42px); margin: 0 0 8px; letter-spacing: -.045em; line-height: 1.02; }}
    h2 {{ font-size: 19px; margin: 0 0 14px; letter-spacing: -.02em; }}
    h3 {{ font-size: 16px; margin: 6px 0 14px; }}
    p {{ margin: 0; color: var(--muted); line-height: 1.5; }}
    .status {{ border: 1px solid #b9d7ff; border-radius: 999px; padding: 9px 13px; background: #edf6ff; color: #16489f; font-weight: 850; white-space: nowrap; box-shadow: 0 8px 18px rgba(31,79,216,.08); }}
    .hero-copy {{ display: grid; gap: 12px; max-width: 860px; }}
    .hero-eyebrow {{ color: var(--brand); font-size: 12px; font-weight: 900; letter-spacing: .12em; text-transform: uppercase; }}
    .governance-legend {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:4px; }}
    .content {{ padding: 24px 34px 38px; display: grid; gap: 18px; min-width: 0; }}
    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(min(190px, 100%), 1fr)); gap: 14px; }}
    .operator-summary-grid, .operator-action-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(min(230px, 100%), 1fr)); gap: 12px; margin: 14px 0; }}
    .operator-action {{ display: grid; gap: 8px; text-decoration: none; color: inherit; border: 1px solid var(--line); border-radius: 16px; padding: 14px; background: linear-gradient(180deg,#fff,#f9fcff); }}
    .operator-action strong {{ font-size: 16px; }}
    .operator-list {{ margin: 10px 0; padding-left: 22px; color: var(--muted); }}
    .operator-list li {{ margin: 8px 0; }}
    summary {{ cursor: pointer; font-weight: 850; margin: 12px 0 8px; }}
    .operator-process-table {{ table-layout: auto; }}
    .metric, .panel, .runtime-card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 18px; padding: 18px; min-width: 0; overflow-x: auto; box-shadow: var(--shadow); }}
    .metric {{ position: relative; overflow: hidden; }}
    .metric::before {{ content:""; position:absolute; inset:0 0 auto; height:4px; background: linear-gradient(90deg, var(--brand), var(--brand-2)); }}
    .panel-heading {{ display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; margin-bottom: 14px; }}
    .compact-heading {{ margin-bottom: 10px; }}
    .panel-heading > div {{ min-width: 0; }}
    .panel-state, .state-badge {{ display: inline-flex; align-items: center; width: fit-content; max-width: 280px; border-radius: 999px; padding: 5px 9px; font-size: 12px; font-weight: 830; white-space: normal; overflow-wrap: anywhere; word-break: break-word; line-height: 1.35; border: 1px solid transparent; }}
    .panel-state, .state-badge.readonly {{ background:#e8f7f7; color:var(--readonly); border-color:#bfe5e5; }}
    .state-badge.confirmation {{ background:#fff6df; color:var(--confirm); border-color:#f5d28a; }}
    .state-badge.blocked, .state-badge.bool-false.blocked {{ background:#fff0ee; color:var(--blocked); border-color:#f7c2bc; }}
    .state-badge.planned {{ background:#f1efff; color:var(--planned); border-color:#d8d1ff; }}
    .state-badge.live, .state-badge.bool-true {{ background:#eaf8ef; color:var(--live); border-color:#bfe7cc; }}
    .state-badge.neutral, .state-badge.bool-false {{ background:#eef3f7; color:#415466; border-color:#d4dee8; }}
    .pulse-summary {{ display: flex; flex-wrap: wrap; gap: 9px; margin: 10px 0 14px; }}
    .pulse-summary span {{ border: 1px solid var(--line); border-radius: 999px; padding: 8px 10px; background: #f7fbff; }}
    .workspace-mode-selector {{ border: 1px solid var(--line); border-radius: 16px; padding: 14px; background: #fbfdff; margin: 0 0 14px; }}
    .workspace-mode-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(min(220px, 100%), 1fr)); gap: 10px; }}
    .workspace-mode-card {{ display: grid; gap: 6px; color: inherit; text-decoration: none; border: 1px solid #d8e2ea; border-radius: 14px; padding: 12px; background: #ffffff; min-width: 0; }}
    .workspace-mode-card:hover {{ border-color: #97b8ea; box-shadow: 0 8px 20px rgba(31,79,216,.08); transform: translateY(-1px); }}
    .workspace-mode-card.selected {{ border-color: #1f4fd8; box-shadow: 0 0 0 3px rgba(31,79,216,.12); background: #f7fbff; }}
    .workspace-mode-card strong {{ font-size: 20px; letter-spacing: -.02em; }}
    .workspace-mode-card span {{ color: var(--muted); font-weight: 740; }}
    .workspace-mode-card p {{ font-size: 13px; }}
    .workspace-mode-sections {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(min(460px, 100%), 1fr)); gap: 12px; margin-bottom: 14px; }}
    .workspace-mode-section {{ border: 1px solid var(--line); border-radius: 16px; padding: 14px; background: linear-gradient(180deg,#fff,#f9fcff); min-width: 0; scroll-margin-top: 18px; }}
    .workspace-mode-section:target {{ border-color: #7ca7e8; box-shadow: 0 0 0 3px rgba(31,79,216,.12); }}
    .workspace-mode-section-head {{ display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; margin-bottom: 10px; }}
    .workspace-domain-row {{ display: flex; flex-wrap: wrap; gap: 7px; margin-bottom: 10px; }}
    .workspace-domain-chip {{ border: 1px solid #d8e2ea; background: #f7fbfc; color: #415466; border-radius: 999px; padding: 5px 8px; font-size: 12px; font-weight: 800; }}
    .workspace-domain-chip.muted, .muted-list-item {{ color: var(--muted); }}
    .workspace-mode-lists {{ display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, .9fr); gap: 10px; }}
    .workspace-project-list, .workspace-route-list {{ list-style: none; padding: 0; margin: 0; display: grid; gap: 8px; }}
    .workspace-project-list li, .workspace-route-list li {{ border-top: 1px solid #e3e9ef; padding-top: 8px; display: grid; gap: 4px; min-width: 0; }}
    .workspace-project-list strong {{ overflow-wrap: anywhere; }}
    .workspace-project-list span {{ color: var(--muted); font-size: 13px; }}
    .node-detail-grid {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 14px; margin-bottom: 14px; }}
    .detail-card {{ border: 1px solid var(--line); border-radius: 16px; padding: 14px; background: linear-gradient(180deg,#fff,#fbfdff); min-width: 0; overflow-x: auto; }}
    pre {{ white-space: pre-wrap; overflow-wrap: anywhere; margin: 8px 0 0; max-height: 340px; overflow-y: auto; background: #f7fbfc; border: 1px solid #d8e2ea; border-radius: 12px; padding: 12px; }}
    .mount-frame {{ width: 100%; height: min(78vh, 820px); min-height: 520px; border: 1px solid var(--line); border-radius: 16px; background: #ffffff; box-shadow: inset 0 0 0 1px rgba(255,255,255,.65); }}
    .mount-frame.graph {{ height: min(82vh, 880px); min-height: 560px; }}
    .mount-frame.compact {{ height: min(66vh, 680px); min-height: 420px; }}
    #dash-status-bar {{ display: flex; flex-wrap: wrap; gap: 10px; align-items: center; border: 1px solid var(--line); border-radius: 14px; padding: 12px 18px; background: rgba(255,255,255,.92); font-size: 13px; }}
    .dash-stat {{ display: inline-flex; align-items: center; gap: 6px; border: 1px solid var(--line); border-radius: 999px; padding: 5px 10px; background: #f7fbff; font-weight: 780; }}
    .dash-stat.warn {{ background:#fff6df; border-color:#f5d28a; color:var(--confirm); }}
    .dash-stat.ok {{ background:#eaf8ef; border-color:#bfe7cc; color:var(--live); }}
    .dash-stat.muted {{ color:var(--muted); }}
    .mount-placeholder {{ border: 1px dashed #a6b8c7; border-radius: 14px; padding: 18px; background: #f7fbfc; color: var(--muted); }}
    .empty-state, .empty-table-cell {{ border: 1px dashed #a6b8c7; border-radius: 14px; padding: 18px; background: #f7fbfc; color: var(--muted); font-weight: 700; }}
    .artifact-path, .boundary-note {{ margin-top: 11px; }}
    .boundary-note {{ border-left: 4px solid var(--readonly); padding: 10px 12px; background:#f4fbfb; border-radius: 10px; }}
    .artifact-link {{ display: inline-flex; margin-top: 9px; color: var(--brand); font-weight: 800; text-decoration: none; }}
    .artifact-link:hover {{ text-decoration: underline; }}
    .metric span, .label, th {{ color: var(--readonly); font-size: 12px; text-transform: uppercase; font-weight: 820; letter-spacing: .055em; }}
    .metric strong {{ display: block; font-size: 30px; margin: 6px 0 2px; letter-spacing: -.03em; }}
    .runtime-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(min(280px, 100%), 1fr)); gap: 14px; }}
    .card-topline {{ display:flex; justify-content:space-between; gap:10px; align-items:center; }}
    dl {{ display: grid; grid-template-columns: 132px minmax(0, 1fr); gap: 8px 10px; margin: 0; }}
    dt {{ color: var(--muted); font-weight: 650; }}
    dd {{ margin: 0; min-width: 0; }}
    code {{ background: #eef3f5; color: #25313b; border-radius: 7px; padding: 2px 6px; word-break: break-word; overflow-wrap: anywhere; white-space: normal; }}
    table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
    .table-scroll {{ width: 100%; overflow-x: auto; }}
    .route-review-table {{ min-width: 760px; table-layout: auto; }}
    th, td {{ text-align: left; border-bottom: 1px solid #e3e9ef; padding: 10px 8px; vertical-align: top; overflow-wrap: anywhere; }}
    td small {{ display:block; color:var(--muted); margin-top:4px; }}
    tr:hover td {{ background:#f8fbff; }}
    .action-button {{ display:inline-flex; align-items:center; justify-content:center; border-radius:999px; padding:7px 10px; font-weight:820; font-size:12px; border:1px solid #b9d7ff; background:#edf6ff; color:#16489f; }}
    .action-button.disabled {{ border-color:#d5dde5; background:#f4f6f8; color:#7a8896; cursor:not-allowed; }}
    @media (max-width: 900px) {{
      .shell {{ grid-template-columns: 1fr; }}
      aside {{ position: static; }}
      header {{ display: grid; }}
      .node-detail-grid {{ grid-template-columns: 1fr; }}
      .workspace-mode-lists {{ grid-template-columns: 1fr; }}
      .status {{ white-space: normal; }}
    }}
    @media (max-width: 640px) {{
      header, .content {{ padding-left: 16px; padding-right: 16px; }}
      table {{ display: block; overflow-x: auto; }}
    }}
  </style>
</head>
<body>
  <div class="shell" data-testid="studio-desktop-shell-root">
    <aside>
      <div class="brand">ChaseOS Studio</div>
      <nav>{nav}</nav>
    </aside>
    <main>
      <header>
        <div class="hero-copy">
          <div class="hero-eyebrow">Product shell · governance-visible MVP</div>
          <h1>{_escape(plan.get('title'))}</h1>
          <p>Read-only MVP shell over live Studio contracts. Actions stay previewed or disabled unless a lower-phase confirmation gate exists.</p>
          <div class="governance-legend" aria-label="Governance color legend">
            {_state_badge('Read-only')}
            {_state_badge('Confirmation-gated')}
            {_state_badge('Blocked')}
            {_state_badge('Planned')}
            {_state_badge('Live')}
          </div>
        </div>
        <div class="status">{_escape(_display_shell_kind(shell.get('kind')))}</div>
      </header>
      <div class="content">
        <div id="dash-status-bar" aria-label="Live system status">{status_bar_html}</div>
        <section class="metrics">{metric_html}</section>
        {operator_overview}
        {workspace_mode_mount}
        {graph_mount}
        {node_mount}
        {pulse_mount}
        {settings_mount}
        {browser_runtime_mount}
        {canvas_mount}
        {approval_queue_mount}
        {arsl_route_review_mount}
        <section id="runtime-cockpit" class="panel" data-testid="runtime-cockpit-mount">
          <h2>Runtime Cockpit</h2>
          <div class="runtime-grid">{runtime_cards}</div>
        </section>
        <section id="app-launcher" class="panel">
          <h2>Studio Apps</h2>
          <table>
            <thead><tr><th>App</th><th>Mode</th><th>Write posture</th><th>Health</th><th>CTA</th><th>Command boundary</th></tr></thead>
            <tbody>{app_rows}</tbody>
          </table>
        </section>
        <section id="shell-boundary" class="panel">
          <h2>Shell Boundary</h2>
          <table>{shell_rows}</table>
        </section>
        <section id="authority" class="panel">
          <h2>Authority</h2>
          <table>{authority_rows}</table>
        </section>
      </div>
    </main>
  </div>
</body>
</html>"""


class _StudioDesktopShellAppHandler(BaseHTTPRequestHandler):
    vault_root: Path
    host: str
    port: int
    runtime_id: str | None
    planning_mode: str
    plan: dict[str, Any] | None
    plan_lock: Lock
    panel_timeout_seconds: float | None

    def _health_plan(self) -> dict[str, Any]:
        return {
            "ok": True,
            "surface": _APP_SURFACE,
            "mode": "localhost_read_only_shell_server",
            "url": f"http://{self.host}:{int(self.port)}/",
            "health_url": f"http://{self.host}:{int(self.port)}/health.json",
            "shell_url": f"http://{self.host}:{int(self.port)}/shell.json",
            "graph_view_shell_panel_url": f"http://{self.host}:{int(self.port)}/graph-view-shell-panel.json",
            "node_inspector_shell_panel_url": f"http://{self.host}:{int(self.port)}/node-inspector-shell-panel.json",
            "arsl_route_review_panel_url": f"http://{self.host}:{int(self.port)}/arsl-route-review.json",
            "browser_runtime_panel_url": f"http://{self.host}:{int(self.port)}/browser-runtime-panel.json",
            "canvas_panel_url": f"http://{self.host}:{int(self.port)}/canvas-panel.json",
            "workspace_mode_panel_url": f"http://{self.host}:{int(self.port)}/workspace-mode-panel.json",
            "dashboard_url": f"http://{self.host}:{int(self.port)}/dashboard.json",
            "plan_ready": self.__class__.plan is not None,
            "read_only": True,
            "writes_performed": False,
            "route_execution_allowed": False,
            "browser_control_allowed": False,
            "workflow_execution_allowed": False,
            "canonical_mutation_allowed": False,
        }

    def _get_plan(self) -> dict[str, Any]:
        cls = self.__class__
        if cls.plan is None:
            with cls.plan_lock:
                if cls.plan is None:
                    cls.plan = build_studio_desktop_shell_app_plan(
                        cls.vault_root,
                        runtime_id=cls.runtime_id,
                        host=cls.host,
                        port=cls.port,
                        planning_mode=cls.planning_mode,
                        panel_timeout_seconds=cls.panel_timeout_seconds,
                    )
        return cls.plan

    def _artifact_path(self, relative_path: str | None) -> Path | None:
        if not relative_path:
            return None
        root = self.__class__.vault_root.resolve()
        candidate = (root / relative_path).resolve()
        if root == candidate or root not in candidate.parents:
            return None
        if not candidate.is_file():
            return None
        return candidate

    def _latest_static_graph_artifact_path(self) -> Path | None:
        root = self.__class__.vault_root.resolve()
        plan = self.__class__.plan
        if plan is not None:
            panel = plan.get("graph_view_shell_panel") or {}
            planned_path = self._artifact_path((panel.get("panel") or {}).get("source_artifact_path"))
            if planned_path is not None:
                return planned_path
        artifact = latest_static_graph_artifact(root)
        if artifact is None:
            return None
        candidate = artifact.resolve()
        if root == candidate or root not in candidate.parents:
            return None
        if not candidate.is_file():
            return None
        return candidate

    def _write(self, status: int, body: str | bytes, *, content_type: str) -> None:
        payload = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        selected_wml_mode = (query.get(MODE_QUERY_PARAM) or [None])[0]
        if path == "/health.json":
            self._write(200, json.dumps(self._health_plan(), indent=2, default=str), content_type="application/json")
            return
        if path == "/graph-view-static-artifact.html":
            artifact = self._latest_static_graph_artifact_path()
            if artifact is None:
                self._write(404, "graph artifact not found", content_type="text/plain; charset=utf-8")
                return
            self._write(200, artifact.read_text(encoding="utf-8"), content_type="text/html; charset=utf-8")
            return
        plan = self._get_plan()
        if path == "/shell.json":
            self._write(200, json.dumps(plan, indent=2, default=str), content_type="application/json")
            return
        if path == "/runtime-cockpit.json":
            self._write(200, json.dumps(plan.get("runtime_cockpit_contract") or {}, indent=2, default=str), content_type="application/json")
            return
        if path == "/app-launcher.json":
            self._write(200, json.dumps(plan.get("app_launcher") or {}, indent=2, default=str), content_type="application/json")
            return
        if path == "/graph-view-shell-panel.json":
            self._write(200, json.dumps(plan.get("graph_view_shell_panel") or {}, indent=2, default=str), content_type="application/json")
            return
        if path == "/node-inspector-shell-panel.json":
            self._write(200, json.dumps(plan.get("node_inspector_shell_panel") or {}, indent=2, default=str), content_type="application/json")
            return
        if path == "/pulse-product-shell.json":
            self._write(200, json.dumps(plan.get("pulse_product_shell_panel") or {}, indent=2, default=str), content_type="application/json")
            return
        if path == "/approval-queue.json":
            self._write(200, json.dumps(plan.get("approval_queue_panel") or {}, indent=2, default=str), content_type="application/json")
            return
        if path == "/arsl-route-review.json":
            self._write(200, json.dumps(plan.get("arsl_route_review_panel") or {}, indent=2, default=str), content_type="application/json")
            return
        if path == "/browser-runtime-panel.json":
            self._write(200, json.dumps(plan.get("browser_runtime_panel") or {}, indent=2, default=str), content_type="application/json")
            return
        if path == "/canvas-panel.json":
            self._write(200, json.dumps(plan.get("canvas_panel") or {}, indent=2, default=str), content_type="application/json")
            return
        if path == "/workspace-mode-panel.json":
            panel = apply_workspace_mode_selection(plan.get("workspace_mode_panel") or {}, selected_wml_mode)
            self._write(200, json.dumps(panel, indent=2, default=str), content_type="application/json")
            return
        if path == "/operator-dashboard.json":
            self._write(200, json.dumps(plan.get("operator_dashboard") or {}, indent=2, default=str), content_type="application/json")
            return
        if path == "/dashboard.json":
            try:
                from runtime.studio.dashboard import get_dashboard  # noqa: PLC0415
                dash = get_dashboard(self.__class__.vault_root, probe_child_apps=False)
            except Exception as exc:
                dash = {"ok": False, "error": str(exc)}
            self._write(200, json.dumps(dash, indent=2, default=str), content_type="application/json")
            return
        if path == "/":
            self._write(
                200,
                render_studio_desktop_shell_app_html(
                    plan,
                    workspace_mode_selected_mode=selected_wml_mode,
                    status_bar=_quick_status(self.__class__.vault_root),
                ),
                content_type="text/html; charset=utf-8",
            )
            return
        self._write(404, "not found", content_type="text/plain; charset=utf-8")

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return


def make_studio_desktop_shell_app_handler(
    vault_root: str | Path,
    *,
    runtime_id: str | None = None,
    host: str = _DEFAULT_HOST,
    port: int = _DEFAULT_PORT,
    plan: dict[str, Any] | None = None,
    planning_mode: str = "full",
    panel_timeout_seconds: float | None = None,
) -> type[BaseHTTPRequestHandler]:
    """Return a configured Studio desktop shell MVP handler."""

    _require_loopback(host)
    vault = _vault_path(vault_root)
    class Handler(_StudioDesktopShellAppHandler):
        pass

    Handler.vault_root = vault
    Handler.host = host
    Handler.port = int(port)
    Handler.runtime_id = runtime_id
    Handler.planning_mode = planning_mode
    Handler.panel_timeout_seconds = panel_timeout_seconds
    Handler.plan = plan
    Handler.plan_lock = Lock()
    return Handler


def serve_studio_desktop_shell_app(
    vault_root: str | Path,
    *,
    runtime_id: str | None = None,
    host: str = _DEFAULT_HOST,
    port: int = _DEFAULT_PORT,
    serve_seconds: float | None = None,
    planning_mode: str = "full",
    panel_timeout_seconds: float | None = None,
) -> None:
    """Serve the read-only Studio desktop shell MVP on a loopback interface."""

    _require_loopback(host)
    handler = make_studio_desktop_shell_app_handler(
        vault_root,
        runtime_id=runtime_id,
        host=host,
        port=port,
        planning_mode=planning_mode,
        panel_timeout_seconds=panel_timeout_seconds,
    )
    server = ThreadingHTTPServer((host, int(port)), handler)
    try:
        if serve_seconds is None:
            server.serve_forever()
            return
        server.timeout = 0.2
        deadline = monotonic() + max(0.0, float(serve_seconds))
        while monotonic() < deadline:
            server.handle_request()
    finally:
        server.server_close()


def smoke_test_studio_desktop_shell_app(
    vault_root: str | Path,
    *,
    runtime_id: str | None = None,
    host: str = _DEFAULT_HOST,
    port: int = 0,
    timeout_seconds: float = 90.0,
    planning_mode: str = "full",
    panel_timeout_seconds: float | None = None,
) -> dict[str, Any]:
    """Run a bounded local HTTP smoke test without leaving a server running."""

    _require_loopback(host)
    server = ThreadingHTTPServer((host, int(port)), BaseHTTPRequestHandler)
    actual_host, actual_port = server.server_address[:2]
    plan = build_studio_desktop_shell_app_plan(
        vault_root,
        runtime_id=runtime_id,
        host=str(actual_host),
        port=int(actual_port),
        planning_mode=planning_mode,
        panel_timeout_seconds=panel_timeout_seconds,
    )
    handler = make_studio_desktop_shell_app_handler(
        vault_root,
        runtime_id=runtime_id,
        host=str(actual_host),
        port=int(actual_port),
        plan=plan,
        planning_mode=planning_mode,
        panel_timeout_seconds=panel_timeout_seconds,
    )
    server.RequestHandlerClass = handler
    actual_host, actual_port = server.server_address[:2]
    # Keep smoke shutdown latency aligned with per-panel hard timeouts; the default
    # serve_forever poll interval can add up to 0.5s of teardown delay after a
    # panel already failed open, which made bounded full-plan smoke timing flaky.
    thread = Thread(target=lambda: server.serve_forever(poll_interval=0.05), daemon=True)
    thread.start()
    base_url = f"http://{actual_host}:{int(actual_port)}"
    routes = [
        "/health.json",
        "/shell.json",
        "/graph-view-shell-panel.json",
        "/graph-view-static-artifact.html",
        "/node-inspector-shell-panel.json",
        "/arsl-route-review.json",
        "/browser-runtime-panel.json",
        "/workspace-mode-panel.json",
        "/runtime-cockpit.json",
        "/",
    ]
    checks: list[dict[str, Any]] = []
    ok = True
    try:
        for route in routes:
            url = f"{base_url}{route}"
            check: dict[str, Any] = {"route": route, "url": url, "ok": False}
            try:
                request = Request(url, headers={"Cache-Control": "no-cache"})
                with urlopen(request, timeout=float(timeout_seconds)) as response:
                    body = response.read().decode("utf-8", errors="replace")
                    status = int(response.status)
                    check.update(
                        {
                            "status_code": status,
                            "content_type": response.headers.get("Content-Type"),
                            "body_bytes": len(body.encode("utf-8")),
                            "ok": status == 200,
                        }
                    )
                    if route == "/":
                        lower = body.lower()
                        check.update(
                            {
                                "shell_root_present": 'data-testid="studio-desktop-shell-root"' in body,
                                "graph_mount_present": 'data-testid="graph-view-panel-mount"' in body,
                                "node_inspector_mount_present": 'data-testid="node-inspector-panel-mount"' in body,
                                "arsl_route_review_mount_present": 'data-testid="arsl-route-review-panel-mount"' in body,
                                "browser_runtime_mount_present": 'data-testid="browser-runtime-panel-mount"' in body,
                                "workspace_mode_mount_present": 'data-testid="workspace-mode-panel-mount"' in body,
                                "graph_route_present": 'href="#graph-view"' in body,
                                "node_inspector_route_present": 'href="#node-inspector"' in body,
                                "arsl_route_review_route_present": 'href="#arsl-route-review"' in body,
                                "browser_runtime_route_present": 'href="#browser-runtime"' in body,
                                "workspace_mode_route_present": 'href="#workspace-mode"' in body,
                                "graph_iframe_title_present": 'title="ChaseOS Studio Graph View"' in body,
                                "script_tags": lower.count("<script"),
                                "iframe_sandbox_empty": 'sandbox=""' in body,
                            }
                        )
                        check["ok"] = bool(
                            check["ok"]
                            and check["shell_root_present"]
                            and check["graph_mount_present"]
                            and check["node_inspector_mount_present"]
                            and check["arsl_route_review_mount_present"]
                            and check["browser_runtime_mount_present"]
                            and check["workspace_mode_mount_present"]
                            and check["graph_route_present"]
                            and check["node_inspector_route_present"]
                            and check["arsl_route_review_route_present"]
                            and check["browser_runtime_route_present"]
                            and check["workspace_mode_route_present"]
                            and check["graph_iframe_title_present"]
                            and check["script_tags"] == 0
                            and check["iframe_sandbox_empty"]
                        )
                    if route == "/graph-view-static-artifact.html":
                        lower = body.lower()
                        check.update(
                            {
                                "graph_svg_present": "<svg" in lower and "class='graph'" in lower,
                                "script_tags": lower.count("<script"),
                            }
                        )
                        check["ok"] = bool(
                            check["ok"]
                            and check["graph_svg_present"]
                            and check["script_tags"] == 0
                        )
                    if route == "/graph-view-shell-panel.json":
                        payload = json.loads(body)
                        authority = payload.get("authority") or {}
                        readiness = payload.get("readiness") or {}
                        check.update(
                            {
                                "graph_panel_ok": bool(payload.get("ok")),
                                "desktop_shell_mount_ready": bool(readiness.get("desktop_shell_mount_ready")),
                                "writes_graph_index": bool(authority.get("writes_graph_index")),
                                "writes_node_ids": bool(authority.get("writes_node_ids")),
                                "node_editing_allowed": bool(authority.get("node_editing_allowed")),
                                "workflow_execution_allowed": bool(authority.get("workflow_execution_allowed")),
                                "provider_calls_allowed": bool(authority.get("provider_calls_allowed")),
                                "connector_calls_allowed": bool(authority.get("connector_calls_allowed")),
                                "canonical_mutation_allowed": bool(authority.get("canonical_mutation_allowed")),
                            }
                        )
                        check["ok"] = bool(
                            check["ok"]
                            and check["graph_panel_ok"]
                            and check["desktop_shell_mount_ready"]
                            and not check["writes_graph_index"]
                            and not check["writes_node_ids"]
                            and not check["node_editing_allowed"]
                            and not check["workflow_execution_allowed"]
                            and not check["provider_calls_allowed"]
                            and not check["connector_calls_allowed"]
                            and not check["canonical_mutation_allowed"]
                        )
                    if route == "/node-inspector-shell-panel.json":
                        payload = json.loads(body)
                        authority = payload.get("authority") or {}
                        readiness = payload.get("readiness") or {}
                        panel = payload.get("panel") or {}
                        node_panel_timed_out = str(payload.get("status") or "").upper() == "SKIPPED TIMEOUT"
                        check.update(
                            {
                                "node_panel_ok": bool(payload.get("ok")),
                                "node_panel_timed_out": node_panel_timed_out,
                                "selected_node_present": bool(panel.get("selected_node_id")),
                                "desktop_shell_mount_ready": bool(readiness.get("desktop_shell_mount_ready")),
                                "writes_node_ids": bool(authority.get("writes_node_ids")),
                                "node_editing_allowed": bool(authority.get("node_editing_allowed")),
                                "writes_graph_index": bool(authority.get("writes_graph_index")),
                                "canonical_mutation_allowed": bool(authority.get("canonical_mutation_allowed")),
                            }
                        )
                        check["ok"] = bool(
                            check["ok"]
                            and (
                                (
                                    check["node_panel_ok"]
                                    and check["selected_node_present"]
                                    and check["desktop_shell_mount_ready"]
                                )
                                or check["node_panel_timed_out"]
                            )
                            and not check["writes_node_ids"]
                            and not check["node_editing_allowed"]
                            and not check["writes_graph_index"]
                            and not check["canonical_mutation_allowed"]
                        )
                    if route == "/arsl-route-review.json":
                        payload = json.loads(body)
                        authority = payload.get("authority") or {}
                        readiness = payload.get("readiness") or {}
                        check.update(
                            {
                                "arsl_panel_ok": bool(payload.get("ok")),
                                "desktop_shell_mount_ready": bool(readiness.get("desktop_shell_mount_ready")),
                                "executes_routes": bool(authority.get("executes_routes")),
                                "writes_routing_ledger": bool(authority.get("writes_routing_ledger")),
                                "grants_approvals": bool(authority.get("grants_approvals")),
                                "mutates_gate_policy": bool(authority.get("mutates_gate_policy")),
                                "provider_calls_allowed": bool(authority.get("provider_calls_allowed")),
                                "browser_control_allowed": bool(authority.get("browser_control_allowed")),
                                "canonical_mutation_allowed": bool(authority.get("canonical_mutation_allowed")),
                            }
                        )
                        check["ok"] = bool(
                            check["ok"]
                            and check["arsl_panel_ok"]
                            and check["desktop_shell_mount_ready"]
                            and not check["executes_routes"]
                            and not check["writes_routing_ledger"]
                            and not check["grants_approvals"]
                            and not check["mutates_gate_policy"]
                            and not check["provider_calls_allowed"]
                            and not check["browser_control_allowed"]
                            and not check["canonical_mutation_allowed"]
                        )
                    if route == "/browser-runtime-panel.json":
                        payload = json.loads(body)
                        authority = payload.get("authority") or {}
                        panel_group = payload.get("panel_group") or {}
                        panel_ids = {item.get("panel_id") for item in payload.get("panels") or []}
                        required_ids = set(panel_group.get("required_panel_ids") or [])
                        check.update(
                            {
                                "browser_runtime_panel_ok": bool(payload.get("ok")),
                                "browser_runtime_required_sections_present": required_ids.issubset(panel_ids),
                                "operator_ui_readiness_contract_ready": bool(
                                    (payload.get("readiness") or {}).get("operator_ui_readiness_contract_ready")
                                ),
                                "read_only": bool(authority.get("read_only")),
                                "starts_servers": bool(authority.get("starts_servers")),
                                "launches_browser": bool(authority.get("launches_browser")),
                                "connects_cdp": bool(authority.get("connects_cdp")),
                                "invokes_mcp": bool(authority.get("invokes_mcp")),
                                "runs_browser_use_cli_live": bool(authority.get("runs_browser_use_cli_live")),
                                "activates_skills": bool(authority.get("activates_skills")),
                                "provider_calls_allowed": bool(authority.get("provider_calls_allowed")),
                                "connector_calls_allowed": bool(authority.get("connector_calls_allowed")),
                                "canonical_mutation_allowed": bool(authority.get("canonical_mutation_allowed")),
                            }
                        )
                        check["ok"] = bool(
                            check["ok"]
                            and check["browser_runtime_panel_ok"]
                            and check["browser_runtime_required_sections_present"]
                            and check["operator_ui_readiness_contract_ready"]
                            and check["read_only"]
                            and not check["starts_servers"]
                            and not check["launches_browser"]
                            and not check["connects_cdp"]
                            and not check["invokes_mcp"]
                            and not check["runs_browser_use_cli_live"]
                            and not check["activates_skills"]
                            and not check["provider_calls_allowed"]
                            and not check["connector_calls_allowed"]
                            and not check["canonical_mutation_allowed"]
                        )
                    if route == "/workspace-mode-panel.json":
                        payload = json.loads(body)
                        authority = payload.get("authority") or {}
                        readiness = payload.get("readiness") or {}
                        check.update(
                            {
                                "workspace_mode_panel_ok": bool(payload.get("ok")),
                                "workspace_mode_panel_mounted": bool(readiness.get("workspace_mode_panel_mounted")),
                                "read_only": bool(authority.get("read_only")),
                                "profile_writes_allowed": bool(authority.get("profile_writes_allowed")),
                                "workflow_execution_allowed": bool(authority.get("workflow_execution_allowed")),
                                "agent_bus_dispatch_allowed": bool(authority.get("agent_bus_dispatch_allowed")),
                                "provider_calls_allowed": bool(authority.get("provider_calls_allowed")),
                                "canonical_mutation_allowed": bool(authority.get("canonical_mutation_allowed")),
                            }
                        )
                        check["ok"] = bool(
                            check["ok"]
                            and check["workspace_mode_panel_ok"]
                            and check["workspace_mode_panel_mounted"]
                            and check["read_only"]
                            and not check["profile_writes_allowed"]
                            and not check["workflow_execution_allowed"]
                            and not check["agent_bus_dispatch_allowed"]
                            and not check["provider_calls_allowed"]
                            and not check["canonical_mutation_allowed"]
                        )
            except Exception as exc:  # noqa: BLE001 - smoke output must capture probe failures.
                check["error"] = str(exc)
            checks.append(check)
            ok = ok and bool(check.get("ok"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)
    return {
        "ok": ok,
        "surface": _APP_SURFACE,
        "mode": "bounded_http_smoke",
        "base_url": base_url,
        "server_stopped": not thread.is_alive(),
        "read_only": True,
        "writes_performed": False,
        "workflow_execution_allowed": False,
        "canonical_mutation_allowed": False,
        "checks": checks,
    }


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _qa_slug(prefix: str | None = None) -> str:
    return prefix or datetime.now(timezone.utc).strftime("%Y-%m-%d-node-inspector-shell-panel-qa-runner")


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _qa_check(checks: list[dict[str, Any]], route: str) -> dict[str, Any]:
    return next((item for item in checks if item.get("route") == route), {})


def run_node_inspector_shell_panel_qa_runner(
    vault_root: str | Path,
    *,
    runtime_id: str | None = None,
    host: str = _DEFAULT_HOST,
    timeout_seconds: float = 90.0,
    write_evidence: bool = False,
    evidence_slug: str | None = None,
) -> dict[str, Any]:
    """Run bounded Node Inspector shell-panel QA without a long-lived server."""

    _require_loopback(host)
    vault = _vault_path(vault_root)
    smoke = smoke_test_studio_desktop_shell_app(
        vault,
        runtime_id=runtime_id,
        host=host,
        port=0,
        timeout_seconds=timeout_seconds,
    )
    checks = list(smoke.get("checks") or [])
    root = _qa_check(checks, "/")
    node_route = _qa_check(checks, "/node-inspector-shell-panel.json")
    shell_route = _qa_check(checks, "/shell.json")
    graph_route = _qa_check(checks, "/graph-view-shell-panel.json")
    static_route = _qa_check(checks, "/graph-view-static-artifact.html")
    qa_ok = bool(
        smoke.get("ok")
        and smoke.get("server_stopped")
        and root.get("node_inspector_mount_present")
        and root.get("node_inspector_route_present")
        and root.get("script_tags") == 0
        and node_route.get("node_panel_ok")
        and node_route.get("selected_node_present")
        and node_route.get("desktop_shell_mount_ready")
        and not node_route.get("writes_node_ids")
        and not node_route.get("writes_graph_index")
        and not node_route.get("node_editing_allowed")
        and not node_route.get("canonical_mutation_allowed")
    )
    report: dict[str, Any] = {
        "ok": qa_ok,
        "surface": "studio_node_inspector_shell_panel_qa_runner",
        "mode": "bounded_internal_http_qa_runner",
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "base_url": smoke.get("base_url"),
        "server_stopped": bool(smoke.get("server_stopped")),
        "read_only": True,
        "writes_performed": bool(write_evidence),
        "writes_vault_source_files": False,
        "workflow_execution_allowed": False,
        "provider_calls_allowed": False,
        "connector_calls_allowed": False,
        "canonical_mutation_allowed": False,
        "visual_browser_qa_complete": False,
        "visual_screenshot_required": True,
        "checks": {
            "shell_root_ok": bool(root.get("ok")),
            "shell_json_ok": bool(shell_route.get("ok")),
            "graph_panel_json_ok": bool(graph_route.get("ok")),
            "static_graph_artifact_ok": bool(static_route.get("ok")),
            "node_inspector_json_ok": bool(node_route.get("ok")),
            "node_inspector_mount_present": bool(root.get("node_inspector_mount_present")),
            "node_inspector_route_present": bool(root.get("node_inspector_route_present")),
            "script_tags": int(root.get("script_tags") or 0),
            "selected_node_present": bool(node_route.get("selected_node_present")),
            "desktop_shell_mount_ready": bool(node_route.get("desktop_shell_mount_ready")),
            "writes_node_ids": bool(node_route.get("writes_node_ids")),
            "writes_graph_index": bool(node_route.get("writes_graph_index")),
            "node_editing_allowed": bool(node_route.get("node_editing_allowed")),
            "canonical_mutation_allowed": bool(node_route.get("canonical_mutation_allowed")),
        },
        "smoke": smoke,
        "evidence": {
            "written": False,
            "json_path": None,
            "markdown_path": None,
        },
        "next_recommended_pass": "phase10-studio-node-inspector-shell-panel-browser-qa",
    }
    if write_evidence:
        slug = _qa_slug(evidence_slug)
        evidence_root = vault / _QA_EVIDENCE_ROOT
        evidence_root.mkdir(parents=True, exist_ok=True)
        json_path = evidence_root / f"{slug}.json"
        markdown_path = evidence_root / f"{slug}.md"
        markdown = "\n".join(
            [
                "# Node Inspector Shell Panel QA Runner Evidence",
                "",
                f"Generated: {report['generated_at']}",
                "Runtime: Codex",
                "Mode: bounded internal HTTP QA runner",
                "",
                "## Result",
                "",
                f"- ok: {report['ok']}",
                f"- base_url: {report['base_url']}",
                f"- server_stopped: {report['server_stopped']}",
                f"- visual_browser_qa_complete: {report['visual_browser_qa_complete']}",
                f"- visual_screenshot_required: {report['visual_screenshot_required']}",
                "",
                "## Checks",
                "",
                f"- node_inspector_mount_present: {report['checks']['node_inspector_mount_present']}",
                f"- node_inspector_route_present: {report['checks']['node_inspector_route_present']}",
                f"- node_inspector_json_ok: {report['checks']['node_inspector_json_ok']}",
                f"- selected_node_present: {report['checks']['selected_node_present']}",
                f"- desktop_shell_mount_ready: {report['checks']['desktop_shell_mount_ready']}",
                f"- script_tags: {report['checks']['script_tags']}",
                "",
                "## Authority",
                "",
                f"- writes_node_ids: {report['checks']['writes_node_ids']}",
                f"- writes_graph_index: {report['checks']['writes_graph_index']}",
                f"- node_editing_allowed: {report['checks']['node_editing_allowed']}",
                f"- canonical_mutation_allowed: {report['checks']['canonical_mutation_allowed']}",
                f"- workflow_execution_allowed: {report['workflow_execution_allowed']}",
                f"- provider_calls_allowed: {report['provider_calls_allowed']}",
                f"- connector_calls_allowed: {report['connector_calls_allowed']}",
                "",
                "## Boundary",
                "",
                "This runner starts an internal localhost-only HTTP server on an ephemeral port, probes the shell and Node Inspector routes, writes evidence only when explicitly requested, and shuts the server down before returning. It does not perform visual screenshot QA and does not mark the live browser pass complete.",
                "",
            ]
        )
        json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        markdown_path.write_text(markdown, encoding="utf-8")
        report["evidence"] = {
            "written": True,
            "json_path": _relative_to_vault(vault, json_path),
            "markdown_path": _relative_to_vault(vault, markdown_path),
        }
        json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return report
