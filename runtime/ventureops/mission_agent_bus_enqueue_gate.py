"""Exact-once Agent Bus enqueue gate for VentureOps Mission Mode."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.agent_bus.bus import create_task, init_db, list_tasks
from runtime.agent_bus.mission_tasks import (
    MISSION_ALLOWED_WRITE_ROOTS,
    MISSION_TASK_TYPE,
    build_mission_task_packet,
    validate_mission_task_packet,
)
from runtime.ventureops.mission_activation_readiness import build_mission_activation_readiness


ENQUEUE_APPROVAL_FILENAME = "mission-agent-bus-enqueue-approval-approved.json"
ENQUEUE_MARKER_FILENAME = "mission-agent-bus-enqueue-consumption.json"
ENQUEUE_APPROVAL_TYPE = "ventureops-mission-agent-bus-enqueue-approval"
ENQUEUE_MARKER_TYPE = "ventureops-mission-agent-bus-enqueue-marker"
SURFACE_ID = "ventureops_mission_agent_bus_enqueue_gate"
APPROVED_NEXT_STEP = "agent_bus_mission_dry_review_enqueue_only"
DEFAULT_RECIPIENT = "Codex"
ADDRESSABLE_RECIPIENTS = ("Codex", "Hermes", "OpenClaw")

FORBIDDEN_TRUE_AUTHORIZATION_FIELDS = (
    "mission_activation_execution_authorized",
    "aor_dispatch_authorized",
    "runtime_task_claim_authorized",
    "workflow_dispatch_authorized",
    "workflow_evolution_apply_authorized",
    "provider_calls_authorized",
    "browser_actions_authorized",
    "browser_skill_activation_authorized",
    "external_side_effects_authorized",
    "crm_or_payment_mutation_authorized",
    "live_trading_authorized",
    "protected_file_edit_authorized",
    "canonical_promotion_authorized",
    "credential_or_secret_read_authorized",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_id(value: str) -> str:
    normalized = "".join(char if char.isalnum() or char in {"-", "_", "."} else "-" for char in value.strip())
    collapsed = "-".join(part for part in normalized.split("-") if part)
    return collapsed[:96] or "mission"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not contain a JSON object")
    return data


def _vault_relative(path: Path, vault_root: Path) -> str:
    try:
        return path.resolve().relative_to(vault_root.resolve()).as_posix()
    except ValueError:
        return str(path)


def _resolve_workspace(vault_root: Path, mission_workspace: str | Path | None) -> Path:
    if mission_workspace is None:
        readiness = build_mission_activation_readiness(vault_root)
        path = readiness.get("mission_workspace_path")
        if path:
            return (vault_root / str(path)).resolve()
        return (
            vault_root
            / "07_LOGS"
            / "VentureOps-Missions"
            / "2026-05-13_mission-chase-ai-runtime-governance-kit-dry-run"
        ).resolve()
    raw = Path(mission_workspace)
    return raw.resolve() if raw.is_absolute() else (vault_root / raw).resolve()


def _resolve_under_vault(vault_root: Path, path: str | Path) -> tuple[Path | None, str | None, str | None]:
    raw = Path(path)
    resolved = raw.resolve() if raw.is_absolute() else (vault_root / raw).resolve()
    try:
        relative = resolved.relative_to(vault_root.resolve())
    except ValueError:
        return None, None, f"path escapes vault root: {path}"
    return resolved, relative.as_posix(), None


def default_enqueue_approval_path(workspace: str | Path) -> Path:
    return Path(workspace) / ENQUEUE_APPROVAL_FILENAME


def default_enqueue_marker_path(workspace: str | Path) -> Path:
    return Path(workspace) / ENQUEUE_MARKER_FILENAME


def _task_id(*, mission_id: str, enqueue_id: str) -> str:
    return f"mission-dry-review-{_safe_id(mission_id)}-{_safe_id(enqueue_id)[:48]}"


def _work_fingerprint(*, mission_id: str, enqueue_id: str) -> str:
    return f"ventureops-mission:{_safe_id(mission_id)}:agent-bus-enqueue:{_safe_id(enqueue_id)}"


def _activation_artifact_path(readiness: dict[str, Any], workspace: Path, vault_root: Path) -> str:
    path = readiness.get("activation_approval_artifact_path")
    if path:
        return str(path)
    return _vault_relative(workspace / "activation-approval-approved.json", vault_root)


def _build_packet_preview(
    *,
    vault_root: Path,
    readiness: dict[str, Any],
    workspace: Path,
    enqueue_id: str,
    recipient: str,
    created_at: str | None = None,
) -> dict[str, Any]:
    mission_id = str(readiness.get("mission_id") or "")
    workspace_rel = _vault_relative(workspace, vault_root)
    approval_path = _activation_artifact_path(readiness, workspace, vault_root)
    packet = build_mission_task_packet(
        mission_id=mission_id,
        mission_workspace_path=workspace_rel,
        activation_approval_packet_path=approval_path,
        sender="Operator",
        recipient=recipient,
        task_id=_task_id(mission_id=mission_id, enqueue_id=enqueue_id),
        run_id=f"mission-bus-enqueue-{_safe_id(enqueue_id)}",
        created_at=created_at or _now_utc(),
        request=(
            "Review the activation-ready VentureOps Mission Mode dry-run workspace and "
            "return local proposal/risk/completion evidence only. Do not claim broader "
            "authority, activate the mission, dispatch AOR, enqueue follow-up tasks, call "
            "providers, use browsers, send externally, mutate CRM/payment systems, trade, "
            "read credentials, or promote canonical state."
        ),
        expected_output=(
            "A bounded local mission dry-review result with proof references, blocker "
            "list, and explicit confirmation that no external or high-impact side effects occurred."
        ),
        artifacts=[
            workspace_rel,
            approval_path,
            str(readiness.get("activation_approval_consumption_marker_path") or ""),
            str(readiness.get("manifest_promotion_review_artifact_path") or ""),
            str(readiness.get("manifest_promotion_review_marker_path") or ""),
        ],
        notes="Exact-once Agent Bus enqueue gate preview; task claim and workflow execution remain separate.",
    )
    validation = validate_mission_task_packet(packet)
    if not validation.get("ok"):
        raise ValueError("; ".join(str(error) for error in validation.get("errors") or []))
    return packet


def build_mission_agent_bus_enqueue_approval(
    vault_root: str | Path,
    *,
    mission_workspace: str | Path | None = None,
    enqueue_id: str | None = None,
    approved_by: str = "operator",
    operator_approval_statement: str | None = None,
    recipient: str = DEFAULT_RECIPIENT,
    priority: str = "normal",
    approved_at: str | None = None,
) -> dict[str, Any]:
    """Build an Agent Bus enqueue approval artifact without writing it."""

    root = Path(vault_root).resolve()
    workspace = _resolve_workspace(root, mission_workspace)
    readiness = build_mission_activation_readiness(root, mission_workspace=workspace)
    errors = [str(error) for error in readiness.get("blockers") or []]
    mission_id = str(readiness.get("mission_id") or "")
    if readiness.get("ready_for_activation") is not True:
        errors.append("mission_activation_readiness_must_be_ready_before_agent_bus_enqueue")
    if readiness.get("ready_for_aor_dispatch") is not True:
        errors.append("mission_aor_dispatch_readiness_must_be_ready_before_agent_bus_enqueue")
    if recipient not in ADDRESSABLE_RECIPIENTS:
        errors.append(f"recipient must be one of {list(ADDRESSABLE_RECIPIENTS)}")
    if priority not in {"low", "normal", "high", "critical"}:
        errors.append("priority must be one of ['low', 'normal', 'high', 'critical']")
    statement = " ".join(str(operator_approval_statement or "").strip().split())
    if not statement:
        errors.append("operator_approval_statement is required")

    enqueue_id = _safe_id(
        enqueue_id
        or f"{mission_id or 'mission'}-agent-bus-enqueue-{datetime.now(timezone.utc).date().isoformat()}"
    )
    approved_by = str(approved_by or "operator").strip() or "operator"
    packet: dict[str, Any] = {}
    if mission_id and recipient in ADDRESSABLE_RECIPIENTS:
        try:
            packet = _build_packet_preview(
                vault_root=root,
                readiness=readiness,
                workspace=workspace,
                enqueue_id=enqueue_id,
                recipient=recipient,
                created_at=approved_at,
            )
        except Exception as exc:
            errors.append(f"mission_task_packet_preview_invalid:{exc}")
    task_id = str(packet.get("task_id") or _task_id(mission_id=mission_id or "mission", enqueue_id=enqueue_id))
    work_fingerprint = _work_fingerprint(mission_id=mission_id or "mission", enqueue_id=enqueue_id)
    artifact = {
        "schema_version": "0.1",
        "type": ENQUEUE_APPROVAL_TYPE,
        "enqueue_id": enqueue_id,
        "approval_decision": "approved" if not errors else "pending",
        "approval_status": "approved" if not errors else "blocked",
        "approved_by": approved_by,
        "approved_at": approved_at or _now_utc(),
        "operator_approval_statement": statement,
        "mission_id": mission_id,
        "mission_workspace_path": _vault_relative(workspace, root),
        "readiness_status_at_approval": readiness.get("readiness_status"),
        "ready_for_activation_at_approval": readiness.get("ready_for_activation") is True,
        "ready_for_aor_dispatch_at_approval": readiness.get("ready_for_aor_dispatch") is True,
        "approved_next_step": APPROVED_NEXT_STEP,
        "recipient": recipient,
        "priority": priority,
        "agent_bus_task_id": task_id,
        "work_fingerprint": work_fingerprint,
        "mission_task_packet_preview": packet,
        "mission_task_packet_digest": _sha256(packet) if packet else "",
        "approved_scope": [
            "write one local Agent Bus mission dry-review task addressed to the selected runtime",
            "keep the task open and unclaimed; this gate does not start a daemon or runtime process",
            "allow only declared local write roots for a future dry-review result",
            "preserve the mission manifest draft file and workflow-evolution proposal pending/unapplied",
        ],
        "required_acknowledgements": [
            "Mission activation readiness must be ready before enqueue",
            "Agent Bus enqueue is local coordination state only and is not mission activation",
            "AOR workflow dispatch, task claim, runtime process start, provider calls, browser actions, external sends, CRM/payment mutation, live trading, credential reads, and canonical promotion remain forbidden",
            "Duplicate enqueue is blocked by an exact-once marker and active task fingerprint check",
        ],
        "consumption_policy": "exact_once",
        "consumable": not errors,
        "agent_bus_task_write_authorized": not errors,
        "mission_activation_execution_authorized": False,
        "aor_dispatch_authorized": False,
        "runtime_task_claim_authorized": False,
        "workflow_dispatch_authorized": False,
        "workflow_evolution_apply_authorized": False,
        "provider_calls_authorized": False,
        "browser_actions_authorized": False,
        "browser_skill_activation_authorized": False,
        "external_side_effects_authorized": False,
        "crm_or_payment_mutation_authorized": False,
        "live_trading_authorized": False,
        "protected_file_edit_authorized": False,
        "canonical_promotion_authorized": False,
        "credential_or_secret_read_authorized": False,
        "context_errors": list(dict.fromkeys(errors)),
    }
    artifact["enqueue_digest"] = _sha256({key: value for key, value in artifact.items() if key != "enqueue_digest"})
    return artifact


def validate_mission_agent_bus_enqueue_approval(
    approval: dict[str, Any],
    *,
    vault_root: str | Path,
    mission_workspace: str | Path | None = None,
) -> dict[str, Any]:
    """Validate an Agent Bus enqueue approval artifact."""

    root = Path(vault_root).resolve()
    workspace = _resolve_workspace(root, mission_workspace)
    errors: list[str] = []
    manifest_path = workspace / "mission-manifest.json"
    if manifest_path.exists():
        try:
            manifest = _load_json(manifest_path)
            mission_id = str(manifest.get("mission_id") or "")
        except Exception as exc:
            mission_id = ""
            errors.append(f"mission_manifest_invalid:{exc}")
    else:
        mission_id = ""
        errors.append("mission_manifest_missing")
    required = {
        "schema_version",
        "type",
        "enqueue_id",
        "approval_decision",
        "approval_status",
        "approved_by",
        "approved_at",
        "operator_approval_statement",
        "mission_id",
        "mission_workspace_path",
        "approved_next_step",
        "recipient",
        "priority",
        "agent_bus_task_id",
        "work_fingerprint",
        "mission_task_packet_preview",
        "mission_task_packet_digest",
        "consumption_policy",
        "consumable",
        "agent_bus_task_write_authorized",
    }
    errors.extend(f"approval missing required field: {field}" for field in sorted(required - set(approval)))
    if approval.get("type") != ENQUEUE_APPROVAL_TYPE:
        errors.append("approval type is not ventureops-mission-agent-bus-enqueue-approval")
    if approval.get("approval_decision") != "approved":
        errors.append("approval_decision must be approved")
    if approval.get("approval_status") != "approved":
        errors.append("approval_status must be approved")
    if not str(approval.get("operator_approval_statement") or "").strip():
        errors.append("operator_approval_statement is required")
    if approval.get("mission_id") != mission_id:
        errors.append("approval mission_id does not match mission workspace")
    if approval.get("approved_next_step") != APPROVED_NEXT_STEP:
        errors.append(f"approved_next_step must be {APPROVED_NEXT_STEP}")
    if approval.get("recipient") not in ADDRESSABLE_RECIPIENTS:
        errors.append(f"recipient must be one of {list(ADDRESSABLE_RECIPIENTS)}")
    if approval.get("priority") not in {"low", "normal", "high", "critical"}:
        errors.append("priority must be one of ['low', 'normal', 'high', 'critical']")
    if approval.get("ready_for_activation_at_approval") is not True:
        errors.append("ready_for_activation_at_approval must be true")
    if approval.get("ready_for_aor_dispatch_at_approval") is not True:
        errors.append("ready_for_aor_dispatch_at_approval must be true")
    if approval.get("agent_bus_task_write_authorized") is not True:
        errors.append("agent_bus_task_write_authorized must be true")
    for field in FORBIDDEN_TRUE_AUTHORIZATION_FIELDS:
        if approval.get(field) is not False:
            errors.append(f"{field} must be false")
    if approval.get("consumption_policy") != "exact_once":
        errors.append("consumption_policy must be exact_once")
    if approval.get("consumable") is not True:
        errors.append("consumable must be true")

    packet = approval.get("mission_task_packet_preview")
    if not isinstance(packet, dict):
        errors.append("mission_task_packet_preview must be an object")
    else:
        packet_validation = validate_mission_task_packet(packet)
        errors.extend(f"mission_task_packet_preview:{error}" for error in packet_validation.get("errors") or [])
        if packet.get("mission_id") != mission_id:
            errors.append("mission_task_packet_preview mission_id does not match mission workspace")
        if packet.get("to") != approval.get("recipient"):
            errors.append("mission_task_packet_preview recipient does not match approval recipient")
        if packet.get("task_id") != approval.get("agent_bus_task_id"):
            errors.append("mission_task_packet_preview task_id does not match approval task id")
        if approval.get("mission_task_packet_digest") != _sha256(packet):
            errors.append("mission_task_packet_digest mismatch")

    workspace_value = str(approval.get("mission_workspace_path") or "")
    if workspace_value:
        resolved = (root / workspace_value).resolve() if not Path(workspace_value).is_absolute() else Path(workspace_value).resolve()
        if resolved != workspace.resolve():
            errors.append("approval mission_workspace_path does not match requested mission workspace")
    else:
        errors.append("mission_workspace_path is required")
    return {"ok": not errors, "errors": list(dict.fromkeys(errors))}


def _marker_payload(
    *,
    status: str,
    approval: dict[str, Any],
    approval_path: Path,
    marker_path: Path,
    operator_id: str,
    agent_bus_task_written: bool,
    stored_task: dict[str, Any] | None = None,
    error: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "type": ENQUEUE_MARKER_TYPE,
        "status": status,
        "surface": SURFACE_ID,
        "enqueue_id": approval.get("enqueue_id"),
        "approval_path": str(approval_path).replace("\\", "/"),
        "approval_digest": approval.get("enqueue_digest"),
        "mission_id": approval.get("mission_id"),
        "mission_workspace_path": approval.get("mission_workspace_path"),
        "recipient": approval.get("recipient"),
        "priority": approval.get("priority"),
        "agent_bus_task_id": approval.get("agent_bus_task_id"),
        "work_fingerprint": approval.get("work_fingerprint"),
        "operator_id": operator_id,
        "consumed_at": _now_utc(),
        "agent_bus_task_written": agent_bus_task_written,
        "runtime_task_claimed": False,
        "runtime_process_started": False,
        "workflow_dispatched": False,
        "mission_activation_performed": False,
        "aor_dispatch_performed": False,
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
        "stored_task_snapshot": stored_task or {},
        "error": error,
        "marker_path": str(marker_path).replace("\\", "/"),
    }


def validate_mission_agent_bus_enqueue_marker(
    marker: dict[str, Any],
    *,
    approval: dict[str, Any],
    vault_root: str | Path,
    mission_workspace: str | Path | None = None,
) -> dict[str, Any]:
    """Validate an exact-once Agent Bus enqueue marker."""

    errors: list[str] = []
    approval_validation = validate_mission_agent_bus_enqueue_approval(
        approval,
        vault_root=vault_root,
        mission_workspace=mission_workspace,
    )
    errors.extend(str(error) for error in approval_validation.get("errors") or [])
    if marker.get("type") != ENQUEUE_MARKER_TYPE:
        errors.append("marker type is not ventureops-mission-agent-bus-enqueue-marker")
    if marker.get("status") != "executed":
        errors.append("marker status must be executed")
    if marker.get("enqueue_id") != approval.get("enqueue_id"):
        errors.append("marker enqueue_id does not match approval")
    if marker.get("approval_digest") != approval.get("enqueue_digest"):
        errors.append("marker approval_digest does not match approval")
    if marker.get("mission_id") != approval.get("mission_id"):
        errors.append("marker mission_id does not match approval")
    if marker.get("recipient") != approval.get("recipient"):
        errors.append("marker recipient does not match approval")
    if marker.get("priority") != approval.get("priority"):
        errors.append("marker priority does not match approval")
    if marker.get("agent_bus_task_id") != approval.get("agent_bus_task_id"):
        errors.append("marker agent_bus_task_id does not match approval")
    if marker.get("work_fingerprint") != approval.get("work_fingerprint"):
        errors.append("marker work_fingerprint does not match approval")
    if marker.get("agent_bus_task_written") is not True:
        errors.append("agent_bus_task_written must be true")
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
            errors.append(f"{field} must be false")
    return {"ok": not errors, "errors": list(dict.fromkeys(errors))}


def _existing_active_task(
    vault_root: Path,
    *,
    task_id: str,
    recipient: str,
    work_fingerprint: str,
) -> dict[str, Any] | None:
    try:
        for task in list_tasks(vault_root, recipient=recipient):
            if task.get("task_id") == task_id:
                return task
            if (
                str(task.get("work_fingerprint") or "") == work_fingerprint
                and str(task.get("status") or "") in {"open", "claimed", "in_progress", "blocked", "review"}
            ):
                return task
    except Exception:
        return None
    return None


def _write_boundary_after_enqueue(
    *,
    workspace: Path,
    approval: dict[str, Any],
    marker_path: Path,
) -> None:
    boundary_path = workspace / "run-boundary.json"
    if not boundary_path.exists():
        return
    boundary = _load_json(boundary_path)
    boundary.update(
        {
            "agent_bus_task_written": True,
            "agent_bus_enqueue_gate_consumed": True,
            "agent_bus_enqueue_approval_id": approval.get("enqueue_id"),
            "agent_bus_enqueue_task_id": approval.get("agent_bus_task_id"),
            "agent_bus_enqueue_marker_path": marker_path.name,
            "agent_bus_task_claimed": False,
            "aor_dispatch_performed": False,
            "mission_activation_performed": False,
            "workflow_mutation_performed": False,
            "workflow_evolution_applied": False,
            "provider_call_performed": False,
            "browser_action_performed": False,
            "external_send_performed": False,
            "crm_or_payment_mutation_performed": False,
            "live_trading_performed": False,
            "canonical_promotion_performed": False,
            "notes": (
                "Activation, manifest-promotion/workflow-evolution review, and exact-once "
                "Agent Bus enqueue gates are consumed. One local Agent Bus dry-review task "
                "was written; it remains unclaimed and no AOR dispatch, mission activation, "
                "workflow evolution apply, provider/browser action, external send, CRM/payment "
                "mutation, live trading, credential read, or canonical promotion occurred."
            ),
        }
    )
    boundary_path.write_text(json.dumps(boundary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _base_response(
    *,
    vault_root: Path,
    workspace: Path,
    approval_path: Path,
    marker_path: Path,
    approval: dict[str, Any],
    blockers: list[str],
    approval_artifact_written: bool = False,
    enqueue_consumed: bool = False,
    exact_once_marker_written: bool = False,
    agent_bus_task_written: bool = False,
    duplicate_blocked: bool = False,
    preview_only: bool = False,
    stored_task: dict[str, Any] | None = None,
    readiness_after_enqueue: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ok": not blockers and (preview_only or enqueue_consumed or approval_artifact_written),
        "schema_version": "0.1",
        "surface": SURFACE_ID,
        "status": (
            "preview_ready"
            if preview_only and not blockers
            else "agent_bus_enqueue_consumed"
            if enqueue_consumed
            else "enqueue_approval_artifact_written"
            if approval_artifact_written and not blockers
            else "blocked"
        ),
        "generated_at": _now_utc(),
        "mission_id": approval.get("mission_id"),
        "mission_workspace_path": _vault_relative(workspace, vault_root),
        "enqueue_id": approval.get("enqueue_id"),
        "recipient": approval.get("recipient"),
        "priority": approval.get("priority"),
        "agent_bus_task_id": approval.get("agent_bus_task_id"),
        "work_fingerprint": approval.get("work_fingerprint"),
        "approval_artifact_path": _vault_relative(approval_path, vault_root),
        "enqueue_marker_path": _vault_relative(marker_path, vault_root),
        "approval_artifact_written": approval_artifact_written,
        "enqueue_consumed": enqueue_consumed,
        "exact_once_marker_written": exact_once_marker_written,
        "agent_bus_task_written": agent_bus_task_written,
        "runtime_task_claimed": False,
        "runtime_process_started": False,
        "workflow_dispatched": False,
        "mission_activation_performed": False,
        "aor_dispatch_performed": False,
        "duplicate_blocked_before_task_write": duplicate_blocked,
        "preview_only": preview_only,
        "stored_task": stored_task or {},
        "readiness_after_enqueue": readiness_after_enqueue,
        "blockers": list(dict.fromkeys(blockers)),
        "approval_artifact": approval if preview_only else None,
        "authority_boundary": {
            "agent_bus_task_write_allowed": True,
            "exact_once_marker_write_allowed": True,
            "mission_activation_performed": False,
            "aor_dispatch_performed": False,
            "runtime_task_claimed": False,
            "runtime_process_started": False,
            "workflow_dispatched": False,
            "workflow_evolution_applied": False,
            "provider_call_performed": False,
            "browser_action_performed": False,
            "browser_skill_activated": False,
            "external_send_performed": False,
            "crm_or_payment_mutation_performed": False,
            "live_trading_performed": False,
            "protected_file_edit_performed": False,
            "canonical_promotion_performed": False,
            "credential_or_secret_read_performed": False,
        },
    }


def consume_mission_agent_bus_enqueue_gate(
    vault_root: str | Path,
    *,
    mission_workspace: str | Path | None = None,
    approval_path: str | Path | None = None,
    marker_path: str | Path | None = None,
    enqueue_id: str | None = None,
    approved_by: str = "operator",
    operator_approval_statement: str | None = None,
    recipient: str = DEFAULT_RECIPIENT,
    priority: str = "normal",
    write_approval: bool = False,
    consume: bool = False,
    enqueue_task: bool = False,
) -> dict[str, Any]:
    """Write and/or consume a Mission Agent Bus enqueue approval exactly once."""

    root = Path(vault_root).resolve()
    workspace = _resolve_workspace(root, mission_workspace)
    raw_approval = approval_path or default_enqueue_approval_path(workspace)
    raw_marker = marker_path or default_enqueue_marker_path(workspace)
    approval_target, _approval_rel, approval_error = _resolve_under_vault(root, raw_approval)
    marker_target, _marker_rel, marker_error = _resolve_under_vault(root, raw_marker)
    blockers: list[str] = []
    if approval_error:
        blockers.append(approval_error.replace("path", "approval_path"))
    if marker_error:
        blockers.append(marker_error.replace("path", "marker_path"))
    if approval_target is None:
        approval_target = root / "blocked-mission-agent-bus-enqueue-approval.json"
    if marker_target is None:
        marker_target = root / "blocked-mission-agent-bus-enqueue-marker.json"

    if consume and marker_target.exists():
        approval = (
            _load_json(approval_target)
            if approval_target.exists()
            else build_mission_agent_bus_enqueue_approval(
                root,
                mission_workspace=workspace,
                enqueue_id=enqueue_id,
                approved_by=approved_by,
                operator_approval_statement=operator_approval_statement,
                recipient=recipient,
                priority=priority,
            )
        )
        return _base_response(
            vault_root=root,
            workspace=workspace,
            approval_path=approval_target,
            marker_path=marker_target,
            approval=approval,
            blockers=[*blockers, "exact_once_marker_already_present"],
            duplicate_blocked=True,
        )

    approval = build_mission_agent_bus_enqueue_approval(
        root,
        mission_workspace=workspace,
        enqueue_id=enqueue_id,
        approved_by=approved_by,
        operator_approval_statement=operator_approval_statement,
        recipient=recipient,
        priority=priority,
    )
    approval_validation = validate_mission_agent_bus_enqueue_approval(
        approval,
        vault_root=root,
        mission_workspace=workspace,
    )
    blockers.extend(str(error) for error in approval_validation.get("errors") or [])

    if enqueue_task and not consume:
        blockers.append("enqueue_task_requires_consume")
    if consume and not enqueue_task:
        blockers.append("consume_requires_enqueue_task")
    if not write_approval and not consume:
        return _base_response(
            vault_root=root,
            workspace=workspace,
            approval_path=approval_target,
            marker_path=marker_target,
            approval=approval,
            blockers=blockers,
            preview_only=True,
        )

    approval_artifact_written = False
    if write_approval:
        if approval_target.exists():
            blockers.append("enqueue_approval_artifact_already_exists")
        if not blockers:
            approval_target.parent.mkdir(parents=True, exist_ok=True)
            with approval_target.open("x", encoding="utf-8") as handle:
                json.dump(approval, handle, indent=2, sort_keys=True)
                handle.write("\n")
            approval_artifact_written = True
    else:
        if not approval_target.exists():
            blockers.append("enqueue_approval_artifact_missing")
        else:
            approval = _load_json(approval_target)
            stored_validation = validate_mission_agent_bus_enqueue_approval(
                approval,
                vault_root=root,
                mission_workspace=workspace,
            )
            blockers.extend(str(error) for error in stored_validation.get("errors") or [])

    stored_task: dict[str, Any] | None = None
    exact_once_marker_written = False
    agent_bus_task_written = False
    enqueue_consumed = False
    readiness_after: dict[str, Any] | None = None
    if consume and not blockers:
        existing_task = _existing_active_task(
            root,
            task_id=str(approval.get("agent_bus_task_id") or ""),
            recipient=str(approval.get("recipient") or DEFAULT_RECIPIENT),
            work_fingerprint=str(approval.get("work_fingerprint") or ""),
        )
        if existing_task is not None:
            return _base_response(
                vault_root=root,
                workspace=workspace,
                approval_path=approval_target,
                marker_path=marker_target,
                approval=approval,
                blockers=["active_agent_bus_mission_task_already_present"],
                duplicate_blocked=True,
                stored_task=existing_task,
            )

        marker_target.parent.mkdir(parents=True, exist_ok=True)
        marker = _marker_payload(
            status="executing",
            approval=approval,
            approval_path=approval_target,
            marker_path=marker_target,
            operator_id=str(approved_by or "operator").strip() or "operator",
            agent_bus_task_written=False,
        )
        with marker_target.open("x", encoding="utf-8") as handle:
            json.dump(marker, handle, indent=2, sort_keys=True)
            handle.write("\n")
        exact_once_marker_written = True

        if enqueue_task:
            try:
                packet = approval.get("mission_task_packet_preview")
                if not isinstance(packet, dict):
                    raise RuntimeError("mission_task_packet_preview_missing")
                init_db(root)
                notes = "\n".join(
                    [
                        f"task_type: {MISSION_TASK_TYPE}",
                        f"mission_id: {approval.get('mission_id')}",
                        f"enqueue_id: {approval.get('enqueue_id')}",
                        f"mission_task_packet_digest: {approval.get('mission_task_packet_digest')}",
                        "boundary: exact-once local Agent Bus enqueue only; no task claim, AOR dispatch, provider/browser/external action, credential read, or canonical promotion by this gate.",
                    ]
                )
                created = create_task(
                    root,
                    task_id=str(approval.get("agent_bus_task_id")),
                    sender="Operator",
                    recipient=str(approval.get("recipient") or DEFAULT_RECIPIENT),
                    intent="TASK",
                    priority=str(approval.get("priority") or "normal"),
                    request=str(packet.get("request") or "")[:1200],
                    expected_output=str(packet.get("expected_output") or "")[:1200],
                    notes=notes,
                    ingress_context={
                        "source_platform": "ventureops-mission",
                        "source_channel_class": "mission_mode",
                        "conversation_key": f"ventureops-mission:{approval.get('mission_id')}",
                        "origin_message_id": str(approval.get("enqueue_id") or ""),
                        "control_plane_route": "ventureops-mission-agent-bus-enqueue",
                    },
                    work_fingerprint=str(approval.get("work_fingerprint") or ""),
                    execution_constraints={
                        "allow_shell_commands": False,
                        "allow_live_subprocess": False,
                        "write_policy": "declared-paths",
                        "allowed_write_paths": list(MISSION_ALLOWED_WRITE_ROOTS),
                    },
                    allow_external_sender=True,
                )
                if not created.get("created"):
                    raise RuntimeError(f"agent_bus_task_create_failed:{created.get('reason')}")
                matches = [
                    task
                    for task in list_tasks(root, recipient=str(approval.get("recipient") or DEFAULT_RECIPIENT))
                    if task.get("task_id") == approval.get("agent_bus_task_id")
                ]
                stored_task = matches[0] if matches else {}
                agent_bus_task_written = True
                _write_boundary_after_enqueue(
                    workspace=workspace,
                    approval=approval,
                    marker_path=marker_target,
                )
            except Exception as exc:
                marker = _marker_payload(
                    status="execution_failed",
                    approval=approval,
                    approval_path=approval_target,
                    marker_path=marker_target,
                    operator_id=str(approved_by or "operator").strip() or "operator",
                    agent_bus_task_written=False,
                    error=str(exc),
                )
                marker_target.write_text(json.dumps(marker, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                return _base_response(
                    vault_root=root,
                    workspace=workspace,
                    approval_path=approval_target,
                    marker_path=marker_target,
                    approval=approval,
                    blockers=[f"agent_bus_enqueue_failed:{exc}"],
                    stored_task=stored_task,
                )

        marker = _marker_payload(
            status="executed",
            approval=approval,
            approval_path=approval_target,
            marker_path=marker_target,
            operator_id=str(approved_by or "operator").strip() or "operator",
            agent_bus_task_written=agent_bus_task_written,
            stored_task=stored_task,
        )
        marker_validation = validate_mission_agent_bus_enqueue_marker(
            marker,
            approval=approval,
            vault_root=root,
            mission_workspace=workspace,
        )
        if marker_validation.get("ok") is not True:
            return _base_response(
                vault_root=root,
                workspace=workspace,
                approval_path=approval_target,
                marker_path=marker_target,
                approval=approval,
                blockers=[str(error) for error in marker_validation.get("errors") or []],
                stored_task=stored_task,
            )
        marker_target.write_text(json.dumps(marker, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        enqueue_consumed = True
        readiness_after = build_mission_activation_readiness(root, mission_workspace=workspace)

    return _base_response(
        vault_root=root,
        workspace=workspace,
        approval_path=approval_target,
        marker_path=marker_target,
        approval=approval,
        blockers=blockers,
        approval_artifact_written=approval_artifact_written,
        enqueue_consumed=enqueue_consumed,
        exact_once_marker_written=exact_once_marker_written,
        agent_bus_task_written=agent_bus_task_written,
        stored_task=stored_task,
        readiness_after_enqueue=readiness_after,
    )


def load_mission_agent_bus_enqueue_state(
    vault_root: str | Path,
    *,
    mission_workspace: str | Path | None = None,
    approval_path: str | Path | None = None,
    marker_path: str | Path | None = None,
) -> dict[str, Any]:
    """Load and validate Mission Agent Bus enqueue state."""

    root = Path(vault_root).resolve()
    workspace = _resolve_workspace(root, mission_workspace)
    approval_target = (
        Path(approval_path)
        if approval_path is not None
        else default_enqueue_approval_path(workspace)
    )
    marker_target = (
        Path(marker_path)
        if marker_path is not None
        else default_enqueue_marker_path(workspace)
    )
    if not approval_target.is_absolute():
        approval_target = (root / approval_target).resolve()
    if not marker_target.is_absolute():
        marker_target = (root / marker_target).resolve()

    errors: list[str] = []
    approval_present = approval_target.exists()
    marker_present = marker_target.exists()
    approval: dict[str, Any] | None = None
    marker: dict[str, Any] | None = None
    approval_valid = False
    marker_valid = False
    stored_task: dict[str, Any] | None = None

    if approval_present:
        try:
            approval = _load_json(approval_target)
            validation = validate_mission_agent_bus_enqueue_approval(
                approval,
                vault_root=root,
                mission_workspace=workspace,
            )
            approval_valid = bool(validation.get("ok"))
            errors.extend(str(error) for error in validation.get("errors") or [])
        except Exception as exc:
            errors.append(f"enqueue_approval_invalid:{exc}")
    if marker_present:
        try:
            marker = _load_json(marker_target)
            if approval is None:
                errors.append("enqueue_marker_present_without_approval_artifact")
            else:
                validation = validate_mission_agent_bus_enqueue_marker(
                    marker,
                    approval=approval,
                    vault_root=root,
                    mission_workspace=workspace,
                )
                marker_valid = bool(validation.get("ok"))
                errors.extend(str(error) for error in validation.get("errors") or [])
                stored_task = _existing_active_task(
                    root,
                    task_id=str(marker.get("agent_bus_task_id") or ""),
                    recipient=str(marker.get("recipient") or DEFAULT_RECIPIENT),
                    work_fingerprint=str(marker.get("work_fingerprint") or ""),
                )
        except Exception as exc:
            errors.append(f"enqueue_marker_invalid:{exc}")

    consumed = approval_valid and marker_valid
    return {
        "ok": not errors,
        "enqueue_approval_artifact_present": approval_present,
        "enqueue_approval_artifact_valid": approval_valid,
        "enqueue_approval_artifact_path": _vault_relative(approval_target, root),
        "enqueue_marker_present": marker_present,
        "enqueue_marker_valid": marker_valid,
        "enqueue_marker_path": _vault_relative(marker_target, root),
        "enqueue_consumed": consumed,
        "agent_bus_task_written": consumed and (marker or {}).get("agent_bus_task_written") is True,
        "agent_bus_task_id": (marker or approval or {}).get("agent_bus_task_id"),
        "recipient": (marker or approval or {}).get("recipient"),
        "priority": (marker or approval or {}).get("priority"),
        "work_fingerprint": (marker or approval or {}).get("work_fingerprint"),
        "runtime_task_claimed": (marker or {}).get("runtime_task_claimed") is True,
        "workflow_dispatched": (marker or {}).get("workflow_dispatched") is True,
        "stored_task_present": stored_task is not None,
        "stored_task": stored_task or {},
        "enqueue_id": (approval or {}).get("enqueue_id"),
        "mission_id": (approval or {}).get("mission_id"),
        "errors": list(dict.fromkeys(errors)),
    }
