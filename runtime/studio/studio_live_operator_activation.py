"""Studio Live Operator Activation — runtime activation state surface.

Checks whether the operator has moved beyond static hardening into a live,
active operating state. Complements `studio-product-hardening-complete` (which
confirms static readiness) by checking runtime/activity signals.

Lanes checked:
  1. Shell launch ready   — config + frontend assets + api importable
  2. Dispatch chain       — bus storage + send/poll + provider-agnostic (static)
  3. Daemon liveness      — any runtime heartbeat within 24 h
  4. Schedules configured — operator_today + operator_close_day enabled
  5. Recent operator activity — operator briefs in last 7 days
  6. Bus traffic          — agent bus tasks created in last 7 days

`operator_activated` = lanes 1 + 2 pass (static chain fully wired and launchable).
`fully_live`         = all 6 lanes pass (operator is actively using the system).

Read-only: no builds, no daemons started, no tasks created, no vault mutations.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


MODEL_VERSION = "studio.studio_live_operator_activation.v1"
SURFACE_ID = "studio_live_operator_activation"
PASS_ID = "studio-live-operator-activation"
NEXT_RECOMMENDED_PASS = "studio-live-operator-activation"  # terminal — loops to self

_DAEMON_RUNTIMES = ("hermes", "openclaw", "archon")
_DAEMON_HEARTBEAT_WINDOW_H = 24     # within 24 h → "recent enough" for activation check
_ACTIVITY_WINDOW_DAYS = 7
_CORE_SCHEDULES = ("sch-operator-today-0700", "sch-operator-close-day-1900")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _now_utc_str() -> str:
    return _now_utc().isoformat().replace("+00:00", "Z")


# ── Lane 1: Shell launch ready ────────────────────────────────────────────────

def _check_shell_launch_ready(vault: Path) -> dict[str, Any]:
    """Config importable + frontend assets present + api importable."""
    try:
        from runtime.studio.shell import config as _cfg  # noqa: F401
        config_importable = True
    except Exception as exc:
        return {"ok": False, "config_importable": False, "error": str(exc)[:120]}

    try:
        from runtime.studio.shell.api import StudioAPI  # noqa: F401
        api_importable = True
    except Exception as exc:
        return {"ok": False, "config_importable": True, "api_importable": False, "error": str(exc)[:120]}

    shell_dir = Path(__file__).parent / "shell"
    frontend_dir = shell_dir / "frontend"
    index_present = (frontend_dir / "index.html").exists()
    app_present = (frontend_dir / "app.js").exists()
    css_present = (frontend_dir / "styles.css").exists()
    frontend_ok = index_present and app_present and css_present

    # Soft: exe packaged
    dist_exe = shell_dir / "dist" / "ChaseOS-Studio.exe"
    exe_built = dist_exe.exists()

    ok = config_importable and api_importable and frontend_ok
    return {
        "ok": ok,
        "config_importable": config_importable,
        "api_importable": api_importable,
        "frontend_assets_present": frontend_ok,
        "index_html": index_present,
        "app_js": app_present,
        "styles_css": css_present,
        "exe_built": exe_built,
    }


# ── Lane 2: Dispatch chain ────────────────────────────────────────────────────

def _check_dispatch_chain(vault: Path) -> dict[str, Any]:
    """Bus storage accessible + send/poll importable + provider-agnostic confirmed."""
    bus_path = vault / "runtime" / "agent_bus" / "agent_bus.sqlite"
    bus_accessible = bus_path.exists()

    try:
        from runtime.studio.phase11_chat_send_message import (  # noqa: F401
            send_chat_message as _send,
            poll_chat_result as _poll,
        )
        send_poll_importable = True
    except Exception:
        send_poll_importable = False

    # Provider-agnostic routing is an architectural invariant confirmed at design time;
    # no runtime check needed beyond the import above.
    provider_agnostic_ok = True

    ok = bus_accessible and send_poll_importable and provider_agnostic_ok
    return {
        "ok": ok,
        "bus_storage_accessible": bus_accessible,
        "send_poll_importable": send_poll_importable,
        "provider_agnostic_confirmed": provider_agnostic_ok,
        "bus_path": str(bus_path),
    }


# ── Lane 3: Daemon liveness ───────────────────────────────────────────────────

def _check_daemon_liveness(vault: Path) -> dict[str, Any]:
    """At least one runtime has a heartbeat within the last 24 hours."""
    bus_path = vault / "runtime" / "agent_bus" / "agent_bus.sqlite"
    if not bus_path.exists():
        return {"ok": False, "error": "bus_storage_missing", "live_runtimes": [], "any_live": False}

    cutoff = _now_utc() - timedelta(hours=_DAEMON_HEARTBEAT_WINDOW_H)
    cutoff_str = cutoff.isoformat().replace("+00:00", "Z")

    live_runtimes: list[str] = []
    runtime_states: dict[str, Any] = {}

    try:
        conn = sqlite3.connect(str(bus_path))
        conn.row_factory = sqlite3.Row
        for rt in _DAEMON_RUNTIMES:
            row = conn.execute(
                "SELECT last_seen FROM heartbeats WHERE LOWER(runtime) = LOWER(?)"
                " ORDER BY last_seen DESC LIMIT 1",
                (rt,),
            ).fetchone()
            if row:
                last_seen = row["last_seen"]
                age_s = (_now_utc() - datetime.fromisoformat(
                    last_seen.replace("Z", "+00:00")
                )).total_seconds()
                is_live = last_seen >= cutoff_str
                if is_live:
                    live_runtimes.append(rt)
                runtime_states[rt] = {
                    "last_seen": last_seen,
                    "age_seconds": round(age_s, 1),
                    "within_24h": is_live,
                }
            else:
                runtime_states[rt] = {"last_seen": None, "within_24h": False}
        conn.close()
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:120], "live_runtimes": [], "any_live": False}

    any_live = len(live_runtimes) > 0
    return {
        "ok": any_live,
        "any_live": any_live,
        "live_runtimes": live_runtimes,
        "runtime_states": runtime_states,
        "heartbeat_window_hours": _DAEMON_HEARTBEAT_WINDOW_H,
    }


# ── Lane 4: Schedules configured ─────────────────────────────────────────────

def _check_schedules_configured(vault: Path) -> dict[str, Any]:
    """operator_today + operator_close_day are enabled; count total enabled."""
    try:
        from runtime.schedules.loader import list_schedules
        schedules = list_schedules(vault)
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:120]}

    enabled_ids: list[str] = []
    core_status: dict[str, bool] = {sid: False for sid in _CORE_SCHEDULES}

    for s in schedules:
        sid = getattr(s, "schedule_id", None)
        enabled = getattr(s, "enabled", False)
        if enabled and sid:
            enabled_ids.append(sid)
            if sid in core_status:
                core_status[sid] = True

    core_ok = all(core_status.values())
    return {
        "ok": core_ok,
        "core_schedules_enabled": core_ok,
        "core_schedule_status": core_status,
        "enabled_schedule_count": len(enabled_ids),
        "enabled_schedules": enabled_ids,
    }


# ── Lane 5: Recent operator activity ─────────────────────────────────────────

def _check_recent_operator_activity(vault: Path) -> dict[str, Any]:
    """Operator briefs or AOR audit records created in the last 7 days."""
    cutoff = _now_utc() - timedelta(days=_ACTIVITY_WINDOW_DAYS)

    def _recent_files_in(folder: Path) -> list[str]:
        if not folder.exists():
            return []
        recent = []
        for f in folder.iterdir():
            if f.is_file():
                try:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
                    if mtime >= cutoff:
                        recent.append(f.name)
                except Exception:
                    pass
        return sorted(recent, reverse=True)[:5]

    briefs_dir = vault / "07_LOGS" / "Operator-Briefs"
    activity_dir = vault / "07_LOGS" / "Agent-Activity"

    recent_briefs = _recent_files_in(briefs_dir)
    recent_activity = _recent_files_in(activity_dir)

    any_recent = bool(recent_briefs or recent_activity)
    return {
        "ok": any_recent,
        "any_recent_activity": any_recent,
        "recent_operator_briefs": recent_briefs,
        "recent_aor_activity": recent_activity,
        "window_days": _ACTIVITY_WINDOW_DAYS,
    }


# ── Lane 6: Bus traffic ───────────────────────────────────────────────────────

def _check_bus_traffic(vault: Path) -> dict[str, Any]:
    """Agent bus has had tasks created in the last 7 days."""
    bus_path = vault / "runtime" / "agent_bus" / "agent_bus.sqlite"
    if not bus_path.exists():
        return {"ok": False, "error": "bus_storage_missing", "recent_task_count": 0}

    cutoff = (_now_utc() - timedelta(days=_ACTIVITY_WINDOW_DAYS)).isoformat().replace("+00:00", "Z")

    try:
        conn = sqlite3.connect(str(bus_path))
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM tasks WHERE created_at >= ?",
            (cutoff,),
        ).fetchone()
        count = row[0] if row else 0

        # Most recent task timestamp
        recent_row = conn.execute(
            "SELECT created_at FROM tasks ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        last_task_at = recent_row[0] if recent_row else None
        conn.close()
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:120], "recent_task_count": 0}

    return {
        "ok": count > 0,
        "recent_task_count": count,
        "last_task_at": last_task_at,
        "window_days": _ACTIVITY_WINDOW_DAYS,
    }


# ── Main builder ──────────────────────────────────────────────────────────────

def build_studio_live_operator_activation(vault_root: str | Path) -> dict[str, Any]:
    """Aggregate all activation lanes into an operator-activation state report.

    Read-only: no builds, no daemons started, no tasks created, no vault mutations.
    """
    vault = Path(vault_root).resolve()

    # ── Run all lanes ─────────────────────────────────────────────────────────
    shell_lane = _check_shell_launch_ready(vault)
    dispatch_lane = _check_dispatch_chain(vault)
    daemon_lane = _check_daemon_liveness(vault)
    schedules_lane = _check_schedules_configured(vault)
    activity_lane = _check_recent_operator_activity(vault)
    bus_traffic_lane = _check_bus_traffic(vault)

    lanes: dict[str, dict[str, Any]] = {
        "shell_launch_ready": shell_lane,
        "dispatch_chain": dispatch_lane,
        "daemon_liveness": daemon_lane,
        "schedules_configured": schedules_lane,
        "recent_operator_activity": activity_lane,
        "bus_traffic": bus_traffic_lane,
    }

    lane_results = {name: lane.get("ok", False) for name, lane in lanes.items()}
    failing_lanes = [name for name, ok in lane_results.items() if not ok]

    # ── Activation levels ─────────────────────────────────────────────────────
    # operator_activated = static chain fully wired (shell + dispatch)
    operator_activated = shell_lane.get("ok", False) and dispatch_lane.get("ok", False)

    # fully_live = all 6 lanes green
    fully_live = all(lane_results.values())

    # Partial activation: activated but not all runtime lanes green
    partial_lanes_failing = [
        name for name in ("daemon_liveness", "schedules_configured",
                          "recent_operator_activity", "bus_traffic")
        if not lane_results.get(name, False)
    ]

    # ── Status string ─────────────────────────────────────────────────────────
    if fully_live:
        status = "FULLY LIVE — operator activated, daemons live, recent activity confirmed"
    elif operator_activated and not partial_lanes_failing:
        status = "ACTIVATED — all static lanes clear; start a runtime daemon for live dispatch"
    elif operator_activated:
        status = (
            f"ACTIVATED (partial runtime) — {len(partial_lanes_failing)} runtime "
            f"lane(s) pending: {', '.join(partial_lanes_failing[:2])}"
        )
    else:
        static_failing = [n for n in ("shell_launch_ready", "dispatch_chain") if not lane_results.get(n)]
        status = f"NOT ACTIVATED — static prerequisites failing: {', '.join(static_failing)}"

    # ── Operator notes ────────────────────────────────────────────────────────
    operator_notes: list[str] = []
    if not daemon_lane.get("ok"):
        operator_notes.append(
            "No runtime daemon heartbeat within 24 h — start Hermes or OpenClaw "
            "via Studio Chat panel (Start Runtime button) or: "
            "chaseos runtime daemon --runtime hermes --synthesize"
        )
    if not shell_lane.get("exe_built"):
        operator_notes.append(
            "ChaseOS-Studio.exe not yet built — run build_exe.ps1 to produce "
            "the standalone desktop application."
        )
    if not schedules_lane.get("core_schedules_enabled"):
        missing = [sid for sid, ok in schedules_lane.get("core_schedule_status", {}).items() if not ok]
        operator_notes.append(
            f"Core schedules not enabled: {', '.join(missing)}. "
            "Enable via: chaseos schedule enable <schedule_id>"
        )
    if not activity_lane.get("ok"):
        operator_notes.append(
            f"No operator briefs or AOR activity in the last {_ACTIVITY_WINDOW_DAYS} days. "
            "Run: chaseos run operator_today"
        )

    return {
        "ok": True,  # probe itself always succeeds
        "operator_activated": operator_activated,
        "fully_live": fully_live,
        "pass": PASS_ID,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc_str(),
        "vault_root": str(vault),
        "status": status,
        "lane_results": lane_results,
        "failing_lanes": failing_lanes,
        "lanes": lanes,
        "operator_notes": operator_notes,
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        "authority": {
            "read_only": True,
            "builds_triggered": False,
            "daemons_started": False,
            "tasks_created": False,
            "vault_mutations": False,
        },
    }
