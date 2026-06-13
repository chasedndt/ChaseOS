"""runtime.capabilities resource handler."""

from __future__ import annotations

from typing import Any

from runtime.mcp.config import MCPConfig
from runtime.mcp.safety import DEFERRED_SURFACES, EXCLUDED_SURFACES, V2_WORKFLOW_TOOLS
from runtime.mcp.types import HandlerResult, PermissionEnvelope


def runtime_capabilities(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    payload = {
        "resources": envelope.resources,
        "tools": envelope.tools,
        "prompts": envelope.prompts,
        "v2_tools": V2_WORKFLOW_TOOLS,
        "deferred": DEFERRED_SURFACES,
        "excluded": EXCLUDED_SURFACES,
        "modes": config.allowed_modes,
    }
    return HandlerResult(True, payload, audit_metadata={"resource": "runtime.capabilities"})
