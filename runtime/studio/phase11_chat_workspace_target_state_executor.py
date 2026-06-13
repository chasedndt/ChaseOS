"""Phase 11 Chat workspace target-state executor.

This executor applies one approved native Studio Chat workspace proposal record
into local Studio Chat state. It creates only native state JSON records. It does
not create Discord threads, call Discord APIs/webhooks, send chat messages,
write Agent Bus tasks, mutate runtime boards, mutate schedules, call providers,
read credentials, or write canonical memory/state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.phase11_chat_native_state import (
    FOLDER_STATE_DIR,
    STATE_ROOT,
    THREAD_STATE_DIR,
    WORKSPACE_STATE_DIR,
    folder_state_path,
    safe_state_id,
    thread_state_path,
    workspace_state_path,
)
from runtime.studio.phase11_chat_workspace_proposal_writer import PROPOSAL_KINDS, PROPOSAL_ROOT


MODEL_VERSION = "studio.phase11_chat_workspace_target_state_executor.v1"
SURFACE_ID = "phase11_chat_workspace_target_state_executor"
PASS_ID = "studio-runtime-chat-workspace-target-state-executor"
STATUS = "COMPLETE / TARGET-STATE-WRITTEN / VERIFIED / NATIVE CHAT STATE ONLY"
NEXT_RECOMMENDED_PASS = "studio-runtime-chat-route-state-and-message-draft-surface"
MARKER_DIR = Path("runtime/studio/approvals/_chat_workspace_target_state_markers")
AUDIT_DIR = Path("07_LOGS") / "Agent-Activity"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _safe_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, f"proposal_record_unreadable:{type(exc).__name__}"
    except json.JSONDecodeError as exc:
        return None, f"proposal_record_json_malformed:{exc}"
    if not isinstance(payload, dict):
        return None, "proposal_record_json_not_object"
    return payload, None


def _authority() -> dict[str, bool]:
    return {
        "native_chat_workspace_state_write_allowed": True,
        "native_chat_folder_state_write_allowed": True,
        "native_chat_thread_state_write_allowed": True,
        "proposal_record_status_mutation_allowed": True,
        "exact_once_marker_write_allowed": True,
        "chat_message_send_allowed": False,
        "chat_transcript_write_allowed": False,
        "discord_api_calls_allowed": False,
        "discord_thread_create_allowed": False,
        "webhook_calls_allowed": False,
        "agent_bus_task_write_allowed": False,
        "runtime_board_write_allowed": False,
        "runtime_dispatch_allowed": False,
        "schedule_mutation_allowed": False,
        "provider_calls_allowed": False,
        "credential_values_visible": False,
        "canonical_mutation_allowed": False,
    }


def _blocked_effects() -> dict[str, bool]:
    return {
        "chat_message_sent": False,
        "chat_transcript_written": False,
        "discord_api_called": False,
        "discord_thread_created": False,
        "webhook_call_performed": False,
        "agent_bus_task_written": False,
        "runtime_board_written": False,
        "runtime_dispatched": False,
        "schedule_mutated": False,
        "provider_call_performed": False,
        "credential_value_read": False,
        "canonical_mutation_performed": False,
    }


def _proposal_path(vault: Path, proposal_path: str | None, proposal_id: str | None) -> tuple[Path | None, list[str]]:
    blockers: list[str] = []
    raw = str(proposal_path or "").replace("\\", "/").strip()
    if not raw and proposal_id:
        raw = f"{PROPOSAL_ROOT}/{safe_state_id(proposal_id, 'proposal')}.json"
    if not raw:
        blockers.append("proposal_path_or_id_required")
        return None, blockers
    if not raw.startswith(f"{PROPOSAL_ROOT}/"):
        blockers.append("proposal_path_not_workspace_proposal_root")
    if not raw.endswith(".json"):
        blockers.append("proposal_path_not_json")
    abs_path = (vault / raw).resolve()
    try:
        abs_path.relative_to((vault / PROPOSAL_ROOT).resolve())
    except ValueError:
        blockers.append("proposal_path_escapes_workspace_proposal_root")
    try:
        abs_path.relative_to(vault.resolve())
    except ValueError:
        blockers.append("proposal_path_escapes_vault")
    return abs_path, blockers


def _validate_proposal(
    *,
    proposal: dict[str, Any] | None,
    expected_proposal_digest: str,
) -> list[str]:
    blockers: list[str] = []
    payload = proposal or {}
    proposal_kind = str(payload.get("proposal_kind") or "")
    proposal_digest = str(payload.get("proposal_digest") or "")
    if not payload:
        return ["proposal_record_missing_or_unreadable"]
    if proposal_kind not in PROPOSAL_KINDS:
        blockers.append("proposal_kind_unsupported")
    if str(payload.get("status") or "") != "approved_proposal_recorded":
        blockers.append("proposal_status_not_approved_recorded")
    if payload.get("approval_consumed") is not True:
        blockers.append("proposal_approval_not_consumed")
    if not str(payload.get("approval_id") or ""):
        blockers.append("proposal_approval_id_missing")
    if not str(payload.get("approval_consumption_digest") or ""):
        blockers.append("proposal_consumption_digest_missing")
    if payload.get("target_state_executor_required") is not True:
        blockers.append("proposal_missing_target_state_executor_required")
    if not proposal_digest:
        blockers.append("proposal_digest_missing")
    if expected_proposal_digest and proposal_digest and expected_proposal_digest != proposal_digest:
        blockers.append("proposal_digest_mismatch")
    if not str(payload.get("workspace_id") or ""):
        blockers.append("workspace_id_missing")
    if proposal_kind in {"create_folder", "create_thread"} and not str(payload.get("folder_id") or ""):
        blockers.append("folder_id_missing")
    if proposal_kind == "create_thread" and not str(payload.get("thread_id") or ""):
        blockers.append("thread_id_missing")
    if proposal_kind == "create_thread" and not str(payload.get("runtime_id") or ""):
        blockers.append("runtime_id_missing")
    for key, expected in _blocked_effects().items():
        if key in payload and bool(payload.get(key)) is not expected:
            blockers.append(f"proposal_blocked_effect_flag_not_false:{key}")
    return blockers


def _state_records_for_proposal(vault: Path, proposal: dict[str, Any]) -> dict[str, dict[str, Any]]:
    kind = str(proposal.get("proposal_kind") or "")
    workspace_id = safe_state_id(str(proposal.get("workspace_id") or ""), "workspace")
    folder_id = safe_state_id(str(proposal.get("folder_id") or ""), "folder")
    thread_id = safe_state_id(str(proposal.get("thread_id") or ""), "thread")
    now = _now_utc()
    base = {
        "schema_version": "phase11_chat_native_state.v1",
        "source_surface": SURFACE_ID,
        "source_proposal_id": proposal.get("proposal_id"),
        "source_proposal_digest": proposal.get("proposal_digest"),
        "approval_id": proposal.get("approval_id"),
        "approval_consumption_digest": proposal.get("approval_consumption_digest"),
        "created_at_utc": now,
        "updated_at_utc": now,
        "native_state_persisted": True,
        **_blocked_effects(),
    }
    records: dict[str, dict[str, Any]] = {}
    if kind == "create_workspace":
        records["workspace"] = {
            **base,
            "record_type": "workspace",
            "workspace_id": workspace_id,
            "label": str(proposal.get("title") or workspace_id.replace("-", " ").title()),
            "workspace_kind": "operator_created_chat_workspace",
            "workspace_mode_hint": str(proposal.get("workspace_mode_hint") or "runtime_agent_ops"),
            "context_paths": list(proposal.get("context_paths") or []),
            "folder_ids": [],
            "runtime_lanes": [],
            "board_targets": [],
        }
    if kind in {"create_folder", "create_thread"}:
        records["folder"] = {
            **base,
            "record_type": "folder",
            "workspace_id": workspace_id,
            "folder_id": folder_id,
            "label": str(proposal.get("title") or folder_id.replace("-", " ").title()),
            "context_paths": list(proposal.get("context_paths") or []),
        }
    if kind == "create_thread":
        records["thread"] = {
            **base,
            "record_type": "thread",
            "thread_id": thread_id,
            "workspace_id": workspace_id,
            "folder_id": folder_id,
            "title": str(proposal.get("title") or thread_id.replace("-", " ").title()),
            "thread_kind": "operator_created_runtime_thread",
            "runtime_id": str(proposal.get("runtime_id") or ""),
            "transport_channel_key": str(proposal.get("transport_channel_key") or ""),
            "native_route_preview": str(proposal.get("native_route_preview") or ""),
            "context_paths": list(proposal.get("context_paths") or []),
            "proposal_targets": ["native_chat_state"],
        }
    return records


def _state_paths(vault: Path, proposal: dict[str, Any]) -> dict[str, Path]:
    workspace_id = safe_state_id(str(proposal.get("workspace_id") or ""), "workspace")
    folder_id = safe_state_id(str(proposal.get("folder_id") or ""), "folder")
    thread_id = safe_state_id(str(proposal.get("thread_id") or ""), "thread")
    paths: dict[str, Path] = {}
    kind = str(proposal.get("proposal_kind") or "")
    if kind == "create_workspace":
        paths["workspace"] = workspace_state_path(vault, workspace_id)
    if kind in {"create_folder", "create_thread"}:
        paths["folder"] = folder_state_path(vault, workspace_id, folder_id)
    if kind == "create_thread":
        paths["thread"] = thread_state_path(vault, thread_id)
    return paths


def _summary(
    *,
    proposal: dict[str, Any] | None,
    proposal_path: str,
    expected_proposal_digest: str,
    target_state_digest: str = "",
    workspace_state_written: bool = False,
    folder_state_written: bool = False,
    thread_state_written: bool = False,
    proposal_record_mutated: bool = False,
    exact_once_marker_written: bool = False,
    duplicate_blocked_before_state_write: bool = False,
    blocker_count: int = 0,
) -> dict[str, Any]:
    payload = proposal or {}
    return {
        "proposal_path": proposal_path or None,
        "proposal_id": payload.get("proposal_id"),
        "proposal_kind": payload.get("proposal_kind"),
        "proposal_digest": payload.get("proposal_digest"),
        "expected_proposal_digest_provided": bool(expected_proposal_digest),
        "target_state_digest": target_state_digest or None,
        "workspace_id": payload.get("workspace_id"),
        "folder_id": payload.get("folder_id"),
        "thread_id": payload.get("thread_id"),
        "runtime_id": payload.get("runtime_id"),
        "native_chat_state_written": workspace_state_written or folder_state_written or thread_state_written,
        "workspace_state_written": workspace_state_written,
        "folder_state_written": folder_state_written,
        "thread_state_written": thread_state_written,
        "proposal_record_mutated": proposal_record_mutated,
        "exact_once_marker_written": exact_once_marker_written,
        "duplicate_blocked_before_state_write": duplicate_blocked_before_state_write,
        "chat_workspace_created": workspace_state_written,
        "chat_folder_created": folder_state_written,
        "chat_thread_created": thread_state_written,
        **_blocked_effects(),
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        "blocker_count": blocker_count,
    }


def _blocked_payload(
    *,
    vault: Path,
    proposal_path: str,
    expected_proposal_digest: str,
    proposal: dict[str, Any] | None,
    marker_path: Path | None,
    blockers: list[str],
) -> dict[str, Any]:
    unique_blockers = list(dict.fromkeys(blockers))
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": "BLOCKED / TARGET-STATE / NO NATIVE CHAT STATE WRITE",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": False,
        "approval_gated": True,
        "summary": _summary(
            proposal=proposal,
            proposal_path=proposal_path,
            expected_proposal_digest=expected_proposal_digest,
            duplicate_blocked_before_state_write="exact_once_marker_already_present" in unique_blockers,
            blocker_count=len(unique_blockers),
        ),
        "digest_proof": {
            "expected_proposal_digest": expected_proposal_digest or None,
            "proposal_digest": (proposal or {}).get("proposal_digest"),
            "proposal_digest_matched": False,
            "target_state_digest": None,
        },
        "exact_once_marker": {
            "marker_path": _rel(vault, marker_path) if marker_path else None,
            "marker_written": False,
            "duplicate_blocked_before_state_write": "exact_once_marker_already_present" in unique_blockers,
        },
        "state_writes": {
            "state_root": STATE_ROOT.as_posix(),
            "workspace_state_written": False,
            "folder_state_written": False,
            "thread_state_written": False,
            "proposal_record_mutated": False,
            "written_paths": [],
            **_blocked_effects(),
        },
        "audit_record": {
            "audit_written": False,
            "audit_record_path": None,
        },
        "authority": _authority(),
        "blocked_reasons": unique_blockers,
    }


def _marker_payload(
    *,
    status: str,
    proposal_id: str,
    proposal_digest: str,
    target_state_digest: str,
    execution_id: str,
    proposal_path: str,
    written_paths: list[str],
    operator_id: str,
    error: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": "phase11_chat_workspace_target_state_marker.v1",
        "status": status,
        "proposal_id": proposal_id,
        "proposal_digest": proposal_digest,
        "target_state_digest": target_state_digest,
        "execution_id": execution_id,
        "pass": PASS_ID,
        "surface": SURFACE_ID,
        "proposal_path": proposal_path,
        "written_paths": written_paths,
        "operator_id": operator_id,
        **_blocked_effects(),
        "error": error,
        "updated_at_utc": _now_utc(),
    }


def _next_audit_path(vault: Path, target_state_digest: str) -> Path:
    root = vault / AUDIT_DIR
    root.mkdir(parents=True, exist_ok=True)
    base = root / f"{PASS_ID}-{target_state_digest[:20]}.md"
    if not base.exists():
        return base
    for index in range(2, 100):
        candidate = root / f"{PASS_ID}-{target_state_digest[:20]}-{index}.md"
        if not candidate.exists():
            return candidate
    raise RuntimeError("could not allocate workspace target-state audit path")


def _write_audit(
    *,
    vault: Path,
    proposal: dict[str, Any],
    proposal_path: str,
    execution_id: str,
    target_state_digest: str,
    written_paths: list[str],
    operator_id: str,
) -> str:
    path = _next_audit_path(vault, target_state_digest)
    text = "\n".join(
        [
            "---",
            "type: agent-activity",
            "runtime: Codex",
            f"pass_id: {PASS_ID}",
            f"proposal_id: {proposal.get('proposal_id') or 'missing'}",
            f"execution_id: {execution_id}",
            f"status: {STATUS}",
            "---",
            "",
            "# Phase 11 Chat Workspace Target-State Executor",
            "",
            f"operator_id: {operator_id}",
            f"proposal_path: {proposal_path}",
            f"proposal_digest: {proposal.get('proposal_digest') or 'missing'}",
            f"target_state_digest: {target_state_digest}",
            f"proposal_kind: {proposal.get('proposal_kind') or 'missing'}",
            f"workspace_id: {proposal.get('workspace_id') or 'missing'}",
            f"folder_id: {proposal.get('folder_id') or 'missing'}",
            f"thread_id: {proposal.get('thread_id') or 'missing'}",
            f"runtime_id: {proposal.get('runtime_id') or 'missing'}",
            "native_chat_state_written: true",
            "discord_api_called: false",
            "discord_thread_created: false",
            "agent_bus_task_written: false",
            "runtime_board_written: false",
            "schedule_mutated: false",
            "provider_call_performed: false",
            "credential_value_read: false",
            "canonical_mutation_performed: false",
            "",
            "## Written Paths",
            "",
            *(f"- `{item}`" for item in written_paths),
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")
    return _rel(vault, path)


def execute_phase11_chat_workspace_target_state(
    vault_root: str | Path,
    *,
    proposal_path: str | None = None,
    proposal_id: str | None = None,
    expected_proposal_digest: str | None = None,
    operator_id: str = "operator",
    operator_target_state_statement: str | None = None,
) -> dict[str, Any]:
    """Apply one approved workspace proposal record to native Studio Chat state."""

    vault = Path(vault_root).resolve()
    expected = str(expected_proposal_digest or "").strip()
    operator = str(operator_id or "operator").strip() or "operator"
    statement = " ".join(str(operator_target_state_statement or "").strip().split())
    blockers: list[str] = []
    if not expected:
        blockers.append("expected_proposal_digest_required")
    if not statement:
        blockers.append("operator_target_state_statement_required")

    proposal_abs, path_blockers = _proposal_path(vault, proposal_path, proposal_id)
    blockers.extend(path_blockers)
    proposal: dict[str, Any] | None = None
    proposal_error = None
    if proposal_abs is None or not proposal_abs.exists():
        blockers.append("proposal_record_not_found")
    else:
        proposal, proposal_error = _safe_json(proposal_abs)
        if proposal_error:
            blockers.append(proposal_error)
        blockers.extend(_validate_proposal(proposal=proposal, expected_proposal_digest=expected))

    effective_proposal_path = _rel(vault, proposal_abs) if proposal_abs else str(proposal_path or "")
    proposal_key = safe_state_id(str((proposal or {}).get("proposal_id") or proposal_id or ""), "proposal")
    marker_path = vault / MARKER_DIR / f"{proposal_key}.json"
    if marker_path.exists():
        blockers.append("exact_once_marker_already_present")

    state_paths = _state_paths(vault, proposal or {}) if proposal else {}
    for kind, path in state_paths.items():
        if path.exists():
            blockers.append(f"{kind}_state_target_collision")

    if blockers:
        return _blocked_payload(
            vault=vault,
            proposal_path=effective_proposal_path,
            expected_proposal_digest=expected,
            proposal=proposal,
            marker_path=marker_path,
            blockers=blockers,
        )

    assert proposal is not None
    assert proposal_abs is not None

    records = _state_records_for_proposal(vault, proposal)
    target_state_material = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "proposal_path": effective_proposal_path,
        "proposal_digest": proposal.get("proposal_digest"),
        "records": records,
    }
    target_state_digest = _sha256_text(_canonical_json(target_state_material))
    execution_id = f"chat-workspace-target-state-{target_state_digest[:20]}"
    written_paths: list[str] = []

    try:
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text(
            json.dumps(
                _marker_payload(
                    status="executing",
                    proposal_id=str(proposal.get("proposal_id") or ""),
                    proposal_digest=str(proposal.get("proposal_digest") or ""),
                    target_state_digest=target_state_digest,
                    execution_id=execution_id,
                    proposal_path=effective_proposal_path,
                    written_paths=[],
                    operator_id=operator,
                ),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        for kind, record in records.items():
            path = state_paths[kind]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            written_paths.append(_rel(vault, path))

        updated_proposal = dict(proposal)
        updated_proposal.update(
            {
                "status": "target_state_applied",
                "target_state_applied": True,
                "target_state_applied_by": SURFACE_ID,
                "target_state_execution_id": execution_id,
                "target_state_digest": target_state_digest,
                "target_state_applied_at_utc": _now_utc(),
                "native_state_paths": written_paths,
                "chat_workspace_created": "workspace" in records,
                "chat_folder_created": "folder" in records,
                "chat_thread_created": "thread" in records,
                **_blocked_effects(),
            }
        )
        proposal_abs.write_text(json.dumps(updated_proposal, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written_paths.append(effective_proposal_path)

        marker_path.write_text(
            json.dumps(
                _marker_payload(
                    status="executed",
                    proposal_id=str(proposal.get("proposal_id") or ""),
                    proposal_digest=str(proposal.get("proposal_digest") or ""),
                    target_state_digest=target_state_digest,
                    execution_id=execution_id,
                    proposal_path=effective_proposal_path,
                    written_paths=written_paths,
                    operator_id=operator,
                ),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        audit_path = _write_audit(
            vault=vault,
            proposal=updated_proposal,
            proposal_path=effective_proposal_path,
            execution_id=execution_id,
            target_state_digest=target_state_digest,
            written_paths=written_paths,
            operator_id=operator,
        )
    except Exception as exc:
        error = str(exc)
        try:
            marker_path.parent.mkdir(parents=True, exist_ok=True)
            marker_path.write_text(
                json.dumps(
                    _marker_payload(
                        status="execution_failed",
                        proposal_id=str((proposal or {}).get("proposal_id") or ""),
                        proposal_digest=str((proposal or {}).get("proposal_digest") or ""),
                        target_state_digest=target_state_digest,
                        execution_id=execution_id,
                        proposal_path=effective_proposal_path,
                        written_paths=written_paths,
                        operator_id=operator,
                        error=error,
                    ),
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
        except Exception:
            pass
        failed = _blocked_payload(
            vault=vault,
            proposal_path=effective_proposal_path,
            expected_proposal_digest=expected,
            proposal=proposal,
            marker_path=marker_path,
            blockers=[f"workspace_target_state_execution_failed:{error}"],
        )
        failed["status"] = "FAILED / TARGET-STATE / PARTIAL EXECUTION CHECK REQUIRED"
        return failed

    workspace_written = "workspace" in records
    folder_written = "folder" in records
    thread_written = "thread" in records
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": False,
        "approval_gated": True,
        "summary": _summary(
            proposal=updated_proposal,
            proposal_path=effective_proposal_path,
            expected_proposal_digest=expected,
            target_state_digest=target_state_digest,
            workspace_state_written=workspace_written,
            folder_state_written=folder_written,
            thread_state_written=thread_written,
            proposal_record_mutated=True,
            exact_once_marker_written=True,
        ),
        "digest_proof": {
            "expected_proposal_digest": expected,
            "proposal_digest": proposal.get("proposal_digest"),
            "proposal_digest_matched": expected == proposal.get("proposal_digest"),
            "target_state_digest": target_state_digest,
            "target_state_material": target_state_material,
            "result_digest": _sha256_text(
                _canonical_json(
                    {
                        "execution_id": execution_id,
                        "proposal_path": effective_proposal_path,
                        "target_state_digest": target_state_digest,
                        "written_paths": written_paths,
                    }
                )
            ),
        },
        "exact_once_marker": {
            "marker_path": _rel(vault, marker_path),
            "marker_written": True,
            "marker_status": "executed",
            "duplicate_blocked_before_state_write": True,
        },
        "state_writes": {
            "state_root": STATE_ROOT.as_posix(),
            "workspace_state_dir": WORKSPACE_STATE_DIR.as_posix(),
            "folder_state_dir": FOLDER_STATE_DIR.as_posix(),
            "thread_state_dir": THREAD_STATE_DIR.as_posix(),
            "workspace_state_written": workspace_written,
            "folder_state_written": folder_written,
            "thread_state_written": thread_written,
            "proposal_record_mutated": True,
            "written_paths": written_paths,
            **_blocked_effects(),
        },
        "audit_record": {
            "audit_written": True,
            "audit_record_path": audit_path,
        },
        "authority": _authority(),
        "blocked_reasons": [],
    }


def format_phase11_chat_workspace_target_state_executor(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    state_writes = payload.get("state_writes") or {}
    lines = [
        "Phase 11 Chat Workspace Target-State Executor",
        f"Status: {payload.get('status')}",
        f"Proposal path: {summary.get('proposal_path') or 'none'}",
        f"Proposal digest: {summary.get('proposal_digest') or 'missing'}",
        f"Native Chat state written: {summary.get('native_chat_state_written')}",
        f"Workspace state written: {summary.get('workspace_state_written')}",
        f"Folder state written: {summary.get('folder_state_written')}",
        f"Thread state written: {summary.get('thread_state_written')}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers)
    written_paths = state_writes.get("written_paths") or []
    if written_paths:
        lines.append("Written paths:")
        lines.extend(f"- {item}" for item in written_paths)
    lines.append(
        "Boundary: native Studio Chat state only; no Discord API/thread/webhook, "
        "message send, Agent Bus task, runtime board, schedule, provider, credential, "
        "or canonical mutation."
    )
    return "\n".join(lines)
