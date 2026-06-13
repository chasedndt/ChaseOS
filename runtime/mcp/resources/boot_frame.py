"""context.boot_frame MCP resource handler.

Returns the ChaseOS pre-execution context bundle for any connecting runtime.
This is the resource that MCP-connected LLMs should fetch before invoking any
workflow or taking any vault action. It is also injected automatically into
workflow.invoke_bounded responses so the LLM always sees it at execution time.

Response fields:
    boot_status     "ok" | "degraded" | "failed"
    runtime_id      the runtime that requested the frame
    current_phase   from Now.md
    sprint_focus    first active priority from Now.md
    trust_ceiling   from adapter manifest
    approval_mode   from adapter manifest
    carry_forward   open loops from last operator_close_day
    frame           the rendered text block for prompt injection
    sources_read    list of files read during boot
    warnings        list of boot warnings (if any)
"""

from __future__ import annotations

from typing import Any

from runtime.context.boot import load_boot_context
from runtime.mcp.config import MCPConfig
from runtime.mcp.types import HandlerResult, PermissionEnvelope


def context_boot_frame(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    runtime_id = params.get("runtime_id") or envelope.runtime_id or "openclaw"
    if not isinstance(runtime_id, str):
        runtime_id = "openclaw"

    try:
        bundle = load_boot_context(vault_root=config.vault_root, runtime_id=runtime_id)
    except Exception as exc:  # noqa: BLE001
        return HandlerResult(
            False,
            data={
                "boot_status": "error",
                "error": str(exc),
                "frame": "## ChaseOS Context Boot\n- Boot status: ERROR\n- Context could not be loaded.",
            },
            audit_metadata={"resource": "context.boot_frame", "boot_status": "error"},
        )

    payload = bundle.to_dict()
    payload["frame"] = bundle.to_frame()

    return HandlerResult(
        True,
        payload,
        files_read=bundle.sources_read,
        audit_metadata={
            "resource": "context.boot_frame",
            "boot_status": bundle.boot_status,
            "runtime_id": runtime_id,
            "warnings_count": len(bundle.boot_warnings),
        },
    )
