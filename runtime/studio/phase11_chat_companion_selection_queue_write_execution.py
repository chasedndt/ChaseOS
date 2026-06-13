"""Phase 11 Chat companion selection queue-write execution proof.

This pass performs the narrow governed write that the prior readiness pass only
previewed: it creates one pending Studio approval artifact for a companion
selection change when the operator supplies the exact queue-write digest.

It does not approve, consume, execute, or apply the companion-selection target
write. It also performs no runtime control, provider call, Agent Bus write,
identity/profile/role-card mutation, or canonical writeback.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from runtime.studio.phase11_chat_companion_selection_queue_write_readiness import (
    build_phase11_chat_companion_selection_queue_write_readiness,
)
from runtime.studio.service import ActionSpec, StudioService


MODEL_VERSION = "studio.phase11_chat_companion_selection_queue_write_execution.v1"
SURFACE_ID = "phase11_chat_companion_selection_queue_write_execution_proof"
PASS_ID = "phase11-chat-companion-selection-queue-write-execution-proof"
STATUS = "COMPLETE / APPROVAL-QUEUE-WRITE / VERIFIED / SELECTION WRITES BLOCKED"
NEXT_RECOMMENDED_PASS = "phase11-chat-companion-selection-approval-consumption-readiness"
RUNTIME_PROFILE_IDENTITY = "OpenClaw / Axiom-Codex on ZeusOS"
AUDIT_DIR = "07_LOGS/Agent-Activity"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return str(path)


def _safe_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _existing_digest_approval(vault: Path, queue_write_digest: str) -> dict[str, Any] | None:
    root = vault / StudioService.APPROVAL_DIR
    if not root.exists():
        return None
    active = {"pending", "approved", "executing", "executed", "execution_failed"}
    for path in sorted(root.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        payload = _safe_json(path) or {}
        spec = payload.get("action_spec") if isinstance(payload.get("action_spec"), dict) else {}
        metadata = spec.get("metadata") if isinstance(spec.get("metadata"), dict) else {}
        if metadata.get("phase11_companion_selection_queue_write_digest") != queue_write_digest:
            continue
        if str(payload.get("status") or "") not in active:
            continue
        return {
            "approval_id": payload.get("approval_id") or path.stem,
            "status": payload.get("status") or "unknown",
            "path": _rel(vault, path),
        }
    return None


def _blocked_payload(
    *,
    vault: Path,
    readiness: dict[str, Any],
    blockers: list[str],
    expected_queue_write_digest: str,
) -> dict[str, Any]:
    summary = readiness.get("summary") or {}
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": "BLOCKED / APPROVAL-QUEUE-WRITE / NO APPROVAL ARTIFACT WRITE",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": False,
        "approval_gated": True,
        "summary": {
            "requested_runtime_id": summary.get("requested_runtime_id"),
            "current_runtime_id": summary.get("current_runtime_id"),
            "expected_queue_write_digest_provided": bool(expected_queue_write_digest),
            "approval_request_created": False,
            "approval_queue_writer_called": False,
            "approval_status": None,
            "approval_execution_called": False,
            "companion_selection_written": False,
            "target_write_performed": False,
            "runtime_control_performed": False,
            "provider_call_performed": False,
            "agent_bus_task_written": False,
            "identity_ledger_mutated": False,
            "profile_writes_performed": False,
            "role_card_writes_performed": False,
            "next_recommended_pass": PASS_ID,
            "blocker_count": len(list(dict.fromkeys(blockers))),
        },
        "readiness_contract": readiness,
        "approval_record": {
            "approval_id": None,
            "approval_path": None,
            "approval_status": None,
        },
        "audit_record": {
            "audit_record_path": None,
            "audit_written": False,
        },
        "authority": _authority(),
        "blocked_reasons": list(dict.fromkeys(blockers)),
    }


def _authority() -> dict[str, bool]:
    return {
        "approval_queue_write_allowed": True,
        "approval_execution_allowed": False,
        "companion_selection_write_allowed": False,
        "runtime_control_allowed": False,
        "runtime_dispatch_allowed": False,
        "identity_ledger_mutation_allowed": False,
        "role_card_mutation_allowed": False,
        "profile_write_allowed": False,
        "provider_calls_allowed": False,
        "agent_bus_task_write_allowed": False,
        "canonical_mutation_allowed": False,
    }


def _write_audit_record(
    *,
    vault: Path,
    approval_id: str,
    approval_path: str,
    requested_runtime: str | None,
    current_runtime: str | None,
    selection_digest: str,
    queue_write_digest: str,
    operator_id: str,
) -> str:
    root = vault / AUDIT_DIR
    root.mkdir(parents=True, exist_ok=True)
    audit_path = root / f"{PASS_ID}-{queue_write_digest[:16]}.md"
    date_index = _now_utc()[:10]
    text = "\n".join(
        [
            "---",
            f"date_index: {date_index}",
            f"runtime_profile_identity: {RUNTIME_PROFILE_IDENTITY}",
            f"pass_id: {PASS_ID}",
            f"approval_id: {approval_id}",
            f"status: {STATUS}",
            "---",
            "",
            "# Phase 11 Chat Companion Selection Queue-Write Execution Proof",
            "",
            f"runtime_profile_identity: {RUNTIME_PROFILE_IDENTITY}",
            f"operator_id: {operator_id or 'operator'}",
            f"requested_runtime_id: {requested_runtime or 'missing'}",
            f"current_runtime_id: {current_runtime or 'missing'}",
            f"selection_digest: {selection_digest}",
            f"queue_write_digest: {queue_write_digest}",
            f"approval_id: {approval_id}",
            f"approval_path: {approval_path}",
            "approval_request_created: true",
            "approval_queue_writer_called: true",
            "approval_execution_called: false",
            "companion_selection_written: false",
            "target_write_performed: false",
            "runtime_control_performed: false",
            "provider_call_performed: false",
            "agent_bus_task_written: false",
            "identity_ledger_mutated: false",
            "profile_writes_performed: false",
            "role_card_writes_performed: false",
            "canonical_mutation_allowed: false",
            "",
        ]
    )
    audit_path.write_text(text, encoding="utf-8")
    return _rel(vault, audit_path)


def execute_phase11_chat_companion_selection_queue_write(
    vault_root: str | Path,
    *,
    requested_runtime: str | None = None,
    current_runtime: str | None = None,
    message: str | None = None,
    expected_queue_write_digest: str | None = None,
    operator_id: str = "operator",
) -> dict[str, Any]:
    """Create one pending approval artifact for a digest-bound companion-selection request."""

    vault = Path(vault_root).resolve()
    expected = str(expected_queue_write_digest or "").strip()
    readiness = build_phase11_chat_companion_selection_queue_write_readiness(
        vault,
        requested_runtime=requested_runtime,
        current_runtime=current_runtime,
        message=message,
    )
    digest = readiness.get("digest_proof") or {}
    queue_write_digest = str(digest.get("queue_write_digest") or "")
    selection_digest = str(digest.get("selection_digest") or "")
    blockers = list(readiness.get("blocked_reasons") or [])

    if not expected:
        blockers.append("expected_queue_write_digest_required")
    elif expected != queue_write_digest:
        blockers.append("expected_queue_write_digest_mismatch")

    existing = _existing_digest_approval(vault, queue_write_digest) if queue_write_digest else None
    if existing:
        blockers.append("approval_queue_request_already_exists_for_digest")

    if readiness.get("ok") is not True and "queue_write_readiness_not_ready" not in blockers:
        blockers.append("queue_write_readiness_not_ready")

    if blockers:
        return _blocked_payload(
            vault=vault,
            readiness=readiness,
            blockers=blockers,
            expected_queue_write_digest=expected,
        )

    packet = readiness.get("future_queue_write_packet_preview") or {}
    action = dict(packet.get("action_spec_preview") or {})
    metadata = dict(action.get("metadata") or {})
    metadata.update(
        {
            "pass": PASS_ID,
            "source_surface": SURFACE_ID,
            "phase11_companion_selection_queue_write_execution_proof": True,
            "phase11_companion_selection_queue_write_digest": queue_write_digest,
            "phase11_companion_selection_digest": selection_digest,
            "operator_confirmation": operator_id or "operator",
            "approval_execution_deferred_until": NEXT_RECOMMENDED_PASS,
            "target_selection_write_performed": False,
            "approval_execution_called": False,
            "runtime_control_performed": False,
            "provider_call_performed": False,
            "agent_bus_task_write_performed": False,
        }
    )
    content = json.dumps(
        {
            "selected_runtime_id": action.get("target_runtime_id"),
            "previous_runtime_id": action.get("current_runtime_id"),
            "selection_digest": selection_digest,
            "queue_write_digest": queue_write_digest,
        },
        indent=2,
        sort_keys=True,
    ) + "\n"
    spec = ActionSpec(
        action_type=str(action.get("action_type") or "chat_companion_selection_change"),
        target_path=str(action.get("target_path") or "runtime/studio/chat/companion-selection.json"),
        content=content,
        metadata=metadata,
        submitted_by="studio-chat",
        note="Phase 11 Chat companion-selection approval queue request; selection write deferred.",
    )
    service = StudioService(vault)
    req = service.queue_for_approval(spec)
    approval_path = f"{StudioService.APPROVAL_DIR}/{req.approval_id}.json"
    summary = readiness.get("summary") or {}
    audit_path = _write_audit_record(
        vault=vault,
        approval_id=req.approval_id,
        approval_path=approval_path,
        requested_runtime=summary.get("requested_runtime_id"),
        current_runtime=summary.get("current_runtime_id"),
        selection_digest=selection_digest,
        queue_write_digest=queue_write_digest,
        operator_id=operator_id,
    )

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": False,
        "approval_gated": True,
        "summary": {
            "requested_runtime_id": summary.get("requested_runtime_id"),
            "current_runtime_id": summary.get("current_runtime_id"),
            "expected_queue_write_digest_provided": True,
            "approval_request_created": True,
            "approval_queue_writer_called": True,
            "approval_status": req.status,
            "approval_execution_called": False,
            "companion_selection_written": False,
            "target_write_performed": False,
            "runtime_control_performed": False,
            "provider_call_performed": False,
            "agent_bus_task_written": False,
            "identity_ledger_mutated": False,
            "profile_writes_performed": False,
            "role_card_writes_performed": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "blocker_count": 0,
        },
        "digest_proof": {
            "selection_digest": selection_digest,
            "queue_write_digest": queue_write_digest,
        },
        "approval_record": {
            "approval_id": req.approval_id,
            "approval_path": approval_path,
            "approval_status": req.status,
        },
        "audit_record": {
            "audit_record_path": audit_path,
            "audit_written": True,
        },
        "readiness_contract": readiness,
        "authority": _authority(),
        "blocked_reasons": [],
    }


def format_phase11_chat_companion_selection_queue_write_execution(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    approval = payload.get("approval_record") or {}
    digest = payload.get("digest_proof") or {}
    lines = [
        "Phase 11 Chat Companion Selection Queue-Write Execution Proof",
        f"Status: {payload.get('status')}",
        f"Approval request created: {summary.get('approval_request_created')}",
        f"Approval id: {approval.get('approval_id') or 'none'}",
        f"Approval status: {summary.get('approval_status') or 'none'}",
        f"Queue-write digest: {digest.get('queue_write_digest') or 'missing'}",
        f"Selection write performed: {summary.get('companion_selection_written')}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers)
    return "\n".join(lines)
