"""Phase 11 companion memory ledger-write approval preview.

This is the second-stage approval lane for companion memory. It reads the
proof-only execution evidence produced by the prior companion-memory executor
and builds a digest-bound approval packet for a future real ledger append. It
may write one pending approval artifact when the operator supplies the exact
digest, but it never creates ``07_LOGS/Companion-Memory`` or appends a ledger.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.phase11_companion_memory_approval_preview import (
    APPROVAL_CLASS as SOURCE_APPROVAL_CLASS,
)
from runtime.studio.phase11_companion_memory_approved_execution_proof import (
    EVIDENCE_ROOT,
    MARKER_DIR,
    PROOF_ROOT,
)
from runtime.studio.service import ActionSpec, StudioService


MODEL_VERSION = "studio.phase11_companion_memory_ledger_write_approval_preview.v1"
SURFACE_ID = "phase11_companion_memory_ledger_write_approval_preview"
PASS_ID = "phase11-companion-memory-ledger-write-approval-preview"
STATUS_PREVIEW = "COMPLETE / APPROVAL-PREVIEW / LEDGER WRITE BLOCKED"
STATUS_WRITTEN = "COMPLETE / APPROVAL-QUEUE-WRITE / VERIFIED / LEDGER WRITE BLOCKED"
BLOCKED_STATUS = "BLOCKED / APPROVAL-PREVIEW / NO APPROVAL ARTIFACT WRITE"
NEXT_RECOMMENDED_PASS = "phase11-companion-memory-approved-ledger-write-execution-proof"
APPROVAL_CLASS = "studio_companion_memory_ledger_write_future"
MEMORY_ROOT = Path("07_LOGS") / "Companion-Memory"
LEDGER_MARKER_DIR = Path("runtime") / "studio" / "approvals" / "_companion_memory_ledger_write_markers"
AUDIT_DIR = Path("07_LOGS") / "Agent-Activity"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_id(value: str | None) -> str:
    return "".join(c if c.isalnum() or c == "-" else "_" for c in str(value or "")) or "unknown"


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _safe_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, f"json_read_failed:{_rel(path.parent, path)}:{exc}"
    except json.JSONDecodeError as exc:
        return None, f"json_malformed:{path.name}:{exc}"
    if not isinstance(payload, dict):
        return None, f"json_not_object:{path.name}"
    return payload, None


def _proof_paths(vault: Path, approval_id: str) -> dict[str, Path]:
    safe = _safe_id(approval_id)
    proof_root = vault / PROOF_ROOT / safe
    return {
        "source_approval": vault / StudioService.APPROVAL_DIR / f"{safe}.json",
        "exact_once_marker": vault / MARKER_DIR / f"{safe}.json",
        "proof_memory_record": proof_root / "proof-memory-record.json",
        "execution_evidence": vault / EVIDENCE_ROOT / f"{safe}-execution-evidence.json",
        "dry_run_evidence": proof_root / "dry-run-evidence.json",
        "rollback_plan": proof_root / "rollback-plan.json",
        "execution_audit": proof_root / "execution-audit.json",
    }


def _path_record(vault: Path, path: Path) -> dict[str, Any]:
    return {
        "path": _rel(vault, path),
        "exists": path.is_file(),
        "sha256": _file_sha256(path) if path.is_file() else None,
        "size_bytes": path.stat().st_size if path.is_file() else 0,
    }


def _memory_snapshot(vault: Path) -> list[str]:
    root = vault / MEMORY_ROOT
    if not root.exists():
        return []
    return sorted(_rel(vault, path) for path in root.rglob("*") if path.is_file())


def _content_payload(raw: Any) -> tuple[dict[str, Any], str]:
    try:
        payload = json.loads(str(raw or "{}"))
    except json.JSONDecodeError as exc:
        return {}, f"approval_content_json_malformed:{exc}"
    if not isinstance(payload, dict):
        return {}, "approval_content_json_not_object"
    return payload, ""


def _is_source_companion_memory_approval(payload: dict[str, Any]) -> bool:
    spec = payload.get("action_spec") if isinstance(payload.get("action_spec"), dict) else {}
    metadata = spec.get("metadata") if isinstance(spec.get("metadata"), dict) else {}
    return bool(
        spec.get("action_type") == "companion_memory_write"
        and metadata.get("required_approval_class") == SOURCE_APPROVAL_CLASS
        and metadata.get("phase11_companion_memory_approval_digest")
    )


def _source_candidate(vault: Path, path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    approval_id = str(payload.get("approval_id") or path.stem)
    spec = payload.get("action_spec") if isinstance(payload.get("action_spec"), dict) else {}
    metadata = spec.get("metadata") if isinstance(spec.get("metadata"), dict) else {}
    content, parse_error = _content_payload(spec.get("content"))
    paths = _proof_paths(vault, approval_id)
    marker, marker_error = _safe_json(paths["exact_once_marker"]) if paths["exact_once_marker"].is_file() else ({}, None)
    proof_record, proof_error = _safe_json(paths["proof_memory_record"]) if paths["proof_memory_record"].is_file() else ({}, None)
    execution_evidence, evidence_error = (
        _safe_json(paths["execution_evidence"]) if paths["execution_evidence"].is_file() else ({}, None)
    )
    proof_written = (
        paths["exact_once_marker"].is_file()
        and paths["proof_memory_record"].is_file()
        and paths["execution_evidence"].is_file()
        and (marker or {}).get("status") == "executed"
        and bool(proof_record)
        and bool(execution_evidence)
    )
    return {
        "approval_id": approval_id,
        "approval_path": _rel(vault, path),
        "approval_status": str(payload.get("status") or "unknown"),
        "execution_status": payload.get("execution_status"),
        "result_action_id": payload.get("result_action_id"),
        "memory_approval_digest": metadata.get("phase11_companion_memory_approval_digest"),
        "companion_id": metadata.get("companion_id") or content.get("companion_id"),
        "memory_class": metadata.get("memory_class") or content.get("memory_class"),
        "target_path": spec.get("target_path") or content.get("target_path"),
        "content_preview": content.get("content_preview") or "",
        "content_sha256": content.get("content_sha256"),
        "source_surface": metadata.get("source_surface") or content.get("source_surface"),
        "source_event_id": metadata.get("source_event_id") or content.get("source_event_id"),
        "proof_status": "proof_written" if proof_written else "proof_missing_or_partial",
        "proof_only": (proof_record or {}).get("proof_only") is True,
        "marker_status": (marker or {}).get("status"),
        "marker_reserved_before_outputs": (marker or {}).get("marker_reserved_before_outputs"),
        "proof_execution_id": (proof_record or {}).get("proof_execution_id")
        or (execution_evidence or {}).get("execution_id"),
        "memory_ledger_written": bool(
            metadata.get("memory_ledger_written")
            or content.get("memory_ledger_written")
            or (proof_record or {}).get("memory_ledger_written")
        ),
        "memory_file_written": bool(metadata.get("companion_memory_file_written") or content.get("memory_file_written")),
        "provider_call_performed": bool(metadata.get("provider_call_performed")),
        "runtime_dispatch_performed": bool(metadata.get("runtime_dispatch_performed")),
        "agent_bus_task_written": bool(metadata.get("agent_bus_task_write_performed")),
        "canonical_mutation_performed": bool(metadata.get("canonical_mutation_allowed")),
        "source_approval_sha256": _file_sha256(path),
        "proof_record_sha256": _file_sha256(paths["proof_memory_record"]) if paths["proof_memory_record"].is_file() else None,
        "execution_evidence_sha256": _file_sha256(paths["execution_evidence"]) if paths["execution_evidence"].is_file() else None,
        "marker_sha256": _file_sha256(paths["exact_once_marker"]) if paths["exact_once_marker"].is_file() else None,
        "proof_outputs": {key: _path_record(vault, item) for key, item in paths.items()},
        "parse_errors": [item for item in (parse_error, marker_error, proof_error, evidence_error) if item],
        "proof_record": proof_record or {},
        "execution_evidence": execution_evidence or {},
    }


def _list_source_proofs(vault: Path) -> list[dict[str, Any]]:
    root = vault / StudioService.APPROVAL_DIR
    if not root.is_dir():
        return []
    items: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json"), key=lambda item: item.stat().st_mtime_ns, reverse=True):
        payload, error = _safe_json(path)
        if error or not payload or not _is_source_companion_memory_approval(payload):
            continue
        items.append(_source_candidate(vault, path, payload))
    return items


def _select_source_proof(vault: Path, source_approval_id: str | None) -> tuple[dict[str, Any] | None, list[str]]:
    requested = str(source_approval_id or "").strip()
    proofs = _list_source_proofs(vault)
    if requested:
        for item in proofs:
            if item.get("approval_id") == requested:
                return item, []
        return None, ["source_companion_memory_approval_not_found"]
    for item in proofs:
        if item.get("proof_status") == "proof_written":
            return item, []
    return None, ["no_executed_companion_memory_proof_found"]


def _ledger_entry_preview(source: dict[str, Any]) -> dict[str, Any]:
    evidence = source.get("execution_evidence") if isinstance(source.get("execution_evidence"), dict) else {}
    proof_record = source.get("proof_record") if isinstance(source.get("proof_record"), dict) else {}
    return {
        "schema_version": "phase11_companion_memory_ledger_entry.v0.1",
        "memory_id": proof_record.get("memory_id")
        or f"companion-memory-{str(source.get('memory_approval_digest') or '')[:16]}",
        "companion_id": source.get("companion_id"),
        "memory_class": source.get("memory_class"),
        "content_preview": source.get("content_preview") or proof_record.get("content_preview") or "",
        "content_sha256": source.get("content_sha256") or proof_record.get("content_sha256"),
        "source_surface": source.get("source_surface"),
        "source_event_id": source.get("source_event_id"),
        "source_approval_id": source.get("approval_id"),
        "source_memory_approval_digest": source.get("memory_approval_digest"),
        "source_proof_execution_id": source.get("proof_execution_id") or evidence.get("execution_id"),
        "target_path": source.get("target_path"),
        "trust_state": "raw",
        "canonical": False,
        "authoritative": False,
        "proof_only_source": True,
        "ledger_write_performed": False,
        "provider_call_performed": False,
        "runtime_dispatch_performed": False,
        "agent_bus_task_written": False,
        "canonical_mutation_performed": False,
    }


def _existing_digest_approval(vault: Path, ledger_write_approval_digest: str) -> dict[str, Any] | None:
    root = vault / StudioService.APPROVAL_DIR
    if not root.exists():
        return None
    active = {"pending", "approved", "executing", "executed", "execution_failed"}
    for path in sorted(root.glob("*.json"), key=lambda item: item.stat().st_mtime_ns, reverse=True):
        payload, _error = _safe_json(path)
        if not payload:
            continue
        spec = payload.get("action_spec") if isinstance(payload.get("action_spec"), dict) else {}
        metadata = spec.get("metadata") if isinstance(spec.get("metadata"), dict) else {}
        if metadata.get("phase11_companion_memory_ledger_write_approval_digest") != ledger_write_approval_digest:
            continue
        if str(payload.get("status") or "") not in active:
            continue
        return {
            "approval_id": payload.get("approval_id") or path.stem,
            "status": payload.get("status") or "unknown",
            "path": _rel(vault, path),
            "target_path": spec.get("target_path"),
        }
    return None


def _authority(created: bool) -> dict[str, bool]:
    return {
        "approval_gated": True,
        "approval_preview_allowed": True,
        "approval_queue_write_allowed_with_digest": True,
        "approval_queue_write_performed": created,
        "approval_grant_or_reject_allowed": False,
        "approval_consumption_allowed": False,
        "approval_execution_allowed": False,
        "ledger_append_allowed": False,
        "memory_ledger_write_allowed": False,
        "memory_ledger_write_performed": False,
        "memory_root_create_allowed": False,
        "memory_root_created": False,
        "real_memory_ledger_read_allowed": False,
        "provider_calls_allowed": False,
        "runtime_dispatch_allowed": False,
        "agent_bus_task_write_allowed": False,
        "gate_mutation_allowed": False,
        "git_mutation_allowed": False,
        "workflow_execution_allowed": False,
        "host_mutation_allowed": False,
        "canonical_mutation_allowed": False,
    }


def _build_action_spec(
    *,
    source: dict[str, Any],
    ledger_entry: dict[str, Any],
    ledger_line: str,
    ledger_write_approval_digest: str,
    digest_material: dict[str, Any],
    operator_id: str,
) -> ActionSpec:
    return ActionSpec(
        action_type="companion_memory_ledger_append",
        target_path=str(source.get("target_path") or ""),
        content=ledger_line,
        metadata={
            "pass": PASS_ID,
            "phase": "Phase 11",
            "source_surface": SURFACE_ID,
            "required_approval_class": APPROVAL_CLASS,
            "phase11_companion_memory_ledger_write_approval_preview": True,
            "phase11_companion_memory_ledger_write_approval_digest": ledger_write_approval_digest,
            "phase11_companion_memory_ledger_write_digest_material_sha256": _sha256_text(
                _canonical_json(digest_material)
            ),
            "source_companion_memory_approval_id": source.get("approval_id"),
            "source_companion_memory_approval_digest": source.get("memory_approval_digest"),
            "source_companion_memory_proof_execution_id": source.get("proof_execution_id"),
            "companion_id": source.get("companion_id"),
            "memory_class": source.get("memory_class"),
            "content_sha256": ledger_entry.get("content_sha256"),
            "operator_confirmation": operator_id or "operator",
            "approval_queue_write_only": True,
            "approval_execution_deferred_until": NEXT_RECOMMENDED_PASS,
            "companion_memory_ledger_write_performed": False,
            "companion_memory_root_created": False,
            "approval_consumed": False,
            "provider_call_performed": False,
            "runtime_dispatch_performed": False,
            "agent_bus_task_write_performed": False,
            "canonical_mutation_allowed": False,
        },
        submitted_by="studio-chat",
        note="Phase 11 companion-memory ledger-write approval request; real ledger append deferred.",
    )


def _write_audit_record(
    *,
    vault: Path,
    approval_id: str,
    approval_path: str,
    source: dict[str, Any],
    ledger_write_approval_digest: str,
    digest_material: dict[str, Any],
    operator_id: str,
) -> str:
    root = vault / AUDIT_DIR
    root.mkdir(parents=True, exist_ok=True)
    audit_path = root / f"{PASS_ID}-{ledger_write_approval_digest[:16]}.md"
    text = "\n".join(
        [
            "---",
            "type: agent-activity",
            "runtime: Codex",
            f"pass_id: {PASS_ID}",
            f"approval_id: {approval_id}",
            f"status: {STATUS_WRITTEN}",
            "---",
            "",
            "# Phase 11 Companion Memory Ledger-Write Approval Preview",
            "",
            f"operator_id: {operator_id or 'operator'}",
            f"source_approval_id: {source.get('approval_id')}",
            f"source_memory_approval_digest: {source.get('memory_approval_digest')}",
            f"ledger_write_approval_digest: {ledger_write_approval_digest}",
            f"digest_material_sha256: {_sha256_text(_canonical_json(digest_material))}",
            f"approval_id: {approval_id}",
            f"approval_path: {approval_path}",
            f"target_path: {source.get('target_path')}",
            "approval_request_created: true",
            "approval_queue_writer_called: true",
            "approval_consumed: false",
            "approval_execution_called: false",
            "memory_ledger_written: false",
            "memory_root_created: false",
            "provider_call_performed: false",
            "runtime_dispatch_performed: false",
            "agent_bus_task_written: false",
            "canonical_mutation_allowed: false",
            "",
        ]
    )
    audit_path.write_text(text, encoding="utf-8")
    return _rel(vault, audit_path)


def build_phase11_companion_memory_ledger_write_approval_preview(
    vault_root: str | Path,
    *,
    source_approval_id: str | None = None,
    expected_ledger_write_approval_digest: str | None = None,
    write_approval: bool = False,
    operator_id: str = "operator",
) -> dict[str, Any]:
    """Preview or queue a future real companion-memory ledger-write approval."""

    vault = Path(vault_root).resolve()
    before_memory = _memory_snapshot(vault)
    source, source_blockers = _select_source_proof(vault, source_approval_id)
    blockers: list[str] = list(source_blockers)
    warnings: list[str] = []

    if source is not None:
        if source.get("parse_errors"):
            blockers.extend(str(item) for item in source.get("parse_errors") or [])
        if source.get("approval_status") != "executed":
            blockers.append("source_approval_not_executed")
        if source.get("execution_status") != "completed":
            blockers.append("source_execution_not_completed")
        if source.get("proof_status") != "proof_written":
            blockers.append("source_proof_outputs_not_complete")
        if source.get("proof_only") is not True:
            blockers.append("source_proof_record_not_proof_only")
        if source.get("memory_ledger_written") is True or source.get("memory_file_written") is True:
            blockers.append("source_already_claims_memory_ledger_written")
        if not source.get("memory_approval_digest"):
            blockers.append("source_memory_approval_digest_missing")
        if not source.get("companion_id"):
            blockers.append("source_companion_id_missing")
        if not source.get("memory_class"):
            blockers.append("source_memory_class_missing")
        if not source.get("content_sha256"):
            blockers.append("source_content_sha256_missing")
        target_path = str(source.get("target_path") or "")
        if not target_path.startswith("07_LOGS/Companion-Memory/") or not target_path.endswith("/memory-ledger.jsonl"):
            blockers.append("source_target_path_not_companion_memory_ledger")
    else:
        target_path = ""

    ledger_entry = _ledger_entry_preview(source or {})
    ledger_line = _canonical_json(ledger_entry) + "\n"
    ledger_line_sha256 = _sha256_text(ledger_line)
    approval_id_preview = f"companion-memory-ledger-appr-{ledger_line_sha256[:16]}"
    future_marker_path = LEDGER_MARKER_DIR / f"{approval_id_preview}.json"
    digest_material = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "source_approval_id": (source or {}).get("approval_id"),
        "source_approval_sha256": (source or {}).get("source_approval_sha256"),
        "source_memory_approval_digest": (source or {}).get("memory_approval_digest"),
        "proof_record_sha256": (source or {}).get("proof_record_sha256"),
        "execution_evidence_sha256": (source or {}).get("execution_evidence_sha256"),
        "marker_sha256": (source or {}).get("marker_sha256"),
        "ledger_line_sha256": ledger_line_sha256,
        "target_path": target_path,
        "future_marker_path": future_marker_path.as_posix(),
        "required_approval_class": APPROVAL_CLASS,
    }
    ledger_write_approval_digest = _sha256_text(_canonical_json(digest_material))
    expected = str(expected_ledger_write_approval_digest or "").strip()

    if write_approval and not expected:
        blockers.append("expected_ledger_write_approval_digest_required")
    elif write_approval and expected != ledger_write_approval_digest:
        blockers.append("expected_ledger_write_approval_digest_mismatch")

    duplicate = _existing_digest_approval(vault, ledger_write_approval_digest) if ledger_write_approval_digest else None
    if write_approval and duplicate:
        blockers.append("approval_queue_request_already_exists_for_digest")

    blocked_unique = list(dict.fromkeys(blockers))
    action_spec = _build_action_spec(
        source=source or {},
        ledger_entry=ledger_entry,
        ledger_line=ledger_line,
        ledger_write_approval_digest=ledger_write_approval_digest,
        digest_material=digest_material,
        operator_id=operator_id,
    )
    created = False
    queue_writer_called = False
    approval_id: str | None = None
    approval_path: str | None = None
    audit_path: str | None = None
    status = STATUS_PREVIEW if not blocked_unique else BLOCKED_STATUS

    if write_approval and not blocked_unique:
        queue_writer_called = True
        request = StudioService(vault).queue_for_approval(action_spec)
        created = True
        approval_id = request.approval_id
        approval_path = f"{StudioService.APPROVAL_DIR}/{request.approval_id}.json"
        audit_path = _write_audit_record(
            vault=vault,
            approval_id=approval_id,
            approval_path=approval_path,
            source=source or {},
            ledger_write_approval_digest=ledger_write_approval_digest,
            digest_material=digest_material,
            operator_id=operator_id,
        )
        status = STATUS_WRITTEN

    after_memory = _memory_snapshot(vault)
    preview_ready = bool(source is not None and not blocked_unique)
    ok = not blocked_unique
    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": status,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": not created,
        "approval_gated": True,
        "summary": {
            "source_approval_id": (source or {}).get("approval_id"),
            "source_proof_status": (source or {}).get("proof_status"),
            "companion_id": (source or {}).get("companion_id"),
            "memory_class": (source or {}).get("memory_class"),
            "ledger_write_approval_preview_ready": preview_ready,
            "write_approval_requested": bool(write_approval),
            "expected_ledger_write_approval_digest_provided": bool(expected),
            "expected_ledger_write_approval_digest_matched": expected == ledger_write_approval_digest if expected else None,
            "approval_request_created": created,
            "approval_queue_writer_called": queue_writer_called,
            "approval_status": "pending" if created else None,
            "duplicate_active_request_present": bool(duplicate),
            "ledger_line_sha256": ledger_line_sha256,
            "memory_root_exists_before": bool(before_memory),
            "memory_snapshot_unchanged": before_memory == after_memory,
            "memory_root_created": False,
            "memory_ledger_written": False,
            "memory_write_executed": False,
            "approval_consumed": False,
            "approval_execution_called": False,
            "provider_call_performed": False,
            "runtime_dispatch_performed": False,
            "agent_bus_task_written": False,
            "canonical_mutation_performed": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "blocker_count": len(blocked_unique),
        },
        "source_proof": {
            key: value
            for key, value in (source or {}).items()
            if key not in {"proof_record", "execution_evidence"}
        },
        "ledger_entry_preview": {
            "entry": ledger_entry,
            "line_sha256": ledger_line_sha256,
            "target_path": target_path,
            "line_bytes": len(ledger_line.encode("utf-8")),
            "ledger_line_included_for_approval": True,
        },
        "digest_proof": {
            "ledger_write_approval_digest": ledger_write_approval_digest,
            "expected_ledger_write_approval_digest": expected or None,
            "expected_digest_matched": expected == ledger_write_approval_digest if expected else None,
            "digest_required_for_write": True,
            "digest_material": digest_material,
            "digest_material_sha256": _sha256_text(_canonical_json(digest_material)),
        },
        "future_approval_packet_preview": {
            "approval_request_created": created,
            "approval_queue_writer_called": queue_writer_called,
            "approval_id_preview": approval_id_preview,
            "approval_queue_path_preview": f"{StudioService.APPROVAL_DIR}/{approval_id_preview}.json",
            "required_approval_class": APPROVAL_CLASS,
            "future_status_if_written": "pending",
            "expected_ledger_write_approval_digest_required": True,
            "ledger_write_approval_digest": ledger_write_approval_digest,
            "future_exact_once_marker_path": future_marker_path.as_posix(),
            "action_spec_preview": {
                "action_type": action_spec.action_type,
                "target_path": action_spec.target_path,
                "submitted_by": action_spec.submitted_by,
                "content_sha256": _sha256_text(action_spec.content or ""),
                "metadata": dict(action_spec.metadata),
            },
        },
        "approval_record": {
            "approval_id": approval_id,
            "approval_path": approval_path,
            "approval_status": "pending" if created else None,
            "duplicate": duplicate,
        },
        "audit_record": {
            "audit_record_written": bool(audit_path),
            "audit_record_path": audit_path,
        },
        "memory_snapshot_proof": {
            "root_path": MEMORY_ROOT.as_posix(),
            "files_before": before_memory,
            "files_after": after_memory,
            "unchanged": before_memory == after_memory,
            "memory_root_created_by_this_surface": False,
            "memory_ledger_written_by_this_surface": False,
        },
        "approval_center_visibility": {
            "source_group": "studio-service",
            "visible_after_write": created,
            "approval_center_reads_runtime_studio_approvals": True,
        },
        "authority": _authority(created),
        "denied_by_this_surface": [
            "approval_grant_or_reject",
            "approval_consumption",
            "approval_execution",
            "companion_memory_ledger_append",
            "companion_memory_directory_create",
            "real_companion_memory_ledger_read",
            "provider_api_call",
            "runtime_dispatch",
            "browser_control",
            "agent_bus_task_write",
            "gate_mutation",
            "git_mutation",
            "workflow_execution",
            "host_mutation",
            "canonical_writeback",
        ],
        "readiness": {
            "companion_memory_ledger_write_approval_preview_ready": preview_ready,
            "companion_memory_ledger_write_approval_queue_write_gated": True,
            "companion_memory_ledger_write_digest_required": True,
            "companion_memory_source_proof_required": True,
            "companion_memory_real_ledger_write_blocked": True,
            "companion_memory_real_ledger_read_blocked": True,
            "companion_memory_approved_ledger_write_executor_required": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "blocked_reasons": blocked_unique,
        "warnings": warnings,
    }


def format_phase11_companion_memory_ledger_write_approval_preview(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    digest = payload.get("digest_proof") or {}
    approval = payload.get("approval_record") or {}
    preview = payload.get("future_approval_packet_preview") or {}
    lines = [
        "Phase 11 Companion Memory Ledger-Write Approval Preview",
        f"Status: {payload.get('status')}",
        f"Source approval id: {summary.get('source_approval_id') or 'missing'}",
        f"Companion: {summary.get('companion_id') or 'missing'}",
        f"Memory class: {summary.get('memory_class') or 'missing'}",
        f"Preview ready: {summary.get('ledger_write_approval_preview_ready')}",
        f"Approval request created: {summary.get('approval_request_created')}",
        f"Approval id: {approval.get('approval_id') or preview.get('approval_id_preview') or 'none'}",
        f"Ledger-write approval digest: {digest.get('ledger_write_approval_digest') or 'missing'}",
        f"Memory ledger written: {summary.get('memory_ledger_written')}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers)
    return "\n".join(lines)
