"""
runtime.chaser.gateway_diagnostic

Chaser Gateway Diagnostic — the ChaseOS-native analog of `hermes gateway status` /
`openclaw doctor`.

This is a READ-ONLY readiness probe. It consolidates existing ChaseOS health
signals (boot context, runtime adapters, Agent Bus mode + heartbeats, schedule
intents, approval backlog, terminal surface policy) into a single state plus a
repair-plan. It NEVER starts a process, installs a service/cron/startup item,
calls a provider, or mutates canonical truth. On a degraded result it emits a
plan for operator review — it does not act on it.

See: 06_AGENTS/Chaser-Gateway-Architecture.md Section 6
     06_AGENTS/Terminal-ChaserAgent-Agent-Bus-Handover.md (unit N1)
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Diagnostic states (from the reverse-engineering books' ladder).
STATE_NOT_CONFIGURED = "not_configured"
STATE_CONFIGURED = "configured"
STATE_RUNNING = "running"
STATE_DEGRADED = "degraded"
STATE_FAILED = "failed"

# Heartbeat freshness thresholds (seconds) — mirrors runtime_cockpit convention.
FRESH_SECONDS = 120
RECENT_SECONDS = 900

_OK = "ok"
_DEGRADED = "degraded"
_FAILED = "failed"
_UNKNOWN = "unknown"


def _check(name: str, status: str, detail: str, **extra: Any) -> dict:
    return {"name": name, "status": status, "detail": detail, **extra}


def _parse_ts(value: Any) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _freshness(ts: Optional[datetime], now: datetime) -> str:
    if ts is None:
        return "unknown"
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    age = (now - ts).total_seconds()
    if age < FRESH_SECONDS:
        return "fresh"
    if age < RECENT_SECONDS:
        return "recent"
    return "stale"


# ── individual checks (each fail-open) ────────────────────────────────────────

def _check_boot_context(vault_root: Path, runtime_id: str) -> dict:
    try:
        from runtime.context.boot import load_boot_context

        bundle = load_boot_context(vault_root, runtime_id)
        status = {"ok": _OK, "degraded": _DEGRADED, "failed": _FAILED}.get(
            bundle.boot_status, _UNKNOWN
        )
        phase = getattr(bundle, "current_phase", "") or "unknown"
        warn = len(getattr(bundle, "warnings", []) or [])
        return _check("boot_context", status,
                      f"boot_status={bundle.boot_status}; phase={phase}; warnings={warn}",
                      boot_status=bundle.boot_status)
    except Exception as exc:  # pragma: no cover - defensive
        return _check("boot_context", _UNKNOWN, f"unavailable: {exc}")


def _check_runtime_adapters(vault_root: Path) -> dict:
    adapters_dir = vault_root / "runtime" / "memory" / "adapters"
    try:
        if not adapters_dir.exists():
            return _check("runtime_adapters", _DEGRADED, "no runtime memory adapters dir", runtimes=[])
        runtimes = sorted(p.name for p in adapters_dir.iterdir() if p.is_dir())
        status = _OK if runtimes else _DEGRADED
        return _check("runtime_adapters", status,
                      f"{len(runtimes)} registered: {', '.join(runtimes) or 'none'}",
                      runtimes=runtimes)
    except Exception as exc:
        return _check("runtime_adapters", _UNKNOWN, f"unavailable: {exc}")


def _check_bus_mode(vault_root: Path) -> dict:
    try:
        from runtime.agent_bus.bus import get_bus_mode

        mode = get_bus_mode(vault_root)
        return _check("agent_bus_mode", _OK, f"mode={mode}", mode=mode)
    except Exception as exc:
        return _check("agent_bus_mode", _UNKNOWN, f"unavailable: {exc}")


def _check_bus_heartbeats(vault_root: Path) -> dict:
    now = datetime.now(timezone.utc)
    # Read-only guard: do not materialize the bus backend. If no bus DB exists
    # yet, report it as not-initialized rather than creating one.
    bus_dir = vault_root / "runtime" / "agent_bus"
    if not (bus_dir.exists() and any(bus_dir.glob("*.sqlite"))):
        return _check("bus_heartbeats", _DEGRADED,
                      "agent bus not initialized (no heartbeats yet)", heartbeats={})
    try:
        from runtime.agent_bus.bus import list_heartbeats

        rows = list_heartbeats(vault_root)
        per_runtime: dict[str, str] = {}
        for row in rows:
            rt = row.get("runtime") or row.get("bus_name") or "unknown"
            ts = _parse_ts(row.get("updated_at") or row.get("last_seen") or row.get("timestamp"))
            fresh = _freshness(ts, now)
            # keep the freshest seen per runtime
            order = {"fresh": 3, "recent": 2, "stale": 1, "unknown": 0}
            if order[fresh] > order.get(per_runtime.get(rt, "unknown"), 0):
                per_runtime[rt] = fresh
        if not per_runtime:
            return _check("bus_heartbeats", _DEGRADED, "no heartbeats recorded", heartbeats={})
        live = [rt for rt, f in per_runtime.items() if f in ("fresh", "recent")]
        status = _OK if live else _DEGRADED
        detail = "; ".join(f"{rt}={f}" for rt, f in sorted(per_runtime.items()))
        return _check("bus_heartbeats", status, detail, heartbeats=per_runtime)
    except Exception as exc:
        return _check("bus_heartbeats", _UNKNOWN, f"unavailable: {exc}")


def _check_schedules(vault_root: Path) -> dict:
    try:
        from runtime.schedules.loader import validate_all_schedules

        errors = validate_all_schedules(vault_root)
        if not errors:
            return _check("schedule_intents", _OK, "all schedule intents valid", errors=[])
        detail = "; ".join(f"{sid}: {msg}" for sid, msg in errors[:5])
        return _check("schedule_intents", _DEGRADED, f"{len(errors)} invalid: {detail}",
                      errors=[{"schedule": s, "error": m} for s, m in errors])
    except Exception as exc:
        return _check("schedule_intents", _UNKNOWN, f"unavailable: {exc}")


def _check_approvals(vault_root: Path) -> dict:
    approvals_dir = vault_root / "runtime" / "studio" / "approvals"
    try:
        if not approvals_dir.exists():
            return _check("approval_backlog", _OK, "0 pending", pending=0)
        pending = sum(1 for p in approvals_dir.glob("*.json"))
        return _check("approval_backlog", _OK, f"{pending} pending", pending=pending)
    except Exception as exc:
        return _check("approval_backlog", _UNKNOWN, f"unavailable: {exc}")


def _check_terminal_surface(vault_root: Path) -> dict:
    policy = vault_root / "runtime" / "operator_surface" / "policies" / "terminal.yaml"
    try:
        if not policy.exists():
            return _check("terminal_surface", _DEGRADED, "terminal policy missing")
        runs = vault_root / "07_LOGS" / "Terminal-Runs"
        run_days = sum(1 for _ in runs.glob("*")) if runs.exists() else 0
        return _check("terminal_surface", _OK,
                      f"policy present; run-audit days={run_days}", run_audit_days=run_days)
    except Exception as exc:
        return _check("terminal_surface", _UNKNOWN, f"unavailable: {exc}")


# ── remediation plan ──────────────────────────────────────────────────────────

_REMEDIATION = {
    "boot_context": "Ensure 00_HOME/Now.md exists and the runtime adapter manifest is present (chaseos context boot).",
    "runtime_adapters": "Register at least one runtime (chaseos agent register …) so runtime/memory/adapters/ is populated.",
    "agent_bus_mode": "Check runtime/agent_bus/bus_config.yaml (mode: local|server); see chaseos agent-bus mode.",
    "bus_heartbeats": "Start a runtime watch loop / daemon so heartbeats are fresh (chaseos runtime daemon …). No auto-start is performed.",
    "schedule_intents": "Fix invalid schedule intents (chaseos schedule validate). Do not auto-enable.",
    "approval_backlog": "Review pending approvals in Studio before unattended work proceeds.",
    "terminal_surface": "Restore runtime/operator_surface/policies/terminal.yaml; verify chaseos operate terminal policy.",
}


def _next_actions(checks: list[dict]) -> list[dict]:
    actions: list[dict] = []
    for c in checks:
        if c["status"] in (_DEGRADED, _FAILED, _UNKNOWN):
            actions.append({
                "check": c["name"],
                "status": c["status"],
                "action": _REMEDIATION.get(c["name"], "Investigate; no automatic action will be taken."),
            })
    return actions


# ── public entry ──────────────────────────────────────────────────────────────

def run_gateway_diagnostic(vault_root: str | Path, *, runtime_id: str = "openclaw") -> dict:
    """Run the read-only Chaser Gateway readiness probe.

    Returns a structured result with per-check status, an overall state, and a
    repair-plan (`next_actions`). Performs NO host mutation, provider call, or
    canonical write.
    """
    root = Path(vault_root).resolve()
    checks = [
        _check_boot_context(root, runtime_id),
        _check_runtime_adapters(root),
        _check_bus_mode(root),
        _check_bus_heartbeats(root),
        _check_schedules(root),
        _check_approvals(root),
        _check_terminal_surface(root),
    ]

    statuses = {c["status"] for c in checks}
    boot = next((c for c in checks if c["name"] == "boot_context"), None)

    if boot is not None and boot["status"] == _FAILED:
        overall = STATE_FAILED
    elif _FAILED in statuses or _DEGRADED in statuses or _UNKNOWN in statuses:
        overall = STATE_DEGRADED
    else:
        overall = STATE_RUNNING

    next_actions = _next_actions(checks)

    return {
        "surface": "chaser_gateway_diagnostic",
        "ok": overall in (STATE_RUNNING, STATE_CONFIGURED),
        "overall_state": overall,
        "ready": overall == STATE_RUNNING,
        "runtime_id": runtime_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "next_actions": next_actions,
        "authority": {
            "host_mutation": False,
            "process_start": False,
            "startup_registration": False,
            "provider_calls": False,
            "canonical_writeback": False,
            "read_only": True,
        },
        "note": "Read-only readiness probe. A degraded result yields a plan for operator review; no action is taken automatically.",
    }
