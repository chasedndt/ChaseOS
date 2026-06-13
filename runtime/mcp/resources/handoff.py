"""runtime.handoff.current resource handler."""

from __future__ import annotations

from typing import Any

from runtime.mcp.config import MCPConfig
from runtime.mcp.resources.briefing import latest_markdown_summary
from runtime.mcp.resources.current_truth import DEFAULT_CURRENT_TRUTH_FIELDS, chaseos_current_truth, parse_open_loops
from runtime.mcp.types import HandlerResult, PermissionEnvelope


def runtime_handoff_current(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    truth_result = chaseos_current_truth(
        {"fields": DEFAULT_CURRENT_TRUTH_FIELDS},
        config,
        envelope,
    )
    if not truth_result.ok:
        return HandlerResult(
            False,
            error=truth_result.error,
            files_read=list(truth_result.files_read),
            audit_metadata={"resource": "runtime.handoff.current", "source_error": "current_truth"},
        )
    payload = {
        "current_truth": truth_result.payload,
        "open_loops": parse_open_loops(config.vault_root),
        "latest_operator_brief": latest_markdown_summary(config.operator_briefs_dir),
    }
    return HandlerResult(
        True,
        payload,
        files_read=list(truth_result.files_read),
        audit_metadata={"resource": "runtime.handoff.current"},
    )
