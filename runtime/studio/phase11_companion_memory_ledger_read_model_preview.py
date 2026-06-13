"""Phase 11 companion memory ledger read-model preview.

This surface is the read side of the governed companion-memory ledger lane. It
may inspect existing companion-memory JSONL ledgers and proof-only backfill
records, but it never creates the memory root, appends a ledger line, consumes
approval, dispatches runtimes, or promotes canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.phase11_companion_memory_ledger_write_approval_preview import MEMORY_ROOT
from runtime.studio.phase11_companion_memory_readback_search_preview import (
    build_phase11_companion_memory_readback_search_preview,
)


MODEL_VERSION = "studio.phase11_companion_memory_ledger_read_model_preview.v1"
SURFACE_ID = "phase11_companion_memory_ledger_read_model_preview"
PASS_ID = "phase11-companion-memory-ledger-read-model-preview"
STATUS = "COMPLETE / READ-ONLY / LEDGER READ MODEL PREVIEW / VERIFIED"
NEXT_RECOMMENDED_PASS = "phase11-companion-memory-context-readiness-preview"
LEDGER_FILENAME = "memory-ledger.jsonl"
KNOWN_SCHEMA_VERSIONS = {"phase11_companion_memory_ledger_entry.v0.1"}
TRUST_STATES = {
    "raw",
    "quarantined",
    "suggested",
    "promoted",
    "canonical",
    "generated",
    "archived",
    "disputed",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _memory_snapshot(vault: Path) -> list[str]:
    root = vault / MEMORY_ROOT
    if not root.exists():
        return []
    return sorted(_rel(vault, path) for path in root.rglob("*") if path.is_file())


def _norm_filter(value: str | None) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _safe_limit(limit: int | None) -> int:
    try:
        parsed = int(limit or 20)
    except (TypeError, ValueError):
        parsed = 20
    return max(1, min(parsed, 500))


def _line_sha(line: str) -> str:
    return _sha256_text(line.rstrip("\n") + "\n")


def _record_id(entry: dict[str, Any], *, companion_id: str, line_number: int) -> str:
    for key in ("memory_id", "ledger_write_approval_id", "source_approval_id", "source_event_id"):
        value = str(entry.get(key) or "").strip()
        if value:
            return value
    return f"{companion_id or 'unknown'}-ledger-line-{line_number}"


def _entry_validity(entry: dict[str, Any]) -> dict[str, Any]:
    schema = str(entry.get("schema_version") or "")
    trust_state = str(entry.get("trust_state") or "")
    canonical = entry.get("canonical")
    authoritative = entry.get("authoritative")
    warnings: list[str] = []
    if schema and schema not in KNOWN_SCHEMA_VERSIONS:
        warnings.append("unknown_schema_version")
    if trust_state not in TRUST_STATES:
        warnings.append("trust_state_missing_or_unknown")
    if canonical is not False:
        warnings.append("canonical_flag_not_false")
    if authoritative is not False:
        warnings.append("authoritative_flag_not_false")
    return {
        "schema_known": not schema or schema in KNOWN_SCHEMA_VERSIONS,
        "trust_state_valid": trust_state in TRUST_STATES,
        "raw_or_noncanonical": trust_state == "raw" and canonical is False and authoritative is False,
        "canonical_false": canonical is False,
        "authoritative_false": authoritative is False,
        "warning_count": len(warnings),
        "warnings": warnings,
    }


def _normalize_ledger_entry(
    vault: Path,
    ledger_path: Path,
    entry: dict[str, Any],
    *,
    line_number: int,
    raw_line: str,
) -> dict[str, Any]:
    companion_id = str(entry.get("companion_id") or ledger_path.parent.name or "").strip().lower()
    memory_class = str(entry.get("memory_class") or "").strip().lower()
    validity = _entry_validity(entry)
    return {
        "source_type": "ledger_entry",
        "record_id": _record_id(entry, companion_id=companion_id, line_number=line_number),
        "companion_id": companion_id or None,
        "memory_class": memory_class or None,
        "content_preview": entry.get("content_preview") or "",
        "content_sha256": entry.get("content_sha256"),
        "memory_id": entry.get("memory_id"),
        "source_surface": entry.get("source_surface"),
        "source_event_id": entry.get("source_event_id"),
        "source_approval_id": entry.get("source_approval_id"),
        "source_memory_approval_digest": entry.get("source_memory_approval_digest"),
        "ledger_write_approval_id": entry.get("ledger_write_approval_id"),
        "ledger_write_approval_digest": entry.get("ledger_write_approval_digest"),
        "ledger_write_execution_id": entry.get("ledger_write_execution_id"),
        "source_proof_execution_id": entry.get("source_proof_execution_id"),
        "ledger_written_at_utc": entry.get("ledger_written_at_utc"),
        "trust_state": entry.get("trust_state"),
        "canonical": entry.get("canonical"),
        "authoritative": entry.get("authoritative"),
        "proof_only_source": entry.get("proof_only_source"),
        "ledger_write_performed": entry.get("ledger_write_performed") is True,
        "provider_call_performed": bool(entry.get("provider_call_performed")),
        "runtime_dispatch_performed": bool(entry.get("runtime_dispatch_performed")),
        "browser_control_performed": bool(entry.get("browser_control_performed")),
        "agent_bus_task_written": bool(entry.get("agent_bus_task_written")),
        "canonical_mutation_performed": bool(entry.get("canonical_mutation_performed")),
        "ledger_path": _rel(vault, ledger_path),
        "line_number": line_number,
        "line_sha256": _line_sha(raw_line),
        "entry_validity": validity,
        "malformed": False,
        "proof_status": "ledger_written",
    }


def _read_ledger_file(vault: Path, ledger_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    try:
        lines = ledger_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        errors.append(
            {
                "ledger_path": _rel(vault, ledger_path),
                "line_number": 0,
                "error": f"ledger_file_read_failed:{exc}",
            }
        )
        return records, errors
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(
                {
                    "ledger_path": _rel(vault, ledger_path),
                    "line_number": line_number,
                    "line_sha256": _line_sha(line),
                    "error": f"ledger_line_malformed:{exc}",
                }
            )
            continue
        if not isinstance(payload, dict):
            errors.append(
                {
                    "ledger_path": _rel(vault, ledger_path),
                    "line_number": line_number,
                    "line_sha256": _line_sha(line),
                    "error": "ledger_line_not_object",
                }
            )
            continue
        records.append(_normalize_ledger_entry(vault, ledger_path, payload, line_number=line_number, raw_line=line))
    return records, errors


def _read_ledger_records(vault: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    root = vault / MEMORY_ROOT
    warnings: list[str] = []
    if not root.exists():
        return [], [], warnings
    if not root.is_dir():
        return [], [{"ledger_path": _rel(vault, root), "line_number": 0, "error": "memory_root_not_directory"}], warnings
    records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for ledger_path in sorted(root.glob(f"*/{LEDGER_FILENAME}")):
        file_records, file_errors = _read_ledger_file(vault, ledger_path)
        records.extend(file_records)
        errors.extend(file_errors)
    if not records and not errors:
        warnings.append("companion_memory_root_exists_without_ledger_files")
    return records, errors, warnings


def _proof_backfill_records(
    vault: Path,
    *,
    include: bool,
    existing_source_approval_ids: set[str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not include:
        return [], {}
    proof_index = build_phase11_companion_memory_readback_search_preview(vault, limit=200)
    records: list[dict[str, Any]] = []
    for item in proof_index.get("results") or []:
        approval_id = str(item.get("approval_id") or "")
        if approval_id and approval_id in existing_source_approval_ids:
            continue
        records.append(
            {
                "source_type": "proof_only_evidence",
                "record_id": approval_id or f"proof-only-{len(records) + 1}",
                "companion_id": item.get("companion_id"),
                "memory_class": item.get("memory_class"),
                "content_preview": item.get("content_preview") or "",
                "content_sha256": item.get("content_sha256"),
                "source_surface": item.get("source_surface"),
                "source_event_id": item.get("source_event_id"),
                "source_approval_id": approval_id or None,
                "source_memory_approval_digest": item.get("memory_approval_digest"),
                "ledger_write_approval_id": None,
                "ledger_write_approval_digest": None,
                "ledger_write_execution_id": None,
                "source_proof_execution_id": item.get("proof_execution_id"),
                "ledger_written_at_utc": None,
                "trust_state": "raw",
                "canonical": False,
                "authoritative": False,
                "proof_only_source": True,
                "ledger_write_performed": False,
                "provider_call_performed": bool(item.get("provider_call_performed")),
                "runtime_dispatch_performed": bool(item.get("runtime_dispatch_performed")),
                "browser_control_performed": False,
                "agent_bus_task_written": bool(item.get("agent_bus_task_written")),
                "canonical_mutation_performed": bool(item.get("canonical_mutation_performed")),
                "ledger_path": None,
                "line_number": None,
                "line_sha256": None,
                "entry_validity": {
                    "schema_known": True,
                    "trust_state_valid": True,
                    "raw_or_noncanonical": True,
                    "canonical_false": True,
                    "authoritative_false": True,
                    "warning_count": 0,
                    "warnings": [],
                },
                "malformed": False,
                "proof_status": item.get("proof_status"),
            }
        )
    return records, proof_index


def _search_text(item: dict[str, Any]) -> str:
    fields = [
        "source_type",
        "record_id",
        "companion_id",
        "memory_class",
        "content_preview",
        "content_sha256",
        "source_surface",
        "source_event_id",
        "source_approval_id",
        "source_memory_approval_digest",
        "ledger_write_approval_id",
        "ledger_write_approval_digest",
        "ledger_write_execution_id",
        "trust_state",
        "proof_status",
        "ledger_path",
    ]
    return " ".join(str(item.get(field) or "") for field in fields).lower()


def _matches_filters(
    item: dict[str, Any],
    *,
    companion_id: str,
    memory_class: str,
    query: str,
) -> bool:
    if companion_id and str(item.get("companion_id") or "").lower() != companion_id:
        return False
    if memory_class and str(item.get("memory_class") or "").lower() != memory_class:
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


def _sort_key(item: dict[str, Any]) -> tuple[int, str, str]:
    source_rank = 0 if item.get("source_type") == "ledger_entry" else 1
    timestamp = str(item.get("ledger_written_at_utc") or "")
    return (source_rank, timestamp, str(item.get("record_id") or ""))


def _authority() -> dict[str, bool]:
    return {
        "read_only": True,
        "real_companion_memory_read_allowed": True,
        "companion_memory_ledger_read_allowed": True,
        "proof_backfill_read_allowed": True,
        "approval_artifact_read_allowed": True,
        "exact_once_marker_read_allowed": True,
        "approval_queue_write_allowed": False,
        "approval_consumption_allowed": False,
        "approval_execution_allowed": False,
        "memory_ledger_write_allowed": False,
        "memory_root_create_allowed": False,
        "provider_calls_allowed": False,
        "runtime_dispatch_allowed": False,
        "browser_control_allowed": False,
        "agent_bus_task_write_allowed": False,
        "gate_mutation_allowed": False,
        "git_mutation_allowed": False,
        "workflow_execution_allowed": False,
        "host_mutation_allowed": False,
        "canonical_mutation_allowed": False,
    }


def build_phase11_companion_memory_ledger_read_model_preview(
    vault_root: str | Path,
    *,
    companion_id: str | None = None,
    memory_class: str | None = None,
    query: str | None = None,
    limit: int = 20,
    include_proof_backfill: bool = True,
) -> dict[str, Any]:
    """Return a bounded read model over companion memory ledger/proof evidence."""

    vault = Path(vault_root).resolve()
    before_memory = _memory_snapshot(vault)
    filters = {
        "companion_id": _norm_filter(companion_id),
        "memory_class": _norm_filter(memory_class),
        "query": _norm_filter(query),
        "limit": _safe_limit(limit),
        "include_proof_backfill": bool(include_proof_backfill),
    }

    ledger_records, malformed_lines, warnings = _read_ledger_records(vault)
    existing_source_ids = {str(item.get("source_approval_id") or "") for item in ledger_records if item.get("source_approval_id")}
    proof_records, proof_index = _proof_backfill_records(
        vault,
        include=bool(include_proof_backfill),
        existing_source_approval_ids=existing_source_ids,
    )
    combined = sorted(ledger_records + proof_records, key=_sort_key, reverse=True)
    filtered = [
        item
        for item in combined
        if _matches_filters(
            item,
            companion_id=filters["companion_id"],
            memory_class=filters["memory_class"],
            query=filters["query"],
        )
    ]
    limited = filtered[: int(filters["limit"])]
    after_memory = _memory_snapshot(vault)
    memory_root_exists = (vault / MEMORY_ROOT).exists()
    ledger_paths = sorted(
        _rel(vault, path)
        for path in (vault / MEMORY_ROOT).glob(f"*/{LEDGER_FILENAME}")
    ) if memory_root_exists and (vault / MEMORY_ROOT).is_dir() else []
    invalid_count = sum(1 for item in ledger_records if (item.get("entry_validity") or {}).get("warning_count", 0))
    digest_material = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "filters": filters,
        "ledger_paths": ledger_paths,
        "ledger_entry_count": len(ledger_records),
        "proof_backfill_count": len(proof_records),
        "result_record_ids": [item.get("record_id") for item in limited],
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
        "summary": {
            "ledger_read_model_preview_ready": True,
            "memory_root_exists": memory_root_exists,
            "memory_root_read": True,
            "memory_ledger_read": True,
            "ledger_file_count": len(ledger_paths),
            "ledger_entry_count": len(ledger_records),
            "proof_backfill_count": len(proof_records),
            "combined_record_count": len(combined),
            "results_count": len(limited),
            "unfiltered_results_count": len(filtered),
            "malformed_line_count": len(malformed_lines),
            "invalid_entry_count": invalid_count,
            "memory_snapshot_unchanged": before_memory == after_memory,
            "memory_root_created": False,
            "memory_ledger_written": False,
            "approval_queue_write_performed": False,
            "approval_consumed": False,
            "provider_call_performed": False,
            "runtime_dispatch_performed": False,
            "browser_control_performed": False,
            "agent_bus_task_written": False,
            "canonical_mutation_performed": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "filters": filters,
        "results": limited,
        "records": limited,
        "ledger_records": [item for item in limited if item.get("source_type") == "ledger_entry"],
        "proof_backfill_records": [item for item in limited if item.get("source_type") == "proof_only_evidence"],
        "indexes": {
            "by_source_type": _count_by(combined, "source_type"),
            "by_companion": _count_by(combined, "companion_id"),
            "by_memory_class": _count_by(combined, "memory_class"),
            "by_trust_state": _count_by(combined, "trust_state"),
            "by_proof_status": _count_by(combined, "proof_status"),
        },
        "ledger_files": ledger_paths,
        "malformed_lines": malformed_lines,
        "proof_backfill_source": {
            "enabled": bool(include_proof_backfill),
            "surface": (proof_index or {}).get("surface"),
            "proof_result_count": ((proof_index or {}).get("summary") or {}).get("results_count"),
            "memory_root_read_by_proof_backfill": ((proof_index or {}).get("summary") or {}).get("memory_root_read"),
        },
        "source_paths": {
            "real_memory_root": MEMORY_ROOT.as_posix(),
            "ledger_glob": f"{MEMORY_ROOT.as_posix()}/*/{LEDGER_FILENAME}",
            "proof_backfill_surface": "phase11_companion_memory_readback_search_preview",
        },
        "memory_snapshot_proof": {
            "root_path": MEMORY_ROOT.as_posix(),
            "files_before": before_memory,
            "files_after": after_memory,
            "unchanged": before_memory == after_memory,
            "memory_root_created_by_this_surface": False,
            "memory_ledger_written_by_this_surface": False,
        },
        "authority": _authority(),
        "readiness": {
            "companion_memory_ledger_read_model_preview_ready": True,
            "companion_memory_real_ledger_read_model_ready": True,
            "companion_memory_ledger_read_only": True,
            "companion_memory_ledger_malformed_tolerated": True,
            "companion_memory_proof_backfill_ready": bool(include_proof_backfill),
            "companion_memory_ledger_writes_blocked": True,
            "companion_memory_provider_calls_blocked": True,
            "companion_memory_runtime_dispatch_blocked": True,
            "companion_memory_agent_bus_write_blocked": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "digest_proof": {
            "ledger_read_model_digest": _sha256_text(_canonical_json(digest_material)),
            "digest_material": digest_material,
        },
        "denied_by_this_surface": [
            "approval_queue_write",
            "approval_consumption",
            "approval_execution",
            "companion_memory_ledger_append",
            "companion_memory_directory_create",
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


def format_phase11_companion_memory_ledger_read_model_preview(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    filters = payload.get("filters") or {}
    lines = [
        "Phase 11 Companion Memory Ledger Read Model Preview",
        f"Status: {payload.get('status')}",
        f"Ledger files: {summary.get('ledger_file_count', 0)}",
        f"Ledger entries: {summary.get('ledger_entry_count', 0)}",
        f"Proof backfill records: {summary.get('proof_backfill_count', 0)}",
        f"Results: {summary.get('results_count', 0)}",
        f"Malformed lines: {summary.get('malformed_line_count', 0)}",
        f"Companion filter: {filters.get('companion_id') or 'all'}",
        f"Memory class filter: {filters.get('memory_class') or 'all'}",
        f"Query: {filters.get('query') or 'none'}",
        f"Read-only: {payload.get('read_only')}",
        f"Memory ledger written: {summary.get('memory_ledger_written')}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    warnings = payload.get("warnings") or []
    if warnings:
        lines.append("Warnings:")
        lines.extend(f"- {item}" for item in warnings[:8])
    malformed = payload.get("malformed_lines") or []
    if malformed:
        lines.append("Malformed ledger lines:")
        lines.extend(f"- {item.get('ledger_path')}:{item.get('line_number')} {item.get('error')}" for item in malformed[:8])
    return "\n".join(lines)
