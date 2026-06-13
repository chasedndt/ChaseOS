"""Guarded live connector/source-scanner execution proof for ChaseOS Pulse.

This module is the execution boundary after the live approval-request proof.
The default path is a dry-run. A proof artifact can be written, but a connector
execution record is possible only when every evidence ref is real, the explicit
execute flag is set, and an approved bounded connector runner is supplied by the
caller. The CLI path deliberately supplies no runner, so the live repo remains
blocked until a ChaseOS runtime provides approved execution evidence.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from runtime.pulse.card_schema import now_utc
from runtime.pulse.connector_source_scanner_live_proof import (
    LIVE_PROOF_STATUS_NO_TARGETS,
    REQUIRED_EVIDENCE_SLOTS,
    PulseLiveProofTarget,
    build_pulse_connector_source_scanner_live_proof,
)
from runtime.pulse.connector_source_scanner_readiness import BLOCKED_EFFECTS as READINESS_BLOCKED_EFFECTS


EXECUTION_STATUS_BLOCKED_EVIDENCE = "blocked_missing_operator_permission_envelope"
EXECUTION_STATUS_BLOCKED_NO_TARGETS = "blocked_no_external_connector_targets"
EXECUTION_STATUS_READY = "ready_for_live_connector_execution"
EXECUTION_STATUS_BLOCKED_RUNNER = "blocked_missing_live_connector_runner"
EXECUTION_STATUS_EXECUTED = "live_connector_execution_recorded"
EXECUTION_STATUSES = {
    EXECUTION_STATUS_BLOCKED_EVIDENCE,
    EXECUTION_STATUS_BLOCKED_NO_TARGETS,
    EXECUTION_STATUS_READY,
    EXECUTION_STATUS_BLOCKED_RUNNER,
    EXECUTION_STATUS_EXECUTED,
}

ALLOWED_WRITE_ROOT = "07_LOGS/Pulse-Decks/source-scanner-live-executions/"
NEXT_RECOMMENDED_PASS = "pulse-product-grade-closeout-or-approved-external-evidence"

BLOCKED_EFFECTS = tuple(
    sorted(
        set(READINESS_BLOCKED_EFFECTS)
        | {
            "approval_grant",
            "canonical_source_promotion",
            "connector_runner_unbound",
            "memory_write",
            "source_content_ingest",
        }
    )
)


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _normalize_connector_id(connector_id: str | None) -> str:
    value = (connector_id or "all").strip()
    return value or "all"


def _slug(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in value).strip("-")


def _date_slug(generated_at: str) -> str:
    date = generated_at[:10]
    return date if len(date) == 10 else now_utc()[:10]


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


def _evidence_refs(evidence_refs: dict[str, str | None] | None) -> dict[str, str | None]:
    refs = evidence_refs or {}
    return {slot: refs.get(slot) for slot in REQUIRED_EVIDENCE_SLOTS}


@dataclass(frozen=True)
class PulseConnectorSourceScannerExecutionEvidenceSlot:
    slot_id: str
    ref: str | None
    satisfied: bool
    authority_class: str = "operator_gate"
    runtime_self_satisfiable: bool = False

    def validate(self) -> None:
        if self.slot_id not in REQUIRED_EVIDENCE_SLOTS:
            raise ValueError("invalid live connector execution evidence slot")
        if self.satisfied != _real_ref(self.ref):
            raise ValueError("evidence slot satisfaction must reflect real ref status")
        if self.runtime_self_satisfiable:
            raise ValueError("live connector execution evidence cannot be runtime self-satisfied")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class PulseConnectorSourceScannerExecutionResult:
    connector_id: str
    result_status: str
    result_ref: str
    item_count: int = 0
    source_content_read: bool = False
    secret_or_credential_read: bool = False
    unrestricted_web_scan: bool = False
    browser_history_ingest: bool = False
    source_promotion_executed: bool = False
    canonical_writeback_executed: bool = False

    def validate(self) -> None:
        if not self.connector_id:
            raise ValueError("execution result connector_id is required")
        if not self.result_status:
            raise ValueError("execution result_status is required")
        if not self.result_ref:
            raise ValueError("execution result_ref is required")
        if self.item_count < 0:
            raise ValueError("execution result item_count cannot be negative")
        if self.secret_or_credential_read:
            raise ValueError("live connector execution proof cannot read secrets")
        if self.unrestricted_web_scan:
            raise ValueError("live connector execution proof cannot run unrestricted web scans")
        if self.browser_history_ingest:
            raise ValueError("live connector execution proof cannot ingest browser history")
        if self.source_promotion_executed or self.canonical_writeback_executed:
            raise ValueError("live connector execution proof cannot promote sources or write canonical state")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


ConnectorRunner = Callable[[PulseLiveProofTarget], PulseConnectorSourceScannerExecutionResult]


@dataclass(frozen=True)
class PulseConnectorSourceScannerLiveExecutionProof:
    generated_at: str
    execution_status: str
    connector_id: str
    target_count: int
    live_proof_status: str
    evidence_slots: tuple[PulseConnectorSourceScannerExecutionEvidenceSlot, ...]
    missing_evidence_slots: tuple[str, ...]
    execute_requested: bool
    write_proof_requested: bool
    write_executed: bool = False
    writes: tuple[str, ...] = ()
    proof_targets: tuple[PulseLiveProofTarget, ...] = ()
    execution_results: tuple[PulseConnectorSourceScannerExecutionResult, ...] = ()
    next_recommended_pass: str = NEXT_RECOMMENDED_PASS
    local_only: bool = True
    writes_artifacts: bool = False
    connector_runner_bound: bool = False
    live_connector_execution_executed: bool = False
    provider_or_connector_call_executed: bool = False
    source_content_read: bool = False
    unrestricted_web_scan_allowed: bool = False
    browser_history_ingest_allowed: bool = False
    credential_or_secret_read_allowed: bool = False
    schedule_activation_allowed: bool = False
    agent_bus_task_write_allowed: bool = False
    approval_granted: bool = False
    approval_execution_allowed: bool = False
    memory_approval_allowed: bool = False
    source_promotion_allowed: bool = False
    autonomous_promotion_allowed: bool = False
    canonical_writeback_allowed: bool = False
    rd_workbook_update_allowed: bool = False
    mutates_canonical_state: bool = False
    allowed_write_root: str = ALLOWED_WRITE_ROOT
    blocked_effects: tuple[str, ...] = BLOCKED_EFFECTS
    notes: tuple[str, ...] = field(
        default_factory=lambda: (
            "Default invocation is a fail-closed dry-run proof.",
            "Live execution requires all evidence refs, an explicit execute flag, and a bounded connector runner.",
            "The CLI does not bind a connector runner and therefore cannot call live connectors by itself.",
        )
    )

    @property
    def execution_result_count(self) -> int:
        return len(self.execution_results)

    def validate(self) -> None:
        if self.execution_status not in EXECUTION_STATUSES:
            raise ValueError("invalid live connector execution status")
        if self.target_count != len(self.proof_targets):
            raise ValueError("target_count must match proof_targets")
        if tuple(slot.slot_id for slot in self.evidence_slots) != REQUIRED_EVIDENCE_SLOTS:
            raise ValueError("execution proof must preserve required evidence slot order")
        for slot in self.evidence_slots:
            slot.validate()
        expected_missing = tuple(slot.slot_id for slot in self.evidence_slots if not slot.satisfied)
        if self.missing_evidence_slots != expected_missing:
            raise ValueError("missing evidence slots must match unsatisfied slots")
        for target in self.proof_targets:
            target.validate()
        for result in self.execution_results:
            result.validate()
        if self.execution_status == EXECUTION_STATUS_BLOCKED_EVIDENCE and not self.missing_evidence_slots:
            raise ValueError("evidence-blocked status requires missing evidence")
        if self.execution_status in {
            EXECUTION_STATUS_READY,
            EXECUTION_STATUS_BLOCKED_RUNNER,
            EXECUTION_STATUS_EXECUTED,
        } and self.missing_evidence_slots:
            raise ValueError("ready/runner/executed statuses cannot have missing evidence")
        if self.execution_status == EXECUTION_STATUS_READY and self.execute_requested:
            raise ValueError("ready status requires execute_requested=false")
        if self.execution_status == EXECUTION_STATUS_BLOCKED_RUNNER and not self.execute_requested:
            raise ValueError("runner-blocked status requires execute_requested=true")
        if self.execution_status == EXECUTION_STATUS_EXECUTED:
            if not self.execute_requested or not self.connector_runner_bound:
                raise ValueError("executed status requires explicit execution and bound runner")
            if not self.execution_results:
                raise ValueError("executed status requires execution results")
            if not self.live_connector_execution_executed or not self.provider_or_connector_call_executed:
                raise ValueError("executed status must report connector execution")
        if self.write_executed and not (self.write_proof_requested or self.execute_requested):
            raise ValueError("write_executed requires proof or execute request")
        if self.write_executed and not self.writes_artifacts:
            raise ValueError("write_executed must report artifact writes")
        if self.unrestricted_web_scan_allowed:
            raise ValueError("live connector execution proof cannot allow unrestricted web scan")
        if self.browser_history_ingest_allowed:
            raise ValueError("live connector execution proof cannot ingest browser history")
        if self.credential_or_secret_read_allowed:
            raise ValueError("live connector execution proof cannot read credentials or secrets")
        if self.schedule_activation_allowed:
            raise ValueError("live connector execution proof cannot activate schedules")
        if self.agent_bus_task_write_allowed:
            raise ValueError("live connector execution proof cannot write Agent Bus tasks")
        if self.approval_granted or self.approval_execution_allowed:
            raise ValueError("live connector execution proof cannot grant or execute approvals")
        if self.memory_approval_allowed:
            raise ValueError("live connector execution proof cannot approve memory")
        if self.source_promotion_allowed or self.autonomous_promotion_allowed:
            raise ValueError("live connector execution proof cannot promote sources")
        if self.canonical_writeback_allowed or self.mutates_canonical_state:
            raise ValueError("live connector execution proof cannot write canonical state")
        if self.rd_workbook_update_allowed:
            raise ValueError("live connector execution proof cannot update the R&D workbook")
        for written in self.writes:
            if not written.replace("\\", "/").startswith(self.allowed_write_root):
                raise ValueError("live connector execution proof writes must stay under execution proof logs")
        if set(self.blocked_effects) != set(BLOCKED_EFFECTS):
            raise ValueError("live connector execution proof must declare blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "execution_status": self.execution_status,
            "connector_id": self.connector_id,
            "target_count": self.target_count,
            "live_proof_status": self.live_proof_status,
            "evidence_slots": [slot.to_dict() for slot in self.evidence_slots],
            "missing_evidence_slots": list(self.missing_evidence_slots),
            "execute_requested": self.execute_requested,
            "write_proof_requested": self.write_proof_requested,
            "write_executed": self.write_executed,
            "writes": list(self.writes),
            "proof_targets": [target.to_dict() for target in self.proof_targets],
            "execution_result_count": self.execution_result_count,
            "execution_results": [result.to_dict() for result in self.execution_results],
            "next_recommended_pass": self.next_recommended_pass,
            "local_only": self.local_only,
            "writes_artifacts": self.writes_artifacts,
            "connector_runner_bound": self.connector_runner_bound,
            "live_connector_execution_executed": self.live_connector_execution_executed,
            "provider_or_connector_call_executed": self.provider_or_connector_call_executed,
            "source_content_read": self.source_content_read,
            "unrestricted_web_scan_allowed": self.unrestricted_web_scan_allowed,
            "browser_history_ingest_allowed": self.browser_history_ingest_allowed,
            "credential_or_secret_read_allowed": self.credential_or_secret_read_allowed,
            "schedule_activation_allowed": self.schedule_activation_allowed,
            "agent_bus_task_write_allowed": self.agent_bus_task_write_allowed,
            "approval_granted": self.approval_granted,
            "approval_execution_allowed": self.approval_execution_allowed,
            "memory_approval_allowed": self.memory_approval_allowed,
            "source_promotion_allowed": self.source_promotion_allowed,
            "autonomous_promotion_allowed": self.autonomous_promotion_allowed,
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "rd_workbook_update_allowed": self.rd_workbook_update_allowed,
            "mutates_canonical_state": self.mutates_canonical_state,
            "allowed_write_root": self.allowed_write_root,
            "blocked_effects": list(self.blocked_effects),
            "notes": list(self.notes),
        }


def _slots(evidence_refs: dict[str, str | None]) -> tuple[PulseConnectorSourceScannerExecutionEvidenceSlot, ...]:
    return tuple(
        PulseConnectorSourceScannerExecutionEvidenceSlot(
            slot_id=slot_id,
            ref=evidence_refs.get(slot_id),
            satisfied=_real_ref(evidence_refs.get(slot_id)),
        )
        for slot_id in REQUIRED_EVIDENCE_SLOTS
    )


def build_pulse_connector_source_scanner_live_execution_proof(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    connector_id: str | None = None,
    evidence_refs: dict[str, str | None] | None = None,
) -> PulseConnectorSourceScannerLiveExecutionProof:
    """Build a dry-run live connector execution proof."""

    vault = _vault_path(vault_root)
    generated = generated_at or now_utc()
    requested = _normalize_connector_id(connector_id)
    refs = _evidence_refs(evidence_refs)
    live_proof = build_pulse_connector_source_scanner_live_proof(
        vault,
        generated_at=generated,
        connector_id=requested,
    )
    slots = _slots(refs)
    missing = tuple(slot.slot_id for slot in slots if not slot.satisfied)
    if live_proof.status == LIVE_PROOF_STATUS_NO_TARGETS:
        status = EXECUTION_STATUS_BLOCKED_NO_TARGETS
    elif missing:
        status = EXECUTION_STATUS_BLOCKED_EVIDENCE
    else:
        status = EXECUTION_STATUS_READY
    model = PulseConnectorSourceScannerLiveExecutionProof(
        generated_at=generated,
        execution_status=status,
        connector_id=requested,
        target_count=live_proof.target_count,
        live_proof_status=live_proof.status,
        evidence_slots=slots,
        missing_evidence_slots=missing,
        execute_requested=False,
        write_proof_requested=False,
        proof_targets=live_proof.proof_targets,
    )
    model.validate()
    return model


def write_pulse_connector_source_scanner_live_execution_proof(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    connector_id: str | None = None,
    evidence_refs: dict[str, str | None] | None = None,
    execute_live_scan: bool = False,
    connector_runner: ConnectorRunner | None = None,
    output_path: str | Path | None = None,
) -> PulseConnectorSourceScannerLiveExecutionProof:
    """Write a proof record, optionally executing a supplied bounded runner."""

    vault = _vault_path(vault_root)
    generated = generated_at or now_utc()
    requested = _normalize_connector_id(connector_id)
    base = build_pulse_connector_source_scanner_live_execution_proof(
        vault,
        generated_at=generated,
        connector_id=requested,
        evidence_refs=evidence_refs,
    )
    status = base.execution_status
    results: tuple[PulseConnectorSourceScannerExecutionResult, ...] = ()
    runner_bound = connector_runner is not None
    if execute_live_scan:
        if base.execution_status != EXECUTION_STATUS_READY:
            raise ValueError("cannot execute live connector/source scan until all evidence refs are ready")
        if requested == "all":
            raise ValueError("live connector/source scan execution requires one explicit connector_id, not all")
        if connector_runner is None:
            status = EXECUTION_STATUS_BLOCKED_RUNNER
        else:
            results = tuple(connector_runner(target) for target in base.proof_targets)
            status = EXECUTION_STATUS_EXECUTED

    if output_path is None:
        target_path = (
            vault
            / ALLOWED_WRITE_ROOT
            / f"{_date_slug(generated)}-live-execution-proof-{_slug(requested)}.json"
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
        raise ValueError("live connector/source execution proof must be written under 07_LOGS/Pulse-Decks/source-scanner-live-executions/") from exc

    model = PulseConnectorSourceScannerLiveExecutionProof(
        generated_at=base.generated_at,
        execution_status=status,
        connector_id=base.connector_id,
        target_count=base.target_count,
        live_proof_status=base.live_proof_status,
        evidence_slots=base.evidence_slots,
        missing_evidence_slots=base.missing_evidence_slots,
        execute_requested=execute_live_scan,
        write_proof_requested=True,
        write_executed=True,
        writes=(target_path.relative_to(vault).as_posix(),),
        proof_targets=base.proof_targets,
        execution_results=results,
        writes_artifacts=True,
        connector_runner_bound=runner_bound,
        live_connector_execution_executed=bool(results),
        provider_or_connector_call_executed=bool(results),
        source_content_read=any(result.source_content_read for result in results),
    )
    model.validate()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(model.to_dict(), indent=2), encoding="utf-8")
    return model
