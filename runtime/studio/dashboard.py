"""
studio/dashboard.py — Studio Operator Dashboard

Aggregates system state across all ChaseOS subsystems into a single read-only
UI-ready model. Each panel is gathered independently; failures are collected into
the top-level `errors` list (fail-open — a broken panel does not abort the dashboard).

Panels:
  - schedule_panel:  runtime/schedules/ — schedule count + enabled/disabled
  - bus_panel:       agent bus — task counts by status
  - quarantine_panel: 03_INPUTS/00_QUARANTINE/ — file count by class
  - graph_panel:     latest snapshot — age + node/edge counts
  - memory_panel:    runtime/memory/adapters/ — registered runtimes + profile existence
  - audit_panel:     07_LOGS/Agent-Activity/ — recent audit file count + last timestamp
  - approval_panel:  runtime/studio/approvals/ — pending approval count
  - runtime_startup_panel: runtime startup/autostart visual cockpit readiness
  - pulse_panel:     07_LOGS/Pulse-Decks/ — read-only Pulse deck/candidate/enqueue summary
  - app_launcher_panel: Studio local app discovery registry summary
  - ventureops_real_world_usecase_panel: VentureOps implementation/revenue gate summary
  - personal_operator_context_panel: personal-instance context grouping + link checks
  - personal_context_import_panel: personal-context import planner + storage/security posture
  - discord_control_plane_panel: redacted Discord binding readiness for runtime control lanes

Governance:
  - Read-only: never writes vault or any subsystem state
  - All panels fail-open: missing subsystem = empty panel + error entry
  - Generated/canonical distinction preserved in all node-level data surfaced
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_BOUNDARY = {
    "reads_vault": True,
    "reads_snapshot": True,
    "reads_mvp_readiness": True,
    "reads_pulse_logs": True,
    "reads_studio_app_registry": True,
    "reads_runtime_provider_status": True,
    "writes_vault": False,
    "reads_workspace_mode_panel": True,
    "reads_ventureops_completion_gate": True,
    "reads_personal_operator_context": True,
    "reads_personal_context_import_panel": True,
    "reads_discord_control_plane_bindings": True,
    "writes_snapshot": False,
    "writes_pulse_logs": False,
    "starts_studio_child_apps": False,
    "canonical_mutation_allowed": False,
}

_APPROVAL_DIR = "runtime/studio/approvals"
_AUDIT_DIR = "07_LOGS/Agent-Activity"
_GRAPH_REPORTS_DIR = "07_LOGS/Graph-Reports"
_MAINTAIN_RUNS_DIR = "07_LOGS/Maintain-Runs"
_LOOSE_NODES_RE    = re.compile(r"review_gated_loose_nodes=(\d+)")
_DUPLICATES_RE     = re.compile(r"duplicate_candidates=(\d+)")
_MEMORY_ADAPTERS_DIR = "runtime/memory/adapters"
_QUARANTINE_DIR = "03_INPUTS/00_QUARANTINE"
_STUDIO_MVP_CLOSURE_DIR = "07_LOGS/Studio-Graph-Views/studio-mvp-closure-gates"
_STUDIO_MVP_DECISION_DIR = "07_LOGS/Studio-Graph-Views/studio-mvp-operator-decisions"
_STUDIO_MVP_ACCEPTANCE_DIR = "07_LOGS/Studio-Graph-Views/studio-mvp-manual-acceptance"


def _release_grade_lanes(vault: Path | str | None = None) -> list[dict[str, Any]]:
    lanes = [dict(item) for item in _RELEASE_GRADE_LANES]
    if vault is None:
        return lanes
    try:
        from runtime.studio.persisted_graph_storage_status import build_persisted_graph_storage_status

        storage_status = build_persisted_graph_storage_status(Path(vault))
        storage_summary = dict(storage_status.get("summary") or {})
        storage_ready = bool(storage_summary.get("cache_ready"))
        for lane in lanes:
            if lane.get("id") == "persisted_graph_storage_scope":
                lane.update(
                    {
                        "status": (
                            "PARTIAL / READ_ONLY_CURRENT_GRAPH_SNAPSHOT_AVAILABLE"
                            if storage_ready
                            else "IN_PROGRESS / READ_ONLY_STORAGE_STATUS_SURFACE_BUILT"
                        ),
                        "next_surface": "persisted-graph-storage-status",
                        "preview_command": "python -m runtime.cli.main studio persisted-graph-storage-status --json",
                        "action_label": "Inspect graph-store status",
                        "operator_input": (
                            "approval to write or refresh graph-store snapshots"
                            if storage_ready
                            else "approval boundary for first persisted snapshot write"
                        ),
                        "safe_preview_available": True,
                        "preview_only": True,
                        "storage_summary": storage_summary,
                        "authority": storage_status.get("authority") or {"read_only": True, "canonical_mutation_allowed": False},
                        "implementation_slice": "read-only persisted graph-store cache/status surface",
                    }
                )
                break
    except Exception as exc:
        for lane in lanes:
            if lane.get("id") == "persisted_graph_storage_scope":
                lane.update(
                    {
                        "status": "IN_PROGRESS / READ_ONLY_STORAGE_STATUS_SURFACE_UNAVAILABLE",
                        "safe_preview_available": True,
                        "preview_only": True,
                        "storage_status_error": str(exc),
                    }
                )
                break
    return lanes


_RELEASE_GRADE_LANES = [
    {
        "id": "branded_installer_logo_icon",
        "label": "Branded installer assets",
        "status": "DEFERRED / OPERATOR-GOVERNED",
        "next_surface": "installer-plan",
        "preview_command": "python -m runtime.cli.main studio installer-plan --json",
        "action_label": "Review installer plan",
        "operator_input": "brand asset or design decision",
        "human_loop": "OPERATOR BRAND DIRECTION",
        "requires_operator": True,
        "requires_credentials": False,
        "requires_host_mutation": False,
        "requires_manual_testing": True,
        "safe_preview_available": True,
        "preview_only": True,
    },
    {
        "id": "signing_chain",
        "label": "Code signing",
        "status": "DEFERRED / CREDENTIALS REQUIRED",
        "next_surface": "signing-approval-preview",
        "preview_command": "python -m runtime.cli.main studio signing-approval-preview --json",
        "action_label": "Preview signing approval",
        "operator_input": "certificate material and signing approval",
        "human_loop": "OPERATOR CERTIFICATE / CREDENTIALS",
        "requires_operator": True,
        "requires_credentials": True,
        "requires_host_mutation": False,
        "requires_manual_testing": True,
        "safe_preview_available": True,
        "preview_only": True,
    },
    {
        "id": "startup_autostart_host_mutation",
        "label": "Startup/autostart",
        "status": "DEFERRED / HOST MUTATION APPROVAL REQUIRED",
        "next_surface": "startup-autostart-approval-preview",
        "preview_command": "python -m runtime.cli.main studio startup-autostart-approval-preview --json",
        "action_label": "Preview startup approval",
        "operator_input": "host mutation approval and manual verification",
        "human_loop": "OPERATOR HOST MUTATION APPROVAL",
        "requires_operator": True,
        "requires_credentials": False,
        "requires_host_mutation": True,
        "requires_manual_testing": True,
        "safe_preview_available": True,
        "preview_only": True,
    },
    {
        "id": "release_promotion",
        "label": "Release promotion",
        "status": "DEFERRED / RELEASE DECISION REQUIRED",
        "next_surface": "release-promotion-approval-preview",
        "preview_command": "python -m runtime.cli.main studio release-promotion-approval-preview --json",
        "action_label": "Preview release approval",
        "operator_input": "release channel/version approval",
        "human_loop": "OPERATOR RELEASE DECISION",
        "requires_operator": True,
        "requires_credentials": False,
        "requires_host_mutation": False,
        "requires_manual_testing": True,
        "safe_preview_available": True,
        "preview_only": True,
    },
    {
        "id": "real_target_workspace_migration",
        "label": "Real workspace migration",
        "status": "DEFERRED / TARGET PATH REQUIRED",
        "next_surface": "approved-target-upgrade-executor",
        "preview_command": "python -m runtime.cli.main studio approved-target-upgrade-executor --json",
        "action_label": "Review target executor",
        "operator_input": "target path, backup confirmation, and execution approval",
        "human_loop": "OPERATOR TARGET PATH / BACKUP",
        "requires_operator": True,
        "requires_credentials": False,
        "requires_host_mutation": False,
        "requires_manual_testing": True,
        "safe_preview_available": True,
        "preview_only": True,
    },
    {
        "id": "provider_model_live_calls",
        "label": "Live provider/model calls",
        "status": "DEFERRED / PROVIDER APPROVAL REQUIRED",
        "next_surface": "phase11-chat-live-provider-execution-approval-preview",
        "preview_command": "python -m runtime.cli.main studio phase11-chat-live-provider-execution-approval-preview --json",
        "action_label": "Preview provider approval",
        "operator_input": "provider credentials, model, and budget approval",
        "human_loop": "OPERATOR PROVIDER CREDENTIALS / BUDGET",
        "requires_operator": True,
        "requires_credentials": True,
        "requires_host_mutation": False,
        "requires_manual_testing": True,
        "safe_preview_available": True,
        "preview_only": True,
    },
    {
        "id": "runtime_browser_dispatch",
        "label": "Runtime/browser dispatch",
        "status": "DEFERRED / RUNTIME AUTHORITY REQUIRED",
        "next_surface": "phase11-chat-runtime-dispatch-readiness-contract",
        "preview_command": "python -m runtime.cli.main studio phase11-chat-runtime-dispatch-readiness-contract --json",
        "action_label": "Preview dispatch readiness",
        "operator_input": "runtime target and browser/profile approval",
        "human_loop": "OPERATOR RUNTIME / BROWSER TARGET",
        "requires_operator": True,
        "requires_credentials": False,
        "requires_host_mutation": False,
        "requires_manual_testing": True,
        "safe_preview_available": True,
        "preview_only": True,
        "secondary_actions": [
            {
                "label": "Browser dispatch readiness",
                "surface": "phase11-chat-browser-dispatch-readiness-contract",
                "command": "python -m runtime.cli.main studio phase11-chat-browser-dispatch-readiness-contract --json",
                "requires_operator": True,
                "preview_only": True,
            }
        ],
    },
    {
        "id": "persisted_graph_storage_scope",
        "label": "Persisted graph storage",
        "status": "DEFERRED / ARCHITECTURE SCOPE REQUIRED",
        "next_surface": "Persisted-Graph-Engine-and-Durable-Node-ID-Layer",
        "preview_command": "06_AGENTS/Persisted-Graph-Engine-and-Durable-Node-ID-Layer.md",
        "action_label": "Review graph-store contract",
        "operator_input": "storage scope decision and graph-store approval boundary",
        "human_loop": "OPERATOR ARCHITECTURE SCOPE",
        "requires_operator": True,
        "requires_credentials": False,
        "requires_host_mutation": False,
        "requires_manual_testing": False,
        "safe_preview_available": False,
        "preview_only": True,
    },
]


# ── Panel gatherers (all fail-open) ──────────────────────────────────────────

try:
    from runtime.schedules.loader import list_schedules as _list_schedules
except ImportError:
    _list_schedules = None  # type: ignore[assignment]


def _gather_schedule_panel(vault: Path, errors: list[str]) -> dict[str, Any]:
    try:
        list_schedules = _list_schedules
        if list_schedules is None:
            errors.append("schedule_panel: schedules module not available")
            return {"total": 0, "enabled": 0, "disabled": 0, "schedules": []}
        schedules = list_schedules(vault, check_registry=False)
        enabled = [s for s in schedules if s.enabled]
        disabled = [s for s in schedules if not s.enabled]
        return {
            "total": len(schedules),
            "enabled": len(enabled),
            "disabled": len(disabled),
            "schedules": [
                {
                    "schedule_id": s.schedule_id,
                    "workflow_id": s.workflow_id,
                    "cadence": s.cadence,
                    "enabled": s.enabled,
                }
                for s in schedules
            ],
        }
    except Exception as exc:
        errors.append(f"schedule_panel: {exc}")
        return {"total": 0, "enabled": 0, "disabled": 0, "schedules": []}


def _gather_bus_panel(vault: Path, errors: list[str]) -> dict[str, Any]:
    try:
        from runtime.agent_bus.bus import list_tasks
        tasks = list_tasks(vault)
        by_status: dict[str, int] = {}
        for t in tasks:
            s = t.get("status", "unknown")
            by_status[s] = by_status.get(s, 0) + 1
        return {
            "total": len(tasks),
            "by_status": by_status,
            "open": sum(v for k, v in by_status.items() if k in ("open", "claimed", "in_progress")),
        }
    except Exception as exc:
        errors.append(f"bus_panel: {exc}")
        return {"total": 0, "by_status": {}, "open": 0}


def _gather_quarantine_panel(vault: Path, errors: list[str]) -> dict[str, Any]:
    try:
        q_root = vault / _QUARANTINE_DIR
        if not q_root.exists():
            return {"total": 0, "by_class": {}}
        by_class: dict[str, int] = {}
        total = 0
        for item in q_root.iterdir():
            if item.is_dir():
                count = sum(1 for f in item.iterdir() if f.is_file() and not f.name.startswith("."))
                by_class[item.name] = count
                total += count
            elif item.is_file() and not item.name.startswith(".") and not item.suffix == ".md":
                by_class["_root"] = by_class.get("_root", 0) + 1
                total += 1
        return {"total": total, "by_class": by_class}
    except Exception as exc:
        errors.append(f"quarantine_panel: {exc}")
        return {"total": 0, "by_class": {}}


def _gather_graph_panel(vault: Path, errors: list[str]) -> dict[str, Any]:
    try:
        from runtime.graph.builder import load_latest_snapshot
        maintenance = _gather_graph_maintenance_summary(vault)
        snapshot = load_latest_snapshot(vault)
        if snapshot is None:
            return {"snapshot_available": False, "maintenance": maintenance}
        now = datetime.now(timezone.utc)
        try:
            created = datetime.fromisoformat(snapshot.created_at.replace("Z", "+00:00"))
            age_hours = round((now - created).total_seconds() / 3600, 1)
        except Exception:
            age_hours = None
        return {
            "snapshot_available": True,
            "snapshot_id": snapshot.snapshot_id,
            "created_at": snapshot.created_at,
            "age_hours": age_hours,
            "node_count": len(snapshot.nodes),
            "edge_count": len(snapshot.edges),
            "community_count": len(set(snapshot.community_assignments.values())) if snapshot.community_assignments else 0,
            "maintenance": maintenance,
        }
    except Exception as exc:
        errors.append(f"graph_panel: {exc}")
        return {"snapshot_available": False, "maintenance": {"available": False}}


def _gather_graph_maintenance_summary(vault: Path) -> dict[str, Any]:
    """Return read-only graph hygiene/vault maintenance status for Studio."""
    maintain_root = vault / _MAINTAIN_RUNS_DIR
    report_root = vault / _GRAPH_REPORTS_DIR
    latest_run = next(iter(sorted(maintain_root.glob("*-os-hygiene-graph-run.md"), reverse=True)), None)
    latest_queue = next(iter(sorted(report_root.glob("*loose-node-review-queue.json"), reverse=True)), None)

    summary: dict[str, Any] = {
        "available": bool(latest_run or latest_queue),
        "surface": "studio_graph_hygiene_maintenance_summary",
        "read_only": True,
        "workflow_id": "os_hygiene_graph",
        "latest_run_path": str(latest_run.relative_to(vault)) if latest_run else None,
        "latest_review_queue_path": str(latest_queue.relative_to(vault)) if latest_queue else None,
    }

    review_gated_loose_nodes = 0
    duplicate_candidates = 0

    if latest_run:
        status = None
        duration_seconds = None
        for line in latest_run.read_text(encoding="utf-8", errors="replace").splitlines()[:40]:
            clean = line.strip().strip("\ufeff")
            if clean.startswith("status:"):
                status = clean.split(":", 1)[1].strip()
            elif clean.startswith("duration_seconds:"):
                duration_seconds = clean.split(":", 1)[1].strip()
            # Extract hygiene counts from stage table rows
            ln_m = _LOOSE_NODES_RE.search(clean)
            if ln_m:
                review_gated_loose_nodes = int(ln_m.group(1))
            dc_m = _DUPLICATES_RE.search(clean)
            if dc_m:
                duplicate_candidates = int(dc_m.group(1))
        summary["latest_run_status"] = status
        summary["latest_run_duration_seconds"] = duration_seconds
        summary["review_gated_loose_nodes"] = review_gated_loose_nodes
        summary["duplicate_candidates"] = duplicate_candidates

    if latest_queue:
        try:
            data = json.loads(latest_queue.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        summary.update({
            "queue_status": data.get("status"),
            "queue_timestamp": data.get("timestamp"),
            "files_scanned": data.get("files_scanned"),
            "total_issues": data.get("total_issues"),
            "loose_node_review_count": data.get("loose_node_review_count"),
            "review_queue_category_counts": data.get("review_queue_category_counts") or {},
        })

    # Derive operator_next_action when hygiene review is required
    run_status = summary.get("latest_run_status", "")
    attention = run_status == "blocked_review_required" or review_gated_loose_nodes > 0
    if attention:
        summary["operator_next_action"] = {
            "id": "graph_hygiene_review_required",
            "label": "Graph Hygiene Review Required",
            "status": "blocked_review_required",
            "route": "#/graph-hygiene",
            "message": (
                f"{review_gated_loose_nodes} loose node(s) and {duplicate_candidates} "
                "duplicate candidate(s) require review before scheduled mutation can proceed."
            ),
        }

    return summary


def _latest_json(root: Path) -> Path | None:
    if not root.is_dir():
        return None
    candidates = [path for path in root.glob("*.json") if path.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: (path.stat().st_mtime, path.name))


def _relative_path(vault: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return str(path)


def _read_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _gather_studio_product_home_panel(vault: Path, errors: list[str]) -> dict[str, Any]:
    """Return the Studio product home/status model shown on the native dashboard."""

    try:
        closure_path = _latest_json(vault / _STUDIO_MVP_CLOSURE_DIR)
        decision_path = _latest_json(vault / _STUDIO_MVP_DECISION_DIR)
        acceptance_path = _latest_json(vault / _STUDIO_MVP_ACCEPTANCE_DIR)
        closure = _read_json(closure_path) or {}
        decision = _read_json(decision_path) or {}
        acceptance = _read_json(acceptance_path) or {}

        closure_summary = closure.get("summary") or {}
        decision_summary = decision.get("summary") or {}
        acceptance_summary = acceptance.get("summary") or {}
        internal_closed = (
            closure_summary.get("mvp_closed") is True
            and closure_summary.get("manual_acceptance_complete") is True
            and closure_summary.get("pass10b_installer_zip_proof_complete") is True
            and len(closure.get("blockers") or []) == 0
        )

        release_grade_complete = False
        open_lanes = _release_grade_lanes(vault)
        current_status = (
            "COMPLETE / INTERNAL PORTABLE MVP CLOSED WITH DEFERRALS"
            if internal_closed
            else closure.get("status") or "PARTIAL / STUDIO NOT CLOSED"
        )
        product_status = (
            "INTERNAL_PORTABLE_CLOSED_RELEASE_GRADE_OPEN"
            if internal_closed
            else "STUDIO_CLOSEOUT_OPEN"
        )

        return {
            "ok": True,
            "surface": "studio_product_home_panel",
            "current_status": current_status,
            "product_status": product_status,
            "internal_portable_mvp_closed": internal_closed,
            "release_grade_complete": release_grade_complete,
            "headline": (
                "Internal portable MVP closed; release-grade Studio remains open"
                if internal_closed
                else "Studio is still open"
            ),
            "summary": {
                "mvp_closed": closure_summary.get("mvp_closed"),
                "manual_acceptance_complete": closure_summary.get("manual_acceptance_complete"),
                "pass10b_installer_zip_proof_complete": closure_summary.get("pass10b_installer_zip_proof_complete"),
                "blocker_count": closure_summary.get("blocker_count", len(closure.get("blockers") or [])),
                "deferred_for_internal_portable_mvp_count": decision_summary.get("deferred_for_internal_portable_mvp_count"),
                "release_grade_open_lane_count": len(open_lanes),
                "next_recommended_pass": "select-next-release-grade-studio-lane",
            },
            "evidence": {
                "closure_gate_path": _relative_path(vault, closure_path),
                "decision_packet_path": _relative_path(vault, decision_path),
                "manual_acceptance_path": _relative_path(vault, acceptance_path),
                "manual_acceptance_validated": (
                    (closure.get("manual_acceptance_evidence_validation") or {}).get("valid") is True
                    or acceptance_summary.get("manual_acceptance_complete") is True
                ),
            },
            "open_release_lanes": open_lanes,
            "action_center": {
                "surface": "studio_release_grade_action_center",
                "status": "ACTIONABLE_PREVIEWS_READY / EXECUTION_BLOCKED",
                "lane_count": len(open_lanes),
                "human_loop_lane_count": sum(1 for lane in open_lanes if lane.get("requires_operator")),
                "safe_preview_count": sum(1 for lane in open_lanes if lane.get("safe_preview_available")),
                "execution_enabled_count": 0,
                "default_next_pass": "studio-release-grade-action-center",
                "description": "Operator-facing release-grade lanes with preview/review actions only; execution remains blocked until explicit governed approval.",
            },
            "authority": {
                "read_only": True,
                "approval_execution_allowed": False,
                "signing_allowed": False,
                "host_mutation_allowed": False,
                "provider_calls_allowed": False,
                "runtime_dispatch_allowed": False,
                "browser_control_allowed": False,
                "target_mutation_allowed": False,
                "release_promotion_allowed": False,
                "canonical_mutation_allowed": False,
            },
        }
    except Exception as exc:
        errors.append(f"studio_product_home_panel: {exc}")
        return {
            "ok": False,
            "surface": "studio_product_home_panel",
            "current_status": "UNKNOWN / DASHBOARD MODEL FAILED",
            "product_status": "unknown",
            "internal_portable_mvp_closed": False,
            "release_grade_complete": False,
            "summary": {"blocker_count": 1, "release_grade_open_lane_count": len(_RELEASE_GRADE_LANES)},
            "evidence": {},
            "open_release_lanes": _release_grade_lanes(vault),
            "authority": {"read_only": True, "canonical_mutation_allowed": False},
        }


def _gather_mvp_readiness_panel(vault: Path, errors: list[str]) -> dict[str, Any]:
    """Return the no-secret MVP blocker map for the Studio cockpit."""

    try:
        from runtime.mvp_readiness_gate import (
            build_mvp_current_state,
            build_mvp_operator_unblock_packet,
            build_mvp_readiness_gate,
        )

        gate = build_mvp_readiness_gate(vault)
        operator_packet = build_mvp_operator_unblock_packet(vault)
        current_state_map = build_mvp_current_state(vault)
        summary = gate.get("summary") or {}
        passes = list(gate.get("passes") or [])
        inputs = list(gate.get("operator_inputs_required") or [])
        next_action_queue = list(gate.get("next_action_queue") or [])
        next_operator_action = (
            gate.get("next_operator_action") if isinstance(gate.get("next_operator_action"), dict) else None
        )
        completion_matrix = list(gate.get("completion_matrix") or [])
        completion_audit = (
            gate.get("completion_audit") if isinstance(gate.get("completion_audit"), dict) else {}
        )
        mvp_usecase_snapshot = (
            gate.get("mvp_usecase_snapshot")
            if isinstance(gate.get("mvp_usecase_snapshot"), dict)
            else {}
        )
        snapshot_usable_now = (
            mvp_usecase_snapshot.get("usable_now")
            if isinstance(mvp_usecase_snapshot.get("usable_now"), list)
            else []
        )
        snapshot_blocked_now = (
            mvp_usecase_snapshot.get("blocked_now")
            if isinstance(mvp_usecase_snapshot.get("blocked_now"), list)
            else []
        )
        snapshot_parked_or_later = (
            mvp_usecase_snapshot.get("parked_or_later")
            if isinstance(mvp_usecase_snapshot.get("parked_or_later"), list)
            else []
        )
        p0_inputs = [item for item in inputs if item.get("priority") == "P0"]
        p1_inputs = [item for item in inputs if item.get("priority") == "P1"]
        operator_schema = list(operator_packet.get("operator_input_schema") or [])
        operator_template = (
            operator_packet.get("operator_input_template")
            if isinstance(operator_packet.get("operator_input_template"), dict)
            else {}
        )
        operator_template_groups = (
            operator_template.get("groups") if isinstance(operator_template.get("groups"), list) else []
        )
        current_state_decision = (
            current_state_map.get("completion_decision")
            if isinstance(current_state_map.get("completion_decision"), dict)
            else {}
        )
        current_state_operator = (
            current_state_map.get("operator_action_required")
            if isinstance(current_state_map.get("operator_action_required"), dict)
            else {}
        )
        current_state_template_artifact = (
            current_state_map.get("operator_input_template_artifact")
            if isinstance(current_state_map.get("operator_input_template_artifact"), dict)
            else {}
        )
        current_state_barrier = (
            current_state_map.get("autonomous_completion_barrier")
            if isinstance(current_state_map.get("autonomous_completion_barrier"), dict)
            else {}
        )
        current_state_safety_contract = (
            current_state_map.get("completion_safety_contract")
            if isinstance(current_state_map.get("completion_safety_contract"), dict)
            else {}
        )
        current_state_approval_boundary = (
            current_state_map.get("approval_queue_boundary")
            if isinstance(current_state_map.get("approval_queue_boundary"), dict)
            else {}
        )
        current_state_setup_boundary = (
            current_state_map.get("setup_scope_boundary")
            if isinstance(current_state_map.get("setup_scope_boundary"), dict)
            else {}
        )
        current_state_pass_status_by_id = (
            current_state_map.get("pass_status_by_id")
            if isinstance(current_state_map.get("pass_status_by_id"), dict)
            else {}
        )
        current_state_summary = {
            "surface": current_state_map.get("surface"),
            "current_sector": current_state_map.get("current_sector"),
            "readiness_status": current_state_map.get("readiness_status"),
            "overall_goal_complete": bool(current_state_map.get("overall_goal_complete")),
            "pass_status_count": int(current_state_map.get("pass_status_count") or 0),
            "pass_status_by_id": dict(current_state_pass_status_by_id),
            "safe_to_call_update_goal_complete": bool(
                current_state_decision.get("safe_to_call_update_goal_complete")
            ),
            "no_safe_autonomous_completion_pass_available": bool(
                current_state_barrier.get("no_safe_autonomous_completion_pass_available")
            ),
            "update_goal_allowed": bool(current_state_barrier.get("update_goal_allowed")),
            "next_operator_action_id": current_state_operator.get("next_operator_action_id"),
            "next_recommended_pass": current_state_barrier.get("next_recommended_pass"),
            "p0_blocker_ids": list(current_state_operator.get("p0_blocker_ids") or []),
            "p1_decision_ids": list(current_state_operator.get("p1_decision_ids") or []),
            "usable_now_count": len(current_state_map.get("usable_now") or []),
            "blocked_now_count": len(current_state_map.get("blocked_now") or []),
            "parked_or_later_count": len(current_state_map.get("parked_or_later") or []),
            "approval_queue_boundary": dict(current_state_approval_boundary),
            "setup_scope_boundary": dict(current_state_setup_boundary),
            "operator_input_template_artifact": dict(current_state_template_artifact),
            "autonomous_completion_barrier": dict(current_state_barrier),
            "completion_safety_contract": dict(current_state_safety_contract),
            "source_command": "python -m runtime.cli.main mvp current-state --json",
        }
        completion_decision = {
            "objective_achieved": bool(current_state_decision.get("objective_achieved")),
            "safe_to_call_update_goal_complete": bool(
                current_state_decision.get("safe_to_call_update_goal_complete")
            ),
            "operator_input_ids": list(current_state_decision.get("operator_input_ids") or []),
            "p0_blocker_ids": list(current_state_decision.get("p0_blocker_ids") or []),
            "p1_decision_ids": list(current_state_decision.get("p1_decision_ids") or []),
            "blocked_requirement_ids": list(
                current_state_decision.get("blocked_requirement_ids") or []
            ),
            "incomplete_or_operator_blocked_requirements": list(
                current_state_decision.get("incomplete_or_operator_blocked_requirements")
                or []
            ),
        }
        operator_handoff = {
            "current_state_map_command": "python -m runtime.cli.main mvp current-state --json",
            "operator_unblock_packet_command": "python -m runtime.cli.main mvp operator-unblock-packet --json",
            "validate_operator_input_command": (
                "python -m runtime.cli.main mvp validate-operator-input --input <OPERATOR_INPUT_JSON> --json"
            ),
            "operator_input_schema_version": operator_packet.get("operator_input_schema_version"),
            "operator_input_template_version": operator_packet.get("operator_input_template_version"),
            "operator_input_schema_groups": [
                {
                    "id": item.get("id"),
                    "priority": item.get("priority"),
                    "field_names": [field.get("name") for field in item.get("fields") or []],
                    "validation_command": item.get("validation_command"),
                }
                for item in operator_schema
            ],
            "operator_input_template_groups": [
                {
                    "id": item.get("id"),
                    "priority": item.get("priority"),
                    "field_names": list((item.get("template_values") or {}).keys()),
                    "validation_command": item.get("validation_command"),
                }
                for item in operator_template_groups
            ],
            "forbidden_values": list(operator_template.get("forbidden_values") or []),
            "operator_input_template_artifact": dict(current_state_template_artifact),
            "source_values_echoed": False,
            "candidate_values_visible": False,
            "followup_requires_separate_operator_confirmation": True,
            "safe_followup_commands_are_templates_only": True,
        }
        checks = gate.get("checks") if isinstance(gate.get("checks"), dict) else {}
        provider = checks.get("provider_credentials") if isinstance(checks.get("provider_credentials"), dict) else {}
        ventureops = checks.get("ventureops") if isinstance(checks.get("ventureops"), dict) else {}
        approvals = checks.get("studio_approvals") if isinstance(checks.get("studio_approvals"), dict) else {}
        agent_bus = checks.get("agent_bus") if isinstance(checks.get("agent_bus"), dict) else {}
        agent_bus_lifecycle = (
            agent_bus.get("lifecycle") if isinstance(agent_bus.get("lifecycle"), dict) else {}
        )
        agent_bus_proof = (
            agent_bus_lifecycle.get("proof_task")
            if isinstance(agent_bus_lifecycle.get("proof_task"), dict)
            else {}
        )
        graph = checks.get("graph_source_intelligence") if isinstance(checks.get("graph_source_intelligence"), dict) else {}
        system_control = checks.get("full_system_control") if isinstance(checks.get("full_system_control"), dict) else {}
        system_boundary = (
            system_control.get("boundary") if isinstance(system_control.get("boundary"), dict) else {}
        )
        system_authority = (
            system_boundary.get("authority") if isinstance(system_boundary.get("authority"), dict) else {}
        )
        authority = gate.get("authority") if isinstance(gate.get("authority"), dict) else {}
        safe_commands = []
        for item in inputs:
            if item.get("safe_next_command"):
                safe_commands.append(
                    {
                        "id": item.get("id"),
                        "priority": item.get("priority"),
                        "command": item.get("safe_next_command"),
                        "validation_command": item.get("validation_command"),
                    }
                )

        return {
            "ok": True,
            "surface": "studio_mvp_readiness_panel",
            "readiness_status": gate.get("readiness_status"),
            "overall_goal_complete": bool(gate.get("overall_goal_complete")),
            "objective_achieved": completion_decision["objective_achieved"],
            "safe_to_call_update_goal_complete": completion_decision[
                "safe_to_call_update_goal_complete"
            ],
            "no_safe_autonomous_completion_pass_available": bool(
                current_state_barrier.get("no_safe_autonomous_completion_pass_available")
            ),
            "update_goal_allowed": bool(current_state_barrier.get("update_goal_allowed")),
            "operator_input_ids": completion_decision["operator_input_ids"],
            "p0_blocker_ids": completion_decision["p0_blocker_ids"],
            "p1_decision_ids": completion_decision["p1_decision_ids"],
            "blocked_requirement_ids": completion_decision["blocked_requirement_ids"],
            "incomplete_or_operator_blocked_requirements": completion_decision[
                "incomplete_or_operator_blocked_requirements"
            ],
            "completion_decision": completion_decision,
            "autonomous_completion_barrier": dict(current_state_barrier),
            "completion_safety_contract": dict(current_state_safety_contract),
            "next_recommended_pass": summary.get("next_recommended_pass"),
            "next_operator_action_id": summary.get("next_operator_action_id"),
            "next_action_count": int(summary.get("next_action_count") or len(next_action_queue)),
            "completion_matrix_count": int(summary.get("completion_matrix_count") or len(completion_matrix)),
            "blocked_requirement_count": int(summary.get("blocked_requirement_count") or 0),
            "pass_count": len(passes),
            "p0_blocker_count": int(summary.get("p0_blocker_count") or len(p0_inputs)),
            "operator_input_count": int(summary.get("operator_input_count") or len(inputs)),
            "next_operator_action": next_operator_action,
            "next_action_queue": next_action_queue,
            "completion_matrix": completion_matrix,
            "completion_audit": completion_audit,
            "current_state_map": current_state_summary,
            "approval_queue_boundary": dict(current_state_approval_boundary),
            "setup_scope_boundary": dict(current_state_setup_boundary),
            "mvp_usecase_snapshot": mvp_usecase_snapshot,
            "p0_operator_inputs": [
                {
                    "id": item.get("id"),
                    "description": item.get("description"),
                    "missing_inputs": list(item.get("missing_inputs") or []),
                    "provided_inputs": dict(item.get("provided_inputs") or {}),
                    "next_required_action": item.get("next_required_action"),
                    "ready_to_author_scope_approval": bool(item.get("ready_to_author_scope_approval")),
                    "ready_to_author_scope_packet": bool(item.get("ready_to_author_scope_packet")),
                    "ready_for_live_client_workflow_proof": bool(
                        item.get("ready_for_live_client_workflow_proof")
                    ),
                }
                for item in p0_inputs
            ],
            "p1_operator_inputs": [
                {
                    "id": item.get("id"),
                    "description": item.get("description"),
                    "approval_id": item.get("approval_id"),
                }
                for item in p1_inputs
            ],
            "operator_input_template_artifact": dict(current_state_template_artifact),
            "operator_input_handoff": operator_handoff,
            "operator_briefing_refs": [
                {
                    "id": "operator_next_action_card",
                    "label": "MVP next action card",
                    "path": "07_LOGS/Operator-Briefs/2026-05-13-mvp-next-action-card.md",
                    "purpose": "short no-secret operator card for the current P0/P1 blockers",
                },
                {
                    "id": "credential_handoff_card",
                    "label": "MVP credential handoff card",
                    "path": "07_LOGS/Operator-Briefs/2026-05-13-mvp-openai-secret-reference-handoff-card.md",
                    "purpose": "P0/P1/P2 credential reference handoff without secret values",
                },
                {
                    "id": "current_openai_handoff_guide",
                    "label": "Current P0 OpenAI handoff guide",
                    "path": "07_LOGS/Operator-Briefs/2026-05-14-openai-api-key-later-guide.md",
                    "purpose": "current no-secret operator guide for resolving the OpenAI reference by reference name only",
                },
                {
                    "id": "pending_chat_approval_decision_card",
                    "label": "MVP pending Chat approval decision card",
                    "path": "07_LOGS/Operator-Briefs/2026-05-13-mvp-pending-chat-approval-decision-card.md",
                    "purpose": "read-only approval summary for operator approve/reject/leave-pending decision",
                },
                {
                    "id": "pending_chat_consumption_readiness_card",
                    "label": "MVP pending Chat consumption readiness card",
                    "path": "07_LOGS/Operator-Briefs/2026-05-13-mvp-pending-chat-consumption-readiness-card.md",
                    "purpose": "no-execution exact-once consumption readiness summary for the pending Chat approval",
                },
                {
                    "id": "current_goal_pass_plan",
                    "label": "MVP current goal and pass plan",
                    "path": "06_AGENTS/ChaseOS-MVP-Current-Goal-and-Pass-Plan.md",
                    "purpose": "operator-readable current goal, sector, blockers, and ten-pass plan",
                },
                {
                    "id": "operator_unblock_packet",
                    "label": "MVP operator unblock packet",
                    "path": "06_AGENTS/ChaseOS-MVP-Operator-Unblock-Packet.md",
                    "purpose": "operator-owned P0/P1 input handoff",
                },
                {
                    "id": "operator_input_template",
                    "label": "MVP operator input template",
                    "path": "07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json",
                    "purpose": "no-secret fillable input packet",
                },
            ],
            "safe_next_commands": safe_commands,
            "pass_statuses": [
                {
                    "pass": row.get("pass"),
                    "name": row.get("name"),
                    "status": row.get("status"),
                    "blockers": list(row.get("blockers") or []),
                }
                for row in passes
            ],
            "key_checks": {
                "provider_status": provider.get("status"),
                "provider_secret_reference_target": provider.get("secret_reference_target"),
                "provider_secret_reference_target_is_placeholder": bool(
                    provider.get("secret_reference_target_is_placeholder")
                ),
                "provider_secret_reference_resolvable": bool(provider.get("secret_reference_resolvable")),
                "provider_secret_reference_probe_source": provider.get("secret_reference_probe_source"),
                "provider_secret_reference_probe_error": provider.get("secret_reference_probe_error"),
                "provider_reference_presence_check_commands": list(
                    provider.get("reference_presence_check_commands") or []
                ),
                "provider_reference_presence_check_outputs_secret_value": bool(
                    provider.get("reference_presence_check_outputs_secret_value")
                ),
                "provider_validation_command": provider.get("setup_provider_validation_command"),
                "provider_live_smoke_readiness_command": (
                    "python -m runtime.cli.main runtime provider live-smoke-readiness --json"
                ),
                "credential_handoff_command": "python -m runtime.cli.main mvp credential-handoff --json",
                "provider_blockers": list(provider.get("blockers") or []),
                "current_state_map_surface": current_state_summary["surface"],
                "current_state_map_pass_status_count": current_state_summary["pass_status_count"],
                "current_state_map_pass_status_by_id_count": len(current_state_pass_status_by_id),
                "current_state_map_safe_to_call_update_goal_complete": current_state_summary[
                    "safe_to_call_update_goal_complete"
                ],
                "current_state_map_no_safe_autonomous_completion_pass_available": current_state_summary[
                    "no_safe_autonomous_completion_pass_available"
                ],
                "current_state_map_update_goal_allowed": current_state_summary[
                    "update_goal_allowed"
                ],
                "current_state_map_next_operator_action_id": current_state_summary[
                    "next_operator_action_id"
                ],
                "current_state_map_next_recommended_pass": current_state_summary[
                    "next_recommended_pass"
                ],
                "current_state_map_operator_input_template_path": current_state_template_artifact.get("path"),
                "current_state_map_operator_input_template_exists": bool(
                    current_state_template_artifact.get("exists")
                ),
                "current_state_map_operator_input_template_contains_secret_values": bool(
                    current_state_template_artifact.get("contains_secret_values")
                ),
                "current_state_map_approval_pending_count": int(
                    current_state_approval_boundary.get("pending_count") or 0
                ),
                "current_state_map_approval_tracked_pending_count": int(
                    current_state_approval_boundary.get("tracked_pending_count") or 0
                ),
                "current_state_map_approval_untracked_pending_count": int(
                    current_state_approval_boundary.get("untracked_pending_approval_count")
                    or 0
                ),
                "current_state_map_untracked_pending_approvals_are_current_mvp_blockers": bool(
                    current_state_approval_boundary.get(
                        "untracked_pending_approvals_are_current_mvp_blockers"
                    )
                ),
                "current_state_map_tracked_chat_approval_is_current_mvp_decision": bool(
                    current_state_approval_boundary.get(
                        "tracked_chat_approval_is_current_mvp_decision"
                    )
                ),
                "current_state_map_setup_scope_status": current_state_setup_boundary.get(
                    "status"
                ),
                "current_state_map_setup_wide_invalid_provider_count": len(
                    current_state_setup_boundary.get("setup_wide_invalid_provider_ids")
                    or []
                ),
                "current_state_map_setup_wide_invalid_integration_count": len(
                    current_state_setup_boundary.get("setup_wide_invalid_integration_ids")
                    or []
                ),
                "current_state_map_non_mvp_setup_gap_count": len(
                    current_state_setup_boundary.get("non_mvp_setup_gap_ids") or []
                ),
                "current_state_map_non_mvp_setup_gaps_are_current_mvp_blockers": bool(
                    current_state_setup_boundary.get(
                        "non_mvp_setup_gaps_are_current_mvp_blockers"
                    )
                ),
                "current_state_map_setup_wide_validation_command": (
                    current_state_setup_boundary.get("setup_wide_validation_command")
                ),
                "autonomous_completion_barrier_active": bool(
                    current_state_barrier.get("active")
                ),
                "autonomous_completion_barrier_rows_covered": bool(
                    current_state_barrier.get("all_numbered_mvp_rows_covered")
                ),
                "autonomous_completion_barrier_update_goal_allowed": bool(
                    current_state_barrier.get("update_goal_allowed")
                ),
                "autonomous_completion_barrier_no_safe_autonomous_completion_pass_available": bool(
                    current_state_barrier.get("no_safe_autonomous_completion_pass_available")
                ),
                "autonomous_completion_barrier_next_operator_action_id": current_state_barrier.get(
                    "next_operator_action_id"
                ),
                "autonomous_completion_barrier_next_recommended_pass": current_state_barrier.get(
                    "next_recommended_pass"
                ),
                "completion_safety_contract_status": current_state_safety_contract.get(
                    "status"
                ),
                "completion_safety_contract_checklist_coverage_is_not_completion": bool(
                    current_state_safety_contract.get(
                        "checklist_coverage_is_not_completion"
                    )
                ),
                "completion_safety_contract_update_goal_allowed": bool(
                    current_state_safety_contract.get("update_goal_allowed")
                ),
                "completion_safety_contract_required_before_update_goal_complete": list(
                    current_state_safety_contract.get(
                        "required_before_update_goal_complete"
                    )
                    or []
                ),
                "next_operator_action_id": summary.get("next_operator_action_id"),
                "next_action_count": int(summary.get("next_action_count") or len(next_action_queue)),
                "completion_matrix_count": int(summary.get("completion_matrix_count") or len(completion_matrix)),
                "blocked_requirement_count": int(summary.get("blocked_requirement_count") or 0),
                "blocked_requirement_ids": list(completion_audit.get("blocked_requirement_ids") or []),
                "mvp_usecase_snapshot_surface": mvp_usecase_snapshot.get("surface"),
                "mvp_usecase_snapshot_status": mvp_usecase_snapshot.get("readiness_status"),
                "current_mvp_usecase": mvp_usecase_snapshot.get("current_mvp_usecase"),
                "usable_now_count": len(snapshot_usable_now),
                "blocked_now_count": len(snapshot_blocked_now),
                "parked_or_later_count": len(snapshot_parked_or_later),
                "p0_usecase_blocker_ids": list(mvp_usecase_snapshot.get("p0_blocker_ids") or []),
                "p1_usecase_decision_ids": list(mvp_usecase_snapshot.get("p1_decision_ids") or []),
                "operator_input_schema_version": operator_handoff["operator_input_schema_version"],
                "operator_input_template_version": operator_handoff["operator_input_template_version"],
                "operator_input_group_count": len(operator_handoff["operator_input_schema_groups"]),
                "operator_input_template_group_count": len(
                    operator_handoff["operator_input_template_groups"]
                ),
                "operator_input_validator_command": operator_handoff["validate_operator_input_command"],
                "operator_input_template_artifact_path": current_state_template_artifact.get("path"),
                "operator_input_template_artifact_exists": bool(
                    current_state_template_artifact.get("exists")
                ),
                "operator_input_template_artifact_contains_secret_values": bool(
                    current_state_template_artifact.get("contains_secret_values")
                ),
                "operator_input_values_visible": False,
                "ventureops_status": ventureops.get("status"),
                "ventureops_missing_inputs": list(ventureops.get("missing_inputs") or []),
                "ventureops_provided_inputs": dict(ventureops.get("provided_inputs") or {}),
                "ventureops_next_required_action": ventureops.get("next_required_action"),
                "ventureops_manifest_command": ventureops.get("real_client_input_manifest_command"),
                "ventureops_next_safe_command": ventureops.get("next_safe_command"),
                "ventureops_ready_to_author_scope_approval": bool(
                    ventureops.get("ready_to_author_scope_approval")
                ),
                "ventureops_ready_to_author_scope_packet": bool(ventureops.get("ready_to_author_scope_packet")),
                "ventureops_ready_for_live_client_workflow_proof": bool(
                    ventureops.get("ready_for_live_client_workflow_proof")
                ),
                "ventureops_approval_artifact_present": bool(ventureops.get("approval_artifact_present")),
                "ventureops_source_paths_valid": bool(ventureops.get("source_paths_valid")),
                "ventureops_scope_approval_artifact_valid": bool(
                    ventureops.get("scope_approval_artifact_valid")
                ),
                "pending_approval_id": (approvals.get("tracked_pending_chat_approval") or {}).get("approval_id")
                if isinstance(approvals.get("tracked_pending_chat_approval"), dict)
                else None,
                "pending_chat_consumption_readiness_command": approvals.get(
                    "approval_consumption_readiness_command"
                ),
                "agent_bus_status": agent_bus.get("status"),
                "agent_bus_proof_task_id": agent_bus_proof.get("task_id"),
                "agent_bus_proof_task_status": agent_bus_proof.get("status"),
                "agent_bus_lifecycle_complete": bool(
                    agent_bus_lifecycle.get("task_created_claimed_executed_artifact_logged")
                ),
                "graph_source_status": graph.get("status"),
                "source_graph_context_ready": bool(graph.get("workflow_can_reference_context_without_mutation")),
                "system_control_status": system_control.get("status"),
                "broad_system_control_allowed": bool(system_authority.get("broad_system_control_allowed")),
                "browser_system_automation_allowed_now": bool(
                    system_authority.get("browser_system_automation_allowed_now")
                ),
                "host_mutation_allowed_now": bool(system_authority.get("host_mutation_allowed_now")),
            },
            "evidence_refs": [
                "python -m runtime.cli.main mvp current-state --json",
                "python -m runtime.cli.main mvp credential-handoff --json",
                "python -m runtime.cli.main mvp readiness-gate --json",
                "python -m runtime.cli.main mvp operator-unblock-packet --json",
                "python -m runtime.cli.main mvp validate-operator-input --input <OPERATOR_INPUT_JSON> --json",
                "python -m runtime.cli.main runtime provider live-smoke-readiness --json",
                "runtime/mvp_readiness_gate.py",
                "runtime/cli/main.py",
                "runtime/mvp_agent_bus_lifecycle.py",
                "runtime/mvp_source_context.py",
                "runtime/mvp_system_control_boundary.py",
                "07_LOGS/Operator-Briefs/2026-05-13-mvp-next-action-card.md",
                "07_LOGS/Operator-Briefs/2026-05-13-mvp-openai-secret-reference-handoff-card.md",
                "07_LOGS/Operator-Briefs/2026-05-14-openai-api-key-later-guide.md",
                "07_LOGS/Operator-Briefs/2026-05-13-mvp-pending-chat-approval-decision-card.md",
                "07_LOGS/Operator-Briefs/2026-05-13-mvp-pending-chat-consumption-readiness-card.md",
                "07_LOGS/Operator-Briefs/2026-05-13-mvp-operator-input-template.json",
                "06_AGENTS/ChaseOS-MVP-Current-Goal-and-Pass-Plan.md",
                "06_AGENTS/ChaseOS-MVP-Completion-Audit.md",
                "06_AGENTS/ChaseOS-MVP-Operator-Unblock-Packet.md",
            ],
            "authority": {
                "read_only": True,
                "secret_values_read": bool(authority.get("secret_values_read")),
                "secret_values_visible": bool(authority.get("secret_values_visible")),
                "provider_calls_allowed": bool(authority.get("provider_calls_allowed")),
                "provider_calls_performed": bool(authority.get("provider_calls_performed")),
                "approval_execution_allowed": bool(authority.get("approval_execution_allowed")),
                "approval_consumption_performed": bool(authority.get("approval_consumption_performed")),
                "agent_bus_task_write_allowed": bool(authority.get("agent_bus_task_write_allowed")),
                "runtime_dispatch_allowed": bool(authority.get("runtime_dispatch_allowed")),
                "browser_control_allowed": bool(authority.get("browser_control_allowed")),
                "host_mutation_allowed": bool(authority.get("host_mutation_allowed")),
                "canonical_mutation_allowed": bool(authority.get("canonical_mutation_allowed")),
            },
        }
    except Exception as exc:  # noqa: BLE001
        errors.append(f"mvp_readiness_panel: {exc}")
        return {
            "ok": False,
            "surface": "studio_mvp_readiness_panel",
            "readiness_status": "unavailable",
            "overall_goal_complete": False,
            "next_recommended_pass": None,
            "next_operator_action_id": None,
            "no_safe_autonomous_completion_pass_available": False,
            "update_goal_allowed": False,
            "next_action_count": 0,
            "completion_matrix_count": 0,
            "blocked_requirement_count": 0,
            "pass_count": 0,
            "p0_blocker_count": 0,
            "operator_input_count": 0,
            "next_operator_action": None,
            "next_action_queue": [],
            "completion_matrix": [],
            "completion_audit": {},
            "current_state_map": {},
            "approval_queue_boundary": {},
            "setup_scope_boundary": {},
            "mvp_usecase_snapshot": {},
            "p0_operator_inputs": [],
            "p1_operator_inputs": [],
            "operator_input_template_artifact": {},
            "operator_input_handoff": {},
            "operator_briefing_refs": [],
            "safe_next_commands": [],
            "pass_statuses": [],
            "key_checks": {},
            "evidence_refs": [],
            "authority": {
                "read_only": True,
                "secret_values_read": False,
                "secret_values_visible": False,
                "provider_calls_allowed": False,
                "provider_calls_performed": False,
                "approval_execution_allowed": False,
                "approval_consumption_performed": False,
                "agent_bus_task_write_allowed": False,
                "runtime_dispatch_allowed": False,
                "browser_control_allowed": False,
                "host_mutation_allowed": False,
                "canonical_mutation_allowed": False,
            },
        }


def _gather_ventureops_real_world_usecase_panel(vault: Path, errors: list[str]) -> dict[str, Any]:
    """Return the Studio-visible VentureOps implementation/revenue gate panel."""

    try:
        from runtime.studio.ventureops_real_world_usecase_panel import (
            build_ventureops_real_world_usecase_panel,
        )

        return build_ventureops_real_world_usecase_panel(vault)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"ventureops_real_world_usecase_panel: {exc}")
        return {
            "ok": False,
            "surface": "studio_ventureops_real_world_usecase_panel",
            "status": "unavailable",
            "headline": "VentureOps real-use hardening",
            "summary": {
                "feature_implementation_complete": False,
                "operator_evidence_required_for_tests": False,
                "real_world_delivery_revenue_complete": False,
                "safe_to_mark_real_world_delivery_revenue_complete": False,
                "real_world_missing_requirement_count": 0,
                "hardening_check_count": 0,
                "hardening_checks_passed": 0,
                "guide_exists": False,
            },
            "studio_entrypoints": [],
            "real_world_test_usecase": {},
            "rehearsal_steps": [],
            "safe_commands": [],
            "operator_guide": {},
            "hardening_checks": [],
            "local_evidence_chain": {},
            "real_world_missing_requirements": [],
            "authority": {
                "read_only": True,
                "writes_vault": False,
                "canonical_mutation_allowed": False,
            },
        }


def _gather_memory_panel(vault: Path, errors: list[str]) -> dict[str, Any]:
    try:
        mem_root = vault / _MEMORY_ADAPTERS_DIR
        if not mem_root.exists():
            return {"registered_runtimes": [], "runtime_count": 0}
        runtimes = []
        for d in sorted(mem_root.iterdir()):
            if d.is_dir() and not d.name.startswith("_"):
                has_profile = (d / "profile.json").exists()
                has_ledger = (d / "identity-ledger.json").exists()
                has_nav_map = (d / "nav-map.json").exists()
                runtimes.append({
                    "runtime_id": d.name,
                    "has_profile": has_profile,
                    "has_identity_ledger": has_ledger,
                    "has_nav_map": has_nav_map,
                })
        return {"registered_runtimes": runtimes, "runtime_count": len(runtimes)}
    except Exception as exc:
        errors.append(f"memory_panel: {exc}")
        return {"registered_runtimes": [], "runtime_count": 0}


def _gather_audit_panel(vault: Path, errors: list[str]) -> dict[str, Any]:
    try:
        audit_root = vault / _AUDIT_DIR
        if not audit_root.exists():
            return {"recent_entry_count": 0, "last_entry_at": None}
        files = sorted(audit_root.glob("*.md"), key=lambda f: f.name, reverse=True)
        last_at = files[0].name[:26].replace("__", "T").replace("_", ":") if files else None
        return {
            "recent_entry_count": len(files),
            "last_entry_at": last_at,
            "sample_entries": [f.name for f in files[:5]],
        }
    except Exception as exc:
        errors.append(f"audit_panel: {exc}")
        return {"recent_entry_count": 0, "last_entry_at": None}


def _gather_approval_panel(vault: Path, errors: list[str]) -> dict[str, Any]:
    try:
        import json
        approval_root = vault / _APPROVAL_DIR
        if not approval_root.exists():
            return {"pending": 0, "total": 0, "by_status": {}}
        by_status: dict[str, int] = {}
        for f in approval_root.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                s = data.get("status", "unknown")
                by_status[s] = by_status.get(s, 0) + 1
            except Exception:
                by_status["unreadable"] = by_status.get("unreadable", 0) + 1
        total = sum(by_status.values())
        return {
            "pending": by_status.get("pending", 0),
            "total": total,
            "by_status": by_status,
        }
    except Exception as exc:
        errors.append(f"approval_panel: {exc}")
        return {"pending": 0, "total": 0, "by_status": {}}


def _gather_runtime_startup_panel(vault: Path, errors: list[str]) -> dict[str, Any]:
    try:
        if not (vault / "runtime" / "lifecycle").exists():
            return {
                "ok": True,
                "surface_count": 0,
                "manageable_surface_count": 0,
                "visual_surface_count": 0,
                "allowed_action_count": 0,
                "local_app_available": False,
                "local_app_command": "chaseos studio runtime-startup-controls-app --dry-run --json",
                "local_app_url": None,
                "authority": {
                    "binds_loopback_only": True,
                    "direct_host_startup_write": False,
                    "uses_runtime_lifecycle_executor": True,
                    "live_toggle_requires_confirm_action": True,
                    "canonical_mutation_allowed": False,
                },
                "runtimes": [],
                "cards": [],
            }
        from runtime.studio.runtime_startup_controls import build_runtime_startup_controls_model

        model = build_runtime_startup_controls_model(vault)
        boundary = model.get("boundary") or {}
        cards = list(model.get("surface_cards") or [])
        manageable_cards = [card for card in cards if card.get("studio_control_enabled")]
        visual_cards = [card for card in cards if card.get("studio_visual_toggle_built")]
        runtimes = sorted({str(card.get("runtime_id")) for card in cards if card.get("runtime_id")})
        return {
            "ok": bool(model.get("ok", True)),
            "surface": model.get("surface"),
            "runtime_filter": model.get("runtime_filter"),
            "runtime_count": model.get("runtime_count"),
            "surface_count": model.get("surface_count", len(cards)),
            "manageable_surface_count": len(manageable_cards),
            "visual_surface_count": len(visual_cards),
            "allowed_action_count": len(manageable_cards),
            "local_app_available": False,
            "local_app_command": "chaseos studio runtime-startup-controls --dry-run --json",
            "local_app_url": None,
            "event_log_relative_path": None,
            "authority": {
                "binds_loopback_only": True,
                "direct_host_startup_write": bool(boundary.get("writes_host_startup", False)),
                "uses_runtime_lifecycle_executor": bool(boundary.get("uses_runtime_lifecycle_executor", True)),
                "live_toggle_requires_confirm_action": bool(boundary.get("live_toggle_requires_confirm_action", True)),
                "canonical_mutation_allowed": bool(boundary.get("canonical_mutation_allowed", False)),
            },
            "runtimes": runtimes,
            "cards": [
                {
                    "runtime_id": card.get("runtime_id"),
                    "surface_id": card.get("surface_id"),
                    "ui_label": card.get("ui_label"),
                    "current_state": card.get("current_state"),
                    "studio_control_enabled": bool(card.get("studio_control_enabled")),
                    "studio_visual_toggle_built": bool(card.get("studio_visual_toggle_built")),
                    "requires_confirm_action": bool(card.get("requires_confirm_action")),
                }
                for card in cards
            ],
        }
    except Exception as exc:
        errors.append(f"runtime_startup_panel: {exc}")
        return {
            "ok": False,
            "surface_count": 0,
            "manageable_surface_count": 0,
            "visual_surface_count": 0,
            "allowed_action_count": 0,
            "local_app_available": False,
            "cards": [],
        }


# ── Public API ────────────────────────────────────────────────────────────────

def _gather_pulse_panel(vault: Path, errors: list[str]) -> dict[str, Any]:
    try:
        from runtime.studio.pulse_inspector import get_pulse_summary

        summary = get_pulse_summary(vault)
        boundary = summary.get("boundary") or {}
        return {
            "ok": bool(summary.get("ok", True)),
            "surface": "studio_pulse_dashboard_panel",
            "inspector_surface": summary.get("surface"),
            "local_app_available": False,
            "local_app_command": "chaseos studio pulse-summary --json",
            "local_app_url": None,
            "total_decks": int(summary.get("total_decks") or 0),
            "decks_by_audience": dict(summary.get("decks_by_audience") or {}),
            "last_deck_generated_at": summary.get("last_deck_generated_at"),
            "total_candidates": int(summary.get("total_candidates") or 0),
            "total_review_decisions": int(summary.get("total_review_decisions") or 0),
            "counts_by_kind": dict(summary.get("counts_by_kind") or {}),
            "enqueue_results_by_status": dict(summary.get("enqueue_results_by_status") or {}),
            "approval_requests_total": int(summary.get("approval_requests_total") or 0),
            "authority": {
                "read_only": True,
                "writes_candidate_logs": bool(boundary.get("writes_candidate_logs")),
                "writes_review_decisions": bool(boundary.get("writes_review_decisions")),
                "applies_candidates": bool(boundary.get("applies_candidates")),
                "grants_approvals": bool(boundary.get("grants_approvals")),
                "triggers_execution": bool(boundary.get("triggers_execution")),
                "feedback_candidate_write_available": True,
                "canonical_mutation_allowed": bool(boundary.get("canonical_mutation_allowed")),
            },
        }
    except Exception as exc:
        errors.append(f"pulse_panel: {exc}")
        return {
            "ok": False,
            "surface": "studio_pulse_dashboard_panel",
            "total_decks": 0,
            "decks_by_audience": {},
            "total_candidates": 0,
            "total_review_decisions": 0,
            "counts_by_kind": {},
            "enqueue_results_by_status": {},
            "approval_requests_total": 0,
            "local_app_available": False,
            "local_app_command": "chaseos studio pulse-deck-app --dry-run --json",
            "local_app_url": None,
            "authority": {
                "read_only": True,
                "writes_candidate_logs": False,
                "writes_review_decisions": False,
                "applies_candidates": False,
                "grants_approvals": False,
                "triggers_execution": False,
                "feedback_candidate_write_available": False,
                "canonical_mutation_allowed": False,
            },
        }


def _operator_next_action_authority() -> dict[str, bool]:
    return {
        "presentation_only": True,
        "executes_actions": False,
        "provider_calls_allowed": False,
        "approval_execution_allowed": False,
        "task_writes_allowed": False,
        "browser_control_allowed": False,
        "config_writes_allowed": False,
        "writes_vault": False,
        "canonical_mutation_allowed": False,
    }


def _next_action_card(
    *,
    card_id: str,
    title: str,
    status: str,
    summary: str,
    operator_next_action: str,
    facts: dict[str, Any],
    evidence: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": card_id,
        "title": title,
        "status": status,
        "summary": summary,
        "operator_next_action": operator_next_action,
        "facts": facts,
        "evidence": evidence or [],
        "authority": _operator_next_action_authority(),
    }


def _gather_provider_runtime_panel(vault: Path, errors: list[str]) -> dict[str, Any]:
    """Return read-only runtime provider posture without live provider calls."""

    try:
        from runtime.providers.governance_status import build_runtime_provider_status

        status = build_runtime_provider_status(
            vault_root=vault,
            runtime_filter="all",
            probe_health=False,
        )
        boundary = dict(status.get("boundary") or {})
        boundary.update({
            "read_only": True,
            "presentation_only": True,
            "provider_calls_allowed": False,
            "provider_calls_performed": False,
        })
        return {
            "ok": True,
            "readiness_summary": status.get("readiness_summary") or {},
            "operator_default_provider": status.get("operator_default_provider") or {},
            "active_runtime": status.get("active_runtime") or {},
            "active_runtime_model_provider": status.get("active_runtime_model_provider") or {},
            "queues": status.get("queues") or {},
            "warnings": status.get("warnings") or [],
            "operator_summary": status.get("operator_summary") or {},
            "boundary": boundary,
        }
    except Exception as exc:
        errors.append(f"provider_runtime_panel: {exc}")
        return {
            "ok": False,
            "readiness_summary": {"posture": "unknown", "degradation_reasons": ["provider_runtime_panel_unavailable"]},
            "operator_default_provider": {},
            "active_runtime": {},
            "active_runtime_model_provider": {},
            "queues": {"stuck_count": 0, "no_chunk_count": 0, "queued_count": 0, "active_count": 0},
            "warnings": [],
            "operator_summary": {"headline": "Runtime provider posture unavailable"},
            "boundary": {"read_only": True, "presentation_only": True, "provider_calls_allowed": False},
        }


def _gather_workspace_mode_panel(vault: Path, errors: list[str]) -> dict[str, Any]:
    """Return the read-only WML Studio panel for dashboard and shell context."""

    try:
        from runtime.studio.workspace_mode_panel import build_workspace_mode_studio_panel

        return build_workspace_mode_studio_panel(vault)
    except Exception as exc:
        errors.append(f"workspace_mode_panel: {exc}")
        return {
            "ok": False,
            "surface": "studio_workspace_mode_panel",
            "summary": {
                "overall_status": "unavailable",
                "wml_product_feature_complete": False,
                "profiles_valid_count": 0,
                "expected_profile_count": 0,
                "approval_artifact_count": 0,
                "route_ready_count": 0,
                "route_blocked_count": 0,
                "manual_testing_ready": False,
            },
            "route_cards": [],
            "authority": {"read_only": True, "canonical_mutation_allowed": False},
        }


def _gather_personal_operator_context_panel(vault: Path, errors: list[str]) -> dict[str, Any]:
    """Return the read-only personal operator context index for Studio."""

    try:
        from runtime.studio.personal_operator_context_index import build_personal_operator_context_index

        return build_personal_operator_context_index(vault)
    except Exception as exc:
        errors.append(f"personal_operator_context_panel: {exc}")
        return {
            "ok": False,
            "surface": "studio_personal_operator_context_index",
            "status": "unavailable",
            "headline": "Personal operator context",
            "root_hub_path": "00_HOME/Personal-Operator-Index.md",
            "summary": {
                "group_count": 0,
                "tracked_file_count": 0,
                "existing_file_count": 0,
                "missing_file_count": 0,
                "project_operating_file_count": 0,
                "knowledge_root_count": 0,
                "link_check_count": 0,
                "link_check_passed_count": 0,
                "link_blocker_count": 0,
                "link_warning_count": 0,
            },
            "groups": [],
            "link_checks": [],
            "authority": {"read_only": True, "canonical_mutation_allowed": False},
        }


def _gather_personal_context_import_panel(vault: Path, errors: list[str]) -> dict[str, Any]:
    """Return the read-only personal context import planner for Studio."""

    try:
        from runtime.studio.personal_context_import import build_personal_context_import_panel

        return build_personal_context_import_panel(vault)
    except Exception as exc:
        errors.append(f"personal_context_import_panel: {exc}")
        return {
            "ok": False,
            "surface": "studio_personal_context_import_panel",
            "status": "unavailable",
            "headline": "Personal context import",
            "implementation_status": "PARTIAL / CANONICAL PROMOTION APPROVED EXECUTOR READY / PERSONAL MAP AND RUNTIME MUTATIONS BLOCKED",
            "summary": {
                "entrypoint_count": 0,
                "pipeline_stage_count": 0,
                "required_hub_count": 0,
                "missing_required_hub_count": 0,
                "node_family_count": 0,
            },
            "entrypoints": [],
            "pipeline_stages": [],
            "required_hubs": [],
            "missing_required_hubs": [],
            "node_families": [],
            "readiness": {
                "personal_context_import_panel_mounted": False,
                "settings_entrypoint_ready": False,
                "dashboard_entrypoint_ready": False,
                "live_import_writes_enabled": False,
            },
            "authority": {"read_only": True, "canonical_mutation_allowed": False},
        }


def _gather_discord_control_plane_panel(vault: Path, errors: list[str]) -> dict[str, Any]:
    """Return redacted Discord control-plane binding readiness for Studio."""

    try:
        from runtime.discord_bindings import build_discord_binding_validation

        validation = build_discord_binding_validation(vault)
        summary = validation.get("summary") or {}
        studio_control = validation.get("studio_runtime_control_plane") or {}
        return {
            "ok": bool(validation.get("ok", True)),
            "surface": "studio_discord_control_plane_panel",
            "status": validation.get("status"),
            "valid": bool(validation.get("valid")),
            "headline": "Discord runtime control-plane bindings",
            "binding_file": validation.get("binding_file") or {},
            "example_template": validation.get("example_template") or {},
            "setup_sop": validation.get("setup_sop") or {},
            "summary": {
                "active_runtime_count": int(summary.get("active_runtime_count") or 0),
                "active_runtime_ids": list(summary.get("active_runtime_ids") or []),
                "bound_channel_count": int(summary.get("bound_channel_count") or 0),
                "primary_channel_count": int(summary.get("primary_channel_count") or 0),
                "unbound_channel_names": list(summary.get("unbound_channel_names") or []),
                "secret_like_finding_count": int(summary.get("secret_like_finding_count") or 0),
                "gitignored": bool(summary.get("gitignored")),
            },
            "runtime_control_capabilities": list(studio_control.get("capabilities") or []),
            "future_runtime_rule": studio_control.get("future_runtime_rule"),
            "blockers": list(validation.get("blockers") or []),
            "warnings": list(validation.get("warnings") or []),
            "safe_commands": [
                "python -m runtime.cli.main setup discord validate --json",
                "python -m runtime.cli.main studio dashboard --json",
            ],
            "authority": {
                "read_only": True,
                "ids_visible": False,
                "secret_values_visible": False,
                "writes_binding_file": False,
                "discord_api_calls_performed": False,
                "agent_bus_task_write_allowed": False,
                "schedule_mutation_allowed": False,
                "canonical_mutation_allowed": False,
            },
        }
    except Exception as exc:
        errors.append(f"discord_control_plane_panel: {exc}")
        return {
            "ok": False,
            "surface": "studio_discord_control_plane_panel",
            "status": "unavailable",
            "valid": False,
            "headline": "Discord runtime control-plane bindings",
            "summary": {
                "active_runtime_count": 0,
                "active_runtime_ids": [],
                "bound_channel_count": 0,
                "primary_channel_count": 0,
                "unbound_channel_names": [],
                "secret_like_finding_count": 0,
                "gitignored": False,
            },
            "runtime_control_capabilities": [],
            "blockers": ["discord_binding_validation_unavailable"],
            "warnings": [],
            "authority": {"read_only": True, "ids_visible": False, "secret_values_visible": False},
        }


def _runtime_binding_valid(binding: dict[str, Any]) -> bool:
    if "valid" in binding:
        return bool(binding.get("valid"))
    primary = binding.get("primary") if isinstance(binding.get("primary"), dict) else {}
    provider_id = primary.get("provider_id")
    model_id = primary.get("model_id")
    return bool(provider_id and model_id)


def _build_operator_next_action_cards(
    *,
    provider_runtime: dict[str, Any],
    approvals: dict[str, Any],
    graph: dict[str, Any],
    launcher: dict[str, Any],
) -> list[dict[str, Any]]:
    readiness = provider_runtime.get("readiness_summary") or {}
    default_provider = provider_runtime.get("operator_default_provider") or {}
    binding = provider_runtime.get("active_runtime_model_provider") or {}
    queues = provider_runtime.get("queues") or {}
    warnings = list(provider_runtime.get("warnings") or [])
    operator_summary = provider_runtime.get("operator_summary") or {}
    posture = str(readiness.get("posture") or "unknown")
    provider_valid = bool(default_provider.get("valid"))
    binding_valid = _runtime_binding_valid(binding)

    graph_age = graph.get("age_hours")
    graph_status = "missing"
    if graph.get("snapshot_available"):
        graph_status = "stale" if isinstance(graph_age, (int, float)) and graph_age > 24 else "fresh"

    support_ports = list(launcher.get("support_ports") or [])
    hermes_support = next((item for item in support_ports if item.get("id") == "hermes-kanban-dashboard"), {})
    hermes_state = str((hermes_support.get("runtime_status") or {}).get("state") or "unknown")
    health_counts = launcher.get("health_counts") or {}
    offline_app_count = int(health_counts.get("offline") or 0)
    offline_apps = [
        {
            "id": app.get("id"),
            "title": app.get("title"),
            "command": app.get("command"),
        }
        for app in list(launcher.get("apps") or [])
        if str((app.get("runtime_status") or {}).get("state") or "unknown") == "offline"
    ]
    stuck_count = int(queues.get("stuck_count") or 0)
    no_chunk_count = int(queues.get("no_chunk_count") or 0)

    return [
        _next_action_card(
            card_id="provider_runtime_posture",
            title="Provider/runtime posture",
            status=posture,
            summary=str(operator_summary.get("headline") or "Read-only provider/runtime posture summary."),
            operator_next_action="Review `python -m runtime.cli.main runtime provider-status --json`; do not run live provider calls from the dashboard.",
            facts={
                "operator_default_provider": default_provider.get("provider_id"),
                "operator_default_provider_valid": provider_valid,
                "runtime_provider_binding_valid": binding_valid,
                "degradation_reasons": list(readiness.get("degradation_reasons") or []),
            },
            evidence=["runtime.providers.governance_status.build_runtime_provider_status(probe_health=False)"],
        ),
        _next_action_card(
            card_id="pending_approval_decision",
            title="Pending approval decisions",
            status="action_required" if int(approvals.get("pending") or 0) else "clear",
            summary=f"{int(approvals.get('pending') or 0)} pending approvals out of {int(approvals.get('total') or 0)} total records.",
            operator_next_action="Open the Approval Center/read-only approval panel and decide pending items through the governed approval path, not this dashboard.",
            facts={
                "pending": int(approvals.get("pending") or 0),
                "total": int(approvals.get("total") or 0),
                "by_status": dict(approvals.get("by_status") or {}),
            },
            evidence=[_APPROVAL_DIR],
        ),
        _next_action_card(
            card_id="stale_graph_snapshot_freshness",
            title="Graph snapshot freshness",
            status=graph_status,
            summary=(
                "No graph snapshot is available."
                if graph_status == "missing"
                else f"Latest graph snapshot age is {graph_age}h."
            ),
            operator_next_action="If stale, review graph hygiene/vault-maintain readiness and run only through the explicit governed workflow gate.",
            facts={
                "snapshot_available": bool(graph.get("snapshot_available")),
                "snapshot_id": graph.get("snapshot_id"),
                "age_hours": graph_age,
                "maintenance": graph.get("maintenance") or {},
            },
            evidence=["07_LOGS/Graph-Snapshots/", _GRAPH_REPORTS_DIR, _MAINTAIN_RUNS_DIR],
        ),
        _next_action_card(
            card_id="hermes_kanban_support_port",
            title="Hermes/Kanban support port",
            status=hermes_state,
            summary=f"Hermes/Kanban support surface on port {hermes_support.get('port') or 9119} is {hermes_state}.",
            operator_next_action="Use the Hermes/Kanban support URL only if reachable; if offline, start/check the Hermes dashboard service outside Studio.",
            facts={
                "port": hermes_support.get("port") or 9119,
                "health_url": (hermes_support.get("runtime_status") or {}).get("health_url") or hermes_support.get("health_url"),
                "state": hermes_state,
            },
            evidence=["runtime.studio.app_launcher._support_port_registry"],
        ),
        _next_action_card(
            card_id="offline_app_launch_guidance",
            title="Offline Studio app launch guidance",
            status="action_required" if offline_app_count else "clear",
            summary=f"{offline_app_count} registered Studio apps are offline; offline means not launched, not necessarily broken.",
            operator_next_action="Copy the app launch command from App Launcher and run it in an operator terminal; the dashboard must not start child apps.",
            facts={
                "offline_app_count": offline_app_count,
                "health_counts": dict(health_counts),
                "offline_apps": offline_apps[:6],
            },
            evidence=["runtime.studio.app_launcher.build_studio_app_launcher_plan"],
        ),
        _next_action_card(
            card_id="runtime_heartbeat_stuck_jobs",
            title="Runtime heartbeat / stuck jobs",
            status="blocked" if stuck_count or no_chunk_count or warnings else "clear",
            summary=f"Queue stuck={stuck_count}, no_chunk={no_chunk_count}; warnings={len(warnings)}.",
            operator_next_action="Inspect runtime provider status and runtime cockpit evidence; clear stuck jobs only through the governed runtime lane.",
            facts={
                "queued_count": int(queues.get("queued_count") or 0),
                "active_count": int(queues.get("active_count") or 0),
                "stuck_count": stuck_count,
                "no_chunk_count": no_chunk_count,
                "warnings": warnings[:6],
            },
            evidence=["runtime provider-status queues", "runtime heartbeats"],
        ),
    ]


def _gather_app_launcher_panel(
    vault: Path,
    errors: list[str],
    *,
    probe_child_apps: bool = True,
) -> dict[str, Any]:
    try:
        from runtime.studio.app_launcher import build_studio_app_launcher_plan

        plan = build_studio_app_launcher_plan(
            vault,
            host="127.0.0.1",
            port=8769,
            probe_health=probe_child_apps,
        )
        apps = list(plan.get("apps") or [])
        health_counts: dict[str, int] = {}
        for app in apps:
            state = str((app.get("runtime_status") or {}).get("state") or "unknown")
            health_counts[state] = health_counts.get(state, 0) + 1
        return {
            "ok": bool(plan.get("ok", True)),
            "surface": "studio_app_launcher_dashboard_panel",
            "launcher_surface": plan.get("surface"),
            "app_count": int(plan.get("app_count") or len(apps)),
            "read_only_app_count": sum(1 for app in apps if app.get("read_only")),
            "write_capable_app_count": sum(1 for app in apps if app.get("write_capable")),
            "confirmation_required_count": sum(1 for app in apps if app.get("requires_confirmation_for_writes")),
            "health_counts": health_counts,
            "support_port_count": int(plan.get("support_port_count") or 0),
            "support_ports": [
                {
                    "id": entry.get("id"),
                    "title": entry.get("title"),
                    "port": entry.get("port"),
                    "health_url": entry.get("health_url"),
                    "default_url": entry.get("default_url"),
                    "runtime_status": entry.get("runtime_status") or {},
                }
                for entry in list(plan.get("support_ports") or [])
            ],
            "local_app_available": True,
            "local_app_command": "chaseos studio app-launcher --dry-run --json",
            "local_app_url": plan.get("url"),
            "apps": [
                {
                    "id": app.get("id"),
                    "title": app.get("title"),
                    "command": app.get("command"),
                    "default_url": app.get("default_url"),
                    "read_only": bool(app.get("read_only")),
                    "write_capable": bool(app.get("write_capable")),
                    "requires_confirmation_for_writes": bool(app.get("requires_confirmation_for_writes")),
                    "runtime_status": app.get("runtime_status") or {},
                }
                for app in apps
            ],
            "authority": {
                "read_only": bool((plan.get("authority") or {}).get("read_only")),
                "starts_child_apps": bool((plan.get("authority") or {}).get("starts_child_apps")),
                "writes_vault": bool((plan.get("authority") or {}).get("writes_vault")),
                "workflow_execution_allowed": bool((plan.get("authority") or {}).get("workflow_execution_allowed")),
                "canonical_mutation_allowed": bool((plan.get("authority") or {}).get("canonical_mutation_allowed")),
            },
        }
    except Exception as exc:
        errors.append(f"app_launcher_panel: {exc}")
        return {
            "ok": False,
            "surface": "studio_app_launcher_dashboard_panel",
            "app_count": 0,
            "read_only_app_count": 0,
            "write_capable_app_count": 0,
            "confirmation_required_count": 0,
            "health_counts": {},
            "support_port_count": 0,
            "support_ports": [],
            "local_app_available": False,
            "apps": [],
            "authority": {
                "read_only": True,
                "starts_child_apps": False,
                "writes_vault": False,
                "workflow_execution_allowed": False,
                "canonical_mutation_allowed": False,
            },
        }


def get_dashboard(
    vault_root: str | Path,
    *,
    probe_child_apps: bool = True,
    lightweight: bool = False,
) -> dict[str, Any]:
    """
    Return a UI-ready operator dashboard model aggregating all subsystem state.

    All panels are gathered fail-open. Failures are recorded in the `errors` list
    but do not prevent other panels from being populated. The dashboard always
    returns `ok: True` unless vault_root itself is invalid.
    """
    vault = Path(vault_root).resolve()
    errors: list[str] = []

    def _safe(fn, name: str, fallback: dict) -> dict:
        try:
            return fn(vault, errors)
        except Exception as exc:
            errors.append(f"{name}: unexpected {exc}")
            return fallback

    def _deferred_panel(surface: str, summary: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "ok": True,
            "surface": surface,
            "status": "deferred_for_fast_command_center",
            "read_only": True,
            "summary": dict(summary or {}),
            "deferred_reason": "Home loaded a lightweight dashboard model; open the owning surface for full evidence.",
            "authority": {"read_only": True, "canonical_mutation_allowed": False},
        }

    schedule_panel = _safe(_gather_schedule_panel, "schedule_panel", {"total": 0, "enabled": 0, "disabled": 0, "schedules": []})
    mvp_readiness_panel = _deferred_panel(
        "studio_mvp_readiness_panel",
        {
            "overall_goal_complete": False,
            "p0_blocker_count": 0,
            "operator_input_count": 0,
            "completion_matrix_count": 0,
        },
    ) if lightweight else _safe(
        _gather_mvp_readiness_panel,
        "mvp_readiness_panel",
        {
            "ok": False,
            "surface": "studio_mvp_readiness_panel",
            "readiness_status": "unavailable",
            "overall_goal_complete": False,
            "p0_blocker_count": 0,
            "operator_input_count": 0,
            "p0_operator_inputs": [],
            "p1_operator_inputs": [],
            "operator_input_template_artifact": {},
            "operator_input_handoff": {},
            "current_state_map": {},
            "approval_queue_boundary": {},
            "setup_scope_boundary": {},
            "safe_next_commands": [],
            "pass_statuses": [],
            "authority": {"read_only": True, "canonical_mutation_allowed": False},
        },
    )
    studio_product_home_panel = _safe(
        _gather_studio_product_home_panel,
        "studio_product_home_panel",
        {
            "ok": False,
            "surface": "studio_product_home_panel",
            "current_status": "UNKNOWN",
            "internal_portable_mvp_closed": False,
            "release_grade_complete": False,
            "summary": {"release_grade_open_lane_count": len(_RELEASE_GRADE_LANES)},
            "open_release_lanes": _release_grade_lanes(vault),
        },
    )
    ventureops_real_world_usecase_panel = _deferred_panel(
        "studio_ventureops_real_world_usecase_panel",
        {
            "feature_implementation_complete": False,
            "operator_evidence_required_for_tests": False,
            "real_world_delivery_revenue_complete": False,
            "safe_to_mark_real_world_delivery_revenue_complete": False,
            "real_world_missing_requirement_count": 0,
            "hardening_check_count": 0,
            "hardening_checks_passed": 0,
            "guide_exists": False,
        },
    ) if lightweight else _safe(
        _gather_ventureops_real_world_usecase_panel,
        "ventureops_real_world_usecase_panel",
        {
            "ok": False,
            "surface": "studio_ventureops_real_world_usecase_panel",
            "status": "unavailable",
            "headline": "VentureOps real-use hardening",
            "summary": {
                "feature_implementation_complete": False,
                "operator_evidence_required_for_tests": False,
                "real_world_delivery_revenue_complete": False,
                "safe_to_mark_real_world_delivery_revenue_complete": False,
                "real_world_missing_requirement_count": 0,
                "hardening_check_count": 0,
                "hardening_checks_passed": 0,
                "guide_exists": False,
            },
            "studio_entrypoints": [],
            "rehearsal_steps": [],
            "safe_commands": [],
            "operator_guide": {},
            "hardening_checks": [],
            "authority": {"read_only": True, "canonical_mutation_allowed": False},
        },
    )
    workspace_mode_panel = _deferred_panel(
        "studio_workspace_mode_panel",
        {"overall_status": "deferred_for_fast_command_center"},
    ) if lightweight else _safe(
        _gather_workspace_mode_panel,
        "workspace_mode_panel",
        {
            "ok": False,
            "surface": "studio_workspace_mode_panel",
            "summary": {
                "overall_status": "unavailable",
                "wml_product_feature_complete": False,
                "profiles_valid_count": 0,
                "expected_profile_count": 0,
                "approval_artifact_count": 0,
                "route_ready_count": 0,
                "route_blocked_count": 0,
                "manual_testing_ready": False,
            },
            "route_cards": [],
            "authority": {"read_only": True, "canonical_mutation_allowed": False},
        },
    )
    personal_operator_context_panel = _deferred_panel(
        "studio_personal_operator_context_index",
        {"tracked_file_count": 0, "link_blocker_count": 0},
    ) if lightweight else _safe(
        _gather_personal_operator_context_panel,
        "personal_operator_context_panel",
        {
            "ok": False,
            "surface": "studio_personal_operator_context_index",
            "status": "unavailable",
            "headline": "Personal operator context",
            "root_hub_path": "00_HOME/Personal-Operator-Index.md",
            "summary": {
                "group_count": 0,
                "tracked_file_count": 0,
                "existing_file_count": 0,
                "missing_file_count": 0,
                "project_operating_file_count": 0,
                "knowledge_root_count": 0,
                "link_check_count": 0,
                "link_check_passed_count": 0,
                "link_blocker_count": 0,
                "link_warning_count": 0,
            },
            "groups": [],
            "link_checks": [],
            "authority": {"read_only": True, "canonical_mutation_allowed": False},
        },
    )
    personal_context_import_panel = _deferred_panel(
        "studio_personal_context_import_panel",
        {"entrypoint_count": 0, "pipeline_stage_count": 0, "node_family_count": 0},
    ) if lightweight else _safe(
        _gather_personal_context_import_panel,
        "personal_context_import_panel",
        {
            "ok": False,
            "surface": "studio_personal_context_import_panel",
            "status": "unavailable",
            "headline": "Personal context import",
            "implementation_status": "PARTIAL / CANONICAL PROMOTION APPROVED EXECUTOR READY / PERSONAL MAP AND RUNTIME MUTATIONS BLOCKED",
            "summary": {
                "entrypoint_count": 0,
                "pipeline_stage_count": 0,
                "required_hub_count": 0,
                "missing_required_hub_count": 0,
                "node_family_count": 0,
            },
            "entrypoints": [],
            "pipeline_stages": [],
            "required_hubs": [],
            "missing_required_hubs": [],
            "node_families": [],
            "readiness": {
                "personal_context_import_panel_mounted": False,
                "settings_entrypoint_ready": False,
                "dashboard_entrypoint_ready": False,
                "live_import_writes_enabled": False,
            },
            "authority": {"read_only": True, "canonical_mutation_allowed": False},
        },
    )
    discord_control_plane_panel = _deferred_panel(
        "studio_discord_control_plane_panel",
        {"active_runtime_count": 0, "bound_channel_count": 0, "secret_like_finding_count": 0},
    ) if lightweight else _safe(
        _gather_discord_control_plane_panel,
        "discord_control_plane_panel",
        {
            "ok": False,
            "surface": "studio_discord_control_plane_panel",
            "status": "unavailable",
            "valid": False,
            "summary": {
                "active_runtime_count": 0,
                "active_runtime_ids": [],
                "bound_channel_count": 0,
                "primary_channel_count": 0,
                "secret_like_finding_count": 0,
                "gitignored": False,
            },
            "runtime_control_capabilities": [],
            "authority": {"read_only": True, "ids_visible": False, "secret_values_visible": False},
        },
    )
    bus_panel = _safe(_gather_bus_panel, "bus_panel", {"total": 0, "by_status": {}, "open": 0})
    quarantine_panel = _safe(_gather_quarantine_panel, "quarantine_panel", {"total": 0, "by_class": {}})
    graph_panel = _safe(_gather_graph_panel, "graph_panel", {"snapshot_available": False})
    memory_panel = _safe(_gather_memory_panel, "memory_panel", {"registered_runtimes": [], "runtime_count": 0})
    audit_panel = _safe(_gather_audit_panel, "audit_panel", {"recent_entry_count": 0, "last_entry_at": None})
    approval_panel = _safe(_gather_approval_panel, "approval_panel", {"pending": 0, "total": 0, "by_status": {}})
    provider_runtime_panel = _safe(
        _gather_provider_runtime_panel,
        "provider_runtime_panel",
        {
            "ok": False,
            "readiness_summary": {"posture": "unknown", "degradation_reasons": []},
            "operator_default_provider": {},
            "active_runtime": {},
            "active_runtime_model_provider": {},
            "queues": {"stuck_count": 0, "no_chunk_count": 0, "queued_count": 0, "active_count": 0},
            "warnings": [],
            "operator_summary": {},
            "boundary": {"read_only": True, "presentation_only": True, "provider_calls_allowed": False},
        },
    )
    pulse_panel = _safe(
        _gather_pulse_panel,
        "pulse_panel",
        {
            "ok": False,
            "surface": "studio_pulse_dashboard_panel",
            "total_decks": 0,
            "decks_by_audience": {},
            "total_candidates": 0,
            "total_review_decisions": 0,
            "counts_by_kind": {},
            "enqueue_results_by_status": {},
            "approval_requests_total": 0,
        },
    )
    runtime_startup_panel = _deferred_panel(
        "studio_runtime_startup_panel",
        {"surface_count": 0, "manageable_surface_count": 0, "visual_surface_count": 0},
    ) if lightweight else _safe(
        _gather_runtime_startup_panel,
        "runtime_startup_panel",
        {
            "ok": False,
            "surface_count": 0,
            "manageable_surface_count": 0,
            "visual_surface_count": 0,
            "allowed_action_count": 0,
            "local_app_available": False,
            "cards": [],
        },
    )
    app_launcher_panel = _safe(
        lambda vault_path, panel_errors: _gather_app_launcher_panel(
            vault_path,
            panel_errors,
            probe_child_apps=probe_child_apps,
        ),
        "app_launcher_panel",
        {
            "ok": False,
            "surface": "studio_app_launcher_dashboard_panel",
            "app_count": 0,
            "read_only_app_count": 0,
            "write_capable_app_count": 0,
            "confirmation_required_count": 0,
            "health_counts": {},
            "support_port_count": 0,
            "support_ports": [],
            "local_app_available": False,
            "apps": [],
        },
    )

    operator_next_action_cards = _build_operator_next_action_cards(
        provider_runtime=provider_runtime_panel,
        approvals=approval_panel,
        graph=graph_panel,
        launcher=app_launcher_panel,
    )

    return {
        "ok": True,
        "surface": "studio_dashboard",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "vault_root": str(vault),
        "mvp_readiness_panel": mvp_readiness_panel,
        "studio_product_home_panel": studio_product_home_panel,
        "ventureops_real_world_usecase_panel": ventureops_real_world_usecase_panel,
        "workspace_mode_panel": workspace_mode_panel,
        "personal_operator_context_panel": personal_operator_context_panel,
        "personal_context_import_panel": personal_context_import_panel,
        "discord_control_plane_panel": discord_control_plane_panel,
        "schedule_panel": schedule_panel,
        "bus_panel": bus_panel,
        "quarantine_panel": quarantine_panel,
        "graph_panel": graph_panel,
        "memory_panel": memory_panel,
        "audit_panel": audit_panel,
        "approval_panel": approval_panel,
        "provider_runtime_panel": provider_runtime_panel,
        "operator_next_action_cards": operator_next_action_cards,
        "pulse_panel": pulse_panel,
        "runtime_startup_panel": runtime_startup_panel,
        "app_launcher_panel": app_launcher_panel,
        "panel_errors": errors,
        "boundary": _BOUNDARY,
    }
