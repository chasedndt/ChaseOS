"""N6 approval-gated terminal write executor.

This is the dedicated consumer for terminal write-lane approval requests. It is
CLI-owned and deliberately narrow: no Studio execution button/API, no shell
operators, no elevation, no provider calls, no Agent Bus writes, and no
canonical writeback.
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.chaser.terminal_write_executor_readiness import (
    build_terminal_write_executor_readiness,
)
from runtime.operator_surface import terminal_runs
from runtime.operator_surface.adapters.terminal_adapter import TerminalAdapter
from runtime.studio.service import StudioService


SURFACE = "terminal_write_executor"
SCHEMA_VERSION = "terminal_write_executor.v1"
MARKER_SCHEMA_VERSION = "terminal_write_execution_marker.v1"
SUPPORTED_WRITE_EXECUTABLES = frozenset({"mkdir", "touch", "copy", "cp"})


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _authority_flags(
    *,
    terminal_execution: bool = False,
    approval_consumption: bool = False,
    terminal_audit_write: bool = False,
    exact_once_marker_write: bool = False,
    host_mutation: bool = False,
) -> dict[str, bool]:
    return {
        "terminal_execution_now": terminal_execution,
        "terminal_audit_write_now": terminal_audit_write,
        "approval_consumption_now": approval_consumption,
        "exact_once_marker_write_now": exact_once_marker_write,
        "studio_execution_now": False,
        "agent_bus_write_now": False,
        "provider_call_now": False,
        "canonical_writeback_now": False,
        "external_upload_now": False,
        "host_mutation_now": host_mutation,
    }


def _blocked_payload(
    *,
    root: Path,
    approval_id: str,
    blockers: list[str],
    readiness: dict[str, Any] | None = None,
    status: str = "blocked",
) -> dict[str, Any]:
    return {
        "ok": False,
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "vault_root": str(root),
        "approval_id": approval_id,
        "status": status,
        "blockers": blockers,
        "readiness": readiness or {},
        "run_id": "",
        "audit_paths": {},
        "exact_once_marker_path": (readiness or {}).get("exact_once_marker_path", ""),
        "approval_status_after": (readiness or {}).get("approval_status", ""),
        "terminal_output_trusted": False,
        "trust_tier": "Tier 4",
        "authority": _authority_flags(),
    }


def _resolve_inside(root: Path, cwd: Path, token: str, *, label: str = "target") -> Path:
    if re.match(r"^[A-Za-z]:", token) and not Path(token).is_absolute():
        raise ValueError(f"{label} path escapes vault root: {token}")
    candidate = Path(token)
    if not candidate.is_absolute():
        candidate = cwd / candidate
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} path escapes vault root: {token}") from exc
    return resolved


def _validate_supported_write(readiness: dict[str, Any], root: Path) -> tuple[Path, tuple[str, ...], Path, Path | None]:
    classification = readiness.get("classification") if isinstance(readiness.get("classification"), dict) else {}
    tokens = tuple(str(token) for token in classification.get("tokens") or ())
    if not tokens:
        raise ValueError("approved command has no parsed tokens")

    executable = TerminalAdapter._normalize_executable(tokens[0])
    if executable not in SUPPORTED_WRITE_EXECUTABLES:
        raise ValueError(f"unsupported_n6_write_executable:{executable}")
    if executable in {"mkdir", "touch"} and len(tokens) != 2:
        raise ValueError(f"{executable} requires exactly one target path in the N6 executor")
    if executable in {"copy", "cp"} and len(tokens) != 3:
        raise ValueError(f"{executable} requires exactly one source path and one target path in the N6 executor")

    cwd = Path(str(readiness.get("cwd") or "")).resolve()
    if not cwd.exists() or not cwd.is_dir():
        raise ValueError(f"cwd is not an existing directory: {cwd}")
    try:
        cwd.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"cwd escapes vault root: {cwd}") from exc

    if executable in {"mkdir", "touch"}:
        if tokens[1].startswith("-"):
            raise ValueError(f"{executable} target must not be a flag")
        target = _resolve_inside(root, cwd, tokens[1], label="target")
        return cwd, tokens, target, None

    source_token, target_token = tokens[1], tokens[2]
    if source_token.startswith("-"):
        raise ValueError(f"{executable} source must not be a flag")
    if target_token.startswith("-"):
        raise ValueError(f"{executable} target must not be a flag")
    source = _resolve_inside(root, cwd, source_token, label="source")
    target = _resolve_inside(root, cwd, target_token, label="target")
    if not source.exists() or not source.is_file():
        raise ValueError(f"source file does not exist: {source}")
    if target.exists():
        raise ValueError(f"target already exists: {target}")
    if not target.parent.exists() or not target.parent.is_dir():
        raise ValueError(f"target parent does not exist: {target.parent}")
    return cwd, tokens, target, source


def _reserve_marker(marker_path: Path, payload: dict[str, Any]) -> None:
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    with marker_path.open("x", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)


def _write_marker(marker_path: Path, payload: dict[str, Any]) -> None:
    marker_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _execute_mkdir(target: Path, root: Path) -> tuple[int, str, str, bool]:
    if target.exists():
        return 1, "", f"target already exists: {target}", False
    target.mkdir(parents=False, exist_ok=False)
    rel_target = target.relative_to(root).as_posix()
    return 0, f"created directory: {rel_target}", "", True


def _execute_touch(target: Path, root: Path) -> tuple[int, str, str, bool]:
    if target.exists():
        return 1, "", f"target already exists: {target}", False
    if not target.parent.exists() or not target.parent.is_dir():
        return 1, "", f"target parent does not exist: {target.parent}", False
    with target.open("x", encoding="utf-8"):
        pass
    rel_target = target.relative_to(root).as_posix()
    return 0, f"created file: {rel_target}", "", True


def _execute_copy(source: Path, target: Path, root: Path) -> tuple[int, str, str, bool]:
    if not source.exists() or not source.is_file():
        return 1, "", f"source file does not exist: {source}", False
    if target.exists():
        return 1, "", f"target already exists: {target}", False
    if not target.parent.exists() or not target.parent.is_dir():
        return 1, "", f"target parent does not exist: {target.parent}", False
    shutil.copyfile(source, target)
    rel_source = source.relative_to(root).as_posix()
    rel_target = target.relative_to(root).as_posix()
    return 0, f"copied file: {rel_source} -> {rel_target}", "", True


def execute_terminal_write_approval(
    vault_root: str | Path,
    *,
    approval_id: str,
    expected_proposal_id: str = "",
    actor: str = "chaser-n6-terminal-executor",
    confirm_approved_terminal_write: bool = False,
    timeout_seconds: int = 15,
    max_output_chars: int = 4000,
) -> dict[str, Any]:
    """Consume one approved terminal write approval and perform a bounded write.

    The explicit confirmation flag is required so accidental CLI invocation does
    not mutate the host. Only the dedicated CLI path should call this helper.
    """

    root = Path(vault_root).resolve()
    approval_id = str(approval_id or "").strip()
    if not confirm_approved_terminal_write:
        return _blocked_payload(
            root=root,
            approval_id=approval_id,
            blockers=["explicit_approved_terminal_write_confirmation_required"],
        )

    readiness = build_terminal_write_executor_readiness(
        root,
        approval_id=approval_id,
        expected_proposal_id=expected_proposal_id,
        executor_implemented=True,
    )
    if not readiness.get("ok"):
        return _blocked_payload(
            root=root,
            approval_id=approval_id,
            blockers=list(readiness.get("blockers") or ["readiness_blocked"]),
            readiness=readiness,
        )

    try:
        cwd, tokens, target, source = _validate_supported_write(readiness, root)
    except ValueError as exc:
        return _blocked_payload(
            root=root,
            approval_id=approval_id,
            blockers=[str(exc)],
            readiness=readiness,
        )

    marker_path = root / str(readiness.get("exact_once_marker_path") or "")
    reserved_at = _now_iso()
    marker_payload = {
        "schema_version": MARKER_SCHEMA_VERSION,
        "status": "reserved",
        "approval_id": approval_id,
        "proposal_id": readiness.get("proposal_id") or "",
        "command": readiness.get("command") or "",
        "cwd": str(cwd),
        "target_path": target.relative_to(root).as_posix(),
        "reserved_at": reserved_at,
        "actor": actor,
        "terminal_output_trusted": False,
        "trust_tier": "Tier 4",
    }
    if source is not None:
        marker_payload["source_path"] = source.relative_to(root).as_posix()
    try:
        _reserve_marker(marker_path, marker_payload)
    except FileExistsError:
        return _blocked_payload(
            root=root,
            approval_id=approval_id,
            blockers=["exact_once_marker_already_present"],
            readiness=readiness,
            status="duplicate_blocked",
        )

    service = StudioService(root)
    request = service.get_approval(approval_id)
    if request is None:  # pragma: no cover - readiness already checked this.
        marker_payload["status"] = "blocked_after_marker_missing_approval"
        marker_payload["finished_at"] = _now_iso()
        _write_marker(marker_path, marker_payload)
        return _blocked_payload(
            root=root,
            approval_id=approval_id,
            blockers=["approval_request_missing_after_marker"],
            readiness=readiness,
        )

    started_at = _now_iso()
    request.status = "executing"
    request.execution_id = f"terminal-write-{approval_id}"
    request.execution_started_at = started_at
    request.execution_finished_at = None
    request.execution_status = None
    request.result_action_id = None
    request.execution_error = ""
    request.updated_at = started_at
    service._write_approval_record(request)

    command = str(readiness.get("command") or "")
    classification = readiness.get("classification") if isinstance(readiness.get("classification"), dict) else {}
    start = datetime.now(timezone.utc)
    stdout = ""
    stderr = ""
    exit_code = 1
    host_mutation = False
    try:
        executable = TerminalAdapter._normalize_executable(tokens[0])
        if executable == "mkdir":
            exit_code, stdout, stderr, host_mutation = _execute_mkdir(target, root)
        elif executable == "touch":
            exit_code, stdout, stderr, host_mutation = _execute_touch(target, root)
        elif executable in {"copy", "cp"} and source is not None:
            exit_code, stdout, stderr, host_mutation = _execute_copy(source, target, root)
        else:  # pragma: no cover - guarded by _validate_supported_write.
            stderr = f"unsupported_n6_write_executable:{executable}"
            exit_code = 1
    except Exception as exc:
        stderr = str(exc)
        exit_code = 1

    duration_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
    stdout_excerpt, stdout_truncated = TerminalAdapter._redact_and_truncate_with_flag(stdout, max_output_chars)
    stderr_excerpt, stderr_truncated = TerminalAdapter._redact_and_truncate_with_flag(stderr, max_output_chars)
    success = exit_code == 0
    record = terminal_runs.build_run_record(
        command=command,
        cwd=str(cwd),
        classification=classification,
        policy_decision="approved_write_executed" if success else "approved_write_execution_failed",
        actor=actor,
        exit_code=exit_code,
        stdout_excerpt=stdout_excerpt,
        stderr_excerpt=stderr_excerpt,
        duration_ms=duration_ms,
        output_truncated=stdout_truncated or stderr_truncated,
        redactions_applied="[REDACTED]" in (stdout_excerpt + stderr_excerpt),
        approval_id=approval_id,
    )
    audit_paths = terminal_runs.record_terminal_run(root, record)

    finished_at = _now_iso()
    request.status = "executed" if success else "execution_failed"
    request.execution_finished_at = finished_at
    request.execution_status = "completed" if success else "error"
    request.result_action_id = record["run_id"]
    request.execution_error = "" if success else stderr_excerpt
    request.updated_at = finished_at
    service._write_approval_record(request)

    marker_payload.update({
        "status": "executed" if success else "execution_failed",
        "finished_at": finished_at,
        "run_id": record["run_id"],
        "exit_code": exit_code,
        "audit_paths": audit_paths,
        "host_mutation_performed": host_mutation,
    })
    _write_marker(marker_path, marker_payload)

    return {
        "ok": success,
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "vault_root": str(root),
        "approval_id": approval_id,
        "proposal_id": readiness.get("proposal_id") or "",
        "status": "executed" if success else "execution_failed",
        "command": command,
        "cwd": str(cwd),
        "supported_write_executable": TerminalAdapter._normalize_executable(tokens[0]),
        "source_path": source.relative_to(root).as_posix() if source is not None else "",
        "target_path": target.relative_to(root).as_posix(),
        "exit_code": exit_code,
        "stdout": stdout_excerpt,
        "stderr": stderr_excerpt,
        "run_id": record["run_id"],
        "audit_paths": audit_paths,
        "exact_once_marker_path": str(readiness.get("exact_once_marker_path") or ""),
        "approval_status_after": request.status,
        "readiness": readiness,
        "terminal_output_trusted": False,
        "trust_tier": "Tier 4",
        "authority": _authority_flags(
            terminal_execution=True,
            approval_consumption=True,
            terminal_audit_write=True,
            exact_once_marker_write=True,
            host_mutation=host_mutation,
        ),
        "timeout_seconds": int(timeout_seconds),
        "warnings": [
            "terminal_output_is_tier4_untrusted",
            "n6_executor_supports_only_explicit_approved_single_step_file_system_write_commands",
            "no_shell_operators_no_elevation_no_provider_no_agent_bus_no_canonical_writeback",
        ],
    }
