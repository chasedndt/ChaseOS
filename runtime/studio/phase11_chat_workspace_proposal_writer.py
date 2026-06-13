"""Phase 11 Chat workspace proposal writer.

This surface creates digest-bound approval requests for native Studio Chat
workspace/folder/thread proposal packets. It does not create the actual
workspace, folder, thread, message, board item, Discord thread, schedule, Agent
Bus task, provider call, or canonical writeback.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from runtime.studio.phase11_chat_workspaces_foundation import (
    RUNTIME_CHANNEL_BINDINGS,
    build_phase11_chat_workspaces_foundation,
)
from runtime.studio.service import ActionSpec, StudioService


MODEL_VERSION = "studio.phase11_chat_workspace_proposal_writer.v1"
SURFACE_ID = "phase11_chat_workspace_proposal_writer"
PASS_ID = "studio-runtime-chat-workspace-proposal-writer"
STATUS_PREVIEW = "READY / APPROVAL-QUEUE-WRITE-PREVIEW / CHAT STATE WRITES BLOCKED"
STATUS_WRITTEN = "COMPLETE / APPROVAL-QUEUE-WRITE / VERIFIED / CHAT STATE WRITES BLOCKED"
NEXT_RECOMMENDED_PASS = "studio-runtime-chat-workspace-proposal-consumption-executor"
PROPOSAL_ROOT = "runtime/studio/chat/workspace-proposals"
AUDIT_ROOT = "runtime/studio/approvals/chat-workspace-proposals"
METADATA_BLOCK_KEY = "phase11_chat_workspace_proposal_execution_blocked"

PROPOSAL_KINDS = {
    "create_workspace",
    "create_folder",
    "create_thread",
}

SECRET_TOKEN = "[REDACTED_SECRET]"
SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("openai_style_api_key", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b", re.IGNORECASE)),
    (
        "token_assignment",
        re.compile(r"(?i)(\b(?:api[_ -]?key|secret|token|credential)\s*[:=]\s*)([^\s,;]{8,})"),
    ),
    ("bearer_token", re.compile(r"(?i)(\bbearer\s+)([A-Za-z0-9._~+/=-]{16,})")),
]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(value: str | None) -> str:
    return " ".join(str(value or "").strip().split())


def _slug(value: str, fallback: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return (text or fallback)[:72].strip("-") or fallback


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _redact(value: str) -> dict[str, Any]:
    redacted = value
    categories: list[str] = []
    count = 0
    for category, pattern in SECRET_PATTERNS:
        def repl(match: re.Match[str]) -> str:
            nonlocal count
            count += 1
            if match.lastindex and match.lastindex >= 2:
                return f"{match.group(1)}{SECRET_TOKEN}"
            return SECRET_TOKEN

        redacted, local_count = pattern.subn(repl, redacted)
        if local_count:
            categories.append(category)
    return {
        "contains_secret": bool(count),
        "redacted": redacted,
        "redaction_count": count,
        "indicator_categories": list(dict.fromkeys(categories)),
    }


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


def _runtime_from_message(message: str, requested_runtime_id: str | None) -> str:
    requested = _norm(requested_runtime_id)
    if requested:
        lowered = requested.lower()
        if lowered == "openclaw":
            return "OpenClaw"
        if lowered == "hermes":
            return "Hermes"
        if lowered == "codex":
            return "Codex"
        return requested
    lowered_message = message.lower()
    if "hermes" in lowered_message:
        return "Hermes"
    if "openclaw" in lowered_message or "open claw" in lowered_message:
        return "OpenClaw"
    if "codex" in lowered_message:
        return "Codex"
    return "OpenClaw"


def _proposal_kind(message: str, requested_kind: str | None) -> str:
    requested = _norm(requested_kind).replace("-", "_")
    if requested in PROPOSAL_KINDS:
        return requested
    lowered = message.lower()
    if "folder" in lowered:
        return "create_folder"
    if "project" in lowered or "workspace" in lowered:
        return "create_workspace"
    return "create_thread"


def _workspace_from_foundation(
    foundation: dict[str, Any],
    workspace_id: str | None,
    *,
    fallback: str = "runtime-ops",
) -> dict[str, Any]:
    requested = _slug(_norm(workspace_id), fallback) if workspace_id else fallback
    workspaces = foundation.get("workspaces") or []
    for workspace in workspaces:
        if str(workspace.get("workspace_id") or "") == requested:
            return workspace
    return next((item for item in workspaces if item.get("workspace_id") == fallback), {}) or {}


def _title(message: str, proposal_kind: str, runtime_id: str, title: str | None) -> str:
    requested = _norm(title)
    if requested:
        return requested[:96]
    if proposal_kind == "create_workspace":
        return " ".join(message.split()[:8]).strip(" .,:;")[:96] or "New Chat Workspace"
    if proposal_kind == "create_folder":
        return " ".join(message.split()[:8]).strip(" .,:;")[:96] or "New Chat Folder"
    return f"{runtime_id} Runtime Thread"


def _proposal_packet(
    *,
    foundation: dict[str, Any],
    message: str,
    proposal_kind: str,
    runtime_id: str,
    workspace: dict[str, Any],
    folder_id: str | None,
    title: str,
    operator_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    workspace_id = str(workspace.get("workspace_id") or "runtime-ops")
    workspace_mode = str(workspace.get("workspace_mode_hint") or "runtime_agent_ops")
    folder = _slug(_norm(folder_id), "runtime-control") if folder_id else (
        "runtime-control" if proposal_kind == "create_thread" else "boards"
    )
    title_slug = _slug(title, "chat-proposal")
    thread_id = f"{workspace_id}-{title_slug}" if proposal_kind == "create_thread" else ""
    channel_keys = RUNTIME_CHANNEL_BINDINGS.get(runtime_id, [])
    transport_channel_key = channel_keys[0] if channel_keys else ""
    context_paths = [
        item.get("path")
        for item in workspace.get("context_paths") or []
        if item.get("path")
    ][:8]
    action_spec = {
        "proposal_kind": proposal_kind,
        "workspace_id": workspace_id,
        "workspace_mode_hint": workspace_mode,
        "folder_id": folder if proposal_kind in {"create_folder", "create_thread"} else "",
        "thread_id": thread_id,
        "title": title,
        "runtime_id": runtime_id if proposal_kind == "create_thread" else "",
        "transport_channel_key": transport_channel_key if proposal_kind == "create_thread" else "",
        "native_route_preview": (
            f"#chat/{workspace_id}/threads/{thread_id}"
            if proposal_kind == "create_thread"
            else f"#chat/{workspace_id}"
        ),
        "context_paths": context_paths,
        "source_message_sha256": _sha256_text(message),
        "submitted_by": operator_id or "operator",
    }
    digest_material = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "action_spec": action_spec,
        "foundation_model_version": foundation.get("model_version"),
    }
    proposal_digest = _sha256_text(_canonical_json(digest_material))
    proposal_id = f"chat-workspace-prop-{proposal_digest[:16]}"
    target_path = f"{PROPOSAL_ROOT}/{proposal_id}.json"
    packet = {
        "proposal_id": proposal_id,
        "proposal_kind": proposal_kind,
        "status": "pending_approval_preview",
        "title": title,
        "workspace_id": workspace_id,
        "folder_id": action_spec["folder_id"],
        "thread_id": thread_id,
        "runtime_id": action_spec["runtime_id"],
        "transport_channel_key": action_spec["transport_channel_key"],
        "native_route_preview": action_spec["native_route_preview"],
        "context_paths": context_paths,
        "approval_required_before_effect": True,
        "chat_workspace_created": False,
        "chat_folder_created": False,
        "chat_thread_created": False,
        "chat_message_sent": False,
        "discord_api_called": False,
        "discord_thread_created": False,
        "agent_bus_task_written": False,
        "runtime_board_written": False,
        "schedule_mutated": False,
        "provider_call_performed": False,
        "canonical_mutation_allowed": False,
        "proposal_digest": proposal_digest,
        "target_path": target_path,
    }
    return packet, digest_material


def _find_existing(vault: Path, proposal_digest: str) -> dict[str, Any] | None:
    root = vault / StudioService.APPROVAL_DIR
    if not root.exists():
        return None
    active_statuses = {"pending", "approved", "executing", "executed", "execution_failed"}
    for path in sorted(root.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        payload = _safe_json(path) or {}
        spec = payload.get("action_spec") if isinstance(payload.get("action_spec"), dict) else {}
        metadata = spec.get("metadata") if isinstance(spec.get("metadata"), dict) else {}
        if metadata.get("phase11_chat_workspace_proposal_digest") != proposal_digest:
            continue
        if str(payload.get("status") or "") not in active_statuses:
            continue
        return {
            "approval_id": payload.get("approval_id") or path.stem,
            "status": payload.get("status") or "unknown",
            "path": _rel(vault, path),
            "target_path": spec.get("target_path"),
        }
    return None


def _approval_spec(
    *,
    proposal_packet: dict[str, Any],
    digest_material: dict[str, Any],
    operator_id: str,
) -> ActionSpec:
    content = json.dumps(proposal_packet, indent=2, sort_keys=True) + "\n"
    proposal_digest = str(proposal_packet.get("proposal_digest") or "")
    return ActionSpec(
        action_type="create_file",
        target_path=str(proposal_packet.get("target_path") or ""),
        content=content,
        metadata={
            "pass": PASS_ID,
            "source_surface": SURFACE_ID,
            "phase11_chat_workspace_proposal_writer": True,
            METADATA_BLOCK_KEY: True,
            "approval_queue_write_only": True,
            "approval_execution_deferred_until": NEXT_RECOMMENDED_PASS,
            "phase11_chat_workspace_proposal_digest": proposal_digest,
            "phase11_chat_workspace_digest_material_sha256": _sha256_text(_canonical_json(digest_material)),
            "proposal_kind": proposal_packet.get("proposal_kind"),
            "workspace_id": proposal_packet.get("workspace_id"),
            "folder_id": proposal_packet.get("folder_id"),
            "thread_id": proposal_packet.get("thread_id"),
            "runtime_id": proposal_packet.get("runtime_id"),
            "operator_confirmation": operator_id or "operator",
            "chat_workspace_created": False,
            "chat_folder_created": False,
            "chat_thread_created": False,
            "chat_message_sent": False,
            "discord_api_called": False,
            "agent_bus_task_written": False,
            "runtime_board_written": False,
            "schedule_mutated": False,
            "provider_call_performed": False,
            "canonical_mutation_allowed": False,
        },
        submitted_by="studio-chat",
        note="Phase 11 Chat workspace proposal approval request; target effects deferred.",
    )


def _write_audit(
    *,
    vault: Path,
    approval_id: str,
    approval_path: str,
    proposal_packet: dict[str, Any],
    digest_material: dict[str, Any],
    operator_id: str,
) -> str:
    root = vault / AUDIT_ROOT
    root.mkdir(parents=True, exist_ok=True)
    proposal_digest = str(proposal_packet.get("proposal_digest") or "")
    path = root / f"{proposal_digest}.json"
    payload = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "recorded_at_utc": _now_utc(),
        "approval_id": approval_id,
        "approval_artifact_path": approval_path,
        "approval_status": "pending",
        "proposal_digest": proposal_digest,
        "digest_material_sha256": _sha256_text(_canonical_json(digest_material)),
        "proposal_id": proposal_packet.get("proposal_id"),
        "proposal_kind": proposal_packet.get("proposal_kind"),
        "target_path": proposal_packet.get("target_path"),
        "operator_id": operator_id or "operator",
        "approval_request_created": True,
        "target_file_written": False,
        "chat_workspace_created": False,
        "chat_folder_created": False,
        "chat_thread_created": False,
        "discord_api_called": False,
        "agent_bus_task_written": False,
        "runtime_board_written": False,
        "schedule_mutated": False,
        "provider_call_performed": False,
        "canonical_mutation_allowed": False,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return _rel(vault, path)


def build_phase11_chat_workspace_proposal_writer(
    vault_root: str | Path,
    *,
    message: str | None = None,
    proposal_kind: str | None = None,
    workspace_id: str | None = None,
    folder_id: str | None = None,
    runtime_id: str | None = None,
    title: str | None = None,
    expected_proposal_digest: str | None = None,
    write_approval: bool = False,
    operator_id: str = "operator",
) -> dict[str, Any]:
    """Preview or queue one Chat workspace proposal approval request."""

    vault = Path(vault_root).resolve()
    raw_message = str(message or "")
    redaction = _redact(_norm(message))
    safe_message = str(redaction["redacted"])
    foundation = build_phase11_chat_workspaces_foundation(vault, message=safe_message)
    kind = _proposal_kind(safe_message, proposal_kind)
    runtime = _runtime_from_message(safe_message, runtime_id)
    workspace = _workspace_from_foundation(foundation, workspace_id)
    proposal_title = _title(safe_message, kind, runtime, title)
    packet, digest_material = _proposal_packet(
        foundation=foundation,
        message=safe_message,
        proposal_kind=kind,
        runtime_id=runtime,
        workspace=workspace,
        folder_id=folder_id,
        title=proposal_title,
        operator_id=operator_id or "operator",
    )
    proposal_digest = str(packet.get("proposal_digest") or "")
    target_path = str(packet.get("target_path") or "")
    target_abs = vault / target_path
    expected = str(expected_proposal_digest or "").strip()

    blockers: list[str] = []
    warnings: list[str] = []
    if not raw_message.strip() and not title:
        blockers.append("message_or_title_required_for_workspace_proposal")
    if kind not in PROPOSAL_KINDS:
        blockers.append("unsupported_workspace_proposal_kind")
    if redaction["contains_secret"]:
        blockers.append("secret_or_credential_indicator_present")
    if target_abs.exists():
        blockers.append("workspace_proposal_target_collision")
    if write_approval and not expected:
        blockers.append("expected_proposal_digest_required_for_queue_write")
    if write_approval and expected and expected != proposal_digest:
        blockers.append("expected_proposal_digest_mismatch")

    spec = _approval_spec(
        proposal_packet=packet,
        digest_material=digest_material,
        operator_id=operator_id,
    )
    validation = StudioService(vault).validate_action(spec)
    if validation.gate_blocked:
        blockers.append("studio_service_validation_gate_blocked")

    duplicate = _find_existing(vault, proposal_digest) if write_approval else None
    if duplicate:
        warnings.append("duplicate_active_workspace_proposal_request_present")

    hard_blockers = list(dict.fromkeys(blockers))
    created = False
    approval_id = None
    approval_path = None
    audit_path = None
    queue_writer_called = False
    status = STATUS_PREVIEW

    if write_approval and not hard_blockers and duplicate:
        approval_id = str(duplicate.get("approval_id") or "")
        approval_path = str(duplicate.get("path") or "")
        status = "COMPLETE / DUPLICATE-BLOCKED / EXISTING APPROVAL RETURNED / CHAT STATE WRITES BLOCKED"
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
            proposal_packet=packet,
            digest_material=digest_material,
            operator_id=operator_id,
        )
        status = STATUS_WRITTEN

    return {
        "ok": not any(
            item in hard_blockers
            for item in {
                "message_or_title_required_for_workspace_proposal",
                "unsupported_workspace_proposal_kind",
                "secret_or_credential_indicator_present",
                "workspace_proposal_target_collision",
                "expected_proposal_digest_required_for_queue_write",
                "expected_proposal_digest_mismatch",
                "studio_service_validation_gate_blocked",
            }
        ),
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": status,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": not bool(created),
        "approval_gated": True,
        "summary": {
            "proposal_kind": kind,
            "proposal_id": packet.get("proposal_id"),
            "workspace_id": packet.get("workspace_id"),
            "folder_id": packet.get("folder_id"),
            "thread_id": packet.get("thread_id"),
            "runtime_id": packet.get("runtime_id"),
            "target_path_preview": target_path,
            "queue_write_preview_ready": not hard_blockers,
            "write_approval_requested": bool(write_approval),
            "approval_request_created": created,
            "duplicate_active_request_present": bool(duplicate),
            "duplicate_returned_existing_request": bool(write_approval and duplicate and not created and not hard_blockers),
            "approval_id": approval_id,
            "approval_artifact_path": approval_path,
            "target_file_written": False,
            "chat_workspace_created": False,
            "chat_folder_created": False,
            "chat_thread_created": False,
            "chat_message_sent": False,
            "discord_api_called": False,
            "agent_bus_task_written": False,
            "runtime_board_written": False,
            "schedule_mutated": False,
            "provider_call_performed": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "blocker_count": len(hard_blockers),
        },
        "digest_proof": {
            "proposal_digest": proposal_digest,
            "expected_proposal_digest": expected or None,
            "expected_digest_matched": bool(expected and expected == proposal_digest),
            "digest_required_for_write": True,
            "digest_material": digest_material,
        },
        "secret_redaction": {
            "source_contains_secret": bool(redaction["contains_secret"]),
            "source_redacted": bool(redaction["contains_secret"]),
            "redaction_count": int(redaction["redaction_count"]),
            "indicator_categories": list(redaction["indicator_categories"]),
            "source_preview": safe_message[:240],
        },
        "proposal_packet_preview": packet,
        "approval_queue_write": {
            "queue_writer": "runtime.studio.service.StudioService.queue_for_approval",
            "queue_writer_called": queue_writer_called,
            "approval_request_created": created,
            "approval_status_now": "pending" if created else (duplicate or {}).get("status"),
            "approval_artifact_path": approval_path,
            "duplicate": duplicate,
        },
        "audit_record": {
            "audit_record_written": bool(audit_path),
            "audit_record_path": audit_path,
        },
        "target_write_proof": {
            "target_path": target_path,
            "target_file_exists_after": target_abs.exists(),
            "target_file_written": False,
            "chat_workspace_created": False,
            "chat_folder_created": False,
            "chat_thread_created": False,
            "discord_api_called": False,
            "discord_thread_created": False,
            "agent_bus_task_written": False,
            "runtime_board_written": False,
            "schedule_mutated": False,
            "provider_call_performed": False,
        },
        "service_validation": {
            "valid": validation.valid,
            "gate_blocked": validation.gate_blocked,
            "approval_required": True,
            "errors": list(validation.errors),
            "warnings": list(validation.warnings),
        },
        "authority": {
            "approval_queue_write_allowed_with_digest": True,
            "approval_queue_write_performed": created,
            "approval_execution_allowed": False,
            "chat_workspace_write_allowed": False,
            "chat_folder_write_allowed": False,
            "chat_thread_create_allowed": False,
            "chat_message_send_allowed": False,
            "discord_api_calls_allowed": False,
            "discord_thread_create_allowed": False,
            "agent_bus_task_write_allowed": False,
            "runtime_board_write_allowed": False,
            "schedule_mutation_allowed": False,
            "provider_calls_allowed": False,
            "credential_values_visible": False,
            "canonical_mutation_allowed": False,
        },
        "denied_by_this_surface": [
            "approval_execution",
            "chat_workspace_write",
            "chat_folder_write",
            "chat_thread_create",
            "chat_message_send",
            "discord_api_call",
            "discord_thread_create",
            "agent_bus_task_write",
            "runtime_board_write",
            "schedule_mutation",
            "provider_api_call",
            "credential_value_display",
            "canonical_writeback",
        ],
        "blocked_reasons": hard_blockers,
        "warnings": list(dict.fromkeys(warnings)),
        "source_contracts": {
            "chat_workspaces_foundation": foundation,
        },
    }


def format_phase11_chat_workspace_proposal_writer(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    digest = payload.get("digest_proof") or {}
    queue = payload.get("approval_queue_write") or {}
    return "\n".join(
        [
            "Phase 11 Chat Workspace Proposal Writer",
            f"  status: {payload.get('status')}",
            f"  proposal_kind: {summary.get('proposal_kind')}",
            f"  proposal_id: {summary.get('proposal_id')}",
            f"  proposal_digest: {digest.get('proposal_digest')}",
            f"  approval_request_created: {summary.get('approval_request_created')}",
            f"  approval_id: {summary.get('approval_id') or 'none'}",
            f"  approval_artifact_path: {queue.get('approval_artifact_path') or 'none'}",
            f"  target_path: {summary.get('target_path_preview')}",
            f"  target_file_written: {summary.get('target_file_written')}",
            f"  next: {summary.get('next_recommended_pass')}",
            "  Boundary: approval queue artifact only after exact digest; no Chat state write, Discord API call, Agent Bus task, board/schedule mutation, provider call, or canonical writeback.",
        ]
    )
