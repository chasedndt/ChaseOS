"""operator.briefing.latest resource handler."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.mcp.config import MCPConfig
from runtime.mcp.resources.current_truth import read_text
from runtime.mcp.types import HandlerResult, PermissionEnvelope


def latest_markdown_summary(directory: Path) -> dict[str, Any] | None:
    if not directory.exists():
        return None
    files = sorted(
        [path for path in directory.iterdir() if path.suffix.lower() == ".md"],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not files:
        return None
    path = files[0]
    text = read_text(path)
    title = None
    for line in text.splitlines():
        if line.startswith("#"):
            title = line.lstrip("#").strip()
            break
    return {
        "path": str(path.relative_to(directory.parents[1])),
        "title": title,
        "preview": "\n".join(text.splitlines()[:12]),
    }


def operator_briefing_latest(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    latest = latest_markdown_summary(config.operator_briefs_dir)
    return HandlerResult(
        True,
        {"latest": latest},
        audit_metadata={"resource": "operator.briefing.latest", "found": latest is not None},
    )
