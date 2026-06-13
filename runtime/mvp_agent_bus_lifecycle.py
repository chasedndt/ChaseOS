"""Read-only MVP Agent Bus lifecycle proof for ChaseOS.

The MVP pass-6 requirement is concrete: one task must be created, claimed,
executed or safely blocked, have an artifact written, and have the result
logged. This module inspects the local Agent Bus store and adapter artifacts
without creating, claiming, or updating tasks.
"""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import sqlite3
from typing import Any


MODEL_VERSION = "chaseos.mvp_agent_bus_lifecycle.v1"
SURFACE_ID = "chaseos_mvp_agent_bus_lifecycle"
BUS_DB_RELATIVE_PATH = Path("runtime/agent_bus/agent_bus.sqlite")
CODEX_RUNS_RELATIVE_DIR = Path("runtime/adapters/codex/runs")
RESULT_ARTIFACT_NAME = "codex-adapter-result.json"
RESULT_EVENT_TYPES = {"result_attached", "completed", "blocked"}


def _read_json(path: Path, default: Any) -> Any:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return default
    return payload


def _parse_json_field(value: Any, default: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if not isinstance(value, str) or not value.strip():
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _parse_dt(value: str | None) -> datetime:
    if not value:
        return datetime.min
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return datetime.min


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique.append(value)
    return unique


def _task_rows(db_path: Path) -> list[dict[str, Any]]:
    if not db_path.exists():
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT *
            FROM tasks
            WHERE recipient = 'Codex'
              AND status IN ('done', 'blocked')
            ORDER BY updated_at DESC
            """
        ).fetchall()
    finally:
        conn.close()

    tasks: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["depends_on"] = _parse_json_field(item.pop("depends_on_json", "[]"), [])
        item["artifacts"] = _parse_json_field(item.pop("artifacts_json", "[]"), [])
        item["ingress_context"] = _parse_json_field(item.pop("ingress_context_json", "{}"), {})
        item["execution_constraints"] = _parse_json_field(
            item.pop("execution_constraints_json", "{}"), {}
        )
        tasks.append(item)
    return tasks


def _event_rows(db_path: Path, task_id: str) -> list[dict[str, Any]]:
    if not db_path.exists():
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT event_id, task_id, run_id, sender, event_type, message, artifacts_json, created_at
            FROM events
            WHERE task_id = ?
            ORDER BY created_at ASC
            """,
            (task_id,),
        ).fetchall()
    finally:
        conn.close()
    events: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["artifacts"] = _parse_json_field(item.pop("artifacts_json", "[]"), [])
        events.append(item)
    return events


def _artifact_summary(root: Path, artifact_refs: list[Any]) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for ref in artifact_refs:
        if not isinstance(ref, str) or not ref.strip():
            continue
        path = (root / ref).resolve()
        artifacts.append(
            {
                "path": ref,
                "exists": path.exists(),
                "inside_repo": str(path).startswith(str(root.resolve())),
                "is_result_artifact": path.name == RESULT_ARTIFACT_NAME,
            }
        )
    return artifacts


def _result_artifact_path(root: Path, task: dict[str, Any], events: list[dict[str, Any]]) -> Path | None:
    refs: list[str] = []
    for ref in task.get("artifacts") or []:
        if isinstance(ref, str):
            refs.append(ref)
    for event in events:
        for ref in event.get("artifacts") or []:
            if isinstance(ref, str):
                refs.append(ref)
    for ref in refs:
        if ref.endswith(f"/{RESULT_ARTIFACT_NAME}") or ref.endswith(f"\\{RESULT_ARTIFACT_NAME}"):
            return (root / ref).resolve()
    return None


def _proof_for_task(root: Path, db_path: Path, task: dict[str, Any]) -> dict[str, Any]:
    events = _event_rows(db_path, str(task.get("task_id") or ""))
    event_types = [str(event.get("event_type") or "") for event in events]
    task_artifacts = _artifact_summary(root, list(task.get("artifacts") or []))
    event_artifact_refs = [
        ref
        for event in events
        for ref in list(event.get("artifacts") or [])
        if isinstance(ref, str)
    ]
    event_artifacts = _artifact_summary(root, event_artifact_refs)
    result_path = _result_artifact_path(root, task, events)
    result_payload = _read_json(result_path, {}) if result_path else {}
    result_artifacts = (
        result_payload.get("artifacts") if isinstance(result_payload.get("artifacts"), list) else []
    )
    result_output_paths = [
        item.get("path")
        for item in result_artifacts
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    ]
    result_output_summary = _artifact_summary(root, result_output_paths)

    created = "created" in event_types
    claimed = "claimed" in event_types and task.get("owner") == "Codex"
    started = "started" in event_types
    result_logged = any(event_type in RESULT_EVENT_TYPES for event_type in event_types)
    adapter_result_matches = bool(
        result_payload
        and result_payload.get("task_id") == task.get("task_id")
        and result_payload.get("run_id") == task.get("run_id")
        and result_payload.get("from") == "Codex"
    )
    task_artifact_exists = any(item["exists"] for item in task_artifacts)
    result_artifact_exists = bool(result_path and result_path.exists())
    result_outputs_exist = bool(result_output_summary) and all(
        item["exists"] and item["inside_repo"] for item in result_output_summary
    )
    completed_or_safely_blocked = task.get("status") in {"done", "blocked"} and result_logged
    complete = bool(
        created
        and claimed
        and started
        and completed_or_safely_blocked
        and result_artifact_exists
        and adapter_result_matches
        and (task_artifact_exists or result_outputs_exist)
    )

    return {
        "task_id": task.get("task_id"),
        "run_id": task.get("run_id"),
        "sender": task.get("sender"),
        "recipient": task.get("recipient"),
        "status": task.get("status"),
        "owner": task.get("owner"),
        "owner_instance": task.get("owner_instance"),
        "created_at": task.get("created_at"),
        "updated_at": task.get("updated_at"),
        "work_fingerprint": task.get("work_fingerprint"),
        "execution_constraints": task.get("execution_constraints") or {},
        "event_types": event_types,
        "task_created": created,
        "task_claimed_by_codex": claimed,
        "task_started_by_codex": started,
        "task_completed_or_safely_blocked": completed_or_safely_blocked,
        "result_logged": result_logged,
        "result_artifact_found": result_artifact_exists,
        "result_artifact_path": _rel(root, result_path) if result_path else None,
        "adapter_result_matches_task": adapter_result_matches,
        "adapter_event_type": result_payload.get("event_type") if isinstance(result_payload, dict) else None,
        "adapter_event_id": result_payload.get("event_id") if isinstance(result_payload, dict) else None,
        "task_artifacts": task_artifacts,
        "event_artifacts": event_artifacts,
        "adapter_output_artifacts": result_output_summary,
        "task_created_claimed_executed_artifact_logged": complete,
    }


def _proof_rank(proof: dict[str, Any]) -> tuple[int, datetime]:
    score = 0
    if proof.get("task_created_claimed_executed_artifact_logged"):
        score += 100
    if proof.get("status") == "done":
        score += 20
    if proof.get("adapter_event_type") == "proposal":
        score += 10
    return score, _parse_dt(str(proof.get("updated_at") or ""))


def build_mvp_agent_bus_lifecycle(vault_root: str | Path = ".") -> dict[str, Any]:
    """Inspect the local bus and Codex adapter artifacts without side effects."""

    root = Path(vault_root).resolve()
    db_path = root / BUS_DB_RELATIVE_PATH
    tasks = _task_rows(db_path)
    proofs = [_proof_for_task(root, db_path, task) for task in tasks]
    complete_proofs = [
        proof for proof in proofs if proof.get("task_created_claimed_executed_artifact_logged")
    ]
    selected = max(complete_proofs or proofs, key=_proof_rank, default=None)
    status = (
        "complete_for_one_codex_task_lifecycle"
        if selected and selected.get("task_created_claimed_executed_artifact_logged")
        else "partial_or_unverified"
    )
    selected_artifact_refs: list[str] = []
    if selected:
        for artifact_group in (
            selected.get("task_artifacts"),
            selected.get("event_artifacts"),
            selected.get("adapter_output_artifacts"),
        ):
            for artifact in artifact_group or []:
                if isinstance(artifact, dict) and artifact.get("exists") and artifact.get("path"):
                    selected_artifact_refs.append(str(artifact["path"]))
        if selected.get("result_artifact_path"):
            selected_artifact_refs.append(str(selected["result_artifact_path"]))

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "read_only": True,
        "bus_db_path": BUS_DB_RELATIVE_PATH.as_posix(),
        "bus_db_present": db_path.exists(),
        "codex_done_task_count": sum(1 for task in tasks if task.get("status") == "done"),
        "codex_blocked_task_count": sum(1 for task in tasks if task.get("status") == "blocked"),
        "proof_task": selected,
        "task_created_claimed_executed_artifact_logged": bool(
            selected and selected.get("task_created_claimed_executed_artifact_logged")
        ),
        "recent_candidate_count": len(proofs),
        "recent_candidates": [
            {
                "task_id": proof.get("task_id"),
                "status": proof.get("status"),
                "updated_at": proof.get("updated_at"),
                "result_artifact_path": proof.get("result_artifact_path"),
                "complete": proof.get("task_created_claimed_executed_artifact_logged"),
            }
            for proof in sorted(proofs, key=lambda item: _parse_dt(str(item.get("updated_at") or "")), reverse=True)[:8]
        ],
        "evidence_refs": _ordered_unique(
            [
                BUS_DB_RELATIVE_PATH.as_posix(),
                CODEX_RUNS_RELATIVE_DIR.as_posix(),
            ]
            + selected_artifact_refs
        ),
        "authority": {
            "read_only": True,
            "agent_bus_task_write_allowed": False,
            "task_claim_allowed": False,
            "task_status_update_allowed": False,
            "runtime_dispatch_allowed": False,
            "provider_calls_allowed": False,
            "browser_control_allowed": False,
            "host_mutation_allowed": False,
            "canonical_mutation_allowed": False,
            "files_modified": False,
        },
        "blockers": []
        if selected and selected.get("task_created_claimed_executed_artifact_logged")
        else ["codex_agent_bus_lifecycle_proof_not_found"],
    }


def format_mvp_agent_bus_lifecycle(payload: dict[str, Any]) -> str:
    proof = payload.get("proof_task") if isinstance(payload.get("proof_task"), dict) else {}
    lines = [
        "ChaseOS MVP Agent Bus Lifecycle",
        f"  status: {payload.get('status')}",
        f"  proof_task: {proof.get('task_id')}",
        f"  proof_task_status: {proof.get('status')}",
        f"  lifecycle_complete: {payload.get('task_created_claimed_executed_artifact_logged')}",
        "  boundary: read-only inspection; no task create, claim, status update, runtime dispatch, provider call, browser/host control, or canonical mutation.",
    ]
    return "\n".join(lines)
