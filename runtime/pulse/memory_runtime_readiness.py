"""Read-only ChaseOS Pulse memory/runtime readiness surface.

This module ties Pulse back to the Context Memory Core and AgentHub runtime
memory substrate without applying memory, feedback, repair candidates, or
permissions. It is an operator-facing readiness contract for the next Pulse
product surfaces, not a memory writer.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.memory.inspector import build_memory_summary
from runtime.pulse.candidate_inspector import build_candidate_inspector_snapshot
from runtime.pulse.card_schema import now_utc


MEMORY_RUNTIME_READINESS_LANES = {
    "context_memory_core",
    "personal_map_candidates",
    "feedback_rules",
    "runtime_profiles",
    "runtime_identity_ledgers",
    "runtime_navigation_maps",
    "execution_repair_memory",
    "runtime_brain_readiness",
}

MEMORY_RUNTIME_READINESS_STATUSES = {
    "ready",
    "partial",
    "blocked",
    "empty",
}

MEMORY_RUNTIME_BLOCKED_EFFECTS = (
    "agent_bus_task_write",
    "approval_grant",
    "approval_execution",
    "canonical_writeback",
    "feedback_rule_application",
    "memory_atom_approval",
    "memory_mutation",
    "personal_map_mutation",
    "provider_or_connector_call",
    "repair_memory_application",
    "runtime_brain_update",
    "runtime_dispatch",
    "runtime_navigation_map_update",
    "schedule_activation",
    "second_datastore_write",
)

FEEDBACK_RULE_ROOT = Path("runtime/memory/feedback-rules")
ACCEPTED_FEEDBACK_RULES_FILE = FEEDBACK_RULE_ROOT / "accepted-signals.jsonl"


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return str(path.resolve())


def _count_jsonl_records(path: Path) -> tuple[int, list[str]]:
    """Count valid JSONL records without creating, mutating, or normalizing files."""

    if not path.exists():
        return 0, []
    count = 0
    errors: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        text = line.strip()
        if not text:
            continue
        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            errors.append(f"{path.as_posix()}:{line_number}: {exc.msg}")
            continue
        count += 1
    return count, errors


def _lane_status(*, count: int, blocked: bool = False, incomplete: bool = False) -> str:
    if blocked:
        return "blocked"
    if count == 0:
        return "empty"
    if incomplete:
        return "partial"
    return "ready"


@dataclass(frozen=True)
class PulseMemoryRuntimeReadinessLane:
    """One display lane in the read-only memory/runtime readiness surface."""

    lane_id: str
    label: str
    item_count: int
    ready_count: int = 0
    partial_count: int = 0
    blocked_count: int = 0
    status: str = "empty"
    source_refs: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.lane_id not in MEMORY_RUNTIME_READINESS_LANES:
            raise ValueError("invalid Pulse memory/runtime readiness lane_id")
        if not self.label:
            raise ValueError("Pulse memory/runtime readiness lane label is required")
        if self.status not in MEMORY_RUNTIME_READINESS_STATUSES:
            raise ValueError("invalid Pulse memory/runtime readiness lane status")
        for value in (self.item_count, self.ready_count, self.partial_count, self.blocked_count):
            if value < 0:
                raise ValueError("Pulse memory/runtime readiness lane counts cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["source_refs"] = list(self.source_refs)
        payload["notes"] = list(self.notes)
        return payload


@dataclass(frozen=True)
class PulseRuntimeMemoryReadinessCard:
    """Compact per-runtime readiness summary for AgentHub/Runtime Brain surfaces."""

    runtime_id: str
    present_families: tuple[str, ...] = ()
    missing_families: tuple[str, ...] = ()
    status: str = "empty"
    source_refs: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.runtime_id:
            raise ValueError("runtime memory readiness card requires runtime_id")
        if self.status not in MEMORY_RUNTIME_READINESS_STATUSES:
            raise ValueError("invalid runtime memory readiness card status")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["present_families"] = list(self.present_families)
        payload["missing_families"] = list(self.missing_families)
        payload["source_refs"] = list(self.source_refs)
        return payload


@dataclass(frozen=True)
class PulseMemoryRuntimeReadinessSurface:
    """Read-only aggregate over Pulse memory, feedback, and runtime brain readiness."""

    generated_at: str
    readiness_status: str
    lanes: tuple[PulseMemoryRuntimeReadinessLane, ...]
    runtime_cards: tuple[PulseRuntimeMemoryReadinessCard, ...]
    source_refs: tuple[str, ...]
    memory_posture: str
    runtime_count: int = 0
    active_task_context_count: int = 0
    family_counts: dict[str, int] = field(default_factory=dict)
    feedback_rule_count: int = 0
    feedback_rule_error_count: int = 0
    personal_map_candidate_count: int = 0
    execution_repair_candidate_count: int = 0
    validation_error_count: int = 0
    read_only: bool = True
    local_only: bool = True
    mutates_memory: bool = False
    applies_feedback_rules: bool = False
    applies_personal_map_candidates: bool = False
    applies_execution_repair_candidates: bool = False
    updates_runtime_brains: bool = False
    grants_permissions: bool = False
    agent_bus_task_write_allowed: bool = False
    runtime_dispatch_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    schedule_activation_allowed: bool = False
    memory_approval_allowed: bool = False
    canonical_writeback_allowed: bool = False
    mutates_canonical_state: bool = False
    second_datastore_created: bool = False
    rd_workbook_update_allowed: bool = False
    blocked_effects: tuple[str, ...] = MEMORY_RUNTIME_BLOCKED_EFFECTS

    @property
    def lane_count(self) -> int:
        return len(self.lanes)

    @property
    def runtime_card_count(self) -> int:
        return len(self.runtime_cards)

    def validate(self) -> None:
        if not self.generated_at:
            raise ValueError("generated_at is required")
        if self.readiness_status not in MEMORY_RUNTIME_READINESS_STATUSES:
            raise ValueError("invalid Pulse memory/runtime readiness status")
        lane_ids = {lane.lane_id for lane in self.lanes}
        if lane_ids != MEMORY_RUNTIME_READINESS_LANES:
            raise ValueError("Pulse memory/runtime readiness must expose all lanes")
        for lane in self.lanes:
            lane.validate()
        for card in self.runtime_cards:
            card.validate()
        for value in (
            self.runtime_count,
            self.active_task_context_count,
            self.feedback_rule_count,
            self.feedback_rule_error_count,
            self.personal_map_candidate_count,
            self.execution_repair_candidate_count,
            self.validation_error_count,
        ):
            if value < 0:
                raise ValueError("Pulse memory/runtime readiness counts cannot be negative")
        if not self.read_only:
            raise ValueError("Pulse memory/runtime readiness must remain read-only")
        if not self.local_only:
            raise ValueError("Pulse memory/runtime readiness must remain local-only")
        if self.mutates_memory:
            raise ValueError("Pulse memory/runtime readiness cannot mutate memory")
        if self.applies_feedback_rules:
            raise ValueError("Pulse memory/runtime readiness cannot apply feedback rules")
        if self.applies_personal_map_candidates:
            raise ValueError("Pulse memory/runtime readiness cannot apply Personal Map candidates")
        if self.applies_execution_repair_candidates:
            raise ValueError("Pulse memory/runtime readiness cannot apply execution repair candidates")
        if self.updates_runtime_brains:
            raise ValueError("Pulse memory/runtime readiness cannot update runtime brains")
        if self.grants_permissions:
            raise ValueError("Pulse memory/runtime readiness cannot grant permissions")
        if self.agent_bus_task_write_allowed:
            raise ValueError("Pulse memory/runtime readiness cannot write Agent Bus tasks")
        if self.runtime_dispatch_allowed:
            raise ValueError("Pulse memory/runtime readiness cannot dispatch runtimes")
        if self.provider_or_connector_call_allowed:
            raise ValueError("Pulse memory/runtime readiness cannot call providers/connectors")
        if self.schedule_activation_allowed:
            raise ValueError("Pulse memory/runtime readiness cannot activate schedules")
        if self.memory_approval_allowed:
            raise ValueError("Pulse memory/runtime readiness cannot approve memory")
        if self.canonical_writeback_allowed:
            raise ValueError("Pulse memory/runtime readiness cannot allow canonical writeback")
        if self.mutates_canonical_state:
            raise ValueError("Pulse memory/runtime readiness cannot mutate canonical state")
        if self.second_datastore_created:
            raise ValueError("Pulse memory/runtime readiness cannot create a second datastore")
        if self.rd_workbook_update_allowed:
            raise ValueError("Pulse memory/runtime readiness cannot update the R&D workbook")
        if set(self.blocked_effects) != set(MEMORY_RUNTIME_BLOCKED_EFFECTS):
            raise ValueError("Pulse memory/runtime readiness must declare blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "readiness_status": self.readiness_status,
            "lane_count": self.lane_count,
            "lanes": [lane.to_dict() for lane in self.lanes],
            "runtime_card_count": self.runtime_card_count,
            "runtime_cards": [card.to_dict() for card in self.runtime_cards],
            "source_refs": list(self.source_refs),
            "memory_posture": self.memory_posture,
            "runtime_count": self.runtime_count,
            "active_task_context_count": self.active_task_context_count,
            "family_counts": dict(self.family_counts),
            "feedback_rule_count": self.feedback_rule_count,
            "feedback_rule_error_count": self.feedback_rule_error_count,
            "personal_map_candidate_count": self.personal_map_candidate_count,
            "execution_repair_candidate_count": self.execution_repair_candidate_count,
            "validation_error_count": self.validation_error_count,
            "read_only": self.read_only,
            "local_only": self.local_only,
            "mutates_memory": self.mutates_memory,
            "applies_feedback_rules": self.applies_feedback_rules,
            "applies_personal_map_candidates": self.applies_personal_map_candidates,
            "applies_execution_repair_candidates": self.applies_execution_repair_candidates,
            "updates_runtime_brains": self.updates_runtime_brains,
            "grants_permissions": self.grants_permissions,
            "agent_bus_task_write_allowed": self.agent_bus_task_write_allowed,
            "runtime_dispatch_allowed": self.runtime_dispatch_allowed,
            "provider_or_connector_call_allowed": self.provider_or_connector_call_allowed,
            "schedule_activation_allowed": self.schedule_activation_allowed,
            "memory_approval_allowed": self.memory_approval_allowed,
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "mutates_canonical_state": self.mutates_canonical_state,
            "second_datastore_created": self.second_datastore_created,
            "rd_workbook_update_allowed": self.rd_workbook_update_allowed,
            "blocked_effects": list(self.blocked_effects),
        }


def _runtime_source_refs(runtime: dict[str, Any]) -> tuple[str, ...]:
    refs = []
    runtime_id = str(runtime.get("runtime_id") or "")
    if runtime.get("profile_present"):
        refs.append(f"runtime/memory/adapters/{runtime_id}/profile.json")
    if runtime.get("identity_ledger_present"):
        refs.append(f"runtime/memory/adapters/{runtime_id}/identity-ledger.json")
    if runtime.get("nav_map_present"):
        refs.append(f"runtime/memory/nav/{runtime_id}/nav-map.json")
    if runtime.get("repair_memory_present"):
        refs.append(f"runtime/memory/repair/{runtime_id}.json")
    if runtime.get("scorecard_present"):
        refs.append(f"runtime/memory/scorecards/{runtime_id}.json")
    return tuple(refs)


def _runtime_cards(memory_summary: dict[str, Any]) -> tuple[PulseRuntimeMemoryReadinessCard, ...]:
    runtime_lookup = {
        str(runtime.get("runtime_id")): runtime
        for runtime in memory_summary.get("layer_c", {}).get("runtimes", [])
        if runtime.get("runtime_id")
    }
    cards: list[PulseRuntimeMemoryReadinessCard] = []
    for coverage in memory_summary.get("runtime_summary", {}).get("runtime_coverage", []):
        runtime_id = str(coverage.get("runtime_id") or "")
        present = tuple(coverage.get("present_families") or ())
        missing = tuple(coverage.get("missing_families") or ())
        status = "ready" if present and not missing else "partial" if present else "empty"
        card = PulseRuntimeMemoryReadinessCard(
            runtime_id=runtime_id,
            present_families=present,
            missing_families=missing,
            status=status,
            source_refs=_runtime_source_refs(runtime_lookup.get(runtime_id, {})),
        )
        card.validate()
        cards.append(card)
    return tuple(cards)


def _lane(
    lane_id: str,
    label: str,
    *,
    item_count: int,
    ready_count: int = 0,
    partial_count: int = 0,
    blocked_count: int = 0,
    status: str,
    source_refs: tuple[str, ...] = (),
    notes: tuple[str, ...] = (),
) -> PulseMemoryRuntimeReadinessLane:
    lane = PulseMemoryRuntimeReadinessLane(
        lane_id=lane_id,
        label=label,
        item_count=item_count,
        ready_count=ready_count,
        partial_count=partial_count,
        blocked_count=blocked_count,
        status=status,
        source_refs=source_refs,
        notes=notes,
    )
    lane.validate()
    return lane


def build_pulse_memory_runtime_readiness(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
) -> PulseMemoryRuntimeReadinessSurface:
    """Build the read-only Pulse memory/runtime readiness packet."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or now_utc()
    memory_summary = build_memory_summary(vault)
    candidate_snapshot = build_candidate_inspector_snapshot(vault)

    accepted_feedback_path = vault / ACCEPTED_FEEDBACK_RULES_FILE
    feedback_rule_count, feedback_rule_errors = _count_jsonl_records(accepted_feedback_path)
    feedback_rule_refs = (
        (_relative_to_vault(vault, accepted_feedback_path),)
        if accepted_feedback_path.exists()
        else ()
    )

    family_counts = dict(memory_summary.get("runtime_summary", {}).get("family_counts") or {})
    runtime_count = int(memory_summary.get("runtime_summary", {}).get("runtime_count") or 0)
    active_task_context_count = int(
        memory_summary.get("task_summary", {}).get("active_task_context_count") or 0
    )
    validation = memory_summary.get("validation") or {}
    validation_error_count = int(validation.get("error_count") or 0)
    runtime_cards = _runtime_cards(memory_summary)
    complete_runtime_count = sum(1 for card in runtime_cards if card.status == "ready")
    partial_runtime_count = sum(1 for card in runtime_cards if card.status == "partial")
    personal_map_candidate_count = candidate_snapshot.counts_by_kind.get("personal_map_candidate", 0)
    execution_repair_candidate_count = candidate_snapshot.counts_by_kind.get(
        "execution_repair_candidate",
        0,
    )

    profile_count = int(family_counts.get("profile", 0))
    identity_count = int(family_counts.get("identity_ledger", 0))
    navigation_count = int(family_counts.get("navigation", 0))
    repair_count = int(family_counts.get("repair_memory", 0))

    blocked = validation_error_count > 0 or bool(feedback_rule_errors)
    runtime_incomplete = partial_runtime_count > 0
    lanes = (
        _lane(
            "context_memory_core",
            "Context Memory Core",
            item_count=runtime_count + active_task_context_count,
            ready_count=runtime_count,
            partial_count=active_task_context_count,
            blocked_count=validation_error_count,
            status=_lane_status(
                count=runtime_count + active_task_context_count,
                blocked=validation_error_count > 0,
            ),
            source_refs=("runtime/memory/",),
            notes=("Layer C/D memory summary is advisory and read-only.",),
        ),
        _lane(
            "personal_map_candidates",
            "Personal Map Candidates",
            item_count=personal_map_candidate_count,
            ready_count=personal_map_candidate_count,
            status=_lane_status(count=personal_map_candidate_count),
            source_refs=tuple(candidate_snapshot.source_log_paths),
            notes=("Candidates are not applied to the Personal Map by this surface.",),
        ),
        _lane(
            "feedback_rules",
            "Feedback Rules",
            item_count=feedback_rule_count,
            ready_count=feedback_rule_count,
            blocked_count=len(feedback_rule_errors),
            status=_lane_status(
                count=feedback_rule_count,
                blocked=bool(feedback_rule_errors),
            ),
            source_refs=feedback_rule_refs,
            notes=tuple(feedback_rule_errors),
        ),
        _lane(
            "runtime_profiles",
            "Runtime Profiles",
            item_count=profile_count,
            ready_count=profile_count,
            status=_lane_status(count=profile_count),
            source_refs=("runtime/memory/adapters/",),
        ),
        _lane(
            "runtime_identity_ledgers",
            "Runtime Identity Ledgers",
            item_count=identity_count,
            ready_count=identity_count,
            status=_lane_status(count=identity_count),
            source_refs=("runtime/memory/adapters/",),
            notes=("Identity ledgers are behavioral evidence, not authority grants.",),
        ),
        _lane(
            "runtime_navigation_maps",
            "Runtime Navigation Maps",
            item_count=navigation_count,
            ready_count=navigation_count,
            status=_lane_status(count=navigation_count),
            source_refs=("runtime/memory/nav/",),
        ),
        _lane(
            "execution_repair_memory",
            "Execution Repair Memory",
            item_count=repair_count + execution_repair_candidate_count,
            ready_count=repair_count,
            partial_count=execution_repair_candidate_count,
            status=_lane_status(count=repair_count + execution_repair_candidate_count),
            source_refs=tuple(
                sorted(set(candidate_snapshot.source_log_paths) | {"runtime/memory/repair/"})
            ),
            notes=("Repair candidates remain reviewable; repair memory is not auto-applied.",),
        ),
        _lane(
            "runtime_brain_readiness",
            "Runtime Brain Readiness",
            item_count=runtime_count,
            ready_count=complete_runtime_count,
            partial_count=partial_runtime_count,
            status=_lane_status(
                count=runtime_count,
                blocked=blocked,
                incomplete=runtime_incomplete,
            ),
            source_refs=("runtime/agents/runtime_brain.py", "runtime/memory/"),
            notes=("Runtime brain readiness is evidence posture only, not self-upgrade activation.",),
        ),
    )

    if blocked:
        readiness_status = "blocked"
    elif runtime_count == 0 and feedback_rule_count == 0 and candidate_snapshot.item_count == 0:
        readiness_status = "empty"
    elif runtime_incomplete:
        readiness_status = "partial"
    else:
        readiness_status = "ready"

    source_refs = tuple(
        sorted(
            {
                "runtime/memory/",
                "runtime/agents/runtime_brain.py",
                "runtime/agents/agent_hub.py",
                "runtime/agents/execution_repair_memory.py",
                "runtime/pulse/memory_runtime_readiness.py",
                *candidate_snapshot.source_log_paths,
                *feedback_rule_refs,
            }
        )
    )
    surface = PulseMemoryRuntimeReadinessSurface(
        generated_at=timestamp,
        readiness_status=readiness_status,
        lanes=lanes,
        runtime_cards=runtime_cards,
        source_refs=source_refs,
        memory_posture=str(memory_summary.get("memory_posture") or "empty"),
        runtime_count=runtime_count,
        active_task_context_count=active_task_context_count,
        family_counts=family_counts,
        feedback_rule_count=feedback_rule_count,
        feedback_rule_error_count=len(feedback_rule_errors),
        personal_map_candidate_count=personal_map_candidate_count,
        execution_repair_candidate_count=execution_repair_candidate_count,
        validation_error_count=validation_error_count,
    )
    surface.validate()
    return surface
