"""Phase 11 Chat schedule intent activation readiness.

This surface inspects an existing ChaseOS schedule intent and prepares a
digest-bound approval packet for a future activation/export executor. It does
not enable schedules, rewrite runtime/schedules, regenerate indexes, mutate
OpenClaw/Hermes cron state, dispatch runtimes, call Discord/providers, or read
credentials.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from runtime.schedules.loader import (
    _parse_yaml_mapping,
    _validate_schedule,
    export_schedules_for_adapter,
    list_schedules,
    load_schedule,
)
from runtime.studio.service import ActionSpec, StudioService


MODEL_VERSION = "studio.phase11_chat_schedule_intent_activation_readiness.v1"
SURFACE_ID = "phase11_chat_schedule_intent_activation_readiness"
PASS_ID = "studio-chat-schedule-intent-activation-readiness"
STATUS_PREVIEW = "READY / ACTIVATION-READINESS PREVIEW / ENABLEMENT BLOCKED"
STATUS_WRITTEN = "COMPLETE / ACTIVATION-APPROVAL QUEUED / ENABLEMENT BLOCKED"
NEXT_RECOMMENDED_PASS = "studio-chat-approved-schedule-activation-executor"
METADATA_BLOCK_KEY = "phase11_chat_schedule_activation_execution_blocked"
AUDIT_ROOT = "runtime/studio/approvals/chat-schedule-activations"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_id(value: str | None) -> str:
    return "".join(c if c.isalnum() or c in {"-", "_"} else "_" for c in str(value or "")) or "unknown"


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _schedule_path(vault: Path, schedule_id: str) -> Path:
    return vault / "runtime" / "schedules" / f"{schedule_id}.yaml"


def _read_schedule_yaml(path: Path) -> tuple[str, list[str]]:
    if not path.exists():
        return "", ["schedule_intent_file_missing"]
    try:
        return path.read_text(encoding="utf-8"), []
    except OSError as exc:
        return "", [f"schedule_intent_file_unreadable:{exc}"]


def _future_enabled_yaml(current_yaml: str) -> tuple[str, list[str]]:
    lines = current_yaml.splitlines()
    changed = False
    future: list[str] = []
    for line in lines:
        if re.fullmatch(r"enabled:\s*false\s*", line):
            future.append("enabled: true")
            changed = True
        else:
            future.append(line)
    if not changed:
        if any(re.fullmatch(r"enabled:\s*true\s*", line) for line in lines):
            return current_yaml.rstrip() + "\n", ["schedule_already_enabled"]
        return current_yaml.rstrip() + "\n", ["schedule_enabled_field_missing_or_not_false"]
    return "\n".join(future).rstrip() + "\n", []


def _activation_digest_material(
    *,
    schedule_id: str,
    target_path: str,
    runtime_adapter_target: str,
    schedule_yaml_sha256: str,
    future_enabled_yaml_sha256: str,
    export_preview_digest: str,
) -> dict[str, Any]:
    return {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "activation_action": "enable_schedule_intent_and_export_readiness",
        "schedule_id": schedule_id,
        "target_path": target_path,
        "runtime_adapter_target": runtime_adapter_target,
        "schedule_yaml_sha256": schedule_yaml_sha256,
        "future_enabled_yaml_sha256": future_enabled_yaml_sha256,
        "export_preview_digest": export_preview_digest,
    }


def _current_enabled_duplicate_blockers(
    *,
    vault: Path,
    schedule_id: str,
    schedule_kind: str,
    workflow_id: str | None,
    command_id: str | None,
    adapter: str,
) -> list[str]:
    blockers: list[str] = []
    try:
        schedules = list_schedules(vault, check_registry=False)
    except Exception as exc:
        return [f"schedule_list_unavailable:{exc}"]

    for item in schedules:
        if item.schedule_id == schedule_id or not item.enabled:
            continue
        targets_adapter = item.runtime_adapter_target == adapter or item.runtime_adapter_fallback == adapter
        if not targets_adapter:
            continue
        if schedule_kind == "command" and item.command_id and item.command_id == command_id:
            blockers.append(f"enabled_duplicate_command_for_adapter:{item.schedule_id}")
        if schedule_kind != "command" and item.workflow_id and item.workflow_id == workflow_id:
            blockers.append(f"enabled_duplicate_workflow_for_adapter:{item.schedule_id}")
    return blockers


def _approval_spec(
    *,
    target_path: str,
    future_enabled_yaml: str,
    activation_digest: str,
    digest_material: dict[str, Any],
    operator_id: str,
) -> ActionSpec:
    return ActionSpec(
        action_type="write_file",
        target_path=target_path,
        content=future_enabled_yaml,
        submitted_by=operator_id,
        note=(
            "Phase 11 Chat schedule activation approval packet. Ambient Studio "
            "execution is blocked; a future governed activation executor must consume it."
        ),
        metadata={
            "phase11_chat_schedule_activation_readiness": True,
            METADATA_BLOCK_KEY: True,
            "source_surface": SURFACE_ID,
            "activation_digest": activation_digest,
            "activation_digest_material": digest_material,
            "schedule_enable_requested": True,
            "schedule_enabled": False,
            "schedule_index_regenerated": False,
            "external_scheduler_changed": False,
            "openclaw_cron_changed": False,
            "hermes_cron_changed": False,
            "agent_bus_task_written": False,
            "runtime_dispatched": False,
            "workflow_dispatched": False,
            "discord_api_called": False,
            "provider_call_performed": False,
            "credential_value_read": False,
        },
    )


def _find_existing(vault: Path, activation_digest: str) -> dict[str, str] | None:
    root = vault / StudioService.APPROVAL_DIR
    if not root.exists():
        return None
    for path in sorted(root.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        metadata = ((payload.get("action_spec") or {}).get("metadata") or {})
        if (
            metadata.get("phase11_chat_schedule_activation_readiness") is True
            and metadata.get("activation_digest") == activation_digest
            and payload.get("status") in {"pending", "approved"}
        ):
            return {"approval_id": str(payload.get("approval_id") or ""), "path": _rel(vault, path)}
    return None


def _next_audit_path(vault: Path, activation_digest: str) -> Path:
    root = vault / AUDIT_ROOT
    root.mkdir(parents=True, exist_ok=True)
    base = root / f"{activation_digest[:20]}.md"
    if not base.exists():
        return base
    for index in range(2, 100):
        candidate = root / f"{activation_digest[:20]}-{index}.md"
        if not candidate.exists():
            return candidate
    raise RuntimeError("could not allocate schedule activation audit path")


def _write_audit(
    *,
    vault: Path,
    approval_id: str,
    approval_path: str,
    schedule_id: str,
    activation_digest: str,
    target_path: str,
    operator_id: str,
) -> str:
    path = _next_audit_path(vault, activation_digest)
    text = "\n".join(
        [
            "---",
            "type: agent-activity",
            "runtime: Codex",
            f"pass_id: {PASS_ID}",
            f"approval_id: {approval_id}",
            f"status: {STATUS_WRITTEN}",
            "---",
            "",
            "# Phase 11 Chat Schedule Intent Activation Readiness",
            "",
            f"operator_id: {operator_id}",
            f"approval_id: {approval_id}",
            f"approval_path: {approval_path}",
            f"schedule_id: {schedule_id}",
            f"activation_digest: {activation_digest}",
            f"target_path: {target_path}",
            "approval_request_created: true",
            "schedule_enabled: false",
            "schedule_index_regenerated: false",
            "external_scheduler_changed: false",
            "openclaw_cron_changed: false",
            "hermes_cron_changed: false",
            "agent_bus_task_written: false",
            "runtime_dispatched: false",
            "workflow_dispatched: false",
            "discord_api_called: false",
            "provider_call_performed: false",
            "credential_value_read: false",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")
    return _rel(vault, path)


def build_phase11_chat_schedule_intent_activation_readiness(
    vault_root: str | Path,
    *,
    schedule_id: str | None = None,
    expected_activation_digest: str | None = None,
    operator_id: str = "studio-operator",
    write_approval: bool = False,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    sid = _safe_id(schedule_id)
    requested_sid = str(schedule_id or "").strip()
    expected = str(expected_activation_digest or "").strip()
    operator = str(operator_id or "studio-operator").strip() or "studio-operator"
    blockers: list[str] = []

    if not requested_sid:
        blockers.append("schedule_id_required")
    if requested_sid and sid != requested_sid:
        blockers.append("schedule_id_not_path_safe")
    if write_approval and not expected:
        blockers.append("expected_activation_digest_required_for_queue_write")

    target_abs = _schedule_path(vault, sid)
    target_path = _rel(vault, target_abs)
    current_yaml, read_blockers = _read_schedule_yaml(target_abs)
    blockers.extend(read_blockers)

    intent = None
    if current_yaml:
        try:
            intent = load_schedule(sid, vault, check_registry=True)
        except Exception as exc:
            blockers.append(f"schedule_intent_invalid:{exc}")
    if intent is None and current_yaml:
        blockers.append("schedule_intent_not_loadable")

    future_yaml = current_yaml
    if current_yaml:
        future_yaml, future_blockers = _future_enabled_yaml(current_yaml)
        blockers.extend(future_blockers)
        try:
            future_data = _parse_yaml_mapping(future_yaml)
            _validate_schedule(future_data, target_abs, vault, check_registry=True)
        except Exception as exc:
            blockers.append(f"future_enabled_schedule_invalid:{exc}")
    else:
        future_data = {}

    runtime_adapter_target = str(getattr(intent, "runtime_adapter_target", "") or future_data.get("runtime_adapter_target") or "")
    schedule_kind = str(getattr(intent, "schedule_kind", "") or future_data.get("schedule_kind") or "workflow")
    workflow_id = getattr(intent, "workflow_id", None) or future_data.get("workflow_id")
    command_id = getattr(intent, "command_id", None) or future_data.get("command_id")

    if intent is not None:
        blockers.extend(
            _current_enabled_duplicate_blockers(
                vault=vault,
                schedule_id=sid,
                schedule_kind=schedule_kind,
                workflow_id=workflow_id,
                command_id=command_id,
                adapter=runtime_adapter_target,
            )
        )

    try:
        current_export = export_schedules_for_adapter(runtime_adapter_target, vault, enabled_only=True) if runtime_adapter_target else []
    except Exception as exc:
        current_export = []
        blockers.append(f"current_adapter_export_unavailable:{exc}")
    candidate_entry = {
        "schedule_id": sid,
        "schedule_kind": schedule_kind,
        "workflow_id": workflow_id,
        "command_id": command_id,
        "runtime_adapter_target": runtime_adapter_target,
        "enabled_after_future_activation": True,
        "target_path": target_path,
    }
    export_preview = {
        "runtime_adapter_target": runtime_adapter_target or None,
        "currently_enabled_export_count": len(current_export),
        "currently_enabled_schedule_ids": [item.get("schedule_id") for item in current_export],
        "future_candidate": candidate_entry,
        "adapter_export_changed_by_preview": False,
    }
    export_preview_digest = _sha256_text(_canonical_json(export_preview))
    schedule_yaml_sha = _sha256_text(current_yaml) if current_yaml else ""
    future_yaml_sha = _sha256_text(future_yaml) if future_yaml else ""
    digest_material = _activation_digest_material(
        schedule_id=sid,
        target_path=target_path,
        runtime_adapter_target=runtime_adapter_target,
        schedule_yaml_sha256=schedule_yaml_sha,
        future_enabled_yaml_sha256=future_yaml_sha,
        export_preview_digest=export_preview_digest,
    )
    activation_digest = _sha256_text(_canonical_json(digest_material))
    if write_approval and expected and expected != activation_digest:
        blockers.append("expected_activation_digest_mismatch")

    spec = _approval_spec(
        target_path=target_path,
        future_enabled_yaml=future_yaml,
        activation_digest=activation_digest,
        digest_material=digest_material,
        operator_id=operator,
    )
    validation = StudioService(vault).validate_action(spec)
    if validation.gate_blocked:
        blockers.append("studio_service_validation_gate_blocked")

    hard_blockers = list(dict.fromkeys(blockers))
    duplicate = _find_existing(vault, activation_digest) if write_approval else None
    warnings: list[str] = []
    if duplicate:
        warnings.append("duplicate_active_schedule_activation_request_present")

    created = False
    approval_id = None
    approval_path = None
    audit_path = None
    queue_writer_called = False
    status = STATUS_PREVIEW
    if write_approval and not hard_blockers and duplicate:
        approval_id = duplicate.get("approval_id")
        approval_path = duplicate.get("path")
        status = "COMPLETE / DUPLICATE-BLOCKED / EXISTING ACTIVATION APPROVAL RETURNED / ENABLEMENT BLOCKED"
    elif write_approval and not hard_blockers:
        queue_writer_called = True
        request = StudioService(vault).queue_for_approval(spec)
        created = True
        approval_id = request.approval_id
        approval_path = f"{StudioService.APPROVAL_DIR}/{request.approval_id}.json"
        audit_path = _write_audit(
            vault=vault,
            approval_id=approval_id,
            approval_path=approval_path,
            schedule_id=sid,
            activation_digest=activation_digest,
            target_path=target_path,
            operator_id=operator,
        )
        status = STATUS_WRITTEN

    ok = not any(
        item in hard_blockers
        for item in {
            "schedule_id_required",
            "schedule_id_not_path_safe",
            "schedule_intent_file_missing",
            "schedule_already_enabled",
            "schedule_enabled_field_missing_or_not_false",
            "expected_activation_digest_required_for_queue_write",
            "expected_activation_digest_mismatch",
            "studio_service_validation_gate_blocked",
        }
    ) and not any(item.startswith(("schedule_intent_invalid:", "future_enabled_schedule_invalid:", "enabled_duplicate_")) for item in hard_blockers)

    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": status,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": not write_approval,
        "approval_gated": True,
        "summary": {
            "schedule_id": sid if requested_sid else None,
            "schedule_kind": schedule_kind or None,
            "workflow_id": workflow_id,
            "command_id": command_id,
            "runtime_adapter_target": runtime_adapter_target or None,
            "schedule_currently_enabled": bool(getattr(intent, "enabled", False)) if intent else None,
            "future_enabled_preview": bool(future_yaml and not hard_blockers),
            "activation_preview_ready": ok,
            "approval_request_created": created,
            "approval_id": approval_id,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "blocker_count": len(hard_blockers),
        },
        "digest_proof": {
            "activation_digest": activation_digest,
            "expected_activation_digest": expected or None,
            "activation_digest_matched": bool(expected and expected == activation_digest),
            "activation_digest_required_for_write": True,
            "digest_material": digest_material,
            "schedule_yaml_sha256": schedule_yaml_sha,
            "future_enabled_yaml_sha256": future_yaml_sha,
        },
        "approval_queue_write": {
            "queue_writer_called": queue_writer_called,
            "approval_request_created": created,
            "approval_id": approval_id,
            "approval_path": approval_path,
            "audit_record_path": audit_path,
            "duplicate_active_request_present": bool(duplicate),
        },
        "target_write_proof": {
            "target_path": target_path,
            "target_file_written": False,
            "schedule_enabled": False,
            "schedule_index_regenerated": False,
            "external_scheduler_changed": False,
            "openclaw_cron_changed": False,
            "hermes_cron_changed": False,
            "agent_bus_task_written": False,
            "runtime_dispatched": False,
            "workflow_dispatched": False,
            "discord_api_called": False,
            "provider_call_performed": False,
            "credential_value_read": False,
        },
        "future_activation_preview": {
            "target_path": target_path,
            "future_enabled_yaml_preview": future_yaml,
            "future_action_type": "write_file",
            "ambient_studio_execution_blocked": True,
            "future_executor_required": True,
        },
        "adapter_export_preview": export_preview,
        "authority": {
            "approval_queue_write_allowed_with_digest": True,
            "schedule_enable_allowed_now": False,
            "schedule_index_regeneration_allowed_now": False,
            "external_scheduler_mutation_allowed": False,
            "openclaw_cron_mutation_allowed": False,
            "hermes_cron_mutation_allowed": False,
            "agent_bus_task_write_allowed": False,
            "runtime_dispatch_allowed": False,
            "workflow_dispatch_allowed": False,
            "discord_api_calls_allowed": False,
            "provider_calls_allowed": False,
            "credential_values_visible": False,
        },
        "blocked_reasons": hard_blockers,
        "warnings": warnings,
    }


def format_phase11_chat_schedule_intent_activation_readiness(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    digest = payload.get("digest_proof") or {}
    queue = payload.get("approval_queue_write") or {}
    lines = [
        "Phase 11 Chat Schedule Intent Activation Readiness",
        f"Status: {payload.get('status')}",
        f"Schedule id: {summary.get('schedule_id') or 'missing'}",
        f"Runtime adapter: {summary.get('runtime_adapter_target') or 'missing'}",
        f"Activation digest: {digest.get('activation_digest') or 'missing'}",
        f"Approval request created: {queue.get('approval_request_created')}",
        f"Schedule enabled now: {(payload.get('target_write_proof') or {}).get('schedule_enabled')}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers)
    lines.append(
        "Boundary: readiness and activation approval packet only; no schedule enablement, "
        "index regeneration, external scheduler mutation, OpenClaw/Hermes cron change, "
        "Agent Bus task write, runtime/workflow dispatch, Discord/provider call, or credential read."
    )
    return "\n".join(lines)
