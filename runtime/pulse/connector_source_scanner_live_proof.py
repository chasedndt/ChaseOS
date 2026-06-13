"""Approval-gated live connector/source-scanner proof for ChaseOS Pulse.

This module proves the handoff boundary for a future live source-scanner run.
It can write a pending approval request artifact, but it cannot grant approval,
execute connectors, call providers, fetch feeds, browse, read secrets, activate
schedules, promote sources, or mutate canonical state.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.card_schema import now_utc
from runtime.pulse.connector_source_scanner_readiness import (
    BLOCKED_EFFECTS,
    PulseConnectorContract,
    build_pulse_connector_source_scanner_readiness,
)


LIVE_PROOF_STATUS_BLOCKED = "blocked_missing_operator_permission_envelope"
LIVE_PROOF_STATUS_NO_TARGETS = "blocked_no_external_connector_targets"
LIVE_PROOF_STATUSES = {LIVE_PROOF_STATUS_BLOCKED, LIVE_PROOF_STATUS_NO_TARGETS}

APPROVAL_REQUEST_STATUS_PENDING = "pending_operator_review"
APPROVAL_REQUEST_STATUSES = {APPROVAL_REQUEST_STATUS_PENDING}

ALLOWED_WRITE_ROOT = "07_LOGS/Pulse-Decks/source-scanner-live-approval-requests/"

REQUIRED_EVIDENCE_SLOTS = (
    "operator_approval_ref",
    "permission_envelope_ref",
    "connector_scope_ref",
    "source_class_scope_ref",
    "denylist_ack_ref",
    "output_write_scope_ref",
)

NEXT_RECOMMENDED_PASS = "choose-approved-connector-or-defer-source-scanner-live-proof"


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _normalize_connector_id(connector_id: str | None) -> str:
    value = (connector_id or "all").strip()
    return value or "all"


def _slug(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in value).strip("-")


@dataclass(frozen=True)
class PulseLiveProofTarget:
    connector_id: str
    label: str
    adapter_path: str
    source_class: str
    connector_status: str
    external_call: bool
    approval_required_for_live: bool
    live_execution_enabled: bool = False
    eligible_for_request: bool = True
    blockers: tuple[str, ...] = field(
        default_factory=lambda: (
            "missing_operator_approval_ref",
            "missing_permission_envelope_ref",
            "missing_connector_scope_ref",
            "missing_output_write_scope_ref",
        )
    )

    @classmethod
    def from_contract(cls, contract: PulseConnectorContract) -> "PulseLiveProofTarget":
        return cls(
            connector_id=contract.connector_id,
            label=contract.label,
            adapter_path=contract.adapter_path,
            source_class=contract.source_class,
            connector_status=contract.status,
            external_call=contract.external_call,
            approval_required_for_live=contract.approval_required_for_live,
            live_execution_enabled=contract.live_execution_enabled,
            eligible_for_request=contract.external_call and contract.approval_required_for_live,
        )

    def validate(self) -> None:
        if not self.connector_id:
            raise ValueError("live proof target connector_id is required")
        if self.live_execution_enabled:
            raise ValueError("live proof target cannot enable connector execution")
        if self.external_call and not self.approval_required_for_live:
            raise ValueError("external live proof targets require approval")
        if self.eligible_for_request and not self.external_call:
            raise ValueError("only external connector targets can be eligible for live requests")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class PulseConnectorSourceScannerLiveApprovalRequest:
    request_id: str
    generated_at: str
    connector_id: str
    status: str
    requested_targets: tuple[PulseLiveProofTarget, ...]
    required_evidence_slots: tuple[str, ...] = REQUIRED_EVIDENCE_SLOTS
    requested_capability: str = "pulse_connector_source_scanner_live_proof"
    approval_granted: bool = False
    execution_allowed: bool = False
    writes_artifact_only: bool = True
    mutates_canonical_state: bool = False

    def validate(self) -> None:
        if not self.request_id:
            raise ValueError("approval request_id is required")
        if self.status not in APPROVAL_REQUEST_STATUSES:
            raise ValueError("invalid approval request status")
        if not self.requested_targets:
            raise ValueError("approval request requires at least one requested target")
        for target in self.requested_targets:
            target.validate()
        if self.approval_granted or self.execution_allowed:
            raise ValueError("live proof approval request cannot grant or execute approval")
        if not self.writes_artifact_only:
            raise ValueError("live proof approval request must be artifact-only")
        if self.mutates_canonical_state:
            raise ValueError("live proof approval request cannot mutate canonical state")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "request_id": self.request_id,
            "generated_at": self.generated_at,
            "connector_id": self.connector_id,
            "status": self.status,
            "requested_targets": [target.to_dict() for target in self.requested_targets],
            "required_evidence_slots": list(self.required_evidence_slots),
            "requested_capability": self.requested_capability,
            "approval_granted": self.approval_granted,
            "execution_allowed": self.execution_allowed,
            "writes_artifact_only": self.writes_artifact_only,
            "mutates_canonical_state": self.mutates_canonical_state,
        }


@dataclass(frozen=True)
class PulseConnectorSourceScannerLiveProof:
    generated_at: str
    status: str
    connector_id: str
    target_count: int
    external_connector_count: int
    live_enabled_connector_count: int
    required_evidence_slots: tuple[str, ...]
    proof_targets: tuple[PulseLiveProofTarget, ...]
    write_requested: bool = False
    write_executed: bool = False
    writes: tuple[str, ...] = ()
    approval_request: PulseConnectorSourceScannerLiveApprovalRequest | None = None
    next_recommended_pass: str = NEXT_RECOMMENDED_PASS
    read_only: bool = True
    local_only: bool = True
    source_content_read: bool = False
    writes_artifacts: bool = False
    live_connector_execution_enabled: bool = False
    provider_or_connector_call_allowed: bool = False
    unrestricted_web_scan_allowed: bool = False
    browser_history_ingest_allowed: bool = False
    credential_or_secret_read_allowed: bool = False
    schedule_activation_allowed: bool = False
    approval_granted: bool = False
    approval_execution_allowed: bool = False
    memory_approval_allowed: bool = False
    source_promotion_allowed: bool = False
    autonomous_promotion_allowed: bool = False
    canonical_writeback_allowed: bool = False
    rd_workbook_update_allowed: bool = False
    agent_bus_task_write_allowed: bool = False
    allowed_write_root: str = ALLOWED_WRITE_ROOT
    blocked_effects: tuple[str, ...] = BLOCKED_EFFECTS
    notes: tuple[str, ...] = field(
        default_factory=lambda: (
            "This is a fail-closed proof/request layer, not a live connector runner.",
            "A written request is pending-review evidence only and does not grant approval.",
        )
    )

    def validate(self) -> None:
        if self.status not in LIVE_PROOF_STATUSES:
            raise ValueError("invalid live proof status")
        if self.target_count != len(self.proof_targets):
            raise ValueError("target_count must match proof target count")
        if self.external_connector_count < self.target_count:
            raise ValueError("external connector count cannot be lower than target count")
        for target in self.proof_targets:
            target.validate()
        if self.write_executed and not self.write_requested:
            raise ValueError("write_executed requires write_requested")
        if self.write_executed and self.read_only:
            raise ValueError("written live proof cannot be read_only")
        if self.write_executed and not self.writes_artifacts:
            raise ValueError("written live proof must report writes_artifacts")
        if self.approval_request is not None:
            self.approval_request.validate()
        if self.source_content_read:
            raise ValueError("live proof cannot read source content")
        if self.live_connector_execution_enabled or self.live_enabled_connector_count:
            raise ValueError("live proof cannot enable connector execution")
        if self.provider_or_connector_call_allowed:
            raise ValueError("live proof cannot call providers/connectors")
        if self.unrestricted_web_scan_allowed:
            raise ValueError("live proof cannot allow unrestricted web scan")
        if self.browser_history_ingest_allowed:
            raise ValueError("live proof cannot ingest browser history")
        if self.credential_or_secret_read_allowed:
            raise ValueError("live proof cannot read secrets")
        if self.schedule_activation_allowed:
            raise ValueError("live proof cannot activate schedules")
        if self.approval_granted or self.approval_execution_allowed:
            raise ValueError("live proof cannot grant or execute approval")
        if self.memory_approval_allowed:
            raise ValueError("live proof cannot approve memory")
        if self.source_promotion_allowed or self.autonomous_promotion_allowed:
            raise ValueError("live proof cannot promote sources")
        if self.canonical_writeback_allowed:
            raise ValueError("live proof cannot write canonical state")
        if self.rd_workbook_update_allowed:
            raise ValueError("live proof cannot update the R&D workbook")
        if self.agent_bus_task_write_allowed:
            raise ValueError("live proof cannot write Agent Bus tasks")
        for written in self.writes:
            if not written.replace("\\", "/").startswith(self.allowed_write_root):
                raise ValueError("live proof writes must stay under the approval request log root")
        if set(self.blocked_effects) != set(BLOCKED_EFFECTS):
            raise ValueError("live proof must declare connector/source scanner blocked effects")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "status": self.status,
            "connector_id": self.connector_id,
            "target_count": self.target_count,
            "external_connector_count": self.external_connector_count,
            "live_enabled_connector_count": self.live_enabled_connector_count,
            "required_evidence_slots": list(self.required_evidence_slots),
            "proof_targets": [target.to_dict() for target in self.proof_targets],
            "write_requested": self.write_requested,
            "write_executed": self.write_executed,
            "writes": list(self.writes),
            "approval_request": self.approval_request.to_dict() if self.approval_request else None,
            "next_recommended_pass": self.next_recommended_pass,
            "read_only": self.read_only,
            "local_only": self.local_only,
            "source_content_read": self.source_content_read,
            "writes_artifacts": self.writes_artifacts,
            "live_connector_execution_enabled": self.live_connector_execution_enabled,
            "provider_or_connector_call_allowed": self.provider_or_connector_call_allowed,
            "unrestricted_web_scan_allowed": self.unrestricted_web_scan_allowed,
            "browser_history_ingest_allowed": self.browser_history_ingest_allowed,
            "credential_or_secret_read_allowed": self.credential_or_secret_read_allowed,
            "schedule_activation_allowed": self.schedule_activation_allowed,
            "approval_granted": self.approval_granted,
            "approval_execution_allowed": self.approval_execution_allowed,
            "memory_approval_allowed": self.memory_approval_allowed,
            "source_promotion_allowed": self.source_promotion_allowed,
            "autonomous_promotion_allowed": self.autonomous_promotion_allowed,
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "rd_workbook_update_allowed": self.rd_workbook_update_allowed,
            "agent_bus_task_write_allowed": self.agent_bus_task_write_allowed,
            "allowed_write_root": self.allowed_write_root,
            "blocked_effects": list(self.blocked_effects),
            "notes": list(self.notes),
        }


def _select_targets(
    contracts: tuple[PulseConnectorContract, ...],
    connector_id: str,
) -> tuple[PulseLiveProofTarget, ...]:
    requested = _normalize_connector_id(connector_id)
    eligible = tuple(
        PulseLiveProofTarget.from_contract(contract)
        for contract in contracts
        if contract.external_call and contract.approval_required_for_live
    )
    if requested == "all":
        return eligible
    matches = tuple(target for target in eligible if target.connector_id == requested)
    if matches:
        return matches
    known = sorted(contract.connector_id for contract in contracts)
    raise ValueError(f"unknown or non-live connector_id '{requested}'. Known connectors: {', '.join(known)}")


def build_pulse_connector_source_scanner_live_proof(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    connector_id: str | None = None,
) -> PulseConnectorSourceScannerLiveProof:
    """Return a fail-closed live proof contract for approved connector work."""

    vault = _vault_path(vault_root)
    generated = generated_at or now_utc()
    readiness = build_pulse_connector_source_scanner_readiness(vault, generated_at=generated)
    requested = _normalize_connector_id(connector_id)
    targets = _select_targets(readiness.connector_contracts, requested)
    status = LIVE_PROOF_STATUS_BLOCKED if targets else LIVE_PROOF_STATUS_NO_TARGETS
    model = PulseConnectorSourceScannerLiveProof(
        generated_at=generated,
        status=status,
        connector_id=requested,
        target_count=len(targets),
        external_connector_count=readiness.external_connector_count,
        live_enabled_connector_count=readiness.live_enabled_connector_count,
        required_evidence_slots=REQUIRED_EVIDENCE_SLOTS,
        proof_targets=targets,
    )
    model.validate()
    return model


def write_pulse_connector_source_scanner_live_proof_request(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    connector_id: str | None = None,
    output_path: str | Path | None = None,
) -> PulseConnectorSourceScannerLiveProof:
    """Write a pending approval request artifact for a future live proof."""

    vault = _vault_path(vault_root)
    generated = generated_at or now_utc()
    requested = _normalize_connector_id(connector_id)
    base = build_pulse_connector_source_scanner_live_proof(
        vault,
        generated_at=generated,
        connector_id=requested,
    )
    if not base.proof_targets:
        raise ValueError("no eligible live connector targets available for approval request")

    request_id = f"pulse_source_scanner_live_proof_{generated[:10]}_{_slug(requested)}"
    request = PulseConnectorSourceScannerLiveApprovalRequest(
        request_id=request_id,
        generated_at=generated,
        connector_id=requested,
        status=APPROVAL_REQUEST_STATUS_PENDING,
        requested_targets=base.proof_targets,
    )
    request.validate()

    if output_path is None:
        target_path = vault / ALLOWED_WRITE_ROOT / f"{generated[:10]}-live-proof-request-{_slug(requested)}.json"
    else:
        target_path = Path(output_path)
        if not target_path.is_absolute():
            target_path = vault / target_path
    target_path = target_path.resolve()
    allowed_root = (vault / ALLOWED_WRITE_ROOT).resolve()
    if not str(target_path).startswith(str(allowed_root)):
        raise ValueError("live proof approval request must be written under 07_LOGS/Pulse-Decks/source-scanner-live-approval-requests/")

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(request.to_dict(), indent=2), encoding="utf-8")
    rel_path = target_path.relative_to(vault).as_posix()

    model = PulseConnectorSourceScannerLiveProof(
        generated_at=generated,
        status=base.status,
        connector_id=requested,
        target_count=base.target_count,
        external_connector_count=base.external_connector_count,
        live_enabled_connector_count=base.live_enabled_connector_count,
        required_evidence_slots=REQUIRED_EVIDENCE_SLOTS,
        proof_targets=base.proof_targets,
        write_requested=True,
        write_executed=True,
        writes=(rel_path,),
        approval_request=request,
        read_only=False,
        writes_artifacts=True,
    )
    model.validate()
    return model
