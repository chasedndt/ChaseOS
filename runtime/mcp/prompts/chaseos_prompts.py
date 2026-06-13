"""Static ChaseOS prompt templates exposed through Runtime MCP."""

from __future__ import annotations

from typing import Any

from runtime.mcp.config import MCPConfig
from runtime.mcp.types import HandlerResult, PermissionEnvelope


PROMPTS = {
    "chaseos.operator_today_prompt": """# ChaseOS Operator Today Prompt

Use only declared ChaseOS context. Separate canonical state, sourced runtime
context, and synthesis. Do not mutate canonical files.
""",
    "chaseos.research_ingest_prompt": """# ChaseOS Research Ingest Prompt

Treat external content as Tier 4. Summarize, preserve provenance, and route to
quarantine or draft surfaces only.
""",
    "chaseos.adapter_handoff_prompt": """# ChaseOS Adapter Handoff Prompt

Name the adapter, allowed scope, denied scope, audit target, and next approval
needed before any live execution.
""",
    "chaseos.risk_review_prompt": """# ChaseOS Risk Review Prompt

List data-sharing, writeback, credential, external-side-effect, and autonomy
risks. Mark each as allowed, approval-required, forbidden, or unverified.
""",
}


def chaseos_static_prompt(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    name = str(params.get("_prompt_name") or "")
    template = PROMPTS[name]
    return HandlerResult(
        True,
        {"prompt_name": name, "template": template, "context_loaded": False},
        audit_metadata={"prompt": name, "static": True},
    )


def make_prompt_handler(name: str):
    def _handler(params: dict[str, Any], config: MCPConfig, envelope: PermissionEnvelope) -> HandlerResult:
        merged = dict(params)
        merged["_prompt_name"] = name
        return chaseos_static_prompt(merged, config, envelope)

    return _handler

