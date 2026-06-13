"""runtime.identity resource handler.

Response shape frozen against ChaseOS-MCP-Data-Contracts.md v1.0.
"""

from __future__ import annotations

from typing import Any

from runtime.mcp.config import MCPConfig
from runtime.mcp.types import HandlerResult, PermissionEnvelope


def runtime_identity(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    vault_root_confirmed = config.vault_root.exists() and config.vault_root.is_dir()
    payload = {
        "server_name": config.server_identity,
        "server_version": config.version,
        "chaseos_phase": "Phase 9",
        "vault_root_confirmed": vault_root_confirmed,
        "transport": config.transport,
        "active_safety_mode": envelope.mode,
        "runtime_id": envelope.runtime_id,
    }
    return HandlerResult(True, payload, audit_metadata={"resource": "runtime.identity"})
