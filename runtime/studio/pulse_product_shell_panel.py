"""Read-only Studio Pulse product-shell panel contract.

This module describes how the verified static Pulse product shell can be
mounted by the Studio shell as a read-only panel. It does not start a server,
open a browser, submit feedback, execute approvals, apply candidates, dispatch
runtimes, activate schedules, call providers/connectors, or mutate canonical
state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.pulse.product_shell import build_pulse_product_shell
from runtime.pulse.product_shell_browser_qa import (
    NEXT_PULSE_PRODUCT_SHELL_PASS_AFTER_BROWSER_QA,
    NEXT_PULSE_PRODUCT_SHELL_PASS_AFTER_PANEL_CONTRACT,
    PRODUCT_SHELL_ROOT,
    latest_pulse_product_shell_artifact,
    latest_pulse_product_shell_browser_qa_note,
    latest_pulse_product_shell_browser_qa_screenshot,
    pulse_product_shell_browser_qa_evidence_built,
    pulse_product_shell_studio_mount_built,
)


MODEL_VERSION = "studio.pulse_product_shell_panel.v1"
SURFACE_ID = "studio_pulse_product_shell_panel_contract"
PANEL_ID = "studio.pulse.product_shell.panel"


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


def _refresh_command(deck_path: str | Path | None) -> str:
    parts = ["chaseos", "pulse", "product-shell"]
    if deck_path is not None:
        parts.extend(["--deck-path", str(deck_path)])
    parts.extend(["--write", "--json"])
    return " ".join(parts)


def build_pulse_product_shell_panel_contract(
    vault_root: str | Path,
    *,
    deck_path: str | Path | None = None,
) -> dict[str, Any]:
    """Return a read-only Studio mount contract for the Pulse product shell."""

    vault = _vault_path(vault_root)
    artifact_path = latest_pulse_product_shell_artifact(vault)
    qa_note_path = latest_pulse_product_shell_browser_qa_note(vault)
    screenshot_path = latest_pulse_product_shell_browser_qa_screenshot(vault)
    browser_qa_ready = pulse_product_shell_browser_qa_evidence_built(vault)
    studio_mount_ready = pulse_product_shell_studio_mount_built(vault)
    blockers: list[str] = []
    warnings: list[str] = []

    try:
        shell_model = build_pulse_product_shell(vault, deck_path=deck_path)
        shell_summary = shell_model.get("summary") or {}
        source_deck_path = shell_model.get("source_deck_path")
        shell_ok = bool(shell_model.get("ok"))
    except Exception as exc:  # pragma: no cover - defensive, surfaced in model
        shell_model = {"ok": False, "error": str(exc)}
        shell_summary = {}
        source_deck_path = None
        shell_ok = False
        blockers.append("pulse-product-shell-model-not-ready")

    if artifact_path is None:
        blockers.append("pulse-product-shell-artifact-not-found")
    if not browser_qa_ready:
        blockers.append("pulse-product-shell-browser-qa-evidence-not-found")
    if screenshot_path is None:
        warnings.append("pulse-product-shell-browser-qa-screenshot-not-found")

    panel_ready = shell_ok and artifact_path is not None and browser_qa_ready
    next_pass = (
        "chaseos-pulse-interactive-governed-controls"
        if studio_mount_ready
        else NEXT_PULSE_PRODUCT_SHELL_PASS_AFTER_PANEL_CONTRACT
        if panel_ready
        else NEXT_PULSE_PRODUCT_SHELL_PASS_AFTER_BROWSER_QA
    )

    return {
        "ok": panel_ready,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "title": "ChaseOS Studio Pulse Product Shell Panel Contract",
        "phase": "Phase 10 - ChaseOS Pulse / Studio product surface",
        "status": (
            (
                "PARTIAL / PULSE PRODUCT SHELL PANEL CONTRACT BUILT / READ-ONLY STUDIO MOUNT BUILT"
                if studio_mount_ready
                else "PARTIAL / PULSE PRODUCT SHELL PANEL CONTRACT BUILT / STUDIO MOUNT NOT BUILT"
            )
            if panel_ready
            else "BLOCKED / PULSE PRODUCT SHELL PANEL CONTRACT BUILT / STATIC PULSE EVIDENCE INCOMPLETE"
        ),
        "vault_root": str(vault),
        "panel": {
            "panel_id": PANEL_ID,
            "label": "Pulse",
            "surface_route": "#pulse",
            "mount_target": "desktop-shell-app:workspace-main-panel",
            "panel_mode": "read-only-static-pulse-product-shell-panel",
            "embedding_strategy": "local-file-iframe-or-webview",
            "source_artifact_path": _relative_to_vault(vault, artifact_path),
            "source_artifact_uri": _file_uri(artifact_path),
            "source_artifact_exists": artifact_path is not None,
            "browser_qa_evidence_path": _relative_to_vault(vault, qa_note_path),
            "browser_qa_screenshot_path": _relative_to_vault(vault, screenshot_path),
            "required_artifact_root": PRODUCT_SHELL_ROOT.as_posix(),
            "artifact_refresh_command": _refresh_command(deck_path),
            "artifact_refresh_requires_explicit_operator_action": True,
        },
        "summary": {
            "source_deck_path": source_deck_path,
            "panel_count": shell_summary.get("panel_count", 0),
            "card_count": shell_summary.get("card_count", 0),
            "surface_status_count": shell_summary.get("surface_status_count", 0),
            "approval_lane_count": shell_summary.get("approval_lane_count"),
            "runtime_card_count": shell_summary.get("runtime_card_count"),
            "personal_map_candidate_count": shell_summary.get("personal_map_candidate_count"),
            "personal_map_apply_preview_count": shell_summary.get("personal_map_apply_preview_count"),
            "current_v1_local_lane_complete": shell_summary.get("current_v1_local_lane_complete"),
            "full_product_grade_complete": shell_summary.get("full_product_grade_complete"),
            "warning_count": len(warnings),
            "blocker_count": len(blockers),
        },
        "source_product_shell": {
            "surface": shell_model.get("surface"),
            "ok": shell_model.get("ok"),
            "authority": shell_model.get("authority", {}),
            "writes": shell_model.get("writes", []),
        },
        "readiness": {
            "pulse_product_shell_panel_contract_ready": panel_ready,
            "pulse_product_shell_model_ready": shell_ok,
            "static_product_shell_artifact_ready": artifact_path is not None,
            "static_product_shell_browser_qa_ready": browser_qa_ready,
            "desktop_shell_mount_ready": studio_mount_ready,
            "interactive_pulse_controls_ready": False,
            "approval_execution_ui_ready": False,
            "candidate_apply_ui_ready": False,
            "schedule_activation_ui_ready": False,
            "blockers": blockers,
            "warnings": warnings,
            "next_recommended_pass": next_pass,
        },
        "pulse_product_shell_truth": {
            "pulse_product_shell_built": shell_ok,
            "pulse_product_shell_static_artifact_built": artifact_path is not None,
            "pulse_product_shell_browser_qa_built": browser_qa_ready,
            "pulse_product_shell_panel_contract_built": True,
            "pulse_product_shell_mounted_in_studio": studio_mount_ready,
            "interactive_pulse_feedback_controls_built": False,
            "interactive_approval_execution_built": False,
            "personal_map_live_apply_ui_built": False,
            "runtime_brain_interactive_ui_built": False,
            "schedule_activation_ui_built": False,
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
            "writes_settings": False,
            "submits_feedback": False,
            "executes_approvals": False,
            "applies_candidates": False,
            "updates_personal_map": False,
            "updates_runtime_brains": False,
            "writes_agent_bus_tasks": False,
            "dispatches_runtimes": False,
            "activates_schedules": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "canonical_mutation_allowed": False,
            "rd_workbook_update_allowed": False,
        },
        "possible_writes": [],
        "allowed_actions": ["inspect-pulse-product-shell-panel-contract"],
        "docs": [
            "06_AGENTS/ChaseOS-Pulse-Product-Shell-Integration.md",
            "06_AGENTS/ChaseOS-Pulse-Product-Shell-Browser-QA-and-Studio-Mount-Contract.md",
            "06_AGENTS/ChaseOS-Pulse-Studio-Product-Shell-Mount.md",
            "06_AGENTS/ChaseOS-Studio-Architecture.md",
        ],
    }
