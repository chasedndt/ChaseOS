"""Phase 10 temp-target approved upgrade executor proof.

This is the first target-effect proof for the Phase 10 real-target upgrade
contract. It is intentionally safe for temp targets only: it validates a
real-target approval scope, reserves an exact-once marker before target writes,
performs approved create-only operations, writes rollback/audit evidence, and can
immediately roll back created paths for proof. It does not select or mutate an
operator live target, invoke scaffold generation, call providers/connectors, use
Git, execute workflows, mutate host/release surfaces, or promote canonical truth.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.target_write_path_policy import validate_target_write_plan


MODEL_VERSION = "studio.approved_target_upgrade_executor.v1"
SURFACE_ID = "studio_approved_target_upgrade_executor"
PASS_ID = "phase10f-real-target-temp-target-executor-proof"
APPROVAL_SCOPE = "one_operator_selected_target_upgrade"
OPERATION = "workspace_upgrade_target_execution"
APPROVAL_RECORD_TYPE = "workspace_upgrade_approval_artifact"
APPROVAL_RELATIVE_DIR = Path("07_LOGS") / "Agent-Activity" / "_workspace_upgrade_approvals"
MARKER_RELATIVE_DIR = APPROVAL_RELATIVE_DIR / "_target_execution_markers"
EVIDENCE_RELATIVE_DIR = Path("07_LOGS") / "Studio-Graph-Views" / "target-upgrade-executions"

PREVIEW_STATUS = "preview_only"
READY_STATUS = "preflight_ready"
COMPLETE_STATUS = "approved_target_upgrade_execution_complete"
BLOCKED_STATUS = "blocked_approved_target_upgrade_execution"
DUPLICATE_BLOCKED_STATUS = "blocked_duplicate_target_upgrade_execution"
ROLLBACK_SUCCEEDED_STATUS = "rollback_succeeded"
ROLLBACK_FAILED_STATUS = "rollback_failed_operator_review_required"

PROTECTED_RELATIVE_PREFIXES = (
    "02_KNOWLEDGE/",
    "runtime/policy/",
    "runtime/workflows/registry/",
    ".obsidian/",
)
PROTECTED_RELATIVE_PATHS = {
    "06_AGENTS/Permission-Matrix.md",
    "06_AGENTS/Trust-Tiers.md",
    "06_AGENTS/Agent-Security-Model.md",
}
ALLOWED_OPERATIONS = {"create_directory", "create_anchor_file"}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _slug(identifier: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in identifier).strip("-") or "approval"


def _safe_json_path(vault: Path, base_relative: Path, identifier: str) -> Path:
    base = (vault / base_relative).resolve()
    path = (base / f"{_slug(identifier)}.json").resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:  # pragma: no cover - defensive after slugging
        raise ValueError(f"target upgrade executor path escapes base directory: {path}") from exc
    return path


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _write_json_create_only(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, default=str)


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def _approval_path(vault: Path, packet_id: str) -> Path:
    return _safe_json_path(vault, APPROVAL_RELATIVE_DIR, packet_id)


def _marker_path(vault: Path, packet_id: str) -> Path:
    return _safe_json_path(vault, MARKER_RELATIVE_DIR, packet_id)


def _evidence_paths(vault: Path, packet_id: str) -> dict[str, Path]:
    root = (vault / EVIDENCE_RELATIVE_DIR / _slug(packet_id)).resolve()
    return {
        "preflight_report": root / "preflight-report.json",
        "planned_writes": root / "planned-writes.json",
        "rollback_plan": root / "rollback-plan.json",
        "execution_audit": root / "execution-audit.json",
        "target_upgrade_execution": root / "target-upgrade-execution.json",
        "rollback_result": root / "rollback-result.json",
    }


def _normalize_target(target_path: str | Path) -> Path:
    target = Path(target_path).expanduser()
    return target.resolve()


def _planned_writes(material: dict[str, Any]) -> list[dict[str, Any]]:
    writes = material.get("planned_writes")
    return [item for item in writes if isinstance(item, dict)] if isinstance(writes, list) else []


def _current_target_fingerprint(target: Path) -> dict[str, Any]:
    fingerprint: dict[str, Any] = {"exists": target.exists(), "is_dir": target.is_dir()}
    try:
        stat_result = target.stat()
    except OSError:
        return fingerprint
    fingerprint["st_dev"] = stat_result.st_dev
    fingerprint["st_ino"] = stat_result.st_ino
    return fingerprint


def _target_fingerprint_has_required_platform_identity(target: Path, approved_fingerprint: Any) -> bool:
    if not isinstance(approved_fingerprint, dict):
        return False
    if not target.exists():
        return True
    return "st_dev" in approved_fingerprint and "st_ino" in approved_fingerprint


def _target_fingerprint_matches(target: Path, approved_fingerprint: Any) -> bool:
    if not isinstance(approved_fingerprint, dict):
        return False
    if "exists" not in approved_fingerprint or "is_dir" not in approved_fingerprint:
        return False
    current = _current_target_fingerprint(target)
    for key in ("exists", "is_dir", "st_dev", "st_ino"):
        if key in approved_fingerprint and approved_fingerprint.get(key) != current.get(key):
            return False
    return True


def _evidence_output_blockers(paths: dict[str, Path]) -> list[str]:
    return [f"evidence-output-already-exists:{name}" for name, path in paths.items() if path.exists()]


def _validate_approval(
    payload: dict[str, Any] | None,
    *,
    packet_id: str,
    target: Path,
) -> tuple[dict[str, bool], list[str], dict[str, Any], list[dict[str, Any]]]:
    material = payload.get("approved_material") if isinstance(payload, dict) and isinstance(payload.get("approved_material"), dict) else {}
    planned_writes = _planned_writes(material)
    expected_digest = _sha256_payload(material) if material else None
    target_from_approval = Path(str(material.get("target_path") or "")).expanduser().resolve() if material.get("target_path") else None
    checks = {
        "approval_artifact_present": payload is not None,
        "approval_record_type_valid": bool(payload and payload.get("record_type") == APPROVAL_RECORD_TYPE),
        "approval_packet_id_matches": bool(payload and payload.get("approval_packet_id") == packet_id),
        "operator_decision_approved": bool(payload and payload.get("operator_decision") == "approved"),
        "approval_scope_valid": bool(payload and payload.get("approval_scope") == APPROVAL_SCOPE),
        "operation_valid": material.get("operation") == OPERATION,
        "request_digest_matches": bool(payload and payload.get("request_digest_sha256") == expected_digest),
        "approval_not_consumed": bool(payload and payload.get("approval_decision_consumed") is False),
        "proof_temp_only_false": bool(payload and payload.get("proof_temp_only") is False),
        "target_workspace_writes_allowed": bool(
            payload
            and (
                payload.get("target_workspace_writes_allowed") is True
                or payload.get("target_workspace_writes_allowed_in_this_pass") is True
            )
        ),
        "target_path_matches_approval": target_from_approval == target,
        "target_is_directory": target.is_dir(),
        "target_fingerprint_present": isinstance(material.get("target_fingerprint"), dict),
        "target_fingerprint_has_required_platform_identity": _target_fingerprint_has_required_platform_identity(target, material.get("target_fingerprint")),
        "target_fingerprint_matches_current_target": _target_fingerprint_matches(target, material.get("target_fingerprint")),
        "planned_writes_present": bool(planned_writes),
    }
    blockers = [name for name, ok in checks.items() if not ok]
    return checks, blockers, material, planned_writes


def _is_protected(rel_path: str) -> bool:
    normalized = Path(rel_path).as_posix().lstrip("/")
    if normalized in PROTECTED_RELATIVE_PATHS:
        return True
    return any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in PROTECTED_RELATIVE_PREFIXES)


def _path_policy_blockers(target: Path, planned_writes: list[dict[str, Any]]) -> list[str]:
    policy_plan = [
        {
            "operation_id": item.get("operation_id", f"planned-write-{index}"),
            "operation_type": "create_file" if item.get("operation") == "create_anchor_file" else item.get("operation"),
            "relative_path": item.get("relative_path"),
        }
        for index, item in enumerate(planned_writes)
    ]
    policy_report = validate_target_write_plan(target, policy_plan)
    blockers: list[str] = [f"path-policy:{item}" for item in policy_report.get("blockers", [])]
    root = target.resolve()
    for item in planned_writes:
        rel_value = str(item.get("relative_path") or "").strip()
        operation = str(item.get("operation") or "").strip()
        if operation not in ALLOWED_OPERATIONS:
            blockers.append(f"unsupported-operation-blocked:{operation or '<missing>'}")
        if not rel_value:
            blockers.append("missing-relative-path")
            continue
        rel_path = Path(rel_value)
        if rel_path.is_absolute():
            blockers.append(f"absolute-planned-target-path-blocked:{rel_value}")
            continue
        if _is_protected(rel_value):
            blockers.append(f"protected-path-blocked:{Path(rel_value).as_posix()}")
        candidate = root / rel_path
        resolved_parent = candidate.parent.resolve()
        resolved_candidate = (resolved_parent / candidate.name).resolve(strict=False)
        try:
            resolved_candidate.relative_to(root)
        except ValueError:
            blockers.append(f"path-escapes-target-root:{Path(rel_value).as_posix()}")
            continue
        if candidate.exists():
            blockers.append(f"write-would-overwrite-existing-path:{Path(rel_value).as_posix()}")
    return list(dict.fromkeys(blockers))


def _build_rollback_plan(packet_id: str, planned_writes: list[dict[str, Any]], generated_at: str) -> dict[str, Any]:
    rollback_items: list[dict[str, Any]] = []
    for item in planned_writes:
        operation = item.get("operation")
        rel_path = str(item.get("relative_path") or "")
        if operation == "create_anchor_file":
            rollback_items.append({"undo_operation": "remove_created_file", "relative_path": rel_path})
        elif operation == "create_directory":
            rollback_items.append({"undo_operation": "remove_created_empty_directory", "relative_path": rel_path})
    return {
        "record_type": "target_upgrade_rollback_plan",
        "schema_version": MODEL_VERSION,
        "approval_packet_id": packet_id,
        "generated_at": generated_at,
        "generated_before_target_writes": True,
        "rollback_items": rollback_items,
        "rollback_deletes_preexisting_paths": False,
    }


def _reserve_marker(path: Path, payload: dict[str, Any]) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, default=str)
        return True
    except FileExistsError:
        return False


def _consume_approval(path: Path, payload: dict[str, Any], timestamp: str) -> None:
    updated = dict(payload)
    updated["approval_decision_consumed"] = True
    updated["consumed_by_pass"] = PASS_ID
    updated["consumed_at"] = timestamp
    _write_json(path, updated)


def _execute_create_only_writes(target: Path, planned_writes: list[dict[str, Any]], timestamp: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    created: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    for index, item in enumerate(planned_writes):
        operation = str(item.get("operation"))
        rel_path = Path(str(item.get("relative_path")))
        destination = target / rel_path
        attempt = {
            "index": index,
            "operation": operation,
            "relative_path": rel_path.as_posix(),
            "attempted_at": timestamp,
            "status": "pending",
        }
        if destination.exists():
            attempt["status"] = "blocked_existing_path"
            attempts.append(attempt)
            raise FileExistsError(rel_path.as_posix())
        if operation == "create_directory":
            destination.mkdir(parents=True, exist_ok=False)
            created.append({"type": "directory", "relative_path": rel_path.as_posix()})
            attempt["status"] = "created"
        elif operation == "create_anchor_file":
            destination.parent.mkdir(parents=True, exist_ok=True)
            content = str(item.get("content_preview") or f"# {destination.stem}\n\nChaseOS bootstrap anchor placeholder.\n")
            with destination.open("x", encoding="utf-8") as handle:
                handle.write(content)
            created.append({"type": "file", "relative_path": rel_path.as_posix(), "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()})
            attempt["status"] = "created"
        attempts.append(attempt)
    return created, attempts


def _rollback_created_paths(target: Path, created: list[dict[str, Any]], timestamp: str) -> dict[str, Any]:
    removed_files: list[str] = []
    removed_dirs: list[str] = []
    retained: list[str] = []
    failures: list[dict[str, str]] = []
    _target_resolved = target.resolve()
    for item in reversed(created):
        rel_path = str(item.get("relative_path"))
        path = target / rel_path
        # L-6 fix: verify resolved path stays inside target before any deletion
        try:
            path.resolve().relative_to(_target_resolved)
        except ValueError:
            failures.append({"relative_path": rel_path, "error": "path_escapes_target_boundary"})
            continue
        try:
            if item.get("type") == "file":
                if path.is_file() or path.is_symlink():
                    path.unlink()
                    removed_files.append(rel_path)
                else:
                    retained.append(rel_path)
            elif item.get("type") == "directory":
                if path.is_dir() and not any(path.iterdir()):
                    path.rmdir()
                    removed_dirs.append(rel_path)
                else:
                    retained.append(rel_path)
        except OSError as exc:
            failures.append({"relative_path": rel_path, "error": str(exc)})
    return {
        "record_type": "target_upgrade_rollback_result",
        "schema_version": MODEL_VERSION,
        "rolled_back_at": timestamp,
        "removed_files": removed_files,
        "removed_dirs": removed_dirs,
        "retained_paths": retained,
        "failures": failures,
        "removed_file_count": len(removed_files),
        "removed_dir_count": len(removed_dirs),
        "operator_follow_up_required": bool(failures),
    }


def _path_records(root: Path, paths: dict[str, Path]) -> dict[str, dict[str, Any]]:
    return {name: {"path": _rel(root, path), "exists": path.exists(), "is_file": path.is_file()} for name, path in paths.items()}


def build_approved_target_upgrade_executor(
    vault_root: str | Path,
    *,
    approval_packet_id: str,
    target_path: str | Path,
    execute: bool = False,
    rollback_after_execute: bool = False,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Preview or execute an approval-scoped create-only temp-target upgrade proof."""

    vault = Path(vault_root).resolve()
    target = _normalize_target(target_path)
    timestamp = generated_at or _now_utc()
    packet_id = str(approval_packet_id or "").strip()
    if not packet_id:
        raise ValueError("approval_packet_id is required")

    approval_path = _approval_path(vault, packet_id)
    marker_path = _marker_path(vault, packet_id)
    evidence_paths = _evidence_paths(vault, packet_id)
    approval_payload = _read_json(approval_path) if approval_path.is_file() else None
    checks, blockers, material, planned_writes = _validate_approval(approval_payload, packet_id=packet_id, target=target)
    blockers.extend(_path_policy_blockers(target, planned_writes))
    blockers.extend(_evidence_output_blockers(evidence_paths))
    if marker_path.exists():
        blockers.append("exact-once-marker-already-present")
    status = PREVIEW_STATUS if not execute else (DUPLICATE_BLOCKED_STATUS if marker_path.exists() else BLOCKED_STATUS)

    rollback_plan = _build_rollback_plan(packet_id, planned_writes, timestamp)
    preflight_report = {
        "record_type": "target_upgrade_preflight_report",
        "schema_version": MODEL_VERSION,
        "approval_packet_id": packet_id,
        "generated_at": timestamp,
        "target_path": str(target),
        "target_fingerprint": {
            "approved": material.get("target_fingerprint") if isinstance(material, dict) else None,
            "current": _current_target_fingerprint(target),
        },
        "checks": checks,
        "blockers": blockers,
        "execute_requested": execute,
        "rollback_after_execute_requested": rollback_after_execute,
    }

    if not execute or blockers:
        return {
            "ok": False,
            "title": "ChaseOS Studio Approved Target Upgrade Executor Proof",
            "status": status,
            "pass": PASS_ID,
            "surface_id": SURFACE_ID,
            "schema_version": MODEL_VERSION,
            "approval_packet_id": packet_id,
            "approval_artifact": {"path": _rel(vault, approval_path), "exists": approval_path.exists()},
            "exact_once_marker": {"path": _rel(vault, marker_path), "exists": marker_path.exists(), "reserved_before_target_writes": False},
            "planned_write_count": len(planned_writes),
            "planned_writes": planned_writes,
            "rollback_plan": rollback_plan,
            "readiness": {"checks": checks, "blockers": blockers, "target_workspace_writes_performed": False},
            "evidence_outputs": _path_records(vault, evidence_paths),
            "authority_boundary": {
                "preview_writes_performed": False,
                "target_workspace_writes_performed": False,
                "scaffold_execution_performed": False,
                "provider_calls_allowed": False,
                "connector_calls_allowed": False,
                "uses_git": False,
                "executes_workflows": False,
                "host_mutation_allowed": False,
                "release_mutation_allowed": False,
                "canonical_mutation_allowed": False,
            },
        }

    _write_json_create_only(evidence_paths["preflight_report"], preflight_report)
    _write_json_create_only(evidence_paths["planned_writes"], {"approval_packet_id": packet_id, "planned_writes": planned_writes})
    _write_json_create_only(evidence_paths["rollback_plan"], rollback_plan)
    marker_payload = {
        "record_type": "target_upgrade_execution_marker",
        "schema_version": MODEL_VERSION,
        "approval_packet_id": packet_id,
        "request_digest_sha256": approval_payload.get("request_digest_sha256") if approval_payload else None,
        "status": "reserved_before_target_writes",
        "reserved_at": timestamp,
        "target_path": str(target),
    }
    marker_reserved = _reserve_marker(marker_path, marker_payload)
    if not marker_reserved:
        blockers.append("exact-once-marker-already-present")
        return {
            "ok": False,
            "status": DUPLICATE_BLOCKED_STATUS,
            "readiness": {"checks": checks, "blockers": blockers, "target_workspace_writes_performed": False},
            "exact_once_marker": {"path": _rel(vault, marker_path), "exists": True, "reserved_before_target_writes": False},
        }

    _consume_approval(approval_path, approval_payload or {}, timestamp)
    created: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    execution_status = COMPLETE_STATUS
    rollback_result: dict[str, Any] | None = None
    try:
        created, attempts = _execute_create_only_writes(target, planned_writes, timestamp)
    except Exception as exc:  # pragma: no cover - policy preflight should prevent this in normal tests
        execution_status = "execution_failed_after_partial_write" if created else "execution_failed_before_target_write"
        rollback_result = _rollback_created_paths(target, created, timestamp)
        if rollback_result["failures"]:
            execution_status = ROLLBACK_FAILED_STATUS
        else:
            execution_status = ROLLBACK_SUCCEEDED_STATUS
        attempts.append({"status": "failed", "error": str(exc)})

    if rollback_after_execute:
        rollback_result = _rollback_created_paths(target, created, timestamp)
        execution_status = ROLLBACK_FAILED_STATUS if rollback_result["failures"] else ROLLBACK_SUCCEEDED_STATUS
        _write_json_create_only(evidence_paths["rollback_result"], {"approval_packet_id": packet_id, **rollback_result})

    target_effect_audit = {
        "target_path": str(target),
        "target_workspace_writes_performed": bool(created),
        "created_paths": created,
        "created_file_count": len([item for item in created if item.get("type") == "file"]),
        "created_dir_count": len([item for item in created if item.get("type") == "directory"]),
        "rollback_after_execute": rollback_after_execute,
    }
    audit = {
        "record_type": "target_upgrade_execution_audit",
        "schema_version": MODEL_VERSION,
        "approval_packet_id": packet_id,
        "generated_at": timestamp,
        "status": execution_status,
        "marker_reserved_before_target_writes": marker_reserved,
        "approval_consumed_after_marker_before_target_writes": True,
        "write_attempts": attempts,
        "target_effect_audit": target_effect_audit,
        "forbidden_authority": {
            "scaffold_execution_performed": False,
            "provider_calls_performed": False,
            "connector_calls_performed": False,
            "git_used": False,
            "workflow_executed": False,
            "host_mutation_performed": False,
            "release_mutation_performed": False,
            "canonical_mutation_performed": False,
        },
    }
    summary = {
        "record_type": "target_upgrade_execution_summary",
        "schema_version": MODEL_VERSION,
        "approval_packet_id": packet_id,
        "status": execution_status,
        "target_path": str(target),
        "planned_write_count": len(planned_writes),
        "created_path_count": len(created),
        "rollback_performed": rollback_result is not None,
        "target_effect_audit": target_effect_audit,
    }
    _write_json_create_only(evidence_paths["execution_audit"], audit)
    _write_json_create_only(evidence_paths["target_upgrade_execution"], summary)

    return {
        "ok": execution_status in {COMPLETE_STATUS, ROLLBACK_SUCCEEDED_STATUS},
        "title": "ChaseOS Studio Approved Target Upgrade Executor Proof",
        "status": execution_status,
        "pass": PASS_ID,
        "surface_id": SURFACE_ID,
        "schema_version": MODEL_VERSION,
        "approval_packet_id": packet_id,
        "approval_artifact": {"path": _rel(vault, approval_path), "exists": approval_path.exists()},
        "exact_once_marker": {"path": _rel(vault, marker_path), "exists": marker_path.exists(), "reserved_before_target_writes": marker_reserved},
        "planned_write_count": len(planned_writes),
        "planned_writes": planned_writes,
        "rollback_plan": rollback_plan,
        "rollback_result": rollback_result,
        "target_effect_audit": target_effect_audit,
        "readiness": {"checks": checks, "blockers": [], "target_workspace_writes_performed": bool(created)},
        "evidence_outputs": _path_records(vault, evidence_paths),
        "authority_boundary": {
            "preview_writes_performed": False,
            "target_workspace_writes_performed": bool(created),
            "scaffold_execution_performed": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "uses_git": False,
            "executes_workflows": False,
            "host_mutation_allowed": False,
            "release_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
    }
