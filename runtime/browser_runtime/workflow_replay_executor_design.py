"""No-execution design preflight for a future Browser Workflow replay executor.

This module is ChaseOS-native and intentionally independent. It does not copy
or import workflow-use, Browser Use, Browser Harness, Playwright, or CDP code.
It only reports the future executor contract and current readiness posture.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.browser_runtime.workflows import summarize_workflow_cache


WORKFLOW_REPLAY_EXECUTOR_DESIGN_VERSION = "browser.workflow_replay_executor_design.v1"
WORKFLOW_REPLAY_EXECUTOR_STATUS_READY = "ready_for_operator_review_no_execution"
WORKFLOW_REPLAY_EXECUTOR_STATUS_BLOCKED = "blocked_cache_foundation_missing"

FORBIDDEN_EFFECTS = (
    "workflow_replay_attempted",
    "browser_launch_attempted",
    "cdp_connection_attempted",
    "browser_harness_used",
    "browser_use_cli_live_used",
    "real_profile_access_attempted",
    "credential_or_cookie_read_attempted",
    "trusted_skill_write_attempted",
    "skill_activation_attempted",
    "agent_bus_enqueue_attempted",
    "provider_call_attempted",
    "gate_mutation_attempted",
    "canonical_writeback_attempted",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class WorkflowReplayExecutorDesign:
    """Machine-readable design packet for the future replay executor."""

    record_type: str
    version: str
    generated_at: str
    status: str
    cache_status: str
    implementation_strategy: str
    external_code_copied: bool
    workflow_use_reference_only: bool
    required_preconditions: list[str] = field(default_factory=list)
    future_executor_sequence: list[str] = field(default_factory=list)
    stop_conditions: list[str] = field(default_factory=list)
    required_artifacts: list[str] = field(default_factory=list)
    forbidden_effects: dict[str, bool] = field(default_factory=dict)
    next_step: str = "operator_review"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def validate(self) -> None:
        if self.external_code_copied:
            raise ValueError("external_code_copied must remain false")
        if not self.workflow_use_reference_only:
            raise ValueError("workflow-use must remain reference-only")
        for name in FORBIDDEN_EFFECTS:
            if self.forbidden_effects.get(name) is not False:
                raise ValueError(f"{name} must remain false")


def build_workflow_replay_executor_design(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
) -> WorkflowReplayExecutorDesign:
    """Return a no-execution design packet for a future replay executor."""
    cache = summarize_workflow_cache(vault_root)
    cache_ready = cache.get("status") == "cache_foundation_ready"
    status = WORKFLOW_REPLAY_EXECUTOR_STATUS_READY if cache_ready else WORKFLOW_REPLAY_EXECUTOR_STATUS_BLOCKED
    design = WorkflowReplayExecutorDesign(
        record_type="browser_workflow_replay_executor_design",
        version=WORKFLOW_REPLAY_EXECUTOR_DESIGN_VERSION,
        generated_at=generated_at or _now_utc(),
        status=status,
        cache_status=str(cache.get("status")),
        implementation_strategy="chaseos_native_aor_siteops_executor_no_external_code_copy",
        external_code_copied=False,
        workflow_use_reference_only=True,
        required_preconditions=[
            "native_inactive_workflow_cache_foundation_present",
            "selected_workflow_entry_validates_as_inactive_review_entry",
            "operator_review_promotes_or_selects_entry_for_trial",
            "AOR_manifest_declares_allowed_domain_actions_and_artifacts",
            "Gate_policy_allows_only_declared_browser_run_and_log_outputs",
            "throwaway_or_isolated_browser_profile_required_for_any_live_trial",
            "Browser_Run_Log_and_Agent_Activity_targets_declared",
            "idempotency_key_and_failure_stop_policy_declared",
        ],
        future_executor_sequence=[
            "load_selected_inactive_workflow_entry",
            "validate_entry_schema_domain_steps_and_source_evidence",
            "resolve_AOR_manifest_and_role_card",
            "verify_Gate_allowance_for_declared_artifact_targets",
            "reserve_idempotency_key_before_any_live_action",
            "start_isolated_browser_context_only_after_explicit_approval",
            "execute_only_reviewed_steps_against_allowed_local_or_allowed_domain_target",
            "stop_on_selector_mismatch_redirect_auth_wall_or_unexpected_mutation",
            "write_Browser_Run_Log_Agent_Activity_and_artifacts",
            "generate_repair_or_skill_candidate_as_review_only_if_replay_fails",
        ],
        stop_conditions=[
            "workflow_entry_not_reviewed_or_not_selected",
            "domain_not_allowlisted",
            "step_requires_credentials_cookies_real_profile_payment_or_account_mutation",
            "selector_or_expected_state_mismatch",
            "redirect_to_forbidden_domain",
            "artifact_target_outside_declared_log_paths",
            "Gate_denies_write_target_or_operation",
            "idempotency_marker_collision",
        ],
        required_artifacts=[
            "07_LOGS/Browser-Runs/<run_id>.json",
            "07_LOGS/Agent-Activity/<run_id>.md",
            "runtime/browser_workflows/workflows/<workflow_id>.workflow.json",
            "future replay approval or AOR manifest evidence",
        ],
        forbidden_effects={name: False for name in FORBIDDEN_EFFECTS},
        next_step="workflow-replay-executor-implementation-request" if cache_ready else "browser-workflow-cache-foundation",
    )
    design.validate()
    return design


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Report no-execution Browser Workflow replay executor design.")
    parser.add_argument("--vault-root", default=".", help="Path to the ChaseOS vault root.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    design = build_workflow_replay_executor_design(args.vault_root)
    payload = design.as_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {design.status}")
        print(f"cache_status: {design.cache_status}")
        print(f"next_step: {design.next_step}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
