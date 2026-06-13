"""Vault maintenance tool for standalone graph sweeps and file structure repair.

Response shape frozen against ChaseOS-MCP-Data-Contracts.md v1.0.
"""

from __future__ import annotations

import uuid
from typing import Any

from runtime.mcp.config import MCPConfig
from runtime.mcp.types import HandlerResult, PermissionEnvelope
from runtime.mcp.errors import system_error, input_error

import runtime.cli.vault_hygiene as hygiene_mod
import runtime.cli.daily_hub_linker as daily_hub_mod
import runtime.cli.provenance_linker as provenance_mod

def vault_maintain(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    """Execute the full 3-stage vault maintenance and graph integrity sweep."""
    
    dry_run = params.get("dry_run", False)
    if not isinstance(dry_run, bool):
         return HandlerResult(False, error=input_error("INVALID_INPUT", "dry_run must be a boolean"))

    # Stage 1: Hygiene run
    try:
        hygiene_mod.run(fix=not dry_run, delete_junk=not dry_run)
    except Exception as exc:
        return HandlerResult(
            False,
            error=system_error("MAINTENANCE_ERROR", f"Stage 1 (Vault Hygiene) failed: {exc}", stage=1)
        )

    # Stage 2: Daily Hub Linker
    try:
        daily_hub_mod.run(fix=not dry_run, update_index=not dry_run)
    except Exception as exc:
        return HandlerResult(
            False,
            error=system_error("MAINTENANCE_ERROR", f"Stage 2 (Daily Hub Linker) failed: {exc}", stage=2)
        )

    # Stage 3: Provenance Linker
    try:
        provenance_mod.run(fix=not dry_run)
    except Exception as exc:
        return HandlerResult(
            False,
            error=system_error("MAINTENANCE_ERROR", f"Stage 3 (Provenance Linker) failed: {exc}", stage=3)
        )

    status_message = "Vault graph integrity checked." if dry_run else "Vault graph integrity applied and verified."

    return HandlerResult(
        True,
        {
            "status": "complete",
            "dry_run": dry_run,
            "message": status_message,
        },
        audit_metadata={
            "tool": "vault.maintain",
            "dry_run": dry_run,
            "outcome": "success",
        },
    )
