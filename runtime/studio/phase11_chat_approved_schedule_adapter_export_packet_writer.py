"""Phase 11 Chat approved schedule adapter export packet writer.

This governed writer consumes one digest-bound Studio Chat schedule adapter
export approval exactly once. It writes the local adapter export JSON packet
prepared by the readiness surface and nothing else.

It does not mutate external scheduler files, OpenClaw/Hermes cron state, Agent
Bus tasks, runtime/workflow dispatch, Discord, providers, credentials, or
canonical vault state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.phase11_chat_schedule_adapter_export_readiness import (
    EXPORT_PACKET_ROOT,
    METADATA_BLOCK_KEY as READINESS_METADATA_BLOCK_KEY,
    SURFACE_ID as READINESS_SURFACE_ID,
    build_phase11_chat_schedule_adapter_export_readiness,
)
from runtime.studio.service import ApprovalRequest, StudioService


MODEL_VERSION = "studio.phase11_chat_approved_schedule_adapter_export_packet_writer.v1"
SURFACE_ID = "phase11_chat_approved_schedule_adapter_export_packet_writer"
PASS_ID = "studio-chat-approved-schedule-adapter-export-packet-writer"
STATUS = "COMPLETE / APPROVED ADAPTER-EXPORT PACKET WRITTEN / CRON MUTATION BLOCKED"
NEXT_RECOMMENDED_PASS = "studio-chat-schedule-ui-action-controls-and-readback"
MARKER_DIR = Path("runtime/studio/approvals/_chat_schedule_adapter_export_packet_markers")
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


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _write_approval(service: StudioService, req: ApprovalRequest) -> None:
    service._write_approval_record(req)  # type: ignore[attr-defined]


def _effect_flags(*, written: bool = False) -> dict[str, bool]:
    return {
        "target_file_written": written,
        "export_packet_written": written,
        "external_scheduler_changed": False,
        "openclaw_cron_changed": False,
        "hermes_cron_changed": False,
        "agent_bus_task_written": False,
        "runtime_dispatched": False,
        "workflow_dispatched": False,
        "discord_api_called": False,
        "provider_call_performed": False,
        "credential_value_read": False,
        "canonical_mutation_performed": False,
    }


def _authority() -> dict[str, bool]:
    return {
        "approval_consumption_allowed": True,
        "approval_status_mutation_allowed": True,
        "exact_once_marker_write_allowed": True,
        "local_export_packet_write_allowed": True,
        "adapter_export_read_model_allowed": True,
        "external_scheduler_mutation_allowed": False,
        "openclaw_cron_mutation_allowed": False,
        "hermes_cron_mutation_allowed": False,
        "agent_bus_task_write_allowed": False,
        "runtime_dispatch_allowed": False,
        "workflow_dispatch_allowed": False,
        "discord_api_calls_allowed": False,
        "provider_calls_allowed": False,
        "credential_values_visible": False,
        "canonical_mutation_allowed": False,
    }


def _target_blockers(vault: Path, target_path: str, adapter: str, export_digest: str) -> tuple[Path | None, list[str]]:
    blockers: list[str] = []
    normalized = str(target_path or "").replace("\\", "/").strip()
    if not normalized:
        blockers.append("approval_target_path_required")
        return None, blockers
    if not export_digest:
        blockers.append("expected_export_digest_required")
    if normalized != f"{EXPORT_PACKET_ROOT}/{adapter}-{export_digest[:20]}.json":
        blockers.append("approval_target_path_digest_mismatch")
    if not normalized.startswith(f"{EXPORT_PACKET_ROOT}/"):
        blockers.append("approval_target_path_not_schedule_adapter_exports")
    if not normalized.endswith(".json"):
        blockers.append("approval_target_path_not_json")
    target_abs = (vault / normalized).resolve()
    export_root = (vault / EXPORT_PACKET_ROOT).resolve()
    try:
        target_abs.relative_to(vault.resolve())
    except ValueError:
        blockers.append("approval_target_path_escapes_vault")
    try:
        target_abs.relative_to(export_root)
    except ValueError:
        blockers.append("approval_target_path_escapes_adapter_export_root")
    if target_abs.exists():
        blockers.append("target_packet_already_exists_before_execution")
    return target_abs, blockers


def _packet_blockers(
    *,
    req: ApprovalRequest,
    packet: dict[str, Any],
    expected_export_digest: str,
    target_path: str,
    current_readiness: dict[str, Any] | None,
) -> list[str]:
    blockers: list[str] = []
    metadata = req.action_spec.metadata or {}
    digest_material = metadata.get("export_digest_material")
    if not isinstance(digest_material, dict):
        digest_material = {}
    if req.action_spec.action_type != "create_file":
        blockers.append("approval_action_type_not_adapter_export_create_file")
    if metadata.get("phase11_chat_schedule_adapter_export_readiness") is not True:
        blockers.append("approval_not_schedule_adapter_export_readiness_artifact")
    if metadata.get(READINESS_METADATA_BLOCK_KEY) is not True:
        blockers.append("approval_missing_adapter_export_execution_block")
    if metadata.get("source_surface") != READINESS_SURFACE_ID:
        blockers.append("approval_source_surface_not_schedule_adapter_export_readiness")
    if not expected_export_digest:
        blockers.append("expected_export_digest_required")
    elif metadata.get("export_digest") != expected_export_digest:
        blockers.append("export_digest_mismatch")
    if packet.get("packet_type") != "phase11_chat_schedule_adapter_export_packet":
        blockers.append("packet_type_mismatch")
    if packet.get("surface") != READINESS_SURFACE_ID:
        blockers.append("packet_source_surface_mismatch")
    if packet.get("export_digest") != expected_export_digest:
        blockers.append("packet_export_digest_mismatch")
    if packet.get("target_path") != target_path:
        blockers.append("packet_target_path_mismatch")
    if packet.get("digest_material") != digest_material:
        blockers.append("packet_digest_material_metadata_mismatch")
    if current_readiness is None or current_readiness.get("ok") is not True:
        blockers.append("current_adapter_export_readiness_unavailable")
    else:
        digest_proof = current_readiness.get("digest_proof") or {}
        current_digest = str(digest_proof.get("export_digest") or "")
        if current_digest != expected_export_digest:
            blockers.append("current_adapter_export_digest_mismatch")
        current_packet = (current_readiness.get("adapter_export_preview") or {}).get("packet_json_preview")
        try:
            current_packet_data = json.loads(str(current_packet or "{}"))
        except json.JSONDecodeError:
            current_packet_data = {}
        if current_packet_data.get("adapter_entries") != packet.get("adapter_entries"):
            blockers.append("current_adapter_export_entries_mismatch")
    for key in (
        "external_scheduler_changed",
        "openclaw_cron_changed",
        "hermes_cron_changed",
        "agent_bus_task_written",
        "runtime_dispatched",
        "workflow_dispatched",
        "discord_api_called",
        "provider_call_performed",
        "credential_value_read",
    ):
        if key in metadata and bool(metadata.get(key)) is not False:
            blockers.append(f"approval_metadata_effect_flag_not_false:{key}")
    return blockers


def _executor_digest_material(
    *,
    approval_id: str,
    export_digest: str,
    target_path: str,
    packet_sha256: str,
) -> dict[str, Any]:
    return {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "approval_id": approval_id,
        "export_digest": export_digest,
        "target_path": target_path,
        "packet_sha256": packet_sha256,
    }


def _summary(
    *,
    approval_id: str,
    export_digest: str,
    target_path: str | None = None,
    runtime_adapter_target: str | None = None,
    entry_count: int = 0,
    approval_status: str | None = None,
    operator_approval_recorded: bool = False,
    approval_consumed: bool = False,
    exact_once_marker_written: bool = False,
    written: bool = False,
    duplicate_blocked_before_target_write: bool = False,
    blocker_count: int = 0,
) -> dict[str, Any]:
    return {
        "approval_id": approval_id or None,
        "approval_status": approval_status,
        "operator_approval_recorded_from_statement": operator_approval_recorded,
        "expected_export_digest_provided": bool(export_digest),
        "export_digest": export_digest or None,
        "runtime_adapter_target": runtime_adapter_target,
        "entry_count": entry_count,
        "target_path": target_path,
        "approval_consumed": approval_consumed,
        "approval_status_mutated": approval_consumed,
        "exact_once_marker_written": exact_once_marker_written,
        "duplicate_blocked_before_target_write": duplicate_blocked_before_target_write,
        **_effect_flags(written=written),
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        "blocker_count": blocker_count,
    }


def _blocked_payload(
    *,
    vault: Path,
    approval_id: str,
    expected_export_digest: str,
    target_path: str,
    runtime_adapter_target: str | None,
    entry_count: int,
    marker_path: Path | None,
    blockers: list[str],
) -> dict[str, Any]:
    unique = list(dict.fromkeys(blockers))
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": "BLOCKED / APPROVED ADAPTER-EXPORT PACKET WRITER / NO TARGET WRITE",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": False,
        "approval_gated": True,
        "summary": _summary(
            approval_id=approval_id,
            export_digest=expected_export_digest,
            target_path=target_path or None,
            runtime_adapter_target=runtime_adapter_target,
            entry_count=entry_count,
            duplicate_blocked_before_target_write=(
                "exact_once_marker_already_present" in unique
                or "target_packet_already_exists_before_execution" in unique
            ),
            blocker_count=len(unique),
        ),
        "digest_proof": {
            "expected_export_digest": expected_export_digest or None,
            "export_digest": None,
            "export_digest_matched": False,
            "executor_digest": None,
        },
        "exact_once_marker": {
            "marker_path": _rel(vault, marker_path) if marker_path else None,
            "marker_written": False,
            "duplicate_blocked_before_target_write": "exact_once_marker_already_present" in unique,
        },
        "target_write": {
            "target_path": target_path or None,
            **_effect_flags(written=False),
        },
        "audit_record": {
            "audit_written": False,
            "audit_record_path": None,
        },
        "authority": _authority(),
        "blocked_reasons": unique,
    }


def _marker_payload(
    *,
    status: str,
    approval_id: str,
    execution_id: str,
    export_digest: str,
    executor_digest: str,
    target_path: str,
    runtime_adapter_target: str,
    operator_id: str,
    written: bool,
    error: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": "phase11_chat_approved_schedule_adapter_export_packet_writer_marker.v1",
        "status": status,
        "approval_id": approval_id,
        "execution_id": execution_id,
        "pass": PASS_ID,
        "surface": SURFACE_ID,
        "export_digest": export_digest,
        "executor_digest": executor_digest,
        "target_path": target_path,
        "runtime_adapter_target": runtime_adapter_target,
        "operator_id": operator_id,
        **_effect_flags(written=written),
        "error": error,
        "updated_at_utc": _now_utc(),
    }


def _next_audit_path(vault: Path, executor_digest: str) -> Path:
    root = vault / AUDIT_DIR
    root.mkdir(parents=True, exist_ok=True)
    base = root / f"{PASS_ID}-{executor_digest[:20]}.md"
    if not base.exists():
        return base
    for index in range(2, 100):
        candidate = root / f"{PASS_ID}-{executor_digest[:20]}-{index}.md"
        if not candidate.exists():
            return candidate
    raise RuntimeError("could not allocate schedule adapter export packet writer audit path")


def _write_audit(
    *,
    vault: Path,
    approval_id: str,
    execution_id: str,
    export_digest: str,
    executor_digest: str,
    target_path: str,
    runtime_adapter_target: str,
    entry_count: int,
    operator_id: str,
) -> str:
    path = _next_audit_path(vault, executor_digest)
    text = "\n".join(
        [
            "---",
            "type: agent-activity",
            "runtime: Codex",
            f"pass_id: {PASS_ID}",
            f"approval_id: {approval_id}",
            f"execution_id: {execution_id}",
            f"status: {STATUS}",
            "---",
            "",
            "# Phase 11 Chat Approved Schedule Adapter Export Packet Writer",
            "",
            f"operator_id: {operator_id}",
            f"approval_id: {approval_id}",
            f"execution_id: {execution_id}",
            f"runtime_adapter_target: {runtime_adapter_target}",
            f"export_digest: {export_digest}",
            f"executor_digest: {executor_digest}",
            f"target_path: {target_path}",
            f"entry_count: {entry_count}",
            "approval_consumed: true",
            "approval_status_mutated: true",
            "exact_once_marker_written: true",
            "target_file_written: true",
            "export_packet_written: true",
            "external_scheduler_changed: false",
            "openclaw_cron_changed: false",
            "hermes_cron_changed: false",
            "agent_bus_task_written: false",
            "runtime_dispatched: false",
            "workflow_dispatched: false",
            "discord_api_called: false",
            "provider_call_performed: false",
            "credential_value_read: false",
            "canonical_mutation_performed: false",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")
    return _rel(vault, path)


def execute_phase11_chat_approved_schedule_adapter_export_packet_writer(
    vault_root: str | Path,
    *,
    approval_id: str | None = None,
    expected_export_digest: str | None = None,
    operator_id: str = "operator",
    operator_export_write_statement: str | None = None,
) -> dict[str, Any]:
    """Consume one approved adapter export packet approval and write the JSON packet."""

    vault = Path(vault_root).resolve()
    requested_approval_id = str(approval_id or "").strip()
    expected = str(expected_export_digest or "").strip()
    operator = str(operator_id or "operator").strip() or "operator"
    statement = " ".join(str(operator_export_write_statement or "").strip().split())
    service = StudioService(vault)
    blockers: list[str] = []
    target_path = ""
    packet: dict[str, Any] = {}
    runtime_adapter_target: str | None = None
    schedule_id: str | None = None
    entry_count = 0
    marker_path = vault / MARKER_DIR / f"{_safe_id(requested_approval_id)}.json"

    if not requested_approval_id:
        blockers.append("approval_id_required_for_adapter_export_packet_write")
    if not expected:
        blockers.append("expected_export_digest_required")
    if not statement:
        blockers.append("operator_export_write_statement_required")

    req = service.get_approval(requested_approval_id) if requested_approval_id else None
    if req is None:
        blockers.append("approval_request_not_loadable")
    else:
        target_path = str(req.action_spec.target_path or "").replace("\\", "/")
        try:
            packet = json.loads(str(req.action_spec.content or ""))
        except json.JSONDecodeError:
            blockers.append("approval_content_not_valid_json")
            packet = {}
        runtime_adapter_target = str(
            (req.action_spec.metadata or {}).get("runtime_adapter_target")
            or packet.get("runtime_adapter_target")
            or ""
        ).strip() or None
        schedule_id = (
            str((packet.get("digest_material") or {}).get("schedule_id_filter") or "").strip()
            or None
        )
        try:
            entry_count = int(packet.get("entry_count") or 0)
        except (TypeError, ValueError):
            entry_count = 0
        if req.status == "pending" and not statement:
            blockers.append("operator_decision_not_approved")
        elif req.status not in {"pending", "approved"}:
            blockers.append("approval_status_not_approved_or_pending_with_statement")

    target_abs, target_blockers = _target_blockers(
        vault,
        target_path,
        runtime_adapter_target or "",
        expected,
    )
    blockers.extend(target_blockers)
    if marker_path.exists():
        blockers.append("exact_once_marker_already_present")

    current_readiness = None
    if runtime_adapter_target:
        current_readiness = build_phase11_chat_schedule_adapter_export_readiness(
            vault,
            runtime_adapter_target=runtime_adapter_target,
            schedule_id=schedule_id,
            expected_export_digest=expected,
            write_approval=False,
        )
    if req is not None:
        blockers.extend(
            _packet_blockers(
                req=req,
                packet=packet,
                expected_export_digest=expected,
                target_path=target_path,
                current_readiness=current_readiness,
            )
        )

    if blockers:
        return _blocked_payload(
            vault=vault,
            approval_id=requested_approval_id,
            expected_export_digest=expected,
            target_path=target_path,
            runtime_adapter_target=runtime_adapter_target,
            entry_count=entry_count,
            marker_path=marker_path,
            blockers=blockers,
        )

    assert req is not None
    assert target_abs is not None
    assert runtime_adapter_target is not None

    packet_json = json.dumps(packet, indent=2, sort_keys=True) + "\n"
    executor_material = _executor_digest_material(
        approval_id=requested_approval_id,
        export_digest=expected,
        target_path=target_path,
        packet_sha256=_sha256_text(packet_json),
    )
    executor_digest = _sha256_text(_canonical_json(executor_material))
    execution_id = f"chat-approved-schedule-adapter-export-{executor_digest[:20]}"
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

        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text(
            json.dumps(
                _marker_payload(
                    status="executing",
                    approval_id=requested_approval_id,
                    execution_id=execution_id,
                    export_digest=expected,
                    executor_digest=executor_digest,
                    target_path=target_path,
                    runtime_adapter_target=runtime_adapter_target,
                    operator_id=operator,
                    written=False,
                ),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        target_abs.parent.mkdir(parents=True, exist_ok=True)
        target_abs.write_text(packet_json, encoding="utf-8")
        written_packet = json.loads(target_abs.read_text(encoding="utf-8"))
        if written_packet.get("export_digest") != expected:
            raise RuntimeError("written_packet_export_digest_mismatch")

        marker_path.write_text(
            json.dumps(
                _marker_payload(
                    status="executed",
                    approval_id=requested_approval_id,
                    execution_id=execution_id,
                    export_digest=expected,
                    executor_digest=executor_digest,
                    target_path=target_path,
                    runtime_adapter_target=runtime_adapter_target,
                    operator_id=operator,
                    written=True,
                ),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
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
                "phase11_chat_approved_schedule_adapter_export_packet_writer": True,
                "phase11_chat_approved_schedule_adapter_export_packet_writer_digest": executor_digest,
                "approval_consumed": True,
                "target_packet_content_sha256": _sha256_text(packet_json),
                "next_required_pass": NEXT_RECOMMENDED_PASS,
                **_effect_flags(written=True),
            }
        )
        req.action_spec.metadata = metadata
        _write_approval(service, req)

        audit_path = _write_audit(
            vault=vault,
            approval_id=requested_approval_id,
            execution_id=execution_id,
            export_digest=expected,
            executor_digest=executor_digest,
            target_path=target_path,
            runtime_adapter_target=runtime_adapter_target,
            entry_count=entry_count,
            operator_id=operator,
        )
    except Exception as exc:
        error = str(exc)
        try:
            marker_path.write_text(
                json.dumps(
                    _marker_payload(
                        status="execution_failed",
                        approval_id=requested_approval_id,
                        execution_id=execution_id,
                        export_digest=expected,
                        executor_digest=executor_digest,
                        target_path=target_path,
                        runtime_adapter_target=runtime_adapter_target,
                        operator_id=operator,
                        written=False,
                        error=error,
                    ),
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
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
            expected_export_digest=expected,
            target_path=target_path,
            runtime_adapter_target=runtime_adapter_target,
            entry_count=entry_count,
            marker_path=marker_path,
            blockers=[f"adapter_export_packet_write_failed:{error}"],
        )
        failed["status"] = "FAILED / APPROVED ADAPTER-EXPORT PACKET WRITER / PARTIAL EXECUTION CHECK REQUIRED"
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
            export_digest=expected,
            target_path=target_path,
            runtime_adapter_target=runtime_adapter_target,
            entry_count=entry_count,
            approval_status="executed",
            operator_approval_recorded=approval_recorded_from_statement,
            approval_consumed=True,
            exact_once_marker_written=True,
            written=True,
            blocker_count=0,
        ),
        "digest_proof": {
            "expected_export_digest": expected,
            "export_digest": expected,
            "export_digest_matched": True,
            "packet_sha256": _sha256_text(packet_json),
            "executor_digest": executor_digest,
            "executor_digest_material": executor_material,
            "result_digest": _sha256_text(
                _canonical_json(
                    {
                        "approval_id": requested_approval_id,
                        "execution_id": execution_id,
                        "target_path": target_path,
                        "target_content_sha256": _sha256_text(packet_json),
                    }
                )
            ),
        },
        "exact_once_marker": {
            "marker_path": _rel(vault, marker_path),
            "marker_written": True,
            "marker_status": "executed",
            "duplicate_blocked_before_target_write": True,
        },
        "target_write": {
            "target_path": target_path,
            "target_content_sha256": _sha256_text(packet_json),
            "runtime_adapter_target": runtime_adapter_target,
            "entry_count": entry_count,
            **_effect_flags(written=True),
        },
        "execution_record": {
            "execution_id": execution_id,
            "execution_status": "completed",
            "approval_status": "executed",
        },
        "audit_record": {
            "audit_written": True,
            "audit_record_path": audit_path,
        },
        "authority": _authority(),
        "blocked_reasons": [],
    }


def format_phase11_chat_approved_schedule_adapter_export_packet_writer(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    digest = payload.get("digest_proof") or {}
    target = payload.get("target_write") or {}
    lines = [
        "Phase 11 Chat Approved Schedule Adapter Export Packet Writer",
        f"Status: {payload.get('status')}",
        f"Approval id: {summary.get('approval_id') or 'none'}",
        f"Runtime adapter: {summary.get('runtime_adapter_target') or target.get('runtime_adapter_target') or 'missing'}",
        f"Export digest: {digest.get('export_digest') or 'missing'}",
        f"Executor digest: {digest.get('executor_digest') or 'missing'}",
        f"Target path: {target.get('target_path') or summary.get('target_path') or 'missing'}",
        f"Export packet written: {target.get('export_packet_written')}",
        f"External scheduler changed: {target.get('external_scheduler_changed')}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers)
    lines.append(
        "Boundary: approved local adapter export packet write only; no external "
        "scheduler mutation, OpenClaw/Hermes cron change, Agent Bus task write, "
        "runtime/workflow dispatch, Discord/API provider call, credential read, "
        "or broader canonical writeback."
    )
    return "\n".join(lines)
