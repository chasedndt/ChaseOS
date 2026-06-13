"""
runtime.operator_surface.terminal_runs

Terminal run-record persistence for the governed Terminal Workbench.

The terminal policy (`runtime/operator_surface/policies/terminal.yaml`) declares
that every terminal run is audited to `07_LOGS/Terminal-Runs/`. This module
implements that contract: it writes one JSON + one Markdown record per run and
provides read-only listing/loading.

Run records are Tier 4 untrusted evidence. They are NOT canonical vault truth
and must not be promoted without a separate review path. This module performs
no command execution and no redaction itself — the TerminalAdapter has already
redacted/truncated output before a record reaches here.

See:
  - 06_AGENTS/Terminal-Workbench-Architecture.md
  - runtime/operator_surface/adapters/terminal_adapter.py
"""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

TERMINAL_RUNS_REL = Path("07_LOGS") / "Terminal-Runs"
UNTRUSTED_TIER = "Tier 4"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def new_run_id(now: Optional[datetime] = None) -> str:
    stamp = (now or _now()).strftime("%Y%m%d%H%M%S")
    return f"term_{stamp}_{secrets.token_hex(3)}"


def runs_root(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve() / TERMINAL_RUNS_REL


def _safe_run_id(run_id: str) -> str:
    rid = (run_id or "").strip()
    if not rid:
        raise ValueError("run_id is empty")
    if any(ch in rid for ch in ("/", "\\", "..")) or Path(rid).name != rid:
        raise ValueError(f"unsafe run_id: {run_id!r}")
    return rid


def build_run_record(
    *,
    command: str,
    cwd: str,
    classification: dict,
    policy_decision: str,
    actor: str = "operator",
    exit_code: Optional[int] = None,
    stdout_excerpt: str = "",
    stderr_excerpt: str = "",
    duration_ms: int = 0,
    output_truncated: bool = False,
    redactions_applied: bool = False,
    approval_id: Optional[str] = None,
    run_id: Optional[str] = None,
    now: Optional[datetime] = None,
) -> dict:
    """Assemble a terminal run record (pure — no disk write)."""
    when = now or _now()
    return {
        "run_id": run_id or new_run_id(when),
        "timestamp": when.isoformat(),
        "actor": actor,
        "command": command,
        "cwd": cwd,
        "classification": classification.get("action_class", "unknown"),
        "policy_decision": policy_decision,
        "approval_id": approval_id,
        "allowed": bool(classification.get("allowed", False)),
        "approval_required": bool(classification.get("approval_required", False)),
        "exit_code": exit_code,
        "stdout_excerpt": stdout_excerpt,
        "stderr_excerpt": stderr_excerpt,
        "duration_ms": duration_ms,
        "redactions_applied": redactions_applied,
        "output_truncated": output_truncated,
        "trust_state": UNTRUSTED_TIER,
        "terminal_output_trusted": False,
    }


def _render_markdown(record: dict) -> str:
    lines = [
        f"# Terminal Run — {record['run_id']}",
        "",
        f"- timestamp: {record['timestamp']}",
        f"- actor: {record['actor']}",
        f"- classification: {record['classification']}",
        f"- policy_decision: {record['policy_decision']}",
        f"- exit_code: {record['exit_code']}",
        f"- duration_ms: {record['duration_ms']}",
        f"- output_truncated: {record['output_truncated']}",
        f"- redactions_applied: {record['redactions_applied']}",
        f"- trust_state: {record['trust_state']} (output is NOT trusted instruction)",
        "",
        "## Command",
        "",
        "```",
        record["command"],
        "```",
        "",
        f"cwd: `{record['cwd']}`",
        "",
        "## stdout (Tier 4 untrusted, redacted/truncated)",
        "",
        "```",
        record["stdout_excerpt"] or "(empty)",
        "```",
        "",
        "## stderr (Tier 4 untrusted, redacted/truncated)",
        "",
        "```",
        record["stderr_excerpt"] or "(empty)",
        "```",
        "",
    ]
    return "\n".join(lines)


def record_terminal_run(vault_root: str | Path, record: dict) -> dict:
    """Persist a run record to JSON + Markdown. Returns the audit paths.

    Fail-soft: if the Markdown render fails, the JSON record is still written.
    """
    when = datetime.fromisoformat(record["timestamp"])
    day_dir = runs_root(vault_root) / when.strftime("%Y-%m-%d")
    day_dir.mkdir(parents=True, exist_ok=True)
    run_id = record["run_id"]

    json_path = day_dir / f"{run_id}.json"
    record = dict(record)
    record["audit_paths"] = {
        "json": str(json_path),
        "markdown": str(day_dir / f"{run_id}.md"),
    }
    json_path.write_text(json.dumps(record, indent=2), encoding="utf-8")

    try:
        (day_dir / f"{run_id}.md").write_text(_render_markdown(record), encoding="utf-8")
    except Exception:
        record["audit_paths"]["markdown"] = None

    return record["audit_paths"]


def list_terminal_runs(vault_root: str | Path, limit: int = 20) -> list[dict]:
    """Return newest-first run summaries (fail-open)."""
    root = runs_root(vault_root)
    if not root.exists():
        return []
    records: list[tuple[float, dict]] = []
    for path in root.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        records.append((
            path.stat().st_mtime,
            {
                "run_id": data.get("run_id", path.stem),
                "timestamp": data.get("timestamp", ""),
                "actor": data.get("actor", ""),
                "command": data.get("command", ""),
                "cwd": data.get("cwd", ""),
                "classification": data.get("classification", ""),
                "policy_decision": data.get("policy_decision", ""),
                "allowed": data.get("allowed"),
                "approval_required": data.get("approval_required"),
                "exit_code": data.get("exit_code"),
                "duration_ms": data.get("duration_ms", 0),
                "redactions_applied": data.get("redactions_applied", False),
                "output_truncated": data.get("output_truncated", False),
                "trust_state": data.get("trust_state", UNTRUSTED_TIER),
                "terminal_output_trusted": data.get("terminal_output_trusted", False),
                "stdout_excerpt": data.get("stdout_excerpt", ""),
                "stderr_excerpt": data.get("stderr_excerpt", ""),
                "audit_paths": data.get("audit_paths", {}),
            },
        ))
    records.sort(key=lambda item: item[0], reverse=True)
    return [summary for _, summary in records[: max(0, limit)]]


def load_terminal_run(vault_root: str | Path, run_id: str) -> Optional[dict]:
    """Load a full run record by id (fail-open → None if not found)."""
    try:
        safe_run_id = _safe_run_id(run_id)
    except ValueError:
        return None
    root = runs_root(vault_root)
    if not root.exists():
        return None
    for path in root.rglob(f"{safe_run_id}.json"):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
    return None


def load_terminal_run_detail(vault_root: str | Path, run_id: str) -> dict:
    """Return a safe full run-detail envelope for read-only UI/CLI surfaces."""
    try:
        safe_run_id = _safe_run_id(run_id)
    except ValueError as exc:
        return {
            "ok": False,
            "run_id": run_id,
            "error": {"code": "unsafe_run_id", "message": str(exc)},
            "trust_state": UNTRUSTED_TIER,
            "terminal_output_trusted": False,
        }

    record = load_terminal_run(vault_root, safe_run_id)
    if record is None:
        return {
            "ok": False,
            "run_id": safe_run_id,
            "error": {"code": "run_not_found", "message": f"no terminal run record for {safe_run_id!r}"},
            "trust_state": UNTRUSTED_TIER,
            "terminal_output_trusted": False,
        }

    full_record = dict(record)
    full_record["trust_state"] = full_record.get("trust_state", UNTRUSTED_TIER)
    full_record["terminal_output_trusted"] = False
    return {
        "ok": True,
        "run_id": safe_run_id,
        "record": full_record,
        "trust_state": full_record["trust_state"],
        "terminal_output_trusted": False,
    }
