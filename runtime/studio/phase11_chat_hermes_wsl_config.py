"""Phase 11 Chat — Hermes WSL connection config and startup guide.

Hermes runs in WSL Ubuntu on this Windows machine. The Agent Bus is a shared
SQLite file accessible from both Windows and WSL via the filesystem mount:

  Windows:  C:\\Users\\chaseos\\Documents\\chaseos_obsidian\\runtime\\agent_bus\\agent_bus.sqlite
  WSL:      <VAULT_ROOT>/runtime/agent_bus/agent_bus.sqlite

When Studio (Windows) writes an Agent Bus task, Hermes (WSL) picks it up via its
polling loop (`hermes_watch.py`). No additional network configuration is needed.

This module exposes:
  - Connection status check (heartbeat + recent task evidence)
  - Startup instructions for the managed Hermes gateway and WSL fallback loop
  - Credential readiness for Hermes' WSL environment (ANTHROPIC_API_KEY)
  - Verification that the vault path is correct in WSL
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODEL_VERSION = "studio.phase11_chat_hermes_wsl_config.v1"
SURFACE_ID = "phase11_chat_hermes_wsl_config"

# The WSL mount path for the vault root (Windows C: drive → /mnt/c/ in WSL)
_WSL_VAULT_PATH = "<VAULT_ROOT>"
_WINDOWS_VAULT_PATH = "C:\\Users\\chaseos\\Documents\\chaseos_obsidian"

_HERMES_STARTUP_COMMANDS = {
    "run_once": (
        f"cd {_WSL_VAULT_PATH} && "
        "source .venv/bin/activate && "
        f"python -m runtime.cli.main run hermes_watch --vault {_WSL_VAULT_PATH}"
    ),
    "run_loop_10s": (
        f"cd {_WSL_VAULT_PATH} && "
        "source .venv/bin/activate && "
        "python -c \""
        "from runtime.workflows.hermes_watch import run_hermes_watch; "
        f"run_hermes_watch({{'interval_seconds': 10, 'max_tasks_per_cycle': 5}}, '{_WSL_VAULT_PATH}')"
        "\""
    ),
    "set_anthropic_key": "export ANTHROPIC_API_KEY=test-key-ant-your-key-here  # add to ~/.bashrc for persistence",
    "verify_key": "echo $ANTHROPIC_API_KEY | wc -c  # should be > 1; never echo the actual value",
    "managed_gateway": "python -m runtime.cli.main runtime startup-surface-toggle --runtime hermes --surface gateway --intent enable --confirm",
    "wsl_warmup": f"wsl -d Ubuntu -u chaseos -- bash -lc 'cd {_WSL_VAULT_PATH} && true'",
    "wsl_startup": f"wsl -d Ubuntu -u chaseos -- bash -lc 'cd {_WSL_VAULT_PATH} && exec <WSL_HOME>/.local/bin/hermes gateway run'",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _check_agent_bus_exists(vault: Path) -> bool:
    bus_path = vault / "runtime" / "agent_bus" / "agent_bus.sqlite"
    return bus_path.exists()


def _get_hermes_heartbeat(vault: Path) -> dict[str, Any] | None:
    try:
        from runtime.agent_bus.bus import list_heartbeats
        beats = list_heartbeats(vault, runtime="Hermes")
        if beats and isinstance(beats[0], dict):
            return beats[0]
    except Exception:
        pass
    return None


def _get_recent_hermes_tasks(vault: Path, limit: int = 5) -> list[dict[str, Any]]:
    try:
        from runtime.agent_bus.bus import list_tasks
        tasks = list_tasks(vault, recipient="Hermes") or []
        return [
            {
                "task_id": t.get("task_id"),
                "status": t.get("status"),
                "task_type": t.get("task_type"),
                "created_at": t.get("created_at"),
                "updated_at": t.get("updated_at"),
            }
            for t in tasks[:limit]
        ]
    except Exception:
        return []


def get_hermes_wsl_connection_status(
    vault_root: str | Path,
) -> dict[str, Any]:
    """Return Hermes WSL connection status and startup guide.

    Read-only. Does not start Hermes, does not write to Agent Bus.
    """
    vault = Path(vault_root).resolve()

    bus_exists = _check_agent_bus_exists(vault)
    heartbeat = _get_hermes_heartbeat(vault) if bus_exists else None
    recent_tasks = _get_recent_hermes_tasks(vault) if bus_exists else []

    hb_status = heartbeat.get("status") if heartbeat else None
    hb_updated = (heartbeat.get("updated_at") or heartbeat.get("last_seen")) if heartbeat else None
    hermes_seen = heartbeat is not None

    # Completed/active task evidence counts as Hermes having been active
    active_evidence = any(
        t.get("status") in {"done", "completed", "in_progress", "claimed"}
        for t in recent_tasks
    )

    connection_state: str
    if hermes_seen and hb_status in ("idle", "busy"):
        connection_state = "LIVE"
    elif hermes_seen:
        connection_state = "HEARTBEAT_PRESENT"
    elif active_evidence:
        connection_state = "TASK_EVIDENCE_ONLY"
    elif bus_exists:
        connection_state = "BUS_EXISTS_NO_HEARTBEAT"
    else:
        connection_state = "BUS_NOT_INITIALIZED"

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "connection_state": connection_state,
        "hermes_live": connection_state == "LIVE",
        "hermes_heartbeat_found": hermes_seen,
        "hermes_heartbeat_status": hb_status,
        "hermes_last_seen_utc": hb_updated,
        "agent_bus_exists": bus_exists,
        "recent_task_count": len(recent_tasks),
        "recent_tasks": recent_tasks,
        "active_task_evidence": active_evidence,
        "wsl_configuration": {
            "wsl_vault_path": _WSL_VAULT_PATH,
            "windows_vault_path": _WINDOWS_VAULT_PATH,
            "shared_bus_file": "runtime/agent_bus/agent_bus.sqlite",
            "shared_bus_note": (
                "The Agent Bus SQLite file is the same physical file for both Windows and WSL. "
                "Windows reads/writes it as C:\\...\\agent_bus.sqlite; "
                "WSL reads/writes it as /mnt/c/...//agent_bus.sqlite. "
                "No network or socket configuration is needed."
            ),
        },
        "hermes_credentials": {
            "note": (
                "Studio does not read or require any of Hermes' credentials. "
                "Hermes uses whatever model/provider it is configured with in its own WSL environment. "
                "Set up credentials in WSL according to Hermes' own configuration."
            ),
            "studio_needs_this_key": False,
            "where_to_set": "In Hermes' WSL Ubuntu environment (not Studio/Windows)",
            "verify_command": "Verify credentials according to Hermes' own configured provider.",
        },
        "startup_guide": {
            "step_1": "Use the managed Hermes gateway startup surface from Windows/Studio when available.",
            "step_2": _HERMES_STARTUP_COMMANDS["managed_gateway"],
            "step_3": "The managed launcher starts the Windows-side Hermes daemon, warms Ubuntu through wsl.exe, then launches the WSL Hermes gateway.",
            "step_4": "Ensure Hermes' configured model/provider credentials are set in the WSL environment.",
            "step_5_manual_warmup": _HERMES_STARTUP_COMMANDS["wsl_warmup"],
            "step_5_manual_gateway": _HERMES_STARTUP_COMMANDS["wsl_startup"],
            "step_5_legacy_watch_once": _HERMES_STARTUP_COMMANDS["run_once"],
            "step_5_legacy_watch_loop": _HERMES_STARTUP_COMMANDS["run_loop_10s"],
            "step_5_run_loop": _HERMES_STARTUP_COMMANDS["run_loop_10s"],
            "step_6_verify": (
                "Send a test chat from Studio and check `chaseos agent-bus heartbeats --runtime Hermes` "
                "to confirm Hermes is polling."
            ),
            "windows_shortcut": _HERMES_STARTUP_COMMANDS["wsl_startup"],
        },
        "openclaw_configuration": {
            "surface_type": "windows-cli",
            "note": (
                "OpenClaw runs directly on Windows (not WSL). It accesses the vault at the Windows "
                "path. Start OpenClaw via its Discord bot process or `chaseos run openclaw_watch`."
            ),
        },
    }
