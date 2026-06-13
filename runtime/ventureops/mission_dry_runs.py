"""Validation helpers for local VentureOps Mission Mode dry-run workspaces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .validation import (
    validate_agent_scorecard,
    validate_domain_goal_profile,
    validate_mission_manifest,
    validate_mission_review,
    validate_mission_state,
    validate_proof_card,
    validate_site_profile,
    validate_sub_agent_plan,
    validate_workflow_evolution_proposal,
)


MISSION_DRY_RUN_REQUIRED_FILES = {
    "artifact-index.json",
    "domain-goal-profile.json",
    "mission-manifest.json",
    "mission-review.json",
    "mission-state-ledger.json",
    "proof-card.json",
    "run-boundary.json",
    "scorecard.json",
    "site-profile-candidate.json",
    "sub-agent-plan.json",
    "workflow-evolution-proposal.json",
}

AGENT_BUS_ENQUEUE_MARKER_FILENAME = "mission-agent-bus-enqueue-consumption.json"
MISSION_RUNTIME_CLAIM_RESULT_MARKER_FILENAME = "mission-runtime-claim-result-consumption.json"
MISSION_ACTIVATION_MARKER_FILENAME = "mission-activation-execution-consumption.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _extend_prefixed(errors: list[str], prefix: str, result: dict[str, Any]) -> None:
    for error in result.get("errors") or []:
        errors.append(f"{prefix}: {error}")


def _agent_bus_enqueue_marker_valid(root: Path, mission_id: str) -> bool:
    marker_path = root / AGENT_BUS_ENQUEUE_MARKER_FILENAME
    if not marker_path.exists():
        return False
    try:
        marker = _load_json(marker_path)
    except Exception:
        return False
    if marker.get("type") != "ventureops-mission-agent-bus-enqueue-marker":
        return False
    if marker.get("status") != "executed":
        return False
    if marker.get("mission_id") != mission_id:
        return False
    if marker.get("agent_bus_task_written") is not True:
        return False
    for field in (
        "runtime_task_claimed",
        "runtime_process_started",
        "workflow_dispatched",
        "mission_activation_performed",
        "aor_dispatch_performed",
        "workflow_evolution_applied",
        "provider_call_performed",
        "browser_action_performed",
        "browser_skill_activated",
        "external_send_performed",
        "crm_or_payment_mutation_performed",
        "live_trading_performed",
        "protected_file_edit_performed",
        "credential_or_secret_read_performed",
        "canonical_promotion_performed",
    ):
        if marker.get(field) is not False:
            return False
    return True


def _runtime_claim_result_marker_valid(root: Path, mission_id: str) -> bool:
    marker_path = root / MISSION_RUNTIME_CLAIM_RESULT_MARKER_FILENAME
    if not marker_path.exists():
        return False
    try:
        marker = _load_json(marker_path)
    except Exception:
        return False
    if marker.get("type") != "ventureops-mission-runtime-claim-result-marker":
        return False
    if marker.get("status") != "executed":
        return False
    if marker.get("mission_id") != mission_id:
        return False
    for field in (
        "runtime_task_claimed",
        "workflow_dispatched",
        "aor_dispatch_performed",
        "mission_result_ingested",
        "agent_bus_task_closed",
    ):
        if marker.get(field) is not True:
            return False
    for field in (
        "mission_activation_performed",
        "agent_bus_followup_task_written",
        "workflow_evolution_applied",
        "provider_call_performed",
        "browser_action_performed",
        "browser_skill_activated",
        "external_send_performed",
        "crm_or_payment_mutation_performed",
        "live_trading_performed",
        "protected_file_edit_performed",
        "credential_or_secret_read_performed",
        "canonical_promotion_performed",
    ):
        if marker.get(field) is not False:
            return False
    return True


def _mission_activation_marker_valid(root: Path, mission_id: str) -> bool:
    marker_path = root / MISSION_ACTIVATION_MARKER_FILENAME
    if not marker_path.exists():
        return False
    try:
        marker = _load_json(marker_path)
    except Exception:
        return False
    if marker.get("type") != "ventureops-mission-activation-execution-marker":
        return False
    if marker.get("status") != "executed":
        return False
    if marker.get("mission_id") != mission_id:
        return False
    for field in (
        "mission_activation_performed",
        "runtime_task_claimed",
        "aor_dispatch_performed",
        "mission_result_ingested",
        "agent_bus_task_closed",
    ):
        if marker.get(field) is not True:
            return False
    for field in (
        "workflow_evolution_applied",
        "provider_call_performed",
        "browser_action_performed",
        "browser_skill_activated",
        "external_send_performed",
        "crm_or_payment_mutation_performed",
        "live_trading_performed",
        "protected_file_edit_performed",
        "credential_or_secret_read_performed",
        "canonical_promotion_performed",
    ):
        if marker.get(field) is not False:
            return False
    return _runtime_claim_result_marker_valid(root, mission_id)


def validate_mission_dry_run_workspace(workspace: str | Path) -> dict[str, Any]:
    """Validate a local dry-run artifact bundle without executing the mission."""

    root = Path(workspace)
    errors: list[str] = []
    missing = sorted(filename for filename in MISSION_DRY_RUN_REQUIRED_FILES if not (root / filename).exists())
    if missing:
        return {"ok": False, "errors": [f"missing dry-run artifact: {filename}" for filename in missing], "files_checked": []}

    loaded: dict[str, dict[str, Any]] = {}
    for filename in sorted(MISSION_DRY_RUN_REQUIRED_FILES):
        try:
            loaded[filename] = _load_json(root / filename)
        except json.JSONDecodeError as exc:
            errors.append(f"{filename}: invalid json: {exc}")

    if errors:
        return {"ok": False, "errors": errors, "files_checked": sorted(loaded)}

    manifest = loaded["mission-manifest.json"]
    state = loaded["mission-state-ledger.json"]
    review = loaded["mission-review.json"]
    proposal = loaded["workflow-evolution-proposal.json"]
    site_profile = loaded["site-profile-candidate.json"]
    boundary = loaded["run-boundary.json"]

    _extend_prefixed(errors, "mission-manifest.json", validate_mission_manifest(manifest))
    _extend_prefixed(errors, "sub-agent-plan.json", validate_sub_agent_plan(loaded["sub-agent-plan.json"]))
    _extend_prefixed(errors, "domain-goal-profile.json", validate_domain_goal_profile(loaded["domain-goal-profile.json"]))
    _extend_prefixed(errors, "mission-state-ledger.json", validate_mission_state(state))
    _extend_prefixed(errors, "mission-review.json", validate_mission_review(review))
    _extend_prefixed(errors, "workflow-evolution-proposal.json", validate_workflow_evolution_proposal(proposal))
    _extend_prefixed(errors, "site-profile-candidate.json", validate_site_profile(site_profile))

    try:
        validate_proof_card(loaded["proof-card.json"])
    except ValueError as exc:
        errors.append(f"proof-card.json: {exc}")
    _extend_prefixed(errors, "scorecard.json", validate_agent_scorecard(loaded["scorecard.json"]))

    mission_id = manifest.get("mission_id")
    for filename in ("sub-agent-plan.json", "mission-state-ledger.json", "mission-review.json", "workflow-evolution-proposal.json"):
        if loaded[filename].get("mission_id") != mission_id:
            errors.append(f"{filename}: mission_id does not match manifest")

    runtime_claim_result_gate_valid = _runtime_claim_result_marker_valid(root, str(mission_id or ""))
    mission_activation_gate_valid = _mission_activation_marker_valid(root, str(mission_id or ""))
    if mission_activation_gate_valid:
        if manifest.get("status") != "active":
            errors.append("mission-manifest.json: activated mission manifest must be active")
    elif manifest.get("status") != "draft":
        errors.append("mission-manifest.json: dry-run manifest must remain draft before activation gate")
    if proposal.get("auto_apply_allowed") is not False:
        errors.append("workflow-evolution-proposal.json: dry-run proposals must not auto-apply")
    if proposal.get("status") not in {"draft", "pending_review"}:
        errors.append("workflow-evolution-proposal.json: dry-run proposal status must remain draft or pending_review")
    if site_profile.get("browser_skill_activation_allowed") is not False:
        errors.append("site-profile-candidate.json: browser skill activation must remain blocked")

    blocked_flags = {
        "aor_dispatch_performed",
        "agent_bus_task_claimed",
        "agent_bus_task_written",
        "browser_action_performed",
        "browser_skill_activated",
        "canonical_promotion_performed",
        "credential_or_secret_read_performed",
        "crm_or_payment_mutation_performed",
        "external_send_performed",
        "live_trading_performed",
        "mission_activation_performed",
        "provider_call_performed",
        "protected_file_edit_performed",
        "runtime_result_ingested",
        "workflow_mutation_performed",
    }
    agent_bus_enqueue_gate_valid = _agent_bus_enqueue_marker_valid(root, str(mission_id or ""))
    for flag in sorted(blocked_flags):
        if flag == "agent_bus_task_written" and boundary.get(flag, False) is True and agent_bus_enqueue_gate_valid:
            continue
        if flag in {"agent_bus_task_claimed", "runtime_result_ingested"} and boundary.get(flag, False) is True and runtime_claim_result_gate_valid:
            continue
        if flag == "aor_dispatch_performed" and boundary.get(flag, False) is True and runtime_claim_result_gate_valid:
            continue
        if flag == "mission_activation_performed" and boundary.get(flag, False) is True and mission_activation_gate_valid:
            continue
        if boundary.get(flag, False) is not False:
            errors.append(f"run-boundary.json: {flag} must be false")

    return {
        "ok": not errors,
        "errors": errors,
        "files_checked": sorted(MISSION_DRY_RUN_REQUIRED_FILES),
        "mission_id": mission_id,
    }
