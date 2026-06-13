"""Read-only Studio panel contract for the Pulse Approval Queue.

This module exposes the existing Pulse Approval Queue static UI as a Studio
panel contract. It is inspection-only: it does not grant approvals, execute
approval decisions, apply candidates, enqueue Agent Bus work, dispatch runtimes,
activate schedules, call providers/connectors, or mutate canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.pulse.approval_queue_ui import (
    APPROVAL_QUEUE_ROOT,
    build_pulse_approval_queue_ui,
)


MODEL_VERSION = "studio.approval_queue_panel.v1"
SURFACE_ID = "studio_pulse_approval_queue_panel_contract"
PANEL_ID = "studio.pulse.approval_queue.panel"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _file_uri(path: Path | None) -> str | None:
    return path.resolve().as_uri() if path is not None else None


def latest_approval_queue_artifact(vault_root: str | Path) -> Path | None:
    """Return the newest written Pulse Approval Queue static HTML artifact."""

    vault = _vault_path(vault_root)
    root = vault / APPROVAL_QUEUE_ROOT
    artifacts = sorted(
        root.glob("*.html"),
        key=lambda path: (path.stat().st_mtime, path.name),
        reverse=True,
    )
    return artifacts[0] if artifacts else None


def _refresh_command(request_id: str | None, evidence_id: str | None) -> str:
    parts = ["chaseos", "pulse", "approval-queue-ui"]
    if request_id:
        parts.extend(["--request-id", request_id])
    if evidence_id:
        parts.extend(["--evidence-id", evidence_id])
    parts.extend(["--write", "--json"])
    return " ".join(parts)


def build_studio_approval_queue_panel_contract(
    vault_root: str | Path,
    *,
    request_id: str | None = None,
    evidence_id: str | None = None,
) -> dict[str, Any]:
    """Return a read-only Studio panel contract for the Pulse Approval Queue."""

    vault = _vault_path(vault_root)
    artifact_path = latest_approval_queue_artifact(vault)
    blockers: list[str] = []
    warnings: list[str] = []

    try:
        queue_model = build_pulse_approval_queue_ui(
            vault,
            request_id=request_id,
            evidence_id=evidence_id,
        )
        queue_summary = queue_model.get("summary") or {}
        queue_ok = bool(queue_model.get("ok"))
    except Exception as exc:  # pragma: no cover - defensive, surfaced in model
        queue_model = {"ok": False, "error": str(exc)}
        queue_summary = {}
        queue_ok = False
        blockers.append("approval-queue-model-not-ready")

    if artifact_path is None:
        blockers.append("approval-queue-static-artifact-not-found")
    elif artifact_path.stat().st_size == 0:
        warnings.append("approval-queue-static-artifact-empty")

    panel_ready = queue_ok and artifact_path is not None and not blockers

    return {
        "ok": panel_ready,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "title": "ChaseOS Studio Pulse Approval Queue Panel Contract",
        "phase": "Phase 10 - ChaseOS Pulse / Studio product surface",
        "status": (
            "PARTIAL / APPROVAL QUEUE PANEL CONTRACT BUILT / READ-ONLY STUDIO MOUNT BUILT"
            if panel_ready
            else "BLOCKED / APPROVAL QUEUE PANEL CONTRACT BUILT / STATIC APPROVAL QUEUE EVIDENCE INCOMPLETE"
        ),
        "vault_root": str(vault),
        "panel": {
            "panel_id": PANEL_ID,
            "label": "Approval Queue",
            "surface_route": "#approval-queue",
            "mount_target": "desktop-shell-app:workspace-main-panel",
            "panel_mode": "read-only-static-approval-queue-panel",
            "embedding_strategy": "local-file-iframe-or-webview",
            "source_artifact_path": _relative_to_vault(vault, artifact_path),
            "source_artifact_uri": _file_uri(artifact_path),
            "source_artifact_exists": artifact_path is not None,
            "required_artifact_root": APPROVAL_QUEUE_ROOT.as_posix(),
            "artifact_refresh_command": _refresh_command(request_id, evidence_id),
            "artifact_refresh_requires_explicit_operator_action": True,
        },
        "summary": {
            "approval_center_status": queue_summary.get("approval_center_status"),
            "lane_count": queue_summary.get("lane_count", 0),
            "action_count": queue_summary.get("action_count", 0),
            "candidate_row_count": queue_summary.get("candidate_row_count", 0),
            "approval_request_count": queue_summary.get("approval_request_count", 0),
            "missing_approval_key_count": queue_summary.get("missing_approval_key_count", 0),
            "warning_count": len(warnings),
            "blocker_count": len(blockers),
        },
        "source_approval_queue": {
            "surface": queue_model.get("surface"),
            "ok": queue_model.get("ok"),
            "authority": queue_model.get("authority", {}),
            "writes": queue_model.get("writes", []),
        },
        "readiness": {
            "approval_queue_panel_contract_ready": panel_ready,
            "approval_queue_model_ready": queue_ok,
            "static_approval_queue_artifact_ready": artifact_path is not None,
            "desktop_shell_mount_ready": panel_ready,
            "approval_execution_ui_ready": False,
            "candidate_apply_ui_ready": False,
            "memory_approval_ui_ready": False,
            "agent_bus_enqueue_ui_ready": False,
            "blockers": blockers,
            "warnings": warnings,
            "next_recommended_pass": "personal-map-live-apply-proof-and-interactive-ui",
        },
        "approval_queue_truth": {
            "approval_queue_static_ui_built": queue_ok,
            "approval_queue_static_artifact_built": artifact_path is not None,
            "approval_queue_panel_contract_built": True,
            "approval_queue_mounted_in_studio": panel_ready,
            "interactive_approval_execution_built": False,
            "candidate_apply_ui_built": False,
            "agent_bus_enqueue_ui_built": False,
            "canonical_writeback_ui_built": False,
        },
        "authority": {
            "read_only": True,
            "local_only": True,
            "requires_existing_static_artifact": True,
            "mounts_existing_artifact_only": True,
            "starts_servers": False,
            "starts_child_apps": False,
            "opens_browser": False,
            "writes_html": False,
            "writes_vault": False,
            "writes_review_decisions": False,
            "writes_feedback_candidates": False,
            "grants_approvals": False,
            "executes_approvals": False,
            "applies_candidates": False,
            "approves_memory": False,
            "writes_agent_bus_tasks": False,
            "dispatches_runtimes": False,
            "activates_schedules": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "canonical_mutation_allowed": False,
            "rd_workbook_update_allowed": False,
        },
        "possible_writes": [],
        "allowed_actions": ["inspect-approval-queue-panel-contract"],
        "docs": [
            "06_AGENTS/ChaseOS-Pulse-Approval-Queue-UI.md",
            "06_AGENTS/ChaseOS-Pulse-Approval-Queue-Studio-Panel-Mount.md",
            "06_AGENTS/ChaseOS-Studio-Architecture.md",
        ],
    }
