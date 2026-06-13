"""Read-only readiness checks for VentureOps Mission Mode activation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.ventureops.mission_activation_approval_consumption import (
    load_mission_activation_approval_consumption_state,
)
from runtime.ventureops.mission_dry_runs import validate_mission_dry_run_workspace
from runtime.ventureops.mission_manifest_promotion_review_gate import (
    load_mission_manifest_promotion_review_state,
)


DEFAULT_MISSION_WORKSPACE = (
    Path("07_LOGS")
    / "VentureOps-Missions"
    / "2026-05-13_mission-chase-ai-runtime-governance-kit-dry-run"
)

HIGH_IMPACT_BOUNDARY_FLAGS = (
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
)


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not contain a JSON object")
    return data


def _vault_relative(path: Path, vault_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(vault_root.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def _resolve_workspace(vault_root: Path, mission_workspace: str | Path | None) -> Path:
    if mission_workspace:
        raw = Path(mission_workspace)
        return raw.resolve() if raw.is_absolute() else (vault_root / raw).resolve()

    default = (vault_root / DEFAULT_MISSION_WORKSPACE).resolve()
    if default.exists():
        return default

    mission_root = vault_root / "07_LOGS" / "VentureOps-Missions"
    if mission_root.exists():
        candidates = sorted(
            (item for item in mission_root.iterdir() if item.is_dir() and item.name.endswith("-dry-run")),
            key=lambda item: item.name,
            reverse=True,
        )
        if candidates:
            return candidates[0].resolve()
    return default


def _mission_handler_candidates(mission_id: str, vault_root: Path) -> list[Path]:
    normalized = mission_id.replace("-", "_").replace(".", "_")
    return [
        vault_root / "runtime" / "workflows" / f"{normalized}.py",
        vault_root / "runtime" / "workflows" / "missions" / f"{normalized}.py",
    ]


def _agent_bus_contract_candidates(vault_root: Path) -> list[Path]:
    return [
        vault_root / "runtime" / "agent_bus" / "mission_tasks.py",
        vault_root / "runtime" / "agent_bus" / "schemas" / "mission_task_packet.schema.json",
        vault_root / "runtime" / "agent_bus" / "schemas" / "mission_task_packet.json",
    ]


def _workflow_alias_declared(vault_root: Path) -> bool:
    registry = vault_root / "runtime" / "workflows" / "registry" / "use_case_registry.yaml"
    if not registry.exists():
        return False
    text = registry.read_text(encoding="utf-8", errors="replace")
    return "agent_runtime_governance_audit" in text and "ventureops_ai_runtime_security_audit" in text


def _blocked_payload(vault_root: Path, workspace: Path, blocker: str) -> dict[str, Any]:
    return {
        "ok": True,
        "schema_version": "0.1",
        "readiness_status": "blocked",
        "ready_for_activation": False,
        "ready_for_aor_dispatch": False,
        "mission_id": None,
        "mission_workspace_path": _vault_relative(workspace, vault_root),
        "mission_workspace_exists": False,
        "artifact_validation_ok": False,
        "artifact_validation_errors": [blocker],
        "blockers": [blocker],
        "mission_state_blockers": [],
        "warnings": [],
        "next_required_action": "create or provide a validated local Mission Mode dry-run workspace",
        "next_command": (
            "chaseos ventureops mission-activation-readiness "
            "--mission-workspace PATH --json"
        ),
        "safe_followup_plan": [
            "provide a local dry-run workspace path",
            "rerun mission activation readiness",
            "do not dispatch AOR or Agent Bus mission tasks until readiness is unblocked",
        ],
        "authority_boundary": {
            **_authority_boundary(),
            "mission_activation_performed": False,
            "aor_dispatch_performed": False,
            "agent_bus_task_written": False,
            "agent_bus_task_claimed": False,
            "mission_result_ingested": False,
        },
    }


def _authority_boundary() -> dict[str, Any]:
    return {
        "readiness_only": True,
        "mission_manifest_file_mutation_performed": False,
        "mission_activation_performed": False,
        "aor_dispatch_performed": False,
        "agent_bus_task_written": False,
        "workflow_mutation_performed": False,
        "workflow_evolution_applied": False,
        "provider_call_performed": False,
        "browser_action_performed": False,
        "browser_skill_activated": False,
        "external_send_performed": False,
        "crm_or_payment_mutation_performed": False,
        "live_trading_performed": False,
        "protected_file_edit_performed": False,
        "credential_or_secret_read_performed": False,
        "canonical_promotion_performed": False,
    }


def build_mission_activation_readiness(
    vault_root: str | Path,
    *,
    mission_workspace: str | Path | None = None,
) -> dict[str, Any]:
    """Return activation/AOR readiness without activating or dispatching a mission."""

    from runtime.ventureops.mission_agent_bus_enqueue_gate import (
        load_mission_agent_bus_enqueue_state,
    )
    from runtime.ventureops.mission_activation_gate import (
        load_mission_activation_gate_state,
    )
    from runtime.ventureops.mission_runtime_claim_result_gate import (
        load_mission_runtime_claim_result_state,
    )

    root = Path(vault_root).resolve()
    workspace = _resolve_workspace(root, mission_workspace)
    if not workspace.exists():
        return _blocked_payload(root, workspace, "mission_dry_run_workspace_missing")

    validation = validate_mission_dry_run_workspace(workspace)
    manifest_path = workspace / "mission-manifest.json"
    state_path = workspace / "mission-state-ledger.json"
    proposal_path = workspace / "workflow-evolution-proposal.json"
    boundary_path = workspace / "run-boundary.json"

    manifest = _load_json(manifest_path)
    state = _load_json(state_path)
    proposal = _load_json(proposal_path)
    boundary = _load_json(boundary_path)

    mission_id = str(manifest.get("mission_id") or validation.get("mission_id") or "")
    approval_state = load_mission_activation_approval_consumption_state(
        root,
        mission_workspace=workspace,
    )
    promotion_review_state = load_mission_manifest_promotion_review_state(
        root,
        mission_workspace=workspace,
    )
    agent_bus_enqueue_state = load_mission_agent_bus_enqueue_state(
        root,
        mission_workspace=workspace,
    )
    runtime_claim_result_state = load_mission_runtime_claim_result_state(
        root,
        mission_workspace=workspace,
    )
    activation_gate_state = load_mission_activation_gate_state(
        root,
        mission_workspace=workspace,
    )
    approval_consumed = boundary.get("approval_consumed") is True or approval_state.get("approval_consumed") is True
    approved_for_activation = boundary.get("approved_for_activation") is True or approval_consumed
    manifest_status = str(manifest.get("status") or "")
    manifest_promotion_review_consumed = promotion_review_state.get("review_consumed") is True
    manifest_promoted_for_activation = (
        promotion_review_state.get("mission_manifest_promoted_for_activation") is True
    )
    effective_manifest_status = (
        str(promotion_review_state.get("effective_mission_manifest_status") or "")
        if manifest_promoted_for_activation
        else manifest_status
    )
    workflow_evolution_status = str(proposal.get("status") or "")
    workflow_evolution_pending_review = workflow_evolution_status == "pending_review"
    workflow_evolution_reviewed_for_activation = (
        promotion_review_state.get("workflow_evolution_reviewed_for_activation") is True
    )
    effective_workflow_evolution_status = (
        str(promotion_review_state.get("effective_workflow_evolution_status") or "")
        if workflow_evolution_reviewed_for_activation
        else workflow_evolution_status
    )
    workflow_evolution_auto_apply_allowed = proposal.get("auto_apply_allowed") is True

    base_workflow_manifest = root / "runtime" / "workflows" / "registry" / "agent_runtime_governance_audit.yaml"
    base_workflow_handler = root / "runtime" / "workflows" / "agent_runtime_governance_audit.py"
    mission_handler_candidates = _mission_handler_candidates(mission_id, root)
    mission_handler_present = any(path.exists() for path in mission_handler_candidates)
    agent_bus_candidates = _agent_bus_contract_candidates(root)
    agent_bus_contract_present = any(path.exists() for path in agent_bus_candidates)
    agent_bus_enqueue_consumed = agent_bus_enqueue_state.get("enqueue_consumed") is True
    runtime_claim_result_consumed = runtime_claim_result_state.get("claim_result_consumed") is True
    mission_activation_gate_consumed = activation_gate_state.get("activation_consumed") is True
    high_impact_drift = []
    for flag in HIGH_IMPACT_BOUNDARY_FLAGS:
        if flag == "agent_bus_task_written" and boundary.get(flag, False) is True and agent_bus_enqueue_consumed:
            continue
        if flag in {"agent_bus_task_claimed", "runtime_result_ingested"} and boundary.get(flag, False) is True and runtime_claim_result_consumed:
            continue
        if flag == "aor_dispatch_performed" and boundary.get(flag, False) is True and runtime_claim_result_consumed:
            continue
        if flag == "mission_activation_performed" and boundary.get(flag, False) is True and mission_activation_gate_consumed:
            continue
        if boundary.get(flag, False) is not False:
            high_impact_drift.append(flag)

    blockers: list[str] = []
    if not validation.get("ok"):
        blockers.append("mission_dry_run_artifact_validation_failed")
    if manifest_status == "draft" and not manifest_promoted_for_activation:
        blockers.append("mission_manifest_is_draft")
    elif effective_manifest_status not in {"approved", "active"}:
        blockers.append(f"mission_manifest_status_not_activation_ready:{effective_manifest_status or 'missing'}")
    approval_state_errors = list(approval_state.get("errors") or [])
    if approval_state_errors:
        blockers.append("mission_activation_approval_consumption_invalid")
    if not approved_for_activation:
        if approval_state.get("approval_artifact_present"):
            blockers.append("mission_activation_approval_not_consumed")
        else:
            blockers.append("mission_activation_approval_missing")
    promotion_review_errors = list(promotion_review_state.get("errors") or [])
    if promotion_review_errors:
        blockers.append("mission_manifest_promotion_workflow_evolution_review_invalid")
    agent_bus_enqueue_errors = list(agent_bus_enqueue_state.get("errors") or [])
    if agent_bus_enqueue_errors:
        blockers.append("mission_agent_bus_enqueue_state_invalid")
    runtime_claim_result_errors = list(runtime_claim_result_state.get("errors") or [])
    if runtime_claim_result_errors:
        blockers.append("mission_runtime_claim_result_state_invalid")
    activation_gate_errors = list(activation_gate_state.get("errors") or [])
    if activation_gate_errors:
        blockers.append("mission_activation_gate_state_invalid")
    if workflow_evolution_pending_review and not workflow_evolution_reviewed_for_activation:
        blockers.append("workflow_evolution_proposal_pending_review")
    if workflow_evolution_auto_apply_allowed:
        blockers.append("workflow_evolution_auto_apply_not_allowed")
    if not mission_handler_present:
        blockers.append("aor_mission_handler_missing")
    if not agent_bus_contract_present:
        blockers.append("agent_bus_mission_dispatch_contract_missing")
    for flag in high_impact_drift:
        blockers.append(f"run_boundary_flag_not_false:{flag}")

    mission_state_blockers = [str(item) for item in state.get("active_blockers") or []]
    ready_for_activation = not blockers and bool(validation.get("ok"))
    ready_for_aor_dispatch = ready_for_activation and mission_handler_present and agent_bus_contract_present
    mission_active = mission_activation_gate_consumed and manifest_status == "active"
    if mission_active:
        ready_for_activation = False
        ready_for_aor_dispatch = False
    next_required_action = (
        "mission is active locally; external/client action requires separate operator-approved evidence"
        if mission_active
        else "consume the separate exact-once mission activation gate"
        if ready_for_activation and runtime_claim_result_consumed
        else "wait for a separately approved runtime claim/result or run an AOR dry-review follow-up"
        if ready_for_activation and agent_bus_enqueue_consumed
        else
        "run a separately approved AOR mission dry-run or exact-once Agent Bus enqueue gate"
        if ready_for_activation
        else "prepare exact-once activation approval consumption before active execution"
        if not approval_consumed
        else "consume the exact-once manifest-promotion/workflow-evolution review gate before active execution"
        if not manifest_promotion_review_consumed
        else "resolve remaining activation blockers before active execution"
    )

    return {
        "ok": True,
        "schema_version": "0.1",
        "readiness_status": (
            "mission_active_local"
            if mission_active
            else "ready_for_activation"
            if ready_for_activation
            else "blocked"
        ),
        "ready_for_activation": ready_for_activation,
        "ready_for_aor_dispatch": ready_for_aor_dispatch,
        "mission_id": mission_id,
        "mission_workspace_path": _vault_relative(workspace, root),
        "mission_workspace_exists": True,
        "artifact_validation_ok": bool(validation.get("ok")),
        "artifact_validation_errors": list(validation.get("errors") or []),
        "files_checked": list(validation.get("files_checked") or []),
        "mission_manifest_status": manifest_status,
        "effective_mission_manifest_status": effective_manifest_status,
        "mission_state_status": state.get("current_status"),
        "mission_state_phase": state.get("current_phase"),
        "mission_state_blockers": mission_state_blockers,
        "approved_for_activation": approved_for_activation,
        "approval_consumed": approval_consumed,
        "activation_approval_artifact_present": approval_state.get("approval_artifact_present") is True,
        "activation_approval_artifact_valid": approval_state.get("approval_artifact_valid") is True,
        "activation_approval_artifact_path": approval_state.get("approval_artifact_path"),
        "activation_approval_consumption_marker_present": approval_state.get("consumption_marker_present") is True,
        "activation_approval_consumption_marker_valid": approval_state.get("consumption_marker_valid") is True,
        "activation_approval_consumption_marker_path": approval_state.get("consumption_marker_path"),
        "activation_approval_consumption_errors": approval_state_errors,
        "manifest_promotion_review_artifact_present": promotion_review_state.get("review_artifact_present") is True,
        "manifest_promotion_review_artifact_valid": promotion_review_state.get("review_artifact_valid") is True,
        "manifest_promotion_review_artifact_path": promotion_review_state.get("review_artifact_path"),
        "manifest_promotion_review_marker_present": promotion_review_state.get("review_marker_present") is True,
        "manifest_promotion_review_marker_valid": promotion_review_state.get("review_marker_valid") is True,
        "manifest_promotion_review_marker_path": promotion_review_state.get("review_marker_path"),
        "manifest_promotion_review_consumed": manifest_promotion_review_consumed,
        "mission_manifest_promoted_for_activation": manifest_promoted_for_activation,
        "workflow_evolution_reviewed_for_activation": workflow_evolution_reviewed_for_activation,
        "manifest_promotion_review_errors": promotion_review_errors,
        "workflow_evolution_status": workflow_evolution_status,
        "effective_workflow_evolution_status": effective_workflow_evolution_status,
        "workflow_evolution_pending_review": workflow_evolution_pending_review,
        "workflow_evolution_auto_apply_allowed": workflow_evolution_auto_apply_allowed,
        "base_aor_workflow_manifest_present": base_workflow_manifest.exists(),
        "base_aor_workflow_handler_present": base_workflow_handler.exists(),
        "workflow_alias_declared": _workflow_alias_declared(root),
        "aor_mission_handler_present": mission_handler_present,
        "aor_mission_handler_candidates": [_vault_relative(path, root) for path in mission_handler_candidates],
        "agent_bus_mission_dispatch_contract_present": agent_bus_contract_present,
        "agent_bus_mission_dispatch_contract_candidates": [
            _vault_relative(path, root) for path in agent_bus_candidates
        ],
        "blockers": blockers,
        "warnings": [],
        "agent_bus_mission_enqueue_artifact_present": (
            agent_bus_enqueue_state.get("enqueue_approval_artifact_present") is True
        ),
        "agent_bus_mission_enqueue_artifact_valid": (
            agent_bus_enqueue_state.get("enqueue_approval_artifact_valid") is True
        ),
        "agent_bus_mission_enqueue_artifact_path": agent_bus_enqueue_state.get("enqueue_approval_artifact_path"),
        "agent_bus_mission_enqueue_marker_present": agent_bus_enqueue_state.get("enqueue_marker_present") is True,
        "agent_bus_mission_enqueue_marker_valid": agent_bus_enqueue_state.get("enqueue_marker_valid") is True,
        "agent_bus_mission_enqueue_marker_path": agent_bus_enqueue_state.get("enqueue_marker_path"),
        "agent_bus_mission_enqueue_consumed": agent_bus_enqueue_consumed,
        "agent_bus_mission_task_written": agent_bus_enqueue_state.get("agent_bus_task_written") is True,
        "agent_bus_mission_task_id": agent_bus_enqueue_state.get("agent_bus_task_id"),
        "agent_bus_mission_task_recipient": agent_bus_enqueue_state.get("recipient"),
        "agent_bus_mission_task_priority": agent_bus_enqueue_state.get("priority"),
        "agent_bus_mission_task_claimed": (
            agent_bus_enqueue_state.get("runtime_task_claimed") is True
            or runtime_claim_result_state.get("runtime_task_claimed") is True
        ),
        "agent_bus_mission_workflow_dispatched": (
            agent_bus_enqueue_state.get("workflow_dispatched") is True
            or runtime_claim_result_state.get("workflow_dispatched") is True
        ),
        "agent_bus_mission_enqueue_errors": agent_bus_enqueue_errors,
        "runtime_claim_result_artifact_present": runtime_claim_result_state.get("claim_result_approval_artifact_present") is True,
        "runtime_claim_result_artifact_valid": runtime_claim_result_state.get("claim_result_approval_artifact_valid") is True,
        "runtime_claim_result_artifact_path": runtime_claim_result_state.get("claim_result_approval_artifact_path"),
        "mission_runtime_result_present": runtime_claim_result_state.get("mission_runtime_result_present") is True,
        "mission_runtime_result_valid": runtime_claim_result_state.get("mission_runtime_result_valid") is True,
        "mission_runtime_result_path": runtime_claim_result_state.get("mission_runtime_result_path"),
        "runtime_claim_result_marker_present": runtime_claim_result_state.get("claim_result_marker_present") is True,
        "runtime_claim_result_marker_valid": runtime_claim_result_state.get("claim_result_marker_valid") is True,
        "runtime_claim_result_marker_path": runtime_claim_result_state.get("claim_result_marker_path"),
        "runtime_claim_result_consumed": runtime_claim_result_consumed,
        "runtime_task_claimed": runtime_claim_result_state.get("runtime_task_claimed") is True,
        "runtime_task_closed": runtime_claim_result_state.get("agent_bus_task_closed") is True,
        "mission_result_ingested": runtime_claim_result_state.get("mission_result_ingested") is True,
        "mission_runtime_aor_dispatch_performed": runtime_claim_result_state.get("aor_dispatch_performed") is True,
        "runtime_claim_result_errors": runtime_claim_result_errors,
        "mission_activation_gate_artifact_present": activation_gate_state.get("activation_approval_artifact_present") is True,
        "mission_activation_gate_artifact_valid": activation_gate_state.get("activation_approval_artifact_valid") is True,
        "mission_activation_gate_artifact_path": activation_gate_state.get("activation_approval_artifact_path"),
        "mission_activation_gate_marker_present": activation_gate_state.get("activation_marker_present") is True,
        "mission_activation_gate_marker_valid": activation_gate_state.get("activation_marker_valid") is True,
        "mission_activation_gate_marker_path": activation_gate_state.get("activation_marker_path"),
        "mission_activation_gate_consumed": mission_activation_gate_consumed,
        "mission_active": mission_active,
        "mission_activation_gate_errors": activation_gate_errors,
        "next_required_action": next_required_action,
        "next_command": (
            "chaseos ventureops mission-external-client-evidence-gate "
            f"--mission-workspace {_vault_relative(workspace, root)} --json"
            if mission_active
            else (
                "chaseos ventureops mission-activation-readiness "
                f"--mission-workspace {_vault_relative(workspace, root)} --json"
            )
        ),
        "safe_followup_plan": (
            [
                "mission is active only in local ChaseOS state",
                "final hardening is complete for local Mission Mode gates",
                "keep provider/browser/credential/payment/CRM/canonical effects blocked until separate approvals exist",
            ]
            if mission_active
            else [
                "runtime claim/result ingestion is complete",
                "consume only the separate exact-once mission activation gate before active local state",
                "do not perform external/client/provider/browser actions from readiness",
            ]
            if ready_for_activation and runtime_claim_result_consumed
            else [
                "do not duplicate the Agent Bus mission task; exact-once enqueue is already consumed",
                "only a separately approved runtime claim/result path may process the open task",
                "do not activate the mission, dispatch AOR directly, or perform external actions from readiness",
            ]
            if ready_for_activation and agent_bus_enqueue_consumed
            else
            [
                "keep Agent Bus mission task handling as inert preview until exact-once enqueue approval exists",
                "run only a separately approved local AOR mission dry-run or dispatch gate",
                "rerun this readiness check immediately before any active mission execution",
            ]
            if ready_for_activation
            else [
                "review or consume the operator activation approval packet if it has not already been consumed",
                "consume the exact-once manifest-promotion/workflow-evolution review gate before active execution",
                "keep Agent Bus mission task handling as inert preview until exact-once enqueue approval exists",
                "rerun this readiness check before any active mission execution",
            ]
        ),
        "authority_boundary": {
            **_authority_boundary(),
            "mission_activation_performed": mission_active,
            "aor_dispatch_performed": runtime_claim_result_consumed,
            "agent_bus_task_written": agent_bus_enqueue_consumed,
            "agent_bus_task_claimed": runtime_claim_result_state.get("runtime_task_claimed") is True,
            "mission_result_ingested": runtime_claim_result_state.get("mission_result_ingested") is True,
        },
    }
