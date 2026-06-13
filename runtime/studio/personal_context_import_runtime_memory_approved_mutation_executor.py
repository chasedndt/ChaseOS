"""Approved runtime memory mutation executor for Personal Context Import.

Consumes one digest-bound runtime memory mutation approval and appends personal
context route hints to each registered runtime's nav map JSON. Writes an
exact-once marker, execution evidence, and audit record.

Does NOT write canonical vault files, Personal Map apply, Agent Bus tasks,
provider calls, or read credentials.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.personal_context_import_runtime_memory_mutation_readiness import (
    APPROVAL_CLASS,
    MODEL_VERSION as READINESS_MODEL_VERSION,
    SURFACE_ID as READINESS_SURFACE_ID,
    _PERSONAL_CONTEXT_ROUTE_HINTS,
    _RUNTIME_IDS,
    _compute_mutation_digest,
    _runtime_nav_map_path,
    _runtime_state,
    build_personal_context_import_runtime_memory_mutation_readiness,
)
from runtime.studio.service import StudioService


MODEL_VERSION = "studio.personal_context_import_runtime_memory_approved_mutation_executor.v1"
SURFACE_ID = "studio_personal_context_import_runtime_memory_approved_mutation_executor"
PASS_ID = "personal-context-import-runtime-memory-approved-mutation-executor"
STATUS_OK = "COMPLETE / RUNTIME NAV MAPS UPDATED / PERSONAL CONTEXT ROUTES WRITTEN"
STATUS_BLOCKED = "BLOCKED / RUNTIME MEMORY MUTATION / NO NAV MAP WRITE"
STATUS_FAILED = "FAILED / RUNTIME MEMORY MUTATION / PARTIAL CHECK REQUIRED"
NEXT_RECOMMENDED_PASS = "personal-context-import-agent-bus-dispatch-packet"
MARKER_DIR = Path(
    "runtime/studio/approvals/personal-context-import/_runtime_memory_mutation_markers"
)
EVIDENCE_ROOT = Path("runtime/studio/context-import/runtime-memory-mutation-executions")
AUDIT_DIR = Path("07_LOGS") / "Agent-Activity"
PERSONAL_CONTEXT_ROUTE_KEY = "personal_context_routes"


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


def _load_json_or_empty(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _append_personal_context_routes(
    nav_data: dict[str, Any],
    *,
    approval_id: str,
    execution_id: str,
    applied_at: str,
) -> dict[str, Any]:
    """Append personal context route hints to nav-map JSON."""
    updated = dict(nav_data)
    existing_routes = list(updated.get(PERSONAL_CONTEXT_ROUTE_KEY) or [])
    existing_route_ids = {r.get("route_id") for r in existing_routes if isinstance(r, dict)}
    new_routes = [
        dict(hint)
        for hint in _PERSONAL_CONTEXT_ROUTE_HINTS
        if hint["route_id"] not in existing_route_ids
    ]
    if new_routes:
        for route in new_routes:
            route["added_at"] = applied_at
            route["approval_id"] = approval_id
            route["execution_id"] = execution_id
        existing_routes.extend(new_routes)
    updated[PERSONAL_CONTEXT_ROUTE_KEY] = existing_routes
    updated["personal_context_import_annotated_at"] = applied_at
    updated["personal_context_import_approval_id"] = approval_id
    return updated


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
    if meta.get("runtime_memory_mutation_readiness_approval") is not True:
        blockers.append("approval_not_runtime_memory_mutation_readiness")
    if meta.get("required_approval_class") != APPROVAL_CLASS:
        blockers.append("approval_class_mismatch")
    if content.get("record_type") != "personal_context_import_runtime_memory_mutation_readiness_approval":
        blockers.append("approval_record_type_mismatch")
    if content.get("schema_version") != READINESS_MODEL_VERSION:
        blockers.append("approval_schema_version_mismatch")
    if content.get("canonical_writeback_allowed") is not False:
        blockers.append("approval_canonical_writeback_allowed")
    stored_digest = str(content.get("mutation_digest") or "")
    if not expected_digest:
        blockers.append("expected_mutation_digest_required")
    elif stored_digest and stored_digest != expected_digest:
        blockers.append("mutation_digest_mismatch")
    metadata_digest = str(meta.get("runtime_memory_mutation_digest") or "")
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
    if "approve" not in low or "runtime" not in low:
        blockers.append("operator_approval_statement_phrase_missing")
    return blockers


def _write_audit(
    *,
    vault: Path,
    approval_id: str,
    execution_id: str,
    executor_digest: str,
    mutation_digest: str,
    written_nav_maps: list[str],
    operator_id: str,
) -> str:
    path = vault / AUDIT_DIR / f"{_now_utc()[:10]}-personal-context-runtime-memory-mutation-{approval_id[:12]}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    written = "\n".join(f"- `{item}`" for item in written_nav_maps) or "- none"
    path.write_text(
        f"""# Personal Context Runtime Memory Mutation Execution

- Runtime: Codex / Studio governed executor
- Surface: `{SURFACE_ID}`
- Approval id: `{approval_id}`
- Execution id: `{execution_id}`
- Mutation digest: `{mutation_digest}`
- Executor digest: `{executor_digest}`
- Operator id: `{operator_id}`

## Written Nav Maps

{written}

## Boundary

This pass wrote personal context route hints to runtime nav maps only. It did not
apply Personal Map candidates, mutate canonical vault files, dispatch Agent Bus
tasks, call providers, read credentials, or inject raw context.
""",
        encoding="utf-8",
    )
    return _rel(vault, path)


def execute_personal_context_import_runtime_memory_approved_mutation(
    vault_root: str | Path,
    *,
    approval_id: str,
    expected_mutation_digest: str,
    operator_approval_statement: str = "",
    operator_id: str = "studio-operator",
    execute: bool = False,
) -> dict[str, Any]:
    """Consume approval and write personal context routes to runtime nav maps."""
    vault = Path(vault_root).resolve()
    approval_id_str = str(approval_id or "").strip()
    expected = str(expected_mutation_digest or "").strip()
    statement = str(operator_approval_statement or "")
    operator = str(operator_id or "studio-operator")
    marker_path = (vault / MARKER_DIR / f"{approval_id_str or 'missing'}.json").resolve()

    blockers: list[str] = []
    if not approval_id_str:
        blockers.append("approval_id_required")
    if not expected:
        blockers.append("expected_mutation_digest_required")
    if not execute:
        blockers.append("execute_flag_required")

    service = StudioService(vault)
    req = service.get_approval(approval_id_str) if approval_id_str else None
    content: dict[str, Any] | None = None
    if req is not None:
        try:
            content = json.loads(str(req.action_spec.content or "{}"))
        except Exception as exc:
            blockers.append(f"approval_content_malformed:{exc}")

    if approval_id_str and req is not None:
        blockers.extend(_content_blockers(service, approval_id_str, content, expected))
    elif approval_id_str and req is None:
        blockers.append("approval_not_found")
    blockers.extend(_statement_blockers(statement, expected))

    # Verify current digest
    runtime_states = [_runtime_state(vault, rid) for rid in _RUNTIME_IDS]
    current_digest = _compute_mutation_digest(runtime_states)
    if expected and current_digest != expected:
        blockers.append("current_runtime_state_digest_mismatch")

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
            "runtime_memory_mutation_performed": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        }

    executor_material = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "approval_id": approval_id_str,
        "mutation_digest": expected,
    }
    executor_digest = _sha256_text(_canonical_json(executor_material))
    execution_id = f"runtime-memory-mutation-{executor_digest[:20]}"
    applied_at = _now_utc()

    assert req is not None

    try:
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(
            marker_path,
            {
                "schema_version": "personal_context_import_runtime_memory_mutation_marker.v1",
                "status": "executing",
                "approval_id": approval_id_str,
                "execution_id": execution_id,
                "mutation_digest": expected,
                "executor_digest": executor_digest,
                "operator_id": operator,
                "applied_at_utc": applied_at,
            },
        )

        written_nav_maps: list[str] = []
        runtime_results: list[dict[str, Any]] = []
        for runtime_id in _RUNTIME_IDS:
            nav_path = vault / _runtime_nav_map_path(runtime_id)
            nav_data = _load_json_or_empty(nav_path)
            updated_data = _append_personal_context_routes(
                nav_data,
                approval_id=approval_id_str,
                execution_id=execution_id,
                applied_at=applied_at,
            )
            nav_path.parent.mkdir(parents=True, exist_ok=True)
            nav_path.write_text(
                json.dumps(updated_data, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            rel = _rel(vault, nav_path)
            written_nav_maps.append(rel)
            runtime_results.append(
                {
                    "runtime_id": runtime_id,
                    "nav_map_path": rel,
                    "written": True,
                    "route_count_added": len(
                        [
                            h
                            for h in _PERSONAL_CONTEXT_ROUTE_HINTS
                            if h["route_id"]
                            not in {
                                r.get("route_id")
                                for r in (nav_data.get(PERSONAL_CONTEXT_ROUTE_KEY) or [])
                            }
                        ]
                    ),
                }
            )

        _write_json(
            marker_path,
            {
                "schema_version": "personal_context_import_runtime_memory_mutation_marker.v1",
                "status": "executed",
                "approval_id": approval_id_str,
                "execution_id": execution_id,
                "mutation_digest": expected,
                "executor_digest": executor_digest,
                "operator_id": operator,
                "written_nav_maps": written_nav_maps,
                "applied_at_utc": applied_at,
            },
        )

        evidence_root = vault / EVIDENCE_ROOT / approval_id_str
        evidence_root.mkdir(parents=True, exist_ok=True)
        _write_json(
            evidence_root / "execution-evidence.json",
            {
                "schema_version": "personal_context_import_runtime_memory_mutation_evidence.v1",
                "surface": SURFACE_ID,
                "pass": PASS_ID,
                "approval_id": approval_id_str,
                "execution_id": execution_id,
                "executor_digest": executor_digest,
                "mutation_digest": expected,
                "operator_id": operator,
                "written_nav_maps": written_nav_maps,
                "runtime_results": runtime_results,
                "runtime_memory_mutation_performed": True,
                "personal_map_apply_performed": False,
                "canonical_writeback_allowed": False,
                "agent_bus_task_written": False,
                "provider_call_performed": False,
                "credential_read_performed": False,
                "generated_at_utc": applied_at,
            },
        )

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
        service._write_approval_record(req)  # type: ignore[attr-defined]

        audit_path = _write_audit(
            vault=vault,
            approval_id=approval_id_str,
            execution_id=execution_id,
            executor_digest=executor_digest,
            mutation_digest=expected,
            written_nav_maps=written_nav_maps,
            operator_id=operator,
        )

    except Exception as exc:
        error = str(exc)
        try:
            _write_json(
                marker_path,
                {
                    "schema_version": "personal_context_import_runtime_memory_mutation_marker.v1",
                    "status": "execution_failed",
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
            "blocked_reasons": [f"runtime_memory_mutation_failed:{error}"],
            "runtime_memory_mutation_performed": False,
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
        "mutation_digest": expected,
        "written_nav_maps": written_nav_maps,
        "runtime_results": runtime_results,
        "audit_record_path": audit_path,
        "runtime_memory_mutation_performed": True,
        "personal_map_apply_performed": False,
        "canonical_writeback_allowed": False,
        "agent_bus_task_written": False,
        "provider_call_performed": False,
        "credential_read_performed": False,
        "blocked_reasons": [],
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }


def format_personal_context_import_runtime_memory_approved_mutation(
    payload: dict[str, Any],
) -> str:
    lines = [
        "Personal Context Import Runtime Memory Approved Mutation Executor",
        f"Status: {payload.get('status')}",
        f"Approval id: {payload.get('approval_id') or 'none'}",
        f"Execution id: {payload.get('execution_id') or 'none'}",
        f"Written nav maps: {payload.get('written_nav_maps')}",
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
