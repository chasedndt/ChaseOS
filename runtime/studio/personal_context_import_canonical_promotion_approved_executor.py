"""Approved canonical-promotion executor for Personal Context Import.

This governed executor consumes one digest-bound canonical-promotion approval
request and appends managed route blocks to the declared canonical hubs/indexes.
It is intentionally narrow: no Personal Map apply, runtime memory mutation,
Agent Bus dispatch, provider call, credential read, or raw full-memory injection
is granted here.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.personal_context_import_canonical_promotion_approval_preview import (
    APPROVAL_CLASS,
    MODEL_VERSION as PREVIEW_MODEL_VERSION,
    PASS_ID as PREVIEW_PASS_ID,
    SURFACE_ID as PREVIEW_SURFACE_ID,
    _canonical_json,
    _sha256_text,
)
from runtime.studio.service import ApprovalRequest, StudioService


MODEL_VERSION = "studio.personal_context_import_canonical_promotion_approved_executor.v1"
SURFACE_ID = "studio_personal_context_import_canonical_promotion_approved_executor"
PASS_ID = "personal-context-import-canonical-promotion-approved-executor"
STATUS = "COMPLETE / APPROVAL-CONSUMED / CANONICAL ROUTES WRITTEN / VERIFIED"
BLOCKED_STATUS = "BLOCKED / CANONICAL PROMOTION / NO CANONICAL WRITES"
FAILED_STATUS = "FAILED / CANONICAL PROMOTION / PARTIAL CHECK REQUIRED"
NEXT_RECOMMENDED_PASS = "personal-context-import-personal-map-apply-readiness"
MARKER_DIR = Path("runtime/studio/approvals/personal-context-import/_canonical_promotion_markers")
EVIDENCE_ROOT = Path("runtime/studio/context-import/canonical-promotion-executions")
AUDIT_DIR = Path("07_LOGS") / "Agent-Activity"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_id(value: str | None) -> str:
    return "".join(c if c.isalnum() or c in {"-", "_"} else "_" for c in str(value or "")) or "unknown"


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_approval(service: StudioService, req: ApprovalRequest) -> None:
    service._write_approval_record(req)  # type: ignore[attr-defined]  # governed executor uses Studio persistence.


def _load_content_payload(req: ApprovalRequest | None) -> tuple[dict[str, Any] | None, dict[str, Any] | None, str | None]:
    if req is None:
        return None, None, "approval_not_found"
    try:
        content = json.loads(str(req.action_spec.content or "{}"))
    except json.JSONDecodeError as exc:
        return None, None, f"approval_content_json_malformed:{exc}"
    if not isinstance(content, dict):
        return None, None, "approval_content_json_not_object"
    packet = content.get("canonical_promotion_packet")
    if not isinstance(packet, dict):
        return content, None, "approval_content_missing_canonical_promotion_packet"
    return content, packet, None


def _resolve_target(vault: Path, rel_path: str) -> tuple[Path | None, list[str]]:
    blockers: list[str] = []
    normalized = str(rel_path or "").replace("\\", "/").strip()
    if not normalized:
        return None, ["canonical_target_path_required"]
    if Path(normalized).is_absolute():
        blockers.append("canonical_target_path_must_be_vault_relative")
    target = (vault / normalized).resolve()
    try:
        target.relative_to(vault.resolve())
    except ValueError:
        blockers.append("canonical_target_path_escapes_vault")
    if not normalized.endswith(".md"):
        blockers.append(f"canonical_target_not_markdown:{normalized}")
    return target, blockers


def _target_records(vault: Path, packet: dict[str, Any] | None) -> tuple[list[dict[str, Any]], dict[str, Path], list[str]]:
    blockers: list[str] = []
    target_records: list[dict[str, Any]] = []
    target_paths: dict[str, Path] = {}
    for item in (packet or {}).get("canonical_target_plan") or []:
        if not isinstance(item, dict):
            blockers.append("canonical_target_plan_item_not_object")
            continue
        target_id = str(item.get("target_id") or "").strip()
        rel_path = str(item.get("path") or "").replace("\\", "/").strip()
        if not target_id:
            blockers.append("canonical_target_id_required")
            continue
        target, path_blockers = _resolve_target(vault, rel_path)
        blockers.extend(path_blockers)
        target_records.append(dict(item))
        if target is not None:
            target_paths[target_id] = target
    if not target_records:
        blockers.append("canonical_target_plan_empty")
    return target_records, target_paths, blockers


def _content_blockers(
    *,
    req: ApprovalRequest | None,
    content: dict[str, Any] | None,
    packet: dict[str, Any] | None,
    expected_canonical_promotion_digest: str,
) -> list[str]:
    blockers: list[str] = []
    if req is None:
        return ["approval_not_found"]
    metadata = req.action_spec.metadata or {}
    content = content or {}
    packet = packet or {}
    packet_digest = str(packet.get("canonical_promotion_digest") or "")
    metadata_digest = str(metadata.get("personal_context_import_canonical_promotion_digest") or "")

    if req.status not in {"pending", "approved"}:
        blockers.append(f"approval_status_not_pending_or_approved:{req.status}")
    if req.action_spec.action_type != "create_file":
        blockers.append("approval_action_type_not_canonical_promotion_create_file")
    if metadata.get("personal_context_import_canonical_promotion_approval_preview") is not True:
        blockers.append("approval_not_canonical_promotion_approval_preview")
    if metadata.get("personal_context_import_canonical_promotion_execution_blocked") is not True:
        blockers.append("approval_missing_canonical_promotion_execution_block")
    if metadata.get("source_surface") != PREVIEW_SURFACE_ID:
        blockers.append("approval_source_surface_not_canonical_promotion_preview")
    if metadata.get("required_approval_class") != APPROVAL_CLASS:
        blockers.append("approval_class_mismatch")
    if content.get("record_type") != "personal_context_import_canonical_promotion_preview_packet":
        blockers.append("approval_content_record_type_mismatch")
    if content.get("schema_version") != PREVIEW_MODEL_VERSION:
        blockers.append("approval_content_schema_mismatch")
    if content.get("source_text_included") is not False:
        blockers.append("approval_content_source_text_included")
    if content.get("raw_full_memory_injection_allowed") is not False:
        blockers.append("approval_content_raw_full_memory_injection_allowed")
    if content.get("future_executor_requires_matching_digest") is not True:
        blockers.append("approval_content_missing_matching_digest_requirement")
    if packet.get("source_text_included") is not False:
        blockers.append("canonical_promotion_packet_source_text_included")
    if packet.get("raw_full_memory_injection_allowed") is not False:
        blockers.append("canonical_promotion_packet_raw_full_memory_injection_allowed")
    if not packet.get("runtime_reference_packet_ready"):
        blockers.append("runtime_reference_packet_not_ready")
    if not expected_canonical_promotion_digest:
        blockers.append("expected_canonical_promotion_digest_required")
    elif packet_digest and packet_digest != expected_canonical_promotion_digest:
        blockers.append("expected_canonical_promotion_digest_mismatch")
    if metadata_digest and packet_digest and metadata_digest != packet_digest:
        blockers.append("approval_metadata_packet_digest_mismatch")
    if metadata_digest and expected_canonical_promotion_digest and metadata_digest != expected_canonical_promotion_digest:
        blockers.append("approval_metadata_expected_digest_mismatch")
    if not packet_digest:
        blockers.append("canonical_promotion_digest_missing")

    for key, expected in {
        "source_text_included": False,
        "raw_full_memory_injection_allowed": False,
        "canonical_writes_performed": False,
        "personal_map_apply_performed": False,
        "runtime_memory_mutation_performed": False,
        "agent_bus_task_written": False,
        "provider_call_performed": False,
        "credential_read_performed": False,
    }.items():
        if key in packet and bool(packet.get(key)) is not expected:
            blockers.append(f"canonical_promotion_packet_effect_flag_not_false:{key}")
        if key in metadata and bool(metadata.get(key)) is not expected:
            blockers.append(f"approval_metadata_effect_flag_not_false:{key}")
    return blockers


def _statement_blockers(
    *,
    statement: str,
    expected_canonical_promotion_digest: str,
    protected_targets: list[str],
    include_protected_targets: bool,
) -> list[str]:
    if not statement.strip():
        return ["operator_approval_statement_required"]
    blockers: list[str] = []
    lowered = statement.lower()
    if expected_canonical_promotion_digest and expected_canonical_promotion_digest not in statement:
        blockers.append("operator_approval_statement_digest_missing")
    if "approve" not in lowered or "personal context" not in lowered or "canonical promotion" not in lowered:
        blockers.append("operator_approval_statement_phrase_missing")
    if protected_targets:
        if not include_protected_targets:
            blockers.append("protected_targets_require_explicit_flag")
        if "protected" not in lowered:
            blockers.append("operator_approval_statement_protected_targets_missing")
        for target in protected_targets:
            if target not in statement:
                blockers.append(f"operator_approval_statement_protected_target_path_missing:{target}")
    return blockers


def _managed_block(packet: dict[str, Any], target: dict[str, Any], *, approval_id: str, execution_id: str, executor_digest: str) -> str:
    digest = str(packet.get("canonical_promotion_digest") or "")
    runtime_digest = str(packet.get("runtime_reference_packet_digest") or "")
    refs = target.get("reference_group_ids") or []
    groups = ", ".join(str(item) for item in refs) or "none"
    label = str(target.get("target_id") or "canonical-target").replace("_", " ").title()
    start = f"<!-- CHASEOS:PERSONAL-CONTEXT-CANONICAL-PROMOTION:{digest}:START -->"
    end = f"<!-- CHASEOS:PERSONAL-CONTEXT-CANONICAL-PROMOTION:{digest}:END -->"
    return f"""{start}

## Personal Context Import Canonical Routes

- Status: APPROVED CANONICAL PROMOTION / ROUTE BLOCK ACTIVE
- Target: {label}
- Approval id: `{approval_id}`
- Execution id: `{execution_id}`
- Canonical promotion digest: `{digest}`
- Runtime reference packet digest: `{runtime_digest}`
- Executor digest: `{executor_digest}`
- Source text included: `false`
- Raw full-memory injection allowed: `false`
- Reference groups: `{groups}`
- Runtime refs available: `{target.get("runtime_refs_available_for_target") or 0}`
- Personal Map apply performed: `false`
- Runtime memory mutation performed: `false`
- Agent Bus dispatch performed: `false`
- Provider call performed: `false`
- Credential read performed: `false`

Routes:
- [[00_HOME/Personal-Operator-Index|Personal Operator Index]]
- [[03_INPUTS/Personal-Context-Intake/Personal-Context-Intake-Index|Personal Context Intake Index]]
- [[00_HOME/Personal-Domains/Personal-Domains-Index|Personal Domains Index]]
- [[02_KNOWLEDGE/Knowledge-Index|Canonical Knowledge Index]]
- [[01_PROJECTS/Projects-Hub|Projects Hub]]
- [[06_AGENTS/Personal-Context-Import-Feature|Personal Context Import Feature]]

Boundary: this block promotes reviewed routing context only. It does not apply
Personal Map candidates, mutate runtime memory, dispatch Agent Bus tasks, call
providers, or read credentials.

{end}
"""


def _append_managed_block(path: Path, block: str) -> tuple[str, int, int, bool]:
    before = path.read_text(encoding="utf-8") if path.exists() else ""
    created = not path.exists()
    after = before.rstrip() + "\n\n" + block.strip() + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(after, encoding="utf-8")
    return before, len(before.encode("utf-8")), len(after.encode("utf-8")), created


def _summary(
    *,
    approval_id: str,
    approval_status: str | None = None,
    operator_approval_recorded: bool = False,
    approval_consumed: bool = False,
    exact_once_marker_written: bool = False,
    canonical_target_count: int = 0,
    canonical_write_count: int = 0,
    protected_target_count: int = 0,
    duplicate_blocked_before_canonical_write: bool = False,
    blocker_count: int = 0,
) -> dict[str, Any]:
    return {
        "approval_id": approval_id or None,
        "approval_status": approval_status,
        "operator_approval_recorded_from_statement": operator_approval_recorded,
        "approval_consumed": approval_consumed,
        "approval_status_mutated": approval_consumed,
        "exact_once_marker_written": exact_once_marker_written,
        "canonical_target_count": canonical_target_count,
        "canonical_write_count": canonical_write_count,
        "protected_target_count": protected_target_count,
        "canonical_routes_written": canonical_write_count > 0 and approval_consumed,
        "canonical_writes_performed": canonical_write_count > 0 and approval_consumed,
        "duplicate_blocked_before_canonical_write": duplicate_blocked_before_canonical_write,
        "personal_map_apply_performed": False,
        "runtime_memory_mutation_performed": False,
        "agent_bus_task_written": False,
        "runtime_dispatch_performed": False,
        "provider_call_performed": False,
        "credential_read_performed": False,
        "raw_full_memory_injection_performed": False,
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        "blocker_count": blocker_count,
    }


def _authority(canonical_written: bool) -> dict[str, bool]:
    return {
        "approval_consumption_allowed": True,
        "approval_status_mutation_allowed": True,
        "exact_once_marker_write_allowed": True,
        "canonical_route_block_write_allowed": True,
        "canonical_route_block_write_performed": bool(canonical_written),
        "dashboard_write_allowed": True,
        "personal_operator_index_write_allowed": True,
        "operating_system_write_allowed_with_explicit_protected_approval": True,
        "projects_hub_write_allowed": True,
        "knowledge_index_write_allowed": True,
        "personal_domains_index_write_allowed": True,
        "personal_context_intake_index_write_allowed": True,
        "personal_map_apply_allowed": False,
        "runtime_memory_mutation_allowed": False,
        "agent_bus_task_write_allowed": False,
        "runtime_dispatch_allowed": False,
        "provider_calls_allowed": False,
        "credential_reads_allowed": False,
        "raw_full_memory_injection_allowed": False,
    }


def _blocked_payload(
    *,
    vault: Path,
    approval_id: str,
    expected_canonical_promotion_digest: str,
    packet: dict[str, Any] | None,
    target_paths: dict[str, Path],
    marker_path: Path,
    blockers: list[str],
) -> dict[str, Any]:
    unique = list(dict.fromkeys(blockers))
    duplicate = any(item in unique for item in ("exact_once_marker_already_present", "canonical_route_block_already_present"))
    targets = (packet or {}).get("canonical_target_plan") or []
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": BLOCKED_STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": False,
        "approval_gated": True,
        "summary": _summary(
            approval_id=approval_id,
            canonical_target_count=len(targets),
            protected_target_count=sum(1 for item in targets if isinstance(item, dict) and item.get("protected")),
            duplicate_blocked_before_canonical_write=duplicate,
            blocker_count=len(unique),
        ),
        "digest_proof": {
            "expected_canonical_promotion_digest": expected_canonical_promotion_digest or None,
            "canonical_promotion_digest": (packet or {}).get("canonical_promotion_digest"),
            "canonical_promotion_digest_matched": False,
            "executor_digest": None,
        },
        "exact_once_marker": {
            "marker_path": _rel(vault, marker_path),
            "marker_written": False,
            "duplicate_blocked_before_canonical_write": duplicate,
        },
        "canonical_writes": {
            "target_paths": {key: _rel(vault, value) for key, value in sorted(target_paths.items())},
            "written_paths": [],
            "canonical_write_count": 0,
            "canonical_writes_performed": False,
        },
        "execution_record": {
            "execution_id": None,
            "execution_status": None,
        },
        "audit_record": {
            "audit_written": False,
            "audit_record_path": None,
        },
        "authority": _authority(False),
        "blocked_reasons": unique,
    }


def _marker_payload(
    *,
    status: str,
    approval_id: str,
    execution_id: str,
    canonical_promotion_digest: str,
    executor_digest: str,
    operator_id: str,
    written_paths: list[str],
    error: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": "personal_context_import_canonical_promotion_marker.v1",
        "status": status,
        "approval_id": approval_id,
        "execution_id": execution_id,
        "pass": PASS_ID,
        "surface": SURFACE_ID,
        "canonical_promotion_digest": canonical_promotion_digest,
        "executor_digest": executor_digest,
        "operator_id": operator_id,
        "written_paths": written_paths,
        "canonical_writes_performed": bool(written_paths) and status == "executed",
        "personal_map_apply_performed": False,
        "runtime_memory_mutation_performed": False,
        "agent_bus_task_written": False,
        "provider_call_performed": False,
        "credential_read_performed": False,
        "error": error,
        "updated_at_utc": _now_utc(),
    }


def _write_evidence(
    *,
    vault: Path,
    approval_id: str,
    execution_id: str,
    executor_digest: str,
    packet: dict[str, Any],
    target_snapshots: list[dict[str, Any]],
    written_paths: list[str],
    operator_id: str,
) -> dict[str, str]:
    root = vault / EVIDENCE_ROOT / _safe_id(approval_id)
    root.mkdir(parents=True, exist_ok=True)
    evidence_path = root / "execution-evidence.json"
    rollback_path = root / "rollback-plan.json"
    target_manifest_path = root / "target-manifest.json"
    evidence = {
        "schema_version": "personal_context_import_canonical_promotion_execution_evidence.v1",
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "approval_id": approval_id,
        "execution_id": execution_id,
        "executor_digest": executor_digest,
        "canonical_promotion_digest": packet.get("canonical_promotion_digest"),
        "runtime_reference_packet_digest": packet.get("runtime_reference_packet_digest"),
        "canonical_target_count": packet.get("canonical_target_count"),
        "protected_target_count": packet.get("protected_target_count"),
        "written_paths": written_paths,
        "operator_id": operator_id,
        "source_text_included": False,
        "raw_full_memory_injection_performed": False,
        "personal_map_apply_performed": False,
        "runtime_memory_mutation_performed": False,
        "agent_bus_task_written": False,
        "provider_call_performed": False,
        "credential_read_performed": False,
        "generated_at_utc": _now_utc(),
    }
    rollback = {
        "schema_version": "personal_context_import_canonical_promotion_rollback_plan.v1",
        "surface": SURFACE_ID,
        "approval_id": approval_id,
        "execution_id": execution_id,
        "rollback_scope": "managed_canonical_route_blocks_only",
        "manual_review_required_before_rollback": True,
        "target_snapshots": target_snapshots,
        "personal_map_apply_to_revert": [],
        "runtime_memory_to_revert": [],
        "agent_bus_tasks_to_revert": [],
        "provider_calls_to_revert": [],
        "created_at_utc": _now_utc(),
    }
    target_manifest = {
        "schema_version": "personal_context_import_canonical_promotion_target_manifest.v1",
        "surface": SURFACE_ID,
        "approval_id": approval_id,
        "execution_id": execution_id,
        "targets": target_snapshots,
        "written_paths": written_paths,
    }
    _write_json(evidence_path, evidence)
    _write_json(rollback_path, rollback)
    _write_json(target_manifest_path, target_manifest)
    return {
        "execution_evidence": _rel(vault, evidence_path),
        "rollback_plan": _rel(vault, rollback_path),
        "target_manifest": _rel(vault, target_manifest_path),
    }


def _write_audit(
    *,
    vault: Path,
    approval_id: str,
    execution_id: str,
    executor_digest: str,
    canonical_promotion_digest: str,
    written_paths: list[str],
    operator_id: str,
) -> str:
    safe = _safe_id(approval_id)
    path = vault / AUDIT_DIR / f"{_now_utc()[:10]}-personal-context-canonical-promotion-{safe}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    writes = "\n".join(f"- `{item}`" for item in written_paths) or "- none"
    path.write_text(
        f"""# Personal Context Canonical Promotion Execution

- Runtime: Codex / Studio governed executor
- Surface: `{SURFACE_ID}`
- Approval id: `{approval_id}`
- Execution id: `{execution_id}`
- Canonical promotion digest: `{canonical_promotion_digest}`
- Executor digest: `{executor_digest}`
- Operator id: `{operator_id}`

## Writes

{writes}

## Boundary

This pass wrote managed canonical route blocks only. It did not apply Personal
Map candidates, mutate runtime memory, dispatch Agent Bus tasks, call providers,
read credentials, or inject raw full-memory context.
""",
        encoding="utf-8",
    )
    return _rel(vault, path)


def execute_personal_context_import_canonical_promotion_approved_executor(
    vault_root: str | Path,
    *,
    approval_id: str,
    expected_canonical_promotion_digest: str,
    operator_approval_statement: str = "",
    operator_id: str = "studio-operator",
    include_protected_targets: bool = False,
    execute: bool = False,
) -> dict[str, Any]:
    """Consume an approved canonical-promotion request and write route blocks once."""

    vault = Path(vault_root).resolve()
    requested_approval_id = str(approval_id or "").strip()
    expected = str(expected_canonical_promotion_digest or "").strip()
    statement = str(operator_approval_statement or "")
    operator = str(operator_id or "studio-operator")
    marker_path = (vault / MARKER_DIR / f"{_safe_id(requested_approval_id)}.json").resolve()

    blockers: list[str] = []
    if not requested_approval_id:
        blockers.append("approval_id_required")
    if not expected:
        blockers.append("expected_canonical_promotion_digest_required")
    if not execute:
        blockers.append("execute_flag_required")

    service = StudioService(vault)
    req = service.get_approval(requested_approval_id) if requested_approval_id else None
    content, packet, content_error = _load_content_payload(req)
    if content_error:
        blockers.append(content_error)

    target_records, target_paths, target_blockers = _target_records(vault, packet)
    blockers.extend(target_blockers)
    protected_targets = [
        str(item.get("path") or "")
        for item in target_records
        if item.get("protected") is True
    ]
    blockers.extend(
        _content_blockers(
            req=req,
            content=content,
            packet=packet,
            expected_canonical_promotion_digest=expected,
        )
    )
    blockers.extend(
        _statement_blockers(
            statement=statement,
            expected_canonical_promotion_digest=expected,
            protected_targets=protected_targets,
            include_protected_targets=include_protected_targets,
        )
    )

    if marker_path.exists():
        blockers.append("exact_once_marker_already_present")
    digest = str((packet or {}).get("canonical_promotion_digest") or expected)
    for target_id, target_path in target_paths.items():
        if target_path.exists():
            text = target_path.read_text(encoding="utf-8")
            if f"CHASEOS:PERSONAL-CONTEXT-CANONICAL-PROMOTION:{digest}:START" in text:
                blockers.append(f"canonical_route_block_already_present:{target_id}")

    hard_blockers = list(dict.fromkeys(blockers))
    if hard_blockers:
        return _blocked_payload(
            vault=vault,
            approval_id=requested_approval_id,
            expected_canonical_promotion_digest=expected,
            packet=packet,
            target_paths=target_paths,
            marker_path=marker_path,
            blockers=hard_blockers,
        )

    assert req is not None
    assert packet is not None
    assert content is not None

    approved_content = str(req.action_spec.content or "")
    executor_material = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "approval_id": requested_approval_id,
        "canonical_promotion_digest": expected,
        "approval_content_sha256": hashlib.sha256(approved_content.encode("utf-8")).hexdigest(),
        "include_protected_targets": bool(include_protected_targets),
        "target_paths": {key: _rel(vault, value) for key, value in sorted(target_paths.items())},
    }
    executor_digest = _sha256_text(_canonical_json(executor_material))
    execution_id = f"personal-context-canonical-promotion-{executor_digest[:20]}"
    written_paths: list[str] = []
    target_snapshots: list[dict[str, Any]] = []
    approval_recorded_from_statement = False

    try:
        if req.status == "pending":
            req.status = "approved"
            req.reviewed_by = operator
            req.reason = statement
            req.updated_at = _now_utc()
            _write_approval(service, req)
            approval_recorded_from_statement = True

        req.status = "executing"
        req.execution_id = execution_id
        req.execution_started_at = _now_utc()
        req.execution_finished_at = None
        req.execution_status = None
        req.result_action_id = None
        req.execution_error = ""
        req.updated_at = req.execution_started_at
        _write_approval(service, req)

        _write_json(
            marker_path,
            _marker_payload(
                status="executing",
                approval_id=requested_approval_id,
                execution_id=execution_id,
                canonical_promotion_digest=expected,
                executor_digest=executor_digest,
                operator_id=operator,
                written_paths=[],
            ),
        )

        targets_by_id = {str(item.get("target_id") or ""): item for item in target_records}
        for target_id, target_path in sorted(target_paths.items()):
            target = targets_by_id.get(target_id) or {}
            block = _managed_block(
                packet,
                target,
                approval_id=requested_approval_id,
                execution_id=execution_id,
                executor_digest=executor_digest,
            )
            before, before_bytes, after_bytes, created = _append_managed_block(target_path, block)
            rel_path = _rel(vault, target_path)
            written_paths.append(rel_path)
            target_snapshots.append(
                {
                    "target_id": target_id,
                    "path": rel_path,
                    "protected": bool(target.get("protected")),
                    "created": created,
                    "before_sha256": hashlib.sha256(before.encode("utf-8")).hexdigest(),
                    "before_bytes": before_bytes,
                    "after_bytes": after_bytes,
                    "managed_block_sha256": hashlib.sha256(block.encode("utf-8")).hexdigest(),
                }
            )

        evidence_paths = _write_evidence(
            vault=vault,
            approval_id=requested_approval_id,
            execution_id=execution_id,
            executor_digest=executor_digest,
            packet=packet,
            target_snapshots=target_snapshots,
            written_paths=written_paths,
            operator_id=operator,
        )

        _write_json(
            marker_path,
            _marker_payload(
                status="executed",
                approval_id=requested_approval_id,
                execution_id=execution_id,
                canonical_promotion_digest=expected,
                executor_digest=executor_digest,
                operator_id=operator,
                written_paths=written_paths,
            ),
        )

        req.status = "executed"
        req.execution_finished_at = _now_utc()
        req.execution_status = "completed"
        req.result_action_id = execution_id
        req.execution_error = ""
        req.updated_at = req.execution_finished_at
        metadata = dict(req.action_spec.metadata or {})
        metadata.update(
            {
                "personal_context_import_canonical_promotion_approved_executor": True,
                "personal_context_import_canonical_promotion_executor_digest": executor_digest,
                "approval_consumed": True,
                "canonical_promotion_digest_matched": True,
                "canonical_writes_performed": True,
                "canonical_write_count": len(written_paths),
                "personal_map_apply_performed": False,
                "runtime_memory_mutation_performed": False,
                "agent_bus_task_written": False,
                "provider_call_performed": False,
                "credential_read_performed": False,
                "next_required_pass": NEXT_RECOMMENDED_PASS,
            }
        )
        req.action_spec.metadata = metadata
        _write_approval(service, req)

        audit_path = _write_audit(
            vault=vault,
            approval_id=requested_approval_id,
            execution_id=execution_id,
            executor_digest=executor_digest,
            canonical_promotion_digest=expected,
            written_paths=written_paths,
            operator_id=operator,
        )
    except Exception as exc:
        error = str(exc)
        try:
            _write_json(
                marker_path,
                _marker_payload(
                    status="execution_failed",
                    approval_id=requested_approval_id,
                    execution_id=execution_id,
                    canonical_promotion_digest=expected,
                    executor_digest=executor_digest,
                    operator_id=operator,
                    written_paths=written_paths,
                    error=error,
                ),
            )
            req.status = "execution_failed"
            req.execution_finished_at = _now_utc()
            req.execution_status = "error"
            req.result_action_id = execution_id
            req.execution_error = error
            req.updated_at = req.execution_finished_at
            _write_approval(service, req)
        except Exception:
            pass
        failed = _blocked_payload(
            vault=vault,
            approval_id=requested_approval_id,
            expected_canonical_promotion_digest=expected,
            packet=packet,
            target_paths=target_paths,
            marker_path=marker_path,
            blockers=[f"personal_context_canonical_promotion_execution_failed:{error}"],
        )
        failed["status"] = FAILED_STATUS
        return failed

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": False,
        "approval_gated": True,
        "summary": _summary(
            approval_id=requested_approval_id,
            approval_status="executed",
            operator_approval_recorded=approval_recorded_from_statement,
            approval_consumed=True,
            exact_once_marker_written=True,
            canonical_target_count=len(target_records),
            canonical_write_count=len(written_paths),
            protected_target_count=len(protected_targets),
            blocker_count=0,
        ),
        "digest_proof": {
            "expected_canonical_promotion_digest": expected,
            "canonical_promotion_digest": packet.get("canonical_promotion_digest"),
            "canonical_promotion_digest_matched": expected == packet.get("canonical_promotion_digest"),
            "approval_content_sha256": hashlib.sha256(approved_content.encode("utf-8")).hexdigest(),
            "executor_digest": executor_digest,
            "executor_digest_material": executor_material,
            "result_digest": _sha256_text(
                _canonical_json(
                    {
                        "approval_id": requested_approval_id,
                        "execution_id": execution_id,
                        "executor_digest": executor_digest,
                        "written_paths": written_paths,
                    }
                )
            ),
        },
        "exact_once_marker": {
            "marker_path": _rel(vault, marker_path),
            "marker_written": True,
            "marker_status": "executed",
            "duplicate_blocked_before_canonical_write": True,
        },
        "canonical_writes": {
            "target_paths": {key: _rel(vault, value) for key, value in sorted(target_paths.items())},
            "target_snapshots": target_snapshots,
            "written_paths": written_paths,
            "canonical_write_count": len(written_paths),
            "canonical_writes_performed": True,
            "managed_block_marker": f"CHASEOS:PERSONAL-CONTEXT-CANONICAL-PROMOTION:{expected}",
        },
        "execution_record": {
            "execution_id": execution_id,
            "execution_status": "completed",
            "approval_status": "executed",
        },
        "evidence_record": {
            "evidence_written": True,
            "evidence_paths": evidence_paths,
        },
        "audit_record": {
            "audit_written": True,
            "audit_record_path": audit_path,
        },
        "authority": _authority(True),
        "blocked_reasons": [],
    }


def format_personal_context_import_canonical_promotion_approved_executor(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    digest = payload.get("digest_proof") or {}
    writes = payload.get("canonical_writes") or {}
    marker = payload.get("exact_once_marker") or {}
    lines = [
        "Personal Context Import Canonical Promotion Approved Executor",
        f"Status: {payload.get('status')}",
        f"Approval id: {summary.get('approval_id') or 'none'}",
        f"Approval consumed: {summary.get('approval_consumed')}",
        f"Canonical promotion digest: {digest.get('canonical_promotion_digest') or 'missing'}",
        f"Digest matched: {digest.get('canonical_promotion_digest_matched')}",
        f"Executor digest: {digest.get('executor_digest') or 'missing'}",
        f"Marker written: {marker.get('marker_written')}",
        f"Canonical write count: {writes.get('canonical_write_count') or 0}",
        f"Personal Map apply performed: {summary.get('personal_map_apply_performed')}",
        f"Runtime memory mutation performed: {summary.get('runtime_memory_mutation_performed')}",
        f"Agent Bus task written: {summary.get('agent_bus_task_written')}",
        f"Provider call performed: {summary.get('provider_call_performed')}",
        f"Credential read performed: {summary.get('credential_read_performed')}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers[:12])
    return "\n".join(lines)
