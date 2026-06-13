"""Error helpers and stable error codes for Runtime MCP."""

from __future__ import annotations

from typing import Any

from runtime.mcp.types import MCPError


def input_error(code: str, message: str, **details: Any) -> MCPError:
    return MCPError(code=code, message=message, category="input_error", details=details)


def domain_error(code: str, message: str, **details: Any) -> MCPError:
    return MCPError(code=code, message=message, category="domain_error", details=details)


def system_error(code: str, message: str, **details: Any) -> MCPError:
    return MCPError(code=code, message=message, category="system_error", details=details)


ERR_BAD_JSON = "bad_json"
ERR_BAD_REQUEST = "bad_request"
ERR_CONFIG_INVALID = "config_invalid"
ERR_MODE_DENIED = "mode_denied"
ERR_SURFACE_UNAVAILABLE = "surface_unavailable"
ERR_UNKNOWN_SURFACE = "unknown_surface"
ERR_PROPOSAL_NOT_FOUND = "proposal_not_found"
ERR_PROTECTED_FILE = "protected_file_violation"
ERR_PATH_DENIED = "path_denied"
ERR_WRITE_FAILED = "artifact_write_failed"
ERR_AUDIT_FAILED = "audit_write_failed"
ERR_AOR_INVOCATION_FAILED = "aor_invocation_failed"
ERR_GATE_POLICY_DENIED = "gate_policy_denied"
ERR_WORKFLOW_INPUTS_INVALID = "workflow_inputs_invalid"
ERR_WORKFLOW_INVOCATION_AUDIT_FAILED = "workflow_invocation_audit_failed"
ERR_WORKFLOW_MANIFEST_NOT_FOUND = "workflow_manifest_not_found"
ERR_WORKFLOW_NOT_ACTIVE = "workflow_not_active"
ERR_WORKFLOW_NOT_ALLOWED = "workflow_not_allowed"
ERR_WORKFLOW_OUTPUT_ALREADY_EXISTS = "workflow_output_already_exists"
ERR_WORKFLOW_PERMISSION_CEILING_EXCEEDED = "workflow_permission_ceiling_exceeded"
ERR_WORKFLOW_WRITEBACK_SCOPE_DENIED = "workflow_writeback_scope_denied"
ERR_ROLE_CARD_NOT_FOUND = "role_card_not_found"


class MCPSystemError(RuntimeError):
    """Raised by subsystems (staging store, etc.) on unrecoverable write failures."""
