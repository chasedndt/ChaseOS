"""Static handoff.runtime_draft_frame prompt."""

from __future__ import annotations

from typing import Any

from runtime.mcp.config import MCPConfig
from runtime.mcp.types import HandlerResult, PermissionEnvelope


HANDOFF_RUNTIME_DRAFT_FRAME = """# Runtime Handoff Draft Frame

Use this template to draft a handoff for human review.

Sections:
- Current state
- Active constraints
- Proposed next action
- Open questions
- Handoff notes

This V1 prompt is static and template-only. It performs no vault reads, no hidden context loading, and no live handoff assembly.
"""


def handoff_runtime_draft_frame(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    return HandlerResult(
        True,
        {
            "prompt_name": "handoff.runtime_draft_frame",
            "template": HANDOFF_RUNTIME_DRAFT_FRAME,
            "context_loaded": False,
        },
        audit_metadata={"prompt": "handoff.runtime_draft_frame", "static": True},
    )
