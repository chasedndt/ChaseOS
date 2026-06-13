"""Read-only Browser Runtime completion estimate.

This module turns the Browser Runtime completion status into an estimated
remaining-pass plan. It is a reporting surface only: it does not launch
browsers, connect CDP, invoke MCP, write artifacts, install dependencies,
promote skills, enqueue Agent Bus tasks, mutate Gate policy, or write canonical
state.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.browser_runtime.completion_status import (
    BrowserRuntimeCompletionStatus,
    build_browser_runtime_completion_status,
)


BROWSER_RUNTIME_COMPLETION_ESTIMATE_RECORD_TYPE = "browser_runtime_completion_estimate"
BROWSER_RUNTIME_COMPLETION_ESTIMATE_VERSION = "browser.completion_estimate.v1"
BROWSER_RUNTIME_COMPLETION_ESTIMATE_COMPLETE = "browser_runtime_completion_estimate_complete"
BROWSER_RUNTIME_COMPLETION_ESTIMATE_BLOCKED = "browser_runtime_completion_estimate_production_blocked"

BLOCKED_EFFECTS = (
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

STUDIO_BROWSER_RUNTIME_OPERATOR_UI_READINESS_PATHS = (
    "runtime/studio/browser_runtime_operator_ui_readiness.py",
    "runtime/studio/test_browser_runtime_operator_ui_readiness.py",
    "06_AGENTS/Studio-Browser-Runtime-Operator-UI-Readiness.md",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _all_exist(vault: Path, relative_paths: tuple[str, ...]) -> bool:
    return all((vault / path).exists() for path in relative_paths)


def _studio_browser_runtime_operator_ui_readiness_ok(vault: Path) -> bool:
    return _all_exist(vault, STUDIO_BROWSER_RUNTIME_OPERATOR_UI_READINESS_PATHS)


@dataclass(frozen=True)
class BrowserRuntimeRemainingPass:
    pass_id: str
    category: str
    status: str
    blocker_reasons: tuple[str, ...]
    min_major_passes: int
    max_major_passes: int
    next_gate: str
    external_dependency: bool = False
    notes: str = ""

    def validate(self) -> None:
        if not self.pass_id:
            raise ValueError("remaining pass id is required")
        if self.status not in {
            "blocked_external_dependency",
            "blocked_unavailable",
            "not_built",
            "ready_for_next_pass",
            "planned_phase10",
        }:
            raise ValueError("invalid remaining pass status")
        if self.min_major_passes < 0 or self.max_major_passes < self.min_major_passes:
            raise ValueError("invalid remaining pass estimate range")
        if not self.next_gate:
            raise ValueError("remaining pass next gate is required")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["blocker_reasons"] = list(self.blocker_reasons)
        return payload


@dataclass(frozen=True)
class BrowserRuntimeCompletionEstimate:
    record_type: str
    schema_version: str
    generated_at: str
    status: str
    overall_status: str
    bounded_mvp_done: bool
    production_feature_done: bool
    source_next_recommended_pass: str
    blocker_count: int
    item_count: int
    total_remaining_major_passes_min: int
    total_remaining_major_passes_max: int
    remaining_passes: tuple[BrowserRuntimeRemainingPass, ...]
    critical_path: tuple[str, ...]
    external_dependencies: tuple[str, ...] = ()
    estimate_assumptions: tuple[str, ...] = field(default_factory=tuple)
    read_only: bool = True
    writes_estimate_artifact: bool = False
    dependency_install_attempted: bool = False
    server_start_attempted: bool = False
    network_probe_attempted: bool = False
    browser_launch_attempted: bool = False
    cdp_connection_attempted: bool = False
    mcp_invocation_attempted: bool = False
    target_navigation_attempted: bool = False
    screenshot_capture_attempted: bool = False
    browser_run_log_written: bool = False
    agent_activity_log_written: bool = False
    draft_skill_written: bool = False
    trusted_skill_write_attempted: bool = False
    skill_activation_attempted: bool = False
    real_profile_access_attempted: bool = False
    credential_or_cookie_read_attempted: bool = False
    browser_harness_used: bool = False
    browser_use_cli_live_used: bool = False
    agent_bus_enqueue_attempted: bool = False
    provider_call_attempted: bool = False
    gate_mutation_attempted: bool = False
    canonical_writeback_attempted: bool = False
    blocked_effects: tuple[str, ...] = BLOCKED_EFFECTS

    def validate(self) -> None:
        if self.record_type != BROWSER_RUNTIME_COMPLETION_ESTIMATE_RECORD_TYPE:
            raise ValueError("invalid Browser Runtime completion estimate record type")
        if self.schema_version != BROWSER_RUNTIME_COMPLETION_ESTIMATE_VERSION:
            raise ValueError("invalid Browser Runtime completion estimate schema version")
        if self.status not in {
            BROWSER_RUNTIME_COMPLETION_ESTIMATE_COMPLETE,
            BROWSER_RUNTIME_COMPLETION_ESTIMATE_BLOCKED,
        }:
            raise ValueError("invalid Browser Runtime completion estimate status")
        for item in self.remaining_passes:
            item.validate()
        expected_min = sum(item.min_major_passes for item in self.remaining_passes)
        expected_max = sum(item.max_major_passes for item in self.remaining_passes)
        if self.total_remaining_major_passes_min != expected_min:
            raise ValueError("minimum remaining estimate does not match remaining passes")
        if self.total_remaining_major_passes_max != expected_max:
            raise ValueError("maximum remaining estimate does not match remaining passes")
        if self.production_feature_done and self.remaining_passes:
            raise ValueError("complete production estimate cannot include remaining passes")
        if not self.read_only or self.writes_estimate_artifact:
            raise ValueError("completion estimate must remain read-only and no-write")
        forbidden_flags = (
            self.dependency_install_attempted,
            self.server_start_attempted,
            self.network_probe_attempted,
            self.browser_launch_attempted,
            self.cdp_connection_attempted,
            self.mcp_invocation_attempted,
            self.target_navigation_attempted,
            self.screenshot_capture_attempted,
            self.browser_run_log_written,
            self.agent_activity_log_written,
            self.draft_skill_written,
            self.trusted_skill_write_attempted,
            self.skill_activation_attempted,
            self.real_profile_access_attempted,
            self.credential_or_cookie_read_attempted,
            self.browser_harness_used,
            self.browser_use_cli_live_used,
            self.agent_bus_enqueue_attempted,
            self.provider_call_attempted,
            self.gate_mutation_attempted,
            self.canonical_writeback_attempted,
        )
        if any(forbidden_flags):
            raise ValueError("Browser Runtime completion estimate attempted a forbidden effect")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["remaining_passes"] = [item.to_dict() for item in self.remaining_passes]
        payload["critical_path"] = list(self.critical_path)
        payload["external_dependencies"] = list(self.external_dependencies)
        payload["estimate_assumptions"] = list(self.estimate_assumptions)
        payload["blocked_effects"] = list(self.blocked_effects)
        return payload


def _remaining_passes_from_blockers(
    status: BrowserRuntimeCompletionStatus,
    *,
    vault: Path,
) -> list[BrowserRuntimeRemainingPass]:
    blockers = set(status.blocked_reasons)
    remaining: list[BrowserRuntimeRemainingPass] = []

    if "browser_use_cli_no_account_safe_url_validation_run_not_started" in blockers:
        remaining.append(
            BrowserRuntimeRemainingPass(
                pass_id="browser-use-cli-no-account-safe-url-validation-run",
                category="provider_validation",
                status="ready_for_next_pass",
                blocker_reasons=("browser_use_cli_no_account_safe_url_validation_run_not_started",),
                min_major_passes=1,
                max_major_passes=1,
                next_gate="browser-use-cli-no-account-safe-url-validation-run",
                external_dependency=True,
                notes="Safe-URL validation design is ready; the next pass may run the approved localhost-only Browser Use open command if browser dependency setup is handled.",
            )
        )
    elif "browser_use_cli_no_account_safe_url_validation_not_run" in blockers:
        remaining.append(
            BrowserRuntimeRemainingPass(
                pass_id="browser-use-cli-no-account-safe-url-validation",
                category="provider_validation",
                status="ready_for_next_pass",
                blocker_reasons=("browser_use_cli_no_account_safe_url_validation_not_run",),
                min_major_passes=1,
                max_major_passes=1,
                next_gate="browser-use-cli-no-account-safe-url-validation-design",
                external_dependency=True,
                notes="Browser Use CLI executable and help surface are validated; a separate no-account safe-URL browser validation remains required.",
            )
        )
    elif "browser_use_cli_live_validation_blocked_unavailable" in blockers:
        remaining.append(
            BrowserRuntimeRemainingPass(
                pass_id="browser-use-cli-live-validation",
                category="provider_validation",
                status="blocked_unavailable",
                blocker_reasons=("browser_use_cli_live_validation_blocked_unavailable",),
                min_major_passes=1,
                max_major_passes=2,
                next_gate="external-runtime-install-browser-use-cli-then-run-no-account-validation",
                external_dependency=True,
                notes="Requires browser-use CLI to be installed outside ChaseOS and an operator-approved no-account validation run.",
            )
        )
    elif "browser_use_cli_live_validation_deferred" in blockers:
        remaining.append(
            BrowserRuntimeRemainingPass(
                pass_id="browser-use-cli-live-validation",
                category="provider_validation",
                status="ready_for_next_pass",
                blocker_reasons=("browser_use_cli_live_validation_deferred",),
                min_major_passes=1,
                max_major_passes=1,
                next_gate="browser-use-cli-live-validation",
                external_dependency=True,
                notes="CLI availability must still be validated under throwaway-profile/no-account rules.",
            )
        )

    excalidraw_target_blockers = tuple(
        reason
        for reason in status.blocked_reasons
        if reason
        in {
            "excalidraw_local_browser_mcp_live_readiness_blocked_missing_local_target",
            "excalidraw_local_browser_mcp_live_readiness_not_built",
            "excalidraw_local_browser_mcp_live_readiness_unsafe_or_invalid",
        }
    )
    if excalidraw_target_blockers:
        remaining.append(
            BrowserRuntimeRemainingPass(
                pass_id="excalidraw-target-and-readiness",
                category="excalidraw_browser_mcp",
                status="blocked_external_dependency",
                blocker_reasons=excalidraw_target_blockers,
                min_major_passes=1,
                max_major_passes=2,
                next_gate="external-runtime-provide-excalidraw-target-url",
                external_dependency=True,
                notes="Requires an external runtime/operator to provide an accepted local loopback target response before any live proof.",
            )
        )

    if "excalidraw_live_browser_mcp_proof_not_run" in blockers:
        public_proof_ready = any(
            item.area == "production:excalidraw_public_live_browser_proof"
            and item.status == "complete_targeted"
            for item in status.items
        )
        public_drawing_approval_ready = any(
            item.area == "production:excalidraw_public_browser_drawing_proof_approval"
            and item.status == "complete_targeted"
            for item in status.items
        )
        remaining.append(
            BrowserRuntimeRemainingPass(
                pass_id="excalidraw-live-browser-mcp-proof",
                category="excalidraw_browser_mcp",
                status="not_built",
                blocker_reasons=("excalidraw_live_browser_mcp_proof_not_run",),
                min_major_passes=1,
                max_major_passes=1 if public_drawing_approval_ready else 2,
                next_gate=(
                    "excalidraw-public-browser-drawing-proof-run"
                    if public_drawing_approval_ready
                    else
                    "excalidraw-public-browser-drawing-proof-approval"
                    if public_proof_ready
                    else "excalidraw-local-browser-mcp-proof-execution"
                ),
                external_dependency=True,
                notes=(
                    "Public Excalidraw drawing-proof approval exists; next is the bounded no-login browser drawing proof run."
                    if public_drawing_approval_ready
                    else
                    "Public Excalidraw browser reachability is proven; next is a separately approved no-login drawing proof against the public site."
                    if public_proof_ready
                    else "Requires target readiness and operator approval before any local browser/MCP canvas proof."
                ),
            )
        )

    if "studio_operator_ui_not_built" in blockers:
        studio_readiness_ready = _studio_browser_runtime_operator_ui_readiness_ok(vault)
        remaining.append(
            BrowserRuntimeRemainingPass(
                pass_id="studio-operator-browser-runtime-ui",
                category="studio_operator_ui",
                status="planned_phase10",
                blocker_reasons=("studio_operator_ui_not_built",),
                min_major_passes=2,
                max_major_passes=3 if studio_readiness_ready else 4,
                next_gate="studio-browser-runtime-approval-and-skill-inspection-ui",
                external_dependency=False,
                notes=(
                    "Read-only Studio operator UI readiness contract exists; remaining work is the actual UI surface for approvals, run evidence, skill inspection, and promotion visibility."
                    if studio_readiness_ready
                    else "Requires a Studio/operator surface for approvals, run evidence, skill inspection, and promotion visibility."
                ),
            )
        )

    known = {
        "browser_use_cli_live_validation_blocked_unavailable",
        "browser_use_cli_no_account_safe_url_validation_run_not_started",
        "browser_use_cli_no_account_safe_url_validation_not_run",
        "browser_use_cli_live_validation_deferred",
        "excalidraw_local_browser_mcp_live_readiness_blocked_missing_local_target",
        "excalidraw_local_browser_mcp_live_readiness_not_built",
        "excalidraw_local_browser_mcp_live_readiness_unsafe_or_invalid",
        "excalidraw_live_browser_mcp_proof_not_run",
        "studio_operator_ui_not_built",
    }
    unknown = tuple(reason for reason in status.blocked_reasons if reason not in known)
    if unknown:
        remaining.append(
            BrowserRuntimeRemainingPass(
                pass_id="unclassified-browser-runtime-blockers",
                category="unknown",
                status="not_built",
                blocker_reasons=unknown,
                min_major_passes=1,
                max_major_passes=2,
                next_gate=status.next_recommended_pass,
                external_dependency=False,
                notes="Unclassified blockers require a repo-truth pass before production can be called complete.",
            )
        )

    return remaining


def build_browser_runtime_completion_estimate(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    completion_status: BrowserRuntimeCompletionStatus | None = None,
) -> BrowserRuntimeCompletionEstimate:
    """Build a read-only completion estimate from Browser Runtime status."""
    timestamp = generated_at or _now_utc()
    vault = Path(vault_root)
    status = completion_status or build_browser_runtime_completion_status(vault, generated_at=timestamp)
    remaining = tuple(_remaining_passes_from_blockers(status, vault=vault))
    external_dependencies = tuple(
        item.pass_id for item in remaining if item.external_dependency
    )
    assumptions = (
        "Estimates count major implementation/verification passes, not minor documentation-only follow-ups.",
        "External dependency blockers cannot complete until an external runtime/operator supplies the missing target or installed CLI.",
        "No real browser profile, credentials, cookies, authenticated accounts, public tunnels, automatic skill activation, Gate mutation, or canonical writeback are assumed.",
    )
    estimate = BrowserRuntimeCompletionEstimate(
        record_type=BROWSER_RUNTIME_COMPLETION_ESTIMATE_RECORD_TYPE,
        schema_version=BROWSER_RUNTIME_COMPLETION_ESTIMATE_VERSION,
        generated_at=timestamp,
        status=(
            BROWSER_RUNTIME_COMPLETION_ESTIMATE_COMPLETE
            if status.production_feature_done
            else BROWSER_RUNTIME_COMPLETION_ESTIMATE_BLOCKED
        ),
        overall_status=status.overall_status,
        bounded_mvp_done=status.bounded_mvp_done,
        production_feature_done=status.production_feature_done,
        source_next_recommended_pass=status.next_recommended_pass,
        blocker_count=len(status.blocked_reasons),
        item_count=status.item_count,
        total_remaining_major_passes_min=sum(item.min_major_passes for item in remaining),
        total_remaining_major_passes_max=sum(item.max_major_passes for item in remaining),
        remaining_passes=remaining,
        critical_path=tuple(item.pass_id for item in remaining),
        external_dependencies=external_dependencies,
        estimate_assumptions=assumptions,
    )
    estimate.validate()
    return estimate


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Report read-only Browser Runtime completion estimate.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    estimate = build_browser_runtime_completion_estimate(args.vault_root)
    payload = estimate.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {payload['status']}")
        print(f"overall_status: {payload['overall_status']}")
        print(
            "remaining_major_passes: "
            f"{payload['total_remaining_major_passes_min']}-{payload['total_remaining_major_passes_max']}"
        )
        print(f"next_recommended_pass: {payload['source_next_recommended_pass']}")
        for item in payload["remaining_passes"]:
            print(f"- {item['pass_id']}: {item['min_major_passes']}-{item['max_major_passes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
