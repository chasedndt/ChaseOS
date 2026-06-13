"""
runtime.operator_surface.terminal.operator

Terminal operator command surface — the execution layer behind
`chaseos operate terminal`.

This is the governed CLI entry point for the Terminal Workbench. It drives the
bounded read-only ``TerminalAdapter`` and persists every executed run through
``terminal_runs``. It mirrors the structure of
``runtime/operator_surface/browser/operator.py``.

Governance (binding):
  - Only read-only-classified commands execute. Destructive / write / network /
    elevated / unknown commands are blocked at preview and never run.
  - Execution is bounded to an explicitly-allowed working directory.
  - Output is redacted, truncated, and labelled Tier 4 untrusted.
  - Every executed run writes a JSON + Markdown audit record.
  - This surface performs no canonical writeback and no provider calls.

Architecture: 06_AGENTS/Terminal-Workbench-Architecture.md
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional

from runtime.operator_surface.adapters.terminal_adapter import TerminalAdapter
from runtime.operator_surface.adapter_registry import get_default_registry
from runtime.operator_surface.capabilities import SurfaceType
from runtime.operator_surface.contracts import OperatorScope, OperatorSession
from runtime.operator_surface import terminal_runs

# Register the adapter in the default registry (idempotent, low-risk).
try:  # pragma: no cover - registration side effect
    get_default_registry().register(TerminalAdapter, replace=True)
except Exception:  # pragma: no cover
    pass


def _get_root(vault_root: Optional[Path] = None) -> Path:
    if vault_root:
        return Path(vault_root).resolve()
    env = os.environ.get("CHASEOS_VAULT_ROOT")
    if env:
        return Path(env).resolve()
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "CLAUDE.md").exists():
            return parent
    raise RuntimeError(
        "Cannot resolve vault root. Set CHASEOS_VAULT_ROOT or pass --vault-root."
    )


def _resolve_cwd(cwd: Optional[str], root: Path) -> Path:
    return Path(cwd).resolve() if cwd else root


def _build_adapter(cwd: Path) -> TerminalAdapter:
    scope = OperatorScope(
        run_id="terminal-cli-run",
        surface=SurfaceType.TERMINAL,
        target_uris=[f"file://{cwd}"],
        allowed_paths=[str(cwd)],
    )
    session = OperatorSession(
        run_id="terminal-cli-run", workflow_id="operate-terminal", surface="terminal"
    )
    adapter = TerminalAdapter()
    adapter.initialize(scope, session)
    return adapter


def _emit_nothing(_event) -> None:  # event sink for direct adapter drive
    return None


# ── policy ────────────────────────────────────────────────────────────────────

def run_policy(output_json: bool = False) -> int:
    """Show the read-only terminal operator authority surface."""
    payload = {
        "surface": "terminal",
        "adapter_status": TerminalAdapter.ADAPTER_STATUS,
        "execution_mode": "read_only_subprocess",
        "allowed_classes": ["read_only_command"],
        "blocked_classes": [
            "destructive_command",
            "write_command",
            "network_command",
            "elevated_command",
            "blocked_shell_control_command",
            "unknown_command",
        ],
        "approval_required_for": sorted(TerminalAdapter.APPROVAL_REQUIRED_ACTIONS),
        "safe_executables": sorted(TerminalAdapter.SAFE_EXECUTABLES),
        "output_trust": terminal_runs.UNTRUSTED_TIER,
        "terminal_output_trusted": False,
        "boundaries": {
            "sudo_or_elevation": False,
            "destructive_commands": False,
            "network_commands": False,
            "writes": False,
            "shell_operators": False,
            "canonical_writeback": False,
            "provider_calls": False,
            "cwd_outside_scope": False,
        },
    }
    if output_json:
        print(json.dumps(payload, indent=2))
    else:
        print("Terminal Operator Surface — read-only, bounded, audited")
        print(f"  adapter status:      {payload['adapter_status']}")
        print(f"  execution mode:      {payload['execution_mode']}")
        print(f"  allowed classes:     {', '.join(payload['allowed_classes'])}")
        print(f"  blocked classes:     {', '.join(payload['blocked_classes'])}")
        print(f"  output trust:        {payload['output_trust']} (never instructions)")
    return 0


# ── preview ───────────────────────────────────────────────────────────────────

def run_preview(command: str, cwd: Optional[str] = None, output_json: bool = False,
                vault_root: Optional[Path] = None) -> int:
    """Classify a command WITHOUT executing it."""
    classification = TerminalAdapter.classify_command(command)
    payload = {
        "command": command,
        "cwd": cwd,
        "classification": classification,
        "would_execute": classification["allowed"],
        "untrusted_tier": terminal_runs.UNTRUSTED_TIER,
    }
    if output_json:
        print(json.dumps(payload, indent=2))
    else:
        verdict = "ALLOW (read-only)" if classification["allowed"] else "BLOCK"
        print(f"[{verdict}] {command}")
        print(f"  class:  {classification['action_class']}")
        print(f"  reason: {classification['reason']}")
        if classification["approval_required"]:
            print("  approval: would be required for a future write-capable lane")
    return 0 if classification["allowed"] else 3


# ── run ───────────────────────────────────────────────────────────────────────

def run_command(command: str, cwd: Optional[str] = None, *, timeout: int = 15,
                max_output: int = 4000, actor: str = "operator",
                output_json: bool = False, vault_root: Optional[Path] = None) -> int:
    """Preview, then execute if read-only; persist an audited run record."""
    root = _get_root(vault_root)
    resolved_cwd = _resolve_cwd(cwd, root)

    classification = TerminalAdapter.classify_command(command)
    if not classification["allowed"]:
        record = terminal_runs.build_run_record(
            command=command, cwd=str(resolved_cwd), classification=classification,
            policy_decision="blocked", actor=actor,
        )
        paths = terminal_runs.record_terminal_run(root, record)
        payload = {"blocked": True, "classification": classification,
                   "audit_paths": paths, "untrusted_tier": terminal_runs.UNTRUSTED_TIER}
        if output_json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"[BLOCKED] {command}")
            print(f"  reason: {classification['reason']}")
            print(f"  audit:  {paths['json']}")
        return 3

    try:
        adapter = _build_adapter(resolved_cwd)
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        return 1

    start = time.monotonic()
    try:
        result = adapter.execute_step(
            {"step_index": 0, "action_type": "run_command", "command": command,
             "cwd": str(resolved_cwd), "timeout_seconds": timeout,
             "max_output_chars": max_output},
            _emit_nothing,
        )
    except OSError as exc:
        # e.g. executable not found on this host — record a clean error run.
        duration_ms = int((time.monotonic() - start) * 1000)
        record = terminal_runs.build_run_record(
            command=command, cwd=str(resolved_cwd), classification=classification,
            policy_decision="execution_error", actor=actor, duration_ms=duration_ms,
            stderr_excerpt=str(exc),
        )
        paths = terminal_runs.record_terminal_run(root, record)
        payload = {"ok": False, "run_id": record["run_id"], "error": str(exc),
                   "audit_paths": paths, "untrusted_tier": terminal_runs.UNTRUSTED_TIER}
        if output_json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"[ERROR] {command}")
            print(f"  {exc}")
            print(f"  audit: {paths['json']}")
        return 1
    duration_ms = int((time.monotonic() - start) * 1000)
    out = result.output if isinstance(result.output, dict) else {}

    record = terminal_runs.build_run_record(
        command=command, cwd=str(resolved_cwd), classification=classification,
        policy_decision="executed" if result.success else "executed_nonzero_or_blocked",
        actor=actor, exit_code=out.get("returncode"),
        stdout_excerpt=out.get("stdout", ""), stderr_excerpt=out.get("stderr", ""),
        duration_ms=duration_ms,
        output_truncated=bool(out.get("stdout_truncated") or out.get("stderr_truncated")),
        redactions_applied="[REDACTED]" in (out.get("stdout", "") + out.get("stderr", "")),
    )
    paths = terminal_runs.record_terminal_run(root, record)

    payload = {
        "ok": result.success,
        "run_id": record["run_id"],
        "action_class": result.action_type,
        "returncode": out.get("returncode"),
        "stdout": out.get("stdout", ""),
        "stderr": out.get("stderr", ""),
        "audit_paths": paths,
        "untrusted_tier": terminal_runs.UNTRUSTED_TIER,
        "terminal_output_trusted": False,
    }
    if output_json:
        print(json.dumps(payload, indent=2))
    else:
        status = "OK" if result.success else "NONZERO"
        print(f"[{status}] {command}  (exit {out.get('returncode')})")
        if out.get("stdout"):
            print("--- stdout (Tier 4 untrusted) ---")
            print(out["stdout"])
        if out.get("stderr"):
            print("--- stderr (Tier 4 untrusted) ---")
            print(out["stderr"])
        print(f"audit: {paths['json']}")
    return 0 if result.success else 1


# ── history ───────────────────────────────────────────────────────────────────

def run_history(limit: int = 20, output_json: bool = False,
                vault_root: Optional[Path] = None) -> int:
    root = _get_root(vault_root)
    runs = terminal_runs.list_terminal_runs(root, limit=limit)
    if output_json:
        print(json.dumps({"runs": runs, "count": len(runs)}, indent=2))
    else:
        if not runs:
            print("No terminal runs recorded yet.")
            return 0
        print(f"Recent terminal runs ({len(runs)}):")
        for r in runs:
            print(f"  {r['run_id']}  [{r['policy_decision']}/{r['classification']}]  {r['command']}")
    return 0


def run_show(run_id: str, output_json: bool = False,
             vault_root: Optional[Path] = None) -> int:
    """Show one audited terminal run record without executing anything."""
    root = _get_root(vault_root)
    detail = terminal_runs.load_terminal_run_detail(root, run_id)
    if output_json:
        print(json.dumps(detail, indent=2))
    elif detail.get("ok"):
        record = detail["record"]
        print(f"Terminal run {record['run_id']}")
        print(f"  command: {record.get('command', '')}")
        print(f"  cwd:     {record.get('cwd', '')}")
        print(f"  policy:  {record.get('policy_decision', '')}/{record.get('classification', '')}")
        print(f"  exit:    {record.get('exit_code')}")
        print(f"  trust:   {record.get('trust_state', terminal_runs.UNTRUSTED_TIER)} (not trusted instructions)")
        if record.get("stdout_excerpt"):
            print("--- stdout excerpt (Tier 4 untrusted) ---")
            print(record["stdout_excerpt"])
        if record.get("stderr_excerpt"):
            print("--- stderr excerpt (Tier 4 untrusted) ---")
            print(record["stderr_excerpt"])
    else:
        error = detail.get("error") or {}
        print(f"[NOT FOUND] {error.get('message', 'terminal run unavailable')}")
    return 0 if detail.get("ok") else 2
