"""Phase 11 companion memory readback/search preview.

This surface indexes companion-memory approval artifacts and proof-only
execution evidence. It intentionally does not read or create the real companion
memory ledger root; that remains a future approval-gated writer/read model.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.phase11_companion_memory_approval_preview import APPROVAL_CLASS
from runtime.studio.phase11_companion_memory_approved_execution_proof import (
    EVIDENCE_ROOT,
    MARKER_DIR,
    PROOF_ROOT,
)
from runtime.studio.service import StudioService


MODEL_VERSION = "studio.phase11_companion_memory_readback_search_preview.v1"
SURFACE_ID = "phase11_companion_memory_readback_search_preview"
PASS_ID = "phase11-companion-memory-readback-search-preview"
STATUS = "COMPLETE / READ-ONLY / PROOF-SEARCH PREVIEW / MEMORY LEDGER WRITES BLOCKED"
NEXT_RECOMMENDED_PASS = "phase11-companion-memory-ledger-write-approval-preview"
MEMORY_ROOT = Path("07_LOGS/Companion-Memory")


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


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _safe_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, f"approval_json_unreadable:{path.name}:{exc}"
    except json.JSONDecodeError as exc:
        return None, f"approval_json_malformed:{path.name}:{exc}"
    if not isinstance(payload, dict):
        return None, f"approval_json_not_object:{path.name}"
    return payload, None


def _content_payload(raw: Any) -> tuple[dict[str, Any], str]:
    if not raw:
        return {}, ""
    try:
        payload = json.loads(str(raw))
    except json.JSONDecodeError as exc:
        return {}, f"approval_content_json_malformed:{exc}"
    if not isinstance(payload, dict):
        return {}, "approval_content_json_not_object"
    return payload, ""


def _memory_snapshot(vault: Path) -> list[str]:
    root = vault / MEMORY_ROOT
    if not root.exists():
        return []
    return sorted(_rel(vault, path) for path in root.rglob("*") if path.is_file())


def _proof_paths(vault: Path, approval_id: str) -> dict[str, Path]:
    safe = _safe_id(approval_id)
    root = vault / PROOF_ROOT / safe
    return {
        "exact_once_marker": vault / MARKER_DIR / f"{safe}.json",
        "proof_memory_record": root / "proof-memory-record.json",
        "dry_run_evidence": root / "dry-run-evidence.json",
        "rollback_plan": root / "rollback-plan.json",
        "execution_audit": root / "execution-audit.json",
        "execution_evidence": vault / EVIDENCE_ROOT / f"{safe}-execution-evidence.json",
    }


def _path_record(vault: Path, path: Path) -> dict[str, Any]:
    return {
        "path": _rel(vault, path),
        "exists": path.is_file(),
        "size_bytes": path.stat().st_size if path.is_file() else 0,
    }


def _read_optional_record(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload, _error = _safe_json(path)
    return payload or {}


def _is_companion_memory_approval(payload: dict[str, Any]) -> bool:
    spec = payload.get("action_spec") if isinstance(payload.get("action_spec"), dict) else {}
    metadata = spec.get("metadata") if isinstance(spec.get("metadata"), dict) else {}
    return (
        spec.get("action_type") == "companion_memory_write"
        or metadata.get("phase11_companion_memory_approval_preview") is True
        or metadata.get("required_approval_class") == APPROVAL_CLASS
        or bool(metadata.get("phase11_companion_memory_approval_digest"))
    )


def _proof_status(status: str, proof_paths: dict[str, Path]) -> str:
    marker_exists = proof_paths["exact_once_marker"].is_file()
    proof_memory_exists = proof_paths["proof_memory_record"].is_file()
    execution_evidence_exists = proof_paths["execution_evidence"].is_file()
    if proof_memory_exists and execution_evidence_exists and marker_exists:
        return "proof_written"
    if status == "pending":
        return "approval_pending"
    if status in {"approved", "executing"}:
        return "approval_approved_no_proof"
    if status == "execution_failed":
        return "execution_failed"
    if status == "executed" and (marker_exists or proof_memory_exists or execution_evidence_exists):
        return "proof_partial"
    if status == "executed":
        return "proof_missing"
    return "not_executed"


def _approval_record(vault: Path, path: Path, payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    spec = payload.get("action_spec") if isinstance(payload.get("action_spec"), dict) else {}
    metadata = spec.get("metadata") if isinstance(spec.get("metadata"), dict) else {}
    approval_id = str(payload.get("approval_id") or path.stem)
    content, parse_error = _content_payload(spec.get("content"))
    if parse_error:
        warnings.append(f"{approval_id}:{parse_error}")
    proof_paths = _proof_paths(vault, approval_id)
    proof_outputs = {key: _path_record(vault, item) for key, item in proof_paths.items()}
    marker_payload = _read_optional_record(proof_paths["exact_once_marker"])
    proof_record = _read_optional_record(proof_paths["proof_memory_record"])
    evidence_record = _read_optional_record(proof_paths["execution_evidence"])
    status = str(payload.get("status") or "unknown")
    companion_id = str(metadata.get("companion_id") or content.get("companion_id") or "").strip().lower()
    memory_class = str(metadata.get("memory_class") or content.get("memory_class") or "").strip().lower()
    target_path = str(spec.get("target_path") or content.get("target_path") or "")
    if not companion_id and target_path.startswith("07_LOGS/Companion-Memory/"):
        parts = target_path.split("/")
        companion_id = parts[2] if len(parts) > 2 else ""
    proof_status = _proof_status(status, proof_paths)
    result = {
        "approval_id": approval_id,
        "approval_path": _rel(vault, path),
        "approval_status": status,
        "execution_status": payload.get("execution_status"),
        "result_action_id": payload.get("result_action_id"),
        "submitted_at": payload.get("submitted_at"),
        "updated_at": payload.get("updated_at"),
        "reviewed_by": payload.get("reviewed_by"),
        "reason": payload.get("reason"),
        "companion_id": companion_id or None,
        "memory_class": memory_class or None,
        "content_preview": content.get("content_preview") or "",
        "content_sha256": content.get("content_sha256"),
        "source_surface": metadata.get("source_surface") or content.get("source_surface"),
        "source_event_id": metadata.get("source_event_id") or content.get("source_event_id"),
        "target_path": target_path,
        "memory_approval_digest": metadata.get("phase11_companion_memory_approval_digest"),
        "required_approval_class": metadata.get("required_approval_class"),
        "proof_status": proof_status,
        "proof_outputs": proof_outputs,
        "marker_status": marker_payload.get("status"),
        "marker_reserved_before_outputs": marker_payload.get("marker_reserved_before_outputs"),
        "proof_execution_id": proof_record.get("proof_execution_id") or evidence_record.get("execution_id"),
        "proof_only": proof_record.get("proof_only") if proof_record else False,
        "memory_ledger_written": bool(
            metadata.get("memory_ledger_written")
            or content.get("memory_ledger_written")
            or proof_record.get("memory_ledger_written")
        ),
        "memory_file_written": bool(content.get("memory_file_written") or metadata.get("companion_memory_file_written")),
        "provider_call_performed": bool(metadata.get("provider_call_performed")),
        "runtime_dispatch_performed": bool(metadata.get("runtime_dispatch_performed")),
        "agent_bus_task_written": bool(metadata.get("agent_bus_task_write_performed")),
        "canonical_mutation_performed": bool(metadata.get("canonical_mutation_allowed")),
        "parse_error": parse_error,
    }
    return result, warnings


def _search_text(item: dict[str, Any]) -> str:
    fields = [
        "approval_id",
        "approval_status",
        "execution_status",
        "companion_id",
        "memory_class",
        "content_preview",
        "source_surface",
        "source_event_id",
        "target_path",
        "memory_approval_digest",
        "proof_status",
        "parse_error",
    ]
    return " ".join(str(item.get(field) or "") for field in fields).lower()


def _matches_filters(
    item: dict[str, Any],
    *,
    companion_id: str,
    memory_class: str,
    query: str,
    status_filter: str,
) -> bool:
    if companion_id and str(item.get("companion_id") or "").lower() != companion_id:
        return False
    if memory_class and str(item.get("memory_class") or "").lower() != memory_class:
        return False
    if status_filter:
        status = str(item.get("approval_status") or "").lower()
        proof_status = str(item.get("proof_status") or "").lower()
        execution = str(item.get("execution_status") or "").lower()
        if status_filter not in {status, proof_status, execution}:
            return False
    if query and query not in _search_text(item):
        return False
    return True


def _count_by(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _authority() -> dict[str, bool]:
    return {
        "read_only": True,
        "approval_artifact_read_allowed": True,
        "exact_once_marker_read_allowed": True,
        "proof_read_allowed": True,
        "real_companion_memory_read_allowed": False,
        "approval_queue_write_allowed": False,
        "approval_consumption_allowed": False,
        "approval_execution_allowed": False,
        "memory_ledger_write_allowed": False,
        "memory_root_create_allowed": False,
        "provider_calls_allowed": False,
        "runtime_dispatch_allowed": False,
        "agent_bus_task_write_allowed": False,
        "gate_mutation_allowed": False,
        "git_mutation_allowed": False,
        "workflow_execution_allowed": False,
        "host_mutation_allowed": False,
        "canonical_mutation_allowed": False,
    }


def build_phase11_companion_memory_readback_search_preview(
    vault_root: str | Path,
    *,
    companion_id: str | None = None,
    memory_class: str | None = None,
    query: str | None = None,
    status_filter: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Read proof-only companion-memory approvals and return a filtered index."""

    vault = Path(vault_root).resolve()
    before_memory = _memory_snapshot(vault)
    filters = {
        "companion_id": " ".join(str(companion_id or "").strip().lower().split()),
        "memory_class": " ".join(str(memory_class or "").strip().lower().split()),
        "query": " ".join(str(query or "").strip().lower().split()),
        "status_filter": " ".join(str(status_filter or "").strip().lower().split()),
        "limit": max(1, min(int(limit or 20), 200)),
    }
    warnings: list[str] = []
    approvals: list[dict[str, Any]] = []
    approval_root = vault / StudioService.APPROVAL_DIR
    if approval_root.exists():
        for path in sorted(approval_root.glob("*.json"), key=lambda item: item.stat().st_mtime_ns, reverse=True):
            payload, error = _safe_json(path)
            if error:
                warnings.append(error)
                continue
            if not payload or not _is_companion_memory_approval(payload):
                continue
            record, record_warnings = _approval_record(vault, path, payload)
            approvals.append(record)
            warnings.extend(record_warnings)

    filtered = [
        item
        for item in approvals
        if _matches_filters(
            item,
            companion_id=filters["companion_id"],
            memory_class=filters["memory_class"],
            query=filters["query"],
            status_filter=filters["status_filter"],
        )
    ]
    limited = filtered[: int(filters["limit"])]
    after_memory = _memory_snapshot(vault)
    proof_written_count = sum(1 for item in approvals if item.get("proof_status") == "proof_written")
    malformed_count = sum(1 for item in approvals if item.get("parse_error"))
    memory_root_exists = (vault / MEMORY_ROOT).exists()
    summary = {
        "approval_candidate_count": len(approvals),
        "executed_approval_count": sum(1 for item in approvals if item.get("approval_status") == "executed"),
        "pending_approval_count": sum(1 for item in approvals if item.get("approval_status") == "pending"),
        "approved_approval_count": sum(1 for item in approvals if item.get("approval_status") == "approved"),
        "execution_failed_count": sum(1 for item in approvals if item.get("approval_status") == "execution_failed"),
        "proof_record_count": proof_written_count,
        "malformed_record_count": malformed_count,
        "results_count": len(limited),
        "unfiltered_results_count": len(filtered),
        "memory_root_exists": memory_root_exists,
        "memory_root_read": False,
        "memory_ledger_read": False,
        "memory_ledger_written": False,
        "memory_root_created": False,
        "provider_call_performed": False,
        "runtime_dispatch_performed": False,
        "agent_bus_task_written": False,
        "canonical_mutation_performed": False,
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }
    digest_material = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "filters": filters,
        "approval_candidate_count": len(approvals),
        "result_approval_ids": [item.get("approval_id") for item in limited],
        "memory_root_exists": memory_root_exists,
        "memory_files_unchanged": before_memory == after_memory,
    }
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "approval_gated": False,
        "summary": summary,
        "filters": filters,
        "results": limited,
        "proof_records": limited,
        "indexes": {
            "by_companion": _count_by(approvals, "companion_id"),
            "by_memory_class": _count_by(approvals, "memory_class"),
            "by_approval_status": _count_by(approvals, "approval_status"),
            "by_proof_status": _count_by(approvals, "proof_status"),
        },
        "source_paths": {
            "approval_dir": StudioService.APPROVAL_DIR,
            "marker_dir": MARKER_DIR.as_posix(),
            "proof_root": PROOF_ROOT.as_posix(),
            "evidence_root": EVIDENCE_ROOT.as_posix(),
            "real_memory_root": MEMORY_ROOT.as_posix(),
        },
        "memory_snapshot_proof": {
            "root_path": MEMORY_ROOT.as_posix(),
            "files_before": before_memory,
            "files_after": after_memory,
            "unchanged": before_memory == after_memory,
            "real_memory_root_read_by_this_surface": False,
            "memory_root_created_by_this_surface": False,
        },
        "authority": _authority(),
        "readiness": {
            "companion_memory_readback_search_preview_ready": True,
            "companion_memory_proof_index_ready": True,
            "companion_memory_proof_search_ready": True,
            "companion_memory_real_ledger_read_blocked": True,
            "companion_memory_ledger_writes_blocked": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "digest_proof": {
            "readback_search_digest": _sha256(digest_material),
            "digest_material": digest_material,
        },
        "denied_by_this_surface": [
            "real_companion_memory_ledger_read",
            "companion_memory_file_write",
            "companion_memory_directory_create",
            "approval_queue_write",
            "approval_consumption",
            "approval_execution",
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
        "blocked_reasons": [],
        "warnings": list(dict.fromkeys(warnings)),
    }


def format_phase11_companion_memory_readback_search_preview(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    filters = payload.get("filters") or {}
    lines = [
        "Phase 11 Companion Memory Readback/Search Preview",
        f"Status: {payload.get('status')}",
        f"Approvals indexed: {summary.get('approval_candidate_count', 0)}",
        f"Proof records: {summary.get('proof_record_count', 0)}",
        f"Results: {summary.get('results_count', 0)}",
        f"Companion filter: {filters.get('companion_id') or 'all'}",
        f"Memory class filter: {filters.get('memory_class') or 'all'}",
        f"Query: {filters.get('query') or 'none'}",
        f"Status filter: {filters.get('status_filter') or 'all'}",
        f"Real memory root read: {summary.get('memory_root_read')}",
        f"Memory ledger written: {summary.get('memory_ledger_written')}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    warnings = payload.get("warnings") or []
    if warnings:
        lines.append("Warnings:")
        lines.extend(f"- {item}" for item in warnings[:8])
    return "\n".join(lines)
