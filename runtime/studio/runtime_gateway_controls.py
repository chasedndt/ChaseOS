"""Studio runtime daemon/gateway controls.

This module is the operator-facing bridge between Studio buttons and the
already-declared Hermes/OpenClaw lifecycle records. It is intentionally narrow:
it can start/stop the selected runtime daemon or gateway, store a local
"launch with ChaseOS Studio" preference, and report live evidence. It does not
read secrets, dispatch Agent Bus tasks, call providers, or mutate canonical
vault state.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import ctypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from runtime.lifecycle.health_cli import load_lifecycle_record
from runtime.lifecycle.startup_surfaces import (
    execute_startup_surface_toggle,
    resolve_gateway_surface_config,
)
from runtime.lifecycle.hermes_gateway_config import (
    build_hermes_gateway_config_control_model,
    run_hermes_gateway_config_action,
)
from runtime.studio.runtime_live_status import build_runtime_live_status


MODEL_VERSION = "studio.runtime_gateway_controls.v1"
SURFACE_ID = "studio_runtime_gateway_controls"

RUNTIME_IDS = ("hermes", "openclaw")
COMPONENT_IDS = ("daemon", "gateway")
STARTUP_MODES = ("manual", "chaseos_start", "system_start")

DEFAULT_INTERVAL_SECONDS = 30
CHASEOS_START_RETRY_COOLDOWN_SECONDS = 120

_SENSITIVE_KEY_FRAGMENTS = (
    "api_key",
    "apikey",
    "secret",
    "token",
    "password",
    "credential",
    "cookie",
)


class RuntimeGatewayControlError(ValueError):
    """Raised when a runtime gateway control request is invalid."""


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_utc(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _launch_retry_cooldown_active(prefs: dict[str, Any]) -> bool:
    attempted = _parse_utc(prefs.get("last_launch_attempt_at_utc"))
    if attempted is None:
        return False
    elapsed = (datetime.now(timezone.utc) - attempted).total_seconds()
    return elapsed < CHASEOS_START_RETRY_COOLDOWN_SECONDS


def _normalize_runtime_id(runtime_id: str) -> str:
    runtime = str(runtime_id or "").strip().lower().replace("_", "-")
    if runtime == "open-claw":
        runtime = "openclaw"
    if runtime not in RUNTIME_IDS:
        raise RuntimeGatewayControlError(f"unsupported runtime: {runtime_id}")
    return runtime


def _normalize_component_id(component_id: str) -> str:
    component = str(component_id or "").strip().lower().replace("_", "-")
    if component not in COMPONENT_IDS:
        raise RuntimeGatewayControlError(f"unsupported component: {component_id}")
    return component


def _normalize_startup_mode(startup_mode: str) -> str:
    mode = str(startup_mode or "").strip().lower().replace("-", "_")
    if mode not in STARTUP_MODES:
        raise RuntimeGatewayControlError(f"unsupported startup mode: {startup_mode}")
    return mode


def _state_path(vault: Path) -> Path:
    return vault / "runtime" / "studio" / "state" / "runtime-gateway-controls.json"


def _event_log_path(vault: Path) -> Path:
    return vault / "runtime" / "lifecycle" / "run" / "studio-runtime-gateway-control-events.jsonl"


def _pid_path(vault: Path, runtime_id: str) -> Path:
    return vault / "runtime" / "lifecycle" / "run" / f"{runtime_id}-chat-daemon.pid"


def _default_state() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "updated_at_utc": None,
        "runtimes": {
            runtime_id: {
                component_id: {
                    "startup_mode": "manual",
                    "launch_on_chaseos_start": False,
                    "last_launch_attempt_at_utc": None,
                    "last_launch_result": None,
                }
                for component_id in COMPONENT_IDS
            }
            for runtime_id in RUNTIME_IDS
        },
    }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_runtime_gateway_preferences(vault_root: str | Path) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    state = _default_state()
    persisted = _read_json(_state_path(vault))
    runtimes = persisted.get("runtimes") if isinstance(persisted.get("runtimes"), dict) else {}
    for runtime_id in RUNTIME_IDS:
        runtime_prefs = runtimes.get(runtime_id) if isinstance(runtimes.get(runtime_id), dict) else {}
        for component_id in COMPONENT_IDS:
            component_prefs = (
                runtime_prefs.get(component_id)
                if isinstance(runtime_prefs.get(component_id), dict)
                else {}
            )
            mode = str(component_prefs.get("startup_mode") or "manual").strip().lower()
            if mode not in STARTUP_MODES:
                mode = "manual"
            state["runtimes"][runtime_id][component_id].update(
                {
                    "startup_mode": mode,
                    "launch_on_chaseos_start": bool(
                        component_prefs.get("launch_on_chaseos_start")
                        or mode == "chaseos_start"
                    ),
                    "last_launch_attempt_at_utc": component_prefs.get(
                        "last_launch_attempt_at_utc"
                    ),
                    "last_launch_result": component_prefs.get("last_launch_result"),
                    "approval_record": component_prefs.get("approval_record")
                    if isinstance(component_prefs.get("approval_record"), dict)
                    else None,
                }
            )
    state["updated_at_utc"] = persisted.get("updated_at_utc")
    state["path"] = str(_state_path(vault))
    return state


def _write_preferences(vault: Path, state: dict[str, Any]) -> None:
    path = _state_path(vault)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def _append_event(vault: Path, payload: dict[str, Any]) -> None:
    path = _event_log_path(vault)
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "event_at_utc": _now_utc(),
        "surface": SURFACE_ID,
        **payload,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def _contains_sensitive_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower().replace("-", "_")
            if any(fragment in lowered for fragment in _SENSITIVE_KEY_FRAGMENTS):
                return True
            if _contains_sensitive_key(item):
                return True
    if isinstance(value, list):
        return any(_contains_sensitive_key(item) for item in value)
    return False


def _gateway_surface(record: dict[str, Any]) -> dict[str, Any]:
    surfaces = record.get("startup_surfaces") if isinstance(record.get("startup_surfaces"), dict) else {}
    gateway = surfaces.get("gateway") if isinstance(surfaces.get("gateway"), dict) else {}
    return gateway


def _resolved_gateway_surface(vault: Path, record: dict[str, Any]) -> dict[str, Any]:
    return resolve_gateway_surface_config(_gateway_surface(record), vault)


def _gateway_record(vault: Path, runtime_id: str) -> dict[str, Any]:
    return load_lifecycle_record(runtime_id, vault)


def _gateway_target_path(vault: Path, runtime_id: str) -> str | None:
    record = _gateway_record(vault, runtime_id)
    target = _resolved_gateway_surface(vault, record).get("target_path")
    target_text = str(target or "").strip()
    return target_text or None


def _startup_launcher_path(vault: Path, runtime_id: str) -> str | None:
    record = _gateway_record(vault, runtime_id)
    launcher = _resolved_gateway_surface(vault, record).get("launcher_path")
    launcher_text = str(launcher or "").strip()
    return launcher_text or None


def _system_start_registered(vault: Path, runtime_id: str) -> bool:
    launcher = _startup_launcher_path(vault, runtime_id)
    return bool(launcher and Path(launcher).exists())


def _popen(
    args: list[str],
    *,
    cwd: Path | None = None,
    visible: bool = False,
) -> subprocess.Popen:
    creationflags = 0
    if os.name == "nt":
        if not visible:
            creationflags |= getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return subprocess.Popen(  # noqa: S603 - args are built from lifecycle/runtime ids.
        args,
        cwd=str(cwd) if cwd else None,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )


def _run_process_probe(args: list[str], timeout_seconds: float = 2.0) -> subprocess.CompletedProcess:
    creationflags = 0
    if os.name == "nt":
        creationflags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
        creationflags=creationflags,
    )


def _powershell_process_query_groups(pattern_groups: list[list[str]]) -> list[dict[str, Any]]:
    if os.name != "nt":
        return []
    escaped_groups = [
        [pattern.replace("'", "''") for pattern in group if pattern]
        for group in pattern_groups
        if group
    ]
    if not escaped_groups:
        return []
    group_exprs = []
    for group in escaped_groups:
        group_exprs.append("(" + " -and ".join([f"$cmd -like '*{pattern}*'" for pattern in group]) + ")")
    filter_expr = " -or ".join(group_exprs)
    script = (
        "Get-CimInstance Win32_Process | ForEach-Object { "
        "$cmd = [string]$_.CommandLine; "
        f"if ($_.ProcessId -ne $PID -and $cmd -and ({filter_expr})) "
        "{ [pscustomobject]@{ProcessId=$_.ProcessId;Name=$_.Name;CommandLine=$cmd} } "
        "} | ConvertTo-Json -Compress"
    )
    try:
        completed = _run_process_probe(
            ["powershell.exe", "-NoProfile", "-Command", script],
            timeout_seconds=4.0,
        )
    except Exception:
        return []
    if completed.returncode != 0 or not completed.stdout.strip():
        return []
    try:
        parsed = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return []
    rows = parsed if isinstance(parsed, list) else [parsed]
    result: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            pid = int(row.get("ProcessId"))
        except Exception:
            continue
        result.append(
            {
                "pid": pid,
                "name": str(row.get("Name") or ""),
                "command": str(row.get("CommandLine") or "")[:500],
            }
        )
    return result[:20]


def _powershell_process_query(patterns: list[str]) -> list[dict[str, Any]]:
    return _powershell_process_query_groups([[pattern] for pattern in patterns if pattern])


def _hermes_wsl_processes(vault: Path) -> list[dict[str, Any]]:
    try:
        record = _gateway_record(vault, "hermes")
    except Exception:
        return []
    gateway = _resolved_gateway_surface(vault, record)
    distro = str(gateway.get("wsl_distro") or "Ubuntu").strip()
    user = str(gateway.get("wsl_user") or "").strip()
    if not distro:
        return []
    args = ["wsl.exe", "-d", distro]
    if user:
        args.extend(["-u", user])
    args.extend(["--", "bash", "-lc", "ps -ef | grep -E '[h]ermes gateway run|[h]ermes.*gateway'"])
    try:
        completed = _run_process_probe(args, timeout_seconds=3.0)
    except Exception:
        return []
    if completed.returncode != 0:
        return []
    processes: list[dict[str, Any]] = []
    for line in completed.stdout.splitlines():
        stripped = line.strip()
        if stripped:
            processes.append({"pid": None, "name": "wsl-hermes", "command": stripped[:500]})
    return processes[:20]


def _gateway_process_patterns(vault: Path, runtime_id: str) -> list[str]:
    target = _gateway_target_path(vault, runtime_id) or ""
    if runtime_id == "hermes":
        return [target, "hermes gateway run", "HERMES_SERVICE_KIND=gateway"]
    if runtime_id == "openclaw":
        return [target, "openclaw gateway", "openclaw\\dist", "OpenClaw Gateway"]
    return [target]


def _gateway_process_evidence(vault: Path, runtime_id: str) -> dict[str, Any]:
    windows_processes = _powershell_process_query(_gateway_process_patterns(vault, runtime_id))
    wsl_processes = _hermes_wsl_processes(vault) if runtime_id == "hermes" else []
    processes = windows_processes + wsl_processes
    return {
        "process_probe_available": os.name == "nt",
        "process_count": len(processes),
        "processes": processes,
        "process_live": bool(processes),
    }


def _daemon_process_groups(runtime_id: str) -> list[list[str]]:
    if runtime_id == "hermes":
        return [
            ["hermes-daemon-loop.cmd"],
            ["runtime.cli.main runtime daemon", "--runtime hermes"],
        ]
    if runtime_id == "openclaw":
        return [
            ["openclaw-daemon-loop.cmd"],
            ["runtime.cli.main runtime daemon", "--runtime openclaw"],
        ]
    return [["runtime.cli.main runtime daemon", f"--runtime {runtime_id}"]]


def _daemon_process_evidence(runtime_id: str) -> dict[str, Any]:
    processes = _powershell_process_query_groups(_daemon_process_groups(runtime_id))
    return {
        "process_probe_available": os.name == "nt",
        "process_count": len(processes),
        "processes": processes,
        "process_live": bool(processes),
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


def _component_status(
    vault: Path,
    runtime_id: str,
    component_id: str,
    *,
    probe_processes: bool = True,
) -> dict[str, Any]:
    live_status = build_runtime_live_status(
        vault,
        runtime_id,
        probe_wsl_processes=probe_processes,
    )
    if component_id == "daemon":
        daemon_evidence = (
            _daemon_process_evidence(runtime_id)
            if probe_processes
            else {
                "process_probe_available": False,
                "process_count": 0,
                "processes": [],
                "process_live": False,
                "skipped": True,
            }
        )
        coordination_watch = live_status.get("coordination_watch") or {}
        coordination_pid = coordination_watch.get("pid") if isinstance(coordination_watch, dict) else None
        process_pid = None
        processes = daemon_evidence.get("processes") if isinstance(daemon_evidence.get("processes"), list) else []
        if processes:
            process_pid = processes[0].get("pid")
        pid = coordination_pid or live_status.get("pid") or process_pid
        coordination_running = bool(live_status.get("coordination_watch_running"))
        heartbeat_online = bool(live_status.get("heartbeat_online"))
        pid_alive = bool(live_status.get("pid_alive"))
        process_live = bool(daemon_evidence.get("process_live"))
        running = coordination_running or pid_alive or process_live
        return {
            "component_id": component_id,
            "status": "running" if running else "not_running",
            "running": running,
            "status_source": (
                "coordination_watch"
                if coordination_running
                else "daemon_process"
                if process_live
                else "pid_file"
                if pid_alive
                else "none"
            ),
            "pid": pid,
            "coordination_watch_pid": coordination_pid,
            "process_evidence": daemon_evidence,
            "pid_file": live_status.get("pid_file"),
            "pid_file_pid": live_status.get("pid"),
            "heartbeat_online": heartbeat_online,
            "heartbeat_freshness": live_status.get("heartbeat_freshness"),
            "coordination_watch_running": coordination_running,
            "blocked_reasons": list(live_status.get("blocked_reasons") or []),
        }

    gateway_evidence = (
        _gateway_process_evidence(vault, runtime_id)
        if probe_processes
        else {
            "process_probe_available": False,
            "process_count": 0,
            "processes": [],
            "process_live": False,
            "skipped": True,
        }
    )
    port_online = bool(live_status.get("gateway_port_online"))
    process_live = bool(gateway_evidence.get("process_live"))
    running = port_online or process_live
    return {
        "component_id": component_id,
        "status": "running" if running else "not_running",
        "running": running,
        "status_source": (
            "gateway_process"
            if process_live
            else "gateway_port"
            if port_online
            else "none"
        ),
        "gateway_port_online": port_online,
        "gateway_port_listening": live_status.get("gateway_port_listening"),
        "gateway_ports_checked": live_status.get("gateway_ports_checked") or [],
        "process_evidence": gateway_evidence,
        "target_path": _gateway_target_path(vault, runtime_id),
        "system_start_registered": _system_start_registered(vault, runtime_id),
    }


def _component_label(runtime_id: str, component_id: str) -> str:
    runtime_label = "OpenClaw" if runtime_id == "openclaw" else "Hermes"
    component_label = "Gateway" if component_id == "gateway" else "Daemon"
    return f"{runtime_label} {component_label}"


def _daemon_command(vault: Path, runtime_id: str) -> list[str]:
    python_exe = vault / ".venv" / "Scripts" / "python.exe"
    executable = str(python_exe) if python_exe.exists() else sys.executable
    return [
        executable,
        "-m",
        "runtime.cli.main",
        "runtime",
        "daemon",
        "--runtime",
        runtime_id,
        "--daemon-interval",
        str(DEFAULT_INTERVAL_SECONDS),
        "--vault-root",
        str(vault),
    ]


def _gateway_command(vault: Path, runtime_id: str) -> list[str]:
    target = _gateway_target_path(vault, runtime_id)
    if not target:
        raise RuntimeGatewayControlError(f"{runtime_id} gateway target_path is not declared")
    if not Path(target).exists():
        raise RuntimeGatewayControlError(f"{runtime_id} gateway launcher is missing: {target}")
    # Use /c rather than /k so Studio never leaves a user-visible command shell
    # open for gateway launches. The process is still tracked/stopped through
    # the runtime gateway controls.
    return ["cmd.exe", "/d", "/c", target] if os.name == "nt" else [target]


def launch_runtime_component(
    vault_root: str | Path,
    runtime_id: str,
    component_id: str,
    *,
    visible: bool = False,
    dry_run: bool = False,
    requested_by: str = "operator",
    popen: Callable[..., subprocess.Popen] | None = None,
) -> dict[str, Any]:
    """Launch one runtime component from Studio.

    `dry_run=True` returns the exact command without spawning anything.
    """

    vault = Path(vault_root).resolve()
    runtime = _normalize_runtime_id(runtime_id)
    component = _normalize_component_id(component_id)
    before = _component_status(vault, runtime, component)
    if component == "daemon":
        command = _daemon_command(vault, runtime)
    else:
        command = _gateway_command(vault, runtime)
    approval_record = {
        "approval_kind": "operator_initiated_runtime_launch",
        "approval_required": component == "gateway",
        "approval_recorded": bool(component == "gateway" and not dry_run),
        "approval_scope": "runtime_gateway_process_launch" if component == "gateway" else "runtime_daemon_process_launch",
        "requested_by": requested_by,
        "runtime_id": runtime,
        "component_id": component,
        "starts_wsl": bool(runtime == "hermes" and component == "gateway"),
        "recorded_at_utc": _now_utc() if component == "gateway" and not dry_run else None,
    }

    if dry_run:
        return {
            "ok": True,
            "surface": SURFACE_ID,
            "action": "launch_component",
            "dry_run": True,
            "runtime_id": runtime,
            "component_id": component,
            "command": command,
            "before": before,
            "approval_required": approval_record["approval_required"],
            "approval_recorded": False,
            "approval_record": approval_record,
            "writes_runtime_lifecycle": False,
            "starts_process": False,
        }

    if before.get("running"):
        return {
            "ok": True,
            "surface": SURFACE_ID,
            "action": "launch_component",
            "status": "already_running",
            "runtime_id": runtime,
            "component_id": component,
            "before": before,
            "after": before,
            "approval_required": approval_record["approval_required"],
            "approval_recorded": False,
            "approval_record": approval_record,
            "starts_process": False,
        }

    launcher = popen or _popen
    process = launcher(command, cwd=vault, visible=visible)
    if component == "daemon":
        path = _pid_path(vault, runtime)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(process.pid), encoding="utf-8")

    event = {
        "action": "launch_component",
        "runtime_id": runtime,
        "component_id": component,
        "pid": int(process.pid),
        "command": command,
        "starts_process": True,
        "writes_runtime_lifecycle": component == "daemon",
        "approval_record": approval_record,
    }
    _append_event(vault, event)

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "action": "launch_component",
        "status": "started",
        "runtime_id": runtime,
        "component_id": component,
        "pid": int(process.pid),
        "command": command,
        "before": before,
        "approval_required": approval_record["approval_required"],
        "approval_recorded": approval_record["approval_recorded"],
        "approval_record": approval_record,
        "starts_process": True,
        "writes_runtime_lifecycle": component == "daemon",
        "event_log": str(_event_log_path(vault)),
    }


def _stop_windows_process_groups(pattern_groups: list[list[str]]) -> dict[str, Any]:
    processes = _powershell_process_query_groups(pattern_groups)
    pids = [str(item["pid"]) for item in processes if item.get("pid")]
    if not pids:
        return {"matched_count": 0, "stopped_count": 0, "pids": []}
    script = (
        "$pids = @("
        + ",".join(pids)
        + "); foreach ($pidValue in $pids) { "
        "Stop-Process -Id $pidValue -Force -ErrorAction SilentlyContinue }"
    )
    completed = _run_process_probe(
        ["powershell.exe", "-NoProfile", "-Command", script],
        timeout_seconds=4.0,
    )
    return {
        "matched_count": len(pids),
        "stopped_count": len(pids) if completed.returncode == 0 else 0,
        "pids": [int(pid) for pid in pids],
        "returncode": completed.returncode,
    }


def _stop_windows_processes(patterns: list[str]) -> dict[str, Any]:
    return _stop_windows_process_groups([[pattern] for pattern in patterns if pattern])


def _stop_hermes_wsl_gateway(vault: Path) -> dict[str, Any]:
    try:
        record = _gateway_record(vault, "hermes")
    except Exception:
        return {"attempted": False, "returncode": None}
    gateway = _resolved_gateway_surface(vault, record)
    distro = str(gateway.get("wsl_distro") or "Ubuntu").strip()
    user = str(gateway.get("wsl_user") or "").strip()
    if not distro:
        return {"attempted": False, "returncode": None}
    args = ["wsl.exe", "-d", distro]
    if user:
        args.extend(["-u", user])
    args.extend(["--", "bash", "-lc", "pkill -f 'hermes gateway run' || true"])
    try:
        completed = _run_process_probe(args, timeout_seconds=4.0)
    except Exception as exc:
        return {"attempted": True, "returncode": None, "error": type(exc).__name__}
    return {"attempted": True, "returncode": completed.returncode}


def stop_runtime_component(
    vault_root: str | Path,
    runtime_id: str,
    component_id: str,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    runtime = _normalize_runtime_id(runtime_id)
    component = _normalize_component_id(component_id)
    before = _component_status(vault, runtime, component)
    if dry_run:
        return {
            "ok": True,
            "surface": SURFACE_ID,
            "action": "stop_component",
            "dry_run": True,
            "runtime_id": runtime,
            "component_id": component,
            "before": before,
            "stops_process": False,
        }

    stop_result: dict[str, Any] = {"stopped_count": 0}
    if component == "daemon":
        stop_result = _stop_windows_process_groups(_daemon_process_groups(runtime))
        if not int(stop_result.get("stopped_count") or 0) and before.get("pid"):
            pid = before.get("pid")
            try:
                os.kill(int(pid), signal.SIGTERM)
                stop_result = {"stopped_count": 1, "pids": [int(pid)]}
            except OSError as exc:
                stop_result = {"stopped_count": 0, "pids": [int(pid)], "error": str(exc)}
    else:
        stop_result = _stop_windows_processes(_gateway_process_patterns(vault, runtime))
        if runtime == "hermes":
            stop_result["wsl_gateway_stop"] = _stop_hermes_wsl_gateway(vault)

    _append_event(
        vault,
        {
            "action": "stop_component",
            "runtime_id": runtime,
            "component_id": component,
            "stop_result": stop_result,
            "stops_process": True,
        },
    )
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "action": "stop_component",
        "status": "stopped" if int(stop_result.get("stopped_count") or 0) else "no_matching_process",
        "runtime_id": runtime,
        "component_id": component,
        "before": before,
        "stop_result": stop_result,
        "stops_process": True,
        "event_log": str(_event_log_path(vault)),
    }


def _toggle_gateway_system_start(vault: Path, runtime_id: str, enable: bool) -> dict[str, Any]:
    intent = "enable" if enable else "disable"
    delegated = execute_startup_surface_toggle(
        runtime_id,
        "gateway",
        intent,
        confirm=True,
        requested_by="studio-runtime-gateway-controls",
    )
    return {
        "action": "gateway-system-start-toggle",
        "runtime_id": runtime_id,
        "intent": intent,
        "launcher_path": delegated.get("execution", {}).get("launcher_path"),
        "target_path": delegated.get("execution", {}).get("target_path"),
        "launcher_present_after": delegated.get("after_state") == "registered",
        "actions": delegated.get("execution", {}).get("actions") or [],
        "approval_required": delegated.get("approval_required"),
        "approval_recorded": delegated.get("approval_recorded"),
        "approval_record": delegated.get("approval_record"),
        "delegated_lifecycle_toggle": delegated,
    }


def set_runtime_component_startup_mode(
    vault_root: str | Path,
    runtime_id: str,
    component_id: str,
    startup_mode: str,
    *,
    apply_system_start: bool = False,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    runtime = _normalize_runtime_id(runtime_id)
    component = _normalize_component_id(component_id)
    mode = _normalize_startup_mode(startup_mode)
    if mode == "system_start" and component != "gateway":
        raise RuntimeGatewayControlError("system_start mode is only supported for gateway launchers")

    state = load_runtime_gateway_preferences(vault)
    state["updated_at_utc"] = _now_utc()
    component_prefs = state["runtimes"][runtime][component]
    approval_record = {
        "approval_kind": "startup_mode_operator_selection",
        "approval_required": mode in {"chaseos_start", "system_start"},
        "approval_recorded": mode in {"chaseos_start", "system_start"},
        "approval_scope": "runtime_gateway_startup_mode" if component == "gateway" else "runtime_component_startup_mode",
        "runtime_id": runtime,
        "component_id": component,
        "startup_mode": mode,
        "starts_wsl": bool(runtime == "hermes" and component == "gateway" and mode in {"chaseos_start", "system_start"}),
        "recorded_at_utc": _now_utc() if mode in {"chaseos_start", "system_start"} else None,
    }
    component_prefs["startup_mode"] = mode
    component_prefs["launch_on_chaseos_start"] = mode == "chaseos_start"
    component_prefs["last_launch_result"] = "mode_updated"
    component_prefs["approval_record"] = approval_record if approval_record["approval_recorded"] else None
    _write_preferences(vault, state)

    system_start_action: dict[str, Any] | None = None
    if apply_system_start and component == "gateway":
        if mode == "system_start":
            system_start_action = _toggle_gateway_system_start(vault, runtime, True)
        elif mode in {"manual", "chaseos_start"}:
            system_start_action = _toggle_gateway_system_start(vault, runtime, False)

    _append_event(
        vault,
        {
            "action": "set_startup_mode",
            "runtime_id": runtime,
            "component_id": component,
            "startup_mode": mode,
            "launch_on_chaseos_start": mode == "chaseos_start",
            "apply_system_start": apply_system_start,
            "approval_required": approval_record["approval_required"],
            "approval_recorded": approval_record["approval_recorded"],
            "approval_record": approval_record,
        },
    )
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "action": "set_startup_mode",
        "runtime_id": runtime,
        "component_id": component,
        "startup_mode": mode,
        "launch_on_chaseos_start": mode == "chaseos_start",
        "preferences_path": str(_state_path(vault)),
        "system_start_action": system_start_action,
        "approval_required": approval_record["approval_required"],
        "approval_recorded": approval_record["approval_recorded"],
        "approval_record": approval_record,
        "writes_runtime_lifecycle": True,
        "writes_host_startup": bool(system_start_action),
    }


def apply_chaseos_start_preferences(
    vault_root: str | Path,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    state = load_runtime_gateway_preferences(vault)
    launches: list[dict[str, Any]] = []
    for runtime_id in RUNTIME_IDS:
        for component_id in COMPONENT_IDS:
            prefs = state["runtimes"][runtime_id][component_id]
            if prefs.get("startup_mode") != "chaseos_start":
                continue
            if not dry_run and _launch_retry_cooldown_active(prefs):
                launches.append(
                    {
                        "ok": True,
                        "surface": SURFACE_ID,
                        "action": "launch_component",
                        "status": "recent_launch_attempt_skipped",
                        "runtime_id": runtime_id,
                        "component_id": component_id,
                        "last_launch_attempt_at_utc": prefs.get("last_launch_attempt_at_utc"),
                        "retry_cooldown_seconds": CHASEOS_START_RETRY_COOLDOWN_SECONDS,
                        "starts_process": False,
                    }
                )
                continue
            result = launch_runtime_component(
                vault,
                runtime_id,
                component_id,
                # ChaseOS-start is an app lifecycle action, not an operator-clicked
                # debug launch. Keep it headless so opening Chat/Studio pages cannot
                # spawn visible WSL/cmd windows on every startup retry. Manual
                # Settings button launches still default to visible=True.
                visible=False,
                dry_run=dry_run,
            )
            launches.append(result)
            prefs["last_launch_attempt_at_utc"] = _now_utc()
            prefs["last_launch_result"] = result.get("status") or (
                "dry_run" if dry_run else "unknown"
            )
    if launches and not dry_run:
        state["updated_at_utc"] = _now_utc()
        _write_preferences(vault, state)
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "action": "apply_chaseos_start_preferences",
        "dry_run": dry_run,
        "launch_count": len(launches),
        "launches": launches,
        "preferences_path": str(_state_path(vault)),
        "starts_process": any(bool(item.get("starts_process")) for item in launches) and not dry_run,
    }


def build_hermes_gateway_config_controls_model(
    vault_root: str | Path,
    *,
    probe_wsl: bool = False,
) -> dict[str, Any]:
    """Return redacted Hermes private gateway config control state for Studio."""

    return build_hermes_gateway_config_control_model(vault_root, probe_wsl=probe_wsl)


def apply_hermes_gateway_config_control(
    vault_root: str | Path,
    *,
    action: str = "add_chaseos_operator",
    allowed_users: str | None = None,
    dry_run: bool = False,
    requested_by: str = "studio-runtime-gateway-controls",
) -> dict[str, Any]:
    """Apply a redacted, backup-first Hermes gateway config button action."""

    normalized = str(action or "").strip().lower().replace("-", "_")
    if normalized in {"check", "check_status", "status"}:
        return run_hermes_gateway_config_action(
            "status",
            vault_root=vault_root,
            requested_by=requested_by,
        )
    if normalized in {"add_chaseos_operator", "add_operator", "operator"}:
        return run_hermes_gateway_config_action(
            "apply",
            vault_root=vault_root,
            use_chaseos_operator=True,
            confirm=not dry_run,
            dry_run=dry_run,
            requested_by=requested_by,
        )
    if normalized in {"set_gateway_allowed_users", "set_allowed_users", "allowed_users"}:
        return run_hermes_gateway_config_action(
            "apply",
            vault_root=vault_root,
            allowed_users=allowed_users,
            confirm=not dry_run,
            dry_run=dry_run,
            requested_by=requested_by,
        )
    raise RuntimeGatewayControlError(f"unsupported Hermes gateway config action: {action}")


def build_runtime_gateway_controls_model(
    vault_root: str | Path,
    *,
    probe_processes: bool = True,
) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    preferences = load_runtime_gateway_preferences(vault)
    runtime_cards: list[dict[str, Any]] = []
    for runtime_id in RUNTIME_IDS:
        try:
            record = load_lifecycle_record(runtime_id, vault)
        except Exception as exc:
            runtime_cards.append(
                {
                    "runtime_id": runtime_id,
                    "runtime_name": runtime_id,
                    "status": "error",
                    "error": str(exc),
                    "components": [],
                }
            )
            continue
        runtime_name = str((record.get("coordination_watch") or {}).get("runtime_name") or runtime_id)
        components: list[dict[str, Any]] = []
        for component_id in COMPONENT_IDS:
            prefs = preferences["runtimes"][runtime_id][component_id]
            status = _component_status(
                vault,
                runtime_id,
                component_id,
                probe_processes=probe_processes,
            )
            components.append(
                {
                    "runtime_id": runtime_id,
                    "runtime_name": runtime_name,
                    "component_id": component_id,
                    "component_label": _component_label(runtime_id, component_id),
                    "status": status,
                    "startup_mode": prefs.get("startup_mode") or "manual",
                    "launch_on_chaseos_start": bool(prefs.get("launch_on_chaseos_start")),
                    "approval_record": prefs.get("approval_record"),
                    "system_start_registered": _system_start_registered(vault, runtime_id)
                    if component_id == "gateway"
                    else False,
                    "startup_modes": list(STARTUP_MODES)
                    if component_id == "gateway"
                    else ["manual", "chaseos_start"],
                    "actions": {
                        "launch": f"StudioAPI.launch_runtime_component({runtime_id}, {component_id})",
                        "stop": f"StudioAPI.stop_runtime_component({runtime_id}, {component_id})",
                        "set_mode": f"StudioAPI.set_runtime_component_startup_mode({runtime_id}, {component_id}, <mode>)",
                    },
                }
            )
        runtime_cards.append(
            {
                "runtime_id": runtime_id,
                "runtime_name": runtime_name,
                "platform": record.get("platform"),
                "lifecycle_mode": record.get("lifecycle_mode"),
                "components": components,
            }
        )

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "runtime_count": len(runtime_cards),
        "component_count": sum(len(card.get("components") or []) for card in runtime_cards),
        "runtimes": runtime_cards,
        "preferences": preferences,
        "hermes_gateway_config": build_hermes_gateway_config_controls_model(vault, probe_wsl=False),
        "preferences_path": str(_state_path(vault)),
        "event_log": str(_event_log_path(vault)),
        "authority": {
            "read_only": False,
            "operator_initiated_only": True,
            "starts_runtimes": True,
            "stops_runtimes": True,
            "starts_gateways": True,
            "stops_gateways": True,
            "writes_runtime_lifecycle": True,
            "writes_studio_preferences": True,
            "writes_host_startup": True,
            "writes_private_hermes_gateway_config": True,
            "approval_execution_allowed": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "canonical_mutation_allowed": False,
            "shows_secret_values": False,
            "shows_raw_credentials": False,
        },
        "security": {
            "secret_values_included": False,
            "raw_credentials_included": False,
            "sensitive_key_scan_passed": not _contains_sensitive_key(runtime_cards),
        },
    }
