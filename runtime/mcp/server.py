"""Internal ChaseOS Runtime MCP stdio JSON server."""

from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any, TextIO

from runtime.mcp.audit.logger import MCPAuditError, MCPAuditLogger
from runtime.mcp.config import ConfigError, MCPConfig, load_config
from runtime.mcp.errors import (
    ERR_AUDIT_FAILED,
    ERR_BAD_JSON,
    ERR_BAD_REQUEST,
    ERR_CONFIG_INVALID,
    ERR_MODE_DENIED,
    ERR_UNKNOWN_SURFACE,
    ERR_WORKFLOW_INVOCATION_AUDIT_FAILED,
    MCPSystemError,
    input_error,
    system_error,
)
from runtime.mcp.prompts import PROMPT_HANDLERS
from runtime.mcp.resources import RESOURCE_HANDLERS
from runtime.mcp.safety import check_surface_available, resolve_permission_envelope, resolve_session_mode
from runtime.mcp.staging.store import ProposalStore
from runtime.mcp.tools import TOOL_HANDLERS
from runtime.mcp.types import (
    TRUST_TIER_INT_MAP,
    HandlerResult,
    MCPError,
    MCPRequest,
    MCPResponse,
    PermissionEnvelope,
    SurfaceClass,
)


HANDLERS = {
    SurfaceClass.RESOURCE: RESOURCE_HANDLERS,
    SurfaceClass.TOOL: TOOL_HANDLERS,
    SurfaceClass.PROMPT: PROMPT_HANDLERS,
}

MCP_PROTOCOL_VERSION = "2025-11-25"
JSONRPC_VERSION = "2.0"

JSONRPC_PARSE_ERROR = -32700
JSONRPC_INVALID_REQUEST = -32600
JSONRPC_METHOD_NOT_FOUND = -32601
JSONRPC_INVALID_PARAMS = -32602
JSONRPC_INTERNAL_ERROR = -32603

MCP_JSONRPC_RESOURCES = [
    "chaseos.current_state",
    "chaseos.project_summary",
    "chaseos.operator_brief_latest",
    "chaseos.sic_workspace_summary",
    "chaseos.adapter_status",
    "chaseos.rnd_register_summary",
    "chaseos.runtime_surfaces_summary",
]

MCP_JSONRPC_TOOLS = [
    "chaseos.generate_operator_brief_draft",
    "chaseos.create_research_digest_draft",
    "chaseos.prepare_discord_alert_draft",
    "chaseos.query_sic_evidence",
    "chaseos.validate_writeback_target",
]

MCP_JSONRPC_PROMPTS = [
    "chaseos.operator_today_prompt",
    "chaseos.research_ingest_prompt",
    "chaseos.adapter_handoff_prompt",
    "chaseos.risk_review_prompt",
]

MCP_SURFACE_DESCRIPTIONS = {
    "chaseos.current_state": "Read-only summary of the current ChaseOS Now state.",
    "chaseos.project_summary": "Read-only project summary from declared ChaseOS project truth.",
    "chaseos.operator_brief_latest": "Read-only latest operator brief summary when available.",
    "chaseos.sic_workspace_summary": "Read-only Source Intelligence workspace summary.",
    "chaseos.adapter_status": "Read-only adapter status summary from policy files.",
    "chaseos.rnd_register_summary": "Read-only feature/R&D register summary when available.",
    "chaseos.runtime_surfaces_summary": "Curated read-only Adaptive Runtime Surface Layer summary; no raw manifests or execution.",
    "runtime.surfaces": "Curated read-only Adaptive Runtime Surface Layer summary; no raw manifests or execution.",
    "chaseos.generate_operator_brief_draft": "Write a bounded operator brief draft only.",
    "chaseos.create_research_digest_draft": "Write a bounded research digest draft only.",
    "chaseos.prepare_discord_alert_draft": "Write a bounded Discord alert draft only.",
    "chaseos.query_sic_evidence": "Query bounded SIC evidence summaries.",
    "chaseos.validate_writeback_target": "Validate whether a target is inside the draft/audit allowlist.",
    "chaseos.operator_today_prompt": "Prompt pattern for bounded operator-today synthesis.",
    "chaseos.research_ingest_prompt": "Prompt pattern for untrusted research ingest.",
    "chaseos.adapter_handoff_prompt": "Prompt pattern for adapter handoff review.",
    "chaseos.risk_review_prompt": "Prompt pattern for adapter and workflow risk review.",
}


def _vault_root_from_env() -> Path | None:
    value = os.environ.get("CHASEOS_MCP_VAULT_ROOT")
    if not value:
        return None
    return Path(value)


def _request_id(payload: dict[str, Any] | None = None) -> str:
    if payload and isinstance(payload.get("request_id"), str) and payload["request_id"]:
        return payload["request_id"]
    return f"req-{uuid.uuid4().hex}"


def _parse_request(payload: dict[str, Any]) -> MCPRequest:
    surface_class: SurfaceClass | None = None
    surface_name: str | None = None
    if isinstance(payload.get("resource"), str):
        surface_class = SurfaceClass.RESOURCE
        surface_name = payload["resource"]
    elif isinstance(payload.get("tool"), str):
        surface_class = SurfaceClass.TOOL
        surface_name = payload["tool"]
    elif isinstance(payload.get("prompt"), str):
        surface_class = SurfaceClass.PROMPT
        surface_name = payload["prompt"]
    elif isinstance(payload.get("method"), str) and isinstance(payload.get("name"), str):
        try:
            surface_class = SurfaceClass(payload["method"])
        except ValueError as exc:
            raise ValueError("method must be resource, tool, or prompt") from exc
        surface_name = payload["name"]

    if surface_class is None or not surface_name:
        raise ValueError("request must name exactly one resource, tool, or prompt")
    params = payload.get("params") or {}
    if not isinstance(params, dict):
        raise ValueError("params must be a mapping when provided")
    runtime_id = payload.get("runtime_id") or "_unregistered"
    if not isinstance(runtime_id, str):
        raise ValueError("runtime_id must be a string")
    mode = payload.get("mode")
    if mode is not None and not isinstance(mode, str):
        raise ValueError("mode must be a string when provided")
    return MCPRequest(
        request_id=_request_id(payload),
        surface_class=surface_class,
        surface_name=surface_name,
        params=params,
        runtime_id=runtime_id,
        requested_mode=mode,
    )


def _error_response(request_id: str, error: MCPError) -> dict[str, Any]:
    return MCPResponse(request_id=request_id, ok=False, error=error).to_dict()


def _write_audit(
    request: MCPRequest,
    envelope: PermissionEnvelope,
    mode: str,
    result: HandlerResult,
    logger: MCPAuditLogger,
) -> None:
    """Call logger.log() with all required fields extracted from request/envelope/result."""
    outcome = "success" if result.ok else "error"
    outcome_detail = result.error.message if result.error else None
    if request.surface_name == "workflow.invoke_bounded" and result.audit_metadata:
        outcome_detail = json.dumps(result.audit_metadata, sort_keys=True, default=str)
    error_code = result.error.code if result.error else None
    error_message = result.error.message if result.error else None
    trust_tier_int = TRUST_TIER_INT_MAP.get(envelope.trust_tier, 3)
    logger.log(
        request_id=request.request_id,
        surface_id=request.surface_name,
        surface_class=request.surface_class.value,
        runtime_id=envelope.runtime_id,
        trust_tier=trust_tier_int,
        safety_mode=mode,
        outcome=outcome,
        outcome_detail=outcome_detail,
        files_read=list(result.files_read),
        files_written=list(result.files_written),
        error_code=error_code,
        error_message=error_message,
    )


def _handle_audit(
    request: MCPRequest,
    envelope: PermissionEnvelope,
    mode: str,
    result: HandlerResult,
    logger: MCPAuditLogger,
    config: MCPConfig,
) -> HandlerResult:
    """Write audit, applying each surface's fail-open/fail-closed policy."""
    try:
        _write_audit(request, envelope, mode, result, logger)
        return result
    except MCPAuditError as exc:
        if (
            request.surface_name == "workflow.invoke_bounded"
            and result.audit_metadata.get("aor_invoked") is True
        ):
            return HandlerResult(
                False,
                error=system_error(
                    ERR_WORKFLOW_INVOCATION_AUDIT_FAILED,
                    str(exc),
                    workflow_id=result.audit_metadata.get("workflow_id"),
                    aor_audit_id=result.audit_metadata.get("aor_audit_id"),
                    aor_status=result.audit_metadata.get("aor_status"),
                ),
                audit_metadata={
                    "audit_write": "failed",
                    "aor_invoked": True,
                    "workflow_id": result.audit_metadata.get("workflow_id"),
                    "aor_audit_id": result.audit_metadata.get("aor_audit_id"),
                },
            )
        if request.surface_name == "proposal.submit":
            # Fail-closed: rollback staging, return audit_required error.
            rollback_failed = False
            if result.rollback_proposal_id:
                try:
                    ProposalStore(config.staging_dir).rollback(result.rollback_proposal_id)
                except MCPSystemError:
                    rollback_failed = True
            err_code = "audit_and_rollback_failed" if rollback_failed else ERR_AUDIT_FAILED
            return HandlerResult(
                False,
                error=system_error(err_code, str(exc)),
                audit_metadata={
                    "audit_write": "failed",
                    "rolled_back_proposal_id": result.rollback_proposal_id,
                },
            )
        # Fail-open for all other surfaces: return result, audit failure is non-blocking.
        return result


def handle_request(
    payload: dict[str, Any],
    *,
    vault_root: Path | None = None,
    config: MCPConfig | None = None,
    logger: MCPAuditLogger | None = None,
) -> dict[str, Any]:
    request_id = _request_id(payload)
    try:
        cfg = config or load_config(vault_root=vault_root)
    except ConfigError as exc:
        return _error_response(request_id, system_error(ERR_CONFIG_INVALID, str(exc)))

    try:
        request = _parse_request(payload)
    except ValueError as exc:
        return _error_response(request_id, input_error(ERR_BAD_REQUEST, str(exc)))

    try:
        mode = resolve_session_mode(request.runtime_id, request.requested_mode, cfg)
    except PermissionError as exc:
        # Mode denial: audit with _unregistered envelope (best-effort, fail-open).
        unregistered_env = resolve_permission_envelope(request.runtime_id, cfg.default_mode, cfg)
        err_result = HandlerResult(False, error=input_error(ERR_MODE_DENIED, str(exc)))
        audit_logger = logger or MCPAuditLogger(cfg.audit_dir)
        try:
            _write_audit(request, unregistered_env, cfg.default_mode, err_result, audit_logger)
        except MCPAuditError:
            pass
        return MCPResponse(request_id=request.request_id, ok=False, error=err_result.error).to_dict()

    envelope = resolve_permission_envelope(request.runtime_id, mode, cfg)
    surface_error = check_surface_available(request, envelope)
    handlers = HANDLERS[request.surface_class]

    if surface_error or request.surface_name not in handlers:
        result = HandlerResult(
            False,
            error=surface_error or input_error(
                ERR_UNKNOWN_SURFACE,
                "Unknown Runtime MCP V1 surface.",
                surface_name=request.surface_name,
                surface_class=request.surface_class.value,
            ),
        )
        audit_logger = logger or MCPAuditLogger(cfg.audit_dir)
        final_result = _handle_audit(request, envelope, mode, result, audit_logger, cfg)
        return MCPResponse(
            request_id=request.request_id,
            ok=False,
            error=final_result.error,
        ).to_dict()

    try:
        result = handlers[request.surface_name](request.params, cfg, envelope)
        if not isinstance(result, HandlerResult):
            result = HandlerResult(False, error=system_error("handler_contract_error", "Handler returned invalid result"))
        if not result.ok and result.error is None:
            result.error = input_error(ERR_BAD_REQUEST, "Handler rejected the request.")
    except Exception as exc:  # noqa: BLE001
        result = HandlerResult(False, error=system_error("handler_failed", str(exc)))

    audit_logger = logger or MCPAuditLogger(cfg.audit_dir)
    final_result = _handle_audit(request, envelope, mode, result, audit_logger, cfg)

    return MCPResponse(
        request_id=request.request_id,
        ok=final_result.ok,
        result=final_result.payload if final_result.ok else None,
        error=final_result.error if not final_result.ok else None,
    ).to_dict()


def _jsonrpc_response(message_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": JSONRPC_VERSION, "id": message_id, "result": result}


def _jsonrpc_error(
    message_id: Any,
    code: int,
    message: str,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data:
        error["data"] = data
    return {"jsonrpc": JSONRPC_VERSION, "id": message_id, "error": error}


def _jsonrpc_params(payload: dict[str, Any]) -> dict[str, Any]:
    params = payload.get("params") or {}
    if not isinstance(params, dict):
        raise ValueError("params must be an object when provided")
    return params


def _jsonrpc_context(params: dict[str, Any]) -> tuple[str, str | None]:
    context: dict[str, Any] = {}
    if isinstance(params.get("_chaseos"), dict):
        context = params["_chaseos"]
    elif isinstance(params.get("_meta"), dict):
        meta_context = params["_meta"].get("chaseos")
        if isinstance(meta_context, dict):
            context = meta_context

    runtime_id = context.get("runtime_id") or "_unregistered"
    if not isinstance(runtime_id, str):
        runtime_id = "_unregistered"
    mode = context.get("mode")
    if mode is not None and not isinstance(mode, str):
        mode = None
    return runtime_id, mode


def _jsonrpc_envelope(
    params: dict[str, Any],
    cfg: MCPConfig,
) -> tuple[PermissionEnvelope, str]:
    runtime_id, requested_mode = _jsonrpc_context(params)
    mode = resolve_session_mode(runtime_id, requested_mode, cfg)
    return resolve_permission_envelope(runtime_id, mode, cfg), mode


def _resource_uri(name: str) -> str:
    return f"chaseos://resource/{name}"


def _resource_name_from_uri(uri: str) -> str:
    prefix = "chaseos://resource/"
    if uri.startswith(prefix):
        return uri[len(prefix):]
    return uri


def _resource_descriptor(name: str) -> dict[str, Any]:
    return {
        "uri": _resource_uri(name),
        "name": name,
        "title": name,
        "description": MCP_SURFACE_DESCRIPTIONS.get(name, ""),
        "mimeType": "application/json",
    }


def _tool_descriptor(name: str) -> dict[str, Any]:
    return {
        "name": name,
        "title": name,
        "description": MCP_SURFACE_DESCRIPTIONS.get(name, ""),
        "inputSchema": {
            "type": "object",
            "additionalProperties": True,
        },
    }


def _prompt_descriptor(name: str) -> dict[str, Any]:
    return {
        "name": name,
        "title": name,
        "description": MCP_SURFACE_DESCRIPTIONS.get(name, ""),
    }


def _legacy_error_jsonrpc(message_id: Any, legacy_response: dict[str, Any]) -> dict[str, Any]:
    error = legacy_response.get("error")
    if isinstance(error, dict):
        message = str(error.get("message") or "ChaseOS Runtime MCP rejected the request.")
        category = error.get("category")
        code = JSONRPC_INVALID_PARAMS if category in {"input_error", "domain_error"} else JSONRPC_INTERNAL_ERROR
        return _jsonrpc_error(message_id, code, message, {"chaseos_error": error})
    return _jsonrpc_error(message_id, JSONRPC_INTERNAL_ERROR, "ChaseOS Runtime MCP request failed.")


def _json_text(payload: dict[str, Any] | None) -> str:
    return json.dumps(payload or {}, sort_keys=True, default=str)


def _handle_jsonrpc_request(
    payload: dict[str, Any],
    *,
    vault_root: Path | None = None,
    config: MCPConfig | None = None,
    logger: MCPAuditLogger | None = None,
) -> dict[str, Any]:
    message_id = payload.get("id")
    method = payload.get("method")
    if not isinstance(method, str):
        return _jsonrpc_error(message_id, JSONRPC_INVALID_REQUEST, "method must be a string")

    try:
        params = _jsonrpc_params(payload)
    except ValueError as exc:
        return _jsonrpc_error(message_id, JSONRPC_INVALID_PARAMS, str(exc))

    try:
        cfg = config or load_config(vault_root=vault_root)
    except ConfigError as exc:
        return _jsonrpc_error(message_id, JSONRPC_INTERNAL_ERROR, "Runtime MCP config is invalid", {"detail": str(exc)})

    if method == "initialize":
        return _jsonrpc_response(
            message_id,
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {
                    "resources": {},
                    "tools": {},
                    "prompts": {},
                },
                "serverInfo": {
                    "name": cfg.server_identity,
                    "version": cfg.version,
                },
                "instructions": (
                    "ChaseOS Runtime MCP exposes bounded resources, tools, and prompts. "
                    "Canonical writeback, shell access, secret reads, and live external side effects are not available."
                ),
            },
        )

    if method == "ping":
        return _jsonrpc_response(message_id, {})

    try:
        envelope, mode = _jsonrpc_envelope(params, cfg)
    except PermissionError as exc:
        return _jsonrpc_error(message_id, JSONRPC_INVALID_PARAMS, str(exc))

    if method == "resources/list":
        resources = [
            _resource_descriptor(name)
            for name in MCP_JSONRPC_RESOURCES
            if name in envelope.resources and name in RESOURCE_HANDLERS
        ]
        return _jsonrpc_response(message_id, {"resources": resources})

    if method == "resources/templates/list":
        return _jsonrpc_response(message_id, {"resourceTemplates": []})

    if method == "resources/read":
        uri = params.get("uri")
        if not isinstance(uri, str) or not uri:
            return _jsonrpc_error(message_id, JSONRPC_INVALID_PARAMS, "resources/read requires a string uri")
        name = _resource_name_from_uri(uri)
        if name not in MCP_JSONRPC_RESOURCES:
            return _jsonrpc_error(
                message_id,
                JSONRPC_INVALID_PARAMS,
                "Resource is not exposed through the ChaseOS JSON-RPC MCP surface.",
                {"resource": name},
            )
        legacy = handle_request(
            {"resource": name, "runtime_id": envelope.runtime_id, "mode": mode, "params": {}},
            vault_root=vault_root,
            config=cfg,
            logger=logger,
        )
        if not legacy.get("ok"):
            return _legacy_error_jsonrpc(message_id, legacy)
        return _jsonrpc_response(
            message_id,
            {
                "contents": [
                    {
                        "uri": _resource_uri(name),
                        "mimeType": "application/json",
                        "text": _json_text(legacy.get("result")),
                    }
                ]
            },
        )

    if method == "tools/list":
        tools = [
            _tool_descriptor(name)
            for name in MCP_JSONRPC_TOOLS
            if name in envelope.tools and name in TOOL_HANDLERS
        ]
        return _jsonrpc_response(message_id, {"tools": tools})

    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if not isinstance(name, str) or not name:
            return _jsonrpc_error(message_id, JSONRPC_INVALID_PARAMS, "tools/call requires a string name")
        if not isinstance(arguments, dict):
            return _jsonrpc_error(message_id, JSONRPC_INVALID_PARAMS, "tools/call arguments must be an object")
        if name not in MCP_JSONRPC_TOOLS:
            return _jsonrpc_error(
                message_id,
                JSONRPC_INVALID_PARAMS,
                "Tool is not exposed through the ChaseOS JSON-RPC MCP surface.",
                {"tool": name},
            )
        legacy = handle_request(
            {"tool": name, "runtime_id": envelope.runtime_id, "mode": mode, "params": arguments},
            vault_root=vault_root,
            config=cfg,
            logger=logger,
        )
        if not legacy.get("ok"):
            return _legacy_error_jsonrpc(message_id, legacy)
        result = legacy.get("result") or {}
        return _jsonrpc_response(
            message_id,
            {
                "content": [{"type": "text", "text": _json_text(result)}],
                "structuredContent": result,
                "isError": False,
            },
        )

    if method == "prompts/list":
        prompts = [
            _prompt_descriptor(name)
            for name in MCP_JSONRPC_PROMPTS
            if name in envelope.prompts and name in PROMPT_HANDLERS
        ]
        return _jsonrpc_response(message_id, {"prompts": prompts})

    if method == "prompts/get":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if not isinstance(name, str) or not name:
            return _jsonrpc_error(message_id, JSONRPC_INVALID_PARAMS, "prompts/get requires a string name")
        if not isinstance(arguments, dict):
            return _jsonrpc_error(message_id, JSONRPC_INVALID_PARAMS, "prompts/get arguments must be an object")
        if name not in MCP_JSONRPC_PROMPTS:
            return _jsonrpc_error(
                message_id,
                JSONRPC_INVALID_PARAMS,
                "Prompt is not exposed through the ChaseOS JSON-RPC MCP surface.",
                {"prompt": name},
            )
        legacy = handle_request(
            {"prompt": name, "runtime_id": envelope.runtime_id, "mode": mode, "params": arguments},
            vault_root=vault_root,
            config=cfg,
            logger=logger,
        )
        if not legacy.get("ok"):
            return _legacy_error_jsonrpc(message_id, legacy)
        result = legacy.get("result") or {}
        text = str(result.get("template") or "")
        return _jsonrpc_response(
            message_id,
            {
                "description": MCP_SURFACE_DESCRIPTIONS.get(name, ""),
                "messages": [
                    {
                        "role": "user",
                        "content": {"type": "text", "text": text},
                    }
                ],
            },
        )

    return _jsonrpc_error(message_id, JSONRPC_METHOD_NOT_FOUND, f"Unknown MCP method: {method}")


def handle_jsonrpc_message(
    payload: dict[str, Any],
    *,
    vault_root: Path | None = None,
    config: MCPConfig | None = None,
    logger: MCPAuditLogger | None = None,
) -> dict[str, Any] | None:
    if payload.get("jsonrpc") != JSONRPC_VERSION:
        return _jsonrpc_error(payload.get("id"), JSONRPC_INVALID_REQUEST, "jsonrpc must be 2.0")
    if "id" not in payload:
        return None
    return _handle_jsonrpc_request(payload, vault_root=vault_root, config=config, logger=logger)


def handle_json_line(
    line: str,
    *,
    vault_root: Path | None = None,
    config: MCPConfig | None = None,
    logger: MCPAuditLogger | None = None,
) -> dict[str, Any] | None:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError as exc:
        return _error_response("unknown", input_error(ERR_BAD_JSON, str(exc)))
    if not isinstance(payload, dict):
        return _error_response("unknown", input_error(ERR_BAD_REQUEST, "request must be a JSON object"))
    if payload.get("jsonrpc") == JSONRPC_VERSION:
        return handle_jsonrpc_message(payload, vault_root=vault_root, config=config, logger=logger)
    return handle_request(payload, vault_root=vault_root, config=config, logger=logger)


def run_server(
    *,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    vault_root: Path | None = None,
) -> int:
    input_stream = stdin or sys.stdin
    output_stream = stdout or sys.stdout
    resolved_vault_root = vault_root or _vault_root_from_env()
    config: MCPConfig | None = None
    try:
        config = load_config(vault_root=resolved_vault_root)
    except ConfigError:
        config = None
    logger = MCPAuditLogger(config.audit_dir) if config else None
    for line in input_stream:
        if not line.strip():
            continue
        response = handle_json_line(line, vault_root=resolved_vault_root, config=config, logger=logger)
        if response is None:
            continue
        try:
            output_stream.write(json.dumps(response, sort_keys=True) + "\n")
            output_stream.flush()
        except Exception:  # noqa: BLE001
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(run_server())
