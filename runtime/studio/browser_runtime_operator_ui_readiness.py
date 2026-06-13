"""Read-only Studio Browser Runtime operator UI readiness contract.

This module defines the future Studio/operator surface for Browser Runtime
Adapter + Site Skill Memory without building or launching the UI. It composes
the existing Browser Runtime completion status and estimate reporters, then
returns panel contracts that Studio can later render.

It does not launch browsers, connect CDP, invoke MCP, probe URLs, write
artifacts, activate skills, call providers, enqueue Agent Bus tasks, mutate Gate
policy, or write canonical ChaseOS state.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.browser_runtime.completion_estimate import (
    BrowserRuntimeCompletionEstimate,
    build_browser_runtime_completion_estimate,
)
from runtime.browser_runtime.completion_status import (
    BrowserRuntimeCompletionStatus,
    build_browser_runtime_completion_status,
)


MODEL_VERSION = "studio.browser_runtime_operator_ui_readiness.v1"
SURFACE_ID = "studio_browser_runtime_operator_ui_readiness_contract"
PANEL_GROUP_ID = "studio.browser_runtime.operator"

FORBIDDEN_EFFECTS = (
    "dependency_install",
    "server_start",
    "network_probe",
    "browser_launch",
    "cdp_connection",
    "mcp_invocation",
    "target_navigation",
    "screenshot_capture",
    "browser_run_log_write",
    "agent_activity_log_write",
    "draft_skill_write",
    "trusted_skill_write",
    "skill_activation",
    "real_profile_access",
    "credential_or_cookie_read",
    "browser_harness_use",
    "browser_use_cli_live_run",
    "agent_bus_enqueue",
    "provider_call",
    "gate_mutation",
    "canonical_writeback",
)

_REQUIRED_PANEL_IDS = (
    "browser-runtime-completion-summary",
    "browser-runtime-remaining-passes",
    "browser-runtime-external-dependencies",
    "browser-runtime-excalidraw-chain",
    "browser-runtime-provider-validation",
    "browser-runtime-site-skill-memory",
    "browser-runtime-approval-queue",
    "browser-runtime-run-evidence",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_exists(vault: Path, relative_path: str) -> bool:
    return (vault / relative_path).exists()


def _panel(
    panel_id: str,
    label: str,
    purpose: str,
    source: str,
    *,
    ready: bool = True,
    future_actions: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "panel_id": panel_id,
        "label": label,
        "purpose": purpose,
        "source": source,
        "ready_for_studio_mount": ready,
        "render_mode": "read-only-data-contract",
        "future_actions": list(future_actions),
    }


def _panels() -> list[dict[str, Any]]:
    return [
        _panel(
            "browser-runtime-completion-summary",
            "Completion",
            "Show bounded MVP state, production state, blocked reason count, and next recommended pass.",
            "runtime.browser_runtime.completion_status",
        ),
        _panel(
            "browser-runtime-remaining-passes",
            "Remaining Passes",
            "Show the current estimated major pass groups and critical path.",
            "runtime.browser_runtime.completion_estimate",
        ),
        _panel(
            "browser-runtime-external-dependencies",
            "External Dependencies",
            "Separate external-runtime blockers from internal ChaseOS implementation blockers.",
            "runtime.browser_runtime.completion_estimate.external_dependencies",
        ),
        _panel(
            "browser-runtime-excalidraw-chain",
            "Excalidraw Chain",
            "Show target-response, readiness, approval, proof-shell, and live-proof state.",
            "runtime.browser_runtime.excalidraw_live_chain_readiness",
            future_actions=("accept-local-loopback-target-response", "run-approved-live-proof"),
        ),
        _panel(
            "browser-runtime-provider-validation",
            "Provider Validation",
            "Show Browser Use CLI availability and no-account validation state.",
            "runtime.browser_runtime.browser_use_cli_validation",
            future_actions=("install-browser-use-cli-outside-chaseos", "run-throwaway-profile-validation"),
        ),
        _panel(
            "browser-runtime-site-skill-memory",
            "Site Skills",
            "Show draft site-skill candidates, review status, and non-active skill memory.",
            "06_AGENTS/Browser-Skills/_drafts",
            future_actions=("review-skill-candidate", "promote-through-gate"),
        ),
        _panel(
            "browser-runtime-approval-queue",
            "Approvals",
            "Show pending Browser Runtime approvals without granting or executing them.",
            "future-studio-approval-queue",
            ready=False,
            future_actions=("build-browser-runtime-approval-ui",),
        ),
        _panel(
            "browser-runtime-run-evidence",
            "Run Evidence",
            "Show Browser Run logs, screenshots, Agent Activity links, and proof artifacts.",
            "07_LOGS/Browser-Runs",
        ),
    ]


def _current_evidence(vault: Path) -> dict[str, Any]:
    evidence_paths = {
        "browser_run_logs_root": "07_LOGS/Browser-Runs",
        "agent_activity_root": "07_LOGS/Agent-Activity",
        "draft_skills_root": "06_AGENTS/Browser-Skills/_drafts",
        "completion_status_doc": "06_AGENTS/Browser-Runtime-Completion-Status.md",
        "completion_estimate_doc": "06_AGENTS/Browser-Runtime-Completion-Estimate.md",
        "excalidraw_chain_doc": "06_AGENTS/Excalidraw-Live-Chain-Readiness.md",
    }
    return {
        key: {
            "path": value,
            "exists": _relative_exists(vault, value),
        }
        for key, value in evidence_paths.items()
    }


def build_studio_browser_runtime_operator_ui_readiness(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    completion_status: BrowserRuntimeCompletionStatus | None = None,
    completion_estimate: BrowserRuntimeCompletionEstimate | None = None,
) -> dict[str, Any]:
    """Return the no-execution readiness contract for the future Studio panel."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    status = completion_status or build_browser_runtime_completion_status(vault, generated_at=timestamp)
    estimate = completion_estimate or build_browser_runtime_completion_estimate(
        vault,
        generated_at=timestamp,
        completion_status=status,
    )
    status_payload = status.to_dict()
    estimate_payload = estimate.to_dict()
    panels = _panels()
    panel_ids = [panel["panel_id"] for panel in panels]
    missing_panel_ids = [panel_id for panel_id in _REQUIRED_PANEL_IDS if panel_id not in panel_ids]
    native_panel_built = "studio_operator_ui_not_built" not in status_payload["blocked_reasons"]
    ui_blockers = [] if native_panel_built else ["studio_operator_ui_not_built"]
    readiness_contract_ready = not missing_panel_ids
    production_complete = (
        status_payload["production_feature_done"]
        and not status_payload["blocked_reasons"]
        and estimate_payload["total_remaining_major_passes_min"] == 0
        and estimate_payload["total_remaining_major_passes_max"] == 0
    )
    next_readiness_pass = (
        status_payload["next_recommended_pass"]
        if production_complete
        else "external-browser-use-cli-or-excalidraw-target-readiness"
        if native_panel_built
        else "studio-browser-runtime-operator-ui-implementation"
    )

    return {
        "ok": readiness_contract_ready,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": timestamp,
        "title": "ChaseOS Studio Browser Runtime Operator UI Readiness",
        "phase": "Phase 9 Browser Runtime Adapter / Phase 10 Studio operator surface",
        "status": (
            "COMPLETE TARGETED / READ-ONLY NATIVE PANEL BUILT"
            if readiness_contract_ready and native_panel_built
            else "PARTIAL / READ-ONLY OPERATOR UI READINESS CONTRACT BUILT / FULL UI NOT BUILT"
            if readiness_contract_ready
            else "BLOCKED / OPERATOR UI READINESS CONTRACT INCOMPLETE"
        ),
        "vault_root": str(vault),
        "panel_group": {
            "panel_group_id": PANEL_GROUP_ID,
            "label": "Browser Runtime",
            "surface_route": "#browser-runtime",
            "mount_target": "future-studio-operator-workspace",
            "panel_count": len(panels),
            "required_panel_ids": list(_REQUIRED_PANEL_IDS),
            "missing_panel_ids": missing_panel_ids,
        },
        "summary": {
            "overall_status": status_payload["overall_status"],
            "bounded_mvp_done": status_payload["bounded_mvp_done"],
            "production_feature_done": status_payload["production_feature_done"],
            "next_recommended_pass": status_payload["next_recommended_pass"],
            "blocker_count": len(status_payload["blocked_reasons"]),
            "item_count": status_payload["item_count"],
            "remaining_major_passes_min": estimate_payload["total_remaining_major_passes_min"],
            "remaining_major_passes_max": estimate_payload["total_remaining_major_passes_max"],
        },
        "panels": panels,
        "remaining_passes": estimate_payload["remaining_passes"],
        "external_dependencies": estimate_payload["external_dependencies"],
        "blocked_reasons": status_payload["blocked_reasons"],
        "current_evidence": _current_evidence(vault),
        "readiness": {
            "operator_ui_readiness_contract_ready": readiness_contract_ready,
            "studio_operator_ui_built": native_panel_built,
            "native_read_only_panel_built": native_panel_built,
            "interactive_approval_ui_built": False,
            "browser_run_evidence_panel_built": native_panel_built,
            "site_skill_inspector_built": native_panel_built,
            "skill_promotion_ui_built": False,
            "live_browser_control_ui_built": False,
            "ui_blockers": ui_blockers,
            "next_recommended_pass": next_readiness_pass,
        },
        "authority": {
            "read_only": True,
            "local_only": True,
            "uses_existing_completion_reporters_only": True,
            "starts_servers": False,
            "opens_browser": False,
            "launches_browser": False,
            "connects_cdp": False,
            "invokes_mcp": False,
            "navigates_targets": False,
            "captures_screenshots": False,
            "writes_browser_run_logs": False,
            "writes_agent_activity_logs": False,
            "writes_draft_skills": False,
            "writes_trusted_skills": False,
            "activates_skills": False,
            "reads_real_profiles": False,
            "reads_credentials_or_cookies": False,
            "uses_browser_harness": False,
            "runs_browser_use_cli_live": False,
            "writes_agent_bus_tasks": False,
            "dispatches_runtimes": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "gate_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "possible_writes": [],
        "allowed_actions": ["inspect-browser-runtime-operator-ui-readiness"],
        "forbidden_effects": list(FORBIDDEN_EFFECTS),
        "docs": [
            "06_AGENTS/Browser-Runtime-Completion-Status.md",
            "06_AGENTS/Browser-Runtime-Completion-Estimate.md",
            "06_AGENTS/Studio-Browser-Runtime-Operator-UI-Readiness.md",
        ],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Report read-only Studio Browser Runtime operator UI readiness."
    )
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    model = build_studio_browser_runtime_operator_ui_readiness(args.vault_root)
    if args.json:
        print(json.dumps(model, indent=2))
    else:
        summary = model["summary"]
        print(f"status: {model['status']}")
        print(f"overall_status: {summary['overall_status']}")
        print(
            "remaining_major_passes: "
            f"{summary['remaining_major_passes_min']}-{summary['remaining_major_passes_max']}"
        )
        print(f"next_recommended_pass: {model['readiness']['next_recommended_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
