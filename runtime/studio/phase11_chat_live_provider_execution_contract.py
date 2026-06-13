"""Approved Phase 11 Chat live-provider execution contract.

This module is the lower-phase governance proof for Chat-originated live model
calls. It consumes the read-only RPGL readiness/route preview, writes a bounded
approval packet only when the caller supplies the exact request digest, executes
only approved packets, passes credential references (not values) to a provider
runner, and persists inspectable conversation + Agent-Activity audit records.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Callable

from runtime.studio.phase11_chat_live_provider_approval_preview import (
    APPROVAL_CLASS,
    build_phase11_chat_live_provider_execution_approval_preview,
)


MODEL_VERSION = "studio.phase11_chat_live_provider_execution_contract.v1"
SURFACE_ID = "phase11_chat_live_provider_execution_contract"
PASS_ID = "phase11-chat-live-provider-execution-contract-proof"
STATUS_PREVIEW = "READY / APPROVAL-PACKET-PREVIEW / PROVIDER CALLS BLOCKED"
STATUS_APPROVAL_WRITTEN = "COMPLETE / APPROVAL-PACKET-WRITTEN / EXECUTION BLOCKED"
STATUS_EXECUTED = "COMPLETE / APPROVED LIVE-PROVIDER EXECUTION / AUDITED"
STATUS_BLOCKED = "BLOCKED / LIVE-PROVIDER EXECUTION DENIED"
APPROVAL_RELATIVE_DIR = Path("runtime/studio/approvals/chat-provider-executions")
MARKER_RELATIVE_DIR = Path("runtime/studio/chat-provider-executions/markers")
RESULT_RELATIVE_DIR = Path("runtime/studio/chat-provider-executions/results")
CONVERSATION_RELATIVE_DIR = Path("07_LOGS/Conversations")
AGENT_ACTIVITY_RELATIVE_DIR = Path("07_LOGS/Agent-Activity")
MAX_PROMPT_CHARS = 4000
MAX_OUTPUT_CHARS = 2000
_SECRET_LIKE_PATTERN = re.compile(
    r"(?i)(sk-[a-z0-9][a-z0-9._-]{8,}|[a-z0-9._-]{8,}[-_](?:secret|token|password|credential)[-_][a-z0-9._-]{4,})"
)

ProviderRunner = Callable[[dict[str, Any]], dict[str, Any] | str]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(message: str | None) -> str:
    return " ".join(str(message or "").strip().split())


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value: str, length: int = 20) -> str:
    return _sha256_text(value)[:length]


def _safe_id(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value or "")).strip("-._")
    return text[:96] or f"chat-provider-exec-{_digest(_now_utc())}"


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return str(path)


def _approval_path(vault: Path, approval_id: str) -> Path:
    safe = _safe_id(approval_id)
    base = (vault / APPROVAL_RELATIVE_DIR).resolve()
    path = (base / f"{safe}.json").resolve()
    path.relative_to(base)
    return path


def _marker_path(vault: Path, approval_id: str) -> Path:
    safe = _safe_id(approval_id)
    base = (vault / MARKER_RELATIVE_DIR).resolve()
    path = (base / f"{safe}.json").resolve()
    path.relative_to(base)
    return path


def _result_path(vault: Path, approval_id: str) -> Path:
    safe = _safe_id(approval_id)
    base = (vault / RESULT_RELATIVE_DIR).resolve()
    path = (base / f"{safe}.json").resolve()
    path.relative_to(base)
    return path


def _conversation_path(vault: Path, request_digest: str) -> Path:
    day = datetime.now(timezone.utc).date().isoformat()
    base = (vault / CONVERSATION_RELATIVE_DIR).resolve()
    path = (base / f"{day}_chat-provider-execution-{_digest(request_digest, 16)}.md").resolve()
    path.relative_to(base)
    return path


def _agent_activity_path(vault: Path, request_digest: str) -> Path:
    day = datetime.now(timezone.utc).date().isoformat()
    base = (vault / AGENT_ACTIVITY_RELATIVE_DIR).resolve()
    path = (base / f"{day}-hermes-optimus-chat-live-provider-execution-{_digest(request_digest, 12)}.md").resolve()
    path.relative_to(base)
    return path


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _write_json_create_new(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(str(path))
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_json_replace(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _provider_env_ref(preview: dict[str, Any]) -> str | None:
    credential = ((preview.get("provider_preflight") or {}).get("provider_readiness") or {}).get("credential_posture") or {}
    return credential.get("primary_provider_env_ref")


def _selected_provider(preview: dict[str, Any]) -> dict[str, Any]:
    return (preview.get("future_provider_execution_preview") or {}).get("selected_route_preview") or {}


def _contains_secret_like_value(value: str) -> bool:
    return bool(_SECRET_LIKE_PATTERN.search(str(value or "")))


def _contains_secret(value: str) -> bool:
    text = str(value or "")
    lowered = text.lower()
    if _contains_secret_like_value(text):
        return True
    return any(marker in lowered for marker in ("secret", "token", "password", "credential"))


def _redacted_text(value: str) -> str:
    text = str(value or "")[:MAX_OUTPUT_CHARS]
    text = _SECRET_LIKE_PATTERN.sub("[redacted-secret]", text)
    return text


def _approval_packet(
    *,
    vault: Path,
    preview: dict[str, Any],
    request_digest: str,
    approval_id: str,
    credential_env_ref: str | None,
    operator_id: str,
) -> dict[str, Any]:
    selection = _selected_provider(preview)
    digest_proof = preview.get("request_digest_proof") or {}
    conversation = preview.get("conversation_audit_preflight") or {}
    return {
        "record_type": "phase11_chat_live_provider_execution_approval",
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "created_at_utc": _now_utc(),
        "approval_id": approval_id,
        "status": "pending",
        "required_approval_class": APPROVAL_CLASS,
        "requested_by": operator_id or "operator",
        "request_digest": request_digest,
        "prompt_message_sha256": digest_proof.get("prompt_message_sha256"),
        "intent_class": (preview.get("summary") or {}).get("intent_class"),
        "provider_id": selection.get("provider_id"),
        "model": selection.get("model"),
        "credential_env_ref": credential_env_ref,
        "credential_env_present_at_request": bool(credential_env_ref and credential_env_ref in os.environ),
        "secret_reference_metadata_only": True,
        "credential_value_included": False,
        "raw_credentials_included": False,
        "conversation_target_path": conversation.get("target_path_preview"),
        "bounded_call_policy": {
            "max_prompt_chars": MAX_PROMPT_CHARS,
            "max_output_chars": MAX_OUTPUT_CHARS,
            "single_turn_only": True,
            "streaming_disabled_for_contract": True,
        },
        "execution_allowed_after_approval_only": True,
        "canonical_writeback_allowed": False,
    }


def _write_conversation(
    *,
    vault: Path,
    request_digest: str,
    message: str,
    provider_text: str,
    approval_id: str,
    provider_id: str | None,
    model: str | None,
) -> str:
    path = _conversation_path(vault, request_digest)
    content = "\n".join(
        [
            "---",
            "type: conversation-log",
            "status: approved-live-provider-execution",
            "generated_by: phase11-chat-live-provider-execution-contract",
            "runtime: hermes-optimus",
            "canonical_memory: false",
            "hidden_memory: false",
            f"approval_id: {approval_id}",
            f"request_digest: {request_digest}",
            f"provider_id: {provider_id}",
            f"model: {model}",
            "secret_values_persisted: false",
            "---",
            "",
            "# Phase 11 Chat Live Provider Conversation",
            "",
            "## Operator Message",
            "",
            message,
            "",
            "## Provider Response",
            "",
            provider_text,
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return _rel(vault, path)


def _write_agent_activity(
    *,
    vault: Path,
    request_digest: str,
    approval_id: str,
    conversation_ref: str,
    provider_id: str | None,
    model: str | None,
) -> str:
    path = _agent_activity_path(vault, request_digest)
    content = "\n".join(
        [
            "---",
            "runtime: hermes-optimus",
            "lane: Optimus",
            "status: approved-live-provider-execution-proof",
            "related:",
            "  - \"[[Hermes-Runtime-Profile]]\"",
            "  - \"[[HERMES]]\"",
            "  - \"[[Agent-Activity-Index]]\"",
            "---",
            "",
            "# Hermes/Optimus Chat Live-Provider Execution Proof",
            "",
            "This Agent-Activity record proves a bounded, approval-gated Phase 11 Chat provider execution path.",
            "",
            "## Evidence",
            "",
            f"- Approval id: `{approval_id}`",
            f"- Request digest: `{request_digest}`",
            f"- Provider/model: `{provider_id}` / `{model}`",
            f"- Conversation audit: `{conversation_ref}`",
            "- Credential handling: environment reference metadata only; raw credential values were not read into output or persisted.",
            "- ChaseOS OS alignment: Chat remains an operator surface; RPGL/provider governance owns the lower-phase execution contract and writes inspectable audit evidence.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return _rel(vault, path)


def build_phase11_chat_live_provider_execution_contract(
    vault_root: str | Path,
    *,
    message: str | None = None,
    explicit_intent: str | None = None,
    requested_provider_id: str | None = None,
    requested_model: str | None = None,
    approval_id: str | None = None,
    expected_request_digest: str | None = None,
    write_approval: bool = False,
    execute: bool = False,
    provider_runner: ProviderRunner | None = None,
    operator_id: str = "operator",
) -> dict[str, Any]:
    """Preview, write, or execute one approved Chat live-provider call."""

    vault = Path(vault_root).resolve()
    normalized_message = _norm(message)
    preview = build_phase11_chat_live_provider_execution_approval_preview(
        vault,
        message=normalized_message,
        explicit_intent=explicit_intent,
        requested_provider_id=requested_provider_id,
        requested_model=requested_model,
    )
    request_digest = str((preview.get("request_digest_proof") or {}).get("request_digest") or "")
    selected = _selected_provider(preview)
    credential_env_ref = _provider_env_ref(preview)
    operator_prompt_secret_like_detected = _contains_secret_like_value(normalized_message)
    selected_approval_id = _safe_id(approval_id or f"chat-provider-exec-appr-{_digest(request_digest)}")
    approval_file = _approval_path(vault, selected_approval_id)
    marker_file = _marker_path(vault, selected_approval_id)
    result_file = _result_path(vault, selected_approval_id)

    blockers: list[str] = list(preview.get("blocked_reasons") or [])
    warnings: list[str] = []
    if operator_prompt_secret_like_detected:
        blockers.append("operator_prompt_failed_secret_exposure_scan")
    if (preview.get("summary") or {}).get("provider_route_status") != "route_contract_satisfied":
        blockers.append("provider_route_contract_not_satisfied")
    if (preview.get("summary") or {}).get("provider_readiness_status") != "verified_by_last_probe_result":
        blockers.append("provider_readiness_not_verified_by_last_probe_result")
    if not credential_env_ref or credential_env_ref not in os.environ:
        blockers.append("primary_provider_credential_or_environment_missing")
    if write_approval and not expected_request_digest:
        blockers.append("expected_request_digest_required_for_approval_packet_write")
    if expected_request_digest and expected_request_digest != request_digest:
        blockers.append("expected_request_digest_mismatch")
    if write_approval and approval_file.exists():
        blockers.append("approval_packet_already_exists")
    if execute:
        packet = _read_json(approval_file) if approval_id else None
        if not approval_id or packet is None:
            blockers.append("approval_packet_missing")
        else:
            if packet.get("status") != "approved":
                blockers.append("approval_packet_not_approved")
            if packet.get("request_digest") != request_digest:
                blockers.append("approval_packet_request_digest_mismatch")
            if packet.get("provider_id") != selected.get("provider_id"):
                blockers.append("approval_packet_provider_mismatch")
            if packet.get("model") != selected.get("model"):
                blockers.append("approval_packet_model_mismatch")
        if provider_runner is None:
            blockers.append("provider_runner_missing_for_bounded_live_call")
        if marker_file.exists() or result_file.exists():
            blockers.append("approval_execution_already_consumed")

    hard_blockers = list(dict.fromkeys(blockers))
    approval_packet: dict[str, Any] | None = None
    approval_request_created = False
    provider_call_performed = False
    conversation_ref: str | None = None
    audit_ref: str | None = None
    result_ref: str | None = None
    status = STATUS_PREVIEW
    ok = not any(
        reason
        in {
            "message_required_for_live_provider_approval_preview",
            "intent_not_model_bound_for_provider_execution",
            "prompt_injection_indicator_present",
            "operator_prompt_failed_secret_exposure_scan",
            "provider_route_contract_not_satisfied",
            "provider_readiness_not_verified_by_last_probe_result",
            "primary_provider_credential_or_environment_missing",
            "expected_request_digest_required_for_approval_packet_write",
            "expected_request_digest_mismatch",
            "approval_packet_already_exists",
            "approval_packet_missing",
            "approval_packet_not_approved",
            "approval_packet_request_digest_mismatch",
            "approval_packet_provider_mismatch",
            "approval_packet_model_mismatch",
            "provider_runner_missing_for_bounded_live_call",
            "approval_execution_already_consumed",
            "provider_output_failed_secret_exposure_scan",
        }
        for reason in hard_blockers
    )

    if write_approval and ok:
        approval_packet = _approval_packet(
            vault=vault,
            preview=preview,
            request_digest=request_digest,
            approval_id=selected_approval_id,
            credential_env_ref=credential_env_ref,
            operator_id=operator_id,
        )
        _write_json_create_new(approval_file, approval_packet)
        approval_request_created = True
        status = STATUS_APPROVAL_WRITTEN
    elif approval_file.exists():
        approval_packet = _read_json(approval_file)

    provider_output_text: str | None = None
    if execute and ok and provider_runner is not None:
        request = {
            "surface": SURFACE_ID,
            "approval_id": selected_approval_id,
            "request_digest": request_digest,
            "provider_id": selected.get("provider_id"),
            "model": selected.get("model"),
            "credential_env_ref": credential_env_ref,
            "credential_available": bool(credential_env_ref and credential_env_ref in os.environ),
            "prompt": normalized_message[:MAX_PROMPT_CHARS],
            "max_prompt_chars": MAX_PROMPT_CHARS,
            "max_output_chars": MAX_OUTPUT_CHARS,
            "single_turn_only": True,
        }
        raw_response = provider_runner(request)
        provider_call_performed = True
        provider_output_text = raw_response.get("text") if isinstance(raw_response, dict) else str(raw_response)
        provider_output_text = str(provider_output_text or "")[:MAX_OUTPUT_CHARS]
        if _contains_secret(provider_output_text):
            hard_blockers.append("provider_output_failed_secret_exposure_scan")
            ok = False
            status = STATUS_BLOCKED
            provider_output_text = None
        else:
            safe_text = _redacted_text(provider_output_text)
            conversation_ref = _write_conversation(
                vault=vault,
                request_digest=request_digest,
                message=normalized_message,
                provider_text=safe_text,
                approval_id=selected_approval_id,
                provider_id=selected.get("provider_id"),
                model=selected.get("model"),
            )
            audit_ref = _write_agent_activity(
                vault=vault,
                request_digest=request_digest,
                approval_id=selected_approval_id,
                conversation_ref=conversation_ref,
                provider_id=selected.get("provider_id"),
                model=selected.get("model"),
            )
            marker = {
                "record_type": "phase11_chat_live_provider_execution_marker",
                "approval_id": selected_approval_id,
                "request_digest": request_digest,
                "created_at_utc": _now_utc(),
                "conversation_path": conversation_ref,
                "agent_activity_audit_path": audit_ref,
            }
            _write_json_create_new(marker_file, marker)
            result = {
                "record_type": "phase11_chat_live_provider_execution_result",
                "approval_id": selected_approval_id,
                "request_digest": request_digest,
                "created_at_utc": _now_utc(),
                "provider_id": selected.get("provider_id"),
                "model": selected.get("model"),
                "provider_call_performed": True,
                "credential_value_read_into_output": False,
                "conversation_path": conversation_ref,
                "agent_activity_audit_path": audit_ref,
            }
            _write_json_create_new(result_file, result)
            result_ref = _rel(vault, result_file)
            approval_packet = _read_json(approval_file) or {}
            approval_packet.update(
                {
                    "status": "executed",
                    "execution_result_ref": result_ref,
                    "conversation_path": conversation_ref,
                    "agent_activity_audit_path": audit_ref,
                    "updated_at_utc": _now_utc(),
                }
            )
            _write_json_replace(approval_file, approval_packet)
            status = STATUS_EXECUTED
    elif not ok:
        status = STATUS_BLOCKED

    unique_blockers = list(dict.fromkeys(hard_blockers))
    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": status,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "approval_gated": True,
        "summary": {
            "message_present": bool(normalized_message),
            "intent_class": (preview.get("summary") or {}).get("intent_class"),
            "approval_packet_ready": not unique_blockers and bool(request_digest),
            "write_approval_requested": bool(write_approval),
            "approval_request_created": approval_request_created,
            "approval_id": selected_approval_id if (approval_request_created or approval_file.exists() or approval_id) else None,
            "execute_requested": bool(execute),
            "provider_call_performed": provider_call_performed,
            "conversation_log_written": bool(conversation_ref),
            "agent_activity_audit_written": bool(audit_ref),
            "provider_id": selected.get("provider_id"),
            "model": selected.get("model"),
            "credential_reference_checked": bool(credential_env_ref),
            "credential_value_included": False,
            "secret_values_visible": False,
            "operator_prompt_secret_like_detected": operator_prompt_secret_like_detected,
            "operator_prompt_secret_policy": "fail_closed_before_approval_write_or_provider_execution",
            "blocker_count": len(unique_blockers),
        },
        "request_digest_proof": {
            "request_digest": request_digest,
            "expected_request_digest": expected_request_digest,
            "expected_digest_matched": bool(expected_request_digest and expected_request_digest == request_digest),
            "prompt_message_sha256": (preview.get("request_digest_proof") or {}).get("prompt_message_sha256"),
        },
        "approval_packet": approval_packet
        or {
            "approval_id": selected_approval_id,
            "status": "not_written",
            "approval_path": _rel(vault, approval_file),
            "provider_id": selected.get("provider_id"),
            "model": selected.get("model"),
            "credential_env_ref": credential_env_ref,
            "secret_reference_metadata_only": True,
            "credential_value_included": False,
        },
        "provider_selection": {
            "provider_id": selected.get("provider_id"),
            "model": selected.get("model"),
            "route_ready": bool(selected.get("route_ready")),
            "routing_status": (preview.get("summary") or {}).get("provider_route_status"),
            "readiness_status": (preview.get("summary") or {}).get("provider_readiness_status"),
            "safe_provider_selection": bool(selected.get("provider_id") and selected.get("model")),
        },
        "credential_posture": {
            "credential_env_ref": credential_env_ref,
            "credential_env_present": bool(credential_env_ref and credential_env_ref in os.environ),
            "secret_reference_metadata_only": True,
            "credential_value_read_into_output": False,
            "raw_credentials_included": False,
        },
        "bounded_live_call": {
            "provider_runner_required": True,
            "provider_call_performed": provider_call_performed,
            "max_prompt_chars": MAX_PROMPT_CHARS,
            "max_output_chars": MAX_OUTPUT_CHARS,
            "single_turn_only": True,
            "model_output_generated": provider_call_performed and ok,
            "model_output_text": _redacted_text(provider_output_text) if provider_output_text and ok else None,
        },
        "conversation_audit": {
            "conversation_path": conversation_ref,
            "conversation_log_written": bool(conversation_ref),
            "canonical_memory": False,
            "hidden_memory": False,
            "operator_prompt_secret_like_detected": operator_prompt_secret_like_detected,
            "operator_prompt_persistence_policy": "fail_closed_before_conversation_write",
            "secret_values_persisted": False,
        },
        "agent_activity_audit": {
            "audit_path": audit_ref,
            "agent_activity_audit_written": bool(audit_ref),
            "required_graph_links": ["[[Hermes-Runtime-Profile]]", "[[HERMES]]", "[[Agent-Activity-Index]]"],
        },
        "execution_records": {
            "approval_path": _rel(vault, approval_file),
            "marker_path": _rel(vault, marker_file) if marker_file.exists() else None,
            "result_path": result_ref,
            "marker_written": marker_file.exists(),
            "result_written": bool(result_ref),
        },
        "source_preview": {
            "surface": preview.get("surface"),
            "model_version": preview.get("model_version"),
            "authority_boundary_consumed": True,
        },
        "authority": {
            "approval_packet_write_allowed_with_digest": True,
            "approval_execution_allowed_with_approved_packet": True,
            "provider_calls_allowed_after_approval": bool(execute and ok),
            "credential_values_visible": False,
            "provider_config_write_allowed": False,
            "runtime_dispatch_allowed": False,
            "browser_control_allowed": False,
            "agent_bus_task_write_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "blocked_reasons": unique_blockers,
        "warnings": list(dict.fromkeys(warnings)),
    }


def format_phase11_chat_live_provider_execution_contract(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    return "\n".join(
        [
            "Phase 11 Chat Live Provider Execution Contract",
            f"  status: {payload.get('status')}",
            f"  provider: {summary.get('provider_id')}",
            f"  model: {summary.get('model')}",
            f"  approval_id: {summary.get('approval_id')}",
            f"  approval_request_created: {summary.get('approval_request_created')}",
            f"  provider_call_performed: {summary.get('provider_call_performed')}",
            f"  conversation_log_written: {summary.get('conversation_log_written')}",
            f"  agent_activity_audit_written: {summary.get('agent_activity_audit_written')}",
            "  Boundary: approved bounded provider call only; credential values are never returned or persisted, and canonical/provider-config/runtime/browser mutations remain blocked.",
        ]
    )
