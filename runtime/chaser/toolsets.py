"""
runtime.chaser.toolsets

Read-only toolset configuration views for ChaserAgent Phase A.
Toolsets here are capability descriptions, not executable tools.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from runtime.chaser.policies import build_no_authority_report


_TOOLSETS: dict[str, dict[str, Any]] = {
    "none": {
        "toolset_id": "none",
        "display_name": "No tools",
        "status": "available",
        "mode": "preview_only",
        "description": "Profile/board preview without tool routing.",
    },
    "terminal-preview": {
        "toolset_id": "terminal-preview",
        "display_name": "Terminal Preview",
        "status": "partial",
        "mode": "policy_preview_only",
        "description": "TerminalAdapter policy preview and historical run references only.",
    },
    "gateway-diagnostic": {
        "toolset_id": "gateway-diagnostic",
        "display_name": "Gateway Diagnostic",
        "status": "partial",
        "mode": "read_only_diagnostic",
        "description": "Read-only Chaser Gateway Diagnostic status surfaces.",
    },
    "artifact-preview": {
        "toolset_id": "artifact-preview",
        "display_name": "Artifact Preview",
        "status": "planned",
        "mode": "manifest_preview_only",
        "description": "Artifact manifest/provenance preview only.",
    },
    "web-preview": {
        "toolset_id": "web-preview",
        "display_name": "Web Preview",
        "status": "planned",
        "mode": "no_network_preview_only",
        "description": "Web/search intent description only; no network call.",
    },
    "repo-preview": {
        "toolset_id": "repo-preview",
        "display_name": "Repo Preview",
        "status": "planned",
        "mode": "proposal_only",
        "description": "Patch/review proposal routing only.",
    },
    "session-preview": {
        "toolset_id": "session-preview",
        "display_name": "Session Preview",
        "status": "partial",
        "mode": "read_only_session_store",
        "description": "Read-only Chaser session metadata and export references.",
    },
}


def list_toolsets() -> list[dict[str, Any]]:
    return [get_toolset(toolset_id) for toolset_id in sorted(_TOOLSETS)]


def get_toolset(toolset_id: str = "none") -> dict[str, Any]:
    key = str(toolset_id or "none").strip().lower()
    item = deepcopy(_TOOLSETS.get(key) or _TOOLSETS["none"])
    item.update(
        {
            "authority": build_no_authority_report(),
            "executes_now": False,
            "writes_now": False,
            "requires_approval_for_future_execution": key != "none",
        }
    )
    return item


def validate_toolset_view(toolset: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(toolset, dict):
        return {"ok": False, "errors": ["toolset_not_object"]}
    if not toolset.get("toolset_id"):
        errors.append("missing_toolset_id")
    if toolset.get("executes_now") is not False:
        errors.append("toolset_must_not_execute_now")
    if toolset.get("writes_now") is not False:
        errors.append("toolset_must_not_write_now")
    if any(bool(value) for value in (toolset.get("authority") or {}).values()):
        errors.append("toolset_authority_flags_must_be_false")
    return {"ok": not errors, "errors": errors}
