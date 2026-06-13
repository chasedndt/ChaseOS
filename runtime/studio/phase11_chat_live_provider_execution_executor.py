"""Phase 11 Chat live-provider execution executor.

This governed executor turns a digest-bound Chat provider preview into one
credential-safe provider call plus a redacted execution record. It reads a
provider secret only to set the outbound Authorization header; it never returns,
writes, or logs the secret value.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any
from urllib import error, request

from runtime.studio.phase11_chat_live_provider_approval_preview import (
    APPROVAL_CLASS,
    build_phase11_chat_live_provider_execution_approval_preview,
)
from runtime.studio.service import ActionSpec, ApprovalRequest, StudioService


MODEL_VERSION = "studio.phase11_chat_live_provider_execution_executor.v1"
SURFACE_ID = "phase11_chat_live_provider_execution_executor"
PASS_ID = "phase11-chat-live-provider-execution-executor"
STATUS = "COMPLETE / APPROVAL-CONSUMED / VERIFIED / PROVIDER RESPONSE WRITTEN"
NEXT_RECOMMENDED_PASS = "studio-chat-full-authority-manual-ui-test"
APPROVAL_ACTION_TYPE = "chat_provider_call"
APPROVAL_TARGET_PATH = "runtime/studio/chat/provider-executions"
MARKER_DIR = Path("runtime/studio/approvals/_provider_execution_markers")
OUTPUT_DIR = Path("runtime/studio/chat/provider-executions")
AUDIT_DIR = Path("07_LOGS") / "Agent-Activity"

_PROVIDER_ENV_REFS: dict[str, str | None] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "ollama": None,  # local; no API key required
}


def _provider_endpoint(provider_id: str) -> str | None:
    if provider_id == "openai":
        return "https://api.openai.com/v1/chat/completions"
    if provider_id == "anthropic":
        return "https://api.anthropic.com/v1/messages"
    if provider_id == "ollama":
        base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        return f"{base}/v1/chat/completions"
    base = os.environ.get("OPENAI_COMPATIBLE_BASE_URL", "").rstrip("/")
    return f"{base}/v1/chat/completions" if base else None


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(value: str | None) -> str:
    return " ".join(str(value or "").strip().split())


def _safe_id(value: str | None) -> str:
    return "".join(c if c.isalnum() or c == "-" else "_" for c in str(value or ""))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _write_approval(service: StudioService, req: ApprovalRequest) -> None:
    service._write_approval_record(req)  # type: ignore[attr-defined]


def _provider_env_ref(provider_id: str | None) -> str | None:
    return _PROVIDER_ENV_REFS.get(str(provider_id or "").lower())


def _extract_output_text(payload: dict[str, Any]) -> str:
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    chunks: list[str] = []
    for item in payload.get("output") or []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content") or []:
            if not isinstance(content, dict):
                continue
            text = content.get("text")
            if isinstance(text, str) and text.strip():
                chunks.append(text.strip())
    return "\n".join(chunks).strip()


def _call_provider_api(
    *,
    provider_id: str,
    api_key: str | None,
    model: str,
    message: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    endpoint = _provider_endpoint(provider_id)
    if not endpoint:
        return {
            "ok": False,
            "status_code": None,
            "error_type": "config_error",
            "reason": f"no endpoint configured for provider '{provider_id}'; set OPENAI_COMPATIBLE_BASE_URL or use a supported provider",
            "raw_response_included": False,
        }

    if provider_id == "anthropic":
        body = json.dumps({
            "model": model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": message}],
        }).encode("utf-8")
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        if api_key:
            headers["x-api-key"] = api_key
    else:
        body = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": message}],
        }).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

    req = request.Request(endpoint, data=body, method="POST", headers=headers)
    try:
        with request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            payload = json.loads(raw) if raw else {}
            output_text = _extract_output_text(payload)
            if not output_text and provider_id == "anthropic":
                for block in payload.get("content") or []:
                    if isinstance(block, dict) and block.get("type") == "text":
                        output_text = str(block.get("text", ""))
                        break
            return {
                "ok": True,
                "status_code": getattr(resp, "status", None),
                "response_id": payload.get("id"),
                "output_text": output_text,
                "raw_response_included": False,
            }
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:800]
        return {
            "ok": False,
            "status_code": exc.code,
            "error_type": "http_error",
            "reason": detail,
            "raw_response_included": False,
        }
    except Exception as exc:
        return {
            "ok": False,
            "status_code": None,
            "error_type": exc.__class__.__name__,
            "reason": str(exc),
            "raw_response_included": False,
        }


def _authority() -> dict[str, bool]:
    return {
        "approval_queue_write_allowed": True,
        "approval_consumption_allowed": True,
        "approval_status_mutation_allowed": True,
        "exact_once_marker_write_allowed": True,
        "provider_calls_allowed": True,
        "model_output_generation_allowed": True,
        "credential_env_reference_allowed": True,
        "credential_value_display_allowed": False,
        "secret_value_returned": False,
        "provider_config_write_allowed": False,
        "conversation_persistence_allowed": False,
        "target_vault_write_allowed": False,
        "runtime_dispatch_allowed": False,
        "agent_bus_task_write_allowed": False,
        "browser_control_allowed": False,
        "workflow_execution_allowed": False,
        "canonical_mutation_allowed": False,
    }


def _approval_content(
    *,
    normalized_message: str,
    provider_digest: str,
    provider_id: str,
    model: str,
    env_ref: str,
) -> str:
    return json.dumps(
        {
            "schema_version": "phase11_chat_live_provider_execution_approval.v1",
            "surface": SURFACE_ID,
            "pass": PASS_ID,
            "approval_class": APPROVAL_CLASS,
            "provider_digest": provider_digest,
            "message_sha256": _sha256_text(normalized_message),
            "provider_id": provider_id,
            "model": model,
            "credential_env_ref": env_ref,
            "credential_value_included": False,
            "provider_config_write_allowed": False,
            "conversation_persistence_allowed": False,
            "runtime_dispatch_allowed": False,
            "agent_bus_task_write_allowed": False,
            "canonical_mutation_allowed": False,
        },
        indent=2,
        sort_keys=True,
    ) + "\n"


def _new_approval_request(
    *,
    service: StudioService,
    normalized_message: str,
    provider_digest: str,
    provider_id: str,
    model: str,
    env_ref: str,
    operator_id: str,
) -> ApprovalRequest:
    spec = ActionSpec(
        action_type=APPROVAL_ACTION_TYPE,
        target_path=APPROVAL_TARGET_PATH,
        content=_approval_content(
            normalized_message=normalized_message,
            provider_digest=provider_digest,
            provider_id=provider_id,
            model=model,
            env_ref=env_ref,
        ),
        metadata={
            "pass": PASS_ID,
            "phase": "Phase 11",
            "source_surface": SURFACE_ID,
            "approval_class": APPROVAL_CLASS,
            "phase11_chat_provider_digest": provider_digest,
            "provider_id": provider_id,
            "model": model,
            "credential_env_ref": env_ref,
            "credential_value_included": False,
            "provider_call_performed": False,
            "operator_confirmation": operator_id,
        },
        submitted_by="studio-chat",
        note="Phase 11 Chat live-provider execution approval; credential values are never displayed.",
    )
    return service.queue_for_approval(spec)


def _blocked_payload(
    *,
    vault: Path,
    preview: dict[str, Any],
    expected_provider_digest: str,
    approval_id: str,
    blockers: list[str],
) -> dict[str, Any]:
    unique = list(dict.fromkeys(blockers))
    digest = preview.get("request_digest_proof") or {}
    summary = preview.get("summary") or {}
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": "BLOCKED / LIVE PROVIDER EXECUTION / NO PROVIDER CALL",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": False,
        "approval_gated": True,
        "summary": {
            "approval_id": approval_id or None,
            "expected_provider_digest_provided": bool(expected_provider_digest),
            "provider_digest_matched": False,
            "selected_provider_id": summary.get("selected_provider_id"),
            "selected_model": summary.get("selected_model"),
            "approval_consumed": False,
            "provider_call_performed": False,
            "model_output_generated": False,
            "credential_env_reference_used": False,
            "credential_value_displayed": False,
            "conversation_log_written": False,
            "blocker_count": len(unique),
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "provider_preview": preview,
        "digest_proof": {
            "expected_provider_digest": expected_provider_digest or None,
            "provider_digest": digest.get("request_digest"),
            "provider_digest_matched": False,
        },
        "approval_record": {
            "approval_id": approval_id or None,
            "approval_written": False,
            "approval_status": None,
        },
        "provider_call": {
            "provider_call_performed": False,
            "credential_env_ref": None,
            "credential_value_displayed": False,
            "secret_value_returned": False,
        },
        "authority": _authority(),
        "blocked_reasons": unique,
        "warnings": [],
    }


def _write_output_record(
    *,
    vault: Path,
    provider_digest: str,
    approval_id: str,
    provider_id: str,
    model: str,
    call_result: dict[str, Any],
) -> str:
    root = vault / OUTPUT_DIR
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"provider-execution-{provider_digest[:20]}.json"
    payload = {
        "schema_version": "phase11_chat_provider_execution_result.v1",
        "surface": SURFACE_ID,
        "pass": PASS_ID,
        "approval_id": approval_id,
        "provider_digest": provider_digest,
        "provider_id": provider_id,
        "model": model,
        "generated_at_utc": _now_utc(),
        "provider_call_performed": True,
        "credential_value_displayed": False,
        "secret_value_returned": False,
        "result": call_result,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return _rel(vault, path)


def _write_audit(
    *,
    vault: Path,
    approval_id: str,
    provider_digest: str,
    provider_id: str,
    model: str,
    output_path: str,
    operator_id: str,
) -> str:
    root = vault / AUDIT_DIR
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{PASS_ID}-{provider_digest[:20]}.md"
    text = "\n".join(
        [
            "---",
            "type: agent-activity",
            "runtime: Codex",
            f"pass_id: {PASS_ID}",
            f"approval_id: {approval_id}",
            f"status: {STATUS}",
            "---",
            "",
            "# Phase 11 Chat Live Provider Execution",
            "",
            f"operator_id: {operator_id}",
            f"approval_id: {approval_id}",
            f"provider_digest: {provider_digest}",
            f"provider_id: {provider_id}",
            f"model: {model}",
            f"output_path: {output_path}",
            "provider_call_performed: true",
            "credential_env_reference_used: true",
            "credential_value_displayed: false",
            "conversation_log_written: false",
            "runtime_dispatch_performed: false",
            "agent_bus_task_written: false",
            "canonical_mutation_performed: false",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")
    return _rel(vault, path)


def execute_phase11_chat_live_provider_execution(
    vault_root: str | Path,
    *,
    approval_id: str | None = None,
    message: str | None = None,
    explicit_intent: str | None = "chat-answer",
    expected_provider_digest: str | None = None,
    operator_id: str = "operator",
    operator_approval_statement: str | None = None,
    requested_provider_id: str | None = None,
    requested_model: str | None = None,
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    """Consume approval and perform one redacted live provider call."""

    vault = Path(vault_root).resolve()
    normalized_message = _norm(message)
    expected = str(expected_provider_digest or "").strip()
    operator = str(operator_id or "operator").strip() or "operator"
    approval_statement = _norm(operator_approval_statement)
    requested_approval_id = str(approval_id or "").strip()
    preview = build_phase11_chat_live_provider_execution_approval_preview(
        vault,
        message=normalized_message,
        explicit_intent=explicit_intent or "chat-answer",
        requested_provider_id=requested_provider_id,
        requested_model=requested_model,
    )
    digest = preview.get("request_digest_proof") or {}
    provider_digest = str(digest.get("request_digest") or "")
    summary = preview.get("summary") or {}
    provider_id = str(summary.get("selected_provider_id") or requested_provider_id or "")
    model = str(summary.get("selected_model") or requested_model or "")
    env_ref = _provider_env_ref(provider_id)

    hard_preview_blockers = {
        "message_required_for_live_provider_approval_preview",
        "intent_not_model_bound_for_provider_execution",
        "prompt_injection_indicator_present",
        "conversation_target_unexpectedly_written",
    }
    blockers = [str(item) for item in (preview.get("blocked_reasons") or []) if str(item) in hard_preview_blockers]
    if not expected:
        blockers.append("expected_provider_digest_required")
    elif expected != provider_digest:
        blockers.append("provider_digest_mismatch")
    if not approval_statement and not requested_approval_id:
        blockers.append("operator_approval_statement_required_for_live_provider_execution")
    if not model:
        blockers.append("provider_model_missing")
    if not env_ref:
        blockers.append("credential_env_ref_missing_for_provider")
    elif not os.environ.get(env_ref):
        blockers.append("provider_credential_environment_missing")

    marker_path = vault / MARKER_DIR / f"{_safe_id(requested_approval_id) or provider_digest[:20]}.json"
    if marker_path.exists():
        blockers.append("exact_once_marker_already_present")

    if blockers:
        return _blocked_payload(
            vault=vault,
            preview=preview,
            expected_provider_digest=expected,
            approval_id=requested_approval_id,
            blockers=blockers,
        )

    service = StudioService(vault)
    req: ApprovalRequest | None = None
    if requested_approval_id:
        req = service.get_approval(requested_approval_id)
        if req is None:
            return _blocked_payload(
                vault=vault,
                preview=preview,
                expected_provider_digest=expected,
                approval_id=requested_approval_id,
                blockers=["approval_request_not_loadable"],
            )
    else:
        req = _new_approval_request(
            service=service,
            normalized_message=normalized_message,
            provider_digest=provider_digest,
            provider_id=provider_id,
            model=model,
            env_ref=str(env_ref),
            operator_id=operator,
        )
        requested_approval_id = req.approval_id
        marker_path = vault / MARKER_DIR / f"{_safe_id(requested_approval_id)}.json"

    assert req is not None
    if req.status not in {"pending", "approved"}:
        return _blocked_payload(
            vault=vault,
            preview=preview,
            expected_provider_digest=expected,
            approval_id=requested_approval_id,
            blockers=["approval_status_not_approved_or_pending_with_statement"],
        )

    execution_id = f"provider-execution-{provider_digest[:20]}"
    try:
        if req.status == "pending" and approval_statement:
            req.status = "approved"
            req.reviewed_by = operator
            req.reason = approval_statement
            req.updated_at = _now_utc()
            _write_approval(service, req)

        req.status = "executing"
        req.execution_id = execution_id
        req.execution_started_at = _now_utc()
        req.execution_finished_at = None
        req.execution_status = None
        req.execution_error = ""
        req.updated_at = req.execution_started_at
        _write_approval(service, req)

        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text(
            json.dumps(
                {
                    "schema_version": "phase11_chat_provider_execution_marker.v1",
                    "status": "executing",
                    "approval_id": requested_approval_id,
                    "execution_id": execution_id,
                    "provider_digest": provider_digest,
                    "provider_call_performed": False,
                    "credential_value_displayed": False,
                    "updated_at_utc": _now_utc(),
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        api_key = os.environ.get(str(env_ref)) if env_ref else None
        call_result = _call_provider_api(
            provider_id=provider_id,
            api_key=api_key,
            model=model,
            message=normalized_message,
            timeout_seconds=max(1, int(timeout_seconds or 60)),
        )
        if not call_result.get("ok"):
            raise RuntimeError(f"provider_call_failed:{call_result.get('error_type') or call_result.get('status_code')}:{call_result.get('reason')}")
        output_path = _write_output_record(
            vault=vault,
            provider_digest=provider_digest,
            approval_id=requested_approval_id,
            provider_id=provider_id,
            model=model,
            call_result=call_result,
        )
        audit_path = _write_audit(
            vault=vault,
            approval_id=requested_approval_id,
            provider_digest=provider_digest,
            provider_id=provider_id,
            model=model,
            output_path=output_path,
            operator_id=operator,
        )

        marker_path.write_text(
            json.dumps(
                {
                    "schema_version": "phase11_chat_provider_execution_marker.v1",
                    "status": "executed",
                    "approval_id": requested_approval_id,
                    "execution_id": execution_id,
                    "provider_digest": provider_digest,
                    "provider_call_performed": True,
                    "credential_value_displayed": False,
                    "output_path": output_path,
                    "updated_at_utc": _now_utc(),
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        req.status = "executed"
        req.execution_finished_at = _now_utc()
        req.execution_status = "completed"
        req.result_action_id = output_path
        req.execution_error = ""
        req.updated_at = req.execution_finished_at
        metadata = dict(req.action_spec.metadata or {})
        metadata.update(
            {
                "provider_call_performed": True,
                "credential_env_reference_used": True,
                "credential_value_displayed": False,
                "output_path": output_path,
            }
        )
        req.action_spec.metadata = metadata
        _write_approval(service, req)
    except Exception as exc:
        error_text = str(exc)
        try:
            req.status = "execution_failed"
            req.execution_finished_at = _now_utc()
            req.execution_status = "error"
            req.execution_error = error_text
            req.updated_at = req.execution_finished_at
            _write_approval(service, req)
        except Exception:
            pass
        failed = _blocked_payload(
            vault=vault,
            preview=preview,
            expected_provider_digest=expected,
            approval_id=requested_approval_id,
            blockers=[f"provider_execution_failed:{error_text}"],
        )
        failed["status"] = "FAILED / LIVE PROVIDER EXECUTION / CHECK PROVIDER RESULT"
        return failed

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
            "approval_id": requested_approval_id,
            "expected_provider_digest_provided": True,
            "provider_digest_matched": True,
            "selected_provider_id": provider_id,
            "selected_model": model,
            "approval_consumed": True,
            "approval_status_mutated": True,
            "exact_once_marker_written": True,
            "provider_call_performed": True,
            "model_output_generated": True,
            "credential_env_reference_used": True,
            "credential_value_displayed": False,
            "secret_value_returned": False,
            "conversation_log_written": False,
            "runtime_dispatch_performed": False,
            "agent_bus_task_written": False,
            "canonical_mutation_performed": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "blocker_count": 0,
        },
        "provider_preview": preview,
        "digest_proof": {
            "expected_provider_digest": expected,
            "provider_digest": provider_digest,
            "provider_digest_matched": True,
        },
        "approval_record": {
            "approval_id": requested_approval_id,
            "approval_written": True,
            "approval_status": "executed",
        },
        "provider_call": {
            "provider_call_performed": True,
            "provider_id": provider_id,
            "model": model,
            "credential_env_ref": env_ref,
            "credential_value_displayed": False,
            "secret_value_returned": False,
            "output_text_preview": str(call_result.get("output_text") or "")[:1200],
            "output_path": output_path,
        },
        "audit_record": {
            "audit_written": True,
            "audit_record_path": audit_path,
        },
        "authority": _authority(),
        "blocked_reasons": [],
        "warnings": [],
    }


def format_phase11_chat_live_provider_execution(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    call = payload.get("provider_call") or {}
    digest = payload.get("digest_proof") or {}
    return "\n".join(
        [
            "Phase 11 Chat Live Provider Execution",
            f"  status: {payload.get('status')}",
            f"  provider: {summary.get('selected_provider_id')}",
            f"  model: {summary.get('selected_model')}",
            f"  provider_digest: {digest.get('provider_digest')}",
            f"  approval_id: {summary.get('approval_id')}",
            f"  provider_call_performed: {summary.get('provider_call_performed')}",
            f"  output_path: {call.get('output_path')}",
            "  Boundary: credential env reference only; no secret value display, provider config mutation, runtime dispatch, Agent Bus write, or canonical mutation.",
        ]
    )
