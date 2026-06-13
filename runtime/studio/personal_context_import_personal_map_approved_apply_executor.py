"""Approved Personal Map apply executor for Personal Context Import.

Consumes one digest-bound Personal Map apply readiness approval. For each
pending-review candidate covered by the approval, appends an approved-status
record to the candidate JSONL log, then calls the governed
apply_approved_personal_map_candidates() function which writes graph.json and an
audit JSONL record.

Exact-once marker prevents duplicate apply runs. Does NOT mutate canonical vault
files, write runtime memory, dispatch Agent Bus tasks, or call providers.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.memory.candidate_store import (
    APPROVED,
    PENDING_REVIEW,
    PersonalMapCandidate,
    load_personal_map_candidates,
    personal_map_candidate_log_path,
)
from runtime.memory.personal_map import (
    APPLIED_PERSONAL_MAP_GRAPH,
    apply_approved_personal_map_candidates,
    build_personal_map_apply_preview,
    personal_map_graph_hash,
    load_applied_personal_map_graph,
)
from runtime.studio.personal_context_import_personal_map_apply_readiness import (
    APPROVAL_CLASS,
    MODEL_VERSION as READINESS_MODEL_VERSION,
    SURFACE_ID as READINESS_SURFACE_ID,
    compute_personal_map_apply_readiness_digest,
)
from runtime.studio.service import StudioService


MODEL_VERSION = "studio.personal_context_import_personal_map_approved_apply_executor.v1"
SURFACE_ID = "studio_personal_context_import_personal_map_approved_apply_executor"
PASS_ID = "personal-context-import-personal-map-approved-apply-executor"
STATUS_OK = "COMPLETE / PERSONAL MAP APPLY EXECUTED / GRAPH WRITTEN"
STATUS_BLOCKED = "BLOCKED / PERSONAL MAP APPLY / NO GRAPH WRITE"
STATUS_FAILED = "FAILED / PERSONAL MAP APPLY / PARTIAL CHECK REQUIRED"
NEXT_RECOMMENDED_PASS = "personal-context-import-runtime-memory-mutation-readiness"
MARKER_DIR = Path("runtime/studio/approvals/personal-context-import/_personal_map_apply_markers")
EVIDENCE_ROOT = Path("runtime/studio/context-import/personal-map-apply-executions")
AUDIT_DIR = Path("07_LOGS") / "Agent-Activity"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _approval_content(service: StudioService, approval_id: str) -> tuple[dict[str, Any] | None, str | None]:
    req = service.get_approval(approval_id)
    if req is None:
        return None, "approval_not_found"
    try:
        content = json.loads(str(req.action_spec.content or "{}"))
    except json.JSONDecodeError as exc:
        return None, f"approval_content_malformed:{exc}"
    if not isinstance(content, dict):
        return None, "approval_content_not_object"
    return content, None


def _content_blockers(
    service: StudioService,
    approval_id: str,
    content: dict[str, Any] | None,
    expected_digest: str,
) -> list[str]:
    req = service.get_approval(approval_id)
    if req is None:
        return ["approval_not_found"]
    content = content or {}
    blockers: list[str] = []
    meta = req.action_spec.metadata or {}
    if req.status not in {"pending", "approved"}:
        blockers.append(f"approval_status_not_pending_or_approved:{req.status}")
    if meta.get("personal_map_apply_readiness_approval") is not True:
        blockers.append("approval_not_personal_map_apply_readiness")
    if meta.get("required_approval_class") != APPROVAL_CLASS:
        blockers.append("approval_class_mismatch")
    if content.get("record_type") != "personal_context_import_personal_map_apply_readiness_approval":
        blockers.append("approval_record_type_mismatch")
    if content.get("schema_version") != READINESS_MODEL_VERSION:
        blockers.append("approval_schema_version_mismatch")
    if content.get("source_text_included") is not False:
        blockers.append("approval_source_text_included")
    if content.get("canonical_writeback_allowed") is not False:
        blockers.append("approval_canonical_writeback_allowed")
    if content.get("future_executor_requires_matching_digest") is not True:
        blockers.append("approval_missing_matching_digest_requirement")
    stored_digest = str(content.get("readiness_digest") or "")
    if not expected_digest:
        blockers.append("expected_readiness_digest_required")
    elif stored_digest and stored_digest != expected_digest:
        blockers.append("readiness_digest_mismatch")
    metadata_digest = str(meta.get("personal_map_apply_readiness_digest") or "")
    if metadata_digest and expected_digest and metadata_digest != expected_digest:
        blockers.append("metadata_digest_mismatch")
    return blockers


def _statement_blockers(statement: str, expected_digest: str) -> list[str]:
    if not statement.strip():
        return ["operator_approval_statement_required"]
    blockers: list[str] = []
    if expected_digest and expected_digest not in statement:
        blockers.append("operator_approval_statement_digest_missing")
    low = statement.lower()
    if "approve" not in low or "personal map" not in low:
        blockers.append("operator_approval_statement_phrase_missing")
    return blockers


def _append_approved_record(vault: Path, candidate: PersonalMapCandidate, applied_at: str) -> None:
    """Append an approved-status update record for the candidate to the JSONL log."""
    updated = PersonalMapCandidate(
        candidate_id=candidate.candidate_id,
        candidate_type=candidate.candidate_type,
        reason=candidate.reason,
        node=candidate.node,
        edge=candidate.edge,
        source_card_id=candidate.source_card_id,
        source_feedback_candidate_id=candidate.source_feedback_candidate_id,
        source_deck_path=candidate.source_deck_path,
        created_at=candidate.created_at,
        status=APPROVED,
        review_required=candidate.review_required,
        candidate_only=candidate.candidate_only,
        canonical_writeback_allowed=candidate.canonical_writeback_allowed,
        applied_to_personal_map=False,
        mutates_canonical_state=candidate.mutates_canonical_state,
        approves_memory=candidate.approves_memory,
        creates_task=candidate.creates_task,
        second_datastore_write_allowed=candidate.second_datastore_write_allowed,
        confidence=candidate.confidence,
        data_class=candidate.data_class,
        sensitivity=candidate.sensitivity,
        no_secret_scan=candidate.no_secret_scan,
        status_history=list(candidate.status_history)
        + [{"status": APPROVED, "timestamp": applied_at, "actor": "personal_map_approved_apply_executor"}],
        revisions=candidate.revisions,
        reviewer="personal_map_approved_apply_executor",
        reviewed_at=applied_at,
    )
    updated.validate()
    log_path = personal_map_candidate_log_path(vault, created_at=candidate.created_at)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(updated.to_dict(), sort_keys=True))
        handle.write("\n")


def _write_evidence(
    *,
    vault: Path,
    approval_id: str,
    execution_id: str,
    executor_digest: str,
    readiness_digest: str,
    apply_result: dict[str, Any],
    operator_id: str,
) -> dict[str, str]:
    root = vault / EVIDENCE_ROOT / approval_id
    root.mkdir(parents=True, exist_ok=True)
    evidence = {
        "schema_version": "personal_context_import_personal_map_apply_execution_evidence.v1",
        "surface": SURFACE_ID,
        "pass": PASS_ID,
        "approval_id": approval_id,
        "execution_id": execution_id,
        "executor_digest": executor_digest,
        "readiness_digest": readiness_digest,
        "operator_id": operator_id,
        "graph_hash_before": apply_result.get("graph_hash_before"),
        "graph_hash_after": apply_result.get("graph_hash_after"),
        "applied_node_ids": apply_result.get("applied_node_ids"),
        "applied_edge_ids": apply_result.get("applied_edge_ids"),
        "already_applied_candidate_count": apply_result.get("already_applied_candidate_count"),
        "writes": apply_result.get("writes"),
        "source_text_included": False,
        "canonical_writeback_allowed": False,
        "personal_map_apply_performed": True,
        "runtime_memory_mutation_performed": False,
        "agent_bus_task_written": False,
        "provider_call_performed": False,
        "credential_read_performed": False,
        "generated_at_utc": _now_utc(),
    }
    rollback = {
        "schema_version": "personal_context_import_personal_map_apply_rollback_plan.v1",
        "surface": SURFACE_ID,
        "approval_id": approval_id,
        "execution_id": execution_id,
        "rollback_scope": "personal_map_graph_json_only",
        "manual_review_required_before_rollback": True,
        "target_path": APPLIED_PERSONAL_MAP_GRAPH.as_posix(),
        "graph_hash_before": apply_result.get("graph_hash_before"),
        "rollback_instruction": (
            "To roll back: restore runtime/memory/personal-map/graph.json to the "
            "snapshot matching graph_hash_before. Candidate JSONL records remain "
            "append-only and cannot be rolled back by removing lines."
        ),
        "created_at_utc": _now_utc(),
    }
    _write_json(root / "execution-evidence.json", evidence)
    _write_json(root / "rollback-plan.json", rollback)
    return {
        "execution_evidence": _rel(vault, root / "execution-evidence.json"),
        "rollback_plan": _rel(vault, root / "rollback-plan.json"),
    }


def _write_audit(
    *,
    vault: Path,
    approval_id: str,
    execution_id: str,
    executor_digest: str,
    readiness_digest: str,
    applied_nodes: list[str],
    applied_edges: list[str],
    operator_id: str,
) -> str:
    path = vault / AUDIT_DIR / f"{_now_utc()[:10]}-personal-context-personal-map-apply-{approval_id[:12]}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    nodes = "\n".join(f"- `{n}`" for n in applied_nodes) or "- none"
    edges = "\n".join(f"- `{e}`" for e in applied_edges) or "- none"
    path.write_text(
        f"""# Personal Context Personal Map Apply Execution

- Runtime: Codex / Studio governed executor
- Surface: `{SURFACE_ID}`
- Approval id: `{approval_id}`
- Execution id: `{execution_id}`
- Readiness digest: `{readiness_digest}`
- Executor digest: `{executor_digest}`
- Operator id: `{operator_id}`

## Applied Nodes

{nodes}

## Applied Edges

{edges}

## Boundary

This pass applied reviewed Personal Map candidates to graph.json only. It did not
mutate canonical vault files, write runtime memory, dispatch Agent Bus tasks, call
providers, read credentials, or inject raw context.
""",
        encoding="utf-8",
    )
    return _rel(vault, path)


def execute_personal_context_import_personal_map_approved_apply(
    vault_root: str | Path,
    *,
    approval_id: str,
    expected_readiness_digest: str,
    operator_approval_statement: str = "",
    operator_id: str = "studio-operator",
    execute: bool = False,
) -> dict[str, Any]:
    """Consume an approved Personal Map apply readiness request and write graph.json."""
    vault = Path(vault_root).resolve()
    approval_id_str = str(approval_id or "").strip()
    expected = str(expected_readiness_digest or "").strip()
    statement = str(operator_approval_statement or "")
    operator = str(operator_id or "studio-operator")
    marker_path = (vault / MARKER_DIR / f"{approval_id_str or 'missing'}.json").resolve()

    blockers: list[str] = []
    if not approval_id_str:
        blockers.append("approval_id_required")
    if not expected:
        blockers.append("expected_readiness_digest_required")
    if not execute:
        blockers.append("execute_flag_required")

    service = StudioService(vault)
    content, content_error = _approval_content(service, approval_id_str)
    if content_error:
        blockers.append(content_error)

    if approval_id_str and not content_error:
        blockers.extend(_content_blockers(service, approval_id_str, content, expected))
    blockers.extend(_statement_blockers(statement, expected))

    # Verify current candidate set matches the digest in approval
    try:
        all_candidates = load_personal_map_candidates(vault)
    except Exception as exc:
        blockers.append(f"candidate_load_error:{exc}")
        all_candidates = []
    current_digest = compute_personal_map_apply_readiness_digest(all_candidates)
    if expected and current_digest != expected:
        blockers.append("current_candidate_set_digest_mismatch")

    if marker_path.exists():
        blockers.append("exact_once_marker_already_present")

    if blockers:
        unique = list(dict.fromkeys(blockers))
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "pass": PASS_ID,
            "status": STATUS_BLOCKED,
            "generated_at_utc": _now_utc(),
            "vault_root": str(vault),
            "approval_id": approval_id_str,
            "blocked_reasons": unique,
            "personal_map_apply_performed": False,
            "runtime_memory_mutation_performed": False,
            "agent_bus_task_written": False,
            "provider_call_performed": False,
            "credential_read_performed": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        }

    # Build executor digest
    executor_material = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "approval_id": approval_id_str,
        "readiness_digest": expected,
    }
    executor_digest = _sha256_text(_canonical_json(executor_material))
    execution_id = f"personal-map-apply-{executor_digest[:20]}"
    applied_at = _now_utc()

    assert content is not None
    req = service.get_approval(approval_id_str)
    assert req is not None

    try:
        # Reserve exact-once marker before writes
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(
            marker_path,
            {
                "schema_version": "personal_context_import_personal_map_apply_marker.v1",
                "status": "executing",
                "approval_id": approval_id_str,
                "execution_id": execution_id,
                "readiness_digest": expected,
                "executor_digest": executor_digest,
                "operator_id": operator,
                "applied_at_utc": applied_at,
            },
        )

        # Transition pending_review candidates to approved
        pending = [c for c in all_candidates if c.status == PENDING_REVIEW]
        for candidate in pending:
            _append_approved_record(vault, candidate, applied_at)

        # Apply approved candidates to graph.json
        apply_result = apply_approved_personal_map_candidates(
            vault,
            operator_confirmed=True,
            applied_at=applied_at,
        )

        # Update marker to executed
        _write_json(
            marker_path,
            {
                "schema_version": "personal_context_import_personal_map_apply_marker.v1",
                "status": "executed",
                "approval_id": approval_id_str,
                "execution_id": execution_id,
                "readiness_digest": expected,
                "executor_digest": executor_digest,
                "operator_id": operator,
                "applied_node_ids": apply_result.get("applied_node_ids", []),
                "applied_edge_ids": apply_result.get("applied_edge_ids", []),
                "applied_at_utc": applied_at,
            },
        )

        # Update approval record
        req.status = "executed"
        req.execution_id = execution_id
        req.execution_started_at = applied_at
        req.execution_finished_at = _now_utc()
        req.execution_status = "completed"
        req.result_action_id = execution_id
        req.execution_error = ""
        req.reviewed_by = operator
        req.reason = statement
        req.updated_at = req.execution_finished_at
        meta = dict(req.action_spec.metadata or {})
        meta.update(
            {
                "personal_map_apply_executed": True,
                "executor_digest": executor_digest,
                "applied_node_count": len(apply_result.get("applied_node_ids", [])),
                "applied_edge_count": len(apply_result.get("applied_edge_ids", [])),
                "personal_map_apply_performed": True,
                "next_required_pass": NEXT_RECOMMENDED_PASS,
            }
        )
        req.action_spec.metadata = meta
        service._write_approval_record(req)  # type: ignore[attr-defined]

        evidence_paths = _write_evidence(
            vault=vault,
            approval_id=approval_id_str,
            execution_id=execution_id,
            executor_digest=executor_digest,
            readiness_digest=expected,
            apply_result=apply_result,
            operator_id=operator,
        )
        audit_path = _write_audit(
            vault=vault,
            approval_id=approval_id_str,
            execution_id=execution_id,
            executor_digest=executor_digest,
            readiness_digest=expected,
            applied_nodes=apply_result.get("applied_node_ids", []),
            applied_edges=apply_result.get("applied_edge_ids", []),
            operator_id=operator,
        )

    except Exception as exc:
        error = str(exc)
        try:
            _write_json(
                marker_path,
                {
                    "schema_version": "personal_context_import_personal_map_apply_marker.v1",
                    "status": "execution_failed",
                    "approval_id": approval_id_str,
                    "execution_id": execution_id,
                    "readiness_digest": expected,
                    "executor_digest": executor_digest,
                    "error": error,
                },
            )
        except Exception:
            pass
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "pass": PASS_ID,
            "status": STATUS_FAILED,
            "generated_at_utc": _now_utc(),
            "vault_root": str(vault),
            "approval_id": approval_id_str,
            "blocked_reasons": [f"personal_map_apply_execution_failed:{error}"],
            "personal_map_apply_performed": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        }

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS_OK,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "approval_id": approval_id_str,
        "execution_id": execution_id,
        "executor_digest": executor_digest,
        "readiness_digest": expected,
        "applied_node_ids": apply_result.get("applied_node_ids", []),
        "applied_edge_ids": apply_result.get("applied_edge_ids", []),
        "already_applied_count": apply_result.get("already_applied_candidate_count", 0),
        "graph_hash_before": apply_result.get("graph_hash_before"),
        "graph_hash_after": apply_result.get("graph_hash_after"),
        "graph_path": APPLIED_PERSONAL_MAP_GRAPH.as_posix(),
        "writes": apply_result.get("writes", []),
        "evidence_record": {"evidence_written": True, "evidence_paths": evidence_paths},
        "audit_record": {"audit_written": True, "audit_record_path": audit_path},
        "personal_map_apply_performed": True,
        "runtime_memory_mutation_performed": False,
        "agent_bus_task_written": False,
        "provider_call_performed": False,
        "credential_read_performed": False,
        "blocked_reasons": [],
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }


def format_personal_context_import_personal_map_approved_apply(
    payload: dict[str, Any],
) -> str:
    lines = [
        "Personal Context Import Personal Map Approved Apply Executor",
        f"Status: {payload.get('status')}",
        f"Approval id: {payload.get('approval_id') or 'none'}",
        f"Execution id: {payload.get('execution_id') or 'none'}",
        f"Readiness digest: {(payload.get('readiness_digest') or 'missing')[:24]}...",
        f"Applied nodes: {len(payload.get('applied_node_ids') or [])}",
        f"Applied edges: {len(payload.get('applied_edge_ids') or [])}",
        f"Graph path: {payload.get('graph_path')}",
        f"Personal Map apply performed: {payload.get('personal_map_apply_performed')}",
        f"Runtime memory mutation performed: {payload.get('runtime_memory_mutation_performed')}",
        f"Agent Bus task written: {payload.get('agent_bus_task_written')}",
        f"Provider call performed: {payload.get('provider_call_performed')}",
        f"Next recommended pass: {payload.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers[:12])
    return "\n".join(lines)
