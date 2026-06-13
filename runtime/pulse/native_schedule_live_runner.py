"""Governed live runner for ChaseOS Pulse native schedules.

This is the first runner that can write real local run-queue and audit records
for Pulse schedules. It remains deliberately narrow: it only consumes manifests
that were already patched into supervised active state, writes append-only local
queue/audit artifacts, and never starts a daemon, dispatches a runtime, executes
workflows, calls providers/connectors, writes Agent Bus tasks, or mutates
canonical state.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from runtime.pulse.card_schema import now_utc
from runtime.pulse.native_schedule_activation_gate import (
    REQUIRED_EVIDENCE_SLOTS,
)
from runtime.pulse.native_schedule_runner_proof import (
    DEFAULT_SCHEDULE_IDS,
    MANIFEST_DIR,
    _read_yaml,
)


LIVE_RUNNER_STATUS_BLOCKED_INACTIVE = "blocked_no_supervised_active_schedules"
LIVE_RUNNER_STATUS_BLOCKED_NOT_DUE = "blocked_no_due_schedules"
LIVE_RUNNER_STATUS_READY = "ready_for_live_run_queue_write"
LIVE_RUNNER_STATUS_WRITTEN = "live_run_queue_audit_written"
LIVE_RUNNER_STATUS_DUPLICATE = "duplicate_run_already_queued"
LIVE_RUNNER_STATUSES = {
    LIVE_RUNNER_STATUS_BLOCKED_INACTIVE,
    LIVE_RUNNER_STATUS_BLOCKED_NOT_DUE,
    LIVE_RUNNER_STATUS_READY,
    LIVE_RUNNER_STATUS_WRITTEN,
    LIVE_RUNNER_STATUS_DUPLICATE,
}

RUN_REASON_NATIVE_DUE = "native_schedule_due"
QUEUE_STATUS_PENDING = "queued_pending_runtime_dispatch"
AUDIT_EVENT_TYPE = "pulse_native_schedule_live_runner_queue_write"
TRIGGER_SOURCE = "native_chaseos_schedule_intent"

RUN_QUEUE_ROOT = "07_LOGS/Pulse-Decks/native-schedule-run-queue/"
AUDIT_ROOT = "07_LOGS/Pulse-Decks/native-schedule-audit/"
RUN_RECORD_ROOT = "07_LOGS/Pulse-Decks/native-schedule-runs/"
RUN_QUEUE_FILENAME = "native-schedule-run-queue.jsonl"
NEXT_RECOMMENDED_PASS = "chaseos-pulse-governed-runtime-dispatch-proof"

BLOCKED_EFFECTS = (
    "agent_bus_task_write",
    "approval_grant",
    "canonical_writeback",
    "external_scheduler_install",
    "provider_or_connector_call",
    "runtime_dispatch",
    "schedule_daemon_start",
    "workflow_execution",
)


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _date_slug(generated_at: str) -> str:
    date = generated_at[:10]
    return date if len(date) == 10 else now_utc()[:10]


def _slug(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in value).strip("-")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_schedule_ids(schedule_ids: tuple[str, ...] | None) -> tuple[str, ...]:
    ids = tuple(item.strip() for item in (schedule_ids or DEFAULT_SCHEDULE_IDS) if item.strip())
    if not ids:
        raise ValueError("at least one schedule_id is required")
    return ids


def _real_ref(value: str | None) -> bool:
    text = (value or "").strip()
    if not text:
        return False
    lowered = text.lower()
    if any(marker in lowered for marker in ("placeholder", "todo", "tbd", "example", "real-ref")):
        return False
    if "<" in text or ">" in text:
        return False
    return True


def _parse_generated_at(generated_at: str) -> datetime:
    text = generated_at.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        parsed = datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _local_now(generated_at: str, timezone_name: str) -> datetime:
    try:
        tz = ZoneInfo(timezone_name)
    except Exception:
        tz = timezone.utc
    return _parse_generated_at(generated_at).astimezone(tz)


def _parse_local_time(value: str) -> time:
    parts = value.strip().split(":")
    if len(parts) < 2:
        raise ValueError("Pulse schedule local_time must be HH:MM")
    return time(hour=int(parts[0]), minute=int(parts[1]))


def _due_values(*, generated_at: str, timezone_name: str, local_time: str) -> tuple[str, str, bool]:
    local = _local_now(generated_at, timezone_name)
    scheduled = _parse_local_time(local_time)
    due_date = local.date().isoformat()
    due_at_local = f"{due_date}T{scheduled.strftime('%H:%M')}:00[{timezone_name}]"
    return due_date, due_at_local, local.time().replace(second=0, microsecond=0) >= scheduled


def _manifest_path(vault: Path, schedule_id: str) -> Path:
    if "/" in schedule_id or "\\" in schedule_id or ".." in schedule_id:
        raise ValueError("invalid schedule_id path segment")
    path = (vault / MANIFEST_DIR / f"{schedule_id}.yaml").resolve()
    allowed_root = (vault / MANIFEST_DIR).resolve()
    try:
        path.relative_to(allowed_root)
    except ValueError as exc:
        raise ValueError("schedule manifest path must stay under runtime/schedules/manifests/") from exc
    if not path.exists():
        raise ValueError(f"Pulse native schedule manifest missing: {path}")
    return path


def _evidence_refs_from_manifest(manifest: dict[str, Any]) -> dict[str, str | None]:
    activation = manifest.get("activation_execution") or {}
    refs = activation.get("evidence_refs") or {}
    if not isinstance(refs, dict):
        refs = {}
    return {slot: refs.get(slot) for slot in REQUIRED_EVIDENCE_SLOTS}


def _missing_evidence(refs: dict[str, str | None]) -> tuple[str, ...]:
    return tuple(slot for slot in REQUIRED_EVIDENCE_SLOTS if not _real_ref(refs.get(slot)))


def _existing_idempotency_keys(queue_file: Path) -> set[str]:
    if not queue_file.exists():
        return set()
    keys: set[str] = set()
    for raw in queue_file.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        key = str(payload.get("idempotency_key") or "")
        if key:
            keys.add(key)
    return keys


@dataclass(frozen=True)
class PulseNativeScheduleLiveRunnerTarget:
    schedule_id: str
    manifest_path: str
    manifest_status: str
    enabled: bool
    activation_state: str
    activation_execution_status: str
    workflow_id: str
    audience: str
    output_root: str
    executor_adapter: str
    schedule_owner: str
    executor_is_adapter_only: bool
    timezone: str
    cadence_type: str
    local_time: str
    due_date: str
    due_at_local: str
    due_now: bool
    forced_due: bool
    active_supervised: bool
    duplicate: bool
    idempotency_key: str
    queue_entry_id: str
    audit_event_id: str
    missing_evidence_slots: tuple[str, ...]
    blockers: tuple[str, ...]
    external_connectors_enabled: bool = False
    unrestricted_browsing_enabled: bool = False
    canonical_writeback_enabled: bool = False
    openclaw_cron_owner: bool = False
    windows_task_scheduler_owner: bool = False

    def validate(self) -> None:
        if not self.schedule_id or not self.manifest_path:
            raise ValueError("live runner target requires schedule_id and manifest_path")
        if self.schedule_owner != "chaseos":
            raise ValueError("live runner requires ChaseOS-owned schedule")
        if not self.executor_is_adapter_only:
            raise ValueError("live runner requires adapter-only executor identity")
        if self.external_connectors_enabled or self.unrestricted_browsing_enabled:
            raise ValueError("live runner cannot enable external sources")
        if self.canonical_writeback_enabled:
            raise ValueError("live runner cannot enable canonical writeback")
        if self.openclaw_cron_owner or self.windows_task_scheduler_owner:
            raise ValueError("live runner cannot assign external scheduler ownership")
        expected_active = (
            self.manifest_status == "active"
            and self.enabled
            and self.activation_state == "active_supervised"
            and self.activation_execution_status == "active_supervised"
            and not self.missing_evidence_slots
        )
        if self.active_supervised != expected_active:
            raise ValueError("active_supervised must reflect manifest state and evidence refs")
        if self.active_supervised and "supervised_activation_missing" in self.blockers:
            raise ValueError("active supervised schedule cannot keep activation missing blocker")
        if not self.active_supervised and not self.blockers:
            raise ValueError("inactive live runner target must report blockers")
        if self.cadence_type != "daily":
            raise ValueError("live runner currently supports daily Pulse schedules only")
        if not self.idempotency_key or not self.queue_entry_id or not self.audit_event_id:
            raise ValueError("live runner target requires queue/audit ids")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class PulseNativeScheduleLiveQueueEntry:
    queue_entry_id: str
    schedule_id: str
    workflow_id: str
    audience: str
    output_root: str
    run_reason: str
    queue_status: str
    requested_at: str
    due_date: str
    due_at_local: str
    executor_adapter: str
    schedule_owner: str
    trigger_source: str
    approval_ref: str
    permission_envelope_ref: str
    audit_identity_ref: str
    run_queue_scope_ref: str
    runtime_adapter_scope_ref: str
    rollback_plan_ref: str
    external_scheduler_denial_ref: str
    canonical_writeback_denial_ref: str
    idempotency_key: str
    agent_bus_task_write_allowed: bool = False
    runtime_dispatch_allowed: bool = False
    workflow_execution_allowed: bool = False
    canonical_writeback_allowed: bool = False

    def validate(self) -> None:
        if not self.queue_entry_id or not self.schedule_id or not self.workflow_id:
            raise ValueError("live queue entry requires ids")
        if self.run_reason != RUN_REASON_NATIVE_DUE:
            raise ValueError("live queue entry has invalid run reason")
        if self.queue_status != QUEUE_STATUS_PENDING:
            raise ValueError("live queue entry must remain pending dispatch")
        if self.schedule_owner != "chaseos" or self.trigger_source != TRIGGER_SOURCE:
            raise ValueError("live queue entry requires ChaseOS native schedule ownership")
        refs = (
            self.approval_ref,
            self.permission_envelope_ref,
            self.audit_identity_ref,
            self.run_queue_scope_ref,
            self.runtime_adapter_scope_ref,
            self.rollback_plan_ref,
            self.external_scheduler_denial_ref,
            self.canonical_writeback_denial_ref,
        )
        if not all(_real_ref(ref) for ref in refs):
            raise ValueError("live queue entry requires real evidence refs")
        if (
            self.agent_bus_task_write_allowed
            or self.runtime_dispatch_allowed
            or self.workflow_execution_allowed
            or self.canonical_writeback_allowed
        ):
            raise ValueError("live queue entry cannot grant dispatch/writeback authority")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class PulseNativeScheduleLiveAuditEvent:
    event_id: str
    event_type: str
    queue_entry_id: str
    schedule_id: str
    generated_at: str
    trigger_source: str
    schedule_owner: str
    executor_is_adapter_only: bool
    audit_identity_ref: str
    run_queue_scope_ref: str
    rollback_plan_ref: str
    external_scheduler_denial_ref: str
    canonical_writeback_denial_ref: str
    real_audit_event_written: bool
    schedule_daemon_started: bool = False
    agent_bus_task_written: bool = False
    runtime_dispatch_started: bool = False
    workflow_execution_started: bool = False
    provider_or_connector_call_started: bool = False
    canonical_writeback_started: bool = False

    def validate(self) -> None:
        if not self.event_id or not self.queue_entry_id or not self.schedule_id:
            raise ValueError("live audit event requires ids")
        if self.event_type != AUDIT_EVENT_TYPE or self.trigger_source != TRIGGER_SOURCE:
            raise ValueError("live audit event has invalid type or trigger")
        if self.schedule_owner != "chaseos" or not self.executor_is_adapter_only:
            raise ValueError("live audit event requires ChaseOS ownership and adapter-only executor")
        if not all(
            _real_ref(ref)
            for ref in (
                self.audit_identity_ref,
                self.run_queue_scope_ref,
                self.rollback_plan_ref,
                self.external_scheduler_denial_ref,
                self.canonical_writeback_denial_ref,
            )
        ):
            raise ValueError("live audit event requires real audit/rollback/denial refs")
        if (
            self.schedule_daemon_started
            or self.agent_bus_task_written
            or self.runtime_dispatch_started
            or self.workflow_execution_started
            or self.provider_or_connector_call_started
            or self.canonical_writeback_started
        ):
            raise ValueError("live audit event cannot record blocked side effects as started")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class PulseNativeScheduleLiveRunner:
    generated_at: str
    runner_status: str
    schedule_ids: tuple[str, ...]
    schedule_count: int
    active_schedule_count: int
    due_schedule_count: int
    duplicate_count: int
    queue_entry_count: int
    audit_event_count: int
    execute_requested: bool
    force_due: bool
    write_executed: bool
    targets: tuple[PulseNativeScheduleLiveRunnerTarget, ...]
    run_queue_entries: tuple[PulseNativeScheduleLiveQueueEntry, ...]
    audit_events: tuple[PulseNativeScheduleLiveAuditEvent, ...]
    missing_evidence_slots: tuple[str, ...] = ()
    writes: tuple[str, ...] = ()
    next_recommended_pass: str = NEXT_RECOMMENDED_PASS
    local_only: bool = True
    writes_artifacts: bool = False
    run_queue_write_executed: bool = False
    audit_event_write_executed: bool = False
    schedule_daemon_started: bool = False
    schedule_manifest_write_executed: bool = False
    schedule_activation_executed: bool = False
    agent_bus_task_write_allowed: bool = False
    runtime_dispatch_allowed: bool = False
    workflow_execution_allowed: bool = False
    approval_granted: bool = False
    provider_or_connector_call_allowed: bool = False
    external_scheduler_install_allowed: bool = False
    canonical_writeback_allowed: bool = False
    mutates_canonical_state: bool = False
    rd_workbook_update_allowed: bool = False
    run_queue_root: str = RUN_QUEUE_ROOT
    audit_root: str = AUDIT_ROOT
    run_record_root: str = RUN_RECORD_ROOT
    blocked_effects: tuple[str, ...] = BLOCKED_EFFECTS
    notes: tuple[str, ...] = field(
        default_factory=lambda: (
            "Live runner writes local queue/audit records only for supervised active manifests.",
            "Queued runs remain pending; this runner does not dispatch runtimes or execute workflows.",
        )
    )

    def validate(self) -> None:
        if self.runner_status not in LIVE_RUNNER_STATUSES:
            raise ValueError("invalid live runner status")
        if self.schedule_count != len(self.targets):
            raise ValueError("schedule_count must match targets")
        if self.schedule_ids != tuple(target.schedule_id for target in self.targets):
            raise ValueError("schedule_ids must match target order")
        if self.active_schedule_count != sum(1 for target in self.targets if target.active_supervised):
            raise ValueError("active_schedule_count must match targets")
        if self.due_schedule_count != sum(1 for target in self.targets if target.due_now and target.active_supervised):
            raise ValueError("due_schedule_count must match targets")
        if self.duplicate_count != sum(1 for target in self.targets if target.duplicate and target.due_now):
            raise ValueError("duplicate_count must match due duplicate targets")
        if self.queue_entry_count != len(self.run_queue_entries):
            raise ValueError("queue_entry_count must match entries")
        if self.audit_event_count != len(self.audit_events):
            raise ValueError("audit_event_count must match audit events")
        for target in self.targets:
            target.validate()
        for entry in self.run_queue_entries:
            entry.validate()
        for event in self.audit_events:
            event.validate()
        if self.write_executed and not self.execute_requested:
            raise ValueError("live runner writes require execute_requested")
        if self.write_executed and not self.writes_artifacts:
            raise ValueError("live runner writes must report writes_artifacts")
        if self.write_executed and not (self.run_queue_write_executed and self.audit_event_write_executed):
            raise ValueError("live runner writes must include queue and audit writes")
        if not self.write_executed and (self.run_queue_write_executed or self.audit_event_write_executed):
            raise ValueError("queue/audit write flags require write_executed")
        if self.runner_status == LIVE_RUNNER_STATUS_WRITTEN and not self.write_executed:
            raise ValueError("written status requires writes")
        if self.runner_status == LIVE_RUNNER_STATUS_READY and (self.write_executed or self.execute_requested):
            raise ValueError("ready status is dry-run only")
        if self.runner_status == LIVE_RUNNER_STATUS_DUPLICATE and self.queue_entry_count:
            raise ValueError("duplicate status cannot include new queue entries")
        if self.runner_status == LIVE_RUNNER_STATUS_BLOCKED_INACTIVE and self.active_schedule_count:
            raise ValueError("inactive-blocked status cannot have active schedules")
        if self.runner_status == LIVE_RUNNER_STATUS_BLOCKED_NOT_DUE and self.due_schedule_count:
            raise ValueError("not-due status cannot have due schedules")
        if (
            self.schedule_daemon_started
            or self.schedule_manifest_write_executed
            or self.schedule_activation_executed
            or self.agent_bus_task_write_allowed
            or self.runtime_dispatch_allowed
            or self.workflow_execution_allowed
            or self.approval_granted
            or self.provider_or_connector_call_allowed
            or self.external_scheduler_install_allowed
            or self.canonical_writeback_allowed
            or self.mutates_canonical_state
            or self.rd_workbook_update_allowed
        ):
            raise ValueError("live runner cannot enable blocked authority")
        allowed_roots = (self.run_queue_root, self.audit_root, self.run_record_root)
        for written in self.writes:
            normalized = written.replace("\\", "/")
            if not any(normalized.startswith(root) for root in allowed_roots):
                raise ValueError("live runner writes escaped allowed Pulse schedule roots")
        if set(self.blocked_effects) != set(BLOCKED_EFFECTS):
            raise ValueError("live runner must declare blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "runner_status": self.runner_status,
            "schedule_ids": list(self.schedule_ids),
            "schedule_count": self.schedule_count,
            "active_schedule_count": self.active_schedule_count,
            "due_schedule_count": self.due_schedule_count,
            "duplicate_count": self.duplicate_count,
            "queue_entry_count": self.queue_entry_count,
            "audit_event_count": self.audit_event_count,
            "execute_requested": self.execute_requested,
            "force_due": self.force_due,
            "write_executed": self.write_executed,
            "targets": [target.to_dict() for target in self.targets],
            "run_queue_entries": [entry.to_dict() for entry in self.run_queue_entries],
            "audit_events": [event.to_dict() for event in self.audit_events],
            "missing_evidence_slots": list(self.missing_evidence_slots),
            "writes": list(self.writes),
            "next_recommended_pass": self.next_recommended_pass,
            "local_only": self.local_only,
            "writes_artifacts": self.writes_artifacts,
            "run_queue_write_executed": self.run_queue_write_executed,
            "audit_event_write_executed": self.audit_event_write_executed,
            "schedule_daemon_started": self.schedule_daemon_started,
            "schedule_manifest_write_executed": self.schedule_manifest_write_executed,
            "schedule_activation_executed": self.schedule_activation_executed,
            "agent_bus_task_write_allowed": self.agent_bus_task_write_allowed,
            "runtime_dispatch_allowed": self.runtime_dispatch_allowed,
            "workflow_execution_allowed": self.workflow_execution_allowed,
            "approval_granted": self.approval_granted,
            "provider_or_connector_call_allowed": self.provider_or_connector_call_allowed,
            "external_scheduler_install_allowed": self.external_scheduler_install_allowed,
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "mutates_canonical_state": self.mutates_canonical_state,
            "rd_workbook_update_allowed": self.rd_workbook_update_allowed,
            "run_queue_root": self.run_queue_root,
            "audit_root": self.audit_root,
            "run_record_root": self.run_record_root,
            "blocked_effects": list(self.blocked_effects),
            "notes": list(self.notes),
        }


def _target_from_manifest(
    vault: Path,
    schedule_id: str,
    *,
    generated_at: str,
    force_due: bool,
    existing_keys: set[str],
) -> PulseNativeScheduleLiveRunnerTarget:
    path = _manifest_path(vault, schedule_id)
    rel_path = path.relative_to(vault).as_posix()
    manifest = _read_yaml(path)
    execution = manifest.get("execution") or {}
    delivery = manifest.get("delivery") or {}
    deck = manifest.get("deck") or {}
    source_policy = manifest.get("source_policy") or {}
    cadence = manifest.get("cadence") or {}
    audit_identity = manifest.get("audit_identity") or {}
    activation = manifest.get("activation_execution") or {}
    manifest_schedule_id = str(manifest.get("schedule_id") or "")
    if manifest_schedule_id != schedule_id:
        raise ValueError(f"manifest schedule_id mismatch for {schedule_id}")

    timezone_name = str(cadence.get("timezone") or "UTC")
    local_time = str(cadence.get("local_time") or "00:00").strip('"')
    due_date, due_at_local, clock_due = _due_values(
        generated_at=generated_at,
        timezone_name=timezone_name,
        local_time=local_time,
    )
    refs = _evidence_refs_from_manifest(manifest)
    missing = _missing_evidence(refs)
    status = str(manifest.get("status") or "")
    enabled = bool(manifest.get("enabled", False))
    activation_state = str(manifest.get("activation_state") or "")
    activation_execution_status = str(activation.get("status") or "")
    active_supervised = (
        status == "active"
        and enabled
        and activation_state == "active_supervised"
        and activation_execution_status == "active_supervised"
        and not missing
    )
    due_now = bool(active_supervised and (force_due or clock_due))
    idempotency_key = f"{schedule_id}:{due_date}:{RUN_REASON_NATIVE_DUE}"
    digest = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()[:12]
    schedule_slug = _slug(schedule_id)
    blockers: list[str] = []
    if status != "active":
        blockers.append("schedule_manifest_not_active")
    if not enabled:
        blockers.append("schedule_manifest_disabled")
    if activation_state != "active_supervised" or activation_execution_status != "active_supervised":
        blockers.append("supervised_activation_missing")
    blockers.extend(f"missing_evidence:{slot}" for slot in missing)
    if active_supervised and not due_now:
        blockers.append("schedule_not_due")
    duplicate = due_now and idempotency_key in existing_keys
    if duplicate:
        blockers.append("idempotency_key_already_queued")

    target = PulseNativeScheduleLiveRunnerTarget(
        schedule_id=schedule_id,
        manifest_path=rel_path,
        manifest_status=status,
        enabled=enabled,
        activation_state=activation_state,
        activation_execution_status=activation_execution_status,
        workflow_id=str(execution.get("workflow_id") or ""),
        audience=str(deck.get("audience") or ""),
        output_root=str(delivery.get("output_root") or ""),
        executor_adapter=str(execution.get("executor_adapter") or ""),
        schedule_owner=str(execution.get("schedule_owner") or ""),
        executor_is_adapter_only=bool(audit_identity.get("executor_is_adapter_only", False)),
        timezone=timezone_name,
        cadence_type=str(cadence.get("type") or ""),
        local_time=local_time,
        due_date=due_date,
        due_at_local=due_at_local,
        due_now=due_now,
        forced_due=force_due,
        active_supervised=active_supervised,
        duplicate=duplicate,
        idempotency_key=idempotency_key,
        queue_entry_id=f"pulse_run_queue_{due_date}_{schedule_slug}_{digest}",
        audit_event_id=f"pulse_schedule_audit_{due_date}_{schedule_slug}_{digest}",
        missing_evidence_slots=missing,
        blockers=tuple(blockers),
        external_connectors_enabled=bool(source_policy.get("external_connectors_enabled", False)),
        unrestricted_browsing_enabled=bool(source_policy.get("unrestricted_browsing_enabled", False)),
        canonical_writeback_enabled=bool(deck.get("canonical_writeback_enabled", False)),
        openclaw_cron_owner=bool(execution.get("openclaw_cron_owner", False)),
        windows_task_scheduler_owner=bool(execution.get("windows_task_scheduler_owner", False)),
    )
    target.validate()
    return target


def _entry_and_event(
    target: PulseNativeScheduleLiveRunnerTarget,
    *,
    generated_at: str,
    evidence_refs: dict[str, str | None],
    audit_written: bool,
) -> tuple[PulseNativeScheduleLiveQueueEntry, PulseNativeScheduleLiveAuditEvent]:
    entry = PulseNativeScheduleLiveQueueEntry(
        queue_entry_id=target.queue_entry_id,
        schedule_id=target.schedule_id,
        workflow_id=target.workflow_id,
        audience=target.audience,
        output_root=target.output_root,
        run_reason=RUN_REASON_NATIVE_DUE,
        queue_status=QUEUE_STATUS_PENDING,
        requested_at=generated_at,
        due_date=target.due_date,
        due_at_local=target.due_at_local,
        executor_adapter=target.executor_adapter,
        schedule_owner=target.schedule_owner,
        trigger_source=TRIGGER_SOURCE,
        approval_ref=str(evidence_refs["operator_approval_ref"]),
        permission_envelope_ref=str(evidence_refs["permission_envelope_ref"]),
        audit_identity_ref=str(evidence_refs["audit_identity_ref"]),
        run_queue_scope_ref=str(evidence_refs["run_queue_scope_ref"]),
        runtime_adapter_scope_ref=str(evidence_refs["runtime_adapter_scope_ref"]),
        rollback_plan_ref=str(evidence_refs["rollback_plan_ref"]),
        external_scheduler_denial_ref=str(evidence_refs["external_scheduler_denial_ref"]),
        canonical_writeback_denial_ref=str(evidence_refs["canonical_writeback_denial_ref"]),
        idempotency_key=target.idempotency_key,
    )
    event = PulseNativeScheduleLiveAuditEvent(
        event_id=target.audit_event_id,
        event_type=AUDIT_EVENT_TYPE,
        queue_entry_id=target.queue_entry_id,
        schedule_id=target.schedule_id,
        generated_at=generated_at,
        trigger_source=TRIGGER_SOURCE,
        schedule_owner=target.schedule_owner,
        executor_is_adapter_only=target.executor_is_adapter_only,
        audit_identity_ref=str(evidence_refs["audit_identity_ref"]),
        run_queue_scope_ref=str(evidence_refs["run_queue_scope_ref"]),
        rollback_plan_ref=str(evidence_refs["rollback_plan_ref"]),
        external_scheduler_denial_ref=str(evidence_refs["external_scheduler_denial_ref"]),
        canonical_writeback_denial_ref=str(evidence_refs["canonical_writeback_denial_ref"]),
        real_audit_event_written=audit_written,
    )
    entry.validate()
    event.validate()
    return entry, event


def _build_model(
    *,
    generated_at: str,
    schedule_ids: tuple[str, ...],
    targets: tuple[PulseNativeScheduleLiveRunnerTarget, ...],
    entries: tuple[PulseNativeScheduleLiveQueueEntry, ...],
    events: tuple[PulseNativeScheduleLiveAuditEvent, ...],
    execute_requested: bool,
    force_due: bool,
    write_executed: bool,
    writes: tuple[str, ...] = (),
) -> PulseNativeScheduleLiveRunner:
    active_count = sum(1 for target in targets if target.active_supervised)
    due_count = sum(1 for target in targets if target.active_supervised and target.due_now)
    duplicate_count = sum(1 for target in targets if target.due_now and target.duplicate)
    missing = tuple(sorted({slot for target in targets for slot in target.missing_evidence_slots}))
    if write_executed:
        status = LIVE_RUNNER_STATUS_WRITTEN
    elif active_count == 0:
        status = LIVE_RUNNER_STATUS_BLOCKED_INACTIVE
    elif due_count == 0:
        status = LIVE_RUNNER_STATUS_BLOCKED_NOT_DUE
    elif duplicate_count == due_count:
        status = LIVE_RUNNER_STATUS_DUPLICATE
    else:
        status = LIVE_RUNNER_STATUS_READY
    model = PulseNativeScheduleLiveRunner(
        generated_at=generated_at,
        runner_status=status,
        schedule_ids=schedule_ids,
        schedule_count=len(schedule_ids),
        active_schedule_count=active_count,
        due_schedule_count=due_count,
        duplicate_count=duplicate_count,
        queue_entry_count=len(entries),
        audit_event_count=len(events),
        execute_requested=execute_requested,
        force_due=force_due,
        write_executed=write_executed,
        targets=targets,
        run_queue_entries=entries,
        audit_events=events,
        missing_evidence_slots=missing,
        writes=writes,
        writes_artifacts=write_executed,
        run_queue_write_executed=write_executed,
        audit_event_write_executed=write_executed,
    )
    model.validate()
    return model


def build_pulse_native_schedule_live_runner(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    schedule_ids: tuple[str, ...] | None = None,
    force_due: bool = False,
) -> PulseNativeScheduleLiveRunner:
    """Build a dry-run live schedule runner decision without writing records."""

    vault = _vault_path(vault_root)
    generated = generated_at or now_utc()
    ids = _normalize_schedule_ids(schedule_ids)
    queue_file = vault / RUN_QUEUE_ROOT / RUN_QUEUE_FILENAME
    existing_keys = _existing_idempotency_keys(queue_file)
    targets = tuple(
        _target_from_manifest(
            vault,
            schedule_id,
            generated_at=generated,
            force_due=force_due,
            existing_keys=existing_keys,
        )
        for schedule_id in ids
    )
    entries_and_events = tuple(
        _entry_and_event(
            target,
            generated_at=generated,
            evidence_refs=_evidence_refs_from_manifest(_read_yaml(vault / target.manifest_path)),
            audit_written=False,
        )
        for target in targets
        if target.active_supervised and target.due_now and not target.duplicate
    )
    entries = tuple(item[0] for item in entries_and_events)
    events = tuple(item[1] for item in entries_and_events)
    return _build_model(
        generated_at=generated,
        schedule_ids=ids,
        targets=targets,
        entries=entries,
        events=events,
        execute_requested=False,
        force_due=force_due,
        write_executed=False,
    )


def write_pulse_native_schedule_live_runner_records(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    schedule_ids: tuple[str, ...] | None = None,
    force_due: bool = False,
    execute: bool = False,
    output_path: str | Path | None = None,
) -> PulseNativeScheduleLiveRunner:
    """Optionally write live local queue/audit records for due supervised schedules."""

    vault = _vault_path(vault_root)
    generated = generated_at or now_utc()
    base = build_pulse_native_schedule_live_runner(
        vault,
        generated_at=generated,
        schedule_ids=schedule_ids,
        force_due=force_due,
    )
    if not execute or not base.run_queue_entries:
        return PulseNativeScheduleLiveRunner(
            generated_at=base.generated_at,
            runner_status=base.runner_status,
            schedule_ids=base.schedule_ids,
            schedule_count=base.schedule_count,
            active_schedule_count=base.active_schedule_count,
            due_schedule_count=base.due_schedule_count,
            duplicate_count=base.duplicate_count,
            queue_entry_count=base.queue_entry_count,
            audit_event_count=base.audit_event_count,
            execute_requested=execute,
            force_due=base.force_due,
            write_executed=False,
            targets=base.targets,
            run_queue_entries=base.run_queue_entries,
            audit_events=base.audit_events,
            missing_evidence_slots=base.missing_evidence_slots,
        )

    run_queue_file = (vault / RUN_QUEUE_ROOT / RUN_QUEUE_FILENAME).resolve()
    audit_file = (vault / AUDIT_ROOT / f"{_date_slug(generated)}-native-schedule-audit.jsonl").resolve()
    if output_path is None:
        digest = _sha256("-".join(entry.idempotency_key for entry in base.run_queue_entries))[:12]
        run_record_file = (vault / RUN_RECORD_ROOT / f"{_date_slug(generated)}-live-runner-{digest}.json").resolve()
    else:
        run_record_file = Path(output_path)
        if not run_record_file.is_absolute():
            run_record_file = vault / run_record_file
        run_record_file = run_record_file.resolve()
    allowed_run_record = (vault / RUN_RECORD_ROOT).resolve()
    try:
        run_record_file.relative_to(allowed_run_record)
    except ValueError as exc:
        raise ValueError(
            "native schedule live runner record must be written under 07_LOGS/Pulse-Decks/native-schedule-runs/"
        ) from exc

    run_queue_file.parent.mkdir(parents=True, exist_ok=True)
    audit_file.parent.mkdir(parents=True, exist_ok=True)
    run_record_file.parent.mkdir(parents=True, exist_ok=True)

    audit_events = tuple(
        _entry_and_event(
            target,
            generated_at=generated,
            evidence_refs=_evidence_refs_from_manifest(_read_yaml(vault / target.manifest_path)),
            audit_written=True,
        )[1]
        for target in base.targets
        if target.active_supervised and target.due_now and not target.duplicate
    )
    queue_text = "".join(json.dumps(entry.to_dict(), sort_keys=True) + "\n" for entry in base.run_queue_entries)
    audit_text = "".join(json.dumps(event.to_dict(), sort_keys=True) + "\n" for event in audit_events)
    with run_queue_file.open("a", encoding="utf-8") as handle:
        handle.write(queue_text)
    with audit_file.open("a", encoding="utf-8") as handle:
        handle.write(audit_text)

    writes = (
        run_queue_file.relative_to(vault).as_posix(),
        audit_file.relative_to(vault).as_posix(),
        run_record_file.relative_to(vault).as_posix(),
    )
    model = _build_model(
        generated_at=base.generated_at,
        schedule_ids=base.schedule_ids,
        targets=base.targets,
        entries=base.run_queue_entries,
        events=audit_events,
        execute_requested=True,
        force_due=base.force_due,
        write_executed=True,
        writes=writes,
    )
    run_record_file.write_text(json.dumps(model.to_dict(), indent=2), encoding="utf-8")
    return model
