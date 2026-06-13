"""
runtime.operator_surface.browser.replay

Replay module — reconstruct a browser operator run from its audit artifact.

Replay is READ-ONLY. It does not re-execute any browser actions.
It reconstructs the event sequence from the audit artifact for:
  - Post-mortem analysis
  - Operator review of what happened
  - Debugging failed runs

Architecture: 06_AGENTS/Full-System-Operator-Surface.md Section 6.4
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from runtime.operator_surface.audit import load_audit, reconstruct_event_sequence


def _safe_print(text: str) -> None:
    """Print text with Unicode errors replaced — handles narrow Windows console encodings."""
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))
from runtime.operator_surface.events import OperatorEvent, OperatorEventType


def replay_run(run_id: str, vault_root: Optional[Path] = None) -> Optional[dict]:
    """
    Load and return the full run replay from audit artifact.

    Returns a dict with:
      - run_metadata: run_id, workflow_id, surface, outcome, timing
      - scope: declared scope
      - event_sequence: list of events in order
      - approvals: approval records
      - summary: step counts, outcome, captures

    Returns None if no audit artifact found for run_id.
    """
    audit_data = load_audit(run_id, vault_root)
    if audit_data is None:
        return None

    events = reconstruct_event_sequence(audit_data)

    return {
        "run_metadata": {
            "run_id": audit_data.get("run_id"),
            "workflow_id": audit_data.get("workflow_id"),
            "surface": audit_data.get("surface"),
            "outcome": audit_data.get("outcome"),
            "started_at": audit_data.get("started_at"),
            "completed_at": audit_data.get("completed_at"),
        },
        "scope": audit_data.get("scope"),
        "event_sequence": [e.to_dict() for e in events],
        "approvals": audit_data.get("approvals", []),
        "summary": {
            "steps_planned": audit_data.get("steps_planned", 0),
            "steps_completed": audit_data.get("steps_completed", 0),
            "steps_failed": audit_data.get("steps_failed", 0),
            "approvals_required": audit_data.get("approvals_required", 0),
            "approvals_granted": audit_data.get("approvals_granted", 0),
            "approvals_denied": audit_data.get("approvals_denied", 0),
            "vault_writes": audit_data.get("vault_writes", []),
            "capture_ids": audit_data.get("capture_ids", []),
        },
    }


def print_replay(run_id: str, vault_root: Optional[Path] = None) -> None:
    """
    Print a human-readable replay of a run to stdout.
    For use with `chaseos operate replay RUN_ID`.
    """
    replay = replay_run(run_id, vault_root)
    if replay is None:
        print(f"No audit artifact found for run_id: {run_id}")
        return

    meta = replay["run_metadata"]
    summary = replay["summary"]
    events = replay["event_sequence"]

    _safe_print(f"\n{'='*60}")
    _safe_print(f"  OPERATOR RUN REPLAY")
    _safe_print(f"{'='*60}")
    _safe_print(f"  Run ID:     {meta['run_id']}")
    _safe_print(f"  Workflow:   {meta['workflow_id']}")
    _safe_print(f"  Surface:    {meta['surface']}")
    _safe_print(f"  Outcome:    {meta['outcome']}")
    _safe_print(f"  Started:    {meta['started_at']}")
    _safe_print(f"  Completed:  {meta['completed_at']}")
    _safe_print(
        f"\n  Steps: {summary['steps_completed']}/{summary['steps_planned']} completed, "
        f"{summary['steps_failed']} failed"
    )
    _safe_print(
        f"  Approvals: {summary['approvals_granted']} granted, "
        f"{summary['approvals_denied']} denied"
    )
    _safe_print(f"\n  Event sequence:")
    for e in events:
        symbol = {
            "step_complete": "+",
            "step_failed": "!",
            "await_approval": "?",
            "recovery_started": "~",
            "session_complete": "*",
            "session_failed": "*",
        }.get(e.get("event_type", ""), " ")
        _safe_print(
            f"  {symbol} [{e.get('timestamp', '')[-8:-1]}]  "
            f"{e.get('event_type', '').upper():<20}  {e.get('description', '')}"
        )
    _safe_print(f"{'='*60}\n")
