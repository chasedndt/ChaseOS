"""ChaseOS-named safe resource aliases for Runtime MCP.

These handlers expose bounded, read-only summaries. They do not accept file
paths from callers and do not traverse outside fixed ChaseOS allowlist paths.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.mcp.config import MCPConfig
from runtime.mcp.types import HandlerResult, PermissionEnvelope


def _read(path: Path, limit: int = 5000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")[:limit]


def _headings(text: str, limit: int = 12) -> list[str]:
    out: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            out.append(stripped)
        if len(out) >= limit:
            break
    return out


def chaseos_current_state(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    rel = "00_HOME/Now.md"
    text = _read(config.vault_root / rel)
    return HandlerResult(
        True,
        {
            "resource": "chaseos.current_state",
            "source": rel,
            "available": bool(text),
            "headings": _headings(text),
            "excerpt": text[:1200],
            "canonical_writeback_allowed": False,
        },
        files_read=[rel] if text else [],
        audit_metadata={"resource": "chaseos.current_state"},
    )


def chaseos_project_summary(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    candidates = [
        "01_PROJECTS/ChaseOS/ChaseOS-OS.md",
        "PROJECT_FOUNDATION.md",
        "README.md",
    ]
    for rel in candidates:
        text = _read(config.vault_root / rel)
        if text:
            return HandlerResult(
                True,
                {
                    "resource": "chaseos.project_summary",
                    "source": rel,
                    "headings": _headings(text),
                    "excerpt": text[:1200],
                },
                files_read=[rel],
                audit_metadata={"resource": "chaseos.project_summary"},
            )
    return HandlerResult(True, {"resource": "chaseos.project_summary", "available": False})


def chaseos_operator_brief_latest(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    root = config.vault_root / "07_LOGS" / "Operator-Briefs"
    files = [p for p in root.glob("*.md") if p.is_file()] if root.exists() else []
    if not files:
        return HandlerResult(True, {"resource": "chaseos.operator_brief_latest", "available": False})
    latest = max(files, key=lambda p: p.stat().st_mtime)
    rel = latest.relative_to(config.vault_root).as_posix()
    text = _read(latest)
    return HandlerResult(
        True,
        {"resource": "chaseos.operator_brief_latest", "source": rel, "excerpt": text[:2000]},
        files_read=[rel],
        audit_metadata={"resource": "chaseos.operator_brief_latest"},
    )


def chaseos_sic_workspace_summary(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    rel = "runtime/source_intelligence/README.md"
    text = _read(config.vault_root / rel)
    workspace_root = config.vault_root / "runtime" / "source_intelligence" / "workspaces"
    count = len([p for p in workspace_root.iterdir() if p.is_dir()]) if workspace_root.exists() else 0
    return HandlerResult(
        True,
        {
            "resource": "chaseos.sic_workspace_summary",
            "readme_available": bool(text),
            "workspace_count": count,
            "headings": _headings(text),
        },
        files_read=[rel] if text else [],
        audit_metadata={"resource": "chaseos.sic_workspace_summary"},
    )


def chaseos_adapter_status(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    adapter_dir = config.vault_root / "runtime" / "policy" / "adapters"
    names = ["claude", "openai", "responses_api", "n8n", "hermes", "openclaw", "local_oss"]
    statuses: dict[str, str] = {}
    files_read: list[str] = []
    for name in names:
        path = adapter_dir / f"{name}.yaml"
        if not path.exists():
            statuses[name] = "missing"
            continue
        files_read.append(path.relative_to(config.vault_root).as_posix())
        status = "unknown"
        for line in _read(path, limit=3000).splitlines():
            if line.strip().startswith("status:"):
                status = line.split(":", 1)[1].strip().strip('"')
                break
        statuses[name] = status
    return HandlerResult(
        True,
        {"resource": "chaseos.adapter_status", "statuses": statuses},
        files_read=files_read,
        audit_metadata={"resource": "chaseos.adapter_status"},
    )


def chaseos_rnd_register_summary(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    files = ["06_AGENTS/Feature-Register.md", "06_AGENTS/Feature-Fit-Register.md"]
    matches: list[str] = []
    files_read: list[str] = []
    needles = ("OpenAI", "Responses", "MCP", "n8n", "Adapter")
    for rel in files:
        text = _read(config.vault_root / rel, limit=12000)
        if not text:
            continue
        files_read.append(rel)
        for line in text.splitlines():
            if any(needle in line for needle in needles):
                matches.append(line.strip())
            if len(matches) >= 30:
                break
    return HandlerResult(
        True,
        {"resource": "chaseos.rnd_register_summary", "matches": matches},
        files_read=files_read,
        audit_metadata={"resource": "chaseos.rnd_register_summary"},
    )

