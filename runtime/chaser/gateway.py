"""N7 governed Chaser Gateway ingress facade.

This is an internal structured ingress router, not a network server. It wraps
existing board/terminal contracts behind explicit local-operator authorization
checks and preserves the authority boundaries of each downstream lane.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SURFACE = "chaser_gateway_ingress"
SCHEMA_VERSION = "chaser_gateway_ingress.v1"
MAX_REQUEST_BYTES = 16_384
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _safe_id(value: str) -> bool:
    return bool(_SAFE_ID_RE.fullmatch(str(value or "")))


def _normalise_intent(intent: str) -> str:
    cleaned = str(intent or "").strip().lower().replace("_", ".").replace("-", ".")
    aliases = {
        "contract": "gateway.contract",
        "gateway": "gateway.contract",
        "board": "board.state",
        "board.state": "board.state",
        "terminal.propose": "terminal.propose",
        "terminal.preview": "terminal.propose",
        "terminal.approval.preview": "terminal.approval_request_preview",
        "terminal.approval.request.preview": "terminal.approval_request_preview",
        "terminal.approval_request_preview": "terminal.approval_request_preview",
        "terminal.approval.write": "terminal.approval_request_write",
        "terminal.approval.request.write": "terminal.approval_request_write",
        "terminal.approval_request_write": "terminal.approval_request_write",
        "terminal.readiness": "terminal.executor_readiness",
        "terminal.executor.readiness": "terminal.executor_readiness",
        "terminal.executor_readiness": "terminal.executor_readiness",
        "terminal.execute": "terminal.execute_approval",
        "terminal.execute.approval": "terminal.execute_approval",
        "terminal.execute_approval": "terminal.execute_approval",
    }
    return aliases.get(cleaned, cleaned)


def _authority_flags(result: dict[str, Any] | None = None) -> dict[str, bool]:
    result = result if isinstance(result, dict) else {}
    nested = result.get("authority") if isinstance(result.get("authority"), dict) else {}
    return {
        "gateway_network_server_now": False,
        "studio_execution_now": False,
        "terminal_execution_now": bool(nested.get("terminal_execution_now") or result.get("terminal_execution_now")),
        "terminal_audit_write_now": bool(nested.get("terminal_audit_write_now") or result.get("terminal_audit_write_now")),
        "approval_queue_write_now": bool(result.get("approval_request_written")),
        "approval_consumption_now": bool(nested.get("approval_consumption_now") or result.get("approval_consumption_now")),
        "exact_once_marker_write_now": bool(
            nested.get("exact_once_marker_write_now") or result.get("exact_once_marker_write_now")
        ),
        "host_mutation_now": bool(nested.get("host_mutation_now") or result.get("host_mutation_now")),
        "agent_bus_write_now": False,
        "provider_call_now": False,
        "canonical_writeback_now": False,
        "external_upload_now": False,
        "profile_activation_now": False,
        "toolset_activation_now": False,
    }


def build_gateway_ingress_contract(vault_root: str | Path) -> dict[str, Any]:
    """Return the N7 ingress contract without routing or executing anything."""

    root = Path(vault_root).resolve()
    return {
        "ok": True,
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "mode": "internal_structured_ingress",
        "vault_root": str(root),
        "updated_at": _now_iso(),
        "authn": {
            "required_for_ingress": True,
            "accepted_mode": "local_operator",
            "session_id_is_not_auth": True,
        },
        "authz": {
            "fail_closed": True,
            "terminal_write_execution_requires": [
                "local_operator_confirmed",
                "operator_approved_terminal_write",
                "payload_confirm_approved_terminal_write",
                "existing_approved_terminal_write_approval",
                "n6_executor_scope_validation",
            ],
            "approval_queue_write_requires": [
                "local_operator_confirmed",
                "approval_queue_write_confirmed",
                "eligible_terminal_write_proposal",
            ],
        },
        "rate_limit": {
            "request_bytes_max": MAX_REQUEST_BYTES,
            "persistent_rate_state": False,
        },
        "supported_intents": [
            {
                "intent": "gateway.contract",
                "writes_now": False,
                "executes_now": False,
                "route": "build_gateway_ingress_contract",
            },
            {
                "intent": "board.state",
                "writes_now": False,
                "executes_now": False,
                "route": "runtime.chaser.board.build_board_state",
            },
            {
                "intent": "terminal.propose",
                "writes_now": False,
                "executes_now": False,
                "route": "runtime.chaser.board.build_action_proposal",
            },
            {
                "intent": "terminal.approval_request_preview",
                "writes_now": False,
                "executes_now": False,
                "route": "runtime.chaser.board.build_terminal_write_approval_request(write_request=False)",
            },
            {
                "intent": "terminal.approval_request_write",
                "writes_now": True,
                "executes_now": False,
                "route": "runtime.chaser.board.build_terminal_write_approval_request(write_request=True)",
            },
            {
                "intent": "terminal.executor_readiness",
                "writes_now": False,
                "executes_now": False,
                "route": "runtime.chaser.terminal_write_executor_readiness",
            },
            {
                "intent": "terminal.execute_approval",
                "writes_now": True,
                "executes_now": True,
                "route": "runtime.chaser.terminal_write_executor.execute_terminal_write_approval",
            },
        ],
        "authority": _authority_flags(),
        "studio_contract": {
            "contract_read_available": True,
            "studio_ingress_execution_api": False,
            "studio_terminal_execution_button": False,
        },
        "warnings": [
            "gateway_ingress_is_not_a_network_server",
            "session_ids_are_routing_selectors_not_auth_tokens",
            "terminal_output_and_gateway_payloads_are_tier4_untrusted",
            "no_agent_bus_writes_no_provider_calls_no_canonical_writeback",
        ],
    }


def _blocked(
    root: Path,
    *,
    request_id: str,
    session_id: str,
    intent: str,
    blockers: list[str],
    request_bytes: int = 0,
) -> dict[str, Any]:
    return {
        "ok": False,
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "status": "blocked",
        "vault_root": str(root),
        "request_id": request_id,
        "session_id": session_id,
        "intent": intent,
        "blockers": blockers,
        "request_bytes": request_bytes,
        "result": {},
        "authority": _authority_flags(),
        "terminal_output_trusted": False,
        "trust_tier": "Tier 4",
        "warnings": [
            "gateway_ingress_failed_closed",
            "no_agent_bus_writes_no_provider_calls_no_canonical_writeback",
        ],
    }


def _authorize(intent: str, auth: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if auth.get("mode") != "local_operator":
        blockers.append("auth_mode_not_local_operator")
    if auth.get("operator_confirmed") is not True:
        blockers.append("local_operator_confirmation_required")
    if intent == "terminal.approval_request_write" and auth.get("approval_queue_write_confirmed") is not True:
        blockers.append("approval_queue_write_confirmation_required")
    if intent == "terminal.execute_approval":
        if auth.get("operator_approved_terminal_write") is not True:
            blockers.append("operator_approved_terminal_write_confirmation_required")
        if payload.get("confirm_approved_terminal_write") is not True:
            blockers.append("payload_confirm_approved_terminal_write_required")
    return blockers


def handle_gateway_ingress(vault_root: str | Path, request: dict[str, Any]) -> dict[str, Any]:
    """Authorize and route one structured gateway request.

    The facade does not create a network listener, write Agent Bus tasks, call a
    provider, or mutate canonical truth. Mutating terminal intents delegate to
    the existing N6 approval/request/executor helpers.
    """

    root = Path(vault_root).resolve()
    if not isinstance(request, dict):
        return _blocked(root, request_id="", session_id="", intent="", blockers=["request_must_be_object"])

    try:
        request_bytes = len(json.dumps(request, default=str).encode("utf-8"))
    except TypeError:
        return _blocked(root, request_id="", session_id="", intent="", blockers=["request_not_json_serializable"])
    raw_intent = _normalise_intent(str(request.get("intent") or ""))
    request_id = str(request.get("request_id") or f"gateway-req-{_digest(request)[:16]}")
    session_id = str(request.get("session_id") or "")
    payload = request.get("payload") if isinstance(request.get("payload"), dict) else {}
    auth = request.get("auth") if isinstance(request.get("auth"), dict) else {}

    blockers: list[str] = []
    if request_bytes > MAX_REQUEST_BYTES:
        blockers.append("request_too_large")
    if not _safe_id(request_id):
        blockers.append("unsafe_request_id")
    if session_id and not _safe_id(session_id):
        blockers.append("unsafe_session_id")

    supported = {
        "gateway.contract",
        "board.state",
        "terminal.propose",
        "terminal.approval_request_preview",
        "terminal.approval_request_write",
        "terminal.executor_readiness",
        "terminal.execute_approval",
    }
    if raw_intent not in supported:
        blockers.append(f"unsupported_intent:{raw_intent or 'missing'}")
    blockers.extend(_authorize(raw_intent, auth, payload))
    if blockers:
        return _blocked(
            root,
            request_id=request_id,
            session_id=session_id,
            intent=raw_intent,
            blockers=blockers,
            request_bytes=request_bytes,
        )

    if raw_intent == "gateway.contract":
        result = build_gateway_ingress_contract(root)
    elif raw_intent == "board.state":
        from runtime.chaser.board import build_board_state

        result = build_board_state(
            root,
            limit=int(payload.get("limit") or 8),
            include_gateway=bool(payload.get("include_gateway", True)),
        )
    elif raw_intent == "terminal.propose":
        from runtime.chaser.board import build_action_proposal

        result = build_action_proposal(
            root,
            action_type="terminal_command",
            command=str(payload.get("command") or ""),
            cwd=payload.get("cwd"),
            card_id=str(payload.get("card_id") or ""),
            actor=str(payload.get("actor") or "gateway"),
        )
    elif raw_intent in {"terminal.approval_request_preview", "terminal.approval_request_write"}:
        from runtime.chaser.board import build_terminal_write_approval_request

        result = build_terminal_write_approval_request(
            root,
            command=str(payload.get("command") or ""),
            cwd=payload.get("cwd"),
            card_id=str(payload.get("card_id") or ""),
            actor=str(payload.get("actor") or "gateway"),
            expected_proposal_id=str(payload.get("expected_proposal_id") or ""),
            write_request=raw_intent == "terminal.approval_request_write",
        )
    elif raw_intent == "terminal.executor_readiness":
        from runtime.chaser.terminal_write_executor_readiness import build_terminal_write_executor_readiness

        result = build_terminal_write_executor_readiness(
            root,
            approval_id=str(payload.get("approval_id") or ""),
            expected_proposal_id=str(payload.get("expected_proposal_id") or ""),
        )
    else:
        from runtime.chaser.terminal_write_executor import execute_terminal_write_approval

        result = execute_terminal_write_approval(
            root,
            approval_id=str(payload.get("approval_id") or ""),
            expected_proposal_id=str(payload.get("expected_proposal_id") or ""),
            actor=str(payload.get("actor") or "gateway"),
            confirm_approved_terminal_write=payload.get("confirm_approved_terminal_write") is True,
            timeout_seconds=int(payload.get("timeout_seconds") or 15),
            max_output_chars=int(payload.get("max_output_chars") or 4000),
        )

    ok = bool(result.get("ok")) if isinstance(result, dict) else False
    return {
        "ok": ok,
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "status": "handled" if ok else "handled_blocked",
        "vault_root": str(root),
        "request_id": request_id,
        "session_id": session_id,
        "intent": raw_intent,
        "handled_at": _now_iso(),
        "request_bytes": request_bytes,
        "authn": {
            "mode": auth.get("mode"),
            "local_operator_confirmed": auth.get("operator_confirmed") is True,
            "session_id_is_not_auth": True,
        },
        "authz": {
            "passed": True,
            "approval_queue_write_confirmed": auth.get("approval_queue_write_confirmed") is True,
            "operator_approved_terminal_write": auth.get("operator_approved_terminal_write") is True,
        },
        "result": result,
        "authority": _authority_flags(result if isinstance(result, dict) else {}),
        "terminal_output_trusted": False,
        "trust_tier": "Tier 4",
        "warnings": [
            "gateway_payload_and_terminal_output_are_tier4_untrusted",
            "gateway_is_internal_facade_not_network_server",
            "no_studio_execution_no_agent_bus_write_no_provider_call_no_canonical_writeback",
        ],
    }
