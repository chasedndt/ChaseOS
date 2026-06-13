"""Proof-only runtime dispatch layer for Pulse native schedule queue records.

This module sits after the live schedule queue/audit runner. It inspects queued
native schedule records and builds bounded dispatch packets, but it never starts
a daemon, dispatches a runtime, executes a workflow, calls providers/connectors,
updates queue state, or mutates canonical ChaseOS state.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.card_schema import now_utc
from runtime.pulse.native_schedule_activation_gate import REQUIRED_EVIDENCE_SLOTS
from runtime.pulse.native_schedule_live_runner import (
    QUEUE_STATUS_PENDING,
    RUN_QUEUE_FILENAME,
    RUN_QUEUE_ROOT,
    RUN_REASON_NATIVE_DUE,
    TRIGGER_SOURCE,
)
from runtime.pulse.native_schedule_runner_proof import MANIFEST_DIR, _read_yaml


DISPATCH_STATUS_BLOCKED_NO_QUEUE = "blocked_no_queued_native_schedule_runs"
DISPATCH_STATUS_BLOCKED_NOT_READY = "blocked_pending_runs_not_dispatch_ready"
DISPATCH_STATUS_READY = "runtime_dispatch_proof_ready"
DISPATCH_STATUS_WRITTEN = "runtime_dispatch_proof_written"
DISPATCH_STATUSES = {
    DISPATCH_STATUS_BLOCKED_NO_QUEUE,
    DISPATCH_STATUS_BLOCKED_NOT_READY,
    DISPATCH_STATUS_READY,
    DISPATCH_STATUS_WRITTEN,
}

DISPATCH_PACKET_STATUS_PROOF_ONLY = "proof_only_not_dispatched"
DISPATCH_EVENT_TYPE = "pulse_native_schedule_runtime_dispatch_proof"
WORKFLOW_REGISTRY_ROOT = "runtime/workflows/registry/"
ALLOWED_WRITE_ROOT = "07_LOGS/Pulse-Decks/native-schedule-runtime-dispatch-proof/"
NEXT_RECOMMENDED_PASS = "chaseos-pulse-workflow-execution-proof"

BLOCKED_EFFECTS = (
    "agent_bus_task_write",
    "approval_grant",
    "canonical_writeback",
    "external_scheduler_install",
    "provider_or_connector_call",
    "run_queue_status_mutation",
    "runtime_dispatch_execution",
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


def _normalize_schedule_ids(schedule_ids: tuple[str, ...] | None) -> tuple[str, ...] | None:
    if schedule_ids is None:
        return None
    ids = tuple(item.strip() for item in schedule_ids if item.strip())
    if not ids:
        raise ValueError("at least one schedule_id is required when filtering")
    return ids


def _safe_leaf(value: str, *, label: str) -> str:
    if not value or "/" in value or "\\" in value or ".." in value:
        raise ValueError(f"invalid {label} path segment")
    return value


def _manifest_path(vault: Path, schedule_id: str) -> Path:
    schedule = _safe_leaf(schedule_id, label="schedule_id")
    path = (vault / MANIFEST_DIR / f"{schedule}.yaml").resolve()
    allowed_root = (vault / MANIFEST_DIR).resolve()
    try:
        path.relative_to(allowed_root)
    except ValueError as exc:
        raise ValueError("schedule manifest path must stay under runtime/schedules/manifests/") from exc
    return path


def _workflow_registry_path(vault: Path, workflow_id: str) -> Path:
    workflow = _safe_leaf(workflow_id, label="workflow_id")
    path = (vault / WORKFLOW_REGISTRY_ROOT / f"{workflow}.yaml").resolve()
    allowed_root = (vault / WORKFLOW_REGISTRY_ROOT).resolve()
    try:
        path.relative_to(allowed_root)
    except ValueError as exc:
        raise ValueError("workflow registry path must stay under runtime/workflows/registry/") from exc
    return path


def _evidence_refs_from_queue(entry: dict[str, Any]) -> dict[str, str | None]:
    return {
        "operator_approval_ref": entry.get("approval_ref"),
        "permission_envelope_ref": entry.get("permission_envelope_ref"),
        "run_queue_scope_ref": entry.get("run_queue_scope_ref"),
        "audit_identity_ref": entry.get("audit_identity_ref"),
        "runtime_adapter_scope_ref": entry.get("runtime_adapter_scope_ref"),
        "rollback_plan_ref": entry.get("rollback_plan_ref"),
        "external_scheduler_denial_ref": entry.get("external_scheduler_denial_ref"),
        "canonical_writeback_denial_ref": entry.get("canonical_writeback_denial_ref"),
    }


def _missing_evidence_slots(entry: dict[str, Any]) -> tuple[str, ...]:
    refs = _evidence_refs_from_queue(entry)
    return tuple(slot for slot in REQUIRED_EVIDENCE_SLOTS if not _real_ref(refs.get(slot)))


def _load_queue_entries(
    vault: Path,
    *,
    schedule_ids: tuple[str, ...] | None,
) -> tuple[bool, tuple[dict[str, Any], ...], tuple[str, ...]]:
    queue_file = vault / RUN_QUEUE_ROOT / RUN_QUEUE_FILENAME
    if not queue_file.exists():
        return False, (), ()
    selected = set(schedule_ids or ())
    entries: list[dict[str, Any]] = []
    invalid: list[str] = []
    for line_number, raw in enumerate(queue_file.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            invalid.append(f"line_{line_number}:invalid_json")
            continue
        schedule_id = str(payload.get("schedule_id") or "")
        if selected and schedule_id not in selected:
            continue
        entries.append(payload)
    return True, tuple(entries), tuple(invalid)


def _manifest_state(vault: Path, schedule_id: str) -> tuple[str, bool, str, bool, str, str, str]:
    path = _manifest_path(vault, schedule_id)
    if not path.exists():
        return path.relative_to(vault).as_posix(), False, "", False, "", "", ""
    manifest = _read_yaml(path)
    execution = manifest.get("execution") or {}
    activation = manifest.get("activation_execution") or {}
    status = str(manifest.get("status") or "")
    enabled = bool(manifest.get("enabled", False))
    activation_state = str(manifest.get("activation_state") or "")
    activation_status = str(activation.get("status") or "")
    runtime_target = str(execution.get("runtime_target") or execution.get("runtime_owner") or "chaseos")
    active = (
        status == "active"
        and enabled
        and activation_state == "active_supervised"
        and activation_status == "active_supervised"
    )
    return path.relative_to(vault).as_posix(), active, status, enabled, activation_state, activation_status, runtime_target


def _workflow_state(vault: Path, workflow_id: str) -> tuple[str, bool, str]:
    path = _workflow_registry_path(vault, workflow_id)
    if not path.exists():
        return path.relative_to(vault).as_posix(), False, ""
    workflow = _read_yaml(path)
    return path.relative_to(vault).as_posix(), True, str(workflow.get("status") or "")


@dataclass(frozen=True)
class PulseNativeScheduleRuntimeDispatchTarget:
    dispatch_packet_id: str
    queue_entry_id: str
    schedule_id: str
    workflow_id: str
    workflow_registry_path: str
    workflow_registry_present: bool
    workflow_registry_status: str
    manifest_path: str
    manifest_active_supervised: bool
    manifest_status: str
    manifest_enabled: bool
    activation_state: str
    activation_execution_status: str
    runtime_target: str
    executor_adapter: str
    audience: str
    output_root: str
    requested_at: str
    due_date: str
    due_at_local: str
    idempotency_key: str
    dispatch_status: str
    command_preview: str
    missing_evidence_slots: tuple[str, ...]
    blockers: tuple[str, ...]
    queue_runtime_dispatch_allowed: bool = False
    queue_workflow_execution_allowed: bool = False
    queue_canonical_writeback_allowed: bool = False
    dispatch_ready: bool = False
    runtime_dispatch_allowed: bool = False
    workflow_execution_allowed: bool = False
    runtime_dispatch_started: bool = False
    workflow_execution_started: bool = False
    provider_or_connector_call_started: bool = False
    canonical_writeback_started: bool = False

    def validate(self) -> None:
        if not self.dispatch_packet_id or not self.queue_entry_id or not self.schedule_id:
            raise ValueError("dispatch target requires ids")
        if not self.workflow_id or not self.command_preview:
            raise ValueError("dispatch target requires workflow id and command preview")
        if self.dispatch_status != DISPATCH_PACKET_STATUS_PROOF_ONLY:
            raise ValueError("dispatch target must remain proof-only")
        if self.dispatch_ready and self.blockers:
            raise ValueError("ready dispatch target cannot report blockers")
        if not self.dispatch_ready and not self.blockers:
            raise ValueError("blocked dispatch target must report blockers")
        if self.dispatch_ready and not (
            self.manifest_active_supervised
            and self.workflow_registry_present
            and self.workflow_registry_status == "active"
            and not self.missing_evidence_slots
        ):
            raise ValueError("dispatch_ready must reflect manifest, workflow, and evidence state")
        if (
            self.queue_runtime_dispatch_allowed
            or self.queue_workflow_execution_allowed
            or self.queue_canonical_writeback_allowed
            or self.runtime_dispatch_allowed
            or self.workflow_execution_allowed
            or self.runtime_dispatch_started
            or self.workflow_execution_started
            or self.provider_or_connector_call_started
            or self.canonical_writeback_started
        ):
            raise ValueError("dispatch proof cannot grant or start execution/writeback authority")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class PulseNativeScheduleRuntimeDispatchProofEvent:
    event_id: str
    event_type: str
    dispatch_packet_id: str
    queue_entry_id: str
    schedule_id: str
    workflow_id: str
    generated_at: str
    trigger_source: str
    dispatch_status: str
    runtime_target: str
    proof_artifact_written: bool
    runtime_dispatch_started: bool = False
    workflow_execution_started: bool = False
    run_queue_status_mutated: bool = False
    provider_or_connector_call_started: bool = False
    canonical_writeback_started: bool = False

    def validate(self) -> None:
        if not self.event_id or not self.dispatch_packet_id or not self.queue_entry_id:
            raise ValueError("dispatch proof event requires ids")
        if self.event_type != DISPATCH_EVENT_TYPE or self.trigger_source != TRIGGER_SOURCE:
            raise ValueError("dispatch proof event has invalid type or trigger")
        if self.dispatch_status != DISPATCH_PACKET_STATUS_PROOF_ONLY:
            raise ValueError("dispatch proof event must remain proof-only")
        if (
            self.runtime_dispatch_started
            or self.workflow_execution_started
            or self.run_queue_status_mutated
            or self.provider_or_connector_call_started
            or self.canonical_writeback_started
        ):
            raise ValueError("dispatch proof event cannot record blocked side effects as started")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class PulseNativeScheduleRuntimeDispatchProof:
    generated_at: str
    dispatch_status: str
    queue_file_path: str
    queue_file_exists: bool
    queue_entry_count: int
    pending_entry_count: int
    invalid_queue_line_count: int
    invalid_queue_lines: tuple[str, ...]
    dispatch_target_count: int
    ready_dispatch_target_count: int
    blocked_dispatch_target_count: int
    missing_workflow_count: int
    write_requested: bool
    write_executed: bool
    dispatch_targets: tuple[PulseNativeScheduleRuntimeDispatchTarget, ...]
    proof_events: tuple[PulseNativeScheduleRuntimeDispatchProofEvent, ...]
    writes: tuple[str, ...] = ()
    next_recommended_pass: str = NEXT_RECOMMENDED_PASS
    local_only: bool = True
    read_only: bool = True
    writes_artifacts: bool = False
    proof_artifact_write_executed: bool = False
    execute_dispatch_action_exposed: bool = False
    schedule_daemon_started: bool = False
    run_queue_status_write_executed: bool = False
    runtime_dispatch_allowed: bool = False
    runtime_dispatch_started: bool = False
    workflow_execution_allowed: bool = False
    workflow_execution_started: bool = False
    agent_bus_task_write_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    external_scheduler_install_allowed: bool = False
    approval_granted: bool = False
    canonical_writeback_allowed: bool = False
    mutates_canonical_state: bool = False
    rd_workbook_update_allowed: bool = False
    allowed_write_root: str = ALLOWED_WRITE_ROOT
    blocked_effects: tuple[str, ...] = BLOCKED_EFFECTS
    notes: tuple[str, ...] = field(
        default_factory=lambda: (
            "This is a runtime dispatch proof packet over queued native schedule records.",
            "It does not dispatch runtimes, execute workflows, or mutate run queue status.",
        )
    )

    def validate(self) -> None:
        if self.dispatch_status not in DISPATCH_STATUSES:
            raise ValueError("invalid runtime dispatch proof status")
        if self.invalid_queue_line_count != len(self.invalid_queue_lines):
            raise ValueError("invalid queue line count must match invalid queue lines")
        if self.dispatch_target_count != len(self.dispatch_targets):
            raise ValueError("dispatch_target_count must match targets")
        if self.ready_dispatch_target_count != sum(1 for target in self.dispatch_targets if target.dispatch_ready):
            raise ValueError("ready_dispatch_target_count must match targets")
        if self.blocked_dispatch_target_count != sum(1 for target in self.dispatch_targets if not target.dispatch_ready):
            raise ValueError("blocked_dispatch_target_count must match targets")
        if self.missing_workflow_count != sum(1 for target in self.dispatch_targets if not target.workflow_registry_present):
            raise ValueError("missing_workflow_count must match targets")
        if self.pending_entry_count > self.queue_entry_count:
            raise ValueError("pending_entry_count cannot exceed queue_entry_count")
        for target in self.dispatch_targets:
            target.validate()
        for event in self.proof_events:
            event.validate()
        if self.write_executed and not self.write_requested:
            raise ValueError("write_executed requires write_requested")
        if self.write_executed and self.read_only:
            raise ValueError("written dispatch proof cannot be read_only")
        if self.write_executed != self.proof_artifact_write_executed:
            raise ValueError("proof artifact write flag must match write_executed")
        if self.write_executed and not self.writes_artifacts:
            raise ValueError("written dispatch proof must report writes_artifacts")
        if self.dispatch_status == DISPATCH_STATUS_BLOCKED_NO_QUEUE and self.pending_entry_count:
            raise ValueError("no-queue status cannot have pending entries")
        if self.dispatch_status == DISPATCH_STATUS_BLOCKED_NOT_READY and self.ready_dispatch_target_count:
            raise ValueError("not-ready status cannot have ready targets")
        if self.dispatch_status in {DISPATCH_STATUS_READY, DISPATCH_STATUS_WRITTEN} and not self.ready_dispatch_target_count:
            raise ValueError("ready/written status requires at least one ready target")
        if self.dispatch_status == DISPATCH_STATUS_WRITTEN and not self.write_executed:
            raise ValueError("written status requires write_executed")
        if self.dispatch_status == DISPATCH_STATUS_READY and self.write_executed:
            raise ValueError("ready status is dry-run only")
        if (
            self.execute_dispatch_action_exposed
            or self.schedule_daemon_started
            or self.run_queue_status_write_executed
            or self.runtime_dispatch_allowed
            or self.runtime_dispatch_started
            or self.workflow_execution_allowed
            or self.workflow_execution_started
            or self.agent_bus_task_write_allowed
            or self.provider_or_connector_call_allowed
            or self.external_scheduler_install_allowed
            or self.approval_granted
            or self.canonical_writeback_allowed
            or self.mutates_canonical_state
            or self.rd_workbook_update_allowed
        ):
            raise ValueError("runtime dispatch proof cannot enable blocked authority")
        for written in self.writes:
            if not written.replace("\\", "/").startswith(self.allowed_write_root):
                raise ValueError("runtime dispatch proof writes escaped allowed Pulse root")
        if set(self.blocked_effects) != set(BLOCKED_EFFECTS):
            raise ValueError("runtime dispatch proof must declare blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "dispatch_status": self.dispatch_status,
            "queue_file_path": self.queue_file_path,
            "queue_file_exists": self.queue_file_exists,
            "queue_entry_count": self.queue_entry_count,
            "pending_entry_count": self.pending_entry_count,
            "invalid_queue_line_count": self.invalid_queue_line_count,
            "invalid_queue_lines": list(self.invalid_queue_lines),
            "dispatch_target_count": self.dispatch_target_count,
            "ready_dispatch_target_count": self.ready_dispatch_target_count,
            "blocked_dispatch_target_count": self.blocked_dispatch_target_count,
            "missing_workflow_count": self.missing_workflow_count,
            "write_requested": self.write_requested,
            "write_executed": self.write_executed,
            "dispatch_targets": [target.to_dict() for target in self.dispatch_targets],
            "proof_events": [event.to_dict() for event in self.proof_events],
            "writes": list(self.writes),
            "next_recommended_pass": self.next_recommended_pass,
            "local_only": self.local_only,
            "read_only": self.read_only,
            "writes_artifacts": self.writes_artifacts,
            "proof_artifact_write_executed": self.proof_artifact_write_executed,
            "execute_dispatch_action_exposed": self.execute_dispatch_action_exposed,
            "schedule_daemon_started": self.schedule_daemon_started,
            "run_queue_status_write_executed": self.run_queue_status_write_executed,
            "runtime_dispatch_allowed": self.runtime_dispatch_allowed,
            "runtime_dispatch_started": self.runtime_dispatch_started,
            "workflow_execution_allowed": self.workflow_execution_allowed,
            "workflow_execution_started": self.workflow_execution_started,
            "agent_bus_task_write_allowed": self.agent_bus_task_write_allowed,
            "provider_or_connector_call_allowed": self.provider_or_connector_call_allowed,
            "external_scheduler_install_allowed": self.external_scheduler_install_allowed,
            "approval_granted": self.approval_granted,
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "mutates_canonical_state": self.mutates_canonical_state,
            "rd_workbook_update_allowed": self.rd_workbook_update_allowed,
            "allowed_write_root": self.allowed_write_root,
            "blocked_effects": list(self.blocked_effects),
            "notes": list(self.notes),
        }


def _target_from_queue_entry(vault: Path, entry: dict[str, Any]) -> PulseNativeScheduleRuntimeDispatchTarget:
    schedule_id = str(entry.get("schedule_id") or "")
    workflow_id = str(entry.get("workflow_id") or "")
    manifest_path, manifest_active, manifest_status, manifest_enabled, activation_state, activation_status, runtime_target = (
        _manifest_state(vault, schedule_id)
    )
    workflow_path, workflow_present, workflow_status = _workflow_state(vault, workflow_id)
    missing_evidence = _missing_evidence_slots(entry)
    blockers: list[str] = []
    if entry.get("queue_status") != QUEUE_STATUS_PENDING:
        blockers.append("queue_entry_not_pending_runtime_dispatch")
    if entry.get("run_reason") != RUN_REASON_NATIVE_DUE:
        blockers.append("queue_entry_not_native_schedule_due")
    if entry.get("schedule_owner") != "chaseos":
        blockers.append("queue_entry_schedule_owner_not_chaseos")
    if entry.get("trigger_source") != TRIGGER_SOURCE:
        blockers.append("queue_entry_trigger_source_not_native_schedule")
    if entry.get("runtime_dispatch_allowed"):
        blockers.append("queue_entry_runtime_dispatch_already_allowed")
    if entry.get("workflow_execution_allowed"):
        blockers.append("queue_entry_workflow_execution_already_allowed")
    if entry.get("canonical_writeback_allowed"):
        blockers.append("queue_entry_canonical_writeback_already_allowed")
    if not manifest_active:
        blockers.append("schedule_manifest_not_active_supervised")
    if not workflow_present:
        blockers.append("workflow_registry_missing")
    elif workflow_status != "active":
        blockers.append("workflow_registry_not_active")
    blockers.extend(f"missing_evidence:{slot}" for slot in missing_evidence)

    dispatch_key = f"{entry.get('queue_entry_id')}:{workflow_id}:runtime_dispatch_proof"
    packet_id = f"pulse_runtime_dispatch_proof_{_sha256(dispatch_key)[:16]}"
    target = PulseNativeScheduleRuntimeDispatchTarget(
        dispatch_packet_id=packet_id,
        queue_entry_id=str(entry.get("queue_entry_id") or ""),
        schedule_id=schedule_id,
        workflow_id=workflow_id,
        workflow_registry_path=workflow_path,
        workflow_registry_present=workflow_present,
        workflow_registry_status=workflow_status,
        manifest_path=manifest_path,
        manifest_active_supervised=manifest_active,
        manifest_status=manifest_status,
        manifest_enabled=manifest_enabled,
        activation_state=activation_state,
        activation_execution_status=activation_status,
        runtime_target=runtime_target,
        executor_adapter=str(entry.get("executor_adapter") or ""),
        audience=str(entry.get("audience") or ""),
        output_root=str(entry.get("output_root") or ""),
        requested_at=str(entry.get("requested_at") or ""),
        due_date=str(entry.get("due_date") or ""),
        due_at_local=str(entry.get("due_at_local") or ""),
        idempotency_key=str(entry.get("idempotency_key") or ""),
        dispatch_status=DISPATCH_PACKET_STATUS_PROOF_ONLY,
        command_preview=f"chaseos run {workflow_id}",
        missing_evidence_slots=missing_evidence,
        blockers=tuple(blockers),
        queue_runtime_dispatch_allowed=bool(entry.get("runtime_dispatch_allowed")),
        queue_workflow_execution_allowed=bool(entry.get("workflow_execution_allowed")),
        queue_canonical_writeback_allowed=bool(entry.get("canonical_writeback_allowed")),
        dispatch_ready=not blockers,
    )
    target.validate()
    return target


def _event_from_target(
    target: PulseNativeScheduleRuntimeDispatchTarget,
    *,
    generated_at: str,
    proof_written: bool,
) -> PulseNativeScheduleRuntimeDispatchProofEvent:
    event = PulseNativeScheduleRuntimeDispatchProofEvent(
        event_id=f"pulse_runtime_dispatch_event_{_sha256(target.dispatch_packet_id)[:16]}",
        event_type=DISPATCH_EVENT_TYPE,
        dispatch_packet_id=target.dispatch_packet_id,
        queue_entry_id=target.queue_entry_id,
        schedule_id=target.schedule_id,
        workflow_id=target.workflow_id,
        generated_at=generated_at,
        trigger_source=TRIGGER_SOURCE,
        dispatch_status=DISPATCH_PACKET_STATUS_PROOF_ONLY,
        runtime_target=target.runtime_target,
        proof_artifact_written=proof_written,
    )
    event.validate()
    return event


def _build_model(
    *,
    generated_at: str,
    queue_file_exists: bool,
    queue_entries: tuple[dict[str, Any], ...],
    invalid_queue_lines: tuple[str, ...],
    targets: tuple[PulseNativeScheduleRuntimeDispatchTarget, ...],
    events: tuple[PulseNativeScheduleRuntimeDispatchProofEvent, ...],
    write_requested: bool,
    write_executed: bool,
    writes: tuple[str, ...] = (),
) -> PulseNativeScheduleRuntimeDispatchProof:
    pending_count = sum(1 for entry in queue_entries if entry.get("queue_status") == QUEUE_STATUS_PENDING)
    ready_count = sum(1 for target in targets if target.dispatch_ready)
    if ready_count and write_executed:
        status = DISPATCH_STATUS_WRITTEN
    elif ready_count:
        status = DISPATCH_STATUS_READY
    elif pending_count:
        status = DISPATCH_STATUS_BLOCKED_NOT_READY
    else:
        status = DISPATCH_STATUS_BLOCKED_NO_QUEUE
    model = PulseNativeScheduleRuntimeDispatchProof(
        generated_at=generated_at,
        dispatch_status=status,
        queue_file_path=f"{RUN_QUEUE_ROOT}{RUN_QUEUE_FILENAME}",
        queue_file_exists=queue_file_exists,
        queue_entry_count=len(queue_entries),
        pending_entry_count=pending_count,
        invalid_queue_line_count=len(invalid_queue_lines),
        invalid_queue_lines=invalid_queue_lines,
        dispatch_target_count=len(targets),
        ready_dispatch_target_count=ready_count,
        blocked_dispatch_target_count=sum(1 for target in targets if not target.dispatch_ready),
        missing_workflow_count=sum(1 for target in targets if not target.workflow_registry_present),
        write_requested=write_requested,
        write_executed=write_executed,
        dispatch_targets=targets,
        proof_events=events,
        writes=writes,
        read_only=not write_executed,
        writes_artifacts=write_executed,
        proof_artifact_write_executed=write_executed,
    )
    model.validate()
    return model


def build_pulse_native_schedule_runtime_dispatch_proof(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    schedule_ids: tuple[str, ...] | None = None,
) -> PulseNativeScheduleRuntimeDispatchProof:
    """Build a proof-only runtime dispatch packet over queued Pulse schedule records."""

    vault = _vault_path(vault_root)
    generated = generated_at or now_utc()
    ids = _normalize_schedule_ids(schedule_ids)
    queue_exists, queue_entries, invalid_lines = _load_queue_entries(vault, schedule_ids=ids)
    targets = tuple(_target_from_queue_entry(vault, entry) for entry in queue_entries)
    events = tuple(
        _event_from_target(target, generated_at=generated, proof_written=False)
        for target in targets
        if target.dispatch_ready
    )
    return _build_model(
        generated_at=generated,
        queue_file_exists=queue_exists,
        queue_entries=queue_entries,
        invalid_queue_lines=invalid_lines,
        targets=targets,
        events=events,
        write_requested=False,
        write_executed=False,
    )


def write_pulse_native_schedule_runtime_dispatch_proof(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    schedule_ids: tuple[str, ...] | None = None,
    output_path: str | Path | None = None,
) -> PulseNativeScheduleRuntimeDispatchProof:
    """Write a proof artifact without dispatching runtimes or mutating queue state."""

    vault = _vault_path(vault_root)
    generated = generated_at or now_utc()
    ids = _normalize_schedule_ids(schedule_ids)
    base = build_pulse_native_schedule_runtime_dispatch_proof(
        vault,
        generated_at=generated,
        schedule_ids=ids,
    )
    queue_exists, queue_entries, invalid_lines = _load_queue_entries(vault, schedule_ids=ids)
    if output_path is None:
        digest_source = "-".join(target.dispatch_packet_id for target in base.dispatch_targets) or "no-queue"
        target_path = (
            vault
            / ALLOWED_WRITE_ROOT
            / f"{_date_slug(generated)}-runtime-dispatch-proof-{_sha256(digest_source)[:12]}.json"
        )
    else:
        target_path = Path(output_path)
        if not target_path.is_absolute():
            target_path = vault / target_path
    target_path = target_path.resolve()
    allowed_root = (vault / ALLOWED_WRITE_ROOT).resolve()
    try:
        target_path.relative_to(allowed_root)
    except ValueError as exc:
        raise ValueError(
            "native schedule runtime dispatch proof must be written under "
            "07_LOGS/Pulse-Decks/native-schedule-runtime-dispatch-proof/"
        ) from exc

    rel_path = target_path.relative_to(vault).as_posix()
    events = tuple(
        _event_from_target(target, generated_at=generated, proof_written=True)
        for target in base.dispatch_targets
        if target.dispatch_ready
    )
    model = _build_model(
        generated_at=base.generated_at,
        queue_file_exists=queue_exists,
        queue_entries=queue_entries,
        invalid_queue_lines=invalid_lines,
        targets=base.dispatch_targets,
        events=events,
        write_requested=True,
        write_executed=True,
        writes=(rel_path,),
    )
    model.validate()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(model.to_dict(), indent=2), encoding="utf-8")
    return model
