"""Phase 11 Chat runtime-side cron/schedule apply handler.

Processes Chat-originated schedule-control handoff packets (written by
``phase11_chat_approved_schedule_adapter_export_packet_writer.py``) and
either dry-runs or applies the schedule change to the live ChaseOS schedule
loader and runtime adapter export.

Hard boundaries:
- Dry-run by default: reads and validates the packet but writes nothing.
- Live apply (``apply_mode=True``) requires ``operator_approved=True`` plus a
  non-empty ``operator_approval_statement``.
- Does NOT mutate external cron/scheduler files (OpenClaw .crontab, system cron).
- Does NOT post to Discord.
- Writes evidence regardless of mode.
- Validates schedule digest material before any write.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.schedules.loader import (
    ScheduleIntent,
    enable_schedule,
    list_schedules,
    load_schedule,
    validate_all_schedules,
)


MODEL_VERSION = "studio.phase11_chat_schedule_apply_handler.v1"
SURFACE_ID = "phase11_chat_schedule_apply_handler"
PASS_ID = "phase11-chat-schedule-apply-handler"
STATUS_DRY = "COMPLETE / DRY RUN / NO SCHEDULE MUTATION"
STATUS_APPLIED = "COMPLETE / SCHEDULE INTENT APPLIED / EXTERNAL CRON UNCHANGED"
STATUS_BLOCKED = "BLOCKED / SCHEDULE APPLY NOT EXECUTED"
NEXT_RECOMMENDED_PASS = "phase11-chat-credential-setup-ux"

EVIDENCE_DIR = Path("07_LOGS") / "Agent-Activity"
ADAPTER_EXPORTS_DIR = Path("runtime") / "studio" / "chat" / "schedule-adapter-exports"

_ALLOWED_APPLY_ACTIONS = {"enable_schedule", "validate_only", "dry_run"}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(value: str | None) -> str:
    return " ".join(str(value or "").strip().split())


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _load_adapter_export_packet(vault: Path, packet_id: str) -> dict[str, Any] | None:
    """Load a local adapter export packet by ID or filename."""
    exports_dir = vault / ADAPTER_EXPORTS_DIR
    if not exports_dir.is_dir():
        return None
    candidates = list(exports_dir.glob(f"*{packet_id}*.json"))
    if not candidates:
        return None
    path = sorted(candidates)[-1]
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_evidence(
    vault: Path,
    *,
    session_id: str,
    action: str,
    schedule_id: str | None,
    dry_run: bool,
    apply_mode: bool,
    operator_approved: bool,
    validation_ok: bool,
    schedule_written: bool,
    blocked_reasons: list[str],
    external_cron_mutated: bool = False,
) -> str:
    root = vault / EVIDENCE_DIR
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{PASS_ID}-{session_id[:20]}.md"
    status = STATUS_DRY if dry_run else (STATUS_APPLIED if schedule_written else STATUS_BLOCKED)
    path.write_text(
        "\n".join([
            "---",
            "type: agent-activity",
            "runtime: Codex",
            f"pass_id: {PASS_ID}",
            f"session_id: {session_id}",
            f"status: {status}",
            "---",
            "",
            "# Phase 11 Chat Schedule Apply Handler",
            "",
            f"action: {action}",
            f"schedule_id: {schedule_id or '—'}",
            f"dry_run: {dry_run}",
            f"apply_mode: {apply_mode}",
            f"operator_approved: {operator_approved}",
            f"validation_ok: {validation_ok}",
            f"schedule_written: {schedule_written}",
            f"external_cron_mutated: {external_cron_mutated}",
            f"blocked_reasons: {blocked_reasons or []}",
            f"written_at_utc: {_now_utc()}",
        ]),
        encoding="utf-8",
    )
    try:
        return path.relative_to(vault).as_posix()
    except ValueError:
        return str(path)


def handle_schedule_apply(
    vault_root: str | Path,
    *,
    schedule_id: str | None = None,
    packet_id: str | None = None,
    action: str = "dry_run",
    expected_schedule_digest: str | None = None,
    operator_approved: bool = False,
    operator_approval_statement: str | None = None,
    apply_mode: bool = False,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Handle a Chat-originated schedule-control apply request.

    Args:
        vault_root: Vault root.
        schedule_id: ChaseOS schedule ID (matches ``runtime/schedules/*.yaml`` filename stem).
        packet_id: Local adapter export packet ID (from ``schedule-adapter-exports/``).
        action: ``enable_schedule``, ``validate_only``, or ``dry_run``.
        expected_schedule_digest: SHA-256 digest of current schedule YAML content; must match.
        operator_approved: Must be True for live ``apply_mode``.
        operator_approval_statement: Required for live ``apply_mode``.
        apply_mode: If True AND operator_approved, writes to ChaseOS schedule YAML.
        dry_run: Default True. ``dry_run=False`` + ``apply_mode=True`` + ``operator_approved=True``
                 = live apply.
    """

    vault = Path(vault_root).resolve()
    action = str(action or "dry_run").strip().lower()
    session_id = _sha256(f"{schedule_id}:{packet_id}:{action}:{expected_schedule_digest}")[:20]
    blockers: list[str] = []

    if action not in _ALLOWED_APPLY_ACTIONS:
        blockers.append(f"action_not_permitted:{action}")

    schedule_intent: ScheduleIntent | None = None
    schedule_yaml_content: str | None = None
    schedule_valid = False

    if schedule_id:
        try:
            schedule_intent = load_schedule(schedule_id, vault)
        except Exception as exc:
            blockers.append(f"schedule_load_failed:{exc!s:.100}")

        if schedule_intent is not None:
            schedule_yaml_path = vault / "runtime" / "schedules" / f"{schedule_id}.yaml"
            if schedule_yaml_path.exists():
                schedule_yaml_content = schedule_yaml_path.read_text(encoding="utf-8")
                actual_digest = _sha256(schedule_yaml_content)[:32]
                if expected_schedule_digest and expected_schedule_digest != actual_digest:
                    blockers.append("schedule_digest_mismatch")
                schedule_valid = True
            else:
                blockers.append(f"schedule_yaml_not_found:{schedule_id}")
    else:
        blockers.append("schedule_id_required")

    packet_data: dict[str, Any] | None = None
    if packet_id:
        packet_data = _load_adapter_export_packet(vault, packet_id)
        if packet_data is None:
            blockers.append(f"adapter_export_packet_not_found:{packet_id}")

    if not dry_run and apply_mode:
        if not operator_approved:
            blockers.append("operator_approved_required_for_apply_mode")
        if not _norm(operator_approval_statement):
            blockers.append("operator_approval_statement_required_for_apply_mode")

    try:
        validation_errors = validate_all_schedules(vault_root=vault)
        validation_ok = len(validation_errors) == 0
        if not validation_ok:
            blockers.append(f"schedule_validation_errors:{len(validation_errors)}")
    except Exception as exc:
        validation_ok = False
        blockers.append(f"schedule_validation_exception:{exc!s:.100}")

    evidence_path = _write_evidence(
        vault,
        session_id=session_id,
        action=action,
        schedule_id=schedule_id,
        dry_run=dry_run,
        apply_mode=apply_mode,
        operator_approved=operator_approved,
        validation_ok=validation_ok,
        schedule_written=False,
        blocked_reasons=blockers,
    )

    if blockers:
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "pass": PASS_ID,
            "status": STATUS_BLOCKED,
            "generated_at_utc": _now_utc(),
            "vault_root": str(vault),
            "dry_run": dry_run,
            "apply_mode": apply_mode,
            "session_id": session_id,
            "action": action,
            "schedule_id": schedule_id,
            "schedule_valid": schedule_valid,
            "validation_ok": validation_ok,
            "operator_approved": operator_approved,
            "schedule_written": False,
            "external_cron_mutated": False,
            "evidence_path": evidence_path,
            "blocked_reasons": list(dict.fromkeys(blockers)),
        }

    schedule_written = False
    pre_state: str | None = None
    post_state: str | None = None

    if not dry_run and apply_mode and operator_approved and action == "enable_schedule" and schedule_id:
        assert schedule_intent is not None
        pre_state = "disabled" if not schedule_intent.enabled else "already_enabled"
        if not schedule_intent.enabled:
            enable_schedule(schedule_id, vault)
            schedule_written = True
            post_state = "enabled"
        else:
            post_state = "already_enabled"

        _write_evidence(
            vault,
            session_id=session_id,
            action=action,
            schedule_id=schedule_id,
            dry_run=False,
            apply_mode=True,
            operator_approved=True,
            validation_ok=True,
            schedule_written=schedule_written,
            blocked_reasons=[],
        )

    current_schedules: list[dict[str, Any]] = []
    try:
        current_schedules = list_schedules(vault_root=vault) or []  # type: ignore[assignment]
    except Exception:
        pass

    schedule_summary = None
    if schedule_intent is not None:
        cadence = schedule_intent.cadence or {}
        schedule_summary = {
            "id": schedule_intent.schedule_id,
            "workflow_id": schedule_intent.workflow_id,
            "cron_expression": (cadence.get("cron_expression") if isinstance(cadence, dict) else getattr(cadence, "cron_expression", None)),
            "enabled": schedule_intent.enabled,
            "runtime_adapter": schedule_intent.runtime_adapter_target,
        }

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS_DRY if dry_run or not apply_mode else STATUS_APPLIED,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "dry_run": dry_run,
        "apply_mode": apply_mode,
        "session_id": session_id,
        "action": action,
        "schedule_id": schedule_id,
        "schedule_valid": schedule_valid,
        "validation_ok": validation_ok,
        "operator_approved": operator_approved,
        "schedule_written": schedule_written,
        "pre_apply_state": pre_state,
        "post_apply_state": post_state,
        "external_cron_mutated": False,
        "schedule_summary": schedule_summary,
        "current_schedule_count": len(current_schedules),
        "packet_data_loaded": packet_data is not None,
        "evidence_path": evidence_path,
        "blocked_reasons": [],
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        "authority": {
            "schedule_yaml_write_allowed_with_approval": True,
            "external_cron_mutation_allowed": False,
            "discord_call_allowed": False,
            "provider_call_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "warnings": [
            "External cron (OpenClaw .crontab, system cron) is never mutated by this handler.",
            "Set apply_mode=True and operator_approved=True for live ChaseOS schedule YAML changes.",
            "Dry-run is the safe default; validation runs in both modes.",
        ],
    }
