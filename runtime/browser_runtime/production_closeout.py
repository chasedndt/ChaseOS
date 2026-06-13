"""Read-only Browser Runtime production closeout report.

This module closes out the internal Studio Browser Runtime lane by composing
repo-local completion status, completion estimate, and native panel evidence.
It does not launch browsers, invoke Browser Use CLI, call Excalidraw/MCP,
grant approvals, activate skills, enqueue Agent Bus tasks, call providers, or
mutate canonical ChaseOS state.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
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
from runtime.studio.browser_runtime_operator_ui_readiness import (
    build_studio_browser_runtime_operator_ui_readiness,
)


BROWSER_RUNTIME_PRODUCTION_CLOSEOUT_RECORD_TYPE = "browser_runtime_production_closeout"
BROWSER_RUNTIME_PRODUCTION_CLOSEOUT_VERSION = "browser.production_closeout.v1"
BROWSER_RUNTIME_PRODUCTION_CLOSEOUT_STATUS_COMPLETE = "browser_runtime_production_complete"
BROWSER_RUNTIME_PRODUCTION_CLOSEOUT_STATUS_EXTERNAL_DEFERRED = (
    "browser_runtime_internal_studio_closeout_complete_external_deferred"
)
BROWSER_RUNTIME_PRODUCTION_CLOSEOUT_STATUS = BROWSER_RUNTIME_PRODUCTION_CLOSEOUT_STATUS_COMPLETE
BROWSER_RUNTIME_PRODUCTION_CLOSEOUT_STATUSES = {
    BROWSER_RUNTIME_PRODUCTION_CLOSEOUT_STATUS_COMPLETE,
    BROWSER_RUNTIME_PRODUCTION_CLOSEOUT_STATUS_EXTERNAL_DEFERRED,
}
DEFAULT_EVIDENCE_ROOT = Path("07_LOGS/Studio-Graph-Views")

NATIVE_PANEL_EVIDENCE_PATHS = (
    "07_LOGS/Studio-Graph-Views/2026-05-04-studio-browser-runtime-native-shell-panel-static-qa.md",
    "07_LOGS/Studio-Graph-Views/2026-05-04-studio-browser-runtime-panel-qa-runner-static-qa.md",
    "07_LOGS/Studio-Graph-Views/2026-05-04-studio-browser-runtime-panel-browser-qa.md",
)

FORBIDDEN_EFFECTS = (
    "dependency_install",
    "server_start",
    "network_probe",
    "browser_launch",
    "cdp_connection",
    "mcp_invocation",
    "target_navigation",
    "screenshot_capture",
    "browser_use_cli_live_run",
    "excalidraw_live_proof",
    "approval_grant",
    "approval_execution",
    "trusted_skill_write",
    "skill_activation",
    "real_profile_access",
    "credential_or_cookie_read",
    "agent_bus_enqueue",
    "provider_call",
    "connector_call",
    "gate_mutation",
    "canonical_writeback",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _evidence_status(vault: Path) -> tuple[dict[str, Any], ...]:
    records = []
    for relative_path in NATIVE_PANEL_EVIDENCE_PATHS:
        path = vault / relative_path
        records.append(
            {
                "path": relative_path,
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else 0,
            }
        )
    return tuple(records)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _markdown(report: "BrowserRuntimeProductionCloseout") -> str:
    payload = report.to_dict()
    lines = [
        "# Browser Runtime Production Closeout",
        "",
        f"- Generated: {payload['generated_at']}",
        f"- Status: {payload['status']}",
        f"- Bounded MVP done: {payload['bounded_mvp_done']}",
        f"- Production feature done: {payload['production_feature_done']}",
        f"- Internal Studio panel lane complete: {payload['internal_studio_panel_lane_complete']}",
        f"- Remaining major passes: {payload['remaining_major_passes_min']}-{payload['remaining_major_passes_max']}",
        f"- Next recommended pass: {payload['next_recommended_pass']}",
        "",
        "## Deferred External Lanes",
    ]
    for lane in payload["external_deferred_lanes"]:
        lines.append(f"- {lane}")
    if not payload["external_deferred_lanes"]:
        lines.append("- None")
    lines.extend(["", "## Remaining Internal Passes"])
    for lane in payload["remaining_internal_passes"]:
        lines.append(f"- {lane}")
    if not payload["remaining_internal_passes"]:
        lines.append("- None")
    lines.extend(["", "## Native Panel Evidence"])
    for record in payload["native_panel_evidence"]:
        lines.append(
            f"- {record['path']} | exists={record['exists']} | size={record['size_bytes']}"
        )
    lines.extend(
        [
            "",
            "## Boundaries",
            "- This closeout command performs no Browser Use CLI run, Excalidraw action, browser launch, target navigation, screenshot capture, MCP invocation, approval execution, skill activation, provider/connector call, Agent Bus write, Gate mutation, or canonical writeback.",
            "- Existing Browser Use safe-URL and public Excalidraw drawing evidence is read as repo-local proof only.",
            "- No real browser profile, credential, cookie, account state, provider, connector, Agent Bus, Gate, approval execution, skill activation, or canonical writeback authority is granted.",
            "",
        ]
    )
    return "\n".join(lines)


def write_production_closeout_evidence(
    vault_root: str | Path,
    report: "BrowserRuntimeProductionCloseout",
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = Path(evidence_root) if evidence_root is not None else DEFAULT_EVIDENCE_ROOT
    if root.is_absolute():
        raise ValueError("evidence root must be vault-relative")
    slug = evidence_slug or datetime.now(timezone.utc).strftime(
        "%Y-%m-%d-browser-runtime-production-closeout"
    )
    base = vault / root / slug
    json_path = base.with_suffix(".json")
    md_path = base.with_suffix(".md")
    _write_json(json_path, report.to_dict())
    md_path.write_text(_markdown(report), encoding="utf-8")
    return {
        "written": True,
        "json_path": str(json_path),
        "markdown_path": str(md_path),
    }


@dataclass(frozen=True)
class BrowserRuntimeProductionCloseout:
    record_type: str
    schema_version: str
    generated_at: str
    status: str
    vault_root: str
    bounded_mvp_done: bool
    production_feature_done: bool
    internal_studio_panel_lane_complete: bool
    external_runtime_lanes_deferred: bool
    blocker_count: int
    remaining_major_passes_min: int
    remaining_major_passes_max: int
    next_recommended_pass: str
    remaining_internal_passes: tuple[str, ...]
    external_deferred_lanes: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    native_panel_evidence: tuple[dict[str, Any], ...]
    completion_status: dict[str, Any]
    completion_estimate: dict[str, Any]
    studio_panel_readiness: dict[str, Any]
    read_only: bool = True
    writes_evidence: bool = False
    dependency_install_attempted: bool = False
    server_start_attempted: bool = False
    network_probe_attempted: bool = False
    browser_launch_attempted: bool = False
    cdp_connection_attempted: bool = False
    mcp_invocation_attempted: bool = False
    target_navigation_attempted: bool = False
    screenshot_capture_attempted: bool = False
    browser_use_cli_live_used: bool = False
    excalidraw_live_proof_attempted: bool = False
    approval_grant_attempted: bool = False
    approval_execution_attempted: bool = False
    trusted_skill_write_attempted: bool = False
    skill_activation_attempted: bool = False
    real_profile_access_attempted: bool = False
    credential_or_cookie_read_attempted: bool = False
    agent_bus_enqueue_attempted: bool = False
    provider_call_attempted: bool = False
    connector_call_attempted: bool = False
    gate_mutation_attempted: bool = False
    canonical_writeback_attempted: bool = False
    forbidden_effects: tuple[str, ...] = FORBIDDEN_EFFECTS

    def validate(self) -> None:
        if self.record_type != BROWSER_RUNTIME_PRODUCTION_CLOSEOUT_RECORD_TYPE:
            raise ValueError("invalid Browser Runtime production closeout record type")
        if self.schema_version != BROWSER_RUNTIME_PRODUCTION_CLOSEOUT_VERSION:
            raise ValueError("invalid Browser Runtime production closeout schema version")
        if self.status not in BROWSER_RUNTIME_PRODUCTION_CLOSEOUT_STATUSES:
            raise ValueError("invalid Browser Runtime production closeout status")
        if self.status == BROWSER_RUNTIME_PRODUCTION_CLOSEOUT_STATUS_COMPLETE:
            if not self.production_feature_done:
                raise ValueError("production-complete closeout requires production_feature_done")
            if self.blocker_count != 0 or self.blocked_reasons:
                raise ValueError("production-complete closeout cannot include blockers")
            if self.external_runtime_lanes_deferred or self.external_deferred_lanes:
                raise ValueError("production-complete closeout cannot include external deferrals")
            if self.remaining_internal_passes:
                raise ValueError("production-complete closeout cannot include internal remaining passes")
            if self.remaining_major_passes_min != 0 or self.remaining_major_passes_max != 0:
                raise ValueError("production-complete closeout requires zero remaining major passes")
        elif self.production_feature_done:
            raise ValueError("production_feature_done closeout must use production-complete status")
        if not self.read_only:
            raise ValueError("production closeout must remain read-only")
        forbidden_flags = (
            self.dependency_install_attempted,
            self.server_start_attempted,
            self.network_probe_attempted,
            self.browser_launch_attempted,
            self.cdp_connection_attempted,
            self.mcp_invocation_attempted,
            self.target_navigation_attempted,
            self.screenshot_capture_attempted,
            self.browser_use_cli_live_used,
            self.excalidraw_live_proof_attempted,
            self.approval_grant_attempted,
            self.approval_execution_attempted,
            self.trusted_skill_write_attempted,
            self.skill_activation_attempted,
            self.real_profile_access_attempted,
            self.credential_or_cookie_read_attempted,
            self.agent_bus_enqueue_attempted,
            self.provider_call_attempted,
            self.connector_call_attempted,
            self.gate_mutation_attempted,
            self.canonical_writeback_attempted,
        )
        if any(forbidden_flags):
            raise ValueError("Browser Runtime production closeout attempted a forbidden effect")
        if not self.internal_studio_panel_lane_complete:
            raise ValueError("production closeout requires completed internal Studio panel evidence")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["remaining_internal_passes"] = list(self.remaining_internal_passes)
        payload["external_deferred_lanes"] = list(self.external_deferred_lanes)
        payload["blocked_reasons"] = list(self.blocked_reasons)
        payload["native_panel_evidence"] = list(self.native_panel_evidence)
        payload["forbidden_effects"] = list(self.forbidden_effects)
        return payload


def build_browser_runtime_production_closeout(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    completion_status: BrowserRuntimeCompletionStatus | None = None,
    completion_estimate: BrowserRuntimeCompletionEstimate | None = None,
) -> BrowserRuntimeProductionCloseout:
    """Build the closeout report from repo-local evidence only."""

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
    studio_readiness = build_studio_browser_runtime_operator_ui_readiness(
        vault,
        generated_at=timestamp,
        completion_status=status,
        completion_estimate=estimate,
    )
    evidence = _evidence_status(vault)
    internal_panel_complete = (
        "studio_operator_ui_not_built" not in status.blocked_reasons
        and all(record["exists"] and record["size_bytes"] > 0 for record in evidence)
        and studio_readiness["readiness"]["native_read_only_panel_built"] is True
    )
    remaining_internal = tuple(
        item["pass_id"]
        for item in estimate_payload["remaining_passes"]
        if not item["external_dependency"]
    )
    external_lanes = tuple(estimate_payload["external_dependencies"])
    closeout_status = (
        BROWSER_RUNTIME_PRODUCTION_CLOSEOUT_STATUS_COMPLETE
        if (
            status.production_feature_done
            and len(status.blocked_reasons) == 0
            and estimate.total_remaining_major_passes_min == 0
            and estimate.total_remaining_major_passes_max == 0
            and not remaining_internal
            and not external_lanes
        )
        else BROWSER_RUNTIME_PRODUCTION_CLOSEOUT_STATUS_EXTERNAL_DEFERRED
    )
    report = BrowserRuntimeProductionCloseout(
        record_type=BROWSER_RUNTIME_PRODUCTION_CLOSEOUT_RECORD_TYPE,
        schema_version=BROWSER_RUNTIME_PRODUCTION_CLOSEOUT_VERSION,
        generated_at=timestamp,
        status=closeout_status,
        vault_root=str(vault),
        bounded_mvp_done=status.bounded_mvp_done,
        production_feature_done=status.production_feature_done,
        internal_studio_panel_lane_complete=internal_panel_complete,
        external_runtime_lanes_deferred=bool(external_lanes),
        blocker_count=len(status.blocked_reasons),
        remaining_major_passes_min=estimate.total_remaining_major_passes_min,
        remaining_major_passes_max=estimate.total_remaining_major_passes_max,
        next_recommended_pass=status.next_recommended_pass,
        remaining_internal_passes=remaining_internal,
        external_deferred_lanes=external_lanes,
        blocked_reasons=status.blocked_reasons,
        native_panel_evidence=evidence,
        completion_status=status_payload,
        completion_estimate=estimate_payload,
        studio_panel_readiness=studio_readiness,
    )
    report.validate()
    return report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write/read Browser Runtime production closeout evidence without external runtime effects."
    )
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument(
        "--write-evidence",
        action="store_true",
        help="Write JSON and Markdown closeout evidence under the Studio QA evidence root.",
    )
    parser.add_argument("--evidence-slug", default=None, metavar="SLUG")
    parser.add_argument(
        "--evidence-root",
        default=None,
        metavar="PATH",
        help="Vault-relative evidence root; defaults to 07_LOGS/Studio-Graph-Views",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    report = build_browser_runtime_production_closeout(args.vault_root)
    payload = report.to_dict()
    if args.write_evidence:
        payload["evidence_write"] = write_production_closeout_evidence(
            args.vault_root,
            report,
            evidence_slug=args.evidence_slug,
            evidence_root=args.evidence_root,
        )
        payload["writes_evidence"] = True
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {payload['status']}")
        print(f"internal_studio_panel_lane_complete: {payload['internal_studio_panel_lane_complete']}")
        print(
            "remaining_major_passes: "
            f"{payload['remaining_major_passes_min']}-{payload['remaining_major_passes_max']}"
        )
        print(f"next_recommended_pass: {payload['next_recommended_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
