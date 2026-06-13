"""Phase 10F5 workspace upgrade approval packet.

This surface turns the read-only 10F1-10F4 import/setup previews into a
governed approval packet for a future proof-only upgrade execution. It may write
one scoped approval artifact when explicitly requested, but it never mutates the
target workspace or invokes scaffold execution.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.chaseos_bootstrap_wizard_preview import (
    REQUIRED_DIRS,
    REQUIRED_FILES,
    build_chaseos_bootstrap_wizard_preview,
)
from runtime.studio.general_markdown_inference_preview import build_general_markdown_inference_preview
from runtime.studio.obsidian_vault_detection import build_obsidian_vault_detection
from runtime.studio.open_folder_compatibility_readiness import build_open_folder_compatibility_readiness


MODEL_VERSION = "studio.upgrade_plan_approval_packet.v1"
SURFACE_ID = "studio_upgrade_plan_approval_packet"
PASS_ID = "phase10f5-upgrade-plan-approval-packet"
NEXT_RECOMMENDED_PASS = "phase10f6-approved-upgrade-execution-proof"
APPROVAL_RECORD_TYPE = "workspace_upgrade_approval_artifact"
APPROVAL_SCOPE = "one_workspace_upgrade_proof_only"
APPROVAL_RELATIVE_DIR = Path("07_LOGS") / "Agent-Activity" / "_workspace_upgrade_approvals"
IDEMPOTENCY_MARKER_RELATIVE_DIR = APPROVAL_RELATIVE_DIR / "_execution_markers"
PROOF_OUTPUT_ROOT = Path(".pytest_tmp_env") / "workspace-upgrade-proof"
EVIDENCE_ROOT = Path("07_LOGS") / "Studio-Graph-Views"

FORBIDDEN_AUTHORITY = {
    "writes_target_workspace": False,
    "writes_target_folders": False,
    "writes_target_files": False,
    "updates_existing_files": False,
    "invokes_scaffold_generator": False,
    "executes_migration": False,
    "executes_upgrade": False,
    "reserves_idempotency_marker": False,
    "consumes_approval_decision": False,
    "provider_calls_allowed": False,
    "connector_calls_allowed": False,
    "writes_agent_bus_tasks": False,
    "mutates_gate": False,
    "uses_git": False,
    "executes_workflows": False,
    "host_mutation_allowed": False,
    "release_mutation_allowed": False,
    "canonical_mutation_allowed": False,
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _resolve_target(vault: Path, target_path: str | Path | None) -> Path:
    if target_path is None or str(target_path).strip() == "":
        return vault
    target = Path(target_path).expanduser()
    if not target.is_absolute():
        target = vault / target
    return target.resolve()


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


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
        raise ValueError(f"workspace upgrade approval path escapes base directory: {path}") from exc
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


def _planned_writes(target: Path) -> list[dict[str, Any]]:
    writes: list[dict[str, Any]] = []
    for rel_path in REQUIRED_DIRS:
        path = target / rel_path
        if not _effective_required_path_exists(target, rel_path):
            writes.append(
                {
                    "operation": "create_directory",
                    "relative_path": rel_path,
                    "target_path": str(path),
                    "exists_now": False,
                    "content_sha256": None,
                }
            )
    for rel_path in REQUIRED_FILES:
        path = target / rel_path
        if not _effective_required_path_exists(target, rel_path):
            placeholder = f"# {Path(rel_path).stem}\n\nChaseOS bootstrap anchor placeholder pending approved upgrade execution.\n"
            writes.append(
                {
                    "operation": "create_anchor_file",
                    "relative_path": rel_path,
                    "target_path": str(path),
                    "exists_now": False,
                    "content_sha256": hashlib.sha256(placeholder.encode("utf-8")).hexdigest(),
                    "content_preview": placeholder,
                }
            )
    return writes


def _existing_records(target: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for rel_path in [*REQUIRED_DIRS, *REQUIRED_FILES]:
        path = target / rel_path
        effective_exists = _effective_required_path_exists(target, rel_path)
        records.append(
            {
                "relative_path": rel_path,
                "exists": effective_exists,
                "is_dir": path.is_dir() if effective_exists and path.exists() else False,
                "is_file": path.is_file() if effective_exists and path.exists() else False,
                "size_bytes": path.stat().st_size if effective_exists and path.is_file() else 0,
                "sha256": _sha256_file(path) if effective_exists else None,
            }
        )
    return records


def _effective_required_path_exists(target: Path, rel_path: str) -> bool:
    path = target / rel_path
    if not path.exists():
        return False
    if rel_path == "07_LOGS" and _only_workspace_upgrade_artifacts(path):
        return False
    return True


def _only_workspace_upgrade_artifacts(path: Path) -> bool:
    if not path.is_dir():
        return False
    allowed = (path / "Agent-Activity" / "_workspace_upgrade_approvals").resolve()
    files = [item for item in path.rglob("*") if item.is_file()]
    if not files:
        return False
    for file_path in files:
        try:
            file_path.resolve().relative_to(allowed)
        except ValueError:
            return False
    return True


def _future_paths(vault: Path, packet_id: str) -> dict[str, dict[str, Any]]:
    proof_root = vault / PROOF_OUTPUT_ROOT / packet_id
    return {
        "proof_root": {"path": _rel(vault, proof_root), "exists": proof_root.exists()},
        "planned_writes_manifest": {
            "path": _rel(vault, proof_root / "planned-writes.json"),
            "exists": (proof_root / "planned-writes.json").exists(),
        },
        "rollback_plan": {
            "path": _rel(vault, proof_root / "rollback-plan.json"),
            "exists": (proof_root / "rollback-plan.json").exists(),
        },
        "execution_audit": {
            "path": _rel(vault, proof_root / "execution-audit.json"),
            "exists": (proof_root / "execution-audit.json").exists(),
        },
        "dry_run_evidence": {
            "path": _rel(vault, vault / EVIDENCE_ROOT / f"{packet_id}-upgrade-dry-run.json"),
            "exists": (vault / EVIDENCE_ROOT / f"{packet_id}-upgrade-dry-run.json").exists(),
        },
        "execution_evidence": {
            "path": _rel(vault, vault / EVIDENCE_ROOT / f"{packet_id}-upgrade-execution.json"),
            "exists": (vault / EVIDENCE_ROOT / f"{packet_id}-upgrade-execution.json").exists(),
        },
    }


def _build_material(
    *,
    target: Path,
    workspace_name: str,
    bootstrap_preview: dict[str, Any],
    planned_writes: list[dict[str, Any]],
    existing_records: list[dict[str, Any]],
) -> dict[str, Any]:
    summary = bootstrap_preview.get("summary") or {}
    return {
        "schema_version": MODEL_VERSION,
        "operation": "workspace_upgrade_proof_temp_only",
        "target_path": str(target),
        "workspace_name": workspace_name,
        "target_state": _effective_target_state(target, str(summary.get("target_state") or "")),
        "required_dirs": REQUIRED_DIRS,
        "required_files": REQUIRED_FILES,
        "planned_writes": planned_writes,
        "existing_records": existing_records,
        "approval_effect": "authorizes one future proof-temp-only workspace upgrade execution proof",
        "real_target_workspace_writes_allowed": False,
        "proof_temp_only": True,
        "scaffold_execution_allowed": False,
        "canonical_mutation_allowed": False,
    }


def _approval_packet_id(material: dict[str, Any]) -> str:
    return f"workspace-upgrade-appr-{_sha256_payload(material)[:16]}"


def _effective_target_state(target: Path, reported_state: str) -> str:
    if not target.is_dir():
        return reported_state
    entries = [item for item in target.iterdir() if item.name not in {".", ".."}]
    if not entries:
        return "empty_directory"
    if len(entries) == 1 and entries[0].name == "07_LOGS" and _only_workspace_upgrade_artifacts(entries[0]):
        return "empty_directory"
    return reported_state


def _approval_artifact_payload(
    *,
    packet_id: str,
    request_digest: str,
    material: dict[str, Any],
    approval_path: Path,
    marker_path: Path,
    future_paths: dict[str, Any],
    generated_at: str,
    requested_by: str,
    operator_id: str,
) -> dict[str, Any]:
    return {
        "record_type": APPROVAL_RECORD_TYPE,
        "schema_version": MODEL_VERSION,
        "approval_packet_id": packet_id,
        "request_digest_sha256": request_digest,
        "operator_decision": "approved",
        "approval_scope": APPROVAL_SCOPE,
        "approved_at": generated_at,
        "requested_by": requested_by,
        "operator_id": operator_id,
        "approval_artifact_path": str(approval_path),
        "exact_once_marker_path": str(marker_path),
        "future_output_paths": future_paths,
        "approved_material": material,
        "approval_decision_consumed": False,
        "execution_allowed_in_this_pass": False,
        "target_workspace_writes_allowed_in_this_pass": False,
        "proof_temp_only": True,
        **FORBIDDEN_AUTHORITY,
    }


def _approval_matches(payload: dict[str, Any] | None, packet_id: str, request_digest: str) -> bool:
    return bool(
        payload
        and payload.get("record_type") == APPROVAL_RECORD_TYPE
        and payload.get("approval_packet_id") == packet_id
        and payload.get("request_digest_sha256") == request_digest
        and payload.get("operator_decision") == "approved"
        and payload.get("approval_scope") == APPROVAL_SCOPE
        and payload.get("approval_decision_consumed") is False
        and payload.get("target_workspace_writes_allowed_in_this_pass") is False
    )


def _approval_matches_digest(payload: dict[str, Any] | None, packet_id: str, request_digest: str) -> bool:
    return bool(
        payload
        and payload.get("record_type") == APPROVAL_RECORD_TYPE
        and payload.get("approval_packet_id") == packet_id
        and payload.get("request_digest_sha256") == request_digest
        and payload.get("operator_decision") == "approved"
        and payload.get("approval_scope") == APPROVAL_SCOPE
        and payload.get("target_workspace_writes_allowed_in_this_pass") is False
    )


def _execution_proof_complete(
    vault: Path,
    marker_path: Path,
    packet_id: str,
    future_paths: dict[str, dict[str, Any]],
) -> bool:
    marker = _read_json(marker_path) if marker_path.is_file() else None
    if not (
        marker
        and marker.get("record_type") == "workspace_upgrade_execution_marker"
        and marker.get("approval_packet_id") == packet_id
        and marker.get("status") == "approved_upgrade_execution_proof_complete"
    ):
        return False
    for key in ["planned_writes_manifest", "rollback_plan", "execution_audit", "dry_run_evidence", "execution_evidence"]:
        rel_path = str((future_paths.get(key) or {}).get("path") or "")
        if not rel_path or not (vault / rel_path).is_file():
            return False
    return True


def build_upgrade_plan_approval_packet(
    vault_root: str | Path,
    *,
    target_path: str | Path | None = None,
    workspace_name: str | None = None,
    write_approval: bool = False,
    requested_by: str = "Codex",
    operator_id: str = "operator",
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build or explicitly write a 10F5 workspace-upgrade approval artifact."""

    vault = _vault_path(vault_root)
    target = _resolve_target(vault, target_path)
    name = workspace_name or target.name or vault.name
    timestamp = generated_at or _now_utc()
    compatibility = build_open_folder_compatibility_readiness(vault, folder_path=target)
    obsidian = build_obsidian_vault_detection(vault, folder_path=target)
    inference = build_general_markdown_inference_preview(vault, folder_path=target)
    bootstrap = build_chaseos_bootstrap_wizard_preview(vault, target_path=target, workspace_name=name)
    writes = _planned_writes(target)
    records = _existing_records(target)
    material = _build_material(
        target=target,
        workspace_name=name,
        bootstrap_preview=bootstrap,
        planned_writes=writes,
        existing_records=records,
    )
    packet_id = _approval_packet_id(material)
    digest = _sha256_payload(material)
    approval_path = _safe_json_path(vault, APPROVAL_RELATIVE_DIR, packet_id)
    marker_path = _safe_json_path(vault, IDEMPOTENCY_MARKER_RELATIVE_DIR, packet_id)
    future_paths = _future_paths(vault, packet_id)
    existing_payload = _read_json(approval_path) if approval_path.is_file() else None
    execution_complete = _execution_proof_complete(vault, marker_path, packet_id, future_paths)

    blockers: list[str] = []
    warnings: list[str] = []
    blockers.extend((bootstrap.get("readiness") or {}).get("blockers") or [])
    warnings.extend((compatibility.get("readiness") or {}).get("warnings") or [])
    warnings.extend((obsidian.get("readiness") or {}).get("warnings") or [])
    warnings.extend((inference.get("readiness") or {}).get("warnings") or [])
    warnings.extend((bootstrap.get("readiness") or {}).get("warnings") or [])
    if marker_path.exists() and not execution_complete:
        blockers.append("exact-once-marker-already-present")
    if any(bool(item.get("exists")) for item in future_paths.values()) and not execution_complete:
        blockers.append("future-output-path-collision")

    approval_reused = False
    approval_written = False
    if approval_path.exists() and not _approval_matches_digest(existing_payload, packet_id, digest):
        blockers.append("existing-approval-artifact-mismatch")

    ok = not blockers
    if write_approval and ok:
        if _approval_matches(existing_payload, packet_id, digest) or (
            execution_complete and _approval_matches_digest(existing_payload, packet_id, digest)
        ):
            approval_reused = True
        else:
            payload = _approval_artifact_payload(
                packet_id=packet_id,
                request_digest=digest,
                material=material,
                approval_path=approval_path,
                marker_path=marker_path,
                future_paths=future_paths,
                generated_at=timestamp,
                requested_by=requested_by,
                operator_id=operator_id,
            )
            _write_json(approval_path, payload)
            approval_written = True

    approval_present = approval_path.is_file()
    status = (
        "workspace_upgrade_approval_consumed_by_execution_proof"
        if execution_complete
        else
        "workspace_upgrade_approval_artifact_written"
        if approval_written
        else "workspace_upgrade_approval_artifact_present"
        if approval_present
        else "workspace_upgrade_approval_packet_ready"
        if ok
        else "blocked_workspace_upgrade_approval_packet"
    )

    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": status,
        "title": "ChaseOS Studio Upgrade Plan Approval Packet",
        "generated_at": timestamp,
        "vault_root": str(vault),
        "target": {
            "resolved_path": str(target),
            "exists": target.exists(),
            "is_directory": target.is_dir() if target.exists() else False,
        },
        "workspace": {"name": name},
        "source_previews": {
            "compatibility": {
                "ok": compatibility.get("ok"),
                "summary": compatibility.get("summary"),
            },
            "obsidian": {"ok": obsidian.get("ok"), "summary": obsidian.get("summary")},
            "inference": {"ok": inference.get("ok"), "summary": inference.get("summary")},
            "bootstrap": {"ok": bootstrap.get("ok"), "summary": bootstrap.get("summary")},
        },
        "approval_packet": {
            "id": packet_id,
            "request_digest_sha256": digest,
            "artifact_path": _rel(vault, approval_path),
            "artifact_exists": approval_present,
            "artifact_written": approval_written,
            "artifact_reused": approval_reused,
            "approval_scope": APPROVAL_SCOPE,
            "operator_decision": "approved" if approval_present else "not_written",
            "approval_decision_consumed": bool((existing_payload or {}).get("approval_decision_consumed")),
        },
        "exact_once_marker": {
            "path": _rel(vault, marker_path),
            "exists": marker_path.exists(),
            "record_type": "workspace_upgrade_execution_marker",
        },
        "planned_writes": {
            "count": len(writes),
            "directory_create_count": sum(1 for item in writes if item["operation"] == "create_directory"),
            "anchor_file_create_count": sum(1 for item in writes if item["operation"] == "create_anchor_file"),
            "items": writes,
        },
        "existing_records": records,
        "rollback_plan": {
            "strategy": "delete proof-temp outputs only in 10F6; real target rollback deferred because real target writes are forbidden",
            "real_target_rollback_required": False,
            "proof_output_root": (PROOF_OUTPUT_ROOT / packet_id).as_posix(),
        },
        "future_output_paths": future_paths,
        "authority_boundary": {
            "read_only": not write_approval,
            "approval_artifact_write_requested": write_approval,
            "writes_approval_artifacts": approval_written,
            "approval_packet_only": True,
            "proof_temp_only": True,
            **FORBIDDEN_AUTHORITY,
        },
        "readiness": {
            "upgrade_plan_approval_packet_ready": ok,
            "approval_artifact_present": approval_present,
            "approval_artifact_written": approval_written,
            "requires_explicit_write_approval_flag": True,
            "approved_upgrade_execution_proof_available": not execution_complete,
            "execution_proof_complete": execution_complete,
            "next_recommended_pass": "phase11-chat-conversation-persistence-approval-contract" if execution_complete else NEXT_RECOMMENDED_PASS,
            "blockers": list(dict.fromkeys(blockers)),
            "warnings": list(dict.fromkeys(warnings)),
        },
        "next_recommended_pass": "phase11-chat-conversation-persistence-approval-contract" if execution_complete else NEXT_RECOMMENDED_PASS,
    }


def get_upgrade_plan_approval_packet(vault_root: str | Path, **kwargs: Any) -> dict[str, Any]:
    return build_upgrade_plan_approval_packet(vault_root, **kwargs)
