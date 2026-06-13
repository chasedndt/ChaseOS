"""Read-only live status probes for Studio runtime surfaces.

This module intentionally does not start, stop, initialize, or write runtime
state. It only reads local configuration/evidence and performs short TCP probes
against explicit candidate gateway ports.
"""
from __future__ import annotations

import json
import os
import re
import socket
import sqlite3
import subprocess
import ctypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODEL_VERSION = "studio.runtime_live_status.v1"

_FRESH_THRESHOLD_SECONDS = 120
_DEFAULT_RECENT_THRESHOLD_SECONDS = 900
_PORT_PROBE_TIMEOUT_SECONDS = 0.25
_RUNTIME_BUS_NAMES: dict[str, str] = {
    "hermes": "Hermes",
    "openclaw": "OpenClaw",
    "claude-code": "Archon",
}
_FALLBACK_PORTS: dict[str, list[int]] = {
    "hermes": [9119, 18790, 18791],
    "openclaw": [18789],
    "claude-code": [],
}
_ENV_PORT_KEYS: dict[str, list[str]] = {
    "hermes": [
        "CHASEOS_HERMES_PORT",
        "CHASEOS_HERMES_GATEWAY_PORT",
        "HERMES_PORT",
        "HERMES_GATEWAY_PORT",
    ],
    "openclaw": [
        "CHASEOS_OPENCLAW_PORT",
        "CHASEOS_OPENCLAW_GATEWAY_PORT",
        "OPENCLAW_PORT",
        "OPENCLAW_GATEWAY_PORT",
    ],
}
_RUN_STATE_SUFFIXES = {".json", ".jsonl", ".log", ".txt"}
_RUN_STATE_MAX_FILES = 24
_RUN_STATE_MAX_BYTES = 262_144
_WSL_PROCESS_TIMEOUT_SECONDS = 2.5


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def seconds_since(iso_ts: str | None) -> float | None:
    if not iso_ts:
        return None
    try:
        dt = datetime.fromisoformat(str(iso_ts).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds()
    except Exception:
        return None


def heartbeat_freshness(elapsed_seconds: float | None, *, recent_threshold_seconds: int = _DEFAULT_RECENT_THRESHOLD_SECONDS) -> str:
    if elapsed_seconds is None:
        return "offline"
    if elapsed_seconds < _FRESH_THRESHOLD_SECONDS:
        return "fresh"
    if elapsed_seconds < recent_threshold_seconds:
        return "recent"
    return "stale"


def _runtime_id(value: str | None) -> str:
    runtime = str(value or "").strip().lower()
    if runtime in {"hermes", "openclaw", "claude-code"}:
        return runtime
    if runtime in {"open_claw", "open claw"}:
        return "openclaw"
    if runtime in {"archon", "claude"}:
        return "claude-code"
    return runtime or "hermes"


def _dedupe_ports(ports: list[int]) -> list[int]:
    seen: set[int] = set()
    result: list[int] = []
    for port in ports:
        if 0 < int(port) <= 65535 and int(port) not in seen:
            seen.add(int(port))
            result.append(int(port))
    return result


def _parse_int(value: Any) -> int | None:
    try:
        parsed = int(str(value).strip())
    except Exception:
        return None
    if 0 < parsed <= 65535:
        return parsed
    return None


def _parse_positive_int(value: Any) -> int | None:
    try:
        parsed = int(str(value).strip())
    except Exception:
        return None
    if parsed > 0:
        return parsed
    return None


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _registry_ports(vault: Path, runtime_id: str) -> list[int]:
    registry = _read_json(vault / "runtime" / "lifecycle" / "runtime-registry.json")
    record = ((registry.get("runtimes") or {}).get(runtime_id) or {})
    ports: list[int] = []
    gateway_port = _parse_int(record.get("gateway_port"))
    if gateway_port:
        ports.append(gateway_port)
    for value in (record.get("dashboard_url"), *(record.get("health_urls") or [])):
        for match in re.findall(r":(\d{2,5})(?:/|$)", str(value or "")):
            parsed = _parse_int(match)
            if parsed:
                ports.append(parsed)
    return ports


def _lifecycle_text(vault: Path, runtime_id: str) -> str:
    path = vault / "runtime" / "lifecycle" / f"{runtime_id}.lifecycle.yaml"
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _lifecycle_recent_threshold(vault: Path, runtime_id: str) -> int:
    text = _lifecycle_text(vault, runtime_id)
    match = re.search(r"\bstale_after_seconds:\s*(\d+)", text)
    parsed = _parse_int(match.group(1)) if match else None
    return parsed or _DEFAULT_RECENT_THRESHOLD_SECONDS


def _lifecycle_ports(vault: Path, runtime_id: str) -> list[int]:
    text = _lifecycle_text(vault, runtime_id)
    ports: list[int] = []
    in_candidate_ports = False
    candidate_indent: int | None = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("candidate_ports:"):
            in_candidate_ports = True
            candidate_indent = len(line) - len(line.lstrip())
            continue
        if in_candidate_ports:
            indent = len(line) - len(line.lstrip())
            if stripped.startswith("-"):
                parsed = _parse_int(stripped.lstrip("-").strip())
                if parsed:
                    ports.append(parsed)
                continue
            if candidate_indent is not None and indent <= candidate_indent:
                in_candidate_ports = False
    for match in re.findall(r":(\d{2,5})(?:/|$)", text):
        parsed = _parse_int(match)
        if parsed:
            ports.append(parsed)
    for match in re.findall(r"--port\s+(\d{2,5})", text):
        parsed = _parse_int(match)
        if parsed:
            ports.append(parsed)
    return ports


def _run_state_sort_key(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except Exception:
        return 0.0


def _read_bounded_text(path: Path) -> str:
    try:
        data = path.read_bytes()
    except Exception:
        return ""
    if len(data) <= _RUN_STATE_MAX_BYTES:
        sample = data
    else:
        half = _RUN_STATE_MAX_BYTES // 2
        sample = data[:half] + b"\n" + data[-half:]
    return sample.decode("utf-8", errors="ignore")


def _ports_from_text(text: str) -> list[int]:
    ports: list[int] = []
    patterns = (
        r":(\d{2,5})(?:/|\s|$)",
        r"\b(?:port|gateway_port|gateway-port|listen_port|listening_port)\s*[:=]\s*(\d{2,5})",
        r"\b(?:listening|listen|bound)\s+(?:on\s+)?(?:port\s+)?(\d{2,5})\b",
        r"--port(?:=|\s+)(\d{2,5})",
    )
    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            parsed = _parse_int(match)
            if parsed:
                ports.append(parsed)
    return ports


def _run_state_ports(vault: Path, runtime_id: str) -> list[int]:
    run_dir = vault / "runtime" / "lifecycle" / "run"
    if not run_dir.exists():
        return []
    runtime_token = runtime_id.replace("-", "").replace("_", "").lower()
    candidates: list[Path] = []
    try:
        children = list(run_dir.iterdir())
    except Exception:
        return []
    for path in children:
        if not path.is_file() or path.suffix.lower() not in _RUN_STATE_SUFFIXES:
            continue
        name_token = path.name.replace("-", "").replace("_", "").lower()
        if runtime_token in name_token:
            candidates.append(path)
    ports: list[int] = []
    for path in sorted(candidates, key=_run_state_sort_key, reverse=True)[:_RUN_STATE_MAX_FILES]:
        ports.extend(_ports_from_text(_read_bounded_text(path)))
    return ports


def _env_ports(runtime_id: str) -> list[int]:
    ports: list[int] = []
    for key in _ENV_PORT_KEYS.get(runtime_id, []):
        parsed = _parse_int(os.environ.get(key))
        if parsed:
            ports.append(parsed)
    return ports


def candidate_gateway_ports(vault_root: str | Path, runtime_id: str) -> list[int]:
    """Return explicit gateway candidate ports from env, config, run state, and fallbacks."""
    vault = Path(vault_root).resolve()
    runtime = _runtime_id(runtime_id)
    configured_ports = (
        _env_ports(runtime)
        + _registry_ports(vault, runtime)
        + _lifecycle_ports(vault, runtime)
        + _run_state_ports(vault, runtime)
    )
    fallback_ports = list(_FALLBACK_PORTS.get(runtime, [])) if (vault / "runtime" / "lifecycle").exists() else []
    return _dedupe_ports(configured_ports + fallback_ports)


def _read_runtime_heartbeat(vault: Path, bus_name: str) -> dict[str, Any]:
    sqlite_path = vault / "runtime" / "agent_bus" / "agent_bus.sqlite"
    if not sqlite_path.exists():
        return {
            "runtime": bus_name,
            "found": False,
            "last_seen": None,
            "elapsed_seconds": None,
            "status": "missing_bus_store",
        }
    try:
        conn = sqlite3.connect(f"file:{sqlite_path.as_posix()}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT runtime, last_seen, status FROM heartbeats "
                "WHERE runtime = ? ORDER BY last_seen DESC LIMIT 1",
                (bus_name,),
            ).fetchall()
        finally:
            conn.close()
        if rows:
            row = rows[0]
            last_seen = str(row["last_seen"] or "")
            elapsed = seconds_since(last_seen)
            return {
                "runtime": bus_name,
                "found": True,
                "last_seen": last_seen,
                "elapsed_seconds": round(elapsed, 1) if elapsed is not None else None,
                "status": str(row["status"] or ""),
            }
    except Exception as exc:
        return {
            "runtime": bus_name,
            "found": False,
            "last_seen": None,
            "elapsed_seconds": None,
            "status": "heartbeat_read_failed",
            "error": type(exc).__name__,
        }
    return {
        "runtime": bus_name,
        "found": False,
        "last_seen": None,
        "elapsed_seconds": None,
        "status": "no_heartbeat",
    }


def _probe_port(host: str, port: int, timeout_s: float = _PORT_PROBE_TIMEOUT_SECONDS) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return True
    except OSError:
        return False


def probe_gateway_ports(vault_root: str | Path, runtime_id: str) -> dict[str, Any]:
    """Fast TCP probe of explicitly declared gateway ports. Read-only."""
    ports = candidate_gateway_ports(vault_root, runtime_id)
    hosts = ["127.0.0.1", "localhost"]
    listening: dict[str, Any] | None = None
    for port in ports:
        for host in hosts:
            if _probe_port(host, port):
                listening = {"host": host, "port": port}
                break
        if listening:
            break
    return {
        "gateway_port_online": listening is not None,
        "gateway_port_listening": listening["port"] if listening else None,
        "gateway_host_listening": listening["host"] if listening else None,
        "gateway_ports_checked": ports,
        "gateway_hosts_checked": hosts,
    }


def _pid_alive(pid: int) -> bool:
    if os.name == "nt":
        try:
            process_query_limited_information = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(
                process_query_limited_information,
                False,
                int(pid),
            )
            if handle:
                ctypes.windll.kernel32.CloseHandle(handle)
                return True
            return False
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _pid_file_status(vault: Path, runtime_id: str) -> dict[str, Any]:
    pid_path = vault / "runtime" / "lifecycle" / "run" / f"{runtime_id}-chat-daemon.pid"
    if not pid_path.exists():
        return {
            "pid_file": str(pid_path),
            "pid": None,
            "pid_file_present": False,
            "pid_alive": False,
        }
    try:
        pid = int(pid_path.read_text(encoding="utf-8").strip())
    except Exception:
        return {
            "pid_file": str(pid_path),
            "pid": None,
            "pid_file_present": True,
            "pid_alive": False,
            "pid_read_error": True,
        }
    return {
        "pid_file": str(pid_path),
        "pid": pid,
        "pid_file_present": True,
        "pid_alive": _pid_alive(pid),
    }


def _empty_wsl_process_status(status: str = "not_checked") -> dict[str, Any]:
    return {
        "status": status,
        "process_alive": False,
        "pid": None,
        "command_preview": "",
    }


def _windows_no_window_creationflags() -> int:
    """Return Windows subprocess flags that prevent transient console windows."""
    if os.name != "nt":
        return 0
    return int(getattr(subprocess, "CREATE_NO_WINDOW", 0) or 0)


def _wsl_process_status(runtime_id: str) -> dict[str, Any]:
    """Best-effort WSL process probe for runtimes launched outside Windows PID files."""
    runtime = _runtime_id(runtime_id)
    if os.name != "nt" or runtime not in {"hermes", "openclaw"}:
        return _empty_wsl_process_status("unsupported")

    try:
        result = subprocess.run(
            ["wsl.exe", "--", "ps", "-eo", "pid=,args="],
            capture_output=True,
            text=True,
            timeout=_WSL_PROCESS_TIMEOUT_SECONDS,
            creationflags=_windows_no_window_creationflags(),
        )
    except Exception:
        return _empty_wsl_process_status("probe_failed")

    if result.returncode != 0:
        return _empty_wsl_process_status("probe_failed")

    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        lowered = line.lower()
        if not line:
            continue
        if runtime == "hermes":
            matched = "hermes" in lowered and "gateway" in lowered
        else:
            matched = "openclaw" in lowered
        if not matched:
            continue
        parts = line.split(maxsplit=1)
        pid = _parse_positive_int(parts[0]) if parts else None
        command = parts[1] if len(parts) > 1 else line
        return {
            "status": "process_found",
            "process_alive": True,
            "pid": pid,
            "command_preview": command[:180],
        }

    return _empty_wsl_process_status("process_not_found")


def _coordination_watch_status(vault: Path, runtime_id: str) -> dict[str, Any]:
    """Read coordination-watch state without trusting stale PID files as readiness."""
    state_path = vault / "runtime" / "lifecycle" / "run" / f"{runtime_id}-coordination-watch.json"
    if not state_path.exists():
        return {
            "state_file": str(state_path),
            "state_present": False,
            "pid": None,
            "pid_alive": False,
            "running": False,
            "stale_state": False,
            "status": "missing",
        }
    payload = _read_json(state_path)
    if not payload:
        return {
            "state_file": str(state_path),
            "state_present": True,
            "pid": None,
            "pid_alive": False,
            "running": False,
            "stale_state": True,
            "status": "invalid_or_unreadable",
        }
    pid = _parse_positive_int(payload.get("pid"))
    state_status = str(payload.get("status") or "").strip().lower()
    ended = bool(payload.get("ended_at") or state_status in {"done", "stopped", "failed", "error"})
    pid_alive = _pid_alive(pid) if pid and not ended else False
    running = bool(pid_alive and not ended)
    return {
        "state_file": str(state_path),
        "state_present": True,
        "pid": pid,
        "pid_alive": pid_alive,
        "running": running,
        "stale_state": bool(not running and not ended),
        "status": state_status or "unknown",
        "started_at": payload.get("started_at"),
        "ended_at": payload.get("ended_at"),
        "interval_seconds": payload.get("interval_seconds"),
        "cycles_run": payload.get("cycles_run"),
        "tasks_dispatched": payload.get("tasks_dispatched"),
        "tasks_escalated": payload.get("tasks_escalated"),
    }


def build_runtime_live_status(
    vault_root: str | Path,
    runtime_id: str,
    *,
    probe_wsl_processes: bool = False,
) -> dict[str, Any]:
    """Return a unified live-status model for a runtime adapter.

    `status == running` means some local liveness signal is present. `dispatch_ready`
    stays stricter and requires a fresh/recent Agent Bus heartbeat, so a WSL
    gateway can be shown as live while still asking for heartbeat repair.
    """
    vault = Path(vault_root).resolve()
    runtime = _runtime_id(runtime_id)
    bus_name = _RUNTIME_BUS_NAMES.get(runtime)
    recent_threshold = _lifecycle_recent_threshold(vault, runtime)
    heartbeat = _read_runtime_heartbeat(vault, bus_name) if bus_name else {
        "runtime": None,
        "found": False,
        "last_seen": None,
        "elapsed_seconds": None,
        "status": "not_bus_runtime",
    }
    freshness = heartbeat_freshness(heartbeat.get("elapsed_seconds"), recent_threshold_seconds=recent_threshold)
    heartbeat_online = freshness in {"fresh", "recent"}
    port_info = probe_gateway_ports(vault, runtime)
    pid_info = _pid_file_status(vault, runtime)
    coordination_watch = _coordination_watch_status(vault, runtime)

    gateway_online = bool(port_info.get("gateway_port_online"))
    pid_alive = bool(pid_info.get("pid_alive"))
    wsl_process = (
        _wsl_process_status(runtime)
        if probe_wsl_processes
        and (vault / "runtime" / "lifecycle").exists()
        and not (heartbeat_online or gateway_online or pid_alive)
        else _empty_wsl_process_status(
            "skipped" if not probe_wsl_processes else "not_checked"
        )
    )
    wsl_process_alive = bool(wsl_process.get("process_alive"))
    running = heartbeat_online or gateway_online or pid_alive or wsl_process_alive
    if heartbeat_online:
        status_source = "agent_bus_heartbeat"
    elif gateway_online:
        status_source = "gateway_port"
    elif pid_alive:
        status_source = "pid_file"
    elif wsl_process_alive:
        status_source = "wsl_process"
    else:
        status_source = "none"

    if heartbeat_online:
        coordination_state = "heartbeat_live"
    elif gateway_online:
        coordination_state = "gateway_live_heartbeat_required"
    elif wsl_process_alive:
        coordination_state = "wsl_process_live_heartbeat_required"
    elif heartbeat.get("found"):
        coordination_state = "heartbeat_stale"
    else:
        coordination_state = "heartbeat_missing"

    blockers: list[str] = []
    if not heartbeat_online and bus_name:
        blockers.append("agent_bus_heartbeat_not_fresh")
    if not gateway_online and candidate_gateway_ports(vault, runtime):
        blockers.append("gateway_port_not_listening_on_declared_candidates")
    if wsl_process_alive and not gateway_online:
        blockers.append("wsl_runtime_process_running_without_gateway_port")
    if coordination_watch.get("stale_state"):
        blockers.append("coordination_watch_state_stale")

    return {
        "ok": True,
        "surface": "studio_runtime_live_status",
        "model_version": MODEL_VERSION,
        "generated_at_utc": _now_utc(),
        "read_only": True,
        "runtime": runtime,
        "adapter_id": runtime,
        "bus_name": bus_name,
        "status": "running" if running else "not_running",
        "status_source": status_source,
        "coordination_state": coordination_state,
        "dispatch_ready": heartbeat_online,
        "runtime_can_receive_chat": heartbeat_online,
        "gateway_online": gateway_online,
        "gateway_port_online": gateway_online,
        "gateway_port_listening": port_info.get("gateway_port_listening"),
        "gateway_host_listening": port_info.get("gateway_host_listening"),
        "gateway_ports_checked": port_info.get("gateway_ports_checked") or [],
        "heartbeat_online": heartbeat_online,
        "heartbeat_freshness": freshness,
        "heartbeat": heartbeat,
        "recent_threshold_seconds": recent_threshold,
        "pid": pid_info.get("pid"),
        "pid_file": pid_info.get("pid_file"),
        "pid_file_present": pid_info.get("pid_file_present"),
        "pid_alive": pid_alive or wsl_process_alive,
        "wsl_process_alive": wsl_process_alive,
        "wsl_process": wsl_process,
        "wsl_process_probe_enabled": bool(probe_wsl_processes),
        "coordination_watch": coordination_watch,
        "coordination_watch_running": bool(coordination_watch.get("running")),
        "coordination_watch_state_stale": bool(coordination_watch.get("stale_state")),
        "blocked_reasons": blockers,
    }
