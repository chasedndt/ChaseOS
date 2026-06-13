"""Proof-only Personal Map apply transaction packet for ChaseOS Pulse.

This module wraps the existing governed Personal Map apply lane with an
auditable transaction packet. It does not execute live apply or mutate the
runtime Personal Map graph. Optional write mode emits only a proof JSON artifact
under Pulse logs.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.card_schema import now_utc
from runtime.pulse.personal_map_live_apply_proof import (
    PERSONAL_MAP_GRAPH_PATH,
    build_personal_map_live_apply_proof,
)


SURFACE_ID = "chaseos_pulse_personal_map_apply_transaction_proof"
PROOF_ROOT = Path("07_LOGS") / "Pulse-Decks" / "personal-map-apply-transactions"
ALLOWED_WRITE_ROOT = "07_LOGS/Pulse-Decks/personal-map-apply-transactions/"

STATUS_READY = "transaction_proof_ready"
STATUS_BLOCKED_NO_READY_CANDIDATES = "blocked_no_ready_personal_map_candidates"
STATUSES = {STATUS_READY, STATUS_BLOCKED_NO_READY_CANDIDATES}

NEXT_RECOMMENDED_PASS = "operator-approved-personal-map-live-apply-or-defer-to-final-closeout"

BLOCKED_EFFECTS = (
    "agent_bus_task_write",
    "approval_execution",
    "canonical_writeback",
    "live_candidate_apply",
    "memory_approval",
    "now_md_mutation",
    "personal_map_mutation",
    "project_file_mutation",
    "provider_or_connector_call",
    "rd_workbook_update",
    "runtime_brain_update",
    "runtime_dispatch",
    "schedule_activation",
    "second_datastore_write",
)


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _date_slug(generated_at: str) -> str:
    date = generated_at[:10]
    return date if len(date) == 10 else now_utc()[:10]


def _slug(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in value).strip("-")


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return str(path.resolve())


def _assert_inside(child: Path, parent: Path, message: str) -> None:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError as exc:
        raise ValueError(message) from exc


def _file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class PersonalMapApplyTransactionEntryProof:
    transaction_entry_id: str
    decision_id: str
    candidate_id: str
    candidate_type: str
    target_type: str
    target_id: str | None
    target_label: str | None
    planned_write_target: str
    idempotency_key: str
    approved_for_future_apply: bool
    already_applied: bool = False
    live_apply_allowed: bool = False
    writes_runtime_memory_graph: bool = False
    canonical_writeback_allowed: bool = False

    def validate(self) -> None:
        if not self.transaction_entry_id or not self.decision_id or not self.candidate_id:
            raise ValueError("Personal Map transaction entry requires ids")
        if not self.planned_write_target:
            raise ValueError("Personal Map transaction entry requires a planned write target")
        if not self.idempotency_key:
            raise ValueError("Personal Map transaction entry requires an idempotency key")
        if not self.approved_for_future_apply:
            raise ValueError("Personal Map transaction entry requires prior approval signal")
        if self.already_applied:
            raise ValueError("Personal Map transaction entry cannot target an already-applied decision")
        if self.live_apply_allowed or self.writes_runtime_memory_graph:
            raise ValueError("Personal Map transaction proof cannot enable live apply")
        if self.canonical_writeback_allowed:
            raise ValueError("Personal Map transaction proof cannot allow canonical writeback")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class PersonalMapApplyTransactionProof:
    generated_at: str
    surface: str
    transaction_status: str
    transaction_id: str | None
    ready_candidate_count: int
    transaction_entry_count: int
    graph_present_before: bool
    graph_node_count_before: int
    graph_edge_count_before: int
    graph_sha256_before: str | None
    planned_write_target: str
    dry_run_apply_count: int
    dry_run_error_count: int
    entries: tuple[PersonalMapApplyTransactionEntryProof, ...]
    source_refs: tuple[str, ...]
    write_requested: bool = False
    write_executed: bool = False
    writes: tuple[str, ...] = ()
    next_recommended_pass: str = NEXT_RECOMMENDED_PASS
    local_only: bool = True
    read_only: bool = True
    writes_artifacts: bool = False
    live_apply_allowed: bool = False
    applies_personal_map_candidates: bool = False
    writes_runtime_memory_graph: bool = False
    approves_memory: bool = False
    mutates_canonical_state: bool = False
    canonical_writeback_allowed: bool = False
    agent_bus_task_write_allowed: bool = False
    runtime_dispatch_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    schedule_activation_allowed: bool = False
    second_datastore_created: bool = False
    rd_workbook_update_allowed: bool = False
    allowed_write_root: str = ALLOWED_WRITE_ROOT
    blocked_effects: tuple[str, ...] = BLOCKED_EFFECTS
    notes: tuple[str, ...] = field(
        default_factory=lambda: (
            "This is a proof-only transaction packet for review before any live Personal Map apply.",
            "The only live apply command remains a separate operator-approved action.",
        )
    )

    def validate(self) -> None:
        if self.surface != SURFACE_ID:
            raise ValueError("invalid Personal Map transaction proof surface")
        if self.transaction_status not in STATUSES:
            raise ValueError("invalid Personal Map transaction proof status")
        if self.ready_candidate_count != len(self.entries):
            raise ValueError("ready_candidate_count must match entries")
        if self.transaction_entry_count != len(self.entries):
            raise ValueError("transaction_entry_count must match entries")
        if self.transaction_status == STATUS_READY and not self.transaction_id:
            raise ValueError("ready transaction proof requires a transaction_id")
        if self.transaction_status == STATUS_BLOCKED_NO_READY_CANDIDATES and self.entries:
            raise ValueError("blocked transaction proof cannot include entries")
        if self.dry_run_error_count:
            raise ValueError("Personal Map transaction proof requires a clean dry-run apply preview")
        if not self.local_only or not self.read_only:
            raise ValueError("Personal Map transaction proof must remain read-only and local-only")
        if self.write_executed and not self.writes_artifacts:
            raise ValueError("write_executed requires writes_artifacts")
        if (
            self.live_apply_allowed
            or self.applies_personal_map_candidates
            or self.writes_runtime_memory_graph
            or self.approves_memory
            or self.mutates_canonical_state
            or self.canonical_writeback_allowed
            or self.agent_bus_task_write_allowed
            or self.runtime_dispatch_allowed
            or self.provider_or_connector_call_allowed
            or self.schedule_activation_allowed
            or self.second_datastore_created
            or self.rd_workbook_update_allowed
        ):
            raise ValueError("Personal Map transaction proof cannot enable blocked authority")
        if set(self.blocked_effects) != set(BLOCKED_EFFECTS):
            raise ValueError("Personal Map transaction proof must declare blocked effects")
        for entry in self.entries:
            entry.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "surface": self.surface,
            "transaction_status": self.transaction_status,
            "transaction_id": self.transaction_id,
            "ready_candidate_count": self.ready_candidate_count,
            "transaction_entry_count": self.transaction_entry_count,
            "graph_present_before": self.graph_present_before,
            "graph_node_count_before": self.graph_node_count_before,
            "graph_edge_count_before": self.graph_edge_count_before,
            "graph_sha256_before": self.graph_sha256_before,
            "planned_write_target": self.planned_write_target,
            "dry_run_apply_count": self.dry_run_apply_count,
            "dry_run_error_count": self.dry_run_error_count,
            "entries": [entry.to_dict() for entry in self.entries],
            "source_refs": list(self.source_refs),
            "write_requested": self.write_requested,
            "write_executed": self.write_executed,
            "writes": list(self.writes),
            "next_recommended_pass": self.next_recommended_pass,
            "local_only": self.local_only,
            "read_only": self.read_only,
            "writes_artifacts": self.writes_artifacts,
            "live_apply_allowed": self.live_apply_allowed,
            "applies_personal_map_candidates": self.applies_personal_map_candidates,
            "writes_runtime_memory_graph": self.writes_runtime_memory_graph,
            "approves_memory": self.approves_memory,
            "mutates_canonical_state": self.mutates_canonical_state,
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "agent_bus_task_write_allowed": self.agent_bus_task_write_allowed,
            "runtime_dispatch_allowed": self.runtime_dispatch_allowed,
            "provider_or_connector_call_allowed": self.provider_or_connector_call_allowed,
            "schedule_activation_allowed": self.schedule_activation_allowed,
            "second_datastore_created": self.second_datastore_created,
            "rd_workbook_update_allowed": self.rd_workbook_update_allowed,
            "allowed_write_root": self.allowed_write_root,
            "blocked_effects": list(self.blocked_effects),
            "notes": list(self.notes),
        }


def build_personal_map_apply_transaction_proof(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
) -> PersonalMapApplyTransactionProof:
    """Build a no-mutation transaction packet for ready Personal Map applies."""

    vault = _vault_path(vault_root)
    generated = generated_at or now_utc()
    live_proof = build_personal_map_live_apply_proof(vault, generated_at=generated)
    summary = live_proof.get("summary") or {}
    graph_summary = live_proof.get("graph_summary") or {}
    ready_rows = tuple(live_proof.get("ready_candidate_rows") or ())
    apply_items = {
        item.get("decision_id"): item
        for item in (live_proof.get("apply_preview") or {}).get("items", [])
        if item.get("decision_id")
    }
    graph_path = vault / PERSONAL_MAP_GRAPH_PATH
    graph_hash = _file_sha256(graph_path)
    entries: list[PersonalMapApplyTransactionEntryProof] = []

    for row in ready_rows:
        decision_id = str(row.get("decision_id") or "")
        candidate_id = str(row.get("candidate_id") or "")
        item = apply_items.get(decision_id) or {}
        seed = f"{decision_id}|{candidate_id}|{generated}"
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
        entry = PersonalMapApplyTransactionEntryProof(
            transaction_entry_id=f"personal-map-apply-entry-{digest}",
            decision_id=decision_id,
            candidate_id=candidate_id,
            candidate_type=str(row.get("candidate_type") or ""),
            target_type=str(row.get("target_type") or ""),
            target_id=row.get("target_id"),
            target_label=row.get("target_label"),
            planned_write_target=str(
                item.get("write_target") or PERSONAL_MAP_GRAPH_PATH.as_posix()
            ).replace("\\", "/"),
            idempotency_key=f"personal_map_apply:{decision_id}",
            approved_for_future_apply=bool(row.get("approved_for_future_apply")),
            already_applied=bool(row.get("already_applied")),
        )
        entry.validate()
        entries.append(entry)

    entries_tuple = tuple(entries)
    transaction_id = None
    status = STATUS_BLOCKED_NO_READY_CANDIDATES
    if entries_tuple:
        seed = "|".join(entry.idempotency_key for entry in entries_tuple)
        transaction_id = f"personal-map-apply-txn-{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:12]}"
        status = STATUS_READY

    proof = PersonalMapApplyTransactionProof(
        generated_at=generated,
        surface=SURFACE_ID,
        transaction_status=status,
        transaction_id=transaction_id,
        ready_candidate_count=len(entries_tuple),
        transaction_entry_count=len(entries_tuple),
        graph_present_before=bool(graph_summary.get("graph_present")),
        graph_node_count_before=int(graph_summary.get("node_count") or 0),
        graph_edge_count_before=int(graph_summary.get("edge_count") or 0),
        graph_sha256_before=graph_hash,
        planned_write_target=PERSONAL_MAP_GRAPH_PATH.as_posix(),
        dry_run_apply_count=int(summary.get("dry_run_apply_count") or 0),
        dry_run_error_count=int(summary.get("dry_run_error_count") or 0),
        entries=entries_tuple,
        source_refs=tuple(
            sorted(
                {
                    "runtime/pulse/personal_map_apply_transaction_proof.py",
                    *tuple(live_proof.get("source_refs") or ()),
                }
            )
        ),
    )
    proof.validate()
    return proof


def write_personal_map_apply_transaction_proof(
    vault_root: str | Path,
    *,
    output_path: str | Path | None = None,
    generated_at: str | None = None,
) -> PersonalMapApplyTransactionProof:
    """Write a proof-only Personal Map apply transaction artifact."""

    vault = _vault_path(vault_root)
    proof = build_personal_map_apply_transaction_proof(vault, generated_at=generated_at)
    root = (vault / PROOF_ROOT).resolve()
    if output_path is None:
        slug = _slug(proof.transaction_id or proof.transaction_status)
        target = root / f"{_date_slug(proof.generated_at)}-{slug}.json"
    else:
        target = Path(output_path)
        target = target if target.is_absolute() else vault / target
    _assert_inside(
        target,
        root,
        "Personal Map apply transaction proof must be written under Pulse transaction logs",
    )
    root.mkdir(parents=True, exist_ok=True)
    payload = proof.to_dict()
    payload["write_requested"] = True
    payload["write_executed"] = True
    payload["writes_artifacts"] = True
    payload["writes"] = [_relative_to_vault(vault, target)]
    target.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    written = PersonalMapApplyTransactionProof(
        **{
            **proof.to_dict(),
            "write_requested": True,
            "write_executed": True,
            "writes_artifacts": True,
            "writes": (_relative_to_vault(vault, target),),
            "entries": proof.entries,
            "source_refs": proof.source_refs,
            "blocked_effects": proof.blocked_effects,
            "notes": proof.notes,
        }
    )
    written.validate()
    return written
