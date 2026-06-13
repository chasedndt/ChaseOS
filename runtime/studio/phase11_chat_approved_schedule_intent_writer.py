"""Phase 11 Chat approved schedule-intent writer.

This governed writer consumes one staged, approved Studio Chat schedule proposal
record and writes its declared schedule YAML exactly once to runtime/schedules/.
It regenerates the schedule index after the file write. It does not enable the
schedule, mutate OpenClaw/Hermes cron state, dispatch runtime work, create Agent
Bus tasks, call Discord/providers, or read credentials.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from runtime.schedules.loader import _parse_yaml_mapping, _regenerate_index, _validate_schedule


MODEL_VERSION = "studio.phase11_chat_approved_schedule_intent_writer.v1"
SURFACE_ID = "phase11_chat_approved_schedule_intent_writer"
PASS_ID = "studio-chat-approved-schedule-intent-writer"
STATUS = "COMPLETE / APPROVED-SCHEDULE-INTENT WRITTEN / VERIFIED / INDEX REGENERATED"
NEXT_RECOMMENDED_PASS = "studio-chat-schedule-intent-activation-readiness"
SCHEDULE_PROPOSAL_ROOT = Path("runtime/studio/chat/schedule-proposals")
MARKER_DIR = Path("runtime/studio/approvals/_chat_schedule_intent_writer_markers")
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


def _authority() -> dict[str, bool]:
    return {
        "staged_schedule_proposal_read_allowed": True,
        "exact_once_marker_write_allowed": True,
        "schedule_intent_yaml_write_allowed": True,
        "schedule_index_regeneration_allowed": True,
        "schedule_enable_allowed": False,
        "external_scheduler_mutation_allowed": False,
        "openclaw_cron_mutation_allowed": False,
        "hermes_cron_mutation_allowed": False,
        "agent_bus_task_write_allowed": False,
        "runtime_dispatch_allowed": False,
        "workflow_dispatch_allowed": False,
        "discord_api_calls_allowed": False,
        "provider_calls_allowed": False,
        "credential_values_visible": False,
    }


def _effect_flags(*, written: bool = False) -> dict[str, bool]:
    return {
        "target_schedule_yaml_written": written,
        "schedule_intent_written": written,
        "schedule_index_regenerated": written,
        "canonical_schedule_intent_written": written,
        "schedule_enabled": False,
        "external_scheduler_changed": False,
        "openclaw_cron_changed": False,
        "hermes_cron_changed": False,
        "agent_bus_task_written": False,
        "runtime_dispatched": False,
        "workflow_dispatched": False,
        "discord_api_called": False,
        "provider_call_performed": False,
        "credential_value_read": False,
    }


def _load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, "staged_schedule_proposal_record_missing"
    except json.JSONDecodeError as exc:
        return None, f"staged_schedule_proposal_record_malformed:{exc}"
    if not isinstance(payload, dict):
        return None, "staged_schedule_proposal_record_not_mapping"
    return payload, None


def _staged_path(
    *,
    vault: Path,
    staged_proposal_path: str,
    schedule_id: str,
) -> tuple[Path | None, list[str]]:
    blockers: list[str] = []
    staged = str(staged_proposal_path or "").replace("\\", "/").strip()
    sid = str(schedule_id or "").strip()
    if staged and sid:
        blockers.append("provide_staged_proposal_path_or_schedule_id_not_both")
    if not staged and not sid:
        blockers.append("staged_proposal_path_or_schedule_id_required")
        return None, blockers
    if sid and not re.fullmatch(r"[A-Za-z0-9_-]+", sid):
        blockers.append("schedule_id_not_path_safe")
    rel_path = Path(staged) if staged else SCHEDULE_PROPOSAL_ROOT / f"{_safe_id(sid)}.json"
    if str(rel_path).replace("\\", "/").startswith("/"):
        blockers.append("staged_proposal_path_must_be_repo_relative")
    normalized = str(rel_path).replace("\\", "/")
    if not normalized.startswith(f"{SCHEDULE_PROPOSAL_ROOT.as_posix()}/"):
        blockers.append("staged_proposal_path_outside_schedule_proposal_root")
    if not normalized.endswith(".json"):
        blockers.append("staged_proposal_path_not_json")
    staged_abs = (vault / normalized).resolve()
    root_abs = (vault / SCHEDULE_PROPOSAL_ROOT).resolve()
    try:
        staged_abs.relative_to(vault.resolve())
    except ValueError:
        blockers.append("staged_proposal_path_escapes_vault")
    try:
        staged_abs.relative_to(root_abs)
    except ValueError:
        blockers.append("staged_proposal_path_escapes_schedule_proposal_root")
    return staged_abs, blockers


def _target_path(
    *,
    vault: Path,
    schedule_id: str,
    declared_target: str,
) -> tuple[Path | None, list[str]]:
    blockers: list[str] = []
    sid = str(schedule_id or "").strip()
    target = str(declared_target or "").replace("\\", "/").strip()
    if not sid:
        blockers.append("schedule_id_required")
    if sid and not re.fullmatch(r"[A-Za-z0-9_-]+", sid):
        blockers.append("schedule_id_not_path_safe")
    expected = f"runtime/schedules/{sid}.yaml" if sid else ""
    if not target:
        blockers.append("target_schedule_path_required")
    elif target != expected:
        blockers.append("target_schedule_path_mismatch")
    if target == "runtime/schedules/index.yaml":
        blockers.append("target_schedule_path_is_index")
    if target and not target.endswith(".yaml"):
        blockers.append("target_schedule_path_not_yaml")
    target_abs = (vault / target).resolve() if target else None
    root_abs = (vault / "runtime" / "schedules").resolve()
    if target_abs is not None:
        try:
            target_abs.relative_to(vault.resolve())
        except ValueError:
            blockers.append("target_schedule_path_escapes_vault")
        try:
            target_abs.relative_to(root_abs)
        except ValueError:
            blockers.append("target_schedule_path_escapes_runtime_schedules")
    return target_abs, blockers


def _record_blockers(
    *,
    record: dict[str, Any] | None,
    expected_schedule_digest: str,
    schedule_yaml: str,
    schedule_intent: dict[str, Any] | None,
    parsed_yaml: dict[str, Any] | None,
    target_abs: Path | None,
    vault: Path,
) -> list[str]:
    blockers: list[str] = []
    if record is None:
        return blockers
    if record.get("schema_version") != "phase11_chat_approved_schedule_proposal_record.v1":
        blockers.append("staged_record_schema_version_mismatch")
    if record.get("status") != "approved_schedule_proposal_recorded":
        blockers.append("staged_record_status_not_approved_schedule_proposal_recorded")
    if record.get("approval_consumed") is not True:
        blockers.append("staged_record_approval_not_consumed")
    if record.get("schedule_intent_writer_required") is not True:
        blockers.append("staged_record_writer_not_required")
    if record.get("schedule_intent_written") is not False:
        blockers.append("staged_record_already_written")
    if record.get("target_schedule_yaml_written") is not False:
        blockers.append("staged_record_target_schedule_already_written")
    digest = str(record.get("schedule_digest") or "")
    if not expected_schedule_digest:
        blockers.append("expected_schedule_digest_required")
    elif digest != expected_schedule_digest:
        blockers.append("schedule_digest_mismatch")
    if not schedule_yaml.strip():
        blockers.append("future_schedule_yaml_missing")
    if schedule_intent is None:
        blockers.append("future_schedule_intent_missing_or_invalid")
    if parsed_yaml is None:
        blockers.append("future_schedule_yaml_missing_or_invalid")
    if schedule_intent is not None and parsed_yaml is not None and schedule_intent != parsed_yaml:
        blockers.append("future_schedule_intent_yaml_mismatch")
    if parsed_yaml is not None:
        if parsed_yaml.get("enabled") is True:
            blockers.append("approved_schedule_intent_enabled_true_not_allowed")
        if target_abs is not None:
            try:
                _validate_schedule(parsed_yaml, target_abs, vault, check_registry=True)
            except Exception as exc:
                blockers.append(f"approved_schedule_intent_invalid:{exc}")
    for key in (
        "schedule_enabled",
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
        if key in record and bool(record.get(key)) is not False:
            blockers.append(f"staged_record_effect_flag_not_false:{key}")
    return blockers


def _summary(
    *,
    vault: Path,
    record: dict[str, Any] | None,
    expected_schedule_digest: str,
    staged_path: Path | None,
    target_path: str,
    written: bool,
    marker_written: bool = False,
    duplicate_blocked_before_target_write: bool = False,
    blocker_count: int = 0,
) -> dict[str, Any]:
    intent = (record or {}).get("future_schedule_intent") or {}
    cadence = intent.get("cadence") if isinstance(intent.get("cadence"), dict) else {}
    return {
        "approval_id": (record or {}).get("approval_id"),
        "expected_schedule_digest_provided": bool(expected_schedule_digest),
        "schedule_digest": (record or {}).get("schedule_digest"),
        "schedule_id": intent.get("schedule_id"),
        "schedule_kind": intent.get("schedule_kind"),
        "workflow_id": intent.get("workflow_id"),
        "command_id": intent.get("command_id"),
        "cron_expression": cadence.get("cron_expression"),
        "timezone": cadence.get("timezone"),
        "runtime_adapter_target": intent.get("runtime_adapter_target"),
        "staged_schedule_proposal_path": _rel(vault, staged_path) if staged_path else None,
        "target_schedule_path": target_path or None,
        "exact_once_marker_written": marker_written,
        "duplicate_blocked_before_target_write": duplicate_blocked_before_target_write,
        **_effect_flags(written=written),
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        "blocker_count": blocker_count,
    }


def _blocked_payload(
    *,
    vault: Path,
    record: dict[str, Any] | None,
    expected_schedule_digest: str,
    staged_path: Path | None,
    target_path: str,
    marker_path: Path | None,
    blockers: list[str],
) -> dict[str, Any]:
    unique = list(dict.fromkeys(blockers))
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": "BLOCKED / APPROVED-SCHEDULE-INTENT WRITER / NO SCHEDULE WRITE",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": False,
        "approval_gated": True,
        "summary": _summary(
            vault=vault,
            record=record,
            expected_schedule_digest=expected_schedule_digest,
            staged_path=staged_path,
            target_path=target_path,
            written=False,
            duplicate_blocked_before_target_write="exact_once_marker_already_present" in unique,
            blocker_count=len(unique),
        ),
        "digest_proof": {
            "expected_schedule_digest": expected_schedule_digest or None,
            "schedule_digest": (record or {}).get("schedule_digest"),
            "schedule_digest_matched": False,
            "writer_digest": None,
        },
        "exact_once_marker": {
            "marker_path": _rel(vault, marker_path) if marker_path else None,
            "marker_written": False,
            "duplicate_blocked_before_target_write": "exact_once_marker_already_present" in unique,
        },
        "target_write": {
            "staged_schedule_proposal_path": _rel(vault, staged_path) if staged_path else None,
            "target_path": target_path or None,
            "target_file_written": False,
            "index_path": "runtime/schedules/index.yaml",
            **_effect_flags(written=False),
        },
        "audit_record": {
            "audit_written": False,
            "audit_record_path": None,
        },
        "authority": _authority(),
        "blocked_reasons": unique,
    }


def _writer_digest_material(
    *,
    staged_path: str,
    target_path: str,
    schedule_digest: str,
    schedule_yaml_sha256: str,
) -> dict[str, Any]:
    return {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "staged_path": staged_path,
        "target_path": target_path,
        "schedule_digest": schedule_digest,
        "schedule_yaml_sha256": schedule_yaml_sha256,
    }


def _marker_payload(
    *,
    status: str,
    execution_id: str,
    schedule_digest: str,
    writer_digest: str,
    staged_path: str,
    target_path: str,
    operator_id: str,
    written: bool,
    error: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": "phase11_chat_approved_schedule_intent_writer_marker.v1",
        "status": status,
        "execution_id": execution_id,
        "pass": PASS_ID,
        "surface": SURFACE_ID,
        "schedule_digest": schedule_digest,
        "writer_digest": writer_digest,
        "staged_schedule_proposal_path": staged_path,
        "target_schedule_path": target_path,
        "operator_id": operator_id,
        **_effect_flags(written=written),
        "error": error,
        "updated_at_utc": _now_utc(),
    }


def _next_audit_path(vault: Path, writer_digest: str) -> Path:
    root = vault / AUDIT_DIR
    root.mkdir(parents=True, exist_ok=True)
    base = root / f"{PASS_ID}-{writer_digest[:20]}.md"
    if not base.exists():
        return base
    for index in range(2, 100):
        candidate = root / f"{PASS_ID}-{writer_digest[:20]}-{index}.md"
        if not candidate.exists():
            return candidate
    raise RuntimeError("could not allocate approved schedule intent writer audit path")


def _write_audit(
    *,
    vault: Path,
    execution_id: str,
    schedule_digest: str,
    writer_digest: str,
    staged_path: str,
    target_path: str,
    schedule_intent: dict[str, Any],
    operator_id: str,
) -> str:
    path = _next_audit_path(vault, writer_digest)
    cadence = schedule_intent.get("cadence") if isinstance(schedule_intent.get("cadence"), dict) else {}
    text = "\n".join(
        [
            "---",
            "type: agent-activity",
            "runtime: Codex",
            f"pass_id: {PASS_ID}",
            f"execution_id: {execution_id}",
            f"status: {STATUS}",
            "---",
            "",
            "# Phase 11 Chat Approved Schedule Intent Writer",
            "",
            f"operator_id: {operator_id}",
            f"execution_id: {execution_id}",
            f"schedule_digest: {schedule_digest}",
            f"writer_digest: {writer_digest}",
            f"schedule_id: {schedule_intent.get('schedule_id') or 'missing'}",
            f"schedule_kind: {schedule_intent.get('schedule_kind') or 'missing'}",
            f"workflow_id: {schedule_intent.get('workflow_id') or 'none'}",
            f"command_id: {schedule_intent.get('command_id') or 'none'}",
            f"cron_expression: {cadence.get('cron_expression') or 'missing'}",
            f"timezone: {cadence.get('timezone') or 'missing'}",
            f"runtime_adapter_target: {schedule_intent.get('runtime_adapter_target') or 'missing'}",
            f"staged_schedule_proposal_path: {staged_path}",
            f"target_schedule_path: {target_path}",
            "target_schedule_yaml_written: true",
            "schedule_intent_written: true",
            "schedule_index_regenerated: true",
            "schedule_enabled: false",
            "external_scheduler_changed: false",
            "openclaw_cron_changed: false",
            "hermes_cron_changed: false",
            "agent_bus_task_written: false",
            "runtime_dispatched: false",
            "workflow_dispatched: false",
            "discord_api_called: false",
            "provider_call_performed: false",
            "credential_value_read: false",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")
    return _rel(vault, path)


def execute_phase11_chat_approved_schedule_intent_writer(
    vault_root: str | Path,
    *,
    staged_proposal_path: str | None = None,
    schedule_id: str | None = None,
    expected_schedule_digest: str | None = None,
    operator_id: str = "operator",
    operator_schedule_write_statement: str | None = None,
) -> dict[str, Any]:
    """Write one staged approved schedule proposal to runtime/schedules."""

    vault = Path(vault_root).resolve()
    expected = str(expected_schedule_digest or "").strip()
    operator = str(operator_id or "operator").strip() or "operator"
    statement = " ".join(str(operator_schedule_write_statement or "").strip().split())
    blockers: list[str] = []

    if not expected:
        blockers.append("expected_schedule_digest_required")
    if not statement:
        blockers.append("operator_schedule_write_statement_required")

    staged_abs, staged_blockers = _staged_path(
        vault=vault,
        staged_proposal_path=str(staged_proposal_path or ""),
        schedule_id=str(schedule_id or ""),
    )
    blockers.extend(staged_blockers)

    record: dict[str, Any] | None = None
    if staged_abs is not None:
        record, load_error = _load_json(staged_abs)
        if load_error:
            blockers.append(load_error)

    schedule_yaml = str((record or {}).get("future_schedule_yaml") or "")
    schedule_intent = (record or {}).get("future_schedule_intent")
    if schedule_intent is not None and not isinstance(schedule_intent, dict):
        schedule_intent = None
    parsed_yaml: dict[str, Any] | None = None
    if schedule_yaml.strip():
        try:
            parsed = _parse_yaml_mapping(schedule_yaml)
            parsed_yaml = parsed if isinstance(parsed, dict) else None
        except Exception as exc:
            blockers.append(f"future_schedule_yaml_malformed:{exc}")

    parsed_schedule_id = str((parsed_yaml or schedule_intent or {}).get("schedule_id") or "")
    declared_target = str((record or {}).get("target_schedule_path") or "")
    target_abs, target_blockers = _target_path(
        vault=vault,
        schedule_id=parsed_schedule_id,
        declared_target=declared_target,
    )
    blockers.extend(target_blockers)
    blockers.extend(
        _record_blockers(
            record=record,
            expected_schedule_digest=expected,
            schedule_yaml=schedule_yaml,
            schedule_intent=schedule_intent,
            parsed_yaml=parsed_yaml,
            target_abs=target_abs,
            vault=vault,
        )
    )

    marker_name = _safe_id(expected or parsed_schedule_id or (staged_abs.stem if staged_abs else "unknown"))
    marker_path = vault / MARKER_DIR / f"{marker_name}.json"
    if marker_path.exists():
        blockers.append("exact_once_marker_already_present")
    if target_abs is not None and target_abs.exists():
        blockers.append("schedule_intent_target_collision")

    if blockers:
        return _blocked_payload(
            vault=vault,
            record=record,
            expected_schedule_digest=expected,
            staged_path=staged_abs,
            target_path=declared_target,
            marker_path=marker_path,
            blockers=blockers,
        )

    assert staged_abs is not None
    assert record is not None
    assert schedule_intent is not None
    assert parsed_yaml is not None
    assert target_abs is not None

    staged_rel = _rel(vault, staged_abs)
    target_rel = _rel(vault, target_abs)
    schedule_yaml_sha = _sha256_text(schedule_yaml)
    writer_material = _writer_digest_material(
        staged_path=staged_rel,
        target_path=target_rel,
        schedule_digest=expected,
        schedule_yaml_sha256=schedule_yaml_sha,
    )
    writer_digest = _sha256_text(_canonical_json(writer_material))
    execution_id = f"chat-approved-schedule-intent-writer-{writer_digest[:20]}"

    try:
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text(
            json.dumps(
                _marker_payload(
                    status="executing",
                    execution_id=execution_id,
                    schedule_digest=expected,
                    writer_digest=writer_digest,
                    staged_path=staged_rel,
                    target_path=target_rel,
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
        target_abs.write_text(schedule_yaml.rstrip() + "\n", encoding="utf-8")
        _regenerate_index(vault)

        updated_record = dict(record)
        updated_record.update(
            {
                "status": "schedule_intent_written",
                "schedule_intent_writer_required": False,
                "schedule_intent_writer": SURFACE_ID,
                "schedule_intent_writer_execution_id": execution_id,
                "schedule_intent_writer_digest": writer_digest,
                "schedule_written_by": SURFACE_ID,
                "schedule_written_at_utc": _now_utc(),
                "operator_schedule_write_statement_recorded": bool(statement),
                "operator_schedule_write_statement_sha256": _sha256_text(statement),
                "target_schedule_content_sha256": schedule_yaml_sha,
                "schedule_index_path": "runtime/schedules/index.yaml",
                "next_required_pass": NEXT_RECOMMENDED_PASS,
                **_effect_flags(written=True),
            }
        )
        staged_abs.write_text(json.dumps(updated_record, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")

        marker_path.write_text(
            json.dumps(
                _marker_payload(
                    status="executed",
                    execution_id=execution_id,
                    schedule_digest=expected,
                    writer_digest=writer_digest,
                    staged_path=staged_rel,
                    target_path=target_rel,
                    operator_id=operator,
                    written=True,
                ),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        audit_path = _write_audit(
            vault=vault,
            execution_id=execution_id,
            schedule_digest=expected,
            writer_digest=writer_digest,
            staged_path=staged_rel,
            target_path=target_rel,
            schedule_intent=schedule_intent,
            operator_id=operator,
        )
    except Exception as exc:
        error = str(exc)
        try:
            marker_path.write_text(
                json.dumps(
                    _marker_payload(
                        status="execution_failed",
                        execution_id=execution_id,
                        schedule_digest=expected,
                        writer_digest=writer_digest,
                        staged_path=staged_rel,
                        target_path=target_rel,
                        operator_id=operator,
                        written=target_abs.exists(),
                        error=error,
                    ),
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
        except Exception:
            pass
        failed = _blocked_payload(
            vault=vault,
            record=record,
            expected_schedule_digest=expected,
            staged_path=staged_abs,
            target_path=target_rel,
            marker_path=marker_path,
            blockers=[f"approved_schedule_intent_writer_execution_failed:{error}"],
        )
        failed["status"] = "FAILED / APPROVED-SCHEDULE-INTENT WRITER / PARTIAL EXECUTION CHECK REQUIRED"
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
            vault=vault,
            record=record,
            expected_schedule_digest=expected,
            staged_path=staged_abs,
            target_path=target_rel,
            written=True,
            marker_written=True,
            blocker_count=0,
        ),
        "digest_proof": {
            "expected_schedule_digest": expected,
            "schedule_digest": record.get("schedule_digest"),
            "schedule_digest_matched": expected == record.get("schedule_digest"),
            "schedule_yaml_sha256": schedule_yaml_sha,
            "writer_digest": writer_digest,
            "writer_digest_material": writer_material,
            "result_digest": _sha256_text(
                _canonical_json(
                    {
                        "execution_id": execution_id,
                        "staged_path": staged_rel,
                        "target_path": target_rel,
                        "target_content_sha256": schedule_yaml_sha,
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
            "staged_schedule_proposal_path": staged_rel,
            "target_path": target_rel,
            "target_file_written": True,
            "target_content_sha256": schedule_yaml_sha,
            "index_path": "runtime/schedules/index.yaml",
            "schedule_id": schedule_intent.get("schedule_id"),
            "schedule_kind": schedule_intent.get("schedule_kind"),
            "workflow_id": schedule_intent.get("workflow_id"),
            "command_id": schedule_intent.get("command_id"),
            **_effect_flags(written=True),
        },
        "execution_record": {
            "execution_id": execution_id,
            "execution_status": "completed",
        },
        "audit_record": {
            "audit_written": True,
            "audit_record_path": audit_path,
        },
        "authority": _authority(),
        "blocked_reasons": [],
    }


def format_phase11_chat_approved_schedule_intent_writer(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    digest = payload.get("digest_proof") or {}
    target = payload.get("target_write") or {}
    lines = [
        "Phase 11 Chat Approved Schedule Intent Writer",
        f"Status: {payload.get('status')}",
        f"Schedule id: {summary.get('schedule_id') or target.get('schedule_id') or 'missing'}",
        f"Schedule digest: {digest.get('schedule_digest') or 'missing'}",
        f"Writer digest: {digest.get('writer_digest') or 'missing'}",
        f"Target schedule path: {target.get('target_path') or 'missing'}",
        f"Schedule intent written: {target.get('schedule_intent_written')}",
        f"Schedule index regenerated: {target.get('schedule_index_regenerated')}",
        f"Schedule enabled: {target.get('schedule_enabled')}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers)
    lines.append(
        "Boundary: approved schedule-intent file and schedule index only; no schedule "
        "enablement, external scheduler mutation, OpenClaw/Hermes cron change, Agent "
        "Bus task write, runtime/workflow dispatch, Discord/API provider call, or credential read."
    )
    return "\n".join(lines)
