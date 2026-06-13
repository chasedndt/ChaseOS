"""Non-executing native schedule runner proof for ChaseOS Pulse.

This module models how a future ChaseOS-owned Pulse schedule runner would read
native schedule manifests and decide whether to defer, review, or catch up. It
does not start a daemon, enable manifests, enqueue runtimes, run workflows,
write Agent Bus tasks, or mutate canonical state.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

from runtime.pulse.card_schema import now_utc


MANIFEST_DIR = Path("runtime") / "schedules" / "manifests"
DEFAULT_SCHEDULE_IDS = ("chaseos_pulse_daily", "hermes_runtime_pulse")
ALLOWED_WRITE_ROOT = "07_LOGS/Pulse-Decks/native-schedule-runner-proof/"
NEXT_RECOMMENDED_PASS = "chaseos-pulse-native-schedule-runner-supervised-activation-gate"

RUNNER_STATUS_READY_BLOCKED = "runner_ready_activation_blocked"
RUNNER_STATUS_PARTIAL = "runner_partial_manifest_gap"
RUNNER_STATUSES = {RUNNER_STATUS_READY_BLOCKED, RUNNER_STATUS_PARTIAL}

SCHEDULE_DECISION_INACTIVE = "blocked_schedule_inactive"
SCHEDULE_DECISION_READY_DISABLED = "ready_disabled_manifest"
SCHEDULE_DECISION_READY_ENABLED = "ready_enabled_not_executed"
SCHEDULE_DECISIONS = {
    SCHEDULE_DECISION_INACTIVE,
    SCHEDULE_DECISION_READY_DISABLED,
    SCHEDULE_DECISION_READY_ENABLED,
}

CATCHUP_DECISION_REVIEW_CARD = "would_create_review_card"
CATCHUP_DECISION_NOOP = "no_catchup_without_enabled_schedule"
CATCHUP_DECISIONS = {CATCHUP_DECISION_REVIEW_CARD, CATCHUP_DECISION_NOOP}

BLOCKED_EFFECTS = (
    "agent_bus_task_write",
    "approval_execution",
    "canonical_writeback",
    "external_scheduler_install",
    "manifest_enablement",
    "provider_or_connector_call",
    "runtime_dispatch",
    "schedule_daemon_start",
    "workflow_execution",
)


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"Pulse native schedule manifest missing: {path}")
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(text) or {}
    else:
        data = _parse_simple_yaml(text)
    if not isinstance(data, dict):
        raise ValueError(f"Pulse native schedule manifest must be a mapping: {path}")
    return data


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, parsed)]
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#") or ":" not in raw:
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        key, value = raw.strip().split(":", 1)
        value = value.strip().strip('"')
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            if value.lower() == "true":
                parent[key] = True
            elif value.lower() == "false":
                parent[key] = False
            else:
                parent[key] = value
    return parsed


def _date_slug(generated_at: str) -> str:
    return generated_at[:10] if len(generated_at) >= 10 else now_utc()[:10]


@dataclass(frozen=True)
class PulseNativeScheduleRunnerTarget:
    schedule_id: str
    manifest_path: str
    owner: str
    feature: str
    enabled: bool
    activation_state: str
    schedule_owner: str
    executor_adapter: str
    workflow_id: str
    audience: str
    output_root: str
    timezone: str
    cadence_type: str
    local_time: str
    if_machine_off: str
    if_server_down: str
    if_runtime_unavailable: str
    if_approval_timeout: str
    external_connectors_enabled: bool
    unrestricted_browsing_enabled: bool
    canonical_writeback_enabled: bool
    openclaw_cron_owner: bool
    windows_task_scheduler_owner: bool
    executor_is_adapter_only: bool
    runner_decision: str
    catchup_decision: str
    blockers: tuple[str, ...]

    def validate(self) -> None:
        if not self.schedule_id:
            raise ValueError("schedule target requires schedule_id")
        if self.runner_decision not in SCHEDULE_DECISIONS:
            raise ValueError("invalid runner decision")
        if self.catchup_decision not in CATCHUP_DECISIONS:
            raise ValueError("invalid catchup decision")
        if self.owner != "chaseos" or self.schedule_owner != "chaseos":
            raise ValueError("Pulse schedule runner proof requires ChaseOS-owned schedule intent")
        if self.openclaw_cron_owner or self.windows_task_scheduler_owner:
            raise ValueError("Pulse schedule runner proof cannot make external schedulers owners")
        if self.external_connectors_enabled or self.unrestricted_browsing_enabled:
            raise ValueError("Pulse schedule runner proof requires external sources disabled")
        if self.canonical_writeback_enabled:
            raise ValueError("Pulse schedule runner proof requires canonical writeback disabled")
        if not self.executor_is_adapter_only:
            raise ValueError("Pulse runner proof requires adapter-only execution identity")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class PulseNativeScheduleRunnerProof:
    generated_at: str
    runner_status: str
    schedule_count: int
    ready_schedule_count: int
    enabled_schedule_count: int
    simulated_missed_run: bool
    write_requested: bool
    write_executed: bool
    schedules: tuple[PulseNativeScheduleRunnerTarget, ...]
    writes: tuple[str, ...] = ()
    next_recommended_pass: str = NEXT_RECOMMENDED_PASS
    read_only: bool = True
    local_only: bool = True
    writes_artifacts: bool = False
    schedule_daemon_started: bool = False
    schedule_manifest_written: bool = False
    schedule_activation_allowed: bool = False
    run_queue_written: bool = False
    agent_bus_task_write_allowed: bool = False
    runtime_dispatch_allowed: bool = False
    workflow_execution_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    approval_execution_allowed: bool = False
    canonical_writeback_allowed: bool = False
    mutates_canonical_state: bool = False
    rd_workbook_update_allowed: bool = False
    external_scheduler_install_allowed: bool = False
    allowed_write_root: str = ALLOWED_WRITE_ROOT
    blocked_effects: tuple[str, ...] = BLOCKED_EFFECTS
    notes: tuple[str, ...] = field(
        default_factory=lambda: (
            "Runner proof is non-executing and does not activate schedules.",
            "Catch-up decisions are proof metadata only unless a future supervised activation gate is approved.",
        )
    )

    def validate(self) -> None:
        if self.runner_status not in RUNNER_STATUSES:
            raise ValueError("invalid runner status")
        if self.schedule_count != len(self.schedules):
            raise ValueError("schedule_count must match schedules")
        if self.ready_schedule_count < 0 or self.enabled_schedule_count < 0:
            raise ValueError("schedule counts cannot be negative")
        for schedule in self.schedules:
            schedule.validate()
        if self.write_executed and not self.write_requested:
            raise ValueError("write_executed requires write_requested")
        if self.write_executed and self.read_only:
            raise ValueError("written runner proof cannot be read_only")
        if self.write_executed and not self.writes_artifacts:
            raise ValueError("written runner proof must report writes_artifacts")
        if self.schedule_daemon_started:
            raise ValueError("runner proof cannot start a schedule daemon")
        if self.schedule_manifest_written or self.schedule_activation_allowed:
            raise ValueError("runner proof cannot write or activate schedule manifests")
        if self.run_queue_written:
            raise ValueError("runner proof cannot write the run queue")
        if self.agent_bus_task_write_allowed:
            raise ValueError("runner proof cannot write Agent Bus tasks")
        if self.runtime_dispatch_allowed or self.workflow_execution_allowed:
            raise ValueError("runner proof cannot dispatch runtimes or execute workflows")
        if self.provider_or_connector_call_allowed:
            raise ValueError("runner proof cannot call providers/connectors")
        if self.approval_execution_allowed:
            raise ValueError("runner proof cannot execute approvals")
        if self.canonical_writeback_allowed or self.mutates_canonical_state:
            raise ValueError("runner proof cannot mutate canonical state")
        if self.rd_workbook_update_allowed:
            raise ValueError("runner proof cannot update the R&D workbook")
        if self.external_scheduler_install_allowed:
            raise ValueError("runner proof cannot install external schedulers")
        for written in self.writes:
            if not written.replace("\\", "/").startswith(self.allowed_write_root):
                raise ValueError("runner proof writes must stay under native schedule runner proof logs")
        if set(self.blocked_effects) != set(BLOCKED_EFFECTS):
            raise ValueError("runner proof must declare blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "runner_status": self.runner_status,
            "schedule_count": self.schedule_count,
            "ready_schedule_count": self.ready_schedule_count,
            "enabled_schedule_count": self.enabled_schedule_count,
            "simulated_missed_run": self.simulated_missed_run,
            "write_requested": self.write_requested,
            "write_executed": self.write_executed,
            "schedules": [schedule.to_dict() for schedule in self.schedules],
            "writes": list(self.writes),
            "next_recommended_pass": self.next_recommended_pass,
            "read_only": self.read_only,
            "local_only": self.local_only,
            "writes_artifacts": self.writes_artifacts,
            "schedule_daemon_started": self.schedule_daemon_started,
            "schedule_manifest_written": self.schedule_manifest_written,
            "schedule_activation_allowed": self.schedule_activation_allowed,
            "run_queue_written": self.run_queue_written,
            "agent_bus_task_write_allowed": self.agent_bus_task_write_allowed,
            "runtime_dispatch_allowed": self.runtime_dispatch_allowed,
            "workflow_execution_allowed": self.workflow_execution_allowed,
            "provider_or_connector_call_allowed": self.provider_or_connector_call_allowed,
            "approval_execution_allowed": self.approval_execution_allowed,
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "mutates_canonical_state": self.mutates_canonical_state,
            "rd_workbook_update_allowed": self.rd_workbook_update_allowed,
            "external_scheduler_install_allowed": self.external_scheduler_install_allowed,
            "allowed_write_root": self.allowed_write_root,
            "blocked_effects": list(self.blocked_effects),
            "notes": list(self.notes),
        }


def _target_from_manifest(
    vault: Path,
    schedule_id: str,
    *,
    simulated_missed_run: bool,
) -> PulseNativeScheduleRunnerTarget:
    rel_path = (MANIFEST_DIR / f"{schedule_id}.yaml").as_posix()
    manifest = _read_yaml(vault / rel_path)
    execution = manifest.get("execution") or {}
    delivery = manifest.get("delivery") or {}
    missed = manifest.get("missed_run_policy") or {}
    source_policy = manifest.get("source_policy") or {}
    deck = manifest.get("deck") or {}
    cadence = manifest.get("cadence") or {}
    audit_identity = manifest.get("audit_identity") or {}
    schedule_id_value = str(manifest.get("schedule_id") or "")
    if schedule_id_value != schedule_id:
        raise ValueError(f"manifest schedule_id mismatch for {schedule_id}")
    enabled = bool(manifest.get("enabled", False))
    runner_decision = SCHEDULE_DECISION_READY_DISABLED if not enabled else SCHEDULE_DECISION_READY_ENABLED
    catchup_decision = (
        CATCHUP_DECISION_REVIEW_CARD
        if simulated_missed_run and str(missed.get("if_machine_off") or "") == "catch_up_once"
        else CATCHUP_DECISION_NOOP
    )
    blockers = ["supervised_activation_gate_missing"]
    if not enabled:
        blockers.append("schedule_manifest_disabled")
    if not simulated_missed_run:
        blockers.append("no_missed_run_simulated")
    target = PulseNativeScheduleRunnerTarget(
        schedule_id=schedule_id_value,
        manifest_path=rel_path,
        owner=str(manifest.get("owner") or ""),
        feature=str(manifest.get("feature") or ""),
        enabled=enabled,
        activation_state=str(manifest.get("activation_state") or ""),
        schedule_owner=str(execution.get("schedule_owner") or ""),
        executor_adapter=str(execution.get("executor_adapter") or ""),
        workflow_id=str(execution.get("workflow_id") or ""),
        audience=str(deck.get("audience") or ""),
        output_root=str(delivery.get("output_root") or ""),
        timezone=str(cadence.get("timezone") or ""),
        cadence_type=str(cadence.get("type") or ""),
        local_time=str(cadence.get("local_time") or ""),
        if_machine_off=str(missed.get("if_machine_off") or ""),
        if_server_down=str(missed.get("if_server_down") or ""),
        if_runtime_unavailable=str(missed.get("if_runtime_unavailable") or ""),
        if_approval_timeout=str(missed.get("if_approval_timeout") or ""),
        external_connectors_enabled=bool(source_policy.get("external_connectors_enabled", False)),
        unrestricted_browsing_enabled=bool(source_policy.get("unrestricted_browsing_enabled", False)),
        canonical_writeback_enabled=bool(deck.get("canonical_writeback_enabled", False)),
        openclaw_cron_owner=bool(execution.get("openclaw_cron_owner", False)),
        windows_task_scheduler_owner=bool(execution.get("windows_task_scheduler_owner", False)),
        executor_is_adapter_only=bool(audit_identity.get("executor_is_adapter_only", False)),
        runner_decision=runner_decision,
        catchup_decision=catchup_decision,
        blockers=tuple(blockers),
    )
    target.validate()
    return target


def build_pulse_native_schedule_runner_proof(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    schedule_ids: tuple[str, ...] = DEFAULT_SCHEDULE_IDS,
    simulate_missed_run: bool = False,
    write: bool = False,
) -> PulseNativeScheduleRunnerProof:
    """Build or optionally write a non-executing Pulse schedule runner proof."""

    vault = _vault_path(vault_root)
    generated = generated_at or now_utc()
    schedules = tuple(
        _target_from_manifest(vault, schedule_id, simulated_missed_run=simulate_missed_run)
        for schedule_id in schedule_ids
    )
    ready_count = sum(1 for schedule in schedules if schedule.runner_decision in SCHEDULE_DECISIONS)
    enabled_count = sum(1 for schedule in schedules if schedule.enabled)
    runner_status = RUNNER_STATUS_READY_BLOCKED if ready_count == len(schedules) else RUNNER_STATUS_PARTIAL
    writes: tuple[str, ...] = ()

    if write:
        out_path = vault / ALLOWED_WRITE_ROOT / f"{_date_slug(generated)}-native-schedule-runner-proof.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        rel_path = out_path.relative_to(vault).as_posix()
        model = PulseNativeScheduleRunnerProof(
            generated_at=generated,
            runner_status=runner_status,
            schedule_count=len(schedules),
            ready_schedule_count=ready_count,
            enabled_schedule_count=enabled_count,
            simulated_missed_run=simulate_missed_run,
            write_requested=True,
            write_executed=True,
            schedules=schedules,
            writes=(rel_path,),
            read_only=False,
            writes_artifacts=True,
        )
        out_path.write_text(json.dumps(model.to_dict(), indent=2), encoding="utf-8")
        model.validate()
        return model

    model = PulseNativeScheduleRunnerProof(
        generated_at=generated,
        runner_status=runner_status,
        schedule_count=len(schedules),
        ready_schedule_count=ready_count,
        enabled_schedule_count=enabled_count,
        simulated_missed_run=simulate_missed_run,
        write_requested=False,
        write_executed=False,
        schedules=schedules,
        writes=writes,
    )
    model.validate()
    return model
