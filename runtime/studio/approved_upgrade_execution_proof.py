"""Phase 10F6 approved workspace upgrade execution proof.

This is a proof-temp-only execution lane. It consumes one matching 10F5 approval
artifact exactly once, reserves the execution marker before proof outputs, and
writes evidence under controlled workspace proof roots. It does not create or
modify folders/files in the target workspace.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.upgrade_plan_approval_packet import (
    APPROVAL_RECORD_TYPE,
    APPROVAL_RELATIVE_DIR,
    APPROVAL_SCOPE,
    EVIDENCE_ROOT,
    FORBIDDEN_AUTHORITY,
    IDEMPOTENCY_MARKER_RELATIVE_DIR,
    MODEL_VERSION as APPROVAL_MODEL_VERSION,
    PROOF_OUTPUT_ROOT,
    build_upgrade_plan_approval_packet,
)


MODEL_VERSION = "studio.approved_upgrade_execution_proof.v1"
SURFACE_ID = "studio_approved_upgrade_execution_proof"
PASS_ID = "phase10f6-approved-upgrade-execution-proof"
READY_STATUS = "ready_for_approved_upgrade_execution_proof"
COMPLETE_STATUS = "approved_upgrade_execution_proof_complete"
BLOCKED_STATUS = "blocked_approved_upgrade_execution_proof"
DUPLICATE_BLOCKED_STATUS = "blocked_duplicate_workspace_upgrade_execution"
NEXT_RECOMMENDED_PASS = "phase11-chat-conversation-persistence-approval-contract"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_json_path(vault: Path, base_relative: Path, identifier: str) -> Path:
    base = (vault / base_relative).resolve()
    slug = "".join(char.lower() if char.isalnum() else "-" for char in identifier).strip("-")
    path = (base / f"{slug}.json").resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"workspace upgrade execution path escapes base directory: {path}") from exc
    return path


def _resolve_vault_relative_path(vault: Path, path_value: str) -> Path:
    path = Path(path_value)
    resolved = path.resolve() if path.is_absolute() else (vault / path).resolve()
    try:
        resolved.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError(f"workspace upgrade execution proof path escapes vault: {path_value}") from exc
    return resolved


def _path_record(vault: Path, path: Path) -> dict[str, Any]:
    return {
        "path": _rel(vault, path),
        "exists": path.exists(),
        "is_file": path.is_file(),
        "size_bytes": path.stat().st_size if path.is_file() else 0,
        "sha256": _sha256_file(path),
    }


def _approval_path(vault: Path, approval_packet_id: str) -> Path:
    return _safe_json_path(vault, APPROVAL_RELATIVE_DIR, approval_packet_id)


def _marker_path(vault: Path, approval_packet_id: str) -> Path:
    return _safe_json_path(vault, IDEMPOTENCY_MARKER_RELATIVE_DIR, approval_packet_id)


def _proof_paths(vault: Path, approval_packet_id: str) -> dict[str, Path]:
    root = vault / PROOF_OUTPUT_ROOT / approval_packet_id
    return {
        "proof_root": root,
        "planned_writes_manifest": root / "planned-writes.json",
        "rollback_plan": root / "rollback-plan.json",
        "execution_audit": root / "execution-audit.json",
        "dry_run_evidence": vault / EVIDENCE_ROOT / f"{approval_packet_id}-upgrade-dry-run.json",
        "execution_evidence": vault / EVIDENCE_ROOT / f"{approval_packet_id}-upgrade-execution.json",
    }


def _validate_approval(
    vault: Path,
    approval_packet_id: str,
    approval_payload: dict[str, Any] | None,
) -> tuple[dict[str, bool], list[str]]:
    payload = approval_payload or {}
    material = payload.get("approved_material") if isinstance(payload.get("approved_material"), dict) else {}
    preview = build_upgrade_plan_approval_packet(
        vault,
        target_path=material.get("target_path") or None,
        workspace_name=material.get("workspace_name") or None,
        write_approval=False,
    )
    expected = preview.get("approval_packet") or {}
    checks = {
        "approval_artifact_present": approval_payload is not None,
        "approval_record_type_valid": payload.get("record_type") == APPROVAL_RECORD_TYPE,
        "approval_packet_id_matches": payload.get("approval_packet_id") == approval_packet_id,
        "request_digest_matches": payload.get("request_digest_sha256") == expected.get("request_digest_sha256"),
        "operator_decision_approved": payload.get("operator_decision") == "approved",
        "approval_scope_valid": payload.get("approval_scope") == APPROVAL_SCOPE,
        "approval_not_consumed": payload.get("approval_decision_consumed") is False,
        "proof_temp_only": payload.get("proof_temp_only") is True,
        "target_workspace_writes_forbidden": payload.get("target_workspace_writes_allowed_in_this_pass") is False
        and payload.get("writes_target_workspace") is False,
        "approval_model_version_known": bool(payload.get("schema_version") == APPROVAL_MODEL_VERSION),
    }
    blockers = [name for name, ok in checks.items() if not ok]
    return checks, blockers


def _outputs_exist(paths: dict[str, Path]) -> bool:
    return any(path.exists() for path in paths.values())


def build_approved_upgrade_execution_proof(
    vault_root: str | Path,
    *,
    approval_packet_id: str,
    execute: bool = False,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Validate or execute the proof-temp-only approved upgrade proof."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    packet_id = str(approval_packet_id or "").strip()
    if not packet_id:
        raise ValueError("approval_packet_id is required")

    approval_path = _approval_path(vault, packet_id)
    marker_path = _marker_path(vault, packet_id)
    proof_paths = _proof_paths(vault, packet_id)
    approval_payload = _read_json(approval_path) if approval_path.is_file() else None
    marker_payload = _read_json(marker_path) if marker_path.is_file() else None
    checks, validation_blockers = _validate_approval(vault, packet_id, approval_payload)
    blockers = list(validation_blockers)

    if marker_path.exists():
        blockers.append("exact-once-marker-already-present")
    if _outputs_exist(proof_paths):
        blockers.append("future-proof-output-collision")
    if not execute:
        blockers.append("execute-flag-required")

    can_execute = not blockers
    marker_reserved_before_outputs = False
    written_outputs: dict[str, dict[str, Any]] = {}
    status = READY_STATUS if can_execute else BLOCKED_STATUS

    if execute and marker_path.exists():
        status = DUPLICATE_BLOCKED_STATUS

    if can_execute:
        material = (approval_payload or {}).get("approved_material") or {}
        planned_writes = material.get("planned_writes") if isinstance(material.get("planned_writes"), list) else []
        marker = {
            "record_type": "workspace_upgrade_execution_marker",
            "schema_version": MODEL_VERSION,
            "approval_packet_id": packet_id,
            "request_digest_sha256": (approval_payload or {}).get("request_digest_sha256"),
            "status": "reserved_before_proof_outputs",
            "reserved_at": timestamp,
            "proof_temp_only": True,
            "target_workspace_writes_allowed": False,
        }
        _write_json(marker_path, marker)
        marker_reserved_before_outputs = marker_path.is_file()

        dry_run = {
            "record_type": "workspace_upgrade_dry_run_evidence",
            "approval_packet_id": packet_id,
            "generated_at": timestamp,
            "planned_write_count": len(planned_writes),
            "planned_writes": planned_writes,
            "target_workspace_writes_performed": False,
            "proof_temp_only": True,
        }
        rollback = {
            "record_type": "workspace_upgrade_rollback_plan",
            "approval_packet_id": packet_id,
            "generated_at": timestamp,
            "rollback_scope": "proof_temp_outputs_only",
            "real_target_rollback_required": False,
            "paths_to_remove_if_rolled_back": [_rel(vault, path) for path in proof_paths.values()],
        }
        audit = {
            "record_type": "workspace_upgrade_execution_audit",
            "approval_packet_id": packet_id,
            "generated_at": timestamp,
            "marker_reserved_before_outputs": marker_reserved_before_outputs,
            "target_workspace_writes_performed": False,
            "scaffold_execution_performed": False,
            "planned_write_count": len(planned_writes),
        }
        execution = {
            "record_type": "workspace_upgrade_execution_evidence",
            "approval_packet_id": packet_id,
            "generated_at": timestamp,
            "status": COMPLETE_STATUS,
            "marker_reserved_before_outputs": marker_reserved_before_outputs,
            "target_workspace_writes_performed": False,
            "proof_temp_only": True,
            "planned_write_count": len(planned_writes),
        }
        _write_json(proof_paths["planned_writes_manifest"], {"approval_packet_id": packet_id, "planned_writes": planned_writes})
        _write_json(proof_paths["rollback_plan"], rollback)
        _write_json(proof_paths["execution_audit"], audit)
        _write_json(proof_paths["dry_run_evidence"], dry_run)
        _write_json(proof_paths["execution_evidence"], execution)

        consumed_approval = {
            **(approval_payload or {}),
            "approval_decision_consumed": True,
            "consumed_at": timestamp,
            "consumed_by_pass": PASS_ID,
            "execution_marker_path": _rel(vault, marker_path),
            "execution_evidence_path": _rel(vault, proof_paths["execution_evidence"]),
        }
        _write_json(approval_path, consumed_approval)

        complete_marker = {
            **marker,
            "status": COMPLETE_STATUS,
            "completed_at": timestamp,
            "marker_reserved_before_outputs": marker_reserved_before_outputs,
            "written_outputs": {key: _rel(vault, path) for key, path in proof_paths.items()},
        }
        _write_json(marker_path, complete_marker)
        status = COMPLETE_STATUS
        written_outputs = {key: _path_record(vault, path) for key, path in proof_paths.items()}

    return {
        "ok": status == COMPLETE_STATUS,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": status,
        "title": "ChaseOS Studio Approved Upgrade Execution Proof",
        "generated_at": timestamp,
        "vault_root": str(vault),
        "approval_packet_id": packet_id,
        "approval_artifact": {
            "path": _rel(vault, approval_path),
            "exists": approval_path.is_file(),
            "record_type": (approval_payload or {}).get("record_type"),
        },
        "exact_once_marker": {
            "path": _rel(vault, marker_path),
            "exists": marker_path.exists(),
            "status": (_read_json(marker_path) or marker_payload or {}).get("status") if marker_path.exists() else None,
            "reserved_before_outputs": marker_reserved_before_outputs,
        },
        "checks": checks,
        "proof_outputs": {
            key: _path_record(vault, path)
            for key, path in proof_paths.items()
        },
        "written_outputs": written_outputs,
        "authority_boundary": {
            "approved_execution_proof": True,
            "execute_requested": execute,
            "proof_temp_only": True,
            "writes_proof_outputs": status == COMPLETE_STATUS,
            "writes_execution_marker": status == COMPLETE_STATUS,
            **FORBIDDEN_AUTHORITY,
            "reserves_idempotency_marker": status == COMPLETE_STATUS,
            "consumes_approval_decision": status == COMPLETE_STATUS,
        },
        "readiness": {
            "approved_upgrade_execution_proof_complete": status == COMPLETE_STATUS,
            "duplicate_execution_blocked": status == DUPLICATE_BLOCKED_STATUS,
            "marker_reserved_before_outputs": marker_reserved_before_outputs,
            "target_workspace_writes_performed": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "blockers": list(dict.fromkeys(blockers)),
        },
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }


def get_approved_upgrade_execution_proof(vault_root: str | Path, **kwargs: Any) -> dict[str, Any]:
    return build_approved_upgrade_execution_proof(vault_root, **kwargs)
