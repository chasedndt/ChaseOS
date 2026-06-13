"""Data contracts for VentureOps instance intelligence and workflow packs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EvidenceRef:
    path: str
    matched_terms: list[str] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "matched_terms": list(self.matched_terms),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class DomainSignal:
    domain: str
    confidence: float
    evidence: list[EvidenceRef] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "confidence": round(self.confidence, 3),
            "evidence": [item.to_dict() for item in self.evidence],
        }


@dataclass(frozen=True)
class InstanceProfile:
    workspace_mode: str
    confidence: float
    detected_domains: list[DomainSignal]
    active_projects: list[dict[str, Any]]
    dormant_projects: list[dict[str, Any]]
    monetization_signals: list[dict[str, Any]]
    workflow_opportunities: list[dict[str, Any]]
    evidence_files: list[str]
    missing_information: list[str]
    discovery_questions: list[str]
    readiness_level: str
    authority_boundary: dict[str, Any]
    scan_summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "workspace_mode": self.workspace_mode,
            "confidence": round(self.confidence, 3),
            "detected_domains": [item.to_dict() for item in self.detected_domains],
            "active_projects": self.active_projects,
            "dormant_projects": self.dormant_projects,
            "monetization_signals": self.monetization_signals,
            "workflow_opportunities": self.workflow_opportunities,
            "evidence_files": list(self.evidence_files),
            "missing_information": list(self.missing_information),
            "discovery_questions": list(self.discovery_questions),
            "readiness_level": self.readiness_level,
            "authority_boundary": dict(self.authority_boundary),
            "scan_summary": dict(self.scan_summary),
        }


@dataclass(frozen=True)
class WorkflowRecommendation:
    workflow_id: str
    workflow_name: str
    target_user_or_customer: str
    domain: str
    problem_solved: str
    why_suggested: str
    evidence_files: list[str]
    confidence_score: float
    required_inputs: list[str]
    required_context: list[str]
    required_runtime_surfaces: list[str]
    approval_requirements: list[str]
    expected_outputs: list[str]
    proof_artifact: str
    monetization_path: str
    risks: list[str]
    first_safe_next_step: str
    readiness_level: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "target_user_or_customer": self.target_user_or_customer,
            "domain": self.domain,
            "problem_solved": self.problem_solved,
            "why_suggested": self.why_suggested,
            "evidence_files": list(self.evidence_files),
            "confidence_score": round(self.confidence_score, 3),
            "required_inputs": list(self.required_inputs),
            "required_context": list(self.required_context),
            "required_runtime_surfaces": list(self.required_runtime_surfaces),
            "approval_requirements": list(self.approval_requirements),
            "expected_outputs": list(self.expected_outputs),
            "proof_artifact": self.proof_artifact,
            "monetization_path": self.monetization_path,
            "risks": list(self.risks),
            "first_safe_next_step": self.first_safe_next_step,
            "readiness_level": self.readiness_level,
            "status": self.status,
        }


@dataclass(frozen=True)
class ProofCard:
    workflow_id: str
    run_id: str
    timestamp: str
    before_state: str
    after_state: str
    input_sources: list[str]
    runtimes_used: list[str]
    actions_taken: list[str]
    approvals_used: list[str]
    outputs_generated: list[str]
    files_written: list[str]
    screenshots_or_logs: list[str]
    scorecard_summary: dict[str, Any]
    result: str
    unresolved_risks: list[str]
    customer_facing_summary: str
    internal_audit_link: str
    cta_or_follow_up: str
    redaction_level: str = "internal_private"

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "before_state": self.before_state,
            "after_state": self.after_state,
            "input_sources": list(self.input_sources),
            "runtimes_used": list(self.runtimes_used),
            "actions_taken": list(self.actions_taken),
            "approvals_used": list(self.approvals_used),
            "outputs_generated": list(self.outputs_generated),
            "files_written": list(self.files_written),
            "screenshots_or_logs": list(self.screenshots_or_logs),
            "scorecard_summary": dict(self.scorecard_summary),
            "result": self.result,
            "unresolved_risks": list(self.unresolved_risks),
            "customer_facing_summary": self.customer_facing_summary,
            "internal_audit_link": self.internal_audit_link,
            "cta_or_follow_up": self.cta_or_follow_up,
            "redaction_level": self.redaction_level,
        }
