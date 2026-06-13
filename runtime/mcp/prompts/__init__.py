"""Prompt handler registry for Runtime MCP V1."""

from runtime.mcp.prompts.handoff_frame import handoff_runtime_draft_frame
from runtime.mcp.prompts.chaseos_prompts import make_prompt_handler


PROMPT_HANDLERS = {
    "handoff.runtime_draft_frame": handoff_runtime_draft_frame,
    "chaseos.operator_today_prompt": make_prompt_handler("chaseos.operator_today_prompt"),
    "chaseos.research_ingest_prompt": make_prompt_handler("chaseos.research_ingest_prompt"),
    "chaseos.adapter_handoff_prompt": make_prompt_handler("chaseos.adapter_handoff_prompt"),
    "chaseos.risk_review_prompt": make_prompt_handler("chaseos.risk_review_prompt"),
}

__all__ = ["PROMPT_HANDLERS"]
