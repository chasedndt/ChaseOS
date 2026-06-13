"""Read-only Studio panel contract for ARSL route review.

This module exposes the existing Adaptive Runtime Surface Layer route-review
contract as a Studio panel. It does not execute routes, grant approvals, write
the routing ledger, dispatch runtimes, call providers, control browsers, expose
raw manifests, mutate Gate policy, or write canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.runtime_surfaces.review_contract import build_route_review_contract


MODEL_VERSION = "studio.arsl_route_review_panel.v1"
SURFACE_ID = "studio_arsl_route_review_panel_contract"
PANEL_ID = "studio.arsl.route_review.panel"
DEFAULT_CAPABILITY = "browser.click"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _source_command(capability: str | None, surface_id: str | None) -> str:
    parts = ["chaseos", "runtime", "surfaces", "route-review"]
    if capability:
        parts.extend(["--capability", capability])
    if surface_id:
        parts.extend(["--surface", surface_id])
    parts.append("--json")
    return " ".join(parts)


def build_arsl_route_review_panel_contract(
    vault_root: str | Path,
    *,
    capability: str | None = DEFAULT_CAPABILITY,
    surface_id: str | None = None,
) -> dict[str, Any]:
    """Return a read-only Studio panel contract over ARSL route review."""

    vault = _vault_path(vault_root)
    review = build_route_review_contract(
        vault,
        capability=capability,
        surface_id=surface_id,
    )
    summary = review.get("summary") or {}
    preview = review.get("route_preview") or {}
    operator_review = review.get("operator_review") or {}
    safety = review.get("safety") or {}
    authority_blockers = [
        key
        for key in [
            "execution_performed",
            "runtime_dispatch_performed",
            "route_proposal_committed",
            "ledger_written",
            "approval_granted",
            "gate_mutated",
            "provider_calls_performed",
            "browser_control_performed",
            "raw_manifest_exposed",
            "mcp_tools_exposed",
            "canonical_writeback_performed",
        ]
        if bool(safety.get(key))
    ]
    panel_ready = bool(review.get("ok")) and not authority_blockers

    return {
        "ok": panel_ready,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "title": "ChaseOS Studio ARSL Route Review Panel Contract",
        "phase": "Phase 10 - Studio / Adaptive Runtime Surface Layer",
        "status": (
            "PARTIAL / ARSL ROUTE REVIEW PANEL CONTRACT BUILT / READ-ONLY STUDIO MOUNT BUILT"
            if panel_ready
            else "BLOCKED / ARSL ROUTE REVIEW PANEL CONTRACT BUILT / ROUTE REVIEW SAFETY FLAGS FAILED"
        ),
        "vault_root": str(vault),
        "panel": {
            "panel_id": PANEL_ID,
            "label": "ARSL Route Review",
            "surface_route": "#arsl-route-review",
            "mount_target": "desktop-shell-app:workspace-main-panel",
            "panel_mode": "read-only-runtime-surface-route-review-panel",
            "source_command": _source_command(capability, surface_id),
            "source_contract": "runtime.runtime_surfaces.review_contract.build_route_review_contract",
            "default_capability": DEFAULT_CAPABILITY,
        },
        "summary": {
            "requested_capability": review.get("requested_capability"),
            "requested_surface_id": review.get("requested_surface_id"),
            "review_row_count": review.get("review_row_count", 0),
            "surface_count": summary.get("surface_count", 0),
            "capability_count": summary.get("capability_count", 0),
            "explicit_or_conditional_approval_rows": summary.get(
                "explicit_or_conditional_approval_rows",
                0,
            ),
            "gate_required_rows": summary.get("gate_required_rows", 0),
            "audit_required_rows": summary.get("audit_required_rows", 0),
            "preview_decision": preview.get("decision"),
            "selected_surface": preview.get("selected_surface"),
            "authority_layer": preview.get("authority_layer"),
            "approval_required": preview.get("approval_required"),
            "gate_required": preview.get("gate_required"),
            "audit_required": preview.get("audit_required"),
            "policy_decision_count": summary.get("policy_decision_count", {}),
            "risk_class_count": summary.get("risk_class_count", {}),
            "approval_required_count": summary.get("approval_required_count", {}),
            "blocked_authority_flag_count": len(authority_blockers),
        },
        "source_route_review": {
            "ok": review.get("ok"),
            "schema_version": review.get("schema_version"),
            "feature": review.get("feature"),
            "contract": review.get("contract"),
            "requested_capability": review.get("requested_capability"),
            "requested_surface_id": review.get("requested_surface_id"),
            "route_preview": preview,
            "review_rows": list(review.get("review_rows") or []),
            "summary": summary,
            "operator_review": operator_review,
            "safety": safety,
            "boundary": review.get("boundary"),
        },
        "readiness": {
            "arsl_route_review_panel_contract_ready": panel_ready,
            "route_review_contract_ready": bool(review.get("ok")),
            "desktop_shell_mount_ready": panel_ready,
            "can_compare_candidate_surfaces": bool(operator_review.get("can_compare_candidate_surfaces")),
            "can_show_policy_refs": bool(operator_review.get("can_show_policy_refs")),
            "route_execution_ui_ready": False,
            "approval_grant_ui_ready": False,
            "ledger_write_ui_ready": False,
            "mcp_apply_ui_ready": False,
            "provider_call_ui_ready": False,
            "browser_control_ui_ready": False,
            "blockers": authority_blockers,
            "warnings": [],
            "next_recommended_pass": "arsl-closeout-or-studio-browser-qa-if-visual-evidence-required",
        },
        "arsl_route_review_truth": {
            "runtime_surface_registry_built": True,
            "capability_policy_records_built": True,
            "route_review_contract_built": True,
            "route_review_cli_built": True,
            "arsl_route_review_panel_contract_built": True,
            "arsl_route_review_mounted_in_studio": panel_ready,
            "route_execution_built": False,
            "approval_execution_built": False,
            "ledger_write_ui_built": False,
            "mcp_apply_tools_built": False,
            "browser_control_from_studio_built": False,
            "provider_calls_from_studio_built": False,
        },
        "authority": {
            "read_only": True,
            "local_only": True,
            "starts_servers": False,
            "starts_child_apps": False,
            "opens_browser": False,
            "writes_vault": False,
            "writes_settings": False,
            "executes_routes": False,
            "commits_route_proposals": False,
            "writes_routing_ledger": False,
            "grants_approvals": False,
            "executes_approvals": False,
            "mutates_gate_policy": False,
            "dispatches_runtimes": False,
            "writes_agent_bus_tasks": False,
            "provider_calls_allowed": False,
            "browser_control_allowed": False,
            "mcp_tools_exposed": False,
            "raw_manifest_exposed": False,
            "credential_values_visible": False,
            "browser_profile_visible": False,
            "canonical_mutation_allowed": False,
        },
        "possible_writes": [],
        "allowed_actions": ["inspect-arsl-route-review-panel-contract"],
        "docs": [
            "06_AGENTS/Adaptive-Runtime-Surface-Layer.md",
            "06_AGENTS/ChaseOS-Studio-Architecture.md",
            "docs/features/adaptive-runtime-surface-layer-spec.md",
        ],
    }
