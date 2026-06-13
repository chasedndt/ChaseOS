"""runtime.permission_envelope resource handler."""

from __future__ import annotations

from typing import Any

from runtime.mcp.config import MCPConfig
from runtime.mcp.types import HandlerResult, PermissionEnvelope


def runtime_permission_envelope(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    return HandlerResult(
        True,
        envelope.to_dict(),
        audit_metadata={"resource": "runtime.permission_envelope"},
    )
