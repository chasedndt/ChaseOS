"""Approved Phase 11 Chat -> Agent Bus / AOR dispatch bridge.

This module is the lower-phase backend seam that the read-only Chat runtime
readiness contract points at.  It turns a Chat runtime-bound intent into a
capability-checked Agent Bus task packet and links the packet to an AOR workflow
validation/dispatch record only after explicit approval state is supplied.

Boundary: Chat/Studio callers may use the preview path without side effects.
The dispatch path is approval-gated, writes only the Agent Bus packet plus an
Agent-Activity audit note, and runs AOR in dry-run mode by default.  Live AOR
execution requires the caller to opt in with ``execute_aor=True`` after the same
approval and binding checks pass.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from runtime.agent_bus.bus import create_task, init_db, list_tasks
from runtime.agent_bus.capabilities import CapabilityError, load_runtime_capabilities, resolve_runtime_identity
from runtime.aor.engine import AORRunResult, run_workflow
from runtime.aor.registry import load_manifest
from runtime.aor.role_cards import load_card
from runtime.aor.task_router import classify
from runtime.studio.phase11_chat_runtime_dispatch_readiness import (
    RUNTIME_BOUND_INTENTS,
    build_phase11_chat_runtime_dispatch_readiness,
)

MODEL_VERSION = "studio.phase11_chat_agent_bus_dispatch_bridge.v1"
SURFACE_ID = "phase11_chat_agent_bus_dispatch_bridge"
APPROVAL_CLASS = "studio_chat_runtime_dispatch_approval"
DEFAULT_EXPECTED_OUTPUT = "Reviewable ChaseOS runtime result artifact, not canonical mutation."
BRIDGE_AUDIT_DIR = Path("07_LOGS/Agent-Activity")
HARD_READINESS_BLOCKERS = {
    "selected_runtime_does_not_advertise_task_type",
}


@dataclass(frozen=True)
class BridgeDecision:
    allowed: bool
    reason: str
    approval_id: str | None = None
    decision: str | None = None
    applied_to_execution: bool = False
    binding_checked: bool = False
    expected_binding: dict[str, Any] | None = None
    missing_binding_fields: list[str] | None = None
    mismatched_binding_fields: dict[str, dict[str, str]] | None = None


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(value: str | None) -> str:
    return " ".join(str(value or "").strip().split())


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _approval_field(approval_state: dict[str, Any], field: str) -> str:
    binding = approval_state.get("binding") if isinstance(approval_state.get("binding"), dict) else {}
    aliases = {
        "approval_class": ["approval_class", "class"],
        "surface": ["surface", "surface_id", "bridge", "bridge_surface"],
        "workflow_id": ["workflow_id"],
        "runtime_id": ["runtime_id", "requested_runtime_id", "selected_runtime_id"],
        "task_type": ["task_type", "requested_action", "action", "selected_task_type"],
        "request_digest": ["request_digest", "dispatch_request_digest", "digest"],
    }
    for key in aliases.get(field, [field]):
        value = binding.get(key)
        if value in (None, ""):
            value = approval_state.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return ""


def _approval_decision(
    approval_state: dict[str, Any] | None,
    *,
    expected_binding: dict[str, Any] | None = None,
) -> BridgeDecision:
    if not approval_state:
        return BridgeDecision(False, "operator_runtime_dispatch_approval_missing")
    decision = str(approval_state.get("decision") or approval_state.get("status") or "").strip().lower()
    approval_id = str(approval_state.get("approval_id") or approval_state.get("id") or "").strip() or None
    applied = bool(approval_state.get("applied_to_execution", True))
    if decision not in {"approved", "approve", "allow", "allowed"}:
        return BridgeDecision(False, "operator_runtime_dispatch_approval_not_approved", approval_id, decision, applied)
    if not approval_id:
        return BridgeDecision(False, "operator_runtime_dispatch_approval_id_missing", None, decision, applied)
    if not applied:
        return BridgeDecision(False, "operator_runtime_dispatch_approval_not_applied_to_execution", approval_id, decision, applied)
    if expected_binding:
        expected = {key: str(value or "").strip() for key, value in expected_binding.items()}
        missing = [key for key in expected if not _approval_field(approval_state, key)]
        if missing:
            return BridgeDecision(
                False,
                "operator_runtime_dispatch_approval_binding_missing",
                approval_id,
                decision,
                applied,
                True,
                expected,
                missing,
                None,
            )
        mismatched = {
            key: {"expected": expected_value, "actual": _approval_field(approval_state, key)}
            for key, expected_value in expected.items()
            if _approval_field(approval_state, key) != expected_value
        }
        if mismatched:
            return BridgeDecision(
                False,
                "operator_runtime_dispatch_approval_binding_mismatch",
                approval_id,
                decision,
                applied,
                True,
                expected,
                None,
                mismatched,
            )
        return BridgeDecision(True, "approved", approval_id, decision, applied, True, expected, [], {})
    return BridgeDecision(True, "approved", approval_id, decision, applied)


def _expected_approval_binding(preview: dict[str, Any], workflow_id: str, requested_action: str) -> dict[str, str]:
    readiness = preview.get("chat_readiness") or {}
    digest_proof = readiness.get("request_digest_proof") or {}
    return {
        "approval_class": APPROVAL_CLASS,
        "surface": SURFACE_ID,
        "workflow_id": workflow_id,
        "runtime_id": str((preview.get("summary") or {}).get("selected_runtime_id") or ""),
        "task_type": requested_action,
        "request_digest": str(digest_proof.get("request_digest") or ""),
    }


def _runtime_capability_blockers(vault: Path, runtime_alias_evidence: dict[str, Any], task_type: str, readiness_blockers: list[str]) -> list[str]:
    if not any(item in HARD_READINESS_BLOCKERS for item in readiness_blockers):
        return []
    runtime_name = str(runtime_alias_evidence.get("runtime_name") or "").strip()
    if not runtime_name:
        return ["selected_runtime_does_not_advertise_task_type"]
    try:
        caps = load_runtime_capabilities(runtime_name, vault)
    except Exception:  # noqa: BLE001
        return ["selected_runtime_does_not_advertise_task_type"]
    if caps.can_handle(task_type):
        return []
    return ["selected_runtime_does_not_advertise_task_type"]


def _load_workflow_binding(vault: Path, workflow_id: str, task_type: str, runtime_bus_name: str) -> tuple[dict[str, Any] | None, list[str], dict[str, Any]]:
    blockers: list[str] = []
    evidence: dict[str, Any] = {"workflow_id": workflow_id, "requested_task_type": task_type}
    try:
        manifest = load_manifest(workflow_id, vault)
    except Exception as exc:  # noqa: BLE001
        return None, [f"workflow_manifest_load_error:{exc}"], evidence
    if manifest is None:
        return None, ["workflow_manifest_not_found"], evidence

    evidence.update(
        {
            "manifest_id": manifest.get("id"),
            "manifest_status": manifest.get("status"),
            "manifest_task_type": manifest.get("task_type"),
            "manifest_role_card": manifest.get("role_card"),
            "manifest_runtime_adapter": manifest.get("runtime_adapter"),
            "manifest_permission_ceiling": manifest.get("permission_ceiling"),
            "manifest_approval_rule": manifest.get("approval_rule"),
        }
    )
    if manifest.get("status") != "active":
        blockers.append("workflow_manifest_not_active")
    if str(manifest.get("task_type") or "") != task_type:
        blockers.append("workflow_manifest_task_type_mismatch")

    manifest_adapter = str(manifest.get("runtime_adapter") or "").strip()
    if manifest_adapter:
        try:
            adapter_identity = resolve_runtime_identity(vault, manifest_adapter)
            evidence["manifest_runtime_bus_name"] = adapter_identity.bus_name
            if adapter_identity.bus_name != runtime_bus_name:
                blockers.append("workflow_manifest_runtime_adapter_mismatch")
        except Exception as exc:  # noqa: BLE001
            blockers.append(f"workflow_manifest_runtime_adapter_unknown:{exc}")

    task_type_def = classify(str(manifest.get("task_type") or task_type), vault)
    evidence["task_type_classification"] = task_type_def.get("id")
    evidence["task_type_permission_ceiling"] = task_type_def.get("permission_ceiling")
    if task_type_def.get("id") == "unclassified":
        blockers.append("workflow_task_type_unclassified")

    role_card_id = str(manifest.get("role_card") or "").strip()
    if not role_card_id:
        blockers.append("workflow_role_card_missing")
    else:
        try:
            role_card = load_card(role_card_id, vault)
        except Exception as exc:  # noqa: BLE001
            role_card = None
            blockers.append(f"workflow_role_card_load_error:{exc}")
        if role_card is None:
            blockers.append("workflow_role_card_not_found")
        else:
            evidence["role_card_id"] = role_card.get("id")
            evidence["role_card_allowed_actions"] = role_card.get("allowed_actions", [])
            evidence["role_card_forbidden_actions"] = role_card.get("forbidden_actions", [])

    return manifest, blockers, evidence


def _packet_id(message: str, runtime_bus_name: str, workflow_id: str, task_type: str, approval_id: str | None) -> str:
    digest = _sha256(_canonical_json({
        "message": message,
        "runtime": runtime_bus_name,
        "workflow_id": workflow_id,
        "task_type": task_type,
        "approval_id": approval_id or "preview",
        "bridge": MODEL_VERSION,
    }))
    return f"chat-aor-{digest[:20]}"


def _default_ingress_context(
    *,
    conversation_key: str | None,
    origin_message_id: str | None,
    source_surface: str,
) -> dict[str, Any]:
    context = {
        "source_platform": source_surface,
        "source_channel_class": "phase11_chat",
        "conversation_key": conversation_key or "phase11-chat:runtime-dispatch",
        "origin_message_id": origin_message_id,
        "control_plane_route": "phase11-chat-runtime-dispatch",
    }
    return {key: value for key, value in context.items() if value not in (None, "")}


def _packet_preview(
    *,
    task_id: str,
    runtime_bus_name: str,
    task_type: str,
    message: str,
    expected_output: str,
    ingress_context: dict[str, Any],
    work_fingerprint: str,
    priority: str,
    workflow_id: str,
    approval_id: str | None,
) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "from": "Operator",
        "to": runtime_bus_name,
        "intent": "TASK",
        "priority": priority,
        "status": "open",
        "request": message,
        "expected_output": expected_output,
        "ingress_context": ingress_context,
        "work_fingerprint": work_fingerprint,
        "execution_constraints": {
            "write_policy": "none",
            "allowed_write_paths": [],
            "allow_shell_commands": False,
            "allow_live_subprocess": False,
        },
        "notes": _canonical_json(
            {
                "bridge": SURFACE_ID,
                "workflow_id": workflow_id,
                "approval_id": approval_id,
                "approval_class": APPROVAL_CLASS,
                "aor_dispatch_mode": "dry_run_by_default",
            }
        ),
    }


def _validate_task_packet_shape(packet: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = ["task_id", "from", "to", "intent", "priority", "status", "request", "expected_output"]
    for key in required:
        if not packet.get(key):
            errors.append(f"task_packet_missing_{key}")
    if packet.get("intent") not in {"TASK", "RESULT", "BLOCKER", "REVIEW", "QUESTION", "NOTICE"}:
        errors.append("task_packet_invalid_intent")
    if packet.get("status") not in {"open", "claimed", "in_progress", "blocked", "review", "done", "cancelled", "expired"}:
        errors.append("task_packet_invalid_status")
    if packet.get("priority") not in {"low", "normal", "high", "critical"}:
        errors.append("task_packet_invalid_priority")
    return errors


def _write_bridge_audit(vault: Path, payload: dict[str, Any]) -> str:
    audit_dir = vault / BRIDGE_AUDIT_DIR
    audit_dir.mkdir(parents=True, exist_ok=True)
    task_id = str((payload.get("bus_task") or {}).get("task_id") or "preview")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = audit_dir / f"{stamp}-hermes-optimus-chat-agent-bus-aor-dispatch-{task_id}.md"
    summary = payload.get("summary") or {}
    body = "\n".join(
        [
            "---",
            "runtime: hermes-optimus",
            "lane: Optimus",
            "phase: Phase 9 backend contract proof for Phase 11 Chat",
            f"status: {summary.get('status')}",
            "related:",
            "  - \"[[Hermes-Runtime-Profile]]\"",
            "  - \"[[HERMES]]\"",
            "  - \"[[Agent-Activity-Index]]\"",
            "  - \"[[Runtime-InterAgent-Coordination-Bus]]\"",
            "---",
            "",
            "# Chat to Agent Bus / AOR Dispatch Bridge Audit",
            "",
            "This audit records an approval-gated backend bridge action from a Phase 11 Chat runtime-bound intent into Agent Bus/AOR lower-phase state. Studio/Chat remains an operator surface; the bridge owns the side effect and keeps AOR execution dry-run by default unless explicitly requested.",
            "",
            "```json",
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False),
            "```",
            "",
        ]
    )
    path.write_text(body, encoding="utf-8")
    return str(path.relative_to(vault))


def preview_chat_agent_bus_dispatch_bridge(
    vault_root: str | Path,
    *,
    message: str,
    workflow_id: str,
    requested_runtime_id: str,
    requested_action: str,
    expected_output: str = DEFAULT_EXPECTED_OUTPUT,
    priority: str = "normal",
    ingress_context: dict[str, Any] | None = None,
    conversation_key: str | None = None,
    origin_message_id: str | None = None,
) -> dict[str, Any]:
    """Return the no-side-effect bridge preflight and task packet preview."""

    vault = Path(vault_root).resolve()
    normalized_message = _norm(message)
    blockers: list[str] = []
    warnings: list[str] = []

    readiness = build_phase11_chat_runtime_dispatch_readiness(
        vault,
        message=normalized_message,
        explicit_intent="runtime-task",
        requested_runtime_id=requested_runtime_id,
        requested_action=requested_action,
    )
    if not normalized_message:
        blockers.append("message_required")
    intent = str((readiness.get("summary") or {}).get("intent_class") or "runtime-task")
    if intent not in RUNTIME_BOUND_INTENTS:
        blockers.append("intent_not_runtime_bound_for_dispatch")

    try:
        runtime_identity = resolve_runtime_identity(vault, requested_runtime_id)
        runtime_bus_name = runtime_identity.bus_name
        runtime_alias_evidence = asdict(runtime_identity)
    except Exception as exc:  # noqa: BLE001
        runtime_bus_name = requested_runtime_id
        runtime_alias_evidence = {"input_name": requested_runtime_id, "error": str(exc)}
        blockers.append(f"runtime_identity_resolution_failed:{exc}")

    manifest, binding_blockers, binding_evidence = _load_workflow_binding(
        vault,
        workflow_id,
        requested_action,
        runtime_bus_name,
    )
    blockers.extend(binding_blockers)

    effective_ingress = dict(ingress_context or {}) or _default_ingress_context(
        conversation_key=conversation_key,
        origin_message_id=origin_message_id,
        source_surface="phase11-chat",
    )
    digest_material = {
        "message": normalized_message,
        "runtime": runtime_bus_name,
        "workflow_id": workflow_id,
        "task_type": requested_action,
        "ingress": effective_ingress,
    }
    work_fingerprint = str(effective_ingress.get("work_fingerprint") or f"chat-dispatch:{_sha256(_canonical_json(digest_material))[:24]}")
    task_id = _packet_id(normalized_message, runtime_bus_name, workflow_id, requested_action, None)
    packet = _packet_preview(
        task_id=task_id,
        runtime_bus_name=runtime_bus_name,
        task_type=requested_action,
        message=normalized_message,
        expected_output=expected_output,
        ingress_context=effective_ingress,
        work_fingerprint=work_fingerprint,
        priority=priority,
        workflow_id=workflow_id,
        approval_id=None,
    )
    shape_errors = _validate_task_packet_shape(packet)
    blockers.extend(shape_errors)
    readiness_blockers = [str(item) for item in readiness.get("blocked_reasons") or []]
    hard_readiness_blockers = _runtime_capability_blockers(
        vault,
        runtime_alias_evidence,
        requested_action,
        readiness_blockers,
    )
    blockers.extend(hard_readiness_blockers)
    warnings.extend(item for item in readiness_blockers if item not in hard_readiness_blockers)

    approval_binding = _expected_approval_binding(
        {
            "summary": {"selected_runtime_id": runtime_bus_name},
            "chat_readiness": readiness,
        },
        workflow_id,
        requested_action,
    )

    return {
        "ok": not blockers,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at_utc": _now_utc(),
        "read_only": True,
        "side_effects_performed": False,
        "summary": {
            "status": "preview_ready" if not blockers else "blocked",
            "workflow_id": workflow_id,
            "selected_runtime_id": runtime_bus_name,
            "selected_task_type": requested_action,
            "task_packet_schema_valid": not shape_errors,
            "agent_bus_task_created": False,
            "aor_dispatched": False,
            "aor_dry_run": False,
        },
        "chat_readiness": readiness,
        "runtime_identity": runtime_alias_evidence,
        "workflow_binding": binding_evidence,
        "approval_binding": {
            "required": True,
            "approval_class": APPROVAL_CLASS,
            "expected": approval_binding,
        },
        "task_packet_preview": packet,
        "blocked_reasons": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def dispatch_chat_agent_bus_aor_bridge(
    vault_root: str | Path,
    *,
    message: str,
    workflow_id: str,
    requested_runtime_id: str,
    requested_action: str,
    approval_state: dict[str, Any] | None,
    expected_output: str = DEFAULT_EXPECTED_OUTPUT,
    priority: str = "normal",
    ingress_context: dict[str, Any] | None = None,
    conversation_key: str | None = None,
    origin_message_id: str | None = None,
    execute_aor: bool = False,
    aor_runner: Callable[..., AORRunResult] = run_workflow,
) -> dict[str, Any]:
    """Create the approved Agent Bus task and link it to an AOR dispatch record.

    By default this performs an AOR dry run, not live workflow execution.  Set
    ``execute_aor=True`` only when the caller has explicit lower-phase authority
    to execute the bound workflow.
    """

    vault = Path(vault_root).resolve()
    preview = preview_chat_agent_bus_dispatch_bridge(
        vault,
        message=message,
        workflow_id=workflow_id,
        requested_runtime_id=requested_runtime_id,
        requested_action=requested_action,
        expected_output=expected_output,
        priority=priority,
        ingress_context=ingress_context,
        conversation_key=conversation_key,
        origin_message_id=origin_message_id,
    )
    expected_binding = dict(((preview.get("approval_binding") or {}).get("expected") or {}))
    decision = _approval_decision(approval_state, expected_binding=expected_binding)
    blockers = list(preview.get("blocked_reasons") or [])
    if not decision.allowed:
        blockers.append(decision.reason)

    if blockers:
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "generated_at_utc": _now_utc(),
            "side_effects_performed": False,
            "summary": {
                "status": "blocked",
                "workflow_id": workflow_id,
                "selected_runtime_id": (preview.get("summary") or {}).get("selected_runtime_id"),
                "selected_task_type": requested_action,
                "agent_bus_task_created": False,
                "aor_dispatched": False,
                "aor_dry_run": False,
            },
            "approval": asdict(decision),
            "preview": preview,
            "blocked_reasons": list(dict.fromkeys(blockers)),
        }

    packet = dict(preview["task_packet_preview"])
    packet["task_id"] = _packet_id(
        _norm(message),
        str((preview.get("summary") or {}).get("selected_runtime_id")),
        workflow_id,
        requested_action,
        decision.approval_id,
    )
    packet["notes"] = _canonical_json(
        {
            "bridge": SURFACE_ID,
            "workflow_id": workflow_id,
            "approval_id": decision.approval_id,
            "approval_class": APPROVAL_CLASS,
            "aor_dispatch_mode": "live_execute" if execute_aor else "dry_run",
        }
    )

    init_db(vault)
    created = create_task(
        vault,
        task_id=packet["task_id"],
        sender="Operator",
        recipient=str(packet["to"]),
        intent="TASK",
        priority=priority,
        request=str(packet["request"]),
        expected_output=str(packet["expected_output"]),
        notes=str(packet["notes"]),
        ingress_context=dict(packet.get("ingress_context") or {}),
        work_fingerprint=str(packet.get("work_fingerprint") or ""),
        execution_constraints=dict(packet.get("execution_constraints") or {}),
        allow_external_sender=True,
    )
    if not created.get("created"):
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "generated_at_utc": _now_utc(),
            "side_effects_performed": False,
            "summary": {
                "status": "blocked",
                "workflow_id": workflow_id,
                "selected_runtime_id": packet.get("to"),
                "selected_task_type": requested_action,
                "agent_bus_task_created": False,
                "aor_dispatched": False,
                "aor_dry_run": False,
            },
            "approval": asdict(decision),
            "preview": preview,
            "bus_task": created,
            "blocked_reasons": [f"agent_bus_task_create_failed:{created.get('reason')}"]
        }

    aor_result = aor_runner(
        workflow_id,
        inputs={
            "task_id": packet["task_id"],
            "chat_dispatch_task_id": packet["task_id"],
            "operator_approval_ref": decision.approval_id,
            "message_digest": _sha256(_norm(message)),
        },
        vault_root=vault,
        dry_run=not execute_aor,
        runtime_id=str(packet["to"]).lower(),
    )
    aor_payload = {
        "workflow_id": getattr(aor_result, "workflow_id", workflow_id),
        "status": getattr(aor_result, "status", "unknown"),
        "audit_id": getattr(aor_result, "audit_id", None),
        "stage_reached": getattr(aor_result, "stage_reached", None),
        "dry_run": not execute_aor,
        "manifest_role_card": ((getattr(aor_result, "manifest_snapshot", None) or {}).get("role_card") if getattr(aor_result, "manifest_snapshot", None) else (preview.get("workflow_binding") or {}).get("manifest_role_card")),
        "manifest_task_type": ((getattr(aor_result, "manifest_snapshot", None) or {}).get("task_type") if getattr(aor_result, "manifest_snapshot", None) else (preview.get("workflow_binding") or {}).get("manifest_task_type")),
    }

    persisted = [task for task in list_tasks(vault, recipient=str(packet["to"])) if task.get("task_id") == packet["task_id"]]
    persisted_task = persisted[0] if persisted else {}
    schema_packet = {
        "task_id": persisted_task.get("task_id") or packet["task_id"],
        "run_id": persisted_task.get("run_id") or created.get("run_id") or "created-by-agent-bus",
        "from": persisted_task.get("sender") or "Operator",
        "to": persisted_task.get("recipient") or packet["to"],
        "intent": persisted_task.get("intent") or "TASK",
        "status": persisted_task.get("status") or "open",
        "priority": persisted_task.get("priority") or priority,
        "request": persisted_task.get("request") or packet["request"],
        "expected_output": persisted_task.get("expected_output") or packet["expected_output"],
        "created_at": persisted_task.get("created_at") or _now_utc(),
        "updated_at": persisted_task.get("updated_at") or _now_utc(),
        "work_fingerprint": persisted_task.get("work_fingerprint") or packet.get("work_fingerprint"),
    }
    schema_errors = _validate_task_packet_shape(schema_packet)
    payload = {
        "ok": not schema_errors and str(aor_payload.get("status")) in {"dry_run_ok", "success", "waiting_approval"},
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at_utc": _now_utc(),
        "side_effects_performed": True,
        "summary": {
            "status": "dispatched" if not schema_errors else "dispatched_with_schema_warning",
            "workflow_id": workflow_id,
            "selected_runtime_id": packet.get("to"),
            "selected_task_type": requested_action,
            "task_packet_schema_valid": not schema_errors,
            "agent_bus_task_created": True,
            "aor_dispatched": True,
            "aor_dry_run": not execute_aor,
            "bus_aor_audit_linked": bool(packet.get("task_id") and aor_payload.get("audit_id")),
        },
        "approval": asdict(decision),
        "bus_task": {"created": True, "task_id": packet["task_id"], "stored_task": persisted_task, "schema_packet": schema_packet},
        "aor_dispatch": aor_payload,
        "preview": preview,
        "blocked_reasons": [],
        "warnings": schema_errors,
    }
    payload["audit_path"] = _write_bridge_audit(vault, payload)
    return payload


__all__ = [
    "APPROVAL_CLASS",
    "MODEL_VERSION",
    "SURFACE_ID",
    "dispatch_chat_agent_bus_aor_bridge",
    "preview_chat_agent_bus_dispatch_bridge",
]
