"""Phase 11 companion memory context-readiness preview.

This surface prepares a bounded, cited context packet from the governed
companion-memory ledger read model. It may read existing raw companion-memory
ledger entries and proof backfill records, but it does not call providers,
persist conversations, write approvals, append memory, dispatch runtimes, or
promote canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.phase11_companion_memory_ledger_read_model_preview import (
    build_phase11_companion_memory_ledger_read_model_preview,
)
from runtime.studio.phase11_companion_memory_ledger_write_approval_preview import MEMORY_ROOT


MODEL_VERSION = "studio.phase11_companion_memory_context_readiness_preview.v1"
SURFACE_ID = "phase11_companion_memory_context_readiness_preview"
PASS_ID = "phase11-companion-memory-context-readiness-preview"
STATUS = "COMPLETE / READ-ONLY / CONTEXT READINESS PREVIEW / VERIFIED"
NO_RECORDS_STATUS = "READY / READ-ONLY / NO CONTEXT RECORDS"
NEXT_RECOMMENDED_PASS = "operator-provide-openai-secret-reference"
DEFAULT_LIMIT = 8
DEFAULT_MAX_CONTEXT_CHARS = 2400
MAX_LIMIT = 50
MAX_CONTEXT_CHARS = 12000


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
        parsed = int(limit or DEFAULT_LIMIT)
    except (TypeError, ValueError):
        parsed = DEFAULT_LIMIT
    return max(1, min(parsed, MAX_LIMIT))


def _safe_char_budget(max_context_chars: int | None) -> int:
    try:
        parsed = int(max_context_chars or DEFAULT_MAX_CONTEXT_CHARS)
    except (TypeError, ValueError):
        parsed = DEFAULT_MAX_CONTEXT_CHARS
    return max(256, min(parsed, MAX_CONTEXT_CHARS))


def _safe_preview(value: Any, *, max_chars: int = 480) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 12)].rstrip() + " [truncated]"


def _item_is_context_safe(record: dict[str, Any]) -> bool:
    validity = record.get("entry_validity") if isinstance(record.get("entry_validity"), dict) else {}
    return (
        str(record.get("trust_state") or "") == "raw"
        and record.get("canonical") is False
        and record.get("authoritative") is False
        and not bool(record.get("provider_call_performed"))
        and not bool(record.get("runtime_dispatch_performed"))
        and not bool(record.get("browser_control_performed"))
        and not bool(record.get("agent_bus_task_written"))
        and not bool(record.get("canonical_mutation_performed"))
        and bool(validity.get("raw_or_noncanonical", True))
    )


def _source_ref(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_type": record.get("source_type"),
        "record_id": record.get("record_id"),
        "companion_id": record.get("companion_id"),
        "memory_class": record.get("memory_class"),
        "ledger_path": record.get("ledger_path"),
        "line_number": record.get("line_number"),
        "line_sha256": record.get("line_sha256"),
        "content_sha256": record.get("content_sha256"),
        "source_approval_id": record.get("source_approval_id"),
        "ledger_write_approval_id": record.get("ledger_write_approval_id"),
        "ledger_write_approval_digest": record.get("ledger_write_approval_digest"),
        "ledger_write_execution_id": record.get("ledger_write_execution_id"),
        "source_proof_execution_id": record.get("source_proof_execution_id"),
        "proof_status": record.get("proof_status"),
    }


def _context_line(index: int, record: dict[str, Any], content: str) -> str:
    return (
        f"[{index}] companion={record.get('companion_id') or 'unknown'}; "
        f"class={record.get('memory_class') or 'unknown'}; "
        f"trust={record.get('trust_state') or 'unknown'}; "
        f"canonical={record.get('canonical')}; authoritative={record.get('authoritative')}; "
        f"source={record.get('source_type') or 'unknown'}:{record.get('record_id') or 'unknown'}; "
        f"content={content}"
    )


def _context_items(records: list[dict[str, Any]], *, max_chars: int) -> tuple[list[dict[str, Any]], dict[str, int]]:
    items: list[dict[str, Any]] = []
    used_chars = 0
    skipped_for_budget = 0
    unsafe_records = 0
    for record in records:
        safe = _item_is_context_safe(record)
        if not safe:
            unsafe_records += 1
            continue
        content = _safe_preview(record.get("content_preview") or "", max_chars=520)
        if not content:
            unsafe_records += 1
            continue
        next_index = len(items) + 1
        line = _context_line(next_index, record, content)
        line_len = len(line)
        if used_chars + line_len > max_chars:
            remaining = max_chars - used_chars
            if remaining < 120 or items:
                skipped_for_budget += 1
                continue
            line = line[:remaining].rstrip()
            content = content[: max(0, len(content) - (line_len - remaining))].rstrip()
            line_len = len(line)
        used_chars += line_len
        items.append(
            {
                "context_item_id": f"companion-context-{next_index:02d}-{_sha256_text(line)[:12]}",
                "position": next_index,
                "content_preview": content,
                "context_line": line,
                "context_chars": line_len,
                "safe_for_provider_context_preview": True,
                "requires_human_review_for_canonical_use": True,
                "trust_state": record.get("trust_state"),
                "canonical": record.get("canonical"),
                "authoritative": record.get("authoritative"),
                "raw_noncanonical_boundary": True,
                "source_ref": _source_ref(record),
            }
        )
    return items, {
        "context_chars": used_chars,
        "skipped_for_budget": skipped_for_budget,
        "unsafe_records": unsafe_records,
    }


def _authority() -> dict[str, bool]:
    return {
        "read_only": True,
        "context_preview_allowed": True,
        "real_companion_memory_read_allowed": True,
        "ledger_read_model_allowed": True,
        "proof_backfill_read_allowed": True,
        "provider_context_packet_preview_allowed": True,
        "provider_context_delivery_allowed": False,
        "model_calls_allowed": False,
        "provider_calls_allowed": False,
        "approval_queue_write_allowed": False,
        "approval_consumption_allowed": False,
        "approval_execution_allowed": False,
        "memory_ledger_write_allowed": False,
        "memory_root_create_allowed": False,
        "conversation_persistence_allowed": False,
        "runtime_dispatch_allowed": False,
        "browser_control_allowed": False,
        "agent_bus_task_write_allowed": False,
        "provider_switch_allowed": False,
        "credential_values_visible": False,
        "gate_mutation_allowed": False,
        "git_mutation_allowed": False,
        "workflow_execution_allowed": False,
        "host_mutation_allowed": False,
        "canonical_mutation_allowed": False,
    }


def build_phase11_companion_memory_context_readiness_preview(
    vault_root: str | Path,
    *,
    companion_id: str | None = None,
    memory_class: str | None = None,
    query: str | None = None,
    limit: int = DEFAULT_LIMIT,
    max_context_chars: int = DEFAULT_MAX_CONTEXT_CHARS,
    include_proof_backfill: bool = True,
) -> dict[str, Any]:
    """Prepare a bounded, non-authoritative context packet preview."""

    vault = Path(vault_root).resolve()
    before_memory = _memory_snapshot(vault)
    filters = {
        "companion_id": _norm_filter(companion_id),
        "memory_class": _norm_filter(memory_class),
        "query": _norm_filter(query),
        "limit": _safe_limit(limit),
        "max_context_chars": _safe_char_budget(max_context_chars),
        "include_proof_backfill": bool(include_proof_backfill),
    }
    read_model = build_phase11_companion_memory_ledger_read_model_preview(
        vault,
        companion_id=filters["companion_id"],
        memory_class=filters["memory_class"],
        query=filters["query"],
        limit=filters["limit"],
        include_proof_backfill=filters["include_proof_backfill"],
    )
    records = list(read_model.get("results") or [])
    items, item_stats = _context_items(records, max_chars=int(filters["max_context_chars"]))
    context_lines = [str(item.get("context_line") or "") for item in items]
    context_text = "\n".join(context_lines)
    context_ready = bool(items)
    after_memory = _memory_snapshot(vault)
    digest_material = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "filters": filters,
        "read_model_digest": (read_model.get("digest_proof") or {}).get("ledger_read_model_digest"),
        "source_record_ids": [item.get("record_id") for item in records],
        "context_item_ids": [item.get("context_item_id") for item in items],
        "context_text_sha256": _sha256_text(context_text) if context_text else None,
        "memory_files_unchanged": before_memory == after_memory,
    }
    packet_digest = _sha256_text(_canonical_json(digest_material))
    blocked_reasons = []
    if not context_ready:
        blocked_reasons.append("no_context_records_found")
    if item_stats["unsafe_records"]:
        blocked_reasons.append("unsafe_or_non_context_records_excluded")
    if item_stats["skipped_for_budget"]:
        blocked_reasons.append("context_budget_excluded_records")

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS if context_ready else NO_RECORDS_STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "approval_gated": False,
        "summary": {
            "context_readiness_preview_ready": True,
            "context_packet_ready": context_ready,
            "context_item_count": len(items),
            "source_record_count": len(records),
            "ledger_entry_count": (read_model.get("summary") or {}).get("ledger_entry_count", 0),
            "proof_backfill_count": (read_model.get("summary") or {}).get("proof_backfill_count", 0),
            "context_chars": item_stats["context_chars"],
            "max_context_chars": filters["max_context_chars"],
            "records_excluded_as_unsafe": item_stats["unsafe_records"],
            "records_excluded_by_budget": item_stats["skipped_for_budget"],
            "raw_noncanonical_context_only": True,
            "provider_context_delivery_allowed": False,
            "provider_call_performed": False,
            "model_call_performed": False,
            "approval_queue_write_performed": False,
            "approval_consumed": False,
            "memory_ledger_written": False,
            "conversation_written": False,
            "runtime_dispatch_performed": False,
            "browser_control_performed": False,
            "agent_bus_task_written": False,
            "canonical_mutation_performed": False,
            "memory_snapshot_unchanged": before_memory == after_memory,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "filters": filters,
        "context_packet_preview": {
            "packet_id": f"companion-context-{packet_digest[:16]}",
            "packet_digest": packet_digest,
            "ready_for_chat_display": True,
            "ready_for_provider_context_preview": context_ready,
            "provider_execution_allowed": False,
            "requires_openai_secret_reference_before_live_use": True,
            "requires_operator_approval_before_live_model_call": True,
            "context_lines": context_lines,
            "context_text_preview": context_text,
            "context_item_ids": [item.get("context_item_id") for item in items],
            "boundary_notice": (
                "Companion memory is raw, non-canonical, non-authoritative context. "
                "It may guide tone or preferences only after a future approved provider handoff."
            ),
        },
        "context_items": items,
        "source_read_model": {
            "surface": read_model.get("surface"),
            "status": read_model.get("status"),
            "summary": read_model.get("summary") or {},
            "filters": read_model.get("filters") or {},
            "digest": (read_model.get("digest_proof") or {}).get("ledger_read_model_digest"),
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
            "companion_memory_context_readiness_preview_ready": True,
            "companion_memory_context_packet_ready": context_ready,
            "companion_memory_context_packet_raw_noncanonical": True,
            "companion_memory_context_for_chat_ui_ready": True,
            "companion_memory_context_provider_delivery_blocked": True,
            "companion_memory_context_provider_calls_blocked": True,
            "companion_memory_context_requires_openai_secret_reference": True,
            "companion_memory_context_requires_operator_approval_for_live_use": True,
            "companion_memory_context_writes_blocked": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "digest_proof": {
            "context_readiness_digest": packet_digest,
            "digest_material": digest_material,
        },
        "denied_by_this_surface": [
            "provider_context_delivery",
            "provider_api_call",
            "model_response_generation",
            "approval_queue_write",
            "approval_consumption",
            "approval_execution",
            "companion_memory_ledger_append",
            "conversation_log_write",
            "runtime_dispatch",
            "browser_control",
            "agent_bus_task_write",
            "provider_switch",
            "credential_value_display",
            "gate_mutation",
            "git_mutation",
            "workflow_execution",
            "host_mutation",
            "canonical_writeback",
        ],
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        "warnings": list(read_model.get("warnings") or []),
    }


def format_phase11_companion_memory_context_readiness_preview(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    packet = payload.get("context_packet_preview") or {}
    filters = payload.get("filters") or {}
    lines = [
        "Phase 11 Companion Memory Context Readiness Preview",
        f"Status: {payload.get('status')}",
        f"Context packet ready: {summary.get('context_packet_ready')}",
        f"Context items: {summary.get('context_item_count', 0)}",
        f"Source records: {summary.get('source_record_count', 0)}",
        f"Ledger entries: {summary.get('ledger_entry_count', 0)}",
        f"Proof backfill records: {summary.get('proof_backfill_count', 0)}",
        f"Context chars: {summary.get('context_chars', 0)} / {summary.get('max_context_chars', 0)}",
        f"Companion filter: {filters.get('companion_id') or 'all'}",
        f"Memory class filter: {filters.get('memory_class') or 'all'}",
        f"Query: {filters.get('query') or 'none'}",
        f"Provider execution allowed: {packet.get('provider_execution_allowed')}",
        f"Requires OpenAI secret reference: {packet.get('requires_openai_secret_reference_before_live_use')}",
        f"Memory snapshot unchanged: {summary.get('memory_snapshot_unchanged')}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers[:10])
    return "\n".join(lines)
