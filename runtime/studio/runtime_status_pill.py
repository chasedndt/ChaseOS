"""Read-only Studio runtime status pill model.

Derives the current OSRIL mode state from agent bus task state and
pending approval queue. No vault writes. Fail-open if bus unavailable.

Mode states (from Operator-Overlay-UX-Spec.md):
  OBSERVE | PLAN | ACT | AWAIT_APPROVAL | RECOVER | DONE | FAILED | IDLE
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MODEL_VERSION = "studio.runtime_status_pill.v1"
SURFACE_ID = "studio_runtime_status_pill"

_APPROVALS_DIR = Path("runtime") / "studio" / "approvals"

_MODE_META: dict[str, dict[str, Any]] = {
    "OBSERVE":        {"color": "gray",   "pulse": False},
    "PLAN":           {"color": "blue",   "pulse": True},
    "ACT":            {"color": "green",  "pulse": True},
    "AWAIT_APPROVAL": {"color": "amber",  "pulse": False},
    "RECOVER":        {"color": "orange", "pulse": True},
    "DONE":           {"color": "green",  "pulse": False},
    "FAILED":         {"color": "red",    "pulse": False},
    "IDLE":           {"color": "gray",   "pulse": False},
}


def _derive_mode(
    *,
    active_count: int,
    pending_approval_count: int,
    failed_count: int,
) -> str:
    if pending_approval_count > 0:
        return "AWAIT_APPROVAL"
    if active_count > 0:
        return "ACT"
    if failed_count > 0:
        return "RECOVER"
    return "OBSERVE"


def _read_pending_approvals(vault: Path) -> list[dict[str, Any]]:
    approval_dir = vault / _APPROVALS_DIR
    if not approval_dir.exists():
        return []
    results = []
    for f in sorted(approval_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("status") == "pending":
                results.append({
                    "approval_id": data.get("approval_id", f.stem),
                    "action_type": data.get("action_type", "unknown"),
                })
        except Exception:
            pass
    return results


def get_runtime_status(vault_root: str | Path) -> dict[str, Any]:
    """Return the current OSRIL runtime status pill data.

    Reads agent bus task list (fail-open if bus unavailable).
    Reads runtime/studio/approvals/ for pending approvals.
    No writes.
    """
    vault = Path(vault_root).resolve()
    warnings: list[str] = []
    bus_available = False
    active_tasks: list[dict[str, Any]] = []
    failed_tasks: list[dict[str, Any]] = []
    heartbeats: list[dict[str, Any]] = []

    try:
        from runtime.agent_bus.bus import list_tasks  # type: ignore[import]
        raw_tasks = list_tasks(str(vault)) or []
        bus_available = True
        for t in raw_tasks:
            status = (t.get("status") or "").lower()
            if status in ("in_progress", "claimed", "started"):
                active_tasks.append({
                    "task_id": t.get("task_id") or t.get("id", "?"),
                    "task_type": t.get("task_type", "unknown"),
                    "status": status,
                    "owner": t.get("owner", ""),
                })
            elif status == "failed":
                failed_tasks.append({
                    "task_id": t.get("task_id") or t.get("id", "?"),
                    "task_type": t.get("task_type", "unknown"),
                })
    except ImportError:
        warnings.append("agent_bus_not_available")
    except Exception as exc:
        warnings.append(f"bus_read_error:{type(exc).__name__}")

    try:
        from runtime.agent_bus.bus import list_heartbeats  # type: ignore[import]
        heartbeats = list_heartbeats(str(vault)) or []
    except Exception:
        pass  # heartbeats are informational only

    pending_approvals = _read_pending_approvals(vault)

    mode = _derive_mode(
        active_count=len(active_tasks),
        pending_approval_count=len(pending_approvals),
        failed_count=len(failed_tasks),
    )
    meta = _MODE_META.get(mode, _MODE_META["OBSERVE"])

    return {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "mode": mode,
        "color": meta["color"],
        "pulse": meta["pulse"],
        "label": mode.replace("_", " "),
        "active_task_count": len(active_tasks),
        "pending_approval_count": len(pending_approvals),
        "failed_task_count": len(failed_tasks),
        "heartbeat_count": len(heartbeats),
        "bus_available": bus_available,
        "active_tasks": active_tasks[:5],
        "pending_approvals": pending_approvals[:5],
        "heartbeats": heartbeats[:10],
        "warnings": warnings,
        "readiness": {
            "bus_available": bus_available,
            "mode_derived": True,
            "read_only": True,
            "writes_vault": False,
            "provider_calls": False,
            "connector_calls": False,
        },
    }
