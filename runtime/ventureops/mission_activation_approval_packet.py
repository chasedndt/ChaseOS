"""Draft Mission Mode activation approval packet and handler design surface."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.ventureops.mission_activation_readiness import build_mission_activation_readiness


MISSION_ACTIVATION_APPROVAL_PACKET_FILENAME = "activation-approval-packet-draft.json"
FORBIDDEN_MISSION_ACTIVATION_ACTIONS = [
    "mission_activation",
    "aor_dispatch",
    "agent_bus_task_write",
    "workflow_evolution_apply",
    "provider_call",
    "browser_action",
    "browser_skill_activation",
    "external_send",
    "crm_or_payment_mutation",
    "live_trading",
    "protected_file_edit",
    "canonical_promotion",
    "credential_or_secret_read",
]


def _safe_slug(value: str) -> str:
    normalized = "".join(char if char.isalnum() or char in {"-", "_", "."} else "-" for char in value.strip())
    collapsed = "-".join(part for part in normalized.split("-") if part)
    return collapsed[:96] or "mission"


def _packet_id(mission_id: str) -> str:
    return f"{_safe_slug(mission_id)}-activation-approval-draft"


def _recommended_packet_path(mission_workspace_path: str | None, mission_id: str | None) -> str:
    if mission_workspace_path and not Path(mission_workspace_path).is_absolute():
        return str(Path(mission_workspace_path) / MISSION_ACTIVATION_APPROVAL_PACKET_FILENAME).replace("\\", "/")
    slug = _safe_slug(mission_id or "mission")
    return f"07_LOGS/VentureOps-Missions/{slug}/{MISSION_ACTIVATION_APPROVAL_PACKET_FILENAME}"


def _approval_template(*, mission_id: str, mission_workspace_path: str) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "type": "ventureops-mission-activation-approval",
        "approval_id": "operator-supplied-id",
        "approval_decision": "pending",
        "approval_status": "draft",
        "approved_by": "operator",
        "approved_at": "operator-supplied-iso8601",
        "mission_id": mission_id,
        "mission_workspace_path": mission_workspace_path,
        "approved_next_step": "aor_mission_dry_run_only",
        "approved_scope": [
            "load the existing validated dry-run mission workspace",
            "run only a separately approved local AOR mission dry-run",
            "write local proof/review/scorecard artifacts only",
        ],
        "required_acknowledgements": [
            "mission manifest is still draft until a separate activation executor consumes approval",
            "workflow evolution proposal remains pending review and must not auto-apply",
            "AOR mission handler and Agent Bus mission packet contract are implemented only for local dry-review and inert packet preview",
            "external sends, provider/browser actions, CRM/payment mutations, live trading, and canonical promotion remain forbidden",
        ],
        "activation_authority_granted": False,
        "aor_dispatch_authorized": False,
        "agent_bus_task_write_authorized": False,
        "workflow_evolution_apply_authorized": False,
        "external_side_effects_authorized": False,
        "draft_boundary": "template only; not consumable as execution authority",
    }


def _aor_handler_design(mission_id: str) -> dict[str, Any]:
    normalized = _safe_slug(mission_id).replace("-", "_").replace(".", "_")
    return {
        "status": "IMPLEMENTED_LOCAL_DRY_REVIEW",
        "handler_id": normalized,
        "implemented_handler_path": f"runtime/workflows/missions/{normalized}.py",
        "implemented_manifest_path": f"runtime/workflows/registry/{normalized}.yaml",
        "base_workflows": [
            "agent_runtime_governance_audit",
            "ventureops_ai_runtime_security_audit",
        ],
        "required_inputs": [
            "mission_workspace_path",
            "activation_approval_packet_path",
            "run_id",
            "date",
            "source_paths",
        ],
        "required_stages": [
            {
                "stage": "load_mission_workspace",
                "requirement": "all dry-run artifacts validate before any handler action",
            },
            {
                "stage": "validate_activation_approval",
                "requirement": "future executor must verify a separate operator approval artifact and exact mission/workspace match",
            },
            {
                "stage": "run_local_aor_dry_run",
                "requirement": "reuse bounded governance-audit workflow behavior without provider/browser/external side effects",
            },
            {
                "stage": "write_mission_artifacts",
                "requirement": "write local mission review, proof card, scorecard, and blocked-action audit only",
            },
            {
                "stage": "propose_evolution",
                "requirement": "emit workflow evolution proposal as pending review; never auto-apply",
            },
        ],
        "allowed_write_roots": [
            "07_LOGS/VentureOps-Missions/",
            "07_LOGS/Mission-Reviews/",
            "07_LOGS/Workflow-Proofs/",
            "07_LOGS/Runtime-Audits/",
        ],
        "forbidden_actions": FORBIDDEN_MISSION_ACTIVATION_ACTIONS,
        "activation_performed": False,
        "aor_dispatch_performed": False,
        "implementation_boundary": "local dry-review handler only; not a mission activation executor",
    }


def _agent_bus_contract_design(mission_id: str) -> dict[str, Any]:
    return {
        "status": "IMPLEMENTED_PREVIEW_CONTRACT",
        "extends": "runtime/agent_bus/task-packet.schema.json",
        "implemented_contract_paths": [
            "runtime/agent_bus/mission_tasks.py",
            "runtime/agent_bus/schemas/mission_task_packet.schema.json",
        ],
        "implemented_enqueue_gate_paths": [
            "runtime/ventureops/mission_agent_bus_enqueue_gate.py",
            "chaseos ventureops mission-agent-bus-enqueue-gate",
        ],
        "mission_id": mission_id,
        "task_type": "mission.run_dry_review",
        "addressable_runtimes": [
            "Codex",
            "Hermes",
            "OpenClaw",
        ],
        "required_packet_fields": [
            "task_id",
            "run_id",
            "from",
            "to",
            "intent",
            "status",
            "request",
            "expected_output",
            "mission_id",
            "mission_workspace_path",
            "activation_approval_packet_path",
            "write_policy",
            "forbidden_actions",
        ],
        "required_execution_constraints": {
            "allow_shell_commands": False,
            "allow_live_subprocess": False,
            "write_policy": "declared-paths",
            "allowed_write_paths": [
                "07_LOGS/VentureOps-Missions/",
                "07_LOGS/Workflow-Proofs/",
                "07_LOGS/Runtime-Audits/",
            ],
        },
        "allowed_result_shapes": [
            "proposal",
            "patch",
            "risk",
            "blocked",
            "complete",
        ],
        "forbidden_actions": FORBIDDEN_MISSION_ACTIVATION_ACTIONS,
        "live_enqueue_implemented": True,
        "agent_bus_task_written": False,
        "implementation_boundary": "exact-once local task write only; task claim and workflow dispatch remain separate approvals",
    }


def _authority_boundary(readiness_boundary: dict[str, Any], *, approval_consumed: bool = False) -> dict[str, Any]:
    return {
        **readiness_boundary,
        "approval_packet_draft_only": not approval_consumed,
        "operator_approval_consumed": approval_consumed,
        "activation_approval_written": False,
        "mission_activation_performed": readiness_boundary.get("mission_activation_performed") is True,
        "aor_dispatch_performed": readiness_boundary.get("aor_dispatch_performed") is True,
        "agent_bus_task_written": readiness_boundary.get("agent_bus_task_written") is True,
        "workflow_evolution_applied": False,
    }


def build_mission_activation_approval_packet(
    vault_root: str | Path,
    *,
    mission_workspace: str | Path | None = None,
) -> dict[str, Any]:
    """Return a draft approval packet and design notes without granting authority."""

    readiness = build_mission_activation_readiness(vault_root, mission_workspace=mission_workspace)
    mission_id = str(readiness.get("mission_id") or "mission-id-missing")
    mission_workspace_path = str(readiness.get("mission_workspace_path") or "mission-workspace-missing")
    artifact_validation_ok = bool(readiness.get("artifact_validation_ok"))
    workspace_exists = bool(readiness.get("mission_workspace_exists"))
    approval_consumed = bool(readiness.get("approval_consumed"))
    manifest_promotion_review_consumed = bool(readiness.get("manifest_promotion_review_consumed"))
    agent_bus_enqueue_consumed = bool(readiness.get("agent_bus_mission_enqueue_consumed"))
    runtime_claim_result_consumed = bool(readiness.get("runtime_claim_result_consumed"))
    mission_active = bool(readiness.get("mission_active"))
    ready_for_activation = bool(readiness.get("ready_for_activation"))
    ready_for_aor_dispatch = bool(readiness.get("ready_for_aor_dispatch"))
    ready_for_operator_review = workspace_exists and artifact_validation_ok
    recommended_packet_path = _recommended_packet_path(mission_workspace_path, mission_id)
    packet_status = (
        "mission_active_local"
        if mission_active
        else "runtime_claim_result_ingested_pending_activation_gate"
        if ready_for_activation and runtime_claim_result_consumed
        else "agent_bus_mission_task_enqueued_pending_runtime_claim_or_result"
        if ready_for_activation and agent_bus_enqueue_consumed
        else "activation_ready_pending_dispatch_approval"
        if ready_for_activation
        else "activation_approval_consumed_pending_remaining_blockers"
        if approval_consumed
        else "draft_pending_operator_approval"
        if ready_for_operator_review
        else "blocked_missing_valid_dry_run_workspace"
    )

    safe_followup_plan = (
        [
            "do not duplicate the Agent Bus mission task; exact-once enqueue is already consumed",
            "only a separately approved runtime claim/result path may process the open task",
            "rerun mission activation readiness immediately before any further active mission action",
        ]
        if ready_for_activation and agent_bus_enqueue_consumed
        and not runtime_claim_result_consumed
        else [
            "runtime claim/result ingestion is complete",
            "consume the separate exact-once activation gate before local active state",
            "rerun mission activation readiness immediately before any further active mission action",
        ]
        if ready_for_activation and runtime_claim_result_consumed
        else [
            "mission is active locally",
            "final hardening is complete for local Mission Mode gates",
            "do not perform external/provider/browser/credential/canonical effects from this packet surface",
        ]
        if mission_active
        else [
            "keep Agent Bus mission task packet handling as inert preview until exact-once enqueue approval exists",
            "run only a separately approved local AOR mission dry-run or dispatch gate",
            "rerun mission activation readiness immediately before any active mission execution",
        ]
        if ready_for_activation
        else [
            "consume the exact-once manifest-promotion/workflow-evolution review gate before active execution",
            "keep Agent Bus mission task packet handling as inert preview until exact-once enqueue approval exists",
            "rerun mission activation readiness before any active mission execution",
        ]
        if approval_consumed and not manifest_promotion_review_consumed
        else
        [
            "resolve remaining manifest/workflow blockers before active execution",
            "keep Agent Bus mission task packet handling as inert preview until exact-once enqueue approval exists",
            "rerun mission activation readiness before any active mission execution",
        ]
        if approval_consumed
        else [
            "consume the exact-once activation approval gate if it is still pending",
            "resolve draft mission manifest and workflow-evolution review blockers before active execution",
            "keep Agent Bus mission task packet handling as inert preview until exact-once enqueue approval exists",
            "rerun mission activation readiness before any active mission execution",
        ]
    )
    next_command = (
        "chaseos ventureops mission-activation-readiness "
        f"--mission-workspace {mission_workspace_path} --json"
        if mission_active
        else "chaseos ventureops mission-activation-gate "
        f"--mission-workspace {mission_workspace_path} --write-approval --consume --activate --json"
        if ready_for_activation and runtime_claim_result_consumed
        else
        "chaseos ventureops mission-activation-readiness "
        f"--mission-workspace {mission_workspace_path} --json"
        if ready_for_activation and agent_bus_enqueue_consumed
        else "chaseos ventureops mission-agent-bus-enqueue-gate "
        f"--mission-workspace {mission_workspace_path} --write-approval --consume --enqueue-task --json"
        if ready_for_activation
        else "chaseos ventureops mission-manifest-promotion-review-gate "
        f"--mission-workspace {mission_workspace_path} --write-review --consume --json"
        if approval_consumed and not manifest_promotion_review_consumed
        else "chaseos ventureops mission-activation-approval-consume "
        f"--mission-workspace {mission_workspace_path} --write-approval --consume --json"
    )

    packet = {
        "schema_version": "0.1",
        "packet_type": "ventureops-mission-activation-approval-packet",
        "packet_id": _packet_id(mission_id),
        "packet_status": packet_status,
        "mission_id": mission_id,
        "mission_workspace_path": mission_workspace_path,
        "readiness_status": readiness.get("readiness_status"),
        "readiness_blockers": list(readiness.get("blockers") or []),
        "mission_state_blockers": list(readiness.get("mission_state_blockers") or []),
        "artifact_validation_ok": artifact_validation_ok,
        "ready_for_operator_review": ready_for_operator_review,
        "operator_decision_required": not approval_consumed,
        "operator_approved": approval_consumed,
        "approval_consumed": approval_consumed,
        "activation_approval_artifact_path": readiness.get("activation_approval_artifact_path"),
        "activation_approval_consumption_marker_path": readiness.get("activation_approval_consumption_marker_path"),
        "manifest_promotion_review_consumed": manifest_promotion_review_consumed,
        "manifest_promotion_review_artifact_path": readiness.get("manifest_promotion_review_artifact_path"),
        "manifest_promotion_review_marker_path": readiness.get("manifest_promotion_review_marker_path"),
        "agent_bus_mission_enqueue_consumed": agent_bus_enqueue_consumed,
        "agent_bus_mission_enqueue_artifact_path": readiness.get("agent_bus_mission_enqueue_artifact_path"),
        "agent_bus_mission_enqueue_marker_path": readiness.get("agent_bus_mission_enqueue_marker_path"),
        "agent_bus_mission_task_id": readiness.get("agent_bus_mission_task_id"),
        "agent_bus_mission_task_recipient": readiness.get("agent_bus_mission_task_recipient"),
        "agent_bus_mission_task_priority": readiness.get("agent_bus_mission_task_priority"),
        "agent_bus_mission_task_claimed": readiness.get("agent_bus_mission_task_claimed") is True,
        "runtime_claim_result_consumed": runtime_claim_result_consumed,
        "runtime_claim_result_marker_path": readiness.get("runtime_claim_result_marker_path"),
        "mission_runtime_result_path": readiness.get("mission_runtime_result_path"),
        "mission_result_ingested": readiness.get("mission_result_ingested") is True,
        "mission_active": mission_active,
        "mission_activation_gate_marker_path": readiness.get("mission_activation_gate_marker_path"),
        "ready_for_activation": ready_for_activation,
        "ready_for_aor_dispatch": ready_for_aor_dispatch,
        "activation_performed": mission_active,
        "aor_dispatch_performed": readiness.get("mission_runtime_aor_dispatch_performed") is True,
        "agent_bus_task_written": readiness.get("agent_bus_mission_task_written") is True,
        "workflow_evolution_applied": False,
        "recommended_packet_path": recommended_packet_path,
        "approval_decision_fields": [
            "approval_id",
            "approval_decision=approved",
            "approved_by",
            "approved_at",
            "mission_id",
            "mission_workspace_path",
            "approved_next_step=aor_mission_dry_run_only",
            "required_acknowledgements",
        ],
        "approval_packet_template": _approval_template(
            mission_id=mission_id,
            mission_workspace_path=mission_workspace_path,
        ),
        "aor_handler_design": _aor_handler_design(mission_id),
        "agent_bus_contract_design": _agent_bus_contract_design(mission_id),
        "safe_followup_plan": safe_followup_plan,
        "next_required_action": (
            "mission is active locally; external/client action requires separate operator-approved evidence"
            if mission_active
            else "consume the separate exact-once mission activation gate"
            if ready_for_activation and runtime_claim_result_consumed
            else "wait for a separately approved runtime claim/result or run an AOR dry-review follow-up"
            if ready_for_activation and agent_bus_enqueue_consumed
            else "run a separately approved AOR mission dry-run or exact-once Agent Bus enqueue gate"
            if ready_for_activation
            else "consume the exact-once manifest-promotion/workflow-evolution review gate before active execution"
            if approval_consumed and not manifest_promotion_review_consumed
            else "resolve remaining manifest/workflow blockers before active execution"
            if approval_consumed
            else "operator review of the draft approval packet plus exact-once activation approval consumption before active execution"
            if ready_for_operator_review
            else "restore or provide a valid local Mission Mode dry-run workspace"
        ),
        "next_command": next_command,
        "authority_boundary": _authority_boundary(
            dict(readiness.get("authority_boundary") or {}),
            approval_consumed=approval_consumed,
        ),
    }

    return {
        "ok": True,
        "schema_version": "0.1",
        "packet_status": packet["packet_status"],
        "ready_for_operator_review": ready_for_operator_review,
        "ready_for_activation": ready_for_activation,
        "ready_for_aor_dispatch": ready_for_aor_dispatch,
        "packet": packet,
        "readiness": readiness,
        "recommended_packet_path": recommended_packet_path,
        "errors": [],
        "authority_boundary": packet["authority_boundary"],
    }
