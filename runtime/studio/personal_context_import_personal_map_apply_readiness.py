"""Personal Map apply readiness surface for Personal Context Import.

Reads the current Personal Map candidate queue and the applied graph, computes a
readiness digest over the candidate set, and supports queueing a digest-gated
apply approval request. It does NOT apply any candidates, mutate the graph, or
change candidate statuses.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.memory.candidate_store import (
    APPLIED,
    APPROVED,
    PENDING_REVIEW,
    PERSONAL_MAP_BLOCKED_EFFECTS,
    load_personal_map_candidates,
)
from runtime.memory.personal_map import (
    APPLIED_PERSONAL_MAP_GRAPH,
    build_personal_map_apply_preview,
    load_applied_personal_map_graph,
    personal_map_graph_hash,
)
from runtime.studio.service import ActionSpec, StudioService


MODEL_VERSION = "studio.personal_context_import_personal_map_apply_readiness.v1"
SURFACE_ID = "studio_personal_context_import_personal_map_apply_readiness"
PASS_ID = "personal-context-import-personal-map-apply-readiness"
APPROVAL_CLASS = "personal_map_apply_readiness"
NEXT_RECOMMENDED_PASS = "personal-context-import-personal-map-approved-apply-executor"
APPROVAL_ROOT = Path("runtime/studio/approvals/personal-context-import/personal-map-apply")

_APPLY_GATE_REQUIREMENTS = (
    "approval_id required",
    "exact personal_map_apply_readiness_digest required",
    "operator_approval_statement required (must contain digest)",
    "execute=True required",
    "exact_once_marker reserved before any graph write",
)

_AUTHORITY = {
    "reads_candidate_queue": True,
    "reads_personal_map_graph": True,
    "personal_map_apply_allowed": False,
    "candidate_status_mutation_allowed": False,
    "graph_write_allowed": False,
    "canonical_writeback_allowed": False,
    "provider_calls_allowed": False,
    "agent_bus_dispatch_allowed": False,
    "runtime_memory_mutation_allowed": False,
    "secret_values_read": False,
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compute_personal_map_apply_readiness_digest(candidates: list[Any]) -> str:
    """Stable digest over the candidate set (all statuses, sorted)."""
    items = sorted(
        [
            {
                "candidate_id": c.candidate_id,
                "candidate_type": c.candidate_type,
                "status": c.status,
            }
            for c in candidates
        ],
        key=lambda x: x["candidate_id"],
    )
    return _sha256_text(_canonical_json({"schema": MODEL_VERSION, "candidate_set": items}))


def _find_existing_approval(service: StudioService, digest: str) -> str | None:
    for req in service.list_pending():
        meta = req.action_spec.metadata or {}
        if (
            meta.get("personal_map_apply_readiness_approval") is True
            and meta.get("personal_map_apply_readiness_digest") == digest
        ):
            return req.approval_id
    return None


def build_personal_context_import_personal_map_apply_readiness(
    vault_root: str | Path,
) -> dict[str, Any]:
    """Return Personal Map apply readiness model: candidates + graph + digest."""
    vault = Path(vault_root).resolve()

    load_error: str | None = None
    all_candidates: list[Any] = []
    try:
        all_candidates = load_personal_map_candidates(vault)
    except Exception as exc:
        load_error = str(exc)

    pending = [c for c in all_candidates if c.status == PENDING_REVIEW]
    approved_list = [c for c in all_candidates if c.status == APPROVED]
    applied_list = [c for c in all_candidates if c.status == APPLIED]

    readiness_digest = compute_personal_map_apply_readiness_digest(all_candidates)

    graph_path = vault / APPLIED_PERSONAL_MAP_GRAPH
    graph_exists = graph_path.exists()
    graph_hash: str | None = None
    graph_node_count = 0
    graph_edge_count = 0
    graph_error: str | None = None
    try:
        graph = load_applied_personal_map_graph(vault)
        graph_hash = personal_map_graph_hash(graph)
        graph_node_count = len(graph.nodes)
        graph_edge_count = len(graph.edges)
    except Exception as exc:
        graph_error = str(exc)

    apply_preview: dict[str, Any] = {}
    preview_error: str | None = None
    try:
        apply_preview = build_personal_map_apply_preview(vault)
    except Exception as exc:
        preview_error = str(exc)

    pending_approval_ids: list[str] = []
    service = StudioService(vault)
    try:
        for req in service.list_pending():
            meta = req.action_spec.metadata or {}
            if meta.get("personal_map_apply_readiness_approval") is True:
                pending_approval_ids.append(req.approval_id)
    except Exception:
        pass

    if load_error:
        status = "blocked_candidate_load_error"
    elif not all_candidates:
        status = "no_candidates_found"
    elif not pending and not approved_list:
        status = "all_candidates_applied" if applied_list else "no_actionable_candidates"
    elif approved_list and not pending:
        status = "approved_candidates_ready_for_apply"
    else:
        status = "pending_review_candidates_available"

    can_request_approval = len(all_candidates) > 0 and not load_error

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "status": status,
        "readiness_digest": readiness_digest,
        "candidate_summary": {
            "total_candidate_count": len(all_candidates),
            "pending_review_count": len(pending),
            "approved_count": len(approved_list),
            "applied_count": len(applied_list),
            "node_count": sum(1 for c in all_candidates if c.candidate_type == "node"),
            "edge_count": sum(1 for c in all_candidates if c.candidate_type == "edge"),
            "pending_node_count": sum(1 for c in pending if c.candidate_type == "node"),
            "pending_edge_count": sum(1 for c in pending if c.candidate_type == "edge"),
            "approved_node_count": sum(1 for c in approved_list if c.candidate_type == "node"),
            "approved_edge_count": sum(1 for c in approved_list if c.candidate_type == "edge"),
            "pending_candidate_ids": [c.candidate_id for c in pending],
            "approved_candidate_ids": [c.candidate_id for c in approved_list],
        },
        "apply_preview": apply_preview,
        "preview_error": preview_error,
        "graph_state": {
            "graph_path": APPLIED_PERSONAL_MAP_GRAPH.as_posix(),
            "graph_present": graph_exists,
            "graph_node_count": graph_node_count,
            "graph_edge_count": graph_edge_count,
            "graph_hash": graph_hash,
            "graph_error": graph_error,
        },
        "pending_approval_ids": pending_approval_ids,
        "approval_class": APPROVAL_CLASS,
        "can_request_approval": can_request_approval,
        "apply_gate_requirements": list(_APPLY_GATE_REQUIREMENTS),
        "blocked_effects": list(PERSONAL_MAP_BLOCKED_EFFECTS),
        "authority": dict(_AUTHORITY),
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        "load_error": load_error,
    }


def request_personal_context_import_personal_map_apply_readiness_approval(
    vault_root: str | Path,
    *,
    expected_readiness_digest: str,
    operator_note: str = "",
    operator_id: str = "studio-operator",
) -> dict[str, Any]:
    """Queue a Personal Map apply readiness approval (exact-digest-gated)."""
    vault = Path(vault_root).resolve()
    readiness = build_personal_context_import_personal_map_apply_readiness(vault)
    actual_digest = str(readiness.get("readiness_digest") or "")
    expected = str(expected_readiness_digest or "").strip()

    blockers: list[str] = []
    if not expected:
        blockers.append("expected_readiness_digest_required")
    elif actual_digest != expected:
        blockers.append("readiness_digest_mismatch")
    if readiness.get("load_error"):
        blockers.append("candidate_load_error")
    total = readiness.get("candidate_summary", {}).get("total_candidate_count", 0)
    if total == 0:
        blockers.append("no_candidates_to_apply")

    if blockers:
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "generated_at": _now_utc(),
            "vault_root": str(vault),
            "approval_queued": False,
            "blockers": blockers,
            "actual_readiness_digest": actual_digest,
            "expected_readiness_digest": expected,
        }

    service = StudioService(vault)
    existing = _find_existing_approval(service, actual_digest)
    if existing:
        return {
            "ok": True,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "generated_at": _now_utc(),
            "vault_root": str(vault),
            "approval_queued": False,
            "approval_already_exists": True,
            "approval_id": existing,
            "readiness_digest": actual_digest,
            "blockers": [],
        }

    content_payload = {
        "record_type": "personal_context_import_personal_map_apply_readiness_approval",
        "schema_version": MODEL_VERSION,
        "readiness_digest": actual_digest,
        "candidate_summary": readiness.get("candidate_summary"),
        "apply_preview": readiness.get("apply_preview"),
        "source_text_included": False,
        "raw_full_memory_injection_allowed": False,
        "personal_map_apply_allowed_after_executor_approval": True,
        "canonical_writeback_allowed": False,
        "future_executor_requires_matching_digest": True,
        "operator_note": operator_note,
    }
    target_path = (
        APPROVAL_ROOT / f"personal-map-apply-readiness-{actual_digest[:16]}.json"
    ).as_posix()
    spec = ActionSpec(
        action_type="create_file",
        target_path=target_path,
        content=json.dumps(content_payload, indent=2, sort_keys=True) + "\n",
        metadata={
            "personal_map_apply_readiness_approval": True,
            "personal_map_apply_readiness_digest": actual_digest,
            "source_surface": SURFACE_ID,
            "required_approval_class": APPROVAL_CLASS,
            "personal_map_apply_allowed": False,
            "source_text_included": False,
            "canonical_writeback_allowed": False,
        },
        submitted_by=operator_id,
        note=operator_note or "Personal Map apply readiness approval (digest-gated).",
    )
    req = service.queue_for_approval(spec)
    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "approval_queued": True,
        "approval_already_exists": False,
        "approval_id": req.approval_id,
        "readiness_digest": actual_digest,
        "blockers": [],
    }


def format_personal_context_import_personal_map_apply_readiness(
    payload: dict[str, Any],
) -> str:
    summary = payload.get("candidate_summary") or {}
    graph = payload.get("graph_state") or {}
    lines = [
        "Personal Context Import Personal Map Apply Readiness",
        f"Status: {payload.get('status')}",
        f"Readiness digest: {(payload.get('readiness_digest') or 'missing')[:24]}...",
        f"Total candidates: {summary.get('total_candidate_count', 0)}",
        f"  Pending review: {summary.get('pending_review_count', 0)}",
        f"  Approved: {summary.get('approved_count', 0)}",
        f"  Applied: {summary.get('applied_count', 0)}",
        f"Graph present: {graph.get('graph_present')}",
        f"Graph nodes: {graph.get('graph_node_count', 0)}",
        f"Graph edges: {graph.get('graph_edge_count', 0)}",
        f"Can request approval: {payload.get('can_request_approval')}",
        f"Next recommended pass: {payload.get('next_recommended_pass')}",
    ]
    if payload.get("load_error"):
        lines.append(f"Load error: {payload['load_error']}")
    return "\n".join(lines)
