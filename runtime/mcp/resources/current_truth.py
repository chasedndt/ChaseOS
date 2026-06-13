"""chaseos.current_truth resource handler.

Field-to-source mapping frozen against ChaseOS-MCP-Data-Contracts.md v1.0.
Missing required source files produce a clean system_error per frozen contract.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.mcp.config import MCPConfig
from runtime.mcp.errors import input_error, system_error
from runtime.mcp.types import HandlerResult, PermissionEnvelope


DEFAULT_CURRENT_TRUTH_FIELDS = ["sprint_focus", "current_phase", "active_domains"]
CURRENT_TRUTH_ALLOWED_FIELDS = DEFAULT_CURRENT_TRUTH_FIELDS + ["open_loops", "recent_decisions"]

# Fixed source mapping — not client-controllable.
_NOW_MD_FIELDS = {"sprint_focus", "current_phase", "active_domains"}
_DECISION_LEDGER_FIELDS = {"recent_decisions"}
_PROJECT_OS_FIELDS = {"open_loops"}


def read_text(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def section_after_heading(text: str, heading: str) -> str:
    lines = text.splitlines()
    capture = False
    captured: list[str] = []
    needle = heading.lower()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            normalized = stripped.lstrip("#").strip().lower()
            if capture and normalized != needle:
                break
            capture = normalized == needle
            continue
        if capture and stripped:
            captured.append(stripped)
    return "\n".join(captured)


def first_bullet(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            return stripped[2:].strip()
    return None


def parse_active_domains(now_text: str) -> list[str]:
    domains: list[str] = []
    active_now = section_after_heading(now_text, "Active Now")
    for line in active_now.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "---" in stripped or "Domain" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and cells[0]:
            domains.append(cells[0])
    return domains[:8]


def parse_open_loops(vault_root: Path) -> list[str]:
    paths = [
        vault_root / "01_PROJECTS" / "ChaseOS" / "ChaseOS-OS.md",
        vault_root / "00_HOME" / "Now.md",
    ]
    loops: list[str] = []
    for path in paths:
        text = read_text(path)
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("- [ ]"):
                loops.append(stripped[5:].strip())
            elif stripped.startswith("- TODO"):
                loops.append(stripped[2:].strip())
        if loops:
            return loops[:10]
    return loops


def parse_recent_decisions(vault_root: Path) -> list[str]:
    text = read_text(vault_root / "07_LOGS" / "Decision-Ledger" / "Index.md")
    decisions: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("|"):
            decisions.append(stripped)
        if len(decisions) >= 10:
            break
    return decisions


def chaseos_current_truth(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    requested = params.get("fields")
    if requested is None:
        fields = list(DEFAULT_CURRENT_TRUTH_FIELDS)
    elif isinstance(requested, list):
        fields = list(requested)
    else:
        return HandlerResult(
            False,
            error=input_error("invalid_field_value", "fields must be a list of field names"),
        )
    if not all(isinstance(f, str) and f in CURRENT_TRUTH_ALLOWED_FIELDS for f in fields):
        return HandlerResult(
            False,
            error=input_error("invalid_field_value", "fields contains an unsupported field name", fields=fields),
        )

    now_path = config.vault_root / "00_HOME" / "Now.md"
    now_fields_requested = any(f in _NOW_MD_FIELDS for f in fields)

    # Fail cleanly if Now.md is missing and fields that depend on it are requested.
    if now_fields_requested and (not now_path.exists() or not now_path.is_file()):
        return HandlerResult(
            False,
            error=system_error(
                "source_file_read_error",
                "Required source file is missing: 00_HOME/Now.md",
                source="00_HOME/Now.md",
            ),
        )

    now_text = read_text(now_path) if now_fields_requested else ""
    files_read: list[str] = []
    if now_fields_requested and now_path.exists():
        files_read.append("00_HOME/Now.md")

    data: dict[str, Any] = {}
    if "sprint_focus" in fields:
        active_now = section_after_heading(now_text, "Active Now")
        data["sprint_focus"] = first_bullet(active_now) or first_bullet(now_text)
    if "current_phase" in fields:
        data["current_phase"] = section_after_heading(now_text, "Current Phase") or None
    if "active_domains" in fields:
        data["active_domains"] = parse_active_domains(now_text)
    if "open_loops" in fields:
        data["open_loops"] = parse_open_loops(config.vault_root)
    if "recent_decisions" in fields:
        decision_path = config.vault_root / "07_LOGS" / "Decision-Ledger" / "Index.md"
        if decision_path.exists():
            files_read.append("07_LOGS/Decision-Ledger/Index.md")
        data["recent_decisions"] = parse_recent_decisions(config.vault_root)

    return HandlerResult(
        True,
        data,
        files_read=files_read,
        audit_metadata={"resource": "chaseos.current_truth", "fields": fields},
    )
