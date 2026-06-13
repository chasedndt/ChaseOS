"""No-execution planner for a future contract-backed VincisOS browser proof.

This module composes the VincisOS full UI target contract validator into the
artifact/action plan for a later browser proof. It does not open a browser,
connect to CDP, capture screenshots, click UI, or write proof artifacts.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from runtime.browser_runtime.models import slugify
from runtime.browser_runtime.vincisos_full_ui_target_contract import (
    evaluate_vincisos_full_ui_target_contract,
    evaluate_vincisos_full_ui_target_contract_file,
)


PROOF_PLAN_VERSION = "vincisos.contract_backed_proof_plan.v1"
DEFAULT_RUN_ID = "vincisos_full_ui_contract_backed_proof"


@dataclass(frozen=True)
class VincisOSContractBackedProofPlanResult:
    """Machine-readable no-execution plan for the future browser proof."""

    ok: bool
    status: str
    proof_plan_version: str
    run_id: str
    target_name: str | None
    target_url: str | None
    blockers: list[dict[str, str]]
    contract_validation: dict[str, Any]
    action_plan: list[dict[str, Any]]
    artifact_plan: list[dict[str, Any]]
    security_constraints: dict[str, bool]
    next_allowed_step: str | None
    browser_launch_attempted: bool = False
    cdp_connection_attempted: bool = False
    browser_harness_used: bool = False
    browser_use_cli_live_used: bool = False
    screenshot_attempted: bool = False
    profile_access_attempted: bool = False
    credentials_read: bool = False
    trusted_skill_write_attempted: bool = False
    skill_activation_attempted: bool = False
    agent_bus_enqueue_attempted: bool = False
    provider_call_attempted: bool = False
    gate_mutation_attempted: bool = False
    canonical_writeback_attempted: bool = False
    files_modified: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _blocker(blocker_id: str, message: str) -> dict[str, str]:
    return {"blocker_id": blocker_id, "message": message}


def _planned_artifacts(run_id: str) -> list[dict[str, Any]]:
    safe_run_id = slugify(run_id, DEFAULT_RUN_ID)
    return [
        {
            "artifact_type": "browser_run_log",
            "path": f"07_LOGS/Browser-Runs/{safe_run_id}.json",
            "write_allowed_in_future_proof": True,
            "written_by_planner": False,
        },
        {
            "artifact_type": "agent_activity_log",
            "path": f"07_LOGS/Agent-Activity/{safe_run_id}.md",
            "write_allowed_in_future_proof": True,
            "written_by_planner": False,
        },
        {
            "artifact_type": "screenshot",
            "path": f"07_LOGS/Browser-Runs/{safe_run_id}_screenshot.png",
            "write_allowed_in_future_proof": True,
            "written_by_planner": False,
        },
        {
            "artifact_type": "draft_site_skill",
            "path": f"06_AGENTS/Browser-Skills/_drafts/{safe_run_id}.md",
            "write_allowed_in_future_proof": True,
            "written_by_planner": False,
            "activation_allowed": False,
        },
        {
            "artifact_type": "untrusted_skill_candidate",
            "path": f"03_INPUTS/Browser-Skill-Candidates/vincisos-local/{safe_run_id}.md",
            "write_allowed_in_future_proof": True,
            "written_by_planner": False,
            "activation_allowed": False,
        },
    ]


def _planned_actions(target_url: str | None) -> list[dict[str, Any]]:
    return [
        {
            "step": 1,
            "action": "validate_contract",
            "target": "vincisos.full_ui_target.v1",
            "execution_surface": "local validator",
            "already_completed_by_planner": True,
        },
        {
            "step": 2,
            "action": "open",
            "target": target_url,
            "execution_surface": "future isolated browser context",
            "requires_future_proof": True,
        },
        {
            "step": 3,
            "action": "read_state",
            "target": target_url,
            "execution_surface": "future isolated browser context",
            "requires_future_proof": True,
        },
        {
            "step": 4,
            "action": "capture_screenshot",
            "target": "visible product UI",
            "execution_surface": "future isolated browser context",
            "requires_future_proof": True,
        },
        {
            "step": 5,
            "action": "harmless_click",
            "target": "operator-approved local test control only",
            "execution_surface": "future isolated browser context",
            "requires_future_proof": True,
        },
        {
            "step": 6,
            "action": "write_draft_evidence",
            "target": "logs and draft-only skill/candidate paths",
            "execution_surface": "future proof writeback",
            "requires_future_proof": True,
        },
    ]


def _security_constraints() -> dict[str, bool]:
    return {
        "throwaway_or_isolated_profile_required": True,
        "real_profile_allowed": False,
        "credentials_allowed": False,
        "cookie_export_allowed": False,
        "cdp_allowed": False,
        "browser_harness_allowed": False,
        "browser_use_cli_live_allowed": False,
        "public_tunnel_allowed": False,
        "trusted_skill_write_allowed": False,
        "skill_activation_allowed": False,
        "agent_bus_enqueue_allowed": False,
        "provider_call_allowed": False,
        "gate_mutation_allowed": False,
        "canonical_writeback_allowed": False,
    }


def build_vincisos_contract_backed_proof_plan(
    contract: Mapping[str, Any] | None,
    *,
    run_id: str | None = None,
) -> VincisOSContractBackedProofPlanResult:
    """Build a no-execution proof plan from a target contract."""
    validation = evaluate_vincisos_full_ui_target_contract(contract)
    validation_dict = validation.as_dict()
    planned_run_id = slugify(run_id or DEFAULT_RUN_ID, DEFAULT_RUN_ID)
    blockers = list(validation.blockers)
    if not validation.ok:
        blockers.insert(
            0,
            _blocker(
                "target_contract_not_ready",
                "The VincisOS target contract is not ready; no browser proof may run.",
            ),
        )

    ok = not blockers
    status = (
        "vincisos_contract_backed_proof_plan_ready_no_execution"
        if ok
        else "blocked_vincisos_contract_backed_proof_plan"
    )
    next_step = (
        "A future pass may run this plan only in an isolated browser context and write draft/log artifacts."
        if ok
        else None
    )
    return VincisOSContractBackedProofPlanResult(
        ok=ok,
        status=status,
        proof_plan_version=PROOF_PLAN_VERSION,
        run_id=planned_run_id,
        target_name=validation.target_name,
        target_url=validation.target_url,
        blockers=blockers,
        contract_validation=validation_dict,
        action_plan=_planned_actions(validation.target_url),
        artifact_plan=_planned_artifacts(planned_run_id),
        security_constraints=_security_constraints(),
        next_allowed_step=next_step,
    )


def build_vincisos_contract_backed_proof_plan_from_file(
    path: Path | str,
    *,
    run_id: str | None = None,
) -> VincisOSContractBackedProofPlanResult:
    """Load a contract file and build the no-execution proof plan."""
    validation = evaluate_vincisos_full_ui_target_contract_file(path)
    planned_run_id = slugify(run_id or DEFAULT_RUN_ID, DEFAULT_RUN_ID)
    blockers = list(validation.blockers)
    if not validation.ok:
        blockers.insert(
            0,
            _blocker(
                "target_contract_not_ready",
                "The VincisOS target contract is not ready; no browser proof may run.",
            ),
        )
    ok = not blockers
    status = (
        "vincisos_contract_backed_proof_plan_ready_no_execution"
        if ok
        else "blocked_vincisos_contract_backed_proof_plan"
    )
    next_step = (
        "A future pass may run this plan only in an isolated browser context and write draft/log artifacts."
        if ok
        else None
    )
    return VincisOSContractBackedProofPlanResult(
        ok=ok,
        status=status,
        proof_plan_version=PROOF_PLAN_VERSION,
        run_id=planned_run_id,
        target_name=validation.target_name,
        target_url=validation.target_url,
        blockers=blockers,
        contract_validation=validation.as_dict(),
        action_plan=_planned_actions(validation.target_url),
        artifact_plan=_planned_artifacts(planned_run_id),
        security_constraints=_security_constraints(),
        next_allowed_step=next_step,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a no-execution VincisOS contract-backed proof plan.")
    parser.add_argument("--contract-json", required=True, help="Path to a JSON target contract.")
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID, help="Planned proof run id.")
    parser.add_argument("--json", action="store_true", help="Print JSON output. Text output is not implemented.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    result = build_vincisos_contract_backed_proof_plan_from_file(Path(args.contract_json), run_id=args.run_id)
    print(json.dumps(result.as_dict(), indent=2))
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
