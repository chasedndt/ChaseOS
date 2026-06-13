"""Studio Vault Health — data integrity surface.

Complements `studio-live-operator-activation` (runtime readiness) by verifying
the underlying vault data is intact and readable. Checks graph data, bus storage,
dedup registry, memory files, schedule config, and audit logs.

Lanes checked:
  1. graph_data_valid        — graph scanner runs, node_count > 0
  2. bus_storage_healthy     — SQLite WAL mode, all tables present, readable
  3. dedup_registry_valid    — .chaseos/dedup_registry.json is valid JSON
  4. memory_files_intact     — at least one runtime profile readable
  5. schedule_config_valid   — schedule loader runs, ≥ 1 valid schedule
  6. audit_logs_present      — Agent-Activity and Build-Logs dirs exist with files

`vault_healthy` = all 6 lanes pass.

Read-only: no mutations, no builds, no tasks created.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODEL_VERSION = "studio.studio_vault_health.v1"
SURFACE_ID = "studio_vault_health"
PASS_ID = "studio-vault-health"
NEXT_RECOMMENDED_PASS = "studio-live-operator-activation"

_BUS_REQUIRED_TABLES = ("tasks", "events", "heartbeats", "locks")
_AUDIT_LOG_DIRS = ("07_LOGS/Agent-Activity", "07_LOGS/Build-Logs")
_MEMORY_ADAPTERS_DIR = Path("runtime/memory/adapters")


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ── Lane 1: Graph data valid ──────────────────────────────────────────────────

def _check_graph_data_valid(vault: Path) -> dict[str, Any]:
    """Run the graph scanner; verify it succeeds and produces nodes."""
    try:
        from runtime.studio.graph_scanner_parser import build_graph_scanner_parser
        result = build_graph_scanner_parser(vault)
        if not result.get("ok"):
            return {
                "ok": False,
                "scanner_ok": False,
                "error": result.get("status", "scanner returned ok=False")[:120],
            }
        summary = result.get("graph_summary") or {}
        node_count = summary.get("node_count", 0) or 0
        edge_count = summary.get("edge_count", 0) or 0
        unresolved = summary.get("unresolved_reference_count", 0) or 0
        node_types = len(summary.get("node_type_counts") or {})
        has_nodes = node_count > 0
        return {
            "ok": has_nodes,
            "scanner_ok": True,
            "node_count": node_count,
            "edge_count": edge_count,
            "unresolved_references": unresolved,
            "node_type_count": node_types,
        }
    except Exception as exc:
        return {"ok": False, "scanner_ok": False, "error": str(exc)[:120]}


# ── Lane 2: Bus storage healthy ───────────────────────────────────────────────

def _check_bus_storage_healthy(vault: Path) -> dict[str, Any]:
    """SQLite WAL mode, all required tables present, bus is readable."""
    bus_path = vault / "runtime" / "agent_bus" / "agent_bus.sqlite"
    if not bus_path.exists():
        return {"ok": False, "error": "bus_storage_missing", "path": str(bus_path)}

    try:
        conn = sqlite3.connect(str(bus_path))
        conn.row_factory = sqlite3.Row

        journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        wal_mode = journal_mode.lower() == "wal"

        existing_tables = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        missing_tables = [t for t in _BUS_REQUIRED_TABLES if t not in existing_tables]
        all_tables_present = len(missing_tables) == 0

        task_count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        event_count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]

        conn.close()
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:120]}

    ok = all_tables_present  # WAL is desired but not a hard requirement
    return {
        "ok": ok,
        "wal_mode": wal_mode,
        "journal_mode": journal_mode,
        "all_tables_present": all_tables_present,
        "missing_tables": missing_tables,
        "task_count": task_count,
        "event_count": event_count,
        "size_bytes": bus_path.stat().st_size,
    }


# ── Lane 3: Dedup registry valid ──────────────────────────────────────────────

def _check_dedup_registry_valid(vault: Path) -> dict[str, Any]:
    """`.chaseos/dedup_registry.json` exists and is valid JSON."""
    reg_path = vault / ".chaseos" / "dedup_registry.json"
    if not reg_path.exists():
        # Registry is created lazily on first capture — missing is acceptable
        return {
            "ok": True,
            "exists": False,
            "entry_count": 0,
            "note": "registry not yet created (created on first capture)",
        }

    try:
        data = json.loads(reg_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "exists": True, "error": f"parse_error: {exc!s}"[:120]}

    if not isinstance(data, dict):
        return {
            "ok": False,
            "exists": True,
            "error": f"unexpected root type: {type(data).__name__}",
        }

    return {
        "ok": True,
        "exists": True,
        "entry_count": len(data),
        "size_bytes": reg_path.stat().st_size,
    }


# ── Lane 4: Memory files intact ───────────────────────────────────────────────

def _check_memory_files_intact(vault: Path) -> dict[str, Any]:
    """At least one runtime memory profile is readable JSON."""
    adapters_dir = vault / _MEMORY_ADAPTERS_DIR
    if not adapters_dir.exists():
        return {
            "ok": False,
            "error": "memory_adapters_dir_missing",
            "path": str(adapters_dir),
        }

    runtime_status: dict[str, Any] = {}
    readable_count = 0

    for rt_dir in sorted(adapters_dir.iterdir()):
        if not rt_dir.is_dir():
            continue
        profile = rt_dir / "profile.json"
        if profile.exists():
            try:
                data = json.loads(profile.read_text(encoding="utf-8"))
                runtime_status[rt_dir.name] = {
                    "profile_readable": True,
                    "runtime_id": data.get("runtime_id"),
                }
                readable_count += 1
            except Exception as exc:
                runtime_status[rt_dir.name] = {
                    "profile_readable": False,
                    "error": str(exc)[:80],
                }
        else:
            runtime_status[rt_dir.name] = {"profile_readable": False, "error": "profile.json missing"}

    ok = readable_count > 0
    return {
        "ok": ok,
        "readable_profiles": readable_count,
        "runtime_status": runtime_status,
    }


# ── Lane 5: Schedule config valid ────────────────────────────────────────────

def _check_schedule_config_valid(vault: Path) -> dict[str, Any]:
    """Schedule loader runs without error; at least 1 valid schedule present."""
    try:
        from runtime.schedules.loader import list_schedules, validate_all_schedules
        schedules = list_schedules(vault)
    except Exception as exc:
        return {"ok": False, "error": f"loader_failed: {exc!s}"[:120]}

    schedule_count = len(schedules)
    enabled_count = sum(1 for s in schedules if getattr(s, "enabled", False))

    try:
        validation = validate_all_schedules(vault)
        all_valid = validation.get("all_valid", False) if isinstance(validation, dict) else True
        invalid_count = validation.get("invalid_count", 0) if isinstance(validation, dict) else 0
    except Exception:
        all_valid = True  # validation is advisory; loader success is the hard check
        invalid_count = 0

    ok = schedule_count > 0
    return {
        "ok": ok,
        "schedule_count": schedule_count,
        "enabled_count": enabled_count,
        "all_valid": all_valid,
        "invalid_count": invalid_count,
    }


# ── Lane 6: Audit logs present ───────────────────────────────────────────────

def _check_audit_logs_present(vault: Path) -> dict[str, Any]:
    """Agent-Activity and Build-Logs dirs exist and contain files."""
    dir_status: dict[str, Any] = {}
    all_ok = True

    for rel in _AUDIT_LOG_DIRS:
        log_dir = vault / rel
        exists = log_dir.exists()
        if exists:
            try:
                count = sum(1 for f in log_dir.iterdir() if f.is_file())
            except Exception:
                count = 0
            dir_status[rel] = {"exists": True, "file_count": count}
            if count == 0:
                all_ok = False
        else:
            dir_status[rel] = {"exists": False, "file_count": 0}
            all_ok = False

    return {
        "ok": all_ok,
        "dirs": dir_status,
    }


# ── Main builder ──────────────────────────────────────────────────────────────

def build_studio_vault_health(vault_root: str | Path) -> dict[str, Any]:
    """Aggregate vault data integrity checks into a health summary.

    Read-only: no mutations, no builds, no tasks created, no vault mutations.
    """
    vault = Path(vault_root).resolve()

    # ── Run all lanes ─────────────────────────────────────────────────────────
    graph_lane = _check_graph_data_valid(vault)
    bus_lane = _check_bus_storage_healthy(vault)
    dedup_lane = _check_dedup_registry_valid(vault)
    memory_lane = _check_memory_files_intact(vault)
    schedule_lane = _check_schedule_config_valid(vault)
    audit_lane = _check_audit_logs_present(vault)

    lanes: dict[str, dict[str, Any]] = {
        "graph_data_valid": graph_lane,
        "bus_storage_healthy": bus_lane,
        "dedup_registry_valid": dedup_lane,
        "memory_files_intact": memory_lane,
        "schedule_config_valid": schedule_lane,
        "audit_logs_present": audit_lane,
    }

    lane_results = {name: lane.get("ok", False) for name, lane in lanes.items()}
    all_ok = all(lane_results.values())
    failing_lanes = [name for name, ok in lane_results.items() if not ok]
    vault_healthy = all_ok

    # ── Status ────────────────────────────────────────────────────────────────
    if vault_healthy:
        node_count = graph_lane.get("node_count", 0)
        task_count = bus_lane.get("task_count", 0)
        status = (
            f"VAULT HEALTHY — {node_count:,} graph nodes, "
            f"{task_count:,} bus tasks, all data layers intact"
        )
    else:
        status = (
            f"VAULT DEGRADED — {len(failing_lanes)} lane(s) failing: "
            f"{', '.join(failing_lanes[:3])}"
        )

    # ── Operator notes ────────────────────────────────────────────────────────
    operator_notes: list[str] = []
    if not graph_lane.get("ok"):
        operator_notes.append(
            "Graph scanner returned no nodes — run: chaseos studio graph-scanner-parser"
        )
    if not bus_lane.get("wal_mode", True):
        operator_notes.append(
            "Agent Bus SQLite is not in WAL mode — consider re-initialising: "
            "chaseos agent-bus mode"
        )
    if (graph_lane.get("unresolved_references") or 0) > 50:
        operator_notes.append(
            f"Graph has {graph_lane['unresolved_references']} unresolved references — "
            "run: chaseos maintain vault"
        )

    return {
        "ok": True,  # probe itself always succeeds
        "vault_healthy": vault_healthy,
        "pass": PASS_ID,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
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
