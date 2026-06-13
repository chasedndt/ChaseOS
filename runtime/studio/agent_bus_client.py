"""Reusable Studio -> Agent Bus client helpers.

This module is the Studio-side client seam for runtime-bound work.  It is
intentionally passive: it may inspect Agent Bus state and enqueue governed task
packets, but it must not start WSL, spawn terminals, call model providers, or
mutate canonical knowledge. Runtime daemons own execution after a task is on the
bus.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from runtime.agent_bus.bus import create_task, list_heartbeats, list_tasks

MODEL_VERSION = "studio.agent_bus_client.v1"
SURFACE_ID = "studio_agent_bus_client"
COMPANION_CONFIG_PATH = ".chaseos/companion_config.json"

DEFAULT_RUNTIME_ID_TO_RECIPIENT: dict[str, str] = {
    "hermes": "Hermes",
    "openclaw": "OpenClaw",
    "claude-code": "Archon",
    "archon": "Archon",
    "codex": "Codex",
}


def _norm_runtime_id(value: str | None) -> str:
    return str(value or "").strip().lower()


def load_recipient_map(vault_root: str | Path) -> dict[str, str]:
    """Return Studio companion/runtime id -> Agent Bus recipient mapping.

    The default is provider-agnostic and repo-portable. A downloaded ChaseOS repo
    may override or extend it with ``.chaseos/companion_config.json`` using a
    ``recipient_names`` object. Invalid config fails closed to defaults rather
    than blocking Studio startup.
    """
    vault = Path(vault_root).resolve()
    mapping = dict(DEFAULT_RUNTIME_ID_TO_RECIPIENT)
    config_path = vault / COMPANION_CONFIG_PATH
    if not config_path.exists():
        return mapping
    try:
        cfg = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return mapping
    recipients = cfg.get("recipient_names") if isinstance(cfg, dict) else None
    if isinstance(recipients, dict):
        for companion_id, recipient in recipients.items():
            companion_key = _norm_runtime_id(str(companion_id))
            recipient_name = str(recipient or "").strip()
            if companion_key and recipient_name:
                mapping[companion_key] = recipient_name
    return mapping


def resolve_recipient(vault_root: str | Path, runtime_id: str | None) -> str:
    """Resolve a Studio runtime selector to an Agent Bus recipient.

    Unknown selectors route to Hermes as the synthesis/default chat runtime;
    they do not trigger provider calls or process launch attempts.
    """
    mapping = load_recipient_map(vault_root)
    return mapping.get(_norm_runtime_id(runtime_id)) or "Hermes"


def runtime_id_for_recipient_name(recipient: str | None) -> str:
    normalized = str(recipient or "").strip().lower()
    reverse = {value.lower(): key for key, value in DEFAULT_RUNTIME_ID_TO_RECIPIENT.items()}
    return reverse.get(normalized, normalized or "hermes")


def derive_portable_vault_paths(vault_root: str | Path) -> dict[str, str | None]:
    """Derive WSL/Windows path hints without hard-coded users.

    This makes GitHub-download installs portable: paths are derived from the
    selected vault root, not from Chase's local username. No path is probed or
    launched here.
    """
    vault = Path(vault_root).resolve()
    posix_path = vault.as_posix()
    windows_path: str | None = None
    if posix_path.startswith("/mnt/") and len(posix_path) > 6 and posix_path[6] == "/":
        drive = posix_path[5].upper()
        rest = posix_path[7:]
        windows_path = f"{drive}:\\" + rest.replace("/", "\\")
    return {
        "vault_path": posix_path,
        "wsl_vault_path": posix_path if posix_path.startswith("/mnt/") else None,
        "windows_vault_path": windows_path,
    }


@dataclass(frozen=True)
class StudioAgentBusClient:
    """Passive Studio client for bus status/read/write operations."""

    vault_root: str | Path
    sender: str = "Codex"

    @property
    def vault(self) -> Path:
        return Path(self.vault_root).resolve()

    def recipient_for(self, runtime_id: str | None) -> str:
        return resolve_recipient(self.vault, runtime_id)

    def runtime_status(self, runtime_id: str | None, *, recent_task_limit: int = 5) -> dict[str, Any]:
        """Read runtime Agent Bus liveness without launching anything."""
        recipient = self.recipient_for(runtime_id)
        heartbeat: dict[str, Any] | None = None
        recent_tasks: list[dict[str, Any]] = []
        heartbeat_error: str | None = None
        task_error: str | None = None
        try:
            beats = list_heartbeats(self.vault, runtime=recipient)
            if beats:
                heartbeat = beats[0] if isinstance(beats[0], dict) else None
        except Exception as exc:  # noqa: BLE001 - status must be best-effort/passive
            heartbeat_error = str(exc)[:160]
        try:
            recent_tasks = (list_tasks(self.vault, recipient=recipient) or [])[:recent_task_limit]
        except Exception as exc:  # noqa: BLE001
            task_error = str(exc)[:160]

        paths = derive_portable_vault_paths(self.vault)
        heartbeat_status = heartbeat.get("status") if heartbeat else None
        heartbeat_updated = (heartbeat.get("updated_at") or heartbeat.get("last_seen")) if heartbeat else None
        return {
            "ok": True,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "runtime_id": _norm_runtime_id(runtime_id) or runtime_id_for_recipient_name(recipient),
            "recipient": recipient,
            "heartbeat_found": heartbeat is not None,
            "heartbeat_status": heartbeat_status,
            "last_seen_utc": heartbeat_updated,
            "recent_task_count": len(recent_tasks),
            "recent_tasks": recent_tasks,
            "paths": paths,
            "launch_policy": {
                "passive_status_only": True,
                "starts_wsl": False,
                "spawns_terminal": False,
                "starts_runtime_daemon": False,
                "provider_call_performed": False,
            },
            "startup_guide": build_startup_guide(self.vault, recipient),
            "warnings": [item for item in [
                f"heartbeat_read_error:{heartbeat_error}" if heartbeat_error else None,
                f"task_read_error:{task_error}" if task_error else None,
            ] if item],
        }

    def create_task(
        self,
        *,
        runtime_id: str | None,
        request: str,
        expected_output: str,
        notes: str | None = None,
        intent: str = "TASK",
        priority: str = "normal",
        ingress_context: dict[str, Any] | None = None,
        execution_constraints: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a runtime-bound task packet on Agent Bus only."""
        recipient = self.recipient_for(runtime_id)
        result = create_task(
            self.vault,
            sender=self.sender,
            recipient=recipient,
            intent=intent,
            priority=priority,
            request=request,
            expected_output=expected_output,
            notes=notes,
            ingress_context=ingress_context,
            execution_constraints=execution_constraints,
        )
        return {
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "recipient": recipient,
            "agent_bus_result": result,
            "created": bool(result.get("created")),
            "task_id": result.get("task_id"),
            "authority": {
                "runtime_dispatch_via_agent_bus": True,
                "provider_call_performed": False,
                "starts_wsl": False,
                "spawns_terminal": False,
                "canonical_mutation_performed": False,
            },
        }


def build_startup_guide(vault_root: str | Path, recipient: str) -> str:
    """Return human-readable daemon guidance; do not execute it."""
    vault = Path(vault_root).resolve().as_posix()
    runtime = runtime_id_for_recipient_name(recipient)
    if runtime == "openclaw":
        workflow = "openclaw_watch"
    elif runtime in {"archon", "claude-code"}:
        workflow = "archon_watch"
    else:
        workflow = "hermes_watch"
    return (
        "Passive status only. If the operator approves startup, use the Runtime Controls surface "
        f"or run: cd {vault} && python -m runtime.workflows.{workflow} --vault {vault} --interval 10"
    )
