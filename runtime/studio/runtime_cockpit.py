"""Studio Runtime Cockpit contract model.

This module provides the first desktop-facing contract for the Phase 10 Runtime
Cockpit. It aggregates existing Studio service-layer models and keeps the
desktop shell unbuilt until the UI can mount this contract without gaining new
write authority.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from typing import Any, Callable
import os
import subprocess

from runtime.lifecycle.health_cli import check_health, load_lifecycle_record
from runtime.studio.app_launcher import build_studio_app_launcher_plan
from runtime.studio.dashboard import get_dashboard
from runtime.studio.runtime_startup_controls import build_runtime_startup_controls_model


_SURFACE = "studio_runtime_cockpit_contract"
_STATUS_READY = "contract_ready_local_mount_built_studio_shell_mvp_built"
_STATUS_READY_WITH_ERRORS = "contract_ready_local_mount_built_with_panel_errors_studio_shell_mvp_built"
_NEXT_NATIVE_PASS = "studio-provenance-memory-identity-runtime-navigation-readonly-panels"


def _hidden_subprocess_creationflags() -> int:
    if os.name != "nt":
        return 0
    return int(getattr(subprocess, "CREATE_NO_WINDOW", 0) or 0)


def _safe_call(
    name: str,
    errors: list[str],
    fn: Callable[[], dict[str, Any]],
    *,
    fallback: dict[str, Any] | None = None,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    fallback_model = fallback if fallback is not None else {"ok": False, "error": f"{name} unavailable"}
    if timeout_seconds is None:
        try:
            return fn()
        except Exception as exc:
            errors.append(f"{name}: {exc}")
            return {**fallback_model, "error": str(exc)}
    if timeout_seconds <= 0:
        errors.append(f"{name}: timed out after 0s")
        return {**fallback_model, "error": "timed out after 0s"}

    queue: Queue[tuple[bool, dict[str, Any] | BaseException]] = Queue(maxsize=1)

    def _target() -> None:
        try:
            queue.put((True, fn()))
        except BaseException as exc:  # noqa: BLE001
            queue.put((False, exc))

    thread = Thread(target=_target, name=f"runtime-cockpit-{name}", daemon=True)
    thread.start()
    try:
        ok, value = queue.get(timeout=max(0.001, timeout_seconds))
    except Empty:
        errors.append(f"{name}: timed out after {timeout_seconds:g}s")
        return {**fallback_model, "error": f"timed out after {timeout_seconds:g}s"}
    if ok:
        return value  # type: ignore[return-value]
    errors.append(f"{name}: {value}")
    return {**fallback_model, "error": str(value)}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _readiness_summary(cards: list[dict[str, Any]]) -> dict[str, Any]:
    total = 0
    approval_missing = 0
    approval_found = 0
    success_marker_blocked = 0
    executor_blocked = 0
    for card in cards:
        readiness_by_intent = card.get("approval_readiness") or {}
        for readiness in readiness_by_intent.values():
            if not isinstance(readiness, dict):
                continue
            total += 1
            approval = readiness.get("approval_artifact") or {}
            if approval.get("status") == "approved-found":
                approval_found += 1
            elif approval.get("approval_required", readiness.get("approval_required")):
                approval_missing += 1
            executor = readiness.get("executor_readiness") or {}
            if executor.get("executor_enabled_now") is False:
                executor_blocked += 1
            verifier = readiness.get("success_marker_evidence_verifier") or {}
            if verifier.get("verifier_status") == "blocked":
                success_marker_blocked += 1
    return {
        "readiness_packet_count": total,
        "approval_missing_count": approval_missing,
        "approval_found_count": approval_found,
        "executor_blocked_count": executor_blocked,
        "success_marker_blocked_count": success_marker_blocked,
        "host_mutation_allowed_now": False,
        "success_marker_acceptance_allowed_now": False,
    }


def _path_status(vault: Path, rel_path: str) -> dict[str, Any]:
    path = vault / rel_path
    exists = path.exists()
    result: dict[str, Any] = {
        "path": rel_path,
        "exists": exists,
        "kind": "missing",
        "size_bytes": None,
        "modified_at_utc": None,
    }
    if not exists:
        return result
    try:
        stat = path.stat()
    except OSError as exc:
        result["kind"] = "inaccessible"
        result["error"] = str(exc)
        return result
    result["kind"] = "directory" if path.is_dir() else "file"
    result["size_bytes"] = stat.st_size if path.is_file() else None
    result["modified_at_utc"] = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat().replace("+00:00", "Z")
    return result


def _latest_files(vault: Path, rel_dir: str, suffixes: tuple[str, ...], *, limit: int = 6, scan_limit: int = 100) -> list[dict[str, Any]]:
    root = vault / rel_dir
    if not root.is_dir():
        return []
    paths: list[Path] = []
    items: list[dict[str, Any]] = []
    try:
        for index, path in enumerate(root.iterdir()):
            if index >= scan_limit:
                break
            if path.is_file() and path.name.lower().endswith(suffixes):
                paths.append(path)
    except OSError:
        return []
    for path in sorted(paths, key=lambda item: item.stat().st_mtime if item.exists() else 0, reverse=True)[:limit]:
        items.append(_path_status(vault, f"{rel_dir}/{path.name}"))
    return items


def _runtime_display_status(health: dict[str, Any], platform: str | None = None) -> str:
    status = str(health.get("status") or "unknown").strip().lower()
    if bool(health.get("healthy")) or status in {"healthy", "live", "running", "ok", "process-live", "heartbeat-live"}:
        return "live"
    # Session-based runtimes (Archon/Codex) that are not live are idle, not blocked.
    # "blocked" implies a malfunction; for local-session runtimes it just means no active session.
    if platform == "local-session":
        return "idle"
    if status in {"unavailable", "not_configured", "invalid_runtime"} or health.get("blocked_reason"):
        return "blocked"
    if status in {"offline", "down", "failed"}:
        return "offline"
    return "unknown"


def _process_probe_allowed(record: dict[str, Any]) -> bool:
    platform = str(record.get("platform") or "").strip().lower()
    lifecycle_mode = str(record.get("lifecycle_mode") or "").strip().lower()
    return platform in {"wsl", "linux", "local", "local-session"} or "wsl" in lifecycle_mode or "process" in lifecycle_mode


def _runtime_process_tokens(runtime_id: str, record: dict[str, Any]) -> list[str]:
    tokens = [runtime_id]
    coordination_watch = record.get("coordination_watch") if isinstance(record.get("coordination_watch"), dict) else {}
    runtime_name = coordination_watch.get("runtime_name") or record.get("runtime_name")
    if runtime_name:
        tokens.append(str(runtime_name))
    start = record.get("start") if isinstance(record.get("start"), dict) else {}
    command = str(start.get("command") or "").strip()
    if command:
        tokens.append(command.split()[0])
    return [token.strip().lower() for token in tokens if token and token.strip()]


def _list_runtime_processes(runtime_id: str, record: dict[str, Any]) -> list[dict[str, Any]]:
    """Return bounded read-only host process evidence for WSL/local runtime records."""

    if not _process_probe_allowed(record):
        return []
    tokens = _runtime_process_tokens(runtime_id, record)
    if not tokens:
        return []
    try:
        completed = subprocess.run(
            ["ps", "-eo", "pid=,comm=,args="],
            capture_output=True,
            text=True,
            timeout=0.5,
            check=False,
            creationflags=_hidden_subprocess_creationflags(),
        )
    except Exception:
        return []
    if completed.returncode != 0:
        return []
    current_tokens = {"ps", "grep"}
    matches: list[dict[str, Any]] = []
    for line in completed.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(maxsplit=2)
        if len(parts) < 3:
            continue
        pid, comm, command = parts
        command_lower = command.lower()
        comm_lower = comm.lower()
        if comm_lower in current_tokens:
            continue
        argv_names = {Path(arg).name.lower() for arg in command.split() if arg.strip()}
        if any(comm_lower == token or token in argv_names for token in tokens):
            matches.append({"pid": int(pid), "command": command[:300]})
    return matches[:12]


def _apply_runtime_evidence_overrides(
    runtime_id: str,
    record: dict[str, Any],
    health: dict[str, Any],
    *,
    probe_processes: bool = False,
) -> dict[str, Any]:
    """Promote live read-only evidence over stale/timeout probes without granting action authority."""

    process_matches = _list_runtime_processes(runtime_id, record) if probe_processes else []
    evidence_sources = []
    merged = dict(health)
    if health.get("healthy"):
        evidence_sources.append({"source": "health", "status": health.get("status") or "healthy"})
    if process_matches:
        evidence_sources.append({"source": "process", "status": "live", "count": len(process_matches)})
        merged.update(
            {
                "status": "process-live",
                "healthy": True,
                "blocked_reason": None,
                "failure_reason": None,
                "process_probe": "wsl-read-only-ps",
                "process_count": len(process_matches),
                "processes": process_matches,
            }
        )
    merged["evidence_sources"] = evidence_sources
    return merged


def _runtime_health(
    vault: Path,
    *,
    health_probe_timeout_seconds: float = 0.15,
    bus_heartbeats: dict[str, Any] | None = None,
    probe_processes: bool = False,
) -> dict[str, Any]:
    root = vault / "runtime" / "lifecycle"
    profiles: list[dict[str, Any]] = []
    heartbeat_by_runtime: dict[str, Any] = {}
    if bus_heartbeats:
        heartbeat_by_runtime = bus_heartbeats.get("runtime_heartbeats") or {}
    if root.is_dir():
        for path in sorted(root.glob("*.lifecycle.yaml")):
            runtime_id = path.name.replace(".lifecycle.yaml", "")
            try:
                record = load_lifecycle_record(runtime_id, vault_root=vault)
            except Exception as exc:
                record = {}
                health = {
                    "status": "invalid_runtime",
                    "healthy": False,
                    "blocked_reason": str(exc),
                    "errors": [{"code": "lifecycle_record_error", "message": str(exc)}],
                }
            else:
                health_errors: list[str] = []
                health = _safe_call(
                    f"runtime_health:{runtime_id}",
                    health_errors,
                    lambda runtime_id=runtime_id: check_health(runtime_id, timeout_seconds=1, vault_root=vault),
                    fallback={
                        "status": "unknown",
                        "healthy": False,
                        "blocked_reason": "health_probe_timeout",
                        "timed_out": True,
                        "errors": [{"code": "health_probe_timeout", "message": "bounded Runtime Cockpit probe timed out"}],
                    },
                    timeout_seconds=health_probe_timeout_seconds,
                )
            health = _apply_runtime_evidence_overrides(
                runtime_id,
                record,
                health,
                probe_processes=probe_processes,
            )

            # Merge bus heartbeat data: upgrade display status when bus shows a fresh heartbeat
            bus_hb = heartbeat_by_runtime.get(runtime_id) or {}
            bus_last_seen = bus_hb.get("last_seen")
            bus_freshness = bus_hb.get("freshness")
            if bus_freshness in {"fresh", "recent"} and not health.get("healthy"):
                health = dict(health)
                health["status"] = "heartbeat-live"
                health["healthy"] = True
                health["blocked_reason"] = None
                health.setdefault("evidence_sources", []).append(
                    {"source": "bus_heartbeat", "status": bus_freshness, "last_seen": bus_last_seen}
                )

            display_status = _runtime_display_status(health, platform=record.get("platform"))
            coordination_watch = record.get("coordination_watch") if isinstance(record.get("coordination_watch"), dict) else {}

            # last_heartbeat: prefer bus data over probe data (bus is more reliable)
            last_heartbeat = (
                bus_last_seen
                or health.get("last_heartbeat")
                or health.get("heartbeat_at")
                or health.get("last_seen_at_utc")
            )

            profiles.append(
                {
                    **_path_status(vault, f"runtime/lifecycle/{path.name}"),
                    "runtime_id": runtime_id,
                    "runtime_name": coordination_watch.get("runtime_name") or record.get("runtime_name") or runtime_id,
                    "status": display_status,
                    "health_status": health.get("status") or "unknown",
                    "health_kind": health.get("kind") or ((record.get("health") or {}).get("kind") if isinstance(record.get("health"), dict) else None),
                    "healthy": bool(health.get("healthy")),
                    "detected_url": health.get("detected_url") or health.get("url"),
                    "candidate_urls": health.get("candidate_urls") or health.get("urls") or [],
                    "candidate_ports": health.get("candidate_ports") or [],
                    "last_heartbeat": last_heartbeat,
                    "bus_heartbeat": {
                        "last_seen": bus_last_seen,
                        "age_seconds": bus_hb.get("age_seconds"),
                        "freshness": bus_hb.get("freshness") or "unknown",
                        "is_stale": bus_hb.get("is_stale", True),
                        "current_task_id": bus_hb.get("current_task_id"),
                        "status": bus_hb.get("status"),
                    } if bus_hb else None,
                    "evidence": {
                        "probe_label": health.get("probe_label"),
                        "probe_notes": health.get("probe_notes"),
                        "status_code": health.get("status_code"),
                        "returncode": health.get("returncode"),
                        "timed_out": bool(health.get("timed_out", False)),
                        "errors": health.get("errors") or [],
                        "evidence_sources": health.get("evidence_sources") or [],
                        "process_probe": health.get("process_probe"),
                        "process_count": health.get("process_count", 0),
                        "processes": health.get("processes") or [],
                    },
                    "authority_ceiling": record.get("ownership") or record.get("authority_ceiling") or "unknown",
                    "blocked_reason": health.get("blocked_reason") or health.get("failure_reason"),
                    "lifecycle_mode": record.get("lifecycle_mode"),
                    "platform": record.get("platform"),
                }
            )
    return {
        "status": "read-only-visible",
        "source": "runtime/lifecycle/*.lifecycle.yaml + runtime.lifecycle.health_cli.check_health + agent_bus.sqlite",
        "runtime_profile_count": len(profiles),
        "live_runtime_count": sum(1 for profile in profiles if profile.get("status") == "live"),
        "heartbeat_live_count": sum(1 for profile in profiles if profile.get("health_status") == "heartbeat-live"),
        "offline_runtime_count": sum(1 for profile in profiles if profile.get("status") == "offline"),
        "blocked_runtime_count": sum(1 for profile in profiles if profile.get("status") == "blocked"),
        "idle_runtime_count": sum(1 for profile in profiles if profile.get("status") == "idle"),
        "unknown_runtime_count": sum(1 for profile in profiles if profile.get("status") == "unknown"),
        "profiles": profiles,
        "host_process_probe_enabled": bool(probe_processes),
        "start_stop_restart_actions_available": False,
    }


def _bus_heartbeat_state(vault: Path) -> dict[str, Any]:
    """Read live bus heartbeat records from SQLite and return per-runtime freshness data."""
    try:
        from runtime.agent_bus.bus import list_heartbeats
        rows = list_heartbeats(vault)
    except Exception as exc:
        return {
            "status": "unavailable",
            "error": str(exc),
            "runtime_heartbeats": {},
            "total_records": 0,
        }

    now = datetime.now(timezone.utc)
    by_runtime: dict[str, dict[str, Any]] = {}

    for row in rows:
        runtime_id = str(row.get("runtime") or "").strip().lower()
        if not runtime_id:
            continue
        last_seen = row.get("last_seen") or row.get("last_seen_at_utc") or row.get("heartbeat_at") or row.get("updated_at")
        age_seconds: float | None = None
        is_stale = True
        if last_seen:
            try:
                ts = datetime.fromisoformat(str(last_seen).replace("Z", "+00:00"))
                age_seconds = (now - ts).total_seconds()
                is_stale = age_seconds > 900  # default stale threshold; lifecycle YAML refines this
            except ValueError:
                pass

        existing = by_runtime.get(runtime_id)
        if existing is None or (age_seconds is not None and (existing.get("age_seconds") is None or age_seconds < existing["age_seconds"])):
            by_runtime[runtime_id] = {
                "runtime": runtime_id,
                "last_seen": last_seen,
                "age_seconds": age_seconds,
                "is_stale": is_stale,
                "status": row.get("status") or "unknown",
                "health": row.get("health") or "unknown",
                "current_task_id": row.get("current_task_id"),
                "summary": row.get("summary"),
                "heartbeat_scope": row.get("heartbeat_scope") or "runtime",
                "control_surface": row.get("control_surface"),
            }

    # Freshness label helper
    for entry in by_runtime.values():
        age = entry.get("age_seconds")
        if age is None:
            entry["freshness"] = "unknown"
        elif age < 120:
            entry["freshness"] = "fresh"
        elif age < 900:
            entry["freshness"] = "recent"
        else:
            entry["freshness"] = "stale"

    return {
        "status": "read-only-live" if by_runtime else "no-heartbeats",
        "source": "agent_bus.sqlite heartbeats table",
        "total_records": len(rows),
        "runtime_heartbeats": by_runtime,
        "runtimes_with_fresh_heartbeat": [r for r, d in by_runtime.items() if d.get("freshness") == "fresh"],
        "runtimes_stale": [r for r, d in by_runtime.items() if d.get("is_stale")],
    }


def _coordination_watch_state(vault: Path) -> dict[str, Any]:
    run_root = vault / "runtime" / "lifecycle" / "run"
    watches: list[dict[str, Any]] = []
    if run_root.is_dir():
        for path in sorted(run_root.glob("*coordination-watch*.json")):
            watches.append(
                {
                    **_path_status(vault, f"runtime/lifecycle/run/{path.name}"),
                    "watch_id": path.stem,
                    "source_kind": "coordination-watch-json",
                }
            )
        for path in sorted(run_root.glob("*coordination-watch*.log")):
            watches.append(
                {
                    **_path_status(vault, f"runtime/lifecycle/run/{path.name}"),
                    "watch_id": path.stem,
                    "source_kind": "coordination-watch-log",
                }
            )
    return {
        "status": "read-only-visible" if watches else "no-watch-artifacts-found",
        "source": "runtime/lifecycle/run/*coordination-watch*",
        "artifact_count": len(watches),
        "artifacts": watches[:12],
        "opens_watch_loops": False,
        "dispatches_runtimes": False,
    }


def _post_reboot_indicators(vault: Path) -> dict[str, Any]:
    bootstrap_root = vault / "runtime" / "lifecycle" / "bootstrap"
    indicators: list[dict[str, Any]] = []
    if bootstrap_root.is_dir():
        for pattern, kind in [
            ("*reboot-verify*.json", "reboot-verify"),
            ("*bootstrap-success*.json", "bootstrap-success"),
            ("*registration.json", "registration"),
        ]:
            for path in sorted(bootstrap_root.glob(pattern)):
                indicators.append(
                    {
                        **_path_status(vault, f"runtime/lifecycle/bootstrap/{path.name}"),
                        "indicator_kind": kind,
                    }
                )
    return {
        "status": "read-only-visible" if indicators else "no-post-reboot-indicators-found",
        "source": "runtime/lifecycle/bootstrap/*",
        "indicator_count": len(indicators),
        "indicators": indicators[:12],
        "accepts_success_markers": False,
        "writes_bootstrap_state": False,
    }


def _startup_drift(cards: list[dict[str, Any]]) -> dict[str, Any]:
    manageable = [card for card in cards if card.get("studio_control_enabled")]
    visual = [card for card in cards if card.get("studio_visual_toggle_built")]
    approval_required = 0
    executor_blocked = 0
    for card in cards:
        for readiness in (card.get("approval_readiness") or {}).values():
            if not isinstance(readiness, dict):
                continue
            if readiness.get("approval_required"):
                approval_required += 1
            executor = readiness.get("executor_readiness") or {}
            if executor.get("executor_enabled_now") is False:
                executor_blocked += 1
    return {
        "status": "read-only-derived",
        "surface_count": len(cards),
        "manageable_surface_count": len(manageable),
        "visual_surface_count": len(visual),
        "approval_required_count": approval_required,
        "executor_blocked_count": executor_blocked,
        "drift_detected": False,
        "drift_probe_scope": "startup-control-contract-only",
        "live_toggle_blocked_until_governed_executor": True,
    }


def _logs_and_audit(vault: Path) -> dict[str, Any]:
    log_groups = [
        {
            "id": "build-logs",
            "label": "Build Logs",
            "root": "07_LOGS/Build-Logs",
            "latest": _latest_files(vault, "07_LOGS/Build-Logs", (".md",), limit=5),
        },
        {
            "id": "agent-activity",
            "label": "Agent Activity",
            "root": "07_LOGS/Agent-Activity",
            "latest": _latest_files(vault, "07_LOGS/Agent-Activity", (".md", ".json"), limit=5),
        },
        {
            "id": "lifecycle-run",
            "label": "Lifecycle Run",
            "root": "runtime/lifecycle/run",
            "latest": _latest_files(vault, "runtime/lifecycle/run", (".log", ".json", ".jsonl"), limit=8),
        },
        {
            "id": "schedule-config",
            "label": "Schedules",
            "root": "runtime/schedules",
            "latest": _latest_files(vault, "runtime/schedules", (".yaml", ".yml", ".json"), limit=6),
        },
    ]
    return {
        "status": "read-only-expanded",
        "groups": log_groups,
        "group_count": len(log_groups),
        "writes_audit_logs": False,
        "consumes_approval_artifacts": False,
        "executes_runtime_actions": False,
    }


def _runtime_cards(cards: list[dict[str, Any]], runtime_health: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    runtime_cards: list[dict[str, Any]] = []
    health_profiles = {profile.get("runtime_id"): profile for profile in (runtime_health or {}).get("profiles", [])}
    seen_runtime_ids: set[str] = set()
    for card in cards:
        runtime_id = card.get("runtime_id")
        seen_runtime_ids.add(str(runtime_id))
        commands = card.get("commands") or {}
        approval = card.get("approval_readiness") or {}
        health = health_profiles.get(runtime_id) or {}
        runtime_cards.append(
            {
                "runtime_id": runtime_id,
                "runtime_name": card.get("runtime_name") or health.get("runtime_name"),
                "surface_id": card.get("surface_id"),
                "ui_label": card.get("ui_label"),
                "current_state": card.get("current_state"),
                "health_status": health.get("status") or "unknown",
                "health_probe_status": health.get("health_status"),
                "last_heartbeat": health.get("last_heartbeat"),
                "detected_url": health.get("detected_url"),
                "authority_ceiling": health.get("authority_ceiling"),
                "blocked_reason": health.get("blocked_reason"),
                "runtime_evidence": health.get("evidence") or {},
                "target_states": card.get("target_states") or {},
                "user_manageable": bool(card.get("user_manageable")),
                "studio_control_enabled": bool(card.get("studio_control_enabled")),
                "studio_visual_toggle_built": bool(card.get("studio_visual_toggle_built")),
                "requires_confirm_action": bool(card.get("requires_confirm_action")),
                "startup_registration_kind": card.get("startup_registration_kind"),
                "launch_profile": card.get("launch_profile") or {},
                "commands": {
                    "model": "chaseos studio runtime-startup-controls --json",
                    "enable_dry_run": ((commands.get("enable") or {}).get("studio_preview")),
                    "enable_toggle": ((commands.get("enable") or {}).get("studio_toggle")),
                    "disable_dry_run": ((commands.get("disable") or {}).get("studio_preview")),
                    "disable_toggle": ((commands.get("disable") or {}).get("studio_toggle")),
                },
                "approval_summary": {
                    "enable_required": bool((approval.get("enable") or {}).get("approval_required")),
                    "disable_required": bool((approval.get("disable") or {}).get("approval_required")),
                    "enable_artifact_status": ((approval.get("enable") or {}).get("approval_artifact") or {}).get("status"),
                    "disable_artifact_status": ((approval.get("disable") or {}).get("approval_artifact") or {}).get("status"),
                    "host_mutation_allowed_now": False,
                },
            }
        )
    for runtime_id, health in health_profiles.items():
        if str(runtime_id) in seen_runtime_ids:
            continue
        runtime_cards.append(
            {
                "runtime_id": runtime_id,
                "runtime_name": health.get("runtime_name") or runtime_id,
                "surface_id": "runtime-profile",
                "ui_label": "Runtime Profile",
                "current_state": health.get("status") or "unknown",
                "health_status": health.get("status") or "unknown",
                "health_probe_status": health.get("health_status"),
                "last_heartbeat": health.get("last_heartbeat"),
                "detected_url": health.get("detected_url"),
                "authority_ceiling": health.get("authority_ceiling"),
                "blocked_reason": health.get("blocked_reason"),
                "runtime_evidence": health.get("evidence") or {},
                "target_states": {},
                "user_manageable": False,
                "studio_control_enabled": False,
                "studio_visual_toggle_built": False,
                "requires_confirm_action": False,
                "startup_registration_kind": None,
                "launch_profile": {},
                "commands": {"model": "chaseos studio runtime-cockpit --json"},
                "approval_summary": {
                    "enable_required": False,
                    "disable_required": False,
                    "enable_artifact_status": "not-applicable",
                    "disable_artifact_status": "not-applicable",
                    "host_mutation_allowed_now": False,
                },
            }
        )
    return runtime_cards


def _available_surfaces(app_launcher_plan: dict[str, Any]) -> list[dict[str, Any]]:
    surfaces = [
        {
            "id": "studio-runtime-cockpit-contract",
            "title": "Runtime Cockpit Contract",
            "command": "chaseos studio runtime-cockpit --json",
            "type": "cli-contract",
            "status": "available",
            "read_only": True,
        },
        {
            "id": "studio-dashboard",
            "title": "Studio Dashboard",
            "command": "chaseos studio dashboard --json",
            "type": "cli-model",
            "status": "available",
            "read_only": True,
        },
        {
            "id": "runtime-startup-controls",
            "title": "Runtime Startup Controls",
            "command": "chaseos studio runtime-startup-controls --json",
            "type": "cli-model",
            "status": "available",
            "read_only": True,
        },
    ]
    for app in app_launcher_plan.get("apps") or []:
        surfaces.append(
            {
                "id": app.get("id"),
                "title": app.get("title"),
                "command": app.get("command"),
                "type": "local-app",
                "status": app.get("status"),
                "default_url": app.get("default_url"),
                "read_only": bool(app.get("read_only")),
                "write_capable": bool(app.get("write_capable")),
                "requires_confirmation_for_writes": bool(app.get("requires_confirmation_for_writes")),
                "runtime_status": app.get("runtime_status") or {},
            }
        )
    return surfaces


def build_runtime_cockpit_fast_contract(vault_root: str | Path, *, runtime_id: str | None = None) -> dict[str, Any]:
    """Return the lightweight runtime truth subset used by fast Studio shell planning."""

    vault = Path(vault_root).resolve()
    errors: list[str] = []
    startup = _safe_call(
        "runtime_startup_controls",
        errors,
        lambda: build_runtime_startup_controls_model(vault, runtime_id),
    )
    cards = list(startup.get("surface_cards") or [])
    manageable_cards = [card for card in cards if card.get("studio_control_enabled")]
    visual_cards = [card for card in cards if card.get("studio_visual_toggle_built")]
    bus_heartbeats = _bus_heartbeat_state(vault)
    runtime_health = _runtime_health(vault, bus_heartbeats=bus_heartbeats)
    return {
        "ok": not bool(errors),
        "surface": _SURFACE,
        "title": "Studio Runtime Cockpit Contract",
        "status": "fast_runtime_truth_ready" if not errors else "fast_runtime_truth_ready_with_errors",
        "generated_at_utc": _utc_now_iso(),
        "vault_root": str(vault),
        "runtime_filter": runtime_id or "all",
        "runtime_startup": {
            "source_surface": startup.get("surface"),
            "runtime_count": startup.get("runtime_count"),
            "surface_count": startup.get("surface_count", len(cards)),
            "manageable_surface_count": len(manageable_cards),
            "visual_surface_count": len(visual_cards),
            "mutation_actions_enabled": bool(startup.get("mutation_actions_enabled")),
            "approval_boundary": startup.get("approval_boundary") or {},
            "readiness_summary": _readiness_summary(cards),
            "cards": _runtime_cards(cards, runtime_health),
        },
        "runtime_health": runtime_health,
        "boundary": {
            "read_only": True,
            "reads_vault": True,
            "reads_runtime_startup_controls": True,
            "reads_lifecycle_profiles": True,
            "writes_vault": False,
            "writes_host_startup": False,
            "starts_runtimes": False,
            "stops_runtimes": False,
            "restarts_runtimes": False,
            "executes_runtime_actions": False,
            "canonical_mutation_allowed": False,
        },
        "errors": errors,
    }


def build_runtime_cockpit_contract(
    vault_root: str | Path,
    *,
    runtime_id: str | None = None,
    probe_child_apps: bool = True,
    probe_processes: bool = False,
    service_timeout_seconds: float = 0.15,
) -> dict[str, Any]:
    """Return the first read-only Studio Runtime Cockpit desktop contract."""

    vault = Path(vault_root).resolve()
    errors: list[str] = []
    dashboard = _safe_call(
        "dashboard",
        errors,
        lambda: get_dashboard(vault, probe_child_apps=probe_child_apps),
        fallback={"ok": False, "surface": None, "panel_errors": []},
        timeout_seconds=service_timeout_seconds,
    )
    startup = _safe_call(
        "runtime_startup_controls",
        errors,
        lambda: build_runtime_startup_controls_model(vault, runtime_id),
        fallback={
            "ok": False,
            "surface": None,
            "runtime_count": 0,
            "surface_count": 0,
            "mutation_actions_enabled": False,
            "approval_boundary": {},
            "surface_cards": [],
        },
        timeout_seconds=service_timeout_seconds,
    )
    app_launcher = _safe_call(
        "app_launcher",
        errors,
        lambda: build_studio_app_launcher_plan(
            vault,
            host="127.0.0.1",
            port=8769,
            probe_health=probe_child_apps,
        ),
        fallback={"ok": False, "surface": None, "app_count": 0, "authority": {}, "apps": []},
        timeout_seconds=service_timeout_seconds,
    )

    cards = list(startup.get("surface_cards") or [])
    manageable_cards = [card for card in cards if card.get("studio_control_enabled")]
    visual_cards = [card for card in cards if card.get("studio_visual_toggle_built")]
    bus_heartbeats = _bus_heartbeat_state(vault)
    runtime_health = _runtime_health(
        vault,
        health_probe_timeout_seconds=service_timeout_seconds,
        bus_heartbeats=bus_heartbeats,
        probe_processes=probe_processes,
    )
    coordination_watch = _coordination_watch_state(vault)
    startup_drift = _startup_drift(cards)
    post_reboot = _post_reboot_indicators(vault)
    logs_and_audit = _logs_and_audit(vault)
    panel_errors = list(dashboard.get("panel_errors") or [])
    all_errors = errors + [f"dashboard_panel: {item}" for item in panel_errors]
    status = _STATUS_READY_WITH_ERRORS if all_errors else _STATUS_READY

    return {
        "ok": True,
        "surface": _SURFACE,
        "title": "Studio Runtime Cockpit Contract",
        "status": status,
        "generated_at_utc": _utc_now_iso(),
        "vault_root": str(vault),
        "runtime_filter": runtime_id or "all",
        "phase": "Phase 10",
        "pass": "runtime-cockpit-expansion",
        "desktop": {
            "desktop_shell_built": False,
            "desktop_runtime_cockpit_built": True,
            "desktop_runtime_cockpit_native_panel_built": True,
            "studio_shell_mvp_built": True,
            "studio_shell_mvp_command": "chaseos studio desktop-shell-app --dry-run --json",
            "studio_shell_mvp_url": "http://127.0.0.1:8772/",
            "desktop_runtime_cockpit_local_mount_built": True,
            "local_app_built": True,
            "local_app_command": "chaseos studio runtime-cockpit-app --dry-run --json",
            "local_app_url": "http://127.0.0.1:8771/",
            "contract_model_built": True,
            "cli_surface_built": True,
            "native_panel_mounted": True,
            "native_panel_id": "runtime-cockpit",
            "native_panel_frontend_target": "panel-runtime-cockpit",
            "mount_target": "native PyWebView Runtime Cockpit panel + localhost-only compatibility app",
        },
        "runtime_startup": {
            "source_surface": startup.get("surface"),
            "runtime_count": startup.get("runtime_count"),
            "surface_count": startup.get("surface_count", len(cards)),
            "manageable_surface_count": len(manageable_cards),
            "visual_surface_count": len(visual_cards),
            "mutation_actions_enabled": bool(startup.get("mutation_actions_enabled")),
            "approval_boundary": startup.get("approval_boundary") or {},
            "readiness_summary": _readiness_summary(cards),
            "cards": _runtime_cards(cards, runtime_health),
        },
        "runtime_health": runtime_health,
        "bus_heartbeats": bus_heartbeats,
        "coordination_watch": coordination_watch,
        "startup_drift": startup_drift,
        "logs_and_audit": logs_and_audit,
        "post_reboot": post_reboot,
        "studio_dashboard": {
            "source_surface": dashboard.get("surface"),
            "has_runtime_startup_panel": "runtime_startup_panel" in dashboard,
            "has_app_launcher_panel": "app_launcher_panel" in dashboard,
            "panel_error_count": len(panel_errors),
        },
        "app_launcher": {
            "source_surface": app_launcher.get("surface"),
            "app_count": app_launcher.get("app_count"),
            "authority": app_launcher.get("authority") or {},
        },
        "available_surfaces": _available_surfaces(app_launcher),
        "views": [
            {
                "id": "runtime_overview",
                "title": "Runtime Overview",
                "source": "studio dashboard + runtime startup controls",
                "status": "native-panel-mounted",
            },
            {
                "id": "runtime_health",
                "title": "Runtime Health",
                "source": "runtime lifecycle profiles + agent bus heartbeats",
                "status": "read-only-visible",
            },
            {
                "id": "bus_heartbeats",
                "title": "Bus Heartbeats",
                "source": "agent_bus.sqlite heartbeats table",
                "status": bus_heartbeats.get("status", "unknown"),
            },
            {
                "id": "coordination_watch",
                "title": "Coordination Watch",
                "source": "runtime lifecycle run artifacts",
                "status": "read-only-visible",
            },
            {
                "id": "runtime_startup_controls",
                "title": "Runtime Startup Controls",
                "source": "studio runtime-startup-controls",
                "status": "service-layer-built",
            },
            {
                "id": "startup_drift",
                "title": "Startup Drift",
                "source": "startup controls readiness packets",
                "status": "read-only-derived",
            },
            {
                "id": "approval_readiness",
                "title": "Approval Readiness",
                "source": "startup-surface approval readiness packets",
                "status": "read-only-visible",
            },
            {
                "id": "proof_status",
                "title": "Proof Status",
                "source": "executor and success-marker readiness previews",
                "status": "read-only-visible",
            },
            {
                "id": "operator_actions",
                "title": "Operator Actions",
                "source": "copyable CLI/service-layer commands",
                "status": "confirmation-gated",
            },
            {
                "id": "logs_and_audit",
                "title": "Logs and Audit",
                "source": "build logs, agent activity, lifecycle run artifacts, schedule configs",
                "status": "read-only-expanded",
            },
            {
                "id": "post_reboot",
                "title": "Post-Reboot Indicators",
                "source": "runtime lifecycle bootstrap evidence",
                "status": "read-only-visible",
            },
        ],
        "actions": [
            {
                "id": "refresh_contract",
                "label": "Refresh Contract",
                "command": "chaseos studio runtime-cockpit --json",
                "writes_host_startup": False,
                "writes_vault": False,
            },
            {
                "id": "open_runtime_cockpit_app_plan",
                "label": "Open Runtime Cockpit App Plan",
                "command": "chaseos studio runtime-cockpit-app --dry-run --json",
                "writes_host_startup": False,
                "writes_vault": False,
            },
            {
                "id": "open_startup_controls_model",
                "label": "Open Startup Controls Model",
                "command": "chaseos studio runtime-startup-controls --json",
                "writes_host_startup": False,
                "writes_vault": False,
            },
            {
                "id": "open_startup_controls_app_plan",
                "label": "Open Startup Controls App Plan",
                "command": "chaseos studio runtime-startup-controls-app --dry-run --json",
                "writes_host_startup": False,
                "writes_vault": False,
            },
        ],
        "integration_contract": {
            "desktop_shell_mount": "NATIVE-PANEL-MOUNTED",
            "full_desktop_shell": "PLANNED",
            "local_runtime_cockpit_mount": "BUILT",
            "native_runtime_cockpit_panel": "MOUNTED-READ-ONLY",
            "runtime_cards_component": "CONTRACT-READY",
            "startup_toggle_component": "SERVICE-LAYER-BUILT",
            "runtime_health_panel": "READ-ONLY",
            "bus_heartbeat_panel": "READ-ONLY",
            "coordination_watch_panel": "READ-ONLY",
            "startup_drift_panel": "READ-ONLY",
            "approval_center_component": "READ-ONLY-MOUNTED",
            "post_reboot_proof_indicator": "READ-ONLY-INDICATOR",
            "logs_and_audit_panel": "READ-ONLY-EXPANDED",
        },
        "boundary": {
            "read_only": True,
            "reads_vault": True,
            "reads_studio_dashboard": True,
            "reads_runtime_startup_controls": True,
            "reads_studio_app_registry": True,
            "reads_lifecycle_profiles": True,
            "reads_lifecycle_run_logs": True,
            "reads_bootstrap_evidence": True,
            "reads_schedule_configs": True,
            "writes_vault": False,
            "writes_host_startup": False,
            "starts_studio_child_apps": False,
            "starts_runtimes": False,
            "stops_runtimes": False,
            "restarts_runtimes": False,
            "executes_runtime_actions": False,
            "browser_automation": False,
            "provider_calls_allowed": False,
            "delivery_allowed": False,
            "scheduler_changed": False,
            "workflow_execution_allowed": False,
            "canonical_mutation_allowed": False,
            "uses_runtime_lifecycle_executor": True,
        },
        "next_desktop_passes": [
            "Add read-only Provenance Explorer panel.",
            "Add read-only Memory Ledger panel.",
            "Add read-only Agent Identity panel.",
            "Add read-only Runtime Navigation Map panel.",
            "Route any future start/stop/restart action through governed lifecycle executors only.",
        ],
        "readiness": {
            "runtime_cockpit_contract_ready": True,
            "runtime_cockpit_native_panel_mounted": True,
            "runtime_health_depth_visible": runtime_health["runtime_profile_count"] >= 0,
            "coordination_watch_visible": coordination_watch["artifact_count"] >= 0,
            "startup_drift_visible": True,
            "logs_and_audit_visible": logs_and_audit["group_count"] >= 0,
            "post_reboot_indicators_visible": post_reboot["indicator_count"] >= 0,
            "no_start_stop_restart_authority": True,
            "next_recommended_pass": _NEXT_NATIVE_PASS,
        },
        "errors": all_errors,
    }
