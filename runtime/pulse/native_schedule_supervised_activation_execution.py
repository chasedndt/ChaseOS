"""Guarded supervised activation execution proof for Pulse native schedules.

This is the last pre-live boundary before a ChaseOS-owned Pulse schedule can be
enabled. The default path is a dry-run. A manifest write is possible only when a
caller supplies every real evidence ref and an explicit execute flag. Even then
this module does not start a schedule daemon, write a real run queue, dispatch a
runtime, execute workflows, call providers/connectors, or mutate canonical
knowledge/project state.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.card_schema import now_utc
from runtime.pulse.native_schedule_activation_gate import (
    BLOCKED_EFFECTS as GATE_BLOCKED_EFFECTS,
    GATE_STATUS_READY,
    REQUIRED_EVIDENCE_SLOTS,
    build_pulse_native_schedule_activation_gate,
)
from runtime.pulse.native_schedule_run_queue_audit_proof import (
    PROOF_STATUS_READY,
    build_pulse_native_schedule_run_queue_audit_proof,
)
from runtime.pulse.native_schedule_runner_proof import DEFAULT_SCHEDULE_IDS, MANIFEST_DIR


EXECUTION_STATUS_BLOCKED_GATE = "blocked_activation_gate_not_ready"
EXECUTION_STATUS_READY = "ready_for_supervised_activation_execution"
EXECUTION_STATUS_EXECUTED = "supervised_activation_execution_recorded"
EXECUTION_STATUSES = {
    EXECUTION_STATUS_BLOCKED_GATE,
    EXECUTION_STATUS_READY,
    EXECUTION_STATUS_EXECUTED,
}

ALLOWED_WRITE_ROOT = "07_LOGS/Pulse-Decks/native-schedule-activation-executions/"
NEXT_RECOMMENDED_PASS = "chaseos-pulse-live-connector-source-scanner-execution-proof"

BLOCKED_EFFECTS = tuple(
    sorted(
        set(GATE_BLOCKED_EFFECTS)
        | {
            "agent_bus_task_write",
            "approval_grant",
            "canonical_writeback",
            "external_scheduler_install",
            "provider_or_connector_call",
            "real_run_queue_write",
            "runtime_dispatch",
            "schedule_daemon_start",
            "workflow_execution",
        }
    )
)


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _date_slug(generated_at: str) -> str:
    date = generated_at[:10]
    return date if len(date) == 10 else now_utc()[:10]


def _slug(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in value).strip("-")


def _normalize_schedule_ids(schedule_ids: tuple[str, ...] | None) -> tuple[str, ...]:
    ids = tuple(item.strip() for item in (schedule_ids or DEFAULT_SCHEDULE_IDS) if item.strip())
    if not ids:
        raise ValueError("at least one schedule_id is required")
    return ids


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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


def _replace_top_level_scalar(text: str, key: str, value: str) -> str:
    lines = text.splitlines()
    replaced = False
    for index, line in enumerate(lines):
        if line.startswith(f"{key}:"):
            lines[index] = f"{key}: {value}"
            replaced = True
            break
    if not replaced:
        lines.append(f"{key}: {value}")
    return "\n".join(lines) + "\n"


def _append_activation_execution_block(
    text: str,
    *,
    generated_at: str,
    evidence_refs: dict[str, str | None],
) -> str:
    marker = "activation_execution:"
    if marker in text:
        text = text.split(marker, 1)[0].rstrip() + "\n"
    block = [
        "",
        "activation_execution:",
        "  status: active_supervised",
        f"  activated_at: {generated_at}",
        "  activated_by_runtime: codex",
        "  activation_mode: supervised_operator_approved",
        "  schedule_owner: chaseos",
        "  executor_role: adapter_only",
        "  external_scheduler_owner: false",
        "  openclaw_cron_owner: false",
        "  windows_task_scheduler_owner: false",
        "  canonical_writeback_enabled: false",
        "  workflow_execution_started: false",
        "  runtime_dispatch_started: false",
        "  agent_bus_task_written: false",
        "  evidence_refs:",
    ]
    for slot in REQUIRED_EVIDENCE_SLOTS:
        block.append(f"    {slot}: {evidence_refs.get(slot)}")
    return text.rstrip() + "\n" + "\n".join(block) + "\n"


@dataclass(frozen=True)
class PulseNativeScheduleManifestPatch:
    schedule_id: str
    manifest_path: str
    before_sha256: str
    after_sha256: str
    status_before: str
    status_after: str
    enabled_before: bool
    enabled_after: bool
    activation_state_before: str
    activation_state_after: str
    external_scheduler_owner: bool = False
    canonical_writeback_enabled: bool = False
    workflow_execution_started: bool = False
    runtime_dispatch_started: bool = False
    agent_bus_task_written: bool = False

    def validate(self) -> None:
        if not self.schedule_id or not self.manifest_path:
            raise ValueError("manifest patch requires schedule_id and path")
        if self.status_after != "active":
            raise ValueError("manifest patch must set active status")
        if self.enabled_after is not True:
            raise ValueError("manifest patch must enable the schedule")
        if self.activation_state_after != "active_supervised":
            raise ValueError("manifest patch must set supervised activation state")
        if (
            self.external_scheduler_owner
            or self.canonical_writeback_enabled
            or self.workflow_execution_started
            or self.runtime_dispatch_started
            or self.agent_bus_task_written
        ):
            raise ValueError("manifest patch cannot enable runtime/canonical/external side effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class PulseNativeScheduleSupervisedActivationExecution:
    generated_at: str
    execution_status: str
    gate_status: str
    run_queue_proof_status: str
    schedule_ids: tuple[str, ...]
    schedule_count: int
    missing_evidence_slots: tuple[str, ...]
    execute_requested: bool
    write_proof_requested: bool
    write_executed: bool = False
    writes: tuple[str, ...] = ()
    manifest_patch_count: int = 0
    manifest_patches: tuple[PulseNativeScheduleManifestPatch, ...] = ()
    next_recommended_pass: str = NEXT_RECOMMENDED_PASS
    local_only: bool = True
    writes_artifacts: bool = False
    schedule_manifest_write_executed: bool = False
    schedule_activation_executed: bool = False
    schedule_daemon_started: bool = False
    real_run_queue_written: bool = False
    real_audit_event_written: bool = False
    agent_bus_task_write_allowed: bool = False
    runtime_dispatch_allowed: bool = False
    workflow_execution_allowed: bool = False
    approval_granted: bool = False
    provider_or_connector_call_allowed: bool = False
    external_scheduler_install_allowed: bool = False
    canonical_writeback_allowed: bool = False
    mutates_canonical_state: bool = False
    rd_workbook_update_allowed: bool = False
    allowed_write_root: str = ALLOWED_WRITE_ROOT
    blocked_effects: tuple[str, ...] = BLOCKED_EFFECTS
    notes: tuple[str, ...] = field(
        default_factory=lambda: (
            "Default invocation is dry-run proof only.",
            "Manifest activation requires all evidence refs plus an explicit execute flag.",
            "Execution does not start schedulers, queue runs, dispatch runtimes, or call providers/connectors.",
        )
    )

    def validate(self) -> None:
        if self.execution_status not in EXECUTION_STATUSES:
            raise ValueError("invalid supervised activation execution status")
        if self.schedule_count != len(self.schedule_ids):
            raise ValueError("schedule_count must match schedule_ids")
        if self.manifest_patch_count != len(self.manifest_patches):
            raise ValueError("manifest_patch_count must match manifest_patches")
        if self.execution_status == EXECUTION_STATUS_BLOCKED_GATE and not self.missing_evidence_slots:
            raise ValueError("blocked execution must report missing evidence")
        if self.execution_status in {EXECUTION_STATUS_READY, EXECUTION_STATUS_EXECUTED} and self.missing_evidence_slots:
            raise ValueError("ready/executed status cannot have missing evidence")
        if self.execution_status == EXECUTION_STATUS_READY and self.execute_requested:
            raise ValueError("ready status without execution requires execute_requested=false")
        if self.execution_status == EXECUTION_STATUS_EXECUTED and not self.execute_requested:
            raise ValueError("executed status requires execute_requested=true")
        if self.execution_status == EXECUTION_STATUS_EXECUTED and not self.schedule_manifest_write_executed:
            raise ValueError("executed status requires manifest writes")
        if self.write_executed and not (self.write_proof_requested or self.execute_requested):
            raise ValueError("write_executed requires write proof or execute request")
        if self.write_executed and not self.writes_artifacts:
            raise ValueError("write_executed must report writes_artifacts")
        for patch in self.manifest_patches:
            patch.validate()
        if self.schedule_manifest_write_executed != bool(self.manifest_patches):
            raise ValueError("manifest write flag must match manifest patches")
        if self.schedule_activation_executed != self.schedule_manifest_write_executed:
            raise ValueError("activation execution flag must match manifest write execution")
        if self.schedule_daemon_started:
            raise ValueError("supervised activation execution cannot start a schedule daemon")
        if self.real_run_queue_written or self.real_audit_event_written:
            raise ValueError("supervised activation execution cannot write real queue/audit events")
        if self.agent_bus_task_write_allowed:
            raise ValueError("supervised activation execution cannot write Agent Bus tasks")
        if self.runtime_dispatch_allowed or self.workflow_execution_allowed:
            raise ValueError("supervised activation execution cannot dispatch runtimes or execute workflows")
        if self.approval_granted:
            raise ValueError("supervised activation execution consumes evidence but cannot grant approval")
        if self.provider_or_connector_call_allowed:
            raise ValueError("supervised activation execution cannot call providers/connectors")
        if self.external_scheduler_install_allowed:
            raise ValueError("supervised activation execution cannot install external schedulers")
        if self.canonical_writeback_allowed or self.mutates_canonical_state:
            raise ValueError("supervised activation execution cannot mutate canonical state")
        if self.rd_workbook_update_allowed:
            raise ValueError("supervised activation execution cannot update the R&D workbook")
        for written in self.writes:
            normalized = written.replace("\\", "/")
            if not normalized.startswith(self.allowed_write_root) and not normalized.startswith(
                (MANIFEST_DIR / "").as_posix()
            ):
                raise ValueError("supervised activation execution writes escaped allowed roots")
        if set(self.blocked_effects) != set(BLOCKED_EFFECTS):
            raise ValueError("supervised activation execution must declare blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "execution_status": self.execution_status,
            "gate_status": self.gate_status,
            "run_queue_proof_status": self.run_queue_proof_status,
            "schedule_ids": list(self.schedule_ids),
            "schedule_count": self.schedule_count,
            "missing_evidence_slots": list(self.missing_evidence_slots),
            "execute_requested": self.execute_requested,
            "write_proof_requested": self.write_proof_requested,
            "write_executed": self.write_executed,
            "writes": list(self.writes),
            "manifest_patch_count": self.manifest_patch_count,
            "manifest_patches": [patch.to_dict() for patch in self.manifest_patches],
            "next_recommended_pass": self.next_recommended_pass,
            "local_only": self.local_only,
            "writes_artifacts": self.writes_artifacts,
            "schedule_manifest_write_executed": self.schedule_manifest_write_executed,
            "schedule_activation_executed": self.schedule_activation_executed,
            "schedule_daemon_started": self.schedule_daemon_started,
            "real_run_queue_written": self.real_run_queue_written,
            "real_audit_event_written": self.real_audit_event_written,
            "agent_bus_task_write_allowed": self.agent_bus_task_write_allowed,
            "runtime_dispatch_allowed": self.runtime_dispatch_allowed,
            "workflow_execution_allowed": self.workflow_execution_allowed,
            "approval_granted": self.approval_granted,
            "provider_or_connector_call_allowed": self.provider_or_connector_call_allowed,
            "external_scheduler_install_allowed": self.external_scheduler_install_allowed,
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "mutates_canonical_state": self.mutates_canonical_state,
            "rd_workbook_update_allowed": self.rd_workbook_update_allowed,
            "allowed_write_root": self.allowed_write_root,
            "blocked_effects": list(self.blocked_effects),
            "notes": list(self.notes),
        }


def _evidence_refs(evidence_refs: dict[str, str | None] | None) -> dict[str, str | None]:
    refs = evidence_refs or {}
    return {slot: refs.get(slot) for slot in REQUIRED_EVIDENCE_SLOTS}


def _patch_manifest(
    vault: Path,
    *,
    schedule_id: str,
    generated_at: str,
    evidence_refs: dict[str, str | None],
) -> PulseNativeScheduleManifestPatch:
    path = _manifest_path(vault, schedule_id)
    before = path.read_text(encoding="utf-8")
    after = _replace_top_level_scalar(before, "status", "active")
    after = _replace_top_level_scalar(after, "enabled", "true")
    after = _replace_top_level_scalar(after, "activation_state", "active_supervised")
    after = _append_activation_execution_block(after, generated_at=generated_at, evidence_refs=evidence_refs)
    path.write_text(after, encoding="utf-8")
    rel_path = path.relative_to(vault).as_posix()
    patch = PulseNativeScheduleManifestPatch(
        schedule_id=schedule_id,
        manifest_path=rel_path,
        before_sha256=_sha256(before),
        after_sha256=_sha256(after),
        status_before="active" if "\nstatus: active\n" in f"\n{before}\n" else "scaffolded",
        status_after="active",
        enabled_before="\nenabled: true\n" in f"\n{before}\n",
        enabled_after=True,
        activation_state_before="active_supervised"
        if "\nactivation_state: active_supervised\n" in f"\n{before}\n"
        else "planned",
        activation_state_after="active_supervised",
    )
    patch.validate()
    return patch


def build_pulse_native_schedule_supervised_activation_execution(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    schedule_ids: tuple[str, ...] | None = None,
    evidence_refs: dict[str, str | None] | None = None,
) -> PulseNativeScheduleSupervisedActivationExecution:
    """Build a dry-run supervised activation execution proof."""

    vault = _vault_path(vault_root)
    generated = generated_at or now_utc()
    ids = _normalize_schedule_ids(schedule_ids)
    refs = _evidence_refs(evidence_refs)
    gate = build_pulse_native_schedule_activation_gate(
        vault,
        generated_at=generated,
        schedule_ids=ids,
        evidence_refs=refs,
    )
    run_queue = build_pulse_native_schedule_run_queue_audit_proof(
        vault,
        generated_at=generated,
        schedule_ids=ids,
        evidence_refs=refs,
    )
    status = EXECUTION_STATUS_READY if gate.gate_status == GATE_STATUS_READY else EXECUTION_STATUS_BLOCKED_GATE
    model = PulseNativeScheduleSupervisedActivationExecution(
        generated_at=generated,
        execution_status=status,
        gate_status=gate.gate_status,
        run_queue_proof_status=run_queue.proof_status,
        schedule_ids=ids,
        schedule_count=len(ids),
        missing_evidence_slots=gate.missing_evidence_slots,
        execute_requested=False,
        write_proof_requested=False,
    )
    model.validate()
    return model


def write_pulse_native_schedule_supervised_activation_execution_proof(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    schedule_ids: tuple[str, ...] | None = None,
    evidence_refs: dict[str, str | None] | None = None,
    execute_activation: bool = False,
    output_path: str | Path | None = None,
) -> PulseNativeScheduleSupervisedActivationExecution:
    """Write a proof record, and optionally patch manifests when explicitly approved."""

    vault = _vault_path(vault_root)
    generated = generated_at or now_utc()
    ids = _normalize_schedule_ids(schedule_ids)
    refs = _evidence_refs(evidence_refs)
    base = build_pulse_native_schedule_supervised_activation_execution(
        vault,
        generated_at=generated,
        schedule_ids=ids,
        evidence_refs=refs,
    )

    patches: tuple[PulseNativeScheduleManifestPatch, ...] = ()
    status = base.execution_status
    if execute_activation:
        if base.execution_status != EXECUTION_STATUS_READY:
            raise ValueError("cannot execute supervised schedule activation until activation gate is ready")
        if base.run_queue_proof_status != PROOF_STATUS_READY:
            raise ValueError("cannot execute supervised schedule activation until run queue/audit proof is ready")
        patches = tuple(
            _patch_manifest(vault, schedule_id=schedule_id, generated_at=generated, evidence_refs=refs)
            for schedule_id in ids
        )
        status = EXECUTION_STATUS_EXECUTED

    schedule_slug = _slug("-".join(ids))
    if output_path is None:
        schedule_digest = hashlib.sha256(schedule_slug.encode("utf-8")).hexdigest()[:12]
        filename = f"{_date_slug(generated)}-activation-execution-{schedule_digest}.json"
        target_path = vault / ALLOWED_WRITE_ROOT / filename
    else:
        target_path = Path(output_path)
        if not target_path.is_absolute():
            target_path = vault / target_path
    target_path = target_path.resolve()
    allowed_root = (vault / ALLOWED_WRITE_ROOT).resolve()
    try:
        target_path.relative_to(allowed_root)
    except ValueError as exc:
        raise ValueError("supervised activation execution proof must be written under 07_LOGS/Pulse-Decks/native-schedule-activation-executions/") from exc

    rel_writes = [target_path.relative_to(vault).as_posix()]
    rel_writes.extend(patch.manifest_path for patch in patches)
    model = PulseNativeScheduleSupervisedActivationExecution(
        generated_at=base.generated_at,
        execution_status=status,
        gate_status=base.gate_status,
        run_queue_proof_status=base.run_queue_proof_status,
        schedule_ids=base.schedule_ids,
        schedule_count=base.schedule_count,
        missing_evidence_slots=base.missing_evidence_slots,
        execute_requested=execute_activation,
        write_proof_requested=True,
        write_executed=True,
        writes=tuple(rel_writes),
        manifest_patch_count=len(patches),
        manifest_patches=patches,
        writes_artifacts=True,
        schedule_manifest_write_executed=bool(patches),
        schedule_activation_executed=bool(patches),
    )
    model.validate()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(model.to_dict(), indent=2), encoding="utf-8")
    return model
