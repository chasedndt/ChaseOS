"""Phase 11 Chat schedule adapter export readiness.

This surface prepares a digest-bound local export packet for enabled ChaseOS
schedules targeting one runtime adapter. It may queue an approval request to
write that local packet in a future pass, but it does not mutate external
scheduler files, OpenClaw/Hermes cron, Agent Bus tasks, Discord, providers, or
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
    VALID_RUNTIME_ADAPTERS,
    export_schedules_for_adapter,
    load_schedule,
)
from runtime.studio.service import ActionSpec, StudioService


MODEL_VERSION = "studio.phase11_chat_schedule_adapter_export_readiness.v1"
SURFACE_ID = "phase11_chat_schedule_adapter_export_readiness"
PASS_ID = "studio-chat-schedule-adapter-export-readiness"
STATUS_PREVIEW = "READY / ADAPTER-EXPORT READINESS / CRON MUTATION BLOCKED"
STATUS_WRITTEN = "COMPLETE / ADAPTER-EXPORT PACKET APPROVAL QUEUED / CRON MUTATION BLOCKED"
NEXT_RECOMMENDED_PASS = "studio-chat-approved-schedule-adapter-export-packet-writer"
METADATA_BLOCK_KEY = "phase11_chat_schedule_adapter_export_execution_blocked"
EXPORT_PACKET_ROOT = "runtime/studio/chat/schedule-adapter-exports"
AUDIT_ROOT = "runtime/studio/approvals/chat-schedule-adapter-exports"


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


def _schedule_sha_map(vault: Path, entries: list[dict[str, Any]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for entry in entries:
        schedule_id = str(entry.get("schedule_id") or "")
        if not schedule_id:
            continue
        path = vault / "runtime" / "schedules" / f"{schedule_id}.yaml"
        try:
            result[schedule_id] = _sha256_text(path.read_text(encoding="utf-8"))
        except OSError:
            result[schedule_id] = ""
    return result


def _index_sha(vault: Path) -> str:
    path = vault / "runtime" / "schedules" / "index.yaml"
    try:
        return _sha256_text(path.read_text(encoding="utf-8"))
    except OSError:
        return ""


def _effect_flags() -> dict[str, bool]:
    return {
        "export_packet_written": False,
        "external_scheduler_changed": False,
        "openclaw_cron_changed": False,
        "hermes_cron_changed": False,
        "agent_bus_task_written": False,
        "runtime_dispatched": False,
        "workflow_dispatched": False,
        "discord_api_called": False,
        "provider_call_performed": False,
        "credential_value_read": False,
        "canonical_mutation_performed": False,
    }


def _authority() -> dict[str, bool]:
    return {
        "adapter_export_read_model_allowed": True,
        "approval_queue_write_allowed_with_digest": True,
        "local_export_packet_write_allowed_now": False,
        "external_scheduler_mutation_allowed": False,
        "openclaw_cron_mutation_allowed": False,
        "hermes_cron_mutation_allowed": False,
        "agent_bus_task_write_allowed": False,
        "runtime_dispatch_allowed": False,
        "workflow_dispatch_allowed": False,
        "discord_api_calls_allowed": False,
        "provider_calls_allowed": False,
        "credential_values_visible": False,
        "canonical_mutation_allowed": False,
    }


def _digest_material(
    *,
    adapter: str,
    schedule_id: str | None,
    entries: list[dict[str, Any]],
    schedule_file_sha256: dict[str, str],
    schedule_index_sha256: str,
) -> dict[str, Any]:
    return {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "export_action": "prepare_adapter_export_packet_for_review",
        "runtime_adapter_target": adapter,
        "schedule_id_filter": schedule_id,
        "enabled_only": True,
        "schedule_ids": [str(item.get("schedule_id") or "") for item in entries],
        "entries": entries,
        "schedule_file_sha256": schedule_file_sha256,
        "schedule_index_sha256": schedule_index_sha256,
    }


def _export_packet(
    *,
    adapter: str,
    schedule_id: str | None,
    export_digest: str,
    digest_material: dict[str, Any],
    target_path: str,
    entries: list[dict[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    return {
        "packet_type": "phase11_chat_schedule_adapter_export_packet",
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at_utc": generated_at,
        "runtime_adapter_target": adapter,
        "schedule_id_filter": schedule_id,
        "export_digest": export_digest,
        "target_path": target_path,
        "enabled_only": True,
        "adapter_entries": entries,
        "entry_count": len(entries),
        "digest_material": digest_material,
        "future_executor_required": True,
        "external_scheduler_mutation_allowed": False,
        "openclaw_cron_mutation_allowed": False,
        "hermes_cron_mutation_allowed": False,
        "agent_bus_task_write_allowed": False,
        "runtime_dispatch_allowed": False,
        "workflow_dispatch_allowed": False,
        "discord_api_calls_allowed": False,
        "provider_calls_allowed": False,
        "credential_values_visible": False,
    }


def _approval_spec(
    *,
    target_path: str,
    packet_json: str,
    export_digest: str,
    digest_material: dict[str, Any],
    adapter: str,
    operator_id: str,
) -> ActionSpec:
    return ActionSpec(
        action_type="create_file",
        target_path=target_path,
        content=packet_json,
        submitted_by=operator_id,
        note=(
            "Phase 11 Chat schedule adapter export packet approval. Ambient Studio "
            "execution is blocked; a future governed packet writer must consume it."
        ),
        metadata={
            "phase11_chat_schedule_adapter_export_readiness": True,
            METADATA_BLOCK_KEY: True,
            "source_surface": SURFACE_ID,
            "export_digest": export_digest,
            "export_digest_material": digest_material,
            "runtime_adapter_target": adapter,
            "adapter_export_packet_requested": True,
            **_effect_flags(),
        },
    )


def _find_existing(vault: Path, export_digest: str) -> dict[str, str] | None:
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
            metadata.get("phase11_chat_schedule_adapter_export_readiness") is True
            and metadata.get("export_digest") == export_digest
            and payload.get("status") in {"pending", "approved"}
        ):
            return {"approval_id": str(payload.get("approval_id") or ""), "path": _rel(vault, path)}
    return None


def _next_audit_path(vault: Path, export_digest: str) -> Path:
    root = vault / AUDIT_ROOT
    root.mkdir(parents=True, exist_ok=True)
    base = root / f"{export_digest[:20]}.md"
    if not base.exists():
        return base
    for index in range(2, 100):
        candidate = root / f"{export_digest[:20]}-{index}.md"
        if not candidate.exists():
            return candidate
    raise RuntimeError("could not allocate schedule adapter export audit path")


def _write_audit(
    *,
    vault: Path,
    approval_id: str,
    approval_path: str,
    adapter: str,
    export_digest: str,
    target_path: str,
    operator_id: str,
    entry_count: int,
) -> str:
    path = _next_audit_path(vault, export_digest)
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
            "# Phase 11 Chat Schedule Adapter Export Readiness",
            "",
            f"operator_id: {operator_id}",
            f"approval_id: {approval_id}",
            f"approval_path: {approval_path}",
            f"runtime_adapter_target: {adapter}",
            f"export_digest: {export_digest}",
            f"target_path: {target_path}",
            f"entry_count: {entry_count}",
            "approval_request_created: true",
            "export_packet_written: false",
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


def build_phase11_chat_schedule_adapter_export_readiness(
    vault_root: str | Path,
    *,
    runtime_adapter_target: str | None = "openclaw",
    schedule_id: str | None = None,
    expected_export_digest: str | None = None,
    operator_id: str = "studio-operator",
    write_approval: bool = False,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    requested_schedule_id = str(schedule_id or "").strip()
    sid = _safe_id(requested_schedule_id) if requested_schedule_id else None
    requested_adapter = str(runtime_adapter_target or "").strip()
    adapter = _safe_id(requested_adapter or "openclaw")
    expected = str(expected_export_digest or "").strip()
    operator = str(operator_id or "studio-operator").strip() or "studio-operator"
    blockers: list[str] = []
    warnings: list[str] = []

    if requested_schedule_id and sid != requested_schedule_id:
        blockers.append("schedule_id_not_path_safe")
    if requested_adapter and adapter != requested_adapter:
        blockers.append("runtime_adapter_target_not_path_safe")
    if not adapter:
        blockers.append("runtime_adapter_target_required")
    if adapter and adapter not in VALID_RUNTIME_ADAPTERS:
        blockers.append("runtime_adapter_target_not_registered")
    if write_approval and not expected:
        blockers.append("expected_export_digest_required_for_queue_write")

    intent = None
    if sid:
        try:
            intent = load_schedule(sid, vault, check_registry=True)
        except Exception as exc:
            blockers.append(f"schedule_intent_invalid:{exc}")
        if intent is None:
            blockers.append("schedule_intent_not_found")
        else:
            if intent.enabled is not True:
                blockers.append("schedule_intent_not_enabled")
            if requested_adapter and intent.runtime_adapter_target != adapter and intent.runtime_adapter_fallback != adapter:
                blockers.append("schedule_not_targeted_to_requested_adapter")
            elif not requested_adapter:
                adapter = intent.runtime_adapter_target

    entries: list[dict[str, Any]] = []
    try:
        if adapter in VALID_RUNTIME_ADAPTERS:
            entries = export_schedules_for_adapter(adapter, vault, enabled_only=True)
    except Exception as exc:
        blockers.append(f"adapter_export_unavailable:{exc}")

    if sid and entries and sid not in {str(item.get("schedule_id") or "") for item in entries}:
        blockers.append("schedule_id_not_present_in_enabled_adapter_export")
    if write_approval and not entries:
        blockers.append("enabled_adapter_export_empty")

    schedule_file_sha256 = _schedule_sha_map(vault, entries)
    schedule_index_sha256 = _index_sha(vault)
    digest_material = _digest_material(
        adapter=adapter,
        schedule_id=sid,
        entries=entries,
        schedule_file_sha256=schedule_file_sha256,
        schedule_index_sha256=schedule_index_sha256,
    )
    export_digest = _sha256_text(_canonical_json(digest_material))
    if write_approval and expected and expected != export_digest:
        blockers.append("expected_export_digest_mismatch")

    target_path = f"{EXPORT_PACKET_ROOT}/{adapter}-{export_digest[:20]}.json"
    generated_at = _now_utc()
    packet = _export_packet(
        adapter=adapter,
        schedule_id=sid,
        export_digest=export_digest,
        digest_material=digest_material,
        target_path=target_path,
        entries=entries,
        generated_at=generated_at,
    )
    packet_json = json.dumps(packet, indent=2, sort_keys=True) + "\n"
    spec = _approval_spec(
        target_path=target_path,
        packet_json=packet_json,
        export_digest=export_digest,
        digest_material=digest_material,
        adapter=adapter,
        operator_id=operator,
    )
    validation = StudioService(vault).validate_action(spec)
    if validation.gate_blocked:
        blockers.append("studio_service_validation_gate_blocked")
    if validation.warnings:
        warnings.extend(validation.warnings)

    hard_blockers = list(dict.fromkeys(blockers))
    duplicate = _find_existing(vault, export_digest) if write_approval else None
    if duplicate:
        warnings.append("duplicate_active_schedule_adapter_export_request_present")

    created = False
    approval_id = None
    approval_path = None
    audit_path = None
    queue_writer_called = False
    status = STATUS_PREVIEW
    if write_approval and not hard_blockers and duplicate:
        approval_id = duplicate.get("approval_id")
        approval_path = duplicate.get("path")
        status = "COMPLETE / DUPLICATE-BLOCKED / EXISTING ADAPTER-EXPORT APPROVAL RETURNED / CRON MUTATION BLOCKED"
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
            adapter=adapter,
            export_digest=export_digest,
            target_path=target_path,
            operator_id=operator,
            entry_count=len(entries),
        )
        status = STATUS_WRITTEN

    ok = not any(
        item in hard_blockers
        for item in {
            "schedule_id_not_path_safe",
            "runtime_adapter_target_not_path_safe",
            "runtime_adapter_target_required",
            "runtime_adapter_target_not_registered",
            "schedule_intent_not_found",
            "schedule_intent_not_enabled",
            "schedule_not_targeted_to_requested_adapter",
            "schedule_id_not_present_in_enabled_adapter_export",
            "expected_export_digest_required_for_queue_write",
            "expected_export_digest_mismatch",
            "enabled_adapter_export_empty",
            "studio_service_validation_gate_blocked",
        }
    ) and not any(item.startswith(("schedule_intent_invalid:", "adapter_export_unavailable:")) for item in hard_blockers)

    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": status,
        "generated_at_utc": generated_at,
        "vault_root": str(vault),
        "read_only": not write_approval,
        "approval_gated": True,
        "summary": {
            "runtime_adapter_target": adapter or None,
            "schedule_id": sid,
            "enabled_only": True,
            "enabled_schedule_count": len(entries),
            "enabled_schedule_ids": [item.get("schedule_id") for item in entries],
            "adapter_export_preview_ready": ok,
            "approval_request_created": created,
            "approval_id": approval_id,
            "target_packet_path": target_path,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "blocker_count": len(hard_blockers),
        },
        "digest_proof": {
            "export_digest": export_digest,
            "expected_export_digest": expected or None,
            "export_digest_matched": bool(expected and expected == export_digest),
            "export_digest_required_for_write": True,
            "digest_material": digest_material,
            "schedule_file_sha256": schedule_file_sha256,
            "schedule_index_sha256": schedule_index_sha256,
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
            **_effect_flags(),
        },
        "adapter_export_preview": {
            "runtime_adapter_target": adapter or None,
            "enabled_only": True,
            "entry_count": len(entries),
            "entries": entries,
            "packet_json_preview": packet_json,
            "future_packet_write_required": True,
            "ambient_studio_execution_blocked": True,
            "external_scheduler_changed": False,
            "openclaw_cron_changed": False,
            "hermes_cron_changed": False,
        },
        "authority": _authority(),
        "blocked_reasons": hard_blockers,
        "warnings": list(dict.fromkeys(warnings)),
    }


def format_phase11_chat_schedule_adapter_export_readiness(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    digest = payload.get("digest_proof") or {}
    queue = payload.get("approval_queue_write") or {}
    target = payload.get("target_write_proof") or {}
    lines = [
        "Phase 11 Chat Schedule Adapter Export Readiness",
        f"Status: {payload.get('status')}",
        f"Runtime adapter: {summary.get('runtime_adapter_target') or 'missing'}",
        f"Schedule id: {summary.get('schedule_id') or 'all enabled'}",
        f"Enabled schedules: {summary.get('enabled_schedule_count')}",
        f"Export digest: {digest.get('export_digest') or 'missing'}",
        f"Approval request created: {queue.get('approval_request_created')}",
        f"Export packet written now: {target.get('export_packet_written')}",
        f"External scheduler changed: {target.get('external_scheduler_changed')}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers)
    lines.append(
        "Boundary: adapter export readiness and approval packet only; no local "
        "export packet write yet, no external scheduler mutation, no OpenClaw/Hermes "
        "cron change, no Agent Bus task, no runtime/workflow dispatch, no Discord/provider "
        "call, and no credential read."
    )
    return "\n".join(lines)
